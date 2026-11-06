"""chargen_portrait_c3 -- dialogue portraits of the Chapter 3 cast on the round-2 portrait pipeline.

Round 7 (2026-11-06).  The first version of this module (cloud session, round 1) imported the first-generation
ellipsoid-bust API of chargen_portrait.py, which master had already replaced by the round-2 pipeline -- it no
longer imported at all, and its static 4-frame strips had no talking mouth and no blink.  This version
registers the seven Chapter-3 speakers in chargen_portrait2_cast.CAST, so chargen_portrait2 builds them like
every other speaker: signed-distance sculpted busts, hand-designed eye / brow / mouth features, 4 expressions x
6 states (rest, talk half / open, blink ...) in portrait_anim.png + the static portrait.png strip.

    py -3 -P tools/pixelgen/chargen_portrait2.py elena kessler     (some C3 speakers)
    py -3 -P tools/pixelgen/chargen_portrait2.py --jobs=8          (every speaker, one process each)

Every face is its own: nose, chin / jaw, eye shape and brows differ per person (head params, eye_shapes(),
brow_pts), see documentation/asset_manifest_parts/portraits_r7.md.  Costumes follow C3_DESIGN.md section 5.
No regime insignia: the border officer's cap badge is the Free City's bridge, the conductor's the railway's
winged wheel (no state emblem).  Deterministic: no randomness, no image inputs.
"""
from __future__ import annotations

import numpy as np

import chargen_portrait2_cast as PC
import chargen_portrait2_face as FC
import chargen_portrait2_sdf as S
from chargen_portrait2_cast import (BROWS_STD, FEMALE, MOUTH_STD, POSES_STD, SKIN_TH, _female_eyes, _local,
                                    _rgb, band_on, coat_layers, ear_detail, eye_bags, glasses, hair_short,
                                    lapels, layered_front, moustache, pass_fur, pass_grain, pass_knit,
                                    pass_strands, peaked_cap, rollneck, scarf_wrap, skin_styles, strap,
                                    stubble, surface_buttons, tie, tie_knot_collar, wrinkles)
from chargen_portrait2_paint import MatStyle, ramp

E = S.Ellipsoid

# ----------------------------------------------------------------------------------- palettes
# dawn station: navy core, violet shadow, warm lamp half-tones; palace: navy-teal core, cool daylight
SKIN_VELTRAVA = ramp('#0a0e18', '#1c1c2b', '#392a39', '#5f3c45', '#8b5a51', '#b57c63', '#d6a27f', '#edc8a1')
SKIN_PALAIS = ramp('#081014', '#1a1c27', '#382a35', '#5e3b41', '#8a594f', '#b47b61', '#d5a07d', '#ecc6a0')
SKIN_OLD = ramp('#0a0e18', '#1e1c2a', '#3c2c39', '#624148', '#8e6058', '#b6846f', '#d6aa8f', '#ecceb3')
RIM_V = '#7f93b4'          # slate dawn
RIM_P = '#7fa2ae'          # palace window light


def lip_of(sk, warm=0):
    """Lip ramp derived from a skin ramp: same dark end, a little redder in the mid tones."""
    base = [np.asarray(c, int) for c in sk]
    out = []
    for i, c in enumerate(base):
        if 2 <= i <= 6:
            c = c + np.array([10 + warm, -6, -4]) * (1 if i < 6 else 0.5)
        out.append('#%02x%02x%02x' % tuple(int(v) for v in np.clip(c, 0, 255)))
    return ramp(*out)


def look_v(**kw):
    d = dict(key=(0.58, -0.42, 0.70), rim=(-0.80, -0.34, -0.50), ambient=0.07, bg='veltrava', glow=(0.80, 0.22))
    d.update(kw)
    return d


