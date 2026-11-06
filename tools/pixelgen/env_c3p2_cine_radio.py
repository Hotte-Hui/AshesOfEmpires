"""env_c3p2_cine_radio -- art of LS_C3_Radio (owner: cinematics stream, round 8; C3P2_DESIGN §2.9).

r1/r6  the station square at night from the station roof (one painting, two shots): Hotel Europa (Konrad, left)
       and Hotel Nord (Alexei, right) face each other across the snow, the palais with its dark east wing at the
       far end; pinhole camera SQ shared with scenes/cinematics/ch3_radio/ch3_radio.gd (walker paths, footprints
       and the lit windows are computed here and handed over in layout.json)
r2     Alexei's room in the Hotel Nord: the table at the window, the Bakelite radio, the tea glass; across the
       square Konrad's lit window
r3     Konrad's room in the Hotel Europa: the same radio model at the same place (the match cut on the dial),
       the notepad, the desk lamp; across the square Alexei's lit window
r4     split: the two doors from the floor, the gap of corridor light; the folded note; the note close-up in two
       languages (its words are copied from data/locale/de_c3p2_cinematics.json)
r5     Café „Korridor" after closing: chairs on the tables, Elena's table with an untouched glass, the station
       clock outside (its hands are drawn at runtime: 0.10)
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, PAPER, BRASS, BAKE, RED, K_COAT,
                               A_COAT, A_FUR, grid, poly, ell, box, hexrgb)
import pg

L = Q.LAYOUT.setdefault('radio', {})

# ======================================================================================= the square (r1/r6)
SQ = {'f': 360.0, 'H': 10.0, 'yh': 120.0, 'cx': 320.0}
HOTEL_X = 24.0                       # facades at X = -24 (Europa) and +24 (Nord)
HOTEL_Z = (18.0, 95.0)
PALAIS_Z = 150.0
DOOR_K = (-24.0, 38.0)               # Europa entrance (X, Z) - Konrad
DOOR_A = (24.0, 43.25)               # Nord entrance - Alexei
WIN_K = (50.6, 53.4, 13.2, 15.4)     # Konrad's window on the Europa facade: Z0, Z1, Y0, Y1
WIN_A = (58.2, 60.8, 7.9, 9.7)       # Alexei's window on the Nord facade
EAST_WING = (22.0, PALAIS_Z)         # where the two tracks converge


def sq(X, Y, Z):
    return (SQ['cx'] + SQ['f'] * X / Z, SQ['yh'] + SQ['f'] * (SQ['H'] - Y) / Z)


def _ss_grid(ss):
    yy, xx = np.mgrid[0:VH * ss, 0:VW * ss].astype(np.float32)
    return (yy + 0.5) / ss, (xx + 0.5) / ss


def _down(a, ss):
    h, w = a.shape[0] // ss, a.shape[1] // ss
    return a.reshape(h, ss, w, ss, *a.shape[2:]).mean(axis=(1, 3))


def _facade_tex(kind):
    """Flat facade texture (u = along the street, v = top->bottom), 12 px per metre."""
    ppm = 12.0
    z0, z1 = HOTEL_Z
    Ytop = 25.0 if kind == 'europa' else 24.5
    w, h = int((z1 - z0) * ppm), int(Ytop * ppm)
    if kind == 'europa':
        R = C.ramps(W=['#06080E', '#0B101A', '#111824', '#18212E', '#202B3A', '#2A3747', '#364558'],
                    S=SNOW, G=['#05070C', '#080C14', '#0D131E', '#131B28', '#1B2533'], L=LAMP, B=BRASS,
                    D=OAK, M=['#070A10', '#0C1119', '#121923', '#1A222D', '#232D39'])
    else:
        R = C.ramps(W=['#07090F', '#0D121B', '#141B26', '#1C2532', '#26313F', '#323E4D', '#404D5D'],
                    S=SNOW, G=['#05070C', '#080C14', '#0D131E', '#131B28', '#1B2533'], L=LAMP, B=BRASS,
                    D=IRON, M=['#070A10', '#0C1119', '#121923', '#1A222D', '#232D39'])
    p = C.Paint(w, h, R, 'facade_' + kind)
    yy, xx = p.yy, p.xx
    Y = Ytop - (yy + 0.5) / ppm                      # metres above the square
    Z = z0 + (xx + 0.5) / ppm
    nz = Q.noise(w, h, 18, 401 if kind == 'europa' else 402)
    p.put(np.ones((h, w), bool), 'W', 2.2 + (nz - 0.5) * 0.9 + np.clip((Y - 4) / 20, 0, 1) * 0.6)
    glass = np.zeros((h, w), bool)
    sills = np.zeros((h, w), bool)
    if kind == 'europa':
        # rusticated ground floor with arches, string course, four upper floors, cornice, mansard
        p.put((Y < 4.6) & (np.mod(Y, 0.75) < 0.09), 'W', 1.0)
        p.put((Y >= 4.5) & (Y < 5.0), 'W', 3.8)                                  # string course
        p.put((Y >= 19.8) & (Y < 20.8), 'W', 4.2)                                # main cornice
        p.put((Y >= 20.7) & (Y < 21.0), 'S', 6.5)                                # snow on the cornice
        roof = Y >= 21.0
        p.put(roof, 'M', 2.0 + nz[roof] * 1.2)
        p.put(roof & (Q.noise(w, h, 7, 409) > 0.55), 'S', 3.6)                   # snow on the slates
        for zc in np.arange(z0 + 2.0, z1, 4.0):
            dx = np.abs(Z - zc)
            # ground floor arches (dark), the door bay is wider and gets doors + lamps
            door = abs(zc - DOOR_K[1]) < 0.1
            aw = 1.5 if door else 1.1
            arch = (dx < aw) & (Y < 3.4) | (np.hypot(Z - zc, (Y - 3.4) * 1.0) < aw) & (Y >= 3.4)
            glass |= arch & (Y > 0.4)
            if door:
                p.put(arch & (Y < 3.1), 'D', 2.0 + (np.abs(Z - zc) < 0.06) * -1.5)
                p.put((np.abs(Z - zc) < 2.2) & (Y >= 3.5) & (Y < 3.8), 'W', 4.6)   # canopy
                p.put((np.abs(Z - zc) < 2.2) & (Y >= 3.8) & (Y < 3.95), 'S', 7.0)
                for s_ in (-1.9, 1.9):
                    p.put((np.abs(Z - zc - s_) < 0.12) & (Y > 2.3) & (Y < 2.7), 'L', 5.6)
            # upper floors: tall windows with sills (snow) and pediments on the first floor
            for fl, (y0, y1) in enumerate(((6.0, 8.4), (9.6, 11.8), (13.2, 15.4), (16.8, 18.8))):
                win = (dx < 0.62) & (Y >= y0) & (Y < y1)
                glass |= win
                sills |= (dx < 0.78) & (Y >= y0 - 0.22) & (Y < y0)
                if fl == 0:
                    ped = (Y >= y1 + 0.15) & (Y < y1 + 0.15 + (0.9 - dx) * 0.5) & (dx < 0.9)
                    p.put(ped, 'W', 4.0)
                    p.put((Y >= y0 - 0.8) & (Y < y0 - 0.1) & (dx < 0.95) & (np.mod(Z * 4, 1.0) < 0.5), 'W', 3.6)
            # dormers
            dorm = (dx < 0.55) & (Y >= 21.6) & (Y < 23.0)
            p.put(dorm | ((dx < 0.75) & (Y >= 23.0) & (Y < 23.4)), 'W', 3.0)
            glass |= (dx < 0.38) & (Y >= 21.8) & (Y < 22.8)
            p.put((dx < 0.8) & (Y >= 23.35) & (Y < 23.6), 'S', 6.0)
        # the sign across the first floor, near the street corner
        tm = K.vtext('HOTEL EUROPA', 'l', 2)
        tm = np.repeat(np.repeat(tm, 2, 0), 2, 1)
        sx0 = int((DOOR_K[1] - z0) * ppm - tm.shape[1] / 2)
        sy0 = int((Ytop - 5.75) * ppm)
        sm = K.place(tm, w, h, sx0, sy0)
        p.put(sm, 'B', 2.2)
        p.put(sm & ~C.shift(sm, 0, -1), 'B', 3.2)
    else:
        # Hotel Nord: smooth render, six storeys of flush windows, flat roof with a parapet and roof letters
        for fl in range(6):
            yb = 0.0 + fl * 3.5
            p.put((Y >= yb + 3.38) & (Y < yb + 3.5), 'W', 1.2)
        p.put((Y >= 20.6) & (Y < 21.4), 'W', 4.0)                                 # parapet
        p.put((Y >= 21.3) & (Y < 21.55), 'S', 6.8)
        for zc in np.arange(z0 + 1.75, z1, 3.5):
            dx = np.abs(Z - zc)
            door = abs(zc - DOOR_A[1]) < 0.9
            if door:
                g = (dx < 1.6) & (Y > 0.0) & (Y < 2.8)
                glass |= g
                p.put((np.abs(Z - DOOR_A[1]) < 2.6) & (Y >= 2.9) & (Y < 3.25), 'W', 5.0)   # concrete canopy
                p.put((np.abs(Z - DOOR_A[1]) < 2.6) & (Y >= 3.25) & (Y < 3.42), 'S', 7.2)
                p.put((np.abs(Z - DOOR_A[1]) < 0.1) & (Y > 2.5) & (Y < 2.8), 'L', 5.8)
            else:
                glass |= (dx < 0.9) & (Y >= 0.7) & (Y < 2.6)                      # ground floor windows
            for fl in range(1, 6):
                yb = fl * 3.5
                win = (dx < 0.7) & (Y >= yb + 0.9) & (Y < yb + 2.7)
                glass |= win
                sills |= (dx < 0.82) & (Y >= yb + 0.72) & (Y < yb + 0.9)
        # roof letters on a steel frame (seen against the sky)
        tm = K.vtext('HOTEL NORD', 'l', 2)
        tm = np.repeat(np.repeat(tm, 3, 0), 3, 1)
        sx0 = int((66.0 - z0) * ppm)
        sm = K.place(tm, w, h, sx0, int((Ytop - 24.2) * ppm))
        p.put(((Y >= 21.4) & (Y < 21.7) & (Z > 65.5) & (Z < 66.0 + tm.shape[1] / ppm)), 'D', 2.0)
        p.put(sm, 'D', 1.6)
    # glass: dark, the sky reflected a little toward the top of each pane
    p.put(glass, 'G', 1.2 + (nz * 1.5)[glass] if False else 1.0 + nz[glass] * 1.6)
    p.put(sills, 'S', 5.2 + nz[sills])
    p.resolve(band=2.0)
    alpha = np.ones((h, w), bool)
    if kind == 'nord':
        alpha = (Y < 21.55) | sm | ((Y >= 21.4) & (Y < 21.7) & (Z > 65.5) & (Z < 66.0 + tm.shape[1] / ppm))
    else:
        alpha = Y < 24.2 - np.abs(np.mod(Z, 4.0) - 2.0) * 0.0
    out = p.L.c.copy()
    out[~alpha] = 0
    return out, ppm, Ytop


def _palais(a):
    """Frontal palais at Z = 150 painted straight into the float RGB canvas (scale 2.4 px per metre)."""
    s = SQ['f'] / PALAIS_Z
    yy, xx = grid()
    X = (xx + 0.5 - SQ['cx']) / s
    Y = SQ['H'] - (yy + 0.5 - SQ['yh']) / s
    wall = np.array([16, 22, 32], np.float32)
    body = (np.abs(X) < 38) & (Y >= 0) & (Y < 17.5)
    centre = (np.abs(X) < 12) & (Y >= 0) & (Y < 21.0)
    drum = (np.abs(X) < 6.0) & (Y >= 21) & (Y < 25.5)
    dome = (np.hypot(X / 7.4, (Y - 25.5) / 9.0) < 1.0) & (Y >= 25.5)
    lantern = (np.abs(X) < 1.0) & (Y >= 34.0) & (Y < 37.5)
    sil = body | centre | drum | dome | lantern
    a[sil] = wall
    a[dome] = np.array([20, 34, 34], np.float32)                     # patina
    a[dome & (np.mod(X + 40, 2.0) < 0.35)] = np.array([30, 46, 44], np.float32)
    snow = (sil & ~C.shift(sil, 0, -1)) | (dome & (Y > 31.5))
    a[snow] = np.array([150, 160, 172], np.float32)
    for yl in (17.5, 21.0):
        ledge = (np.abs(Y - yl) < 0.42) & (np.abs(X) < (38 if yl < 18 else 12))
        a[ledge] = np.array([120, 130, 144], np.float32)
    # windows: west wing and centre partly lit, the east wing dark but for one high window
    for xc in np.arange(-36.0, 37.0, 3.0):
        for (y0, y1) in ((1.2, 3.6), (6.0, 9.0), (11.0, 14.5)):
            m = (np.abs(X - xc) < 0.7) & (Y >= y0) & (Y < y1) & body
            east = xc > 13.0
            lit = (not east) and ((int(xc * 7 + y0 * 3) % 5) in (0, 2)) and xc < -14 or (abs(xc) < 3 and y0 < 2)
            if east and abs(xc - 30.0) < 0.1 and y0 > 10:
                a[m] = np.array([60, 44, 26], np.float32)               # one dim window high up in the dark wing
            elif lit:
                a[m] = np.array([170, 120, 64], np.float32)
            else:
                a[m] = np.array([9, 12, 18], np.float32)
    # portico columns, lamps either side of the steps
    for xc in np.arange(-7.5, 8.0, 3.0):
        a[(np.abs(X - xc) < 0.45) & (Y >= 0.8) & (Y < 9.5)] = np.array([44, 52, 64], np.float32)
    a[(np.abs(X) < 9.0) & (Y >= 9.5) & (Y < 10.6)] = np.array([60, 68, 80], np.float32)
    return sil


def _ground_color(X, Z, nz):
    """Snow of the square at (X, Z) (float RGB): trodden paths, tram rails, lamp pools."""
    base = np.array([58, 70, 88], np.float32)
    fog = np.clip((Z - 30) / 130, 0, 1)[..., None]
    c = base[None] * (0.82 + 0.28 * nz[..., None])
    # pavements along the facades and the street at the far end (trodden, bluer)
    pave = (np.abs(np.abs(X) - 21.8) < 2.0) | ((Z > 97) & (Z < 112))
    c = np.where(pave[..., None], c * 0.80 + np.array([2, 4, 10]) * 1.0, c)
    # the walked diagonal from the station steps to the two hotel doors
    for (dx, dz) in (DOOR_K, DOOR_A):
        t = np.clip(((X - 0) * dx + (Z - 18) * (dz - 18)) / (dx * dx + (dz - 18) ** 2), 0, 1)
        d = np.hypot(X - t * dx, Z - (18 + t * (dz - 18)))
        c = np.where((d < 0.55)[..., None], c * 0.93, c)
    # tram rails (two tracks), half buried
    for rx in (-3.4, -2.0, 2.0, 3.4):
        m = (np.abs(X - rx) < 0.06 + Z * 0.0009) & (nz > 0.32)
        c = np.where(m[..., None], np.array([20, 24, 32], np.float32)[None], c)
    # lamp pools
    for lx in (-12.0, 12.0):
        for lz in (32.0, 52.0, 72.0, 92.0):
            d = np.hypot(X - lx, Z - lz)
            g = np.clip(1 - d / 7.0, 0, 1) ** 1.6
            c = c + g[..., None] * np.array([120, 72, 30], np.float32)
    c = c * (1 - 0.35 * fog) + fog * np.array([22, 28, 40], np.float32) * 0.35
    return c


def square_bg():
    """r1/r6 background: sky, palais, square, both hotels (supersampled perspective, re-quantised)."""
    ss = 3
    yy, xx = _ss_grid(ss)
    f, H, yh, cx = SQ['f'], SQ['H'], SQ['yh'], SQ['cx']
    rgb = np.zeros((VH * ss, VW * ss, 3), np.float32)
    # sky: overcast night, a warm city glow low over the palais
    sky = np.array([10, 13, 22], np.float32)[None, None] + (np.clip((yy - 30) / 110, 0, 1)[..., None]
                                                         * np.array([14, 14, 18], np.float32))
    rgb[:] = sky
    gl = np.clip(1 - np.hypot((xx - 330) / 260, (yy - 130) / 70), 0, 1) ** 1.6
    rgb += gl[..., None] * np.array([26, 18, 12], np.float32)
    # ground plane
    below = yy > yh + 0.5
    Zg = np.where(below, f * H / np.maximum(yy - yh, 0.5), 1e6)
    Xg = (xx - cx) * Zg / f
    nz = pg.value_noise(VW * ss, VH * ss, 30, 411, octaves=3)
    gcol = _ground_color(Xg, Zg, nz)
    rgb = np.where(below[..., None], gcol, rgb)
    rgb = _down(rgb, ss)
    # the palais and the far street (frontal, painted at 1x), lime trees in front of it
    _palais(rgb)
    yy1, xx1 = grid()
    for tx in (-30.0, -20.0, 18.0, 28.0):
        for tz in (112.0, 128.0):
            bx, by = sq(tx, 0.0, tz)
            top = sq(tx, 7.5, tz)[1]
            s = f / tz
            trunk = (np.abs(xx1 + 0.5 - bx) < max(0.6, 0.18 * s)) & (yy1 < by) & (yy1 > by - 2.6 * s)
            crown = (np.hypot((xx1 + 0.5 - bx) / (3.2 * s), (yy1 + 0.5 - (top + 2.4 * s)) / (2.6 * s)) < 1.0)
            twig = crown & (pg.value_noise(VW, VH, 2.2, int(abs(tx) * 10 + tz + (500 if tx < 0 else 0)), octaves=2) > 0.58)
            rgb[trunk | twig] = np.array([12, 15, 22], np.float32)
            rgb[twig & (pg.value_noise(VW, VH, 1.6, int(tz), octaves=1) > 0.72)] = np.array([96, 106, 120],
                                                                                             np.float32)
    # facades (supersampled warp of the flat textures)
    for kind, sign in (('europa', -1.0), ('nord', 1.0)):
        tex, ppm, Ytop = _facade_tex(kind)
        th, tw = tex.shape[:2]
        side = (xx - cx) * sign > 0.5
        Zf = np.where(side, f * (HOTEL_X * sign) / np.where(side, xx - cx, 1.0), -1.0)
        Yf = H - (yy - yh) * Zf / f
        u = ((Zf - HOTEL_Z[0]) * ppm).astype(np.int32)
        v = ((Ytop - Yf) * ppm).astype(np.int32)
        ok = side & (u >= 0) & (u < tw) & (v >= 0) & (v < th)
        samp = np.zeros((VH * ss, VW * ss, 4), np.float32)
        samp[ok] = tex[v[ok], u[ok]].astype(np.float32)
        a = samp[..., 3:] / 255.0
        col = _down(samp[..., :3] * a, ss)
        cov = _down(a, ss)
        m = cov[..., 0] >= 0.5
        rgb[m] = col[m] / np.maximum(cov[m], 1e-3)
    # lamp posts (in front of everything on the ground) with their lanterns
    for lx in (-12.0, 12.0):
        for lz in (32.0, 52.0, 72.0, 92.0):
            bx, by = sq(lx, 0.0, lz)
            tx, ty = sq(lx, 4.6, lz)
            w = max(1, int(round(f * 0.14 / lz)))
            rgb[int(ty):int(by), int(bx):int(bx) + w] = np.array([10, 12, 18], np.float32)
            r = max(1.0, f * 0.28 / lz)
            m = ell(bx + w / 2, ty - r * 0.4, r, r * 1.2)
            rgb[m] = np.array([250, 214, 150], np.float32)
    # advertising column (Litfaßsäule) with a snow cap
    bx, by = sq(-8.0, 0.0, 40.0)
    s = f / 40.0
    col = (np.abs(xx1 + 0.5 - bx) < 0.55 * s) & (yy1 < by) & (yy1 > by - 3.0 * s)
    rgb[col] = np.array([24, 30, 40], np.float32)
    rgb[col & (xx1 + 0.5 > bx + 0.15 * s)] = np.array([34, 42, 54], np.float32)
    for k in (0.9, 1.7, 2.4):
        rgb[col & (np.abs(yy1 + 0.5 - (by - k * s)) < 0.7)] = np.array([60, 52, 46], np.float32)
    cap = ell(bx, by - 3.0 * s - 1, 0.75 * s, 0.4 * s)
    rgb[cap] = np.array([170, 180, 192], np.float32)
    pal = sorted(set(NIGHT + SNOW + LAMP + IRON[:6] + ['#14202A', '#1E3036', '#2C4448', '#3A3226', '#5A4630',
                                                       '#7A6A58', '#A8916E', '#FCE2B0', '#3C2E24', '#6B4A2C']))
    out = Q.requant(rgb, pal, spread=14.0)
    _record_square()
    return out


def _window_quad(kind):
    z0, z1, y0, y1 = WIN_K if kind == 'konrad' else WIN_A
    X = -HOTEL_X if kind == 'konrad' else HOTEL_X
    pts = [sq(X, y1, z0), sq(X, y1, z1), sq(X, y0, z1), sq(X, y0, z0)]
    return [(round(x, 2), round(y, 2)) for (x, y) in pts]


def lit_window(kind):
    """The lit window seen from the station roof (oblique): lamp light, curtain, the man at his radio."""
    q = _window_quad(kind)
    xs = [p[0] for p in q]
    ys = [p[1] for p in q]
    x0, y0 = int(math.floor(min(xs))) - 6, int(math.floor(min(ys))) - 6
    x1, y1 = int(math.ceil(max(xs))) + 6, int(math.ceil(max(ys))) + 6
    w, h = x1 - x0, y1 - y0
    R = C.ramps(L=LAMP, N=NIGHT)
    p = C.Paint(w, h, R, 'litwin_' + kind)
    m = poly([(x - x0, y - y0) for (x, y) in q], w, h)
    yy, xx = grid(h, w)
    cxw = (xx[m].mean() if m.any() else w / 2)
    p.put(m, 'L', 4.6 - np.clip((yy - yy[m].min()) / max(1, h - 12), 0, 1) * 1.6)
    p.put(m & (np.abs(xx - cxw) < 0.6), 'N', 3.0)                            # mullion
    side = (xx < cxw - 2) if kind == 'konrad' else (xx > cxw + 2)
    p.put(m & side & (np.mod(xx, 2) == 0), 'L', 2.6)                            # curtain folds
    # the man at the table: head and shoulders against the light
    hx = cxw + (2 if kind == 'konrad' else -2)
    by = yy[m].max() if m.any() else h
    head = ell(hx, by - 5.5, 1.6, 1.9, w, h)
    sh = poly([(hx - 3.2, by + 1), (hx - 2.4, by - 3.2), (hx + 2.4, by - 3.2), (hx + 3.2, by + 1)], w, h)
    p.put((head | sh) & m, 'N', 1.0)
    p.resolve(band=2.0)
    out = p.L.c
    L['win_' + kind] = [x0, y0]
    return out


def lit_glow():
    """Additive spill of the two lit windows into the snowy air (r1)."""
    blobs = []
    for kind in ('konrad', 'alexei'):
        q = _window_quad(kind)
        cx_ = sum(p[0] for p in q) / 4
        cy_ = sum(p[1] for p in q) / 4
        blobs.append((cx_, cy_, 16, 14, (40, 26, 12), 1.8))
    for lx in (-12.0, 12.0):
        for lz in (32.0, 52.0, 72.0, 92.0):
            tx, ty = sq(lx, 4.6, lz)
            r = 1.0 + 140.0 / lz
            blobs.append((tx + 0.5, ty, r * 1.4, r * 1.2, (60, 40, 18), 1.6))
    return Q.glow_sprite(VW, VH, blobs, 6.0)


def door_open(kind):
    """r6: the hotel door opened, warm light falling onto the snow (straight RGBA, drawn over the bg)."""
    X, Z = DOOR_K if kind == 'konrad' else DOOR_A
    sgn = -1 if kind == 'konrad' else 1
    w_m = 1.0 if kind == 'konrad' else 1.3
    pts = [sq(X, 2.7, Z - w_m), sq(X, 2.7, Z + w_m), sq(X, 0.0, Z + w_m), sq(X, 0.0, Z - w_m)]
    a = np.zeros((VH, VW, 3), np.float32)
    m = poly(pts)
    yy, xx = grid()
    a[m] = np.array([236, 190, 120], np.float32)
    a[m & (yy > min(p[1] for p in pts) + 0.6 * (max(p[1] for p in pts) - min(p[1] for p in pts)))] = \
        np.array([250, 214, 150], np.float32)
    # light spill on the snow: a wedge from the door toward the square centre
    spill = [sq(X, 0, Z - w_m), sq(X, 0, Z + w_m), sq(X - sgn * 7.0, 0, Z + w_m * 2.6), sq(X - sgn * 7.0, 0, Z - w_m * 2.2)]
    sm = poly(spill) & ~m
    d = np.clip(np.abs(xx - pts[0][0]) / 60.0, 0, 1)
    g = (1 - d) ** 1.5
    th = pg.bayer(VW, VH, 1, 2)
    sel = sm & (g > th * 0.9)
    a[sel] = np.array([96, 72, 46], np.float32) + g[sel, None] * np.array([70, 50, 24], np.float32)
    out = np.zeros((VH, VW, 4), np.uint8)
    on = m | sel
    pal = LAMP + ['#5A4630', '#7A5E40', '#9A7650', '#6B4A2C']
    q = Q.requant(a, pal, spread=10.0)
    out[on] = q[on]
    ys, xs = np.nonzero(on)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    L['door_' + kind] = [int(x0), int(y0)]
    return out[y0:y1, x0:x1]


def walker(kind):
    """r6: a tiny man walking away from the camera, 4 frames (back view), ~13/11 px."""
    hgt = 15 if kind == 'konrad' else 13
    fw, fh = 11, hgt + 3
    frames = []
    for i in range(4):
        R = C.ramps(N=NIGHT, K=K_COAT, A=A_COAT, F=A_FUR, H=['#0E0D12', '#1F1A22', '#2D2D36'], S=SNOW,
                    L=LAMP)
        p = C.Paint(fw, fh, R, 'walker')
        cx = fw / 2
        ph = i / 4 * 2 * math.pi
        step = math.sin(ph)
        bob = 0 if i % 2 == 0 else -1
        top = 2 + bob
        coat = 'K' if kind == 'konrad' else 'A'
        legy = top + int(hgt * 0.62)
        for s_, k in ((-1, step), (1, -step)):
            lx = cx + s_ * 1.0 + k * 0.8
            p.put(p.box(int(lx) - (1 if s_ < 0 else 0), legy, int(lx) + (1 if s_ > 0 else 0) + 1,
                        min(fh, top + hgt + int(max(0, -k) * 0)) ), 'N', 1.0)
        body = poly([(cx - 2.6, top + 4), (cx + 2.6, top + 4), (cx + 3.1, legy + 1), (cx - 3.1, legy + 1)], fw, fh)
        p.put(body, coat, 2.0)
        p.put(body & (p.xx > cx + 1), coat, 3.2)                                   # lamp-lit side
        if kind == 'konrad':
            p.put(ell(cx, top + 2.6, 1.4, 1.7, fw, fh), 'N', 2.0)
            p.put(p.box(int(cx) - 2, top + 1, int(cx) + 3, top + 2), 'H', 1.0)    # hat brim
            p.put(p.box(int(cx) - 1, top, int(cx) + 2, top + 1), 'H', 1.6)
        else:
            p.put(ell(cx, top + 2.4, 2.0, 2.0, fw, fh), 'F', 2.4)                  # ushanka
            p.put(p.box(int(cx) - 2, top + 3, int(cx) + 3, top + 5), 'F', 1.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


def _record_square():
    L['sq'] = dict(SQ)
    L['door_konrad_xz'] = list(DOOR_K)
    L['door_alexei_xz'] = list(DOOR_A)
    # walker paths: screen position + figure height every 0.1 s, footprints every 0.37 m (alternating)
    for kind, (X0, Z0), speed in (('konrad', DOOR_K, 1.7), ('alexei', DOOR_A, 1.6)):
        X0 = X0 + (1.4 if X0 < 0 else -1.4)          # the first step out of the door, off the pavement edge
        ex, ez = EAST_WING
        dx, dz = ex - X0, ez - Z0
        n = math.hypot(dx, dz)
        ux, uz = dx / n, dz / n
        path, prints = [], []
        for i in range(0, 61):
            d = i * 0.1 * speed
            X, Z = X0 + ux * d, Z0 + uz * d
            x, y = sq(X, 0.0, Z)
            path.append([round(x, 2), round(y, 2), round(SQ['f'] * 1.8 / Z, 2)])
        k = 0
        d = 0.2
        while d < 6.0 * speed:
            side = 0.13 if k % 2 == 0 else -0.13
            X, Z = X0 + ux * d - uz * side, Z0 + uz * d + ux * side
            x, y = sq(X, 0.0, Z)
            prints.append([round(x, 2), round(y, 2), round(d / speed, 3)])
            d += 0.37
            k += 1
        L['path_' + kind] = path
        L['prints_' + kind] = prints


def steam():
    """r1: steam of the 23.40 drifting from the station below the camera (6 frames, 120 x 72)."""
    return K.puff_sheet(6, 120, 72, ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796'], 4401,
                        grow=(0.30, 0.50), thin=0.62, light=(0.3, -0.8), drift=0.05)


# ======================================================================================= the rooms (r2/r3)
WIN = (168, 52, 492, 214)            # window opening (x0, y0, x1, y1) - identical in both rooms
MULLION = 330
RADIO_AT = (278, 134)                # top-left of the radio sprite in both rooms
DIAL = (330, 182)                    # dial centre (absolute) - the match cut
DIAL_R = 24
TABLE_Y = 236                        # front edge of the tabletop


def radio():
    """The Bakelite table radio (shared by both rooms): dial left, cloth grille right, knobs, piano keys."""
    w, h = 172, 104
    R = C.ramps(B=BAKE, C=['#2A1E14', '#4A3826', '#6A5236', '#8C7048', '#A88A5C', '#C2A576', '#E0C894'],
                G=['#1E140E', '#3A2A1C', '#55402A', '#6E5638', '#8A6E48'], K=['#1A1410', '#3A3024', '#6E604A',
                                                                             '#A69878', '#D8CCAE', '#F0E8D2'],
                M=BRASS, N=NIGHT)
    p = C.Paint(w, h, R, 'radio')
    yy, xx = p.yy, p.xx
    arch = 6.0 + 7.0 * ((xx + 0.5 - w / 2) / (w / 2)) ** 2
    body = (yy >= arch) & (yy < h - 2) & (xx >= 0) & (xx < w)
    body &= ~((xx < 3) & (yy > h - 6)) & ~((xx > w - 4) & (yy > h - 6))
    lit = np.clip(1.0 - (xx / w) * 0.6, 0, 1) + np.clip((26 - yy) / 26, 0, 1) * 0.8
    p.put(body, 'B', 2.6 + lit * 1.9)
    p.put(body & (yy < arch + 2), 'B', 6.2 - (xx / w) * 1.6)                     # polished top edge
    p.put(body & (xx < 2), 'B', 5.0)
    p.put(body & (yy >= h - 5), 'B', 1.2)                                         # foot
    # dial bezel + glass (warm backlight); the needle is drawn at runtime
    dx, dy = DIAL[0] - RADIO_AT[0], DIAL[1] - RADIO_AT[1]
    r = np.hypot(xx + 0.5 - dx, yy + 0.5 - dy)
    p.put(body & (r < DIAL_R + 3), 'M', 3.4 - (yy - dy) / DIAL_R * 1.2)
    p.put(body & (r < DIAL_R + 1), 'M', 1.4)
    face = body & (r < DIAL_R)
    p.put(face, 'C', 4.6 - r[face] / DIAL_R * 1.8)
    ang = (np.degrees(np.arctan2(xx + 0.5 - dx, -(yy + 0.5 - dy))) + 360) % 360
    ring = face & (r > DIAL_R - 6) & (r < DIAL_R - 5)
    p.put(ring & ((ang < 140) | (ang > 220)), 'G', 1.2)
    for k in range(-13, 14):
        a = (k * 10) % 360
        tick = face & (r > DIAL_R - 6 - (2 if k % 3 == 0 else 0)) & (r < DIAL_R - 2) & \
            (np.abs(((ang - a + 180) % 360) - 180) < (2.4 if k % 3 == 0 else 1.2))
        p.put(tick, 'G', 0.8)
    # the two Veltrava services: a red mark (I, russisch) and a blue one (II, deutsch)
    for a, col in ((300.0, 'red'), (40.0, 'blue')):
        mk = face & (r > DIAL_R - 4.5) & (r < DIAL_R - 1.5) & (np.abs(((ang - a + 180) % 360) - 180) < 5.5)
        if col == 'red':
            p.put(mk, 'B', 7.0)
        else:
            p.put(mk, 'N', 6.0)
    p.put(face & (r < 3.2), 'M', 2.0)                                              # needle hub
    # the maker's name on a small plate under the dial (the needle stays the only thing moving on the glass)
    tm = K.vtext('KOMET', 's', 1)
    sm = K.place(tm, w, h, int(dx - tm.shape[1] / 2), int(dy + DIAL_R + 4))
    p.put(body & (np.abs(xx - dx) < 12) & (yy >= dy + DIAL_R + 4) & (yy < dy + DIAL_R + 11), 'M', 2.6)
    p.put(sm & body, 'B', 1.0)
    # cloth grille behind a Bakelite fret
    gx0, gx1, gy0, gy1 = 92, 162, 18, 80
    grille = body & (xx >= gx0) & (xx < gx1) & (yy >= gy0) & (yy < gy1)
    weave = ((xx.astype(int) + yy.astype(int)) % 2 == 0)
    p.put(grille, 'G', 2.0 + weave[grille] * 0.6 + (1 - (xx[grille] - gx0) / (gx1 - gx0)) * 0.8)
    for bx in range(gx0 + 6, gx1 - 2, 9):
        bar = grille & (xx >= bx) & (xx < bx + 3)
        p.put(bar, 'B', 3.6 - (bx - gx0) / 70.0)
        p.put(bar & (xx == bx), 'B', 5.4)
    p.put(body & (xx >= gx0 - 2) & (xx < gx1 + 2) & ((yy == gy0 - 1) | (yy == gy1)), 'B', 5.2)
    # magic eye above the grille (green; drawn brighter at runtime), maker's badge
    p.put(body & (np.hypot(xx + 0.5 - 127, yy + 0.5 - 11) < 3.6), 'M', 1.5)
    p.put(body & (np.hypot(xx + 0.5 - 127, yy + 0.5 - 11) < 2.4), 'N', 0.0)
    p.put(body & (xx >= 112) & (xx < 142) & (yy >= 84) & (yy < 86), 'M', 3.0)
    # knobs (volume, tuning) and four ivory piano keys
    for kx in (22, 70):
        kn = body & (np.hypot(xx + 0.5 - kx, yy + 0.5 - 90) < 6.5)
        p.put(kn, 'B', 1.6 + np.clip((92 - yy[kn]) / 6, 0, 1) * 4.0)
        p.put(kn & (np.hypot(xx + 0.5 - kx + 1.5, yy + 0.5 - 87.5) < 1.5), 'B', 7.0)
    for i in range(4):
        kx0 = 98 + i * 15
        key = body & (xx >= kx0) & (xx < kx0 + 12) & (yy >= 88) & (yy < 96)
        p.put(key, 'K', 4.2 - (i * 0.2))
        p.put(key & (yy >= 94), 'K', 2.0)
    p.resolve(band=2.0)
    out = p.L.c
    L['radio'] = list(RADIO_AT)
    L['dial'] = list(DIAL)
    L['dial_r'] = DIAL_R
    L['knob_tune'] = [RADIO_AT[0] + 70, RADIO_AT[1] + 90]
    L['magic_eye'] = [RADIO_AT[0] + 127, RADIO_AT[1] + 11]
    return out


def _view_facade(p, kind, lit_xy):
    """The hotel across the square seen through the window (frontal, ~5 px per metre), one lit window."""
    yy, xx = p.yy, p.xx
    x0, y0, x1, y1 = WIN
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    # night sky above the roofline, the facade, the snowy square at the bottom of the view
    sky = inside & (yy < 84)
    p.put(sky, 'N', 1.2 + (yy[sky] - y0) / 40.0)
    fac = inside & (yy >= 84) & (yy < 190)
    nz = Q.noise(VW, VH, 9, 503)
    p.put(fac, 'F', 1.6 + nz[fac] * 0.9)
    if kind == 'europa':                                           # mansard + dormers, ornate cornice
        p.put(inside & (yy >= 70) & (yy < 84) & (np.abs(np.mod(xx, 26) - 13) < 13 - (84 - yy) * 0.2), 'F', 0.8)
        p.put(inside & (yy >= 68) & (yy < 71), 'S', 4.0)
        p.put(inside & (yy >= 84) & (yy < 87), 'F', 3.6)
        p.put(inside & (yy >= 87) & (yy < 88), 'S', 5.6)
        cols, rows, ww, wh = 20, ((96, 114), (124, 142), (152, 170)), 7, 15
    else:                                                          # flat roof with parapet
        p.put(inside & (yy >= 80) & (yy < 84), 'F', 3.0)
        p.put(inside & (yy >= 79) & (yy < 80), 'S', 6.0)
        cols, rows, ww, wh = 17, ((92, 104), (112, 124), (132, 144), (152, 164)), 8, 11
    for cxw in range(x0 + 8, x1, cols):
        for (ry0, ry1) in rows:
            win = inside & (xx >= cxw) & (xx < cxw + ww) & (yy >= ry0) & (yy < ry1)
            p.put(win, 'N', 1.0)
            p.put(inside & (xx >= cxw - 1) & (xx < cxw + ww + 1) & (yy == ry1), 'S', 5.0)   # snow on the sill
    # the lit window of the other man, his silhouette at his own radio
    lx, ly = lit_xy
    lwin = inside & (xx >= lx) & (xx < lx + ww) & (yy >= ly) & (yy < ly + wh)
    p.put(lwin, 'L', 5.2 - (yy[lwin] - ly) / wh * 1.4)
    p.put(lwin & (np.abs(xx - (lx + ww // 2)) < 0.6), 'F', 2.0)
    hx = lx + ww * (0.32 if kind == 'europa' else 0.68)
    head = ell(hx, ly + wh - 5.0, 1.5, 1.8) | poly([(hx - 3, ly + wh), (hx - 2.2, ly + wh - 3.2),
                                                     (hx + 2.2, ly + wh - 3.2), (hx + 3, ly + wh)])
    p.put(head & lwin, 'N', 1.4)
    ground = inside & (yy >= 190)
    p.put(ground, 'S', 3.0 + nz[ground] * 1.2 + (yy[ground] - 190) / 24.0)
    return lwin


def _room(kind):
    """Shared room geometry: back wall, the window with its view, tabletop.  Returns the Paint."""
    europa = kind == 'konrad'
    R = C.ramps(N=NIGHT, S=SNOW, L=LAMP, F=['#06080D', '#0A0E16', '#10161F', '#161E29', '#1F2834', '#2A3542'],
                W=(['#100A0A', '#1A0F10', '#261616', '#331D1C', '#432826', '#563532'] if europa else
                   ['#0A0E0E', '#111818', '#192222', '#222E2D', '#2D3A39', '#3B4A48']),
                D=(['#0C0807', '#170F0B', '#231710', '#311F15', '#43291B', '#5A3824'] if europa else
                   ['#080B0B', '#0F1514', '#162020', '#1E2A29', '#283634', '#344543']),
                O=OAK, P=PAPER, M=BRASS, T=(['#14080A', '#22100F', '#341815', '#4A221C', '#622E22'] if europa else
                                            ['#1A1A18', '#2C2B27', '#403D36', '#58544A', '#726C5E', '#8E8774']),
                B=BAKE, G=['#0A0F12', '#121A1F', '#1C262C', '#283439', '#36444A'], K=K_COAT, A=A_COAT, U=A_FUR,
                H=['#0E0D12', '#1F1A22', '#2D2D36', '#3D3639', '#4B4547'])
    p = C.Paint(VW, VH, R, 'room_' + kind)
    yy, xx = p.yy, p.xx
    x0, y0, x1, y1 = WIN
    nz = Q.noise(VW, VH, 14, 611 if europa else 612)
    # light: the radio dial (warm, centre), the desk lamp (Konrad, left), the window (cold)
    warm = Q.lightfield(VW, VH, [(DIAL[0], DIAL[1], 200, 1.0, 1.6)] +
                        ([(190, 150, 300, 1.4, 1.3)] if europa else []))
    cold = np.clip(1 - np.hypot((xx - (x0 + x1) / 2) / 300, (yy - 140) / 200), 0, 1) ** 1.4
    wall = np.ones((VH, VW), bool)
    p.put(wall, 'W', 0.6 + warm * 2.8 + cold * 0.8 + nz * 0.4)
    if europa:
        # damask: a dithered diamond lattice in the wallpaper, wainscot below the window line
        lat = (np.abs(np.mod(xx + yy * 0.5, 18) - 9) + np.abs(np.mod(yy, 24) - 12) * 0.75) < 4.2
        p.put(lat & (yy < 210), 'W', 0.2 + warm[lat & (yy < 210)] * 2.4 + cold[lat & (yy < 210)] * 0.6)
        wain = yy >= 214
        p.put(wain, 'D', 0.8 + warm[wain] * 3.0)
        p.put((yy >= 214) & (yy < 217), 'D', 2.2 + warm[(yy >= 214) & (yy < 217)] * 2.4)
    else:
        dado = yy >= 200
        p.put(dado, 'W', 0.3 + warm[dado] * 2.2 + cold[dado] * 0.4)
        p.put((yy >= 199) & (yy < 201), 'W', 2.2 + warm[(yy >= 199) & (yy < 201)] * 2.0)
    # the window: reveal, frame, the view, glazing bars
    reveal = (xx >= x0 - 10) & (xx < x1 + 10) & (yy >= y0 - 8) & (yy < y1 + 6)
    p.put(reveal, 'W', 1.2 + warm[reveal] * 2.6 + cold[reveal] * 1.6)
    lwin = _view_facade(p, 'europa' if not europa else 'nord', (420, 124) if not europa else (230, 112))
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    frame = inside & ((np.abs(xx - MULLION) < 3) | (xx < x0 + 4) | (xx >= x1 - 4) | (yy < y0 + 4) |
                      (np.abs(yy - 92) < 2) | (yy >= y1 - 5))
    p.put(frame, 'G' if not europa else 'D', 1.4 + warm[frame] * 2.6 + cold[frame] * 0.8)
    p.put(inside & (yy >= y1 - 6) & (yy < y1 - 4), 'S', 5.0)                          # snow on the outer sill
    # curtains
    for side in (-1, 1):
        cx0 = x0 - 16 if side < 0 else x1 - 30
        cur = (xx >= cx0) & (xx < cx0 + 46) & (yy >= y0 - 14) & (yy < 226)
        cur &= (xx < x0 + 30) if side < 0 else (xx >= x1 - 30)
        fold = np.sin((xx - cx0) * 0.55) * 0.8
        if europa:
            p.put(cur, 'T', 1.2 + fold[cur] + warm[cur] * 2.6)
        else:
            p.put(cur & (np.mod(xx, 3) != 0), 'T', 1.5 + fold[cur & (np.mod(xx, 3) != 0)] + cold[cur & (np.mod(xx, 3) != 0)] * 2.0 + warm[cur & (np.mod(xx, 3) != 0)] * 1.6)
    # the table
    top = (yy >= TABLE_Y - 12) & (yy < TABLE_Y) & (xx >= 120) & (xx < 560)
    p.put(top, 'O', 2.0 + warm[top] * 4.0 + cold[top] * 0.6 + (yy[top] - TABLE_Y + 12) / 14.0)
    p.put((yy >= TABLE_Y) & (yy < TABLE_Y + 6) & (xx >= 120) & (xx < 560), 'O', 1.4 +
          warm[(yy >= TABLE_Y) & (yy < TABLE_Y + 6) & (xx >= 120) & (xx < 560)] * 2.4)
    under = (yy >= TABLE_Y + 6) & (xx >= 120) & (xx < 560)
    p.put(under, 'O', 0.3)
    for lx in (132, 540):
        leg = (xx >= lx) & (xx < lx + 8) & (yy >= TABLE_Y + 6)
        p.put(leg, 'O', 1.0 + warm[leg] * 1.4)
    if not europa:
        # a crocheted doily under the radio, the tea glass in its holder, sugar on a saucer
        doily = ell(328, TABLE_Y - 5, 112, 8)
        p.put(doily & ((xx.astype(int) + yy.astype(int)) % 3 != 0), 'P', 3.0 + warm[doily & ((xx.astype(int) + yy.astype(int)) % 3 != 0)] * 2.4)
        gx = 476
        glass = (np.abs(xx + 0.5 - gx) < 9 - (TABLE_Y - yy) * 0.03) & (yy >= TABLE_Y - 34) & (yy < TABLE_Y - 3)
        p.put(glass, 'L', 2.6 + warm[glass] * 2.0 - (yy[glass] - (TABLE_Y - 34)) / 30.0)
        tea = glass & (yy >= TABLE_Y - 28)
        p.put(tea, 'L', 3.2 + warm[tea] * 1.4)
        p.put(glass & (np.abs(xx + 0.5 - (gx - 6)) < 1), 'S', 7.0)
        holder = (np.abs(xx + 0.5 - gx) < 10) & (yy >= TABLE_Y - 18) & (yy < TABLE_Y - 2)
        lace = holder & (np.mod(xx + yy, 4) < 2)
        p.put(holder, 'M', 1.8 + warm[holder] * 2.4)
        p.put(lace, 'M', 3.6)
        handle = (np.abs(np.hypot(xx + 0.5 - (gx + 11), yy + 0.5 - (TABLE_Y - 12)) - 5) < 1.2) & (xx > gx + 10)
        p.put(handle, 'M', 2.6)
        p.put((np.abs(xx + 0.5 - (gx + 2)) < 0.6) & (yy >= TABLE_Y - 42) & (yy < TABLE_Y - 28), 'M', 4.0)  # spoon
        sau = ell(gx + 30, TABLE_Y - 3, 12, 3)
        p.put(sau, 'P', 4.0)
        p.put(box(gx + 26, TABLE_Y - 8, gx + 30, TABLE_Y - 4) | box(gx + 31, TABLE_Y - 7, gx + 35, TABLE_Y - 3), 'P', 6.0)
        # his coat on the hook at the right wall: quilted green, the ushanka hung above it
        coat = poly([(596, 118), (604, 112), (618, 116), (632, 132), (640, 150), (640, 262), (588, 262), (584, 200),
                     (586, 140)])
        quilt = coat & (np.mod(yy + np.abs(xx - 612) * 0.2, 10) < 1.2)
        p.put(coat, 'A', 1.4 + cold[coat] * 1.6 + warm[coat] * 1.2)
        p.put(quilt, 'A', 0.6 + cold[quilt] * 1.0)
        p.put(coat & (xx < 592), 'A', 2.4 + cold[coat & (xx < 592)] * 1.4)
        hook = box(607, 92, 610, 112)
        p.put(hook, 'M', 2.0)
        hat = ell(608, 92, 13, 9) | poly([(594, 92), (590, 112), (598, 112), (600, 96)]) |             poly([(622, 92), (626, 112), (618, 112), (616, 96)])
        p.put(hat, 'U', 1.6 + nz[hat] * 1.4 + cold[hat] * 1.6)
        p.put(hat & ~C.shift(hat, 0, -1), 'U', 4.2)
    else:
        # a fine desk: blotter, notepad, his hat at the left, the desk lamp with a cream shade
        p.put(box(380, TABLE_Y - 10, 560, TABLE_Y - 2), 'D', 1.6 + warm[box(380, TABLE_Y - 10, 560, TABLE_Y - 2)] * 2.0)
        pad = poly([(424, TABLE_Y - 9), (500, TABLE_Y - 9), (506, TABLE_Y - 2), (418, TABLE_Y - 2)])
        p.put(pad, 'P', 4.4 + warm[pad] * 1.4)
        for ly in (TABLE_Y - 7, TABLE_Y - 5, TABLE_Y - 3):
            p.put(pad & (yy == ly) & (np.mod(xx, 7) < 5) & (xx < 470 - (ly - TABLE_Y) * 0), 'P', 2.4)
        hat = ell(176, TABLE_Y - 8, 26, 5) | ell(176, TABLE_Y - 14, 15, 8)
        p.put(hat, 'H', 1.2 + warm[hat] * 2.6)
        p.put(ell(176, TABLE_Y - 11, 15.5, 1.6) & hat, 'H', 0.4)
        # lamp: brass foot, stem, cream shade (glow sprite on top at runtime)
        p.put(ell(206, TABLE_Y - 4, 12, 3), 'M', 3.6)
        p.put(box(204, 150, 208, TABLE_Y - 4), 'M', 3.0)
        shade = poly([(186, 132), (226, 132), (236, 156), (176, 156)])
        p.put(shade, 'P', 5.0)
        p.put(shade & (yy >= 152), 'P', 6.0)
        # his coat and scarf on the stand at the far left
        stand = box(46, 70, 50, 314)
        p.put(stand, 'O', 1.6)
        coat = poly([(30, 92), (64, 88), (74, 140), (78, 270), (22, 272), (26, 140)])
        p.put(coat, 'K', 1.4 + warm[coat] * 1.6)
        sc = poly([(38, 96), (58, 94), (54, 170), (44, 172)])
        p.put(sc, 'P', 2.6 + warm[sc] * 1.4)
    p.resolve(band=2.0)
    L['lit_view_' + kind] = [int(v) for v in ((420, 124) if not europa else (230, 112))]
    return p


def room(kind):
    return _room(kind).L.c


def dial_glow():
    """Additive amber light of the dial on the radio front, the table and the near wall."""
    return Q.glow_sprite(VW, VH, [(DIAL[0], DIAL[1], 30, 30, (70, 48, 20), 1.4),
                                  (DIAL[0], TABLE_Y - 4, 90, 10, (44, 28, 10), 1.6),
                                  (DIAL[0], DIAL[1], 130, 90, (18, 12, 5), 1.2)], 6.0)


def lamp_glow():
    return Q.glow_sprite(VW, VH, [(206, 158, 70, 50, (60, 42, 18), 1.5), (206, 145, 22, 14, (80, 60, 30), 1.2),
                                  (300, TABLE_Y - 4, 170, 12, (40, 28, 12), 1.5)], 6.0)


def magic_eye():
    """3 frames of the green tuning indicator: open (searching), half, closed (tuned)."""
    fw, fh = 7, 7
    out = np.zeros((fh, fw * 3, 4), np.uint8)
    yy, xx = grid(fh, fw)
    r = np.hypot(xx + 0.5 - 3.5, yy + 0.5 - 3.5)
    ang = np.degrees(np.arctan2(xx + 0.5 - 3.5, -(yy + 0.5 - 3.5)))
    for i, gap in enumerate((70.0, 36.0, 6.0)):
        a = np.zeros((fh, fw, 3), np.float32)
        disc = r < 2.6
        a[disc] = np.array([60, 190, 120], np.float32)
        a[disc & (np.abs(ang) < gap)] = np.array([14, 40, 26], np.float32)
        a[r < 0.9] = np.array([20, 50, 30], np.float32)
        out[:, i * fw:(i + 1) * fw] = K.soft_quant(a, 6.0)
    return out


def steam_tea():
    """6 frames of steam rising from the tea glass (light, thin)."""
    fw, fh = 18, 34
    out = np.zeros((fh, fw * 6, 4), np.uint8)
    yy, xx = grid(fh, fw)
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        cxs = fw / 2 + np.sin(ph + (fh - yy) * 0.22) * (1 + (fh - yy) * 0.12)
        d = np.abs(xx + 0.5 - cxs)
        dens = np.clip(1 - d / 1.6, 0, 1) * np.clip((yy - 2) / 10, 0, 1) * np.clip((fh - yy) / 6, 0, 1)
        m = dens > pg.bayer(fw, fh, i, i * 2) * 0.9 + 0.08
        fr = np.zeros((fh, fw, 4), np.uint8)
        fr[m, :3] = hexrgb('#7D8796').astype(np.uint8)
        fr[m & (dens > 0.75), :3] = hexrgb('#A1AAB7').astype(np.uint8)
        fr[m, 3] = 255
        out[:, i * fw:(i + 1) * fw] = fr
    L['steam_tea'] = [467, TABLE_Y - 66]
    return out


def arm_alexei():
    """Alexei's right arm reaching for the tuning knob: 4 frames (0 = out of the shot).  The arm comes from
    behind his body (the figure is drawn over its root); knit sleeve lit by the dial from above-right."""
    kx, ky = L.get('knob_tune', [348, 224])
    x0, y0, w, h = 200, 168, 160, 72
    R = C.ramps(K=['#08090B', '#121418', '#1D2025', '#2A2E34', '#3A3E44', '#5A5450', '#7E6A56'],
                S=SKIN_A, L=LAMP)
    frames = []
    for i in range(4):
        p = C.Paint(w, h, R, 'arm_a', ox=x0, oy=y0)
        if i > 0:
            reach = (0.62, 0.96, 1.0)[i - 1]
            sh = (238.0, 190.0)                                   # shoulder, hidden behind the torso
            hx = sh[0] + (kx - 3 - sh[0]) * reach
            hy = sh[1] + (ky - 1 - sh[1]) * reach
            el = (sh[0] + (hx - sh[0]) * 0.42, max(sh[1], hy) + 9.0)
            upper = p.line([sh, el], r=7.0)
            fore = p.line([el, ((el[0] + hx) / 2, (el[1] + hy) / 2 + 1.5), (hx - 7, hy)], r=5.2)
            sleeve = upper | fore
            yy, xx = p.yy, p.xx
            lit = C.edge_light(sleeve, (0.6, -1.0), width=4.0, soft=1)
            p.put(sleeve, 'K', 1.4 + lit[sleeve] * 3.6)
            rib = sleeve & (np.mod(xx * 0.8 + yy * 0.35, 3.0) < 1.0)
            p.put(rib, 'K', 1.0 + lit[rib] * 3.0)
            p.put(sleeve & ~C.shift(sleeve, 0, 1), 'K', 0.4)                      # under side in shadow
            cuff = p.line([(hx - 10, hy), (hx - 6, hy)], r=4.4)
            p.put(cuff & ~sleeve | cuff, 'K', 2.2 + lit[cuff] * 2.0)
            turn = i == 3
            palm = p.ell(hx - 2.0, hy - 0.5, 4.6, 3.6)
            fingers = p.line([(hx - 1, hy - 3), (hx + 4, hy - 3.5 + (1 if turn else 0))], r=1.3) |                 p.line([(hx + 1, hy - 1), (hx + 5, hy + (1 if turn else 0))], r=1.2) |                 p.line([(hx - 1, hy + 2), (hx + 3, hy + 3.5 - (1 if turn else 0))], r=1.1)
            hand = palm | fingers
            hl = C.edge_light(hand, (0.7, -0.8), width=2.5, soft=1)
            p.put(hand, 'S', 1.6 + hl[hand] * 3.2)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    L['arm_alexei'] = [x0, y0]
    return Q.sheet(frames)


SKIN_A = ['#2A1C1C', '#4E302C', '#6E4440', '#8E5C50', '#B07A66', '#CC9A7E']
SKIN_K = ['#2A1C22', '#4E3036', '#6E4448', '#8E5C58', '#B47B68', '#D29A80']


def hand_konrad():
    """Konrad's right hand writing on the notepad: 4 writing frames + 1 stopped (pencil lifted)."""
    x0, y0, w, h = 404, 186, 110, 56
    R = C.ramps(K=K_COAT, S=SKIN_K, Y=['#3A2A10', '#6E5420', '#A8862E', '#D8B84A'], P=PAPER,
                W=['#2A2C32', '#5A5E66', '#9A9EA6', '#D2D4D8'])
    frames = []
    for i in range(5):
        p = C.Paint(w, h, R, 'hand_k', ox=x0, oy=y0)
        stop = i == 4
        tipx = 430 + (i % 4) * 9 if not stop else 452
        tipy = TABLE_Y - 6 - (3 if stop else 0)
        hx, hy = tipx + 12, tipy - 7
        sleeve = p.line([(520, 200), (hx + 22, hy - 4), (hx + 10, hy - 1)], r=6.0)
        p.put(sleeve, 'K', 2.4)
        p.put(sleeve & ~C.shift(sleeve, 0, -2), 'K', 4.4)
        cuff = p.line([(hx + 10, hy - 1), (hx + 6, hy)], r=4.0)
        p.put(cuff, 'W', 2.6)
        hand = p.ell(hx, hy, 6.0, 4.4) | p.line([(hx - 3, hy + 2), (tipx + 3, tipy - 1)], r=1.5)
        p.put(hand, 'S', 2.6)
        p.put(hand & ~C.shift(hand, 0, -1), 'S', 4.6)
        p.put(hand & ~C.shift(hand, 0, 1), 'S', 1.2)
        pencil = p.line([(tipx, tipy), (tipx + 14, tipy - 12)], r=0.9)
        p.put(pencil, 'Y', 2.6)
        p.put(p.line([(tipx, tipy), (tipx + 1.6, tipy - 1.4)], r=0.6), 'W', 0.4)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    L['hand_konrad'] = [x0, y0]
    L['pad_line'] = [428, TABLE_Y - 6, 466]
    return Q.sheet(frames)


