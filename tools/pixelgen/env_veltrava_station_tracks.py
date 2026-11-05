"""env_veltrava_station_tracks -- tracks, trains, island canopy and the platform floor of L_C3_Station.

Depth bands (screen y = world y; oblique Mode B, tracks run horizontally, FOUR-RAIL dual gauge everywhere:
1520 mm outer pair + 1435 mm inner pair, the inner pair closer together):
    198..210  far edge strip behind track 4 (station side)              layer 'far_track'  parallax 0.86
    210..226  track 4 (German delegation train)  rails 212/215/221/224  layer 'far_track'  parallax 0.86
    226..244  island platform (surface, coping, front wall) + canopy    layer 'island'     parallax 0.93
    244..261  track 5 (Soviet train, courier wagon 4) rails 246/249/256/259   layer 'ground' parallax 1
    262..265  platform edge coping; 265..360 walkable platform (under our canopy)
Trains are layers (not props): they stand entirely behind the walkable band, actors are always in front.
"""
from __future__ import annotations

import math

import numpy as np

from env_veltrava_lib import (Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, CLEAR, UP, bayer, value_noise, dmask,
                              ladder_paint, ladder_shift, text, text_width, text_center, cyl_normal, flat_normal,
                              snow_top, snow_lip, stains, figure, tiny_person, layer_w, arch_mask, put_mask)

W = 1920
FAR_RAILS = (212, 215, 221, 224)
NEAR_RAILS = (246, 249, 256, 259)
PLATFORM_EDGE = 262
ISLAND = dict(surf=(226, 233), coping=(233, 236), wall=(236, 244))
P_FAR, P_ISL = 0.86, 0.93


# =========================================================================== shared
def four_rail_track(L, x0, x1, rails, sleeper_top, sleeper_bot, seed=0, snow=0.5, step=11, ballast=None,
                    dark=False):
    """Dual-gauge track: long sleepers carrying four rails (outer 1520 pair, inner 1435 pair)."""
    rng = np.random.default_rng(seed)
    ballast = ballast if ballast is not None else [NI[3], IR[1], IR[2], SL[1]]
    nz = value_noise(x1 - x0 + 2, sleeper_bot - sleeper_top + 4, 7, seed=seed, octaves=2)
    for y in range(sleeper_top - 1, sleeper_bot + 1):
        for x in range(x0, x1):
            v = nz[y - sleeper_top + 1, x - x0]
            c = ballast[0] if v < 0.38 else (ballast[1] if v < 0.62 else ballast[2])
            if not dark and snow > 0 and v > 1 - snow * 0.55:
                c = SN[0] if v < 1 - snow * 0.3 else SN[1]
            L.px(x, y, c, 0.2)
    off = int(rng.integers(0, step))
    for sx in range(x0 - off, x1, step):
        sxx = sx + int(rng.integers(-1, 2))
        top, body, low = (CR[1], CR[0], NI[3]) if rng.random() < 0.85 else (CR[2], CR[1], CR[0])
        L.rect(sxx, sleeper_top, 5, sleeper_bot - sleeper_top, body, hgt=0.35)
        L.hline(sxx, sleeper_top, 5, top, 0.4)
        L.vline(sxx + 4, sleeper_top, sleeper_bot - sleeper_top, low, 0.3)
        if not dark and rng.random() < 0.55:
            L.hline(sxx, sleeper_top + int(rng.integers(0, 3)), 4, SN[1], 0.42)
    for ry in rails:
        L.hline(x0, ry - 1, x1 - x0, IR[2], 0.55)          # rail head top
        L.hline(x0, ry, x1 - x0, IR[4], 0.6)               # worn head (catches the sky)
        L.hline(x0, ry + 1, x1 - x0, NI[1], 0.3)           # web shadow
        for x in range(x0, x1):
            n = (x * 7 + ry * 13) % 29
            if n < 3:
                L.px(x, ry, SK[1])
            elif n == 14:
                L.px(x, ry - 1, IR[3])
    flat_normal(L, x0, sleeper_top - 1, x1 - x0, sleeper_bot - sleeper_top + 2, UP)
    for ry in rails:
        flat_normal(L, x0, ry - 1, x1 - x0, 1, (0, 0.8, 0.6))
        flat_normal(L, x0, ry + 1, x1 - x0, 1, (0, -0.4, 0.9))


