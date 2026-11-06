"""mg_r7_v_kit -- shared helpers of the two Chapter-3 mini-game art generators (owner: minigames r7, Veltrava).

Used by tools/pixelgen/gen_mg_flap.py (Bahnhof Veltrava, "Die Fallblatttafel") and gen_mg_cloak.py (Palais,
"Die Garderobe"). Nothing here writes files by itself.

  * palettes: data/chapters/c3.json "veltrava" (station) and "palais" (palace); every colour the generators use
    is a palette entry or a documented mix of two entries (mix())
  * Cv: a float RGBA canvas (numpy) with px / rect / line / poly / ellipse / outline / dither helpers
  * three hand-made bitmap fonts (original, drawn for this game -- no font file is read or traced):
      BIG   7x11 bold condensed capitals + digits (split-flap faces)
      SMALL 5x7 capitals, digits, punctuation and the Cyrillic letters the station signs need
      TINY  3x5 (variable width) capitals and digits for world-scale boards, brass plates and tokens
Deterministic: no clocks, no randomness except numpy generators seeded with crc32 of a name.
"""
from __future__ import annotations

import json
import os
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
_C3 = json.load(open(os.path.join(ROOT, 'data', 'chapters', 'c3.json'), encoding='utf-8'))
PALETTES = _C3['palettes']
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hx(h: str, a: int = 255) -> np.ndarray:
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], np.float64)


