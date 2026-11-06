"""env_c4_cine_anat -- anatomy kit of the Chapter-4 cinematic figures (owner: c4 figure stream, round 10).

Built on the signed-distance pipeline of the dialogue portraits (chargen_portrait2_sdf: nodes + sphere tracer,
chargen_portrait2_paint: light value, ramps, outlines, rims; imported read-only, nothing there is changed).
Replaces the round-9 paddle hands (one flattened ellipsoid + sausages) with an articulated hand and a sleeved arm:

  hand(M, mat, s, side, flex, spread, thumb, glove)
        palm = metacarpal block + heel + thenar / hypothenar pads + an arched row of knuckles; four fingers of three
        phalanges each (index 0.80 s, middle 0.89 s, ring 0.83 s, little 0.66 s, s = palm length) bending at MCP /
        PIP / DIP; a thumb of metacarpal + two phalanges with its own flexion plane (abduction, opposition);
        fingernails on bare hands (large scales), knuckle and tendon relief on the back of the hand; gloves are a
        little fuller and have no nails (seams come from pass_glove()).
  arm(M, sleeve, skin, shoulder, elbow, wrist, radii, hand_y, hand_z, s, ...)
        shoulder -> upper arm -> elbow (olecranon point, folds in the crook) -> forearm -> an OPEN sleeve end (the
        hollow is painted with its own dark material) -> optional shirt cuff / sleeve protector -> wrist -> hand.
  paint(nodes, M, size, look, styles, ...)
        trace + paint like env_c3p2_cine_hands.paint, plus: a depth range for macro scales, and `shadow` = a plane
        (desk, card, counter) that receives the figure's soft cast shadow -- returned as dithered dark pixels with
        partial alpha around the figure, so a hand lies ON the paper instead of floating over it.

Every arm in the Chapter-4 films starts at a shoulder outside the visible frame (or at a body), so no sleeve ends in
mid-air.  Deterministic numpy; renders are memoised on disk (key = the pipeline sources + this file + env_c4_cine_figs
+ the call), ASHES_NO_CACHE=1 disables the cache.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_paint as P  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
F32 = np.float32
_memo: dict = {}


def _src_key():
    h = hashlib.sha1()
    for f in ('chargen_portrait2_anat.py', 'chargen_portrait2_cast.py', 'chargen_portrait2_paint.py',
              'chargen_portrait2_sdf.py', 'chargen_portrait2.py', 'env_c4_cine_anat.py'):
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()[:16]


# ----------------------------------------------------------------------------------------------- vectors
def nrm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def rot(v, axis, deg):
    """Rotate v about `axis` by `deg` degrees (right hand rule, Rodrigues)."""
    v = np.asarray(v, float)
    k = nrm(axis)
    a = math.radians(deg)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * float(np.dot(k, v)) * (1.0 - math.cos(a))


def frame_along(o, y_axis, z_hint):
    """Frame at o: local +y along y_axis, local +z as close as possible to z_hint, x = y cross z."""
    ey = nrm(y_axis)
    zh = np.asarray(z_hint, float)
    ez = nrm(zh - ey * float(np.dot(zh, ey)))
    ex = np.cross(ey, ez)
    return S.Frame(o, np.stack([ex, ey, ez], axis=1))


def basis(ax, ay, az):
    """Rotation matrix whose columns are the given local axes (Ellipsoid / RoundBox orientation)."""
    return np.stack([nrm(ax), nrm(ay), nrm(az)], axis=1)


def ortho(y, z_hint=(0.0, 0.0, 1.0)):
    """Orthonormal basis (columns x, y, z) with y along `y` and z as close as possible to z_hint."""
    ey = nrm(y)
    zh = np.asarray(z_hint, float)
    if abs(float(np.dot(nrm(zh), ey))) > 0.98:
        zh = np.array([1.0, 0.0, 0.0])
    ez = nrm(zh - ey * float(np.dot(zh, ey)))
    return np.stack([np.cross(ey, ez), ey, ez], axis=1)


def bounded(node, pts, pad):
    pts = np.asarray(pts, float)
    c = (pts.max(0) + pts.min(0)) / 2.0
    r = float(np.sqrt(((pts - c) ** 2).sum(1)).max()) + pad
    return S.Bound(node, c, r, margin=3.0)


# ----------------------------------------------------------------------------------------------- the hand
#            name      x (thumb side +)  MCP y   length  radius   (units of s = palm length, wrist -> knuckles)
FINGERS = (('index', 0.290, 0.930, 0.80, 0.100),
           ('middle', 0.098, 0.972, 0.89, 0.104),
           ('ring', -0.098, 0.948, 0.83, 0.097),
           ('little', -0.282, 0.862, 0.66, 0.085))
SEG = (0.47, 0.29, 0.24)            # proximal, middle, distal phalanx (share of the finger length)
POSES = {
    # (MCP, PIP, DIP) flexion per finger (index, middle, ring, little), degrees towards the palm
    'flat': ((4, 6, 4), (4, 6, 4), (5, 7, 5), (8, 9, 6)),
    'relaxed': ((16, 26, 12), (20, 30, 14), (24, 34, 16), (30, 38, 18)),
    'rest': ((10, 16, 8), (12, 18, 9), (16, 22, 10), (20, 26, 12)),
    'curl': ((38, 60, 30), (44, 66, 34), (50, 70, 36), (56, 74, 38)),
    'fist': ((82, 98, 62), (86, 100, 64), (88, 100, 64), (90, 98, 60)),
    'grip': ((62, 84, 46), (68, 88, 50), (72, 90, 52), (76, 90, 52)),
    'pinch': ((40, 46, 20), (52, 76, 40), (60, 84, 46), (66, 86, 48)),
    'pen': ((30, 32, 16), (44, 62, 34), (62, 88, 50), (70, 92, 52)),
    'point': ((4, 8, 4), (70, 96, 60), (76, 98, 60), (80, 96, 58)),
    'press': ((-4, 4, 2), (2, 10, 6), (8, 14, 8), (14, 20, 10)),
}
THUMBS = {
    # abduction (deg from the index line in the palm plane), opposition (deg towards the palm side), MCP, IP
    'rest': dict(abd=38.0, opp=28.0, mcp=12.0, ip=14.0),
    'out': dict(abd=58.0, opp=10.0, mcp=4.0, ip=6.0),
    'along': dict(abd=22.0, opp=8.0, mcp=6.0, ip=4.0),
    'tuck': dict(abd=24.0, opp=52.0, mcp=34.0, ip=30.0),
    'pinch': dict(abd=30.0, opp=50.0, mcp=20.0, ip=16.0),
    'wrap': dict(abd=20.0, opp=62.0, mcp=40.0, ip=40.0),
    'press': dict(abd=52.0, opp=22.0, mcp=0.0, ip=-8.0),
}


def _pose(p, default):
    if p is None:
        return POSES[default]
    if isinstance(p, str):
        return POSES[p]
    return p


def _thumb(t):
    if t is None:
        return dict(THUMBS['rest'])
    if isinstance(t, str):
        return dict(THUMBS[t])
    out = dict(THUMBS['rest'])
    out.update(t)
    return out


def finger_chain(i, s, side, flex, spread):
    """Joint positions [MCP, PIP, DIP, tip], radii and the hinge axis of finger i (0 index .. 3 little)."""
    _n, fx, fy, L, R = FINGERS[i]
    p0 = np.array([fx * side * s, fy * s, 0.0])
    a = spread * (1.5 - i) * 0.5                       # index fans towards the thumb, the little finger away
    d0 = rot((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), -a * side)
    lat = nrm(np.cross(d0, (0.0, 0.0, 1.0)))           # hinge axis (flexion bends towards -z, the palm)
    f = flex[i]
    d1 = rot(d0, lat, -f[0])
    d2 = rot(d1, lat, -f[1])
    d3 = rot(d2, lat, -f[2])
    L = L * s
    j1 = p0 + d1 * L * SEG[0]
    j2 = j1 + d2 * L * SEG[1]
    j3 = j2 + d3 * L * SEG[2]
    r = R * s
    return [p0, j1, j2, j3], [r, r * 0.93, r * 0.86, r * 0.74], lat, d3


def thumb_chain(s, side, t):
    """Thumb joints [CMC, MCP, IP, tip], radii, hinge axis, distal direction."""
    c0 = np.array([0.235 * side * s, 0.15 * s, -0.05 * s])
    abd, opp = math.radians(t['abd']), math.radians(t['opp'])
    dm = nrm((math.sin(abd) * math.cos(opp) * side, math.cos(abd) * math.cos(opp), -math.sin(opp)))
    bend = nrm((-side * 0.75, 0.25, -0.6))              # thumb flexion: towards the middle of the palm
    ax = np.cross(dm, bend)
    if np.linalg.norm(ax) < 1e-6:
        ax = np.array([0.0, 0.0, 1.0])
    ax = nrm(ax)
    c1 = c0 + dm * 0.44 * s
    d1 = rot(dm, ax, t['mcp'])
    c2 = c1 + d1 * 0.34 * s
    d2 = rot(d1, ax, t['ip'])
    c3 = c2 + d2 * 0.28 * s
    return [c0, c1, c2, c3], [0.150 * s, 0.128 * s, 0.116 * s, 0.098 * s], ax, d2


def hand(M, mat, s, side=1.0, flex=None, spread=4.0, thumb=None, glove=False, nail=None,
         parts=('palm', 'fingers', 'thumb'), relief=True):
    """An articulated hand in its own frame: origin at the wrist joint, +y towards the knuckles / fingers, +z the
    back of the hand, the thumb on +x when side = +1 (mirror with side = -1).  s = palm length (wrist ->
    knuckles).  flex = POSES name or ((MCP, PIP, DIP) x 4 fingers, index first); spread = degrees between
    neighbouring fingers; thumb = THUMBS name or dict(abd, opp, mcp, ip); glove = fuller shapes, no nails;
    nail = nail material (bare hands at s >= 24 px); parts selects palm / fingers / thumb (layer splits)."""
    m = M(mat)
    fl = _pose(flex, 'relaxed')
    tp = _thumb(thumb)
    g = 1.12 if glove else 1.0
    palm = []
    # metacarpal block (the back of the hand level with the backs of the fingers), heel, pads on both sides
    palm += [E((0.0, 0.56 * s, -0.012 * s), (0.42 * s * g, 0.40 * s, 0.112 * s * g), m),
             E((0.0, 0.40 * s, -0.045 * s), (0.36 * s * g, 0.34 * s, 0.12 * s * g), m),
             E((0.0, 0.15 * s, -0.02 * s), (0.30 * s * g, 0.20 * s, 0.15 * s * g), m),
             E((0.215 * side * s, 0.28 * s, -0.08 * s), (0.17 * s * g, 0.23 * s, 0.125 * s * g), m),
             E((-0.27 * side * s, 0.44 * s, -0.06 * s), (0.12 * s * g, 0.30 * s, 0.10 * s * g), m)]
    # the arched row of knuckles (heads of the metacarpals), a little proud of the back of the hand
    for i in range(4):
        _n, fx, fy, _L, R = FINGERS[i]
        palm.append(S.Sphere((fx * side * s, (fy - 0.03) * s, 0.018 * s), R * s * 1.04 * g, m))
        if relief and not glove and s >= 30:
            palm.append(RC((fx * side * s * 0.45, 0.24 * s, 0.07 * s), (fx * side * s, (fy - 0.12) * s, 0.07 * s),
                           0.028 * s, 0.032 * s, m))
    curl = sum(f[1] for f in fl) / 4.0
    if curl > 55.0:
        # a closed hand: the fleshy pads of the curled fingers fill the hollow of the palm (no see-through loop)
        q = min(1.0, (curl - 55.0) / 35.0)
        palm.append(E((0.0, 0.80 * s, -0.17 * s - 0.10 * s * q), (0.40 * s * g, 0.20 * s + 0.06 * s * q,
                                                                  0.13 * s + 0.07 * s * q), m))
    core = S.Union(palm, k=0.10 * s)
    out = [core] if 'palm' in parts else []
    extra = []
    # every digit is blended into the palm on its own and joined to its neighbours with a hard union: separate
    # fingers with a crease between them instead of a webbed paddle
    if 'fingers' in parts:
        for i in range(4):
            pts, rr, lat, dd = finger_chain(i, s, side, fl, spread)
            rr = [r * g for r in rr]
            fing = S.Union([RC(tuple(pts[0]), tuple(pts[1]), rr[0], rr[1], m),
                            RC(tuple(pts[1]), tuple(pts[2]), rr[1], rr[2], m),
                            RC(tuple(pts[2]), tuple(pts[3]), rr[2], rr[3], m)], k=0.03 * s)
            out.append(S.Union([core, fing], k=0.07 * s) if 'palm' in parts else fing)
            if nail is not None and not glove:
                nd = nrm(np.cross(lat, dd))
                L3 = FINGERS[i][3] * s * SEG[2]
                c = pts[3] - dd * (L3 * 0.30) + nd * (rr[3] * 0.62)
                extra.append(E(tuple(c), (rr[3] * 0.80, L3 * 0.40, rr[3] * 0.30), M(nail), R=basis(lat, dd, nd)))
    if 'thumb' in parts:
        pts, rr, ax, dd = thumb_chain(s, side, tp)
        rr = [r * g for r in rr]
        th = S.Union([RC(tuple(pts[0]), tuple(pts[1]), rr[0], rr[1], m),
                      RC(tuple(pts[1]), tuple(pts[2]), rr[1], rr[2], m),
                      RC(tuple(pts[2]), tuple(pts[3]), rr[2], rr[3], m)], k=0.04 * s)
        out.append(S.Union([core, th], k=0.10 * s) if 'palm' in parts else th)
        if nail is not None and not glove:
            nd = nrm(np.cross(dd, ax)) * (1.0 if side > 0 else -1.0)
            nd = nd if nd[2] > -0.2 else -nd
            c = pts[3] - dd * (0.28 * s * 0.30) + nd * (rr[3] * 0.62)
            extra.append(E(tuple(c), (rr[3] * 0.80, 0.28 * s * 0.42, rr[3] * 0.30), M(nail),
                           R=basis(np.cross(dd, nd), dd, nd)))
    return S.Union(out + extra, k=0.0)


def hand_points(s, side=1.0, flex=None, spread=4.0, thumb=None):
    """Hand-local key points: fingertips (index..little), the thumb tip and the knuckle row (placement helpers)."""
    fl = _pose(flex, 'relaxed')
    tips = [finger_chain(i, s, side, fl, spread)[0][3] for i in range(4)]
    th = thumb_chain(s, side, _thumb(thumb))[0][3]
    return dict(tips=tips, thumb=th, knuckles=[np.array([f[1] * side * s, f[2] * s, 0.0]) for f in FINGERS])


def to_view(frame, p):
    return frame.to_view(np.asarray(p, float))


# ----------------------------------------------------------------------------------------------- the arm
def arm(M, sleeve, skin, shoulder, elbow, wrist, r, hand_y, hand_z, s, cuff=None, cuff_len=0.0, cover=0.30,
        folds=True, sleeve_in=None, wrist_mat=None, hand_mat=None, hand_kw=None, bulk=1.0, cuff_r=None,
        sleeve_fx=None):
    """Sleeve from the shoulder over the elbow to an open end `cover`*s before the wrist joint, an optional cuff
    (shirt cuff, sleeve protector, glove gauntlet: `cuff` material, `cuff_len` px along the forearm, it starts
    inside the sleeve), the bare wrist and hand().  r = (shoulder, elbow, sleeve end) radii.  hand_y / hand_z
    orient the hand (finger direction / back of the hand).  sleeve_in = material of the sleeve's dark inside.
    cuff_r = (start, end) radii of the cuff (default: 0.74 / 0.70 of the sleeve end -- a slim sleeve passes
    its own, a little wider than the wrist).  sleeve_fx(node) -> node reshapes the sleeve alone (quilting) before
    its open end is cut -- never the cuff, wrist or hand."""
    shoulder, elbow, wrist = (np.asarray(p, float) for p in (shoulder, elbow, wrist))
    udir = nrm(elbow - shoulder)
    fdir = nrm(wrist - elbow)
    end = wrist - fdir * cover * s
    ms = M(sleeve)
    r0, r1, r2 = r
    tube = [RC(tuple(shoulder), tuple(elbow), r0, r1, ms), RC(tuple(elbow), tuple(end), r1, r2, ms)]
    out_e = udir - fdir
    if np.linalg.norm(out_e) > 0.2:
        out_e = nrm(out_e)
        # the point of the elbow and the cloth gathered in its crook
        tube.append(S.Sphere(tuple(elbow + out_e * r1 * 0.30), r1 * 0.80, ms))
        if folds:
            inn = -out_e
            for k, a in enumerate((0.9, 1.7)):
                c = elbow + fdir * r1 * a + inn * r1 * 0.55
                tube.append(E(tuple(c), (r1 * 0.62, r1 * 0.20 * (1.0 - 0.2 * k), r1 * 0.62), ms, R=ortho(fdir, inn)))
            for a in (0.8, 1.6):
                c = elbow - udir * r1 * a + inn * r1 * 0.5
                tube.append(E(tuple(c), (r1 * 0.55, r1 * 0.18, r1 * 0.55), ms, R=ortho(udir, inn)))
    if folds:
        # a soft ring of gathered cloth a little above the sleeve end
        c = end - fdir * r2 * 1.1
        tube.append(E(tuple(c), (r2 * 1.06, r2 * 0.32, r2 * 1.06), ms, R=ortho(fdir)))
    sl = S.Union(tube, k=r1 * 0.35)
    if sleeve_fx is not None:
        sl = sleeve_fx(sl)
    # the open sleeve end: a hollow, painted with the sleeve's dark inside
    hollow = RC(tuple(end - fdir * r2 * 1.3), tuple(end + fdir * r2 * 3.0), r2 * 0.80 * bulk, r2 * 0.80 * bulk, ms)
    sl = S.Sub(sl, hollow, k=0.0, cut_mat=M(sleeve_in or sleeve))
    cap = S.Inter(sl, S.Fn(lambda P_, e=end.astype(F32), d=fdir.astype(F32): ((P_ - e) @ d), ms))
    nodes = [cap]
    wm = M(wrist_mat or skin)
    if cuff is not None and cuff_len > 0:
        c0 = end - fdir * r2 * 0.9
        c1 = end + fdir * cuff_len
        ca, cb = cuff_r if cuff_r is not None else (r2 * 0.74, r2 * 0.70)
        nodes.append(RC(tuple(c0), tuple(c1), ca, cb, M(cuff)))
    nodes.append(RC(tuple(end - fdir * r2 * 1.0), tuple(wrist + fdir * 0.10 * s), 0.27 * s, 0.30 * s, wm))
    hk = dict(hand_kw or {})
    nodes.append(S.Xform(hand(M, hand_mat or skin, s, **hk), frame=frame_along(wrist, hand_y, hand_z)))
    pts = [shoulder, elbow, wrist, wrist + nrm(hand_y) * 1.9 * s]
    ks = [0.0] * (len(nodes) - 2) + [0.07 * s]
    return bounded(S.Union(nodes, k=ks), pts, max(r) + s * 1.0)


def hand_at(M, mat, wrist, hand_y, hand_z, s, **kw):
    """A hand placed at a wrist point (no arm), oriented by hand_y / hand_z."""
    node = S.Xform(hand(M, mat, s, **kw), frame=frame_along(wrist, hand_y, hand_z))
    return bounded(node, [np.asarray(wrist, float), np.asarray(wrist, float) + nrm(hand_y) * 1.9 * s], s * 1.1)


def reach(elbow, target, local, up, flexion=0.0, deviation=0.0, side=1.0, iters=8):
    """The hand at the end of a forearm from `elbow`: returns (wrist, hand_y, hand_z) such that the hand-local
    point `local` lies on `target`, the hand CONTINUES the forearm (bent at the wrist by `flexion` degrees towards
    the palm, negative = extended, and `deviation` degrees towards the little finger) and the back of the hand is
    turned as close to `up` as the forearm allows.  No hand hangs off a forearm at a right angle any more."""
    elbow = np.asarray(elbow, float)
    target = np.asarray(target, float)
    local = np.asarray(local, float)
    up = nrm(up)
    w = target.copy()
    hy = hz = None
    for _ in range(iters):
        fd = nrm(w - elbow)
        hz0 = up - fd * float(np.dot(up, fd))
        if np.linalg.norm(hz0) < 1e-6:
            hz0 = np.array([0.0, 0.0, 1.0]) - fd * float(fd[2])
        hz0 = nrm(hz0)
        ax = nrm(np.cross(fd, hz0))
        hy = rot(fd, ax, -flexion)
        hz = rot(hz0, ax, -flexion)
        if deviation:
            hy = rot(hy, hz, deviation * (1.0 if side >= 0 else -1.0))
        w = target - frame_along((0.0, 0.0, 0.0), hy, hz).to_view(local)
    return w, hy, hz


def cloth_tube(M, mat, a, b, r_a, r_b, puff=0.10, gather=0.80, folds=7, fold_amp=0.07, seed=0, hem=True):
    """A loose cloth tube from a to b (a sleeve protector, a loose sleeve): radius r_a -> r_b, puffed between the
    ends, drawn in by elastic at both ends (end radius * gather) with soft radial folds that fade towards the
    middle and a narrow hem ridge.  Never a ball or a hemisphere at its end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = nrm(b - a)
    L = float(np.linalg.norm(b - a))
    m = M(mat)
    ts = (0.0, 0.10, 0.50, 0.90, 1.0)
    rm = (r_a + r_b) * 0.5
    rs = (r_a * gather, r_a * (1.0 + puff * 0.7), rm * (1.0 + puff), r_b * (1.0 + puff * 0.7), r_b * gather)
    pts = [a + d * L * t for t in ts]
    segs = [RC(tuple(pts[i]), tuple(pts[i + 1]), rs[i], rs[i + 1], m) for i in range(4)]
    tube = S.Union(segs, k=min(r_a, r_b) * 0.35)
    if hem:
        # the elastic: a soft rounded ridge just inside each end (thick enough that the folds never fray it)
        for p, r in ((pts[0] + d * 2.6, rs[0] * 1.04), (pts[-1] - d * 2.6, rs[-1] * 1.04)):
            tube = S.Union([tube, E(tuple(p), (r, max(2.4, 0.14 * r), r), m, R=ortho(d))], k=1.6)
    e1 = nrm(np.cross(d, (0.0, 0.0, 1.0)) if abs(d[2]) < 0.9 else np.cross(d, (1.0, 0.0, 0.0)))
    e2 = np.cross(d, e1)
    a32, d32, e132, e232 = (v.astype(F32) for v in (a, d, e1, e2))
    ph = (seed % 7) * 0.7

    def fn(P):
        # longitudinal ridges of the gathered cloth: strongest beside the elastic, fading to the middle and
        # dying out ON the very ends (no petals at the hem)
        Q = P - a32
        t = np.clip((Q @ d32) / F32(L), 0.0, 1.0)
        ang = np.arctan2(Q @ e232, Q @ e132)
        e = np.minimum(t, 1.0 - t)
        env = np.clip(1.0 - np.abs(e - 0.10) / 0.16, 0.0, 1.0) * np.clip(e / 0.04, 0.0, 1.0)
        wav = np.sin(ang * folds + ph + t * 2.3) * (0.25 + 0.75 * env)
        return wav.astype(F32)
    return S.Displace(tube, fn, amp=fold_amp * rm, lipschitz=1.25)


