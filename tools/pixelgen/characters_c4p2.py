"""characters_c4p2.py -- the Chapter-4 part-2 cast („Stimmen unter Beton“, second half) on the round-2 rig, with
living portraits for the four new speakers and life sheets for the three watchers.

    py -3 -P tools/pixelgen/characters_c4p2.py                  (all seven: sheets, previews, checks)
    py -3 -P tools/pixelgen/characters_c4p2.py maria hanna      (selected ids)
    py -3 -P tools/pixelgen/characters_c4p2.py --portraits      (additionally the living portraits through
                                                                chargen_portrait2; specs: PORTRAITS_C4P2 below)
    py -3 -P tools/pixelgen/characters_c4p2.py --check          (validate only)
    py -3 -P tools/pixelgen/characters_c4p2.py --heads          (review: the heads only, 8x, next to the cast)
    py -3 -P tools/pixelgen/characters_c4p2.py --out=DIR        (review run: write everything below DIR)

The cast (documentation/C4P2_DESIGN.md section 5; costume notes: documentation/asset_manifest_parts/c4p2_cast_audio.md;
round 10 art review: no figure may be a recolour of an existing one -- Hanna is not Elena, Wendt is not Kessler, Maria
is not Irina):
  maria          Maria Gorelowa (34), returnee from Veltrava, Kolonne 4 -- a green woollen headscarf with a woven check
                 tied UNDER THE CHIN, a thin Western wool coat (plum heather, lapels: Veltrava) under an issued Soviet
                 quilted vest, felt boots a size too big, pale linen rags round her hands, coal on her face, a needle in
                 her lapel (a seamstress); a long angular face, an old break in the nose, dark eyes, high cheekbones, a
                 straight back.  Works: shovels coal.
  hanna          Hanna Adler (27), teacher, Konrad's younger sister -- dark-blonde hair pinned up in a knot high on the
                 crown, a round open face with freckles; a knee-length navy swing coat over a grey cardigan and a tweed
                 skirt, the rust-red knitted scarf thrown on loosely with both ends down the front, chalk dust on the
                 sleeve and the coat, a bunch of keys in her hand; the family's upright posture, freer than Konrad's.
  wendt          Kommissar Ludwig Wendt (about 50), Staatspolizei -- heavy and broad; a pearl-grey homburg with a black
                 band, dark hair grey at the temples, a dark grey civilian overcoat with a wide dark-brown fur shawl
                 collar, a bottle-green silk foulard (no white collar, no tie), black leather gloves, a small notebook;
                 clean-shaven, heavy-lidded, jowls.  No uniform, no insignia, no moustache or glasses that quote a
                 historical perpetrator.
  blockwart      Erwin Kuhnert (about 60), caretaker and Blockleiter of Kolonnenstrasse 12-18 -- a brown work coat
                 over a cardigan, a flat cap, reading glasses on a string, a big key ring at the belt, the wooden card
                 box clamped under his arm (held against his belly while he sorts it), felt slippers in galoshes.  The
                 armband exists ONLY in sheet_hist.png (TECHNICAL_ARCHITECTURE 12.4, resolved by Symbols.pick at
                 runtime); the neutral sheet has none.
  guard_karsk    (life sheet) a young Soviet guard: a long sheepskin coat with the fleece at collar, cuffs and hem, a belt,
                 the ushanka's flaps tied up, a rifle slung on his back (the barrel stands clear behind the ushanka);
                 warms his hands at the barrel fire.  Neutral: a plain ushanka; sheet_hist.png: the small red star.
  press_officer  (life sheet) the Soviet press minder: a good grey double-breasted city coat, a karakul pirozhok,
                 glasses, a tan briefcase clamped under the near arm, a cigarette in the same hand; smokes.
  stapo_civil    (life sheet) the man at the kiosk: a black belted leather coat, a dark hat with the brim snapped
                 down, a newspaper he does not read; watches over its edge.
  alexei_press   (look, KarskB) Alexei made presentable for the Swede's cameras: shaved, the ushanka's flaps tied up, a
                 new cream-white wool scarf; the protagonist rows plus the carry rows with Ekdahl's red guidebook under
                 his arm (the c4p2.json "carry" row of KarskB) -- c4p2.json "looks" {"L_C4P2_KarskB": {"alexei":
                 "alexei_press"}}.
The work loops play in the part-2 level shells (idle_anim = "work_side" on Maria, the guard, the minder, the man at the
kiosk and Kuhnert).  check_props() proves that every listed prop shows in every frame of its rows.

Everything goes through the EXISTING pipeline: characters.py (ANIMS, ROWS, build_sheet, previews), characters_check.py
and characters_c4.py are imported and their tables extended IN MEMORY (nothing is patched on disk); heads are
hand-drawn ASCII maps in the chargen_heads format, hands from chargen_body.make_hands, animation keys from
chargen_anim (the gestures / work loops of this cast are added in memory).  The portraits are chargen_portrait2
specs registered in memory in chargen_portrait2_cast.CAST and written by chargen_portrait2.build_char (round-2
contract: portrait.png, portrait_anim.png, portrait.json).  Deterministic: no randomness, no network, no image
inputs.  Outputs: assets/characters/<id>/sheet.png, sheet_n.png, sheet.json (+ sheet_hist.png for blockwart and
guard_karsk), portrait.png, portrait_anim.png, portrait.json (the four speakers); review images
assets/characters/_preview/c4p2_* (git-ignored, .gdignore).
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
import characters_c4 as RC4               # noqa: E402  the part-1 runner (install chain, previews, checks)
import chargen_anim as A                  # noqa: E402
import chargen_core as C                  # noqa: E402
import chargen_heads as HD                # noqa: E402
from chargen_body import CELL_H, CELL_W, Coat, Skirt, Spec, M, make_hands   # noqa: E402
from chargen_core import put_bitmap                                 # noqa: E402
from chargen_cast import (EYE_B, EYE_K, GLASS, SKIN, belt_front, belt_side, bm, boot_bitmaps, buttons,  # noqa: E402
                          column_line, flap, lag_dx, lapels_front, materials, put_line, put_poly, quilt_lines,
                          side_light, walking, _puff)
from chargen_cast_c3 import (BRASS, CHROME, GREY_HAIR, TALK_HANDS, TALK_NOD, calm_front_hem,  # noqa: E402
                             ladies_boots, put_hand)

C4P2_IDS = ['maria', 'hanna', 'wendt', 'blockwart', 'guard_karsk', 'press_officer', 'stapo_civil', 'alexei_press']
SPEAKERS = ['maria', 'hanna', 'wendt', 'blockwart']            # with living portraits
LIFE = ['guard_karsk', 'press_officer', 'stapo_civil']          # life sheets (side rows + a working idle)
LOOKS = {'alexei_press': 'alexei'}                              # looks of existing characters (sheet + portrait)
REFERENCE = ['alexei', 'konrad', 'emil', 'clerk', 'guard', 'conductor', 'kessler', 'typist', 'berlin_mother',
             'berlin_father', 'porter', 'librarian', 'worker_a', 'worker_b', 'border_officer', 'babushka', 'irina',
             'vendor', 'elena', 'journalist', 'voronova', 'lev', 'marta', 'registrar']

# ----------------------------------------------------------------------------------- scenes
# OKLCh hue / chroma of the shadow and light tints (data/chapters/c4p2.json grades): the Karsk depot at dawn and in
# the evening floodlights (sodium / kerosene amber light, a cold blue-teal shadow over coal black), the Berlin
# Ostbahnhof under its glass roof (sodium light in the steam, a grey-violet shadow), the courtyard of No. 14 at night
# (night blue shadow, warm window light).
C.SCENE_TINT.setdefault('c4p2_depot', dict(shadow_h=232.0, shadow_c=0.050, light_h=66.0, light_c=0.078))
C.SCENE_TINT.setdefault('c4p2_station', dict(shadow_h=278.0, shadow_c=0.040, light_h=78.0, light_c=0.062))
C.SCENE_TINT.setdefault('c4p2_court', dict(shadow_h=262.0, shadow_c=0.056, light_h=70.0, light_c=0.058))
RIM_C4P2 = {
    'c4p2_depot': np.array([166, 180, 204, 255], np.uint8),     # the cold dawn sky behind the coal stage
    'c4p2_station': np.array([196, 188, 166, 255], np.uint8),   # sodium light through the steam
    'c4p2_court': np.array([132, 150, 190, 255], np.uint8),     # night blue from the open courtyard
}

# ----------------------------------------------------------------------------------- gestures / work (in memory)
# Maria: after a shovelful she straightens, both rag-wrapped hands pressed into the small of her back
A.GESTURES.setdefault('press_back', [
    {}, {'arm_n': (-14, 40), 'arm_f': (-16, 44)}, {'arm_n': (-22, 62), 'arm_f': (-24, 66), 'lean': -2.0,
                                                    'head': (0, -1), 'breath': 1},
    {'arm_n': (-24, 66), 'arm_f': (-26, 70), 'lean': -3.0, 'head': (0, -1), 'breath': 1},
    {'arm_n': (-24, 66), 'arm_f': (-26, 70), 'lean': -3.0, 'head': (0, -1), 'face': 'blink', 'puff': 1},
    {'arm_n': (-20, 58), 'arm_f': (-22, 60), 'lean': -1.6, 'puff': 2}, {'arm_n': (-10, 30), 'puff': 3}, {},
])
# Maria at the coal stage: the blade bites into the pile, lifts, swings up, throws into the tender, comes back.
# The keys are hand TARGETS relative to the shoulder (x forward, y down; the far hand on the shaft's end, the near
# hand low on the shaft) solved to arm angles by _arm_to; 'shovel' = blade state, 'coal' = coal on the blade.
MARIA_ARM = (7.0, 6.0)


def _arm_to(tx, ty, lean, uarm=MARIA_ARM[0], farm=MARIA_ARM[1]):
    """Two-link IK in the side view (chargen_body.side_joints: angles from straight down, + forward, the upper
    arm turned by lean / 2): the (shoulder, elbow) angles that put the wrist at (tx, ty) from the shoulder,
    elbow bent below / behind the line."""
    d = min(max(math.hypot(tx, ty), abs(uarm - farm) + 0.05), uarm + farm - 0.05)
    phi = math.degrees(math.atan2(tx, ty))
    alpha = math.degrees(math.acos(max(-1.0, min(1.0, (uarm * uarm + d * d - farm * farm) / (2 * uarm * d)))))
    a1 = phi - alpha
    ex, ey = uarm * math.sin(math.radians(a1)), uarm * math.cos(math.radians(a1))
    a2 = math.degrees(math.atan2(tx - ex, ty - ey))
    return (round(a1 - lean * 0.5, 1), round(a2 - a1, 1))


# (far hand target, near hand target, lean, stoop, dx, blade, coal, extra)
_SHOVEL_KEYS = [
    ((1.5, 8.5), (4.5, 14.0), 12.0, 6.0, -1.5, 'low', 0, {}),
    ((2.5, 8.5), (5.0, 13.5), 14.0, 8.0, -1.5, 'low', 0, {}),
    ((1.5, 6.5), (5.5, 10.5), 8.0, 4.0, -2.0, 'mid', 1, {}),
    ((0.5, 6.0), (6.0, 2.0), 2.0, 1.0, -2.0, 'high', 1, {}),
    ((1.0, 5.0), (6.5, -1.0), 0.0, 0.0, -2.0, 'throw', 2, {'breath': 1}),
    ((1.0, 7.0), (5.0, 9.0), 4.0, 2.0, -2.0, 'mid', 0, {'face': 'blink'}),
    ((1.5, 7.5), (5.0, 12.0), 8.0, 4.0, -1.5, 'low', 0, {}),
    ((1.5, 8.0), (4.5, 13.5), 10.0, 5.0, -1.5, 'low', 0, {}),
]
A.WORKS.setdefault('shovel', [
    dict({'arm_f': _arm_to(f[0], f[1], ln), 'arm_n': _arm_to(n[0], n[1], ln), 'lean': ln, 'stoop': sp, 'dx': dx,
          'shovel': bl, 'coal': co, 'hand_n': 'fist', 'hand_f': 'fist'}, **ex)
    for (f, n, ln, sp, dx, bl, co, ex) in _SHOVEL_KEYS])
SHOVEL_LEN = 15.0          # far hand (the shaft's end) to the blade's tip, px
# Hanna: the key ring comes up, a thumb finds the right key, it goes back down
A.GESTURES.setdefault('find_key', [
    {}, {'arm_n': (10, 58)}, {'arm_n': (16, 90), 'head': (0, 1), 'keys': 1},
    {'arm_n': (18, 96), 'head': (0, 1), 'keys': 2}, {'arm_n': (18, 96), 'head': (0, 1), 'keys': 1, 'face': 'blink'},
    {'arm_n': (18, 96), 'head': (0, 1), 'keys': 2}, {'arm_n': (12, 64)}, {},
])
# Wendt: the notebook comes up and opens, the far hand notes a word, it closes
A.GESTURES.setdefault('note_word', [
    {}, {'arm_n': (10, 60)}, {'arm_n': (16, 92), 'head': (0, 1), 'lean': 1.0, 'note': 1},
    {'arm_n': (18, 96), 'arm_f': (8, 84), 'head': (0, 1), 'lean': 1.2, 'note': 1},
    {'arm_n': (18, 96), 'arm_f': (10, 92), 'head': (0, 1), 'lean': 1.2, 'note': 1, 'face': 'blink'},
    {'arm_n': (18, 96), 'arm_f': (8, 84), 'head': (0, 1), 'lean': 1.0, 'note': 1},
    {'arm_n': (12, 62)}, {}, {},
])
# Kuhnert: a nervous tug at the peak of the cap, a glance down the passage
A.GESTURES.setdefault('tug_cap', [
    {}, {'arm_n': (14, 96)}, {'arm_n': (30, 128), 'head': (0, 1)}, {'arm_n': (34, 138), 'head': (0, 1)},
    {'arm_n': (32, 134), 'head': (0, 1), 'face': 'blink'}, {'arm_n': (30, 128), 'face': 'look'},
    {'arm_n': (14, 92), 'face': 'look'}, {},
])
# ... the same with the free (far) hand: the card box stays clamped under the near arm (round 10 review)
A.GESTURES.setdefault('tug_cap_f', [
    {}, {'arm_f': (14, 96)}, {'arm_f': (30, 128), 'head': (0, 1)}, {'arm_f': (34, 138), 'head': (0, 1)},
    {'arm_f': (32, 134), 'head': (0, 1), 'face': 'blink'}, {'arm_f': (30, 128), 'face': 'look'},
    {'arm_f': (14, 92), 'face': 'look'}, {},
])
# Kuhnert's working idle: the card box held open against his belly on the far forearm (close to the body, never
# held out), the near hand walks the cards, pulls one, holds it up to the reading glasses, puts it back
_BOX_F = (10.0, 100.0)
A.WORKS.setdefault('cards', [
    {'arm_n': (16, 70), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 0},
    {'arm_n': (18, 76), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 1},
    {'arm_n': (16, 70), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 0},
    {'arm_n': (18, 76), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 1},
    {'arm_n': (26, 104), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.4, 'cards': 2},
    {'arm_n': (28, 112), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.4, 'cards': 2, 'face': 'blink'},
    {'arm_n': (22, 90), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 1},
    {'arm_n': (16, 70), 'arm_f': _BOX_F, 'head': (0, 1), 'lean': 2.0, 'cards': 0},
])
# the press minder: the cigarette to the lips (the ember glows), down, the smoke breathed out, ash tapped off
A.GESTURES.setdefault('one_drag', [
    {}, {'arm_n': (20, 80)}, {'arm_n': (26, 126), 'head': (0, -1), 'ember': 2},
    {'arm_n': (26, 130), 'head': (0, -1), 'ember': 2, 'face': 'blink'}, {'arm_n': (18, 84), 'puff': 1},
    {'arm_n': (14, 64), 'puff': 2}, {'arm_n': (12, 56), 'puff': 3}, {},
])
A.WORKS.setdefault('smoke', [
    {'arm_n': (12, 56)}, {'arm_n': (18, 80)}, {'arm_n': (26, 126), 'head': (0, -1), 'ember': 2},
    {'arm_n': (26, 130), 'head': (0, -1), 'ember': 2}, {'arm_n': (18, 84), 'puff': 1},
    {'arm_n': (14, 64), 'puff': 2}, {'arm_n': (14, 60), 'puff': 3, 'face': 'blink'},
    {'arm_n': (16, 62), 'ash': 1}, {'arm_n': (12, 56), 'ash': 2}, {'arm_n': (12, 56)},
])
# the man at the kiosk: the paper held open, a page turned, a look over its edge, back behind it
A.WORKS.setdefault('read_paper', [
    {'paper': 0}, {'paper': 0}, {'paper': 0, 'face': 'blink'}, {'paper': 1, 'head': (0, 0)},
    {'paper': 2}, {'paper': 0}, {'paper': 3, 'head': (0, -1)}, {'paper': 3, 'head': (0, -1)},
    {'paper': 3, 'head': (0, -1), 'face': 'look'}, {'paper': 0},
])
A.GESTURES.setdefault('fold_paper', [
    {}, {'arm_n': (14, 70)}, {'arm_n': (18, 92), 'head': (0, 1)}, {'arm_n': (18, 92), 'head': (0, 1),
                                                                     'face': 'blink'},
    {'arm_n': (18, 92), 'face': 'look'}, {'arm_n': (14, 70), 'face': 'look'}, {},
])

# ----------------------------------------------------------------------------------- shared materials
RAG = ['#4A443A', '#6E6656', '#948A74', '#B4AA92', '#CEC4AC', '#E4DCC6']          # pale linen rag wrappings
COAL = ['#060606', '#0E0E10', '#18181A', '#242426', '#34343A', '#4A4A52']         # coal, its glints
KEYS = ['#2E2A22', '#5A5240', '#8A8064', '#B4AA88', '#D8D0B0', '#F0EAD2']         # brass / steel key bunch
PAPER_W = ['#4A4A44', '#7E7E74', '#A8A89A', '#C8C8B8', '#DEDED0', '#F0F0E6']
NEWS = ['#3E3C36', '#6E6A5E', '#9A9484', '#BAB3A0', '#D2CBB6', '#E6E0CC']        # newsprint, a little grey
WOOD_BOX = ['#2A1A0E', '#4A3018', '#6C4824', '#8E6434', '#AE8048', '#C89C62']     # the card box (beech)
SMOKE = ['#5A5E62', '#7A7E82', '#9A9EA0', '#B6B8B8', '#CED0CE', '#E2E2DE']
EMBER = ['#3A0E04', '#6E1E06', '#A8380A', '#D8601A', '#F49038', '#FFD08A']
STEEL = ['#1C1E20', '#34383A', '#545A5C', '#7A8082', '#A2A8A8', '#CED2D2']
FLEECE = ['#4A4234', '#706650', '#968A6E', '#B4A88A', '#CCC2A4', '#E2D8BE']      # sheepskin fleece
BREATH = ['#6E7C7A', '#8E9C98', '#AEBAB4', '#C4CEC8', '#DCE2DC', '#EEF2EE']

KEYS_LG = {'k': ('keys', 3), 'K': ('keys', 5), 'o': ('keys', 1), 'r': ('keys', 2)}
COAL_LG = {'c': ('coal', 2), 'C': ('coal', 4), 'o': ('coal', 0)}
BLADE_LG = {'a': ('steel', 1), 'b': ('steel', 2), 'c': ('steel', 3), 'd': ('steel', 4), 'o': ('steel', 0)}
NOTE_LG = {'p': ('paper', 3), 'P': ('paper', 4), 'q': ('paper', 5), 'l': ('paper', 2), 'o': ('book', 1),
           'O': ('book', 2)}
BOX_LG = {'o': ('box', 0), 'a': ('box', 1), 'b': ('box', 2), 'c': ('box', 3), 'd': ('box', 4), 'e': ('box', 5),
          'p': ('paper', 3), 'P': ('paper', 4), 'q': ('paper', 5)}
NEWS_LG = {'o': ('news', 1), 'a': ('news', 2), 'b': ('news', 3), 'c': ('news', 4), 'd': ('news', 5),
           'l': ('news', 0)}
CASE_LG = {'o': ('case', 0), 'a': ('case', 1), 'b': ('case', 2), 'c': ('case', 3), 'd': ('case', 4),
           'm': ('clasp', 4)}


def _rows(sheet: str) -> list[str]:
    return [r for r in sheet.strip('\n').split('\n')]


# =================================================================================== MARIA
# the green woollen headscarf (its woven check shows in the portrait; darker folds here) tied UNDER THE CHIN: it frames
# the face down the cheek to the knot below the jaw, its rolled front edge pushed back off dark hair (k), the back
# corner falls over the nape; high cheekbones (H), dark eyes, coal smudged on the cheek (q).  Round 10 review: the
# nape-tied cap shape was Irina's -- this is a different garment, not a recolour.
MARIA_SIDE = [
    '. . . . 2 3 3 3 . . . .',
    '. . . 2 3 3 3 4 3 . . .',
    '. . 1 2 3 3 3 4 4 3 . .',
    '. . 1 2 2 3 3 3 4 4 3 .',
    '. 1 2 2 2 2 3 4 k S L .',
    '. 1 1 2 2 2 4 S e S L .',
    '. 0 1 1 2 2 4 H S L L H',
    '. 1 0 1 1 2 3 4 S m S .',
    '. . 1 0 1 2 3 4 5 S . .',
    '. . . 0 . 1 2 4 @ . . .',
]
MARIA_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 3 4 3 2 . .',
    '. 1 2 3 3 4 4 3 3 2 .',
    '. 1 2 4 4 4 4 4 3 2 .',
    '. 1 4 k k q k k 4 1 .',
    '. 1 4 r B S B r 4 1 .',
    '. 0 4 L e S e s 4 0 .',
    '. 0 2 H S S n s 4 0 .',
    '. . 1 4 S m m S 4 . .',
    '. . . 2 4 S S 4 2 . .',
    '. . . . 3 5 @ 4 . . .',
]


def maria():
    """Maria Gorelowa (34): straight-backed, thin from the filtration months, the Western coat (thin plum
    heather wool, lapels) under the issued quilted vest, felt boots a size too big, hands wound in rags; a needle
    in the lapel.  Shovels coal at the coal stage (work_side)."""
    scene = 'c4p2_depot'
    mats, names = materials(scene, {
        'coat': ('#5C4858', {'texture': 'tweed'}),
        'vest': ('#3A3E34', {'bias': -0.04}),
        'trouser': '#2C2A2A',
        'boot': ('#5E5A52', {'texture': 'felt'}),
        'patch': '#4A3E46',
        'kerchief': ['#0C140C', '#1A2A18', '#2A4024', '#3C5632', '#526E42', '#6A8856'],
        'skin': ['#2A1C22', '#56383A', '#80564C', '#A87A64', '#C69C84', '#DEBEA6'],
        'hair': ['#0E0C0E', '#1C181A', '#2C2628', '#3C3436', '#4E4446', '#625656'],
        'eye': EYE_K,
        'rag': RAG,
        'steel': STEEL,
        'wood': '#4C3824',
        'coal': COAL,
        'needle': ['#3A3E42', '#6E7478', '#A4AAAE', '#CED4D6', '#E8ECEC', '#FFFFFF'],
        'thread': ['#3A0C0A', '#6A1812', '#9A2A1E', '#C03A2C', '#D85A44', '#EC8A70'],
        'breath': BREATH,
        'button': '#2A2428',
        'glass': GLASS,
        'hat': '#2C2A2A',
        'band': '#2A2A30',
    })
    lg = HD.base_legend(hat='kerchief', band=None)
    spec = Spec(id='maria', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=21.0, torso=12.6, neck=1.3, thigh=9.8, shin=9.6, uarm=7.0, farm=6.0,
                leg_r=(1.35, 1.2), arm_r=(1.45, 1.25), hip_f=1.6,
                coat=Coat(mat='coat', hem=-10.6, back=3.5, front=3.7, flare=0.8, chest=0.5, collar=1.0,
                          width_f=5.1, waist_f=4.1, hem_f=4.8, R=2.1, cyl=0.65, folds=0.5),
                heads=HD.head_views(lg, MARIA_SIDE, MARIA_FRONT, side_talk={(9, 7): 'M'},
                                    front_talk={(5, 8): 'M'}),
                boots=boot_bitmaps('boot', style='valenki'), hands=make_hands('rag', 'mitten'),
                lean=-0.6, stoop=0.0,
                style=dict(stride=4.8, swing=14.0, bob=1, walk_lean=1.5, lift=2.2, hem=0.6, idle_feet=(1.6, -1.6),
                           arm_n_idle=(3.0, 14.0), arm_f_idle=(-3.0, 12.0), gesture='press_back', work='shovel',
                           talk_front_arm='r', front_abd=5.0,
                           talk_n=[(4.0, 18.0), (8.0, 40.0), (14.0, 66.0), (16.0, 74.0), (14.0, 66.0), (8.0, 42.0),
                                   (10.0, 52.0), (4.0, 20.0)],
                           talk_hand_n=[None, None, 'open', 'open', None, None, 'open', None],
                           talk_head=[(0, 0), (0, 0), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('coat', maria_vest_side), ('coat', maria_needle_side), ('front', maria_shovel_side),
                           ('head', _puff)],
                  'front': [('coat', maria_vest_front), ('coat', maria_needle_front), ('head', _puff)]}
    return spec


def maria_vest_side(fr, J, P, spec):
    """The issued quilted vest over the thin coat: sleeveless, to the hip, quilted in rows; the coat's lapel and the
    needle show at the throat; coal dust on the coat skirt."""
    body = J['body']
    T = J['T']
    c = spec.coat
    pts = [body(-c.back - 0.7, T - 0.4), body(c.front + 0.6, T - 0.8), body(c.front + 0.9, -1.8),
           body(-c.back - 0.6, -1.8)]
    put_poly(fr, spec, pts, 'vest', R=1.9, cyl=0.6, name='vest')
    quilt_lines(fr, spec, J, 'vest', step=2, start=0, vmin=-1.8, vmax=T - 1.0)
    column_line(fr, spec, J, c.front - 0.2, -1.8, T - 1.2, 'vest', -0.8)
    # the plum coat's lapel above the vest opening, the needle catching the light in it
    put_poly(fr, spec, [body(c.front - 1.4, T + 0.6), body(c.front + 0.4, T - 0.2), body(c.front + 0.1, T - 2.6)],
             'coat', R=0.8, cyl=0.3, cast=False, name='lapel')
    # coal dust on the coat skirt (darker flecks on the lit side)
    for u, v in ((c.front - 0.4, -5.0), (c.front - 1.6, -7.5), (c.front - 0.8, -9.0), (-0.6, -6.2)):
        fr.recolor(*body(u, v), M(spec, 'coal'), 3)


def maria_needle_side(fr, J, P, spec):
    """The sewing needle in the lapel above the vest's opening: a short bright diagonal glint (the seamstress)."""
    x, y = J['body'](spec.coat.front - 0.2, J['T'] - 1.2)
    fr.recolor(x, y, M(spec, 'needle'), 5)
    fr.recolor(x - 1, y + 1, M(spec, 'needle'), 3)


