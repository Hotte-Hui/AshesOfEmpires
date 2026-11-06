"""characters_c3.py -- builds the Chapter 3 cast through the EXISTING character pipeline.

    py -3 -P tools/pixelgen/characters_c3.py                 (all seven C3 ids: sheets, previews, validator)
    py -3 -P tools/pixelgen/characters_c3.py elena kessler   (selected ids)
    py -3 -P tools/pixelgen/characters_c3.py --portraits     (additionally the dialogue portraits through
                                                             chargen_portrait2 -- the C3 speakers are
                                                             registered there by chargen_portrait_c3)
    py -3 -P tools/pixelgen/characters_c3.py --check         (validate only)
    py -3 -P tools/pixelgen/characters_c3.py --out=DIR       (review run: write everything below DIR)

Imports characters.py (ANIMS, ROWS, build_sheet, ground_speed, previews) and characters_check.py and extends
their tables IN MEMORY with the new ids (chargen_cast_c3); only the new ids are built.
Round 7: the cast is on the round-2 rig (8-frame idle / talk, variants, front views); the first-generation
portrait generator this runner used to call no longer exists (portraits: chargen_portrait_c3 on the
round-2 pipeline).
Outputs (TECHNICAL_ARCHITECTURE section 4):
    assets/characters/<id>/sheet.png, sheet_n.png, sheet.json  (+ portrait.png, portrait_anim.png, portrait.json)
    assets/characters/_preview/c3_*            (review images; the folder is .gdignore'd and git-ignored)
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
from chargen_body import CELL_H, CELL_W   # noqa: E402

C3_IDS = list(C3.CAST_C3)
REFERENCE = ['alexei', 'konrad', 'irina', 'emil']      # existing cast shown next to the new one in previews


# ----------------------------------------------------------------------------------- install
def install():
    """Extend the existing pipeline's tables in memory (idempotent)."""
    CH.CAST.update(C3.CAST_C3)
    CH.ROWS.update(C3.ROWS_C3)
    CHK.EXPECT_H.update(C3.EXPECT_H_C3)
    for cid, rows in C3.ROWS_C3.items():     # NPC rule: exactly the rows this cast ships
        CHK.NPC_MIN[cid] = list(rows)
    voronova_hat_edge()


# Round 8 (feel_r8): at 1x Lidia Voronova's dark karakul pirozhok ran into her grey hair (both dark in the
# station's dawn light). The lowest row of the hat gets the light curl tips (hat tones 5 / 4 instead of 1 / 2):
# a 1-px lighter fur edge between hat and hair, in both views (the talking / blinking variants derive from them).
VORONOVA_HAT_EDGE = {
    'VORONOVA_SIDE': (3, '. . . 4 5 4 5 4 5 4 . .'),
    'VORONOVA_FRONT': (3, '. 4 5 4 5 4 5 4 5 4 .'),
}


def voronova_hat_edge():
    """Patches the head bitmaps of chargen_cast_c3 in memory before voronova() is built (idempotent)."""
    for name, (row, text) in VORONOVA_HAT_EDGE.items():
        rows = getattr(C3, name)
        if len(text.split()) != len(rows[row].split()):
            raise ValueError(f'{name}: hat edge row has the wrong width')
        rows[row] = text


def set_out(root):
    CH.OUT = os.path.join(root, 'assets', 'characters') if root else CH.OUT
    CH.PREV = os.path.join(CH.OUT, '_preview')
    CHK.OUT = CH.OUT


# ----------------------------------------------------------------------------------- previews
def _cell(sheet, meta, anim, f=0):
    r = meta['anims'][anim]['row']
    return Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W], 'RGBA')


def _load(cid):
    d = os.path.join(CH.OUT, cid)
    if not os.path.exists(os.path.join(d, 'sheet.json')):
        d = os.path.join(os.path.dirname(HERE), '..', 'assets', 'characters', cid)
    meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
    sheet = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA'))
    return sheet, meta


def preview_lineup(sheets: dict):
    """idle_side frame 0 of the new cast next to the reference cast, 1x and 4x, three backgrounds,
    plus a pure silhouette strip (readability at 46 px)."""
    ids = list(sheets)
    W = CELL_W * len(ids)
    strip = Image.new('RGBA', (W, CELL_H), (0, 0, 0, 0))
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        strip.alpha_composite(_cell(sheet, meta, 'idle_side'), (i * CELL_W, 0))
    bgs = [CH.BG_K, CH.BG_A, CH.BG_L, (58, 70, 88, 255)]
    out = Image.new('RGBA', (W, CELL_H * len(bgs)), (0, 0, 0, 255))
    for k, bg in enumerate(bgs):
        out.paste(CH.on_bg(strip, bg), (0, k * CELL_H))
    out.save(os.path.join(CH.PREV, 'c3_lineup_1x.png'))
    CH.up(out, 4).save(os.path.join(CH.PREV, 'c3_lineup_4x.png'))
    sil = np.array(Image.new('RGBA', strip.size, (205, 210, 200, 255)))
    sil[np.array(strip)[..., 3] > 0] = (20, 20, 24, 255)
    CH.up(Image.fromarray(sil), 4).save(os.path.join(CH.PREV, 'c3_lineup_silhouettes_4x.png'))


