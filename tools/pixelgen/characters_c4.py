"""characters_c4.py -- the Chapter-4 part-1 cast („Stimmen unter Beton“) on the round-2 rig, with living portraits.

    py -3 -P tools/pixelgen/characters_c4.py                  (all three: sheets, previews, checks)
    py -3 -P tools/pixelgen/characters_c4.py lev marta        (selected ids)
    py -3 -P tools/pixelgen/characters_c4.py --portraits      (additionally the living portraits through
                                                              chargen_portrait2; specs: PORTRAITS_C4 below)
    py -3 -P tools/pixelgen/characters_c4.py --check          (validate only)
    py -3 -P tools/pixelgen/characters_c4.py --heads          (review: the heads only, 8x, next to the cast)
    py -3 -P tools/pixelgen/characters_c4.py --out=DIR        (review run: write everything below DIR)

The cast (documentation/C4_DESIGN.md section 5; costume notes: documentation/asset_manifest_parts/c4_cast_audio.md):
  lev        Lev Sokolov (54), archive clerk of the Karsk freight office -- thin, a little stooped, bareheaded;
             thinning grey hair, grey stubble, round steel glasses taped at the hinge, a pencil behind the ear;
             grey quilted vest over a darned brown cardigan, black sleeve protectors, felt boots with galoshes; a
             glass of tea in its nickel holder in the far hand (the samovar of the cellar)
  marta      Marta Vogel (34), tram driver of line 74 -- dark-blue driver's coat with brass buttons and a belt,
             a uniform cap with a small numbered „74“ plate (no insignia), knitted grey scarf, fingerless grey
             gloves, the leather money satchel on a strap, lace-up boots; short dark-blond hair, red cheeks
  registrar  Registrator Fengler (about 50), Nebenstelle Süd -- a light grey dust coat over a dark suit, white
             collar and tie, black sleeve protectors, rimless glasses, a precise side parting with grey temples,
             a rubber stamp in his hand, a small plain round lapel pin (no insignia)

Everything goes through the EXISTING pipeline: characters.py (ANIMS, ROWS, build_sheet, previews) and
characters_check.py are imported and their tables extended IN MEMORY (nothing is patched on disk); the heads are
hand-drawn ASCII maps in the chargen_heads format, hands from chargen_body.make_hands (Marta's fingerless gloves
are drawn here), animation keys from chargen_anim (two gestures are added in memory: Fengler's stamp tap and
Marta's look along the line).  The portraits are chargen_portrait2 specs registered in memory in
chargen_portrait2_cast.CAST and written by chargen_portrait2.build_char (round-2 contract: portrait.png,
portrait_anim.png, portrait.json).  Deterministic: no randomness, no network, no image inputs.
Outputs: assets/characters/{lev,marta,registrar}/sheet.png, sheet_n.png, sheet.json, portrait.png,
portrait_anim.png, portrait.json; review images assets/characters/_preview/c4_* (git-ignored, .gdignore).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import characters as CH                   # noqa: E402  existing runner (ANIMS, ROWS, build_sheet, previews)
import characters_check as CHK            # noqa: E402  existing validator
import chargen_anim as A                  # noqa: E402
import chargen_core as C                  # noqa: E402
import chargen_heads as HD                # noqa: E402
from chargen_body import CELL_H, CELL_W, Coat, Spec, M, make_hands   # noqa: E402
from chargen_core import Bitmap, put_bitmap                         # noqa: E402
from chargen_cast import (EYE_B, EYE_K, GLASS, SKIN, belt_front, belt_side, bm, boot_bitmaps, buttons,  # noqa: E402
                          column_line, flap, lag_dx, lapels_front, materials, put_line, put_poly, quilt_lines,
                          side_light, walking, _puff)
from chargen_cast_c3 import (BRASS, CHROME, TALK_HANDS, TALK_NOD, VISOR, calm_front_hem,  # noqa: E402
                             ladies_boots, put_hand)

C4_IDS = ['lev', 'marta', 'registrar']
REFERENCE = ['alexei', 'konrad', 'emil', 'clerk', 'guard', 'conductor', 'kessler', 'typist', 'berlin_mother',
             'berlin_father', 'porter', 'librarian', 'worker_b', 'border_officer']

# ----------------------------------------------------------------------------------- scenes
# OKLCh hue / chroma of the shadow and light tints (data/chapters/c4.json palettes): the Karsk cellar is lit by a
# kerosene lamp (amber light, a cold navy-teal shadow from the barred window), the tram loop by the Berlin dawn
# (blue-violet shadow, pale gold light), the annex by fluorescent tubes (green-teal shadow, greenish-white light).
C.SCENE_TINT.setdefault('c4_cellar', dict(shadow_h=228.0, shadow_c=0.048, light_h=68.0, light_c=0.072))
C.SCENE_TINT.setdefault('c4_dawn', dict(shadow_h=268.0, shadow_c=0.050, light_h=84.0, light_c=0.050))
C.SCENE_TINT.setdefault('c4_annex', dict(shadow_h=196.0, shadow_c=0.040, light_h=138.0, light_c=0.034))
RIM_C4 = {
    'c4_cellar': np.array([150, 166, 184, 255], np.uint8),   # cold window light from behind
    'c4_dawn': np.array([172, 180, 214, 255], np.uint8),     # blue dawn sky
    'c4_annex': np.array([168, 196, 178, 255], np.uint8),    # fluorescent tube light
}

# ----------------------------------------------------------------------------------- gestures (in memory)
# Fengler: the rubber stamp tapped twice against the counter edge / his palm (bored, procedural)
A.GESTURES.setdefault('tap_stamp', [
    {}, {'arm_n': (14, 62)}, {'arm_n': (18, 78), 'head': (0, 1)}, {'arm_n': (12, 52), 'head': (0, 1)},
    {'arm_n': (18, 78), 'head': (0, 1)}, {'arm_n': (12, 52), 'face': 'blink'}, {'arm_n': (10, 40)}, {},
])
# Marta: a look down the line -- weight back, chin up, the near hand shading the eyes against the dawn
A.GESTURES.setdefault('look_down_line', [
    {}, {'dx': -0.4, 'lean': -1.0}, {'dx': -0.8, 'lean': -1.8, 'arm_n': (30, 128), 'head': (0, -1)},
    {'dx': -0.8, 'lean': -1.8, 'arm_n': (32, 136), 'head': (0, -1)},
    {'dx': -0.8, 'lean': -1.8, 'arm_n': (32, 136), 'head': (0, -1), 'face': 'blink'},
    {'dx': -0.6, 'lean': -1.2, 'arm_n': (24, 100)}, {'dx': -0.2}, {},
])

# ----------------------------------------------------------------------------------- shared materials
PROTECTOR = ['#08080A', '#101014', '#18181E', '#222228', '#2E2E36', '#40404A']   # black sleeve protectors
TAPE = ['#4A463A', '#7A7464', '#A8A08A', '#C8C0A6', '#DED6BE', '#EEE8D4']        # yellowed sticking plaster
TEA = ['#1E0A04', '#3E1606', '#6A2A0C', '#92421A', '#B8642C', '#D88C48']
GLASS_W = ['#4A5458', '#6E7C80', '#94A4A8', '#B8C8CA', '#D4E0E0', '#EEF6F6']        # tea glass catching light
BREATH = ['#6E7C7A', '#8E9C98', '#AEBAB4', '#C4CEC8', '#DCE2DC', '#EEF2EE']
PAPER_W = ['#4A4A44', '#7E7E74', '#A8A89A', '#C8C8B8', '#DEDED0', '#F0F0E6']


# =================================================================================== LEV
# bareheaded: thinning grey hair (receded from the forehead), round steel glasses with sticking plaster on the near
# hinge (W), a pencil behind the ear (p / P), grey stubble on a long thin face, sunken cheeks
LEV_SIDE = [
    '. . . l h K K j . . .',
    '. . l h K K j j s . .',
    '. l h h K K j s S L .',
    '. l h p P r S S b L .',
    '. l h h r W g e G L .',
    '. l h h r s S S S L H',
    '. . l h h s S S r S .',
    '. . . l h r s S m . .',
    '. . . . . r s r S . .',
    '. . . . . . s @ . . .',
]
LEV_FRONT = [
    '. . . . h K K j . . .',
    '. . . l K K K j j . .',
    '. . l h s S S S j h .',
    '. . l s S S S S s h .',
    '. p h b S S S b s h .',
    '. l W g e g g e G h .',
    '. r h L S S n s s r .',
    '. . h s r m m r s . .',
    '. . . r s S S s r . .',
    '. . . . r s s r . . .',
    '. . . . . s @ . . . .',
]


def lev():
    """Lev Sokolov (54): thin, a little stooped, the near hand free (glasses, gestures), a glass of tea in its
    nickel holder held at the chest in the far hand; quilted vest over the darned cardigan."""
    scene = 'c4_cellar'
    mats, names = materials(scene, {
        'coat': '#686A64',                       # grey quilted vest (quilting: lev_vest_side)
        'cardigan': ('#6A5644', {'texture': 'knit'}),
        'darn': ('#7E6A50', {'texture': 'knit'}),
        'trouser': '#3A3634',
        'boot': ('#5A564E', {'texture': 'felt'}),
        'galosh': ('#141418', {'glossy': True}),
        'patch': '#6A685E',
        'protector': PROTECTOR,
        'skin': SKIN['old'],
        'hair': ['#1C1C1E', '#3A3A3C', '#58595B', '#78797A', '#98999A', '#B6B6B2'],   # iron grey
        'eye': EYE_K,
        'glass': GLASS,
        'tape': TAPE,
        'pencil': '#B0502C',
        'tea': TEA,
        'tglass': GLASS_W,
        'nickel': CHROME,
        'button': '#26262A',
        'hat': '#3A3634',
        'band': '#2A2A30',
    })
    lg = HD.base_legend()
    lg.update({'W': ('tape', 4, 'f'), 'p': ('pencil', 4, 'f'), 'P': ('pencil', 2, 'f')})
    spec = Spec(id='lev', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4[scene],
                hip_h=21.4, torso=12.8, neck=1.4, thigh=10.0, shin=9.8, uarm=7.2, farm=6.2,
                leg_r=(1.35, 1.2), arm_r=(1.4, 1.2), hip_f=1.7,
                coat=Coat(mat='coat', hem=-1.6, back=3.6, front=3.5, flare=0.2, chest=0.2, collar=0.5,
                          width_f=4.9, waist_f=4.2, hem_f=4.3, R=2.0, cyl=0.65, hunch=0.7),
                sleeve='cardigan', inner='cardigan', inner_w=1.5,
                heads=HD.head_views(lg, LEV_SIDE, LEV_FRONT, side_talk={(8, 7): 'M'}, front_talk={(5, 7): 'M'}),
                boots=boot_bitmaps('boot', sole='galosh', style='valenki'), hands=make_hands('skin'),
                lean=3.0, stoop=9.0, head_off=(0.8, -0.3),
                style=dict(stride=4.2, swing=10.0, bob=1, walk_lean=2.5, lift=2.2, idle_feet=(1.0, -1.5),
                           hold_f=(6.0, 118.0), arm_f_idle=(6.0, 118.0), arm_n_idle=(3.0, 14.0),
                           gesture='push_glasses', front_l=(3.0, 0.3, -96.0), talk_front_arm='r', front_abd=4.0,
                           talk_n=[(4.0, 18.0), (8.0, 44.0), (12.0, 66.0), (14.0, 74.0), (12.0, 64.0), (8.0, 46.0),
                                   (10.0, 56.0), (5.0, 26.0)],
                           talk_hand_n=TALK_HANDS,
                           talk_head=[(0, 0), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('back1', lev_protector_far), ('legs', lev_cardigan_hem_side), ('coat', lev_vest_side),
                           ('coat', lev_tea_side), ('front', lev_arm_near_side)],
                  'front': [('legs', lev_cardigan_hem_front), ('coat', lev_vest_front), ('arms', lev_tea_front)]}
    return spec


TEA_LG = {'w': ('tglass', 4, 'f'), 'W': ('tglass', 5, 'f'), 't': ('tea', 3, 'f'), 'T': ('tea', 4, 'f'),
          'n': ('nickel', 3, 'f'), 'N': ('nickel', 4, 'f'), 'o': ('nickel', 1, 'f'), 'h': ('nickel', 2, 'f')}


def lev_protector_far(fr, J, P, spec):
    put_line(fr, spec, J['el_f'], J['wr_f'], 1.15, 'protector', name='protector_f', bias=-1.0)


def lev_cardigan_hem_side(fr, J, P, spec):
    """The darned cardigan hangs a hand's breadth below the short vest."""
    body = J['body']
    c = spec.coat
    pts = [body(-c.back + 0.5, 1.0), body(c.front - 0.1, 1.0), body(c.front + 0.1, -3.9), body(-c.back + 0.4, -3.9)]
    put_poly(fr, spec, pts, 'cardigan', R=1.4, cyl=0.6, name='cardigan_hem')


