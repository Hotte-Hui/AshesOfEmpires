"""gen_tasks -- art for the side tasks (Aufgaben, TECHNICAL_ARCHITECTURE 12.9; owner: tasks).

Writes
  assets/explore/tasks/<name>.png  close-ups, 240 x 150 px pixel art 1:1, shown x3 by the discovery view (12.1):
    berlin_drawing   Lotte's folded drawing for the porter (task "Zweimal klopfen", find berlin.task.mittens.door):
                     squared school paper, folded twice, held up in the dim stairwell; drawn in coloured pencil by
                     a child: the porter's lodge with a wobbly PFOERTNER sign, the porter with cap and moustache,
                     the radio on the counter with its green eye, music notes flying out, a sun, the signature
                     LOTTE and a heart.  No insignia of any kind.
  assets/ui/tasks/mark_task.png    HUD prompt marker "next step of a side task" (9 x 9 art px stored x3 like the
                                   exploration kit's mark_new.png: a small hollow amber diamond with a lit core,
                                   echoing the objective diamond of the HUD, quieter than the "new find" twinkle).
Painted in the tone space of tools/pixelgen/explore_berlin.py (its Canvas, ramps and helpers are imported
read-only, so the close-up shares the Berlin archive palette and dithering); the marker uses the colours of the
exploration UI kit (tools/pixelgen/gen_ui_explore.py, read-only constants).  Everything is procedural; nothing
is traced or sampled.  Deterministic: all randomness comes from numpy generators seeded with crc32 of fixed
names (no wall clock, no hash()); a re-run reproduces the files byte for byte.

Run:  py -3 -P tools/pixelgen/gen_tasks.py [--preview DIR]
"""
from __future__ import annotations

import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explore_berlin as eb  # noqa: E402  (read-only: Canvas, ramps, masks)
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'explore', 'tasks')
W, H = eb.W, eb.H
YY, XX = np.mgrid[0:H, 0:W]


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


# =========================================================================== child's pencil
def wobble(pts, seed, amp=0.7, step=1.5):
    """Densifies a polyline and offsets it with a smooth random wobble (a child's unsteady hand)."""
    rng = np.random.default_rng(seed)
    dense = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(n):
            t = k / n
            dense.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    dense.append(pts[-1])
    # low-frequency noise along the stroke: sum of two sines with random phase
    ph1, ph2 = rng.uniform(0, 6.28, 2)
    f1, f2 = rng.uniform(0.12, 0.2), rng.uniform(0.3, 0.5)
    out = []
    for i, (x, y) in enumerate(dense):
        dx = amp * (math.sin(i * f1 + ph1) * 0.7 + math.sin(i * f2 + ph2) * 0.3)
        dy = amp * (math.cos(i * f1 * 1.1 + ph2) * 0.7 + math.sin(i * f2 * 0.9 + ph1) * 0.3)
        out.append((x + dx, y + dy))
    return out


def pencil(cv, pts, ramp, tone, seed, amp=0.7, skip=0.06, closed=False):
    """1-px coloured-pencil stroke: wobbly, with the occasional skipped pixel where the lead lifts."""
    if closed:
        pts = list(pts) + [pts[0]]
    path = wobble(pts, seed, amp)
    rng = np.random.default_rng(seed + 11)
    m = np.zeros((cv.h, cv.w), bool)
    for a, b in zip(path[:-1], path[1:]):
        for (x, y) in eb.bres(a[0], a[1], b[0], b[1]):
            if 0 <= x < cv.w and 0 <= y < cv.h:
                m[y, x] = True
    if skip > 0:
        m &= rng.random((cv.h, cv.w)) > skip
    cv.put(m, 0, 0, ramp, tone, flat=True)
    return m


def scribble_fill(cv, mask, ramp, tone, seed, spacing=3, angle=0.9, cover=0.82, under=None):
    """Child colouring: parallel zig-zag strokes across the mask, a few gaps, strokes may stop short."""
    rng = np.random.default_rng(seed)
    ca, sa = math.cos(angle), math.sin(angle)
    u = XX * ca + YY * sa                    # stroke-normal coordinate
    band = np.floor(u / spacing).astype(np.int32)
    on = (np.abs(u - (band + 0.5) * spacing) < 0.75)
    # per-band random start/stop along the stroke direction -> unfinished colouring
    v = -XX * sa + YY * ca
    keep = np.zeros_like(mask)
    for b in np.unique(band[mask]):
        sel = mask & (band == b)
        if not sel.any():
            continue
        vv = v[sel]
        lo, hi = vv.min(), vv.max()
        a = lo + (hi - lo) * rng.uniform(0.0, 1.0 - cover) * 0.5
        z = hi - (hi - lo) * rng.uniform(0.0, 1.0 - cover) * 0.5
        keep |= sel & (v >= a) & (v <= z)
    m = mask & on & keep
    if under is not None:
        m &= under
    m &= rng.random((cv.h, cv.w)) > 0.08
    cv.put(m, 0, 0, ramp, tone, flat=True)
    return m


