"""chargen_portrait2_berlin -- dialogue busts of the evicted Berlin family (round 8, feel_r8).

The mother and the father of the sealed flat speak in the plaza (task „Das Foto“ and their chats) and showed the
silhouette placeholder.  Both are built on the round-2 pipeline exactly like the other Berlin speakers
(chargen_portrait2_cast: Konrad, Emil, the porter, the librarian) and match their sprites (chargen_cast.py):
  berlin_father  -- forties, tired: grey tweed flat cap over short dark hair, no moustache, bags under the eyes,
                    day-old stubble; brown wool coat with lapels, grey knitted scarf.
  berlin_mother  -- late thirties, worried: small dark felt pillbox with a wine ribbon worn towards the back of the
                    head, auburn hair swept back into a low chignon; plum coat, oatmeal knitted scarf wrapped high.
Imported by chargen_portrait2.py (registers both in chargen_portrait2_cast.CAST).  Deterministic, no image input.
    py -3 -P tools/pixelgen/chargen_portrait2.py berlin_father berlin_mother
Provenance: documentation/asset_manifest_parts/feel_r8.md.
"""
from __future__ import annotations

import numpy as np

import chargen_portrait2_cast as PC
import chargen_portrait2_face as FC
import chargen_portrait2_sdf as S
from chargen_portrait2_cast import (BROWS_STD, FEMALE, MOUTH_STD, SKIN_BERLIN, _female_eyes, coat_layers,
                                    ear_detail, eye_bags, hair_short, pass_grain, pass_knit, pass_strands,
                                    scarf_wrap, skin_styles, stubble, wrinkles)
from chargen_portrait2_paint import MatStyle, ramp
from chargen_portrait_c3 import SOFT, hair_swept, lip_of

E = S.Ellipsoid
RIM_B = '#6e8fa6'          # Berlin dusk rim, as Konrad / Emil / the porter
TH6 = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]


