"""chargen_portrait_c3 -- 112x112 dialogue portraits (bust, 3/4 view facing right) for the Chapter 3 cast.

Same method as chargen_portrait.py (whose primitives are imported, nothing there is modified):
analytic ellipsoid busts ray-cast into per-group depth buffers, 2.5D cast shadows, one warm key light
(front-right-top), deep ambient, cool back rim, posterised ramps with an ordered-dither band, selective
outlines; eyes / brows / mouths are hand-designed pixel stamps placed at projected 3D landmarks.
Additions here:
  * two new looks: 'veltrava' (slate-blue dawn station) and 'palais' (navy-teal conference palace)
  * per-character stamp sets (Elena has her own eyes / brows / mouths and creases), and per-expression
    head poses (small turns / tilts) so the four expressions act instead of only swapping features
Expressions: neutral, concerned, determined, surprised (portrait.json contract).
Deterministic: no randomness, nothing sampled from reference images.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image

import chargen_portrait as PT
from chargen_portrait import (BERLIN_FEAT, EXPRESSIONS, H, W, Look, Scene, add_head, background, cloth_folds,
                              dither_mask, face_colors, feat, head_frame, hexc, local_coords, project, ramp, rotm,
                              shade_portrait, stamp)

# ----------------------------------------------------------------------------------- looks
LOOK_VELTRAVA = dict(bg=ramp('#05070D', '#0A0F19', '#101724', '#172131', '#1F2B3D'),
                     rim=ramp('#3C4C68', '#94A4C4'), glow=(98, 30, 70))
LOOK_PALAIS = dict(bg=ramp('#05080A', '#0A1215', '#101B1F', '#172528', '#1F2F31'),
                   rim=ramp('#33515C', '#88A8B8'), glow=(100, 32, 72))

SKIN_V = ramp('#0A0E1A', '#1A1C2E', '#3C2C3C', '#6C4446', '#A06650', '#D09260', '#F0C482')
SKIN_W = ramp('#0A0E1A', '#1B1C2E', '#3E2D3E', '#704648', '#A46A55', '#D49767', '#F2C98C')   # women
SKIN_P = ramp('#090E14', '#191C28', '#3C2C38', '#6E4644', '#A2684E', '#D2945E', '#F0C47E')   # palais

VELTRAVA_FEAT = dict(BERLIN_FEAT, white_dk='#3A3C4E', white_dk2='#282A3A', lid_dk='#3A2C3C',
                     crease_dk='#2E2638')
PALAIS_FEAT = dict(BERLIN_FEAT, white_dk='#383E48', white_dk2='#262C36', lid_dk='#382C36')

GENERIC = dict(eyes=PT.EYES, brows=PT.BROWS, mouths=PT.MOUTHS, creases=PT.CREASES)


# ----------------------------------------------------------------------------------- rendering
def draw_features_c3(img, sc, info, expr, cols, skin_mask, stamps, extra=None, creases=True, nostril=True,
                     mouth=True):
    val = info['val']

    def lit_at(x, y):
        xi, yi = int(np.clip(round(x), 0, W - 1)), int(np.clip(round(y), 0, H - 1))
        return val[yi, xi] > 0.30

    for side in ('near', 'far'):
        x, y, z = project(sc, 'eye_' + side[0])
        rows, anc = stamps['eyes'][side][expr]
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
        x, y, z = project(sc, 'brow_' + side[0])
        rows, anc = stamps['brows'][side][expr]
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    if mouth:
        x, y, z = project(sc, 'mouth')
        rows, anc = stamps['mouths'][expr]
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    for where, rows, anc in (stamps['creases'][expr] if creases else []):
        if where == 'brow_mid':
            xn, yn, _ = project(sc, 'brow_n')
            xf, yf, _ = project(sc, 'brow_f')
            x, y = (xn + xf) / 2 + 0.5, (yn + yf) / 2 + 1
        else:
            x, y, _ = project(sc, where)
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    if nostril:
        x, y, _ = project(sc, 'nostril')
        stamp(img, 'nn', x, y, {'n': cols['nostril']}, mask=skin_mask, anchor=(1, 0))
    if extra:
        extra(img, sc, info, expr, cols, skin_mask, lit_at)


def finish_c3(sc, look_d, ramps, expr, feat_cols, extra=None, creases=True, stamps=None, pre=None, **kw):
    """Composite, shade, background, features.  `pre(img, sc, info)` runs before the feature stamps
    (cloth textures); `extra` runs after them (spectacles, badges, props)."""
    sc.composite()
    look = Look(rim_cols=look_d['rim'])
    img, info = shade_portrait(sc, look, ramps)
    out = background(look_d['bg'], look_d.get('glow'))
    occ = info['occ']
    out[occ] = img[occ]
    if pre:
        pre(out, sc, info)
    skin_mask = np.zeros((H, W), bool)
    if 'skin' in sc.mat_names:
        skin_mask = (sc.mat == sc.mat_names.index('skin')) & (sc.grp == sc.order.index('head'))
    draw_features_c3(out, sc, info, expr, feat_cols, skin_mask, stamps or GENERIC, extra, creases=creases, **kw)
    return out, info


def shoulders(sc, cx=54.0, yaw=20.0, mat='coat', width=1.0, drop=0.0, z=0.0, arm_mat=None):
    """add_shoulders with the upper arms in their own groups ('arm_n' viewer-left, 'arm_f') so arm
    details (armbands) can be addressed."""
    bf = (np.array([cx, 0.0, z]), rotm(yaw, 0.0, 0.0), 1.0)
    B = dict(frame=bf, group='body', mat=mat)
    sc.ellipsoid((0, 108 + drop, -6), (33 * width, 30, 18), k=0, **B)
    for sx in (-1, 1):
        sc.ellipsoid((sx * 26 * width, 94 + drop, -7), (16 * width, 9.5, 13), k=7, **B)
    am = arm_mat or mat
    for sx, g in ((-1, 'arm_n'), (1, 'arm_f')):
        sc.ellipsoid((sx * 35 * width, 114 + drop, -6), (10.5, 26, 12), k=0, frame=bf, group=g, mat=am)
    sc.ellipsoid((0, 92 + drop, -16), (28 * width, 12, 10), k=6, **B)
    return bf


def mat_mask(sc, name, group=None):
    if name not in sc.mat_names:
        return np.zeros((H, W), bool)
    m = sc.mat == sc.mat_names.index(name)
    if group is not None:
        m &= sc.grp == sc.order.index(group) if group in sc.order else False
    return m


def tone_shift(img, sc, info, ramps, name, sel, d):
    """Re-colour pixels of material `name` in `sel` with their tone shifted by d."""
    R = np.stack(ramps[name])
    t = np.clip(info['tone'] + d, 0, len(R) - 1)
    m = sel & mat_mask(sc, name)
    img[m] = R[t][m]


def hash2(xx, yy, a=73, b=151, mod=23):
    return (xx * a + yy * b + (xx * yy) % 7 * 31) % mod


def wrinkles(img, sc, skin_mask, lit_at, ramp_):
    """Age lines: crow's feet at the near eye and a nasolabial fold (cf. Emil)."""
    R = np.stack(ramp_)
    x, y, _ = project(sc, 'eye_n')
    stamp(img, ['c.', '.c', 'c.'], x - 6, y, {'c': R[2]}, mask=skin_mask)
    x, y, _ = project(sc, 'nostril')
    stamp(img, ['c..', '.c.', '.c.', '..c'], x - 5, y + 1, {'c': R[2] if not lit_at(x - 4, y + 2) else R[3]},
          mask=skin_mask)