def lev_vest_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    quilt_lines(fr, spec, J, 'coat', step=2, start=0, vmin=-1.5, vmax=T - 1.0)
    column_line(fr, spec, J, c.front - 0.9, -1.5, T - 1.5, 'coat', -0.8)
    buttons(fr, spec, J, c.front - 0.9, (T - 3.5, T - 7.0, 0.0), tone=1)
    # the cardigan's V-neck and the collarless shirt at the throat
    body = J['body']
    put_poly(fr, spec, [body(c.front - 1.6, T + 0.4), body(c.front + 0.1, T - 0.6), body(c.front - 0.4, T - 2.6)],
             'cardigan', R=0.8, cyl=0.3, cast=False, name='cardigan_v')


def lev_tea_side(fr, J, P, spec):
    """The tea glass in its nickel holder, held at the chest by the far hand (drawn over the vest)."""
    if P.get('arm_f') != spec.style.get('hold_f'):
        return
    x, y = J['wr_f']
    g = bm(['wWw.', 'tTt.', 'nNnh', 'nNnh', '.oo.'], TEA_LG, anchor=(1, 3))
    put_bitmap(fr, g, spec.names, x + 1.2, y - 0.6, name='tea')
    put_hand(fr, spec, 'fist', x - 0.2, y - 0.4, name='hand_f2')


def lev_arm_near_side(fr, J, P, spec):
    """Black sleeve protector on the near forearm; a darned patch at the elbow of the cardigan sleeve."""
    put_line(fr, spec, J['el_n'], J['wr_n'], 1.2, 'protector', name='protector')
    ex, ey = J['el_n']
    sx, sy = J['sh_n']
    fr.recolor(ex + (sx - ex) * 0.22 - 0.2, ey + (sy - ey) * 0.22, M(spec, 'darn'), 3)
    fr.recolor(ex + (sx - ex) * 0.22 + 0.8, ey + (sy - ey) * 0.22, M(spec, 'darn'), 2)


def lev_cardigan_hem_front(fr, J, P, spec):
    body = J['body']
    c = spec.coat
    pts = [body(-c.hem_f + 0.2, 1.0), body(c.hem_f - 0.2, 1.0), body(c.hem_f, -3.9), body(-c.hem_f, -3.9)]
    put_poly(fr, spec, pts, 'cardigan', R=1.4, cyl=0.6, name='cardigan_hem')


def lev_vest_front(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=2, start=0, vmin=-1.5, vmax=T - 1.0, light=spec.light_front.key)
    column_line(fr, spec, J, 1.5, -1.5, T - 2.0, 'coat', -0.8)
    column_line(fr, spec, J, -1.5, -1.5, T - 2.0, 'coat', -0.8)
    buttons(fr, spec, J, 1.6, (T - 4.0, T - 7.5, 0.5), tone=1)


def lev_tea_front(fr, J, P, spec):
    for s in ('l', 'r'):
        put_line(fr, spec, J['el_' + s], J['wr_' + s], 1.1, 'protector', name='protector_' + s)
    x, y = J['wr_l']
    g = bm(['wWw', 'tTt', 'nNn', 'nNn', 'ooo'], TEA_LG, anchor=(1, 3))
    put_bitmap(fr, g, spec.names, x + 0.2, y - 0.4, name='tea')
    put_hand(fr, spec, 'front_l', x + 0.6, y - 0.2, name='hand_l2')


