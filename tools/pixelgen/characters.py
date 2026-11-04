"""characters.py -- builds every character sprite sheet (+ normal map) and the sprite review previews.

    py -3 -P tools/pixelgen/characters.py               (all characters + previews)
    py -3 -P tools/pixelgen/characters.py alexei vendor (some characters)
    py -3 -P tools/pixelgen/characters.py --portraits   (additionally run the portrait generator;
                                                         portraits are owned by chargen_portrait*)

Outputs (contract: documentation/TECHNICAL_ARCHITECTURE.md section 4):
    assets/characters/<id>/sheet.png, sheet_n.png, sheet.json
    assets/characters/_preview/*        (review images, .gdignore'd)
sheet.json extras (optional keys, ignored by older readers):
    "ground_speed": {anim: px/s}         planted-foot speed of walk rows (playback = speed / ground_speed)
    anims[a]["variants"]: [names]        one-shot rows the runtime mixes into the looping row `a`
    anims[a]["variant_gap"]: [min, max]  seconds between variants
    anims[v]["variant_of"]: a            marks a variant row
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

import chargen_anim as A                      # noqa: E402
from chargen_body import CELL_H, CELL_W, render   # noqa: E402
from chargen_cast import CAST as CAST_OLD     # noqa: E402
from chargen_cast import CAST_HIST            # noqa: E402
from chargen_cast_new import CAST_NEW         # noqa: E402

CAST = dict(CAST_OLD)
CAST.update(CAST_NEW)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'characters')
PREV = os.path.join(OUT, '_preview')
ORIGIN = [16, 54]

# anim name -> (view, pose builder, fps, loop)
ANIMS = {
    'idle_side': ('side', A.idle_side, 5, True),
    'walk_side': ('side', A.walk_side, 10, True),
    'idle_front': ('front', A.idle_front, 5, True),
    'walk_front': ('front', A.walk_front, 10, True),
    'idle_back': ('back', A.idle_front, 5, True),
    'walk_back': ('back', lambda s: A.walk_front(s, back=True), 10, True),
    'inspect_side': ('side', A.inspect_side, 8, False),
    'interact_side': ('side', A.interact_side, 9, False),
    'talk_side': ('side', A.talk_side, 7, True),
    'blink_side': ('side', A.blink_side, 9, False),
    'look_side': ('side', A.look_side, 6, False),
    'gesture_side': ('side', A.gesture_side, 7, False),
    'work_side': ('side', A.work_side, 6, True),
    'blink_front': ('front', A.blink_front, 9, False),
}
VARIANTS = {
    'idle_side': (['blink_side', 'blink_side', 'look_side', 'gesture_side'], [2.2, 5.5]),
    'idle_front': (['blink_front'], [2.5, 6.0]),
}
PROTAG = ['idle_side', 'walk_side', 'idle_front', 'walk_front', 'idle_back', 'walk_back', 'inspect_side',
          'interact_side', 'talk_side', 'blink_side', 'look_side', 'gesture_side', 'blink_front']
NPC = ['idle_side', 'walk_side', 'idle_front', 'talk_side', 'blink_side', 'look_side', 'gesture_side',
       'blink_front']
ROWS = {
    'alexei': PROTAG,
    'konrad': PROTAG,
    'irina': NPC,
    'emil': ['idle_side', 'talk_side', 'idle_front', 'walk_side', 'blink_side', 'look_side', 'gesture_side',
             'blink_front'],
    'worker_a': NPC + ['work_side'],
    'babushka': NPC,
    'child_a': NPC,
    'berlin_father': NPC,
    'berlin_mother': NPC,
    'berlin_child': NPC,
    'clerk': NPC,
    'guard': NPC,
    'librarian': NPC + ['work_side'],
    'porter': NPC + ['work_side'],
    'vendor': NPC + ['work_side'],
    'worker_b': NPC + ['work_side'],
}


def ground_speed(spec, anim):
    """Planted-foot speed of the walk rows (chargen_anim.walk_side: 0.5*stride per frame at 10 fps)."""
    s = A.st(spec.style)
    if anim == 'walk_side':
        return round(s['stride'] * 5.0, 1)
    if anim in ('walk_front', 'walk_back'):
        return round(s['stride'] * 5.0 * 0.6, 1)
    return None


def build_sheet(cid: str):
    spec = CAST[cid]()
    rows = ROWS[cid]
    built = []
    for name in rows:
        view, fn, fps, loop = ANIMS[name]
        built.append((name, view, fn(spec.style), fps, loop))
    ncols = max(len(f) for _, _, f, _, _ in built)
    sheet = np.zeros((CELL_H * len(rows), CELL_W * ncols, 4), np.uint8)
    nsheet = np.zeros_like(sheet)
    meta = {'id': cid, 'cell': [CELL_W, CELL_H], 'origin': ORIGIN, 'facing': 'right', 'anims': {}}
    speeds = {}
    for r, (name, view, frames, fps, loop) in enumerate(built):
        for c, P in enumerate(frames):
            rgba, nm, fr, J = render(spec, view, P)
            sheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = rgba
            nsheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = nm
        meta['anims'][name] = {'row': r, 'frames': len(frames), 'fps': fps, 'loop': loop}
        gs = ground_speed(spec, name)
        if gs:
            speeds[name] = gs
    for base, (vs, gap) in VARIANTS.items():
        have = [v for v in vs if v in meta['anims']]
        if base in meta['anims'] and have:
            meta['anims'][base]['variants'] = have
            meta['anims'][base]['variant_gap'] = gap
            for v in set(have):
                meta['anims'][v]['variant_of'] = base
    if speeds:
        meta['ground_speed'] = speeds
    d = os.path.join(OUT, cid)
    os.makedirs(d, exist_ok=True)
    Image.fromarray(sheet, 'RGBA').save(os.path.join(d, 'sheet.png'))
    Image.fromarray(nsheet, 'RGBA').save(os.path.join(d, 'sheet_n.png'))
    with open(os.path.join(d, 'sheet.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)
    if cid in CAST_HIST:
        # same rows / poses with the historical insignia -> sheet_hist.png (resolved by Symbols.pick at runtime)
        hspec = CAST_HIST[cid]()
        hsheet = np.zeros_like(sheet)
        for r, (name, view, frames, fps, loop) in enumerate(built):
            for c, P in enumerate(frames):
                rgba, nm, fr, J = render(hspec, view, P)
                hsheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = rgba
        Image.fromarray(hsheet, 'RGBA').save(os.path.join(d, 'sheet_hist.png'))
    return spec, sheet, nsheet, meta


# ----------------------------------------------------------------------------------- previews
BG_K = (40, 54, 52, 255)       # Karsk playfield shadow
BG_A = (14, 26, 32, 255)       # archive navy
BG_L = (152, 173, 154, 255)    # bright Karsk haze
BG_B = (52, 40, 50, 255)       # Berlin violet dusk


def on_bg(img: Image.Image, bg) -> Image.Image:
    out = Image.new('RGBA', img.size, bg)
    out.alpha_composite(img)
    return out


def up(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def cell(sheet, meta, anim, f=0):
    r = meta['anims'][anim]['row']
    return Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W], 'RGBA')


def preview_contact(cid, spec, sheet, meta):
    img = Image.fromarray(sheet, 'RGBA')
    bg = BG_K if spec.scene == 'karsk' else (BG_A if spec.scene == 'archive' else BG_B)
    a = on_bg(img, bg)
    b = on_bg(img, BG_L)
    out = Image.new('RGBA', (img.width * 2 + 8, img.height), (0, 0, 0, 255))
    out.paste(a, (0, 0))
    out.paste(b, (img.width + 8, 0))
    up(out, 3).save(os.path.join(PREV, f'{cid}_contact_3x.png'))


def preview_lineup(sheets: dict):
    """Frame 0 of idle_side for every character at 1x, 3x and 6x, on four backgrounds."""
    ids = list(sheets)
    W = CELL_W * len(ids)
    strip = Image.new('RGBA', (W, CELL_H), (0, 0, 0, 0))
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        strip.alpha_composite(cell(sheet, meta, 'idle_side'), (i * CELL_W, 0))
    rows = [on_bg(strip, BG_K), on_bg(strip, BG_A), on_bg(strip, BG_B), on_bg(strip, BG_L)]
    out = Image.new('RGBA', (W, CELL_H * len(rows)), (0, 0, 0, 255))
    for k, r in enumerate(rows):
        out.paste(r, (0, k * CELL_H))
    out.save(os.path.join(PREV, 'lineup_1x.png'))
    up(out, 3).save(os.path.join(PREV, 'lineup_3x.png'))
    up(rows[0], 6).save(os.path.join(PREV, 'lineup_6x.png'))
    # silhouette check: pure black shapes at 1x
    sil = Image.new('RGBA', strip.size, (205, 210, 200, 255))
    a = np.array(strip)[..., 3] > 0
    s = np.array(sil)
    s[a] = (20, 20, 24, 255)
    up(Image.fromarray(s), 3).save(os.path.join(PREV, 'lineup_silhouettes_3x.png'))
    # front views
    fids = [c for c in ids if 'idle_front' in sheets[c][1]['anims']]
    fs = Image.new('RGBA', (CELL_W * len(fids), CELL_H), (0, 0, 0, 0))
    for i, cid in enumerate(fids):
        sheet, meta = sheets[cid]
        fs.alpha_composite(cell(sheet, meta, 'idle_front'), (i * CELL_W, 0))
    up(on_bg(fs, BG_K), 6).save(os.path.join(PREV, 'lineup_front_6x.png'))


def preview_walks(sheets: dict):
    """All walk_side rows stacked (3x) + an animated GIF of every walk for timing review."""
    ids = [c for c in sheets if 'walk_side' in sheets[c][1]['anims']]
    out = Image.new('RGBA', (CELL_W * 8, CELL_H * len(ids)), BG_K)
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        r = meta['anims']['walk_side']['row']
        row = Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W * 8], 'RGBA')
        out.alpha_composite(row, (0, i * CELL_H))
    up(out, 3).save(os.path.join(PREV, 'walk_strips_3x.png'))
    frames = []
    for f in range(8):
        fr_img = Image.new('RGBA', (CELL_W * len(ids), CELL_H), BG_K)
        for i, cid in enumerate(ids):
            sheet, meta = sheets[cid]
            fr_img.alpha_composite(cell(sheet, meta, 'walk_side', f), (i * CELL_W, 0))
        frames.append(up(fr_img, 3).convert('P', palette=Image.ADAPTIVE, colors=255))
    frames[0].save(os.path.join(PREV, 'walk_side_all.gif'), save_all=True, append_images=frames[1:],
                   duration=100, loop=0, disposal=2)


def preview_onion(cid, sheet, meta, anim='walk_side'):
    """Overlay of all frames of one row (silhouette density) -> reveals jitter / volume changes."""
    if anim not in meta['anims']:
        return
    r = meta['anims'][anim]['row']
    n = meta['anims'][anim]['frames']
    acc = np.zeros((CELL_H, CELL_W), np.float32)
    for f in range(n):
        acc += sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W, 3] > 0
    img = (255 - acc / n * 230).astype(np.uint8)
    up(Image.fromarray(img, 'L'), 6).save(os.path.join(PREV, f'{cid}_{anim}_onion.png'))


def preview_relight(sheets: dict):
    """Relights idle frame 0 of every character through its normal map from the left, right and top
    (Lambert, like Godot's 2D lights), also MIRRORED (facing left, normal x negated as Godot does for
    flip_h) -> verifies the normal maps visually."""
    tiles = []
    for cid, (sheet, meta) in sheets.items():
        nm = np.asarray(Image.open(os.path.join(OUT, cid, 'sheet_n.png')).convert('RGBA')).astype(np.float32)
        r = meta['anims']['idle_side']['row']
        d = sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W].astype(np.float32)
        n = nm[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W, :3] / 255 * 2 - 1
        for mirror in (False, True):
            dd, nn = d, n.copy()
            if mirror:
                dd = d[:, ::-1]
                nn = n[:, ::-1].copy()
                nn[..., 0] *= -1
            for L in ((-1.0, 0.3, 0.4), (1.0, 0.3, 0.4)):
                Lv = np.asarray(L, np.float32) / np.linalg.norm(L)
                lam = np.clip((nn * Lv).sum(-1), 0, 1)
                out = dd.copy()
                out[..., :3] = np.clip(dd[..., :3] * (0.35 + 1.2 * lam[..., None]), 0, 255)
                tiles.append(Image.fromarray(out.astype(np.uint8), 'RGBA'))
    o = Image.new('RGBA', (CELL_W * 8, CELL_H * ((len(tiles) + 7) // 8)), (30, 34, 40, 255))
    for i, t in enumerate(tiles):
        o.alpha_composite(t, ((i % 8) * CELL_W, (i // 8) * CELL_H))
    up(o, 3).save(os.path.join(PREV, 'normal_relight_test.png'))


def main(argv):
    os.makedirs(PREV, exist_ok=True)
    open(os.path.join(PREV, '.gdignore'), 'a').close()
    args = [a for a in argv[1:] if not a.startswith('--')]
    ids = args or list(CAST)
    sheets = {}
    for cid in ids:
        spec, sheet, nsheet, meta = build_sheet(cid)
        sheets[cid] = (sheet, meta)
        preview_contact(cid, spec, sheet, meta)
        preview_onion(cid, sheet, meta)
        print(f'{cid:14s} rows={len(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]}'
              f' ground_speed={meta.get("ground_speed", {})}')
    if len(ids) > 1:
        preview_lineup(sheets)
        preview_walks(sheets)
        preview_relight(sheets)
    if '--portraits' in argv:
        import chargen_portrait
        chargen_portrait.main([c for c in ids if c in chargen_portrait.PORTRAITS])


if __name__ == '__main__':
    main(sys.argv)
