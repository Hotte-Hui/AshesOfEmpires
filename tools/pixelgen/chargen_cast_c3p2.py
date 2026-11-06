"""chargen_cast_c3p2 -- Chapter 3, part 2 ("Der eiserne Frieden", the archive fire): character LOOKS on the
round-2 rig (documentation/C3P2_DESIGN.md section 6: existing ids only, a soot overlay for the fire scenes and
the quay, a carry row with the file, Frau Brunner in her coat over the nightdress).

  alexei_soot   Alexei after the smoke: coat hem and cuffs blackened, sooty hands, a smear across the cheek
                and jaw, coal dust on the trouser legs, a greyed scarf, two flakes of ash on the ushanka.
                Every row of `alexei` (same poses, same row indices) + `carry_side` (walk) and
                `carry_idle_side` (idle): the file C-17 held to the chest with the near arm.
  konrad_soot   the same for Konrad (a smear on the forehead under the brim, the beige scarf greyed).
  typist_night  Frau Brunner on the quay at 2.20: a dark winter coat thrown over her nightdress (its pale hem
                shows down to the ankles), felt boots, one hand holding the collar shut, no pencil, no pad.

A look is NOT a new character: dialogue speaker and NPC `char_id` stay `alexei` / `konrad` / `typist`; the
runtime chooses the sheet directory per scene (c3.json "looks", integration notes of round 8).  Every pose
comes unchanged from chargen_anim / chargen_cast / chargen_cast_c3: a variant spec is the base spec plus extra
materials and ONE last hook that repaints material ids (normals, light, outlines stay those of the base, so
the silhouette is pixel-identical and the variants follow every later change of the base characters).
Deterministic: no randomness.
"""
from __future__ import annotations

import dataclasses
import math

import numpy as np

import chargen_anim as A
import chargen_cast_c3 as C3
import chargen_heads as HD
from chargen_body import Coat, Skirt, M, Spec
from chargen_cast import CAST as CAST_BASE
from chargen_cast import bm, buttons, column_line, flap, materials, put_poly
from chargen_core import Material, hex_rgb, put_bitmap

# ----------------------------------------------------------------------------------- soot materials
# dark warm grey-brown (wood smoke + coal dust), slot for slot [outline, deep, shadow, base, light, highlight]
SOOT = ['#0B0909', '#151111', '#201A18', '#2C2522', '#3A322D', '#4A413A']
ASH = ['#3C3A38', '#5C5A56', '#7E7C78', '#9E9C96', '#BAB8B2', '#D2D0CA']
LEVELS = {'heavy': 0.70, 'smudge': 0.55, 'dust': 0.30}
SOOTY = ('coat', 'trouser', 'skin', 'hair', 'scarf', 'hat', 'band', 'strap', 'satchel', 'tube', 'cap',
         'folder', 'boot', 'akte')


def twin(name: str, level: str) -> str:
    """Name of the soot twin of material `name` at `level`."""
    return f'{name}~{level}'


def soot_ramp(ramp, k: float):
    out = []
    for i, c in enumerate(ramp):
        s = np.array([*hex_rgb(SOOT[i]), 255.0])
        v = np.asarray(c, float) * (1.0 - k) + s * k
        v[3] = 255.0
        out.append(np.round(v).astype(np.uint8))
    return out


def add_mat(spec: Spec, name: str, ramp, like: str | None = None, **kw) -> int:
    """Append a material to spec.mats / spec.names (idempotent); `like` copies the shading flags."""
    if name in spec.names:
        return spec.names[name]
    if like is not None:
        base = spec.mats[spec.names[like]]
        m = dataclasses.replace(base, name=name, ramp=ramp, glossy=False, rim_k=base.rim_k * 0.6, **kw)
    else:
        m = Material(name, ramp, **kw)
    spec.mats.append(m)
    spec.names[name] = len(spec.mats) - 1
    return spec.names[name]


def add_soot_materials(spec: Spec) -> None:
    for n in SOOTY:
        if n in spec.names:
            for lv, k in LEVELS.items():
                add_mat(spec, twin(n, lv), soot_ramp(spec.mats[spec.names[n]].ramp, k), like=n)
    add_mat(spec, 'ash', [np.array([*hex_rgb(h), 255], np.uint8) for h in ASH], outline=False, rim_ok=False)


