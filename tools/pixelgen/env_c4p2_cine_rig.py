"""env_c4p2_cine_rig -- the people of the Chapter-4-part-2 wide shots on the game's own rig (owner: cine stream).

Poses are chargen_anim-style pose dicts (side view, facing +x; arm_* = (shoulder deg, elbow deg) from straight down,
+ forward; foot_* = (ankle x, lift, pitch)); props are rig hooks drawn into the cell's G-buffer with their own
materials, so they are outlined and shaded like the clothes:
  shovel_cycle()   8 frames: dig, push in, lift, lift, throw (coal leaves the blade), follow, return, down --
                   CONTACT_FRAME is the frame the blade bites (the sound tool syncs the bites to it)
  rest_on_shovel() idle 4 frames: leaning on the shovel's D-handle, breathing
  push_tub()       a loaded tipper tub pushed along the narrow-gauge track (4 frames)
  toolbox_walk()   8 frames: the in-game walk with the near arm carrying a fitter's toolbox (Alexei, p2)
  tarp_pull()      a worker hauling a tarpaulin rope / holding a pole up (3 frames)
  band(kind)       a works band musician: trumpet, cornet, trombone (slide), tenor horn, helicon, bass drum,
                   snare (4 frames each, playing)
  match_light()    the press minder brings a match to his cigarette (6 frames incl. the flare)
  carbons()        Lev buttons the carbon copies back into his coat (6 frames)
  canister_up()    (unused by the wide shots; the window is a close shot)
Every builder returns (spec, poses, hooks, width) for kit.rig_frames().  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_kit as K

CONTACT_FRAME = 1           # shovel_cycle(): the blade bites into the coal on this frame
THROW_FRAME = 4             # shovel_cycle(): the coal leaves the blade on this frame

WOOD = ['#1a1009', '#2e1d10', '#4a2f19', '#6a4424', '#8c5c32', '#ae7a48']
STEEL = ['#0c0e10', '#1c2024', '#323840', '#4e5660', '#76808a', '#a8b2ba']
COAL = ['#050506', '#0b0b0d', '#141418', '#1e1e24', '#2c2c34', '#4a4a56']
BRASS = ['#24180a', '#4a3212', '#7a5a1e', '#ae8a34', '#d8b85a', '#f6e4a0']
TOOLB = ['#0e1410', '#18261c', '#26382a', '#38503c', '#4e6a52', '#6c8a6e']
PAPER = ['#2e2c28', '#5c5a52', '#8e8a7e', '#bab4a4', '#dcd6c4', '#f2eedc']
SKIN_W = ['#2a1612', '#4e2a1e', '#7a4632', '#a2664a', '#c48a68', '#e2b08c']
FLAME = ['#4a1a04', '#8a3a08', '#d07018', '#f4a838', '#ffd878', '#fff6d0']
DRUMH = ['#3a342a', '#6a6250', '#9a907a', '#c4baa2', '#e2d8c0', '#f6f0de']
RED = ['#1e0606', '#3e0c0a', '#621410', '#8a1e16', '#b02a1e', '#d0442e']


def _mats(spec, **extra):
    base = dict(c4p2_wood=WOOD, c4p2_steel=STEEL, c4p2_coal=COAL, c4p2_brass=BRASS, c4p2_paper=PAPER,
                c4p2_flame=FLAME, c4p2_box=TOOLB, c4p2_drum=DRUMH, c4p2_red=RED)
    base.update(extra)
    for n, r in base.items():
        K.add_mat(spec, n, r, glossy=n in ('c4p2_brass', 'c4p2_steel'), max_tone=5 if n == 'c4p2_flame' else 4)
    return spec


def _line(fr, spec, a, b, r, mat, tone=None, name='prop'):
    CH, CB, A, CC = K.rig()
    m, x0, y0, n = CC.capsule(a, b, r)
    return fr.put(m, x0, y0, spec.names[mat], n, tone=tone, cast=False, name=name)


def _px(fr, spec, x, y, mat, tone):
    fr.px(x, y, spec.names[mat], tone, fixed=True)


def _head(J, P):
    if 'head_at' in J:
        return J['head_at']
    hx, hy = J['neck']
    hd = P.get('head', (0, 0))
    return (hx + hd[0], hy + hd[1])


def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    L = math.hypot(*d) + 1e-6
    return (d[0] / L, d[1] / L)


# ============================================================================================ shovel
SHOVEL_KEYS = [
    # lean, stoop, arm_n (front hand), arm_f (rear hand), foot_n, foot_f, bob, coal on blade, coal flying
    # 0 the blade goes in low in front of the feet, 1 the bite (front knee bent, the blade in the coal), 2 the
    # load comes up, 3 the turn, 4 the throw (the coal leaves), 5 the follow-through, 6 back, 7 reaching down
    (32.0, 17.0, (24.0, 6.0), (8.0, 44.0), (7.0, 0.0, 8), (-6.0, 0.0, -4), 1, 0, 0),
    (40.0, 23.0, (16.0, 2.0), (14.0, 34.0), (7.5, 0.0, 10), (-6.0, 0.0, -6), 2, 1, 0),
    (22.0, 11.0, (40.0, 24.0), (2.0, 58.0), (6.5, 0.0, 6), (-6.0, 0.0, -4), 1, 1, 0),
    (11.0, 5.0, (56.0, 40.0), (12.0, 74.0), (5.5, 0.0, 2), (-5.5, 0.0, -2), 0, 1, 0),
    (3.0, 0.0, (92.0, 30.0), (54.0, 56.0), (5.0, 0.0, 0), (-5.0, 0.6, -10), 0, 0, 1),
    (5.0, 1.0, (100.0, 16.0), (62.0, 38.0), (5.0, 0.0, 0), (-5.0, 0.4, -8), 0, 0, 2),
    (15.0, 6.0, (62.0, 10.0), (30.0, 40.0), (5.5, 0.0, 2), (-5.5, 0.0, -2), 0, 0, 0),
    (28.0, 14.0, (32.0, 6.0), (12.0, 44.0), (6.5, 0.0, 6), (-6.0, 0.0, -4), 1, 0, 0),
]


# round 11c (art director, Depot p1: "arms out like zombies"): the turn, throw, follow-through and return with
# the rear hand low by the hip and the shaft on a diagonal -- the front arm never level with the shoulder
SHOVEL_LOW_THROW = {3: ((46.0, 48.0), (8.0, 70.0)), 4: ((68.0, 26.0), (16.0, 66.0)), 5: ((78.0, 14.0), (26.0, 52.0)),
                    6: ((56.0, 16.0), (20.0, 46.0))}


def shovel_poses(phase_lean=0.0, reach=0.0, low_throw=False):
    """low_throw: the round-11c throw (SHOVEL_LOW_THROW) and the long-shafted coal shovel with its broad blade."""
    out = []
    for i, (le, st, an, af, fn, ff, bob, onb, fly) in enumerate(SHOVEL_KEYS):
        if low_throw and i in SHOVEL_LOW_THROW:
            an, af = SHOVEL_LOW_THROW[i]
        an = (an[0] + reach * (1.0 if an[0] < 60 else 0.0), an[1])
        out.append(dict(bob=bob, lean=le + phase_lean, stoop=st, foot_n=fn, foot_f=ff, arm_n=an, arm_f=af,
                        face='base', phase=i, dx=-2.0, lag=0.0, bounce=0, hand_n='fist', hand_f='fist',
                        c4p2_shovel=True, c4p2_onblade=onb, c4p2_fly=fly, c4p2_big=low_throw))
    return out


def shovel_hook_back(fr, J, P, spec):
    """Shaft and blade (drawn behind the near arm, over the body): rear grip at the far wrist, through the near
    hand, blade at the end; coal on the blade / leaving it."""
    if not P.get('c4p2_shovel'):
        return
    a, b = J['wr_f'], J['wr_n']
    ux, uy = _unit(a, b)
    big = bool(P.get('c4p2_big'))
    s0 = (a[0] - ux * 2.5, a[1] - uy * 2.5)
    s1 = (b[0] + ux * (9.5 if big else 7.0), b[1] + uy * (9.5 if big else 7.0))
    _line(fr, spec, s0, s1, 0.55, 'c4p2_wood', name='shaft')
    _line(fr, spec, (s0[0] - uy * 1.2, s0[1] + ux * 1.2), (s0[0] + uy * 1.2, s0[1] - ux * 1.2), 0.5, 'c4p2_wood',
          name='dgrip')
    # the blade: a short scoop angled ~25 deg down from the shaft (big: the broad coal scoop, its raised side)
    ang = math.atan2(uy, ux) + math.radians(22)
    bx, by = math.cos(ang), math.sin(ang)
    bl = 7.5 if big else 5.5
    e = (s1[0] + bx * bl, s1[1] + by * bl)
    _line(fr, spec, s1, e, 1.35 if big else 1.1, 'c4p2_steel', name='blade')
    if big:
        _line(fr, spec, (s1[0] + bx * 1.0 + by * 1.2, s1[1] + by * 1.0 - bx * 1.2),
              (e[0] - bx * 0.6 + by * 1.2, e[1] - by * 0.6 - bx * 1.2), 0.45, 'c4p2_steel', tone=4, name='blade_lip')
    if P.get('c4p2_onblade'):
        for k, (dx, dy) in enumerate(((1.5, -1.6), (3.0, -1.8), (4.2, -1.2), (2.3, -2.6))):
            _px(fr, spec, s1[0] + bx * dx - by * 0.2, s1[1] + by * dx + dy, 'c4p2_coal', 2 + (k % 2))
    if P.get('c4p2_fly'):
        n = P['c4p2_fly']
        for k in range(5):
            d = 3.0 + k * 2.2 + n * 3.0
            _px(fr, spec, e[0] + d * 0.9, e[1] - 2.5 - k * 0.8 + n * 1.5 + (k % 2), 'c4p2_coal', 2 + (k % 3))


def shovel_setup(spec):
    _mats(spec)
    return [('back1', shovel_hook_back)]


def rest_poses():
    out = []
    for i, br in enumerate((0, 0, 1, 1)):
        out.append(dict(bob=0, lean=8.0, stoop=4.0, foot_n=(3.0, 0.0, 0), foot_f=(-3.0, 0.0, 0),
                        arm_n=(42.0, 58.0 + br * 2), arm_f=(38.0, 62.0 + br), breath=br, face='base', phase=i,
                        dx=-1.0, lag=0.0, bounce=0, hand_n='fist', hand_f='fist', c4p2_rest=True))
    return out


def rest_hook(fr, J, P, spec):
    """The shovel planted upright in front, both hands on the D-handle."""
    if not P.get('c4p2_rest'):
        return
    hx, hy = J['wr_n']
    top = (hx + 0.5, hy - 1.0)
    bot = (hx + 3.5, 54.0)
    _line(fr, spec, top, bot, 0.55, 'c4p2_wood', name='shaft')
    _line(fr, spec, (bot[0] - 0.5, bot[1] - 5.0), (bot[0] + 0.8, bot[1]), 1.2, 'c4p2_steel', name='blade')
    _line(fr, spec, (top[0] - 1.3, top[1]), (top[0] + 1.3, top[1]), 0.5, 'c4p2_wood', name='dgrip')


def rest_setup(spec):
    _mats(spec)
    return [('back1', rest_hook)]


# ============================================================================================ toolbox walk
def toolbox_poses(style):
    CH, CB, A, CC = K.rig()
    s = dict(style or {})
    s['hold_n'] = (-3.0, 6.0)
    frames = A.walk_side(s)
    for P in frames:
        P['c4p2_toolbox'] = True
        P['hand_n'] = 'fist'
    return frames


def toolbox_hook(fr, J, P, spec):
    """A fitter's steel toolbox (dented green paint, a brass catch) hanging from the near fist; it swings a
    little behind the steps (P['lag'])."""
    if not P.get('c4p2_toolbox'):
        return
    x, y = J['wr_n']
    sw = P.get('lag', 0.0) * 0.6
    x0, y0 = int(round(x - 6 + sw)), int(round(y + 2))
    CH, CB, A, CC = K.rig()
    box = np.zeros((7, 13), bool)
    box[1:, :] = True
    box[0, 1:-1] = True
    tone = np.full(box.shape, np.nan, np.float32)
    tone[1, :] = 3.0
    tone[-1, :] = 1.0
    tone[3, 2:11] = 1.6
    nrm_ = np.zeros(box.shape + (3,), np.float32)
    nrm_[..., 2] = 1
    nrm_[0:2, :, 1] = 0.7
    fr.put(box, x0, y0, spec.names['c4p2_box'], nrm_, tone=tone, cast=True, name='toolbox')
    _px(fr, spec, x0 + 6, y0 + 2, 'c4p2_brass', 3)
    _line(fr, spec, (x - 3 + sw, y + 1.5), (x + 3 + sw, y + 1.5), 0.45, 'c4p2_steel', name='handle')


def toolbox_setup(spec):
    _mats(spec)
    return [('front', toolbox_hook)]


# ============================================================================================ tarpaulin
def tarp_poses():
    out = []
    keys = [((158.0, 6.0), (150.0, 10.0), 2.0), ((150.0, 14.0), (140.0, 18.0), 0.0), ((164.0, 2.0), (156.0, 6.0), 3.0)]
    for i, (an, af, le) in enumerate(keys):
        out.append(dict(bob=0, lean=-le, stoop=0.0, foot_n=(4.0, 0.0, 0), foot_f=(-4.5, 0.0, 0), arm_n=an, arm_f=af,
                        face='base', phase=i, dx=0.0, lag=0.0, bounce=0, hand_n='fist', hand_f='fist',
                        c4p2_pole=True))
    return out


def tarp_hook(fr, J, P, spec):
    if not P.get('c4p2_pole'):
        return
    x, y = J['wr_n']
    _line(fr, spec, (x + 0.5, 2.0), (x + 0.5, 54.0), 0.6, 'c4p2_wood', name='pole')


def tarp_setup(spec):
    _mats(spec)
    return [('back1', tarp_hook)]


# ============================================================================================ band
BAND_ARMS = {
    # instrument: list of 4 (arm_n, arm_f, head, extra) -- arm angles put the hands at the mouthpiece / drum
    'trumpet': [((70.0, 88.0), (64.0, 92.0), (0, 0), 0), ((71.0, 88.0), (64.0, 92.0), (0, 0), 1),
                ((70.0, 86.0), (63.0, 92.0), (0, 0), 0), ((72.0, 88.0), (65.0, 90.0), (0, 0), 1)],
    'trombone': [((60.0, 98.0), (78.0, 40.0), (0, 0), 0), ((60.0, 98.0), (86.0, 22.0), (0, 0), 1),
                 ((60.0, 98.0), (92.0, 10.0), (0, 0), 2), ((60.0, 98.0), (84.0, 26.0), (0, 0), 1)],
    'horn': [((40.0, 100.0), (30.0, 100.0), (0, 0), 0), ((40.0, 102.0), (30.0, 100.0), (0, 0), 1),
             ((40.0, 100.0), (30.0, 100.0), (0, 0), 0), ((40.0, 102.0), (30.0, 100.0), (0, 0), 1)],
    'helicon': [((30.0, 96.0), (20.0, 100.0), (0, 0), 0), ((30.0, 98.0), (20.0, 100.0), (0, 0), 1),
                ((30.0, 96.0), (20.0, 100.0), (0, 0), 0), ((30.0, 98.0), (20.0, 100.0), (0, 0), 1)],
    'bassdrum': [((40.0, 60.0), (20.0, 70.0), (0, 0), 0), ((70.0, 70.0), (20.0, 70.0), (0, 0), 1),
                 ((30.0, 40.0), (20.0, 70.0), (0, 0), 2), ((40.0, 60.0), (20.0, 70.0), (0, 0), 0)],
    'snare': [((40.0, 70.0), (36.0, 64.0), (0, 1), 0), ((46.0, 84.0), (34.0, 60.0), (0, 1), 1),
              ((40.0, 70.0), (40.0, 76.0), (0, 1), 2), ((38.0, 64.0), (34.0, 60.0), (0, 1), 0)],
}


def band_poses(kind):
    out = []
    for i, (an, af, hd, ex) in enumerate(BAND_ARMS[kind]):
        out.append(dict(bob=0, lean=-2.0 if kind in ('helicon', 'bassdrum') else 0.0, stoop=0.0,
                        foot_n=(3.0, 0.0, 0), foot_f=(-3.0, 0.0, 0), arm_n=an, arm_f=af, head=hd, face='base',
                        phase=i, dx=0.0, lag=0.0, bounce=0, hand_n='fist', hand_f='fist', breath=ex % 2,
                        c4p2_band=kind, c4p2_ex=ex))
    return out


def band_hook_back(fr, J, P, spec):
    kind = P.get('c4p2_band')
    if not kind:
        return
    hx, hy = _head(J, P)
    if kind == 'helicon':
        cx, cy = J['body'](0.0, 9.0)
        # the big brass loop round the body and the bell over the near shoulder, facing forward
        for k in range(28):
            a = 2 * math.pi * k / 28
            x = cx + 6.0 * math.cos(a)
            y = cy + 3.0 * math.sin(a) - 1.0
            _px(fr, spec, x, y, 'c4p2_brass', 2 + (1 if math.cos(a) > 0.3 else 0))
        bx, by = hx - 1.0, hy - 9.0
        _line(fr, spec, (cx + 3.0, cy - 3.0), (bx, by + 4.0), 1.0, 'c4p2_brass', name='bellneck')
        bell = np.zeros((7, 9), bool)
        for yy in range(7):
            for xx in range(9):
                bell[yy, xx] = ((xx - 4.0) / 4.5) ** 2 + ((yy - 3.0) / 3.6) ** 2 <= 1.0
        tone = np.full(bell.shape, np.nan, np.float32)
        tone[:, 6:] = 4.0
        tone[:, :2] = 1.5
        fr.put(bell, int(bx) - 3, int(by) - 3, spec.names['c4p2_brass'], None, tone=tone, cast=False, name='bell')
    if kind == 'bassdrum':
        cx, cy = J['body'](4.5, 4.0)
        drum = np.zeros((14, 6), bool)
        for yy in range(14):
            for xx in range(6):
                drum[yy, xx] = ((xx - 2.5) / 3.0) ** 2 + ((yy - 6.5) / 7.0) ** 2 <= 1.0
        tone = np.full(drum.shape, np.nan, np.float32)
        tone[:, 0] = 1.0
        tone[:, -1] = 4.0
        fr.put(drum, int(cx) - 1, int(cy) - 7, spec.names['c4p2_drum'], None, tone=tone, cast=False, name='drum')
        _line(fr, spec, (cx - 1, cy - 6.5), (cx - 1, cy + 6.5), 0.5, 'c4p2_red', name='hoop')
        _line(fr, spec, (cx + 4, cy - 6.5), (cx + 4, cy + 6.5), 0.5, 'c4p2_red', name='hoop2')
    if kind == 'snare':
        cx, cy = J['body'](4.0, -3.0)
        _line(fr, spec, (cx - 3, cy), (cx + 4, cy), 1.6, 'c4p2_drum', name='snare')
        _line(fr, spec, (cx - 3, cy - 1.6), (cx + 4, cy - 1.6), 0.4, 'c4p2_brass', name='rim')


def band_hook_front(fr, J, P, spec):
    kind = P.get('c4p2_band')
    if not kind:
        return
    hx, hy = _head(J, P)
    mx, my = hx + 4.0, hy + 4.0                     # mouth
    ex = P.get('c4p2_ex', 0)
    if kind == 'trumpet':
        _line(fr, spec, (mx, my), (mx + 9.0, my - 0.5), 0.6, 'c4p2_brass', name='leadpipe')
        _line(fr, spec, (mx + 2.0, my + 1.4), (mx + 7.0, my + 1.4), 0.6, 'c4p2_brass', name='valves')
        _line(fr, spec, (mx + 9.0, my - 2.0), (mx + 9.6, my + 1.5), 1.1, 'c4p2_brass', name='bell')
        _px(fr, spec, mx + 10.0, my - 1.0 - ex * 0.5, 'c4p2_brass', 5)
    elif kind == 'trombone':
        slide = 6.0 + ex * 3.5
        _line(fr, spec, (mx, my), (mx + 8.0, my - 1.0), 0.55, 'c4p2_brass', name='tube')
        _line(fr, spec, (mx + 2.0, my + 1.5), (mx + 2.0 + slide, my + 1.0), 0.5, 'c4p2_brass', name='slide')
        _line(fr, spec, (mx + 2.0 + slide, my - 0.2), (mx + 2.0 + slide, my + 1.6), 0.5, 'c4p2_brass', name='bow')
        _line(fr, spec, (mx - 3.0, my - 3.0), (mx - 2.0, my + 2.0), 1.2, 'c4p2_brass', name='bell')
    elif kind == 'horn':
        cx, cy = mx + 2.0, my + 4.0
        for k in range(16):
            a = 2 * math.pi * k / 16
            _px(fr, spec, cx + 2.6 * math.cos(a), cy + 2.6 * math.sin(a), 'c4p2_brass', 3)
        _line(fr, spec, (cx + 2.0, cy - 2.0), (cx + 3.0, cy - 6.0), 1.2, 'c4p2_brass', name='bell')
        _line(fr, spec, (mx, my), (cx - 1.0, cy - 1.0), 0.5, 'c4p2_brass', name='pipe')
    elif kind == 'snare':
        for side, a in ((0, P['arm_n']), (1, P['arm_f'])):
            wx, wy = J['wr_n'] if side == 0 else J['wr_f']
            _line(fr, spec, (wx, wy), (wx + 4.0, wy + 2.5 - ex), 0.4, 'c4p2_wood', name='stick')
    elif kind == 'bassdrum':
        wx, wy = J['wr_n']
        _line(fr, spec, (wx, wy), (wx + 3.0, wy - 2.0), 0.5, 'c4p2_wood', name='beater')
        _line(fr, spec, (wx + 3.0, wy - 2.0), (wx + 3.6, wy - 2.6), 1.0, 'c4p2_drum', name='head')


def band_setup(spec):
    _mats(spec)
    return [('back1', band_hook_back), ('front', band_hook_front)]


# ============================================================================================ the match
def match_poses():
    keys = [((10.0, 30.0), (18.0, 70.0), 0), ((20.0, 80.0), (24.0, 96.0), 0), ((14.0, 116.0), (20.0, 112.0), 1),
            ((14.0, 118.0), (20.0, 114.0), 2), ((14.0, 118.0), (22.0, 112.0), 3), ((16.0, 100.0), (20.0, 80.0), 4)]
    out = []
    for i, (an, af, fl) in enumerate(keys):
        out.append(dict(bob=0, lean=2.0, stoop=1.0 if fl else 0.0, foot_n=(3.0, 0.0, 0), foot_f=(-3.0, 0.0, 0),
                        arm_n=an, arm_f=af, head=(0, 1) if fl in (1, 2, 3) else (0, 0), face='base', phase=i, dx=0.0,
                        lag=0.0, bounce=0, hand_n='fist', hand_f='fist', c4p2_match=fl))
    return out


def match_hook(fr, J, P, spec):
    fl = P.get('c4p2_match', 0)
    hx, hy = _head(J, P)
    mx, my = hx + 4.5, hy + 4.5
    _px(fr, spec, mx, my, 'c4p2_paper', 4)
    _px(fr, spec, mx + 1, my, 'c4p2_paper', 5)
    if fl in (1, 2, 3):
        wx, wy = J['wr_n']
        big = fl == 1
        _px(fr, spec, mx + 2, my - (1 if big else 0), 'c4p2_flame', 5)
        _px(fr, spec, mx + 2, my - 1 - (1 if big else 0), 'c4p2_flame', 4)
        if big:
            _px(fr, spec, mx + 3, my - 1, 'c4p2_flame', 3)
            _px(fr, spec, mx + 2, my - 3, 'c4p2_flame', 3)
    if fl >= 3:
        _px(fr, spec, mx + 2, my, 'c4p2_flame', 4)


def match_setup(spec):
    _mats(spec)
    return [('front', match_hook)]


# ============================================================================================ Lev's carbons
def carbons_poses():
    keys = [((14.0, 40.0), (10.0, 30.0), 1), ((24.0, 96.0), (26.0, 90.0), 1), ((22.0, 116.0), (28.0, 110.0), 2),
            ((18.0, 124.0), (26.0, 116.0), 3), ((16.0, 110.0), (24.0, 104.0), 0), ((12.0, 40.0), (10.0, 30.0), 0)]
    out = []
    for i, (an, af, ph) in enumerate(keys):
        out.append(dict(bob=0, lean=4.0 if ph else 2.0, stoop=3.0 if ph in (2, 3) else 0.0, foot_n=(3.0, 0.0, 0),
                        foot_f=(-3.0, 0.0, 0), arm_n=an, arm_f=af, head=(0, 1) if ph in (2, 3) else (0, 0),
                        face='base', phase=i, dx=0.0, lag=0.0, bounce=0, hand_n='open' if ph == 1 else 'fist',
                        hand_f='fist', c4p2_carbons=ph))
    return out


def carbons_hook(fr, J, P, spec):
    ph = P.get('c4p2_carbons', 0)
    if not ph:
        return
    x, y = J['wr_n']
    if ph == 1:          # the folded carbons in the near hand
        _line(fr, spec, (x + 0.5, y - 3.0), (x + 1.5, y + 2.0), 1.0, 'c4p2_paper', name='carbons')
    elif ph == 2:        # pushed into the coat front at the chest
        cx, cy = J['body'](2.5, 12.0)
        _line(fr, spec, (cx, cy - 2.5), (cx + 0.5, cy + 1.5), 0.9, 'c4p2_paper', name='carbons')
    elif ph == 3:        # only the top edge still shows above the button
        cx, cy = J['body'](2.5, 13.0)
        _px(fr, spec, cx, cy, 'c4p2_paper', 4)


def carbons_setup(spec):
    _mats(spec)
    return [('front', carbons_hook)]


# ============================================================================================ helpers
def render_set(spec, poses, hooks, width=48):
    """[(rgba, nm, J)] of the poses with the hooks."""
    return K.rig_frames(spec, poses, 'side', width, hooks)


def sheet_of(frames):
    """Horizontal sheets (rgba, nm) of rendered frames."""
    rg = np.concatenate([f[0] for f in frames], axis=1)
    nm = np.concatenate([f[1] for f in frames], axis=1)
    return rg, nm


def flip_frames(frames):
    out = []
    for rg, nm, J in frames:
        n2 = nm[:, ::-1].copy()
        n2[..., 0] = 255 - n2[..., 0]
        n2[..., 3] = nm[:, ::-1, 3]
        out.append((rg[:, ::-1].copy(), n2, J))
    return out


def tint_frames(frames, lights, x0, y0, z, pal, flip=False, **kw):
    """Each frame tinted by the shot's lights as if its cell's top-left stood at (x0, y0)."""
    return [K.fig_tint(rg, nm, lights, x0, y0, z, pal, flip=False, **kw) for rg, nm, J in frames]


# ============================================================================================ props of the base specs
PROP_WORDS = ('shovel', 'satchel', 'bundle', 'crate', 'suitcase', 'toy', 'file_side', 'notebook', 'camera', '_case',
              'punch', 'stamp', 'clipboard', 'tea', 'book', 'kettle', 'folder', 'tube', 'cards', '_box', 'keys',
              'paper', 'note', '_pad', 'cigarette', 'smoke', 'watch', 'rifle', 'akte')


def strip_props(spec, keep=()):
    """Remove the hand props of a base spec (its parcel, file, kettle ...) so the film's own prop is the only one;
    clothing hooks (coats, collars, scarves, flaps, breath) stay."""
    for view in list(spec.hooks):
        spec.hooks[view] = [(l, f) for (l, f) in spec.hooks[view]
                            if f.__name__ in keep or not any(wd in f.__name__ for wd in PROP_WORDS)]
    return spec
