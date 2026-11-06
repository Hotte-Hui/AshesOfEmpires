"""env_veltrava_cine_line -- t3b of LS_C3_Trains (round 10): the Line before dawn.

Owner: cinematics stream (LS_C3_Trains places/motion).  A new shot between Alexei's compartment (t3) and the dawn
over Veltrava (t4): seen from high above the Line, the floodlit double fence runs straight to the horizon, where
the Free City glows under the low cloud; on its left Konrad's train, on its right Alexei's, both racing away from
us toward the same light without stopping.  Villages sleep on either side (a steeple in the west, an onion dome in
the east), searchlights sweep from the towers, the first pale band of the morning lies on the eastern horizon.

Art (assets/cinematics/ch3/trains/): l3_bg (sky, horizon city, ground, tracks, villages, the lit strip),
l3_fg (the fence posts, floodlight masts and watchtowers in front of the trains), l3_glow (additive halos).
The runtime draws the two trains in the same pinhole projection (LAYOUT['trains']['line']['proj']).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
kit = C.kit
shift = C.shift
LAYOUT = C.LAYOUT.setdefault('trains', {})

PROJ = {'vpx': 320.0, 'vpy': 122.0, 'f': 400.0, 'eye': 16.0}
TRACK_X = (-42.0, 42.0)                 # Konrad's track (west, left), Alexei's (east, right)
FENCE_X = (-7.0, 7.0)
MAST_X = -9.0
MAST_H = 11.0
MAST_Z = [float(z) for z in range(36, 1400, 46)]
TOWER_X = 9.5
TOWER_Z = [118.0, 386.0, 760.0]
POLE_DX = 5.0                            # telegraph poles on the outer side of each track
POLE_Z = [float(z) for z in range(18, 1200, 52)]

NIGHT = ['#04060B', '#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70',
         '#687789', '#8593A3', '#A1AAB7']
SNOWR = ['#121A26', '#1A2431', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2',
         '#DEE2E7', '#F2F3F5']
LAMPR = ['#22150F', '#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0', '#FFF4DA']
DAWNR = ['#1A2431', '#2A3646', '#3A4859', '#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3']
IRONR = ['#05070C', '#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#8593A3']
COLDL = ['#2A3646', '#4F5E70', '#8593A3', '#B6C4D6', '#DEE7F2', '#F6FAFF']


def ramps():
    return C.ramps(N=NIGHT, W=SNOWR, L=LAMPR, D=DAWNR, I=IRONR, F=COLDL, R=C.V['red'],
                   P=['#0C1A1A', '#1E302E', '#2B4541', '#3D5E57'])


def proj(x, y, z):
    zz = max(z, 0.3)
    return (PROJ['vpx'] + PROJ['f'] * x / zz, PROJ['vpy'] - PROJ['f'] * (y - PROJ['eye']) / zz)


def ground_xz(yy, xx):
    dy = yy - PROJ['vpy']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = PROJ['f'] * PROJ['eye'] / dy
        x = (xx - PROJ['vpx']) * z / PROJ['f']
    bad = ~(dy > 0.25)
    return np.where(bad, np.nan, z), np.where(bad, np.nan, x)


def world_noise(x, z, scale, seed):
    """Value noise on world coordinates (vectorised): smooth in [0, 1]."""
    x = np.nan_to_num(x, nan=0.0) / scale
    z = np.nan_to_num(z, nan=0.0) / scale
    xi = np.floor(x).astype(np.int64)
    zi = np.floor(z).astype(np.int64)
    fx = x - xi
    fz = z - zi
    fx = fx * fx * (3 - 2 * fx)
    fz = fz * fz * (3 - 2 * fz)

    def h(a, b):
        n = (a * 374761393 + b * 668265263 + seed * 1442695041) & 0x7fffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0x7fffffff
        return (n & 0xffff) / 65535.0
    a = h(xi, zi)
    b = h(xi + 1, zi)
    c = h(xi, zi + 1)
    d = h(xi + 1, zi + 1)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fz


def _line(p, x0, z0, x1, z1, y=0.0, r=0.5):
    return p.line([proj(x0, y, z0), proj(x1, y, z1)], r)


# =========================================================================== background
def l3_bg():
    R = ramps()
    p = C.Paint(VW, VH, R, 'l3_bg')
    yy, xx = p.yy, p.xx
    vpx, vpy = PROJ['vpx'], PROJ['vpy']
    allm = np.ones((VH, VW), bool)
    # ---- sky: black-blue overhead; the low cloud deck lit from below by the Line (a cold band over the fence)
    # and by the city (warm, at the vanishing point); the first pale band of the morning on the eastern horizon
    u = np.clip((yy - 20) / (vpy - 20), 0, 1)
    st = 1.2 + u ** 1.6 * 3.2 + (pg.value_noise(VW, VH, 46, 1501, 3) - 0.5) * 0.8
    linelit = np.clip(1 - np.abs(xx - vpx) / (40 + (vpy - yy) * 2.2), 0, 1) * np.clip((yy - 40) / (vpy - 40), 0, 1)
    st += linelit * 1.8
    p.put(allm, 'N', st)
    rngc = np.random.default_rng(1502)
    for _ in range(16):                                                              # stratus banks, lit from below
        by = rngc.uniform(26, vpy - 8)
        x0 = rngc.uniform(-200, 560)
        ln = rngc.uniform(140, 420)
        th = rngc.uniform(1.5, 5.0) * (0.5 + (by - 20) / 100)
        slope = rngc.uniform(-0.01, 0.01)
        prof = np.clip(1 - np.abs(yy - by - slope * (xx - x0)) / th, 0, 1)
        taper = np.clip(np.minimum(xx - x0, x0 + ln - xx) / 60.0, 0, 1)
        dens = prof ** 0.7 * taper * (0.7 + 0.6 * pg.value_noise(VW, VH, 18, int(rngc.integers(1 << 20)), 2))
        band = dens > pg.bayer(VW, VH, 2, 3) * 0.9 + 0.1
        uu = np.clip((by - 20) / (vpy - 20), 0, 1)
        lit = np.clip(1 - np.abs(xx - vpx) / (60 + (vpy - by) * 3.0), 0, 1)
        p.put(band, 'N', 1.4 + uu * 2.4 + lit * 1.6)
        under = band & ~shift(band, 0, 1) & (yy > by)
        p.put(under, 'N', 2.6 + uu * 2.6 + lit * 2.4)
    east = np.clip((xx - 330) / 310, 0, 1) * np.clip(1 - (vpy - yy) / 34, 0, 1) * (yy < vpy + 1)
    p.put((east * 1.4 > pg.bayer(VW, VH, 1, 1)) & (east > 0.05), 'D', 1.6 + east * 4.6)
    glow = np.clip(1 - np.hypot((xx - vpx) / 120, (yy - vpy + 4) / 26), 0, 1) ** 1.4
    p.put((glow * 1.5 > pg.bayer(VW, VH, 2, 3)) & (glow > 0.04) & (yy < vpy + 1), 'L', 0.6 + glow * 2.6)
    # ---- the horizon: low forest belts on both sides, the city at the vanishing point
    rng = np.random.default_rng(1503)
    hz = np.zeros((VH, VW), bool)
    for xa, xb in ((0, 270), (372, VW)):
        x = xa
        while x < xb:
            w_ = rng.uniform(2, 6)
            hgt = rng.uniform(1.5, 4.5) * (1.0 if abs(x - vpx) > 90 else 0.6)
            hz |= p.box(x, vpy - hgt, x + w_ + 1, vpy + 1)
            x += w_
    p.put(hz, 'N', 1.4)
    city = np.zeros((VH, VW), bool)
    x = vpx - 34
    while x < vpx + 34:
        w_ = rng.uniform(2, 5)
        city |= p.box(x, vpy - rng.uniform(2, 6), x + w_, vpy + 1)
        x += w_
    city |= p.ell(vpx + 2, vpy - 7, 5, 5) & (yy < vpy - 6) | p.box(vpx - 3, vpy - 7, vpx + 8, vpy)
    city |= p.box(vpx + 1, vpy - 15, vpx + 3, vpy - 11)
    city |= p.poly([(vpx - 20, vpy - 4), (vpx - 18, vpy - 16), (vpx - 16, vpy - 4)])
    city |= p.poly([(vpx - 13, vpy - 4), (vpx - 11.5, vpy - 12), (vpx - 10, vpy - 4)])
    city |= p.box(vpx + 18, vpy - 12, vpx + 21, vpy) | p.poly([(vpx + 17, vpy - 12), (vpx + 19.5, vpy - 17), (vpx + 22, vpy - 12)])
    p.put(city, 'N', 2.0)
    for _ in range(46):
        wx, wy = rng.uniform(vpx - 34, vpx + 34), rng.uniform(vpy - 6, vpy)
        if city[int(wy), int(wx)]:
            p.px(wx, wy, 'L', float(rng.choice([2.4, 3.2, 4.2])))
    p.px(vpx + 2, vpy - 16, 'R', 3.0)                                                 # aircraft light on the dome
    # ---- ground (snow plain), perspective furrows, darker far away
    zg, xg = ground_xz(yy, xx)
    ground = (yy > vpy) & np.isfinite(zg)
    zf = np.nan_to_num(zg, nan=1e4)
    xf = np.nan_to_num(xg, nan=0.0)
    far = np.clip((zf - 40) / 900, 0, 1)
    n1 = world_noise(xf, zf, 18.0, 11)
    n2 = world_noise(xf * 3.0, zf, 6.0, 12)
    gt = 2.6 - far * 1.2 + (n1 - 0.5) * 0.9 + (n2 - 0.5) * 0.4
    # the Line's light on the snow: bright near the strip, falling off sideways
    strip_light = np.clip(1 - np.abs(xf) / 70.0, 0, 1) ** 1.8
    gt += strip_light * 2.6 * (1 - far * 0.6)
    p.put(ground, 'W', gt)
    furrow = ground & (np.sin(xf * 0.9 + n1 * 5.0) > 0.86) & (zf < 260)
    p.add(furrow, -0.7)
    sast = ground & (world_noise(xf * 0.4, zf * 2.5, 3.0, 13) > 0.78) & (zf < 140)
    p.add(sast, 0.6)
    # ---- the Line: control strip (raked, darker), patrol road, two fences (posts in l3_fg)
    strip = ground & (np.abs(xf) < FENCE_X[1])
    p.put(strip, 'W', 5.6 - far * 2.6 + (n2 - 0.5) * 0.6)
    raked = strip & (np.mod(np.abs(xf), 0.9) < 0.3) & (np.abs(xf) > 2.2) & (zf < 300)
    p.add(raked, -1.4)
    road = ground & (np.abs(xf) < 1.8)
    p.put(road, 'W', 4.0 - far * 2.2)
    for tx in (-1.0, 1.0):                                                            # tyre tracks
        p.put(_line(p, tx, 4.0, tx, 3000.0, 0.0, 0.4) & ground, 'W', 3.0)
    # floodlight pools on the strip under each mast
    for mz in MAST_Z:
        cx_, cy_ = proj(-3.0, 0.0, mz)
        rx = max(1.0, PROJ['f'] * 9.0 / mz)
        ry = max(0.6, rx * PROJ['eye'] / mz * 1.1)
        pool = p.ell(cx_, cy_, rx, ry) & ground
        p.add(pool, 1.0)
        p.add(p.ell(cx_, cy_, rx * 0.55, ry * 0.55) & ground, 0.9)
    for fx in FENCE_X:
        for yv, tone in ((2.6, 2.2), (1.3, 2.6)):
            p.put(_line(p, fx, 3.0, fx, 3000.0, yv, 0.45), 'I', tone)
        p.put(_line(p, fx, 3.0, fx, 3000.0, 0.0, 0.5) & ground, 'W', 6.6)              # drift along the fence foot
    # ---- the two tracks on their embankments, telegraph wires (poles in bg: behind the trains)
    for i, tx in enumerate(TRACK_X):
        emb = ground & (np.abs(xf - tx) < 3.6)
        lit_side = np.clip(1 - np.abs(xf) / 70.0, 0, 1) ** 1.8
        p.put(emb, 'W', 3.4 - far * 1.4 + lit_side * 1.6 + (n2 - 0.5) * 0.4)
        p.put(emb & (np.abs(xf - tx) > 2.6), 'W', 4.4 - far * 1.6 + lit_side * 1.6)          # snow on the shoulders
        bal = ground & (np.abs(xf - tx) < 1.7)
        p.put(bal, 'N', 2.4 - far * 1.0)
        sl = bal & (np.mod(zf, 0.7) < 0.26) & (zf < 160)
        p.put(sl, 'W', 3.2 - far * 1.2)
        for rx in (tx - 0.72, tx + 0.72):
            rm = _line(p, rx, 2.0, rx, 3000.0, 0.15, 0.5) & ground
            p.put(rm, 'I', 6.2)
        side = 1 if tx > 0 else -1
        pole_x = tx + side * POLE_DX
        for pz in POLE_Z:
            if pz < 6:
                continue
            a = proj(pole_x, 0.0, pz)
            b = proj(pole_x, 7.5, pz)
            pw = max(1.0, PROJ['f'] * 0.25 / pz)
            pm = p.box(a[0] - pw / 2, b[1], a[0] + pw / 2 + 0.5, a[1])
            p.put(pm, 'N', 1.6)
            cw = max(1.0, PROJ['f'] * 1.3 / pz)
            p.put(p.box(a[0] - cw, b[1], a[0] + cw + 0.5, b[1] + max(1.0, 8.0 / pz)), 'N', 1.8)
        for wy in (7.2, 6.6):
            p.put(_line(p, pole_x - 0.9, 6.0, pole_x - 0.9, 3000.0, wy, 0.35), 'N', 3.4)
    # ---- villages: a steeple in the west, an onion dome in the east (dark, a few lit windows, smoke)
    _village(p, rng, -150.0, 330.0, 'steeple')
    _village(p, rng, 140.0, 300.0, 'onion')
    _village(p, rng, -360.0, 900.0, 'farm')
    _village(p, rng, 300.0, 820.0, 'farm')
    p.resolve(band=2.6)
    L = LAYOUT.setdefault('line', {})
    L['proj'] = dict(PROJ)
    L['track_x'] = list(TRACK_X)
    L['towers'] = [[TOWER_X, z] for z in TOWER_Z]
    L['masts'] = [[MAST_X, MAST_H, z] for z in MAST_Z[:16]]
    return p.L


def _village(p, rng, vx, vz, kind):
    """A handful of houses at world (vx, vz): roofs with snow, lit windows, a church."""
    yy, xx = p.yy, p.xx
    houses = []
    for k in range(7 if kind != 'farm' else 3):
        hx = vx + rng.uniform(-40, 40)
        hz = vz + rng.uniform(-50, 50)
        houses.append((hz, hx))
    houses.sort(reverse=True)                     # far first
    for (hz, hx) in houses:
        w = rng.uniform(8, 14)
        h = rng.uniform(4, 6)
        a = proj(hx - w / 2, 0.0, hz)
        b = proj(hx + w / 2, h, hz)
        wall = p.box(a[0], b[1], b[0] + 0.5, a[1] + 0.5)
        p.put(wall, 'N', 1.6)
        rh = max(1.0, PROJ['f'] * 3.5 / hz)
        roof = p.poly([(a[0] - 0.5, b[1] + 0.5), ((a[0] + b[0]) / 2, b[1] - rh), (b[0] + 0.5, b[1] + 0.5)])
        p.put(roof, 'W', 4.2)
        p.put(roof & ~shift(roof, 0, -1), 'W', 6.0)
        if rng.random() < 0.6:
            wx = rng.uniform(a[0] + 0.5, max(a[0] + 0.6, b[0] - 0.5))
            p.px(wx, (a[1] + b[1]) / 2, 'L', float(rng.choice([2.6, 3.4, 4.2])))
    cz = vz + 10
    if kind == 'steeple':
        a = proj(vx + 8, 0.0, cz)
        b = proj(vx + 12, 14.0, cz)
        tw = p.box(a[0], b[1], b[0] + 0.5, a[1])
        p.put(tw, 'N', 1.8)
        tip = proj(vx + 10, 26.0, cz)
        p.put(p.poly([(a[0] - 0.5, b[1] + 0.5), tip, (b[0] + 1.0, b[1] + 0.5)]), 'N', 1.6)
        p.px(tip[0], tip[1] - 1, 'N', 1.6)
    elif kind == 'onion':
        a = proj(vx - 6, 0.0, cz)
        b = proj(vx - 1, 10.0, cz)
        p.put(p.box(a[0], b[1], b[0] + 0.5, a[1]), 'N', 1.8)
        c = proj(vx - 3.5, 12.5, cz)
        r = max(1.0, PROJ['f'] * 3.0 / cz)
        on = p.ell(c[0], c[1], r, r) | p.poly([(c[0] - r * 0.6, c[1] - r * 0.4), (c[0], c[1] - r * 2.2),
                                                 (c[0] + r * 0.6, c[1] - r * 0.4)])
        p.put(on, 'P', 2.4)
        p.put(on & ~shift(on, 0, -1), 'W', 5.4)
    LAYOUT.setdefault('line', {}).setdefault('villages', []).append([vx, vz])


# =========================================================================== foreground (in front of the trains)
def l3_fg():
    """Fence posts, floodlight masts with their lamp heads, the watchtowers (all between us and the trains)."""
    R = ramps()
    p = C.Paint(VW, VH, R, 'l3_fg')
    yy, xx = p.yy, p.xx
    for fx in FENCE_X:
        for z in np.arange(6.0, 260.0, 4.0):
            a = proj(fx, 0.0, z)
            b = proj(fx, 2.8, z)
            pw = max(1.0, PROJ['f'] * 0.12 / z)
            p.put(p.box(a[0] - pw / 2, b[1], a[0] + pw / 2 + 0.5, a[1] + 0.5), 'I', 2.4)
            # the bent-over top with its barbed wire
            arm = proj(fx + (0.5 if fx > 0 else -0.5), 3.2, z)
            p.put(p.line([b, arm], max(0.4, pw * 0.4)), 'I', 2.4)
    for i, mz in enumerate(sorted(MAST_Z, reverse=True)):
        if mz < 8:
            continue
        a = proj(MAST_X, 0.0, mz)
        b = proj(MAST_X, MAST_H, mz)
        pw = max(1.0, PROJ['f'] * 0.35 / mz)
        p.put(p.box(a[0] - pw / 2, b[1], a[0] + pw / 2 + 0.5, a[1] + 0.5), 'I', 1.6)
        p.put(p.box(a[0] - pw / 2, b[1], a[0] - pw / 2 + 1, a[1] + 0.5), 'I', 3.4)
        hw = max(1.0, PROJ['f'] * 0.9 / mz)
        hh = max(1.0, PROJ['f'] * 0.3 / mz)
        head = p.box(a[0] - hw, b[1] - hh, a[0] + hw + 0.5, b[1] + 0.5)
        p.put(head, 'I', 2.2)
        p.put(p.box(a[0] - hw, b[1], a[0] + hw + 0.5, b[1] + max(1.0, hh * 0.6)), 'F', 4.4, emis=True)
    for tz in TOWER_Z:
        base = proj(TOWER_X, 0.0, tz)
        top = proj(TOWER_X, 9.0, tz)
        w = PROJ['f'] * 1.6 / tz
        legs = p.box(base[0] - w, top[1], base[0] - w + max(1.0, w * 0.25), base[1]) | \
            p.box(base[0] + w - max(1.0, w * 0.25), top[1], base[0] + w, base[1])
        p.put(legs, 'I', 1.8)
        p.put(p.line([(base[0] - w, base[1]), (base[0] + w, top[1] + (base[1] - top[1]) * 0.5)], max(0.4, w * 0.12)), 'I', 1.6)
        cab_top = proj(TOWER_X, 12.5, tz)
        cab = p.box(base[0] - w * 1.4, cab_top[1], base[0] + w * 1.4, top[1] + 0.5)
        p.put(cab, 'I', 1.4)
        slit = p.box(base[0] - w * 1.0, cab_top[1] + (top[1] - cab_top[1]) * 0.35,
                     base[0] + w * 1.0, cab_top[1] + (top[1] - cab_top[1]) * 0.6)
        p.put(slit, 'L', 3.6, emis=True)
        roof = p.box(base[0] - w * 1.7, cab_top[1] - max(1.0, w * 0.4), base[0] + w * 1.7, cab_top[1] + 0.5)
        p.put(roof, 'I', 2.6)
        p.put(roof & ~shift(roof, 0, -1), 'W', 6.6)
    p.resolve(band=2.0)
    return p.L


def l3_glow():
    """Additive halos: the floodlight heads in the haze, the city glow on the horizon."""
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    a = np.zeros((VH, VW, 3), np.float32)
    for mz in MAST_Z:
        if mz < 8:
            continue
        cx, cy = proj(MAST_X, MAST_H, mz)
        r = max(3.0, PROJ['f'] * 6.0 / mz)
        d = np.hypot((xx + 0.5 - cx) / r, (yy + 0.5 - cy) / (r * 0.7))
        g = np.clip(1 - d, 0, 1) ** 1.6
        k = min(1.0, 50.0 / mz + 0.25)
        for c, v in enumerate((40, 48, 60)):
            a[..., c] += g * v * k
    d = np.hypot((xx - PROJ['vpx']) / 90.0, (yy - PROJ['vpy'] + 6) / 22.0)
    g = np.clip(1 - d, 0, 1) ** 1.5
    for c, v in enumerate((70, 44, 22)):
        a[..., c] += g * v
    return K.soft_quant(a, 6.0)


def preview():
    import os
    from PIL import Image
    bg = l3_bg().c.astype(np.float32)
    fg = l3_fg().c
    gl = l3_glow()
    img = bg[..., :3]
    a = fg[..., 3:4] / 255.0
    img = fg[..., :3] * a + img * (1 - a)
    img = np.clip(img + gl[..., :3], 0, 255)
    out = os.path.join(os.environ.get('TEMP', '.'), 'l3_preview.png')
    Image.fromarray(img.astype(np.uint8)).save(out)
    print(out)
