"""chargen_cast_c3 -- Chapter 3 cast (Free City of Veltrava) for the character rig.

Seven new characters built through the EXISTING rig (chargen_core / chargen_body / chargen_anim) and the
helpers of chargen_cast (materials, legends, boots, hands, buttons, seams).  Nothing in the existing
generators is modified: the two new lighting scenes are added to chargen_core.SCENE_TINT in memory when
this module is imported, and character-specific animation (talk gestures, held props) is expressed as
pose lists in `spec.style['anims_c3']` which characters_c3.py dispatches to.

Scenes:  'veltrava' -- station at a cold slate-blue dawn, warm lamps (shadow tint slate blue, light amber)
         'palais'   -- conference palace interior: cold window daylight, warm chandeliers (navy-teal shadow)

Cast (documentation/C3_DESIGN.md section 5):
    elena, border_officer, conductor, voronova  -> 'veltrava'  (elena / voronova also appear in the palais)
    kessler, typist, journalist                -> 'palais'
Deterministic: no randomness.
"""
from __future__ import annotations

import math

import numpy as np

import chargen_anim as A
import chargen_core as C
from chargen_body import Coat, Skirt, Spec, M
from chargen_core import Bitmap, capsule, put_bitmap
from chargen_cast import (EYE_B, bm, boot_bitmaps, buttons, column_line, digit_legend, faces, hand_bitmaps,
                          materials, merge, put_line, put_poly, quilt_lines, side_light, skin_legend, walking)

# ----------------------------------------------------------------------------------- scenes
# OKLCh hue / chroma of the shadow and light tint used for ramp hue shifting (measured from the
# data/chapters/c3.json palettes: veltrava slate h~254, lamp h~70; palais night h~237, amber h~73).
C.SCENE_TINT.setdefault('veltrava', dict(shadow_h=255.0, shadow_c=0.046, light_h=72.0, light_c=0.060))
C.SCENE_TINT.setdefault('palais', dict(shadow_h=238.0, shadow_c=0.044, light_h=73.0, light_c=0.062))

SKIN_C3 = {
    'veltrava': ['#261A28', '#583746', '#885551', '#B47B65', '#D5A081', '#EAC6A5'],
    'palais': ['#281B26', '#5B383D', '#88564E', '#B47D63', '#D4A17F', '#EAC7A4'],
}
RIM_C3 = {
    'veltrava': np.array([162, 180, 206, 255], np.uint8),   # cold slate-blue dawn from behind
    'palais': np.array([155, 181, 200, 255], np.uint8),     # window daylight
}

WHITE_BAND = ['#4A505C', '#7C8490', '#A9B0BA', '#CDD2D8', '#E2E5E8', '#F2F3F4']   # commission armband
SLATE_BAND = ['#141C2A', '#22304A', '#33476A', '#44608A', '#5A78A0', '#7290B4']   # slate-blue stripe
BLACK_BOOK = ['#08080B', '#101014', '#18181E', '#24242C', '#34343E', '#4C4C58']
PAPER = ['#3E3C34', '#7C7868', '#A8A390', '#C9C3AC', '#DED8C2', '#EEE9D6']
BRASS = ['#2E2210', '#5E4418', '#8E6A2A', '#B88E40', '#DEB660', '#F2D88E']
VISOR = ['#07080B', '#101216', '#1A1D22', '#272B32', '#3E444E', '#646C78']
GLASS = ['#101318', '#1E242C', '#3A4652', '#7A8C9A', '#B4C6D0', '#E4EEF2']
CHROME = ['#16171A', '#2C2E32', '#4C4F54', '#7A7E84', '#A8ACB0', '#D6D8DA']


def _part(fr, name):
    """Id of the most recently drawn part called `name` (or None)."""
    for i in range(len(fr.names) - 1, -1, -1):
        if fr.names[i] == name:
            return i
    return None


def band_on_limb(fr, spec, part_name, a, b, bands):
    """Paint cloth bands around a limb: pixels of `part_name` whose projection on a->b lies in one of the
    [t0, t1) intervals get that material (auto-shaded, keeps the limb's normals and outline)."""
    pid = _part(fr, part_name)
    if pid is None:
        return
    ys, xs = np.nonzero(fr.part == pid)
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy or 1.0
    for y, x in zip(ys, xs):
        t = ((x + 0.5 - ax) * dx + (y + 0.5 - ay) * dy) / L2
        for t0, t1, mname in bands:
            if t0 <= t < t1:
                fr.mat[y, x] = M(spec, mname)
                fr.tone[y, x] = np.nan
                break


def put_hand(fr, spec, key, x, y, name='hand2'):
    put_bitmap(fr, spec.hands[key], spec.names, x, y, name=name)


def lg_mat(m, chars):
    """chars[i] -> tone i of material m (i = 0..5)."""
    return {ch: (m, i) for i, ch in enumerate(chars)}


# ----------------------------------------------------------------------------------- poses
def talk_c3(style):
    """talk_side superset: per-frame near / far arm, hands, face, head offset and lean."""
    s = A.st(style)
    base = A.talk_side(style)
    n = len(base)
    for i, P in enumerate(base):
        for key, pkey in (('talk_n', 'arm_n'), ('talk_f', 'arm_f'), ('talk_hand_n', 'hand_n'),
                          ('talk_hand_f', 'hand_f'), ('talk_face', 'face'), ('talk_head', 'head'),
                          ('talk_lean', 'lean')):
            seq = s.get(key)
            if seq is not None:
                P[pkey] = seq[i % len(seq)]
        if s.get('talk_f') is None and s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
    return base[:n]


