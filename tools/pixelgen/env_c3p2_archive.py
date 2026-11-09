"""env_c3p2_archive -- generator for L_C3_Registry 'Registratur der Kommission' (Chapter 3 part 2).

Run:  py -3 -P tools/pixelgen/env_c3p2_archive.py [--preview=DIR]      (deterministic, no network)

Produces assets/environments/veltrava_registry/ (C3P2_DESIGN.md 5.1):
* four baked looks of the same rooms (one opaque layer each, z-banded so a later look covers an earlier one):
    room_a.png      A  night, the green lamp still off, Konrad's torch in the aisle   (until c3c_talk_konrad)
    room.png        B  night, green lamp on (base layer, always loaded)
    room_fire_c.png C  smoke + fire in the Magazin / Planarchiv, ramp door shut      (after c3d_choose)
    room_fire_d.png D  the fire in the Karteisaal                                   (after c3e_reach_konrad)
  each with its own _n (normals) and _e (emission) map;
* patches/: small opaque crops of a look with one story change applied (scarf taken, halves on the table,
  file taken, Blatt 7 pocketed, fire case smashed, desk pushed) and the insignia site of the Magazin
  (neutral + *_hist), gated by the objective / choice that causes them;
* props/cart*.png (+ *_hist): the handcart with the crates of wagon 4 (seal wire until c3c_inspect_crates);
* outside.png (light wells behind the high windows), shafts.png (night), smoke_c/d.png, fg_frame.png;
* fx/ strips: yard snow, snow through the door gap, dust in the lamp light, flames, embers, ash, smoke
  plumes, heat shimmer, the ringing fire bell; life/guard_feet.png (boots passing a window);
* scene.json (layers / props / decals / fx / lights with the gate keys after / until / choice / fade, the
  design's spawns, hotspots, walk band, blockers, zones, looks) + provenance.json.
The gates are applied by scripts/levels/c3p2_archive/registry_level.gd (the level script of the .tscn).
Shared folder (round 11, tools/pixelgen/env_keep.py): a run removes only the PNGs its previous run recorded in
provenance.json and merges scene.json / provenance.json over the old ones -- explore_hotspots.json, keys and
"actors" other writers add, their files and provenance rows stay; an unchanged run is byte-identical.
"""
from __future__ import annotations

import json
import os
import sys
import time
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_c3p2_archive_kit as K          # noqa: E402
import env_c3p2_archive_layout as L       # noqa: E402
import env_c3p2_archive_room as ER        # noqa: E402
import env_c3p2_archive_fx as EFX         # noqa: E402
import env_c3p2_archive_props as EP       # noqa: E402
import env_keep as KEEP                 # noqa: E402  (round 11: the folder is shared)

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'veltrava_registry')
LF = chr(10)
PRODUCED: list[tuple[str, str, str]] = []
FAMILY = 'tools/pixelgen/env_c3p2_archive'   # provenance rows of this generator and its modules (env_keep)

STATES = {
    'a': dict(lamp_green=False, torch=True, door_closed=False, clock=(0, 38), scarf=True, halves=False, file=True,
              blatt7=True, fire=0),
    'b': dict(lamp_green=True, door_closed=False, clock=(0, 52), scarf=True, halves=False, file=True, blatt7=True,
              fire=0),
    'c': dict(lamp_green=True, door_closed=True, clock=(1, 43), scarf=False, halves=True, file=True, blatt7=True,
              fire=1),
    'd': dict(lamp_green=False, door_closed=True, clock=(1, 47), scarf=False, halves=True, file=False, blatt7=True,
              fire=2),
}
ROOM_FILE = {'a': 'room_a', 'b': 'room', 'c': 'room_fire_c', 'd': 'room_fire_d'}
STATE_GATE = {'a': {'until': ['c3c_talk_konrad']}, 'b': {}, 'c': {'after': ['c3d_choose'], 'until': ['c3e_reach_konrad']},
              'd': {'after': ['c3e_reach_konrad']}}
# the gate of everything that belongs to one look (b = the base look: hidden once the fire starts)
LOOK_GATE = {'a': {'until': ['c3c_talk_konrad']}, 'b': {'after': ['c3c_talk_konrad'], 'until': ['c3d_choose']},
             'c': {'after': ['c3d_choose'], 'until': ['c3e_reach_konrad']}, 'd': {'after': ['c3e_reach_konrad']}}
ZBAND = {'b': -50, 'a': -48, 'c': -46, 'd': -44}
FADE = {'a': 0.15, 'b': 0.15, 'c': 0.8, 'd': 2.6}       # live transition into this look (s); cuts are instant
VARIANTS = {
    'a': [],
    'b': [('scarf_taken', {'scarf': False}, {'after': ['c3d_inspect_drawer']}),
          ('halves', {'halves': True}, {'after': ['c3d_talk_compare']})],
    'c': [('blatt7_pocketed', {'blatt7': False}, {'choice': {'c3d_choose': 'pocket_plan'}}),
          ('file_taken', {'file': False}, {'after': ['c3e_take_file']})],
    'd': [('blatt7_pocketed', {'blatt7': False}, {'choice': {'c3d_choose': 'pocket_plan'}}),
          ('case_broken', {'case_broken': True}, {'after': ['c3f_inspect_hose']}),
          ('desk_pushed', {'desk_pushed': True}, {'after': ['c3f_push_desk']})],
}
COL = {'warm': '#F0C487', 'cold': '#9FB4CC', 'white': '#E8E4DA', 'fire': '#F2A044', 'fire_deep': '#D8662A',
       'green': '#B8D49A'}
