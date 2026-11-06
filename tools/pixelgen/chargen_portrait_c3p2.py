"""chargen_portrait_c3p2 -- living portraits of the Chapter-3 part-2 looks, through chargen_portrait2.

  alexei_soot / konrad_soot  the speaker's own portrait spec + soot: a smoke-grey face, dark smears placed in
                             head-local coordinates (cheekbone, jaw, forehead -- they follow every expression),
                             grimy collar and shoulders, flakes of ash on the hat; the rim light turned from
                             the cool sky to the warm glow of the fire behind them; a smoky backdrop that glows
                             from the left (the burning wing).
  typist_night               Frau Brunner's spec with the cardigan and blouse replaced by a dark winter coat over
                             the pale collar of her nightdress (a small bow at the throat), no pencil behind the
                             ear; the quay at night behind her, the fire's glow from the left.

The specs are registered IN MEMORY in chargen_portrait2_cast.CAST (chargen_portrait2*.py are not changed) and
written by chargen_portrait2.build_char: portrait.png / portrait_anim.png / portrait.json keep the round-2
contract; portrait.json additionally names the look's base speaker ("look_of").
Run through tools/pixelgen/characters_c3p2.py --portraits.  Deterministic: no randomness.
"""
from __future__ import annotations

import json
import os

import numpy as np

import chargen_portrait2 as PG
import chargen_portrait2_cast as PC
import chargen_portrait2_paint as PP
import chargen_portrait_c3 as PC3
from chargen_portrait2_paint import MatStyle, ramp

# backdrops (top, bottom, glow, speck): smoke-filled registry / the quay at night, both lit from the left
PP.BG.setdefault('c3p2_smoke', ('#1a1210', '#070508', '#5c2e1a', '#b86a3a'))
PP.BG.setdefault('c3p2_quay', ('#0c1322', '#05070d', '#4a2a1c', '#9a6a4a'))
GLOW_LEFT = (0.16, 0.34)
WARM_SKIN = '#e09a62'      # rim of the fire on skin
WARM_CLOTH = '#b8703e'     # ... on cloth, fur, felt
SOOT = np.array([34, 30, 30], float)
ASH = np.array([170, 165, 155], float)
SKIN_MATS = ('skin', 'lip', 'ear', 'neck', 'cheek')
CLOTH_MATS = ('coat', 'coat_lapel', 'shirt', 'knit', 'scarf', 'strap', 'tie', 'cardigan')
HAT_MATS = ('fur', 'hat_top', 'felt', 'brim', 'ribbon', 'tie_string')

# smears: (centre, radii, strength) in head-local coordinates (x: negative = the near side, y: down, z: forward)
SMEARS = {
    'alexei': [((-8.5, 9.6, 10.5), (4.2, 1.5, 7.0), 0.55), ((-3.0, 17.2, 11.5), (5.2, 1.6, 7.0), 0.42),
               ((2.5, -6.2, 15.5), (5.6, 1.3, 7.0), 0.42)],
    'konrad': [((-1.0, -8.6, 15.0), (6.2, 1.7, 7.0), 0.48), ((-8.0, 10.2, 10.5), (3.8, 1.5, 7.0), 0.50),
               ((2.5, 19.0, 11.5), (3.0, 2.0, 6.0), 0.34)],
}


def _hash(x, y, seed):
    return PC._hash2(np.asarray(x), np.asarray(y), seed)


def _mask(G, names):
    d, M = G['d'], G['M']
    ids = [i for i, n in enumerate(M.names) if n in names]
    return np.isin(d.mat, ids) & d.hit if ids else np.zeros(d.mat.shape, bool)


def _mix(rgb, m, a, col):
    """rgb[m] towards col by per-pixel weight a (array over the pixels of m)."""
    px = rgb[m].astype(float)
    a = np.broadcast_to(np.clip(np.asarray(a, float), 0.0, 1.0), (px.shape[0],))[:, None]
    rgb[m] = np.round(px * (1.0 - a) + col[None, :] * a).astype(np.uint8)


