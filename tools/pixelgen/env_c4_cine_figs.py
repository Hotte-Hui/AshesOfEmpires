"""env_c4_cine_figs -- hands and figures of the Chapter-4 cinematics (owner: cine stream, round 9).

Everything here is sculpted and lit by the signed-distance pipeline of the dialogue portraits (chargen_portrait2_*:
sphere tracer, material ramps, outlines, rims) through the helpers of env_c3p2_cine_hands (arm(), limb(), paint())
and env_veltrava_cine_figs (render(): head + bust of the cast specs) -- all imported read-only -- so the hands
carry the same materials and light as the rest of the cinematics.  No painted silhouettes.

  c1_lhand / c1_rhand   Konrad's gloved hands with the German half (left hand holds the card; the right thumb
                        runs down the perforated edge)
  c2_thumb              macro: the glove's thumb along the perforation
  c3_finger             macro: Alexei's bare index finger along the other (mirrored) edge
  c3_hand               close: Alexei's hand on the Russian half on the siding-office desk (quilted sleeve)
  c4_back(f)            Alexei from behind at the booth window, f 0 head down to the card, 1 looking up
  s1_pencil(f)          Alexei's right hand writing with a pencil (2 frames)
  s1_lev                Lev's left hand (darned cardigan, black sleeve protector, the missing fingertip) pushing
                        the card into the box
  s2_hand / s3_hand     a hand on the knob of a rubber stamp (Lev in Karsk / Registrator Fengler in Berlin)
  s3_hands_med          Fengler's two hands on the counter (medium shot): stamp hand + flat hand on a card
  v2_konrad(f)          Konrad from behind at the tram loop, f 0 arm down, 1 half raised, 2 raised (the
                        protect_marta variant waves to Ilse)
Renders are memoised on disk (key = pipeline sources + this file + call); ASHES_NO_CACHE=1 disables the cache.
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
import chargen_portrait2_sdf as S    # noqa: E402
import env_c3p2_cine_hands as H      # noqa: E402  (arm, limb, paint, frame_along; read-only)
import env_veltrava_cine_figs as F   # noqa: E402  (render, styles; read-only)
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]

E = S.Ellipsoid
RC = S.RoundCone
TH7 = [0.05, 0.12, 0.21, 0.32, 0.46, 0.62, 0.82]
SKIN_TH = [0.05, 0.11, 0.19, 0.30, 0.43, 0.60, 0.84]
_norm = H._norm


# ----------------------------------------------------------------------------------------- materials
def _styles(city):
    """Material styles; `city` 'karsk' = kerosene amber light, 'berlin' = dawn blue / fluorescent green."""
    if city == 'karsk':
        skin_a = ramp('#0a0b10', '#1c1718', '#35231f', '#563428', '#7e4c32', '#a86a40', '#cc8e56', '#ecba7c')
        skin_l = ramp('#0b0b0f', '#1d1819', '#352826', '#52392f', '#76503c', '#9a6c4c', '#bc8c62', '#d8ae80')
        quilt = ramp('#040806', '#0a120e', '#111c16', '#1a2a20', '#2c3626', '#4a4628', '#6e5c30', '#94783c')
        knit = ramp('#0b0b0c', '#18171a', '#262426', '#383432', '#504840', '#6c5e4c', '#8a7658', '#a68e68')
        prot = ramp('#050506', '#0b0b0d', '#131315', '#1c1b1d', '#2a2726', '#3e3632', '#584a40')
        wood = ramp('#120a06', '#22140c', '#361f12', '#4e2e1a', '#6a4024', '#8a5630', '#aa6e3e', '#c88a52')
        pencil = ramp('#1a1206', '#3a2a0e', '#6a4a14', '#9a6c1e', '#c8962c', '#e8bc4e')
        rim = '#5f7f8c'
    else:
        skin_a = ramp('#0b0d16', '#1d1b28', '#372a37', '#5b3b43', '#86584f', '#b27b63', '#d4a17f', '#ecc9a1')
        skin_l = ramp('#0c0f14', '#1d2027', '#33363c', '#4f4f52', '#726c68', '#968c82', '#b8aea0', '#d6ccbc')
        quilt = ramp('#04060b', '#090e1a', '#0f1628', '#162036', '#1f2c48', '#2e3e5e', '#425478', '#5a6c90')
        knit = ramp('#0a0c0e', '#15191c', '#20262a', '#2d353a', '#3e484c', '#56605f', '#717a76', '#8e968e')
        prot = ramp('#050607', '#0a0c0e', '#111417', '#191d21', '#23292c', '#33393a', '#4a504c')
        wood = ramp('#0e0e0c', '#1c1c18', '#2c2a24', '#403c32', '#585244', '#726a58', '#8e866e', '#aaa288')
        pencil = ramp('#14100a', '#2a2214', '#4a3c1e', '#6e5a2c', '#94783c', '#b49650')
        rim = '#7f9aa8'
    glove = ramp('#030304', '#08080a', '#0e0d10', '#151316', '#1d1a1d', '#272326', '#352e30', '#4a4042')
    navy = ramp('#04060b', '#090e1a', '#0f1628', '#172038', '#202c48', '#2c3a5a', '#3c4c6e', '#526284')
    dust = ramp('#0c0e0e', '#171a1a', '#232727', '#303535', '#3f4544', '#525857', '#6a706c', '#888c86')
    shirt = ramp('#0e0f14', '#272a33', '#4a4c56', '#77777b', '#a19d98', '#d2c6b2')
    metal = ramp('#08090b', '#14161a', '#22262b', '#363b41', '#50565c', '#727980', '#9aa2a8', '#c8ced2')
    return {
        'skin': MatStyle(skin_a, SKIN_TH, dither=0.02, rim=rim, wrap=0.18),
        'skin_l': MatStyle(skin_l, SKIN_TH, dither=0.02, rim=rim, wrap=0.18),
        'glove': MatStyle(glove, TH7, dither=0.02, rim=rim, spec=0.35, spec_pow=10.0),
        'quilt': MatStyle(quilt, TH7, dither=0.05, rim=rim),
        'coat': MatStyle(navy, TH7, dither=0.03, rim=rim),
        'knit': MatStyle(knit, TH7, dither=0.04, rim=rim),
        'prot': MatStyle(prot, TH7[:6], dither=0.02, rim=rim, spec=0.2),
        'dust': MatStyle(dust, TH7, dither=0.03, rim=rim),
        'shirt': MatStyle(shirt, TH7[:5], dither=0.03, rim=rim),
        'wood': MatStyle(wood, TH7, dither=0.03, rim=rim, spec=0.25),
        'pencil': MatStyle(pencil, TH7[:5], rim=rim),
        'metal': MatStyle(metal, TH7, rim=rim, spec=0.6, spec_pow=16.0),
    }


GROUPS = {'skin': 0, 'skin_l': 0, 'glove': 1, 'quilt': 2, 'coat': 3, 'knit': 4, 'prot': 5, 'dust': 6, 'shirt': 7,
          'wood': 8, 'pencil': 9, 'metal': 10}


def _look(key, rim, ambient=0.06, fill=0.07, fill_dir=(0.0, -0.6, 0.8), bg='karsk'):
    return dict(key=key, rim=rim, ambient=ambient, wrap=0.12, bg=bg, glow=(0.8, 0.2), fill=fill,
                fill_dir=fill_dir, ao=0.55)


def _paint(nodes, M, size, look, city, cache, glow=None, passes=()):
    root = S.Union(nodes, k=1.0)
    return H.paint(root, M, size, look, _styles(city), groups=GROUPS, tone_passes=list(passes),
                   cache=(cache, _SRC), glow=glow)


# ----------------------------------------------------------------------------------------- a hand
def hand(M, mat, s, curl=0.25, spread=0.0, thumb=1.0, grip=0.0, curls=None, cut=None, thumb_dir=None,
         parts=('palm', 'fingers', 'thumb')):
    """A hand in its own frame (origin at the wrist, +y along the fingers, +z the back of the hand), like
    env_c3p2_cine_hands.hand but with per-finger curl (`curls` little..index), a cut fingertip (`cut` = finger
    index whose last joint is missing: Lev), an explicit thumb direction and selectable parts (so a thumb can be
    painted in front of a card and the rest behind it)."""
    m = M(mat)
    out = []
    if 'palm' in parts:
        out += [E((0.0, 0.50 * s, 0.02 * s), (0.44 * s, 0.54 * s, 0.17 * s), m),
                E((0.0, 0.10 * s, -0.02 * s), (0.30 * s, 0.24 * s, 0.18 * s), m)]
    lens = (0.62, 0.84, 0.92, 0.82)
    xs = (-0.33, -0.11, 0.11, 0.33)
    if 'fingers' in parts:
        for i in range(4):
            c_ = curl if curls is None else curls[i]
            t1 = math.radians(52.0 * c_)
            t2 = math.radians(78.0 * c_)
            x0 = xs[i] * s * thumb
            fan = (i - 1.5) * spread * 0.16 * thumb
            L = lens[i] * s
            r = (0.085 if i == 0 else 0.10) * s
            a = np.array([x0, 0.96 * s, 0.03 * s])
            d1 = _norm((fan, math.cos(t1), -math.sin(t1)))
            b = a + d1 * L * 0.55
            d2 = _norm((fan * 0.6, math.cos(t1 + t2), -math.sin(t1 + t2)))
            c = b + d2 * L * (0.22 if cut == i else 0.45)
            out += [RC(tuple(a), tuple(b), r, r * 0.92, m), RC(tuple(b), tuple(c), r * 0.92, r * 0.80, m)]
    if 'thumb' in parts:
        tb = np.array([0.34 * s * thumb, 0.26 * s, -0.06 * s])
        if thumb_dir is None:
            td = _norm((thumb * (0.62 - 0.40 * grip), 0.72, -0.22 - 0.70 * grip))
            td2 = _norm((thumb * (0.30 - 0.45 * grip), 0.85, -0.25 - 0.60 * grip))
        else:
            td = _norm(thumb_dir)
            td2 = _norm(np.asarray(thumb_dir, float) + np.array([0.0, 0.25, 0.0]))
        tm = tb + td * 0.40 * s
        tt = tm + td2 * 0.30 * s
        out += [RC(tuple(tb), tuple(tm), 0.15 * s, 0.12 * s, m), RC(tuple(tm), tuple(tt), 0.12 * s, 0.095 * s, m)]
    return S.Union(out, k=0.12 * s)


def arm(M, sleeve, skin, shoulder, elbow, wrist, r, hand_y, hand_z, s, cuff=None, cuff_len=0.0, **hand_kw):
    """Sleeve from the shoulder over the elbow to the wrist, an optional cuff, the wrist and a hand()."""
    shoulder, elbow, wrist = (np.asarray(p, float) for p in (shoulder, elbow, wrist))
    fdir = _norm(wrist - elbow)
    sleeve_end = wrist - fdir * (0.55 * s + cuff_len)
    nodes = [H.limb(M, sleeve, [shoulder, elbow, sleeve_end], [r[0], r[1], r[2]], k=2.0 + r[1] * 0.3)]
    if cuff is not None and cuff_len > 0:
        nodes.append(RC(tuple(sleeve_end - fdir * 0.6), tuple(sleeve_end + fdir * cuff_len), r[2] * 0.80,
                        r[2] * 0.74, M(cuff)))
    wrist_start = sleeve_end + fdir * (cuff_len * 0.5)
    nodes.append(RC(tuple(wrist_start), tuple(wrist + fdir * 0.15 * s), 0.30 * s, 0.27 * s, M(skin)))
    nodes.append(S.Xform(hand(M, skin, s, **hand_kw), frame=H.frame_along(wrist, hand_y, hand_z)))
    pts = [shoulder, elbow, wrist, wrist + _norm(hand_y) * 1.6 * s]
    return H.bounded(S.Union(nodes, k=0.08 * s + 0.6), pts, max(r) + s * 0.9)


def _split(full, part):
    """Layer of `full` covered by the separately rendered `part` (the thumb in front of a card)."""
    m = part[..., 3] > 0
    a = full.copy()
    a[~m, 3] = 0
    b = full.copy()
    b[m, 3] = 0
    return a, b


# ----------------------------------------------------------------------------------------- LS_C4_Card
C1_L_SIZE = (230, 200)       # canvas of the left hand (frame origin in layout.json card.c1_lhand_at)
C1_R_SIZE = (420, 300)       # wide and tall enough that the sleeve leaves the frame (right edge / letterbox)


def c1_lhand():
    """Konrad's left hand in the black glove holds the card by its upper-left corner from above (pinch: the
    thumb on the front, the curled fingers behind the edge); lit by the dawn from the upper left and the sodium
    lamp of the loop (rim, right).  -> (behind, thumb) layers of the same render (the card goes between)."""
    look = _look(key=(-0.62, -0.72, 0.30), rim=(0.80, -0.20, -0.55), ambient=0.05, bg='berlin')
    s = 40.0
    w = (96.0, 70.0, 0.0)
    hy, hz = (0.30, 0.92, -0.25), (-0.35, -0.45, 0.82)
    kw = dict(curls=(0.98, 0.95, 0.9, 0.82), spread=0.1, thumb=1.0, thumb_dir=(0.55, 0.80, 0.55))

    def build(thumb_only):
        M = A.Mats()
        if thumb_only:
            return [S.Xform(hand(M, 'glove', s, parts=('thumb',), **kw), frame=H.frame_along(w, hy, hz))], M
        return [arm(M, 'coat', 'glove', (-150.0, -170.0, -70.0), (-30.0, -40.0, -30.0), w, (30.0, 26.0, 22.0),
                    hy, hz, s, **kw)], M
    n, M = build(False)
    full = _paint(n, M, C1_L_SIZE, look, 'berlin', 'c1_lhand')
    n2, M2 = build(True)
    th = _paint(n2, M2, C1_L_SIZE, look, 'berlin', 'c1_lhand_thumb')
    thumb, behind = _split(full, th)
    return behind, thumb


def c1_rhand():
    """Konrad's right hand from the right: the thumb pressed on the card at the perforated edge, the fingers
    curled behind the card's edge (to the right of it, visible).  The coat sleeve runs on along the same line
    past the right frame edge / under the letterbox (the canvas reaches beyond both), never a cut in the frame."""
    M = A.Mats()
    s = 38.0
    wx, wy = 150.0, 96.0
    node = arm(M, 'coat', 'glove', (480.0, 380.0, -145.0), (250.0, 150.0, -30.0), (wx, wy, 0.0),
               (30.0, 26.0, 22.0), (-0.70, -0.62, -0.10), (0.30, -0.15, 0.94), s, curls=(0.9, 0.9, 0.85, 0.75),
               spread=0.15, thumb=-1.0, thumb_dir=(-0.95, -0.15, 0.35))
    look = _look(key=(-0.62, -0.72, 0.30), rim=(0.80, -0.20, -0.55), ambient=0.05, bg='berlin')
    return _paint([node], M, C1_R_SIZE, look, 'berlin', 'c1_rhand')


C2_SIZE = (300, 260)


def c2_thumb():
    """Macro: the gloved thumb pressed on the paper at the perforation (Berlin, dawn light)."""
    M = A.Mats()
    s = 150.0
    node = arm(M, 'coat', 'glove', (560.0, 520.0, -200.0), (420.0, 330.0, -90.0), (250.0, 190.0, -10.0),
               (110.0, 96.0, 84.0), (-0.75, -0.55, -0.20), (0.30, -0.20, 0.93), s, curls=(0.9, 0.9, 0.9, 0.8),
               spread=0.1, thumb=-1.0, thumb_dir=(-0.98, -0.05, 0.20))
    look = _look(key=(-0.60, -0.72, 0.32), rim=(0.70, -0.30, -0.62), ambient=0.05, bg='berlin')
    return _paint([node], M, C2_SIZE, look, 'berlin', 'c2_thumb')


def c3_finger():
    """Macro: Alexei's bare index finger along the other half's edge (Karsk, kerosene lamp from the right)."""
    M = A.Mats()
    s = 150.0
    node = arm(M, 'quilt', 'skin', (-280.0, 520.0, -200.0), (-140.0, 330.0, -90.0), (50.0, 200.0, -10.0),
               (110.0, 96.0, 84.0), (0.72, -0.62, 0.05), (-0.20, -0.25, 0.95), s, curls=(0.95, 0.9, 0.85, 0.08),
               spread=0.0, thumb=1.0, grip=0.6)
    look = _look(key=(0.74, -0.58, 0.32), rim=(-0.70, -0.30, -0.62), ambient=0.05, bg='karsk')
    return _paint([node], M, C2_SIZE, look, 'karsk', 'c3_finger')


C3_SIZE = (260, 210)


def c3_hand():
    """Close: Alexei's right hand lying flat on the desk, the fingertips along the card's perforated left edge
    (the green quilted sleeve from the lower left); the kerosene lamp at the upper right."""
    M = A.Mats()
    s = 40.0
    node = arm(M, 'quilt', 'skin', (-170.0, 300.0, -40.0), (-40.0, 196.0, -14.0), (104.0, 112.0, 0.0),
               (34.0, 29.0, 25.0), (0.94, -0.30, 0.0), (0.0, -0.25, 0.97), s, curls=(0.30, 0.22, 0.12, 0.10),
               spread=0.10, thumb=-1.0, grip=0.15)
    look = _look(key=(0.74, -0.56, 0.32), rim=(-0.60, -0.40, -0.66), ambient=0.05, bg='karsk')
    return _paint([node], M, C3_SIZE, look, 'karsk', 'c3_hand')


C4_SIZE = (230, 250)
C4_AT = (16, 96)             # top-left of the over-shoulder figure in the frame


def c4_back(f):
    """Alexei from behind at the booth window, seen over his right shoulder: f 0 the head bowed to the card on
    the desk, 1 lifted to the window (the wagon outside).  Kerosene lamp at his left (warm key), the cold work
    lamp beyond the glass as rim."""
    spec = CC.alexei()
    look = dict(key=(-0.70, 0.30, -0.60), rim=(0.40, -0.55, -0.72), ambient=0.06, wrap=0.10, bg='karsk',
                glow=(0.8, 0.2), fill=0.06, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.ushanka(M, hp, flaps='up'),
                  lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0, nape=13.0,
                                              back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=12.0, collar_r=(13.4, 14.8)),
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8))]
    pitch = 22.0 if f == 0 else -14.0
    res = F.render(spec, C4_SIZE, 1.55, (116.0, 70.0 + (6.0 if f == 0 else 0.0)), (112.0, 112.0), 196.0,
                   pitch=pitch, roll=0.0, torso_yaw=190.0, torso_pitch=10.0, look=look,
                   torso_kw=dict(width=1.05, depth=1.05, slope=1.0, arm_out=1.05, lean=4.0,
                                 arm_l=((-30.0, 56.0, 10.0), (-14.0, 54.0, 36.0)),
                                 arm_r=((30.0, 56.0, 10.0), (14.0, 54.0, 36.0))),
                   head_items=head_items, torso_items=torso_items, styles=F.alexei_train_styles(),
                   tone_passes=[CC.pass_fur('fur'), CC.pass_stitches('coat', 5.0), F.pass_hair_back('hair'),
                                CC.pass_knit('knit', ribs=30)],
                   cache_key=('c4_back_alexei', f, _SRC))
    return res['rgba']


# ----------------------------------------------------------------------------------------- LS_C4_Stamp
S1_P_SIZE = (200, 180)


def s1_pencil(f):
    """Alexei's right hand writing (pencil between thumb and index), two frames of the stroke."""
    M = A.Mats()
    s = 34.0
    dx = (0.0, 7.0)[f]
    wx, wy = 112.0 + dx, 96.0 - dx * 0.2
    node = arm(M, 'quilt', 'skin', (330.0 + dx, 260.0, -60.0), (230.0 + dx, 180.0, -24.0), (wx, wy, 0.0),
               (30.0, 26.0, 22.0), (-0.62, -0.70, 0.30), (0.25, -0.45, 0.86), s, curls=(0.85, 0.8, 0.7, 0.55),
               spread=0.05, thumb=-1.0, grip=0.5)
    tip = np.array([wx - 52.0, wy - 34.0 + (1.5 if f else 0.0), 6.0])
    end = tip + np.array([46.0, -44.0, 14.0])
    pen = RC(tuple(tip), tuple(end), 2.1, 2.4, M('pencil'))
    look = _look(key=(0.62, -0.60, 0.50), rim=(-0.60, -0.45, -0.66), ambient=0.06, bg='karsk')
    return _paint([node, pen], M, S1_P_SIZE, look, 'karsk', ('s1_pencil', f))


