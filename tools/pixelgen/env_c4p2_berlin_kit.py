"""env_c4p2_berlin_kit -- palettes, super-ramps and small painters for L_C4P2_Berlin (Chapter 4 part 2, round 10).

Owned by the env-berlin stream (documentation/C4P2_DESIGN.md §4.2 / §10).  Same tone-space painting model as the
round-9 annex (env_c4_annex_kit, built on env_veltrava_hall_kit.TLayer / Ramps / light fields -- imported read-only):
every pixel is painted as (ramp, tone); baked light adds tone and, where it is strong, moves a pixel onto the
light's counterpart ramp at equal luminance.  Two places share one level file and get two palettes:

  * 'ostbahnhof' (L_C4P2_BerlinA, Monday 20.30): sodium under a glass vault, steam, the warm dining car, the cold
    blue night at the open end of the hall;
  * 'courtyard'  (L_C4P2_BerlinB, Tuesday 22.10-23.40): night blue plaster and snow, warm windows, one sodium lamp
    in the gate passage.

Both are data/chapters/c4p2.json palettes (story stream's placeholder ramps, kept colour for colour) PLUS proposed
ramps (OST_EXTRA / YARD_EXTRA) -- the grade's palette snap (palette_strength 0.5) should know them; the proposal is
in asset_manifest_parts/env_c4p2_berlin.md and the integration notes.  Every PNG this stream writes is palette-pure
in its place's palette (checked at build time and by tests/test_c4p2_berlin_art.gd).
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
import env_c3p2_archive_kit as AK  # noqa: E402  (generic painters: bevel, recess, bricks, grain, noise ...)

DATE = '2026-11-06'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# --------------------------------------------------------------------------- palettes
# c4p2.json palettes.ostbahnhof (binding, compared at build time)
OST_C4P2 = {
    'night': ['#06080B', '#0C1015', '#141A21', '#1D252E'],
    'glass': ['#1C2630', '#2A3846', '#3C4E60', '#56697C', '#76899A'],
    'steel': ['#1C2228', '#2A323A', '#3B4650', '#526070', '#6E7D8C'],
    'sodium': ['#4A3014', '#7E521E', '#B67E2C', '#E2AC4A', '#F8DB96'],
    'steam': ['#5E646C', '#7F868E', '#A2A8AE', '#C6CACE', '#E8EAEC'],
    'green': ['#162A22', '#223D31', '#325443', '#486E58'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
}
# proposed refinement (C4P2_DESIGN §3: "the env streams refine them"): wood of the buffet / kiosk / dining car,
# the brick of the hall's far wall, the blue enamel of the signs, the warm white of tablecloths and enamel letters
OST_EXTRA = {
    'wood': ['#2A1B12', '#43291A', '#5E3B24', '#7C5233'],
    'brick': ['#2B1A15', '#3F261D', '#573527', '#714734'],
    'enamel': ['#101C34', '#1C2E52', '#2E4878'],
    'cream': ['#E9DFC4', '#F6F0DE'],
}
# c4p2.json palettes.courtyard (binding)
YARD_C4P2 = {
    'night': ['#05070B', '#0A0F16', '#111822', '#1A2330'],
    'plaster': ['#2A2C30', '#3C3F44', '#53575C', '#6E7277', '#8D9195'],
    'brick': ['#2B1A15', '#3F261D', '#573527', '#714734'],
    'window': ['#5A3A16', '#8C5E26', '#C08A3A', '#E8B65A', '#FBE2A0'],
    'snow': ['#6F7A8C', '#94A0B2', '#B9C3D0', '#DCE2EA', '#F2F4F7'],
    'laundry': ['#8E8C86', '#B2AFA6', '#D4D0C6'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
}
# proposed: the night blue of plaster and snow in shadow, wood of doors / window frames / the card box, the green of
# a Berlin stair door
YARD_EXTRA = {
    'dusk': ['#1C2433', '#273248', '#36435C', '#4A5874', '#63718C'],
    'wood': ['#2A1B12', '#43291A', '#5E3B24', '#7C5233'],
    'green': ['#1B2E28', '#28423A', '#3A5B4F'],
}
OST = dict(OST_C4P2)
OST.update(OST_EXTRA)
YARD = dict(YARD_C4P2)
YARD.update(YARD_EXTRA)
pg.PALETTES['ostbahnhof_r10'] = OST
pg.PALETTES['courtyard_r10'] = YARD


def hexset(pal: dict) -> set:
    return {h.upper() for r in pal.values() for h in r}


def palette_count(pal: dict) -> int:
    return len(hexset(pal))


def check_c4p2_palettes() -> list[str]:
    """Differences between c4p2.json palettes and the palettes painted here (notes, not errors)."""
    p = os.path.join(ROOT, 'data', 'chapters', 'c4p2.json')
    try:
        with open(p, encoding='utf-8') as f:
            ref = json.load(f).get('palettes', {})
    except (OSError, ValueError):
        return ['c4p2.json not readable']
    notes = []
    for name, pal in (('ostbahnhof', OST), ('courtyard', YARD)):
        have = ref.get(name, {})
        for ramp, cols in pal.items():
            got = [c.upper() for c in have.get(ramp, [])]
            if [c.upper() for c in cols] != got:
                notes.append('%s.%s %s c4p2.json' % (name, ramp, 'missing in' if not got else 'differs from'))
    return notes


def _lum(h: str) -> float:
    return hk.lum(pg.hx(h))


def by_lum(cols: list) -> list:
    return sorted(cols, key=_lum)


# --------------------------------------------------------------------------- super-ramps: the station (A)
_o = OST
RAMPS_A = {
    'N': [_o['night'][0], _o['night'][1], _o['night'][2], _o['night'][3]],                      # poche (0..3)
    'G': [_o['night'][1], _o['glass'][0], _o['glass'][1], _o['glass'][2], _o['glass'][3],
          _o['glass'][4]],                                                                    # roof glass (0..5)
    'S': [_o['night'][0], _o['night'][1], _o['steel'][0], _o['steel'][1], _o['steel'][2], _o['steel'][3],
          _o['steel'][4]],                                                                    # iron, steel (0..6)
    'L': [_o['wood'][1], _o['sodium'][0], _o['sodium'][1], _o['sodium'][2], _o['sodium'][3],
          _o['sodium'][4]],                                                                   # sodium (0..5)
    'V': by_lum([_o['steel'][3], _o['steam'][0], _o['steam'][1], _o['steam'][2], _o['steam'][3],
                 _o['steam'][4]]),                                                            # steam, snow (0..5)
    'E': [_o['night'][1], _o['green'][0], _o['green'][1], _o['green'][2], _o['green'][3]],      # green cars (0..4)
    'P': by_lum([_o['night'][2], _o['paper'][0], _o['paper'][1], _o['paper'][2], _o['paper'][3], _o['paper'][4],
                 _o['cream'][0], _o['cream'][1]]),                                            # paper, stone (0..7)
    'R': [_o['night'][0], _o['red'][0], _o['red'][1], _o['red'][2], _o['red'][3]],              # red, wine red (0..4)
    'Y': [_o['skin'][0], _o['skin'][1], _o['skin'][2]],                                       # skin (0..2)
    'D': [_o['night'][1], _o['wood'][0], _o['wood'][1], _o['wood'][2], _o['wood'][3]],          # wood (0..4)
    'K': [_o['night'][1], _o['brick'][0], _o['brick'][1], _o['brick'][2], _o['brick'][3]],      # brick (0..4)
    'B': [_o['night'][1], _o['enamel'][0], _o['enamel'][1], _o['enamel'][2]],                   # blue enamel (0..3)
    'I': [_o['night'][0], _o['night'][1], _o['night'][2], _o['steel'][0]],                      # ink / black (0..3)
}
RA = hk.Ramps(RAMPS_A)
# sodium turns iron brown and stone amber; the cold light of the hall end / the steam turns things blue-white
WARM_A = {'S': 'D', 'I': 'D', 'N': 'D', 'G': 'S', 'V': 'P', 'P': 'L', 'E': 'D', 'K': 'R', 'B': 'S', 'D': 'L'}
COLD_A = {'P': 'V', 'D': 'S', 'L': 'P', 'K': 'S', 'N': 'G', 'I': 'S', 'E': 'G', 'R': 'R', 'Y': 'P'}
GAINS_A = {
    'N': (1.4, 1.6, 1.4), 'G': (1.8, 2.0, 2.0), 'S': (2.2, 2.4, 2.4), 'L': (1.6, 0.8, 1.2), 'V': (1.6, 2.2, 2.0),
    'E': (1.8, 1.8, 1.8), 'P': (2.4, 2.2, 2.4), 'R': (1.6, 1.0, 1.2), 'Y': (1.0, 0.6, 1.0), 'D': (2.0, 1.4, 1.6),
    'K': (2.0, 1.4, 1.8), 'B': (1.4, 1.6, 1.4), 'I': (0.7, 0.7, 0.7),
}

# --------------------------------------------------------------------------- super-ramps: the courtyard (B)
_y = YARD
RAMPS_B = {
    'N': [_y['night'][0], _y['night'][1], _y['night'][2], _y['night'][3]],                      # poche (0..3)
    'W': [_y['night'][1], _y['night'][2], _y['plaster'][0], _y['plaster'][1], _y['plaster'][2],
          _y['plaster'][3], _y['plaster'][4]],                                                # plaster (0..6)
    'U': [_y['night'][1], _y['dusk'][0], _y['dusk'][1], _y['dusk'][2], _y['dusk'][3], _y['dusk'][4]],  # night blue
    'K': [_y['night'][1], _y['brick'][0], _y['brick'][1], _y['brick'][2], _y['brick'][3]],      # brick (0..4)
    'L': [_y['brick'][0], _y['window'][0], _y['window'][1], _y['window'][2], _y['window'][3],
          _y['window'][4]],                                                                   # lamp light (0..5)
    'SN': by_lum([_y['dusk'][2], _y['dusk'][3], _y['snow'][0], _y['snow'][1], _y['snow'][2], _y['snow'][3],
                  _y['snow'][4]]),                                                            # snow (0..6)
    'Q': by_lum([_y['plaster'][3], _y['laundry'][0], _y['laundry'][1], _y['laundry'][2]]),      # linen (0..3)
    'R': [_y['night'][0], _y['red'][0], _y['red'][1], _y['red'][2], _y['red'][3]],              # red (0..4)
    'P': by_lum([_y['night'][2], _y['paper'][0], _y['paper'][1], _y['paper'][2], _y['paper'][3],
                 _y['paper'][4]]),                                                            # paper (0..5)
    'Y': [_y['skin'][0], _y['skin'][1], _y['skin'][2]],                                       # skin (0..2)
    'D': [_y['night'][1], _y['wood'][0], _y['wood'][1], _y['wood'][2], _y['wood'][3]],          # wood (0..4)
    'E': [_y['night'][1], _y['green'][0], _y['green'][1], _y['green'][2]],                      # door green (0..3)
    'I': [_y['night'][0], _y['night'][1], _y['night'][2], _y['plaster'][0]],                    # ink / iron (0..3)
}
RB = hk.Ramps(RAMPS_B)
WARM_B = {'W': 'P', 'U': 'W', 'SN': 'L', 'I': 'D', 'N': 'D', 'D': 'L', 'K': 'R', 'P': 'L', 'E': 'D', 'Q': 'P'}
COLD_B = {'W': 'U', 'P': 'SN', 'L': 'P', 'D': 'U', 'K': 'U', 'I': 'U', 'N': 'U', 'E': 'U', 'Q': 'SN', 'Y': 'P'}
GAINS_B = {
    'N': (1.4, 1.6, 1.4), 'W': (2.4, 2.4, 2.4), 'U': (2.0, 2.4, 2.2), 'K': (2.0, 1.4, 1.8), 'L': (1.6, 0.8, 1.2),
    'SN': (1.8, 2.2, 2.0), 'Q': (1.6, 1.6, 1.6), 'R': (1.6, 1.0, 1.2), 'P': (2.2, 2.2, 2.4), 'Y': (1.0, 0.6, 1.0),
    'D': (2.0, 1.4, 1.6), 'E': (1.8, 1.6, 1.6), 'I': (0.7, 0.9, 0.7),
}

WORLD = {'A': (RA, WARM_A, COLD_A, GAINS_A, OST), 'B': (RB, WARM_B, COLD_B, GAINS_B, YARD)}


class TLayer(hk.TLayer):
    """hk.TLayer whose fresh paint covers what lies beneath: a pixel painted with a ramp and no explicit emis /
    unlit flag stops glowing (the passage wall over a stairwell window, a window bar over lit glass, a kiosk over
    the cab's firebox glow) -- before, the flag survived the overpaint and the hidden glow showed through."""

    def put(self, mask, x0, y0, ramp, tone, hgt=None, flat=None, emis=None, unlit=None, gain=None, crisp=None):
        if ramp is not None:
            emis = False if emis is None else emis
            unlit = False if unlit is None else unlit
        return super().put(mask, x0, y0, ramp, tone, hgt=hgt, flat=flat, emis=emis, unlit=unlit, gain=gain,
                           crisp=crisp)


def tlayer(w: int, h: int, name: str = 'layer', world: str = 'A') -> 'hk.TLayer':
    R, warm, cold, gains, _p = WORLD[world]
    return TLayer(w, h, R, name, warm_of=dict(warm), cold_of=dict(cold), gains=gains)


def resolve(lay, fields: dict | None, seed: int = 0, exposure: float = 0.9):
    """Resolve a TLayer palette-pure. `exposure` scales the painted tones of every lit pixel first (the night keeps
    its darks, the baked lights make the pools)."""
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
bres, stroke_mask = hk.bres, hk.stroke_mask

# glyphs the shared 3x5 font lacks (en dash, middle dot, the Swedish ring A): 5 rows, plus the overhang row on top.
# 'W' replaces the shared font's 3-wide W (which differs from H in one row only: „WASCH“ read „HASCH“) by a
# 5-wide one that cannot be mistaken.
EXTRA_35 = {
    '–': ['...', '...', '###', '...', '...'], '·': ['...', '...', '.#.', '...', '...'],
    'Å': ['.#.', '#.#', '###', '#.#', '#.#'],
    'W': ['#...#', '#...#', '#.#.#', '#.#.#', '.#.#.'],
}
EXTRA_35_TOP = {'Å': '.#.'}


def text_mask(s: str, font: str = '35', spacing: int = 1, overhang: bool = False) -> np.ndarray:
    """hk.text_mask plus the glyphs of EXTRA_35 (3x5 font only); with overhang the mask has one row more on top
    when any glyph uses it (distinct umlauts, the ring of Å)."""
    if font == '35':
        s = s.upper()
    if font != '35' or not any(ch in EXTRA_35 for ch in s):
        return hk.text_mask(s, font, spacing, overhang=overhang)
    parts = []
    for ch in s:
        if ch in EXTRA_35:
            g = np.array([[c == '#' for c in row] for row in EXTRA_35[ch]], bool)
            top = np.array([[c == '#' for c in EXTRA_35_TOP.get(ch, '.' * g.shape[1])]], bool)
            parts.append((np.vstack([top, g]), True))
        else:
            m = hk.text_mask(ch, font, 1, overhang=overhang)
            parts.append((m if m.shape[0] == 6 else np.vstack([np.zeros((1, m.shape[1]), bool), m]), True))
    tall = overhang and any(p[0][0].any() for p in parts)
    cols = []
    for i, (m, _) in enumerate(parts):
        cols.append(m if tall else m[1:])
        if i < len(parts) - 1:
            cols.append(np.zeros((cols[-1].shape[0], spacing), bool))
    return np.concatenate(cols, axis=1)


def text_width(s: str, font: str = '35', spacing: int = 1) -> int:
    return text_mask(s, font, spacing).shape[1]
bevel, recess, frame, pseudo_text = AK.bevel, AK.recess, AK.frame, AK.pseudo_text
bricks, grain, soft_box, disc, periodic_noise, noise = AK.bricks, AK.grain, AK.soft_box, AK.disc, \
    AK.periodic_noise, AK.noise
add_pools = AK.add_pools


def text(lay, s, x, y, ramp, tone, font='35', spacing=1, center=False, **kw):
    """Pixel text with its top-left at (x, y); distinct umlauts (their dots one row above y)."""
    m = text_mask(s, font, spacing, overhang=True)
    oh = m.shape[0] - (5 if font == '35' else 7)
    if center:
        x = int(round(x - m.shape[1] / 2))
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    lay.put(m, x, y - oh, ramp, tone, **kw)
    return m.shape[1]


def tw(s, font='35', spacing=1) -> int:
    return text_width(s, font, spacing)


def cyl(lay, x, y, w, h, ramp, tone, hgt=0.6, axis='v', amp=1.2, light=-0.35, **kw):
    """A pipe / pole / boiler: tone + relief rounded across its thickness (light from the upper left)."""
    n = w if axis == 'v' else h
    for i in range(n):
        c = (i + 0.5) / n * 2 - 1
        t = tone + amp * (0.5 - abs(c - light))
        hg = hgt * math.sqrt(max(0.0, 1 - c * c))
        if axis == 'v':
            lay.rect(x + i, y, 1, h, ramp, t, hgt=hg, **kw)
        else:
            lay.rect(x, y + i, w, 1, ramp, t, hgt=hg, **kw)


def dots(lay, x0, y0, w, h, ramp, tone, density, seed, hgt=None, **kw):
    """Sparse single pixels (grit, stains, rivets of wear)."""
    rng = np.random.default_rng(seed)
    n = int(w * h * density)
    for _ in range(n):
        lay.px(x0 + int(rng.integers(0, max(1, w))), y0 + int(rng.integers(0, max(1, h))), ramp, tone, hgt=hgt, **kw)


def snowcap(lay, x, y, w, depth=2, seed=0, drip=0.25, tone=None, ramp=None):
    """Snow on an upward edge at y (the cap sits on y-depth .. y-1), soft irregular top, a few drips below."""
    rng = np.random.default_rng(seed)
    R = lay.R
    ramp = ramp or ('SN' if 'SN' in R.idx else 'V')
    top = R.n(ramp) - 1
    tone = top - 0.6 if tone is None else tone
    for i in range(int(w)):
        d = depth + (1 if rng.random() < 0.3 else 0) - (1 if rng.random() < 0.15 else 0)
        if i == 0 or i == w - 1:
            d = max(1, d - 1)
        for k in range(max(1, d)):
            lay.px(x + i, y - 1 - k, ramp, tone - 0.9 * (k == 0 and d > 1) + 0.5 * (k == d - 1), hgt=0.5)
        if rng.random() < drip * 0.25:
            lay.px(x + i, y, ramp, tone - 2.0, hgt=0.2)


def icicles(lay, x, y, w, seed=0, n=None, maxlen=5, ramp=None, tone=None):
    """Short icicles hanging from an edge at y (growing downward)."""
    rng = np.random.default_rng(seed)
    R = lay.R
    ramp = ramp or ('SN' if 'SN' in R.idx else 'V')
    tone = (R.n(ramp) - 1.5) if tone is None else tone
    n = n if n is not None else max(1, int(w / 5))
    for _ in range(n):
        xx = x + int(rng.integers(0, max(1, w)))
        ln = int(rng.integers(1, maxlen + 1))
        for k in range(ln):
            lay.px(xx, y + k, ramp, tone - k * 0.5, hgt=0.4)


def plank_floor(lay, x, y, w, h, ramp, base, seed=0, plank=5, gap=-1.0):
    """Floor boards seen from the side (horizontal boards, joints, nail heads)."""
    rng = np.random.default_rng(seed)
    for yy in range(y, y + h):
        lay.hline(x, yy, w, ramp, base + (0.3 if (yy - y) % plank == 0 else 0), hgt=0.2)
    xx = x
    while xx < x + w:
        ln = int(rng.integers(26, 60))
        lay.vline(min(x + w - 1, xx), y, h, ramp, base + gap, hgt=0.0)
        xx += ln


def emblem(lay, cx, y, size, hist, ramp_light='L', ramp_dark='I'):
    """The Reich's emblem at an official site (TECHNICAL_ARCHITECTURE 12.4): neutral = the fictional Reichssiegel
    (white pillar in a black disc); historical (the _hist file, Symbols.pick) = the state eagle with the wreath,
    drawn by env_berlin_insignia (original pixel drawing).  Returns the drawn height."""
    import env_berlin_insignia as BI
    if hist:
        ms = BI.eagle_masks(size, wreath=True, swastika=True)
        h_, w_ = ms['body'].shape
        x0 = cx - w_ // 2
        lay.put(ms['body'], x0, y, ramp_light, 2.4, hgt=0.6)
        lay.put(ms['lines'], x0, y, ramp_light, 1.2)
        lay.put(ms['wreath'], x0, y, ramp_light, 3.4, hgt=0.7)
        lay.put(ms['swastika'], x0, y, ramp_dark, 0.8)
        lay.put(ms['eye'], x0, y, ramp_dark, 0.8)
        return h_
    d = max(7, size - 4)
    disc_m, pillar = BI.reichssiegel(d)
    lay.put(disc_m, cx - d // 2, y + 1, ramp_dark, 0.8, hgt=0.7)
    lay.put(pillar, cx - d // 2, y + 1, 'P', lay.R.n('P') - 1.0, hgt=0.8)
    return d + 1


def soviet_emblem(lay, x, y, hist, ramp, tone, kind='gw7'):
    """The Soviet emblem (12.4): neutral = the fictional gear-and-wheat (env_karsk_emblems 'gw*'), historical =
    hammer and sickle ('hs*').  Same footprint for both."""
    import env_karsk_emblems as KE
    m = KE.mask(KE.kind_for(kind, hist))
    lay.put(m, x, y, ramp, tone, hgt=0.6, crisp=True)
    return m.shape


def palette_report(arr: np.ndarray, pal: dict) -> tuple[int, list]:
    a = arr[..., 3] > 0
    cols = {'#%02X%02X%02X' % tuple(int(v) for v in c[:3]) for c in arr[a].reshape(-1, 4)}
    allowed = hexset(pal)
    return len(cols), sorted(c for c in cols if c not in allowed)


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


def rgba(R, ramp: str, i: float) -> np.ndarray:
    return R.table[R[ramp], int(np.clip(round(i), 0, R.n(ramp) - 1))].copy()


def ramp_rgba(R, ramp: str, t: np.ndarray, alpha: np.ndarray, seed=0, x0=0, y0=0) -> np.ndarray:
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


# --------------------------------------------------------------------------- small figures (life strips)
class Fig:
    """A small painted person for life strips / window life (side view, 1 px = 1 world px).  Drawn onto a TLayer
    with its feet (or its waist for `bust`) at (x, y).  Parts are tone-shaded with a light from the upper left,
    a darker rim on the shadow side; faces get 1-px features.  Sizes: an adult is ~ 46 px tall, a child ~ 30,
    a figure in a window is drawn as a bust (head + shoulders + arms)."""

    def __init__(self, coat=('S', 3.0), skin=('Y', 1.2), hair=('I', 1.6), hat=None, legs=None, shoe=('I', 0.8),
                 scarf=None, apron=None, collar=None, h=46, face=1, bulk=0):
        self.coat, self.skin, self.hair, self.hat = coat, skin, hair, hat
        self.legs = legs or (coat[0], coat[1] - 1.0)
        self.shoe, self.scarf, self.apron, self.collar = shoe, scarf, apron, collar
        self.h, self.face, self.bulk = h, face, bulk

    def _blob(self, lay, x, y, w, h, ramp, tone, shade_side, **kw):
        """A rounded block shaded across its width (lit side toward -face... light from the upper left)."""
        for i in range(w):
            c = (i + 0.5) / w
            t = tone + (0.6 - c * 1.2) * 0.9
            top = y + (1 if (i == 0 or i == w - 1) else 0)
            lay.rect(x + i, top, 1, h - (top - y), ramp, t, hgt=0.6 * math.sin(math.pi * c), **kw)

    def head(self, lay, x, y, s=1.0, look=None, **kw):
        """Head with its top-left near (x - 3, y): 6 x 7 px at s=1 (hair, ear, eye, nose by facing)."""
        f = self.face if look is None else look
        hw, hh = max(4, int(round(6 * s))), max(5, int(round(7 * s)))
        x0 = x - hw // 2
        sr, st = self.skin
        lay.rect(x0, y + 1, hw, hh - 1, sr, st, hgt=0.6, **kw)
        lay.rect(x0 + (hw - 1 if f > 0 else 0), y + 2, 1, hh - 3, sr, st - 0.6, **kw)       # back of the head shade
        lay.px(x0 + (hw - 2 if f > 0 else 1), y + hh // 2, sr, st + 0.6, **kw)               # cheek light
        hr, ht = self.hair
        lay.rect(x0, y, hw, 2, hr, ht, hgt=0.7, **kw)
        lay.rect(x0 + (0 if f > 0 else hw - 2), y + 1, 2, hh // 2 + 1, hr, ht - 0.3, **kw)  # hair at the back
        ex = x0 + (hw - 2 if f > 0 else 1)
        lay.px(ex, y + 3, 'I', 0.6, **kw)                                                    # eye
        lay.px(x0 + (hw if f > 0 else -1), y + 4, sr, st - 0.2, **kw)                        # nose tip
        if self.hat is not None:
            r, t, kind = self.hat
            if kind == 'cap':
                lay.rect(x0 - 1, y - 1, hw + 2, 2, r, t, hgt=0.8, **kw)
                lay.rect(x0 + (hw - 1 if f > 0 else -2), y + 1, 3, 1, r, t - 0.8, **kw)   # visor
            elif kind == 'hat':
                lay.rect(x0 - 2, y + 1, hw + 4, 1, r, t - 0.4, hgt=0.8, **kw)             # brim
                lay.rect(x0, y - 2, hw, 3, r, t, hgt=0.8, **kw)
                lay.hline(x0, y, hw, 'I', 1.0, **kw)                                      # band
            elif kind == 'scarf':                                                         # headscarf
                lay.rect(x0 - 1, y - 1, hw + 2, 3, r, t, hgt=0.7, **kw)
                lay.rect(x0 + (-1 if f > 0 else hw - 1), y + 1, 2, hh - 2, r, t - 0.4, **kw)
                lay.px(x0 + (-2 if f > 0 else hw), y + hh - 1, r, t - 0.8, **kw)
            elif kind == 'ushanka':
                lay.rect(x0 - 1, y - 2, hw + 2, 3, r, t, hgt=0.8, **kw)
                lay.rect(x0 + (-1 if f > 0 else hw - 1), y, 2, 5, r, t - 0.4, **kw)
            elif kind == 'bun':
                lay.rect(x0 + (-1 if f > 0 else hw - 2), y - 1, 3, 3, hr, ht + 0.4, **kw)
        return hw, hh

    def stand(self, lay, x, y, pose=0.0, arm=None, carry=None, **kw):
        """A standing adult, feet at (x, y). pose = small sway; arm: None | 'up' (to the mouth) | 'out' | 'down';
        carry: None | ('case', ramp, tone) | ('paper', ...) -- in the near hand."""
        H = self.h
        f = self.face
        bw = 9 + self.bulk
        sway = int(round(pose))
        hx = x + sway
        head_y = y - H
        self.head(lay, hx, head_y, **kw)
        # neck + collar / scarf
        lay.rect(hx - 1, head_y + 7, 3, 2, self.skin[0], self.skin[1] - 0.4, **kw)
        torso_top = head_y + 8
        torso_h = int(H * 0.46)
        cr, ct = self.coat
        self._blob(lay, hx - bw // 2, torso_top, bw, torso_h, cr, ct, f, **kw)
        # coat skirt down to the knees, slightly flared
        sk_top = torso_top + torso_h
        sk_h = int(H * 0.2)
        for k in range(sk_h):
            ww = bw + (k // 4)
            self._blob(lay, hx - ww // 2, sk_top + k, ww, 1, cr, ct - 0.2 - k * 0.03, f, **kw)
        if self.apron is not None:
            ar, at = self.apron
            lay.rect(hx - bw // 2 + (1 if f > 0 else 2), torso_top + torso_h - 4, bw - 3, sk_h + 4, ar, at, **kw)
        if self.scarf is not None:
            sr, st = self.scarf
            lay.rect(hx - 3, torso_top, 7, 2, sr, st, hgt=0.7, **kw)
            lay.rect(hx + (-3 if f > 0 else 2), torso_top + 2, 2, 6, sr, st - 0.4, **kw)
        if self.collar is not None:
            lr, lt = self.collar
            lay.rect(hx - 4, torso_top, 9, 2, lr, lt, hgt=0.8, **kw)
        # buttons
        for k in range(3):
            lay.px(hx + (2 if f > 0 else -2), torso_top + 3 + k * 4, 'I', 0.9, **kw)
        # legs
        lr, lt = self.legs
        leg_top = sk_top + sk_h
        leg_h = y - leg_top - 1
        lay.rect(hx - 3, leg_top, 2, leg_h, lr, lt, **kw)
        lay.rect(hx + 1, leg_top, 2, leg_h, lr, lt - 0.5, **kw)
        sr_, st_ = self.shoe
        lay.rect(hx - 4 + (1 if f > 0 else 0), y - 1, 4, 1, sr_, st_, **kw)
        lay.rect(hx + (1 if f > 0 else 0), y - 1, 4, 1, sr_, st_ - 0.2, **kw)
        # arms
        ax = hx + (bw // 2 - 1 if f > 0 else -bw // 2)
        if arm == 'up':
            lay.rect(ax, torso_top + 2, 2, 7, cr, ct - 0.5, **kw)
            lay.rect(ax + (1 if f > 0 else -1), torso_top - 1, 2, 4, cr, ct - 0.2, **kw)
            lay.px(ax + (2 if f > 0 else -2), torso_top - 2, self.skin[0], self.skin[1], **kw)
        elif arm == 'out':
            lay.rect(ax, torso_top + 2, 2, 7, cr, ct - 0.5, **kw)
            lay.rect(ax + (1 if f > 0 else -4), torso_top + 8, 5, 2, cr, ct - 0.3, **kw)
            lay.px(ax + (6 if f > 0 else -5), torso_top + 8, self.skin[0], self.skin[1], **kw)
        else:
            lay.rect(ax, torso_top + 2, 2, torso_h - 1, cr, ct - 0.6, **kw)
            lay.px(ax, torso_top + torso_h + 1, self.skin[0], self.skin[1] - 0.2, **kw)
        if carry is not None:
            kind, rr, tt = carry
            if kind == 'case':
                cx = ax - (2 if f > 0 else 6)
                lay.rect(cx, torso_top + torso_h - 1, 9, 7, rr, tt, hgt=0.6, **kw)
                lay.hline(cx, torso_top + torso_h - 1, 9, rr, tt + 0.8, **kw)
                lay.px(cx + 4, torso_top + torso_h - 2, 'I', 1.0, **kw)
            elif kind == 'paper':
                lay.rect(ax + (1 if f > 0 else -3), torso_top + 6, 4, 5, rr, tt, **kw)
        return head_y

    def bust(self, lay, x, y, lean=0, arm=None, **kw):
        """Waist-up figure (behind a window sill / a counter): the waist at (x, y)."""
        H = int(self.h * 0.55)
        f = self.face
        bw = 9 + self.bulk
        hx = x + lean
        head_y = y - H
        self.head(lay, hx, head_y, **kw)
        lay.rect(hx - 1, head_y + 7, 3, 2, self.skin[0], self.skin[1] - 0.4, **kw)
        cr, ct = self.coat
        self._blob(lay, x - bw // 2, head_y + 8, bw, y - head_y - 8, cr, ct, f, **kw)
        if self.collar is not None:
            lr, lt = self.collar
            lay.rect(hx - 4, head_y + 8, 9, 2, lr, lt, hgt=0.8, **kw)
        if self.apron is not None:
            ar, at = self.apron
            lay.rect(x - bw // 2 + 1, head_y + 12, bw - 2, y - head_y - 12, ar, at, **kw)
        ax = x + (bw // 2 - 1 if f > 0 else -bw // 2)
        if arm == 'up':
            lay.rect(ax + (1 if f > 0 else -1), head_y + 7, 2, 5, cr, ct - 0.2, **kw)
            lay.px(ax + (2 if f > 0 else -2), head_y + 6, self.skin[0], self.skin[1], **kw)
        elif arm == 'out':
            lay.rect(ax + (1 if f > 0 else -4), head_y + 14, 5, 2, cr, ct - 0.3, **kw)
            lay.px(ax + (6 if f > 0 else -5), head_y + 14, self.skin[0], self.skin[1], **kw)
        elif arm == 'table':
            lay.rect(ax + (0 if f > 0 else -5), y - 4, 6, 2, cr, ct - 0.3, **kw)
            lay.px(ax + (6 if f > 0 else -6), y - 4, self.skin[0], self.skin[1], **kw)
        return head_y


def fig_mask_render(R, draw, w, h, fields=None, seed=0, world_tl=(0, 0), exposure=1.0):
    """Paint something with `draw(lay)` on a fresh w x h TLayer, resolve it (optionally lit by `fields`, already
    cropped to this box) and return its RGBA."""
    lay = hk.TLayer(w, h, R, 'fig')
    draw(lay)
    if exposure != 1.0:
        m = ~lay.emis & ~lay.unlit
        lay.tone[m] = lay.tone[m] * exposure
    lay.resolve(fields, seed=seed)
    return lay.c.copy()


def save_rgba(arr: np.ndarray, path: str):
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.asarray(arr).astype(np.uint8), 'RGBA').save(path)