# ----------------------------------------------------------------------------------- soot hook
HANDS = ('hand_n', 'hand_f', 'hand_l', 'hand_r', 'hand_n2', 'hand_l2', 'hand_r2', 'hand2')
CUFFS = ('cuff_n', 'cuff_f', 'cuff_l', 'cuff_r')
LEGS = ('shin_n', 'shin_f', 'shin_l', 'shin_r', 'thigh_n', 'thigh_f', 'thigh_l', 'thigh_r')
SCARF = ('scarf_roll', 'scarf_tuck', 'scarf_end', 'scarf_end1')
# ragged upper edge of the blackened hem, by column relative to the pelvis (moves with the body: no shimmer)
HEM_DEPTH = (3, 2, 3, 4, 2, 3, 3, 2, 4, 3, 2, 3, 4)
# head-anchor offsets (dx, dy) of the smears (only skin pixels are touched) and of the ash flakes (only hat)
SMEAR = {
    ('alexei', 'side'): [(0, -2), (1, -1)],
    ('alexei', 'front'): [(-3, -2), (-2, -1), (2, -2)],
    ('konrad', 'side'): [(2, -5), (0, -2), (1, -1)],
    ('konrad', 'front'): [(-3, -2), (-2, -1), (1, -5)],
}
ASH_FLAKES = {
    ('alexei', 'side'): [(-2, -9), (2, -8)],
    ('alexei', 'front'): [(-2, -9), (2, -8)],
    ('alexei', 'back'): [(-1, -9), (2, -8)],
    ('konrad', 'side'): [(-1, -9), (2, -10)],
    ('konrad', 'front'): [(-2, -9), (1, -10)],
    ('konrad', 'back'): [(-2, -9), (1, -10)],
}


def _parts(fr, names) -> np.ndarray:
    ids = [i for i, n in enumerate(fr.names) if n in names]
    return np.isin(fr.part, ids) if ids else np.zeros(fr.mat.shape, bool)


def _repaint(fr, spec: Spec, mask: np.ndarray, level: str) -> None:
    """Pixels of `mask` -> the `level` soot twin of their own material (where the twin exists)."""
    ys, xs = np.nonzero(mask & (fr.mat >= 0))
    for y, x in zip(ys, xs):
        t = spec.names.get(twin(spec.mats[fr.mat[y, x]].name, level))
        if t is not None:
            fr.mat[y, x] = t


def _hem(fr, spec: Spec, J) -> None:
    """Blackened hem (ragged band of 2..4 px) under a band of grey dust (3 px, checkered upper edge)."""
    coat = _parts(fr, ('coat',)) & (fr.mat == spec.names['coat'])
    px, py = int(math.floor(J['pelvis'][0])), int(math.floor(J['pelvis'][1]))
    heavy = np.zeros_like(coat)
    dust = np.zeros_like(coat)
    for x in np.nonzero(coat.any(0))[0]:
        ys = np.nonzero(coat[:, x])[0]
        d = HEM_DEPTH[(x - px) % len(HEM_DEPTH)]
        low = ys.max()
        heavy[ys[ys > low - d], x] = True
        band = ys[(ys <= low - d) & (ys > low - d - 3)]
        for y in band:
            if y > low - d - 3 + 1 or (x - px + y - py) % 2 == 0:
                dust[y, x] = True
    _repaint(fr, spec, heavy, 'heavy')
    _repaint(fr, spec, dust, 'dust')


def _at_head(fr, spec: Spec, J, offsets, mat_name: str):
    hx, hy = int(math.floor(J['head_at'][0])), int(math.floor(J['head_at'][1]))
    want = spec.names.get(mat_name)
    for dx, dy in offsets:
        x, y = hx + dx, hy + dy
        if 0 <= x < fr.w and 0 <= y < fr.h and fr.mat[y, x] == want:
            yield x, y


def soot_hook(base_id: str, view: str):
    """Last hook layer ('front'): blacken hem, cuffs, hands, legs, scarf; smear the face; ash on the hat."""
    def fn(fr, J, P, spec):
        _hem(fr, spec, J)
        _repaint(fr, spec, _parts(fr, CUFFS), 'heavy')
        _repaint(fr, spec, _parts(fr, HANDS), 'heavy')
        _repaint(fr, spec, _parts(fr, LEGS), 'dust')
        _repaint(fr, spec, _parts(fr, SCARF), 'dust')
        smear = np.zeros(fr.mat.shape, bool)
        for x, y in _at_head(fr, spec, J, SMEAR.get((base_id, view), ()), 'skin'):
            smear[y, x] = True
        face = np.isin(fr.mat, [spec.names[n] for n in ('skin', 'hair') if n in spec.names])
        _repaint(fr, spec, _parts(fr, ('head',)) & face & ~smear, 'dust')   # smoke-grey face and hair
        _repaint(fr, spec, smear, 'smudge')
        ash = spec.names['ash']
        for x, y in _at_head(fr, spec, J, ASH_FLAKES.get((base_id, view), ()), 'hat'):
            fr.recolor(x, y, ash, 4)
    return fn