S1_L_SIZE = (200, 140)


def s1_lev():
    """Lev's left hand from across the desk (from the top of the frame), bare, the tip of the index finger
    missing (an old injury); the darned grey cardigan sleeve under a black sleeve protector.  The fingertips
    hold the card's upper edge and slide it into the box."""
    M = A.Mats()
    s = 34.0
    node = arm(M, 'prot', 'skin_l', (40.0, -170.0, -50.0), (70.0, -50.0, -20.0), (96.0, 52.0, 0.0),
               (30.0, 26.0, 21.0), (0.10, 0.98, -0.12), (0.10, -0.25, 0.96), s, curls=(0.40, 0.30, 0.22, 0.18),
               spread=0.12, thumb=1.0, grip=0.2, cut=3, cuff='knit', cuff_len=8.0)
    look = _look(key=(-0.55, -0.62, 0.40), rim=(0.55, -0.50, -0.66), ambient=0.06, bg='karsk')
    return _paint([node], M, S1_L_SIZE, look, 'karsk', 's1_lev')


STAMP_HAND_SIZE = (200, 200)


def stamp_hand(city):
    """A hand from above gripping the knob of a rubber stamp (the knob itself is painted with the stamp):
    Lev's (Karsk: knit + black protector, warm light) or Fengler's (Berlin: grey dust coat + protector,
    flat fluorescent light)."""
    M = A.Mats()
    s = 46.0
    sleeve, skin = ('prot', 'skin_l')
    knob = (100.0, 150.0)
    node = arm(M, sleeve, skin, (180.0, -160.0, 20.0), (150.0, -40.0, 30.0), (knob[0] + 4.0, knob[1] - 50.0, 26.0),
               (40.0, 34.0, 28.0), (-0.05, 0.98, -0.10), (0.05, -0.15, 0.99), s, curls=(0.95, 0.95, 0.95, 0.92),
               spread=0.05, thumb=-1.0, grip=0.9, cuff='knit' if city == 'karsk' else 'dust', cuff_len=10.0)
    if city == 'karsk':
        look = _look(key=(0.66, -0.55, 0.50), rim=(-0.60, -0.45, -0.66), ambient=0.06, bg='karsk')
    else:
        look = _look(key=(0.05, -0.95, 0.30), rim=(-0.50, -0.40, -0.75), ambient=0.10, fill=0.10, bg='berlin')
    return _paint([node], M, STAMP_HAND_SIZE, look, city, ('stamp_hand', city))


