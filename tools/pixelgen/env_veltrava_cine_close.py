"""env_veltrava_cine_close -- art of LS_C3_Close (owner: cinematics stream).

n1  platform 5 at 23.40, one-point perspective down the track (pinhole PROJ shared with
    scenes/cinematics/ch3_close/ch3_close.gd, which draws the departing special train in the same projection):
    the canopy and its lamps, the empty dual-gauge track, the dark yard beyond, the split-flap indicator.
n2  the station square at night in snow: two hotels far apart, one lit window each (Konrad left, Alexei
    right), a street lamp, a parked car under the limes with someone smoking in it.
Called by env_veltrava_cine.main(); every function returns RGBA arrays (or MLayers).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
V = C.V
PROJ = {'vpx': 236.0, 'vpy': 168.0, 'f': 420.0, 'eye': 1.7}
LAYOUT = C.LAYOUT.setdefault('close', {})
LAYOUT['proj'] = dict(PROJ)
LAMPS_Z = [6.0, 16.0, 26.0, 36.0, 46.0, 56.0]
LAMP_X, LAMP_Y = 0.8, 3.75
CANOPY_Y = 4.35
EDGE_X = 1.0
RAILS = (2.18, 3.62)          # broad-gauge pair ...
RAILS_STD = (2.18, 3.29)      # ... and the inner standard-gauge rail (four-rail dual gauge, WORLD_BIBLE)

NIGHT = ['#05070C', '#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70',
         '#687789', '#8593A3']
LAMPR = ['#22150F', '#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0']
SNOWR = ['#1A2431', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7']
IRONR = ['#05070C', '#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E']


def proj(x, y, z):
    zz = max(z, 0.3)
    return (PROJ['vpx'] + PROJ['f'] * x / zz, PROJ['vpy'] - PROJ['f'] * (y - PROJ['eye']) / zz)


def _grid():
    return np.mgrid[0:VH, 0:VW].astype(np.float32)


def plane_y(yy, xx, y_world):
    """For a horizontal plane at height y_world: per-pixel depth z and lateral x (nan where not visible)."""
    dy = yy - PROJ['vpy']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = -PROJ['f'] * (y_world - PROJ['eye']) / dy
        x = (xx - PROJ['vpx']) * z / PROJ['f']
    bad = ~(z > 0.2)
    z = np.where(bad, np.nan, z)
    x = np.where(bad, np.nan, x)
    return z, x


def lamp_pool(z, x, strength=1.0):
    """Warm light on the platform/track from the canopy lamps (falls off with distance)."""
    out = np.zeros(np.shape(z), np.float32)
    for lz in LAMPS_Z:
        d = np.hypot(np.nan_to_num(z, nan=1e3, posinf=1e3, neginf=1e3) - lz,
                     (np.nan_to_num(x, nan=1e3, posinf=1e3, neginf=1e3) - LAMP_X) * 1.3)
        out = np.maximum(out, np.clip(1 - d / 3.6, 0, 1) ** 1.5)
    return out * strength


# =========================================================================== n1: platform 5
PL6_X0, PL6_X1 = 9.2, 14.6                       # platform 6 (surface y = 0) between track 6 and track 7
PL6_END = 96.0
PL6_LAMP_X = 10.7
PL6_LAMPS_Z = [8.0, 18.0, 28.0, 38.0, 48.0, 58.0, 68.0, 78.0]
PL6_LIT = (8.0, 28.0, 48.0, 68.0)                # night economy: every other lamp of the empty platform is out


def plane_x(yy, xx, x_world):
    """For a vertical plane x = x_world (facing the camera's track): per-pixel depth z and height y (nan behind)."""
    dx = xx - PROJ['vpx']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = PROJ['f'] * x_world / dx
        y = PROJ['eye'] - (yy - PROJ['vpy']) * z / PROJ['f']
    bad = ~(z > 0.2)
    return np.where(bad, np.nan, z), np.where(bad, np.nan, y)


def _q(p, pts):
    return p.poly([proj(*q) for q in pts])


def _n1_right(p, ground, zg, xg):
    """AD round 2: the right third of the platform shot is no longer an empty field under a ruler-straight horizon.
    Platform 6 under its own canopy (every other lamp lit, pools of light on the trodden snow, cast-iron columns,
    the sign '6', a bench, a mail barrow), track 7 empty, a sleeping-car train standing on track 8 with two lit
    compartments, the long goods shed with its loading doors, lamps and snowy roof, over which the water tower and a
    floodlight mast of the yard show, a water crane with a fire pot glowing at its foot, a signal gantry over the
    tracks, a plank crossing for the porters' barrows -- all in the platform's one-point perspective."""
    yy, xx = p.yy, p.xx
    vpx, vpy = PROJ['vpx'], PROJ['vpy']
    zgn = np.nan_to_num(zg, nan=1e4, posinf=1e4, neginf=1e4)
    xgn = np.nan_to_num(xg, nan=-99.0, posinf=-99.0, neginf=-99.0)
    far = np.clip((zgn - 8) / 90, 0, 1)
    # ---- the ground right of track 6: snow over the track bed, tracks 7 and 8, the yard beyond
    yard = ground & (xgn > PL6_X0)
    p.put(yard, 'W', 3.0 - far * 1.1 + (pg.value_noise(VW, VH, 10, 731, 2) - 0.5) * 0.6)
    for (r0, r1) in ((15.6, 17.1), (19.8, 21.3)):
        sl = yard & (xgn > r0 - 0.4) & (xgn < r1 + 0.4) & (np.mod(np.clip(zgn, 0, 1e4), 0.65) < 0.2) & (zgn < 90)
        p.put(sl, 'W', 2.2 - far * 0.6)
        for rx in (r0, r1):
            rm = p.line([proj(rx, -1.0, 6.0), proj(rx, -1.0, 400.0)], 0.5) & yard
            p.put(rm, 'I', 3.2)
            p.put(rm & ~C.shift(rm, 0, -1), 'W', 5.4)
    for rx in (6.4, 7.9):                                                     # track 6 (under the goods train)
        p.put(p.line([proj(rx, -1.0, 3.0), proj(rx, -1.0, 400.0)], 0.5) & ground, 'W', 4.6)
    # ---- far down the yard, over the goods train: the water tower and a floodlight mast break the skyline
    wz_, wx_ = 150.0, 30.0
    wt0, wt1 = proj(wx_ - 1.5, -1.0, wz_), proj(wx_ + 1.5, 13.0, wz_)               # the brick shaft
    p.put(p.box(wt0[0], wt1[1], wt1[0] + 1, wt0[1]), 'N', 5.4)
    t0_, t1_ = proj(wx_ - 3.2, 13.0, wz_), proj(wx_ + 3.2, 18.0, wz_)
    tank = p.box(t0_[0], t1_[1], t1_[0] + 1, t0_[1])
    p.put(tank, 'N', 6.4)
    p.put(tank & ((yy.astype(int) % 2) == 0) & (xx > (t0_[0] + t1_[0]) / 2), 'N', 7.4)
    p.put(tank & ((yy.astype(int) - int(t1_[1])) == 2), 'N', 4.0)                    # the iron band
    rf = p.poly([(t0_[0] - 1, t1_[1]), ((t0_[0] + t1_[0]) / 2, t1_[1] - 4), (t1_[0] + 2, t1_[1])])
    p.put(rf, 'W', 5.4)
    p.put(tank & ~C.shift(tank, 0, -1), 'W', 6.0)
    p.px((t0_[0] + t1_[0]) / 2 + 2, t0_[1] + 3, 'L', 3.6)
    m0, m1 = proj(42.0, -1.0, 170.0), proj(42.0, 20.0, 170.0)                  # floodlight mast of the yard
    p.put(p.box(m0[0], m1[1], m0[0] + 1, m0[1]), 'I', 2.6)
    for k in range(int(m1[1]) + 2, int(m0[1]), 3):
        p.put(p.box(m0[0] - 1, k, m0[0] + 2, k + 1), 'I', 2.0)
    p.put(p.box(m0[0] - 3, m1[1] - 2, m0[0] + 4, m1[1] + 1), 'I', 3.0)
    p.put(p.box(m0[0] - 2, m1[1], m0[0] + 3, m1[1] + 1), 'L', 6.0, emis=True)
    LAYOUT['yard_mast'] = [int(m0[0]), int(m1[1])]
    # ---- the goods shed along the right of the yard: plank wall facing the tracks, loading doors with lamps over
    # them, the office window lit, snow along the eaves and on the long roof rising to its ridge; a loading ramp
    zs0, zs1, xs_ = 30.0, 128.0, 27.0
    roof = _q(p, [(xs_, 6.4, zs0), (33.0, 9.2, zs0), (33.0, 9.2, zs1), (xs_, 6.4, zs1)])
    zr_, xr_ = plane_y(yy, xx, 7.8)
    zrn = np.nan_to_num(zr_, nan=1e4, posinf=1e4, neginf=1e4)
    p.put(roof, 'W', 4.2 + np.clip((zrn - 30) / 100, 0, 1) * 0.8 + (pg.value_noise(VW, VH, 6, 734, 2) - 0.5) * 0.6)
    p.put(roof & ~C.shift(roof, 0, -1), 'W', 5.6)
    for vz in (48.0, 72.0, 96.0):                                              # roof vents with snow caps
        v0, v1 = proj(30.0, 7.8, vz), proj(30.6, 9.0, vz)
        p.put(p.box(v0[0], v1[1], v1[0] + 1, v0[1]), 'N', 2.0)
        p.put(p.box(v0[0], v1[1] - 1, v1[0] + 1, v1[1]), 'W', 6.2)
    zsh, ysh = plane_x(yy, xx, xs_)
    zshn = np.nan_to_num(zsh, nan=-1.0, posinf=-1.0, neginf=-1.0)
    yshn = np.nan_to_num(ysh, nan=-99.0, posinf=-99.0, neginf=-99.0)
    shed = (zshn > zs0) & (zshn < zs1) & (yshn > -1.0) & (yshn < 6.4)
    sfar = np.clip((zshn - 30) / 100, 0, 1)
    p.put(shed, 'N', 5.2 + sfar * 0.8)
    p.put(shed & (np.mod(zshn, 0.9) < 0.14), 'N', 4.0 + sfar * 0.6)               # the planks
    p.put(shed & (np.abs(yshn - 3.0) < 0.12), 'N', 4.2)                          # the rail of the sliding doors
    p.put(shed & (yshn > 6.0), 'W', 5.6 - sfar)                                  # snow along the eaves
    p.put(shed & (yshn < 0.25), 'N', 1.4)                                        # the ramp's shadow
    for k, dz in enumerate(np.arange(36.0, 122.0, 12.0)):
        door = shed & (zshn > dz) & (zshn < dz + 4.2) & (yshn > 0.2) & (yshn < 4.0)
        p.put(door, 'N', 3.0 + sfar * 0.6)
        p.put(door & ((np.abs(yshn - 1.0) < 0.1) | (np.abs(yshn - 2.6) < 0.1)), 'I', 3.0)    # iron straps
        p.put(door & (np.abs(zshn - (dz + 2.1)) < 0.08), 'N', 1.0)
        lq = proj(xs_ - 0.1, 4.5, dz + 2.1)
        lamp_on = k % 2 == 0
        p.put(p.box(lq[0] - 1, lq[1] - 1, lq[0] + 1, lq[1] + 1), 'L' if lamp_on else 'I', 5.6 if lamp_on else 2.4,
              emis=lamp_on)
        if lamp_on:                                                                # its light on the wall and the ramp
            pool = shed & (np.abs(zshn - (dz + 2.1)) < 2.6) & (yshn > 0.2) & (yshn < 4.4)
            p.put(pool & ~door, 'L', 1.2 + np.clip(1 - np.abs(zshn - (dz + 2.1)) / 2.6, 0, 1) * 0.8)
        if k == 2:
            win = shed & (zshn > dz + 5.0) & (zshn < dz + 9.0) & (yshn > 1.8) & (yshn < 3.2)
            p.put(win, 'L', 2.8, emis=True)
            p.put(win & (np.mod(zshn, 1.0) < 0.15), 'N', 1.6)
    ramp_ = _q(p, [(24.0, 0.2, zs0), (27.0, 0.2, zs0), (27.0, 0.2, zs1), (24.0, 0.2, zs1)])
    p.put(ramp_, 'W', 3.4)
    for (cz, cn) in ((40.0, 2), (63.0, 3), (88.0, 1)):
        for j in range(cn):
            c0, c1 = proj(25.0 + j * 0.7, 0.2, cz), proj(25.6 + j * 0.7, 0.9, cz)
            cr = p.box(c0[0], c1[1], c1[0] + 1, c0[1])
            p.put(cr, 'N', 2.6)
            p.put(cr & ~C.shift(cr, 0, -1), 'W', 6.0)
    # ---- a sleeping-car train standing on track 8 till morning: dark green sides, the blinds down, two lit
    # compartments, snow on the roofs, the gaps between the cars
    zt0, zt1, xt_ = 22.0, 190.0, 19.4
    ztr, ytr = plane_x(yy, xx, xt_)
    ztn = np.nan_to_num(ztr, nan=-1.0, posinf=-1.0, neginf=-1.0)
    ytn = np.nan_to_num(ytr, nan=-99.0, posinf=-99.0, neginf=-99.0)
    coach = (ztn > zt0) & (ztn < zt1) & (ytn > -0.6) & (ytn < 3.4)
    cfar = np.clip((ztn - 22) / 120, 0, 1)
    p.put(coach, 'G', 1.6 + cfar * 1.0)
    p.put(coach & (np.abs(ytn - 0.9) < 0.07), 'W', 3.6)                            # the cream waist line
    p.put(coach & (ytn > 3.1), 'W', 4.6 - cfar)
    p.put(coach & (ytn < 0.2), 'N', 1.0)
    gaps = coach & (np.mod(ztn - zt0, 24.8) > 24.0)
    p.put(gaps, 'N', 0.6)
    cyc = np.mod(ztn - zt0, 24.8)
    winz = coach & (ytn > 1.25) & (ytn < 2.15) & (cyc > 1.6) & (cyc < 23.0) & (np.mod(cyc - 1.6, 2.3) < 1.3)
    p.put(winz, 'N', 1.2 + cfar * 0.8)
    p.put(winz & (ytn > 2.0), 'G', 3.0)                                           # the blind's top catches light
    for (lz0, lz1) in ((28.5, 29.8), (56.1, 57.4)):
        p.put(winz & (ztn > lz0) & (ztn < lz1), 'L', 3.2, emis=True)
    rf_ = _q(p, [(xt_, 3.4, zt0), (xt_ + 2.9, 3.7, zt0), (xt_ + 2.9, 3.7, zt1), (xt_, 3.4, zt1)])
    p.put(rf_, 'W', 4.0)
    end = _q(p, [(xt_, -0.6, zt0), (xt_, 3.4, zt0), (xt_ + 2.9, 3.7, zt0), (xt_ + 2.9, -0.6, zt0)])
    p.put(end, 'G', 1.2)
    p.put(end & ~C.shift(end, 0, -1), 'W', 5.0)
    gw0, gw1 = proj(xt_ + 1.0, 0.2, zt0), proj(xt_ + 1.9, 2.6, zt0)
    p.put(p.box(gw0[0], gw1[1], gw1[0] + 1, gw0[1]), 'N', 1.0)                     # the gangway door
    for bx_ in (xt_ + 0.5, xt_ + 2.4):
        q = proj(bx_, 0.1, zt0 - 0.1)
        p.put(p.ell(q[0], q[1], 1.6, 1.2), 'I', 3.0)
    tl = proj(xt_ + 0.4, 0.5, zt0 - 0.05)
    p.put(p.box(tl[0], tl[1], tl[0] + 2, tl[1] + 2), 'R', 2.4)                     # a tail lamp, dark
    # ---- a plank crossing for the porters' barrows over tracks 5 and 6 (snow trodden flat on it)
    xc0, xc1, zc0_, zc1_ = EDGE_X, PL6_X0, 10.6, 11.6
    zk, xk = plane_y(yy, xx, -0.84)
    zkn = np.nan_to_num(zk, nan=-1.0, posinf=-1.0, neginf=-1.0)
    xkn = np.nan_to_num(xk, nan=-99.0, posinf=-99.0, neginf=-99.0)
    cross = (yy > vpy) & (zkn > zc0_) & (zkn < zc1_) & (xkn > xc0) & (xkn < xc1)
    rails = np.zeros((VH, VW), bool)
    for rx in (2.18, 3.29, 3.62, 6.4, 7.9):
        rails |= np.abs(xkn - rx) < 0.06
    p.put(cross & ~rails, 'D', 1.5)
    p.put(cross & ~rails & (np.mod(zkn - zc0_, 0.25) < 0.05), 'D', 0.8)                # the gaps between planks
    trod = cross & (np.abs(zkn - (zc0_ + zc1_) / 2) < 0.22)
    snowk = cross & ~rails & ~trod
    p.put(snowk & (pg.value_noise(VW, VH, 4, 735, 1) > 0.35), 'W', 3.6)             # snow lying on the planks
    p.put(snowk & ~C.shift(cross, 0, -1), 'W', 4.8)
    # sleepers of track 6 in front of the goods train
    sl6 = ground & (xgn > 5.9) & (xgn < 8.4) & (np.mod(np.clip(zgn, 0, 1e4), 0.65) < 0.22) & (zgn < 17.0) & ~cross
    p.put(sl6, 'N', 2.4)
    # ---- the signal gantry over tracks 6-8 (a lattice beam on two legs, three signal heads)
    zgy = 64.0
    for lx_ in (5.0, 23.4):
        a_, b_ = proj(lx_, -1.0, zgy), proj(lx_, 7.4, zgy)
        p.put(p.box(a_[0], b_[1], a_[0] + 2, a_[1]), 'I', 2.2)
    bm0, bm1 = proj(5.0, 7.6, zgy), proj(23.4, 7.0, zgy)
    beam = p.box(bm0[0], bm0[1], bm1[0] + 2, bm1[1] + 1)
    p.put(beam, 'I', 2.0)
    p.put(beam & (((xx.astype(int) + yy.astype(int)) % 3) == 0), 'N', 0.8)
    p.put(p.box(bm0[0], bm0[1] - 1, bm1[0] + 2, bm0[1]), 'W', 5.0)
    for (sx_, col) in ((7.15, 'R'), (16.35, 'R'), (20.55, 'G')):
        h0, h1 = proj(sx_ - 0.35, 7.0, zgy), proj(sx_ + 0.35, 5.6, zgy)
        p.put(p.box(h0[0], h0[1], h1[0] + 1, h1[1]), 'I', 1.2)
        lq = proj(sx_, 6.0, zgy)
        p.px(lq[0], lq[1], col, 3.0)
    # ---- the water crane at the end of platform 6, its fire pot glowing (they keep it from freezing)
    zw, xw = 82.0, 14.9
    c0, c1 = proj(xw, -1.0, zw), proj(xw, 3.0, zw)
    p.put(p.box(c0[0], c1[1], c0[0] + 2, c0[1]), 'I', 2.4)
    arm = p.line([proj(xw, 3.0, zw), proj(xw - 2.4, 3.0, zw - 0.4)], 0.6)
    p.put(arm, 'I', 2.6)
    p.put(p.line([proj(xw - 2.4, 3.0, zw - 0.4), proj(xw - 2.4, 1.6, zw - 0.4)], 0.4), 'N', 1.4)
    p.px(c1[0], c1[1] - 1, 'W', 6.0)
    fq = proj(xw + 0.7, -0.7, zw)
    p.put(p.box(fq[0], fq[1] - 1, fq[0] + 2, fq[1] + 1), 'L', 5.0, emis=True)
    p.put(p.box(fq[0], fq[1] + 1, fq[0] + 2, fq[1] + 2), 'R', 2.0)
    LAYOUT['firepot'] = [int(fq[0]), int(fq[1]) - 1]
    # ---- platform 6: the face of its wall toward track 6, the white edge, the trodden snow, lamp pools
    face = _q(p, [(PL6_X0, -1.0, 4.0), (PL6_X0, 0.0, 4.0), (PL6_X0, 0.0, PL6_END), (PL6_X0, -1.0, PL6_END)])
    p.put(face, 'N', 1.4)
    p.put(face & ((yy.astype(int) % 3) == 0), 'N', 2.0)
    zp6, xp6 = plane_y(yy, xx, 0.0)
    zp6n = np.nan_to_num(zp6, nan=1e4, posinf=1e4, neginf=1e4)
    xp6n = np.nan_to_num(xp6, nan=-99.0, posinf=-99.0, neginf=-99.0)
    pl6 = (yy > vpy + 0.5) & (xp6n >= PL6_X0) & (xp6n < PL6_X1) & (zp6n > 4.0) & (zp6n < PL6_END)
    pool6 = np.zeros((VH, VW), np.float32)
    for lz in PL6_LIT:
        d = np.hypot(zp6n - lz, (xp6n - PL6_LAMP_X) * 1.3)
        pool6 = np.maximum(pool6, np.clip(1 - d / 3.4, 0, 1) ** 1.5)
    p.put(pl6, 'W', 2.6 + pool6 * 2.0 - np.clip((zp6n - 6) / 80, 0, 1) * 0.9
          + (pg.value_noise(VW, VH, 8, 732, 2) - 0.5) * 0.6)
    p.put(pl6 & (np.mod(zp6n, 2.0) < 0.07), 'W', 2.0)                              # paving joints under the snow
    p.put(pl6 & (xp6n < PL6_X0 + 0.3), 'W', 6.0 + pool6 * 1.4)                      # the white edge
    trod = pl6 & (np.abs(xp6n - (11.6 + 0.4 * np.sin(zp6n * 0.7))) < 0.35) & (np.mod(zp6n, 0.9) < 0.45)
    p.put(trod, 'W', 2.0 + pool6)
    rampf = _q(p, [(PL6_X0, 0.0, PL6_END), (PL6_X1, 0.0, PL6_END), (PL6_X1, -1.0, PL6_END + 5.0),
                   (PL6_X0, -1.0, PL6_END + 5.0)])
    p.put(rampf, 'W', 2.4)
    # the bench and the mail barrow on platform 6
    b0 = _q(p, [(13.4, 0.46, 20.0), (13.9, 0.46, 20.0), (13.9, 0.46, 22.0), (13.4, 0.46, 22.0)])
    p.put(b0, 'N', 2.4)
    p.put(b0 & ~C.shift(b0, 0, -1), 'W', 5.4)
    bk = _q(p, [(13.95, 0.5, 20.0), (13.95, 0.95, 20.0), (13.95, 0.95, 22.0), (13.95, 0.5, 22.0)])
    p.put(bk, 'N', 1.8)
    for bz in (20.2, 21.8):
        p.put(p.line([proj(13.5, 0.0, bz), proj(13.5, 0.46, bz)], 0.4), 'I', 1.4)
    mb = _q(p, [(11.6, 0.0, 33.0), (11.6, 0.9, 33.0), (12.6, 0.9, 33.0), (12.6, 0.0, 33.0)])
    p.put(mb, 'N', 2.0)
    for j in range(3):
        sq = proj(11.75 + j * 0.3, 1.05, 33.2)
        p.put(p.ell(sq[0], sq[1], 2.0, 1.6), 'W', 4.6)
        p.px(sq[0], sq[1] - 1, 'W', 6.2)
    # cast-iron columns of the canopy, lit on the side of the lamps
    for cz in (6.0, 16.0, 26.0, 36.0, 46.0, 56.0, 66.0, 76.0):
        x0_, y0_ = proj(12.5, 4.2, cz)
        x1_, y1_ = proj(12.75, 0.0, cz)
        col = p.box(x0_, y0_, x1_ + 1, y1_)
        lit_ = min(abs(cz - lz) for lz in PL6_LIT) < 6.0
        p.put(col, 'I', 1.4 + (1.6 if lit_ else 0.4))
        p.put(col & (xx <= x0_), 'I', 2.6 + (1.8 if lit_ else 0.0))
        cw_ = max(1.0, (x1_ - x0_) * 0.5)
        p.put(p.box(x0_ - cw_, y0_, x1_ + cw_ + 1, y0_ + max(1.0, 12.0 / cz)), 'I', 2.4)
    # ---- the canopy of platform 6: boarded underside with purlins catching the lamps, the fascia with snow
    zc6, xc6 = plane_y(yy, xx, 4.2)
    zc6n = np.nan_to_num(zc6, nan=1e4, posinf=1e4, neginf=1e4)
    xc6n = np.nan_to_num(xc6, nan=-99.0, posinf=-99.0, neginf=-99.0)
    can6 = (yy < vpy - 0.5) & (xc6n > 8.8) & (xc6n < PL6_X1 + 0.4) & (zc6n > 3.0) & (zc6n < 84.0)
    cl6 = np.zeros((VH, VW), np.float32)
    for lz in PL6_LIT:
        d = np.hypot(zc6n - lz, (xc6n - PL6_LAMP_X) * 1.3)
        cl6 = np.maximum(cl6, np.clip(1 - d / 3.0, 0, 1) ** 1.5)
    p.put(can6, 'N', 1.4 + cl6 * 2.2 + np.clip(1 - zc6n / 30, 0, 1) * 0.5)
    p.add(can6 & (np.mod(zc6n, 3.0) < 0.22), 1.2)
    p.add(can6 & (np.mod(xc6n + 20.0, 0.5) < 0.06), -0.4)
    fas6 = _q(p, [(8.8, 4.2, 3.0), (8.8, 4.2, 84.0), (8.8, 3.75, 84.0), (8.8, 3.75, 3.0)])
    p.put(fas6, 'I', 1.6)
    p.put(fas6 & ~C.shift(fas6, 0, 1), 'W', 3.4)
    outer = _q(p, [(PL6_X1 + 0.4, 4.2, 3.0), (PL6_X1 + 0.4, 4.2, 84.0), (PL6_X1 + 0.4, 3.75, 84.0),
                   (PL6_X1 + 0.4, 3.75, 3.0)])
    p.put(outer, 'I', 1.2)
    rfsnow = _q(p, [(PL6_X1 + 0.4, 4.2, 3.0), (PL6_X1 + 0.4, 4.55, 3.0), (PL6_X1 + 0.4, 4.55, 84.0),
                    (PL6_X1 + 0.4, 4.2, 84.0)])
    p.put(rfsnow, 'W', 4.6)
    # the hanging lamps (shade + bulb; the dark ones too) and the sign "6"
    for lz in PL6_LAMPS_Z:
        top = proj(PL6_LAMP_X, 4.2, lz)
        bot = proj(PL6_LAMP_X, 3.95, lz)
        p.put(p.box(top[0], top[1], top[0] + 1, bot[1] + 1), 'I', 2.2)
        sw = max(1.5, 220.0 / lz / 2)
        sh = max(1.0, 90.0 / lz)
        shade = p.poly([(bot[0] - sw * 0.4, bot[1]), (bot[0] + sw * 0.4, bot[1]), (bot[0] + sw, bot[1] + sh),
                        (bot[0] - sw, bot[1] + sh)])
        p.put(shade, 'I', 2.8)
        p.put(shade & ~C.shift(shade, 0, -1), 'W', 4.6)
        on = lz in PL6_LIT
        p.put(p.ell(bot[0], bot[1] + sh + max(0.7, 30.0 / lz), max(1.0, sw * 0.45), max(0.7, 30.0 / lz)),
              'L' if on else 'N', 6.0 if on else 2.4, emis=on)
    sz6 = 12.5
    s0, s1 = proj(9.4, 3.95, sz6), proj(10.4, 3.3, sz6)
    sign6 = p.box(s0[0], s0[1], s1[0], s1[1])
    p.put(sign6, 'N', 5.4)
    p.put(sign6 & ~C.kit.erode(sign6, 1), 'W', 6.4)
    p.put(K.text_at('6', VW, VH, int((s0[0] + s1[0]) / 2), int(s0[1] + 3), font='l', center=True) & sign6, 'W', 8.0)
    for hx_ in (s0[0] + 3, s1[0] - 4):
        p.put(p.box(hx_, proj(9.9, 4.2, sz6)[1], hx_ + 1, s0[1]), 'I', 2.4)
    LAYOUT['pl6_lamps'] = [[round(v, 1) for v in proj(PL6_LAMP_X, 3.75, lz)] + [lz] for lz in PL6_LIT]


def _barrow(p):
    """AD round 2: the luggage barrow on platform 5, seen from its near end: an oak bed on iron-shod wheels, the
    drawbar with its T-grip leaning toward us, a load of canvas mail sacks tied at the neck (one lying across the top),
    a parcel in string and a wicker hamper behind; snow dusted on top, the warm rim of the lamp at z 16."""
    yy, xx = p.yy, p.xx
    tz, tx0, tx1 = 12.5, -1.4, -0.5
    # shadow on the platform
    sh = p.poly([proj(tx0 - 0.1, 0.0, tz - 0.1), proj(tx1 + 0.2, 0.0, tz - 0.1), proj(tx1 + 0.2, 0.0, tz + 2.3),
                 proj(tx0 - 0.1, 0.0, tz + 2.3)])
    p.add(sh, -0.9)
    # wheels (edge-on from here): iron rims under the bed, the axle between them
    for wx in (tx0 + 0.08, tx1 - 0.08):
        for wz in (tz + 0.35, tz + 1.85):
            a_, b_ = proj(wx, 0.0, wz), proj(wx, 0.5, wz)
            w_ = max(2.0, 0.08 * 420 / wz)
            p.put(p.box(a_[0] - w_ / 2, b_[1], a_[0] + w_ / 2 + 0.5, a_[1]), 'I', 1.6)
            p.put(p.box(a_[0] - w_ / 2, b_[1], a_[0] - w_ / 2 + 1, a_[1]), 'I', 3.0)
    ax_ = p.line([proj(tx0, 0.25, tz + 0.35), proj(tx1, 0.25, tz + 0.35)], 0.5)
    p.put(ax_, 'I', 1.2)
    # the bed: top (oak planks running away from us) and the near end board with its iron corner plates
    top = p.poly([proj(tx0, 0.55, tz), proj(tx1, 0.55, tz), proj(tx1, 0.55, tz + 2.2), proj(tx0, 0.55, tz + 2.2)])
    p.put(top, 'D', 2.4)
    endb = p.poly([proj(tx0, 0.38, tz), proj(tx0, 0.58, tz), proj(tx1, 0.58, tz), proj(tx1, 0.38, tz)])
    p.put(endb, 'D', 1.8)
    p.put(endb & ((yy.astype(int) % 3) == 0), 'D', 1.2)
    p.put(endb & ~C.shift(endb, 0, -1), 'D', 3.2)
    for cx_ in (tx0, tx1 - 0.08):
        cp = p.poly([proj(cx_, 0.38, tz - 0.01), proj(cx_, 0.58, tz - 0.01), proj(cx_ + 0.08, 0.58, tz - 0.01),
                     proj(cx_ + 0.08, 0.38, tz - 0.01)])
        p.put(cp, 'I', 2.8)
    # the load: a parcel in string and a wicker hamper at the back, three mail sacks, one lying across the top
    pq0, pq1 = proj(tx1 - 0.36, 0.55, tz + 1.6), proj(tx1 - 0.04, 0.95, tz + 1.6)
    parcel = p.box(pq0[0], pq1[1], pq1[0] + 1, pq0[1])
    p.put(parcel, 'D', 3.4)
    pmx, pmy = (pq0[0] + pq1[0]) / 2, (pq0[1] + pq1[1]) / 2
    p.put(parcel & ((np.abs(xx - pmx) < 0.6) | (np.abs(yy - pmy) < 0.6)), 'W', 5.2)
    p.put(parcel & ~C.shift(parcel, 0, -1), 'W', 6.0)
    hq0, hq1 = proj(tx0 + 0.04, 0.55, tz + 1.5), proj(tx0 + 0.42, 0.98, tz + 1.5)
    hamper = p.box(hq0[0], hq1[1], hq1[0] + 1, hq0[1])
    p.put(hamper, 'D', 2.6)
    p.put(hamper & (((xx.astype(int) + yy.astype(int)) % 2) == 0), 'D', 3.6)       # the weave
    p.put(hamper & ~C.shift(hamper, 0, -1), 'W', 5.6)
    sacks = [((tx0 + 0.24, tz + 0.5), 0.26, 0.36), ((tx1 - 0.24, tz + 0.55), 0.25, 0.34),
             ((tx0 + 0.45, tz + 0.9), 0.36, 0.2)]
    for i, ((sxw, szw), rw, rh) in enumerate(sacks):
        base_y = 0.55 if i < 2 else 0.86
        cxs, cys = proj(sxw, base_y + rh, szw)
        rx = rw * 420 / szw
        ry = rh * 420 / szw
        m = p.ell(cxs, cys, rx, ry) & (yy < proj(sxw, base_y, szw)[1] + 1)
        dxn = (xx - cxs) / max(rx, 1)
        dyn = (yy - cys) / max(ry, 1)
        p.put(m, 'S', 2.5 + dxn * 0.8 - dyn * 0.9)
        fold = m & (np.abs(dxn * 0.8 + np.sin(dyn * 3.0 + i) * 0.25) < 0.08)
        p.put(fold, 'S', 1.3)
        band = m & (np.abs(dyn - 0.15) < 0.12)
        p.put(band, 'S', 1.0)                                                     # the stencilled band
        p.put(m & ~C.kit.erode(m, 1) & (dyn > -0.2), 'S', 0.6)                     # the outline in shadow
        p.put(m & ~C.shift(m, 0, -1), 'W', 6.2)                                   # snow dust on top
        p.put(m & ~C.shift(m, 1, 0) & (dyn < 0.3), 'L', 1.4)                      # the lamp's warm rim
        if i < 2:                                                                 # the tied neck
            nq = (cxs + rx * 0.1, cys - ry - 1)
            p.put(p.box(nq[0] - 1, nq[1] - 1, nq[0] + 2, nq[1] + 1), 'S', 2.4)
            p.put(p.box(nq[0] - 1, nq[1] + 1, nq[0] + 2, nq[1] + 2), 'I', 1.2)
        p.px(cxs + rx * 0.4, cys + ry * 0.15, 'L', 2.6)                           # the brass label
    # the drawbar lowered to the platform in front of it, the T-grip lying in the snow
    a_ = proj((tx0 + tx1) / 2, 0.42, tz)
    b_ = proj((tx0 + tx1) / 2 + 0.1, 0.04, tz - 1.0)
    p.put(p.line([a_, b_], 0.6), 'I', 1.8)
    p.put(p.line([(b_[0] - 3, b_[1]), (b_[0] + 3, b_[1])], 0.5), 'I', 2.6)
    p.put(p.line([(b_[0] - 3, b_[1] + 1), (b_[0] + 3, b_[1] + 1)], 0.5), 'N', 1.2)


def n1_bg():
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, R=V['red'], G=['#0C111C', '#1E302E', '#3D5E57', '#739585'],
                D=['#22150F', '#331F16', '#4A2D1F', '#63402C', '#7E553B'],
                S=['#2A2A2E', '#4A4A4E', '#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA'])
    p = C.Paint(VW, VH, R, 'n1_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    vpx, vpy = PROJ['vpx'], PROJ['vpy']
    # ---- the night beyond: low cloud lit faintly by the city (warm-grey near the horizon), the yard dark
    sky_t = 1.6 + np.clip(1 - np.abs(yy - vpy + 10) / 90, 0, 1) * 1.6 + (pg.value_noise(VW, VH, 50, 701, 3) - 0.5) * 0.6
    p.put(allm, 'N', sky_t)
    # distant city glow on the cloud base behind the VP
    glow = np.clip(1 - np.hypot((xx - 300) / 260, (yy - 150) / 40), 0, 1) ** 1.5
    p.add(allm, glow * 1.4)
    # far skyline (domes, a spire, the palais dome with a red aircraft light)
    sk = np.zeros((VH, VW), bool)
    rng = np.random.default_rng(702)
    x = 240.0
    while x < VW:
        w_ = rng.uniform(10, 26)
        sk |= p.box(x, vpy - rng.uniform(3, 10), x + w_, vpy + 2)
        x += w_
    sk |= p.ell(402, vpy - 10, 9, 8) & (yy < vpy - 8) | p.box(394, vpy - 10, 411, vpy)
    sk |= p.box(401, vpy - 26, 403, vpy - 17)
    sk |= p.poly([(470, vpy), (474, vpy - 30), (478, vpy)])
    p.put(sk, 'N', 2.0)
    for _ in range(26):
        wx, wy = rng.uniform(250, 636), rng.uniform(vpy - 8, vpy)
        if sk[int(wy), int(wx)]:
            p.px(wx, wy, 'L', float(rng.choice([1.6, 2.4, 3.0])))
    p.px(402, vpy - 27, 'R', 3.0)
    # ---- ground plane (rail level, y = -1): track bed beyond the platform, snow, sleepers, rails
    zg, xg = plane_y(yy, xx, -1.0)
    ground = (yy > vpy + 0.5) & np.isfinite(zg)
    gtone = 2.6 - np.clip((np.nan_to_num(zg) - 8) / 60, 0, 1) * 1.2 + (pg.value_noise(VW, VH, 14, 703, 2) - 0.5) * 0.8
    p.put(ground, 'W', gtone)
    # lamp light spilled onto the track bed (near the platform)
    pool_g = lamp_pool(zg, xg, 1.0) * ground
    # sleepers every 0.65 m between the outer rails
    zi = np.clip(np.nan_to_num(zg, nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1e4)
    sl = ground & (np.nan_to_num(xg) > 1.8) & (np.nan_to_num(xg) < 4.0) & (np.mod(zi, 0.65) < 0.22) & (zi < 70)
    p.put(sl, 'N', 2.6 + pool_g * 3.0)
    ballast = ground & (np.nan_to_num(xg) > 1.7) & (np.nan_to_num(xg) < 4.1)
    p.add(ballast & ~sl, -0.6)
    # the rails: four-rail dual gauge, the inner rail of the standard gauge
    for rx in (2.18, 3.29, 3.62):
        a_ = proj(rx, -1.0, 2.5)
        b_ = proj(rx, -1.0, 400.0)
        rm = p.line([a_, b_], 0.55) & ground
        p.put(rm, 'I', 3.4)
        p.put(rm & ~C.shift(rm, 0, -1), 'W', 5.6)
    # platform 6, the yard and its buildings to the right (AD round 2)
    _n1_right(p, ground, zg, xg)
    # ---- platform 5 (left): surface y = 0, the white edge, lamp pools, snow trodden into slush
    zp, xp = plane_y(yy, xx, 0.0)
    plat = (yy > vpy + 0.5) & np.isfinite(zp) & (np.nan_to_num(xp, nan=99) < EDGE_X)
    pool = lamp_pool(zp, xp, 1.0)
    pt = 2.0 + pool * 2.2 - np.clip((np.nan_to_num(zp) - 6) / 70, 0, 1) * 1.0
    pt += (pg.value_noise(VW, VH, 8, 704, 2) - 0.5) * 0.7
    p.put(plat, 'W', pt)
    # the lamps mirrored in the wet, trodden snow: short warm streaks running toward the camera
    for lz in LAMPS_Z:
        qx, qy = proj(LAMP_X - 0.15, 0.0, lz)
        ln = max(2.0, 90.0 / lz)
        streak = plat & (np.abs(xx - qx) < max(0.6, 6.0 / lz)) & (yy > qy - 1) & (yy < qy + ln) &             (((yy.astype(int) + int(lz)) % 3) != 0)
        p.put(streak, 'L', 2.6)
    slabs = plat & (np.mod(np.nan_to_num(zp), 2.0) < 0.07)
    p.add(slabs, -0.8)
    edge = plat & (np.nan_to_num(xp) > EDGE_X - 0.28)
    p.put(edge, 'W', 6.2 + pool * 1.6)
    p.put(plat & (np.nan_to_num(xp) > EDGE_X - 0.34) & (np.nan_to_num(xp) <= EDGE_X - 0.28), 'N', 3.0)
    # ---- canopy over platform 5: underside boards, purlins, the fascia over the track edge
    zc, xc = plane_y(yy, xx, CANOPY_Y)
    can = (yy < vpy - 0.5) & np.isfinite(zc) & (np.nan_to_num(xc, nan=99) < 1.8)
    ct = 1.4 + lamp_pool(zc, xc, 1.0) * 2.4 + np.clip(1 - np.nan_to_num(zc) / 30, 0, 1) * 0.6
    p.put(can, 'N', ct)
    purl = can & (np.mod(np.nan_to_num(zc), 3.0) < 0.22)
    p.add(purl, 1.4)
    boards = can & (np.mod(np.nan_to_num(xc) + 20.0, 0.5) < 0.06)
    p.add(boards, -0.5)
    # fascia board at x = 1.8 hanging 0.45 m below the roof edge (vertical strip in perspective)
    f_top = proj(1.8, CANOPY_Y, 3.0)
    f_bot_near = proj(1.8, CANOPY_Y - 0.45, 3.0)
    fas = p.poly([f_top, proj(1.8, CANOPY_Y, 300.0), proj(1.8, CANOPY_Y - 0.45, 300.0), f_bot_near])
    p.put(fas, 'I', 1.6)
    p.put(fas & ~C.shift(fas, 0, 1), 'W', 3.0)                                 # snow on top of the fascia
    # ---- columns down the middle of the platform (cast iron, fluted, lit from the lamps)
    for cz in (3.6, 10.6, 17.6, 24.6, 31.6, 38.6, 45.6):
        x0_, y0_ = proj(-2.4, CANOPY_Y, cz)
        x1_, y1_ = proj(-2.1, 0.0, cz)
        if x1_ < 0:
            continue
        col = p.box(x0_, y0_, x1_ + 1, y1_)
        li = lamp_pool(np.array(cz), np.array(-0.9), 1.0)
        p.put(col, 'I', 1.2 + float(li) * 3.0 + np.clip((xx - x0_) / max(1.0, x1_ - x0_), 0, 1) * 1.4)
        cap_w = max(1.0, (x1_ - x0_) * 0.4)
        p.put(p.box(x0_ - cap_w, y0_, x1_ + cap_w + 1, y0_ + max(1.0, 12.0 / cz)), 'I', 2.6)
    # ---- a goods train standing on the next track: box cars, a tank wagon and a flat car with a tarpaulin,
    # plank sides with their iron straps catching the canopy lamps, sliding doors, snow on every roof
    kinds = ['box', 'box', 'tank', 'box', 'flat', 'box', 'box', 'tank']
    for c in range(8):
        z0 = 17.0 + c * 13.6
        z1 = z0 + 12.8
        xl, xr = 5.7, 8.6
        kind = kinds[c]
        li = float(np.clip(1 - abs(z0 + 6 - 16.0) / 26.0, 0, 1))          # how much canopy light reaches it
        if kind == 'tank':
            barrel = p.poly([proj(xl + 0.2, 0.4, z0 + 0.6), proj(xl + 0.2, 2.7, z0 + 0.6), proj(xl + 0.2, 2.7, z1 - 0.6),
                             proj(xl + 0.2, 0.4, z1 - 0.6)])
            p.put(barrel, 'N', 2.0 + li * 1.4)
            p.put(p.line([proj(xl + 0.2, 2.3, z0 + 0.6), proj(xl + 0.2, 2.3, z1 - 0.6)], 0.5), 'N', 3.2 + li * 1.6)
            p.put(p.line([proj(xl + 0.2, 2.7, z0 + 0.6), proj(xl + 0.2, 2.7, z1 - 0.6)], 0.5), 'W', 4.4)
            for bz in (z0 + 3.0, z1 - 3.0):                                  # the straps of the tank
                p.put(p.line([proj(xl + 0.2, 0.4, bz), proj(xl + 0.2, 2.7, bz)], 0.4), 'I', 2.6)
            dq = proj(xl + 0.6, 3.0, z0 + 6.4)
            dw = max(1.0, 420.0 * 0.6 / (z0 + 6.4))
            p.put(p.box(dq[0] - dw, dq[1] - dw, dq[0] + dw + 1, dq[1] + 1), 'N', 2.4)
            frame_ = p.poly([proj(xl, -0.6, z0), proj(xl, 0.4, z0), proj(xl, 0.4, z1), proj(xl, -0.6, z1)])
            p.put(frame_, 'N', 1.2)
            continue
        if kind == 'flat':
            load = p.poly([proj(xl, 0.4, z0 + 0.4), proj(xl, 2.2, z0 + 1.2), proj(xl, 2.2, z1 - 1.2), proj(xl, 0.4, z1 - 0.4)])
            p.put(load, 'N', 2.6 + li * 1.2)
            folds = load & (np.mod(p.xx + p.yy * 0.5, 7.0) < 1.0)
            p.add(folds, -0.8)
            p.put(p.line([proj(xl, 2.2, z0 + 1.2), proj(xl, 2.2, z1 - 1.2)], 0.6), 'W', 5.4)
            for rz in (z0 + 3.0, z0 + 6.4, z1 - 3.0):                         # ropes over the tarpaulin
                p.put(p.line([proj(xl, 0.4, rz), proj(xl, 2.2, rz)], 0.4), 'I', 1.6)
            frame_ = p.poly([proj(xl, -0.6, z0), proj(xl, 0.4, z0), proj(xl, 0.4, z1), proj(xl, -0.6, z1)])
            p.put(frame_, 'N', 1.2)
            continue
        side = p.poly([proj(xl, -0.6, z0), proj(xl, 3.0, z0), proj(xl, 3.0, z1), proj(xl, -0.6, z1)])
        p.put(side, 'N', 1.8 + (c % 2) * 0.3 + li * 1.2)
        for k in range(1, 12):                                                 # the planks
            zr = z0 + k * (z1 - z0) / 12
            p.put(p.line([proj(xl, -0.4, zr), proj(xl, 2.8, zr)], 0.35) & side, 'N', 1.4 + li * 0.6)
        for yb in (0.3, 1.2, 2.2):                                             # iron straps catching the light
            p.put(p.line([proj(xl, yb, z0), proj(xl, yb, z1)], 0.4) & side, 'I', 3.0 + li * 2.2)
        dz0, dz1 = z0 + 4.6, z0 + 8.2                                          # the sliding door and its rail
        door = p.poly([proj(xl, -0.3, dz0), proj(xl, 2.7, dz0), proj(xl, 2.7, dz1), proj(xl, -0.3, dz1)])
        p.put(door, 'N', 2.2 + li * 1.0)
        p.put(p.line([proj(xl, 2.75, dz0 - 1.0), proj(xl, 2.75, dz1 + 1.0)], 0.4), 'I', 3.4 + li * 1.6)
        p.put(p.line([proj(xl, -0.3, (dz0 + dz1) / 2), proj(xl, 2.7, (dz0 + dz1) / 2)], 0.4), 'I', 2.6)
        if c == 1:                                                             # a chalked number on a door
            p.put(p.line([proj(xl, 1.5, dz0 + 0.7), proj(xl, 1.5, dz0 + 2.0)], 0.4), 'W', 4.4)
            p.put(p.line([proj(xl, 1.1, dz0 + 0.9), proj(xl, 1.9, dz0 + 1.6)], 0.4), 'W', 4.0)
        p.put(p.line([proj(xl, 3.0, z0), proj(xl, 3.0, z1)], 0.6), 'W', 5.0)    # snow on the roof edge
        roof = p.poly([proj(xl, 3.0, z0), proj(xr, 3.1, z0), proj(xr, 3.1, z1), proj(xl, 3.0, z1)])
        p.put(roof, 'W', 3.4 + li * 1.0)
        if c == 0:
            # the end of the first wagon faces us: planks, corner posts, the brake wheel on its platform,
            # buffers and the coupling, snow along the roof, the canopy lamps catching the left post
            face = p.poly([proj(xl, -0.6, z0), proj(xl, 3.0, z0), proj(xr, 3.1, z0), proj(xr, -0.6, z0)])
            p.put(face, 'N', 1.6)
            for k in range(1, 10):
                yb = -0.6 + k * 0.38
                p.put(p.line([proj(xl, yb, z0), proj(xr, yb, z0)], 0.4) & face, 'N', 1.0)
            for px_ in (xl + 0.08, xr - 0.08):
                p.put(p.line([proj(px_, -0.6, z0), proj(px_, 3.0, z0)], 0.8) & face, 'I', 2.2 if px_ < 7 else 1.6)
            p.put(p.line([proj(xl + 0.08, -0.6, z0), proj(xl + 0.08, 3.0, z0)], 0.5) & face, 'I', 4.2)
            p.put(p.line([proj(xl, 1.2, z0), proj(xr, 1.2, z0)], 0.5) & face, 'I', 2.6)
            p.put(face & ~C.shift(face, 0, -1), 'W', 5.4)
            p.put(face & ~C.shift(face, 0, -2) & C.shift(face, 0, -1), 'W', 4.0)
            wc = proj(xr - 0.7, 1.9, z0 - 0.1)
            p.put(p.ell(wc[0], wc[1], 4.5, 4.5) & ~p.ell(wc[0], wc[1], 3.2, 3.2), 'I', 3.2)   # the brake wheel
            p.put(p.line([(wc[0] - 4, wc[1]), (wc[0] + 4, wc[1])], 0.4) | p.line([(wc[0], wc[1] - 4), (wc[0], wc[1] + 4)], 0.4),
                  'I', 3.0)
            for bx in (xl + 0.5, xr - 0.5):                                     # buffers
                q = proj(bx, 0.2, z0 - 0.2)
                p.put(p.ell(q[0], q[1], 3, 2.5), 'I', 3.4)
                p.put(p.ell(q[0] - 0.5, q[1] - 0.5, 1.4, 1.0), 'I', 5.0)
            hk = proj((xl + xr) / 2, 0.2, z0 - 0.3)
            p.put(p.box(hk[0] - 1, hk[1] - 1, hk[0] + 2, hk[1] + 4), 'I', 2.8)
            tb = proj(xl + 0.4, 2.6, z0 - 0.05)
            p.put(p.box(tb[0], tb[1], tb[0] + 6, tb[1] + 4), 'R', 2.4)               # the tail board
            p.put(p.box(tb[0] + 2, tb[1], tb[0] + 4, tb[1] + 4), 'W', 6.0)
    for c in range(8):                                                         # the dark gaps and couplings
        zg = 17.0 + c * 13.6 + 12.8
        p.put(p.line([proj(5.7, -0.2, zg + 0.4), proj(5.7, 2.6, zg + 0.4)], 0.5), 'N', 0.6)
    # ---- on platform 5: the luggage barrow with mail sacks, a stack of crates, footprints in the slush
    _barrow(p)
    for (cz, cx, ch) in ((24.6, -1.6, 0.5), (24.0, -1.6, 0.9), (24.0, -1.0, 0.5)):
        # wooden crates (AD round 2: planks, corner battens, a stencil, snow on top -- not dark boxes)
        a_ = proj(cx, 0.0, cz)
        b_ = proj(cx + 0.5, ch, cz)
        cr = p.box(a_[0], b_[1], b_[0] + 1, a_[1])
        p.put(cr, 'D', 2.4)
        p.put(cr & ((p.yy.astype(int) - int(b_[1])) % 3 == 2), 'D', 1.4)
        p.put(cr & ((p.xx <= a_[0]) | (p.xx >= b_[0])), 'D', 3.4)
        p.put(cr & ~C.shift(cr, 1, 0), 'D', 1.0)
        p.put(p.box((a_[0] + b_[0]) / 2 - 1, (a_[1] + b_[1]) / 2, (a_[0] + b_[0]) / 2 + 1, (a_[1] + b_[1]) / 2 + 1)
              & cr, 'N', 1.4)
        p.put(cr & ~C.shift(cr, 0, -1), 'W', 6.0)
    for k in range(18):                                                        # footprints toward the edge
        fz = 5.0 + k * 1.1
        fx = -0.5 + 0.15 * ((k % 2) * 2 - 1) + k * 0.02
        q = proj(fx, 0.0, fz)
        p.put(p.box(q[0], q[1], q[0] + max(1.0, 8.0 / fz), q[1] + 1), 'W', 1.6)
    # ---- the far end: a signal at red where the track vanishes, tiny yard lamps
    sx, sy = proj(2.6, 3.2, 160.0)
    p.put(p.box(sx, sy, sx + 1, proj(2.6, -1.0, 160.0)[1]), 'I', 2.0)
    p.px(sx, sy, 'G', 3.0)
    LAYOUT['signal'] = [int(sx), int(sy)]
    for (lx, ly_, lz) in ((-4.0, 5.0, 120.0), (6.0, 6.0, 140.0), (12.0, 7.0, 90.0), (16.0, 6.0, 70.0)):
        qx, qy = proj(lx, ly_, lz)
        p.px(qx, qy, 'L', 3.4)
    p.resolve(band=2.6)
    LAYOUT['edge_x'] = EDGE_X
    return p.L


def n1_mid():
    """In front of the train: the hanging canopy lamps (shade + bulb), the platform-5 sign, the clock."""
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, D=['#8593A3', '#A1AAB7', '#C2C9D2', '#DEE2E7'])
    p = C.Paint(VW, VH, R, 'n1_mid')
    for lz in LAMPS_Z:
        top = proj(LAMP_X, CANOPY_Y, lz)
        bot = proj(LAMP_X, LAMP_Y + 0.25, lz)
        if top[1] < -10 and bot[1] < 40:
            continue
        p.put(p.box(top[0], top[1], top[0] + 1, bot[1]), 'I', 2.4)
        sw = max(2.0, 260.0 / lz / 2)
        sh = max(1.0, 110.0 / lz)
        shade = p.poly([(bot[0] - sw * 0.4, bot[1]), (bot[0] + sw * 0.4, bot[1]), (bot[0] + sw, bot[1] + sh),
                        (bot[0] - sw, bot[1] + sh)])
        p.put(shade, 'I', 3.0)
        p.put(shade & ~C.shift(shade, 0, -1), 'W', 5.0)
        p.put(p.ell(bot[0], bot[1] + sh + max(0.8, 40.0 / lz), max(1.0, sw * 0.45), max(0.8, 40.0 / lz)), 'L', 6.0,
              emis=True)
    # the platform sign "5" hanging under the canopy (enamel, slate blue, white numeral)
    sz = 9.0
    c0 = proj(0.1, 3.95, sz)
    c1 = proj(0.9, 3.35, sz)
    sign = p.box(c0[0], c0[1], c1[0], c1[1])
    p.put(sign, 'N', 6.0)
    p.put(sign & ~C.kit.erode(sign, 1), 'W', 6.6)
    p.put(K.text_at('5', VW, VH, int((c0[0] + c1[0]) / 2), int(c0[1] + 3), font='l', center=True) & sign, 'W', 8.2)
    for hx_ in (c0[0] + 3, c1[0] - 4):
        p.put(p.box(hx_, proj(0.5, CANOPY_Y, sz)[1], hx_ + 1, c0[1]), 'I', 2.6)
    # a small platform clock (23.40) further down
    ck = proj(0.4, 3.55, 21.0)
    rr_ = 6
    yy, xx = p.yy, p.xx
    dial = K.disc(yy, xx, ck[0], ck[1], rr_)
    p.put(K.disc(yy, xx, ck[0], ck[1], rr_ + 1.4), 'I', 2.0)
    p.put(dial, 'D', 1.6)
    for (deg, ln) in ((350.0, 3.2), (240.0, 5.0)):
        u = (math.sin(math.radians(deg)), -math.cos(math.radians(deg)))
        p.put(p.line([(ck[0], ck[1]), (ck[0] + u[0] * ln, ck[1] + u[1] * ln)], 0.45), 'N', 1.0)
    p.put(p.box(ck[0], proj(0.4, CANOPY_Y, 21.0)[1], ck[0] + 1, ck[1] - rr_), 'I', 2.6)
    p.resolve(band=2.0)
    return p.L


def n1_fg():
    """Near foreground: a bench at the platform edge with snow on it, a litter bin, the near column base."""
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, D=['#22150F', '#331F16', '#4A2D1F', '#63402C'])
    p = C.Paint(VW, VH, R, 'n1_fg')
    yy, xx = p.yy, p.xx
    # bench (left foreground, side-on in perspective: seat from z 2.6 to 4.2)
    for (z0, z1) in ((2.8, 4.6),):
        seat = p.poly([proj(-0.9, 0.46, z0), proj(-0.9, 0.46, z1), proj(-0.45, 0.46, z1), proj(-0.45, 0.46, z0)])
        p.put(seat, 'D', 1.6)
        p.put(seat & ~C.shift(seat, 0, -1), 'W', 5.4)
        back = p.poly([proj(-0.95, 0.5, z0), proj(-0.95, 0.5, z1), proj(-0.95, 0.95, z1), proj(-0.95, 0.95, z0)])
        p.put(back, 'D', 1.2)
        for k in range(3):
            yb = 0.58 + k * 0.13
            sl = p.line([proj(-0.95, yb, z0), proj(-0.95, yb, z1)], 0.7)
            p.put(sl & back, 'D', 2.4)
        for lz in (z0 + 0.15, z1 - 0.15):
            leg = p.poly([proj(-0.9, 0.0, lz), proj(-0.9, 0.46, lz), proj(-0.86, 0.46, lz), proj(-0.86, 0.0, lz)])
            p.put(leg, 'I', 1.2)
    # litter bin on a post
    bx0, by0 = proj(-0.3, 0.9, 6.5)
    bx1, by1 = proj(-0.05, 0.45, 6.5)
    binm = p.box(bx0, by0, bx1, by1)
    p.put(binm, 'I', 2.0)
    p.put(binm & ~C.shift(binm, 0, -1), 'W', 5.0)
    p.put(p.box((bx0 + bx1) / 2, by1, (bx0 + bx1) / 2 + 1, proj(-0.2, 0.0, 6.5)[1]), 'I', 1.6)
    p.resolve(band=2.0)
    return p.L


