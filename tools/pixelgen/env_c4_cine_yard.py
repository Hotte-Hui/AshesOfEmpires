"""env_c4_cine_yard -- the Karsk freight yard before dawn, in parallax layers (owner: cine stream, polish pass).

LS_C4_Homeward w3 (Alexei walks to the lit cellar window; the camera tracks him) and LS_C4_Voices v3 (Alexei and
Lev climb out of the cellar stair under the green signal).  16 February 1964, 4.40: snow falls, the town still
dark, the yard lit by two lamps, the repaired signal and the cellar window of the freight office.

  sky      low snow clouds lit orange from below by the town and the power plant          (static)
  far      Karsk: the silos and chimneys of the level's skyline (re-lit for the night, a few lit windows),
           the cooling towers of the power plant with their plumes, red lights on the chimneys   (parallax 0.15)
  mid      the far sidings: a long rake of covered wagons under snow, the water tower, a signal gantry, a
           shunting lamp, the lamp posts of the yard                                           (parallax 0.5)
  main     the near tracks in the snow, the repaired signal (lattice mast, ladder, green lens), the freight
           office (brick, gutter and downpipe, one lit window upstairs, the sign, the door, the outside stair down
           to the archive cellar, the lit cellar window in its light well), the yard lamp, a hand cart, sleepers
                                                                                                   (parallax 1)
  parapet  the stair's parapet (drawn over the climbers of v3)
  glows    additive: the signal's green, the lamps, the window, the stair
The anchors (signal, window, stair, lamps, towers) are those of env_c4_cine_places (layout.json "places").
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CONCRETE, BRICK, IRONK, SIGNAL, SNOWK, box, ell,
                             poly)
import env_c4_cine_levelart as LA

FEET = 300
MAIN_W = 720                           # the main layer runs on to the right for the tracking camera of w3
FAR_W, MID_W = 760, 760
SIG_AT = (152, 158)
WINDOW = (520, 280, 560, 297)
STAIR = (414, 500)
LAMPS = ((262, 104), (612, 96))
TOWERS = ((96, 200), (176, 200))       # cooling towers (far layer, centre x, base y)
OFFICE_X = 392
TRACKS_MAIN = (272, 279)               # the near siding in front of the wagons (rail heads y)


def _sky():
    """Low snow clouds lit from below (the town's sodium, the plant), darker to the zenith."""
    R = Q.ramps(K=KNIGHT, A=['#1A1210', '#2A1C16', '#3C2A1E', '#523826', '#6A4A30'])
    p = C.Paint(VW, VH, R, 'ysky')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 22, 9201)
    nz2 = Q.noise(VW, VH, 9, 9203)
    town = Q.lightfield(VW, VH, [(120, 230, 330, 1.0, 1.3), (520, 240, 300, 0.7, 1.4)])
    p.put(yy >= 0, 'K', 0.8 + (yy / 210.0) * 1.6 + nz * 0.8 + town * 1.0)
    # cloud banks: their undersides faintly lit by the town (a dull brown-grey, never a fire)
    bank = (np.sin(xx / 47.0 + nz * 5.0) * 10 + 160 + nz2 * 22 > yy) & (yy > 96 + nz * 30)
    under = bank & (nz2 > 0.5)
    p.put(under, 'K', 2.2 + town[under] * 1.6 + (nz2[under] - 0.5) * 2.0)
    warm_ = under & (town > 0.6) & (nz2 > 0.62)
    p.put(warm_, 'A', 1.0 + town[warm_] * 0.6)
    p.resolve(band=2.0)
    return p.L.c


