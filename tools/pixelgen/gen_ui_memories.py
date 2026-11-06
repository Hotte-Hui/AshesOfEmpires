"""gen_ui_memories -- pixel-art UI for the „Erinnerungen“ feature (TECHNICAL_ARCHITECTURE 12.10).

Writes
  * assets/ui/memories/icon_memory.png      x3 nearest (39x39): a small pocket watch whose hands run back,
                                             drawn procedurally in the UI palette (copper case, paper face, ink)
  * assets/ui/memories/<scene>.png          320x180 sepia prints for the MemoryView cards, made from the raw
                                             in-game captures assets/ui/memories/src/raw_<scene>.png
                                             (tests/visual/memory_thumbs.tscn, neutral insignia --symbols=0):
                                             a hand-framed 320x180 window of the 640x360 world frame (1 world px =
                                             1 print px, crisp), toned to a warm silver-gelatine ramp with a lifted
                                             black, a soft vignette, a faint paper grain and an ordered 4x4 Bayer
                                             quantisation to 16 tones (pixel-art print, no blur)
  * assets/ui/memories/manifest.json        what was written (sizes, crops, sources)
The raw captures are renderings of the running game (snow and walkers move), so re-capturing gives slightly
different frames; everything this script does is deterministic: the same raw files give byte-identical output.
No real insignia: the captures are taken with the neutral twins (§12.4 — never in menus).

Run:  py -3 -P tools/pixelgen/gen_ui_memories.py
"""
from __future__ import annotations

import json
import math
import os
import zlib

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'memories')
SRC = os.path.join(OUT, 'src')

PRINT = (320, 180)
## scene -> top-left of the 320x180 window inside the 640x360 capture (chosen from a camera survey)
CROPS = {
    'L_A1_Railyard': (236, 126),
    'L_M1_Archive': (196, 146),
    'L_M1_Plaza': (214, 92),
    'L_C3_Station': (120, 56),
    'L_C3_Hall': (150, 50),
    # Chapter 3 part 2 (one level file, a look per scene): A night yard + Annahme, B green lamp over the sorting
    # table, C fire front at the card cabinet, D booth / chute with the fire in the Karteisaal; the night quay
    'L_C3_RegistryA': (150, 124),
    'L_C3_RegistryB': (236, 124),
    'L_C3_RegistryC': (320, 124),
    'L_C3_RegistryD': (100, 124),
    'L_C3_Quay': (225, 124),
    # Chapter 4 part 1 (two level files, two scenes each; round-9 fix compl-03): A Lev's desk under the green lamp
    # with the samovar, B the tram loop at dawn with tram 74 and Marta, C the siding: wagon 24 318 (C-17/45), the
    # heap of number plates and Alexei facing Lev at his siding post (art-13), D the whole counter „Auskunft ·
    # Abgleich“ with Fengler behind it, the waiting bench and Konrad at the tube station
    'L_C4_TunnelsA': (260, 128),
    'L_C4_AnnexA': (130, 128),
    'L_C4_TunnelsB': (218, 128),
    'L_C4_AnnexB': (262, 128),
    # Chapter 4 part 2 (round 10, lead; two level files, two scenes each): A the coal stage at dawn — Alexei, Kolonne 4
    # shovelling, Maria in her headscarf, the guard at the barrel fire; B the Corridor platform — the courier car
    # „C-17“, the green car „Di – Kordon“, the dining car and Ekdahl facing Konrad; C the showcase for the press —
    # „ВОССТАНОВИМ ВМЕСТЕ“ on the tarpaulin, Alexei facing Ekdahl at the signal post, the model locomotive in its arch
    # (top edge under the banner), the band, the minder, the canteen table; D the courtyard at night — Konrad and
    # Hanna at the stair door „Aufg. B“, the lit windows of the households, the lodge window with Frau Kuhnert
    'L_C4P2_KarskA': (228, 128),
    'L_C4P2_BerlinA': (310, 124),
    'L_C4P2_KarskB': (0, 130),
    'L_C4P2_BerlinB': (84, 124),
}
## warm silver-gelatine ramp: lifted black -> umber -> sepia -> cream highlight (sRGB)
RAMP = [(0.00, (30, 22, 16)), (0.18, (58, 42, 30)), (0.40, (104, 79, 56)), (0.62, (156, 126, 92)),
        (0.82, (206, 180, 140)), (1.00, (240, 228, 202))]
LEVELS = 16
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float64) + 0.5) / 16.0

# UI palette (scripts/ui/ui_kit.gd)
COPPER_D, COPPER, COPPER_L, AMBER = '#7A3E26', '#BA775B', '#DCA16E', '#F0C487'
PAPER_D, PAPER_M, PAPER, PAPER_L = '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'
INK, INK_B = '#1A1C2A', '#2E3248'


def hx(h: str, a: int = 255) -> np.ndarray:
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], np.uint8)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


