"""chargen_cast -- the cast: materials, garments, props and per-character hooks (round 2 redesign).

Bitmap legends map a character to (material, tone[, flags]):  tone 0..5 = ramp slot (0 outline,
1 deep shadow, 2 shadow, 3 base, 4 light, 5 highlight), None = auto-shaded.  flags: 'f' = fixed pixel
(no outline / rim), 'd' = darker (-1).  Heads live in chargen_heads.py (hand-drawn, all views).
1964 costume notes per character are in documentation/asset_manifest_parts/characters.md.
"""
from __future__ import annotations

import math

import numpy as np

import chargen_anim as A
import chargen_heads as HD
from chargen_body import Coat, Skirt, Spec, M, make_hands
from chargen_core import (Bitmap, Light, Material, add, capsule, ellipse, make_ramp, poly, put_bitmap,
                          ramp_from_hex, rot)

SKIN = {
    'karsk': ['#2A1C22', '#5A3A3A', '#865548', '#B07A5E', '#CE9C7A', '#E6C2A0'],
    'berlin': ['#2B1A24', '#5C3540', '#8A5550', '#B67D66', '#D7A182', '#EDC7A6'],
    'old': ['#2A1C22', '#5A3C3E', '#87605A', '#AE8574', '#CCA38E', '#E2C4AE'],
    'ruddy': ['#2A1A1E', '#5E3434', '#8E5446', '#B6765A', '#D29876', '#E8BC98'],
}

RIM = {
    'karsk': np.array([168, 196, 184, 255], np.uint8),
    'berlin': np.array([170, 172, 200, 255], np.uint8),
    'archive': np.array([150, 178, 196, 255], np.uint8),
}

EYE_K = ['#0A0E12', '#141A1F', '#3A2226', '#7E8A86', '#B9C6C0', '#E8EDE6']
EYE_B = ['#0A0B12', '#15141F', '#3A2230', '#7E808A', '#B9BCC6', '#E8E8EE']
GLASS = ['#101318', '#1E242C', '#3A4652', '#8A9AA6', '#B4C6D0', '#EEF4F4']


def materials(scene: str, table: dict):
    """table: name -> base hex | (base hex, kwargs) | list of 6 hexes.  Returns (mats, names)."""
    mats, names = [], {}
    for i, (name, spec) in enumerate(table.items()):
        kw = {}
        if isinstance(spec, tuple):
            spec, kw = spec
        if isinstance(spec, list):
            ramp = ramp_from_hex(spec)
        else:
            ramp = make_ramp(spec, scene)
        mats.append(Material(name, ramp, **kw))
        names[name] = i
    return mats, names


def side_light():
    return Light(key=(0.78, 0.42, 0.46), rim=(-0.80, 0.45, -0.30), ambient=0.16,
                 thresholds=(0.28, 0.62, 0.82, 0.96))


def merge(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


def tones(m, chars='oabcde'):
    """chars -> tones 0..5 of material m."""
    return {ch: (m, i) for i, ch in enumerate(chars)}


# ----------------------------------------------------------------------------------- footwear
def boot_bitmaps(m='boot', sole=None, style='heavy'):
    """Footwear.  Anchor = ankle pixel; the sole sits on the row below the ankle row (ground row)."""
    s = sole or m
    lg = {'o': (s, 0), 'a': (s, 1), 'b': (m, 2), 'c': (m, 3), 'd': (m, 4), 'e': (m, 5), 'p': ('patch', 3),
          'q': ('patch', 4), 'g': (s, 1)}
    if style == 'heavy':        # kirza boots: shaft over the trousers, square toe, heel
        d = dict(
            side_flat=(['bcd...', 'bcd...', 'bccd..', 'bcccde', 'oaaaao'], (1, 3)),
            side_heel=(['bcd...', 'bcd...', 'bccd.e', 'bcccd.', 'oaaa..'], (1, 3)),
            side_toe=(['bcd...', 'bccd..', 'bcccd.', '.bccde', '..oaao'], (1, 3)),
            side_toe2=(['bcd..', 'bccd.', '.bccd', '..bcd', '...ao'], (1, 3)),
            front=(['bcd', 'bcd', 'bcd', 'bcde', 'oaao'], (1, 3)),
            back=(['bcb', 'bcb', 'bcb', 'bccb', 'oaao'], (1, 3)),
        )
    elif style == 'shoe':       # leather street shoes (glossy toe cap)
        d = dict(
            side_flat=(['bcc..', 'bccde', 'oaaao'], (1, 1)),
            side_heel=(['bcc.e', 'bccd.', 'oaa..'], (1, 1)),
            side_toe=(['bcc..', '.bcde', '..aao'], (1, 1)),
            side_toe2=(['bc...', 'bcd..', '.bcd.', '..ao.'], (1, 1)),
            front=(['bcd', 'bcde', 'oaao'], (1, 1)),
            back=(['bcb', 'bccb', 'oaao'], (1, 1)),
        )
    elif style == 'lady':       # women's low-heeled shoes, stockings show
        d = dict(
            side_flat=(['bc..', 'bcde', 'o.ao'], (1, 1)),
            side_heel=(['bc.e', 'bcd.', 'o.a.'], (1, 1)),
            side_toe=(['bc..', '.bcd', '..ao'], (1, 1)),
            side_toe2=(['bc..', '.bc.', '..bo'], (1, 1)),
            front=(['bc', 'bcd', 'oao'], (1, 1)),
            back=(['bc', 'bcb', 'o.o'], (1, 1)),
        )
    elif style == 'valenki':    # felt boots: tall, round, no heel; dark rubber galosh at the bottom
        d = dict(
            side_flat=(['bccd.', 'bccd.', 'bcccd', 'gggggo'], (1, 2)),
            side_heel=(['bccd.', 'bccd.', 'bcccd', 'gggg.'], (1, 2)),
            side_toe=(['bccd.', 'bccd.', '.bcccd', '..gggo'], (1, 2)),
            side_toe2=(['bcd..', 'bccd.', '.bccd', '..bcd', '...go'], (1, 2)),
            front=(['bccd', 'bccd', 'bccd', 'gggo'], (1, 2)),
            back=(['bccb', 'bccb', 'bccb', 'gggo'], (1, 2)),
        )
    elif style == 'child':      # small felt boots
        d = dict(
            side_flat=(['bcd.', 'bccd', 'gggo'], (1, 1)),
            side_heel=(['bcd.', 'bccd', 'ggg.'], (1, 1)),
            side_toe=(['bcd.', '.bccd', '..ggo'], (1, 1)),
            side_toe2=(['bcd.', '.bcd', '..go'], (1, 1)),
            front=(['bcd', 'bcd', 'ggo'], (1, 1)),
            back=(['bcb', 'bcb', 'ggo'], (1, 1)),
        )
    else:                       # tall riding boots (guard): glossy shaft up to below the knee
        d = dict(
            side_flat=(['bcde.', 'bcde.', 'bcdd.', 'bcdd.', 'bccdd', 'oaaao'], (1, 4)),
            side_heel=(['bcde.', 'bcde.', 'bcdd.', 'bcdd.', 'bccde', 'oaaa.'], (1, 4)),
            side_toe=(['bcde.', 'bcde.', 'bcdd.', 'bccdd', '.bccd', '..aao'], (1, 4)),
            side_toe2=(['bcd..', 'bcde.', 'bcdd.', '.bcdd', '..bcd', '...ao'], (1, 4)),
            front=(['bcde', 'bcde', 'bcdd', 'bcdd', 'bcdd', 'oaao'], (1, 4)),
            back=(['bccb', 'bccb', 'bccb', 'bccb', 'bccb', 'oaao'], (1, 4)),
        )
    return {k: Bitmap(rows, lg, anchor=anc) for k, (rows, anc) in d.items()}


# ----------------------------------------------------------------------------------- helpers
def put_poly(fr, spec, pts, mat, tone=None, R=1.5, cyl=0.5, cast=True, name='poly', bias=0.0, inline=False):
    m, x0, y0, n = poly(pts, R=R, cyl=cyl)
    return fr.put(m, x0, y0, M(spec, mat), n, tone=tone, cast=cast, name=name, bias=bias, inline=inline)


def put_line(fr, spec, a, b, r, mat, tone=None, cast=False, name='line', bias=0.0):
    m, x0, y0, n = capsule(a, b, r)
    return fr.put(m, x0, y0, M(spec, mat), n, tone=tone, cast=cast, name=name, bias=bias)


def bm(rows, legend, anchor):
    return Bitmap(rows, legend, anchor=anchor)


def buttons(fr, spec, J, u, vs, mat='button', tone=2):
    for v in vs:
        x, y = J['body'](u, v)
        fr.recolor(x, y, M(spec, mat), tone)


def column_line(fr, spec, J, u, v0, v1, mat_name, dt=-1.0):
    """Darken a vertical seam (front edge of a coat) in body space."""
    mid = M(spec, mat_name)
    v = v0
    while v <= v1:
        x, y = J['body'](u, v)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] == mid:
            fr.bias[yi, xi] += dt
        v += 1.0