def _towers(p, nz, glow):
    """The cooling towers of the power plant: hyperboloid shells, lit from below on the inside edge, plumes."""
    yy, xx = p.yy, p.xx
    for k, (tx, tb) in enumerate(TOWERS):
        ht = 70 - k * 8
        u = np.clip((tb - yy) / ht, 0, 1)
        # hyperboloid shell: widest at the foot, waist at 70 %, a slight flare at the lip
        half = 25 - 11 * np.sin(np.clip(u / 0.72, 0, 1) * math.pi * 0.5) + np.clip(u - 0.72, 0, 1) * 14 - k * 3
        tw = (yy <= tb) & (yy >= tb - ht) & (np.abs(xx - tx) < half)
        side = (xx - tx) / np.maximum(half, 1)
        p.put(tw, 'K', 2.0 + (1 - u[tw]) * 0.7 + nz[tw] * 0.3 + glow[tw] * 1.2 - side[tw] * 0.6)
        p.put(tw & (side > 0.72), 'K', 3.4 + glow[tw & (side > 0.72)] * 0.8)    # the lit flank
        p.put(tw & (side < -0.8), 'K', 1.2)
        p.put(tw & (yy >= tb - 3), 'A', 1.0 + glow[tw & (yy >= tb - 3)] * 1.2)   # the lit base
        rim_ = (yy >= tb - ht - 1) & (yy < tb - ht + 1) & (np.abs(xx - tx) < half + 1)
        p.put(rim_, 'K', 3.0)
        # the plume rising and leaning east, a soft dithered column lit warm from below
        th = Q.pg.bayer(p.w, p.h, k, 0)
        for j in range(9):
            cx_, cy_ = tx + j * 7 + j * j * 0.9, tb - ht - 8 - j * 11
            pr = ell(cx_, cy_, 13 + j * 3.5, 8 + j * 2.4, p.w, p.h)
            sel = pr & (th < 0.88 - j * 0.085) & (yy < tb - ht)
            p.put(sel, 'K', 3.0 - j * 0.14 + nz[sel] * 0.6 + (j < 2) * 0.7)


