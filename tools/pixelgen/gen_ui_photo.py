"""gen_ui_photo -- original pixel-art assets of the PHOTO MODE (owner: photo-mode).

Writes (deterministic, no wall clock, seeds = crc32 of the asset names):
  * assets/ui/photo/frame_print.png   640x360 RGBA at 1:1 (one art pixel = one world pixel); PhotoMode shows it
                                      full screen at exactly x3 with nearest filtering. A 1940s deckle-edged
                                      paper print ("Buettenrand") lying on a dark album page, held by four black
                                      photo corners; transparent window for the picture.
  * assets/ui/photo/icon_camera.png   16x12 RGBA pixel camera (bellows-less 1930s/40s rangefinder) for the
                                      panel header, shown at x3.
Colours: the UI kit palette of scripts/ui/ui_kit.gd (paper ramp, night/navy, copper). Nothing is traced or
sampled; every shape is procedural.

Run:  py -3 -P tools/pixelgen/gen_ui_photo.py [--preview=<dir>]
"""
from __future__ import annotations

import os
import sys
import zlib

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'photo')

W, H = 640, 360
# picture window inside the print (1:1 px): left/top/right border 18, bottom 22
WIN = (18, 18, 622, 338)
PAGE = 3            # dark album page visible around the print
CORNER = 26         # leg of the photo-corner triangles


def hx(s: str) -> np.ndarray:
    s = s.lstrip('#')
    return np.array([int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255], np.int16)


PAPER_L = hx('f5efda')
PAPER = hx('e6dec2')
PAPER_M = hx('cec6aa')
PAPER_D = hx('b0aa93')
FOX = hx('ba9a74')       # foxing (age spots), between copper and paper
NIGHT = hx('04090d')
NIGHT1 = hx('06151d')
NAVY_L = hx('14272b')
WALL = hx('354448')


def rng(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode('utf-8')))


def bayer4() -> np.ndarray:
    b = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)
    return (b + 0.5) / 16.0


