"""chargen_portrait2_anat -- parametric head / neck / torso sculpt (signed distance) for the dialogue busts.

Head-local frame: origin between the eyes on the eye line (y = 0), x -> the character's LEFT (image right
when the head faces the viewer), y down, z out of the face.  Units = final portrait pixels; a head is about
52 px from chin to crown (chin y ~ +25.5, crown y ~ -26.5).

The sculpt follows the classic planes of the head (Asaro): a cranium ellipsoid, a forehead block and a
mid-face block with rounded corners (flat front / side planes), cheekbones, malar pads, brow ridge, shallow
eye sockets with eyeballs as lids, a nose made of bridge / tip / alae, the dental "muzzle", lips, a lower
face (jaw) mass with a defined jaw line and a box chin -- the whole jaw group rotates about the hinge for the
talking frames -- ears, neck with sterno-mastoids.
"""
from __future__ import annotations

import numpy as np

import chargen_portrait2_sdf as S


class Mats:
    """Material registry: name -> small int id (ids are stable in insertion order)."""

    def __init__(self):
        self.names: list[str] = []

    def __call__(self, name: str) -> int:
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def __len__(self):
        return len(self.names)


DEFAULT_HEAD = dict(
    # cranium + blocks
    skull_c=(0.0, -9.6, -5.0), skull_r=(16.2, 16.9, 20.6),
    fore_c=(0.0, -8.0, 3.6), fore_h=(12.0, 9.0, 12.0), fore_rad=6.5,
    mid_c=(0.0, 5.0, 4.0), mid_h=(12.2, 7.0, 11.6), mid_rad=5.6,
    cheek_c=(10.6, 3.0, 9.8), cheek_r=(4.6, 3.0, 4.0),
    malar_c=(7.0, 8.0, 12.0), malar_r=(4.2, 3.6, 3.4),
    brow_c=(0.0, -3.4, 13.0), brow_r=(12.0, 2.5, 3.3),
    # eyes
    eye_x=6.3, eye_y=0.2, socket_r=(4.2, 2.6, 2.0), socket_z=16.8, eyeball_r=3.9, eyeball_z=11.3,
    # nose
    nose_root=(0.0, -1.4, 15.4), nose_tip=(0.0, 9.3, 19.7), nose_r=(1.5, 2.0), tip_r=2.4,
    ala_x=2.4, ala_y=10.5, ala_z=16.9, ala_r=(1.6, 1.5, 1.9),
    # mouth
    muzzle_c=(0.0, 14.6, 11.6), muzzle_r=(7.0, 5.6, 5.8),
    mouth_y=14.9, lip_up=(0.0, 14.1, 16.6), lip_up_r=(4.3, 1.25, 1.45),
    lip_lo=(0.0, 16.25, 16.2), lip_lo_r=(3.7, 1.45, 1.55),
    # lower face / jaw / chin
    low_c=(0.0, 14.0, 3.0), low_r=(12.0, 11.2, 12.8),
    ramus_top=(12.0, 3.0, -6.0), jaw_angle=(11.4, 15.6, -4.2), jaw_r=(2.6, 3.0, 3.0),
    chin_pt=(4.2, 23.6, 10.2),
    chin_c=(0.0, 22.2, 12.2), chin_h=(4.8, 3.3, 3.4), chin_rad=2.6,
    jaw_hinge=(0.0, 3.0, -5.5),
    # ears
    ear_c=(15.5, 3.0, -5.6), ear_r=(1.7, 6.1, 3.6), ear_yaw=18.0,
    # neck
    neck_top=(0.0, 8.0, -3.5), neck_bot=(0.0, 44.0, 1.0), neck_r=(8.0, 9.4),
    adams_apple=True, scm=True,
    # lumps added by the cast (list of (kind, args))
    extra=(),
    jaw_extra=(),
)


def head_params(**over):
    hp = dict(DEFAULT_HEAD)
    hp.update(over)
    return hp


def _mirror(p):
    return (-p[0], p[1], p[2])


def _pair(c):
    return [c, _mirror(c)]