# =================================================================================== MARTA
# uniform cap (dark blue, black visor, a small brass number plate „74“ = Z), short dark-blond hair at the nape and
# temples, round face with red cheeks (c / C), quick eyes
MARTA_SIDE = [
    '. . . . 1 2 3 3 . . . .',
    '. . . 1 2 3 3 4 4 . . .',
    '. . . 1 2 2 3 Z 4 4 . .',
    '. . . 0 u v v V V x x .',
    '. . j k r r s B S L . .',
    '. . j h h S S e S L . .',
    '. . . j h s c S L L H .',
    '. . . . h r C S m S . .',
    '. . . . . r s S S . . .',
    '. . . . . . s @ . . . .',
]
MARTA_FRONT = [
    '. . 1 2 3 3 3 3 1 . .',
    '. 1 2 3 3 Z 4 3 3 1 .',
    '. 1 2 3 3 3 3 3 2 1 .',
    '. 0 u v V V V v u 0 .',
    '. . j r B S B r j . .',
    '. . j L e S e s j . .',
    '. . h C S S n c h . .',
    '. . . s S m m S r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def fingerless_hands(glove='glove', skin='skin'):
    """Knitted fingerless gloves: palm and wrist in wool, the finger row in skin (chargen_body.make_hands keys)."""
    lg = {'a': (glove, 1), 'b': (glove, 2), 'c': (glove, 3), 'd': (glove, 4), 'f': (skin, 3), 'F': (skin, 4),
          'o': (glove, 0)}
    d = {
        'down': ['cd', 'cd', 'fF'],
        'diag': ['cdd', 'bcF', '.f.'],
        'fwd': ['cdF', 'bcf', '.f.'],
        'up': ['.F', 'cd', 'bc'],
        'open_fwd': ['.F.', 'cdF', 'bc.'],
        'open_up': ['.FF', 'cdd', 'bc.'],
        'fist': ['cd', 'bf'],
    }
    hands = {k: Bitmap(rows, lg, anchor=(0, 0)) for k, rows in d.items()}
    hands['front_l'] = Bitmap(['dc', 'cb', '.f'], lg, anchor=(1, 0))
    hands['front_r'] = Bitmap(['cc', 'bc', 'f.'], lg, anchor=(0, 0))
    hands['back_l'] = Bitmap(['cb', 'ba'], lg, anchor=(1, 0))
    hands['back_r'] = Bitmap(['bc', 'ab'], lg, anchor=(0, 0))
    hands['front'] = hands['front_r']
    hands['back'] = hands['back_r']
    hands['side'] = hands['down']
    return hands


def marta():
    """Marta Vogel (34), tram driver of line 74: sturdy and quick; the money satchel at the near hip, one end of the
    grey scarf over the coat front (it swings when she walks), breath in the cold."""
    scene = 'c4_dawn'
    mats, names = materials(scene, {
        'coat': ('#27324E', {'bias': 0.06}),
        'trouser': '#232A3C',
        'boot': ('#1C181A', {'glossy': True}),
        'patch': '#3A3436',
        'hat': '#222B44',
        'visor': VISOR,
        'brass': BRASS,
        'belt': ('#161B2A', {'glossy': True}),
        'scarf': ('#7A7C7A', {'texture': 'knit'}),
        'glove': ('#5C5C62', {'texture': 'knit'}),
        'bag': ('#5A3A24', {'glossy': True}),
        'strap': '#3E2A1C',
        'skin': SKIN['berlin'],
        'cheek': ['#3A1A20', '#6A2E34', '#9A4A48', '#C46A5E', '#DA8C78', '#ECB49C'],
        'hair': ['#1E1810', '#3C3020', '#5C4C30', '#7C6A44', '#9C885A', '#BCA878'],
        'eye': EYE_B,
        'breath': BREATH,
        'button': BRASS,
        'glass': GLASS,
    })
    lg = HD.base_legend(band='visor')
    lg.update({'Z': ('brass', 4, 'f'), 'c': ('cheek', 3, 'f'), 'C': ('cheek', 4, 'f')})
    spec = Spec(id='marta', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4[scene],
                hip_h=20.8, torso=12.4, neck=1.4, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.45, 1.25), arm_r=(1.55, 1.3), hip_f=1.6,
                coat=Coat(mat='coat', hem=-10.0, back=3.9, front=4.0, flare=1.0, chest=0.9, collar=1.3,
                          width_f=5.2, waist_f=4.0, hem_f=4.9, R=2.2, cyl=0.65, folds=0.5),
                heads=HD.head_views(lg, MARTA_SIDE, MARTA_FRONT, side_talk={(8, 7): 'M'}, front_talk={(5, 7): 'M'}),
                boots=ladies_boots('boot'), hands=fingerless_hands(), lean=0.0,
                style=dict(stride=5.2, swing=18.0, bob=1, walk_lean=2.0, lift=2.6, hem=0.7, idle_feet=(1.5, -1.5),
                           arm_n_idle=(4.0, 16.0), arm_f_idle=(-4.0, 14.0), gesture='blow_hands',
                           talk_front_arm='l', front_abd=6.0,
                           talk_n=[(6.0, 22.0), (12.0, 58.0), (18.0, 86.0), (22.0, 98.0), (18.0, 88.0), (10.0, 54.0),
                                   (16.0, 74.0), (6.0, 26.0)],
                           talk_hand_n=TALK_HANDS, talk_head=TALK_NOD))
    spec.hooks = {'side': [('coat', marta_coat_side), ('head', _puff)],
                  'front': [('coat', marta_coat_front), ('head', _puff)]}
    return spec


SCARF_GREY = {'o': ('scarf', 0), 'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4),
              'e': ('scarf', 5)}
SATCHEL_LG = {'o': ('bag', 0), 'a': ('bag', 1), 'b': ('bag', 2), 'c': ('bag', 3), 'd': ('bag', 4), 'm': ('brass', 4)}


def marta_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    belt_side(fr, spec, J, 2.4, 'belt', buckle='brass')
    column_line(fr, spec, J, c.front - 1.0, -10, T - 2, 'coat', -0.6)
    for v in (T - 3.0, T - 6.0, 0.0, -4.0):
        fr.recolor(*body(c.front - 1.0, v), M(spec, 'brass'), 4)
    flap(fr, spec, J, c.front - 3.2, c.front - 1.6, -2.4, 'coat')
    # money satchel on its strap: far shoulder -> near hip, the bag in front of the hip (bounces when walking)
    put_line(fr, spec, body(-1.2, T - 0.2), body(c.front - 0.6, -0.6), 0.5, 'strap', tone=2, name='strap')
    sw = 1 if walking(P) and P.get('phase', 0) in (1, 2, 5, 6) else 0
    x, y = body(c.front + 0.4, -0.4)
    bag = bm(['obbbm', 'abccd', 'abccd', 'oaabb'], SATCHEL_LG, anchor=(2, 0))
    put_bitmap(fr, bag, spec.names, x - sw, y, name='satchel')
    # the grey scarf wrapped high, one end down the coat front
    x, y = body(0.4, T + 1.4)
    sl = lag_dx(P, 1.0) if walking(P) else 0
    sc = bm(['.bccd', 'bccdd', 'obccd', '..bcd', '..bcd', '...bc'], SCARF_GREY, anchor=(2, 0))
    put_bitmap(fr, sc, spec.names, x + sl, y, name='scarf')


