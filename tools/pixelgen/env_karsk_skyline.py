"""env_karsk_skyline -- redesigned background skyline for scene A1 'Verladebahnhof Karsk' (fictional Soviet
provincial railway town, winter dawn 1964).  Replaces the parallax planes far_city (0.12), far_industry (0.25),
mid (0.45) and near_bg (0.72) of assets/environments/karsk_railyard with drop-in files of identical size, pos,
parallax and conventions in assets/environments/karsk_skyline/.

    py -3 -P tools/pixelgen/env_karsk_skyline.py              layers + test manifest + palette check + previews
    py -3 -P tools/pixelgen/env_karsk_skyline.py --no-preview  skip the review composites

Outputs: assets/environments/karsk_skyline/<plane>.png + _n (normal, OpenGL +Y up) + _e (emission) and
mid_hist.png (+ _n / _e: hammer & sickle beside the rooftop slogan, TECHNICAL_ARCHITECTURE 12.4);
assets/environments/karsk_skyline/skyline.json (layer + fx + hotspot entries for the lead to merge);
tests/visual/skyline/scene.json (copy of the railyard manifest with these layers / fx swapped in).
Deterministic (fixed seeds), no network; original procedural art, palette 'karsk' + the shared C-17 red ramp.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import env_karsk_skyline_lib as SL  # noqa: E402
from env_karsk_skyline_lib import (NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, PLANES, put, rect, hline, vline,  # noqa: E402
                                   line, Haze, vfog, N_UP)
import env_karsk_skyline_kit as K  # noqa: E402
import env_karsk_skyline_arch as A  # noqa: E402
import env_karsk_skyline_far as F  # noqa: E402
import env_karsk_skyline_near as N  # noqa: E402

SLOGAN = 'СЛАВА ТРУДУ!'
RAIL_Y = 210        # world y of the far railway on the mid plane (= karsk_railyard RAIL_Y_MID, KarskTrain home y)


def embankment_mid(L, rail_y, B):
    """Railway embankment across the mid plane: rail heads catching the sky on row rail_y-1, sleepers on rail_y,
    ballast, a snowy shoulder and the shadowed slope down to the plane base (hazed by the ground fog pass)."""
    rng = np.random.default_rng(210)
    for x in range(L.w):
        put(L, x, rail_y - 1, SA[4] if (x * 7) % 11 < 3 else TE[2], N_UP)
        put(L, x, rail_y, TE[1], N_UP)
        put(L, x, rail_y + 1, SA[2] if rng.random() < 0.3 else TE[3], N_UP)
        put(L, x, rail_y + 2, SN[2] if rng.random() < 0.55 else SA[4], N_UP)
        put(L, x, rail_y + 3, SA[4] if rng.random() < 0.4 else SA[2])
        for yy in range(rail_y + 4, B + 3):
            t = (yy - rail_y - 4) / max(1.0, B - rail_y - 5)
            c = TE[3] if SL.dith(x, yy, 0.75 - t * 0.6) else SA[2]
            if (x + yy * 3) % 37 == 0:
                c = SA[4]
            put(L, x, yy, c)


# =========================================================================== MID (0.45)
def make_mid(hist=False):
    """mid plane, base y 231, scale 4.75 px/m.  Layout (layer x = screen x at camera 0):
        20-70    brick mill / office building of the elevator (no chimney: the TETs stacks of far_industry
                 rise behind it)
        76-304   grain elevator: 5 silos (one with the patched shell hole), gallery with the rooftop slogan
                 СЛАВА ТРУДУ! (+ emblem: gear-and-wheat / hammer & sickle in mid_hist), working house, conveyor
                 bridge, receiving building                      -> exp_grain, cam 0 left third
        336-452  five-domed church used as a warehouse (СКЛАД)  -> cam 0 between tea stall and signal box
        467-593  Khrushchyovka, 2 sections, 5 storeys (balconies, laundry, firewood, antennas, canopies)
        604-640  garages (the sun at cam 0)
        640-790  Stalinist railway administration with clock tower, spire and star (cam 640 centre, cam 1280 left)
        850-990  panel block under construction (2 storeys up: stays below the office roof at cam 1280)
        1000     tower crane, jib over the site, panel hoisted high, red jib lamp
        990-1216 log houses, garages, birches -- kept low: cooling towers and sun at cam 1280;
        all x    far railway embankment, rail heads y 209 / sleepers y 210 (KarskTrain runs in front of this plane);
        1134-1164 district boiler house + red/white striped steel chimney (smoke anchor 1150,107)."""
    S = K.STYLES['mid']
    ppm = SL.ppm('mid')
    g = PLANES['mid']
    B = g['base']
    L = SL.world_layer('mid')
    meta = {'smoke': [], 'lamps': []}
    # ---- far left: warehouse + elevator boiler house with its brick chimney
    K.facade(L, -2, B - 20, 30, 20, S['brick'])
    K.snow_line(L, -2, B - 21, 30, S, 1, 1)
    K.facade(L, 26, B - 26, 46, 26, S['brick'])
    for wx in (31, 41, 51, 61):
        K.arched_window(L, wx, B - 20, 5, 9, S)
    K.snow_line(L, 25, B - 27, 48, S, 1, 2)
    # ---- grain elevator + rooftop slogan
    el = K.grain_elevator(L, 76, B, S, ppm, seed=3)
    gx0, gx1 = el['gallery_x']
    emb = 'hs11' if hist else 'gw11'
    sw = K.slogan_width(SLOGAN, emb)
    sl = K.rooftop_slogan(L, gx0 + (gx1 - gx0 - sw) // 2, el['gallery_top'], SLOGAN, S, emblem=emb, seed=5)
    meta['slogan'] = sl
    pm = 1.75 * ppm                                                   # a person on this plane: ~8 px
    K.tiny_person(L, gx1 - 9, el['gallery_top'] + 1, int(round(pm)), TE[1], SA[3])     # worker on the gallery
    vline(L, gx1 - 5, el['gallery_top'] - 9, 10, WO[3])                                  # his ladder to the letters
    meta['grain_mark'] = [76 + 2 * 24 + 12, el['silos'][3] + 40]
    K.birch(L, 312, B, 46, S, seed=11)
    K.birch(L, 326, B, 34, S, seed=12)
    # ---- church (warehouse)
    ch = A.church(L, 336, B, S, seed=5)
    meta['church'] = ch
    K.birch(L, 456, B, 40, S, seed=13)
    # ---- Khrushchyovka (2 sections; fully behind the signal box at cam 0)
    kh = K.khrushchyovka(L, 467, B, S, ppm, sections=2, bays=5, floors=5, seed=4, lit=0.05, bay_px=12)
    meta['khrushchyovka'] = kh
    # ---- garages under the sun at cam 0
    A.garages(L, 606, B, 3, S, ppm, seed=2)
    K.birch(L, 632, B, 30, S, seed=14)
    # ---- Stalinist railway administration
    st = A.stalinka(L, 640, B, S, seed=6, lit=3)
    meta['stalinka'] = st
    # ---- low gap + log houses
    A.izba(L, 798, B, S, ppm, seed=21, mat='logs')
    K.birch(L, 840, B, 38, S, seed=15)
    # ---- construction site: block in progress (low: hidden behind the office at cam 1280), crane with a panel
    #      hoisted high (well above the office roofline)
    kb = K.khrushchyovka(L, 850, B, S, ppm, sections=2, bays=5, floors=5, seed=5, built=2, lit=0.0)
    for (px_, pose) in ((kb['x'] + 70, 'stand'), (kb['x'] + 96, 'walk')):                 # erectors on the slab
        K.tiny_person(L, px_, kb['top'], int(round(1.75 * ppm)), TE[1], SA[3], pose=pose)
    lamp = A.tower_crane(L, 1000, B, 139, 100, 30, [TE[2], TE[3], SA[3]], lamp=RED[3], hook_x=944, hook_y=118,
                         load=(12, 4), load_cols=[SA[3], SA[4]])
    meta['lamps'].append(lamp)
    # ---- low east end: log houses, garages, birches (kept below y ~205 for the train / tower views)
    for i, xx in enumerate((1012, 1052, 1092)):
        A.izba(L, xx, B, S, ppm, w_m=7.0, wall_m=2.6, roof_m=3.6, seed=30 + i, mat='logs', lit=(i == 1))
    A.garages(L, 1166, B, 4, S, ppm, seed=7)
    # district boiler house + striped steel chimney (cam 1280: right of the office, smoke drifts past the sun)
    K.facade(L, 1134, B - 20, 30, 20, S['brick'])
    K.snow_line(L, 1133, B - 21, 32, S, 1, 4)
    band = [[RED[1], RED[2], RED[3]], [SA[3], SA[4], SA[5]]]
    meta['smoke'].append(('mid_chimney_e', K.chimney(L, 1150, B - 20, 104, 6, 4, S['conc'], bands=7,
                                                     band_cols=band, seed=4)))
    for i, (bx, bh) in enumerate(((1046, 40), (1086, 30), (1126, 34), (1214, 38))):
        K.birch(L, bx, B, bh, S, seed=40 + i)
    # ---- far railway embankment in front of the town (KarskTrain rail: wheels on y RAIL_Y, sprites in front of
    #      this layer at z -73), then the ground haze
    embankment_mid(L, RAIL_Y, B)
    hz = Haze([[NI[2], NI[3], TE[1], TE[2], TE[3], TE[4], SA[2], SA[3], SA[4], SA[5]],
               [SA[0], SA[1], SA[2], SA[3], SA[4], SA[5]],
               [ST[1], ST[2], ST[3], ST[4], ST[5], SA[4], SA[5]],
               [WO[1], WO[2], WO[3], WO[4], ST[4], ST[5], SA[4], SA[5]],
               [RU[1], RU[2], RU[3], ST[4], ST[5]],
               [SN[0], SN[1], SN[2], SN[3]]])
    hz.shift(L, vfog(L, 198, B + 2, 3.2, 1.6))
    return L, meta


# =========================================================================== save / manifest
EMISSION_STRENGTH = {'far_city': 0.35, 'far_industry': 0.35, 'mid': 0.45, 'near_bg': 0.45}
# anim strips of the railyard (assets/environments/karsk_railyard/fx): mouth/origin inside a frame, frame size, n
FX_STRIPS = {'smoke_ribbon_a': (10, 130, 72, 132, 8), 'smoke_ribbon_b': (10, 130, 72, 132, 8),
             'smoke_ribbon_far': (10, 94, 56, 96, 8), 'tower_plume': (20, 62, 84, 64, 8),
             'chimney_wisp': (5, 58, 30, 60, 8), 'steam_puffs': (6, 42, 26, 44, 6)}
REL_RAILYARD = '../../../assets/environments/karsk_railyard/'   # from tests/visual/skyline/
REL_SKYLINE_FROM_RAILYARD = '../karsk_skyline/'                 # from assets/environments/karsk_railyard/


def save_plane(L, plane, hist_layer=None, out_dir=SL.OUT_DIR):
    g = PLANES[plane]
    C = SL.crop_rows(L, g['top'], g['top'] + g['H'])
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, plane)
    info = C.save(base, normal=True, strength=3.0)
    if hist_layer is not None:
        H = SL.crop_rows(hist_layer, g['top'], g['top'] + g['H'])
        H.save(base + '_hist', normal=True, emission=info['emission'], strength=3.0)
    assert (C.w, C.h) == (g['W'], g['H']), (plane, C.w, C.h)
    return C, info


def layer_entry(plane, info, file_prefix):
    g = PLANES[plane]
    e = {'name': plane, 'file': file_prefix + plane + '.png', 'pos': [0, g['top']], 'parallax': [g['p'], 0.0],
         'z': g['z'], 'normal': True, 'emission': bool(info['emission']), 'lit': True}
    if e['emission']:
        e['emission_strength'] = EMISSION_STRENGTH[plane]
    return e


def anim(key, mouth, plane, fps, file_prefix='fx/'):
    ox, oy, fw, fh, n = FX_STRIPS[key]
    g = PLANES[plane]
    return {'type': 'anim_sprite', 'file': file_prefix + key + '.png', 'frames': n, 'fps': fps,
            'pos': [int(mouth[0] - ox), int(mouth[1] - oy)], 'parallax': g['p'], 'z': g['z'] + 1,
            'emission': False, 'frame_size': [fw, fh], 'layer': plane}


def fx_entries(meta, file_prefix='fx/'):
    """Smoke / steam strips of the railyard placed on the new chimney mouths (one entry per source)."""
    fx = []
    fi = dict(meta['far_industry']['smoke'])
    fx.append(anim('smoke_ribbon_a', fi['tets_a'], 'far_industry', 4, file_prefix))
    fx.append(anim('smoke_ribbon_b', fi['tets_b'], 'far_industry', 5, file_prefix))
    fx.append(anim('smoke_ribbon_far', fi['fi_east'], 'far_industry', 4, file_prefix))
    fc = meta['far_city']
    fx.append(anim('smoke_ribbon_far', dict(fc['smoke'])['fc_chimney'], 'far_city', 4, file_prefix))
    fx.append(anim('tower_plume', fc['towers'][0], 'far_city', 5, file_prefix))
    fx.append(anim('tower_plume', fc['towers'][1], 'far_city', 4, file_prefix))
    fx.append(anim('smoke_ribbon_far', dict(meta['mid']['smoke'])['mid_chimney_e'], 'mid', 4, file_prefix))
    nb = meta['near_bg']
    for i, (nm, xy) in enumerate(nb['smoke']):
        fx.append(anim('chimney_wisp', xy, 'near_bg', 5 + (i % 2), file_prefix))
    for nm, xy in nb['steam']:
        fx.append(anim('steam_puffs', xy, 'near_bg', 5, file_prefix))
    return fx


def hotspot_marks(meta, man=None):
    """hotspot_info marks pointing at the redrawn objects, for the CURRENT player positions of the railyard
    manifest (the camera centres on the player: cam = clamp(x - 320, 0, 1280)); player positions never change."""
    man = man or json.load(open(os.path.join(SL.SRC_ENV, 'scene.json'), encoding='utf-8'))
    hs = man.get('hotspots', {})

    def cam_for(name):
        x = hs.get(name, [320, 0])[0]
        return min(1280, max(0, x - 320))

    gm = meta['mid']['grain_mark']
    t1, _t2 = meta['far_city']['towers']
    bx0, bw, wall_top = meta['near_bg']['barrack']
    c = cam_for('exp_cooling_towers')
    pf = PLANES['far_city']['p']
    return {'exp_grain': {'mark': [int(gm[0]), int(gm[1])], 'layer': 'mid'},
            'exp_cooling_towers': {'mark': [int(round(c + t1[0] - c * pf)), int(t1[1] + 26)], 'layer': 'far_city'},
            'exp_barrack': {'mark': [int(bx0 + bw // 2), int(wall_top - 8)], 'layer': 'near_bg'}}


def write_manifests(results, meta):
    """skyline.json (entries for the lead, paths relative to karsk_railyard) + the test manifest."""
    entries = {pl: layer_entry(pl, results[pl][1], REL_SKYLINE_FROM_RAILYARD) for pl in results}
    sky = {'_doc': 'Drop-in replacement planes for assets/environments/karsk_railyard/scene.json (generator: '
                   'tools/pixelgen/env_karsk_skyline.py).  layers: replace the four entries of the same name '
                   '(file paths are relative to karsk_railyard).  fx: replace every anim_sprite whose "layer" is '
                   'far_city / far_industry / mid / near_bg.  laundry_pegs: KarskLaundry actor props.pegs.  '
                   'hotspot_marks: optional hotspot_info marks (player positions of exp_* are unchanged).',
           'layers': [entries[k] for k in ('far_city', 'far_industry', 'mid', 'near_bg') if k in entries],
           'fx': fx_entries(meta), 'laundry_pegs': meta['near_bg']['pegs'], 'hotspot_marks': hotspot_marks(meta)}
    with open(os.path.join(SL.OUT_DIR, 'skyline.json'), 'w', encoding='utf-8') as f:
        json.dump(sky, f, indent=1, ensure_ascii=False)
    # ---- test manifest: copy of the railyard manifest with the planes / fx swapped, all paths resolvable
    man = json.load(open(os.path.join(SL.SRC_ENV, 'scene.json'), encoding='utf-8'))
    planes = set(entries)
    layers = []
    for Ly in man['layers']:
        if Ly['name'] in planes:
            e = dict(entries[Ly['name']])
            e['file'] = '../../../assets/environments/karsk_skyline/' + Ly['name'] + '.png'
            layers.append(e)
        else:
            Ly = dict(Ly)
            Ly['file'] = REL_RAILYARD + Ly['file']
            layers.append(Ly)
    man['layers'] = layers
    for P in man.get('props', []):
        P['file'] = REL_RAILYARD + P['file']
    for D in man.get('decals', []):
        D['file'] = REL_RAILYARD + D['file']
    fx = []
    for F_ in man.get('fx', []):
        if F_.get('layer') in planes and F_['type'] == 'anim_sprite':
            continue
        F_ = dict(F_)
        if 'file' in F_:
            F_['file'] = REL_RAILYARD + F_['file']
        fx.append(F_)
    man['fx'] = fx + fx_entries(meta, REL_RAILYARD + 'fx/')
    for a in man.get('actors', []):
        if a.get('scene', '').endswith('KarskLaundry.tscn'):
            a['props']['pegs'] = meta['near_bg']['pegs']
    hi = man.get('hotspot_info', {})
    for k, v in hotspot_marks(meta).items():
        if k in hi:
            hi[k].update(v)
    man.setdefault('notes', {})['skyline'] = ('TEST COPY (tests/visual/skyline): karsk_railyard manifest with the '
                                              'far_city / far_industry / mid / near_bg planes of '
                                              'assets/environments/karsk_skyline swapped in.')
    os.makedirs(SL.TEST_DIR, exist_ok=True)
    with open(os.path.join(SL.TEST_DIR, 'scene.json'), 'w', encoding='utf-8') as f:
        json.dump(man, f, indent=1, ensure_ascii=False)
    return sky


def palette_check():
    from PIL import Image
    bad = {}
    for fn in sorted(os.listdir(SL.OUT_DIR)):
        if not fn.endswith('.png') or fn.endswith('_n.png'):
            continue
        arr = np.asarray(Image.open(os.path.join(SL.OUT_DIR, fn)).convert('RGBA'))
        rep = SL.palette_report(arr)
        if rep:
            bad[fn] = rep
    return bad


def previews(tag='skyline'):
    import env_karsk_skyline_preview as PV
    PV.clear_cache()
    out = os.path.join(SL.SCRATCH, 'preview')
    os.makedirs(out, exist_ok=True)
    man = os.path.join(SL.TEST_DIR, 'scene.json')
    res = {}
    for cam in (0, 640, 1280):
        img, cover, names = PV.compose(man, cam, lit=True)
        PV.save(img, os.path.join(out, '%s_cam%04d_x2.png' % (tag, cam)), 2)
        res[cam] = round(PV.sun_visibility(cover, names), 2)
    return res


def build(preview=True):
    results = {}
    mid, meta_mid = make_mid(hist=False)
    mid_h, _ = make_mid(hist=True)
    results['mid'] = save_plane(mid, 'mid', hist_layer=mid_h)
    fi, meta_fi = F.make_far_industry()
    results['far_industry'] = save_plane(fi, 'far_industry')
    fc, meta_fc = F.make_far_city()
    results['far_city'] = save_plane(fc, 'far_city')
    nb, meta_nb = N.make_near_bg()
    results['near_bg'] = save_plane(nb, 'near_bg')
    meta = {'mid': meta_mid, 'far_industry': meta_fi, 'far_city': meta_fc, 'near_bg': meta_nb}
    sky = write_manifests(results, meta)
    bad = palette_check()
    sun = previews() if preview else None
    return results, meta, sky, bad, sun


if __name__ == '__main__':
    results, meta, sky, bad, sun = build(preview='--no-preview' not in sys.argv)
    for k, (C, info) in results.items():
        print('%-13s %4dx%-4d emission=%s' % (k, C.w, C.h, info['emission']))
    print('palette check:', 'OK (no off-palette pixels)' if not bad else bad)
    if sun:
        print('sun visible (fraction of the disc) at cam 0/640/1280:', sun)
