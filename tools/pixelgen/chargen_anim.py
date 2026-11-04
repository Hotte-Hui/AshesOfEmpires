"""chargen_anim -- keyframed poses for the character rig.

Every animation is a list of pose dicts (one per frame, held -- never tweened at runtime).
Side poses: arm_* = (shoulder deg, elbow deg) measured from straight down, + = forward;
foot_* = (ankle x relative to pelvis, lift px, foot pitch deg) solved by 2-bone IK.
Front/back poses: arm_* = (abduction deg, swing -1..1, elbow flex deg), foot_* = (depth dy px, lift px).
`style` (per character) scales stride, swing, bob and lean so each silhouette moves differently.
"""
from __future__ import annotations

import math

DEFAULT_STYLE = dict(
    stride=5.0,        # half stride (px) at contact
    swing=22.0,        # arm swing amplitude (deg)
    elbow=10.0,        # resting elbow flex (deg)
    bob=1,             # vertical bob on the down frames (px)
    up=0,              # extra rise on the up frames (px, negative = higher)
    walk_lean=3.0,     # extra lean while walking (deg)
    lift=3.0,          # passing foot lift (px)
    idle_feet=(1.5, -1.5),
    hem=0.6,           # coat hem lag amplitude (px)
    arm_n_idle=(7.0, 10.0),
    arm_f_idle=(-4.0, 8.0),
    hold_n=None,       # if set: near arm locked in this pose (props held in hand)
    hold_f=None,
    front_swing=1.0,
    front_abd=7.0,
)


def st(style: dict | None) -> dict:
    s = dict(DEFAULT_STYLE)
    if style:
        s.update(style)
    return s


# ----------------------------------------------------------------------------------- side
def walk_side(style=None):
    s = st(style)
    S = s['stride']
    L = s['lift']
    # near-leg cycle (8 frames); far leg = same cycle shifted by 4
    leg = [
        (+S, 0.0, +16),            # 0 contact (heel strike)
        (+S * 0.55, 0.0, 0),       # 1 down (flat, weight accept)
        (+S * 0.05, 0.0, 0),       # 2 passing (support)
        (-S * 0.5, 0.0, -6),       # 3 up (heel starts to rise)
        (-S * 0.95, 0.6, -24),     # 4 contact of the other foot: toe-off
        (-S * 0.75, L * 0.7, -32), # 5 lift
        (-S * 0.05, L, -6),        # 6 passing (knee forward)
        (+S * 0.75, L * 0.45, +8), # 7 reaching forward
    ]
    bob = [0, s['bob'], 0, s['up'], 0, s['bob'], 0, s['up']]
    frames = []
    for i in range(8):
        ph = 2 * math.pi * (i - 0.5) / 8.0
        a = -s['swing'] * math.cos(ph)            # near arm: back when near leg forward
        el_n = s['elbow'] + max(0.0, a) * 0.55
        el_f = s['elbow'] + max(0.0, -a) * 0.55
        hem_lag = -s['hem'] * math.sin(2 * math.pi * (i + 1) / 4.0)
        P = dict(
            bob=bob[i], lean=s['walk_lean'],
            foot_n=leg[i], foot_f=leg[(i + 4) % 8],
            arm_n=(a, el_n), arm_f=(-a, el_f),
            hem=(hem_lag, hem_lag * 0.5 - 0.3),
            face='base', phase=i, dx=s.get('dx', 0.0),
        )
        if s['hold_n'] is not None:
            P['arm_n'] = s['hold_n']
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


def idle_side(style=None):
    s = st(style)
    fn, ff = s['idle_feet']
    breath = [0, 0, 1, 1, 0, 0]
    frames = []
    for i in range(6):
        P = dict(
            bob=0, lean=0.0,
            foot_n=(fn, 0.0, 0), foot_f=(ff, 0.0, 0),
            arm_n=(s['arm_n_idle'][0], s['arm_n_idle'][1] + breath[i] * 2),
            arm_f=(s['arm_f_idle'][0], s['arm_f_idle'][1]),
            breath=breath[i], face='blink' if i == 4 else 'base', phase=i, dx=s.get('dx', 0.0),
        )
        if s['hold_n'] is not None:
            P['arm_n'] = s['hold_n']
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


