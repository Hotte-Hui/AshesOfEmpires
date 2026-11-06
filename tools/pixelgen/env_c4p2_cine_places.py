"""env_c4p2_cine_places -- structures painted in more than one Chapter-4-part-2 film (owner: cine stream).

Karsk depot: skyline() (cooling towers, chimneys, sheds, apartment blocks, plumes lit by the town), roundhouse()
(brick front with arched stall doors, roof vents, the patched banner), water_tower(), mast() (lattice floodlight
mast with its lamp cluster), gantry() (the coal crane with its grab), coal_heap(), gondola() (an open coal wagon:
planks, iron straps, stencils, bogies), barrel() (an oil drum fire basket), ground() (snow, tracks, footprints).
Each painter writes into a kit.GB with depths, so one light set lights them all.  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import pg
import env_c4p2_cine_kit as K
from env_c4p2_cine_kit import GB, lc, noise, snow_on, tex_noise


# ============================================================================================ Karsk skyline
def sky(g: GB, top='#070b12', mid='#162034', low='#3a3450', glow='#6a4a3c', horizon=186, glow_x=None, z=3000.0,
        clouds=True, seed=11):
    """Pre-dawn sky: night blue above, a violet band, the town's sodium glow low on the horizon; ragged
    clouds lit from below."""
    yy, xx = g.yy, g.xx
    u = np.clip((yy - g.oy) / max(1.0, horizon - g.oy), 0, 1)
    c = lc(top)[None, None] * (1 - u[..., None]) ** 1.6 + lc(mid)[None, None] * (1 - np.abs(u - 0.55)[..., None] * 1.8).clip(0, 1) + \
        lc(low)[None, None] * (u[..., None] ** 2.4)
    if glow_x is not None:
        gl = np.exp(-((xx - glow_x) / 260.0) ** 2) * u ** 3
        c = c + lc(glow)[None, None] * gl[..., None] * 0.8
    if clouds:
        n1 = noise(g.w, g.h, 40, seed, 4)
        n2 = noise(g.w, g.h, 11, seed + 1, 3)
        band = np.exp(-((u - 0.5) / 0.26) ** 2)
        cl = np.clip((n1 * 0.85 + n2 * 0.35 - 0.58) * 3.2, 0, 1) * band
        under = np.clip((n2 - 0.35) * 2, 0, 1) * (0.4 + u)
        c = c * (1 - cl[..., None] * 0.45) + lc(glow)[None, None] * (cl * under * 0.55)[..., None] +             lc(low)[None, None] * (cl * 0.25)[..., None]
    m = np.ones((g.h, g.w), bool)
    g.put(m, '#000000', z=z)
    g.em[m] = c[m]


def cooling_tower(g: GB, cx, base, half_b, half_t, height, z, col='#1a1e26', lit='#3a3036', seed=0):
    yy, xx = g.yy, g.xx
    v = np.clip((base - yy) / height, 0, 1)
    waist = 0.62
    half = np.where(v < waist, half_b + (half_t * 0.86 - half_b) * np.sin(v / waist * math.pi / 2),
                    half_t * 0.86 + (half_t - half_t * 0.86) * ((v - waist) / (1 - waist)) ** 2)
    m = (yy <= base) & (yy >= base - height) & (np.abs(xx - cx) <= half)
    side = (xx - cx) / np.maximum(half, 1)
    n = np.stack([side * 0.7, np.zeros_like(side), np.sqrt(np.clip(1 - (side * 0.7) ** 2, 0, 1))], -1)
    g.put(m, col, tex=tex_noise(g, 3, seed, 0.12) * (0.8 + 0.25 * v), n=n, z=z)
    g.put(m & (yy < base - height + 2), lit, z=z)
    rimm = m & ~K.shift(m, -1, 0) & (yy > base - height + 2)
    g.put(rimm, '#4a3a3c', z=z)
    for k in range(3):
        band = m & (np.abs(yy - (base - height * (0.25 + k * 0.22))) < 0.5)
        g.mul(band, 0.8)


def plume(g: GB, x0, y0, w, h, lean, col, lit, z, seed, dens=0.9):
    """A steam plume rising and leaning; its underside lit by the town (painted into the plate)."""
    yy, xx = g.yy, g.xx
    v = np.clip((y0 - yy) / h, 0, 1)
    cx = x0 + lean * v ** 1.4
    half = w * (0.5 + 1.6 * v)
    nz = noise(g.w, g.h, 7, seed, 4)
    d = np.abs(xx - cx) / np.maximum(half, 1)
    f = np.clip(1 - d, 0, 1) * (1 - v) ** 0.6 * (0.5 + nz) * dens
    m = (f > 0.35) & (yy <= y0) & (yy >= y0 - h)
    k = np.clip((f - 0.35) * 2, 0, 1)
    al = lc(col)[None, None] * (0.6 + 0.4 * nz[..., None])
    g.put(m, al, z=z)
    g.em[m] += (lc(lit)[None, None] * ((1 - v) * k * 0.5)[..., None])[m]


def skyline(g: GB, base=186, z=1400.0, seed=21, towers=((58, 26, 17, 80), (122, 22, 15, 70)), blocks=(300, 440),
            chimneys=((178, 5, 94), (202, 4, 112), (262, 4, 124)), lit_k=0.6):
    """Far Karsk: cooling towers with plumes, chimneys with red lamps, sheds with saw-tooth roofs, apartment
    blocks with a scatter of lit windows, all softened by the haze (depth)."""
    for i, (cx, hb, ht, hh) in enumerate(towers):
        plume(g, cx + 2, base - hh + 2, ht * 0.8, 84, 46 + i * 12, '#2a2832', '#8a5a40', z + 10, seed + i, 0.75)
        cooling_tower(g, cx, base, hb, ht, hh, z, seed=seed + 5 + i)
    for (cx, w, top) in chimneys:
        g.put(g.box(cx - w // 2, top, cx + w - w // 2, base), '#151a22', tex=tex_noise(g, 2, seed, 0.1), z=z)
        g.put(g.box(cx - w // 2 - 1, top - 1, cx + w - w // 2 + 1, top + 1), '#151a22', z=z)
        g.glow(g.box(cx, top - 3, cx + 1, top - 2), '#ff3018', 1.6)
        plume(g, cx, top - 2, 3, 40, 30, '#24222a', '#6a4030', z + 5, seed + cx, 0.7)
    # sheds with saw-tooth roofs between the towers and the blocks
    x = 150
    k = 0
    while x < blocks[0]:
        w = 26 + int(K.hash2(k, 3, seed) * 14)
        h = 14 + int(K.hash2(k, 4, seed) * 10)
        g.put(g.box(x, base - h, x + w, base), '#141a22', z=z)
        for tx in range(x, x + w, 7):
            g.put(g.poly([(tx, base - h), (tx + 7, base - h), (tx + 7, base - h - 4)]), '#141a22', z=z)
            g.glow(g.box(tx + 5, base - h - 3, tx + 7, base - h), '#ffb060', 0.25 * lit_k)
        x += w + 2
        k += 1
    # apartment blocks: lit windows, a few blue (a radio dial, a television)
    for bi, bx in enumerate(range(blocks[0], blocks[1], 46)):
        bh = 30 + int(K.hash2(bi, 7, seed) * 26)
        bw = 34 + int(K.hash2(bi, 8, seed) * 10)
        g.put(g.box(bx, base - bh, bx + bw, base), '#121822', tex=tex_noise(g, 4, seed + bi, 0.08), z=z)
        g.put(g.box(bx - 1, base - bh - 1, bx + bw + 1, base - bh + 1), '#1a2230', z=z)
        for ax in range(bx + 4, bx + bw - 2, 11):                       # chimneys / aerials on the flat roof
            if K.hash2(ax, bi, seed) > 0.5:
                g.put(g.box(ax, base - bh - 4, ax + 2, base - bh), '#121822', z=z)
            else:
                g.put(g.box(ax, base - bh - 7, ax + 1, base - bh), '#1a2230', z=z)
                g.put(g.box(ax - 2, base - bh - 6, ax + 3, base - bh - 5), '#1a2230', z=z)
        for wy in range(base - bh + 4, base - 3, 5):
            for wx in range(bx + 3, bx + bw - 2, 5):
                r = K.hash2(wx, wy, seed + 9)
                if r > 0.86:
                    c = '#ffc070' if r < 0.975 else '#9ab8e0'
                    g.glow(g.box(wx, wy, wx + 2, wy + 2), c, 0.55 * lit_k)
                else:
                    g.put(g.box(wx, wy, wx + 2, wy + 2), '#0c1018', z=z)


# ============================================================================================ roundhouse
def roundhouse(g: GB, x0, x1, base, wall_top, z, doors, lit_door=None, banner=None, seed=31, vents=True):
    """Brick front of the roundhouse: pilasters, arched stall doors (wooden leaves, one open and lit), a low roof
    with smoke hoods, snow on every ledge.  doors = [(cx, half_w, arch_top)]."""
    wall = g.box(x0, wall_top, x1, base)
    soot = 0.75 + 0.25 * np.clip((g.yy - wall_top) / max(1, base - wall_top), 0, 1)
    K.bricks(g, wall, '#6a3424', '#3a3430', bw=8, bh=3, seed=seed, z=z, soot=soot)
    roof = g.poly([(x0 - 6, wall_top), (x1 + 6, wall_top), (x1 + 6, wall_top - 10), (x0 + 4, wall_top - 16)])
    K.corrugated(g, roof, '#2a2e34', period=3.0, vertical=True, z=z + 4, rust='#5a3420', seed=seed + 1)
    g.put(snow_on(roof, 3, seed + 2), '#dde4ec', n=(0, 0.9, 0.4), z=z + 4)
    g.put(g.box(x0 - 6, wall_top, x1 + 6, wall_top + 2), '#4a4642', z=z)          # cornice
    for (cx, hw, at) in doors:
        arch = g.box(cx - hw, at + hw * 0.55, cx + hw, base) | g.ell(cx, at + hw * 0.55, hw, hw * 0.55)
        ring = K.dilate(arch, 2) & ~arch & wall
        g.put(ring, '#7a4a32', tex=tex_noise(g, 2, seed + cx, 0.15), z=z)
        if lit_door is not None and abs(cx - lit_door) < 2:
            g.put(arch, '#100c0a', z=z + 30)
            K.ground_light_pool(g, cx, base - 20, hw * 1.4, 60, '#ffb060', 0.0)
        else:
            K.planks(g, arch, '#3a2a1e', pw=5, vertical=True, seed=seed + cx, z=z + 1)
            g.put(arch & (np.abs(g.xx - cx) < 1), '#1a120c', z=z + 1)
            for yb in (base - 26, base - 60):
                g.put(arch & (np.abs(g.yy - yb) < 1.5), '#1e2228', z=z + 1, gl=0.4)
        g.put(snow_on(g.box(cx - hw - 2, base - 1, cx + hw + 2, base), 1, seed), '#cfd7e0', z=z)
    if vents:
        for (cx, hw, at) in doors:
            vx = cx
            g.put(g.box(vx - 4, wall_top - 30, vx + 4, wall_top - 12), '#1c2026', tex=tex_noise(g, 2, seed, 0.15),
                  z=z + 6)
            g.put(g.poly([(vx - 8, wall_top - 30), (vx + 8, wall_top - 30), (vx + 4, wall_top - 36),
                          (vx - 4, wall_top - 36)]), '#24282e', z=z + 6)
            g.put(snow_on(g.box(vx - 8, wall_top - 31, vx + 8, wall_top - 30), 2, seed + vx), '#dde4ec', z=z + 6)
    if banner:
        bx0, by0, bx1, by1, text = banner
        tw = K.VK.vtext(text, 's').shape[1]
        cxb = (bx0 + bx1) // 2
        bx0, bx1 = min(bx0, cxb - tw // 2 - 4), max(bx1, cxb + tw // 2 + 4)
        bm = g.box(bx0, by0, bx1, by1)
        K.cloth(g, bm, '#8a1e16', seed + 7, folds=0.35, period=9, vertical=True, z=z - 2)
        tm = g.text(text, cxb - tw // 2, by0 + 1, 's') & bm
        g.put(tm, '#e8dcc4', z=z - 2)
        g.put(snow_on(bm, 1, seed + 8), '#dde4ec', z=z - 2)


def water_tower(g: GB, cx, tank_top, tank_h, r, base, z, seed=41):
    tank = g.box(cx - r, tank_top, cx + r, tank_top + tank_h)
    side = (g.xx - cx) / r
    n = np.stack([np.clip(side, -1, 1) * 0.8, np.zeros_like(side), np.sqrt(np.clip(1 - (side * 0.8) ** 2, 0, 1))], -1)
    K.planks(g, tank, '#3a2e24', pw=3, vertical=True, seed=seed, z=z)
    g.n[tank] = n[tank]
    for hy in (tank_top + 4, tank_top + tank_h - 5):
        g.put(tank & (np.abs(g.yy - hy) < 1), '#1c2024', n=n, z=z - 1, gl=0.5)
    cone = g.poly([(cx - r - 3, tank_top), (cx + r + 3, tank_top), (cx, tank_top - 12)])
    g.put(cone, '#262a30', z=z)
    g.put(snow_on(cone, 2, seed), '#e0e6ee', n=(0, 0.9, 0.4), z=z)
    for lx in (cx - r + 3, cx + r - 4):
        g.put(g.box(lx, tank_top + tank_h, lx + 2, base), '#1a1e24', z=z)
    g.put(g.line([(cx - r + 4, tank_top + tank_h + 6), (cx + r - 3, base - 10)], 0.5), '#1a1e24', z=z)
    g.put(g.line([(cx + r - 3, tank_top + tank_h + 6), (cx - r + 4, base - 10)], 0.5), '#1a1e24', z=z)


def mast(g: GB, x, top, base, z, lamps=4, seed=51):
    """A lattice floodlight mast; the lamp cluster's lenses are emissive (the beams are runtime glows)."""
    K.lattice_mast(g, x, top + 8, base, z, '#262c34', 6, seed)
    g.put(g.box(x - 9, top + 6, x + 10, top + 8), '#2a3038', z=z)
    for i in range(lamps):
        lx = x - 8 + (i % 2) * 9 + (i // 2) * 0
        ly = top + (i // 2) * -6
        g.put(g.box(lx, ly - 1, lx + 7, ly + 6), '#1e2228', z=z - 1)
        g.put(g.box(lx + 1, ly + 4, lx + 6, ly + 6), '#ffe8c0', em=lc('#ffe2b0') * 2.4, z=z - 2)
        g.put(snow_on(g.box(lx, ly - 1, lx + 7, ly), 1, seed + i), '#e6ecf2', z=z - 1)
    g.put(g.box(x - 2, top + 9, x + 3, top + 12), '#3a3e44', z=z)


def gantry(g: GB, xl, xr, girder_y, base, z, trolley_x, grab_y, seed=61):
    """The coal crane: two A-frame legs, a box girder with lattice sides, the trolley, cables and the grab."""
    for lx in (xl, xr):
        g.put(g.poly([(lx - 7, base), (lx - 2, girder_y + 8), (lx + 2, girder_y + 8), (lx + 7, base)]) &
              ~g.poly([(lx - 4, base), (lx - 1, girder_y + 16), (lx + 1, girder_y + 16), (lx + 4, base)]),
              '#3a2e1c', tex=tex_noise(g, 3, seed, 0.15), z=z, gl=0.2)
        for yb in range(girder_y + 20, base, 18):
            w = 2 + (yb - girder_y) * 6 / max(1, base - girder_y)
            g.put(g.box(lx - w, yb, lx + w, yb + 1), '#3a2e1c', z=z)
    gm = g.box(xl - 16, girder_y, xr + 16, girder_y + 10)
    g.put(gm, '#4a3a20', tex=tex_noise(g, 4, seed + 1, 0.1), z=z - 2, gl=0.2)
    for x in range(xl - 14, xr + 14, 8):
        g.put(g.line([(x, girder_y + 1), (x + 8, girder_y + 9)], 0.5) & gm, '#1e1810', z=z - 3)
    g.put(snow_on(gm, 2, seed + 2), '#e2e8ee', n=(0, 0.9, 0.4), z=z - 2)
    tx = trolley_x
    g.put(g.box(tx - 8, girder_y + 8, tx + 8, girder_y + 16), '#2a2418', z=z - 4)
    for cx in (tx - 3, tx + 3):
        g.put(g.box(cx, girder_y + 16, cx + 1, grab_y - 6), '#141414', z=z - 4)
    head = g.box(tx - 8, grab_y - 8, tx + 8, grab_y - 4)
    g.put(head, '#3a3e46', n=(0, 0.6, 0.8), z=z - 5, gl=0.6)
    for sgn in (-1, 1):
        jaw = g.poly([(tx, grab_y - 4), (tx + sgn * 9, grab_y - 4), (tx + sgn * 12, grab_y + 3),
                      (tx + sgn * 7, grab_y + 9), (tx + sgn * 1, grab_y + 4)])
        g.put(jaw, '#2e3238', n=(sgn * 0.5, 0.3, 0.8), z=z - 5, gl=0.6)
        g.put(g.line([(tx + sgn * 2, grab_y - 3), (tx + sgn * 10, grab_y + 3)], 0.5), '#5a606a', z=z - 6, gl=1.0)
        g.put(g.line([(tx + sgn * 8, grab_y - 6), (tx + sgn * 11, grab_y + 2)], 0.5), '#16181c', z=z - 6)
    g.put(g.box(tx - 1, grab_y + 3, tx + 1, grab_y + 9), '#121216', z=z - 6)
    g.put(g.box(tx - 3, grab_y - 9, tx + 4, grab_y - 8), '#5a606a', z=z - 6, gl=1.0)
    g.put(g.box(tx - 1, girder_y + 16, tx + 2, girder_y + 18), '#ffd8a0', em=lc('#ffd8a0') * 1.5, z=z - 6)


def coal_heap(g: GB, pts, z, seed=71, snow_k=0.5):
    """A heap of coal behind a contour polygon: lumps, glints, a dusting of snow on the gentle top."""
    m = g.poly(pts)
    K.coal(g, m, seed, 2.6, z=z, dust=0.25)
    top = K.top_edge(m)
    cap = np.zeros_like(m)
    for k in range(4):
        cap |= K.shift(top, 0, k) & (noise(g.w, g.h, 4, seed + k, 2) < snow_k - k * 0.12)
    cap &= m
    K.snow(g, cap, seed + 9, z=z)
    flakes = m & (noise(g.w, g.h, 2, seed + 13, 1) > 0.93) & (noise(g.w, g.h, 13, seed + 14, 2) < 0.35)
    g.put(flakes, '#b8c2ce', n=(0, 0.9, 0.4), z=z)
    return m


# ============================================================================================ wagons / props
def gondola(g: GB, x0, x1, top, rail_y, z, number='61 205', load=1.0, seed=81, col='#5a2a1c', stencil=True):
    """An open four-axle coal wagon (side view): plank body with iron stakes and straps, a stencilled number,
    coal heaped above the edge (load 0..1), two bogies with spoked wheels on the rail."""
    body_b = rail_y - 12
    body = g.box(x0, top, x1, body_b)
    K.planks(g, body, col, pw=5, vertical=False, seed=seed, z=z, gap='#1a0c08', grain=0.1)
    soot = noise(g.w, g.h, 6, seed + 1, 3)
    g.mul(body & (soot > 0.62), 0.7)
    for sx in range(int(x0) + 6, int(x1) - 4, 18):
        g.put(g.box(sx, top - 1, sx + 3, body_b + 1), '#1e1a18', z=z - 1, gl=0.3)
    for yb in (top + 1, body_b - 2):
        g.put(g.box(x0, yb, x1, yb + 2), '#262220', z=z - 1, gl=0.3)
    g.put(g.box(x0 - 2, body_b, x1 + 2, body_b + 3), '#1a1816', z=z - 1)
    if stencil:
        tm = g.text(number, x0 + 14, top + 9, 's')
        g.put(tm & body, '#d8d0bc', z=z - 1)
        tm2 = g.text('КАРСК', x1 - 40, top + 9, 's')
        g.put(tm2 & body, '#d8d0bc', z=z - 1)
    if load > 0:
        lh = 4 + 10 * load
        pts = [(x0 + 2, top)]
        n = 9
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + 2 + (x1 - x0 - 4) * u, top - lh * math.sin(math.pi * u) ** 0.6 - (K.hash2(i, 1, seed) - 0.5) * 3))
        pts.append((x1 - 2, top))
        cm = g.poly(pts)
        K.coal(g, cm, seed + 3, 2.2, z=z + 2)
        g.put(snow_on(cm, 1, seed + 4, 2.0) & (noise(g.w, g.h, 3, seed + 5, 1) > 0.5), '#c8d0da', z=z + 2)
    for bx in (x0 + 22, x1 - 22):
        g.put(g.box(bx - 16, body_b + 3, bx + 16, rail_y - 6), '#141618', z=z + 1)
        for wx in (bx - 9, bx + 9):
            wm = g.ell(wx, rail_y - 5, 5.5, 5.5)
            g.put(wm, '#1c2024', z=z + 1, gl=0.5)
            g.put(g.ell(wx, rail_y - 5, 1.5, 1.5), '#3a4048', z=z, gl=0.8)
            for a in range(0, 180, 45):
                r = math.radians(a)
                g.put(g.line([(wx - 4.5 * math.cos(r), rail_y - 5 - 4.5 * math.sin(r)),
                              (wx + 4.5 * math.cos(r), rail_y - 5 + 4.5 * math.sin(r))], 0.4) & wm, '#2a3036', z=z)
        g.put(g.box(bx - 3, body_b + 4, bx + 3, body_b + 8), '#2a2e34', z=z)
    for cx in (x0 - 3, x1 + 1):
        g.put(g.box(cx, body_b - 4, cx + 2, body_b - 1), '#22262a', z=z, gl=0.6)
    g.put(snow_on(body, 1, seed + 6), '#d6dde6', z=z - 1)


