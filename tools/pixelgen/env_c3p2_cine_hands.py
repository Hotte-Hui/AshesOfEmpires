"""env_c3p2_cine_hands -- hands, reaching arms and the two men lying in the snow for LS_C3_Escape / LS_C3_Halves
(round 9, feel pass 2; owner feel_r9).  Replaces the round-8 painted silhouettes (e3a hand close-up, e3b men in the
yard, h1 reaching arms) with figures sculpted and lit by the signed-distance pipeline of the dialogue portraits
(chargen_portrait2_*: sphere tracer, material ramps, outlines, rims; the heads, hats and hair of the cast specs --
imported read-only), so the hands and bodies carry the same materials, light and faces as the rest of the
cinematics (env_c3p2_cine_figs.py: the men on the bench from behind).

  e3a_frame(i)       520 x 360, 4 frames: Alexei's sooty hand rises out of the smoke of the coal hatch (0), reaches
                     with the fingers open (1), Konrad's hand comes down from the rim and takes his wrist (2), pulls
                     (3) -- the quilted green sleeve, Konrad's navy sleeve with the shirt cuff; lit from below by the
                     glow in the hatch, the cold yard lamp as rim
  lying_men(b)       560 x 96, 2 frames (b = chest heave): both on their backs in the snow, heads toward each other
                     (Konrad left, his hat beside him; Alexei right in the ushanka), one knee up, an arm flung out;
                     the yard lamp from the upper right, the snow's bounce from below
  arm_frame(w, m)    220 x 110: the reaching arms of h1 (w = 'a' / 'k', m = near / far / hold), seen from behind and
                     above like the bench figures, with their fire light from the left

Everything is deterministic numpy (no image inputs, no randomness).  Renders are memoised on disk (key = the
pipeline sources + this file + the call), ASHES_NO_CACHE=1 disables the cache.
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
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
TH7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]
_memo: dict = {}


def _src_key():
    h = hashlib.sha1()
    for f in ('chargen_portrait2_anat.py', 'chargen_portrait2_cast.py', 'chargen_portrait2_paint.py',
              'chargen_portrait2_sdf.py', 'env_c3p2_cine_hands.py'):
        with open(os.path.join(HERE, f), 'rb') as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def _norm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def frame_along(o, y_axis, z_hint):
    """Frame at o: local +y along y_axis, local +z as close as possible to z_hint, x = y cross z."""
    ey = _norm(y_axis)
    zh = np.asarray(z_hint, float)
    ez = _norm(zh - ey * float(np.dot(zh, ey)))
    ex = np.cross(ey, ez)
    return S.Frame(o, np.stack([ex, ey, ez], axis=1))


# ------------------------------------------------------------------------------------------------ painting
def paint(root, M, size, look, styles, frames=None, tone_passes=(), groups=None, ss=3, outline=True, rim=True,
          cache=None, glow=None):
    """Trace + paint a hand-built scene (view space = canvas px, y down, z toward the viewer) -> RGBA uint8.
    glow = (centre, radius, floor): the key is a local light (the fire in the hatch) -- the light value fades with
    the distance from centre down to `floor` (parts outside the hatch stay in the cold night)."""
    key = None
    if cache is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        import tempfile
        h = hashlib.sha1((_src_key() + repr((cache, size, look, ss, outline, rim, glow))).encode('utf-8')).hexdigest()[:20]
        d = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
        os.makedirs(d, exist_ok=True)
        key = os.path.join(d, 'hands_' + h + '.npz')
        if key in _memo:
            return _memo[key]
        if os.path.exists(key):
            out = np.load(key)['rgba']
            _memo[key] = out
            return out
    w, h = size
    lk = P.Look(**look)
    g = S.trace(root, w, h, ss=ss, key=lk.key)
    d = S.downsample(g, len(M))
    names = M.names
    G = dict(d=d, M=M, look=lk, zoom=1.0)
    for k, fr in (frames or {}).items():
        G[k] = fr
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
    if key is not None:
        np.savez(key, rgba=out)
        _memo[key] = out
    return out


# ------------------------------------------------------------------------------------------------ body parts
def hand(M, mat, s, curl=0.25, spread=0.0, thumb=1.0, grip=0.0):
    """A hand in its own frame (origin at the wrist, +y along the fingers, +z the back of the hand, the thumb on
    the +x side when thumb = 1).  s = palm length; curl 0 (open) .. 1 (fist), spread fans the fingers, grip
    folds the thumb in."""
    m = M(mat)
    parts = [E((0.0, 0.50 * s, 0.02 * s), (0.44 * s, 0.54 * s, 0.17 * s), m),        # palm / back of the hand
             E((0.0, 0.10 * s, -0.02 * s), (0.30 * s, 0.24 * s, 0.18 * s), m)]       # heel of the hand
    lens = (0.62, 0.84, 0.92, 0.82)                 # little, ring, middle, index (index next to the thumb)
    xs = (-0.33, -0.11, 0.11, 0.33)
    t1 = math.radians(52.0 * curl)
    t2 = math.radians(78.0 * curl)
    for i in range(4):
        x0 = xs[i] * s * thumb
        fan = (i - 1.5) * spread * 0.16 * thumb
        L = lens[i] * s
        r = (0.085 if i == 0 else 0.10) * s
        a = np.array([x0, 0.96 * s, 0.03 * s])
        d1 = _norm((fan, math.cos(t1), -math.sin(t1)))
        b = a + d1 * L * 0.55
        d2 = _norm((fan * 0.6, math.cos(t1 + t2), -math.sin(t1 + t2)))
        c = b + d2 * L * 0.45
        parts += [RC(tuple(a), tuple(b), r, r * 0.92, m), RC(tuple(b), tuple(c), r * 0.92, r * 0.76, m)]
    tb = np.array([0.34 * s * thumb, 0.26 * s, -0.06 * s])
    td = _norm((thumb * (0.62 - 0.40 * grip), 0.72, -0.22 - 0.70 * grip))
    tm = tb + td * 0.40 * s
    td2 = _norm((thumb * (0.30 - 0.45 * grip), 0.85, -0.25 - 0.60 * grip))
    tt = tm + td2 * 0.30 * s
    parts += [RC(tuple(tb), tuple(tm), 0.15 * s, 0.12 * s, m), RC(tuple(tm), tuple(tt), 0.12 * s, 0.095 * s, m)]
    return S.Union(parts, k=0.12 * s)


def limb(M, mat, pts, radii, k=3.0):
    """A sleeve / leg through the points with the radii (round cones, smooth joints)."""
    m = M(mat)
    parts = [RC(tuple(pts[i]), tuple(pts[i + 1]), radii[i], radii[i + 1], m) for i in range(len(pts) - 1)]
    return S.Union(parts, k=k)


def bounded(node, pts, pad):
    c = np.mean(np.asarray(pts, float), axis=0)
    r = max(float(np.linalg.norm(np.asarray(p, float) - c)) for p in pts) + pad
    return S.Bound(node, c, r, margin=3.0)


def arm(M, coat, skin, shoulder, elbow, wrist, r, hand_y, hand_z, s, cuff=None, cuff_len=0.0, **hand_kw):
    """Sleeve from the shoulder over the elbow to the wrist (radii r = shoulder, elbow, cuff), an optional shirt
    cuff peeking out, the wrist and the hand oriented by (hand_y = finger direction, hand_z = back of the hand)."""
    shoulder, elbow, wrist = (np.asarray(p, float) for p in (shoulder, elbow, wrist))
    fdir = _norm(wrist - elbow)
    sleeve_end = wrist - fdir * (0.55 * s + cuff_len)
    nodes = [limb(M, coat, [shoulder, elbow, sleeve_end], [r[0], r[1], r[2]], k=2.0 + r[1] * 0.3)]
    if cuff is not None and cuff_len > 0:
        nodes.append(RC(tuple(sleeve_end - fdir * 0.6), tuple(sleeve_end + fdir * cuff_len), r[2] * 0.72, r[2] * 0.66,
                        M(cuff)))
    wrist_start = sleeve_end + fdir * (cuff_len * 0.5)
    nodes.append(RC(tuple(wrist_start), tuple(wrist + fdir * 0.15 * s), 0.30 * s, 0.27 * s, M(skin)))
    nodes.append(S.Xform(hand(M, skin, s, **hand_kw), frame=frame_along(wrist, hand_y, hand_z)))
    pts = [shoulder, elbow, wrist, wrist + _norm(hand_y) * 1.6 * s]
    return bounded(S.Union(nodes, k=0.08 * s + 0.6), pts, max(r) + s * 0.9)


# ------------------------------------------------------------------------------------------------ styles
SOOT_SKIN_A = ramp('#07090c', '#121216', '#211a1c', '#352624', '#4e342c', '#6c4636', '#8c5c44', '#ad7856')
SOOT_SKIN_K = ramp('#08090e', '#14131a', '#241d23', '#3a2c2c', '#544036', '#725846', '#94745a', '#b49472')
SKIN_TH = [0.035, 0.085, 0.15, 0.25, 0.37, 0.55, 0.80]


def _styles_escape():
    """LS_C3_Escape e3a: key = the orange glow deep in the hatch (from below / in front), rim = the cold lamp."""
    fire_quilt = ramp('#030706', '#08120e', '#0f1d16', '#18291f', '#262a1c', '#3e3018', '#5e3e1c', '#86562a')
    fire_navy = ramp('#04060b', '#090e1a', '#0f1628', '#172038', '#262434', '#3e2a26', '#5e381e', '#86502a')
    shirt = ramp('#0d0c0e', '#221d1d', '#3d322d', '#5a463a', '#7a5e48', '#9c7a58', '#b8946a')
    return {
        'quilt': MatStyle(fire_quilt, TH7, dither=0.05, rim='#6f8e9a'),
        'coat': MatStyle(fire_navy, TH7, dither=0.03, rim='#7290b0'),
        'shirt': MatStyle(shirt, TH7[:6], dither=0.03, rim='#9aaabb'),
        'skin': MatStyle(SOOT_SKIN_A, SKIN_TH, dither=0.02, rim='#8fa6b4', wrap=0.18),
        'skin_k': MatStyle(SOOT_SKIN_K, SKIN_TH, dither=0.02, rim='#8fa6b4', wrap=0.18),
    }


def _styles_quay():
    """LS_C3_Halves h1: the bench figures' materials (env_c3p2_cine_figs fire styles): fire light from the left."""
    green = ramp('#030807', '#0a1411', '#111e18', '#1a2a21', '#4a2c18', '#7a4a20', '#b87430')
    navy = ramp('#04060b', '#090e1a', '#0f1628', '#162036', '#4a2818', '#7a3e1c', '#b8642a')
    shirt = ramp('#0e0f14', '#272a33', '#4a4c56', '#77777b', '#a19d98', '#d2c6b2')
    return {
        'quilt': MatStyle(green, TH7[:6], dither=0.05, rim='#5f8a96'),
        'coat': MatStyle(navy, TH7[:6], dither=0.03, rim='#6a86a6'),
        'shirt': MatStyle(shirt, [0.05, 0.12, 0.24, 0.42, 0.62], rim='#8ea2b4'),
        'skin': MatStyle(CC.SKIN_KARSK, SKIN_TH, dither=0.02, rim='#8fa6b4', wrap=0.15),
        'skin_k': MatStyle(CC.SKIN_BERLIN, SKIN_TH, dither=0.02, rim='#8fa6b4', wrap=0.15),
    }