def look_p(**kw):
    d = dict(key=(0.56, -0.44, 0.71), rim=(-0.80, -0.30, -0.50), ambient=0.08, bg='palais', glow=(0.78, 0.20))
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------- head items
def homburg(M, hp, tilt=(4.0, -2.0), y0=-12.8, z0=-5.0, band_r=(17.2, 21.4), crown_h=15.5, brim_w=8.6):
    """Homburg: stiff felt crown with ONE centre dent (gutter crown, no front pinches), grosgrain band and
    a brim curled up evenly all round (bound edge).  Hat frame origin = centre of the band's lower edge."""
    felt, band, brim_m = M('felt'), M('ribbon'), M('brim')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = band_r

    def tap(P):
        s_ = 1.0 + 0.10 * np.clip(-P[:, 1] / crown_h, 0, 1)
        off = np.zeros_like(P)
        off[:, 0] = P[:, 0] - P[:, 0] * s_
        off[:, 2] = P[:, 2] - P[:, 2] * s_
        return off

    base = S.Warp(S.EllipticCylinder((0, -(crown_h - 4.0) / 2, 0), rx, rz, (crown_h + 4.0) / 2, felt, e=3.6),
                  tap, lip=1.12)
    crown = S.Sub(base, S.RoundCone((0, -crown_h - 1.2, -rz * 0.55), (0, -crown_h - 0.6, rz * 0.55), 2.6, 2.6,
                                    felt), k=2.2)
    bandn = S.EllipticCylinder((0, -2.2, 0), rx + 0.45, rz + 0.45, 2.0, band, e=0.4)

    def curl(P):
        x, z = P[:, 0], P[:, 2]
        r = np.sqrt((x / (rx + brim_w)) ** 2 + (z / (rz + brim_w + 1.0)) ** 2)
        off = np.zeros_like(P)
        off[:, 1] = -2.4 * np.clip(r - 0.72, 0, 1) ** 1.5 * 6.0      # edge rolls up all round
        return off

    brimn = S.Warp(S.EllipticCylinder((0, 0.3, 0.4), rx + brim_w, rz + brim_w + 1.0, 0.75, brim_m, e=0.65),
                   curl, lip=1.35)
    hat = S.Union([crown, bandn, brimn])
    inner = S.Offset(base, -0.7)
    allowed = S.Union([inner, S.Fn(lambda P: -(P[:, 1] - 1.6), felt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def pirozhok(M, hp, tilt=(-2.0, -3.0), y0=-13.4, z0=-4.6, r=(17.0, 20.6), h=9.4, seed=91):
    """Karakul 'pirozhok': a brimless oval fur toque, flat crown with a lengthwise crease, worn level."""
    m = M('karakul')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    def taper(P):
        s_ = 1.0 - 0.07 * np.clip(-P[:, 1] / h, 0, 1)
        off = np.zeros_like(P)
        off[:, 0] = P[:, 0] - P[:, 0] / s_
        off[:, 2] = P[:, 2] - P[:, 2] / s_
        return off

    body = S.Warp(S.EllipticCylinder((0, -h / 2 + 0.4, 0), rx + 0.6, rz + 0.6, h / 2 + 0.4, m, e=2.6), taper,
                  lip=1.12)
    body = S.Sub(body, S.RoundCone((0, -h - 0.6, -rz * 0.7), (0, -h - 0.6, rz * 0.7), 1.6, 1.6, m), k=1.6)
    body = S.Displace(body, lambda P: S.vnoise3(P, 1.1, seed) + 0.5 * S.vnoise3(P, 2.4, seed + 3), amp=0.7,
                      lipschitz=1.4)
    inner = S.Offset(S.EllipticCylinder((0, -h / 2, 0), rx, rz, h / 2 + 0.4, m, e=2.0), -0.6)
    allowed = S.Union([inner, S.Fn(lambda P: -(P[:, 1] - 1.0), m)])
    return dict(node=S.Xform(body, frame=hf), clip=S.Xform(allowed, frame=hf))


def hair_swept(M, hp, mat='hair', hairline=-13.4, thick=2.4, part_x=6.0, nape_bun=(-0.5, 6.5, -21.5),
               bun_r=(7.4, 6.4, 5.8), seed=95):
    """Hair parted on the far side and swept back over the ears into a low chignon at the nape (Elena):
    a full shell over the skull, a swell where it sweeps back over the near ear, the chignon behind."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    shell = S.Offset(E(sc + np.array([0.0, -0.5, 0.0]), sr, m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        # the hairline dips a little towards the temples and rises at the parting
        front = np.minimum(y - hairline - 0.16 * np.abs(x) + 1.4 * np.exp(-((x - part_x) / 2.5) ** 2), z - 5.5)
        side = np.minimum(y - 7.0, z + 3.0)              # covers the ear and sweeps back
        return np.maximum(np.maximum(front, side), y - 12.5)

    hairn = S.Inter(shell, S.Fn(region, m))
    swell = S.Inter(E((-9.8, -6.5, -1.0), (5.0, 6.8, 9.0), m),
                    S.Fn(lambda P: np.minimum(P[:, 2] - 2.5, hairline + 2.0 - P[:, 1]), m))
    bun = S.Displace(E(nape_bun, bun_r, m), lambda P: S.vnoise3(P, 1.7, seed), amp=0.35)
    return S.Union([hairn, swell, bun], k=[1.6, 1.8])


def hair_curls(M, hp, mat='hair', hairline=-13.2, nape=7.0, thick=2.4, seed=97):
    """Short set hair in soft curls (a 1960s office perm): a thick lumpy cap ending above the collar."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    shell = S.Offset(E(sc + np.array([0, -0.6, -0.4]), sr, m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = np.minimum(y - hairline - 0.08 * np.abs(x), z - 5.5)
        side = np.minimum(y - 2.5, z + 1.0)
        ear = np.maximum(np.maximum(y + 2.5, -y + 9.0), np.maximum(z + 1.0, -8.5 - z))
        return np.maximum(np.maximum(np.maximum(front, side), y - nape), -ear)

    node = S.Inter(shell, S.Fn(region, m))
    return S.Displace(node, lambda P: S.vnoise3(P, 1.5, seed) + 0.45 * S.vnoise3(P, 3.0, seed + 1), amp=1.15,
                      lipschitz=1.5)


def hair_tousled(M, hp, mat='hair', hairline=-14.6, thick=1.8, seed=99):
    """Fair tousled hair, bareheaded: fuller on top, a loose forelock, short at the neck (journalist)."""
    m = M(mat)
    sc, sr = np.array(hp['skull_c']), np.array(hp['skull_r'])
    shell = S.Offset(E(sc + np.array([0.0, -1.4, 0.4]), sr * np.array([1.0, 1.03, 1.0]), m), thick, m)

    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = np.minimum(y - hairline + 0.9 * np.clip(x - 2.0, 0, 6) * 0.25, z - 7.5)
        side = np.minimum(y - 1.0, z + 2.0)
        ear = np.maximum(np.maximum(y + 3.0, -y + 9.0), np.maximum(z + 2.0, -9.0 - z))
        return np.maximum(np.maximum(np.maximum(front, side), y - 8.0), -ear)

    node = S.Inter(shell, S.Fn(region, m))
    lock = E((3.5, -14.6, 12.0), (4.6, 2.2, 3.0), m, R=S.rot(0, -20, 18))
    node = S.Union([node, lock], k=1.6)
    return S.Displace(node, lambda P: S.vnoise3(P * np.array([1.0, 0.7, 1.0], np.float32), 1.9, seed), amp=0.7,
                      lipschitz=1.35)


def temple_wave(M, hp, mat='hair', seed=107):
    """A soft wave of hair over the near temple and ear, below a hat brim (Voronova)."""
    m = M(mat)
    w = E((-11.6, -5.0, 1.0), (3.4, 5.6, 6.6), m, R=S.rot(0, 0, -12))
    w = S.Inter(w, S.Fn(lambda P: P[:, 2] - 6.0, m))
    return S.Displace(w, lambda P: S.vnoise3(P, 1.6, seed), amp=0.4)


def fur_collar(M, mat='karakul', y=-1.0, r=13.2, tube=4.6, seed=93):
    """Karakul shawl collar: a fur roll round the neck that runs down both lapels (torso-local)."""
    m = M(mat)
    parts = []
    for i in range(13):
        a = np.radians(-150 + i * 25.0)
        parts.append(E((r * np.sin(a), y + 1.6 * (1 - np.cos(a)), -1.5 + (r - 1.0) * np.cos(a)),
                       (tube + 1.2, tube, tube + 0.5), m))
    for sx in (1, -1):
        parts.append(S.RoundCone((sx * 6.0, y + 6.0, 11.0), (sx * 3.4, y + 26.0, 13.0), 4.2, 2.6, m))
    node = S.Union(parts, k=2.6)
    return S.Displace(node, lambda P: S.vnoise3(P, 1.3, seed), amp=0.6, lipschitz=1.3)


# ----------------------------------------------------------------------------------- 2D passes
def pass_curls(mat='karakul', seed=101, frame='hf', light=1, dark=1):
    """Tight karakul / perm curls: little C-shaped clusters (a lit pixel over a dark one) on a coarse lattice,
    so the pile reads as curls, not as noise."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        ys, xs = np.nonzero(m)
        if not len(xs):
            return tone
        tone = tone.copy()
        r = PC._hash2(xs // 2, ys // 2, seed)
        sub = ((xs + (ys // 2) % 2) % 2 == 0) & (ys % 2 == 0)
        for x, y, rv, s_ in zip(xs, ys, r, sub):
            if not s_:
                continue
            if rv < 0.55 and tone[y, x] >= 2:
                tone[y, x] += light
                if y + 1 < tone.shape[0] and m[y + 1, x] and tone[y + 1, x] >= 2:
                    tone[y + 1, x] -= dark
        return tone
    return fn


def pass_badge(at, rows, cols, frame='hf'):
    """Small cap badge drawn as absolute pixels on the cap band (projected from the head frame)."""
    def fn(spec, G, rgb, v, expr, row):
        from chargen_portrait2 import zoom_pt
        p = zoom_pt({'zoom': G.get('zoom', 1.0)}, G[frame].to_view(at))
        x0, y0 = int(np.floor(p[0])), int(np.floor(p[1]))
        h, w = rgb.shape[:2]
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == '.':
                    continue
                x, y = x0 - len(r) // 2 + i, y0 - len(rows) // 2 + j
                if 0 <= x < w and 0 <= y < h and G['d'].hit[y, x]:
                    rgb[y, x] = _rgb(cols[ch])
        return rgb
    return fn


def pass_armband(x_range, y_range, white='#d9dde2', white_d='#7e8794', stripe='#46628c', stripe_d='#22324c',
                 mats=('coat',), frame='tf'):
    """The commission's white armband with a slate-blue stripe on the near upper arm (torso frame box)."""
    def fn(spec, G, rgb, v, expr, row):
        M = G['M']
        ids = [M.names.index(n) for n in mats if n in M.names]
        m = np.isin(G['d'].mat, ids)
        if not m.any():
            return rgb
        L = _local(G, frame, m)
        ys, xs = np.nonzero(m)
        on = (L[:, 0] > x_range[0]) & (L[:, 0] < x_range[1]) & (L[:, 1] > y_range[0]) & (L[:, 1] < y_range[1])
        band_lo = y_range[0] + (y_range[1] - y_range[0]) * 0.62
        for x, y, o, ly in zip(xs, ys, on, L[:, 1]):
            if o:
                lit = v[y, x] > 0.28
                if ly > band_lo:
                    rgb[y, x] = _rgb(stripe if lit else stripe_d)
                else:
                    rgb[y, x] = _rgb(white if lit else white_d)
        return rgb
    return fn


def pencil_ear(spec, G, rgb, v, expr, row):
    """Frau Brunner's pencil behind the near ear: a short yellow stroke with a dark point."""
    lm = G['lmv']['ear_r']
    x0, y0 = int(np.floor(lm[0])) + 1, int(np.floor(lm[1])) - 5
    h, w = rgb.shape[:2]
    cols = ['#d8b04c', '#c9a23a', '#c9a23a', '#a8842c', '#e0cfa0', '#3a2c20']
    for k, c in enumerate(cols):
        x, y = x0 + k, y0 + k // 2
        if 0 <= x < w and 0 <= y < h:
            rgb[y, x] = _rgb(c)
    return rgb


def loose_strand(spec, G, cv, expr, mouth_state, blink, v):
    """One strand escaped from Elena's chignon at the near temple (end of a long day -- not glamour)."""
    PC.head_line(G, cv, [(-9.2, -11.0, 9.4), (-10.0, -6.5, 9.0), (-9.4, -2.5, 9.2)], -2,
                 allow_mats=('skin', 'ear'))


def cheek_hollow(spec, G, cv, expr, mouth_state, blink, v):
    """Gaunt cheeks under the cheekbones (conductor, Kessler): a short darker stroke."""
    for sx in (-1, 1):
        PC.head_line(G, cv, [(sx * 9.6, 6.6, 9.6), (sx * 8.6, 10.6, 9.4)], -1)


def chin_cleft(spec, G, cv, expr, mouth_state, blink, v):
    PC.head_line(G, cv, [(0.2, 21.0, 15.2), (0.2, 23.6, 14.6)], -1)


# ----------------------------------------------------------------------------------- shared
def groups_std(extra=None):
    g = {'skin': 0, 'lip': 0, 'ear': 0, 'hair': 0, 'neck': 1, 'coat': 4, 'coat_lapel': 8, 'shirt': 5, 'body': 4}
    g.update(extra or {})
    return g


def coat_style(ramp_, th, rim, dither=0.05):
    return {'coat': MatStyle(ramp_, th, dither=dither, rim=rim), 'coat_lapel': MatStyle(ramp_, th, rim=rim)}


TH6 = [0.05, 0.12, 0.22, 0.36, 0.54, 0.76]
# softer planes for the women's faces (flatter brow ridge, rounder blocks, shallower sockets, thinner jaw line,
# fuller cheek pads) -- applied on top of chargen_portrait2_cast.FEMALE
SOFT = dict(brow_r=(10.8, 1.8, 2.4), brow_c=(0.0, -3.4, 12.4), fore_rad=7.5, mid_rad=6.8, socket_r=(4.0, 2.4, 1.6),
            jaw_r=(2.0, 2.4, 2.4), malar_r=(4.6, 4.2, 4.0), malar_c=(7.0, 8.0, 12.4))
TH7 = [0.04, 0.10, 0.19, 0.31, 0.46, 0.64, 0.84]


# =================================================================================== ELENA
def elena():
    """Elena Weiss (30s): slim oval face, fine straight nose, small firm chin, alert eyes with a lifted outer
    corner and fine arched brows; dark hair swept back into a low chignon, one strand loose; wine-red scarf
    wrapped high, charcoal wool coat, the commission's white armband with the slate stripe."""
    sk = SKIN_VELTRAVA
    styles = skin_styles(sk, RIM_V, lip_of(sk, warm=6))
    styles.update(coat_style(ramp('#06070b', '#0d0e13', '#16171d', '#212229', '#2d2e36', '#3c3d45', '#504f56'),
                             TH6, RIM_V))
    styles.update({
        'hair': MatStyle(ramp('#050406', '#0e0b0d', '#1a1415', '#271d1c', '#372923', '#4a382d'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#5a6a86', wrap=0.2),
        'scarf': MatStyle(ramp('#0c0406', '#1d080d', '#330d16', '#4e1420', '#6c1c2b', '#8a2737', '#a63a45'),
                          TH6, dither=0.03, rim='#8a7a96'),
        'shirt': MatStyle(ramp('#0b0c10', '#1a1b21', '#2a2b33'), [0.1, 0.3], rim=RIM_V),
    })
    head = dict(FEMALE)
    head.update(SOFT)
    head.update(skull_r=(15.2, 16.4, 19.6), mid_h=(10.4, 6.4, 10.8), cheek_c=(9.8, 2.2, 10.2), cheek_r=(3.6, 2.6, 3.4),
                jaw_angle=(9.0, 13.4, -4.4), low_r=(10.0, 9.6, 11.6),
                chin_c=(0.0, 21.0, 11.4), chin_h=(3.4, 2.8, 2.9), chin_rad=2.8, chin_pt=(3.0, 21.8, 9.6),
                nose_root=(0.0, -1.2, 15.6), nose_tip=(0.0, 8.6, 19.3), nose_r=(1.1, 1.5), tip_r=1.95,
                ala_x=2.0, ala_r=(1.3, 1.3, 1.6), eye_x=6.4, lip_up_r=(3.8, 1.25, 1.4), lip_lo_r=(3.3, 1.6, 1.5),
                brow_r=(11.2, 2.0, 2.8), neck_r=(6.4, 7.8))
    return dict(
        id='elena', city='veltrava', look=look_v(),
        head=head, zoom=1.18, smooth=2,
        head_pos=(55.0, 55.0, 0.0), yaw=31.0, pitch=1.0, roll=-1.0,
        torso_pos=(55.5, 90.5, -0.5), torso_yaw=14.0, torso=dict(width=0.88, depth=0.94, slope=1.4),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 3, -2), 'determined': (2, -1, 1), 'surprised': (3, -3, 1)},
        head_items=[lambda M, hp: hair_swept(M, hp)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.26, v_top=5.0, lapel=True, collar_h=6.0, collar_r=(11.6, 13.2)),
            lambda M, t: scarf_wrap(M, y=-7.0, r=9.8, tube=4.4, ends=True,
                                    end_pts=[(-1.0, -3.0, 11.6), (-3.0, 7.0, 13.2), (-3.6, 17.0, 14.0)], seed=7),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'scarf': 6}),
        tone_passes=[pass_strands('hair', seed=14), pass_knit('scarf', ribs=28), pass_grain('coat', 0.05, seed=12)],
        rgb_passes=[pass_armband((-40.0, -21.0), (24.0, 34.0))],
        eye=dict(iris='#3e2f28', iris_d='#241a16', sclera='#c7beb2', sclera_d='#6c6a76', lash='#0e080c',
                 pupil='#08070a', catch='#f2ead8'),
        brow=dict(col='#1c1214', col_l='#3a2a26'),
        mouth=dict(line='#46191f', corner='#5e2a2c', inner='#1a0a0d', teeth='#bcaea0', tongue='#733035'),
        features=dict(
            eyes=FC.eye_shapes(_female_eyes(), 'lift'),
            extra=[ear_detail],
            brows={'neutral': dict(arch=1.1), 'concerned': dict(lift_inner=2.0, lift_outer=-0.4, arch=0.6),
                   'determined': dict(lift_inner=-1.4, arch=0.4, dy=0.4),
                   'surprised': dict(dy=-1.8, arch=1.5, lift_inner=0.4)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.8, -4.1, 17.0), (10.2, -3.9, 13.2)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.1), 'concerned': dict(corner_drop=0.8),
                   'determined': dict(corner_drop=0.4), 'surprised': dict(parted=2)},
        ),
        priority={'scarf': 1},
    )