def build_head(hp: dict, M: Mats, jaw_open=0.0):
    """Returns (node in head-local coordinates, landmarks dict in head-local coordinates)."""
    skin, lip, neck = M('skin'), M('lip'), M('neck')
    ear_m = M('ear')
    E = S.Ellipsoid
    cran = E(hp['skull_c'], hp['skull_r'], skin)
    fore = S.RoundBox(hp['fore_c'], hp['fore_h'], hp['fore_rad'], skin)
    mid = S.RoundBox(hp['mid_c'], hp['mid_h'], hp['mid_rad'], skin)
    cheeks = S.Union([E(c, hp['cheek_r'], skin) for c in _pair(hp['cheek_c'])])
    malar = S.Union([E(c, hp['malar_r'], skin) for c in _pair(hp['malar_c'])])
    brow = E(hp['brow_c'], hp['brow_r'], skin)
    muzzle = E(hp['muzzle_c'], hp['muzzle_r'], skin)
    # jaw group (rotates around the hinge for talking frames)
    rt, ja, cp = hp['ramus_top'], hp['jaw_angle'], hp['chin_pt']
    jr = hp['jaw_r']
    jaw_parts = [
        E(hp['low_c'], hp['low_r'], skin),
        S.RoundCone(rt, ja, jr[0], jr[1], skin), S.RoundCone(_mirror(rt), _mirror(ja), jr[0], jr[1], skin),
        S.RoundCone(ja, cp, jr[1], jr[2], skin), S.RoundCone(_mirror(ja), _mirror(cp), jr[1], jr[2], skin),
        S.RoundBox(hp['chin_c'], hp['chin_h'], hp['chin_rad'], skin),
    ]
    jaw = S.Union(jaw_parts, k=3.2)
    for kind, args in hp.get('jaw_extra', ()):
        if kind == 'ellipsoid':
            c, r, mname, k = args
            jaw = S.Union([jaw, E(c, r, M(mname))], k=k)
    jaw = S.Union([jaw, E(hp['lip_lo'], hp['lip_lo_r'], lip)], k=0.9)
    if jaw_open:
        piv = np.asarray(hp['jaw_hinge'], float)
        R = S.rot(0, jaw_open, 0)   # chin swings down (pitch > 0 = front goes down)
        jaw = S.Xform(S.Xform(jaw, o=-piv), o=piv, R=R)
    face = S.Union([cran, fore, mid], k=[4.0, 3.0])
    face = S.Union([face, cheeks, malar, brow, muzzle], k=[2.6, 3.0, 2.2, 3.0])
    face = S.Union([face, jaw], k=3.0)
    # eye sockets + lids
    ex, ey = hp['eye_x'], hp['eye_y']
    sock = S.Union([E((x, ey - 0.5, hp['socket_z']), hp['socket_r'], skin) for x in (ex, -ex)])
    face = S.Sub(face, sock, k=2.0)
    balls = S.Union([S.Sphere((x, ey + 0.3, hp['eyeball_z']), hp['eyeball_r'], skin) for x in (ex, -ex)])
    face = S.Union([face, balls], k=1.0)
    # nose
    nr, nt = hp['nose_root'], hp['nose_tip']
    nose = S.Union([
        S.RoundCone(nr, nt, hp['nose_r'][0], hp['nose_r'][1], skin),
        S.Sphere(nt, hp['tip_r'], skin),
    ] + [E(c, hp['ala_r'], skin) for c in _pair((hp['ala_x'], hp['ala_y'], hp['ala_z']))], k=1.3)
    face = S.Union([face, nose], k=1.6)
    # upper lip
    face = S.Union([face, E(hp['lip_up'], hp['lip_up_r'], lip)], k=0.9)
    # extras (cast specific lumps: e.g. moustache base, double chin, brow bulge)
    for kind, args in hp.get('extra', ()):
        if kind == 'ellipsoid':
            c, r, mname, k = args
            face = S.Union([face, E(c, r, M(mname))], k=k)
        elif kind == 'sub':
            c, r, k = args
            face = S.Sub(face, E(c, r, skin), k=k)
    # ears
    eyaw = hp['ear_yaw']
    ears = []
    for sgn in (1, -1):
        ec = np.array(hp['ear_c']) * np.array([sgn, 1, 1])
        R = S.rot(sgn * eyaw, 0, sgn * 6)
        outer = E(ec, hp['ear_r'], ear_m, R=R)
        bowl = E(ec + np.array([sgn * 1.5, 0.5, 0.6]), np.array(hp['ear_r']) * np.array([0.9, 0.6, 0.6]),
                 ear_m, R=R)
        ears.append(S.Sub(outer, bowl, k=0.6))
    face = S.Union([face] + ears, k=[1.2, 1.2])
    # neck
    nk = [S.RoundCone(hp['neck_top'], hp['neck_bot'], hp['neck_r'][0], hp['neck_r'][1], neck)]
    if hp.get('scm'):
        for sgn in (1, -1):
            nk.append(S.RoundCone((sgn * 9.6, 8.0, -6.0), (sgn * 1.8, 38.0, 4.6), 2.2, 2.0, neck))
    if hp.get('adams_apple'):
        nk.append(E((0.0, 27.0, 6.4), (1.6, 2.4, 1.8), neck))
    necknode = S.Union(nk, k=2.4)
    root = S.Union([face, necknode], k=1.0)
    return root, landmarks(hp, jaw_open)


