"""cine_a1m1_berlin -- shot 4 of the A1 -> M1 transition: Berlin, early morning, snow.

A crane shot descends from the Great Hall dome (faint in the haze) past the rooftops to a street of
Gruenderzeit tenements and the Bauarchiv.  A tram stops and pulls away; Konrad, who got off on the far
side, crosses the pavement and enters the archive between the regime's banners.

Local set coordinates: x 0..1000, y -260..360 (street level / far pavement at y 262..276).
Writes assets/cinematics/a1m1/berlin/ (all original, deterministic):
  sky.png          642x362   overcast morning haze, faint warm east glow (right)         parallax 0
  dome.png         620x330   the Great Hall dome in haze, lantern with eagle on the globe  parallax .12/.2
  far.png         1000x200   distant roofs, firewalls, chimneys (haze)                      parallax .45
  street.png (+_n,_e) 1000x620  facades (Bauarchiv + tenements), pavements, tram tracks    parallax 1
  fg.png          1100x200   near lamp post + overhead tram wire                           parallax 1.15
  banner.png / banner_hist.png   strip 3: vertical banner (neutral: Reichssiegel on grey-black;
                   _hist: red with white disc and black swastika), slight sway
  relief.png / relief_hist.png   stone eagle above the portal (neutral: wreath with the Reichssiegel)
  door.png         strip 3: portal doors closed / ajar / open (+_e warm interior)
  jambs.png        portal jambs drawn above Konrad as he enters
  tram.png (+_e)   two-axle tram, lit windows with passengers, destination board
  tram_spark.png (+_e) strip 3: trolley pole spark
  smoke.png        strip 8: chimney smoke wisp (violet-grey)
  pigeons.png      strip 2: three pigeons on the cornice (head bob)
  window_on.png (+_e) a window that lights up during the shot
  queue.png        strip 2: three small figures queueing at the bakery
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_a1m1_lib as lib  # noqa: E402
from cine_a1m1_lib import Layer, BR, tone_put, rect_tone, bayer, value_noise, white_noise, seed_of  # noqa: E402
import pg  # noqa: E402

NI, VI, STN, OC, GL, SL, PA, SN = (BR[k] for k in ('night', 'violet', 'stone', 'ochre', 'glow', 'steel',
                                                   'patina', 'snow'))
RD = lib.SR_['red']
DIR = 'berlin'
SET_W = 1000
Y0 = -260                       # top of the street layer in set coordinates
PAVE_Y = 262                    # far pavement top (facade base line)
STREET_Y = 276
RAIL_FAR = (288, 292)
RAIL_NEAR = (302, 306)
ARCH_X0, ARCH_X1 = 210, 500     # Bauarchiv facade
PORTAL_CX = 355
DOOR_W, DOOR_H = 34, 50
DOOR_Y = PAVE_Y - 6 - DOOR_H    # door top (two steps of 3 px)
CHIMNEYS: list = []             # (x, y) of chimney tops in set coordinates (smoke anchors)


# =========================================================================== sky
def make_sky():
    W, H = 642, 362
    L = Layer(W, H, 'sky')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ramp = [NI[3], VI[1], VI[2], VI[3], SL[2], SL[3], SN[0], SN[1], SN[2]]
    v = np.clip(yy / 300.0, 0, 1) ** 0.9 * 7.6
    v += 0.9 * np.exp(-(((xx - 560) / 260.0) ** 2) - (((yy - 250) / 90.0) ** 2))
    v += (value_noise(W, H, 40, seed_of('bsky'), octaves=3) - 0.5) * 0.8
    tone_put(L, np.ones((H, W), bool), 0, 0, ramp, v)
    warm = np.exp(-(((xx - 590) / 150.0) ** 2) - (((yy - 268) / 26.0) ** 2))
    m = warm > 0.35
    tone_put(L, m, 0, 0, [SN[2], GL[4], GL[3]], (warm - 0.35) * 4.0)
    L.hgt[:] = 0
    return L


# =========================================================================== dome
def make_dome():
    """The Great Hall in morning haze: drum with colonnade, ribbed dome, lantern, eagle on the globe.
    Same in both symbol modes (Speer's final design crowned the dome with an eagle on a globe)."""
    W, H = 620, 330
    L = Layer(W, H, 'dome')
    cx = W // 2
    base_y = 300
    drum_h = 40
    R = 232
    dh = 196
    dy0 = base_y - drum_h
    haze = [VI[2], VI[3], SL[2], SL[3], SN[0]]
    rect_tone(L, cx - 300, base_y, 600, H - base_y, haze, 1.3)
    L.hline(cx - 300, base_y, 600, SN[0])
    rect_tone(L, cx - R - 8, dy0, 2 * R + 16, drum_h, haze, 1.7)
    for x in range(cx - R - 4, cx + R + 4, 9):
        L.rect(x, dy0 + 8, 3, drum_h - 12, VI[3])
        L.px(x + 3, dy0 + 8, SL[3])
    L.rect(cx - R - 10, dy0, 2 * R + 20, 4, SL[2])
    L.hline(cx - R - 10, dy0, 2 * R + 20, SN[0])

    def radius(y):
        k = (dy0 - y) / dh
        return R * max(0.0, 1 - k ** 1.9) ** 0.62
    ribs = [math.radians(a) for a in range(-84, 85, 12)]
    for y in range(dy0 - dh, dy0):
        r = radius(y)
        if r < 1:
            continue
        x0, x1 = int(round(cx - r)), int(round(cx + r))
        k = (dy0 - y) / dh
        for x in range(x0, x1 + 1):
            u = (x - cx) / r
            t = 1.7 + u * 0.75 + k * 0.25                         # lit from the right (east)
            idx = int(np.clip(round(t + (bayer(1, 1, x, y)[0, 0] - 0.5)), 0, 3))
            col = [VI[3], PA[2], SL[3], PA[3]][idx]
            if idx in (1, 3) and (x * 3 + y) % 5:                     # patina only as a hint
                col = [VI[3], SL[2], SL[3], SN[0]][idx]
            L.c[y, x] = col
        for th in ribs:                                              # meridian ribs
            xr = int(round(cx + r * math.sin(th)))
            if x0 < xr < x1:
                L.c[y, xr] = VI[3] if math.sin(th) < 0.3 else SL[2]
        L.c[y, x0] = VI[2]
        L.c[y, x1] = SN[0]
    # lantern + globe + eagle on top
    ly = dy0 - dh
    L.rect(cx - 15, ly - 24, 30, 26, VI[3])
    for x in range(cx - 13, cx + 13, 5):
        L.rect(x, ly - 20, 2, 16, SL[2])
    L.rect(cx - 18, ly - 27, 36, 4, SL[2])
    L.hline(cx - 18, ly - 28, 36, SN[0])
    gm, gx, gy = L.ellipse_mask(cx, ly - 35, 8, 8)
    L._put(gm, gx, gy, VI[3])
    L._put(lib.edge_of(gm) & (np.mgrid[0:gm.shape[0], 0:gm.shape[1]][1] > gm.shape[1] // 2), gx, gy, SL[3])
    eagle = lib._grid([
        '.........X.........',
        '........XXX........',
        'X........XX.......X',
        'XX......XXXX.....XX',
        'XXXX...XXXXXX..XXXX',
        '.XXXXXXXXXXXXXXXXX.',
        '..XXXXXXXXXXXXXXX..',
        '....XXX.XXXXX.XXX..',
        '........XXXXX......',
        '.......XX.X.XX.....',
    ])
    L._put(eagle, cx - 9, ly - 53, VI[2])
    L.px(cx, ly - 55, RD[2])                       # aircraft warning lamp (the scene blinks a light here)
    L.hgt[:] = 0
    return L


# =========================================================================== far roofs
def make_far():
    W, H = 1000, 200
    L = Layer(W, H, 'far')
    rng = np.random.default_rng(seed_of('bfar'))
    x = -10
    while x < W:
        bw = int(rng.integers(36, 96))
        top = int(rng.integers(50, 130))
        col = SL[2] if rng.random() < 0.5 else VI[3]
        L.rect(x, top, bw, H - top, col)
        kind = rng.random()
        if kind < 0.45:                                           # mansard
            for k in range(10):
                L.hline(x + k // 2, top - 1 - k, bw - k, col)
            L.hline(x + 5, top - 10, bw - 10, SN[0])
        elif kind < 0.7:                                          # gable / firewall
            for k in range(12):
                L.hline(x + k, top - 1 - k, max(1, bw - 2 * k), col)
        L.hline(x, top, bw, SN[0])
        for k in range(int(rng.integers(1, 4))):                  # chimneys
            cxp = x + int(rng.integers(4, max(5, bw - 6)))
            L.rect(cxp, top - 16, 3, 16, VI[2])
        for k in range(int(rng.integers(0, 3))):                  # an early light
            L.rect(x + int(rng.integers(4, max(5, bw - 6))), top + int(rng.integers(8, 60)), 2, 3, GL[1], em=GL[1])
        x += bw + int(rng.integers(-4, 6))
    L.hgt[:] = 0
    return L


# =========================================================================== street (main plane)
def _window(L, x, y, w, h, lit=False, curtain=False, frame=None, deep=True, seed=0):
    frame = STN[1] if frame is None else frame
    L.rect(x - 1, y - 1, w + 2, h + 2, frame, hgt=0.6)
    if lit:
        tone_put(L, np.ones((h, w), bool), x, y, [OC[4], GL[0], GL[1], GL[2]], lib.grad_v(h, w, 3.2, 1.0),
                 hgt=0.2, em=True)
        if curtain:
            L.rect(x, y, 2, h, OC[3], em=OC[3])
            L.rect(x + w - 2, y, 2, h, OC[3], em=OC[3])
    else:
        L.rect(x, y, w, h, NI[1] if deep else NI[2], hgt=0.15)
        L.px(x, y, SL[2])                               # cold sky reflection
        if w > 3:
            L.px(x + 1, y, SL[1])
    L.vline(x + w // 2, y, h, frame)                    # mullion
    L.hline(x, y + h // 3, w, frame)                    # transom
    L.hline(x - 2, y + h + 1, w + 4, SN[2], hgt=0.7)     # sill with snow
    L.hline(x - 2, y + h + 2, w + 4, STN[1])


def _tenement(L, x0, x1, top, floors, ground_h, base_col, seed, shop=None):
    """Gruenderzeit tenement: plaster facade with stucco cornices, window axes, balconies, mansard roof."""
    rng = np.random.default_rng(seed)
    w = x1 - x0
    y_ground = PAVE_Y - ground_h
    fh = (y_ground - top) // floors
    ly = top - Y0
    # plaster body with soot and damage
    nz = value_noise(w, PAVE_Y - top, 9, seed, octaves=3)
    t = base_col + (nz - 0.5) * 0.9 - np.repeat((np.arange(PAVE_Y - top) / (PAVE_Y - top))[:, None], w, 1) * 0.5
    tone_put(L, np.ones((PAVE_Y - top, w), bool), x0, ly, [VI[1], VI[2], VI[3], STN[1], STN[2], STN[3]], t,
             hgt=0.5)
    # flaking plaster revealing bricks (war damage, never repaired)
    for k in range(int(rng.integers(2, 5))):
        bx, by = int(rng.integers(x0 + 4, x1 - 20)), int(rng.integers(top + 10, y_ground - 20))
        m, mx, my = L.ellipse_mask(bx, by - Y0, rng.uniform(5, 12), rng.uniform(3, 7))
        brick = m & ((np.add.outer(np.arange(m.shape[0]), np.zeros(m.shape[1], int)) % 3) != 0)
        L._put(m, mx, my, OC[1])
        L._put(m & ~brick, mx, my, STN[0])
    # cornices (stucco bands) per floor + main cornice
    for f in range(floors + 1):
        yy = top + f * fh
        L.rect(x0, yy - Y0, w, 2, STN[3], hgt=0.8)
        L.hline(x0, yy - Y0 + 2, w, VI[1])
        L.hline(x0, yy - Y0 - 1, w, SN[1])
    L.rect(x0 - 3, top - Y0 - 6, w + 6, 6, STN[2], hgt=0.9)
    L.hline(x0 - 3, top - Y0 - 6, w + 6, SN[3])
    L.hline(x0 - 3, top - Y0 - 7, w + 6, SN[2])
    for k in range(x0, x1, 6):                                       # dentils
        L.px(k, top - Y0 - 1, VI[2])
    # mansard roof with dormers and chimneys + snow
    rh = 34
    for k in range(rh):
        inset = int(k * 0.55)
        L.hline(x0 - 2 + inset, top - Y0 - 7 - k, w + 4 - 2 * inset, NI[3] if k % 5 else VI[0], hgt=0.6)
    for k in range(rh):
        if k % 3 == 0:
            inset = int(k * 0.55)
            L.hline(x0 - 2 + inset, top - Y0 - 7 - k, w + 4 - 2 * inset, SN[2])
    for dx in range(x0 + 14, x1 - 20, 34):
        L.rect(dx, top - Y0 - 26, 12, 14, VI[1])
        L.rect(dx + 2, top - Y0 - 23, 8, 9, NI[1] if rng.random() < 0.7 else GL[1],
               em=GL[1] if rng.random() < 0.15 else None)
        L.hline(dx - 1, top - Y0 - 27, 14, SN[3])
    for k in range(int(rng.integers(2, 4))):
        cxp = int(rng.integers(x0 + 10, x1 - 14))
        CHIMNEYS.append([cxp + 4, top - 53])
        L.rect(cxp, top - Y0 - 50, 8, 26, OC[0], hgt=0.7)
        L.rect(cxp - 1, top - Y0 - 52, 10, 3, STN[1])
        L.hline(cxp - 1, top - Y0 - 53, 10, SN[3])
    # window axes
    axes = list(range(x0 + 10, x1 - 14, 26))
    for f in range(floors):
        yy = top + f * fh + 8
        for i, ax in enumerate(axes):
            lit = rng.random() < (0.16 if f > 0 else 0.1)
            _window(L, ax, yy - Y0, 12, fh - 14, lit=lit, curtain=lit and rng.random() < 0.5, seed=seed + f * 31 + i)
            if rng.random() < 0.18:                                  # stove pipe through a window
                L.rect(ax + 9, yy - Y0 - 4, 2, 8, NI[2])
            # stucco lintel
            L.hline(ax - 2, yy - Y0 - 3, 16, STN[3])
            L.px(ax + 6, yy - Y0 - 4, STN[3])
        # balconies on the 2nd floor every other axis
        if f == 1:
            for ax in axes[1::2]:
                by = top + (f + 1) * fh - 4
                L.rect(ax - 4, by - Y0, 20, 3, STN[2], hgt=0.9)
                L.hline(ax - 4, by - Y0 - 1, 20, SN[3])
                for k in range(ax - 4, ax + 16, 2):
                    L.vline(k, by - Y0 - 8, 7, NI[2])
                L.hline(ax - 4, by - Y0 - 9, 20, NI[2])
    # ground floor
    gy = y_ground - Y0
    L.rect(x0, gy, w, ground_h, VI[1], hgt=0.45)
    L.hline(x0, gy, w, STN[2])
    if shop:
        sx0, sx1, kind = shop
        L.rect(sx0, gy + 8, sx1 - sx0, ground_h - 14, NI[1])
        tone_put(L, np.ones((ground_h - 20, sx1 - sx0 - 6), bool), sx0 + 3, gy + 11,
                 [OC[3], OC[4], GL[0], GL[1], GL[2]], lib.grad_v(ground_h - 20, sx1 - sx0 - 6, 3.4, 1.4), em=True)
        for k in range(sx0 + 3, sx1 - 3, 14):
            L.vline(k, gy + 11, ground_h - 20, NI[2])
            L.em[gy + 11:gy + ground_h - 9, k] = 0
        # sign board
        L.rect(sx0, gy + 1, sx1 - sx0, 7, NI[2])
        lib.text(L, sx0 + 4, gy + 2, kind, GL[2] if kind != 'TABAK' else SN[3])
        # display: bread loaves / newspapers silhouettes at the bottom of the window
        for k in range(sx0 + 6, sx1 - 8, 7):
            L.rect(k, gy + ground_h - 12, 5, 3, OC[1])
            L.em[gy + ground_h - 12:gy + ground_h - 9, k:k + 5] = 0
    for ax in axes:
        if shop and shop[0] - 4 <= ax <= shop[1]:
            continue
        L.rect(ax, gy + 10, 12, ground_h - 16, NI[1])
        L.hline(ax - 1, gy + 9, 14, STN[1])
    # house door
    dxp = x0 + w // 2 - 7 if not shop else (shop[1] + 6 if shop[1] + 20 < x1 else x0 + 6)
    L.rect(dxp, gy + 12, 14, ground_h - 12, OC[0])
    L.vline(dxp + 7, gy + 12, ground_h - 12, NI[2])
    L.rect(dxp + 2, gy + 14, 10, 6, NI[2])
    return axes


def _archive(L, hist: bool):
    """Bauarchiv: sober stripped classicism -- rusticated base, giant pilasters, tall windows, attic with
    the inscription, portal with lanterns.  (Eagle relief, banners and doors are separate sprites.)"""
    x0, x1 = ARCH_X0, ARCH_X1
    top = 44
    w = x1 - x0
    ly = top - Y0
    h = PAVE_Y - top
    nz = value_noise(w, h, 11, seed_of('arch'), octaves=3)
    t = 3.0 + (nz - 0.5) * 0.7 - np.repeat((np.arange(h) / h)[:, None], w, 1) * 0.8
    tone_put(L, np.ones((h, w), bool), x0, ly, [VI[2], VI[3], STN[1], STN[2], STN[3], STN[4]], t, hgt=0.6)
    # vertical soot streaks
    rng = np.random.default_rng(seed_of('soot'))
    for k in range(40):
        sx = int(rng.integers(x0, x1))
        sy = int(rng.integers(top + 4, PAVE_Y - 40))
        L.rect(sx, sy - Y0, 1, int(rng.integers(6, 30)), STN[1] if rng.random() < 0.6 else VI[3])
    # rusticated base (ground floor): horizontal joints every 7 px
    base_top = PAVE_Y - 70
    for y in range(base_top, PAVE_Y, 7):
        L.hline(x0, y - Y0, w, VI[2])
        L.hline(x0, y - Y0 + 1, w, STN[3])
    for y in range(base_top, PAVE_Y, 14):
        for x in range(x0 + 12, x1, 24):
            L.vline(x + (12 if (y // 7) % 2 else 0), y - Y0, 7, VI[2])
    L.rect(x0 - 2, base_top - Y0 - 5, w + 4, 5, STN[4], hgt=0.9)
    L.hline(x0 - 2, base_top - Y0 - 6, w + 4, SN[3])
    # giant pilasters (piers) between tall windows
    piers = list(range(x0 + 6, x1 - 4, 36))
    for px_ in piers:
        L.rect(px_, top + 22 - Y0, 8, base_top - top - 27, STN[3], hgt=0.85)
        L.vline(px_, top + 22 - Y0, base_top - top - 27, STN[4])
        L.vline(px_ + 7, top + 22 - Y0, base_top - top - 27, VI[3])
        L.rect(px_ - 1, top + 20 - Y0, 10, 3, STN[4])
    # tall windows (two storeys merged) between piers, dark, a few lit (night clerks), with snow sills
    for i, px_ in enumerate(piers[:-1]):
        wx = px_ + 12
        lit = i in (2, 5)
        _window(L, wx, top + 34 - Y0, 16, 58, lit=lit, frame=VI[3])
        _window(L, wx, top + 104 - Y0, 16, 30, lit=(i == 1), frame=VI[3])
    # attic band with the inscription
    L.rect(x0, top - Y0, w, 20, STN[4], hgt=0.9)
    L.hline(x0, top - Y0, w, SN[3])
    L.hline(x0, top - Y0 + 19, w, VI[3])
    ins = lib.carved_mask('BAUARCHIV', spacing=3)
    ix = (x0 + x1) // 2 - ins.shape[1] // 2
    L._put(ins, ix, top - Y0 + 6, VI[2])
    L._put(np.roll(ins, 1, axis=0) & ~ins, ix, top - Y0 + 6, STN[2])
    L.rect(x0 - 4, top - Y0 - 6, w + 8, 6, STN[3], hgt=1.0)          # heavy cornice
    L.hline(x0 - 4, top - Y0 - 7, w + 8, SN[3])
    L.hline(x0 - 4, top - Y0 - 8, w + 8, SN[2])
    # flat roof edge / parapet with snow
    L.rect(x0 - 2, top - Y0 - 14, w + 4, 7, STN[2])
    L.hline(x0 - 2, top - Y0 - 15, w + 4, SN[3])
    # portal: deep stone surround (door sprite sits inside), steps
    pw = DOOR_W + 20
    pxl = PORTAL_CX - pw // 2
    L.rect(pxl, DOOR_Y - 14 - Y0, pw, DOOR_H + 14, STN[4], hgt=0.95)
    L.rect(pxl + 4, DOOR_Y - 10 - Y0, pw - 8, DOOR_H + 10, VI[1], hgt=0.3)
    L.rect(PORTAL_CX - DOOR_W // 2, DOOR_Y - Y0, DOOR_W, DOOR_H, NI[1], hgt=0.2)
    # transom window above the doors (lit, emission) with bars
    L.rect(PORTAL_CX - DOOR_W // 2, DOOR_Y - 9 - Y0, DOOR_W, 7, GL[1], em=GL[1])
    for x in range(PORTAL_CX - DOOR_W // 2 + 4, PORTAL_CX + DOOR_W // 2, 5):
        L.vline(x, DOOR_Y - 9 - Y0, 7, NI[2])
        L.em[DOOR_Y - 9 - Y0:DOOR_Y - 2 - Y0, x] = 0
    # steps (2) in front of the portal
    for k, (ex, ew) in enumerate(((pxl - 6, pw + 12), (pxl - 2, pw + 4))):
        y = PAVE_Y - 3 * (k + 1)
        L.rect(ex, y - Y0, ew, 3, STN[4] if k else STN[3], hgt=0.7)
        L.hline(ex, y - Y0, ew, SN[3])
    # lantern brackets either side of the portal (the lamps themselves glow: emission)
    for lx in (pxl - 12, pxl + pw + 4):
        L.rect(lx + 3, DOOR_Y + 2 - Y0, 2, 10, NI[2])
        L.rect(lx, DOOR_Y - 8 - Y0, 8, 11, NI[2])
        L.rect(lx + 1, DOOR_Y - 7 - Y0, 6, 8, GL[2], em=GL[3])
        L.hline(lx - 1, DOOR_Y - 9 - Y0, 10, SN[3])
    # small enamel sign right of the portal: opening hours
    L.rect(pxl + pw + 16, PAVE_Y - 44 - Y0, 14, 10, SN[3])
    L.hline(pxl + pw + 18, PAVE_Y - 41 - Y0, 10, NI[2])
    L.hline(pxl + pw + 18, PAVE_Y - 38 - Y0, 8, NI[2])


def _street(L):
    w = SET_W
    # far pavement: granite slabs with snow, curb
    py0, py1 = PAVE_Y - Y0, STREET_Y - Y0
    nz = value_noise(w, py1 - py0, 10, seed_of('pave'), octaves=3)
    tone_put(L, np.ones((py1 - py0, w), bool), 0, py0, [VI[2], VI[3], SN[0], SN[1], SN[2]], 1.8 + nz * 2.0,
             hgt=0.4)
    for x in range(0, w, 16):
        L.vline(x, py0, py1 - py0, VI[2])
    L.rect(0, py1 - 2, w, 3, STN[3], hgt=0.7)                       # curb
    L.hline(0, py1 - 2, w, SN[3])
    # snow heaps along the curb (shovelled)
    rng = np.random.default_rng(seed_of('heaps'))
    for k in range(28):
        hx = int(rng.integers(0, w))
        m, mx, my = L.ellipse_mask(hx, py1 - 2, rng.uniform(6, 16), rng.uniform(2, 4))
        L._put(m, mx, my, SN[2], hgt=0.6)
        L._put(m & (np.arange(m.shape[0])[:, None] < m.shape[0] // 2), mx, my, SN[3])
    # street: cobbles in offset rows, trodden snow in the wheel ruts between and beside the rails
    sy0, sy1 = STREET_Y - Y0 + 1, 360 - Y0
    h = sy1 - sy0
    depth = np.repeat((np.arange(h) / h)[:, None], w, 1)
    cob = white_noise(w, h, seed_of('cob'))
    t = 1.6 + (cob - 0.5) * 0.5 - depth * 0.5
    tone_put(L, np.ones((h, w), bool), 0, sy0, [NI[3], VI[1], VI[2], VI[3]], t, hgt=0.35, dither=False)
    for y in range(sy0, sy1, 3):                                    # cobble joints
        for x in range((y // 3) % 2 * 2, w, 4):
            L.px(x, y, NI[2])
    # trodden snow as long horizontal streaks (wheel ruts run along the street)
    rng0 = np.random.default_rng(seed_of('ruts'))
    streak = np.zeros((h, w), bool)
    for r in range(h):
        y = sy0 + r + Y0
        if RAIL_FAR[0] - 1 <= y <= RAIL_FAR[1] + 1 or RAIL_NEAR[0] - 1 <= y <= RAIL_NEAR[1] + 1:
            continue
        line = value_noise(w, 1, int(rng0.integers(18, 40)), seed_of('rut%d' % r), octaves=2)[0]
        thr = 0.56 + 0.08 * math.sin(r * 0.9)
        streak[r] = line > thr
    tone_put(L, streak, 0, sy0, [VI[3], SN[0], SN[1]], 1.2 - depth * 0.9 + (white_noise(w, h, 7) - 0.5) * 0.6)
    for (ra, rb) in (RAIL_FAR, RAIL_NEAR):
        L.rect(0, ra - Y0 + 1, w, rb - ra - 1, NI[2])               # groove between the rail heads
        for y in (ra, rb):
            L.hline(0, y - Y0, w, SL[4], hgt=0.7)
            L.hline(0, y - Y0 + 1, w, NI[1])
    rng = np.random.default_rng(seed_of('heaps2'))
    # puddles reflecting the lamps (dark; light comes from the scene lights + normal map)
    for k in range(8):
        px_ = int(rng.integers(20, w - 40))
        py_ = int(rng.integers(sy0 + 4, sy0 + 40))
        m, mx, my = L.ellipse_mask(px_, py_, rng.uniform(8, 20), rng.uniform(1.5, 2.5))
        L._put(m, mx, my, NI[2], hgt=0.1)


def make_street(hist: bool):
    CHIMNEYS.clear()
    H = 360 - Y0
    L = Layer(SET_W, H, 'street')
    # buildings left of the archive (corner house, darker), the archive, tenements to the right
    _tenement(L, -6, ARCH_X0 - 2, 70, 4, 52, 2.4, seed_of('t0'))
    _archive(L, hist)
    _tenement(L, ARCH_X1 + 2, 680, 62, 5, 50, 2.9, seed_of('t1'), shop=(560, 640, 'BAECKEREI'))
    # side street gap 680..726 (deeper city + dome visible through it): leave transparent
    _tenement(L, 726, SET_W + 6, 58, 5, 50, 2.6, seed_of('t2'), shop=(780, 836, 'TABAK'))
    # firewall of the corner house at the gap with a faded painted sign
    L.rect(726, 40 - Y0, 10, PAVE_Y - 40, VI[1])
    _street(L)
    # tram stop sign (H) on the far pavement, gas lamp posts
    sx = 520
    L.rect(sx, PAVE_Y - 54 - Y0, 2, 54, NI[2], hgt=0.7)
    m, mx, my = L.ellipse_mask(sx + 1, PAVE_Y - 58 - Y0, 6, 6)
    L._put(m, mx, my, GL[3] if False else SN[3], hgt=0.8)
    L._put(lib.edge_of(m), mx, my, NI[2])
    hm = lib.text_mask('H')
    L._put(hm, sx, PAVE_Y - 61 - Y0, NI[1])
    for lx in (150, 640, 905):
        L.rect(lx, PAVE_Y - 66 - Y0, 3, 66, NI[2], hgt=0.7)
        L.vline(lx, PAVE_Y - 66 - Y0, 66, SL[2])
        L.rect(lx - 3, PAVE_Y - 78 - Y0, 9, 12, NI[2])
        L.rect(lx - 2, PAVE_Y - 76 - Y0, 7, 8, GL[2], em=GL[3])
        L.hline(lx - 4, PAVE_Y - 79 - Y0, 11, SN[3])
        L.px(lx + 1, PAVE_Y - 81 - Y0, NI[2])
    # tram overhead contact wire (along the street) with hangers to wall rosettes
    wy = 148 - Y0
    L.hline(0, wy, SET_W, NI[1])
    for x in range(30, SET_W, 120):
        L.px(x, wy - 1, NI[2])
    pg.snow_caps(L, [SN[1], SN[2], SN[3]], depth=1, seed=seed_of('bsnow'), coverage=0.6)
    return L


def make_fg():
    W, H = 1100, 200
    L = Layer(W, H, 'fg')
    # a near cast-iron lamp post (right side of the end frame) and a snowy railing piece
    x = 868
    L.rect(x, 20, 5, 180, NI[0])
    L.rect(x - 1, 60, 7, 4, NI[1])
    L.rect(x - 6, 6, 17, 16, NI[0])
    L.rect(x - 4, 9, 13, 10, OC[2], em=GL[2])
    L.hline(x - 7, 5, 19, SN[2])
    for k in range(40, 200, 30):
        L.hline(x, k, 5, NI[1])
    for k in range(0, W, 7):                                          # snow bank at the very bottom
        h = 10 + int(6 * math.sin(k * 0.05) + 4 * math.sin(k * 0.13))
        L.rect(k, H - h, 7, h, NI[1])
        L.hline(k, H - h, 7, VI[1])
    return L


# =========================================================================== sprites
def make_banner(hist: bool):
    frames = []
    W, H = 24, 96
    for k in range(3):
        F = Layer(W, H, 'banner%d' % k)
        sway = [0, 1, 0][k]
        for y in range(H):
            off = int(round(sway * (y / H) ** 2 * 2))
            u = y / H
            for x in range(W - 2):
                fold = math.sin((x + off) * 0.9 + k) * 0.5 + (0.5 if x in (6, 7, 15, 16) else 0)
                if hist:
                    ramp = [RD[0], RD[1], RD[2], RD[3]]
                    t = 2.0 - fold * 0.8 - u * 0.4
                else:
                    ramp = [NI[0], NI[1], NI[2], VI[1]]
                    t = 1.8 - fold * 0.8 - u * 0.3
                idx = int(np.clip(round(t + (bayer(1, 1, x, y)[0, 0] - 0.5) * 0.8), 0, 3))
                F.px(x + 1 + off, y, ramp[idx])
        # pole at the top
        F.rect(0, 0, W, 2, NI[2])
        F.hline(0, 0, W, SN[3])
        # emblem disc
        d = lib.disc_mask(17)
        ox, oy = 4 + sway, 26
        F._put(d, ox, oy, SN[4] if hist else SN[3])
        if hist:
            sw = lib.swastika(3, 3, 2)
            F._put(sw, ox + (17 - sw.shape[1]) // 2, oy + (17 - sw.shape[0]) // 2, NI[0])
        else:
            F._put(d, ox, oy, NI[0])
            F._put(lib.edge_of(d), ox, oy, SN[2])
            rs = lib.REICHSSIEGEL_11
            F._put(rs, ox + 3, oy + 3, SN[3])
        # fringe at the bottom
        for x in range(1, W - 1, 2):
            F.px(x + sway, H - 1, SN[1] if not hist else RD[0])
        frames.append(F)
    return frames


def make_relief(hist: bool):
    """Stone eagle relief above the portal (wings spread, head to the viewer's left, wreath in the claws)."""
    W, H = 52, 34
    L = Layer(W, H, 'relief')
    body = lib._grid([
        '.....................XXX......................',
        '....................XXXX......................',
        '...................XXXX.......................',
        'XX.................XXXX.....................XX',
        'XXXX..............XXXXXX..................XXXX',
        '.XXXXX...........XXXXXXXX...............XXXXX.',
        '..XXXXXXX.......XXXXXXXXXX............XXXXXX..',
        '...XXXXXXXXXX..XXXXXXXXXXXX.......XXXXXXXXX...',
        '....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX....',
        '.....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.....',
        '......XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX......',
        '........XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX........',
        '..........XXXXXXXXXXXXXXXXXXXXXXXXXX..........',
        '.............XXXXX.XXXXXXXX.XXXXX.............',
        '...................XXXXXXXX...................',
        '..................XXXXXXXXXX..................',
        '..................XX.XXXX.XX..................',
    ])
    bh, bw = body.shape
    ox = (W - bw) // 2
    L._put(body, ox, 0, STN[3], hgt=0.9)
    # feather steps: darker lines across the wings
    for k in range(4, bh - 4, 2):
        row = body[k]
        for x in range(bw):
            if row[x] and (x < 18 or x > 28) and (x + k) % 4 == 0:
                L.px(ox + x, k, STN[2])
    top = body & ~np.vstack([np.zeros((1, bw), bool), body[:-1]])
    L._put(top, ox, 0, STN[4])
    L.px(ox + 20, 1, NI[2])                                   # eye
    # wreath with the emblem
    d = lib.disc_mask(15)
    ring = lib.edge_of(d) | lib.edge_of(lib.erode(d, 1))
    wy = bh - 1
    L._put(ring, W // 2 - 7, wy, STN[3], hgt=0.9)
    if hist:
        sw = lib.swastika(2, 2, 1)
        L._put(sw, W // 2 - sw.shape[1] // 2, wy + 7 - sw.shape[0] // 2, STN[2])
    else:
        rs = lib.REICHSSIEGEL_11[:, 2:9]
        L._put(rs[1:10], W // 2 - 3, wy + 3, STN[2])
    # shadow side (lower right edges) for depth
    sh = L.alpha() & ~np.vstack([L.alpha()[1:], np.zeros((1, W), bool)])
    L.c[sh] = VI[2]
    return L


def make_door():
    frames = []
    W, H = DOOR_W, DOOR_H
    for k in range(3):
        F = Layer(W, H, 'door%d' % k)
        # warm interior visible through the opening
        open_w = [0, 8, 16][k]
        F.rect(0, 0, W, H, NI[1])
        if open_w:
            F.rect(W // 2 - open_w, 0, open_w * 2, H, GL[1], em=GL[1])
            F.rect(W // 2 - open_w, H - 6, open_w * 2, 6, OC[3], em=OC[3])
        # two leaves: dark bronze panels, each leaf narrows as it opens (swinging inward)
        lw = W // 2 - open_w
        for side in (0, 1):
            if lw <= 0:
                continue
            x = 0 if side == 0 else W - lw
            F.rect(x, 0, lw, H, OC[0], hgt=0.6)
            F.rect(x + 1, 2, max(1, lw - 2), H // 2 - 4, NI[3], hgt=0.5)
            F.rect(x + 1, H // 2 + 1, max(1, lw - 2), H // 2 - 4, NI[3], hgt=0.5)
            F.vline(x if side == 0 else x + lw - 1, 0, H, PA[2])      # bronze edge (patina)
            if lw > 4:
                F.rect(x + (lw - 3 if side == 0 else 1), H // 2 - 2, 2, 5, GL[0])   # handle
        frames.append(F)
    return frames


def make_jambs():
    """Portal jambs + lintel drawn ABOVE Konrad while he steps into the doorway."""
    W = DOOR_W + 20
    H = DOOR_H + 14
    L = Layer(W, H, 'jambs')
    L.rect(0, 0, 10, H, STN[4], hgt=0.95)
    L.rect(W - 10, 0, 10, H, STN[4], hgt=0.95)
    L.rect(0, 0, W, 10, STN[4], hgt=0.95)
    L.rect(4, 4, 6, H - 4, VI[1])
    L.rect(W - 10, 4, 6, H - 4, VI[1])
    L.rect(4, 4, W - 8, 6, VI[1])
    L.vline(0, 0, H, STN[3])
    L.hline(0, 0, W, SN[3])
    return L


def make_tram():
    W, H = 214, 92
    L = Layer(W, H, 'tram')
    rail = H - 1
    x0, x1 = 6, 208
    body_top, body_bot = 16, rail - 10
    # lower body ochre, cream window band, dark roof
    rect_tone(L, x0, body_top + 34, x1 - x0, body_bot - body_top - 34, [OC[1], OC[2], OC[3], OC[4]],
              lib.grad_v(body_bot - body_top - 34, x1 - x0, 2.6, 1.2), hgt=0.6)
    rect_tone(L, x0, body_top + 6, x1 - x0, 28, [STN[3], STN[4], STN[5], GL[4]], 2.0, hgt=0.6)
    L.rect(x0 - 2, body_top, x1 - x0 + 4, 6, NI[2], hgt=0.8)
    L.hline(x0 - 2, body_top, x1 - x0 + 4, SN[3])
    L.rect(x0 + 30, body_top - 4, x1 - x0 - 60, 4, NI[2])
    L.hline(x0 + 30, body_top - 4, x1 - x0 - 60, SN[2])
    # windows lit warm with passenger silhouettes (hats, heads)
    rng = np.random.default_rng(seed_of('tram'))
    for i, wx in enumerate(range(x0 + 18, x1 - 24, 20)):
        L.rect(wx, body_top + 9, 16, 20, NI[1])
        tone_put(L, np.ones((18, 14), bool), wx + 1, body_top + 10, [OC[4], GL[0], GL[1], GL[2]],
                 lib.grad_v(18, 14, 3.0, 1.2), em=True)
        if rng.random() < 0.75:
            px_ = wx + int(rng.integers(2, 9))
            hat = rng.random() < 0.5
            L.rect(px_, body_top + 16, 5, 13, NI[1])
            L.rect(px_ + 1, body_top + 13, 3, 3, NI[1])
            if hat:
                L.rect(px_, body_top + 13, 5, 1, NI[1])
            L.em[body_top + 13:body_top + 29, px_:px_ + 5] = 0
    # front (left end, moving left): driver's windows, destination board, headlight
    L.rect(x0, body_top + 6, 12, 40, STN[4])
    L.rect(x0 + 1, body_top + 9, 9, 18, NI[1])
    L.rect(x0 + 2, body_top + 10, 6, 15, GL[0], em=GL[0])
    L.rect(x0 + 2, body_top + 15, 4, 10, NI[1])                    # the driver
    L.em[body_top + 15:body_top + 25, x0 + 2:x0 + 6] = 0
    L.rect(x0 + 24, body_top - 3, 52, 8, NI[1])
    lib.text(L, x0 + 26, body_top - 2, '3 GR.HALLE', GL[3], em=GL[3])
    L.rect(x0 - 3, body_bot - 14, 5, 5, GL[3], em=GL[4])            # headlight
    # doors (folding, middle and rear) on this side are closed; boarding happens on the far side
    for dxp in (x0 + 96, x1 - 30):
        L.rect(dxp, body_top + 8, 14, body_bot - body_top - 8, OC[0])
        L.vline(dxp + 7, body_top + 8, body_bot - body_top - 8, NI[2])
    # fleet number + coat stripe
    lib.text(L, x0 + 40, body_bot - 12, '3418', SN[3])
    L.hline(x0, body_top + 34, x1 - x0, NI[2])
    # truck, skirts, wheels hint, fender
    L.rect(x0 + 4, body_bot, x1 - x0 - 8, 4, NI[2])
    for wc in (x0 + 44, x1 - 44):
        L.ellipse(wc, rail - 4, 5, 4, NI[0])
    L.rect(x0 - 4, body_bot - 4, 6, 6, NI[2])
    # trolley pole base on the roof
    L.rect(x1 - 70, body_top - 8, 16, 4, NI[2])
    # snow on the roof
    L.hline(x0 + 32, body_top - 5, x1 - x0 - 64, SN[3])
    L.hline(x0, body_top - 1, x1 - x0, SN[2])
    return L


def make_tram_pole():
    """Trolley pole from the roof base to the wire with the contact head; frame 1/2 add the spark."""
    frames = []
    W, H = 70, 64
    for k in range(3):
        F = Layer(W, H, 'pole%d' % k)
        F.line(4, H - 2, W - 8, 4, NI[1])
        F.line(5, H - 2, W - 7, 4, NI[2])
        F.rect(W - 10, 2, 6, 3, NI[1])
        if k:
            for (dx, dy) in ((0, 0), (1, -1), (-1, 1), (2, 0), (0, -2), (-2, -1)) if k == 1 else ((0, 0), (1, 1), (-1, -1)):
                F.px(W - 7 + dx, 2 + dy, SN[4], em=SN[4])
            F.px(W - 7, 2, GL[4], em=GL[4])
        frames.append(F)
    return frames


def make_smoke():
    frames = []
    cols = [VI[2], VI[3], SL[2], SL[3], SN[0]]
    rng = np.random.default_rng(seed_of('bsmoke'))
    lobes = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0.5, 1)) for _ in range(9)]
    for k in range(8):
        t = k / 8
        F = Layer(36, 64, 'smoke%d' % k)
        circles = []
        for i, (lx, ly, lr) in enumerate(lobes):
            u = (i / len(lobes) + t) % 1.0
            circles.append((14 + lx * 3 + u * 10, 60 - u * 54, (1.5 + u * 5.5) * lr))
        pg.puffs(F, circles, cols, light=(0.6, -0.7, 0.4), ambient=0.3, seed=seed_of('bs') + k)
        keep = bayer(36, 64) > np.clip((60 - np.arange(64)[:, None] - 30) / 40.0, 0, 0.8)
        F.c[~keep] = 0
        F.hgt[:] = 0
        frames.append(F)
    return frames


def make_pigeons():
    frames = []
    for k in range(2):
        F = Layer(30, 6, 'pig%d' % k)
        for i, x in enumerate((2, 12, 23)):
            bob = 1 if (k + i) % 2 else 0
            F.rect(x, 2, 5, 3, VI[1])
            F.px(x + 5, 2, VI[1])
            F.px(x - 1 + (0 if i != 1 else 6), 1 + bob, VI[2])           # head
            F.px(x + 1, 2, SL[3])
        frames.append(F)
    return frames


def make_window_on():
    """A tenement window (12x16, same as the facade windows) whose light comes on during the shot."""
    L = Layer(12, 16, 'window_on')
    tone_put(L, np.ones((16, 12), bool), 0, 0, [OC[4], GL[0], GL[1], GL[2]], lib.grad_v(16, 12, 3.0, 1.0), em=True)
    L.vline(6, 0, 16, STN[1])
    L.em[:, 6] = 0
    L.hline(0, 5, 12, STN[1])
    L.em[5, :] = 0
    L.rect(1, 7, 3, 9, NI[1])                                             # someone at the window
    L.rect(2, 5, 2, 2, NI[1])
    L.em[5:16, 1:4] = 0
    return L


def make_queue():
    frames = []
    for k in range(2):
        F = Layer(30, 30, 'queue%d' % k)
        for i, x in enumerate((2, 11, 20)):
            h = [26, 22, 25][i]
            shift = 1 if (k + i) % 2 == 0 else 0
            F.rect(x, 30 - h, 7, h, NI[1])
            F.rect(x + 1 + shift, 30 - h - 4, 5, 5, NI[1])
            if i != 1:
                F.rect(x, 30 - h - 5, 7, 2, NI[2])                        # hats
            F.vline(x + 6, 30 - h + 2, h - 6, VI[2])                    # rim from the shop light
        frames.append(F)
    return frames


# =========================================================================== build
def build():
    info = {}
    info['sky'] = lib.save(make_sky(), DIR + '/sky', normal=False)
    info['dome'] = lib.save(make_dome(), DIR + '/dome', normal=False)
    info['far'] = lib.save(make_far(), DIR + '/far', normal=False)
    info['street'] = lib.save(make_street(False), DIR + '/street', normal=True)
    info['fg'] = lib.save(make_fg(), DIR + '/fg', normal=False)
    info['banner'] = lib.strip(make_banner(False), DIR + '/banner', normal=False)
    info['banner_hist'] = lib.strip(make_banner(True), DIR + '/banner_hist', normal=False)
    info['relief'] = lib.save(make_relief(False), DIR + '/relief', normal=True)
    info['relief_hist'] = lib.save(make_relief(True), DIR + '/relief_hist', normal=True)
    info['door'] = lib.strip(make_door(), DIR + '/door', normal=False)
    info['jambs'] = lib.save(make_jambs(), DIR + '/jambs', normal=True)
    info['tram'] = lib.save(make_tram(), DIR + '/tram', normal=True)
    info['tram_pole'] = lib.strip(make_tram_pole(), DIR + '/tram_pole', normal=False)
    info['smoke'] = lib.strip(make_smoke(), DIR + '/smoke', normal=False)
    info['pigeons'] = lib.strip(make_pigeons(), DIR + '/pigeons', normal=False)
    info['window_on'] = lib.save(make_window_on(), DIR + '/window_on', normal=False)
    info['queue'] = lib.strip(make_queue(), DIR + '/queue', normal=False)
    info['geometry'] = {'set_w': SET_W, 'y0': Y0, 'pave_y': PAVE_Y, 'street_y': STREET_Y,
                        'rail_far': list(RAIL_FAR), 'rail_near': list(RAIL_NEAR), 'arch': [ARCH_X0, ARCH_X1],
                        'portal_cx': PORTAL_CX, 'door': [PORTAL_CX - DOOR_W // 2, DOOR_Y, DOOR_W, DOOR_H],
                        'chimneys': CHIMNEYS, 'wire_y': 148}
    return info


if __name__ == '__main__':
    import json
    print(json.dumps(build(), indent=1))