# =================================================================================== BORDER OFFICER
def border_officer():
    """Frontier officer (50s): broad fleshy face, short wide nose, heavy jowls, a grey moustache, hooded
    tired eyes under bushy brows; slate-blue cap with the Free City's bridge badge, greatcoat, armband."""
    sk = SKIN_VELTRAVA
    styles = skin_styles(sk, RIM_V, lip_of(sk))
    slate = ramp('#05070c', '#0b111b', '#121b2a', '#1b273b', '#26354d', '#344663', '#465a7a', '#5c7092')
    styles.update(coat_style(slate, TH7, RIM_V))
    styles.update({
        'cap': MatStyle(ramp('#05070c', '#0b111b', '#141e2e', '#1e2b40', '#2a3a54', '#3a4c68'),
                        [0.06, 0.14, 0.27, 0.45, 0.66], dither=0.04, rim='#6e88aa'),
        'cap_band': MatStyle(ramp('#030407', '#080b12', '#0e1420', '#161e2e', '#20293c'), [0.08, 0.2, 0.4, 0.65],
                             rim='#4a5f78'),
        'visor': MatStyle(ramp('#030304', '#0b0b0f', '#1a1a22', '#3a3c46', '#7d8190'), [0.1, 0.3, 0.55, 0.8],
                          rim='#7d8fa6', spec=1.4, spec_pow=18.0),
        'cord': MatStyle(ramp('#0a0c10', '#1c2028', '#343a46', '#566070', '#7c8696'), [0.08, 0.2, 0.42, 0.65],
                         rim='#9aa6b8'),
        'shirt': MatStyle(ramp('#121318', '#2a2c33', '#4a4c53', '#73747a', '#9c9b9c', '#c1bdb5'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#9eb2c2'),
        'tie': MatStyle(ramp('#050508', '#0c0f16', '#151b26', '#1f2836'), [0.08, 0.2, 0.45], rim=RIM_V),
        'hair': MatStyle(ramp('#0a0909', '#1c1817', '#302926', '#4a4240', '#6e6864', '#96928c'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#a8b8c4', wrap=0.3),
        'moustache': MatStyle(ramp('#0a0909', '#1c1817', '#302926', '#45403c', '#5e5852', '#7a746c'),
                              [0.04, 0.10, 0.2, 0.36, 0.58], rim='#8a98a8', wrap=0.3),
        'button': MatStyle(ramp('#1a1c20', '#3c4048', '#6a707a', '#9aa0a8', '#c8ccd0'), [0.06, 0.16, 0.32, 0.55],
                           rim='#c8ccd0', spec=0.8),
    })
    head = dict(mid_h=(12.8, 7.0, 11.8), cheek_c=(11.2, 3.4, 9.6), cheek_r=(5.2, 3.6, 4.4), malar_r=(4.6, 3.8, 3.8),
                jaw_angle=(12.8, 15.8, -3.6), low_r=(13.0, 11.2, 13.0), chin_h=(5.2, 3.2, 3.4), chin_c=(0.0, 21.8, 12.0),
                nose_root=(0.0, -1.0, 15.2), nose_tip=(0.0, 8.6, 19.0), tip_r=2.8, nose_r=(1.6, 2.3), ala_x=3.2,
                ala_r=(2.0, 1.7, 2.1), brow_r=(12.8, 3.0, 3.6), neck_r=(9.4, 10.6), lip_up_r=(4.4, 1.0, 1.3),
                jaw_extra=[('ellipsoid', ((9.8, 17.6, 7.4), (4.8, 4.2, 4.0), 'skin', 2.4)),
                           ('ellipsoid', ((-9.8, 17.6, 7.4), (4.8, 4.2, 4.0), 'skin', 2.4))],
                extra=moustache(c=(0.0, 12.6, 17.6), r=(4.2, 1.2, 1.6), droop=0.6))
    return dict(
        id='border_officer', city='veltrava', look=look_v(),
        head=head, zoom=1.10,
        head_pos=(55.0, 57.0, 0.0), yaw=27.0, pitch=4.0, roll=-1.0,
        torso_pos=(55.0, 94.0, -0.5), torso_yaw=12.0, torso=dict(width=1.12, depth=1.12, slope=0.9),
        poses=POSES_STD,
        head_items=[lambda M, hp: peaked_cap(M, hp, y0=-13.0, tilt=(4.0, -1.0)),
                    lambda M, hp: hair_short(M, hp, hairline=-13.6, front_z=8.0, burn_y=3.5)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.30, v_top=3.0, lapel=True, collar_h=7.0, collar_r=(12.8, 14.4)),
            lambda M, t: tie_knot_collar(M),
            lambda M, t: tie(M, mat='tie', top=(0.2, 3.4, 10.0), bot=(0.6, 24.0, 13.8)),
            lambda M, t: surface_buttons(M, t, 2.6, [(-7.8, 10.0), (7.8, 10.0), (-8.6, 18.0), (8.6, 18.0)], r=1.15),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'moustache': 9, 'cap': 2, 'cap_band': 2, 'cord': 2, 'visor': 3, 'tie': 5, 'button': 7}),
        tone_passes=[pass_grain('coat', 0.05, seed=16), pass_grain('cap', 0.05, seed=17), pass_strands('hair'),
                     pass_strands('moustache', seed=18)],
        rgb_passes=[pass_armband((-42.0, -22.0), (26.0, 36.0)),
                    pass_badge((0.0, -16.2, 21.6), ['.w.w.', 'wwwww', 's...s'],
                               {'w': '#d8dde2', 's': '#5c7090'})],
        eye=dict(iris='#5d6a72', iris_d='#363f46', sclera='#c0b8ae', sclera_d='#6e6a74', lash='#140c10',
                 pupil='#0b0a0e', catch='#f2ead8'),
        brow=dict(col='#2a2422', col_l='#4c4440'),
        mouth=dict(line='#3a1c20', corner='#5a2c2c', inner='#1c0c0e', teeth='#b2a593', tongue='#6c3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'hooded', 'narrow'),
            extra=[ear_detail, wrinkles(forehead=1, crow=True, naso=True, under=False), eye_bags()],
            brows={**BROWS_STD, 'neutral': dict(arch=0.2, lift_inner=-0.2)},
            brow_thick=((3, 3, 2), (2, 2, 2)), brow_pts=((1.4, -4.0, 17.2), (11.0, -3.0, 13.2)), nostril='wide',
            mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.6)}),
        priority={'button': 3, 'cord': 2, 'visor': 1, 'moustache': 1},
    )