def flap(fr, spec, J, u0, u1, v, mat_name):
    """Pocket flap: dark seam line with a lit lip directly below it."""
    row_line(fr, spec, J, u0, u1, v, mat_name, -1.0)
    row_line(fr, spec, J, u0 + 0.5, u1, v - 1.0, mat_name, +0.8)


def row_line(fr, spec, J, u0, u1, v, mat_name, dt=-1.0):
    """Darken a short horizontal seam / pocket flap in body space."""
    mid = M(spec, mat_name)
    u = u0
    seen = set()
    while u <= u1 + 1e-6:
        x, y = J['body'](u, v)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if (xi, yi) not in seen and 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] == mid:
            fr.bias[yi, xi] += dt
            seen.add((xi, yi))
        u += 0.5


def quilt_lines(fr, spec, J, mat_name, step=3, start=1, vmin=-99, vmax=99, light=None):
    """Horizontal quilting seams: every `step`-th row of a material is darkened where the cloth faces
    the key light (seams read on lit cloth, the shadow side stays calm)."""
    mid = M(spec, mat_name)
    py = J['pelvis'][1]
    L = np.asarray(light if light is not None else spec.light.key, np.float32)
    L = L / np.linalg.norm(L)
    facing = (fr.n * L).sum(-1) > 0.35
    for y in range(fr.h):
        v = py - y - 0.5
        if v < vmin or v > vmax or (int(math.floor(v)) - start) % step != 0:
            continue
        row = (fr.mat[y] == mid) & np.isnan(fr.tone[y]) & facing[y]
        fr.bias[y][row] -= 1.0


def belt_side(fr, spec, J, v, mat='belt', buckle='metal', front_u=None, back_u=None):
    c = spec.coat
    fu = c.front - 0.2 if front_u is None else front_u
    bu = -c.back + 0.3 if back_u is None else back_u
    put_line(fr, spec, J['body'](bu, v), J['body'](fu, v), 0.55, mat, tone=None, name='belt')
    if buckle:
        x, y = J['body'](fu - 0.4, v)
        fr.recolor(x, y, M(spec, buckle), 4)


def belt_front(fr, spec, J, v, mat='belt', buckle='metal', half=None):
    c = spec.coat
    W = (c.waist_f + 0.2) if half is None else half
    put_line(fr, spec, J['body'](-W, v), J['body'](W, v), 0.55, mat, tone=None, name='belt')
    if buckle:
        x, y = J['body'](0.0, v)
        fr.recolor(x, y, M(spec, buckle), 4)
        fr.recolor(x - 1, y, M(spec, buckle), 3)


def lapels_front(fr, spec, J, depth=4.0, width=2.2, mat=None, dt=-1.0):
    """V-shaped lapel edges: two darker diagonal lines from the collar to the chest."""
    mid = M(spec, mat or spec.coat.mat)
    T = J['T']
    for sgn in (-1, 1):
        for k in range(int(depth * 2) + 1):
            t = k / (depth * 2)
            u = sgn * width * (1 - t) + sgn * 0.3 * t
            v = T + 0.6 - depth * t
            x, y = J['body'](u, v)
            xi, yi = int(math.floor(x)), int(math.floor(y))
            if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] == mid:
                fr.bias[yi, xi] += dt


def walking(P):
    return bool(P.get('walking'))


def lag_dx(P, k=1.0):
    """Horizontal offset (px, int) of a loose item behind the body (side view: backwards = -x)."""
    return -int(round(max(0.0, P.get('lag', 0.0)) * k))


# ----------------------------------------------------------------------------------- shared props
SATCHEL_LG = merge(tones('satchel'), {'m': ('metal', 4), 'n': ('metal', 2), 's': ('strap', 2)})
FOLDER_LG = tones('folder')
SCARF_LG = tones('scarf')


def _puff(fr, J, P, spec, mat='breath'):
    """Breath cloud in front of the mouth for the cold-weather gestures (P['puff'] = 1..3)."""
    k = P.get('puff', 0)
    if not k or 'breath' not in spec.names:
        return
    hx, hy = J['head_at']
    shapes = {1: ['.c', 'cd'], 2: ['.cd.', 'cdd.', '.cc.'], 3: ['..c.', '.c.d', '..c.']}
    put_bitmap(fr, bm(shapes[k], {'c': (mat, 3), 'd': (mat, 4)}, (0, 1)), spec.names, hx + 5 + k, hy - 3,
               name='puff', cast=False)


# =========================================================================================== ALEXEI
def alexei():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': ('#3D5A47', {}),
        'trouser': '#3A4248',
        'boot': ('#3A2F28', {'glossy': True}),
        'patch': '#5E4C3B',
        'hat': ('#5E5044', {'texture': 'fur'}),
        'band': '#2A2A30',
        'skin': SKIN['karsk'],
        'hair': '#3A2C24',
        'eye': EYE_K,
        'satchel': ('#7A5639', {'glossy': True}),
        'strap': '#4E3626',
        'metal': '#9A9A8A',
        'button': '#26302A',
        'scarf': ('#55585C', {'texture': 'knit'}),
        'glass': GLASS,
        'breath': ['#6E7C7A', '#8E9C98', '#AEBAB4', '#C4CEC8', '#DCE2DC', '#EEF2EE'],
    })
    lg = HD.base_legend()
    spec = Spec(id='alexei', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.4, neck=1.6,
                coat=Coat(mat='coat', hem=-7.0, back=4.6, front=4.3, flare=0.8, chest=0.6, collar=1.4,
                          width_f=6.0, waist_f=4.6, hem_f=5.0, R=2.4, cyl=0.65, folds=0.6, hunch=0.3),
                heads=HD.alexei(lg), boots=boot_bitmaps('boot', style='heavy'), hands=make_hands('skin'),
                lean=2.0, arm_r=(1.85, 1.55), leg_r=(1.8, 1.6),
                style=dict(stride=6.9, swing=24.0, bob=1, walk_lean=3.0, gesture='blow_hands', talk_front_arm='r',
                           arm_n_idle=(6.0, 12.0), arm_f_idle=(-5.0, 10.0)))
    spec.hooks = {'side': [('coat', alexei_coat_side), ('coat', satchel_side), ('head', alexei_scarf_side),
                           ('head', alexei_flaps_side), ('front', _puff)],
                  'front': [('coat', alexei_coat_front), ('head', alexei_scarf_front), ('head', alexei_flaps_front)],
                  'back': [('coat', alexei_coat_back), ('head', alexei_scarf_back)]}
    return spec