## A child writes N and M with their diagonals (the 3-px archive font cannot): wider glyphs for those two.
CHILD_GLYPHS = {
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#'],
}


def child_text(cv, x, y, s, ramp, tone, seed, scale=2, jitter=1.2, gap=1):
    """Capital letters on an uneven baseline, each one leaning its own way (F35 glyphs, sheared)."""
    rng = np.random.default_rng(seed)
    cx = x
    for ch in s:
        g = CHILD_GLYPHS.get(ch.upper(), eb.F35.get(ch.upper(), eb.F35[' ']))
        sc = scale
        dy = int(round(rng.uniform(-jitter, jitter)))
        shear = rng.uniform(-0.18, 0.18)
        for yy, row in enumerate(g):
            for xx, c in enumerate(row):
                if c != '#':
                    continue
                for sy in range(sc):
                    for sx in range(sc):
                        px = cx + xx * sc + sx + int(round((yy * sc + sy - 2 * sc) * shear))
                        cv.px(px, y + dy + yy * sc + sy, ramp, tone)
        cx += len(g[0]) * sc + gap + int(rng.integers(0, 2))
    return cx - x


def note(cv, x, y, ramp, tone, seed, flag=True, beam_to=None):
    """A music note as a child draws it: filled oval head, stem, a flag (or a beam to the next note)."""
    m, x0, y0 = eb.ellipse_mask(x, y, 2.2, 1.6)
    cv.put(m, x0, y0, ramp, tone, flat=True)
    pencil(cv, [(x + 2, y), (x + 2, y - 7)], ramp, tone, seed, amp=0.25, skip=0.0)
    if beam_to is not None:
        pencil(cv, [(x + 2, y - 7), (beam_to[0] + 2, beam_to[1] - 7)], ramp, tone, seed + 1, amp=0.3, skip=0.0)
    elif flag:
        pencil(cv, [(x + 2, y - 7), (x + 5, y - 4), (x + 4, y - 2)], ramp, tone, seed + 2, amp=0.25, skip=0.0)