GROUPS = {'quilt': 4, 'coat': 5, 'shirt': 6, 'skin': 0, 'skin_k': 1, 'neck': 0, 'lip': 0, 'ear': 0, 'hair': 2,
          'fur': 3, 'hat_top': 3, 'felt': 3, 'brim': 3, 'scarf': 7, 'knit': 8, 'boot': 9, 'trouser': 10, 'snowcap': 11}


# ------------------------------------------------------------------------------------------------ e3a
E3A_ORIGIN = (120, 0)          # canvas top-left in the 640 x 360 frame (layout.json escape.e3_hands)
E3A_SIZE = (520, 360)


def e3a_frame(fr):
    """Round 11: the arms on the anatomical rig with true bone lengths (env_c3p2_cine_hero.e3a_frame): 0 the hand
    rises out of the smoke, 1 reaches (fingers open), 2 Konrad's open hand comes in from the rim, 3 it closes round
    the wrist, 4-6 he pulls (both arms rise, his elbow bends)."""
    import env_c3p2_cine_hero as HR
    return HR.e3a_frame(fr)


def _legacy_e3a_frame(fr):
    """0 the hand rises out of the smoke, 1 reaches (fingers open), 2 Konrad's hand takes the wrist, 3 he pulls."""
    ox, oy = E3A_ORIGIN
    up = (0.0, -10.0, -14.0, -58.0)[fr]
    M = A.Mats()
    s = 46.0
    wx, wy = 300.0 - ox, 214.0 + up                     # Alexei's wrist (canvas px)
    a_hand = dict(curl=(0.38, 0.06, 0.62, 0.66)[fr], spread=(0.2, 1.3, 0.3, 0.3)[fr], thumb=1.0,
                  grip=(0.0, 0.0, 0.7, 0.75)[fr])
    nodes = [arm(M, 'quilt', 'skin', (wx + 14.0, 470.0, -80.0), (wx + 8.0, 360.0, -36.0), (wx, wy, 8.0),
                 (34.0, 31.0, 28.0), (0.06, -1.0, 0.42), (0.0, 0.35, 1.0), s, **a_hand)]
    frames = {'tf': frame_along((wx, wy, 8.0), (0.0, -1.0, 0.3), (0.0, 0.3, 1.0))}
    if fr >= 2:
        # Konrad kneels at the rim (upper right): his wrist above Alexei's, fingers round the back of the hand
        kx, ky = wx + 34.0, wy - 34.0
        nodes.append(arm(M, 'coat', 'skin_k', (kx + 260.0, ky - 230.0, 40.0), (kx + 120.0, ky - 92.0, 34.0),
                         (kx, ky, 26.0), (36.0, 31.0, 26.0), (-0.62, 0.70, -0.15), (0.25, -0.35, 1.0), 44.0,
                         cuff='shirt', cuff_len=10.0, curl=0.72, spread=0.15, thumb=-1.0, grip=0.8))
    root = S.Union(nodes, k=1.0)
    # the glow deep in the hatch lights the arm from below (grazing), the cold yard lamp rims it from the upper right
    look = dict(key=(0.10, 0.80, 0.22), rim=(0.60, -0.62, 0.48), ambient=0.04, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.07, fill_dir=(0.5, -0.6, 0.6), ao=0.55)
    return paint(root, M, E3A_SIZE, look, _styles_escape(), frames=frames, groups=GROUPS,
                 tone_passes=[CC.pass_stitches('quilt', 12.0, frame='tf', axis=1)], cache=('e3a', fr),
                 glow=((200.0, 420.0, -40.0), 330.0, 0.30))