# dynamic Godot lights for the baked lights (energy, radius, height, flicker, colour) -- the bake carries the look
DYN = {
    'yard_lamp': (0.55, 150, 30, 0.0, 'warm'), 'lane_lamp': (0.3, 60, 10, 0.0, 'warm'),
    'yard_lit_window': (0.2, 60, 6, 0.0, 'warm'), 'booth_lamp': (0.7, 110, 16, 0.02, 'warm'),
    'desk_lamp': (0.45, 70, 10, 0.0, 'warm'), 'radio_dial': (0.2, 26, 4, 0.0, 'warm'),
    'exit_lamp': (0.4, 90, 14, 0.0, 'warm'), 'green_lamp': (0.95, 150, 12, 0.0, 'warm'),
    'torch': (1.1, 120, 10, 0.0, 'white'),
}
FIRE_DYN = {   # name: (pos, energy, radius, height, colour, slow-flicker amplitude, Hz <= 3)
    'c': [('fire_c17', (1704, 210), 0.75, 300, 40, 'fire', 0.2, 1.6), ('fire_magazin', (1830, 250), 0.5, 220, 34, 'fire', 0.22, 2.1),
          ('fire_planarchiv', (1410, 262), 0.5, 220, 30, 'fire', 0.24, 1.9), ('fire_front_c', (1248, 246), 0.8, 280, 36, 'fire', 0.22, 2.4)],
    'd': [('fire_rows', (810, 216), 0.7, 260, 40, 'fire', 0.22, 1.7), ('fire_bank', (1150, 206), 0.7, 280, 40, 'fire', 0.22, 2.2),
          ('fire_front_d', (702, 250), 0.8, 280, 36, 'fire', 0.24, 2.6), ('fire_table', (1000, 262), 0.4, 160, 24, 'fire_deep', 0.26, 2.0)],
}
FLAMES = {     # name: (x, y_bottom, w, h, seed, fuel spots [(x, width, strength)], height, frames, fps)
    'c': [('flames_front_c', 1222, 292, 52, 118, 31, [(14, 8, 1.0), (30, 10, 1.0), (44, 6, 0.8)], 0.95),
          ('flames_fallen', 1380, 296, 56, 34, 32, [(10, 6, 0.8), (26, 9, 1.0), (44, 6, 0.7)], 0.8),
          ('flames_chests', 1290, 248, 196, 30, 33, [(20, 10, 0.7), (70, 14, 0.9), (120, 10, 0.6), (170, 12, 0.8)], 0.7),
          ('flames_frame_a', 1288, 208, 30, 40, 34, [(15, 7, 0.9)], 0.9),
          ('flames_frame_b', 1402, 176, 30, 44, 39, [(15, 7, 1.0)], 0.9),
          ('flames_frame_c', 1478, 208, 30, 38, 40, [(15, 6, 0.8)], 0.9),
          ('flames_units', 1580, 290, 100, 150, 35, [(16, 10, 0.9), (52, 14, 1.0), (86, 10, 0.8)], 0.9),
          ('flames_c17', 1670, 292, 64, 190, 36, [(16, 8, 1.0), (34, 12, 1.0), (52, 8, 0.9)], 1.0),
          ('flames_shelves', 1746, 290, 118, 160, 37, [(16, 10, 0.8), (50, 12, 1.0), (90, 12, 0.9)], 0.9),
          ('flames_door', 1858, 292, 52, 80, 38, [(14, 8, 0.8), (36, 8, 0.7)], 0.8)],
    'd': [('flames_front_d', 676, 292, 52, 118, 41, [(14, 8, 1.0), (30, 10, 1.0), (44, 6, 0.8)], 0.95),
          ('flames_rows', 726, 292, 196, 160, 42, [(24, 10, 0.9), (84, 12, 1.0), (146, 12, 0.9), (180, 8, 0.6)], 0.9),
          ('flames_bank', 1068, 292, 178, 170, 43, [(20, 12, 0.8), (70, 14, 1.0), (120, 12, 0.9), (160, 10, 0.8)], 0.95),
          ('flames_table', 940, 268, 124, 34, 44, [(24, 10, 0.7), (60, 12, 0.9), (98, 10, 0.7)], 0.8)],
}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def record(path: str, gen: str, desc: str):
    PRODUCED.append((rel(path), gen, desc))


def save_arr(arr, path, gen, desc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)
    record(path, gen, desc)


