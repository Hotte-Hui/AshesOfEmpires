"""env_c3p2_cine_registry -- the registry places of LS_C3_Fire, round 10 (owner: c3p2 places stream).

The commission's registry in the souterrain of the palais' east wing (the old Kurhaus coal cellar), ray-cast as a
small 3D room (floor, side walls, back wall, a segmental brick vault) and lit by the green-shaded lamp (f1) or the
burning cabinets (f4), then the sorting table and its things are painted over it:
  hall(mode)   the Karteisaal: oak card-index cabinets on the back and both side walls (small drawers with brass
               label holders, cornices, plinths), a rolling ladder on its rail, the high barred window with snow
               light, the brick vault with iron tie rods, the sorting table with the two halves of the file side by
               side, the red thread of the check, a magnifier, the drawer C-17 pulled out, ink, a stamp, card boxes,
               a chair with Elena's wine-red scarf; f4: the same hall in smoke and fire light, the table as left
  f2_bg        the Magazin aisle in one-point perspective (the round-8 camera kept): shelving with archive boxes,
               caged lamps under the vault, pipes, a ladder, a book trolley, papers on the floor, the service door
  f3_bg        the ramp door from inside: plank door with iron straps and the inner latch, the stone jamb with the
               gap, crates, a hand truck, the fire bucket, a lantern on its hook, the sign, snow blown in
Figures are the figures stream's (env_c3p2_cine_figs.reg_konrad, the fire-lit Alexei of env_c3p2_cine_fire).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, GREEN, PAPER, FIRE, RED, BRASS, SMOKE)
import env_c3p2_cine_life as LF
import pg

LF_ = Q.LAYOUT.setdefault('fire', {})
BRICKC = ['#0A0706', '#140D0A', '#1E140F', '#2A1C15', '#3A271C', '#4E3424', '#66442E']
EMBER = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']
PAL_R = LF.palette(NIGHT[:8], SNOW[:7], LAMP, OAK, GREEN, PAPER, BRASS, RED, BRICKC, EMBER, SMOKE,
                   ['#1A2A20', '#24382A', '#30483A', '#3E5A48', '#162018', '#203024', '#4E6A50', '#2A1E1A',
                    '#3E2A22', '#5A3A28', '#7A4A2C', '#E8D8B0', '#B8AE96', '#8E856C', '#4A3A6A', '#6A5690',
                    '#2E2440', '#7A2218'])

HV = dict(f=300.0, vx=320.0, vy=150.0, eye=1.55, W=4.4, Zb=5.6, Ys=2.05, rise=1.45)
LAMP_G = (300, 104)
TABLE_TOP = (236, 268)


def _cast(h=HV):
    """Ray-cast the hall: returns dict with surface id (0 floor, 1 back wall, 2 left, 3 right, 4 vault), world
    hit points X, Y, Z and normals (per pixel, 640 x 360)."""
    f, vx, vy, eye, W, Zb, Ys, rise = (h[k] for k in ('f', 'vx', 'vy', 'eye', 'W', 'Zb', 'Ys', 'rise'))
    R = (W * W + rise * rise) / (2 * rise)
    Yc = Ys + rise - R
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    dx = (xx + 0.5 - vx) / f
    dy = -(yy + 0.5 - vy) / f
    big = 1e9
    t = np.full((VH, VW), big, np.float32)
    sid = np.full((VH, VW), -1, np.int32)

    def take(tc, ok, k):
        nonlocal t, sid
        m = ok & (tc > 0) & (tc < t)
        t = np.where(m, tc, t)
        sid = np.where(m, k, sid)

    # floor
    tf = np.where(dy < -1e-6, -eye / np.minimum(dy, -1e-6), big)
    take(tf, (np.abs(tf * dx) <= W) & (tf <= Zb), 0)
    # back wall (under the vault's arch)
    tb = np.full((VH, VW), Zb, np.float32)
    Xb, Yb = tb * dx, eye + tb * dy
    inside_arch = (Yb <= Ys) | ((Xb * Xb + (Yb - Yc) ** 2) <= R * R)
    take(tb, (np.abs(Xb) <= W) & (Yb >= 0) & inside_arch, 1)
    # side walls (up to the springing line)
    ts = np.where(np.abs(dx) > 1e-6, W / np.maximum(np.abs(dx), 1e-6), big)
    Ysw = eye + ts * dy
    take(ts, (dx < 0) & (Ysw >= 0) & (Ysw <= Ys) & (ts <= Zb), 2)
    take(ts, (dx > 0) & (Ysw >= 0) & (Ysw <= Ys) & (ts <= Zb), 3)
    # the vault: cylinder along Z, centre (0, Yc), radius R, above the springing line
    a = dx * dx + dy * dy
    b = 2 * dy * (eye - Yc)
    c = (eye - Yc) ** 2 - R * R
    disc = np.maximum(b * b - 4 * a * c, 0)
    tv = (-b + np.sqrt(disc)) / np.maximum(2 * a, 1e-9)
    Yv = eye + tv * dy
    take(tv, (Yv >= Ys) & (tv <= Zb), 4)
    X = t * dx
    Y = eye + t * dy
    Z = t
    return dict(sid=sid, X=X, Y=Y, Z=Z, R=R, Yc=Yc, t=t)


def _cabinets(cv, m, U, V, light, seed, mode, face_dir=1.0):
    """Card-index cabinets on a wall: U along the wall (m), V height (m).  Units 1.1 m wide, 2.15 m tall, with a
    plinth, a cornice, 4 x 13 small drawers each (brass label holder, a pale card, a knob)."""
    unit = 1.1
    uu = np.mod(U, unit)
    ui = np.floor(U / unit)
    body = m & (V < 2.15)
    cv.put(body, '#3D271A', 0.78 + LF.hsh(ui, 1.0, seed)[body] * 0.12)
    plinth = body & (V < 0.12)
    cv.put(plinth, '#1C120C', 1.0)
    cornice = m & (V >= 2.05) & (V < 2.2)
    cv.put(cornice, '#553826', 0.95)
    cv.put(cornice & (V >= 2.17), '#6E4A33', 1.0)
    side = body & ((uu < 0.035) | (uu > unit - 0.035))
    cv.put(side, '#1C120C', 1.0)
    dw, dh = (unit - 0.08) / 4.0, (2.0 - 0.14) / 13.0
    du = np.mod(uu - 0.04, dw)
    dv = np.mod(V - 0.14, dh)
    drawer = body & (V >= 0.14) & (V < 2.0) & (uu >= 0.04) & (uu < unit - 0.04)
    gap = drawer & ((du < 0.012) | (dv < 0.012))
    cv.put(gap, '#140D0A', 1.0)
    face = drawer & ~gap
    hv = LF.hsh(np.floor((uu - 0.04) / dw) + ui * 7, np.floor((V - 0.14) / dh), seed + 1)
    cv.put(face, '#553826', 0.72 + hv[face] * 0.16)
    holder = face & (np.abs(du - dw * 0.5) < dw * 0.26) & (np.abs(dv - dh * 0.66) < dh * 0.17)
    cv.put(holder, '#9C7630', 0.9)
    card = holder & (np.abs(dv - dh * 0.66) < dh * 0.09) & (np.abs(du - dw * 0.5) < dw * 0.2)
    cv.put(card, '#D8CFB2', 0.85)
    knob = face & (np.abs(du - dw * 0.5) < dw * 0.07) & (np.abs(dv - dh * 0.28) < dh * 0.1)
    cv.put(knob, '#C49A48', 0.95)
    if mode in ('fire', 'fire_dark'):
        sc = body & (V > 1.2 + LF.nz(VW, VH, 9, seed + 3, 2) * 0.8)
        cv.mix(sc, '#0B0908', 0.75)
    return body | cornice


def _bricks(cv, m, U, V, light, seed, course=0.16, brick=0.34, base='#3A271C', mortar='#1E140F'):
    row = np.floor(V / course)
    off = np.where(np.mod(row, 2) == 0, 0.0, brick / 2)
    col = np.floor((U + off) / brick)
    hv = LF.hsh(row, col, seed)
    cv.put(m, base, 0.72 + hv[m] * 0.3)
    joint = m & ((np.mod(V, course) < course * 0.14) | (np.mod(U + off, brick) < brick * 0.07))
    cv.put(joint, mortar, 0.9)


def hall(mode):
    """f1 ('night') / f4 ('fire': the hall before the fire reaches it -- smoke, the lamp, the red of the aisle;
    the fire's own light is the additive f4_lit the runtime reveals behind the fire front) background."""
    cv = _hall_cv('fire_dark' if mode == 'fire' else mode)
    out = cv.quant(PAL_R, spread=10.0)
    out[..., 3] = 255
    return out


def f4_lit():
    """f4: the light of the burning cabinets (additive, black = clear) = the hall lit by the fire minus the hall
    without it, so bg + lit is the burning hall; the runtime reveals it from the right as the fire runs left."""
    a = np.clip(_hall_cv('fire').rgb - _hall_cv('fire_dark').rgb, 0, 255)
    return K.soft_quant(a, 3.0)


def f4_table():
    """f4: the sorting table and its things as a layer in front of the fire (the flames rise behind its far edge);
    the fire's light on it comes from f4_lit over it."""
    cv = _hall_cv('fire_dark')
    out = cv.quant(PAL_R, spread=10.0)
    out[..., 3] = np.where(cv.table, 255, 0)
    ys, xs = np.nonzero(cv.table)
    y0 = int(ys.min())
    LF_['f4_table_at'] = [0, y0]
    return out[y0:]


def _hall_cv(mode):
    """The ray-cast hall as a lit float canvas; mode 'night' (f1), 'fire' (f4 burning), 'fire_dark' (f4 unlit)."""
    fire = mode in ('fire', 'fire_dark')
    g = _cast()
    sid, X, Y, Z = g['sid'], g['X'], g['Y'], g['Z']
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.10, 0.11, 0.12) if not fire else (0.16, 0.11, 0.10))
    xx, yy = cv.xx, cv.yy
    # lights in world space: the green lamp (point, over the table), the window's snow light, the fire
    lamp = np.array([-0.16, 1.92, 2.4])
    P = np.stack([X, Y, Z], -1)
    N = np.zeros_like(P)
    N[sid == 0] = (0, 1, 0)
    N[sid == 1] = (0, 0, -1)
    N[sid == 2] = (1, 0, 0)
    N[sid == 3] = (-1, 0, 0)
    vm = sid == 4
    nv = np.stack([-X, -(Y - g['Yc']), np.zeros_like(X)], -1) / g['R']
    N[vm] = nv[vm]

    def point(pos, col, power, rng=6.0, soft=0.18):
        Lv = np.asarray(pos, np.float32)[None, None] - P
        d = np.linalg.norm(Lv, axis=-1) + 1e-6
        lam = np.clip((N * Lv).sum(-1) / d, 0, 1) * 0.8 + 0.2
        fall = np.clip(1 - d / rng, 0, 1) ** 2 / (0.5 + d * d * soft)
        cv.L += (lam * fall * power)[..., None] * np.asarray(col, np.float32)[None, None]

    if not fire:
        point(lamp, (0.70, 1.25, 0.82), 3.2, 10.0, 0.07)
        point((-2.55, 2.6, 5.5), (0.35, 0.42, 0.6), 1.2, 6.0, 0.1)
        cv.L[:] = np.minimum(cv.L, 2.2)
    else:
        point(lamp, (0.3, 0.5, 0.35), 0.8, 5.0)
        point((4.6, 1.0, 1.2), (0.55, 0.22, 0.08), 1.4, 8.0)       # the red of the burning aisle through the door
        if mode == 'fire':
            # the burning cabinets light the hall from low down, in front of each wall (weaker than round 10: the
            # flames themselves must stay the brightest thing in the frame)
            for fx, fy, fz, k in ((3.6, 0.9, 4.0, 1.45), (1.0, 0.9, 5.2, 1.25), (-2.2, 0.9, 5.2, 1.05),
                                  (4.2, 0.8, 2.0, 1.0), (-4.1, 0.8, 3.4, 0.75)):
                point((fx, fy, fz), (1.5, 0.74, 0.34), k, 8.0)
    # ---- surfaces
    floor = sid == 0
    fu, fv = X, Z
    flag = (np.mod(fu + np.floor(fv / 0.6) * 0.3, 0.6) < 0.02) | (np.mod(fv, 0.6) < 0.02)
    cv.put(floor, '#3A3226' if not fire else '#2A1E18', 0.85 + LF.nz(VW, VH, 6, 905, 2)[floor] * 0.2)
    cv.put(floor & flag, '#140D0A', 1.0)
    back = sid == 1
    cab_b = _cabinets(cv, back & (Y < 2.2) & (np.abs(X) < 4.38), X + 4.4, Y, None, 911, mode)
    _bricks(cv, back & ~cab_b, X, Y, None, 913)
    for k_, side in ((2, -1), (3, 1)):
        sw = sid == k_
        cab_s = _cabinets(cv, sw & (Y < 2.2) & (Z > 0.6), Z, Y, None, 915 + k_, mode)
        _bricks(cv, sw & ~cab_s, Z, Y, None, 917 + k_)
    vault = sid == 4
    th = np.arctan2(X, Y - g['Yc']) * g['R']
    _bricks(cv, vault, th + 30.0, Z, None, 921, course=0.18, brick=0.36, base='#2A1C15', mortar='#140D0A')
    for zr in (1.6, 3.6):                                                        # iron tie rods across the vault
        rod = vault & (np.abs(Z - zr) < 0.03)
        cv.put(rod, '#15171C', 1.0)
    rods = np.zeros_like(vault)
    for zr in (1.6, 3.6):
        a_ = (HV['vx'] - HV['f'] * HV['W'] / zr, HV['vy'] - HV['f'] * (HV['Ys'] - HV['eye']) / zr)
        b_ = (HV['vx'] + HV['f'] * HV['W'] / zr, a_[1])
        rods |= cv.seg([a_, b_], 0.6)
    cv.put(rods, '#15171C', 1.0)
    # the high barred window in the back wall's lunette (snow outside)
    wx0, wx1, wy0, wy1 = -3.0, -2.1, 2.3, 2.95
    win = back & (X >= wx0) & (X < wx1) & (Y >= wy0) & (Y < wy1)
    cv.emit(win, '#4F5E70', 0.8 + (Y[win] - wy0) * 0.5)
    cv.emit(win & (Y < wy0 + 0.12), '#C2C9D2', 0.9)
    cv.put(win & (np.mod(X - wx0, 0.15) < 0.025), '#05070C', 1.0, lit=False)
    cv.put(back & (X >= wx0 - 0.05) & (X < wx1 + 0.05) & (Y >= wy0 - 0.06) & (Y < wy0), '#56677A', 1.0)
    if not fire:
        shaft = cv.poly([(146, 82), (176, 82), (236, 236), (176, 236)])
        sk = np.clip(1 - (yy - 82) / 170.0, 0, 1) * (0.5 + 0.5 * LF.nz(VW, VH, 6, 1609, 2))
        cv.add(shaft & (pg.bayer(VW, VH, 0, 0) < sk * 0.55), '#141A22', 1.0)
    # the rolling ladder leaning on the left cabinets, its rail under the cornice
    lad = cv.seg([(118, 128), (150, 234)], 1.2) | cv.seg([(132, 126), (164, 232)], 1.2)
    for k in range(9):
        y_ = 136 + k * 11
        lad |= cv.seg([(118 + (y_ - 128) * 0.3, y_), (132 + (y_ - 126) * 0.3, y_ - 1)], 0.7)
    cv.put(lad, '#553826', 1.0)
    cv.put(cv.box(84, 122, 556, 124) & (back | (sid == 2) | (sid == 3)), '#9C7630', 0.8)
    if not fire:
        # drawer C-17 pulled out in the right cabinets, its red tag; Elena's scarf on the chair at the right
        dr = cv.box(498, 166, 522, 178)
        cv.put(dr, '#6E4A33', 1.0)
        cv.put(cv.box(500, 162, 520, 166), '#D8CFB2', 0.95)
        cv.put(cv.box(506, 170, 514, 175), '#A8382E', 1.0)
    else:
        # smoke already hangs under the vault, the far cabinets scorched
        sm = (sid == 4) | ((yy < 96 + LF.nz(VW, VH, 40, 931, 3) * 30) & (yy < 130))
        cv.mix(sm, '#2B2E33', 0.55 + LF.nz(VW, VH, 20, 933, 3)[sm] * 0.35)
    # ---- the sorting table (screen space), its things, a chair at the right
    far, near = TABLE_TOP
    top = (yy >= far) & (yy < near) & (xx >= 24) & (xx < 616)
    tl = 0.0
    cv.put(top, '#553826', 0.9 + (yy - far) / 60.0)
    cv.put(top & (yy == far), '#8A6040', 1.0)
    cv.put(top & (np.mod(xx * 0.25 + yy * 1.7 + LF.nz(VW, VH, 5, 941, 2) * 4, 7.0) < 0.5), '#3D271A', 0.9)
    front = (yy >= near) & (yy < near + 12) & (xx >= 24) & (xx < 616)
    cv.put(front, '#3D271A', 0.85)
    cv.put((yy >= near + 12) & (xx >= 24) & (xx < 616), '#140D0A', 1.0)
    for lx in (34, 596):
        cv.put(cv.box(lx, near + 12, lx + 10, 360), '#2B1B12', 0.9)
    table = (yy >= far) & (xx >= 24) & (xx < 616)
    for lx in (34, 596):
        table |= cv.box(lx, near + 12, lx + 10, 360)
    if True:
        # the two halves side by side: Russian pages (bluish, violet stamps) left, German (cream, black) right;
        # f4: the table as they left it
        for i, (x0, ru) in enumerate(((112, True), (150, True), (188, True), (232, False), (270, False), (308, False))):
            y0 = far + 6 + (i % 2) * 3
            sheet = cv.poly([(x0, y0), (x0 + 32, y0 - 1), (x0 + 34, y0 + 20), (x0 + 2, y0 + 21)])
            cv.put(sheet, '#C2C9D2' if ru else '#D8CFB2', 0.95)
            for ly in range(y0 + 4, y0 + 18, 3):
                ln = sheet & (yy == ly) & (np.mod(xx * 3 + ly, 5) < 3) & (xx > x0 + 4) & (xx < x0 + 28)
                cv.put(ln, '#4A3A6A' if ru else '#2A261E', 1.0)
            st = sheet & cv.ell(x0 + 24, y0 + 14, 4, 3)
            cv.put(st, '#6A5690' if ru else '#A8382E', 1.0)
        for (a, b) in ((128, 248), (166, 286), (204, 324)):
            cv.put(cv.seg([(a, far + 16), ((a + b) / 2, far + 25), (b, far + 16)], 0.5), '#A8382E', 1.1)
        mag = cv.ell(372, far + 14, 9, 5)
        cv.put(mag, '#9C7630', 1.0)
        cv.put(cv.ell(372, far + 14, 6, 3), '#E8D8B0', 1.0)
        cv.put(cv.seg([(380, far + 16), (394, far + 23)], 1.2), '#3D271A', 1.0)
        # the drawer C-17 on the table, cards standing in it; ink, a stamp on its pad, card boxes
        dr = cv.poly([(408, far + 2), (452, far + 1), (456, far + 22), (404, far + 23)])
        cv.put(dr, '#6E4A33', 1.0)
        cv.put(cv.poly([(412, far + 3), (448, far + 2), (450, far + 10), (410, far + 11)]), '#D8CFB2', 0.9)
        cv.put(cv.box(424, far + 14, 436, far + 19), '#A8382E', 1.0)
        cv.put(cv.box(470, far + 2, 482, far + 14), '#14161A', 1.0)
        cv.put(LF.edge_top(cv.box(470, far + 2, 482, far + 14)), '#9C7630', 1.0)
        cv.put(cv.box(490, far + 8, 512, far + 18), '#2A1E1A', 1.0)
        cv.put(cv.box(496, far + 2, 504, far + 9), '#3D271A', 1.0)
        for bx in (530, 556):
            bx_m = cv.box(bx, far - 10, bx + 22, far + 10)
            cv.put(bx_m, '#8E856C', 0.95)
            cv.put(LF.edge_top(bx_m), '#B8AE96', 1.0)
    if not fire:
        # a chair at the right end with Elena's wine-red scarf over its back
        chair = cv.seg([(574, far - 30), (576, near + 10)], 1.6) | cv.seg([(600, far - 30), (602, near + 10)], 1.6) | \
            cv.seg([(574, far - 28), (600, far - 28)], 1.4) | cv.seg([(574, far - 14), (600, far - 14)], 1.0)
        cv.put(chair, '#3D271A', 1.0)
        scarf = cv.poly([(570, far - 32), (604, far - 34), (602, far - 22), (592, far - 20), (590, near - 4),
                         (582, near - 2), (580, far - 18), (572, far - 20)])
        cv.put(scarf, '#7A2218', 0.95 + C.edge_light(scarf, (-0.7, -0.7), width=3.0, soft=1)[scarf] * 0.5)
        cv.put(scarf & (np.mod(cv.yy + cv.xx * 0.3, 4) < 1), '#4A1712', 1.0)
    else:
        # loose cards blown about, the chair knocked over, Elena's scarf slipped onto the table's edge
        for x0, y0 in ((134, far + 22), (352, far + 18), (520, far + 20), (588, far + 12), (250, far + 26)):
            card = cv.poly([(x0, y0), (x0 + 14, y0 - 2), (x0 + 15, y0 + 7), (x0 + 1, y0 + 9)])
            cv.put(card, '#B3A98D', 0.9)
            cv.put(LF.edge_top(card), '#D8CFB2', 0.95)
        fallen = cv.seg([(560, near - 4), (600, near + 20)], 1.6) | cv.seg([(566, near + 14), (606, near - 6)], 1.4)
        cv.put(fallen, '#3D271A', 1.0)
        scarf = cv.poly([(536, far + 4), (566, far + 8), (570, near + 2), (562, near + 16), (552, near + 14),
                         (556, near - 2), (540, far + 14)])
        cv.put(scarf, '#7A2218', 0.95 + C.edge_light(scarf, (0.6, -0.8), width=3.0, soft=1)[scarf] * 0.5)
        cv.put(scarf & (np.mod(cv.yy + cv.xx * 0.3, 4) < 1), '#4A1712', 1.0)
        table |= fallen | scarf
    cv.table = table
    # ---- the lamp: cord from the vault, enamel shade (green outside, white inside), the bulb
    cv.put(cv.box(LAMP_G[0], 30, LAMP_G[0] + 1, LAMP_G[1] - 22), '#15171C', 1.0, lit=False)
    shade = cv.poly([(LAMP_G[0] - 9, LAMP_G[1] - 22), (LAMP_G[0] + 10, LAMP_G[1] - 22), (LAMP_G[0] + 34, LAMP_G[1]),
                     (LAMP_G[0] - 33, LAMP_G[1])])
    cv.put(shade, '#2E5640', 0.5 + np.clip((LAMP_G[0] - cv.xx) / 60.0, -0.2, 0.4), lit=False)
    cv.put(shade & (yy >= LAMP_G[1] - 2), '#B5D6BC', 0.9 if not fire else 0.5, lit=False)
    cv.emit(cv.ell(LAMP_G[0], LAMP_G[1] + 1, 6, 2.5), '#EFE8D2' if not fire else '#8E856C')
    LF_['lamp'] = list(LAMP_G)
    return cv