# ------------------------------------------------------------------------------------------------ e3b
E3B_ORIGIN = (40, 220)         # layout.json escape.e3b_men
E3B_SIZE = (560, 96)
E3B_HEADS = (292.0, 360.0)     # head centres (frame x) of Konrad and Alexei, a hand's breadth apart
E3B_BREATH = [[287, 250], [384, 251]]   # their mouths (layout.json escape.e3b_breath, the runtime's breath puffs;
                                        # round 10: measured on the rigged men of env_c3p2_cine_hero.lying_men)


def _man_lying(M, who, b):
    """One man on his back in body units (portrait head units; origin = the pit of the neck, +y along the body
    toward the feet, +z = up out of the snow).  b = chest heave (0 / 1)."""
    spec = CC.alexei() if who == 'a' else CC.konrad()
    coat = 'quilt' if who == 'a' else 'coat'
    hp = A.head_params(**spec['head'])
    head, _lm = A.build_head(hp, M, jaw_open=0.06 if b else 0.0)
    if who == 'a':
        fns = [lambda: CC.ushanka(M, hp, flaps='down'),
               lambda: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0)]
    else:
        fns = [lambda: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2)]
    soft, clips, solid = [], [], []
    for f in fns:                                      # same assembly as env_veltrava_cine_figs._scene
        r = f()
        if isinstance(r, dict):
            solid.append(r['node'])
            if r.get('clip') is not None:
                clips.append(r['clip'])
            if r.get('soft') is not None:
                soft.append(r['soft'])
        else:
            soft.append(r)
    hb = S.Union([head] + soft)
    for c in clips:
        hb = S.Inter(hb, c)
    hnode = S.Union([hb] + solid)
    # body frame = standing frame (face along +z); lying on his back the face looks up, the chin a little raised
    head_f = S.Frame((0.0, -44.0, 2.0), S.rot(0.0, -12.0, 0.0))
    parts = [S.Xform(hnode, frame=head_f)]
    m = M(coat)
    chest = 1.0 + 0.05 * b
    torso = [E((0.0, 16.0, -2.0), (28.0, 12.0, 11.0), m),                     # shoulders
             E((0.0, 34.0, 1.0 + 1.5 * b), (24.0 * chest, 20.0, 13.0 * chest), m),   # chest (heaves)
             E((0.0, 60.0, -1.0), (23.0, 18.0, 11.0), m),                     # belly
             E((0.0, 84.0, -2.0), (22.0, 14.0, 11.0), m)]                     # hips
    if who == 'k':
        torso.append(E((0.0, 112.0, -4.0), (26.0, 34.0, 8.0), m))             # the long coat over the thighs
        parts.append(RC((-4.0, 2.0, 2.0), (6.0, 2.0, 4.0), 7.0, 6.5, M('scarf')))
        parts.append(RC((6.0, 4.0, 5.0), (11.0, 20.0, 8.0), 4.0, 3.4, M('scarf')))
    else:
        parts.append(RC((0.0, -6.0, -1.0), (0.0, 4.0, 1.0), 9.5, 10.0, M('knit')))   # roll-neck collar
    parts.append(S.Union(torso, k=6.0))
    leg = M('trouser')
    boot = M('boot')
    # right leg straight, left knee up (in the snow), boots pointing up
    for (hip, knee, ank) in (((-10.0, 88.0, -2.0), (-11.0, 150.0, 2.0), (-11.0, 212.0, 0.0)),
                             ((10.0, 88.0, -2.0), (14.0, 140.0, 34.0), (12.0, 190.0, 2.0))):
        parts.append(RC(hip, knee, 10.5, 8.5, leg))
        parts.append(RC(knee, ank, 8.5, 6.5, leg))
        parts.append(RC(ank, (ank[0], ank[1] + 6.0, ank[2] + 14.0), 7.0, 6.0, boot))
    # arms: one flung out above the head into the snow, one along the body
    sk = M('skin') if who == 'a' else M('skin_k')
    if who == 'a':
        sh, el, wr = (-26.0, 16.0, -2.0), (-38.0, -22.0, 2.0), (-30.0, -62.0, 4.0)
    else:
        sh, el, wr = (-26.0, 16.0, -2.0), (-44.0, 40.0, 0.0), (-40.0, 76.0, 4.0)
    parts.append(RC(sh, el, 8.6, 7.4, m))
    parts.append(RC(el, wr, 7.4, 6.4, m))
    hand_dir = _norm(np.asarray(wr) - np.asarray(el))
    parts.append(RC(wr, tuple(np.asarray(wr) + hand_dir * 14.0), 5.0, 4.0, sk))
    sh2, el2, wr2 = (26.0, 16.0, -2.0), (34.0, 46.0, 6.0), (16.0, 66.0, 12.0)   # the other hand on the chest
    parts.append(RC(sh2, el2, 8.6, 7.4, m))
    parts.append(RC(el2, wr2, 7.4, 6.4, m))
    parts.append(RC(wr2, (8.0, 60.0, 15.0), 5.0, 4.2, sk))
    return S.Union(parts, k=2.5)