def spectacles(img, sc, lit_at, frame_c, glint, glint2, rx=(4, 3), ry=3.4, temple=True, thin=False):
    """Round / oval spectacles over both eyes, bridge, temple arm (cf. Emil), optionally thin."""
    for side, r in (('n', rx[0]), ('f', rx[1])):
        x, y, _ = project(sc, 'eye_' + side)
        cx, cy = int(round(x)), int(round(y))
        n = 40 if thin else 48
        for a in np.linspace(0, 2 * np.pi, n, endpoint=False):
            px_ = int(round(cx + 0.5 + math.cos(a) * (r + 0.6)))
            py_ = int(round(cy + 0.5 + math.sin(a) * ry))
            if thin and math.sin(a) > 0.55:
                continue                     # half-rimmed: no lower rim line
            if 0 <= px_ < W and 0 <= py_ < H:
                img[py_, px_] = frame_c
        if lit_at(cx + 2, cy - 1):
            img[cy - 2, cx + r - 2] = glint
            img[cy - 1, cx + r - 1] = glint2
        else:
            img[cy - 2, cx + r - 2] = glint2
    xn, yn, _ = project(sc, 'eye_n')
    xf, yf, _ = project(sc, 'eye_f')
    for t in np.linspace(0, 1, 8):
        bx = int(round(xn + rx[0] + 0.6 + (xf - rx[1] - 0.6 - xn - rx[0] - 0.6) * t))
        by = int(round(yn - 1 + (yf - yn) * t))
        img[by, bx] = frame_c
    if temple:
        xe, ye, _ = project(sc, 'ear')
        sk = sc.mat_names.index('skin') if 'skin' in sc.mat_names else -1
        for t in np.linspace(0, 1, 14):
            bx = int(round(xn - rx[0] - 0.6 + (xe + 2 - xn + rx[0] + 0.6) * t))
            by = int(round(yn - 1 + (ye - 2 - yn + 1) * t))
            if 0 <= bx < W and 0 <= by < H and sc.mat[by, bx] == sk:
                img[by, bx] = frame_c


# =================================================================================== ELENA
# Her own feature stamps: almond eyes with a heavier upper lid (tired, attentive), a soft lower-lid
# shadow 'u', finer arched brows, a smaller mouth with natural lips (no lipstick).
ELENA_EYES = {
    'near': {
        'neutral': ('''
            .LLLLLL.
            LLwWIIWl
            ..wWICl.
            ...ccc..''', (4, 1)),
        'concerned': ('''
            ...LLLL.
            .LLwWIIl
            ..wWICl.
            ...cccc.''', (4, 1)),
        'determined': ('''
            .LLLLLL.
            ..LLIIL.
            ..wWICl.
            ...cc...''', (4, 1)),
        'surprised': ('''
            ..LLLL..
            .LwWWWL.
            .wWIIWl.
            .wWICWl.
            ..cccc..''', (4, 2)),
    },
    'far': {
        'neutral': ('''
            .LLLL
            lWIIL
            .wICl
            ..cc.''', (2, 1)),
        'concerned': ('''
            ..LLL
            lLWIL
            .wICl
            ..cc.''', (2, 1)),
        'determined': ('''
            .LLLL
            .LIIL
            .wICl
            ..c..''', (2, 1)),
        'surprised': ('''
            .LLL.
            lWWWL
            lWIIL
            .wICl
            ..cc.''', (2, 2)),
    },
}
ELENA_BROWS = {
    'near': {
        'neutral': ('''
            ....bBBb..
            ..bBb..bBB
            .bb.......''', (5, 1)),
        'concerned': ('''
            ........bB
            ......bBB.
            ...bBBb...
            .bb.......''', (5, 2)),
        'determined': ('''
            ...bBBb...
            .bBb..bBBB''', (5, 1)),
        'surprised': ('''
            ...bBBBb..
            ..b....bBb
            .b.......b''', (5, 4)),
    },
    'far': {
        'neutral': ('''
            .bBb.
            B...b''', (2, 1)),
        'concerned': ('''
            Bb...
            .bBb.
            ....b''', (2, 2)),
        'determined': ('''
            BBBb.
            ...bb''', (2, 1)),
        'surprised': ('''
            .bBb.
            b...b''', (2, 4)),
    },
}
ELENA_MOUTHS = {
    'neutral': ('''
        .mMMMMm.
        ..uuuu..''', (4, 0)),
    'concerned': ('''
        ..mMMm..
        .mM..Mm.
        ..uuu...''', (4, 0)),
    'determined': ('''
        mMMMMMMm
        ..ssss..''', (4, 0)),
    'surprised': ('''
        ..MMM...
        .MDDDM..
        ..MDM...
        ...u....''', (4, 1)),
}
ELENA_CREASES = {
    'neutral': [],
    'concerned': [('brow_mid', '''
        c.
        c.''', (1, 0))],
    'determined': [('brow_mid', '''
        c.c''', (1, 0))],
    'surprised': [],
}
ELENA_STAMPS = dict(eyes=ELENA_EYES, brows=ELENA_BROWS, mouths=ELENA_MOUTHS, creases=ELENA_CREASES)
# per-expression head pose: (yaw, pitch, roll, dx, dy) -- small changes so the head acts
ELENA_POSE = {
    'neutral': (25.0, 2.0, -3.0, 0.0, 0.0),        # attentive, listening, slight tilt
    'concerned': (22.0, 6.0, -6.0, -0.5, 1.0),     # chin lowered, more tilt
    'determined': (28.0, -1.0, -1.0, 0.5, -0.5),   # level gaze, turned towards the listener
    'surprised': (24.0, -3.5, -2.0, -1.0, -1.0),   # head pulled back
}


