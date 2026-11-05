"""env_karsk_emblems -- hand-pixelled state emblems for scene A1 'Verladebahnhof Karsk'.

TECHNICAL_ARCHITECTURE §12.4 (historical insignia switch):
    neutral files  -> the fictional gear-and-wheat emblem ('gw*', 'g*')
    *_hist files   -> the real Soviet hammer & sickle ('hs*')
Both variants of one placement have the same footprint, so a _hist file only swaps the emblem pixels.
The masks are drawn by hand at their final size (no scaling): one pixel = one game pixel.
Insignia appear only as in-world iconography of the Soviet state (civic banner, freight-office sign,
reconstruction poster, an old wagon stencil, a newspaper masthead) -- never as decoration of UI or rewards.
"""
from __future__ import annotations

import numpy as np

MASKS = {
    # ---- hammer & sickle (sickle opens to the upper left, tip at the top, handle down-left;
    #      hammer head inside the curve at the upper left, handle down-right)
    'hs11': """
.....###...
.##....##..
####....##.
.####....#.
..####...#.
...#.##.##.
......###..
....######.
..###...##.
.##......#.
##.........""",
    'hs9': """
.....##..
.#.....#.
###....##
.###...##
..#.#.##.
....###..
..##.##..
.##...##.
##.....#.""",
    'hs7': """
....##.
.#....#
###...#
.#.#.#.
...##..
.##.##.
#....#.""",
    'hs5': """
.#.#.
###.#
.#.#.
.##..
#..#.""",
    # ---- fictional neutral emblem: cogwheel with a wheat ear across it
    'gw11': """
....###....
.#.#####.#.
..##....##.
.##....####
###...####.
###..####.#
###.####.##
.##.#.#.##.
..#.#..##..
.#.#####.#.
....###....""",
    'gw9': """
...###...
.#######.
.##...##.
###..####
###.####.
###.#.###
.#.#..##.
.#######.
...###...""",
    'gw7': """
..###..
.#####.
##..###
##.###.
##.#.##
.#####.
..###..""",
    'gw5': """
.###.
##.##
#.#.#
##.##
.###.""",
    # ---- plain five-pointed star (used in both variants, e.g. tiny loco lamp board)
    'star7': """
...#...
...#...
#######
.#####.
..###..
.##.##.
.#...#.""",
}

# neutral -> historical pairs of equal size
PAIRS = {'gw11': 'hs11', 'gw9': 'hs9', 'gw7': 'hs7', 'gw5': 'hs5'}


def mask(kind: str) -> np.ndarray:
    rows = [r for r in MASKS[kind].strip('\n').split('\n')]
    w = max(len(r) for r in rows)
    m = np.zeros((len(rows), w), bool)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            m[y, x] = ch == '#'
    return m


def size(kind: str):
    m = mask(kind)
    return m.shape[1], m.shape[0]


def kind_for(neutral_kind: str, hist: bool) -> str:
    return PAIRS.get(neutral_kind, neutral_kind) if hist else neutral_kind


def paint(L, x: int, y: int, kind: str, col, shade=None, hgt=None, wear: float = 0.0, seed: int = 0,
          wear_col=None):
    """Stamp emblem `kind` with its top-left at (x, y).
    shade: optional colour for the lower-right edge pixels (relief / paint thickness).
    wear:  0..1 fraction of pixels knocked back to `wear_col` (or left untouched when wear_col is None),
           deterministic per (seed, pixel) -> weathered stencils."""
    m = mask(kind)
    h, w = m.shape
    rng = np.random.default_rng(seed)
    worn = rng.random((h, w)) < wear
    for yy in range(h):
        for xx in range(w):
            if not m[yy, xx]:
                continue
            if worn[yy, xx]:
                if wear_col is not None:
                    L.px(x + xx, y + yy, wear_col, hgt)
                continue
            c = col
            if shade is not None:
                below = yy + 1 >= h or not m[yy + 1, xx]
                right = xx + 1 >= w or not m[yy, xx + 1]
                if below and right:
                    c = shade
            L.px(x + xx, y + yy, c, hgt)
