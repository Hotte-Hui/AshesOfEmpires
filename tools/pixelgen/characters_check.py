"""characters_check.py -- validates the character sheets against TECHNICAL_ARCHITECTURE section 4.

    py -3 -P tools/pixelgen/characters_check.py      -> prints a report, exit code 1 on any failure
Checks: json schema, row/frame layout, non-empty frames, feet on the origin row, no clipping at cell
borders, normal-map alpha == diffuse alpha, normals normalised, figure heights, portrait strips.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'characters')

EXPECT_H = {  # (min, max) figure height in px incl. headgear, idle_side frame 0
    'alexei': (44, 48), 'konrad': (44, 48), 'irina': (41, 45), 'emil': (41, 46), 'worker_a': (44, 48),
    'babushka': (37, 43), 'child_a': (28, 34), 'berlin_father': (44, 48), 'berlin_mother': (41, 45),
    'berlin_child': (28, 34), 'clerk': (44, 48), 'guard': (44, 49),
}
REQUIRED = {'alexei': 9, 'konrad': 9}
NPC_MIN = {'irina': ['idle_side', 'talk_side'], 'emil': ['idle_side', 'talk_side']}
CIV_MIN = ['idle_side', 'walk_side']


def main():
    fails, notes = [], []
    ids = sorted(d for d in os.listdir(OUT) if os.path.isdir(os.path.join(OUT, d)) and not d.startswith('_'))
    for cid in ids:
        d = os.path.join(OUT, cid)
        meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
        for k in ('id', 'cell', 'origin', 'facing', 'anims'):
            if k not in meta:
                fails.append(f'{cid}: sheet.json missing {k}')
        cw, ch = meta['cell']
        ox, oy = meta['origin']
        img = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA'))
        nrm = np.asarray(Image.open(os.path.join(d, 'sheet_n.png')).convert('RGBA'))
        if img.shape != nrm.shape:
            fails.append(f'{cid}: normal map size {nrm.shape} != sheet {img.shape}')
        if not np.array_equal(img[..., 3] > 0, nrm[..., 3] > 0):
            fails.append(f'{cid}: normal alpha differs from diffuse alpha')
        a = img[..., 3] > 0
        N = nrm[..., :3].astype(np.float32) / 255 * 2 - 1
        ln = np.linalg.norm(N[a], axis=-1)
        if len(ln) and (ln.min() < 0.9 or ln.max() > 1.1):
            fails.append(f'{cid}: normals not unit length ({ln.min():.2f}..{ln.max():.2f})')
        if (N[a][:, 2] < -0.05).any():
            fails.append(f'{cid}: normals pointing away from the viewer')
        names = list(meta['anims'])
        if cid in REQUIRED and len(names) != REQUIRED[cid]:
            fails.append(f'{cid}: expected {REQUIRED[cid]} rows, got {len(names)}')
        need = NPC_MIN.get(cid, CIV_MIN if cid not in REQUIRED else [])
        for n_ in need:
            if n_ not in meta['anims']:
                fails.append(f'{cid}: missing required anim {n_}')
        rows_used = set()
        for name, an in meta['anims'].items():
            r, nf = an['row'], an['frames']
            if r in rows_used:
                fails.append(f'{cid}: row {r} used twice')
            rows_used.add(r)
            if (r + 1) * ch > img.shape[0] or nf * cw > img.shape[1]:
                fails.append(f'{cid}:{name} outside the sheet')
                continue
            for f in range(nf):
                cell = a[r * ch:(r + 1) * ch, f * cw:(f + 1) * cw]
                if not cell.any():
                    fails.append(f'{cid}:{name}[{f}] empty')
                    continue
                if cell[:, 0].any() or cell[:, -1].any() or cell[0, :].any():
                    fails.append(f'{cid}:{name}[{f}] touches the cell border (clipped)')
                if cell[oy + 1:, :].any():
                    fails.append(f'{cid}:{name}[{f}] has pixels below the origin row')
                ys, xs = np.nonzero(cell)
                if name.startswith('idle') or name.startswith('talk'):
                    if ys.max() != oy:
                        fails.append(f'{cid}:{name}[{f}] feet row {ys.max()} != origin {oy}')
                    foot = xs[ys >= oy - 1]
                    if abs(foot.mean() - ox) > 3.5:
                        fails.append(f'{cid}:{name}[{f}] feet centre {foot.mean():.1f} far from origin x {ox}')
            # empty cells beyond frame count must stay empty
            if a[r * ch:(r + 1) * ch, nf * cw:].any():
                fails.append(f'{cid}:{name} has pixels beyond its frame count')
        r0 = meta['anims']['idle_side']['row']
        cell = a[r0 * ch:(r0 + 1) * ch, 0:cw]
        ys = np.nonzero(cell)[0]
        hgt = oy - ys.min() + 1
        lo, hi = EXPECT_H.get(cid, (20, 56))
        notes.append(f'{cid:14s} height {hgt:2d}px rows={len(names)} sheet={img.shape[1]}x{img.shape[0]}')
        if not lo <= hgt <= hi:
            fails.append(f'{cid}: figure height {hgt} outside {lo}-{hi}')
        pp = os.path.join(d, 'portrait.png')
        if os.path.exists(pp):
            pj = json.load(open(os.path.join(d, 'portrait.json'), encoding='utf-8'))
            pim = Image.open(pp)
            n = len(pj['expressions'])
            if pim.size != (pj['size'][0] * n, pj['size'][1]):
                fails.append(f'{cid}: portrait strip {pim.size} != {n} x {pj["size"]}')
            notes.append(f'{"":14s} portrait {pim.size[0]}x{pim.size[1]} {pj["expressions"]}')
    for n in notes:
        print(n)
    if fails:
        print('\nFAIL')
        for f in fails:
            print('  -', f)
        return 1
    print('\nOK: all character sheets pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