S3M_SIZE = (440, 280)        # canvas of Fengler's arms, placed at S3M_AT (layout stamp.s3b_hands_at)
S3M_AT = (170, 30)           # its top edge lies under the letterbox
S3M_SHOULDERS = ((280, 0), (420, 0))   # world: both upper arms run up into the letterbox, to Fengler's shoulders


def s3_hands_med():
    """Medium: Fengler leaning over the counter -- his right hand on the stamp knob (left), his left hand flat on a
    card (right), elbows out; grey dust coat sleeves with black protectors; flat fluorescent light from above.  The
    upper arms run up out of the frame (under the letterbox) to his shoulders; his chest between them is painted
    in the counter plate (env_c4_cine_stamp.s3b_counter), so no sleeve ends in mid-air."""
    M = A.Mats()
    s = 22.0
    (l_sx, l_sy), (r_sx, r_sy) = ((x - S3M_AT[0], y - S3M_AT[1]) for (x, y) in S3M_SHOULDERS)
    n1 = arm(M, 'prot', 'skin_l', (l_sx, l_sy, 10.0), (60.0, 120.0, 20.0), (82.0, 172.0, 16.0),
             (20.0, 17.0, 14.0), (0.05, 0.98, -0.1), (0.05, -0.15, 0.99), s, curls=(0.95, 0.95, 0.95, 0.9),
             thumb=-1.0, grip=0.9, cuff='dust', cuff_len=6.0)
    n2 = arm(M, 'prot', 'skin_l', (r_sx, r_sy, 10.0), (260.0, 150.0, 10.0), (204.0, 214.0, 4.0),
             (20.0, 17.0, 14.0), (-0.72, 0.62, -0.05), (0.0, -0.3, 0.95), s, curls=(0.15, 0.1, 0.08, 0.06),
             spread=0.2, thumb=1.0, grip=0.1, cuff='dust', cuff_len=6.0)
    look = _look(key=(0.05, -0.95, 0.30), rim=(-0.50, -0.40, -0.75), ambient=0.10, fill=0.10, bg='berlin')
    return _paint([n1, n2], M, S3M_SIZE, look, 'berlin', 's3_hands_med')


