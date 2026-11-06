"""walkers_r8 -- anonymous colour variants of existing character sheets for the ambient walkers (round 8).

    py -3 -P tools/pixelgen/walkers_r8.py                    # writes every variant sheet
    py -3 -P tools/pixelgen/walkers_r8.py --preview=DIR      # + a contact sheet DIR/walkers_r8_contact.png
    py -3 -P tools/pixelgen/walkers_r8.py --check            # only verifies the pipeline reproduces the sources

Each variant re-renders one EXISTING character (chargen_cast / chargen_cast_new / chargen_cast_c3) through the
existing body pipeline (chargen_body.render, same rows and frames as the shipped sheet.json) with a few entries
of its material table swapped (coat, hair, hat, scarf ...).  The silhouette is identical pixel for pixel (checked),
so the runtime reuses the character's own sheet_n.png and sheet.json; only the diffuse changes.  A walker
therefore never reads as the twin of a speaking character (Frau Brunner, Nils Ekdahl, the archive clerk, the
Berlin family, the archive porter).  No insignia on any variant.  Deterministic: no randomness, no network.

Outputs: assets/environments/<env>/walkers/<name>.png  (runtime: scripts/actors/ambient_walker.gd, data in
assets/environments/<env>/walkers.json; provenance: documentation/asset_manifest_parts/feel_r8.md).
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
]


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


def main(argv):
    CC3.install()
    if '--check' in argv:
        bad = check_sources()
        print('walkers_r8: sources reproduce' if not bad else f'walkers_r8: drift in {bad}')
        return 1 if bad else 0
    prev = next((a.split('=', 1)[1] for a in argv if a.startswith('--preview=')), '')
    built = []
    for env, name, src, ov in VARIANTS:
        built.append((name, src, build(env, name, src, ov)))
        print(f'walkers_r8: {env}/walkers/{name}.png  <- {src}')
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview(built, os.path.join(prev, 'walkers_r8_contact.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
