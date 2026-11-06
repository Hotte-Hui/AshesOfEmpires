"""walkers_r8 -- anonymous colour variants of existing character sheets for the ambient walkers (rounds 8 + 9).

    py -3 -P tools/pixelgen/walkers_r8.py                    # writes every variant sheet and rig
    py -3 -P tools/pixelgen/walkers_r8.py --preview=DIR      # + contact sheets DIR/walkers_r8_contact.png, _rigs.png
    py -3 -P tools/pixelgen/walkers_r8.py --check            # only verifies the pipeline reproduces the sources

Each variant re-renders one EXISTING character (chargen_cast / chargen_cast_new / chargen_cast_c3) through the
existing body pipeline (chargen_body.render, same rows and frames as the shipped sheet.json) with a few entries
of its material table swapped (coat, hair, hat, scarf ...).  The silhouette is identical pixel for pixel (checked),
so the runtime reuses the character's own sheet_n.png and sheet.json; only the diffuse changes.  A walker
therefore never reads as the twin of a speaking character (Frau Brunner, Nils Ekdahl, the archive clerk, the
Berlin family, the archive porter).  No insignia on any variant.  Deterministic: no randomness, no network.

Outputs: assets/environments/<env>/walkers/<name>.png  (runtime: scripts/actors/ambient_walker.gd, data in
assets/environments/<env>/walkers.json; provenance: documentation/asset_manifest_parts/feel_r8.md).

Round 9 (feel pass 2) -- RIGS: every variant also gets its own complete sheet <name>_rig.png + <name>_rig_n.png +
<name>_rig.json: the source's rows (same order, same frames, same silhouette -- checked) plus the appended rows
walk_front / idle_back / walk_back from the same body pipeline, so a walker's path may run diagonally on oblique
floors (it walks toward / away from the camera).  The quay of Chapter 3 (veltrava_quay) adds firemen, onlookers,
a commission clerk with rescued files and a city policeman -- all new variants only exist as rigs.
Provenance: documentation/asset_manifest_parts/feel_r9.md.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import characters as CH                   # noqa: E402  existing runner (ANIMS, CAST)
import characters_c3 as CC3               # noqa: E402  installs the Chapter-3 cast into CH's tables
from chargen_body import CELL_H, CELL_W, render   # noqa: E402
from chargen_cast import SKIN             # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CHAR_DIR = os.path.join(ROOT, 'assets', 'characters')
ENV_DIR = os.path.join(ROOT, 'assets', 'environments')

DARK_HAIR = ['#140E0C', '#2A1C16', '#3E2A20', '#563C2C', '#6E503A', '#88664A']
BLUE_BLACK = ['#0C0B10', '#18161E', '#26222C', '#36303C', '#48404E', '#5C5262']
FAIR_HAIR = ['#3A2E1C', '#5E4C2E', '#82693E', '#A08A5A', '#BCA674', '#D6C494']
GREY_HAIR = ['#2E2E30', '#55575A', '#7C7E80', '#A2A3A2', '#C4C4BE', '#E0DFD8']

# (env, file name, source character, material overrides).  A plain hex override keeps the original entry's
# keyword options (knit / tweed / glossy); a tuple replaces them.
VARIANTS = [
    # Palais: a delegation secretary, a second press man, an elderly delegate -- none of them speaks
    ('veltrava_hall', 'secretary', 'typist', {
        'coat': '#3E5468', 'skirt': '#2C2E36', 'hair': BLUE_BLACK, 'button': '#2A2E3A'}),
    ('veltrava_hall', 'pressman', 'journalist', {
        'coat': '#4C5258', 'scarf': '#6A2E2A', 'hair': DARK_HAIR, 'trouser': '#2E3036'}),
    ('veltrava_hall', 'delegate', 'clerk', {
        'coat': '#3C302C', 'sleeve': '#3C302C', 'protector': '#3C302C', 'trouser': '#2E2624',
        'hair': GREY_HAIR, 'tie': '#2A3A52'}),
    # Station: two travellers with their luggage, a Veltrava station porter
    ('veltrava_station', 'traveller_woman', 'berlin_mother', {
        'coat': '#3E5246', 'hat': '#4A3A2E', 'band': '#2A2A30', 'hair': '#2A2224', 'scarf': '#6A7A8A',
        'case': '#4E3E34'}),
    ('veltrava_station', 'traveller_man', 'berlin_father', {
        'coat': '#3E4650', 'hat': '#3A3A40', 'scarf': '#7A5A3A', 'hair': '#5A5652', 'crate': '#7A6248'}),
    ('veltrava_station', 'porter', 'porter', {
        'coat': '#4A3C30', 'hat': '#4A3C30', 'collar': '#3A2E26', 'trouser': '#2E2824', 'hair': DARK_HAIR,
        'skin': SKIN['ruddy']}),
    # Berlin archive reading room: a reader with his files, a student
    ('berlin_archive', 'reader', 'clerk', {
        'coat': '#5A4A3C', 'sleeve': '#5A4A3C', 'protector': '#5A4A3C', 'trouser': '#3A3430',
        'hair': GREY_HAIR, 'tie': '#2E3A2C'}),
    ('berlin_archive', 'student', 'typist', {
        'coat': '#6A2E36', 'skirt': '#2A2E3A', 'hair': FAIR_HAIR, 'button': '#3A1E22'}),
    # Quay (round 9): the night of the registry fire -- a fireman of the Veltrava brigade (black leather helmet with
    # a brass comb, dark tunic, leather gloves), a man from the old town woken by the fire (coat over pyjama
    # trousers), a commission clerk carrying rescued folders, an old woman in a headscarf, a city policeman
    # (green-grey, not the commission's blue).  None of the sources stands or speaks on the quay.
    ('veltrava_quay', 'fireman', 'worker_b', {
        'coat': '#2A3346', 'trouser': '#20242E', 'boot': ('#141416', {'glossy': True}), 'galosh': '#101012',
        'hat': ('#4A4C50', {'glossy': True}), 'band': '#B49A58', 'mitten': '#3E3222', 'belt': '#4A3A26',
        'metal': '#C4A458', 'button': '#A88E4C', 'patch': '#323A4C', 'hair': DARK_HAIR}),
    ('veltrava_quay', 'resident', 'worker_a', {
        'coat': '#54443A', 'trouser': '#6C7486', 'hat': '#3A3A40', 'band': '#2A2A2E', 'hair': GREY_HAIR,
        'boot': ('#2E2622', {'texture': 'felt'}), 'mitten': '#4A3E32', 'patch': '#4A3C32', 'button': '#2A221E'}),
    ('veltrava_quay', 'clerk_files', 'clerk', {
        'coat': '#2C3038', 'sleeve': '#2C3038', 'protector': '#2C3038', 'trouser': '#24262C', 'hair': GREY_HAIR,
        'tie': '#5A2A26', 'hat': '#1E1E22', 'button': '#16161A'}),
    ('veltrava_quay', 'old_woman', 'babushka', {
        'coat': '#2E3A44', 'skirt': '#3A3036', 'hat': '#6A3A34', 'band': '#C2B49A', 'cloth': '#5A6670',
        'fur': ('#3E3632', {'texture': 'fur'}), 'hair': GREY_HAIR}),
    ('veltrava_quay', 'policeman', 'conductor', {
        'coat': ('#33403A', {'bias': 0.06}), 'trouser': '#262C2A', 'hat': '#2E3A34', 'bag': ('#18181A', {'glossy': True}),
        'strap': '#18181A', 'hair': DARK_HAIR,
        'brass': ['#26282A', '#4A4E52', '#767C82', '#A4AAB0', '#C8CED2', '#E6EAEC'],
        'button': ['#26282A', '#4A4E52', '#767C82', '#A4AAB0', '#C8CED2', '#E6EAEC']}),
]
RIG_ROWS = ['walk_front', 'idle_back', 'walk_back']   # appended after the source's rows (row indices never move)
LEGACY_ENVS = ('veltrava_hall', 'veltrava_station', 'berlin_archive')   # round 8: also the same-size diffuse variant


def _patched_spec(src: str, overrides: dict):
    """Calls the cast function of `src` with its material table entries replaced (same keys, same order ->
    identical material indices, so every bitmap / hook resolves exactly as in the shipped sheet)."""
    fn = CH.CAST[src]
    mod = sys.modules[fn.__module__]
    orig = mod.materials

    def patched(scene, table):
        t = dict(table)
        for k, v in overrides.items():
            if k not in t:
                raise KeyError(f'{src}: no material {k!r}')
            if isinstance(v, str) and isinstance(t[k], tuple):
                v = (v, t[k][1])
            t[k] = v
        return orig(scene, t)

    mod.materials = patched
    try:
        return fn()
    finally:
        mod.materials = orig


FACE_MATS = ('skin', 'eye', 'glass')


def back_head(bm):
    """The back of a head from its front bitmap (NPC casts only draw side and front heads): down to the nose row
    the face turns into hair (tone 2, darker at the edges) -- or into the headscarf / hat when the head has no hair
    of its own --; below it (mouth, chin) the nape in shadow.  Same size and anchor, so hats sit unchanged."""
    tone = {k: (v[0], v[1]) for k, v in bm.legend.items()}
    mat = {k: v[0] for k, v in tone.items()}

    def char_for(m, t):
        for k, (mm, tt) in tone.items():
            if mm == m and tt == t and len(bm.legend[k]) == 2:
                return k
        return None

    rows = [list(r.ljust(bm.w, '.')) for r in bm.rows]
    used = {c for r in rows for c in r}
    has_hair = any(mat.get(c) == 'hair' for c in used)
    has_hat = any(mat.get(c) == 'hat' for c in used)
    if has_hair:
        inner, outer = char_for('hair', 2), char_for('hair', 1)
    elif has_hat:
        inner, outer = char_for('hat', 2), char_for('hat', 1)
    else:
        return bm
    nape_in, nape_out = char_for('skin', 2), char_for('skin', 1)
    if None in (inner, outer, nape_in, nape_out):
        return bm
    eye_rows = [y for y, r in enumerate(rows) if any(mat.get(c) == 'eye' for c in r)]
    nose_rows = [y for y, r in enumerate(rows) if any(c in r for c in 'n')]
    split = nose_rows[-1] if nose_rows else (eye_rows[-1] + 1 if eye_rows else len(rows) // 2)
    subs = {}
    for y, r in enumerate(rows):
        face = [x for x, c in enumerate(r) if mat.get(c) in FACE_MATS]
        if not face:
            continue
        a, b = (inner, outer) if y <= split else (nape_in, nape_out)
        for x in face:
            subs[(x, y)] = b if x in (face[0], face[-1]) and len(face) > 2 else a
    return bm.variant(subs)


def with_back_heads(spec):
    """Installs derived back heads when the cast has none (protagonists bring their own)."""
    if 'back' not in spec.heads:
        h = spec.heads['front']
        spec.heads['back'] = {k: back_head(v) for k, v in h.items()} if isinstance(h, dict) else back_head(h)
    return spec


def render_sheet(spec, meta: dict) -> np.ndarray:
    """Renders the rows of an existing sheet.json (same order, same frame counts) for `spec`."""
    rows = sorted(meta['anims'].items(), key=lambda kv: kv[1]['row'])
    ncols = max(a['frames'] for _, a in rows)
    sheet = np.zeros((CELL_H * len(rows), CELL_W * ncols, 4), np.uint8)
    for name, a in rows:
        view, fn, _fps, _loop = CH.ANIMS[name]
        frames = fn(spec.style)
        if len(frames) != a['frames']:
            raise ValueError(f'{spec.id}/{name}: {len(frames)} frames, sheet has {a["frames"]}')
        r = a['row']
        for c, P in enumerate(frames):
            rgba, _nm, _fr, _J = render(spec, view, P)
            sheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = rgba
    return sheet


def _source(src: str):
    d = os.path.join(CHAR_DIR, src)
    meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
    sheet = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA'))
    return meta, sheet


def build(env: str, name: str, src: str, overrides: dict, write=True) -> np.ndarray:
    meta, ref = _source(src)
    out = render_sheet(_patched_spec(src, overrides), meta)
    if out.shape != ref.shape:
        raise ValueError(f'{name}: size {out.shape} != {ref.shape} of {src}')
    if not np.array_equal(out[..., 3] > 0, ref[..., 3] > 0):
        raise ValueError(f'{name}: silhouette differs from {src} (normal map would not fit)')
    if write:
        d = os.path.join(ENV_DIR, env, 'walkers')
        os.makedirs(d, exist_ok=True)
        Image.fromarray(out, 'RGBA').save(os.path.join(d, name + '.png'))
    return out


def build_rig(env: str, name: str, src: str, overrides: dict, write=True):
    """Round 9: the variant's own complete sheet -- the source's rows (same order / frames / timing / variants,
    silhouette checked against the source) plus RIG_ROWS, with its own normal map.  Returns (sheet, nsheet, meta)."""
    meta, ref = _source(src)
    spec = with_back_heads(_patched_spec(src, overrides))
    rows = sorted(meta['anims'].items(), key=lambda kv: kv[1]['row'])
    names = [n for n, _ in rows] + [n for n in RIG_ROWS if n not in meta['anims']]
    built = []
    for name_ in names:
        view, fn, fps, loop = CH.ANIMS[name_]
        built.append((name_, view, fn(spec.style), fps, loop))
    ncols = max(len(f) for _, _, f, _, _ in built)
    sheet = np.zeros((CELL_H * len(built), CELL_W * ncols, 4), np.uint8)
    nsheet = np.zeros_like(sheet)
    out_meta = {'id': name, 'source': src, 'cell': [CELL_W, CELL_H], 'origin': list(meta.get('origin', CH.ORIGIN)),
                'facing': meta.get('facing', 'right'), 'anims': {}}
    for r, (name_, view, frames, fps, loop) in enumerate(built):
        for c, P in enumerate(frames):
            rgba, nm, _fr, _J = render(spec, view, P)
            sheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = rgba
            nsheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = nm
        if name_ in meta['anims']:
            a = dict(meta['anims'][name_])
            if a['row'] != r or a['frames'] != len(frames):
                raise ValueError(f'{name}: row {name_} moved or changed length')
        else:
            a = {'row': r, 'frames': len(frames), 'fps': fps, 'loop': loop}
        out_meta['anims'][name_] = a
    speeds = dict(meta.get('ground_speed', {}))
    for name_ in RIG_ROWS:
        gs = CH.ground_speed(spec, name_)
        if gs and name_ not in speeds:
            speeds[name_] = gs
    out_meta['ground_speed'] = speeds
    h0, w0 = ref.shape[:2]
    if not np.array_equal(sheet[:h0, :w0, 3] > 0, ref[..., 3] > 0) or (sheet[:h0, w0:, 3] > 0).any():
        raise ValueError(f'{name}: the source rows of the rig do not keep the silhouette of {src}')
    if write:
        d = os.path.join(ENV_DIR, env, 'walkers')
        os.makedirs(d, exist_ok=True)
        Image.fromarray(sheet, 'RGBA').save(os.path.join(d, name + '_rig.png'))
        Image.fromarray(nsheet, 'RGBA').save(os.path.join(d, name + '_rig_n.png'))
        with open(os.path.join(d, name + '_rig.json'), 'w', encoding='utf-8', newline=chr(10)) as f:
            json.dump(out_meta, f, indent=1)
    return sheet, nsheet, out_meta


def check_sources() -> list:
    """The unmodified pipeline must reproduce every source sheet (else the variants drift from the cast)."""
    bad = []
    for src in sorted({v[2] for v in VARIANTS}):
        meta, ref = _source(src)
        out = render_sheet(CH.CAST[src](), meta)
        if not np.array_equal(out, ref):
            bad.append(src)
    return bad


def preview(sheets: list, path: str):
    """idle_side + walk frame 2 of every source and its variant (4x) on a mid-grey."""
    k = 4
    img = Image.new('RGBA', (len(sheets) * CELL_W * 2 * k, CELL_H * 2 * k), (96, 104, 108, 255))
    for i, (name, src, out) in enumerate(sheets):
        meta, ref = _source(src)
        for j, sh in enumerate((ref, out)):
            for rr, (anim, f) in enumerate((('idle_side', 0), ('walk_side', 2))):
                r = meta['anims'][anim]['row']
                cell = Image.fromarray(sh[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W], 'RGBA')
                cell = cell.resize((CELL_W * k, CELL_H * k), Image.NEAREST)
                img.alpha_composite(cell, ((i * 2 + j) * CELL_W * k, rr * CELL_H * k))
    img.save(path)


def preview_rigs(rigs: list, path: str):
    """Per rig (one column, 3x): idle_side, walk_side 2, walk_front 2, idle_back, walk_back 2 -- <= 1280 px wide."""
    k = 3
    cells = (('idle_side', 0), ('walk_side', 2), ('walk_front', 2), ('idle_back', 0), ('walk_back', 2))
    img = Image.new('RGBA', (len(rigs) * CELL_W * k, len(cells) * CELL_H * k), (96, 104, 108, 255))
    for i, (name, sheet, meta) in enumerate(rigs):
        for j, (anim, f) in enumerate(cells):
            r = meta['anims'][anim]['row']
            cell = Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W], 'RGBA')
            img.alpha_composite(cell.resize((CELL_W * k, CELL_H * k), Image.NEAREST), (i * CELL_W * k, j * CELL_H * k))
    img.save(path)


def main(argv):
    CC3.install()
    if '--check' in argv:
        bad = check_sources()
        print('walkers_r8: sources reproduce' if not bad else f'walkers_r8: drift in {bad}')
        return 1 if bad else 0
    prev = next((a.split('=', 1)[1] for a in argv if a.startswith('--preview=')), '')
    built = []
    rigs = []
    for env, name, src, ov in VARIANTS:
        if env in LEGACY_ENVS:
            built.append((name, src, build(env, name, src, ov)))
            print(f'walkers_r8: {env}/walkers/{name}.png  <- {src}')
        sheet, _ns, meta = build_rig(env, name, src, ov)
        rigs.append((name, sheet, meta))
        print(f'walkers_r8: {env}/walkers/{name}_rig.png (+_n, .json, {len(meta["anims"])} rows)  <- {src}')
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview(built, os.path.join(prev, 'walkers_r8_contact.png'))
        preview_rigs(rigs, os.path.join(prev, 'walkers_r8_rigs.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