def inspect_side(style=None):
    s = st(style)
    keys = [
        # lean, stoop, arm_n (hand comes up to the chin), head, bob, face
        (-1.0, 0.0, (4.0, 18.0), (0, 0), 0, 'base'),
        (6.0, 3.0, (8.0, 70.0), (0, 0), 0, 'base'),
        (12.0, 6.0, (6.0, 112.0), (1, 0), 1, 'base'),
        (14.0, 7.0, (4.0, 122.0), (1, 1), 1, 'base'),
        (14.0, 7.0, (4.0, 122.0), (1, 1), 1, 'blink'),
        (14.0, 7.0, (4.0, 124.0), (1, 1), 1, 'base'),
    ]
    frames = []
    for i, (lean, stoop, arm, head, bob, face) in enumerate(keys):
        P = dict(bob=bob, lean=lean, stoop=stoop, foot_n=(3.0, 0.0, 0), foot_f=(-2.5, 0.0, 0),
                 arm_n=arm, arm_f=(-6.0, 14.0), head=head, face=face, hand_n='side', phase=i,
                 dx=s.get('dx', 0.0) - 1.0)
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


def interact_side(style=None):
    s = st(style)
    keys = [
        (-1.0, (-8.0, 22.0), 0, (1.5, 0.0, 0), 'side'),
        (4.0, (34.0, 30.0), 0, (3.0, 0.0, 0), 'side_open'),
        (5.0, (48.0, 12.0), 1, (4.0, 0.0, 0), 'side_open'),
        (5.0, (50.0, 9.0), 1, (4.0, 0.0, 0), 'side_open'),
    ]
    frames = []
    for i, (lean, arm, bob, fn, hand) in enumerate(keys):
        P = dict(bob=bob, lean=lean, foot_n=fn, foot_f=(-2.5, 0.0, 0), arm_n=arm, arm_f=(-8.0, 12.0),
                 hand_n=hand, face='base', phase=i, dx=s.get('dx', 0.0) - 2.0)
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


def talk_side(style=None):
    s = st(style)
    fn, ff = s['idle_feet']
    keys = [
        ((10.0, 48.0), 'base', (0, 0), 'side'),
        ((16.0, 66.0), 'talk', (0, 0), 'side_open'),
        ((13.0, 58.0), 'base', (0, 1), 'side_open'),
        ((9.0, 44.0), 'talk', (0, 0), 'side'),
    ]
    frames = []
    for i, (arm, face, head, hand) in enumerate(keys):
        P = dict(bob=0, lean=0.0, foot_n=(fn, 0.0, 0), foot_f=(ff, 0.0, 0), arm_n=arm,
                 arm_f=s['arm_f_idle'], face=face, head=head, hand_n=hand, phase=i, dx=s.get('dx', 0.0))
        if s.get('talk_n') is not None:
            P['arm_n'] = s['talk_n'][i]
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


# ----------------------------------------------------------------------------------- front / back
def idle_front(style=None):
    s = st(style)
    breath = [0, 0, 1, 1, 0, 0]
    a = s['front_abd']
    return [dict(bob=0, foot_l=(0.0, 0.0), foot_r=(0.0, 0.0), arm_l=(a, 0.0, 6.0), arm_r=(a, 0.0, 6.0),
                 breath=breath[i], face='blink' if i == 4 else 'base', phase=i) for i in range(6)]


def walk_front(style=None, back=False):
    s = st(style)
    L = s['lift']
    # (depth dy, lift) for the left leg; right = shifted by 4
    leg = [(0.0, 0.0), (-0.5, 0.0), (-1.0, 0.0), (-1.5, 0.0), (-2.0, 0.8), (-1.5, L * 0.75), (-1.0, L * 0.9),
           (-0.4, L * 0.4)]
    bob = [0, s['bob'], 0, s['up'], 0, s['bob'], 0, s['up']]
    frames = []
    a = s['front_abd']
    for i in range(8):
        ph = 2 * math.pi * (i - 0.5) / 8.0
        sw = -math.cos(ph) * s['front_swing']     # left arm swing (+ = forward)
        frames.append(dict(
            bob=bob[i], foot_l=leg[i], foot_r=leg[(i + 4) % 8],
            arm_l=(a, sw, 8.0 + max(0, sw) * 14), arm_r=(a, -sw, 8.0 + max(0, -sw) * 14),
            sway=0.0, hem=(0.0, 0.0), face='base', phase=i))
    return frames