def alexei_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    column_line(fr, spec, J, c.front - 1.0, c.hem + 1, T - 2, 'coat', -0.8)
    buttons(fr, spec, J, c.front - 1.0, (T - 3.0, T - 7.0, 0.5))
    flap(fr, spec, J, c.front - 3.4, c.front - 1.6, -2.2, 'coat')     # pocket flap
    x, y = J['ank_n']
    fr.recolor(x + 1, y - 1, M(spec, 'patch'), 4)       # repaired boot: a lighter patch pixel


def satchel_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(1.8, T - 0.4), body(-0.8, 1.2), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['bcddde', 'bcmmdd', 'obcncd', 'obbccc', '.oooa.'], SATCHEL_LG, anchor=(2, 0))
    sway = lag_dx(P) if walking(P) else 0
    bounce = P.get('bounce', 0)
    x, y = body(-1.4, 1.4)
    put_bitmap(fr, sat, spec.names, x + sway, y + max(0, -bounce), name='satchel')


def alexei_scarf_side(fr, J, P, spec):
    """Grey knitted scarf tucked into the collar: a rolled band around the neck."""
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.6, T + 1.2), body(1.4, T + 0.6), 1.05, 'scarf', name='scarf_roll')
    put_line(fr, spec, body(1.3, T + 0.5), body(1.8, T - 1.4), 0.75, 'scarf', name='scarf_tuck')


def alexei_flaps_side(fr, J, P, spec):
    """Loose ear-flap tie strings swing with the steps (secondary motion)."""
    hx, hy = J['head_at']
    dx = lag_dx(P) if walking(P) else 0
    dy = 1 if P.get('bounce', 0) < 0 else 0
    for (ox, oy) in ((-3, 1), (-3, 2)):
        x, y = hx + ox + (dx if oy == 2 else 0), hy + oy - dy
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] < 0:
            fr.px(x, y, M(spec, 'band'), 2)


def alexei_coat_front(fr, J, P, spec):
    T = J['T']
    body = J['body']
    column_line(fr, spec, J, 0.6, spec.coat.hem + 1, T - 1, 'coat', -0.9)
    buttons(fr, spec, J, 1.8, (T - 3.0, T - 6.5, 0.5))
    buttons(fr, spec, J, -1.0, (T - 3.0, T - 6.5, 0.5))
    flap(fr, spec, J, -4.0, -2.2, -2.0, 'coat')
    flap(fr, spec, J, 2.2, 4.0, -2.0, 'coat')
    put_line(fr, spec, body(3.8, T + 0.2), body(-3.9, 0.4), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['bcdd', 'bmmd', 'bccd', 'obcc', '.oo.'], SATCHEL_LG, anchor=(2, 0))
    x, y = body(-5.6, 1.2)
    put_bitmap(fr, sat, spec.names, x, y, name='satchel')


def alexei_scarf_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.6, T + 1.0), body(2.6, T + 1.0), 1.0, 'scarf', name='scarf_roll')
    put_line(fr, spec, body(0.8, T + 0.4), body(1.2, T - 1.6), 0.8, 'scarf', name='scarf_tuck')


def alexei_flaps_front(fr, J, P, spec):
    hx, hy = J['head_at']
    for ox in (-4, 4):
        for oy in (1, 2):
            x, y = hx + ox, hy + oy
            xi, yi = int(math.floor(x)), int(math.floor(y))
            if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] < 0:
                fr.px(x, y, M(spec, 'band'), 2)


def alexei_coat_back(fr, J, P, spec):
    T = J['T']
    body = J['body']
    column_line(fr, spec, J, 0.0, spec.coat.hem + 1, T - 3, 'coat', -0.7)
    row_line(fr, spec, J, -3.6, 3.6, T - 4.0, 'coat', -0.8)      # yoke seam
    put_line(fr, spec, body(-3.8, T + 0.2), body(3.9, 0.4), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['bcd', 'bcd', 'obc', '.o.'], SATCHEL_LG, anchor=(1, 0))
    x, y = body(5.6, 1.2)
    put_bitmap(fr, sat, spec.names, x, y, name='satchel')


def alexei_scarf_back(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.6, T + 1.0), body(2.6, T + 1.0), 1.0, 'scarf', name='scarf_roll')


# =========================================================================================== KONRAD
def konrad():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#2E3E63',
        'trouser': '#383848',
        'boot': ('#2A2024', {'glossy': True}),
        'patch': '#4A3A3A',
        'hat': '#4A4245',
        'band': ['#0E0B0D', '#17121A', '#1F1A22', '#2C2430', '#3E3444', '#524858'],
        'scarf': ('#7E6646', {'texture': 'knit'}),
        'skin': SKIN['berlin'],
        'hair': '#7A6248',
        'eye': EYE_B,
        'tube': ('#4E5852', {'max_tone': 4, 'rim_k': 0.35}),
        'cap': '#2B2B2E',
        'folder': ('#5C3A28', {'glossy': True}),
        'strap': '#3A2820',
        'button': '#16141C',
        'glass': GLASS,
        'metal': '#A8A49A',
    })
    lg = HD.base_legend()
    spec = Spec(id='konrad', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.5, torso=13.8, neck=1.6,
                coat=Coat(mat='coat', hem=-11.5, back=4.0, front=3.9, flare=1.3, chest=0.5, collar=1.8,
                          width_f=5.7, waist_f=4.1, hem_f=4.9, R=2.2, cyl=0.7, folds=0.9),
                heads=HD.konrad(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=0.5, arm_r=(1.6, 1.35), leg_r=(1.65, 1.5),
                style=dict(stride=7.0, swing=16.0, bob=1, walk_lean=1.5, hem=0.9, hold_f=(-4.0, 24.0),
                           arm_f_idle=(-4.0, 24.0), arm_n_idle=(5.0, 10.0), gesture='adjust_hat'))
    spec.hooks = {'side': [('back0', konrad_tube_side), ('back1', konrad_folder_side), ('coat', konrad_coat_side),
                           ('head', konrad_scarf_side)],
                  'front': [('back0', konrad_tube_front), ('coat', konrad_coat_front), ('arms', konrad_folder_front),
                            ('head', konrad_scarf_front)],
                  'back': [('coat', konrad_coat_back), ('arms', konrad_folder_back), ('head', konrad_tube_back),
                           ('head', konrad_scarf_back)]}
    return spec


def konrad_tube_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(-3.7, T + 2.8)      # top end sticks out above / behind the shoulder
    b = body(-5.0, 0.2)           # bottom end behind the hip
    put_line(fr, spec, a, b, 1.25, 'tube', name='tube', tone=None)
    put_line(fr, spec, a, (a[0] + (b[0] - a[0]) * 0.1, a[1] + (b[1] - a[1]) * 0.1), 1.3, 'cap', tone=2,
             name='tube_cap')
    put_line(fr, spec, (b[0] + (a[0] - b[0]) * 0.06, b[1] + (a[1] - b[1]) * 0.06), b, 1.3, 'cap', tone=1,
             name='tube_end')


def konrad_tube_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(4.5, T + 2.9)        # sticks out above the right shoulder (screen right)
    b = body(-4.6, -2.5)
    put_line(fr, spec, a, b, 1.2, 'tube', name='tube', bias=-1.0)
    put_line(fr, spec, a, (a[0] - 0.6, a[1] + 0.9), 1.25, 'cap', tone=2, name='tube_cap')


def konrad_tube_back(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(-4.5, T + 2.9)
    b = body(4.6, -2.5)
    put_line(fr, spec, a, b, 1.25, 'tube', name='tube')
    put_line(fr, spec, a, (a[0] + 0.6, a[1] + 0.9), 1.3, 'cap', tone=2, name='tube_cap')
    put_line(fr, spec, (b[0] - 0.4, b[1] - 0.6), b, 1.3, 'cap', tone=1, name='tube_end')


def konrad_folder_side(fr, J, P, spec):
    # leather folder clamped under the far arm: shows behind the back
    x, y = J['wr_f']
    f = bm(['obbbbbbo', 'obcccbbo', 'oaaaaaao'], FOLDER_LG, anchor=(3, 1))
    put_bitmap(fr, f, spec.names, x - 1, y - 4, name='folder', bias=-1.0)


def konrad_folder_front(fr, J, P, spec):
    x, y = J['el_r']
    f = bm(['obd', 'bcd', 'bcd', 'bcd', 'bcd', 'bcd', 'bcc', 'oab'], FOLDER_LG, anchor=(0, 0))
    put_bitmap(fr, f, spec.names, x + 0.3, y - 3, name='folder')


def konrad_folder_back(fr, J, P, spec):
    x, y = J['el_l']
    f = bm(['bbo', 'cbb', 'cbb', 'cbb', 'cbb', 'cbb', 'bba', 'aao'], FOLDER_LG, anchor=(2, 0))
    put_bitmap(fr, f, spec.names, x - 0.3, y - 3, name='folder')


def konrad_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    column_line(fr, spec, J, c.front - 1.2, c.hem + 1, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, c.front - 1.2, (T - 4.5, T - 8.0, -0.5))
    flap(fr, spec, J, c.front - 3.6, c.front - 2.0, -1.0, 'coat')     # pocket flap
    put_line(fr, spec, body(2.2, T - 0.4), body(-2.8, 1.0), 0.5, 'strap', tone=2, name='strap')


def konrad_scarf_side(fr, J, P, spec):
    """Grey-beige wool scarf: a thick roll round the neck, one short end hanging over the chest (swings)."""
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.5, T + 0.6), body(2.0, T + 0.3), 1.15, 'scarf', name='scarf_roll')
    sw = lag_dx(P, 1.0) if walking(P) else 0
    top = body(2.2, T - 0.4)
    bot = body(2.7, T - 3.6)
    put_line(fr, spec, top, (bot[0] + sw, bot[1]), 0.9, 'scarf', name='scarf_end', bias=-0.4)
    fr.px(bot[0] + sw, bot[1] + 1, M(spec, 'scarf'), 2, fixed=False)        # fringe