# ============================================================================ icon
def icon_memory() -> Image.Image:
    """13x13 pocket watch: copper case with crown, paper face, the hands at nine o'clock (minute hand up, hour
    hand left — an unmistakable clock face, no 'face' reading), and an amber arc on the rim from twelve back to
    eight o'clock with its arrow tip: time running backwards. Upscaled x3 like every UI icon."""
    n = 13
    a = np.zeros((n, n, 4), np.uint8)
    cx, cy, r = 6.5, 7.0, 5.0
    for y in range(n):
        for x in range(n):
            d = math.hypot(x + 0.5 - cx - 0.5, y - cy)
            if d <= r + 0.4:
                a[y, x] = hx(COPPER)
                if d <= r - 0.8:
                    a[y, x] = hx(PAPER)
            if r - 0.8 < d <= r + 0.4:
                ang = math.degrees(math.atan2(y - cy, x - cx + 0.5))   # 0 = 3 o'clock, -90 = 12 o'clock
                if 20 < ang < 120:
                    a[y, x] = hx(COPPER_D)                           # shadowed lower right
                if -95 <= ang <= -88 or ang >= 145 or ang <= -150:
                    a[y, x] = hx(AMBER)                              # the arc 12 -> 9 -> 8 o'clock
                elif -150 < ang < -95:
                    a[y, x] = hx(AMBER)
    # crown on top
    a[0, 5:8] = hx(COPPER_L)
    a[1, 6] = hx(COPPER_D)
    # arrow tip at ~8 o'clock pointing down (counter-clockwise direction on the left side)
    a[10, 0] = hx(AMBER)
    a[10, 2] = hx(AMBER)
    a[11, 1] = hx(AMBER)
    # hands: minute up (12), hour left (9); hub
    for (x, y) in [(6, 4), (6, 5), (6, 6), (5, 7), (4, 7)]:
        a[y, x] = hx(INK)
    a[7, 6] = hx(COPPER_D)
    # quarter marks at 3 and 6
    a[7, 10] = hx(PAPER_D)
    a[10, 6] = hx(PAPER_D)
    img = Image.fromarray(a, 'RGBA')
    return img.resize((n * 3, n * 3), Image.NEAREST)


# ============================================================================ prints
def _ramp(L: np.ndarray) -> np.ndarray:
    out = np.zeros(L.shape + (3,), np.float64)
    for i in range(len(RAMP) - 1):
        a0, c0 = RAMP[i]
        a1, c1 = RAMP[i + 1]
        m = (L >= a0) & (L <= a1)
        t = ((L - a0) / (a1 - a0))[m][:, None]
        out[m] = np.array(c0, np.float64) * (1.0 - t) + np.array(c1, np.float64) * t
    return out


def sepia_print(raw: Image.Image, crop: tuple[int, int], name: str) -> Image.Image:
    x0, y0 = crop
    im = raw.convert('RGB').crop((x0, y0, x0 + PRINT[0], y0 + PRINT[1]))
    a = np.asarray(im).astype(np.float64) / 255.0
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    # normalise the frame's own range (night scenes stay night, but use the whole print scale)
    lo, hi = np.percentile(L, 1.5), np.percentile(L, 99.6)
    L = np.clip((L - lo) / max(hi - lo, 1e-3), 0.0, 1.0)
    L = L ** 0.82                                   # open the shadows a little
    L = 0.7 * L + 0.3 * (L * L * (3.0 - 2.0 * L))   # gentle S curve
    h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w]
    qx = (xx + 0.5) / w - 0.5
    qy = (yy + 0.5) / h - 0.5
    v = np.clip((qx * qx + qy * qy) * 2.0 * 0.5, 0.0, 1.0)
    L = L * (1.0 - 0.55 * v)                        # soft vignette, like an old enlargement
    rng = np.random.default_rng(seed_of(name))
    L = np.clip(L + (rng.random((h, w)) - 0.5) * 0.035, 0.0, 1.0)   # paper grain
    th = BAYER4[yy % 4, xx % 4]
    Lq = np.clip(np.floor(L * (LEVELS - 1) + th), 0, LEVELS - 1) / (LEVELS - 1)
    rgb = _ramp(Lq)
    return Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), 'RGB')


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    manifest = {'generator': 'tools/pixelgen/gen_ui_memories.py', 'files': []}
    ic = icon_memory()
    ic.save(os.path.join(OUT, 'icon_memory.png'), optimize=False)
    manifest['files'].append({'file': 'icon_memory.png', 'size': list(ic.size), 'scale': 3})
    for name, crop in CROPS.items():
        src = os.path.join(SRC, 'raw_%s.png' % name)
        if not os.path.exists(src):
            print('missing capture', os.path.relpath(src, ROOT), '(run tests/visual/memory_thumbs.tscn)')
            continue
        pr = sepia_print(Image.open(src), crop, name)
        pr.save(os.path.join(OUT, name + '.png'), optimize=False)
        manifest['files'].append({'file': name + '.png', 'size': list(pr.size), 'source': 'src/raw_%s.png' % name,
                                  'crop': list(crop)})
        print('wrote', os.path.relpath(os.path.join(OUT, name + '.png'), ROOT))
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
