"""chargen_cast_c3 -- the Chapter 3 cast (Free City of Veltrava) on the round-2 character rig.

Round 7 (2026-11-06): the cast was first built in a cloud session against the ROUND-1 rig (its helpers
digit_legend / faces / hand_bitmaps no longer exist, so the module could not even be imported any more and the
sheets were frozen round-1 art: 6-frame idles, 4-frame talks, no blink / glance / gesture, no front views for
most).  This version ports every character to the round-2 API used by the rest of the cast:
  * heads are hand-drawn ASCII maps in the chargen_heads format (HD.base_legend + head_views: side / front
    with blink, talk and glance-back variants),
  * hands from chargen_body.make_hands (Kessler wears gloves),
  * 8-frame idle (two-stage breathing), 8-frame talk (two beats + nod, per-frame hands / head), blink, glance
    back, a character gesture, front idle + front talk for everybody (soft turns need the front frame).
Designs (documentation/C3_DESIGN.md section 5) and proportions follow the first version.

Scenes:  'veltrava' -- station at a cold slate-blue dawn, warm lamps (shadow tint slate blue, light amber)
         'palais'   -- conference palace interior: cold window daylight, warm chandeliers (navy-teal shadow)
Both are added to chargen_core.SCENE_TINT when this module is imported (nothing else is patched).
Deterministic: no randomness.
"""
from __future__ import annotations

import math

import numpy as np

import chargen_anim as A
import chargen_core as C
import chargen_heads as HD
from chargen_body import Coat, Skirt, Spec, M, make_hands
from chargen_core import Bitmap, put_bitmap
from chargen_cast import (EYE_B, GLASS, belt_front, bm, boot_bitmaps, buttons, column_line, flap, lag_dx,
                          lapels_front, materials, merge, put_line, put_poly, quilt_lines, row_line, side_light,
                          walking)

# ----------------------------------------------------------------------------------- scenes
# OKLCh hue / chroma of the shadow and light tint used for ramp hue shifting (measured from the
# data/chapters/c3.json palettes: veltrava slate h~254, lamp h~70; palais night h~237, amber h~73).
C.SCENE_TINT.setdefault('veltrava', dict(shadow_h=255.0, shadow_c=0.046, light_h=72.0, light_c=0.060))
C.SCENE_TINT.setdefault('palais', dict(shadow_h=238.0, shadow_c=0.044, light_h=73.0, light_c=0.062))

SKIN_C3 = {
    'veltrava': ['#261A28', '#583746', '#885551', '#B47B65', '#D5A081', '#EAC6A5'],
    'palais': ['#281B26', '#5B383D', '#88564E', '#B47D63', '#D4A17F', '#EAC7A4'],
    'old': ['#261A26', '#58393F', '#865D58', '#AC8271', '#CBA28C', '#E2C3AC'],      # conductor, Voronova
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
CHROME = ['#16171A', '#2C2E32', '#4C4F54', '#7A7E84', '#A8ACB0', '#D6D8DA']
GREY_HAIR = ['#2E2E30', '#55575A', '#7C7E80', '#A2A3A2', '#C4C4BE', '#E0DFD8']


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


def calm_front_hem(fr, spec, J, amount=-0.5, from_v=1.0):
    """Front view: a long neutral-grey coat catches the front key below the waist and reads lighter than
    the chest (like an apron); pull its auto-shaded pixels below the waist a little darker."""
    pid = _part(fr, 'coat')
    if pid is None:
        return
    y0 = J['body'](0.0, from_v)[1]
    sel = (fr.part == pid) & np.isnan(fr.tone)
    sel &= np.arange(fr.h)[:, None] >= y0
    fr.bias[sel] += amount


def put_hand(fr, spec, key, x, y, name='hand2'):
    put_bitmap(fr, spec.hands[key], spec.names, x, y, name=name)


def heads(lg, side, front, **kw):
    """head_views + a neutral back head (hair / hat only) is not needed: NPCs have no back rows."""
    return HD.head_views(lg, side, front, **kw)


# ----------------------------------------------------------------------------------- footwear
def ladies_boots(m='boot', sole=None):
    """Slim low-heeled winter ankle boots (women): 4 px foot instead of 5 (anchor = ankle, sole below)."""
    s = sole or m
    lg = {'o': (s, 0), 'a': (s, 1), 'b': (m, 2), 'c': (m, 3), 'd': (m, 4), 'e': (m, 5)}
    return dict(
        side_flat=Bitmap(['bc..', 'bccd', 'oaao'], lg, anchor=(1, 1)),
        side_heel=Bitmap(['bc.d', 'bccd', 'oaa.'], lg, anchor=(1, 1)),
        side_toe=Bitmap(['bc..', 'bccd', '.oao'], lg, anchor=(1, 1)),
        side_toe2=Bitmap(['bc..', 'bcd.', '.bcd', '..ao'], lg, anchor=(1, 1)),
        front=Bitmap(['bc', 'bcd', 'oao'], lg, anchor=(0, 1)),
        back=Bitmap(['bc', 'bcb', 'oao'], lg, anchor=(0, 1)),
    )


# talk rhythm shared by the cast (round-2 TALK_DEFAULT): rest, lift, beat, beat + nod, settle, lift, small
# beat, rest.  Hands: None = by forearm angle, 'open' = open palm, 'fist' = closed (props held).
TALK_HANDS = [None, None, 'open', 'open', 'open', None, 'open', None]
TALK_NOD = [(0, 0), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0), (0, 0)]


