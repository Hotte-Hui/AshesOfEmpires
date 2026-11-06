"""env_c3p2_cine_body -- one anatomical full-body rig for every person in the Chapter-3 part-2 cinematics
(LS_C3_Radio, LS_C3_Fire, LS_C3_Escape, LS_C3_Halves; owner: figures stream, round 10).

Why: the round-8/9 figures were busts with arms fused into the torso, round-cone "sleeves" without hands, painted
paper-doll silhouettes and stick walkers.  This module sculpts whole people with the signed-distance pipeline of
the dialogue portraits (chargen_portrait2_*: heads, hats, hair, materials, sphere tracer, painter -- imported
read-only) on a real skeleton:

  pelvis frame -> lumbar pivot -> chest frame (neck base) -> atlas pivot -> head (portrait head, own neck)
  shoulder -> elbow -> wrist -> hand (palm, four two-joint fingers, thumb; env_c3p2_cine_hands.hand)
  hip -> knee -> ankle -> foot (boot / shoe with a flat sole)
Arms and legs are posed by forward kinematics (joint angles) or by two-bone IK (wrist / ankle targets with a pole
for the elbow / knee); garments follow the bones: sleeves with cuffs, a long overcoat whose skirt panels follow the
thighs and fall from the knees, a quilted jacket, collars, scarves, satchel straps, trousers, boots.

Units: portrait head units (a head is 52 u from chin to crown); a man is ~7.6 heads (395 u) tall.
Scene frame: x = the figure's left when it faces +z, y DOWN, z forward; the ground is y = 0.
render() places a posed figure in a sprite through an orthographic camera (yaw about the vertical, elevation,
scale px per unit) and paints it with the portrait painter (material ramps generated for the shot's light).
Everything is deterministic numpy (no image inputs, no randomness); renders are memoised on disk like the other
cinematic figures (key = pipeline sources + this file + the call), ASHES_NO_CACHE=1 disables the cache.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_anat as A   # noqa: E402
import chargen_portrait2_cast as CC  # noqa: E402
import chargen_portrait2_paint as P  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402
from chargen_portrait2_paint import MatStyle  # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
F32 = np.float32
_memo: dict = {}

# ------------------------------------------------------------------------------------------------ proportions
PROP = dict(
    hip=16.0, thigh=90.0, shin=86.0, foot=48.0, heel=9.0, ankle_h=9.0,
    lumbar_p=(0.0, -42.0, -5.0),          # lumbar pivot in the pelvis frame
    lumbar_c=(0.0, 97.0, -5.0),           # ... and in the chest frame (origin = centre of the neck base)
    atlas=(0.0, -34.0, -6.0),             # head pivot in the chest frame (round 11: a short, strong neck)
    head_from_atlas=(0.0, -6.0, 4.0),     # head-local origin (eye line) relative to the pivot (head-local axes)
    shoulder=(38.5, 23.0, -3.0), upper=74.0, fore=62.0, palm=22.0,
)


HEAD_SCALE = 1.10          # the portrait head a little larger on the body (7.2 heads tall) -- reads at small sizes


def _n(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    return S.rot(yaw, pitch, roll)


def _rx(a):
    a = math.radians(a)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def ik2(a, t, l1, l2, pole):
    """Two-bone IK: root a, target t, bone lengths, pole direction (where the middle joint bends to)."""
    a, t = np.asarray(a, float), np.asarray(t, float)
    d = t - a
    L = float(np.linalg.norm(d))
    L = min(max(L, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    u = _n(d)
    t = a + u * L
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    p = np.asarray(pole, float)
    v = p - u * float(np.dot(p, u))
    if np.linalg.norm(v) < 1e-6:
        v = np.cross(u, (1.0, 0.0, 0.0))
    v = _n(v)
    return a + u * x + v * h, t


def fk_dir(flex, abd, side):
    """Limb direction from 'hanging straight down' (+y): abduction (outward, degrees) then flexion (forward)."""
    a = math.radians(abd)
    d = np.array([side * math.sin(a), math.cos(a), 0.0])
    return _rx(flex) @ d


# ------------------------------------------------------------------------------------------------ rig
class Rig:
    """Joint positions (scene units) of one posed figure.

    pose keys (all optional):
      root      (x, y, z) hip-joint centre in the scene (default standing on the ground, see ground())
      pelvis    (yaw, pitch, roll) of the pelvis (pitch > 0 tips the pelvis forward)
      spine     (yaw, pitch, roll) of the chest relative to the pelvis (pitch > 0 bends forward)
      head      (yaw, pitch, roll) of the head relative to the chest
      arm_l/r   dict(wrist=(x,y,z) scene target, pole=dir) | dict(fk=(flex, abd, elbow[, twist]))
                + hand=dict(dir=, up=, curl=, spread=, grip=) (directions in the scene)
      leg_l/r   dict(fk=(flex, abd, knee[, ankle])) | dict(ankle=(x,y,z), pole=dir[, foot=dir])
    """

    def __init__(self, pose: dict, prop=PROP):
        self.pose = pose
        pr = prop
        self.R_pel = rot(*pose.get('pelvis', (0, 0, 0)))
        if 'pelvis_R' in pose:
            self.R_pel = np.asarray(pose['pelvis_R'], float) @ self.R_pel
        self.o_pel = np.asarray(pose.get('root', (0.0, -(pr['thigh'] + pr['shin'] + pr['ankle_h'] + 1.0), 0.0)), float)
        lum = self.o_pel + self.R_pel @ np.asarray(pr['lumbar_p'])
        self.R_ch = self.R_pel @ rot(*pose.get('spine', (0, 0, 0)))
        self.o_ch = lum - self.R_ch @ np.asarray(pr['lumbar_c'])
        piv = self.o_ch + self.R_ch @ np.asarray(pr['atlas'])
        self.R_head = self.R_ch @ rot(*pose.get('head', (0, 0, 0)))
        self.o_head = piv + self.R_head @ np.asarray(pr['head_from_atlas'])
        self.atlas = piv
        self.arm = {}
        for side, key in ((1.0, 'arm_l'), (-1.0, 'arm_r')):
            spec = pose.get(key, {})
            sh = self.o_ch + self.R_ch @ (np.asarray(pr['shoulder']) * np.array([side, 1, 1]))
            if 'sh_off' in spec:
                sh = sh + np.asarray(spec['sh_off'], float)
            if 'wrist' in spec:
                pole = spec.get('pole', self.R_ch @ np.array([side * 0.5, 0.2, -1.0]))
                el, wr = ik2(sh, spec['wrist'], pr['upper'], pr['fore'], pole)
            else:
                flex, abd, elb = spec.get('fk', (6.0, 6.0, 14.0))[:3]
                twist = spec.get('fk', (0, 0, 0, 0))[3] if len(spec.get('fk', ())) > 3 else 0.0
                du = self.R_ch @ fk_dir(flex, abd, side)
                el = sh + du * pr['upper']
                # the forearm bends toward the arm's front (+z of the chest frame rotated with the arm), twisted
                front = self.R_ch @ (_rx(flex) @ np.array([0.0, 0.0, 1.0]))
                front = _n(front - du * float(np.dot(front, du)))
                lat = _n(np.cross(du, front)) * side
                tw = math.radians(twist)
                bend_dir = _n(front * math.cos(tw) - lat * math.sin(tw))
                e = math.radians(elb)
                df = _n(du * math.cos(e) + bend_dir * math.sin(e))
                wr = el + df * pr['fore']
            hs = dict(spec.get('hand', {}))
            fdir = _n(wr - el)
            hdir = _n(hs.get('dir', fdir))
            up = hs.get('up', None)
            if up is None:
                # back of the hand: outward / backward for a hanging arm (thumb forward)
                up = self.R_ch @ np.array([side * 1.0, 0.0, -0.35])
            up = np.asarray(up, float)
            up = _n(up - hdir * float(np.dot(up, hdir)))
            self.arm[key] = dict(sh=sh, el=el, wr=wr, side=side, hdir=hdir, hup=up,
                                 curl=hs.get('curl', 0.35), spread=hs.get('spread', 0.1),
                                 grip=hs.get('grip', 0.15), thumb=hs.get('thumb', -side))
        self.leg = {}
        for side, key in ((1.0, 'leg_l'), (-1.0, 'leg_r')):
            spec = pose.get(key, {})
            hip = self.o_pel + self.R_pel @ np.array([side * pr['hip'], 0.0, 0.0])
            if 'ankle' in spec:
                pole = spec.get('pole', self.R_pel @ np.array([0.0, 0.0, 1.0]))
                kn, an = ik2(hip, spec['ankle'], pr['thigh'], pr['shin'], pole)
                foot = _n(spec.get('foot', self.R_pel @ np.array([0.0, 0.0, 1.0])))
            else:
                fk = spec.get('fk', (0.0, 3.0, 4.0, 0.0))
                flex, abd, knee = fk[:3]
                ank = fk[3] if len(fk) > 3 else 0.0
                dt = self.R_pel @ fk_dir(flex, abd, side)
                kn = hip + dt * pr['thigh']
                ds = self.R_pel @ fk_dir(flex - knee, abd * 0.6, side)
                an = kn + ds * pr['shin']
                foot = self.R_pel @ fk_dir(flex - knee + 90.0 - ank, abd * 0.4, side)
            self.leg[key] = dict(hip=hip, kn=kn, an=an, foot=_n(foot), side=side)

    def chest(self, p):
        return self.o_ch + self.R_ch @ np.asarray(p, float)

    def pelvis(self, p):
        return self.o_pel + self.R_pel @ np.asarray(p, float)

    def head(self, p):
        return self.o_head + self.R_head @ np.asarray(p, float)

    def soles(self):
        """Lowest points (max y) of both feet."""
        out = []
        for lg in self.leg.values():
            heel = lg['an'] + np.array([0.0, PROP['ankle_h'], 0.0]) - lg['foot'] * PROP['heel']
            toe = lg['an'] + np.array([0.0, PROP['ankle_h'], 0.0]) + lg['foot'] * (PROP['foot'] - PROP['heel'])
            out.append(max(heel[1], toe[1]))
        return out


def ground(pose, y=0.0, which=None):
    """Return the pose moved vertically so that its lowest sole (or the given leg's) stands on y."""
    r = Rig(pose)
    soles = r.soles()
    low = max(soles) if which is None else soles[0 if which == 'l' else 1]
    p = dict(pose)
    root = np.asarray(p.get('root', r.o_pel), float).copy()
    root[1] += y - low
    p['root'] = tuple(root)
    return p


# ------------------------------------------------------------------------------------------------ poses
def stand(**kw):
    p = dict(pelvis=(0, 0, 0), spine=(0, 2, 0), head=(0, 0, 0),
             arm_l=dict(fk=(4.0, 7.0, 12.0)), arm_r=dict(fk=(4.0, 7.0, 12.0)),
             leg_l=dict(fk=(1.0, 3.0, 2.0)), leg_r=dict(fk=(-1.0, 3.0, 2.0)))
    p.update(kw)
    return ground(p)


def walk(phase, stride=1.0, arm_swing=1.0, lean=4.0, hands=None, **kw):
    """Walk cycle in the figure's +z direction.  phase 0 = left heel strike (left leg forward)."""
    def leg(ph):
        ph = ph % 1.0
        hip = 3.0 + 21.0 * stride * math.cos(2 * math.pi * ph)
        if ph < 0.6:
            knee = 4.0 + 12.0 * math.sin(math.pi * ph / 0.6) ** 2
            ank = -6.0 * math.sin(math.pi * min(ph / 0.6, 1.0)) + (14.0 * max(0.0, (ph - 0.42) / 0.18) ** 2 if ph > 0.42 else 0.0)
        else:
            u = (ph - 0.6) / 0.4
            knee = 4.0 + 58.0 * stride * math.sin(math.pi * min(1.0, u ** 0.75))
            ank = 14.0 * (1.0 - u) - 6.0 * u
        return hip, knee, ank

    hl, kl, al = leg(phase)
    hr, kr, ar = leg(phase + 0.5)
    sw = 15.0 * arm_swing * math.cos(2 * math.pi * phase)
    bob = 2.6 * math.cos(4 * math.pi * phase)
    yaw = 4.0 * math.cos(2 * math.pi * phase)
    hands = hands or {}
    p = dict(pelvis=(yaw, 2.0, 0.0), spine=(-yaw * 1.6, lean, 0.0), head=(-yaw * 0.3, -lean * 0.6, 0.0),
             arm_l=dict(fk=(-sw, 8.0, 14.0 + max(0.0, -sw) * 0.8), hand=hands.get('l', dict(curl=0.45))),
             arm_r=dict(fk=(sw, 8.0, 14.0 + max(0.0, sw) * 0.8), hand=hands.get('r', dict(curl=0.45))),
             leg_l=dict(fk=(hl, 2.0, kl, al)), leg_r=dict(fk=(hr, 2.0, kr, ar)))
    p.update(kw)
    p = ground(p)
    root = np.asarray(p['root'], float)
    root[1] += bob * 0.0
    p['root'] = tuple(root)
    return p


# ------------------------------------------------------------------------------------------------ outfits
KONRAD = dict(
    id='konrad', head='konrad', hat='fedora', hair=dict(nape=13.5, back_z=-11.0, thick=1.2),
    coat='long', coat_mat='coat', hem=122.0, coat_bulk=5.0, sleeve=4.2, collar='turned', scarf=True,
    strap=('r', 'l'), bag='l', trouser='trouser', boot='shoe', skin='skin', cuff='shirt',
)
ALEXEI = dict(
    id='alexei', head='alexei', hat='ushanka', flaps='down',
    hair=dict(hairline=-13.0, front_z=9.0, burn_y=2.0, nape=13.0, back_z=-11.0, thick=1.2),
    coat='quilted', coat_mat='quilt', hem=58.0, coat_bulk=6.0, sleeve=5.0, collar='stand', rollneck=True,
    strap=('r', 'l'), bag='l', trouser='trouser', boot='kirza', skin='skin', cuff=None, quilt=14.0,
)


def townsperson(kind, variant=0):
    """Outfits of the extras (no faces close up): hotel guests, porters, firemen, onlookers, travellers."""
    v = variant
    heads = ('porter', 'vendor', 'worker_a', 'librarian', 'konrad', 'alexei')
    if kind == 'fireman':
        return dict(id='fireman', head=heads[v % 3], hat='helmet', hair=dict(), coat='fire', coat_mat='fjacket',
                    hem=40.0, coat_bulk=6.0, sleeve=5.0, collar='stand', belt=True, trouser='trouser',
                    boot='kirza', skin='skin', cuff=None)
    if kind == 'porter':
        return dict(id='porter', head='porter', hat='cap', hair=dict(hairline=-14.0, front_z=8.0, burn_y=3.0),
                    coat='long', coat_mat='coat', hem=60.0, coat_bulk=4.0, sleeve=3.8, collar='stand',
                    buttons=True, trouser='trouser', boot='shoe', skin='skin', cuff=None)
    if kind == 'woman':
        return dict(id='woman', head='irina' if v % 2 == 0 else 'babushka', female=True,
                    hat='scarf' if v % 2 else 'cloche', hair=dict(), coat='long', coat_mat='coat', hem=150.0,
                    coat_bulk=4.5, sleeve=4.0, collar='fur', trouser='stocking', boot='shoe', skin='skin',
                    cuff=None, flare=1.25)
    if kind == 'worker':
        return dict(id='worker', head=heads[(v + 2) % 3], hat='cap' if v % 2 else 'ushanka', flaps='up',
                    hair=dict(), coat='quilted', coat_mat='coat', hem=58.0, coat_bulk=6.0, sleeve=5.0,
                    collar='stand', trouser='trouser', boot='kirza', skin='skin', cuff=None, quilt=14.0)
    # 'guest' / 'man': a gentleman in an overcoat and a hat
    return dict(id='man', head=heads[v % 4], hat=('fedora', 'homburg', 'fedora', 'cap')[v % 4], hair=dict(),
                coat='long', coat_mat='coat', hem=118.0 + 6 * (v % 2), coat_bulk=4.8, sleeve=4.0,
                collar='turned', scarf=bool(v % 2), trouser='trouser', boot='shoe', skin='skin', cuff='shirt')


# ------------------------------------------------------------------------------------------------ head
def _cast_spec(name):
    fn = {'konrad': CC.konrad, 'alexei': CC.alexei}.get(name) or CC.CAST.get(name)
    if fn is None:
        import chargen_portrait2_cast as C2
        fn = getattr(C2, name, CC.konrad)
    return fn()


def _head_node(M, ch, jaw_open=0.0):
    """Portrait head (neck cut below the skull) + hair + hat, in head-local coordinates."""
    spec = _cast_spec(ch['head'])
    hp = A.head_params(**spec['head'])
    head, _lm = A.build_head(hp, M, jaw_open=jaw_open)
    # cut the portrait neck (it would swing with the head); our own neck joins the skull to the chest
    head = S.Inter(head, S.Fn(lambda Q: Q[:, 1] - (8.0 + (Q[:, 2] + 12.0) * 0.86), M('neck')))
    items, clips, solid = [], [], []
    hat = ch.get('hat')
    hk = ch.get('hair', {})
    fns = []
    if hat == 'fedora':
        fns.append(lambda: fedora_soft(M, hp, y0=-13.2))
    elif hat == 'homburg':
        fns.append(lambda: fedora_soft(M, hp, y0=-13.2, crown_h=15.5, brim_w=8.6, taper=0.08, snap=0.4))
    elif hat == 'ushanka':
        fns.append(lambda: CC.ushanka(M, hp, flaps=ch.get('flaps', 'down')))
    elif hat == 'cap':
        fns.append(lambda: CC.peaked_cap(M, hp))
    elif hat == 'helmet':
        fns.append(lambda: _helmet(M, hp))
    elif hat == 'scarf':
        fns.append(lambda: CC.headscarf(M, hp))
    elif hat == 'cloche':
        fns.append(lambda: _cloche(M, hp))
    if hat not in ('scarf',):
        kw = dict(nape=13.0, back_z=-11.0, thick=1.2)
        kw.update(hk)
        fns.append(lambda: CC.hair_short(M, hp, **kw))
    for f in fns:
        r = f()
        if isinstance(r, dict):
            solid.append(r['node'])
            if r.get('clip') is not None:
                clips.append(r['clip'])
            if r.get('soft') is not None:
                items.append(r['soft'])
        else:
            items.append(r)
    body = S.Union([head] + items)
    for c in clips:
        body = S.Inter(body, c)
    return S.Union([body] + solid), spec


def fedora_soft(M, hp, tilt=(5.0, -3.0), y0=-12.4, z0=-5.2, band_r=(17.4, 21.6), crown_h=17.5, brim_w=10.2,
                taper=0.17, snap=0.4):
    """chargen_portrait2_cast.fedora with a softer brim for the full figures: the front snapped down, the back
    only a little up, the sides barely curled (the bust's strongly curled sides read as a ranger hat from behind
    and above)."""
    felt, band, brim_m = M('felt'), M('ribbon'), M('brim')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = band_r

    def tap(Q):
        s_ = 1.0 + taper * np.clip(-Q[:, 1] / crown_h, 0, 1)
        off = np.zeros_like(Q)
        off[:, 0] = Q[:, 0] - Q[:, 0] * s_
        off[:, 2] = Q[:, 2] - Q[:, 2] * s_
        return off

    base = S.Warp(S.EllipticCylinder((0, -(crown_h - 4.0) / 2, 0), rx, rz, (crown_h + 4.0) / 2, felt, e=3.2),
                  tap, lip=1.15)
    crown = S.Sub(base, E((0, -crown_h - 0.9, -3.0), (3.4, 3.6, rz * 0.52), felt), k=2.0)
    for sx in (1, -1):
        crown = S.Sub(crown, E((sx * 8.2, -crown_h + 3.4, rz * 0.90), (2.0, 4.0, 2.4), felt), k=2.2)
    bandn = S.EllipticCylinder((0, -2.0, 0), rx + 0.45, rz + 0.45, 1.75, band, e=0.4)

    def snapf(Q):
        x, z = Q[:, 0], Q[:, 2]
        off = np.zeros_like(Q)
        off[:, 1] = snap * (-0.0045 * np.maximum(np.abs(x) - rx * 0.85, 0) ** 2
                            + 0.07 * np.maximum(z - rz * 0.75, 0) + 0.018 * np.minimum(z + rz * 0.75, 0))
        return off

    brimn = S.Warp(S.EllipticCylinder((0, 0.2, 0.6), rx + brim_w, rz + brim_w + 1.0, 0.85, brim_m, e=0.7),
                   snapf, lip=1.3)
    hat = S.Union([crown, bandn, brimn])
    inner = S.Offset(base, -0.7)
    allowed = S.Union([inner, S.Fn(lambda Q: -(Q[:, 1] - 1.6), felt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def _helmet(M, hp):
    """Fireman's leather helmet with a comb and a neck flap (no badge)."""
    m, comb = M('helmet'), M('brass')
    hf = S.Frame((0.0, -13.0, -4.0), S.rot(0, 4.0, 0))
    dome = E((0, -4.0, 0), (19.0, 15.0, 22.0), m)
    dome = S.Inter(dome, S.Plane((0, 3.0, 0), (0, 1, 0), m))
    brim = S.EllipticCylinder((0, 2.4, -2.0), 22.0, 27.0, 0.9, m, e=0.6)
    flap = E((0, 9.0, -20.0), (17.0, 9.0, 4.0), m)
    crest = S.RoundBox((0, -17.0, 0), (1.6, 3.0, 16.0), 1.4, comb)
    hat = S.Union([dome, brim, flap, crest], k=[1.0, 1.4, 0.8])
    allowed = S.Union([S.Offset(dome, -0.8), S.Fn(lambda Q: -(Q[:, 1] - 2.6), m)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def _cloche(M, hp):
    m = M('felt')
    hf = S.Frame((0.0, -11.0, -4.0), S.rot(0, 6.0, 0))
    dome = E((0, -5.0, 0), (18.6, 14.0, 21.4), m)
    dome = S.Inter(dome, S.Plane((0, 4.0, 0), (0, 1, 0), m))
    brim = S.EllipticCylinder((0, 3.6, 1.0), 20.6, 23.6, 1.2, m, e=0.8)
    hat = S.Union([dome, brim], k=1.2)
    allowed = S.Union([S.Offset(dome, -0.8), S.Fn(lambda Q: -(Q[:, 1] - 4.0), m)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


# ------------------------------------------------------------------------------------------------ body build
def _seg(a, b, ra, rb, m):
    return RC(tuple(np.asarray(a, float)), tuple(np.asarray(b, float)), ra, rb, m)


def _frame(o, y_axis, z_hint):
    ey = _n(y_axis)
    zh = np.asarray(z_hint, float)
    ez = _n(zh - ey * float(np.dot(zh, ey)))
    ex = np.cross(ey, ez)
    return S.Frame(o, np.stack([ex, ey, ez], axis=1))


def hand_node(M, mat, rig_arm, s=None):
    import env_c3p2_cine_hands as HN
    a = rig_arm
    s = s or PROP['palm']
    fr = _frame(a['wr'], a['hdir'], a['hup'])
    return S.Xform(HN.hand(M, mat, s, curl=a['curl'], spread=a['spread'], thumb=a['thumb'], grip=a['grip']),
                   frame=fr)


def arm_node(M, ch, a, sf='', hands=True, fade=None):
    """Sleeve from the shoulder over the elbow to the cuff (padded channels for a quilted coat), the shirt cuff,
    the wrist and the hand (palm, fingers, thumb) of one rig arm a = Rig.arm[...] (scene coordinates).
    Round 11: an anatomical sleeve -- the deltoid / biceps mass high on the upper arm, a slimmer elbow, the
    forearm thick below the elbow and tapering to the wrist (no constant-width tube, no sausage folds); cloth
    folds only in the bend of the elbow, more of them the more the arm is bent."""
    sleeve = ch.get('sleeve', 4.0)
    coat_a = M(ch.get('coat_mat', 'coat') + sf)
    skin = ch.get('skin', 'skin') + sf
    sh, el, wr = a['sh'], a['el'], a['wr']
    udir = _n(el - sh)
    fdir = _n(wr - el)
    cuff_end = wr - fdir * 3.5
    lu = float(np.linalg.norm(el - sh))
    lf = float(np.linalg.norm(cuff_end - el))
    bend = float(np.clip(1.0 - np.dot(udir, fdir), 0.0, 1.0))           # 0 straight .. 1 right angle
    knit = ch.get('coat_mat') == 'knit'
    arm_parts = [_seg(sh, el, 9.6 + sleeve, 7.4 + sleeve, coat_a),
                 _seg(el, cuff_end, 7.6 + sleeve, 5.5 + sleeve * (0.75 if knit else 0.9), coat_a),
                 # deltoid + biceps under the sleeve, high on the upper arm
                 _seg(sh + udir * lu * 0.12, sh + udir * lu * 0.50, 10.6 + sleeve, 9.0 + sleeve, coat_a),
                 # the forearm's muscle mass just below the elbow
                 _seg(el + fdir * lf * 0.10, el + fdir * lf * 0.42, 8.4 + sleeve, 7.2 + sleeve, coat_a),
                 E(tuple(el - udir * 1.5), (7.8 + sleeve, 7.8 + sleeve, 7.8 + sleeve), coat_a)]
    armn = S.Union(arm_parts, k=3.5)
    if ch.get('coat') == 'quilted' and ch.get('quilt'):
        # padded channels round the sleeve (constant distance along the bone)
        ax0, axd = a['sh'], _n(a['wr'] - a['sh'])
        per = ch['quilt'] * 0.8

        def qfn(Q, ax0=ax0, axd=axd, per=per):
            u = ((Q - ax0.astype(F32)) @ axd.astype(F32)) / per
            return np.abs(np.sin(np.pi * u)) * 2.0 - 1.0
        armn = S.Displace(armn, qfn, amp=0.8, lipschitz=1.25)
    elif bend > 0.12 and not knit:
        # cloth gathers in the bend of the elbow: a few soft creases round the inner elbow
        ax0, axd = el, fdir
        amp = 0.45 + 0.5 * bend

        def ffn(Q, ax0=ax0, axd=axd):
            u = ((Q - ax0.astype(F32)) @ axd.astype(F32))
            return np.sin(u * 0.42 + 0.6) * np.clip(1.0 - np.abs(u + 2.0) / 14.0, 0, 1)
        armn = S.Displace(armn, ffn, amp=amp, lipschitz=1.25)
    cu = ch.get('cuff')
    extra = []
    if cu:
        extra.append(_seg(cuff_end - fdir * 2.5, wr - fdir * 1.0, 6.4, 6.0, M(cu + sf)))
    elif knit:
        # the ribbed knit cuff, a little tighter than the sleeve
        extra.append(_seg(cuff_end - fdir * 7.0, cuff_end + fdir * 0.5, 5.6 + sleeve * 0.6, 5.4 + sleeve * 0.55, coat_a))
    extra.append(_seg(cuff_end - fdir * 3.0, wr + fdir * 2.5, 5.4, 5.0, M(skin)))       # wrist
    if hands:
        extra.append(hand_node(M, ch.get('glove', skin) if not sf or not ch.get('glove') else ch['glove'] + sf, a))
    pts = [a['sh'], a['el'], a['wr'], a['wr'] + a['hdir'] * 44.0]
    c, r = S.bound_of(pts, 20.0 + sleeve)
    return S.Bound(S.Union([armn] + extra, k=1.2), c, r, margin=3.0)


def build(M, ch, rig: Rig, parts_out=None, hide=(), suffix=None):
    """SDF of the whole posed figure in scene coordinates.  hide = names of parts to leave out ('arm_l', 'arm_r',
    'leg_l', 'leg_r', 'head', 'lower' (everything below the waist), 'hands')."""
    coat = M(ch.get('coat_mat', 'coat'))
    bulk = ch.get('coat_bulk', 4.0)
    nodes = []
    # ---------------------------------------------------------------- torso (chest + pelvis frames)
    # round 11: the trapezius rises high to the neck and runs out flat to the shoulders (no bottle shoulders)
    tc = [_seg((-6, -2, -4.5), (-31, 12, -4), 9.0, 9.5, coat), _seg((6, -2, -4.5), (31, 12, -4), 9.0, 9.5, coat),
          E((0, 16, -3), (35, 10.0, 13.5), coat), E((-38.5, 22, -3), (12.5, 13.0, 12.5), coat),
          E((38.5, 22, -3), (12.5, 13.0, 12.5), coat), E((0, 36, 2), (30.0, 24, 15.5), coat),
          E((0, 32, -6), (32, 24, 12.5), coat), E((0, 72, 1), (25.5, 27, 14.0), coat)]
    chest = S.Union(tc, k=6.0)
    if bulk:
        chest = S.Offset(chest, bulk, coat)
    if ch.get('coat') in ('quilted',) and ch.get('quilt'):
        chest = CC.quilted(chest, period=ch['quilt'], amp=0.9)
    tp = [E((0, -26, 4), (25, 18, 14), coat), E((0, -6, 0), (27, 16, 15), coat),
          E((-11, 5, -8), (13, 13, 11), coat), E((11, 5, -8), (13, 13, 11), coat)]
    pelv = S.Union(tp, k=6.0)
    if bulk:
        pelv = S.Offset(pelv, bulk, coat)
    torso = S.Union([S.Xform(chest, o=rig.o_ch, R=rig.R_ch), S.Xform(pelv, o=rig.o_pel, R=rig.R_pel)], k=10.0)
    ctr = rig.chest((0, 50, 0))
    nodes.append(S.Bound(torso, ctr, 120.0 + bulk, margin=3.0))
    # ---------------------------------------------------------------- neck + head
    if 'head' not in hide:
        hn, _spec = _head_node(M, ch, jaw_open=ch.get('jaw', 0.0))
        nk = M('neck')
        # a man's neck from behind is ~0.7 of the head's width and flares into the trapezius
        top = rig.head((0.0, 8.0, -5.0))
        bot = rig.chest((0.0, -1.0, -4.5))
        neck = _seg(top, bot, 11.6, 13.6, nk)
        hs = ch.get('head_scale', HEAD_SCALE)
        hnode = S.Xform(hn, o=rig.o_head, R=rig.R_head)
        if hs != 1.0:
            hnode = S.Scale(hnode, rig.atlas, hs)
        head = S.Union([hnode, neck], k=2.5)
        nodes.append(S.Bound(head, rig.head((0, -4, 0)), 62.0, margin=3.0))
    # ---------------------------------------------------------------- garments on the torso
    nodes += _collar_scarf(M, ch, rig, coat, bulk)
    # ---------------------------------------------------------------- arms
    suffix = suffix or {}
    for key in ('arm_l', 'arm_r'):
        if key in hide:
            continue
        nodes.append(arm_node(M, ch, rig.arm[key], suffix.get(key, ''), hands='hands' not in hide))
    # ---------------------------------------------------------------- legs
    if 'lower' not in hide:
        trous = M(ch.get('trouser', 'trouser'))
        boot = M(ch.get('boot', 'shoe') if ch.get('boot') != 'kirza' else 'boot')
        for key in ('leg_l', 'leg_r'):
            if key in hide:
                continue
            lg = rig.leg[key]
            hip, kn, an, ft = lg['hip'], lg['kn'], lg['an'], lg['foot']
            lp = [_seg(hip, kn, 15.0, 10.5, trous), _seg(kn, an, 10.0, 7.0, trous)]
            # calf
            sd = _n(an - kn)
            back = _n(np.cross(sd, np.cross(ft, sd))) if abs(float(np.dot(ft, sd))) < 0.98 else -ft
            lp.append(E(tuple(kn + sd * 26.0 - back * 2.5), (8.6, 20.0, 8.6), trous))
            legn = S.Union(lp, k=4.0)
            sole_up = np.array([0.0, PROP['ankle_h'], 0.0])
            heel = an + sole_up * 0.55 - ft * PROP['heel']
            toe = an + sole_up * 0.75 + ft * (PROP['foot'] - PROP['heel'] - 6.0)
            bp = [_seg(heel, toe, 7.4, 6.2, boot), E(tuple(an + sole_up * 0.2), (8.6, 9.0, 9.0), boot)]
            if ch.get('boot') == 'kirza':
                bp.append(_seg(an + sole_up * 0.2, an - sd * 44.0, 8.6, 10.6, boot))       # boot shaft
            bootn = S.Union(bp, k=3.0)
            pts = [hip, kn, an, toe]
            c, r = S.bound_of(pts, 22.0)
            nodes.append(S.Bound(S.Union([legn, bootn], k=1.5), c, r, margin=3.0))
        nodes += _skirt(M, ch, rig, coat, bulk, hide)
    # ---------------------------------------------------------------- straps, bag, belt, buttons
    nodes += _accessories(M, ch, rig, coat, bulk, hide)
    root = S.Union(nodes, k=1.0)
    if parts_out is not None:
        parts_out['nodes'] = nodes
    return root


def _collar_scarf(M, ch, rig, coat, bulk):
    out = []
    col = ch.get('collar')
    cm = M(ch.get('collar_mat', ch.get('coat_mat', 'coat')))
    if col == 'turned':
        ring = S.Shell(RC((0, -24, -5.5), (0, 8, -1.5), 16.2, 21.0, cm), 1.8, cm)
        ring = S.Inter(ring, S.Fn(lambda Q: np.maximum(Q[:, 1] - 8.0, -24.0 - Q[:, 1] + 9.0 * np.clip(Q[:, 2] / 14.0, 0, 1)), cm))
        ring = S.Sub(ring, S.Fn(lambda Q: np.maximum(7.0 - Q[:, 2], np.abs(Q[:, 0]) - 5.5), cm), k=1.0)
        out.append(S.Xform(ring, o=rig.o_ch, R=rig.R_ch))
    elif col == 'stand':
        ring = S.Shell(RC((0, -21, -4.0), (0, 6, -1.0), 15.2, 17.6, cm), 1.9, cm)
        ring = S.Inter(ring, S.Fn(lambda Q: np.maximum(Q[:, 1] - 6.0, -21.0 - Q[:, 1]), cm))
        ring = S.Sub(ring, S.Fn(lambda Q: np.maximum(9.0 - Q[:, 2], np.abs(Q[:, 0]) - 4.0), cm), k=1.0)
        out.append(S.Xform(ring, o=rig.o_ch, R=rig.R_ch))
    elif col == 'suit':
        # a suit jacket: the shirt collar round the neck, the jacket's collar rolled low over it at the back
        sm = M(ch.get('cuff') or 'shirt')
        shirt = S.Shell(RC((0, -16, -4.0), (0, 2, -2.0), 14.0, 15.2, sm), 1.2, sm)
        shirt = S.Inter(shirt, S.Fn(lambda Q: np.maximum(Q[:, 1] - 2.0, -16.0 - Q[:, 1] + 6.0 * np.clip(Q[:, 2] / 12.0, 0, 1)), sm))
        roll = S.Shell(RC((0, -9, -4.5), (0, 8, -1.5), 16.0, 18.4, cm), 1.7, cm)
        roll = S.Inter(roll, S.Fn(lambda Q: np.maximum(Q[:, 1] - 8.0, -8.0 - Q[:, 1] + 10.0 * np.clip(Q[:, 2] / 12.0, 0, 1)), cm))
        roll = S.Sub(roll, S.Fn(lambda Q: np.maximum(6.0 - Q[:, 2], np.abs(Q[:, 0]) - 8.0), cm), k=1.0)
        out.append(S.Xform(S.Union([shirt, roll], k=0.6), o=rig.o_ch, R=rig.R_ch))
    elif col == 'fur':
        fm = M('fur')
        parts = []
        for i in range(14):
            a = math.radians(i * 360.0 / 14)
            parts.append(E((14.0 * math.sin(a), 2.0 + 1.2 * math.cos(a * 2), -1.5 + 12.5 * math.cos(a)),
                           (6.0, 5.0, 6.0), fm))
        out.append(S.Xform(S.Union(parts, k=2.5), o=rig.o_ch, R=rig.R_ch))
    if ch.get('scarf'):
        out.append(S.Xform(CC.scarf_wrap(M, y=-10.0, r=15.0, tube=6.2, ends='drape'), o=rig.o_ch, R=rig.R_ch))
    if ch.get('rollneck'):
        # centred on the neck (its axis lies 3-4 units behind the chest frame's origin), a little wider than it
        out.append(S.Xform(CC.rollneck(M, 'knit', y_top=-23.0, y_bot=3.0, r=(14.4, 15.6), z=-3.8), o=rig.o_ch,
                           R=rig.R_ch))
    return out


def _skirt(M, ch, rig, coat, bulk, hide):
    """Coat skirt below the waist: one panel per leg that follows the thigh and falls from the knee toward the
    hem, a back panel between them; flare widens the hem (women's coats)."""
    hem = ch.get('hem', 0.0)
    if hem <= 10.0:
        return []
    fl = ch.get('flare', 1.0)
    out = []
    down = np.array([0.0, 1.0, 0.0])
    pan = []
    for key in ('leg_l', 'leg_r'):
        lg = rig.leg[key]
        hip, kn, an = lg['hip'], lg['kn'], lg['an']
        side = lg['side']
        top = rig.pelvis((side * 12.0, -18.0, 0.0))
        thigh_len = PROP['thigh']
        if hem <= thigh_len * 0.9:
            # short jacket / quilted coat: the panel ends on the thigh
            u = hem / thigh_len
            end = hip + (kn - hip) * u + down * 4.0
            pan.append(_seg(top, end, 20.0 + bulk * 0.6, (18.5 + bulk * 0.5) * fl, coat))
        else:
            rest = hem - thigh_len
            sd = _n(an - kn)
            hang = _n(sd * 0.45 + down * 0.55)
            end = kn + hang * rest
            pan.append(_seg(top, kn, 22.0 + bulk, 17.5 + bulk, coat))
            pan.append(_seg(kn, end, 17.5 + bulk, (17.0 + bulk) * fl, coat))
    # back panel (between the legs at the back, it hangs from the buttocks)
    ml = rig.leg['leg_l']
    mr = rig.leg['leg_r']
    mid_kn = (ml['kn'] + mr['kn']) / 2
    back = rig.pelvis((0.0, 4.0, -10.0))
    if hem > PROP['thigh'] * 0.9:
        end = mid_kn + (down * 0.8 + _n(mid_kn - rig.o_pel) * 0.2) * (hem - PROP['thigh']) + rig.R_pel @ np.array([0, 0, -8.0])
        pan.append(_seg(back, mid_kn + rig.R_pel @ np.array([0, 0, -10.0]), 21.0 + bulk, 18.0 + bulk, coat))
        pan.append(_seg(mid_kn + rig.R_pel @ np.array([0, 0, -10.0]), end, 18.0 + bulk, (18.0 + bulk) * fl, coat))
    else:
        mid = (ml['hip'] + mr['hip']) / 2 + (mid_kn - (ml['hip'] + mr['hip']) / 2) * (hem / PROP['thigh'])
        pan.append(_seg(back, mid + rig.R_pel @ np.array([0, 0, -6.0]), 20.0 + bulk * 0.6, 18.5 + bulk * 0.5, coat))
    skirt = S.Union(pan, k=9.0)
    # flatten the panels into cloth: keep them within a slab around the legs' plane is overkill -- a gentle
    # hem cut perpendicular to gravity keeps the lower edge crisp
    lowest = max(float(p[1]) for p in [rig.leg['leg_l']['kn'], rig.leg['leg_r']['kn']]) + max(0.0, hem - PROP['thigh']) + 10.0
    if hem > PROP['thigh'] * 0.9:
        skirt = S.Inter(skirt, S.Fn(lambda Q: Q[:, 1] - lowest, coat))
    if ch.get('coat') == 'quilted' and ch.get('quilt'):
        skirt = S.Xform(CC.quilted(S.Xform(skirt, o=-rig.o_pel), period=ch['quilt'], amp=0.9), o=rig.o_pel)
    pts = [rig.o_pel, rig.leg['leg_l']['kn'], rig.leg['leg_r']['kn'], rig.leg['leg_l']['an'], rig.leg['leg_r']['an']]
    c, r = S.bound_of(pts, 40.0 + bulk)
    out.append(S.Bound(skirt, c, r, margin=3.0))
    return out


def _accessories(M, ch, rig, coat, bulk, hide):
    out = []
    if ch.get('strap'):
        st = M('strap')
        # from the right shoulder (front and back) across to the left hip
        sx = 1.0 if ch['strap'][0] == 'l' else -1.0
        pts_f = [(sx * 22.0, 4.0, 15.0 + bulk), (sx * 6.0, 36.0, 19.0 + bulk), (-sx * 14.0, 70.0, 17.0 + bulk),
                 (-sx * 25.0, 96.0, 13.0 + bulk)]
        pts_b = [(sx * 24.0, 2.0, -12.0 - bulk), (sx * 6.0, 34.0, -19.5 - bulk), (-sx * 14.0, 68.0, -17.0 - bulk),
                 (-sx * 26.0, 96.0, -12.0 - bulk)]
        segs = []
        for pts in (pts_f, pts_b):
            for i in range(len(pts) - 1):
                segs.append(RC(pts[i], pts[i + 1], 2.4, 2.4, st))
        top = [RC((sx * 22.0, 4.0, 15.0 + bulk), (sx * 30.0, -2.0, 2.0), 2.4, 2.4, st),
               RC((sx * 30.0, -2.0, 2.0), (sx * 24.0, 2.0, -12.0 - bulk), 2.4, 2.4, st)]
        out.append(S.Xform(S.Union(segs + top, k=0.8), o=rig.o_ch, R=rig.R_ch))
    if ch.get('bag') and 'lower' not in hide:
        bg = M('bag')
        side = 1.0 if ch['bag'] == 'l' else -1.0
        bag = S.RoundBox((side * (31.0 + bulk), 6.0, 2.0), (6.0, 15.0, 19.0), 3.0, bg)
        flap = S.RoundBox((side * (33.0 + bulk), -2.0, 2.0), (5.0, 7.0, 19.5), 2.6, bg)
        out.append(S.Xform(S.Union([bag, flap], k=1.0), o=rig.o_pel, R=rig.R_pel))
    if ch.get('belt'):
        bl = M('belt')
        belt = S.Shell(E((0, -14, 1), (28.5 + bulk, 5.0, 17.5 + bulk), bl), 1.5, bl)
        belt = S.Inter(belt, S.Fn(lambda Q: np.abs(Q[:, 1] + 14.0) - 3.2, bl))
        out.append(S.Xform(belt, o=rig.o_pel, R=rig.R_pel))
    if ch.get('buttons'):
        bt = M('button')
        bs = [S.Sphere((sx * 7.0, y, 18.5 + bulk), 1.8, bt) for sx in (-1, 1) for y in (22.0, 40.0, 58.0)]
        out.append(S.Xform(S.Union(bs), o=rig.o_ch, R=rig.R_ch))
    return out


# ------------------------------------------------------------------------------------------------ light + styles
def _lin(h):
    c = P.hexc(h).astype(np.float64) / 255.0
    return c ** 2.2


def _srgb(c):
    c = np.clip(c, 0, 1) ** (1 / 2.2)
    return '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in c)


LIGHTS = {
    # key colour, ambient colour, rim colour, key gain
    'night': ((0.62, 0.72, 0.95), (0.20, 0.24, 0.40), '#8ea4bc', 1.9),
    'lamp': ((1.00, 0.80, 0.55), (0.09, 0.10, 0.19), '#7f96ae', 2.2),
    'yard': ((1.00, 0.84, 0.62), (0.18, 0.21, 0.36), '#8fa6b4', 2.0),
    'fire': ((1.00, 0.56, 0.26), (0.10, 0.11, 0.21), '#6f8ea6', 2.4),
    'green': ((0.40, 1.00, 0.52), (0.09, 0.11, 0.20), '#56708a', 2.0),
    'dial': ((1.00, 0.74, 0.44), (0.08, 0.09, 0.17), '#5f7a86', 2.3),
    'dawn': ((0.80, 0.80, 0.86), (0.26, 0.28, 0.40), '#a8b6c8', 1.8),
}
LEVELS8 = [0.0, 0.05, 0.10, 0.17, 0.27, 0.41, 0.60, 0.86]
TH7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]

ALBEDO = {
    'konrad': {'coat': '#2a3a64', 'coat_lapel': '#2a3a64', 'felt': '#4a4248', 'brim': '#4a4248', 'ribbon': '#1d1a20',
               'scarf': '#a08a62', 'hair': '#3e2e2c', 'trouser': '#2c2f3a', 'shoe': '#1d1714', 'boot': '#1d1714',
               'shirt': '#c8c0b2', 'strap': '#5e3a24', 'bag': '#6a4428', 'jacket': '#34363e'},
    'alexei': {'quilt': '#34503e', 'coat': '#34503e', 'fur': '#6a6258', 'hat_top': '#2e2620', 'knit': '#4a4e56',
               'trouser': '#292c34', 'boot': '#3a2a20', 'shoe': '#2a201a', 'strap': '#5e3a24', 'bag': '#74502e',
               'hair': '#3a2c22', 'tie_string': '#5a4a3a'},
}
EXTRA_ALBEDO = {'coat': '#3a3a40', 'trouser': '#2c2e36', 'shoe': '#1e1a18', 'boot': '#2a221c', 'felt': '#4a4448',
                'brim': '#4a4448', 'ribbon': '#1d1a20', 'scarf': '#7a5a4a', 'hair': '#3a3030', 'shirt': '#b8b0a4',
                'cap': '#2a2e3a', 'cap_band': '#16161c', 'visor': '#121218', 'cord': '#a08040', 'button': '#a08a50',
                'fjacket': '#2e2c2a', 'helmet': '#2a2420', 'brass': '#b08a40', 'belt': '#2a2018', 'fur': '#5a4c40',
                'hat_top': '#3e342c', 'knit': '#4a4c50', 'kerchief': '#6a3a34', 'stocking': '#2a2224',
                'quilt': '#3a4436', 'strap': '#4a2e1c', 'bag': '#5a3a22', 'tie_string': '#4a3c30', 'moustache': '#6a6460',
                'wood': '#6a4a30', 'iron': '#3a3c40', 'hose': '#4a4038', 'case': '#5a3a26', 'card': '#7e6242',
                'paper': '#d8cfb2', 'pencil': '#c4983a', 'pencil_wood': '#cfae80', 'graphite': '#2c2c32',
                'chair': '#4a3020', 'list': '#e2dccb'}


def ramp_for(albedo_hex, light, n=8, sheen=0.0):
    key, amb, _rim, gain = LIGHTS[light]
    a = _lin(albedo_hex)
    cols = []
    for i in range(n):
        l = LEVELS8[i] if n == 8 else i / (n - 1)
        c = a * (np.asarray(amb) * (0.55 + 0.45 * (1 - l)) + np.asarray(key) * l * gain)
        c = c + sheen * l * l * np.asarray(key) * 0.08
        cols.append(_srgb(c))
    return P.ramp(*cols)


SKIN_ALBEDO = {'konrad': '#d6a888', 'alexei': '#cf9a76'}
SKIN_LV = [0.010, 0.026, 0.055, 0.10, 0.18, 0.31, 0.56, 0.93]
SKIN_KMIX = [0.0, 0.05, 0.15, 0.30, 0.55, 0.80, 0.95, 1.0]


def skin_ramp(albedo_hex, light):
    """Skin under a scene light (round 11): skin scatters light, so its shadows stay warm brown (the portrait
    ramps' lilac / mauve shadow steps read as bruised skin on the small figures); the lit steps take the colour
    of the key light, the deepest steps a trace of the ambient."""
    key, amb, _rim, _gain = LIGHTS[light]
    a = _lin(albedo_hex)
    kc = np.asarray(key, float) / max(key)
    ac = np.asarray(amb, float) / max(amb)
    warm = np.array([1.0, 0.70, 0.56])
    cols = []
    for lv, k in zip(SKIN_LV, SKIN_KMIX):
        tint = (warm * (1 - k) + kc * k) * 0.88 + ac * 0.12 * (1 - k)
        cols.append(_srgb(a * lv * tint * 1.6))
    return P.ramp(*cols)


def styles(char_id, light, overrides=None, skin=None):
    """Material styles for one figure under one light: ramps from the material albedos."""
    alb = dict(EXTRA_ALBEDO)
    alb.update(ALBEDO.get(char_id, {}))
    if overrides:
        alb.update(overrides)
    key, amb, rim, gain = LIGHTS[light]
    st = {}
    for nm, h in alb.items():
        dith = 0.05 if nm in ('coat', 'quilt', 'fur', 'felt', 'fjacket', 'scarf', 'knit') else 0.02
        st[nm] = MatStyle(ramp_for(h, light), TH7, dither=dith, rim=rim)
    for nm in ('visor', 'brass', 'button', 'cord'):
        if nm in st:
            st[nm] = MatStyle(st[nm].ramp, TH7, rim=rim, spec=1.0, spec_pow=16.0)
    sk = skin if skin is not None else skin_ramp(SKIN_ALBEDO.get(char_id, '#d2a282'), light)
    sst = MatStyle(sk, CC.SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24, ao=0.75)
    for nm in ('skin', 'neck', 'ear', 'lip', 'skin_k', 'skin_a'):
        st[nm] = sst
    return st


GROUPS = {'skin': 0, 'lip': 0, 'ear': 0, 'neck': 1, 'hair': 0, 'felt': 2, 'brim': 3, 'ribbon': 2, 'fur': 2,
          'hat_top': 2, 'tie_string': 2, 'cap': 2, 'cap_band': 2, 'visor': 3, 'cord': 2, 'helmet': 2, 'brass': 2,
          'kerchief': 2, 'coat': 4, 'quilt': 4, 'fjacket': 4, 'coat_lapel': 8, 'shirt': 5, 'scarf': 6, 'knit': 6,
          'strap': 7, 'bag': 7, 'belt': 7, 'button': 7, 'trouser': 10, 'stocking': 10, 'shoe': 9, 'boot': 9,
          'skin_k': 1, 'skin_a': 0, 'moustache': 0}


# ------------------------------------------------------------------------------------------------ camera + render
def camera(yaw=0.0, elev=0.0, roll=0.0):
    """Scene -> view rotation: the figure turned by yaw (0 = faces the viewer, 90 = walks to image right,
    180 = seen from behind), then the camera's elevation (> 0 looks down on it)."""
    return _rx_view(elev) @ S.rot(yaw, 0.0, roll)


def _rx_view(e):
    return S.rot(0.0, e, 0.0)


def _o3(p):
    p = [float(v) for v in p]
    return np.array(p + [0.0] * (3 - len(p)))


def place(node, origin_px, R, scale):
    """Scene node -> view node: scene point q appears at origin_px + scale * R q."""
    o = _o3(origin_px)
    return S.Scale(S.Xform(node, o=o / scale, R=R), (0.0, 0.0, 0.0), scale)


_SRC_KEY = []


def _src_key():
    """Hash of the sculpting / painting sources AS LOADED by this process (computed once, at the first call right
    after import): a generator that runs while the files are being edited must not file renders of its in-memory
    code under the key of the edited files."""
    if not _SRC_KEY:
        h = hashlib.sha1(b'c3p2-body-v2')
        for f in ('chargen_portrait2_anat.py', 'chargen_portrait2_cast.py', 'chargen_portrait2_paint.py',
                  'chargen_portrait2_sdf.py', 'env_c3p2_cine_hands.py', 'env_c3p2_cine_body.py'):
            with open(os.path.join(HERE, f), 'rb') as fh:
                h.update(fh.read())
        _SRC_KEY.append(h.hexdigest()[:16])
    return _SRC_KEY[0]


def view_frame(o_scene, R_scene, origin_px, Rcam, scale):
    """A local frame (for the tone passes) given in scene coordinates -> view frame with the scale folded in."""
    o = _o3(origin_px) + scale * (Rcam @ np.asarray(o_scene, float))
    R = Rcam @ np.asarray(R_scene, float)
    return S.Frame(o, R / scale)


TRACE_DEPTH = (90.0, -90.0, 110)      # the default tracing volume (view z) and march steps


def trace_paint(root, M, size, look, st, frames=None, tone_passes=(), ss=3, glow=None, outline=True, rim=True,
                depth=None):
    """Trace + paint a scene in view space -> (rgba uint8, downsampled G-buffer).  glow = (centre, radius, floor):
    the key light fades with the distance from a local source (fire in a hatch, a lamp).  depth = (z near, z far,
    steps): round 11 -- the close shots reach far beyond the default +-90 px volume (a hand on a notepad far up
    the desk, a shoulder close to the camera were cut away by it)."""
    w, h = size
    lk = P.Look(**look)
    z0, zf, steps = depth or TRACE_DEPTH
    g = S.trace(root, w, h, ss=ss, key=lk.key, z0=z0, zfar=zf, steps=steps)
    d = S.downsample(g, len(M))
    names = M.names
    G = dict(d=d, M=M, look=lk, zoom=1.0)
    for k, fr in (frames or {}).items():
        G[k] = fr
    st = dict(st)
    for nm in names:
        if nm not in st and '__' in nm and nm.split('__')[0] in st:
            st[nm] = st[nm.split('__')[0]]
    v, rimv, keyv = P.light_value(d, lk, st, names)
    if glow is not None:
        c, r, floor = glow
        dist = np.linalg.norm(d.P - np.asarray(c, np.float32)[None, None, :], axis=2)
        fall = np.clip(1.0 - dist / r, 0.0, 1.0) ** 1.3
        v = v * (floor + (1.0 - floor) * fall).astype(np.float32)
        keyv = keyv * fall.astype(np.float32)
    v = P.smooth_by_material(v, d.mat, passes=1)
    tone = P.quantise(d, v, st, names)
    for fn in tone_passes:
        tone = fn({}, G, tone, v)
    tone = P.clean(tone, d.mat)
    rgb = P.colorize(d, tone, st, names)
    rgb = hair_fade(rgb, d, names)
    if outline:
        rgb = P.outline(rgb, d, st, names, look=lk)
        grp = dict(GROUPS)
        for nm in names:
            if '__' in nm:
                grp[nm] = 20 + names.index(nm)          # its own group: a contact line where it crosses the body
        rgb, _ = P.depth_lines(rgb, d, st, names, grp)
    if rim:
        rgb = P.apply_rim(rgb, d, rimv, keyv, st, names, tone)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    return out, d


def face_marks(rgba, d, heads, scale, Rcam, origin_px, col=(26, 18, 22), brow=True):
    """Eyes (and brows) of small faces that look toward the camera: the 2D feature pass of the portraits in
    miniature.  heads = [(o_head, R_head)] in scene coordinates."""
    out = rgba.copy()
    h, w = out.shape[:2]
    o3 = _o3(origin_px)
    for hd in heads:
        oh, Rh = hd[0], hd[1]
        if len(hd) > 2:
            hs, at = hd[2], np.asarray(hd[3], float)
            oh = at + hs * (np.asarray(oh, float) - at)
            Rh = np.asarray(Rh) * hs
        fwd = Rcam @ (Rh @ np.array([0.0, 0.0, 1.0]))
        if fwd[2] < 0.2:
            continue
        sz = max(1, int(round(scale * 3.2)))
        for ex in (-6.3, 6.3):
            p = o3 + scale * (Rcam @ (np.asarray(oh) + Rh @ np.array([ex, 0.6, 15.0])))
            x, y = int(math.floor(p[0])), int(math.floor(p[1]))
            if not (0 <= x < w and 0 <= y < h) or not d.hit[y, x]:
                continue
            if d.z[y, x] > p[2] + 2.5 * max(1.0, scale * 3):
                continue                           # hidden behind the nose / a hat brim
            for dy in range(sz if sz < 3 else 2):
                for dx in range(sz):
                    xx, yy = x + dx - sz // 2, y + dy
                    if 0 <= xx < w and 0 <= yy < h and out[yy, xx, 3]:
                        out[yy, xx, :3] = col
            if brow and scale >= 0.35:
                pb = o3 + scale * (Rcam @ (np.asarray(oh) + Rh @ np.array([ex * 1.05, -3.6, 15.6])))
                bx, by = int(math.floor(pb[0])), int(math.floor(pb[1]))
                for dx in range(-sz // 2, sz - sz // 2 + 1):
                    if 0 <= bx + dx < w and 0 <= by < h and out[by, bx + dx, 3]:
                        out[by, bx + dx, :3] = np.minimum(out[by, bx + dx, :3], np.array(col) + 30)
    return out


def paint_scene(root, M, size, look, st, frames=None, tone_passes=(), ss=3, cache=None, glow=None, outline=True,
                rim=True, post=None):
    """trace_paint with a disk cache; post(rgba, d) -> rgba runs before caching."""
    key = None
    if cache is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        import tempfile
        h = hashlib.sha1((_src_key() + repr((cache, size, look, ss, outline, rim, glow))).encode('utf-8')).hexdigest()[:20]
        dd = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
        os.makedirs(dd, exist_ok=True)
        key = os.path.join(dd, 'body_' + h + '.npz')
        if key in _memo:
            return _memo[key]
        if os.path.exists(key):
            out = np.load(key)['rgba']
            _memo[key] = out
            return out
    out, d = trace_paint(root, M, size, look, st, frames=frames, tone_passes=tone_passes, ss=ss, glow=glow,
                         outline=outline, rim=rim)
    if post is not None:
        out = post(out, d)
    if key is not None:
        np.savez(key, rgba=out)
        _memo[key] = out
    return out


def pass_hair_strands(mat='hair', seed=23):
    """Cropped hair seen from behind / the side (round 11; the bust hair is a smooth bowl at figure scale):
    strands fanning down from the crown in the head frame 'hf', broken into clumps, a lighter strand here and
    there on the lit side, the short hair over the nape one step darker."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names or 'hf' not in G:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = CC._local(G, 'hf', m)
        th = np.arctan2(L[:, 0], L[:, 1] + 27.0)
        r = np.hypot(L[:, 0], L[:, 1] + 27.0)
        k = np.floor(th * 26.0 / np.pi + 0.35 * np.sin(r * 0.21)).astype(int)
        seg = np.floor(r / 6.0).astype(int)
        h1 = CC._hash2(k, np.zeros_like(k), seed)
        h2 = CC._hash2(k, seg, seed + 7)
        t = tone[m].copy()
        dark = (h1 < 0.36) | (h2 < 0.16)
        lite = (h1 > 0.80) & (h2 > 0.30) & (v[m] > 0.18)
        t = np.where(dark & (t >= 2), t - 1, np.where(lite & (t >= 2) & (t <= 4), t + 1, t))
        low = L[:, 1] > 10.5
        t = np.where(low & (t >= 2), t - 1, t)
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def hair_fade(rgb, d, names):
    """The hairline at the nape and the temples: a few hairs reach into the skin below (every other pixel takes
    a darkened hair colour), the hair's lowest row softens toward the skin -- no hard bowl edge."""
    if 'hair' not in names:
        return rgb
    hid = names.index('hair')
    sk = [names.index(n) for n in ('neck', 'skin') if n in names]
    if not sk:
        return rgb
    mh = (d.mat == hid) & d.hit
    ms = np.isin(d.mat, sk) & d.hit
    h, w = mh.shape
    yy, xx = np.mgrid[0:h, 0:w]
    out = rgb.astype(np.float32).copy()
    src = rgb.astype(np.float32)
    up1 = np.zeros_like(mh)
    up1[1:] = mh[:-1]
    up2 = np.zeros_like(mh)
    up2[2:] = mh[:-2]
    hair_above = np.zeros_like(src)
    hair_above[1:] = src[:-1]
    hair_above2 = np.zeros_like(src)
    hair_above2[2:] = src[:-2]
    # depth continuity: only where the hair and the skin touch on the surface (not a hat brim over a far neck)
    zc = np.zeros_like(d.z)
    zc[1:] = d.z[:-1]
    near = np.abs(d.z - zc) < 3.0
    s1 = ms & up1 & near & (((xx + yy) % 2) == 0)
    out[s1] = src[s1] * 0.35 + hair_above[s1] * 0.65 * 0.92
    s2 = ms & up2 & ~up1 & near & ((xx % 3) == (yy % 3))
    out[s2] = src[s2] * 0.6 + hair_above2[s2] * 0.4
    dn1 = np.zeros_like(ms)
    dn1[:-1] = ms[1:]
    s3 = mh & dn1 & (((xx + yy) % 2) == 1)
    skin_below = np.zeros_like(src)
    skin_below[:-1] = src[1:]
    out[s3] = src[s3] * 0.7 + skin_below[s3] * 0.3
    return np.clip(out, 0, 255).astype(rgb.dtype)


def figure_passes(ch, frames_ok=True):
    tp = [pass_hair_strands()]
    if ch.get('hat') == 'ushanka' or ch.get('collar') == 'fur':
        tp.append(CC.pass_fur('fur'))
    if ch.get('scarf'):
        tp.append(CC.pass_knit('scarf'))
    if ch.get('rollneck'):
        tp.append(CC.pass_knit('knit', ribs=30))
    if ch.get('hat') in ('fedora', 'homburg', 'cloche'):
        tp.append(CC.pass_grain('felt', 0.07, seed=3))
    if frames_ok and ch.get('coat') == 'quilted' and ch.get('quilt'):
        tp.append(CC.pass_stitches(ch.get('coat_mat', 'coat'), ch['quilt'], frame='tf', axis=1))
    if ch.get('coat') == 'long':
        tp.append(CC.pass_grain(ch.get('coat_mat', 'coat'), 0.04, seed=4))
    return tp


def render(ch, pose, size, origin_px, yaw=0.0, elev=0.0, scale=0.2, light='night', look=None, styles_=None,
           hide=(), ss=3, cache=None, glow=None, extra_nodes=None, outline=True, rim=True, pose_is_rig=False,
           eyes=True):
    """Render one posed figure into a (w, h) RGBA sprite.  origin_px = where the scene origin (ground under the
    hips by default) lands in the sprite.  look: dict for chargen_portrait2_paint.Look (light directions in view
    space), default per light preset; styles_: material styles (default styles(ch['id'], light))."""
    M = A.Mats()
    rig = pose if pose_is_rig else Rig(pose)
    node = build(M, ch, rig, hide=hide)
    if extra_nodes:
        # props in scene coordinates, built from the posed rig (f(M, rig) -> node): shovel, hose, suitcase ...
        node = S.Union([node] + [f(M, rig) for f in extra_nodes], k=0.5)
    Rc = camera(yaw, elev)
    root = place(node, origin_px, Rc, scale)
    lk = look or dict(key=(0.45, -0.55, 0.70), rim=(-0.70, -0.40, -0.60), ambient=0.07, wrap=0.12, bg='berlin',
                      glow=(0.8, 0.2), fill=0.06, fill_dir=(0.0, -0.8, 0.6), ao=0.5)
    st = styles_ or styles(ch['id'], light)
    frames = {'tf': view_frame(rig.o_ch, rig.R_ch, origin_px, Rc, scale),
              'hf': view_frame(rig.o_head, rig.R_head, origin_px, Rc, scale)}
    tps = figure_passes(ch)

    def post(img, d):
        if 'head' in hide or not eyes:
            return img
        return face_marks(img, d, [(rig.o_head, rig.R_head, ch.get('head_scale', HEAD_SCALE), rig.atlas)], scale,
                          Rc, origin_px)
    return paint_scene(root, M, size, lk, st, frames=frames, tone_passes=tps, ss=ss,
                       cache=(cache, repr(sorted(ch.items())), repr(pose) if not pose_is_rig else 'rig', size,
                              tuple(origin_px), yaw, elev, scale, light, repr(lk), tuple(hide), eyes) if cache else None,
                       glow=glow, outline=outline, rim=rim, post=post)


_src_key()
