"""env_c4_tunnels_kit -- palette, super-ramps, light hue tables, fonts and small painters for L_C4_Tunnels.

Owned by the env-tunnels stream (Chapter 4 part 1, documentation/C4_DESIGN.md 4.1).  Builds on tools/pixelgen/pg.py,
the tone-space painting model of env_veltrava_hall_kit.py (TLayer, Ramps, baked light fields, bitmap fonts) and the
masonry / wood helpers of env_c3p2_archive_kit.py -- imported read-only, never modified.  Every pixel is painted as
(ramp, tone); baked light adds tone and, where it is strong, moves a pixel onto the light's counterpart ramp at equal
luminance (lamp -> paper / amber, work lamp -> concrete / snow).  Output is palette-pure in the 'tunnels' palette
below (checked at build time against data/chapters/c4.json; the two added ramps -- 'green' for the oil paint and
Lev's lamp shade, 'concrete' for the 1941 tube -- are the Karsk teal / stone ramps of Chapter 1, so Karsk stays one
city across chapters).
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

DATE = '2026-11-06'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# 'tunnels' = data/chapters/c4.json palettes.tunnels (story placeholder) + 'green' + 'concrete' (Karsk, Chapter 1)
TUN = {
    'night': ['#07080B', '#0D0F13', '#15171C', '#1E2128'],
    'brick': ['#2A1712', '#3E2219', '#563124', '#704332', '#8C5A45'],
    'iron': ['#15171C', '#22262D', '#323840', '#464D55', '#5E666E'],
    'lamp': ['#5A3216', '#8C5426', '#BA7A3A', '#E0A85A', '#F8D898'],
    'wagon': ['#2E140E', '#4A2016', '#68301F', '#86422C', '#A3583C'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'snow': ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
    'green': ['#1B3033', '#26403F', '#36534D', '#4A675C', '#6C7A62', '#9DAF91'],
    'concrete': ['#2A2D2C', '#3B3F3B', '#4F534C', '#666A60', '#7F8275', '#9A9B8B'],
}
pg.PALETTES['tunnels'] = TUN


def tun_hex() -> set:
    return {h.upper() for r in TUN.values() for h in r}


def check_c4_palette() -> list[str]:
    """Differences between TUN and data/chapters/c4.json palettes.tunnels (integration note of this stream)."""
    p = os.path.join(ROOT, 'data', 'chapters', 'c4.json')
    try:
        with open(p, encoding='utf-8') as f:
            ref = json.load(f).get('palettes', {}).get('tunnels', {})
    except (OSError, ValueError):
        return ['c4.json not readable']
    notes = []
    for ramp, cols in TUN.items():
        if [c.upper() for c in cols] != [c.upper() for c in ref.get(ramp, [])]:
            notes.append('tunnels.%s differs from c4.json (lead: copy TUN into palettes.tunnels)' % ramp)
    return notes


def _lum(h: str) -> float:
    return hk.lum(pg.hx(h))


def by_lum(cols: list) -> list:
    return sorted(cols, key=_lum)


N, K_, I_, L_, WG, P_, S_, R_, SK, G_, C_ = (TUN[k] for k in ('night', 'brick', 'iron', 'lamp', 'wagon', 'paper',
                                                              'snow', 'red', 'skin', 'green', 'concrete'))

RAMPS = {
    'N': [N[0], N[1], N[2], N[3]],                                                  # poche / night (0..3)
    'K': [N[0], N[1], K_[0], K_[1], K_[2], K_[3], K_[4]],                           # brick (0..6)
    'W': by_lum([N[1], N[3], C_[1], C_[2], P_[0], P_[1], P_[2], P_[3], P_[4]]),       # limewash (0..8)
    'D': by_lum([N[0], K_[0], WG[0], K_[1], L_[0], K_[2], L_[1], K_[3]]),           # wood, stained (0..7)
    'L': [K_[1], L_[0], L_[1], L_[2], L_[3], L_[4]],                                 # lamp light / brass (0..5)
    'P': [N[2], P_[0], P_[1], P_[2], P_[3], P_[4], S_[4]],                           # paper (0..6)
    'I': [N[0], N[1], I_[0], I_[1], I_[2], I_[3], I_[4], S_[0]],                     # iron / steel (0..7)
    'C': [N[1], C_[0], C_[1], C_[2], C_[3], C_[4], C_[5], S_[1]],                    # concrete (0..7)
    'G': [N[0], G_[0], G_[1], G_[2], G_[3], G_[4], G_[5]],                           # oil green / lamp shade (0..6)
    'R': [N[0], R_[0], R_[1], R_[2], R_[3], L_[3]],                                  # red (0..5)
    'V': [N[0], WG[0], WG[1], WG[2], WG[3], WG[4], R_[3]],                           # wagon red-brown (0..6)
    'S': [I_[3], I_[4], S_[0], S_[1], S_[2], S_[3], S_[4]],                          # snow / cold light (0..6)
    'Y': [SK[0], SK[1], SK[2]],                                                     # skin (0..2)
    'E': by_lum([N[1], N[2], K_[0], C_[0], K_[1], C_[1], I_[1]]),                   # earth / soil section (0..6)
}
R = hk.Ramps(RAMPS)

# hue counterparts (src ramp -> ramp a pixel moves onto when the light is strong)
WARM_OF = {'W': 'P', 'C': 'P', 'S': 'P', 'I': 'D', 'N': 'D', 'K': 'L', 'P': 'L', 'E': 'D', 'V': 'R'}
COLD_OF = {'D': 'I', 'P': 'S', 'L': 'P', 'W': 'S', 'N': 'I', 'K': 'C', 'G': 'C', 'C': 'S', 'I': 'S', 'E': 'C',
           'Y': 'Y'}
GAINS = {
    'W': (2.4, 2.6, 2.4), 'C': (2.2, 2.6, 2.4), 'D': (2.4, 1.4, 2.0), 'P': (2.2, 2.2, 2.4), 'L': (2.0, 1.2, 1.8),
    'I': (2.0, 2.4, 2.2), 'K': (2.2, 1.6, 2.0), 'G': (1.8, 1.6, 1.8), 'R': (1.6, 0.8, 1.2), 'V': (1.8, 1.2, 1.6),
    'S': (1.6, 2.2, 2.0), 'N': (1.4, 1.6, 1.4), 'Y': (1.0, 0.6, 1.0), 'E': (1.2, 1.2, 1.2),
}


def tlayer(w: int, h: int, name: str = 'layer') -> 'hk.TLayer':
    return hk.TLayer(w, h, R, name, warm_of=dict(WARM_OF), cold_of=dict(COLD_OF), gains=GAINS)


def resolve(lay, fields: dict, seed: int = 0, exposure: float = 0.85):
    """Resolve a TLayer; `exposure` scales the painted (unlit) tones of every lit pixel first: the night keeps its
    darks, the baked lights make the pools."""
    t0 = lay.tone.copy()
    m = ~lay.emis & ~lay.unlit
    lay.tone[m] = lay.tone[m] * exposure
    lay.resolve(fields, seed=seed)
    lay.tone = t0
    return lay


# --------------------------------------------------------------------------- re-exported helpers
light_fields = hk.light_fields
sub_fields = hk.sub_fields
add_pools = ak.add_pools
dilate, erode, edge_of, box_blur, arch_mask = hk.dilate, hk.erode, hk.edge_of, hk.box_blur, hk.arch_mask
bres, stroke_mask = hk.bres, hk.stroke_mask
noise, bevel, recess, bricks, grain, soft_box, disc = ak.noise, ak.bevel, ak.recess, ak.bricks, ak.grain, \
    ak.soft_box, ak.disc
periodic_noise = ak.periodic_noise
rivets = ak.rivets


# --------------------------------------------------------------------------- fonts
# 3x5 signage font of the hall kit + the glyphs the Karsk signs need (Щ, №, Ё, Ъ, the arrows)
F35 = dict(hk.F35)
F35.update({
    'Щ': ['#.#.#.', '#.#.#.', '#.#.#.', '######', '.....#'],
    '№': ['#..#...', '##.#.#.', '#.##.#.', '#..#.#.', '#..#...'],
    'Ъ': ['##..', '.#..', '.##.', '.#.#', '.##.'],
    '←': ['..#..', '.#...', '#####', '.#...', '..#..'],
    '→': ['..#..', '...#.', '#####', '...#.', '..#..'],
    '–': ['....', '....', '####', '....', '....'],
    '«': ['...', '.##', '#..', '.##', '...'], '»': ['...', '##.', '..#', '##.', '...'],
})
# 5x7 stencil font of the wagon numbers (open counters bridged like a tin stencil)
F57S = {
    '0': ['.###.', '#...#', '#...#', '.....', '#...#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['####.', '....#', '....#', '.##..', '....#', '....#', '####.'],
    '4': ['#..#.', '#..#.', '#..#.', '#####', '...#.', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['.###.', '#....', '#....', '.###.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '..#..', '..#..', '..#..'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.###.', '....#', '....#', '.###.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'С': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    '-': ['....', '....', '....', '####', '....', '....', '....'],
    '/': ['....#', '...#.', '...#.', '..#..', '.#...', '.#...', '#....'],
    ' ': ['...'] * 7,
}


def _glyph(f, ch):
    return f.get(ch, f.get(ch.upper(), f[' ']))


def text_mask(s: str, font: str = '35', spacing: int = 1) -> np.ndarray:
    f = {'35': F35, '57': hk.F57, '57s': F57S}[font]
    gh = 5 if font == '35' else 7
    if font != '57s':
        s = s.upper()
    if not s:
        return np.zeros((gh, 0), bool)
    widths = [max(len(r) for r in _glyph(f, ch)) for ch in s]
    w = sum(widths) + spacing * (len(s) - 1)
    m = np.zeros((gh, w), bool)
    x = 0
    for ch, gw in zip(s, widths):
        for yy, row in enumerate(_glyph(f, ch)):
            for xx, c in enumerate(row):
                if c == '#':
                    m[yy, x + xx] = True
        x += gw + spacing
    return m


def text_width(s: str, font: str = '35', spacing: int = 1) -> int:
    return int(text_mask(s, font, spacing).shape[1])


def text(lay, s, x, y, ramp, tone, font='35', spacing=1, center=False, **kw):
    m = text_mask(s, font, spacing)
    if center:
        x = int(round(x - m.shape[1] / 2))
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    lay.put(m, x, y, ramp, tone, **kw)
    return m.shape[1]


def worn_text(lay, s, x, y, ramp, tone, font='35', wear=0.25, seed=0, ghost=None, center=False, **kw):
    """Weathered paint: a share of the stroke pixels drops out (or turns into `ghost` = (ramp, tone))."""
    m = text_mask(s, font)
    if center:
        x = int(round(x - m.shape[1] / 2))
    rng = np.random.default_rng(seed)
    keep = m & (rng.random(m.shape) >= wear)
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    if ghost is not None:
        lay.put(m & ~keep, x, y, ghost[0], ghost[1], **kw)
    lay.put(keep, x, y, ramp, tone, **kw)
    return m.shape[1]


def cyl(lay, x, y, w, h, ramp, tone, hgt=0.6, axis='h', amp=1.2, **kw):
    """A pipe / pole / cable: tone + relief rounded across its thickness."""
    if axis == 'h':
        for i in range(h):
            c = (i + 0.5) / h * 2 - 1
            lay.rect(x, y + i, w, 1, ramp, tone + amp * (0.5 - abs(c + 0.35)), hgt=hgt * math.sqrt(max(0, 1 - c * c)),
                     **kw)
    else:
        for i in range(w):
            c = (i + 0.5) / w * 2 - 1
            lay.rect(x + i, y, 1, h, ramp, tone + amp * (0.5 - abs(c + 0.35)), hgt=hgt * math.sqrt(max(0, 1 - c * c)),
                     **kw)


def sag_line(lay, x0, x1, y, sag, ramp, tone, hgt=0.5, thick=1, **kw):
    """A hanging cable between two hooks (parabolic sag)."""
    for x in range(int(x0), int(x1) + 1):
        u = (x - x0) / max(1.0, (x1 - x0))
        yy = int(round(y + sag * 4 * u * (1 - u)))
        lay.rect(x, yy, 1, thick, ramp, tone, hgt=hgt, **kw)


# --------------------------------------------------------------------------- palette helpers
_PAL = None


def pal_array():
    global _PAL
    if _PAL is None:
        _PAL = np.array([pg.hx(h)[:3] for h in sorted(tun_hex())], np.int32)
    return _PAL


def snap(rgb: np.ndarray) -> np.ndarray:
    """Nearest 'tunnels' palette colour for an (..., 3) array."""
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
    allowed = tun_hex()
    return len(cols), sorted(c for c in cols if c not in allowed)