def idle_c3(style):
    """idle_side with optional per-frame near arm / face / head sequences (6 frames)."""
    s = A.st(style)
    frames = A.idle_side(style)
    for i, P in enumerate(frames):
        for key, pkey in (('idle_n_seq', 'arm_n'), ('idle_f_seq', 'arm_f'), ('idle_face', 'face'),
                          ('idle_head', 'head'), ('idle_hand_n', 'hand_n')):
            seq = s.get(key)
            if seq is not None:
                P[pkey] = seq[i % len(seq)]
    return frames


def front_c3(style):
    """idle_front with fixed arm poses for held props (front_l / front_r = (abd, swing, flex))."""
    s = A.st(style)
    frames = A.idle_front(style)
    for P in frames:
        if s.get('front_l') is not None:
            P['arm_l'] = s['front_l']
        if s.get('front_r') is not None:
            P['arm_r'] = s['front_r']
    return frames


DEFAULT_ANIMS = {'talk_side': talk_c3, 'idle_side': idle_c3, 'idle_front': front_c3}


def with_anims(style: dict, **extra) -> dict:
    style = dict(style)
    a = dict(DEFAULT_ANIMS)
    a.update(extra)
    style['anims_c3'] = a
    return style


# ----------------------------------------------------------------------------------- footwear
def ladies_boots(m='boot', sole=None):
    """Slim low-heeled winter ankle boots (women): 4 px foot instead of 5."""
    s = sole or m
    lg = {'a': (s, 1), 'b': (m, 2), 'c': (m, 3), 'd': (m, 4), 'o': (s, 0)}
    return dict(
        side_flat=Bitmap(['bc..', 'bccd', 'aaaa'], lg, anchor=(1, 1)),
        side_heel=Bitmap(['bc.d', 'bccd', 'aaa.'], lg, anchor=(1, 1)),
        side_toe=Bitmap(['bc..', 'bccd', '.aaa'], lg, anchor=(1, 1)),
        side_toe2=Bitmap(['bc..', 'bcd.', '.bcd', '..aa'], lg, anchor=(1, 1)),
        front=Bitmap(['bc', 'bd', 'aa'], lg, anchor=(0, 1)),
        back=Bitmap(['bc', 'bc', 'aa'], lg, anchor=(0, 1)),
    )