def bogie(L, cx, wheel_y, r=7, frame=None, convertible=False, rim=None):
    """Two-axle bogie seen from the side: wheels on wheel_y (bottom), frame, coil springs, axle boxes.
    convertible: gauge-changing bogie with the visible second wheel-set notch + gauge plate."""
    frame = frame if frame is not None else [NI[2], IR[1], IR[2], IR[3]]
    rim = rim if rim is not None else IR[4]
    span = int(r * 2.6)
    cy = wheel_y - r
    for wx in (cx - span // 2 - r // 2, cx + span // 2 + r // 2):
        L.ellipse(wx, cy + 0.5, r + 0.5, r + 0.5, NI[1], hgt=0.55)
        L.ellipse(wx, cy + 0.5, r - 1, r - 1, NI[2], hgt=0.5)
        L.ellipse(wx, cy + 0.5, 2.2, 2.2, IR[3], hgt=0.7)
        for a in range(-70, 71, 14):
            L.px(wx + int(round(math.cos(math.radians(a)) * r)), int(round(cy + 0.5 + math.sin(math.radians(a)) * r)),
                 rim)
        L.rect(wx - 3, cy - 3, 7, 5, frame[2], hgt=0.7)       # axle box
        L.hline(wx - 3, cy - 3, 7, frame[3])
        cyl_normal(L, wx - r, cy - r, 2 * r + 1, 2 * r + 1)
    fx0, fx1 = cx - span - r, cx + span + r
    fy = cy - r + 1
    L.rect(fx0, fy, fx1 - fx0, 4, frame[1], hgt=0.7)       # side frame
    L.hline(fx0, fy, fx1 - fx0, frame[3])
    L.hline(fx0, fy + 3, fx1 - fx0, frame[0])
    L.vline(fx1 - 1, fy, 4, rim)
    for sx in (cx - 3, cx + 2):                               # bolster coil springs
        for k in range(5):
            L.px(sx + (k % 2), fy - 1 - k, frame[2])
    L.rect(cx - 5, fy - 6, 11, 3, frame[1], hgt=0.7)       # bolster
    L.hline(cx - 5, fy - 6, 11, frame[3])
    for wx in (cx - span // 2 - r // 2, cx + span // 2 + r // 2):  # brake shoes
        L.rect(wx + r - 1, cy - 2, 2, 5, LA[0])
    if convertible:
        # second wheel-set notch: open U-guides in the frame beside each axle (the other gauge position)
        for nx in (fx0 + 2, fx1 - 7):
            L.rect(nx, fy + 4, 5, 5, frame[1], hgt=0.66)
            L.rect(nx + 1, fy + 4, 3, 4, NI[0], hgt=0.3)
            L.px(nx + 2, fy + 8, frame[3])
        L.rect(cx - 6, fy + 5, 13, 5, CR[3], hgt=0.75)       # gauge plate
        L.hline(cx - 6, fy + 5, 13, CR[5])
        L.px(cx - 4, fy + 7, NI[1]); L.px(cx - 3, fy + 7, NI[1])
        L.px(cx + 3, fy + 7, NI[1]); L.px(cx + 4, fy + 7, NI[1])
        L.px(cx, fy + 6, NI[1]); L.px(cx, fy + 8, NI[1])
    return (fx0, fy, fx1 - fx0)


def window_glass(L, x, y, w, h, frame, glass, refl, curtain=None, lit=None, seed=0):
    L.rect(x - 1, y - 1, w + 2, h + 2, frame, hgt=0.6)
    if lit is not None:
        L.rect(x, y, w, h, lit, hgt=0.25, em=lit)
        return
    L.rect(x, y, w, h, glass, hgt=0.22)
    for k in range(min(w, h) // 2 + 2):                       # cold diagonal sky reflection
        xx, yy = x + w - 2 - k, y + 1 + k // 2
        if x <= xx < x + w and y <= yy < y + h:
            L.px(xx, yy, refl)
    L.px(x + w - 1, y, SK[2])
    if curtain is not None:
        rng = np.random.default_rng(abs(seed + x * 7 + y * 3))
        kind = int(rng.integers(0, 3))
        if kind == 0:                                         # drape tied back at the left
            for k in range(h):
                cw = max(1, int(round((w // 3) * (1 - 0.55 * math.sin(math.pi * k / max(1, h - 1))))))
                L.hline(x, y + k, cw, curtain, 0.25)
        elif kind == 1:                                       # lower half curtain on a rod
            L.rect(x, y + h // 2, w, h - h // 2, curtain, hgt=0.25)
            L.hline(x, y + h // 2, w, NI[2])
            for xx in range(x + 1, x + w, 3):
                L.px(xx, y + h - 1, NI[2])
        else:                                                 # blind pulled half down
            L.rect(x, y, w, h // 2 - 1, curtain, hgt=0.25)
            L.hline(x, y + h // 2 - 1, w, NI[2])


# =========================================================================== FAR TRACK + GERMAN TRAIN (0.86)
def german_car(L, x0, length, number, seed=0):
    """Grey-black delegation carriage (Reich special train), drawn ~0.8 scale (it stands one track further)."""
    rng = np.random.default_rng(seed)
    x1 = x0 + length
    wy = FAR_RAILS[3]
    roof_top, body_top, body_bot = 150, 159, 209
    B = dict(deep=NI[1], sh=IR[1], body=IR[2], lit=IR[3], rim=IR[4])
    L.rect(x0, body_top, length, body_bot - body_top, B['body'], hgt=0.5)
    for xx in range(x0, x1, 3):                               # panel rivet lines
        L.px(xx, body_top + 2, B['sh'])
        L.px(xx, body_bot - 3, B['sh'])
    L.rect(x0, body_bot - 12, length, 2, B['sh'])          # lower moulding
    L.hline(x0, body_top + 21, length, B['lit'])            # waist line
    for k in range(length // 22):
        wx = x0 + 14 + k * 22
        if wx + 14 > x1 - 12:
            break
        lit = rng.random() < 0.12
        window_glass(L, wx, body_top + 5, 13, 13, B['sh'], NI[3], SL[3],
                     curtain=CR[2] if rng.random() < 0.5 else None, lit=LA[1] if lit else None)
    for dx in (x0 + 2, x1 - 12):                              # end doors with handrails
        L.rect(dx, body_top + 3, 10, body_bot - body_top - 3, B['sh'], hgt=0.45)
        L.rect(dx + 2, body_top + 6, 6, 9, NI[3])
        L.px(dx + 6, body_top + 7, SL[3])
        L.vline(dx - 1, body_top + 8, 30, B['rim'])
        L.vline(dx + 10, body_top + 8, 30, B['rim'])
        L.rect(dx, body_bot, 10, 3, B['sh'])                  # step
    plate = 'BERLIN - VELTRAVA'
    pw = text_width(plate, 's') + 6
    px0 = x0 + length // 2 - pw // 2
    L.rect(px0, body_top + 26, pw, 9, CR[2], hgt=0.6)
    L.rect(px0 + 1, body_top + 27, pw - 2, 7, CR[3])
    text(L, px0 + 3, body_top + 28, plate, IR[1])
    text(L, x0 + 14, body_bot - 9, 'SONDERZUG', B['lit'])
    text(L, x1 - 22, body_bot - 9, str(number), B['lit'])
    for k in range(8):                                        # roof (arched) with snow
        inset = [0, 0, 1, 1, 2, 3, 4, 6][k]
        col = B['sh'] if k < 3 else (B['body'] if k < 5 else (SN[1] if k < 7 else SN[2]))
        L.hline(x0 + inset, body_top - 1 - k, length - 2 * inset, col, 0.7)
    snow_top(L, x0 + 6, roof_top + 2, length - 12, [SN[1], SN[2], SN[3]], depth=1, seed=seed)
    for vx in range(x0 + 20, x1 - 16, 34):                    # roof vents
        L.rect(vx, roof_top - 4, 5, 3, B['sh'])
        L.hline(vx - 1, roof_top - 5, 7, SN[3])
    L.vline(x1 - 1, body_top, body_bot - body_top, B['rim'])
    L.vline(x0, body_top, body_bot - body_top, B['deep'])
    L.rect(x0 + 2, body_bot, length - 4, 4, NI[2], hgt=0.6)   # solebar
    L.hline(x0 + 2, body_bot, length - 4, B['sh'])
    for bx in (x0 + 26, x1 - 26):
        bogie(L, bx, wy, r=5, frame=[NI[1], NI[2], IR[1], IR[2]], rim=IR[3])
    for ex in range(x0 + 56, x1 - 56, 30):                   # underfloor boxes
        L.rect(ex, body_bot + 4, 18, 4, NI[2])
        L.hline(ex, body_bot + 4, 18, IR[1])
    return [(x0 + 2, x1 - 2)], (x0 + 6, x1 - 6)


def make_far():
    """Far edge strip, track 4 and the German delegation's special train (3 grey-black carriages at layer x
    600-1260: cam640 screen 50..710, peeking above wagon 4 at cam 0).  Returns layer + anchors."""
    L = Layer(layer_w(P_FAR, 16), 360, 'far_track')
    Wf = L.w
    E = {'pennants': [], 'doors': []}
    # far edge strip (the station-side platform edge, snow-covered) hides the station building base
    rng = np.random.default_rng(41)
    for x in range(Wf):
        top = 197 + int(1.5 * math.sin(x / 13.0) + (1 if (x * 7) % 11 == 0 else 0))
        L.rect(x, top, 1, 207 - top, SN[1], hgt=0.5)
        L.px(x, top, SN[2])
        L.rect(x, 207, 1, 3, SL[1], hgt=0.45)
    for x in range(0, Wf, 24):
        L.vline(x, 207, 3, SL[0])
    for x in range(8, Wf, 96):                                # far platform lamp posts (cold), cast iron
        L.vline(x, 168, 30, IR[1])
        L.vline(x + 1, 168, 30, IR[2])
        L.hline(x - 2, 168, 6, IR[1])
        L.px(x + 3, 169, SN[4], em=SN[4])
        L.px(x - 1, 169, SN[3], em=SN[3])
    four_rail_track(L, 0, Wf, FAR_RAILS, 210, 226, seed=4, snow=0.55)
    # German special train: three carriages coupled, gangway bellows between them
    x = 600
    for i in range(3):
        rails, door = german_car(L, x, 204, 10 + i, seed=60 + i)
        E['doors'].append(door)
        E['pennants'].append((x + 6, 150))
        E['pennants'].append((x + 198, 150))
        if i < 2:
            for k in range(6):
                L.vline(x + 204 + k, 162, 46, NI[2] if k % 2 else IR[1])
        x += 210
    E['train_span'] = (600, x - 6)
    return L, E


def make_pennants(E, hist=False):
    """Small delegation pennants on staffs at the carriage ends (Reich).  Neutral: the fictional
    Reichssiegel (white pillar in a black disc on grey-black); hist: the historical swastika pennant.
    Separate layer at the far-track parallax so the insignia switch (Symbols.pick) can swap the file."""
    L = Layer(layer_w(P_FAR, 16), 360, 'pennants_reich')
    for (sx, sy) in E['pennants']:
        L.vline(sx, sy - 12, 13, IR[3], hgt=0.6)
        L.px(sx, sy - 13, CR[4])
        for k in range(9):                                    # swallow-less triangular pennant, hanging
            hh = max(1, 6 - (k * 6) // 9)
            L.rect(sx + 1 + k, sy - 12, 1, hh, (RD[2] if hist else IR[2]) if k < 8 else (RD[1] if hist else IR[1]),
                   hgt=0.6)
        L.hline(sx + 1, sy - 12, 8, RD[3] if hist else IR[3])  # top edge catches the light
        cx, cy = sx + 3, sy - 10
        if hist:
            L.px(cx, cy, SN[4]); L.px(cx + 1, cy, SN[4]); L.px(cx, cy + 1, SN[4]); L.px(cx + 1, cy + 1, SN[4])
            L.px(cx, cy, NI[0]); L.px(cx + 1, cy + 1, NI[0])
        else:
            L.px(cx, cy, NI[0]); L.px(cx + 1, cy, NI[0]); L.px(cx, cy + 1, NI[0]); L.px(cx + 1, cy + 1, NI[0])
            L.px(cx, cy, SN[4]); L.px(cx, cy + 1, SN[4])
    return L


# =========================================================================== ISLAND PLATFORM + CANOPY (0.93)
def make_island():
    """Island platform between tracks 4 and 5 with its cast-iron canopy (columns every 150 px, ornamental
    brackets, roof fascia with dagger boards, snow on top).  Small baked figures of the German delegation
    and a porter stand at x 760-1180 (cam640), well away from the playfield NPC anchors."""
    p = P_ISL
    L = Layer(layer_w(p, 16), 360, 'island')
    Wi = L.w
    E = {'lamps': []}
    s0, s1 = ISLAND['surf']
    # surface (dry under the roof, snow-dusted near the edges), coping, front wall
    nz = value_noise(Wi, 20, 9, seed=7, octaves=2)
    for y in range(s0, s1):
        for x in range(Wi):
            v = nz[y - s0, x]
            L.px(x, y, SN[0] if (y < s0 + 2 and v > 0.45) else (SL[2] if v > 0.55 else SL[1]), 0.3)
    c0, c1 = ISLAND['coping']
    L.rect(0, c0, Wi, c1 - c0, CR[2], hgt=0.6)
    L.hline(0, c0, Wi, CR[4])
    for x in range(0, Wi, 20):
        L.vline(x, c0, c1 - c0, CR[1])
    snow_top(L, 0, c0 - 1, Wi, [SN[1], SN[2], SN[3]], depth=1, seed=3)
    w0, w1 = ISLAND['wall']
    L.rect(0, w0, Wi, w1 - w0, SL[1], hgt=0.5)
    for y in range(w0 + 2, w1, 3):
        for x in range(Wi):
            if (x + (y // 3) * 5) % 9 == 0:
                L.px(x, y, SL[0])
    L.hline(0, w0, Wi, NI[3])
    for x in range(Wi):                                       # snow drift at the wall foot
        h = int(1 + 1.5 * (1 + math.sin(x / 7.0 + math.sin(x / 23.0))))
        for k in range(h):
            L.px(x, w1 - 1 - k, SN[1] if k == h - 1 else SN[0], 0.4)
    flat_normal(L, 0, s0, Wi, s1 - s0, UP)
    flat_normal(L, 0, w0, Wi, w1 - w0, (0, 0, 1))
    # people on the island (German delegation boarding, a porter with a luggage cart, a guard)
    figs = [
        (790, figure(37, [IR[0], IR[1], IR[2]], hat='homburg', hat_col=NI[1], rim=SL[4], seed=81, coat_len=0.82,
                     bag=([NI[2], IR[2], IR[3]], 1))),
        (806, figure(36, [NI[3], IR[1], IR[2]], hat='fedora', hat_col=IR[1], rim=SL[4], seed=82, coat_len=0.8)),
        (1004, figure(37, [SL[0], SL[1], SL[2]], hat='peaked', hat_col=SL[0], rim=SL[4], seed=83, arms='push',
                      scarf=CR[3])),
        (1110, figure(36, [IR[0], IR[1], IR[2]], hat='homburg', hat_col=NI[1], rim=SL[4], seed=84, coat_len=0.82,
                      facing='back')),
        (1124, figure(34, [IR[1], IR[2], IR[3]], hat='beret', hat_col=NI[2], rim=SL[4], seed=85, coat_len=0.84,
                      hair=NI[2])),
    ]
    for fx, F in figs:
        L.blit(F, fx - F.w // 2, s1 - F.h + 1)
    cx0 = 1012                                                # the porter's cart with suitcases
    L.rect(cx0, 220, 34, 3, CR[1], hgt=0.6)
    L.hline(cx0, 220, 34, CR[2])
    for (bx, bw, bh, col) in ((cx0 + 2, 12, 8, (LA[0], LA[1])), (cx0 + 15, 10, 6, (IR[1], IR[2])),
                              (cx0 + 6, 14, 5, (CR[1], CR[3])), (cx0 + 26, 7, 9, (PA[0], PA[1]))):
        yb = 220 if bx != cx0 + 6 else 212
        L.rect(bx, yb - bh, bw, bh, col[0], hgt=0.6)
        L.hline(bx, yb - bh, bw, col[1])
        L.vline(bx + bw - 1, yb - bh, bh, col[1])
    for wx in (cx0 + 5, cx0 + 29):
        L.ellipse(wx, 225, 2.5, 2.5, NI[2])
    L.line(cx0 + 34, 220, cx0 + 40, 210, CR[1])
    # canopy: columns, brackets, fascia + dagger boards, snow on top, hanging lamps and track signs
    roof_y = 160
    col_xs = list(range(40, Wi, 150))
    for i, cx in enumerate(col_xs):
        L.rect(cx - 2, roof_y + 8, 5, s1 - roof_y - 8, IR[1], hgt=0.6)
        L.vline(cx + 2, roof_y + 8, s1 - roof_y - 8, IR[3])
        L.vline(cx - 2, roof_y + 8, s1 - roof_y - 8, NI[2])
        cyl_normal(L, cx - 2, roof_y + 8, 5, s1 - roof_y - 8)
        L.rect(cx - 4, s1 - 4, 9, 4, IR[1], hgt=0.62)        # base
        L.hline(cx - 4, s1 - 4, 9, IR[3])
        L.rect(cx - 4, roof_y + 8, 9, 3, IR[2], hgt=0.66)    # capital
        L.hline(cx - 4, roof_y + 8, 9, IR[4])
        for side in (-1, 1):                                  # curved brackets (quarter circles)
            for a in range(0, 91, 6):
                r = 14
                bx = cx + side * int(round(r - math.cos(math.radians(a)) * r))
                by = roof_y + 8 + int(round(math.sin(math.radians(a)) * r)) - r + 1
                L.px(bx, by + 6, IR[2], 0.6)
            L.line(cx, roof_y + 15, cx + side * 14, roof_y + 7, IR[1])
        if i % 2 == 0:
            E['lamps'].append((cx + 75, roof_y + 13))
    L.rect(0, roof_y, Wi, 8, SL[1], hgt=0.7)                 # fascia
    L.hline(0, roof_y, Wi, SL[3])
    L.hline(0, roof_y + 7, Wi, SL[0])
    for x in range(0, Wi, 4):                                 # dagger boards (valance)
        L.vline(x, roof_y + 8, 3, SL[1])
        L.px(x + 1, roof_y + 8, SL[1])
        L.px(x + 1, roof_y + 9, SL[2])
    for k in range(2):                                        # snow lying on the roof, seen over the fascia
        L.hline(0, roof_y - 1 - k, Wi, [SN[1], SN[2]][k], 0.8)
    for x in range(Wi):
        bump = int(1.2 + 1.2 * math.sin(x / 11.0) + 0.8 * math.sin(x / 4.3))
        for k in range(max(0, bump)):
            L.px(x, roof_y - 3 - k, SN[3] if k == bump - 1 else SN[2], 0.8)
    snow_lip(L, 0, roof_y + 11, Wi, [SL[3], SL[4]], seed=5, icicles=0.05, ice_col=SL[4])
    flat_normal(L, 0, roof_y - 9, Wi, 9, (0, 0.85, 0.5))
    for (lx, ly) in E['lamps']:                               # hanging cold lamps
        L.vline(lx, roof_y + 11, 5, IR[1])
        L.rect(lx - 3, ly + 3, 7, 2, IR[2])
        L.hline(lx - 4, ly + 5, 9, SN[2])
        L.rect(lx - 1, ly + 6, 3, 2, SN[4], em=SN[4])
    for (sx, label) in ((115, '4  5'), (565, '4  5'), (1015, '4  5'), (1465, '4  5')):
        L.vline(sx + 2, roof_y + 11, 5, IR[1])
        L.vline(sx + 17, roof_y + 11, 5, IR[1])
        L.rect(sx, roof_y + 16, 20, 9, SN[3], hgt=0.7)
        L.rect(sx + 1, roof_y + 17, 18, 7, SL[1])
        text(L, sx + 3, roof_y + 18, label, SN[4])
        L.vline(sx + 10, roof_y + 17, 7, SN[3])
    return L, E


# =========================================================================== GROUND (parallax 1)
def r_slab(row, k):
    h = (row * 7919 + k * 104729 + 17) % 23
    return 3 if h < 4 else (4 if h == 9 else (h % 3))


def make_ground(E_props, cold_lamps, warm_sources):
    """Track 5 (four rails, buffer stop at x 1340) and the walkable platform under our canopy: dry dark
    slabs, tracked-in wet patches mirroring the cold canopy lamps, blown snow only along the open rear edge
    (outside the roof) with footprints at x 150-178 (exp_footprints), warm café reflections at x 1560-1730."""
    L = Layer(W, 360, 'ground')
    rng = np.random.default_rng(77)
    nz = value_noise(W, 360, 11, seed=2, octaves=3)
    nzf = value_noise(W, 360, 4, seed=8, octaves=2)
    four_rail_track(L, 0, 1344, NEAR_RAILS, 244, 261, seed=9, snow=0.5)
    # concourse forecourt (head of track 5): paving behind the buffer stop
    L.rect(1344, 240, W - 1344, 22, SL[1], hgt=0.3)
    for x in range(1344, W, 16):
        L.vline(x, 240, 22, SL[0])
    for y in range(243, 262, 6):
        L.hline(1344, y, W - 1344, SL[0])
    # ---- platform edge coping (light stone) + worn white line
    pe = PLATFORM_EDGE
    L.rect(0, pe, W, 3, CR[3], hgt=0.7)
    L.hline(0, pe, W, CR[4], 0.75)
    L.hline(0, pe + 2, W, CR[1], 0.6)
    for x in range(0, W, 26):
        L.vline(x, pe, 3, CR[1])
    for x in range(W):
        if (x // 5) % 7 != 6 and nzf[pe + 3, x] > 0.3:
            L.px(x, pe + 4, SN[2] if x % 9 else SN[1], 0.5)
    # ---- slabs (dry, dark): rows grow toward the camera (oblique), long slabs, soft joints
    tones = [SL[1], SL[1], IR[2], SL[1], IR[2], SL[2]]
    y0 = 266
    row = 0
    for rh in (8, 9, 10, 11, 12, 13, 14, 15, 16):
        sw = 60 + row * 6
        shift = (row * 37) % sw
        for k, x0 in enumerate(range(-shift, W, sw)):
            L.rect(x0, y0, sw, rh, tones[r_slab(row, k) % len(tones)], hgt=0.3)
            L.vline(x0, y0, rh, SL[0], 0.26)
        L.hline(0, y0, W, SL[0], 0.26)
        y0 += rh
        row += 1
        if y0 >= 360:
            break
    L.rect(0, 265, W, 1, NI[3])
    # wear on the walking line (lighter polish) + scuffs
    for x in range(0, W):
        fy = 300 + int(6 * math.sin(x / 97.0))
        for y in (fy, fy + 7):
            if nzf[y, x] > 0.55 and (L.c[y, x, :3] != NI[3][:3]).any():
                L.px(x, y, SL[2])
    # ---- tracked-in wet patches (darker) reflecting the cold lamps (dashes); slush streaks
    wet = value_noise(W, 360, 30, seed=41, octaves=2)
    for y in range(268, 360, 2):
        x = 0
        while x < W:
            if wet[y, x] > 0.62:
                ln = 3 + (x * 7 + y) % 6
                for xx in range(x, min(W, x + ln)):
                    cur = L.c[y, xx, :3]
                    if (cur == SL[1][:3]).all() or (cur == IR[2][:3]).all() or (cur == IR[1][:3]).all():
                        L.px(xx, y, NI[3] if (xx + y) % 5 else SL[0], 0.28)
                x += ln + 2 + (x * 3 + y) % 5
            else:
                x += 3
    for _ in range(120):
        x = int(rng.integers(0, W - 8))
        y = int(rng.integers(272, 350))
        ln = int(rng.integers(3, 8))
        L.hline(x, y, ln, SN[0], 0.32)
    # ---- blown snow along the open rear edge (outside the roof drip line) + footprints (hidden find)
    for x in range(W):
        d = int(1 + 2.4 * nz[266, x] + 1.6 * nzf[267, x])
        if 1344 < x:
            d = max(0, d - 2)
        for k in range(d):
            L.px(x, 266 + k, SN[2] if k == 0 else SN[1], 0.4)
    for i in range(7):                                        # footprints in the edge snow (exp_footprints)
        fx = 148 + i * 5
        fy = 266 + (i % 2) * 2
        L.rect(fx, fy, 2, 2, SL[2] if i % 2 else SL[3])
        L.px(fx + 1, fy, SN[0])
        if i % 3 == 0:
            L.rect(fx, 266, 3, 6, SN[1])
            L.rect(fx + 1, 267 + (i % 2), 2, 3, SL[3])
    E_props['footprints'] = (160, 268)
    # puddles near the front (the canopy drips at its front edge, off-screen above the camera)
    for (px_, py_, rx, ry) in ((210, 344, 26, 3), (560, 336, 30, 4), (980, 346, 34, 3), (1270, 338, 24, 3),
                               (1490, 344, 30, 4), (1800, 340, 28, 3), (760, 352, 22, 2)):
        m, mx, my = L.ellipse_mask(px_, py_, rx, ry)
        hh, ww = m.shape
        sy, sx = np.mgrid[0:hh, 0:ww]
        T = np.clip(1 - sy / max(1, hh - 1) * 1.5, 0, 1) * 2.8
        lad = [NI[1], NI[2], SL[0], SL[2]]
        idx = np.clip(np.floor(T).astype(int) + ((T - np.floor(T)) > bayer(ww, hh, mx, my)), 0, 3)
        cols = np.stack(lad)[idx]
        L._put(m, mx, my, cols, hgt=0.05)
        for x in range(mx, mx + ww):
            colm = m[:, x - mx]
            if colm.any():
                L.px(x, my + int(np.nonzero(colm)[0].max()) + 1, SL[2])
    # ---- reflections: short broken dashes below each source on wet/dark pixels (emissive)
    wet_cols = [NI[1], NI[2], NI[3], SL[0], SL[1], SL[2], IR[1], IR[2]]
    wet_keys = set(int(c[0]) << 16 | int(c[1]) << 8 | int(c[2]) for c in wet_cols)
    rr = np.random.default_rng(5)
    for (lx, ly_base, col_list, strength, spread) in warm_sources + cold_lamps:
        for k, y in enumerate(range(ly_base, min(360, ly_base + 40), 2)):
            t = k / 20.0
            if rr.random() > strength * (1 - t * 0.85):
                continue
            half = 1 + int(rr.integers(0, 2)) + int(spread * t)
            off = int(rr.integers(-2, 3))
            for x in range(int(lx) - half + off, int(lx) + half + off + 1):
                if not (0 <= x < W):
                    continue
                c = L.c[y, x]
                key = int(c[0]) << 16 | int(c[1]) << 8 | int(c[2])
                if key in wet_keys and (x + y) % 3:
                    cc = col_list[0] if t < 0.35 else col_list[1]
                    L.px(x, y, cc, em=cc if col_list[0] is not SK[1] else None)
    flat_normal(L, 0, 262, W, 360 - 262, UP)
    flat_normal(L, 0, pe, W, 1, (0, 0.85, 0.5))
    return L


# =========================================================================== NEAR TRAIN (parallax 1)
def soviet_car(L, x0, x1, number, seed=0, saloon_window=None, doors=('l', 'r')):
    """Dark-green Soviet delegation carriage (1960s all-metal), cream waist stripe, curtained windows,
    route board МОСКВА — ВЕЛТРАВА, arched roof with vents and snow, two bogies on track 5."""
    rng = np.random.default_rng(seed)
    length = x1 - x0
    wy = NEAR_RAILS[3]
    roof_top, body_top, body_bot = 160, 171, 234
    G = dict(deep=NI[3], sh=PA[0], body=PA[1], lit=PA[2], rim=PA[3], hi=PA[4])
    L.rect(x0, body_top, length, body_bot - body_top, G['body'], hgt=0.5)
    L.rect(x0, body_top, length, 3, G['lit'], hgt=0.55)
    for xx in range(x0, x1, 3):
        L.px(xx, body_top + 4, G['sh'])
    L.rect(x0, 205, length, 2, CR[4], hgt=0.6)              # cream waist stripe
    L.hline(x0, 207, length, G['sh'])
    L.rect(x0, body_bot - 6, length, 2, G['sh'])
    out = {'windows': [], 'doors': []}
    door_w = 16
    dxs = []
    if 'l' in doors:
        dxs.append(x0 + 5)
    if 'r' in doors:
        dxs.append(x1 - 5 - door_w)
    k = 0
    wx = x0 + 5 + door_w + 8
    while wx + 16 <= x1 - 5 - door_w - 6:
        lit = saloon_window is not None and abs(wx + 8 - saloon_window) < 12
        curtain = CR[3] if (k % 3 != 2) else None
        window_glass(L, wx, 183, 16, 17, G['sh'], NI[3], PA[2], curtain=curtain if not lit else None,
                     lit=LA[2] if lit else None)
        if lit:                                               # warm saloon: lamp, tea glass, a reading figure
            L.rect(wx + 1, 184, 14, 15, LA[2], em=LA[2])
            L.rect(wx + 9, 185, 6, 8, LA[3], em=LA[3])
            L.px(wx + 11, 186, LA[4], em=LA[4])
            L.rect(wx + 2, 188, 5, 11, LA[0], em=LA[0])      # silhouette shoulder/head
            L.rect(wx + 3, 186, 3, 3, LA[0], em=LA[0])
            L.rect(wx + 9, 195, 2, 3, LA[1], em=LA[1])      # tea glass in its holder
            L.hline(wx, 199, 16, CR[3])
            for (cxx, cyy) in ((wx, 183), (wx + 15, 183)):
                L.px(cxx, cyy, LA[1])
            out['saloon'] = (wx + 8, 191)
        out['windows'].append((wx, 183, 16, 17))
        L.hline(wx - 1, 201, 18, G['lit'])
        wx += 24
        k += 1
    for dx in dxs:                                            # doors with drop window, handrails, steps
        L.rect(dx, body_top + 3, door_w, body_bot - body_top - 3, G['sh'], hgt=0.45)
        L.vline(dx, body_top + 3, body_bot - body_top - 3, G['deep'])
        L.vline(dx + door_w - 1, body_top + 3, body_bot - body_top - 3, G['lit'])
        window_glass(L, dx + 3, 183, 10, 14, G['deep'], NI[3], PA[2])
        L.px(dx + 12, 212, CR[4])
        for hx in (dx - 2, dx + door_w + 1):
            L.vline(hx, 186, 44, IR[4])
            L.px(hx, 185, IR[3])
        for st in range(3):                                   # steps down to the platform
            L.rect(dx + 1, body_bot + 2 + st * 7, door_w - 2, 2, IR[2], hgt=0.6)
            L.hline(dx + 1, body_bot + 2 + st * 7, door_w - 2, IR[4])
        L.vline(dx + 1, body_bot, 22, IR[1])
        L.vline(dx + door_w - 2, body_bot, 22, IR[1])
        out['doors'].append((dx, door_w))
    # route board + car number + small Cyrillic stencils
    plate = 'МОСКВА — ВЕЛТРАВА'.replace('—', '-')
    pw = text_width(plate, 's') + 8
    px0 = x0 + length // 2 - pw // 2
    L.rect(px0, 174, pw, 9, CR[5], hgt=0.6)
    L.rect(px0, 174, pw, 1, SN[4])
    L.rect(px0, 182, pw, 1, CR[2])
    text(L, px0 + 4, 176, plate, NI[1])
    text(L, x0 + 26, 210, str(number), CR[4], font='l')
    text(L, x1 - 60, 213, 'ВАГОН ' + str(number), PA[3])
    # roof: arched, vents, snow
    for k in range(10):                                       # arched roof: dark iron, lit rim, snow on top
        inset = [0, 0, 0, 1, 1, 2, 2, 3, 5, 7][k]
        col = IR[1] if k < 3 else (IR[2] if k < 6 else (SN[1] if k < 8 else SN[2]))
        L.hline(x0 + inset, body_top - 1 - k, length - 2 * inset, col, 0.72)
        L.px(x1 - 1 - inset, body_top - 1 - k, IR[3] if k < 6 else SN[3])
    snow_top(L, x0 + 8, roof_top + 1, length - 16, [SN[2], SN[3], SN[4]], depth=1, seed=seed)
    for vx in range(x0 + 24, x1 - 20, 30):
        L.rect(vx, roof_top - 2, 6, 3, IR[1])
        L.hline(vx - 1, roof_top - 3, 8, SN[3])
    for xx in range(x0, x1):                                  # snow drips over the roof edge
        if (xx * 7 + seed) % 13 < 3:
            L.px(xx, body_top - 1, SN[2])
    L.vline(x1 - 1, body_top, body_bot - body_top, G['rim'])
    L.vline(x1 - 2, body_top, body_bot - body_top, G['lit'])
    L.vline(x0, body_top, body_bot - body_top, G['deep'])
    # underframe: solebar, equipment boxes, steam pipe, bogies
    L.rect(x0 + 2, body_bot, length - 4, 5, NI[2], hgt=0.6)
    L.hline(x0 + 2, body_bot, length - 4, IR[1])
    for ex in range(x0 + 70, x1 - 70, 34):
        L.rect(ex, body_bot + 5, 22, 6, NI[2], hgt=0.55)
        L.hline(ex, body_bot + 5, 22, IR[2])
        L.vline(ex + 21, body_bot + 5, 6, IR[3])
    L.hline(x0 + 40, body_bot + 12, length - 80, IR[2])
    out['bogies'] = []
    for bx in (x0 + 36, x1 - 36):
        out['bogies'].append(bogie(L, bx, wy, r=7))
    stains(L, x0, body_top + 5, length, body_bot - body_top - 8, [NI[3], PA[0], PA[1], PA[2]], seed=seed,
           density=0.12, length=(3, 10))
    return out


def courier_wagon(L, x0, x1, seed=0):
    """Courier wagon 4: windowless dark van, riveted panels, two sliding doors with lead seals, the BRASS
    FRAME with the weighing ticket between them, convertible (gauge-changing) bogies, tail lamps."""
    length = x1 - x0
    wy = NEAR_RAILS[3]
    roof_top, body_top, body_bot = 162, 172, 234
    G = dict(deep=NI[1], sh=NI[3], body=PA[0], lit=PA[1], rim=PA[2])
    L.rect(x0, body_top, length, body_bot - body_top, G['body'], hgt=0.5)
    for py in range(body_top + 2, body_bot - 2, 10):           # riveted panel seams
        L.hline(x0, py, length, G['sh'])
        for xx in range(x0 + 2, x1 - 2, 4):
            L.px(xx, py + 1, IR[3])
    for px_ in range(x0, x1, 30):
        L.vline(px_, body_top, body_bot - body_top, G['sh'])
        for yy in range(body_top + 3, body_bot - 2, 4):
            L.px(px_ + 1, yy, IR[3])
    E = {}
    doors = [(x0 + 28, 38), (x1 - 66, 38)]
    E['seals'] = []
    for (dx, dw) in doors:
        L.rect(dx, body_top + 4, dw, body_bot - body_top - 8, G['lit'], hgt=0.45)
        for xx in range(dx + 4, dx + dw, 6):
            L.vline(xx, body_top + 5, body_bot - body_top - 10, G['body'])
        L.vline(dx + dw - 1, body_top + 4, body_bot - body_top - 8, G['rim'])
        L.rect(dx - 3, body_top + 1, dw + 8, 2, IR[2])        # door rails
        L.rect(dx - 3, body_bot - 4, dw + 8, 2, IR[2])
        L.hline(dx - 3, body_top + 1, dw + 8, IR[4])
        hy = 208
        L.rect(dx + dw - 5, hy - 8, 2, 16, IR[3], hgt=0.75)   # handle bar
        L.vline(dx + dw - 4, hy - 8, 16, IR[4])
        L.rect(dx + dw - 2, hy - 1, 6, 3, IR[1], hgt=0.75)    # hasp
        sx, sy = dx + dw + 4, hy + 4                           # lead seal on its wire
        L.px(dx + dw + 2, hy + 2, SN[1])
        L.px(dx + dw + 3, hy + 3, SN[1])
        L.rect(sx, sy, 3, 3, SN[1], hgt=0.85)
        L.px(sx, sy, SN[3])
        L.px(sx + 2, sy + 2, IR[3])
        L.px(sx + 1, sy + 3, SN[0])
        E['seals'].append((sx + 1, sy + 1))
    # the brass frame with the weighing ticket (paper under glass), between the doors, eye-catching glint
    fx, fy, fw, fh = (x0 + x1) // 2 - 9, 202, 18, 16
    L.rect(fx - 1, fy - 1, fw + 2, fh + 2, LA[0], hgt=0.8)
    L.rect(fx, fy, fw, fh, LA[1], hgt=0.85)
    L.hline(fx, fy, fw, LA[3])
    L.vline(fx + fw - 1, fy, fh, LA[3])
    L.px(fx + fw - 1, fy, LA[4], em=LA[3])
    L.rect(fx + 2, fy + 2, fw - 4, fh - 4, CR[5], hgt=0.7)
    for k, yy in enumerate(range(fy + 3, fy + fh - 3, 2)):     # printed rows (scribble at world scale)
        L.hline(fx + 3, yy, fw - 6 - (k % 2) * 3, CR[2])
    L.rect(fx + 3, fy + 3, 4, 1, NI[2])
    L.rect(fx + fw - 7, fy + fh - 6, 3, 3, SL[3])             # commission counter-seal (slate blue ink)
    L.px(fx + fw - 4, fy + 3, SN[4])                           # glass glint
    L.px(fx + fw - 5, fy + 4, SN[3])
    for (sx, sy) in ((fx - 1, fy - 1), (fx + fw, fy - 1), (fx - 1, fy + fh), (fx + fw, fy + fh)):
        L.px(sx, sy, LA[2])
    E['frame'] = (fx + fw // 2, fy + fh // 2)
    # stencils: big 4, KURIERWAGEN / КУРЬЕРСКИЙ, gauge marks
    text(L, x0 + 8, 180, '4', CR[3], font='l', scale=2)
    text(L, x0 + 76, 180, 'KURIERWAGEN', PA[2])
    text(L, x0 + 76, 187, 'КУРЬЕРСКИЙ', PA[2])
    text(L, x1 - 24, 222, '1435', PA[2])
    text(L, x1 - 24, 228, '1520', PA[2])
    for k in range(10):                                         # roof (arched) + snow
        inset = [0, 0, 0, 1, 1, 2, 2, 3, 5, 7][k]
        col = NI[2] if k < 3 else (IR[1] if k < 6 else (SN[1] if k < 8 else SN[2]))
        L.hline(x0 + inset, body_top - 1 - k, length - 2 * inset, col, 0.72)
        L.px(x1 - 1 - inset, body_top - 1 - k, IR[2] if k < 6 else SN[3])
    snow_top(L, x0 + 8, roof_top + 1, length - 16, [SN[2], SN[3], SN[4]], depth=1, seed=seed)
    L.vline(x1 - 1, body_top, body_bot - body_top, G['rim'])
    L.vline(x0, body_top, body_bot - body_top, G['deep'])
    for (tx, ty) in ((x1 + 1, 222), (x1 + 1, 200)):            # tail lamps (dim red)
        L.rect(tx, ty, 3, 5, NI[2])
        L.rect(tx + 1, ty + 1, 2, 3, RD[2], em=RD[1])
    L.rect(x0 + 2, body_bot, length - 4, 5, NI[1], hgt=0.6)
    L.hline(x0 + 2, body_bot, length - 4, IR[1])
    E['bogies'] = []
    for bx in (x0 + 34, x1 - 34):
        E['bogies'].append(bogie(L, bx, wy, r=7, convertible=True))
    stains(L, x0, body_top + 3, length, body_bot - body_top - 6, [NI[1], NI[3], PA[0], PA[1]], seed=seed + 4,
           density=0.18, length=(4, 14))
    return E


def gangway(L, x0, x1, top=176, bot=232):
    for x in range(x0, x1):
        L.vline(x, top, bot - top, NI[2] if (x - x0) % 2 else NI[1], 0.4)
    L.hline(x0, top, x1 - x0, IR[2])


def buffer_stop(L, x):
    """Cast-iron buffer stop at the head of track 5 (x .. x+20), with a dim red lamp."""
    L.rect(x, 232, 20, 6, IR[1], hgt=0.6)
    L.hline(x, 232, 20, IR[3])
    for bx in (x + 1, x + 15):
        L.rect(bx, 233, 4, 4, IR[2])
        L.px(bx + 3, 233, IR[4])
    L.line(x + 18, 237, x + 6, 258, IR[1])
    L.line(x + 2, 237, x + 14, 258, IR[1])
    L.rect(x + 4, 238, 12, 3, NI[2])
    L.rect(x + 8, 224, 4, 7, NI[2])
    L.rect(x + 9, 225, 2, 3, RD[2], em=RD[1])
    snow_top(L, x, 231, 20, [SN[1], SN[2]], depth=1, seed=x)


def make_train_near():
    """Soviet delegation train on track 5: car 1 (x <0..80, loco further left off-screen), car 2 x 90-322
    (Alexei's door x 95-111), car 3 x 330-556 (warm saloon window above Voronova x ~388), courier wagon 4
    x 564-758.  Buffer stop at x 1330."""
    L = Layer(W, 360, 'train_near')
    E = {}
    c1 = soviet_car(L, -150, 82, 1, seed=11, doors=('l', 'r'))
    gangway(L, 82, 90)
    c2 = soviet_car(L, 90, 322, 2, seed=12)
    gangway(L, 322, 330)
    c3 = soviet_car(L, 330, 556, 3, seed=13, saloon_window=388)
    gangway(L, 556, 564)
    w4 = courier_wagon(L, 564, 758, seed=14)
    buffer_stop(L, 1330)
    E['cars'] = (c1, c2, c3)
    E['wagon4'] = w4
    E['saloon'] = c3.get('saloon')
    E['gangways'] = [(86, 236), (326, 236), (560, 236)]
    E['alexei_door'] = c2['doors'][0]
    E['buffer_lamp'] = (1340, 226)
    return L, E