def far():
    """Karsk at night: the skyline of the railyard level (silhouettes, re-lit), lit windows, chimneys, towers."""
    W = FAR_W
    R = Q.ramps(K=KNIGHT, S=SNOWK, A=AMBER, R=['#200606', '#4A0E0A', '#8A1C12', '#D0402A'])
    p = C.Paint(W, VH, R, 'yfar')
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 12, 9211)
    glow = Q.lightfield(W, VH, [(130, 210, 160, 1.0, 1.2), (560, 214, 140, 0.6, 1.3)])
    _towers(p, nz, glow)
    # the level's skyline silhouettes (far_city, far_industry), night-tinted, the windows lit at random
    sil = np.zeros((VH, W), bool)
    lit = np.zeros((VH, W), bool)
    shade = np.zeros((VH, W), np.float32)
    for nm, oy, sx in (('far_city', 150, 260), ('far_industry', 96, 40)):
        a = LA.layer('karsk_railyard', nm)['alb']
        h, w = a.shape[:2]
        Y1 = min(VH, oy + h)
        for xs in range(-sx, W, w):
            X0, X1 = max(0, xs), min(W, xs + w)
            if X1 <= X0:
                continue
            m = a[:Y1 - oy, X0 - xs:X1 - xs, 3] > 0.5
            lum = a[:Y1 - oy, X0 - xs:X1 - xs, :3].mean(-1)
            sil[oy:Y1, X0:X1] |= m
            shade[oy:Y1, X0:X1] = np.where(m, lum, shade[oy:Y1, X0:X1])
            gy, gx = np.mgrid[oy:Y1, X0:X1]
            cell = ((gx // 3) * 7919 + (gy // 4) * 104729 + xs * 31 + oy) % 1000 / 1000.0
            lit[oy:Y1, X0:X1] |= m & (lum > 0.62) & (cell > 0.86)
    p.put(sil, 'K', 0.7 + shade[sil] * 1.0 + nz[sil] * 0.3 + glow[sil] * 0.7)
    p.put(lit, 'A', 3.4 + nz[lit] * 1.2)
    # the plant's chimneys with red lamps (the lamps blink at runtime: layout "yard_redlights")
    reds = []
    for (cx_, top) in ((236, 112), (262, 124), (612, 118)):
        p.put(box(cx_, top, cx_ + 5, 214, W), 'K', 1.6 + glow[top + 40, cx_] * 1.2)
        p.put(box(cx_ - 1, top - 2, cx_ + 6, top, W), 'K', 2.2)
        p.put(box(cx_ + 1, top + 3, cx_ + 4, top + 5, W), 'R', 2.0)
        reds.append([cx_ + 2.5, top + 4])
    # the far ground: snow fields under the town glow
    gr = yy >= 212
    p.put(gr, 'S', 1.2 + (yy[gr] - 212) / 34.0 + nz[gr] * 0.5 + glow[gr] * 1.2)
    p.resolve(band=2.0)
    out = p.L.c.copy()
    out[p.L.rid < 0] = 0               # the sky stays a separate layer
    return out, reds


def mid():
    """The far sidings: a rake of covered wagons under snow, the water tower, the gantry, the yard's far lamps."""
    W = MID_W
    R = Q.ramps(K=KNIGHT, S=SNOWK, R=['#0E0807', '#1A0E0B', '#2A1510', '#3C1E16', '#52291C', '#6A3624', '#84462E'],
                I=IRONK, A=AMBER, G=SIGNAL)
    p = C.Paint(W, VH, R, 'ymid')
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 10, 9221)
    lamps = Q.lightfield(W, VH, [(x, 210, 150, 1.0, 1.3) for x in (140, 420, 690)])
    # the water tower on its trestle
    wt = ell(330, 168, 26, 15, W) | box(306, 168, 354, 182, W)
    p.put(wt, 'K', 1.6 + nz[wt] * 0.5 + lamps[wt] * 0.8)
    p.put(box(304, 166, 356, 168, W) | ell(330, 154, 20, 6, W) & (yy < 156), 'S', 4.0)
    for lx_ in (312, 326, 334, 348):
        p.put(box(lx_, 182, lx_ + 2, 236, W), 'K', 1.4)
    p.put(p.line([(312, 196), (348, 222)], r=0.5) | p.line([(348, 196), (312, 222)], r=0.5), 'K', 1.4)
    # the signal gantry over the far tracks, its small red / white lamps
    p.put(box(470, 150, 474, 240, W) | box(640, 150, 644, 240, W), 'I', 1.4)
    p.put(box(466, 148, 648, 154, W), 'I', 1.8)
    p.put(box(466, 146, 648, 148, W), 'S', 4.6)
    for gx in (500, 556, 612):
        p.put(box(gx - 4, 154, gx + 5, 168, W), 'I', 1.2)
        p.put(ell(gx + 0.5, 160, 2, 2, W), 'A' if gx != 556 else 'G', 4.0 if gx != 556 else 4.6)
    # the rake of covered wagons: planked sides, sliding doors, snow on the roofs, couplings, wheels
    for i, wx0 in enumerate(range(-20, W, 78)):
        wx1 = wx0 + 72
        top, bot = 222, 258
        side = box(wx0, top, wx1, bot, W)
        light = lamps[side]
        p.put(side, 'R', 0.6 + nz[side] * 0.6 + light * 2.2 - (np.mod(yy[side] - top, 6) == 0) * 0.5)
        p.put(box(wx0 + 1, top - 4, wx1 - 1, top, W), 'I', 1.4 + lamps[top - 2, max(0, min(W - 1, wx0 + 36))] * 1.4)
        roof = box(wx0 + 2, top - 7, wx1 - 2, top - 4, W) | ell((wx0 + wx1) / 2, top - 6, 36, 3, W) & (yy < top - 4)
        p.put(roof, 'S', 3.0 + lamps[top - 6, max(0, min(W - 1, wx0 + 36))] * 3.0 + nz[roof] * 0.5)
        door = box(wx0 + 28, top + 4, wx0 + 46, bot - 2, W)
        p.put(door, 'R', 0.4 + lamps[door] * 1.6)
        p.put(box(wx0 + 27, top + 3, wx0 + 47, top + 4, W), 'I', 2.0 + lamps[top, max(0, min(W - 1, wx0 + 36))])
        for bx in (wx0 + 4, wx1 - 6):
            p.put(box(bx, top + 2, bx + 2, bot, W), 'I', 1.2 + lamps[top + 10, max(0, min(W - 1, bx))] * 1.4)
        p.put(box(wx0, bot, wx1, bot + 3, W), 'I', 0.8)
        for ax in (wx0 + 14, wx1 - 14):
            p.put(ell(ax, bot + 6, 5, 5, W), 'I', 0.9 + lamps[bot + 4, max(0, min(W - 1, ax))] * 1.6)
            p.put(ell(ax, bot + 6, 1.5, 1.5, W), 'I', 2.6)
        p.put(box(wx1, bot - 6, wx1 + 6, bot - 3, W), 'I', 1.0)                 # coupling
        if i % 3 == 1:                                                         # a chalk mark on a door
            p.put(box(wx0 + 32, top + 12, wx0 + 40, top + 13, W), 'S', 5.0)
    p.put(box(0, 266, W, 268, W), 'I', 1.4 + lamps * 2.0)
    p.put(box(0, 266, W, 267, W), 'I', 2.6 + lamps * 2.0)
    # the far lamp posts (the heads glow at runtime)
    for lx_ in (140, 690):
        p.put(box(lx_, 150, lx_ + 2, 262, W), 'I', 1.4)
        p.put(box(lx_ - 5, 147, lx_ + 7, 151, W), 'I', 2.2)
        p.put(box(lx_ - 3, 151, lx_ + 5, 153, W), 'A', 6.4)
    p.resolve(band=2.0)
    out = p.L.c.copy()
    out[p.L.rid < 0] = 0
    return out


def main_layer():
    """The near yard and the freight office (cam 0 = the film's frame of v3; w3 tracks on to the right)."""
    W = MAIN_W
    R = Q.ramps(K=KNIGHT, S=SNOWK, B=BRICK, C=CONCRETE, I=IRONK, A=AMBER, G=SIGNAL, R=RUST,
                W=['#1A120C', '#2C1E14', '#40301E', '#58442C', '#72583A'])
    p = C.Paint(W, VH, R, 'ymain')
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 14, 9231)
    fine = Q.noise(W, VH, 3, 9233)
    lamps = Q.lightfield(W, VH, [(x, y + 60, 150, 1.0, 1.25) for (x, y) in LAMPS])
    sig = Q.lightfield(W, VH, [(SIG_AT[0], SIG_AT[1] + 20, 110, 1.0, 1.4)])
    wx0, wy0, wx1, wy1 = WINDOW
    s0, s1 = STAIR
    win = Q.lightfield(W, VH, [((wx0 + wx1) / 2, 300, 120, 1.0, 1.35), ((s0 + s1) / 2, 304, 96, 0.9, 1.4),
                               (566, 160, 70, 0.6, 1.4)])
    # ---- the yard surface: snow over ballast, the near siding, sleepers, a trodden path
    gr = yy >= 262
    p.put(gr, 'S', 1.6 + (yy[gr] - 262) / 46.0 + nz[gr] * 0.8 + fine[gr] * 0.3 + lamps[gr] * 2.4 + sig[gr] * 0.7 +
          win[gr] * 2.0)
    for ry in TRACKS_MAIN:
        rail = (yy >= ry) & (yy < ry + 2) & (xx < OFFICE_X - 4)
        p.put(rail, 'I', 2.6 + lamps[rail] * 3.0 + sig[rail] * 1.4)
        p.put(rail & (yy == ry), 'S', 4.6 + lamps[rail & (yy == ry)] * 2.4)
    slp = (yy >= TRACKS_MAIN[0] - 1) & (yy < TRACKS_MAIN[1] + 4) & (np.mod(xx, 11) < 3) & (xx < OFFICE_X - 4) & \
        (fine > 0.35)
    p.put(slp, 'W', 1.4 + lamps[slp] * 1.6)
    ruts = gr & (yy > 286) & (yy < 312) & (np.abs(np.mod(xx * 0.31 + yy * 1.7, 23) - 11) < 0.8) & (fine > 0.4)
    p.put(ruts, 'S', 2.0 + lamps[ruts] * 1.4)
    path = gr & (yy >= FEET - 4) & (yy < FEET + 6)
    p.put(path, 'S', 2.2 + nz[path] * 0.5 + lamps[path] * 2.0 + win[path] * 1.8 + sig[path] * 0.5)
    for k in range(0, 46):                                                     # foot prints toward the office
        fx_, fy_ = 120 + k * 9.5, FEET + (1 if k % 2 else 4)
        p.put(box(fx_, fy_, fx_ + 3, fy_ + 2, W), 'S', 1.6 + lamps[int(fy_), int(min(W - 1, fx_))] * 1.2)
    # ---- the yard lamp at 262 (pole, bracket, shade); the second lamp hangs on the office wall
    for (lx, ly) in LAMPS:
        if lx < OFFICE_X:
            p.put(box(lx - 1, ly, lx + 2, FEET - 2, W), 'I', 1.8 + lamps[ly:FEET, lx].mean() * 1.2)
            p.put(box(lx - 3, FEET - 8, lx + 4, FEET - 2, W), 'I', 1.4)
        else:
            p.put(p.line([(lx + 18, ly - 4), (lx + 6, ly - 4), (lx, ly)], r=0.8), 'I', 2.4)
        shade = poly([(lx - 7, ly + 3), (lx + 8, ly + 3), (lx + 4, ly - 2), (lx - 3, ly - 2)], W)
        p.put(shade, 'I', 2.6)
        p.put(shade & (yy <= ly - 1), 'S', 5.6)
        p.put(box(lx - 4, ly + 3, lx + 5, ly + 5, W), 'A', 7.0)
    # ---- the repaired signal: lattice mast, ladder, platform, the lamp case with the green lens, the arm
    sx, sy = SIG_AT
    mast = box(sx - 3, sy + 8, sx + 3, FEET, W)
    p.put(mast, 'I', 1.6 + sig[mast] * 2.6)
    p.put(mast & (np.mod(yy + xx, 7) < 1), 'I', 0.8)
    p.put(mast & (np.mod(yy - xx, 7) < 1), 'I', 0.9)
    p.put(box(sx + 5, sy + 30, sx + 6, FEET, W) | box(sx + 9, sy + 30, sx + 10, FEET, W), 'I', 2.6 + sig[200, sx] * 1.6)
    for ry in range(sy + 32, FEET, 6):
        p.put(box(sx + 5, ry, sx + 10, ry + 1, W), 'I', 2.8 + sig[min(VH - 1, ry), sx] * 1.6)
    p.put(box(sx - 10, sy + 20, sx + 12, sy + 23, W), 'I', 2.2 + sig[sy + 21, sx] * 1.8)   # platform
    p.put(box(sx - 10, sy + 19, sx + 12, sy + 20, W), 'S', 5.4)
    p.put(box(sx - 10, sy + 12, sx - 9, sy + 20, W) | box(sx + 11, sy + 12, sx + 12, sy + 20, W), 'I', 2.0)
    case = box(sx - 8, sy - 9, sx + 9, sy + 10, W)
    p.put(case, 'K', 1.0 + sig[case] * 1.6)
    p.put(case & C.rim(case, 1, 0), 'K', 2.6 + sig[case & C.rim(case, 1, 0)])
    p.put(ell(sx + 0.5, sy - 2, 5, 5, W), 'G', 5.8)
    p.put(ell(sx + 0.5, sy - 2, 2.5, 2.5, W), 'G', 7.0)
    p.put(ell(sx + 0.5, sy + 5, 2.5, 2.5, W), 'K', 2.2)                       # the dark red lens below
    p.put(p.line([(sx - 9, sy - 9), (sx + 10, sy - 9), (sx + 14, sy - 4)], r=0.6), 'S', 5.6)  # hood + snow
    p.put(box(sx - 11, sy - 12, sx + 12, sy - 9, W), 'S', 6.2)
    p.put(box(sx + 3, sy + 2, sx + 26, sy + 5, W), 'I', 1.8 + sig[sy + 3, sx + 10])           # the repaired arm
    p.put(box(sx + 22, sy + 1, sx + 27, sy + 6, W), 'C', 4.2)                                   # new bolt plate
    # ---- a hand cart with a tarpaulin and two crates by the mast
    cart = box(190, 282, 236, 292, W)
    p.put(cart, 'W', 1.6 + lamps[cart] * 2.0 + sig[cart] * 0.8)
    p.put(box(194, 268, 214, 282, W) | box(216, 272, 232, 282, W), 'W', 2.2 + lamps[275, 212] * 2.0)
    p.put(box(194, 266, 232, 268, W), 'S', 5.6)
    for ax in (198, 228):
        p.put(ell(ax, 294, 4, 4, W), 'I', 1.2 + lamps[294, ax] * 1.6)
    p.put(p.line([(236, 286), (254, 280)], r=0.6), 'I', 2.0)
    # ---- the freight office: brick, plinth, gutter and downpipe, windows, the sign, the door, the stair
    bx0 = OFFICE_X
    wall = (xx >= bx0) & (yy >= 116) & (yy < FEET)
    course = np.mod(yy, 6) == 0
    bond = np.mod(xx + (np.floor(yy / 6) % 2) * 6, 12) == 0
    wl = lamps * 1.4 + win * 1.2
    p.put(wall, 'B', 1.4 + nz[wall] * 0.8 + fine[wall] * 0.3 + wl[wall])
    p.put(wall & (course | bond), 'B', 0.7 + wl[wall & (course | bond)] * 0.7)
    p.put(wall & (fine > 0.82) & ~(course | bond), 'B', 2.4 + wl[wall & (fine > 0.82) & ~(course | bond)])
    p.put(box(bx0, 262, W, FEET, W), 'C', 1.2 + nz * 0.5 + wl * 1.2)   # plinth
    p.put(box(bx0, 262, W, 263, W), 'C', 3.0)
    p.put(box(bx0 - 3, 116, bx0 + 3, FEET, W), 'B', 2.4 + wl[116:FEET, bx0] .mean())                      # pilaster
    # the roof: eaves, gutter, snow, an icicle row, the chimney with smoke at runtime
    roof = poly([(bx0 - 10, 118), (W, 118), (W, 86), (bx0 + 34, 90)], W)
    p.put(roof, 'K', 1.2 + nz[roof] * 0.4)
    p.put(poly([(bx0 - 10, 118), (W, 118), (W, 110), (bx0 - 4, 111)], W), 'S', 4.6 + nz[110:118].mean() * 0.4)
    p.put(box(bx0 - 10, 117, W, 120, W), 'I', 1.6)
    for ix in range(bx0 - 8, W, 7):
        ln = 2 + int(fine[120, min(W - 1, ix)] * 7)
        p.put(box(ix, 120, ix + 1, 120 + ln, W), 'S', 5.2)
    p.put(box(496, 62, 512, 92, W), 'B', 1.6 + nz * 0.6)
    p.put(box(494, 60, 514, 64, W), 'C', 2.4)
    p.put(box(494, 58, 514, 60, W), 'S', 5.0)
    p.put(box(bx0 + 4, 120, bx0 + 8, FEET - 14, W), 'I', 1.6 + wl[120:FEET, bx0 + 6].mean())          # downpipe
    for by_ in range(140, FEET - 14, 34):
        p.put(box(bx0 + 3, by_, bx0 + 9, by_ + 2, W), 'I', 2.6)
    p.put(box(bx0 + 2, FEET - 14, bx0 + 14, FEET - 10, W), 'I', 1.8)
    # upper windows: frames, mullions, sills with snow; one lit (the night clerk), one with a curtain
    for i, wx in enumerate((420, 476, 590, 650)):
        ww = box(wx, 146, wx + 24, 190, W)
        lit = i == 2
        p.put(box(wx - 3, 143, wx + 27, 193, W), 'C', 1.8 + wl[143:193, wx].mean())
        p.put(ww, 'A' if lit else 'K', 3.0 + fine[ww] * 0.8 if lit else 0.5 + lamps[ww] * 0.6 + nz[ww] * 0.4)
        if lit:
            p.put(ww & (yy > 170), 'A', 4.2)                                  # the desk lamp's pool on the sill
            p.put(box(wx + 15, 160, wx + 22, 176, W), 'A', 1.6)               # a coat on a hook
        p.put(box(wx + 11, 146, wx + 13, 190, W) | box(wx, 166, wx + 24, 168, W), 'C', 2.0 + wl[166, wx] * 0.8)
        p.put(box(wx - 4, 190, wx + 28, 194, W), 'C', 2.8)
        p.put(box(wx - 4, 188, wx + 28, 190, W), 'S', 5.4)
        if i == 1:
            p.put(ww & (xx < wx + 8), 'K', 1.4)
    # the sign
    p.put(box(466, 204, 590, 218, W), 'K', 1.0)
    p.put(box(466, 204, 590, 205, W), 'S', 4.6)
    p.put(Q.text_at('ГРУЗОВАЯ КОНТОРА', W, VH, 474, 208, 's'), 'C', 4.6)
    # the door to the yard (shut, a frosted pane, the step)
    door = box(612, 226, 640, FEET - 2, W)
    p.put(door, 'W', 1.6 + nz[door] * 0.4 + wl[door] * 1.4)
    p.put(box(616, 232, 636, 248, W), 'A', 2.2)
    p.put(box(608, 222, 644, 226, W), 'C', 2.6)
    p.put(box(606, FEET - 2, 646, FEET + 2, W), 'C', 2.2)
    p.put(box(632, 262, 635, 266, W), 'I', 3.6)
    # the outside stair down to the cellar: the well, the steps, the warm light rising, the cellar door
    well = box(s0, 270, s1, FEET + 2, W)
    p.put(well, 'A', 1.2 + win[well] * 2.6 - (FEET - yy[well]) / 34.0)
    for k in range(6):
        sy_ = 274 + k * 5
        st_ = box(s0 + 4 + k * 12, sy_, s1, sy_ + 2, W)
        p.put(st_, 'C', 2.0 + win[st_] * 2.0)
    p.put(box(s1, 238, s1 + 14, FEET, W), 'C', 1.6 + win[238:FEET, s1:s1 + 14].mean() * 1.2)
    p.put(box(s1, 234, s1 + 14, 238, W), 'S', 5.4)
    door2 = box(s1 - 26, 260, s1 - 6, FEET, W)
    p.put(door2, 'A', 2.8 + win[door2] * 2.0)
    p.put(box(s1 - 27, 258, s1 - 5, 260, W), 'C', 2.4)
    # the cellar window in its light well: bars, frost flowers, warm lamp light, the shelves seen inside
    cw = box(wx0, wy0, wx1, wy1, W)
    p.put(cw, 'A', 4.0 + Q.noise(W, VH, 3, 9235)[cw] * 1.6)
    p.put(cw & (np.mod(yy - wy0, 6) == 3), 'A', 3.0)                          # shelf boards inside
    p.put(cw & (np.mod(xx - wx0, 9) < 2), 'I', 1.2)
    p.put(box(wx0 - 4, wy0 - 4, wx1 + 4, wy0, W), 'C', 2.6)
    p.put(box(wx0 - 6, wy1, wx1 + 6, FEET + 3, W), 'C', 1.6 + win[wy1:FEET, wx0:wx1].mean() * 1.6)
    frost = cw & (Q.noise(W, VH, 2, 9237) > 0.68) & ((yy > wy1 - 5) | (xx < wx0 + 5) | (xx > wx1 - 5))
    p.put(frost, 'A', 7.2)
    # snow on the ground in front of the office, banked against the wall
    bank = (xx >= bx0) & (yy >= FEET - 6) & (yy < FEET + 14) & ~well & ~box(wx0 - 6, wy1, wx1 + 6, FEET + 3, W)
    p.put(bank, 'S', 3.0 + nz[bank] * 0.8 + lamps[bank] * 1.6 + win[bank] * 2.2)
    p.resolve(band=2.0)
    return p.L.c