def elena_portrait(expr):
    sc = Scene()
    yaw, pitch, roll, dx, dy = ELENA_POSE[expr]
    jd = 1.2 if expr == 'surprised' else 0.0
    fr = head_frame((53.0 + dx, 50.0 + dy, 0.0), yaw=yaw, pitch=pitch, roll=roll, scale=1.12)
    add_head(sc, fr, dict(jaw_w=12.2, crown_w=18.0, nose_len=0.9, nose_w=0.82, chin=0.84, jaw_drop=jd,
                          lip_w=0.88, lip_l=1.12, face_h=0.93))

    def face(L):
        x, y, z = L[..., 0], L[..., 1], L[..., 2]
        return (z > 0.5) & (y > -11.6 + 0.024 * x * x)

    def hair_clip(L):
        return ~face(L) & (L[..., 1] < 10.0)
    Hh = dict(frame=fr, group='hair')
    # hair swept back from a side parting (far side), covering the upper ears, into a low chignon
    sc.ellipsoid((0, -7.8, -2.6), (20.0, 21.9, 23.2), mat='hair', k=0, clip=hair_clip, **Hh)
    sc.ellipsoid((-6.0, -15.5, 9.0), (11.0, 5.5, 10.0), mat='hair', k=4.0, clip=hair_clip, **Hh)   # wave
    for sx in (-1, 1):
        sc.ellipsoid((sx * 16.8, -3.0, -4.0), (5.2, 10.0, 11.5), mat='hair', k=4.0,
                     clip=lambda L: ~face(L) & (L[..., 1] < 7.0), **Hh)                         # over the ears
    B = dict(frame=fr, group='bun')
    sc.ellipsoid((0.0, 10.0, -23.5), (11.0, 8.4, 8.6), mat='hair2', k=0, **B)                     # chignon
    sc.ellipsoid((0.0, 3.5, -20.5), (13.0, 7.5, 7.0), mat='hair2', k=4.0, **B)
    bf = shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.84, drop=4.0)
    C_ = dict(frame=bf, group='collar')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 12.0, 90, 1.0), (8.0, 8.0, 8.6), mat='coat2', k=3, **C_)
    sc.ellipsoid((0, 85, -9), (15, 9, 7), mat='coat2', k=3, **C_)
    S = dict(frame=bf, group='scarf')
    sc.ellipsoid((0, 81.5, 0.5), (11.8, 6.2, 11.0), mat='scarf', k=0, **S)                       # high wrap
    sc.ellipsoid((0, 86.5, 2.0), (13.2, 5.6, 12.0), mat='scarf', k=3.0, **S)
    sc.ellipsoid((-3.5, 91.0, 9.5), (7.6, 5.6, 5.0), mat='scarf', k=3, **S)
    sc.ellipsoid((3.5, 100.0, 12.0), (4.4, 10.5, 2.4), R=rotm(0, 0, 8), mat='scarf2', k=1.2, **S)  # end
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 12.5, 104, 15.0), (4.8, 15, 1.3), R=rotm(0, 0, sx * -22), mat='coat2', k=0, **L_)
    ramps = {
        'skin': SKIN_W,
        'hair': ramp('#040407', '#09080C', '#110E12', '#1A1418', '#261C1E', '#352624', '#48342E'),
        'hair2': ramp('#040407', '#0A080C', '#130F13', '#1D1619', '#2A1E1F', '#3A2A27', '#4E3A32'),
        'coat': ramp('#05070C', '#0C1016', '#161A22', '#22262E', '#33363E', '#4A4C52', '#66666A'),
        'coat2': ramp('#05070C', '#0A0E14', '#13171E', '#1E222A', '#2E3138', '#43454C', '#5E5E64'),
        'scarf': ramp('#0A0508', '#1A0910', '#320E18', '#4E1622', '#6E202E', '#902C38', '#AE4244'),
        'scarf2': ramp('#0A0508', '#16080E', '#2C0C16', '#46141E', '#641C2A', '#842834', '#A23C40'),
    }

    def pre(img, sc, info):
        # hair: fine strands swept back towards the chignon (darker lines in head-local space)
        Lh = local_coords(sc, fr)
        hm = mat_mask(sc, 'hair')
        strands = hm & ((((Lh[..., 1] - 0.45 * Lh[..., 2]) % 4.2) < 0.9) & (info['tone'] >= 2))
        tone_shift(img, sc, info, ramps, 'hair', strands, -1)
        sheen = hm & ((((Lh[..., 1] - 0.45 * Lh[..., 2]) % 4.2) > 2.6) & (((Lh[..., 1] - 0.45 * Lh[..., 2]) % 4.2) < 3.2)
                      & (info['tone'] >= 4))
        tone_shift(img, sc, info, ramps, 'hair', sheen, +1)
        # side parting on the far side: a darker line from the hairline back over the crown
        part = hm & (np.abs(Lh[..., 0] - 7.0 + 0.03 * Lh[..., 2]) < 0.8) & (Lh[..., 1] < -13)
        tone_shift(img, sc, info, ramps, 'hair', part, -2)
        # chignon: twisted coil
        bm_ = mat_mask(sc, 'hair2')
        coil = bm_ & ((((Lh[..., 0] * 0.9 + Lh[..., 1] * 1.1) % 3.8) < 0.9))
        tone_shift(img, sc, info, ramps, 'hair2', coil, -1)
        tone_shift(img, sc, info, ramps, 'hair2', bm_ & ((((Lh[..., 0] * 0.9 + Lh[..., 1] * 1.1) % 3.8) > 2.6)), +1)
        # wool coat: a few soft folds
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-24, 100, -21, 112), (22, 99, 19, 112)])
        # commission armband on her left (near) upper arm: white band with a slate-blue stripe
        arm = (sc.grp == sc.order.index('arm_n')) if 'arm_n' in sc.order else np.zeros((H, W), bool)
        yy = np.mgrid[0:H, 0:W][0]
        white = ramp('#3A404C', '#5E6672', '#8A929E', '#B4BAC2', '#D4D8DC', '#E8EAEC', '#F4F5F6')
        slate = ramp('#0E1420', '#18243A', '#22324E', '#2E4466', '#3E5880', '#54709A', '#6C88B0')
        Wr, Sr = np.stack(white), np.stack(slate)
        t = np.clip(info['tone'] + 1, 0, 6)
        bandw = arm & (yy >= 101) & (yy < 112) & ~((yy >= 105) & (yy < 108))
        bands = arm & (yy >= 105) & (yy < 108)
        img[bandw] = Wr[t][bandw]
        img[bands] = Sr[t][bands]

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # a loose strand escaping at the near temple (end of a long day) -- not glamour
        x, y, _ = project(sc, 'forehead')
        stamp(img, ['h..', 'h..', '.h.', '.h.', '..h'], x - 8, y + 6, {'h': hexc('#1A1418')}, mask=skin_mask)

    out, info = finish_c3(sc, LOOK_VELTRAVA, ramps, expr,
                          feat(VELTRAVA_FEAT, iris='#2C2830', lip='#A8645A', lip_dk='#4A2C34', mouth='#3E1E24',
                               mouth2='#6A3836', brow='#1E1416', brow2='#3E2C28', lid='#9E6450', lash='#120C12'),
                          extra, creases=True, stamps=ELENA_STAMPS, pre=pre)
    return out