# ================================================================================================ f2 the aisle
F2 = {'vpx': 320.0, 'vpy': 150.0, 'f': 300.0, 'eye': 1.6, 'half': 1.2, 'far': 9.0, 'h': 2.6}


def _f2p(X, Y, Z):
    return (F2['vpx'] + F2['f'] * X / Z, F2['vpy'] - F2['f'] * (Y - F2['eye']) / Z)


def f2_bg():
    """f2: the aisle before the fire -- dim caged lamps, the lit service door at the end, a red glimmer low on the
    right where the C-17 boxes start to smoulder; the fire's light is the additive f2_glow (f2_fire_light)."""
    cv = _f2_cv(False)
    out = cv.quant(PAL_R, spread=10.0)
    out[..., 3] = 255
    return out


def f2_fire_light():
    """f2: the light of the burning boxes on the right shelves (additive: the aisle lit by the fire minus the aisle
    without it), faded in by the runtime as the boxes catch."""
    a = np.clip(_f2_cv(True).rgb - _f2_cv(False).rgb, 0, 255)
    return K.soft_quant(a, 3.0)


def _f2_cv(burning):
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.12, 0.11, 0.11))
    xx, yy = cv.xx, cv.yy
    f, vx, vy, eye, half, far = F2['f'], F2['vpx'], F2['vpy'], F2['eye'], F2['half'], F2['far']
    cv.light(430, 190, 160, (0.30, 0.12, 0.05), 1.4)
    if burning:
        cv.light(436, 170, 300, (1.0, 0.48, 0.2), 1.3)
        cv.light(436, 175, 90, (0.7, 0.36, 0.14), 1.2)
    cv.light(vx, vy + 20, 110, (0.9, 0.62, 0.32), 1.4)
    for zl in (2.2, 4.6, 7.0):                                                    # dim caged lamps under the vault
        lx_, ly_ = _f2p(0.0, 2.75, zl)
        cv.light(lx_, ly_ + 30 / zl, 160 / zl, (0.4, 0.34, 0.24), 1.4)
    dx = xx + 0.5 - vx
    dy = yy + 0.5 - vy
    fw = cv.full()
    cv.put(fw, '#2A1C15', 0.8)
    # floor
    Zf = np.where(dy > 0.5, f * eye / np.maximum(dy, 0.5), 1e9)
    Xf = dx * Zf / f
    floor = (dy > 0.5) & (Zf < far) & (np.abs(Xf) < half)
    cv.put(floor, '#3A3226', 0.8 + LF.nz(VW, VH, 5, 1601, 2)[floor] * 0.25)
    cv.put(floor & (np.mod(Zf, 1.2) < 0.04), '#140D0A', 1.0)
    cell = np.floor(Xf / 0.3) * 31 + np.floor(Zf / 0.4) * 7
    lx_ = np.mod(Xf, 0.3) / 0.3
    lz_ = np.mod(Zf, 0.4) / 0.4
    papers = floor & (LF.hsh(cell, 2.0, 1603) > 0.86) & (np.abs(lx_ - 0.5) < 0.3) & (np.abs(lz_ - 0.5) < 0.22)
    cv.put(papers, '#B3A98D', 0.9)
    # ceiling (brick vault, flattened) with a pipe along it
    Zc = np.where(dy < -0.5, f * (2.9 - eye) / np.maximum(-dy, 0.5), 1e9)
    Xc = dx * Zc / f
    ceil = (dy < -0.5) & (Zc < far) & (np.abs(Xc) < half + 0.3)
    _bricks(cv, ceil, Xc * 2.0, Zc, None, 1605, course=0.25, brick=0.5, base='#2A1C15', mortar='#140D0A')
    for px_ in (-0.7, 0.75):
        pipe = ceil & (np.abs(Xc - px_) < 0.05)
        cv.put(pipe, '#464D55', 1.0)
    # shelving on both sides: boards, uprights, archive boxes with labels, the red C-17 tags on the right
    for sgn in (-1, 1):
        side = (dx * sgn > 0.5)
        Zs = np.where(side, f * half / np.maximum(np.abs(dx), 0.5), 1e9)
        Ys = eye - dy * Zs / f
        sh = side & (Zs >= 0.9) & (Zs < far) & (Ys >= 0) & (Ys < F2['h'])
        cv.put(sh, '#1C120C', 1.0)
        boards = sh & (np.mod(Ys, 0.42) < 0.035)
        cv.put(boards, '#553826', 0.9)
        bz = np.mod(Zs, 0.36)
        by = np.mod(Ys, 0.42)
        boxf = sh & (bz > 0.02) & (by > 0.04) & (by < 0.34 - LF.hsh(np.floor(Zs / 0.36), np.floor(Ys / 0.42), sgn) * 0.06)
        hv = LF.hsh(np.floor(Zs / 0.36) * 7.1, np.floor(Ys / 0.42) * 3.3, sgn + 4)
        cv.put(boxf, '#665036', 0.7 + hv[boxf] * 0.3)
        lab = boxf & (np.abs(bz - 0.18) < 0.06) & (np.abs(by - 0.19) < 0.05)
        cv.put(lab, '#D8CFB2', 0.85)
        if sgn > 0:
            c17 = lab & (Zs > 2.9) & (Zs < 4.7) & (Ys > 0.8) & (Ys < 1.7)
            cv.put(c17, '#A8382E', 1.0)
        missing = boxf & (hv > 0.92)
        cv.put(missing, '#0B0908', 1.0)
        up = sh & (np.mod(Zs, 2.0) < 0.07)
        cv.put(up, '#464D55', 0.9)
        top = side & (Zs >= 0.9) & (Zs < far) & (Ys >= F2['h']) & (Ys < 2.9)
        cv.put(top, '#1E140F', 0.9)
    # a ladder leaning on the left shelves, a book trolley in the aisle
    a0, a1 = _f2p(-1.15, 0.0, 3.0), _f2p(-1.15, 2.4, 3.6)
    b0, b1 = _f2p(-0.85, 0.0, 3.0), _f2p(-1.15, 2.4, 3.3)
    lad = cv.seg([a0, a1], 1.0) | cv.seg([b0, b1], 1.0)
    for k in range(1, 8):
        u = k / 8
        lad |= cv.seg([(a0[0] + (a1[0] - a0[0]) * u, a0[1] + (a1[1] - a0[1]) * u),
                       (b0[0] + (b1[0] - b0[0]) * u, b0[1] + (b1[1] - b0[1]) * u)], 0.6)
    cv.put(lad, '#553826', 1.0)
    t0, t1 = _f2p(-0.5, 0.0, 5.0), _f2p(0.1, 0.9, 5.0)
    trolley = cv.box(t0[0], t1[1], t1[0], t0[1] - 3)
    cv.put(trolley, '#2B1B12', 1.0)
    cv.put(trolley & (np.mod(yy, 6) < 1), '#553826', 1.0)
    cv.put(cv.box(t0[0] + 2, t1[1] - 5, t1[0] - 2, t1[1]), '#665036', 1.0)
    for wx_ in (t0[0] + 2, t1[0] - 3):
        cv.put(cv.ell(wx_, t0[1] - 2, 2, 2), '#15171C', 1.0)
    # caged lamps (off) hanging from the vault
    for zl in (2.2, 4.6, 7.0):
        lx_, ly_ = _f2p(0.0, 2.75, zl)
        r = 34.0 / zl
        cv.put(cv.seg([(lx_, ly_ - r * 3), (lx_, ly_ - r)], 0.5), '#15171C', 1.0)
        cg = cv.ell(lx_, ly_, r, r * 1.2)
        cv.put(cg, '#3A3226', 1.0)
        cv.put(cg & (np.mod(xx, 2) == 0), '#15171C', 1.0)
    # the service door at the end (closed state; the open frames are a sprite), its sign
    d0 = _f2p(-0.5, 2.1, far)
    d1 = _f2p(0.5, 0.0, far)
    door = cv.box(d0[0], d0[1], d1[0], d1[1])
    cv.put(door, '#15171C', 1.0)
    cv.put(door & (np.mod(xx, 5) < 1), '#464D55', 1.0)
    sg = cv.box(d0[0] + 6, d0[1] - 9, d1[0] - 6, d0[1] - 3)
    cv.put(sg, '#D8CFB2', 0.8)
    LF_['f2_door'] = [int(d0[0]), int(d0[1]), int(d1[0]), int(d1[1])]
    anchors = []
    for (Z, Y) in ((3.4, 1.26), (3.9, 1.26), (3.1, 0.84), (4.3, 1.68), (2.9, 1.68), (4.5, 0.84)):
        x, y = _f2p(half - 0.02, Y, Z)
        anchors.append([round(x, 1), round(y, 1)])
    LF_['f2_fire'] = anchors
    LF_['f2_proj'] = dict(F2)
    return cv