def quilt_on(node, a, d, period=6.0, amp=0.8):
    """Padded quilting across a limb: channels round the axis (a, d) that bulge between the stitch lines."""
    a32 = np.asarray(a, F32)
    d32 = nrm(d).astype(F32)

    def fn(P):
        u = ((P - a32) @ d32) / F32(period)
        return (np.abs(np.sin(np.pi * u)) * 2.0 - 1.0).astype(F32)
    return S.Displace(node, fn, amp=amp, lipschitz=1.25)


def pass_contact(pairs, dark=(2, 1)):
    """Contact creases between two materials that touch (a sleeve against the coat's side, an arm against the
    trunk): the pixels of `a` next to `b` go dark[0] tones darker, the pixels of `b` next to `a` dark[1] tones.
    pairs = ((a, b), ...) material names.  Separates parts of one colour that a depth line misses."""
    def fn(spec, G, tone, v):
        M = G['M']
        d = G['d']
        out = tone.copy()
        h, w = tone.shape
        for a, b in pairs:
            if a not in M.names or b not in M.names:
                continue
            ia, ib = M.names.index(a), M.names.index(b)
            ma, mb = (d.mat == ia) & d.hit, (d.mat == ib) & d.hit
            na = np.zeros((h, w), bool)
            nb = np.zeros((h, w), bool)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sa = np.roll(np.roll(ma, dy, 0), dx, 1)
                sb = np.roll(np.roll(mb, dy, 0), dx, 1)
                nb |= sa
                na |= sb
            sel_a = ma & na
            sel_b = mb & nb
            out = np.where(sel_a & (out >= 1), np.maximum(out - dark[0], 0), out)
            out = np.where(sel_b & (out >= 1), np.maximum(out - dark[1], 0), out)
        return out.astype(tone.dtype)
    return fn