def konrad_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    lapels_front(fr, spec, J, depth=4.5, width=2.6)
    column_line(fr, spec, J, 0.5, spec.coat.hem + 1, T - 5, 'coat', -0.9)
    buttons(fr, spec, J, 1.4, (T - 5.5, T - 8.5, -0.5))
    flap(fr, spec, J, -4.0, -2.0, -1.0, 'coat')
    flap(fr, spec, J, 2.0, 4.0, -1.0, 'coat')
    put_line(fr, spec, body(-3.7, T + 0.4), body(3.9, 0.5), 0.5, 'strap', tone=2, name='strap')


def konrad_scarf_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.8, T + 0.7), body(2.8, T + 0.7), 1.1, 'scarf', name='scarf_roll')
    put_line(fr, spec, body(-1.4, T - 0.2), body(-1.9, T - 4.2), 0.95, 'scarf', name='scarf_end1')
    fr.px(*body(-2.0, T - 5.0), M(spec, 'scarf'), 2, fixed=False)


def konrad_coat_back(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, 0.0, spec.coat.hem + 1, -2, 'coat', -0.9)   # rear vent
    row_line(fr, spec, J, -2.5, 2.5, 2.5, 'coat', -0.8)                    # half belt
    buttons(fr, spec, J, -2.0, (2.5,))
    buttons(fr, spec, J, 2.0, (2.5,))


def konrad_scarf_back(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.6, T + 1.2), body(2.6, T + 1.2), 1.0, 'scarf', name='scarf_roll')


# =========================================================================================== IRINA
def irina():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#3E5466',
        'skirt': '#352F2C',
        'trouser': '#3A3534',
        'boot': ('#5C5A54', {'texture': 'felt'}),
        'galosh': '#1E1E22',
        'patch': '#6A685E',
        'hat': '#8E3A28',
        'band': '#6A2A1E',
        'skin': SKIN['karsk'],
        'hair': '#33241E',
        'eye': EYE_K,
        'board': '#6E5438',
        'paper': ['#3E3C34', '#7C7868', '#A8A390', '#C9C3AC', '#DED8C2', '#EEE9D6'],
        'metal': '#8C8E80',
        'button': '#1E2428',
        'flag': '#B8963A',
        'belt': '#2A2422',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='irina', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.5, torso=12.4, neck=1.4, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.5, 1.35), arm_r=(1.65, 1.4), hip_f=1.7,
                coat=Coat(mat='coat', hem=-3.5, back=4.0, front=3.9, flare=0.5, chest=0.9, collar=1.2,
                          width_f=5.2, waist_f=3.9, hem_f=4.5, R=2.2, cyl=0.65),
                skirt=Skirt(mat='skirt', top=3.0, hem=-14.0, back=3.4, front=3.4, flare=1.2, hem_f=4.6,
                            waist_f=3.6, folds=0.6),
                heads=HD.irina(lg), boots=boot_bitmaps('boot', sole='galosh', style='valenki'),
                hands=make_hands('skin'), lean=1.0,
                style=dict(stride=4.3, swing=18.0, bob=1, walk_lean=2.0, hold_n=(6.0, 30.0), lift=2.6,
                           talk_front_arm='r', idle_feet=(1.0, -1.0), arm_f_idle=(-3.0, 10.0), gesture='shift',
                           talk_n=[(6.0, 30.0), (10.0, 52.0), (14.0, 74.0), (16.0, 80.0), (12.0, 66.0),
                                   (8.0, 44.0), (12.0, 60.0), (6.0, 34.0)],
                           talk_f=[(-3.0, 10.0)] * 2 + [(4.0, 40.0), (8.0, 56.0), (6.0, 50.0)] + [(-3.0, 10.0)] * 3))
    spec.hooks = {'side': [('coat', irina_coat_side), ('front', clipboard_side)],
                  'front': [('coat', irina_coat_front), ('arms', clipboard_front)]}
    return spec


def irina_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-4, vmax=T - 1)
    column_line(fr, spec, J, c.front - 1.0, -3, T - 2, 'coat', -0.6)
    belt_side(fr, spec, J, 2.2, 'belt', buckle='metal')
    # rolled signal flag tucked into the belt at the back (yellow accent)
    put_line(fr, spec, J['body'](-c.back - 0.4, 4.8), J['body'](-c.back + 0.6, -1.2), 0.6, 'flag', name='flag')


def irina_coat_front(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-4, vmax=T - 1, light=spec.light_front.key)
    column_line(fr, spec, J, 0.0, -3, T - 1, 'coat', -1.0)
    buttons(fr, spec, J, 1.0, (T - 3.0, T - 6.0, 2.0))
    belt_front(fr, spec, J, 2.2, 'belt', buckle='metal')


CLIP_LG = {'a': ('board', 1), 'b': ('board', 2), 'c': ('board', 3), 'o': ('board', 0),
           'p': ('paper', 3), 'P': ('paper', 4), 'w': ('paper', 5), 'l': ('paper', 2), 'm': ('metal', 4)}


def clipboard_side(fr, J, P, spec):
    x, y = J['wr_n']
    cb = bm(['.omm..', 'oPwwPc', 'oplpPc', 'oPPwPc', 'opplPc', 'oPPPpc', 'oaaaab'], CLIP_LG, anchor=(2, 1))
    put_bitmap(fr, cb, spec.names, x + 0.5, y, name='clipboard')
    put_bitmap(fr, spec.hands['fist'], spec.names, x + 0.2, y - 0.4, name='hand_n2')


def clipboard_front(fr, J, P, spec):
    x, y = J['wr_l']
    cb = bm(['.mm.', 'oPwc', 'oplc', 'oPPc', 'oplc', 'oaab'], CLIP_LG, anchor=(2, 1))
    put_bitmap(fr, cb, spec.names, x, y, name='clipboard')