def board():
    """The split-flap indicator hanging under the canopy at the left: 4 frames
    (0 = the special train, 1-2 = flaps turning, 3 = the row cleared)."""
    bw, bh = 196, 46
    x0, y0 = 24, 64
    R = C.ramps(N=NIGHT, I=IRONR, P=['#1A2431', '#2A3646', '#4A4236', '#80745E', '#BBAD8F', '#D6CBAE', '#F2F3F5'],
                L=LAMPR)
    sheet = np.zeros((bh * 4, bw, 4), np.uint8)
    rows = [('23.40', 'SONDERZUG', 'KORDON-17', '5')]
    cols_x = [6, 34, 92, 178]
    for fr in range(4):
        p = C.Paint(bw, bh, R, 'board')
        box = p.box(0, 0, bw, bh)
        p.put(box, 'I', 1.4)
        p.put(box & ~C.kit.erode(box, 1), 'I', 3.4)
        p.put(p.box(0, 0, bw, 1), 'I', 5.0)
        hdr = K.text_at('ABFAHRT · ОТПРАВЛЕНИЕ · DÉPART', bw, bh, bw // 2, 4, font='s', center=True)
        p.put(hdr, 'P', 4.2)
        p.put(p.box(4, 12, bw - 4, 13), 'I', 3.0)
        # the flap cells of the one live row
        ry = 20
        cells = np.zeros((bh, bw), bool)
        for k in range(0, (bw - 12) // 6):
            cells |= p.box(6 + k * 6, ry - 2, 6 + k * 6 + 5, ry + 9)
        p.put(cells, 'N', 4.0)
        p.put(cells & (p.yy == ry + 3), 'N', 1.0)                             # the split of every flap
        rng = np.random.default_rng(711 + fr)
        if fr == 0:
            for (txt, cx) in zip(rows[0], cols_x):
                m = K.text_at(txt, bw, bh, cx, ry, font='s')
                p.put(m, 'P', 5.6)
        elif fr in (1, 2):
            for (txt, cx) in zip(rows[0], cols_x):
                m = K.text_at(txt, bw, bh, cx, ry, font='s')
                keep = (rng.random((bh, bw)) > (0.45 if fr == 1 else 0.75)) & ((p.yy < ry + 3) if fr == 1 else (p.yy >= ry + 2))
                p.put(m & keep, 'P', 5.0)
                p.put(m & ~keep & (p.yy >= ry + 3), 'P', 3.4)
        # second row: an older, already cleared slot (blank flaps), a third with the next morning train
        for k in range(0, (bw - 12) // 6):
            p.put(p.box(6 + k * 6, 33, 6 + k * 6 + 5, 44), 'N', 3.4)
        m2 = K.text_at('06:12', bw, bh, 6, 35, font='s') | K.text_at('BERLIN', bw, bh, 34, 35, font='s') | \
            K.text_at('4', bw, bh, 178, 35, font='s')
        p.put(m2, 'P', 4.6)
        p.resolve(band=2.0)
        sheet[fr * bh:(fr + 1) * bh] = p.L.c
    LAYOUT['board'] = [x0, y0]
    return sheet


def steam():
    """Eight frames of the engine's steam drifting back under the canopy (120 x 70), lit by the platform lamps:
    one cloud at successive ages (CT._drift_frames, AD round 2) that the runtime cross-fades through."""
    import env_veltrava_cine_city as CT
    n, fw, fh = 8, 120, 70
    LAYOUT['steam_frames'] = n
    return CT._drift_frames(n, fw, fh, ['#121A26', '#1A2431', '#2A3646', '#3A4859', '#4F5E70', '#687789'], 721,
                            light=(-0.4, 0.8), aspect=1.9, lobes=13, grow=(0.65, 1.0), thin=0.6)


def n1_glow():
    """Additive light of platform 5: the cones of the canopy lamps falling through the snow onto the platform,
    their halos, the green far signal, the yard lamps."""
    yy, xx = _grid()
    a = np.zeros((VH, VW, 3), np.float32)
    for lz in LAMPS_Z:
        bx, by = proj(LAMP_X, LAMP_Y, lz)
        fx, fy = proj(LAMP_X, 0.0, lz)
        r = max(4.0, 420.0 * 0.5 / lz)
        d = np.hypot((xx - bx) / (r * 1.2), (yy - by) / r)
        g = np.clip(1 - d, 0, 1) ** 1.6
        h = max(1.0, fy - by)
        u = np.clip((yy - by) / h, 0, 1)
        half = r * 0.3 + u * (420.0 * 1.4 / lz)
        cone = np.clip(1 - np.abs(xx - (bx + (fx - bx) * u)) / np.maximum(half, 1.0), 0, 1) * (yy > by) * (yy < fy)
        cone = cone ** 1.4 * (0.35 + 0.65 * u) * np.clip(18.0 / lz, 0.2, 1.0)
        for c, v in enumerate((64, 42, 20)):
            a[..., c] += g * v + cone * v * 0.45
    # AD round 2: the lit lamps of platform 6, the yard's floodlight mast, the fire pot at the water crane
    for (lx_, ly_, lz) in LAYOUT.get('pl6_lamps', []):
        r = max(3.0, 420.0 * 0.42 / lz)
        g = np.clip(1 - np.hypot((xx - lx_) / (r * 1.2), (yy - ly_ - 1) / r), 0, 1) ** 1.6
        for c, v in enumerate((48, 32, 16)):
            a[..., c] += g * v
    ym = LAYOUT.get('yard_mast')
    if ym:
        g = np.clip(1 - np.hypot((xx - ym[0]) / 16.0, (yy - ym[1]) / 9.0), 0, 1) ** 1.8
        for c, v in enumerate((40, 42, 46)):
            a[..., c] += g * v
    fp = LAYOUT.get('firepot')
    if fp:
        g = np.clip(1 - np.hypot(xx - fp[0], (yy - fp[1]) * 1.3) / 5.0, 0, 1) ** 1.5
        for c, v in enumerate((60, 30, 10)):
            a[..., c] += g * v
    sg = LAYOUT.get('signal', [262, 158])
    d = np.hypot(xx - sg[0], yy - sg[1]) / 6.0
    for c, v in enumerate((20, 70, 40)):
        a[..., c] += np.clip(1 - d, 0, 1) ** 1.5 * v
    return K.soft_quant(a, 6.0)


# =========================================================================== n2: the station square
def n2_bg():
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, R=V['red'],
                F=['#070A12', '#0C111C', '#121A26', '#1A2431', '#2A3646', '#3A4859', '#4A4236', '#645A49', '#80745E'],
                G=['#070A12', '#0C111C', '#15171C', '#1E2836', '#2A3646', '#3A4859', '#4F5E70'],
                P=['#0C111C', '#1E302E', '#2B4541', '#3D5E57', '#56796E'])
    p = C.Paint(VW, VH, R, 'n2_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    # night sky heavy with snow; the old town's glow low in the street between the hotels
    st = 1.4 + np.clip(1 - np.abs(xx - 320) / 260, 0, 1) * np.clip((yy - 60) / 170, 0, 1) * 2.4
    st += (pg.value_noise(VW, VH, 60, 731, 3) - 0.5) * 0.7
    p.put(allm, 'N', st)
    # ---- the street into the old town: gables, the dome of the palais, a few lit windows
    town = np.zeros((VH, VW), bool)
    rng = np.random.default_rng(732)
    x = 196.0
    while x < 444:
        w_ = rng.uniform(12, 22)
        h_ = rng.uniform(28, 52)
        top = 236 - h_
        town |= p.box(x, top, x + w_, 244)
        town |= p.poly([(x, top), (x + w_ / 2, top - rng.uniform(6, 11)), (x + w_, top)])
        x += w_
    dome = p.ell(322, 168, 17, 16) & (yy < 170)
    town |= dome | p.box(305, 168, 340, 244) | p.box(321, 142, 323, 152)
    p.put(town, 'N', 2.6)
    p.put(dome, 'P', 1.4)
    for _ in range(46):
        wx, wy = int(rng.uniform(200, 440)), int(rng.uniform(190, 238))
        if town[wy, wx] and town[wy + 1, wx + 1] and not dome[wy, wx]:
            p.put(p.box(wx, wy, wx + 2, wy + 2), 'L', float(rng.choice([1.6, 2.4, 3.0])), emis=True)
    p.put(town & ~C.shift(town, 0, -1), 'W', 3.2)
    p.px(322, 141, 'R', 3.0)                                                   # aircraft light on the lantern

    def facade(x0, x1, top, name, floors, tone, seed, kind):
        """A hotel front at night: dark masonry, snow on every ledge, the ground floor lit from the street."""
        fm = p.box(x0, top, x1, 254)
        lit_low = np.clip((yy - 180) / 74, 0, 1) ** 1.6                       # street light climbing the wall
        p.put(fm, 'F', tone + lit_low * 2.4 + (pg.value_noise(VW, VH, 9, seed, 2) - 0.5) * 0.5)
        rows = []
        fy = top + 14
        for k in range(floors):
            rows.append(fy)
            fy += 34 if k == 0 else 30
        ground = rows[-1] + 30
        # string courses and cornices with snow on them
        for cy in [top + 6] + [r - 6 for r in rows[1:]] + [ground - 4]:
            p.put(p.box(x0 - 2, cy, x1 + 2, cy + 3), 'F', tone + 1.2 + float(lit_low[cy, 0]) * 2.0)
            p.put(p.box(x0 - 2, cy - 1, x1 + 2, cy), 'W', 5.6)
        # windows (dark panes, white frames catching the snow light, sills with snow)
        wins = []
        step = 22 if kind == 'old' else 20
        for r_i, wy in enumerate(rows):
            for wx in range(x0 + 12, x1 - 14, step):
                ww, wh = (11, 18) if kind == 'old' else (13, 14)
                wm = p.box(wx, wy, wx + ww, wy + wh)
                p.put(wm, 'G', 1.2 + float(lit_low[wy, 0]) * 1.6)
                p.put(wm & ~C.kit.erode(wm, 1), 'F', tone + 2.2 + float(lit_low[wy, 0]) * 1.6)
                p.put(p.box(wx + ww // 2, wy, wx + ww // 2 + 1, wy + wh), 'F', tone + 1.6)
                p.put(p.box(wx - 1, wy + wh, wx + ww + 1, wy + wh + 1), 'W', 6.0)
                if kind == 'old':
                    p.put(p.box(wx - 1, wy - 3, wx + ww + 1, wy - 1), 'F', tone + 1.6)     # window hood
                    p.put(p.box(wx - 1, wy - 4, wx + ww + 1, wy - 3), 'W', 5.0)
                wins.append((wx, wy))
        # balconies with iron railings on the first floor (old hotel)
        if kind == 'old':
            for wx in range(x0 + 12, x1 - 14, step * 2):
                by = rows[1] + 18
                p.put(p.box(wx - 4, by, wx + 15, by + 2), 'F', tone + 1.4)
                p.put(p.box(wx - 4, by - 1, wx + 15, by), 'W', 6.0)
                for rx in range(wx - 4, wx + 16, 2):
                    p.put(p.box(rx, by - 6, rx + 1, by), 'I', 1.4)
                p.put(p.box(wx - 4, by - 7, wx + 15, by - 6), 'I', 2.0)
        # ground floor: arched shop windows / the lobby (lit), the entrance with a canopy and two lamps
        ex = (x0 + x1) // 2
        for k, gx in enumerate(range(x0 + 10, x1 - 16, 26)):
            arch = p.box(gx, ground + 8, gx + 16, 254) | (p.ell(gx + 8, ground + 8, 8, 6) & (yy < ground + 8))
            lobby = abs(gx + 8 - ex) < 30
            p.put(arch, 'L' if lobby else 'G', 2.2 if lobby else 1.0, emis=lobby)
            p.put(arch & ~C.kit.erode(arch, 1), 'F', tone + 3.0)
        p.put(p.box(ex - 22, ground + 4, ex + 22, ground + 8), 'I', 2.6)
        p.put(p.box(ex - 22, ground + 3, ex + 22, ground + 4), 'W', 6.6)
        for lx in (ex - 25, ex + 24):
            p.put(p.box(lx, ground + 10, lx + 2, ground + 14), 'L', 5.4, emis=True)
        # roof: mansard with dormers (old) or a flat roof with a parapet (new), snow on top
        if kind == 'old':
            roof = p.poly([(x0 - 4, top), (x0 + 8, top - 20), (x1 - 8, top - 20), (x1 + 4, top)])
            p.put(roof, 'N', 1.8)
            p.put(roof & ~C.shift(roof, 0, -2), 'W', 6.0)
            for dx in range(x0 + 16, x1 - 16, 34):
                dm = p.box(dx, top - 15, dx + 10, top - 3) | p.poly([(dx - 1, top - 15), (dx + 5, top - 21), (dx + 11, top - 15)])
                p.put(dm, 'N', 2.6)
                p.put(p.box(dx + 3, top - 12, dx + 7, top - 5), 'G', 0.8)
                p.put(dm & ~C.shift(dm, 0, -1), 'W', 6.2)
            for cx in (x0 + 30, x1 - 40):
                p.put(p.box(cx, top - 30, cx + 5, top - 18), 'N', 2.2)
                p.put(p.box(cx, top - 31, cx + 5, top - 30), 'W', 5.6)
        else:
            p.put(p.box(x0 - 2, top - 6, x1 + 2, top), 'F', tone + 0.8)
            p.put(p.box(x0 - 2, top - 7, x1 + 2, top - 6), 'W', 6.2)
        nm = K.text_at(name, VW, VH, ex, top - (16 if kind == 'old' else 4) - 8, font='s', center=True)
        p.put(nm, 'L', 4.4, emis=True)
        return wins, rows, ground
    wl, rows_l, gl = facade(0, 214, 104, 'HOTEL EUROPA', 3, 1.0, 733, 'old')
    wr, rows_r, gr = facade(428, 640, 92, 'HOTEL NORD', 4, 0.8, 734, 'new')
    # ---- the square: snow over the cobbles, the tram rails curving away, tyre tracks, footprints
    sq = p.box(0, 254, VW, VH)
    p.put(sq, 'W', 3.2 + (pg.value_noise(VW, VH, 20, 735, 2) - 0.5) * 0.8 - np.clip((yy - 254) / 60, 0, 1) * 0.5)
    for a_ in (0.0, 6.0):
        pts = [(330 + a_, 254), (318 + a_, 270), (276 + a_, 292), (180 + a_, 314), (80 + a_, 330)]
        p.put(p.line(pts, 0.45), 'I', 2.6)
    tyre = p.line([(250, 254), (262, 280), (300, 316)], 0.6) | p.line([(262, 254), (276, 280), (318, 316)], 0.6)
    p.put(tyre, 'W', 2.0)
    for k in range(14):
        fx = 560 - k * 13 + (k % 2) * 3
        fy = 264 + k * 4
        p.put(p.box(fx, fy, fx + 2, fy + 1), 'W', 1.8)
    # ---- limes along the street and the parked car under them
    for (tx, th) in ((236, 70), (404, 64), (276, 54), (366, 50)):
        p.put(p.box(tx, 254 - th, tx + 2, 256), 'N', 0.8)
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * 0.42
            ln = th * 0.35 + (k % 3) * 4
            sx0, sy0 = tx + 1, 254 - th * 0.55 - (k % 2) * 6
            br = p.line([(sx0, sy0), (sx0 + math.cos(ang) * ln, sy0 + math.sin(ang) * ln)], 0.45)
            p.put(br, 'N', 1.2)
            p.put(br & ~C.shift(br, 0, -1), 'W', 4.4)
    car = p.rr(250, 238, 306, 254, 4) | p.rr(262, 228, 294, 242, 5)
    p.put(car, 'N', 1.2)
    p.put(car & ~C.shift(car, 0, -1), 'W', 6.0)
    p.put(p.rr(266, 231, 290, 239, 3), 'N', 0.4)
    for wx in (258, 298):
        p.put(p.ell(wx, 254, 4, 3) & (yy < 255), 'N', 0.2)
    LAYOUT['ember'] = [281, 235]
    # the street lamp in the middle of the square
    lpx = 352
    p.put(p.box(lpx, 198, lpx + 2, 264), 'I', 1.6)
    p.put(p.box(lpx - 3, 260, lpx + 5, 266), 'I', 1.4)
    for s_ in (-1, 1):
        arm = p.line([(lpx + 1, 202), (lpx + 1 + s_ * 9, 198), (lpx + 1 + s_ * 13, 201)], 0.5)
        p.put(arm, 'I', 1.6)
        p.put(p.box(lpx + 1 + s_ * 13 - 2, 201, lpx + 1 + s_ * 13 + 3, 207), 'L', 5.4, emis=True)
    LAYOUT['lamp'] = [lpx + 1, 204]
    pool = np.clip(1 - np.hypot((xx - lpx) / 70, (yy - 266) / 14), 0, 1) * sq
    p.put(pool > 0.2, 'W', 3.6 + pool * 3.2)
    p.put(pool > 0.62, 'L', 3.0 + pool * 1.4)
    # ---- round 10: the square is alive at 23.45 -- more lit rooms, lamps down the street into the old town,
    # a kiosk with its shutters down, an advertising column, a telephone box, the tram stop, a taxi at the Europa
    rngw = np.random.default_rng(741)
    extra = []
    for (wx, wy) in list(wl) + list(wr):
        if rngw.random() < 0.16:
            ww_, wh_ = (11, 18) if wx < 320 else (13, 14)
            room_ = p.box(wx + 1, wy + 1, wx + ww_ - 1, wy + wh_ - 1)
            p.put(room_, 'L', 2.6 + rngw.random() * 1.2 - np.clip((yy - wy) / wh_, 0, 1) * 0.8, emis=True)
            p.put(p.box(wx + 1, wy + 1, wx + 3, wy + wh_ - 1), 'L', 1.4, emis=True)          # drawn curtain
            p.put(p.box(wx + ww_ // 2, wy, wx + ww_ // 2 + 1, wy + wh_), 'F', 2.4)
            extra.append([int(wx) + ww_ // 2, int(wy) + wh_ // 2])
    LAYOUT['n2_lit'] = extra
    lamps2 = []
    for (lx, base, hgt) in ((246, 252, 30), (276, 236, 18), (294, 226, 11), (398, 252, 30), (368, 236, 18),
                            (350, 226, 11)):
        p.put(p.box(lx, base - hgt, lx + 1, base), 'I', 1.4)
        hw = max(1, hgt // 10)
        p.put(p.box(lx - hw, base - hgt - max(1, hgt // 8), lx + hw + 1, base - hgt), 'L', 5.4, emis=True)
        p.put(p.box(lx - hw, base - hgt - max(1, hgt // 8) - 1, lx + hw + 1, base - hgt - max(1, hgt // 8)), 'W', 5.6)
        lamps2.append([lx, base - hgt - max(1, hgt // 16), hgt])
    LAYOUT['n2_lamps'] = lamps2
    # kiosk (closed): octagonal body, shutters, a roof with snow and a little sign
    kx0, kb = 472, 278
    kio = p.box(kx0, kb - 26, kx0 + 30, kb)
    p.put(kio, 'F', 1.6 + np.clip((xx - kx0) / 30, 0, 1) * 1.0)
    for k in range(kb - 22, kb - 6, 2):
        p.put(p.box(kx0 + 2, k, kx0 + 28, k + 1), 'F', 3.0)                             # the shutters
    p.put(p.poly([(kx0 - 4, kb - 26), (kx0 + 15, kb - 36), (kx0 + 34, kb - 26)]), 'N', 2.2)
    p.put(p.poly([(kx0 - 4, kb - 26), (kx0 + 15, kb - 36), (kx0 + 34, kb - 26)]) & ~C.shift(
        p.poly([(kx0 - 4, kb - 26), (kx0 + 15, kb - 36), (kx0 + 34, kb - 26)]), 0, -2), 'W', 6.4)
    p.put(p.box(kx0 + 6, kb - 30, kx0 + 24, kb - 27), 'P', 2.6)
    p.put(K.text_at('ZEITUNGEN', VW, VH, kx0 + 15, kb - 30, font='s', center=True) & p.box(kx0 + 4, kb - 31, kx0 + 26, kb - 26),
          'W', 6.0)
    # the advertising column with posters, its little dome capped with snow
    cx0, cb = 168, 284
    col = p.box(cx0, cb - 34, cx0 + 14, cb)
    p.put(col, 'F', 2.2 + np.clip((xx - cx0) / 14, 0, 1) * 1.6)
    for (py0, py1, tone, ramp) in ((cb - 30, cb - 20, 6.6, 'F'), (cb - 18, cb - 8, 3.0, 'P'), (cb - 30, cb - 22, 2.0, 'R')):
        p.put(p.box(cx0 + 2 + (5 if ramp == 'R' else 0), py0, cx0 + (12 if ramp != 'R' else 8), py1), ramp, tone)
    p.put(p.ell(cx0 + 7, cb - 35, 9, 4) & (yy < cb - 34), 'N', 2.0)
    p.put(p.ell(cx0 + 7, cb - 36, 8, 3) & (yy < cb - 35), 'W', 6.4)
    p.put(p.box(cx0 - 1, cb - 2, cx0 + 15, cb), 'N', 1.4)
    # the telephone box (glass, lit inside) by the Nord
    tx0, tb = 606, 272
    tbx = p.box(tx0, tb - 24, tx0 + 11, tb)
    p.put(tbx, 'F', 2.0)
    p.put(p.box(tx0 + 2, tb - 21, tx0 + 9, tb - 3), 'L', 2.6, emis=True)
    p.put(p.box(tx0 + 2, tb - 13, tx0 + 9, tb - 12), 'F', 2.4)
    p.put(p.box(tx0 - 1, tb - 26, tx0 + 12, tb - 24), 'W', 6.4)
    # the tram stop (a pole with the round sign), and the taxi waiting at the Europa with its roof sign lit
    p.put(p.box(332, 252, 333, 286), 'I', 1.8)
    p.put(p.ell(332.5, 252, 4, 4), 'P', 3.0)
    p.put(p.ell(332.5, 252, 2, 2), 'W', 6.0)
    taxi = p.rr(124, 264, 176, 276, 3) | p.rr(134, 255, 166, 266, 4)
    p.put(taxi, 'N', 1.6)
    p.put(taxi & ~C.shift(taxi, 0, -1), 'W', 6.2)
    p.put(p.rr(137, 257, 163, 264, 2), 'G', 1.2)
    p.put(p.box(146, 252, 154, 255), 'L', 5.6, emis=True)                                  # the roof sign
    p.put(p.box(125, 268, 128, 271), 'L', 3.6, emis=True)                                  # parking light
    for wx_ in (134, 166):
        p.put(p.ell(wx_, 276, 4, 3) & (yy < 277), 'N', 0.3)
    LAYOUT['n2_taxi'] = [177, 272]
    # the lobbies spill warm light onto the snow in front of both hotels; trails of footprints cross the square;
    # a row of snow-capped bollards with their chain along the near edge
    for (ex_, gy_) in ((107, 254), (534, 254)):
        spill = p.poly([(ex_ - 22, gy_), (ex_ + 22, gy_), (ex_ + 40, gy_ + 26), (ex_ - 40, gy_ + 26)]) & sq
        fall = np.clip(1 - (yy - gy_) / 26.0, 0, 1)
        p.put(spill & (fall * 1.1 > pg.bayer(VW, VH, 1, 2) + 0.15), 'L', 0.8 + fall * 1.2)
    rngt = np.random.default_rng(742)
    for (x0_, y0_, x1_, y1_) in ((120, 262, 330, 312), (540, 262, 420, 312), (330, 256, 470, 300)):
        n_ = int(np.hypot(x1_ - x0_, y1_ - y0_) / 6)
        for k in range(n_):
            u_ = k / max(1, n_ - 1)
            fx_ = x0_ + (x1_ - x0_) * u_ + (2 if k % 2 else -2) + rngt.uniform(-0.6, 0.6)
            fy_ = y0_ + (y1_ - y0_) * u_
            p.put(p.box(fx_, fy_, fx_ + 2, fy_ + 1), 'W', 1.6)
            p.put(p.box(fx_, fy_ - 1, fx_ + 2, fy_), 'W', 4.6)
    for bx_ in range(14, VW, 46):
        by_ = 306
        p.put(p.box(bx_, by_ - 9, bx_ + 4, by_), 'I', 1.6)
        p.put(p.box(bx_, by_ - 10, bx_ + 4, by_ - 8), 'W', 6.4)
        if bx_ + 46 < VW:
            for cxk in range(bx_ + 4, bx_ + 46):
                sag = 2.5 * math.sin(math.pi * (cxk - bx_ - 4) / 42.0)
                p.px(cxk, by_ - 7 + sag, 'I', 2.2)
    p.L.amb_field(-np.clip(np.hypot((xx - 320) / 420, (yy - 200) / 260) - 0.45, 0, 1) * 1.4)
    p.resolve(band=2.6)
    LAYOUT['windows_left'] = wl
    LAYOUT['windows_right'] = wr
    # the lit windows: second floor of Europa (Konrad), third floor of Nord (Alexei)
    kx, ky = wl[(len(wl) // 3) * 1 + 6]
    ax, ay = wr[(len(wr) // 4) * 2 + 4]
    LAYOUT['win_konrad'] = [int(kx) - 1, int(ky) - 1]
    LAYOUT['win_alexei'] = [int(ax) - 1, int(ay) - 1]
    LAYOUT['win_size'] = {'konrad': [13, 20], 'alexei': [15, 16]}
    return p.L


def _window_frames(who):
    """Frames of one lit hotel window: curtains half open, the lit room; 0 = empty, then the man steps to the
    glass and turns his head toward the station (the whistle).  Round 10b (figures stream): the states come from
    env_veltrava_cine_people.WINDOW_SEQ (empty, at the back of the room, beside the curtain, at the glass, the head
    half turned, the profile) and ch3_close.gd shows them on the schedule in LAYOUT['win_seq'] -- no more pop
    from an empty window to a full silhouette."""
    import env_veltrava_cine_people as PP
    seq = list(getattr(PP, 'WINDOW_SEQ', (0, 1, 2)))
    LAYOUT['win_frames'] = len(seq)
    if hasattr(PP, 'WINDOW_TIMES'):
        LAYOUT.setdefault('win_seq', {})[who] = [list(e) for e in PP.WINDOW_TIMES[who]]
    ww, wh = (13, 20) if who == 'konrad' else (15, 16)
    R = C.ramps(L=LAMPR, N=NIGHT, C=['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55'],
                F=['#121A26', '#1A2431', '#2A3646', '#3A4859', '#4A4236', '#645A49', '#80745E'])
    sheet = np.zeros((wh, ww * len(seq), 4), np.uint8)
    for fr, state in enumerate(seq):
        p = C.Paint(ww, wh, R, 'win')
        yy, xx = p.yy, p.xx
        room = p.box(1, 1, ww - 1, wh - 1)
        p.put(p.box(0, 0, ww, wh), 'F', 4.0)                                  # the frame
        p.put(room, 'L', 4.4 - np.clip((yy - 2) / wh, 0, 1) * 1.6 - np.abs(xx - ww / 2) * 0.06)
        p.put(p.box(ww // 2 - 2, 2, ww // 2 + 2, 4), 'L', 6.0)               # the ceiling lamp of the room
        p.put(p.box(1, 1, 3, wh - 1), 'C', 2.2)                               # curtains
        p.put(p.box(ww - 3, 1, ww - 1, wh - 1), 'C', 2.0)
        p.put(p.box(ww // 2, 0, ww // 2 + 1, wh), 'F', 3.4)                    # mullion
        if state != 0:
            # round 10 (figures stream): head with jaw / turned profile, neck, sloping shoulders, Alexei's tea
            # glass in its holder at his chest; a warm rim where the room lamp wraps round him
            fm = PP.window_figure_masks(who, ww, wh, state)
            tone = fm.get('tone', ('N', 0.6))
            p.put(fm['body'], tone[0], tone[1])
            p.put(fm['rim'] & ~p.box(ww // 2, 0, ww // 2 + 1, wh), 'C', 1.4)
            p.put(fm['glass'], 'L', 4.6)
            p.put(fm['glint'], 'L', 6.0)
            if tone[0] != 'N':
                # a figure at the back of the room stays behind the window cross
                p.put(p.box(ww // 2, 0, ww // 2 + 1, wh), 'F', 3.4)
        p.put(p.box(0, wh - 1, ww, wh), 'F', 5.0)
        p.resolve(band=2.0)
        sheet[:, fr * ww:(fr + 1) * ww] = p.L.c
    return sheet


def n2_win_konrad():
    return _window_frames('konrad')


def n2_win_alexei():
    return _window_frames('alexei')


def n2_lamp_glow():
    yy, xx = _grid()
    a = np.zeros((VH, VW, 3), np.float32)
    lx, ly = LAYOUT.get('lamp', [353, 202])
    for s_ in (-1, 1):
        cx = lx + s_ * 13
        d = np.hypot((xx - cx) / 26, (yy - ly) / 20)
        g = np.clip(1 - d, 0, 1) ** 1.6
        for c, v in enumerate((70, 46, 22)):
            a[..., c] += g * v
    for (lx_, ly_, hgt) in LAYOUT.get('n2_lamps', []):
        r_ = max(4.0, hgt * 0.55)
        d = np.hypot((xx - lx_) / r_, (yy - ly_) / (r_ * 0.8))
        g = np.clip(1 - d, 0, 1) ** 1.6
        for c, v in enumerate((60, 40, 18)):
            a[..., c] += g * v
    for (wx, wy) in LAYOUT.get('n2_lit', []):
        d = np.hypot((xx - wx) / 12, (yy - wy) / 12)
        g = np.clip(1 - d, 0, 1) ** 2.0
        for c, v in enumerate((22, 14, 6)):
            a[..., c] += g * v
    for (gx, gy, rr, col) in ((150, 253, 10, (60, 40, 14)), (611, 260, 14, (34, 24, 10))):
        d = np.hypot((xx - gx) / rr, (yy - gy) / (rr * 0.7))
        g = np.clip(1 - d, 0, 1) ** 1.6
        for c, v in enumerate(col):
            a[..., c] += g * v
    # the two lit hotel windows breathe a little light into the snow-filled air in front of them
    for (wx, wy) in (LAYOUT.get('win_konrad', [119, 157]), LAYOUT.get('win_alexei', [547, 147])):
        d = np.hypot((xx - wx - 6) / 22, (yy - wy - 10) / 22)
        g = np.clip(1 - d, 0, 1) ** 2.0
        for c, v in enumerate((30, 20, 9)):
            a[..., c] += g * v
    return K.soft_quant(a, 8.0)