# =================================================================================== BORDER OFFICER
def border_officer_portrait(expr):
    sc = Scene()
    jd = 2.2 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 54.0, 0.0), yaw=26.0, pitch=2.0, roll=-1.5, scale=1.2)
    add_head(sc, fr, dict(jaw_w=15.2, crown_w=19.0, nose_len=1.05, nose_w=1.12, chin=1.04, jaw_drop=jd,
                          lip_w=1.0, lip_l=0.9))
    E = dict(frame=fr, group='head')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.5, 12.5, 7.0), (5.4, 5.2, 5.6), mat='skin', k=3, **E)            # jowls
    sc.ellipsoid((0, -2.0, -4.0), (19.2, 17.0, 20.6), mat='hair', group='hair', frame=fr,
                 clip=lambda L: (L[..., 2] < 4.0) & (L[..., 1] > -14.0) & (L[..., 1] < 8.0))
    sc.ellipsoid((0, 10.4, 18.6), (7.0, 2.5, 3.2), mat='stache', group='stache', frame=fr)
    Hc = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -16.6, -1.0), (19.4, 3.4, 20.6), mat='capband', k=0, **Hc)
    sc.ellipsoid((0, -22.0, -2.5), (22.0, 6.2, 23.6), mat='cap', k=2.0, **Hc)
    sc.ellipsoid((0, -25.5, -2.5), (20.6, 2.6, 22.4), mat='cap', k=2.5, **Hc)
    sc.ellipsoid((0, -14.2, 14.0), (15.5, 1.7, 10.0), R=rotm(0, -18, 0), mat='visor', k=0,
                 clip=lambda L: L[..., 2] > 6.0, **Hc)
    bf = shoulders(sc, cx=57.0, yaw=20.0, mat='coat', width=0.98, drop=4.0)
    C_ = dict(frame=bf, group='collar')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 11.5, 87, 2), (10.5, 10.5, 10.0), mat='coat2', k=3, **C_)
    sc.ellipsoid((0, 84, -9), (16, 10, 7), mat='coat2', k=3, **C_)
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 12.0, 104, 15.5), (5.4, 17, 1.4), R=rotm(0, 0, sx * -20), mat='coat2', k=0, **L_)
    sc.ellipsoid((0, 91, 9.5), (5.5, 3.2, 5.0), mat='tie', group='shirt', frame=bf)
    ramps = {
        'skin': SKIN_V,
        'hair': ramp('#0C0E12', '#1E2026', '#34363A', '#525250', '#76746E', '#9A968C', '#BAB4A6'),
        'stache': ramp('#0C0C10', '#1C1A1E', '#302C2C', '#4A4440', '#6A625A', '#8A8074', '#A89C8C'),
        'cap': ramp('#04070D', '#0A1220', '#122036', '#1C2E4A', '#2A4062', '#3E567C', '#587094'),
        'capband': ramp('#030408', '#070A12', '#0C121E', '#131C2C', '#1C283C', '#283650', '#384864'),
        'visor': ramp('#020305', '#05070A', '#0A0D12', '#11151C', '#1C222C', '#3A4452', '#7A8696'),
        'coat': ramp('#04070D', '#0A1220', '#13213A', '#1E3250', '#2E466A', '#445E84', '#5E769A'),
        'coat2': ramp('#04070D', '#091020', '#111D34', '#1A2C48', '#283E60', '#3C5478', '#566C90'),
        'shirt': ramp('#14161C', '#2A2C34', '#4A4C52', '#76766E', '#A4A090', '#C8C2AA', '#E0D8BE'),
        'tie': ramp('#04050A', '#0A0C14', '#10141E', '#18202C', '#22303E', '#2E4050', '#3C5262'),
    }

    def pre(img, sc, info):
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-26, 100, -22, 112), (24, 99, 20, 112)])

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # Free City badge on the cap band: a small bridge of three arches, white on slate
        o, R = fr[0], fr[1]
        p = o + R @ (np.array([0.0, -17.0, 20.2]) * fr[2])
        stamp(img, ['.wwwww.', 'w.w.w.w', 'ssssss.'], p[0] + 1, p[1], {'w': hexc('#D8DCE0'), 's': hexc('#5C7090')},
              anchor=(3, 1))
        # coat buttons (silver)
        for (bx, by) in ((62, 106), (64, 111)):
            if sc.mat[by, bx] >= 0:
                img[by, bx] = hexc('#9CA2AA')
        wrinkles(img, sc, skin_mask, lit_at, SKIN_V)

    out, info = finish_c3(sc, LOOK_VELTRAVA, ramps, expr, feat(VELTRAVA_FEAT, brow='#3A3430', brow2='#6A625A'),
                          extra, pre=pre, mouth=(expr == 'surprised'))
    return out


