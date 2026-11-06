"""env_c4p2_karsk_kit -- palette, tone ramps, light hue tables, fonts and painters for L_C4P2_Karsk.

Owned by the env-karsk stream (Chapter 4 part 2, documentation/C4P2_DESIGN.md 4.1).  Builds on the tone-space
painting model of env_veltrava_hall_kit.py (TLayer, Ramps, baked light fields, bitmap fonts) and the helpers of
env_c3p2_archive_kit.py / env_c4_tunnels_kit.py -- imported read-only, never modified.  Every pixel is painted as
(ramp, tone); baked light adds tone and, where it is strong, moves a pixel onto the light's counterpart ramp at equal
luminance (sodium -> lamp / paper, floodlight -> snow).  Output is palette-pure in DEPOT below = the story stream's
placeholder palette data/chapters/c4p2.json palettes.depot (kept unchanged) + the ramps this stream adds (timber,
quilted cotton, railway navy, plum wool, the dawn sky, stone, the signal green) -- integration note: the lead copies
DEPOT into palettes.depot.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_veltrava_hall_kit as hk  # noqa: E402  (TLayer, Ramps, light fields, fonts -- read-only use)
import env_c3p2_archive_kit as ak  # noqa: E402  (bricks, grain, bevel ... -- read-only use)
import env_c4_tunnels_kit as tk  # noqa: E402  (Karsk signage glyphs, stencil font -- read-only use)

DATE = '2026-11-06'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# 'depot' = data/chapters/c4p2.json palettes.depot (story placeholder, unchanged) + the ramps of this stream
DEPOT = {
    'night': ['#07090C', '#0D1015', '#15191F', '#1F242B'],
    'brick': ['#2B1A15', '#3F261D', '#573527', '#714734', '#8C5D46'],
    'coal': ['#08080A', '#121214', '#1C1C1F', '#2A2A2E', '#3A3A3F'],
    'iron': ['#15181C', '#23282E', '#343A42', '#4A525B', '#646D76'],
    'steam': ['#5E646C', '#7F868E', '#A2A8AE', '#C6CACE', '#E8EAEC'],
    'lamp': ['#5A3216', '#8C5426', '#BA7A3A', '#E0A85A', '#F8D898'],
    'snow': ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'green': ['#1B2E28', '#28423A', '#3A5B4F', '#527766', '#6F9580'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
    # ---- added by env-karsk (round 10)
    'skin_shade': ['#5E3B38', '#E8BE98'],
    'wood': ['#1C1511', '#2B2018', '#3D2E21', '#54402D', '#6E563C', '#8C7150'],
    'quilt': ['#1A1C17', '#272A21', '#373B2E', '#4B503E', '#62684F'],
    'navy': ['#0F131D', '#182033', '#232E48', '#32405F', '#46577A'],
    'plum': ['#21161D', '#33212B', '#4A2F3B', '#64404D'],
    'dawn': ['#121826', '#1A2335', '#24304A', '#33425F', '#475879', '#617494'],
    'dusk': ['#3A3040', '#56464F', '#776060'],
    'stone': ['#26282A', '#37393A', '#4C4E4D', '#646662', '#7E807A'],
    'signal': ['#6FD49A', '#B6F2CC'],
    # ---- added by env-a (round 10 review): the town's sodium skyglow on low cloud, violet copying ink
    'skyglow': ['#272630', '#383139', '#4F3D3C', '#6B4E42', '#8C6449'],
    'violet': ['#2A2142', '#3A2E5C', '#4D3F78', '#625494'],
}
pg.PALETTES['depot'] = DEPOT


def depot_hex() -> set:
    return {h.upper() for r in DEPOT.values() for h in r}


def check_c4p2_palette() -> list[str]:
    """Differences between DEPOT and data/chapters/c4p2.json palettes.depot (integration note of this stream)."""
    p = os.path.join(ROOT, 'data', 'chapters', 'c4p2.json')
    try:
        with open(p, encoding='utf-8') as f:
            ref = json.load(f).get('palettes', {}).get('depot', {})
    except (OSError, ValueError):
        return ['c4p2.json not readable']
    notes = []
    for ramp, cols in DEPOT.items():
        if [c.upper() for c in cols] != [c.upper() for c in ref.get(ramp, [])]:
            notes.append('depot.%s not in c4p2.json yet (lead: copy DEPOT into palettes.depot)' % ramp)
    return notes


def _lum(h: str) -> float:
    return hk.lum(pg.hx(h))


def by_lum(cols: list) -> list:
    return sorted(cols, key=_lum)


D_ = DEPOT
N, K_, X_, I_, V_, L_, S_, R_, G_, P_, SK = (D_[k] for k in ('night', 'brick', 'coal', 'iron', 'steam', 'lamp', 'snow',
                                                             'red', 'green', 'paper', 'skin'))
W_, Q_, U_, M_, B_, Z_, C_, SG, SS = (D_[k] for k in ('wood', 'quilt', 'navy', 'plum', 'dawn', 'dusk', 'stone',
                                                      'signal', 'skin_shade'))
H_, O_ = D_['skyglow'], D_['violet']

RAMPS = {
    'N': [N[0], N[1], N[2], N[3]],                                              # poche / night (0..3)
    'K': [N[0], N[1], K_[0], K_[1], K_[2], K_[3], K_[4]],                       # brick (0..6)
    'X': [X_[0], X_[1], X_[2], X_[3], X_[4], I_[3], V_[1]],                     # coal, glints (0..6)
    'I': [N[0], N[1], I_[0], I_[1], I_[2], I_[3], I_[4], S_[0]],                # iron / steel (0..7)
    'S': [I_[3], I_[4], S_[0], S_[1], S_[2], S_[3], S_[4]],                     # snow / cold light (0..6)
    'V': [I_[2], V_[0], V_[1], V_[2], V_[3], V_[4], S_[4]],                     # steam / smoke (0..6)
    'L': [K_[1], L_[0], L_[1], L_[2], L_[3], L_[4]],                            # lamp light / brass (0..5)
    'P': [N[2], P_[0], P_[1], P_[2], P_[3], P_[4], S_[4]],                      # paper / linen (0..6)
    'R': [N[0], R_[0], R_[1], R_[2], R_[3], L_[3]],                             # red (0..5)
    'G': [N[0], G_[0], G_[1], G_[2], G_[3], G_[4], SG[0], SG[1]],               # green paint, signal (0..7)
    'D': [N[0], W_[0], W_[1], W_[2], W_[3], W_[4], W_[5]],                      # timber (0..6)
    'Q': [N[0], Q_[0], Q_[1], Q_[2], Q_[3], Q_[4]],                             # quilted cotton, khaki (0..5)
    'U': [N[0], U_[0], U_[1], U_[2], U_[3], U_[4]],                             # railway navy (0..5)
    'M': [N[0], M_[0], M_[1], M_[2], M_[3], K_[3]],                             # plum wool (0..5)
    'Y': [SS[0], SK[0], SK[1], SK[2], SS[1]],                                   # skin (0..4)
    'B': [N[1], B_[0], B_[1], B_[2], B_[3], B_[4], B_[5], S_[0]],               # sky, dawn (0..7)
    'Z': [B_[3], Z_[0], Z_[1], Z_[2]],                                          # dawn glow (0..3)
    'C': [N[1], C_[0], C_[1], C_[2], C_[3], C_[4], S_[1]],                      # stone / concrete (0..6)
    'W': by_lum([N[2], C_[2], P_[1], P_[2], P_[3], P_[4], S_[4]]),              # whitewash / plaster (0..6)
    'E': by_lum([N[1], X_[3], K_[0], I_[1], C_[1], W_[2]]),                     # cinders / earth (0..5)
    'H': [B_[1], H_[0], H_[1], H_[2], H_[3], H_[4], L_[2]],                     # sodium skyglow, lit smoke (0..6)
    'O': [N[1], O_[0], O_[1], O_[2], O_[3]],                                    # violet copying ink (0..4)
}
R = hk.Ramps(RAMPS)

# hue counterparts (src ramp -> ramp a pixel moves onto when the light is strong)
WARM_OF = {'S': 'P', 'V': 'P', 'C': 'P', 'W': 'P', 'I': 'D', 'N': 'D', 'K': 'L', 'P': 'L', 'X': 'D', 'E': 'D',
           'B': 'Z', 'Q': 'D', 'U': 'M'}
COLD_OF = {'D': 'I', 'P': 'S', 'L': 'P', 'W': 'S', 'N': 'I', 'K': 'C', 'C': 'S', 'I': 'S', 'E': 'C', 'X': 'I',
           'V': 'S', 'Q': 'C', 'M': 'U', 'Y': 'Y'}
GAINS = {
    'W': (2.4, 2.6, 2.4), 'C': (2.2, 2.6, 2.4), 'D': (2.4, 1.6, 2.0), 'P': (2.2, 2.2, 2.4), 'L': (2.0, 1.2, 1.8),
    'I': (2.0, 2.4, 2.2), 'K': (2.2, 1.6, 2.0), 'G': (1.8, 1.8, 1.8), 'R': (1.6, 0.8, 1.2), 'X': (1.6, 1.8, 1.8),
    'S': (1.6, 2.2, 2.0), 'N': (1.4, 1.6, 1.4), 'Y': (1.4, 0.8, 1.2), 'E': (1.4, 1.4, 1.4), 'V': (1.6, 2.0, 2.0),
    'Q': (1.8, 1.6, 1.8), 'U': (1.6, 1.8, 1.8), 'M': (1.6, 1.2, 1.4), 'B': (1.0, 1.4, 1.2), 'Z': (1.0, 0.6, 0.8),
    'H': (1.2, 0.8, 1.0), 'O': (1.4, 1.2, 1.2),
}


def tlayer(w: int, h: int, name: str = 'layer') -> 'hk.TLayer':
    return hk.TLayer(w, h, R, name, warm_of=dict(WARM_OF), cold_of=dict(COLD_OF), gains=GAINS)


def resolve(lay, fields: dict, seed: int = 0, exposure: float = 0.85, band: float = 2.2):
    """Resolve a TLayer; `exposure` scales the painted (unlit) tones of every lit pixel first (scalar, or an (h, w)
    array): the hour keeps its darks, the baked lights make the pools."""
    t0 = lay.tone.copy()
    m = ~lay.emis & ~lay.unlit
    ex = np.broadcast_to(np.asarray(exposure, np.float32), lay.tone.shape)
    lay.tone[m] = lay.tone[m] * ex[m]
    lay.resolve(fields, seed=seed, band=band)
    lay.tone = t0
    return lay


def empty_fields(h: int, w: int) -> dict:
    return {k: np.zeros((h, w), np.float32) for k in ('warm', 'cold', 'white')}


# --------------------------------------------------------------------------- re-exported helpers
light_fields = hk.light_fields
sub_fields = hk.sub_fields
add_pools = ak.add_pools
dilate, erode, edge_of, box_blur, arch_mask = hk.dilate, hk.erode, hk.edge_of, hk.box_blur, hk.arch_mask
bres, stroke_mask = hk.bres, hk.stroke_mask
noise, bevel, recess, bricks, grain, soft_box, disc = ak.noise, ak.bevel, ak.recess, ak.bricks, ak.grain, \
    ak.soft_box, ak.disc
periodic_noise = ak.periodic_noise
pseudo_text = ak.pseudo_text
cyl, sag_line = tk.cyl, tk.sag_line

# --------------------------------------------------------------------------- fonts
F35 = dict(tk.F35)
F35.update({
    'Å': ['.#.', '.#.', '#.#', '###', '#.#'], '?': ['##.', '..#', '.#.', '...', '.#.'],
    '!': ['.#.', '.#.', '.#.', '...', '.#.'], '(': ['.#', '#.', '#.', '#.', '.#'], ')': ['#.', '.#', '.#', '.#', '#.'],
    '"': ['#.#', '#.#', '...', '...', '...'], '·': ['.', '.', '#', '.', '.'], '×': ['...', '#.#', '.#.', '#.#', '...'],
    'Ц': ['#.#.', '#.#.', '#.#.', '###.', '...#'], 'Щ': ['#.#.#.', '#.#.#.', '#.#.#.', '######', '.....#'],
    'Д': ['..##.', '.#.#.', '.#.#.', '#####', '#...#'], '*': ['...', '#.#', '.#.', '#.#', '...'],
})
F57 = dict(hk.F57)
F57.update({
    'И': ['#...#', '#...#', '#..##', '#.#.#', '##..#', '#...#', '#...#'],
    'Л': ['..###', '.#..#', '.#..#', '.#..#', '.#..#', '#...#', '#...#'],
    'Д': ['..##.', '.#.#.', '.#.#.', '.#.#.', '.#.#.', '#####', '#...#'],
    'Б': ['#####', '#....', '#....', '####.', '#...#', '#...#', '####.'],
    'Г': ['#####', '#....', '#....', '#....', '#....', '#....', '#....'],
    'П': ['#####', '#...#', '#...#', '#...#', '#...#', '#...#', '#...#'],
    'Я': ['.####', '#...#', '#...#', '.####', '..#.#', '.#..#', '#...#'],
    'Ы': ['#...#', '#...#', '#...#', '###.#', '#..##', '#..##', '###.#'],
    'У': ['#...#', '#...#', '#...#', '.####', '....#', '#...#', '.###.'],
    'Х': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Ж': ['#.#.#', '#.#.#', '.###.', '..#..', '.###.', '#.#.#', '#.#.#'],
    'Ч': ['#...#', '#...#', '#...#', '.####', '....#', '....#', '....#'],
    'Ш': ['#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#####'],
    'Ь': ['#....', '#....', '#....', '####.', '#...#', '#...#', '####.'],
    'Ю': ['#..#.', '#.#.#', '#.#.#', '###.#', '#.#.#', '#.#.#', '#..#.'],
    'Э': ['.###.', '#...#', '....#', '..###', '....#', '#...#', '.###.'],
    'Ф': ['..#..', '.###.', '#.#.#', '#.#.#', '.###.', '..#..', '..#..'],
    '4': ['#..#.', '#..#.', '#..#.', '#####', '...#.', '...#.', '...#.'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '..#..', '..#..', '..#..'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '/': ['....#', '...#.', '...#.', '..#..', '.#...', '.#...', '#....'],
})
for _c, _l in (('А', 'A'), ('В', 'B'), ('Е', 'E'), ('К', 'K'), ('М', 'M'), ('Н', 'H'), ('О', 'O'), ('Р', 'P'),
               ('С', 'C'), ('Т', 'T')):
    F57[_c] = F57[_l]

# Readability (round-10 art review): in the shared 3x5 table „4“ was the same glyph as „Ч“ (the order read „НАРЯД № Ч5/С“,
# „19.Ч0“) and „Й“ had no breve („СПЕЦРЕИС“).  Here „4“ gets its open diagonal form, and the close-up / sign renderers
# draw from the overhang tables: „Й“ with its breve one row ABOVE the cap line over a full-height „И“, the distinct
# umlauts of pixfont_umlauts (dots above the cap line) -- the same convention as round 9's Ä / Ö / Ü.
F35['4'] = ['..#', '.##', '#.#', '###', '..#']
import pixfont_umlauts as _UML  # noqa: E402
F35_OH = _UML.install(dict(F35), 5)
F35_OH['Й'] = ['.##.'] + list(F35['И'])                                  # breve + the 4-wide И (5 rows)
F57_OH = _UML.install(dict(F57), 7)
F57_OH['Й'] = ['.###.'] + list(F57['И'])
assert F35['4'] != F35['Ч'] and F35_OH['Й'] != F35_OH['И'] and F57_OH['Й'] != F57_OH['И']


def _glyph(f, ch):
    return f.get(ch, f.get(ch.upper(), f[' ']))


def text_mask(s: str, font: str = '35', spacing: int = 1, overhang: bool = False) -> np.ndarray:
    """Bitmap of a string.  overhang=True: tall glyphs (Й with its breve, the distinct umlauts) keep their marks;
    the mask then has that many rows more at the TOP (text() / worn_text() draw them above the given cap line).
    Without overhang a tall glyph is cut to its bottom rows (the plain letter)."""
    if overhang and font in ('35', '57'):
        f = F35_OH if font == '35' else F57_OH
    else:
        f = {'35': F35, '57': F57, '57s': tk.F57S}[font]
    gh = 5 if font == '35' else 7
    if font != '57s':
        s = s.upper()
    if not s:
        return np.zeros((gh, 0), bool)
    glyphs = [_glyph(f, ch) for ch in s]
    extra = max(0, max(len(g) for g in glyphs) - gh) if overhang else 0
    widths = [max(len(r) for r in g) for g in glyphs]
    w = sum(widths) + spacing * (len(s) - 1)
    m = np.zeros((gh + extra, w), bool)
    x = 0
    for g, gw in zip(glyphs, widths):
        rows = g if overhang else g[-gh:]
        top = extra + gh - len(rows)
        for yy, row in enumerate(rows):
            for xx, c in enumerate(row):
                if c == '#':
                    m[top + yy, x + xx] = True
        x += gw + spacing
    return m


def text_overhang(s: str, font: str = '35') -> int:
    """Rows a string's marks reach above the cap line (0 without Й / umlauts)."""
    return int(text_mask(s, font, 1, overhang=True).shape[0]) - (5 if font == '35' else 7)