def pal(name: str):
    """Returns C(ramp, i, a=255) for palette `name` (veltrava | palais)."""
    p = PALETTES[name]

    def C(ramp: str, i: int, a: int = 255) -> np.ndarray:
        return hx(p[ramp][i], a)
    return C


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Documented blend of two palette colours (alpha of `a`)."""
    out = a * (1.0 - t) + b * t
    out[3] = a[3]
    return np.round(out)


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


class Cv:
    def __init__(self, w: int, h: int):
        self.w, self.h = int(w), int(h)
        self.a = np.zeros((self.h, self.w, 4), np.float64)

    def blend(self, x: int, y: int, c, alpha: float = 1.0) -> None:
        a = (float(c[3]) / 255.0) * alpha
        if a <= 0.0:
            return
        dst = self.a[y, x]
        if a >= 0.999 or dst[3] == 0:
            self.a[y, x] = [c[0], c[1], c[2], max(dst[3], a * 255) if dst[3] > 0 else a * 255]
            return
        self.a[y, x, :3] = dst[:3] * (1 - a) + np.asarray(c[:3], np.float64) * a
        self.a[y, x, 3] = max(dst[3], a * 255)

    def px(self, x, y, c, alpha: float = 1.0) -> None:
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.blend(x, y, c, alpha)

    def get(self, x: int, y: int) -> np.ndarray:
        return self.a[y, x].copy()

    def rect(self, x0, y0, x1, y1, c, alpha: float = 1.0) -> None:
        """Half-open [x0, x1) x [y0, y1)."""
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.blend(x, y, c, alpha)

    def frame(self, x0, y0, x1, y1, c, alpha: float = 1.0) -> None:
        """1-px outline of [x0, x1) x [y0, y1)."""
        self.rect(x0, y0, x1, y0 + 1, c, alpha)
        self.rect(x0, y1 - 1, x1, y1, c, alpha)
        self.rect(x0, y0 + 1, x0 + 1, y1 - 1, c, alpha)
        self.rect(x1 - 1, y0 + 1, x1, y1 - 1, c, alpha)

    def line(self, x0, y0, x1, y1, c, alpha: float = 1.0) -> None:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, alpha)

    def poly(self, pts, c, alpha: float = 1.0) -> None:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(self.w, int(max(xs)) + 1)):
                if inside(x + 0.5, y + 0.5, pts):
                    self.blend(x, y, c, alpha)

    def ellipse(self, cx, cy, rx, ry, c, alpha: float = 1.0) -> None:
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / max(0.01, rx)) ** 2 + ((y + 0.5 - cy) / max(0.01, ry)) ** 2 <= 1.0:
                    self.px(x, y, c, alpha)

    def dither_rect(self, x0, y0, x1, y1, c, amount: float, alpha: float = 1.0) -> None:
        """Ordered-dither `c` over the rect with coverage `amount` (0..1)."""
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                if BAYER[y % 4, x % 4] < amount:
                    self.blend(x, y, c, alpha)

    def vgrad(self, x0, y0, x1, y1, c_top, c_bot) -> None:
        """Vertical two-colour gradient made of ordered dither (no new colours)."""
        h = max(1, int(y1) - int(y0))
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            t = (y - int(y0)) / max(1, h - 1)
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.blend(x, y, c_bot if BAYER[y % 4, x % 4] < t else c_top)

    def outline(self, c) -> None:
        m = self.a[:, :, 3] > 0
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]
        o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]
        o[:, :-1] |= m[:, 1:]
        o &= ~m
        self.a[o] = c

    def paste(self, other: 'Cv', x: int, y: int) -> None:
        for yy in range(other.h):
            for xx in range(other.w):
                c = other.a[yy, xx]
                if c[3] > 0:
                    self.px(x + xx, y + yy, c)

    def binarize_alpha(self) -> None:
        self.a[:, :, 3] = np.where(self.a[:, :, 3] >= 128, 255, 0)

    def img(self) -> Image.Image:
        return Image.fromarray(np.clip(np.round(self.a), 0, 255).astype(np.uint8), 'RGBA')

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.binarize_alpha()
        self.img().save(path, optimize=False)
        return path


def inside(x, y, pts) -> bool:
    n, j, r = len(pts), len(pts) - 1, False
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            r = not r
        j = i
    return r


# ============================================================================ fonts (hand-made bitmaps)
def _g(rows: str):
    return [r for r in rows.split()]


BIG = {
    'A': _g('..###.. .##.##. ##...## ##...## ##...## ##...## ####### ##...## ##...## ##...## ##...##'),
    'B': _g('######. ##...## ##...## ##...## ######. ##...## ##...## ##...## ##...## ##...## ######.'),
    'C': _g('.#####. ##...## ##..... ##..... ##..... ##..... ##..... ##..... ##..... ##...## .#####.'),
    'D': _g('#####.. ##..##. ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##..##. #####..'),
    'E': _g('####### ##..... ##..... ##..... ######. ##..... ##..... ##..... ##..... ##..... #######'),
    'F': _g('####### ##..... ##..... ##..... ######. ##..... ##..... ##..... ##..... ##..... ##.....'),
    'G': _g('.#####. ##...## ##..... ##..... ##..... ##.#### ##...## ##...## ##...## ##...## .#####.'),
    'H': _g('##...## ##...## ##...## ##...## ####### ##...## ##...## ##...## ##...## ##...## ##...##'),
    'I': _g('.#####. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. .#####.'),
    'J': _g('....##. ....##. ....##. ....##. ....##. ....##. ....##. ##..##. ##..##. ##..##. .####..'),
    'K': _g('##...## ##..##. ##.##.. ####... ###.... ###.... ####... ##.##.. ##..##. ##...## ##...##'),
    'L': _g('##..... ##..... ##..... ##..... ##..... ##..... ##..... ##..... ##..... ##..... #######'),
    'M': _g('##...## ###.### ####### ##.#.## ##.#.## ##...## ##...## ##...## ##...## ##...## ##...##'),
    'N': _g('##...## ##...## ###..## ###..## ##.#.## ##.#.## ##..### ##..### ##...## ##...## ##...##'),
    'O': _g('.#####. ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## .#####.'),
    'P': _g('######. ##...## ##...## ##...## ##...## ######. ##..... ##..... ##..... ##..... ##.....'),
    'R': _g('######. ##...## ##...## ##...## ##...## ######. ##.##.. ##..##. ##..##. ##...## ##...##'),
    'S': _g('.#####. ##...## ##..... ##..... .#####. .....## .....## .....## .....## ##...## .#####.'),
    'T': _g('####### ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###.. ..###..'),
    'U': _g('##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## .#####.'),
    'V': _g('##...## ##...## ##...## ##...## ##...## ##...## ##...## .##.##. .##.##. ..###.. ...#...'),
    'W': _g('##...## ##...## ##...## ##...## ##...## ##.#.## ##.#.## ####### ###.### ##...## #.....#'),
    'X': _g('##...## ##...## .##.##. .##.##. ..###.. ..###.. .##.##. .##.##. ##...## ##...## ##...##'),
    'Y': _g('##...## ##...## ##...## .##.##. .##.##. ..###.. ..###.. ..###.. ..###.. ..###.. ..###..'),
    'Z': _g('####### .....## ....##. ....##. ...##.. ..###.. ..##... .##.... .##.... ##..... #######'),
    'Ü': _g('.##.##. ....... ##...## ##...## ##...## ##...## ##...## ##...## ##...## ##...## .#####.'),
    '0': _g('.#####. ##...## ##...## ##..### ##.#.## ##.#.## ###..## ##...## ##...## ##...## .#####.'),
    '1': _g('...##.. ..###.. .####.. ...##.. ...##.. ...##.. ...##.. ...##.. ...##.. ...##.. ..####.'),
    '2': _g('.#####. ##...## .....## .....## ....##. ...##.. ..##... .##.... ##..... ##..... #######'),
    '3': _g('.#####. ##...## .....## .....## ..####. .....## .....## .....## .....## ##...## .#####.'),
    '4': _g('....##. ...###. ..####. .##.##. ##..##. ##..##. ####### ....##. ....##. ....##. ....##.'),
    '5': _g('####### ##..... ##..... ##..... ######. .....## .....## .....## .....## ##...## .#####.'),
    '6': _g('.#####. ##...## ##..... ##..... ######. ##...## ##...## ##...## ##...## ##...## .#####.'),
    '7': _g('####### .....## .....## ....##. ....##. ...##.. ...##.. ..##... ..##... ..##... ..##...'),
    '8': _g('.#####. ##...## ##...## ##...## .#####. ##...## ##...## ##...## ##...## ##...## .#####.'),
    '9': _g('.#####. ##...## ##...## ##...## ##...## .###### .....## .....## .....## ##...## .#####.'),
    '-': _g('....... ....... ....... ....... ....... .#####. ....... ....... ....... ....... .......'),
    ' ': _g('....... ....... ....... ....... ....... ....... ....... ....... ....... ....... .......'),
}

SMALL = {
    'A': _g('.###. #...# #...# ##### #...# #...# #...#'),
    'B': _g('####. #...# #...# ####. #...# #...# ####.'),
    'C': _g('.###. #...# #.... #.... #.... #...# .###.'),
    'D': _g('####. #...# #...# #...# #...# #...# ####.'),
    'E': _g('##### #.... #.... ####. #.... #.... #####'),
    'F': _g('##### #.... #.... ####. #.... #.... #....'),
    'G': _g('.###. #...# #.... #.### #...# #...# .###.'),
    'H': _g('#...# #...# #...# ##### #...# #...# #...#'),
    'I': _g('.###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.'),
    'J': _g('..### ...#. ...#. ...#. ...#. #..#. .##..'),
    'K': _g('#...# #..#. #.#.. ##... #.#.. #..#. #...#'),
    'L': _g('#.... #.... #.... #.... #.... #.... #####'),
    'M': _g('#...# ##.## #.#.# #.#.# #...# #...# #...#'),
    'N': _g('#...# ##..# #.#.# #..## #...# #...# #...#'),
    'O': _g('.###. #...# #...# #...# #...# #...# .###.'),
    'P': _g('####. #...# #...# ####. #.... #.... #....'),
    'R': _g('####. #...# #...# ####. #.#.. #..#. #...#'),
    'S': _g('.#### #.... #.... .###. ....# ....# ####.'),
    'T': _g('##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..'),
    'U': _g('#...# #...# #...# #...# #...# #...# .###.'),
    'V': _g('#...# #...# #...# #...# #...# .#.#. ..#..'),
    'W': _g('#...# #...# #...# #.#.# #.#.# #.#.# .#.#.'),
    'X': _g('#...# #...# .#.#. ..#.. .#.#. #...# #...#'),
    'Y': _g('#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..'),
    'Z': _g('##### ....# ...#. ..#.. .#... #.... #####'),
    'Ü': _g('.#.#. ..... #...# #...# #...# #...# .###.'),
    'Ä': _g('.#.#. ..... .###. #...# ##### #...# #...#'),
    'Ö': _g('.#.#. ..... .###. #...# #...# #...# .###.'),
    'É': _g('...#. ..#.. ##### #.... ####. #.... #####'),
    '0': _g('.###. #...# #..## #.#.# ##..# #...# .###.'),
    '1': _g('..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.'),
    '2': _g('.###. #...# ....# ...#. ..#.. .#... #####'),
    '3': _g('####. ....# ....# .###. ....# ....# ####.'),
    '4': _g('...#. ..##. .#.#. #..#. ##### ...#. ...#.'),
    '5': _g('##### #.... ####. ....# ....# #...# .###.'),
    '6': _g('.###. #.... #.... ####. #...# #...# .###.'),
    '7': _g('##### ....# ...#. ..#.. .#... .#... .#...'),
    '8': _g('.###. #...# #...# .###. #...# #...# .###.'),
    '9': _g('.###. #...# #...# .#### ....# ....# .###.'),
    ':': _g('. # # . # # .'),
    '.': _g('.. .. .. .. .. ## ##'),
    '·': _g('... ... ... .#. ... ... ...'),
    '-': _g('.... .... .... #### .... .... ....'),
    '/': _g('....# ...#. ...#. ..#.. .#... .#... #....'),
    ' ': _g('... ... ... ... ... ... ...'),
    'П': _g('##### #...# #...# #...# #...# #...# #...#'),
    'Р': _g('####. #...# #...# ####. #.... #.... #....'),
    'И': _g('#...# #..## #.#.# ##..# #...# #...# #...#'),
    'Б': _g('##### #.... #.... ####. #...# #...# ####.'),
    'Ы': _g('#...# #...# #...# ##..# #.#.# #.#.# ##..#'),
    'Т': _g('##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..'),
    'Е': _g('##### #.... #.... ####. #.... #.... #####'),
    'У': _g('#...# #...# #...# .#### ....# ....# .###.'),
    'Ь': _g('#.... #.... #.... ####. #...# #...# ####.'),
    'Д': _g('.###. .#.#. .#.#. .#.#. .#.#. ##### #...#'),
    'З': _g('.###. #...# ....# ..##. ....# #...# .###.'),
    'Ч': _g('#...# #...# #...# .#### ....# ....# ....#'),
    'Л': _g('..### .#..# .#..# .#..# .#..# .#..# #...#'),
    'Г': _g('##### #.... #.... #.... #.... #.... #....'),
    'О': _g('.###. #...# #...# #...# #...# #...# .###.'),
    'К': _g('#...# #..#. #.#.. ##... #.#.. #..#. #...#'),
    'А': _g('.###. #...# #...# ##### #...# #...# #...#'),
    'В': _g('####. #...# #...# ####. #...# #...# ####.'),
    'С': _g('.###. #...# #.... #.... #.... #...# .###.'),
    'Н': _g('#...# #...# #...# ##### #...# #...# #...#'),
    'М': _g('#...# ##.## #.#.# #.#.# #...# #...# #...#'),
}

TINY = {
    'A': _g('.#. #.# ### #.# #.#'), 'B': _g('##. #.# ##. #.# ##.'), 'C': _g('.## #.. #.. #.. .##'),
    'D': _g('##. #.# #.# #.# ##.'), 'E': _g('### #.. ##. #.. ###'), 'F': _g('### #.. ##. #.. #..'),
    'G': _g('.## #.. #.# #.# .##'), 'H': _g('#.# #.# ### #.# #.#'), 'I': _g('### .#. .#. .#. ###'),
    'K': _g('#.# #.# ##. #.# #.#'), 'L': _g('#.. #.. #.. #.. ###'), 'M': _g('#...# ##.## #.#.# #...# #...#'),
    'N': _g('#..# ##.# #.## #..# #..#'), 'O': _g('.#. #.# #.# #.# .#.'), 'P': _g('##. #.# ##. #.. #..'),
    'R': _g('##. #.# ##. #.# #.#'), 'S': _g('.## #.. .#. ..# ##.'), 'T': _g('### .#. .#. .#. .#.'),
    'U': _g('#.# #.# #.# #.# ###'), 'V': _g('#.# #.# #.# #.# .#.'), 'W': _g('#...# #...# #.#.# ##.## #...#'),
    'Z': _g('### ..# .#. #.. ###'), 'Ü': _g('#.# ... #.# #.# ###'), 'É': _g('.#. ### ##. #.. ###'),
    '0': _g('### #.# #.# #.# ###'), '1': _g('.#. ##. .#. .#. ###'), '2': _g('##. ..# .#. #.. ###'),
    '3': _g('##. ..# .#. ..# ##.'), '4': _g('#.# #.# ### ..# ..#'), '5': _g('### #.. ##. ..# ##.'),
    '6': _g('.## #.. ### #.# ###'), '7': _g('### ..# .#. .#. .#.'), '8': _g('### #.# ### #.# ###'),
    '9': _g('### #.# ### ..# ##.'), ':': _g('. # . # .'), '.': _g('. . . . #'), '-': _g('.. .. ## .. ..'),
    '·': _g('. . # . .'), ' ': _g('.. .. .. .. ..'), '/': _g('..# ..# .#. #.. #..'),
    'П': _g('### #.# #.# #.# #.#'), 'Р': _g('##. #.# ##. #.. #..'), 'И': _g('#..# #.## ##.# #..# #..#'),
    'Б': _g('### #.. ##. #.# ##.'), 'Ы': _g('#..# #..# ##.# #.## ##.#'), 'Т': _g('### .#. .#. .#. .#.'),
    'Е': _g('### #.. ##. #.. ###'), 'О': _g('.#. #.# #.# #.# .#.'),
}

FONTS = {'big': (BIG, 2, 11), 'small': (SMALL, 1, 7), 'tiny': (TINY, 1, 5)}


def glyph(font: str, ch: str):
    table = FONTS[font][0]
    return table.get(ch, table.get(ch.upper(), table[' ']))


def text_width(s: str, font: str = 'small') -> int:
    table, gap, _h = FONTS[font]
    w = 0
    for i, ch in enumerate(s):
        w += len(glyph(font, ch)[0]) + (gap if i < len(s) - 1 else 0)
    return w


def text(cv: Cv, x: int, y: int, s: str, c, font: str = 'small', alpha: float = 1.0, cell: int = 0) -> int:
    """Draws `s` at (x, y) (top-left); `cell` > 0 = monospace advance. Returns the end x."""
    table, gap, _h = FONTS[font]
    cx = int(x)
    for ch in s:
        g = glyph(font, ch)
        gw = len(g[0])
        ox = cx + ((cell - gw) // 2 if cell > 0 else 0)
        for yy, row in enumerate(g):
            for xx, v in enumerate(row):
                if v == '#':
                    cv.px(ox + xx, y + yy, c, alpha)
        cx += cell if cell > 0 else gw + gap
    return cx


def write_json(path: str, data) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write('\n')
    return path
