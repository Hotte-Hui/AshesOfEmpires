"""env_veltrava_cine_people -- the people of the Chapter-3 part-1 cinematics (LS_C3_Trains, LS_C3_ToHall,
LS_C3_Close), round 10.  Owner: the figures stream of this film family.

Every extra -- travellers, porters, railwaymen, police of the Free City, delegates, the woman with the milk sled,
passengers at the train windows -- is a full body built from the same signed-distance rig as Konrad and Alexei
(env_veltrava_cine_rig: articulated arms with elbows and hands, legs with knees and shoes, coats that open with
the stride) and painted by the portrait pipeline, so a 14 px figure on the river bank and a 70 px delegate in the
palais share proportions, light and outline rules with the heroes.  Proportions are measured in heads (7.5 heads
tall; shoulders 2 heads wide for men); poses are joint angles (walk cycles are 8 frames).

PUBLIC API (for the places builder -- call these, do not copy the code):
  person_sheet(kind, height, frames=8, pose='walk', facing=1, light='dawn', seed=0, **opts) -> RGBA sheet
        frames side by side; each frame is box(kind, height) = (w, h) px with the soles on the bottom row
        (anchor = (w // 2, h - 1)).  kinds: see KINDS (man_coat, man_cap, woman_scarf, woman_coat, child,
        porter, railwayman, police, guard, delegate, usher, woman_sled, fisher, sweeper).
        pose: 'walk' (cycle), 'stand' (breathing idle, 4 frames), 'sit' (on a box / bench), 'wait' (hands in
        pockets).  light presets: 'dawn', 'day_overcast', 'palais', 'night_lamp', 'night'.
  passenger_strip(n, w, h, side, seed, light) -> RGBA: heads and shoulders of passengers behind a lit carriage
        window (w x h px), facing the glass or reading, for train sprites (side = 'de' | 'su').
  window_figure(who, ww, wh, state) -> RGBA: Konrad / Alexei stepping to a lit hotel window (LS_C3_Close n2).
  build(out_dir, layout) -> writes the atlases of every cast entry below and returns the cast list
        (assets/cinematics/ch3/people/*.png + layout['people'] entries consumed by
        scenes/cinematics/ch3_common/c3_people.gd).
Deterministic numpy; renders are cached on disk by the rig (ASHES_NO_CACHE=1 disables the cache).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_anat as A   # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402
import env_veltrava_cine_rig as R    # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
TH5 = [0.06, 0.15, 0.30, 0.52]
TH6 = [0.05, 0.12, 0.24, 0.40, 0.60]
TH7 = [0.04, 0.09, 0.17, 0.28, 0.42, 0.62]


# ------------------------------------------------------------------------------------------------ palettes
def _r(*h):
    return ramp(*h)


CLOTH = {
    'navy': _r('#06080e', '#0d1220', '#161e33', '#222d47', '#334262', '#4d5d7c', '#7684a0'),
    'charcoal': _r('#07080a', '#111317', '#1b1e23', '#282c33', '#3a3f47', '#555b64', '#7a808a'),
    'brown': _r('#0c0807', '#1a110c', '#2a1b13', '#3e2a1c', '#583d28', '#7a5838', '#9e7a52'),
    'camel': _r('#120d08', '#241a10', '#3a2a18', '#574022', '#7a5a32', '#9e7a48', '#c4a06a'),
    'green': _r('#050a09', '#0b1512', '#12201a', '#1b2c23', '#26392d', '#3d5240', '#5a7356'),
    'grey': _r('#0b0c0e', '#17191d', '#262a30', '#383d45', '#50565f', '#6e757e', '#959ca5'),
    'black': _r('#040405', '#0a0a0d', '#121216', '#1c1c22', '#2a2a32', '#3e3e48', '#5a5a66'),
    'police': _r('#05070c', '#0b1019', '#121b2a', '#1b283d', '#273a55', '#3a5272', '#5a7494'),
    'rail': _r('#06070a', '#0e1116', '#171c24', '#232a35', '#323b49', '#4a5464', '#6a7686'),
    'red': _r('#140606', '#2a0c0b', '#4a1712', '#6e231a', '#8f3524', '#b04a32', '#cc6a48'),
    'wine': _r('#0e0508', '#1e0a10', '#331219', '#4a1c24', '#632a30', '#7e3c3e', '#9a5450'),
    'mustard': _r('#120e06', '#261d0a', '#3e3010', '#5c4618', '#7e6224', '#a08034', '#c4a04c'),
    'teal': _r('#04090a', '#0a1517', '#102124', '#183034', '#234446', '#3a5e5c', '#5a7e78'),
    'cream': _r('#14120e', '#2a2620', '#46403a', '#6a6256', '#8e8474', '#b2a690', '#d6c8ae'),
    'fur': _r('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#574b3f', '#7a6247', '#9c7d58'),
    'leather': _r('#0a0606', '#180e0b', '#2a1810', '#3e2416', '#583420', '#7a4a2c', '#9a6440'),
    'boot': _r('#040404', '#0a0a0b', '#141416', '#1e1e22', '#2c2c32', '#44444c'),
    'felt_boot': _r('#0a0a0b', '#18181a', '#26262a', '#36363c', '#4a4a52', '#66666e'),
    'brass': _r('#0e0a04', '#2a1e0a', '#4a3612', '#7a5a22', '#a87e36', '#d4a84e', '#f2d08a'),
    'steel': _r('#07080a', '#14171c', '#22262d', '#323840', '#464d55', '#5e666e', '#8593a3'),
    'snowy': _r('#3a4859', '#4f5e70', '#687789', '#8593a3', '#a1aab7', '#c2c9d2', '#dee2e7'),
    'wood': _r('#0a0705', '#1a120c', '#2a1d12', '#3e2b1a', '#583e24', '#765630', '#946e40'),
}
SKINS = {
    'light': _r('#0b0d16', '#1d1b28', '#372a37', '#5b3b43', '#86584f', '#b27b63', '#d4a17f', '#ecc9a1'),
    'ruddy': _r('#080d14', '#1a1b24', '#36262e', '#5c3637', '#8a5242', '#b5724f', '#d69868', '#efc490'),
    'old': _r('#0a0c12', '#1c1a22', '#352a30', '#57403f', '#7e5c52', '#a47e6c', '#c8a48c', '#e2c6ae'),
}
HAIR = {
    'dark': _r('#07080d', '#141218', '#221a1e', '#33262a', '#4a3533', '#614640'),
    'brown': _r('#0b0a0b', '#1b1614', '#2d241e', '#45372b', '#5e4b39', '#786049'),
    'grey': _r('#141518', '#2a2b2f', '#45464a', '#64656a', '#86878c', '#a8a9ad'),
    'blond': _r('#14100a', '#2e2414', '#4e3e22', '#74603a', '#9a8456', '#c0aa78'),
}

LIGHTS = {
    # key: direction TOWARD the light (view space, y down), rim, ambient
    'dawn': dict(key=(0.70, -0.45, 0.55), rim=(0.85, -0.30, -0.45), ambient=0.10, wrap=0.20, fill=0.10,
                 fill_dir=(-0.4, -0.6, 0.7), ao=0.4, bg='veltrava', glow=(0.8, 0.2)),
    'day_overcast': dict(key=(0.35, -0.80, 0.50), rim=(-0.6, -0.5, -0.6), ambient=0.08, wrap=0.25, fill=0.07,
                         fill_dir=(0.0, -0.3, 1.0), ao=0.45, bg='veltrava', glow=(0.8, 0.2)),
    'palais': dict(key=(0.55, -0.65, 0.50), rim=(-0.75, -0.35, -0.55), ambient=0.08, wrap=0.15, fill=0.08,
                   fill_dir=(-0.3, -0.2, 1.0), ao=0.45, bg='palais', glow=(0.8, 0.2)),
    'night_lamp': dict(key=(-0.45, -0.75, 0.45), rim=(0.80, -0.30, -0.50), ambient=0.05, wrap=0.10, fill=0.05,
                       fill_dir=(0.0, 0.6, 0.8), ao=0.4, bg='veltrava', glow=(0.8, 0.2)),
    'night': dict(key=(0.30, -0.60, 0.70), rim=(-0.80, -0.30, -0.50), ambient=0.04, wrap=0.10, fill=0.04,
                  fill_dir=(0.0, -0.3, 1.0), ao=0.4, bg='veltrava', glow=(0.8, 0.2)),
}
VGAIN = {'dawn': 0.78, 'day_overcast': 0.72, 'palais': 0.85, 'night_lamp': 0.62, 'night': 0.7}
RIMS = {'dawn': '#e8dcd6', 'day_overcast': '#a1aab7', 'palais': '#7a5636', 'night_lamp': '#8a5a36',
        'night': '#4f5e70'}


def _style(rmp, light, dither=0.0, rim=None, th=None):
    n = len(rmp)
    if th is None:
        base = [0.07, 0.16, 0.28, 0.44, 0.64, 0.84, 0.95]
        th = base[:n - 1]
    return MatStyle(rmp, th, dither=dither, rim=rim or RIMS.get(light, '#a1aab7'))


# ------------------------------------------------------------------------------------------------ figure kinds
# each kind: clothes and accessories; colours by name from CLOTH / SKINS / HAIR
KINDS = {
    'man_coat': dict(sex='m', coat='charcoal', coat_len=0.80, hat='fedora', hat_col='black', scarf='camel',
                     legs='charcoal', shoes='boot'),
    'man_cap': dict(sex='m', coat='brown', coat_len=0.55, hat='cap', hat_col='charcoal', scarf=None, legs='grey',
                    shoes='boot'),
    'woman_scarf': dict(sex='f', coat='charcoal', coat_len=0.92, hat='headscarf', hat_col='red', scarf=None,
                        legs='black', shoes='felt_boot', skin='old'),
    'woman_coat': dict(sex='f', coat='wine', coat_len=0.88, hat='beret', hat_col='black', scarf='cream',
                       legs='black', shoes='boot'),
    'child': dict(sex='c', coat='mustard', coat_len=0.55, hat='knit', hat_col='red', scarf='red', legs='navy',
                  shoes='felt_boot', scale=0.68),
    'porter': dict(sex='m', coat='rail', coat_len=0.62, hat='peaked', hat_col='rail', scarf=None, legs='rail',
                   shoes='boot', apron=True),
    'railwayman': dict(sex='m', coat='rail', coat_len=0.85, hat='peaked', hat_col='rail', scarf=None, legs='rail',
                       shoes='boot', lantern=True),
    'police': dict(sex='m', coat='police', coat_len=0.88, hat='shako', hat_col='police', scarf=None, legs='police',
                   shoes='boot', belt='leather', cape=False),
    'guard': dict(sex='m', coat='grey', coat_len=0.95, hat='ushanka', hat_col='fur', scarf=None, legs='grey',
                  shoes='boot', rifle=True, belt='leather'),
    'delegate': dict(sex='m', coat='black', coat_len=0.82, hat='homburg', hat_col='black', scarf='grey',
                     legs='black', shoes='boot', briefcase=True, skin='old', hair='grey'),
    'usher': dict(sex='m', coat='teal', coat_len=0.60, hat=None, hat_col='teal', scarf=None, legs='black',
                  shoes='boot', braid=True, hair='grey', skin='old'),
    'woman_sled': dict(sex='f', coat='charcoal', coat_len=0.95, hat='headscarf', hat_col='red', scarf=None,
                       legs='black', shoes='felt_boot', skin='old', sled=True),
    'fisher': dict(sex='m', coat='brown', coat_len=0.70, hat='ushanka', hat_col='fur', scarf=None, legs='grey',
                   shoes='felt_boot', skin='ruddy', crate=True, rod=True),
    'stationmaster': dict(sex='m', coat='rail', coat_len=0.88, hat='peaked', hat_col='red', scarf=None, legs='rail',
                          shoes='boot', disc=True),
    'conductor': dict(sex='f', coat='rail', coat_len=0.80, hat='beret', hat_col='rail', scarf=None, legs='black',
                      shoes='boot', flag=True),
    'customs': dict(sex='m', coat='green', coat_len=0.90, hat='peaked', hat_col='green', scarf=None, legs='green',
                    shoes='boot', belt='leather', briefcase=False),
    'child_b': dict(sex='c', coat='navy', coat_len=0.50, hat='ushanka', hat_col='fur', scarf='red', legs='grey',
                    shoes='felt_boot', scale=0.62),
    'sweeper': dict(sex='m', coat='green', coat_len=0.60, hat='cap', hat_col='grey', scarf=None, legs='grey',
                    shoes='felt_boot', broom=True, skin='ruddy'),
    'traveller': dict(sex='m', coat='camel', coat_len=0.85, hat='fedora', hat_col='brown', scarf='wine',
                      legs='brown', shoes='boot', suitcase=True),
    'traveller_f': dict(sex='f', coat='navy', coat_len=0.90, hat='beret', hat_col='wine', scarf='cream',
                        legs='black', shoes='boot', suitcase=True),
    'watcher': dict(sex='m', coat='black', coat_len=0.98, hat='fedora', hat_col='black', scarf=None, legs='black',
                    shoes='boot', hands='pockets'),
}


def box(kind, height):
    """Frame size (w, h) for a figure of `height` px (standing, soles on the bottom row)."""
    k = KINDS[kind]
    hh = height * k.get('scale', 1.0)
    w = int(math.ceil(hh * 0.62)) + 6
    if k.get('sled'):
        w = int(math.ceil(hh * 1.45)) + 6
    if k.get('rifle') or k.get('broom'):
        w = max(w, int(math.ceil(hh * 0.80)) + 6)
    return w + (w % 2), int(math.ceil(height)) + 3


# ------------------------------------------------------------------------------------------------ poses
def walk_pose(phase, stride=1.0):
    """Joint angles (degrees, 0 = hanging straight down, + = forward) for one walk phase (radians).
    phase 0: near (right) leg forward at heel strike; the arms swing against the legs."""
    c = math.cos(phase)
    s = math.sin(phase)
    leg_n = 24.0 * stride * c
    leg_f = -leg_n
    knee_n = 6.0 + 48.0 * stride * max(0.0, s) ** 1.3       # the leg swinging forward bends its knee
    knee_f = 6.0 + 48.0 * stride * max(0.0, -s) ** 1.3
    arm_n = -20.0 * stride * c
    arm_f = -arm_n
    return dict(leg_n=leg_n, leg_f=leg_f, knee_n=knee_n, knee_f=knee_f, arm_n=arm_n, arm_f=arm_f,
                elb_n=10.0 + 16.0 * max(0.0, -c), elb_f=10.0 + 16.0 * max(0.0, c),
                bob=0.025 * math.cos(2 * phase), lean=3.0)


def stand_pose(i=0):
    b = [0.0, 0.004, 0.008, 0.004][i % 4]
    return dict(leg_n=3.0, leg_f=-4.0, knee_n=4.0, knee_f=6.0, arm_n=4.0, arm_f=-3.0, elb_n=14.0, elb_f=12.0,
                bob=-b, lean=1.0)


def sit_pose(i=0):
    b = [0.0, 0.005][i % 2]
    return dict(leg_n=80.0, leg_f=74.0, knee_n=95.0, knee_f=88.0, arm_n=30.0, arm_f=26.0, elb_n=50.0, elb_f=46.0,
                bob=-b, lean=12.0, sit=True)


# ------------------------------------------------------------------------------------------------ geometry
def _limb_angles(top, a_deg, b_deg, L1, L2, facing, z=0.0):
    """Two-segment limb in the view plane from `top`: first segment at a_deg from straight down (+ = toward
    the facing direction), the second bent by b_deg more."""
    a = math.radians(a_deg)
    b = math.radians(a_deg + b_deg)
    j1 = top + np.array([facing * math.sin(a) * L1, math.cos(a) * L1, z])
    j2 = j1 + np.array([facing * math.sin(b) * L2, math.cos(b) * L2, z])
    return j1, j2


def _leg_back(top, a_deg, knee_deg, L1, L2, facing, z):
    """Leg: thigh forward by a_deg, the shin bends BACK at the knee by knee_deg (knees bend backward)."""
    a = math.radians(a_deg)
    b = math.radians(a_deg - knee_deg)
    kn = top + np.array([facing * math.sin(a) * L1, math.cos(a) * L1, z])
    an = kn + np.array([facing * math.sin(b) * L2, math.cos(b) * L2, z])
    return kn, an


def _head_xf(head_c, hu, facing, nod):
    """Head-local point (dx toward the face, dy down, dz toward the camera; in heads) -> sprite px, the head
    tipped forward by `nod` (radians) about its centre."""
    c, s = math.cos(nod), math.sin(nod)

    def f(dx, dy, dz=0.0):
        x, y = dx * hu, dy * hu
        xr, yr = x * c - y * s, x * s + y * c
        return (float(head_c[0] + facing * xr), float(head_c[1] + yr), float(head_c[2] + dz * hu))
    return f


def build_person(M, kind, height, pose, facing=1, seed=0, opts=None):
    """SDF of one figure in sprite pixels; returns (root, anchors).  Origin: the soles at (cx, ground)."""
    k = dict(KINDS[kind])
    if opts:
        k.update(opts)
    sc = k.get('scale', 1.0)
    H = height * sc
    hu = H / 7.5                                  # one head
    w, h = box(kind, height)
    cx = w / 2.0 + (-0.08 * hu * facing if k.get('sled') else 0.0)
    if k.get('sled'):
        cx = w - 0.42 * H if facing > 0 else 0.42 * H
    ground = h - 1.0
    sexf = k['sex']
    bob = pose.get('bob', 0.0) * H
    lean = math.radians(pose.get('lean', 2.0)) * facing
    sit = pose.get('sit', False)
    hip_y = ground - 3.55 * hu + bob
    if sit:
        hip_y = ground - 2.15 * hu
    hip = np.array([cx, hip_y, 0.0])
    # spine: hips -> shoulders, leaning forward a little in the walk
    sh_c = hip + np.array([math.sin(lean) * 2.55 * hu, -2.55 * hu * math.cos(lean), 0.0])
    neck = sh_c + np.array([math.sin(lean) * 0.25 * hu, -0.32 * hu, 0.0])
    head_c = neck + np.array([0.15 * hu * facing, -0.60 * hu, 0.0])     # the neck leans forward a little
    sw = {'m': 1.0, 'f': 0.86, 'c': 0.92}[sexf]
    mats = {}

    def mm(name, rmp):
        mats[name] = rmp
        return M(name)

    coat = mm('coat', CLOTH[k['coat']])
    legs_m = mm('legs', CLOTH[k['legs']])
    shoe = mm('shoe', CLOTH[k['shoes']])
    skin = mm('skin', SKINS[k.get('skin', 'light')])
    hair_m = mm('hair', HAIR[k.get('hair', 'dark')])
    parts = []
    zn, zf = 0.42 * hu, -0.42 * hu                 # near (toward the camera) and far limbs
    # ---- legs (thigh, shin, shoe)
    L_th, L_sh = 1.85 * hu, 1.78 * hu
    rl = 0.30 * hu
    for side, z in (('n', zn), ('f', zf)):
        top = hip + np.array([0.0, 0.15 * hu, z * 0.7])
        kn, an = _leg_back(top, pose['leg_' + side], pose['knee_' + side], L_th, L_sh, facing, z * 0.7)
        if not sit:
            an[1] = min(an[1], ground - 0.22 * hu)
        parts.append(RC(tuple(top), tuple(kn), rl * 1.15, rl * 0.92, legs_m))
        parts.append(RC(tuple(kn), tuple(an), rl * 0.92, rl * 0.70, legs_m))
        toe = an + np.array([facing * 0.85 * hu, 0.16 * hu, 0.0])
        parts.append(RC(tuple(an + np.array([-facing * 0.12 * hu, 0.04 * hu, 0])), tuple(toe), rl * 0.78,
                        rl * 0.55, shoe))
    # ---- trunk: chest, waist, hips (inside the coat)
    tw = 1.0 * hu * sw
    trunk = [E(tuple(sh_c + np.array([0.05 * hu * facing, 0.64 * hu, 0])), (0.78 * hu, 0.84 * hu, 0.90 * hu * sw),
               coat),                                                                     # chest in its coat
             RC(tuple(sh_c + np.array([0, 0.5 * hu, 0])), tuple(hip + np.array([0, -0.2 * hu, 0])),
                0.72 * hu * sw, 0.66 * hu * sw, coat),
             E(tuple(sh_c + np.array([0, 0.18 * hu, 0])), (0.72 * hu, 0.38 * hu, 1.0 * tw), coat)]  # shoulders
    if sexf == 'f':
        trunk.append(E(tuple(hip + np.array([0, -0.1 * hu, 0])), (0.62 * hu, 0.55 * hu, 0.72 * hu), coat))
    parts += trunk
    # ---- coat skirt: from the waist down to coat_len of the leg, opening with the stride
    clen = k['coat_len']
    if clen > 0:
        hem_y = hip[1] + clen * (L_th + L_sh) * (0.62 if sit else 1.0)
        r_top = 0.62 * hu * (1.08 if sexf == 'f' else 1.0)
        # men's coats hang nearly straight from the hips (round 10: a bell that read as a skirt)
        r_hem = ((0.58 + 0.25 * clen) * 1.12 if sexf == 'f' else (0.50 + 0.16 * clen)) * hu
        skirt = [RC(tuple(hip + np.array([0, -0.4 * hu, 0])), (hip[0], hem_y - 0.1 * hu, 0.0), r_top * 1.15,
                    r_hem * 1.05, coat)]                                                  # the A-line of the coat
        for side, z in (('n', zn * 0.55), ('f', zf * 0.55)):
            a = math.radians(pose['leg_' + side] * 0.65)
            bot = np.array([hip[0] + facing * math.sin(a) * (hem_y - hip[1]), hem_y, z])
            skirt.append(RC(tuple(hip + np.array([0, -0.3 * hu, z])), tuple(bot), r_top, r_hem * 0.80, coat))
        parts.append(S.Union(skirt, k=0.6 * hu))
    # ---- arms
    L_ua, L_fa = 1.42 * hu, 1.18 * hu
    ra = 0.27 * hu
    hands = k.get('hands', 'free')
    acc = []
    arm_pts = {}
    for side, z in (('n', zn * 1.6), ('f', zf * 1.6)):
        sh = sh_c + np.array([-facing * 0.05 * hu, 0.22 * hu, z])
        a = pose['arm_' + side]
        b = pose['elb_' + side]
        if hands == 'pockets':
            a, b = -4.0, 38.0
        if k.get('sled') and side == 'n':
            a, b = -42.0, 4.0                      # the near hand pulls the sled rope behind her
        if k.get('rifle') and side == 'n':
            a, b = 8.0, -118.0                     # hand at the rifle sling on the shoulder
        if k.get('lantern') and side == 'n':
            a, b = 12.0, 58.0                      # lantern held forward at waist height
        if k.get('broom') and side == 'n':
            a, b = 30.0, 40.0
        if k.get('briefcase') and side == 'n':
            a, b = 2.0 + 0.25 * pose['arm_n'], 6.0           # the case swings a little with the step
        if k.get('suitcase') and side == 'n':
            a, b = 1.0 + 0.12 * pose['arm_n'], 2.0
        if (k.get('disc') or k.get('flag')) and side == 'n':
            a, b = 20.0, 70.0                      # the signal disc / flag held up at the shoulder
        if k.get('rod') and side == 'n':
            a, b = 40.0, 20.0
        el, wr = _limb_angles(sh, a, b, L_ua, L_fa, facing, z)
        sl = 'sleeve' if side == 'n' else 'coat'
        if side == 'n':
            mats['sleeve'] = CLOTH[k['coat']]
        arm, ap = R.sleeve_arm(M, sl, sh, el, wr, (ra * 1.2, ra * 1.02, ra * 0.9), cuff=None, skin='skin',
                               hand_s=hu / 23.0, side=(-1 if facing > 0 else 1) if side == 'n' else
                               (1 if facing > 0 else -1), hand_up=(0, 0, 1 if side == 'n' else -1),
                               hand_kw=dict(curl=(0.45, 0.5, 0.55, 0.6), split=False, knuckles=False),
                               folds=0, elbow_point=False, wrist_r=0.11 * hu)
        parts.append(arm)
        arm_pts[side] = dict(sh=sh, el=el, wr=wr)
    # ---- neck, head, hair, hat
    # round 10b: a sculpted profile instead of an egg with a bump -- cranium, an upright forehead over the brow
    # ridge, the nose, the lips, a chin set back under the nose, the jaw line running back to the ear -- and the
    # head carried a few degrees forward as people hold it (the old face plane and jaw pushed the chin out and
    # read as a head tipped back).  Eyes, brows and mouth are painted on the render (face_marks).
    nod = math.radians(k.get('nod', 5.0))
    hp = _head_xf(head_c, hu, facing, nod)
    parts.append(RC(tuple(neck + np.array([-facing * 0.04 * hu, 0.28 * hu, 0])), hp(-0.08, 0.30), 0.21 * hu,
                    0.19 * hu, skin))
    hr = 0.5 * hu
    head = [E(hp(-0.05, -0.05), (0.47 * hu, 0.49 * hu, 0.45 * hu), skin),           # cranium
            E(hp(0.19, -0.17), (0.25 * hu, 0.24 * hu, 0.36 * hu), skin),           # forehead, upright
            E(hp(0.34, -0.05), (0.09 * hu, 0.06 * hu, 0.30 * hu), skin),           # brow ridge
            E(hp(0.19, 0.12), (0.25 * hu, 0.25 * hu, 0.38 * hu), skin),            # cheek and the face plane
            RC(hp(0.37, -0.03), hp(0.50, 0.13), 0.05 * hu, 0.075 * hu, skin),      # nose
            E(hp(0.35, 0.26), (0.08 * hu, 0.06 * hu, 0.22 * hu), skin),            # lips
            E(hp(0.30, 0.39), (0.11 * hu, 0.10 * hu, 0.17 * hu), skin),            # chin
            RC(hp(-0.14, 0.16), hp(0.23, 0.37), 0.20 * hu, 0.12 * hu, skin),       # jaw line
            E(hp(-0.05, 0.05, 0.40), (0.09 * hu, 0.15 * hu, 0.07 * hu), skin)]     # the ear on our side
    parts.append(S.Union(head, k=0.10 * hu))
    hat = k.get('hat')
    hc = mm('hat', CLOTH[k['hat_col']] if k['hat_col'] in CLOTH else CLOTH['black'])
    top = np.array(hp(-0.02, -0.42))
    if hat in (None, 'cap', 'beret', 'knit', 'peaked', 'shako', 'homburg', 'fedora'):
        # hair at the back of the head / under the hat: the hairline leaves the forehead free
        parts.append(E(hp(-0.12, -0.10), (hr * 0.90, hr * 0.92, hr * 0.95), hair_m))
        if hat is None:
            # bare heads: the hair over the crown down to the hairline (round 10 left them bald in front)
            if sexf == 'f':
                parts.append(E(hp(0.05, -0.27), (0.42 * hu, 0.26 * hu, 0.47 * hu), hair_m))
                parts.append(E(hp(-0.46, -0.12), (0.20 * hu, 0.19 * hu, 0.20 * hu), hair_m))    # the bun
            else:
                parts.append(E(hp(-0.04, -0.30), (0.42 * hu, 0.23 * hu, 0.46 * hu), hair_m))
    if hat in ('fedora', 'homburg'):
        crown = E(tuple(top + np.array([0, -0.12 * hu, 0])), (0.50 * hu, 0.27 * hu, 0.50 * hu), hc)
        dent = E(tuple(top + np.array([0, -0.40 * hu, 0])), (0.12 * hu, 0.08 * hu, 0.30 * hu), hc)
        parts.append(S.Sub(crown, dent, k=0.04 * hu))
        brim_r = 0.82 * hu if hat == 'fedora' else 0.72 * hu
        tilt = S.rot(0, 0, 4.0 * facing)                  # worn level, the front of the brim a touch down
        parts.append(S.Xform(S.Cylinder((0, 0, 0), brim_r, 0.05 * hu, hc, e=0.04 * hu),
                             o=top + np.array([facing * 0.05 * hu, 0.10 * hu, 0]), R=tilt))
    elif hat == 'cap':
        parts.append(E(tuple(top + np.array([facing * 0.06 * hu, 0.0, 0])), (0.58 * hu, 0.20 * hu, 0.54 * hu), hc))
        parts.append(E(tuple(top + np.array([facing * 0.48 * hu, 0.12 * hu, 0])), (0.30 * hu, 0.06 * hu, 0.36 * hu),
                       hc))
    elif hat in ('peaked', 'shako'):
        hgt = 0.26 if hat == 'peaked' else 0.42
        parts.append(S.Cylinder(tuple(top + np.array([0, -hgt * 0.5 * hu, 0])), 0.50 * hu, hgt * hu * 0.55, hc,
                                e=0.06 * hu))
        parts.append(E(tuple(top + np.array([facing * 0.50 * hu, 0.10 * hu, 0])), (0.26 * hu, 0.05 * hu,
                                                                                   0.36 * hu), M('visor')))
        mats['visor'] = CLOTH['black']
    elif hat == 'beret':
        parts.append(E(tuple(top + np.array([-facing * 0.06 * hu, 0.02 * hu, 0])), (0.60 * hu, 0.17 * hu,
                                                                                    0.58 * hu), hc))
    elif hat == 'knit':
        parts.append(E(tuple(top + np.array([0, 0.06 * hu, 0])), (0.54 * hu, 0.34 * hu, 0.54 * hu), hc))
        parts.append(S.Sphere(tuple(top + np.array([0, -0.30 * hu, 0])), 0.16 * hu, hc))
    elif hat == 'ushanka':
        parts.append(E(tuple(top + np.array([0, 0.10 * hu, 0])), (0.64 * hu, 0.40 * hu, 0.64 * hu), hc))
        for sz in (1, -1):
            parts.append(E(tuple(head_c + np.array([-facing * 0.05 * hu, 0.18 * hu, sz * 0.46 * hu])),
                           (0.30 * hu, 0.36 * hu, 0.12 * hu), hc))
    elif hat == 'headscarf':
        parts.append(E(tuple(head_c + np.array([-facing * 0.06 * hu, -0.04 * hu, 0])), (hr * 1.0, hr * 1.06,
                                                                                         hr * 1.02), hc))
        parts.append(E(tuple(head_c + np.array([-facing * 0.10 * hu, 0.48 * hu, 0])), (0.40 * hu, 0.24 * hu,
                                                                                        0.42 * hu), hc))
    if k.get('scarf'):
        sm = mm('scarf', CLOTH[k['scarf']])
        parts.append(E(tuple(neck + np.array([0, 0.18 * hu, 0])), (0.36 * hu, 0.22 * hu, 0.40 * hu), sm))
    if k.get('belt'):
        bm = mm('belt', CLOTH[k['belt']])
        parts.append(S.Cylinder(tuple(hip + np.array([0, -0.35 * hu, 0])), 0.60 * hu * sw, 0.09 * hu, bm,
                                e=0.03 * hu))
    if k.get('braid'):
        bm = mm('braid', CLOTH['brass'])
        parts.append(E(tuple(sh_c + np.array([facing * 0.2 * hu, 0.15 * hu, zn * 1.4])), (0.22 * hu, 0.08 * hu,
                                                                                         0.10 * hu), bm))
    if k.get('apron'):
        am = mm('apron', CLOTH['cream'])
        parts.append(E(tuple(hip + np.array([facing * 0.36 * hu, 0.4 * hu, 0])), (0.18 * hu, 1.0 * hu, 0.5 * hu),
                       am))
    # ---- accessories in the near hand
    # round 10b: cases and the lantern HANG from the hand -- the handle runs through the curled fingers, the
    # case sits below and just behind the hand (z), so the knuckles and fingers read in front of the handle
    # (round 10 placed the case in front of the hand: a case floating at the hip with no hand on it)
    wr = arm_pts['n']['wr']
    hdir = R.nrm(wr - arm_pts['n']['el'])
    grip = wr + hdir * 0.46 * hu                                 # inside the curled fingers
    grip[2] = wr[2] - 0.10 * hu
    if k.get('suitcase') or k.get('briefcase'):
        big = bool(k.get('suitcase'))
        sm = mm('case', CLOTH['leather'])
        bm = mm('brassm', CLOTH['brass'])
        hw, hh, hd = (1.0, 0.62, 0.30) if big else (0.80, 0.52, 0.15)
        top_y = grip[1] + 0.13 * hu
        c = np.array([grip[0] + facing * 0.04 * hu, top_y + hh * hu, grip[2] - (hd + 0.04) * hu])
        acc.append(S.RoundBox(tuple(c), (hw * hu, hh * hu, hd * hu), (0.08 if big else 0.10) * hu, sm))
        # the leather handle: a bar through the fist on two short posts riveted to the top of the case
        hz = grip[2] - 0.02 * hu
        acc.append(RC((grip[0] - facing * 0.20 * hu, grip[1], hz), (grip[0] + facing * 0.20 * hu, grip[1], hz),
                      0.055 * hu, 0.055 * hu, sm))
        for sx in (-1, 1):
            p0 = (grip[0] + sx * 0.20 * hu, grip[1], hz)
            acc.append(RC(p0, (p0[0] + sx * 0.04 * hu, top_y + 0.02 * hu, hz), 0.05 * hu, 0.05 * hu, sm))
        # the brass lock (and the suitcase's strap buckle) on the face toward us
        acc.append(S.RoundBox((c[0], top_y + 0.14 * hu, c[2] + hd * hu), (0.09 * hu, 0.06 * hu, 0.02 * hu),
                              0.02 * hu, bm))
        if big:
            acc.append(S.RoundBox((c[0], c[1] + 0.05 * hu, c[2] + hd * hu + 0.01 * hu), (1.02 * hu, 0.06 * hu,
                                                                                        0.02 * hu), 0.02 * hu, bm))
    if k.get('lantern'):
        lm = mm('lantern', CLOTH['steel'])
        gm = mm('glow', _r('#6e3f22', '#d08f55', '#fce2b0', '#fff4da'))
        c = grip + np.array([facing * 0.02 * hu, 0.48 * hu, -0.12 * hu])
        acc.append(RC(tuple(grip + np.array([0, 0, -0.05 * hu])), tuple(c + np.array([0, -0.30 * hu, 0])),
                      0.04 * hu, 0.04 * hu, lm))                                    # the bail in the fist
        acc.append(S.RoundBox(tuple(c), (0.24 * hu, 0.34 * hu, 0.24 * hu), 0.05 * hu, lm))
        acc.append(E(tuple(c + np.array([0, 0.02 * hu, 0.20 * hu])), (0.17 * hu, 0.24 * hu, 0.12 * hu), gm))
    if k.get('rifle'):
        rm = mm('rifle', CLOTH['wood'])
        sh = arm_pts['n']['sh']
        a0 = sh + np.array([-facing * 0.45 * hu, -1.05 * hu, zn * 1.2])
        a1 = sh + np.array([facing * 0.30 * hu, 1.35 * hu, zn * 1.2])
        acc.append(RC(tuple(a0), tuple(a1), 0.07 * hu, 0.13 * hu, rm))
    if k.get('broom'):
        bm = mm('broom', CLOTH['wood'])
        a0 = wr + np.array([-facing * 0.6 * hu, -0.8 * hu, zn])
        a1 = wr + np.array([facing * 1.4 * hu, 2.6 * hu, zn])
        acc.append(RC(tuple(a0), tuple(a1), 0.06 * hu, 0.06 * hu, bm))
        acc.append(E(tuple(a1 + np.array([facing * 0.2 * hu, 0.15 * hu, 0])), (0.5 * hu, 0.16 * hu, 0.3 * hu), bm))
    if k.get('sled'):
        wm = mm('sled', CLOTH['wood'])
        st = mm('steel_m', CLOTH['steel'])
        sx0 = cx - facing * 1.08 * H
        sx1 = cx - facing * 0.52 * H
        lo, hi_ = min(sx0, sx1), max(sx0, sx1)
        acc.append(S.RoundBox(((lo + hi_) / 2, ground - 0.55 * hu, 0), ((hi_ - lo) / 2, 0.08 * hu, 0.55 * hu),
                              0.05 * hu, wm))
        acc.append(S.RoundBox(((lo + hi_) / 2, ground - 0.12 * hu, 0), ((hi_ - lo) / 2 + 0.15 * hu, 0.05 * hu,
                                                                         0.5 * hu), 0.04 * hu, st))
        can_c = ((lo + hi_) / 2, ground - 1.25 * hu, 0)
        acc.append(S.Cylinder(can_c, 0.48 * hu, 0.72 * hu, mm('can', CLOTH['steel']), e=0.1 * hu))
        acc.append(S.Cylinder((can_c[0], can_c[1] - 0.75 * hu, 0), 0.22 * hu, 0.16 * hu, M('can'), e=0.05 * hu))
        rope_a = wr + np.array([0, 0.05 * hu, 0])
        rope_b = np.array([hi_ if facing > 0 else lo, ground - 0.55 * hu, 0])
        acc.append(RC(tuple(rope_a), tuple(rope_b), 0.05 * hu, 0.05 * hu, mm('rope', CLOTH['cream'])))
    if k.get('crate'):
        wm = mm('crate', CLOTH['wood'])
        acc.append(S.RoundBox((hip[0] - facing * 0.15 * hu, ground - 0.95 * hu, 0), (0.75 * hu, 0.95 * hu, 0.7 * hu),
                              0.08 * hu, wm))
    if k.get('rod'):
        rm = mm('rod', CLOTH['wood'])
        tip = wr + np.array([facing * 1.6 * hu, -0.5 * hu, zn])
        acc.append(RC(tuple(wr), tuple(tip), 0.08 * hu, 0.05 * hu, rm))
        acc.append(RC(tuple(tip), (tip[0], ground - 0.05 * hu, zn), 0.02 * hu, 0.02 * hu, mm('line', CLOTH['grey'])))
        acc.append(S.Cylinder((tip[0], ground + 0.02 * hu, zn), 0.55 * hu, 0.04 * hu, mm('hole', CLOTH['black']),
                              e=0.02 * hu))
    if k.get('disc'):
        dm = mm('disc', _r('#2a0c0b', '#6e231a', '#b04a32', '#e8dcd6', '#f2f3f5'))
        tip = wr + np.array([facing * 0.25 * hu, -0.9 * hu, zn])
        acc.append(RC(tuple(wr), tuple(tip), 0.06 * hu, 0.06 * hu, mm('stick', CLOTH['black'])))
        acc.append(S.Cylinder(tuple(tip + np.array([0, -0.32 * hu, 0])), 0.36 * hu, 0.05 * hu, dm, e=0.02 * hu,
                              R=S.rot(0, 90, 0)))
    if k.get('flag'):
        fm = mm('flagc', CLOTH['mustard'])
        tip = wr + np.array([facing * 0.2 * hu, -1.0 * hu, zn])
        acc.append(RC(tuple(wr), tuple(tip), 0.05 * hu, 0.05 * hu, mm('stick', CLOTH['black'])))
        acc.append(S.RoundBox(tuple(tip + np.array([facing * 0.35 * hu, 0.25 * hu, 0])), (0.32 * hu, 0.24 * hu,
                                                                                         0.03 * hu), 0.02 * hu, fm))
    root = S.Union(parts + acc, k=0.0)
    return root, mats, dict(head=head_c, hip=hip, sh=sh_c, ground=ground, arms=arm_pts, hu=hu, nod=nod,
                            hair=k.get('hair', 'dark'), hat=hat)


def face_marks(rgba, matmap, names, anc, facing=1):
    """Round 10b: the features of a profile at sprite scale, painted on the rendered skin (only where the skin
    shows -- never on a hat brim or a collar): the eye (iris and upper lid as one dark mark, from 7 px heads a
    lid line), the brow in the hair colour, the closed mouth, the nostril, the shadow inside the ear.  Each mark
    darkens the lit skin under it, so it follows the light of the shot.  Heads under ~3.6 px get nothing."""
    hu = float(anc['hu'])
    if hu < 3.6 or 'skin' not in names:
        return rgba
    hp = _head_xf(anc['head'], hu, facing, anc['nod'])
    sk = names.index('skin')
    out = rgba.copy()
    h, w = matmap.shape
    hair = HAIR.get(anc.get('hair', 'dark'), HAIR['dark'])
    hair_c = np.array([int(hair[min(2, len(hair) - 1)][i:i + 2], 16) for i in (1, 3, 5)], float) \
        if isinstance(hair[0], str) else np.array(hair[2][:3], float)

    def at(dx, dy):
        x, y, _ = hp(dx, dy)
        return int(math.floor(x)), int(math.floor(y))

    def ok(x, y):
        return 0 <= x < w and 0 <= y < h and matmap[y, x] == sk and out[y, x, 3] > 0

    def mark(x, y, f, tint=None, mix=0.0):
        if ok(x, y):
            c = out[y, x, :3].astype(float) * f
            if tint is not None:
                c = c * (1 - mix) + tint * mix * (0.35 + 0.65 * out[y, x, :3].mean() / 255.0)
            out[y, x, :3] = np.clip(c, 0, 255).astype(np.uint8)

    done = set()

    def put(dx, dy, f, tint=None, mix=0.0):
        x, y = at(dx, dy)
        if (x, y) not in done:
            done.add((x, y))
            mark(x, y, f, tint, mix)

    # eye: one dark mark set back from the brow ridge
    put(0.29, -0.01, 0.30)
    # brow: hair coloured, a skin pixel above the eye (never touching it: a touching brow reads as a smudge)
    by = -0.20 if hu >= 9 else -0.16
    for dx in (() if hu < 6 else (0.24, 0.35) if hu < 9 else (0.20, 0.29, 0.38)):   # small heads: the eye only
        put(dx, by, 0.55, hair_c, 0.55)
    # mouth: the line between the lips, ending short of the lip front
    if hu >= 5.0:
        put(0.37, 0.26, 0.62)
        if hu >= 9.0:
            put(0.29, 0.27, 0.72)
    # the hollow of the ear
    if hu >= 7.0:
        put(-0.05, 0.07, 0.62)
    return out


def render_person(kind, height, pose, facing=1, light='dawn', seed=0, opts=None, ss=4, cache=None,
                  outline=True):
    M = A.Mats()
    root, mats, anc = build_person(M, kind, height, pose, facing, seed, opts)
    st = {}
    for nm, rmp in mats.items():
        th = None
        if nm == 'glow':
            th = [0.02, 0.05, 0.1]
        elif nm == 'skin':
            th = [0.02, 0.05, 0.09, 0.15, 0.24, 0.38, 0.56]      # faces and hands read at a distance
        st[nm] = _style(rmp, light, th=th)
    w, h = box(kind, height)
    look = dict(LIGHTS[light])
    gain = VGAIN.get(light, 0.8)
    keep = ('glow', 'skin')

    def v_mul(v, d, Mm):
        mk = np.zeros(v.shape, bool)
        for nm in keep:
            if nm in Mm.names:
                mk |= d.mat == Mm.names.index(nm)
        sk = np.zeros(v.shape, bool)
        if 'skin' in Mm.names:
            sk = d.mat == Mm.names.index('skin')
        night = light.startswith('night')
        boost = 0.06 if night else 0.2
        return np.where(mk, v * min(1.0, gain + boost), v * gain) + sk * (0.02 if night else 0.08)
    res = R.render(root, M, (w, h), look, st, groups={n: i for i, n in enumerate(M.names)}, priority={'skin': 1},
                   tone_passes=(), lights=(), ss=ss, outline=outline, rim=light.startswith('night') or light == 'palais',
                   cache_key=cache, v_mul=v_mul, src=('env_veltrava_cine_people.py',))
    if 'glow' in M.names:
        # the lantern flame does not depend on the scene light: paint it bright
        g = res['mat'] == M.names.index('glow')
        rgba = res['rgba'].copy()
        rgba[g, :3] = (252, 226, 176)
        res = dict(res, rgba=rgba)
    res = dict(res, rgba=face_marks(res['rgba'], res['mat'], list(res['names']), anc, facing))
    return res


def person_sheet(kind, height, frames=8, pose='walk', facing=1, light='dawn', seed=0, ss=4, **opts):
    """Frames side by side (see the module doc)."""
    out = []
    for i in range(frames):
        if pose == 'walk':
            ps = walk_pose(2 * math.pi * i / frames, stride=opts.pop('stride', 1.0) if i == 0 and 'stride' in opts
                           else 1.0)
        elif pose == 'stand':
            ps = stand_pose(i)
        elif pose == 'sit':
            ps = sit_pose(i)
        else:
            ps = stand_pose(i)
        key = ('person_v8', kind, round(float(height), 2), pose, i, frames, facing, light, seed, ss,
               tuple(sorted(opts.items())))
        out.append(render_person(kind, height, ps, facing, light, seed, opts or None, ss=ss, cache=key)['rgba'])
    return np.concatenate(out, axis=1)


# ------------------------------------------------------------------------------------------------ hotel windows
def _raster(w, h, shapes, ss=8, thresh=0.45):
    """Union of 2D shapes in pixel coordinates (ellipse ('e', cx, cy, rx, ry), polygon ('p', [(x, y)...]),
    capsule ('c', x0, y0, x1, y1, r)) rasterised with ss x ss coverage -> bool mask."""
    ys, xs = np.mgrid[0:h * ss, 0:w * ss].astype(np.float32)
    X = (xs + 0.5) / ss
    Y = (ys + 0.5) / ss
    m = np.zeros(X.shape, bool)
    for s in shapes:
        if s[0] == 'e':
            _, cx, cy, rx, ry = s
            m |= ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0
        elif s[0] == 'c':
            _, x0, y0, x1, y1, r = s
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy + 1e-9
            t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1)
            m |= (X - (x0 + t * dx)) ** 2 + (Y - (y0 + t * dy)) ** 2 <= r * r
        elif s[0] == 'p':
            pts = s[1]
            inside = np.zeros(X.shape, bool)
            n = len(pts)
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                cond = ((ya > Y) != (yb > Y)) & (X < (xb - xa) * (Y - ya) / (yb - ya + 1e-9) + xa)
                inside ^= cond
            m |= inside
    cov = m.reshape(h, ss, w, ss).mean((1, 3))
    return cov >= thresh


# hand-set pixel templates for the two windows of LS_C3_Close n2 (13 x 20 and 15 x 16): at this size every
# pixel is a decision (head and jaw, the neck, sloping shoulders, the turned profile with nose and chin, the
# tea glass at Alexei's chest); '#' body, 'r' rim of lamp light, 'g' amber tea, 'w' glint on the glass rim
_WIN_TPL = {
    ('konrad', 13, 20, 1): [
        '.............', '.............', '.............', '.............',
        '.....rrr.....', '....r###r....', '....#####....', '....#####....', '....#####....', '.....###.....',
        '......#......', '...r#####r...', '..r#######r..', '..#########..', '..#########..', '.##########..',
        '.###########.', '.###########.', '.###########.', '.###########.'],
    ('konrad', 13, 20, 2): [
        '.............', '.............', '.............', '.............',
        '.....rrr.....', '....r###r....', '....######...', '....#####....', '....####.....', '.....###.....',
        '......#......', '...r#####r...', '..r#######r..', '..#########..', '..#########..', '.##########..',
        '.###########.', '.###########.', '.###########.', '.###########.'],
    ('alexei', 15, 16, 1): [
        '...............', '...............', '...............', '......rrr......', '.....r###r.....',
        '.....#####.....', '.....#####.....', '.....#####.....', '......###......', '...rrr###rrr...',
        '..r#########r..', '.r###########r.', '.########wg###.', '.########gg###.', '.#############.',
        '.#############.'],
    ('alexei', 15, 16, 2): [
        '...............', '...............', '...............', '......rrr......', '.....r###r.....',
        '.....######....', '.....#####.....', '.....####......', '......###......', '...rrr###rrr...',
        '..r#########r..', '.r###########r.', '.########wg###.', '.########gg###.', '.#############.',
        '.#############.'],
}


# round 10b: the in-between states of the two windows (the art director saw them pop: an empty lit window, then a
# full silhouette in one frame, then the profile in one frame).  'far': he comes in at the back of the room under
# the ceiling lamp -- smaller, lower in the window (we look up from the square), dim and warm rather than black;
# 'side': he steps to the glass from the right, the right curtain still in front of his shoulder; 'turn': the head
# halfway round to the whistle (the jaw already turned, no nose yet).
_WIN_TPL.update({
    ('konrad', 13, 20, 'far'): ['.' * 13] * 9 + [
        '.......##....', '......####...', '......####...', '.......##....', '.....######..', '....########.',
        '....########.', '....########.', '....########.', '....########.', '....########.'],
    ('konrad', 13, 20, 'side'): [
        '.............', '.............', '.............', '.............',
        '.......rrr...', '......r###...', '......####...', '......####...', '......####...', '.......###...',
        '........#....', '.....r####...', '....r#####...', '....######...', '....######...', '...#######...',
        '...#######...', '...#######...', '...#######...', '...#######...'],
    ('konrad', 13, 20, 'turn'): [
        '.............', '.............', '.............', '.............',
        '.....rrr.....', '....r###r....', '....#####....', '....#####....', '....####.....', '.....###.....',
        '......#......', '...r#####r...', '..r#######r..', '..#########..', '..#########..', '.##########..',
        '.###########.', '.###########.', '.###########.', '.###########.'],
    ('alexei', 15, 16, 'far'): ['.' * 15] * 7 + [
        '.........##....', '........####...', '........####...', '.........##....', '.......######..',
        '......########.', '......########.', '......########.', '......########.'],
    ('alexei', 15, 16, 'side'): [
        '...............', '...............', '...............', '........rrr....', '.......r###r...',
        '.......#####...', '.......#####...', '.......#####...', '........###....', '.....rrr###r...',
        '....r#######...', '...r########...', '...########w...', '...########g...', '...#########...',
        '...#########...'],
    ('alexei', 15, 16, 'turn'): [
        '...............', '...............', '...............', '......rrr......', '.....r###r.....',
        '.....#####.....', '.....#####.....', '.....####......', '......###......', '...rrr###rrr...',
        '..r#########r..', '.r###########r.', '.########wg###.', '.########gg###.', '.#############.',
        '.#############.'],
})
for _k, _rows in list(_WIN_TPL.items()):
    assert len(_rows) == _k[2] and all(len(r) == _k[1] for r in _rows), _k
# frames of the window sheets (env_veltrava_cine_close._window_frames) and when the runtime shows them
# (ch3_close.gd reads layout close.win_seq: [[t, frame], ...] per man; the whistle blows at 8.4 s)
WINDOW_SEQ = (0, 'far', 'side', 1, 'turn', 2)
WINDOW_TIMES = {'konrad': [[0.0, 0], [6.9, 1], [7.2, 2], [7.42, 3], [8.75, 4], [8.87, 5]],
                'alexei': [[0.0, 0], [7.45, 1], [7.75, 2], [7.97, 3], [9.05, 4], [9.17, 5]]}
WINDOW_TONE = {'far': ('C', 1.0)}          # dim and warm at the back of the lit room; the rest are silhouettes


def _from_template(rows):
    a = np.array([list(r) for r in rows])
    body = (a == '#') | (a == 'r')
    return dict(body=body, rim=a == 'r', glass=(a == 'g'), glint=(a == 'w'))


def window_figure_masks(who, ww, wh, state):
    """Masks (ww x wh) of Konrad / Alexei behind the lit glass of a hotel window, seen against the room lamp.
    state 0: nobody; 1: he has stepped to the glass (one hand on the curtain / the tea glass at his chest);
    2: he turns his head toward the station (the whistle) -- the profile shows the nose and chin.
    Konrad: slim, upright, hatless, hair parted, shirt sleeves and waistcoat; Alexei: broad, in his rollneck,
    the tea glass in the holder in his right hand.  Returns dict(body, rim, glass, glint) bool masks."""
    z = np.zeros((wh, ww), bool)
    if isinstance(state, str):
        # round 10b in-between states (hand-set templates only; other window sizes fall back to the nearest)
        key = (who, ww, wh, state)
        if key in _WIN_TPL:
            out = _from_template(_WIN_TPL[key])
            out['tone'] = WINDOW_TONE.get(state, ('N', 0.6))
            return out
        state = {'far': 0, 'side': 1, 'turn': 1}.get(state, 1)
    if state <= 0:
        return dict(body=z, rim=z, glass=z, glint=z)
    key = (who, ww, wh, min(2, int(state)))
    if key in _WIN_TPL:
        return _from_template(_WIN_TPL[key])
    s = wh / 20.0                                   # designed on a 13 x 20 window
    cx = ww / 2.0 - (0.3 if who == 'konrad' else -0.2) * s
    turn = state >= 2
    if who == 'konrad':
        hx, hy, hr = cx, 7.0 * s, 2.25 * s
        sh_w = 4.2 * s
    else:
        hx, hy, hr = cx, 6.9 * s, 2.45 * s
        sh_w = 5.4 * s
    shapes = [('e', hx, hy, hr * 0.92, hr)]                                   # head
    if turn:
        shapes.append(('e', hx + hr * 0.78, hy + hr * 0.15, hr * 0.34, hr * 0.28))   # nose: profile to the right
        shapes.append(('e', hx + hr * 0.35, hy + hr * 0.80, hr * 0.48, hr * 0.32))   # chin
    else:
        shapes.append(('e', hx, hy + hr * 0.60, hr * 0.70, hr * 0.55))             # jaw seen from the front
    if who == 'konrad':
        shapes.append(('e', hx - hr * 0.15, hy - hr * 0.62, hr * 0.85, hr * 0.48))   # parted hair, fuller on top
    ny = hy + hr * 1.0
    shapes.append(('c', hx, ny - 0.4 * s, hx, ny + 0.8 * s, hr * 0.48))           # neck
    top = ny + 0.9 * s
    shapes.append(('p', [(cx - sh_w * 0.50, top - 0.3 * s), (cx + sh_w * 0.50, top - 0.3 * s),
                         (cx + sh_w * 0.96, top + 1.2 * s), (cx + sh_w * 1.0, wh + 1.0), (cx - sh_w * 1.0, wh + 1.0),
                         (cx - sh_w * 0.96, top + 1.2 * s)]))
    glass = np.zeros((wh, ww), bool)
    glint = np.zeros((wh, ww), bool)
    if who == 'alexei':
        # the tea glass in its holder at his chest, held in the right hand
        gx, gy = cx + sh_w * 0.42, top + 4.0 * s
        glass = _raster(ww, wh, [('p', [(gx - 1.0 * s, gy - 1.7 * s), (gx + 1.0 * s, gy - 1.7 * s),
                                        (gx + 0.9 * s, gy + 0.9 * s), (gx - 0.9 * s, gy + 0.9 * s)])], thresh=0.5)
        glint = _raster(ww, wh, [('e', gx - 0.1 * s, gy - 1.55 * s, 0.9 * s, 0.35 * s)], thresh=0.5)
    body = _raster(ww, wh, shapes)
    body &= ~glass
    # the room lamp wraps round the edges of the silhouette: a 1 px rim where the body meets the lit room on
    # the lamp side (upper right)
    inner = body.copy()
    inner[:, :-1] &= body[:, 1:]
    inner[1:, :] &= body[:-1, :]
    rim = body & ~inner
    rim &= (np.arange(wh)[:, None] < top + 3 * s)
    return dict(body=body, rim=rim, glass=glass, glint=glint)


# ------------------------------------------------------------------------------------------------ passengers
# tiny people behind the lit windows of the dawn trains (LS_C3_Trains t4): rows of a 4 x 6 (salon 6 x 6) window,
# '#' = silhouette against the lamp-lit compartment.  Konrad (fedora) and Alexei (ushanka) sit at one window each
# of the two trains -- they pass each other over the middle arch.
_PAX = {
    4: [['....', '....', '.##.', '.##.', '####', '####'],          # one passenger facing the glass
        ['....', '##..', '##..', '###.', '####', '####'],          # sitting at the left of the window
        ['....', '..##', '..##', '.###', '####', '####'],          # sitting at the right
        ['....', '....', '#..#', '#..#', '####', '####'],          # two across the table
        None],                                                      # nobody at this window
    6: [['......', '......', '.##...', '.##.##', '######', '######'],
        ['......', '...##.', '...##.', '######', '######', '######'],
        ['......', '......', '##..##', '##..##', '######', '######'],
        None],
}
_HERO_PAX = {
    'fedora': ['.##.', '####', '.##.', '.##.', '####', '####'],   # crown, brim, head, shoulders
    'ushanka': ['####', '####', '#..#', '.##.', '####', '####'],   # fur hat with the flaps down
}
HERO_WINDOWS = {('train_de', 158): 'fedora', ('train_su', 104): 'ushanka'}


def window_passenger_mask(w, h, wx, wy, ww, wh, seed, sprite=''):
    """Bool mask (h x w) of the passenger(s) behind the lit window at (wx, wy, ww, wh) of a train sprite, or
    None when the seat is empty.  Deterministic in seed; the heroes' windows are listed in HERO_WINDOWS."""
    hero = HERO_WINDOWS.get((sprite, int(wx)))
    if hero is not None:
        pad = '.' * max(0, (int(ww) - 4) // 2)
        rows = [(pad + r + pad)[:int(ww)].ljust(int(ww), '.') for r in _HERO_PAX[hero]]
    else:
        opts = _PAX.get(int(ww)) or _PAX[4]
        rows = opts[(seed * 7 + 3) % len(opts)]
    if rows is None:
        return None
    a = np.array([list(r) for r in rows]) == '#'
    a = a[:wh, :ww]
    m = np.zeros((h, w), bool)
    y0, x0 = int(wy), int(wx)
    m[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    return m


def paint_window_passengers(p, wx, wy, ww, wh, seed):
    """Paint the passenger silhouette(s) into a lit window of an env_veltrava_cine.Paint (ramp 'N', dark)."""
    m = window_passenger_mask(p.w, p.h, wx, wy, ww, wh, seed, getattr(getattr(p, 'L', None), 'name', ''))
    if m is not None:
        p.put(m, 'N', 0.8)


# ------------------------------------------------------------------------------------------------ extras cast
# The extras this stream places itself in LS_C3_ToHall and LS_C3_Close (the trains film is cast by the places
# builder in env_veltrava_cine_cast.py).  Written to assets/cinematics/ch3/<part>/ex_<name>.png and
# layout['<part>']['extras'] -> scenes/cinematics/ch3_common/c3_people.gd (entries as documented there).
# name, kind, height, pose, frames, facing, light, path [[t, x, y]...] (soles), stride (px per cycle, walkers),
# fps (idle), opts
CLOSE_PROJ = {'vpx': 236.0, 'vpy': 168.0, 'f': 420.0, 'eye': 1.7}


def _proj(x, z):
    """Platform 5 (LS_C3_Close n1): soles of a figure standing at lateral x, depth z (m) -> px, height px."""
    P = CLOSE_PROJ
    return P['vpx'] + P['f'] * x / z, P['vpy'] + P['f'] * P['eye'] / z, P['f'] * 1.75 / z


def _n1(name, kind, x, z, pose='stand', facing=1, light='night_lamp', fps=1.2, **opts):
    sx, sy, hpx = _proj(x, z)
    return (name, kind, round(hpx, 1), pose, 4 if pose == 'stand' else 8, facing, light,
            [[0.0, round(sx, 1), round(sy, 1)]], 0.0, fps, opts)


EXTRAS = {
    'tohall': [
        # k1 (0-3 s): the far platform under the station clock, people in the steam and the overcast light
        ('k1_porter', 'porter', 31, 'walk', 8, -1, 'day_overcast', [[0.0, 520, 298], [3.0, 448, 298]], 34.0, 0, {}),
        ('k1_woman', 'traveller_f', 29, 'walk', 8, 1, 'day_overcast', [[0.0, 292, 298], [3.0, 354, 298]], 30.0, 0,
         {}),
        ('k1_master', 'stationmaster', 32, 'stand', 4, 1, 'day_overcast', [[0.0, 252, 299]], 0.0, 1.3, {}),
        ('k1_soldier', 'police', 31, 'walk', 8, -1, 'day_overcast', [[0.0, 640, 297], [3.0, 584, 297]], 32.0, 0,
         {}),
        ('k1_man', 'man_coat', 30, 'stand', 4, -1, 'day_overcast', [[0.0, 410, 297]], 0.0, 1.0, {}),
        # k2 (3-6 s): the palais foyer at 9.40 -- an usher at the door to the hall, two delegates talking by the
        # wainscot, a secretary hurrying ahead of Konrad toward the hall with her briefcase (round 10b: she no
        # longer walks in his lane at half his pace -- he would have walked through her)
        ('k2_usher', 'usher', 92, 'stand', 4, -1, 'palais', [[3.0, 606, 304]], 0.0, 1.0, {}),
        ('k2_deleg1', 'delegate', 90, 'stand', 4, 1, 'palais', [[3.0, 494, 303]], 0.0, 0.9, {}),
        ('k2_deleg2', 'delegate', 88, 'stand', 4, -1, 'palais', [[3.0, 536, 303]], 0.0, 1.1,
         {'coat': 'charcoal', 'hair': 'dark', 'skin': 'light', 'briefcase': False}),
        ('k2_secretary', 'woman_coat', 84, 'walk', 8, 1, 'palais', [[3.0, 150, 303], [6.0, 380, 303]], 64.0, 0,
         {'coat': 'wine', 'hat': None, 'hair': 'brown', 'briefcase': True}),   # not navy: Konrad walks behind her
    ],
    'close': [
        # n1 (0-6 s): platform 5 at 23.40 -- a railwayman with his lantern at the edge, two men in long coats
        # further back watching the special train go, a policeman of the Free City by the near pillar
        _n1('n1_rail', 'railwayman', 0.25, 13.0, facing=1, fps=1.3),
        _n1('n1_watch1', 'watcher', -2.05, 19.5, facing=1, fps=0.8),
        _n1('n1_watch2', 'watcher', -2.55, 20.6, facing=1, fps=0.9, coat='charcoal'),
        _n1('n1_police', 'police', -2.75, 8.6, facing=1, fps=0.7, hands='pockets'),
        # n2 (6-12 s): the station square -- a policeman walking his beat under the lamps, the hotel doorman
        # stamping his feet, a late traveller crossing from the station toward Hotel Nord
        ('n2_police', 'police', 19, 'walk', 8, -1, 'night_lamp', [[6.0, 470, 263], [12.0, 404, 263]], 16.0, 0, {}),
        ('n2_door', 'usher', 17, 'stand', 4, 1, 'night', [[6.0, 116, 253]], 0.0, 1.5,
         {'coat': 'wine', 'hat': 'peaked', 'hat_col': 'wine'}),
        ('n2_late', 'traveller', 20, 'walk', 8, 1, 'night_lamp', [[6.0, 214, 286], [12.0, 330, 279]], 18.0, 0, {}),
    ],
}


def build_extras(part, layout_part, out_root):
    """Render the extras of `part` ('tohall' | 'close') into out_root/<part>/ex_*.png and record them in
    layout_part['extras'].  Returns the list."""
    out = []
    os.makedirs(os.path.join(out_root, part), exist_ok=True)
    names = set()
    for (name, kind, h, pose, frames, facing, light, path, stride, fps, opts) in EXTRAS.get(part, []):
        sh = person_sheet(kind, float(h), frames=frames, pose=pose, facing=facing, light=light, **opts)
        rel = '%s/ex_%s.png' % (part, name)
        from PIL import Image
        Image.fromarray(sh).save(os.path.join(out_root, rel))
        names.add('ex_%s.png' % name)
        fw = sh.shape[1] // frames
        out.append({'name': name, 'tex': rel, 'frames': frames, 'anchor': [fw // 2, int(sh.shape[0]) - 1],
                    'path': path, 'stride': stride, 'fps': fps, 'phase': (len(out) * 3) % max(1, frames)})
    # remove sheets of extras that left the cast
    d = os.path.join(out_root, part)
    for f in os.listdir(d):
        if f.startswith('ex_') and f.endswith('.png') and f not in names:
            for g in (f, f + '.import'):
                try:
                    os.remove(os.path.join(d, g))
                except OSError:
                    pass
    layout_part['extras'] = out
    return out