# =================================================================================== ELENA
def elena():
    """Elena Weiss (30s), interpreter of the commission: slim, upright, quick.  Charcoal wool coat to
    mid-calf, wine-red scarf (her one warm accent), dark hair pinned low at the nape, white armband with a
    slate-blue band on the left (near) upper arm, black notebook held to the chest by the far arm."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#4C4A52', {'bias': 0.08}),
        'trouser': '#2A282E',
        'boot': '#1F1B1D',
        'patch': '#3A3436',
        'scarf': '#7A2638',
        'skin': SKIN_C3[scene],
        'hair': '#3A2C2A',
        'eye': EYE_B,
        'band': WHITE_BAND,
        'stripe': SLATE_BAND,
        'book': BLACK_BOOK,
        'paper': PAPER,
        'button': '#1C1C22',
    })
    lg = merge(skin_legend(), digit_legend('hair'))
    side_rows = [
        '...1233...',
        '..124333..',
        '.1243SSS..',
        '.1232sSSL.',
        '.123rSSeL.',
        '.122sSSSL.',
        '1221rsSSm.',
        '0221.rsS..',
        '.10..ss...',
    ]
    front_rows = [
        '..12221..',
        '.1233321.',
        '123sSSs21',
        '12SeLeS21',
        '1rSSLsSr1',
        '.rsSmSsr.',
        '..rsSsr..',
        '...sSs...',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 8), blink={(7, 4): 'S'}, talk={(8, 6): 'M'}),
        'front': faces(front_rows, lg, anchor=(4, 7), blink={(3, 3): 's', (5, 3): 's'}, talk={'m': 'M'}),
    }
    spec = Spec(id='elena', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.6, torso=12.4, neck=1.7, thigh=9.6, shin=9.5, uarm=7.0, farm=6.0,
                leg_r=(1.35, 1.15), arm_r=(1.4, 1.2), hip_f=1.5,
                coat=Coat(mat='coat', hem=-14.0, back=3.5, front=3.4, flare=1.3, chest=0.7, collar=1.4,
                          width_f=4.8, waist_f=3.4, hem_f=4.5, R=2.1, cyl=0.7),
                heads=heads, boots=ladies_boots('boot'), hands=hand_bitmaps('skin'),
                lean=0.0,
                style=with_anims(dict(
                    stride=6.0, swing=18.0, bob=1, walk_lean=2.0, hem=0.8, lift=2.6, idle_feet=(1.0, -1.0),
                    hold_f=(4.0, 128.0), arm_n_idle=(3.0, 10.0),
                    talk_n=[(6.0, 40.0), (14.0, 88.0), (18.0, 96.0), (10.0, 66.0)],
                    talk_hand_n=['side', 'side_open', 'side_open', 'side'],
                    talk_head=[(0, 0), (0, 0), (0, 1), (0, 0)],
                    front_l=(-6.0, 0.0, -290.0))))
    spec.hooks = {'side': [('coat', elena_coat_side), ('coat', elena_notebook_side),
                           ('front', elena_armband_side)],
                  'front': [('coat', elena_coat_front), ('arms', elena_arms_front)]}
    return spec


SCARF_RED = {'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4), 'e': ('scarf', 5),
             'o': ('scarf', 0)}
ARMBAND = [(0.34, 0.50, 'band'), (0.50, 0.64, 'stripe')]     # white band, slate-blue stripe below
BOOK_LG = {'o': ('book', 0), 'a': ('book', 1), 'b': ('book', 2), 'c': ('book', 3), 'd': ('book', 4),
           'p': ('paper', 3), 'P': ('paper', 4)}


def elena_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -14, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 6.0, T - 9.5, 1.5), tone=1)
    # wine-red scarf wrapped high around the neck, one short end over the coat front
    x, y = body(0.3, T + 1.4)
    ph = P.get('phase', 0)
    lag = 1 if walking(P) and ph % 4 in (1, 2) else 0
    sc = bm(['.bcdd', 'bccdd', 'obccd', '..bcd', '...bc'], SCARF_RED, anchor=(2, 0))
    put_bitmap(fr, sc, spec.names, x - lag, y, name='scarf')


def elena_notebook_side(fr, J, P, spec):
    # black notebook pressed to the chest by the far hand (drawn over the coat, under the near arm)
    x, y = J['wr_f']
    nb = bm(['oab', 'abc', 'abc', 'abc', 'abc', 'oaa'], BOOK_LG, anchor=(1, 2))
    put_bitmap(fr, nb, spec.names, x + 0.5, y, name='notebook')
    fr.recolor(x + 1.5, y - 1.0, M(spec, 'paper'), 3)       # page edge catching the light
    fr.recolor(x + 1.5, y + 0.0, M(spec, 'paper'), 2)
    put_hand(fr, spec, 'side', x - 0.4, y - 0.6, name='hand_f2')


def elena_armband_side(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_n', J['sh_n'], J['el_n'],
                 ARMBAND)


def elena_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, 0.5, -14, T - 2, 'coat', -0.8)
    buttons(fr, spec, J, 1.4, (T - 6.0, T - 9.5, 1.5), tone=1)
    x, y = body(0.0, T + 1.6)
    sc = bm(['.bccdc.', 'obccddb', '.obccb.', '..bcd..', '..bc...'], SCARF_RED, anchor=(3, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


def elena_arms_front(fr, J, P, spec):
    # notebook pressed to the chest by her right hand (screen left), drawn over the forearm
    body = J['body']
    T = J['T']
    x, y = body(-1.0, T - 2.0)
    nb = bm(['oabP', 'abcp', 'abcp', 'abcp', 'oaao'], BOOK_LG, anchor=(1, 0))
    put_bitmap(fr, nb, spec.names, x, y, name='notebook')
    put_hand(fr, spec, 'front_l', x - 0.2, y + 3.0, name='hand_l2')
    band_on_limb(fr, spec, 'uarm_r', J['sh_r'], J['el_r'], ARMBAND)


# =================================================================================== BORDER OFFICER
def border_officer():
    """Frontier officer of the Free City (50s): slate-blue greatcoat, peaked cap with a small bridge
    badge, white armband, grey moustache, rubber stamp in hand; bored but decent."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': '#3B4B62',
        'trouser': '#2C3240',
        'boot': '#1C1A1E',
        'patch': '#3A3436',
        'cap': '#34435A',
        'visor': VISOR,
        'badge': WHITE_BAND,
        'band': WHITE_BAND,
        'belt': '#2A2624',
        'skin': SKIN_C3[scene],
        'hair': '#66625C',
        'stache': '#5C5650',
        'eye': EYE_B,
        'stamp': '#8E6842',
        'rubber': ['#0A0A0C', '#141416', '#202024', '#2E2E34', '#44444C', '#5E5E68'],
        'button': '#8E949C',
    })
    lg = merge(skin_legend(), digit_legend('cap'), {'v': ('visor', 1), 'V': ('visor', 3), 'h': ('hair', 2),
                                                   'H': ('hair', 3), 'k': ('cap', 1), 'B': ('badge', 4, 'f'),
                                                   'w': ('stache', 2), 'W': ('stache', 3)})
    side_rows = [
        '.122333344',
        '.123334455',
        '..kkkkkBk.',
        '..011vvVVV',
        '..hrssSS..',
        '..hrSSeS..',
        '..hhSSSLL.',
        '...hswWW..',
        '....sSSm..',
        '.....ss...',
    ]
    front_rows = [
        '.12333321.',
        '1233443321',
        '.kkkBkkk1.',
        '.0vVVVVv0.',
        '..sSSSSs..',
        '..SeLSes..',
        '..SSLSss..',
        '..swWWws..',
        '...sSms...',
        '....ss....',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 9), blink={(6, 5): 'S'}, talk={(7, 8): 'M'}),
        'front': faces(front_rows, lg, anchor=(5, 9), blink={(3, 5): 's', (6, 5): 's'}, talk={'m': 'M'}),
    }
    spec = Spec(id='border_officer', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=21.8, torso=13.8, neck=1.5, leg_r=(1.8, 1.6), arm_r=(1.7, 1.45),
                coat=Coat(mat='coat', hem=-14.0, back=4.4, front=4.9, flare=1.4, chest=0.2, collar=1.8,
                          width_f=6.2, waist_f=5.2, hem_f=5.7, R=2.4, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=-1.5, head_off=(0.3, 0.0),
                style=with_anims(dict(
                    stride=4.6, swing=12.0, bob=1, walk_lean=0.5, lift=2.6, hem=0.4, idle_feet=(1.5, -1.5),
                    arm_n_idle=(10.0, 62.0), arm_f_idle=(-6.0, 14.0),
                    talk_n=[(10.0, 62.0), (18.0, 98.0), (22.0, 112.0), (12.0, 70.0)],
                    talk_hand_n=['side', 'side', 'side', 'side'],
                    talk_head=[(0, 0), (0, 0), (0, 1), (0, 0)],
                    front_r=(4.0, 0.0, 6.0))))
    spec.hooks = {'side': [('coat', officer_coat_side), ('front', officer_stamp_side)],
                  'front': [('coat', officer_coat_front), ('arms', officer_arms_front)]}
    return spec


STAMP_LG = {'k': ('stamp', 4), 'h': ('stamp', 3), 'H': ('stamp', 2), 'r': ('rubber', 2), 'R': ('rubber', 3),
            'o': ('rubber', 1)}


def officer_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-spec.coat.back + 0.3, 2.4), body(spec.coat.front - 0.2, 2.4), 0.6, 'belt',
             tone=2, name='belt')
    column_line(fr, spec, J, spec.coat.front - 1.2, -14, T - 2, 'coat', -0.6)
    for v in (T - 3.0, T - 6.5, 0.0):
        x, y = body(spec.coat.front - 1.2, v)
        fr.recolor(x, y, M(spec, 'button'), 3)
        x, y = body(spec.coat.front - 3.0, v)
        fr.recolor(x, y, M(spec, 'button'), 2)