# =================================================================================== CONDUCTOR
def conductor_portrait(expr):
    sc = Scene()
    jd = 2.0 if expr == 'surprised' else 0.0
    fr = head_frame((52.0, 55.0, 0.0), yaw=24.0, pitch=7.0, roll=-2.0, scale=1.18)
    add_head(sc, fr, dict(jaw_w=14.6, crown_w=18.8, nose_len=1.15, nose_w=1.15, chin=1.0, jaw_drop=jd,
                          lip_w=1.0, lip_l=0.9))
    E = dict(frame=fr, group='head')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.0, 12.0, 8.0), (5.0, 5.4, 5.4), mat='skin', k=3, **E)            # jowls
    sc.ellipsoid((0, -2.0, -4.0), (19.0, 17.0, 20.6), mat='hair', group='hair', frame=fr,
                 clip=lambda L: (L[..., 2] < 5.0) & (L[..., 1] > -14.0) & (L[..., 1] < 9.0))
    St = dict(frame=fr, group='stache')
    sc.ellipsoid((0, 10.8, 18.4), (7.6, 2.8, 3.4), mat='stache', **St)                       # walrus moustache
    for sx in (-1, 1):
        sc.ellipsoid((sx * 5.2, 12.6, 17.2), (2.6, 2.8, 2.6), mat='stache', k=1.5, **St)
    Hc = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -16.4, -1.0), (19.2, 3.4, 20.4), mat='capband', k=0, **Hc)
    sc.ellipsoid((0, -23.0, -1.5), (19.8, 8.0, 21.2), mat='cap', k=2.0, **Hc)
    sc.ellipsoid((0, -29.0, -1.5), (18.4, 2.8, 19.8), mat='cap', k=2.5, **Hc)
    sc.ellipsoid((0, -14.0, 14.5), (15.0, 1.7, 9.5), R=rotm(0, -22, 0), mat='visor', k=0,
                 clip=lambda L: L[..., 2] > 6.0, **Hc)
    bf = shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.94, drop=7.0)
    C_ = dict(frame=bf, group='collar')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.5, 87, 3), (9.5, 8.6, 9.0), mat='coat2', k=3, **C_)
    sc.ellipsoid((0, 84, -9), (15, 9, 7), mat='coat2', k=3, **C_)
    sc.ellipsoid((0, 90.5, 8.5), (6.0, 2.6, 5.2), mat='shirt', group='shirt', frame=bf)
    sc.ellipsoid((0.3, 93.5, 11.0), (2.0, 2.4, 2.0), mat='tie', group='tie', frame=bf)
    sc.ellipsoid((-16, 112, 18.5), (2.4, 24, 1.0), R=rotm(0, 0, -32), mat='strap', group='strap', frame=bf)
    ramps = {
        'skin': SKIN_V,
        'hair': ramp('#0E1014', '#22262C', '#3E4248', '#62666A', '#8C8E8C', '#B4B4AC', '#D4D2C6'),
        'stache': ramp('#101216', '#262A30', '#44484C', '#6A6C6C', '#929290', '#B8B6AE', '#D6D2C6'),
        'cap': ramp('#030409', '#070A14', '#0D1222', '#151C32', '#202A46', '#30405E', '#465478'),
        'capband': ramp('#020306', '#05070C', '#090C14', '#0F141E', '#161D2A', '#22293A', '#30384C'),
        'visor': ramp('#020305', '#05070A', '#0A0D12', '#11151C', '#1C222C', '#3A4452', '#7A8696'),
        'coat': ramp('#030409', '#070A15', '#0D1324', '#151E36', '#212C4A', '#323E60', '#4A5474'),
        'coat2': ramp('#030409', '#060914', '#0B1120', '#131B30', '#1E2842', '#2E3A58', '#444E6E'),
        'shirt': ramp('#14161C', '#2A2C34', '#4A4C52', '#76766E', '#A4A090', '#C8C2AA', '#E0D8BE'),
        'tie': ramp('#04050A', '#0A0C14', '#10141E', '#18202C', '#22303E', '#2E4050', '#3C5262'),
        'strap': ramp('#060506', '#110C0E', '#1E1516', '#2E201C', '#423024', '#5A422E', '#76583A'),
    }

    def pre(img, sc, info):
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-26, 100, -22, 112), (23, 99, 20, 112)])

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # winged-wheel railway badge (brass) on the cap band: no state insignia
        o, R = fr[0], fr[1]
        p = o + R @ (np.array([0.0, -16.8, 20.0]) * fr[2])
        stamp(img, ['bb.o.bb', '.bbObb.', 'bb.o.bb'], p[0] + 1, p[1],
              {'b': hexc('#B88E40'), 'o': hexc('#7A5A24'), 'O': hexc('#E8C878')}, anchor=(3, 1))
        # brass buttons on the coat front
        for (bx, by) in ((61, 105), (63, 110)):
            if sc.mat[by, bx] >= 0:
                img[by, bx] = hexc('#D2A850')
                if by + 1 < H:
                    img[by + 1, bx] = hexc('#7A5A24')
        wrinkles(img, sc, skin_mask, lit_at, SKIN_V)
        # tired eyes: a soft bag under the near eye
        x, y, _ = project(sc, 'eye_n')
        R7 = np.stack(SKIN_V)
        stamp(img, ['.ccc.'], x - 1, y + 3, {'c': R7[2] if not lit_at(x, y + 3) else R7[3]}, mask=skin_mask)

    out, info = finish_c3(sc, LOOK_VELTRAVA, ramps, expr, feat(VELTRAVA_FEAT, brow='#7A7874', brow2='#A6A49E'),
                          extra, pre=pre, mouth=(expr == 'surprised'))
    return out