# =========================================================================== the close-up
def s_berlin_drawing(cv):
    # ---- the stairwell behind the sheet: dark green-grey tiles, a step edge below, cold light from above left
    eb.wall(cv, 3.6, seed=2)
    tiles = np.zeros((H, W), bool)
    tiles[(YY % 12) == 0] = True
    tiles[((XX + (YY // 12) * 6) % 12) == 0] = True
    cv.adjust(-0.9, tiles)
    step = cv.full(cv.rect(0, 132, W, 18, 'stone', 1.6))
    cv.adjust(np.where(YY < 134, 1.2, 0.0), step)
    cv.noise(6, 0.35, step, seed_add=5)
    cv.grain(0.25, step, seed_add=6)

    # ---- the sheet: squared school paper, folded twice (vertical + horizontal crease), held up crooked
    px0, py0, pw, ph = 30, 10, 180, 124
    sheet = eb.paper_sheet(cv, px0, py0, pw, ph, tone=6.1, seed=21, age=0.32, edge_dark=0.6)
    grid = sheet & (((XX - px0) % 6 == 0) | ((YY - py0) % 6 == 0))
    cv.put(grid, 0, 0, 'snow', 3.0, flat=True)                                # faint grey squares
    cv.put(sheet & ((XX - px0) == 14), 0, 0, 'red', 4.0, flat=True)            # the red margin line
    crease_x, crease_y = px0 + pw // 2, py0 + ph // 2
    cv.adjust(-1.1, sheet & (XX == crease_x))
    cv.adjust(0.6, sheet & (XX == crease_x + 1))
    cv.adjust(-0.8, sheet & (YY == crease_y))
    cv.adjust(0.4, sheet & (YY == crease_y + 1))
    cv.adjust(np.where(XX > crease_x, -0.35, 0.15), sheet)                     # the two halves catch light differently
    corner = cv.full(cv.poly([(px0 + pw - 13, py0 + ph), (px0 + pw, py0 + ph - 13), (px0 + pw, py0 + ph)], 'room', 3.0))
    cv.put(cv.full(cv.poly([(px0 + pw - 13, py0 + ph - 1), (px0 + pw - 1, py0 + ph - 13), (px0 + pw - 12, py0 + ph - 12)],
                           'paper', 4.4)), 0, 0, 'paper', 4.4)               # dog-ear
    sheet &= ~corner
    cv.shadow(sheet, 3, 3, 1.3)

    # ---- the lodge: counter (brown, coloured in), two posts, the roof line and the sign
    counter = cv.full(cv.rect(60, 86, 100, 30, 'paper', 6.1))                  # placeholder (keeps the paper tone)
    pencil(cv, [(58, 86), (162, 85), (161, 117), (59, 118)], 'wood', 4.0, seed_of('counter'), amp=0.8, closed=True)
    scribble_fill(cv, counter & (XX > 61) & (XX < 159) & (YY > 87) & (YY < 116), 'wood', 6.0, seed_of('counter_fill'),
                  spacing=3, angle=1.05)
    pencil(cv, [(60, 86), (59, 47)], 'wood', 4.0, seed_of('post_l'), amp=0.6)
    pencil(cv, [(160, 85), (161, 46)], 'wood', 4.0, seed_of('post_r'), amp=0.6)
    pencil(cv, [(52, 48), (110, 42), (168, 47)], 'wood', 3.5, seed_of('roof'), amp=0.7)
    pencil(cv, [(52, 48), (60, 52), (161, 51), (168, 47)], 'wood', 3.5, seed_of('roof2'), amp=0.5)
    child_text(cv, 76, 26, 'PFÖRTNER', 'red', 3.2, seed_of('sign'), scale=2, jitter=1.4)

    # ---- the porter behind the counter: cap with visor, round face, dots, moustache, smile, blue uniform
    head = cv.full(cv.ellipse(92, 66, 9.5, 9, 'paper', 6.1))
    pencil(cv, [(92 + 9.5 * math.cos(a), 66 + 9 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 26)],
           'wood', 3.0, seed_of('head'), amp=0.45, closed=False, skip=0.02)
    scribble_fill(cv, head & ((XX - 92) ** 2 / 80 + (YY - 66) ** 2 / 72 < 1), 'glow', 1.6, seed_of('face'),
                  spacing=2, angle=0.6, cover=0.75)
    cap = cv.full(cv.poly([(81, 60), (83, 53), (92, 50), (101, 53), (103, 60)], 'blue', 1.5, flat=True))
    pencil(cv, [(81, 60), (110, 60)], 'blue', 0.5, seed_of('visor'), amp=0.3, skip=0.0)
    cv.px(88, 64, 'ink', 0); cv.px(96, 64, 'ink', 0)
    cv.px(89, 64, 'ink', 0); cv.px(97, 64, 'ink', 1)
    pencil(cv, [(85, 70), (88, 68.5), (92, 70), (96, 68.5), (99, 70)], 'wood', 2.0, seed_of('moustache'), amp=0.2, skip=0.0)
    pencil(cv, [(87, 73), (92, 75.5), (97, 73)], 'red', 3.0, seed_of('smile'), amp=0.2, skip=0.0)
    body = cv.full(cv.poly([(80, 86), (83, 76), (101, 76), (104, 86)], 'paper', 6.1))
    pencil(cv, [(80, 86), (83, 76), (101, 76), (104, 86)], 'blue', 1.0, seed_of('body'), amp=0.4)
    scribble_fill(cv, body, 'blue', 2.6, seed_of('body_fill'), spacing=2, angle=-0.8, cover=0.9)
    pencil(cv, [(101, 79), (112, 83), (117, 79)], 'blue', 1.2, seed_of('arm'), amp=0.4)   # hand on the radio

    # ---- the radio on the counter: brown box, round grille, the green magic eye, the tuning knob
    radio = cv.full(cv.rect(118, 68, 28, 18, 'paper', 6.1))
    pencil(cv, [(117, 68), (146, 67), (147, 86), (118, 86)], 'wood', 2.5, seed_of('radio'), amp=0.5, closed=True)
    scribble_fill(cv, radio & (XX > 118) & (XX < 146) & (YY > 68) & (YY < 85), 'wood', 5.0, seed_of('radio_fill'),
                  spacing=2, angle=0.3, cover=0.9)
    gr, gx, gy = eb.ellipse_mask(127, 77, 4.5, 4.5)
    cv.put(gr, gx, gy, 'graphite', 1.0, flat=True)
    cv.put(gr & ((np.add.outer(np.arange(gr.shape[0]), np.arange(gr.shape[1]))) % 2 == 0), gx, gy, 'graphite', 3.0, flat=True)
    eye, ex, ey = eb.ellipse_mask(139, 73, 2.0, 2.0)
    cv.put(eye, ex, ey, 'green', 5.0, flat=True)
    cv.px(139, 73, 'green', 6)
    cv.px(140, 81, 'ink', 1); cv.px(141, 81, 'ink', 1); cv.px(140, 82, 'ink', 1)

    # ---- music notes flying out of the radio, along a dotted swirl, up to the sun
    swirl = [(146 + t * 46, 64 - t * 36 - 7 * math.sin(t * 7.5)) for t in np.linspace(0, 1, 40)]
    for i, (x, y) in enumerate(swirl):
        if i % 3 == 0:
            cv.px(x, y, 'blue', 2.0)
    note(cv, 152, 60, 'ink', 0, seed_of('n1'))
    note(cv, 163, 50, 'ink', 0, seed_of('n2'), beam_to=(170, 46))
    note(cv, 170, 46, 'ink', 0, seed_of('n3'), flag=False)
    note(cv, 181, 34, 'ink', 1, seed_of('n4'))
    note(cv, 176, 62, 'blue', 1.0, seed_of('n5'))
    note(cv, 191, 50, 'blue', 1.0, seed_of('n6'))

    # ---- the sun in the corner (coloured in, rays drawn twice where the child pressed harder)
    sun = cv.full(cv.ellipse(190, 25, 6.5, 6.5, 'paper', 6.1))
    scribble_fill(cv, sun, 'amber', 4.0, seed_of('sun'), spacing=2, angle=0.2, cover=0.95)
    pencil(cv, [(190 + 6.5 * math.cos(a), 25 + 6.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18)],
           'amber', 2.5, seed_of('sun_rim'), amp=0.3, skip=0.0)
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.3
        pencil(cv, [(190 + 9 * math.cos(a), 25 + 9 * math.sin(a)), (190 + 14 * math.cos(a), 25 + 14 * math.sin(a))],
               'amber', 3.0, seed_of('ray%d' % k), amp=0.2, skip=0.0)

    # ---- signature and a heart, bottom right
    child_text(cv, 150, 116, 'LOTTE', 'blue', 1.0, seed_of('lotte'), scale=2, jitter=0.8)
    heart = [(190, 126), (186, 121), (187, 117), (190, 117), (192, 120), (194, 117), (197, 117), (198, 121), (194, 126), (192, 128)]
    hm = cv.full(cv.poly(heart, 'red', 3.6, flat=True))
    pencil(cv, heart, 'red', 2.4, seed_of('heart'), amp=0.2, closed=True, skip=0.0)

    # ---- light: cold daylight from the stairwell window (top left), the far half of the sheet in shadow
    cv.spot(0, -10, 210, 1.1)
    cv.linear(0.2, -0.5)
    cv.vignette(1.4)
    return hm


SCENES = {
    'berlin_drawing': s_berlin_drawing,
}


def render(name: str) -> np.ndarray:
    cv = eb.Canvas('tasks_' + name)
    SCENES[name](cv)
    return cv.render()


# =========================================================================== HUD prompt marker
UI_OUT = os.path.join(ROOT, 'assets', 'ui', 'tasks')
# exploration UI kit colours (tools/pixelgen/gen_ui_explore.py: COPPER, COPPER_L, AMBER, AMBER_L)
MARK_COLS = {'o': '#BA775B', 'a': '#DCA16E', 'L': '#F0C487', 'W': '#FBE3AA'}
MARK_TASK = ['....o....',
             '...oao...',
             '..oa.ao..',
             '.oa.L.ao.',
             'oa.LWL.ao',
             '.oa.L.ao.',
             '..oa.ao..',
             '...oao...',
             '....o....']


def mark_task() -> Image.Image:
    """Next step of a side task: a hollow amber diamond (copper rim) around a small lit core, 9 x 9 at 1:1."""
    img = Image.new('RGBA', (9, 9), (0, 0, 0, 0))
    for y, row in enumerate(MARK_TASK):
        for x, ch in enumerate(row):
            if ch in MARK_COLS:
                c = pg.hx(MARK_COLS[ch])
                img.putpixel((x, y), (int(c[0]), int(c[1]), int(c[2]), 255))
    return img


def main(argv: list[str]) -> int:
    preview = None
    if len(argv) >= 2 and argv[0] == '--preview':
        preview = argv[1]
    os.makedirs(UI_OUT, exist_ok=True)
    mark_task().resize((27, 27), Image.NEAREST).save(os.path.join(UI_OUT, 'mark_task.png'))
    print('wrote mark_task 27 x 27')
    os.makedirs(OUT, exist_ok=True)
    for name in SCENES:
        arr = render(name)
        bad = eb.palette_problems(arr)
        if bad:
            print('PALETTE', name, bad[:6])
        Image.fromarray(arr, 'RGBA').save(os.path.join(OUT, name + '.png'))
        print('wrote', name, arr.shape[1], 'x', arr.shape[0])
        if preview:
            os.makedirs(preview, exist_ok=True)
            Image.fromarray(arr, 'RGBA').resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(preview, name + '_x3.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
