"""gen_minigame_plaza -- art for the plaza mini-game "Das Blatt im Schnee" (owner: plaza-polish, §12.8).

    py -3 -P tools/pixelgen/gen_minigame_plaza.py          (then import under the shared lock)

Writes assets/ui/minigames/plaza/ at 1:1 art pixels (the game draws the whole scene x3, nearest):
  leaflet_back.png     300x124  parade evening: snow cloud sky with searchlight shafts, the hall's colonnade,
                                avenue snow, the strip behind the barrier and the pavement lane in front of it
  leaflet_march.png    300x30   tileable strip of the marching column (scrolls slowly behind the posts)
  leaflet_barrier.png  300x24   red-white trestle boards, sagging chains, small sign boards (over the posts' legs)
  leaflet_front.png    300x124  foreground crowd at both edges (backs, hats, shoulders; drawn last)
  leaflet_bend.png     3 x 40x56  Konrad stooping (16/31/46 deg). Derived read-only from
                                assets/characters/konrad/sheet.png idle_side frame 0 (upper body rotated about the
                                hip, RotSprite-style x8 nearest); re-run this script when that sheet changes
  leaflet_sheet.png    3 x 12x8   the typed sheet in the snow: flat / corner lifted / fluttering
  world_leaflet.png    2 x 8x6    the same sheet as a world cue in the plaza snow (two flutter frames)
  leaflet_layout.json  lane, rows and the posts' spots (art px) for scripts/ui/minigames/leaflet_game.gd
Deterministic (seeds = crc32 of names). Colours: data/palettes.json "berlin" plus the barrier's faded red.
No insignia anywhere; the marching column is a rhythm of helmets and rifles, nothing more.
"""
from __future__ import annotations

import json
import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'minigames', 'plaza')
PAL = json.load(open(os.path.join(ROOT, 'data', 'palettes.json'), encoding='utf-8'))['berlin']
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
W, H = 300, 124
LANE = (40, 260)          # Konrad's walkable x range (logic 0..1)
FEET_Y = 114              # Konrad's feet
SHEET_Y = 113             # the sheet's ground line
GUARDS = [(92, 80), (212, 80)]
BARRIER_Y = 62
MARCH_Y = 40


def hx(h: str, a: int = 255):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], np.float64)


def C(ramp: str, i: int, a: int = 255):
    return hx(PAL[ramp][i], a)


RED = [hx('#4a2226'), hx('#6e2e2c'), hx('#8d3b33'), hx('#a8503d')]   # faded barrier red (dark -> light)


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float64)

    def px(self, x, y, c, alpha=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.blend(x, y, c, alpha)

    def blend(self, x, y, c, alpha=1.0):
        a = (c[3] / 255.0) * alpha
        dst = self.a[y, x]
        if a >= 0.999 or dst[3] == 0:
            if a > 0:
                self.a[y, x] = [c[0], c[1], c[2], max(dst[3], a * 255)] if dst[3] > 0 else [c[0], c[1], c[2], a * 255]
            return
        self.a[y, x, :3] = dst[:3] * (1 - a) + np.asarray(c[:3]) * a
        self.a[y, x, 3] = max(dst[3], a * 255)

    def rect(self, x0, y0, x1, y1, c, alpha=1.0):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.blend(x, y, c, alpha)

    def line(self, x0, y0, x1, y1, c, alpha=1.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, alpha)

    def poly(self, pts, c, alpha=1.0):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(self.w, int(max(xs)) + 1)):
                if inside(x + 0.5, y + 0.5, pts):
                    self.blend(x, y, c, alpha)

    def ellipse(self, cx, cy, rx, ry, c, alpha=1.0):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c, alpha)

    def outline(self, c):
        m = self.a[:, :, 3] > 0
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]
        o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]
        o[:, :-1] |= m[:, 1:]
        o &= ~m
        self.a[o] = c

    def img(self):
        return Image.fromarray(np.clip(np.round(self.a), 0, 255).astype(np.uint8), 'RGBA')


def inside(x, y, pts):
    n, j, r = len(pts), len(pts) - 1, False
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            r = not r
        j = i
    return r