# ======================================================================================= r4: doors + note
DOOR_FLOOR = 262                     # the gap line (bottom edge of both doors)


def doors():
    """Split screen: left Alexei's door (Nord, painted), right Konrad's door (Europa, panelled), from the floor."""
    R = C.ramps(N=NIGHT, L=LAMP, P=PAPER, M=BRASS,
                A=['#0F0807', '#1A0E0B', '#29150F', '#3A1D14', '#4E271A', '#663322'],     # oxblood paint
                E=['#14141A', '#25252C', '#3A3A42', '#55545A', '#727076', '#918E90'],     # cream paint at night
                F=['#0A0806', '#141009', '#21190F', '#2E2416', '#3E311E'],                 # linoleum
                C=['#120709', '#1E0C0F', '#2C1216', '#3E1A1D', '#552426'],                 # carpet
                W=['#0A0D12', '#121821', '#1B2430', '#26313F'])
    p = C.Paint(VW, VH, R, 'doors')
    yy, xx = p.yy, p.xx
    left = xx < 319
    right = xx >= 321
    gap = (yy >= DOOR_FLOOR - 4) & (yy < DOOR_FLOOR)
    for side, m, ramp, floor in ((0, left, 'A', 'F'), (1, right, 'E', 'C')):
        cx = 160 if side == 0 else 480
        dx0, dx1 = cx - 96, cx + 96
        wall = m & (yy < DOOR_FLOOR)
        p.put(wall, 'W', 0.6 + (1 - np.abs(xx - cx) / 160.0)[wall] * 0.8)
        door = m & (xx >= dx0) & (xx < dx1) & (yy < DOOR_FLOOR - 4)
        spill = np.clip(1 - (DOOR_FLOOR - yy) / 70.0, 0, 1)
        p.put(door, ramp, 1.4 + spill[door] * 1.4)
        # frame / architrave
        arch = m & (((xx >= dx0 - 12) & (xx < dx0)) | ((xx >= dx1) & (xx < dx1 + 12))) & (yy < DOOR_FLOOR)
        p.put(arch, ramp, 2.6 + spill[arch])
        if side == 1:                                                        # panels, brass kick plate
            for (px0, px1) in ((dx0 + 18, cx - 8), (cx + 8, dx1 - 18)):
                pan = (xx >= px0) & (xx < px1) & (yy >= 60) & (yy < 206)
                p.put(door & pan & ((xx < px0 + 3) | (yy < 63)), ramp, 0.6)
                p.put(door & pan & ((xx >= px1 - 3) | (yy >= 203)), ramp, 3.0 + spill[door & pan & ((xx >= px1 - 3) | (yy >= 203))])
            kick = door & (yy >= DOOR_FLOOR - 30)
            p.put(kick, 'M', 1.2 + spill[kick] * 1.6)
            p.put(kick & (yy == DOOR_FLOOR - 30), 'M', 3.4)
            plate = door & (np.abs(xx - cx) < 15) & (yy >= 30) & (yy < 42)
            p.put(plate, 'M', 2.0)
            p.put(plate & K.place(K.vtext('317', 'l', 1), VW, VH, cx - 9, 31), 'M', 0.6)
        else:                                                                # plain painted door
            for bx in (dx0 + 48, cx, dx1 - 48):
                p.put(door & (np.abs(xx - bx) < 1) & (yy < DOOR_FLOOR - 18), ramp, 0.7)
            p.put(door & (yy >= DOOR_FLOOR - 18), ramp, 2.2 + spill[door & (yy >= DOOR_FLOOR - 18)])
            p.put(door & (yy == DOOR_FLOOR - 18), ramp, 3.2)
            plate = door & (np.abs(xx - cx) < 15) & (yy >= 92) & (yy < 104)
            p.put(plate, 'M', 2.2)
            p.put(plate & K.place(K.vtext('214', 'l', 1), VW, VH, cx - 9, 93), 'M', 0.6)
            p.put(door & ell(cx + 70, 66, 4, 6), 'M', 2.0)                      # lock escutcheon
            p.put(door & ell(cx + 70, 67, 1, 2.5), 'N', 0.0)
            p.put(door & (np.mod(yy + np.abs(xx - cx) * 0.02, 13) < 0.6) & (yy < DOOR_FLOOR - 18), ramp, 1.0)
        # threshold gap: corridor light
        g = m & gap & (xx >= dx0) & (xx < dx1)
        p.put(g, 'L', 5.6 + (yy[g] - DOOR_FLOOR + 4) * 0.3)
        p.put(m & gap & ~((xx >= dx0) & (xx < dx1)), 'N', 0.5)
        # floor in perspective, the light falling onto it in a widening wedge
        fl = m & (yy >= DOOR_FLOOR)
        u = (yy - DOOR_FLOOR) / (VH - DOOR_FLOOR)
        tone = 1.0 + u * 1.6
        if side == 0:
            boards = np.mod((xx - cx) / (0.6 + u * 3.0), 18) < 1.0
            p.put(fl, floor, tone[fl])
            p.put(fl & boards, floor, tone[fl & boards] - 0.8)
        else:
            pat = (np.mod((xx - cx) / (1 + u * 2.4) + (yy - DOOR_FLOOR) * 0.8, 16) < 3)
            p.put(fl, floor, tone[fl] + 0.4)
            p.put(fl & pat, floor, tone[fl & pat] + 1.6)
        wedge = fl & (np.abs(xx - cx) < 96 + (yy - DOOR_FLOOR) * 1.6)
        lit = np.clip(1 - (yy - DOOR_FLOOR) / 52.0, 0, 1) ** 1.3
        sel = wedge & (lit > pg.bayer(VW, VH, 3, 1) * 0.85 + 0.05)
        p.put(sel, 'L', 1.4 + lit[sel] * 3.2)
    p.put((xx >= 319) & (xx < 321), 'N', 0.0)
    p.resolve(band=2.0)
    L['door_floor'] = DOOR_FLOOR
    L['door_cx'] = [160, 480]
    return p.L.c