def clean_env_dir():
    """Remove the PNGs this generator wrote last time (its provenance.json rows, tools/pixelgen/env_keep.py) so
    renamed / dropped files never linger; every other file of the shared folder stays (explore_hotspots.json, hand
    or walker art, the .import sidecars -- UIDs stay stable); scene.json and provenance.json are merged, not wiped."""
    if os.path.isdir(ENV_DIR):
        KEEP.remove_own_pngs(ENV_DIR, ROOT, FAMILY)


def gate_merge(*gs) -> dict:
    out: dict = {}
    for g in gs:
        for k in ('after', 'until'):
            if g.get(k):
                out.setdefault(k, [])
                for o in g[k]:
                    if o not in out[k]:
                        out[k].append(o)
        if g.get('choice'):
            out.setdefault('choice', {}).update(g['choice'])
    return out


# =========================================================================== bakes
def bake(cfg: dict):
    room = ER.Room(cfg)
    room.build()
    lights = room.all_lights()
    F = K.light_fields(room.lay, lights)
    K.add_pools(F, lights, L.FLOOR, L.WORLD_H, L.WORLD_W)
    K.resolve_state(room.lay, F, fire=room.fire > 0, exposure=0.78 if room.fire else 0.93)
    return room


def maps(room):
    lay = room.lay
    return lay.c.copy(), lay.normal_map(3.0), lay.em.copy()