def text_width(s: str, font: str = '35', spacing: int = 1) -> int:
    return int(text_mask(s, font, spacing).shape[1])


def text(lay, s, x, y, ramp, tone, font='35', spacing=1, center=False, **kw):
    m = text_mask(s, font, spacing, overhang=font in ('35', '57'))
    if center:
        x = int(round(x - m.shape[1] / 2))
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    lay.put(m, x, y - (m.shape[0] - (5 if font == '35' else 7)), ramp, tone, **kw)
    return m.shape[1]


def worn_text(lay, s, x, y, ramp, tone, font='35', wear=0.25, seed=0, ghost=None, center=False, spacing=1, **kw):
    """Weathered paint: a share of the stroke pixels drops out (or turns into `ghost` = (ramp, tone))."""
    m = text_mask(s, font, spacing, overhang=font in ('35', '57'))
    if center:
        x = int(round(x - m.shape[1] / 2))
    y = y - (m.shape[0] - (5 if font == '35' else 7))
    rng = np.random.default_rng(abs(int(seed)))
    keep = m & (rng.random(m.shape) >= wear)
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    if ghost is not None:
        lay.put(m & ~keep, x, y, ghost[0], ghost[1], **kw)
    lay.put(keep, x, y, ramp, tone, **kw)
    return m.shape[1]


