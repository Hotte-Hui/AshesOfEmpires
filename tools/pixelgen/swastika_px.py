"""swastika_px -- pixel-exact Hakenkreuz masks for the `*_hist` insignia (TECHNICAL_ARCHITECTURE 12.4).

Only ever drawn into `_hist` twins that Symbols.pick() selects (neutral twins: the fictional Reichssiegel);
in-world iconography of the regime inside a critical narrative, never UI, reward or decoration.

Geometry: the right-facing hooked cross (hooks bent clockwise) of the classical 5 x 5 unit construction --
arm width = gap width = 1 unit, cross bars 5 units, hooks 3 units including the corner -- standing on a point
(turned 45 degrees) and centred in the white disc, as on the regime's flag.

Sizes from 9 px up are constructed exactly on the 45-degree pixel lattice instead of being rasterised from a
vector and thresholded: a pixel centre (x + .5, y + .5) relative to the emblem centre (cx, cy) maps to the
diagonal coordinates
    A = dx + dy   (the upright x axis)        B = dy - dx   (the upright y axis)
and every cell of the 5 x 5 grid is a U x U square in (A, B).  Each diagonal arm is then a clean stair band
exactly U pixels wide on every row, the hooks have the same width as the arms and the gaps, and no pixel
centre ever falls on a cell edge when the centre has the parity that U needs:
    U odd : centre on a pixel centre in both axes -> 5U x 5U box, single-pixel tips
            centre on a pixel corner in both axes -> (5U-1) x (5U-1) box, blunt 2-px tips
    U even: centre on a pixel centre in one axis and on a pixel corner in the other -> (5U-1) x 5U box
U odd is exact under the quarter turn (four congruent arms); U even is exact under the half turn and the
adjacent arms differ only in the phase of the stairs.  Below U = 2 the lattice loses the hooks, so the small
sizes (5, 7, 9 px) are hand-pixelled (picked from fractional lattices, frozen, quarter-turn symmetric).
"""
from __future__ import annotations

import math

import numpy as np

# Upright right-facing (clockwise) hooked cross, row 0 = top: the top arm hooks right, the right arm down,
# the bottom arm left, the left arm up.  Turned 45 degrees: NE arm -> SE, SE -> SW, SW -> NW, NW -> NE
# (the top point of the emblem is the tip of the NW arm's hook).
GRID = ("X.XXX",
        "X.X..",
        "XXXXX",
        "..X.X",
        "XXX.X")
_G = np.array([[c == 'X' for c in r] for r in GRID], bool)


def _frac(v: float) -> float:
    return v - math.floor(v)


def parity_ok(cx: float, cy: float, U: int) -> bool:
    fx, fy = _frac(cx), _frac(cy)
    if fx not in (0.0, 0.5) or fy not in (0.0, 0.5):
        return False
    return (fx == fy) if U % 2 else (fx != fy)


def at(w: int, h: int, cx: float, cy: float, U: int) -> np.ndarray:
    """Full-canvas (h x w) mask of the on-point hooked cross, cell size U, centred at (cx, cy) in continuous
    pixel coordinates (pixel (x, y) covers [x, x+1) x [y, y+1)).  Raises on a centre whose parity would put
    pixel centres on cell edges (the source of the lopsided arms of thresholded rasters)."""
    if U < 2 or not parity_ok(cx, cy, U):
        raise ValueError('swastika_px.at: centre (%.2f, %.2f) does not suit U=%d' % (cx, cy, U))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dx = xx + 0.5 - cx
    dy = yy + 0.5 - cy
    q = np.floor((dx + dy + 2.5 * U) / U).astype(int)
    r = np.floor((dy - dx + 2.5 * U) / U).astype(int)
    inside = (q >= 0) & (q < 5) & (r >= 0) & (r < 5)
    m = np.zeros((h, w), bool)
    m[inside] = _G[r[inside], q[inside]]
    return m