# =================================================================================== CONDUCTOR
def conductor():
    """Schaffner (60): a long tired face, a long nose with a drooping tip, a receding chin half hidden by a
    full grey walrus moustache, gaunt cheeks, kind drooping eyes under grey brows; navy railway cap with the
    winged-wheel badge (no state emblem), uniform coat with brass buttons, the strap of his bag."""
    sk = SKIN_OLD
    styles = skin_styles(sk, RIM_V, lip_of(sk))
    navy = ramp('#04060a', '#090d16', '#0f1522', '#171f30', '#212b40', '#2d3954', '#3c4a68')
    styles.update(coat_style(navy, TH6, RIM_V))
    brass = ramp('#1a1208', '#3d2c12', '#6e5222', '#a07c36', '#d1ad5c', '#f0d890')
    styles.update({
        'cap': MatStyle(ramp('#04060a', '#0a0e18', '#121826', '#1a2234', '#252f44', '#323e56'),
                        [0.06, 0.14, 0.27, 0.45, 0.66], dither=0.04, rim='#5d7ea4'),
        'cap_band': MatStyle(ramp('#030305', '#08090e', '#0e1016', '#161820', '#20232e'), [0.08, 0.2, 0.4, 0.65],
                             rim='#4a5f78'),
        'visor': MatStyle(ramp('#030304', '#0b0b0f', '#1a1a22', '#3a3c46', '#7d8190'), [0.1, 0.3, 0.55, 0.8],
                          rim='#7d8fa6', spec=1.4, spec_pow=18.0),
        'cord': MatStyle(brass, [0.06, 0.15, 0.30, 0.50, 0.72], rim='#d1ad5c'),
        'button': MatStyle(brass, [0.05, 0.12, 0.25, 0.42, 0.62], rim='#d1ad5c', spec=0.8),
        'shirt': MatStyle(ramp('#121318', '#2a2c33', '#4a4c53', '#73747a', '#9c9b9c', '#c1bdb5'),
                          [0.05, 0.12, 0.24, 0.42, 0.62], rim='#9eb2c2'),
        'tie': MatStyle(ramp('#050508', '#0c0b10', '#16141a', '#221e25'), [0.08, 0.2, 0.45], rim=RIM_V),
        'strap': MatStyle(ramp('#0a0607', '#1b0f0c', '#2e1a12', '#472918', '#633a22', '#7d4f30'),
                          [0.05, 0.12, 0.24, 0.40, 0.6], rim='#6a6a76'),
        'hair': MatStyle(ramp('#121316', '#2e2f33', '#56575a', '#808080', '#a8a6a2', '#cbc8c0', '#e2ded6'),
                         [0.03, 0.08, 0.16, 0.28, 0.44, 0.66], rim='#c2ccd4', wrap=0.45, lift=0.3),
        'moustache': MatStyle(ramp('#121316', '#2e2f33', '#56575a', '#808080', '#a8a6a2', '#cbc8c0', '#e2ded6'),
                              [0.03, 0.08, 0.16, 0.28, 0.44, 0.66], rim='#c2ccd4', wrap=0.45, lift=0.3),
    })
    head = dict(mid_h=(11.4, 7.6, 11.4), skull_r=(15.8, 17.2, 20.4), cheek_c=(10.6, 2.6, 9.8), cheek_r=(4.2, 2.6, 3.6),
                malar_r=(3.2, 2.8, 2.8), jaw_angle=(10.8, 16.4, -4.0), low_r=(11.2, 11.8, 12.4),
                chin_c=(0.0, 22.8, 10.8), chin_h=(4.0, 3.4, 3.0), chin_pt=(3.6, 23.8, 9.0),
                nose_root=(0.0, -1.4, 15.6), nose_tip=(0.0, 10.6, 19.6), tip_r=2.6, nose_r=(1.5, 2.1), ala_x=2.6,
                ala_y=11.4, ala_r=(1.7, 1.5, 1.9), brow_r=(12.4, 2.8, 3.4), mouth_y=15.6, lip_up=(0.0, 14.8, 16.2),
                lip_up_r=(4.0, 0.9, 1.2), lip_lo=(0.0, 16.9, 15.6), lip_lo_r=(3.4, 1.1, 1.2),
                ear_r=(1.9, 6.8, 3.9), ear_c=(15.8, 3.8, -5.6),
                jaw_extra=[('ellipsoid', ((8.6, 18.6, 7.6), (3.8, 3.6, 3.4), 'skin', 2.2)),
                           ('ellipsoid', ((-8.6, 18.6, 7.6), (3.8, 3.6, 3.4), 'skin', 2.2))],
                extra=moustache(c=(0.0, 13.4, 17.6), r=(5.4, 1.9, 2.0), droop=2.4)
                + [('sub', ((10.4, 9.0, 9.6), (2.4, 3.2, 2.0), 1.6)), ('sub', ((-10.4, 9.0, 9.6), (2.4, 3.2, 2.0), 1.6))])
    return dict(
        id='conductor', city='veltrava', look=look_v(),
        head=head, zoom=1.10,
        head_pos=(54.0, 59.0, 0.0), yaw=27.0, pitch=6.0, roll=-2.0,
        torso_pos=(54.0, 96.0, -2.0), torso_yaw=13.0, torso=dict(width=0.98, depth=1.04, slope=1.8),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 3, -2), 'determined': (1, -2, 1), 'surprised': (2, -5, 1)},
        head_items=[lambda M, hp: peaked_cap(M, hp, y0=-13.2, tilt=(1.0, -2.0)),
                    lambda M, hp: hair_short(M, hp, hairline=-13.0, front_z=8.0, burn_y=4.5, thick=1.2)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.22, v_top=4.0, lapel=False, collar_h=8.5, collar_r=(12.2, 13.8)),
            lambda M, t: tie_knot_collar(M),
            lambda M, t: tie(M, mat='tie', top=(0.2, 3.6, 10.2), bot=(0.5, 20.0, 13.2)),
            lambda M, t: band_on(M, t, 3.3, (6.0, 20.0), -40.0, 2.6, 'strap', y_range=(2.0, 60.0)),
            lambda M, t: surface_buttons(M, t, 2.6, [(1.8, 12.0), (1.8, 19.0), (2.0, 26.0)], r=1.1),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'moustache': 9, 'cap': 2, 'cap_band': 2, 'cord': 2, 'visor': 3, 'strap': 7, 'button': 7,
                           'tie': 5}),
        tone_passes=[pass_grain('coat', 0.05, seed=19), pass_grain('cap', 0.05, seed=20), pass_strands('hair'),
                     pass_strands('moustache', seed=21)],
        rgb_passes=[pass_badge((0.0, -16.6, 21.4), ['b.w.b', '.www.', 'b.w.b'],
                               {'w': '#e0bc66', 'b': '#a07c36'})],
        eye=dict(iris='#5a6670', iris_d='#353e46', sclera='#bdb5aa', sclera_d='#6c6a70', lash='#140c10',
                 pupil='#0b0a0e', catch='#f0e8d6'),
        brow=dict(col='#7a7874', col_l='#aaa69e'),
        mouth=dict(line='#3a1c20', corner='#5a2c2c', inner='#1c0c0e', teeth='#a89a86', tongue='#6c3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'droop', 'hooded'),
            extra=[ear_detail, wrinkles(forehead=3, under=True), eye_bags(), cheek_hollow],
            brows={**BROWS_STD, 'neutral': dict(arch=0.7, lift_inner=0.8)},
            brow_thick=((3, 2, 2), (2, 2, 1)), brow_pts=((1.6, -3.6, 17.2), (10.6, -2.4, 13.2)),
            mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.6)}),
        priority={'button': 3, 'cord': 2, 'visor': 1, 'moustache': 1, 'strap': 1},
    )