# =================================================================================== VORONOVA
def voronova_portrait(expr):
    sc = Scene()
    jd = 1.8 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 55.0, 0.0), yaw=22.0, pitch=3.0, roll=-1.0, scale=1.14)
    add_head(sc, fr, dict(jaw_w=14.2, crown_w=18.6, nose_len=0.95, nose_w=1.02, chin=0.96, jaw_drop=jd,
                          lip_w=1.0, lip_l=1.05, face_h=0.96))
    E = dict(frame=fr, group='head')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.0, 11.5, 7.5), (5.0, 5.0, 5.4), mat='skin', k=3, **E)
    sc.ellipsoid((0, -5.0, -3.0), (19.4, 18.5, 21.4), mat='hair', group='hair', frame=fr,
                 clip=lambda L: ((L[..., 2] < 3.0) | (L[..., 1] < -10.5)) & (L[..., 1] > -16.0) & (L[..., 1] < 6.0))
    Hh = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -20.0, -1.5), (19.2, 7.4, 22.6), mat='fur', k=0, **Hh)
    sc.ellipsoid((0, -26.0, -1.5), (17.6, 4.0, 21.2), mat='fur', k=3, **Hh)
    for sz in (-1, 1):
        sc.ellipsoid((0, -27.0, sz * 11.0), (16.0, 3.4, 9.0), mat='fur', k=2.0, **Hh)          # front / back peaks
    bf = shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.98, drop=6.0)
    C_ = dict(frame=bf, group='collar')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 15.0, 92, 4), (13.0, 11.0, 12.0), mat='fur2', k=4, **C_)
    sc.ellipsoid((0, 86, -7), (19, 11, 9), mat='fur2', k=4, **C_)
    for sx in (-1, 1):
        sc.ellipsoid((sx * 8.0, 106, 13), (6.0, 14.0, 4.5), R=rotm(0, 0, sx * -14), mat='fur2', k=3, **C_)
    ramps = {
        'skin': SKIN_W,
        'hair': ramp('#0E0E12', '#22201E', '#3A3430', '#58504A', '#7A6E64', '#9A8C80', '#B8A898'),
        'fur': ramp('#060608', '#101014', '#1C1C22', '#2C2C34', '#424248', '#5E5E64', '#7E7E84'),
        'fur2': ramp('#060608', '#0E0E12', '#1A1A20', '#2A2A30', '#3E3E44', '#58585E', '#76767C'),
        'coat': ramp('#070506', '#140D0C', '#241814', '#38261C', '#503628', '#6A4A36', '#866046'),
    }

    def pre(img, sc, info):
        # karakul: tight curls -> scattered light and dark flecks on the fur surfaces
        yy, xx = np.mgrid[0:H, 0:W]
        h = hash2(xx, yy)
        for name in ('fur', 'fur2'):
            m = mat_mask(sc, name) & (info['tone'] >= 1)
            tone_shift(img, sc, info, ramps, name, m & (h < 4), +1)
            tone_shift(img, sc, info, ramps, name, m & (h >= 4) & (h < 8), -1)
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-27, 100, -23, 112), (25, 99, 21, 112)])

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        wrinkles(img, sc, skin_mask, lit_at, SKIN_W)

    out, info = finish_c3(sc, LOOK_VELTRAVA, ramps, expr,
                          feat(VELTRAVA_FEAT, brow='#4A3E38', brow2='#6E6058', lip='#A46A5C'), extra, pre=pre)
    return out


# =================================================================================== KESSLER
def kessler_portrait(expr):
    sc = Scene()
    jd = 1.6 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 55.0, 0.0), yaw=26.0, pitch=-2.0, roll=0.0, scale=1.2)
    add_head(sc, fr, dict(jaw_w=13.8, crown_w=18.6, nose_len=1.12, nose_w=0.9, chin=1.06, jaw_drop=jd,
                          lip_w=0.9, lip_l=0.78, face_h=1.0))
    sc.ellipsoid((0, -4.0, -4.0), (18.9, 18.5, 20.6), mat='hair', group='hair', frame=fr,
                 clip=lambda L: (L[..., 2] < 3.0) & (L[..., 1] > -16.0) & (L[..., 1] < 8.0))
    Hh = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -22.0, -1.0), (17.8, 8.5, 19.0), mat='hat', k=0, **Hh)
    sc.ellipsoid((0, -29.0, -1.5), (15.0, 7.0, 16.4), mat='hat', k=4, **Hh)
    for sx in (-1, 1):                                                                 # centre gutter crease
        sc.ellipsoid((sx * 5.4, -33.5, -2.0), (6.4, 3.0, 13.4), mat='hat', k=2.5, **Hh)
    sc.ellipsoid((0, -16.8, -1.0), (18.2, 2.6, 19.6), mat='band', k=0.4, **Hh)
    sc.ellipsoid((0, -14.6, 1.0), (26.0, 1.9, 27.6), R=rotm(0, -5, 0), mat='brim', k=0, **Hh)
    sc.ellipsoid((0, -15.6, 1.0), (26.6, 2.4, 28.2), R=rotm(0, -5, 0), mat='brim', k=0,
                 clip=lambda L: (L[..., 0] / 26.6) ** 2 + (L[..., 2] / 28.2) ** 2 > 0.84, **Hh)  # curled edge
    bf = shoulders(sc, cx=57.0, yaw=20.0, mat='coat', width=0.9, drop=5.0)
    C_ = dict(frame=bf, group='collar')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.5, 87, 2.5), (9.6, 9.0, 9.4), mat='velvet', k=3, **C_)
    sc.ellipsoid((0, 84, -9), (15, 9, 7), mat='velvet', k=3, **C_)
    sc.ellipsoid((0, 90.5, 9.0), (6.4, 3.0, 5.4), mat='shirt', group='shirt', frame=bf)
    sc.ellipsoid((0.4, 97, 13.5), (2.0, 6.5, 1.2), mat='tie', group='tie', frame=bf)
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 12.0, 104, 15.5), (5.0, 17, 1.4), R=rotm(0, 0, sx * -20), mat='coat2', k=0, **L_)
    ramps = {
        'skin': SKIN_P,
        'hair': ramp('#0C0E12', '#1E2024', '#34363A', '#525452', '#76766E', '#9A988C', '#B8B4A6'),
        'hat': ramp('#040406', '#0A0A0E', '#121216', '#1C1C22', '#2A2A30', '#3E3C40', '#565256'),
        'brim': ramp('#030304', '#08080A', '#0E0E12', '#18181C', '#242428', '#363438', '#4C484C'),
        'band': ramp('#020203', '#050506', '#08080A', '#0E0E10', '#141418', '#1E1E22', '#28282E'),
        'coat': ramp('#040608', '#0A0E12', '#12171C', '#1C2228', '#2A3036', '#3E4448', '#56585A'),
        'coat2': ramp('#040608', '#090C10', '#10141A', '#191E24', '#262C32', '#383E44', '#4E5256'),
        'velvet': ramp('#020304', '#050608', '#090B0E', '#0F1216', '#161A1E', '#20252A', '#2C3236'),
        'shirt': ramp('#14161C', '#2A2C34', '#4A4C52', '#80807A', '#B0AC9C', '#D4CEB6', '#ECE4CA'),
        'tie': ramp('#040408', '#0A0A10', '#12121A', '#1A1A26', '#242434', '#302E44', '#3E3A54'),
    }

    def pre(img, sc, info):
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-25, 100, -22, 112), (24, 99, 21, 112)])

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # thin steel half-rim spectacles (lighter, finer than Emil's): upper rim + glints
        spectacles(img, sc, lit_at, frame_c=hexc('#6E7478'), glint=hexc('#E8ECEE'), glint2=hexc('#9EAAB2'),
                   rx=(4, 3), ry=3.0, thin=True)
        Rk = np.stack(SKIN_P)
        x, y, _ = project(sc, 'nostril')
        stamp(img, ['c..', '.c.', '.c.', '..c'], x - 5, y + 1, {'c': Rk[2] if not lit_at(x - 4, y + 2) else Rk[3]},
              mask=skin_mask)

    out, info = finish_c3(sc, LOOK_PALAIS, ramps, expr, feat(PALAIS_FEAT, brow='#4A4442', brow2='#7A746E',
                                                             lip='#A06858', iris='#3A4450'),
                          extra, pre=pre)
    return out


