"""mg_r7_kb_lib -- shared helpers of the round-7 mini-game generators gen_mg_morse.py / gen_mg_rohrpost.py
(TECHNICAL_ARCHITECTURE 12.8). Pillow + numpy only, deterministic (seeds = crc32 of names), no downloads.

* Canvas: RGBA numpy canvas with pixel / rect / line / disc helpers, ordered-dither blends, outline, paste.
* Fonts: F57 (5x7 capitals: Latin incl. AEOEUE, the full Russian alphabet, digits, punctuation) and F35 (3x5 Latin
  capitals and digits). Hand-drawn bitmaps, original work.
* save_x3(): UI art is drawn 1:1 and STORED x3 nearest (like assets/ui/minigames); save_1x(): explore close-ups
  are stored 1:1 (DiscoveryView shows them x3).
"""
from __future__ import annotations

import json
import math
import os
import zlib

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PAL = json.load(open(os.path.join(ROOT, 'data', 'palettes.json'), encoding='utf-8'))
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hx(h: str, a: int = 255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def P(area: str, ramp: str, i: int, a: int = 255):
    return hx(PAL[area][ramp][i], a)


def mix(c1, c2, t: float):
    return tuple(int(round(c1[k] + (c2[k] - c1[k]) * t)) for k in range(3)) + (int(round(c1[3] + (c2[3] - c1[3]) * t)),)


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


def bayer(x: int, y: int) -> float:
    return float(BAYER4[y % 4, x % 4])


class Canvas:
    def __init__(self, w: int, h: int, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.a[:, :] = bg

    # ---------------------------------------------------------------- primitives
    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if len(c) == 4 and c[3] < 255:
                if c[3] == 0:
                    return
                base = self.a[y, x].astype(np.float64)
                al = c[3] / 255.0
                out = base[:3] * (1 - al) + np.array(c[:3], np.float64) * al
                self.a[y, x, :3] = np.round(out).astype(np.uint8)
                self.a[y, x, 3] = max(int(base[3]), c[3])
            else:
                self.a[y, x] = c

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x])

    def rect(self, x0, y0, x1, y1, c):
        """filled, inclusive-exclusive"""
        x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(self.w, int(x1)), min(self.h, int(y1))
        if x1 > x0 and y1 > y0:
            if len(c) == 4 and c[3] < 255:
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        self.px(x, y, c)
            else:
                self.a[y0:y1, x0:x1] = c

    def frame(self, x0, y0, x1, y1, c):
        self.rect(x0, y0, x1, y0 + 1, c)
        self.rect(x0, y1 - 1, x1, y1, c)
        self.rect(x0, y0, x0 + 1, y1, c)
        self.rect(x1 - 1, y0, x1, y1, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y + 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x + 1, y1, c)

    def line(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for y in range(int(math.floor(cy - r - 1)), int(math.ceil(cy + r + 2))):
            for x in range(int(math.floor(cx - r - 1)), int(math.ceil(cx + r + 2))):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px(x, y, c)

    def ring(self, cx, cy, r0, r1, c):
        for y in range(int(math.floor(cy - r1 - 1)), int(math.ceil(cy + r1 + 2))):
            for x in range(int(math.floor(cx - r1 - 1)), int(math.ceil(cx + r1 + 2))):
                d = math.hypot(x - cx, y - cy)
                if r0 <= d <= r1:
                    self.px(x, y, c)

    def dither_rect(self, x0, y0, x1, y1, c_a, c_b, t: float):
        """ordered-dither blend of two colours with ratio t (0 = all a, 1 = all b)"""
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.px(x, y, c_b if bayer(x, y) < t else c_a)

    def vgrad(self, x0, y0, x1, y1, cols):
        """vertical dithered gradient through a list of colours"""
        n = len(cols) - 1
        hgt = max(1, y1 - y0 - 1)
        for y in range(int(y0), int(y1)):
            f = (y - y0) / hgt * n
            i = min(n - 1, int(f))
            t = f - i
            for x in range(int(x0), int(x1)):
                self.px(x, y, cols[i + 1] if bayer(x, y) < t else cols[i])

    def outline(self, c, src_alpha=1):
        """1 px outer outline around opaque pixels"""
        m = self.a[:, :, 3] >= src_alpha
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]
        o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]
        o[:, :-1] |= m[:, 1:]
        o &= ~m
        self.a[o] = c

    def paste(self, other: 'Canvas', ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.a[y, x]
                if c[3] > 0:
                    self.px(ox + x, oy + y, tuple(int(v) for v in c))

    def shade(self, x0, y0, x1, y1, k: float, mask_alpha=1):
        """multiply RGB of opaque pixels in a rect by k (k < 1 darker, > 1 lighter)"""
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                if self.a[y, x, 3] >= mask_alpha:
                    v = np.clip(self.a[y, x, :3].astype(np.float64) * k, 0, 255)
                    self.a[y, x, :3] = np.round(v).astype(np.uint8)

    def glow(self, cx, cy, r, c, strength=0.5):
        """soft additive light pool, dithered (keeps the pixel palette feel)"""
        for y in range(max(0, int(cy - r)), min(self.h, int(cy + r + 1))):
            for x in range(max(0, int(cx - r)), min(self.w, int(cx + r + 1))):
                d = math.hypot(x - cx, y - cy) / r
                if d >= 1.0 or self.a[y, x, 3] == 0:
                    continue
                t = (1.0 - d) ** 2 * strength
                if bayer(x, y) < t * 1.6:
                    base = self.a[y, x, :3].astype(np.float64)
                    out = base + (np.array(c[:3], np.float64) - base) * min(1.0, t * 1.2)
                    self.a[y, x, :3] = np.round(np.clip(out, 0, 255)).astype(np.uint8)

    # ---------------------------------------------------------------- output
    def image(self) -> Image.Image:
        return Image.fromarray(self.a, 'RGBA')


def save_x3(c: Canvas, path: str, x: int = 3):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = c.image().resize((c.w * x, c.h * x), Image.NEAREST)
    im.save(path, optimize=True)


def save_1x(c: Canvas, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c.image().save(path, optimize=True)


def save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')


# ==================================================================================== fonts (original bitmaps)
_L57 = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    'Ä': [".#.#.", ".....", ".###.", "#...#", "#####", "#...#", "#...#"],
    'Ö': [".#.#.", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    'Ü': [".#.#.", ".....", "#...#", "#...#", "#...#", "#...#", ".###."],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '.': [".", ".", ".", ".", ".", ".", "#"],
    ',': ["..", "..", "..", "..", "..", ".#", "#."],
    ':': [".", ".", "#", ".", ".", "#", "."],
    '-': ["....", "....", "....", "####", "....", "....", "...."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    '№': ["#..#.", "##.#.", "#.##.", "#..#.", "#..#.", "....#", "...##"],
}
_C57 = {
    'А': _L57['A'], 'В': _L57['B'], 'Е': _L57['E'], 'К': _L57['K'], 'М': _L57['M'], 'Н': _L57['H'],
    'О': _L57['O'], 'Р': _L57['P'], 'С': _L57['C'], 'Т': _L57['T'], 'Х': _L57['X'],
    'Б': ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'Г': ["#####", "#....", "#....", "#....", "#....", "#....", "#...."],
    'Д': [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    'Ж': ["#.#.#", "#.#.#", ".###.", "..#..", ".###.", "#.#.#", "#.#.#"],
    'З': [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    'И': ["#...#", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'Й': [".#.#.", "#.#.#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'Л': ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    'П': ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    'У': ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    'Ф': ["..#..", ".###.", "#.#.#", "#.#.#", "#.#.#", ".###.", "..#.."],
    'Ц': ["#..#.", "#..#.", "#..#.", "#..#.", "#..#.", "#####", "....#"],
    'Ч': ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    'Щ': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####", "....#"],
    'Ъ': ["##...", ".#...", ".#...", ".###.", ".#..#", ".#..#", ".###."],
    'Ы': ["#...#", "#...#", "#...#", "###.#", "#.#.#", "#.#.#", "###.#"],
    'Ь': ["#....", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'Э': [".###.", "#...#", "....#", "..###", "....#", "#...#", ".###."],
    'Ю': ["#..#.", "#.#.#", "#.#.#", "###.#", "#.#.#", "#.#.#", "#..#."],
    'Я': [".####", "#...#", "#...#", ".####", "..#.#", ".#..#", "#...#"],
}
F57 = dict(_L57)
F57.update(_C57)

F35 = {
    'A': ["###", "#.#", "###", "#.#", "#.#"], 'B': ["##.", "#.#", "##.", "#.#", "##."],
    'C': ["###", "#..", "#..", "#..", "###"], 'D': ["##.", "#.#", "#.#", "#.#", "##."],
    'E': ["###", "#..", "##.", "#..", "###"], 'F': ["###", "#..", "##.", "#..", "#.."],
    'G': ["###", "#..", "#.#", "#.#", "###"], 'H': ["#.#", "#.#", "###", "#.#", "#.#"],
    'I': ["###", ".#.", ".#.", ".#.", "###"], 'J': ["..#", "..#", "..#", "#.#", "###"],
    'K': ["#.#", "#.#", "##.", "#.#", "#.#"], 'L': ["#..", "#..", "#..", "#..", "###"],
    'M': ["#.#", "###", "###", "#.#", "#.#"], 'N': ["##.", "#.#", "#.#", "#.#", "#.#"],
    'O': ["###", "#.#", "#.#", "#.#", "###"], 'P': ["###", "#.#", "###", "#..", "#.."],
    'Q': ["###", "#.#", "#.#", "###", "..#"], 'R': ["##.", "#.#", "##.", "#.#", "#.#"],
    'S': ["###", "#..", "###", "..#", "###"], 'T': ["###", ".#.", ".#.", ".#.", ".#."],
    'U': ["#.#", "#.#", "#.#", "#.#", "###"], 'V': ["#.#", "#.#", "#.#", "#.#", ".#."],
    'W': ["#.#", "#.#", "###", "###", "#.#"], 'X': ["#.#", "#.#", ".#.", "#.#", "#.#"],
    'Y': ["#.#", "#.#", ".#.", ".#.", ".#."], 'Z': ["###", "..#", ".#.", "#..", "###"],
    'Ä': ["#.#", ".#.", "#.#", "###", "#.#"], 'Ö': ["#.#", "...", "###", "#.#", "###"],
    'Ü': ["#.#", "...", "#.#", "#.#", "###"],
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#", "##", ".#", ".#", ".#"],
    '2': ["##.", "..#", ".#.", "#..", "###"], '3': ["##.", "..#", ".#.", "..#", "##."],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "##."],
    '.': [".", ".", ".", ".", "#"], ',': ["..", "..", "..", ".#", "#."], ':': [".", "#", ".", "#", "."],
    '-': ["...", "...", "###", "...", "..."], '/': ["..#", "..#", ".#.", "#..", "#.."],
    '?': ["###", "..#", ".#.", "...", ".#."], '!': ["#", "#", "#", ".", "#"],
}


def text_width(s: str, font=F57, spacing: int = 1) -> int:
    w = 0
    space = 3 if font is F57 else 2
    for ch in s:
        if ch == ' ':
            w += space + spacing
            continue
        g = font.get(ch, font.get('?'))
        w += len(g[0]) + spacing
    return max(0, w - spacing)


def draw_text(c: Canvas, x: int, y: int, s: str, col, font=F57, spacing: int = 1, wear: float = 0.0, r=None,
              shadow=None, bold: bool = False) -> int:
    """pixel text; returns the x after the text. wear drops pixels (pencil / worn print); bold widens strokes."""
    cx = x
    space = 3 if font is F57 else 2
    for ch in s:
        if ch == ' ':
            cx += space + spacing
            continue
        g = font.get(ch, font.get('?'))
        for ry, row in enumerate(g):
            for rx, v in enumerate(row):
                if v != '#':
                    continue
                if wear and r is not None and r.random() < wear:
                    continue
                for bx in range(2 if bold else 1):
                    if shadow is not None:
                        c.px(cx + rx + bx + 1, y + ry + 1, shadow)
                    c.px(cx + rx + bx, y + ry, col)
        cx += len(g[0]) + spacing + (1 if bold else 0)
    return cx


def draw_text_centered(c: Canvas, cx: int, y: int, s: str, col, font=F57, spacing: int = 1, **kw) -> None:
    draw_text(c, cx - text_width(s, font, spacing) // 2, y, s, col, font, spacing, **kw)
