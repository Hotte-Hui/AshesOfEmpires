"""chargen_body -- generic humanoid paper-doll for the character rig (side / front / back views).

A character `Spec` describes proportions, materials, garments and hand-designed bitmaps.  `render()`
turns one pose dict into a shaded cell (RGBA + normal map).  Character-specific details are added
through hook callables (spec.hooks[view] -> list of (layer, fn(fr, J, pose, spec))).

v2 (2026-11-04, round 2): orientation-aware hands (hanging / reaching / raised / open / fist), sleeve
cuffs, coat folds (height relief -> light and shadow creases), collar layer drawn over the neck, tucked
trousers, per-pose head offsets / face variants, secondary-motion signals in the pose (`lag`, `bounce`).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from chargen_core import (Bitmap, Frame, Light, Material, add, capsule, ellipse, ik2, poly, polar,
                          put_bitmap, rot, shade)

CELL_W, CELL_H = 32, 56
GROUND = 55.0          # bottom edge of the feet row (row 54 = origin pixel row)
CX = 16.5              # pelvis x (pixel centre of column 16 -> origin x = 16)


@dataclass
class Coat:
    mat: str = 'coat'
    hem: float = -6.0            # hem height relative to pelvis (v, negative = below)
    back: float = 3.5            # half depth at the back (side view)
    front: float = 3.5           # half depth at the front
    flare: float = 0.5           # extra width at the hem
    chest: float = 0.5           # chest bulge
    collar: float = 1.5          # collar height above shoulder line
    collar_mat: str | None = None
    width_f: float = 5.5         # front view half width at shoulders
    waist_f: float = 4.5         # front view half width at waist
    hem_f: float = 5.0           # front view half width at the hem
    open_front: bool = False     # front view: open coat shows the inner garment
    inner_mat: str | None = None
    belt: str | None = None      # material of a belt (or None)
    belt_v: float = 2.0
    buttons: str | None = None   # material of buttons
    quilted: bool = False        # horizontal quilting seams (telogreika / dispatcher jacket)
    skirt: bool = False          # long skirt (women) rendered as part of the hem
    R: float = 2.4
    cyl: float = 0.65
    folds: float = 0.0           # amplitude of vertical fold relief below the waist (long coats)
    hunch: float = 0.0           # extra roundness of the upper back (padded / old)


@dataclass
class Skirt:
    mat: str = 'skirt'
    top: float = 3.0            # v of the waistband
    hem: float = -15.0          # v of the hem (below pelvis)
    back: float = 3.4
    front: float = 3.4
    flare: float = 1.2
    hem_f: float = 4.6          # front view half width at the hem
    waist_f: float = 3.8
    folds: float = 0.5


@dataclass
class Spec:
    id: str
    scene: str
    mats: list                            # list[Material]
    names: dict                           # material name -> index
    light: Light
    rim: np.ndarray
    # proportions (px)
    hip_h: float = 22.0
    torso: float = 13.5
    neck: float = 2.0
    thigh: float = 10.2
    shin: float = 10.2
    ankle_h: float = 2.0
    uarm: float = 7.5
    farm: float = 6.5
    leg_r: tuple = (1.75, 1.6)            # thigh radius, shin radius
    arm_r: tuple = (1.6, 1.35)            # upper arm, forearm radius (sleeves)
    hip_f: float = 2.0                    # front view: hip joint half spacing
    sh_v: float = -1.2                    # shoulder joint v relative to torso top
    sh_u: float = -0.3                    # shoulder joint u (side view)
    lean: float = 2.0                     # default forward lean (deg)
    stoop: float = 0.0                    # extra upper-spine bend (deg)
    head_off: tuple = (0.0, 0.0)          # head anchor offset from neck
    coat: Coat = field(default_factory=Coat)
    trouser: str = 'trouser'
    sleeve: str = 'coat'
    cuff: str | None = None               # material of sleeve cuffs (None = darker sleeve tone)
    heads: dict = field(default_factory=dict)     # view -> {face: Bitmap}
    boots: dict = field(default_factory=dict)     # 'side_flat','side_heel','side_toe','front','back'
    hands: dict = field(default_factory=dict)     # see make_hands()
    hooks: dict = field(default_factory=dict)     # view -> list of (layer, fn)
    rim_strength: float = 1.0
    light_front: Light = field(default_factory=lambda: Light(
        key=(-0.72, 0.48, 0.50), rim=(0.0, 0.85, -0.5), ambient=0.16, thresholds=(0.28, 0.62, 0.82, 0.96),
        inline_dirs=((1, 0), (-1, 0), (0, 1)),
        shadow_dirs=((0, -1), (-1, -1)), rim_dirs=((0, -1),), lit_dirs=((-1, 0), (-1, -1), (0, -1))))
    light_back: Light = field(default_factory=lambda: Light(
        key=(0.70, 0.50, 0.50), rim=(0.0, 0.85, -0.5), ambient=0.16, thresholds=(0.28, 0.62, 0.82, 0.96),
        inline_dirs=((1, 0), (-1, 0), (0, 1)),
        shadow_dirs=((0, -1), (1, -1)), rim_dirs=((0, -1),), lit_dirs=((1, 0), (1, -1), (0, -1))))
    style: dict = field(default_factory=dict)     # animation style parameters
    side_arm_ao: bool = True
    skirt: Skirt | None = None
    inner: str | None = None                      # inner garment visible at the open coat front
    inner_w: float = 1.2                          # its visible width (front view half width)
    arm_front_out: float = 0.0                    # front view: extra outward shoulder offset
    leg_gap_f: bool = True                        # front view: dark gap between the legs

    def __post_init__(self):
        # standing reach, and the heel strike at full stride (contact frames sit 1 px lower)
        stride = float((self.style or {}).get('stride', 5.0))
        need = max((self.hip_h - self.ankle_h) + 0.6,
                   math.hypot(stride, self.hip_h - self.ankle_h - 1.0) + 0.05)
        if self.thigh + self.shin < need:
            k = need / (self.thigh + self.shin)
            self.thigh *= k
            self.shin *= k


def M(spec: Spec, name: str) -> int:
    return spec.names[name]


# ----------------------------------------------------------------------------------- hands
def make_hands(m='skin', kind='skin'):
    """Hand bitmaps.  Side view (facing right): chosen by forearm direction.  Letters = tones 1..4 of `m`,
    'o' = tone 0 (outline).  Anchor = wrist pixel.  kind: 'skin' (fingers + thumb), 'mitten', 'glove'."""
    lg = {'o': (m, 0), 'a': (m, 1), 'b': (m, 2), 'c': (m, 3), 'd': (m, 4), 'e': (m, 5)}
    if kind == 'mitten':
        d = {
            'down': ['bc', 'bd', 'bc', '.a'],          # hanging, thumb lump forward
            'diag': ['bcd', 'bcc', '.ab'],
            'fwd': ['bcdd', 'abcc', '..a.'],
            'up': ['.d', 'cd', 'bc', 'bc'],
            'open_fwd': ['bcdd', 'abcc', '..a.'],
            'open_up': ['.d', 'cd', 'bc', 'bc'],
            'fist': ['cd', 'bc', 'ab'],
        }
    elif kind == 'glove':
        d = {
            'down': ['bc', 'bc', 'ab'],
            'diag': ['bcd', 'abc', '.a.'],
            'fwd': ['bcd.', 'abcd', '.a..'],
            'up': ['.c', 'bd', 'bc'],
            'open_fwd': ['bcdd', 'abc.', '.a..'],
            'open_up': ['c.d', 'bcd', 'bc.'],
            'fist': ['cd', 'bc'],
        }
    else:
        d = {
            'down': ['cd', 'cd', 'bc'],                 # wrist, palm, fingers (thumb side lit)
            'diag': ['cdd', 'bcd', '.b.'],
            'fwd': ['cdd', 'bcd', '.b.'],
            'up': ['.d', 'cd', 'bc'],
            'open_fwd': ['.d.', 'cdd', 'bc.'],          # palm up, thumb raised (talk gestures)
            'open_up': ['.dd', 'cdd', 'bc.'],
            'fist': ['cd', 'bc'],
        }
    hands = {}
    for k, rows in d.items():
        hands[k] = Bitmap(rows, lg, anchor=(0, 0))
    # front / back views (hanging, seen from the front / behind)
    if kind == 'mitten':
        fl, fr_, bl, br = ['cb', 'cb', 'ba'], ['bc', 'bc', 'ab'], ['bb', 'ba', 'aa'], ['bb', 'ab', 'aa']
    else:
        fl, fr_, bl, br = ['dc', 'cb', '.b'], ['cc', 'bc', 'b.'], ['cb', 'ba'], ['bc', 'ab']
    hands['front_l'] = Bitmap(fl, lg, anchor=(1, 0))
    hands['front_r'] = Bitmap(fr_, lg, anchor=(0, 0))
    hands['back_l'] = Bitmap(bl, lg, anchor=(1, 0))
    hands['back_r'] = Bitmap(br, lg, anchor=(0, 0))
    hands['front'] = hands['front_r']
    hands['back'] = hands['back_r']
    hands['side'] = hands['down']
    return hands


def hand_for_angle(ang: float, key: str | None = None) -> str:
    """ang = forearm direction in degrees from straight down (+ forward)."""
    if key in ('fist',):
        return key
    opn = key in ('side_open', 'open')
    if ang > 120:
        return 'open_up' if opn else 'up'
    if ang > 68:
        return 'open_fwd' if opn else 'fwd'
    if ang > 32:
        return 'open_fwd' if opn else 'diag'
    return 'down'


# ----------------------------------------------------------------------------------- side view
def side_joints(spec: Spec, P: dict) -> dict:
    """Compute joint positions for the side view (facing +x)."""
    bob = P.get('bob', 0)
    lean = spec.lean + P.get('lean', 0.0)
    stoop = spec.stoop + P.get('stoop', 0.0)
    px = CX + P.get('dx', 0.0)
    py = GROUND - spec.hip_h + bob
    pelvis = (px, py)
    waist_v = 4.0

    def body(u, v):
        """Body space (u forward, v up from pelvis) -> cell coords, with lean + stoop."""
        if v <= waist_v:
            o = rot((u, -v), lean)
        else:
            w = rot((0, -waist_v), lean)
            o = add(w, rot((u, -(v - waist_v)), lean + stoop))
        return (pelvis[0] + o[0], pelvis[1] + o[1])

    def skirt(u, v, sway=0.0):
        o = rot((u, -v), lean * 0.4 + sway)
        return (pelvis[0] + o[0], pelvis[1] + o[1])

    T = spec.torso + P.get('breath', 0) * 0.9
    J = dict(pelvis=pelvis, body=body, skirt=skirt, lean=lean, stoop=stoop, T=T)
    J['neck'] = body(0.6 + spec.head_off[0], T + spec.neck + spec.head_off[1])
    sh = body(spec.sh_u, T + spec.sh_v + P.get('shrug', 0.0))
    J['sh_n'] = sh
    J['sh_f'] = (sh[0] - 0.6, sh[1])
    # arms (FK, angles from straight down, + forward)
    for side in ('n', 'f'):
        a_sh, a_el = P.get('arm_' + side, (0.0, 10.0))
        s = J['sh_' + side]
        el = polar(s, spec.uarm, a_sh + lean * 0.5)
        wr = polar(el, spec.farm, a_sh + a_el + lean * 0.5)
        J['el_' + side], J['wr_' + side] = el, wr
        J['farm_ang_' + side] = a_sh + a_el + lean * 0.5
    # legs (IK to foot targets)
    for side, hx in (('n', 0.0), ('f', -0.6)):
        fx, lift, pitch = P.get('foot_' + side, (0.0, 0.0, 0.0))
        hip = (px + hx, py)
        target = (px + fx, GROUND - spec.ankle_h - lift)
        knee, ankle = ik2(hip, target, spec.thigh, spec.shin, forward=1)
        J['hip_' + side], J['knee_' + side], J['ank_' + side] = hip, knee, ankle
        J['pitch_' + side] = pitch
    return J


def _boot_key(pitch):
    if pitch > 12:
        return 'side_heel'
    if pitch < -28:
        return 'side_toe2'
    if pitch < -8:
        return 'side_toe'
    return 'side_flat'


def draw_leg_side(fr, spec, J, side, bias=0.0):
    hip, knee, ank = J['hip_' + side], J['knee_' + side], J['ank_' + side]
    tm = M(spec, spec.trouser)
    r1, r2 = spec.leg_r
    m, x0, y0, n = capsule(hip, knee, r1, r2 * 1.05)
    fr.put(m, x0, y0, tm, n, bias=bias, name='thigh_' + side)
    m, x0, y0, n = capsule(knee, ank, r2, r2 * 0.92)
    fr.put(m, x0, y0, tm, n, bias=bias, name='shin_' + side)
    key = _boot_key(J['pitch_' + side])
    bm = spec.boots.get(key) or spec.boots['side_flat']
    put_bitmap(fr, bm, spec.names, ank[0], ank[1], name='boot_' + side, bias=bias)


def draw_arm_side(fr, spec, J, side, bias=0.0, hand_key=None):
    sh, el, wr = J['sh_' + side], J['el_' + side], J['wr_' + side]
    sm = M(spec, spec.sleeve)
    r1, r2 = spec.arm_r
    near = side == 'n'
    lift = 0.7 if near else 0.0           # the near sleeve sits closer to the key light than the torso
    m, x0, y0, n = capsule(sh, el, r1, r1 * 0.95)
    fr.put(m, x0, y0, sm, n, bias=bias + lift, name='uarm_' + side, ao=(near and spec.side_arm_ao), inline=near,
           edge_light=near)
    m, x0, y0, n = capsule(el, wr, r1 * 0.95, r2)
    fr.put(m, x0, y0, sm, n, bias=bias + lift, name='farm_' + side, ao=(near and spec.side_arm_ao), inline=near,
           edge_light=near)
    ang = J['farm_ang_' + side]
    ux, uy = math.sin(math.radians(ang)), math.cos(math.radians(ang))
    # cuff: the last ~1.3 px of the sleeve
    cx0, cy0 = wr[0] - ux * 1.3, wr[1] - uy * 1.3
    m, x0, y0, n = capsule((cx0, cy0), wr, r2 * 1.02, r2 * 1.02)
    if spec.cuff:
        fr.put(m, x0, y0, M(spec, spec.cuff), n, bias=bias, name='cuff_' + side, cast=False)
    else:
        fr.put(m, x0, y0, sm, n, bias=bias - 0.6, name='cuff_' + side, cast=False)
    if hand_key == 'hidden':
        return
    k = hand_for_angle(ang, hand_key)
    hb = spec.hands.get(k) or spec.hands['down']
    hx = wr[0] + ux * 0.9
    hy = wr[1] + uy * 0.9
    put_bitmap(fr, hb, spec.names, hx, hy, name='hand_' + side, bias=bias)


def coat_side_points(spec, J, P):
    c = spec.coat
    body, skirt = J['body'], J['skirt']
    T = J['T']
    hem = c.hem
    hf, hb = P.get('hem', (0.0, 0.0))
    knee_push = back_push = 0.0
    if hem < -2:
        # the forward knee pushes the coat front, the rear knee drags the back
        kx = max(J['knee_n'][0], J['knee_f'][0]) - J['pelvis'][0]
        knee_push = max(0.0, kx + 1.4 - (c.front + c.flare))
        kb = min(J['knee_n'][0], J['knee_f'][0]) - J['pelvis'][0]
        back_push = min(0.0, kb - 1.2 + (c.back + c.flare))
    pts = [
        body(-1.4, T + c.collar),               # collar back
        body(-c.back + 0.9 - c.hunch * 0.3, T - 0.2),   # shoulder back
        body(-c.back - c.hunch, T - 3.5),       # shoulder blade
        body(-c.back + 0.2, 4.5),               # small of the back
        body(-c.back, 0.5),                     # seat
    ]
    if hem < 0:
        pts += [skirt(-c.back - c.flare + back_push * 0.8 + hb, hem)]
        pts += [skirt(c.front + c.flare + knee_push * 0.8 + hf, hem)]
    else:
        pts += [body(-c.back, hem), body(c.front, hem)]
    pts += [
        body(c.front, 0.5),                     # front hip
        body(c.front - 0.1, 4.5),               # belly
        body(c.front + c.chest, T - 3.5),       # chest
        body(c.front - 1.2, T - 0.2),           # front shoulder
        body(1.6, T + c.collar - 0.6),          # collar front
    ]
    return pts


def _fold_relief(J, amp, view='side'):
    """Vertical fold relief below the waist: ridges whose normals catch the key light (deeper towards the
    hem, slightly diagonal so the folds fan out from the hip)."""
    py = J['pelvis'][1]
    px = J['pelvis'][0]

    def f(X, Y):
        below = np.clip((Y - (py - 2.0)) / 7.0, 0, 1)
        fan = (X - px) * (1.0 - 0.025 * (Y - py))
        return amp * 1.6 * below * (0.5 + 0.5 * np.sin(fan * 1.25 + 0.7))
    return f


def draw_skirt_side(fr, spec, J, P):
    k = spec.skirt
    body, skirt = J['body'], J['skirt']
    hf, hb = P.get('hem', (0.0, 0.0))
    kx = max(J['knee_n'][0], J['knee_f'][0]) - J['pelvis'][0]
    push = max(0.0, kx + 1.3 - (k.front + k.flare))
    kb = min(J['knee_n'][0], J['knee_f'][0]) - J['pelvis'][0]
    drag = min(0.0, kb - 1.1 + (k.back + k.flare))
    pts = [body(-k.back + 0.3, k.top), skirt(-k.back - 0.2, 0.0),
           skirt(-k.back - k.flare + drag * 0.7 + hb * 1.5, k.hem),
           skirt(k.front + k.flare + push * 0.7 + hf * 1.5, k.hem),
           skirt(k.front + 0.2, 0.0), body(k.front - 0.2, k.top)]
    m, x0, y0, n = poly(pts, R=2.0, cyl=0.7, extra_h=_fold_relief(J, k.folds) if k.folds else None)
    fr.put(m, x0, y0, M(spec, k.mat), n, name='skirt')


def draw_skirt_front(fr, spec, J, P):
    k = spec.skirt
    body = J['body']
    hl, hr = P.get('hem', (0.0, 0.0))
    pts = [body(-k.waist_f, k.top), body(-k.waist_f - 0.3, 0.0), body(-k.hem_f + hl, k.hem),
           body(k.hem_f + hr, k.hem), body(k.waist_f + 0.3, 0.0), body(k.waist_f, k.top)]
    m, x0, y0, n = poly(pts, R=2.2, cyl=0.7, extra_h=_fold_relief(J, k.folds) if k.folds else None)
    fr.put(m, x0, y0, M(spec, k.mat), n, name='skirt')


def draw_coat_side(fr, spec, J, P):
    c = spec.coat
    pts = coat_side_points(spec, J, P)
    eh = _fold_relief(J, c.folds) if c.folds else None
    m, x0, y0, n = poly(pts, R=c.R, cyl=c.cyl, extra_h=eh)
    pid = fr.put(m, x0, y0, M(spec, c.mat), n, name='coat')
    return pid, pts


def build_side(spec: Spec, P: dict):
    fr = Frame(CELL_W, CELL_H)
    J = side_joints(spec, P)
    hooks = spec.hooks.get('side', [])

    def run(layer):
        for lay, fn in hooks:
            if lay == layer:
                fn(fr, J, P, spec)
    run('back0')
    if not P.get('hide_arm_f'):
        draw_arm_side(fr, spec, J, 'f', bias=-1.0, hand_key=P.get('hand_f'))
    run('back1')
    draw_leg_side(fr, spec, J, 'f', bias=-1.0)
    draw_leg_side(fr, spec, J, 'n')
    run('legs')
    if spec.skirt is not None:
        draw_skirt_side(fr, spec, J, P)
        run('skirt')
    draw_coat_side(fr, spec, J, P)
    run('coat')
    head = spec.heads['side']
    hb = head.get(P.get('face', 'base'), head['base']) if isinstance(head, dict) else head
    hx, hy = J['neck']
    hd = P.get('head', (0, 0))
    J['head_at'] = (hx + hd[0], hy + hd[1])
    put_bitmap(fr, hb, spec.names, hx + hd[0], hy + hd[1], name='head')
    run('head')
    if not P.get('hide_arm_n'):
        draw_arm_side(fr, spec, J, 'n', hand_key=P.get('hand_n'))
    run('front')
    return fr, J


# ----------------------------------------------------------------------------------- front / back
def front_joints(spec: Spec, P: dict, back: bool = False) -> dict:
    bob = P.get('bob', 0)
    px = CX + P.get('dx', 0.0)
    py = GROUND - spec.hip_h + bob
    pelvis = (px, py)
    T = spec.torso + P.get('breath', 0) * 0.9
    sway = P.get('sway', 0.0)
    stoop_drop = spec.stoop * 0.06 + P.get('stoop', 0.0) * 0.06

    def body(u, v):
        return (pelvis[0] + u + sway * (v / max(1.0, T)), pelvis[1] - v + (stoop_drop if v > 8 else 0))
    J = dict(pelvis=pelvis, body=body, back=back, T=T)
    J['neck'] = body(0.0, T + spec.neck)
    c = spec.coat
    for side, sgn in (('l', -1), ('r', 1)):
        sh = body(sgn * (c.width_f - 1.2 + spec.arm_front_out), T + spec.sh_v + P.get('shrug', 0.0))
        J['sh_' + side] = sh
        abd, swing, flex = P.get('arm_' + side, (6.0, 0.0, 6.0))
        # abduction rotates outward in the picture plane; swing foreshortens the arm
        fs = 1.0 - 0.18 * abs(swing)
        el = (sh[0] + sgn * math.sin(math.radians(abd)) * spec.uarm,
              sh[1] + math.cos(math.radians(abd)) * spec.uarm * fs)
        a2 = abd + flex * 0.4
        wr = (el[0] + sgn * math.sin(math.radians(a2)) * spec.farm * 0.9,
              el[1] + math.cos(math.radians(a2)) * spec.farm * fs * (1 - 0.25 * max(0.0, swing if not back else -swing)))
        J['el_' + side], J['wr_' + side] = el, wr
        J['swing_' + side] = swing
        dy, lift = P.get('foot_' + side, (0.0, 0.0))
        hip = (px + sgn * spec.hip_f, py)
        ank = (px + sgn * (spec.hip_f + 0.0), GROUND - spec.ankle_h + dy - lift)
        J['hip_' + side], J['ank_' + side], J['lift_' + side], J['dy_' + side] = hip, ank, lift, dy
        L = spec.thigh + spec.shin
        d = ank[1] - hip[1]
        kt = spec.thigh / L
        J['knee_' + side] = (hip[0], hip[1] + d * kt)
    return J


def draw_leg_front(fr, spec, J, side, back=False, bias=0.0):
    hip, knee, ank = J['hip_' + side], J['knee_' + side], J['ank_' + side]
    tm = M(spec, spec.trouser)
    r1, r2 = spec.leg_r
    m, x0, y0, n = capsule(hip, knee, r1, r2)
    fr.put(m, x0, y0, tm, n, bias=bias, name='thigh_' + side, inline=True)
    m, x0, y0, n = capsule(knee, ank, r2, r2 * 0.95)
    fr.put(m, x0, y0, tm, n, bias=bias, name='shin_' + side, inline=True)
    key = 'back' if back else 'front'
    bm = spec.boots[key]
    if side == 'l' and (key + '_l') in spec.boots:
        bm = spec.boots[key + '_l']
    elif side == 'r' and (key + '_r') in spec.boots:
        bm = spec.boots[key + '_r']
    put_bitmap(fr, bm, spec.names, ank[0], ank[1], name='boot_' + side, bias=bias)


def coat_front_points(spec, J, P):
    c = spec.coat
    body = J['body']
    T = J['T']
    hem = c.hem
    hl, hr = P.get('hem', (0.0, 0.0))
    W, Wa = c.width_f, c.waist_f
    pts = [
        body(-2.0, T + c.collar), body(-W + 1.0, T + 0.5), body(-W, T - 0.9),
        body(-Wa - 0.4, T - 5.5), body(-Wa, 3.0), body(-Wa - 0.1, 0.0),
    ]
    if hem < 0:
        pts += [body(-c.hem_f - c.flare + hl, hem), body(c.hem_f + c.flare + hr, hem)]
    else:
        pts += [body(-Wa, hem), body(Wa, hem)]
    pts += [
        body(Wa + 0.1, 0.0), body(Wa, 3.0), body(Wa + 0.4, T - 5.5),
        body(W, T - 0.9), body(W - 1.0, T + 0.5), body(2.0, T + c.collar),
    ]
    return pts


def draw_arm_front(fr, spec, J, side, bias=0.0, back=False, hand_key=None):
    sh, el, wr = J['sh_' + side], J['el_' + side], J['wr_' + side]
    sm = M(spec, spec.sleeve)
    r1, r2 = spec.arm_r
    m, x0, y0, n = capsule(sh, el, r1, r1 * 0.95)
    fr.put(m, x0, y0, sm, n, bias=bias, name='uarm_' + side, ao=True, inline=True, edge_light=True)
    m, x0, y0, n = capsule(el, wr, r1 * 0.95, r2)
    fr.put(m, x0, y0, sm, n, bias=bias, name='farm_' + side, ao=True, inline=True, edge_light=True)
    # cuff
    m, x0, y0, n = capsule((wr[0], wr[1] - 1.2), wr, r2 * 1.02, r2 * 1.02)
    if spec.cuff:
        fr.put(m, x0, y0, M(spec, spec.cuff), n, bias=bias, name='cuff_' + side, cast=False)
    else:
        fr.put(m, x0, y0, sm, n, bias=bias - 0.6, name='cuff_' + side, cast=False)
    if hand_key == 'hidden':
        return
    key = ('back' if back else 'front')
    hb = spec.hands.get(key + '_' + side) or spec.hands.get(key) or spec.hands['front']
    put_bitmap(fr, hb, spec.names, wr[0], wr[1] + 0.6, name='hand_' + side, bias=bias)


def build_front(spec: Spec, P: dict, back: bool = False):
    fr = Frame(CELL_W, CELL_H)
    J = front_joints(spec, P, back)
    view = 'back' if back else 'front'
    hooks = spec.hooks.get(view, [])

    def run(layer):
        for lay, fn in hooks:
            if lay == layer:
                fn(fr, J, P, spec)
    run('back0')
    # legs: the one stepping towards the camera (larger dy) is drawn last
    order = sorted(('l', 'r'), key=lambda s: J['dy_' + s] * (-1 if back else 1))
    for s in order:
        draw_leg_front(fr, spec, J, s, back=back)
    run('legs')
    if spec.skirt is not None:
        draw_skirt_front(fr, spec, J, P)
        run('skirt')
    c = spec.coat
    pts = coat_front_points(spec, J, P)
    eh = _fold_relief(J, c.folds * 0.8, 'front') if c.folds else None
    m, x0, y0, n = poly(pts, R=c.R + 0.6, cyl=c.cyl, extra_h=eh)
    fr.put(m, x0, y0, M(spec, c.mat), n, name='coat')
    if spec.inner and not back:
        T = J['T']
        iw = spec.inner_w
        ipts = [J['body'](-iw, T + 0.2), J['body'](-iw * 0.6, 1.0), J['body'](iw * 0.6, 1.0), J['body'](iw, T + 0.2)]
        m, x0, y0, n = poly(ipts, R=1.2, cyl=0.3)
        fr.put(m, x0, y0, M(spec, spec.inner), n, name='inner', cast=False)
    run('coat')
    for s in ('l', 'r'):
        sw = J['swing_' + s]
        draw_arm_front(fr, spec, J, s, bias=(-0.5 if (sw < -0.3 and not back) else 0.0), back=back,
                       hand_key=P.get('hand_' + s))
    run('arms')
    head = spec.heads.get(view) or spec.heads['front']
    hb = head.get(P.get('face', 'base'), head['base']) if isinstance(head, dict) else head
    hx, hy = J['neck']
    hd = P.get('head', (0, 0))
    J['head_at'] = (hx + hd[0], hy + hd[1])
    put_bitmap(fr, hb, spec.names, hx + hd[0], hy + hd[1], name='head')
    run('head')
    run('front')
    return fr, J


def render(spec: Spec, view: str, P: dict):
    if view == 'side':
        fr, J = build_side(spec, P)
        light = spec.light
    else:
        fr, J = build_front(spec, P, back=(view == 'back'))
        light = spec.light_front if view == 'front' else spec.light_back
    rim_ymax = J['pelvis'][1] - (1 if view == 'side' else 6)
    rgba, nm, tone = shade(fr, spec.mats, light, rim_color=spec.rim, rim_strength=spec.rim_strength,
                           rim_ymax=rim_ymax)
    return rgba, nm, fr, J