# =================================================================================== TYPIST
def typist_portrait(expr):
    sc = Scene()
    jd = 2.0 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 53.0, 0.0), yaw=22.0, pitch=4.0, roll=-3.0, scale=1.12)
    add_head(sc, fr, dict(jaw_w=13.4, crown_w=18.2, nose_len=0.92, nose_w=0.96, chin=0.92, jaw_drop=jd,
                          lip_w=1.0, lip_l=1.12, face_h=0.95))
    E = dict(frame=fr, group='head')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.2, 5.0, 11.0), (6.4, 5.6, 6.4), mat='skin', k=4, **E)            # round cheeks

    def hair_clip(L):
        x, y, z = L[..., 0], L[..., 1], L[..., 2]
        face = (z > 2.0) & (y > -11.0 + 0.02 * x * x)
        return ~face & (y < 6.0)
    Hh = dict(frame=fr, group='hair')
    sc.ellipsoid((0, -9.0, -1.5), (21.0, 22.6, 23.0), mat='hair', k=0, clip=hair_clip, **Hh)
    for (cx_, cy_, cz_) in ((-14, -14, 8), (-6, -20, 12), (4, -21, 11), (13, -15, 8), (-18, -4, -2),
                            (17, -5, -2), (-10, -20, -10), (10, -20, -10), (0, -24, 0)):     # set curls
        sc.ellipsoid((cx_, cy_, cz_), (6.2, 5.6, 6.2), mat='hair', k=3.5,
                     clip=lambda L: ~((L[..., 2] > 2.0) & (L[..., 1] > -11.0 + 0.02 * L[..., 0] ** 2)), **Hh)
    bf = shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.88, drop=9.0)
    sc.ellipsoid((0, 93, 4), (12.0, 6.0, 11.0), mat='blouse', group='blouse', frame=bf)
    for sx in (-1, 1):
        sc.ellipsoid((sx * 5.2, 95.5, 12.5), (5.4, 3.2, 2.0), R=rotm(0, 0, sx * 18), mat='blouse', k=1.2,
                     group='collar', frame=bf)
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 9.5, 106, 14.5), (4.2, 15, 1.3), R=rotm(0, 0, sx * -14), mat='coat2', k=0, **L_)
    ramps = {
        'skin': SKIN_W,
        'hair': ramp('#0A0808', '#18100E', '#2A1C16', '#40291E', '#5A3C2A', '#765236', '#926A46'),
        'coat': ramp('#0E0C0A', '#221C16', '#3A3022', '#584A34', '#76644A', '#94805E', '#B09C76'),
        'coat2': ramp('#0E0C0A', '#1E1814', '#342A1E', '#50432E', '#6C5A42', '#8A7656', '#A6906C'),
        'blouse': ramp('#14161C', '#2C2E36', '#4E5056', '#82827A', '#B2AE9E', '#D6D0B8', '#EEE6CC'),
    }

    def pre(img, sc, info):
        # knitted cardigan: vertical rib lines
        xx = np.mgrid[0:H, 0:W][1]
        rib = mat_mask(sc, 'coat') & (xx % 3 == 0) & (info['tone'] >= 2)
        tone_shift(img, sc, info, ramps, 'coat', rib, -1)
        # set curls: short arcs in the hair
        yy, xx2 = np.mgrid[0:H, 0:W]
        h = hash2(xx2, yy, 31, 17, 13)
        tone_shift(img, sc, info, ramps, 'hair', mat_mask(sc, 'hair') & (h < 2), +1)
        tone_shift(img, sc, info, ramps, 'hair', mat_mask(sc, 'hair') & (h >= 2) & (h < 4), -1)

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # pencil behind the near ear: yellow shaft, dark tip, pointing back and up
        x, y, _ = project(sc, 'ear')
        for k in range(9):
            px_, py_ = int(round(x + 7 - k)), int(round(y - 3 - k * 0.55))
            if 0 <= px_ < W and 0 <= py_ < H:
                img[py_, px_] = hexc('#D0A040') if k < 7 else hexc('#3A2E28')
                if k < 7 and 0 <= py_ + 1 < H:
                    img[py_ + 1, px_] = hexc('#8C6424')
        # grey strands at the temple
        Lh = local_coords(sc, fr)
        grey = mat_mask(sc, 'hair') & (np.abs(Lh[..., 0] + 15) < 3) & (Lh[..., 1] > -12) & ((Lh[..., 1] % 3) < 1)
        img[grey] = hexc('#8C847A')

    out, info = finish_c3(sc, LOOK_PALAIS, ramps, expr, feat(PALAIS_FEAT, lip='#AC6A5C', brow='#3A2820',
                                                             brow2='#5A4030'), extra, pre=pre,
                          creases=(expr != 'neutral'))
    return out


