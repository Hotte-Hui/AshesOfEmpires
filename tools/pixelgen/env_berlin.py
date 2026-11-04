"""env_berlin -- generator for the env_berlin area of ASHES OF EMPIRES: THE LAST WINTER.

Run:  py -3 -P tools/pixelgen/env_berlin.py            (deterministic, no network)

Produces
* assets/environments/berlin_archive/   scene M1 'Berliner Bauarchiv' layers, props, scene.json,
                                        previews in _preview/ (git/Godot-ignored)
* assets/ui/documents/berlin_*.png/json plan documents for the overlay puzzle + Emil's slip
* assets/ui/documents/x1_*.png          640x360 cinematic stills for the A1->M1 / X1 transitions
* documentation/asset_manifest_parts/env_berlin.md   provenance of every produced file
Optional flags: --scene-only, --docs-only, --no-preview
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import env_berlin_kit as kit          # noqa: E402
import env_berlin_layout as L         # noqa: E402
import pg                             # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'berlin_archive')
PREV_DIR = os.path.join(ENV_DIR, '_preview')
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')
MANIFEST = os.path.join(ROOT, 'documentation', 'asset_manifest_parts', 'env_berlin.md')

PRODUCED: list[tuple[str, str, str]] = []   # (relative path, generator, description)

LIGHT_COLORS = {'warm': '#F0C487', 'cold': '#A7BCCB', 'green': '#8FC79A', 'white': '#E3ECEA'}
# dynamic (Godot) light energies are lower than the baked ones: the art already carries the bake.
DYN = {
    'window_1': (0.55, 150, 40, 0.0), 'window_2': (0.55, 150, 40, 0.0), 'window_3': (0.55, 150, 40, 0.0),
    'corridor_glass': (0.25, 56, 8, 0.03), 'lamp_konrad': (0.95, 112, 24, 0.02),
    'lamp_typist': (0.55, 84, 18, 0.03), 'archive_pendant': (0.85, 118, 28, 0.02),
    'archive_sconce': (0.5, 76, 16, 0.05), 'light_table': (0.7, 92, 6, 0.0), 'lamp_emil': (0.8, 90, 10, 0.02),
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


# =========================================================================== scene
def build_scene(preview=True):
    import env_berlin_room as ER
    import env_berlin_props as EP
    import env_berlin_ext as EX
    import env_berlin_fg as EF
    import env_berlin_fx as EFX
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
    print('  scene built in %.1fs' % (time.time() - t0))

    # ---- save
    os.makedirs(ENV_DIR, exist_ok=True)
    kit.ensure_gdignore(PREV_DIR)
    layers = []
    for name, lay in (('ext_sky', ext['ext_sky']), ('ext_far', ext['ext_far']), ('ext_near', ext['ext_near'])):
        info = save_layer(lay, os.path.join(ENV_DIR, name), normal=False, gen='env_berlin_ext.py',
                          desc={'ext_sky': 'Berlin winter dusk sky (seen through windows)',
                                'ext_far': 'far city, smoke and the fictional Great Hall dome (muted, hazy)',
                                'ext_near': 'Gruenderzeit tenements across the street, tram wires'}[name])
        layers.append({'name': name, 'file': name + '.png', 'pos': [0, 0],
                       'parallax': [L.PARALLAX[name], L.PARALLAX[name]],
                       'z': {'ext_sky': -100, 'ext_far': -95, 'ext_near': -90}[name],
                       'normal': False, 'emission': info['emission'], 'lit': False, 'repeat_x': 0})
    info = save_layer(room.lay, os.path.join(ENV_DIR, 'room'), gen='env_berlin_room.py',
                      desc='archive interior: office, archive hall, light-table room, issue counter')
    layers.append({'name': 'room', 'file': 'room.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -50,
                   'normal': True, 'emission': info['emission'], 'lit': True})
    info = save_layer(shafts, os.path.join(ENV_DIR, 'shafts'), normal=False, gen='env_berlin.py',
                      desc='volumetric daylight-shaft veil (soft alpha, additive blend hint)')
    layers.append({'name': 'shafts', 'file': 'shafts.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': 10,
                   'normal': False, 'emission': False, 'lit': False, 'blend': 'add',
                   'note': 'soft alpha veil (max ~18%); additive preferred, plain alpha acceptable'})
    info = save_layer(fg, os.path.join(ENV_DIR, 'fg_frame'), normal=False, gen='env_berlin_fg.py',
                      desc='foreground framing silhouettes (columns, rubber plant, desk, chair)')
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
    glass_rects = [[a, L.WIN_Y[0], b - a, L.WIN_Y[1] - L.WIN_Y[0]] for (a, b) in L.WINDOWS]
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
        # ---- extension data (not required by the level contract; safe to ignore)
        'npcs': {'emil': {'pos': list(L.EMIL_POS), 'facing': 'left',
                          'note': 'stands behind the counter prop (counter base_y 292 > feet y 284)'}},
        'interaction': {k: {'approach': list(L.APPROACH[k][0]), 'facing': L.APPROACH[k][1],
                            'focus': list(L.FOCUS[k])} for k in L.HOTSPOTS},
        'windows': {'glass_rects': glass_rects, 'note': 'room.png is transparent here; ext_* layers show through'},
        'meta': {'mode': 'side', 'feet_y': L.WALK_Y, 'generator': 'tools/pixelgen/env_berlin.py',
                 'date': kit.DATE, 'shafts_blend': 'shafts.png is meant for additive/screen blending; '
                                                    'with plain alpha it reads as dithered motes'},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    with open(sj, 'w', encoding='utf-8') as f:
        json.dump(scene, f, indent=1, ensure_ascii=False)
    record(sj, 'env_berlin.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1)')

    # ---- checks
    issues = EF.check_clearance(fg)
    if issues:
        print('  WARNING fg covers hotspots:', issues)
    allowed = {h.upper() for h in kit.archive_palette_hex()}
    for nm, lay in [('room', room.lay)] + [(p.name, p.lay) for p in props] + [('fg', fg)]:
        n, bad = kit.palette_report(lay.c, allowed)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    allowed_b = {h.upper() for h in kit.berlin_palette_hex()} | {h.upper() for h in ['#2A2130', '#2C4440',
                                                                                     '#454E58', '#3E5D55',
                                                                                     '#5F6973']}
    for nm, lay in ext.items():
        n, bad = kit.palette_report(lay.c, allowed_b)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    if preview:
        previews(scene)
    return scene


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
    for (x0, x1) in L.WINDOWS:
        a[L.WIN_Y[0] - 8:L.WIN_Y[1] + 2, x0 - 6:x1 + 6] *= 0.0
    alpha = np.clip(np.round(a * 46), 0, 255).astype(np.uint8)
    col = pg.hx('#A7BCCB')
    lay.c[..., 0], lay.c[..., 1], lay.c[..., 2] = col[0], col[1], col[2]
    lay.c[..., 3] = alpha
    lay.c[alpha == 0] = 0
    return lay


# =========================================================================== previews
def hexc(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32) / 255.0


def figure(kind='konrad'):
    """Preview-only scale figure (46 px).  NOT a shipped asset -- characters are another area."""
    lay = pg.Layer(20, 48)
    dark = pg.hx('#1A2433') if kind == 'konrad' else pg.hx('#3B3A36')
    mid = pg.hx('#2B3C50') if kind == 'konrad' else pg.hx('#55524A')
    skin = pg.hx('#B57B59')
    if kind == 'konrad':
        lay.rect(6, 0, 9, 2, dark)          # fedora brim
        lay.rect(8, -2 + 2, 5, 1, dark)
        lay.rect(8, 2, 5, 5, skin)
        lay.rect(5, 8, 11, 30, mid)         # long coat
        lay.rect(5, 8, 2, 30, dark)
        lay.rect(9, 8, 3, 3, pg.hx('#7A2A26'))   # scarf
        lay.rect(6, 38, 3, 9, dark); lay.rect(12, 38, 3, 9, dark)
    else:
        lay.rect(8, 2, 5, 6, skin)
        lay.rect(8, 1, 5, 2, pg.hx('#B0AA93'))
        lay.px(8, 4, pg.hx('#1A1C2A')); lay.px(12, 4, pg.hx('#1A1C2A'))
        lay.rect(6, 9, 10, 26, mid)
        lay.rect(6, 9, 10, 2, dark)
        lay.rect(7, 35, 3, 12, dark); lay.rect(12, 35, 3, 12, dark)
    return lay.image()


def compose(scene, cx, lit=False, figures=True):
    out = np.zeros((L.VIEW_H, L.VIEW_W, 3), np.float32)
    mod = hexc(scene['canvas_modulate'])
    items = []
    for ly in scene['layers']:
        items.append((ly['z'], 'layer', ly))
    for pr in scene['props']:
        items.append((0, 'prop', pr))
    for fx in scene.get('fx', []):
        if fx.get('type') == 'anim_sprite':
            items.append((fx.get('z', -20), 'fx', fx))
    items.sort(key=lambda t: (t[0], t[2].get('base_y', 0) if t[1] == 'prop' else 0))
    # figures for scale (preview only)
    figs = []
    if figures:
        figs.append(('konrad', L.SPAWNS['SP_M1_Office'] if cx < 300 else ((cx + 320), L.WALK_Y)))
        figs.append(('emil', L.EMIL_POS))

    def blit(img_path, x, y, is_lit, normal_path=None, emis_path=None, additive=False):
        im = np.asarray(Image.open(img_path).convert('RGBA'), np.float32) / 255.0
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

    fig_done = False
    for z, kind, d in items:
        if kind == 'layer':
            if z > 0 and not fig_done:
                fig_done = True
                draw_figs(out, figs, cx)
            px_ = d['parallax'][0]
            x = int(round(d['pos'][0] - cx * px_))
            base = os.path.join(ENV_DIR, d['file'][:-4])
            blit(base + '.png', x, d['pos'][1], d.get('lit', False), base + '_n.png', base + '_e.png',
                 additive=(d.get('blend') == 'add'))
        elif kind == 'fx':
            if z > 0 and not fig_done:
                fig_done = True
                draw_figs(out, figs, cx)
            strip = Image.open(os.path.join(ENV_DIR, d['file'])).convert('RGBA')
            fw = strip.width // int(d.get('frames', 1))
            tmp = os.path.join(PREV_DIR, '_fx_frame0.png')
            strip.crop((0, 0, fw, strip.height)).save(tmp)
            pxp = d['parallax'][0] if isinstance(d['parallax'], list) else d['parallax']
            blit(tmp, int(round(d['pos'][0] - cx * pxp)), d['pos'][1], False)
        else:
            base = os.path.join(ENV_DIR, d['file'][:-4])
            blit(base + '.png', d['pos'][0] - cx, d['pos'][1], True, base + '_n.png', base + '_e.png')
            if not fig_done and figs:
                # draw figures whose feet are above this prop's base (y-sort)
                pass
    if not fig_done:
        draw_figs(out, figs, cx)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGB')


def draw_figs(out, figs, cx):
    for kind, (fx, fy) in figs:
        im = np.asarray(figure(kind).convert('RGBA'), np.float32) / 255.0
        x = int(fx - cx - 10)
        y = int(fy - 47)
        h, w = im.shape[:2]
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(L.VIEW_W, x + w), min(L.VIEW_H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            continue
        sub = im[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4] > 0.5
        if kind == 'emil':
            # behind the counter: only draw rows above the counter top (prop starts at y 261)
            a = a & (np.arange(Y0, Y1)[:, None, None] < 267)
        out[Y0:Y1, X0:X1] = np.where(a, sub[..., :3], out[Y0:Y1, X0:X1])


def previews(scene):
    kit.ensure_gdignore(PREV_DIR)
    for cx in (0, 480, 960):
        for lit in (False, True):
            im = compose(scene, cx, lit=lit)
            fn = os.path.join(PREV_DIR, 'cam%04d_%s.png' % (cx, 'lit' if lit else 'albedo'))
            im.save(fn)
            # 3x crops of the interesting third
            for i, (x0, y0) in enumerate(((0, 60), (213, 120), (427, 150))):
                pg.upscale(im.crop((x0, y0, x0 + 213, y0 + 120)), 3).save(
                    fn[:-4] + '_crop%d_x3.png' % i)
    # full world overview (albedo, no parallax offsets beyond cam 0 logic)
    world = Image.new('RGB', (L.WORLD_W, L.WORLD_H))
    for cx in range(0, L.WORLD_W - L.VIEW_W + 1, 320):
        world.paste(compose(scene, cx, lit=False, figures=False), (cx, 0))
    world.paste(compose(scene, L.WORLD_W - L.VIEW_W, lit=False, figures=False), (L.WORLD_W - L.VIEW_W, 0))
    world.save(os.path.join(PREV_DIR, 'world_overview.png'))


# =========================================================================== manifest
def write_manifest():
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    lines = [
        '# Asset manifest part -- env_berlin (M1 Berliner Bauarchiv, plan documents, X1 stills)',
        '',
        'All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`',
        '(`env_berlin.py` drives `env_berlin_room.py`, `env_berlin_ext.py`, `env_berlin_props.py`,',
        '`env_berlin_fg.py`, `env_berlin_docs.py`, `env_berlin_stills.py`, helpers `env_berlin_kit.py`,',
        '`env_berlin_layout.py` and the shared `pg.py`).  No pixels were copied, traced or sampled from the',
        'reference images in `documentation/references/` (style study only).  No third-party assets, fonts',
        'or textures are embedded; the tiny bitmap fonts are hand-defined in `env_berlin_kit.py`.',
        '',
        '* Licence / rights: project-owned original artwork (generated for this project), freely',
        '  redistributable with the game.  Provenance: deterministic generator, re-run with',
        '  `py -3 -P tools/pixelgen/env_berlin.py`.',
        '* Date: %s.  Palettes: `archive` (+ local `green`, `graphite` ramps), `berlin`, `sepia`, `karsk`.' % kit.DATE,
        '* Insignia policy: only the fictional **Reichssiegel** (white pillar in a black disc) appears; no',
        '  swastika, eagle or SS rune anywhere.  The Great Hall is fictional and shown muted, not heroic.',
        '* Locale `data/locale/de_env_berlin.json` is hand-written original German text (Konrad\'s voice).',
        '',
        '| File | Generator | Content |',
        '|---|---|---|',
    ]
    for path, gen, desc in sorted(PRODUCED):
        lines.append('| `%s` | `tools/pixelgen/%s` | %s |' % (path, gen, desc.replace('|', '/')))
    lines += ['| `data/locale/de_env_berlin.json` | hand-written | observation prompts/texts (obs_window, '
              'obs_notice, obs_photo) |', '']
    with open(MANIFEST, 'w', encoding='utf-8') as f:
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
        import env_berlin_stills as ES
        print('[env_berlin] documents ...')
        for path, desc in ED.build_all(DOC_DIR, PREV_DIR if preview else None):
            record(path, 'env_berlin_docs.py', desc)
        print('[env_berlin] cinematic stills ...')
        for path, desc in ES.build_all(DOC_DIR, PREV_DIR if preview else None):
            record(path, 'env_berlin_stills.py', desc)
    if not ({"--scene-only", "--docs-only"} & set(argv)):
        write_manifest()
    print('[env_berlin] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
