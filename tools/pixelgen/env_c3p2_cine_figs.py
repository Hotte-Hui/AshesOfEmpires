"""env_c3p2_cine_figs -- Konrad and Alexei for the Chapter-3 part-2 cinematics (owner: cinematics stream).

Sculpted and lit with the signed-distance pipeline of the dialogue portraits through the round-6 cinematic
figure module env_veltrava_cine_figs (render(), seated torso, hair from behind; chargen_portrait2_* specs give the
heads, hats, hair and coat materials -- all imported read-only), so the men keep the faces, hats and coats the
player knows.  Seen from behind in every shot (no faces to animate):

  room_alexei   r2: at the table in his room, no hat, the grey roll-neck, lit by the radio dial (warm, front right)
  room_konrad   r3: at the desk in his room, no hat, the charcoal jacket, lit by the desk lamp (warm, front left)
  reg_konrad    f1: at the sorting table, hat and coat, the green lamp above him; pose 0 head down, 1 looks up
  bench_alexei / bench_konrad   h1: on the quay bench from behind and above, hats and coats, fire light from the
                left (the burning wing), cold sky light from the right
Renders are memoised on disk by env_veltrava_cine_figs (key = pipeline sources + call arguments); the cache keys
here also carry a hash of this file, so editing a style or garment here re-renders.
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

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]

ROOM_A_AT = (58, 84)                 # top-left of the r2 figure (absolute frame px)
ROOM_K_AT = (466, 84)                # top-left of the r3 figure
REG_K_AT = (330, 78)                 # f1
BENCH_A_AT = (112, 150)              # h1
BENCH_K_AT = (378, 148)
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


def room_konrad():
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
def reg_konrad(pose):
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


def reg_konrad_sheet():
    return _sheet(reg_konrad(0), reg_konrad(1))


# ----------------------------------------------------------------------------------------- h1
def bench_alexei():
    spec = CC.alexei()
    look = dict(key=(-0.80, -0.05, -0.58), rim=(0.62, -0.42, -0.66), ambient=0.05, wrap=0.10, bg='karsk',
                glow=(0.8, 0.2), fill=0.05, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.ushanka(M, hp, flaps='down'),
                  lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0, nape=13.0,
                                              back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=12.0, collar_r=(13.4, 14.8)),
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8)),
                   lambda M, t: F.band_back(M, t, 3.4, (6.0, 30.0), 50.0, 3.0, 'strap', y_range=(8.0, 92.0))]
    res = F.render(spec, (150, 170), 1.0, (78.0, 44.0), (76.0, 74.0), 172.0, pitch=24.0, roll=2.0,
                   torso_yaw=176.0, torso_pitch=22.0, look=look,
                   torso_kw=dict(width=1.05, depth=1.05, slope=1.0, arm_out=1.10, lean=6.0,
                                 arm_l=((-30.0, 58.0, 10.0), (-18.0, 64.0, 34.0)),
                                 arm_r=((30.0, 58.0, 10.0), (18.0, 64.0, 34.0))),
                   head_items=head_items, torso_items=torso_items, styles=_fire_styles_alexei(),
                   tone_passes=[CC.pass_fur('fur'), CC.pass_stitches('coat', 5.0), F.pass_hair_back('hair'),
                                CC.pass_knit('knit', ribs=30)],
                   cache_key=('c3p2_bench_alexei', _SRC))
    f = res['rgba']
    return _sheet(f, _breath(f))


def bench_konrad():
    spec = CC.konrad()
    look = dict(key=(-0.82, -0.05, -0.56), rim=(0.60, -0.45, -0.66), ambient=0.05, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.05, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape')]
    res = F.render(spec, (140, 170), 1.0, (70.0, 44.0), (72.0, 74.0), 186.0, pitch=24.0, roll=-2.0,
                   torso_yaw=182.0, torso_pitch=22.0, look=look,
                   torso_kw=dict(width=0.96, depth=1.0, slope=1.25, arm_out=1.08, lean=6.0,
                                 arm_l=((-29.0, 58.0, 10.0), (-17.0, 64.0, 34.0)),
                                 arm_r=((29.0, 58.0, 10.0), (17.0, 64.0, 34.0))),
                   head_items=head_items, torso_items=torso_items, styles=_fire_styles_konrad(),
                   tone_passes=[CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3),
                                CC.pass_grain('coat', 0.04, seed=4), F.pass_hair_back('hair')],
                   cache_key=('c3p2_bench_konrad', _SRC))
    f = res['rgba']
    return _sheet(f, _breath(f))