def preview_rows(cid, sheet, meta):
    """Every row of one character at 4x on the station-dawn and palais backgrounds."""
    img = Image.fromarray(sheet, 'RGBA')
    a = CH.on_bg(img, (40, 50, 64, 255))
    b = CH.on_bg(img, (22, 34, 40, 255))
    out = Image.new('RGBA', (img.width * 2 + 8, img.height), (0, 0, 0, 255))
    out.paste(a, (0, 0))
    out.paste(b, (img.width + 8, 0))
    CH.up(out, 4).save(os.path.join(CH.PREV, f'c3_{cid}_rows_4x.png'))


def preview_talk(sheets: dict):
    """All talk_side rows stacked (4x): the gesture must read in every frame."""
    ids = [c for c in sheets if 'talk_side' in sheets[c][1]['anims']]
    out = Image.new('RGBA', (CELL_W * 4, CELL_H * len(ids)), (40, 50, 64, 255))
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        for f in range(meta['anims']['talk_side']['frames']):
            out.alpha_composite(_cell(sheet, meta, 'talk_side', f), (f * CELL_W, i * CELL_H))
    CH.up(out, 4).save(os.path.join(CH.PREV, 'c3_talk_strips_4x.png'))


def preview_walk_gif(sheets: dict):
    ids = [c for c in sheets if 'walk_side' in sheets[c][1]['anims']]
    if not ids:
        return
    frames = []
    for f in range(8):
        fr_img = Image.new('RGBA', (CELL_W * len(ids), CELL_H), (40, 50, 64, 255))
        for i, cid in enumerate(ids):
            sheet, meta = sheets[cid]
            fr_img.alpha_composite(_cell(sheet, meta, 'walk_side', f), (i * CELL_W, 0))
        frames.append(CH.up(fr_img, 4).convert('P', palette=Image.ADAPTIVE, colors=255))
    frames[0].save(os.path.join(CH.PREV, 'c3_walk_side.gif'), save_all=True, append_images=frames[1:],
                   duration=100, loop=0, disposal=2)


