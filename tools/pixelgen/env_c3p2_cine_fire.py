"""env_c3p2_cine_fire -- art of LS_C3_Fire and LS_C3_Escape (owner: cinematics stream, round 8; C3P2_DESIGN §2.9).

The commission's registry in the souterrain of the palais' east wing (the former Kurhaus coal cellar, brick vaults,
oak card cabinets with brass label holders, the green-shaded lamp over the sorting table; §5.1).

LS_C3_Fire   f1 the sorting table under the green lamp, Konrad from behind (pose 0/1: he looks up)
             f2 the Magazin aisle in one-point perspective: the C-17 boxes catch, a figure in a long coat and a
                porter's cap slips out through the lit service door at the end (a silhouette, no face)
             f3 the iron-clad ramp door from inside: the cold gap light, a shadow passes, the bolt slides home
             f4 the same hall as f1, burning: fire along the cabinets, smoke under the vault, Alexei at the table
LS_C3_Escape e1 up the coal chute toward the square of snow light, the file pushed ahead
             e2 the yard: the 1909 hatch flips open, Konrad crawls out with the file, smoke after him
             e3 a: Alexei's hand out of the smoke, Konrad's hand takes it; b: both on their backs in the snow
             e4 the east wing from the lane: the souterrain windows burst orange one after another
Runtime: scenes/cinematics/ch3_fire/ch3_fire.gd, ch3_escape/ch3_escape.gd (anchors in layout.json fire/escape).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, GREEN, PAPER, FIRE, RED, BRASS,
                               SMOKE, K_COAT, A_COAT, A_FUR, K_HAT, grid, poly, ell, box, hexrgb)
import pg

LF = Q.LAYOUT.setdefault('fire', {})
LE = Q.LAYOUT.setdefault('escape', {})

BRICK = ['#0A0706', '#140D0A', '#1E140F', '#2A1C15', '#3A271C', '#4E3424', '#66442E']
SOOT = ['#050404', '#0B0908', '#13100E', '#1C1814', '#27211C', '#342C25']
EMBERGLOW = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']


def _bricks(p, m, ramp, base, light=None, course=7, brick=16, seed=0, gain=2.4, mortar=-0.9):
    """Brickwork on mask m: running bond, value noise per brick, darker mortar joints."""
    yy, xx = p.yy, p.xx
    row = np.floor(yy / course)
    off = np.where(np.mod(row, 2) == 0, 0, brick / 2)
    col = np.floor((xx + off) / brick)
    hsh = np.mod(np.sin(row * 12.9898 + col * 78.233 + seed) * 43758.5453, 1.0)
    joint = (np.mod(yy, course) < 1) | (np.mod(xx + off, brick) < 1)
    lt = 0.0 if light is None else light
    t = base + (hsh - 0.5) * 0.9 + lt * gain
    p.put(m, ramp, t[m] if not np.isscalar(t) else t)
    j = m & joint
    p.put(j, ramp, (t + mortar)[j])


# =========================================================================================== LS_C3_Fire
LAMP_G = (300, 104)                   # the green shade (centre of its rim)
TABLE_TOP = (236, 268)                # far / near edge of the sorting table (f1 / f4)


def lamp_cone():
    """Additive green light of the lamp: the cone and the pool on the table (modulated at runtime)."""
    a = np.zeros((VH, VW, 3), np.float32)
    yy, xx = grid()
    lx, ly = LAMP_G
    u = np.clip((yy - ly) / (TABLE_TOP[1] - ly), 0, 1)
    half = 30 + u * 150
    cone = (yy > ly) & (np.abs(xx - lx) < half)
    g = np.clip(1 - np.abs(xx - lx) / np.maximum(half, 1), 0, 1) ** 1.2 * (1 - u * 0.5)
    a += (cone * g)[..., None] * np.array([10, 26, 16], np.float32)
    Q.add_glow(a, lx, TABLE_TOP[0] + 14, 190, 26, (26, 56, 34), 1.4)
    Q.add_glow(a, lx, ly + 2, 40, 10, (40, 70, 46), 1.2)
    return K.soft_quant(a, 6.0)


def fire_glow(cx, cy, rx, ry, k=1.0):
    return Q.glow_sprite(VW, VH, [(cx, cy, rx, ry, (110 * k, 52 * k, 16 * k), 1.3),
                                  (cx, cy, rx * 0.45, ry * 0.5, (90 * k, 40 * k, 10 * k), 1.2)], 6.0)


# ------------------------------------------------------------------------------------------- f2 aisle
F2 = {'vpx': 320.0, 'vpy': 150.0, 'f': 300.0, 'eye': 1.6, 'half': 1.2, 'far': 9.0, 'h': 2.6}


def _f2p(X, Y, Z):
    return (F2['vpx'] + F2['f'] * X / Z, F2['vpy'] - F2['f'] * (Y - F2['eye']) / Z)


_DOOR_FIG = None


def f2_door():
    """4 frames of the service door (sprite over the bg door): the figure in the lit doorway, half out, the
    empty lit doorway, closed.  Long coat, porter's cap, seen from behind - never a face."""
    x0, y0, x1, y1 = LF.get('f2_door', [304, 115, 336, 197])
    w, h = x1 - x0 + 8, y1 - y0 + 4
    R = C.ramps(L=LAMP, N=NIGHT, I=IRON)
    frames = []
    for i in range(4):
        p = C.Paint(w, h, R, 'f2door', ox=x0 - 4, oy=y0 - 2)
        yy, xx = p.yy, p.xx
        dm = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
        if i < 3:
            p.put(dm, 'L', 3.6 - (yy[dm] - y0) / (y1 - y0) * 1.2)           # the lit stairwell
            p.put(dm & (yy > y1 - 14) & (np.mod(yy, 4) < 1), 'L', 2.2)       # steps
            p.put(dm & (np.mod(xx, 5) < 1) & (i == 2), 'I', 1.6)
        else:
            p.put(dm, 'I', 1.2)
            p.put(dm & (np.mod(xx, 5) < 1), 'I', 2.4)
        if i < 2 and _DOOR_FIG is not None:
            pass
        elif i < 2:
            cx = (x0 + x1) / 2 + (0 if i == 0 else 9)
            hgt = (y1 - y0) * 0.86
            top = y1 - hgt
            sil = p.poly([(cx - 5.5, top + 9), (cx + 5.5, top + 9), (cx + 8, y1), (cx - 8, y1)])
            sil |= p.ell(cx, top + 5.5, 3.6, 4.2)
            sil |= p.box(cx - 4.5, top + 1, cx + 4.5, top + 4)                  # porter's cap crown
            sil |= p.box(cx - 2, top + 3, cx + 6.5, top + 5)                    # its peak (he turns away)
            sil |= p.poly([(cx - 6, top + 10), (cx - 9, top + 26), (cx - 6, top + 27)])   # arm
            if i == 1:
                sil &= xx >= x0 + (x1 - x0) * 0.55                               # half through the door
            p.put(sil & dm, 'N', 0.6)
            p.put(sil & dm & C.rim(sil, 1, 0), 'L', 1.6)
        p.resolve(band=2.0)
        fr = p.L.c.copy()
        if i < 2 and _DOOR_FIG is not None:
            fig = _DOOR_FIG(i, (x0, y0, x1, y1), (4, 2, 4, 2))
            sel = fig[..., 3] > 0
            fr[sel] = fig[sel]
        frames.append(fr)
    LF['f2_door_at'] = [x0 - 4, y0 - 2]
    return Q.sheet(frames)