def diff_box(a, b, pad=1):
    d = np.zeros(a[0].shape[:2], bool)
    for x, y in zip(a, b):
        d |= np.any(x != y, axis=-1)
    if not d.any():
        return None
    ys, xs = np.nonzero(d)
    y0, y1 = max(0, ys.min() - pad), min(L.WORLD_H, ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(L.WORLD_W, xs.max() + pad + 1)
    return x0, y0, x1, y1


def write_room(state, m, name, desc):
    c, n, e = m
    base = os.path.join(ENV_DIR, name)
    save_arr(c, base + '.png', 'env_c3p2_archive_room.py', desc)
    save_arr(n, base + '_n.png', 'env_c3p2_archive_room.py', desc + ' -- normal map (OpenGL +Y up)')
    has_e = bool(e[..., 3].any())
    if has_e:
        save_arr(e, base + '_e.png', 'env_c3p2_archive_room.py', desc + ' -- emission mask (unshaded glow)')
    return has_e


def write_patch(m, box, name, desc, hist_m=None):
    x0, y0, x1, y1 = box
    c, n, e = m
    base = os.path.join(ENV_DIR, 'patches', name)
    cc = c[y0:y1, x0:x1].copy()
    if (cc[..., 3] == 0).any():
        # patches are opaque crops; glass inside them stays transparent (outside.png shows through)
        pass
    save_arr(cc, base + '.png', 'env_c3p2_archive.py', desc)
    save_arr(n[y0:y1, x0:x1], base + '_n.png', 'env_c3p2_archive.py', desc + ' -- normal map')
    ee = e[y0:y1, x0:x1]
    has_e = bool(ee[..., 3].any())
    if hist_m is not None:
        hc, hn, he = hist_m
        save_arr(hc[y0:y1, x0:x1], base + '_hist.png', 'env_c3p2_archive.py',
                 desc + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
        save_arr(hn[y0:y1, x0:x1], base + '_hist_n.png', 'env_c3p2_archive.py', desc + ' -- historical, normal map')
        if has_e or bool(he[y0:y1, x0:x1][..., 3].any()):
            save_arr(he[y0:y1, x0:x1], base + '_hist_e.png', 'env_c3p2_archive.py', desc + ' -- historical, emission')
    if has_e:
        save_arr(ee, base + '_e.png', 'env_c3p2_archive.py', desc + ' -- emission mask')
    return has_e


# =========================================================================== scene
def build_scene(preview_dir=None):
    t0 = time.time()
    clean_env_dir()
    layers, props, decals, fx, lights = [], [], [], [], []
    rooms = {}
    hotspot_info = {}
    for st in ('b', 'a', 'c', 'd'):
        cfg = dict(STATES[st])
        room = bake(cfg)
        rooms[st] = room
        m = maps(room)
        desc = {'a': 'registry at night, before the green lamp is switched on (Konrad\'s torch in the aisle)',
                'b': 'registry at night: yard in the snow, Annahme, Karteisaal under the green lamp, Planarchiv, '
                     'Magazin',
                'c': 'registry on fire (C): smoke under the vaults, the Magazin and Planarchiv burning, ramp door '
                     'shut',
                'd': 'registry on fire (D): the fire in the Karteisaal, smoke low, ramp door shut'}[st]
        has_e = write_room(st, m, ROOM_FILE[st], desc)
        entry = {'name': ROOM_FILE[st], 'file': ROOM_FILE[st] + '.png', 'pos': [0, 0], 'parallax': [1, 1],
                 'z': ZBAND[st], 'normal': True, 'emission': has_e, 'emission_strength': 0.5, 'lit': True}
        if STATE_GATE[st]:
            entry.update(STATE_GATE[st])
            entry['fade'] = FADE[st]
        layers.append(entry)
        # insignia site (Magazin delegation plates): neutral crop + _hist crop of the same look
        hroom = bake(dict(cfg, hist=True))
        hm = maps(hroom)
        box = diff_box(m, hm, pad=2)
        if box is not None:
            nm = 'insignia_magazin_' + st
            he = write_patch(m, box, nm, 'Magazin delegation plates (look %s), neutral emblems' % st, hist_m=hm)
            d = {'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])], 'z': ZBAND[st] + 1,
                 'lit': True, 'normal': True, 'emission': he, 'hist_variant': 'patches/%s_hist.png' % nm}
            d.update(gate_merge(LOOK_GATE[st]))
            d['fade'] = FADE[st]
            decals.append(d)
        # story variants (cumulative inside the look)
        prev_cfg, prev_m = cfg, m
        for (vname, change, gate) in VARIANTS[st]:
            vcfg = dict(prev_cfg, **change)
            vroom = bake(vcfg)
            vm = maps(vroom)
            box = diff_box(prev_m, vm, pad=1)
            if box is None:
                print('  WARNING variant %s@%s changes nothing' % (vname, st))
                continue
            nm = '%s_%s' % (vname, st)
            he = write_patch(vm, box, nm, 'look %s with the story change "%s"' % (st, vname))
            d = {'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])], 'z': ZBAND[st] + 1,
                 'lit': True, 'normal': True, 'emission': he}
            d.update(gate_merge(LOOK_GATE[st], gate))
            d['fade'] = 0.35
            decals.append(d)
            prev_cfg, prev_m = vcfg, vm
    print('  rooms baked in %.1fs' % (time.time() - t0))

    # ---- outside (light wells) + guard life strip
    room = rooms['b']
    wells = EFX.light_wells(room.windows)
    save_arr(wells, os.path.join(ENV_DIR, 'outside.png'), 'env_c3p2_archive_fx.py',
             'light wells behind the high windows: snow heap, grating shadow, street-lamp glow (unlit)')
    layers.insert(0, {'name': 'outside', 'file': 'outside.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -60,
                      'normal': False, 'emission': False, 'lit': False})
    gw = [w_ for w_ in room.windows if abs((w_[0] + w_[2]) / 2 - 1220) < 4][0]
    gs = EFX.guard_feet_strip(gw[2] - gw[0], gw[3] - gw[1], 80)
    save_arr(gs, os.path.join(ENV_DIR, 'life', 'guard_feet.png'), 'env_c3p2_archive_fx.py',
             'a guard\'s boots passing the high window of the Karteisaal, turning, passing back (80 frames, 8 fps)')
    d = {'name': 'guard_feet', 'file': 'life/guard_feet.png', 'pos': [gw[0], gw[1]], 'z': -55, 'frames': 80,
         'fps': 8, 'lit': False, 'normal': False, 'emission': False,
         'note': 'between outside.png and the room layer: seen through the glass, behind the bars'}
    d.update(gate_merge({'until': ['c3d_choose']}))
    decals.append(d)

    tb = EFX.torch_beam()
    save_arr(tb, os.path.join(ENV_DIR, 'torch_beam.png'), 'env_c3p2_archive_fx.py',
             "Konrad's torch: soft cone of light into the aisle (look A, plain alpha)")
    e = {'name': 'torch_beam', 'file': 'torch_beam.png', 'pos': [878, 202], 'parallax': [1, 1], 'z': 11,
         'normal': False, 'emission': False, 'lit': False, 'fade': 0.15}
    e.update(LOOK_GATE['a'])
    layers.append(e)
    # ---- veils: night shafts, smoke of C and D
    sh = EFX.shafts(room.windows)
    save_arr(sh, os.path.join(ENV_DIR, 'shafts.png'), 'env_c3p2_archive_fx.py',
             'cold light falling from the high windows (soft veil, plain alpha)')
    e = {'name': 'shafts', 'file': 'shafts.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': 10, 'normal': False,
         'emission': False, 'lit': False, 'fade': 0.8}
    e.update({'until': ['c3d_choose']})
    layers.append(e)
    xs = np.arange(L.WORLD_W, dtype=np.float32)
    x0s = L.PIER[1]
    bot_c = np.interp(xs, [0, 404, 700, 1236, 1600, 1920], [0, 46, 70, 118, 150, 168])
    den_c = np.interp(xs, [0, 400, 404, 900, 1236, 1920], [0, 0, 0.35, 0.55, 0.85, 1.0])
    bot_d = np.interp(xs, [0, 404, 690, 1236, 1920], [0, 150, 186, 200, 214])
    den_d = np.interp(xs, [0, 400, 404, 690, 1920], [0, 0, 0.75, 0.95, 1.0])
    for (nm, bot, den, gl, gate, fade) in (
            ('smoke_c', bot_c, den_c, 1600, LOOK_GATE['c'], FADE['c']),
            ('smoke_d', bot_d, den_d, 1000, LOOK_GATE['d'], FADE['d'])):
        sm = EFX.smoke_layer(L.WORLD_W - x0s, 240, bot[x0s:], den[x0s:], seed=zlib.crc32(nm.encode()) % 1000, glow_x=gl,
                             glow_k=0.9, x_off=x0s)
        save_arr(sm, os.path.join(ENV_DIR, nm + '.png'), 'env_c3p2_archive_fx.py',
                 'smoke under the vaults (%s): sooty grey, lit orange from below near the fire' % nm)
        e = {'name': nm, 'file': nm + '.png', 'pos': [x0s, 0], 'parallax': [1, 1], 'z': 20, 'normal': False,
             'emission': False, 'lit': False, 'fade': fade}
        e.update(gate)
        layers.append(e)

    # ---- fg frame
    fg = EP.build_fg()
    issues = EP.check_clearance(fg, {**L.HOTSPOTS, **L.SPAWNS})
    if issues:
        print('  WARNING fg covers:', issues)
    save_arr(fg.c, os.path.join(ENV_DIR, 'fg_frame.png'), 'env_c3p2_archive_props.py',
             'foreground silhouettes (bollard, cast-iron columns, boxes, cables), parallax 1.25')
    layers.append({'name': 'fg_frame', 'file': 'fg_frame.png', 'pos': [0, 0], 'parallax': [EP.FG_PARALLAX, 1.0],
                   'z': 60, 'normal': False, 'emission': False, 'lit': False})

    # ---- props: the handcart (seal / no seal), neutral + _hist
    yard_lights = [lt for lt in room.all_lights() if lt['pos'][0] < 420]
    for seal, gate in ((True, {'until': ['c3c_inspect_crates']}), (False, {'after': ['c3c_inspect_crates']})):
        p = EP.build_cart(hist=True, seal=seal)
        EP.bake_prop(p, yard_lights, exposure=0.93)
        pb = os.path.join(ENV_DIR, 'props', p.name)
        save_arr(p.lay.c, pb + '.png', 'env_c3p2_archive_props.py', p.note)
        save_arr(p.lay.normal_map(3.0), pb + '_n.png', 'env_c3p2_archive_props.py', p.note + ' -- normal map')
        save_arr(p.hist_lay.c, pb + '_hist.png', 'env_c3p2_archive_props.py',
                 p.note + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
        save_arr(p.hist_lay.normal_map(3.0), pb + '_hist_n.png', 'env_c3p2_archive_props.py',
                 p.note + ' -- historical, normal map')
        e = {'name': p.name, 'file': 'props/%s.png' % p.name, 'pos': [p.x, p.y], 'base_y': p.base_y,
             'size': [p.w, p.h], 'collision': p.collision, 'normal': True, 'emission': False,
             'hist_variant': 'props/%s_hist.png' % p.name, 'fade': 0.3}
        e.update(gate)
        props.append(e)

    # ---- flames (decal strips with emission), per fire look
    for st in ('c', 'd'):
        for (nm, x, yb, w, h, seed, spots, hgt) in FLAMES[st]:
            rgba, em = EFX.flame_strip(w, h, seed, frames=16, spots=spots,
                                       base=0.0 if nm.startswith('flames_frame') else 0.15, height=hgt)
            base = os.path.join(ENV_DIR, 'fx', nm)
            save_arr(rgba, base + '.png', 'env_c3p2_archive_fx.py', 'flames (%s), 16 frames' % nm)
            save_arr(em, base + '_e.png', 'env_c3p2_archive_fx.py', 'flames (%s) -- emission strip' % nm)
            d = {'name': nm, 'file': 'fx/%s.png' % nm, 'pos': [x, yb - h], 'z': -40, 'frames': 16, 'fps': 10,
                 'lit': False, 'normal': False, 'emission': True, 'emission_strength': 0.55, 'fade': FADE[st]}
            d.update(LOOK_GATE[st] if st == 'd' else gate_merge({'after': ['c3d_choose']}))
            decals.append(d)
    # the ringing fire bell
    bs = EFX.bell_strip()
    save_arr(bs, os.path.join(ENV_DIR, 'fx', 'bell_ringing.png'), 'env_c3p2_archive_fx.py',
             'fire bell ringing: the striker against the dome (4 frames, small motion, no flashing)')
    d = {'name': 'bell_ringing', 'file': 'fx/bell_ringing.png', 'pos': [L.BELL[0] - 8, L.BELL[1] - 1], 'z': -42,
         'frames': 4, 'fps': 12, 'lit': True, 'normal': False, 'emission': False, 'after': ['c3d_choose'],
         'fade': 0.2}
    decals.append(d)

    # ---- fx strips
    def fxe(nm, arr, pos, frames, fps, z, gate, desc, fade=0.6, alpha=None):
        save_arr(arr, os.path.join(ENV_DIR, 'fx', nm + '.png'), 'env_c3p2_archive_fx.py', desc)
        e = {'type': 'anim_sprite', 'name': nm, 'file': 'fx/%s.png' % nm, 'frames': frames, 'fps': fps,
             'pos': [int(pos[0]), int(pos[1])], 'parallax': [1.0, 1.0], 'z': z, 'lit': False, 'fade': fade}
        if alpha is not None:
            e['alpha'] = alpha
        e.update(gate)
        fx.append(e)

    sw, sh_ = L.PIER[0] + 4, 296
    fxe('snow_yard', EFX.particles(sw, sh_, 24, 8, 150, 501, kind='snow', vy=(18, 30), vx=(4, 9), sway=3.0),
        (0, 0), 24, 8, 30, {}, 'falling snow over the yard (24 frames, 8 fps)')
    fxe('snow_gap', EFX.particles(64, 40, 24, 10, 26, 502, kind='snow', vy=(2, 10), vx=(18, 34), sway=1.5,
                                  spawn=lambda r: (r.uniform(0, 6), r.uniform(4, 38))),
        (L.DOOR[1] - 2, 258), 24, 10, 31, {'after': ['c3d_choose']},
        'snow blowing through the gaps of the shut ramp door', fade=0.4)
    fxe('dust_lamp', EFX.particles(84, 40, 32, 6, 20, 503, kind='dust', vy=(-2, 2), vx=(-2, 2), sway=2.0),
        (958, 232), 32, 6, 12, gate_merge(LOOK_GATE['b']), 'dust motes in the light of the green lamp', fade=0.3)
    # embers + ash
    for st, regions in (('c', [(1220, 1570), (1570, 1920)]), ('d', [(680, 970), (970, 1260)])):
        for i, (a, b) in enumerate(regions):
            w = b - a
            fxe('embers_%s%d' % (st, i), EFX.particles(w, 250, 24, 10, int(w * 0.16), 600 + i + ord(st), kind='ember',
                                                     vy=(-34, -14), vx=(-6, 8), sway=3.0,
                                                     spawn=lambda r, w=w: (r.uniform(0, w), r.uniform(150, 250))),
                (a, 40), 24, 10, 32, LOOK_GATE[st] if st == 'd' else {'after': ['c3d_choose']},
                'rising embers (look %s)' % st, fade=FADE[st])
    for st, regions in (('c', [(880, 1220), (1220, 1570), (1570, 1920)]), ('d', [(404, 690), (690, 975)])):
        for i, (a, b) in enumerate(regions):
            w = b - a
            fxe('ash_%s%d' % (st, i), EFX.particles(w, 260, 24, 8, int(w * 0.09), 700 + i + ord(st), kind='ash',
                                                  vy=(5, 12), vx=(-4, 2), sway=4.0, life=3.0,
                                                  spawn=lambda r, w=w: (r.uniform(0, w), r.uniform(0, 160))),
                (a, 30), 24, 8, 34, LOOK_GATE[st] if st == 'd' else {'after': ['c3d_choose']},
                'falling ash (look %s)' % st, fade=FADE[st])
    # smoke plumes + heat shimmer at the fire fronts, smoke from the service door and the ramp door gap
    for (nm, x, y, w, h, gate, glow, desc) in (
            ('plume_front_c', 1208, 60, 80, 220, {'after': ['c3d_choose']}, 0.8, 'smoke rising from the fire front (C)'),
            ('plume_service', 1850, 120, 64, 150, {'after': ['c3d_choose']}, 0.4, 'smoke pouring from the service stairs'),
            ('plume_front_d', 662, 70, 80, 214, LOOK_GATE['d'], 0.8, 'smoke rising from the fire front (D)'),
            ('plume_door', 372, 196, 34, 70, {'after': ['c3d_choose']}, 0.0, 'smoke squeezing out above the ramp door')):
        fxe(nm, EFX.smoke_wisp_strip(w, h, 16, zlib.crc32(nm.encode()) % 997, glow=glow), (x, y), 16, 8, 22, gate, desc,
            fade=FADE['d'] if 'front_d' in nm else 0.8)
    for (nm, x, y, w, gate, glow) in (('roll_c0', 1300, 70, 220, {'after': ['c3d_choose']}, 0.6),
                                      ('roll_c1', 960, 50, 220, LOOK_GATE['c'], 0.3),
                                      ('roll_c2', 620, 30, 200, LOOK_GATE['c'], 0.0),
                                      ('roll_d0', 860, 120, 240, LOOK_GATE['d'], 0.7),
                                      ('roll_d1', 520, 100, 220, LOOK_GATE['d'], 0.4)):
        fxe(nm, EFX.smoke_roll_strip(w, 70, 32, zlib.crc32(nm.encode()) % 983, speed=3, glow=glow), (x, y), 32, 6,
            21, gate, 'smoke rolling along under the vaults toward the Annahme', fade=FADE['d'] if '_d' in nm else 0.8)
    for (nm, x, gate) in (('heat_c', 1218, {'after': ['c3d_choose']}), ('heat_d', 672, LOOK_GATE['d'])):
        fxe(nm, EFX.heat_strip(60, 120, 16, zlib.crc32(nm.encode()) % 991), (x, 150), 16, 10, -39, gate,
            'heat shimmer above the fire front', fade=0.8)

    # ---- lights
    def dyn_entry(lt, nm, gate, energy_k=1.0, flicker=0.0, slow=None):
        if nm.startswith('win_'):
            e_, r_, h_, fl_, kind = 0.32, 120, 24, 0.0, 'cold'
        else:
            e_, r_, h_, fl_, kind = DYN[nm]
        e = {'name': nm, 'pos': [int(round(lt['pos'][0])), int(round(lt['pos'][1]))], 'color': COL[kind],
             'energy': round(e_ * energy_k, 3), 'radius': r_, 'flicker': flicker or fl_, 'height': h_,
             'on_layer': 'playfield'}
        if slow:
            e['flicker_slow'], e['flicker_hz'] = slow
        e.update(gate)
        return e
    # always-on practical lights (from the night look)
    for lt in rooms['b'].lights:
        nm = lt['name']
        if nm in ('yard_lamp', 'lane_lamp', 'yard_lit_window', 'booth_lamp', 'radio_dial', 'exit_lamp'):
            lights.append(dyn_entry(lt, nm, {}))
        elif nm == 'desk_lamp':
            lights.append(dyn_entry(lt, nm, {'until': ['c3f_push_desk']}))
        elif nm.startswith('win_'):
            lights.append(dyn_entry(lt, nm, {'until': ['c3d_choose'], 'fade': 0.8}))
    for lt in rooms['d'].lights:
        if lt['name'] == 'desk_lamp':
            e = dyn_entry(dict(lt, pos=(lt['pos'][0] + L.DESK_PUSH, lt['pos'][1])), 'desk_lamp',
                          {'after': ['c3f_push_desk']})
            e['name'] = 'desk_lamp_pushed'
            lights.append(e)
    for lt in rooms['b'].lights:
        if lt['name'] == 'green_lamp':
            lights.append(dyn_entry(lt, 'green_lamp', dict(LOOK_GATE['b'], fade=0.15)))
            e = dyn_entry(lt, 'green_lamp', dict(LOOK_GATE['c'], fade=0.8), energy_k=0.8, slow=(0.22, 2.4))
            e['name'] = 'green_lamp_flicker'
            lights.append(e)
    for lt in rooms['a'].lights:
        if lt['name'] == 'torch':
            lights.append(dyn_entry(lt, 'torch', dict(LOOK_GATE['a'], fade=0.15)))
    for st in ('c', 'd'):
        for (nm, pos, en, rad, hgt, col, amp, hz) in FIRE_DYN[st]:
            e = {'name': nm, 'pos': list(pos), 'color': COL[col], 'energy': en, 'radius': rad, 'flicker': 0.0,
                 'height': hgt, 'on_layer': 'playfield', 'flicker_slow': amp, 'flicker_hz': hz, 'fade': FADE[st]}
            e.update(LOOK_GATE[st] if st == 'd' else {'after': ['c3d_choose']})
            lights.append(e)

    # ---- hotspot info (which painted object each story hotspot belongs to)
    for k, (what, span) in L.HOTSPOT_PROPS.items():
        hotspot_info[k] = {'kind': 'story', 'stand': list(L.HOTSPOTS[k]), 'what': what, 'span': list(span)}

    scene = {
        'id': 'veltrava_registry', 'palette': 'registry',
        'world_size': [L.WORLD_W, L.WORLD_H],
        'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]},
        'canvas_modulate': '#CED4DC',
        'layers': layers,
        'props': props,
        'decals': decals,
        'lights': lights,
        'fx': fx,
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]],
                     [L.WALK_X[1], L.WALK_BAND[1]], [L.WALK_X[0], L.WALK_BAND[1]]],
        'spawns': {k: list(v) for k, v in L.SPAWNS.items()},
        'hotspots': {k: list(v) for k, v in L.HOTSPOTS.items()},
        'blockers': [dict(b) for b in L.BLOCKERS],
        'zones': {k: list(v) for k, v in L.ROOMS.items()},
        # ---- registry extensions (read by scripts/levels/c3p2_archive/registry_level.gd)
        'looks': [
            {'name': 'night', 'canvas_modulate': '#CED4DC', 'grade': 'registry'},
            {'name': 'fire', 'after': ['c3d_choose'], 'canvas_modulate': '#D9CBC0', 'grade': 'registry_fire',
             'fade': 0.8},
        ],
        'hotspot_info': hotspot_info,
        'gates_doc': ('Entries with "after" (objectives that must be complete), "until" (hidden once one of them is '
                      'complete) or "choice" ({objective: choice id | "!id"}) are built by registry_level.gd and '
                      'shown while the condition holds; "fade" = seconds of the live cross-fade (instant at load, '
                      'switch cuts and while the level is hidden). An objective of a scene before the one the level '
                      'plays counts as complete; inside a memory only those count. c3d_choose (the fire starts in '
                      'LS_C3_Fire) shows its look only once the level is hidden by the cinematic or the scene is C.'),
        'notes': [
            'Side view like L_C3_Hall: feet line y 300, walk band 296-306, x 18-1902.',
            'Four looks: A (lamp off, torch), B (green lamp), C (fire in Magazin/Planarchiv, smoke), D (fire in the '
            'Karteisaal). Each look is one opaque room layer + patches; flames, embers, ash, smoke are FX strips.',
            'Insignia: props/cart*.png (railway stencil on the crates) and patches/insignia_magazin_*.png '
            '(delegation plates in the Magazin) have *_hist variants; layer_stack resolves them via Symbols.pick.',
            'No story character is painted into the art; the partner stands at the switch spawns.',
            'Sprinkler-less 1964 cellar: fire case with hose and axe, bucket stand, extinguisher, an electric fire '
            'bell (rings from the fire on), a sliding steel fire door at the service stairs (wedged open in C/D).',
        ],
        'meta': {'mode': 'side', 'feet_y': L.WALK_Y, 'generator': 'tools/pixelgen/env_c3p2_archive.py',
                 'date': K.DATE, 'palette_ramps': K.REG},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    scene = KEEP.merge_scene(scene, KEEP.read_json(sj))     # keys / "actors" other writers added stay in place
    KEEP.write_json(sj, scene)   # same content as before: the file stays byte for byte
    record(sj, 'env_c3p2_archive.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1 + the registry gates)')

    # ---- checks
    for st, r_ in rooms.items():
        n, bad = K.palette_report(r_.lay.c)
        if bad:
            print('  WARNING room %s uses non-palette colours: %s' % (st, bad[:6]))
    for note in K.check_c3_palette():
        print('  NOTE', note)
    print('  scene built in %.1fs' % (time.time() - t0))
    if preview_dir:
        preview(scene, preview_dir)
    return scene


# =========================================================================== preview (layers + decals frame 0)
def preview(scene, out_dir, looks=('a', 'b', 'c', 'd')):
    os.makedirs(out_dir, exist_ok=True)
    W, H = L.WORLD_W, L.WORLD_H

    def load(p):
        return np.asarray(Image.open(os.path.join(ENV_DIR, p)).convert('RGBA'))

    def over(dst, src, x, y, frames=1, alpha=1.0):
        h, w = src.shape[:2]
        w //= frames
        s = src[:, :w].astype(np.float32)
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        sub = s[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4] / 255.0 * alpha
        dst[Y0:Y1, X0:X1, :3] = dst[Y0:Y1, X0:X1, :3] * (1 - a) + sub[..., :3] * a

    done = {'b': set(), 'a': {'c3c_inspect_crates'}, 'c': {'c3c_talk_konrad', 'c3d_choose', 'c3c_inspect_crates'},
            'd': {'c3c_talk_konrad', 'c3d_choose', 'c3e_reach_konrad', 'c3c_inspect_crates'}}
    done['b'] = {'c3c_talk_konrad', 'c3c_inspect_crates'}

    def holds(e, st):
        for o in e.get('after', []):
            if o not in done[st]:
                return False
        for o in e.get('until', []):
            if o in done[st]:
                return False
        return not e.get('choice')

    for st in looks:
        img = np.zeros((H, W, 3), np.float32)
        items = []
        for e in scene['layers']:
            if holds(e, st) and e['name'] != 'fg_frame':
                items.append((e['z'], 0, e['file'], e['pos'], 1, e.get('alpha', 1.0)))
        for e in scene['decals']:
            if holds(e, st):
                items.append((e.get('z', 0), 1, e['file'], e['pos'], e.get('frames', 1), 1.0))
        for e in scene['props']:
            if holds(e, st):
                items.append((0, 2, e['file'], e['pos'], 1, 1.0))
        for e in scene['fx']:
            if holds(e, st):
                items.append((e.get('z', 0), 3, e['file'], e['pos'], e.get('frames', 1), e.get('alpha', 1.0)))
        for (_z, _k, f, pos, fr, al) in sorted(items, key=lambda t: (t[0], t[1])):
            over(img, load(f), int(pos[0]), int(pos[1]), fr, al)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(out_dir, 'look_%s.png' % st))
    print('  preview written to', out_dir)