def soot_pass(base_id):
    def fn(spec, G, rgb, v, expr, row):
        rgb = rgb.copy()
        seed = PG.seed_of(spec['id'], 'soot')
        # the face: smoke grey everywhere, smears in head-local coordinates (they move with the head)
        m = _mask(G, SKIN_MATS)
        if m.any():
            ys, xs = np.nonzero(m)
            L = PC._local(G, 'hf', m)
            px = rgb[m].astype(float)
            luma = (px @ np.array([0.30, 0.55, 0.15]))[:, None]
            rgb[m] = np.round(px * 0.80 + luma * np.array([0.92, 0.88, 0.84])[None, :] * 0.12).astype(np.uint8)
            a = np.zeros(len(ys))
            for c, r, s in SMEARS.get(base_id, ()):
                q = (((L - np.array(c)) / np.array(r)) ** 2).sum(1)
                a = np.maximum(a, s * np.clip(1.2 - q, 0.0, 1.0) ** 0.7)
            grain = _hash(xs, ys, seed)
            a = np.where(a > 0.05, a * (0.75 + 0.5 * grain), 0.0)
            _mix(rgb, m, a, SOOT)
        # cloth: grime + darker speckles; the hat: grime + ash
        c = _mask(G, CLOTH_MATS)
        if c.any():
            ys, xs = np.nonzero(c)
            g = _hash(xs, ys, seed + 1)
            _mix(rgb, c, 0.10 + 0.30 * (g < 0.12), SOOT)
        h = _mask(G, HAT_MATS)
        if h.any():
            ys, xs = np.nonzero(h)
            g = _hash(xs, ys, seed + 2)
            _mix(rgb, h, 0.12, SOOT)
            ash = h.copy()
            ash[h] = (g > 0.972) & (ys < np.percentile(ys, 70))
            if ash.any():
                _mix(rgb, ash, np.full(int(ash.sum()), 0.85), ASH)
        return rgb
    return fn


def _warm_rims(spec):
    for name, st in spec['styles'].items():
        if getattr(st, 'rim', None) is not None:
            st.rim = PP.hexc(WARM_SKIN if name in SKIN_MATS else WARM_CLOTH)


def sooty(base_id):
    def make():
        spec = PC.CAST[base_id]()
        spec['id'] = base_id + '_soot'
        _warm_rims(spec)
        spec['look'] = dict(spec['look'], bg='c3p2_smoke', glow=GLOW_LEFT)
        spec['rgb_passes'] = list(spec.get('rgb_passes', ())) + [soot_pass(base_id)]
        return spec
    return make


def typist_night():
    """Frau Brunner at the quay, 2.20 at night: dark wool coat over the nightdress, a small bow at the throat."""
    spec = PC.CAST['typist']()
    spec['id'] = 'typist_night'
    st = spec['styles']
    coat = ramp('#08070a', '#141016', '#201a22', '#2e252e', '#3e323c', '#504250', '#655464')
    st['coat'] = MatStyle(coat, PC3.TH6, dither=0.04, rim=PC3.RIM_P)
    st['coat_lapel'] = MatStyle(coat, PC3.TH6, rim=PC3.RIM_P)
    st['night'] = MatStyle(ramp('#14161c', '#3a3a40', '#66646a', '#94908e', '#bcb6ae', '#dcd6cc', '#eeeae2'),
                           [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#a8c0c8')
    spec['torso_items'] = [
        lambda M, t: PC.coat_layers(M, t, coat='coat', inner='night', v_open=0.50, v_top=1.0, lapel=True,
                                    collar=True, collar_h=6.5, collar_r=(11.6, 13.8)),
        lambda M, t: PC.tie_knot_collar(M, mat='night', y=1.4, z=8.4),
    ]
    spec['groups'] = PC3.groups_std({'cheek': 0, 'night': 5, 'button': 5})
    spec['tone_passes'] = [PC3.pass_curls('hair', seed=106, light=2, dark=1)]
    spec['rgb_passes'] = []                      # no pencil behind the ear tonight
    _warm_rims(spec)
    for name in ('hair', 'night'):
        if name in st:
            st[name].rim = PP.hexc(WARM_CLOTH)
    spec['look'] = dict(spec['look'], bg='c3p2_quay', glow=GLOW_LEFT)
    return spec


CAST_C3P2 = {'alexei_soot': sooty('alexei'), 'konrad_soot': sooty('konrad'), 'typist_night': typist_night}
LOOK_OF = {'alexei_soot': 'alexei', 'konrad_soot': 'konrad', 'typist_night': 'typist'}


def register():
    for cid, fn in CAST_C3P2.items():
        PC.CAST.setdefault(cid, fn)


def build(ids, char_dir):
    """Writes the living portraits of `ids` below `char_dir` (an assets/characters directory) + previews."""
    register()
    PG.set_out(char_dir)
    for cid in ids:
        if cid not in CAST_C3P2:
            continue
        spec, frames, grid = PG.build_char(cid, write=True)
        PG.preview(cid, frames, spec.get('expressions', PG.EXPRESSIONS), tag='c3p2_portrait')
        pj = os.path.join(char_dir, cid, 'portrait.json')
        meta = json.load(open(pj, encoding='utf-8'))
        meta['look_of'] = LOOK_OF[cid]
        meta['anim']['spec'] = 'tools/pixelgen/chargen_portrait_c3p2.py'
        with open(pj, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
            f.write('\n')