# ----------------------------------------------------------------------------------------------- painting
def _cache_path(tag):
    d = os.path.join(tempfile.gettempdir(), 'ashes_c4fig_cache')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, tag + '.npz')


def unbound(node):
    """The same scene without its Bound short-cuts (exact distances far from the figure: the shadow march)."""
    if isinstance(node, S.Bound):
        return unbound(node.child)
    if isinstance(node, S.Union):
        u = S.Union([unbound(c) for c in node.ch], k=node.k)
        return u
    if isinstance(node, S.Xform):
        x = S.Xform(unbound(node.child))
        x.o, x.R = node.o, node.R
        return x
    if isinstance(node, (S.Sub, S.Inter)):
        c = S.Sub.__new__(type(node))
        c.__dict__.update(node.__dict__)
        c.a, c.b = unbound(node.a), unbound(node.b)
        return c
    if isinstance(node, (S.Scale, S.Displace, S.Warp, S.Offset, S.Shell, S.Mat)):
        c = type(node).__new__(type(node))
        c.__dict__.update(node.__dict__)
        c.child = unbound(node.child)
        return c
    return node


def plane_shadow(root, w, h, p0, n, key, k=0.035, steps=64, tmax=260.0):
    """Key-light visibility (0 = shadowed .. 1) on a plane (point p0, normal n towards the viewer) at every pixel
    centre, marched through the figure's distance field.  The penumbra widens with the distance to the occluder
    (0.6 px + k * t) -- narrow enough that the bounding-sphere short-cuts of the scene never cast false shade."""
    ys, xs = np.mgrid[0:h, 0:w]
    x = (xs + 0.5).astype(F32).ravel()
    y = (ys + 0.5).astype(F32).ravel()
    n = nrm(n)
    z = F32(p0[2]) - (F32(n[0]) * (x - F32(p0[0])) + F32(n[1]) * (y - F32(p0[1]))) / F32(n[2])
    Pp = np.stack([x, y, z], 1).astype(F32) + F32(0.6) * n.astype(F32)[None]
    L = nrm(key).astype(F32)
    root = unbound(root)
    N = Pp.shape[0]
    vis = np.ones(N, F32)
    t = np.full(N, F32(1.0))
    act = np.ones(N, bool)
    ar = np.arange(N)
    for _ in range(steps):
        a = ar[act]
        if a.size == 0:
            break
        Q = Pp[a] + L[None] * t[a, None]
        d, _m = root.eval(Q)
        vis[a] = np.minimum(vis[a], np.clip(d / (F32(0.6) + F32(k) * t[a]), 0, 1))
        t[a] += np.clip(d, 0.4, 8.0)
        act[a[(d < 0.02) | (t[a] > tmax)]] = False
    return vis.reshape(h, w)


