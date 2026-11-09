"""env_flashback -- art of the four flashback films of the real-history cards (TECHNICAL_ARCHITECTURE 12.15).

Run:  py -3 -P tools/pixelgen/env_flashback.py [--sheet PNG] [--only film/shot]

Writes assets/cinematics/flashback/
  <film>/<shot>.png        twelve painted plates, 512 x 368 (the film shows a 480 x 360 gate drifting across them)
  nuremberg/desk_yellow.png, desk_red.png   the two lit lamps of the monitor (shown by the film in turn)
  look/gate.png            the gate: rounded corners, a ragged edge, a hair
  look/scratch_a.png, scratch_b.png, dust.png   one light and one dark scratch, four dust specks
  layout.json              plates, drift anchors, overlay positions, the ramp
Films and their cards: nuremberg = hist.reich.nuremberg_interpreters, evictions = hist.reich.evictions,
settlement = hist.soviet.special_settlements, kyshtym = hist.soviet.kyshtym (sheets: data/flashbacks/flashbacks.json).
Original and deterministic: fixed seeds, no downloads, no traced references; a re-run writes the same bytes.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_flashback_kit as K  # noqa: E402
import env_flashback_reich as R  # noqa: E402
import env_flashback_soviet as S  # noqa: E402

# film -> [(shot, painter, drift from, drift to)]: top-left of the 480 x 360 gate on the plate, at the start and the end
FILMS = {
    'nuremberg': [('court', R.court, (2, 4), (28, 4)), ('booth', R.booth, (20, 6), (10, 2)),
                  ('desk', R.desk, (4, 2), (26, 6))],
    'evictions': [('street', R.street, (2, 4), (28, 4)), ('chronicle', R.chronicle, (10, 2), (20, 6)),
                  ('room', R.room, (28, 4), (6, 4))],
    'settlement': [('steppe', S.steppe, (2, 4), (30, 4)), ('kommandantur', S.kommandantur, (26, 4), (8, 4)),
                   ('boundary', S.boundary, (16, 6), (16, 2))],
    'kyshtym': [('plant', S.plant, (2, 4), (28, 4)), ('village', S.village, (28, 4), (4, 4)),
                ('fence', S.fence, (16, 6), (16, 2))],
}
LAMP = 48                    # size of a lamp overlay
BLACK = (0, 0, 0, 255)


def save(arr: np.ndarray, rel: str) -> str:
    path = os.path.join(K.OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path, optimize=False)
    return path


def lamp_overlay(kind: str) -> np.ndarray:
    """One lit lamp as its own small sprite: the lens in three hard steps, a hot spot, a dithered halo on the box."""
    c = [K.hexrgb(h) for h in K.ACCENT[kind]]
    out = np.zeros((LAMP, LAMP, 4), np.uint8)
    yy, xx = np.mgrid[0:LAMP, 0:LAMP]
    d = np.hypot(xx + 0.5 - LAMP / 2.0, yy + 0.5 - LAMP / 2.0)
    chk = ((xx + yy) % 2) == 0
    out[(d < 20) & (d >= 13) & chk & ((d < 16) | (((xx // 2 + yy // 2) % 2) == 0))] = (*c[0], 255)
    out[d < 13] = (*c[1], 255)
    out[d < 10] = (*c[2], 255)
    out[np.hypot(xx + 0.5 - LAMP / 2.0 + 3, yy + 0.5 - LAMP / 2.0 + 3) < 4] = (*c[3], 255)
    out[(d < 14) & (d >= 12.5)] = (*K.hexrgb(K.RAMP_HEX[1]), 255)
    return out


def gate_mask() -> np.ndarray:
    """Black where the gate hides the frame: rounded corners, a slightly ragged edge, a hair at the top."""
    out = np.zeros((K.GH, K.GW, 4), np.uint8)
    yy, xx = np.mgrid[0:K.GH, 0:K.GW]
    rad = 9
    for cx in (rad, K.GW - rad):
        for cy in (rad, K.GH - rad):
            corner = (np.abs(xx + 0.5 - (0 if cx == rad else K.GW)) < rad) & (np.abs(yy + 0.5 - (0 if cy == rad else K.GH)) < rad)
            out[corner & (np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) > rad)] = BLACK
    r = K.rng(131)
    out[0, :] = BLACK
    out[-1, :] = BLACK
    out[:, 0] = BLACK
    out[:, -1] = BLACK
    for x in range(K.GW):
        if r.random() < 0.22:
            out[1, x] = BLACK
        if r.random() < 0.22:
            out[-2, x] = BLACK
    for y in range(K.GH):
        if r.random() < 0.18:
            out[y, 1] = BLACK
        if r.random() < 0.18:
            out[y, -2] = BLACK
    hair = pg.bezier([(150, 0), (158, 9), (148, 16), (159, 24)], 40)
    for hx, hy in hair:
        out[int(round(hy)), int(round(hx))] = BLACK
    return out


def scratch(h: int, seed: int, col: str) -> np.ndarray:
    """A vertical scratch, one pixel wide, broken into runs."""
    out = np.zeros((h, 1, 4), np.uint8)
    r = K.rng(seed)
    y = 0
    while y < h:
        run = int(r.integers(6, 40))
        out[y:min(h, y + run), 0] = (*K.hexrgb(col), 255)
        y += run + int(r.integers(1, 9))
    return out


def dust() -> np.ndarray:
    """Four specks, 8 x 8 each, in one strip."""
    out = np.zeros((8, 32, 4), np.uint8)
    r = K.rng(133)
    dark = (*K.hexrgb(K.RAMP_HEX[0]), 255)
    for f in range(4):
        x, y = 3 + int(r.integers(0, 2)), 3 + int(r.integers(0, 2))
        for _ in range(int(r.integers(3, 8))):
            out[y, f * 8 + x] = dark
            x = int(np.clip(x + r.integers(-1, 2), 1, 6))
            y = int(np.clip(y + r.integers(-1, 2), 1, 6))
    return out


def main(argv: list) -> int:
    sheet = argv[argv.index('--sheet') + 1] if '--sheet' in argv else ''
    only = argv[argv.index('--only') + 1] if '--only' in argv else ''
    layout = {
        'note': 'Flashback films of the real-history cards: plates, drift anchors (top-left of the 480x360 gate on '
                'the plate), overlays. Written by tools/pixelgen/env_flashback.py; do not edit by hand.',
        'view': [640, 360], 'gate': [80, 0, K.GW, K.GH], 'plate': [K.PW, K.PH],
        'ramp': K.RAMP_HEX, 'accents': K.ACCENT,
        'look': {'gate': 'look/gate.png', 'scratches': ['look/scratch_a.png', 'look/scratch_b.png'],
                 'dust': 'look/dust.png', 'dust_frames': 4},
        'films': {},
    }
    cells = []
    seed = 1000
    for film, shots in FILMS.items():
        layout['films'][film] = {'shots': {}}
        for shot, painter, a, b in shots:
            seed += 17
            rel = '%s/%s.png' % (film, shot)
            entry = {'tex': rel, 'size': [K.PW, K.PH], 'from': list(a), 'to': list(b), 'overlays': []}
            if shot == 'desk':
                for name, (cx, cy) in R.LAMPS.items():
                    entry['overlays'].append({'id': name, 'tex': 'nuremberg/desk_%s.png' % name,
                                              'pos': [cx - LAMP // 2, cy - LAMP // 2]})
            layout['films'][film]['shots'][shot] = entry
            if only and only != '%s/%s' % (film, shot):
                continue
            arr = K.resolve(painter(), seed=seed)
            save(arr, rel)
            cells.append(arr)
            print('wrote', rel)
    if not only:
        for name in R.LAMPS:
            save(lamp_overlay(name), 'nuremberg/desk_%s.png' % name)
        save(gate_mask(), 'look/gate.png')
        save(scratch(230, 141, K.RAMP_HEX[12]), 'look/scratch_a.png')
        save(scratch(150, 142, K.RAMP_HEX[0]), 'look/scratch_b.png')
        save(dust(), 'look/dust.png')
        with open(os.path.join(K.OUT, 'layout.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(layout, f, indent=1, ensure_ascii=False)
            f.write('\n')
        print('wrote layout.json')
    if sheet and cells:
        cols = 3 if len(cells) > 1 else 1
        rows = (len(cells) + cols - 1) // cols
        big = np.zeros((rows * K.PH, cols * K.PW, 4), np.uint8)
        big[..., 3] = 255
        for i, c in enumerate(cells):
            y, x = (i // cols) * K.PH, (i % cols) * K.PW
            big[y:y + K.PH, x:x + K.PW] = c
        img = Image.fromarray(big, 'RGBA').convert('RGB')
        if len(cells) > 1:
            img = img.resize((1278, int(round(big.shape[0] * 1278.0 / big.shape[1]))), Image.BOX)
        else:
            img = img.resize((K.PW * 2, K.PH * 2), Image.NEAREST)
        os.makedirs(os.path.dirname(os.path.abspath(sheet)), exist_ok=True)
        img.save(sheet)
        print('sheet', sheet)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
