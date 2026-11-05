"""cine_a1m1_karsk -- shot 1 of the A1 -> M1 transition: Karsk freight platform at dusk.

The C-17 wagon (re-used read-only from assets/environments/karsk_railyard/props/wagon_c17.png) is coupled
to a westbound freight train; an L-class style 2-10-0 steam locomotive pulls out to the LEFT (west, into
the last light of the day) while Alexei watches from the platform.

Assets written to assets/cinematics/a1m1/karsk/ (all original, deterministic):
  sky.png                 642x360  dusk gradient, glow low on the left (west), stratus streaks  (parallax 0)
  clouds.png              980x150  dusk cloud banks, warm undersides on the left                  (parallax .04)
  yard.png (+_n,_e)      1760x220  far track, fence, water tower, signal mast, near track, platform (p 1)
  fg.png                 1900x120  near-black foreground framing (crate stack, post, snow bank)  (p 1.15)
  loco.png / loco_hist.png (+_n,_e)  locomotive body facing left; neutral = fictional gear-and-wheat
                          emblem, _hist = red star + hammer & sickle (TECHNICAL_ARCHITECTURE 12.4)
  loco_wheels.png        strip 60 frames (crop WHEELS_CROP): drivers, rods, crosshead, Walschaerts valve gear
  wheel_pilot/_tender/_box.png  strips 8: small spoked wheels turning over one spoke period
  tender.png, gondola.png, boxcar.png   further train vehicles (+_n)
  tail_lamp.png (+_e)    red tail signal for the last wagon (the C-17 wagon)
  fx_puff.png            strip 12: chimney exhaust puff (expand, rise, thin out)
  fx_steam.png           strip 8: cylinder-cock steam along the rails
  fx_whistle.png         strip 8: whistle plume
  fx_snowdrop.png        strip 8: snow sliding off a wagon roof after the coupling jolt
  ledger_arm.png         the freight ledger under Alexei's arm (branch keep_private)
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_a1m1_lib as lib  # noqa: E402
from cine_a1m1_lib import (Layer, KR, tone_put, rect_tone, bayer, value_noise, white_noise, seed_of,  # noqa: E402
                           erode, dilate, edge_of, disc_mask, text)
import pg  # noqa: E402

NI, TE, SA, SK, ST, RU, CO, SN, WO = (KR[k] for k in ('night', 'teal', 'sage', 'sky', 'stone', 'rust',
                                                      'copper', 'snow', 'wood'))
RD = lib.SR_['red']
DIR = 'karsk'

# ---- set geometry (world pixels; the scene script reads layout.json written by cine_a1m1.py)
YARD_X0, YARD_Y0, YARD_W, YARD_H = 0, 140, 1760, 220
RAIL_Y = 272            # wheel contact row of every train vehicle (bottom row of their images)
PLATFORM_Y = 279        # platform edge line
LOCO_W, LOCO_H = 284, 112
WHEEL_R = 16
DRIVERS = [84, 120, 156, 192, 228]           # driver centres (x in loco image)
WHEEL_CY = LOCO_H - 1 - WHEEL_R              # y of wheel centres in the loco image
CRANK = 6                                   # crank radius (px)
CROSSHEAD_Y = WHEEL_CY - 2
CHIMNEY = (40, 11)                          # chimney mouth in loco image (x centre, y top)
WHISTLE = (198, 20)
CYL_STEAM = (26, 98)                        # cylinder cocks (front, low)
CAB_WINDOW = (232, 44, 16, 14)
WHEEL_FRAMES = 60                           # frames per driver revolution (6 deg: 1.7 px of travel per frame)
WHEELS_CROP = (20, 70, 228, 42)             # x, y, w, h of the running-gear strip inside the loco image
MAIN_ROD = 82
# Walschaerts valve gear (loco faces left: cylinders front-left, link behind the slide bars)
LINK_C = (104, 88)                          # expansion link trunnion
LINK_H = 6                                  # half length of the link
RET_THROW = 2.6                             # return crank throw around the main axle
DIE = -4                                    # die block position on the link (forward gear: upper half)
SPINDLE_Y = 84                              # valve spindle / lever top
RADIUS_Y = 86                               # radius rod joint on the combination lever
LEVER_B = CROSSHEAD_Y + 6                   # lever foot (union link)
LEVER_X = 64                                # combination lever (mid position)
UNION = 10                                  # union link length (crosshead arm -> lever foot)
# small rotating wheels drawn over the static ones of the vehicle images (x, y centre in that image)
SMALL_WHEELS = {
    'loco': [('wheel_pilot', 40, LOCO_H - 1 - 10)],
    'tender': [('wheel_tender', x, 82) for x in (26, 54, 136, 164)],
    'boxcar': [('wheel_box', x, 81) for x in (46, 150)],
}
SMALL_FRAMES = 8                            # frames over one spoke period


# =========================================================================== sky
def make_sky():
    W, H = 642, 360
    L = Layer(W, H, 'sky')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    horizon = 236.0
    # cool field: index into a night->teal->sky ramp, brighter toward the horizon
    cool = [NI[1], NI[2], NI[3], TE[1], TE[2], TE[3], TE[4], SK[0], SK[1], SK[2]]
    v = np.clip((yy - 10) / (horizon - 10), 0, 1) ** 1.35 * 8.4
    glow = np.exp(-(((xx - 70) / 430.0) ** 2) - (((yy - horizon + 6) / 62.0) ** 2))
    v += glow * 1.8
    v += (value_noise(W, H, 46, seed_of('ksky'), octaves=3) - 0.5) * 0.7
    tone_put(L, np.ones((H, W), bool), 0, 0, cool, v)
    # warm band: near the horizon on the left (sun just set in the west)
    warm = [RU[2], RU[3], RU[4], CO[1], CO[2], CO[3], CO[4]]
    wg = np.exp(-(((xx - 60) / 400.0) ** 2) - (((yy - horizon + 30) / 34.0) ** 2))
    wg += 0.55 * np.exp(-(((xx - 40) / 170.0) ** 2) - (((yy - horizon + 22) / 16.0) ** 2))
    wmask = wg > 0.16
    wt = np.clip((wg - 0.16) / 0.9, 0, 1) * 6.2
    sub = wmask
    tone_put(L, sub, 0, 0, warm, wt)
    # dither the boundary between cool and warm a little (ordered, no orphans)
    edge = (wg > 0.10) & (wg <= 0.16) & (bayer(W, H) < (wg - 0.10) / 0.06)
    L.c[edge] = RU[2]
    L.hgt[:] = 0
    return L


def _stratus(L, cx, cy, length, thick, seed, warm_until, lit_cols, body_cols):
    """One long, flat stratus band: ragged noisy outline, dark body, lit LOWER edge (the sun is below the
    horizon in the west) as long as the band lies west of `warm_until` (layer x)."""
    rng = np.random.default_rng(seed)
    x0 = int(cx - length / 2)
    prof_t = value_noise(length + 2, 1, 22, seed, octaves=3)[0]
    prof_b = value_noise(length + 2, 1, 15, seed + 7, octaves=3)[0]
    for i in range(length):
        x = x0 + i
        if not 0 <= x < L.w:
            continue
        u = i / max(1, length - 1)
        env = math.sin(math.pi * u) ** 0.45
        top = cy - thick * env * (0.35 + 0.65 * prof_t[i])
        bot = cy + thick * env * (0.15 + 0.35 * prof_b[i])
        y0, y1 = int(round(top)), int(round(bot))
        if y1 - y0 < 1:
            if env > 0.05 and rng.random() < 0.6:
                L.px(x, int(cy), body_cols[0])
            continue
        for y in range(y0, y1 + 1):
            if not 0 <= y < L.h:
                continue
            d = (y - y0) / max(1, y1 - y0)
            L.c[y, x] = body_cols[min(len(body_cols) - 1, int(d * len(body_cols)))]
        # lit lower edge, warm in the west, fading east (ordered dither on the transition)
        wt = np.clip((warm_until - x) / 260.0, 0, 1)
        if wt > 0 and 0 <= y1 < L.h:
            k = min(len(lit_cols) - 1, int(wt * len(lit_cols)))
            if wt > 0.15 or bayer(1, 1, x, y1)[0, 0] < wt * 5:
                L.c[y1, x] = lit_cols[k]
            if wt > 0.6 and y1 - 1 > y0:
                L.c[y1 - 1, x] = lit_cols[max(0, k - 2)]


# =========================================================================== clouds
def make_clouds():
    """Dusk sky texture: long flat stratus bands (layer x 0..980), warm-lit undersides in the west."""
    W, H = 980, 150
    L = Layer(W, H, 'clouds')
    rng = np.random.default_rng(seed_of('kclouds'))
    body = [NI[2], NI[3], TE[1]]
    lit = [RU[2], RU[3], RU[4], CO[1], CO[2]]
    bands = []
    for i in range(16):
        y = rng.uniform(8, 138)
        ln = int(rng.uniform(140, 420) * (0.6 + y / 150))
        th = rng.uniform(1.5, 5.5) * (0.5 + y / 150)
        cx = rng.uniform(-80, W + 80)
        bands.append((y, cx, ln, th, i))
    for (y, cx, ln, th, i) in sorted(bands):
        _stratus(L, cx, y, ln, th, seed_of('st%d' % i), warm_until=430 + y * 1.4, lit_cols=lit,
                 body_cols=body if y > 50 else [NI[1], NI[2]])
    L.hgt[:] = 0
    return L


# =========================================================================== yard (p = 1)
def _rails(L, y_far, y_near, x0, x1, seed):
    """Oblique track: sleepers between two rails, ballast with snow."""
    rng = np.random.default_rng(seed)
    yb0, yb1 = y_far - 4, y_near + 4
    # ballast
    nz = value_noise(x1 - x0, yb1 - yb0, 5, seed, octaves=2)
    t = 1.2 + nz * 1.6
    tone_put(L, np.ones((yb1 - yb0, x1 - x0), bool), x0, yb0, [ST[0], ST[1], ST[2], ST[3]], t, hgt=0.3)
    # sleepers (dark wood, slightly skewed in oblique)
    for x in range(x0 + int(rng.integers(0, 4)), x1, 7):
        L.rect(x, y_far - 1, 4, y_near - y_far + 3, WO[1], hgt=0.42)
        L.hline(x, y_far - 1, 4, WO[2], hgt=0.45)
        L.px(x + 3, y_near + 1, WO[0])
    # snow lying on ballast between sleepers, patchy
    sn = value_noise(x1 - x0, yb1 - yb0, 9, seed + 3, octaves=3)
    m = sn > 0.52
    m[:2] = False
    tone_put(L, m, x0, yb0, [SN[0], SN[1], SN[2]], 0.6 + (sn - 0.52) * 9, hgt=0.36)
    # rails: far rail (thin, partially hidden), near rail with a bright top edge
    for y, hi in ((y_far, ST[3]), (y_near, ST[4])):
        L.rect(x0, y, x1 - x0, 2, NI[3], hgt=0.6)
        L.hline(x0, y, x1 - x0, hi, hgt=0.65)
        L.hline(x0, y + 2, x1 - x0, NI[1], hgt=0.3)
        for x in range(x0, x1):            # warm sky glint on the rail tops toward the west
            if x < x0 + 900 and (x * 13 + y * 7) % 23 < 2:
                L.px(x, y, CO[2])


def _fence(L, x0, x1, ytop, seed):
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = int(rng.integers(26, 34))
        if rng.random() < 0.12:
            x += w
            continue
        h = 14 + int(rng.integers(-1, 2))
        rect_tone(L, x, ytop + (16 - h), w - 1, h, [NI[3], TE[0], TE[1], TE[2]],
                  lib.grad_v(h, w - 1, 2.6, 1.0), hgt=0.4)
        L.vline(x + w - 2, ytop + (16 - h), h, NI[2])
        L.hline(x, ytop + (16 - h), w - 1, SN[1])          # snow on top
        if rng.random() < 0.5:
            L.hline(x + 2, ytop + (16 - h) - 1, w - 6, SN[2])
        x += w


def _water_tower(L, cx, base):
    """Brick base, wooden tank with hoops, conical roof with snow; warm rim on the left (west glow)."""
    bw, bh = 34, 64
    x0 = cx - bw // 2
    rng = np.random.default_rng(seed_of('wtower'))
    for y in range(base - bh, base):
        for x in range(x0, x0 + bw):
            row = (y - (base - bh)) // 2
            off = 2 if row % 2 else 0
            mortar = ((x - x0 + off) % 5 == 0) or ((y - (base - bh)) % 2 == 0)
            c = NI[3] if mortar else (RU[0] if rng.random() < 0.7 else RU[1])
            L.px(x, y, c, hgt=0.45)
    L.rect(x0 + 13, base - 22, 8, 22, NI[1], hgt=0.2)        # door
    L.rect(x0 + 6, base - bh + 14, 5, 7, NI[1])
    L.rect(x0 + bw - 11, base - bh + 14, 5, 7, NI[1])
    L.vline(x0, base - bh, bh, RU[2])                          # west rim
    # tank
    tw, th = 52, 30
    tx = cx - tw // 2
    ty = base - bh - th
    for x in range(tx, tx + tw):
        t = 2.4 - abs((x - tx) / tw - 0.25) * 2.0
        L.rect(x, ty, 1, th, WO[int(np.clip(round(t), 0, 4))], hgt=0.5)
    for k in range(3):
        L.hline(tx, ty + 6 + k * 9, tw, NI[2])
    L.vline(tx, ty, th, CO[0])
    L.hline(tx - 2, ty + th, tw + 4, NI[2])
    # roof
    for k in range(10):
        w = tw + 4 - k * 5
        if w <= 2:
            break
        L.hline(cx - w // 2, ty - 1 - k, w, SN[1] if k > 1 else NI[3], hgt=0.6)
    L.hline(cx - (tw + 4) // 2, ty - 2, 10, CO[1])
    # spout arm
    L.rect(tx + tw, ty + 20, 14, 2, NI[2])
    L.rect(tx + tw + 12, ty + 22, 2, 9, NI[2])


def _signal_mast(L, x, base):
    L.rect(x, base - 88, 3, 88, NI[2], hgt=0.6)
    L.vline(x, base - 88, 88, ST[2])
    L.rect(x - 4, base - 92, 11, 18, NI[1], hgt=0.5)            # lamp housing
    L.rect(x - 2, base - 90, 7, 6, RD[1], hgt=0.6, em=RD[3])     # red aspect (emission)
    L.px(x - 1, base - 89, RD[3], em=RD[3])
    L.rect(x - 2, base - 82, 7, 6, NI[0], hgt=0.6)               # dark green aspect (off)
    L.hline(x - 4, base - 93, 11, SN[2])
    for k in range(0, 80, 6):                                     # ladder
        L.hline(x + 3, base - 84 + k, 3, NI[3])


def _ground(L, x0, x1):
    """West of the platform: a snow-covered embankment in front of the track -- continuous snow with
    soft drifts, a cinder strip right at the sleepers and a few tufts of dead grass poking through."""
    y0 = PLATFORM_Y - 2 - YARD_Y0
    h = YARD_H - y0
    w = x1 - x0
    nz = value_noise(w, h, 26, seed_of('ground'), octaves=3)
    rows = np.arange(h, dtype=np.float32)[:, None]
    depth = np.repeat(rows / h, w, 1)
    drift = np.sin(np.arange(w) / 23.0)[None, :] * 0.25 + np.sin(np.arange(w) / 61.0)[None, :] * 0.35
    t = 2.0 + (nz - 0.5) * 0.7 - depth * 1.1 + drift * np.exp(-((rows - 18) / 10.0) ** 2)
    tone_put(L, np.ones((h, w), bool), x0, y0, [ST[1], ST[2], SN[0], SN[1], SN[2]], t, hgt=0.5)
    # cinder strip at the track edge (dark, uneven top edge)
    edge = 3 + (value_noise(w, 1, 9, seed_of('cinder'), octaves=2)[0] * 4).astype(int)
    for x in range(w):
        L.rect(x0 + x, y0, 1, int(edge[x]), ST[0] if x % 5 else NI[3])
    rng = np.random.default_rng(seed_of('ground2'))
    for k in range(int(w * 0.06)):                     # dead grass through the snow
        gx = int(rng.integers(x0, x1))
        gy = int(y0 + rng.integers(10, h - 6))
        for j in range(int(rng.integers(2, 5))):
            L.px(gx + int(rng.integers(-1, 2)), gy - j, SA[0] if rng.random() < 0.5 else WO[1])


def _platform(L, x0, x1):
    """Platform: edge stones, then a continuous snow cover with a trodden, darker path along the platform,
    footprints, a few slush spots near the edge and slab joints showing through where the snow is thin."""
    y0 = PLATFORM_Y - YARD_Y0
    h = YARD_H - y0
    w = x1 - x0
    nz = value_noise(w, h, 22, seed_of('plat'), octaves=3)
    fine = white_noise(w, h, seed_of('plat2'))
    rows = np.arange(h, dtype=np.float32)[:, None]
    depth = np.repeat(rows / h, w, 1)
    # snow cover: cold blue-grey dusk values, slightly brighter just behind the edge (sky reflection)
    t = 1.9 + (nz - 0.5) * 0.9 - depth * 0.9 + np.exp(-((rows - 4) / 5.0) ** 2) * 0.6
    tone_put(L, np.ones((h, w), bool), x0, y0, [ST[1], ST[2], SN[0], SN[1], SN[2]], t, hgt=0.55)
    # trodden path: a darker band (people walk 10..24 px behind the edge), wavy, with footprints
    path_c = 17 + 4 * np.sin(np.arange(w) / 37.0) + 2 * np.sin(np.arange(w) / 11.0)
    band = np.abs(rows - path_c[None, :]) < (5 + 2 * nz)
    tone_put(L, band, x0, y0, [ST[0], ST[1], ST[2], SN[0]], 1.5 + (nz - 0.5) * 1.2, hgt=0.45)
    rng = np.random.default_rng(seed_of('steps'))
    for k in range(int(w * 0.35)):
        fx = int(rng.integers(0, w - 2))
        fy = int(path_c[fx] + rng.integers(-5, 6))
        if 0 <= fy < h - 1:
            L.rect(x0 + fx, y0 + fy, 2, 1, ST[0] if rng.random() < 0.5 else ST[1])
    # thin snow over the slab joints: joints show as faint lines
    for jy in (30, 52):
        if jy < h:
            m = fine[jy] > 0.35
            for x in range(w):
                if m[x]:
                    L.px(x0 + x, y0 + jy, ST[2])
    for jx in range(x0 + 5, x1, 48):
        for k in range(26, h):
            xx = jx - k // 4
            if x0 <= xx < x1 and fine[k, min(w - 1, xx - x0)] > 0.45:
                L.px(xx, y0 + k, ST[2])
    # edge stones: bright worn stripe with snow caps
    L.rect(x0, y0 - 1, w, 3, ST[4], hgt=0.7)
    L.hline(x0, y0 - 1, w, SN[3], hgt=0.75)
    L.hline(x0, y0 + 2, w, ST[1])
    for x in range(x0, x1, 9):
        L.vline(x, y0 - 1, 3, ST[2])
    # slush spots near the edge (dark, catch lamp light through the normal map)
    for k in range(9):
        px_ = int(rng.integers(x0 + 20, x1 - 60))
        py_ = int(y0 + rng.integers(4, 9))
        m, mx, my = L.ellipse_mask(px_, py_, rng.uniform(8, 18), rng.uniform(1.2, 2.2))
        L._put(m & (bayer(m.shape[1], m.shape[0], mx, my) < 0.75), mx, my, ST[1], hgt=0.2)


def make_yard():
    L = Layer(YARD_W, YARD_H, 'yard')
    Y = YARD_Y0

    class Off:          # draw in world coordinates
        pass
    # far track and fence (behind the train)
    _fence(L, 0, YARD_W, 236 - Y, seed_of('fence'))
    _rails(L, 254 - Y, 258 - Y, 0, YARD_W, seed_of('rails_far'))
    _rails(L, 266 - Y, RAIL_Y - Y, 0, YARD_W, seed_of('rails_near'))
    # water tower (behind the locomotive's start) and signal mast (west end beyond the platform)
    _water_tower(L, 640, 250 - Y)
    _signal_mast(L, 1640, 252 - Y)
    # low snow banks along the far track
    rng = np.random.default_rng(seed_of('banks'))
    for k in range(40):
        bx = int(rng.integers(0, YARD_W))
        m, mx, my = L.ellipse_mask(bx, 251 - Y, rng.uniform(6, 18), rng.uniform(1.5, 3))
        L._put(m, mx, my, SN[1], hgt=0.5)
        L._put(m & (np.arange(m.shape[0])[:, None] < m.shape[0] // 2), mx, my, SN[2])
    _ground(L, 0, 772)
    _platform(L, 760, YARD_W)
    # the platform begins at x=760: ramp end (sloping edge) toward the west
    for k in range(12):
        L.hline(748 + k, PLATFORM_Y - Y + k * 2 - 1, 12 - k, ST[2])
    return L


def make_fg():
    """Near-black framing silhouettes (parallax 1.15): a snow-capped sleeper stack and a frozen hand cart for
    the platform shots, a buffer stop for the locomotive shot; cold rim from the sky on their tops."""
    W, H = 2000, 120
    L = Layer(W, H, 'fg')
    def stack(x, w, layers, top):
        for k in range(layers):
            y = top + k * 6
            L.rect(x + (k % 2) * 3, y, w - (k % 2) * 3, 5, NI[1])
            L.hline(x + (k % 2) * 3, y, w - (k % 2) * 3, NI[3])
            for e in range(x + (k % 2) * 3, x + w, 9):
                L.vline(e, y + 1, 4, NI[0])
        L.hline(x, top - 1, w, SN[1])
        L.hline(x + 2, top - 2, w - 6, SN[0])
    # hand cart (lower right of the platform shot)
    L.rect(1560, 70, 46, 10, NI[1])
    L.hline(1560, 70, 46, NI[3])
    L.hline(1562, 69, 40, SN[1])
    for wx in (1570, 1596):
        L.ellipse(wx, 86, 7, 7, NI[0])
        L.ellipse(wx, 86, 2, 2, NI[2])
    L.line(1606, 72, 1626, 52, NI[1])
    # snow bank along the bottom edge
    nz = value_noise(W, 24, 14, seed_of('fgbank'), octaves=3)
    for x in range(W):
        h = int(4 + nz[0, x] * 12)
        L.rect(x, H - h, 1, h, NI[1])
        L.px(x, H - h, NI[3])
    return L


# =========================================================================== locomotive
def _emblem_layer(hist: bool) -> Layer:
    """Smoke-deflector emblem. hist: red disc with gold hammer & sickle under a red star (Soviet state
    iconography on a locomotive); neutral: fictional gear-and-wheat on a red disc."""
    if hist:
        E = Layer(17, 26, 'emb')
        star = lib.STAR_9
        E._put(star, 4, 0, RD[2], hgt=0.85)
        E._put(edge_of(star) & (np.arange(9)[:, None] < 5), 4, 0, RD[3])
        d = disc_mask(17)
        E._put(d, 0, 9, RD[1], hgt=0.7)
        E._put(edge_of(d), 0, 9, CO[2], hgt=0.8)
        hs = lib.HS_13
        E._put(hs, 2, 11, CO[3], hgt=0.9)
        E._put(hs & (np.arange(13)[:, None] > 8), 2, 11, CO[2])
        return E
    E = Layer(17, 26, 'emb')
    d = disc_mask(17)
    E._put(d, 0, 9, RD[1], hgt=0.7)
    E._put(edge_of(d), 0, 9, CO[2], hgt=0.8)
    gw = lib.GEAR_WHEAT_13
    E._put(gw, 2, 11, CO[3], hgt=0.9)
    E._put(gw & (np.arange(13)[:, None] > 8), 2, 11, CO[2])
    # small plain plate above instead of the star
    E.rect(6, 3, 5, 4, ST[2], hgt=0.8)
    E.hline(6, 3, 5, ST[4])
    return E


def make_loco(hist: bool):
    W, H = LOCO_W, LOCO_H
    L = Layer(W, H, 'loco')
    rail = H - 1
    # ---------------- frame + running gear behind the wheels
    fy0, fy1 = WHEEL_CY - 18, WHEEL_CY + 4
    L.rect(60, fy0, 196, fy1 - fy0, NI[1], hgt=0.35)                  # frame plates (behind wheels)
    L.hline(60, fy0, 196, NI[3])
    for x in range(64, 252, 12):
        L.px(x, fy0 + 3, ST[1])
    # ---------------- boiler
    bx0, bx1 = 22, 214
    by_c, br = 54, 23                                               # centre y, radius
    bh = br * 2
    btop = by_c - br
    tone = lib.cyl_tone(bh, bx1 - bx0, 0.6, 4.2, light_y=0.22)
    cyl = [NI[1], NI[2], NI[3], TE[1], TE[2], TE[3]]
    tone_put(L, np.ones((bh, bx1 - bx0), bool), bx0, btop, cyl, tone,
             hgt=lib.cyl_height(bh, bx1 - bx0) * 0.9 + 0.1)
    # boiler bands (rings) every ~30 px, with a lit top pixel
    for x in range(bx0 + 34, bx1, 30):
        L.rect(x, btop, 2, bh, NI[2], hgt=0.95)
        L.px(x, btop + 3, ST[3])
        L.px(x, btop + 4, ST[2])
    # specular streak along the upper boiler (sky reflection)
    for x in range(bx0 + 4, bx1 - 2):
        if (x * 7) % 11 < 8:
            L.px(x, btop + 5, TE[4])
    L.hline(bx0 + 2, btop, bx1 - bx0 - 4, TE[3])
    # handrail along the boiler
    L.hline(bx0 + 30, by_c - 4, bx1 - bx0 - 40, ST[3], hgt=1.0)
    for x in range(bx0 + 40, bx1 - 10, 26):
        L.px(x, by_c - 3, ST[1])
    # ---------------- smokebox (front, slightly darker, with the door ring edge on the left)
    sx0, sx1 = 14, 64
    st = lib.cyl_tone(bh + 4, sx1 - sx0, 0.4, 3.4, light_y=0.2)
    tone_put(L, np.ones((bh + 4, sx1 - sx0), bool), sx0, btop - 2, cyl, st,
             hgt=lib.cyl_height(bh + 4, sx1 - sx0) * 0.95 + 0.1)
    L.rect(sx0 - 3, btop + 1, 4, bh + 2, NI[2], hgt=0.9)              # door ring seen edge-on
    L.vline(sx0 - 3, btop + 1, bh + 2, CO[1])                          # warm west rim on the very front
    L.vline(sx0 - 2, btop + 4, bh - 4, RU[3])
    L.rect(sx1 - 2, btop - 2, 2, bh + 4, NI[2])
    # chimney
    cx, cy = CHIMNEY
    L.rect(cx - 6, cy + 2, 13, btop - cy, NI[2], hgt=0.8)
    L.rect(cx - 7, cy, 15, 3, NI[3], hgt=0.9)                          # lip
    L.hline(cx - 7, cy, 15, ST[2])
    L.vline(cx - 7, cy, btop - cy + 1, CO[0])
    L.vline(cx - 6, cy + 3, btop - cy - 2, TE[2])
    # headlamp on top of the smokebox front
    L.rect(16, btop - 9, 11, 8, NI[2], hgt=0.85)
    L.hline(16, btop - 10, 11, ST[2])
    L.rect(15, btop - 7, 3, 5, CO[3], hgt=0.9, em=CO[4])               # lamp glass (faces left)
    L.px(15, btop - 6, CO[4], em=CO[4])
    # domes
    for (dx, dw, dh) in ((112, 22, 9), (152, 18, 7)):
        for k in range(dh):
            w = dw - max(0, (k - dh + 4)) * 0 - (2 if k < 2 else 0)
            L.hline(dx - w // 2, btop - dh + k, w, NI[3] if k > 1 else TE[2], hgt=0.9)
        L.hline(dx - dw // 2 + 2, btop - dh, dw - 4, TE[3])
        L.px(dx - dw // 2, btop - dh + 3, CO[1])
    # whistle
    wx, wy = WHISTLE
    L.rect(wx - 1, wy, 3, btop - wy, ST[2], hgt=0.9)
    L.rect(wx - 2, wy - 2, 5, 3, ST[3], hgt=1.0)
    # air pump + pipes on the side (Soviet practice), dark with highlights
    L.rect(76, by_c + 4, 9, 20, NI[3], hgt=0.7)
    L.hline(76, by_c + 4, 9, ST[2])
    L.vline(76, by_c + 4, 20, CO[0])
    L.hline(85, by_c + 10, 60, NI[3])
    L.hline(85, by_c + 14, 90, NI[2])
    L.hline(85, by_c + 11, 60, ST[1])
    # running board (with bright edge line) and steps
    rb = btop + bh + 2
    L.rect(60, rb, 160, 3, NI[3], hgt=0.6)
    L.hline(60, rb, 160, ST[3])
    L.hline(60, rb + 3, 160, NI[0])
    # ---------------- cylinders (front, low)
    L.rect(18, rb + 2, 42, 18, NI[2], hgt=0.75)
    L.rect(16, rb + 4, 4, 14, NI[3], hgt=0.8)
    L.hline(18, rb + 2, 42, ST[2])
    L.hline(18, rb + 10, 42, NI[3])
    L.vline(16, rb + 4, 14, CO[0])
    L.rect(26, rb - 3, 26, 5, NI[3], hgt=0.7)                         # steam chest
    L.hline(26, rb - 3, 26, ST[2])
    # buffer beam (red) + buffers + coupler
    L.rect(4, rb + 4, 14, 9, RD[1], hgt=0.6)
    L.hline(4, rb + 4, 14, RD[2])
    for by in (rb + 5, rb + 10):
        L.rect(0, by, 5, 3, ST[2], hgt=0.8)
        L.px(0, by, ST[4])
    L.rect(2, rb + 13, 10, 3, NI[2])                                    # pilot / cow-catcher plate
    for k in range(6):
        L.hline(3 + k, rb + 16 + k, 12 - k, NI[2])
    # leading (pilot) wheel
    pcx, pcy, pr = 40, rail - 10, 10
    m, mx, my = L.ellipse(pcx, pcy, pr + 0.5, pr + 0.5, NI[1], hgt=0.5)
    L.ellipse(pcx, pcy, pr - 1.0, pr - 1.0, RD[0], hgt=0.45)
    L.ellipse(pcx, pcy, pr - 2.4, pr - 2.4, NI[0], hgt=0.2)
    L.ellipse(pcx, pcy, 2.4, 2.4, ST[2], hgt=0.7)
    for a in range(0, 360, 45):
        L.line(pcx, pcy, pcx + math.cos(math.radians(a)) * (pr - 2), pcy + math.sin(math.radians(a)) * (pr - 2),
               RD[1])
    # ---------------- smoke deflectors (big plates beside the smokebox) + emblem
    dx0, dx1 = 8, 62
    dy0, dy1 = btop + 2, rb
    for y in range(dy0, dy1):
        inset = max(0, 6 - (y - dy0)) if True else 0
        L.rect(dx0 + inset, y, dx1 - dx0 - inset, 1, NI[2], hgt=0.75)
    L.hline(dx0 + 6, dy0, dx1 - dx0 - 6, ST[2])
    for k in range(6):
        L.px(dx0 + 6 - k, dy0 + k, CO[1])
    L.vline(dx0, dy0 + 6, dy1 - dy0 - 6, CO[1])                         # west rim on the plate edge
    L.vline(dx1 - 1, dy0, dy1 - dy0, NI[1])
    L.hline(dx0, dy1 - 1, dx1 - dx0, NI[1])
    # subtle plate shading: lighter band at the top (sky)
    for y in range(dy0 + 1, dy0 + 6):
        for x in range(dx0 + 7, dx1 - 1):
            if (x + y) % 2 == 0:
                L.px(x, y, NI[3])
    E = _emblem_layer(hist)
    L.blit(E, (dx0 + dx1) // 2 - 8, dy0 + 8)
    # ---------------- cab
    cx0, cx1 = 214, 270
    cy0 = 18
    cab_bot = rb + 2
    rect_tone(L, cx0, cy0 + 4, cx1 - cx0, cab_bot - cy0 - 4, [NI[1], NI[2], NI[3], TE[1]],
              lib.grad_v(cab_bot - cy0 - 4, cx1 - cx0, 2.6, 1.0), hgt=0.7)
    L.vline(cx0, cy0 + 4, cab_bot - cy0 - 4, CO[0])
    for k in range(4):                                                  # roof with overhang + snow
        L.hline(cx0 - 4 + k // 2, cy0 + k, cx1 - cx0 + 8 - k, NI[3] if k > 1 else SN[2], hgt=0.85)
    L.hline(cx0 - 3, cy0 - 1, cx1 - cx0 + 6, SN[3])
    # cab side window with the firebox glow (emission) and the driver's silhouette
    wx_, wy_, ww_, wh_ = CAB_WINDOW
    L.rect(wx_ - 1, wy_ - 1, ww_ + 2, wh_ + 2, NI[0])
    gl = [CO[0], CO[1], CO[2], CO[3]]
    gm = np.ones((wh_, ww_), bool)
    gt = lib.grad_v(wh_, ww_, 0.6, 3.2) + lib.grad_h(wh_, ww_, 0.0, 0.6)
    tone_put(L, gm, wx_, wy_, gl, gt, hgt=0.3, em=True)
    # driver: cap + shoulder silhouette leaning toward the window (looks back along the train)
    for (x, y, w, h) in ((wx_ + 3, wy_ + 3, 6, 4), (wx_ + 2, wy_ + 7, 9, 7), (wx_ + 4, wy_ + 2, 4, 1)):
        L.rect(x, y, w, h, NI[1])
        L.em[y:y + h, x:x + w] = 0
    L.px(wx_ + 3, wy_ + 5, CO[1])                                       # cheek lit by the fire
    L.em[wy_ + 5, wx_ + 3] = CO[1]
    L.vline(wx_ + ww_ // 2 + 3, wy_, wh_, NI[0])                        # window mullion
    L.em[wy_:wy_ + wh_, wx_ + ww_ // 2 + 3] = 0
    # front cab window (small, faces forward: just a dark slot with a warm edge)
    L.rect(cx0 + 3, cy0 + 10, 5, 10, NI[0])
    L.rect(cx0 + 7, cy0 + 10, 1, 10, CO[1], em=CO[1])
    # cab number plate: Cyrillic class letter + number (white stencil)
    text(L, cx0 + 14, wy_ + wh_ + 6, 'Л-2317', SN[3])
    L.hline(cx0 + 12, wy_ + wh_ + 4, 36, RD[1])                         # thin red band
    L.hline(cx0 + 12, wy_ + wh_ + 12, 36, RD[1])
    # firebox glow spilling under the cab (ash pan) -> emission
    L.rect(cx0 + 4, cab_bot - 1, 30, 2, RU[3], em=CO[1])
    # steps + handrails at the cab
    L.rect(cx1 - 6, cab_bot, 6, 2, NI[3])
    L.rect(cx1 - 6, cab_bot + 8, 6, 2, NI[3])
    L.vline(cx1 - 1, cy0 + 20, 30, ST[3])
    # drawbar to the tender
    L.rect(cx1, cab_bot + 4, W - cx1, 3, NI[2])
    # ---------------- snow on upward edges (boiler top, cab roof, running board, domes)
    pg.snow_caps(L, [SN[1], SN[2], SN[3]], depth=1, seed=seed_of('locosnow'), coverage=0.55,
                 mask=L.alpha() & (np.arange(H)[:, None] < rb + 1))
    return L


def _rod(F, a, b, col, hi=None, lo=None, hgt=0.9):
    """A steel rod a->b: body colour, optional lit upper edge / dark lower edge (1 px each)."""
    F.line(a[0], a[1], b[0], b[1], col, hgt=hgt)
    if hi is not None:
        F.line(a[0], a[1] - 1, b[0], b[1] - 1, hi, hgt=hgt)
    if lo is not None:
        F.line(a[0], a[1] + 1, b[0], b[1] + 1, lo, hgt=hgt)


def gear_state(ang: float) -> dict:
    """Positions of every moving part for wheel angle `ang` (radians, screen space). The scene script uses
    the same formulas only through the frame index, so the strip *is* the kinematics."""
    cx_m, cy = DRIVERS[2], WHEEL_CY
    pins = [(wx + math.cos(ang) * CRANK, cy + math.sin(ang) * CRANK) for wx in DRIVERS]
    mp = pins[2]
    chx = mp[0] - math.sqrt(max(1.0, MAIN_ROD ** 2 - (mp[1] - CROSSHEAD_Y) ** 2))
    # return crank: 90 deg ahead of the main crank, small throw around the axle
    ra = ang - math.pi / 2
    E = (cx_m + math.cos(ra) * RET_THROW, cy + math.sin(ra) * RET_THROW)
    E0x = cx_m                                   # mid position (for the link swing)
    th = math.asin(max(-0.9, min(0.9, (E[0] - E0x) / (LINK_H + 1.0))))
    sx, sy = math.sin(th), math.cos(th)
    foot = (LINK_C[0] + sx * LINK_H, LINK_C[1] + sy * LINK_H)
    top = (LINK_C[0] - sx * LINK_H, LINK_C[1] - sy * LINK_H)
    die = (LINK_C[0] + sx * DIE, LINK_C[1] + sy * DIE)
    R = (die[0] - (LINK_C[0] - LEVER_X), RADIUS_Y)
    B = (chx - UNION, LEVER_B)
    T = (R[0] + (R[0] - B[0]) * (RADIUS_Y - SPINDLE_Y) / (LEVER_B - RADIUS_Y), SPINDLE_Y)
    return {'pins': pins, 'chx': chx, 'E': E, 'foot': foot, 'top': top, 'die': die, 'R': R, 'B': B, 'T': T}


def _driver(F, cx, cy, ang):
    F.ellipse(cx, cy, WHEEL_R + 0.5, WHEEL_R + 0.5, NI[1], hgt=0.5)       # tyre (steel, dark)
    F.ellipse(cx, cy, WHEEL_R - 1.2, WHEEL_R - 1.2, RD[0], hgt=0.45)      # red wheel-centre rim
    F.ellipse(cx, cy, WHEEL_R - 2.6, WHEEL_R - 2.6, NI[0], hgt=0.2)       # see-through gaps
    for s in range(10):                                                   # spokes (10, red)
        a = ang + s * (2 * math.pi / 10)
        F.line(cx + math.cos(a) * 2, cy + math.sin(a) * 2,
               cx + math.cos(a) * (WHEEL_R - 2.5), cy + math.sin(a) * (WHEEL_R - 2.5), RD[1])
    # counterweight (crescent) opposite the crank
    ca = ang + math.pi
    m, mx, my = F.ellipse_mask(cx + math.cos(ca) * 8, cy + math.sin(ca) * 8, 6.5, 6.5)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    inside = ((xx + mx + 0.5 - cx) ** 2 + (yy + my + 0.5 - cy) ** 2) <= (WHEEL_R - 1.2) ** 2
    F._put(m & inside, mx, my, RD[1], hgt=0.55)
    # tyre rim light: warm upper-left (west glow), cold steel lower-right -- fixed in screen space
    for a in range(0, 360, 6):
        rx = cx + int(round(math.cos(math.radians(a)) * WHEEL_R))
        ry = cy + int(round(math.sin(math.radians(a)) * WHEEL_R))
        if 180 <= a <= 270:
            F.px(rx, ry, CO[0] if a < 230 else ST[2])
        elif a > 270:
            F.px(rx, ry, ST[1])
    F.ellipse(cx, cy, 2.6, 2.6, ST[2], hgt=0.8)                            # hub
    F.px(cx - 1, cy - 1, ST[4])


def make_wheels():
    """WHEEL_FRAMES frames of one driver revolution, cropped to WHEELS_CROP: 5 coupled drivers (red centres,
    counterweights), coupling rod, main rod, crosshead in its slide bars, piston rod, and the Walschaerts valve
    gear (return crank, eccentric rod, swinging expansion link, radius rod, combination lever, union link,
    valve spindle) -- all derived from the one wheel angle, so rods and valve gear are always in phase.
    Frame k = rotation angle -k * 360/WHEEL_FRAMES deg (anticlockwise on screen: the engine runs left)."""
    frames = []
    W, H = LOCO_W, LOCO_H
    x0, y0, cw, chh = WHEELS_CROP
    for k in range(WHEEL_FRAMES):
        F = Layer(W, H, 'wheels%d' % k)
        ang = -k * (2 * math.pi / WHEEL_FRAMES)
        g = gear_state(ang)
        # slide bars behind the crosshead + the expansion-link bracket (static parts on this strip)
        F.hline(60, CROSSHEAD_Y - 5, 38, NI[2])
        F.hline(60, CROSSHEAD_Y + 4, 38, NI[2])
        F.rect(LINK_C[0] - 3, LINK_C[1] - 2, 7, 5, NI[1], hgt=0.6)        # link bracket
        for wx in DRIVERS:
            _driver(F, wx, WHEEL_CY, ang)
        pins = g['pins']
        for (ax, ay), (bx, by) in zip(pins[:-1], pins[1:]):               # coupling rod (thick steel bar)
            for d in (-1, 0, 1):
                F.line(ax, ay + d, bx, by + d, NI[3] if d else ST[2])
            F.line(ax, ay - 1, bx, by - 1, ST[3])
        for (px_, py_) in pins:
            F.ellipse(px_, py_, 2.2, 2.2, ST[3], hgt=0.95)
        chx, mp = g['chx'], pins[2]
        # piston rod, crosshead, main rod
        F.line(58, CROSSHEAD_Y, chx - 4, CROSSHEAD_Y, ST[3])
        F.line(58, CROSSHEAD_Y + 1, chx - 4, CROSSHEAD_Y + 1, NI[2])
        _rod(F, (chx, CROSSHEAD_Y), mp, ST[2], hi=ST[3], lo=NI[3])
        F.rect(int(round(chx)) - 4, CROSSHEAD_Y - 3, 8, 7, NI[3], hgt=0.85)    # crosshead
        F.hline(int(round(chx)) - 4, CROSSHEAD_Y - 3, 8, ST[3])
        F.px(int(round(chx)) - 4, CROSSHEAD_Y - 2, CO[0])
        F.rect(int(round(chx)) - 2, CROSSHEAD_Y + 4, 3, 3, NI[3])             # crosshead arm (union link)
        F.hline(60, CROSSHEAD_Y - 5, 38, ST[1])                              # upper bar edge over it
        # valve gear (outermost): return crank -> eccentric rod -> link -> radius rod -> lever -> spindle
        E, foot, top, die, R, B, T = g['E'], g['foot'], g['top'], g['die'], g['R'], g['B'], g['T']
        _rod(F, mp, E, ST[3])                                                # return crank
        _rod(F, E, foot, ST[1])                                              # eccentric rod
        _rod(F, top, foot, ST[2], lo=NI[2])                                  # expansion link (slotted arc)
        F.ellipse(LINK_C[0], LINK_C[1], 1.6, 1.6, ST[3], hgt=1.0)            # trunnion
        _rod(F, die, R, ST[1])                                               # radius rod
        F.px(int(round(die[0])), int(round(die[1])), ST[4])                  # die block
        _rod(F, (chx - 2, CROSSHEAD_Y + 5), B, NI[3])                        # union link
        _rod(F, B, T, ST[2])                                                 # combination lever
        F.line(58, SPINDLE_Y, T[0], SPINDLE_Y, ST[2])                        # valve spindle
        F.ellipse(E[0], E[1], 1.3, 1.3, ST[4], hgt=1.0)
        C = Layer(cw, chh, 'wheels%d' % k)
        C.c = F.c[y0:y0 + chh, x0:x0 + cw].copy()
        C.hgt = F.hgt[y0:y0 + chh, x0:x0 + cw].copy()
        C.nrm = F.nrm[y0:y0 + chh, x0:x0 + cw].copy()
        C.em = F.em[y0:y0 + chh, x0:x0 + cw].copy()
        frames.append(C)
    return frames


def _small_wheel(style: str, k: int) -> Layer:
    """One frame of a small spoked wheel, centre (11, 11) of a 23x23 canvas, drawn exactly like the static
    wheel of the vehicle image it covers, spokes turned by k/SMALL_FRAMES of one spoke period."""
    F = Layer(23, 23, '%s%d' % (style, k))
    c = 11
    if style == 'wheel_pilot':                       # loco leading truck (make_loco)
        n, rot = 8, -k * (2 * math.pi / 8) / SMALL_FRAMES
        F.ellipse(c, c, 10.5, 10.5, NI[1], hgt=0.5)
        F.ellipse(c, c, 9.0, 9.0, RD[0], hgt=0.45)
        F.ellipse(c, c, 7.6, 7.6, NI[0], hgt=0.2)
        F.ellipse(c, c, 2.4, 2.4, ST[2], hgt=0.7)
        for s in range(n):
            a = rot + s * 2 * math.pi / n
            F.line(c, c, c + math.cos(a) * 8, c + math.sin(a) * 8, RD[1])
    elif style == 'wheel_tender':                    # make_tender bogies
        n, rot = 8, -k * (2 * math.pi / 8) / SMALL_FRAMES
        F.ellipse(c, c, 9.5, 9.5, NI[1], hgt=0.5)
        F.ellipse(c, c, 8.0, 8.0, RD[0], hgt=0.45)
        F.ellipse(c, c, 6.6, 6.6, NI[0], hgt=0.2)
        for s in range(n):
            a = rot + s * 2 * math.pi / n
            F.line(c, c, c + math.cos(a) * 6.5, c + math.sin(a) * 6.5, RD[0])
        F.ellipse(c, c, 2.2, 2.2, ST[2], hgt=0.8)
        for a in range(200, 271, 10):
            F.px(c + int(round(math.cos(math.radians(a)) * 9)), c + int(round(math.sin(math.radians(a)) * 9)), CO[0])
    else:                                            # make_boxcar (9 dark spokes)
        n, rot = 9, -k * (2 * math.pi / 9) / SMALL_FRAMES
        F.ellipse(c, c, 9.5, 9.5, NI[1], hgt=0.5)
        F.ellipse(c, c, 8, 8, NI[2], hgt=0.45)
        F.ellipse(c, c, 2.5, 2.5, ST[2], hgt=0.7)
        for s in range(n):
            a = rot + s * 2 * math.pi / n
            F.line(c, c, c + math.cos(a) * 7, c + math.sin(a) * 7, NI[3])
    return F


def make_small_wheels() -> dict:
    return {st: [_small_wheel(st, k) for k in range(SMALL_FRAMES)]
            for st in ('wheel_pilot', 'wheel_tender', 'wheel_box')}


def make_tender():
    W, H = 196, 92
    L = Layer(W, H, 'tender')
    rail = H - 1
    x0, x1 = 6, 190
    top = 20
    body_bot = rail - 22
    rect_tone(L, x0, top, x1 - x0, body_bot - top, [NI[1], NI[2], NI[3], TE[1], TE[2]],
              lib.grad_v(body_bot - top, x1 - x0, 3.4, 1.0, 0.8), hgt=0.6)
    L.hline(x0, top, x1 - x0, TE[3])
    L.vline(x0, top, body_bot - top, CO[0])
    for x in range(x0 + 4, x1, 9):                                         # rivet rows
        L.px(x, top + 3, ST[1])
        L.px(x, body_bot - 3, ST[1])
    L.hline(x0, body_bot - 1, x1 - x0, NI[0])
    # coal heap with snow on top
    rng = np.random.default_rng(seed_of('coal'))
    prof = value_noise(x1 - x0, 1, 14, seed_of('coalp'), octaves=3)[0]
    for x in range(x0 + 2, x1 - 2):
        h = int(8 + prof[x - x0] * 10)
        for y in range(top - h, top):
            L.px(x, y, NI[1] if rng.random() < 0.6 else NI[2], hgt=0.7)
        L.px(x, top - h, SN[2])
        if rng.random() < 0.6:
            L.px(x, top - h + 1, SN[1])
    # number stencil + red band
    text(L, x0 + 70, top + 18, '2317', SN[2])
    L.hline(x0 + 60, top + 26, 40, RD[1])
    # bogies (two 2-axle trucks)
    for bc in (40, 150):
        L.rect(bc - 26, body_bot, 52, 7, NI[2], hgt=0.6)
        L.hline(bc - 26, body_bot, 52, ST[1])
        for wc in (bc - 14, bc + 14):
            L.ellipse(wc, rail - 9, 9.5, 9.5, NI[1], hgt=0.5)
            L.ellipse(wc, rail - 9, 8.0, 8.0, RD[0], hgt=0.45)
            L.ellipse(wc, rail - 9, 6.6, 6.6, NI[0], hgt=0.2)
            for a in range(0, 360, 45):
                L.line(wc, rail - 9, wc + math.cos(math.radians(a)) * 6.5,
                       rail - 9 + math.sin(math.radians(a)) * 6.5, RD[0])
            L.ellipse(wc, rail - 9, 2.2, 2.2, ST[2], hgt=0.8)
            for a in range(200, 271, 10):
                L.px(wc + int(round(math.cos(math.radians(a)) * 9)), rail - 9 + int(round(math.sin(math.radians(a)) * 9)),
                     CO[0])
    # buffers at the rear (right)
    for by in (body_bot + 1, body_bot + 6):
        L.rect(x1, by, 5, 3, ST[2])
    L.rect(0, body_bot + 2, 7, 3, NI[2])
    return L


def make_gondola():
    W, H = 180, 76
    L = Layer(W, H, 'gondola')
    rail = H - 1
    x0, x1 = 10, 170
    top, body_bot = 22, rail - 20
    for x in range(x0, x1):                                                 # steel sides, rust streaks
        c = RU[0] if (x - x0) % 16 else NI[2]
        L.rect(x, top, 1, body_bot - top, c, hgt=0.55)
    pg_noise = value_noise(x1 - x0, body_bot - top, 6, seed_of('gonrust'), octaves=3)
    m = pg_noise > 0.6
    L._put(m, x0, top, RU[1])
    L.hline(x0, top, x1 - x0, ST[2])
    L.hline(x0, top + 1, x1 - x0, NI[3])
    L.vline(x0, top, body_bot - top, CO[0])
    # load: scrap / rails under snow
    rng = np.random.default_rng(seed_of('scrap'))
    for k in range(40):
        sx = int(rng.integers(x0 + 2, x1 - 10))
        L.rect(sx, top - int(rng.integers(1, 6)), int(rng.integers(4, 14)), 2, NI[1])
    for x in range(x0 + 1, x1 - 1):
        if rng.random() < 0.7:
            L.px(x, top - 1 - int(rng.integers(0, 3)), SN[2])
    text(L, x0 + 12, top + 10, '61-044', SN[1])
    L.rect(x0 - 4, body_bot, x1 - x0 + 8, 5, NI[2], hgt=0.6)
    for wc in (x0 + 30, x1 - 30):
        L.ellipse(wc, rail - 9, 9.5, 9.5, NI[1], hgt=0.5)
        L.ellipse(wc, rail - 9, 7.5, 7.5, NI[2], hgt=0.45)
        L.ellipse(wc, rail - 9, 2.2, 2.2, ST[2], hgt=0.8)
    for bx in (0, x1 + 2):
        L.rect(bx, body_bot + 1, 8, 3, ST[2])
    return L


def make_boxcar():
    """A second covered wagon (grey-green paint, no seal) so the C-17 wagon is not the only one."""
    W, H = 196, 91
    L = Layer(W, H, 'boxcar')
    rail = H - 1
    x0, x1 = 12, 184
    body_bot = rail - 22
    body_top = body_bot - 58
    for x in range(x0, x1):
        c = TE[1] if (x - x0) % 4 else TE[0]
        L.rect(x, body_top, 1, body_bot - body_top, c, hgt=0.5)
    nz = value_noise(x1 - x0, body_bot - body_top, 5, seed_of('boxfade'), octaves=3)
    L._put(nz > 0.64, x0, body_top, TE[2])
    L._put(nz < 0.22, x0, body_top, NI[3])
    L.rect(x0, body_top, x1 - x0, 3, NI[2])
    L.rect(x0, body_bot - 4, x1 - x0, 4, NI[2])
    for px_ in (x0, x0 + 40, x1 - 44, x1 - 4):
        L.rect(px_, body_top, 4, body_bot - body_top, NI[2], hgt=0.62)
    for (ax, bx2) in ((x0 + 4, x0 + 40), (x1 - 40, x1 - 4)):
        L.line(ax, body_bot - 5, bx2 - 1, body_top + 3, NI[2])
        L.line(ax + 1, body_bot - 5, bx2, body_top + 3, NI[2])
    L.rect(80, body_top + 4, 40, body_bot - body_top - 9, TE[2], hgt=0.55)   # door
    L.rect(78, body_top - 1, 46, 2, NI[2])
    L.rect(78, body_bot - 5, 46, 2, NI[2])
    L.line(82, body_bot - 8, 118, body_top + 7, NI[3])
    text(L, x0 + 8, body_top + 12, '42-905', SN[2])
    L.vline(x0, body_top, body_bot - body_top, CO[0])
    for k in range(5):
        inset = [3, 1, 0, 0, 0][k]
        L.hline(x0 - 2 + inset, body_top - 1 - k, x1 - x0 + 4 - 2 * inset, NI[3] if k < 2 else SN[2], 0.7)
    L.hline(x0 + 2, body_top - 6, x1 - x0 - 4, SN[3])
    L.rect(x0 - 4, body_bot, x1 - x0 + 8, 6, NI[2], hgt=0.6)
    for wc in (x0 + 34, x1 - 34):
        L.ellipse(wc, rail - 9, 9.5, 9.5, NI[1], hgt=0.5)
        L.ellipse(wc, rail - 9, 8, 8, NI[2], hgt=0.45)
        L.ellipse(wc, rail - 9, 2.5, 2.5, ST[2], hgt=0.7)
        for a in range(0, 360, 40):
            L.line(wc, rail - 9, wc + math.cos(math.radians(a)) * 7, rail - 9 + math.sin(math.radians(a)) * 7, NI[3])
    for bx in (0, x1 + 4):
        L.rect(bx, body_bot + 1, 8, 4, NI[3])
        L.rect(bx + (0 if bx == 0 else 5), body_bot - 1, 3, 8, ST[2])
    return L


def make_tail_lamp():
    L = Layer(7, 9, 'tail_lamp')
    L.rect(0, 2, 7, 7, NI[1], hgt=0.6)
    L.rect(1, 3, 5, 5, RD[2], hgt=0.8, em=RD[3])
    L.rect(2, 4, 2, 2, RD[3], em=RD[3])
    L.hline(0, 1, 7, NI[2])
    L.rect(3, 0, 1, 2, NI[2])
    return L


def make_ledger_arm():
    """The freight ledger carried under the arm (dark cloth binding, page edges)."""
    L = Layer(8, 11, 'ledger_arm')
    L.rect(0, 0, 8, 11, RD[0], hgt=0.6)
    L.rect(1, 1, 6, 9, RU[1], hgt=0.7)
    L.vline(7, 1, 9, SN[1])                    # page block edge
    L.vline(6, 2, 7, SN[0])
    L.hline(1, 1, 5, RU[2])
    L.rect(2, 4, 3, 2, CO[1])                  # paper label on the cover
    return L


# =========================================================================== FX strips
def _puff_frames(n, size, cols, seed, rise=18.0, grow=1.9, drift=6.0, base_r=6.0, lumps=7, thin_from=0.45):
    frames = []
    rng = np.random.default_rng(seed)
    lobes = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.55, 1.0)) for _ in range(lumps)]
    W, H = size
    for k in range(n):
        t = k / (n - 1)
        F = Layer(W, H, 'puff%d' % k)
        r = base_r * (1 + (grow - 1) * t ** 0.7)
        cx = W * 0.5 + drift * t
        cy = H - base_r - 2 - rise * t ** 0.8
        circles = [(cx + lx * r * 0.9, cy + ly * r * 0.6, r * lr) for (lx, ly, lr) in lobes]
        m = pg.puffs(F, circles, cols, light=(-0.5, -0.8, 0.4), ambient=0.25, seed=seed + k)
        # thin out with an ordered dither as it ages (no alpha blending: crisp pixels)
        if t > thin_from:
            keep = bayer(W, H) > (t - thin_from) / (1 - thin_from) * 0.95
            F.c[~keep] = 0
        F.hgt[:] = 0
        frames.append(F)
    return frames


def make_fx():
    out = {}
    smoke = [NI[2], NI[3], TE[1], TE[2], ST[2], ST[3]]
    out['fx_puff'] = _puff_frames(12, (56, 60), smoke, seed_of('puff'), rise=34, grow=2.2, drift=10,
                                  base_r=7.0, lumps=8)
    steam = [ST[3], SN[0], SN[1], SN[2], SN[3], SN[4]]
    # cylinder cocks: low, wide jets along the rails
    frames = []
    for k in range(8):
        t = k / 7
        F = Layer(72, 28, 'steam%d' % k)
        rng = np.random.default_rng(seed_of('steam') + k)
        circles = []
        for i in range(10):
            u = i / 9
            circles.append((8 + u * (30 + 30 * t), 20 - u * (4 + 6 * t) + rng.uniform(-1, 1),
                            2.5 + u * (5 + 3 * t)))
        pg.puffs(F, circles, steam, light=(-0.4, -0.9, 0.5), ambient=0.4, seed=seed_of('steam') + k)
        if t > 0.5:
            keep = bayer(72, 28) > (t - 0.5) * 1.6
            F.c[~keep] = 0
        F.hgt[:] = 0
        frames.append(F)
    out['fx_steam'] = frames
    out['fx_whistle'] = _puff_frames(8, (30, 46), steam, seed_of('whistle'), rise=30, grow=2.4, drift=-4,
                                     base_r=3.0, lumps=6, thin_from=0.55)
    # snow sliding off the wagon roof: clumps falling + powder
    frames = []
    rng = np.random.default_rng(seed_of('snowdrop'))
    clumps = [(rng.uniform(2, 60), rng.uniform(0, 3), rng.uniform(1, 2.5)) for _ in range(14)]
    for k in range(8):
        t = k / 7
        F = Layer(64, 40, 'sd%d' % k)
        for (cx, cy, r) in clumps:
            y = cy + 34 * t * t * (0.7 + r * 0.2)
            if y > 38:
                continue
            F.ellipse(cx + t * 3, y, r * (1 - t * 0.4), r * (1 - t * 0.4), SN[3] if r > 1.6 else SN[2])
        if k >= 2:   # powder cloud near the roof edge
            for i in range(30):
                px_ = rng.uniform(0, 64)
                py_ = rng.uniform(0, 10 + k * 2)
                if rng.random() < 0.6 - t * 0.5:
                    F.px(px_, py_, SN[2])
        frames.append(F)
    out['fx_snowdrop'] = frames
    return out


# =========================================================================== build
def build():
    info = {}
    info['sky'] = lib.save(make_sky(), DIR + '/sky', normal=False)
    info['clouds'] = lib.save(make_clouds(), DIR + '/clouds', normal=False)
    info['yard'] = lib.save(make_yard(), DIR + '/yard', normal=True)
    info['fg'] = lib.save(make_fg(), DIR + '/fg', normal=False)
    info['loco'] = lib.save(make_loco(False), DIR + '/loco', normal=True)
    info['loco_hist'] = lib.save(make_loco(True), DIR + '/loco_hist', normal=True)
    info['loco_wheels'] = lib.strip(make_wheels(), DIR + '/loco_wheels', normal=True)
    for k, frames in make_small_wheels().items():
        info[k] = lib.strip(frames, DIR + '/' + k, normal=True)
    info['tender'] = lib.save(make_tender(), DIR + '/tender', normal=True)
    info['gondola'] = lib.save(make_gondola(), DIR + '/gondola', normal=True)
    info['boxcar'] = lib.save(make_boxcar(), DIR + '/boxcar', normal=True)
    info['tail_lamp'] = lib.save(make_tail_lamp(), DIR + '/tail_lamp', normal=False)
    info['ledger_arm'] = lib.save(make_ledger_arm(), DIR + '/ledger_arm', normal=True)
    for k, frames in make_fx().items():
        info[k] = lib.strip(frames, DIR + '/' + k, normal=False)
    return info


if __name__ == '__main__':
    import json
    print(json.dumps(build(), indent=1))