def landmarks(hp, jaw_open=0.0):
    ex, ey = hp['eye_x'], hp['eye_y']
    ez = hp['eyeball_z'] + hp['eyeball_r']
    nt = np.array(hp['nose_tip'])
    lu, ll = np.array(hp['lip_up']), np.array(hp['lip_lo'])
    L = {
        'eye_r': (-ex, ey, ez), 'eye_l': (ex, ey, ez),          # character right / left eye
        'brow_r': (-ex - 0.3, ey - 3.8, ez + 1.0), 'brow_l': (ex + 0.3, ey - 3.8, ez + 1.0),
        'nose_tip': tuple(nt + np.array([0, 0.3, hp['tip_r']])),
        'nose_root': hp['nose_root'],
        'nostril_r': (-hp['ala_x'] + 0.7, hp['ala_y'] + 1.1, hp['ala_z'] + 0.9),
        'nostril_l': (hp['ala_x'] - 0.7, hp['ala_y'] + 1.1, hp['ala_z'] + 0.9),
        'mouth_c': (0.0, hp['mouth_y'], lu[2] + hp['lip_up_r'][2] - 0.3),
        'mouth_r': (-hp['lip_up_r'][0] + 0.2, hp['mouth_y'] + 0.4, lu[2] - 0.8),
        'mouth_l': (hp['lip_up_r'][0] - 0.2, hp['mouth_y'] + 0.4, lu[2] - 0.8),
        'lip_lo': tuple(ll + np.array([0, 0.4, hp['lip_lo_r'][2]])),
        'chin': (0.0, hp['chin_c'][1] + hp['chin_h'][1], hp['chin_c'][2] + hp['chin_h'][2] - 1.0),
        'ear_r': tuple(np.array(hp['ear_c']) * np.array([-1, 1, 1]) + np.array([-1.0, 0, 0])),
        'ear_l': tuple(np.array(hp['ear_c']) + np.array([1.0, 0, 0])),
        'cheek_r': (-hp['cheek_c'][0], hp['cheek_c'][1] + 2, hp['cheek_c'][2] + hp['cheek_r'][2]),
        'cheek_l': (hp['cheek_c'][0], hp['cheek_c'][1] + 2, hp['cheek_c'][2] + hp['cheek_r'][2]),
        'forehead': (0.0, -12.0, hp['fore_c'][2] + hp['fore_h'][2]),
        'jaw_r': tuple(np.array(hp['jaw_angle']) * np.array([-1, 1, 1])),
        'jaw_l': tuple(hp['jaw_angle']),
    }
    if jaw_open:
        piv = np.asarray(hp['jaw_hinge'], float)
        R = S.rot(0, jaw_open, 0)
        for k in ('chin', 'jaw_r', 'jaw_l', 'lip_lo'):
            L[k] = tuple(R @ (np.asarray(L[k]) - piv) + piv)
    return L


# ----------------------------------------------------------------------------------------- torso
def build_torso(M: Mats, mat='body', width=1.0, depth=1.0, slope=1.0):
    """Shoulders + chest in a torso-local frame (origin at the pit of the neck, y down)."""
    m = M(mat)
    E = S.Ellipsoid
    w, d = width, depth
    parts = [
        E((0.0, 16.0, -4.0), (29.0 * w, 13.0, 13.0 * d), m),                  # shoulder girdle
        E((0.0, 30.0, 0.0), (25.0 * w, 22.0, 13.5 * d), m),                   # chest
        S.RoundCone((-6.0 * w, 1.0, -5.0), (-25.0 * w, 9.0 + 4 * slope, -4.0), 5.5, 8.0, m),   # trapezius
        S.RoundCone((6.0 * w, 1.0, -5.0), (25.0 * w, 9.0 + 4 * slope, -4.0), 5.5, 8.0, m),
        E((-26.0 * w, 20.0, -3.0), (9.0, 12.0, 9.5 * d), m),                  # deltoids
        E((26.0 * w, 20.0, -3.0), (9.0, 12.0, 9.5 * d), m),
    ]
    return S.Union(parts, k=5.0)