# =================================================================================== VORONOVA
def voronova():
    """Lidia Voronova (50s): a broad face with a square jaw and strong cheekbones, a short broad nose, level
    heavy brows, steady hooded eyes; grey-streaked hair under a dark karakul pirozhok, karakul shawl collar
    on a heavy dark-brown coat."""
    sk = SKIN_OLD
    styles = skin_styles(sk, RIM_V, lip_of(sk, warm=14))
    brown = ramp('#070504', '#110c0a', '#1c1410', '#291e17', '#38291f', '#4a3729', '#5f4735')
    styles.update(coat_style(brown, TH6, RIM_V))
    styles.update({
        'karakul': MatStyle(ramp('#050404', '#0e0b0a', '#1a1513', '#29211d', '#3a302a', '#4e4239', '#67584c'),
                            TH6, dither=0.05, rim='#8a8e9e'),
        'hair': MatStyle(ramp('#0e0d0e', '#262426', '#423f40', '#666262', '#8a8580', '#aca69e'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#a8b0bc', wrap=0.35),
        'shirt': MatStyle(ramp('#0c0b0c', '#1c1a1c', '#2e2b2c', '#45403f'), [0.08, 0.2, 0.45], rim=RIM_V),
    })
    head = dict(FEMALE)
    head.update(SOFT)
    head.update(brow_r=(11.4, 2.1, 2.7))
    head.update(skull_r=(16.0, 16.6, 20.0), mid_h=(12.4, 6.8, 11.6), cheek_c=(11.0, 2.8, 10.0), cheek_r=(5.0, 3.4, 4.2),
                malar_r=(5.0, 4.4, 4.0), jaw_angle=(10.8, 14.2, -4.0), jaw_r=(2.5, 2.9, 2.8), low_r=(11.6, 10.0, 12.4),
                chin_c=(0.0, 20.6, 11.6), chin_h=(4.2, 2.8, 3.0), chin_rad=2.6, chin_pt=(3.8, 21.6, 9.8),
                nose_root=(0.0, -1.0, 15.2), nose_tip=(0.0, 8.4, 18.8), tip_r=2.5, nose_r=(1.5, 2.1), ala_x=2.8,
                ala_r=(1.8, 1.6, 1.9), brow_r=(12.4, 2.6, 3.4), lip_up_r=(4.2, 1.25, 1.4), lip_lo_r=(3.7, 1.7, 1.6),
                neck_r=(7.4, 8.8),
                jaw_extra=[('ellipsoid', ((9.0, 17.6, 7.6), (4.2, 3.6, 3.6), 'skin', 2.2)),
                           ('ellipsoid', ((-9.0, 17.6, 7.6), (4.2, 3.6, 3.6), 'skin', 2.2))])
    return dict(
        id='voronova', city='veltrava', look=look_v(),
        head=head, zoom=1.12, smooth=2,

        head_pos=(55.0, 57.0, 0.0), yaw=28.0, pitch=3.0, roll=0.0,
        torso_pos=(55.0, 93.5, -0.5), torso_yaw=11.0, torso=dict(width=1.08, depth=1.12, slope=1.0),
        poses={'neutral': (0, 0, 0), 'concerned': (-1, 3, -1), 'determined': (1, -2, 0), 'surprised': (2, -3, 1)},
        head_items=[lambda M, hp: pirozhok(M, hp),
                    lambda M, hp: PC.hair_bun(M, hp, bun=(-1.0, 4.0, -21.5), bun_r=5.6, hairline=-13.8, thick=1.8,
                                              seed=53),
                    lambda M, hp: temple_wave(M, hp)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.26, v_top=4.0, lapel=False, collar=False),
            lambda M, t: fur_collar(M, y=-2.0, r=13.0),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'karakul': 2}),
        tone_passes=[pass_curls('karakul', seed=103, light=2, dark=1), pass_strands('hair', seed=22),
                     pass_grain('coat', 0.05, seed=23)],
        eye=dict(iris='#4e4a42', iris_d='#2e2b26', sclera='#c0b8ac', sclera_d='#6c6a70', lash='#120c0e',
                 pupil='#0a0908', catch='#f0e8d6'),
        brow=dict(col='#3c3836', col_l='#625c56'),
        mouth=dict(line='#42191d', corner='#5c2a2a', inner='#1a0a0b', teeth='#b6a896', tongue='#733033'),
        features=dict(
            eyes=FC.eye_shapes(_female_eyes(), 'hooded'),
            extra=[ear_detail, wrinkles(forehead=1, crow=True, naso=False, under=False)],
            brows={**BROWS_STD, 'neutral': dict(arch=0.15, lift_inner=-0.2),
                   'concerned': dict(lift_inner=1.6, lift_outer=-0.3, arch=0.2)},
            brow_thick=((2, 2, 1), (2, 1, 1)), brow_pts=((1.6, -4.3, 17.2), (10.6, -4.2, 13.4)),
            mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.3)}),
        priority={'karakul': 1},
    )


