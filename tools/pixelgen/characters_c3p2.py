"""characters_c3p2.py -- builds the Chapter-3 part-2 looks through the EXISTING character pipeline.

    py -3 -P tools/pixelgen/characters_c3p2.py                 (all three looks: sheets, previews, checks)
    py -3 -P tools/pixelgen/characters_c3p2.py konrad_soot     (selected ids)
    py -3 -P tools/pixelgen/characters_c3p2.py --portraits     (additionally the living portraits through
                                                               chargen_portrait2; specs: chargen_portrait_c3p2)
    py -3 -P tools/pixelgen/characters_c3p2.py --check         (validate only)
    py -3 -P tools/pixelgen/characters_c3p2.py --out=DIR       (review run: write everything below DIR)

Imports characters.py (ANIMS, ROWS, build_sheet, previews) and characters_check.py and extends their tables
IN MEMORY with the looks of chargen_cast_c3p2 (nothing else is patched; only the new ids are built).
Outputs (TECHNICAL_ARCHITECTURE section 4 + documentation/asset_manifest_parts/c3p2_cast_audio.md):
    assets/characters/<id>/sheet.png, sheet_n.png, sheet.json  (+ portrait.png, portrait_anim.png, portrait.json)
    assets/characters/_preview/c3p2_*         (review images; the folder is .gdignore'd and git-ignored)
Re-run after any change of the base characters (alexei, konrad, typist): the looks derive from them.
Deterministic: no randomness, no network.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import characters as CH                   # noqa: E402  existing runner (ANIMS, ROWS, build_sheet, previews)
import characters_check as CHK            # noqa: E402  existing validator
import chargen_cast_c3 as C3              # noqa: E402
import chargen_cast_c3p2 as P2            # noqa: E402
from chargen_body import CELL_H, CELL_W   # noqa: E402

IDS = list(P2.CAST_C3P2)
_GS = CH.ground_speed


def _ground_speed(spec, anim):
    """carry_side walks exactly like walk_side (same feet): same planted-foot speed."""
    return _GS(spec, 'walk_side' if anim == 'carry_side' else anim)


def install():
    """Extend the existing pipeline's tables in memory (idempotent).  The Chapter-3 runner's own in-memory patches
    (characters_c3.install) come first, so the looks inherit every fix of their base characters."""
    import characters_c3 as RC3
    if hasattr(RC3, 'install'):
        RC3.install()
    CH.CAST.update(C3.CAST_C3)
    CH.ROWS.update(C3.ROWS_C3)
    CH.CAST.update(P2.CAST_C3P2)
    CH.ANIMS.update(P2.ANIMS_C3P2)
    CH.ROWS.update(P2.rows_c3p2(CH.ROWS))
    CH.ground_speed = _ground_speed
    CHK.EXPECT_H.update(P2.EXPECT_H_C3P2)
    for cid in ('alexei_soot', 'konrad_soot'):
        CHK.REQUIRED[cid] = list(CHK.CONTRACT_ROWS)
    CHK.NPC_MIN['typist_night'] = list(C3.ROWS_C3['typist'])


def set_out(root):
    CH.OUT = os.path.join(root, 'assets', 'characters') if root else CH.OUT
    CH.PREV = os.path.join(CH.OUT, '_preview')
    CHK.OUT = CH.OUT


def _base_dir(cid):
    d = os.path.join(CH.OUT, cid)
    if not os.path.exists(os.path.join(d, 'sheet.json')):
        d = os.path.abspath(os.path.join(HERE, '..', '..', 'assets', 'characters', cid))
    return d


def _load(cid):
    d = _base_dir(cid)
    meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
    return np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA')), meta


def _row(sheet, meta, anim):
    r = meta['anims'][anim]['row']
    return sheet[r * CELL_H:(r + 1) * CELL_H]


# ----------------------------------------------------------------------------------- previews
BGS = [(36, 30, 34, 255), (28, 36, 52, 255), (78, 52, 38, 255)]       # smoke dark, quay night, fire glow


def preview(ids):
    """Base and look side by side, every row, 3x, on three backgrounds; <= 1280 px wide."""
    for cid in ids:
        base = P2.BASE_OF[cid]
        sb, mb = _load(base)
        sv, mv = _load(cid)
        rows = [a for a in mv['anims'] if a in mb['anims'] or a in P2.CARRY_ROWS]
        k = 2 if len(rows) > 9 else 3
        tiles = []
        for a in rows:
            nb = mb['anims'].get(a, {}).get('frames', 0)
            nv = mv['anims'][a]['frames']
            rb = _row(sb, mb, a)[:, :nb * CELL_W] if nb else np.zeros((CELL_H, CELL_W, 4), np.uint8)
            rv = _row(sv, mv, a)[:, :nv * CELL_W]
            w = max(rb.shape[1], rv.shape[1])
            line = np.zeros((CELL_H, 2 * w + 8, 4), np.uint8)
            line[:, :rb.shape[1]] = rb
            line[:, w + 8:w + 8 + rv.shape[1]] = rv
            tiles.append(line)
        W = max(t.shape[1] for t in tiles)
        strip = np.zeros((CELL_H * len(tiles), W, 4), np.uint8)
        for i, t in enumerate(tiles):
            strip[i * CELL_H:(i + 1) * CELL_H, :t.shape[1]] = t
        img = Image.fromarray(strip, 'RGBA')
        out = Image.new('RGBA', (img.width * len(BGS) + 6 * (len(BGS) - 1), img.height), (0, 0, 0, 255))
        for j, bg in enumerate(BGS):
            out.paste(CH.on_bg(img, bg), (j * (img.width + 6), 0))
        if out.width * k > 1280:
            k = max(1, 1280 // out.width)
        CH.up(out, k).save(os.path.join(CH.PREV, f'c3p2_{cid}_rows.png'))


# ----------------------------------------------------------------------------------- checks
def check_c3p2(ids=None) -> list[str]:
    """Look contract: the base's rows first in the base's order with the same frame counts and the SAME alpha
    (a look never changes the silhouette), visible soot, carry rows walking like walk_side, portraits."""
    fails = []
    for cid in ids or IDS:
        base = P2.BASE_OF[cid]
        try:
            sb, mb = _load(base)
            sv, mv = _load(cid)
        except FileNotFoundError as e:
            fails.append(f'{cid}: {e}')
            continue
        if mv.get('cell') != [32, 56] or mv.get('origin') != [16, 54]:
            fails.append(f'{cid}: cell/origin differ from the contract')
        names_b, names_v = list(mb['anims']), list(mv['anims'])
        if names_v[:len(names_b)] != names_b:
            fails.append(f'{cid}: rows {names_v} do not start with the rows of {base} {names_b}')
        want = names_b + (P2.CARRY_ROWS if cid.endswith('_soot') else [])
        if names_v != want:
            fails.append(f'{cid}: rows {names_v} != {want}')
        changed = opaque = 0
        for a in names_b:
            if a not in mv['anims']:
                continue
            ab, av = mb['anims'][a], mv['anims'][a]
            if (ab['row'], ab['frames'], ab['fps'], ab['loop']) != (av['row'], av['frames'], av['fps'], av['loop']):
                fails.append(f'{cid}: row {a} {av} differs from {base} {ab}')
                continue
            if cid.endswith('_soot'):
                rb, rv = _row(sb, mb, a), _row(sv, mv, a)
                if not np.array_equal(rb[..., 3] > 0, rv[..., 3] > 0):
                    fails.append(f'{cid}: row {a}: silhouette differs from {base}')
                m = rb[..., 3] > 0
                opaque += int(m.sum())
                changed += int((np.abs(rb[..., :3].astype(int) - rv[..., :3].astype(int)).sum(-1)[m] > 0).sum())
        if cid.endswith('_soot'):
            share = changed / max(1, opaque)
            if not 0.05 <= share <= 0.50:
                fails.append(f'{cid}: soot covers {share:.1%} of the figure (expected 5..50 %)')
            for a in P2.CARRY_ROWS:
                an = mv['anims'].get(a, {})
                if an.get('frames') != 8:
                    fails.append(f'{cid}: {a} has {an.get("frames")} frames, expected 8')
            gs = mv.get('ground_speed', {})
            if gs.get('carry_side') != gs.get('walk_side'):
                fails.append(f'{cid}: carry_side ground_speed {gs.get("carry_side")} != walk_side {gs.get("walk_side")}')
            if mv['anims'].get('idle_side', {}).get('variants') != mb['anims'].get('idle_side', {}).get('variants'):
                fails.append(f'{cid}: idle variants differ from {base}')
            # the file is really in the hands: carry rows differ from idle / walk at the chest
            for a, ref in (('carry_side', 'walk_side'), ('carry_idle_side', 'idle_side')):
                if a in mv['anims'] and np.array_equal(_row(sv, mv, a), _row(sv, mv, ref)):
                    fails.append(f'{cid}: {a} is identical to {ref}')
        d = _base_dir(cid)
        pj = os.path.join(d, 'portrait.json')
        if os.path.exists(pj):
            meta_p = json.load(open(pj, encoding='utf-8'))
            if meta_p.get('size') != [112, 112] or \
                    meta_p.get('expressions') != ['neutral', 'concerned', 'determined', 'surprised']:
                fails.append(f'{cid}: portrait.json {meta_p.get("size")} {meta_p.get("expressions")} off contract')
            if (meta_p.get('anim') or {}).get('file') != 'portrait_anim.png' or \
                    not os.path.exists(os.path.join(d, 'portrait_anim.png')):
                fails.append(f'{cid}: no living portrait')
        else:
            fails.append(f'{cid}: portrait missing (run with --portraits)')
    return fails


def run_checks(ids=None) -> int:
    fails = check_c3p2(ids)
    # the generic validator (feet, borders, orphans, heights, normals) on the looks only
    print('--- characters_check (tables extended in memory) ---')
    keep = CHK.OUT
    rc = CHK.main()
    CHK.OUT = keep
    for f in fails:
        print('  -', f)
    print('OK: C3P2 look checks pass' if not fails else 'FAIL: C3P2 look checks')
    return 1 if (rc or fails) else 0


# ----------------------------------------------------------------------------------- main
def main(argv):
    install()
    args = [a for a in argv[1:] if not a.startswith('--')]
    opts = dict(a[2:].split('=', 1) if '=' in a else (a[2:], '1') for a in argv[1:] if a.startswith('--'))
    if 'out' in opts:
        set_out(os.path.abspath(opts['out']))
    if 'check' in opts:
        return run_checks(args or None)
    ids = args or IDS
    bad = [c for c in ids if c not in P2.CAST_C3P2]
    if bad:
        print('not a C3P2 look:', bad)
        return 2
    os.makedirs(CH.PREV, exist_ok=True)
    open(os.path.join(CH.PREV, '.gdignore'), 'a').close()
    for cid in ids:
        spec, sheet, nsheet, meta = CH.build_sheet(cid)
        print(f'{cid:13s} rows={",".join(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]} '
              f'ground_speed={meta.get("ground_speed", {})}')
    preview(ids)
    if 'portraits' in opts:
        import chargen_portrait_c3p2 as PP
        PP.build(ids, CH.OUT)
    return run_checks(ids)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