# --------------------------------------------------------------------------- generic painters
def nz(w, h, cell, seed, octaves=3):
    """Value noise in [-0.5, 0.5] (w, h >= 2)."""
    return pg.value_noise(max(2, int(w)), max(2, int(h)), cell, abs(int(seed)) % 2147483647, octaves=octaves) - 0.5


def tex_rect(lay, x, y, w, h, ramp, base, seed=0, amp=0.5, cell=4.0, hgt=0.3, mask=None, crisp=False):
    """A noisy surface: base tone +- amp of value noise."""
    w, h = int(w), int(h)
    if w <= 0 or h <= 0:
        return
    t = base + nz(w, h, cell, seed) * amp * 2
    m = np.ones((h, w), bool) if mask is None else mask
    lay.put(m, x, y, ramp, t, hgt=hgt, flat=False, crisp=crisp)


def brick_wall(lay, x, y, w, h, base=3.6, seed=0, soot=0.5, ramp='K', course=4, length=8, relief=0.14, mask=None):
    """Stretcher-bond brick with soot from the top and damp from the bottom (tone noise over the bricks)."""
    w, h = int(w), int(h)
    if w <= 0 or h <= 0:
        return
    bricks(lay, x, y, w, h, ramp, base, seed=seed, course=course, length=length, joint=-0.7, var=0.32, hgt=relief,
           mask=mask)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    n = nz(w, h, 9, seed + 3)
    dt = -soot * (1 - yy) ** 2 * (1.0 + n) - 0.5 * np.clip(yy - 0.82, 0, 1) * 5 * (0.6 + n)
    m = np.ones((h, w), bool) if mask is None else mask
    X0, Y0 = max(0, int(x)), max(0, int(y))
    X1, Y1 = min(lay.w, int(x) + w), min(lay.h, int(y) + h)
    if X1 > X0 and Y1 > Y0:
        sub = (slice(Y0 - int(y), Y1 - int(y)), slice(X0 - int(x), X1 - int(x)))
        mm = m[sub] & (lay.rid[Y0:Y1, X0:X1] >= 0)
        lay.tone[Y0:Y1, X0:X1][mm] += dt[sub][mm]