def dither_ramp(cv: Cv, x0, y0, x1, y1, cols, f):
    """Fill with a ramp: f(x, y) in 0..len(cols)-1, ordered (Bayer) dithering between neighbours."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = min(len(cols) - 1.0001, max(0.0, f(x, y)))
            i = int(v)
            fr = v - i
            k = i + 1 if fr > BAYER[y % 4, x % 4] else i
            cv.a[y, x] = cols[min(k, len(cols) - 1)]


def save(cv_or_img, name):
    os.makedirs(OUT, exist_ok=True)
    im = cv_or_img.img() if isinstance(cv_or_img, Cv) else cv_or_img
    im.save(os.path.join(OUT, name), optimize=True)
    print('wrote', name, im.size)


# ===================================================================================== backdrop
def back():
    cv = Cv(W, H)
    r = rng('leaflet.back')
    sky = [C('night', 0), C('night', 1), C('night', 3), C('violet', 0), C('violet', 1), C('violet', 2)]
    dither_ramp(cv, 0, 0, W, 64, sky, lambda x, y: 0.4 + y / 64.0 * 4.6 + 0.35 * math.sin(x * 0.05 + y * 0.11))
    # searchlight shafts of the Lichtdom (pale, leaning), drawn before the colonnade
    for k, (xb, lean) in enumerate(((46, -16), (128, 6), (196, 14), (268, 22))):
        for y in range(0, 40):
            t = y / 40.0
            cx = xb + lean * (1 - t)
            half = 1.5 + 2.5 * (1 - t)
            for x in range(int(cx - half), int(cx + half) + 1):
                a = 0.10 + 0.16 * t
                cv.px(x, y, C('snow', 1), a)
    # the colonnade of the hall far behind: cornice, pillars, dark gaps with a few lit doors
    cv.rect(0, 12, W, 15, C('violet', 1))
    cv.rect(0, 15, W, 16, C('night', 3))
    for x in range(-6, W, 19):
        cv.rect(x, 16, x + 9, 44, C('violet', 1))
        cv.rect(x, 16, x + 2, 44, C('violet', 2))          # floodlit edge
        cv.rect(x + 8, 16, x + 9, 44, C('night', 3))
        for y in range(18, 44, 3):                          # fluting
            cv.px(x + 5, y, C('violet', 0))
    for x in (29, 105, 181, 257):
        cv.rect(x + 1, 30, x + 7, 44, C('ochre', 0), 0.55)  # far lit doorways
    cv.rect(0, 40, W, 44, C('night', 2))                    # plinth shadow
    # avenue snow band behind the posts (trampled, in shadow) and the ground strip at the barrier
    av = [C('snow', 0), C('violet', 3), C('snow', 1)]
    dither_ramp(cv, 0, 44, W, 86, av, lambda x, y: min(1.0, max(0.0, (y - 62 + math.sin(x * 0.21)) / 5.0))
                + min(1.0, max(0.0, (y - 77 + math.sin(x * 0.17)) / 4.0)))
    for _ in range(140):                                    # boot-trodden ruts
        x, y = int(r.integers(0, W)), int(r.integers(46, 84))
        cv.px(x, y, C('violet', 2), 0.7)
    # the pavement lane: snowy cobbles, trodden darker in the middle, footprints, the kerb at the bottom
    lane = [C('snow', 0), C('snow', 1), C('snow', 2), C('snow', 3)]
    dither_ramp(cv, 0, 86, W, H, lane, lambda x, y: 2.0 + min(0.999, max(0.0, (y - 113) / 3.0))
                - min(1.0, max(0.0, 1.0 - (abs(y - 106 - 1.5 * math.sin(x * 0.05)) - 4.0) / 2.0))
                - (1.0 if y < 88 else 0.0))
    for y in range(92, 120, 5):                             # cobble joints peeking through
        off = (y // 5) % 2 * 4
        for x in range(off, W, 8):
            if r.random() < 0.45:
                cv.px(x, y, C('snow', 1), 0.8)
                cv.px(x + 1, y, C('snow', 1), 0.5)
    for _ in range(46):                                     # footprints (pairs)
        x, y = int(r.integers(4, W - 8)), int(r.integers(96, 118))
        cv.px(x, y, C('snow', 0)); cv.px(x + 1, y, C('snow', 0), 0.6)
        cv.px(x + 4, y + 2, C('snow', 0)); cv.px(x + 5, y + 2, C('snow', 0), 0.6)
    cv.rect(0, 119, W, 120, C('violet', 2))                 # kerb
    cv.rect(0, 120, W, H, C('violet', 1))
    # cold evening light: lamp glow from the left, floodlight wash from the right
    for y in range(86, H):
        for x in range(W):
            g = math.exp(-((x - 20) / 70.0) ** 2) * 0.16 + math.exp(-((x - 280) / 90.0) ** 2) * 0.08
            if g > 0.01:
                cv.blend(x, y, C('glow', 1), g)
    save(cv, 'leaflet_back.png')


def march():
    """Tileable 300x30 strip: three ranks of marching soldiers seen over the barrier (helmets, rifles)."""
    cv = Cv(W, 30)
    r = rng('leaflet.march')
    for rank, (y0, tone, step) in enumerate(((6, 0, 10), (9, 1, 10), (12, 1, 10))):
        for x in range(rank * 3, W, step):
            body = C('steel', tone) if rank else C('night', 3)
            cv.rect(x, y0 + 4, x + 6, 30, body)              # greatcoat
            cv.ellipse(x + 3, y0 + 2, 3.2, 2.4, C('steel', tone + 1))   # helmet
            cv.rect(x, y0 + 3, x + 7, y0 + 4, C('steel', tone))         # helmet brim
            cv.px(x + 2, y0 + 1, C('steel', tone + 2))
            cv.line(x + 6, y0 - 4, x + 6, y0 + 10, C('steel', 0))      # rifle on the shoulder
            cv.rect(x + 1, y0 + 4, x + 5, y0 + 6, C('skin', 0), 0.35)   # face in shadow
    for x in range(0, W, 100):                               # a plain standard pole, no emblem
        cv.line(x + 47, 0, x + 47, 30, C('stone', 1))
        cv.rect(x + 43, 0, x + 52, 2, C('stone', 2))
    a = cv.a
    a[:, :, :3] *= 0.86                                       # haze: the column is far behind the posts
    save(cv, 'leaflet_march.png')


def barrier():
    cv = Cv(W, 24)
    boards = list(range(-14, W + 40, 50))
    for k, xc in enumerate(boards):
        # X legs
        for (xa, xb) in ((xc - 14, xc - 6), (xc + 14, xc + 6)):
            pass
        for sx in (-1, 1):
            for lx in (xc - 15, xc + 15):
                cv.line(lx - 5 * sx, 22, lx + 4 * sx, 6, C('stone', 0))
        # the board, striped red/white in 6 px fields, a darker lower edge, snow on top
        x0, x1 = xc - 21, xc + 21
        for x in range(x0, x1):
            red = ((x - x0) // 6) % 2 == 0
            col = RED[2] if red else C('snow', 3)
            dark = RED[1] if red else C('snow', 1)
            cv.rect(x, 3, x + 1, 7, col)
            cv.rect(x, 7, x + 1, 8, dark)
        cv.rect(x0, 2, x1, 3, C('snow', 4))
        cv.px(x0, 2, C('snow', 2)); cv.px(x1 - 1, 2, C('snow', 2))
        cv.rect(x0, 8, x1, 9, C('night', 2), 0.6)
        # sagging chain to the next board
        nx = xc + 50 - 21
        for i in range(0, 9):
            t = i / 8.0
            x = x1 + (nx - x1) * t
            y = 5 + 4 * math.sin(math.pi * t)
            cv.px(x, y, C('steel', 3) if i % 2 else C('steel', 2))
        if k % 3 == 1:                                         # small sign board (no readable text)
            cv.rect(xc - 5, 9, xc + 6, 15, C('snow', 4))
            cv.rect(xc - 5, 15, xc + 6, 16, C('snow', 1))
            for y in (11, 13):
                for x in range(xc - 3, xc + 4, 2):
                    cv.px(x, y, C('night', 2), 0.8)
    save(cv, 'leaflet_barrier.png')


def front():
    """Backs of the crowd at both edges of the view (dark, rim-lit by the floodlights)."""
    cv = Cv(W, H)
    figs = [(-6, 50, 18, 'hat'), (12, 62, 15, 'scarf'), (274, 54, 17, 'scarf'), (290, 46, 19, 'hat')]
    for (x0, top, w, kind) in figs:
        body = [(x0, H), (x0 + 1, top + 16), (x0 + 4, top + 12), (x0 + w - 4, top + 12), (x0 + w - 1, top + 16),
                (x0 + w, H)]
        cv.poly(body, C('night', 1))
        cx = x0 + w / 2
        cv.ellipse(cx, top + 7, 5.0, 6.0, C('night', 2))
        if kind == 'hat':
            cv.rect(cx - 7, top + 2, cx + 8, top + 4, C('night', 0))
            cv.rect(cx - 4, top - 3, cx + 5, top + 2, C('night', 0))
        else:
            cv.ellipse(cx, top + 5, 6.0, 6.5, C('violet', 0))
        # rim light from the floodlights (towards the scene)
        m = cv.a[:, :, 3] > 0
        side = 1 if x0 < W / 2 else -1
        for y in range(top - 4, H):
            xs = [x for x in range(max(0, int(x0 - 8)), min(W, int(x0 + w + 8))) if m[y, x]]
            if xs:
                edge = max(xs) if side > 0 else min(xs)
                cv.a[y, edge] = C('violet', 2)
    save(cv, 'leaflet_front.png')


# ===================================================================================== Konrad stooping
def bend():
    src = Image.open(os.path.join(ROOT, 'assets', 'characters', 'konrad', 'sheet.png')).convert('RGBA')
    meta = json.load(open(os.path.join(ROOT, 'assets', 'characters', 'konrad', 'sheet.json'), encoding='utf-8'))
    cw, ch = meta['cell']
    row = meta['anims']['idle_side']['row']
    cell = np.array(src.crop((0, row * ch, cw, row * ch + ch)))
    ys = np.nonzero(cell[:, :, 3])[0]
    top, bot = int(ys.min()), int(ys.max())
    hip_y = int(round(top + (bot - top) * 0.50))
    hx_ = float(np.nonzero(cell[hip_y, :, 3])[0].mean())
    FW = 40
    out = np.zeros((ch, FW * 3, 4), np.uint8)
    K = 8
    for i, ang in enumerate((16, 31, 46)):
        upper = np.zeros_like(cell)
        upper[:hip_y + 1] = cell[:hip_y + 1]
        lower = cell.copy()
        lower[:hip_y + 1] = 0
        big = Image.fromarray(upper, 'RGBA').resize((cw * K, ch * K), Image.NEAREST)
        canvas = Image.new('RGBA', (FW * K, ch * K), (0, 0, 0, 0))
        canvas.paste(big, (0, 0))
        drop = i                                      # knees give a little as he stoops
        rot = canvas.rotate(-ang, resample=Image.NEAREST, center=(hx_ * K, (hip_y + 0.5) * K),
                            translate=(0, drop * K))
        ra = np.array(rot)
        small = ra[K // 2::K, K // 2::K][:ch, :FW]
        frame = np.zeros((ch, FW, 4), np.uint8)
        lw = np.zeros((ch, FW, 4), np.uint8)
        lw[:, :cw] = lower
        if drop:                                      # shorten the coat hem a touch (bent knees)
            lw[hip_y + 1:ch - 3] = np.concatenate([lw[hip_y + 1 + drop:ch - 3], np.zeros((drop, FW, 4), np.uint8)])
        frame[:] = lw
        m = small[:, :, 3] > 0
        frame[m] = small[m]
        out[:, i * FW:(i + 1) * FW] = frame
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'leaflet_bend.png'), optimize=True)
    print('wrote leaflet_bend.png', out.shape[1], 'x', out.shape[0], 'hip', hip_y, round(hx_, 1))
    return hip_y


# ===================================================================================== the sheet
def sheet():
    cv = Cv(36, 8)
    paper, paper_d, ink = C('snow', 4), C('snow', 2), C('night', 2)
    # 0 flat: a parallelogram lying in the snow, typed lines, a faint shadow
    cv.poly([(1, 7), (3, 4), (11, 4), (9, 7)], paper)
    cv.line(2, 7, 9, 7, paper_d)
    for x in range(4, 10, 2):
        cv.px(x, 5, ink, 0.7)
    cv.px(5, 6, ink, 0.6); cv.px(7, 6, ink, 0.6)
    # 1 corner lifted by the wind
    o = 12
    cv.poly([(o + 1, 7), (o + 3, 4), (o + 8, 4), (o + 8, 7)], paper)
    cv.poly([(o + 8, 4), (o + 11, 2), (o + 10, 6), (o + 8, 7)], paper_d)
    for x in range(o + 4, o + 8, 2):
        cv.px(x, 5, ink, 0.7)
    cv.line(o + 2, 7, o + 9, 7, C('snow', 1), 0.6)
    # 2 fluttering: lifted off the ground, curled, shadow below
    o = 24
    cv.poly([(o + 2, 4), (o + 4, 1), (o + 10, 2), (o + 9, 5)], paper)
    cv.line(o + 2, 4, o + 9, 5, paper_d)
    cv.px(o + 6, 3, ink, 0.6); cv.px(o + 8, 3, ink, 0.6)
    cv.rect(o + 3, 7, o + 10, 8, C('snow', 1), 0.7)
    save(cv, 'leaflet_sheet.png')
    w = Cv(16, 6)
    w.poly([(0, 5), (2, 3), (7, 3), (6, 5)], paper)
    w.px(3, 4, ink, 0.6); w.px(5, 4, ink, 0.6)
    w.poly([(8, 5), (10, 3), (13, 3), (14, 1), (14, 5)], paper)
    w.px(10, 4, ink, 0.6)
    w.line(9, 5, 14, 5, paper_d)
    save(w, 'world_leaflet.png')


def layout(hip_y):
    data = {
        'size': [W, H], 'scale': 3, 'lane': list(LANE), 'feet_y': FEET_Y, 'sheet_y': SHEET_Y,
        'guards': [list(g) for g in GUARDS], 'eye_dy': -44, 'barrier_y': BARRIER_Y, 'march_y': MARCH_Y,
        'march_speed': 7.0, 'bend_cell': [40, 56], 'bend_origin': [16, 54], 'bend_hip_y': hip_y,
        'sheet_cell': [12, 8], 'world_cell': [8, 6],
        'note': 'art px; generated by tools/pixelgen/gen_minigame_plaza.py',
    }
    with open(os.path.join(OUT, 'leaflet_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1)
        f.write('\n')
    print('wrote leaflet_layout.json')


def preview(path):
    """Composite preview of the scene (x3) for review; not an asset."""
    def ld(n):
        return Image.open(os.path.join(OUT, n)).convert('RGBA')
    im = ld('leaflet_back.png')
    im.alpha_composite(ld('leaflet_march.png'), (0, MARCH_Y))
    g = Image.open(os.path.join(ROOT, 'assets', 'characters', 'guard', 'sheet.png')).convert('RGBA')
    gm = json.load(open(os.path.join(ROOT, 'assets', 'characters', 'guard', 'sheet.json'), encoding='utf-8'))
    fr = g.crop((0, gm['anims']['idle_front']['row'] * 56, 32, gm['anims']['idle_front']['row'] * 56 + 56))
    fs = g.crop((0, 0, 32, 56)).transpose(Image.FLIP_LEFT_RIGHT)
    im.alpha_composite(fs, (GUARDS[0][0] - 16, GUARDS[0][1] - 54))
    im.alpha_composite(fr, (GUARDS[1][0] - 16, GUARDS[1][1] - 54))
    im.alpha_composite(ld('leaflet_barrier.png'), (0, BARRIER_Y))
    sh = ld('leaflet_sheet.png').crop((0, 0, 12, 8))
    im.alpha_composite(sh, (150, SHEET_Y - 7))
    k = Image.open(os.path.join(ROOT, 'assets', 'characters', 'konrad', 'sheet.png')).convert('RGBA').crop((0, 0, 32, 56))
    im.alpha_composite(k, (80 - 16, FEET_Y - 54))
    b = ld('leaflet_bend.png')
    for i in range(3):
        im.alpha_composite(b.crop((i * 40, 0, i * 40 + 40, 56)), (170 + i * 30 - 16, FEET_Y - 54))
    im.alpha_composite(ld('leaflet_front.png'), (0, 0))
    im.resize((W * 3, H * 3), Image.NEAREST).save(path)
    print('preview', path)


def main(argv):
    back()
    march()
    barrier()
    front()
    hip = bend()
    sheet()
    layout(hip)
    for i, a in enumerate(argv):
        if a == '--preview' and i + 1 < len(argv):
            preview(argv[i + 1])


if __name__ == '__main__':
    main(sys.argv[1:])