def barrel(g: GB, cx, top, base, z, seed=91):
    """An oil drum fire basket punched with holes (the holes glow), the rim lit from inside."""
    r = 9
    m = g.box(cx - r, top, cx + r, base)
    side = (g.xx - cx) / r
    n = np.stack([np.clip(side, -1, 1) * 0.85, np.zeros_like(side), np.sqrt(np.clip(1 - (side * 0.85) ** 2, 0, 1))],
                 -1)
    g.put(m, '#2a2420', tex=tex_noise(g, 2, seed, 0.25), n=n, z=z, gl=0.3)
    rustm = m & (noise(g.w, g.h, 3, seed + 1, 2) > 0.6)
    g.put(rustm, '#5a2e18', n=n, z=z)
    for hy in (top + 5, base - 6):
        g.put(m & (np.abs(g.yy - hy) < 1), '#1a1614', n=n, z=z)
    for k in range(9):
        hx_ = cx - 6 + (k % 3) * 6 + (k // 3) % 2 * 3
        hy = top + 8 + (k // 3) * 5
        g.put(g.box(hx_, hy, hx_ + 1, hy + 1), '#ffb040', em=lc('#ff9a30') * 1.8, z=z - 1)
    g.put(g.box(cx - r, top, cx + r, top + 1), '#ff9a40', em=lc('#ff8a30') * 1.2, z=z - 1)


def ground(g: GB, y0, y1, z, seed=101, tracks=(), foot=None, col='#dfe6ee', shade_col='#9eaabb'):
    m = g.box(-1000, y0, 5000, y1)
    K.snow(g, m, seed, z=z, col=col, shade_col=shade_col)
    for (ty, x0, x1, tz) in tracks:
        K.rail_side(g, ty, x0, x1, tz, seed=seed + int(ty))
    return m


# ============================================================================================ steam locomotive (side)
def _wheel(g: GB, cx, cy, r, z, col='#7a1a12', tyre='#1e2024', spokes=12, ang=0.0, hub='#2a2a2e', seed=0):
    """A spoked wheel: steel tyre, red centre with spokes, the crank boss."""
    disc = g.ell(cx, cy, r, r)
    g.put(disc, tyre, z=z, gl=0.6)
    ri = r - max(1.5, r * 0.12)
    inner = g.ell(cx, cy, ri, ri)
    g.put(inner, '#0e0e10', z=z - 0.2)
    sp = np.zeros_like(disc)
    for k in range(spokes):
        a = ang + 2 * math.pi * k / spokes
        sp |= g.line([(cx + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2),
                      (cx + math.cos(a) * (r - 1.5), cy + math.sin(a) * (r - 1.5))], max(0.5, r * 0.06))
    g.put(sp & inner, col, z=z - 0.4, gl=0.3)
    rim_ = inner & ~K.erode(inner, max(1, int(r * 0.08)))
    g.put(rim_, col, z=z - 0.4)
    g.put(g.ell(cx, cy, max(1.5, r * 0.22), max(1.5, r * 0.22)), col, z=z - 0.5, gl=0.4)
    g.put(g.ell(cx, cy, max(1.0, r * 0.1), max(1.0, r * 0.1)), hub, z=z - 0.6, gl=0.8)


def steam_loco(g: GB, x0, rail_y, z, facing=-1, kind='soviet', number='Л 2238', body='#18191c', wheels='#7a1a12',
               bands='#3a3c40', ribbons=False, polish=0.4, seed=301, tender=True):
    """A side-view steam locomotive.  kind 'soviet' (a 2-10-0 freight engine: five small coupled wheels, the
    cab with two windows), 'german' (a 4-6-2 express engine: three big drivers, smoke deflectors), 'show' (the
    soviet engine polished, with red ribbons and a fir garland).  x0 = the smokebox end; facing -1 = the
    smokebox at the left (the engine runs left).  Returns anchors (valve top, cab door, chimney, tender)."""
    f = facing
    big = kind == 'german'
    L = 330 if big else 300

    def X(u):
        return x0 - f * u if f < 0 else x0 + f * u

    def box_u(u0, u1, y0, y1):
        a, b = sorted((X(u0), X(u1)))
        return g.box(a, y0, b, y1)
    br = 28 if big else 26
    by = rail_y - (84 if big else 78)
    rb = by + br
    bo = box_u(18, L - 70, by - br, by + br)
    vv = np.clip((g.yy - by) / br, -1, 1)
    n = np.stack([np.zeros_like(vv), -vv * 0.9, np.sqrt(np.clip(1 - (vv * 0.9) ** 2, 0, 1))], -1)
    g.put(bo, body, tex=tex_noise(g, 5, seed, 0.06), n=n, z=z, gl=polish)
    for u in range(40, L - 80, 34):
        g.put(box_u(u, u + 2, by - br, by + br), bands, n=n, z=z - 0.2, gl=polish + 0.2)
    g.put(box_u(0, 22, by - br - 2, by + br + 2), '#121315', n=n, z=z - 0.3, gl=0.3)
    g.put(box_u(10, 20, by - br - 18, by - br + 1), '#141416', z=z - 0.4, gl=0.3)
    g.put(box_u(8, 22, by - br - 20, by - br - 16), '#1a1a1e', z=z - 0.5)
    for (u, w, h) in ((90 if big else 110, 18, 10), (150 if big else 170, 16, 8)):
        dm = g.ell(X(u), by - br, w / 2, h) & (g.yy <= by - br + 1)
        g.put(dm, body, n=(0, 0.7, 0.7), z=z - 0.3, gl=polish + 0.2)
    vx = X(210 if big else 196)
    g.put(g.box(vx - 5, by - br - 5, vx + 5, by - br + 1), '#5a4418' if big else '#3a2a14', z=z - 0.4, gl=0.9)
    g.put(g.box(vx - 3, by - br - 10, vx - 1, by - br - 4) | g.box(vx + 1, by - br - 10, vx + 3, by - br - 4),
          '#8a6a2a', z=z - 0.5, gl=1.0)
    valve_top = (vx, by - br - 10)
    if big:
        g.put(box_u(-2, 42, by - br - 6, by + br - 8), '#141517', tex=tex_noise(g, 4, seed + 3, 0.08), z=z - 2,
              gl=0.3)
    g.put(box_u(0, L - 66, rb, rb + 3), '#1a1b1e', z=z - 1, gl=0.4)
    g.put(box_u(28, L - 70, by - 2, by - 1), '#5a5c60', z=z - 1, gl=1.0)
    g.put(box_u(60, 72, rb - 26, rb), '#202124', z=z - 1.5, gl=0.5)
    cu0, cu1 = L - 70, L - 28
    g.put(box_u(cu0, cu1, by - br - 12, rb + 4), body, tex=tex_noise(g, 4, seed + 4, 0.06), z=z - 0.5, gl=polish)
    g.put(box_u(cu0 - 3, cu1 + 4, by - br - 16, by - br - 11), '#121316', z=z - 0.6)
    for k, (w0, w1) in enumerate(((cu0 + 6, cu0 + 18), (cu0 + 22, cu0 + 34))):
        g.put(box_u(w0, w1, by - br - 6, by - br + 10), '#0c0a08', em=lc('#ffa050') * (0.5 if k == 0 else 0.25),
              z=z - 0.7)
    g.put(box_u(cu1 - 10, cu1 - 2, by - 6, rb + 4), '#0e0a08', em=lc('#ff8a30') * 0.35, z=z - 0.7)
    cab_door = (X(cu1 - 6), by + 10)
    npm = box_u(cu0 + 8, cu0 + 36, by + 12, by + 20)
    g.put(npm, '#c8a050' if kind == 'show' else '#1e1e22', z=z - 0.8, gl=0.6)
    tw = K.VK.vtext(number, 's').shape[1]
    nx = int((X(cu0 + 8) + X(cu0 + 36)) / 2 - tw / 2)
    g.put(g.text(number, nx, by + 13, 's') & npm, '#2a1a0a' if kind == 'show' else '#e0d0a8', z=z - 0.9)
    g.put(box_u(4, L - 40, rb + 3, rail_y - 14), '#141416', z=z + 1)
    g.put(box_u(22, 50, rb + 2, rail_y - 18), '#1c1d20', tex=tex_noise(g, 2, seed + 5, 0.1), z=z - 1, gl=0.4)
    if big:
        drivers = [(98 + 48 * k, 19) for k in range(3)]
        others = [(34, 8), (58, 8), (262, 10)]
    else:
        drivers = [(70 + 34 * k, 12) for k in range(5)]
        others = [(36, 8)]
    for (u, r) in others:
        _wheel(g, X(u), rail_y - r - 1, r, z - 2, col=wheels, spokes=8, seed=seed + u)
    for (u, r) in drivers:
        _wheel(g, X(u), rail_y - r - 1, r, z - 2, col=wheels, spokes=14 if big else 10, seed=seed + u)
    rr = drivers[0][1]
    rod_y = rail_y - rr - 1 + rr * 0.45
    g.put(g.line([(X(drivers[0][0]), rod_y), (X(drivers[-1][0]), rod_y)], 1.2), '#5a5e64', z=z - 3, gl=1.0)
    g.put(g.line([(X(42), rail_y - rr - 6), (X(drivers[1 if big else 2][0]), rod_y)], 1.4), '#4a4e54', z=z - 3,
          gl=1.0)
    if ribbons:
        for u in (6, 40, 120, 200):
            bx_, by_ = X(u), (by - br + 4 if u < 30 else rb - 4)
            g.put(g.line([(bx_ - 4, by_ - 3), (bx_ + 4, by_ + 3)], 1.2) |
                  g.line([(bx_ - 4, by_ + 3), (bx_ + 4, by_ - 3)], 1.2), '#c8281c', z=z - 4)
            g.put(g.line([(bx_, by_), (bx_ - 2, by_ + 10)], 0.8) | g.line([(bx_, by_), (bx_ + 3, by_ + 9)], 0.8),
                  '#a81e14', z=z - 4)
        for u in range(30, L - 70, 5):
            gx, gy = X(u), rb - 1 + 3 * math.sin(u * 0.25)
            g.put(g.ell(gx, gy, 3, 2), '#1e4a26', tex=tex_noise(g, 1, seed + 7, 0.3), z=z - 4)
    out = dict(valve_top=valve_top, cab_door=cab_door, chimney=(X(15), by - br - 20), cab_x=sorted((X(cu0), X(cu1))))
    if tender:
        tu0, tu1 = L - 24, L + 92
        tb = box_u(tu0, tu1, by - br + 4, rb + 6)
        K.planks(g, tb, body, pw=40, vertical=True, seed=seed + 9, z=z + 2, gap='#0a0a0c', grain=0.02)
        g.put(box_u(tu0, tu1, by - br + 2, by - br + 5), '#121315', z=z + 1.5)
        g.put(box_u(tu0, tu1, rb + 6, rail_y - 12), '#141416', z=z + 2)
        for u in (tu0 + 22, tu0 + 44, tu1 - 44, tu1 - 22):
            _wheel(g, X(u), rail_y - 9, 8, z, col=wheels, spokes=8)
        out['tender'] = tuple(sorted((X(tu0), X(tu1)))) + (by - br + 2,)
    return out


def carriage(g: GB, x0, x1, rail_y, z, body='#1e3a2a', stripe='#c8b070', roof='#2a2c30', lit=0.9, seed=401,
             board=None, windows=10, people=True, warm='#ffc070', gangway=True):
    """A passenger carriage side: green body, a cream stripe, the roof with snow, lit compartment windows with
    curtains and the odd silhouette, two bogies, the destination board."""
    top = rail_y - 96
    bot = rail_y - 22
    bm = g.box(x0, top, x1, bot)
    g.put(bm, body, tex=tex_noise(g, 8, seed, 0.06), n=(0, 0.1, 1), z=z, gl=0.35)
    rf = g.poly([(x0 + 2, top), (x1 - 2, top), (x1 - 8, top - 10), (x0 + 8, top - 10)])
    g.put(rf, roof, n=(0, 0.8, 0.6), z=z + 1, gl=0.3)
    g.put(snow_on(rf, 3, seed + 1), '#dfe6ee', n=(0, 0.9, 0.4), z=z + 1)
    g.put(g.box(x0, top + 54, x1, top + 57), stripe, z=z - 0.2)
    ww = (x1 - x0 - 40) / windows
    for k in range(windows):
        wx0 = x0 + 20 + k * ww + 3
        wx1 = wx0 + ww - 8
        on = lit > 0 and K.hash2(k, 2, seed) > 0.12
        K.window(g, wx0, top + 16, wx1, top + 46, lit=lit * (0.8 + 0.4 * K.hash2(k, 3, seed)) if on else 0.0,
                 seed=seed + k, frame='#14241a', z=z - 0.3, mullion=False, sill_snow=False,
                 curtain='#7a2a22' if K.hash2(k, 4, seed) > 0.4 else None,
                 figure=(0.5, 18) if people and on and K.hash2(k, 5, seed) > 0.55 else None, warm=warm)
    if board:
        bw_ = K.VK.vtext(board, 's').shape[1] + 8
        bx = (x0 + x1) // 2 - bw_ // 2
        bdm = g.box(bx, top + 4, bx + bw_, top + 12)
        g.put(bdm, '#e8e2d0', z=z - 0.5)
        g.put(g.text(board, bx + 4, top + 5, 's') & bdm, '#1a1a1e', z=z - 0.6)
    for bx in (x0 + 34, x1 - 34):
        g.put(g.box(bx - 22, bot, bx + 22, rail_y - 6), '#141416', z=z + 1)
        for wx in (bx - 13, bx + 13):
            g.put(g.ell(wx, rail_y - 7, 6.5, 6.5), '#1e2024', z=z + 0.5, gl=0.6)
            g.put(g.ell(wx, rail_y - 7, 2, 2), '#3a3e44', z=z + 0.4, gl=0.8)
    if gangway:
        for gx in (x0 - 4, x1):
            g.put(g.box(gx, top + 10, gx + 4, bot - 4), '#101010', z=z + 0.5)
    return top, bot


def jet_sheet(n=12, w=120, h=240, seed=501, cols=('#3a4048', '#6a7280', '#9aa2ae', '#c8ccd2', '#e8eaee', '#fafbfc'),
              lean=0.25):
    """The safety valve's jet (the shared object of LS_C4P2_Steam's match cut): a white column shooting up from
    the bottom centre, widening and tearing into eddies that travel up the frames (a seamless n-frame loop).
    RGBA sheet n*w x h, base at (w/2, h-1)."""
    out = np.zeros((h, w * n, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (h - 1 - yy) / h                                     # 0 at the valve, 1 at the top
    P = np.stack([K.hx(c) for c in cols])
    for i in range(n):
        ph = i / n
        cx = w / 2 + lean * v * w * 0.5
        half = 2.0 + v * w * 0.42 + v * v * 10
        d = np.abs(xx - cx) / half
        # eddies: noise scrolled upward by a whole period over the loop
        nz = K.noise(w, h * 2, 9, seed, 3)
        nz2 = K.noise(w, h * 2, 4, seed + 1, 2)
        off = int(round(ph * h))
        a = nz[h - off: 2 * h - off] if off > 0 else nz[h:2 * h]
        b = nz2[h - off: 2 * h - off] if off > 0 else nz2[h:2 * h]
        dens = np.clip(1.15 - d, 0, 1) ** 0.9 * (0.55 + 0.6 * a + 0.25 * b) * np.clip(1.25 - v, 0, 1)
        core = np.clip(1 - d * 2.2, 0, 1) * np.clip(1 - v * 1.6, 0, 1)
        dens = np.maximum(dens, core)
        th = pg.bayer(w, h, i, i * 3)
        m = (dens > 0.18 + th * 0.35)
        lit = np.clip(dens * 0.9 + core * 0.5 + (b - 0.5) * 0.3 + (cx - xx) / half * 0.12, 0, 0.999)
        idx = (lit * len(cols)).astype(int)
        cell = np.zeros((h, w, 4), np.uint8)
        cell[..., :3] = np.round(P[idx] * 255).astype(np.uint8)
        cell[..., 3] = np.where(m, 255, 0)
        out[:, i * w:(i + 1) * w] = cell
    return out