def planks(lay, x, y, w, h, ramp='D', base=3.0, seed=0, pitch=5, vertical=True, gap=-1.2, var=0.35, hgt=0.35):
    """Board wall / deck: boards of `pitch` px with dark gaps, each board its own tone, grain inside."""
    w, h = int(w), int(h)
    if w <= 0 or h <= 0:
        return
    rng = np.random.default_rng(abs(int(seed)))
    grain(lay, x, y, w, h, ramp, base, seed=seed, amp=0.35, vertical=vertical, hgt=hgt)
    n = (w if vertical else h)
    for k in range(0, n, pitch):
        dv = float(rng.normal(0, var))
        if vertical:
            lay.shade_rect(x + k, y, min(pitch - 1, w - k), h, dv)
            if k > 0:
                lay.rect(x + k - 1, y, 1, h, ramp, base + gap, hgt=0.0, flat=True)
        else:
            lay.shade_rect(x, y + k, w, min(pitch - 1, h - k), dv)
            if k > 0:
                lay.rect(x, y + k - 1, w, 1, ramp, base + gap, hgt=0.0, flat=True)


def snowcap(lay, x, y, w, depth=2, seed=0, base=4.6, ramp='S', drift=0.0, hgt=0.7):
    """Snow lying on a top edge at row y (the snow sits ON y, rising `depth` px above it, wavy; optional drift
    thickens it to one side: drift > 0 = deeper to the right)."""
    w = int(w)
    if w <= 0:
        return
    rng = np.random.default_rng(abs(int(seed)))
    nn = nz(w + 2, 2, 6, seed, octaves=2)[0]
    for i in range(w):
        u = i / max(1, w - 1)
        d = depth + nn[i] * 2.0 + drift * (u if drift > 0 else (1 - u)) * abs(drift)
        d = int(round(max(1.0, d)))
        for k in range(d):
            t = base - 0.5 * (k / max(1, d)) + (0.4 if k == d - 1 else 0.0)
            lay.px(x + i, y - k, ramp, t, hgt=hgt)
        if rng.random() < 0.08:
            lay.px(x + i, y + 1, ramp, base - 1.0, hgt=hgt * 0.6)       # a crumb hanging over the edge