def marta_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.4)
    belt_front(fr, spec, J, 2.4, 'belt', buckle='brass')
    column_line(fr, spec, J, 0.3, -10, T - 2, 'coat', -0.8)
    for v in (T - 3.0, T - 6.0, 0.0, -4.0):
        for u in (-1.5, 1.6):
            fr.recolor(*body(u, v), M(spec, 'brass'), 4 if u > 0 else 3)
    lapels_front(fr, spec, J, depth=3.0, width=2.6)
    put_line(fr, spec, body(3.4, T + 0.2), body(-2.6, -0.4), 0.5, 'strap', tone=2, name='strap')
    bag = bm(['obbm', 'abcd', 'abcd', 'oaab'], SATCHEL_LG, anchor=(2, 0))
    put_bitmap(fr, bag, spec.names, *body(-3.4, -0.2), name='satchel')
    x, y = body(0.0, T + 1.6)
    sc = bm(['.bccdc.', 'obccddb', '..bcd..', '..bcd..', '..bc...', '..bc...'], SCARF_GREY, anchor=(3, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


# =================================================================================== REGISTRAR (Fengler)
# bareheaded: dark hair with grey temples (J), parted precisely, combed flat; rimless glasses (only the lens
# edges catch the light: G / E); a well-fed, smooth face
FENGLER_SIDE = [
    '. . . l h K K j . . .',
    '. . l h K K K j J . .',
    '. l h h h K K s S L .',
    '. l h h j j S S S L .',
    '. l h r j S S S b L .',
    '. l h r s S G e E L .',
    '. . l h r s S S L L H',
    '. . . r s S S S m S .',
    '. . . . r S S S L . .',
    '. . . . . r s S . . .',
    '. . . . . . s @ . . .',
]
FENGLER_FRONT = [
    '. . . l h K K h . . .',
    '. . l h K K J K h . .',
    '. . l h s S S S h h .',
    '. . j L S S S S s j .',
    '. . j b S S S b s j .',
    '. r s G e S S e G s r',
    '. . s L S S n s s . .',
    '. . . s S m m S r . .',
    '. . . s S S S S r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def registrar():
    """Registrator Fengler (about 50): upright, a little portly, the dust coat buttoned to the collar over a dark
    suit, the rubber stamp in the near hand; bored, polite, procedural."""
    scene = 'c4_annex'
    mats, names = materials(scene, {
        'coat': ('#8E918A', {'bias': 0.04}),
        'trouser': '#2E3036',
        'boot': ('#121214', {'glossy': True}),
        'patch': '#3A3436',
        'protector': PROTECTOR,
        'shirt': PAPER_W,
        'tie': '#2E2A36',
        'pin': ['#2A2A2E', '#4E5054', '#7A7E82', '#A8ACB0', '#CED2D4', '#ECEEEE'],
        'skin': SKIN['berlin'],
        'hair': ['#16120F', '#2C2622', '#443C36', '#6A645E', '#94908A', '#B8B4AE'],
        'eye': EYE_B,
        'glass': ['#5A6466', '#8A989A', '#A8B8BA', '#C6D4D6', '#DCE8EA', '#F2FAFA'],
        'stamp': '#6E4E30',
        'rubber': ['#0A0A0C', '#141416', '#202024', '#2E2E34', '#44444C', '#5E5E68'],
        'button': '#3A3C3A',
        'hat': '#2E3036',
        'band': '#2A2A30',
    })
    lg = HD.base_legend()
    spec = Spec(id='registrar', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4[scene],
                hip_h=21.8, torso=13.6, neck=1.3, thigh=10.2, shin=10.0, uarm=7.2, farm=6.3,
                leg_r=(1.6, 1.45), arm_r=(1.55, 1.35), hip_f=1.9,
                coat=Coat(mat='coat', hem=-10.0, back=3.9, front=4.5, flare=0.6, chest=0.5, collar=1.2,
                          width_f=5.6, waist_f=5.1, hem_f=5.3, R=2.2, cyl=0.65, folds=0.5),
                heads=HD.head_views(lg, FENGLER_SIDE, FENGLER_FRONT, side_talk={(8, 7): 'M'},
                                    front_talk={(5, 7): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'), lean=-0.5,
                style=dict(stride=4.6, swing=11.0, bob=1, walk_lean=0.5, lift=2.4, hem=0.4, idle_feet=(1.5, -1.5),
                           hold_n=(10.0, 62.0), arm_f_idle=(-4.0, 12.0), gesture='tap_stamp', work='stamp',
                           front_l=(4.0, 0.3, 30.0), talk_front_arm='r', front_abd=5.0,
                           talk_n=[(10.0, 62.0), (12.0, 74.0), (16.0, 90.0), (18.0, 100.0), (16.0, 92.0),
                                   (12.0, 72.0), (14.0, 82.0), (10.0, 64.0)],
                           talk_hand_n=['fist'] * 8,
                           talk_head=[(0, 0), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('back1', registrar_protector_far), ('coat', registrar_coat_side),
                           ('front', registrar_stamp_side)],
                  'front': [('coat', registrar_coat_front), ('arms', registrar_arms_front)]}
    return spec


STAMP_LG = {'k': ('stamp', 4), 'h': ('stamp', 3), 'H': ('stamp', 2), 'r': ('rubber', 2), 'R': ('rubber', 3),
            'o': ('rubber', 1)}


def registrar_protector_far(fr, J, P, spec):
    put_line(fr, spec, J['el_f'], J['wr_f'], 1.2, 'protector', name='protector_f', bias=-1.0)


def registrar_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    # white collar + dark tie at the throat, the dust coat buttoned up to it
    pts = [body(c.front - 1.6, T + 0.8), body(c.front - 0.1, T - 0.4), body(c.front - 0.2, T - 1.8),
           body(c.front - 1.3, T - 1.6)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='collar')
    put_line(fr, spec, body(c.front - 0.6, T - 0.6), body(c.front - 0.4, T - 2.2), 0.5, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, c.front - 1.0, -10, T - 2, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 1.0, (T - 3.5, T - 7.0, 0.0, -4.5), tone=1)
    flap(fr, spec, J, c.front - 3.4, c.front - 1.8, -3.0, 'coat')
    fr.recolor(*body(c.front - 1.9, T - 2.6), M(spec, 'pin'), 4)        # the plain round lapel pin


def registrar_stamp_side(fr, J, P, spec):
    put_line(fr, spec, J['el_n'], J['wr_n'], 1.25, 'protector', name='protector')
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    hx, hy = x + math.sin(ang) * 1.2, y + math.cos(ang) * 1.2
    st = bm(['.k.', '.h.', '.H.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 1))
    put_bitmap(fr, st, spec.names, hx + 0.6, hy, name='stamp')
    put_hand(fr, spec, 'fist', hx, hy - 0.2, name='hand_n2')


def registrar_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.4)
    pts = [body(-1.4, T + 0.6), body(1.4, T + 0.6), body(0.5, T - 2.0), body(-0.5, T - 2.0)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=0.8, cyl=0.2, cast=False, name='collar')
    put_line(fr, spec, body(0.0, T - 0.2), body(0.0, T - 2.4), 0.45, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, 0.6, -10, T - 2.5, 'coat', -0.8)
    buttons(fr, spec, J, 1.2, (T - 3.5, T - 7.0, 0.0, -4.5), tone=1)
    flap(fr, spec, J, -4.2, -2.4, -3.0, 'coat')
    flap(fr, spec, J, 2.4, 4.2, -3.0, 'coat')
    fr.recolor(*body(-2.2, T - 2.4), M(spec, 'pin'), 4)


def registrar_arms_front(fr, J, P, spec):
    for s in ('l', 'r'):
        put_line(fr, spec, J['el_' + s], J['wr_' + s], 1.2, 'protector', name='protector_' + s)
    x, y = J['wr_l']
    st = bm(['.k.', '.h.', 'rRr', 'ooo'], STAMP_LG, anchor=(1, 0))
    put_bitmap(fr, st, spec.names, x, y + 1.5, name='stamp')
    put_hand(fr, spec, 'front_l', x, y + 0.5, name='hand_l2')


# =================================================================================== PORTRAITS
# Busts on the round-2 pipeline (chargen_portrait2): signed-distance heads with individual planes, hand-designed
# eyes / brows / mouths, 4 expressions x 6 states.  Every face is its own (no shared head preset): Lev long and
# gaunt with hollow cheeks, deep tired eyes and grey stubble; Marta round, full-cheeked and quick-eyed; Fengler
# smooth and well fed with a soft double chin and hooded, bored eyes.  Backdrops per place (registered in memory
# in chargen_portrait2_paint.BG; no chargen_portrait2*.py file is changed).
def _portrait_mods():
    import chargen_portrait2 as PG
    import chargen_portrait2_cast as PC
    import chargen_portrait2_face as FC
    import chargen_portrait2_paint as PP
    import chargen_portrait2_sdf as S
    import chargen_portrait_c3 as PC3
    PP.BG.setdefault('c4_cellar', ('#140e0b', '#060405', '#4c3018', '#a8743c'))   # kerosene lamp in the cellar
    PP.BG.setdefault('c4_loop', ('#1a2236', '#080a12', '#46465e', '#a29cb8'))     # Berlin dawn at the tram loop
    PP.BG.setdefault('c4_annex', ('#0e1713', '#040706', '#2a3e32', '#86a68e'))    # fluorescent tubes underground
    return PG, PC, FC, PP, S, PC3


def _pt(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)


def pass_pencil(col='#b0502c', col_d='#6e2e18', tip='#2a1c14'):
    """Lev's pencil behind the near ear: a short red-brown stroke with a sharpened point toward the face."""
    def fn(spec, G, rgb, v, expr, row):
        lm = G['lmv']['ear_r']
        x0, y0 = int(np.floor(lm[0])) - 2, int(np.floor(lm[1])) - 6
        h, w = rgb.shape[:2]
        cols = [col_d, col, col, col, col_d, '#d8c0a0', tip]
        for k, c in enumerate(cols):
            x, y = x0 + k, y0 + (k + 1) // 3
            if 0 <= x < w and 0 <= y < h:
                rgb[y, x] = _pt(c)
        return rgb
    return fn


def pass_tape(lens_r=(4.2, 3.3), col='#d8ceb0', col_d='#8e8670'):
    """Sticking plaster wound round the near hinge of Lev's glasses (where the arm meets the rim)."""
    def fn(spec, G, rgb, v, expr, row):
        lm = G['lmv']['eye_r']
        cx, cy = lm[0] + 0.5, lm[1] + 0.4
        x1 = int(np.floor(cx - lens_r[0]))
        y1 = int(np.floor(cy - 1.0))
        h, w = rgb.shape[:2]
        for dx, dy, c in ((-2, 0, col_d), (-1, 0, col), (0, 0, col), (1, 0, col_d), (-2, 1, col_d), (-1, 1, col),
                          (0, 1, col_d)):
            x, y = x1 + dx, y1 + dy
            if 0 <= x < w and 0 <= y < h:
                rgb[y, x] = _pt(c)
        return rgb
    return fn


def pass_darns(mat='cardigan', spots=((-8.5, 15.0, 2.2), (6.5, 23.0, 1.8)), lit='#7e6a52', shade='#3c3024',
               frame='tf'):
    """Darned patches on Lev's cardigan: small woven squares in a slightly different wool (checker of two tones)."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3 = _portrait_mods()
        M = G['M']
        if mat not in M.names:
            return rgb
        m = G['d'].mat == M.names.index(mat)
        if not m.any():
            return rgb
        L = PC._local(G, frame, m)
        ys, xs = np.nonzero(m)
        lc, sc = _pt(lit), _pt(shade)
        for x, y, lx, ly in zip(xs, ys, L[:, 0], L[:, 1]):
            for (px, py, r) in spots:
                if abs(lx - px) < r and abs(ly - py) < r:
                    base = lc if v[y, x] > 0.3 else sc
                    rgb[y, x] = base if (x + y) % 2 == 0 else (base.astype(int) * 0.82).astype(np.uint8)
        return rgb
    return fn


def pass_parting(part_x=4.8, below=-6.0, width=0.55, mat='hair', frame='hf'):
    """Fengler's precise side parting: a one-tone-darker line in the hair along head-local x = part_x."""
    def fn(spec, G, tone, v):
        PG, PC, FC, PP, S, PC3 = _portrait_mods()
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = PC._local(G, frame, m)
        sel = (np.abs(L[:, 0] - part_x) < width) & (L[:, 1] < below)
        tone = tone.copy()
        ys, xs = np.nonzero(m)
        for x, y, s_ in zip(xs, ys, sel):
            if s_:
                tone[y, x] = max(0, tone[y, x] - 2)
        return tone
    return fn


def pass_temples(mat='hair', grey='#8a8680', grey_d='#4a4642', x_min=11.0, y_min=-7.0, y_max=2.0, frame='hf'):
    """Grey temples: hair pixels at the sides above the ears shift to grey (lit / shaded)."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3 = _portrait_mods()
        M = G['M']
        if mat not in M.names:
            return rgb
        m = G['d'].mat == M.names.index(mat)
        if not m.any():
            return rgb
        L = PC._local(G, frame, m)
        ys, xs = np.nonzero(m)
        sel = (np.abs(L[:, 0]) > x_min) & (L[:, 1] > y_min) & (L[:, 1] < y_max)
        g, gd = _pt(grey), _pt(grey_d)
        for x, y, s_ in zip(xs, ys, sel):
            if s_ and (x + y) % 2 == 0:
                c = g if v[y, x] > 0.32 else gd
                rgb[y, x] = ((rgb[y, x].astype(int) + c.astype(int)) // 2).astype(np.uint8)
        return rgb
    return fn


def lev_portrait():
    """Lev Sokolov (54): a long gaunt face, high cheekbones over hollow cheeks, a long straight nose, thin lips,
    a narrow chin; deep-set, tired eyes behind round steel glasses (plaster on the near hinge); thinning iron-grey
    hair receding at the temples, grey stubble; a pencil behind the ear; the quilted vest over the darned
    cardigan and a collarless shirt.  The cellar's kerosene lamp from the front right, cold window light behind."""
    PG, PC, FC, PP, S, PC3 = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0c0a10', '#1e1820', '#3a2a2c', '#603e3a', '#8c5e4e', '#b58466', '#d6a882', '#ecc8a2')
    rim = '#7d8c9c'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=-2))
    vest = ramp('#08090a', '#121416', '#1c1f21', '#282b2c', '#363938', '#464946', '#5a5d58')
    card = ramp('#0b0806', '#17110c', '#251b13', '#35271b', '#463424', '#5a432f', '#70553c')
    styles.update({
        'coat': MatStyle(vest, PC3.TH6, dither=0.04, rim=rim),
        'coat_lapel': MatStyle(vest, PC3.TH6, rim=rim),
        'cardigan': MatStyle(card, PC3.TH6, dither=0.03, rim=rim),
        'shirt': MatStyle(ramp('#0e0e10', '#222120', '#3a3733', '#565049', '#746c60', '#8e8576'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim=rim),
        'hair': MatStyle(ramp('#0c0c0e', '#1c1c20', '#2e2e32', '#424246', '#58585c', '#707072', '#8a8a88'),
                         [0.05, 0.12, 0.22, 0.36, 0.54, 0.74], rim='#98a4ae', wrap=0.3, lift=0.15),
        'button': MatStyle(ramp('#08080a', '#16161a', '#26262c', '#3a3a42'), [0.08, 0.25, 0.5], rim=rim),
    })
    head = dict(skull_r=(15.4, 17.0, 20.0), mid_h=(11.0, 7.8, 11.4), fore_h=(11.4, 9.6, 12.0),
                cheek_c=(10.0, 2.8, 9.6), cheek_r=(3.6, 2.4, 3.2), malar_r=(3.8, 3.2, 3.0),
                jaw_angle=(10.2, 16.4, -4.2), jaw_r=(2.2, 2.6, 2.6), low_r=(10.4, 11.8, 12.0),
                chin_c=(0.0, 22.8, 11.0), chin_h=(3.4, 3.4, 3.0), chin_rad=2.2, chin_pt=(3.0, 23.8, 9.4),
                nose_root=(0.0, -1.6, 15.6), nose_tip=(0.0, 10.0, 20.0), tip_r=2.0, nose_r=(1.3, 1.7), ala_x=2.2,
                ala_y=11.0, ala_r=(1.4, 1.3, 1.7), brow_r=(12.0, 2.6, 3.2), mouth_y=15.6, lip_up=(0.0, 14.9, 16.0),
                lip_up_r=(3.8, 0.85, 1.1), lip_lo=(0.0, 16.8, 15.4), lip_lo_r=(3.2, 0.95, 1.1), neck_r=(7.4, 8.8))
    lens = (4.2, 3.3)
    return dict(
        id='lev', city='karsk',
        look=dict(key=(0.60, -0.38, 0.70), rim=(-0.80, -0.34, -0.50), ambient=0.08, bg='c4_cellar',
                  glow=(0.78, 0.30)),
        head=head, zoom=1.12,
        head_pos=(54.0, 58.0, 0.0), yaw=28.0, pitch=5.0, roll=-2.0,
        torso_pos=(54.0, 92.5, -2.0), torso_yaw=13.0, torso=dict(width=0.94, depth=0.98, slope=1.9),
        poses={'neutral': (0, 2, 0), 'concerned': (-2, 5, -2), 'determined': (1, 0, 1), 'surprised': (2, -2, 1)},
        head_items=[lambda M, hp: PC.hair_short(M, hp, hairline=-15.8, front_z=3.6, burn_y=3.0, thick=0.6)],
        torso_items=[
            lambda M, t: PC.layered_front(M, t, outer='coat', mid='cardigan', inner='shirt', v_outer=(0.55, 1.0),
                                          v_mid=(0.30, 6.0), outer_t=2.9, mid_t=1.8, lapel=False, collar_h=0),
            lambda M, t: PC.surface_buttons(M, t, 2.2, [(0.3, 19.0), (0.5, 26.0)], r=1.0),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=PC3.groups_std({'cardigan': 5, 'button': 7}),
        tone_passes=[PC.pass_strands('hair', seed=141), PC.pass_stitches('coat', 4.6, seed=142),
                     PC.pass_knit('cardigan', ribs=34, seed=143)],
        rgb_passes=[PC.glasses('round', rim='#3e454c', rim_hi='#c4ccd2', glare='#a6b6c0', lens_r=lens),
                    pass_tape(lens), pass_pencil(), pass_darns()],
        eye=dict(iris='#5a5a4e', iris_d='#34342c', sclera='#bcb4a6', sclera_d='#6a6670', lash='#140e10',
                 pupil='#0a0a0c', catch='#efe4cc'),
        brow=dict(col='#5a5a5a', col_l='#8a8884'),
        mouth=dict(line='#3a1a1c', corner='#552a28', inner='#1a0a0b', teeth='#ada08a', tongue='#6c3032'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'deep', 'hooded', 'droop'),
            extra=[PC.ear_detail, PC.wrinkles(forehead=2, crow=True, naso=True, under=True), PC.eye_bags(),
                   PC3.cheek_hollow, PC.stubble(density=0.55, seed=144)],
            brows={'neutral': dict(arch=0.5, lift_inner=0.4), 'concerned': dict(lift_inner=2.2, lift_outer=-0.4,
                                                                                 arch=0.3),
                   'determined': dict(lift_inner=-1.4, arch=0.1, dy=0.4),
                   'surprised': dict(dy=-1.6, arch=1.1, lift_inner=0.6)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.6, -3.8, 17.2), (10.6, -3.0, 13.4)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.2, smile=0.25), 'concerned': dict(corner_drop=0.9),
                   'determined': dict(corner_drop=0.5), 'surprised': dict(parted=1)}),
        priority={'button': 3},
    )


def marta_portrait():
    """Marta Vogel (34): a round, open face with full red cheeks, a short straight nose, a wide warm mouth, quick
    eyes with a lifted outer corner under level brows; short dark-blond hair under the uniform cap with the small
    brass „74“ (no badge, no insignia), the grey knitted scarf, the dark-blue coat with brass buttons, the strap of
    the money satchel.  Berlin dawn behind her."""
    PG, PC, FC, PP, S, PC3 = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0b0d18', '#1e1c2a', '#3a2a36', '#603c44', '#8c5a52', '#b67c64', '#d8a282', '#eecaa6')
    rim = '#8090bc'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=14))
    styles['cheek'] = MatStyle(PC3.lip_of(sk, warm=26), PC.SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24,
                               ao=0.75)
    navy = ramp('#04050b', '#090c16', '#0f1424', '#171e34', '#212a46', '#2c3858', '#3a486c')
    brass = ramp('#1a1208', '#3d2c12', '#6e5222', '#a07c36', '#d1ad5c', '#f0d890')
    styles.update(PC3.coat_style(navy, PC3.TH6, rim))
    styles.update({
        'cap': MatStyle(ramp('#04050b', '#0a0d18', '#121828', '#1b2338', '#262f4a', '#323e5c'),
                        [0.06, 0.14, 0.27, 0.45, 0.66], dither=0.04, rim='#6c80aa'),
        'cap_band': MatStyle(ramp('#020306', '#06080e', '#0c1018', '#141a26', '#1e2634'), [0.08, 0.2, 0.4, 0.65],
                             rim='#4a5a78'),
        'visor': MatStyle(ramp('#030304', '#0b0b0f', '#1a1a22', '#3a3c46', '#7d8190'), [0.1, 0.3, 0.55, 0.8],
                          rim='#8a98b8', spec=1.4, spec_pow=18.0),
        'cord': MatStyle(ramp('#06080e', '#10141e', '#1c2232', '#2a3248'), [0.1, 0.3, 0.6], rim='#6c80aa'),
        'button': MatStyle(brass, [0.05, 0.12, 0.25, 0.42, 0.62], rim='#d1ad5c', spec=0.8),
        'scarf': MatStyle(ramp('#0c0c0e', '#1a1a1d', '#2a2a2e', '#3c3c40', '#505054', '#666668', '#7e7e7e'),
                          PC3.TH6, dither=0.03, rim='#8a96b0'),
        'strap': MatStyle(ramp('#0a0607', '#1b0f0b', '#2e1a10', '#462816', '#60381e'), [0.05, 0.12, 0.24, 0.40],
                          rim='#7a7488'),
        'shirt': MatStyle(ramp('#0b0c12', '#1a1c24', '#2a2c36'), [0.1, 0.3], rim=rim),
        'hair': MatStyle(ramp('#140f08', '#2c2214', '#46381f', '#62502e', '#80693e', '#9e8452', '#bca06a'),
                         [0.04, 0.10, 0.19, 0.31, 0.47, 0.68], rim='#a8a8c4', wrap=0.3, lift=0.2),
    })
    head = dict(PC.FEMALE)
    head.update(PC3.SOFT)
    head.update(skull_r=(15.8, 16.2, 19.6), mid_h=(10.8, 6.2, 11.0), cheek_c=(10.4, 3.6, 10.4),
                cheek_r=(5.2, 3.6, 4.6), malar_r=(4.8, 4.2, 4.0), jaw_angle=(9.8, 13.2, -4.0),
                low_r=(11.0, 9.4, 12.4), chin_c=(0.0, 20.2, 11.6), chin_h=(3.6, 2.7, 3.0), chin_rad=3.0,
                chin_pt=(3.6, 21.2, 10.0), nose_root=(0.0, -0.8, 15.2), nose_tip=(0.0, 8.0, 18.8), tip_r=2.15,
                nose_r=(1.2, 1.7), ala_x=2.2, ala_r=(1.45, 1.35, 1.7), eye_x=6.6, mouth_y=14.0,
                lip_up=(0.0, 13.3, 16.2), lip_up_r=(4.3, 1.2, 1.4), lip_lo=(0.0, 15.4, 15.8), lip_lo_r=(3.8, 1.5, 1.5),
                brow_r=(11.4, 2.0, 2.8), extra=PC.blush(c=(9.4, 6.6, 11.2), r=(4.6, 3.6, 3.4)))
    digits = ['www.w.w', '..w.w.w', '..w.www', '.w....w', '.w....w']      # „74“, brass on the cap front
    return dict(
        id='marta', city='berlin',
        look=dict(key=(0.56, -0.44, 0.71), rim=(-0.80, -0.34, -0.50), ambient=0.08, bg='c4_loop', glow=(0.80, 0.18)),
        head=head, zoom=1.16, smooth=2,
        head_pos=(55.0, 57.0, 0.0), yaw=30.0, pitch=2.0, roll=1.0,
        torso_pos=(55.5, 92.0, -0.5), torso_yaw=13.0, torso=dict(width=0.98, depth=1.02, slope=1.3),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -2), 'determined': (2, -1, 2), 'surprised': (3, -3, 1)},
        head_items=[lambda M, hp: PC.peaked_cap(M, hp, y0=-12.8, tilt=(3.0, -2.0), band_r=(16.8, 20.6),
                                                top_r=(18.6, 22.6), h=8.8),
                    lambda M, hp: PC.hair_short(M, hp, hairline=-12.0, front_z=8.6, nape=8.6, burn_y=5.2,
                                                thick=1.8)],
        torso_items=[
            lambda M, t: PC.coat_layers(M, t, v_open=0.20, v_top=6.0, lapel=True, collar_h=6.5,
                                        collar_r=(12.0, 13.6)),
            lambda M, t: PC.scarf_wrap(M, y=-6.6, r=10.0, tube=4.6, ends=True,
                                       end_pts=[(2.0, -2.0, 12.0), (3.4, 8.0, 13.4), (4.0, 18.0, 14.2)], seed=151),
            lambda M, t: PC.band_on(M, t, 3.3, (-7.0, 18.0), 44.0, 2.6, 'strap', y_range=(2.0, 60.0)),
            lambda M, t: PC.surface_buttons(M, t, 2.6, [(-7.2, 14.0), (7.2, 14.0), (-7.6, 22.0), (7.6, 22.0)],
                                            r=1.1),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck', 'cheek'),
        groups=PC3.groups_std({'cheek': 0, 'cap': 2, 'cap_band': 2, 'cord': 2, 'visor': 3, 'scarf': 6, 'strap': 7,
                               'button': 7}),
        tone_passes=[PC.pass_strands('hair', seed=152), PC.pass_knit('scarf', ribs=26, seed=153),
                     PC.pass_grain('coat', 0.05, seed=154), PC.pass_grain('cap', 0.05, seed=155)],
        rgb_passes=[PC3.pass_badge((0.0, -15.6, 21.2), digits, {'w': '#dcb862'})],
        eye=dict(iris='#4e6276', iris_d='#2c3a48', sclera='#c8beb2', sclera_d='#6e6a78', lash='#120a0c',
                 pupil='#08070a', catch='#f2ead8'),
        brow=dict(col='#4a3a24', col_l='#6e5a3a'),
        mouth=dict(line='#4e1c20', corner='#64302e', inner='#1a0a0d', teeth='#c0b2a2', tongue='#763236'),
        features=dict(
            eyes=FC.eye_shapes(PC._female_eyes(), 'round'),
            extra=[PC.ear_detail, PC.wrinkles(forehead=0, crow=True, naso=False, under=False)],
            brows={'neutral': dict(arch=0.5, lift_inner=0.2), 'concerned': dict(lift_inner=2.0, lift_outer=-0.4,
                                                                                 arch=0.3),
                   'determined': dict(lift_inner=-1.6, arch=0.2, dy=0.5),
                   'surprised': dict(dy=-1.8, arch=1.4, lift_inner=0.5)},
            brow_thick=((2, 2, 1), (1, 1, 1)), brow_pts=((1.8, -4.2, 17.0), (10.4, -4.0, 13.2)),
            mouth={'neutral': dict(smile=0.7), 'concerned': dict(corner_drop=0.8),
                   'determined': dict(corner_drop=0.3), 'surprised': dict(parted=2)}),
        priority={'button': 3, 'cord': 2, 'visor': 1, 'scarf': 1, 'strap': 1},
    )


def registrar_portrait():
    """Registrator Fengler (about 50): a smooth, well-fed face with full cheeks, a soft double chin, a short
    slightly upturned nose and a small mouth; hooded, bored eyes behind rimless glasses (only the lens edges catch
    the light); dark hair combed flat from a precise side parting, grey at the temples; the light-grey dust coat
    over a dark suit, white shirt and dark tie, a plain round pin on the lapel.  Fluorescent tubes overhead."""
    PG, PC, FC, PP, S, PC3 = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0a1010', '#1c1c24', '#382a32', '#5c3c40', '#88584e', '#b27a62', '#d29e7e', '#e8c4a0')
    rim = '#8eac94'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=-6))
    dust = ramp('#0e100f', '#1e211f', '#323632', '#4a4f4a', '#646a64', '#80867f', '#9da39b', '#b8beb5')
    styles.update({
        'coat': MatStyle(dust, [0.04, 0.09, 0.17, 0.28, 0.42, 0.60, 0.80], dither=0.03, rim=rim),
        'coat_lapel': MatStyle(dust, [0.04, 0.09, 0.17, 0.28, 0.42, 0.60, 0.80], rim=rim),
        'suit': MatStyle(ramp('#060708', '#0d0f11', '#16191b', '#212528', '#2e3236'), [0.06, 0.16, 0.34, 0.58],
                         rim=rim),
        'shirt': MatStyle(ramp('#14161a', '#30343a', '#585c60', '#868884', '#b2b2aa', '#d6d4c8', '#ecebe0'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#b8d0c0'),
        'tie': MatStyle(ramp('#050508', '#0c0b12', '#16131c', '#221d28'), [0.08, 0.2, 0.45], rim=rim),
        'pin': MatStyle(ramp('#1a1c1e', '#3c4044', '#6a7074', '#9aa0a4', '#c8ccd0'), [0.06, 0.16, 0.32, 0.55],
                        rim='#d8e0dc', spec=0.9),
        'button': MatStyle(ramp('#121412', '#262a26', '#3c403c', '#565a56'), [0.08, 0.25, 0.5], rim=rim),
        'hair': MatStyle(ramp('#080706', '#15120f', '#231e19', '#332b24', '#463b31', '#5a4c3f'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#86a08c', wrap=0.25),
    })
    head = dict(skull_r=(16.0, 16.8, 20.2), mid_h=(12.0, 7.0, 11.8), cheek_c=(11.0, 4.0, 10.0),
                cheek_r=(6.0, 4.2, 5.0), malar_r=(3.8, 3.4, 3.2), jaw_angle=(12.4, 15.0, -3.2),
                low_r=(13.2, 11.0, 13.4), chin_c=(0.0, 21.6, 11.8), chin_h=(4.8, 3.4, 3.6), chin_pt=(3.6, 22.6, 10.4),
                nose_root=(0.0, -0.8, 15.4), nose_tip=(0.0, 8.6, 19.2), tip_r=2.3, nose_r=(1.3, 1.8), ala_x=2.4,
                ala_r=(1.6, 1.4, 1.8), brow_r=(12.0, 2.2, 3.0), lip_up_r=(3.4, 0.9, 1.1), lip_lo_r=(3.0, 1.15, 1.2),
                neck_r=(8.6, 9.8),
                jaw_extra=[('ellipsoid', ((0.0, 24.4, 8.0), (6.8, 2.6, 4.6), 'skin', 2.6))])
    return dict(
        id='registrar', city='berlin',
        look=dict(key=(0.40, -0.66, 0.64), rim=(-0.78, -0.40, -0.48), ambient=0.10, bg='c4_annex',
                  glow=(0.62, 0.08)),
        head=head, zoom=1.12,
        head_pos=(55.0, 56.0, 0.0), yaw=26.0, pitch=2.0, roll=0.0,
        torso_pos=(55.0, 93.0, -0.5), torso_yaw=11.0, torso=dict(width=1.08, depth=1.10, slope=1.0),
        poses={'neutral': (0, 0, 0), 'concerned': (-1, 2, -1), 'determined': (1, -1, 0), 'surprised': (1, -2, 1)},
        head_items=[lambda M, hp: PC.hair_short(M, hp, hairline=-13.4, front_z=8.4, burn_y=2.0, thick=1.0)],
        torso_items=[
            lambda M, t: PC.layered_front(M, t, outer='coat', mid='suit', inner='shirt', v_outer=(0.34, 3.0),
                                          v_mid=(0.20, 5.0), lapel=True, collar_h=5.0, collar_r=(11.8, 13.4)),
            lambda M, t: PC.tie_knot_collar(M),
            lambda M, t: PC.tie(M, mat='tie', top=(0.3, 3.8, 11.8), bot=(0.8, 24.0, 13.6)),
            lambda M, t: PC.surface_buttons(M, t, 3.4, [(-10.0, 10.0)], r=1.1, mat='pin'),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=PC3.groups_std({'suit': 5, 'tie': 5, 'pin': 7}),
        tone_passes=[PC.pass_strands('hair', seed=161), pass_parting(), PC.pass_grain('coat', 0.04, seed=162)],
        rgb_passes=[pass_temples(), PC.glasses('round', rim='#6c706c', rim_hi='#dce8e4', glare='#c8dcd8',
                                                lens_r=(3.9, 3.1))],
        eye=dict(iris='#5c6458', iris_d='#363c34', sclera='#c4bcb0', sclera_d='#6c6a70', lash='#120c0e',
                 pupil='#0a0a0c', catch='#eef2e6'),
        brow=dict(col='#2e2620', col_l='#4c4238'),
        mouth=dict(line='#3c1c20', corner='#56282a', inner='#1a0a0d', teeth='#b8ab98', tongue='#6c3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'hooded', 'round'),
            extra=[PC.ear_detail, PC.wrinkles(forehead=1, crow=False, naso=True, under=True)],
            brows={'neutral': dict(arch=0.2), 'concerned': dict(lift_inner=1.2, lift_outer=-0.2, arch=0.2),
                   'determined': dict(lift_inner=-1.0, arch=0.0, dy=0.4),
                   'surprised': dict(dy=-1.2, arch=0.8, lift_inner=0.3)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.8, -4.2, 17.0), (10.4, -3.8, 13.4)), nostril='small',
            mouth={'neutral': dict(smile=0.15), 'concerned': dict(corner_drop=0.5),
                   'determined': dict(corner_drop=0.3), 'surprised': dict(parted=1)}),
        priority={'pin': 3, 'tie': 1},
    )


PORTRAITS_C4 = {'lev': lev_portrait, 'marta': marta_portrait, 'registrar': registrar_portrait}


def build_portraits(ids, char_dir, preview_tag='c4_portrait'):
    """Writes the living portraits of `ids` below `char_dir` (an assets/characters directory) + 3x previews."""
    PG, PC, FC, PP, S, PC3 = _portrait_mods()
    for cid, fn in PORTRAITS_C4.items():
        PC.CAST.setdefault(cid, fn)
    PG.set_out(char_dir)
    for cid in ids:
        if cid not in PORTRAITS_C4:
            continue
        spec, frames, grid = PG.build_char(cid, write=True)
        PG.preview(cid, frames, spec.get('expressions', PG.EXPRESSIONS), tag=preview_tag)
        pj = os.path.join(char_dir, cid, 'portrait.json')
        meta = json.load(open(pj, encoding='utf-8'))
        meta['anim']['spec'] = 'tools/pixelgen/characters_c4.py'
        with open(pj, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
            f.write('\n')


# ----------------------------------------------------------------------------------- tables
CAST_C4 = {'lev': lev, 'marta': marta, 'registrar': registrar}
_NPC = ['idle_side', 'walk_side', 'idle_front', 'talk_side', 'blink_side', 'look_side', 'gesture_side',
        'blink_front', 'talk_front']
ROWS_C4 = {'lev': list(_NPC), 'marta': list(_NPC), 'registrar': _NPC + ['work_side']}
# figure height (px, idle_side frame 0, incl. headgear) the validator expects
EXPECT_H_C4 = {'lev': (42, 46), 'marta': (42, 46), 'registrar': (44, 48)}


# =================================================================================== install / out
def install():
    """Extend the existing pipeline's tables in memory (idempotent).  The Chapter-3 runners' own in-memory tables
    come first, so the validator sees the same expectations as their runs."""
    import characters_c3p2 as RC3P2
    RC3P2.install()
    CH.CAST.update(CAST_C4)
    CH.ROWS.update(ROWS_C4)
    CHK.EXPECT_H.update(EXPECT_H_C4)
    for cid, rows in ROWS_C4.items():          # NPC rule: exactly the rows this cast ships
        CHK.NPC_MIN[cid] = list(rows)


def set_out(root):
    CH.OUT = os.path.join(root, 'assets', 'characters') if root else CH.OUT
    CH.PREV = os.path.join(CH.OUT, '_preview')
    CHK.OUT = CH.OUT


def _dir_of(cid):
    d = os.path.join(CH.OUT, cid)
    if not os.path.exists(os.path.join(d, 'sheet.json')):
        d = os.path.abspath(os.path.join(HERE, '..', '..', 'assets', 'characters', cid))
    return d


def _load(cid):
    d = _dir_of(cid)
    meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
    return np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA')), meta


def _cell(sheet, meta, anim, f=0):
    r = meta['anims'][anim]['row']
    return Image.fromarray(np.ascontiguousarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W]),
                           'RGBA')


# ----------------------------------------------------------------------------------- previews (<= 1280 px wide)
BGS = [(34, 28, 26, 255), (44, 52, 74, 255), (40, 52, 46, 255), (150, 160, 150, 255)]   # cellar, dawn, annex, haze


def preview_lineup(ids):
    """idle_side frame 0 of the new cast between the reference cast (1x strip at 4x on four backgrounds) and a
    silhouette strip: readability at game scale and no twin silhouettes."""
    order = ids + [r for r in REFERENCE if os.path.exists(os.path.join(_dir_of(r), 'sheet.json'))]
    strip = Image.new('RGBA', (CELL_W * len(order), CELL_H), (0, 0, 0, 0))
    for i, cid in enumerate(order):
        sh, me = _load(cid)
        strip.alpha_composite(_cell(sh, me, 'idle_side'), (i * CELL_W, 0))
    out = Image.new('RGBA', (strip.width, CELL_H * (len(BGS) + 1)), (0, 0, 0, 255))
    for k, bg in enumerate(BGS):
        out.paste(CH.on_bg(strip, bg), (0, k * CELL_H))
    sil = np.array(Image.new('RGBA', strip.size, (205, 210, 200, 255)))
    sil[np.array(strip)[..., 3] > 0] = (20, 20, 24, 255)
    out.paste(Image.fromarray(sil), (0, len(BGS) * CELL_H))
    k = max(1, min(4, 1280 // out.width))
    CH.up(out, k).save(os.path.join(CH.PREV, 'c4_lineup.png'))


def preview_rows(cid):
    """Every row of one character on the cellar / dawn / annex backgrounds, scaled to <= 1280 px."""
    sheet, meta = _load(cid)
    img = Image.fromarray(sheet, 'RGBA')
    tiles = [CH.on_bg(img, bg) for bg in BGS[:3]]
    out = Image.new('RGBA', (img.width * 3 + 16, img.height), (0, 0, 0, 255))
    for j, t in enumerate(tiles):
        out.paste(t, (j * (img.width + 8), 0))
    k = max(1, min(4, 1280 // out.width))
    CH.up(out, k).save(os.path.join(CH.PREV, f'c4_{cid}_rows.png'))


def preview_heads(ids):
    """The heads of idle_side / idle_front frame 0 at 8x (review of the hand-drawn maps)."""
    tiles = []
    for cid in ids + ['alexei', 'konrad', 'emil']:
        sheet, meta = _load(cid)
        for a in ('idle_side', 'idle_front', 'talk_side'):
            f = 3 if a == 'talk_side' else 0
            tiles.append(CH.on_bg(_cell(sheet, meta, a, f).crop((4, 0, 28, 30)), (58, 62, 70, 255)))
    per = 6                                    # two characters per line
    lines = (len(tiles) + per - 1) // per
    out = Image.new('RGBA', (per * 26 - 2, lines * 32 - 2), (0, 0, 0, 255))
    for i, t in enumerate(tiles):
        out.paste(t, ((i % per) * 26, (i // per) * 32))
    k = max(1, min(8, 1280 // out.width))
    CH.up(out, k).save(os.path.join(CH.PREV, 'c4_heads.png'))


# ----------------------------------------------------------------------------------- checks
EXPR = ['neutral', 'concerned', 'determined', 'surprised']


def check_c4(ids=None) -> list[str]:
    """Contract checks beyond characters_check: exact rows, round-2 talk rhythm and a visible gesture, walk speed,
    living portraits (contract, talking mouth, blink, four distinct expressions, opaque), and silhouettes distinct
    from each other and from the existing cast (IoU of idle_side frame 0 <= 0.90)."""
    fails = []
    ids = ids or C4_IDS
    sil = {}
    for cid in ids + REFERENCE:
        d = _dir_of(cid)
        if not os.path.exists(os.path.join(d, 'sheet.json')):
            if cid in ids:
                fails.append(f'{cid}: sheet missing')
            continue
        sheet, meta = _load(cid)
        a = sheet[..., 3] > 0
        r = meta['anims']['idle_side']['row']
        sil[cid] = a[r * CELL_H:(r + 1) * CELL_H, :CELL_W]
        if cid in REFERENCE:
            continue
        if list(meta['anims']) != ROWS_C4[cid]:
            fails.append(f'{cid}: rows {list(meta["anims"])} != {ROWS_C4[cid]}')
        if meta.get('origin') != [16, 54] or meta.get('cell') != [32, 56]:
            fails.append(f'{cid}: cell/origin differ from the contract')
        for row in ('talk_side', 'gesture_side', 'talk_front'):
            t = meta['anims'].get(row)
            if not t:
                continue
            if row.startswith('talk') and t['frames'] != 8:
                fails.append(f'{cid}: {row} has {t["frames"]} frames, expected 8 (round-2 rhythm)')
            rr = t['row']
            fr = [a[rr * CELL_H:(rr + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W] for f in range(t['frames'])]
            moved = max((fr[0] ^ fr[k]).sum() for k in range(1, len(fr)))
            if moved < 8:
                fails.append(f'{cid}: {row} gesture too small ({moved} px change)')
        gs = meta.get('ground_speed', {}).get('walk_side', 0)
        if not 15.0 <= gs <= 30.0:
            fails.append(f'{cid}: walk_side ground_speed {gs} outside 15..30 px/s (an NPC walks slower than 34)')
        pp, pj = os.path.join(d, 'portrait.png'), os.path.join(d, 'portrait.json')
        if not (os.path.exists(pp) and os.path.exists(pj)):
            fails.append(f'{cid}: portrait missing (run with --portraits)')
            continue
        meta_p = json.load(open(pj, encoding='utf-8'))
        if meta_p.get('size') != [112, 112] or meta_p.get('expressions') != EXPR:
            fails.append(f'{cid}: portrait.json {meta_p.get("size")} {meta_p.get("expressions")} off contract')
        anim = meta_p.get('anim') or {}
        ap = os.path.join(d, 'portrait_anim.png')
        if anim.get('file') != 'portrait_anim.png' or not os.path.exists(ap):
            fails.append(f'{cid}: no living portrait (portrait_anim.png + anim block, round-2 contract)')
            continue
        grid = np.asarray(Image.open(ap).convert('RGBA'))
        rows = anim.get('rows', [])
        if grid.shape[:2] != (112 * len(rows), 448):
            fails.append(f'{cid}: portrait_anim.png {grid.shape[:2]} does not match {len(rows)} rows x 4')
            continue
        strip = np.asarray(Image.open(pp).convert('RGBA'))
        if strip.shape[:2] != (112, 448) or (strip[..., 3] < 255).any():
            fails.append(f'{cid}: portrait strip {strip.shape[:2]} / transparent pixels')
        frames = [strip[:, k * 112:(k + 1) * 112, :3].astype(int) for k in range(4)]
        for k in range(1, 4):
            if (np.abs(frames[k] - frames[0]).sum(-1) > 0).sum() < 30:
                fails.append(f'{cid}: portrait expression {EXPR[k]} barely differs from neutral')
        for j, row in ((2, 'talk_open'), (3, 'blink')):
            if j < len(rows):
                diff = (np.abs(grid[j * 112:(j + 1) * 112, :112, :3].astype(int)
                               - grid[:112, :112, :3].astype(int)).sum(-1) > 0).sum()
                if diff < 6:
                    fails.append(f'{cid}: portrait row {row} barely differs from rest ({diff} px)')
    keys = list(sil)
    for i, p in enumerate(keys):
        for q in keys[i + 1:]:
            if p in REFERENCE and q in REFERENCE:
                continue
            inter = (sil[p] & sil[q]).sum()
            uni = (sil[p] | sil[q]).sum()
            if uni and inter / uni > 0.90:
                fails.append(f'silhouettes of {p} and {q} nearly identical (IoU {inter / uni:.2f})')
    return fails


def run_checks(ids=None) -> int:
    print('--- characters_check (tables extended in memory) ---')
    keep = CHK.OUT
    rc = CHK.main()
    CHK.OUT = keep
    print('--- C4 contract checks ---')
    fails = check_c4(ids)
    for f in fails:
        print('  -', f)
    print('OK: C4 cast checks pass' if not fails else 'FAIL: C4 cast checks')
    return 1 if (rc or fails) else 0


# ----------------------------------------------------------------------------------- main
def main(argv):
    install()
    args = [a for a in argv[1:] if not a.startswith('--')]
    opts = dict(a[2:].split('=', 1) if '=' in a else (a[2:], '1') for a in argv[1:] if a.startswith('--'))
    if 'out' in opts:
        set_out(os.path.abspath(opts['out']))
    if 'check' in opts:
        return run_checks(args or None)
    ids = args or C4_IDS
    bad = [c for c in ids if c not in CAST_C4]
    if bad:
        print('not a C4 character:', bad)
        return 2
    os.makedirs(CH.PREV, exist_ok=True)
    open(os.path.join(CH.PREV, '.gdignore'), 'a').close()
    for cid in ids:
        spec, sheet, nsheet, meta = CH.build_sheet(cid)
        print(f'{cid:10s} rows={",".join(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]} '
              f'ground_speed={meta.get("ground_speed", {})}')
        preview_rows(cid)
    preview_heads(ids)
    if 'heads' in opts:
        return 0
    preview_lineup(ids)
    if 'portraits' in opts:
        build_portraits(ids, CH.OUT)
    return run_checks(ids)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