def _hat_in_snow(M):
    """Konrad's fedora fallen beside his head: crown and brim (body units of the man, view-local)."""
    felt, brim = M('felt'), M('brim')
    crown = S.Union([E((0.0, 0.0, 6.0), (14.0, 11.0, 8.0), felt), E((0.0, 0.0, 11.0), (11.0, 9.0, 4.0), felt)], k=3.0)
    rim_ = E((0.0, 0.0, 1.0), (22.0, 17.0, 2.2), brim)
    return S.Union([crown, rim_], k=1.0)


def lying_men(b):
    """Round 10: both men on the full anatomical rig (env_c3p2_cine_hero.lying_men), 2 frames (chest heave)."""
    import env_c3p2_cine_hero as HR
    return HR.lying_men(b)


def _legacy_lying_men(b):
    """Both men on their backs (2 frames: b = 0 / 1 chest heave), view = canvas px of the e3b sprite."""
    ox, oy = E3B_ORIGIN
    M = A.Mats()
    zoom = 0.58                                   # body units -> px (heads about 26 px, bodies about 190 px)
    # camera low over the snow: the body's +z (up) is mostly view -y, tilted a little toward the viewer
    tilt = math.radians(22.0)
    nodes = []
    for who, hx, sgn in (('k', E3B_HEADS[0], -1.0), ('a', E3B_HEADS[1], 1.0)):
        ey = np.array([sgn, 0.0, 0.0])                                 # along the body (toward the feet)
        ez = np.array([0.0, -math.cos(tilt), math.sin(tilt)])          # out of the snow (up), toward the viewer
        ex = np.cross(ey, ez)
        R = np.stack([ex, ey, ez], axis=1) * zoom                      # local -> view incl. zoom
        o = np.array([hx - ox + sgn * 44.0 * zoom, 272.0 - oy, 0.0])   # the neck pit (head at hx)
        man = _man_lying(M, who, b)
        # Xform maps view -> local with R^T: scale the local frame by the zoom through a scaled child instead
        node = S.Scale(S.Xform(man, o=o / zoom, R=R / zoom), (0.0, 0.0, 0.0), zoom)
        nodes.append(S.Bound(node, (o[0] + sgn * 60.0, o[1], 0.0), 130.0, margin=3.0))
    # Konrad's hat in the snow beside his head
    hat_o = np.array([320.0 - ox, 287.0 - oy, 6.0])
    R = np.stack([np.array([1.0, 0.0, 0.0]), np.array([0.0, math.sin(tilt), math.cos(tilt)]),
                  np.array([0.0, -math.cos(tilt), math.sin(tilt)])], axis=1)
    nodes.append(S.Scale(S.Xform(_hat_in_snow(M), o=hat_o / zoom, R=R), (0.0, 0.0, 0.0), zoom))
    root = S.Union(nodes, k=0.5)
    look = dict(key=(0.50, -0.80, 0.33), rim=(-0.55, -0.45, -0.70), ambient=0.07, wrap=0.15, bg='berlin',
                glow=(0.8, 0.2), fill=0.10, fill_dir=(0.0, 0.85, 0.5), ao=0.5)
    st = _styles_escape()
    snow_lit = ['#0e1219', '#1a2230', '#2a3446', '#3e4a5e', '#56647a', '#75839a', '#98a6ba']
    st.update({
        'quilt': MatStyle(ramp('#030706', '#08120e', '#0f1d16', '#16261d', '#1e3226', '#283e30', '#34503d'), TH7[:6],
                          dither=0.05, rim='#7f97a6'),
        'coat': MatStyle(ramp('#04060b', '#090e1a', '#0f1628', '#151f34', '#1c2944', '#253452', '#304264'), TH7[:6],
                         dither=0.03, rim='#7f93b0'),
        'trouser': MatStyle(ramp('#06070a', '#0e1016', '#171a22', '#222631', '#303544', '#434a5c'),
                            [0.05, 0.12, 0.24, 0.40, 0.60], rim='#7f93a8'),
        'boot': MatStyle(ramp('#050505', '#0d0c0c', '#171514', '#24201e', '#36302c'), [0.06, 0.15, 0.3, 0.5],
                         rim='#7f93a8'),
        'scarf': MatStyle(ramp('#0e0c0e', '#1f1a1b', '#2e2724', '#41382e', '#544636', '#68563e'), TH7[:5],
                          dither=0.03, rim='#8fa0ae'),
        'knit': MatStyle(ramp('#0a0b0d', '#16181c', '#24272c', '#353940', '#4a4e55', '#61656b'), TH7[:5], rim='#8fa0ae'),
        'felt': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840'), TH7[:5], dither=0.04,
                         rim='#8fa0ae'),
        'brim': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840'), TH7[:5], rim='#8fa0ae'),
        'hair': MatStyle(ramp('#07080d', '#100e13', '#1a1518', '#261d1f', '#3a2a26', '#5a3e2e'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#7f93a8'),
        'fur': MatStyle(ramp('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#574b3f', '#716250', '#8b7b66'),
                        TH7[:6], dither=0.06, rim='#8aa4b4'),
        'hat_top': MatStyle(ramp('#0a0909', '#161312', '#221d1a', '#312a25', '#423830', '#55483c'),
                            [0.06, 0.14, 0.27, 0.45, 0.66], rim='#8aa4b4'),
        'tie_string': MatStyle(ramp('#0c0a09', '#2a221c', '#4a3c30', '#6a5844'), [0.1, 0.3, 0.6], rim='#8aa4b4'),
        'neck': MatStyle(SOOT_SKIN_K, SKIN_TH, rim='#8fa6b4'),
        'lip': MatStyle(SOOT_SKIN_K, SKIN_TH, rim='#8fa6b4'),
        'ear': MatStyle(SOOT_SKIN_K, SKIN_TH, rim='#8fa6b4'),
        'snowcap': MatStyle(ramp(*snow_lit), [0.05, 0.12, 0.24, 0.40, 0.6, 0.8], rim='#c8d2de'),
    })
    out = paint(root, M, E3B_SIZE, look, st, groups=GROUPS, cache=('e3b', b),
                glow=((560.0 - ox, -180.0, 60.0), 760.0, 0.55)).copy()
    # contact with the snow: a 1-2 px trodden shadow under every column of the two bodies
    a = out[..., 3] > 0
    shadow = np.array(P.hexc('#3b4556'), np.uint8) if hasattr(P, 'hexc') else np.array([59, 69, 86], np.uint8)
    for x in range(out.shape[1]):
        ys = np.nonzero(a[:, x])[0]
        if ys.size == 0:
            continue
        for dy in (1, 2) if ys.size > 6 else (1,):
            y = ys[-1] + dy
            if y < out.shape[0] and not a[y, x]:
                out[y, x, :3] = shadow
                out[y, x, 3] = 255
    return out


# ------------------------------------------------------------------------------------------------ h1 arms
# Round 10: the reaching arms come from the same 3D scene as the bench figures (env_c3p2_cine_hero): the inner arm
# (Alexei's right, Konrad's left) leaves the body at the shoulder, the blade slides toward the pages for the far
# reach, the hand lands flat on the stack; drawn under the bodies by the runtime.
import env_c3p2_cine_hero as _HR   # noqa: E402
E3A_FRAMES = _HR.E3A_FRAMES        # round 11: 7 frames (see env_c3p2_cine_hero.e3a_arms)
E3B_BREATH = _HR.e3b_breath()      # round 11: the mouths of the men in the snow, measured on the low camera

ARMS_ORIGIN = _HR.ARMS_AT     # layout.json halves.arms_at
ARMS_SIZE = _HR.ARMS_WH


def arms_sheet():
    """h1 arms.png, round 11: (sheet, layout additions) -- 2 rows x env_c3p2_cine_hero.ARM_COLS cells (reach
    in three steps, the pull in two, the hold, Konrad's list); see env_c3p2_cine_hero.arms_sheet."""
    return _HR.arms_sheet()


def arm_frame(who, mode):
    """h1 arms.png frame: who 'a' / 'k', mode near / far / hold."""
    return _HR.bench_arm(who, mode)
