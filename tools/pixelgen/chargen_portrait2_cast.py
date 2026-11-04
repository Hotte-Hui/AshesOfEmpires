"""chargen_portrait2_cast -- garments, hats, hair and the nine speaking characters of the dialogue busts.

Builders return SDF nodes in the HEAD-local frame (hats, hair, glasses, beards) or in the TORSO-local frame
(garments; origin at the pit of the neck, y down, z forward).  Character specs bundle: head shape
overrides, pose per expression, palette ramps per material, light/background, builders and 2D passes.
"""
from __future__ import annotations

import numpy as np

import chargen_portrait2_sdf as S
from chargen_portrait2_paint import MatStyle, ramp

E = S.Ellipsoid


def slab_y(y0, y1):
    """Signed slab y0 < y < y1."""
    return lambda P: np.maximum(P[:, 1] - y1, y0 - P[:, 1])


# ======================================================================================= head items
def fedora(M, hp, tilt=(5.0, -3.0), y0=-12.4, z0=-5.2, band_r=(17.4, 21.6), crown_h=17.5, brim_w=10.2,
           taper=0.17):
    """Felt fedora: tapered crown with centre crease and front pinches, ribbon band, snap brim (front down,
    sides curled up).  Hat frame origin = centre of the band's lower edge (head-local y0/z0)."""
    felt, band, brim_m = M('felt'), M('ribbon'), M('brim')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = band_r

    def tap(P):
        s_ = 1.0 + taper * np.clip(-P[:, 1] / crown_h, 0, 1)
        off = np.zeros_like(P)
        off[:, 0] = P[:, 0] - P[:, 0] * s_
        off[:, 2] = P[:, 2] - P[:, 2] * s_
        return off

    base = S.Warp(S.EllipticCylinder((0, -(crown_h - 4.0) / 2, 0), rx, rz, (crown_h + 4.0) / 2, felt, e=3.2),
                  tap, lip=1.15)
    crown = base
    crown = S.Sub(crown, E((0, -crown_h - 0.9, -3.0), (3.4, 3.6, rz * 0.52), felt), k=2.0)
    for sx in (1, -1):
        crown = S.Sub(crown, E((sx * 8.2, -crown_h + 3.4, rz * 0.90), (2.0, 4.0, 2.4), felt), k=2.2)
    bandn = S.EllipticCylinder((0, -2.0, 0), rx + 0.45, rz + 0.45, 1.75, band, e=0.4)

    def snap(P):
        x, z = P[:, 0], P[:, 2]
        off = np.zeros_like(P)
        off[:, 1] = (-0.013 * np.maximum(np.abs(x) - rx * 0.8, 0) ** 2
                     + 0.07 * np.maximum(z - rz * 0.75, 0) + 0.05 * np.minimum(z + rz * 0.75, 0))
        return off

    brimn = S.Warp(S.EllipticCylinder((0, 0.2, 0.6), rx + brim_w, rz + brim_w + 1.0, 0.8, brim_m, e=0.7),
                   snap, lip=1.3)
    hat = S.Union([crown, bandn, brimn])
    # clip volume for the head: inside the crown (shrunk 0.6 px) or below the brim plane
    inner = S.Offset(base, -0.7)
    allowed = S.Union([inner, S.Fn(lambda P: -(P[:, 1] - 1.6), felt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def hair_short(M, hp, hairline=-15.0, front_z=7.0, nape=9.0, burn_y=1.0, burn_z=-3.0, thick=0.9, mat='hair',
               back_z=-9.0):
    m = M(mat)
    shell = S.Offset(E(hp['skull_c'], hp['skull_r'], m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = np.minimum(y - hairline, z - front_z)
        nap = y - nape
        side = np.minimum(y - burn_y, z - burn_z)
        # around the ear: only a thin sideburn in front of it, hair again behind it
        ear = np.maximum(np.maximum(y + 3.5, -y + 9.5), np.maximum(z - burn_z, back_z - z))
        return np.maximum(np.maximum(np.maximum(front, nap), side), -ear)

    return S.Inter(shell, S.Fn(region, m))


# ======================================================================================= garments
def coat_layers(M, torso_node, coat='coat', inner='shirt', v_open=0.45, v_top=2.0, coat_t=2.6,
                lapel=True, collar=True, collar_h=7.0, quilt=None, collar_r=(10.8, 13.0)):
    """Coat shell with a V opening over an inner layer; optional stand/turned collar and lapels;
    quilt = (period, amp) adds padded channels."""
    mc, mi = M(coat), M(inner)
    ml = M(coat + '_lapel')
    coatn = S.Offset(torso_node, coat_t, mc)
    if quilt:
        coatn = quilted(coatn, period=quilt[0], amp=quilt[1])

    def vwedge(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        return np.maximum(3.0 - z, np.abs(x) - (y - v_top) * v_open)

    coatn = S.Sub(coatn, S.Fn(vwedge, mc), k=0.8)
    parts = [coatn, S.Offset(torso_node, 1.0, mi)]
    if lapel:
        parts.append(lapels(M, torso_node, coat_t, v_open, v_top, mat=coat + '_lapel'))
    if collar:
        col = S.Shell(S.RoundCone((0, -collar_h, -2.5), (0, 3.0, -1.0), collar_r[0], collar_r[1], mc), 1.1, mc)
        col = S.Inter(col, S.Fn(lambda P: np.maximum(P[:, 1] - 3.0, -collar_h - P[:, 1]), mc))
        col = S.Sub(col, S.Fn(lambda P: np.maximum(6.0 - P[:, 2], np.abs(P[:, 0]) - 6.0), mc), k=1.0)
        parts.append(col)
    return S.Union(parts, k=[0.0] + [1.2] * (len(parts) - 2) if len(parts) > 2 else 0.0)


def scarf_wrap(M, mat='scarf', y=-2.0, r=10.6, tube=4.4, ends=True, lean=0.0, end_pts=None, seed=3):
    """Wool scarf wrapped once around the neck (lumpy roll) with one end hanging in front, tucked into the
    coat (end_pts = polyline of the hanging end in torso-local coordinates)."""
    m = M(mat)
    parts = []
    for i in range(12):
        a = np.radians(i * 30.0)
        wob = 0.9 * np.sin(a * 2.0 + 0.7)
        tb = tube * (1.0 + 0.12 * np.sin(a * 3.0 + 1.3))
        parts.append(E((r * np.sin(a), y + wob + lean * np.cos(a), -1.0 + r * np.cos(a)),
                       (tb + 0.5, tb * 0.95, tb + 0.5), m))
    if ends == 'drape':
        # both ends crossed over the chest and tucked into the coat: a soft folded mass in the V opening
        parts.append(E((-1.2, y + 13.0, 11.6), (5.6, 9.5, 3.0), m, R=S.rot(0, 0, 10)))
        parts.append(E((2.4, y + 16.0, 11.0), (4.2, 9.0, 2.6), m, R=S.rot(0, 0, -14)))
    elif ends:
        pts = end_pts or [(-2.0, y + 3.0, 12.0), (-4.0, y + 12.0, 13.4), (-5.0, y + 22.0, 14.2)]
        for i in range(len(pts) - 1):
            parts.append(S.RoundCone(pts[i], pts[i + 1], 4.0 - i * 0.3, 3.7 - i * 0.3, m))
    node = S.Union(parts, k=2.4)
    return S.Displace(node, lambda P: S.vnoise3(P, 2.2, seed), amp=0.45, lipschitz=1.3)


def rollneck(M, mat='knit', y_top=-12.0, y_bot=4.0, r=(10.0, 11.6), z=-0.8):
    """Roll-neck sweater collar: a folded knitted tube around the neck (torso-local)."""
    m = M(mat)
    tube = S.RoundCone((0, y_top, z), (0, y_bot, z + 0.6), r[0], r[1], m)
    fold = E((0, y_top + 3.2, z), (r[0] + 1.0, 2.6, r[0] + 1.0), m)
    return S.Union([tube, fold], k=1.4)


def band_on(M, torso_node, lift, p0, angle_deg, width, mat, y_range=None, x_range=None):
    """A flat band lying ON the torso surface (offset by `lift`): straps, belts, lapels.  The band follows a
    straight line through p0 (x, y) at angle_deg in the x/y plane, `width` px wide."""
    m = M(mat)
    a = np.radians(angle_deg)
    n = np.array([-np.sin(a), np.cos(a)])

    def region(P):
        dd = np.abs((P[:, 0] - p0[0]) * n[0] + (P[:, 1] - p0[1]) * n[1]) - width / 2
        dd = np.maximum(dd, 2.0 - P[:, 2])
        if y_range is not None:
            dd = np.maximum(dd, np.maximum(y_range[0] - P[:, 1], P[:, 1] - y_range[1]))
        if x_range is not None:
            dd = np.maximum(dd, np.maximum(x_range[0] - P[:, 0], P[:, 0] - x_range[1]))
        return dd

    return S.Inter(S.Offset(torso_node, lift, m), S.Fn(region, m))


def lapels(M, torso_node, coat_t, v_open, v_top, width=5.5, y_end=30.0, mat='coat_lapel'):
    """Flat lapels folded back along both edges of the coat's V opening."""
    m = M(mat)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        edge = (y - v_top) * v_open
        dd = np.abs(np.abs(x) - edge - width / 2) - width / 2
        dd = np.maximum(dd, 3.0 - z)
        dd = np.maximum(dd, np.maximum(v_top - y, y - y_end))
        return dd

    return S.Inter(S.Offset(torso_node, coat_t + 0.7, m), S.Fn(region, m))


def strap(M, pts, r=1.3, mat='strap'):
    m = M(mat)
    segs = [S.RoundCone(pts[i], pts[i + 1], r, r, m) for i in range(len(pts) - 1)]
    return S.Union(segs, k=0.5)


def tie(M, mat='tie', top=(0.0, 4.0, 13.4), bot=(0.6, 30.0, 14.6)):
    m = M(mat)
    return S.Union([S.RoundCone(top, (top[0] + 0.1, top[1] + 2.4, top[2] + 0.4), 1.8, 1.6, m),
                    S.RoundCone((top[0] + 0.1, top[1] + 2.4, top[2] + 0.4), bot, 1.4, 2.6, m)], k=0.6)


# ======================================================================================= palettes
# shared skin ramps (dark -> light): navy core, violet shadow, warm half-tones, ochre light
SKIN_BERLIN = ramp('#0b0d16', '#1d1b28', '#372a37', '#5b3b43', '#86584f', '#b27b63', '#d4a17f', '#ecc9a1')
SKIN_KARSK = ramp('#080d14', '#1a1b24', '#36262e', '#5c3637', '#8a5242', '#b5724f', '#d69868', '#efc490')
SKIN_TH = [0.035, 0.085, 0.15, 0.25, 0.37, 0.55, 0.86]


def skin_styles(sk, rim, lip=None):
    st = MatStyle(sk, SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24, ao=0.75)
    lp = MatStyle(lip if lip is not None else sk, SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24, ao=0.75)
    return {'skin': st, 'ear': st, 'neck': st, 'lip': lp}


# ======================================================================================= characters
def konrad():
    rim = '#6e8fa6'
    sk = SKIN_BERLIN
    lip = ramp('#0b0d16', '#1d1b28', '#3a2834', '#603842', '#8c5250', '#b37064', '#d29680', '#e9bc9c')
    styles = skin_styles(sk, rim, lip)
    styles.update({
        'felt': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3b353d', '#504748', '#685c58',
                              '#837468'), [0.03, 0.08, 0.15, 0.25, 0.38, 0.55, 0.75], dither=0.05, rim='#56708a'),
        'brim': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3b353d', '#504748', '#685c58',
                              '#837468'), [0.03, 0.08, 0.15, 0.25, 0.38, 0.55, 0.75], dither=0.0, rim='#56708a'),
        'ribbon': MatStyle(ramp('#050508', '#0c0b10', '#16141a', '#221e25', '#302a32'),
                           [0.06, 0.16, 0.32, 0.55], rim='#3f526a'),
        'hair': MatStyle(ramp('#07080d', '#141218', '#221a1e', '#33262a', '#4a3533', '#614640'),
                         [0.05, 0.12, 0.24, 0.4, 0.6], rim='#4a5f74'),
        'coat': MatStyle(ramp('#05070d', '#0a0f1d', '#10182b', '#18233c', '#212f4f', '#2d3e63', '#3d5379'),
                         [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], dither=0.05, rim='#56769c'),
        'coat_lapel': MatStyle(ramp('#05070d', '#0a0f1d', '#10182b', '#18233c', '#212f4f', '#2d3e63',
                                    '#3d5379'), [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#56769c'),
        'shirt': MatStyle(ramp('#0c0e16', '#262935', '#4a4c56', '#77777b', '#a19d98', '#c6beb2'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#8ea2b4'),
        'tie': MatStyle(ramp('#0a0509', '#1d0b11', '#33131a', '#4d1d23', '#68292c'),
                        [0.06, 0.15, 0.3, 0.5], rim='#5a4a62'),
        'scarf': MatStyle(ramp('#0e0c0e', '#1f1a1b', '#352d2a', '#504536', '#6c5f48', '#88795c', '#a39373',
                               '#bcae8e'), [0.05, 0.12, 0.22, 0.35, 0.50, 0.68, 0.88], dither=0.04,
                          rim='#7f93a0'),
        'strap': MatStyle(ramp('#0a0607', '#1b0f0c', '#2e1a12', '#472918', '#633a22', '#7d4f30'),
                          [0.05, 0.12, 0.24, 0.40, 0.6], rim='#5a5a66'),
    })
    return dict(
        id='konrad', city='berlin',
        look=dict(key=(0.54, -0.42, 0.72), rim=(-0.80, -0.35, -0.50), ambient=0.07, bg='berlin',
                  glow=(0.80, 0.18)),
        head=dict(mid_h=(11.7, 7.0, 11.6), jaw_angle=(10.8, 15.4, -4.0), cheek_c=(10.4, 3.0, 10.2),
                  malar_r=(3.8, 3.4, 3.2), chin_h=(4.6, 3.3, 3.4), low_r=(11.4, 11.2, 12.8)),
        zoom=1.18,
        head_pos=(55.0, 53.0, 0.0), yaw=30.0, pitch=2.0, roll=0.0,
        torso_pos=(55.0, 89.0, -0.5), torso_yaw=14.0, torso=dict(width=0.98, depth=1.0, slope=1.2),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -2), 'determined': (1, -1, 1), 'surprised': (2, -4, 1)},
        head_items=[lambda M, hp: fedora(M, hp, y0=-13.2), lambda M, hp: hair_short(M, hp)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.42, v_top=3.0),
            lambda M, t: scarf_wrap(M, y=-6.0, r=10.9, tube=4.6, ends='drape'),
            lambda M, t: band_on(M, t, 3.3, (-6.0, 20.0), 38.0, 2.6, 'strap', y_range=(4.0, 60.0)),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'felt': 2, 'ribbon': 2, 'brim': 3,
                'coat': 4, 'coat_lapel': 8, 'shirt': 5, 'tie': 5, 'scarf': 6, 'strap': 7, 'body': 4},
        tone_passes=[pass_knit('scarf'), pass_grain('felt', 0.07, seed=3), pass_grain('coat', 0.05, seed=4),
                     pass_strands('hair')],
        eye=dict(iris='#4c6277', iris_d='#2a3747', sclera='#c9bfb2', sclera_d='#7d7480', lash='#140c10',
                 pupil='#0a0a10', catch='#f2ead8'),
        brow=dict(col='#2a1d1c', col_l='#47332c'),
        mouth=dict(line='#3a1a1e', corner='#55282a', inner='#1a0a0d', teeth='#b9ab9c', tongue='#6e2f33'),
        features=dict(
            extra=[ear_detail],
            brows={'neutral': dict(arch=0.6), 'concerned': dict(lift_inner=2.2, lift_outer=-0.4, arch=0.3),
                   'determined': dict(lift_inner=-1.7, arch=0.0, dy=0.5),
                   'surprised': dict(dy=-1.8, arch=1.3, lift_inner=0.4)},
            mouth={'neutral': dict(corner_drop=0.3), 'concerned': dict(corner_drop=1.0),
                   'determined': dict(corner_drop=0.6), 'surprised': dict(parted=2)},
        ),
        priority={'brim': 2, 'ribbon': 2, 'strap': 1},
    )


CAST = {'konrad': konrad}


# ======================================================================================= 2D passes
def _local(G, frame_key, mask):
    """Local coordinates (head / torso frame) of the pixels in mask (undoing the zoom)."""
    d = G['d']
    spec_zoom = G.get('zoom', 1.0)
    P = d.P[mask]
    c = np.array([56.0, 56.0, 0.0])
    P = (P - c) / spec_zoom + c
    fr = G[frame_key]
    return (P - fr.o) @ fr.R


def _hash2(x, y, seed):
    h = (x.astype(np.int64) * 374761393 + y.astype(np.int64) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def pass_knit(mat='scarf', ribs=26, seed=5):
    """Knitted ribs on a scarf wrapped around the neck (lines of constant angle around the neck axis),
    vertical ribs on the hanging/draped parts; one tone darker on every other rib."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone > 0)
        if not m.any():
            return tone
        L = _local(G, 'tf', m)
        ang = np.arctan2(L[:, 0], L[:, 2] + 1.0)
        ring = L[:, 1] < -1.0
        k_ring = np.floor((ang / (2 * np.pi) + 0.5) * ribs).astype(int)
        k_drape = np.floor((L[:, 0] + 40.0) / 1.6).astype(int)
        k = np.where(ring, k_ring, k_drape)
        dark = (k % 2 == 0)
        t = tone[m].copy()
        t = np.where(dark & (t >= 2), t - 1, t)
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def pass_grain(mat, density=0.10, seed=7, lo=2, hi=6):
    """Sparse 1-px grain (felt, wool): darkens isolated pixels inside mid tones, never at edges."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        d = G['d']
        m = (d.mat == M.names.index(mat)) & (tone >= lo) & (tone <= hi)
        ys, xs = np.nonzero(m)
        r = _hash2(xs, ys, seed)
        pick = r < density
        # keep a 1-px margin from other materials so silhouettes stay clean
        h, w = tone.shape
        ok = []
        for x, y in zip(xs[pick], ys[pick]):
            if 1 <= x < w - 1 and 1 <= y < h - 1 and (d.mat[y - 1:y + 2, x - 1:x + 2] == d.mat[y, x]).all():
                ok.append((x, y))
        tone = tone.copy()
        for x, y in ok:
            tone[y, x] -= 1
        return tone
    return fn


def pass_strands(mat='hair', seed=11, period=3, frame='hf', axis=1):
    """Hair strands: alternating darker streaks following the hair flow (constant x in head space)."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = _local(G, frame, m)
        ang = np.arctan2(L[:, 0], L[:, 2] + 5.0) * 9.0 + L[:, 1] * 0.18
        k = np.floor(ang).astype(int)
        r = _hash2(k, np.zeros_like(k), seed)
        dark = r < 0.38
        light = r > 0.86
        t = tone[m].copy()
        t = np.where(dark & (t >= 2), t - 1, np.where(light, t + 1, t))
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def ear_detail(spec, G, cv, expr, mouth_state, blink, v):
    """Near ear: lighter helix rim, dark concha + canal (only on 'ear' pixels)."""
    M = G['M']
    if 'ear' not in M.names:
        return
    eid = M.names.index('ear')
    ear = G['d'].mat == eid
    lm = G['lmv']['ear_r']
    ex, ey = int(np.floor(lm[0])), int(np.floor(lm[1]))
    rows = ["..++.", ".+--+", ".+-=.", ".+=-.", "..+-.", "...+."]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            x, y = ex - 2 + i, ey - 3 + j
            if 0 <= x < ear.shape[1] and 0 <= y < ear.shape[0] and ear[y, x]:
                cv.rel(x, y, {'+': 1, '-': -1, '=': -2}[ch], allow=ear)


# ======================================================================================= more head items
def ushanka(M, hp, flaps='down', seed=21, tilt=(3.0, -2.0), y0=-15.6, z0=-4.8, r=(18.4, 22.2), fur='fur',
            top='hat_top'):
    """Fur ushanka.  flaps='down': ear flaps hanging over the ears; 'up': flaps raised and tied on the crown."""
    mf, mt = M(fur), M(top)
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    dome = E((0, -1.0, 0), (rx - 1.2, 10.0, rz - 1.2), mt)
    dome = S.Inter(dome, S.Plane((0, 2.0, 0), (0, 1, 0), mt))
    parts = [dome]
    # turned-up front/side flap: a thick fur roll around the head (front 240 degrees)
    roll = []
    for i in range(17):
        a = np.radians(-128 + i * 16.0)
        # flat turned-up band: long along the tangent, tall, thin radially
        roll.append(E(((rx + 0.6) * np.sin(a), 0.6, (rz + 0.6) * np.cos(a)), (5.6, 5.4, 3.4), mf,
                      R=S.rot(np.degrees(a), 0, 0)))
    parts.append(S.Union(roll, k=2.4))
    if flaps == 'down':
        for sx in (1, -1):
            fl = S.RoundBox((sx * (rx - 0.2), 14.5, -3.4), (2.2, 12.0, 7.0), 2.0, mf, R=S.rot(sx * 8.0, 0, sx * 5.0))
            parts.append(fl)
            parts.append(S.RoundCone((sx * (rx + 0.6), 26.0, 0.5), (sx * (rx + 1.4), 31.0, 1.5), 0.55, 0.45,
                                     M('tie_string')))
        parts.append(E((0, 10.0, -rz + 2.0), (rx - 3.0, 11.0, 4.6), mf))       # back flap
    else:
        for sx in (1, -1):
            fl = S.RoundBox((sx * (rx - 9.5), -9.6, -2.0), (2.0, 5.6, 7.2), 1.9, mf, R=S.rot(0, 0, -sx * 62.0))
            parts.append(fl)
        parts.append(E((0, -12.4, -2.0), (1.8, 1.4, 1.8), M('tie_string')))
        parts.append(E((0, 6.0, -rz + 2.5), (rx - 4.0, 7.0, 4.2), mf))
    hat = S.Union(parts, k=[1.6] + [2.0] * (len(parts) - 2))
    hat = S.Displace(hat, lambda P: S.vnoise3(P * np.array([1.0, 0.6, 1.0], np.float32), 1.6, seed),
                     amp=0.75, lipschitz=1.35)
    allowed = S.Union([S.Offset(dome, -0.6), S.Fn(lambda P: -(P[:, 1] - 3.6), mt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def pass_fur(mat='fur', seed=31, frame='hf'):
    """Fur tufts: short vertical strokes of lighter / darker tone (clustered, never single noise)."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        d = G['d']
        mid = M.names.index(mat)
        m = (d.mat == mid) & (tone >= 1)
        ys, xs = np.nonzero(m)
        tone = tone.copy()
        r = _hash2(xs // 2, (ys + (xs // 2) % 3) // 3, seed)
        for x, y, rv in zip(xs, ys, r):
            if rv < 0.22 and tone[y, x] >= 2:
                tone[y, x] -= 1
            elif rv > 0.84:
                tone[y, x] += 1
        return tone
    return fn


def quilted(node, period=5.0, amp=0.55, axis=1):
    """Padded quilting: horizontal channels that bulge between stitch lines."""
    def fn(P):
        u = P[:, axis] / period
        return np.abs(np.sin(np.pi * u)) * 2.0 - 1.0
    return S.Displace(node, fn, amp=amp, lipschitz=1.25)


def pass_stitches(mat, period=5.0, seed=13, frame='tf', axis=1, dark=1):
    """Stitch lines of a quilted garment (follow the same channels as quilted())."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = _local(G, frame, m)
        u = L[:, axis] / period
        f = u - np.floor(u)
        line = (f < 0.12) | (f > 0.94)
        t = tone[m].copy()
        t = np.where(line, np.maximum(0, t - dark), t)
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def stubble(region=(11.0, 25.5), x_max=13.0, upper=(11.6, 13.4), seed=17, density=0.5):
    """Beard shadow: a dithered one-tone-darker pattern on the jaw, chin and upper lip (head-local mask)."""
    def fn(spec, G, cv, expr, mouth_state, blink, v):
        d = G['d']
        M = G['M']
        sk = [M.names.index(n) for n in ('skin', 'lip') if n in M.names]
        m = np.isin(d.mat, sk)
        ys, xs = np.nonzero(m)
        L = _local(G, 'hf', m)
        x, y, z = L[:, 0], L[:, 1], L[:, 2]
        jaw = (y > region[0]) & (y < region[1]) & (np.abs(x) < x_max) & (z > -4.0)
        lipzone = (np.abs(x) < 4.6) & (y > 13.4) & (y < 17.8)
        up_lip = (y > upper[0]) & (y < upper[1]) & (np.abs(x) < 4.8)
        sel = (jaw & ~lipzone) | up_lip
        sel &= d.mat[ys, xs] == M.names.index('skin')
        pat = ((xs + ys) % 2 == 0) | (_hash2(xs, ys, seed) < density * 0.3)
        for xx, yy, s_, p_ in zip(xs, ys, sel, pat):
            if s_ and p_:
                cv.rel(int(xx), int(yy), -1)
    return fn


def eye_bags(depth=-1):
    def fn(spec, G, cv, expr, mouth_state, blink, v):
        for key, w in (('eye_r', 5), ('eye_l', 4)):
            x, y = (int(np.floor(c)) for c in G['lmv'][key][:2])
            for i in range(w):
                cv.rel(x - w // 2 + i + (0 if key == 'eye_r' else 0), y + 4, depth)
    return fn


def alexei():
    rim = '#5f8a84'
    sk = SKIN_KARSK
    lip = ramp('#080d14', '#1a1b24', '#3a2630', '#603639', '#8a4c46', '#b0685a', '#cf8d72', '#e6b291')
    styles = skin_styles(sk, rim, lip)
    green = ramp('#050a09', '#0b1512', '#12201a', '#1b2c23', '#26392d', '#334938', '#445c45', '#5a7356')
    gth = [0.05, 0.11, 0.20, 0.32, 0.46, 0.63, 0.82]
    styles.update({
        'fur': MatStyle(ramp('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#574b3f', '#716250', '#8b7b66',
                             '#a2937c'), [0.04, 0.10, 0.18, 0.29, 0.43, 0.60, 0.80], dither=0.06, rim='#7d9a92'),
        'hat_top': MatStyle(ramp('#0a0909', '#161312', '#221d1a', '#312a25', '#423830', '#55483c'),
                            [0.06, 0.14, 0.27, 0.45, 0.66], rim='#5f7a76'),
        'coat': MatStyle(green, gth, dither=0.05, rim=rim),
        'coat_lapel': MatStyle(green, gth, rim=rim),
        'shirt': MatStyle(ramp('#0b0d10', '#1a1d22', '#2b2f35', '#40444a', '#575b60', '#6f7276'),
                          [0.05, 0.12, 0.24, 0.40, 0.60], dither=0.04, rim=rim),
        'strap': MatStyle(ramp('#0c0807', '#1d120d', '#311e14', '#4a2d1c', '#643e26', '#7e5232'),
                          [0.05, 0.12, 0.24, 0.40, 0.60], rim='#6b7f7a'),
        'hair': MatStyle(ramp('#0b0a0b', '#1b1614', '#2d241e', '#45372b', '#5e4b39', '#786049'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#6b8a84'),
        'knit': MatStyle(ramp('#0a0b0d', '#16181c', '#24272c', '#353940', '#4a4e55', '#61656b', '#7a7d80'),
                         [0.05, 0.12, 0.22, 0.35, 0.52, 0.72], dither=0.03, rim='#6f8c88'),
        'tie_string': MatStyle(ramp('#0c0a09', '#2a221c', '#4a3c30', '#6a5844'), [0.1, 0.3, 0.6], rim='#7d9a92'),
    })
    return dict(
        id='alexei', city='karsk',
        look=dict(key=(0.58, -0.40, 0.71), rim=(-0.80, -0.32, -0.50), ambient=0.07, bg='karsk',
                  glow=(0.82, 0.20)),
        head=dict(jaw_angle=(11.6, 15.6, -4.0), brow_r=(12.4, 2.8, 3.5), nose_tip=(0.0, 9.0, 19.4),
                  tip_r=2.6, ala_x=2.7, cheek_c=(10.9, 3.2, 9.8), chin_h=(5.0, 3.3, 3.4)),
        zoom=1.16,
        head_pos=(55.0, 55.0, 0.0), yaw=29.0, pitch=3.0, roll=0.0,
        torso_pos=(55.0, 91.0, -0.5), torso_yaw=12.0, torso=dict(width=1.05, depth=1.05, slope=1.0),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -2), 'determined': (1, -1, 1), 'surprised': (2, -3, 1)},
        head_items=[lambda M, hp: ushanka(M, hp, flaps='down'),
                    lambda M, hp: hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                     collar_h=6.0, collar_r=(13.2, 14.4)),
            lambda M, t: rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8)),
            lambda M, t: band_on(M, t, 3.5, (-8.0, 18.0), 46.0, 2.8, 'strap', y_range=(2.0, 60.0)),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'fur': 2, 'hat_top': 2, 'tie_string': 2,
                'coat': 4, 'coat_lapel': 8, 'shirt': 5, 'strap': 7, 'body': 4, 'knit': 6},
        tone_passes=[pass_fur('fur'), pass_stitches('coat', 5.0), pass_strands('hair'),
                     pass_knit('knit', ribs=30)],
        eye=dict(iris='#61705f', iris_d='#3a4439', sclera='#c4bfb0', sclera_d='#6f7072', lash='#120c0e',
                 pupil='#0a0a0c', catch='#efe8d6'),
        brow=dict(col='#2e241e', col_l='#4a3a2e'),
        mouth=dict(line='#3a1a1c', corner='#552a28', inner='#1a0a0b', teeth='#b8ab98', tongue='#6e2f30'),
        features=dict(
            extra=[ear_detail, stubble(), eye_bags()],
            brows={'neutral': dict(arch=0.5), 'concerned': dict(lift_inner=2.0, lift_outer=-0.3, arch=0.3),
                   'determined': dict(lift_inner=-1.8, arch=0.0, dy=0.6),
                   'surprised': dict(dy=-1.8, arch=1.2, lift_inner=0.4)},
            mouth={'neutral': dict(corner_drop=0.4), 'concerned': dict(corner_drop=1.0),
                   'determined': dict(corner_drop=0.6), 'surprised': dict(parted=2)},
        ),
        priority={'strap': 1},
    )


CAST['alexei'] = alexei


# ======================================================================================= headscarves, hair
def headscarf(M, hp, mat='kerchief', tie='nape', front_y=-12.6, seed=41, slope=1.15, z_off=0.5, thick=1.7,
              hair=True, hair_mat='hair', fold_amp=0.5):
    """Cloth headscarf.  tie='nape': tied behind the head (knot + tails at the nape);
    tie='chin': wrapped round the face and knotted under the chin (covers forehead, ears, cheeks)."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    cloth = S.Union([
        E(sc, sr + thick, m),
        E((0, -1.0, -6.5), (sr[0] + thick + 0.6, 14.0, sr[2] - 1.0), m),     # hood part round the back / ears
    ], k=3.0)
    if tie == 'nape':
        # loose fabric falls straight from the crown to the knot: extra volume at the back of the head
        cloth = S.Union([cloth, E((0, 0.5, -12.0), (sr[0] + 0.4, 12.5, 11.5), m)], k=4.0)
    if tie == 'chin':
        cloth = S.Union([cloth, E((0, 12.0, -1.0), (sr[0] + 0.6, 16.0, sr[2] - 2.5), m)], k=3.0)

        def region(P):
            x, y, z = P[:, 0], P[:, 1], P[:, 2]
            # face opening: an ellipse on the face front (brow line to the chin)
            fo = ((x / 10.2) ** 2 + ((y - 8.0) / 13.0) ** 2) - 1.0
            return np.maximum(np.minimum(-fo * 6.0, z - 2.0), y - 30.0)
    else:
        def region(P):
            x, y, z = P[:, 0], P[:, 1], P[:, 2]
            return np.maximum(np.minimum(y - front_y, z - z_off + slope * y), y - 13.0)

    node = S.Inter(cloth, S.Fn(region, m))
    hem = S.Inter(S.Offset(cloth, 0.9, m), S.Fn(lambda P: np.abs(region(P) + 0.9) - 1.0, m))
    parts = [node, hem]
    if tie == 'nape':
        for sx in (1, -1):
            parts.append(E((sx * 2.8, 10.5, -sr[2] - 0.8), (3.2, 2.6, 2.6), m))
            parts.append(S.RoundCone((sx * 1.8, 12.0, -sr[2] - 1.0), (sx * 5.5, 23.0, -sr[2] + 0.6), 2.4, 1.4, m))
        # the scarf's corner hanging down the back of the neck below the knot
        parts.append(S.RoundCone((0.0, 9.0, -sr[2] + 0.6), (0.0, 20.0, -sr[2] + 3.2), 5.0, 1.2, m))
    else:
        parts.append(E((0.0, 27.5, 9.0), (3.2, 2.8, 2.8), m))                  # knot under the chin
        for sx in (1, -1):
            parts.append(S.RoundCone((sx * 1.2, 28.5, 9.5), (sx * 4.8, 34.0, 11.0), 2.2, 1.6, m))
    scarf = S.Union(parts, k=1.2)

    def folds(P):
        if tie == 'nape':
            a = np.arctan2(P[:, 1] - 11.0, P[:, 2] + sr[2])
        else:
            a = np.arctan2(P[:, 0], P[:, 1] - 28.0)
        return np.sin(a * 7.0 + 0.9 * S.vnoise3(P, 4.0, seed))

    scarf = S.Displace(scarf, folds, amp=fold_amp, lipschitz=1.3)
    out = dict(node=scarf, clip=S.Union([S.Offset(cloth, -(0.7 + fold_amp)), S.Fn(lambda P: -region(P), m)]))
    if hair and tie == 'nape':
        mh = M(hair_mat)
        hs = S.Offset(E(sc, sr, mh), 1.7, mh)
        out['soft'] = S.Inter(hs, S.Fn(lambda P: np.maximum(np.abs(region(P) - 1.1) - 1.4, P[:, 1] - 3.0), mh))
    return out


def hair_fringe(M, hp, mat='hair', top=-7.5, front_z=3.5, nape=10.0, thick=1.3):
    """Bald crown with a fringe of hair round the back and sides (ear height)."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    shell = S.Offset(E(sc, sr, m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.maximum(top - y, z - front_z - 0.25 * (y - top))
        r = np.maximum(r, y - nape)
        ear = np.maximum(np.maximum(y + 1.5, -y + 9.0), np.maximum(z + 2.0, -9.5 - z))
        return np.maximum(r, -ear)

    return S.Inter(shell, S.Fn(region, m))


def hair_bun(M, hp, mat='hair', bun=(-2.0, -19.0, -27.0), bun_r=6.6, hairline=-14.5, thick=1.5, seed=51):
    """Hair combed back over the skull into a bun (librarian)."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    shell = S.Offset(E(sc, sr, m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = np.minimum(y - hairline - 0.12 * np.abs(x), z - 6.0)
        side = np.minimum(y - 2.0, z + 1.5)
        ear = np.maximum(np.maximum(y + 3.0, -y + 9.5), np.maximum(z + 1.5, -9.0 - z))
        return np.maximum(np.maximum(np.maximum(front, side), y - 10.0), -ear)

    hairn = S.Inter(shell, S.Fn(region, m))
    b = S.Displace(E(bun, (bun_r, bun_r * 0.92, bun_r * 0.8), m), lambda P: S.vnoise3(P, 1.8, seed), amp=0.4)
    return S.Union([hairn, b], k=1.6)


def moustache(c=(0.0, 12.7, 17.3), r=(4.4, 1.45, 1.7), droop=1.0, mat='moustache'):
    return [('ellipsoid', (c, r, mat, 0.6)),
            ('ellipsoid', ((-r[0] + 0.4, c[1] + droop, c[2] - 1.6), (1.6, 1.5, 1.4), mat, 0.6)),
            ('ellipsoid', ((r[0] - 0.4, c[1] + droop, c[2] - 1.6), (1.6, 1.5, 1.4), mat, 0.6))]


# ======================================================================================= line marks / glasses
def head_line(G, cv, pts, delta=-1, steps=24, skip=None, allow_mats=('skin', 'lip', 'ear', 'neck')):
    """Draw a relative-tone polyline given in HEAD-local coordinates (wrinkles, folds, creases)."""
    from chargen_portrait2 import zoom_pt   # late import (circular)
    spec_like = {'zoom': G.get('zoom', 1.0)}
    hf = G['hf']
    d = G['d']
    M = G['M']
    ok = np.isin(d.mat, [M.names.index(n) for n in allow_mats if n in M.names])
    seen = set()
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        for k in range(steps + 1):
            u = k / steps
            p = pts[i] * (1 - u) + pts[i + 1] * u
            v = zoom_pt(spec_like, hf.to_view(p))
            x, y = int(np.floor(v[0])), int(np.floor(v[1]))
            if (x, y) in seen:
                continue
            seen.add((x, y))
            if skip is not None and skip(len(seen)):
                continue
            if 0 <= y < ok.shape[0] and 0 <= x < ok.shape[1] and ok[y, x]:
                # only draw where the surface is really there (depth check)
                if abs(d.z[y, x] - v[2]) < 3.5:
                    cv.rel(x, y, delta, allow=ok)


def wrinkles(forehead=3, crow=True, naso=True, under=True, strength=-1):
    def fn(spec, G, cv, expr, mouth_state, blink, v):
        fz = G['hp']['fore_c'][2] + G['hp']['fore_h'][2] - 0.3
        extra = {'surprised': 1, 'concerned': 1}.get(expr, 0)
        for i in range(forehead + extra):
            yy = -8.8 - i * 2.6 - (0.6 if expr == 'surprised' else 0)
            w = 6.0 - i * 0.8
            pts = [(-w, yy + 0.5, fz - 1.0), (-1.5, yy, fz - 0.2), (w - 1.0, yy + 0.3, fz - 0.8)]
            head_line(G, cv, pts, strength, skip=lambda n: n == 4 or n == 9)
        if expr == 'concerned':
            head_line(G, cv, [(-1.2, -5.2, 16.4), (-0.8, -8.0, 15.8)], strength)
        if expr == 'determined':
            head_line(G, cv, [(-1.0, -4.6, 16.4), (-1.3, -6.6, 16.0)], strength)
            head_line(G, cv, [(1.0, -4.6, 16.4), (1.3, -6.6, 16.0)], strength)
        if crow:
            ex = G['hp']['eye_x']
            for sx in (-1, 1):
                b = (sx * (ex + 4.2), 0.2, 12.6)
                head_line(G, cv, [b, (sx * (ex + 5.6), -1.0, 11.4)], strength)
                head_line(G, cv, [(b[0], 1.2, 12.6), (sx * (ex + 5.4), 2.4, 11.4)], strength)
        if naso:
            hp = G['hp']
            for sx in (-1, 1):
                a = (sx * (hp['ala_x'] + 1.4), hp['ala_y'] + 0.2, hp['ala_z'] - 0.4)
                b = (sx * (hp['lip_up_r'][0] + 1.6), hp['mouth_y'] + 1.4, hp['lip_up'][2] - 2.2)
                c = (sx * (hp['lip_up_r'][0] + 1.8), hp['mouth_y'] + 4.0, hp['lip_up'][2] - 3.0)
                head_line(G, cv, [a, b, c], strength)
        if under:
            ex = G['hp']['eye_x']
            for sx in (-1, 1):
                head_line(G, cv, [(sx * (ex - 2.6), 3.4, 15.0), (sx * ex, 4.0, 15.0), (sx * (ex + 2.4), 3.6, 14.2)],
                          strength)
    return fn


def _rgb(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)


def glasses(kind='round', rim='#2b2622', rim_hi='#b9a27b', glare='#9fb0b4', lens_r=(4.3, 3.4), low=0.0,
            chain=None):
    """Wire spectacles drawn as pixel ellipses in front of the eyes (rgb pass), with bridge, arm and a cold
    glare; kind='half' = half-moon reading glasses sitting low on the nose (optional chain)."""
    def fn(spec, G, rgb, v, expr, row):
        lm = G['lmv']
        out = rgb
        rc, rh, gl = _rgb(rim), _rgb(rim_hi), _rgb(glare)
        h, w = rgb.shape[:2]
        lit = v > 0.3
        centers = []
        for key, rx_, ry_ in (('eye_r', lens_r[0], lens_r[0] + 0.2), ('eye_l', lens_r[1], lens_r[0] + 0.2)):
            cx, cy = lm[key][0] + 0.5, lm[key][1] + 0.4 + low
            centers.append((cx, cy, rx_, ry_))
            seen = set()
            for a in np.linspace(0, 2 * np.pi, 160, endpoint=False):
                x = int(np.floor(cx + rx_ * np.cos(a)))
                y = int(np.floor(cy + ry_ * np.sin(a)))
                if kind == 'half' and y < cy - 0.5:
                    continue
                if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
                    continue
                seen.add((x, y))
                hi = (np.cos(a) > 0.25 and np.sin(a) < -0.2) or (kind == 'half' and np.cos(a) > 0.6)
                out[y, x] = rh if hi and lit[y, x] else rc
            if kind == 'half':
                y = int(np.floor(cy - 0.5))
                for x in range(int(np.floor(cx - rx_)), int(np.floor(cx + rx_)) + 1):
                    if 0 <= x < w and 0 <= y < h:
                        out[y, x] = rc
            if key == 'eye_l':
                for k in range(3):
                    x, y = int(cx + 1 + k * 0.6), int(cy - 2 + k)
                    if 0 <= x < w and 0 <= y < h:
                        out[y, x] = ((out[y, x].astype(int) + gl.astype(int) * 2) // 3).astype(np.uint8)
        (x0, y0, r0, _), (x1, y1, r1, _) = centers
        by = int(np.floor(min(y0, y1) - (1.0 if kind == 'round' else -0.5)))
        for x in range(int(np.floor(x0 + r0)) + 1, int(np.floor(x1 - r1))):
            if 0 <= x < w and 0 <= by < h:
                out[by, x] = rc
        ear = lm['ear_r']
        ay = int(np.floor(y0 - 0.5))
        for x in range(int(np.floor(ear[0])) + 1, int(np.floor(x0 - r0))):
            t = (x - ear[0]) / max(1.0, (x0 - r0) - ear[0])
            y = int(np.floor(ear[1] - 1.5 + (ay - ear[1] + 1.5) * t))
            if 0 <= x < w and 0 <= y < h:
                out[y, x] = rc
        if chain:
            cc = _rgb(chain)
            for k in range(26):
                t = k / 25
                x = int(np.floor(x0 - r0 - 4.0 * np.sin(t * np.pi) - 2.0 * t))
                y = int(np.floor(y0 + 1 + t * 26))
                if 0 <= x < w and 0 <= y < h and k % 2 == 0:
                    out[y, x] = cc
        return out
    return fn


# ======================================================================================= eye variants
def _flick_table(base):
    """Female eyes: one lash flick at the outer corner of each eye (near: top-left, far: top-right)."""
    out = {}
    for (side, ex), (rows, anc) in base.items():
        r = [ln.strip() for ln in rows.strip('\n').split('\n') if ln.strip()]
        w = len(r[0])
        r = [ln.ljust(w, '.') for ln in r]
        lash_row = next((i for i, ln in enumerate(r) if 'K' in ln), 1)
        if side == 'near':
            r = [('.' + ln) for ln in r]
            r[max(0, lash_row - 1)] = 'K' + r[max(0, lash_row - 1)][1:]
            anc = (anc[0] + 1, anc[1])
        else:
            r = [(ln + '.') for ln in r]
            j = max(0, lash_row - 1)
            r[j] = r[j][:-1] + 'K'
        out[(side, ex)] = ('\n'.join(r), anc)
    return out


def _female_eyes():
    import chargen_portrait2_face as FC
    return _flick_table(FC.EYES)


def tie_knot_collar(M, mat='shirt', y=1.2, z=8.6):
    m = M(mat)
    return S.Union([S.RoundBox((sx * 2.8, y, z), (2.4, 1.3, 0.7), 0.6, m, R=S.rot(0, 0, sx * 32.0))
                    for sx in (1, -1)], k=0.6)


def layered_front(M, torso_node, outer='coat', mid='cardigan', inner='shirt', v_outer=(0.62, 0.0),
                  v_mid=(0.30, 6.0), outer_t=2.8, mid_t=1.8, lapel=True, collar_h=5.0, collar_r=(11.6, 13.4),
                  buttons=None):
    """Open outer coat (lapels) over a V-neck middle layer (cardigan / waistcoat) over a shirt."""
    mo, mm, mi = M(outer), M(mid), M(inner)
    o = S.Offset(torso_node, outer_t, mo)
    vo, to = v_outer
    o = S.Sub(o, S.Fn(lambda P: np.maximum(3.0 - P[:, 2], np.abs(P[:, 0]) - (P[:, 1] - to) * vo), mo), k=0.8)
    md = S.Offset(torso_node, mid_t, mm)
    vm, tm = v_mid
    md = S.Sub(md, S.Fn(lambda P: np.maximum(3.0 - P[:, 2], np.abs(P[:, 0]) - (P[:, 1] - tm) * vm), mm), k=0.6)
    parts = [o, md, S.Offset(torso_node, 0.9, mi)]
    if lapel:
        parts.append(lapels(M, torso_node, outer_t, vo, to, width=5.0, mat=outer + '_lapel'))
    if collar_h:
        col = S.Shell(S.RoundCone((0, -collar_h, -2.5), (0, 3.0, -1.0), collar_r[0], collar_r[1], mo), 1.1, mo)
        col = S.Inter(col, S.Fn(lambda P: np.maximum(P[:, 1] - 3.0, -collar_h - P[:, 1]), mo))
        col = S.Sub(col, S.Fn(lambda P: np.maximum(5.0 - P[:, 2], np.abs(P[:, 0]) - 7.0), mo), k=1.0)
        parts.append(col)
    if buttons:
        mb = M('button')
        for (bx, by) in buttons:
            parts.append(E((bx, by, 0.0), (1.1, 1.1, 1.1), mb))
    return S.Union(parts)


def surface_buttons(M, torso_node, lift, pts, r=1.0, mat='button'):
    """Small round buttons lying on a garment surface (torso-local x/y points)."""
    m = M(mat)
    blobs = []
    for (bx, by) in pts:
        blobs.append(S.Inter(S.Offset(torso_node, lift + 0.6, m),
                             S.Fn(lambda P, bx=bx, by=by: np.sqrt((P[:, 0] - bx) ** 2 + (P[:, 1] - by) ** 2) - r, m)))
    return S.Union(blobs)


def pencils(at=(11.5, 15.0, 0.0), cols=('#c9a23a', '#a8382e'), lift=4.2):
    """Two pencils in a breast pocket (rgb pass, projected from the torso frame onto the surface)."""
    def fn(spec, G, rgb, v, expr, row):
        from chargen_portrait2 import zoom_pt
        tf = G['tf']
        d = G['d']
        spec_like = {'zoom': G.get('zoom', 1.0)}
        for i, c in enumerate(cols):
            base = np.array([at[0] + i * 1.6, at[1], 0.0])
            # find the surface depth by sampling the gbuffer around the projected point
            p = zoom_pt(spec_like, tf.to_view(base + np.array([0, 0, 14.0])))
            x, y = int(np.floor(p[0])), int(np.floor(p[1]))
            col = _rgb(c)
            dark = (col.astype(int) * 0.55).astype(np.uint8)
            for k in range(4):
                yy = y - k
                if 0 <= yy < rgb.shape[0] and 0 <= x < rgb.shape[1] and d.hit[yy, x]:
                    rgb[yy, x] = col if k < 3 else _rgb('#d8c8a8')
            if 0 <= y + 1 < rgb.shape[0]:
                rgb[y + 1, x] = dark
        return rgb
    return fn


# ======================================================================================= Irina, Emil
def irina():
    rim = '#5f8a84'
    sk = ramp('#080d14', '#1b1b25', '#382631', '#5f3739', '#8d5445', '#b77553', '#d89b6d', '#f0c695')
    lip = ramp('#080d14', '#1b1b25', '#3c2430', '#66323a', '#934448', '#b85d58', '#d4806c', '#e8a68a')
    styles = skin_styles(sk, rim, lip)
    slate = ramp('#07090c', '#0e1319', '#161e27', '#212c38', '#2f3d4b', '#40515f', '#566a77')
    sth = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
    styles.update({
        'kerchief': MatStyle(ramp('#100707', '#260c0c', '#3e1512', '#5a2118', '#7a2f1f', '#9a4128', '#b45734',
                                  '#c87346'), [0.04, 0.10, 0.19, 0.31, 0.46, 0.65, 0.86], dither=0.03,
                             rim='#7d9a92'),
        'hair': MatStyle(ramp('#0e0809', '#22110f', '#391c16', '#55291d', '#723a25', '#8e4d2f'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#7d9a92'),
        'coat': MatStyle(slate, sth, dither=0.05, rim=rim),
        'coat_lapel': MatStyle(slate, sth, rim=rim),
        'shirt': MatStyle(slate, sth, rim=rim),
        'knit': MatStyle(ramp('#0d0a06', '#1f170d', '#352713', '#4e391b', '#6a4f26', '#866632', '#a07e44'),
                         [0.05, 0.12, 0.22, 0.35, 0.52, 0.72], dither=0.03, rim='#7d9a92'),
    })
    return dict(
        id='irina', city='karsk',
        look=dict(key=(0.58, -0.42, 0.70), rim=(-0.80, -0.32, -0.50), ambient=0.07, bg='karsk',
                  glow=(0.80, 0.22)),
        head=dict(skull_r=(15.6, 16.4, 19.8), fore_h=(11.6, 8.6, 11.6), mid_h=(11.2, 6.6, 11.2),
                  cheek_c=(10.0, 2.6, 10.0), cheek_r=(4.4, 2.9, 3.8), malar_r=(3.8, 3.4, 3.2),
                  jaw_angle=(10.2, 14.6, -4.0), jaw_r=(2.4, 2.8, 2.8), chin_pt=(3.6, 22.2, 10.0),
                  chin_c=(0.0, 21.3, 11.8), chin_h=(4.2, 3.0, 3.2), low_r=(11.0, 10.6, 12.4),
                  nose_tip=(0.0, 8.5, 19.0), tip_r=2.2, nose_r=(1.3, 1.8), ala_x=2.2, ala_r=(1.5, 1.4, 1.8),
                  mouth_y=14.2, lip_up=(0.0, 13.5, 16.3), lip_up_r=(4.1, 1.35, 1.5),
                  lip_lo=(0.0, 15.6, 15.9), lip_lo_r=(3.6, 1.65, 1.6), brow_r=(11.6, 2.2, 3.0),
                  adams_apple=False, scm=False, neck_r=(6.8, 8.2), ear_r=(1.5, 5.6, 3.3)),
        zoom=1.18,
        head_pos=(55.0, 56.0, 0.0), yaw=31.0, pitch=2.0, roll=-2.0,
        torso_pos=(55.5, 91.5, -0.5), torso_yaw=13.0, torso=dict(width=0.92, depth=0.98, slope=1.3),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -3), 'determined': (1, -1, 1), 'surprised': (2, -3, 2)},
        head_items=[lambda M, hp: headscarf(M, hp, mat='kerchief', tie='nape', front_y=-12.2, fold_amp=0.85)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.20, v_top=6.0, lapel=False, quilt=(4.6, 0.5),
                                     collar_h=5.5, collar_r=(11.8, 13.2)),
            lambda M, t: rollneck(M, 'knit', y_top=-10.5, y_bot=3.0, r=(8.8, 10.4)),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'kerchief': 2, 'coat': 4, 'coat_lapel': 8,
                'shirt': 5, 'knit': 6, 'body': 4},
        tone_passes=[pass_stitches('coat', 4.6), pass_strands('hair'), pass_knit('knit', ribs=28),
                     pass_folds('kerchief', knot=(0.0, 10.5, -21.5), n=8, seed=82)],
        rgb_passes=[pass_scarf_border(-12.2, lit='#c39a4a', shade='#5e4320')],
        eye=dict(iris='#6a4a34', iris_d='#3e2a1e', sclera='#c8bfb0', sclera_d='#6f6e72', lash='#120a0c',
                 pupil='#0a0808', catch='#f2e9d6'),
        brow=dict(col='#3a1f16', col_l='#5a3322'),
        mouth=dict(line='#46191d', corner='#5e2a2a', inner='#1a0a0b', teeth='#bcae9c', tongue='#733033'),
        features=dict(
            eyes=_female_eyes(),
            extra=[ear_detail],
            brows={'neutral': dict(arch=0.9), 'concerned': dict(lift_inner=2.2, lift_outer=-0.4, arch=0.5),
                   'determined': dict(lift_inner=-1.6, arch=0.2, dy=0.5),
                   'surprised': dict(dy=-1.8, arch=1.4, lift_inner=0.4)},
            brow_thick=((2, 1, 1), (1, 1, 1)),
            mouth={'neutral': dict(corner_drop=0.2), 'concerned': dict(corner_drop=0.9),
                   'determined': dict(corner_drop=0.5), 'surprised': dict(parted=2)},
        ),
        priority={},
    )


def emil():
    rim = '#6e8fa6'
    sk = ramp('#0b0d16', '#1f1b28', '#3b2b38', '#614047', '#8d5f58', '#b8846f', '#d8aa8f', '#efd0b4')
    lip = ramp('#0b0d16', '#1f1b28', '#3d2934', '#643a42', '#8f5552', '#b4705f', '#d3937c', '#e9b8a0')
    styles = skin_styles(sk, rim, lip)
    grey_hair = ramp('#0c0d10', '#25262b', '#45464b', '#6b6b6e', '#8f8e8c', '#b2aea7', '#cdc8bd')
    ghth = [0.05, 0.12, 0.24, 0.38, 0.56, 0.78]
    coat = ramp('#08090b', '#121417', '#1d2024', '#2a2e33', '#3a3f45', '#4e545a', '#666c70', '#80858a')
    cth = [0.04, 0.10, 0.19, 0.31, 0.46, 0.64, 0.84]
    styles.update({
        'hair': MatStyle(grey_hair, [0.03, 0.07, 0.14, 0.24, 0.40, 0.62], rim='#a8b8c4', wrap=0.45, lift=0.3),
        'moustache': MatStyle(grey_hair, [0.03, 0.07, 0.14, 0.24, 0.40, 0.62], rim='#a8b8c4', wrap=0.45,
                              lift=0.3),
        'coat': MatStyle(coat, cth, dither=0.04, rim=rim),
        'coat_lapel': MatStyle(coat, cth, rim=rim),
        'cardigan': MatStyle(ramp('#0d0807', '#1d120e', '#2f1f17', '#452e20', '#5d402b', '#765437', '#8e6947'),
                             [0.05, 0.12, 0.22, 0.36, 0.54, 0.76], dither=0.03, rim=rim),
        'shirt': MatStyle(ramp('#121318', '#2a2c33', '#4a4c53', '#73747a', '#9c9b9c', '#c1bdb5', '#dcd6ca'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#9eb2c2'),
        'tie': MatStyle(ramp('#0c120e', '#16211a', '#223228', '#304537', '#425b49'),
                        [0.06, 0.15, 0.30, 0.52], rim=rim),
        'button': MatStyle(ramp('#0e0a08', '#2a1f18', '#4f3c2c', '#7a6046'), [0.08, 0.25, 0.5], rim=rim),
    })
    head = dict(nose_tip=(0.0, 9.9, 20.3), tip_r=2.8, ala_x=2.8, nose_r=(1.6, 2.2), ala_r=(1.8, 1.6, 2.0),
                ear_r=(1.9, 7.0, 4.0), ear_c=(15.8, 3.6, -5.6),
                lip_up_r=(4.2, 1.0, 1.3), lip_lo_r=(3.6, 1.2, 1.4), brow_r=(12.4, 2.7, 3.4),
                skull_r=(15.9, 16.6, 20.4), skull_c=(0.0, -9.2, -5.0),
                jaw_extra=[('ellipsoid', ((8.4, 18.2, 8.0), (4.2, 3.8, 3.8), 'skin', 2.2)),
                           ('ellipsoid', ((-8.4, 18.2, 8.0), (4.2, 3.8, 3.8), 'skin', 2.2)),
                           ('ellipsoid', ((0.0, 26.0, 6.4), (6.4, 3.0, 5.0), 'skin', 2.6))],
                extra=moustache(c=(0.0, 12.9, 17.4), r=(4.6, 1.5, 1.8), droop=1.2))
    return dict(
        id='emil', city='berlin',
        look=dict(key=(0.62, -0.32, 0.72), rim=(-0.80, -0.35, -0.50), ambient=0.08, bg='archive',
                  glow=(0.80, 0.20)),
        head=head,
        zoom=1.13,
        head_pos=(55.0, 60.0, 0.0), yaw=28.0, pitch=9.0, roll=-1.5,
        torso_pos=(54.0, 95.0, -2.0), torso_yaw=13.0, torso=dict(width=0.98, depth=1.05, slope=1.8),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 3, -2), 'determined': (1, -2, 1), 'surprised': (2, -5, 1)},
        head_items=[lambda M, hp: hair_fringe(M, hp)],
        torso_items=[
            lambda M, t: layered_front(M, t, v_outer=(0.66, -1.0), v_mid=(0.30, 7.0)),
            lambda M, t: tie_knot_collar(M),
            lambda M, t: tie(M, mat='tie', top=(0.2, 3.4, 9.6), bot=(0.6, 30.0, 13.4)),
            lambda M, t: surface_buttons(M, t, 1.8, [(0.0, 19.5), (0.0, 26.5)], r=1.0),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'moustache': 9, 'neck': 1, 'coat': 4, 'coat_lapel': 8,
                'cardigan': 5, 'shirt': 6, 'tie': 6, 'button': 5, 'body': 4},
        tone_passes=[pass_strands('hair'), pass_strands('moustache', seed=12), pass_grain('coat', 0.05, seed=5),
                     pass_knit('cardigan', ribs=40)],
        rgb_passes=[glasses('round'), pencils(at=(11.0, 14.0, 0.0))],
        eye=dict(iris='#6f8291', iris_d='#41505c', sclera='#c6beb4', sclera_d='#75707a', lash='#1a1012',
                 pupil='#0b0a0e', catch='#f2ead8'),
        brow=dict(col='#6b6b6e', col_l='#a8a49c'),
        mouth=dict(line='#3a1c20', corner='#5a2c2c', inner='#1c0c0e', teeth='#b2a593', tongue='#6c3034'),
        features=dict(
            extra=[ear_detail, wrinkles(forehead=2), eye_bags()],
            brows={'neutral': dict(arch=0.8), 'concerned': dict(lift_inner=2.3, lift_outer=-0.5, arch=0.4),
                   'determined': dict(lift_inner=-1.5, arch=0.1, dy=0.5),
                   'surprised': dict(dy=-2.0, arch=1.4, lift_inner=0.5)},
            mouth={'neutral': dict(corner_drop=0.6), 'concerned': dict(corner_drop=1.2),
                   'determined': dict(corner_drop=0.8), 'surprised': dict(parted=2)},
        ),
        priority={'button': 2, 'tie': 1},
    )


CAST['irina'] = irina
CAST['emil'] = emil


# ======================================================================================= more builders
def peaked_cap(M, hp, y0=-13.4, z0=-4.8, tilt=(5.0, 0.0), band_r=(17.2, 21.0), top_r=(19.4, 23.4), h=9.6,
               visor_tilt=30.0):
    """Doorman's peaked cap: cloth band, flared crown with a raised front, glossy visor, braided cord.
    Deliberately WITHOUT any badge or insignia."""
    mc, mb, mv, mk = M('cap'), M('cap_band'), M('visor'), M('cord')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = band_r
    band = S.EllipticCylinder((0, -2.5, 0), rx, rz, 2.5, mb, e=0.5)

    def flare(P):
        t = np.clip((-P[:, 1] - 4.5) / (h - 4.5), 0, 1)
        s_ = 1.0 / (1.0 + (top_r[0] / rx - 1.0) * t)
        off = np.zeros_like(P)
        off[:, 0] = P[:, 0] - P[:, 0] * s_
        off[:, 2] = P[:, 2] - P[:, 2] * s_
        # saddle: the front of the crown rises
        off[:, 1] = -1.6 * np.clip(P[:, 2] / rz, 0, 1) * t
        return off

    crown = S.Warp(S.EllipticCylinder((0, -(h + 4.0) / 2, 0), rx, rz, (h - 4.0) / 2 + 2.0, mc, e=1.8),
                   flare, lip=1.3)
    vf = S.Frame((0.0, -0.2, rz - 2.0), S.rot(0, visor_tilt, 0))
    visor = S.Inter(S.EllipticCylinder((0, 0, -2.0), 13.0, 9.5, 0.55, mv, e=0.45),
                    S.Fn(lambda P: -(P[:, 2] - 0.3), mv))
    visor = S.Xform(visor, frame=vf)
    cord = S.Inter(S.EllipticCylinder((0, -3.4, 0), rx + 0.45, rz + 0.45, 0.6, mk, e=0.3),
                   S.Fn(lambda P: 6.0 - P[:, 2], mk))
    hat = S.Union([band, crown, visor, cord])
    allowed = S.Union([S.Offset(S.EllipticCylinder((0, -6.0, 0), rx, rz, 7.0, mc, e=1.0), -0.6),
                       S.Fn(lambda P: -(P[:, 1] - 0.8), mc)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def apron_bib(M, torso_node, lift=3.4, half_w=8.5, top=7.0, mat='apron', straps=True):
    m = M(mat)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        bib = np.maximum(np.abs(x) - half_w - 0.08 * (y - top), np.maximum(top - y, 3.0 - z))
        if straps:
            for sx in (1, -1):
                st = np.maximum(np.abs(x - sx * (half_w - 1.0) - sx * 0.35 * (top - y)) - 1.2,
                                np.maximum(y - top - 1.0, 2.0 - z))
                bib = np.minimum(bib, st)
        return bib

    return S.Inter(S.Offset(torso_node, lift, m), S.Fn(region, m))


def shawl(M, mat='shawl', y=-2.0, r=14.6, tube=4.2, seed=61):
    """Knitted shawl round the shoulders, crossed in front."""
    m = M(mat)
    parts = []
    for i in range(14):
        a = np.radians(-150 + i * 23.0)
        parts.append(E((r * np.sin(a), y + 6.0 * (1 - np.cos(a)) * 0.3, -2.0 + (r - 2.0) * np.cos(a)),
                       (tube + 1.5, tube, tube + 0.6), m))
    parts.append(E((-2.0, y + 12.0, 12.5), (6.5, 8.0, 3.0), m, R=S.rot(0, 0, 18)))
    parts.append(E((3.0, y + 14.0, 12.0), (5.5, 8.0, 2.6), m, R=S.rot(0, 0, -20)))
    node = S.Union(parts, k=2.6)
    return S.Displace(node, lambda P: S.vnoise3(P, 2.4, seed), amp=0.5, lipschitz=1.3)


def pass_dots(mat="kerchief", period=5.6, seed=71, frame="hf", lit="#b9b4a6", shade="#5d6474", radius=0.19):
    """Polka dots printed on a scarf: a staggered lattice in surface coordinates (arc length round the
    head, height), drawn as absolute colours so every dot is a clean 1-2 px cluster."""
    def fn(spec, G, rgb, v, expr, row):
        M = G['M']
        if mat not in M.names:
            return rgb
        d = G['d']
        m = (d.mat == M.names.index(mat))
        if not m.any():
            return rgb
        L = _local(G, frame, m)
        u = np.arctan2(L[:, 0], L[:, 2] + 3.0) * 17.0
        w = L[:, 1]
        rowi = np.floor(w / period)
        fu = (u / period + 0.5 * (rowi % 2)) % 1.0
        fw = (w / period) % 1.0
        dot = ((fu - 0.5) ** 2 + (fw - 0.5) ** 2) < radius ** 2
        ys, xs = np.nonzero(m)
        lit_c, sh_c = _rgb(lit), _rgb(shade)
        for x, y, dd in zip(xs, ys, dot):
            if dd:
                rgb[y, x] = lit_c if v[y, x] > 0.30 else sh_c
        return rgb
    return fn


def gold_tooth(spec, G, cv, expr, mouth_state, blink, v):
    """The tea vendor's gold tooth, visible whenever the mouth is open."""
    if mouth_state == 'rest':
        return
    teeth = sorted([k for k, c in cv.abs.items() if c == 'T'])
    if teeth:
        x, y = teeth[min(len(teeth) - 1, len(teeth) // 2 + 1)]
        cv.abs[(x, y)] = 'G'


def blush(c=(9.0, 7.0, 11.0), r=(4.2, 3.4, 3.4)):
    return [('ellipsoid', (c, r, 'cheek', 1.4)), ('ellipsoid', ((-c[0], c[1], c[2]), r, 'cheek', 1.4))]


# ======================================================================================= NPC speakers
FEMALE = dict(skull_r=(15.6, 16.4, 19.8), fore_h=(11.6, 8.6, 11.6), mid_h=(11.2, 6.6, 11.2),
              cheek_c=(10.0, 2.6, 10.0), cheek_r=(4.4, 2.9, 3.8), malar_r=(3.8, 3.4, 3.2),
              jaw_angle=(10.2, 14.6, -4.0), jaw_r=(2.4, 2.8, 2.8), chin_pt=(3.6, 22.2, 10.0),
              chin_c=(0.0, 21.3, 11.8), chin_h=(4.2, 3.0, 3.2), low_r=(11.0, 10.6, 12.4),
              nose_tip=(0.0, 8.5, 19.0), tip_r=2.2, nose_r=(1.3, 1.8), ala_x=2.2, ala_r=(1.5, 1.4, 1.8),
              mouth_y=14.2, lip_up=(0.0, 13.5, 16.3), lip_up_r=(4.1, 1.35, 1.5),
              lip_lo=(0.0, 15.6, 15.9), lip_lo_r=(3.6, 1.65, 1.6), brow_r=(11.6, 2.2, 3.0),
              adams_apple=False, scm=False, neck_r=(6.8, 8.2), ear_r=(1.5, 5.6, 3.3))

BROWS_STD = {'neutral': dict(arch=0.6), 'concerned': dict(lift_inner=2.2, lift_outer=-0.4, arch=0.3),
             'determined': dict(lift_inner=-1.7, arch=0.0, dy=0.5), 'surprised': dict(dy=-1.8, arch=1.3,
                                                                                      lift_inner=0.4)}
MOUTH_STD = {'neutral': dict(corner_drop=0.3), 'concerned': dict(corner_drop=1.0),
             'determined': dict(corner_drop=0.6), 'surprised': dict(parted=2)}
POSES_STD = {'neutral': (0, 0, 0), 'concerned': (-2, 4, -2), 'determined': (1, -1, 1), 'surprised': (2, -3, 1)}


def vendor():
    rim = '#5f8a84'
    sk = ramp('#080d14', '#1b1b25', '#3a2630', '#633638', '#935244', '#bd7151', '#db976a', '#f1c393')
    lip = ramp('#080d14', '#1b1b25', '#3e2430', '#6a3038', '#984246', '#bd5a55', '#d77d69', '#eba487')
    cheek = ramp('#080d14', '#1b1b25', '#3e2430', '#683238', '#984a44', '#c0654f', '#da8765', '#eeae87')
    styles = skin_styles(sk, rim, lip)
    styles['cheek'] = MatStyle(cheek, SKIN_TH, rim=rim, outline=sk[0], wrap=0.18, lift=0.24, ao=0.75)
    teal = ramp('#070d0e', '#0e1a1c', '#142629', '#1d3335', '#284443', '#365853', '#4a6f66')
    tth = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
    styles.update({
        'kerchief': MatStyle(ramp('#121417', '#2b2e33', '#4f5258', '#7a7b7c', '#a3a19b', '#c6c1b5', '#e1dccd'),
                             [0.05, 0.12, 0.22, 0.36, 0.55, 0.78], dither=0.03, rim='#9ab4ae'),
        'hair': MatStyle(ramp('#0d0a0a', '#1e1614', '#33251f', '#4a372c', '#614a3a'),
                         [0.06, 0.14, 0.28, 0.48], rim='#7d9a92'),
        'coat': MatStyle(teal, tth, dither=0.05, rim=rim),
        'coat_lapel': MatStyle(teal, tth, rim=rim),
        'shirt': MatStyle(teal, tth, rim=rim),
        'apron': MatStyle(ramp('#14161a', '#30343a', '#565a5e', '#83857f', '#aeaca1', '#cfcabb', '#e6e0cf'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#a8c0b8'),
        'knit': MatStyle(ramp('#0d0b0b', '#1f1a19', '#332b29', '#4a3f3b', '#61544e', '#7a6c63'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], dither=0.03, rim=rim),
    })
    head = dict(FEMALE)
    head.update(mid_h=(12.0, 6.8, 11.6), cheek_c=(10.6, 3.6, 10.0), cheek_r=(5.0, 3.6, 4.2),
                malar_r=(4.8, 4.2, 4.0), jaw_angle=(11.2, 14.6, -3.8), low_r=(12.4, 10.4, 12.6),
                chin_h=(4.2, 2.8, 3.0), chin_c=(0.0, 21.0, 11.6), nose_tip=(0.0, 8.4, 18.8), tip_r=2.3,
                neck_r=(7.6, 9.0), extra=blush())
    return dict(
        id='vendor', city='karsk',
        look=dict(key=(0.60, -0.40, 0.70), rim=(-0.80, -0.32, -0.50), ambient=0.07, bg='karsk',
                  glow=(0.80, 0.24)),
        head=head, zoom=1.16,
        head_pos=(55.0, 56.0, 0.0), yaw=30.0, pitch=2.0, roll=2.0,
        torso_pos=(55.5, 92.0, -0.5), torso_yaw=12.0, torso=dict(width=1.02, depth=1.1, slope=1.4),
        poses=POSES_STD,
        head_items=[lambda M, hp: headscarf(M, hp, mat='kerchief', tie='nape', front_y=-11.6, fold_amp=0.8,
                                            seed=43)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.22, v_top=5.0, lapel=False, quilt=(4.4, 0.5),
                                     collar_h=4.5, collar_r=(11.6, 13.0)),
            lambda M, t: rollneck(M, 'knit', y_top=-9.5, y_bot=3.0, r=(9.4, 11.0)),
            lambda M, t: apron_bib(M, t, half_w=8.0, top=9.0),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck', 'cheek'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'cheek': 0, 'hair': 0, 'neck': 1, 'kerchief': 2, 'coat': 4,
                'coat_lapel': 8, 'shirt': 5, 'knit': 6, 'apron': 7, 'body': 4},
        tone_passes=[pass_stitches('coat', 4.4), pass_strands('hair'), pass_knit('knit', ribs=26),
                     pass_folds('kerchief', knot=(0.0, 10.5, -21.5), n=8, seed=84),
                     pass_grain('apron', 0.02, seed=10)],
        rgb_passes=[pass_scarf_border(-11.6, lit='#5f7fa4', shade='#2c3c52')],
        eye=dict(iris='#5b4a3a', iris_d='#352a20', sclera='#cbc2b2', sclera_d='#6f6e72', lash='#120a0c',
                 pupil='#0a0808', catch='#f2e9d6'),
        brow=dict(col='#2e211b', col_l='#4c382c'),
        mouth=dict(line='#46191d', corner='#5e2a2a', inner='#1a0a0b', teeth='#bcae9c', tongue='#733033'),
        abs_extra={'G': ('#e2b44c', '#9a7426')},
        features=dict(eyes=_female_eyes(), extra=[ear_detail, gold_tooth, wrinkles(forehead=1, naso=True,
                                                                                   crow=True, under=False)],
                      brows={**BROWS_STD, 'neutral': dict(arch=0.9)}, mouth=MOUTH_STD),
        priority={},
    )


def worker_a():
    rim = '#5f8a84'
    sk = ramp('#080d14', '#1a1a23', '#37252c', '#5e3433', '#8a4d3d', '#b06947', '#cf8d5e', '#e8b685')
    lip = ramp('#080d14', '#1a1a23', '#3a2530', '#5f3437', '#884843', '#ab6352', '#c9856a', '#e0a988')
    styles = skin_styles(sk, rim, lip)
    olive = ramp('#090a06', '#13150d', '#1e2114', '#2b2f1c', '#3a3f26', '#4c5232', '#606741')
    oth = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
    styles.update({
        'fur': MatStyle(ramp('#0a0909', '#171413', '#26201c', '#372f28', '#4c4136', '#645646', '#7c6c58'),
                        [0.05, 0.11, 0.20, 0.32, 0.48, 0.68], dither=0.06, rim='#7d9a92'),
        'hat_top': MatStyle(ramp('#090a07', '#14160f', '#212418', '#303422', '#41462e'),
                            [0.06, 0.16, 0.32, 0.55], rim='#6f8c88'),
        'tie_string': MatStyle(ramp('#0c0a09', '#2a221c', '#4a3c30', '#6a5844'), [0.1, 0.3, 0.6], rim='#7d9a92'),
        'coat': MatStyle(olive, oth, dither=0.05, rim=rim),
        'coat_lapel': MatStyle(olive, oth, rim=rim),
        'shirt': MatStyle(ramp('#0b0b0c', '#1a1a1c', '#2c2b2c', '#423f3e', '#5a5552'), [0.06, 0.15, 0.3, 0.52],
                          rim=rim),
        'knit': MatStyle(ramp('#0b0b0c', '#1a1a1c', '#2c2b2c', '#423f3e', '#5a5552', '#736c66'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], dither=0.03, rim=rim),
        'hair': MatStyle(ramp('#0b0a0b', '#191514', '#29221d', '#3d332a', '#544638'),
                         [0.06, 0.14, 0.28, 0.48], rim='#6b8a84'),
    })
    head = dict(jaw_angle=(12.0, 15.8, -4.0), brow_r=(12.6, 3.0, 3.6), nose_tip=(0.0, 9.4, 19.2), tip_r=2.8,
                ala_x=2.9, ala_r=(1.9, 1.6, 2.0), cheek_c=(11.0, 3.4, 9.6), chin_h=(5.2, 3.3, 3.4),
                lip_up_r=(4.4, 1.1, 1.4), lip_lo_r=(3.9, 1.35, 1.5), neck_r=(8.8, 10.0))
    return dict(
        id='worker_a', city='karsk',
        look=dict(key=(0.58, -0.40, 0.71), rim=(-0.80, -0.32, -0.50), ambient=0.07, bg='karsk',
                  glow=(0.82, 0.20)),
        head=head, zoom=1.14,
        head_pos=(55.0, 57.0, 0.0), yaw=28.0, pitch=4.0, roll=1.5,
        torso_pos=(55.0, 93.0, -0.5), torso_yaw=11.0, torso=dict(width=1.10, depth=1.12, slope=1.0),
        poses=POSES_STD,
        head_items=[lambda M, hp: ushanka(M, hp, flaps='up', seed=23, r=(18.2, 22.0)),
                    lambda M, hp: hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.5)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.30, v_top=4.0, lapel=False, quilt=(5.4, 0.6),
                                     collar_h=4.0, collar_r=(12.6, 14.2)),
            lambda M, t: rollneck(M, 'knit', y_top=-8.0, y_bot=3.0, r=(10.6, 12.0)),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'fur': 2, 'hat_top': 2, 'tie_string': 2,
                'coat': 4, 'coat_lapel': 8, 'shirt': 5, 'knit': 6, 'body': 4},
        tone_passes=[pass_fur('fur', seed=33), pass_stitches('coat', 5.4), pass_knit('knit', ribs=30),
                     pass_strands('hair')],
        eye=dict(iris='#4f5a4c', iris_d='#2f362d', sclera='#bfb8a8', sclera_d='#6c6c6e', lash='#120c0e',
                 pupil='#0a0a0c', catch='#efe8d6'),
        brow=dict(col='#2a211b', col_l='#45372b'),
        mouth=dict(line='#3a1a1c', corner='#552a28', inner='#1a0a0b', teeth='#ab9d86', tongue='#6e2f30'),
        features=dict(extra=[ear_detail, stubble(density=0.8), eye_bags(), wrinkles(forehead=2, under=False)],
                      brows={**BROWS_STD, 'neutral': dict(arch=0.2, lift_inner=-0.4)}, mouth=MOUTH_STD),
        priority={'tie_string': 2},
    )


def babushka():
    rim = '#5f8a84'
    sk = ramp('#0a0d15', '#1d1b26', '#3a2a35', '#604044', '#8c5e55', '#b5826b', '#d4a88a', '#ebcfb2')
    lip = ramp('#0a0d15', '#1d1b26', '#3b2833', '#5e383f', '#865050', '#a96a62', '#c68c7c', '#dfae9a')
    styles = skin_styles(sk, rim, lip)
    styles.update({
        'kerchief': MatStyle(ramp('#07080d', '#0f1219', '#171c27', '#212938', '#2d384b', '#3c4a60', '#4f5f78',
                                  '#6a7a92'), [0.04, 0.10, 0.19, 0.31, 0.46, 0.65, 0.86], dither=0.03,
                             rim='#7d9aa8'),
        'coat': MatStyle(ramp('#0b0908', '#161210', '#221c18', '#302722', '#40352d', '#52453a'),
                         [0.06, 0.14, 0.27, 0.45, 0.66], dither=0.05, rim=rim),
        'coat_lapel': MatStyle(ramp('#0b0908', '#161210', '#221c18', '#302722', '#40352d', '#52453a'),
                               [0.06, 0.14, 0.27, 0.45, 0.66], rim=rim),
        'shirt': MatStyle(ramp('#0b0908', '#161210', '#221c18', '#302722'), [0.08, 0.2, 0.45], rim=rim),
        'shawl': MatStyle(ramp('#0d0e10', '#1d1f22', '#2f3236', '#44474b', '#5b5e61', '#73767a', '#8c8e90'),
                          [0.05, 0.12, 0.22, 0.35, 0.52, 0.72], dither=0.04, rim='#8aa4a6'),
    })
    head = dict(FEMALE)
    head.update(nose_tip=(0.0, 9.3, 19.4), tip_r=2.6, ala_x=2.6, nose_r=(1.4, 2.0), mouth_y=14.8,
                lip_up=(0.0, 14.3, 15.6), lip_up_r=(3.9, 0.9, 1.2), lip_lo=(0.0, 16.0, 15.2),
                lip_lo_r=(3.4, 1.0, 1.2), muzzle_c=(0.0, 14.8, 10.6), chin_c=(0.0, 21.6, 11.4),
                jaw_extra=[('ellipsoid', ((8.0, 17.4, 7.6), (4.0, 3.6, 3.6), 'skin', 2.2)),
                           ('ellipsoid', ((-8.0, 17.4, 7.6), (4.0, 3.6, 3.6), 'skin', 2.2))],
                cheek_r=(4.0, 2.7, 3.6), malar_r=(3.4, 3.0, 2.8))
    return dict(
        id='babushka', city='karsk',
        look=dict(key=(0.58, -0.42, 0.70), rim=(-0.80, -0.32, -0.50), ambient=0.08, bg='karsk',
                  glow=(0.78, 0.24)),
        head=head, zoom=1.12,
        head_pos=(56.0, 58.0, 0.0), yaw=32.0, pitch=10.0, roll=-3.0,
        torso_pos=(55.0, 95.0, -3.0), torso_yaw=14.0, torso=dict(width=0.98, depth=1.15, slope=2.0),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 4, -3), 'determined': (1, -1, 1), 'surprised': (2, -4, 1)},
        head_items=[lambda M, hp: headscarf(M, hp, mat='kerchief', tie='chin', thick=1.9, fold_amp=0.7,
                                            seed=47, hair=False)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.25, v_top=4.0, lapel=False, collar=False),
            lambda M, t: shawl(M, y=-1.0, r=14.0),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'neck': 1, 'kerchief': 2, 'coat': 4, 'coat_lapel': 8, 'shirt': 5,
                'shawl': 6, 'body': 4},
        tone_passes=[pass_knit('shawl', ribs=36), pass_folds('kerchief', knot=(0.0, 28.0, 9.0), mode='chin', n=7,
                                                            seed=86, width=0.08)],
        rgb_passes=[pass_dots('kerchief')],
        eye=dict(iris='#5a6670', iris_d='#353e46', sclera='#bdb5aa', sclera_d='#6c6a70', lash='#140c10',
                 pupil='#0b0a0e', catch='#f0e8d6'),
        brow=dict(col='#6a6464', col_l='#9a948c'),
        mouth=dict(line='#3a1c20', corner='#5a2c2c', inner='#1c0c0e', teeth='#9c8e7c', tongue='#6c3034'),
        features=dict(extra=[wrinkles(forehead=3), eye_bags(), wrinkles(forehead=0, crow=False, naso=True,
                                                                         under=False)],
                      brows={**BROWS_STD, 'neutral': dict(arch=0.9, lift_inner=0.4)},
                      brow_thick=((1, 1, 1), (1, 1, 1)),
                      mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.8)}),
        priority={},
    )


def librarian():
    rim = '#6e8fa6'
    sk = ramp('#0b0d16', '#1e1b28', '#3a2a37', '#5f3e46', '#8b5c57', '#b6806d', '#d6a68b', '#eecdb0')
    lip = ramp('#0b0d16', '#1e1b28', '#3d2734', '#663541', '#924b52', '#b5645f', '#d08777', '#e6ad98')
    styles = skin_styles(sk, rim, lip)
    green = ramp('#060a08', '#0c1510', '#132018', '#1c2d22', '#273c2d', '#344d3a', '#46624a')
    gth = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
    styles.update({
        'hair': MatStyle(ramp('#0c0a0b', '#1c1719', '#2e2729', '#433a3a', '#5a504d', '#756b65', '#928a82'),
                         [0.05, 0.12, 0.22, 0.36, 0.55, 0.78], rim='#8ea2b4', wrap=0.3),
        'coat': MatStyle(green, gth, dither=0.04, rim=rim),
        'coat_lapel': MatStyle(green, gth, rim=rim),
        'cardigan': MatStyle(green, gth, rim=rim),
        'shirt': MatStyle(ramp('#16171b', '#33353a', '#5a5b5e', '#888680', '#b2ada2', '#d4cdbd', '#e8e1d0'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#9eb2c2'),
        'brooch': MatStyle(ramp('#1a1208', '#3d2c12', '#6e5222', '#a07c36', '#d1ad5c'), [0.06, 0.16, 0.32, 0.55],
                           rim='#d1ad5c', spec=0.5),
    })
    head = dict(FEMALE)
    head.update(nose_tip=(0.0, 8.8, 19.4), tip_r=2.2, nose_r=(1.3, 1.9), lip_up_r=(3.9, 1.15, 1.4),
                lip_lo_r=(3.4, 1.4, 1.5), jaw_angle=(10.4, 14.8, -4.0))
    return dict(
        id='librarian', city='berlin',
        look=dict(key=(0.56, -0.42, 0.71), rim=(-0.80, -0.35, -0.50), ambient=0.07, bg='archive',
                  glow=(0.80, 0.20)),
        head=head, zoom=1.16,
        head_pos=(55.0, 57.0, 0.0), yaw=30.0, pitch=4.0, roll=-1.0,
        torso_pos=(55.5, 92.0, -0.5), torso_yaw=13.0, torso=dict(width=0.92, depth=0.98, slope=1.4),
        poses=POSES_STD,
        head_items=[lambda M, hp: hair_bun(M, hp)],
        torso_items=[
            lambda M, t: layered_front(M, t, outer='coat', mid='shirt', inner='shirt', v_outer=(0.55, 2.0),
                                       v_mid=(0.0, 60.0), lapel=False, collar_h=0),
            lambda M, t: rollneck(M, 'shirt', y_top=-7.5, y_bot=3.0, r=(8.0, 9.6)),
            lambda M, t: surface_buttons(M, t, 1.4, [(0.0, 6.0)], r=1.6, mat='brooch'),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'coat': 4, 'coat_lapel': 8, 'shirt': 5,
                'cardigan': 5, 'brooch': 6, 'body': 4},
        tone_passes=[pass_strands('hair', seed=13), pass_knit('coat', ribs=44)],
        rgb_passes=[glasses('half', rim='#3a2c1e', rim_hi='#c9a96a', lens_r=(4.1, 3.2), low=2.2,
                            chain='#a08a5a')],
        eye=dict(iris='#5b5e4a', iris_d='#363a2c', sclera='#c8bfb4', sclera_d='#726e78', lash='#120a0c',
                 pupil='#0a0808', catch='#f2e9d6'),
        brow=dict(col='#2e2729', col_l='#4a4040'),
        mouth=dict(line='#46191d', corner='#5e2a2a', inner='#1a0a0b', teeth='#bcae9c', tongue='#733033'),
        features=dict(eyes=_female_eyes(), extra=[ear_detail, wrinkles(forehead=1, naso=True, under=True)],
                      brows={**BROWS_STD, 'neutral': dict(arch=1.0)}, brow_thick=((2, 1, 1), (1, 1, 1)),
                      mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.5)}),
        priority={'brooch': 3},
    )


def porter():
    rim = '#6e8fa6'
    sk = ramp('#0b0d16', '#1f1b28', '#3d2934', '#663940', '#94544c', '#bd755d', '#da9a78', '#f0c29f')
    lip = ramp('#0b0d16', '#1f1b28', '#3e2833', '#66363e', '#90504d', '#b26a5e', '#cf8c78', '#e6b098')
    styles = skin_styles(sk, rim, lip)
    navy = ramp('#06080c', '#0c1018', '#131925', '#1c2433', '#283244', '#364257', '#47546b')
    nth = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
    brass = ramp('#1a1208', '#3d2c12', '#6e5222', '#a07c36', '#d1ad5c', '#f0d890')
    styles.update({
        'cap': MatStyle(ramp('#06070a', '#0e1016', '#171a22', '#22262f', '#2f343e', '#3f4550'),
                        [0.06, 0.14, 0.27, 0.45, 0.66], dither=0.04, rim='#5d7ea4'),
        'cap_band': MatStyle(ramp('#040406', '#0a0a0e', '#121218', '#1c1c24', '#282833'),
                             [0.08, 0.2, 0.4, 0.65], rim='#4a5f78'),
        'visor': MatStyle(ramp('#030304', '#0b0b0f', '#1a1a22', '#3a3c46', '#7d8190'), [0.1, 0.3, 0.55, 0.8],
                          rim='#7d8fa6', spec=1.4, spec_pow=18.0),
        'cord': MatStyle(brass, [0.06, 0.15, 0.30, 0.50, 0.72], rim='#d1ad5c'),
        'button': MatStyle(brass, [0.05, 0.12, 0.25, 0.42, 0.62], rim='#d1ad5c', spec=0.8),
        'coat': MatStyle(navy, nth, dither=0.04, rim=rim),
        'coat_lapel': MatStyle(navy, nth, rim=rim),
        'shirt': MatStyle(ramp('#121318', '#2a2c33', '#4a4c53', '#73747a', '#9c9b9c', '#c1bdb5'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#9eb2c2'),
        'tie': MatStyle(ramp('#050508', '#0c0b10', '#16141a', '#221e25'), [0.08, 0.2, 0.45], rim=rim),
        'hair': MatStyle(ramp('#0c0d10', '#25262b', '#45464b', '#6b6b6e', '#8f8e8c', '#b2aea7'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#a8b8c4', wrap=0.35),
    })
    head = dict(mid_h=(12.8, 7.2, 11.8), jaw_angle=(12.6, 16.0, -3.6), low_r=(12.8, 11.4, 13.0),
                cheek_c=(11.2, 3.6, 9.6), cheek_r=(5.2, 3.6, 4.4), nose_tip=(0.0, 9.4, 19.8), tip_r=2.9,
                ala_x=3.0, ala_r=(1.9, 1.7, 2.1), nose_r=(1.7, 2.3), brow_r=(12.8, 3.0, 3.6),
                chin_h=(5.4, 3.4, 3.6), neck_r=(9.6, 10.8),
                jaw_extra=[('ellipsoid', ((9.4, 18.4, 7.4), (4.6, 4.0, 4.0), 'skin', 2.4)),
                           ('ellipsoid', ((-9.4, 18.4, 7.4), (4.6, 4.0, 4.0), 'skin', 2.4)),
                           ('ellipsoid', ((0.0, 26.4, 6.8), (7.4, 3.4, 5.6), 'skin', 2.8))])
    return dict(
        id='porter', city='berlin',
        look=dict(key=(0.56, -0.42, 0.71), rim=(-0.80, -0.35, -0.50), ambient=0.07, bg='berlin',
                  glow=(0.80, 0.18)),
        head=head, zoom=1.10,
        head_pos=(55.0, 57.0, 0.0), yaw=28.0, pitch=3.0, roll=0.0,
        torso_pos=(55.0, 94.0, -0.5), torso_yaw=12.0, torso=dict(width=1.14, depth=1.18, slope=0.9),
        poses=POSES_STD,
        head_items=[lambda M, hp: peaked_cap(M, hp),
                    lambda M, hp: hair_short(M, hp, hairline=-14.0, front_z=8.0, burn_y=3.0)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.30, v_top=3.0, lapel=True, collar_h=6.0,
                                     collar_r=(12.6, 14.0)),
            lambda M, t: tie_knot_collar(M),
            lambda M, t: tie(M, mat='tie', top=(0.2, 3.4, 10.0), bot=(0.6, 24.0, 13.8)),
            lambda M, t: surface_buttons(M, t, 2.6, [(-7.6, 9.5), (7.6, 9.5), (-8.4, 16.5), (8.4, 16.5)],
                                         r=1.15),
        ],
        styles=styles,
        skin=('skin', 'lip', 'ear', 'neck'),
        groups={'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'cap': 2, 'cap_band': 2, 'cord': 2,
                'visor': 3, 'coat': 4, 'coat_lapel': 8, 'shirt': 5, 'tie': 5, 'button': 7, 'body': 4},
        tone_passes=[pass_grain('coat', 0.05, seed=6), pass_grain('cap', 0.05, seed=7), pass_strands('hair')],
        eye=dict(iris='#5d6a72', iris_d='#363f46', sclera='#c4bcb2', sclera_d='#726e78', lash='#140c10',
                 pupil='#0b0a0e', catch='#f2ead8'),
        brow=dict(col='#5e5c5c', col_l='#8c8884'),
        mouth=dict(line='#3a1c20', corner='#5a2c2c', inner='#1c0c0e', teeth='#b2a593', tongue='#6c3034'),
        features=dict(extra=[ear_detail, wrinkles(forehead=2, under=True), eye_bags()],
                      brows={**BROWS_STD, 'neutral': dict(arch=0.3, lift_inner=-0.3)},
                      brow_thick=((3, 2, 2), (2, 2, 1)), mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.7)}),
        priority={'button': 3, 'cord': 2, 'visor': 1},
    )


CAST['vendor'] = vendor
CAST['worker_a'] = worker_a
CAST['babushka'] = babushka
CAST['librarian'] = librarian
CAST['porter'] = porter


def pass_folds(mat='kerchief', knot=(0.0, 11.0, -20.0), mode='nape', n=9, seed=81, width=0.10):
    """Cloth folds radiating towards a knot: a dark crease with a lit ridge beside it (tone map), so a
    headscarf reads as gathered fabric instead of a smooth cap."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = _local(G, 'hf', m)
        if mode == 'nape':
            a = np.arctan2(L[:, 1] - knot[1], L[:, 2] - knot[2])
            r = np.sqrt((L[:, 1] - knot[1]) ** 2 + (L[:, 2] - knot[2]) ** 2)
        else:
            a = np.arctan2(L[:, 0] - knot[0], L[:, 1] - knot[1])
            r = np.sqrt((L[:, 0] - knot[0]) ** 2 + (L[:, 1] - knot[1]) ** 2)
        wob = 0.05 * np.sin(r * 0.35 + seed)
        u = (a / (2 * np.pi) + 0.5) * n * 2.0 + wob * n
        k = np.floor(u).astype(int)
        f = u - k
        keep = _hash2(k, np.zeros_like(k), seed) < 0.7          # irregular: some folds missing
        far = r > 6.0                                           # folds fade out near the knot itself
        crease = keep & far & (f < width)
        ridge = keep & far & (f >= width) & (f < width * 2.2)
        t = tone[m].copy()
        t = np.where(crease & (t >= 2), t - 2, np.where(ridge, t + 1, t))
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def pass_scarf_border(front_y, slope=1.15, z_off=0.5, band=(-2.7, -1.6), lit='#b8873e', shade='#5a3f1e',
                      mat='kerchief'):
    """Printed border stripe running parallel to the face edge of a nape-tied headscarf (rgb pass): the
    stripe makes the cloth read as a scarf, never as hair."""
    def fn(spec, G, rgb, v, expr, row):
        M = G['M']
        if mat not in M.names:
            return rgb
        m = G['d'].mat == M.names.index(mat)
        if not m.any():
            return rgb
        L = _local(G, 'hf', m)
        y, z = L[:, 1], L[:, 2]
        reg = np.maximum(np.minimum(y - front_y, z - z_off + slope * y), y - 13.0)
        on = (reg > band[0]) & (reg < band[1]) & (y < 9.0)
        ys, xs = np.nonzero(m)
        cl, cs = _rgb(lit), _rgb(shade)
        for x, yy, o in zip(xs, ys, on):
            if o:
                rgb[yy, x] = cl if v[yy, x] > 0.28 else cs
        return rgb
    return fn