# ----------------------------------------------------------------------------------- the file (carry rows)
AKTE = '#A88E5C'          # buff registry board (reads against the dark coats)
STRING = ['#3A342A', '#6A604E', '#948A74', '#B8AE96', '#D4CCB4', '#E8E2CC']
PAPER = C3.PAPER
# side view: the file carried at the side under the near arm, seen face-on: grey-brown board, the pages
# showing at the top edge, the tied string, one scorched corner (anchor = bottom front corner, at the hand)
AKTE_SIDE = ['.pPpPp.',
             'obbbbco',
             'obsbbco',
             'obbsbco',
             'obbbsco',
             'obbbbco',
             'oabbbxo',
             'oabbxxo',
             '.ooox..']
AKTE_LG = {'o': ('akte', 0), 'a': ('akte', 1), 'b': ('akte', 2), 'c': ('akte', 3),
           'p': ('paper', 3), 'P': ('paper', 2), 's': ('string', 3), 'x': (twin('akte', 'heavy'), 1)}
CARRY_HOLD = (10.0, 34.0)          # near arm: clamps the file to the side, the hand under its edge


def add_carry_materials(spec: Spec) -> None:
    from chargen_core import make_ramp
    add_mat(spec, 'akte', make_ramp(AKTE, spec.scene))
    add_mat(spec, twin('akte', 'heavy'), soot_ramp(spec.mats[spec.names['akte']].ramp, LEVELS['heavy']), like='akte')
    add_mat(spec, 'paper', [np.array([*hex_rgb(h), 255], np.uint8) for h in PAPER])
    add_mat(spec, 'string', [np.array([*hex_rgb(h), 255], np.uint8) for h in STRING], outline=False)


def akte_side(fr, J, P, spec):
    """Drawn in the 'head' layer: after the body, before the near arm (the forearm lies over the file)."""
    if not P.get('carry'):
        return
    x, y = J['wr_n']
    put_bitmap(fr, bm(AKTE_SIDE, AKTE_LG, anchor=(6, 8)), spec.names, x + 2.2, y + 0.5, name='akte')


def _carry_style(style):
    s = dict(style or {})
    s['hold_n'] = CARRY_HOLD
    return s


def carry_side(style=None):
    """Walk cycle with the file: chargen_anim.walk_side with the near arm locked (same feet, same ground speed)."""
    frames = A.walk_side(_carry_style(style))
    for P in frames:
        P['carry'] = True
        P['hand_n'] = 'fist'
    return frames


def carry_idle_side(style=None):
    frames = A.idle_side(_carry_style(style))
    for P in frames:
        P['carry'] = True
        P['hand_n'] = 'fist'
    return frames


ANIMS_C3P2 = {
    'carry_side': ('side', carry_side, 10, True),
    'carry_idle_side': ('side', carry_idle_side, 5, True),
}
CARRY_ROWS = ['carry_side', 'carry_idle_side']


# ----------------------------------------------------------------------------------- protagonists
def _sooty(base_id: str):
    spec = CAST_BASE[base_id]()
    spec.id = base_id + '_soot'
    add_carry_materials(spec)
    add_soot_materials(spec)
    hooks = {k: list(v) for k, v in spec.hooks.items()}
    hooks.setdefault('side', []).append(('head', akte_side))
    for view in ('side', 'front', 'back'):
        hooks.setdefault(view, []).append(('front', soot_hook(base_id, view)))
    spec.hooks = hooks
    return spec


def alexei_soot():
    return _sooty('alexei')


def konrad_soot():
    return _sooty('konrad')


# ----------------------------------------------------------------------------------- Frau Brunner at night
NIGHT = ['#4E4A48', '#827C76', '#ACA69C', '#CAC4B8', '#DED9CE', '#EEEAE2']      # pale cotton nightdress