def shadow_layer(vis, hit, rgb, levels=((0.18, 0.46), (0.45, 0.30), (0.75, 0.15)), seed=0):
    """Visibility -> RGBA of the cast shadow outside the figure: stepped alpha (core / penumbra), ordered dither on
    the step borders, one colour."""
    h, w = vis.shape
    occ = 1.0 - vis
    bay = P.bayer(h, w, seed % 4, (seed // 4) % 4)
    out = np.zeros((h, w, 4), np.uint8)
    a = np.zeros((h, w), np.float32)
    for vmax, alpha in sorted(levels, key=lambda q: -q[0]):
        sel = (vis < vmax + (bay - 0.5) * 0.10)
        a = np.where(sel, alpha, a)
    a = np.where(occ < 0.06, 0.0, a)
    a[hit] = 0.0
    out[..., :3] = np.asarray(rgb, np.uint8)[None, None]
    out[..., 3] = (a * 255).astype(np.uint8)
    return out


def crease_lines(d, tone, v, cos_th=0.55, zgap=2.2):
    """One tone darker on the darker side of a sharp fold inside one material (between two fingers, under a
    cuff, the folds of a sleeve) and two tones on the far side of a depth step (a finger in front of another):
    the inner drawing that the silhouette outline alone does not give."""
    h, w = tone.shape
    n = d.n
    z = np.where(d.hit, d.z, -1e9)
    mat = d.mat
    fold = np.zeros((h, w), bool)
    step = np.zeros((h, w), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ys = slice(max(0, dy), h + min(0, dy))
        xs = slice(max(0, dx), w + min(0, dx))
        yd = slice(max(0, -dy), h + min(0, -dy))
        xd = slice(max(0, -dx), w + min(0, -dx))
        same = (mat[yd, xd] == mat[ys, xs]) & d.hit[yd, xd] & d.hit[ys, xs]
        dot = (n[yd, xd] * n[ys, xs]).sum(-1)
        darker = v[yd, xd] <= v[ys, xs]
        fold[yd, xd] |= same & (dot < cos_th) & darker
        step[yd, xd] |= same & (z[ys, xs] - z[yd, xd] > zgap)
    out = tone.copy()
    out = np.where(fold & (out >= 1), out - 1, out)
    out = np.where(step & (out >= 1), np.maximum(out - 2, 0), out)
    return out.astype(tone.dtype)


def paint(nodes, M, size, look, styles, groups=None, tone_passes=(), frames=None, ss=3, outline=True, rim=True,
          cache=None, z_range=(90.0, -90.0), steps=110, shadow=None, glow=None, k=1.0, post=None, creases=True):
    """Trace + paint the union of `nodes` (view space = canvas px, y down, z towards the viewer) -> RGBA uint8.
    shadow = dict(p=point, n=normal, rgb=colour, levels=..., clip=bool mask or None): the plane's cast shadow is
    composited under the figure as partial-alpha pixels.  glow = (centre, radius, floor) local key falloff."""
    key = None
    if cache is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        hk = hashlib.sha1((_src_key() + repr((cache, size, look, ss, outline, rim, z_range, steps,
                                               None if shadow is None else {kk: (vv if kk not in ('clip', 'nodes')
                                                                                 else None)
                                                                             for kk, vv in shadow.items()},
                                               glow, k, creases))).encode('utf-8')).hexdigest()[:22]
        key = _cache_path('c4f_' + hk)
        if key in _memo:
            return _memo[key].copy()
        if os.path.exists(key):
            out = np.load(key)['rgba']
            _memo[key] = out
            return out.copy()
    root = S.Union(list(nodes), k=k) if isinstance(nodes, (list, tuple)) else nodes
    w, h = size
    lk = P.Look(**look)
    g = S.trace(root, w, h, ss=ss, key=lk.key, z0=z_range[0], zfar=z_range[1], steps=steps)
    d = S.downsample(g, len(M))
    names = M.names
    G = dict(d=d, M=M, look=lk, zoom=1.0)
    for kk, fr in (frames or {}).items():
        G[kk] = fr
    v, rimv, keyv = P.light_value(d, lk, styles, names)
    if glow is not None:
        c, r, floor = glow
        dist = np.linalg.norm(d.P - np.asarray(c, np.float32)[None, None, :], axis=2)
        fall = np.clip(1.0 - dist / r, 0.0, 1.0) ** 1.3
        v = v * (floor + (1.0 - floor) * fall).astype(np.float32)
        keyv = keyv * fall.astype(np.float32)
    v = P.smooth_by_material(v, d.mat, passes=1)
    tone = P.quantise(d, v, styles, names)
    for fn in tone_passes:
        tone = fn({}, G, tone, v)
    if creases:
        tone = crease_lines(d, tone, v)
    tone = P.clean(tone, d.mat)
    rgb = P.colorize(d, tone, styles, names)
    if outline:
        rgb = P.outline(rgb, d, styles, names, look=lk)
        rgb, _ = P.depth_lines(rgb, d, styles, names, groups or {})
    if rim:
        rgb = P.apply_rim(rgb, d, rimv, keyv, styles, names, tone)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    if post is not None:
        out = post(out, d, M)
    if shadow is not None:
        caster = shadow.get('nodes')
        caster = root if caster is None else S.Union(list(caster), k=0.0)
        vis = plane_shadow(caster, w, h, shadow['p'], shadow['n'], lk.key, k=shadow.get('k', 0.035))
        lay = shadow_layer(vis, out[..., 3] > 0, shadow.get('rgb', (0, 0, 0)),
                           levels=shadow.get('levels', ((0.18, 0.46), (0.45, 0.30), (0.75, 0.15))),
                           seed=shadow.get('seed', 0))
        if shadow.get('clip') is not None:
            lay[~shadow['clip'], 3] = 0
        empty = out[..., 3] == 0
        out[empty] = lay[empty]
    if key is not None:
        np.savez(key, rgba=out)
        _memo[key] = out
    return out.copy()


def split(full, part):
    """(layer of `full` covered by the separately rendered `part`, the rest): a thumb in front of a card."""
    m = part[..., 3] > 0
    a = full.copy()
    a[~m, 3] = 0
    b = full.copy()
    b[m, 3] = 0
    return a, b


# ----------------------------------------------------------------------------------------------- tone passes
def pass_glove(mat='glove', period=0.0, seam_frames=()):
    """Leather glove: a darker stitched line along the back of the hand (frame 'hf': hand-local) and a slight
    sheen break on the knuckles (one tone up where the surface faces the key strongly)."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        d = G['d']
        m = (d.mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        tone = tone.copy()
        for fk in seam_frames:
            fr = G.get(fk)
            if fr is None:
                continue
            Pm = d.P[m]
            L = (Pm - fr.o) @ fr.R
            s_ = G.get(fk + '_s', 30.0)
            line = np.zeros(L.shape[0], bool)
            for xx in (-0.18, 0.0, 0.18):
                line |= (np.abs(L[:, 0] - xx * s_) < 0.55) & (L[:, 1] > 0.35 * s_) & (L[:, 1] < 0.85 * s_) & \
                        (L[:, 2] > 0.05 * s_)
            t = tone[m]
            t = np.where(line & (t >= 2), t - 1, t)
            tone[m] = t
        return tone
    return fn
