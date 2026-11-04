"""chargen_anim -- keyframed poses for the character rig.

Every animation is a list of pose dicts (one per frame, held -- never tweened at runtime).
Side poses: arm_* = (shoulder deg, elbow deg) measured from straight down, + = forward;
foot_* = (ankle x relative to pelvis, lift px, foot pitch deg) solved by 2-bone IK.
Front/back poses: arm_* = (abduction deg, swing -1..1, elbow flex deg), foot_* = (depth dy px, lift px).
`style` (per character) scales stride, swing, bob and lean so each silhouette moves differently.

v2 (round 2): walk with uniform planted-foot travel (ground speed = 5 * stride px/s at 10 fps), weight
shift (bob + lean pulse + shoulder drop) and secondary-motion signals for hooks:
  P['lag']    -1..1  horizontal lag of loose items (scarf ends, ear-flaps, bags) behind the body
  P['bounce'] -1/0/1 vertical lag of loose items (they stay up when the body drops, and vice versa)
  P['hem']    (front, back) coat-hem offsets
Idle 8 frames (two-stage breathing, no blink), plus variant rows the runtime mixes in occasionally:
blink, look (glance back over the shoulder), gesture (character-specific: rub/blow hands, adjust hat,
check watch, push glasses ...), and optional work loops (pour tea, stamp cards, warm hands ...).
Talk = 8 frames with two different hand gestures, a nod and mouth shapes.
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
    gesture='shift',   # idle gesture variant (see GESTURES)
    work=None,         # optional work loop (see WORKS)
    talk_n=None,       # optional 8 (or 4) talk arm poses for the near arm
    talk_f=None,
)


def st(style: dict | None) -> dict:
    s = dict(DEFAULT_STYLE)
    if style:
        s.update(style)
    return s


def _held(P, s, near=True, far=True):
    if near and s['hold_n'] is not None:
        P['arm_n'] = s['hold_n']
    if far and s['hold_f'] is not None:
        P['arm_f'] = s['hold_f']
    return P


def idle_pose(s, i=0, breath=0):
    fn, ff = s['idle_feet']
    P = dict(bob=0, lean=0.0, foot_n=(fn, 0.0, 0), foot_f=(ff, 0.0, 0),
             arm_n=(s['arm_n_idle'][0], s['arm_n_idle'][1] + breath * 2),
             arm_f=(s['arm_f_idle'][0], s['arm_f_idle'][1] + breath),
             breath=breath, face='base', phase=i, dx=s.get('dx', 0.0), lag=0.0, bounce=0)
    return _held(P, s)


# ----------------------------------------------------------------------------------- side
def walk_side(style=None):
    s = st(style)
    S = s['stride']
    L = s['lift']
    # near-leg cycle (8 frames); far leg = same cycle shifted by 4.  Planted foot travels uniformly
    # 0.5*S per frame (frames 0..4) -> ground speed = 2*S / 0.4 s = 5*S px/s at 10 fps.
    leg = [
        (+S, 0.0, +14),            # 0 contact (heel strike)
        (+S * 0.5, 0.0, 0),        # 1 down (flat, weight accept)
        (0.0, 0.0, 0),             # 2 passing (support)
        (-S * 0.5, 0.0, -8),       # 3 up (heel starts to rise)
        (-S, 0.6, -26),            # 4 toe-off (other foot strikes)
        (-S * 0.62, L * 0.75, -34),  # 5 lift
        (-S * 0.02, L, -8),        # 6 passing (knee forward)
        (+S * 0.68, L * 0.4, +8),  # 7 reaching forward
    ]
    # contact + down frames sit 1 px lower (legs spread / weight accept), passing + up frames high
    bob = [s['bob'], s['bob'], 0, s['up'], s['bob'], s['bob'], 0, s['up']]
    frames = []
    for i in range(8):
        ph = 2 * math.pi * (i - 0.6) / 8.0
        a = -s['swing'] * math.cos(ph)            # near arm: back when near leg forward
        el_n = s['elbow'] + max(0.0, a) * 0.6
        el_f = s['elbow'] + max(0.0, -a) * 0.6
        hem_lag = -s['hem'] * math.sin(2 * math.pi * (i + 1) / 4.0)
        lag = math.sin(2 * math.pi * (i - 1.0) / 4.0)          # loose items swing behind the steps
        bounce = bob[(i - 1) % 8] - bob[i]
        P = dict(
            bob=bob[i], lean=s['walk_lean'] + (0.8 if i in (1, 5) else 0.0),
            foot_n=leg[i], foot_f=leg[(i + 4) % 8],
            arm_n=(a, el_n), arm_f=(-a, el_f),
            hem=(hem_lag, hem_lag * 0.5 - 0.3),
            shrug=(-0.4 if i in (1, 5) else 0.0),
            face='base', phase=i, dx=s.get('dx', 0.0), lag=lag, bounce=bounce, walking=True,
        )
        frames.append(_held(P, s))
    return frames


def idle_side(style=None):
    """8 frames @5 fps: inhale over frames 2-4 (chest + shoulders rise 1 px), exhale, rest."""
    s = st(style)
    breath = [0, 0, 1, 1, 1, 0, 0, 0]
    return [idle_pose(s, i, breath[i]) for i in range(8)]


def blink_side(style=None):
    s = st(style)
    out = []
    for i, f in enumerate(('base', 'blink', 'base')):
        P = idle_pose(s, i)
        P['face'] = f
        out.append(P)
    return out


def look_side(style=None):
    """Glance back over the shoulder and return (head flips, shoulders follow a little)."""
    s = st(style)
    seq = [('base', 0, 0.0), ('base', 0, -0.6), ('look', 0, -1.2), ('look', 1, -1.2), ('look', 1, -1.2),
           ('look', 1, -1.2), ('look', 0, -1.0), ('look', 0, -1.2), ('base', 0, -0.6), ('base', 0, 0.0)]
    out = []
    for i, (face, br, lean) in enumerate(seq):
        P = idle_pose(s, i, br)
        P['face'] = face
        P['lean'] = lean
        out.append(P)
    return out


def _gesture_frames(s, keys):
    """keys: list of dicts with overrides on the idle pose."""
    out = []
    for i, k in enumerate(keys):
        P = idle_pose(s, i, k.get('breath', 0))
        P.update(k)
        out.append(P)
    return out


GESTURES = {
    # cold: rub the hands in front of the chest, then blow warm air into them
    'blow_hands': [
        {}, {'arm_n': (6, 62), 'arm_f': (10, 64), 'hand_n': 'fist', 'hand_f': 'fist'},
        {'arm_n': (8, 68), 'arm_f': (8, 58), 'hand_n': 'fist', 'hand_f': 'fist'},
        {'arm_n': (6, 60), 'arm_f': (10, 68), 'hand_n': 'fist', 'hand_f': 'fist'},
        {'arm_n': (8, 68), 'arm_f': (8, 58), 'hand_n': 'fist', 'hand_f': 'fist'},
        {'arm_n': (10, 112), 'arm_f': (14, 106), 'hand_n': 'fist', 'hand_f': 'fist', 'lean': 2.0, 'head': (0, 1)},
        {'arm_n': (10, 118), 'arm_f': (14, 110), 'hand_n': 'fist', 'hand_f': 'fist', 'lean': 2.0, 'head': (0, 1),
         'face': 'talk', 'puff': 1},
        {'arm_n': (10, 118), 'arm_f': (14, 110), 'hand_n': 'fist', 'hand_f': 'fist', 'lean': 2.0, 'head': (0, 1),
         'face': 'talk', 'puff': 2},
        {'arm_n': (8, 66), 'arm_f': (10, 62), 'hand_n': 'fist', 'hand_f': 'fist', 'puff': 3},
        {},
    ],
    # touch / straighten the hat brim (fedora) or the cap
    'adjust_hat': [
        {}, {'arm_n': (30, 60)}, {'arm_n': (52, 112), 'head': (0, 1)}, {'arm_n': (56, 126), 'head': (0, 1)},
        {'arm_n': (58, 130), 'head': (0, 1), 'face': 'blink'}, {'arm_n': (56, 126), 'head': (0, 1)},
        {'arm_n': (34, 70)}, {},
    ],
    # look at the wristwatch: forearm raised across the body, head bends down
    'check_watch': [
        {}, {'arm_n': (20, 60)}, {'arm_n': (26, 92), 'head': (0, 1), 'lean': 2.0},
        {'arm_n': (26, 96), 'head': (0, 1), 'lean': 2.5}, {'arm_n': (26, 96), 'head': (0, 1), 'lean': 2.5},
        {'arm_n': (26, 96), 'head': (0, 1), 'lean': 2.5, 'face': 'blink'}, {'arm_n': (22, 70), 'lean': 1.0}, {},
    ],
    # push the spectacles up the nose
    'push_glasses': [
        {}, {'arm_n': (14, 60)}, {'arm_n': (30, 124), 'head': (0, 1)}, {'arm_n': (32, 132)},
        {'arm_n': (32, 132), 'face': 'blink'}, {'arm_n': (22, 92)}, {},
    ],
    # wipe the forehead with the back of the hand
    'wipe_brow': [
        {}, {'arm_n': (30, 80)}, {'arm_n': (46, 128), 'head': (0, 1)}, {'arm_n': (40, 134), 'head': (0, 1)},
        {'arm_n': (34, 136), 'head': (0, 1), 'face': 'blink'}, {'arm_n': (30, 90)}, {},
    ],
    # weight shift: settle on the back foot, roll the shoulders, back
    'shift': [
        {}, {'dx': -0.6, 'lean': -1.0}, {'dx': -1.0, 'lean': -1.5, 'shrug': 0.6, 'breath': 1},
        {'dx': -1.0, 'lean': -1.5, 'shrug': 0.6, 'breath': 1}, {'dx': -0.8, 'lean': -1.0}, {'dx': -0.4},
        {}, {},
    ],
    # rise onto the toes and settle (guard)
    'rock_heels': [
        {}, {'bob': -1, 'foot_n': (1.5, 1.0, -20), 'foot_f': (-1.5, 1.0, -20)},
        {'bob': -1, 'foot_n': (1.5, 1.0, -20), 'foot_f': (-1.5, 1.0, -20)}, {}, {}, {'face': 'blink'}, {},
    ],
    # hop on the spot (child)
    'hop': [
        {}, {'bob': 1}, {'bob': -2, 'foot_n': (1.0, 2.0, -10), 'foot_f': (-1.0, 2.0, -10), 'arm_n': (30, 40)},
        {'bob': -2, 'foot_n': (1.0, 2.0, -10), 'foot_f': (-1.0, 2.0, -10), 'arm_n': (36, 40)}, {'bob': 1}, {},
        {'bob': 1}, {'bob': -2, 'foot_n': (1.0, 2.0, -10), 'foot_f': (-1.0, 2.0, -10), 'arm_n': (30, 40)},
        {'bob': 1}, {},
    ],
    # hitch a heavy load up (father with the crate)
    'hitch': [{}, {'bob': 1}, {'bob': -1, 'shrug': 0.8}, {'bob': -1, 'shrug': 0.8}, {}, {'face': 'blink'}, {}],
    # hand to the throat / scarf knot or tie
    'touch_collar': [
        {}, {'arm_n': (12, 64)}, {'arm_n': (22, 112)}, {'arm_n': (22, 118), 'head': (0, 1)},
        {'arm_n': (24, 114), 'head': (0, 1)}, {'arm_n': (22, 118), 'face': 'blink'}, {'arm_n': (14, 70)}, {},
    ],
    # hug the toy closer, sway
    'hug': [{}, {'dx': 0.5}, {'dx': 0.8, 'head': (0, 1)}, {'dx': 0.8, 'head': (0, 1), 'face': 'blink'},
            {'dx': 0.4}, {}],
}

WORKS = {
    # pour tea: teapot hand rises, tilts, holds, returns (8 frames, loop)
    'pour': [
        {'arm_n': (22, 58), 'tilt': 0, 'dx': -1.5}, {'arm_n': (28, 62), 'tilt': 0, 'dx': -1.5},
        {'arm_n': (32, 66), 'tilt': 1, 'head': (0, 1), 'dx': -1.5},
        {'arm_n': (34, 68), 'tilt': 2, 'head': (0, 1), 'stream': 1, 'dx': -1.5},
        {'arm_n': (34, 68), 'tilt': 2, 'head': (0, 1), 'stream': 2, 'dx': -1.5},
        {'arm_n': (34, 68), 'tilt': 2, 'head': (0, 1), 'stream': 1, 'dx': -1.5},
        {'arm_n': (30, 64), 'tilt': 1, 'dx': -1.5}, {'arm_n': (24, 60), 'tilt': 0, 'dx': -1.5},
    ],
    # stamp an index card on the desk
    'stamp': [
        {'arm_n': (30, 70)}, {'arm_n': (36, 96), 'head': (0, 1)}, {'arm_n': (40, 112), 'head': (0, 1)},
        {'arm_n': (30, 62), 'head': (0, 1), 'thump': 1}, {'arm_n': (30, 62), 'head': (0, 1)},
        {'arm_n': (32, 78)}, {'arm_n': (30, 70), 'face': 'blink'}, {'arm_n': (30, 70)},
    ],
    # warm the hands over a fire: both forearms forward, palms down, small rubbing
    'warm': [
        {'arm_n': (26, 52), 'arm_f': (30, 50), 'lean': 3.0, 'dx': -1.0},
        {'arm_n': (28, 54), 'arm_f': (28, 46), 'lean': 3.0, 'dx': -1.0},
        {'arm_n': (26, 50), 'arm_f': (30, 52), 'lean': 3.0, 'dx': -1.0},
        {'arm_n': (28, 54), 'arm_f': (28, 48), 'lean': 3.0, 'dx': -1.0, 'face': 'blink'},
        {'arm_n': (26, 52), 'arm_f': (30, 50), 'lean': 3.0, 'dx': -1.0},
        {'arm_n': (28, 54), 'arm_f': (28, 46), 'lean': 3.0, 'dx': -1.0, 'breath': 1},
    ],
    # pocket watch: take it out, look, put back (porter)
    'watch': [
        {}, {'arm_n': (16, 62)}, {'arm_n': (22, 86), 'head': (0, 1), 'lean': 1.5},
        {'arm_n': (22, 90), 'head': (0, 1), 'lean': 2.0, 'watch': 1},
        {'arm_n': (22, 90), 'head': (0, 1), 'lean': 2.0, 'watch': 1},
        {'arm_n': (22, 90), 'head': (0, 1), 'lean': 2.0, 'watch': 1, 'face': 'blink'},
        {'arm_n': (18, 66)}, {}, {}, {},
    ],
}


def gesture_side(style=None):
    s = st(style)
    keys = GESTURES.get(s['gesture']) or GESTURES['shift']
    out = _gesture_frames(s, keys)
    hold_far_only = s.get('gesture_keep_hold', True)
    for P, k in zip(out, keys):
        if hold_far_only and s['hold_f'] is not None and 'arm_f' not in k:
            P['arm_f'] = s['hold_f']
        if s['hold_n'] is not None and 'arm_n' not in k:
            P['arm_n'] = s['hold_n']
    return out


def work_side(style=None):
    s = st(style)
    keys = WORKS.get(s['work']) or WORKS['warm']
    return _gesture_frames(s, keys)


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
                 arm_n=arm, arm_f=(-6.0, 14.0), head=head, face=face, hand_n='fist' if i >= 3 else None,
                 phase=i, dx=s.get('dx', 0.0) - 1.0, lag=0.0, bounce=0)
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


def interact_side(style=None):
    s = st(style)
    keys = [
        (-1.5, (-10.0, 24.0), 0, (1.5, 0.0, 0), None),        # anticipation: pull back
        (3.0, (26.0, 36.0), 0, (3.0, 0.0, 0), 'open'),
        (4.5, (40.0, 18.0), 1, (4.0, 0.0, 0), 'open'),
        (4.5, (42.0, 14.0), 1, (4.0, 0.0, 0), 'open'),
        (4.0, (40.0, 16.0), 1, (4.0, 0.0, 0), 'open'),
    ]
    frames = []
    for i, (lean, arm, bob, fn, hand) in enumerate(keys):
        P = dict(bob=bob, lean=lean, foot_n=fn, foot_f=(-2.5, 0.0, 0), arm_n=arm, arm_f=(-8.0, 12.0),
                 hand_n=hand, face='base', phase=i, dx=s.get('dx', 0.0) - 2.0, lag=0.0, bounce=0)
        if s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


TALK_DEFAULT = [
    # (arm_n, face, head, hand): rest, lift, open-palm beat with a nod, settle, small second beat, rest
    ((8.0, 28.0), 'base', (0, 0), None),
    ((10.0, 50.0), 'talk', (0, 0), None),
    ((14.0, 64.0), 'base', (0, 0), 'open'),
    ((16.0, 70.0), 'talk', (0, 1), 'open'),       # beat + nod
    ((14.0, 62.0), 'base', (0, 0), 'open'),
    ((10.0, 46.0), 'talk', (0, 0), None),
    ((12.0, 56.0), 'base', (0, 0), 'open'),
    ((8.0, 34.0), 'talk', (0, 0), None),
]


def talk_side(style=None):
    s = st(style)
    fn, ff = s['idle_feet']
    frames = []
    for i, (arm, face, head, hand) in enumerate(TALK_DEFAULT):
        P = dict(bob=0, lean=0.0, foot_n=(fn, 0.0, 0), foot_f=(ff, 0.0, 0), arm_n=arm,
                 arm_f=s['arm_f_idle'], face=face, head=head, hand_n=hand, phase=i, dx=s.get('dx', 0.0),
                 breath=(1 if i in (2, 3, 4) else 0), lag=0.0, bounce=0)
        if s.get('talk_n') is not None:
            tn = s['talk_n']
            P['arm_n'] = tn[i % len(tn)] if len(tn) == 8 else tn[(i // 2) % len(tn)]
            if len(tn) != 8:
                P['hand_n'] = 'open' if i in (2, 3, 4, 6) else None
        elif s['hold_n'] is not None:
            P['arm_n'] = s['hold_n']
            P['hand_n'] = None
        if s.get('talk_f') is not None:
            P['arm_f'] = s['talk_f'][i % len(s['talk_f'])]
        elif s['hold_f'] is not None:
            P['arm_f'] = s['hold_f']
        frames.append(P)
    return frames


# ----------------------------------------------------------------------------------- front / back
def idle_front(style=None):
    s = st(style)
    breath = [0, 0, 1, 1, 1, 0, 0, 0]
    a = s['front_abd']
    return [dict(bob=0, foot_l=(0.0, 0.0), foot_r=(0.0, 0.0), arm_l=(a, 0.0, 6.0 + breath[i] * 2),
                 arm_r=(a, 0.0, 6.0 + breath[i] * 2), breath=breath[i], face='base', phase=i, lag=0.0,
                 bounce=0) for i in range(8)]


def blink_front(style=None):
    out = idle_front(style)[:3]
    out[1] = dict(out[1])
    out[1]['face'] = 'blink'
    return out


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
        # weight shift: the body leans over the supporting leg (left leg supports frames 0-3)
        sway = 0.5 * math.sin(2 * math.pi * (i - 1) / 8.0)
        frames.append(dict(
            bob=bob[i], foot_l=leg[i], foot_r=leg[(i + 4) % 8],
            arm_l=(a, sw, 8.0 + max(0, sw) * 14), arm_r=(a, -sw, 8.0 + max(0, -sw) * 14),
            sway=sway * (-1 if back else 1), hem=(0.3 * sway, 0.3 * sway), face='base', phase=i,
            lag=math.sin(2 * math.pi * (i - 1.0) / 4.0), bounce=bob[(i - 1) % 8] - bob[i], walking=True))
    return frames
