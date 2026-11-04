"""characters.py -- builds every character sprite sheet (+ normal map) and dialogue portrait strip.

    py -3 -P tools/pixelgen/characters.py            (all characters + portraits + previews)
    py -3 -P tools/pixelgen/characters.py alexei     (one character)

Outputs (contract: documentation/TECHNICAL_ARCHITECTURE.md section 4):
    assets/characters/<id>/sheet.png, sheet_n.png, sheet.json
    assets/characters/<id>/portrait.png, portrait.json            (alexei, konrad, irina, emil)
    assets/characters/_preview/*                                   (review images, .gdignore'd)
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
from chargen_cast import CAST                 # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'characters')
PREV = os.path.join(OUT, '_preview')
ORIGIN = [16, 54]

# anim name -> (view, pose builder, fps, loop)
ANIMS = {
    'idle_side': ('side', lambda s: A.idle_side(s), 5, True),
    'walk_side': ('side', lambda s: A.walk_side(s), 10, True),
    'idle_front': ('front', lambda s: A.idle_front(s), 5, True),
    'walk_front': ('front', lambda s: A.walk_front(s), 10, True),
    'idle_back': ('back', lambda s: A.idle_front(s), 5, True),
    'walk_back': ('back', lambda s: A.walk_front(s, back=True), 10, True),
    'inspect_side': ('side', lambda s: A.inspect_side(s), 8, False),
    'interact_side': ('side', lambda s: A.interact_side(s), 8, False),
    'talk_side': ('side', lambda s: A.talk_side(s), 6, True),
}
FULL = ['idle_side', 'walk_side', 'idle_front', 'walk_front', 'idle_back', 'walk_back', 'inspect_side',
        'interact_side', 'talk_side']
ROWS = {
    'alexei': FULL,
    'konrad': FULL,
    'irina': ['idle_side', 'walk_side', 'idle_front', 'talk_side'],
    'emil': ['idle_side', 'talk_side', 'idle_front'],
    'worker_a': ['idle_side', 'walk_side'],
    'babushka': ['idle_side', 'walk_side'],
    'child_a': ['idle_side', 'walk_side'],
    'berlin_father': ['idle_side', 'walk_side'],
    'berlin_mother': ['idle_side', 'walk_side'],
    'berlin_child': ['idle_side', 'walk_side'],
    'clerk': ['idle_side', 'walk_side'],
    'guard': ['idle_side', 'walk_side'],
}
# ground speed (px/s) that matches the planted foot travel of the walk cycles
def ground_speed(spec, anim):
    st = A.st(spec.style)
    if anim == 'walk_side':
        return round(st['stride'] * 1.95 / 4 * 10, 1)   # planted foot travels ~1.95*stride in 4 frames
    if anim in ('walk_front', 'walk_back'):
        return round(st['stride'] * 1.95 / 4 * 10 * 0.6, 1)
    return None


def build_sheet(cid: str):
    spec = CAST[cid]()
    rows = ROWS[cid]
    ncols = max(len(ANIMS[a][1](spec.style)) for a in rows)
    sheet = np.zeros((CELL_H * len(rows), CELL_W * ncols, 4), np.uint8)
    nsheet = np.zeros_like(sheet)
    meta = {'id': cid, 'cell': [CELL_W, CELL_H], 'origin': ORIGIN, 'facing': 'right', 'anims': {}}
    speeds = {}
    for r, name in enumerate(rows):
        view, fn, fps, loop = ANIMS[name]
        frames = fn(spec.style)
        for c, P in enumerate(frames):
            rgba, nm, fr, J = render(spec, view, P)
            sheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = rgba
            nsheet[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] = nm
        meta['anims'][name] = {'row': r, 'frames': len(frames), 'fps': fps, 'loop': loop}
        gs = ground_speed(spec, name)
        if gs:
            speeds[name] = gs
    if speeds:
        meta['ground_speed'] = speeds
    d = os.path.join(OUT, cid)
    os.makedirs(d, exist_ok=True)
    Image.fromarray(sheet, 'RGBA').save(os.path.join(d, 'sheet.png'))
    Image.fromarray(nsheet, 'RGBA').save(os.path.join(d, 'sheet_n.png'))
    with open(os.path.join(d, 'sheet.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)
    return spec, sheet, nsheet, meta


# ----------------------------------------------------------------------------------- previews
BG_K = (40, 54, 52, 255)       # Karsk playfield shadow
BG_A = (14, 26, 32, 255)       # archive navy
BG_L = (152, 173, 154, 255)    # bright Karsk haze


def on_bg(img: Image.Image, bg) -> Image.Image:
    out = Image.new('RGBA', img.size, bg)
    out.alpha_composite(img)
    return out


def up(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def preview_contact(cid, sheet, meta):
    img = Image.fromarray(sheet, 'RGBA')
    bg = BG_A if CAST[cid]().scene != 'karsk' else BG_K
    a = on_bg(img, bg)
    b = on_bg(img, BG_L)
    out = Image.new('RGBA', (img.width * 2 + 8, img.height), (0, 0, 0, 255))
    out.paste(a, (0, 0))
    out.paste(b, (img.width + 8, 0))
    up(out, 3).save(os.path.join(PREV, f'{cid}_contact_3x.png'))


def preview_lineup(sheets: dict):
    """Frame 0 of idle_side for every character at 1x and 3x, on three backgrounds."""
    ids = list(sheets)
    W = CELL_W * len(ids)
    strip = Image.new('RGBA', (W, CELL_H), (0, 0, 0, 0))
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        r = meta['anims']['idle_side']['row']
        cell = Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W], 'RGBA')
        strip.alpha_composite(cell, (i * CELL_W, 0))
    rows = [on_bg(strip, BG_K), on_bg(strip, BG_A), on_bg(strip, BG_L)]
    out = Image.new('RGBA', (W, CELL_H * 3), (0, 0, 0, 255))
    for k, r in enumerate(rows):
        out.paste(r, (0, k * CELL_H))
    out.save(os.path.join(PREV, 'lineup_1x.png'))
    up(out, 3).save(os.path.join(PREV, 'lineup_3x.png'))
    # silhouette check: pure black shapes at 1x
    sil = Image.new('RGBA', strip.size, (205, 210, 200, 255))
    a = np.array(strip)[..., 3] > 0
    s = np.array(sil)
    s[a] = (20, 20, 24, 255)
    up(Image.fromarray(s), 3).save(os.path.join(PREV, 'lineup_silhouettes_3x.png'))


def preview_walks(sheets: dict):
    """All walk_side rows stacked (3x) for timing / volume review."""
    ids = [c for c in sheets if 'walk_side' in sheets[c][1]['anims']]
    out = Image.new('RGBA', (CELL_W * 8, CELL_H * len(ids)), BG_K)
    for i, cid in enumerate(ids):
        sheet, meta = sheets[cid]
        r = meta['anims']['walk_side']['row']
        row = Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W * 8], 'RGBA')
        out.alpha_composite(row, (0, i * CELL_H))
    up(out, 3).save(os.path.join(PREV, 'walk_strips_3x.png'))
    # animated GIFs side by side (for manual review in a browser)
    frames = []
    for f in range(8):
        fr_img = Image.new('RGBA', (CELL_W * len(ids), CELL_H), BG_K)
        for i, cid in enumerate(ids):
            sheet, meta = sheets[cid]
            r = meta['anims']['walk_side']['row']
            cell = Image.fromarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W], 'RGBA')
            fr_img.alpha_composite(cell, (i * CELL_W, 0))
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
    (Lambert, like Godot's 2D lights) -> verifies the normal maps visually."""
    tiles = []
    for cid, (sheet, meta) in sheets.items():
        nm = np.asarray(Image.open(os.path.join(OUT, cid, 'sheet_n.png')).convert('RGBA')).astype(np.float32)
        r = meta['anims']['idle_side']['row']
        d = sheet[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W].astype(np.float32)
        n = nm[r * CELL_H:(r + 1) * CELL_H, 0:CELL_W, :3] / 255 * 2 - 1
        for L in ((-1.0, 0.3, 0.4), (1.0, 0.3, 0.4), (0.0, 1.0, 0.3)):
            Lv = np.asarray(L, np.float32) / np.linalg.norm(L)
            lam = np.clip((n * Lv).sum(-1), 0, 1)
            out = d.copy()
            out[..., :3] = np.clip(d[..., :3] * (0.35 + 1.2 * lam[..., None]), 0, 255)
            tiles.append(Image.fromarray(out.astype(np.uint8), 'RGBA'))
    o = Image.new('RGBA', (CELL_W * 6, CELL_H * ((len(tiles) + 5) // 6)), (30, 34, 40, 255))
    for i, t in enumerate(tiles):
        o.alpha_composite(t, ((i % 6) * CELL_W, (i // 6) * CELL_H))
    up(o, 3).save(os.path.join(PREV, 'normal_relight_test.png'))


def main(argv):
    os.makedirs(PREV, exist_ok=True)
    open(os.path.join(PREV, '.gdignore'), 'a').close()
    ids = argv[1:] or list(CAST)
    sheets = {}
    for cid in ids:
        spec, sheet, nsheet, meta = build_sheet(cid)
        sheets[cid] = (sheet, meta)
        preview_contact(cid, sheet, meta)
        preview_onion(cid, sheet, meta)
        print(f'{cid:14s} rows={len(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]}')
    if len(ids) > 1:
        preview_lineup(sheets)
        preview_walks(sheets)
        preview_relight(sheets)
    try:
        import chargen_portrait
        chargen_portrait.main([c for c in ids if c in chargen_portrait.PORTRAITS])
    except ImportError:
        pass


if __name__ == '__main__':
    main(sys.argv)