# =================================================================================== JOURNALIST
def journalist_portrait(expr):
    sc = Scene()
    jd = 2.2 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 54.0, 0.0), yaw=27.0, pitch=3.0, roll=-3.0, scale=1.18)
    add_head(sc, fr, dict(jaw_w=14.4, crown_w=18.8, nose_len=1.0, nose_w=1.0, chin=1.08, jaw_drop=jd,
                          lip_w=1.0, lip_l=0.95, face_h=1.02))

    def hair_clip(L):
        x, y, z = L[..., 0], L[..., 1], L[..., 2]
        face = (z > 3.0) & (y > -13.5 + 0.018 * x * x)
        ear = (np.abs(x) > 16.0) & (y > -3.0) & (z > -5.0)
        return ~face & ~ear & (y < 6.0)
    Hh = dict(frame=fr, group='hair')
    sc.ellipsoid((0, -9.5, -2.0), (20.0, 22.4, 22.6), mat='hair', k=0, clip=hair_clip, **Hh)
    for (cx_, cy_, cz_, rx_) in ((6, -24, 12, 7.5), (-4, -26, 6, 7.0), (12, -20, 15, 5.5), (-12, -22, -4, 7.0),
                                 (2, -25, -10, 7.5), (-17, -12, -10, 5.5)):          # tousled tufts
        sc.ellipsoid((cx_, cy_, cz_), (rx_, 5.0, rx_), mat='hair', k=3.0, clip=hair_clip, **Hh)
    sc.ellipsoid((9.0, -16.0, 16.5), (6.0, 3.2, 3.6), R=rotm(0, 0, -25), mat='hair2', group='fringe', frame=fr)
    bf = shoulders(sc, cx=57.0, yaw=20.0, mat='coat', width=0.94, drop=6.0)
    S = dict(frame=bf, group='scarf')
    sc.ellipsoid((0, 87, 2), (14.5, 7.0, 12.5), mat='scarf', k=0, **S)
    sc.ellipsoid((-5, 93, 10), (7.5, 6.0, 5.5), mat='scarf', k=3, **S)
    sc.ellipsoid((4, 106, 13.5), (4.8, 14.0, 2.6), R=rotm(0, 0, 4), mat='scarf2', k=1.5, **S)
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 12.0, 104, 15.5), (5.0, 17, 1.4), R=rotm(0, 0, sx * -20), mat='coat2', k=0, **L_)
    sc.ellipsoid((-15, 112, 18.8), (1.8, 24, 1.0), R=rotm(0, 0, -34), mat='strap', group='strap', frame=bf)
    ramps = {
        'skin': SKIN_P,
        'hair': ramp('#0C0A08', '#221C12', '#40341E', '#64522E', '#8A7444', '#B09860', '#D2BC84'),
        'hair2': ramp('#0C0A08', '#201A10', '#3C301C', '#5E4C2C', '#846C40', '#A8905A', '#CAB27C'),
        'coat': ramp('#0A0806', '#1A140E', '#2C2418', '#433624', '#5C4C34', '#766446', '#907C5A'),
        'coat2': ramp('#0A0806', '#17120C', '#281F15', '#3D3020', '#54442E', '#6C5A40', '#867254'),
        'scarf': ramp('#04060A', '#0A1018', '#121C2A', '#1C2C40', '#2A3E58', '#3C5472', '#546E8C'),
        'scarf2': ramp('#04060A', '#091018', '#101A28', '#19283C', '#263854', '#384C6C', '#4E6486'),
        'strap': ramp('#060506', '#110C0E', '#1E1516', '#2E201C', '#423024', '#5A422E', '#76583A'),
    }

    def pre(img, sc, info):
        yy, xx = np.mgrid[0:H, 0:W]
        h = hash2(xx, yy)
        cm = mat_mask(sc, 'coat') | mat_mask(sc, 'coat2')
        tone_shift(img, sc, info, ramps, 'coat', cm & (h < 4), -1)                   # tweed flecks
        tone_shift(img, sc, info, ramps, 'coat', cm & (h == 11), +1)
        tone_shift(img, sc, info, ramps, 'coat2', cm & (h < 4), -1)
        rib = mat_mask(sc, 'scarf') & (xx % 2 == 0) & (info['tone'] >= 2)            # knitted scarf
        tone_shift(img, sc, info, ramps, 'scarf', rib, -1)
        Lh = local_coords(sc, fr)
        strands = mat_mask(sc, 'hair') & (((Lh[..., 0] * 0.6 + Lh[..., 1]) % 5.0) < 1.0) & (info['tone'] >= 3)
        tone_shift(img, sc, info, ramps, 'hair', strands, -1)
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-26, 100, -22, 112), (24, 99, 20, 112)])

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # light stubble on the lit jaw (long nights at the press room)
        Lc = local_coords(sc, fr)
        jaw = skin_mask & (Lc[..., 1] > 16.0) & (Lc[..., 1] < 24) & (info['val'] > 0.30) & dither_mask(level=0.10)
        R = np.stack(SKIN_P)
        img[jaw] = R[np.clip(info['tone'] - 1, 0, 6)][jaw]
        # camera top plate at the bottom of the frame (chrome edge + black body)
        stamp(img, ['.XXXXXXXX..', 'xkkkkkkkkx.', 'kkkkkkkkkkk'], 70, 109,
              {'X': hexc('#C8CCD0'), 'x': hexc('#6E7276'), 'k': hexc('#0E0E12')})

    out, info = finish_c3(sc, LOOK_PALAIS, ramps, expr, feat(PALAIS_FEAT, brow='#6A5636', brow2='#9A8256',
                                                             iris='#3A4A58'), extra, pre=pre)
    return out


# ----------------------------------------------------------------------------------- table + build
PORTRAITS_C3 = {
    'elena': elena_portrait, 'border_officer': border_officer_portrait, 'conductor': conductor_portrait,
    'voronova': voronova_portrait, 'kessler': kessler_portrait, 'typist': typist_portrait,
    'journalist': journalist_portrait,
}


def strip_for(cid):
    return np.concatenate([PORTRAITS_C3[cid](e) for e in EXPRESSIONS], 1)


def build(ids, out_dir, prev_dir, reference=()):
    """Write portrait.png / portrait.json for `ids` and the review sheets (new cast next to the
    reference portraits) into prev_dir."""
    strips = {}
    for cid in ids:
        if cid not in PORTRAITS_C3:
            continue
        strip = strip_for(cid)
        d = os.path.join(out_dir, cid)
        os.makedirs(d, exist_ok=True)
        Image.fromarray(strip, 'RGBA').save(os.path.join(d, 'portrait.png'))
        with open(os.path.join(d, 'portrait.json'), 'w', encoding='utf-8') as f:
            json.dump({'size': [W, H], 'expressions': EXPRESSIONS}, f, indent=1)
        Image.fromarray(strip, 'RGBA').resize((strip.shape[1] * 3, strip.shape[0] * 3), Image.NEAREST).save(
            os.path.join(prev_dir, f'c3_{cid}_portraits_3x.png'))
        strips[cid] = strip
        print(f'portrait {cid}: {len(EXPRESSIONS)} expressions')
    if strips:
        rows = []
        root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        for cid in reference:
            p = os.path.join(root, 'assets', 'characters', cid, 'portrait.png')
            if os.path.exists(p):
                rows.append(np.asarray(Image.open(p).convert('RGBA')))
        rows += list(strips.values())
        allp = np.concatenate(rows, 0)
        Image.fromarray(allp, 'RGBA').resize((allp.shape[1] * 2, allp.shape[0] * 2), Image.NEAREST).save(
            os.path.join(prev_dir, 'c3_portraits_all_2x.png'))
    return strips


if __name__ == '__main__':
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, '..', '..'))
    out = os.path.join(root, 'assets', 'characters')
    prev = os.path.join(out, '_preview')
    os.makedirs(prev, exist_ok=True)
    open(os.path.join(prev, '.gdignore'), 'a').close()
    build(sys.argv[1:] or list(PORTRAITS_C3), out, prev, reference=['alexei', 'konrad', 'irina', 'emil'])
