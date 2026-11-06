"""env_veltrava_cine_heroes -- Konrad and Alexei for the Chapter-3 part-1 cinematics, round 10 (owner: the
figures stream of LS_C3_Trains / LS_C3_ToHall / LS_C3_Close).

Replaces the round-7 seated busts (env_veltrava_cine_figs.back_konrad / back_alexei stay untouched for the other
film families that import that module).  Every figure here has complete arms built with
env_veltrava_cine_rig: shoulder -> upper arm -> elbow (sleeve folds, the point of the elbow) -> forearm -> shirt
cuff -> wrist -> hand (palm, knuckles, three phalanges per finger, thumb) -- sculpted and lit in the portrait
pipeline (heads, hats, hair and garments of chargen_portrait2_cast.konrad()/alexei(), read-only), so the faces,
hats and coats stay the ones the player knows.

  seated_konrad(turn)      t1: Konrad at the window of the saloon car, from behind-right; his left forearm on the
                           table, the hand round the coffee cup by the lamp; his right elbow out on the armrest of
                           the club chair whose buttoned back hides his hips.  turn 1 = head a little more toward
                           the glass.  Lit by the reading lamp (point light) and the cold window (rim).
  seated_alexei(turn)      t3: Alexei at the window of the Soviet compartment, from behind-left; his right hand at
                           the handle of the tea-glass holder, the left forearm on his knee; the wall lamp (point
                           light) at the right.
  fig_konrad_sheet(L) / fig_alexei_sheet(L)   the runtime sheets (4 frames: 2 head poses x breath; the breath
                           lifts only the shoulders and head, the hand stays on the cup) + their layout boxes.
  reach_shadow_k(p, lamp) / reach_shadow_a(p, lamp)   contact shadows of the forearm and hand on the table
                           (painted into the interior under the figure).

  walking_konrad(frame) / k2_konrad_sheet(L)   LS_C3_ToHall k2: Konrad as a whole man (~112 px) walking in under
                           the palais clock, legs by IK on a gait table, and the path / stride the runtime follows.

Round 10b (art-director pass): the hands at the cup and the tea glass are hand-sized (~1.85 px/cm, as the cup
and the glass) hook grips with four readable fingers, the thumb on top (finger_marks draws the gaps the camera
sees) and, for Alexei, the handle's bar in his fist; Konrad's hat has a real ribbon band and no felt strip under
the brim (fedora_cut / hat_band: round 10 showed a dashed black line round the crown); the walking Konrad has a
continuous rim along his outline (contour_rim) instead of the dashed per-pixel rim.

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
import chargen_portrait2_cast as CC  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402
import env_veltrava_cine_rig as R    # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
C0 = np.array([56.0, 56.0, 0.0])          # zoom centre of the bust tone passes (chargen_portrait2_cast._local)
TH7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]

# screen boxes (x, y, w, h) of the seated figures; the runtime reads their position from layout.json
BOX_K = (334, 88, 236, 232)
BOX_A = (90, 86, 252, 232)
K_CUP = (352, 236)                        # foot of Konrad's coffee cup (env_veltrava_cine.K_CUP)
K_LAMP = (330, 207)                       # the silk shade of the reading lamp
TEA = (331, 236)                          # foot of Alexei's tea-glass holder (env_veltrava_cine.TEA)
A_LAMP = (507, 152)                       # the wall lamp of the Soviet compartment


def _pre(px, zoom):
    p = np.asarray(px, float)
    return tuple((p - C0[:len(p)]) / zoom + C0[:len(p)])


def to_img(frame, zoom, p_local):
    """Torso/head-local point -> figure-image pixel coordinates (x, y, z)."""
    v = frame.to_view(p_local)
    return C0 + (v - C0) * zoom


# ------------------------------------------------------------------------------------------------ styles
def _warm(base, warm_tail):
    return ramp(*(list(base) + list(warm_tail)))


def konrad_styles():
    k_dark = ['#05070d', '#0a0f1d', '#10182b', '#18233c', '#23304f']
    k_warm = ['#3c3a52', '#5e4b52', '#86624f']
    sk = CC.SKIN_BERLIN
    st = {
        'coat': MatStyle(_warm(k_dark, k_warm), TH7, dither=0.02, rim='#56769c'),
        'sleeve': MatStyle(_warm(k_dark, k_warm), TH7, dither=0.02, rim='#56769c'),
        'coat_lapel': MatStyle(_warm(k_dark, k_warm), TH7, rim='#56769c'),
        'felt': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840', '#7e6450',
                              '#a07c5c'), TH7, dither=0.04, rim='#5a7590'),
        'brim': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840', '#7e6450',
                              '#a07c5c'), TH7, rim='#5a7590'),
        'ribbon': MatStyle(ramp('#050508', '#0c0b10', '#16141a', '#221e25', '#302a32', '#4a3a36'),
                           [0.06, 0.16, 0.32, 0.5, 0.7], rim='#3f526a'),
        'hair': MatStyle(ramp('#07080d', '#100e13', '#1a1518', '#261d1f', '#3a2a26', '#5a3e2e'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#4a5f74'),
        'scarf': MatStyle(ramp('#0e0c0e', '#1f1a1b', '#352d2a', '#504536', '#6c5a40', '#93754c', '#b99159',
                               '#d6ad6c'), TH7, dither=0.03, rim='#7f93a0'),
        'shirt': MatStyle(ramp('#14141c', '#2c2b33', '#4f4b4f', '#7a726c', '#a59a8c', '#cfc2ab', '#efe2c6'),
                          [0.04, 0.10, 0.2, 0.33, 0.5, 0.7], rim='#8ea2b4'),
        'hand': MatStyle(sk, [0.03, 0.07, 0.13, 0.22, 0.36, 0.55, 0.80], rim='#6e8fa6', outline=sk[0], wrap=0.2,
                         lift=0.3, ao=0.6),
        'chair': MatStyle(ramp('#050708', '#0a1012', '#10191b', '#172427', '#203235', '#2c4245', '#3f5452',
                               '#5e6656'), TH7, dither=0.03, rim='#3f6070'),
        'nail': MatStyle(ramp('#1a1206', '#3a2810', '#6e5226', '#a88446', '#d8b878'), [0.05, 0.15, 0.35, 0.6],
                         rim='#c8b080'),
        'belt': MatStyle(_warm(k_dark, k_warm), TH7, rim='#56769c'),
        'button': MatStyle(ramp('#050508', '#141218', '#2a2228', '#4a3a38', '#6e5a50'), [0.05, 0.15, 0.3, 0.55],
                           rim='#56769c'),
    }
    for k, v in CC.skin_styles(sk, '#6e8fa6').items():
        st[k] = v
    return R.hand_styles(st)


def alexei_styles():
    green = ['#050a09', '#0b1512', '#12201a', '#1b2c23', '#26392d']
    warm = ['#3d4630', '#5d5a3a', '#867548']
    sk = CC.SKIN_KARSK
    st = {
        'coat': MatStyle(_warm(green, warm), TH7, dither=0.04, rim='#5f8a84'),
        'sleeve': MatStyle(_warm(green, warm), TH7, dither=0.04, rim='#5f8a84'),
        'coat_lapel': MatStyle(_warm(green, warm), TH7, rim='#5f8a84'),
        'fur': MatStyle(ramp('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#574b3f', '#7a6247', '#9c7d58',
                             '#bb9a6e'), TH7, dither=0.06, rim='#7d9a92'),
        'hat_top': MatStyle(ramp('#0a0909', '#161312', '#221d1a', '#312a25', '#4a3a2c', '#665038'),
                            [0.05, 0.12, 0.24, 0.40, 0.6], rim='#5f7a76'),
        'hair': MatStyle(ramp('#0b0a0b', '#1b1614', '#2d241e', '#45372b', '#644a32', '#866340'),
                         [0.04, 0.10, 0.2, 0.34, 0.52], rim='#6b8a84'),
        'knit': MatStyle(ramp('#0a0b0d', '#16181c', '#24272c', '#353940', '#4f4c4a', '#6e6457', '#8f7f68'),
                         [0.04, 0.10, 0.2, 0.32, 0.48, 0.68], dither=0.03, rim='#6f8c88'),
        'strap': MatStyle(ramp('#0c0807', '#1d120d', '#311e14', '#4a2d1c', '#643e26', '#7e5232', '#9a6a40'),
                          [0.05, 0.12, 0.24, 0.40, 0.60, 0.8], rim='#6b7f7a'),
        'tie_string': MatStyle(ramp('#0c0a09', '#2a221c', '#4a3c30', '#6a5844'), [0.1, 0.3, 0.6], rim='#7d9a92'),
        'shirt': MatStyle(ramp('#0a0b0d', '#16181c', '#24272c', '#353940', '#4f4c4a', '#6e6457', '#8f7f68'),
                          [0.04, 0.10, 0.2, 0.32, 0.48, 0.68], dither=0.02, rim='#6f8c88'),
        'hand': MatStyle(sk, [0.03, 0.07, 0.13, 0.22, 0.36, 0.55, 0.80], rim='#5f8a84', outline=sk[0], wrap=0.2,
                         lift=0.3, ao=0.6),
        'buckle': MatStyle(ramp('#15171c', '#323840', '#5e666e', '#a1aab7', '#dee2e7'), [0.08, 0.2, 0.42, 0.66],
                           rim='#c2c9d2'),
        # round 10b: the bar of the podstakannik handle in his fist (nickel silver, lit by the tea)
        'handle': MatStyle(ramp('#15171c', '#323840', '#5e666e', '#8593a3', '#c2c9d2', '#eef0f2'),
                           [0.06, 0.15, 0.3, 0.5, 0.72], rim='#c2c9d2'),
    }
    for k, v in CC.skin_styles(sk, '#5f8a84').items():
        st[k] = v
    return R.hand_styles(st)


# ------------------------------------------------------------------------------------------------ body parts
def seated_back(M, mat='body', width=1.0, depth=1.0, slope=1.0, lean=0.0, hips=1.0):
    """Shoulders, back and hips of a seated man (torso-local frame of the busts: origin at the pit of the
    neck, y down, z forward = toward the table).  No arms: those are chained in view space."""
    m = M(mat)
    w, d = width, depth
    base = A.build_torso(M, mat, width, depth, slope)
    parts = [base,
             E((0.0, 34.0, -4.5 + lean * 0.4), (25.5 * w, 22.0, 12.0 * d), m),                   # upper back
             E((11.5 * w, 30.0, -10.5 * d), (8.5, 11.5, 4.0), m),                                # shoulder blades
             E((-11.5 * w, 30.0, -10.5 * d), (8.5, 11.5, 4.0), m),
             E((0.0, 56.0, -1.5 + lean), (23.0 * w, 22.0, 12.5 * d), m),                         # waist / lower back
             E((0.0, 80.0, 1.0 + lean * 1.4), (24.0 * w * hips, 15.0, 14.5 * d), m)]             # hips on the seat
    return S.Union(parts, k=6.0)


def coat_back(M, t, coat='coat', drape=1.0, w=1.0):
    """A heavy coat falling straight from the shoulder blades over the waist (no wasp waist under wool)."""
    m = M(coat)
    return S.Union([E((0.0, 60.0, -3.5), (27.5 * w, 38.0 * drape, 13.8), m),
                    E((0.0, 88.0, 1.5), (27.5 * w, 16.0, 16.5), m)], k=6.0)


def band_back(M, torso_node, lift, p0, angle_deg, width, mat, y_range=None, x_range=None):
    """A flat band on the BACK of the torso (z < -2): straps, a half belt."""
    m = M(mat)
    a = np.radians(angle_deg)
    n = np.array([-np.sin(a), np.cos(a)])

    def region(Pp):
        dd = np.abs((Pp[:, 0] - p0[0]) * n[0] + (Pp[:, 1] - p0[1]) * n[1]) - width / 2
        dd = np.maximum(dd, Pp[:, 2] + 2.0)
        if y_range is not None:
            dd = np.maximum(dd, np.maximum(y_range[0] - Pp[:, 1], Pp[:, 1] - y_range[1]))
        if x_range is not None:
            dd = np.maximum(dd, np.maximum(x_range[0] - Pp[:, 0], Pp[:, 0] - x_range[1]))
        return dd

    return S.Inter(S.Offset(torso_node, lift, m), S.Fn(region, m))


def nape(M, mat='hair', c=(0.0, 4.5, -10.0), r=(10.5, 5.5, 6.0)):
    return E(c, r, M(mat))


def pass_hair_back(mat='hair', seed=19):
    """Hair from behind: fine combed strands toward the nape (clustered value breaks, never noise)."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = CC._local(G, 'hf', m)
        k = np.floor(L[:, 0] * 0.7 + L[:, 1] * 0.08).astype(int)
        r = CC._hash2(k, np.floor(L[:, 1] / 6).astype(int), seed)
        t = tone[m].copy()
        t = np.where((r < 0.22) & (t >= 2), t - 1, np.where(r > 0.90, t + 1, t))
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def pass_back_seam(mat='coat', frame='tf', x=0.0, y0=-2.0, y1=200.0, width=0.45, vent=None):
    """The centre back seam of a coat (one tone darker), optionally opening into the vent below `vent`."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = CC._local(G, frame, m)
        sel = (np.abs(L[:, 0] - x) < width) & (L[:, 1] > y0) & (L[:, 1] < y1) & (L[:, 2] < -3.0)
        t = tone[m].copy()
        t = np.where(sel, np.maximum(0, t - 1), t)
        if vent is not None:
            vs = (np.abs(L[:, 0] - x - 1.1) < 0.5) & (L[:, 1] > vent) & (L[:, 2] < -3.0)
            t = np.where(vs, np.maximum(0, t - 1), t)
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def pass_tension(mat, frame, a, b, n=3, spacing=3.2, width=0.42, dark=1, z_max=-3.0):
    """Diagonal tension folds pulled across the back toward a reaching arm: n lines parallel to a->b
    (torso-local x/y), one tone darker on the shadow side and one lighter just above (a fold, not a scratch)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    L_ = np.linalg.norm(d)
    u = d / L_
    nv = np.array([-u[1], u[0]])

    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        Lc = CC._local(G, frame, m)
        q = Lc[:, :2] - a[None, :]
        along = q @ u
        across = q @ nv
        t = tone[m].copy()
        inside = (along > 0) & (along < L_) & (Lc[:, 2] < z_max)
        fade = np.clip(1 - np.abs(along / L_ - 0.5) * 2.2, 0, 1)
        for k in range(n):
            c = (k - (n - 1) / 2) * spacing
            dark_l = inside & (np.abs(across - c) < width * (0.6 + fade)) & (fade > 0.15)
            lite_l = inside & (np.abs(across - c + 1.1) < width * 0.8) & (fade > 0.35)
            t = np.where(dark_l, np.maximum(0, t - dark), np.where(lite_l, t + 1, t))
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


