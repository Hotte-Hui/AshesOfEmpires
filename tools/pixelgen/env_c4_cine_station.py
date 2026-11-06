"""env_c4_cine_station -- Veltrava station at first light, down the island platform (LS_C4_Homeward w1).

Owner: cine stream (polish pass).  The plate is ray-cast in a small box world so the game's own figures (56 px,
1.75 m) stand at the right size where they board: a camera 3.3 m above the platform looks down platform 5 under the
iron-and-glass shed.  Left: the westbound to Berlin (dark green Reich stock, lit compartments, the destination
boards BERLIN); right: the eastbound to Karsk (Soviet green, lace curtains, КАРСК); both trains' roofs carry the
night's snow.  Hanging globes and a clock over the platform, benches, a luggage trolley, mail sacks, the snow blown
in at the edges, the yellow edge lines; at the far end the shed opens on the dawn: the tracks running out, signals,
the locomotives' steam (runtime puffs), Veltrava's towers against the pink sky.

  station()      the opaque plate (640 x 360)
  glow()         additive: globes, lit windows' spill on the platform, the dawn in the opening
  doors()        the two carriage doors the men board, open / shut (they slam shut at the cue times)
  geometry       project() and the anchors written to layout.json "homeward"
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (VW, VH, DAWN, SNOWB, IRONK, SODIUM, PAPERB, CREAM)

# ------------------------------------------------------------------------------------------------ the camera
CX, CY = 320.0, 160.0                  # vanishing point
HC = 3.3                               # camera height above the platform (m)
F = 640.0                              # focal length (px)
PLAT = 2.9                             # platform half width (m)
WALL = 3.05                            # carriage side wall (|X|)
BODY = (-0.15, 3.0)                    # carriage body: Z from .. to (m above the platform)
ROOF_Z = 3.25
CAR_W = 2.9                            # carriage width (wall to wall)
CAR_L, CAR_GAP = 22.0, 1.2             # carriage length + gap between carriages (m)
TRAIN_D0 = -4.05                       # the trains run on behind the camera (m); a door centred at DOOR_D
TRAIN_END = 182.0                      # the locomotives' tenders end here (m)
SHED_END = 230.0                       # the shed opens here
VAULT_R, VAULT_Z0 = 15.0, 3.5          # barrel vault radius, axis height (m above the platform)
TRUSS = 9.0                            # truss spacing (m)
DOOR_D = 17.0                          # depth of the doors the men board (m)
DOOR_M = 20.1                          # the next door of the Berlin train (the mother and her boy board there)
DOOR_HALF = 0.55                       # half width of a door opening (m)
STEP_Z = 0.35                          # the vestibule floor above the platform (m)
LAMP_D = (19.0, 31.0, 43.0, 55.0, 67.0, 79.0, 91.0, 103.0)
LAMP_X = 1.45                          # two rows of hanging globes over the platform halves
LAMP_Z = 5.4


def project(X, Z, D):
    """World (lateral m, height m above the platform, depth m) -> image (x, y)."""
    return CX + X * F / D, CY + (HC - Z) * F / D


def depth_at_floor(y):
    return HC * F / max(1e-3, (y - CY))


def _rays():
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    dx = (xx + 0.5 - CX) / F
    dz = (CY - (yy + 0.5)) / F
    return yy, xx, dx, dz


def _hits():
    """Nearest surface per pixel: dict of masks + depth/coords."""
    yy, xx, dx, dz = _rays()
    INF = np.float32(1e9)
    D = np.full((VH, VW), INF, np.float32)
    kind = np.zeros((VH, VW), np.int8)          # 0 sky/open, 1 floor, 2 wall, 3 roof, 4 track, 5 vault, 6 far wall
    side = np.sign(dx)
    with np.errstate(divide='ignore', invalid='ignore'):
        # floor of the platform (Z = 0)
        Df = np.where(dz < 0, -HC / dz, INF)
        Xf = dx * Df
        ok = (np.abs(Xf) <= PLAT) & (Df < SHED_END + 400)
        D = np.where(ok, Df, D)
        kind = np.where(ok, 1, kind)
        # carriage side walls (|X| = WALL), body between BODY Z
        Dw = np.where(np.abs(dx) > 1e-6, WALL / np.abs(dx), INF)
        Zw = HC + dz * Dw
        okw = (Zw >= BODY[0]) & (Zw <= BODY[1]) & (Dw >= TRAIN_D0) & (Dw < D) & (Dw < TRAIN_END)
        D = np.where(okw, Dw, D)
        kind = np.where(okw, 2, kind)
        # carriage roofs (plane Z = ROOF_Z between WALL and WALL + CAR_W)
        Dr = np.where(dz < 0, -(HC - ROOF_Z) / dz, INF)
        Xr = np.abs(dx * Dr)
        okr = (Xr >= WALL) & (Xr <= WALL + CAR_W) & (Dr >= TRAIN_D0) & (Dr < D) & (Dr < TRAIN_END)
        D = np.where(okr, Dr, D)
        kind = np.where(okr, 3, kind)
        # the track bed (Z = -1.1) in the gaps and beyond
        Dt = np.where(dz < 0, -(HC + 1.1) / dz, INF)
        okt = (Dt < D) & (np.abs(dx * Dt) > PLAT)
        D = np.where(okt, Dt, D)
        kind = np.where(okt, 4, kind)
        # the vault: X^2 + (Z - Z0)^2 = R^2, the ray from inside
        a = dx * dx + dz * dz
        b = 2 * dz * (HC - VAULT_Z0)
        c = (HC - VAULT_Z0) ** 2 - VAULT_R ** 2
        Dv = (-b + np.sqrt(np.maximum(0, b * b - 4 * a * c))) / (2 * a + 1e-12)
        Zv = HC + dz * Dv
        okv = (Dv < D) & (Zv > 4.0) & (Dv < SHED_END)
        D = np.where(okv, Dv, D)
        kind = np.where(okv, 5, kind)
        # the shed's side walls below the vault's springing (|X| = 13.5)
        Dsw = np.where(np.abs(dx) > 1e-6, 13.5 / np.abs(dx), INF)
        Zsw = HC + dz * Dsw
        oks = (Dsw < D) & (Zsw > -1.1) & (Zsw <= 4.6) & (Dsw < SHED_END)
        D = np.where(oks, Dsw, D)
        kind = np.where(oks, 6, kind)
    X = dx * D
    Z = HC + dz * D
    return dict(yy=yy, xx=xx, dx=dx, dz=dz, D=D, X=X, Z=Z, kind=kind, side=side)


def _car_u(Dd):
    """Position along a carriage (m from its start) and the carriage index for a depth."""
    k = np.floor((Dd - TRAIN_D0) / (CAR_L + CAR_GAP))
    u = (Dd - TRAIN_D0) - k * (CAR_L + CAR_GAP)
    return u, k


def station():
    h = _hits()
    yy, xx, D, X, Z, kind, side = h['yy'], h['xx'], h['D'], h['X'], h['Z'], h['kind'], h['side']
    nz = Q.noise(VW, VH, 9, 8401)
    fine = Q.noise(VW, VH, 2, 8403)
    rgb = np.zeros((VH, VW, 3), np.float32)
    col = lambda hx: Q.hexrgb(hx)  # noqa: E731
    fog = np.clip((D - 20) / 210.0, 0, 1)[..., None]       # dawn haze down the shed
    haze = col('#7C7A90')
    # light: globes over the platform (warm), the dawn from the far opening (cool pink), the windows' spill
    lamp = np.zeros((VH, VW), np.float32)
    for ld in LAMP_D:
        for lx_ in (-LAMP_X, LAMP_X):
            d3 = np.sqrt((X - lx_) ** 2 + (Z - LAMP_Z) ** 2 + (D - ld) ** 2)
            lamp += np.clip(1 - d3 / 8.0, 0, 1) ** 1.6 * 0.7
    dawn = np.clip(1 - np.abs(D - SHED_END) / 120.0, 0, 1) ** 1.4

    # ---- the platform: stone slabs, the edge lines, snow blown in, wet patches reflecting the globes
    fl = kind == 1
    slab = (np.abs(np.mod(D, 1.2) - 0.6) > 0.56) | (np.abs(np.mod(X + 0.3, 1.0) - 0.5) > 0.47)
    base = col('#4A4C5C') * (0.55 + nz[..., None] * 0.25) + col('#C8A060') * lamp[..., None] * 0.55
    base = np.where(slab[..., None], base * 0.78, base)
    edge = np.abs(np.abs(X) - (PLAT - 0.25)) < 0.12
    base = np.where(edge[..., None], col('#B8A060') * (0.7 + lamp[..., None] * 0.4), base)
    lip = np.abs(X) > PLAT - 0.08
    base = np.where(lip[..., None], col('#D8D4CC') * 0.85, base)
    snow = (np.abs(X) > PLAT - 0.7 - fine * 0.5) & ~edge & ~lip
    base = np.where(snow[..., None], col('#AEB2C4') * (0.75 + nz[..., None] * 0.25) + col('#C8A060') *
                    lamp[..., None] * 0.35, base)
    wet = (fine > 0.62) & (np.abs(X) < 1.6)
    base = np.where(wet[..., None], base * 0.85 + col('#E8C890') * lamp[..., None] * 0.35, base)
    rgb[fl] = base[fl]

    # ---- the carriage walls: Reich stock left (dark green-blue), Soviet green right; windows, doors, boards
    wl = kind == 2
    u, k = _car_u(D)
    left = side < 0
    livery = np.where(left[..., None], col('#2A3846'), col('#2E4A2C'))
    wall = livery * (0.75 + nz[..., None] * 0.25) + col('#C89A58') * lamp[..., None] * 0.28
    # window band: Z 1.25 .. 2.25; windows 1.1 m wide every 1.8 m, doors at both ends
    wu = np.mod(u - 2.6, 1.8)
    is_door = (u < 1.9) | (u > CAR_L - 1.9)
    door_open = is_door & ((np.abs(D - DOOR_D) < DOOR_HALF) | (left & (np.abs(D - DOOR_M) < DOOR_HALF)))
    win = (Z > 1.25) & (Z < 2.25) & (wu < 1.1) & ~is_door
    warm = col('#E8B060') * (0.75 + fine[..., None] * 0.2)
    curtain = np.where(left[..., None], col('#8A6A4A'), col('#D8D0C0'))
    wv = np.mod(wu, 1.1)
    cur = (wv < 0.22) | (wv > 0.88)
    winc = np.where(cur[..., None], curtain * 0.8, warm)
    rack = (Z > 2.05) & (Z < 2.12)
    winc = np.where(rack[..., None], col('#5A4030'), winc)
    luggage = (Z > 2.12) & (Z < 2.25) & (np.mod(u * 3.1 + k, 2.0) < 0.9)
    winc = np.where(luggage[..., None], col('#6A4A2E') * 0.9, winc)
    wall = np.where(win[..., None], winc, wall)
    frame = (Z > 1.2) & (Z < 2.3) & (wu < 1.16) & ~win & ~is_door
    wall = np.where(frame[..., None], livery * 1.5, wall)
    # doors: panel, its window, handrails; the open doors the men board are dark with a lit step
    dpanel = is_door & (Z < 2.45)
    wall = np.where(dpanel[..., None], livery * 0.85, wall)
    dwin = is_door & (Z > 1.45) & (Z < 2.2) & (np.abs(np.mod(u, CAR_L - 1.9) - 0.95) < 0.35)
    wall = np.where(dwin[..., None], warm * 0.7, wall)
    rail_ = is_door & (np.abs(np.mod(u, CAR_L - 1.9) - 0.15) < 0.05) & (Z < 2.2) & (Z > 0.2)
    wall = np.where(rail_[..., None], col('#C8C0A8'), wall)
    wall = np.where((door_open & (Z < 2.4))[..., None], col('#2A1A10') + col('#E0A050') * 0.35 *
                    np.clip(Z, 0, 1)[..., None], wall)
    # belt lines, the cant rail, the solebar; the gap between carriages (bellows)
    belt = (np.abs(Z - 1.05) < 0.05) | (np.abs(Z - 2.6) < 0.04)
    wall = np.where(belt[..., None], np.where(left[..., None], col('#B49A5A'), col('#C8B070')) * 0.8, wall)
    cant = Z > 2.82
    wall = np.where(cant[..., None], livery * 0.6, wall)
    snowl = Z > 2.95
    wall = np.where(snowl[..., None], col('#C8CCD8') * 0.85, wall)                  # the snow on the roof edge
    sole = Z < 0.05
    wall = np.where(sole[..., None], col('#16181A'), wall)
    gap = u > CAR_L
    fold = np.mod(np.floor((u - CAR_L) * 6.0), 2) == 0
    wall = np.where(gap[..., None], np.where(fold[..., None], col('#24242A'), col('#18181C')), wall)
    # destination boards under the windows of every second carriage
    board = (Z > 0.55) & (Z < 0.9) & (np.abs(u - CAR_L / 2) < 1.6) & (np.mod(k, 2) == 0)
    wall = np.where(board[..., None], col('#E2DCC8') * 0.9, wall)
    wall = wall * (1 - fog * 0.85) + haze * fog * 0.85
    rgb[wl] = wall[wl]

    # ---- carriage roofs: snow, ventilators, the edge
    rf = kind == 3
    ru, rk = _car_u(D)
    roof = col('#9EA4B8') * (0.7 + nz[..., None] * 0.3)
    vent = (np.abs(np.mod(ru, 2.4) - 1.2) < 0.22) & (np.abs(np.abs(X) - (WALL + CAR_W / 2)) < 0.3)
    roof = np.where(vent[..., None], col('#3A3C44'), roof)
    redge = np.abs(np.abs(X) - WALL) < 0.12
    roof = np.where(redge[..., None], col('#2A2C34'), roof)
    rgap = ru > CAR_L
    roof = np.where(rgap[..., None], col('#16161A'), roof)
    roof = roof * (1 - fog * 0.8) + haze * fog * 0.8
    rgb[rf] = roof[rf]

    # ---- track beds: ballast, sleepers, rails with a dawn gleam; the tracks beyond the trains
    tk = kind == 4
    sl = np.abs(np.mod(D, 0.7) - 0.35) < 0.1
    trk = col('#2A2830') * (0.7 + nz[..., None] * 0.3)
    trk = np.where(sl[..., None], col('#3A3026'), trk)
    for rx in (4.1, 5.6, 9.1, 10.6):
        rr = np.abs(np.abs(X) - rx) < 0.05 + D * 0.0006
        trk = np.where(rr[..., None], col('#A8A0B0') * (0.5 + dawn[..., None] * 0.6), trk)
    trk = trk * (1 - fog * 0.8) + haze * fog * 0.8
    rgb[tk] = trk[tk]

    # ---- the vault: iron trusses (arched ribs), purlins, dirty glass with the dawn behind
    vt = kind == 5
    ang = np.arctan2(X, Z - VAULT_Z0)
    rib = np.abs(np.mod(D, TRUSS) - TRUSS / 2) > TRUSS / 2 - 0.22
    purl = np.abs(np.mod(ang * 12.0 / math.pi, 1.0) - 0.5) > 0.46
    up = np.clip((Z - 6.0) / 12.0, 0, 1)[..., None]
    glass = col('#6E6C86') * (0.62 + up * 0.25 + nz[..., None] * 0.08) + col('#E8B8A8') * dawn[..., None] * 0.30
    pane = np.abs(np.mod(D, TRUSS / 3) - TRUSS / 6) > TRUSS / 6 - 0.07
    glass = np.where(pane[..., None], glass * 0.86, glass)
    soot = np.clip((Q.noise(VW, VH, 26, 8405) - 0.45) * 2.0, 0, 1)[..., None] * (1 - up)
    glass = glass * (1 - soot * 0.22)
    snowg = np.clip((np.abs(X) - 10.0) / 3.0, 0, 1)[..., None]
    glass = glass * (1 - snowg * 0.5) + col('#A8A8BC') * snowg * 0.5
    vault = np.where((rib | purl)[..., None], col('#1E2028') + col('#C8A060') * lamp[..., None] * 0.2, glass)
    ridge = np.abs(ang) < 0.04
    vault = np.where(ridge[..., None], col('#2A2A34'), vault)
    vault = vault * (1 - fog * 0.6) + col('#B8A0A8') * fog * 0.6
    rgb[vt] = vault[vt]
    # the shed's side walls: brick arcades
    sw = kind == 6
    arc_ = np.abs(np.mod(D, TRUSS) - TRUSS / 2) < TRUSS / 2 - 1.2
    winz = (Z > 0.8) & (Z < 3.9) & arc_
    swc = col('#3A2C30') * (0.75 + nz[..., None] * 0.25)
    swc = np.where(winz[..., None], col('#9A7C8A') * (0.8 + dawn[..., None] * 0.4), swc)
    mull = winz & (np.abs(np.mod(D, TRUSS / 3) - TRUSS / 6) > TRUSS / 6 - 0.15)
    swc = np.where(mull[..., None], col('#2A2228'), swc)
    swc = swc * (1 - fog * 0.7) + haze * fog * 0.7
    rgb[sw] = swc[sw]

    # ---- the opening at the far end: dawn sky, the town's towers, tracks running out
    op = kind == 0
    t = np.clip((yy - 70) / (CY - 70), 0, 1)[..., None]
    sky = col('#4E4A68') * (1 - t) + col('#E8A890') * t
    # Veltrava against the dawn: roofs, two towers, signal lamps
    sil = (yy > CY - 9 - (np.mod(np.floor(xx / 5) * 7.3, 5.0)) * (np.abs(xx - CX) < 46)) & (yy <= CY + 2)
    sil |= (np.abs(xx - (CX - 22)) < 2) & (yy > CY - 26) & (yy <= CY)
    sil |= (np.abs(xx - (CX + 30)) < 3) & (yy > CY - 20) & (yy <= CY)
    sky = np.where(sil[..., None], col('#5A4A62'), sky)
    rgb[op] = sky[op]
    out = np.clip(rgb, 0, 255)
    img = np.zeros((VH, VW, 4), np.uint8)
    img[..., :3] = out.astype(np.uint8)
    img[..., 3] = 255
    _props(img, h, lamp)
    pal = _palette()
    return Q.requant(img[..., :3].astype(np.float32), pal, 10.0, alpha=None), h


def _palette():
    """A shared station palette (dawn blues, iron, the two liveries, warm windows, snow)."""
    return (['#0E0E14', '#16161E', '#1E2028', '#282A34', '#343644', '#424456', '#54566A', '#6A6C82', '#82849A',
             '#9EA0B4', '#BCBECE', '#D8D8E2', '#F0EEF2'] +
            ['#1C2A2A', '#283A3A', '#344A48', '#22381F', '#2E4A2C', '#3E6038'] +
            ['#3A2214', '#5A3A1E', '#8A5A2A', '#B47A36', '#D89A4A', '#EEC070', '#FAE0A0'] +
            ['#6A5A70', '#9A7A88', '#C8988E', '#E8B49A', '#F4CDB4'] +
            ['#8A7A50', '#B8A060', '#D8C890', '#C8C0A8', '#E2DCC8'] +
            ['#4A3A30', '#6A4A2E', '#8A6A4A'])


def _props(img, h, lamp):
    """Things standing on the platform and hanging under the vault (drawn into `img` RGB)."""
    P = lambda X, Z, D: project(X, Z, D)  # noqa: E731

    def rect3(X0, X1, Z0, Z1, D, hexcol, shade=1.0):
        x0, y0 = P(X0, Z1, D)
        x1, y1 = P(X1, Z0, D)
        a0, b0, a1, b1 = int(round(min(x0, x1))), int(round(y0)), int(round(max(x0, x1))), int(round(y1))
        if a1 <= a0:
            a1 = a0 + 1
        if b1 <= b0:
            b1 = b0 + 1
        img[max(0, b0):min(VH, b1), max(0, a0):min(VW, a1), :3] = (Q.hexrgb(hexcol) * shade).astype(np.uint8)

    def box3(X0, X1, Z0, Z1, D0, D1, front, top=None, shade=True):
        """A box on the platform: the face toward the camera at D0 and its top face back to D1 -- the front lit
        from above (lighter top, darker foot, grain), a highlight along its top edge, the top face lighter."""
        x0, y1 = P(X0, Z0, D0)
        x1, y0 = P(X1, Z1, D0)
        a0, a1 = int(round(min(x0, x1))), int(round(max(x0, x1)))
        b0, b1 = int(round(y0)), int(round(y1))
        tx0, ty1 = P(X0, Z1, D1)
        tx1, _ = P(X1, Z1, D1)
        topm = np.zeros((VH, VW), bool)
        tb0, tb1 = int(round(ty1)), b0
        if tb1 > tb0:
            for yrow in range(max(0, tb0), min(VH, tb1)):
                u = (yrow - ty1) / max(1e-3, (b0 - ty1))
                l_ = min(tx0, tx1) + (min(x0, x1) - min(tx0, tx1)) * u
                r_ = max(tx0, tx1) + (max(x0, x1) - max(tx0, tx1)) * u
                topm[yrow, max(0, int(round(l_))):max(0, int(round(r_)) + 1)] = True
        tc = Q.hexrgb(top or front)
        img[topm, :3] = np.clip(tc * (1.08 + grain[topm, None] * 0.12), 0, 255).astype(np.uint8)
        fy0, fy1 = max(0, b0), min(VH, max(b1, b0 + 1))
        fx0, fx1 = max(0, a0), min(VW, max(a1, a0 + 1))
        if fy1 <= fy0 or fx1 <= fx0:
            return
        fc = Q.hexrgb(front)
        if not shade:
            img[fy0:fy1, fx0:fx1, :3] = fc.astype(np.uint8)
            return
        v = (np.arange(fy0, fy1, dtype=np.float32) - b0) / max(1.0, b1 - b0)
        k = (1.10 - 0.34 * v)[:, None] + grain[fy0:fy1, fx0:fx1] * 0.10
        img[fy0:fy1, fx0:fx1, :3] = np.clip(fc[None, None] * k[..., None], 0, 255).astype(np.uint8)
        if fy1 - fy0 >= 3:
            img[fy0, fx0:fx1, :3] = np.clip(fc * 1.35 + 14, 0, 255).astype(np.uint8)
        if fy1 < VH:
            img[fy1 - 1, fx0:fx1, :3] = np.clip(fc * 0.55, 0, 255).astype(np.uint8)

    yy, xx = np.mgrid[0:VH, 0:VW]
    grain = Q.noise(VW, VH, 2, 8409) - 0.5
    # the hanging globes in two rows: rods, the globes (the glow is added separately)
    for ld in LAMP_D:
        for lx_ in (-LAMP_X, LAMP_X):
            x, y0 = P(lx_, 9.5, ld)
            _, y1 = P(lx_, LAMP_Z + 0.2, ld)
            r = max(1.0, 0.22 * F / ld)
            img[int(y0):int(y1), int(round(x)):int(round(x)) + 1, :3] = Q.hexrgb('#1E2028').astype(np.uint8)
            cy_ = P(lx_, LAMP_Z, ld)[1]
            m = (xx - x) ** 2 + (yy - cy_) ** 2 <= r * r
            img[m, :3] = Q.hexrgb('#FAE0A0').astype(np.uint8)
            img[m & (yy > cy_ + r * 0.35), :3] = Q.hexrgb('#EEC070').astype(np.uint8)
            cap = (np.abs(xx - x) <= r * 0.6) & (yy >= cy_ - r - 1) & (yy < cy_ - r + 1)
            img[cap, :3] = Q.hexrgb('#282A34').astype(np.uint8)
    # the clock hanging over the middle (two faces), the platform number 5 under it
    cd = 25.0
    cx_, cyc = P(0, 5.6, cd)
    r = 0.42 * F / cd
    m = (xx - cx_) ** 2 + (yy - cyc) ** 2 <= r * r
    img[m, :3] = Q.hexrgb('#E2DCC8').astype(np.uint8)
    ring = m & ((xx - cx_) ** 2 + (yy - cyc) ** 2 > (r - 1.6) ** 2)
    img[ring, :3] = Q.hexrgb('#1E2028').astype(np.uint8)
    img[int(cyc - r + 3):int(cyc) + 1, int(round(cx_)), :3] = Q.hexrgb('#1E2028').astype(np.uint8)
    img[int(cyc), int(round(cx_)):int(round(cx_ + r - 4)), :3] = Q.hexrgb('#1E2028').astype(np.uint8)
    _, ytop = P(0, 10.0, cd)
    img[int(ytop):int(cyc - r), int(round(cx_)), :3] = Q.hexrgb('#1E2028').astype(np.uint8)
    nx, ny = P(0, 4.55, cd)
    _, nyt = P(0, 4.95, cd)
    _, nyb = P(0, 4.15, cd)
    bw = int(round(0.55 * F / cd))
    img[int(nyt):int(nyb), int(round(nx)) - bw:int(round(nx)) + bw, :3] = Q.hexrgb('#E2DCC8').astype(np.uint8)
    t5 = Q.text('5', 'l', 1)
    th, tw = t5.shape
    sub = img[int(ny) - th // 2:int(ny) - th // 2 + th, int(round(nx)) - tw // 2:int(round(nx)) - tw // 2 + tw, :3]
    sub[t5] = Q.hexrgb('#1E2028').astype(np.uint8)
    # far to near: the locomotives' tenders closing the trains, a kiosk, sacks, a trolley, benches -- every face
    # shaded (lit top, darker foot, a highlight on the top edge, a contact line on the floor), with their parts
    for sg in (-1, 1):
        lo, hi = (WALL, WALL + CAR_W) if sg > 0 else (-(WALL + CAR_W), -WALL)
        box3(lo, hi, BODY[0], 3.6, TRAIN_END, TRAIN_END + 6, '#1A1A20', '#3A3A44')
    _kiosk(img, P, box3)
    for bd in (37.0, 61.0, 85.0):
        for sx_ in (-1, 1):
            _bench(img, P, box3, sx_, bd)
    _trolley(img, P, box3)
    _sacks(img, P)
    box3(-1.7, -1.1, 0.0, 0.62, 45.0, 45.8, '#5A2A20', '#7A3A2A')              # a trunk, its lid and straps
    box3(-1.72, -1.08, 0.62, 0.72, 45.0, 45.8, '#6A3424', '#8A4A32')
    for sx_ in (-1.55, -1.25):
        x, y0 = P(sx_, 0.72, 45.0)
        _, y1 = P(sx_, 0.0, 45.0)
        img[int(round(y0)):int(round(y1)), int(round(x)), :3] = Q.hexrgb('#B8A060').astype(np.uint8)
    # the destination boards on the near carriages: BERLIN left, КАРСК right
    for sgn, txt in ((-1, 'BERLIN'), (1, 'КАРСК')):
        for bd in (TRAIN_D0 + CAR_L / 2, TRAIN_D0 + (CAR_L + CAR_GAP) * 2 + CAR_L / 2):
            x, y = P(sgn * WALL, 0.72, bd)
            tm = Q.text(txt, 's', 1)
            th, tw = tm.shape
            x0 = int(round(x)) - (tw + 4 if sgn < 0 else -4)
            y0 = int(round(y)) - th // 2
            if 0 <= y0 and y0 + th < VH and 0 <= x0 and x0 + tw < VW:
                img[y0 - 1:y0 + th + 1, x0 - 2:x0 + tw + 2, :3] = Q.hexrgb('#E2DCC8').astype(np.uint8)
                sub = img[y0:y0 + th, x0:x0 + tw, :3]
                sub[tm] = Q.hexrgb('#283A3A' if sgn < 0 else '#2E4A2C').astype(np.uint8)


def _bench(img, P, box3, sx_, bd):
    """A platform bench (slatted seat and back on cast-iron end frames), facing the camera."""
    lo, hi = (0.35, 1.55) if sx_ > 0 else (-1.55, -0.35)
    for ex in (lo + 0.04, hi - 0.10):                                            # the end frames, cast iron
        box3(ex, ex + 0.06, 0.0, 0.92, bd + 0.02, bd + 0.46, '#1E1C20', '#2A282C')
    box3(lo, hi, 0.40, 0.47, bd, bd + 0.42, '#5A3A1E', '#8A6A4A')               # the seat
    box3(lo, hi, 0.55, 0.95, bd + 0.40, bd + 0.46, '#4A3020', '#6A4A2E')        # the back
    for zz in (0.68, 0.81):                                                      # the gaps between the slats
        x0, y = P(lo, zz, bd + 0.40)
        x1, _ = P(hi, zz, bd + 0.40)
        yi = int(round(y))
        if 0 <= yi < VH:
            img[yi, int(round(min(x0, x1))):int(round(max(x0, x1))), :3] = Q.hexrgb('#24160E').astype(np.uint8)
    x0, y = P(lo, 0.0, bd + 0.5)                                                 # its shadow on the stones
    x1, _ = P(hi, 0.0, bd + 0.5)
    yi = int(round(y))
    if 0 <= yi < VH:
        seg = img[yi, int(round(min(x0, x1))) + 1:int(round(max(x0, x1))), :3].astype(np.float32)
        img[yi, int(round(min(x0, x1))) + 1:int(round(max(x0, x1))), :3] = (seg * 0.6).astype(np.uint8)


def _trolley(img, P, box3):
    """The porters' luggage trolley: a deck on iron wheels, the drawbar down on the stones, two suitcases with
    straps and brass corners and a hat box."""
    box3(1.15, 2.35, 0.26, 0.40, 29.0, 31.2, '#2A2C34', '#4A4C56')               # the deck
    for wx in (1.25, 2.15):                                                      # the wheels (the near pair)
        cx, cy = P(wx + 0.05, 0.13, 29.0)
        r = max(1.5, 0.13 * F / 29.0)
        yy, xx = np.mgrid[0:VH, 0:VW]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        img[m, :3] = Q.hexrgb('#16161A').astype(np.uint8)
        img[m & ((xx - cx) ** 2 + (yy - cy) ** 2 <= (r * 0.4) ** 2), :3] = Q.hexrgb('#6A6C82').astype(np.uint8)
    x0, y0 = P(1.75, 0.33, 29.0)                                                 # the drawbar
    x1, y1 = P(1.75, 0.0, 27.4)
    for i in range(24):
        u = i / 23.0
        xi, yi = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
        if 0 <= yi < VH and 0 <= xi < VW:
            img[yi, xi, :3] = Q.hexrgb('#1E2028').astype(np.uint8)
    box3(1.22, 2.28, 0.40, 0.78, 29.3, 31.0, '#6A4A2E', '#8A6A4A')              # the big suitcase
    box3(1.40, 2.10, 0.78, 1.08, 29.6, 30.7, '#7A3A2A', '#9A5A3A')              # the small one
    box3(1.55, 1.90, 1.08, 1.30, 29.9, 30.4, '#5A5A6A', '#7A7A8A')              # a hat box
    for (X0, X1, Z0, Z1, dd) in ((1.22, 2.28, 0.40, 0.78, 29.3), (1.40, 2.10, 0.78, 1.08, 29.6)):
        for sxx in (X0 + (X1 - X0) * 0.3, X0 + (X1 - X0) * 0.7):                 # the straps
            x, ya = P(sxx, Z1, dd)
            _, yb = P(sxx, Z0, dd)
            img[int(round(ya)):int(round(yb)), int(round(x)), :3] = Q.hexrgb('#3A2214').astype(np.uint8)
        for cxx in (X0, X1):                                                     # brass corners
            x, ya = P(cxx, Z1, dd)
            xi = int(round(x)) - (0 if cxx == X0 else 1)
            img[int(round(ya)):int(round(ya)) + 2, xi:xi + 1, :3] = Q.hexrgb('#D89A4A').astype(np.uint8)


def _sacks(img, P):
    """Three mail sacks heaped by the left edge: rounded canvas, the tied necks, a little snow on top."""
    yy, xx = np.mgrid[0:VH, 0:VW]
    for (X, Z, D, rx, rz, col_) in ((-2.05, 0.28, 33.3, 0.42, 0.30, '#6A6252'), (-1.68, 0.26, 33.6, 0.36, 0.27,
                                                                                   '#7A7262'),
                                    (-1.88, 0.62, 33.5, 0.32, 0.24, '#8A8274')):
        cx, cy = P(X, Z, D)
        ax = rx * F / D
        az = rz * F / D
        d = ((xx - cx) / max(1.0, ax)) ** 2 + ((yy - cy) / max(1.0, az)) ** 2
        m = d <= 1.0
        base = Q.hexrgb(col_)
        k = 1.12 - 0.35 * np.clip((yy - (cy - az)) / max(1.0, 2 * az), 0, 1)
        img[m, :3] = np.clip(base[None] * k[m][:, None], 0, 255).astype(np.uint8)
        img[m & (d > 0.72) & (yy > cy), :3] = np.clip(base * 0.6, 0, 255).astype(np.uint8)
        nx, ny = P(X + rx * 0.2, Z + rz * 0.95, D)                               # the tied neck
        img[int(round(ny)) - 2:int(round(ny)), int(round(nx)) - 1:int(round(nx)) + 1, :3] = \
            Q.hexrgb('#4A3A30').astype(np.uint8)
        top = m & (yy < cy - az * 0.6)
        img[top, :3] = Q.hexrgb('#BCBECE').astype(np.uint8)


def _kiosk(img, P, box3):
    """The newspaper kiosk at the far end of the platform: its body, the lit window with the papers clipped
    above it, the sign band and the roof overhang."""
    box3(-0.9, 0.9, 0.0, 2.5, 120.0, 124.0, '#4A3A30', '#6A5A4A')
    box3(-1.05, 1.05, 2.5, 2.72, 119.7, 124.2, '#2A2A34', '#5A5A6A')            # the roof overhang
    box3(-0.8, 0.8, 2.12, 2.42, 119.95, 120.0, '#E2DCC8', shade=False)           # the sign band
    box3(-0.7, 0.7, 1.05, 1.95, 119.9, 120.0, '#EEC070', shade=False)            # the lit window
    for i, cx in enumerate((-0.5, -0.15, 0.2, 0.5)):                             # papers on the line
        box3(cx - 0.12, cx + 0.12, 1.6, 1.9, 119.85, 119.9, ('#D8D4CC', '#B8A060', '#C8C0A8', '#E2DCC8')[i],
             shade=False)
    box3(-0.8, 0.8, 0.95, 1.05, 119.6, 120.0, '#6A5A4A', '#8A7A5A')              # the counter


def glow(h):
    """Additive light: the globes, their pools, the dawn in the opening, window spill on the platform edges."""
    blobs = []
    for ld in LAMP_D:
        x, y = project(0, LAMP_Z, ld)
        s = F / ld
        blobs.append((x, y, s * 1.6, s * 1.4, (90, 64, 30), 1.4))
        fx, fy = project(0, 0, ld)
        blobs.append((fx, fy, s * 2.4, s * 0.7, (40, 28, 12), 1.5))
    blobs.append((CX, CY - 6, 90, 60, (60, 40, 40), 1.3))
    for sgn in (-1, 1):
        for dd in (16.0, 22.0, 30.0):
            x, y = project(sgn * (PLAT - 0.4), 0, dd)
            s = F / dd
            blobs.append((x, y, s * 1.2, s * 0.35, (44, 30, 12), 1.5))
    return Q.glow_sprite(VW, VH, blobs, 6.0)


def door_sprites():
    """The two doors the men board, as [open, shut] frames each (left door, right door) + their top-left."""
    out = {}
    for sgn, key, livery in ((-1, 'k', '#283A3A'), (1, 'a', '#2E4A2C')):
        d0, d1 = DOOR_D - 0.55, DOOR_D + 0.55
        xa, ya = project(sgn * WALL, 2.4, d0)
        xb, yb = project(sgn * WALL, BODY[0], d0)
        xc, yc = project(sgn * WALL, 2.4, d1)
        xd, yd = project(sgn * WALL, BODY[0], d1)
        x0 = int(math.floor(min(xa, xb, xc, xd)))
        x1 = int(math.ceil(max(xa, xb, xc, xd))) + 1
        y0 = int(math.floor(min(ya, yc)))
        y1 = int(math.ceil(max(yb, yd))) + 1
        w, h = x1 - x0, y1 - y0
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        Xs, Ys = xx + x0 + 0.5, yy + y0 + 0.5
        dx = (Xs - CX) / F
        dz = (CY - Ys) / F
        Dw = WALL / np.maximum(np.abs(dx), 1e-6)
        Zw = HC + dz * Dw
        inside = (Dw >= d0) & (Dw <= d1) & (Zw >= BODY[0]) & (Zw <= 2.4)
        lv = Q.hexrgb(livery)
        shut = np.zeros((h, w, 4), np.uint8)
        c = np.where((np.abs(Dw - DOOR_D) < 0.28)[..., None] & ((Zw > 1.45) & (Zw < 2.2))[..., None],
                     Q.hexrgb('#B47A36'), lv * 0.95)
        c = np.where((np.abs(Dw - (d1 if sgn < 0 else d0)) < 0.06)[..., None], lv * 1.5, c)
        c = np.where(((np.abs(Dw - (d0 if sgn < 0 else d1)) < 0.06) & (Zw < 2.2) & (Zw > 0.2))[..., None],
                     Q.hexrgb('#C8C0A8'), c)
        shut[..., :3] = c.astype(np.uint8)
        shut[..., 3] = np.where(inside, 255, 0)
        opn = np.zeros_like(shut)
        out[key] = (Q.sheet([opn, shut]), [x0, y0])
    return out


def _opening(sgn, dd):
    """Screen rect [x0, y0, x1, y1] of a door opening (the hole in the carriage wall) at depth dd."""
    pts = [project(sgn * WALL, z, d) for z in (BODY[0], 2.4) for d in (dd - DOOR_HALF, dd + DOOR_HALF)]
    xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
    return [int(math.floor(min(xs))), int(math.floor(min(ys))), int(math.ceil(max(xs))), int(math.ceil(max(ys)))]


def anchors():
    """Feet positions of the walk, the doors, the steam points, NPC spots (layout.json 'homeward').
    Round 10: door_* is the threshold (on the wall line, where a boarder stands before stepping up), w1_in_* the
    vestibule floor half a metre inside (where he goes on stepping in), w1_open_* the opening's screen rect (what
    hides him: the jambs); the conductors stand where they never cover an opening."""
    kx, ky = project(-(WALL - 0.08), 0, DOOR_D)
    ax, ay = project(WALL - 0.08, 0, DOOR_D)
    mx, my = project(-(WALL - 0.08), 0, DOOR_M)
    ins = {key: project(sg * (WALL + 0.45), STEP_Z, dd) for key, sg, dd in (('k', -1, DOOR_D), ('a', 1, DOOR_D),
                                                                           ('m', -1, DOOR_M))}
    s0x, s0y = project(-0.5, 0, 14.4)
    s1x, s1y = project(0.5, 0, 14.4)
    far_l = project(-(WALL + CAR_W / 2), ROOF_Z + 1.0, 150.0)
    far_r = project(WALL + CAR_W / 2, ROOF_Z + 1.0, 150.0)
    under = [list(project(sg * (WALL - 0.1), -0.1, dd)) for sg in (-1, 1) for dd in (14.6, 25.4, 48.6)]
    return {'door_k': [round(kx), round(ky)], 'door_a': [round(ax), round(ay)], 'door_m': [round(mx), round(my)],
            'w1_in_k': [round(ins['k'][0]), round(ins['k'][1])], 'w1_in_a': [round(ins['a'][0]), round(ins['a'][1])],
            'w1_in_m': [round(ins['m'][0]), round(ins['m'][1])],
            'w1_open_k': _opening(-1, DOOR_D), 'w1_open_a': _opening(1, DOOR_D), 'w1_open_m': _opening(-1, DOOR_M),
            'w1_start_k': [round(s0x), round(s0y)], 'w1_start_a': [round(s1x), round(s1y)],
            'w1_steam': [[round(far_l[0]), round(far_l[1])], [round(far_r[0]), round(far_r[1])]],
            'w1_steam_under': [[round(a), round(b)] for (a, b) in under],
            'w1_npc': {'conductor_k': [round(project(-2.0, 0, 15.0)[0]), round(project(0, 0, 15.0)[1])],
                       'conductor_a': [round(project(2.0, 0, 15.0)[0]), round(project(0, 0, 15.0)[1])],
                       'porter': [round(project(1.0, 0, 14.0)[0]), round(project(0, 0, 14.0)[1])],
                       'mother': [round(project(-1.4, 0, 15.8)[0]), round(project(0, 0, 15.8)[1])],
                       'babushka': [round(project(2.75, 0, 13.6)[0]), round(project(0, 0, 13.6)[1])]},
            'vp': [int(CX), int(CY)]}