def look_b(**kw):
    d = dict(key=(0.55, -0.42, 0.72), rim=(-0.80, -0.35, -0.50), ambient=0.07, bg='berlin', glow=(0.80, 0.18))
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------- head items
def flat_cap(M, hp, y0=-12.8, z0=-4.0, tilt=(9.0, -2.0), r=(17.8, 21.6), h=12.8, visor_tilt=10.0,
             visor_r=(12.0, 7.6)):
    """Berlin flat cap („Schiebermütze“): a soft tweed dome hugging the skull, drawn forward over a short cloth
    peak, the front lower than the back.  No band ribbon, no cord, no badge.  Frame origin = centre of the
    lower edge (head-local y0 / z0), like peaked_cap; the head is clipped to the cap's inside."""
    mc, mv = M('cap'), M('visor')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    shell = E((0.0, -0.8, 1.8), (rx + 1.0, h, rz + 2.4), mc)
    dome = S.Inter(shell, S.Fn(lambda P: P[:, 1] - 0.2, mc))
    band = S.EllipticCylinder((0, -1.5, 0.6), rx + 0.3, rz + 0.5, 1.5, mc, e=0.6)
    vf = S.Frame((0.0, -0.6, rz - 1.0), S.rot(0, visor_tilt, 0))
    visor = S.Inter(S.EllipticCylinder((0, 0, -2.0), visor_r[0], visor_r[1], 0.6, mv, e=0.45),
                    S.Fn(lambda P: -(P[:, 2] - 0.3), mv))
    visor = S.Xform(visor, frame=vf)
    hat = S.Union([dome, band, visor], k=[0.6, 0.3])
    allowed = S.Union([S.Offset(E((0.0, -0.8, 1.8), (rx + 1.0, h, rz + 2.4), mc), -0.6),
                       S.Fn(lambda P: -(P[:, 1] - 0.8), mc)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def pillbox(M, hp, y0=-24.6, z0=-8.0, tilt=(-18.0, -6.0), r=(11.8, 13.6), h=6.6):
    """Small felt pillbox worn towards the back of the head, a ribbon round its base (sits on the hair; nothing
    of the head is clipped)."""
    mf, mr = M('felt'), M('ribbon')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    body = S.EllipticCylinder((0, -h / 2 - 0.4, 0), rx, rz, h / 2, mf, e=1.6)
    band = S.EllipticCylinder((0, -1.3, 0), rx + 0.35, rz + 0.35, 1.0, mr, e=0.4)
    return dict(node=S.Xform(S.Union([body, band], k=0.3), frame=hf))


# ----------------------------------------------------------------------------------- the father
def berlin_father():
    sk = ramp('#0b0d16', '#1e1b28', '#3a2a35', '#603d43', '#8b5a51', '#b37a62', '#d29e80', '#e8c4a2')
    styles = skin_styles(sk, RIM_B, lip_of(sk, warm=2))
    brown = ramp('#07060a', '#110d10', '#1d1616', '#2c211d', '#3d2e26', '#523e32', '#6a5242')
    tweed = ramp('#08090c', '#121318', '#1d1e23', '#2b2b30', '#3b3a3e', '#4f4d4f', '#666262', '#7d7874')
    styles.update({
        'coat': MatStyle(brown, TH6, dither=0.05, rim=RIM_B),
        'coat_lapel': MatStyle(brown, TH6, rim=RIM_B),
        'shirt': MatStyle(ramp('#0c0d12', '#23252c', '#41434a', '#66676b', '#8c8b8a', '#aeaaa2'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#9eb2c2'),
        'cap': MatStyle(tweed, [0.03, 0.08, 0.15, 0.25, 0.38, 0.55, 0.75], dither=0.06, rim='#5d7590'),
        'visor': MatStyle(tweed, [0.04, 0.10, 0.18, 0.29, 0.43, 0.60, 0.80], dither=0.0, rim='#5d7590'),
        'hair': MatStyle(ramp('#07080d', '#141218', '#221b1d', '#33282a', '#463634'),
                         [0.05, 0.14, 0.30, 0.52], rim='#4e6278'),
        'scarf': MatStyle(ramp('#0a0b0e', '#16171c', '#24252b', '#34353c', '#46474e', '#5b5c62', '#727378'),
                          TH6, dither=0.04, rim='#7f93a0'),
    })
    head = dict(mid_h=(11.6, 7.2, 11.8), jaw_angle=(11.4, 15.8, -3.8), low_r=(11.6, 11.2, 12.6),
                cheek_c=(10.6, 3.4, 9.8), cheek_r=(4.6, 3.2, 4.0), nose_tip=(0.0, 9.6, 19.6), tip_r=2.4,
                ala_x=2.6, ala_r=(1.6, 1.5, 1.9), nose_r=(1.5, 1.9), chin_h=(4.6, 3.4, 3.4), neck_r=(8.8, 10.2))
    return dict(
        id='berlin_father', city='berlin', look=look_b(),
        head=head, zoom=1.14,
        head_pos=(55.0, 56.0, 0.0), yaw=29.0, pitch=4.0, roll=0.0,
        torso_pos=(55.0, 92.0, -0.5), torso_yaw=13.0, torso=dict(width=1.06, depth=1.08, slope=1.1),
        # a tired man: the head sinks a little when worried, lifts only briefly when surprised
        poses={'neutral': (0, 2, 0), 'concerned': (-2, 6, -2), 'determined': (1, 0, 1), 'surprised': (2, -3, 1)},
        head_items=[lambda M, hp: flat_cap(M, hp),
                    lambda M, hp: hair_short(M, hp, hairline=-14.6, front_z=8.0, burn_y=2.0)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.34, v_top=3.5, lapel=True, collar_h=5.0,
                                     collar_r=(12.2, 13.6)),
            lambda M, t: scarf_wrap(M, y=-6.0, r=10.6, tube=4.6, ends='drape', seed=11),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'cap': 2, 'visor': 3, 'coat': 4,
                'coat_lapel': 8, 'shirt': 5, 'scarf': 6, 'body': 4},
        tone_passes=[pass_grain('cap', 0.10, seed=23), pass_grain('coat', 0.05, seed=24), pass_knit('scarf', ribs=24),
                     pass_strands('hair', seed=25)],
        eye=dict(iris='#4e4434', iris_d='#2c261c', sclera='#c2b8ac', sclera_d='#6e6a74', lash='#120a0c',
                 pupil='#0a0808', catch='#efe6d2'),
        brow=dict(col='#221a1a', col_l='#3e302c'),
        mouth=dict(line='#3c1a1e', corner='#56282a', inner='#1a0b0d', teeth='#b4a794', tongue='#6c3034'),
        features=dict(extra=[ear_detail, wrinkles(forehead=2, crow=True, naso=True, under=True), eye_bags(),
                             stubble(density=0.38, seed=27)],
                      eyes=FC.eye_shapes(FC.EYES, 'hooded'),
                      brows={**BROWS_STD, 'neutral': dict(arch=0.4, lift_inner=0.5)},
                      brow_thick=((2, 2, 1), (2, 1, 1)), brow_pts=((1.5, -4.0, 17.2), (10.6, -3.4, 13.4)),
                      nostril='wide', mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.8)}),
        priority={'visor': 2, 'scarf': 1},
    )


# ----------------------------------------------------------------------------------- the mother
def berlin_mother():
    sk = SKIN_BERLIN
    styles = skin_styles(sk, RIM_B, lip_of(sk, warm=8))
    plum = ramp('#07050a', '#110b12', '#1c121c', '#2a1a28', '#3a2436', '#4e3048', '#653e5c')
    styles.update({
        'coat': MatStyle(plum, TH6, dither=0.05, rim=RIM_B),
        'coat_lapel': MatStyle(plum, TH6, rim=RIM_B),
        'shirt': MatStyle(ramp('#0b0a10', '#1a1820', '#2a2730'), [0.1, 0.3], rim=RIM_B),
        'hair': MatStyle(ramp('#080406', '#170a0a', '#2a120e', '#401c12', '#582716', '#71341c', '#8a4426'),
                         [0.04, 0.10, 0.20, 0.34, 0.52, 0.74], rim='#7a6a7e', wrap=0.25),
        'felt': MatStyle(ramp('#050508', '#0b0a10', '#131118', '#1d1a22', '#29252e', '#36313b'),
                         [0.05, 0.13, 0.26, 0.45, 0.68], dither=0.04, rim='#56708a'),
        'ribbon': MatStyle(ramp('#0a0406', '#1a080c', '#2e0f15', '#44171e', '#5c2229'),
                           [0.06, 0.16, 0.32, 0.55], rim='#7a5a6a'),
        'scarf': MatStyle(ramp('#0e0c0e', '#1f1a1b', '#352d2a', '#4e4436', '#695c49', '#85765e', '#a09078',
                               '#b8a991'), [0.05, 0.12, 0.22, 0.35, 0.50, 0.68, 0.88], dither=0.04, rim='#7f93a0'),
    })
    head = dict(FEMALE)
    head.update(SOFT)
    head.update(skull_r=(15.4, 16.4, 19.6), mid_h=(10.8, 6.8, 11.0), cheek_c=(10.0, 2.6, 10.0),
                cheek_r=(4.0, 3.0, 3.6), jaw_angle=(9.6, 14.0, -4.2), low_r=(10.6, 10.2, 12.0),
                chin_c=(0.0, 21.4, 11.4), chin_h=(3.5, 2.9, 3.0), chin_rad=2.8,
                nose_root=(0.0, -1.2, 15.4), nose_tip=(0.0, 8.9, 19.2), nose_r=(1.2, 1.6), tip_r=2.05,
                ala_x=2.1, ala_r=(1.35, 1.3, 1.65), eye_x=6.5, lip_up_r=(3.7, 1.15, 1.35), lip_lo_r=(3.2, 1.5, 1.4),
                brow_r=(11.2, 2.0, 2.8), neck_r=(6.6, 8.0))
    return dict(
        id='berlin_mother', city='berlin', look=look_b(key=(0.56, -0.43, 0.71)),
        head=head, zoom=1.17, smooth=2,
        head_pos=(55.0, 56.0, 0.0), yaw=31.0, pitch=2.0, roll=-1.0,
        torso_pos=(55.5, 91.0, -0.5), torso_yaw=14.0, torso=dict(width=0.90, depth=0.96, slope=1.4),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -2), 'determined': (2, -1, 1), 'surprised': (3, -3, 1)},
        head_items=[lambda M, hp: hair_swept(M, hp, hairline=-13.0, part_x=5.0, seed=131),
                    lambda M, hp: pillbox(M, hp)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.24, v_top=5.0, lapel=True, collar_h=6.0, collar_r=(11.8, 13.4)),
            lambda M, t: scarf_wrap(M, y=-7.4, r=10.0, tube=4.6, ends=True,
                                    end_pts=[(1.0, -3.0, 11.8), (2.6, 7.0, 13.4), (3.2, 17.0, 14.2)], seed=13),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'felt': 2, 'ribbon': 2, 'coat': 4,
                'coat_lapel': 8, 'shirt': 5, 'scarf': 6, 'body': 4},
        tone_passes=[pass_strands('hair', seed=33), pass_knit('scarf', ribs=30), pass_grain('coat', 0.05, seed=34),
                     pass_grain('felt', 0.06, seed=35)],
        eye=dict(iris='#4a5a52', iris_d='#2a3630', sclera='#c6bdb1', sclera_d='#6e6a76', lash='#0e080c',
                 pupil='#08070a', catch='#f2ead8'),
        brow=dict(col='#2a1410', col_l='#4a2a1e'),
        mouth=dict(line='#4a1a20', corner='#602a2e', inner='#1a0a0d', teeth='#bcaea0', tongue='#733035'),
        features=dict(
            eyes=FC.eye_shapes(_female_eyes(), 'hooded'),
            extra=[ear_detail, wrinkles(forehead=1, crow=False, naso=True, under=True)],
            brows={'neutral': dict(arch=1.0, lift_inner=0.6), 'concerned': dict(lift_inner=2.4, lift_outer=-0.4, arch=0.6),
                   'determined': dict(lift_inner=-1.2, arch=0.4, dy=0.4),
                   'surprised': dict(dy=-1.8, arch=1.5, lift_inner=0.6)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.8, -4.1, 17.0), (10.2, -3.9, 13.2)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.4), 'concerned': dict(corner_drop=1.1),
                   'determined': dict(corner_drop=0.5), 'surprised': dict(parted=2)},
        ),
        priority={'ribbon': 2, 'scarf': 1},
    )


PC.CAST['berlin_father'] = berlin_father
PC.CAST['berlin_mother'] = berlin_mother
