"""env_berlin -- generator for the env_berlin area of ASHES OF EMPIRES: THE LAST WINTER.

Run:  py -3 -P tools/pixelgen/env_berlin.py            (deterministic, no network)

Produces
* assets/environments/berlin_archive/   scene M1 'Berliner Bauarchiv' (round 2: arrival hall + porter's lodge,
                                        reading room & library, office, archive, light-table room, Emil's
                                        counter): layers, props, actor sheets, insignia decals, scene.json,
                                        previews in _preview/ (git/Godot-ignored)
* assets/ui/documents/berlin_*.png/json plan documents for the overlay puzzle + Emil's slip (+ _hist variants)
* documentation/asset_manifest_parts/env_berlin.md   provenance of every produced file
Optional flags: --scene-only, --docs-only, --no-preview
(The X1/match-cut stills of env_berlin_stills.py now belong to the transition work and are NOT rebuilt here;
 run `--stills` only if you own them.)
Shared folder (round 10, env_keep.py): a run deletes nothing (it only writes its own files, so walkers/ and walkers.json
of walkers_r8.py / the feel passes stay) and merges scene.json over the old one -- the round-8 "actors" entry
AmbientWalkers and any key added by hand stay, an unchanged scene.json stays byte for byte; the plan document JSON and
the manifest part are written with LF on every platform (byte-identical re-runs, .gitattributes).
"""
from __future__ import annotations

import copy
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import env_berlin_kit as kit          # noqa: E402
import env_berlin_layout as L         # noqa: E402
import env_keep as KEEP               # noqa: E402  (round 10: the folder is shared)
import pg                             # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'berlin_archive')
PREV_DIR = os.path.join(ENV_DIR, '_preview')
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')
MANIFEST = os.path.join(ROOT, 'documentation', 'asset_manifest_parts', 'env_berlin.md')

PRODUCED: list[tuple[str, str, str]] = []   # (relative path, generator, description)

LIGHT_COLORS = {'warm': '#F0C487', 'cold': '#A7BCCB', 'green': '#8FC79A', 'white': '#E3ECEA'}
# dynamic (Godot) light energies are lower than the baked ones: the art already carries the bake.
# name: (energy, radius, height, flicker)
DYN = {
    'window_1': (0.55, 150, 40, 0.0), 'window_2': (0.55, 150, 40, 0.0), 'window_3': (0.55, 150, 40, 0.0),
    'window_h1': (0.5, 140, 40, 0.0), 'window_l1': (0.55, 150, 40, 0.0), 'window_l2': (0.55, 150, 40, 0.0),
    'corridor_glass': (0.25, 56, 8, 0.03), 'lamp_konrad': (0.95, 112, 24, 0.02),
    'lamp_typist': (0.55, 84, 18, 0.03), 'archive_pendant': (0.85, 118, 28, 0.02),
    'archive_sconce': (0.5, 76, 16, 0.05), 'light_table': (0.7, 92, 6, 0.0), 'lamp_emil': (0.8, 90, 10, 0.02),
    'stair_glass': (0.3, 64, 8, 0.03), 'lodge_lamp': (0.85, 92, 14, 0.03), 'hall_pendant': (0.55, 130, 40, 0.02),
    'lib_pendant_1': (0.5, 126, 40, 0.02), 'lib_pendant_2': (0.5, 126, 40, 0.02),
    'lib_pendant_3': (0.5, 126, 40, 0.02), 'lib_sconce': (0.45, 76, 16, 0.05),
    'lamp_librarian': (0.75, 86, 10, 0.02), 'read_lamp_1': (0.75, 82, 10, 0.02), 'read_lamp_2': (0.75, 82, 10, 0.02),
}
CANVAS_MODULATE = '#C4CCD2'


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def record(path: str, gen: str, desc: str):
    PRODUCED.append((rel(path), gen, desc))


def save_layer(lay, base: str, normal=True, gen='env_berlin_room.py', desc=''):
    os.makedirs(os.path.dirname(base), exist_ok=True)
    info = lay.save(base, normal=normal)
    record(base + '.png', gen, desc)
    if normal:
        record(base + '_n.png', gen, desc + ' -- normal map (OpenGL +Y up)')
    if info['emission']:
        record(base + '_e.png', gen, desc + ' -- emission mask (unshaded glow)')
    return info