def parapet():
    """The concrete parapet along the outside stair (drawn over the figures climbing out), its iron railing."""
    R = Q.ramps(C=CONCRETE, S=SNOWK, I=IRONK, A=AMBER)
    p = C.Paint(MAIN_W, VH, R, 'yparapet')
    yy, xx = p.yy, p.xx
    x0, x1 = STAIR
    nz = Q.noise(MAIN_W, VH, 6, 9241)
    win = Q.lightfield(MAIN_W, VH, [((x0 + x1) / 2, 304, 96, 0.9, 1.4)])
    par = box(x0 - 6, 282, x1, FEET + 12, MAIN_W)
    p.put(par, 'C', 1.8 + nz[par] * 0.8 + (xx[par] - x0) / (x1 - x0) * 0.8 + win[par] * 1.0)
    p.put(par & (np.mod(xx - x0, 24) == 0), 'C', 1.0)
    p.put(box(x0 - 6, 279, x1, 283, MAIN_W), 'S', 5.6 + nz[279:283, x0:x1].mean())
    for px in range(x0, x1, 22):
        p.put(box(px, 262, px + 2, 282, MAIN_W), 'I', 2.4 + win[270, min(MAIN_W - 1, px)] * 2.0)
    p.put(box(x0 - 4, 262, x1, 264, MAIN_W), 'I', 3.0)
    p.put(box(x0 - 4, 261, x1, 262, MAIN_W), 'S', 5.0)
    p.resolve(band=2.0)
    return p.L.c