def note_fold():
    """The folded note on the floor (seen flat from low: 46 x 14) - emerges from under the door."""
    w, h = 46, 14
    R = C.ramps(P=PAPER, L=LAMP)
    p = C.Paint(w, h, R, 'note_fold')
    sh = poly([(3, 0), (43, 0), (46, 13), (0, 13)], w, h)
    p.put(sh, 'P', 4.8 + (p.yy / h) * 1.2)
    p.put(sh & (p.yy == 0), 'P', 6.4)
    p.put(sh & (np.abs(p.yy - 7) < 0.5), 'P', 3.4)                     # the fold
    p.put(sh & (p.yy >= 2) & (p.yy < 5) & (np.abs(p.xx - 23) < 12) & (np.mod(p.xx, 3) == 0), 'P', 2.0)  # ink
    p.resolve(band=2.0)
    return p.L.c


def note_close():
    """Close-up: the note, unfolded on the floorboards, the gap light across it; two languages, block letters."""
    R = C.ramps(P=PAPER, L=LAMP, F=['#07060A', '#0E0B0D', '#171214', '#211A18', '#2C221C', '#3A2D22'],
                G=['#141418', '#24242A', '#36363C', '#4A4A50'])
    p = C.Paint(VW, VH, R, 'note_close')
    yy, xx = p.yy, p.xx
    light = np.clip(1 - np.abs((yy - 0.18 * xx) - 60) / 210.0, 0, 1)
    nz = Q.noise(VW, VH, 22, 707)
    boards = np.ones((VH, VW), bool)
    p.put(boards, 'F', 1.0 + light * 2.4 + nz * 0.8)
    p.put(np.mod(yy + xx * 0.04, 34) < 1.2, 'F', 0.3)
    paper = poly([(132, 84), (504, 74), (516, 270), (122, 282)])
    p.put(paper, 'P', 3.4 + light[paper] * 2.0 + nz[paper] * 0.6)
    crease = paper & (np.abs(yy - (178 - (xx - 132) * 0.025)) < 1.0)
    p.put(crease, 'P', 2.4)
    p.put(paper & (yy > 178 - (xx - 132) * 0.025) & (yy < 186 - (xx - 132) * 0.025), 'P', 3.0 + light[paper & (yy > 178 - (xx - 132) * 0.025) & (yy < 186 - (xx - 132) * 0.025)] * 1.6)
    p.put(paper & ~C.shift(paper, 0, 2), 'P', 1.6)                                # the paper's shadow edge
    lines = [(Q.locale('cin.c3p2.radio.note_ru'), 0), (Q.locale('cin.c3p2.radio.note'), 1)]
    ty = 102
    for txt, k in lines:
        parts = _split_note(txt)
        for j, ln in enumerate(parts):
            tm = Q.hand_text(ln.upper(), scale=2, slant=0.18, seed=17 + k * 5 + j)
            x = 156 + (6 if j else 0)
            sm = K.place(tm, VW, VH, x, ty) & paper
            p.put(sm, 'G', 1.0 + light[sm] * 0.8)
            ty += 22
        ty += 14
    p.resolve(band=2.0)
    return p.L.c