# =========================================================================================== EMIL
def emil():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': '#5D6462',
        'inner': ('#6A5038', {'texture': 'knit'}),
        'trouser': '#33343B',
        'boot': ('#2E2622', {'glossy': True}),
        'patch': '#4A3E36',
        'skin': SKIN['old'],
        'hair': ['#2A2C30', '#4E5054', '#73767A', '#9A9C9C', '#BFC0BC', '#DCDCD6'],
        'glass': GLASS,
        'eye': EYE_B,
        'pencil': '#9A6A3A',
        'button': '#2A2C2C',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#5A2A2C',
        'hat': '#5D6462',
        'band': '#2A2C30',
    })
    lg = HD.base_legend()
    spec = Spec(id='emil', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.0, neck=1.2, thigh=10.0, shin=9.8, uarm=7.2, farm=6.3,
                leg_r=(1.6, 1.45), arm_r=(1.5, 1.3),
                coat=Coat(mat='coat', hem=-10.5, back=3.9, front=3.8, flare=0.9, chest=0.2, collar=1.0,
                          width_f=5.3, waist_f=4.2, hem_f=4.8, R=2.2, cyl=0.65, folds=0.7, hunch=0.6),
                inner='inner', inner_w=1.8,
                heads=HD.emil(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=3.0, stoop=13.0, head_off=(1.0, -0.5),
                style=dict(stride=3.6, swing=10.0, bob=1, walk_lean=2.0, arm_n_idle=(4.0, 18.0),
                           arm_f_idle=(-4.0, 16.0), idle_feet=(1.0, -1.5), gesture='push_glasses',
                           talk_n=[(6.0, 30.0), (10.0, 56.0), (14.0, 82.0), (16.0, 90.0), (12.0, 74.0),
                                   (8.0, 50.0), (12.0, 66.0), (6.0, 36.0)]))
    spec.hooks = {'side': [('coat', emil_coat_side)], 'front': [('coat', emil_coat_front)]}
    return spec


def emil_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    pts = [body(c.front - 1.3, T - 0.8), body(c.front + 0.3, T - 3.0),
           body(c.front + 0.1, 1.5), body(c.front - 1.2, 1.5)]
    put_poly(fr, spec, pts, 'inner', R=1.0, cyl=0.3, cast=False, name='cardigan')
    put_line(fr, spec, body(c.front - 0.6, T - 0.4), body(c.front - 0.2, T - 1.8), 0.5, 'shirt', tone=4, name='collar')
    put_line(fr, spec, body(c.front - 0.1, T - 1.2), body(c.front + 0.2, T - 4.2), 0.45, 'tie', tone=3, name='tie')
    x, y = body(1.4, T - 3.0)
    fr.recolor(x, y, M(spec, 'pencil'), 4)          # pencils in the breast pocket
    fr.recolor(x, y - 1, M(spec, 'pencil'), 3)
    fr.recolor(x - 1, y - 1, M(spec, 'metal' if 'metal' in spec.names else 'pencil'), 2)
    flap(fr, spec, J, c.front - 3.0, c.front - 1.6, -2.0, 'coat')


def emil_coat_front(fr, J, P, spec):
    T = J['T']
    body = J['body']
    put_line(fr, spec, body(-0.6, T + 0.2), body(0.6, T + 0.2), 0.6, 'shirt', tone=4, name='collar')
    put_line(fr, spec, body(0.0, T - 0.3), body(0.0, T - 4.5), 0.5, 'tie', tone=3, name='tie')
    buttons(fr, spec, J, 0.0, (T - 6.0, T - 8.5, 2.0), mat='button', tone=1)
    x, y = body(3.0, T - 3.0)
    fr.recolor(x, y, M(spec, 'pencil'), 4)
    fr.recolor(x, y - 1, M(spec, 'pencil'), 3)


# =========================================================================================== WORKER A
def worker_a():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#4C4E3E',
        'trouser': '#36382F',
        'boot': ('#5E5C56', {'texture': 'felt'}),
        'galosh': '#1E1E22',
        'patch': '#6A685E',
        'hat': '#5E4E3E',
        'band': '#2E2A28',
        'skin': SKIN['ruddy'],
        'hair': '#2E2620',
        'eye': EYE_K,
        'mitten': '#6E6450',
        'wood': '#7A5E40',
        'steel': '#5A6260',
        'button': '#22241E',
        'glass': GLASS,
        'belt': '#2A2620',
        'metal': '#8C8E80',
    })
    lg = HD.base_legend()
    spec = Spec(id='worker_a', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.6, neck=1.4,
                coat=Coat(mat='coat', hem=-4.0, back=4.9, front=4.7, flare=0.4, chest=0.7, collar=1.4,
                          width_f=6.2, waist_f=5.0, hem_f=5.1, R=2.6, cyl=0.6, hunch=0.4),
                heads=HD.worker_a(lg), boots=boot_bitmaps('boot', sole='galosh', style='valenki'),
                hands=make_hands('mitten', 'mitten'), lean=3.0, arm_r=(1.9, 1.6), leg_r=(1.9, 1.7),
                style=dict(stride=4.8, swing=20.0, bob=1, walk_lean=3.0, hold_n=(18.0, 84.0), lift=2.8,
                           gesture='shift', work='warm'))
    spec.hooks = {'side': [('coat', worker_coat_side), ('coat', shovel_side)],
                  'front': [('coat', worker_coat_front)]}
    return spec


def worker_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    quilt_lines(fr, spec, J, 'coat', step=3, start=1, vmin=-4, vmax=T - 1)
    column_line(fr, spec, J, c.front - 1.0, -4, T - 2, 'coat', -0.6)
    belt_side(fr, spec, J, 1.6, 'belt', buckle='metal')


def worker_coat_front(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=1, vmin=-4, vmax=T - 1, light=spec.light_front.key)
    column_line(fr, spec, J, 0.0, -4, T - 1, 'coat', -1.0)
    buttons(fr, spec, J, 0.9, (T - 3.0, T - 6.0, 4.0))
    belt_front(fr, spec, J, 1.6, 'belt', buckle='metal')


SHOVEL_LG = {'a': ('steel', 1), 'b': ('steel', 2), 'c': ('steel', 3), 'd': ('steel', 4), 'o': ('steel', 0)}


def shovel_side(fr, J, P, spec):
    """Shovel resting on the near shoulder: shaft from the hand (chest height) up over the shoulder,
    blade behind the head.  Hidden while the gesture / work rows free the hand."""
    if P.get('arm_n') != spec.style.get('hold_n'):
        return
    hx, hy = J['wr_n']
    sx, sy = J['sh_n']
    tx, ty = sx - 1.0, sy - 3.0
    dx, dy = tx - hx, ty - hy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    a = (hx - ux * 2.5, hy - uy * 2.5)
    b = (hx + ux * 19.0, hy + uy * 19.0)
    put_line(fr, spec, a, b, 0.6, 'wood', name='shaft', cast=True)
    blade = bm(['.cd.', 'bccd', 'bccd', 'obcc', '.ob.'], SHOVEL_LG, anchor=(2, 4))
    put_bitmap(fr, blade, spec.names, b[0] + ux * 1.5, b[1] + uy * 1.5, name='blade')