def save_crop(arr, rect, path):
    x, y, w, h = rect
    kit.save_rgba(np.ascontiguousarray(arr[y:y + h, x:x + w]), path)


# =========================================================================== insignia decals
def build_decals(room, ext):
    """Bake the room (and ext_near) a second time with the historical insignia and cut both variants of every
    insignia site into decal sprites: decal_<site>.png (neutral) / decal_<site>_hist.png."""
    import env_berlin_room as ER
    import env_berlin_ext as EX
    adir = os.path.join(ENV_DIR, 'decals')
    os.makedirs(adir, exist_ok=True)
    decals = []
    # ---- room sites (lit, with normal maps): the whole room is painted again with hist=True and baked with
    #      the same lights, so everything painted over a site later (conduits, shadows) matches exactly
    import env_berlin_props as EP
    room_h = ER.Room(hist=True)
    room_h.build()
    prop_lights = [lt for p in EP.build_all() for lt in p.lights]
    ER.bake(room_h, extra_lights=prop_lights)
    hl = room_h.lay
    n_neu = room.lay.normal_map(3.0)
    n_his = hl.normal_map(3.0)
    diff = np.any(room.lay.c != hl.c, axis=-1)
    covered = np.zeros_like(diff)
    for name, (x, y, w, h, painter) in room.decal_sites.items():
        covered[y:y + h, x:x + w] = True
        for suf, arr, nrm in (('', room.lay.c, n_neu), ('_hist', hl.c, n_his)):
            p = os.path.join(adir, 'decal_%s%s.png' % (name, suf))
            save_crop(arr, (x, y, w, h), p)
            save_crop(nrm, (x, y, w, h), p[:-4] + '_n.png')
            record(p, 'env_berlin.py', 'insignia site %s, %s variant' % (name, 'historical' if suf else 'neutral'))
            record(p[:-4] + '_n.png', 'env_berlin.py', 'insignia site %s -- normal map' % name)
        decals.append({'name': 'insignia_' + name, 'file': 'decals/decal_%s.png' % name, 'pos': [x, y],
                       'layer': 'room', 'z': 1, 'lit': True, 'normal': True,
                       'note': 'insignia site (12.4): neutral file; Symbols.pick -> decal_%s_hist.png' % name})
    leak = int((diff & ~covered).sum())
    if leak:
        print('  WARNING hist bake differs outside the decal sites: %d px' % leak)
    # ---- exterior banners (unlit, parallax of ext_near)
    near = ext['ext_near']
    sites = list(EX.NEAR_SITES)
    hn = EX.build_near(hist=True)
    diff_n = np.any(near.c != hn.c, axis=-1)
    cov_n = np.zeros_like(diff_n)
    for (name, (x, y, w, h), args) in sites:
        cov_n[y:y + h, x:x + w] = True
    if (diff_n & ~cov_n).any():
        print('  WARNING hist ext_near differs outside the banner sites: %d px' % int((diff_n & ~cov_n).sum()))
    for (name, (x, y, w, h), args) in sites:
        for suf, arr in (('', near.c), ('_hist', hn.c)):
            p = os.path.join(adir, 'decal_%s%s.png' % (name, suf))
            save_crop(arr, (x, y, w, h), p)
            record(p, 'env_berlin.py', 'facade banner %s, %s variant' % (name, 'historical' if suf else 'neutral'))
        decals.append({'name': 'insignia_' + name, 'file': 'decals/decal_%s.png' % name, 'pos': [x, y],
                       'layer': 'ext_near', 'z': 1, 'lit': False, 'normal': False,
                       'note': 'facade banner (12.4), local coords of ext_near; Symbols.pick -> _hist'})
    return decals


