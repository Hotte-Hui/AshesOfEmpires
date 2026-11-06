"""env_c4_tunnels -- generator for L_C4_Tunnels 'Stimmen unter Beton' (Chapter 4 part 1, Karsk).

Run:  py -3 -P tools/pixelgen/env_c4_tunnels.py [--preview=DIR]      (deterministic, no network)

Produces assets/environments/karsk_tunnels/ (documentation/C4_DESIGN.md 4.1):
* room.png (+ _n normals, _e emission): ONE baked layer for both scenes -- the Archivkeller of the freight office
  (scene A, ~4.40: Lev's green lamp, the light box, the stove, the iron door of 1941), the door wall in section, the
  concrete tube of Dienststollen 3 and the vaulted Umsetzgleis with wagon 24 318 (scene C, ~7.30: cold work lamps,
  the single bulb over the wagon, the kerosene lamp in the siding office, dawn through the portal gate);
* patches/: opaque crops of a bake with one story change (plan handed over, iron door open, wagon door slid open)
  and the three insignia sites (wall calendar, lever-frame plate, wagon stencil; neutral + *_hist);
* outside.png (the yard behind the cellar windows), veils.png (lamp cones + paint haze), fg_frame.png;
* fx/ strips: snow behind the windows, the night shift's feet, samovar steam, stove vents, the clock pendulum, dust
  motes, drips, steam at the leaking flange, smoke of the booth's stove pipe, the kerosene flame, snow under the
  portal gate; swing strips (the hanging lamp, the bulb over the wagon) and event strips (dust shaken from the
  vault, the train crossing the yard above) for scripts/levels/c4/tunnels_level.gd;
* scene.json (layers / props / decals / fx / lights with the gate keys after / until / choice / fade of
  registry_level.gd, plus "scene" filters, "swing", "event_fx", "train" and "looks" read by tunnels_level.gd) and
  provenance.json.  The story contract (spawns, hotspots, npcs, the cellar_door blocker) is kept unchanged.
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
import env_c4_tunnels_kit as K          # noqa: E402
import env_c4_tunnels_layout as L       # noqa: E402
import env_c4_tunnels_room as ER        # noqa: E402
import env_c4_tunnels_fx as EFX         # noqa: E402

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'karsk_tunnels')
LF = chr(10)
PRODUCED: list[tuple[str, str, str]] = []
SA, SC = 'L_C4_TunnelsA', 'L_C4_TunnelsB'

BASE = dict(door_open=False, wagon_door='half', plan_rolled=True, hist=False)
VARIANTS = [   # (name, change, gate, scene filter)
    ('plan_taken', {'plan_rolled': False}, {'after': ['c4a_talk_tunnel']}, [SA]),
    ('door_open', {'door_open': True}, {'after': ['c4a_open_door']}, [SA]),
    ('wagon_open', {'wagon_door': 'open'}, {'after': ['c4c_inspect_wagon']}, [SC]),
]
INSIGNIA_SITES = {   # name: (x0, x1) world span searched for the neutral/_hist difference, scene
    'insignia_calendar': ((300, 420), SA),
    'insignia_lever_plate': ((1040, 1130), SC),
    'insignia_wagon': ((1600, 1660), SC),
}
COL = {'warm': '#F0C487', 'cold': '#9FB4CC', 'white': '#E8E4DA', 'green': '#B8D49A', 'kerosene': '#F2B060',
       'blue': '#8FA8C8'}
# dynamic Godot lights for the baked ones: name -> (energy, radius, height, colour, slow flicker, Hz, scene)
DYN = {
    'green_lamp': (0.55, 120, 10, 'warm', 0.0, 0.0, SA), 'green_shade': (0.2, 40, 4, 'green', 0.0, 0.0, SA),
    'hang_lamp': (0.3, 110, 18, 'warm', 0.0, 0.0, SA), 'stove': (0.5, 100, 6, 'kerosene', 0.18, 1.3, SA),
    'lightbox': (0.45, 70, 4, 'white', 0.0, 0.0, SA), 'lightbox_lens': (0.2, 40, 6, 'warm', 0.0, 0.0, SA),
    'office_door': (0.45, 120, 14, 'warm', 0.0, 0.0, SA),
    'win_204': (0.25, 90, 10, 'cold', 0.0, 0.0, SA), 'win_412': (0.25, 90, 10, 'cold', 0.0, 0.0, SA),
    'yard_lamp_412': (0.2, 70, 10, 'warm', 0.0, 0.0, SA),
    'cage_782': (0.45, 110, 12, 'warm', 0.0, 0.0, SC), 'cage_902': (0.5, 110, 12, 'warm', 0.0, 0.0, SC),
    'cage_1142': (0.45, 110, 12, 'warm', 0.32, 0.8, SC), 'airlock_warm': (0.35, 90, 8, 'warm', 0.0, 0.0, SC),
    'work_left': (0.4, 200, 30, 'cold', 0.0, 0.0, SC), 'work_right': (0.32, 180, 30, 'cold', 0.0, 0.0, SC),
    'bulb_wagon': (0.45, 150, 26, 'white', 0.0, 0.0, SC), 'kerosene': (0.6, 90, 10, 'kerosene', 0.12, 1.6, SC),
    'portal_dawn': (0.4, 130, 4, 'cold', 0.0, 0.0, SC), 'shunt_blue': (0.25, 36, 4, 'blue', 0.0, 0.0, SC),
    'brazier': (0.35, 70, 10, 'kerosene', 0.2, 1.1, SC),
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
    if not os.path.isdir(ENV_DIR):
        return
    keep = {'explore_hotspots.json'}
    for root, _dirs, files in os.walk(ENV_DIR):
        if '_preview' in root:
            continue
        for f in files:
            if f.endswith('.png') or (f.endswith('.json') and f not in keep and root == ENV_DIR):
                os.remove(os.path.join(root, f))


# =========================================================================== bakes
def bake(cfg: dict):
    room = ER.Room(cfg)
    room.build()
    lights = room.all_lights()
    F = K.light_fields(room.lay, lights)
    K.add_pools(F, lights, L.FLOOR, L.WORLD_H, L.WORLD_W)
    K.resolve(room.lay, F, exposure=0.86)
    return room


def maps(room):
    lay = room.lay
    return lay.c.copy(), lay.normal_map(3.0), lay.em.copy()


def diff_mask(a, b):
    d = np.zeros(a[0].shape[:2], bool)
    for x, y in zip(a, b):
        d |= np.any(x != y, axis=-1)
    return d


def box_of(d, pad=1, xspan=None):
    if xspan is not None:
        d = d.copy()
        d[:, :xspan[0]] = False
        d[:, xspan[1]:] = False
    if not d.any():
        return None
    ys, xs = np.nonzero(d)
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(L.WORLD_W, xs.max() + pad + 1),
            min(L.WORLD_H, ys.max() + pad + 1))


def write_room(m, name, desc):
    c, n, e = m
    base = os.path.join(ENV_DIR, name)
    save_arr(c, base + '.png', 'env_c4_tunnels_room.py', desc)
    save_arr(n, base + '_n.png', 'env_c4_tunnels_room.py', desc + ' -- normal map (OpenGL +Y up)')
    save_arr(e, base + '_e.png', 'env_c4_tunnels_room.py', desc + ' -- emission mask (unshaded glow)')


def write_patch(m, box, name, desc, hist_m=None):
    x0, y0, x1, y1 = box
    c, n, e = m
    base = os.path.join(ENV_DIR, 'patches', name)
    save_arr(c[y0:y1, x0:x1], base + '.png', 'env_c4_tunnels.py', desc)
    save_arr(n[y0:y1, x0:x1], base + '_n.png', 'env_c4_tunnels.py', desc + ' -- normal map')
    ee = e[y0:y1, x0:x1]
    has_e = bool(ee[..., 3].any())
    if has_e:
        save_arr(ee, base + '_e.png', 'env_c4_tunnels.py', desc + ' -- emission mask')
    if hist_m is not None:
        hc, hn, he = hist_m
        save_arr(hc[y0:y1, x0:x1], base + '_hist.png', 'env_c4_tunnels.py',
                 desc + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
        save_arr(hn[y0:y1, x0:x1], base + '_hist_n.png', 'env_c4_tunnels.py', desc + ' -- historical, normal map')
        if has_e:
            save_arr(he[y0:y1, x0:x1], base + '_hist_e.png', 'env_c4_tunnels.py', desc + ' -- historical, emission')
    return has_e


# =========================================================================== foreground
def fg_frame():
    """Dark foreground silhouettes below the walk band (parallax 1.25): crates and a sack by the stairs, a cable
    drum and a concrete block in the tunnel, the buffer stop of track 2, a stack of sleepers."""
    lay = K.tlayer(L.WORLD_W, L.WORLD_H, 'fg')
    rng = np.random.default_rng(801)

    def crate(x, y, w, h):
        lay.rect(x, y, w, h, 'N', 1.4, hgt=0.6)
        lay.rect(x, y, w, 1, 'D', 1.6, hgt=0.7)
        lay.rect(x, y + h // 2, w, 1, 'N', 0.6)
        lay.rect(x + 2, y + 1, 1, h - 1, 'N', 0.6)
        lay.rect(x + w - 3, y + 1, 1, h - 1, 'N', 0.6)

    crate(4, 330, 34, 30)
    crate(24, 314, 26, 18)
    lay.ellipse(62, 350, 14, 10, 'N', 2.0, hgt=0.5)                                   # sack
    lay.rect(52, 342, 4, 2, 'L', 1.4)
    lay.rect(596, 334, 22, 26, 'I', 1.0, hgt=0.6)                                     # coal bin
    lay.rect(596, 334, 22, 1, 'I', 2.0)
    m, mx, my = lay.ellipse_mask(904, 352, 22, 16)                                   # cable drum
    lay.put(m, mx, my, 'N', 1.8, hgt=0.7)
    lay.put(K.disc(10), 899, 341, 'N', 0.4)
    lay.rect(1098, 336, 40, 24, 'C', 1.0, hgt=0.6)                                   # concrete block
    lay.rect(1098, 336, 40, 1, 'C', 2.2)
    lay.rect(1296, 318, 10, 42, 'N', 1.8, hgt=0.7)                                   # buffer stop, track 2
    lay.rect(1290, 324, 24, 6, 'V', 0.8, hgt=0.8)
    lay.put(K.disc(8), 1286, 323, 'I', 1.2, hgt=0.8)
    lay.put(K.disc(8), 1308, 323, 'I', 1.2, hgt=0.8)
    for k in range(5):                                                                # sleepers stack
        lay.rect(1740 + (k % 2) * 3, 356 - k * 5, 60, 5, 'N', 1.4 + (k % 2) * 0.6, hgt=0.6)
    for x in range(0, L.WORLD_W, 1):
        pass
    fields = {'warm': np.zeros((L.WORLD_H, L.WORLD_W), np.float32),
              'cold': np.zeros((L.WORLD_H, L.WORLD_W), np.float32),
              'white': np.zeros((L.WORLD_H, L.WORLD_W), np.float32)}
    K.resolve(lay, fields, exposure=1.0)
    return lay


def check_clearance(fg_lay, points, par=1.25):
    issues = []
    a = fg_lay.c[..., 3] > 0
    for k, (x, _y) in points.items():
        cam = min(max(x - 320, 0), 1280)
        fx = int(round(x - cam + par * cam))
        if a[250:306, max(0, fx - 12):fx + 13].any():
            issues.append(k)
    return issues


# =========================================================================== scene
def build_scene(preview_dir=None):
    t0 = time.time()
    clean_env_dir()
    layers, props, decals, fx, lights = [], [], [], [], []
    swing, event_fx = [], []

    room = bake(dict(BASE))
    m = maps(room)
    write_room(m, 'room', 'Karsk, 16 February 1964: the Archivkeller of the freight office (Lev\'s desk under the '
                          'green lamp), the iron door of 1941, Dienststollen 3, the Umsetzgleis with wagon 24 318')
    layers.append({'name': 'room', 'file': 'room.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -50, 'normal': True,
                   'emission': True, 'emission_strength': 0.5, 'lit': True})
    print('  base room baked in %.1fs' % (time.time() - t0))
    # ---- story patches
    for (vname, change, gate, scenes) in VARIANTS:
        vroom = bake(dict(BASE, **change))
        vm = maps(vroom)
        box = box_of(diff_mask(m, vm), pad=1)
        if box is None:
            print('  WARNING variant %s changes nothing' % vname)
            continue
        he = write_patch(vm, box, vname, 'the room with the story change "%s"' % vname)
        d = {'name': vname, 'file': 'patches/%s.png' % vname, 'pos': [int(box[0]), int(box[1])], 'z': -48,
             'lit': True, 'normal': True, 'emission': he, 'emission_strength': 0.5, 'fade': 0.45, 'scene': scenes}
        d.update(gate)
        decals.append(d)
        print('  patch %s %s' % (vname, box))
    # ---- insignia sites (neutral + _hist of the base look)
    hroom = bake(dict(BASE, hist=True))
    hm = maps(hroom)
    dm = diff_mask(m, hm)
    for nm, (span, scene) in INSIGNIA_SITES.items():
        box = box_of(dm, pad=2, xspan=span)
        if box is None:
            print('  WARNING insignia site %s: no difference' % nm)
            continue
        he = write_patch(m, box, nm, 'insignia site %s, fictional emblem (neutral)' % nm, hist_m=hm)
        decals.append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])], 'z': -49,
                       'lit': True, 'normal': True, 'emission': he, 'hist_variant': 'patches/%s_hist.png' % nm,
                       'scene': [scene]})
    print('  patches + insignia in %.1fs' % (time.time() - t0))

    # ---- outside, veils, foreground
    out = EFX.outside(room.windows)
    save_arr(out, os.path.join(ENV_DIR, 'outside.png'), 'env_c4_tunnels_fx.py',
             'the freight yard at night behind the high cellar windows: snow heaped at the glass, the yard lamp')
    layers.insert(0, {'name': 'outside', 'file': 'outside.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -60,
                      'normal': False, 'emission': False, 'lit': False})
    vl = EFX.veils()
    save_arr(vl, os.path.join(ENV_DIR, 'veils.png'), 'env_c4_tunnels_fx.py',
             'soft light cones under the lamps and the faint paint haze of the siding (plain alpha)')
    layers.append({'name': 'veils', 'file': 'veils.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': 10,
                   'normal': False, 'emission': False, 'lit': False})
    fg = fg_frame()
    issues = check_clearance(fg, {**L.HOTSPOTS, **L.SPAWNS})
    if issues:
        print('  WARNING fg covers:', issues)
    save_arr(fg.c, os.path.join(ENV_DIR, 'fg_frame.png'), 'env_c4_tunnels.py',
             'foreground silhouettes (crates, sack, cable drum, buffer stop, sleepers), parallax 1.25')
    layers.append({'name': 'fg_frame', 'file': 'fg_frame.png', 'pos': [0, 0], 'parallax': [1.25, 1.0], 'z': 60,
                   'normal': False, 'emission': False, 'lit': False})

    # ---- looping strips
    def strip_entry(section, nm, arr, pos, frames, fps, z, scene, desc, em=None, lit=False, kind='anim_sprite',
                    alpha=None, gate=None):
        base = os.path.join(ENV_DIR, 'fx', nm)
        save_arr(arr, base + '.png', 'env_c4_tunnels_fx.py', desc)
        e = {'name': nm, 'file': 'fx/%s.png' % nm, 'frames': frames, 'fps': fps, 'pos': [int(pos[0]), int(pos[1])],
             'z': z, 'lit': lit, 'scene': scene}
        if em is not None:
            save_arr(em, base + '_e.png', 'env_c4_tunnels_fx.py', desc + ' -- emission strip')
            e['emission'] = True
            e['emission_strength'] = 0.6
        if section == 'fx':
            e['type'] = kind
            e['parallax'] = [1.0, 1.0]
        else:
            e['normal'] = False
        if alpha is not None:
            e['alpha'] = alpha
        if gate:
            e.update(gate)
        (fx if section == 'fx' else decals).append(e)

    for i, (x0, y0, x1, y1) in enumerate(room.windows):
        strip_entry('decals', 'snow_win_%d' % i,
                    EFX.particles(x1 - x0, y1 - y0, 24, 8, 14, 710 + i, kind='snow', vy=(5, 9), vx=(1, 4), sway=1.0),
                    (x0, y0), 24, 8, -55, [SA], 'snow falling in the yard behind cellar window %d' % i)
    gx0, gy0, gx1, gy1 = room.windows[1]
    strip_entry('decals', 'feet_win', EFX.feet(gx1 - gx0, gy1 - gy0, 96), (gx0, gy0), 96, 8, -56, [SA],
                'the night shift passing the cellar window: felt boots in the snow (96 frames, 8 fps)')
    sx = (L.SAMOVAR[0] + L.SAMOVAR[1]) // 2
    strip_entry('fx', 'samovar_steam', EFX.steam_wisp(14, 34, 16, 721, dens=0.8), (sx - 7, 266 - 31 - 34), 16, 6,
                -20, [SA], 'steam from the samovar chimney (16 frames)')
    vx_ = L.STOVE[0] + 8
    vents = EFX.vents(8, 722)
    strip_entry('decals', 'stove_vents', vents, (vx_, 246 + 10 + 3), 8, 5, -45, [SA],
                'the fire breathing behind the stove\'s vent slits (8 frames, emission)', em=vents)
    pend = EFX.pendulum(12)
    strip_entry('decals', 'clock_pendulum', pend, (L.CLOCK[0] - 4, L.CLOCK[1] + 7), 12, 6, -45, [SA],
                'the wall clock\'s pendulum, one beat per second')
    strip_entry('fx', 'dust_lamp', EFX.particles(60, 44, 32, 6, 16, 723, kind='dust', vy=(-1.5, 1.5),
                                                 vx=(-1.5, 1.5), sway=1.5),
                (L.GREEN_LAMP[0] - 30, L.GREEN_LAMP[1] + 2), 32, 6, 12, [SA], 'dust motes in the green lamp light')
    strip_entry('fx', 'dust_hang', EFX.particles(70, 90, 32, 6, 14, 724, kind='dust', vy=(-1.2, 1.2),
                                                 vx=(-1.5, 1.5), sway=1.5),
                (L.HANG_LAMP[0] - 35, L.HANG_LAMP[1] + 8), 32, 6, 12, [SA], 'dust motes under the hanging lamp')
    for i, dx in enumerate(L.T_DRIPS + [1418, 1760]):
        top = L.T_SOFFIT[1] - 2 if dx < L.SIDING[0] else L.S_SPRING - 30
        hh = L.FLOOR + 8 - top
        frames = 30 + (i % 3) * 6
        strip_entry('fx', 'drip_%d' % i, EFX.drip(hh, frames, 10, 730 + i), (dx - 5, top), frames, 10, -30, [SC],
                    'water dripping from the vault into a puddle (%d frames)' % frames)
    strip_entry('fx', 'steam_flange', EFX.steam_wisp(22, 46, 16, 741, dens=0.9, drift=1.0),
                (L.T_FLANGE - 10, 196 - 44), 16, 7, -20, [SC], 'steam hissing from the leaking flange of the pipe')
    strip_entry('fx', 'booth_smoke', EFX.steam_wisp(16, 40, 16, 742, dens=0.55, ramp='C', drift=0.8),
                (L.BOOTH[1] - 20, 162 - 40), 16, 5, -20, [SC], 'thin smoke from the siding office\'s stove pipe')
    fl = EFX.flame(8, 5, 6, 743)
    strip_entry('decals', 'kerosene_flame', fl, ((L.BOOTH_WIN[0] + L.BOOTH_WIN[1]) // 2 - 4 - 2, 240), 8, 6, -45,
                [SC], 'the kerosene lamp\'s flame in the siding office (8 frames, emission)', em=fl)
    strip_entry('fx', 'dust_bulb', EFX.particles(90, 120, 32, 6, 18, 744, kind='dust_cold', vy=(-1.2, 1.2),
                                                 vx=(-1.5, 1.5), sway=1.5),
                (L.BULB[0] - 45, L.BULB[1] + 10), 32, 6, 12, [SC], 'dust and paint mist in the light of the bulb')
    strip_entry('fx', 'dust_work', EFX.particles(110, 120, 32, 6, 16, 745, kind='dust_cold', vy=(-1, 1),
                                                 vx=(-1.5, 1.5), sway=1.5),
                (L.WORK_LAMPS[0][0] - 20, L.WORK_LAMPS[0][1] + 14), 32, 6, 12, [SC], 'dust in the work lamp cone')
    ba, bb = L.BRAZIER
    holes = [(5, 6), (10, 6), (14, 6), (7, 12), (12, 12), (5, 18), (10, 18), (14, 18)]
    emb = EFX.embers(holes, bb - ba, 22, 12, 747)
    strip_entry('decals', 'brazier_embers', emb, (ba, L.FLOOR - 26), 12, 5, -45, [SC],
                'the embers of the workers\' brazier glowing and dimming (12 frames, emission)', em=emb)
    strip_entry('fx', 'snow_gate', EFX.snow_gate(70, 26, 24, 10, 746), (L.PORTAL[0] - 30, L.FLOOR - 22), 24, 10,
                -20, [SC], 'snow blowing in under the shut portal gate')

    # ---- swinging lamps (frame 3 = at rest), driven by the level script
    for (nm, (img, em), pos, scene, light, desc) in (
            ('hang_lamp', EFX.hang_lamp(L.HANG_LAMP[1] - 46), (L.HANG_LAMP[0] - 8, 46), SA, 'hang_lamp',
             'enamel shade on its cord from the cellar vault, 7 swing frames'),
            ('bulb_wagon', EFX.wagon_bulb(L.BULB[1] - 38), (L.BULB[0] - 7, 38), SC, 'bulb_wagon',
             'the single bulb over the wagon on its cord, 7 swing frames')):
        base = os.path.join(ENV_DIR, 'fx', nm)
        save_arr(img, base + '.png', 'env_c4_tunnels_fx.py', desc)
        save_arr(em, base + '_e.png', 'env_c4_tunnels_fx.py', desc + ' -- emission strip')
        swing.append({'name': nm, 'file': 'fx/%s.png' % nm, 'frames': EFX.SWING_FRAMES, 'rest': 3,
                      'pos': list(pos), 'z': -30, 'emission': True, 'emission_strength': 0.7, 'light': light,
                      'max_px': 3, 'scene': [scene]})
    # ---- event strips: dust shaken from the vault, the train over the yard
    df = [(EFX.dust_fall(40, 120, 16, 10, 750 + i), (x, y), sc) for i, (x, y, sc) in enumerate(
        [(140, 0, SA), (430, 0, SA), (610, 0, SA), (790, 116, SC), (1010, 116, SC), (1370, 30, SC),
         (1540, 30, SC), (1720, 30, SC)])]
    for i, (arr, pos, sc) in enumerate(df):
        base = os.path.join(ENV_DIR, 'fx', 'dust_fall_%d' % i)
        save_arr(arr, base + '.png', 'env_c4_tunnels_fx.py', 'grit and dust shaken from the vault by a train '
                                                            'overhead (16 frames, played once per train)')
        event_fx.append({'name': 'dust_fall_%d' % i, 'file': 'fx/dust_fall_%d.png' % i, 'frames': 16, 'fps': 10,
                         'pos': [int(pos[0]), int(pos[1])], 'z': 14, 'delay': round(0.35 * (i % 3), 2),
                         'scene': [sc]})
    tr = EFX.train_top()
    save_arr(tr, os.path.join(ENV_DIR, 'fx', 'train_top.png'), 'env_c4_tunnels_fx.py',
             'the underframes of a freight train rolling over the yard above the tunnel (section, event)')
    train = {'file': 'fx/train_top.png', 'y': -10, 'z': -45, 'from_x': L.WORLD_W + 20,
             'to_x': L.TUNNEL[0] - tr.shape[1] - 20, 'seconds': 7.0, 'scene': [SC]}

    # ---- lights (every light carries a gate so registry_level names it and drives its slow flicker)
    for lt in room.all_lights():
        nm = lt['name']
        if nm not in DYN:
            continue
        en, rad, hgt, col, slow, hz, sc = DYN[nm]
        e = {'name': nm, 'pos': [int(round(lt['pos'][0])), int(round(lt['pos'][1]))], 'color': COL[col],
             'energy': en, 'radius': rad, 'height': hgt, 'flicker': 0.0, 'on_layer': 'playfield',
             'after': [], 'scene': [sc]}
        if slow > 0:
            e['flicker_slow'], e['flicker_hz'] = slow, hz
        lights.append(e)
    vroom = bake(dict(BASE, door_open=True))
    for lt in vroom.all_lights():
        if lt['name'] == 'door_cold':
            lights.append({'name': 'door_cold', 'pos': [int(lt['pos'][0]), int(lt['pos'][1])], 'color': COL['cold'],
                           'energy': 0.3, 'radius': 70, 'height': 6, 'flicker': 0.0, 'on_layer': 'playfield',
                           'after': ['c4a_open_door'], 'fade': 0.6, 'scene': [SA]})

    # ---- hotspot info + explore suggestions
    hotspot_info = {}
    for k, (what, span) in L.HOTSPOT_PROPS.items():
        hotspot_info[k] = {'kind': 'story', 'stand': list(L.HOTSPOTS[k]), 'focus': [L.HOTSPOTS[k][0], 270],
                           'what': what, 'span': [int(span[0]), int(span[1])]}

    scene = {
        'id': 'karsk_tunnels', 'palette': 'tunnels',
        'world_size': [L.WORLD_W, L.WORLD_H],
        'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]},
        'camera_zones': {k: [v[0], 0, v[1] - v[0], L.WORLD_H] for k, v in L.CAMERA.items()},
        'canvas_modulate': '#CFC8BE',
        'layers': layers, 'props': props, 'decals': decals, 'lights': lights, 'fx': fx,
        'swing': swing, 'event_fx': event_fx, 'train': train,
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]],
                     [L.WALK_X[1], L.WALK_BAND[1]], [L.WALK_X[0], L.WALK_BAND[1]]],
        'blockers': [dict(b) for b in L.BLOCKERS],
        'spawns': {k: list(v) for k, v in L.SPAWNS.items()},
        'hotspots': {k: list(v) for k, v in L.HOTSPOTS.items()},
        'zones': {k: list(v) for k, v in L.ROOMS.items()},
        'npcs': {k: dict(v) for k, v in L.NPCS.items()},
        'looks': [
            {'name': 'cellar', 'scene': [SA], 'canvas_modulate': '#CFC8BE', 'grade': 'tunnels'},
            {'name': 'siding', 'scene': [SC], 'canvas_modulate': '#BCC3C8', 'grade': 'tunnels_siding'},
        ],
        'hotspot_info': hotspot_info,
        'gates_doc': ('scripts/levels/c4/tunnels_level.gd (extends the registry level): an entry with "scene" is '
                      'built only when the level plays one of those Story scenes (level_id, set before _ready); '
                      '"after" / "until" / "choice" / "fade" are the registry gates (objectives of earlier scenes '
                      'count as complete). Lights carry an empty "after" so they are named and their slow flicker '
                      'runs. "swing" = 7-frame lamp strips (frame "rest" at rest) the train event swings, with the '
                      'named light; "event_fx" = strips played once per train (after "delay" s); "train" = the '
                      'freight train rolling over the yard above (scene C). camera_zones = the camera window '
                      'per scene (the walk area of the other scene stays off screen); looks = canvas modulate + '
                      'grade per scene.'),
        'notes': [
            'Side view like the registry: feet line y 300, walk band 296-306, x 18-1902; the door wall 700-720 is '
            'the permanent blocker cellar_door between scene A (cellar) and scene C (tunnel + siding).',
            'Readable story figures: wagon side C-17/45 (fresh stencil, still taped) over 47 702 (brushed) over the '
            'ghost of C-17/42, enamel plate 24 318 on the solebar, chalk "ВТ 23.40" on the door; card box '
            '"C-17/45 / ПРИНЯТЬ" and the stamp on the siding office counter; stencils C-17/41 .. /45 on the paint '
            'stand; the January gap on the 1964 shelf; sign "Бомбоубежище - Служебный тоннель №3" over the door.',
            'Insignia: patches/insignia_*.png (wall calendar, lever-frame plate, wagon stencil) show the fictional '
            'gear-and-wheat emblem of Chapter 1; their *_hist twins the hammer and sickle (Symbols.pick).',
            'No story character is painted into the art; Lev stands at the npcs anchors (cast stream sheet).',
            'Palette: data/chapters/c4.json palettes.tunnels + the ramps green and concrete of TUN (env_c4_tunnels_'
            'kit.py) -- integration note of the env-tunnels stream.',
        ],
        'meta': {'mode': 'side', 'feet_y': L.WALK_Y, 'generator': 'tools/pixelgen/env_c4_tunnels.py',
                 'date': K.DATE, 'palette_ramps': K.TUN},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    with open(sj, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(scene, f, indent=1, ensure_ascii=False)
    record(sj, 'env_c4_tunnels.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1 + registry gates + tunnels extensions)')

    n, bad = K.palette_report(room.lay.c)
    if bad:
        print('  WARNING room uses non-palette colours: %s' % bad[:6])
    for note in K.check_c4_palette():
        print('  NOTE', note)
    print('  scene built in %.1fs' % (time.time() - t0))
    if preview_dir:
        preview(scene, preview_dir)
    return scene


# =========================================================================== preview (layers + decals frame 0)
def preview(scene, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    W, H = L.WORLD_W, L.WORLD_H

    def load(p):
        return np.asarray(Image.open(os.path.join(ENV_DIR, p)).convert('RGBA'))

    def over(dst, src, x, y, frames=1, alpha=1.0, frame=0):
        h, w = src.shape[:2]
        w //= frames
        s = src[:, frame * w:(frame + 1) * w].astype(np.float32)
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        sub = s[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4] / 255.0 * alpha
        dst[Y0:Y1, X0:X1, :3] = dst[Y0:Y1, X0:X1, :3] * (1 - a) + sub[..., :3] * a

    states = {'a': (SA, set()), 'a_door': (SA, {'c4a_talk_tunnel', 'c4a_open_door'}),
              'c': (SC, {'c4a_talk_tunnel', 'c4a_open_door'}),
              'c_open': (SC, {'c4a_talk_tunnel', 'c4a_open_door', 'c4c_inspect_wagon'})}

    def holds(e, st):
        sc, done = states[st]
        if 'scene' in e and sc not in e['scene']:
            return False
        for o in e.get('after', []):
            if o not in done:
                return False
        for o in e.get('until', []):
            if o in done:
                return False
        return True

    for st in states:
        img = np.zeros((H, W, 3), np.float32)
        items = []
        for e in scene['layers']:
            if holds(e, st) and e['name'] not in ('fg_frame',):
                items.append((e['z'], 0, e['file'], e['pos'], 1, e.get('alpha', 1.0), 0))
        for e in scene['decals']:
            if holds(e, st):
                items.append((e.get('z', 0), 1, e['file'], e['pos'], e.get('frames', 1), 1.0, 0))
        for e in scene['fx']:
            if holds(e, st):
                items.append((e.get('z', 0), 3, e['file'], e['pos'], e.get('frames', 1), e.get('alpha', 1.0), 0))
        for e in scene['swing']:
            if holds(e, st):
                items.append((e.get('z', 0), 2, e['file'], e['pos'], e['frames'], 1.0, e['rest']))
        for (_z, _k, f, pos, fr, al, frm) in sorted(items, key=lambda t: (t[0], t[1])):
            over(img, load(f), int(pos[0]), int(pos[1]), fr, al, frm)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(out_dir, 'look_%s.png' % st))
    print('  preview written to', out_dir)


# =========================================================================== provenance
def write_provenance():
    files = [{'path': p, 'generator': 'tools/pixelgen/' + g, 'content': d} for p, g, d in sorted(PRODUCED)]
    out = {'generator': 'tools/pixelgen/env_c4_tunnels.py (+ _kit, _layout, _room, _siding, _fx)',
           'date': K.DATE,
           'licence': 'project-owned original artwork, generated procedurally; no copied, traced, downloaded or '
                      'AI-generated pixels; bitmap fonts hand-defined (env_veltrava_hall_kit.py + env_c4_tunnels_kit.py)',
           'run': 'py -3 -P tools/pixelgen/env_c4_tunnels.py',
           'files': files}
    p = os.path.join(ENV_DIR, 'provenance.json')
    with open(p, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


def main(argv):
    t0 = time.time()
    prev = None
    for a in argv:
        if a.startswith('--preview'):
            prev = a.split('=', 1)[1] if '=' in a else os.path.join(ENV_DIR, '_preview')
    print('[env_c4_tunnels] scene ...')
    build_scene(prev)
    write_provenance()
    for root, _dirs, files in os.walk(ENV_DIR):
        for f in files:
            if f.endswith('.png.import') and not os.path.exists(os.path.join(root, f[:-len('.import')])):
                os.remove(os.path.join(root, f))
    print('[env_c4_tunnels] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