def officer_stamp_side(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_n', J['sh_n'], J['el_n'], [(0.30, 0.62, 'band')])
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    st = bm(['.k.', '.h.', '.H.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 1))
    put_bitmap(fr, st, spec.names, hx + 0.6, hy, name='stamp')
    put_hand(fr, spec, 'side', hx, hy - 0.2, name='hand_n2')


def officer_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-spec.coat.waist_f - 0.4, 2.4), body(spec.coat.waist_f + 0.4, 2.4), 0.6, 'belt',
             tone=2, name='belt')
    column_line(fr, spec, J, 0.0, -14, 1.5, 'coat', -0.8)
    for v in (T - 3.0, T - 6.5, 0.0):
        for u in (-1.6, 1.6):
            x, y = body(u, v)
            fr.recolor(x, y, M(spec, 'button'), 3 if u > 0 else 2)


def officer_arms_front(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_r', J['sh_r'], J['el_r'], [(0.30, 0.62, 'band')])
    x, y = J['wr_l']
    st = bm(['.k.', '.h.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 0))
    put_bitmap(fr, st, spec.names, x, y + 1.5, name='stamp')
    put_hand(fr, spec, 'front_l', x, y + 0.5, name='hand_l2')


# =================================================================================== CONDUCTOR
def conductor():
    """Schaffner of the Corridor Express (60), German railwayman of the mixed crew: dark navy uniform coat
    with brass buttons, peaked railway cap with a winged-wheel badge (no state insignia), grey moustache,
    conductor's leather bag on a strap, ticket punch in hand; slightly stooped, kind and tired."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#2A3246', {'bias': 0.06}),
        'trouser': '#22252E',
        'boot': '#1E1A1C',
        'patch': '#3A3436',
        'cap': '#232A3C',
        'visor': VISOR,
        'brass': BRASS,
        'skin': SKIN_C3[scene],
        'hair': '#8C8A86',
        'stache': '#9A9690',
        'eye': EYE_B,
        'bag': '#4E3526',
        'strap': '#3A281E',
        'punch': CHROME,
        'button': BRASS,
    })
    lg = merge(skin_legend(), digit_legend('cap'), {'v': ('visor', 1), 'V': ('visor', 3), 'h': ('hair', 2),
                                                   'H': ('hair', 3), 'k': ('cap', 1), 'B': ('brass', 4, 'f'),
                                                   'w': ('stache', 2), 'W': ('stache', 3)})
    side_rows = [
        '..1223333.',
        '..1223334.',
        '..1222334.',
        '..kkkkkBk.',
        '..011vvVVV',
        '..hrssSS..',
        '..hrSSeS..',
        '..hhSSSLL.',
        '...hswWW..',
        '....sSSm..',
        '.....ss...',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 10), blink={(6, 6): 'S'}, talk={(7, 9): 'M'})}
    spec = Spec(id='conductor', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=21.4, torso=13.2, neck=1.2, thigh=10.0, shin=9.8, leg_r=(1.65, 1.5), arm_r=(1.55, 1.3),
                coat=Coat(mat='coat', hem=-9.5, back=4.0, front=4.6, flare=0.9, chest=0.3, collar=1.2,
                          width_f=5.6, waist_f=4.8, hem_f=5.0, R=2.3, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=3.0, stoop=9.0, head_off=(0.8, -0.4),
                style=with_anims(dict(
                    stride=4.4, swing=12.0, bob=1, walk_lean=2.0, lift=2.4, hem=0.5, idle_feet=(1.0, -1.5),
                    arm_n_idle=(8.0, 34.0), arm_f_idle=(-4.0, 14.0),
                    talk_n=[(8.0, 40.0), (16.0, 84.0), (14.0, 96.0), (10.0, 60.0)],
                    talk_hand_n=['side', 'side_open', 'side', 'side'],
                    talk_head=[(0, 0), (0, 1), (0, 1), (0, 0)])))
    spec.hooks = {'side': [('coat', conductor_coat_side), ('front', conductor_punch_side)]}
    return spec


BAG_LG = {'o': ('bag', 0), 'a': ('bag', 1), 'b': ('bag', 2), 'c': ('bag', 3), 'd': ('bag', 4), 'm': ('brass', 4)}
PUNCH_LG = {'a': ('punch', 2), 'b': ('punch', 3), 'c': ('punch', 4), 'd': ('punch', 5)}


def conductor_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -9, T - 2, 'coat', -0.6)
    for v in (T - 3.0, T - 6.0, T - 9.0, 1.0):
        x, y = body(spec.coat.front - 1.0, v)
        fr.recolor(x, y, M(spec, 'brass'), 4)
    # conductor's bag on a strap from the far shoulder to the near hip, bag in front of the belly
    put_line(fr, spec, body(1.8, T - 0.4), body(2.6, 1.6), 0.5, 'strap', tone=2, name='strap')
    ph = P.get('phase', 0)
    sway = (1 if walking(P) and ph in (1, 2, 5, 6) else 0)
    x, y = body(spec.coat.front + 0.2, 1.4)
    bag = bm(['obbbm', 'abccd', 'abccd', 'oaabb'], BAG_LG, anchor=(2, 0))
    put_bitmap(fr, bag, spec.names, x - sway, y, name='bag')


def conductor_punch_side(fr, J, P, spec):
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    pu = bm(['.c', 'ba'], PUNCH_LG, anchor=(0, 1))
    put_bitmap(fr, pu, spec.names, hx + 1.0, hy - 0.2, name='punch')


# =================================================================================== VORONOVA
def voronova():
    """Lidia Voronova (50s), Soviet deputy minister of railways: heavy dark-brown coat with a grey karakul
    shawl collar and a karakul pirozhok hat, leather document folder clamped under the arm; sturdy,
    practical stance (feet apart, chest out)."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#4E3D32', {'bias': 0.05}),
        'trouser': '#2C2626',
        'boot': '#221C1C',
        'patch': '#3A3436',
        'fur': ['#16161A', '#26262C', '#3A3A42', '#55555E', '#72727A', '#929298'],
        'skin': SKIN_C3[scene],
        'hair': '#6E6258',
        'eye': EYE_B,
        'folder': '#946238',
        'clasp': BRASS,
        'button': '#221A16',
    })
    # karakul: dark grey pile with irregular light curl pixels (explicit tones, so the curls ride
    # with the hat instead of swimming over it)
    lg = merge(skin_legend(), digit_legend('fur'), {'h': ('hair', 2), 'H': ('hair', 3), 'g': ('hair', 1)})
    side_rows = [
        '.23343432.',
        'R3424342..',
        'R2432423..',
        '.1212121..',
        '.hhgsSSS..',
        '.hHgSSeL..',
        '.hhrSSSLL.',
        '..hrsSSm..',
        '...rsSS...',
        '....ss....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 9), blink={(6, 5): 'S'}, talk={(7, 7): 'M'})}
    spec = Spec(id='voronova', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.2, torso=12.8, neck=1.0, thigh=9.4, shin=9.3, uarm=7.0, farm=6.0,
                leg_r=(1.6, 1.45), arm_r=(1.75, 1.45), hip_f=1.9,
                coat=Coat(mat='coat', hem=-13.0, back=4.6, front=4.7, flare=1.5, chest=1.0, collar=1.0,
                          width_f=6.0, waist_f=5.2, hem_f=5.6, R=2.6, cyl=0.6),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=-0.8,
                style=with_anims(dict(
                    stride=4.4, swing=10.0, bob=1, walk_lean=1.0, lift=2.4, hem=0.4, idle_feet=(2.0, -2.0),
                    arm_n_idle=(2.0, 22.0), arm_f_idle=(-4.0, 12.0),
                    talk_n=[(2.0, 22.0), (4.0, 70.0), (6.0, 88.0), (3.0, 50.0)],
                    talk_hand_n=['side', 'side_open', 'side_open', 'side'],
                    talk_head=[(0, 0), (0, 0), (0, 1), (0, 0)])))
    spec.hooks = {'side': [('coat', voronova_coat_side), ('head', voronova_folder_side),
                           ('head', voronova_collar_side)]}
    return spec


FOLDER_LG = {'o': ('folder', 0), 'a': ('folder', 1), 'b': ('folder', 2), 'c': ('folder', 3), 'd': ('folder', 4),
             'm': ('clasp', 4)}
FUR_LG = {'0': ('fur', 0), '1': ('fur', 1), '2': ('fur', 2), '3': ('fur', 3), '4': ('fur', 4), '5': ('fur', 5),
          'R': ('fur', 'rim')}


def voronova_coat_side(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.4, -13, T - 3, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.4, (T - 6.0, T - 9.0, 1.0), tone=1)


def voronova_collar_side(fr, J, P, spec):
    # heavy karakul shawl collar: a roll around the neck (back to throat) and a lapel down the coat front
    body = J['body']
    T = J['T']
    x, y = body(0.2, T + 0.6)
    col = bm(['.R2343.', 'R342432', '2432423', '.13242.', '...432.', '...342.', '...24..', '...12..'],
             FUR_LG, anchor=(3, 1))
    put_bitmap(fr, col, spec.names, x, y, name='collar')


def voronova_folder_side(fr, J, P, spec):
    # leather document folder clamped flat under the near arm (drawn before the near arm)
    body = J['body']
    T = J['T']
    x, y = body(1.4, T - 6.0)
    f = bm(['obbbbbc', 'abccccd', 'abcmccd', 'abccccd', 'abccccd', 'oaaaabb'], FOLDER_LG, anchor=(3, 0))
    put_bitmap(fr, f, spec.names, x, y, name='folder')


# =================================================================================== KESSLER
def kessler():
    """Ministerialdirektor Gerhard Kessler (50s), Reich Ministry of Transport: long charcoal overcoat,
    homburg, dark leather gloves, briefcase, thin glasses; very upright.  A civil servant -- no uniform,
    no badges, no pins."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': ('#3A3C43', {'bias': 0.06}),
        'trouser': '#2A2C32',
        'boot': '#141316',
        'patch': '#2A2628',
        'hat': '#2A2A2F',
        'band': ['#060608', '#0C0C10', '#121216', '#1A1A20', '#24242C', '#30303A'],
        'glove': '#3E302A',
        'case': '#3E2B22',
        'clasp': BRASS,
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#2A2834',
        'skin': SKIN_C3[scene],
        'hair': '#625E5A',
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#16161A',
    })
    lg = merge(skin_legend(), digit_legend('hat'), {'k': ('band', 2), 'K': ('band', 3), 'h': ('hair', 2),
                                                   'H': ('hair', 3), 'g': ('glass', 5, 'f'), 'G': ('glass', 1, 'f')})
    side_rows = [
        '....1223..',
        '...123334.',
        '...123334.',
        '.1.kkkkK.4',
        '..01223344',
        '...hssSS..',
        '...rSGgS..',
        '...rSSSLL.',
        '...rSSm...',
        '....sSS...',
        '.....s....',
    ]
    front_rows = [
        '...1223...',
        '..123334..',
        '..123334..',
        '..kkkkkK..',
        '1012233441',
        '..sSSSSs..',
        '..SeGSeS..',
        '..SSLsss..',
        '..sSmSs...',
        '...sSs....',
        '....s.....',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 10), blink={}, talk={'m': 'M'}),
        'front': faces(front_rows, lg, anchor=(4, 10), blink={}, talk={'m': 'M'}),
    }
    spec = Spec(id='kessler', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=23.0, torso=14.0, neck=1.8, thigh=10.6, shin=10.6, leg_r=(1.6, 1.45), arm_r=(1.45, 1.25),
                coat=Coat(mat='coat', hem=-13.0, back=3.8, front=3.8, flare=0.9, chest=0.6, collar=1.6,
                          width_f=5.4, waist_f=4.0, hem_f=4.6, R=2.2, cyl=0.7),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin', glove='glove'),
                lean=-1.5,
                style=with_anims(dict(
                    stride=6.0, swing=10.0, bob=1, walk_lean=0.0, lift=2.6, hem=0.5, idle_feet=(1.0, -1.0),
                    hold_n=(2.0, 4.0), arm_f_idle=(-3.0, 10.0),
                    talk_n=[(2.0, 4.0)] * 4,
                    talk_f=[(-3.0, 10.0), (-8.0, 120.0), (-6.0, 132.0), (-4.0, 92.0)],
                    talk_hand_f=['side', 'side_open', 'side_open', 'side'],
                    talk_head=[(0, 0), (0, 0), (0, -1), (0, 0)],
                    front_r=(3.0, 0.0, 4.0))))
    spec.hooks = {'side': [('coat', kessler_coat_side), ('front', kessler_case_side)],
                  'front': [('coat', kessler_coat_front), ('arms', kessler_case_front)]}
    return spec


CASE_LG = {'o': ('case', 0), 'a': ('case', 1), 'b': ('case', 2), 'c': ('case', 3), 'd': ('case', 4),
           'm': ('clasp', 4), 'n': ('case', 1)}


def kessler_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    # white shirt collar + dark tie in the coat opening at the throat
    pts = [body(spec.coat.front - 1.5, T + 0.8), body(spec.coat.front - 0.1, T - 0.6),
           body(spec.coat.front - 0.1, T - 2.4), body(spec.coat.front - 1.2, T - 2.4)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(spec.coat.front - 0.5, T - 0.8), body(spec.coat.front - 0.4, T - 2.6), 0.5, 'tie',
             tone=2, name='tie')
    column_line(fr, spec, J, spec.coat.front - 1.2, -13, T - 3, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.2, (T - 4.5, T - 8.0, 0.5), tone=1)


def kessler_case_side(fr, J, P, spec):
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    case = bm(['..nn...', '.n..n..', 'obbmbbo', 'abccccd', 'abccccd', 'abccccd', 'oaaaaab'], CASE_LG,
              anchor=(3, 1))
    put_bitmap(fr, case, spec.names, hx + 0.3, hy + 0.6, name='briefcase')
    put_hand(fr, spec, 'side', hx, hy - 0.2, name='hand_n2')


def kessler_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(-1.3, T + 0.6), body(1.3, T + 0.6), body(0.4, T - 3.0), body(-0.4, T - 3.0)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=0.8, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(0.0, T - 0.2), body(0.0, T - 3.0), 0.45, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, 0.6, -13, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, 1.6, (T - 4.5, T - 8.0, 0.5), tone=1)


def kessler_case_front(fr, J, P, spec):
    x, y = J['wr_r']
    case = bm(['.nn.', 'nobn', 'abcd', 'abcd', 'abcd', 'oaab'], CASE_LG, anchor=(1, 0))
    put_bitmap(fr, case, spec.names, x, y + 1.0, name='briefcase')
    put_hand(fr, spec, 'front_r', x, y + 0.6, name='hand_r2')


# =================================================================================== TYPIST
def typist():
    """Frau Brunner (40s, Swiss), commission typist: oatmeal cardigan over a white blouse, dark skirt,
    black sleeve protectors, short set hair with a pencil behind the ear, steno pad in hand."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': '#857356',
        'skirt': '#3C383C',
        'trouser': '#6A5650',
        'boot': '#2A2022',
        'patch': '#3A3436',
        'sleeve': '#1E1E22',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'skin': SKIN_C3[scene],
        'hair': '#5A4232',
        'eye': EYE_B,
        'pencil': '#C09038',
        'paper': PAPER,
        'wire': CHROME,
        'button': '#4A3C2C',
    })
    lg = merge(skin_legend(), digit_legend('hair'), {'p': ('pencil', 4, 'f'), 'P': ('pencil', 2, 'f')})
    side_rows = [
        '...1233...',
        '..123344..',
        '.12343344.',
        '.1232sSS4.',
        '.12p3SSeL.',
        '.1P23SSSLL',
        '.1232sSm..',
        '..12rsS...',
        '....ss....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 8), blink={(7, 4): 'S'}, talk={(7, 6): 'M'})}
    spec = Spec(id='typist', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.4, torso=12.2, neck=1.5, thigh=9.4, shin=9.3, uarm=6.9, farm=5.9,
                leg_r=(1.4, 1.2), arm_r=(1.45, 1.25), hip_f=1.7,
                coat=Coat(mat='coat', hem=-2.0, back=3.8, front=3.9, flare=0.3, chest=1.0, collar=0.4,
                          width_f=5.0, waist_f=4.2, hem_f=4.4, R=2.2, cyl=0.65),
                skirt=Skirt(mat='skirt', top=3.0, hem=-11.0, back=3.6, front=3.7, flare=0.7, hem_f=4.3,
                            waist_f=3.8),
                heads=heads, boots=ladies_boots('boot'), hands=hand_bitmaps('skin'),
                lean=0.5,
                style=with_anims(dict(
                    stride=4.0, swing=16.0, bob=1, walk_lean=1.5, lift=2.4, idle_feet=(1.0, -1.0),
                    hold_n=(8.0, 64.0), arm_f_idle=(-3.0, 12.0),
                    talk_n=[(8.0, 64.0), (14.0, 92.0), (12.0, 104.0), (8.0, 70.0)],
                    talk_hand_n=['side', 'side_open', 'side', 'side'],
                    talk_head=[(0, 0), (0, 1), (0, 0), (0, 0)])))
    spec.hooks = {'side': [('back1', typist_sleeve_far), ('coat', typist_coat_side), ('front', typist_pad_side)]}
    return spec


PAD_LG = {'w': ('wire', 4), 'W': ('wire', 3), 'p': ('paper', 3), 'P': ('paper', 4), 'q': ('paper', 5),
          'l': ('paper', 2), 'o': ('paper', 1)}


def typist_sleeve_far(fr, J, P, spec):
    put_line(fr, spec, J['el_f'], J['wr_f'], 1.2, 'sleeve', name='protector_f', bias=-1.0)


def typist_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    # white blouse collar at the throat, cardigan front edge with buttons
    pts = [body(spec.coat.front - 1.6, T + 0.6), body(spec.coat.front + 0.2, T - 0.4),
           body(spec.coat.front - 0.2, T - 2.2), body(spec.coat.front - 1.4, T - 1.6)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='blouse')
    column_line(fr, spec, J, spec.coat.front - 0.8, -2, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 0.8, (T - 3.5, T - 6.0, T - 8.5, 2.0), tone=1)
    quilt_lines(fr, spec, J, 'coat', step=2, start=0, vmin=-2, vmax=1.0)     # knitted rib at the hem


def typist_pad_side(fr, J, P, spec):
    put_line(fr, spec, J['el_n'], J['wr_n'], 1.25, 'sleeve', name='protector')
    x, y = J['wr_n']
    pad = bm(['wWw', 'qPp', 'Plp', 'PPp', 'Plo'], PAD_LG, anchor=(1, 1))
    put_bitmap(fr, pad, spec.names, x + 0.6, y, name='pad')
    put_hand(fr, spec, 'side', x + 0.2, y - 0.3, name='hand_n2')


# =================================================================================== JOURNALIST
def journalist():
    """Nils Ekdahl (40s), Swedish newspaper correspondent: brown tweed overcoat, knitted scarf, fair
    tousled hair (bareheaded), camera on a strap at the chest, notebook and pencil in hand."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': '#5C5040',
        'trouser': '#3A3A3E',
        'boot': '#3A2A22',
        'patch': '#4A3A30',
        'scarf': '#2E4A62',
        'skin': SKIN_C3[scene],
        'hair': '#A08A5A',
        'eye': EYE_B,
        'camera': ['#08080A', '#121216', '#1C1C22', '#2A2A32', '#3E3E48', '#5A5A66'],
        'chrome': CHROME,
        'strap': '#2A2220',
        'paper': PAPER,
        'button': '#2E2620',
    })
    lg = merge(skin_legend(), digit_legend('hair'))
    side_rows = [
        '...23443..',
        '..2344554.',
        '.123445545',
        '.12334sSS.',
        '.1233rSeL.',
        '.1232SSSLL',
        '..122sSm..',
        '...1rsS...',
        '.....s....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 8), blink={(7, 4): 'S'}, talk={(7, 6): 'M'})}
    spec = Spec(id='journalist', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=22.2, torso=13.6, neck=1.8,
                coat=Coat(mat='coat', hem=-9.5, back=4.3, front=4.2, flare=1.0, chest=0.4, collar=1.6,
                          width_f=5.8, waist_f=4.6, hem_f=5.0, R=2.3, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=2.5, stoop=4.0,
                style=with_anims(dict(
                    stride=5.6, swing=20.0, bob=1, walk_lean=3.0, lift=2.8, hem=0.8, idle_feet=(1.5, -1.5),
                    hold_n=(10.0, 70.0), arm_f_idle=(-6.0, 16.0),
                    talk_n=[(10.0, 70.0), (22.0, 96.0), (16.0, 84.0), (8.0, 60.0)],
                    talk_hand_n=['side', 'side_open', 'side', 'side'],
                    talk_head=[(0, 0), (0, 0), (0, 1), (0, 0)])))
    spec.hooks = {'side': [('coat', journalist_coat_side), ('coat', journalist_camera_side),
                           ('front', journalist_notebook_side)]}
    return spec


CAM_LG = {'o': ('camera', 0), 'a': ('camera', 1), 'b': ('camera', 2), 'c': ('camera', 3), 'd': ('camera', 4),
          'x': ('chrome', 3), 'X': ('chrome', 5)}
SCARF_BLUE = {'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4), 'e': ('scarf', 5),
              'o': ('scarf', 0)}
NOTE_LG = {'p': ('paper', 3), 'P': ('paper', 4), 'q': ('paper', 5), 'l': ('paper', 2), 'o': ('paper', 1)}


def tweed(fr, spec, J, mat='coat'):
    """Tweed: a sparse deterministic speckle of darker / lighter flecks, anchored to the pelvis so it
    rides with the body (no swimming during bob / breathing)."""
    mid = M(spec, mat)
    yy, xx = np.mgrid[0:fr.h, 0:fr.w]
    px, py = int(math.floor(J['pelvis'][0])), int(math.floor(J['pelvis'][1]))
    u, v = xx - px + 64, yy - py + 64
    h = (u * 73 + v * 151 + (u * v) % 7 * 31) % 23
    sel = (fr.mat == mid) & np.isnan(fr.tone)
    fr.bias[sel & (h < 3)] -= 0.8
    fr.bias[sel & (h == 11)] += 0.6


def journalist_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    tweed(fr, spec, J)
    column_line(fr, spec, J, spec.coat.front - 1.0, -9, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 4.0, T - 7.5, 0.0), tone=1)
    x, y = body(0.4, T + 1.2)
    ph = P.get('phase', 0)
    lag = 1 if walking(P) and ph % 4 in (1, 2) else 0
    sc = bm(['.bcdd', 'bccdd', 'obbcd', '..bcd', '..bc.', '..ab.', '..b..'], SCARF_BLUE, anchor=(2, 0))
    put_bitmap(fr, sc, spec.names, x - lag, y, name='scarf')


def journalist_camera_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(0.4, T + 0.6), body(spec.coat.front + 0.4, T - 4.0), 0.45, 'strap', tone=1,
             name='cam_strap')
    ph = P.get('phase', 0)
    sway = (1 if walking(P) and ph in (2, 3, 6, 7) else 0)
    x, y = body(spec.coat.front + 0.6, T - 4.2)
    cam = bm(['xX..', 'abdc', 'abo.'], CAM_LG, anchor=(1, 0))
    put_bitmap(fr, cam, spec.names, x + sway, y, name='camera')


def journalist_notebook_side(fr, J, P, spec):
    x, y = J['wr_n']
    nb = bm(['oPq', 'lPP', 'lPp', 'olp'], NOTE_LG, anchor=(1, 1))
    put_bitmap(fr, nb, spec.names, x + 0.8, y - 0.4, name='notebook')
    put_hand(fr, spec, 'side', x + 0.2, y - 0.2, name='hand_n2')


# ----------------------------------------------------------------------------------- tables
CAST_C3 = {
    'elena': elena, 'border_officer': border_officer, 'conductor': conductor, 'voronova': voronova,
    'kessler': kessler, 'typist': typist, 'journalist': journalist,
}
ROWS_C3 = {
    'elena': ['idle_side', 'walk_side', 'idle_front', 'talk_side'],
    'border_officer': ['idle_side', 'talk_side', 'idle_front'],
    'conductor': ['idle_side', 'walk_side', 'talk_side'],
    'voronova': ['idle_side', 'talk_side'],
    'kessler': ['idle_side', 'talk_side', 'idle_front'],
    'typist': ['idle_side', 'talk_side'],
    'journalist': ['idle_side', 'walk_side', 'talk_side'],
}
# figure height (px, idle_side frame 0, incl. headgear) the validator expects
EXPECT_H_C3 = {
    'elena': (41, 45), 'border_officer': (44, 49), 'conductor': (43, 48), 'voronova': (41, 46),
    'kessler': (45, 50), 'typist': (40, 45), 'journalist': (44, 48),
}