# =========================================================================== scene
def build_scene(preview=True):
    import env_berlin_room as ER
    import env_berlin_props as EP
    import env_berlin_ext as EX
    import env_berlin_fg as EF
    import env_berlin_fx as EFX
    import env_berlin_actors as EA
    t0 = time.time()
    room = ER.Room()
    room.build()
    props = EP.build_all()
    prop_lights = [lt for p in props for lt in p.lights]
    ER.bake(room, extra_lights=prop_lights)
    for p in props:
        EP.bake_prop(p, room.all_lights, shaft_air=room.shaft_air)
    ext = EX.build_all()
    fg = EF.build()
    shafts = build_shaft_overlay(room)
    fx_files, fx_entries = EFX.build_all(ENV_DIR, room)
    for (fp, desc) in fx_files:
        record(fp, 'env_berlin_fx.py', desc)
    decals = build_decals(room, ext)
    outer = EA.win_outer_layer()
    act_files, actors = EA.build_all(ENV_DIR, room)
    for (fp, desc) in act_files:
        record(fp, 'env_berlin_actors.py', desc)
    print('  scene built in %.1fs' % (time.time() - t0))

    # ---- save
    os.makedirs(ENV_DIR, exist_ok=True)
    kit.ensure_gdignore(PREV_DIR)
    layers = []
    for name, lay in (('ext_sky', ext['ext_sky']), ('ext_far', ext['ext_far']), ('ext_near', ext['ext_near'])):
        info = save_layer(lay, os.path.join(ENV_DIR, name), normal=False, gen='env_berlin_ext.py',
                          desc={'ext_sky': 'Berlin winter dusk sky (seen through windows)',
                                'ext_far': 'far city, smoke and the fictional Great Hall dome (muted, hazy)',
                                'ext_near': 'Gruenderzeit tenements across the street, state banners (neutral), '
                                            'tram contact wires, street lamps'}[name])
        layers.append({'name': name, 'file': name + '.png', 'pos': [0, 0],
                       'parallax': [L.PARALLAX[name], L.PARALLAX[name]],
                       'z': {'ext_sky': -100, 'ext_far': -95, 'ext_near': -90}[name],
                       'normal': False, 'emission': info['emission'], 'lit': False, 'repeat_x': 0})
    save_layer(outer, os.path.join(ENV_DIR, 'win_outer'), normal=False, gen='env_berlin_actors.py',
               desc='outer stone window sills with snow (behind the glass; the pigeons sit here)')
    layers.append({'name': 'win_outer', 'file': 'win_outer.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -60,
                   'normal': False, 'emission': False, 'lit': False})
    info = save_layer(room.lay, os.path.join(ENV_DIR, 'room'), gen='env_berlin_room.py',
                      desc='interior: arrival hall + porter\'s lodge, reading room & library, office, archive hall, '
                           'light-table room, issue counter (neutral insignia; hist variants are decals)')
    layers.append({'name': 'room', 'file': 'room.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -50,
                   'normal': True, 'emission': info['emission'], 'lit': True})
    save_layer(shafts, os.path.join(ENV_DIR, 'shafts'), normal=False, gen='env_berlin.py',
               desc='volumetric daylight-shaft veil (soft alpha, additive blend hint)')
    layers.append({'name': 'shafts', 'file': 'shafts.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': 10,
                   'normal': False, 'emission': False, 'lit': False, 'blend': 'add',
                   'note': 'soft alpha veil (max ~18%); additive preferred, plain alpha acceptable'})
    save_layer(fg, os.path.join(ENV_DIR, 'fg_frame'), normal=False, gen='env_berlin_fg.py',
               desc='foreground framing silhouettes (columns, plants, desk, chair, hanging lamps)')
    layers.append({'name': 'fg_frame', 'file': 'fg_frame.png', 'pos': [0, 0],
                   'parallax': [L.PARALLAX['fg_frame'], 1.0], 'z': 60, 'normal': False,
                   'emission': False, 'lit': False})
    prop_entries = []
    for p in props:
        info = save_layer(p.lay, os.path.join(ENV_DIR, 'props', p.name), gen='env_berlin_props.py', desc=p.note)
        prop_entries.append({'name': p.name, 'file': 'props/%s.png' % p.name, 'pos': [p.x, p.y],
                             'base_y': p.base_y, 'size': [p.w, p.h], 'normal': True,
                             'emission': info['emission']})

    # ---- lights for Godot (dynamic, subtler than the bake)
    lights = []
    for lt in room.all_lights:
        name = lt.get('name', '')
        if name not in DYN:
            continue
        e, r, h, fl = DYN[name]
        lights.append({'name': name, 'pos': [int(round(lt['pos'][0])), int(round(lt['pos'][1]))],
                       'color': LIGHT_COLORS[lt['kind']], 'energy': e, 'radius': r, 'flicker': fl,
                       'height': h, 'on_layer': 'playfield'})
    missing = sorted(set(DYN) - {l['name'] for l in lights})
    if missing:
        print('  WARNING dynamic lights without a baked source:', missing)
    glass_rects = [[a, L.win_y(a)[0], b - a, L.win_y(a)[1] - L.win_y(a)[0]] for (a, b) in L.ALL_WINDOWS]
    scene = {
        'id': 'berlin_archive', 'palette': 'archive', 'palette_exterior': 'berlin',
        'world_size': [L.WORLD_W, L.WORLD_H],
        'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]},
        'canvas_modulate': CANVAS_MODULATE,
        'layers': layers,
        'props': prop_entries,
        'walkable': [[18, L.WALK_BAND[0]], [L.WORLD_W - 18, L.WALK_BAND[0]],
                     [L.WORLD_W - 18, L.WALK_BAND[1]], [18, L.WALK_BAND[1]]],
        'spawns': {k: list(v) for k, v in L.SPAWNS.items()},
        'hotspots': {k: list(v) for k, v in L.HOTSPOTS.items()},
        'lights': lights,
        'fx': fx_entries,
        'decals': decals,
        'actors': actors,
        # ---- extension data (not required by the level contract; safe to ignore)
        'npcs': L.NPCS,
        'interaction': {k: {'approach': list(L.APPROACH[k][0]), 'facing': L.APPROACH[k][1],
                            'focus': list(L.FOCUS[k])} for k in L.HOTSPOTS},
        'windows': {'glass_rects': glass_rects, 'note': 'room.png is transparent here; ext_* layers show through'},
        'rooms': {'hall': list(L.HALL), 'library': list(L.LIBRARY), 'office': list(L.OFFICE),
                  'archive': list(L.ARCHIVE), 'lightroom': list(L.LIGHTROOM), 'emil': list(L.EMIL)},
        'meta': {'mode': 'side', 'feet_y': L.WALK_Y, 'generator': 'tools/pixelgen/env_berlin.py',
                 'date': kit.DATE, 'first_slice_offset_x': L.OFF,
                 'entry_spawn': 'SP_M1_Arrival',
                 'insignia': 'neutral art in the layers; "decals" (layer_stack) swap to *_hist via Symbols.pick',
                 'shafts_blend': 'shafts.png is meant for additive/screen blending; '
                                 'with plain alpha it reads as dithered motes'},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    scene = KEEP.merge_scene(scene, KEEP.read_json(sj))   # keeps the AmbientWalkers actor (round 8) and later keys
    KEEP.write_json(sj, scene)   # same content as before: the file stays byte for byte
    record(sj, 'env_berlin.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1, 12.2 hotspots, actors)')

    # ---- checks
    issues = EF.check_clearance(fg)
    if issues:
        print('  WARNING fg covers hotspots:', issues)
    allowed = {h.upper() for h in kit.archive_palette_hex()}
    for nm, lay in [('room', room.lay)] + [(p.name, p.lay) for p in props] + [('fg', fg)]:
        n, bad = kit.palette_report(lay.c, allowed)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    allowed_b = {h.upper() for h in kit.berlin_palette_hex()} | {h.upper() for h in [
        '#2A2130', '#2C4440', '#454E58', '#3E5D55', '#5F6973', '#2A1B16', '#7A2A26', '#A8382E']}
    for nm, lay in list(ext.items()) + [('win_outer', outer)]:
        n, bad = kit.palette_report(lay.c, allowed_b)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    check_hotspots(scene)
    if preview:
        previews(scene)
    return scene


def check_hotspots(scene):
    need = ['exp_lib_shelf_%d' % i for i in range(1, 6)] + [
        'exp_lib_hidden', 'exp_card_catalogue', 'exp_librarian_desk', 'exp_reading_table', 'exp_globe',
        'exp_poster_aufbau', 'exp_photo', 'exp_master_plan', 'exp_pneumatic_tube', 'exp_radio', 'exp_mouse',
        'exp_pigeons', 'exp_coat_stand', 'exp_porter', 'exp_clock', 'exp_heater',
        'plan_a', 'plan_b', 'overlay_table', 'emil', 'obs_window', 'obs_photo', 'obs_notice']
    hs = scene['hotspots']
    miss = [n for n in need if n not in hs]
    assert not miss, miss
    assert 'SP_M1_Arrival' in scene['spawns'] and 'SP_M1_Office' in scene['spawns']
    xs = sorted((v[0], k) for k, v in hs.items() if k != 'emil')
    for (a, ka), (b, kb) in zip(xs[:-1], xs[1:]):
        if b - a < 36:
            print('  NOTE hotspots close together: %s (%d) / %s (%d)' % (ka, a, kb, b))
    for k, (x, y) in hs.items():
        if k == 'emil':
            continue
        assert L.WALK_BAND[0] <= y <= L.WALK_BAND[1] and 18 <= x <= L.WORLD_W - 18, (k, x, y)
    print('  hotspots ok: %d (%d exploration)' % (len(hs), sum(1 for k in hs if k.startswith('exp_'))))


def build_shaft_overlay(room):
    """Volumetric daylight veil for additive (or plain alpha) blending above the playfield.
    Low alpha (max ~18 %%) so actors walking through the shafts are brightened, not hidden; the
    post-process palette snap turns it into ordered dither in-engine."""
    air = room.shaft_air
    H, W = air.shape
    lay = pg.Layer(W, H, 'shafts')
    y = np.arange(H, dtype=np.float32)[:, None]
    fade = np.clip((L.FLOOR + 30 - y) / 50, 0, 1) * np.clip((y - (L.WIN_Y[0] - 10)) / 40, 0, 1)
    a = (np.clip(air, 0, 1) ** 1.25) * fade
    # keep the window glass itself clear (the view must not grey out)
    for (x0, x1) in L.ALL_WINDOWS:
        wy0, wy1 = L.win_y(x0)
        a[wy0 - 8:wy1 + 2, x0 - 6:x1 + 6] *= 0.0
    alpha = np.clip(np.round(a * 46), 0, 255).astype(np.uint8)
    col = pg.hx('#A7BCCB')
    lay.c[..., 0], lay.c[..., 1], lay.c[..., 2] = col[0], col[1], col[2]
    lay.c[..., 3] = alpha
    lay.c[alpha == 0] = 0
    return lay


# =========================================================================== previews (python composite, dev aid)
def hexc(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32) / 255.0


def compose(scene, cx, lit=False, symbols=False):
    out = np.zeros((L.VIEW_H, L.VIEW_W, 3), np.float32)
    mod = hexc(scene['canvas_modulate'])
    items = []
    for ly in scene['layers']:
        items.append((ly['z'], 0, 'layer', ly))
    for pr in scene['props']:
        items.append((0, pr['base_y'], 'prop', pr))
    for fx in scene.get('fx', []):
        if fx.get('type') == 'anim_sprite':
            items.append((fx.get('z', -20), 0, 'fx', fx))
    zl = {ly['name']: ly['z'] for ly in scene['layers']}
    par = {ly['name']: ly['parallax'][0] for ly in scene['layers']}
    for dc in scene.get('decals', []):
        items.append((zl.get(dc.get('layer'), 0) + 0.5, 0, 'decal', dc))
    items.sort(key=lambda t: (t[0], t[1]))

    def blit(img_path, x, y, is_lit, normal_path=None, emis_path=None, additive=False, frames=1):
        im = np.asarray(Image.open(img_path).convert('RGBA'), np.float32) / 255.0
        if frames > 1:
            im = im[:, :im.shape[1] // frames]
        h, w = im.shape[:2]
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(L.VIEW_W, x + w), min(L.VIEW_H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        sub = im[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4] > 0.5
        col = sub[..., :3]
        if additive:
            out[Y0:Y1, X0:X1] = np.clip(out[Y0:Y1, X0:X1] + col * sub[..., 3:4], 0, 1)
            return
        if lit and is_lit:
            shade = np.ones_like(col) * mod
            if normal_path and os.path.exists(normal_path):
                nm = np.asarray(Image.open(normal_path).convert('RGB'), np.float32)[Y0 - y:Y1 - y, X0 - x:X1 - x]
                N = nm / 127.5 - 1.0
            else:
                N = np.zeros_like(col); N[..., 2] = 1
            ys, xs = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
            wx, wy = xs + cx, ys
            for lt in scene['lights']:
                lx, lyy = lt['pos']
                if abs(lx - cx - 320) > 460:
                    continue
                dx = lx - wx; dyu = -(lyy - wy); dz = float(lt['height'])
                d2 = np.sqrt(dx * dx + dyu * dyu)
                d3 = np.sqrt(dx * dx + dyu * dyu + dz * dz) + 1e-6
                ndl = np.clip((N[..., 0] * dx + N[..., 1] * dyu + N[..., 2] * dz) / d3, 0, 1)
                att = np.clip(1 - d2 / lt['radius'], 0, 1) ** 1.5
                shade += (hexc(lt['color']) * lt['energy'])[None, None, :] * (ndl * att)[..., None]
            col = col * shade
            if emis_path and os.path.exists(emis_path):
                em = np.asarray(Image.open(emis_path).convert('RGBA'), np.float32)[Y0 - y:Y1 - y, X0 - x:X1 - x] / 255
                e = em[..., 3:4] > 0.5
                col = np.where(e, em[..., :3], col)
        out[Y0:Y1, X0:X1] = np.where(a, col, out[Y0:Y1, X0:X1])

    for z, _, kind, d in items:
        if kind == 'layer':
            px_ = d['parallax'][0]
            x = int(round(d['pos'][0] - cx * px_))
            base = os.path.join(ENV_DIR, d['file'][:-4])
            blit(base + '.png', x, d['pos'][1], d.get('lit', False), base + '_n.png', base + '_e.png',
                 additive=(d.get('blend') == 'add'))
        elif kind == 'fx':
            pxp = d['parallax'][0] if isinstance(d['parallax'], list) else d['parallax']
            blit(os.path.join(ENV_DIR, d['file']), int(round(d['pos'][0] - cx * pxp)), d['pos'][1], False,
                 frames=int(d.get('frames', 1)))
        elif kind == 'decal':
            f = d['file']
            if symbols:
                f = f[:-4] + '_hist.png'
            pxp = float(par.get(d.get('layer'), 1.0))
            base = os.path.join(ENV_DIR, f[:-4])
            blit(base + '.png', int(round(d['pos'][0] - cx * pxp)), d['pos'][1], d.get('lit', False),
                 base + '_n.png' if d.get('normal') else None)
        else:
            base = os.path.join(ENV_DIR, d['file'][:-4])
            blit(base + '.png', d['pos'][0] - cx, d['pos'][1], True, base + '_n.png', base + '_e.png')
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGB')


def previews(scene):
    kit.ensure_gdignore(PREV_DIR)
    for cx in (0, 520, 1000, 1324, 2284):
        im = compose(scene, cx, lit=True)
        im.save(os.path.join(PREV_DIR, 'cam%04d_lit.png' % cx))
    for sym in (False, True):
        world = Image.new('RGB', (L.WORLD_W, L.WORLD_H))
        for cx in list(range(0, L.WORLD_W - L.VIEW_W + 1, 320)) + [L.WORLD_W - L.VIEW_W]:
            world.paste(compose(scene, cx, lit=False, symbols=sym), (cx, 0))
        world.save(os.path.join(PREV_DIR, 'world_overview%s.png' % ('_hist' if sym else '')))


# =========================================================================== manifest
def write_manifest():
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    lines = [
        '# Asset manifest part -- env_berlin (M1 Berliner Bauarchiv round 2, plan documents)',
        '',
        'All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`',
        '(`env_berlin.py` drives `env_berlin_room.py`, `env_berlin_hall.py`, `env_berlin_library.py`,',
        '`env_berlin_ext.py`, `env_berlin_props.py`, `env_berlin_fg.py`, `env_berlin_fx.py`, `env_berlin_actors.py`,',
        '`env_berlin_insignia.py`, `env_berlin_docs.py`, helpers `env_berlin_kit.py`, `env_berlin_layout.py` and the',
        'shared, read-only `pg.py`).  No pixels were copied, traced or sampled from the reference images in',
        '`documentation/references/` (style study only).  No third-party assets, fonts or textures are embedded;',
        'the tiny bitmap fonts are hand-defined in `env_berlin_kit.py`.  Sounds: `tools/audiogen/berlin_env_sfx.py`',
        '(numpy synthesis, no samples).',
        '',
        '* Licence / rights: project-owned original artwork (generated for this project), freely',
        '  redistributable with the game.  Provenance: deterministic generator, re-run with',
        '  `py -3 -P tools/pixelgen/env_berlin.py` and `py -3 -P tools/audiogen/berlin_env_sfx.py`.',
        '* Date: %s.  Palettes: `archive` (+ local `green`, `graphite` ramps), `berlin` (+ archive ink reds for flag' % kit.DATE,
        '  cloth), `sepia`.',
        '* Insignia (TECHNICAL_ARCHITECTURE 12.4): the layers carry only the neutral art (fictional Reichssiegel /',
        '  a plain eagle).  The historical variants (`*_hist.png`: Reichsadler with the wreathed swastika on the',
        '  plaque and the AUFBAU poster, the swastika flag on the facade banners, eagle seals on plan A / plan B /',
        '  Emil\'s slip) are separate files chosen at runtime by `Symbols.pick()` -- in-world iconography of the regime',
        '  inside the critical narrative only, never UI, rewards or player decoration.  Drawn from original geometry',
        '  in `env_berlin_insignia.py` (no traced emblem).',
        '* The Great Hall is fictional and shown muted, not heroic.',
        '* Locale `data/locale/de_env_berlin.json` is hand-written original German text (Konrad\'s voice).',
        '* `env_berlin_stills.py` / `x1_*.png` were made by this area in round 1; they now belong to the transition',
        '  work and are not rebuilt by `env_berlin.py` (see that owner\'s manifest part).',
        '',
        '| File | Generator | Content |',
        '|---|---|---|',
    ]
    seen = set()
    for path, gen, desc in sorted(PRODUCED):
        if path in seen:
            continue
        seen.add(path)
        g = gen if '/' in gen else 'tools/pixelgen/' + gen
        lines.append('| `%s` | `%s` | %s |' % (path, g, desc.replace('|', '/')))
    sfx = [('berlin_tram_rumble', 'tram rumble loop: motor hum, rail joints, muffled by the window'),
           ('berlin_tram_bell', 'tram bell, two strikes'),
           ('berlin_pigeon_coo', 'pigeon cooing'), ('berlin_pigeon_flutter', 'pigeons taking off'),
           ('berlin_mouse_squeak', 'mouse squeaks'), ('berlin_clock_tick', 'regulator tick'),
           ('berlin_clock_tock', 'regulator tock'), ('berlin_clock_chime', 'quarter-hour chime'),
           ('berlin_radiator_knock', 'water hammer knocking in the heating pipes'),
           ('berlin_radiator_hiss', 'steam hiss at the radiator valve'),
           ('berlin_radio_loop', 'faint dance music from the porter\'s radio (loop)'),
           ('berlin_paper_flutter', 'papers lifting in a draught'),
           ('berlin_tube_capsule', 'pneumatic tube capsule arriving')]
    for n, d in sfx:
        lines.append('| `assets/audio/sfx/%s.wav` | `tools/audiogen/berlin_env_sfx.py` | %s (44.1 kHz mono) |' % (n, d))
    lines += ['| `data/locale/de_env_berlin.json` | hand-written | observation prompts/texts (obs_window, '
              'obs_notice, obs_photo), canonical hotspot prompts |',
              '| `scripts/levels/berlin/*.gd`, `scenes/levels/berlin/*.tscn` | hand-written | ambient actors (tram, '
              'pigeons, mouse, clocks, radiator, radio, papers, tube, anim) |',
              '| `tests/visual/berlin_env_capture.gd/.tscn`, `tests/visual/berlin_actors_check.gd` | hand-written | '
              'visual harness (no post) and headless actor/decal behaviour check |', '']
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:   # LF on every platform
        f.write('\n'.join(lines))


# =========================================================================== main
def main(argv):
    preview = '--no-preview' not in argv
    t0 = time.time()
    if '--docs-only' not in argv:
        print('[env_berlin] scene M1 ...')
        build_scene(preview=preview)
    if '--scene-only' not in argv:
        import env_berlin_docs as ED
        print('[env_berlin] documents ...')
        docs = ED.build_all(DOC_DIR, PREV_DIR if preview else None)
        for path, desc in docs:
            record(path, 'env_berlin_docs.py', desc)
        KEEP.lf_json([path for path, _desc in docs])   # the repo's LF form on every platform (byte-identical)
        if '--stills' in argv:
            import env_berlin_stills as ES
            print('[env_berlin] cinematic stills ...')
            for path, desc in ES.build_all(DOC_DIR, PREV_DIR if preview else None):
                record(path, 'env_berlin_stills.py', desc)
    if not ({"--scene-only", "--docs-only"} & set(argv)):
        write_manifest()
    print('[env_berlin] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