def preview_relight(ids):
    """Lambert relight of idle frame 0 through the normal map from left / right / top (like Godot 2D
    lights) -> verifies the normal maps visually."""
    tiles = []
    for cid in ids:
        d = os.path.join(CH.OUT, cid)
        meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
        sheet = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA')).astype(np.float32)
        nm = np.asarray(Image.open(os.path.join(d, 'sheet_n.png')).convert('RGBA')).astype(np.float32)
        r = meta['anims']['idle_side']['row']
        dd = sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W]
        n = nm[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W, :3] / 255 * 2 - 1
        for L in ((-1.0, 0.3, 0.4), (1.0, 0.3, 0.4), (0.0, 1.0, 0.3)):
            Lv = np.asarray(L, np.float32) / np.linalg.norm(L)
            lam = np.clip((n * Lv).sum(-1), 0, 1)
            o = dd.copy()
            o[..., :3] = np.clip(dd[..., :3] * (0.35 + 1.2 * lam[..., None]), 0, 255)
            tiles.append(Image.fromarray(o.astype(np.uint8), 'RGBA'))
    o = Image.new('RGBA', (CELL_W * 6, CELL_H * ((len(tiles) + 5) // 6)), (30, 34, 40, 255))
    for i, t in enumerate(tiles):
        o.alpha_composite(t, ((i % 6) * CELL_W, (i // 6) * CELL_H))
    CH.up(o, 3).save(os.path.join(CH.PREV, 'c3_normal_relight_test.png'))


# ----------------------------------------------------------------------------------- checks
def check_c3(ids=None) -> list[str]:
    """Contract checks beyond characters_check: exact rows, talk gesture, walk speed, portraits,
    silhouette distinctness against the existing cast."""
    fails = []
    ids = ids or C3_IDS
    sil = {}
    for cid in ids + REFERENCE:
        d = os.path.join(CH.OUT, cid)
        if cid in REFERENCE and not os.path.exists(os.path.join(d, 'sheet.json')):
            d = os.path.abspath(os.path.join(HERE, '..', '..', 'assets', 'characters', cid))
        meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
        a = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA'))[..., 3] > 0
        r = meta['anims']['idle_side']['row']
        sil[cid] = a[r * CELL_H:(r + 1) * CELL_H, :CELL_W]
        if cid in REFERENCE:
            continue
        if list(meta['anims']) != C3.ROWS_C3[cid]:
            fails.append(f'{cid}: rows {list(meta["anims"])} != {C3.ROWS_C3[cid]}')
        if meta.get('origin') != [16, 54] or meta.get('cell') != [32, 56]:
            fails.append(f'{cid}: cell/origin differ from the contract')
        t = meta['anims'].get('talk_side')
        if t:
            if t['frames'] != 8:
                fails.append(f'{cid}: talk_side has {t["frames"]} frames, expected 8 (round-2 rhythm)')
            rr = t['row']
            fr = [a[rr * CELL_H:(rr + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W] for f in range(t['frames'])]
            moved = max((fr[0] ^ fr[k]).sum() for k in range(1, len(fr)))
            if moved < 10:
                fails.append(f'{cid}: talk_side gesture too small ({moved} px change)')
        if 'walk_side' in meta['anims'] and 'walk_side' not in meta.get('ground_speed', {}):
            fails.append(f'{cid}: walk_side without ground_speed')
        pp, pj = os.path.join(d, 'portrait.png'), os.path.join(d, 'portrait.json')
        if not (os.path.exists(pp) and os.path.exists(pj)):
            fails.append(f'{cid}: portrait strip missing')
        else:
            meta_p = json.load(open(pj, encoding='utf-8'))
            if meta_p.get('size') != [112, 112] or                     meta_p.get('expressions') != ['neutral', 'concerned', 'determined', 'surprised']:
                fails.append(f'{cid}: portrait.json {meta_p} differs from the contract')
            anim = meta_p.get('anim') or {}
            if anim.get('file') != 'portrait_anim.png' or not os.path.exists(os.path.join(d, 'portrait_anim.png')):
                fails.append(f'{cid}: no living portrait (portrait_anim.png + anim block, round-2 contract)')
            else:
                ga = Image.open(os.path.join(d, 'portrait_anim.png'))
                if ga.size != (448, 112 * len(anim.get('rows', []))):
                    fails.append(f'{cid}: portrait_anim.png size {ga.size} does not match its rows')
            im = Image.open(pp)
            if im.size != (448, 112):
                fails.append(f'{cid}: portrait strip size {im.size} != (448, 112)')
            px = np.asarray(im.convert('RGBA'))
            if (px[..., 3] < 255).any():
                fails.append(f'{cid}: portrait has transparent pixels')
            frames = [px[:, k * 112:(k + 1) * 112, :3].astype(int) for k in range(4)]
            for k in range(1, 4):
                if (np.abs(frames[k] - frames[0]).sum(-1) > 0).sum() < 30:
                    fails.append(f'{cid}: portrait expression {k} barely differs from neutral')
    # silhouette distinctness (idle_side frame 0): intersection over union against every other figure
    keys = list(sil)
    for i, p in enumerate(keys):
        for q in keys[i + 1:]:
            if p in REFERENCE and q in REFERENCE:
                continue
            inter = (sil[p] & sil[q]).sum()
            uni = (sil[p] | sil[q]).sum()
            if uni and inter / uni > 0.90:
                fails.append(f'silhouettes of {p} and {q} nearly identical (IoU {inter / uni:.2f})')
    return fails


def run_checks(ids=None) -> int:
    print('--- characters_check (existing validator, tables extended in memory) ---')
    rc = CHK.main()
    print('--- C3 contract checks ---')
    fails = check_c3(ids)
    for f in fails:
        print('  -', f)
    print('OK: C3 contract checks pass' if not fails else 'FAIL: C3 contract checks')
    return 1 if (rc or fails) else 0


# ----------------------------------------------------------------------------------- main
def main(argv):
    install()
    args = [a for a in argv[1:] if not a.startswith('--')]
    opts = dict(a[2:].split('=', 1) if '=' in a else (a[2:], '1') for a in argv[1:] if a.startswith('--'))
    if 'out' in opts:
        set_out(os.path.abspath(opts['out']))
    if 'check' in opts:
        return run_checks()
    ids = args or C3_IDS
    bad = [c for c in ids if c not in C3.CAST_C3]
    if bad:
        print('not a C3 character:', bad)
        return 2
    os.makedirs(CH.PREV, exist_ok=True)
    open(os.path.join(CH.PREV, '.gdignore'), 'a').close()
    sheets = {}
    for cid in ids:
        spec, sheet, nsheet, meta = CH.build_sheet(cid)
        sheets[cid] = (sheet, meta)
        preview_rows(cid, sheet, meta)
        CH.preview_onion(cid, sheet, meta)
        gs = meta.get('ground_speed', {})
        print(f'{cid:15s} rows={",".join(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]} '
              f'ground_speed={gs}')
    for cid in REFERENCE:
        sheets_ref = _load(cid)
        sheets.setdefault(cid, sheets_ref)
    order = REFERENCE + ids
    sheets = {c: sheets[c] for c in order}
    preview_lineup(sheets)
    preview_talk(sheets)
    preview_walk_gif(sheets)
    preview_relight(ids)
    if 'portraits' in opts:
        import chargen_portrait2 as PG          # the C3 speakers are registered by chargen_portrait_c3
        PG.set_out(CH.OUT)
        PG.main(list(ids))
    return run_checks(ids)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