# ------------------------------------------------------------------------------------------------ scenes
def _head_and_torso(spec, M, zoom, head_px, torso_px, yaw, pitch, roll, torso_yaw, torso_pitch, torso_node,
                    head_items, torso_items):
    hp = A.head_params(**spec['head'])
    head, lm = A.build_head(hp, M, jaw_open=0.0)
    items, clips, solid = [], [], []
    for f in head_items:
        r = f(M, hp)
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
    hpos = _pre(tuple(head_px) + (0.0,), zoom)
    tpos = _pre(tuple(torso_px) + (0.0,), zoom)
    hf = S.Frame(hpos, S.rot(yaw, pitch, roll))
    tf = S.Frame(tpos, S.rot(torso_yaw, torso_pitch, 0))
    t_items = [f(M, torso_node) for f in torso_items]
    hnode = S.Bound(S.Xform(S.Union([body] + solid), frame=hf), np.array(hpos) + np.array([0, -7.0, 0]), 48.0,
                    margin=3.0)
    tnode = S.Bound(S.Xform(S.Union([torso_node] + t_items), frame=tf), np.array(tpos) + np.array([0, 44.0, 0]),
                    124.0, margin=3.0)
    scaled = S.Scale(S.Union([hnode, tnode]), C0, zoom)
    return scaled, hp, lm, hf, tf


