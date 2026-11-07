"""env_c4_annex -- generator for L_C4_Annex (Chapter 4 part 1 'Stimmen unter Beton', C4_DESIGN.md 4.2).

Run:  py -3 -P tools/pixelgen/env_c4_annex.py [--preview=DIR]      (deterministic, no network)

Produces assets/environments/berlin_annex/ (one level file, two Story scenes, two walk areas):
* scene A 'Wendeschleife Sued 8' (L_C4_AnnexA, street at dawn): sky.png, dome.png (+ _hist banners), far.png,
  mid.png (parallax, unlit), loop.png (+ _n / _e; the playfield street 0..846), fg_loop.png;
* scene B 'Nebenstelle Sued' (L_C4_AnnexB, the annex under the clearance zone): annex.png (+ _n / _e; placed at
  x 846), fg_annex.png;
* patches/: exact crops of a layer baked with one story change applied (Konrad's tracing sheets on the timetable
  case, the poster of S 2 torn back, drawer Sued 8 pulled out, the capsule opened, the form on the counter) and
  the three official insignia sites (notice on S 2, the plate above the counter, the plate of the Staatspolizei
  door), neutral + *_hist (TECHNICAL_ARCHITECTURE 12.4);
* fx/ and life/ strips (env_c4_annex_fx): snow, steam, exhaust, chimney smoke, aviation lights, the blinker, Ilse
  at the last window, the fans, dust, the capsule in the glass tube, a failing tube, the typists;
* scene.json (layers / decals / fx / lights / actors with the gate keys after / until / choice and the per-scene
  key "scene", the design's spawns, hotspots, NPC anchors, walk band, blocker, zones, camera_zones, looks)
  + provenance.json.  scripts/levels/c4/annex_level.gd applies the gates, the scene filter and the camera zones.
explore_hotspots.json (exploration stream) and any foreign scene.json "actors" entries are kept.
Shared folder (round 11, tools/pixelgen/env_keep.py): a run removes only the PNGs of ITS previous provenance rows,
keeps the rows (and files) of other generators and writes scene.json only when its content changed.
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
import env_c4_annex_kit as K          # noqa: E402
import env_c4_annex_layout as L       # noqa: E402
import env_c4_annex_loop as EL        # noqa: E402
import env_c4_annex_hall as EH        # noqa: E402
import env_c4_annex_fx as EFX         # noqa: E402
import env_c4_annex_docs as EDOC      # noqa: E402
import env_keep as KEEP               # noqa: E402  (round 11: the folder is shared)

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'berlin_annex')
GEN = 'tools/pixelgen/env_c4_annex.py'
FAMILY = 'tools/pixelgen/env_c4_annex'   # provenance rows of this generator and its modules (env_keep)
PRODUCED: list[tuple[str, str, str]] = []
BUILD_S = 0.0
A, B = L.SCENE_A, L.SCENE_B
X0 = L.SEAM

COL = {'warm': '#F0C487', 'sodium': '#F2C46A', 'cold': '#DDE6EA', 'tube': '#C4D8C4', 'red': '#C8503C',
       'machine': '#B8CCC0'}


# =========================================================================== io
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def save(arr, relpath, gen, desc):
    path = os.path.join(ENV_DIR, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.asarray(arr).astype(np.uint8), 'RGBA').save(path)
    PRODUCED.append((rel(path), gen, desc))
    return relpath


def clean_previous():
    """Remove the PNGs this generator wrote last time (its own provenance.json rows); never touches foreign files
    (rows of other generators, hand art, the .import sidecars)."""
    if os.path.isdir(ENV_DIR):
        KEEP.remove_own_pngs(ENV_DIR, ROOT, FAMILY)


def maps(lay):
    return lay.c.copy(), lay.normal_map(3.0), lay.em.copy()


def write_layer(name, m, gen, desc):
    c, n, e = m
    save(c, name + '.png', gen, desc)
    save(n, name + '_n.png', gen, desc + ' -- normal map (OpenGL +Y up)')
    has_e = bool(e[..., 3].any())
    if has_e:
        save(e, name + '_e.png', gen, desc + ' -- emission mask (unshaded glow)')
    return has_e


def diff_mask(a, b):
    d = np.zeros(a[0].shape[:2], bool)
    for x, y in zip(a, b):
        d |= np.any(x != y, axis=-1)
    return d


def box_of(mask, pad=1, xr=None):
    m = mask.copy()
    if xr is not None:
        m[:, :xr[0]] = False
        m[:, xr[1]:] = False
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    h, w = mask.shape
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad + 1), min(h, ys.max() + pad + 1))


def write_patch(name, m, box, gen, desc, hist_m=None):
    x0, y0, x1, y1 = box
    c, n, e = m
    sl = (slice(y0, y1), slice(x0, x1))
    save(c[sl], 'patches/%s.png' % name, gen, desc)
    save(n[sl], 'patches/%s_n.png' % name, gen, desc + ' -- normal map')
    has_e = bool(e[sl][..., 3].any())
    if hist_m is not None:
        hc, hn, he = hist_m
        save(hc[sl], 'patches/%s_hist.png' % name, gen,
             desc + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
        save(hn[sl], 'patches/%s_hist_n.png' % name, gen, desc + ' -- historical, normal map')
        if has_e or bool(he[sl][..., 3].any()):
            save(he[sl], 'patches/%s_hist_e.png' % name, gen, desc + ' -- historical, emission')
    if has_e:
        save(e[sl], 'patches/%s_e.png' % name, gen, desc + ' -- emission mask')
    return has_e


# =========================================================================== the street (scene A)
def build_street(scene: dict, notes: list):
    gen = 'tools/pixelgen/env_c4_annex_loop.py'
    base = EL.bake_street({})
    mb = maps(base.lay)
    write_layer('loop', mb, gen, 'Wendeschleife Sued 8 at dawn: houses No. 11 / No. 9, shelter, tram 74, column S 2, '
                                 'freight hatch, hoarding, the street (x 0..846)')
    scene['layers'].append({'name': 'loop', 'file': 'loop.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -50,
                            'normal': True, 'emission': True, 'emission_strength': 0.6, 'lit': True})
    # story patches (gated) and the insignia site
    for key, cfg, gate, nm, desc, fade in (
            ('routes', {'routes': True}, {'after': ['c4b_solve_routes']}, 'routes_case',
             "Konrad's tracing sheets taped over the lit timetable case: Marta's line and three detours", 0.4),
            ('bared', {'bared': True}, {'after': ['c4b_inspect_column']}, 'column_bared',
             'the poster of S 2 torn back: the steel door of the ventilation structure', 0.5)):
        st = EL.bake_street(cfg)
        m = maps(st.lay)
        box = box_of(diff_mask(mb, m))
        sth = EL.bake_street(dict(cfg, hist=True))
        mh = maps(sth.lay)
        neutral_h = EL.bake_street({'hist': True})
        hist_differs = bool(diff_mask(m, mh)[box[1]:box[3], box[0]:box[2]].any()) and \
            bool(diff_mask(maps(neutral_h.lay), mh)[box[1]:box[3], box[0]:box[2]].any())
        has_e = write_patch(nm, m, box, gen, desc, hist_m=mh if hist_differs else None)
        e = {'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])], 'z': -46, 'lit': True,
             'normal': True, 'emission': has_e, 'fade': fade, 'scene': A}
        if hist_differs:
            e['hist_variant'] = 'patches/%s_hist.png' % nm
        e.update(gate)
        scene['decals'].append(e)
    sth = EL.bake_street({'hist': True})
    mh = maps(sth.lay)
    box = box_of(diff_mask(mb, mh))
    has_e = write_patch('notice_s2', mb, box, gen, 'the official notice on S 2: the emblem above the small print',
                        hist_m=mh)
    scene['decals'].append({'name': 'notice_s2', 'file': 'patches/notice_s2.png', 'pos': [int(box[0]), int(box[1])],
                            'z': -48, 'lit': True, 'normal': True, 'emission': has_e, 'scene': A,
                            'hist_variant': 'patches/notice_s2_hist.png',
                            'note': 'insignia site (12.4): neutral Reichssiegel / historical state eagle'})
    # the notice on the door of No. 9 (obj.c4b_notice „Lies den Bescheid an der Tür von Nummer neun.“): a neutral
    # typed sheet with the Bezirksamt stamp and the stapled site plan, pasted over the planks of the left leaf
    st9 = EL.bake_street({'notice9': True})
    m9 = maps(st9.lay)
    box9 = box_of(diff_mask(mb, m9))
    has_e9 = write_patch('notice_9', m9, box9, gen, 'the notice on the boarded door of No. 9: typed sheet, red '
                         'Bezirksamt stamp, the site plan stapled under it (no insignia)')
    scene['decals'].append({'name': 'notice_9', 'file': 'patches/notice_9.png', 'pos': [int(box9[0]), int(box9[1])],
                            'z': -47, 'lit': True, 'normal': True, 'emission': has_e9, 'scene': A,
                            'note': 'the notice read at door_9 (c4b_inspect_notice); the seal strip and the 9 plate '
                                    'stay visible'})
    # lights of the street for the actors (the art has them baked)
    for (nm, pos, col, en, rad, h, extra) in (
            ('sodium_loop', (344, 156), COL['sodium'], 1.0, 170, 40, {}),
            ('tram_inside', (482, 246), COL['warm'], 0.6, 120, 14, {}),
            ('tram_headlamp', (364, 268), '#FAE3A2', 0.35, 50, 6, {}),
            ('marta_window', (60, 215), COL['warm'], 0.35, 50, 10, {}),
            ('timetable_case', (292, 246), COL['cold'], 0.6, 60, 8, {}),
            ('column_grate', (646, 284), '#E6B44C', 0.25, 26, 4, {}),
            ('lorry_tail_l', (718, 263), COL['red'], 0.35, 30, 4, {}),
            ('lorry_tail_r', (786, 263), COL['red'], 0.35, 30, 4, {}),
            ('fence_blinker', (838, 194), COL['red'], 0.25, 30, 6, {}),
            ('stair_11', (66, 238), COL['warm'], 0.2, 26, 6, {})):
        li = {'name': nm, 'pos': [pos[0], pos[1]], 'color': col, 'energy': en, 'radius': rad, 'flicker': 0.0,
              'height': h, 'on_layer': 'playfield', 'scene': A}
        li.update(extra)
        scene['lights'].append(li)
    return base


def build_distant(scene: dict):
    gen = 'tools/pixelgen/env_c4_annex_loop.py'
    sky = EL.sky_layer()
    save(sky.c, 'sky.png', gen, 'dawn sky over the clearance zone: night -> lavender band, low stratus, the last stars')
    dome_n, dome_h = EL.dome_layer(False), EL.dome_layer(True)
    save(dome_n.c, 'dome.png', gen, 'the Great Hall far away in the dawn haze, neutral banners (Reichssiegel)')
    save(dome_h.c, 'dome_hist.png', gen, 'the Great Hall far away, historical banners (Symbols.pick, 12.4)')
    far = EL.far_layer()
    save(far.c, 'far.png', gen, 'the north-south axis under construction: shells in scaffolding, tower cranes')
    if far.em[..., 3].any():
        save(far.em, 'far_e.png', gen, 'far layer -- emission (site lights)')
    mid = EL.mid_layer()
    save(mid.c, 'mid.png', gen, 'cleared blocks: the last tenements, site huts, an excavator')
    if mid.em[..., 3].any():
        save(mid.em, 'mid_e.png', gen, 'mid layer -- emission (lit windows, site lamps)')
    fg = EL.fg_layer()
    save(fg.c, 'fg_loop.png', gen, 'near-black snow banks and bollards (foreground frame of the street)')
    scene['layers'][0:0] = [
        {'name': 'sky', 'file': 'sky.png', 'pos': [0, 0], 'parallax': [0.03, 1.0], 'z': -100, 'normal': False,
         'emission': False, 'lit': False, 'scene': A},
        {'name': 'dome', 'file': 'dome.png', 'pos': [430, 54], 'parallax': [0.08, 1.0], 'z': -96, 'normal': False,
         'emission': False, 'lit': False, 'scene': A, 'hist_variant': 'dome_hist.png',
         'note': 'the Great Hall; banners on its front: neutral / historical (12.4)'},
        {'name': 'far', 'file': 'far.png', 'pos': [0, 62], 'parallax': [0.2, 1.0], 'z': -92, 'normal': False,
         'emission': bool(far.em[..., 3].any()), 'emission_strength': 0.5, 'lit': False, 'scene': A},
        {'name': 'mid', 'file': 'mid.png', 'pos': [0, 150], 'parallax': [0.5, 1.0], 'z': -80, 'normal': False,
         'emission': bool(mid.em[..., 3].any()), 'emission_strength': 0.5, 'lit': False, 'scene': A},
    ]
    scene['layers'].append({'name': 'fg_loop', 'file': 'fg_loop.png', 'pos': [0, 318], 'parallax': [1.25, 1.0],
                            'z': 60, 'normal': False, 'emission': False, 'lit': False, 'scene': A})
    return far


# =========================================================================== the annex (scene B)
# The counter as a y-sorted prop (like the archive counter of berlin_archive): Fengler stands behind it (feet y 276,
# hotspot_offset (18, -24) in L_C4_Annex.tscn: head and shoulders above the counter top at y 248, the registrar sheet
# is 47 px tall), the player (walk band y >= 296) passes in front of it.
COUNTER_BASE_Y = 292
COUNTER_PROP_Y0 = 228                 # what stands on the counter in front of him from here down (his head: y 229)
COUNTER_PROP_X = (1648, 1778)         # the counter (1650..1772) and the perforator's lever


def counter_paint_mask():
    """Pixels the hall's counter() paints (the counter body and what stands on it), read from the paint arrays
    before and after the call -- independent of the light fields."""
    h = EH.Hall({})
    orig = h.counter
    snap = {}

    def counter(form=False):
        rid0, tone0 = h.lay.rid.copy(), h.lay.tone.copy()
        orig(form=form)
        snap['mask'] = (h.lay.rid != rid0) | (h.lay.tone != tone0)
    h.counter = counter
    h.build()
    return snap['mask']


def build_counter_prop(scene: dict, mb, form_mask):
    """props/counter_front.png: the counter body and the things standing on it, cut from annex.png (identical
    pixels, binary alpha); the form patch (gated decal under it) stays uncovered."""
    gen = 'tools/pixelgen/env_c4_annex_hall.py'
    mask = counter_paint_mask()
    keep = np.zeros_like(mask)
    keep[COUNTER_PROP_Y0:L.COUNTER_Y[1] + 2, EH.lx(COUNTER_PROP_X[0]):EH.lx(COUNTER_PROP_X[1])] = True
    mask &= keep
    if form_mask is not None:
        mask &= ~K.dilate(form_mask, 1)
    bx0, by0, bx1, by1 = box_of(mask, pad=0)
    sl = (slice(by0, by1), slice(bx0, bx1))
    a = mask[sl]
    c, n, e = mb
    out = []
    for arr in (c, n):
        p = arr[sl].copy()
        p[..., 3] = np.where(a, 255, 0)
        out.append(p)
    desc = 'the counter „Auskunft · Abgleich“ and what stands on it, cut from annex.png (y-sorted prop: Fengler ' \
           'behind it, the player in front)'
    save(out[0], 'props/counter_front.png', gen, desc)
    save(out[1], 'props/counter_front_n.png', gen, desc + ' -- normal map')
    ee = e[sl].copy()
    ee[..., 3] = np.where(a, ee[..., 3], 0)
    has_e = bool(ee[..., 3].any())
    if has_e:
        save(ee, 'props/counter_front_e.png', gen, desc + ' -- emission mask')
    scene['props'].append({'name': 'counter_front', 'file': 'props/counter_front.png', 'pos': [int(bx0) + X0, int(by0)],
                           'base_y': COUNTER_BASE_Y, 'size': [int(bx1 - bx0), int(by1 - by0)], 'normal': True,
                           'emission': has_e, 'scene': B,
                           'note': 'Fengler (registrar_counter, feet y 276) stands behind it, the walk band '
                                   '(y 296..306) in front of it'})


def build_annex(scene: dict):
    gen = 'tools/pixelgen/env_c4_annex_hall.py'
    base = EH.bake_hall({})
    mb = maps(base.lay)
    write_layer('annex', mb, gen, 'Nebenstelle Sued: shaft and ladder, machine room, card hall, plan, tube station, '
                                  'counter, typists, Staatspolizei door (x 846..1920)')
    scene['layers'].append({'name': 'annex', 'file': 'annex.png', 'pos': [X0, 0], 'parallax': [1, 1], 'z': -50,
                            'normal': True, 'emission': True, 'emission_strength': 0.55, 'lit': True})
    form_mask = None
    for key, gate, nm, desc in (
            ('drawer', {'after': ['c4d_inspect_drawer']}, 'drawer_s8_open',
             'drawer Sued 8 pulled out: 212 cards, the red C-17 tabs'),
            ('tube', {'after': ['c4d_inspect_tube']}, 'capsule_open', 'the capsule opened, the slip taken'),
            ('form', {'after': ['c4d_talk_registrar']}, 'form_counter', 'the form laid out on the counter: name and address')):
        h = EH.bake_hall({key: True})
        m = maps(h.lay)
        dmask = diff_mask(mb, m)
        if key == 'form':
            form_mask = dmask
        box = box_of(dmask)
        has_e = write_patch(nm, m, box, gen, desc)
        e = {'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]) + X0, int(box[1])], 'z': -46,
             'lit': True, 'normal': True, 'emission': has_e, 'fade': 0.3, 'scene': B}
        e.update(gate)
        scene['decals'].append(e)
    hh = EH.bake_hall({'hist': True})
    mh = maps(hh.lay)
    dm = diff_mask(mb, mh)
    for nm, xr, desc in (('plate_counter', (EH.lx(1640), EH.lx(1790)), 'the plate above the counter: emblem, NEBENSTELLE SUED'),
                         ('plate_stapo', (EH.lx(1820), EH.lx(1920)), 'the emblem above the Staatspolizei door')):
        box = box_of(dm, xr=xr)
        has_e = write_patch(nm, mb, box, gen, desc, hist_m=mh)
        scene['decals'].append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]) + X0, int(box[1])],
                                'z': -48, 'lit': True, 'normal': True, 'emission': has_e, 'scene': B,
                                'hist_variant': 'patches/%s_hist.png' % nm,
                                'note': 'insignia site (12.4): neutral Reichssiegel / historical state eagle'})
    build_counter_prop(scene, mb, form_mask)
    fg = EH.fg_layer()
    save(fg.c, 'fg_annex.png', gen, 'near-black foreground of the annex: chairs, a cable reel, a trolley')
    scene['layers'].append({'name': 'fg_annex', 'file': 'fg_annex.png', 'pos': [1058, 318], 'parallax': [1.25, 1.0],
                            'z': 60, 'normal': False, 'emission': False, 'lit': False, 'scene': B,
                            'note': 'pos x = 846 * 1.25: its left edge meets the screen edge at the annex camera stop'})
    for i, fx in enumerate(L.FIXTURES):
        scene['lights'].append({'name': 'tube_%d' % i, 'pos': [fx, 82], 'color': COL['tube'], 'energy': 0.45,
                                'radius': 170, 'flicker': 0.05 if i == 5 else 0.0, 'height': 34,
                                'on_layer': 'playfield', 'scene': B})
    for (nm, pos, col, en, rad, h) in (
            ('shaft_bulkhead', (911, 118), COL['warm'], 0.45, 80, 10),
            ('machine_lamp', (995, 96), COL['machine'], 0.35, 100, 20),
            ('counter_lamp', (1743, 228), COL['warm'], 0.8, 110, 14),
            ('stapo_lamp', (1894, 236), COL['red'], 0.3, 30, 6),
            ('tube_station', (1548, 202), '#86A28A', 0.2, 30, 6)):
        scene['lights'].append({'name': nm, 'pos': [pos[0], pos[1]], 'color': col, 'energy': en, 'radius': rad,
                                'flicker': 0.0, 'height': h, 'on_layer': 'playfield', 'scene': B})
    return base


# =========================================================================== strips
def build_strips(scene: dict, street, hall, far):
    gen = 'tools/pixelgen/env_c4_annex_fx.py'

    def fx(nm, arr, pos, frames, fps, z, scene_id, desc, parallax=(1.0, 1.0), **kw):
        save(arr, 'fx/%s.png' % nm, gen, desc)
        e = {'type': 'anim_sprite', 'name': nm, 'file': 'fx/%s.png' % nm, 'frames': frames, 'fps': fps,
             'pos': [int(pos[0]), int(pos[1])], 'parallax': [parallax[0], parallax[1]], 'z': z, 'lit': False,
             'scene': scene_id}
        e.update(kw)
        scene['fx'].append(e)

    def decal(nm, arr, pos, frames, fps, scene_id, desc, em=None, lit=True, z=-47, folder='life', **kw):
        save(arr, '%s/%s.png' % (folder, nm), gen, desc)
        if em is not None:
            save(em, '%s/%s_e.png' % (folder, nm), gen, desc + ' -- emission')
        e = {'name': nm, 'file': '%s/%s.png' % (folder, nm), 'pos': [int(pos[0]), int(pos[1])], 'z': z,
             'frames': frames, 'fps': fps, 'lit': lit, 'normal': False, 'emission': em is not None,
             'scene': scene_id}
        e.update(kw)
        scene['decals'].append(e)

    # ---- street: snow in two halves (texture width limit), steam, exhaust, chimney, cranes, blinker, Ilse
    half = L.SEAM // 2
    for k, x0 in enumerate((0, half)):
        fx('snow_%s' % 'ab'[k], EFX.snow_strip(half, 312, 24, 8, 120, seed=11 + k),
           (x0, 0), 24, 8, 30, A, 'light snowfall over the loop, two depths (%s half)' % ('left', 'right')[k])
    fx('steam_s2', EFX.plume_strip(40, 84, 16, seed=3, ramp='SN', base=4.4, dens=0.9, warm_root=True),
       (L.COLUMN[0] - 4, L.BASE_Y - 82), 16, 8, -40, A, 'warm air steaming out of the grate at the foot of S 2')
    fx('exhaust', EFX.plume_strip(28, 26, 12, seed=5, ramp='D', base=3.4, dens=0.8, drift=0.6),
       (L.LORRY[1] - 6, 238), 12, 8, -45, A, "the lorry's engine runs: exhaust in the frost")
    fx('chimney_11', EFX.plume_strip(36, 40, 16, seed=7, ramp='D', base=3.0, dens=0.9, drift=0.8),
       (6, -30), 16, 5, -45, A, 'morning smoke from the chimney of No. 11')
    for i, (cx, ch) in enumerate(EL.CRANE_TOPS):
        on = np.zeros((3, 3, 4), np.uint8)
        on[1, :] = K.rgba('R', 4)
        on[:, 1] = K.rgba('R', 4)
        on[1, 1] = K.rgba('L', 5)
        y = 62 + (190 - 14) - ch - 6
        fx('crane_light_%d' % i, EFX.blink_strip(3, 3, on, frames=4, on_frames=(0, 1)), (cx + 1, y), 4, 2, -91, A,
           'aviation light on a tower crane of the axis (1 Hz)', parallax=(0.2, 1.0))
    c, em = street.lay.c, street.lay.em
    f1 = L.FENCE[1]
    bx0, by0, bw, bh = f1 - 10, 192, 7, 5
    on = c[by0:by0 + bh, bx0:bx0 + bw].copy()
    off = on.copy()
    lit = em[by0:by0 + bh, bx0:bx0 + bw][..., 3] > 0
    off[lit] = K.rgba('R', 1.6)
    decal('fence_blinker', K.strip([on, on, off, off]), (bx0, by0), 4, 2, A, 'red blinker on the site hoarding (1 Hz)',
          em=K.strip([em[by0:by0 + bh, bx0:bx0 + bw]] * 2 + [np.zeros_like(on)] * 2), lit=False)
    wx0, wx1 = L.ILSE_WIN
    wy0, wy1 = 232, 256
    crop = c[wy0:wy1, wx0:wx1].copy()
    ecrop = em[wy0:wy1, wx0:wx1].copy()
    strip = EFX.ilse_strip(crop, frames=48, fps=6)
    fr = np.split(strip, 48, axis=1)
    efr = []
    for f in fr:
        e = ecrop.copy()
        changed = np.any(f != crop, axis=-1)
        glow = changed & (f[..., 0].astype(int) + f[..., 1] > 360)
        e[changed & ~glow] = 0
        e[glow] = f[glow]
        efr.append(e)
    decal('ilse', strip, (wx0, wy0), 48, 6, A,
          'Ilse on the last bench of tram 74: looks out, breathes on the glass, wipes a peephole (life strip)',
          em=K.strip(efr), lit=False)

    # ---- annex: fans, dust, the capsule, the failing tube, the typists
    hc, hem = hall.lay.c, hall.lay.em
    for i, (cx, cy, r) in enumerate(L.FANS):
        x0, y0 = EH.lx(cx) - r - 3, cy - r - 3
        sz = 2 * r + 7
        frames = []
        for k in range(6):
            hk = EH.bake_hall({'fan_phase': -k * (np.pi / 2) / 6}) if k else hall
            frames.append(hk.lay.c[y0:y0 + sz, x0:x0 + sz].copy())
        decal('fan_%s' % 'ab'[i], K.strip(frames), (x0 + X0, y0), 6, 12, B,
              'axial fan %s behind the grille, turning (6 frames = a quarter turn of the 4 blades)' % 'AB'[i])
    fx('dust_fans', EFX.dust_strip(124, 150, 32, 6, 46, seed=21, ramp='G', tones=(5, 4)), (934, 74), 32, 6, 12, B,
       'dust in the draught of the fans')
    fx('dust_hall', EFX.dust_strip(440, 160, 32, 4, 70, seed=22, ramp='G', tones=(5, 4), drift=(-1.5, 1.5),
                                    rise=(-1.5, 2.0)), (1060, 80), 32, 4, 12, B, 'dust under the tubes of the card hall')
    g0, g1 = EH.lx(1698), EH.lx(1762)
    gy0, gy1 = L.TUBES_Y[0] - 2, L.TUBES_Y[0] + 10
    base_g = hc[gy0:gy1, g0:g1].copy()
    frames = []
    for k in range(72):
        fr_ = base_g.copy()
        if k < 4:
            cxp = (g1 - g0) - 10 - k * 16
            for yy in range(3, 8):
                for xx in range(cxp, cxp + 8):
                    if 0 <= xx < g1 - g0:
                        fr_[yy, xx] = K.rgba('S', 1.6 if yy > 5 else 4.6)
            for xx in range(cxp + 8, min(g1 - g0, cxp + 14)):
                fr_[5, xx] = K.rgba('G', 5)
        frames.append(fr_)
    decal('capsule_glass', K.strip(frames), (g0 + X0, gy0), 72, 12, B,
          'a capsule shooting through the glass length of the tube (every 6 s)', folder='fx')
    tx0 = EH.lx(L.FIXTURES[5]) - 20
    ty0 = L.FIXTURE_Y
    on = hc[ty0:ty0 + 8, tx0:tx0 + 40].copy()
    eon = hem[ty0:ty0 + 8, tx0:tx0 + 40].copy()
    off = on.copy()
    lit_ = eon[..., 3] > 0
    off[lit_] = K.rgba('G', 1.6)
    seq = [on] * 24
    eseq = [eon] * 24
    for k in (9, 10, 17):
        seq[k], eseq[k] = off, np.zeros_like(eon)
    decal('tube_flicker', K.strip(seq), (tx0 + X0, ty0), 24, 8, B, 'a failing fluorescent tube (drops out twice in 3 s)',
          em=K.strip(eseq), lit=False, folder='fx')
    gm = hall.glass_mask
    for (tx, v) in L.TYPISTS:
        x0 = EH.lx(tx) - 20
        y0 = L.GLASS_Y[1] - 40
        crop = hc[y0:y0 + 38, x0:x0 + 40].copy()
        decal('typist_%s' % v, EFX.typist_strip(crop, gm[y0:y0 + 38, x0:x0 + 40], 16, v), (x0 + X0, y0), 16, 6, B,
              'a typist behind the glass of the counter (life strip)')


# =========================================================================== scene.json
def hotspot_info():
    what = {
        'door_9': 'house No. 9 of the half-cleared block: boarded double door, red seal strip, the notice; above it the '
                  'exposed wall with three storeys of wallpaper',
        'timetable_case': "the shelter's lit timetable case — Konrad's light table (his tracing sheets after the puzzle)",
        'marta_tram': 'Marta Vogel (x 422) beside the open front door of tram 74; Ilse (life strip) at the last window',
        'column_s2': 'the advertising column S 2: warm air steaming from the grate at its foot; after the inspect the '
                     'poster is torn back from the steel door',
        'loading_hatch': 'the freight hatch under the hoist: crates stencilled C-17/45, one split, a card in the snow, '
                         'the lorry backed up to it',
        'drawer_s8': 'the drawer bank „Süd 1 … Süd 12“; Süd 8 shows a red tab, after the inspect it is pulled out '
                     '(Süd 3 stands a finger\'s width open all along, a card up: the hidden find exp_brandt_card)',
        'plan_wall': 'the framed ventilation plan of the annex, Blatt 3, three shafts, gez. K. Adler',
        'tube_station': 'the pneumatic-tube station, the capsule from the Staatspolizei in the tray',
        'registrar_counter': 'the counter „Auskunft · Abgleich“, Registrator Fengler (x 1734, feet y 276) behind it '
                             '(prop counter_front, base_y 292, hides his legs); stamps, forms, the perforator, the lamp',
        'guard_annex': 'a guard (existing `guard`) at the steel door to the Staatspolizei corridor; never talks',
    }
    out = {}
    for k, (x, y) in L.HOTSPOTS.items():
        out[k] = {'kind': 'npc_anchor' if k == 'guard_annex' else 'story', 'stand': [x, y], 'focus': [x, 270],
                  'what': what[k], 'object_x': list(L.HOTSPOT_PROPS[k][1])}
    return out


def build_scene(preview_dir=None):
    t0 = time.time()
    scene = {'id': 'berlin_annex', 'palette': 'annex', 'world_size': [L.WORLD_W, L.WORLD_H],
             'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]}, 'camera_zones': L.CAMERA_ZONES,
             'canvas_modulate': '#C2C9D8', 'layers': [], 'props': [], 'decals': [], 'lights': [], 'fx': [],
             'actors': []}
    notes = []
    street = build_street(scene, notes)
    far = build_distant(scene)
    hall = build_annex(scene)
    build_strips(scene, street, hall, far)
    scene['actors'] = [
        {'scene': 'res://scenes/levels/karsk/KarskCrows.tscn', 'pos': [700, 300],
         'props': {'perches': [[676, 176], [690, 176], [705, 176], [722, 176]],
                   'sprite': 'res://assets/environments/karsk_railyard/actors/crows.png', 'scare_radius': 34.0,
                   'nervous_radius': 80.0},
         'gen': 'env_c4_annex', 'scene_id': A,
         'note': 'hooded crows on the contact wire over the loop; they lift when Konrad comes to the hatch'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [422, 301],
         'props': {'points': [[417, 262]], 'sprite': 'res://assets/environments/karsk_railyard/actors/breath_puff.png',
                   'interval': 4.4},
         'gen': 'env_c4_annex', 'scene_id': A, 'note': "Marta's breath in the frost"},
    ]
    scene.update({
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[1]],
                     [L.WALK_X[0], L.WALK_BAND[1]]],
        'blockers': [dict(L.BLOCKER)],
        'spawns': {k: [v[0], v[1]] for k, v in L.SPAWNS.items()},
        'hotspots': {k: [v[0], v[1]] for k, v in L.HOTSPOTS.items()},
        'zones': L.ZONES,
        'looks': [
            {'name': 'loop', 'scene': A, 'canvas_modulate': '#C2C9D8', 'grade': 'annex_loop'},
            {'name': 'annex', 'scene': B, 'canvas_modulate': '#D2DCD2', 'grade': 'annex'},
        ],
        'hotspot_info': hotspot_info(),
        'npcs': {k: dict(v) for k, v in L.NPCS.items()},
        'gates_doc': 'Entries with "after" (objectives that must be complete), "until" (hidden once one of them is '
                     'complete) or "choice" are built by registry_level.gd (base of scripts/levels/c4/annex_level.gd) and '
                     'shown while the condition holds; "fade" = seconds of the live cross-fade. "scene" (one id or a '
                     'list; actors use "scene_id") = only built when the level plays that Story scene (decided at load: '
                     'every C4 scene starts with a level load). camera_zones clamp the camera to the walk area of the '
                     'scene played (the street never shows underground, the annex never the sky).',
        'notes': [
            'Two walk areas in one file: L_C4_AnnexA (street, x 18..822) left of the permanent blocker shaft_wall, '
            'L_C4_AnnexB (annex, x 846..1902) right of it; the camera seam is x 846.',
            'Every spawn, hotspot and NPC anchor name and position of C4_DESIGN 4.2 is kept (story placeholder).',
            'Palette: data/chapters/c4.json palettes.annex + the proposed ramp "lamp" (sodium light, lit windows, '
            'the counter lamp) -- see asset_manifest_parts/env_c4_annex.md.',
        ],
        'meta': {'mode': 'side', 'feet_y': L.FEET, 'generator': GEN, 'date': K.DATE,
                 'palette_ramps': {k: v for k, v in K.ANNEX.items()}},
    })
    global BUILD_S
    BUILD_S = round(time.time() - t0, 1)
    if preview_dir:
        preview(scene, preview_dir)
    return scene


def merge_foreign(scene: dict):
    """Keep what other streams added to scene.json: foreign actors and unknown top-level keys."""
    p = os.path.join(ENV_DIR, 'scene.json')
    try:
        with open(p, encoding='utf-8') as f:
            old = json.load(f)
    except (OSError, ValueError):
        return []
    kept = []
    for a in old.get('actors', []):
        if isinstance(a, dict) and a.get('gen') != 'env_c4_annex':
            scene['actors'].append(a)
            kept.append('actor ' + str(a.get('scene')))
    for k, v in old.items():
        if k not in scene and k != 'placeholder':
            scene[k] = v
            kept.append('key ' + k)
    for sec in ('hotspots', 'spawns'):
        for k, v in (old.get(sec) or {}).items():
            if k not in scene[sec]:
                scene[sec][k] = v
                kept.append('%s %s' % (sec, k))
    return kept


def write_scene(scene: dict):
    kept = merge_foreign(scene)
    KEEP.write_json(os.path.join(ENV_DIR, 'scene.json'), scene)   # same content as before: byte for byte
    return kept


def write_provenance():
    files = [{'path': p, 'generator': g, 'description': d} for (p, g, d) in PRODUCED]
    have = {f['path'] for f in files}
    old = KEEP.read_json(os.path.join(ENV_DIR, 'provenance.json'))
    files += [r for r in KEEP.merge_rows([], old, FAMILY, ROOT) if r.get('path') not in have]   # foreign rows stay
    data = {'environment': 'berlin_annex', 'level': 'scenes/levels/L_C4_Annex.tscn', 'generator': GEN,
            'date': K.DATE, 'license': 'original work, generated deterministically by the project tools (no third-party '
                                      'images, no traced references)', 'files': files}
    with open(os.path.join(ENV_DIR, 'provenance.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')


# =========================================================================== preview (dev aid)
def preview(scene, out_dir, hist=False):
    """Composite the layers + static decals per scene at a few camera stops (python, no engine)."""
    os.makedirs(out_dir, exist_ok=True)

    def load(rp):
        if hist:
            hp = rp[:-4] + '_hist.png'
            if os.path.isfile(os.path.join(ENV_DIR, hp)):
                rp = hp
        return Image.open(os.path.join(ENV_DIR, rp)).convert('RGBA')
    shots = []
    for sid, cams in ((A, (0, 206)), (B, (846, 1066, 1280))):
        for cam in cams:
            img = Image.new('RGBA', (640, 360), (0, 0, 0, 255))
            ents = [e for e in scene['layers'] if e.get('scene', sid) == sid]
            ents += [dict(e, parallax=[1, 1]) for e in scene['decals'] if e.get('scene', sid) == sid
                     and not e.get('after')]
            ents.sort(key=lambda e: e.get('z', 0))
            for e in ents:
                im = load(e['file'])
                fr = int(e.get('frames', 1))
                if fr > 1:
                    im = im.crop((0, 0, im.size[0] // fr, im.size[1]))
                px = e.get('parallax', [1, 1])
                x = int(round(e['pos'][0] - cam * float(px[0])))
                tmp = Image.new('RGBA', (640, 360), (0, 0, 0, 0))
                tmp.paste(im, (x, int(e['pos'][1])))
                img.alpha_composite(tmp)
            p = os.path.join(out_dir, 'prev_%s_%04d%s.png' % (sid[-1], cam, '_hist' if hist else ''))
            img.convert('RGB').save(p)
            shots.append(p)
    return shots


def main(argv):
    pv = None
    for a in argv:
        if a.startswith('--preview='):
            pv = a.split('=', 1)[1]
    os.makedirs(ENV_DIR, exist_ok=True)
    clean_previous()
    scene = build_scene(pv)
    PRODUCED.extend(EDOC.build())
    kept = write_scene(scene)
    write_provenance()
    if pv:
        preview(scene, pv, hist=True)
    bad = []
    for (p, _g, _d) in PRODUCED:
        if p.endswith('_n.png') or not p.endswith('.png'):
            continue
        arr = np.asarray(Image.open(os.path.join(ROOT, p)).convert('RGBA'))
        _n, off = K.palette_report(arr)
        if off:
            bad.append((p, off[:4]))
    print('env_c4_annex: %d files, %d layers, %d decals, %d fx, %d lights in %.1f s' % (
        len(PRODUCED), len(scene['layers']), len(scene['decals']), len(scene['fx']), len(scene['lights']), BUILD_S))
    for n_ in K.check_c4_palette():
        print('  palette note:', n_)
    if kept:
        print('  kept from the previous scene.json:', ', '.join(kept))
    for b in bad:
        print('  OFF PALETTE', b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