def _split_note(s: str):
    """'Registratur. Hof, Rampe. 0.30 Uhr. – E.' -> ['Registratur. Hof, Rampe.', '0.30 Uhr. – E.']"""
    i = s.find('0.30')
    return [s[:i].strip(), s[i:].strip()] if i > 0 else [s]


# ======================================================================================= r5: Café Korridor
CLOCK = (452, 112)
CLOCK_R = 21


def cafe():
    R = C.ramps(N=NIGHT, S=SNOW, L=LAMP, M=BRASS, P=PAPER, O=OAK,
                T=['#0B0D10', '#14171B', '#1F2328', '#2C3137', '#3C424A', '#555C64', '#727A82'],   # marble
                W=['#07090D', '#0D1117', '#141A22', '#1C242E', '#26303C'], R=RED,
                K=['#1A1A1C', '#3A3A3C', '#7C7A76', '#C8C4BA', '#EEEAE0'])
    p = C.Paint(VW, VH, R, 'cafe')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 811)
    cold = np.clip(1 - np.hypot((xx - 330) / 360, (yy - 120) / 200), 0, 1) ** 1.2
    bulb = Q.lightfield(VW, VH, [(586, 96, 220, 1.0, 1.6)])
    p.put(np.ones((VH, VW), bool), 'W', 0.6 + cold * 1.6 + bulb * 1.6 + nz * 0.4)
    # the window front: three panes, outside the station facade with its clock, snow, a street lamp
    wx0, wy0, wx1, wy1 = 40, 58, 600, 228
    win = (xx >= wx0) & (xx < wx1) & (yy >= wy0) & (yy < wy1)
    p.put(win, 'N', 2.4 + (yy - wy0) / 100.0 + nz * 0.5)
    stn = win & (yy >= 72) & (yy < 196) & (xx >= 360) & (xx < 560)
    p.put(stn, 'N', 3.6 + nz[stn] * 0.8)
    for ax in range(372, 556, 34):
        arc = stn & (np.abs(xx - ax - 12) < 10) & (yy > 150)
        p.put(arc, 'N', 1.6)
    p.put(stn & (yy >= 72) & (yy < 76), 'S', 5.0)
    clock = ell(CLOCK[0], CLOCK[1], CLOCK_R + 3, CLOCK_R + 3)
    p.put(clock & win, 'M', 2.4)
    face = ell(CLOCK[0], CLOCK[1], CLOCK_R, CLOCK_R)
    p.put(face & win, 'K', 3.6)
    r, a = K.polar(yy, xx, CLOCK[0], CLOCK[1])
    hours, mins = K.clock_indices(yy, xx, CLOCK[0], CLOCK[1], CLOCK_R - 1.5, 5.0, 2.5)
    p.put(hours & face, 'K', 0.6)
    p.put(mins & face, 'K', 1.6)
    ground = win & (yy >= 196)
    p.put(ground, 'S', 4.0 + nz[ground] * 1.4)
    lamp_post = win & (np.abs(xx - 300) < 1.2) & (yy >= 116) & (yy < 200)
    p.put(lamp_post, 'N', 1.0)
    p.put(win & ell(300, 112, 4, 5), 'L', 6.0)
    # gold letters on the glass, reversed (we read them from inside)
    tm = K.vtext('KORRIDOR', 'l', 2)[:, ::-1]
    tm = np.repeat(np.repeat(tm, 2, 0), 2, 1)
    sm = K.place(tm, VW, VH, 320 - tm.shape[1] // 2, 66) & win
    p.put(sm, 'M', 3.0)
    p.put(sm & ~C.shift(sm, 0, -1), 'M', 4.6)
    # mullions + the sill
    frame = win & ((np.abs(xx - 226) < 3) | (np.abs(xx - 414) < 3) | (xx < wx0 + 3) | (xx >= wx1 - 3) |
                   (yy < wy0 + 3) | (yy >= wy1 - 4))
    p.put(frame, 'O', 1.4 + cold[frame] * 1.2)
    p.put((xx >= wx0 - 6) & (xx < wx1 + 6) & (yy >= wy1) & (yy < wy1 + 6), 'O', 2.0 + cold[(xx >= wx0 - 6) & (xx < wx1 + 6) & (yy >= wy1) & (yy < wy1 + 6)])
    # floor: black and white tiles in perspective, dark
    fl = yy >= 262
    u = (yy - 262) / 98.0
    chk = (np.floor((xx - 320) / (14 + u * 40)) + np.floor((yy - 262) / (4 + u * 10))) % 2 == 0
    p.put(fl, 'T', 0.8 + cold[fl] * 1.4 + bulb[fl])
    p.put(fl & chk, 'T', 2.2 + cold[fl & chk] * 1.6 + bulb[fl & chk] * 1.4)
    p.put((yy >= 228) & (yy < 262), 'W', 1.0 + cold[(yy >= 228) & (yy < 262)] * 0.6)            # wainscot
    # tables with chairs upside down (silhouettes against the window), the counter at the right
    def table(cx, ty, s=1.0, up=True, elena=False):
        top = ell(cx, ty, 30 * s, 6 * s)
        p.put(top, 'T', 3.0 + cold[top] * 2.6)
        p.put(top & (yy > ty + 2 * s), 'T', 1.6)
        p.put((np.abs(xx - cx) < 2.5 * s) & (yy >= ty + 5 * s) & (yy < ty + 52 * s), 'N', 0.8)
        p.put(ell(cx, ty + 52 * s, 13 * s, 3 * s), 'N', 0.8)
        if up:
            for sx in (-1, 1):
                ch = poly([(cx + sx * 6 * s, ty - 4 * s), (cx + sx * 26 * s, ty - 4 * s), (cx + sx * 24 * s, ty - 10 * s),
                           (cx + sx * 8 * s, ty - 10 * s)])
                legs = p.line([(cx + sx * 9 * s, ty - 10 * s), (cx + sx * 7 * s, ty - 46 * s)], r=1.0 * s) | \
                    p.line([(cx + sx * 23 * s, ty - 10 * s), (cx + sx * 26 * s, ty - 46 * s)], r=1.0 * s)
                back = p.line([(cx + sx * 24 * s, ty - 10 * s), (cx + sx * 30 * s, ty - 2 * s), (cx + sx * 34 * s, ty + 18 * s)], r=1.2 * s)
                p.put(ch | legs | back, 'O', 0.6)
        else:
            ch = p.line([(cx + 38 * s, ty - 30 * s), (cx + 40 * s, ty + 8 * s)], r=1.5 * s) | \
                ell(cx + 30 * s, ty + 8 * s, 12 * s, 3 * s) | p.line([(cx + 22 * s, ty + 10 * s), (cx + 20 * s, ty + 50 * s)], r=1.1 * s) | \
                p.line([(cx + 38 * s, ty + 10 * s), (cx + 40 * s, ty + 50 * s)], r=1.1 * s)
            p.put(ch, 'O', 1.0 + cold[ch] * 1.4)
        if elena:
            gx, gy = cx - 10 * s, ty - 2 * s
            gw, gh = 4.4 * s, 17 * s
            glass = (np.abs(xx + 0.5 - gx) < gw - (gy - yy) * 0.04) & (yy >= gy - gh) & (yy < gy)
            p.put(glass, 'S', 3.0 + cold[glass] * 2.0)
            tea = glass & (yy >= gy - gh * 0.7)
            p.put(tea, 'L', 2.2 + cold[tea] * 0.8)
            p.put(glass & (np.abs(xx + 0.5 - (gx - gw * 0.55)) < 0.7), 'S', 7.6)
            p.put(glass & (yy < gy - gh + 1.5), 'S', 6.0)
            p.put((np.abs(xx + 0.5 - (gx + 1.5 * s)) < 0.6) & (yy >= gy - gh - 7 * s) & (yy < gy - gh * 0.6), 'M', 4.2)
            p.put(ell(gx, gy, 9 * s, 2.0 * s), 'K', 3.0 + cold[ell(gx, gy, 9 * s, 2.0 * s)] * 1.2)    # saucer
            # her chair is still at the table: pushed back a little, as if someone had just got up
    table(520, 246, 0.9, True)
    table(372, 240, 0.78, True)
    table(250, 238, 0.7, True)
    table(196, 268, 1.45, False, elena=True)
    cnt = (xx >= 600) & (yy >= 150)
    p.put(cnt, 'O', 1.2 + bulb[cnt] * 3.0)
    p.put(cnt & (yy < 156), 'O', 3.4 + bulb[cnt & (yy < 156)] * 2.0)
    p.put(box(590, 0, 640, 60), 'W', 1.0)
    p.resolve(band=2.0)
    L['clock'] = list(CLOCK)
    L['clock_r'] = CLOCK_R
    L['cafe_win'] = [wx0 + 3, wy0 + 3, wx1 - 3, 196]
    return p.L.c


def cafe_glow():
    return Q.glow_sprite(VW, VH, [(CLOCK[0], CLOCK[1], 46, 40, (34, 34, 30), 1.4), (586, 96, 90, 70, (50, 34, 14), 1.6),
                                  (300, 112, 26, 26, (40, 28, 12), 1.5)], 6.0)


# ======================================================================================= build
def build(w):
    w('radio/square_bg.png', square_bg())
    w('radio/win_konrad.png', lit_window('konrad'))
    w('radio/win_alexei.png', lit_window('alexei'))
    w('radio/square_glow.png', lit_glow())
    w('radio/door_konrad.png', door_open('konrad'))
    w('radio/door_alexei.png', door_open('alexei'))
    w('radio/walker_konrad.png', walker('konrad'))
    w('radio/walker_alexei.png', walker('alexei'))
    w('radio/steam.png', steam())
    w('radio/radio.png', radio())
    w('radio/room_alexei.png', room('alexei'))
    w('radio/room_konrad.png', room('konrad'))
    w('radio/dial_glow.png', dial_glow())
    w('radio/lamp_glow.png', lamp_glow())
    w('radio/magic_eye.png', magic_eye())
    w('radio/steam_tea.png', steam_tea())
    w('radio/arm_alexei.png', arm_alexei())
    w('radio/hand_konrad.png', hand_konrad())
    w('radio/doors.png', doors())
    w('radio/note_fold.png', note_fold())
    w('radio/note_close.png', note_close())
    w('radio/cafe.png', cafe())
    w('radio/cafe_glow.png', cafe_glow())
    import env_c3p2_cine_figs as F
    w('radio/fig_alexei.png', F.room_alexei())
    w('radio/fig_konrad.png', F.room_konrad())
    L['fig_alexei'] = list(F.ROOM_A_AT)
    L['fig_konrad'] = list(F.ROOM_K_AT)