def _render_seated(who, turn, size, zoom, head_px, torso_px, yaw, pitch, torso_yaw, torso_pitch, torso_kw,
                   head_items, torso_items, arms_fn, look, styles, tone_passes, lights, extra_fn=None,
                   groups=None, cache=None, ss=3, post=None):
    """post(res) -> rgba: a 2D pass on the finished render (round 10b: the finger gaps of the hand at the cup /
    the tea glass)."""
    spec = CC.konrad() if who == 'konrad' else CC.alexei()
    M = A.Mats()
    for nm in ('skin', 'lip', 'ear', 'neck'):
        M(nm)
    torso = seated_back(M, 'body', **torso_kw)
    scaled, hp, lm, hf, tf = _head_and_torso(spec, M, zoom, head_px, torso_px, yaw, pitch, 0.0, torso_yaw,
                                             torso_pitch, torso, head_items, torso_items)
    arms, pts = arms_fn(M, tf, zoom)
    parts = [scaled] + arms
    if extra_fn is not None:
        parts += extra_fn(M, tf, zoom)
    root = S.Union(parts, k=0.0)
    gr = dict(spec['groups'])
    gr.update({'sleeve': 9, 'hand': 10, 'hand_a': 10, 'hand_b': 10, 'hand_t': 10, 'chair': 11, 'nail': 11,
               'belt': 4, 'button': 4, 'buckle': 7})
    if groups:
        gr.update(groups)
    res = R.render(root, M, size, look, styles, groups=gr, priority=dict(spec.get('priority', {}), hand=3,
                                                                          shirt=2),
                   tone_passes=tone_passes, G_extra=dict(hp=hp, lm=lm, hf=hf, tf=tf, zoom=zoom),
                   lights=lights, ss=ss, cache_key=cache)
    res = dict(res)
    res['pts'] = pts
    if post is not None:
        res['rgba'] = post(res)
    return res


def fedora_cut(M, hp, y0=-13.2, z0=-5.2, tilt=(5.0, -3.0), cut=1.0):
    """CC.fedora with its crown ending at the underside of the brim (round 10b).  The portrait crown runs 4 units
    below the brim -- hidden in front views, but from behind at eye level it showed as a felt strip under the brim
    whose outline broke into the dashed black line the art director saw round the crown.  The head may now fill
    right up to the brim (the clip plane moves up with the cut)."""
    r = dict(CC.fedora(M, hp, y0=y0, z0=z0, tilt=tilt))
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    r['node'] = S.Inter(r['node'], S.Xform(S.Fn(lambda P, c=cut: P[:, 1] - c, M('felt')), frame=hf))
    r['clip'] = S.Union([r['clip'], S.Xform(S.Fn(lambda P, c=cut: c - P[:, 1], M('felt')), frame=hf)])
    return r


# ---------------------------------------------------------------------------------------------- hands (round 10b)
# the outline between alternate fingers and round the thumb (with finger_marks: the gaps the camera sees)
HAND_SEAMS = [R.pass_seam('hand_a', 'hand_b', 1), R.pass_seam('hand_t', 'hand', 1), R.pass_seam('hand_t', 'hand_a', 1)]

# The art director measured round 10's hands at 14 x 11 px (Konrad) and 18 x 16 px (Alexei) against heads 40-50 px
# wide: mittens.  At the depth of the table the cup and the tea glass are drawn at ~2.1-2.3 px/cm, so a hand there
# is ~2 px/cm -- the knuckles ~16 px across, the back of the hand ~19 px long.  Both grips are hooks: the first
# phalanges come straight out of the knuckles (the MCP joints barely bent, joints=(mcp, pip, dip) of rig.hand), so
# their backs face the camera and read as four fingers with dark gaps between them; the middle and end joints fold
# round the handle; the thumb lies along the top of the handle, pointing at the cup / the glass.  Alexei's fist closes round the vertical bar of the
# podstakannik handle (painted in the room at x 320, y 225-231): the sprite repeats the bar above and below the fist
# in lit nickel silver so the grip reads against the dark sill.
K_HAND = dict(s=1.85, side=1, dir=(-0.97, 0.10, -0.22), up=(0.10, -0.42, 0.90),
              kw=dict(curl=(0.55, 0.60, 0.66, 0.72), joints=(0.35, 1.0, 0.9), spread=0.12, thumb_abd=0.22,
                      thumb_curl=0.12, thumb_flex=-1.00),
              wrist=(40.0, -3.0), elbow=(64.0, 11.0))
A_HAND = dict(s=1.85, side=-1, dir=(0.97, 0.08, -0.22), up=(-0.10, -0.40, 0.91),
              kw=dict(curl=(0.62, 0.68, 0.74, 0.80), joints=(0.35, 1.0, 0.9), spread=0.06, thumb_abd=0.22,
                      thumb_curl=0.12, thumb_flex=-1.00),
              wrist=(-27.0, 1.0), elbow=(-48.0, 19.0))


def _konrad_arms(M, tf, zoom, ox=BOX_K[0], oy=BOX_K[1]):
    """Left arm: down from the shoulder to the elbow on the near table edge, the forearm along the table, the
    hand hooked round the cup handle (back of the hand toward us, four fingers, the thumb along the top of the
    handle).  Right arm: the elbow out on the armrest of the club chair."""
    w = 0.96
    sh_l = to_img(tf, zoom, (25.5 * w, 18.0, -2.5))
    sh_r = to_img(tf, zoom, (-25.5 * w, 18.0, -2.5))
    cx, cy = K_CUP[0] - ox, K_CUP[1] - oy                        # cup foot in figure pixels
    kh = K_HAND
    el = np.array([cx + kh['elbow'][0], cy + kh['elbow'][1], sh_l[2] - 10.0])
    wr = np.array([cx + kh['wrist'][0], cy + kh['wrist'][1], sh_l[2] - 24.0])
    # NB view space has y down: hand(side=+1) is a LEFT hand
    arm_l, pl = R.sleeve_arm(M, 'sleeve', sh_l + np.array([2.0, 4.0, -3.0]), el, wr, (12.2, 9.4, 6.8),
                             cuff='shirt', cuff_len=5.0, cuff_r=5.0, skin='hand', hand_s=kh['s'], side=kh['side'],
                             hand_dir=kh['dir'], hand_up=kh['up'], hand_kw=dict(kh['kw']), folds=3, fold_amp=0.12,
                             wrist_r=1.75 * kh['s'])
    # right (near) arm: elbow out over the armrest, forearm forward out of sight
    el_r = np.array([sh_r[0] + 31.0, sh_r[1] + 44.0, sh_r[2] + 6.0])
    wr_r = np.array([sh_r[0] - 22.0, sh_r[1] + 60.0, sh_r[2] - 44.0])
    arm_r, pr = R.sleeve_arm(M, 'sleeve', sh_r + np.array([-2.0, 4.0, -3.0]), el_r, wr_r, (13.8, 12.0, 9.5),
                             cuff=None, skin='hand', hand_s=2.2, side=1, hand_kw=dict(curl=(0.4,) * 4),
                             folds=2, fold_amp=0.14)
    return [R.bounded(arm_l, [sh_l, el, wr, pl['hand_tip']], 30.0),
            R.bounded(arm_r, [sh_r, el_r, wr_r, pr['hand_tip']], 30.0)], dict(left=pl, right=pr)


_A_ARMS = {}


def _alexei_arms(M, tf, zoom, ox=BOX_A[0], oy=BOX_A[1]):
    """Right arm (near side, screen right): from the shoulder down to the elbow at the table edge, the forearm
    along the table, the right fist closed round the vertical bar of the tea-glass holder's handle (back of the
    hand toward us, the fingers stacked, the thumb on top of the handle).  Left arm (far side): the elbow out to
    the left, the forearm on his knee out of sight."""
    w = 1.05
    sh_r = to_img(tf, zoom, (-25.5 * w, 18.0, -2.5))            # character right -> screen right
    sh_l = to_img(tf, zoom, (25.5 * w, 18.0, -2.5))
    hx, hy = TEA[0] - 11 - ox, TEA[1] - 8 - oy                  # the handle's vertical bar, figure pixels
    ah = A_HAND
    el = np.array([hx + ah['elbow'][0], hy + ah['elbow'][1], sh_r[2] - 6.0])
    wr = np.array([hx + ah['wrist'][0], hy + ah['wrist'][1], sh_r[2] - 13.0])
    # view space has y down: hand(side=-1) is a RIGHT hand
    arm_r, pr = R.sleeve_arm(M, 'sleeve', sh_r + np.array([-2.0, 4.0, -3.0]), el, wr, (13.4, 10.6, 7.4),
                             cuff='shirt', cuff_len=5.0, cuff_r=5.4, skin='hand', hand_s=ah['s'], side=ah['side'],
                             hand_dir=ah['dir'], hand_up=ah['up'], hand_kw=dict(ah['kw']), folds=2, fold_amp=0.10,
                             wrist_r=1.75 * ah['s'])
    # the handle's bar in the fist (nickel silver, lit by the tea), just behind the fingers
    zf = pr['hand_frame'].o[2] - 3.5 if hasattr(pr['hand_frame'], 'o') else wr[2] - 8.0
    bar = RC((hx + 0.5, hy - 3.5, zf), (hx + 0.5, hy + 3.5, zf), 0.75, 0.75, M('handle'))
    arms_ = [hx + 0.5, hy - 3.5, hx + 4.5, hy - 4.5], [hx + 0.5, hy + 3.5, hx + 4.5, hy + 4.5]
    bows = [RC((a[0], a[1], zf), (a[2], a[3], zf), 0.65, 0.65, M('handle')) for a in arms_]
    el_l = np.array([sh_l[0] - 30.0, sh_l[1] + 46.0, sh_l[2] + 4.0])
    wr_l = np.array([sh_l[0] + 18.0, sh_l[1] + 62.0, sh_l[2] - 44.0])
    arm_l, pl = R.sleeve_arm(M, 'sleeve', sh_l + np.array([2.0, 4.0, -3.0]), el_l, wr_l, (14.2, 12.4, 9.8),
                             cuff=None, skin='hand', hand_s=2.2, side=1, hand_kw=dict(curl=(0.4,) * 4),
                             folds=1, fold_amp=0.12)
    _A_ARMS['axes'] = [(sh_r, el), (el, wr), (sh_l, el_l), (el_l, wr_l)]
    return [R.bounded(arm_r, [sh_r, el, wr, pr['hand_tip']], 30.0),
            S.Union([bar] + bows),
            R.bounded(arm_l, [sh_l, el_l, wr_l, pl['hand_tip']], 30.0)], dict(right=pr, left=pl)