# =================================================================================== KESSLER
def kessler():
    """Gerhard Kessler (50s): a narrow ascetic face, a sharp aquiline nose, a pointed chin, thin lips, cool
    narrow eyes behind thin rimless glasses, straight thin brows; black homburg, charcoal overcoat, white
    shirt, dark tie.  A civil servant -- no badges, no pins."""
    sk = SKIN_PALAIS
    styles = skin_styles(sk, RIM_P, lip_of(sk, warm=-4))
    char = ramp('#050607', '#0b0c0f', '#131519', '#1c1f24', '#272a30', '#34383f', '#454950')
    styles.update(coat_style(char, TH6, RIM_P))
    felt = ramp('#040405', '#09090b', '#111114', '#1a1a1e', '#242429', '#303036', '#3e3e45', '#4e4e56')
    fth = [0.03, 0.08, 0.15, 0.25, 0.38, 0.55, 0.75]
    styles.update({
        'felt': MatStyle(felt, fth, dither=0.04, rim='#6a8494'),
        'brim': MatStyle(felt, fth, dither=0.0, rim='#6a8494'),
        'ribbon': MatStyle(ramp('#020203', '#060608', '#0c0c10', '#141418', '#1e1e24'), [0.06, 0.16, 0.32, 0.55],
                           rim='#4a5a66'),
        'shirt': MatStyle(ramp('#14161a', '#30343a', '#585c60', '#868884', '#b2b2aa', '#d6d4c8', '#ecebe0'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#a8c0c8'),
        'tie': MatStyle(ramp('#050508', '#0c0b12', '#15131c', '#201d28'), [0.08, 0.2, 0.45], rim=RIM_P),
        'hair': MatStyle(ramp('#0c0d10', '#25262b', '#45464b', '#6b6b6e', '#8f8e8c', '#b2aea7'),
                         [0.04, 0.10, 0.2, 0.36, 0.58], rim='#a8b8c4', wrap=0.35),
    })
    head = dict(skull_r=(15.8, 17.0, 20.6), mid_h=(11.0, 7.4, 11.6), fore_h=(11.4, 9.4, 12.0),
                cheek_c=(10.2, 2.8, 10.0), cheek_r=(4.0, 2.6, 3.6), malar_r=(3.2, 3.0, 2.8),
                jaw_angle=(10.2, 15.8, -4.2), jaw_r=(2.3, 2.7, 2.6), low_r=(10.6, 11.6, 12.2),
                chin_c=(0.0, 22.8, 11.6), chin_h=(3.2, 3.6, 3.0), chin_rad=2.2, chin_pt=(2.8, 24.0, 10.0),
                nose_root=(0.0, -1.6, 15.8), nose_tip=(0.0, 9.6, 20.6), tip_r=1.85, nose_r=(1.2, 1.5), ala_x=2.1,
                ala_r=(1.3, 1.3, 1.6), brow_r=(11.8, 2.4, 3.2), lip_up_r=(3.9, 0.85, 1.1), lip_lo_r=(3.3, 0.95, 1.1),
                neck_r=(7.6, 8.8),
                extra=[('ellipsoid', ((0.0, 3.6, 18.4), (1.25, 1.9, 1.15), 'skin', 0.9))])
    return dict(
        id='kessler', city='palais', look=look_p(),
        head=head, zoom=1.14,
        head_pos=(55.0, 54.0, 0.0), yaw=29.0, pitch=0.0, roll=0.0,
        torso_pos=(55.0, 90.0, -0.5), torso_yaw=13.0, torso=dict(width=0.96, depth=0.98, slope=1.3),
        poses={'neutral': (0, 0, 0), 'concerned': (-1, 3, -1), 'determined': (1, -2, 0), 'surprised': (2, -3, 1)},
        head_items=[lambda M, hp: homburg(M, hp),
                    lambda M, hp: hair_short(M, hp, hairline=-14.4, front_z=8.0, burn_y=1.5, thick=0.8)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.40, v_top=3.0, lapel=True, collar_h=8.0, collar_r=(12.0, 13.6)),
            lambda M, t: tie_knot_collar(M),
            lambda M, t: tie(M, mat='tie', top=(0.4, 4.0, 12.4), bot=(1.0, 24.0, 13.8)),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'felt': 2, 'ribbon': 2, 'brim': 3, 'tie': 5}),
        tone_passes=[pass_grain('felt', 0.06, seed=24), pass_grain('coat', 0.05, seed=25), pass_strands('hair')],
        rgb_passes=[glasses('round', rim='#6c747c', rim_hi='#d8dee2', glare='#d0dce0', lens_r=(3.6, 2.8))],
        eye=dict(iris='#5d7484', iris_d='#36444e', sclera='#c4bcb2', sclera_d='#6e6a74', lash='#120c10',
                 pupil='#0a0a0e', catch='#f2ead8'),
        brow=dict(col='#46464a', col_l='#6e6e70'),
        mouth=dict(line='#3a1a1e', corner='#55282a', inner='#1a0a0d', teeth='#b2a593', tongue='#6c3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'narrow'),
            extra=[ear_detail, wrinkles(forehead=1, crow=True, naso=True, under=False), cheek_hollow],
            brows={'neutral': dict(arch=0.1), 'concerned': dict(lift_inner=1.4, lift_outer=-0.2, arch=0.1),
                   'determined': dict(lift_inner=-1.6, arch=0.0, dy=0.5),
                   'surprised': dict(dy=-1.4, arch=0.8, lift_inner=0.3)},
            brow_thick=((2, 1, 1), (1, 1, 1)), brow_pts=((1.8, -4.0, 17.0), (10.0, -3.8, 13.4)), nostril='small',
            mouth={'neutral': dict(corner_drop=0.5), 'concerned': dict(corner_drop=0.9),
                   'determined': dict(corner_drop=0.7), 'surprised': dict(parted=1)},
        ),
        priority={'brim': 2, 'ribbon': 2, 'tie': 1},
    )


