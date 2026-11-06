"""env_veltrava_cine_rig -- articulated figure rig for the Chapter-3 part-1 cinematics (LS_C3_Trains,
LS_C3_ToHall, LS_C3_Close).  Owner: the figures stream of this film family (round 10).

Why: the round-7 figures were busts with arms glued on as two capsules each (forearms hidden behind the back)
and a hand painted separately into the room, so arms read as stumps growing out of the chest.  This rig builds
every arm as one continuous chain -- shoulder -> upper arm -> elbow -> forearm -> wrist -> hand -- with the
sleeve, its elbow folds, the shirt cuff and a hand made of a palm, knuckles, three phalanges per finger and a
two-joint thumb, all in the signed-distance pipeline of the dialogue portraits (chargen_portrait2_sdf/paint,
imported read-only) so hands carry the same light, ramps and outlines as the faces.

Limbs are modelled in VIEW space (pixels of the figure image, x right, y down, z toward the camera).  Arms that
reach away from the camera (to a cup on the table by the window) taper with distance -- radii and the hand scale
are given per joint -- which fakes the perspective of the room inside the orthographic tracer.

  hand(M, mat, s, side, ...)          hand in its local frame (origin = wrist, +y = knuckles, +z = back of hand)
  sleeve_arm(M, ...)                  sleeve chain with elbow folds + cuff + wrist + hand, returns (node, points)
  render(root, M, size, ...)          trace + paint with point lights (lamp, tea glass, chandelier), disk cache
  frame_along(o, y_axis, z_hint)      helper frame

Everything is deterministic numpy; no image inputs.
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
import chargen_portrait2_paint as P  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
_memo: dict = {}


# ------------------------------------------------------------------------------------------------ geometry
def nrm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def frame_along(o, y_axis, z_hint):
    """Frame at o whose local +y runs along y_axis and whose local +z is as close as possible to z_hint."""
    y = nrm(y_axis)
    z = np.asarray(z_hint, float)
    z = nrm(z - y * float(z @ y))
    x = np.cross(y, z)
    return S.Frame(np.asarray(o, float), np.stack([x, y, z], 1))


def _rot_axis(axis, deg):
    a = nrm(axis)
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


# finger table (cm): knuckle x for a RIGHT hand (thumb side = -x), knuckle y, segment lengths, root radius
_FINGERS = (
    (-2.75, 9.15, (4.3, 2.5, 2.0), 0.92, 9.0),     # index (spread angle toward the thumb)
    (-0.92, 9.45, (4.7, 2.85, 2.1), 0.95, 0.0),    # middle
    (0.90, 9.15, (4.4, 2.65, 2.0), 0.90, -6.0),    # ring
    (2.62, 8.35, (3.5, 2.05, 1.85), 0.80, -13.0),  # little
)
_JOINT = (78.0, 98.0, 62.0)                         # flexion at MCP / PIP / DIP for curl = 1


def hand(M, mat, s, side=1, curl=(0.35, 0.35, 0.35, 0.35), spread=0.0, thumb_abd=0.45, thumb_curl=0.25,
         thumb_flex=0.0, knuckles=True, fist=0.0, split=True, joints=None):
    """A hand in its local frame: origin at the wrist centre, +y toward the knuckles, +z = back of the hand,
    the thumb at -x for side=+1 (right hand, palm down) and at +x for side=-1.  Units: s px per cm.
    curl = flexion per finger (index, middle, ring, little) 0 = straight .. 1 = fully bent; spread fans the
    fingers; thumb_abd opens the thumb away from the index (0 = against it), thumb_curl bends its joints,
    thumb_flex swings it under the palm (opposition).  split: the fingers alternate between the materials
    mat+'_a' / mat+'_b' and the thumb is mat+'_t' (same style, see hand_styles) so pass_part_lines can draw
    the dark gaps between overlapping fingers.  joints (round 10b): per-joint multipliers (MCP, PIP, DIP) of the
    flexion, e.g. (0.2, 1, 1) for a hook grip whose first phalanges stay straight out of the knuckles (None = all 1,
    the round-10 hands)."""
    m = M(mat)
    jm = tuple(joints) if joints is not None else (1.0, 1.0, 1.0)
    fm = (M(mat + '_a'), M(mat + '_b')) if split else (m, m)
    tm = M(mat + '_t') if split else m
    sx = float(side)
    parts = [
        S.RoundBox((0.0, 5.6 * s, 0.05 * s), (3.55 * s, 3.75 * s, 1.08 * s), 0.95 * s, m),     # palm plate
        E((0.0, 1.7 * s, -0.25 * s), (3.0 * s, 2.5 * s, 1.55 * s), m),                         # heel of the hand
        E((-sx * 1.9 * s, 3.3 * s, -0.95 * s), (1.9 * s, 2.8 * s, 1.35 * s), m),               # thenar mound
        E((sx * 2.55 * s, 3.9 * s, -0.75 * s), (1.25 * s, 3.2 * s, 1.15 * s), m),              # hypothenar
    ]
    knuck = []
    for i, (kx, ky, segs, r0, ang) in enumerate(_FINGERS):
        c = float(curl[i]) if i < len(curl) else float(curl[-1])
        c = min(1.0, c + fist)
        base = np.array([sx * kx * s, ky * s, 0.15 * s + (0.25 * s if i == 1 else 0.0)])
        d = _rot_axis((0, 0, 1), -sx * ang * spread) @ np.array([0.0, 1.0, 0.0])
        bend_axis = nrm(np.cross(d, (0, 0, 1)))          # flexion turns +y toward -z (into the palm)
        p = base
        r = r0
        for j, L in enumerate(segs):
            d = _rot_axis(bend_axis, -_JOINT[j] * c * jm[j]) @ d
            q = p + d * L * s
            r1 = r * (0.88 if j < 2 else 0.80)
            parts.append(RC(tuple(p), tuple(q), r * s, r1 * s, fm[i % 2]))
            p = q
            r = r1 * 0.97
        if knuckles:
            knuck.append(S.Sphere(tuple(base + np.array([0, -0.15 * s, 0.35 * s])), r0 * 1.12 * s, m))
    # thumb: metacarpal from the wrist base, proximal + distal phalanx
    tb = np.array([-sx * 2.45 * s, 1.6 * s, -0.75 * s])
    td = nrm(np.array([-sx * (0.30 + 0.60 * thumb_abd), 0.92 - 0.35 * thumb_abd, -0.25 - 0.5 * thumb_flex]))
    tl = (4.1, 3.0, 2.55)
    tr = (1.28, 1.05, 0.92, 0.78)
    p = tb
    target = nrm(np.array([sx * 0.55, 0.15, -0.8]))     # the thumb tip curls in toward the palm centre
    axis = nrm(np.cross(td, target))
    for j, L in enumerate(tl):
        if j > 0:
            td = _rot_axis(axis, 38.0 * thumb_curl * (1 if j == 1 else 1.3)) @ td
        q = p + td * L * s
        parts.append(RC(tuple(p), tuple(q), tr[j] * s, tr[j + 1] * s, tm if j > 0 else m))
        p = q
    node = S.Union(parts, k=0.55 * s)
    if knuck:
        node = S.Union([node] + knuck, k=0.5 * s)
    return node


def hand_axes(s, side=1, curl=(0.35, 0.35, 0.35, 0.35), spread=0.0, thumb_abd=0.45, thumb_curl=0.25,
              thumb_flex=0.0, fist=0.0, joints=None, **_):
    """Round 10b: the joint chains of hand() (same arguments, hand-local px): [index, middle, ring, little,
    thumb], each a list of points from the knuckle (thumb: its base) to the tip, plus the radius at the
    knuckle.  Used by 2D passes that draw the gaps between the fingers and the knuckle lights of small hands."""
    jm = tuple(joints) if joints is not None else (1.0, 1.0, 1.0)
    sx = float(side)
    out = []
    for i, (kx, ky, segs, r0, ang) in enumerate(_FINGERS):
        c = float(curl[i]) if i < len(curl) else float(curl[-1])
        c = min(1.0, c + fist)
        p = np.array([sx * kx * s, ky * s, 0.15 * s + (0.25 * s if i == 1 else 0.0)])
        d = _rot_axis((0, 0, 1), -sx * ang * spread) @ np.array([0.0, 1.0, 0.0])
        bend_axis = nrm(np.cross(d, (0, 0, 1)))
        pts = [p.copy()]
        for j, L in enumerate(segs):
            d = _rot_axis(bend_axis, -_JOINT[j] * c * jm[j]) @ d
            p = p + d * L * s
            pts.append(p.copy())
        out.append((pts, r0 * s))
    tb = np.array([-sx * 2.45 * s, 1.6 * s, -0.75 * s])
    td = nrm(np.array([-sx * (0.30 + 0.60 * thumb_abd), 0.92 - 0.35 * thumb_abd, -0.25 - 0.5 * thumb_flex]))
    target = nrm(np.array([sx * 0.55, 0.15, -0.8]))
    axis = nrm(np.cross(td, target))
    p = tb
    pts = [p.copy()]
    for j, L in enumerate((4.1, 3.0, 2.55)):
        if j > 0:
            td = _rot_axis(axis, 38.0 * thumb_curl * (1 if j == 1 else 1.3)) @ td
        p = p + td * L * s
        pts.append(p.copy())
    out.append((pts, 1.28 * s))
    return out


def place(node, frame):
    return S.Xform(node, frame=frame)


def bounded(node, pts, pad):
    c, r = S.bound_of(np.asarray(pts, float), pad)
    return S.Bound(node, c, r, margin=3.0)


def sleeve_arm(M, sleeve, shoulder, elbow, wrist, r, cuff=None, cuff_len=1.5, cuff_r=None, skin='hand',
               hand_s=1.8, side=1, hand_dir=None, hand_up=(0, 0, 1), hand_kw=None, folds=3, fold_amp=0.10,
               elbow_point=True, flare=1.06, wrist_r=None, hand_len=None, gloves=None):
    """One continuous arm in view space.  shoulder/elbow/wrist: joint centres (wrist = end of the sleeve);
    r = (shoulder, elbow, sleeve end) radii.  The shirt cuff (material `cuff`, cuff_len px) and the bare wrist
    continue the forearm axis, then the hand (scale hand_s px/cm) whose fingers point along hand_dir (default:
    the forearm direction) with its back facing hand_up.  Returns (node, dict of key points)."""
    sh, el, wr = (np.asarray(v, float) for v in (shoulder, elbow, wrist))
    ms = M(sleeve)
    r_sh, r_el, r_wr = r
    parts = [RC(tuple(sh), tuple(el), r_sh, r_el, ms),
             RC(tuple(el), tuple(wr), r_el * 0.97, r_wr * flare, ms)]
    up_dir = nrm(el - sh)
    fo_dir = nrm(wr - el)
    if elbow_point:
        # the point of the elbow pushes the cloth out on the outside of the bend
        bend = nrm(up_dir - fo_dir)
        parts.append(E(tuple(el + bend * r_el * 0.35), (r_el * 0.72, r_el * 0.72, r_el * 0.72), ms))
    # folds: soft rings across the forearm close to the elbow (cloth gathered in the bend) and one under the
    # shoulder seam; their alternating bulges give the sleeve its creases
    for k in range(folds):
        t = 0.14 + 0.16 * k
        c = el + (wr - el) * t
        rr = r_el + (r_wr - r_el) * t
        R = frame_along(c, fo_dir, (0.31, 0.6, 0.73)).R            # columns = local axes (y = forearm)
        parts.append(E(tuple(c), (rr * (1.0 + fold_amp), rr * 0.22, rr * (1.0 + fold_amp)), ms, R=R))
    node = S.Union(parts, k=max(1.0, r_el * 0.25))
    pts = {'shoulder': sh, 'elbow': el, 'wrist': wr}
    tip = wr
    if cuff is not None:
        cr = cuff_r if cuff_r is not None else r_wr * 0.72
        c_end = wr + fo_dir * cuff_len
        cuffn = RC(tuple(wr - fo_dir * cuff_len * 0.8), tuple(c_end), cr, cr * 0.96, M(cuff))
        node = S.Union([node, cuffn], k=0.4)
        tip = c_end
    hk = dict(hand_kw or {})
    hd = nrm(hand_dir) if hand_dir is not None else fo_dir
    wr_r = wrist_r if wrist_r is not None else 1.55 * hand_s
    wrist_end = tip + hd * 0.4 * hand_s
    node = S.Union([node, RC(tuple(tip - fo_dir * 0.6 * hand_s), tuple(wrist_end), wr_r * 1.02, wr_r,
                             M(gloves or skin))], k=0.5)
    hf = frame_along(wrist_end, hd, hand_up)
    hnode = place(hand(M, gloves or skin, hand_s, side=side, **hk), hf)
    node = S.Union([node, hnode], k=0.6)
    pts.update(cuff_end=tip, hand_frame=hf, hand_tip=wrist_end + hd * 11.0 * hand_s)
    return node, pts


# ------------------------------------------------------------------------------------------------ painting
PIPELINE = ('chargen_portrait2_anat.py', 'chargen_portrait2_cast.py', 'chargen_portrait2_paint.py',
            'chargen_portrait2_sdf.py', 'env_veltrava_cine_rig.py')


def _src_key(extra=('env_veltrava_cine_heroes.py',)):
    """Content key of the sources a render depends on (the disk cache only skips recomputation)."""
    h = hashlib.sha1()
    for f in PIPELINE + tuple(extra):
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()[:16]


def _cache_dir():
    import tempfile
    d = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
    os.makedirs(d, exist_ok=True)
    return d


class Hit:
    def __init__(self, hit):
        self.hit = hit


def point_light(d, root, pos, gain, radius, wrap=0.25, shadow=True, steps=40, power=1.6):
    """Diffuse contribution of a point light at pos (view space px) for the downsampled buffer d."""
    Pp = d.P
    n = d.n
    L = np.asarray(pos, np.float32)[None, None, :] - Pp
    dist = np.sqrt((L * L).sum(2)) + 1e-4
    Ld = L / dist[..., None]
    ndl = (n * Ld).sum(2)
    diff = np.clip((ndl + wrap) / (1 + wrap), 0, 1)
    fall = np.clip(1.0 - dist / radius, 0, 1) ** power
    val = gain * diff * fall * d.hit
    if shadow and val.any():
        sel = (val > 0.002)
        idx = np.nonzero(sel)
        Q0 = Pp[idx] + n[idx] * 0.8
        Ls = Ld[idx]
        dl = dist[idx]
        vis = np.ones(len(dl), np.float32)
        t = np.full(len(dl), 1.5, np.float32)
        act = np.ones(len(dl), bool)
        for _ in range(steps):
            a = np.nonzero(act)[0]
            if a.size == 0:
                break
            Q = Q0[a] + Ls[a] * t[a, None]
            dd, _ = root.eval(Q.astype(np.float32))
            vis[a] = np.minimum(vis[a], np.clip(8.0 * dd / t[a], 0, 1))
            t[a] += np.clip(dd, 0.3, 5.0)
            act[a[(dd < 0.02) | (t[a] > dl[a] - 2.0)]] = False
        vv = val[idx] * (0.25 + 0.75 * vis)
        val = val.copy()
        val[idx] = vv
    return val.astype(np.float32)


def render(root, M, size, look, styles, groups=None, priority=None, tone_passes=(), G_extra=None, lights=(),
           outline=True, rim=True, ss=3, smooth=1, no_depth_line=(), cache_key=None, key_cut=None, v_mul=None,
           src=('env_veltrava_cine_heroes.py',)):
    """Trace + paint a scene -> dict(rgba, mat, names, key, rim, d, v).  lights = [(pos, gain, radius, mats)]
    point lights added to the light value (mats = None: all materials, else a tuple of material names)."""
    if cache_key is not None and cache_key in _memo:
        return _memo[cache_key]
    disk = None
    if cache_key is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        h = hashlib.sha1((_src_key(src) + repr((cache_key, size, ss))).encode('utf-8')).hexdigest()[:24]
        disk = os.path.join(_cache_dir(), 'rig_' + h + '.npz')
        if os.path.exists(disk):
            z = np.load(disk, allow_pickle=False)
            res = dict(rgba=z['rgba'], mat=z['mat'], names=[str(n) for n in z['names']], key=z['key'],
                       rim=z['rim'], d=Hit(z['hit']), v=z['v'], z=z['zb'])
            _memo[cache_key] = res
            return res
    w, h = size
    lk = P.Look(**look)
    g = S.trace(root, w, h, ss=ss, key=lk.key)
    names = M.names
    pri = [(priority or {}).get(n, 0) for n in names]
    d = S.downsample(g, len(M), priority=pri)
    v, rimv, keyv = P.light_value(d, lk, styles, names)
    for li in lights:
        if isinstance(li, dict):
            pos, gain, radius, mats = li['pos'], li['gain'], li['radius'], li.get('mats')
            add = point_light(d, root, pos, gain, radius, wrap=li.get('wrap', 0.25), shadow=li.get('shadow', True),
                              power=li.get('power', 1.6))
        else:
            pos, gain, radius, mats = li
            add = point_light(d, root, pos, gain, radius)
        if mats is not None:
            mm = np.zeros(d.mat.shape, bool)
            for nm in mats:
                if nm in names:
                    mm |= d.mat == names.index(nm)
            add = add * mm
        v = v + add
        keyv = np.maximum(keyv, add)
    if v_mul is not None:
        v = v_mul(v, d, M)
    if key_cut is not None:
        v = key_cut(v, d, M)
    v = P.smooth_by_material(v, d.mat, passes=smooth)
    tone = P.quantise(d, v, styles, names)
    G = dict(d=d, M=M, look=lk, v=v)
    if G_extra:
        G.update(G_extra)
    for fn in tone_passes:
        tone = fn(None, G, tone, v)
    tone = P.clean(tone, d.mat)
    rgb = P.colorize(d, tone, styles, names)
    if outline:
        rgb = P.outline(rgb, d, styles, names, look=lk)
        rgb, _ = P.depth_lines(rgb, d, styles, names, groups or {}, skip=no_depth_line)
    if rim:
        rgb = P.apply_rim(rgb, d, rimv, keyv, styles, names, tone)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    res = dict(rgba=out, mat=d.mat, names=list(names), key=keyv, rim=rimv, d=d, v=v, z=d.z, tone=tone)
    if cache_key is not None:
        _memo[cache_key] = res
    if disk is not None:
        np.savez(disk, rgba=out, mat=d.mat, names=np.array(list(names)), key=keyv, rim=rimv, hit=d.hit, v=v,
                 zb=np.where(d.hit, d.z, -1e4).astype(np.float32))
    return res


def mat_mask(res, *names):
    m = np.zeros(res['mat'].shape, bool)
    for n in names:
        if n in res['names']:
            m |= res['mat'] == res['names'].index(n)
    return m


# ------------------------------------------------------------------------------------------------ 2D passes
def pass_seam(mat_a, mat_b, dark=1):
    """Darken one tone where material a borders material b (a sleeve's armhole seam, a belt edge)."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat_a not in M.names or mat_b not in M.names:
            return tone
        d = G['d']
        ia, ib = M.names.index(mat_a), M.names.index(mat_b)
        a = d.mat == ia
        b = d.mat == ib
        nb = np.zeros_like(a)
        nb[1:] |= b[:-1]
        nb[:-1] |= b[1:]
        nb[:, 1:] |= b[:, :-1]
        nb[:, :-1] |= b[:, 1:]
        m = a & nb & (tone >= 1)
        tone = tone.copy()
        tone[m] = np.maximum(0, tone[m] - dark)
        return tone
    return fn


def pass_lines(mat, fn_mask, dark=1, lift=0):
    """Generic stitched/creased line pass: fn_mask(G, mask) -> bool array over the masked pixels."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        d = G['d']
        m = (d.mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        sel = fn_mask(G, m)
        t = tone[m].copy()
        t = np.where(sel, np.maximum(0, t - dark) + lift, t)
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def hand_styles(st, base='hand'):
    """Copy the hand style to the split finger / thumb materials of hand(split=True)."""
    for suf in ('_a', '_b', '_t'):
        st[base + suf] = st[base]
    return st


def pass_part_lines(prefix='hand', dark=2, gap=0.8, floor=1):
    """Dark 1-px gaps where one part of a hand (palm, alternate fingers, thumb) passes in front of another:
    the pixel BEHIND the depth step (material starting with `prefix`) drops `dark` tones (not below floor)."""
    def fn(spec, G, tone, v):
        M = G['M']
        ids = [i for i, n in enumerate(M.names) if n.startswith(prefix)]
        if len(ids) < 2:
            return tone
        d = G['d']
        mat = d.mat
        inh = np.isin(mat, ids)
        if not inh.any():
            return tone
        z = np.where(d.hit, d.z, -1e9)
        h, w = mat.shape
        zp = np.pad(z, 1, constant_values=-1e9)
        mp = np.pad(mat, 1, constant_values=-1)
        mark = np.zeros((h, w), bool)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            zn = zp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            mn = mp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            mark |= inh & np.isin(mn, ids) & (mn != mat) & (zn > z + gap)
        tone = tone.copy()
        tone[mark] = np.maximum(np.minimum(tone[mark], floor), tone[mark] - dark)
        return tone
    return fn