def centre_for(cx: float, cy_row: int, U: int) -> float:
    """Continuous y of the emblem centre on pixel row cy_row (its centre or its top edge), so that
    (cx, result) has the parity U needs."""
    fx = _frac(cx)
    want_centre = (fx == 0.5) if U % 2 else (fx == 0.0)
    return cy_row + (0.5 if want_centre else 0.0)


def tight(U: int, corner: bool = False, flip: bool = False) -> np.ndarray:
    """Cropped lattice emblem.  U odd: corner=False -> 5U x 5U (pixel-centred), corner=True -> (5U-1)^2.
    U even: flip=False -> (5U-1) wide x 5U tall, flip=True -> 5U wide x (5U-1) tall."""
    n = 5 * U + 4
    k = n // 2
    if U % 2:
        cx = cy = k if corner else k + 0.5
    else:
        cx, cy = (k + 0.5, float(k)) if not flip else (float(k), k + 0.5)
    m = at(n, n, cx, cy, U)
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _g(rows) -> np.ndarray:
    return np.array([[c == '#' for c in r] for r in rows], bool)


# Hand-pixelled small emblems, same chirality as the lattice (NE arm hooks to the SE), quarter-turn symmetric.
HAND = {
    5: _g([".#...",
           ".#.##",
           "..#..",
           "##.#.",
           "...#."]),
    7: _g(["..##...",
           ".##..#.",
           "..#.###",
           "#..#..#",
           "###.#..",
           ".#..##.",
           "...##.."]),
    9: _g(["....#....",
           "...##....",
           "..##..#..",
           "...#.###.",
           "##..#..##",
           ".###.#...",
           "..#..##..",
           "....##...",
           "....#...."]),
}


def mask(size: int) -> np.ndarray:
    """size x size box (the API of the older rasterisers): hand-pixelled for 5/7/9; otherwise the largest
    lattice emblem that fits, preferring one that sits exactly centred (an off-centre one only when it is at
    least 3 px larger)."""
    if size in HAND:
        return HAND[size].copy()
    exact, loose = None, None
    for U in range(2, size):
        if 5 * U - 1 > size:
            break
        for t in (tight(U), tight(U, corner=True)) if U % 2 else (tight(U),):
            th, tw = t.shape
            if th > size or tw > size:
                continue
            if (size - th) % 2 == 0 and (size - tw) % 2 == 0:
                if exact is None or t.sum() > exact.sum():
                    exact = t
            elif loose is None or t.sum() > loose.sum():
                loose = t
    t = exact
    if t is None or (loose is not None and min(loose.shape) >= min(t.shape) + 3):
        t = loose
    if t is None:
        raise ValueError('swastika_px.mask: no emblem for size %d' % size)
    out = np.zeros((size, size), bool)
    oy, ox = (size - t.shape[0]) // 2, (size - t.shape[1]) // 2
    out[oy:oy + t.shape[0], ox:ox + t.shape[1]] = t
    return out


def disc(w: int, h: int, cx: float, cy: float, r: float) -> np.ndarray:
    """Pixel-centre disc of radius r around (cx, cy) on an h x w canvas."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    return (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r


def pick_u(disc_d: float, ratio: float = 0.86) -> int:
    """Cell size for a disc of diameter disc_d: tip-to-tip span 5U at most `ratio` of the disc (the flag's
    white margin around the hooks)."""
    return max(2, int(math.floor(ratio * disc_d / 5.0)))


def ascii(m: np.ndarray) -> str:
    return '\n'.join(''.join('#' if v else '.' for v in row) for row in m)


if __name__ == '__main__':
    for U, corner, flip in ((2, False, False), (3, False, False), (3, True, False), (4, False, True)):
        t = tight(U, corner, flip)
        print('U=%d corner=%s flip=%s  %dx%d' % (U, corner, flip, t.shape[1], t.shape[0]))
        print(ascii(t))
        print()
    for s in (5, 7, 9, 11, 13, 15):
        print(s)
        print(ascii(mask(s)))
        print()