# =================================================================================== TYPIST
def typist():
    """Frau Brunner (40s, Swiss): a round friendly face, full cheeks, a small slightly upturned nose, a soft
    round chin, wide-open eyes with lifted arched brows; brown hair in a short set perm, a pencil behind the
    ear; oatmeal cardigan over a white blouse."""
    sk = SKIN_PALAIS
    styles = skin_styles(sk, RIM_P, lip_of(sk, warm=18))
    styles['cheek'] = MatStyle(lip_of(sk, warm=16), SKIN_TH, rim=RIM_P, outline=sk[0], wrap=0.18, lift=0.24, ao=0.75)
    oat = ramp('#0c0a07', '#1d1810', '#30281c', '#45392a', '#5c4d3a', '#76644c', '#917d60')
    styles.update({
        'cardigan': MatStyle(oat, TH6, dither=0.03, rim=RIM_P),
        'coat': MatStyle(oat, TH6, dither=0.03, rim=RIM_P),
        'coat_lapel': MatStyle(oat, TH6, rim=RIM_P),
        'shirt': MatStyle(ramp('#14161a', '#30343a', '#585c60', '#868884', '#b2b2aa', '#d6d4c8', '#ecebe0'),
                          [0.05, 0.12, 0.24, 0.40, 0.58, 0.80], rim='#a8c0c8'),
        'hair': MatStyle(ramp('#0a0605', '#1a100c', '#2c1c14', '#40291c', '#583a28', '#704c34', '#8a6244'),
                         [0.04, 0.10, 0.2, 0.34, 0.52, 0.74], rim='#8aa0a8', wrap=0.25),
        'button': MatStyle(ramp('#0e0a08', '#2a1f18', '#4f3c2c', '#7a6046'), [0.08, 0.25, 0.5], rim=RIM_P),
    })
    head = dict(FEMALE)
    head.update(SOFT)
    head.update(skull_r=(15.8, 16.2, 19.8), mid_h=(11.8, 6.4, 11.4), cheek_c=(10.4, 3.8, 10.4), cheek_r=(5.0, 3.6, 4.4),
                malar_r=(5.2, 4.6, 4.2), jaw_angle=(10.4, 13.6, -3.8), low_r=(11.8, 9.6, 12.6),
                chin_c=(0.0, 20.2, 11.6), chin_h=(4.0, 2.7, 3.0), chin_rad=2.8, chin_pt=(3.6, 21.0, 10.0),
                nose_root=(0.0, -0.6, 15.2), nose_tip=(0.0, 7.8, 18.6), tip_r=2.25, nose_r=(1.2, 1.7), ala_x=2.2,
                ala_y=9.0, ala_r=(1.5, 1.4, 1.7), eye_x=6.6, mouth_y=13.8, lip_up=(0.0, 13.1, 16.2),
                lip_up_r=(4.0, 1.3, 1.5), lip_lo=(0.0, 15.2, 15.8), lip_lo_r=(3.5, 1.7, 1.6), brow_r=(11.4, 2.0, 2.8),
                extra=PC.blush(c=(9.0, 6.6, 11.2)),
                jaw_extra=[('ellipsoid', ((0.0, 24.6, 7.6), (6.0, 2.4, 4.4), 'skin', 2.6))])
    return dict(
        id='typist', city='palais', look=look_p(),
        head=head, zoom=1.16, smooth=2,
        head_pos=(55.0, 57.0, 0.0), yaw=30.0, pitch=2.0, roll=2.0,
        torso_pos=(55.5, 92.0, -0.5), torso_yaw=12.0, torso=dict(width=0.96, depth=1.06, slope=1.4),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 3, -2), 'determined': (1, -1, 1), 'surprised': (2, -3, 2)},
        head_items=[lambda M, hp: hair_curls(M, hp)],
        torso_items=[
            lambda M, t: layered_front(M, t, outer='cardigan', mid='shirt', inner='shirt', v_outer=(0.40, 4.0),
                                       v_mid=(0.0, 60.0), lapel=False, collar_h=0,
                                       buttons=[(0.0, 16.0), (0.0, 23.0), (0.0, 30.0)]),
            lambda M, t: tie_knot_collar(M, mat='shirt', y=1.0, z=8.2),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck', 'cheek'),
        groups=groups_std({'cheek': 0, 'cardigan': 4, 'button': 5}),
        tone_passes=[pass_curls('hair', seed=105, light=2, dark=1), pass_knit('cardigan', ribs=40)],
        rgb_passes=[pencil_ear],
        eye=dict(iris='#5a4630', iris_d='#34281c', sclera='#cbc2b2', sclera_d='#6f6e72', lash='#120a0c',
                 pupil='#0a0808', catch='#f2e9d6'),
        brow=dict(col='#2e1c16', col_l='#4c3428'),
        mouth=dict(line='#46191d', corner='#5e2a2a', inner='#1a0a0b', teeth='#bcae9c', tongue='#733033'),
        features=dict(
            eyes=FC.eye_shapes(_female_eyes(), 'round'),
            extra=[ear_detail, wrinkles(forehead=0, crow=True, naso=False, under=False)],
            brows={'neutral': dict(arch=1.3, lift_inner=0.3), 'concerned': dict(lift_inner=2.4, lift_outer=-0.2, arch=0.8),
                   'determined': dict(lift_inner=-1.2, arch=0.6, dy=0.4),
                   'surprised': dict(dy=-2.0, arch=1.7, lift_inner=0.5)},
            brow_thick=((1, 1, 1), (1, 1, 1)), brow_pts=((1.9, -4.6, 17.0), (10.2, -4.6, 13.2)),
            mouth={'neutral': dict(smile=0.4), 'concerned': dict(corner_drop=0.8),
                   'determined': dict(corner_drop=0.2), 'surprised': dict(parted=2)},
        ),
        priority={'button': 2},
    )


