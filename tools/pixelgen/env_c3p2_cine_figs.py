"""env_c3p2_cine_figs -- every person in the Chapter-3 part-2 cinematics (LS_C3_Radio / _Fire / _Escape / _Halves);
the API the place generators call (owner: figures stream; round 10 rebuilt on a full anatomical rig).

Round 10: the men were busts with the arms fused into the torso, the reaching arms grew out of the chest and the
smaller people were painted paper-doll silhouettes.  Now every person stands on env_c3p2_cine_body (a skeleton:
pelvis, spine, neck, the portrait heads, shoulder -> elbow -> wrist -> hand with fingers and thumb, hip -> knee ->
foot; garments that follow the bones), the close shots are single 3D scenes in env_c3p2_cine_hero (an arm drawn as
its own sprite is rendered from the same scene as the body, so it leaves the body at the shoulder), the rest are in
env_c3p2_cine_people.

Hero figures (kept names, kept sheet layouts):
  room_alexei / room_konrad      r2 / r3   at the radio in their rooms, from behind (2 frames: breath)
  reg_konrad_sheet               f1        at the sorting table under the green lamp (pose 0 head down, 1 looks up)
  bench_alexei / bench_konrad    h1        on the quay bench from behind and above (2 frames), anchors BENCH_*_AT
Drop-in replacements for persons still painted in the place modules (same size, frames and anchor):
  arm_alexei()        r2   radio.arm_alexei      (4 frames 160 x 72 at ARM_A_AT, rendered from the r2 scene)
  hand_konrad()       r3   radio.hand_konrad     (5 frames 110 x 56 at HAND_K_AT, from the r3 scene)
  walker(kind)        r6   radio.walker          (4 frames, tiny, from behind)
  window_listener(kind, size)  r1  the man at the radio in radio.lit_window
  doorway_figure(i, rect)      f2  the man in the porter's cap in fire.f2_door (figure only, compose it)
  fire_alexei()       f4   fire.f4_alexei        (2 frames 190 x 230 at F4_ALEXEI_AT)
  chute_file()        e1   fire.e1_file          (2 frames)
  hatch_konrad()      e2   fire.e2_konrad        (E2_FRAMES = 6 frames 420 x 220 at E2_KONRAD_AT)
  quay_walk(kind)     h2   quay._walk_frames     (6 frames 44 x 72, facing right)
Extras for empty places: person_sheet(), hotel_guests(), onlookers(), firemen(), quay_crowd(), travellers()
(env_c3p2_cine_people; documented there).
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_cast as CC  # noqa: E402
import env_veltrava_cine_figs as F  # noqa: E402
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402
import env_c3p2_cine_hero as HR  # noqa: E402
import env_c3p2_cine_people as PP  # noqa: E402

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]

ROOM_A_AT = HR.DESK['r2']['at']     # top-left of the r2 figure (absolute frame px)
ROOM_K_AT = HR.DESK['r3']['at']     # top-left of the r3 figure
REG_K_AT = HR.DESK['f1']['at']      # f1
ARM_A_AT = HR.ARM_A_AT              # r2 arm sheet (layout radio.arm_alexei)
ARM_A_N = HR.ARM_A_N
HAND_K_AT = HR.HAND_K_AT            # r3 hand sheet (layout radio.hand_konrad)
HAND_K_N = HR.HAND_K_N
HAND_K_POS = HR.HAND_K_POS
PAD_LINE = HR.PAD_LINE              # r3: where the pencil writes (layout radio.pad_line); the radio sprite covers the
                                    # notepad's left end, so the line starts right of it
REG_POSES = HR.REG_POSES
BENCH_A_AT = HR.BENCH_AT['a']        # h1 (the runtime puts the breath at + (80, 30) / (66, 28))
BENCH_K_AT = HR.BENCH_AT['k']
TH7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]


def _breath(img, dy=1):
    out = np.empty_like(img)
    out[:-dy] = img[dy:]
    out[-dy:] = img[-dy:]
    return out


def _sheet(*frames):
    return np.concatenate(frames, axis=1)


# ----------------------------------------------------------------------------------------- styles
def _alexei_room_styles():
    s = F.alexei_train_styles()
    s['knit'] = MatStyle(F._warm(['#08090B', '#121418', '#1D2025', '#2A2E34', '#3A3E44'],
                                 ['#5A5450', '#7E6A56', '#A4825E']), TH7, dither=0.03, rim='#5f7a86')
    s['hair'] = MatStyle(ramp('#070607', '#100d0c', '#1a1512', '#271f19', '#3a2c21', '#53402c'),
                         [0.06, 0.14, 0.26, 0.42, 0.62], rim='#5d7286')
    return s


def _konrad_room_styles():
    s = F.konrad_train_styles()
    jacket = F._warm(['#060709', '#0D0F13', '#15181E', '#1F232A', '#2B3038'], ['#45403F', '#66574C', '#8C7058'])
    s['coat'] = MatStyle(jacket, TH7, dither=0.03, rim='#6a7f96')
    s['coat_lapel'] = MatStyle(jacket, TH7, rim='#6a7f96')
    s['shirt'] = MatStyle(ramp('#0c0e16', '#262935', '#4a4c56', '#77777b', '#a19d98', '#d2c6b2'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#8ea2b4')
    return s


def _green_styles():
    """Konrad under the green lamp: the lit steps of every material turn green."""
    s = F.konrad_train_styles()
    g = ['#1c3a2c', '#2e5640', '#4a7a5c', '#7fae8c']
    s['coat'] = MatStyle(ramp('#05070d', '#0a0f1d', '#10182b', '#16243a', *g[:3]), TH7, dither=0.03, rim='#4a5f78')
    s['coat_lapel'] = MatStyle(ramp('#05070d', '#0a0f1d', '#10182b', '#16243a', *g[:3]), TH7, rim='#4a5f78')
    s['felt'] = MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#22302c', '#2e4a3c', '#4a7a5c', '#7fae8c'),
                         TH7[:6], dither=0.04, rim='#4a5f78')
    s['brim'] = MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#22302c', '#2e4a3c', '#4a7a5c', '#7fae8c'),
                         TH7[:6], rim='#4a5f78')
    s['scarf'] = MatStyle(ramp('#0e0c0e', '#1f1a1b', '#352d2a', '#3e4a36', '#5a7a52', '#86a878'), TH7[:5],
                          dither=0.03, rim='#6f8494')
    return s


def _fire_styles_alexei():
    """Night by the river: the lit steps of the coats turn orange (the burning wing at the left)."""
    s = F.alexei_train_styles()
    fire = ['#4a2c18', '#7a4a20', '#b87430']
    s['coat'] = MatStyle(F._warm(['#030807', '#0a1411', '#111e18', '#1a2a21'], fire), TH7[:6], dither=0.05,
                         rim='#5f8a96')
    s['coat_lapel'] = MatStyle(F._warm(['#030807', '#0a1411', '#111e18', '#1a2a21'], fire), TH7[:6],
                               rim='#5f8a96')
    s['fur'] = MatStyle(ramp('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#6a4a30', '#94643a', '#bb8a52'),
                        TH7[:6], dither=0.06, rim='#7d9aa2')
    return s


def _fire_styles_konrad():
    s = F.konrad_train_styles()
    fire = ['#4a2818', '#7a3e1c', '#b8642a']
    s['coat'] = MatStyle(F._warm(['#04060b', '#090e1a', '#0f1628', '#162036'], fire), TH7[:6], dither=0.03,
                         rim='#6a86a6')
    s['coat_lapel'] = MatStyle(F._warm(['#04060b', '#090e1a', '#0f1628', '#162036'], fire), TH7[:6],
                               rim='#6a86a6')
    s['felt'] = MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#4a3428', '#7a4e30', '#a8703e'),
                         TH7[:6], dither=0.04, rim='#5a7590')
    s['brim'] = MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#4a3428', '#7a4e30', '#a8703e'),
                         TH7[:6], rim='#5a7590')
    return s


# ----------------------------------------------------------------------------------------- r2 / r3
def room_alexei():
    """r2: Alexei at the table in his room from behind (grey roll-neck, no hat), forearms on the table, lit by
    the dial; 2 frames (breath).  The arm to the knob: arm_alexei()."""
    return _sheet(HR.room_body('a', 0), HR.room_body('a', 1))


def room_konrad():
    """r3: Konrad at the desk from behind (charcoal jacket, shirt cuffs), lit by the desk lamp; 2 frames.  The
    writing hand: hand_konrad()."""
    return _sheet(HR.room_body('k', 0), HR.room_body('k', 1))


def arm_alexei():
    """r2 drop-in for env_c3p2_cine_radio.arm_alexei: ARM_A_N frames of ARM_A_WH at ARM_A_AT -- Alexei's right arm
    in every frame (0 resting on the table, 1 lifting, 2 / 3 on the way, 4 on the knob, 5 turning it); the body
    sprite has no right arm, so there is never a second one (round 11)."""
    return HR.arm_alexei_sheet()


def hand_konrad():
    """r3 drop-in for env_c3p2_cine_radio.hand_konrad: HAND_K_N frames of HAND_K_WH at HAND_K_AT -- Konrad's left
    arm writing with a pencil: HAND_K_POS positions along layout pad_line x 2 strokes, then the same positions with
    the pencil lifted (round 11; the body sprite has no left arm)."""
    return HR.hand_konrad_sheet()


def reg_konrad(pose):
    """f1: Konrad at the sorting table under the green lamp, from behind; pose 0 head down over the halves,
    1 the head lifted (he smells the smoke)."""
    return HR.reg_body(pose)


def reg_konrad_sheet():
    """f1 sheet: REG_POSES frames (0 head bowed, 1 lifting, 2 up, 3 up and turned toward the smoke)."""
    return _sheet(*[reg_konrad(i) for i in range(HR.REG_POSES)])


def _legacy_room_alexei():
    """Alexei at the table, no hat, roll-neck; seen from behind-left; 2 frames (breath)."""
    spec = CC.alexei()
    look = dict(key=(0.80, 0.30, -0.52), rim=(-0.15, -0.60, -0.78), ambient=0.06, wrap=0.12, bg='karsk',
                glow=(0.8, 0.2), fill=0.06, fill_dir=(-0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0, nape=13.0,
                                              back_z=-11.0, thick=1.3),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8))]
    res = F.render(spec, (220, 232), 1.5, (122.0, 66.0), (116.0, 106.0), 156.0, pitch=10.0, roll=0.0,
                   torso_yaw=164.0, torso_pitch=8.0, look=look,
                   torso_kw=dict(mat='knit', width=1.05, depth=1.05, slope=1.0, arm_out=1.05, lean=4.0,
                                 arm_l=((-30.0, 56.0, 8.0), (-14.0, 52.0, 34.0)),
                                 arm_r=((30.0, 54.0, 6.0), (16.0, 48.0, 30.0))),
                   head_items=head_items, torso_items=torso_items, styles=_alexei_room_styles(),
                   tone_passes=[F.pass_hair_back('hair'), CC.pass_knit('knit', ribs=30)],
                   cache_key=('c3p2_room_alexei', _SRC))
    f = res['rgba']
    return _sheet(f, _breath(f))


def _legacy_room_konrad():
    """Konrad at the desk, no hat, charcoal jacket over the white shirt; from behind-right; 2 frames."""
    spec = CC.konrad()
    look = dict(key=(-0.80, 0.30, -0.50), rim=(0.15, -0.62, -0.76), ambient=0.06, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.06, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.3),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=8.0,
                                               collar_r=(11.0, 13.0), coat_t=2.0)]
    res = F.render(spec, (200, 232), 1.5, (84.0, 64.0), (86.0, 104.0), 200.0, pitch=12.0, roll=0.0,
                   torso_yaw=194.0, torso_pitch=8.0, look=look,
                   torso_kw=dict(width=0.96, depth=1.0, slope=1.25, arm_out=1.05, lean=4.0,
                                 arm_l=((-29.0, 54.0, 8.0), (-12.0, 50.0, 34.0)),
                                 arm_r=((29.0, 56.0, 6.0), (14.0, 50.0, 30.0))),
                   head_items=head_items, torso_items=torso_items, styles=_konrad_room_styles(),
                   tone_passes=[CC.pass_grain('coat', 0.04, seed=4), F.pass_hair_back('hair')],
                   cache_key=('c3p2_room_konrad', _SRC))
    f = res['rgba']
    return _sheet(f, _breath(f))


# ----------------------------------------------------------------------------------------- f1
def _legacy_reg_konrad(pose):
    """Konrad at the sorting table under the green lamp, seen from behind-left; pose 0 head down over the
    papers, pose 1 the head lifted (he smells the smoke)."""
    spec = CC.konrad()
    look = dict(key=(0.15, -0.88, -0.45), rim=(-0.55, -0.55, -0.62), ambient=0.05, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.05, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape')]
    pitch = 26.0 if pose == 0 else -6.0
    yaw = 162.0 if pose == 0 else 150.0
    res = F.render(spec, (200, 232), 1.45, (96.0, 62.0 + (6.0 if pose == 0 else 0.0)), (100.0, 104.0), yaw,
                   pitch=pitch, roll=0.0, torso_yaw=168.0, torso_pitch=14.0, look=look,
                   torso_kw=dict(width=0.96, depth=1.0, slope=1.25, arm_out=1.08, lean=8.0,
                                 arm_l=((-30.0, 52.0, 10.0), (-16.0, 54.0, 38.0)),
                                 arm_r=((30.0, 52.0, 10.0), (16.0, 54.0, 38.0))),
                   head_items=head_items, torso_items=torso_items, styles=_green_styles(),
                   tone_passes=[CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3),
                                CC.pass_grain('coat', 0.04, seed=4), F.pass_hair_back('hair')],
                   cache_key=('c3p2_reg_konrad', pose, _SRC))
    return res['rgba']


# ----------------------------------------------------------------------------------------- h1
def bench_alexei():
    """h1: Alexei on the quay bench from behind and above, forearms in his lap; 4 frames (round 11): breath 0 / 1,
    leaning half / fully toward the middle of the bench (the reach across for the other man's pages)."""
    return _sheet(*[HR.bench_body('a', b, l) for b, l in HR.BENCH_FRAMES])


def bench_konrad():
    return _sheet(*[HR.bench_body('k', b, l) for b, l in HR.BENCH_FRAMES])


# ----------------------------------------------------------------------------------------- drop-in people
chute_file = HR.chute_file_sheet            # e1 (fire.e1_file): 2 frames 220 x 130, bottom-anchored
hatch_konrad = HR.hatch_konrad_sheet        # e2 (fire.e2_konrad): E2_FRAMES frames 420 x 220 at E2_KONRAD_AT
E2_KONRAD_AT = HR.E2_AT
E2_FRAMES = HR.E2_FRAMES
walker = PP.square_walker_sheet
window_listener = PP.window_listener
doorway_figure = PP.doorway_figure
fire_alexei = PP.fire_alexei_sheet
quay_walk = PP.quay_walk_sheet
F4_ALEXEI_AT = PP.F4_ALEXEI_AT
person_sheet = PP.person_sheet
hotel_guests = PP.hotel_guests
onlookers = PP.onlookers
firemen = PP.firemen
quay_crowd = PP.quay_crowd
travellers = PP.travellers