# ================================================================================================ f3 ramp door
F3_GAP_X = 470
F3_FLOOR = 292


def f3_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.12, 0.11, 0.11))
    xx, yy = cv.xx, cv.yy
    cv.light(260, 330, 440, (1.0, 0.5, 0.22), 1.25)
    cv.light(80, 300, 200, (0.5, 0.26, 0.12), 1.3)
    cv.light(F3_GAP_X + 1, 150, 90, (0.4, 0.46, 0.6), 1.4)
    wall = cv.full()
    _bricks(cv, wall, xx / 50.0, (360 - yy) / 50.0, None, 1701, course=0.16, brick=0.4, base='#3A271C', mortar='#1E140F')
    salt = wall & (yy > 250) & (LF.nz(VW, VH, 6, 1703, 2) > 0.6)
    cv.mix(salt, '#8E856C', 0.25)
    # the plank door with three iron straps, rivets, the inner latch and its handle
    door = cv.box(150, 30, F3_GAP_X, F3_FLOOR)
    cv.put(door, '#553826', 0.78 + LF.nz(VW, VH, 10, 1705, 2)[door] * 0.18)
    cv.put(door & (np.mod(xx - 150, 40) < 1), '#1C120C', 1.0)
    grain = door & (LF.vnoise(xx * 0.08, yy * 0.9, 1707) > 0.68)
    cv.put(grain, '#3D271A', 0.95)
    for sy in (52, 150, 250):
        strap = door & (yy >= sy) & (yy < sy + 14)
        cv.put(strap, '#22262D', 1.0)
        cv.put(strap & (yy == sy), '#5E666E', 1.0)
        for rx in range(160, F3_GAP_X - 6, 26):
            cv.put(cv.ell(rx, sy + 7, 2.4, 2.4), '#5E666E', 1.0)
            cv.put(cv.ell(rx - 0.6, sy + 6.4, 1.0, 1.0), '#7A828A', 1.0)
        cv.put(cv.ell(156, sy + 7, 6, 9), '#15171C', 1.0)                         # hinge pin knuckle
    lb = cv.box(398, 112, 440, 166)
    cv.put(lb, '#22262D', 1.0)
    cv.put(LF.edge_top(lb) | LF.edge_dir(lb, -1, 0), '#5E666E', 1.0)
    cv.put(cv.ell(418, 150, 4, 4), '#05070C', 1.0)
    cv.put(cv.seg([(406, 128), (446, 128), (450, 136)], 2.2), '#464D55', 1.0)
    cv.put(cv.box(380, 126, 398, 132), '#22262D', 1.0)                          # the inner latch bar
    cv.put(cv.box(340, 124, 346, 134), '#464D55', 1.0)                           # its keeper on the door
    # the stone jamb right of the gap, the lintel, the threshold
    jamb = cv.box(F3_GAP_X + 3, 0, F3_GAP_X + 46, F3_FLOOR)
    cv.put(jamb, '#3E4A5A', 0.8 + LF.nz(VW, VH, 5, 1709, 2)[jamb] * 0.2)
    cv.put(jamb & (np.mod(yy, 46) < 1), '#1B232E', 1.0)
    cv.put(cv.box(140, 18, F3_GAP_X + 46, 30), '#3E4A5A', 0.85)
    cv.put(cv.box(F3_GAP_X, 0, F3_GAP_X + 3, F3_FLOOR), '#05070C', 1.0, lit=False)
    flr = yy >= F3_FLOOR
    cv.put(flr, '#3A3226', 0.85 + LF.nz(VW, VH, 6, 1711, 2)[flr] * 0.2)
    cv.put(flr & (np.mod(xx + (yy - F3_FLOOR) * 0.4, 48) < 1), '#140D0A', 1.0)
    cv.put(cv.box(150, F3_FLOOR, F3_GAP_X + 3, F3_FLOOR + 3), '#05070C', 1.0, lit=False)
    # snow blown in under the door: a low cold drift along the gap (lit by the yard's light through the gap, not by
    # the fire), crisp crystals on its crest
    dn = LF.nz(VW, VH, 6, 955, 2)
    drift = flr & (yy < F3_FLOOR + 16) & (xx > 160) & (xx < 470) & (dn > 0.5 + (yy - F3_FLOOR) / 34.0)
    cv.emit(drift, '#687789', 0.9 + dn[drift] * 0.2)
    crest = drift & ~C.shift(drift, 0, -1)
    cv.emit(crest, '#C2C9D2', 0.95)
    cv.emit(crest & (LF.hsh(xx, yy, 957) > 0.8), '#F2F3F5', 1.0)
    cv.emit(drift & (yy >= F3_FLOOR + 3) & ~crest & (LF.hsh(xx, yy, 959) > 0.9), '#A1AAB7', 1.0)
    # crates and archive boxes stacked at the left, a hand truck, the fire bucket on its hook, a lantern, the sign
    LF.crate(cv, 20, F3_FLOOR + 6, 62, 40, col='#553826', snow=None, lid=False)
    LF.crate(cv, 30, F3_FLOOR - 34, 48, 30, col='#665036', snow=None, lid=False)
    LF.crate(cv, 84, F3_FLOOR + 4, 46, 30, col='#3D271A', snow=None, lid=False)
    for bx in (36, 52):
        cv.put(cv.box(bx, F3_FLOOR - 46, bx + 14, F3_FLOOR - 34), '#8E856C', 0.95)
        cv.put(cv.box(bx + 4, F3_FLOOR - 42, bx + 10, F3_FLOOR - 38), '#D8CFB2', 0.9)
    ht = cv.seg([(538, F3_FLOOR + 8), (556, F3_FLOOR - 70)], 1.4) | cv.seg([(552, F3_FLOOR + 8), (570, F3_FLOOR - 70)], 1.4) | \
        cv.seg([(534, F3_FLOOR + 8), (560, F3_FLOOR + 8)], 1.4)
    cv.put(ht, '#22262D', 1.0)
    cv.put(cv.ell(546, F3_FLOOR + 10, 5, 5), '#15171C', 1.0)
    cv.put(cv.seg([(588, 150), (594, 144)], 1.0), '#464D55', 1.0)
    bucket = cv.poly([(580, 152), (602, 152), (598, 176), (584, 176)])
    cv.put(bucket, '#A8382E', 0.95 + C.edge_light(bucket, (-0.8, -0.4), width=3.0, soft=1)[bucket] * 0.6)
    tf = K.vtext('FEUER', 's', 1)
    cv.put(K.place(tf, VW, VH, 591 - tf.shape[1] // 2, 160) & bucket, '#EFE8D2', 0.9)
    cv.put(cv.seg([(560, 70), (566, 64)], 1.0), '#464D55', 1.0)
    lan = cv.poly([(560, 74), (572, 74), (570, 94), (562, 94)])
    cv.put(lan, '#22262D', 1.0)
    cv.put(cv.box(563, 78, 569, 90), '#3A3226', 1.0)
    sign = cv.box(520, 58, 626, 70)
    cv.put(sign, '#D8CFB2', 0.85)
    ts = K.vtext('RAMPE · АППАРЕЛЬ', 's', 1)
    cv.put(K.place(ts, VW, VH, 573 - ts.shape[1] // 2, 61) & sign, '#2A261E', 1.0)
    cv.put(cv.seg([(530, 58), (536, 50)], 0.5) | cv.seg([(616, 58), (610, 50)], 0.5), '#464D55', 1.0)
    out = cv.quant(PAL_R, spread=10.0)
    out[..., 3] = 255
    LF_['f3_gap'] = [F3_GAP_X, 0, F3_GAP_X + 3, F3_FLOOR]
    LF_['f3_floor'] = [150, F3_FLOOR, F3_GAP_X + 3, F3_FLOOR + 3]
    return out


# ================================================================================================ fire sheets
def f4_anchors():
    """Fire clusters on the burning cabinets in the order the fire runs (right -> left): [x, y bottom, kind
    (0 mid / 1 big / 2 wide / 3 small)].  Round 13: the flames are the pixel fire kit's -- the runtime runs its
    wall of fire along the back wall behind the table's far edge (the f4_table layer hides its bed) and stands
    the kit's single flames on these anchors: towers behind the wall at the big and mid ones, large flames on
    the side walls' (lower, nearer the camera)."""
    rng = np.random.default_rng(1851)
    pts = []
    # right side wall (in perspective: the cabinets' feet run from (556, 233) at the back to (640, 263))
    for x in (630, 604, 578):
        yb = 233 + (x - 556) * 30.0 / 84.0 + 8
        pts.append([x, round(yb), 1 if x > 600 else 0])
    # back wall, right to left: irregular steps, a big or wide one every few, small catching ones between
    x = 548.0
    k = 0
    while x > 92:
        r = rng.random()
        kind = 1 if r < 0.3 else (2 if r < 0.55 else 0)
        if k % 4 == 3:
            kind = 1
        pts.append([round(x), 246 + int(rng.integers(-3, 4)), kind])
        if rng.random() < 0.45:
            pts.append([round(x - rng.uniform(10, 18)), 240 + int(rng.integers(-2, 3)), 3])
        x -= rng.uniform(30, 56)
        k += 1
    # left side wall
    for x in (70, 44, 14):
        yb = 233 + (84 - x) * 30.0 / 84.0 + 8
        pts.append([x, round(yb), 1 if x < 30 else 0])
    LF_['f4_fire'] = pts
    return pts
