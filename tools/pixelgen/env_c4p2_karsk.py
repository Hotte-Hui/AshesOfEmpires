"""env_c4p2_karsk -- generator for L_C4P2_Karsk (Chapter 4 part 2, Karsk locomotive depot; documentation/C4P2_DESIGN.md
4.1).  Replaces the story stream's placeholder scene.json and keeps every spawn, hotspot, blocker, camera zone and NPC
name of it.

Run:  py -3 -P tools/pixelgen/env_c4p2_karsk.py [--preview=DIR]      (deterministic, no network)

Produces assets/environments/karsk_c4p2/:
* depot_a.png / depot_b.png (+ _n normals, _e emission): the two places, each baked in its own light -- A the back
  yard and the coal stage at dawn (Monday 6.10), B the showcase and platform 1 in the evening floodlight (Tuesday);
* sky_a/b, town_a/b, line_a/b: the parallax backgrounds (dawn / night), veils_a/b (light cones in the haze),
  fg_a/b (foreground silhouettes, parallax 1.25);
* patches/: story states (the order taken from the sill, the guidebook taken from the press table, the halves on
  Lev's bench, the joined card) and the insignia sites (roundhouse gable, roundhouse front, the engine's smokebox
  door; neutral + *_hist via Symbols.pick);
* life/: the people as looping strips baked in the scene's light (Kolonne 4, the cook, the stoker, the fitter; the
  band, children, the cleaner, the canteen, the militia, families, the conductor, a vendor, a porter ...);
* fx/: steam, smoke, snow, coal dust, sparks, embers, the fire door, the shovels behind the tarpaulin;
* actors/: sparrows, the yard dog, breath puffs, the barrel's flames, the far goods train;
* scene.json (registry gates + "scene" filters of scripts/levels/c4/annex_level.gd, camera_zones, looks, actors)
  and provenance.json.  The documents (inspect close-ups) come from env_c4p2_karsk_docs.py.
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
import env_c4p2_karsk_kit as K          # noqa: E402
import env_c4p2_karsk_layout as L       # noqa: E402
import env_c4p2_karsk_yard as EY        # noqa: E402
import env_c4p2_karsk_show as ES        # noqa: E402
import env_c4p2_karsk_far as EF         # noqa: E402
import env_c4p2_karsk_life as LF        # noqa: E402
import env_c4p2_karsk_fx as FX          # noqa: E402
import env_keep as EK                   # noqa: E402  (round-10 shared-folder rules: own PNGs, scene merge)

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'karsk_c4p2')
LF_ = chr(10)
GEN = 'tools/pixelgen/env_c4p2_karsk'
PRODUCED: list[tuple[str, str, str]] = []
SA, SB = L.SA, L.SB
EXPOSURE = {SA: 0.80, SB: 0.70}
# sparrow perches (feet; the bird's cell reaches 6 px left, 7 right, 11 up): on top of the „РАЗДАЧА“ board and on the
# counter's end -- never on the letters; on the roundhouse cornice right of the parapet emblem
SPARROWS_HATCH = [[265, 232], [272, 232], [292, 232], [257, 268]]
SPARROWS_CORNICE = [[738, 115], [747, 115], [866, 115], [876, 115], [886, 115]]

COL = {'warm': '#F0C487', 'sodium': '#F2B060', 'cold': '#A8BCD4', 'white': '#E8E4DA', 'green': '#9FE0B4',
       'fire': '#F2A050'}
# dynamic Godot lights for the baked ones: name -> (energy, radius, height, colour, slow flicker, Hz)
DYN = {
    SA: {'lamp_yard': (0.45, 110, 22, 'sodium', 0.0, 0), 'win_dispatch': (0.35, 70, 8, 'warm', 0.0, 0),
         'hatch': (0.45, 80, 10, 'warm', 0.0, 0), 'brazier': (0.3, 44, 6, 'fire', 0.25, 1.4),
         'flood_1': (0.45, 300, 60, 'sodium', 0.0, 0), 'deck_bulb': (0.3, 70, 12, 'warm', 0.0, 0),
         'barrel': (0.55, 80, 12, 'fire', 0.3, 1.2), 'ash_glow': (0.2, 46, 4, 'fire', 0.2, 0.8),
         'stall': (0.45, 110, 14, 'warm', 0.0, 0), 'door_lamp': (0.4, 54, 14, 'warm', 0.0, 0)},
    SB: {'flood_engine_1': (0.5, 150, 30, 'white', 0.0, 0), 'flood_engine_-1': (0.5, 150, 30, 'white', 0.0, 0),
         'headlamp': (0.3, 90, 30, 'white', 0.0, 0), 'signal_green': (0.35, 60, 10, 'green', 0.0, 0),
         'bulbs': (0.35, 80, 30, 'warm', 0.0, 0), 'canteen_1182': (0.45, 90, 14, 'warm', 0.0, 0),
         'canteen_1236': (0.4, 90, 14, 'warm', 0.0, 0), 'kitchen_fire': (0.3, 50, 6, 'fire', 0.25, 1.1),
         'cabin': (0.3, 50, 6, 'warm', 0.0, 0), 'sand_stove': (0.5, 90, 8, 'fire', 0.25, 1.3),
         'green_lamp': (0.55, 74, 14, 'warm', 0.0, 0), 'canopy_1676': (0.5, 110, 30, 'cold', 0.0, 0),
         'canopy_1796': (0.5, 110, 30, 'cold', 0.0, 0), 'canopy_1900': (0.45, 110, 30, 'cold', 0.0, 0),
         'express_door_win': (0.35, 50, 8, 'warm', 0.0, 0), 'stage_flood': (0.3, 260, 60, 'sodium', 0.0, 0)},
}


def _jsonable(o):
    if hasattr(o, 'item'):
        return o.item()
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(type(o))


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def record(path: str, gen: str, desc: str):
    PRODUCED.append((rel(path), gen, desc))


def save_arr(arr, path, gen, desc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)
    record(path, gen, desc)


def clean_env_dir():
    """Remove only this generator's own previous PNGs (its provenance rows, tools/pixelgen/env_keep.py); keep
    explore_hotspots.json, foreign files and the .import sidecars (UIDs stay stable)."""
    if os.path.isdir(ENV_DIR):
        EK.remove_own_pngs(ENV_DIR, ROOT, GEN)


# =========================================================================== bakes
def bake(scene: str, cfg: dict):
    painter = (EY.Yard if scene == SA else ES.Show)(cfg).build()
    lights = painter.all_lights()
    F = K.light_fields(painter.lay, lights)
    K.add_pools(F, lights, L.FEET - 8, L.WORLD_H, L.WORLD_W)
    K.resolve(painter.lay, F, exposure=EXPOSURE[scene])
    return painter


def maps(painter):
    lay = painter.lay
    x0, x1 = L.SPAN[painter_scene(painter)]
    return lay.c[:, x0:x1].copy(), lay.normal_map(3.0)[:, x0:x1].copy(), lay.em[:, x0:x1].copy()


def painter_scene(p):
    return SA if isinstance(p, EY.Yard) else SB


def diff_box(a, b, pad=1):
    d = np.zeros(a[0].shape[:2], bool)
    for x, y in zip(a, b):
        d |= np.any(x != y, axis=-1)
    if not d.any():
        return None
    ys, xs = np.nonzero(d)
    h, w = d.shape
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad + 1), min(h, ys.max() + pad + 1))


def write_patch(m, box, name, desc, hist_m=None):
    x0, y0, x1, y1 = box
    c, n, e = m
    base = os.path.join(ENV_DIR, 'patches', name)
    g = GEN + '.py'
    save_arr(c[y0:y1, x0:x1], base + '.png', g, desc)
    save_arr(n[y0:y1, x0:x1], base + '_n.png', g, desc + ' -- normal map')
    ee = e[y0:y1, x0:x1]
    has_e = bool(ee[..., 3].any())
    if has_e:
        save_arr(ee, base + '_e.png', g, desc + ' -- emission mask')
    if hist_m is not None:
        hc, hn, he = hist_m
        save_arr(hc[y0:y1, x0:x1], base + '_hist.png', g,
                 desc + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
        save_arr(hn[y0:y1, x0:x1], base + '_hist_n.png', g, desc + ' -- historical, normal map')
        if has_e or bool(he[y0:y1, x0:x1][..., 3].any()):
            save_arr(he[y0:y1, x0:x1], base + '_hist_e.png', g, desc + ' -- historical, emission')
            has_e = True
    return has_e


# =========================================================================== foreground
def fg(scene: str):
    """Dark silhouettes nearer than the walk band (parallax 1.25), all below y 318."""
    p = 1.25
    c0, c1 = L.CAMERA[scene][0], L.CAMERA[scene][1] - 640
    home = int(round(c0 * p - c0))
    w = int(640 + (c1 - c0) * (p - 1.0) + (c1 - c0)) + 8
    lay = K.tlayer(w, L.WORLD_H, 'fg')
    rng = np.random.default_rng(801 if scene == SA else 802)
    yb = L.WORLD_H
    # a snow bank along the bottom edge, with dark things stuck in it
    n = K.nz(w, 4, 30, 803 if scene == SA else 804)[0]
    for x in range(w):
        top = int(338 + n[x] * 14)
        lay.rect(x, top, 1, yb - top, 'B', 2.2, hgt=0.5)
        lay.rect(x, top + 2, 1, yb - top - 2, 'B', 1.4, hgt=0.5)
        lay.px(x, top, 'S', 1.4)
        lay.px(x, top + 1, 'B', 3.0)
    things = []
    if scene == SA:
        things = [('rails', 30), ('barrow', 250), ('post', 470), ('sleepers', 640), ('drum', 820)]
    else:
        things = [('bench', 70), ('trolley', 420), ('post', 700), ('bin', 980)]
    for kind, x in things:
        if kind == 'rails':
            for k in range(3):
                lay.rect(x, 330 + k * 4, 90, 3, 'N', 2.0 + k * 0.2, hgt=0.6)
                lay.rect(x, 330 + k * 4, 90, 1, 'I', 2.6)
        elif kind == 'barrow':
            lay.poly([(x, 326), (x + 26, 326), (x + 20, 340), (x + 4, 340)], 'N', 1.8, hgt=0.6)
            lay.ellipse(x + 22, 342, 5, 5, 'N', 1.2)
            lay.line(x, 326, x - 12, 336, 'N', 2.0)
            lay.rect(x + 2, 324, 22, 2, 'S', 2.2)
        elif kind == 'post':
            lay.rect(x, 322, 5, 38, 'N', 1.4, hgt=0.6)                     # a stump of a fence post
            lay.rect(x, 322, 1, 38, 'S', 1.8)
            lay.rect(x - 1, 320, 7, 2, 'S', 2.4)
        elif kind == 'sleepers':
            for k in range(3):
                lay.rect(x + k * 2, 334 - k * 6, 70, 6, 'N', 1.6 + (k % 2) * 0.4, hgt=0.6)
                lay.rect(x + k * 2, 334 - k * 6, 70, 1, 'S', 2.0)
        elif kind == 'drum':
            lay.ellipse(x, 340, 16, 13, 'N', 1.6, hgt=0.6)
            lay.ellipse(x, 340, 7, 6, 'N', 0.8)
        elif kind == 'bench':
            lay.rect(x, 326, 60, 3, 'N', 2.0, hgt=0.6)
            lay.rect(x, 318, 60, 3, 'N', 1.8)
            lay.rect(x + 4, 329, 2, 20, 'N', 1.4)
            lay.rect(x + 54, 329, 2, 20, 'N', 1.4)
            lay.rect(x, 324, 60, 1, 'S', 2.4)
        elif kind == 'trolley':
            lay.rect(x, 328, 50, 4, 'N', 1.8, hgt=0.6)
            lay.rect(x + 6, 318, 20, 10, 'N', 2.2)
            lay.rect(x + 28, 320, 16, 8, 'N', 2.0)
            lay.ellipse(x + 8, 336, 4, 4, 'N', 1.2)
            lay.ellipse(x + 42, 336, 4, 4, 'N', 1.2)
            lay.rect(x + 6, 317, 20, 1, 'S', 2.2)
        elif kind == 'bin':
            lay.rect(x, 322, 14, 24, 'N', 1.8, hgt=0.6)
            lay.rect(x, 322, 14, 1, 'S', 2.4)
    F = K.empty_fields(L.WORLD_H, w)
    K.resolve(lay, F, exposure=1.0)
    return lay, home, w


# =========================================================================== scene
def build_scene(preview_dir=None):
    t0 = time.time()
    clean_env_dir()
    layers, props, decals, fx, lights, actors = [], [], [], [], [], []
    painters = {}
    for scene, cfg_base, fname, desc in (
            (SA, {}, 'depot_a', 'Karsk locomotive depot, the back yard and the coal stage, Monday 17 February 1964, '
                                '6.10 (dawn): dispatch office, canteen hatch, water crane, coal stage with Kolonne '
                                '4\'s heap, the special run\'s tender, ash pit, fire barrel, roundhouse back'),
            (SB, {}, 'depot_b', 'Karsk locomotive depot, the showcase and platform 1, Tuesday 18 February 1964, '
                                'evening floodlight: the painted tarpaulin, the restored signal, the polished engine, '
                                'the band stage, the press canteen, the turntable, the sand-drying house, the '
                                'westbound Corridor express')):
        p = bake(scene, cfg_base)
        painters[scene] = p
        m = maps(p)
        x0 = L.SPAN[scene][0]
        base = os.path.join(ENV_DIR, fname)
        save_arr(m[0], base + '.png', GEN + '_%s.py' % ('yard' if scene == SA else 'show'), desc)
        save_arr(m[1], base + '_n.png', GEN + '.py', desc + ' -- normal map (OpenGL +Y up)')
        save_arr(m[2], base + '_e.png', GEN + '.py', desc + ' -- emission mask (unshaded glow)')
        layers.append({'name': fname, 'file': fname + '.png', 'pos': [x0, 0], 'parallax': [1, 1], 'z': -50,
                       'normal': True, 'emission': True, 'emission_strength': 0.5, 'lit': True, 'scene': [scene]})
        print('  %s baked (%.1fs)' % (fname, time.time() - t0))
        # ---- story patches
        variants = ([('order_taken', {'order_taken': True}, {'after': ['c4e_inspect_order']})] if scene == SA else
                    [('book_taken', {'book_taken': True}, {'after': ['c4g_inspect_book']}),
                     ('halves_on_bench', {'halves': True},
                      {'after': ['c4g_talk_lev'], 'until': ['c4g_solve_halves']}),
                     ('card_joined', {'joined': True}, {'after': ['c4g_solve_halves']})])
        for (vname, change, gate) in variants:
            vm = maps(bake(scene, dict(cfg_base, **change)))
            box = diff_box(m, vm)
            if box is None:
                print('  WARNING variant %s changes nothing' % vname)
                continue
            he = write_patch(vm, box, vname, 'the %s with the story change "%s"' % (fname, vname))
            d = {'name': vname, 'file': 'patches/%s.png' % vname, 'pos': [int(x0 + box[0]), int(box[1])], 'z': -48,
                 'lit': True, 'normal': True, 'emission': he, 'emission_strength': 0.5, 'fade': 0.45,
                 'scene': [scene]}
            d.update(gate)
            decals.append(d)
        # ---- insignia sites: neutral (= the base bake) + *_hist
        hm = maps(bake(scene, dict(cfg_base, hist=True)))
        sites = {SA: {'insignia_roundhouse_back': (L.GABLE_EMBLEM[0] - 14, L.GABLE_EMBLEM[0] + 15)},
                 SB: {'insignia_roundhouse_front': (L.RH_FRONT[0] + 30, L.RH_FRONT[1] - 30),
                      'insignia_engine': (L.LOCO[0] + 24, L.LOCO[1] - 24)}}[scene]
        d_all = np.zeros(m[0].shape[:2], bool)
        for a_, b_ in zip(m, hm):
            d_all |= np.any(a_ != b_, axis=-1)
        for nm, (sx0, sx1) in sites.items():
            dd = d_all.copy()
            dd[:, :sx0 - x0] = False
            dd[:, sx1 - x0:] = False
            if nm == 'insignia_roundhouse_front':
                dd[130:, :] = False
            if nm == 'insignia_engine':
                dd[:150, :] = False
            if not dd.any():
                print('  WARNING insignia site %s: no difference' % nm)
                continue
            ys, xs = np.nonzero(dd)
            box = (xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3)
            he = write_patch(m, box, nm, 'insignia site %s, fictional emblem (neutral)' % nm, hist_m=hm)
            decals.append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [x0 + int(box[0]), int(box[1])],
                           'z': -49, 'lit': True, 'normal': True, 'emission': he,
                           'hist_variant': 'patches/%s_hist.png' % nm, 'scene': [scene]})
        print('  %s patches + insignia (%.1fs)' % (fname, time.time() - t0))

    # ---- parallax backgrounds
    for scene, sfx_ in ((SA, 'a'), (SB, 'b')):
        for (fn, p, z, desc) in ((EF.sky, 0.1, -80, 'the sky (%s)'), (EF.town, 0.3, -72, 'the town of Karsk (%s)'),
                                 (EF.embankment, 0.55, -64, 'the embankment / station side (%s)')):
            lay, home = fn(scene)
            nm = '%s_%s' % (fn.__name__.replace('embankment', 'line'), sfx_)
            save_arr(lay.c, os.path.join(ENV_DIR, nm + '.png'), GEN + '_far.py',
                     desc % ('dawn' if scene == SA else 'evening') + ', parallax %.2f' % p)
            ent = {'name': nm, 'file': nm + '.png', 'pos': [home, 0], 'parallax': [p, 1.0], 'z': z, 'normal': False,
                   'lit': False, 'scene': [scene]}
            if bool(lay.em[..., 3].any()):
                save_arr(lay.em, os.path.join(ENV_DIR, nm + '_e.png'), GEN + '_far.py', 'lit windows -- emission')
                ent['emission'] = True
                ent['emission_strength'] = 0.35
            layers.insert(0, ent)
    # ---- veils
    ya, sb_ = painters[SA], painters[SB]
    fm = L.FLOOD_MAST
    cones = {
        SA: [(fm - 6, 70, 3, 60, 262, 'L', 5, 0.9, -150), (fm, 70, 3, 60, 270, 'L', 5, 0.8, -90),
             (fm + 6, 72, 3, 50, 276, 'L', 5, 0.6, 10), (L.LAMP_A[0] + 9, L.LAMP_A[1] + 2, 2, 22, 290, 'L', 5, 0.6, 0),
             (789, 242, 2, 14, 286, 'L', 5, 0.6, 0), ((L.CHUTES[0] + L.CHUTES[1]) // 2, 200, 2, 24, 280, 'L', 5,
                                                      0.5, 0)],
        SB: [(L.RH_FRONT[0] + 12, 208, 2, 30, 290, 'S', 5, 0.7, 30), (L.RH_FRONT[1] - 12, 208, 2, 30, 290, 'S', 5,
                                                                      0.7, -30),
             (1676, 161, 2, 30, 292, 'S', 5, 0.8, 0), (1796, 161, 2, 30, 292, 'S', 5, 0.8, 0),
             (1900, 161, 2, 30, 292, 'S', 5, 0.7, 0), (L.GREEN_LAMP[0], L.GREEN_LAMP[1] + 2, 6, 22, 262, 'L', 5,
                                                       0.8, 0),
             (1182, 202, 2, 20, 270, 'L', 5, 0.5, 0), (1236, 202, 2, 20, 270, 'L', 5, 0.5, 0),
             (994, 64, 3, 50, 190, 'L', 5, 0.5, -60),
             (sb_.flood_b[0] - 5, sb_.flood_b[1], 3, 46, 176, 'L', 5, 0.55, 40),
             (sb_.flood_b[0] + 5, sb_.flood_b[1], 3, 52, 180, 'L', 5, 0.5, 70)],
    }
    for scene, sfx_ in ((SA, 'a'), (SB, 'b')):
        x0, x1 = L.SPAN[scene]
        vl = FX.veils(scene, cones[scene], x0, x1 - x0)
        nm = 'veils_%s' % sfx_
        save_arr(vl, os.path.join(ENV_DIR, nm + '.png'), GEN + '_fx.py',
                 'light cones of the floodlights and lamps in the haze (%s, plain alpha)' % scene)
        layers.append({'name': nm, 'file': nm + '.png', 'pos': [x0, 0], 'parallax': [1, 1], 'z': 10,
                       'normal': False, 'emission': False, 'lit': False, 'scene': [scene]})
        lay, home, w = fg(scene)
        nm = 'fg_%s' % sfx_
        save_arr(lay.c, os.path.join(ENV_DIR, nm + '.png'), GEN + '.py',
                 'foreground silhouettes below the walk band (parallax 1.25)')
        layers.append({'name': nm, 'file': nm + '.png', 'pos': [home + L.CAMERA[scene][0], 0],
                       'parallax': [1.25, 1.0], 'z': 60, 'normal': False, 'emission': False, 'lit': False,
                       'scene': [scene]})
    print('  backgrounds, veils, fg (%.1fs)' % (time.time() - t0))

    # ---- life strips
    mouths = {SA: [], SB: []}
    for scene, fn in ((SA, LF.life_a), (SB, LF.life_b)):
        lts = painters[scene].all_lights()
        for e in fn(lts, EXPOSURE[scene]):
            c, n, em = e.strip.arrays()
            base = os.path.join(ENV_DIR, 'life', e.name)
            save_arr(c, base + '.png', GEN + '_life.py', e.desc)
            save_arr(n, base + '_n.png', GEN + '_life.py', e.desc + ' -- normal map')
            d = {'name': e.name, 'file': 'life/%s.png' % e.name, 'frames': len(e.strip.frames), 'fps': e.fps,
                 'pos': [int(e.strip.origin[0]), int(e.strip.origin[1])], 'z': e.z, 'lit': True, 'normal': True,
                 'scene': [scene]}
            if bool(em[..., 3].any()):
                save_arr(em, base + '_e.png', GEN + '_life.py', e.desc + ' -- emission')
                d['emission'] = True
                d['emission_strength'] = 0.6
            if e.t0 is not None:
                d['t0'] = float(e.t0)
            d.update(e.gate)
            decals.append(d)
            if e.mouth is not None:
                mouths[scene].append([int(e.mouth[0]), int(e.mouth[1])])
    print('  life strips (%.1fs)' % (time.time() - t0))

    # ---- fx strips
    def fx_entry(nm, arr, pos, frames, fps, z, scene, desc, em=None, section='fx', alpha=None, lit=False):
        base = os.path.join(ENV_DIR, 'fx', nm)
        save_arr(arr, base + '.png', GEN + '_fx.py', desc)
        e = {'name': nm, 'file': 'fx/%s.png' % nm, 'frames': frames, 'fps': fps, 'pos': [int(pos[0]), int(pos[1])],
             'z': z, 'lit': lit, 'scene': [scene]}
        if em is not None:
            save_arr(em, base + '_e.png', GEN + '_fx.py', desc + ' -- emission strip')
            e['emission'] = True
            e['emission_strength'] = 0.7
        if section == 'fx':
            e['type'] = 'anim_sprite'
            e['parallax'] = [1.0, 1.0]
            fx.append(e)
        else:
            e['normal'] = False
            decals.append(e)
        if alpha is not None:
            e['alpha'] = alpha

    # scene A
    sx, sy = ya.stall_glow
    fx_entry('stall_steam', FX.billow(48, 90, 16, 901, warm_k=0.35), (sx - 14, L.A_BACK - 90), 16, 7, -46, SA,
             'steam rolling out of the open stall door and up the roundhouse wall (16 frames)')
    for i, (hx, hy) in enumerate(ya.smoke_hoods):
        fx_entry('hood_smoke_%d' % i, FX.plume(26, 70, 16, 910 + i, ramp='V', tone=2.2 + (i % 2) * 0.6, drift=0.9,
                                               spread_k=0.3), (hx - 13, hy - 70), 16, 6, -46, SA,
                 'smoke and steam from the roundhouse smoke hood %d (16 frames)' % i)
    px_, py_ = ya.stovepipe_top
    fx_entry('dispatch_smoke', FX.plume(16, 44, 16, 920, ramp='V', tone=2.0, drift=1.0), (px_ - 8, py_ - 44), 16, 5,
             -46, SA, 'thin smoke from the dispatch office\'s stove pipe (16 frames)')
    vx_, vy_ = ya.vent
    fx_entry('canteen_vent', FX.plume(18, 40, 16, 921, ramp='V', tone=3.4, drift=0.7), (vx_ - 9, vy_ - 40), 16, 6,
             -46, SA, 'kitchen steam from the canteen\'s vent (16 frames)')
    kx, ky = ya.pot
    fx_entry('kasha_steam', FX.plume(14, 26, 16, 922, ramp='V', tone=4.2, dens=0.8), (kx - 7, ky - 26), 16, 6,
             -45, SA, 'steam over the kasha pot in the hatch (16 frames)')
    bx, by = ya.brazier
    fx_entry('brazier_embers', FX.glow_door(9, 3, 8, 923), (bx - 4, by + 1), 8, 5, -45, SA,
             'the water crane brazier\'s embers breathing (8 frames)', em=FX.glow_door(9, 3, 8, 923), section='decals')
    fx_entry('brazier_smoke', FX.plume(14, 30, 16, 924, ramp='V', tone=2.4, dens=0.6), (bx - 7, by - 30), 16, 5,
             -46, SA, 'a thread of smoke over the brazier (16 frames)')
    fx_entry('flood_dust', FX.particles(150, 120, 32, 8, 46, 925, kind='dust', vy=(-1.0, 2.0), vx=(-2.0, 1.0),
                                         sway=1.5), (L.STAGE[0] + 50, 150), 32, 8, 12, SA,
             'coal dust and frost glittering in the floodlight over the stage (32 frames)')
    fx_entry('coal_grains', FX.particles(120, 60, 24, 8, 24, 926, kind='coal', vy=(2.0, 6.0), vx=(-1.0, 1.0),
                                          sway=0.6), (L.TENDER[0], L.DECK_Y + 2), 24, 8, -43, SA,
             'coal grains trickling from the chutes\' lips (24 frames)')
    fx_entry('snow_a', FX.particles(700, 300, 48, 10, 150, 927, kind='snow', vy=(5, 10), vx=(1, 4), sway=1.2),
             (0, 0), 48, 10, 30, SA, 'snow falling over the yard (48 frames)')
    fx_entry('snow_a2', FX.particles(670, 300, 48, 10, 106, 928, kind='snow', vy=(4, 8), vx=(1, 3), sway=1.0),
             (230, 20), 48, 10, 30, SA, 'snow falling over the stage and the roundhouse (48 frames)')
    fx_entry('barrel_sparks', FX.particles(24, 50, 16, 10, 7, 929, kind='spark', vy=(-9, -5), vx=(-1.5, 2.0),
                                            spawn=lambda r: (12 + r.uniform(-3, 3), 48)), (L.BARREL - 12,
                                                                                         L.A_MID - 72), 16, 10, -30,
             SA, 'sparks rising from the fire barrel (16 frames)')
    # scene B
    fx_entry('shovels_over', FX.shovels_over(60, 26, 12, 931), (906, 168), 12, 8, -47, SB,
             'behind the tarpaulin: two shovels swing up over its edge in turn, coal flies (12 frames)')
    fx_entry('coal_dust_b', FX.plume(70, 80, 16, 932, ramp='X', tone=3.0, drift=0.5, spread_k=0.4, dens=0.7),
             (900, 96), 16, 6, -47, SB, 'coal dust rising from behind the tarpaulin (16 frames)')
    cxp, cyp = sb_.cabin_pipe
    fx_entry('cabin_smoke', FX.plume(14, 36, 16, 933, ramp='H', tone=2.6), (cxp - 7, cyp - 36), 16, 5, -46, SB,
             'smoke from the turntable cabin\'s stove pipe, lit from below by the yard (16 frames)')
    chx, chy = sb_.stove_chimney
    fx_entry('sandhouse_smoke', FX.plume(26, 84, 16, 934, ramp='H', tone=2.8, drift=0.8), (chx - 13, chy - 84), 16,
             5, -46, SB, 'smoke from the sand-drying house chimney catching the floodlight (16 frames)')
    smx, smy = sb_.samovar
    fx_entry('samovar_steam', FX.plume(12, 22, 16, 935, ramp='V', tone=4.4, dens=0.8), (smx - 6, smy - 22), 16, 6,
             -45, SB, 'steam from the samovar (16 frames)')
    kax, kay = sb_.kasha
    fx_entry('kasha_steam_b', FX.plume(14, 24, 16, 936, ramp='V', tone=4.0, dens=0.7), (kax - 7, kay - 24), 16, 6,
             -46, SB, 'steam over the band\'s kasha behind the curtain (16 frames)')
    sfx_, sfy = sb_.stove_fire
    fx_entry('sand_fire', FX.glow_door(10, 6, 8, 937), (sfx_ - 5, sfy - 2), 8, 6, -45, SB,
             'the sand stove\'s fire behind its door (8 frames)', em=FX.glow_door(10, 6, 8, 937), section='decals')
    for i, (ex_, ey_) in enumerate(sb_.steam_points):
        fx_entry('express_steam_%d' % i, FX.plume(30, 40, 16, 940 + i, ramp='V', tone=3.6, drift=1.2, dens=0.7),
                 (ex_ - 15, ey_ - 40), 16, 6, -44, SB, 'heating steam leaking from under the express (16 frames)')
    lx_, ly_ = sb_.headlamp
    fx_entry('snow_b', FX.particles(700, 300, 48, 10, 150, 945, kind='snow', vy=(5, 10), vx=(1, 4), sway=1.2),
             (880, 0), 48, 10, 30, SB, 'snow falling over the showcase (48 frames)')
    fx_entry('snow_b2', FX.particles(700, 300, 48, 10, 150, 946, kind='snow', vy=(4, 9), vx=(1, 3), sway=1.0),
             (1220, 10), 48, 10, 30, SB, 'snow falling over the platform (48 frames)')
    fx_entry('lamp_dust_b', FX.particles(90, 110, 32, 8, 26, 947, kind='dust', vy=(-1, 1.5), vx=(-1.5, 1.5)),
             (L.GREEN_LAMP[0] - 45, L.GREEN_LAMP[1]), 32, 8, 12, SB, 'dust motes under the green lamp (32 frames)')
    print('  fx strips (%.1fs)' % (time.time() - t0))

    # ---- actors (Karsk ambient actors of Chapter 1 with this level's sprites; scene_id filters them)
    adir = 'res://assets/environments/karsk_c4p2/actors/'
    sp = FX.sparrows()
    save_arr(sp, os.path.join(ENV_DIR, 'actors', 'sparrows.png'), GEN + '_fx.py',
             'sparrows (KarskCrows frame layout: idle, look, chirp, preen, hop, take-off, flight; 14 x 12 cells)')
    dg, dge = FX.dog()
    save_arr(dg, os.path.join(ENV_DIR, 'actors', 'dog.png'), GEN + '_fx.py',
             'the yard dog curled up in the ash pit\'s warmth (KarskCat frame layout, 24 x 12 cells)')
    save_arr(dge, os.path.join(ENV_DIR, 'actors', 'dog_e.png'), GEN + '_fx.py', 'the dog\'s eyes in the glow')
    br = FX.breath_puff()
    save_arr(br, os.path.join(ENV_DIR, 'actors', 'breath_puff.png'), GEN + '_fx.py', 'breath puff (6 frames)')
    fl = FX.flames(8, 14, 18, 951)
    save_arr(fl, os.path.join(ENV_DIR, 'fx', 'barrel_flames.png'), GEN + '_fx.py',
             'the fire barrel\'s flame tongues (KarskBarrel, 8 frames)')
    save_arr(fl, os.path.join(ENV_DIR, 'fx', 'barrel_flames_e.png'), GEN + '_fx.py', 'the flames -- emission')
    loco, wags, puff = FX.train_parts()
    save_arr(loco, os.path.join(ENV_DIR, 'actors', 'train_loco.png'), GEN + '_fx.py',
             'the first goods train of the day on the far embankment: locomotive and tender')
    for k, img in wags.items():
        save_arr(img, os.path.join(ENV_DIR, 'actors', 'train_wag_%s.png' % k), GEN + '_fx.py',
                 'far goods wagon (%s)' % k)
    save_arr(puff, os.path.join(ENV_DIR, 'actors', 'train_puff.png'), GEN + '_fx.py', 'the train\'s smoke puffs')
    rail_a = 222
    actors += [
        {'scene': 'res://scenes/levels/c4p2/KarskDepotTrain.tscn', 'pos': [0, rail_a],
         'props': {'loco': adir + 'train_loco.png',
                   'wagons': [adir + 'train_wag_%s.png' % k for k in ('box', 'gond', 'tank', 'flat')],
                   'puff': adir + 'train_puff.png', 'parallax': 0.55, 'z': -63.0, 'span': [-80.0, 840.0],
                   'speed': 30.0, 'interval': [30.0, 50.0], 'first_delay': 9.0, 'chimney': [7.0, -18.0],
                   'wagons_min': 7.0, 'wagons_max': 11.0, 'train_db': -8.0,
                   'amb_trains': {'amb_karsk_depot': [0.0]}, 'amb_train_len': 18.0, 'sound_len': 13.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA,
         'note': 'goods trains on the far embankment: every 30-50 s at -8 dB, silently in time with the train inside '
                 'amb_karsk_depot (0-18 s of its loop, never two on top of each other), nothing while a film runs '
                 '(scripts/levels/c4p2/karsk_depot_train.gd)'},
        {'scene': 'res://scenes/levels/c4p2/KarskDepotDog.tscn', 'pos': [L.DOG[0], L.DOG[1]],
         'props': {'sprite': adir + 'dog.png', 'wake_radius': 40.0, 'z': -39.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA,
         'note': 'the yard dog asleep on the ash pit rim; lifts its head when Alexei comes near'},
        {'scene': 'res://scenes/levels/c4p2/KarskDepotSparrows.tscn', 'pos': [280, 232],
         'props': {'perches': SPARROWS_HATCH, 'sprite': adir + 'sparrows.png',
                   'scare_radius': 30.0, 'nervous_radius': 64.0, 'z': -44.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA,
         'note': 'sparrows after the crumbs: on top of the „РАЗДАЧА“ board (never on its letters) and on the counter'},
        {'scene': 'res://scenes/levels/c4p2/KarskDepotSparrows.tscn', 'pos': [800, 120],
         'props': {'perches': SPARROWS_CORNICE, 'sprite': adir + 'sparrows.png', 'scare_radius': 26.0,
                   'nervous_radius': 50.0, 'z': -45.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA, 'note': 'sparrows on the warm roundhouse cornice (clear of the '
                                                          'emblem)'},
        {'scene': 'res://scenes/levels/karsk/KarskBarrel.tscn', 'pos': [L.BARREL, L.A_MID + 1],
         'props': {'flames': 'res://assets/environments/karsk_c4p2/fx/barrel_flames.png',
                   'flame_pos': [L.BARREL, ya.barrel_top[1]], 'flame_frames': 8.0, 'mouths': [],
                   'breath': adir + 'breath_puff.png', 'z': -30.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA, 'note': 'the guard\'s fire barrel: flame tongues and sparks'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [500, 292],
         'props': {'points': [[445, 258], [502, 254], [536, 262], [562, 260], [610, 256], [430, 142], [547, 123],
                              [495, 123], [402, 194]],
                   'sprite': adir + 'breath_puff.png', 'interval': 4.2, 'z': -39.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA, 'note': 'Kolonne 4\'s breath in the frost'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [300, 292],
         'props': {'points': [[308, 255], [363, 249]], 'sprite': adir + 'breath_puff.png', 'interval': 5.0,
                   'z': -39.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SA, 'note': 'breath at the hatch and the brazier'},
        {'scene': 'res://scenes/levels/karsk/KarskWind.tscn', 'pos': [0, 0],
         'props': {'roofs': [[88, 236, 203], [233, 347, 150], [380, 600, 166], [710, 904, 116]]},
         'gen': 'env_c4p2_karsk', 'scene_id': SA, 'note': 'gusts: spindrift along the ground and off the roofs'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [1600, 292],
         'props': {'points': mouths[SB], 'sprite': adir + 'breath_puff.png', 'interval': 4.6, 'z': -37.0},
         'gen': 'env_c4p2_karsk', 'scene_id': SB,
         'note': 'the band\'s and the platform\'s breath in the frost (at every outdoor figure\'s mouth)'},
        {'scene': 'res://scenes/levels/karsk/KarskWind.tscn', 'pos': [0, 0],
         'props': {'roofs': [[1146, 1268, 166], [1314, 1568, 174], [1594, 1920, 134], [856, 1014, 190]]},
         'gen': 'env_c4p2_karsk', 'scene_id': SB, 'note': 'gusts: spindrift off the roofs and the canopy'},
    ]

    # ---- dynamic lights (every light carries an empty "after" so registry_level names it and its flicker runs)
    for scene in (SA, SB):
        for lt in painters[scene].all_lights():
            nm = lt['name']
            if nm not in DYN[scene]:
                continue
            en, rad, hgt, col, slow, hz = DYN[scene][nm]
            e = {'name': nm, 'pos': [int(round(lt['pos'][0])), int(round(lt['pos'][1]))], 'color': COL[col],
                 'energy': en, 'radius': rad, 'height': hgt, 'flicker': 0.0, 'on_layer': 'playfield', 'after': [],
                 'scene': [scene]}
            if slow > 0:
                e['flicker_slow'], e['flicker_hz'] = slow, hz
            lights.append(e)

    # ---- hotspot info + explore art
    hotspot_info = {}
    for k, (what, span) in L.HOTSPOT_PROPS.items():
        hotspot_info[k] = {'kind': 'story', 'stand': list(L.HOTSPOTS[k]), 'focus': [L.HOTSPOTS[k][0], 262],
                           'what': what, 'span': [int(span[0]), int(span[1])]}
    # story text the art keeps readable: no life strip, sparrow or NPC anchor may cover these rects (test)
    readable = {'duty_board': {'rect': list(L.DUTY_BOARD), 'scene': SA},
                'press_notice': {'rect': list(L.NOTICE), 'scene': SA}}
    for scene in (SA, SB):
        for k, r in painters[scene].readable.items():
            readable[k] = {'rect': [int(v) for v in r], 'scene': scene}

    manifest = {
        'id': 'karsk_c4p2', 'palette': 'depot',
        'world_size': [L.WORLD_W, L.WORLD_H],
        'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]},
        'camera_zones': {k: [v[0], 0, v[1] - v[0], L.WORLD_H] for k, v in L.CAMERA.items()},
        'canvas_modulate': '#D4DAE2',
        'layers': layers, 'props': props, 'decals': decals, 'lights': lights, 'fx': fx, 'actors': actors,
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]],
                     [L.WALK_X[1], L.WALK_BAND[1]], [L.WALK_X[0], L.WALK_BAND[1]]],
        'blockers': [dict(b) for b in L.BLOCKERS],
        'spawns': {k: list(v) for k, v in L.SPAWNS.items()},
        'hotspots': {k: list(v) for k, v in L.HOTSPOTS.items()},
        'zones': {k: list(v) for k, v in L.ZONES.items()},
        'looks': [
            {'name': 'dawn', 'scene': SA, 'canvas_modulate': '#D4DAE2', 'grade': 'depot_dawn'},
            {'name': 'evening', 'scene': SB, 'canvas_modulate': '#E2D8CA', 'grade': 'depot_evening'},
        ],
        'npcs': {k: dict(v) for k, v in L.NPCS.items()},
        'hotspot_info': hotspot_info,
        'readable': readable,
        'gates_doc': ('scripts/levels/c4/annex_level.gd (extends the registry level): an entry with "scene" is built '
                      'only when the level plays that Story scene (level_id, set before _ready); actors carry '
                      '"scene_id". "after" / "until" / "choice" / "fade" are the registry gates (objectives of '
                      'earlier scenes count as complete). Lights carry an empty "after" so they are named and their '
                      'slow flicker runs. camera_zones = the camera window per scene; looks = canvas modulate + '
                      'grade per scene.'),
        'notes': [
            'Side view: feet line y 300, walk band 296-306, x 18-1902; everything painted stands behind it (base_y '
            '<= 294), the fg layers stay below y 318. The tarpaulin (858-898) is the permanent blocker between scene '
            'A (back yard and coal stage, Monday dawn) and scene B (showcase and platform 1, Tuesday evening): two '
            'places, two bakes (depot_a / depot_b), never seen together (camera_zones).',
            'People: Kolonne 4 (ten life strips + Maria, the speaking NPC at x 578), the cook (seen through the '
            'hatch), a stoker and a fitter in A; in B the brass band (five different people on one beat; the tuba is '
            'the turntable man, bareheaded -- his cap lies on the controller), children, the cleaner, the canteen\'s '
            'waitress and cook, an old fitter oiling the turntable, a smoker in the sand-house door, a woman sifting '
            'sand, the depot cat, the militia patrol (grey greatcoats, fur hats), the families of the explore text, '
            'the grandmother, the conductor (navy, silver cap band, lantern), a mother and boy, a couple, the '
            'pirozhki seller, the porter (quilted jacket, white apron) -- anonymous, no insignia. Irina, Maria, the '
            'guard, Ekdahl, the press officer and Lev stand at the npcs anchors (cast stream sheets).',
            'Readable story figures (scene.json "readable": no life strip, sparrow or NPC covers them): the carbon '
            'on Irina\'s sill (order_taken removes it), the duty blackboard, the press notice on the roundhouse back '
            'door, „РАЗДАЧА“ over the hatch, „ВОССТАНОВИМ ВМЕСТЕ“ on the old banner (5x7) and on the tarpaulin '
            'panel (lashed in front of its poles), the brass plate „1939“, the guidebook on the press table '
            '(book_taken), the halves / the joined card on Lev\'s bench, „БЕРЛИН – КАРСК“ / „СПАЛЬНЫЙ ВАГОН“ / '
            '„ВАГОН-РЕСТОРАН“ on the express\'s letterboard above the windows (over the people\'s heads), the two '
            'clocks and „ВЫХОД НА ПЕРРОН“ on the gate\'s iron bracket.',
            'Insignia: patches/insignia_*.png (roundhouse gable, roundhouse front, the engine\'s smokebox door) show '
            'the fictional gear-and-wheat emblem; their *_hist twins the red star with hammer and sickle '
            '(Symbols.pick). No life strip carries insignia.',
            'Palette: data/chapters/c4p2.json palettes.depot + the ramps of env_c4p2_karsk_kit.DEPOT (integration '
            'note of the env-karsk stream).',
        ],
        'meta': {'mode': 'side', 'feet_y': L.FEET, 'generator': 'tools/pixelgen/env_c4p2_karsk.py', 'date': K.DATE,
                 'palette_ramps': K.DEPOT},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    manifest = json.loads(json.dumps(manifest, ensure_ascii=False, default=_jsonable))
    manifest = EK.merge_scene(manifest, EK.read_json(sj))       # keys / actors other writers added stay
    EK.write_json(sj, manifest)
    record(sj, GEN + '.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1 + registry gates + scene filters)')
    for scene in (SA, SB):
        n_, bad = K.palette_report(painters[scene].lay.c)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (scene, bad[:6]))
    for note in K.check_c4p2_palette()[:1]:
        print('  NOTE', note, '(+%d more)' % (len(K.check_c4p2_palette()) - 1))
    print('  scene built in %.1fs' % (time.time() - t0))
    if preview_dir:
        preview(manifest, preview_dir)
    return manifest


# =========================================================================== preview (parallax-correct composite)
def compose(scene_json, scene, cam_x, done=(), t=0.0, hist=False):
    W_, H_ = 640, L.WORLD_H
    img = np.zeros((H_, W_, 3), np.float32)

    def load(p):
        if hist:
            hp = p[:-4] + '_hist.png'
            if os.path.exists(os.path.join(ENV_DIR, hp)):
                p = hp
        return np.asarray(Image.open(os.path.join(ENV_DIR, p)).convert('RGBA'))

    def holds(e):
        if 'scene' in e and scene not in e['scene']:
            return False
        for o in e.get('after', []):
            if o not in done:
                return False
        for o in e.get('until', []):
            if o in done:
                return False
        return True

    items = []
    for e in scene_json['layers']:
        if holds(e):
            items.append((e['z'], 0, e))
    for e in scene_json['decals']:
        if holds(e):
            items.append((e.get('z', 0), 1, e))
    for e in scene_json['fx']:
        if holds(e):
            items.append((e.get('z', 0), 2, e))
    for (_z, _k, e) in sorted(items, key=lambda r: (r[0], r[1])):
        src = load(e['file'])
        frames = int(e.get('frames', 1))
        fw = src.shape[1] // frames
        fr = int((t * float(e.get('fps', 6)))) % frames
        s = src[:, fr * fw:(fr + 1) * fw].astype(np.float32)
        par = e.get('parallax', [1, 1])
        p = float(par[0]) if isinstance(par, list) else float(par)
        x = int(round(e['pos'][0] - cam_x * p))
        y = int(e['pos'][1])
        h, w = s.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W_, x + w), min(H_, y + h)
        if X1 <= X0 or Y1 <= Y0:
            continue
        sub = s[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4] / 255.0 * float(e.get('alpha', 1.0))
        img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - a) + sub[..., :3] * a
        if e.get('emission'):
            ep = os.path.join(ENV_DIR, e['file'][:-4] + '_e.png')
            if os.path.exists(ep):
                em = np.asarray(Image.open(ep).convert('RGBA')).astype(np.float32)[:, fr * fw:(fr + 1) * fw]
                esub = em[Y0 - y:Y1 - y, X0 - x:X1 - x]
                k = float(e.get('emission_strength', 0.22)) * esub[..., 3:4] / 255.0
                img[Y0:Y1, X0:X1] = np.clip(img[Y0:Y1, X0:X1] + esub[..., :3] * k, 0, 255)
    return np.clip(img, 0, 255).astype(np.uint8)


def preview(scene_json, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    shots = [('a_cam0', SA, 0, ()), ('a_cam238', SA, 238, ()), ('a_order', SA, 0, ('c4e_inspect_order',)),
             ('b_cam878', SB, 878, ()), ('b_cam1100', SB, 1100, ()), ('b_cam1280', SB, 1280, ()),
             ('b_halves', SB, 1100, ('c4g_talk_ekdahl', 'c4g_inspect_book', 'c4g_talk_lev')),
             ('b_joined', SB, 1100, ('c4g_talk_ekdahl', 'c4g_inspect_book', 'c4g_talk_lev', 'c4g_solve_halves'))]
    for (nm, sc, cx, done) in shots:
        img = compose(scene_json, sc, cx, done, t=1.3)
        Image.fromarray(img).save(os.path.join(out_dir, 'look_%s.png' % nm))
    print('  preview written to', out_dir)


# =========================================================================== provenance
def write_provenance():
    files = [{'path': p, 'generator': g if g.startswith('tools/') else 'tools/pixelgen/' + g, 'content': d}
             for p, g, d in sorted(PRODUCED)]
    for f_ in files:
        if not f_['generator'].endswith('.py'):
            f_['generator'] += '.py'
    out = {'generator': 'tools/pixelgen/env_c4p2_karsk.py (+ _kit, _layout, _yard, _show, _far, _people, _life, _fx)',
           'date': K.DATE,
           'licence': 'project-owned original artwork, generated procedurally; no copied, traced, downloaded or '
                      'AI-generated pixels; bitmap fonts hand-defined (env_veltrava_hall_kit.py, env_c4_tunnels_kit.py, '
                      'env_c4p2_karsk_kit.py)',
           'run': 'py -3 -P tools/pixelgen/env_c4p2_karsk.py',
           'files': files}
    p = os.path.join(ENV_DIR, 'provenance.json')
    out['files'] = EK.merge_rows(out['files'], EK.read_json(p), GEN, ROOT)
    EK.write_json(p, out)


def main(argv):
    t0 = time.time()
    prev = None
    for a in argv:
        if a.startswith('--preview'):
            prev = a.split('=', 1)[1] if '=' in a else os.path.join(ENV_DIR, '_preview')
    print('[env_c4p2_karsk] scene ...')
    build_scene(prev)
    write_provenance()
    for root, _dirs, files in os.walk(ENV_DIR):
        for f in files:
            if f.endswith('.png.import') and not os.path.exists(os.path.join(root, f[:-len('.import')])):
                os.remove(os.path.join(root, f))
    print('[env_c4p2_karsk] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