# ------------------------------------------------------------------------------------------- f3 ramp door
F3_GAP_X = 470                        # x of the vertical gap (door edge / frame)
F3_FLOOR = 292


# ------------------------------------------------------------------------------------------- f4 Alexei
def f4_alexei():
    """Alexei from behind at the near side of the table, the burning cabinets beyond: almost black against the
    fire, an orange rim on the ushanka (crown, ear flaps, back flap), the fur collar, broad quilted shoulders and
    the satchel strap; 2 frames (breath / the head turned a little toward the fire's front)."""
    w, h = 190, 230
    x0, y0 = 54, 112
    R = C.ramps(A=['#020504', '#060B09', '#0B1410', '#122019'], U=['#060506', '#0E0C0C', '#181412', '#241E1A'],
                F=EMBERGLOW, T=['#0A0604', '#160E08', '#24160C'])
    frames = []
    for fr in range(2):
        p = C.Paint(w, h, R, 'f4_alexei', ox=x0, oy=y0)
        b = 0 if fr == 0 else -1
        t = 0 if fr == 0 else 3
        hx, hy = x0 + 96 + t, y0 + 52 + b
        crown = p.ell(hx, hy - 12, 27, 18)
        hat = crown | p.rr(hx - 30, hy - 14, hx + 30, hy + 24, 9)
        collar = p.ell(hx - t, hy + 28, 34, 12)
        coat = p.poly([(hx - 34 - t, hy + 22), (hx - 66 - t, hy + 44 + b), (hx - 80 - t, hy + 92), (hx - 86 - t, y0 + h),
                       (hx + 86 - t, y0 + h), (hx + 80 - t, hy + 92), (hx + 66 - t, hy + 44 + b), (hx + 34 - t, hy + 22)])
        sil = hat | collar | coat
        p.put(coat, 'A', 1.0)
        quilt = coat & (np.mod(p.yy + np.abs(p.xx - hx) * 0.12, 12) < 1.0)
        p.put(quilt, 'A', 0.2)
        p.put(collar, 'U', 1.2 + Q.noise(w, h, 3, 961)[collar] * 1.0)
        p.put(hat, 'U', 1.0 + Q.noise(w, h, 2.5, 962)[hat] * 1.2)
        flap = hat & (np.abs(p.xx - hx) > 16) & (p.yy > hy - 2)
        p.put(flap, 'U', 0.6)                                                       # the ear flaps, a shade darker
        strap = p.line([(hx - 44 - t, hy + 34), (hx + 58 - t, hy + 170)], r=3.2) & coat
        p.put(strap, 'T', 1.4)
        # fire ahead: a hot rim on the outer boundary only (top strongest, flanks weaker)
        outer = sil & ~C.shift(sil, 0, -1)
        for k in (2, 3):
            outer |= sil & ~C.shift(sil, 0, -k) & (Q.noise(w, h, 2, 964 + k) > 0.35)
        p.put(outer, 'F', 3.0 + (outer & hat)[outer] * 1.6)
        for sx in (-1, 1):
            side = sil & ~C.shift(sil, sx, 0) & ~outer
            p.put(side, 'F', 2.0)
            side2 = sil & ~C.shift(sil, sx * 2, 0) & ~outer & ~side & (p.yy < hy + 80)
            p.put(side2, 'F', 1.0)
        fuzz = hat & ~C.shift(hat, 0, -3) & (Q.noise(w, h, 1.5, 963) > 0.5)
        p.put(fuzz, 'F', 4.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LF['f4_alexei'] = [x0, y0]
    return Q.sheet(frames)


# =========================================================================================== LS_C3_Escape
CH = {'vpx': 320.0, 'vpy': 110.0, 'f': 280.0, 'half': 0.42}
CH_TOP = 5.0                          # distance of the hatch (m)


def e1_file():
    """Konrad's sooty hands shoving the tied file up the slide (2 frames: grip, shove); 220 x 130, bottom-anchored."""
    w, h = 220, 130
    R = C.ramps(S=['#1E1414', '#3A2624', '#5A3C34', '#7A5446', '#9A6E58', '#B88A6C'], P=PAPER,
                C=['#1C140C', '#3A2A18', '#5E4426', '#806038', '#9E7C4C'], K=K_COAT, T=['#2A2418', '#5A4E36', '#8A7A58'],
                L=['#3A4859', '#687789', '#A1AAB7'])
    frames = []
    for fr in range(2):
        p = C.Paint(w, h, R, 'e1_file')
        yy, xx = p.yy, p.xx
        b = 0 if fr == 0 else -8
        folder = p.poly([(44, 46 + b), (176, 46 + b), (188, 88 + b), (32, 88 + b)])
        p.put(folder, 'C', 1.2 + (88 - yy[folder]) / 42.0 * 2.2)
        pages = p.poly([(50, 36 + b), (170, 36 + b), (176, 47 + b), (44, 47 + b)])
        p.put(pages, 'P', 3.0 + np.mod(yy[pages], 2) * 0.9)
        string = (p.line([(110, 36 + b), (112, 88 + b)], r=0.9) | p.line([(40, 66 + b), (184, 66 + b)], r=0.8)) & (folder | pages)
        p.put(string, 'T', 1.6)
        p.put((folder | pages) & C.rim(folder | pages, 0, -1, 2), 'L', 2.0)         # snow light from above
        for sx in (-1, 1):
            hx = 110 + sx * 62
            palm = p.ell(hx, 94 + b, 19, 14)
            fing = p.line([(hx - 12, 88 + b), (hx - 10 - 3 * sx, 72 + b)], r=4.2) | p.line([(hx - 3, 86 + b), (hx - sx, 70 + b)], r=4.2) |                 p.line([(hx + 6, 86 + b), (hx + 6 + 2 * sx, 72 + b)], r=4.0) | p.line([(hx + 14, 90 + b), (hx + 15 + 3 * sx, 78 + b)], r=3.6)
            hand = palm | fing
            p.put(hand, 'S', 1.4 + np.clip((96 - yy[hand]) / 20.0, 0, 1) * 2.4)
            p.put(hand & C.rim(hand, 0, -1), 'S', 4.4)
            sleeve = p.poly([(hx - 22, 104 + b), (hx + 22, 102 + b), (hx + 30 + sx * 8, h), (hx - 30 + sx * 8, h)])
            p.put(sleeve, 'K', 1.0)
            p.put(sleeve & C.rim(sleeve, 0, -1, 2), 'L', 1.0)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


# ------------------------------------------------------------------------------------------- e2 yard
WALL_FOOT = 214
HATCH = dict(back=(250, 390, 218), front=(238, 402, 246), outer_back=(236, 404, 213), outer_front=(220, 420, 253))
YARD_LAMP = (486, 64)
YARD_R = dict(W=['#05070B', '#0A0D13', '#10151D', '#171E28', '#202935', '#2B3644', '#394656'], S=SNOW, L=LAMP, I=IRON,
              N=NIGHT, F=EMBERGLOW, X=SOOT)


KR = dict(K=K_COAT, A=['#020504', '#071009', '#0E1A14', '#16261D', '#20342A', '#2E4636'], U=A_FUR, H=K_HAT,
          Z=['#140C0C', '#2A1A18', '#46302A', '#6A4A3C', '#8A644E'], P=PAPER, F=EMBERGLOW, L=LAMP, S=SNOW)


def _shade_fig(p, sil, coat, parts, warm_dir=(0.8, -0.6), hot_dir=(-0.3, 1.0)):
    """Soot-dark figure: base tone, lamp rim (warm, from the upper right), fire rim from below (the mouth)."""
    p.put(sil, coat, 0.8)
    for nm, m in parts:
        if nm == 'hat':
            p.put(m, 'H' if coat == 'K' else 'U', 1.0)
        elif nm == 'skin':
            p.put(m, 'Z', 1.6)
        elif nm == 'file':
            p.put(m, 'P', 2.4)
            p.put(m & C.rim(m, 0, -1), 'P', 4.0)
    e = C.edge_light(sil, warm_dir, width=3.5, soft=1)
    sel = sil & (e > 0.3)
    p.put(sel, 'L', 1.2 + e[sel] * 2.6)
    e2 = C.edge_light(sil, hot_dir, width=2.5, soft=1)
    sel2 = sil & (e2 > 0.42) & ~sel
    p.put(sel2, 'F', 2.0 + e2[sel2] * 2.4)


def e2_konrad():
    """4 frames: hat, head and shoulders out of the mouth (the file thrust onto the snow), out to the waist with a
    knee on the rim, then on hands and knees in the snow beside the hatch (two steps).  Drawn at scale k about
    the mouth so he fills the opening (a man's shoulders ~ two thirds of the hatch width)."""
    x0, y0, w, h = 190, 70, 420, 220
    R = C.ramps(**KR)
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    mx = (b0 + b1) / 2
    k = 1.55

    def P(pts, ax, ay):
        return [(ax + (x - ax) * k, ay + (y - ay) * k) for (x, y) in pts]

    frames = []
    for fr in range(4):
        p = C.Paint(w, h, R, 'e2k', ox=x0, oy=y0)
        parts = []
        if fr in (0, 1):
            up = 0 if fr == 0 else 16
            cx = mx - 4 + (6 if fr == 1 else 0)
            ax, ay = cx, fy
            parts.append(('body', p.poly(P([(cx - 26, fy - 2), (cx + 26, fy - 2), (cx + 24, fy - 22 - up), (cx + 10, fy - 30 - up),
                                             (cx - 12, fy - 30 - up), (cx - 24, fy - 20 - up)], ax, ay))))
            parts.append(('collar', p.poly(P([(cx - 12, fy - 28 - up), (cx + 12, fy - 28 - up), (cx + 8, fy - 36 - up),
                                               (cx - 8, fy - 36 - up)], ax, ay))))
            hx, hy = ax + 3 * k, ay - (40 + up) * k
            parts.append(('skin', p.ell(hx, hy, 7.5 * k, 8.5 * k)))
            parts.append(('hat', p.ell(hx, hy - 6 * k, 14 * k, 3.6 * k) | p.rr(hx - 9 * k, hy - 17 * k, hx + 9 * k, hy - 5 * k, 3 * k)))
            parts.append(('arm', p.line(P([(cx + 18, fy - 24 - up), (cx + 38, fy - 12 - up * 0.4), (cx + 54, fy + 2)], ax, ay), r=4.6 * k)))
            parts.append(('file', p.poly(P([(cx + 46, fy - 5), (cx + 76, fy - 8), (cx + 79, fy + 4), (cx + 48, fy + 6)], ax, ay))))
            if fr == 1:
                parts.append(('leg', p.line(P([(cx - 18, fy - 6), (cx - 30, fy + 2), (cx - 27, fy + 6)], ax, ay), r=5.6 * k)))
        else:
            s_ = 0 if fr == 2 else 5
            gx = b1 + 50 + (0 if fr == 2 else 14)
            gy = fy + 8
            ax, ay = gx, gy
            parts.append(('body', p.poly(P([(gx - 36, gy - 28), (gx + 20, gy - 36), (gx + 27, gy - 21), (gx - 33, gy - 13)], ax, ay))))
            parts.append(('skirt', p.poly(P([(gx - 38, gy - 26), (gx - 24, gy - 28), (gx - 20, gy - 8), (gx - 42, gy - 6)], ax, ay))))
            parts.append(('collar', p.ell(gx + 22 * k, gy - 33 * k, 9 * k, 6 * k)))
            hx, hy = gx + 33 * k, gy - 33 * k
            parts.append(('skin', p.ell(hx, hy, 7 * k, 7.5 * k)))
            parts.append(('hat', p.ell(hx + 1 * k, hy - 5.5 * k, 12 * k, 3.4 * k) | p.rr(hx - 7 * k, hy - 15 * k, hx + 9 * k, hy - 5 * k, 3 * k)))
            parts.append(('arm', p.line(P([(gx + 18, gy - 30), (gx + 24 + s_, gy - 14), (gx + 27 + s_, gy)], ax, ay), r=3.8 * k)))
            parts.append(('arm2', p.line(P([(gx + 7, gy - 28), (gx + 11 - s_, gy - 12), (gx + 10 - s_, gy)], ax, ay), r=3.4 * k)))
            parts.append(('leg', p.line(P([(gx - 30, gy - 16), (gx - 20 + s_, gy - 2), (gx - 44 + s_, gy)], ax, ay), r=5.4 * k)))
            parts.append(('leg2', p.line(P([(gx - 33, gy - 18), (gx - 28 - s_, gy - 1), (gx - 52 - s_, gy)], ax, ay), r=5.0 * k)))
            parts.append(('file', p.poly(P([(gx - 6, gy - 33), (gx + 18, gy - 38), (gx + 20, gy - 30), (gx - 4, gy - 25)], ax, ay))))
        sil = np.zeros((h, w), bool)
        for _, m in parts:
            sil |= m
        _shade_fig(p, sil, 'K', parts)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LE['e2_konrad'] = [x0, y0]
    return Q.sheet(frames)


def e3a_hands():
    """0 Alexei's hand rises out of the smoke, 1 it reaches (fingers open), 2 Konrad's hand from above takes it,
    3 both a little higher: he pulls.  Round 9: sculpted and lit by the portrait pipeline
    (env_c3p2_cine_hands.e3a_frame -- the quilted sleeve, the sooty hands, Konrad's navy sleeve and shirt cuff)."""
    import env_c3p2_cine_hands as H
    # round 11 (figures stream): E3A_FRAMES frames -- Konrad's hand reaches in, closes, the pull in three steps
    frames = [H.e3a_frame(fr) for fr in range(getattr(H, 'E3A_FRAMES', 4))]
    LE['e3_hands'] = list(H.E3A_ORIGIN)
    return Q.sheet(frames)


E3B_SNOW = 214


def e3b_men():
    """Both on their backs in the snow, heads toward each other near the middle (Konrad left, his hat beside him,
    Alexei right in the ushanka), one knee up, an arm flung out; the yard lamp from the upper right; 2 frames
    (chests heaving).  Round 9: the men are sculpted by the portrait pipeline (env_c3p2_cine_hands.lying_men);
    the tied file lies in the snow between them (painted here)."""
    import env_c3p2_cine_hands as H
    x0, y0 = H.E3B_ORIGIN
    w, h = H.E3B_SIZE
    R = C.ramps(**KR)
    frames = []
    for fr in range(2):
        img = H.lying_men(fr).copy()
        p = C.Paint(w, h, R, 'e3bm', ox=x0, oy=y0)
        fl = p.poly([(318, 298), (352, 295), (354, 304), (320, 306)])           # the file, thrown into the snow
        p.put(fl, 'P', 2.6)
        p.put(fl & C.rim(fl, 0, -1), 'P', 4.0)
        p.resolve(band=2.0)
        lay = p.L.c
        m = lay[..., 3] > 0
        img[m] = lay[m]
        frames.append(img)
    LE['e3b_men'] = [x0, y0]
    LE['e3b_breath'] = H.E3B_BREATH
    return Q.sheet(frames)


# =========================================================================================== build
def _preview_fire():
    LF['preview'] = [
        {'id': 'f1', 'layers': [['fire/f1_bg.png', [0, 0]], ['fire/lamp_cone.png', [0, 0], 'add'],
                                ['fire/f1_konrad.png', LF['f1_konrad'], 'over', 2, 1]]},
        {'id': 'f2', 'layers': [['fire/f2_bg.png', [0, 0]], ['fire/f2_glow.png', [0, 0], 'add'],
                                ['fire/f2_door.png', LF['f2_door_at'], 'over', 4, 0]] +
            [['fire/f2_fire_m.png', [int(x) - 24, int(y) - 68], 'over', 8, i] for i, (x, y) in enumerate(LF['f2_fire'][:4])]},
        {'id': 'f3', 'layers': [['fire/f3_bg.png', [0, 0]], ['fire/f3_warm.png', [0, 0], 'add']]},
        {'id': 'f4', 'layers': [['fire/f4_bg.png', [0, 0]], ['fire/f4_lit.png', [0, 0], 'add']] +
            [[LF['f4_kinds'][b][0], [int(x) - LF['f4_kinds'][b][1] // 2, int(y) - LF['f4_kinds'][b][2]],
              'over', 8, (i * 3) % 8] for i, (x, y, b) in enumerate(LF['f4_fire'])] +
            [['fire/f4_table.png', LF['f4_table_at']], ['fire/f4_alexei.png', LF['f4_alexei'], 'over', 2, 0]]},
    ]


def build_fire(w):
    import env_c3p2_cine_registry as RG
    import env_c3p2_cine_life as LFE
    w('fire/f1_bg.png', RG.hall('night'))
    w('fire/lamp_cone.png', lamp_cone())
    import env_c3p2_cine_figs as F
    w('fire/f1_konrad.png', F.reg_konrad_sheet())
    LF['f1_konrad'] = list(F.REG_K_AT)
    w('fire/f2_bg.png', RG.f2_bg())
    global _DOOR_FIG
    _DOOR_FIG = getattr(F, 'doorway_figure', None)
    w('fire/f2_door.png', f2_door())
    w('fire/f2_glow.png', RG.f2_fire_light())
    # round 11: fire that reads as fire (bright cores, no dark rim) and soft smoke (no dithered blotches)
    w('fire/f2_fire_s.png', LFE.fire_sheet(8, 26, 36, 1871, tongues=2, width=(0.2, 0.3), length=(0.6, 1.0)))
    w('fire/f2_fire_m.png', LFE.fire_sheet(8, 48, 70, 1872, tongues=3, width=(0.15, 0.26), length=(0.5, 1.0),
                                           lean=-0.05))
    w('fire/f2_fire_l.png', LFE.fire_sheet(8, 60, 104, 1873, tongues=4, width=(0.13, 0.22), length=(0.45, 1.0),
                                           lean=-0.06))
    w('fire/f3_bg.png', RG.f3_bg())
    w('fire/f3_warm.png', Q.glow_sprite(VW, VH, [(300, 360, 360, 200, (70, 30, 10), 1.3)], 6.0))
    w('fire/f4_bg.png', RG.hall('fire'))
    w('fire/f4_lit.png', RG.f4_lit())
    w('fire/f4_table.png', RG.f4_table())
    w('fire/fire_band.png', RG.fire_band())
    w('fire/smoke_hot.png', LFE.soft_puff_sheet(8, 112, 84, LFE.SMOKE_FIRE, 1023, grow=(0.26, 0.5), light=(0.1, 0.95),
                                                thin=0.45, drift=0.04, alpha=0.95))
    w('fire/paper.png', LFE.paper_sheet())
    w('fire/f4_glow.png', Q.glow_sprite(VW, VH, [(420, 200, 330, 140, (54, 22, 6), 1.4),
                                                 (160, 210, 200, 110, (36, 14, 4), 1.4)], 3.0))
    fa = getattr(F, 'fire_alexei', None)
    w('fire/f4_alexei.png', fa() if fa else f4_alexei())
    if fa:
        LF['f4_alexei'] = list(getattr(F, 'F4_ALEXEI_AT', (54, 112)))
    RG.f4_anchors()
    RG.f4_fire_sheets(w)
    w('fire/smoke.png', LFE.soft_puff_sheet(8, 64, 48, ['#0E1310', '#151D18', '#1E2A22', '#2A3A2E', '#3A4E3E',
                                                        '#4E6650', '#668066'], 1021, grow=(0.24, 0.48),
                                            light=(-0.2, -0.9), thin=0.6, drift=-0.08, alpha=0.8, wisp=0.6))
    w('fire/ember.png', Q.ember_sheet())
    LF['lamp'] = list(LAMP_G)
    LF['f2_proj'] = dict(F2)
    _preview_fire()


def _preview_escape():
    LE['preview'] = [
        {'id': 'e1', 'layers': [['escape/e1_bg.png', [0, 0]], ['escape/e1_light.png', [0, 0], 'add'],
                                ['escape/e1_file.png', [210, 200], 'over', 2, 0]]},
        {'id': 'e2', 'layers': [['escape/e2_bg.png', [0, 0]], ['escape/e2_lamp.png', [0, 0], 'add'],
                                ['escape/e2_hatch.png', LE['hatch_at'], 'over', 3, 2],
                                ['escape/e2_konrad.png', LE['e2_konrad'], 'over', 4, 1]]},
        {'id': 'e2b', 'layers': [['escape/e2_bg.png', [0, 0]], ['escape/e2_lamp.png', [0, 0], 'add'],
                                 ['escape/e2_hatch.png', LE['hatch_at'], 'over', 3, 2],
                                 ['escape/e2_konrad.png', LE['e2_konrad'], 'over', 4, 3]]},
        {'id': 'e3a', 'layers': [['escape/e3a_bg.png', [0, 0]], ['escape/e3a_glow.png', [0, 0], 'add'],
                                 ['escape/e3a_hands.png', LE['e3_hands'], 'over', 4, 3]]},
        {'id': 'e3b', 'layers': [['escape/e3b_bg.png', [0, 0]], ['escape/e3b_hatch.png', LE['e3b_hatch'], 'over', 2, 1],
                                 ['escape/e3b_men.png', LE['e3b_men'], 'over', 2, 0]]},
        {'id': 'e4', 'layers': [['escape/e4_bg.png', [0, 0]], ['escape/e4_glow.png', [0, 0], 'add']] +
            [['escape/e4_window.png', xy, 'over', 3, 2 if i < 4 else 0] for i, xy in enumerate(LE['e4_windows'])]},
    ]


def build_escape(w):
    import env_c3p2_cine_yard as YD
    import env_c3p2_cine_life as LFE
    import env_c3p2_cine_figs as F
    w('escape/e1_bg.png', YD.e1_bg())
    w('escape/e1_light.png', YD.e1_light())
    cf = getattr(F, 'chute_file', None)
    w('escape/e1_file.png', cf() if cf else e1_file())
    w('escape/e2_bg.png', YD.e2_bg())
    hk = getattr(F, 'hatch_konrad', None)
    w('escape/e2_konrad.png', hk() if hk else e2_konrad())
    if hk:
        LE['e2_konrad'] = list(getattr(F, 'E2_KONRAD_AT', (190, 70)))
    w('escape/e2_lamp.png', Q.glow_sprite(VW, VH, [(YARD_LAMP[0], YARD_LAMP[1] + 4, 80, 60, (60, 46, 26), 1.5),
                                                   (128, 172, 70, 46, (70, 30, 8), 1.4),
                                                   (612, 112, 20, 20, (40, 32, 18), 1.5)], 6.0))
    w('escape/e3a_bg.png', YD.e3a_bg())
    w('escape/e3a_hands.png', e3a_hands())
    w('escape/e3a_glow.png', Q.glow_sprite(VW, VH, [(320, 340, 230, 150, (110, 46, 12), 1.4),
                                                    (320, 360, 120, 60, (90, 50, 20), 1.2)], 6.0))
    w('escape/e3b_bg.png', YD.e3b_bg())
    w('escape/e3b_hatch.png', YD.e3b_hatch())
    w('escape/e3b_men.png', e3b_men())
    build_escape_places(w)
    build_escape_people(w)
    _preview_escape()


def build_escape_places(w):
    """The escape's places and effects that need no figure renders (round 11 quick path)."""
    import env_c3p2_cine_yard as YD
    import env_c3p2_cine_life as LFE
    w('escape/e2_hatch.png', YD.e2_hatch())
    w('escape/e4_bg.png', YD.e4_bg())
    w('escape/e4_window.png', YD.e4_window())
    w('escape/e4_glow.png', YD.e4_glow())
    # soft smoke (no dithered blotches), lit orange from below by the burning windows
    w('escape/smoke.png', LFE.soft_puff_sheet(8, 112, 84, LFE.SMOKE_FIRE, 1031, grow=(0.24, 0.5), light=(0.05, 0.95),
                                              thin=0.4, drift=0.08, alpha=0.95))
    w('escape/breath.png', LFE.soft_puff_sheet(6, 24, 18, ['#3A4859', '#4F5E70', '#687789', '#A1AAB7', '#C2C9D2'], 1041,
                                               grow=(0.2, 0.42), light=(0.3, -0.8), thin=0.7, alpha=0.8, lobes=6))
    w('escape/flame_s.png', LFE.fire_sheet(8, 32, 40, 1043, tongues=3, width=(0.16, 0.26), length=(0.55, 1.0)))
    w('escape/flame_out.png', LFE.fire_sheet(8, 40, 70, 1045, tongues=3, width=(0.15, 0.24), length=(0.5, 1.0),
                                             lean=0.05, bed=0.7))
    w('escape/fire_halo.png', LFE.fire_halo(64, 64, (110, 46, 12), 1.5))
    w('escape/engine.png', YD.e4_engine())
    w('escape/beacon.png', YD.e4_beacon_glow())
    w('escape/beacon_wash.png', YD.e4_beacon_wash())


def build_escape_people(w):
    import env_c3p2_cine_figs as F
    # people in the lane (the figures stream's rig through env_c3p2_cine_people.person_sheet): four onlookers who
    # watch the wing and react to the bursts near them -- flinch, hands to the face, a step back, one points, one
    # waves the brigade in -- and two firemen running in as the engine noses into the lane
    import env_c3p2_cine_people as PP
    rim = getattr(PP, 'FIRE_RIM', None)

    def ps(kind, v, act, facing, n, look='fire_back'):
        return PP.person_sheet(kind, v, act, 28, facing, 'fire', look, n, eyes=False, rim=rim)
    people = []
    # each: a sequence of takes [t0, file, frames, fps, from (x, y), to (x, y), t1 of the move, flip]
    takes = {
        0: [('guest', 3, 'look_up', 165.0, 4, 3.0), ('guest', 3, 'huddle', 175.0, 1, 0.0)],
        1: [('woman', 1, 'look_up', 160.0, 4, 2.5), ('woman', 1, 'huddle', 200.0, 1, 0.0)],
        2: [('worker', 0, 'point', 170.0, 4, 3.0), ('worker', 0, 'walk', 30.0, 6, 9.0)],
        3: [('guest', 0, 'look_up', 160.0, 4, 2.0), ('guest', 0, 'walk', 90.0, 6, 9.0)],
    }
    seqs = {
        0: [[12.0, 0, (96, 304), (96, 304), 12.0], [13.66, 1, (96, 304), (84, 314), 14.2]],
        1: [[12.0, 0, (334, 306), (334, 306), 12.0], [12.42, 1, (334, 306), (324, 318), 12.95]],
        2: [[12.0, 0, (398, 303), (398, 303), 12.0], [13.25, 1, (398, 303), (420, 322), 14.6]],
        3: [[12.0, 0, (500, 305), (500, 305), 12.0], [14.6, 1, (500, 305), (552, 309), 16.0]],
    }
    for i in range(4):
        files = []
        for j, (kind, v, act, facing, n, fps) in enumerate(takes[i]):
            f = 'escape/onlooker_%d%s.png' % (i, '' if j == 0 else '_r%d' % j)
            w(f, ps(kind, v, act, facing, n))
            files.append((f, n, fps))
        seq = []
        for (t0, j, a0, a1, t1) in seqs[i]:
            seq.append(dict(t0=t0, file=files[j][0], n=files[j][1], fps=files[j][2], at=list(a0), to=list(a1), t1=t1))
        people.append(dict(file=files[0][0], n=files[0][1], fps=files[0][2], at=list(seqs[i][0][2]), t0=12.0,
                           seq=seq))
    fm = getattr(F, 'firemen', None)
    if fm:
        for i, d in enumerate(fm(26, 'fire')[:2]):
            w('escape/fireman_%d.png' % i, d['sheet'])
            people.append(dict(file='escape/fireman_%d.png' % i, n=d['n'], fps=d['fps'],
                               at=[(690, 306), (720, 308)][i], to=[(566, 306), (606, 310)][i], t0=14.7 + i * 0.25,
                               t1=15.9 + i * 0.25, flip=True))
    LE['e4_people'] = people