# =========================================================================================== BABUSHKA
def babushka():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#40393A',
        'skirt': '#2E2B2A',
        'trouser': '#3A3634',
        'boot': ('#4E4C46', {'texture': 'felt'}),
        'galosh': '#1A1A1E',
        'patch': '#6A685E',
        'hat': '#4A4660',
        'band': '#A8A4B8',
        'skin': SKIN['old'],
        'hair': '#8A8A84',
        'eye': EYE_K,
        'cloth': '#8C7A58',
        'button': '#1E1C1A',
        'glass': GLASS,
        'fur': ('#5A4E44', {'texture': 'fur'}),
    })
    lg = HD.base_legend()
    spec = Spec(id='babushka', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=19.0, torso=12.0, neck=1.0, thigh=8.9, shin=8.8, uarm=6.6, farm=5.8,
                leg_r=(1.5, 1.4), arm_r=(1.6, 1.35),
                coat=Coat(mat='coat', hem=-12.5, back=4.4, front=4.1, flare=1.4, chest=0.6, collar=1.0,
                          width_f=5.4, waist_f=4.6, hem_f=5.3, R=2.4, cyl=0.65, folds=0.6, hunch=0.8),
                heads=HD.babushka(lg), boots=boot_bitmaps('boot', sole='galosh', style='valenki'),
                hands=make_hands('skin'), lean=5.0, stoop=17.0, head_off=(1.2, -0.3),
                style=dict(stride=3.2, swing=10.0, bob=1, walk_lean=2.0, hold_n=(8.0, 10.0), lift=2.0,
                           idle_feet=(1.0, -1.0), gesture='shift'))
    spec.hooks = {'side': [('coat', babushka_coat_side), ('head', fur_collar_side), ('front', bundle_side)],
                  'front': [('coat', babushka_coat_front), ('head', fur_collar_front), ('arms', bundle_front)]}
    return spec


def babushka_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    column_line(fr, spec, J, c.front - 1.0, c.hem + 1, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, c.front - 1.0, (T - 3.5, T - 6.5, 0.0))


def babushka_coat_front(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, 0.5, spec.coat.hem + 1, T - 2, 'coat', -0.8)
    buttons(fr, spec, J, 1.3, (T - 3.5, T - 6.5, 0.0))


def fur_collar_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.2, T + 0.6), body(1.6, T + 0.2), 1.15, 'fur', name='fur_collar')


def fur_collar_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.8, T + 0.6), body(2.8, T + 0.6), 1.15, 'fur', name='fur_collar')


BUNDLE_LG = {'a': ('cloth', 1), 'b': ('cloth', 2), 'c': ('cloth', 3), 'd': ('cloth', 4), 'o': ('cloth', 0)}


def bundle_side(fr, J, P, spec):
    if P.get('arm_n') != spec.style.get('hold_n'):
        return
    x, y = J['wr_n']
    b = bm(['..cd..', '.bccd.', 'obcdcd', 'obccdc', 'obbccc', '.oabb.'], BUNDLE_LG, anchor=(3, 0))
    put_bitmap(fr, b, spec.names, x + 0.5, y + 0.5, name='bundle')
    put_bitmap(fr, spec.hands['fist'], spec.names, x + 0.3, y + 0.3, name='hand_n2')


def bundle_front(fr, J, P, spec):
    x, y = J['wr_r']
    b = bm(['.cd.', 'bccd', 'bcdc', 'obbc', '.oa.'], BUNDLE_LG, anchor=(1, 0))
    put_bitmap(fr, b, spec.names, x, y + 1, name='bundle')


# =========================================================================================== CHILD (Karsk)
def child_a():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#56654F',
        'trouser': '#3A3A3C',
        'boot': ('#5A5852', {'texture': 'felt'}),
        'galosh': '#1E1E22',
        'patch': '#6A685E',
        'hat': ('#9A4434', {'texture': 'knit'}),
        'band': '#2A2A30',
        'scarf': ('#9A4434', {'texture': 'knit'}),
        'skin': SKIN['ruddy'],
        'hair': '#5A4030',
        'eye': EYE_K,
        'mitten': '#9A4434',
        'button': '#22241E',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='child_a', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=12.5, torso=8.4, neck=0.8, thigh=6.0, shin=5.9, ankle_h=2.0, uarm=4.6, farm=4.0,
                leg_r=(1.4, 1.3), arm_r=(1.4, 1.2), hip_f=1.4, sh_v=-1.0,
                coat=Coat(mat='coat', hem=-3.0, back=3.2, front=3.1, flare=0.6, chest=0.3, collar=0.8,
                          width_f=4.3, waist_f=3.6, hem_f=4.0, R=1.8, cyl=0.65),
                heads=HD.child_a(lg), boots=boot_bitmaps('boot', sole='galosh', style='child'),
                hands=make_hands('mitten', 'mitten'), lean=1.0,
                style=dict(stride=3.0, swing=24.0, bob=1, up=-1, walk_lean=2.0, lift=2.0, idle_feet=(1.0, -1.0),
                           gesture='hop', arm_n_idle=(8.0, 14.0)))
    spec.hooks = {'side': [('head', child_scarf_side)], 'front': [('head', child_scarf_front)]}
    return spec


def child_scarf_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.4, T + 0.8), body(1.2, T + 0.5), 0.9, 'scarf', name='scarf_roll')
    sw = lag_dx(P, 1.5) if walking(P) else 0
    a = body(-1.2, T + 0.6)
    fr_end = (a[0] - 1.5 + sw, a[1] + 3.0)
    put_line(fr, spec, a, fr_end, 0.6, 'scarf', name='scarf_tail')


def child_scarf_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.0, T + 0.8), body(2.0, T + 0.8), 0.9, 'scarf', name='scarf_roll')
    put_line(fr, spec, body(1.0, T + 0.4), body(1.4, T - 3.0), 0.6, 'scarf', name='scarf_end')


# =========================================================================================== BERLIN FAMILY
def berlin_father():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#5A4A3C',
        'trouser': '#3A3940',
        'boot': ('#2E2426', {'glossy': True}),
        'patch': '#4A3A3A',
        'hat': ('#5E5A55', {'texture': 'tweed'}),
        'band': '#2A2A30',
        'skin': SKIN['berlin'],
        'hair': '#3A2E26',
        'eye': EYE_B,
        'crate': '#8A6A48',
        'button': '#2A2222',
        'glass': GLASS,
        'cloth': '#7A7268',
        'scarf': ('#4A4A52', {'texture': 'knit'}),
    })
    lg = HD.base_legend()
    spec = Spec(id='berlin_father', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.0, torso=13.6, neck=1.4,
                coat=Coat(mat='coat', hem=-6.0, back=4.2, front=4.0, flare=0.6, chest=0.5, collar=1.3,
                          width_f=5.7, waist_f=4.4, hem_f=4.8, R=2.3, cyl=0.65, folds=0.4),
                heads=HD.berlin_father(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=3.0, arm_r=(1.65, 1.4),
                style=dict(stride=4.6, swing=0.0, bob=1, walk_lean=2.5, hold_n=(26.0, 66.0), hold_f=(26.0, 66.0),
                           talk_front_seq=[(None, f, h) for _a, f, h in A.TALK_FRONT],
                           lift=2.6, dx=-2.5, gesture='hitch', front_abd=4.0))
    spec.hooks = {'side': [('front', crate_side), ('coat', father_coat_side), ('head', father_scarf_side)],
                  'front': [('coat', father_coat_front), ('head', father_scarf_front), ('front', crate_front)]}
    return spec


def father_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    column_line(fr, spec, J, c.front - 1.0, c.hem + 1, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, c.front - 1.0, (T - 4.0, T - 8.0, -1.0))
    flap(fr, spec, J, c.front - 3.4, c.front - 1.8, -1.6, 'coat')


def father_coat_front(fr, J, P, spec):
    T = J['T']
    lapels_front(fr, spec, J, depth=3.5, width=2.4)
    column_line(fr, spec, J, 0.5, spec.coat.hem + 1, T - 4, 'coat', -0.8)
    buttons(fr, spec, J, 1.3, (T - 4.5, T - 8.0, -1.0))


def father_scarf_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.6, T + 1.0), body(1.4, T + 0.6), 0.9, 'scarf', name='scarf_roll')


def father_scarf_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-2.2, T + 1.0), body(2.2, T + 1.0), 0.9, 'scarf', name='scarf_roll')


CRATE_LG = merge(tones('crate'), {'l': ('cloth', 3), 'L': ('cloth', 4)})