def maria_needle_front(fr, J, P, spec):
    x, y = J['body'](-1.4, J['T'] - 1.6)
    fr.recolor(x, y, M(spec, 'needle'), 5)
    fr.recolor(x + 1, y + 1, M(spec, 'needle'), 3)


def maria_shovel_side(fr, J, P, spec):
    """The coal shovel of the work loop: from the far hand (gripping the shaft's end, drawn over the body) through
    the near hand to the blade, which follows the shaft (scooping low / carried / raised / tipped); coal on the
    blade while it is carried, thrown forward on the tip.  Every row: the rag wound round the near wrist shows as a
    pale band above the hand (the hands are wrapped in rags, not gloved)."""
    ex, ey = J['el_n']
    wx, wy = J['wr_n']
    fr.recolor(ex + (wx - ex) * 0.82, ey + (wy - ey) * 0.82, M(spec, 'rag'), 4)
    where = P.get('shovel')
    if not where:
        return
    fx, fy = J['wr_f']
    nx, ny = J['wr_n']
    dx, dy = nx - fx, ny - fy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    tip = (fx + ux * SHOVEL_LEN, fy + uy * SHOVEL_LEN)
    root = (fx + ux * (SHOVEL_LEN - 3.5), fy + uy * (SHOVEL_LEN - 3.5))
    put_line(fr, spec, (fx - ux * 1.0, fy - uy * 1.0), root, 0.5, 'wood', name='shaft', cast=True)
    put_line(fr, spec, root, tip, 1.5, 'steel', name='blade', cast=True)
    fr.recolor(tip[0] - ux * 0.6, tip[1] - uy * 0.6, M(spec, 'steel'), 5)          # the worn bright edge
    k = P.get('coal', 0)
    mx, my = (root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2
    if k == 1:
        put_bitmap(fr, bm(['cCc', 'occ'], COAL_LG, anchor=(1, 1)), spec.names, mx, my - 1.0, name='coal_load',
                   cast=False)
    elif k == 2:          # thrown: the coal leaves the tip up and forward
        put_bitmap(fr, bm(['.c.C', 'c.C.', '.c..'], COAL_LG, anchor=(0, 2)), spec.names, tip[0] - 1.0,
                   tip[1] - 1.0, name='coal_fly', cast=False)
    put_hand(fr, spec, 'fist', fx, fy, name='hand_f2')
    put_hand(fr, spec, 'fist', nx, ny, name='hand_n2')


def maria_vest_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.3)
    pts = [body(-4.9, T - 0.2), body(4.9, T - 0.2), body(4.7, -1.8), body(-4.7, -1.8)]
    put_poly(fr, spec, pts, 'vest', R=1.8, cyl=0.6, name='vest')
    quilt_lines(fr, spec, J, 'vest', step=2, start=0, vmin=-1.8, vmax=T - 1.0, light=spec.light_front.key)
    # the vest's opening: the plum coat with its lapels and the needle
    put_poly(fr, spec, [body(-1.8, T + 0.5), body(1.8, T + 0.5), body(0.6, T - 4.6), body(-0.6, T - 4.6)],
             'coat', R=0.9, cyl=0.3, cast=False, name='coat_v')
    lapels_front(fr, spec, J, depth=3.6, width=1.9)
    column_line(fr, spec, J, 0.0, -10.0, -2.2, 'coat', -0.8)
    for u, v in ((2.0, -5.0), (-2.6, -7.4), (1.2, -9.0)):
        fr.recolor(*body(u, v), M(spec, 'coal'), 3)