def _line_px(a, b):
    """Integer pixels of the segment a -> b (2D), one per step of the longer axis."""
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    out = []
    for k in range(n + 1):
        t = k / max(1, n)
        out.append((int(math.floor(a[0] + (b[0] - a[0]) * t)), int(math.floor(a[1] + (b[1] - a[1]) * t)),
                    a[2] + (b[2] - a[2]) * t))
    return out


def finger_marks(rgba, res, hf, s, side, kw, dark=0.60, light=1.10, ztol=2.2, start=0.25):
    """Round 10b: the gaps between the fingers and the knuckle lights of a small hand, drawn along the projected
    finger axes of rig.hand_axes (the SDF hand alone shades into a mitten at 15-25 px).  A gap line runs between
    neighbouring fingers from just past the knuckles to the shorter tip; it is only drawn on hand pixels whose depth
    matches the line (a curled-away finger leaves no line on the back of the hand).  Each knuckle gets one lit
    pixel."""
    names = res['names']
    ids = [names.index(n) for n in ('hand', 'hand_a', 'hand_b', 'hand_t') if n in names]
    mat = res['mat']
    z = res['z'] if 'z' in res else res['d'].z
    out = rgba.copy()
    h, w = mat.shape
    ax = R.hand_axes(s, side=side, **kw)
    view = [([hf.to_view(p) for p in pts], r) for pts, r in ax]

    def ok(x, y, zz):
        return 0 <= x < w and 0 <= y < h and mat[y, x] in ids and out[y, x, 3] > 0 and abs(z[y, x] - zz) < ztol

    done = set()
    for i in range(3):
        a, _ = view[i]
        b, _ = view[i + 1]
        mids = [(a[j] + b[j]) / 2.0 for j in range(len(a))]
        mids[0] = mids[0] + (mids[1] - mids[0]) * start
        for j in range(len(mids) - 1):
            for (x, y, zz) in _line_px(mids[j], mids[j + 1]):
                if (x, y) in done:
                    continue
                if ok(x, y, zz + 0.8):
                    out[y, x, :3] = np.clip(out[y, x, :3].astype(float) * dark, 0, 255).astype(np.uint8)
                    done.add((x, y))
    for i in range(4):
        pts, r = view[i]
        k = pts[0] + hf.dir_to_view(np.array([0.0, -0.1 * s, 0.9 * r]))
        x, y = int(math.floor(k[0])), int(math.floor(k[1]))
        if ok(x, y, k[2]) and (x, y) not in done:
            out[y, x, :3] = np.clip(out[y, x, :3].astype(float) * light + 6, 0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------------------------- Konrad (t1)
def _club_chair(M, tf, zoom, ox=BOX_K[0], oy=BOX_K[1]):
    """The buttoned back and the right armrest of the saloon car's club chair (in front of his lower back)."""
    m = M('chair')
    mn = M('nail')
    hip = to_img(tf, zoom, (0.0, 70.0, -16.0))
    cx = hip[0] + 2.0
    top = 190.0                                                  # figure px: the chair back's top edge
    zc = hip[2] + 16.0
    back = S.RoundBox((cx, top + 40.0, zc), (78.0, 40.0, 8.0), 9.0, m)
    roll = S.RoundCone((cx - 78.0, top + 4.0, zc + 2.0), (cx + 78.0, top + 4.0, zc + 2.0), 9.5, 9.5, m)
    parts = [back, roll]
    # buttons of the capitonnage (dimples) and the brass nails along the edge
    tufts = []
    for row, yv in enumerate((top + 20.0, top + 36.0)):
        for k in range(-4, 5):
            xv = cx + k * 17.0 + (8.5 if row % 2 else 0.0)
            tufts.append(S.Sphere((xv, yv, zc + 9.6), 2.2, m))
    node = S.Sub(S.Union(parts, k=4.0), S.Union(tufts), k=1.6)
    nails = [S.Sphere((cx + k * 6.0, top + 13.0, zc + 9.2), 0.95, mn) for k in range(-12, 13)]
    return [S.Bound(S.Union([node] + nails, k=0.0), np.array([cx, top + 40.0, zc]), 120.0, margin=3.0)]


def konrad_look():
    return dict(key=(-0.78, 0.40, -0.48), rim=(0.05, -0.62, -0.78), ambient=0.06, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(0.2, -0.8, 0.6), ao=0.5)


def seated_konrad(turn=0, breath=0, ss=3):
    """Konrad from behind-right at the saloon-car window (see the module doc).  breath = 1 lifts head and
    shoulders by about a pixel; the hand on the cup and the chair stay put."""
    zoom = 1.62
    ox, oy = BOX_K[0], BOX_K[1]
    lift = 1.0 if breath else 0.0
    head_px = (82.0 + 363 - ox, 58.0 - lift)
    torso_px = (84.0 + 363 - ox, 100.0 - lift * 0.8)
    head_items = [lambda M, hp: fedora_cut(M, hp, y0=-13.2),
                  lambda M, hp: hat_band(M),
                  lambda M, hp: CC.hair_short(M, hp, nape=10.5, back_z=-10.0, thick=0.85),
                  lambda M, hp: nape(M, c=(0.0, 5.5, -9.0), r=(9.5, 4.6, 5.0))]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: coat_back(M, t, w=0.97),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape'),
                   lambda M, t: band_back(M, coat_back(M, t, w=0.97), 0.9, (0.0, 62.0), 0.0, 5.0, 'belt',
                                          x_range=(-15.0, 15.0)),
                   lambda M, t: S.Union([S.Sphere((sx * 13.0, 62.0, -18.4), 1.5, M('button')) for sx in (1, -1)])]
    yaw = 198.0 + (9.0 if turn else 0.0)
    lamp = (K_LAMP[0] - ox, K_LAMP[1] - oy - 2.0, -6.0)
    table = (K_CUP[0] - ox + 14.0, K_CUP[1] - oy + 18.0, -10.0)        # light bounced off the polished top
    near = ('hand', 'hand_a', 'hand_b', 'hand_t', 'shirt', 'sleeve')
    lights = [(lamp, 0.75, 230.0, None),
              dict(pos=lamp, gain=0.95, radius=150.0, mats=near, wrap=0.45, power=1.0),
              dict(pos=table, gain=0.35, radius=60.0, mats=near, wrap=0.3, power=1.2, shadow=False)]
    tone = [CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3), CC.pass_grain('coat', 0.04, seed=4),
            pass_hair_back('hair'), R.pass_seam('coat', 'sleeve'), R.pass_seam('sleeve', 'coat'),
            pass_back_seam('coat', y0=14.0, vent=78.0),
            R.pass_part_lines('hand')] + HAND_SEAMS
    # the chair does not breathe: it is placed from the resting torso frame
    tf_rest = S.Frame(_pre((84.0 + 363 - ox, 100.0, 0.0), zoom), S.rot(192.0, 6.0, 0))
    return _render_seated('konrad', turn, (BOX_K[2], BOX_K[3]), zoom, head_px, torso_px, yaw,
                          4.0 + (2.0 if turn else 0.0), 192.0, 6.0 - lift * 0.6,
                          dict(width=0.96, depth=1.0, slope=1.25, lean=2.0), head_items, torso_items,
                          _konrad_arms, konrad_look(), konrad_styles(), tone, lights,
                          extra_fn=lambda M, tf, zm: _club_chair(M, tf_rest, zm),
                          cache=('seated_konrad_v10', turn, breath, ss), ss=ss,
                          post=lambda r: finger_marks(r['rgba'], r, r['pts']['left']['hand_frame'], K_HAND['s'],
                                                      K_HAND['side'], K_HAND['kw']))