# ----------------------------------------------------------------------------------------- LS_C4_Voices
V2_SIZE = (240, 270)
V2_AT = (14, 98)             # top-left of Konrad's back in the frame (bottom cut by the letterbox)


def v2_konrad(f):
    """Konrad from behind at the tram loop (hat, coat, scarf), the tram leaving beyond him; f 0 arms down,
    1 the right arm half raised, 2 raised (protect_marta: he waves to Ilse).  Morning light from the front
    (cold), the sodium lamp of the loop as a warm rim from the right."""
    spec = CC.konrad()
    look = dict(key=(0.30, -0.45, -0.84), rim=(0.70, -0.30, -0.65), ambient=0.08, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(0.0, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape')]
    # right arm (his right = our right when seen from behind): down, half, up -- elbow / hand in torso space
    arm_r = (((31.0, 58.0, -2.0), (30.0, 96.0, 2.0)),
             ((44.0, 30.0, -6.0), (52.0, -4.0, -8.0)),
             ((44.0, 6.0, -6.0), (48.0, -40.0, -10.0)))[f]
    arm_l = ((-31.0, 58.0, -2.0), (-30.0, 96.0, 2.0))
    res = F.render(spec, V2_SIZE, 1.5, (118.0, 64.0), (116.0, 108.0), 184.0, pitch=2.0, roll=0.0,
                   torso_yaw=182.0, torso_pitch=2.0, look=look,
                   torso_kw=dict(width=0.96, depth=1.0, slope=1.25, arm_out=1.0, lean=0.0, arm_l=arm_l, arm_r=arm_r),
                   head_items=head_items, torso_items=torso_items, styles=F.konrad_train_styles(),
                   tone_passes=[CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3),
                                CC.pass_grain('coat', 0.04, seed=4), F.pass_hair_back('hair')],
                   cache_key=('c4_v2_konrad', f, _SRC))
    return res['rgba']
