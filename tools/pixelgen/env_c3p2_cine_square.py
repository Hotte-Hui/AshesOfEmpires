"""env_c3p2_cine_square -- the station square of LS_C3_Radio r1/r6, round 10 (owner: c3p2 places stream).

The square at 0.10 seen from the station roof, painted as layers so the runtime can crane (r1) and pan (r6) the
camera with parallax (scenes/cinematics/ch3_radio/ch3_radio.gd):
  square_bg    664 x 380 at (-12, -10): sky with the city glow under the snow clouds, the palais at the far end
               (the dark east wing, one dim window high up), lime trees, the far street with a taxi rank, the two
               hotels facing each other (Hotel Europa left: arches, the lit lobby, balconies, brass sign, mansard;
               Hotel Nord right: flush windows, lit lobby, roof letters), the snowed square with tram rails and the
               overhead wires on their poles, a tram shelter, the clock post (0.10), a kiosk, the advertising column,
               lamp posts with their warm pools, snowed-in cars at the kerb, trodden paths and tyre tracks, haze
  square_near  700 x 96: the station roof's parapet in front of the camera (snow pillow, coping, balusters, an urn
               at the left, a lantern on its pedestal at the right)
  taxi         a small saloon with its headlights (2 frames) driving along the far street during r1
The pinhole camera, the hotel geometry, the lit windows and the walker paths stay those of env_c3p2_cine_radio
(SQ, HOTEL_X, DOOR_*, WIN_*), so layout.json keeps every round-8 key.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, BRASS, RED)
import env_c3p2_cine_life as LF
import env_c3p2_cine_radio as RD
import pg

L = Q.LAYOUT.setdefault('radio', {})
MX, MY = 12, 10                       # margins of square_bg (the camera moves inside them)
SQ_F = RD.SQ['f']
W2, H2 = VW + 2 * MX, VH + 2 * MY
NEAR_W, NEAR_H, NEAR_X, NEAR_Y = 700, 164, -30, 200

PATINA = ['#14202A', '#1E3036', '#2C4448', '#3E5A5A']
WARMWIN = ['#3A2614', '#5A3A1C', '#7E5226', '#A8703A', '#D09A58', '#F2C888']
PAL = LF.palette(NIGHT, SNOW, LAMP, PATINA, WARMWIN, BRASS[:5],
                 ['#0E1622', '#16202E', '#222E3E', '#2E3C4E', '#3E4C5E', '#56667A', '#26323F', '#323E4C',
                  '#384454', '#44505F', '#26201E', '#3A302A', '#4E4036', '#6A5848', '#8A7660', '#2A1A14',
                  '#4A2A1E', '#6E3A26', '#5A2A22', '#7A3A2C', '#9AB0C8', '#C8D8E8', '#0A0E16',
                  # lamp light on snow (round 11): pale warm greys, so the pools read as light, not as mud
                  '#5C5B5A', '#77716A', '#928A7E', '#ADA392', '#C8BCA6', '#E0D4BC', '#4A505A', '#666A70'])


def sq(X, Y, Z):
    return RD.sq(X, Y, Z)


# ================================================================================================ facades
def _facade(kind):
    """Flat facade texture (u along the street, v top -> bottom, 12 px per metre) as lit float RGB + alpha."""
    ppm = 12.0
    z0, z1 = RD.HOTEL_Z
    europa = kind == 'europa'
    Ytop = 25.0 if europa else 24.5
    w, h = int((z1 - z0) * ppm), int(Ytop * ppm)
    cv = LF.Cv(w, h, amb=(1.0, 1.0, 1.0))
    yy, xx = cv.yy, cv.xx
    Y = Ytop - (yy + 0.5) / ppm
    Z = z0 + (xx + 0.5) / ppm
    n1 = LF.nz(w, h, 18, 401 if europa else 402)
    n2 = LF.nz(w, h, 4, 405 if europa else 406)
    amb = np.array([0.42, 0.47, 0.62], np.float32)
    # night light on the wall: cool sky from above, warm bounce of the lamps and the lobby near the ground
    door_z = RD.DOOR_K[1] if europa else RD.DOOR_A[1]
    warm = np.clip(1 - Y / 9.0, 0, 1) ** 1.6 * 0.55 + np.clip(1 - np.hypot((Z - door_z) / 9.0, Y / 6.0), 0, 1) ** 1.4 * 0.9
    for lz in (32.0, 52.0, 72.0, 92.0):
        warm += np.clip(1 - np.hypot((Z - lz) / 10.0, (Y - 3.0) / 7.0), 0, 1) ** 1.6 * 0.25
    cv.L[:] = amb[None, None] + warm[..., None] * np.array([0.9, 0.62, 0.32], np.float32)[None, None]
    stone = '#3E4A5A' if europa else '#46505C'
    cv.put(cv.full(), stone, 0.72 + (n1 - 0.5) * 0.22 + (n2 - 0.5) * 0.08 + np.clip((Y - 4) / 20, 0, 1) * 0.12)
    glass = np.zeros((h, w), bool)
    lit = np.zeros((h, w), bool)
    lit_k = np.zeros((h, w), np.float32)
    snow = np.zeros((h, w), bool)
    dark = np.zeros((h, w), bool)
    emis = []

    def lit_window(m, seedv, base=1.0):
        nonlocal lit, lit_k
        lit |= m
        cur = (np.mod(xx * 0.5 + seedv * 7, 3) < 1.2) & m
        lit_k[m] = base
        lit_k[cur] = base * 0.72

    if europa:
        cv.put((Y < 4.6) & (np.mod(Y, 0.75) < 0.09), stone, 0.5)                   # rustication
        cv.put((Y >= 4.5) & (Y < 5.0), stone, 1.08)                                 # string course
        cv.put((Y >= 19.8) & (Y < 20.8), stone, 1.12)                               # main cornice
        cv.put((Y >= 19.75) & (Y < 19.85), stone, 0.45)
        snow |= (Y >= 20.7) & (Y < 21.0)
        roof = Y >= 21.0
        cv.put(roof, '#1E2836', 0.9 + n1[roof] * 0.5)
        cv.put(roof & (np.mod(Y * 3.2 + np.mod(Z * 0.9, 1.0) * 0.0, 1.0) < 0.12), '#121A26', 1.0)
        snow |= roof & (LF.nz(w, h, 14, 409) > 0.6)
        for i, zc in enumerate(np.arange(z0 + 2.0, z1, 4.0)):
            dx = np.abs(Z - zc)
            door = abs(zc - door_z) < 0.1
            aw = 1.5 if door else 1.1
            arch = ((dx < aw) & (Y < 3.4)) | ((np.hypot(Z - zc, Y - 3.4) < aw) & (Y >= 3.4))
            arch &= Y > 0.25
            lobby = abs(zc - door_z) < 4.5
            if door:
                cv.put(arch & (Y < 3.1), '#2B1B12', 1.0)
                dglass = arch & (Y > 1.0) & (Y < 2.9) & (np.abs(Z - zc) > 0.18) & (np.abs(Z - zc) < 1.1)
                emis.append((dglass, '#D09A58', 1.0))
                emis.append((arch & (Y >= 3.1), '#F2C888', 1.0))                     # fanlight
                cv.put((np.abs(Z - zc) < 2.2) & (Y >= 3.5) & (Y < 3.8), '#2E3C4E', 1.2)  # canopy
                snow |= (np.abs(Z - zc) < 2.3) & (Y >= 3.8) & (Y < 4.0)
                for s_ in (-1.9, 1.9):
                    emis.append(((np.abs(Z - zc - s_) < 0.14) & (Y > 2.3) & (Y < 2.75), '#FCE2B0', 1.0))
            elif lobby:
                emis.append((arch, '#A8703A', 1.0))
                emis.append((arch & (np.abs(np.mod(Z - zc + 0.55, 0.55)) < 0.05), '#5A3A1C', 1.0))
                emis.append((arch & (Y < 1.2), '#7E5226', 1.0))
            else:
                glass |= arch
                cv.put(arch & (Y < 1.0), '#2A1A14', 1.0)                             # shop blinds down
            # upper floors
            for fl, (y0, y1) in enumerate(((6.0, 8.4), (9.6, 11.8), (13.2, 15.4), (16.8, 18.8))):
                win = (dx < 0.62) & (Y >= y0) & (Y < y1)
                sill = (dx < 0.8) & (Y >= y0 - 0.24) & (Y < y0)
                cv.put(sill, stone, 1.1)
                snow |= (dx < 0.8) & (Y >= y0 - 0.06) & (Y < y0 + 0.05)
                hv = LF.hsh(zc, fl, 3.0)
                is_k = abs(zc - (RD.WIN_K[0] + RD.WIN_K[1]) / 2) < 1.5 and fl == 2
                if hv < 0.10 and not is_k:
                    lit_window(win, i * 4 + fl, 0.75 + hv * 2.0)
                else:
                    glass |= win
                cv.put(win & (np.abs(Z - zc) < 0.05), stone, 0.6)                    # mullion
                if fl == 0:
                    ped = (Y >= y1 + 0.15) & (Y < y1 + 0.15 + (0.9 - dx) * 0.5) & (dx < 0.9)
                    cv.put(ped, stone, 1.12)
                    snow |= ped & ~C.shift(ped, 0, -1)
                    if i % 2 == 0:                                                   # balcony
                        slab = (dx < 1.15) & (Y >= y0 - 0.32) & (Y < y0 - 0.12)
                        cv.put(slab, stone, 1.0)
                        rail = (dx < 1.1) & (Y >= y0 - 0.12) & (Y < y0 + 0.9) & \
                            ((np.mod(Z * 6.0, 1.0) < 0.22) | (Y >= y0 + 0.8))
                        dark |= rail
                        snow |= (dx < 1.15) & (Y >= y0 + 0.86) & (Y < y0 + 0.96)
            # dormers
            dorm = (dx < 0.55) & (Y >= 21.6) & (Y < 23.0)
            cv.put(dorm | ((dx < 0.75) & (Y >= 23.0) & (Y < 23.4)), stone, 1.0)
            dg = (dx < 0.38) & (Y >= 21.8) & (Y < 22.8)
            if LF.hsh(zc, 9.0, 5.0) < 0.12:
                lit_window(dg, i, 0.6)
            else:
                glass |= dg
            snow |= (dx < 0.8) & (Y >= 23.35) & (Y < 23.6)
        # brass sign across the first floor, lit by two small lamps
        tm = K.vtext('HOTEL EUROPA', 'l', 2)
        tm = np.repeat(np.repeat(tm, 2, 0), 2, 1)
        sx0 = int((door_z - z0) * ppm - tm.shape[1] / 2)
        sy0 = int((Ytop - 5.75) * ppm)
        sm = K.place(tm, w, h, sx0, sy0)
        emis.append((sm, '#E8C779', 1.0))
        emis.append((sm & ~C.shift(sm, 0, 1), '#9C7630', 1.0))
        alpha = Y < 24.2
    else:
        for fl in range(6):
            yb = fl * 3.5
            cv.put((Y >= yb + 3.38) & (Y < yb + 3.5), stone, 0.6)
        cv.put((Y >= 20.6) & (Y < 21.4), stone, 1.15)                               # parapet
        snow |= (Y >= 21.3) & (Y < 21.55)
        for i, zc in enumerate(np.arange(z0 + 1.75, z1, 3.5)):
            dx = np.abs(Z - zc)
            door = abs(zc - door_z) < 0.9
            if door:
                g = (dx < 1.6) & (Y > 0.0) & (Y < 2.8)
                emis.append((g, '#D09A58', 1.0))
                emis.append((g & (np.abs(Z - door_z) < 0.06), '#5A3A1C', 1.0))
                emis.append((g & (Y < 0.9) & (np.abs(Z - door_z) > 0.7), '#A8703A', 1.0))
                cv.put((np.abs(Z - door_z) < 2.6) & (Y >= 2.9) & (Y < 3.25), stone, 1.3)
                snow |= (np.abs(Z - door_z) < 2.6) & (Y >= 3.25) & (Y < 3.42)
                emis.append(((np.abs(Z - door_z) < 0.12) & (Y > 2.55) & (Y < 2.85), '#FCE2B0', 1.0))
            else:
                gw = (dx < 0.9) & (Y >= 0.7) & (Y < 2.6)
                if abs(zc - door_z) < 4.0:
                    emis.append((gw, '#7E5226', 1.0))
                else:
                    glass |= gw
            for fl in range(1, 6):
                yb = fl * 3.5
                win = (dx < 0.7) & (Y >= yb + 0.9) & (Y < yb + 2.7)
                cv.put((dx < 0.82) & (Y >= yb + 0.72) & (Y < yb + 0.9), stone, 1.1)
                snow |= (dx < 0.82) & (Y >= yb + 0.84) & (Y < yb + 0.92)
                hv = LF.hsh(zc, fl, 7.0)
                is_a = abs(zc - (RD.WIN_A[0] + RD.WIN_A[1]) / 2) < 1.5 and fl == 2
                if hv < 0.09 and not is_a:
                    lit_window(win, i * 5 + fl, 0.7 + hv * 2.0)
                else:
                    glass |= win
        tm = K.vtext('HOTEL NORD', 'l', 2)[:, ::-1]        # read from the square: mirrored along u
        tm = np.repeat(np.repeat(tm, 3, 0), 3, 1)
        sx0 = int((66.0 - z0) * ppm)
        sm = K.place(tm, w, h, sx0, int((Ytop - 24.2) * ppm))
        frame = (Y >= 21.4) & (Y < 21.7) & (Z > 65.5) & (Z < 66.0 + tm.shape[1] / ppm)
        cv.put(frame, '#121A26', 1.0)
        emis.append((sm, '#F2E8C8', 1.0))
        emis.append((sm & ~C.shift(sm, 0, 1), '#B09A70', 1.0))
        alpha = (Y < 21.55) | sm | frame
    # glass: dark, the sky reflected toward the top of each pane
    cv.put(glass, '#0C121C', 0.8 + n2[glass] * 0.5 + np.clip(np.mod(-Y, 1.0), 0, 1)[glass] * 0.3)
    cv.put(dark, '#06080C', 1.0)
    for m, col, k in emis:
        cv.emit(m, col, k)
    if lit.any():
        base = LF.hexf('#C88A48')
        cv.rgb[lit] = base[None] * lit_k[lit][:, None]
        cv.a |= lit
    cv.put(snow, '#A1AAB7', 0.95 + n2[snow] * 0.2)
    cv.a = alpha.copy()
    return cv, ppm, Ytop


# ================================================================================================ the palais
def _palais(cv):
    """Frontal palais at Z = 150 (2.4 px per metre): rusticated base, pilasters, the central pavilion with the
    portico, the drum and the patinated dome, mansards; west wing partly lit, the east wing dark but for one
    dim window high up."""
    s = RD.SQ['f'] / RD.PALAIS_Z
    xx, yy = cv.xx, cv.yy
    X = (xx + 0.5 - RD.SQ['cx']) / s
    Y = RD.SQ['H'] - (yy + 0.5 - RD.SQ['yh']) / s
    Z = RD.PALAIS_Z
    body = (np.abs(X) < 38) & (Y >= 0) & (Y < 17.5)
    centre = (np.abs(X) < 12) & (Y >= 0) & (Y < 21.0)
    mans = (np.abs(X) < 37) & (Y >= 17.5) & (Y < 20.0 - np.clip(np.abs(X) - 35, 0, 2)) & ~centre
    drum = (np.abs(X) < 6.0) & (Y >= 21) & (Y < 25.5)
    dome = (np.hypot(X / 7.4, (Y - 25.5) / 9.0) < 1.0) & (Y >= 25.5)
    lantern = (np.abs(X) < 1.0) & (Y >= 34.0) & (Y < 37.5)
    sil = body | centre | drum | dome | lantern | mans
    cv.put(sil & ~dome, '#202A38', 1.0, z=Z)
    cv.put(mans, '#18202C', 1.0, z=Z)
    cv.put(dome, '#2C4448', 0.9 + (np.mod(X + 40, 2.0) < 0.35) * 0.3, z=Z)
    cv.put(dome & (X > 2.5), '#1E3036', 1.0, z=Z)
    cv.put(lantern, '#2C4448', 1.0, z=Z)
    cv.put(body & (Y < 4.0) & (np.mod(Y, 1.0) < 0.3), '#1A2230', 1.0, z=Z)            # rustication
    for xc in np.arange(-37.0, 38.0, 6.0):
        cv.put(body & (np.abs(X - xc) < 0.5) & (Y >= 4.0), '#2A3646', 1.0, z=Z)       # pilasters
    snow = LF.edge_top(sil) | (dome & (Y > 31.5)) | LF.edge_top(sil, 2) & (LF.nz(cv.w, cv.h, 2, 77, 1) > 0.4)
    for yl in (4.0, 17.5, 21.0):
        ledge = (np.abs(Y - yl) < 0.42) & (np.abs(X) < (38 if yl < 18 else 12))
        cv.put(ledge, '#56667A', 1.0, z=Z)
        snow |= ledge & (Y > yl)
    # windows: west wing and centre partly lit, the east wing dark but for one dim window high up
    for xc in np.arange(-34.5, 36.0, 3.0):
        for (y0, y1) in ((1.2, 3.4), (6.0, 9.0), (11.0, 14.5)):
            m = (np.abs(X - xc) < 0.7) & (Y >= y0) & (Y < y1) & body & ~centre
            east = xc > 13.0
            hv = LF.hsh(xc, y0, 2.0)
            if east and abs(xc - 30.0) < 0.6 and y0 > 10:
                cv.emit(m, '#5A3A1C', z=Z)
            elif (not east) and xc < -13 and hv < 0.45:
                cv.emit(m, '#A8703A' if hv < 0.2 else '#7E5226', z=Z)
            else:
                cv.put(m, '#0A0E16', 1.0, z=Z)
    for xc in np.arange(-10.5, 11.0, 3.0):
        for (y0, y1) in ((11.0, 14.5), (15.5, 19.0)):
            m = (np.abs(X - xc) < 0.65) & (Y >= y0) & (Y < y1) & centre
            cv.put(m, '#0A0E16', 1.0, z=Z) if LF.hsh(xc, y0, 4.0) > 0.3 else cv.emit(m, '#7E5226', z=Z)
    # portico: columns, pediment, the lit door, two lanterns either side of the steps
    for xc in np.arange(-7.5, 8.0, 3.0):
        cv.put((np.abs(X - xc) < 0.45) & (Y >= 0.8) & (Y < 9.5), '#3E4C5E', 1.0, z=Z)
    ped = (Y >= 9.5) & (Y < 9.5 + (9.0 - np.abs(X)) * 0.28) & (np.abs(X) < 9.0)
    cv.put(ped, '#2E3C4E', 1.0, z=Z)
    snow |= LF.edge_top(ped)
    cv.emit((np.abs(X) < 1.3) & (Y >= 0.6) & (Y < 3.6), '#7E5226', z=Z)
    cv.put((np.abs(X) < 9.5) & (Y < 0.8) & (np.mod(Y, 0.27) < 0.1), '#56667A', 1.0, z=Z)   # steps
    for sx in (-9.5, 9.5):
        cv.emit(np.hypot(X - sx, (Y - 3.0) * 0.8) < 0.7, '#FCE2B0', z=Z)
    # chimneys
    for xc in (-30.0, -21.0, 21.0, 30.0):
        ch = (np.abs(X - xc) < 0.8) & (Y >= 19.0) & (Y < 22.0)
        cv.put(ch, '#18202C', 1.0, z=Z)
        snow |= LF.edge_top(ch)
    cv.put(snow & sil, '#7D8796', 1.0, z=Z)
    return sil


# ================================================================================================ square_bg
def _ground(Xg, Zg, n1, n2):
    """Lit colour of the snow on the square (float RGB) at ground coordinates (X, Z)."""
    snow = LF.hexf('#7D8796')
    rip = LF.vnoise(Xg * 0.9, Zg * 0.22, 3) * 0.6 + LF.vnoise(Xg * 2.6, Zg * 0.7, 4) * 0.4
    base = snow[None, None] * (0.31 + 0.09 * n1[..., None] + 0.03 * n2[..., None] + 0.09 * rip[..., None])
    c = base.copy()
    # pavements along the facades (trodden, bluer), the kerb line, ploughed snow banks on the kerb
    pave = np.abs(np.abs(Xg) - 21.8) < 2.0
    c = np.where(pave[..., None], c * 0.86 + np.array([0, 2, 8], np.float32), c)
    bank = (np.abs(np.abs(Xg) - 19.4) < 0.55 + 0.25 * n2) & (Zg < 96)
    c = np.where(bank[..., None], snow[None, None] * (0.62 + 0.12 * n1[..., None]), c)
    kerb = np.abs(np.abs(Xg) - 19.85) < 0.08
    c = np.where((kerb & ~bank)[..., None], c * 0.7, c)
    # far street in front of the palais (cleared, darker), the steps' forecourt
    street = (Zg > 97) & (Zg < 112)
    c = np.where(street[..., None], c * 0.78 + np.array([2, 2, 6], np.float32), c)
    # trodden diagonals from the station steps to the two hotel doors
    for (dx, dz) in (RD.DOOR_K, RD.DOOR_A):
        t = np.clip(((Xg - 0) * dx + (Zg - 18) * (dz - 18)) / (dx * dx + (dz - 18) ** 2), 0, 1)
        d = np.hypot(Xg - t * dx, Zg - (18 + t * (dz - 18)))
        c = np.where((d < 0.55)[..., None], c * (0.93 - 0.05 * (LF.vnoise(Xg * 3, Zg * 3, 9) > 0.6))[..., None], c)
    # tyre tracks of a taxi: from the far street round to the Europa door
    for off in (-0.75, 0.75):
        u = np.clip((Zg - 40.0) / 60.0, 0, 1)
        xt = -14.0 + 8.0 * u ** 2 + off
        trk = (np.abs(Xg - xt) < 0.16) & (Zg > 40) & (Zg < 100)
        c = np.where(trk[..., None], c * 0.82, c)
    # tram rails (two tracks), half buried, a glint where the lamps catch them
    for rx in (-3.4, -2.0, 2.0, 3.4):
        m = (np.abs(Xg - rx) < 0.05 + Zg * 0.0009) & (n1 > 0.36)
        c = np.where(m[..., None], np.array([18, 22, 30], np.float32)[None, None], c)
    # lamp pools: incandescent light on snow -- the snow keeps its whiteness and takes the lamp's warmth (a pale
    # cream at the foot of the post, greying out into the blue night), sparkling crystals in the brightest part
    for lx in (-12.0, 12.0):
        for lz in (32.0, 52.0, 72.0, 92.0):
            d = np.hypot(Xg - lx, Zg - lz)
            g = np.clip(1 - d / 8.0, 0, 1) ** 1.35
            c = c * (1.0 + g[..., None] * 0.9) + g[..., None] * np.array([96, 82, 58], np.float32)
            sp = (g > 0.35) & (LF.vnoise(Xg * 9.0, Zg * 3.0, 77) > 0.86)
            c = np.where(sp[..., None], c + np.array([40, 36, 30], np.float32), c)
    for (dx, dz) in (RD.DOOR_K, RD.DOOR_A):
        d = np.hypot((Xg - dx) * 0.8, Zg - dz)
        c = c + (np.clip(1 - d / 5.0, 0, 1) ** 1.6)[..., None] * np.array([58, 46, 30], np.float32)
    return c


def square_bg():
    """r1/r6 background with margins (664 x 380 at (-12, -10)): see the module docstring."""
    ss = 3
    f, H, yh, cx = RD.SQ['f'], RD.SQ['H'], RD.SQ['yh'], RD.SQ['cx']
    hs, ws = H2 * ss, W2 * ss
    yy = (np.arange(hs, dtype=np.float32)[:, None] + 0.5) / ss - MY + np.zeros((1, ws), np.float32)
    xx = (np.arange(ws, dtype=np.float32)[None, :] + 0.5) / ss - MX + np.zeros((hs, 1), np.float32)
    rgb = np.zeros((hs, ws, 3), np.float32)
    # sky: snow clouds lit from below by the city, darker overhead
    cl = pg.value_noise(ws, hs, 60 * ss, 4411, octaves=4)
    up = np.clip((yh - yy) / 140.0, 0, 1)
    sky = (np.array([14, 17, 26], np.float32)[None, None] * (1 - up[..., None]) * 1.0 +
           np.array([8, 10, 16], np.float32)[None, None] * up[..., None])
    sky = sky + (cl[..., None] - 0.45) * np.array([16, 15, 16], np.float32) * (1 - up[..., None] * 0.5)
    gl = np.clip(1 - np.hypot((xx - 330) / 300, (yy - 128) / 80), 0, 1) ** 1.5
    sky += gl[..., None] * np.array([34, 24, 16], np.float32)
    rgb[:] = sky
    # ground plane
    below = yy > yh + 0.5
    Zg = np.where(below, f * H / np.maximum(yy - yh, 0.5), 1e6).astype(np.float32)
    Xg = (xx - cx) * Zg / f
    n1 = pg.value_noise(ws, hs, 30, 411, octaves=3)
    n2 = pg.value_noise(ws, hs, 7, 413, octaves=2)
    g = _ground(Xg, Zg, n1, n2)
    fogk = np.clip((Zg - 30) / 140, 0, 1)[..., None] * 0.42
    g = g * (1 - fogk) + np.array([24, 28, 40], np.float32) * fogk
    rgb = np.where(below[..., None], g, rgb)
    # facades: supersampled warp of the flat textures
    zbuf = np.where(below, Zg, 1e4)
    for kind, sign in (('europa', -1.0), ('nord', 1.0)):
        fc, ppm, Ytop = _facade(kind)
        tex = fc.rgb
        ta = fc.a
        th, tw = tex.shape[:2]
        side = (xx - cx) * sign > 0.5
        Zf = np.where(side, f * (RD.HOTEL_X * sign) / np.where(side, xx - cx, 1.0), -1.0)
        Yf = H - (yy - yh) * Zf / f
        u = ((Zf - RD.HOTEL_Z[0]) * ppm).astype(np.int32)
        v = ((Ytop - Yf) * ppm).astype(np.int32)
        ok = side & (u >= 0) & (u < tw) & (v >= 0) & (v < th)
        ok2 = ok.copy()
        ok2[ok] = ta[v[ok], u[ok]]
        col = tex[np.clip(v, 0, th - 1), np.clip(u, 0, tw - 1)]
        fk = np.clip((Zf - 30) / 150, 0, 1)[..., None] * 0.45
        col = col * (1 - fk) + np.array([24, 28, 40], np.float32) * fk
        rgb = np.where(ok2[..., None], col, rgb)
        zbuf = np.where(ok2, Zf, zbuf)
    # down-sample to 1x
    def down(a):
        h2, w2 = a.shape[0] // ss, a.shape[1] // ss
        return a.reshape(h2, ss, w2, ss, *a.shape[2:]).mean(axis=(1, 3))
    cv = LF.Cv(W2, H2, -MX, -MY, amb=(0.42, 0.47, 0.6))
    cv.rgb = down(rgb)
    cv.a[:] = True
    cv.z = down(zbuf)
    # the palais and the far street furniture
    pal_m = _palais(cv)
    s150 = f / RD.PALAIS_Z
    for tx in (-30.0, -24.0, -18.0, 17.0, 23.0, 29.0):
        for tz in (113.0, 126.0):
            bx, by = sq(tx, 0.0, tz)
            hgt = f * 8.5 / tz
            LF.tree(cv, bx, by, hgt, int(abs(tx) * 10 + tz), col='#0E141C', snow='#56667A', spread=1.1,
                    trunk_r=max(0.6, f * 0.22 / tz))
    # taxi rank in front of the palais: two parked taxis, snowed in, one with its roof sign lit
    for i, (X, Zc) in enumerate(((-9.0, 105.0), (-4.2, 105.0))):
        bx, by = sq(X, 0.0, Zc)
        LF.car(cv, bx, by, s=f * 0.1 / Zc, facing=1, body='#1E242C', snow='#7D8796', seed=50 + i)
        if i == 0:
            cv.emit(cv.box(bx - 1, by - f * 1.75 / Zc - 1, bx + 2, by - f * 1.55 / Zc), '#F2C888')
    # overhead tram wires: poles either side of the tracks, span wires, the two contact wires
    poles = []
    for Zp in (26.0, 44.0, 62.0, 80.0, 98.0):
        for X in (-6.2, 6.2):
            b = sq(X, 0.0, Zp)
            t = sq(X, 6.6, Zp)
            r = max(0.5, f * 0.09 / Zp)
            m = cv.seg([b, t], r, r * 0.8)
            cv.put(m, '#0A0E16', 1.0, z=Zp)
            poles.append((X, Zp))
        a = sq(-6.2, 6.0, Zp)
        bb = sq(6.2, 6.0, Zp)
        LF.wire(cv, a, bb, f * 0.25 / Zp, '#0A0E16', r=0.42)
    for X in (-2.7, 2.7):
        pts = [sq(X, 5.6, z) for z in np.arange(19.0, 110.0, 3.0)]
        cv.put(cv.seg(pts, 0.42), '#0A0E16', 1.0)
    # the tram shelter (glass roof under snow, a bench, the timetable lit) at the stop
    Zs, X0s, X1s = 47.0, -7.8, -6.6
    a0, a1 = sq(X0s, 2.6, Zs - 3.0), sq(X0s, 2.6, Zs + 3.0)
    b0, b1 = sq(X1s, 2.6, Zs + 3.0), sq(X1s, 2.6, Zs - 3.0)
    roof = cv.poly([a0, a1, b0, b1])
    for Zq in (Zs - 3.0, Zs + 3.0):
        cv.put(cv.seg([sq(X0s, 0.0, Zq), sq(X0s, 2.6, Zq)], 0.6), '#0A0E16', 1.0)
    glassw = cv.poly([sq(X0s, 0.4, Zs - 3.0), sq(X0s, 0.4, Zs + 3.0), sq(X0s, 2.5, Zs + 3.0), sq(X0s, 2.5, Zs - 3.0)])
    cv.put(glassw, '#26323F', 1.0)
    cv.emit(cv.poly([sq(X0s, 1.0, Zs - 0.6), sq(X0s, 1.0, Zs + 0.4), sq(X0s, 1.9, Zs + 0.4), sq(X0s, 1.9, Zs - 0.6)]),
            '#D09A58')
    cv.put(roof, '#A1AAB7', 1.0)
    # the clock post (Normaluhr): 0.10 -- two hands on a lit face
    cb = sq(-4.4, 0.0, 31.0)
    ct = sq(-4.4, 3.9, 31.0)
    cv.put(cv.seg([cb, ct], 0.7), '#0A0E16', 1.0)
    cr = f * 0.42 / 31.0
    face = cv.ell(ct[0] + 0.5, ct[1] - cr, cr, cr)
    cv.put(cv.ell(ct[0] + 0.5, ct[1] - cr, cr + 1.0, cr + 1.0), '#0A0E16', 1.0)
    cv.emit(face, '#E8DCC0')
    ccx, ccy = ct[0] + 0.5, ct[1] - cr
    cv.put(cv.seg([(ccx, ccy), (ccx + math.sin(math.radians(60)) * (cr - 1.0), ccy - math.cos(math.radians(60)) * (cr - 1.0))], 0.45),
           '#0A0E16', 1.0, lit=False)
    cv.put(cv.seg([(ccx, ccy), (ccx, ccy - (cr - 2.0))], 0.6), '#0A0E16', 1.0, lit=False)
    cv.put(LF.edge_top(cv.ell(ccx, ccy - cr - 0.6, cr + 1.0, 1.4)), '#A1AAB7', 1.0)
    L['clock_post'] = [round(ccx, 1), round(ccy, 1), round(cr, 2)]
    # kiosk (closed shutters, a little lamp) and the advertising column with posters
    kb = sq(8.6, 0.0, 37.0)
    kw = f * 1.0 / 37.0
    kh = f * 2.4 / 37.0
    kio = cv.box(kb[0] - kw, kb[1] - kh, kb[0] + kw, kb[1])
    cv.put(kio, '#2E3C4E', 1.0)
    cv.put(kio & (np.mod(cv.yy, 2) < 1) & (cv.yy > kb[1] - kh * 0.82), '#1A2431', 1.0)
    rf = cv.poly([(kb[0] - kw - 2, kb[1] - kh), (kb[0] + kw + 2, kb[1] - kh), (kb[0], kb[1] - kh - kw * 0.9)])
    cv.put(rf, '#1E3036', 1.0)
    LF.snowcap(cv, rf, 2, '#A1AAB7', 31)
    cv.emit(cv.box(kb[0] - kw * 0.6, kb[1] - kh * 0.62, kb[0] + kw * 0.2, kb[1] - kh * 0.38), '#A8703A')
    cv.emit(cv.ell(kb[0] - kw + 2, kb[1] - kh * 0.9, 1.0, 1.0), '#FCE2B0')
    bx, by = sq(-8.0, 0.0, 40.0)
    s40 = f / 40.0
    col_m = (np.abs(cv.xx + 0.5 - bx) < 0.55 * s40) & (cv.yy < by) & (cv.yy > by - 3.0 * s40)
    cv.put(col_m, '#2E3C4E', 1.0)
    for k_, pc in ((0.6, '#6E3A26'), (1.2, '#8A7660'), (1.9, '#2C4448'), (2.5, '#7A3A2C')):
        cv.put(col_m & (np.abs(cv.yy + 0.5 - (by - k_ * s40)) < 0.28 * s40), pc, 1.0)
    cv.put(col_m & (cv.xx + 0.5 > bx + 0.2 * s40), '#16202E', 1.0)
    cap = cv.ell(bx, by - 3.0 * s40 - 1, 0.75 * s40, 0.4 * s40)
    cv.put(cap, '#A1AAB7', 1.0)
    # snowed-in cars at the Europa kerb (seen from behind) and one at the Nord side
    for i, (X, Zc) in enumerate(((-18.2, 34.0), (-18.0, 41.0), (18.2, 58.0))):
        bx, by = sq(X, 0.0, Zc)
        s_ = f / Zc
        wcar, hcar = 0.86 * s_, 1.45 * s_
        body = cv.poly([(bx - wcar, by - 0.25 * s_), (bx - wcar, by - 0.85 * s_), (bx - wcar * 0.7, by - hcar),
                        (bx + wcar * 0.7, by - hcar), (bx + wcar, by - 0.85 * s_), (bx + wcar, by - 0.25 * s_)])
        cv.put(body, ('#2A3038', '#3A2C2A', '#22303A')[i], 1.0)
        rw = cv.poly([(bx - wcar * 0.62, by - 0.92 * s_), (bx - wcar * 0.55, by - hcar * 0.94),
                      (bx + wcar * 0.55, by - hcar * 0.94), (bx + wcar * 0.62, by - 0.92 * s_)])
        cv.put(rw, '#0A0E16', 1.0)
        for sx in (-1, 1):
            cv.put(cv.box(bx + sx * wcar * 0.8 - 0.6, by - 0.62 * s_, bx + sx * wcar * 0.8 + 0.8, by - 0.48 * s_),
                   '#5A2A22', 1.0)
        cv.put(cv.box(bx - wcar * 0.9, by - 0.3 * s_, bx + wcar * 0.9, by - 0.18 * s_), '#56667A', 1.0)
        cap_m = np.zeros_like(body)
        for kk in range(1, int(0.32 * s_) + 2):
            cap_m |= LF.edge_top(body | rw, kk)
        cv.put(cap_m & (LF.nz(cv.w, cv.h, 2.2, 60 + i, 2) > 0.2), '#A1AAB7', 1.0)
        cv.put(cv.ell(bx, by, wcar * 1.2, 0.5 * s_) & (cv.yy >= by - 1), '#7D8796', 1.0)
    # lamp posts with lanterns (in front of everything on the ground)
    for lx in (-12.0, 12.0):
        for lz in (92.0, 72.0, 52.0, 32.0):
            b = sq(lx, 0.0, lz)
            t = sq(lx, 4.6, lz)
            r = max(0.5, f * 0.07 / lz)
            cv.put(cv.seg([b, t], r, r * 0.8), '#0A0E16', 1.0)
            rr = max(1.0, f * 0.26 / lz)
            cv.emit(cv.ell(t[0] + 0.5, t[1] - rr * 0.4, rr, rr * 1.2), '#FCE2B0')
            cv.emit(cv.ell(t[0] + 0.5 - rr * 0.3, t[1] - rr * 0.6, rr * 0.45, rr * 0.5), '#FFF6DC')
            cv.put(cv.box(t[0] - rr * 0.6, t[1] - rr * 1.7 - 1, t[0] + rr * 0.6 + 1, t[1] - rr * 1.5), '#A1AAB7', 1.0)
    out = cv.quant(PAL, spread=12.0)
    out[..., 3] = 255
    RD._record_square()
    L['square_bg_at'] = [-MX, -MY]
    return out


def lit_glow():
    """Additive spill of the lit windows, the lamps, the lobbies and the hotel signs into the snowy air."""
    blobs = []
    for kind in ('konrad', 'alexei'):
        q = RD._window_quad(kind)
        cx_ = sum(p[0] for p in q) / 4
        cy_ = sum(p[1] for p in q) / 4
        blobs.append((cx_, cy_, 16, 14, (40, 26, 12), 1.8))
    for lx in (-12.0, 12.0):
        for lz in (32.0, 52.0, 72.0, 92.0):
            tx, ty = sq(lx, 4.6, lz)
            r = 1.0 + 140.0 / lz
            blobs.append((tx + 0.5, ty, r * 1.6, r * 1.3, (64, 46, 22), 1.6))
            # the light falling on the snow at the post's foot (a flat ellipse in perspective)
            gx, gy = sq(lx, 0.0, lz)
            rx = SQ_F * 7.0 / lz
            ry = SQ_F * 10.0 * 7.0 / (lz * lz) * 0.9
            blobs.append((gx + 0.5, gy, rx, max(2.0, ry), (34, 28, 18), 1.4))
    for (X, Z) in (RD.DOOR_K, RD.DOOR_A):
        x, y = sq(X, 1.6, Z)
        blobs.append((x, y, 26, 18, (40, 26, 10), 1.6))
    x, y = sq(-24.0, 5.75, 38.0)
    blobs.append((x + 10, y, 30, 10, (30, 22, 8), 1.6))
    x, y = sq(24.0, 22.5, 70.0)
    blobs.append((x - 8, y, 30, 8, (26, 24, 18), 1.6))
    return Q.glow_sprite(VW, VH, blobs, 2.0)


# ================================================================================================ near layer
def square_near():
    """The station roof in front of the camera (700 x 96 at (-30, 268)): the snow pillow on the parapet, the
    coping, the tops of the balusters, a stone urn at the left, a lantern on its pedestal at the right."""
    cv = LF.Cv(NEAR_W, NEAR_H, NEAR_X, NEAR_Y, amb=(0.36, 0.40, 0.54))
    xx, yy = cv.xx, cv.yy
    lan = (612.0, 254.0)
    cv.light(lan[0], lan[1] + 10, 150, (1.3, 0.85, 0.45), 1.5)
    cv.light(320, 400, 420, (0.25, 0.18, 0.1), 1.2)              # the station's platform lights below
    n1 = cv.nz(9, 1501)
    n2 = cv.nz(3, 1503)
    top = 296.0 + (xx - NEAR_X) * 0.008 + (n1 - 0.5) * 3.0
    pillow = (yy >= top) & (yy < 302 + (xx - NEAR_X) * 0.008)
    coping = (yy >= 302 + (xx - NEAR_X) * 0.008) & (yy < 309 + (xx - NEAR_X) * 0.008)
    below = yy >= 309 + (xx - NEAR_X) * 0.008
    cv.put(coping, '#3E4A5A', 0.9 + n2[coping] * 0.25)
    cv.put(coping & (yy >= 307 + (xx - NEAR_X) * 0.008), '#26303E', 1.0)
    bal_x = np.mod(xx + 8, 26)
    bal = below & (np.abs(bal_x - 13) < 6.0 - np.clip(yy - 312, 0, 9) * 0.3)
    cv.put(below, '#0A0E16', 1.0)
    cv.put(bal, '#2E3C4E', 0.85 + (bal_x[bal] < 11) * 0.25)
    cv.put(pillow, '#A1AAB7', 0.95 + n2[pillow] * 0.25 - np.clip((yy[pillow] - top[pillow]) / 8.0, 0, 1) * 0.25)
    cv.put(LF.edge_top(pillow), '#DEE2E7', 0.9)
    # the urn at the left (on the parapet, cut by the frame)
    ux, uy = 34.0, 299.0
    urn = cv.poly([(ux - 15, uy - 30), (ux + 15, uy - 30), (ux + 11, uy - 16), (ux + 5, uy - 8), (ux + 8, uy),
                   (ux - 8, uy), (ux - 5, uy - 8), (ux - 11, uy - 16)])
    lip = cv.box(ux - 17, uy - 33, ux + 17, uy - 29)
    cv.put(urn | lip, '#26303E', 1.0 + np.clip((xx - ux) / 30.0, -0.4, 0.4))
    cv.put(urn & (np.abs(yy - (uy - 20)) < 1.0), '#16202E', 1.0)
    sn = cv.ell(ux, uy - 34, 17, 5) & (yy < uy - 31)
    cv.put(sn, '#C2C9D2', 1.0)
    # the lantern on its pedestal at the right
    ped = cv.box(lan[0] - 9, 266, lan[0] + 9, 300)
    cv.put(ped, '#2E3C4E', 0.9 + np.clip((lan[0] - xx) / 20.0, -0.3, 0.4))
    cv.put(cv.box(lan[0] - 11, 264, lan[0] + 11, 268), '#3E4A5A', 1.0)
    cv.put(cv.ell(lan[0], 263, 11, 3) & (yy < 265), '#C2C9D2', 1.0)
    post = cv.seg([(lan[0], 264), (lan[0], 236)], 1.6, 1.2)
    cv.put(post, '#0A0E16', 1.0)
    head = cv.poly([(lan[0] - 7, 222), (lan[0] + 7, 222), (lan[0] + 5, 236), (lan[0] - 5, 236)])
    cv.put(head, '#0A0E16', 1.0)
    cv.emit(cv.poly([(lan[0] - 5, 224), (lan[0] + 5, 224), (lan[0] + 3.5, 234), (lan[0] - 3.5, 234)]), '#FCE2B0')
    cv.emit(cv.box(lan[0] - 1, 226, lan[0] + 2, 232), '#FFF6DC')
    roofm = cv.poly([(lan[0] - 9, 222), (lan[0] + 9, 222), (lan[0], 213)])
    cv.put(roofm, '#0A0E16', 1.0)
    LF.snowcap(cv, roofm, 2, '#C2C9D2', 1505)
    cv.put(cv.seg([(lan[0], 213), (lan[0], 208)], 0.6), '#0A0E16', 1.0)
    # icicles under the coping
    for x in range(NEAR_X + 6, NEAR_X + NEAR_W, 17):
        ln = 2 + int(LF.hsh(x, 1.0, 2.0) * 5)
        y0 = 309 + (x - NEAR_X) * 0.008
        cv.put(cv.seg([(x + 0.5, y0), (x + 0.5, y0 + ln)], 0.5, 0.3), '#7D8796', 1.0)
    out = cv.quant(PAL, spread=10.0)
    L['near_at'] = [NEAR_X, NEAR_Y]
    L['near_lantern'] = [lan[0], 229]
    return out


def near_glow():
    """The roof lantern's halo (additive, 120 x 90 around it)."""
    return Q.glow_sprite(120, 90, [(60, 45, 46, 38, (70, 48, 22), 1.5), (60, 45, 14, 14, (60, 46, 26), 1.2)], 6.0)