# ---------------------------------------------------------------------------------------------- Alexei (t3)
def pass_rings(mat, axes, period=4.6, dark=1):
    """Quilting of a padded sleeve: stitched rings across the arm.  axes = [(a, b)] segments of the arm in
    figure pixels (view space); a pixel's ring index is its distance along the nearest segment / period."""
    segs = [(np.asarray(a, float), np.asarray(b, float)) for a, b in axes]

    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names or not segs:
            return tone
        d = G['d']
        m = (d.mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        Pp = d.P[m].astype(float)
        best = np.full(len(Pp), 1e9)
        along = np.zeros(len(Pp))
        for a, b in segs:
            ab = b - a
            L2 = float(ab @ ab)
            t = np.clip(((Pp - a) @ ab) / L2, 0, 1)
            q = a + t[:, None] * ab
            dist = np.linalg.norm(Pp - q, axis=1)
            take = dist < best
            best = np.where(take, dist, best)
            along = np.where(take, t * math.sqrt(L2), along)
        f = (along / period) % 1.0
        line = (f < 0.16) | (f > 0.94)
        t_ = tone[m].copy()
        t_ = np.where(line, np.maximum(0, t_ - dark), t_)
        tone = tone.copy()
        tone[m] = t_
        return tone
    return fn


def alexei_look():
    return dict(key=(0.80, 0.25, -0.55), rim=(-0.05, -0.62, -0.78), ambient=0.06, wrap=0.10, bg='karsk',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(-0.2, -0.8, 0.6), ao=0.5)


def seated_alexei(turn=0, breath=0, ss=3):
    """Alexei from behind-left at the window of the Soviet compartment (see the module doc)."""
    zoom = 1.62
    ox, oy = BOX_A[0], BOX_A[1]
    lift = 1.0 if breath else 0.0
    head_px = (118.0 + 96 - ox, 60.0 - lift)
    torso_px = (114.0 + 96 - ox, 102.0 - lift * 0.8)
    head_items = [lambda M, hp: CC.ushanka(M, hp, flaps='down'),
                  lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0, nape=10.5,
                                              back_z=-10.0, thick=0.9),
                  lambda M, hp: nape(M, c=(0.0, 5.0, -9.0), r=(9.0, 4.4, 5.0))]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=12.0, collar_r=(13.4, 14.8)),
                   lambda M, t: CC.quilted(coat_back(M, t, w=0.93, drape=0.96), period=5.0, amp=0.5),
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8)),
                   lambda M, t: band_back(M, S.Union([S.Offset(t, 2.6), coat_back(M, t, w=0.93, drape=0.96)], k=6.0),
                                          1.5, (6.0, 30.0), 50.0, 3.4, 'strap', y_range=(4.0, 96.0))]
    yaw = 160.0 - (9.0 if turn else 0.0)
    lamp = (A_LAMP[0] - ox, A_LAMP[1] - oy, -40.0)
    tea = (TEA[0] - ox - 2.0, TEA[1] - oy - 16.0, 8.0)            # the amber tea glowing in its glass
    near = ('hand', 'hand_a', 'hand_b', 'hand_t', 'shirt', 'sleeve', 'handle')
    lights = [(lamp, 0.55, 320.0, None),
              dict(pos=lamp, gain=0.55, radius=260.0, mats=near, wrap=0.45, power=1.0),
              dict(pos=tea, gain=0.75, radius=64.0, mats=near, wrap=0.5, power=1.1, shadow=False)]

    def rings(spec, G, tone, v):
        return pass_rings('sleeve', _A_ARMS.get('axes', []), period=4.6)(spec, G, tone, v)
    tone = [CC.pass_fur('fur'), CC.pass_stitches('coat', 5.0), pass_hair_back('hair'), CC.pass_knit('knit', ribs=30),
            CC.pass_knit('shirt', ribs=16), rings, R.pass_seam('coat', 'sleeve'), R.pass_part_lines('hand')] + HAND_SEAMS
    return _render_seated('alexei', turn, (BOX_A[2], BOX_A[3]), zoom, head_px, torso_px, yaw,
                          4.0 + (2.0 if turn else 0.0), 168.0, 6.0 - lift * 0.6,
                          dict(width=1.05, depth=1.05, slope=1.0, lean=2.0), head_items, torso_items,
                          _alexei_arms, alexei_look(), alexei_styles(), tone, lights,
                          cache=('seated_alexei_v4', turn, breath, ss), ss=ss,
                          groups={'handle': 12},
                          post=lambda r: finger_marks(r['rgba'], r, r['pts']['right']['hand_frame'], A_HAND['s'],
                                                      A_HAND['side'], A_HAND['kw']))


# ------------------------------------------------------------------------------------------------ sheets
def fig_konrad_sheet(layout=None, ss=3):
    """4 frames [turn0, turn0 + breath, turn1, turn1 + breath] for ch3_trains.gd (hframes = 4); sets
    layout['fig_konrad'] (top-left of the frame on screen) and layout['fig_frames']."""
    frames = [seated_konrad(t, b, ss=ss)['rgba'] for t in (0, 1) for b in (0, 1)]
    if layout is not None:
        layout['fig_konrad'] = [BOX_K[0], BOX_K[1]]
        layout['fig_frames'] = 4
    return np.concatenate(frames, axis=1)


def fig_alexei_sheet(layout=None, ss=3):
    frames = [seated_alexei(t, b, ss=ss)['rgba'] for t in (0, 1) for b in (0, 1)]
    if layout is not None:
        layout['fig_alexei'] = [BOX_A[0], BOX_A[1]]
    return np.concatenate(frames, axis=1)


def _shadow_on(p, x0, y0, x1, y1, half, dark):
    """Soft contact shadow on the table-top band (rows y0..y1) under an arm / hand spanning x0..x1."""
    yy, xx = p.yy, p.xx
    m = (yy >= y0) & (yy < y1) & (xx >= x0 - half) & (xx < x1 + half)
    edge = np.clip(np.minimum(xx - (x0 - half), (x1 + half) - xx) / max(1.0, half), 0, 1)
    p.add(m, -dark * edge * np.clip(1 - (yy - y0) / max(1.0, (y1 - y0) * 1.6), 0.25, 1))


def reach_shadow_k(p, lamp=None):
    """Konrad's forearm and hand darken the polished table top under them (painted into int_konrad, under
    the figure sprite): from the cup handle out to the near edge."""
    _shadow_on(p, K_CUP[0] + 8, K_CUP[1], K_CUP[0] + 64, K_CUP[1] + 8, 4.0, 1.4)


def reach_shadow_a(p, lamp=None):
    """Alexei's forearm and hand on the laminate (painted into int_alexei, under the figure sprite)."""
    _shadow_on(p, TEA[0] - 60, TEA[1], TEA[0] - 10, TEA[1] + 7, 4.0, 1.2)


# ---------------------------------------------------------------------------------------------- Konrad walking
# LS_C3_ToHall k2 (round 10b): Konrad walks in under the palais clock as a FULL figure.  Round 10 framed him so
# large (a 150 px bust-and-torso placed at y 224) that the letterbox cut him off at the chest -- no hands, no legs --
# and he never reached the clock.  Now he is a whole man of ~112 px (hat to soles; the extras by the wainscot are
# 84-92 px, he walks nearer the camera at the front of the floor), in profile from his right side, walking right
# at a natural pace (one step = WALK_STEP_PX, one cycle = WALK_STRIDE px of floor = 1.1 s in ch3_tohall.gd):
#   legs     solved per frame by two-bone IK from the hip to an ankle that follows the gait table: the planted
#            foot slides back exactly one stride per cycle (no skating), heel strike with the toes up, flat foot,
#            heel off, toe off pivoting on the ball of the foot, the swing with the knee folding past the stance
#            leg; the hip rises on the passing steps (bob from the geometry, ~4 px)
#   arms     swing against the legs from the shoulder, the elbow bending on the forward swing; relaxed hands
#   coat     the long navy coat opens over the forward thigh and trails behind; trousers and shoes show below
#   tube     the drafting tube rides on its strap across his back
# Lit by the chandelier (warm key from the front, high) with a continuous cold rim on his back from the tall
# windows and a warm rim along the top of the hat and the shoulders (contour_rim: drawn along the outline, never
# the dashed per-pixel rim of round 10).
WALK_FRAMES = 8
WALK_SIZE = (76, 122)                # two rows under the soles for his shadow on the marble
WALK_ZOOM = 0.275                    # one bust head (52 units) = 14.3 px
WALK_STEP_PX = 44.0                  # one step on the floor (px)
WALK_STRIDE = 2.0 * WALK_STEP_PX     # one cycle = two steps
WALK_HIP_X = 36.0
WALK_ANCHOR = (36, WALK_SIZE[1] - 3)  # the soles' line under the hip: the runtime path is given in soles