def smooth_noise(r: np.random.Generator, n: int, step: int) -> np.ndarray:
    """1D value noise of length n, knots every `step` px, cosine-interpolated, range -1..1."""
    knots = r.uniform(-1.0, 1.0, n // step + 3)
    x = np.arange(n) / step
    i = x.astype(int)
    f = x - i
    f = (1 - np.cos(f * np.pi)) * 0.5
    return knots[i] * (1 - f) + knots[i + 1] * f


def frame_print() -> np.ndarray:
    r = rng('photo_frame_print')
    img = np.zeros((H, W, 4), np.int16)
    yy, xx = np.mgrid[0:H, 0:W]
    th = np.tile(bayer4(), (H // 4 + 1, W // 4 + 1))[:H, :W]

    # --- album page (dark, slightly lighter cardboard fibres)
    img[:, :] = NIGHT1
    fib = r.random((H, W)) < 0.05
    img[fib] = NAVY_L

    # --- print outline with deckled (scalloped, torn) outer edge
    left = PAGE + 1 + np.round(1.5 * smooth_noise(r, H, 3) + 0.8 * smooth_noise(r, H, 7)).astype(int)
    right = W - 1 - PAGE - 1 - np.round(1.5 * smooth_noise(r, H, 3) + 0.8 * smooth_noise(r, H, 7)).astype(int)
    top = PAGE + 1 + np.round(1.2 * smooth_noise(r, W, 3) + 0.8 * smooth_noise(r, W, 7)).astype(int)
    bot = H - 1 - PAGE - 1 - np.round(1.2 * smooth_noise(r, W, 3) + 0.8 * smooth_noise(r, W, 7)).astype(int)
    paper = (xx >= left[yy]) & (xx <= right[yy]) & (yy >= top[xx]) & (yy <= bot[xx])

    # paper tone: warm cream, yellowing towards the outer edge, fibre dither, a few foxing spots
    dx = np.minimum(xx - left[yy], right[yy] - xx).astype(np.float32)
    dy = np.minimum(yy - top[xx], bot[xx] - yy).astype(np.float32)
    edge = np.clip(1.0 - np.minimum(dx, dy) / 4.0, 0.0, 1.0)
    grain = r.random((H, W)).astype(np.float32)
    col = np.broadcast_to(PAPER, (H, W, 4)).copy()
    # sparse paper fibres: short horizontal streaks of the mid tone, a few bright flecks
    streak = (r.random((H, W)) < 0.035)
    streak = streak | np.roll(streak, 1, axis=1) & (r.random((H, W)) < 0.6)
    col[streak] = PAPER_M
    col[(grain < 0.02)] = PAPER_L
    # yellowed rim along the deckle (ordered dither, 1..3 px deep)
    col[(edge > th * 0.85 + 0.1)] = PAPER_M
    col[(edge > 0.9) & (th > 0.5)] = PAPER_D
    img[paper] = col[paper]
    # foxing: small irregular brownish spots, only on the border
    for _ in range(26):
        cx, cy = int(r.integers(6, W - 6)), int(r.integers(6, H - 6))
        if WIN[0] - 2 < cx < WIN[2] + 2 and WIN[1] - 2 < cy < WIN[3] + 2:
            continue
        rad = r.uniform(0.6, 1.8)
        m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad) & paper
        img[m] = FOX if rad > 1.2 else PAPER_D

    # torn-edge shadow on the album page (1 px right/below the deckle)
    sh = np.zeros_like(paper)
    sh[1:, 1:] = paper[:-1, :-1]
    shadow = sh & ~paper
    img[shadow] = NIGHT

    # --- picture window (transparent) with a thin emulsion edge + a paper bevel on top/left
    x0, y0, x1, y1 = WIN
    win = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    rim = (xx >= x0 - 1) & (xx < x1 + 1) & (yy >= y0 - 1) & (yy < y1 + 1) & ~win
    img[rim] = WALL
    bevel = ((yy == y0 - 2) & (xx >= x0 - 2) & (xx <= x1)) | ((xx == x0 - 2) & (yy >= y0 - 2) & (yy <= y1))
    img[bevel & paper] = PAPER_D
    img[win] = 0

    # --- black photo corners (album mounts) over the four print corners
    def corner(cx: int, cy: int, sx: int, sy: int) -> None:
        for j in range(CORNER + 1):
            for i in range(CORNER + 1 - j):
                x, y = cx + sx * i, cy + sy * j
                if 0 <= x < W and 0 <= y < H:
                    on_hyp = i + j >= CORNER - 1
                    img[y, x] = NAVY_L if on_hyp else NIGHT
        # small paper-pocket gloss line one px inside the hypotenuse
        for i in range(3, CORNER - 4):
            x, y = cx + sx * i, cy + sy * (CORNER - 3 - i)
            if 0 <= x < W and 0 <= y < H and (i % 3) != 0:
                img[y, x] = WALL

    corner(PAGE, PAGE, 1, 1)
    corner(W - 1 - PAGE, PAGE, -1, 1)
    corner(PAGE, H - 1 - PAGE, 1, -1)
    corner(W - 1 - PAGE, H - 1 - PAGE, -1, -1)
    return np.clip(img, 0, 255).astype(np.uint8)


def icon_camera() -> np.ndarray:
    # 16x12, 1:1. '.' clear, k night outline, b wall body, l navy-light leatherette, c copper, a amber, g lens glass
    rows = [
        "....kkkk...kkk..",
        "...kccck..kaak..",
        ".kkkkkkkkkkkkkk.",
        "kbbbbbbbbbbbbbbk",
        "kbllllkkkkllllbk",
        "kbllkkgggkklllbk",
        "kbllkggaggklllbk",
        "kbllkgggggklllbk",
        "kbllkkgggkklllbk",
        "kbllllkkkkllllbk",
        "kbbbbbbbbbbbbbbk",
        ".kkkkkkkkkkkkkk.",
    ]
    pal = {'.': np.array([0, 0, 0, 0], np.int16), 'k': NIGHT, 'b': WALL, 'l': NAVY_L, 'c': hx('ba775b'),
           'a': hx('f0c487'), 'g': hx('3e546b')}
    img = np.zeros((12, 16, 4), np.int16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            img[y, x] = pal[ch]
    return np.clip(img, 0, 255).astype(np.uint8)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    fp = frame_print()
    Image.fromarray(fp, 'RGBA').save(os.path.join(OUT, 'frame_print.png'))
    ic = icon_camera()
    Image.fromarray(ic, 'RGBA').resize((48, 36), Image.NEAREST).save(os.path.join(OUT, 'icon_camera.png'))
    print('wrote', os.path.join(OUT, 'frame_print.png'), fp.shape, 'and icon_camera.png (x3)')
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            d = a.split('=', 1)[1]
            os.makedirs(d, exist_ok=True)
            bg = np.zeros((H, W, 4), np.uint8)
            bg[..., 0] = (np.arange(W) * 200 // W)[None, :]
            bg[..., 1] = 90
            bg[..., 2] = (np.arange(H) * 200 // H)[:, None]
            bg[..., 3] = 255
            comp = Image.alpha_composite(Image.fromarray(bg, 'RGBA'), Image.fromarray(fp, 'RGBA'))
            comp.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(d, 'frame_print_preview.png'))
            comp.crop((0, 0, 120, 70)).resize((480, 280), Image.NEAREST).save(os.path.join(d, 'frame_print_corner.png'))
            print('preview in', d)


if __name__ == '__main__':
    main()
