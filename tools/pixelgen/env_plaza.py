"""env_plaza -- the plaza before the Great Hall during the parade (L_M1_Plaza), evening, snow, palette 'berlin'.

Run:  py -3 -P tools/pixelgen/env_plaza.py [--preview=DIR]
Writes assets/environments/hall_plaza/ (layers + _n/_e maps, _hist twins, props, decals, actor sheets, fx)
and its scene.json (TECHNICAL_ARCHITECTURE 3.1 / 12.2).  Area: plaza-env.  Deterministic, no downloads.
scene.json is merged over the previous one (round 11, tools/pixelgen/env_keep.py): keys and "actors" other
writers add stay in place; unchanged content leaves the file byte for byte (LF).

Planes (world 1920x360, oblique 2.5D like Karsk):
  sky   p0.12  overcast dusk, cloud base lit by the searchlights      beams fx p0.12 (Lichtdom, 12 frames)
  hall  p0.12  the Great Hall: block with pilasters + banners, portico eagle, drum, patina dome, lantern with
               the eagle above the globe (consistent with the 3D hall)                       (+ hall_hist)
  far_plaza p0.45  tribune with banners and officials, standing formations, flag masts       (+ _hist)
  ground p1    avenue setts, guard strip, trampled crowd strip, pavement, kerb, street with tram rails
  [actor PlazaParade z-15: marching blocks, standard bearers, tanks]
  plaza_mid p1 guards facing the crowd + striped barrier + flood masts (z -14)
  street_back p1  tenements with the sealed door (left), fire wall of the cleared block (right)
  playfield: crowd strips (animated decals), props, banner, vendor, photographer, children, tank, rubble
  fg p1.25  dark snow mounds at the bottom edge
Insignia only through `_hist` twins resolved by Symbols.pick (neutral: Reichssiegel / plain eagle).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
from pg import Layer  # noqa: E402
import env_berlin_insignia as INS  # noqa: E402
import env_berlin_kit as kit  # noqa: E402
import env_plaza_sprites as SP  # noqa: E402
import env_keep as KEEP  # noqa: E402  (round 11: the folder is shared)
from env_plaza_sprites import N, V, S, O, G, T, PA, W, RED, COLD, STONE_D, PATR, save, save_color, \
    strip, edges, tfill, put, disc, emit  # noqa: E402

ENV = SP.ENV
WW = 1920
AX = 402            # hall axis (hall layer px, parallax 0.12) -> centred on screen when the player is at x 1000
TX = 626            # tribune axis (far_plaza layer px, parallax 0.45)
DB = 129            # dome base row
SKY = [N[0], N[1], N[2], N[3], V[1], V[2], V[3], W[0], W[1]]
BEAMS = sorted(AX + s * d for d in (40, 96, 152, 214, 280, 352) for s in (-1, 1))
BAY = pg.BAYER4


def beam_angle(i, bx, f=0, frames=12):
    return (bx - AX) / AX * 0.11 + 0.028 * math.sin(2 * math.pi * f / frames + i * 1.7)


# =========================================================================== sky + beams
def paint_sky() -> Layer:
    w, h = 800, 360
    L = Layer(w, h, 'sky')
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    t = 0.06 + 0.6 * np.clip(y / 215.0, 0, 1) ** 1.25
    n1 = pg.value_noise(w, 92, 22, seed=7, octaves=3)
    cloud = np.repeat(n1, 4, axis=0)[:h]
    t = t + (cloud - 0.5) * 0.26 * np.clip(1.25 - y / 190, 0.25, 1)
    for i, bx in enumerate(BEAMS):
        xt = bx + 175 * math.tan(beam_angle(i, bx))
        t = t + 0.2 * np.exp(-((x - xt) / 20.0) ** 2 - ((y - 34) / 13.0) ** 2)
    tfill(L, 0, 0, np.clip(t, 0, 1), SKY)
    th = pg.bayer(w, h)
    glow = (y > 160) & (y < 208) & (th < 0.45 * np.clip((420 - x) / 420, 0, 1) * np.sin((y - 160) / 48 * np.pi))
    L.c[glow & (L.c[..., 0] > 60)] = S[1]
    return L


def paint_beams(frames=12) -> Layer:
    out = []
    for f in range(frames):
        L = Layer(800, 210, 'beams')
        for i, bx in enumerate(BEAMS):
            tn = math.tan(beam_angle(i, bx, f, frames))
            for yy in range(28, 206):
                d = 205 - yy
                xc = bx + d * tn
                wd = 1.4 + d / 177 * 6.5
                d0 = 0.9 - 0.5 * d / 177
                for xx in range(int(xc - wd), int(xc + wd) + 1):
                    e = 1 - abs(xx + 0.5 - xc) / wd
                    if e <= 0 or not 0 <= xx < 800:
                        continue
                    dens = d0 * e ** 0.6 * (min(1.0, (yy - 28) / 14.0))
                    if dens > BAY[yy % 4, xx % 4]:
                        L.c[yy, xx] = W[3] if dens > 0.62 else (W[2] if dens > 0.4 else W[1])
        out.append(L)
    return strip(out)


# =========================================================================== the Great Hall
def eagle(L, cx, bottom, w, hist, body, lines, lit):
    em = INS.eagle_masks(w, wreath=hist, swastika=hist)
    h, ww = em['size']
    x0, y0 = int(cx - ww // 2), int(bottom - h)
    put(L, em['body'], x0, y0, body, 0.8)
    put(L, em['lines'], x0, y0, lines, 0.75)
    if hist:
        put(L, em['wreath'], x0, y0, lines, 0.8)
        put(L, em['swastika'], x0, y0, body, 0.8)
    sub = np.zeros((L.h, L.w), bool)
    ys, xs = np.nonzero(em['all'])
    ys, xs = ys + y0, xs + x0
    ok = (ys >= 0) & (ys < L.h) & (xs >= 0) & (xs < L.w)
    sub[ys[ok], xs[ok]] = True
    bt = edges(sub)[1]
    L.c[bt] = lit
    return h


def hall_banner(L, x, y, w, h, hist):
    for i in range(w):
        col = (RED[1] if i in (0, w - 1) else RED[2]) if hist else (T[0] if i in (0, w - 1) else T[1])
        L.rect(x + i, y, 1, h - (1 if i % 2 else 0), col, 0.55)
    cx, cy = x + w // 2, y + 8
    if hist:
        disc(L, cx + 0.5, cy + 0.5, w / 2.0 - 0.2, W[3], 0.6)
        sw = INS.swastika_mask(5)
        put(L, sw, cx - 2, cy - 2, N[0], 0.6)
    else:
        dm, pil = kit.reichssiegel_mask(w)
        put(L, dm, cx - w // 2, cy - w // 2, N[0], 0.6)
        put(L, pil, cx - w // 2, cy - w // 2, W[3], 0.6)
    L.rect(x - 1, y - 1, w + 2, 1, T[1], 0.6)


def paint_hall(hist) -> Layer:
    L = Layer(800, 215, 'hall')
    bx0, bx1, by0 = AX - 170, AX + 170, DB + 27
    yy = np.arange(by0, 215, dtype=np.float32)[:, None] + np.zeros((1, bx1 - bx0))
    t = 0.12 + 0.66 * ((yy - by0) / (215 - by0)) ** 1.1
    tfill(L, bx0, by0, t, STONE_D, hgt=0.4)
    pil = [p for p in range(bx0 + 4, bx1 - 6, 12) if not (AX - 66 < p < AX + 60)]
    for p in pil:
        sub = t[:, :5] + np.array([0.16, 0.22, 0.14, 0.04, -0.16])[None, :]
        tfill(L, p, by0, sub, STONE_D, hgt=0.7)
        L.rect(p - 1, by0 + 3, 7, 2, S[2], 0.75)
        L.rect(p - 1, by0 + 3, 7, 1, S[3], 0.75)
    left = [p for p in pil if p < AX][-4:]
    right = [p for p in pil if p > AX][:4]
    for p in left + right:
        hall_banner(L, p + 5 if p < AX else p - 7, by0 + 9, 7, 38, hist)
    # cornice, attic, drum
    L.rect(bx0 - 3, by0 - 4, 346, 1, W[3], 0.8)
    L.rect(bx0 - 3, by0 - 3, 346, 2, S[3], 0.75)
    L.rect(bx0 - 3, by0 - 1, 346, 1, N[3], 0.6)
    L.rect(AX - 150, DB + 12, 301, 11, S[0], 0.5)
    L.rect(AX - 150, DB + 12, 301, 1, W[2], 0.6)
    L.rect(AX - 150, DB + 17, 301, 1, V[1], 0.5)
    L.rect(AX - 128, DB, 257, 12, N[2], 0.4)
    for c in range(AX - 127, AX + 127, 5):
        L.rect(c, DB + 1, 2, 11, S[2], 0.6)
        L.rect(c, DB + 7, 2, 5, S[3], 0.6)
    L.rect(AX - 129, DB, 259, 1, S[3], 0.7)
    L.rect(AX - 129, DB - 1, 259, 1, W[2], 0.7)
    # dome
    rx, ry = 132.0, 90.0
    m, mx, my = L.ellipse_mask(AX, DB, rx, ry)
    rows = np.arange(m.shape[0])[:, None] + my
    m &= rows < DB - 1
    yy_, xx_ = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    v = np.clip((DB - (yy_ + my + 0.5)) / ry, 0, 1)
    u = (xx_ + mx + 0.5 - AX) / rx
    td = 0.16 + 0.55 * (1 - v) ** 2.4 + 0.1 * np.clip(-u, 0, 1) * v + 0.06 * (1 - np.abs(u))
    L.tone_fill(m, mx, my, np.clip(td, 0, 1), PATR, hgt=None)
    L.dome_height(AX, DB, rx, ry, amp=1.0)
    for s_ in np.linspace(-0.92, 0.92, 15):
        for yv in range(int(DB - ry) + 2, DB - 1):
            vv = (DB - yv) / ry
            xv = int(round(AX + s_ * rx * math.sqrt(max(0.0, 1 - vv * vv))))
            if 0 <= yv - my < m.shape[0] and 0 <= xv - mx < m.shape[1] and m[yv - my, xv - mx]:
                L.px(xv, yv, N[1] if vv > 0.45 else PA[0])
    for k_, vr in enumerate((0.3, 0.55, 0.77)):
        yr = int(round(DB - vr * ry))
        half = rx * math.sqrt(1 - vr * vr)
        for xv in range(int(AX - half) + 2, int(AX + half) - 1):
            L.px(xv, yr, PA[3] if xv % 2 else PA[2])
            if (xv * 7 + k_) % 5 == 0:
                L.px(xv, yr - 1, W[1])
    tp = edges(L.alpha() & (np.arange(L.h)[:, None] < DB - 1))[0]
    L.c[tp & (np.arange(L.w)[None, :] > AX - rx - 1) & (np.arange(L.w)[None, :] < AX + rx + 1)] = PA[2]
    # lantern, globe, eagle above the globe (plain eagle in both modes: Speer's 1939 lantern figure)
    top = int(DB - ry)
    L.rect(AX - 10, top - 16, 21, 17, N[1], 0.7)
    for c in range(AX - 9, AX + 10, 4):
        L.rect(c, top - 15, 2, 15, S[2], 0.75)
        L.rect(c, top - 6, 2, 6, S[3], 0.75)
    L.rect(AX - 12, top - 18, 25, 3, PA[1], 0.85)
    L.rect(AX - 12, top - 19, 25, 1, W[2], 0.85)
    L.rect(AX - 11, top, 23, 1, S[2], 0.7)
    gy = top - 25
    disc(L, AX + 0.5, gy + 0.5, 6.2, PA[1], 0.9)
    L.ellipse(AX + 0.5, gy + 2.5, 5.2, 3.2, PA[2], 0.9)
    L.vline(AX, gy - 5, 11, N[1])
    L.hline(AX - 5, gy, 11, PA[0])
    L.px(AX - 13, top - 18, O[4], em=emit(O[4]))
    L.px(AX + 12, top - 18, O[4], em=emit(O[4]))
    eagle(L, AX + 0.5, gy - 5, 18, False, PA[1], N[1], PA[3])
    # portico: projecting centre with nine piers, the state eagle on the entablature (insignia site)
    px0 = AX - 62
    L.rect(px0, by0 - 8, 125, 215 - by0 + 8, N[2], 0.4)
    for i in range(9):
        x = px0 + i * 14 + 2
        tp_ = np.linspace(0.34, 0.85, 215 - by0 - 4)[:, None] + np.array([0.08, 0.12, 0.06, 0.0, -0.06, -0.14])[None, :]
        tfill(L, x, by0 + 4, tp_, STONE_D, hgt=0.8)
    L.rect(px0 - 2, by0 - 8, 129, 12, S[2], 0.7)
    L.rect(px0 - 2, by0 - 8, 129, 1, W[3], 0.75)
    L.rect(px0 - 2, by0 - 2, 129, 2, S[3], 0.75)
    L.rect(px0 - 2, by0 + 3, 129, 1, N[3], 0.6)
    for i in range(8):
        L.rect(px0 + i * 14 + 9, by0 + 30, 4, 215 - by0 - 30, S[0], 0.45)
    eagle(L, AX + 0.5, by0 - 8, 46, hist, N[2], N[0], T[4])
    return L


# =========================================================================== far plaza (tribune, formations)
def tiny_soldier(L, x, base, h=7, rim=T[3]):
    L.rect(x, base - h, 3, 2, T[1])
    L.px(x + 1, base - h, rim)
    L.px(x + 1, base - h + 2, S[1])
    L.rect(x, base - h + 3, 3, h - 4, T[0])
    L.px(x + 1, base - 1, N[1])


def paint_far_plaza(hist) -> Layer:
    L = Layer(1220, 110, 'far_plaza')
    yy = np.arange(76, 110, dtype=np.float32)[:, None] + np.zeros((1, 1220))
    n = pg.value_noise(1220, 34, 9, seed=3, octaves=2)
    tfill(L, 0, 76, np.clip(0.58 + 0.08 * (n - 0.5) + 0.04 * (yy - 76) / 34, 0, 1), COLD, hgt=0.2)
    rng = np.random.default_rng(12)
    # flag masts across the plaza
    for x in range(40, 1200, 108):
        if abs(x - TX) < 130:
            continue
        L.rect(x, 12, 1, 76, T[3], 0.6)
        L.rect(x - 4, 14, 9, 1, T[2], 0.6)
        for i in range(7):
            col = (RED[2] if i not in (0, 6) else RED[1]) if hist else (T[1] if i not in (0, 6) else T[0])
            L.rect(x - 3 + i, 15, 1, 15 + (i % 2), col, 0.6)
        if hist:
            L.rect(x - 1, 19, 3, 3, W[3])
            L.px(x, 20, N[0])
        else:
            L.rect(x - 1, 19, 3, 3, N[0])
            L.px(x, 20, W[3])
    # standing formations: blocks of tiny helmets, rows 2 px apart, an officer in front of each block
    for side in (-1, 1):
        x0, x1 = (12, TX - 112) if side < 0 else (TX + 112, 1208)
        bx = x0
        while bx + 30 < x1:
            for r in range(10):
                base = 80 + r * 2
                for c in range(bx + (r % 2), bx + 34, 3):
                    tiny_soldier(L, c, base, rim=T[3] if r < 9 else T[4])
            tiny_soldier(L, bx + 15, 103, h=9, rim=W[2])
            bx += 44
    # tribune
    L.rect(TX - 46, 34, 93, 28, S[0], 0.5)
    L.rect(TX - 46, 34, 93, 1, W[3], 0.6)
    for i, bxx in enumerate((TX - 34, TX - 4, TX + 26)):
        w = 9
        for j in range(w):
            col = (RED[1] if j in (0, w - 1) else RED[2]) if hist else (T[0] if j in (0, w - 1) else T[1])
            L.rect(bxx + j, 37, 1, 22 - (j % 2), col, 0.55)
        cx_, cy_ = bxx + 4, 44
        if hist:
            disc(L, cx_ + 0.5, cy_ + 0.5, 3.7, W[3])
            put(L, INS.swastika_mask(5), cx_ - 2, cy_ - 2, N[0])
        else:
            dm, pil = kit.reichssiegel_mask(7)
            put(L, dm, cx_ - 3, cy_ - 3, N[0])
            put(L, pil, cx_ - 3, cy_ - 3, W[3])
    pl = np.linspace(0.55, 0.8, 22)[:, None] + np.zeros((1, 141))
    tfill(L, TX - 70, 62, pl, STONE_D, hgt=0.6)
    L.rect(TX - 70, 62, 141, 1, W[3], 0.7)
    for x in range(TX - 66, TX + 70, 10):
        L.rect(x, 63, 1, 21, S[1], 0.6)
    for y in range(64, 84, 2):
        L.rect(TX - 12, y, 25, 1, S[4] if y % 4 else S[2], 0.65)
    L.rect(TX - 3, 55, 7, 7, S[1], 0.7)
    for i, x in enumerate(range(TX - 40, TX + 41, 10)):
        if abs(x - TX) < 4:
            continue
        L.rect(x, 54, 3, 8, (N[1], N[2], T[0])[i % 3])
        L.rect(x, 53, 3, 1, T[3])
    L.rect(TX - 1, 51, 3, 4, N[1])
    for fx_ in (TX - 75, TX + 74):
        L.rect(fx_, 50, 2, 34, T[1], 0.6)
        L.rect(fx_ - 2, 46, 6, 4, T[2], 0.7)
        L.rect(fx_ - 1, 47, 4, 2, W[4], 0.9, em=emit(W[4]))
    return L


# =========================================================================== ground (avenue, pavement, street)
def paint_ground() -> Layer:
    """avenue (188..226), guard strip (226..242), crowd strip (242..271), pavement (271..318), kerb, street"""
    H0 = 182
    Hh = 360 - H0
    L = Layer(WW, Hh, 'ground')
    yw = np.arange(H0, 360)[:, None] + np.zeros((1, WW), int)
    xw = np.arange(WW)[None, :] + np.zeros((Hh, 1), int)
    n = pg.value_noise(WW, Hh, 11, seed=21, octaves=3)
    n2 = pg.value_noise(WW, Hh, 3, seed=22, octaves=1)
    t = np.zeros((Hh, WW), np.float32)
    av = (yw >= 188) & (yw < 226)
    joint = (yw % 2 == 0) | (((xw + (yw // 2 % 2) * 2) % 5) == 0)
    flood = sum(np.exp(-((xw - fx) / 170.0) ** 2) for fx in (700, 1000, 1310, 1650))
    tav = 0.36 + 0.1 * flood + 0.06 * (n - 0.5)
    outer = (yw < 193) | (yw > 221)
    tav = np.where(joint, np.where(outer, 0.58, 0.28), tav)
    wet = (yw >= 202) & (yw <= 222) & (n2 > 0.7) & ~joint
    tav = np.where(wet, tav + 0.16 * flood, tav)
    t = np.where(av, tav, t)
    t = np.where((yw >= 184) & (yw < 188), 0.62, t)
    t = np.where((yw >= 226) & (yw < 242), 0.56 + 0.06 * (n2 - 0.5) - 0.08 * (n > 0.62), t)
    t = np.where((yw >= 242) & (yw < 271), 0.3 + 0.08 * (n - 0.5) + 0.04 * (n2 > 0.75), t)
    # pavement: snow (W0) with a trampled walking band (V2/V3) where the slab joints show
    pv = (yw >= 271) & (yw < 318)
    band = np.exp(-((yw - 296 - 6 * (n - 0.5)) / 9.0) ** 2)
    slab_j = ((yw - 271) % 8 == 0) | (((xw + ((yw - 271) // 8 % 2) * 9) % 18) == 0)
    tpv = 0.54 + 0.05 * (n - 0.5) - 0.13 * band - np.where(slab_j, 0.05 + 0.05 * band, 0.0)
    tpv = np.where((yw < 276) | (yw > 313), tpv + 0.04, tpv)
    t = np.where(pv, tpv, t)
    # street: dark packed snow, ruts along the rails, wet patches
    st = yw >= 322
    rut = (np.abs(yw - 333) <= 1) | (np.abs(yw - 343) <= 1)
    tst = 0.4 + 0.06 * (n - 0.5) - np.where(rut, 0.14, 0.0) - np.where(n2 > 0.78, 0.1, 0.0)
    t = np.where(st, tst, t)
    lot = (xw > 1544) & (yw >= 222) & (yw < 271)
    t = np.where(lot, 0.5 + 0.12 * (n - 0.5) - 0.1 * (n2 > 0.75), t)
    tfill(L, 0, 0, np.clip(t, 0, 1), COLD, hgt=np.where(yw < 322, 0.3, 0.2).astype(np.float32))
    for y_, col in ((318, W[2]), (319, T[3]), (320, T[2]), (321, N[2])):
        L.rect(0, y_ - H0, WW, 1, col, 0.6)
    for ry in (332, 342):
        L.rect(0, ry - H0, WW, 1, T[3], 0.55)
        L.rect(0, ry + 1 - H0, WW, 1, N[1], 0.4)
        for x in range(0, WW, 7):
            if (x * 13) % 5 == 0:
                L.rect(x, ry - H0, 3, 1, W[1])
    rng = np.random.default_rng(31)
    for _ in range(220):
        x, y = int(rng.integers(1546, WW - 3)), int(rng.integers(226, 270))
        L.rect(x, y - H0, 2, 1, (O[1], S[1], V[2], N[3])[int(rng.integers(0, 4))], 0.5)
    for x in range(560, 1540, 3):
        if rng.random() < 0.5:
            L.px(x, 241 - H0 + int(rng.integers(0, 2)), V[2])
    for _ in range(140):                       # footprints in the walking band
        x = int(rng.integers(0, WW - 3))
        y = int(296 + rng.normal(0, 6))
        L.rect(x, y - H0, 2, 1, V[2])
        L.px(x + 3, y + 2 - H0, V[2])
    for kx in range(30, WW, 137):                  # shovelled snow ridges along the kerb
        w = int(rng.integers(18, 34))
        for x in range(kx, min(WW, kx + w)):
            h = int(3 * math.sin(math.pi * (x - kx) / w)) + 1
            L.rect(x, 317 - h - H0, 1, h, W[1], 0.6)
            L.px(x, 317 - h - H0, W[2])
    for mxh in (262, 884, 1452):                    # manhole covers in the street
        L.ellipse(mxh, 349 - H0, 7, 2.2, N[2], 0.4)
        L.ellipse(mxh, 349 - H0, 5, 1.4, V[1], 0.4)
    th = pg.bayer(WW, Hh)
    for lx, y0, y1, wdt in ((58, 324, 352, 4), (1618, 324, 352, 4), (1284, 284, 316, 7), (1700, 272, 296, 5)):
        for y in range(y0, y1):
            for x in range(lx - wdt, lx + wdt + 1):
                pdist = 1 - abs(x - lx) / (wdt + 1) - 0.6 * (y - y0) / (y1 - y0)
                if pdist > th[y - H0, x] + 0.3 and y % 2 == 0:
                    col = O[3] if pdist > 0.6 else O[2]
                    L.px(x, y - H0, col, em=emit(col, 120))
    return L

def paint_plaza_mid() -> Layer:
    H0 = 104
    L = Layer(WW, 140, 'plaza_mid')
    masts = (700, 1000, 1310)
    for mx_ in masts:
        L.rect(mx_ - 1, 124 - H0, 3, 112, T[1], 0.6)
        L.vline(mx_ - 1, 124 - H0, 112, T[3], 0.62)
        for y in range(128, 234, 6):
            L.px(mx_ + 1, y - H0, N[2])
        L.rect(mx_ - 7, 118 - H0, 15, 2, T[1], 0.7)
        for hx_ in (mx_ - 6, mx_ + 3):
            L.rect(hx_, 112 - H0, 4, 6, T[2], 0.75)
            L.rect(hx_, 116 - H0, 4, 2, W[4], 0.9, em=emit(W[4]))
        L.rect(mx_ - 4, 138 - H0, 3, 4, T[2], 0.7)
        L.rect(mx_ - 5, 139 - H0, 1, 2, N[1])
    g = SP.guard_front()
    gx = 566
    while gx < 1530:
        if all(abs(gx - m) > 14 for m in masts):
            L.blit(g, gx - g.w // 2, 232 - H0 - g.h + 1)
        gx += 46
    # trestle barrier, striped top rail, crossed legs
    for x in range(548, 1542):
        seg = ((x - 548) // 10) % 2
        L.rect(x, 226 - H0, 1, 2, W[3] if seg else N[2], 0.7)
        L.px(x, 225 - H0, W[4])
        L.rect(x, 233 - H0, 1, 2, S[1], 0.65)
    for lx in range(571, 1542, 46):
        L.line(lx - 4, 240 - H0, lx + 3, 224 - H0, S[0], 0.6)
        L.line(lx + 3, 240 - H0, lx - 4, 224 - H0, S[0], 0.6)
    L.rect(906, 228 - H0, 12, 7, W[3], 0.75)
    L.rect(907, 230 - H0, 10, 1, N[2])
    L.rect(907, 232 - H0, 7, 1, N[2])
    # chain line closing the cleared lot
    for px_ in range(1550, WW, 42):
        L.rect(px_, 228 - H0, 2, 12, T[1], 0.6)
        L.px(px_, 227 - H0, W[3])
        if px_ + 42 < WW + 40:
            pts = pg.catenary(px_ + 1, 230 - H0, px_ + 43, 230 - H0, 3, 0)
            L.polyline(pts, N[1])
    return L


# =========================================================================== tenements + fire wall
def window(L, x, y, lit=0, H0=90):
    y -= H0
    L.rect(x - 1, y - 3, 14, 1, S[3], 0.7)
    L.rect(x - 1, y - 2, 14, 1, S[1], 0.6)
    L.rect(x, y, 12, 22, S[2], 0.55)
    if lit:
        cols = [O[3], O[4], G[0], G[1]] if lit == 2 else [O[1], O[2], O[3], O[3]]
        g = np.linspace(0.85, 0.25, 20)[:, None] + np.zeros((1, 10))
        tfill(L, x + 1, y + 1, g, cols, hgt=0.3)
        L.em[y + 1:y + 21, x + 1:x + 11] = L.c[y + 1:y + 21, x + 1:x + 11]
        L.em[y + 1:y + 21, x + 1:x + 11, 3] = 200 if lit == 2 else 120
    else:
        L.rect(x + 1, y + 1, 10, 20, T[0], 0.3)
        L.px(x + 8, y + 2, T[2])
        L.px(x + 9, y + 3, T[2])
        L.px(x + 2, y + 12, T[1])
    L.vline(x + 6, y + 1, 20, S[1], 0.6)
    L.hline(x + 1, y + 8, 10, S[1], 0.6)
    L.rect(x - 1, y + 22, 14, 1, W[3], 0.7)
    L.rect(x - 1, y + 23, 14, 1, S[1], 0.6)


def paint_street_back() -> Layer:
    H0 = 90
    L = Layer(WW, 190, 'street_back')
    n = pg.value_noise(WW, 190, 7, seed=41, octaves=3)
    # side street mouth (x 0..36): the way back to the archive
    yy = np.arange(96, 277, dtype=np.float32)[:, None] + np.zeros((1, 36))
    tfill(L, 0, 96 - H0, np.clip(0.06 + 0.2 * (yy - 96) / 180, 0, 1), COLD)
    L.rect(4, 150 - H0, 26, 70, V[0], 0.3)
    for (wx, wy) in ((9, 168), (20, 190), (9, 204)):
        L.rect(wx, wy - H0, 3, 4, O[2], 0.4, em=emit(O[2], 140))
    L.rect(15, 236 - H0, 3, 4, G[2], 0.8, em=emit(G[2]))
    L.vline(16, 240 - H0, 30, N[2])
    L.rect(36, 96 - H0, 5, 180, S[0], 0.6)
    L.vline(36, 96 - H0, 180, S[1], 0.6)
    # facades x 41..548
    x0, x1 = 41, 548
    y_ = np.arange(140, 214, dtype=np.float32)[:, None] + np.zeros((1, x1 - x0))
    nn = n[140 - H0:214 - H0, x0:x1]
    tw = np.clip(0.22 + 0.3 * (y_ - 140) / 74 + 0.1 * (nn - 0.5), 0, 1)
    houseA = np.arange(x0, x1)[None, :] < 290
    FA = [N[1], N[3], V[1], V[2], V[3]]
    FB = [N[2], V[1], S[0], S[1], S[2]]
    tfill(L, x0, 140 - H0, tw, FA, mask=np.broadcast_to(houseA, tw.shape).copy(), hgt=0.5)
    tfill(L, x0, 140 - H0, tw, FB, mask=np.broadcast_to(~houseA, tw.shape).copy(), hgt=0.5)
    y_ = np.arange(214, 277, dtype=np.float32)[:, None] + np.zeros((1, x1 - x0))
    xr = np.arange(x0, x1)[None, :] + np.zeros((63, 1), int)
    rj = ((y_ - 214) % 7 == 0) | (((xr + ((y_ - 214) // 7 % 2).astype(int) * 7) % 14) == 0)
    tr = np.where(rj, 0.22, 0.36) + 0.06 * (n[214 - H0:277 - H0, x0:x1] - 0.5) + 0.1 * (y_ - 214) / 62
    tfill(L, x0, 214 - H0, np.clip(tr, 0, 1), STONE_D, hgt=0.55)
    L.rect(x0, 270 - H0, x1 - x0, 7, S[0], 0.5)
    L.rect(x0, 270 - H0, x1 - x0, 1, S[2], 0.55)
    L.rect(x0, 176 - H0, x1 - x0, 2, S[2], 0.6)
    L.rect(x0, 176 - H0, x1 - x0, 1, S[3], 0.62)
    L.rect(x0, 212 - H0, x1 - x0, 2, S[2], 0.6)
    L.rect(x0 - 2, 136 - H0, x1 - x0 + 4, 6, S[3], 0.7)
    L.rect(x0 - 2, 135 - H0, x1 - x0 + 4, 1, W[3], 0.75)
    L.rect(x0 - 2, 141 - H0, x1 - x0 + 4, 1, N[3], 0.6)
    # mansard + dormers + chimneys
    ym = np.arange(112, 135, dtype=np.float32)[:, None] + np.zeros((1, x1 - x0 + 2))
    nm = n[112 - H0:135 - H0, x0 - 1:x1 + 1]
    xm = np.arange(x0 - 1, x1 + 1)[None, :] + np.zeros_like(ym)
    snowrow = ((ym - 112) % 4 == 0) & (nm > 0.42) & (((xm * 7) // 5) % 6 != 0)
    tm = 0.2 + 0.14 * (ym - 112) / 23 + np.where(snowrow, 0.42, 0.0) + np.where(ym < 114, 0.62, 0.0)
    tfill(L, x0 - 1, 112 - H0, np.clip(tm, 0, 1), [N[3], V[1], V[2], V[3], W[1], W[2], W[3]], hgt=0.7)
    for i, dx in enumerate(range(70, 520, 76)):
        L.rect(dx, 116 - H0, 10, 12, S[1], 0.8)
        L.rect(dx + 2, 119 - H0, 6, 8, O[3] if i == 4 else T[0], 0.4, em=emit(O[3], 150) if i == 4 else None)
        L.poly([(dx - 1, 116 - H0), (dx + 10, 116 - H0), (dx + 5, 111 - H0)], S[1], 0.85)
        L.line(dx - 1, 116 - H0, dx + 5, 111 - H0, W[3])
        L.line(dx + 5, 111 - H0, dx + 10, 116 - H0, W[2])
    for cx_ in (100, 236, 420, 506):
        L.rect(cx_, 96 - H0, 7, 17, O[1], 0.8)
        L.vline(cx_, 96 - H0, 17, O[0], 0.8)
        L.rect(cx_ - 1, 95 - H0, 9, 2, N[2], 0.85)
        L.rect(cx_ - 1, 94 - H0, 9, 1, W[3], 0.85)
    L.rect(288, 136 - H0, 2, 134, N[2], 0.6)
    # windows (upper floors); the decal 'window_life' sits on floor 1 at x 238
    for fl_y in (148, 184):
        for i, wx in enumerate(range(58, 520, 30)):
            if fl_y == 184 and wx == 238:
                L.rect(wx - 1, fl_y - 3 - H0, 14, 1, S[3], 0.7)
                L.rect(wx - 1, fl_y + 22 - H0, 14, 1, W[3], 0.7)
                continue
            lit = 2 if (fl_y, wx) in ((148, 148), (184, 418)) else (1 if (fl_y, wx) == (148, 448) else 0)
            window(L, wx, fl_y, lit)
    # balcony on house A
    L.rect(110, 206 - H0, 36, 2, S[2], 0.7)
    for x in range(110, 146, 2):
        L.vline(x, 198 - H0, 8, N[1])
    L.rect(110, 197 - H0, 36, 1, W[3], 0.8)
    # ground floor: shop shutter, house door A, barred window, the SEALED door of the evicted family (B)
    L.rect(52, 216 - H0, 78, 7, S[0], 0.6)
    for x in range(56, 126, 4):
        L.px(x, 219 - H0, V[3])
    L.rect(52, 224 - H0, 78, 46, S[1], 0.5)
    for y in range(226, 270, 2):
        L.rect(54, y - H0, 74, 1, T[1] if y % 4 else T[2], 0.5)
    L.rect(148, 216 - H0, 22, 54, S[3], 0.6)
    L.rect(150, 218 - H0, 18, 8, N[2], 0.4)
    L.vline(159, 218 - H0, 8, T[2])
    L.rect(150, 227 - H0, 18, 43, S[0], 0.5)
    for (px_, py_) in ((152, 230), (160, 230), (152, 250), (160, 250)):
        L.rect(px_, py_ - H0, 6, 16, S[1], 0.55)
    L.rect(186, 228 - H0, 26, 30, T[0], 0.3)
    L.rect(185, 227 - H0, 28, 1, S[3])
    for x in range(188, 212, 3):
        L.vline(x, 228 - H0, 30, N[1])
    L.rect(185, 258 - H0, 28, 1, W[3])
    # B: sealed door with crossed boards and a paper seal strip
    L.rect(320, 216 - H0, 24, 54, S[3], 0.6)
    L.rect(322, 218 - H0, 20, 52, S[1], 0.5)
    for (px_, py_) in ((324, 222), (333, 222), (324, 246), (333, 246)):
        L.rect(px_, py_ - H0, 7, 20, S[2], 0.55)
    for k in range(3):
        L.line(320, 226 + k - H0, 344, 258 + k - H0, S[2] if k < 2 else S[0], 0.7)
        L.line(344, 226 + k - H0, 320, 258 + k - H0, S[3] if k < 2 else S[0], 0.72)
    L.line(321, 244 - H0, 343, 238 - H0, W[3], 0.75)
    L.rect(330, 239 - H0, 3, 3, RED[1], 0.75)
    L.rect(360, 228 - H0, 32, 30, S[0], 0.4)
    for y in range(229, 258, 5):
        L.rect(360, y - H0, 32, 4, S[1] if y % 2 else S[2], 0.6)
    L.rect(420, 222 - H0, 112, 48, N[2], 0.4)
    for i, x in enumerate(range(424, 528, 13)):
        L.rect(x, 228 - H0, 10, 14 + (i * 5) % 9, (S[4], W[2], S[3])[i % 3], 0.5)
    L.rect(418, 220 - H0, 116, 2, S[3], 0.6)
    L.rect(540, 96 + 40 - H0, 8, 140, S[2], 0.6)
    L.vline(547, 136 - H0, 140, T[3], 0.65)
    # fire wall of the demolished neighbour (x 1838..1920): ghost of the gable, floors, stairs, wallpaper
    fx0 = 1838
    for x in range(fx0, WW):
        top = int(144 - (x - fx0) * 0.42) + (2 if (x // 5) % 3 == 0 else 0)
        h = 272 - top
        col_t = np.clip(0.12 + 0.12 * np.linspace(0, 1, h) + 0.08 * (n[top - H0:272 - H0, x] - 0.5), 0, 1)[:, None]
        ghost = np.array([(yy > 150 + (x - fx0) * 0.0) and (yy > 186 - (x - fx0) * 0.6) for yy in range(top, 272)])
        col_t = col_t + 0.13 * ghost[:, None]
        tfill(L, x, top - H0, col_t, STONE_D, hgt=0.5)
        L.px(x, top - H0, W[3])
        L.px(x, top + 1 - H0, W[1])
    for yfl in (178, 216):
        L.rect(fx0 + 2, yfl - H0, WW - fx0 - 2, 1, N[3], 0.45)
    for (wx, wy, ww_, wh, c1, c2) in ((1846, 184, 26, 28, V[2], V[1]), (1882, 186, 30, 26, S[0], V[1]),
                                       (1852, 222, 34, 40, V[1], N[3])):
        for x in range(wx, wx + ww_):
            for y in range(wy, wy + wh):
                if (x * 3 + y) % 7 or (y - wy) < wh - 3:
                    L.px(x, y - H0, c1 if (x // 2) % 2 else c2, 0.5)
    for k in range(0, 52, 2):
        L.px(1846 + k, 268 - k - H0, N[3])
        L.px(1847 + k, 268 - k - H0, N[3])
    L.rect(1904, 124 - H0, 4, 146, N[3], 0.4)
    for y in range(130, 272, 3):
        L.px(fx0 + (y * 7) % 3, y - H0, 0 * W[0])           # ragged left edge of the fire wall
    return L


def paint_fg() -> Layer:
    L = Layer(2240, 40, 'fg')
    rng = np.random.default_rng(51)
    for cx in (70, 610, 1180, 1720, 2120):
        w = int(rng.integers(44, 70))
        for x in range(cx - w // 2, cx + w // 2):
            h = int(12 * math.sqrt(max(0.0, 1 - ((x - cx) / (w / 2)) ** 2))) + int(rng.integers(0, 2))
            if h > 0:
                L.rect(x, 40 - h, 1, h, N[1] if x % 9 else N[0])
                L.px(x, 40 - h, V[2])
    for bx in (880, 1460):
        L.rect(bx, 24, 5, 16, N[0])
        L.rect(bx, 23, 5, 1, V[3])
    return L


# =========================================================================== manifest
def build_manifest(sz) -> dict:
    def prop(name, file, pos, coll=None, emission=False, base=None):
        w, h = sz[name]
        P = {"name": name if name == file else file, "file": "props/%s.png" % file, "pos": pos,
             "base_y": base if base is not None else pos[1] + h - 1, "normal": True, "emission": emission}
        if coll:
            P["collision"] = coll
        return P

    def box(x0, y0, x1, y1):
        return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]

    crowd = [(548, 1), (718, 2), (818, 3), (936, 4), (1150, 5), (1318, 6), (1440, 7)]
    m = {
        "id": "hall_plaza", "palette": "berlin", "world_size": [WW, 360],
        "camera": {"bounds": [0, 0, WW, 360]},
        "canvas_modulate": "#BAB8C8",
        "layers": [
            {"name": "sky", "file": "sky.png", "pos": [0, 0], "parallax": [0.12, 0.0], "z": -100, "normal": False,
             "emission": False, "lit": False},
            {"name": "hall", "file": "hall.png", "pos": [0, 0], "parallax": [0.12, 0.0], "z": -90, "normal": True,
             "emission": True, "lit": True, "emission_strength": 0.6},
            {"name": "far_plaza", "file": "far_plaza.png", "pos": [0, 96], "parallax": [0.45, 0.0], "z": -80,
             "normal": True, "emission": True, "lit": True, "emission_strength": 0.6},
            {"name": "ground", "file": "ground.png", "pos": [0, 182], "parallax": [1.0, 1.0], "z": -16,
             "normal": True, "emission": True, "lit": True, "emission_strength": 0.3},
            {"name": "plaza_mid", "file": "plaza_mid.png", "pos": [0, 104], "parallax": [1.0, 1.0], "z": -14,
             "normal": True, "emission": True, "lit": True, "emission_strength": 0.7},
            {"name": "street_back", "file": "street_back.png", "pos": [0, 90], "parallax": [1.0, 1.0], "z": -13,
             "normal": True, "emission": True, "lit": True, "emission_strength": 0.45},
            {"name": "fg_frame", "file": "fg_frame.png", "pos": [0, 320], "parallax": [1.25, 1.0], "z": 60,
             "normal": False, "emission": False, "lit": False},
        ],
        "decals": [
            {"name": "window_life", "file": "props/window_life.png", "pos": [238, 184], "layer": "street_back",
             "frames": 8, "fps": 1.2, "emission": True, "emission_strength": 0.5, "lit": True},
            {"name": "notice_door", "file": "props/notice_door.png", "pos": [326, 227], "layer": "street_back",
             "lit": True},
            {"name": "banner_near", "file": "props/banner_near.png", "pos": [1119, 104], "layer": "playfield",
             "base_y": 271, "frames": 6, "fps": 4, "lit": True},
        ] + [{"name": "crowd_%d" % i, "file": "props/crowd_%d.png" % i, "pos": [x, 215], "layer": "playfield",
              "base_y": 266, "frames": 4, "fps": 2, "lit": True} for x, i in crowd],
        "props": [
            prop('lamp_post', 'lamp_post', [52, 226], box(54, 315, 62, 320), True),
            dict(prop('lamp_post', 'lamp_post', [1612, 226], box(1614, 315, 1622, 320), True), name="lamp_post_2"),
            prop('tram_stop', 'tram_stop', [152, 252], box(158, 315, 162, 320)),
            prop('litfass', 'litfass', [440, 238], box(441, 293, 461, 300)),
            prop('loudspeaker', 'loudspeaker', [580, 150]),
            prop('children', 'children', [674, 232], box(675, 268, 703, 277)),
            prop('banner_mast', 'banner_mast', [1116, 96], box(1126, 266, 1136, 272), base=270),
            prop('vendor', 'vendor', [1262, 232], box(1264, 272, 1302, 280), True),
            prop('photographer', 'photographer', [1408, 214], box(1410, 272, 1430, 278)),
            prop('tank_parked', 'tank_parked', [1556, 218]),
            prop('barrel_guard', 'barrel_guard', [1690, 222], None, True),
            prop('rubble_a', 'rubble_a', [1726, 258], box(1730, 280, 1786, 288)),
            prop('rubble_b', 'rubble_b', [1836, 264], box(1840, 282, 1884, 288)),
        ],
        "walkable": [[0, 276], [540, 276], [552, 270], [WW, 270], [WW, 352], [0, 352]],
        "spawns": {"SP_Plaza_Start": [64, 300]},
        "hotspots": {
            "exit_archive": [16, 300], "exp_pz_tram_stop": [174, 306], "exp_pz_window": [244, 286],
            "exp_pz_family_door": [332, 286], "exp_pz_poster": [452, 312], "exp_pz_loudspeaker": [604, 288],
            "exp_pz_children": [690, 294], "exp_pz_guard": [800, 282], "exp_pz_barrier": [912, 282],
            "exp_pz_tribune": [1000, 290], "exp_pz_banner": [1132, 290], "exp_pz_vendor": [1284, 296],
            "exp_pz_photographer": [1420, 292], "exp_pz_tank": [1598, 284], "exp_pz_rubble": [1760, 302]},
        "hotspot_info": {
            "exit_archive": {"mark": [18, 228], "what": "mouth of the side street back to the archive (lamp, far lit windows)"},
            "exp_pz_tram_stop": {"mark": [160, 250], "what": "tram stop sign 'H' with timetable case, pasted-over strip (traffic suspended)"},
            "exp_pz_window": {"mark": [244, 180], "what": "lit window above the sealed flat: a woman behind the lace curtain leans to look down (decal window_life)"},
            "exp_pz_family_door": {"mark": [332, 214], "what": "sealed front door of the evicted family: crossed boards, paper seal strip with red wax, official notice (decal notice_door, stamp = insignia site)"},
            "exp_pz_poster": {"mark": [451, 234], "what": "advertising column: state poster (eagle / Reichssiegel), ration notice, torn posters"},
            "exp_pz_loudspeaker": {"mark": [600, 148], "what": "loudspeaker pole with three horns over the crowd, junction box, cables"},
            "exp_pz_children": {"mark": [690, 230], "what": "two children on a crate behind the crowd, one with a limp paper flag (insignia site)"},
            "exp_pz_guard": {"mark": [796, 186], "what": "guard behind the barrier facing the crowd, helmet shadow over the eyes, rifle at order arms"},
            "exp_pz_barrier": {"mark": [912, 220], "what": "striped trestle barrier with a small white sign board"},
            "exp_pz_tribune": {"mark": {"mark": [TX, 146], "layer": "far_plaza"}, "layer": "far_plaza", "what": "tribune before the hall: banners, a row of officials, a speaker at the lectern, floodlights; the Great Hall and the portico eagle above (layer hall)"},
            "exp_pz_banner": {"mark": [1131, 100], "what": "tall mast with a long state banner (decal banner_near, insignia site)"},
            "exp_pz_vendor": {"mark": [1286, 228], "what": "chestnut vendor's handcart with a glowing brazier, old man warming his hands (warm focal light)"},
            "exp_pz_photographer": {"mark": [1420, 210], "what": "press photographer on a stepladder with flash reflector (actor PlazaFlash fires every 8-14 s)"},
            "exp_pz_tank": {"mark": [1598, 214], "what": "parked tank in the cleared lot, snow on the hull; crewman at a fire barrel"},
            "exp_pz_rubble": {"mark": [1760, 254], "what": "rubble of the cleared block; the remaining fire wall shows the ghost of stairs, floors and wallpaper"},
        },
        "lights": [
            {"id": "lamp_archive_street", "pos": [58, 238], "color": "#F4BA81", "energy": 1.0, "radius": 120,
             "flicker": 0.03, "height": 30, "on_layer": "playfield"},
            {"id": "lamp_lot", "pos": [1618, 238], "color": "#F4BA81", "energy": 0.7, "radius": 100,
             "flicker": 0.03, "height": 30, "on_layer": "playfield"},
            {"id": "window_neighbours", "pos": [244, 196], "color": "#F0AE6E", "energy": 0.6, "radius": 56,
             "flicker": 0.02, "height": 20, "on_layer": "playfield"},
            {"id": "vendor_brazier", "pos": [1276, 244], "color": "#F0AE6E", "energy": 1.3, "radius": 104,
             "flicker": 0.18, "height": 18, "on_layer": "playfield"},
            {"id": "lot_fire_barrel", "pos": [1698, 250], "color": "#E5945A", "energy": 1.1, "radius": 92,
             "flicker": 0.2, "height": 18, "on_layer": "playfield"},
            {"id": "flood_1", "pos": [700, 118], "color": "#A3ACB4", "energy": 0.85, "radius": 150, "flicker": 0.0,
             "height": 60, "on_layer": "playfield"},
            {"id": "flood_2", "pos": [1000, 118], "color": "#A3ACB4", "energy": 0.85, "radius": 150,
             "flicker": 0.0, "height": 60, "on_layer": "playfield"},
            {"id": "flood_3", "pos": [1310, 118], "color": "#A3ACB4", "energy": 0.85, "radius": 150,
             "flicker": 0.0, "height": 60, "on_layer": "playfield"},
            {"id": "tribune_floods", "pos": [TX, 146], "color": "#D2CCCB", "energy": 0.8, "radius": 110,
             "flicker": 0.0, "height": 30, "on_layer": "far_plaza"},
        ],
        "fx": [
            {"type": "snow", "density": 0.6, "wind": 7.0, "color_far": "#8F8A92", "color_near": "#D2CCCB"},
            {"type": "anim_sprite", "file": "fx/beams.png", "frames": 12, "fps": 3, "pos": [0, 0],
             "parallax": [0.12, 0.0], "z": -95, "alpha": 0.5},
            {"type": "fog_band", "y": 180, "height": 40, "color": "#6E6A73", "alpha": 0.32, "parallax": 0.3,
             "z": -85, "seed": 5},
            {"type": "fog_band", "y": 198, "height": 22, "color": "#8F8A92", "alpha": 0.2, "parallax": 0.7,
             "z": -60, "seed": 6},
        ] + [{"type": "anim_sprite", "file": "fx/smoke.png", "frames": 8, "fps": 5, "pos": [cx - 6, 50],
              "parallax": 1.0, "z": -12} for cx in (100, 236, 420)] + [
            {"type": "anim_sprite", "file": "fx/steam.png", "frames": 8, "fps": 6, "pos": [1284, 230],
             "parallax": 1.0, "z": 1},
            {"type": "anim_sprite", "file": "fx/exhaust.png", "frames": 8, "fps": 6, "pos": [1546, 212],
             "parallax": 1.0, "z": 1},
        ],
        "actors": [
            {"scene": "res://scenes/levels/plaza/PlazaParade.tscn", "pos": [0, 0],
             "props": {"z": -15, "block": "res://assets/environments/hall_plaza/actors/march_block.png",
                       "standard": "res://assets/environments/hall_plaza/actors/standard.png",
                       "tank": "res://assets/environments/hall_plaza/actors/tank.png",
                       "puff": "res://assets/environments/hall_plaza/actors/exhaust_puff.png",
                       "feet_y": 220.0, "speed": 20.0, "span": [-260.0, 2240.0]}},
            {"scene": "res://scenes/levels/plaza/PlazaFlash.tscn", "pos": [1428, 217],
             "props": {"z": 2, "sprite": "res://assets/environments/hall_plaza/actors/flash.png"}},
        ],
        "notes": {
            "generator": "tools/pixelgen/env_plaza.py (+ env_plaza_sprites.py); py -3 -P tools/pixelgen/env_plaza.py",
            "rows": {"avenue": [188, 226], "parade_feet": 220, "guards_feet": 232, "barrier": [224, 240], "crowd_feet": 266,
                     "walk_band": [270, 352], "pavement": [271, 318], "kerb": 318, "street": [322, 352],
                     "tram_rails": [332, 342]},
            "axis": "hall + tribune are centred on screen when the player stands at x 1000 (exp_pz_tribune)",
            "z_order": "sky -100 < beams -95 < hall -90 < fog -85 < far_plaza -80 < fog -60 < ground -16 < "
                       "PlazaParade -15 < plaza_mid (guards, barrier) -14 < street_back -13 < smoke -12 < "
                       "playfield 0 (crowd, props, player) < fg 60",
            "insignia": "hall.png/hall_hist.png, far_plaza.png/far_plaza_hist.png, props/litfass, "
                        "props/banner_near, props/children, props/notice_door, actors/standard: neutral base + "
                        "_hist twin (Symbols.pick); the lantern figure is a plain eagle on the globe in both modes",
            "hotspots": "15 hotspots inside the walk band, >= 26 px apart (oblique metric dy x 1.6), outside "
                        "prop collisions; mark = where a marker may float",
        },
    }
    return m


# =========================================================================== checks + preview
def hotspot_check(m) -> list:
    errs = []
    poly = m['walkable']

    def inside(p):
        x, y = p
        c = False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    hs = dict(m['hotspots'])
    hs['SP_Plaza_Start'] = m['spawns']['SP_Plaza_Start']
    names = list(hs)
    for n_ in names:
        if not inside(hs[n_]):
            errs.append('outside walkable: ' + n_)
        for P in m['props']:
            c = P.get('collision')
            if c and c[0][0] - 3 <= hs[n_][0] <= c[1][0] + 3 and c[0][1] - 3 <= hs[n_][1] <= c[2][1] + 3:
                errs.append('in collision: %s / %s' % (n_, P['name']))
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a.startswith('SP_') or b.startswith('SP_'):
                continue
            d = math.hypot(hs[a][0] - hs[b][0], (hs[a][1] - hs[b][1]) * 1.6)
            if d < 26:
                errs.append('too close: %s %s %.1f' % (a, b, d))
    return errs


def palette_check() -> dict:
    allowed = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in SP.ALLOWED_HEX}
    bad = {}
    for dp, _, fs in os.walk(ENV):
        for f in fs:
            if not f.endswith('.png') or f.endswith('_n.png') or '_preview' in dp:
                continue
            a = np.asarray(Image.open(os.path.join(dp, f)).convert('RGBA'))
            op = a[..., 3] > 0
            cols = {tuple(c) for c in a[..., :3][op].reshape(-1, 3).tolist()}
            off = cols - allowed
            semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()) if not f.endswith('_e.png') else 0
            if off or semi:
                bad[os.path.relpath(os.path.join(dp, f), ENV)] = (len(off), semi)
    return bad


def compose_view(m, cam_x, hist, t_frame=0):
    """software preview of the layer stack at camera top-left (cam_x, 0); parade blocks at fixed spots"""
    out = Image.new('RGBA', (640, 360), (0, 0, 0, 255))

    def img(rel, frames=1, f=0):
        p = os.path.join(ENV, rel)
        if hist:
            hp = p[:-4] + '_hist.png'
            if os.path.exists(hp):
                p = hp
        im = Image.open(p).convert('RGBA')
        if frames > 1:
            w = im.width // frames
            im = im.crop((w * (f % frames), 0, w * (f % frames + 1), im.height))
        return im
    items = []
    for L_ in m['layers']:
        items.append((L_['z'], 0, img(L_['file']), L_['pos'], L_['parallax'][0]))
    for fx in m['fx']:
        if fx['type'] == 'anim_sprite':
            par = fx['parallax'][0] if isinstance(fx['parallax'], list) else fx['parallax']
            im = img(fx['file'], fx['frames'], t_frame)
            if 'alpha' in fx:
                a = np.asarray(im).copy()
                a[..., 3] = (a[..., 3] * fx['alpha']).astype(np.uint8)
                im = Image.fromarray(a)
            items.append((fx['z'], 0, im, fx['pos'], par))
    for i, x in enumerate((cam_x + 90, cam_x + 330)):
        items.append((-15, 0, img('actors/march_block.png', 8, t_frame + i), [x, 220 - 35], 1.0))
    items.append((-15, 0, img('actors/standard.png', 8, t_frame), [cam_x + 60, 220 - 52], 1.0))
    items.append((-15, 0, img('actors/tank.png', 4, t_frame), [cam_x + 470, 222 - 33], 1.0))
    pf = []
    for D in m['decals']:
        im = img(D['file'], D.get('frames', 1), t_frame)
        if D['layer'] == 'playfield':
            pf.append((D['base_y'], im, D['pos']))
        else:
            z = [L_['z'] for L_ in m['layers'] if L_['name'] == D['layer']][0]
            items.append((z, 1, im, D['pos'], 1.0))
    for P in m['props']:
        pf.append((P['base_y'], img(P['file']), P['pos']))
    items.sort(key=lambda it: (it[0], it[1]))
    for z, _, im, pos, par in [it for it in items if it[0] < 0]:
        _paste(out, im, int(round(pos[0] - cam_x * par)), int(pos[1]))
    for by, im, pos in sorted(pf, key=lambda q: q[0]):
        _paste(out, im, int(pos[0] - cam_x), int(pos[1]))
    for z, _, im, pos, par in [it for it in items if it[0] >= 0]:
        _paste(out, im, int(round(pos[0] - cam_x * par)), int(pos[1]))
    return out


def _paste(out, im, x, y):
    if x >= 640 or y >= 360 or x + im.width <= 0 or y + im.height <= 0:
        return
    tmp = Image.new('RGBA', out.size, (0, 0, 0, 0))
    tmp.paste(im, (x, y))
    out.alpha_composite(tmp)


def build_all(preview_dir=None):
    sz = SP.build_sprites()
    sky = paint_sky(); save(sky, 'sky', normal=False)
    save(paint_beams(), 'fx/beams', normal=False)
    save(paint_hall(False), 'hall', strength=2.0)
    save_color(paint_hall(True), 'hall_hist')
    save(paint_far_plaza(False), 'far_plaza', strength=2.0)
    save_color(paint_far_plaza(True), 'far_plaza_hist')
    save(paint_ground(), 'ground', strength=2.0)
    save(paint_plaza_mid(), 'plaza_mid')
    save(paint_street_back(), 'street_back')
    save(paint_fg(), 'fg_frame', normal=False)
    m = build_manifest(sz)
    sj = os.path.join(ENV, 'scene.json')
    KEEP.write_json(sj, KEEP.merge_scene(m, KEEP.read_json(sj)))   # keys / actors of other writers stay
    errs = hotspot_check(m)
    bad = palette_check()
    print('hotspot check:', errs or 'OK')
    print('palette check:', bad or 'OK', '| snapped off-palette px per file:',
          {k: v for k, v in SP.OFF_PALETTE.items() if v} or 'none')
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        for hist in (False, True):
            for cx in (0, 680, 1280):
                compose_view(m, cx, hist).save(os.path.join(preview_dir, 'view_%d_%s.png' % (cx, 'hist' if hist else 'neutral')))
    return m


if __name__ == '__main__':
    pv = None
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            pv = a.split('=', 1)[1]
    build_all(pv)