def icicles(lay, x0, x1, y, seed=0, density=0.3, maxlen=5, ramp='S'):
    """Icicles hanging below row y, grouped where the meltwater runs."""
    rng = np.random.default_rng(abs(int(seed)))
    w = max(2, int(x1 - x0))
    n = nz(w, 2, 5, seed + 7, octaves=2)[0] + 0.5
    x = int(x0)
    while x < x1:
        v = n[min(w - 1, x - int(x0))]
        if rng.random() < density * (0.4 + v):
            ln = 1 + int(round((maxlen - 1) * v ** 1.6 * rng.uniform(0.6, 1.0)))
            for k in range(ln):
                lay.px(x, y + k, ramp, 4.6 - 1.2 * k / max(1, ln), hgt=0.6)
            if ln >= 3:
                lay.px(x, y + ln - 2, ramp, 5.8, hgt=0.7)
            x += 2 if ln >= 3 else 1
        x += 1


def rust_streak(lay, x, y, length, seed=0, ramp='K', tone=3.4):
    rng = np.random.default_rng(abs(int(seed)))
    for k in range(int(length)):
        u = k / max(1, length - 1)
        if rng.random() < 0.15 + 0.5 * u:
            continue
        lay.px(x, y + k, ramp, tone - 1.4 * u)