# =================================================================================== JOURNALIST
def journalist():
    """Nils Ekdahl (40s): a long Nordic face, a strong straight nose, a long jaw with a cleft chin, light
    brows that almost vanish, observant eyes with a slight squint; fair tousled hair, blue knitted scarf,
    brown tweed overcoat, the camera strap."""
    sk = SKIN_PALAIS
    styles = skin_styles(sk, RIM_P, lip_of(sk))
    tweed = ramp('#0a0806', '#16120d', '#241d15', '#342a1e', '#463928', '#5a4a34', '#6f5c42')
    styles.update(coat_style(tweed, TH6, RIM_P, dither=0.06))
    styles.update({
        'scarf': MatStyle(ramp('#04070b', '#0a1119', '#111c29', '#1a2a3c', '#243a52', '#304c68', '#3e5e7e'),
                          TH6, dither=0.03, rim='#8aa4b4'),
        'shirt': MatStyle(ramp('#14161a', '#30343a', '#585c60', '#868884', '#b2b2aa'), [0.05, 0.12, 0.24, 0.40],
                          rim='#a8c0c8'),
        'strap': MatStyle(ramp('#0a0607', '#1b0f0c', '#2e1a12', '#472918', '#633a22'), [0.05, 0.12, 0.24, 0.40],
                          rim='#6a6a76'),
        'hair': MatStyle(ramp('#1a140a', '#3a2c16', '#5c4626', '#80663c', '#a08652', '#bea66c', '#d8c48a'),
                         [0.04, 0.09, 0.17, 0.29, 0.45, 0.66], rim='#d0d8d4', wrap=0.35, lift=0.25),
    })
    head = dict(skull_r=(15.8, 17.4, 20.4), mid_h=(11.6, 7.8, 11.6), fore_h=(11.8, 9.6, 12.0),
                cheek_c=(10.6, 3.0, 9.8), cheek_r=(4.4, 2.8, 3.8), malar_r=(3.6, 3.2, 3.0),
                jaw_angle=(11.2, 17.0, -4.0), low_r=(11.6, 12.4, 12.8), chin_c=(0.0, 23.6, 12.2),
                chin_h=(4.6, 3.6, 3.4), chin_pt=(4.0, 24.8, 10.4),
                nose_root=(0.0, -1.6, 15.8), nose_tip=(0.0, 10.0, 20.2), tip_r=2.35, nose_r=(1.5, 2.0), ala_x=2.4,
                ala_y=11.0, ala_r=(1.6, 1.5, 1.9), mouth_y=15.6, lip_up=(0.0, 14.8, 16.6), lip_up_r=(4.4, 1.1, 1.4),
                lip_lo=(0.0, 17.0, 16.2), lip_lo_r=(3.8, 1.3, 1.5), brow_r=(12.4, 2.8, 3.4), neck_r=(8.2, 9.6),
                extra=[('sub', ((0.0, 24.4, 15.4), (0.7, 1.6, 0.8), 0.5))])
    return dict(
        id='journalist', city='palais', look=look_p(),
        head=head, zoom=1.10,
        head_pos=(55.0, 54.0, 0.0), yaw=27.0, pitch=2.0, roll=-2.0,
        torso_pos=(55.0, 92.0, -0.5), torso_yaw=13.0, torso=dict(width=1.04, depth=1.04, slope=1.1),
        poses={'neutral': (0, 0, 0), 'concerned': (-2, 3, -2), 'determined': (1, -1, 1), 'surprised': (3, -3, 2)},
        head_items=[lambda M, hp: hair_tousled(M, hp)],
        torso_items=[
            lambda M, t: coat_layers(M, t, v_open=0.40, v_top=3.0, lapel=True, collar_h=8.0, collar_r=(12.6, 14.2)),
            lambda M, t: scarf_wrap(M, y=-5.6, r=10.6, tube=4.2, ends='drape', seed=11),
            lambda M, t: band_on(M, t, 3.4, (7.0, 18.0), -46.0, 2.4, 'strap', y_range=(4.0, 60.0)),
        ],
        styles=styles, skin=('skin', 'lip', 'ear', 'neck'),
        groups=groups_std({'scarf': 6, 'strap': 7}),
        tone_passes=[pass_strands('hair', seed=26), pass_knit('scarf', ribs=26), pass_grain('coat', 0.12, seed=27)],
        eye=dict(iris='#5a7488', iris_d='#344452', sclera='#c6beb4', sclera_d='#72707a', lash='#2a1e18',
                 pupil='#0a0a0e', catch='#f2ead8'),
        brow=dict(col='#6e5a3a', col_l='#9a8458'),
        mouth=dict(line='#3a1a1e', corner='#55282a', inner='#1a0a0d', teeth='#b8ab9a', tongue='#6c3034'),
        features=dict(
            eyes=FC.eye_shapes(FC.EYES, 'narrow', 'droop'),
            extra=[ear_detail, stubble(density=0.35), wrinkles(forehead=2, under=False), chin_cleft],
            brows={**BROWS_STD, 'neutral': dict(arch=0.4, lift_inner=0.5)},
            brow_thick=((2, 2, 1), (1, 1, 1)), brow_pts=((1.6, -4.2, 17.2), (10.8, -3.6, 13.4)),
            mouth={**MOUTH_STD, 'neutral': dict(corner_drop=0.0, smile=0.3)}),
        priority={'strap': 1, 'scarf': 1},
    )


PORTRAITS_C3 = {
    'elena': elena, 'border_officer': border_officer, 'conductor': conductor, 'voronova': voronova,
    'kessler': kessler, 'typist': typist, 'journalist': journalist,
}
PC.CAST.update(PORTRAITS_C3)