def crate_side(fr, J, P, spec):
    # a wooden crate with belongings (a folded blanket on top) carried in front of the chest
    x, y = J['wr_n']
    cr = bm(['..lLLl..', '.oddeed.', 'obccccdd', 'obbbbbbd', 'obccccdc', 'obbbbbbc', 'obccccdc', 'oaaaaaab'],
            CRATE_LG, anchor=(2, 4))
    put_bitmap(fr, cr, spec.names, x, y, name='crate')
    put_bitmap(fr, spec.hands['fist'], spec.names, x + 0.2, y - 0.2, name='hand_n2')


def crate_front(fr, J, P, spec):
    x0, y0 = J['wr_l']
    x1, y1 = J['wr_r']
    cr = bm(['..lLLLLl..', '.odddeeed.', 'obcccccccd', 'obbbbbbbbd', 'obcccccccd', 'oaaaaaaaab'],
            CRATE_LG, anchor=(5, 3))
    put_bitmap(fr, cr, spec.names, (x0 + x1) / 2, (y0 + y1) / 2 - 1, name='crate')


def berlin_mother():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#5C4456',
        'trouser': '#6A5A58',
        'boot': ('#2B2024', {'glossy': True}),
        'patch': '#4A3A3A',
        'hat': '#2F2A33',
        'band': '#5A2A30',
        'skin': SKIN['berlin'],
        'hair': '#6A3E2A',
        'eye': EYE_B,
        'case': ('#6E5038', {'glossy': True}),
        'metal': '#8A8478',
        'belt': '#3A2A30',
        'button': '#2A1E26',
        'glass': GLASS,
        'scarf': ('#8A7A6A', {'texture': 'knit'}),
    })
    lg = HD.base_legend()
    spec = Spec(id='berlin_mother', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.5, torso=12.2, neck=1.4, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.3, 1.1), arm_r=(1.5, 1.25), hip_f=1.6,
                coat=Coat(mat='coat', hem=-11.0, back=3.8, front=3.7, flare=1.5, chest=0.9, collar=1.2,
                          width_f=5.0, waist_f=3.5, hem_f=4.9, R=2.2, cyl=0.65, folds=0.7),
                heads=HD.berlin_mother(lg), boots=boot_bitmaps('boot', style='lady'), hands=make_hands('skin'),
                lean=-1.0,
                style=dict(stride=4.0, swing=16.0, bob=1, walk_lean=1.5, hold_n=(4.0, 4.0), lift=2.4,
                           idle_feet=(1.0, -1.0), gesture='shift'))
    spec.hooks = {'side': [('coat', mother_coat_side), ('front', suitcase_side)],
                  'front': [('coat', mother_coat_front), ('arms', suitcase_front)]}
    return spec


def mother_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    belt_side(fr, spec, J, 3.0, 'belt', buckle='metal')
    column_line(fr, spec, J, c.front - 1.0, c.hem + 1, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, c.front - 1.0, (T - 4.0, 0.0, -4.0))


def mother_coat_front(fr, J, P, spec):
    T = J['T']
    lapels_front(fr, spec, J, depth=3.0, width=2.2)
    belt_front(fr, spec, J, 3.0, 'belt', buckle='metal')
    column_line(fr, spec, J, 0.4, spec.coat.hem + 1, T - 3, 'coat', -0.8)


CASE_LG = merge(tones('case'), {'m': ('metal', 4), 'n': ('metal', 2)})


def suitcase_side(fr, J, P, spec):
    if P.get('arm_n') != spec.style.get('hold_n'):
        return
    x, y = J['wr_n']
    sc = bm(['...nn....', '..n..n...', 'ocddddddd', 'obcccccdd', 'obmccccmc', 'obcccccdc', 'obbbbbbcc',
             'oaaaaaaab'], CASE_LG, anchor=(4, 1))
    put_bitmap(fr, sc, spec.names, x, y + 0.5, name='suitcase')
    put_bitmap(fr, spec.hands['fist'], spec.names, x, y, name='hand_n2')


def suitcase_front(fr, J, P, spec):
    x, y = J['wr_r']
    sc = bm(['.nn.', 'ocdd', 'obcd', 'obmd', 'obcd', 'obcc', 'oaab'], CASE_LG, anchor=(1, 0))
    put_bitmap(fr, sc, spec.names, x + 0.5, y + 1, name='suitcase')


def berlin_child():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#6A5846',
        'trouser': '#8C8478',
        'boot': ('#2B2024', {'glossy': True}),
        'patch': '#4A3A3A',
        'hat': '#343448',
        'band': '#2A2A30',
        'skin': SKIN['berlin'],
        'hair': '#6E5034',
        'eye': EYE_B,
        'toy': ('#8A6A4A', {'texture': 'fur'}),
        'shorts': '#3E3A40',
        'button': '#2A2222',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='berlin_child', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=13.5, torso=8.8, neck=0.8, thigh=6.4, shin=6.4, ankle_h=2.0, uarm=4.8, farm=4.2,
                leg_r=(1.3, 1.15), arm_r=(1.35, 1.15), hip_f=1.4, sh_v=-1.0,
                coat=Coat(mat='coat', hem=-4.0, back=3.1, front=3.0, flare=0.7, chest=0.3, collar=0.8,
                          width_f=4.2, waist_f=3.5, hem_f=4.0, R=1.8, cyl=0.65),
                heads=HD.berlin_child(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=0.0,
                style=dict(stride=3.2, swing=22.0, bob=1, up=-1, walk_lean=2.0, lift=2.0, hold_n=(10.0, 30.0),
                           idle_feet=(1.0, -1.0), gesture='hug'))
    spec.hooks = {'side': [('front', toy_side)], 'front': [('arms', toy_front)]}
    return spec


TOY_LG = merge(tones('toy'), {'e': ('eye', 1)})


def toy_side(fr, J, P, spec):
    x, y = J['wr_n']
    t = bm(['c.c', 'cdc', 'bec', 'bcc', 'b.b'], TOY_LG, anchor=(1, 0))
    put_bitmap(fr, t, spec.names, x + 1, y + 1, name='toy')
    put_bitmap(fr, spec.hands['fist'], spec.names, x + 0.3, y + 0.3, name='hand_n2')


def toy_front(fr, J, P, spec):
    x, y = J['wr_r']
    t = bm(['c.c', 'cdc', 'ece', 'bcc', 'b.b'], TOY_LG, anchor=(1, 0))
    put_bitmap(fr, t, spec.names, x + 0.5, y + 1, name='toy')


# =========================================================================================== CLERK
def clerk():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': '#4C5157',
        'trouser': '#3F434A',
        'boot': ('#1E1A1C', {'glossy': True}),
        'patch': '#3A3436',
        'sleeve': '#4C5157',
        'protector': '#24262C',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#4A2A30',
        'skin': SKIN['berlin'],
        'hair': '#2A2224',
        'eye': EYE_B,
        'file': ['#4A4030', '#7A6A4A', '#A08C62', '#BCA878', '#D2BF8E', '#E4D3A6'],
        'button': '#1C1C22',
        'hat': '#2A2224',
        'band': '#2A2A30',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='clerk', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.0, torso=13.4, neck=1.6,
                coat=Coat(mat='coat', hem=-3.0, back=3.7, front=3.6, flare=0.2, chest=0.4, collar=1.0,
                          width_f=5.3, waist_f=4.0, hem_f=4.1, R=2.0, cyl=0.7),
                heads=HD.clerk(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=0.5, arm_r=(1.45, 1.25), leg_r=(1.6, 1.45),
                style=dict(stride=4.8, swing=16.0, bob=1, walk_lean=1.0, hold_n=(4.0, 70.0), lift=2.6,
                           gesture='shift'))
    spec.hooks = {'side': [('coat', clerk_coat_side), ('front', file_side)],
                  'front': [('coat', clerk_coat_front), ('arms', file_front)]}
    return spec