# =================================================================================== ELENA
# dark hair swept back from a side parting into a low chignon at the nape, a loose strand at the temple,
# slim oval face, straight fine nose
ELENA_SIDE = [
    '. . . . k l h h . . .',
    '. . . k l h K K h . .',
    '. . k l h K K j K . .',
    '. . k l h h l s S L .',
    '. k l h l h r S B L .',
    '. k l h k l S S e L .',
    '. k l k . s S S L L H',
    'k l h k . r s S m . .',
    '. k k . . . r s S . .',
    '. . . . . . s @ . . .',
]
ELENA_FRONT = [
    '. . . k l h h k . . .',
    '. . k l h K K h k . .',
    '. k l K j K h h h k .',
    '. k h l s S S s l k .',
    '. k l r B S S B s k .',
    '. k l L e S S e s k .',
    '. . l L S S n s s . .',
    '. . . s S m m S r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def elena():
    """Elena Weiss (30s), interpreter of the commission: slim, upright, quick.  Charcoal wool coat to
    mid-calf, wine-red scarf (her one warm accent), dark hair pinned low at the nape, white armband with a
    slate-blue band on the near upper arm, black notebook held to the chest by the far arm."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#4C4A52', {'bias': 0.08}),
        'trouser': '#2A282E',
        'boot': ('#1F1B1D', {'glossy': True}),
        'patch': '#3A3436',
        'scarf': ('#7A2638', {'texture': 'knit'}),
        'skin': SKIN_C3[scene],
        'hair': ['#0E0B0E', '#1E1719', '#2E2224', '#40302E', '#56403A', '#6E5446'],
        'eye': EYE_B,
        'band': WHITE_BAND,
        'stripe': SLATE_BAND,
        'book': BLACK_BOOK,
        'paper': PAPER,
        'button': '#1C1C22',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='elena', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.6, torso=12.4, neck=1.7, thigh=9.6, shin=9.5, uarm=7.0, farm=6.0,
                leg_r=(1.35, 1.15), arm_r=(1.4, 1.2), hip_f=1.5,
                coat=Coat(mat='coat', hem=-14.0, back=3.5, front=3.4, flare=1.3, chest=0.7, collar=1.4,
                          width_f=4.8, waist_f=3.4, hem_f=4.5, R=2.1, cyl=0.7, folds=0.6),
                heads=heads(lg, ELENA_SIDE, ELENA_FRONT, side_talk={(8, 7): 'M'}, front_talk={(5, 7): 'M'}),
                boots=ladies_boots('boot'), hands=make_hands('skin'), lean=0.0,
                style=dict(stride=6.0, swing=18.0, bob=1, walk_lean=2.0, hem=0.8, lift=2.6, idle_feet=(1.0, -1.0),
                           hold_f=(4.0, 128.0), arm_f_idle=(4.0, 128.0), arm_n_idle=(3.0, 10.0),
                           gesture='tuck_hair', front_r=(-6.0, 0.0, -290.0), talk_front_arm='l',
                           talk_n=[(4.0, 14.0), (8.0, 46.0), (14.0, 84.0), (18.0, 96.0), (14.0, 86.0), (8.0, 52.0),
                                   (12.0, 70.0), (5.0, 22.0)],
                           talk_hand_n=TALK_HANDS, talk_head=TALK_NOD))
    spec.hooks = {'side': [('coat', elena_coat_side), ('coat', elena_notebook_side), ('front', elena_armband_side)],
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
    # wine-red scarf wrapped high around the neck, one short end over the coat front (swings when walking)
    x, y = body(0.3, T + 1.4)
    sw = lag_dx(P, 1.0) if walking(P) else 0
    sc = bm(['.bcdd', 'bccdd', 'obccd', '..bcd', '...bc'], SCARF_RED, anchor=(2, 0))
    put_bitmap(fr, sc, spec.names, x + sw, y, name='scarf')


def elena_notebook_side(fr, J, P, spec):
    # black notebook pressed to the chest by the far hand (drawn over the coat, under the near arm)
    x, y = J['wr_f']
    nb = bm(['oab', 'abc', 'abc', 'abc', 'abc', 'oaa'], BOOK_LG, anchor=(1, 2))
    put_bitmap(fr, nb, spec.names, x + 0.5, y, name='notebook')
    fr.recolor(x + 1.5, y - 1.0, M(spec, 'paper'), 3)       # page edge catching the light
    fr.recolor(x + 1.5, y + 0.0, M(spec, 'paper'), 2)
    put_hand(fr, spec, 'fist', x - 0.4, y - 0.6, name='hand_f2')


def elena_armband_side(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_n', J['sh_n'], J['el_n'], ARMBAND)


def elena_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J)
    column_line(fr, spec, J, 0.5, -14, T - 2, 'coat', -0.8)
    buttons(fr, spec, J, 1.4, (T - 6.0, T - 9.5, 1.5), tone=1)
    x, y = body(0.0, T + 1.6)
    sc = bm(['.bccdc.', 'obccddb', '.obccb.', '..bcd..', '..bc...'], SCARF_RED, anchor=(3, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


def elena_arms_front(fr, J, P, spec):
    # notebook pressed to the chest by her left hand (screen right), drawn over the forearm
    body = J['body']
    T = J['T']
    x, y = body(1.0, T - 2.0)
    nb = bm(['oPpo', 'abcb', 'abcb', 'abcb', 'oaao'], BOOK_LG, anchor=(2, 0))
    put_bitmap(fr, nb, spec.names, x, y, name='notebook')
    put_hand(fr, spec, 'front_r', x + 0.2, y + 3.0, name='hand_r2')
    band_on_limb(fr, spec, 'uarm_l', J['sh_l'], J['el_l'], ARMBAND)


# =================================================================================== BORDER OFFICER
# slate-blue peaked cap with a small white bridge badge, black visor, grey temples, grey moustache, 50s
OFFICER_SIDE = [
    '. . . 1 2 3 3 4 4 . . .',
    '. . 1 2 3 3 4 4 4 5 . .',
    '. . 1 2 2 3 3 3 Z 4 . .',
    '. . 0 u v v v V V x x .',
    '. . . j r r s B S L . .',
    '. . . j h S S e S L . .',
    '. . . h h s S S L L H .',
    '. . . . h r Q W W S . .',
    '. . . . . r s S m . . .',
    '. . . . . r s S . . . .',
    '. . . . . . s @ . . . .',
]
OFFICER_FRONT = [
    '. . 1 2 3 3 4 4 1 . .',
    '. 1 2 3 3 4 4 4 3 1 .',
    '. 1 2 3 3 Z 4 3 3 1 .',
    '. 0 u v V V V v v 0 .',
    '. . j r B S B r j . .',
    '. . j L e S e s j . .',
    '. . . L S n s s . . .',
    '. . . Q W W Q r . . .',
    '. . . s S m S r . . .',
    '. . . . r S r . . . .',
    '. . . . . s @ . . . .',
]


def border_officer():
    """Frontier officer of the Free City (50s): slate-blue greatcoat, peaked cap with a small bridge
    badge, white armband, grey moustache, rubber stamp in hand; bored but decent."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': '#3B4B62',
        'trouser': '#2C3240',
        'boot': ('#1C1A1E', {'glossy': True}),
        'patch': '#3A3436',
        'hat': '#34435A',
        'visor': VISOR,
        'badge': WHITE_BAND,
        'band': WHITE_BAND,
        'belt': '#2A2624',
        'skin': SKIN_C3[scene],
        'hair': GREY_HAIR,
        'stache': ['#1E1C1E', '#3C3836', '#5E5852', '#7E766E', '#9C948A', '#BAB2A6'],
        'eye': EYE_B,
        'stamp': '#8E6842',
        'rubber': ['#0A0A0C', '#141416', '#202024', '#2E2E34', '#44444C', '#5E5E68'],
        'button': '#8E949C',
        'glass': GLASS,
    })
    lg = HD.base_legend(band='visor')
    lg.update({'Z': ('badge', 4, 'f'), 'Q': ('stache', 2), 'W': ('stache', 4)})
    spec = Spec(id='border_officer', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=21.8, torso=13.8, neck=1.5, leg_r=(1.8, 1.6), arm_r=(1.7, 1.45),
                coat=Coat(mat='coat', hem=-14.0, back=4.4, front=4.9, flare=1.4, chest=0.2, collar=1.8,
                          width_f=6.2, waist_f=5.2, hem_f=5.7, R=2.4, cyl=0.65, folds=0.7),
                heads=heads(lg, OFFICER_SIDE, OFFICER_FRONT, side_talk={(8, 8): 'M'}, front_talk={(5, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=-1.5, head_off=(0.3, 0.0),
                style=dict(stride=4.6, swing=12.0, bob=1, walk_lean=0.5, lift=2.6, hem=0.4, idle_feet=(1.5, -1.5),
                           hold_n=(10.0, 62.0), arm_f_idle=(-6.0, 14.0), gesture='rock_heels',
                           front_l=(4.0, 0.3, 30.0), talk_front_arm='r', front_abd=5.0,
                           talk_n=[(10.0, 62.0), (14.0, 80.0), (18.0, 98.0), (22.0, 112.0), (18.0, 100.0),
                                   (12.0, 72.0), (16.0, 90.0), (10.0, 64.0)],
                           talk_hand_n=['fist'] * 8, talk_head=TALK_NOD))
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
    flap(fr, spec, J, spec.coat.front - 3.8, spec.coat.front - 2.2, -2.0, 'coat')


def officer_stamp_side(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_n', J['sh_n'], J['el_n'], [(0.30, 0.62, 'band')])
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    st = bm(['.k.', '.h.', '.H.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 1))
    put_bitmap(fr, st, spec.names, hx + 0.6, hy, name='stamp')
    put_hand(fr, spec, 'fist', hx, hy - 0.2, name='hand_n2')


def officer_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    belt_front(fr, spec, J, 2.4, 'belt', buckle='button')
    column_line(fr, spec, J, 0.0, -14, 1.5, 'coat', -0.8)
    for v in (T - 3.0, T - 6.5, 0.0):
        for u in (-1.6, 1.6):
            x, y = body(u, v)
            fr.recolor(x, y, M(spec, 'button'), 3 if u > 0 else 2)
    lapels_front(fr, spec, J, depth=3.0, width=3.2)


def officer_arms_front(fr, J, P, spec):
    band_on_limb(fr, spec, 'uarm_r', J['sh_r'], J['el_r'], [(0.30, 0.62, 'band')])
    x, y = J['wr_l']
    st = bm(['.k.', '.h.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 0))
    put_bitmap(fr, st, spec.names, x, y + 1.5, name='stamp')
    put_hand(fr, spec, 'front_l', x, y + 0.5, name='hand_l2')


# =================================================================================== CONDUCTOR
# dark navy railway cap with a brass winged-wheel badge (no state insignia), grey hair and a full grey
# moustache, a long tired face; 60
CONDUCTOR_SIDE = [
    '. . . 1 2 3 3 3 3 . . .',
    '. . 1 2 3 3 3 4 4 . . .',
    '. . 1 2 2 3 3 3 Z 4 . .',
    '. . 0 u u v v V V x x .',
    '. . . j r r s B S L . .',
    '. . . j h S S e S L . .',
    '. . . j j s S S S L H .',
    '. . . . j r S S S H . .',
    '. . . . . r J J J j . .',
    '. . . . . r s S m . . .',
    '. . . . . . r s . . . .',
    '. . . . . . s @ . . . .',
]
CONDUCTOR_FRONT = [
    '. . 1 2 3 3 3 3 1 . .',
    '. 1 2 3 3 3 3 3 3 1 .',
    '. 1 2 2 3 Z 3 3 2 1 .',
    '. 0 u v V V V v u 0 .',
    '. . j r B S B r j . .',
    '. . j L e S e s j . .',
    '. . j L S S s s j . .',
    '. . . L S n s s . . .',
    '. . . J J j J J . . .',
    '. . . s S m S r . . .',
    '. . . . r S r . . . .',
    '. . . . . s @ . . . .',
]


def conductor():
    """Schaffner of the Corridor Express (60), German railwayman of the mixed crew: dark navy uniform coat
    with brass buttons, peaked railway cap with a winged-wheel badge (no state insignia), grey moustache,
    conductor's leather bag on a strap, ticket punch in hand; slightly stooped, kind and tired."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#2A3246', {'bias': 0.06}),
        'trouser': '#22252E',
        'boot': ('#1E1A1C', {'glossy': True}),
        'patch': '#3A3436',
        'hat': '#232A3C',
        'visor': VISOR,
        'brass': BRASS,
        'skin': SKIN_C3['old'],
        'hair': GREY_HAIR,
        'eye': EYE_B,
        'bag': ('#4E3526', {'glossy': True}),
        'strap': '#3A281E',
        'punch': CHROME,
        'button': BRASS,
        'glass': GLASS,
    })
    lg = HD.base_legend(band='visor')
    lg.update({'Z': ('brass', 4, 'f')})
    spec = Spec(id='conductor', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=21.4, torso=13.2, neck=1.2, thigh=10.0, shin=9.8, leg_r=(1.65, 1.5), arm_r=(1.55, 1.3),
                coat=Coat(mat='coat', hem=-9.5, back=4.0, front=4.6, flare=0.9, chest=0.3, collar=1.2,
                          width_f=5.6, waist_f=4.8, hem_f=5.0, R=2.3, cyl=0.65, folds=0.6, hunch=0.4),
                heads=heads(lg, CONDUCTOR_SIDE, CONDUCTOR_FRONT, side_talk={(8, 9): 'M'},
                            front_talk={(5, 9): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=3.0, stoop=9.0, head_off=(0.8, -0.4),
                style=dict(stride=4.4, swing=12.0, bob=1, walk_lean=2.0, lift=2.4, hem=0.5, idle_feet=(1.0, -1.5),
                           hold_n=(8.0, 34.0), arm_f_idle=(-4.0, 14.0), gesture='touch_cap',
                           talk_front_arm='l', front_abd=5.0,
                           talk_n=[(8.0, 34.0), (10.0, 50.0), (14.0, 76.0), (16.0, 92.0), (14.0, 80.0),
                                   (10.0, 56.0), (12.0, 70.0), (8.0, 38.0)],
                           talk_hand_n=['fist'] * 8, talk_head=[(0, 0), (0, 0), (0, 1), (0, 1), (0, 0),
                                                                (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('coat', conductor_coat_side), ('front', conductor_punch_side)],
                  'front': [('coat', conductor_coat_front), ('arms', conductor_punch_front)]}
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
    sw = 1 if walking(P) and P.get('phase', 0) in (1, 2, 5, 6) else 0
    x, y = body(spec.coat.front + 0.2, 1.4)
    bag = bm(['obbbm', 'abccd', 'abccd', 'oaabb'], BAG_LG, anchor=(2, 0))
    put_bitmap(fr, bag, spec.names, x - sw, y, name='bag')


def conductor_punch_side(fr, J, P, spec):
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    pu = bm(['.c', 'ba'], PUNCH_LG, anchor=(0, 1))
    put_bitmap(fr, pu, spec.names, hx + 1.0, hy - 0.2, name='punch')


def conductor_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, 0.0, -9, T - 2, 'coat', -0.8)
    for v in (T - 3.0, T - 6.0, T - 9.0, 1.0):
        fr.recolor(*body(0.9, v), M(spec, 'brass'), 4)
    lapels_front(fr, spec, J, depth=2.6, width=2.6)
    put_line(fr, spec, body(3.6, T + 0.2), body(-2.4, 1.0), 0.5, 'strap', tone=2, name='strap')
    x, y = body(-3.2, 0.6)
    bag = bm(['obbm', 'abcd', 'abcd', 'oaab'], BAG_LG, anchor=(2, 0))
    put_bitmap(fr, bag, spec.names, x, y, name='bag')


def conductor_punch_front(fr, J, P, spec):
    x, y = J['wr_r']
    put_bitmap(fr, bm(['c', 'b', 'a'], PUNCH_LG, anchor=(0, 0)), spec.names, x + 1.0, y + 0.6, name='punch')


# =================================================================================== VORONOVA
# karakul "pirozhok" hat (dark brown curly pile, light curl tips), grey-streaked hair in a low knot under
# it, broad square face; 50s
VORONOVA_SIDE = [
    '. . . . R 2 3 2 3 . . .',
    '. . . R 3 2 4 3 2 3 . .',
    '. . . 2 4 3 2 4 3 4 . .',
    '. . . 1 2 1 2 1 2 1 . .',
    '. . . j K r s S S L . .',
    '. . j K h S S B S L . .',
    '. . j K h S S e S L . .',
    '. . k j k s S S L L H .',
    '. . . k . r s S S m . .',
    '. . . . . r s S S . . .',
    '. . . . . . s @ . . . .',
]
VORONOVA_FRONT = [
    '. . R 2 3 2 3 2 3 . .',
    '. R 3 2 4 3 2 4 3 2 .',
    '. 2 4 3 2 4 3 2 4 2 .',
    '. 1 2 1 2 1 2 1 2 1 .',
    '. . K h s S S s h . .',
    '. . K r B S B r h . .',
    '. . j L e S e s K . .',
    '. . . L S n s s . . .',
    '. . . s S m m s . . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def voronova():
    """Lidia Voronova (50s), Soviet deputy minister of railways: heavy dark-brown coat with a karakul
    shawl collar and a karakul pirozhok hat, leather document folder clamped under the arm; sturdy,
    practical stance (feet apart, chest out)."""
    scene = 'veltrava'
    mats, names = materials(scene, {
        'coat': ('#4E3D32', {'bias': 0.05}),
        'trouser': '#2C2626',
        'boot': ('#221C1C', {'glossy': True}),
        'patch': '#3A3436',
        'hat': ['#0C0A0A', '#1A1514', '#2A221F', '#3C312C', '#52443C', '#6C5C50'],     # karakul (dark brown)
        'fur': ('#625850', {'texture': 'fur'}),                                      # karakul collar
        'skin': SKIN_C3['old'],
        'hair': ['#2A2626', '#4A4442', '#6C6460', '#8E8680', '#AEA69E', '#CCC6BE'],
        'eye': EYE_B,
        'folder': ('#946238', {'glossy': True}),
        'clasp': BRASS,
        'button': '#221A16',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='voronova', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.2, torso=12.8, neck=1.0, thigh=9.4, shin=9.3, uarm=7.0, farm=6.0,
                leg_r=(1.6, 1.45), arm_r=(1.75, 1.45), hip_f=1.9,
                coat=Coat(mat='coat', hem=-13.0, back=4.6, front=4.7, flare=1.5, chest=1.0, collar=1.0,
                          width_f=6.0, waist_f=5.2, hem_f=5.6, R=2.6, cyl=0.6, folds=0.7),
                heads=heads(lg, VORONOVA_SIDE, VORONOVA_FRONT, side_talk={(9, 8): 'M'},
                            front_talk={(5, 8): 'M', (6, 8): 'm'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'), lean=-0.8,
                style=dict(stride=4.4, swing=10.0, bob=1, walk_lean=1.0, lift=2.4, hem=0.4, idle_feet=(2.0, -2.0),
                           arm_n_idle=(2.0, 22.0), arm_f_idle=(-4.0, 12.0), gesture='touch_collar',
                           talk_front_arm='l', front_abd=6.0, front_r=(4.0, 0.0, 10.0),
                           talk_n=[(2.0, 22.0), (3.0, 40.0), (5.0, 64.0), (6.0, 84.0), (5.0, 70.0), (3.0, 46.0),
                                   (4.0, 60.0), (2.0, 26.0)],
                           talk_hand_n=TALK_HANDS, talk_head=TALK_NOD))
    spec.hooks = {'side': [('coat', voronova_coat_side), ('coat', voronova_folder_side), ('head', voronova_collar_side)],
                  'front': [('coat', voronova_coat_front), ('head', voronova_collar_front),
                            ('arms', voronova_folder_front)]}
    return spec


FOLDER_LG = {'o': ('folder', 0), 'a': ('folder', 1), 'b': ('folder', 2), 'c': ('folder', 3), 'd': ('folder', 4),
             'm': ('clasp', 4)}


def voronova_coat_side(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.4, -13, T - 3, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.4, (T - 6.0, T - 9.0, 1.0), tone=1)


def voronova_collar_side(fr, J, P, spec):
    """Heavy karakul shawl collar: a fur roll around the neck (back to throat) and a lapel down the front."""
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-3.0, T + 0.4), body(2.6, T + 0.2), 1.45, 'fur', name='collar_roll')
    put_line(fr, spec, body(2.6, T - 0.2), body(3.4, T - 5.0), 1.05, 'fur', name='collar_lapel')


def voronova_collar_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-3.4, T + 0.6), body(3.4, T + 0.6), 1.4, 'fur', name='collar_roll')
    for sgn in (-1, 1):
        put_line(fr, spec, body(sgn * 2.6, T - 0.2), body(sgn * 1.2, T - 5.0), 1.0, 'fur', name='collar_lapel')


def voronova_folder_side(fr, J, P, spec):
    # leather document folder clamped flat under the near arm (drawn before the near arm)
    body = J['body']
    T = J['T']
    x, y = body(1.4, T - 6.0)
    f = bm(['obbbbbc', 'abccccd', 'abcmccd', 'abccccd', 'abccccd', 'oaaaabb'], FOLDER_LG, anchor=(3, 0))
    put_bitmap(fr, f, spec.names, x, y, name='folder')


def voronova_coat_front(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, 0.4, -13, T - 4, 'coat', -0.8)
    buttons(fr, spec, J, 1.4, (T - 6.0, T - 9.0, 1.0), tone=1)


def voronova_folder_front(fr, J, P, spec):
    # the folder under her left arm (screen right) shows as a thin brown edge at the hip
    x, y = J['el_r']
    f = bm(['bd', 'cd', 'cd', 'cd', 'cd', 'ab'], FOLDER_LG, anchor=(0, 0))
    put_bitmap(fr, f, spec.names, x + 0.4, y - 2.0, name='folder')


# =================================================================================== KESSLER
# black homburg (dented crown, curled brim, ribbon), thin rimless glasses catching the light, grey temples,
# narrow ascetic face, thin mouth; 50s
KESSLER_SIDE = [
    '. . . . . 1 2 3 3 . . .',
    '. . . . 1 2 2 3 3 3 . .',
    '. . . . 1 2 3 3 3 4 . .',
    '. . . . u u v v V V . .',
    '. R 1 1 2 2 3 3 3 4 4 .',
    '. . . j r r s B S L . .',
    '. . . j h g S e G L . .',
    '. . . . h s S S L L H .',
    '. . . . r s S S m . . .',
    '. . . . . r s S . . . .',
    '. . . . . . s @ . . . .',
]
KESSLER_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 2 3 3 2 . .',
    '. . 1 2 3 3 3 3 2 . .',
    '. . u u v V V v u . .',
    'R 1 2 2 3 3 3 3 3 2 1',
    '. . j r B S B r j . .',
    '. . j E e S e s j . .',
    '. . . L S n s s . . .',
    '. . . s S m m r . . .',
    '. . . . r S r . . . .',
    '. . . . . s @ . . . .',
]


def kessler():
    """Ministerialdirektor Gerhard Kessler (50s), Reich Ministry of Transport: long charcoal overcoat,
    homburg, dark leather gloves, briefcase, thin glasses; very upright.  A civil servant -- no uniform,
    no badges, no pins."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': ('#3A3C43', {'bias': 0.06}),
        'trouser': '#2A2C32',
        'boot': ('#141316', {'glossy': True}),
        'patch': '#2A2628',
        'hat': ['#060608', '#0E0E12', '#18181D', '#24242A', '#34343C', '#4A4A54'],
        'band': ['#020203', '#060608', '#0C0C10', '#121216', '#1A1A20', '#24242C'],
        'glove': '#3E302A',
        'case': ('#3E2B22', {'glossy': True}),
        'clasp': BRASS,
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#2A2834',
        'skin': SKIN_C3[scene],
        'hair': GREY_HAIR,
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#16161A',
    })
    lg = HD.base_legend()
    spec = Spec(id='kessler', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=23.0, torso=14.0, neck=1.8, thigh=10.6, shin=10.6, leg_r=(1.6, 1.45), arm_r=(1.45, 1.25),
                coat=Coat(mat='coat', hem=-13.0, back=3.8, front=3.8, flare=0.9, chest=0.6, collar=1.6,
                          width_f=5.4, waist_f=4.0, hem_f=4.6, R=2.2, cyl=0.7, folds=0.8),
                heads=heads(lg, KESSLER_SIDE, KESSLER_FRONT, side_talk={(8, 8): 'M'}, front_talk={(5, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('glove', kind='glove'), lean=-1.5,
                style=dict(stride=6.0, swing=10.0, bob=1, walk_lean=0.0, lift=2.6, hem=0.5, idle_feet=(1.0, -1.0),
                           hold_n=(2.0, 4.0), arm_f_idle=(-3.0, 10.0), gesture='straighten',
                           front_r=(3.0, 0.0, 4.0), talk_front_arm='l', front_abd=4.0,
                           talk_f=[(-3.0, 10.0), (0.0, 40.0), (4.0, 90.0), (8.0, 112.0), (5.0, 96.0), (1.0, 60.0),
                                   (3.0, 80.0), (-2.0, 20.0)],
                           talk_hand_f=TALK_HANDS,
                           talk_head=[(0, 0), (0, 0), (0, 0), (0, -1), (0, 0), (0, 0), (0, 0), (0, 0)]))
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
    put_hand(fr, spec, 'fist', hx, hy - 0.2, name='hand_n2')


def kessler_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J)
    pts = [body(-1.3, T + 0.6), body(1.3, T + 0.6), body(0.4, T - 3.0), body(-0.4, T - 3.0)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=0.8, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(0.0, T - 0.2), body(0.0, T - 3.0), 0.45, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, 0.6, -13, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, 1.6, (T - 4.5, T - 8.0, 0.5), tone=1)
    lapels_front(fr, spec, J, depth=3.6, width=2.4)


def kessler_case_front(fr, J, P, spec):
    x, y = J['wr_r']
    case = bm(['.nn.', 'nobn', 'abcd', 'abcd', 'abcd', 'oaab'], CASE_LG, anchor=(1, 0))
    put_bitmap(fr, case, spec.names, x, y + 1.0, name='briefcase')
    put_hand(fr, spec, 'front_r', x, y + 0.6, name='hand_r2')


# =================================================================================== TYPIST
# Frau Brunner: short set brown hair in soft curls, a pencil behind the ear, round friendly face; 40s
TYPIST_SIDE = [
    '. . . . k l l h . . .',
    '. . . k l h K h K . .',
    '. . k l K h j K h K .',
    '. . k h l K h s S L .',
    '. k l K l r S S B L .',
    '. k h p P r S S e L .',
    '. . k l h s S S L L H',
    '. . . k l r s S S m .',
    '. . . . . . r s S . .',
    '. . . . . . s @ . . .',
]
TYPIST_FRONT = [
    '. . . k l h h k . . .',
    '. . k l K h K h k . .',
    '. k l K j K h K h k .',
    '. k h K s S S s K k .',
    '. k l r B S S B r p .',
    '. k l L e S S e s P .',
    '. . l L S S n s s . .',
    '. . . s S m m S r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def typist():
    """Frau Brunner (40s, Swiss), commission typist: oatmeal cardigan over a white blouse, dark skirt,
    black sleeve protectors, short set hair with a pencil behind the ear, steno pad in hand."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': ('#857356', {'texture': 'knit'}),
        'skirt': '#3C383C',
        'trouser': '#6A5650',
        'boot': ('#2A2022', {'glossy': True}),
        'patch': '#3A3436',
        'sleeve': '#1E1E22',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'skin': SKIN_C3[scene],
        'hair': ['#140E0C', '#2A1C16', '#3E2A20', '#563C2C', '#6E503A', '#88664A'],
        'eye': EYE_B,
        'pencil': '#C09038',
        'paper': PAPER,
        'wire': CHROME,
        'button': '#4A3C2C',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    lg.update({'p': ('pencil', 4, 'f'), 'P': ('pencil', 2, 'f')})
    spec = Spec(id='typist', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=20.4, torso=12.2, neck=1.5, thigh=9.4, shin=9.3, uarm=6.9, farm=5.9,
                leg_r=(1.4, 1.2), arm_r=(1.45, 1.25), hip_f=1.7,
                coat=Coat(mat='coat', hem=-2.0, back=3.8, front=3.9, flare=0.3, chest=1.0, collar=0.4,
                          width_f=5.0, waist_f=4.2, hem_f=4.4, R=2.2, cyl=0.65),
                skirt=Skirt(mat='skirt', top=3.0, hem=-11.0, back=3.6, front=3.7, flare=0.7, hem_f=4.3,
                            waist_f=3.8, folds=0.5),
                heads=heads(lg, TYPIST_SIDE, TYPIST_FRONT, side_talk={(9, 7): 'M'}, front_talk={(5, 7): 'M'}),
                boots=ladies_boots('boot'), hands=make_hands('skin'), lean=0.5,
                style=dict(stride=4.0, swing=16.0, bob=1, walk_lean=1.5, lift=2.4, idle_feet=(1.0, -1.0),
                           hold_n=(8.0, 64.0), arm_f_idle=(-3.0, 12.0), gesture='read_pad',
                           front_l=(2.0, 0.6, -84.0), talk_front_arm='r', front_abd=5.0,
                           talk_n=[(8.0, 64.0), (10.0, 76.0), (14.0, 92.0), (12.0, 104.0), (12.0, 94.0), (9.0, 72.0),
                                   (11.0, 84.0), (8.0, 66.0)],
                           talk_hand_n=['fist'] * 8, talk_head=[(0, 0), (0, 0), (0, 1), (0, 1), (0, 0), (0, 0),
                                                                (0, 0), (0, 0)]))
    spec.hooks = {'side': [('back1', typist_sleeve_far), ('coat', typist_coat_side), ('front', typist_pad_side)],
                  'front': [('coat', typist_coat_front), ('arms', typist_pad_front)]}
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
    put_hand(fr, spec, 'fist', x + 0.2, y - 0.3, name='hand_n2')


def typist_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(-1.6, T + 0.6), body(1.6, T + 0.6), body(0.6, T - 2.2), body(-0.6, T - 2.2)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=0.8, cyl=0.2, cast=False, name='blouse')
    column_line(fr, spec, J, 0.4, -2, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, 1.2, (T - 3.5, T - 6.0, T - 8.5), tone=1)
    quilt_lines(fr, spec, J, 'coat', step=2, start=0, vmin=-2, vmax=1.0, light=spec.light_front.key)


def typist_pad_front(fr, J, P, spec):
    # steno pad held in front of the waist by her right hand (screen left), black sleeve protectors
    for s in ('l', 'r'):
        put_line(fr, spec, J['el_' + s], J['wr_' + s], 1.15, 'sleeve', name='protector_' + s)
    x, y = J['wr_l']
    pad = bm(['wWw', 'qPp', 'Plp', 'PPo'], PAD_LG, anchor=(1, 0))
    put_bitmap(fr, pad, spec.names, x + 0.4, y + 0.4, name='pad')
    put_hand(fr, spec, 'front_l', x, y + 0.2, name='hand_l2')


# =================================================================================== JOURNALIST
# Nils Ekdahl: fair tousled hair (bareheaded), long Nordic face, strong straight nose; 40s
JOURNALIST_SIDE = [
    '. . . . h K j K . . .',
    '. . . h K j J j K . .',
    '. . h K j K J j J K .',
    '. . h K h K j s S L .',
    '. . h K h r S S B L .',
    '. . h h K r S S e L .',
    '. . . h l s S S L L H',
    '. . . . . r s S S L .',
    '. . . . . r s S m . .',
    '. . . . . . r s S . .',
    '. . . . . . s @ . . .',
]
JOURNALIST_FRONT = [
    '. . . h K j K h . . .',
    '. . h K j J j K h . .',
    '. h K j J K J j K h .',
    '. h K j s S S s K h .',
    '. . h r B S S B r . .',
    '. . h L e S S e s . .',
    '. . . L S S n s s . .',
    '. . . s S S S s r . .',
    '. . . . s S m s . . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def journalist():
    """Nils Ekdahl (40s), Swedish newspaper correspondent: brown tweed overcoat, knitted scarf, fair
    tousled hair (bareheaded), camera on a strap at the chest, notebook and pencil in hand."""
    scene = 'palais'
    mats, names = materials(scene, {
        'coat': ('#5C5040', {'texture': 'tweed'}),
        'trouser': '#3A3A3E',
        'boot': ('#3A2A22', {'glossy': True}),
        'patch': '#4A3A30',
        'scarf': ('#2E4A62', {'texture': 'knit'}),
        'skin': SKIN_C3[scene],
        'hair': ['#3A2E1C', '#5E4C2E', '#82693E', '#A08A5A', '#BCA674', '#D6C494'],
        'eye': EYE_B,
        'camera': ['#08080A', '#121216', '#1C1C22', '#2A2A32', '#3E3E48', '#5A5A66'],
        'chrome': CHROME,
        'strap': '#2A2220',
        'paper': PAPER,
        'button': '#2E2620',
        'glass': GLASS,
    })
    lg = HD.base_legend()
    spec = Spec(id='journalist', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C3[scene],
                hip_h=22.2, torso=13.6, neck=1.8,
                coat=Coat(mat='coat', hem=-9.5, back=4.3, front=4.2, flare=1.0, chest=0.4, collar=1.6,
                          width_f=5.8, waist_f=4.6, hem_f=5.0, R=2.3, cyl=0.65, folds=0.6),
                heads=heads(lg, JOURNALIST_SIDE, JOURNALIST_FRONT, side_talk={(8, 8): 'M'},
                            front_talk={(6, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=2.5, stoop=4.0,
                style=dict(stride=5.6, swing=20.0, bob=1, walk_lean=3.0, lift=2.8, hem=0.8, idle_feet=(1.5, -1.5),
                           hold_n=(10.0, 70.0), arm_f_idle=(-6.0, 16.0), gesture='jot',
                           front_l=(3.0, 0.6, -80.0), talk_front_arm='r', front_abd=6.0,
                           talk_n=[(10.0, 70.0), (14.0, 80.0), (20.0, 94.0), (22.0, 96.0), (18.0, 88.0), (12.0, 74.0),
                                   (16.0, 84.0), (10.0, 72.0)],
                           talk_hand_n=['fist'] * 8,
                           talk_f=[(-6.0, 16.0), (-4.0, 30.0), (2.0, 60.0), (4.0, 76.0), (2.0, 64.0), (-3.0, 34.0),
                                   (0.0, 50.0), (-6.0, 18.0)],
                           talk_hand_f=TALK_HANDS, talk_head=TALK_NOD))
    spec.hooks = {'side': [('coat', journalist_coat_side), ('coat', journalist_camera_side),
                           ('front', journalist_notebook_side)],
                  'front': [('coat', journalist_coat_front), ('arms', journalist_notebook_front)]}
    return spec


CAM_LG = {'o': ('camera', 0), 'a': ('camera', 1), 'b': ('camera', 2), 'c': ('camera', 3), 'd': ('camera', 4),
          'x': ('chrome', 3), 'X': ('chrome', 5)}
SCARF_BLUE = {'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4), 'e': ('scarf', 5),
              'o': ('scarf', 0)}
NOTE_LG = {'p': ('paper', 3), 'P': ('paper', 4), 'q': ('paper', 5), 'l': ('paper', 2), 'o': ('paper', 1)}


def journalist_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -9, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 4.0, T - 7.5, 0.0), tone=1)
    flap(fr, spec, J, spec.coat.front - 3.6, spec.coat.front - 2.0, -1.0, 'coat')
    x, y = body(0.4, T + 1.2)
    sw = lag_dx(P, 1.0) if walking(P) else 0
    sc = bm(['.bcdd', 'bccdd', 'obbcd', '..bcd', '..bc.', '..ab.', '..b..'], SCARF_BLUE, anchor=(2, 0))
    put_bitmap(fr, sc, spec.names, x + sw, y, name='scarf')


def journalist_camera_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(0.4, T + 0.6), body(spec.coat.front + 0.4, T - 4.0), 0.45, 'strap', tone=1,
             name='cam_strap')
    sway = 1 if walking(P) and P.get('phase', 0) in (2, 3, 6, 7) else 0
    x, y = body(spec.coat.front + 0.6, T - 4.2)
    cam = bm(['xX..', 'abdc', 'abo.'], CAM_LG, anchor=(1, 0))
    put_bitmap(fr, cam, spec.names, x + sway, y, name='camera')


def journalist_notebook_side(fr, J, P, spec):
    x, y = J['wr_n']
    nb = bm(['oPq', 'lPP', 'lPp', 'olp'], NOTE_LG, anchor=(1, 1))
    put_bitmap(fr, nb, spec.names, x + 0.8, y - 0.4, name='notebook')
    put_hand(fr, spec, 'fist', x + 0.2, y - 0.2, name='hand_n2')


def journalist_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, 0.5, -9, T - 4, 'coat', -0.8)
    buttons(fr, spec, J, 1.4, (T - 5.0, T - 8.0, 0.0), tone=1)
    lapels_front(fr, spec, J, depth=4.0, width=2.6)
    flap(fr, spec, J, -4.0, -2.2, -1.0, 'coat')
    flap(fr, spec, J, 2.2, 4.0, -1.0, 'coat')
    x, y = body(0.0, T + 1.4)
    sc = bm(['.bccdb.', 'obccddb', '..bcd..', '..bcd..', '..bc...', '..ab...'], SCARF_BLUE, anchor=(3, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')
    put_line(fr, spec, body(-3.4, T + 0.4), body(1.6, T - 4.6), 0.45, 'strap', tone=1, name='cam_strap')
    put_line(fr, spec, body(3.4, T + 0.4), body(2.6, T - 4.6), 0.45, 'strap', tone=1, name='cam_strap2')
    cam = bm(['xxXx', 'abdc', 'abbc'], CAM_LG, anchor=(1, 0))
    put_bitmap(fr, cam, spec.names, *body(2.2, T - 4.6), name='camera')


def journalist_notebook_front(fr, J, P, spec):
    x, y = J['wr_l']
    nb = bm(['oPq', 'lPP', 'olp'], NOTE_LG, anchor=(1, 0))
    put_bitmap(fr, nb, spec.names, x + 0.4, y + 0.2, name='notebook')
    put_hand(fr, spec, 'front_l', x, y + 0.2, name='hand_l2')


# ----------------------------------------------------------------------------------- tables
CAST_C3 = {
    'elena': elena, 'border_officer': border_officer, 'conductor': conductor, 'voronova': voronova,
    'kessler': kessler, 'typist': typist, 'journalist': journalist,
}
# Row order: the rows of the first Chapter-3 contract (C3_DESIGN section 5) first, in their old order, then
# what the round-2 cast has (walk, front idle, blink / glance / gesture variants, front talk), appended.
_EXTRA = ['blink_side', 'look_side', 'gesture_side', 'blink_front', 'talk_front']
ROWS_C3 = {
    'elena': ['idle_side', 'walk_side', 'idle_front', 'talk_side'] + _EXTRA,
    'border_officer': ['idle_side', 'talk_side', 'idle_front', 'walk_side'] + _EXTRA,
    'conductor': ['idle_side', 'walk_side', 'talk_side', 'idle_front'] + _EXTRA,
    'voronova': ['idle_side', 'talk_side', 'idle_front', 'walk_side'] + _EXTRA,
    'kessler': ['idle_side', 'talk_side', 'idle_front', 'walk_side'] + _EXTRA,
    'typist': ['idle_side', 'talk_side', 'idle_front', 'walk_side'] + _EXTRA,
    'journalist': ['idle_side', 'walk_side', 'talk_side', 'idle_front'] + _EXTRA,
}
# figure height (px, idle_side frame 0, incl. headgear) the validator expects
EXPECT_H_C3 = {
    'elena': (41, 45), 'border_officer': (44, 49), 'conductor': (43, 48), 'voronova': (41, 46),
    'kessler': (45, 50), 'typist': (40, 45), 'journalist': (44, 48),
}