# per frame of ONE leg's own cycle (0 = its heel strike): ankle track on the floor as a fraction of a step
# (+ = forward of the hip), lift of the ankle in heads (swing only), foot angle (deg, + = toes up), pivot on the floor
_GAIT = ((0.50, 0.00, 15.0, 'heel'),
         (0.25, 0.00, 0.0, 'flat'),
         (0.00, 0.00, 0.0, 'flat'),
         (-0.25, 0.00, 0.0, 'flat'),
         (-0.50, 0.00, -15.0, 'toe'),
         (-0.75, 0.00, -40.0, 'toe'),
         (-0.15, 0.40, -12.0, None),
         (0.38, 0.16, 6.0, None))


def _rot2(v, deg):
    """Rotate a 2D view vector (y down) by deg, + = counter-clockwise on screen (toes up)."""
    a = math.radians(deg)
    return np.array([v[0] * math.cos(a) + v[1] * math.sin(a), -v[0] * math.sin(a) + v[1] * math.cos(a)])


def _foot(hd):
    """Heel and toe points of the sole relative to the ankle of a flat foot (px, y down)."""
    return np.array([-0.25 * hd, 0.28 * hd]), np.array([0.86 * hd, 0.28 * hd])


def gait_ankle(fr, hd, step):
    """(ankle (x, y) with the floor at y = 0 and x relative to the hip, foot angle) for frame fr of a leg's cycle."""
    tr, lift, ang, pivot = _GAIT[fr % len(_GAIT)]
    heel, toe = _foot(hd)
    flat = np.array([tr * step, -heel[1]])
    if pivot == 'heel':
        a = (flat + heel) - _rot2(heel, ang)
    elif pivot == 'toe':
        a = (flat + toe) - _rot2(toe, ang)
    else:
        a = flat - np.array([0.0, lift * hd])
    return a, ang


def leg_ik(hip, ankle, L1, L2):
    """Knee of a two-bone leg from hip to ankle (2D view, y down), bending forward (+x).  Returns (knee, ankle)
    (the ankle pulled in if out of reach)."""
    d = ankle - hip
    dist = float(np.linalg.norm(d))
    reach = L1 + L2 - 0.05
    u = d / max(dist, 1e-6)
    if dist > reach:
        ankle = hip + u * reach
        dist = reach
    ca = (L1 * L1 + dist * dist - L2 * L2) / (2.0 * L1 * dist)
    a = math.acos(max(-1.0, min(1.0, ca)))
    n = np.array([u[1], -u[0]])                     # perpendicular toward the front for a leg pointing down
    if n[0] < 0:
        n = -n
    knee = hip + (u * math.cos(a) + n * math.sin(a)) * L1
    return knee, ankle


def walk_styles():
    """Konrad's colours of the dialogue portraits and the in-game sheet (navy coat, taupe felt, camel scarf, dark
    trousers, black shoes, the brown drafting tube with brass caps) on ramps that end in the chandelier's warm
    light."""
    st = konrad_styles()
    navy = ['#04060b', '#080d18', '#0e1526', '#151f37', '#1e2b4a', '#2a3a5e', '#384b74']
    warm = ['#66667a']
    st['coat'] = MatStyle(ramp(*(navy + warm)), [0.05, 0.10, 0.17, 0.27, 0.40, 0.56, 0.80], dither=0.02, rim='#5f7d9e')
    st['sleeve'] = MatStyle(ramp(*(navy[1:] + ['#43588a'] + warm)), [0.05, 0.10, 0.17, 0.27, 0.40, 0.56, 0.80],
                            dither=0.02, rim='#5f7d9e')
    st['coat_lapel'] = st['coat']
    # dark brown hair that still shows its colour under the hat (pure black read as a visor across the face)
    st['hair'] = MatStyle(ramp('#0d0b0e', '#1a1416', '#2a1f1e', '#3e2c26', '#5a3e2e', '#7a5638'),
                          [0.04, 0.10, 0.2, 0.34, 0.52], rim='#5f7d9e')
    st['legs'] = MatStyle(ramp('#040508', '#090b11', '#10131b', '#181c27', '#232836', '#353a4a', '#575464'),
                          [0.05, 0.11, 0.2, 0.32, 0.48, 0.68], rim='#5f7d9e')
    st['shoe'] = MatStyle(ramp('#030303', '#08070a', '#120f12', '#1e1819', '#33282a', '#5a4038'),
                          [0.06, 0.14, 0.26, 0.42, 0.62], rim='#7f93a0')
    st['strap'] = MatStyle(ramp('#050304', '#0f0a08', '#1c120c', '#2e1c12', '#4a2e1c', '#74482a'),
                           [0.06, 0.14, 0.26, 0.42, 0.62], rim='#6a86a0')
    st['tube'] = MatStyle(ramp('#050304', '#0e0907', '#1a110b', '#28190f', '#3c2616', '#5a3a20', '#82562e'),
                          [0.05, 0.11, 0.2, 0.32, 0.48, 0.68], rim='#6a86a0')
    # the far arm and leg one step darker (in the body's shadow): the alternation reads in profile
    st['sleeve_far'] = MatStyle(ramp(*navy[:6]), [0.06, 0.13, 0.24, 0.38, 0.58], dither=0.02, rim='#5f7d9e')
    st['legs_far'] = MatStyle(ramp('#030407', '#07090e', '#0d1017', '#141822', '#1d2230', '#2c3040'),
                              [0.06, 0.13, 0.24, 0.38, 0.58], rim='#5f7d9e')
    st['shoe_far'] = MatStyle(ramp('#020202', '#060508', '#0e0b0e', '#181314', '#2a2022'), [0.07, 0.16, 0.3, 0.5],
                              rim='#7f93a0')
    st['cap'] = MatStyle(ramp('#0a0805', '#1e160a', '#3a2a12', '#6a4e22', '#a07c3c', '#d4ac62'),
                         [0.05, 0.12, 0.24, 0.42, 0.62], rim='#8aa0b4')
    return R.hand_styles(st)


def standing_torso(M, mat='body', depth=1.0, width=1.0, skirt=True):
    """A standing man's trunk in realistic proportions (unit = the bust head: 52 = one head; y down from the pit
    of the neck, z forward): shoulders two heads wide with the deltoids, chest, waist, hips (and, unless skirt is
    False, the coat skirt hanging to the knees).  The bust torso (chargen_portrait2_anat.build_torso) is far too
    narrow for full figures."""
    m = M(mat)
    w, d = width, depth
    parts = [E((0.0, 13.0, -3.0), (38.0 * w, 12.0, 20.0 * d), m),                 # shoulder girdle
             E((36.0 * w, 18.0, -3.0), (12.5, 15.0, 15.0 * d), m),                 # deltoids
             E((-36.0 * w, 18.0, -3.0), (12.5, 15.0, 15.0 * d), m),
             E((0.0, 36.0, 1.5), (34.0 * w, 26.0, 23.0 * d), m),                   # chest
             E((0.0, 68.0, -0.5), (30.0 * w, 22.0, 21.0 * d), m),                  # waist
             E((0.0, 98.0, 0.0), (32.0 * w, 22.0, 22.0 * d), m)]                   # hips
    if skirt:
        parts.append(E((0.0, 150.0, 0.5), (34.0 * w, 46.0, 23.5 * d), m))         # coat skirt
    return S.Union(parts, k=7.0)


def _blur5(a):
    k = np.array([1.0, 4.0, 6.0, 4.0, 1.0], np.float32) / 16.0
    p = np.pad(a, 2, mode='edge')
    h, w = a.shape
    b = sum(k[i] * p[2:2 + h, i:i + w] for i in range(5))
    p = np.pad(b, ((2, 2), (0, 0)), mode='edge')
    return sum(k[i] * p[i:i + h, :] for i in range(5))


