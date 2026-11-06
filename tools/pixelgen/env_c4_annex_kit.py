"""env_c4_annex_kit -- palette, super-ramps, hue tables and small painters for L_C4_Annex (Chapter 4 part 1).

Owned by the env-annex stream.  Same tone-space painting model as the registry (env_c3p2_archive_kit, built on
env_veltrava_hall_kit.TLayer / Ramps / light fields -- imported read-only): every pixel is painted as
(ramp, tone); baked light adds tone and, where it is strong, moves a pixel onto the light's counterpart ramp at
equal luminance.  Two hue worlds share one palette:
  * the street at dawn (loop layers): blue dawn plaster and snow, sodium light turns snow and stone yellow-cream,
  * the annex (hall layer): fluorescent tubes turn concrete, steel and paint pale green-white, one warm lamp.
Output is palette-pure in the 'annex' palette of data/chapters/c4.json plus the proposed 'lamp' ramp
(sodium lamp, lit windows, the counter lamp -- see ANNEX_EXTRA; checked at build time and by the art test).
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
import env_c3p2_archive_kit as AK  # noqa: E402  (generic painters: bevel, recess, frame, bricks, grain ...)

DATE = '2026-11-06'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# 'annex' = data/chapters/c4.json palettes.annex (binding, compared at build time)
ANNEX_C4 = {
    'night': ['#06080C', '#0B1016', '#121A22', '#1A242E'],
    'concrete': ['#2A2C2E', '#3C3F42', '#525659', '#6B7073', '#8A8F91', '#A9AEAF'],
    'steel': ['#1C2228', '#2A323A', '#3B4650', '#526070', '#6E7D8C'],
    'fluor': ['#2A3A30', '#3E5444', '#5A7660', '#86A28A', '#C4D8C4'],
    'dawn': ['#3A4256', '#56607A', '#7A829C', '#A3A8BC', '#D0CED8'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'snow': ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
}
# refinement proposed for c4.json palettes.annex (the env streams refine the placeholder ramps, C4_DESIGN 3):
# sodium light at the loop, the lit windows and the tram, the counter lamp -- the city's only warm accents
ANNEX_EXTRA = {
    'lamp': ['#4A3016', '#83561E', '#BC862C', '#E6B44C', '#FAE3A2'],
}
ANNEX = dict(ANNEX_C4)
ANNEX.update(ANNEX_EXTRA)
pg.PALETTES['annex'] = ANNEX


def annex_hex() -> set:
    return {h.upper() for r in ANNEX.values() for h in r}


def check_c4_palette() -> list[str]:
    """Differences between c4.json palettes.annex and the palette the art is painted in (notes, not errors)."""
    p = os.path.join(ROOT, 'data', 'chapters', 'c4.json')
    try:
        with open(p, encoding='utf-8') as f:
            ref = json.load(f).get('palettes', {}).get('annex', {})
    except (OSError, ValueError):
        return ['c4.json not readable']
    notes = []
    for ramp, cols in ANNEX.items():
        have = [c.upper() for c in ref.get(ramp, [])]
        if [c.upper() for c in cols] != have:
            notes.append('annex.%s %s c4.json' % (ramp, 'missing in' if not have else 'differs from'))
    return notes


def _lum(h: str) -> float:
    return hk.lum(pg.hx(h))


def by_lum(cols: list) -> list:
    return sorted(cols, key=_lum)


N, CO, ST, FL, DA, PA, SN, RD, SK = (ANNEX[k] for k in ('night', 'concrete', 'steel', 'fluor', 'dawn', 'paper',
                                                       'snow', 'red', 'skin'))
LA = ANNEX['lamp']

RAMPS = {
    'N': [N[0], N[1], N[2], N[3]],                                                  # poche / night (0..3)
    'C': [N[1], N[2], CO[0], CO[1], CO[2], CO[3], CO[4], CO[5]],                     # concrete (0..7)
    'S': [N[0], N[1], ST[0], ST[1], ST[2], ST[3], ST[4], SN[1]],                     # painted steel (0..7)
    'G': [N[1], FL[0], FL[1], FL[2], FL[3], FL[4]],                                  # oil green / fluor (0..5)
    'D': [N[2], N[3], DA[0], DA[1], DA[2], DA[3], DA[4]],                             # dawn / cold plaster (0..6)
    'P': [N[2], PA[0], PA[1], PA[2], PA[3], PA[4]],                                  # paper / cream / pine (0..5)
    'SN': by_lum([DA[0], DA[1], DA[2], SN[0], SN[1], SN[2], SN[3], SN[4]]),           # snow (0..7)
    'R': [N[0], RD[0], RD[1], RD[2], RD[3]],                                         # red (0..4)
    'Y': [SK[0], SK[1], SK[2]],                                                      # skin (0..2)
    'L': [N[1], LA[0], LA[1], LA[2], LA[3], LA[4]],                                  # lamp light (0..5)
    'W': by_lum([N[1], N[2], CO[0], CO[1], PA[1], CO[2], PA[2], CO[3], PA[3], CO[4]]),  # stucco (0..9)
    'K': by_lum([N[1], RD[0], PA[0], RD[1], SK[0], PA[1]]),                          # sooty brick (0..5)
    'I': [N[0], N[1], N[2], ST[0]],                                                  # ink / black iron (0..3)
}
R = hk.Ramps(RAMPS)

# hue counterparts per hue world (src ramp -> ramp a pixel moves onto where the light is strong)
WARM_LOOP = {'W': 'P', 'C': 'P', 'SN': 'L', 'D': 'P', 'S': 'P', 'N': 'P', 'P': 'L', 'K': 'R', 'I': 'P'}
COLD_LOOP = {'P': 'SN', 'W': 'D', 'C': 'D', 'L': 'P', 'K': 'D', 'S': 'D', 'N': 'D', 'I': 'S'}
WARM_HALL = {'G': 'P', 'C': 'P', 'S': 'P', 'W': 'P', 'P': 'L', 'N': 'P', 'D': 'P', 'I': 'P'}
COLD_HALL = {'C': 'G', 'S': 'G', 'W': 'G', 'D': 'G', 'N': 'G', 'I': 'S', 'L': 'P'}
GAINS = {
    'W': (2.4, 2.6, 2.4), 'S': (2.2, 2.4, 2.4), 'P': (2.2, 2.2, 2.4), 'G': (1.8, 2.0, 1.8), 'R': (1.6, 1.0, 1.2),
    'C': (2.2, 2.4, 2.2), 'SN': (1.6, 2.2, 2.0), 'N': (1.4, 1.6, 1.4), 'I': (0.7, 0.7, 0.7), 'K': (2.0, 1.4, 1.8),
    'Y': (1.0, 0.6, 1.0), 'D': (2.0, 2.4, 2.2), 'L': (1.6, 0.8, 1.2),
}


def tlayer(w: int, h: int, name: str = 'layer', world: str = 'loop') -> 'hk.TLayer':
    warm, cold = (WARM_LOOP, COLD_LOOP) if world == 'loop' else (WARM_HALL, COLD_HALL)
    return hk.TLayer(w, h, R, name, warm_of=dict(warm), cold_of=dict(cold), gains=GAINS)


def resolve(lay, fields: dict | None, seed: int = 0, exposure: float = 0.9):
    """Resolve a TLayer palette-pure. `exposure` scales the painted tones of every lit pixel first (the darks
    stay dark, the baked lights make the pools)."""
    t0 = lay.tone.copy()
    m = ~lay.emis & ~lay.unlit
    lay.tone[m] = lay.tone[m] * exposure
    lay.resolve(fields, seed=seed)
    lay.tone = t0
    return lay


# --------------------------------------------------------------------------- re-exported helpers
light_fields = hk.light_fields
sub_fields = hk.sub_fields
dilate, erode, edge_of, box_blur, arch_mask = hk.dilate, hk.erode, hk.edge_of, hk.box_blur, hk.arch_mask
text_mask, text_width, bres, stroke_mask = hk.text_mask, hk.text_width, hk.bres, hk.stroke_mask
bevel, recess, frame, pseudo_text, text, rivets = AK.bevel, AK.recess, AK.frame, AK.pseudo_text, AK.text, AK.rivets
bricks, grain, soft_box, disc, periodic_noise, noise = AK.bricks, AK.grain, AK.soft_box, AK.disc, \
    AK.periodic_noise, AK.noise
add_pools = AK.add_pools


def cyl(lay, x, y, w, h, ramp, tone, hgt=0.6, axis='v', amp=1.2, light=-0.35):
    """A pipe / pole / column: tone + relief rounded across its thickness (light from the upper left)."""
    n = w if axis == 'v' else h
    for i in range(n):
        c = (i + 0.5) / n * 2 - 1
        t = tone + amp * (0.5 - abs(c - light))
        hg = hgt * math.sqrt(max(0.0, 1 - c * c))
        if axis == 'v':
            lay.rect(x + i, y, 1, h, ramp, t, hgt=hg)
        else:
            lay.rect(x, y + i, w, 1, ramp, t, hgt=hg)


def dots(lay, x0, y0, w, h, ramp, tone, density, seed, hgt=None):
    """Sparse single pixels (stains, grit, rivets of wear)."""
    rng = np.random.default_rng(seed)
    n = int(w * h * density)
    for _ in range(n):
        lay.px(x0 + int(rng.integers(0, max(1, w))), y0 + int(rng.integers(0, max(1, h))), ramp, tone, hgt=hgt)


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


def rgba(ramp: str, i: float) -> np.ndarray:
    return R.table[R[ramp], int(np.clip(round(i), 0, R.n(ramp) - 1))].copy()


def palette_report(arr: np.ndarray) -> tuple[int, list]:
    a = arr[..., 3] > 0
    cols = {'#%02X%02X%02X' % tuple(int(v) for v in c[:3]) for c in arr[a].reshape(-1, 4)}
    allowed = annex_hex()
    return len(cols), sorted(c for c in cols if c not in allowed)


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


def emblem(lay, cx, y, size, hist):
    """The regime's emblem at an official site (TECHNICAL_ARCHITECTURE 12.4): neutral = the fictional
    Reichssiegel (white pillar in a black disc); historical (the _hist file, Symbols.pick) = the state eagle
    with the wreath, drawn by env_berlin_insignia (original pixel drawing)."""
    import env_berlin_insignia as BI
    if hist:
        ms = BI.eagle_masks(size, wreath=True, swastika=True)
        h_, w_ = ms['body'].shape
        x0, y0 = cx - w_ // 2, y
        lay.put(ms['body'], x0, y0, 'L', 2.4, hgt=0.6)
        lay.put(ms['lines'], x0, y0, 'L', 1.2)
        lay.put(ms['wreath'], x0, y0, 'L', 3.4, hgt=0.7)
        lay.put(ms['swastika'], x0, y0, 'I', 0.8)
        lay.put(ms['eye'], x0, y0, 'I', 0.8)
        return h_
    d = max(7, size - 4)
    disc, pillar = BI.reichssiegel(d)
    lay.put(disc, cx - d // 2, y + 1, 'I', 0.8, hgt=0.7)
    lay.put(pillar, cx - d // 2, y + 1, 'P', 5.0, hgt=0.8)
    return d + 1