def taxi():
    """r1: a small saloon (side view) driving along the far street, 2 frames (wheel spokes), 24 x 10, lit tail
    and head lights; the runtime adds the headlight beam."""
    frames = []
    for i in range(2):
        cv = LF.Cv(24, 10, 0, 0, amb=(0.5, 0.55, 0.7))
        LF.car(cv, 12.0, 9.0, s=0.46, facing=1, body='#26303A', snow='#7D8796', seed=70)
        cv.emit(cv.box(22, 5, 24, 7), '#FCE2B0')
        cv.emit(cv.box(0, 5, 1, 6), '#A8382E')
        if i == 1:
            cv.put(cv.box(6, 7, 7, 9) | cv.box(17, 7, 18, 9), '#2A3646', 1.0)
        frames.append(cv.quant(PAL, spread=6.0))
    L['taxi_path'] = [list(sq(-16.0, 0.0, 104.0)), list(sq(16.0, 0.0, 104.0))]
    return Q.sheet(frames)


def steam():
    """Big steam clouds of the 23.40 rising from the platforms below the roof: soft volumetric puffs (no dithered
    checkerboard), lit warm from below by the platform lamps, cold blue-grey on top, fraying as they rise."""
    return LF.soft_puff_sheet(6, 150, 110, LF.STEAM_LAMP, 4401, grow=(0.30, 0.50), light=(0.12, 0.95), thin=0.55,
                              drift=0.06, rise=0.04, alpha=0.86, wisp=0.55)