# =================================================================================== HANNA
# bareheaded: dark-blonde hair pinned up in a round knot HIGH on the crown (a dark pin band under it), a strand at
# the nape; a round, open face (full cheek, a soft chin), the Adler blue-grey eyes, a mouth about to say something
# ironic.  Round 10 review: nothing of Elena (dark low chignon, wine scarf high at the throat, long slim coat).
HANNA_SIDE = [
    '. . . h K J J h . . . .',
    '. . . k h K J k j . . .',
    '. . K h K h h K K j j .',
    '. K J K h h K K j j s .',
    '. K h K h h K j s S L .',
    '. . k h h h j S B S L .',
    '. . . h h h r S S e L .',
    '. . . l h h S s S S L H',
    '. . . l . h r S S m S .',
    '. . . . . . r s S S . .',
    '. . . . . . . s @ . . .',
]
HANNA_FRONT = [
    '. . . h K J K h . . .',
    '. . . k h K h k . . .',
    '. . h K K j K K h . .',
    '. h K K j s j K K h .',
    '. h K s S S S s K h .',
    '. . h r B S B r h . .',
    '. . j L e S e s j . .',
    '. . . L S S n s . . .',
    '. . . s S m m S . . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def hanna():
    """Hanna Adler (27): upright like her brother, but looser in the shoulders and quicker; a knee-length navy
    swing coat open at the throat over the grey cardigan, a grey-brown tweed skirt below it, dark wool stockings,
    laced ankle boots; the rust-red scarf thrown on loosely with both long ends down the front; chalk on the near
    sleeve and on the coat where she wiped her hand; the key ring."""
    scene = 'c4p2_court'
    mats, names = materials(scene, {
        'coat': ('#2C3E7A', {'bias': 0.06}),          # a clear wool blue: not Marta's grey-navy uniform
        'cardigan': ('#6A6A6C', {'texture': 'knit'}),
        'skirt': ('#5C5248', {'texture': 'tweed'}),
        'trouser': '#2E2624',
        'boot': ('#1E1A1A', {'glossy': True}),
        'patch': '#34364A',
        'scarf': ('#8E3C22', {'texture': 'knit'}),
        'chalk': ['#46506E', '#5C6684', '#76809A', '#9098AE', '#AAB0C0', '#C6CAD4'],     # chalk dust on navy
        'keys': KEYS,
        'skin': SKIN['berlin'],
        'hair': ['#22190F', '#3E301E', '#5C4A2E', '#7A6440', '#968054', '#B09A6A'],
        'eye': EYE_B,
        'button': '#141826',
        'glass': GLASS,
        'hat': '#22242E',
        'band': '#2A2A30',
        'breath': BREATH,
    })
    lg = HD.base_legend()
    spec = Spec(id='hanna', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=21.4, torso=12.6, neck=1.6, thigh=10.0, shin=9.8, uarm=7.0, farm=6.0,
                leg_r=(1.25, 1.05), arm_r=(1.4, 1.2), hip_f=1.5,
                coat=Coat(mat='coat', hem=-9.2, back=3.4, front=3.8, flare=2.4, chest=0.8, collar=1.6,
                          width_f=5.0, waist_f=3.7, hem_f=6.4, R=2.1, cyl=0.65, folds=0.6),
                skirt=Skirt(mat='skirt', top=-3.0, hem=-13.4, back=3.0, front=3.2, flare=1.4, hem_f=4.6,
                            waist_f=3.8, folds=0.4),
                heads=HD.head_views(lg, HANNA_SIDE, HANNA_FRONT, side_talk={(9, 8): 'M'}, front_talk={(5, 8): 'M'}),
                boots=ladies_boots('boot'), hands=make_hands('skin'), lean=-1.0,
                style=dict(stride=5.4, swing=20.0, bob=1, walk_lean=1.5, lift=2.8, hem=1.0, idle_feet=(1.8, -1.4),
                           arm_n_idle=(3.0, 16.0), arm_f_idle=(-5.0, 12.0), gesture='find_key',
                           talk_front_arm='r', front_abd=6.0,
                           talk_n=[(6.0, 24.0), (14.0, 62.0), (20.0, 92.0), (24.0, 104.0), (20.0, 94.0), (12.0, 58.0),
                                   (18.0, 82.0), (6.0, 28.0)],
                           talk_hand_n=TALK_HANDS,
                           talk_f=[(-5.0, 12.0), (-4.0, 18.0), (-2.0, 30.0), (0.0, 40.0), (-2.0, 30.0), (-4.0, 18.0),
                                   (-3.0, 24.0), (-5.0, 12.0)],
                           talk_head=[(0, 0), (0, 0), (0, -1), (0, 0), (0, 0), (0, 0), (0, 1), (0, 0)]))
    spec.hooks = {'side': [('coat', hanna_coat_side), ('front', hanna_keys_side), ('front', hanna_chalk_side),
                           ('head', _puff)],
                  'front': [('coat', hanna_coat_front), ('arms', hanna_arms_front), ('head', _puff)]}
    return spec


SCARF_RUST = {'o': ('scarf', 0), 'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4),
              'e': ('scarf', 5)}
CHALK_LG = {'a': ('chalk', 2), 'b': ('chalk', 3), 'c': ('chalk', 4), 'd': ('chalk', 5)}


def hanna_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    # the coat open at the throat: the grey cardigan in the opening, the coat's edge and buttons below
    put_poly(fr, spec, [body(c.front - 1.6, T + 0.4), body(c.front + 0.2, T - 0.6), body(c.front + 0.2, T - 4.4),
                        body(c.front - 0.9, T - 4.0)], 'cardigan', R=0.9, cyl=0.3, cast=False, name='cardigan_v')
    column_line(fr, spec, J, c.front - 0.8, c.hem, T - 4.4, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 0.8, (T - 5.4, T - 8.6, -0.6, -4.2), tone=1)
    flap(fr, spec, J, c.front - 3.4, c.front - 1.8, -2.4, 'coat')
    # the rust-red scarf: a loose loop round the neck and BOTH long ends down the front (they swing behind a step)
    x, y = body(-0.2, T + 1.4)
    put_bitmap(fr, bm(['.bccdc.', 'bccddcc', 'obccddc'], SCARF_RUST, anchor=(3, 0)), spec.names, x, y,
               name='scarf')
    sl = lag_dx(P, 1.0) if walking(P) else 0
    ex, ey = body(c.front - 0.9, T - 0.6)
    ends = bm(['dc', 'dc', 'cb', 'dc', 'cb', 'dc', 'cb', 'cb', 'ba', 'ao'], SCARF_RUST, anchor=(1, 0))
    put_bitmap(fr, ends, spec.names, ex + sl, ey, name='scarf_ends')


def hanna_keys_side(fr, J, P, spec):
    """The key ring in the near hand: two or three keys glint below the fist; spread when she finds the key."""
    x, y = J['wr_n']
    k = P.get('keys', 0)
    rows = {0: ['.o.', 'kKr', '.k.'], 1: ['o..', 'kKk', 'r.K'], 2: ['.o.', 'Kkr', 'k.K']}[k]
    put_bitmap(fr, bm(rows, KEYS_LG, anchor=(1, 0)), spec.names, x + 0.4, y + 0.4, name='keys', cast=False)
    put_hand(fr, spec, 'fist', x, y - 0.2, name='hand_n2')


def hanna_chalk_side(fr, J, P, spec):
    """Chalk dust from the afternoon's blackboard (drawn over the near arm): a dusty streak along the cuff and the
    forearm, a touch on the upper arm, and where she wiped her hand on the coat at the hip."""
    body = J['body']
    c = spec.coat
    ex, ey = J['el_n']
    x, y = J['wr_n']
    sx, sy = J['sh_n']
    for t, tone in ((0.45, 2), (0.60, 3), (0.75, 3), (0.90, 2)):
        fr.recolor(ex + (x - ex) * t, ey + (y - ey) * t, M(spec, 'chalk'), tone)
    fr.recolor(sx + (ex - sx) * 0.7, sy + (ey - sy) * 0.7, M(spec, 'chalk'), 2)
    for u, v, t in ((c.front - 1.6, -3.8, 2), (c.front - 1.0, -4.6, 1), (c.front - 2.2, -4.6, 0)):
        fr.recolor(*body(u, v), M(spec, 'chalk'), t)


def hanna_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.3)
    put_poly(fr, spec, [body(-1.7, T + 0.6), body(1.7, T + 0.6), body(0.5, T - 4.4), body(-0.5, T - 4.4)],
             'cardigan', R=0.9, cyl=0.3, cast=False, name='cardigan_v')
    lapels_front(fr, spec, J, depth=4.0, width=2.4)
    column_line(fr, spec, J, 0.6, spec.coat.hem, T - 4.6, 'coat', -0.8)
    buttons(fr, spec, J, 1.4, (T - 5.4, T - 8.6, -0.6, -4.2), tone=1)
    for u, v, t in ((-2.8, -3.8, 2), (-2.2, -4.6, 1), (-3.4, -4.6, 0)):
        fr.recolor(*body(u, v), M(spec, 'chalk'), t)
    x, y = body(0.0, T + 1.6)
    sc = bm(['.bccdcc.', 'obccddcb', '.dc..dc.', '.dc..cb.', '.cb..dc.', '.dc..cb.', '.cb..dc.', '.dc..cb.',
             '.ba..ba.', '.a....o.'], SCARF_RUST, anchor=(4, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


def hanna_arms_front(fr, J, P, spec):
    x, y = J['wr_r']
    put_bitmap(fr, bm(['.o', 'kK', 'r.'], KEYS_LG, anchor=(0, 0)), spec.names, x, y + 1.0, name='keys', cast=False)
    ex, ey = J['el_l']
    wx, wy = J['wr_l']
    for t, tone in ((0.35, 2), (0.65, 3), (0.9, 2)):
        fr.recolor(ex + (wx - ex) * t, ey + (wy - ey) * t, M(spec, 'chalk'), tone)


# =================================================================================== WENDT
# a PEARL-GREY homburg with a black band (Kessler's is black: the value is inverted on purpose), dark hair with grey
# temples (T), heavy lids (the brow row sits low on the eye), a broad clean-shaven face, soft jowls and a double
# chin over the collar
WENDT_SIDE = [
    '. . . . 1 2 3 3 3 . . .',
    '. . . 1 2 3 4 4 4 4 . .',
    '. . . 1 2 3 4 4 4 5 . .',
    '. . . u u v v V V V . .',
    'R 1 2 2 3 3 4 4 4 5 5 4',
    '. . . k T r s B B L . .',
    '. . . k T s S e S L . .',
    '. . . . r S S S L L H .',
    '. . . . r s S S m S . .',
    '. . . . s S S S S . . .',
    '. . . . r s S S s . . .',
    '. . . . . . s @ . . . .',
]
WENDT_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 4 4 3 2 . .',
    '. . 1 2 3 4 4 4 3 . .',
    '. . u u v V V v u . .',
    'R 1 2 3 4 4 4 4 3 2 1',
    '. . T r B S B r T . .',
    '. . T L e S e s T . .',
    '. . r L S S n s r . .',
    '. . r s S m m S r . .',
    '. . . r S S S S r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def wendt():
    """Kommissar Wendt (about 50): heavy, broad and calm -- the long dark grey civilian coat with a wide dark-brown
    fur shawl collar lying over his shoulders and down the front, a bottle-green silk foulard in the opening (no
    white collar, no tie), the pearl-grey homburg, black leather gloves, the small notebook (its pale page edge
    catches the light) in the near hand.  Moves slowly, gestures little."""
    scene = 'c4p2_court'
    mats, names = materials(scene, {
        'coat': ('#3C3E44', {'bias': 0.05}),
        'trouser': '#26282C',
        'boot': ('#121214', {'glossy': True}),
        'patch': '#2E2E34',
        'fur': (['#0A0705', '#160F0A', '#24180F', '#342317', '#463020', '#5A3F2A'], {'texture': 'fur'}),
        'hat': ['#3E4044', '#5A5C60', '#76787A', '#929492', '#AEAEA8', '#C6C4BC'],
        'band': ['#050506', '#0A0A0C', '#121216', '#1A1A20', '#24242C', '#30303A'],
        'glove': ('#141214', {'glossy': True}),
        'book': ['#0C0A0A', '#1E1616', '#30201E', '#422C28', '#583A34', '#6E4C44'],
        'paper': PAPER_W,
        'silk': ['#06140E', '#0C2418', '#143424', '#1E4632', '#2A5A42', '#3A7056'],
        'dot': '#D8D0B4',
        'skin': SKIN['berlin'],
        'hair': ['#0C0A0A', '#161212', '#201A18', '#2A2220', '#342A26', '#40342E'],
        'temple': GREY_HAIR,
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#16161A',
    })
    lg = HD.base_legend()
    lg.update({'T': ('temple', 3)})
    spec = Spec(id='wendt', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=22.0, torso=14.0, neck=1.0, thigh=10.2, shin=10.4, uarm=7.4, farm=6.4,
                leg_r=(1.95, 1.75), arm_r=(1.85, 1.6), hip_f=2.2,
                coat=Coat(mat='coat', hem=-14.0, back=4.9, front=5.6, flare=1.0, chest=1.6, collar=1.4,
                          width_f=6.6, waist_f=6.2, hem_f=6.6, R=2.6, cyl=0.7, folds=0.8),
                heads=HD.head_views(lg, WENDT_SIDE, WENDT_FRONT, side_talk={(8, 8): 'M'}, front_talk={(5, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('glove', kind='glove'), lean=-1.4,
                style=dict(stride=4.2, swing=7.0, bob=1, walk_lean=0.2, lift=2.0, hem=0.5, idle_feet=(1.6, -1.6),
                           hold_n=(4.0, 22.0), arm_f_idle=(-6.0, 14.0), gesture='note_word',
                           front_l=(3.0, 0.2, 10.0), talk_front_arm='r', front_abd=4.0,
                           talk_f=[(-6.0, 14.0), (-4.0, 30.0), (0.0, 56.0), (2.0, 66.0), (0.0, 58.0), (-3.0, 34.0),
                                   (-1.0, 46.0), (-6.0, 16.0)],
                           talk_hand_f=[None, None, 'open', 'open', 'open', None, None, None],
                           talk_head=[(0, 0), (0, 0), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('coat', wendt_coat_side), ('head', wendt_collar_side), ('front', wendt_note_side)],
                  'front': [('coat', wendt_coat_front), ('head', wendt_collar_front), ('arms', wendt_note_front)]}
    return spec


FUR_LG = {'o': ('fur', 0), 'a': ('fur', 1), 'b': ('fur', 2), 'c': ('fur', 3), 'd': ('fur', 4), 'e': ('fur', 5)}


def wendt_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    # the bottle-green foulard in the opening (an ivory dot catches the light)
    pts = [body(c.front - 1.8, T + 0.4), body(c.front - 0.2, T - 0.6), body(c.front - 0.3, T - 2.6),
           body(c.front - 1.5, T - 2.4)]
    put_poly(fr, spec, pts, 'silk', R=1.0, cyl=0.3, cast=False, name='foulard')
    fr.recolor(*body(c.front - 0.8, T - 1.4), M(spec, 'dot'), 4)
    column_line(fr, spec, J, c.front - 1.2, -14.0, T - 3.0, 'coat', -0.6)
    buttons(fr, spec, J, c.front - 1.2, (T - 5.0, T - 8.6, -0.6, -4.2), tone=1)
    flap(fr, spec, J, c.front - 4.0, c.front - 2.0, -1.8, 'coat')
    column_line(fr, spec, J, -c.back + 1.2, -14.0, -2.0, 'coat', -0.5)        # the back vent


def wendt_collar_side(fr, J, P, spec):
    """The wide dark-brown fur shawl collar: round the back of the neck, lying broad over the shoulder and running
    down the coat's front edge as a fur lapel (drawn after the head, before the near arm)."""
    body = J['body']
    T = J['T']
    c = spec.coat
    put_poly(fr, spec, [body(-c.back - 0.8, T + 0.4), body(-1.2, T + 2.4), body(c.front - 0.2, T + 1.2),
                        body(c.front + 0.5, T - 1.2), body(c.front - 0.1, T - 5.6), body(c.front - 1.8, T - 5.2),
                        body(c.front - 2.0, T - 1.4), body(-c.back + 0.2, T - 1.6)], 'fur', R=1.6, cyl=0.6,
             name='fur_collar')


def wendt_note_side(fr, J, P, spec):
    """The small black notebook in the gloved near hand: its pale page edge shows when closed; open (white pages)
    while he notes something."""
    x, y = J['wr_n']
    if P.get('note'):
        nb = bm(['oPq', 'lPP', 'oPp'], NOTE_LG, anchor=(1, 1))
    else:
        nb = bm(['oOP', 'oOP', 'oOp'], NOTE_LG, anchor=(0, 1))
    put_bitmap(fr, nb, spec.names, x + 0.8, y - 0.2, name='notebook')
    put_hand(fr, spec, 'fist', x + 0.1, y - 0.2, name='hand_n2')


def wendt_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.4)
    pts = [body(-1.6, T + 0.6), body(1.6, T + 0.6), body(0.8, T - 3.4), body(-0.8, T - 3.4)]
    put_poly(fr, spec, pts, 'silk', R=0.8, cyl=0.3, cast=False, name='foulard')
    for u, v in ((-0.4, T - 0.8), (0.6, T - 2.2)):
        fr.recolor(*body(u, v), M(spec, 'dot'), 4)
    column_line(fr, spec, J, 0.7, -14.0, T - 3.6, 'coat', -0.8)
    buttons(fr, spec, J, 1.9, (T - 5.0, T - 8.6, -0.6, -4.2), tone=1)
    flap(fr, spec, J, -5.2, -3.0, -1.8, 'coat')
    flap(fr, spec, J, 3.0, 5.2, -1.8, 'coat')


def wendt_collar_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    for sgn in (-1, 1):
        put_poly(fr, spec, [body(sgn * 1.6, T + 2.0), body(sgn * 6.6, T + 0.8), body(sgn * 6.4, T - 1.8),
                            body(sgn * 2.6, T - 5.4), body(sgn * 1.2, T - 4.8), body(sgn * 1.0, T - 0.6)], 'fur',
                 R=1.4, cyl=0.6, name='fur_collar')


def wendt_note_front(fr, J, P, spec):
    x, y = J['wr_l']
    put_bitmap(fr, bm(['oOP', 'oOP'], NOTE_LG, anchor=(1, 0)), spec.names, x + 0.3, y + 0.4, name='notebook')
    put_hand(fr, spec, 'front_l', x, y + 0.2, name='hand_l2')


# =================================================================================== BLOCKWART (Kuhnert)
BOX_UNDER_ARM = (2.0, 26.0)        # the near arm pressing the card box to his side (the box lies under it)
# a flat cap drawn forward over a short peak (y = the peak's shadow), grey hair at the temple, a lined, pinched
# face with grey stubble
BLOCKWART_SIDE = [
    '. . . . 1 2 3 3 3 . . .',
    '. . . 1 2 3 3 4 4 4 . .',
    '. . 1 2 2 3 3 3 4 4 4 .',
    '. . 0 1 1 2 2 2 3 y y y',
    '. . . K h r s B S L . .',
    '. . . K h s S e S L . .',
    '. . . . h s r S L L H .',
    '. . . . r s r S m S . .',
    '. . . . . r s S S . . .',
    '. . . . . . s @ . . . .',
]
BLOCKWART_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 3 3 3 2 . .',
    '. 1 2 3 3 4 4 3 3 2 .',
    '. 0 y y y y y y y 0 .',
    '. . K r B S B r K . .',
    '. . K L e S e s K . .',
    '. . . L r S n r . . .',
    '. . . s r m m r r . .',
    '. . . . r S S r . . .',
    '. . . . . s @ . . . .',
]


def blockwart(hist: bool = False):
    """Erwin Kuhnert (about 60): a little stooped, quick short steps, the brown work coat buttoned over the
    cardigan, the flat cap, reading glasses dangling on their string, the big key ring at the belt, the beech card
    box carried on the far forearm.  hist=True: the armband (sheet_hist.png only, §12.4)."""
    scene = 'c4p2_court'
    mats, names = materials(scene, {
        'coat': ('#5E4630', {'bias': 0.02}),
        'cardigan': ('#4A4C3E', {'texture': 'knit'}),
        'trouser': '#2E2C2A',
        'boot': ('#4E4A44', {'texture': 'felt'}),
        'galosh': ('#101012', {'glossy': True}),
        'patch': '#4A3A2A',
        'hat': (['#16130F', '#26221C', '#36302A', '#48413A', '#5C544A', '#706858'], {'texture': 'tweed'}),
        'band': ['#0A0908', '#14120F', '#1E1B17', '#29251F', '#36302A', '#443C34'],
        'skin': SKIN['old'],
        'hair': GREY_HAIR,
        'eye': EYE_B,
        'glass': GLASS,
        'string': '#2A2622',
        'keys': KEYS,
        'box': WOOD_BOX,
        'paper': PAPER_W,
        'belt': ('#1E1A16', {'glossy': True}),
        'metal': '#8A8676',
        'button': '#2A2016',
        'armband': '#9A2A22' if hist else '#5E4630',
        'emblem': ['#0E0E10', '#1A1A1E', '#2A2A2E', '#C8C8C0', '#E2E2DA', '#F2F2EA'],
    })
    lg = HD.base_legend()
    spec = Spec(id='blockwart', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=20.8, torso=13.0, neck=1.2, thigh=9.6, shin=9.6, uarm=7.0, farm=6.0,
                leg_r=(1.45, 1.3), arm_r=(1.5, 1.3), hip_f=1.7,
                coat=Coat(mat='coat', hem=-9.6, back=3.9, front=4.4, flare=0.7, chest=0.4, collar=0.9,
                          width_f=5.4, waist_f=5.0, hem_f=5.2, R=2.2, cyl=0.65, folds=0.4, hunch=0.6),
                heads=HD.head_views(lg, BLOCKWART_SIDE, BLOCKWART_FRONT, side_talk={(8, 7): 'M'},
                                    front_talk={(5, 7): 'M'}),
                boots=boot_bitmaps('boot', sole='galosh', style='shoe'), hands=make_hands('skin'),
                lean=2.0, stoop=6.0, head_off=(0.6, -0.2),
                style=dict(stride=4.0, swing=12.0, bob=1, walk_lean=2.5, lift=1.8, hem=0.4, idle_feet=(1.2, -1.2),
                           hold_n=BOX_UNDER_ARM, arm_n_idle=BOX_UNDER_ARM, arm_f_idle=(-4.0, 12.0),
                           gesture='tug_cap_f', work='cards', front_l=(16.0, 0.0, 34.0), talk_front_arm='r',
                           front_abd=5.0,
                           talk_f=[(-4.0, 12.0), (-1.0, 30.0), (4.0, 58.0), (6.0, 70.0), (4.0, 62.0), (0.0, 40.0),
                                   (3.0, 52.0), (-4.0, 14.0)],
                           talk_hand_f=[None, None, 'open', 'open', 'open', None, 'open', None],
                           talk_head=[(0, 0), (0, 1), (0, 0), (0, 0), (0, 1), (0, 0), (0, 0), (0, 0)]))
    spec.hooks = {'side': [('coat', blockwart_coat_side), ('head', blockwart_box_side),
                           ('front', blockwart_armband_side), ('front', blockwart_cards_side)],
                  'front': [('coat', blockwart_coat_front), ('coat', blockwart_box_front),
                            ('arms', blockwart_armband_front)]}
    spec.hist = hist
    return spec


def blockwart_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    put_poly(fr, spec, [body(c.front - 1.4, T + 0.4), body(c.front + 0.1, T - 0.4), body(c.front - 0.2, T - 2.4)],
             'cardigan', R=0.8, cyl=0.3, cast=False, name='cardigan_v')
    column_line(fr, spec, J, c.front - 1.0, -9.6, T - 2.0, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 1.0, (T - 3.0, T - 6.0, -0.4, -4.4), tone=1)
    flap(fr, spec, J, c.front - 3.4, c.front - 1.8, -2.6, 'coat')
    belt_side(fr, spec, J, 1.6, 'belt', buckle='metal')
    # the big key ring at the near hip (it swings when he walks) and the reading glasses on their string
    sw = 1 if walking(P) and P.get('phase', 0) in (1, 2, 5, 6) else 0
    kx, ky = body(c.front - 1.6, 0.8)
    put_bitmap(fr, bm(['.o.', 'kKk', 'rkK', '.r.'], KEYS_LG, anchor=(1, 0)), spec.names, kx - sw, ky,
               name='key_ring', cast=False)
    put_line(fr, spec, body(c.front - 1.6, T + 0.4), body(c.front - 0.4, T - 3.4), 0.3, 'string', tone=1,
             name='string')
    gx, gy = body(c.front - 0.2, T - 3.8)
    fr.recolor(gx, gy, M(spec, 'glass'), 4)
    fr.recolor(gx + 1, gy, M(spec, 'glass'), 2)


def blockwart_box_side(fr, J, P, spec):
    """The beech card box (drawn after the body, before the near arm).  Every row but the work loop: clamped UNDER
    THE NEAR ARM against the hip -- the upper arm presses it to his side, the forearm runs under it, the hand holds
    its front end, so the arm lies over it.  The work loop: held open against the belly on the far forearm, close
    to the coat, the cards' tops showing; P['cards'] = which card is pulled."""
    k = P.get('cards', -1)
    if k >= 0:
        x, y = J['wr_f']
        top = ['.pP.q.', '.PpqP.', 'pqPPp.'][k]
        box = bm([top, 'eddddc', 'cbbbba', 'obaaao'], BOX_LG, anchor=(4, 2))
        put_bitmap(fr, box, spec.names, x + 0.4, y - 0.4, name='card_box')
        put_hand(fr, spec, 'fist', x + 0.8, y + 0.2, name='hand_f2')
        return
    if P.get('arm_n') != spec.style.get('hold_n'):
        return
    ex, ey = J['el_n']
    box = bm(['edddddc', 'cbbbbba', 'cbbbbba', 'obaaaao'], BOX_LG, anchor=(3, 3))
    put_bitmap(fr, box, spec.names, ex + 0.6, ey + 0.6, name='card_box')


def blockwart_cards_side(fr, J, P, spec):
    """In the work loop the near hand holds the pulled card up to the eyes."""
    if P.get('cards') == 2:
        x, y = J['wr_n']
        put_bitmap(fr, bm(['qP', 'Pp', 'pP'], BOX_LG, anchor=(0, 2)), spec.names, x + 0.6, y - 0.6, name='card',
                   cast=False)


def _armband(fr, spec, sh, el, r):
    """Hist variant only: the band round the upper arm with the white disc and a dark mark (2 px, as the guard's
    hist band in chargen_cast).  The neutral sheet draws nothing."""
    if not getattr(spec, 'hist', False):
        return
    from chargen_core import capsule
    a = (sh[0] + (el[0] - sh[0]) * 0.40, sh[1] + (el[1] - sh[1]) * 0.40)
    b = (sh[0] + (el[0] - sh[0]) * 0.60, sh[1] + (el[1] - sh[1]) * 0.60)
    m, x0, y0, n = capsule(a, b, max(0.6, r - 0.35))
    fr.put(m, x0, y0, M(spec, 'armband'), n, name='armband', cast=False)
    ex, ey = (a[0] + b[0]) / 2 - 0.2, (a[1] + b[1]) / 2 - 0.5
    for x, t in ((ex, 4), (ex + 1, 1)):          # only on the sleeve: the hist sheet keeps the neutral alpha
        xi, yi = int(math.floor(x)), int(math.floor(ey))
        if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] >= 0:
            fr.px(x, ey, M(spec, 'emblem'), t)


def blockwart_armband_side(fr, J, P, spec):
    _armband(fr, spec, J['sh_n'], J['el_n'], spec.arm_r[0])


def blockwart_armband_front(fr, J, P, spec):
    _armband(fr, spec, J['sh_r'], J['el_r'], spec.arm_r[0])


def blockwart_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    calm_front_hem(fr, spec, J, amount=-0.3)
    put_poly(fr, spec, [body(-1.6, T + 0.5), body(1.6, T + 0.5), body(0.5, T - 2.6), body(-0.5, T - 2.6)],
             'cardigan', R=0.8, cyl=0.3, cast=False, name='cardigan_v')
    column_line(fr, spec, J, 0.5, -9.6, T - 2.6, 'coat', -0.8)
    buttons(fr, spec, J, 1.3, (T - 3.0, T - 6.0, -0.4, -4.4), tone=1)
    flap(fr, spec, J, -4.4, -2.6, -2.6, 'coat')
    flap(fr, spec, J, 2.6, 4.4, -2.6, 'coat')
    belt_front(fr, spec, J, 1.6, 'belt', buckle='metal')
    put_line(fr, spec, body(-1.4, T + 0.4), body(-0.6, T - 3.6), 0.3, 'string', tone=1, name='string')
    put_line(fr, spec, body(1.4, T + 0.4), body(0.6, T - 3.6), 0.3, 'string', tone=1, name='string2')
    gx, gy = body(-0.6, T - 3.9)
    for dx_, t in ((0, 4), (1, 2), (2, 4)):
        fr.recolor(gx + dx_, gy, M(spec, 'glass'), t)
    put_bitmap(fr, bm(['.o', 'kK', 'rk'], KEYS_LG, anchor=(0, 0)), spec.names, *body(3.6, 1.0), name='key_ring',
               cast=False)


def blockwart_box_front(fr, J, P, spec):
    """Front view: the box's end under the left arm at the hip, sticking out past the coat (drawn before the arms,
    so the arm lies over it)."""
    body = J['body']
    x, y = body(-spec.coat.width_f - 0.4, 1.6)
    put_bitmap(fr, bm(['edc', 'cba', 'cba', 'oao'], BOX_LG, anchor=(1, 0)), spec.names, x, y, name='card_box')


# =================================================================================== GUARD_KARSK (life sheet)
# ushanka with the flaps tied up on the crown (the tie = 5), a young face with cold-red cheeks; hist: the small red
# star on the front of the fur (Z)
GUARD_K_SIDE = [
    '. . . . 1 2 3 3 . . . .',
    '. . . 1 2 3 5 4 4 . . .',
    '. . 1 2 3 3 4 4 4 4 . .',
    '. . 1 2 2 3 3 3 3 Z 2 .',
    '. . . k k r s B S L . .',
    '. . . k h S S e S L . .',
    '. . . . h s c S L L H .',
    '. . . . r s S S m S . .',
    '. . . . . r s S S . . .',
    '. . . . . . s @ . . . .',
]


def guard_karsk(hist: bool = False):
    """A young Soviet guard at the coal stage: the long sheepskin coat (fleece at collar, cuffs and hem), belted,
    the ushanka's flaps tied up, felt boots, the rifle slung on his back.  Warms his hands at the barrel fire."""
    scene = 'c4p2_depot'
    mats, names = materials(scene, {
        'coat': (['#2C2014', '#4A3622', '#6A4E32', '#866642', '#A07E54', '#B89668'], {'texture': 'felt'}),
        'fleece': (FLEECE, {'texture': 'fur'}),
        'trouser': '#2E3028',
        'boot': ('#4E4A42', {'texture': 'felt'}),
        'patch': '#5A4632',
        'hat': (['#16120E', '#28201A', '#3A3026', '#4C4034', '#5E5244', '#726656'], {'texture': 'fur'}),
        'star': ['#5A0E0A', '#8A1A12', '#B8261A', '#D63A26', '#EE5A3E', '#FF8A66'] if hist
        else ['#16120E', '#28201A', '#3A3026', '#4C4034', '#5E5244', '#726656'],
        'belt': ('#2A1E14', {'glossy': True}),
        'metal': '#8A8C80',
        'rifle': ['#120E0A', '#22180E', '#3A2814', '#54381C', '#6E4A26', '#865E34'],
        'steel': STEEL,
        'mitten': ('#5C5446', {'texture': 'felt'}),
        'skin': SKIN['ruddy'],
        'cheek': ['#3A1A1C', '#6A2C2E', '#9A4440', '#C46454', '#DA8670', '#ECAE96'],
        'hair': '#3A2C20',
        'eye': EYE_K,
        'glass': GLASS,
        'button': '#22180E',
        'band': '#2A2A30',
        'breath': BREATH,
    })
    lg = HD.base_legend()
    lg.update({'Z': ('star', 3, 'f'), 'c': ('cheek', 3, 'f')})
    spec = Spec(id='guard_karsk', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=22.0, torso=13.4, neck=1.2, thigh=10.2, shin=10.0,
                leg_r=(1.6, 1.45), arm_r=(1.85, 1.6), hip_f=1.9,
                coat=Coat(mat='coat', hem=-14.5, back=4.6, front=4.6, flare=2.0, chest=0.8, collar=1.6,
                          width_f=6.2, waist_f=4.6, hem_f=6.4, R=2.5, cyl=0.65, folds=0.9),
                heads=HD.head_views(lg, GUARD_K_SIDE, None, side_talk={(8, 7): 'M'}),
                boots=boot_bitmaps('boot', style='valenki'), hands=make_hands('mitten', 'mitten'), lean=0.5,
                style=dict(stride=5.0, swing=16.0, bob=1, walk_lean=1.5, lift=2.4, hem=0.8, idle_feet=(1.8, -1.8),
                           arm_n_idle=(2.0, 12.0), arm_f_idle=(-2.0, 10.0), gesture='blow_hands', work='warm',
                           talk_n=[(4.0, 16.0), (8.0, 36.0), (12.0, 54.0), (14.0, 60.0), (12.0, 54.0), (8.0, 36.0),
                                   (10.0, 44.0), (4.0, 18.0)],
                           talk_hand_n=['fist'] * 8))
    spec.hooks = {'side': [('back0', guard_rifle_side), ('coat', guard_coat_side), ('head', _puff)]}
    spec.hist = hist
    return spec


FLEECE_LG = {'a': ('fleece', 2), 'b': ('fleece', 3), 'c': ('fleece', 4), 'd': ('fleece', 5)}


def guard_rifle_side(fr, J, P, spec):
    """The rifle slung on his back, muzzle up: the barrel (dark steel, a lit edge and the front sight at the
    muzzle) stands clear BEHIND the ushanka (the head no longer hides it), the wooden stock runs down behind the
    back to the hip, the butt shows below the coat's back edge; the sling crosses the chest (guard_coat_side).
    Drawn first (back0): the coat and the head lie over the parts in front of it."""
    body = J['body']
    T = J['T']
    b = spec.coat.back
    butt = body(-b - 1.2, -7.0)
    grip = body(-b - 1.8, T - 2.0)
    muzzle = body(-b - 3.6, T + 11.0)
    put_line(fr, spec, butt, grip, 1.15, 'rifle', name='stock', cast=True)
    put_line(fr, spec, grip, muzzle, 0.62, 'steel', tone=1, name='barrel', cast=True)
    # the lit edge along the barrel (one px beside the dark core) and the front sight at the muzzle
    for k in range(11):
        t = k / 10.0
        x = grip[0] + (muzzle[0] - grip[0]) * t + 1.0
        y = grip[1] + (muzzle[1] - grip[1]) * t
        fr.px(x, y, M(spec, 'steel'), 4 if k % 3 else 3)
    fr.px(muzzle[0] + 0.5, muzzle[1] - 1.0, M(spec, 'steel'), 5)
    # the butt plate and the lit top edge of the stock
    fr.px(butt[0], butt[1] + 0.6, M(spec, 'steel'), 2)
    for t in (0.25, 0.5, 0.75):
        fr.px(butt[0] + (grip[0] - butt[0]) * t - 0.8, butt[1] + (grip[1] - butt[1]) * t, M(spec, 'rifle'), 5)


def guard_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    belt_side(fr, spec, J, 2.2, 'belt', buckle='metal')
    column_line(fr, spec, J, c.front - 0.6, -14.0, T - 2.0, 'coat', -0.7)
    # fleece: the big turned-down collar and the open front edge, the hem
    put_poly(fr, spec, [body(-c.back + 0.2, T + 0.8), body(c.front - 0.2, T + 1.0), body(c.front + 0.3, T - 1.8),
                        body(-c.back + 0.6, T - 1.4)], 'fleece', R=1.4, cyl=0.6, name='collar')
    for v in range(-14, int(T - 2), 2):
        fr.recolor(*body(c.front - 0.2, v), M(spec, 'fleece'), 3 if v % 4 else 4)
    put_line(fr, spec, body(-c.back - 0.6, -14.0), body(c.front + 0.9, -14.0), 0.7, 'fleece', name='hem_fleece')
    put_line(fr, spec, body(c.front - 1.4, T - 0.2), body(-0.4, -2.0), 0.35, 'belt', tone=1, name='sling')


# =================================================================================== PRESS_OFFICER (life sheet)
# a karakul pirozhok (curly grey fur, low and flat), round glasses, a smooth, careful face
PRESS_SIDE = [
    '. . . 1 3 2 3 2 3 . . .',
    '. . 1 2 3 2 3 2 3 2 . .',
    '. . 1 2 2 3 2 3 2 3 . .',
    '. . . k r r s B S L . .',
    '. . . h g S G e G L . .',
    '. . . . r s S S L L H .',
    '. . . . r s S S m S . .',
    '. . . . . r s S S . . .',
    '. . . . . . s @ . . . .',
]


def press_officer():
    """The press minder: a good grey double-breasted city coat, the karakul pirozhok, glasses, a brown briefcase
    clamped under the near arm, a cigarette in the same hand; smokes and watches who talks to the Swede."""
    scene = 'c4p2_depot'
    mats, names = materials(scene, {
        'coat': ('#4E5256', {'bias': 0.04}),
        'trouser': '#2E3034',
        'boot': ('#141214', {'glossy': True}),
        'patch': '#3A3C40',
        'hat': (['#121214', '#24242A', '#38383E', '#4C4C52', '#626268', '#7C7C80'], {'texture': 'fur'}),
        'case': ('#74502E', {'glossy': True}),          # tan leather: it reads against the grey coat
        'clasp': BRASS,
        'glove': '#2A2420',
        'ember': EMBER,
        'smoke': SMOKE,
        'skin': SKIN['karsk'],
        'hair': '#2A2420',
        'eye': EYE_K,
        'glass': GLASS,
        'button': '#22242A',
        'band': '#2A2A30',
        'breath': SMOKE,
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#3A2228',
    })
    lg = HD.base_legend()
    spec = Spec(id='press_officer', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=22.4, torso=13.8, neck=1.6, thigh=10.4, shin=10.2,
                leg_r=(1.55, 1.4), arm_r=(1.55, 1.35), hip_f=1.8,
                coat=Coat(mat='coat', hem=-12.0, back=3.9, front=4.2, flare=0.9, chest=0.6, collar=1.6,
                          width_f=5.6, waist_f=4.6, hem_f=5.0, R=2.3, cyl=0.65, folds=0.7),
                heads=HD.head_views(lg, PRESS_SIDE, None, side_talk={(8, 6): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('glove', kind='glove'), lean=-0.5,
                style=dict(stride=4.6, swing=10.0, bob=1, walk_lean=0.5, lift=2.4, hem=0.5, idle_feet=(1.4, -1.4),
                           hold_n=(12.0, 56.0), arm_f_idle=(-3.0, 8.0), arm_n_idle=(12.0, 56.0), gesture='one_drag',
                           work='smoke',
                           talk_n=[(12.0, 56.0), (14.0, 66.0), (18.0, 82.0), (20.0, 88.0), (18.0, 80.0), (14.0, 64.0),
                                   (16.0, 74.0), (12.0, 58.0)],
                           talk_hand_n=['fist'] * 8))
    spec.hooks = {'side': [('coat', press_coat_side), ('head', press_case_side), ('front', press_cigarette_side),
                           ('head', press_smoke_side)]}
    return spec


def press_case_side(fr, J, P, spec):
    """The brown leather briefcase clamped under the near arm (drawn after the body, before the near arm: the upper
    arm lies over its middle; its back half sticks out behind the coat), the brass clasp catching the light.
    The cigarette hand stays free: it smokes with the case under the same arm."""
    body = J['body']
    x, y = body(-1.2, J['T'] - 3.0)
    case = bm(['obbbbmbbbbo', 'abccccccccd', 'abccccccccd', 'abccccccccd', 'oaaaaaaaaab'], CASE_LG, anchor=(5, 0))
    put_bitmap(fr, case, spec.names, x, y, name='briefcase')


def press_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    put_poly(fr, spec, [body(c.front - 1.5, T + 0.8), body(c.front - 0.1, T - 0.5), body(c.front - 0.2, T - 2.2),
                        body(c.front - 1.2, T - 2.0)], 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(c.front - 0.6, T - 0.8), body(c.front - 0.4, T - 2.4), 0.45, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, c.front - 0.6, -12.0, T - 2.4, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 0.6, (T - 3.6, T - 6.8, -0.2), tone=1)       # double-breasted: two rows
    buttons(fr, spec, J, c.front - 2.6, (T - 3.6, T - 6.8, -0.2), tone=1)
    flap(fr, spec, J, c.front - 3.6, c.front - 2.0, -2.6, 'coat')


def press_cigarette_side(fr, J, P, spec):
    x, y = J['wr_n']
    ang = math.radians(J['farm_ang_n'])
    tx, ty = x + math.sin(ang) * 1.6, y + math.cos(ang) * 1.6
    fr.recolor(tx, ty, M(spec, 'smoke'), 5)                       # the paper
    fr.recolor(tx + 1, ty, M(spec, 'ember'), 4 + min(1, P.get('ember', 0) // 2))
    if P.get('ash') == 1:
        fr.recolor(tx + 1, ty + 1, M(spec, 'smoke'), 2)
    elif P.get('ash') == 2:
        fr.recolor(tx + 1, ty + 3, M(spec, 'smoke'), 2)
    put_hand(fr, spec, 'fist', x, y, name='hand_n2')


def press_smoke_side(fr, J, P, spec):
    _puff(fr, J, P, spec, mat='smoke')
    if P.get('puff', 0) == 0 and P.get('ember', 0) == 0:
        # a thin thread of smoke rising from the cigarette between drags
        x, y = J['wr_n']
        ang = math.radians(J['farm_ang_n'])
        tx, ty = x + math.sin(ang) * 1.6 + 1, y + math.cos(ang) * 1.6
        ph = P.get('phase', 0) % 2
        for k in range(3):
            fr.px(tx + ((k + ph) % 2), ty - 2 - k, M(spec, 'smoke'), 3 + (k == 1))


# =================================================================================== STAPO_CIVIL (life sheet)
# a dark hat with the brim snapped down at the front (its shadow over the eyes), a hard square face
STAPO_SIDE = [
    '. . . . . 1 2 3 3 . . .',
    '. . . . 1 2 3 3 3 3 . .',
    '. . . 1 2 2 3 3 3 4 . .',
    '. . . u u v v V V V . .',
    '. R 1 1 2 2 2 3 3 3 4 3',
    '. . . j r r s B 2 2 . .',
    '. . . j h s S e S L . .',
    '. . . . r s S S L L H .',
    '. . . . r s S S m S . .',
    '. . . . . r s S S S . .',
    '. . . . . . s @ . . . .',
]


def stapo_civil():
    """The man at the kiosk: square-built, the black leather coat belted, the hat brim down, the newspaper held
    up -- he reads nothing; his eyes go over the edge of the paper to the buffet."""
    scene = 'c4p2_station'
    mats, names = materials(scene, {
        'coat': (['#060606', '#0E0E10', '#18181C', '#242428', '#383A40', '#5A5E66'], {'glossy': True}),
        'trouser': '#22242A',
        'boot': ('#121214', {'glossy': True}),
        'patch': '#2A2A2E',
        'hat': ['#0C0C0E', '#16161A', '#202026', '#2C2C34', '#3A3A44', '#4C4C56'],
        'band': ['#040405', '#08080A', '#0E0E12', '#141418', '#1C1C22', '#26262E'],
        'belt': (['#040404', '#0A0A0C', '#121216', '#1C1C20', '#2C2C32', '#44444C'], {'glossy': True}),
        'metal': '#7A7C80',
        'news': NEWS,
        'glove': '#1A1616',
        'skin': SKIN['berlin'],
        'hair': '#2A2422',
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#08080A',
    })
    lg = HD.base_legend()
    spec = Spec(id='stapo_civil', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM_C4P2[scene],
                hip_h=22.2, torso=14.0, neck=1.2, thigh=10.4, shin=10.2,
                leg_r=(1.7, 1.55), arm_r=(1.7, 1.45), hip_f=2.0,
                coat=Coat(mat='coat', hem=-11.0, back=4.4, front=4.6, flare=0.7, chest=0.8, collar=1.5,
                          width_f=6.0, waist_f=5.0, hem_f=5.4, R=2.4, cyl=0.7, folds=0.5),
                heads=HD.head_views(lg, STAPO_SIDE, None, side_talk={(8, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('glove', kind='glove'), lean=0.0,
                style=dict(stride=4.8, swing=10.0, bob=1, walk_lean=0.5, lift=2.4, hem=0.4, idle_feet=(1.6, -1.6),
                           hold_n=(6.0, 30.0), arm_f_idle=(-4.0, 10.0), gesture='fold_paper', work='read_paper',
                           talk_f=[(-4.0, 10.0), (-2.0, 24.0), (2.0, 44.0), (4.0, 52.0), (2.0, 44.0), (-2.0, 24.0),
                                   (0.0, 34.0), (-4.0, 12.0)],
                           talk_hand_f=[None, None, 'open', 'open', None, None, None, None]))
    spec.hooks = {'side': [('coat', stapo_coat_side), ('front', stapo_paper_side)]}
    return spec


def stapo_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    belt_side(fr, spec, J, 2.4, 'belt', buckle='metal')
    column_line(fr, spec, J, c.front - 1.0, -11.0, T - 1.8, 'coat', -0.8)
    buttons(fr, spec, J, c.front - 1.0, (T - 3.2, T - 6.4, -1.0), tone=1)
    put_poly(fr, spec, [body(-c.back + 0.2, T + 1.0), body(c.front - 0.4, T + 1.0), body(c.front, T - 1.4),
                        body(-c.back + 0.8, T - 1.0)], 'coat', tone=4, R=1.2, cyl=0.5, name='collar')
    flap(fr, spec, J, c.front - 3.8, c.front - 2.2, -2.8, 'coat')


def stapo_paper_side(fr, J, P, spec):
    """Folded newspaper in the near hand; in the work loop held open in both hands (P['paper']: 0 open, 1 turning
    a page, 2 shaken straight, 3 lowered a little -- the look over the edge)."""
    body = J['body']
    T = J['T']
    k = P.get('paper', -1)
    if k < 0:
        x, y = J['wr_n']
        put_bitmap(fr, bm(['ab', 'ac', 'ab', 'oa'], NEWS_LG, anchor=(0, 1)), spec.names, x + 0.6, y - 0.6,
                   name='paper', cast=False)
        put_hand(fr, spec, 'fist', x, y - 0.2, name='hand_n2')
        return
    px_, py_ = body(spec.coat.front + 2.6, T - 2.0 - (1.0 if k == 3 else 0.0))
    sheets = {
        0: ['bccdcc', 'bllalb', 'bcbacb', 'bbcabc', 'bcbacb', 'bbcabc', 'bcbacb', 'oaaoaa'],
        1: ['bccd..', 'bllad.', 'bcbacb', 'bbcabc', 'bcbacb', 'bbcabc', 'bcbacb', 'oaaoaa'],
        2: ['bccdcc', 'bllalb', 'bbcabc', 'bcbacb', 'bbcabc', 'bcbacb', 'bbcabc', 'oaaoaa'],
        3: ['bllalb', 'bcbacb', 'bbcabc', 'bcbacb', 'bbcabc', 'bcbacb', 'oaaoaa'],
    }
    put_bitmap(fr, bm(sheets[k], NEWS_LG, anchor=(2, 0)), spec.names, px_, py_, name='paper_open')
    put_hand(fr, spec, 'fist', px_ - 2.4, py_ + 2.0, name='hand_n2')
    put_hand(fr, spec, 'fist', px_ + 3.2, py_ + 2.4, name='hand_f2')


# =================================================================================== ALEXEI_PRESS (look)
GUIDEBOOK = ['#1E0A08', '#3E1410', '#5E2018', '#7E3022', '#9C4430', '#B85C40']   # red cloth binding, faded
# Ekdahl's guidebook carried at the side under the near arm, seen face-on: the red cloth cover, the gilt title, the
# pages' edge at the top (anchor = bottom front corner, at the hand)
BOOK_SIDE = ['.pPp.', 'obbbo', 'obgbo', 'obbbo', 'obcbo', 'oaaao']
BOOK_LG = {'o': ('book', 0), 'a': ('book', 1), 'b': ('book', 2), 'c': ('book', 3), 'g': ('gilt', 4),
           'p': ('paper', 3), 'P': ('paper', 4)}


# the ushanka's ear flaps tied up on the crown (a fold of fur on top, the tie knot), so the cropped dark hair, the
# ear and the clean-shaven jaw show -- the base sheet has the flaps down over the ears
ALEXEI_PRESS_SIDE = [
    '. . . . 1 2 3 3 3 . . .',
    '. . . 1 3 4 4 3 4 4 . .',
    '. . 1 2 3 3 4 3 3 4 4 .',
    '. 1 2 2 3 3 4 4 4 5 5 4',
    '. 1 2 3 2 3 3 3 4 4 4 3',
    '. . k h h k h r s b L .',
    '. . k h L S h k S e L .',
    '. . . k S s h s S S L H',
    '. . . . r s r S S S m .',
    '. . . . . r s r s S . .',
    '. . . . . . . s @ . . .',
]
ALEXEI_PRESS_FRONT = [
    '. . . . 2 3 4 3 2 . . .',
    '. . . 2 4 3 3 4 3 2 . .',
    '. . 2 3 4 5 5 4 4 3 2 .',
    '. 1 3 4 4 4 4 4 4 3 2 1',
    '. 2 3 3 3 3 3 3 3 2 2 .',
    '. . k L b S S b s k . .',
    '. . L L e S S e s L . .',
    '. . . L S S n s s . . .',
    '. . . s S m m S r . . .',
    '. . . . r S S r . . . .',
    '. . . . . s @ . . . . .',
]
ALEXEI_PRESS_BACK = [
    '. . . . 2 3 4 3 2 . . .',
    '. . . 2 4 3 3 4 4 3 . .',
    '. . 2 3 3 3 4 4 4 4 3 .',
    '. 1 2 2 3 3 3 4 4 4 3 2',
    '. 2 2 2 3 3 3 3 3 3 2 .',
    '. . k h h h h h h k . .',
    '. . L h h h h h h L . .',
    '. . . k h h h h k . . .',
    '. . . . k h h k . . . .',
    '. . . . r s s r . . . .',
    '. . . . . s @ . . . . .',
]


def alexei_press():
    """Alexei for the showcase on platform 1 (KarskB): the base sheet (chargen_cast.alexei) made presentable for the
    cameras -- the ushanka's flaps tied up on the crown (ear, cropped hair and the clean-shaven jaw show), a NEW
    cream-white wool scarf (its end lies over the jacket front) instead of the worn grey one.  The silhouette and
    the pace stay his own (the same person); the carry rows hold the guidebook (drawn before the near arm, so the
    forearm lies over it)."""
    import chargen_cast as CC
    import chargen_cast_c3p2 as P2
    from chargen_core import make_ramp
    spec = CC.alexei()
    spec.id = 'alexei_press'
    sc = spec.names['scarf']
    spec.mats[sc] = type(spec.mats[sc])('scarf', make_ramp('#D4CCB8', spec.scene), texture='knit')
    spec.heads = HD.head_views(HD.base_legend(), ALEXEI_PRESS_SIDE, ALEXEI_PRESS_FRONT, ALEXEI_PRESS_BACK)
    P2.add_mat(spec, 'book', [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8) for h in GUIDEBOOK])
    P2.add_mat(spec, 'gilt', [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8) for h in BRASS])
    P2.add_mat(spec, 'paper', [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8) for h in PAPER_W])
    hooks = {}
    for view, lst in spec.hooks.items():          # the flaps are tied up: no loose tie strings swinging
        hooks[view] = [(lay, fn) for lay, fn in lst if 'flaps' not in fn.__name__]
    hooks.setdefault('side', []).append(('head', press_scarf_end_side))
    hooks.setdefault('front', []).append(('head', press_scarf_end_front))
    hooks['side'].append(('head', guidebook_side))
    spec.hooks = hooks
    return spec


def press_scarf_end_side(fr, J, P, spec):
    """The new scarf's end lying over the jacket front below the roll (2 px wide, it swings a little with a step)."""
    body = J['body']
    T = J['T']
    sl = lag_dx(P, 0.6) if walking(P) else 0
    for v in (T - 1.6, T - 2.6, T - 3.6):
        x, y = body(spec.coat.front - 0.6, v)
        fr.px(x + sl, y, spec.names['scarf'], 4 if v > T - 3 else 3, name='scarf_end')
        fr.px(x + sl - 1, y, spec.names['scarf'], 3, name='scarf_end')


def press_scarf_end_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    for v in (T - 1.4, T - 2.4, T - 3.4, T - 4.2):
        x, y = body(0.8, v)
        fr.px(x, y, spec.names['scarf'], 4 if v > T - 3 else 3, name='scarf_end')
        fr.px(x + 1, y, spec.names['scarf'], 3, name='scarf_end')


def guidebook_side(fr, J, P, spec):
    """Drawn in the 'head' layer: after the body, before the near arm (the carry rows only)."""
    if not P.get('carry'):
        return
    x, y = J['wr_n']
    put_bitmap(fr, bm(BOOK_SIDE, BOOK_LG, anchor=(4, 5)), spec.names, x + 1.8, y + 0.5, name='guidebook')


# =================================================================================== PORTRAITS
# Busts on the round-2 pipeline (chargen_portrait2): signed-distance heads with individual planes, hand-designed
# eyes / brows / mouths, 4 expressions x 6 states.  Every face is its own: Maria angular and spare with high
# cheekbones and dark level eyes; Hanna oval with the Adler nose, quick and warm; Wendt broad and fleshy, heavy
# lids, soft jowls; Kuhnert lined and pinched, glasses low on the nose.  Backdrops per place and light (registered
# in memory in chargen_portrait2_paint.BG; no chargen_portrait2*.py file is changed).
def _portrait_mods():
    import chargen_portrait2 as PG
    import chargen_portrait2_cast as PC
    import chargen_portrait2_face as FC
    import chargen_portrait2_paint as PP
    import chargen_portrait2_sdf as S
    import chargen_portrait_c3 as PC3
    import chargen_portrait2_berlin as PCB
    PP.BG.setdefault('c4p2_depot', ('#16110e', '#060506', '#523618', '#b0783a'))    # coal stage, sodium dawn
    PP.BG.setdefault('c4p2_window', ('#0d1222', '#05060d', '#5c4226', '#c89048'))   # Hanna's lit window behind her
    PP.BG.setdefault('c4p2_gate', ('#0a0f1a', '#04060a', '#28343f', '#7a8a96'))     # the gate passage's cold lamp
    PP.BG.setdefault('c4p2_lodge', ('#110e14', '#060508', '#4c3c20', '#b09050'))    # the lodge window's yellow lamp
    PP.BG.setdefault('c4p2_platform', ('#120f13', '#050406', '#4e3a22', '#b08a50'))  # the showcase's floodlights
    return PG, PC, FC, PP, S, PC3, PCB


def _pt(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)


def _hash(x, y, seed):
    h = (np.asarray(x, np.int64) * 73856093) ^ (np.asarray(y, np.int64) * 19349663) ^ (seed * 83492791)
    return (h % 1000) / 1000.0


def pass_coal(smears, cloth=('vest', 'coat', 'coat_lapel'), seed=171):
    """Coal on Maria: smears on the face in head-local coordinates (they move with the head, never on the eyes)
    and dark flecks of coal dust on the vest and the coat."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
        M = G['M']
        d = G['d']
        rgb = rgb.copy()
        ids = [M.names.index(n) for n in ('skin', 'neck', 'ear', 'cheek') if n in M.names]
        m = np.isin(d.mat, ids) & d.hit
        if m.any():
            ys, xs = np.nonzero(m)
            L = PC._local(G, 'hf', m)
            a = np.zeros(len(ys))
            for c, r, s in smears:
                q = (((L - np.array(c)) / np.array(r)) ** 2).sum(1)
                a = np.maximum(a, s * np.clip(1.15 - q, 0.0, 1.0) ** 0.7)
            g = _hash(xs, ys, seed)
            a = np.where(a > 0.06, a * (0.7 + 0.6 * g), 0.0)
            px = rgb[m].astype(float)
            col = np.array([30.0, 28.0, 30.0])
            rgb[m] = np.round(px * (1.0 - a[:, None]) + col[None, :] * a[:, None]).astype(np.uint8)
        cid = [M.names.index(n) for n in cloth if n in M.names]
        c = np.isin(d.mat, cid) & d.hit
        if c.any():
            ys, xs = np.nonzero(c)
            g = _hash(xs, ys, seed + 1)
            fl = g < 0.035
            px = rgb[c].astype(float)
            px[fl] = px[fl] * 0.62
            rgb[c] = np.round(px).astype(np.uint8)
        return rgb
    return fn


def pass_needle(at=(-7.8, 9.0, 13.4), frame='tf'):
    """The sewing needle stuck in Maria's lapel: a short bright steel line, a red thread wound round its eye and
    hanging in a loop (the seamstress's mark, readable at dialogue size)."""
    def fn(spec, G, rgb, v, expr, row):
        from chargen_portrait2 import zoom_pt
        p = zoom_pt({'zoom': G.get('zoom', 1.0)}, G[frame].to_view(at))
        x0, y0 = int(np.floor(p[0])), int(np.floor(p[1]))
        h, w = rgb.shape[:2]
        for k, (dx, dy, c) in enumerate(((0, 0, '#eef2f2'), (1, -1, '#c8d0d2'), (2, -2, '#9aa2a4'),
                                         (3, -3, '#6e7678'), (-1, 1, '#c03a2e'), (-1, 2, '#8e2a22'),
                                         (-2, 3, '#b03428'), (-1, 4, '#7a241e'))):
            x, y = x0 + dx, y0 + dy
            if 0 <= x < w and 0 <= y < h and G['d'].hit[y, x]:
                rgb[y, x] = _pt(c)
        return rgb
    return fn


def pass_chalk(x_range=(-17.0, -8.0), y_range=(14.0, 46.0), mats=('coat',), seed=181, frame='tf'):
    """Chalk dust on Hanna's near sleeve / shoulder: pale specks, denser in a smear."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
        M = G['M']
        ids = [M.names.index(n) for n in mats if n in M.names]
        m = np.isin(G['d'].mat, ids) & G['d'].hit
        if not m.any():
            return rgb
        rgb = rgb.copy()
        L = PC._local(G, frame, m)
        ys, xs = np.nonzero(m)
        on = (L[:, 0] > x_range[0]) & (L[:, 0] < x_range[1]) & (L[:, 1] > y_range[0]) & (L[:, 1] < y_range[1])
        g = _hash(xs, ys, seed)
        cx = 0.5 * (x_range[0] + x_range[1])
        dens = 0.10 + 0.22 * np.clip(1.0 - np.abs(L[:, 0] - cx) / (0.5 * (x_range[1] - x_range[0])), 0, 1)
        sel = on & (g < dens)
        px = rgb[m].astype(float)
        lit = v[ys, xs] > 0.3
        col = np.where(lit[:, None], np.array([188.0, 190.0, 196.0])[None, :], np.array([120.0, 124.0, 136.0])[None, :])
        px[sel] = px[sel] * 0.35 + col[sel] * 0.65
        rgb[m] = np.round(px).astype(np.uint8)
        return rgb
    return fn


def pass_freckles(spots=(((0.0, 4.6, 18.0), (6.4, 2.4, 6.0)), ((-7.6, 6.4, 13.0), (3.4, 2.4, 5.0)),
                         ((7.6, 6.4, 13.0), (3.4, 2.4, 5.0))), density=0.16, seed=187, col=(150, 92, 64)):
    """Hanna's freckles: sparse warm specks over the bridge of the nose and the cheekbones (head-local, so they
    move with the head; never on the eyes or the lips -- skin material only)."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
        M = G['M']
        d = G['d']
        ids = [M.names.index(n) for n in ('skin', 'cheek') if n in M.names]
        m = np.isin(d.mat, ids) & d.hit
        if not m.any():
            return rgb
        rgb = rgb.copy()
        ys, xs = np.nonzero(m)
        L = PC._local(G, 'hf', m)
        a = np.zeros(len(ys))
        for c, r in spots:
            q = (((L - np.array(c)) / np.array(r)) ** 2).sum(1)
            a = np.maximum(a, np.clip(1.0 - q, 0.0, 1.0))
        g = _hash(xs, ys, seed)
        sel = (a > 0.0) & (g < density * (0.4 + a))
        px = rgb[m].astype(float)
        c = np.array(col, float)
        lit = (v[ys, xs] > 0.45)[:, None]
        tgt = np.where(lit, c, c * 0.72)
        px[sel] = px[sel] * 0.45 + tgt[sel] * 0.55
        rgb[m] = np.round(px).astype(np.uint8)
        return rgb
    return fn


def pass_earring(side=1, drop=4.6, col='#ded8c8', shade='#8a8478'):
    """A small pearl stud on the visible earlobe (2 px: the pearl and its shadow)."""
    def fn(spec, G, rgb, v, expr, row):
        lm = G['lmv'].get('ear_l' if side > 0 else 'ear_r')
        if lm is None:
            return rgb
        x, y = int(np.floor(lm[0])), int(np.floor(lm[1] + drop))
        h, w = rgb.shape[:2]
        for dx, dy, c in ((0, 0, col), (0, 1, shade)):
            if 0 <= x + dx < w and 0 <= y + dy < h and G['d'].hit[y + dy, x + dx]:
                rgb[y + dy, x + dx] = _pt(c)
        return rgb
    return fn


def pass_temple_grey(mat='hair', y0=-8.0, ramp_hex=('#2c2c2e', '#4a4a4c', '#6e6c6a', '#8e8c88', '#aeaca6'),
                     seed=213):
    """Wendt's dark hair goes grey at the temples: hair pixels low on the head (head-local y > y0) are re-coloured
    into a grey ramp by their own lightness, with a ragged edge (hash) where the grey begins."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
        M = G['M']
        if mat not in M.names:
            return rgb
        m = (G['d'].mat == M.names.index(mat)) & G['d'].hit
        if not m.any():
            return rgb
        rgb = rgb.copy()
        ys, xs = np.nonzero(m)
        L = PC._local(G, 'hf', m)
        g = _hash(xs, ys, seed)
        on = L[:, 1] > (y0 + 2.0 * (g - 0.5))
        px = rgb[m].astype(float)
        lum = px.mean(1)
        lo, hi = lum.min(), max(lum.max(), lum.min() + 1.0)
        k = np.clip(((lum - lo) / (hi - lo)) * (len(ramp_hex) - 1) + 0.5, 0, len(ramp_hex) - 1).astype(int)
        grey = np.array([_pt(c) for c in ramp_hex], float)[k]
        px[on] = grey[on]
        rgb[m] = np.round(px).astype(np.uint8)
        return rgb
    return fn


def pass_check(mat='kerchief', period=(4.6, 4.6), frame='hf', dark=0.70, cross=0.52, accent='#b89a52',
               accent_every=3, seed=177):
    """A woven check on a wool headscarf (rgb pass): darker warp and weft bars in surface coordinates (round the
    head, height), darker where they cross, and a thin ochre thread every few bars -- the cloth reads as a printed
    / woven scarf, never as a knitted cap."""
    def fn(spec, G, rgb, v, expr, row):
        PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
        M = G['M']
        if mat not in M.names:
            return rgb
        m = (G['d'].mat == M.names.index(mat)) & G['d'].hit
        if not m.any():
            return rgb
        rgb = rgb.copy()
        L = PC._local(G, frame, m)
        u = np.arctan2(L[:, 0], L[:, 2] + 3.0) * 17.0
        w = L[:, 1]
        fu = (u / period[0]) % 1.0
        fw = (w / period[1]) % 1.0
        bu = fu < 0.30
        bw = fw < 0.30
        iu = np.floor(u / period[0]).astype(int)
        iw = np.floor(w / period[1]).astype(int)
        acc = ((iu % accent_every == 0) & (fu > 0.62) & (fu < 0.80)) | \
              ((iw % accent_every == 0) & (fw > 0.62) & (fw < 0.80))
        px = rgb[m].astype(float)
        f = np.where(bu & bw, cross, np.where(bu | bw, dark, 1.0))
        px = px * f[:, None]
        ys, xs = np.nonzero(m)
        lit = v[ys, xs] > 0.32
        ac = _pt(accent).astype(float)
        tgt = np.where(lit[:, None], ac[None, :], ac[None, :] * 0.55)
        px[acc] = px[acc] * 0.35 + tgt[acc] * 0.65
        rgb[m] = np.round(np.clip(px, 0, 255)).astype(np.uint8)
        return rgb
    return fn


def scarf_loose(M, mat='scarf', y=0.0, r=11.2, tube=3.4, ends=None, seed=182):
    """Hanna's rust-red scarf thrown on loosely: one loose loop lying low round the collar (lower in front than
    at the back) and BOTH long ends hanging down the front of the open coat (torso-local)."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    m = M(mat)
    parts = []
    for i in range(12):
        a = np.radians(i * 30.0)
        wob = 0.8 * np.sin(a * 2.0 + 0.4)
        tb = tube * (1.0 + 0.16 * np.sin(a * 3.0 + 0.9))
        parts.append(S.Ellipsoid((r * np.sin(a), y + wob + 1.6 * (1.0 + np.cos(a)), -1.0 + r * np.cos(a)),
                                 (tb + 0.7, tb, tb + 0.5), m))
    ends = ends or [[(-4.0, y + 4.0, 12.4), (-6.0, y + 15.0, 13.6), (-6.8, y + 32.0, 14.2)],
                    [(3.4, y + 4.4, 12.4), (5.0, y + 16.0, 13.4), (5.6, y + 32.0, 14.0)]]
    for pts in ends:
        for i in range(len(pts) - 1):
            parts.append(S.RoundCone(pts[i], pts[i + 1], 3.3 - i * 0.15, 3.1 - i * 0.15, m))
    node = S.Union(parts, k=2.2)
    return S.Displace(node, lambda P: S.vnoise3(P, 2.2, seed), amp=0.45, lipschitz=1.3)


def foulard(M, mat='silk', y=-0.5, r=8.6, seed=211):
    """Wendt's silk foulard instead of a shirt and tie: a thin roll round the neck under the fur collar and the two
    ends crossed flat in the coat's opening (torso-local)."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    m = M(mat)
    parts = []
    for i in range(12):
        a = np.radians(i * 30.0)
        parts.append(S.Ellipsoid((r * np.sin(a), y + 0.8 * (1.0 + np.cos(a)), -1.0 + r * np.cos(a)),
                                 (3.2, 2.6, 3.0), m))
    parts.append(S.Ellipsoid((-1.6, y + 9.0, 11.4), (5.6, 9.0, 2.4), m, R=S.rot(0, 0, 16)))
    parts.append(S.Ellipsoid((2.2, y + 11.5, 11.0), (4.6, 9.2, 2.2), m, R=S.rot(0, 0, -20)))
    node = S.Union(parts, k=1.6)
    return S.Displace(node, lambda P: S.vnoise3(P, 2.6, seed), amp=0.3, lipschitz=1.3)


def pass_glasses_string(col='#3a3430', side=-1):
    """The cord of Kuhnert's reading glasses: from the near temple of the frame down behind the ear to the collar."""
    def fn(spec, G, rgb, v, expr, row):
        lm = G['lmv'].get('ear_r') if side < 0 else G['lmv'].get('ear_l')
        if lm is None:
            return rgb
        x0, y0 = int(np.floor(lm[0])), int(np.floor(lm[1]))
        h, w = rgb.shape[:2]
        for k in range(16):
            x, y = x0 - 1 + (k // 6), y0 + 2 + k
            if 0 <= x < w and 0 <= y < h and G['d'].hit[y, x]:
                rgb[y, x] = _pt(col) if k % 5 else _pt('#5a524a')
        return rgb
    return fn


def vest_over(M, t, mat='vest', off=4.0, v_open=0.75, v_top=-1.0, half_w=13.6, quilt=(4.4, 0.55)):
    """Maria's issued quilted vest OVER the thin coat: a padded sleeveless shell, open in a wide V at the throat (the
    coat's lapels show inside it), cut away at the shoulders (the coat's sleeves show)."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    m = M(mat)
    node = PC.quilted(S.Offset(t, off, m), period=quilt[0], amp=quilt[1])

    def cut(P):
        """< 0 where the vest is cut away: the V at the throat and outside the shoulder seams."""
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        vw = np.maximum(3.0 - z, np.abs(x) - (y - v_top) * v_open)
        arm = np.abs(x) - half_w - 0.10 * np.maximum(y - 6.0, 0.0)
        return np.minimum(vw, -arm)
    return S.Inter(node, S.Fn(lambda P: -cut(P), m))


def fur_roll(M, mat='karakul', y=1.0, r=12.6, tube=4.2, seed=191):
    """Wendt's fur collar: a thick roll round the back and sides of the neck, its two ends lying OPEN down the coat
    edges (they never cross in front: the shirt and tie show between them)."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    E = S.Ellipsoid
    m = M(mat)
    parts = []
    for i in range(13):
        a = np.radians(45.0 + i * 22.5)          # 45..315 deg: round the back, open in front (0 = front)
        parts.append(E((r * np.sin(a), y + 1.6 * (1 - np.cos(a)), -1.5 + (r - 1.0) * np.cos(a)),
                       (tube + 1.2, tube, tube + 0.5), m))
    for sx in (1, -1):
        parts.append(S.RoundCone((sx * 9.0, y + 4.0, 8.6), (sx * 10.8, y + 15.0, 10.6), 3.6, 2.6, m))
    node = S.Union(parts, k=2.6)
    return S.Displace(node, lambda P: S.vnoise3(P, 1.3, seed), amp=0.6, lipschitz=1.3)


def maria_portrait():
    """Maria Gorelowa (34): a long, angular, spare face -- cheekbones set high and sharp over hollow cheeks, a long
    straight nose with the small bump of an old break on the bridge, a wide thin-lipped mouth held firm, a narrow
    chin, dark deep-set eyes under thick straight brows; coal on the forehead, the cheekbone and the jaw.  The green
    woollen headscarf with its woven check is tied UNDER THE CHIN (knot and two short tails, the back corner over
    the nape), its rolled front edge pushed back off a centre parting of dark hair; the plum Western coat with its
    lapels under the issued quilted vest, a grey jumper at the throat, the needle with a red thread in the lapel.
    Head a little raised and turned further than the others -- the straight back.  The coal stage's sodium light
    from the front right, the cold dawn behind."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0a0c14', '#1c1a24', '#36282e', '#583a3a', '#82584a', '#a8785c', '#c89a78', '#e2be9a')
    rim = '#8c98b8'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=2))
    green = ramp('#060906', '#0e150c', '#172214', '#22301c', '#2e3e26', '#3c4e32', '#4c5f40', '#5e7150')
    plum = ramp('#0b070b', '#170f15', '#251a22', '#352630', '#473440', '#5a4452', '#6e5664')
    vest = ramp('#070807', '#0f110e', '#181b16', '#22261f', '#2d3229', '#3a4034', '#4a5042')
    styles.update({
        'kerchief': MatStyle(green, [0.04, 0.09, 0.17, 0.28, 0.42, 0.60, 0.80], dither=0.03, rim='#8aa0a0'),
        'kerchief_hem': MatStyle(ramp('#050705', '#0b100a', '#131b11', '#1c2718', '#26331f', '#314028', '#3e4e33'),
                                 [0.05, 0.12, 0.24, 0.40, 0.60, 0.80], rim='#7a9090'),
        'coat': MatStyle(plum, PC3.TH6, dither=0.05, rim=rim),
        'coat_lapel': MatStyle(plum, PC3.TH6, rim=rim),
        'vest': MatStyle(vest, PC3.TH7, dither=0.03, rim=rim),
        'shirt': MatStyle(ramp('#0b0b0c', '#1a1a1c', '#2c2c2e', '#403f40', '#565454', '#6c6a68'),
                          [0.06, 0.14, 0.27, 0.45, 0.66], rim=rim),
        'hair': MatStyle(ramp('#050406', '#0d0a0d', '#171215', '#221a1d', '#2e2427'), [0.06, 0.16, 0.32, 0.55],
                         rim='#6c7690', wrap=0.25),
    })
    head = dict(PC.FEMALE)
    head.update(PC3.SOFT)
    head.update(skull_r=(15.0, 16.6, 19.6), mid_h=(10.6, 7.4, 11.0), fore_h=(11.2, 8.8, 11.6),
                cheek_c=(9.6, 2.8, 9.6), cheek_r=(3.8, 2.6, 3.2), malar_c=(7.8, 6.0, 12.8), malar_r=(5.2, 3.0, 4.0),
                jaw_angle=(10.0, 15.6, -4.0), jaw_r=(2.2, 2.6, 2.6), low_r=(10.4, 11.2, 12.0),
                chin_c=(0.0, 22.6, 11.2), chin_h=(3.6, 3.0, 3.0), chin_rad=2.0, chin_pt=(3.0, 23.6, 9.6),
                nose_root=(0.0, -1.4, 15.6), nose_tip=(0.0, 9.4, 19.6), tip_r=1.9, nose_r=(1.15, 1.6), ala_x=2.1,
                ala_r=(1.35, 1.3, 1.6), eye_x=6.4, mouth_y=15.0, lip_up=(0.0, 14.3, 16.0), lip_up_r=(4.5, 0.95, 1.2),
                lip_lo=(0.0, 16.2, 15.6), lip_lo_r=(3.9, 1.25, 1.3), brow_r=(11.4, 2.2, 3.0), neck_r=(6.4, 7.8),
                extra=[('ellipsoid', ((0.0, 2.6, 18.1), (1.35, 1.6, 1.15), 'skin', 0.9))])
    return dict(
        id='maria', city='karsk',
        look=dict(key=(0.60, -0.38, 0.70), rim=(-0.82, -0.32, -0.48), ambient=0.08, bg='c4p2_depot',
                  glow=(0.80, 0.24)),
        head=head, zoom=1.14,
        head_pos=(54.0, 55.0, 0.0), yaw=36.0, pitch=-3.0, roll=1.0,
        torso_pos=(55.0, 92.0, -0.5), torso_yaw=16.0, torso=dict(width=0.90, depth=0.96, slope=1.2),
        poses={'neutral': (0, 0, 0), 'concerned': (-1, 3, -1), 'determined': (1, -1, 0), 'surprised': (2, -2, 1)},
        head_items=[lambda M, hp: PC.kerchief_chin(M, hp, mat='kerchief', thick=1.9, fold_amp=0.75, seed=171,
                                                   open_w=12.4, open_top=-15.4, open_bot=25.8)],
        torso_items=[
            lambda M, t: PC.coat_layers(M, t, coat='coat', inner='shirt', v_open=0.46, v_top=1.0, coat_t=2.4,
                                        lapel=True, collar_h=5.0, collar_r=(11.0, 12.8)),
            lambda M, t: vest_over(M, t),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=dict(PC3.groups_std({'kerchief': 2, 'vest': 6, 'shirt': 5}), kerchief_hem=3),
        tone_passes=[PC.pass_folds('kerchief', knot=(0.0, 27.0, 11.0), mode='chin', n=7, seed=172),
                     PC.pass_grain('kerchief', 0.04, seed=173), PC.pass_stitches('vest', 4.4, seed=174),
                     PC.pass_grain('coat', 0.10, seed=175), PC.pass_knit('shirt', ribs=30, seed=176)],
        rgb_passes=[pass_check('kerchief', period=(4.4, 4.4), dark=0.78, cross=0.62, seed=177),
                    pass_coal([((-5.0, -9.0, 12.5), (5.0, 1.8, 7.0), 0.66), ((-9.6, 7.0, 10.0), (3.4, 2.6, 7.0), 0.66),
                               ((5.8, 17.0, 12.0), (2.6, 1.8, 6.0), 0.50)]),
                    pass_needle()],
        eye=dict(iris='#2a201c', iris_d='#16100e', sclera='#bcb2a4', sclera_d='#6a6670', lash='#0c080a',
                 pupil='#050404', catch='#efe4cc'),
        brow=dict(col='#120c0e', col_l='#2a2022'),
        mouth=dict(line='#3a181c', corner='#522628', inner='#1a0a0d', teeth='#b4a896', tongue='#6a3034'),
        features=dict(
            eyes=FC.eye_shapes(PC._female_eyes(), 'deep'),
            extra=[PC.ear_detail, PC3.cheek_hollow, PC.wrinkles(forehead=0, crow=False, naso=False, under=False)],
            brows={'neutral': dict(arch=0.0, lift_inner=0.0), 'concerned': dict(lift_inner=1.6, lift_outer=-0.3,
                                                                                arch=0.1),
                   'determined': dict(lift_inner=-1.6, arch=0.0, dy=0.5),
                   'surprised': dict(dy=-1.4, arch=0.6, lift_inner=0.4)},
            brow_thick=((2, 2, 2), (2, 1, 1)), brow_pts=((1.6, -4.0, 17.0), (10.6, -4.0, 13.4)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.3, smile=0.0), 'concerned': dict(corner_drop=0.8),
                   'determined': dict(corner_drop=0.5), 'surprised': dict(parted=1)}),
        priority={'kerchief': 1, 'kerchief_hem': 1, 'vest': 1},
    )


def hanna_portrait():
    """Hanna Adler (27): a round, open face -- full cheeks, a short rounded chin, a short straight nose with a soft
    tip, a wide mouth that is about to say something ironic, freckles over the nose; Konrad's blue-grey eyes, set
    wider; dark-blonde hair pinned up in a practical knot HIGH on the crown (it stands above the head in the
    silhouette), strands escaped at the temple and the nape, a small pearl stud; the dark-blue coat open over the
    grey cardigan and the round white blouse collar, the rust-red knitted scarf thrown on loosely with both ends
    down the front, chalk dust on the near sleeve and the coat.  Her own lit window behind her in the night yard;
    she faces the viewer more squarely than anyone in the cast."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0b0d18', '#1e1b28', '#3a2b37', '#603e45', '#8c5b50', '#b67e64', '#d8a682', '#eecaa6')
    rim = '#7c8cb4'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=18))
    styles['cheek'] = MatStyle(PC3.lip_of(sk, warm=22), PC.SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24,
                               ao=0.75)
    navy = ramp('#04060c', '#0a1020', '#111a34', '#1a2648', '#24335e', '#304276', '#3f548e')
    styles.update(PC3.coat_style(navy, PC3.TH6, rim))
    styles.update({
        'cardigan': MatStyle(ramp('#0c0c0e', '#1a1a1d', '#2a2a2e', '#3c3c40', '#505054', '#666668', '#7c7c7c'),
                             PC3.TH6, dither=0.03, rim=rim),
        'shirt': MatStyle(ramp('#16181c', '#34383e', '#5e6266', '#8e908c', '#b8b8b0', '#dcdace', '#f0efe4'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#b0c0d4'),
        'scarf': MatStyle(ramp('#120604', '#2a0d06', '#46180a', '#662410', '#883418', '#a84622', '#c45c30'),
                          PC3.TH6, dither=0.03, rim='#d09878'),
        'hair': MatStyle(ramp('#0e0a07', '#25190f', '#3e2b18', '#5a4024', '#775834', '#927046', '#aa885a'),
                         [0.04, 0.10, 0.19, 0.31, 0.47, 0.68], rim='#a0a8c0', wrap=0.3, lift=0.2),
    })
    head = dict(PC.FEMALE)
    head.update(PC3.SOFT)
    head.update(skull_r=(15.6, 16.2, 19.4), mid_h=(11.8, 6.2, 11.4), fore_h=(11.8, 8.4, 11.6),
                cheek_c=(10.6, 3.4, 10.2), cheek_r=(5.4, 3.8, 4.6), malar_c=(7.2, 7.6, 12.6), malar_r=(4.8, 4.0, 4.0),
                jaw_angle=(10.6, 13.8, -3.6), jaw_r=(2.9, 3.0, 3.0), low_r=(11.6, 10.0, 12.6),
                chin_c=(0.0, 20.4, 11.8), chin_h=(4.4, 2.8, 3.2), chin_rad=3.4, chin_pt=(3.8, 21.2, 10.4),
                nose_root=(0.0, -0.8, 15.0), nose_tip=(0.0, 7.8, 18.8), nose_r=(1.2, 1.7), tip_r=2.3, ala_x=2.2,
                ala_r=(1.45, 1.35, 1.7), eye_x=6.8, mouth_y=13.8, lip_up=(0.0, 13.1, 16.2),
                lip_up_r=(4.4, 1.5, 1.6), lip_lo=(0.0, 15.2, 15.8), lip_lo_r=(3.9, 1.9, 1.7),
                brow_r=(11.4, 1.9, 2.6), neck_r=(6.0, 7.4),
                extra=PC.blush(c=(9.4, 6.6, 11.2), r=(4.4, 3.2, 3.2)))
    return dict(
        id='hanna', city='berlin',
        look=dict(key=(0.50, -0.44, 0.75), rim=(-0.82, -0.32, -0.48), ambient=0.09, bg='c4p2_window',
                  glow=(0.78, 0.22)),
        head=head, zoom=1.12, smooth=2,
        head_pos=(56.0, 57.0, 0.0), yaw=17.0, pitch=-1.0, roll=-4.0,
        torso_pos=(56.0, 93.0, -0.5), torso_yaw=8.0, torso=dict(width=0.94, depth=1.0, slope=1.3),
        poses={'neutral': (0, 0, 0), 'concerned': (-3, 3, -2), 'determined': (2, -1, 1), 'surprised': (3, -3, 2)},
        head_items=[lambda M, hp: PC.hair_bun(M, hp, bun=(-1.0, -27.5, -12.0), bun_r=7.4, hairline=-13.8,
                                              thick=2.1, seed=181)],
        torso_items=[
            lambda M, t: PC.layered_front(M, t, outer='coat', mid='cardigan', inner='shirt', v_outer=(0.58, 0.0),
                                          v_mid=(0.30, 5.0), outer_t=2.8, mid_t=1.8, lapel=True, collar_h=6.4,
                                          collar_r=(12.0, 13.8)),
            lambda M, t: PC.tie_knot_collar(M, mat='shirt', y=1.0, z=8.0),
            lambda M, t: scarf_loose(M, mat='scarf', y=-2.6, r=12.8, tube=3.1, seed=182,
                                    ends=[[(-6.4, 1.0, 12.2), (-7.8, 14.0, 13.6), (-8.4, 34.0, 14.4)],
                                          [(5.4, 1.6, 12.2), (6.8, 15.0, 13.4), (7.4, 34.0, 14.2)]]),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck', 'cheek'),
        groups=PC3.groups_std({'cheek': 0, 'cardigan': 5, 'scarf': 6}),
        tone_passes=[PC.pass_strands('hair', seed=183), PC.pass_knit('scarf', ribs=22, seed=184),
                     PC.pass_knit('cardigan', ribs=36, seed=185), PC.pass_grain('coat', 0.05, seed=186)],
        rgb_passes=[pass_freckles(density=0.10, col=(176, 112, 80)), pass_earring(side=1),
                    pass_chalk(x_range=(-18.0, -7.0), y_range=(12.0, 50.0), seed=181),
                    pass_chalk(x_range=(4.0, 12.0), y_range=(30.0, 52.0), seed=188)],
        eye=dict(iris='#536b82', iris_d='#2c3a4a', sclera='#cac0b4', sclera_d='#7d7480', lash='#160e0c',
                 pupil='#0a0a10', catch='#f4ecda'),
        brow=dict(col='#3e2e1e', col_l='#62492e'),
        mouth=dict(line='#4e1c20', corner='#66302e', inner='#1a0a0d', teeth='#c4b6a6', tongue='#7a3438'),
        features=dict(
            eyes=FC.eye_shapes(PC._female_eyes(), 'lift'),
            extra=[PC.ear_detail, PC3.loose_strand, hanna_strands],
            brows={'neutral': dict(arch=0.7, lift_inner=0.2), 'concerned': dict(lift_inner=2.2, lift_outer=-0.3,
                                                                                 arch=0.5),
                   'determined': dict(lift_inner=-1.2, arch=0.3, dy=0.4),
                   'surprised': dict(dy=-2.0, arch=1.5, lift_inner=0.6)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.9, -4.0, 17.0), (10.6, -3.8, 13.2)), nostril='small',
            mouth={'neutral': dict(smile=0.65, corner_drop=-0.2), 'concerned': dict(corner_drop=0.6, smile=0.1),
                   'determined': dict(corner_drop=0.1, smile=0.25), 'surprised': dict(parted=2)}),
        priority={'scarf': 1},
    )


def hanna_strands(spec, G, cv, expr, mouth_state, blink, v):
    """Two more strands escaped from the high knot: one over the far temple, one down the nape."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    PC.head_line(G, cv, [(9.6, -12.0, 9.0), (10.6, -7.0, 8.6), (10.2, -3.0, 8.8)], -2, allow_mats=('skin', 'ear'))
    PC.head_line(G, cv, [(-12.4, -2.0, -6.0), (-12.8, 3.0, -7.0), (-12.0, 8.0, -7.6)], -2,
                 allow_mats=('skin', 'ear', 'neck'))


def wendt_portrait():
    """Kommissar Wendt (about 50): a heavy, broad, fleshy face -- soft jowls and a double chin over a thick short
    neck, full cheeks, a fleshy rounded nose, a wide thin upper lip over a fuller lower one set in a polite half
    smile, small pale eyes under heavy lids, dark heavy brows; dark hair oiled back, grey at the temples; a PEARL-GREY
    homburg with a black band (the cast's other homburgs are dark); the dark grey coat with a wide dark-brown fur
    shawl collar lying over his shoulders, an bottle-green silk foulard with ivory dots in the opening -- no white collar,
    no tie, no glasses, no moustache, no badge.  He looks out from under the brim, head a little lowered, almost
    straight at the viewer.  The gate passage's cold lamp behind him in the night courtyard."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0a0e16', '#1c1c26', '#3a2b34', '#603f44', '#8c5c51', '#b48068', '#d4a486', '#eac8aa')
    rim = '#7c90a8'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=-2))
    grey = ramp('#050607', '#0b0d10', '#13161a', '#1b1f24', '#252a30', '#30363d', '#3c434b')
    styles.update(PC3.coat_style(grey, PC3.TH6, rim))
    felt = ramp('#101114', '#22242a', '#383a3e', '#505256', '#6a6b6c', '#848480', '#9c9a94', '#b2b0a8')
    fth = [0.03, 0.08, 0.15, 0.25, 0.38, 0.55, 0.75]
    styles.update({
        'felt': MatStyle(felt, fth, dither=0.04, rim='#c8d0d8'),
        'brim': MatStyle(felt, fth, dither=0.0, rim='#c8d0d8'),
        'ribbon': MatStyle(ramp('#020203', '#060608', '#0c0c10', '#141418', '#1e1e24'), [0.06, 0.16, 0.32, 0.55],
                           rim='#4a5a66'),
        'karakul': MatStyle(ramp('#040302', '#0b0705', '#140d09', '#1e140d', '#2a1c12', '#382618', '#48321f'),
                            [0.05, 0.12, 0.22, 0.36, 0.52, 0.72], dither=0.05, rim='#8a8478'),
        'silk': MatStyle(ramp('#030806', '#06110c', '#0b1c14', '#12281d', '#1a3527', '#234333', '#2e5240'),
                         [0.05, 0.12, 0.24, 0.40, 0.58, 0.78], rim='#8aa898'),
        'shirt': MatStyle(ramp('#14161a', '#30343a', '#585c60', '#868884'), [0.08, 0.2, 0.45], rim=rim),
        'hair': MatStyle(ramp('#050404', '#0c0a09', '#15110f', '#1f1916', '#2a221e', '#362c27'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#6a7484', wrap=0.3),
    })
    head = dict(skull_r=(17.2, 17.0, 20.4), mid_h=(13.4, 7.6, 12.0), fore_h=(12.4, 9.0, 12.0),
                cheek_c=(12.2, 5.0, 9.4), cheek_r=(7.0, 5.2, 5.6), malar_r=(3.8, 3.4, 3.2),
                jaw_angle=(13.8, 16.0, -3.0), jaw_r=(3.6, 3.6, 3.4), low_r=(14.4, 12.2, 13.8),
                chin_c=(0.0, 22.4, 11.8), chin_h=(5.6, 3.8, 3.8), chin_rad=3.4, chin_pt=(4.4, 23.6, 10.6),
                nose_root=(0.0, -0.8, 15.6), nose_tip=(0.0, 9.0, 20.0), tip_r=2.8, nose_r=(1.6, 2.1), ala_x=2.8,
                ala_r=(1.8, 1.6, 2.0), brow_r=(12.6, 2.8, 3.4), mouth_y=15.4, lip_up=(0.0, 14.7, 16.6),
                lip_up_r=(4.9, 0.9, 1.2), lip_lo=(0.0, 16.6, 16.2), lip_lo_r=(4.2, 1.4, 1.4), neck_r=(10.4, 11.6),
                eye_x=6.0,
                jaw_extra=[('ellipsoid', ((9.4, 19.6, 4.4), (5.0, 4.0, 5.0), 'skin', 2.6)),
                           ('ellipsoid', ((-9.4, 19.6, 4.4), (5.0, 4.0, 5.0), 'skin', 2.6)),
                           ('ellipsoid', ((0.0, 26.2, 6.4), (7.8, 3.0, 5.2), 'skin', 2.6))])
    return dict(
        id='wendt', city='berlin',
        look=dict(key=(0.40, -0.60, 0.69), rim=(-0.80, -0.36, -0.48), ambient=0.07, bg='c4p2_gate',
                  glow=(0.72, 0.12)),
        head=head, zoom=1.10,
        head_pos=(56.0, 57.0, 0.0), yaw=19.0, pitch=6.0, roll=1.0,
        torso_pos=(56.0, 94.0, -0.5), torso_yaw=9.0, torso=dict(width=1.16, depth=1.12, slope=0.8),
        poses={'neutral': (0, 0, 0), 'concerned': (-1, 2, -1), 'determined': (1, 2, 0), 'surprised': (1, -1, 0)},
        head_items=[lambda M, hp: PC3.homburg(M, hp, y0=-12.8, band_r=(18.0, 21.8), crown_h=14.0, brim_w=8.8),
                    lambda M, hp: PC.hair_short(M, hp, hairline=-14.0, front_z=7.6, burn_y=2.6, thick=0.9)],
        torso_items=[
            lambda M, t: PC.coat_layers(M, t, v_open=0.34, v_top=4.0, lapel=False, collar=False),
            lambda M, t: foulard(M, mat='silk', y=-1.0, r=9.0, seed=211),
            lambda M, t: PC3.fur_collar(M, mat='karakul', y=-0.6, r=14.4, tube=5.4, seed=191),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=PC3.groups_std({'felt': 2, 'ribbon': 2, 'brim': 3, 'silk': 5, 'karakul': 6}),
        tone_passes=[PC.pass_grain('felt', 0.05, seed=192), PC.pass_grain('coat', 0.05, seed=193),
                     PC.pass_fur('karakul', seed=194), PC.pass_strands('hair', seed=195)],
        rgb_passes=[pass_temple_grey(y0=-8.0), PC.pass_dots('silk', period=3.4, seed=212, frame='tf',
                                                            lit='#d8d0b4', shade='#5c6a58', radius=0.17)],
        eye=dict(iris='#7a888c', iris_d='#465256', sclera='#c2bab0', sclera_d='#6c6a72', lash='#120c10',
                 pupil='#0a0a0e', catch='#eef0e6'),
        brow=dict(col='#1e1a1a', col_l='#3a3432'),
        mouth=dict(line='#3c1a1e', corner='#54282a', inner='#1a0a0d', teeth='#b6a896', tongue='#6a3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'hooded', 'droop'),
            extra=[PC.ear_detail, PC.wrinkles(forehead=1, crow=True, naso=True, under=True), PC.eye_bags()],
            brows={'neutral': dict(arch=0.2), 'concerned': dict(lift_inner=0.9, lift_outer=-0.2, arch=0.2),
                   'determined': dict(lift_inner=-0.9, arch=0.1, dy=0.3),
                   'surprised': dict(dy=-0.8, arch=0.6, lift_inner=0.2)},
            brow_thick=((2, 2, 2), (2, 1, 1)), brow_pts=((1.8, -3.8, 17.2), (10.6, -3.4, 13.8)), nostril='small',
            mouth={'neutral': dict(smile=0.55, corner_drop=-0.1), 'concerned': dict(corner_drop=0.3, smile=0.2),
                   'determined': dict(corner_drop=0.1, smile=0.2), 'surprised': dict(parted=1)}),
        priority={'brim': 2, 'ribbon': 2, 'silk': 1, 'karakul': 1},
    )


def blockwart_portrait():
    """Erwin Kuhnert (about 60): a lined, pinched face -- a narrow forehead under the flat cap, deep lines from the
    nose to the mouth, a small sharp nose, thin lips pressed together, watery pale eyes under bushy grey brows, grey
    stubble, the reading glasses low on the nose on their cord; grey hair at the temples; the brown work coat
    buttoned high over a dark green cardigan and a striped collarless shirt.  The lodge's yellow lamp beside him."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    sk = ramp('#0c0c12', '#1e1a20', '#3a2a2c', '#604040', '#8a6052', '#b08468', '#cea688', '#e4c6a8')
    rim = '#7a86a0'
    styles = PC.skin_styles(sk, rim, PC3.lip_of(sk, warm=-8))
    brown = ramp('#0a0705', '#160f0a', '#241910', '#342416', '#46321e', '#5a4128', '#6e5234', '#846444')
    styles.update(PC3.coat_style(brown, PC3.TH7, rim))
    styles.update({
        'cap': MatStyle(ramp('#070605', '#110f0d', '#1b1814', '#26221c', '#322c25', '#40382f', '#4e463a'),
                        [0.05, 0.12, 0.22, 0.36, 0.54, 0.74], dither=0.05, rim='#8a8a94'),
        'visor': MatStyle(ramp('#050404', '#0c0a09', '#15120f', '#201b16', '#2c251e'), [0.08, 0.2, 0.4, 0.65],
                          rim='#6a6a72'),
        'cardigan': MatStyle(ramp('#070806', '#0f110d', '#181b15', '#22261d', '#2d3226', '#393f30', '#474e3c'),
                             PC3.TH6, dither=0.03, rim=rim),
        'shirt': MatStyle(ramp('#121418', '#2a2e34', '#4a4e54', '#727470', '#9a9a90', '#bcbaae'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#a8b4c0'),
        'button': MatStyle(ramp('#0a0806', '#1e1810', '#362a1c', '#4e3e2a'), [0.08, 0.25, 0.5], rim=rim),
        'hair': MatStyle(ramp('#121214', '#2c2c30', '#4e4e52', '#747476', '#9a9998', '#bebab4'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#b0bccc', wrap=0.35),
    })
    head = dict(skull_r=(15.4, 16.6, 20.0), mid_h=(10.8, 7.6, 11.0), fore_h=(11.0, 9.2, 11.6),
                cheek_c=(9.8, 3.0, 9.4), cheek_r=(3.6, 2.6, 3.2), malar_r=(3.6, 3.2, 3.0),
                jaw_angle=(10.0, 15.6, -4.0), jaw_r=(2.2, 2.6, 2.6), low_r=(10.2, 11.2, 11.8),
                chin_c=(0.0, 22.0, 11.0), chin_h=(3.4, 3.2, 3.0), chin_rad=2.2, chin_pt=(3.0, 23.0, 9.6),
                nose_root=(0.0, -1.0, 15.2), nose_tip=(0.0, 8.6, 19.2), tip_r=1.8, nose_r=(1.1, 1.5), ala_x=2.0,
                ala_r=(1.3, 1.2, 1.5), brow_r=(11.8, 2.8, 3.4), mouth_y=15.0, lip_up=(0.0, 14.4, 15.8),
                lip_up_r=(3.6, 0.75, 1.0), lip_lo=(0.0, 16.0, 15.4), lip_lo_r=(3.0, 0.85, 1.0), neck_r=(6.8, 8.2))
    return dict(
        id='blockwart', city='berlin',
        look=dict(key=(0.62, -0.30, 0.72), rim=(-0.80, -0.36, -0.48), ambient=0.09, bg='c4p2_lodge',
                  glow=(0.84, 0.36)),
        head=head, zoom=1.14,
        head_pos=(54.0, 58.0, 0.0), yaw=30.0, pitch=6.0, roll=2.0,
        torso_pos=(54.0, 93.0, -1.5), torso_yaw=14.0, torso=dict(width=0.94, depth=0.98, slope=1.8),
        poses={'neutral': (0, 2, 0), 'concerned': (-2, 5, -2), 'determined': (1, -1, 1), 'surprised': (3, -2, 2)},
        head_items=[lambda M, hp: PCB.flat_cap(M, hp, y0=-12.0, tilt=(12.0, -2.0), r=(16.8, 20.6), h=10.0),
                    lambda M, hp: PC.hair_short(M, hp, hairline=-12.0, front_z=6.0, burn_y=3.4, thick=0.7)],
        torso_items=[
            lambda M, t: PC.layered_front(M, t, outer='coat', mid='cardigan', inner='shirt', v_outer=(0.30, 6.0),
                                          v_mid=(0.22, 3.0), outer_t=2.8, mid_t=1.8, lapel=True, collar_h=4.6,
                                          collar_r=(11.0, 12.6)),
            lambda M, t: PC.surface_buttons(M, t, 3.2, [(1.0, 24.0), (1.4, 33.0)], r=1.1),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=PC3.groups_std({'cap': 2, 'visor': 3, 'cardigan': 5, 'button': 7}),
        tone_passes=[PC.pass_grain('cap', 0.10, seed=201), PC.pass_grain('coat', 0.06, seed=202),
                     PC.pass_knit('cardigan', ribs=34, seed=203), PC.pass_strands('hair', seed=204)],
        rgb_passes=[PC.glasses('round', rim='#4a4038', rim_hi='#c8b890', glare='#b8c4c4', lens_r=(3.6, 2.6), low=2.6),
                    pass_glasses_string()],
        eye=dict(iris='#7a8a90', iris_d='#4a565c', sclera='#c8bcb0', sclera_d='#746c72', lash='#160e10',
                 pupil='#0a0a0c', catch='#f2f0e6'),
        brow=dict(col='#7a7674', col_l='#a8a49e'),
        mouth=dict(line='#3a1a1c', corner='#522828', inner='#1a0a0b', teeth='#a89a86', tongue='#6a3032'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'deep', 'droop'),
            extra=[PC.ear_detail, PC.wrinkles(forehead=3, crow=True, naso=True, under=True), PC.eye_bags(),
                   PC.stubble(density=0.40, seed=205), PC3.cheek_hollow],
            brows={'neutral': dict(arch=0.4, lift_inner=0.9), 'concerned': dict(lift_inner=2.4, lift_outer=-0.5,
                                                                                arch=0.3),
                   'determined': dict(lift_inner=-1.2, arch=0.1, dy=0.4),
                   'surprised': dict(dy=-1.8, arch=1.2, lift_inner=0.8)},
            brow_thick=((2, 2, 2), (1, 1, 1)), brow_pts=((1.6, -3.8, 17.0), (10.4, -3.4, 13.4)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.7), 'concerned': dict(corner_drop=1.1),
                   'determined': dict(corner_drop=0.5), 'surprised': dict(parted=1)}),
        priority={'visor': 1, 'button': 3},
    )


def alexei_press_portrait():
    """Alexei made presentable for the Swede's cameras: chargen_portrait2_cast.alexei shaved (no stubble), the
    ushanka's flaps tied up on the crown (neat, the way the depot's photographs want him), and a NEW cream-white
    wool scarf wound round the neck over the quilted jacket instead of the old grey roll-neck at the throat -- the
    bright clean wool is the first thing one sees.  The depot's evening floodlights behind him."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    from chargen_portrait2_paint import MatStyle, ramp
    spec = PC.alexei()
    spec['id'] = 'alexei_press'
    spec['look'] = dict(spec['look'], bg='c4p2_platform')
    st = dict(spec['styles'])
    st['scarf'] = MatStyle(ramp('#16140f', '#2e2a22', '#4c463c', '#6e675a', '#928a7a', '#b4ac9a', '#d2cab8',
                                '#e8e2d2'), [0.04, 0.09, 0.17, 0.28, 0.42, 0.60, 0.80], dither=0.03, rim='#e4e8ec')
    spec['styles'] = st
    items = list(spec['head_items'])
    items[0] = lambda M, hp: PC.ushanka(M, hp, flaps='up')
    spec['head_items'] = items
    torso = list(spec['torso_items'])
    torso[1] = lambda M, t: PC.scarf_wrap(M, mat='scarf', y=-6.4, r=10.6, tube=4.3, ends=True,
                                          end_pts=[(-1.4, -2.0, 12.0), (-3.0, 8.0, 13.6), (-3.6, 18.0, 14.4)],
                                          seed=221)
    spec['torso_items'] = torso
    groups = dict(spec['groups'])
    groups['scarf'] = 6
    spec['groups'] = groups
    spec['tone_passes'] = list(spec['tone_passes']) + [PC.pass_knit('scarf', ribs=26, seed=222)]
    pri = dict(spec.get('priority', {}))
    pri['scarf'] = 1
    spec['priority'] = pri
    feats = dict(spec['features'])
    feats['extra'] = [PC.ear_detail, PC.eye_bags()]          # shaved: no stubble
    spec['features'] = feats
    return spec


PORTRAITS_C4P2 = {'maria': maria_portrait, 'hanna': hanna_portrait, 'wendt': wendt_portrait,
                  'blockwart': blockwart_portrait, 'alexei_press': alexei_press_portrait}


def build_portraits(ids, char_dir, preview_tag='c4p2_portrait'):
    """Writes the living portraits of `ids` below `char_dir` (an assets/characters directory) + 3x previews."""
    PG, PC, FC, PP, S, PC3, PCB = _portrait_mods()
    for cid, fn in PORTRAITS_C4P2.items():
        PC.CAST.setdefault(cid, fn)
    PG.set_out(char_dir)
    for cid in ids:
        if cid not in PORTRAITS_C4P2:
            continue
        spec, frames, grid = PG.build_char(cid, write=True)
        PG.preview(cid, frames, spec.get('expressions', PG.EXPRESSIONS), tag=preview_tag)
        pj = os.path.join(char_dir, cid, 'portrait.json')
        meta = json.load(open(pj, encoding='utf-8'))
        meta['anim']['spec'] = 'tools/pixelgen/characters_c4p2.py'
        with open(pj, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
            f.write('\n')


# ----------------------------------------------------------------------------------- tables
CAST_C4P2 = {'maria': maria, 'hanna': hanna, 'wendt': wendt, 'blockwart': blockwart, 'guard_karsk': guard_karsk,
             'press_officer': press_officer, 'stapo_civil': stapo_civil, 'alexei_press': alexei_press}
# historical-insignia variants (TECHNICAL_ARCHITECTURE 12.4): sheet_hist.png next to sheet.png, same geometry
CAST_HIST_C4P2 = {'blockwart': lambda: blockwart(hist=True), 'guard_karsk': lambda: guard_karsk(hist=True)}
_NPC = ['idle_side', 'walk_side', 'idle_front', 'talk_side', 'blink_side', 'look_side', 'gesture_side',
        'blink_front', 'talk_front']
_LIFE = ['idle_side', 'walk_side', 'talk_side', 'blink_side', 'look_side', 'gesture_side', 'work_side']
ROWS_C4P2 = {'maria': _NPC + ['work_side'], 'hanna': list(_NPC), 'wendt': list(_NPC),
             'blockwart': _NPC + ['work_side'], 'guard_karsk': list(_LIFE), 'press_officer': list(_LIFE),
             'stapo_civil': list(_LIFE), 'alexei_press': list(CH.PROTAG) + ['carry_side', 'carry_idle_side']}
# figure height (px, idle_side frame 0, incl. headgear) the validator expects
EXPECT_H_C4P2 = {'maria': (41, 45), 'hanna': (42, 46), 'wendt': (46, 50), 'blockwart': (40, 45),
                 'guard_karsk': (44, 49), 'press_officer': (44, 48), 'stapo_civil': (45, 49),
                 'alexei_press': (45, 47)}


# =================================================================================== install / out
def install():
    """Extend the existing pipeline's tables in memory (idempotent).  The part-1 runner's own in-memory tables (and
    through it the Chapter-3 runners') come first, so the validator sees the same expectations as their runs."""
    RC4.install()
    CH.CAST.update(CAST_C4P2)
    CH.ROWS.update(ROWS_C4P2)
    CH.CAST_HIST.update(CAST_HIST_C4P2)
    CHK.EXPECT_H.update(EXPECT_H_C4P2)
    for cid, rows in ROWS_C4P2.items():        # NPC rule: exactly the rows this cast ships
        if cid in LOOKS:
            CHK.REQUIRED[cid] = list(CHK.CONTRACT_ROWS)     # a protagonist's look: the protagonist contract
        else:
            CHK.NPC_MIN[cid] = list(rows)


def set_out(root):
    CH.OUT = os.path.join(root, 'assets', 'characters') if root else CH.OUT
    CH.PREV = os.path.join(CH.OUT, '_preview')
    CHK.OUT = CH.OUT
    RC4.set_out(root)


def _dir_of(cid):
    d = os.path.join(CH.OUT, cid)
    if not os.path.exists(os.path.join(d, 'sheet.json')):
        d = os.path.abspath(os.path.join(HERE, '..', '..', 'assets', 'characters', cid))
    return d


def _load(cid, hist=False):
    d = _dir_of(cid)
    meta = json.load(open(os.path.join(d, 'sheet.json'), encoding='utf-8'))
    name = 'sheet_hist.png' if hist and os.path.exists(os.path.join(d, 'sheet_hist.png')) else 'sheet.png'
    return np.asarray(Image.open(os.path.join(d, name)).convert('RGBA')), meta


def _cell(sheet, meta, anim, f=0):
    r = meta['anims'][anim]['row']
    return Image.fromarray(np.ascontiguousarray(sheet[r * CELL_H:(r + 1) * CELL_H, f * CELL_W:(f + 1) * CELL_W]),
                           'RGBA')


# ----------------------------------------------------------------------------------- previews (<= 1280 px wide)
BGS = [(30, 26, 26, 255), (24, 30, 52, 255), (58, 50, 40, 255), (150, 160, 150, 255)]   # depot, court, station, haze


def preview_lineup(ids):
    """idle_side frame 0 of the new cast between the reference cast (on four backgrounds) and a silhouette strip:
    readability at game scale and no twin silhouettes."""
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
    CH.up(out, k).save(os.path.join(CH.PREV, 'c4p2_lineup.png'))


def preview_rows(cid):
    """Every row of one character on the depot / court / station backgrounds, scaled to <= 1280 px."""
    sheet, meta = _load(cid)
    img = Image.fromarray(sheet, 'RGBA')
    tiles = [CH.on_bg(img, bg) for bg in BGS[:3]]
    out = Image.new('RGBA', (img.width * 3 + 16, img.height), (0, 0, 0, 255))
    for j, t in enumerate(tiles):
        out.paste(t, (j * (img.width + 8), 0))
    k = max(1, min(4, 1280 // out.width))
    CH.up(out, k).save(os.path.join(CH.PREV, f'c4p2_{cid}_rows.png'))


def preview_heads(ids):
    """The heads of idle_side / idle_front / talk_side at 8x (review of the hand-drawn maps)."""
    tiles = []
    for cid in ids:
        sheet, meta = _load(cid)
        for a in ('idle_side', 'idle_front', 'talk_side'):
            if a not in meta['anims']:
                a = 'work_side' if 'work_side' in meta['anims'] else 'gesture_side'
            f = 3 if a in ('talk_side', 'work_side') else 0
            tiles.append(CH.on_bg(_cell(sheet, meta, a, f).crop((4, 0, 28, 30)), (58, 62, 70, 255)))
    per = 6
    lines = (len(tiles) + per - 1) // per
    out = Image.new('RGBA', (per * 26 - 2, lines * 32 - 2), (0, 0, 0, 255))
    for i, t in enumerate(tiles):
        out.paste(t, ((i % per) * 26, (i // per) * 32))
    k = max(1, min(8, 1280 // out.width))
    CH.up(out, k).save(os.path.join(CH.PREV, 'c4p2_heads.png'))


# ----------------------------------------------------------------------------------- checks
EXPR = ['neutral', 'concerned', 'determined', 'surprised']


def check_c4p2(ids=None) -> list[str]:
    """Contract checks beyond characters_check: exact rows, round-2 talk rhythm and a visible gesture / work loop,
    walk speed, living portraits for the speakers (contract, talking mouth, blink, four distinct expressions,
    opaque), hist variants that differ from the neutral sheet only by the insignia pixels, and silhouettes distinct
    from each other and from the existing cast (IoU of idle_side frame 0 <= 0.90)."""
    fails = []
    ids = ids or C4P2_IDS
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
        if list(meta['anims']) != ROWS_C4P2[cid]:
            fails.append(f'{cid}: rows {list(meta["anims"])} != {ROWS_C4P2[cid]}')
        if meta.get('origin') != [16, 54] or meta.get('cell') != [32, 56]:
            fails.append(f'{cid}: cell/origin differ from the contract')
        for row in ('talk_side', 'gesture_side', 'talk_front', 'work_side'):
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
        if cid in LOOKS:
            base_meta = json.load(open(os.path.join(_dir_of(LOOKS[cid]), 'sheet.json'), encoding='utf-8'))
            if gs != base_meta.get('ground_speed', {}).get('walk_side'):
                fails.append(f'{cid}: walks at {gs}, its base at {base_meta.get("ground_speed")}')
            if meta.get('ground_speed', {}).get('carry_side') != gs:
                fails.append(f'{cid}: carry_side does not walk like walk_side')
        elif not 15.0 <= gs <= 30.0:
            fails.append(f'{cid}: walk_side ground_speed {gs} outside 15..30 px/s (an NPC walks slower than 34)')
        if cid in CAST_HIST_C4P2:
            hp = os.path.join(d, 'sheet_hist.png')
            if not os.path.exists(hp):
                fails.append(f'{cid}: sheet_hist.png missing')
            else:
                h = np.asarray(Image.open(hp).convert('RGBA'))
                if h.shape != sheet.shape:
                    fails.append(f'{cid}: sheet_hist.png {h.shape} != sheet.png {sheet.shape}')
                else:
                    diff = (np.abs(h.astype(int) - sheet.astype(int)).sum(-1) > 0)
                    per = diff.reshape(len(meta['anims']), CELL_H, -1, CELL_W).sum((1, 3))
                    if diff.sum() == 0 or per.max() > 24:
                        fails.append(f'{cid}: sheet_hist differs by {diff.sum()} px (max {per.max()} per cell)')
        if cid not in SPEAKERS and cid not in LOOKS:
            if os.path.exists(os.path.join(d, 'portrait.png')):
                fails.append(f'{cid}: a life sheet ships no portrait')
            continue
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
            if LOOKS.get(p) == q or LOOKS.get(q) == p:      # a look is the same person
                continue
            inter = (sil[p] & sil[q]).sum()
            uni = (sil[p] | sil[q]).sum()
            if uni and inter / uni > 0.90:
                fails.append(f'silhouettes of {p} and {q} nearly identical (IoU {inter / uni:.2f})')
    return fails


# props and costume details that must read at 1x (round 10 art review): every frame of the listed rows shows at
# least `need` pixels of the prop (rendered with and without its hook); `reach` = how far (px) the prop may stick out
# in front of the figure (the card box is carried under the arm, never held out like a tray)
PROPS_C4P2 = [
    ('press_officer', ('idle_side', 'walk_side', 'talk_side', 'work_side', 'gesture_side'), 'press_case_side', 12,
     None),
    ('guard_karsk', ('idle_side', 'walk_side', 'talk_side', 'work_side'), 'guard_rifle_side', 12, None),
    ('blockwart', ('idle_side', 'walk_side', 'talk_side', 'look_side', 'blink_side', 'gesture_side'),
     'blockwart_box_side', 10, 2),
    ('blockwart', ('work_side',), 'blockwart_box_side', 8, 6),
    ('wendt', ('idle_side', 'talk_side', 'walk_side'), 'wendt_note_side', 4, None),
    ('maria', ('idle_side', 'talk_side', 'walk_side', 'look_side'), 'maria_needle_side', 2, None),
    ('hanna', ('idle_side', 'talk_side', 'walk_side'), 'hanna_chalk_side', 4, None),
    ('alexei_press', ('carry_side', 'carry_idle_side'), 'guidebook_side', 10, None),
    ('alexei_press', ('idle_side', 'walk_side', 'talk_side'), 'press_scarf_end_side', 4, None),
]


def check_props(ids=None) -> list[str]:
    """Every listed prop is visible (and the card box never reaches out in front of Kuhnert)."""
    from chargen_body import render
    fails = []
    for cid, rows, hook, need, reach in PROPS_C4P2:
        if ids and cid not in ids:
            continue
        spec = CH.CAST[cid]()
        bare = CH.CAST[cid]()
        bare.hooks = {v: [(lay, fn) for lay, fn in lst if fn.__name__ != hook] for v, lst in bare.hooks.items()}
        for row in rows:
            view, fn, fps, loop = CH.ANIMS[row]
            for k, P in enumerate(fn(spec.style)):
                a = render(spec, view, dict(P))[0]
                b = render(bare, view, dict(P))[0]
                diff = np.abs(a.astype(int) - b.astype(int)).sum(-1) > 0
                n = int(diff.sum())
                if n < need:
                    fails.append(f'{cid}: {hook} shows {n} px in {row} frame {k} (needs {need})')
                if reach is not None and n:
                    ys, xs = np.nonzero(diff)
                    body = b[..., 3] > 0
                    band = body[ys.min():ys.max() + 1]
                    front = np.nonzero(band.any(0))[0].max() if band.any() else xs.max()
                    if xs.max() - front > reach:
                        fails.append(f'{cid}: {hook} sticks out {xs.max() - front} px in front of the figure in '
                                     f'{row} frame {k} (at most {reach})')
    return fails


def run_checks(ids=None) -> int:
    print('--- characters_check (tables extended in memory) ---')
    keep = CHK.OUT
    rc = CHK.main()
    CHK.OUT = keep
    print('--- C4P2 contract checks ---')
    fails = check_c4p2(ids) + check_props(ids)
    for f in fails:
        print('  -', f)
    print('OK: C4P2 cast checks pass' if not fails else 'FAIL: C4P2 cast checks')
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
    ids = args or C4P2_IDS
    bad = [c for c in ids if c not in CAST_C4P2]
    if bad:
        print('not a C4P2 character:', bad)
        return 2
    os.makedirs(CH.PREV, exist_ok=True)
    open(os.path.join(CH.PREV, '.gdignore'), 'a').close()
    for cid in ids:
        spec, sheet, nsheet, meta = CH.build_sheet(cid)
        print(f'{cid:14s} rows={",".join(meta["anims"])} size={sheet.shape[1]}x{sheet.shape[0]} '
              f'ground_speed={meta.get("ground_speed", {})}')
        preview_rows(cid)
    preview_heads(ids)
    if 'heads' in opts:
        return 0
    preview_lineup(ids)
    if 'portraits' in opts:
        build_portraits([c for c in ids if c in SPEAKERS or c in LOOKS], CH.OUT)
    return run_checks(ids)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