def glows():
    """(green, warm) additive sprites in main-layer coordinates."""
    sx, sy = SIG_AT
    wx0, wy0, wx1, wy1 = WINDOW
    x0, x1 = STAIR
    green = Q.glow_sprite(MAIN_W, VH, [(sx, sy - 2, 44, 40, (30, 110, 50), 1.4), (sx, sy - 2, 10, 8, (60, 170, 90), 1.6),
                                       (sx, FEET, 70, 10, (10, 44, 22), 1.5)], 6.0)
    warm = Q.glow_sprite(MAIN_W, VH, [((wx0 + wx1) / 2, wy0 + 6, 74, 40, (100, 58, 18), 1.4),
                                      ((x0 + x1) / 2, FEET - 6, 70, 36, (84, 48, 14), 1.4),
                                      (602, 168, 40, 30, (50, 32, 12), 1.5)] +
                         [(x, y + 6, 50, 44, (66, 44, 18), 1.4) for (x, y) in LAMPS] +
                         [(x, FEET, 60, 12, (44, 28, 10), 1.5) for (x, y) in LAMPS], 6.0)
    return green, warm


def layers():
    """{name: rgba} + anchors for the runtimes."""
    fa, reds = far()
    out = {'sky': _sky(), 'far': fa, 'mid': mid(), 'main': main_layer(), 'parapet': parapet()}
    g, w = glows()
    out['green'] = g
    out['warm'] = w
    meta = {'par': {'sky': 0.0, 'far': 0.15, 'mid': 0.5, 'main': 1.0}, 'reds': reds, 'main_w': MAIN_W,
            'chimney': [504, 58], 'lamp_heads': [[140, 152], [690, 152]]}
    return out, meta


def composite(lay, cam=0):
    """The yard as one opaque frame at camera x `cam` (the legacy plate places/yard.png)."""
    c = np.zeros((VH, VW, 4), np.float32)
    c[..., 3] = 1.0
    for nm, par in (('sky', 0.0), ('far', 0.15), ('mid', 0.5), ('main', 1.0)):
        a = lay[nm].astype(np.float32) / 255.0
        LA.over(c, a, int(round(-cam * par)), 0)
    return LA.to8(c)