def clerk_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    pts = [body(c.front - 1.4, T + 0.6), body(c.front - 0.2, T - 0.8),
           body(c.front - 0.2, T - 5.0), body(c.front - 1.1, T - 5.0)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(c.front - 0.5, T - 1.5), body(c.front - 0.4, T - 5.5), 0.5, 'tie',
             tone=3, name='tie')
    buttons(fr, spec, J, c.front - 0.8, (T - 7.0, 1.0))
    flap(fr, spec, J, c.front - 3.0, c.front - 1.6, -0.6, 'coat')


def clerk_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(-1.6, T + 0.4), body(1.6, T + 0.4), body(0.0, T - 5.5)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(0.0, T - 0.5), body(0.0, T - 5.0), 0.5, 'tie', tone=3, name='tie')
    lapels_front(fr, spec, J, depth=5.0, width=2.0)
    buttons(fr, spec, J, 0.5, (T - 7.0, 1.0))


FILE_LG = tones('file')


def file_side(fr, J, P, spec):
    # file folder held under the near forearm; black sleeve protector (Aermelschoner) on the forearm
    put_line(fr, spec, J['el_n'], J['wr_n'], 1.3, 'protector', name='protector')
    if P.get('arm_n') == spec.style.get('hold_n'):
        x, y = J['wr_n']
        f = bm(['oddddeo', 'obccccd', 'obccccd', 'obccccd', 'oaaaaab'], FILE_LG, anchor=(4, 1))
        put_bitmap(fr, f, spec.names, x, y, name='file')
        put_bitmap(fr, spec.hands['fist'], spec.names, x + 0.8, y + 0.2, name='hand_n2')


def file_front(fr, J, P, spec):
    for s in ('l', 'r'):
        put_line(fr, spec, J['el_' + s], J['wr_' + s], 1.2, 'protector', name='protector_' + s)
    x, y = J['wr_r']
    f = bm(['oddd', 'obcd', 'obcd', 'obcd', 'obcd', 'oaab'], FILE_LG, anchor=(1, 1))
    put_bitmap(fr, f, spec.names, x + 0.5, y, name='file')


# =========================================================================================== GUARD
def guard(hist: bool = False):
    """Building guard of the Reich administration.  Armband on the near upper arm (TECHNICAL_ARCHITECTURE
    12.4): neutral sheet = the fictional state's grey-black band with the white 'Reichssiegel' pillar,
    `sheet_hist.png` (hist=True) = the historical red armband with the white disc and black emblem."""
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#55595A',
        'trouser': '#3C3F42',
        'boot': ('#1E1B1D', {'glossy': True}),
        'patch': '#3A3436',
        'hat': '#4E5354',
        'band': ['#08090B', '#121418', '#1E2126', '#2C3036', '#4A5058', '#7A828C'],
        'belt': ('#2A2422', {'glossy': True}),
        'metal': '#9A968A',
        'skin': SKIN['berlin'],
        'hair': '#3A3030',
        'eye': EYE_B,
        'button': '#2E3134',
        'glass': GLASS,
        'collar': '#3E4446',
        'armband': '#9A2A22' if hist else '#2A2A30',
        'emblem': ['#0E0E10', '#1A1A1E', '#2A2A2E', '#C8C8C0', '#E2E2DA', '#F2F2EA'],
    })
    lg = HD.base_legend()
    spec = Spec(id='guard', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.5, torso=14.0, neck=1.4,
                coat=Coat(mat='coat', hem=-14.0, back=4.4, front=4.4, flare=1.6, chest=0.9, collar=1.6,
                          width_f=6.2, waist_f=4.4, hem_f=5.5, R=2.3, cyl=0.65, folds=0.8),
                heads=HD.guard(lg), boots=boot_bitmaps('boot', style='tall'), hands=make_hands('skin'),
                lean=-0.5, arm_r=(1.7, 1.45),
                style=dict(stride=5.0, swing=12.0, bob=1, walk_lean=0.5, lift=2.6, hem=0.4,
                           arm_n_idle=(-24.0, 100.0), arm_f_idle=(-24.0, 100.0), idle_feet=(1.5, -1.5),
                           gesture='rock_heels', front_abd=5.0))
    spec.hooks = {'side': [('coat', guard_coat_side), ('head', guard_collar_side), ('front', guard_armband_side)],
                  'front': [('coat', guard_coat_front), ('head', guard_collar_front), ('arms', guard_armband_front)]}
    spec.hist = hist
    return spec


def _armband(fr, spec, sh, el, r, emblem_at):
    """Band round the upper arm (40..58 % of shoulder -> elbow) + a 2-px emblem on its visible face."""
    a = (sh[0] + (el[0] - sh[0]) * 0.40, sh[1] + (el[1] - sh[1]) * 0.40)
    b = (sh[0] + (el[0] - sh[0]) * 0.58, sh[1] + (el[1] - sh[1]) * 0.58)
    m, x0, y0, n = capsule(a, b, r * 1.0)
    fr.put(m, x0, y0, M(spec, 'armband'), n, name='armband', cast=False)
    ex, ey = emblem_at(a, b)
    if getattr(spec, 'hist', False):
        fr.px(ex, ey, M(spec, 'emblem'), 4)          # white disc ...
        fr.px(ex + 1, ey, M(spec, 'emblem'), 1)      # ... with the black emblem
    else:
        fr.px(ex, ey, M(spec, 'emblem'), 4)          # Reichssiegel: white pillar on the dark band
        fr.px(ex, ey + 1, M(spec, 'emblem'), 3)


def guard_armband_side(fr, J, P, spec):
    _armband(fr, spec, J['sh_n'], J['el_n'], spec.arm_r[0],
             lambda a, b: ((a[0] + b[0]) / 2 + 0.3, (a[1] + b[1]) / 2 - 0.5))


def guard_armband_front(fr, J, P, spec):
    _armband(fr, spec, J['sh_r'], J['el_r'], spec.arm_r[0],
             lambda a, b: ((a[0] + b[0]) / 2 - 0.5, (a[1] + b[1]) / 2 - 0.5))


def guard_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    belt_side(fr, spec, J, 2.6, 'belt', buckle='metal')
    column_line(fr, spec, J, c.front - 1.2, c.hem + 1, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, c.front - 1.2, (T - 3.0, T - 6.0, T - 9.0), mat='button', tone=1)
    flap(fr, spec, J, c.front - 3.2, c.front - 1.6, T - 4.0, 'coat')   # breast pocket flap


def guard_coat_front(fr, J, P, spec):
    T = J['T']
    belt_front(fr, spec, J, 2.6, 'belt', buckle='metal')
    for u in (-1.2, 1.2):
        buttons(fr, spec, J, u, (T - 3.0, T - 6.0, T - 9.0), mat='button', tone=1)
    flap(fr, spec, J, -4.0, -2.0, T - 4.0, 'coat')
    flap(fr, spec, J, 2.0, 4.0, T - 4.0, 'coat')
    column_line(fr, spec, J, 0.0, spec.coat.hem + 1, 1.6, 'coat', -0.8)


def guard_collar_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.6, T + 1.3), body(1.2, T + 0.9), 0.95, 'collar', name='collar')


def guard_collar_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_poly(fr, spec, [body(-2.8, T + 1.6), body(-0.2, T - 0.6), body(0.2, T - 0.6), body(2.8, T + 1.6),
                        body(2.4, T + 0.0), body(-2.4, T + 0.0)], 'collar', R=1.0, cyl=0.3, name='collar')


# historical-insignia variants (TECHNICAL_ARCHITECTURE 12.4): written as sheet_hist.png next to sheet.png,
# identical geometry (the neutral sheet_n.png / sheet.json serve both)
CAST_HIST = {'guard': lambda: guard(hist=True)}

CAST = {
    'alexei': alexei, 'konrad': konrad, 'irina': irina, 'emil': emil,
    'worker_a': worker_a, 'babushka': babushka, 'child_a': child_a,
    'berlin_father': berlin_father, 'berlin_mother': berlin_mother, 'berlin_child': berlin_child,
    'clerk': clerk, 'guard': guard,
}