def typist_night():
    """Frau Brunner (C3_DESIGN section 5) woken by the fire: her dark winter coat thrown over the nightdress,
    felt boots, the near hand holding the collar shut; no pencil behind the ear, no steno pad, no sleeve
    protectors.  Proportions, head and walk are those of `typist`."""
    base = C3.typist()
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': '#3C3236',            # aubergine-brown wool
        'skirt': NIGHT,               # the nightdress below the coat
        'trouser': '#8A7C74',         # bare ankles / thick stockings
        'boot': ('#2C2628', {}),      # felt boots
        'patch': '#3A3436',
        'shirt': NIGHT,               # nightdress collar at the throat
        'skin': C3.SKIN_C3[scene],
        'hair': ['#140E0C', '#2A1C16', '#3E2A20', '#563C2C', '#6E503A', '#88664A'],
        'eye': C3.EYE_B,
        'button': '#1E181A',
        'glass': C3.GLASS,
    })
    lg = HD.base_legend()
    lg.update({'p': ('hair', 3), 'P': ('hair', 2)})          # no pencil: loose hair over the ear
    style = dict(base.style)
    style.update(hold_n=None, talk_n=None, talk_hand_n=None, gesture='touch_collar', arm_n_idle=(10.0, 118.0),
                 arm_f_idle=(-4.0, 14.0), front_l=(8.0, 0.8, -112.0), stride=4.0, swing=12.0)
    spec = dataclasses.replace(
        base, id='typist_night', mats=mats, names=names,
        coat=Coat(mat='coat', hem=-12.5, back=4.2, front=4.3, flare=0.9, chest=1.1, collar=1.8,
                  width_f=5.3, waist_f=4.8, hem_f=5.3, R=2.3, cyl=0.65, folds=0.7),
        skirt=Skirt(mat='skirt', top=3.0, hem=-17.6, back=3.3, front=3.4, flare=1.0, hem_f=4.3, waist_f=3.7,
                    folds=0.4),
        arm_r=(1.6, 1.4),
        heads=C3.heads(lg, C3.TYPIST_SIDE, C3.TYPIST_FRONT, side_talk={(9, 7): 'M'}, front_talk={(5, 7): 'M'}),
        boots=C3.ladies_boots('boot'),
        style=style, hooks={})
    spec.hooks = {'side': [('coat', night_coat_side)], 'front': [('coat', night_coat_front)]}
    return spec


def night_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    pts = [body(c.front - 1.7, T + 0.8), body(c.front + 0.1, T - 0.2), body(c.front - 0.3, T - 2.1),
           body(c.front - 1.5, T - 1.5)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='night_collar')
    column_line(fr, spec, J, c.front - 0.9, c.hem + 1, T - 2, 'coat', -0.7)      # the coat's front edge
    buttons(fr, spec, J, c.front - 0.9, (T - 4.5, T - 8.0, 0.5, -3.5), tone=1)
    flap(fr, spec, J, c.front - 3.4, c.front - 1.6, -2.5, 'coat')                 # pocket


def night_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(-1.7, T + 0.7), body(1.7, T + 0.7), body(0.7, T - 2.3), body(-0.7, T - 2.3)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=0.8, cyl=0.2, cast=False, name='night_collar')
    column_line(fr, spec, J, 0.5, spec.coat.hem + 1, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, 1.3, (T - 4.5, T - 8.0, 0.5, -3.5), tone=1)
    flap(fr, spec, J, -4.2, -2.4, -2.5, 'coat')
    flap(fr, spec, J, 2.4, 4.2, -2.5, 'coat')


# ----------------------------------------------------------------------------------- tables
CAST_C3P2 = {'alexei_soot': alexei_soot, 'konrad_soot': konrad_soot, 'typist_night': typist_night}
BASE_OF = {'alexei_soot': 'alexei', 'konrad_soot': 'konrad', 'typist_night': 'typist'}
# figure height (px, idle_side frame 0, incl. headgear): the variants keep their base's
EXPECT_H_C3P2 = {'alexei_soot': (45, 47), 'konrad_soot': (47, 49), 'typist_night': (40, 45)}


def rows_c3p2(base_rows: dict) -> dict:
    """Rows of every variant: the base's rows in the base's order (indices never move), carry rows appended
    to the protagonists."""
    return {'alexei_soot': list(base_rows['alexei']) + CARRY_ROWS,
            'konrad_soot': list(base_rows['konrad']) + CARRY_ROWS,
            'typist_night': list(C3.ROWS_C3['typist'])}