def window(lay, x, y, w, h, lit=True, rows=2, cols=2, frame=('D', 2.2), glass=('L', 4.0), seed=0, curtain=None,
           sill_snow=True, frost=0.3, emis=True, glow=None):
    """A window with frame, mullions, glowing (emissive) or dark glass, frost in the corners, a snowy sill.
    `glow` = (ramp, tone) of the lit glass; curtain = (ramp, tone, side 'l'|'r'|'both')."""
    fr, ft = frame
    lay.rect(x - 1, y - 1, w + 2, h + 2, fr, ft - 0.8, hgt=0.5)
    gr, gt = glow if glow else glass
    if lit:
        t = np.full((h, w), gt, np.float32)
        yy = np.linspace(0, 1, h)[:, None]
        t = t - 0.8 * yy + nz(w, h, 3, seed) * 0.6
        lay.put(np.ones((h, w), bool), x, y, gr, t, emis=emis, flat=False, hgt=-0.2)
    else:
        lay.vgrad(x, y, w, h, 'N', 2.4, 1.2, hgt=-0.2)
        lay.rect(x, y, max(1, w // 3), 1, 'S', 2.0)                     # a cold reflection
    if curtain:
        cr, ct, side = curtain
        cw = max(2, w // 3)
        if side in ('l', 'both'):
            lay.rect(x, y, cw, h, cr, ct, emis=emis and lit)
            lay.vline(x + cw - 1, y, h, cr, ct - 0.6, emis=emis and lit)
        if side in ('r', 'both'):
            lay.rect(x + w - cw, y, cw, h, cr, ct, emis=emis and lit)
            lay.vline(x + w - cw, y, h, cr, ct - 0.6, emis=emis and lit)
    for c in range(1, cols):
        mx = x + round(c * w / cols) - 1
        lay.rect(mx, y, 1, h, fr, ft, hgt=0.5)
    for r in range(1, rows):
        my = y + round(r * h / rows) - 1
        lay.rect(x, my, w, 1, fr, ft, hgt=0.5)
    if frost > 0:
        rng = np.random.default_rng(abs(int(seed)) + 5)
        for (cx, cy) in ((x, y + h - 1), (x + w - 1, y + h - 1)):
            for k in range(int(4 + frost * 6)):
                dx_ = int(rng.integers(0, 3))
                px_ = cx + dx_ if cx == x else cx - dx_
                py_ = cy - int(rng.integers(0, 3 - dx_ // 2))
                lay.px(px_, py_, 'S', 4.4 if not lit else 5.0, emis=False)
    lay.rect(x - 2, y + h + 1, w + 4, 2, fr, ft + 0.4, hgt=0.6)        # sill
    if sill_snow:
        snowcap(lay, x - 2, y + h + 1, w + 4, depth=2, seed=seed + 9)


def wire(lay, x0, y0, x1, y1, sag, ramp='N', tone=1.4):
    for (x, y) in pg.catenary(x0, y0, x1, y1, sag):
        lay.px(int(round(x)), int(round(y)), ramp, tone, hgt=0.3)


def lamp_head(lay, x, y, kind='enamel', lit=True, ramp_glow='L'):
    """A street/yard lamp head at (x, y) = bulb centre; returns nothing (the light is added by the caller)."""
    if kind == 'enamel':                                     # enamel cone shade, bulb under it
        lay.poly([(x - 5, y - 1), (x + 5, y - 1), (x + 2, y - 4), (x - 2, y - 4)], 'I', 3.0, hgt=0.6)
        lay.rect(x - 5, y - 1, 11, 1, 'S', 3.6)
        lay.rect(x - 1, y - 5, 3, 1, 'I', 2.0)
        if lit:
            lay.rect(x - 1, y, 3, 2, ramp_glow, 5.0, emis=True)
            lay.px(x, y + 2, ramp_glow, 4.0, emis=True)
    elif kind == 'flood':                                    # floodlight box, tilted down
        lay.poly([(x - 4, y - 3), (x + 4, y - 4), (x + 5, y + 2), (x - 4, y + 3)], 'I', 2.4, hgt=0.6)
        if lit:
            lay.poly([(x - 3, y + 1), (x + 4, y), (x + 4, y + 2), (x - 3, y + 3)], ramp_glow, 5.0, emis=True)


def crate(lay, x, y, w, h, ramp='D', base=2.8, seed=0, snow=True):
    lay.rect(x, y, w, h, ramp, base, hgt=0.5)
    grain(lay, x + 1, y + 1, w - 2, h - 2, ramp, base, seed=seed, amp=0.3)
    lay.rect(x, y, w, 1, ramp, base + 1.0, hgt=0.6)
    lay.rect(x, y + h - 1, w, 1, ramp, base - 1.0)
    lay.rect(x + w - 1, y, 1, h, ramp, base - 0.8)
    lay.line(x + 1, y + h - 2, x + w - 2, y + 1, ramp, base - 0.6)        # diagonal brace
    if snow:
        snowcap(lay, x, y, w, depth=2, seed=seed + 1)


def barrel(lay, x, y, w, h, ramp='I', base=3.0, seed=0, hoops=2, snow=False):
    """Steel drum standing; x, y = top-left."""
    for i in range(w):
        c = (i + 0.5) / w * 2 - 1
        t = base + 1.2 * (0.45 - abs(c + 0.3))
        lay.rect(x + i, y, 1, h, ramp, t, hgt=0.7 * math.sqrt(max(0.0, 1 - c * c)))
    for k in range(hoops):
        yy = y + int(round((k + 1) * h / (hoops + 1)))
        lay.rect(x, yy, w, 1, ramp, base + 1.4, hgt=0.8)
    lay.rect(x, y, w, 1, ramp, base + 1.8, hgt=0.8)
    rng = np.random.default_rng(abs(int(seed)))
    for k in range(3):
        rust_streak(lay, x + int(rng.integers(1, max(2, w - 1))), y + 1, int(rng.integers(3, max(4, h - 2))),
                    seed=seed + k, tone=3.0)
    if snow:
        snowcap(lay, x, y, w, depth=2, seed=seed + 3)


def coal_heap(lay, cx, base, w, h, seed=0, glint=0.05, snow=0.0, ramp='X'):
    """A heap of coal lumps: an uneven mound (cx = centre, base = ground row), lumpy tone + relief, glints."""
    w, h = int(w), int(h)
    rng = np.random.default_rng(abs(int(seed)))
    xs = np.arange(w)
    u = (xs - (w - 1) / 2) / max(1.0, (w - 1) / 2)
    prof = h * np.clip(1 - u * u, 0, 1) ** 0.75 * (1 + nz(w, 2, 7, seed)[0] * 0.5)
    m = np.zeros((h + 2, w), bool)
    for i in range(w):
        top = int(round(h + 1 - prof[i]))
        m[max(0, top):, i] = True
    lumps = nz(w, h + 2, 1.6, seed + 1, octaves=2)
    t = 2.3 + lumps * 2.4
    yy = np.linspace(0, 1, h + 2)[:, None]
    t = t - yy * 0.6
    hg = np.clip(0.4 + lumps * 1.2, 0, 1)
    x0, y0 = int(cx - w // 2), int(base - h - 1)
    lay.put(m, x0, y0, ramp, t, hgt=hg, flat=False)
    g = m & (rng.random(m.shape) < glint)
    lay.put(g, x0, y0, ramp, 5.4, crisp=True, hgt=0.9)
    if snow > 0:
        top_m = m & ~np.roll(m, 1, axis=0)
        sm = top_m & (rng.random(m.shape) < snow)
        lay.put(sm, x0, y0, 'S', 4.4, hgt=0.8)
    return m, x0, y0


def ground(lay, x, y, w, h, seed=0, snow=0.55, ramp_snow='S', ramp_cinder='E', tracks=None):
    """Yard floor: trodden snow over cinders, darker paths where people walk (`tracks` = [(x0, x1, dark)])."""
    w, h = int(w), int(h)
    n1 = nz(w, h, 6, seed, octaves=3)
    n2 = nz(w, h, 2, seed + 1, octaves=2)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    cover = snow + n1 * 0.9 - 0.25 * yy * 0
    sm = cover > 0.0
    t_s = 3.2 + n2 * 1.0 + (1 - yy) * 0.2
    t_c = 2.2 + n2 * 1.6
    lay.put(~sm, x, y, ramp_cinder, t_c, hgt=0.2, flat=False)
    lay.put(sm, x, y, ramp_snow, t_s, hgt=0.35, flat=False)
    if tracks:
        for (a, b, dark) in tracks:
            a, b = int(a), int(b)
            if b <= a:
                continue
            nn = nz(b - a, h, 3, seed + 11 + a)
            mk = (nn + 0.5) < dark
            lay.put(mk, x + a - int(x), y, ramp_cinder, 2.0 + nn * 1.4, hgt=0.15, flat=False)
    return sm


def footprints(lay, x0, x1, y0, y1, seed=0, n=40, ramp='E', tone=1.6):
    rng = np.random.default_rng(abs(int(seed)))
    for _ in range(n):
        x = int(rng.integers(x0, x1))
        y = int(rng.integers(y0, y1))
        lay.rect(x, y, 2, 1, ramp, tone)


def sign_plate(lay, x, y, w, h, bg=('P', 4.6), fg=('N', 1.0), lines=(), font='35', border=True, wear=0.0, seed=0,
               emis=False):
    """Enamel / painted plate with centred text lines."""
    lay.rect(x, y, w, h, bg[0], bg[1], hgt=0.4, emis=emis)
    if border:
        lay.rect(x, y, w, 1, fg[0], fg[1] + 0.4)
        lay.rect(x, y + h - 1, w, 1, fg[0], fg[1] + 0.4)
        lay.rect(x, y, 1, h, fg[0], fg[1] + 0.4)
        lay.rect(x + w - 1, y, 1, h, fg[0], fg[1] + 0.4)
    gh = 5 if font == '35' else 7
    total = len(lines) * (gh + 2) - 2
    yy = y + (h - total) // 2
    for i, s in enumerate(lines):
        if wear > 0:
            worn_text(lay, s, x + w // 2, yy + i * (gh + 2), fg[0], fg[1], font=font, wear=wear, seed=seed + i,
                      center=True, emis=emis)
        else:
            text(lay, s, x + w // 2, yy + i * (gh + 2), fg[0], fg[1], font=font, center=True, emis=emis)


def light(name, x, y, kind='warm', energy=1.0, radius=80, height=20, **kw):
    d = {'name': name, 'pos': (float(x), float(y)), 'kind': kind, 'energy': float(energy), 'radius': float(radius),
         'height': float(height)}
    d.update(kw)
    return d


# --------------------------------------------------------------------------- palette helpers
_PAL = None


def pal_array():
    global _PAL
    if _PAL is None:
        _PAL = np.array([pg.hx(h)[:3] for h in sorted(depot_hex())], np.int32)
    return _PAL


def snap(rgb: np.ndarray) -> np.ndarray:
    """Nearest 'depot' palette colour for an (..., 3) array."""
    pal = pal_array()
    flat = rgb.reshape(-1, 3).astype(np.int32)
    out = np.empty((flat.shape[0], 3), np.uint8)
    for i in range(0, flat.shape[0], 65536):
        d = ((flat[i:i + 65536, None, :] - pal[None, :, :]) ** 2).sum(-1)
        out[i:i + 65536] = pal[np.argmin(d, axis=1)]
    return out.reshape(rgb.shape)


def ramp_rgba(ramp: str, t: np.ndarray, alpha: np.ndarray, seed=0, x0=0, y0=0) -> np.ndarray:
    """Dithered palette colours of `ramp` at float tones t (h, w) with alpha (h, w) uint8."""
    cols = R.table[R[ramp], :R.n(ramp)]
    h, w = t.shape
    thr = pg.bayer(w, h, x0 + seed, y0 + seed, 4)
    fl = np.floor(t)
    idx = np.clip(fl + ((t - fl) > thr), 0, R.n(ramp) - 1).astype(np.int32)
    out = cols[idx].copy()
    out[..., 3] = alpha
    out[alpha == 0] = 0
    return out


def rgba(ramp: str, idx: int, a: int = 255) -> np.ndarray:
    c = R.color(ramp, idx).copy()
    c[3] = a
    return c


def palette_report(arr: np.ndarray) -> tuple[int, list]:
    a = arr[..., 3] > 0
    cols = {'#%02X%02X%02X' % tuple(int(v) for v in c[:3]) for c in arr[a].reshape(-1, 4)}
    allowed = depot_hex()
    return len(cols), sorted(c for c in cols if c not in allowed)