def contour_rim(rgba, light2d, color, strength=0.85, lo=0.3, protect=None):
    """A rim light drawn ALONG the outline: every outline pixel (opaque, with a transparent 4-neighbour) whose
    outward normal (from the blurred alpha) faces the 2D light direction (x right, y down) is blended toward
    `color`, fading in from dot = lo.  Neighbouring outline pixels have nearly the same normal, so the rim runs as
    one unbroken line (the per-pixel shading rim breaks into dashes on small figures).  protect: bool mask of
    pixels to leave alone."""
    a = rgba[..., 3] > 0
    b = _blur5(a.astype(np.float32))
    gy, gx = np.gradient(b)
    nx, ny = -gx, -gy
    nn = np.hypot(nx, ny) + 1e-6
    L = np.asarray(light2d, float)
    L = L / np.linalg.norm(L)
    dot = (nx * L[0] + ny * L[1]) / nn
    p = np.pad(a, 1)
    edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    m = edge & (dot > lo)
    if protect is not None:
        m &= ~protect
    t = (np.clip((dot - lo) / (1.0 - lo), 0, 1) * strength)[m][:, None]
    out = rgba.copy()
    c = np.asarray(color, float)[None, :]
    out[m, :3] = np.clip(out[m, :3].astype(float) * (1 - t) + c * t, 0, 255).astype(np.uint8)
    return out


def hero_face_marks(rgba, mat, names, hf, zoom, lm, hair=(40, 30, 28), side='r'):
    """The near eye, brow and mouth of a small portrait-pipeline head (walking figures: one head ~14 px), at the
    projected landmarks of chargen_portrait2_anat.build_head, painted on skin only and darkening the lit skin
    (the bust pipeline's eye stamps are made for 112 px busts)."""
    skin_ids = [names.index(n) for n in ('skin', 'lip') if n in names]
    if not skin_ids:
        return rgba
    out = rgba.copy()
    h, w = mat.shape

    def at(key, dy=0.0):
        p = to_img(hf, zoom, np.asarray(lm[key], float))
        return int(math.floor(p[0])), int(math.floor(p[1] + dy))

    def put(x, y, f, tint=None, mix=0.0):
        if 0 <= x < w and 0 <= y < h and mat[y, x] in skin_ids and out[y, x, 3] > 0:
            c = out[y, x, :3].astype(float) * f
            if tint is not None:
                c = c * (1 - mix) + np.asarray(tint, float) * mix
            out[y, x, :3] = np.clip(c, 0, 255).astype(np.uint8)
    ex, ey = at('eye_' + side)
    put(ex, ey, 0.30)
    bx, by = at('brow_' + side, -0.6)
    by = min(by, ey - 2)
    put(bx, by, 0.55, hair, 0.5)
    put(bx + 1, by, 0.6, hair, 0.45)
    mx, my = at('mouth_' + side)
    put(mx, my, 0.62)
    return out


def floor_shadow(rgba, ankles, sole_row, hd, dx=-2.0):
    """A contact shadow on the floor under a walking figure (the chandelier is high in front of him: the shadow is
    short and falls a little behind): an ellipse round both feet on the soles' row and the row below, two alpha steps,
    only where the figure itself does not cover."""
    out = rgba.copy()
    h, w = out.shape[:2]
    xs = [float(a[0]) for a in ankles]
    cx = (min(xs) + max(xs)) / 2.0 + dx
    rx = (max(xs) - min(xs)) / 2.0 + 0.95 * hd
    for y in range(int(sole_row) - 1, min(h, int(sole_row) + 3)):
        ry = (y - (sole_row + 0.6)) / 1.9
        for x in range(w):
            q = ((x + 0.5 - cx) / rx) ** 2 + ry * ry
            if q >= 1.0 or out[y, x, 3] > 0:
                continue
            out[y, x] = (10, 12, 16, 120 if q < 0.45 else 64)
    return out


def hat_band(M, y0=-13.2, z0=-5.2, tilt=(5.0, -3.0), band_r=(17.4, 21.6), half=2.5, lift=1.2):
    """A taller ribbon band round the crown of CC.fedora (same hat frame): the portrait band (3.5 units) shows
    as a broken 1-px line on small or back views; this one stands ~2 px clear of the brim."""
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = band_r
    band = S.EllipticCylinder((0, -half - 0.2, 0), rx + lift, rz + lift, half, M('ribbon'), e=0.4)
    return S.Xform(band, frame=hf)