# =========================================================================== provenance
def write_provenance():
    files = [{'path': p, 'generator': 'tools/pixelgen/' + g, 'content': d} for p, g, d in sorted(PRODUCED)]
    p = os.path.join(ENV_DIR, 'provenance.json')
    files = KEEP.merge_rows(files, KEEP.read_json(p), FAMILY, ROOT)   # rows of other generators stay
    out = {'generator': 'tools/pixelgen/env_c3p2_archive.py (+ _kit, _layout, _room, _props, _fx)',
           'date': K.DATE,
           'licence': 'project-owned original artwork, generated procedurally; no copied, traced, downloaded or '
                      'AI-generated pixels; bitmap fonts from env_veltrava_hall_kit.py (hand-defined)',
           'run': 'py -3 -P tools/pixelgen/env_c3p2_archive.py',
           'files': files}
    with open(p, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


def main(argv):
    t0 = time.time()
    prev = None
    for a in argv:
        if a.startswith('--preview'):
            prev = a.split('=', 1)[1] if '=' in a else os.path.join(ENV_DIR, '_preview')
    print('[env_c3p2_archive] scene ...')
    build_scene(prev)
    write_provenance()
    # Godot's .import twins of PNGs this run no longer produces (renamed / dropped strips) would linger
    for root, _dirs, files in os.walk(ENV_DIR):
        for f in files:
            if f.endswith('.png.import') and not os.path.exists(os.path.join(root, f[:-len('.import')])):
                os.remove(os.path.join(root, f))
    print('[env_c3p2_archive] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
