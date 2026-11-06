"""gen_parade -- sprites and mattes for L_M1_Parade (the regime's parade before the Great Hall).
Owner: parade.  Original, deterministic, berlin palette only (pg.PALETTES['berlin']).
Outputs (assets/architecture/parade/):
  figures.png + figures.json  LOD atlas of the parade figures (gen_parade_figs.py).  19 LOD strips, figure
                              heights 2..346 px, every strip drawn at 1 texel = 1 px.  Slots: 18 civilians seen
                              from behind (coats, hats, headscarves, collars, scarves, bags, a cane, heights and
                              shoulder widths), a child with a limp little flag, a small child, 2 guards (gorget,
                              white belt; rifle at order / slung), soldier at attention, block leader, marching
                              soldier in profile (8 frames = 2 steps, breath), 3 grey officials, 3 dust/snow puffs.
                              The large strips (>= 86 px) hold only the slots that come that close to a camera
                              (figures.json lods[i][4] = slots in strip i).  Faces of the troops are always a
                              shadow under the helmet: anonymous ranks, no individuals.  parade_figures.gdshader
                              picks the strip whose height matches the projected size.
  flag_limp.png / flag_limp_hist.png   the child's limp hand flag (neutral cloth / historical variant, §12.4)
  sky_parade.png, fog_parade.png       cold overcast dusk matte + cold fog gradient (same mapping as the hall's)
Run: py -3 -P tools/pixelgen/gen_parade.py   (PARADE_PREVIEW=<png> also writes a 2x preview)
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import gen_parade_figs as F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'architecture', 'parade')
B = pg.PALETTES['berlin']
LODS = F.LODS


def c(r, i):
    return B[r][i]


# ------------------------------------------------------------------------------------------- figures
# Figure kit + designs live in gen_parade_figs.py (crowd backs, children, guards, troops, officials, puffs).
def build_atlas():
    sl, big_n, mid_n = F.slots()
    strips = []
    width = 0
    for h in LODS:
        cw, ch = F.cell_size(h)
        n = F.strip_slot_count(h, len(sl), big_n, mid_n)
        strip = np.zeros((ch, cw * n, 4), np.uint8)
        for i, (kind, fig) in enumerate(sl[:n]):
            strip[:, i * cw:(i + 1) * cw] = F.render(fig, h)
        strips.append((strip, n))
        width = max(width, strip.shape[1])
    height = sum(s.shape[0] for s, _ in strips)
    atlas = np.zeros((height, width, 4), np.uint8)
    lods = []
    y = 0
    for h, (s, n) in zip(LODS, strips):
        atlas[y:y + s.shape[0], :s.shape[1]] = s
        cw, ch = F.cell_size(h)
        lods.append([y, cw, ch, h, n])
        y += s.shape[0]
    Image.fromarray(atlas, 'RGBA').save(os.path.join(OUT, 'figures.png'))
    names = [k for k, _ in sl]
    slots = {}
    for i, k in enumerate(names):
        if k not in slots:
            slots[k] = [i, names.count(k)]
    meta = {'atlas': [width, height], 'lods': lods, 'slots': slots, 'height_m': 1.8,
            'anchor': 'x = floor(cell_w / 2), y = fig_h + 1 (feet bottom boundary)',
            'lod_fields': 'strip_y, cell_w, cell_h, figure_h, slots_in_strip (large strips hold only the first slots)',
            'generator': 'tools/pixelgen/gen_parade.py + gen_parade_figs.py'}
    with open(os.path.join(OUT, 'figures.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, indent=1)
    return atlas, meta


# ------------------------------------------------------------------------------------------- hand flag
def limp_flag(hist):
    w, h = 9, 19
    a = np.zeros((h, w, 4), np.uint8)

    def px(x, y, col):
        a[y, x, :3] = pg.hx(col)[:3]
        a[y, x, 3] = 255
    for y in range(2, h):
        px(1, y, c('ochre', 0))
    cloth = [c('ochre', 3), c('ochre', 2)] if hist else [c('steel', 3), c('steel', 2)]
    for y in range(2, 12):
        for x in range(2, 2 + max(1, 5 - (y - 2) // 3)):
            px(x, y, cloth[(x + y // 4) % 2] if y < 10 else cloth[1])
    if hist:   # a fold of the white disc shows, the emblem itself is crumpled out of sight
        px(3, 5, c('snow', 3))
        px(3, 6, c('snow', 2))
        px(2, 6, c('night', 2))
    px(1, 1, c('steel', 4))
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, 'flag_limp%s.png' % ('_hist' if hist else '')))


# ------------------------------------------------------------------------------------------- mattes
def sky_and_fog():
    W, H = 1024, 720
    AX, AY = 512, 430
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    xx = np.ones((H, 1), np.float32) * np.arange(W, dtype=np.float32)[None, :]
    k = np.clip((yy - 40.0) / (AY - 40.0), 0.0, 1.0)            # 0 zenith .. 1 horizon
    ramp = [pg.hx(x)[:3].astype(np.float32) for x in ['#120C14', '#1B1520', '#211623', '#2A2130', '#342F37',
                                                       '#443B43', '#454E58', '#5F6973', '#6E6A73']]
    pos = np.clip(k ** 1.6 * (len(ramp) - 1), 0, len(ramp) - 1.001)
    i0 = pos.astype(int)
    f = (pos - i0)[..., None]
    R = np.stack(ramp)
    rgb = R[i0] * (1 - f) + R[i0 + 1] * f
    # low overcast deck: dark bellies, edges catching the cold city glow from below
    n = pg.value_noise(W, H, 90.0, seed=1964, octaves=5)
    n2 = pg.value_noise(W, H, 28.0, seed=77, octaves=3)
    band = np.clip(1.0 - np.abs(yy - 300.0) / 170.0, 0.0, 1.0)
    cloud = np.clip((n * 0.8 + n2 * 0.3 - 0.52) * 3.2, 0.0, 1.0) * band
    belly = pg.hx('#2A2130')[:3].astype(np.float32)
    rgb = rgb * (1 - cloud[..., None] * 0.75) + belly * cloud[..., None] * 0.75
    lit = np.clip((n2 - 0.55) * 4.0, 0, 1) * cloud * np.clip((yy - 260.0) / 140.0, 0, 1)
    rgb = rgb * (1 - lit[..., None] * 0.5) + pg.hx('#5F6973')[:3].astype(np.float32) * lit[..., None] * 0.5
    # faint cold glow of the floodlit plaza on the horizon, centred under the dome
    glow = np.exp(-((xx - AX) / 330.0) ** 2) * np.exp(-((yy - AY) / 46.0) ** 2)
    rgb = rgb * (1 - glow[..., None] * 0.45) + pg.hx('#8F8A92')[:3].astype(np.float32) * glow[..., None] * 0.45
    below = yy > AY
    rgb[below] = pg.hx('#443B43')[:3]
    cols = ['#120C14', '#1B1520', '#211623', '#2A2130', '#25202B', '#342F37', '#443B43', '#57494D', '#454E58',
            '#5F6973', '#6E6A73', '#8F8A92']
    q = pg.quantize_rgb(rgb, [pg.hx(x) for x in cols], dither=True).astype(np.uint8)
    img = np.concatenate([q, np.full((H, W, 1), 255, np.uint8)], -1)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'sky_parade.png'))
    # fog: cold violet-grey, slightly lighter towards the horizon glow
    fk = np.clip((yy - 200.0) / (AY - 200.0), 0.0, 1.0)
    fcol = (pg.hx('#342F37')[:3] * (1 - fk[..., None]) + pg.hx('#57494D')[:3] * fk[..., None]).astype(np.float32)
    fcol = fcol * (1 - glow[..., None] * 0.5) + pg.hx('#6E6A73')[:3].astype(np.float32) * glow[..., None] * 0.5
    fcol[below] = pg.hx('#57494D')[:3]
    q = pg.quantize_rgb(fcol, [pg.hx(x) for x in ['#342F37', '#443B43', '#57494D', '#6E6A73']],
                        dither=True).astype(np.uint8)
    img = np.concatenate([q, np.full((H, W, 1), 255, np.uint8)], -1)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'fog_parade.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    atlas, meta = build_atlas()
    limp_flag(False)
    limp_flag(True)
    sky_and_fog()
    prev = os.environ.get('PARADE_PREVIEW', '')       # optional 2x preview outside the project
    if prev:
        big = Image.fromarray(atlas, 'RGBA')
        bg = Image.new('RGBA', big.size, (60, 70, 80, 255))
        bg.alpha_composite(big)
        bg.resize((big.size[0] * 2, big.size[1] * 2), Image.NEAREST).save(prev)
    print('figures', meta['atlas'], 'slots', meta['slots'])


if __name__ == '__main__':
    main()