def walking_konrad(frame, ss=3):
    """One frame (0..7; frame 0 = heel strike of his near/right foot) of Konrad's walk under the palais clock:
    a full figure, WALK_SIZE px, the soles on the bottom row under x = WALK_HIP_X at the contact frames."""
    spec = CC.konrad()
    zoom = WALK_ZOOM
    w, h = WALK_SIZE
    hd = 52.0 * zoom
    L1, L2 = 1.80 * hd, 1.70 * hd                     # thigh, shin (hip joint -> knee -> ankle)
    step = WALK_STEP_PX
    ground = WALK_ANCHOR[1] + 0.98                   # the soles' row; the two rows below hold the shadow
    # the hip rises on the passing steps (frames 2 and 6) and sinks at the double supports (0 and 4)
    h_mid, bob = 3.75 * hd, 0.31 * hd
    hip_h = h_mid - bob * (1.0 + math.cos(math.pi * frame / 2.0)) / 2.0
    hip = np.array([WALK_HIP_X, ground - hip_h])
    legs2 = {}
    for side, off in (('n', 0), ('f', 4)):
        a, ang = gait_ankle(frame + off, hd, step)
        ank = np.array([WALK_HIP_X + a[0], ground + a[1]])
        kn, ank = leg_ik(hip, ank, L1, L2)
        legs2[side] = (kn, ank, ang)
    torso_px = (WALK_HIP_X + 0.10 * hd, hip[1] - 2.45 * hd)
    head_px = (torso_px[0] + 0.30 * hd, torso_px[1] - 0.66 * hd)
    phase = 2 * math.pi * frame / WALK_FRAMES
    swing = math.cos(phase)                           # +1: near leg forward -> near arm back
    M = A.Mats()
    for nm in ('skin', 'lip', 'ear', 'neck'):
        M(nm)
    torso = standing_torso(M, 'body', depth=1.05, skirt=False)
    head_items = [lambda M, hp: fedora_cut(M, hp, y0=-13.2),
                  lambda M, hp: hat_band(M),
                  lambda M, hp: CC.hair_short(M, hp, nape=10.5, back_z=-10.0, thick=0.85)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.30, v_top=3.0, collar_h=14.0, collar_r=(13.0, 15.5)),
                   lambda M, t: CC.scarf_wrap(M, y=-8.0, r=11.5, tube=5.0, ends=True,
                                              end_pts=[(-3.0, -2.0, 18.0), (-5.0, 12.0, 22.0), (-6.0, 30.0, 23.5)])]
    tyaw = 90.0 - 5.0 * swing                         # the shoulders turn against the hips
    scaled, hp, lm, hf, tf = _head_and_torso(spec, M, zoom, head_px, torso_px, 84.0, 0.5, 0.0,
                                             tyaw, 3.0, torso, head_items, torso_items)
    parts = [scaled]
    # ---- legs: trousers and shoes (near leg toward the camera)
    heel, toe = _foot(hd)
    leg_nodes = []
    for side, z in (('n', 0.30 * hd), ('f', -0.30 * hd)):
        lm_ = M('legs' if side == 'n' else 'legs_far')
        sm = M('shoe' if side == 'n' else 'shoe_far')
        kn, ank, ang = legs2[side]
        H3 = np.array([hip[0], hip[1], z])
        K3 = np.array([kn[0], kn[1], z * 0.85])
        A3 = np.array([ank[0], ank[1], z * 0.80])
        leg_nodes += [RC(tuple(H3), tuple(K3), 0.27 * hd, 0.20 * hd, lm_),
                      RC(tuple(K3), tuple(A3), 0.20 * hd, 0.155 * hd, lm_)]
        hc = ank + _rot2(heel + np.array([0.07 * hd, -0.13 * hd]), ang)
        tc = ank + _rot2(toe + np.array([-0.12 * hd, -0.11 * hd]), ang)
        inst = ank + _rot2(np.array([0.22 * hd, 0.02 * hd]), ang)
        leg_nodes += [RC((hc[0], hc[1], A3[2]), (tc[0], tc[1], A3[2]), 0.16 * hd, 0.115 * hd, sm),
                      E((inst[0], inst[1], A3[2]), (0.30 * hd, 0.15 * hd, 0.16 * hd), sm)]
    parts.append(S.Bound(S.Union(leg_nodes, k=0.12 * hd), np.array([hip[0], (hip[1] + ground) / 2, 0.0]), 70.0,
                         margin=3.0))
    # ---- the coat skirt: from the waist to just below the knees, opening over the forward thigh
    cm = M('coat')
    Lc = L1 + 0.42 * hd
    hem_y = hip[1] + Lc - 0.15 * hd
    waist = np.array([hip[0] + 0.06 * hd, hip[1] - 0.75 * hd, 0.0])
    skirt = [RC(tuple(waist), (hip[0] - 0.10 * hd, hip[1] + Lc, 0.0), 0.54 * hd, 0.44 * hd, cm)]
    for side, z in (('n', 0.20 * hd), ('f', -0.20 * hd)):
        kn = legs2[side][0]
        tdir = R.nrm(np.array([kn[0] - hip[0], kn[1] - hip[1]]))
        d = R.nrm(0.40 * np.array([0.0, 1.0]) + 0.60 * tdir)
        bot = np.array([hip[0] + d[0] * Lc * 1.05, hip[1] + d[1] * Lc * 1.05])
        skirt.append(RC((hip[0], hip[1] - 0.40 * hd, z), (bot[0], bot[1], z), 0.46 * hd, 0.36 * hd, cm))
    # a straight hem: the round ends of the cones cut off at the hem line
    parts.append(S.Inter(S.Union(skirt, k=0.30 * hd), S.Fn(lambda P, y=hem_y: P[:, 1] - y, cm)))
    # ---- arms: the near (right) arm swings against the near leg, the elbow bends on the forward swing
    La1, La2 = 1.40 * hd, 1.18 * hd
    sh_n = to_img(tf, zoom, (-35.0, 19.0, -3.0))       # his right shoulder: toward the camera
    sh_f = to_img(tf, zoom, (35.0, 19.0, -3.0))

    def chain(sh, a_deg, bend_deg):
        a = math.radians(a_deg)
        b = math.radians(a_deg + bend_deg)
        el = sh + np.array([math.sin(a) * La1, math.cos(a) * La1, 0.0])
        wr = el + np.array([math.sin(b) * La2, math.cos(b) * La2, 0.0])
        return el, wr
    a_n = -24.0 * swing
    el_n, wr_n = chain(sh_n, a_n, 8.0 + 26.0 * max(0.0, -swing))
    el_f, wr_f = chain(sh_f, -a_n, 8.0 + 26.0 * max(0.0, swing))
    el_f[2] -= 2.0
    wr_f[2] -= 3.0
    rs = zoom * 13.0
    hs = 0.75 * hd / 19.0                              # the hand: three quarters of a head
    arm_n, pn = R.sleeve_arm(M, 'sleeve', sh_n + np.array([0.0, 0.5, 2.0]), el_n, wr_n, (rs, rs * 0.82, rs * 0.68),
                             cuff='shirt', cuff_len=0.9, cuff_r=rs * 0.45, skin='hand', hand_s=hs, side=-1,
                             hand_dir=R.nrm(wr_n - el_n), hand_up=(0.0, 0.0, 1.0),
                             hand_kw=dict(curl=(0.30, 0.38, 0.45, 0.52), spread=0.12, thumb_abd=0.3,
                                          thumb_curl=0.2), folds=1, fold_amp=0.10, wrist_r=0.13 * hd)
    arm_f, pf = R.sleeve_arm(M, 'sleeve_far', sh_f, el_f, wr_f, (rs * 0.96, rs * 0.80, rs * 0.66), cuff=None,
                             skin='hand', hand_s=hs, side=1, hand_dir=R.nrm(wr_f - el_f), hand_up=(0.0, 0.0, -1.0),
                             hand_kw=dict(curl=(0.35, 0.42, 0.5, 0.55)), folds=0, wrist_r=0.13 * hd)
    parts += [R.bounded(arm_n, [sh_n, el_n, wr_n, pn['hand_tip']], 8.0),
              R.bounded(arm_f, [sh_f, el_f, wr_f, pf['hand_tip']], 8.0)]
    # ---- the drafting tube on its strap across his back (top cap behind the right shoulder, the lower end
    # behind the left hip); the strap runs over the right shoulder to the front
    t_top = to_img(tf, zoom, (-12.0, -16.0, -30.0))
    t_bot = to_img(tf, zoom, (14.0, 96.0, -34.0))
    tr = 0.56 * 8.5 * zoom / 0.64 * 1.15
    tube = RC(tuple(t_top), tuple(t_bot), tr, tr, M('tube'))
    cap_dir = R.nrm(t_top - t_bot)
    cl = 2.5 * zoom / 0.64 + 0.6
    caps = S.Union([RC(tuple(t_top - cap_dir * cl), tuple(t_top + cap_dir * 0.4), tr + 0.4, tr + 0.4, M('cap')),
                    RC(tuple(t_bot - cap_dir * 0.4), tuple(t_bot + cap_dir * cl), tr + 0.4, tr + 0.4, M('cap'))])
    s0 = to_img(tf, zoom, (-30.0, 2.0, -16.0))
    s1 = to_img(tf, zoom, (-24.0, 4.0, 18.0))
    s2 = to_img(tf, zoom, (8.0, 60.0, 26.0))
    sr = 0.75
    strap = S.Union([RC(tuple(t_top - cap_dir * 0.6), tuple(s0), sr, sr, M('strap')),
                     RC(tuple(s0), tuple(s1), sr, sr, M('strap')), RC(tuple(s1), tuple(s2), sr, sr, M('strap'))])
    parts += [S.Union([tube, caps]), strap]
    root = S.Union(parts, k=0.0)
    look = dict(key=(0.55, -0.62, 0.56), rim=(-0.86, -0.25, -0.45), ambient=0.06, wrap=0.12, bg='palais',
                glow=(0.8, 0.2), fill=0.06, fill_dir=(-0.3, -0.2, 1.0), ao=0.45)
    gr = dict(spec['groups'])
    gr.update({'sleeve': 9, 'hand': 10, 'hand_a': 10, 'hand_b': 10, 'hand_t': 10, 'tube': 11, 'cap': 11,
               'strap': 7, 'legs': 12, 'shoe': 13, 'legs_far': 14, 'shoe_far': 14, 'sleeve_far': 15})
    chand = (w + 40.0, -60.0, 30.0)                   # the chandelier, high to the right, in front of him

    def v_mul(v, d, Mm):
        return v * 0.84
    lights = [dict(pos=chand, gain=0.30, radius=520.0, mats=None, wrap=0.1, power=1.0, shadow=False)]
    res = R.render(root, M, (w, h), look, walk_styles(), groups=gr, priority={'brim': 2, 'cap': 2, 'hand': 3},
                   tone_passes=[R.pass_part_lines('hand', dark=1)],
                   G_extra=dict(hp=hp, lm=lm, hf=hf, tf=tf, zoom=zoom), lights=lights, ss=ss, rim=False,
                   v_mul=v_mul, cache_key=('walking_konrad_full_v2', frame, ss))
    rgba = contour_rim(res['rgba'], (-1.0, -0.25), (96, 124, 156), strength=0.80, lo=0.35)    # windows: cold
    rgba = contour_rim(rgba, (0.55, -1.0), (214, 160, 104), strength=0.55, lo=0.55)          # chandelier: warm
    rgba = hero_face_marks(rgba, res['mat'], res['names'], hf, zoom, lm, hair=(58, 40, 34))
    rgba = floor_shadow(rgba, [legs2['n'][1], legs2['f'][1]], WALK_ANCHOR[1], hd)
    return dict(res, rgba=rgba)


def k2_konrad_sheet(layout=None, ss=3):
    """WALK_FRAMES frames side by side for ch3_tohall.gd; layout: konrad_frames, konrad_anchor (soles in the
    frame), konrad_stride (px of floor per cycle), konrad_path ([[t, x, y], ...] of the soles: he is walking
    when the shot cuts in and is under the clock as it ends), konrad_y (frame top on the path, for older
    runtimes)."""
    frames = [walking_konrad(i, ss=ss)['rgba'] for i in range(WALK_FRAMES)]
    if layout is not None:
        path = [[3.0, 45.0, 311.0], [6.0, 285.0, 311.0]]
        layout['konrad_frames'] = WALK_FRAMES
        layout['konrad_anchor'] = list(WALK_ANCHOR)
        layout['konrad_stride'] = WALK_STRIDE
        layout['konrad_path'] = path
        layout['konrad_y'] = int(path[0][2]) - WALK_ANCHOR[1]
    return np.concatenate(frames, axis=1)
