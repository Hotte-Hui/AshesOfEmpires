"""env_karsk_skyline_kit -- parametric building kit for the Karsk skyline (Soviet provincial town, 1964).

Every painter draws into a world-row Layer (see env_karsk_skyline_lib) with a plane STYLE (material ramps after
atmospheric perspective) and returns nothing but metadata it may need (anchor points for smoke FX etc.).
Light model: low dawn sun behind haze at the back right -> facades facing the viewer are in shadow (cold
ambient), right edges / returns catch a 1 px rim, top surfaces (snow, ledges) are light, cylinders are dark left /
lit right.  All dimensions are given in metres and converted with the plane scale (px/m), then rounded.
"""
from __future__ import annotations

import math

import numpy as np

from env_karsk_skyline_lib import (Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, CLEAR, put, rect, hline, vline,
                                   line, poly, clear_rect, opaque, dith, cyl_normals, sphere_normals, N_FRONT, N_UP,
                                   N_RIGHT, N_LEFT, N_DOWN, text_masks, emblem_mask, paint_mask, draw_text, value_noise)


# =========================================================================== plane styles
# role order for every material: [deep, sh, body, lit, rim]
STYLES = {
    'far_city': {
        'conc': [SK[0], SK[0], SK[1], SK[2], SK[3]],
        'pale': [SK[0], SK[1], SK[2], SK[3], SK[4]],
        'old': [SK[0], SK[0], SK[0], SK[1], SK[2]],
        'metal': [SK[0], SK[0], SK[0], SK[1], SK[2]],
        'snow': [SK[2], SK[3], SK[4]],
        'glass': SK[0], 'warm': CO[2], 'warm2': CO[1], 'band': RU[5], 'band2': SK[3], 'lamp': RED[3],
        'tree': [SK[0], SK[1]],
    },
    'far_industry': {
        'conc': [TE[4], SK[0], SK[1], SK[2], SK[3]],
        'pale': [SK[0], SK[1], SK[2], SK[3], SK[4]],
        'brick': [TE[4], ST[3], ST[4], ST[5], SK[3]],
        'old': [TE[3], TE[4], SK[0], SK[1], SK[2]],
        'metal': [TE[3], TE[4], SK[0], SK[1], SK[2]],
        'dome': [TE[2], TE[3], TE[4], SK[0], SK[2]],
        'snow': [SK[3], SK[4], SN[2]],
        'glass': TE[4], 'warm': CO[2], 'warm2': CO[1], 'band': RU[4], 'band2': SK[3], 'lamp': RED[3],
        'tree': [TE[4], SK[0]], 'rust': ST[4],
    },
    'mid': {
        'conc': [TE[3], SA[1], SA[3], SA[4], SA[5]],
        'conc_d': [TE[3], SA[1], SA[2], SA[3], SA[4]],
        'white': [SA[1], SA[2], SA[3], SA[4], SA[5]],
        'stucco': [ST[2], ST[3], ST[4], ST[5], SN[2]],
        'logs': [WO[2], WO[3], WO[4], ST[3], ST[4]], 'carve': [SA[3], SA[4]],
        'brick': [WO[2], WO[3], ST[3], ST[4], SA[4]],
        'brick_r': [RU[1], RU[2], RU[3], RU[4], RU[5]],
        'wood': [WO[1], WO[2], WO[3], WO[4], ST[4]],
        'metal': [TE[1], TE[2], TE[3], TE[4], SA[3]],
        'dome': [TE[1], TE[2], TE[3], TE[4], SA[4]],
        'snow': [SN[1], SN[2], SN[3]],
        'glass': TE[3], 'glass_d': TE[2], 'glass_hi': SA[2], 'void': NI[3],
        'warm': CO[3], 'warm2': CO[2], 'band': RED[3], 'band2': SN[2], 'lamp': RED[3],
        'red': [RED[0], RED[1], RED[2], RED[3]], 'rust': [RU[2], RU[3]],
        'tree': [TE[2], TE[3], SA[2]], 'trunk': [SN[1], SN[2]],
    },
    'near_bg': {
        'conc': [TE[0], TE[1], TE[2], TE[3], TE[4]],
        'logs': [NI[3], WO[1], WO[2], WO[3], TE[4]],
        'plank': [TE[0], TE[1], TE[2], TE[3], TE[4]],
        'brick': [NI[3], RU[0], RU[1], RU[2], RU[3]],
        'white': [TE[3], TE[4], SA[2], SA[3], SA[4]],
        'metal': [NI[2], NI[3], TE[1], TE[2], TE[3]],
        'snow': [SN[0], SN[1], SN[2], SN[3]],
        'glass': NI[2], 'glass_hi': TE[3], 'warm': CO[3], 'warm2': CO[2], 'lamp': RED[3],
        'carve': [SA[3], SA[4]], 'tree': [TE[1], TE[2], TE[3]], 'trunk': [SN[1], SN[2]],
        'stove': NI[1],
    },
}


def M(m, plane_ppm):
    """metres -> px (rounded, >= 1)."""
    return max(1, int(round(m * plane_ppm)))


# =========================================================================== generic shapes
def facade(L, x, y, w, h, C, rim=True, left=True):
    """Flat facade facing the viewer: body, darker left return, 1 px rim right."""
    rect(L, x, y, w, h, C[2], N_FRONT)
    if left:
        vline(L, x, y, h, C[1], N_LEFT)
    if rim:
        vline(L, x + w - 1, y, h, C[4], N_RIGHT)


def snow_line(L, x, y, w, S, depth=1, seed=0, ragged=0.25):
    """Snow on a horizontal top edge (row y = top surface)."""
    rng = np.random.default_rng(abs(int(seed)) + 7)
    sn = S['snow']
    for xx in range(int(x), int(x + w)):
        d = depth + (1 if rng.random() < ragged else 0)
        for k in range(d):
            put(L, xx, y + k, sn[-1] if k == 0 else sn[-2], N_UP)


def snow_on_tops(L, x0, y0, x1, y1, S, depth=1, coverage=0.9, seed=0, mask_cols=None):
    """Snow on every upward-facing top edge of opaque pixels inside the box (roofs, ledges, sills)."""
    rng = np.random.default_rng(seed + 11)
    sn = S['snow']
    a = L.c[..., 3] > 0
    for yy in range(max(1, y0), min(L.h, y1)):
        for xx in range(max(0, x0), min(L.w, x1)):
            if a[yy, xx] and not a[yy - 1, xx] and rng.random() < coverage:
                if mask_cols is not None and not any((L.c[yy, xx, :3] == c[:3]).all() for c in mask_cols):
                    continue
                for k in range(depth):
                    if yy + k < L.h and a[yy + k, xx]:
                        put(L, xx, yy + k, sn[-1] if k == 0 else sn[-2], N_UP)


def gable_roof(L, x, y_eave, w, rise, C, overhang=1, snow=True, S=None, seed=0, steep=None, ridge_cut=0):
    """Symmetric gable seen from the long side? -> NO: a gable END facing the viewer (triangle).
    The triangle sits on (x .. x+w) at row y_eave and peaks `rise` px higher.  Shaded: left half sh, right lit."""
    cx = x + w / 2.0
    for k in range(rise + 1):
        t = k / max(1, rise)
        half = (w / 2.0 + overhang) * (1 - t)
        xa, xb = int(round(cx - half)), int(round(cx + half))
        yy = y_eave - k
        for xx in range(xa, xb):
            c = C[1] if xx < cx else C[2]
            put(L, xx, yy, c, N_FRONT)
        if xb - 1 >= xa:
            put(L, xb - 1, yy, C[4], N_RIGHT)
    return int(round(cx))


def pitched_roof_side(L, x, y_eave, w, rise, C, S, overhang=2, seed=0, snow_cov=1.0, slope_px=None):
    """Long side of a pitched roof seen from the front: trapezoid from eave (wide) to ridge (narrower when hipped)
    -- here as a plain band of `rise` rows: snowy (snow covers most of the slope), dark eave line."""
    rng = np.random.default_rng(seed + 5)
    sn = S['snow']
    for k in range(rise):
        yy = y_eave - 1 - k
        inset = 0 if slope_px is None else int(k * slope_px)
        for xx in range(x - overhang + inset, x + w + overhang - inset):
            t = k / max(1, rise - 1)
            if rng.random() < snow_cov * (0.55 + 0.45 * t):
                c = sn[-1] if (k == rise - 1 or rng.random() < 0.35) else sn[-2]
            else:
                c = C[3] if rng.random() < 0.5 else C[2]
            put(L, xx, yy, c, N_UP)
    hline(L, x - overhang, y_eave, w + 2 * overhang, C[0], N_DOWN)


def cylinder_v(L, x, y, w, h, C, joints=0, seed=0, lit_frac=0.18):
    """Vertical cylinder (silo, tank, tower shaft) lit from the back right."""
    for i in range(w):
        u = (i + 0.5) / w
        if i == w - 1:
            c = C[4]
        elif u > 1 - lit_frac:
            c = C[3]
        elif u > 1 - lit_frac - 0.12:
            c = None   # dither band body/lit
        elif u < 0.1:
            c = C[0]
        elif u < 0.3:
            c = C[1]
        else:
            c = C[2]
        for yy in range(y, y + h):
            cc = c
            if cc is None:
                cc = C[3] if dith(x + i, yy, 0.5) else C[2]
            put(L, x + i, yy, cc)
    if joints:
        for jy in range(y + joints, y + h, joints):
            for i in range(2, w - 3):
                xx = x + i
                if (xx + jy) % 2:
                    continue
                cur = L.c[jy, xx]
                if (cur[:3] == C[2][:3]).all():
                    put(L, xx, jy, C[1])
    cyl_normals(L, x, y, w, h)


def chimney(L, cx, base, h, wb, wt, C, bands=None, band_cols=None, seed=0, lip=True):
    """Tapered chimney; bands = number of aviation stripes at the top (alternating band_cols)."""
    top = base - h
    for k in range(h):
        t = k / max(1, h - 1)                     # 0 top .. 1 base
        w = wt + (wb - wt) * t
        x0 = int(round(cx - w / 2))
        x1 = int(round(cx + w / 2))
        yy = top + k
        for xx in range(x0, x1):
            u = (xx - x0 + 0.5) / max(1, x1 - x0)
            c = C[1] if u < 0.34 else (C[4] if xx == x1 - 1 else C[2])
            put(L, xx, yy, c)
    if bands and band_cols:
        bh = max(1, int(round(h * 0.045)))
        for b in range(bands):
            yy0 = top + 1 + b * bh
            col = band_cols[b % 2]
            for yy in range(yy0, min(base, yy0 + bh)):
                t = (yy - top) / max(1, h - 1)
                w = wt + (wb - wt) * t
                x0 = int(round(cx - w / 2))
                x1 = int(round(cx + w / 2))
                for xx in range(x0, x1):
                    u = (xx - x0 + 0.5) / max(1, x1 - x0)
                    if col is None:
                        continue
                    c = col[0] if u < 0.34 else (col[2] if xx == x1 - 1 else col[1])
                    put(L, xx, yy, c)
    if lip:
        hline(L, int(round(cx - wt / 2)) - 1, top, int(round(wt)) + 2, C[0])
    cyl_normals(L, int(round(cx - wb / 2)) - 1, top - 1, int(round(wb)) + 2, h + 1)
    return (int(round(cx)), top)


def lattice_mast(L, cx, base, h, wb, wt, col, rim=None, step=4, lights=None, light_col=None, guys=None,
                 guy_col=None):
    """Lattice tower (radio/TV mast, crane mast at distance).  lights: list of heights (px above base) for red
    obstruction lamps (emission)."""
    top = base - h
    for k in range(h):
        t = k / max(1, h - 1)
        w = wt + (wb - wt) * t
        xl = int(round(cx - w / 2))
        xr = int(round(cx + w / 2))
        yy = top + k
        put(L, xl, yy, col)
        put(L, xr, yy, rim if rim is not None else col)
        if w >= 3 and (k % step == 0):
            for xx in range(xl, xr + 1):
                put(L, xx, yy, col)
        if w >= 3 and step > 2:
            ph = (k % step) / step
            xd = int(round(xl + (xr - xl) * (ph if (k // step) % 2 == 0 else 1 - ph)))
            put(L, xd, yy, col)
    if guys:
        for (gh, gx) in guys:
            gy = base - gh
            pg_pts = [(cx, gy), (cx + gx, base)]
            line(L, cx, gy, cx + gx, base, guy_col if guy_col is not None else col)
    if lights and light_col is not None:
        for lh in lights:
            ly = base - lh
            put(L, cx, ly, light_col, em=light_col)
            if lh == max(lights):
                put(L, cx, ly - 1, light_col, em=light_col)
    return (cx, top)


def birch(L, x, base, h, S, seed=0, lean=0.0, crown=0.75, twig_density=1.0, trunk_cols=None, twig_cols=None,
          mark=None):
    """Bare winter birch: pale trunk with dark marks, upward limbs, fine drooping twigs (hazy plane colours)."""
    rng = np.random.default_rng(seed)
    tc = trunk_cols or S.get('trunk', [SN[1], SN[2]])
    tw = twig_cols or S['tree']
    mark = mark if mark is not None else NI[3]
    th = int(h * 0.85)
    pts = []
    for k in range(th):
        xx = x + int(round(math.sin(k / 13.0 + seed) * 0.9 + lean * k))
        put(L, xx, base - k, tc[0])
        if k < th * 0.5 and h > 26:
            put(L, xx + 1, base - k, tc[1])
        if (k * 7 + seed) % 9 == 0 and k > 3:
            put(L, xx, base - k, mark)
        pts.append((xx, base - k))

    def limb(x0, y0, ang, ln, depth):
        segs = max(2, int(ln / 3))
        cx_, cy_ = x0, y0
        for i in range(segs):
            a2 = ang + rng.uniform(-0.22, 0.22)
            nx = cx_ + math.cos(a2) * ln / segs
            ny = cy_ - math.sin(a2) * ln / segs
            line(L, cx_, cy_, nx, ny, tw[0] if depth > 1 else tw[-1])
            cx_, cy_ = nx, ny
            if depth > 0 and rng.random() < 0.5 * twig_density:
                side = rng.choice([-1, 1])
                limb(cx_, cy_, ang + side * rng.uniform(0.4, 0.9), ln * rng.uniform(0.35, 0.6), depth - 1)
        if depth <= 1:
            for _ in range(int(rng.integers(1, 3))):
                line(L, cx_, cy_, cx_ + rng.uniform(-1.5, 1.5), cy_ + rng.uniform(2, 5), tw[-1])

    n_limbs = max(3, int(h / 9))
    for i in range(n_limbs):
        k = int(th * rng.uniform(1 - crown, 0.97))
        sx, sy = pts[min(k, len(pts) - 1)]
        side = -1 if i % 2 else 1
        limb(sx, sy, math.pi / 2 + side * rng.uniform(0.25, 0.8), h * rng.uniform(0.16, 0.3), 2)
    limb(pts[-1][0], pts[-1][1], math.pi / 2 + rng.uniform(-0.2, 0.2), h * 0.16, 2)


def spruce(L, x, base, h, cols, snow=None, seed=0, w_ratio=0.42):
    """Dark conical spruce with layered branch tiers and snow on the tier tops."""
    rng = np.random.default_rng(seed)
    w = max(3, int(h * w_ratio))
    for k in range(h):
        t = k / max(1, h - 1)                 # 0 top -> 1 bottom
        tier = (k % 5) / 5.0
        half = (0.5 + w / 2.0 * t) * (0.75 + 0.25 * tier)
        xa = int(round(x - half))
        xb = int(round(x + half))
        for xx in range(xa, xb + 1):
            c = cols[0] if xx < x else cols[1]
            put(L, xx, base - h + k, c)
        if snow is not None and k % 5 == 0 and k > 1:
            for xx in range(xa, xb + 1):
                if rng.random() < 0.6:
                    put(L, xx, base - h + k, snow)
    vline(L, x, base - 2, 2, cols[0])


def antenna(L, x, roof_y, h, col, bars=2, bw=3, tilt=0):
    """Rooftop TV antenna: mast + crossbars."""
    for k in range(h):
        put(L, x + (tilt if k > h * 0.6 else 0), roof_y - 1 - k, col)
    for b in range(bars):
        yy = roof_y - h + b * 2
        hline(L, x - bw // 2 + (tilt if True else 0), yy, bw, col)


def pylon(L, cx, base, h, col, rim=None, arms=2):
    """Soviet steel lattice power pylon (portal/'goblet' style) at distance: tapering shaft + arms."""
    wb = max(3, int(round(h * 0.28)))
    for k in range(h):
        t = k / max(1, h - 1)
        w = 1 + (wb - 1) * (t ** 1.2)
        xl = int(round(cx - w / 2))
        xr = int(round(cx + w / 2))
        put(L, xl, base - h + k, col)
        put(L, xr, base - h + k, rim if rim is not None else col)
        if w > 2 and k % 3 == 0:
            put(L, cx, base - h + k, col)
    aw = max(3, int(round(h * 0.45)))
    for a in range(arms):
        ay = base - h + 1 + a * max(2, int(h * 0.16))
        hline(L, cx - aw // 2, ay, aw, col)
        put(L, cx - aw // 2, ay + 1, col)
        put(L, cx + aw // 2 - 1, ay + 1, col)
    return [(cx - aw // 2, base - h + 2), (cx + aw // 2 - 1, base - h + 2)]


def wire(L, x0, y0, x1, y1, sag, col):
    n = max(2, int(abs(x1 - x0)))
    prev = None
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(x)), int(round(y)))
        if prev is not None and p != prev:
            line(L, prev[0], prev[1], p[0], p[1], col)
        prev = p


# =========================================================================== windows
def window(L, x, y, w, h, S, kind='dark', frame=None, sill=True, em_rng=None, curtain=None):
    """One window: kind dark | lit | curtain | void | boarded | frost.  frame: colour of a 1 px frame (around)."""
    glass = S['glass']
    if frame is not None:
        rect(L, x - 1, y - 1, w + 2, h + 2, frame)
    if kind == 'lit':
        rect(L, x, y, w, h, S['warm'], N_FRONT, em=S['warm'])
        if w >= 3 and h >= 3:
            put(L, x, y + h - 1, S['warm2'], em=S['warm2'])
    elif kind == 'void':
        rect(L, x, y, w, h, S.get('void', NI[3]))
    elif kind == 'boarded':
        rect(L, x, y, w, h, WO[2])
        for yy in range(y + 1, y + h, 2):
            hline(L, x, yy, w, WO[3])
    else:
        rect(L, x, y, w, h, glass)
        if kind == 'curtain' and w >= 3:
            vline(L, x, y, h, curtain if curtain is not None else S.get('glass_hi', glass))
        elif kind == 'refl' and w >= 2:
            put(L, x + w - 1, y, S.get('glass_hi', glass))
    if sill:
        hline(L, x - (1 if w >= 4 else 0), y + h, w + (2 if w >= 4 else 0), S['snow'][-1], N_UP)


def arched_window(L, x, y, w, h, S, kind='dark', frame=None, sill=True):
    """Round-headed window (w odd works best)."""
    r = w / 2.0
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dy = yy - y
            if dy < r:
                dx = xx + 0.5 - (x + r)
                if dx * dx + (r - dy - 0.5) ** 2 > r * r + 0.3:
                    continue
            if kind == 'lit':
                put(L, xx, yy, S['warm'], N_FRONT, em=S['warm'])
            elif kind == 'boarded':
                put(L, xx, yy, WO[3] if (yy - y) % 2 else WO[2])
            elif kind == 'void':
                put(L, xx, yy, S.get('void', NI[3]))
            else:
                put(L, xx, yy, S['glass'])
    if sill:
        hline(L, x - 1, y + h, w + 2, S['snow'][-1], N_UP)


# =========================================================================== KHRUSHCHYOVKA (panel block)
def khrushchyovka(L, x, base, S, ppm, sections=2, bays=5, floors=5, seed=0, built=None, detail=2,
                  balcony_bays=(1, 3), lit=0.06, antennas=3, laundry=True, crane_panel=False, mat='conc',
                  stair_bay=2, entrance=True, bay_px=None):
    """Five-storey prefabricated panel block (series 1-464 / K-7 look), long side facing the viewer.
    bays per section (stair bay in the middle of each section); detail 0 far / 1 medium / 2 mid-plane.
    built: number of finished floors (under construction) or None.  Returns dict with geometry."""
    rng = np.random.default_rng(seed)
    C = S[mat]
    bay = bay_px or max(3, int(round(3.2 * ppm * 0.86)))  # ~2.75 m bays read better than 3.2 m at this size
    fh = max(3, int(round(2.75 * ppm)))
    plinth = max(1, int(round(0.9 * ppm)))
    parapet = max(1, int(round(0.4 * ppm)))
    end = max(1, int(round(0.5 * ppm)))
    W = sections * bays * bay + 2 * end
    nfl = floors if built is None else built
    H = plinth + nfl * fh + (parapet if built is None else 0)
    top = base - H
    # body
    facade(L, x, top, W, H, C)
    # plinth (darker, cellar vents)
    rect(L, x, base - plinth, W, plinth, C[1])
    if detail >= 2:
        for vx in range(x + end + 2, x + W - 2, bay):
            put(L, vx, base - plinth + plinth // 2, C[0])
    # floor lines / panel joints
    for f in range(nfl + 1):
        fy = base - plinth - f * fh
        if detail >= 1 and 0 < f <= nfl:
            for xx in range(x + 1, x + W - 1):
                if detail >= 2 or (xx % 2 == 0):
                    put(L, xx, fy, C[1] if detail >= 2 else C[1])
    if detail >= 2:
        for s in range(sections):
            for b in range(bays + 1):
                jx = x + end + s * bays * bay + b * bay
                for yy in range(top + (parapet if built is None else 0), base - plinth):
                    if (yy + jx) % 3 != 0:
                        put(L, jx, yy, C[1])
    info = {'x': x, 'w': W, 'top': top, 'bays': [], 'stairs': []}
    win_w = max(1, int(round(1.35 * ppm)))
    win_h = max(1, int(round(1.45 * ppm)))
    for s in range(sections):
        for b in range(bays):
            bx = x + end + (s * bays + b) * bay
            is_stair = (b == stair_bay)
            info['bays'].append(bx)
            for f in range(nfl):
                fy = base - plinth - (f + 1) * fh          # top row of this floor
                if is_stair:
                    if detail == 0:
                        continue
                    sw = max(1, win_w - 2 if detail >= 2 else 1)
                    sh = max(1, int(round(win_h * 0.7)))
                    sx = bx + (bay - sw) // 2
                    sy = fy + fh // 2 + max(1, fh // 4) - sh // 2 - fh // 2 + 1   # half a floor lower
                    sy = fy + max(1, (fh - sh) // 2) + fh // 2
                    if sy + sh < base - plinth:
                        if detail >= 2:
                            window(L, sx, sy, sw, sh, S, 'dark', sill=False)
                        else:
                            rect(L, sx, sy, sw, sh, S['glass'])
                    continue
                wx = bx + (bay - win_w) // 2
                wy = fy + max(1, (fh - win_h) // 2)
                if detail == 0:
                    if (wx + wy) % 2 == 0 or rng.random() < 0.4:
                        put(L, wx, wy, S['glass'])
                    continue
                roll = rng.random()
                kind = 'dark'
                if roll < lit:
                    kind = 'lit'
                elif roll < lit + 0.25 and detail >= 2:
                    kind = 'curtain'
                elif roll < lit + 0.4:
                    kind = 'refl'
                has_balc = detail >= 2 and (b in balcony_bays) and f >= 1
                if has_balc:
                    # balcony door + window (glass reaches the slab), slab + railing in front
                    window(L, wx, wy, win_w, fh - (wy - fy) - 1, S, kind if kind != 'curtain' else 'dark',
                           sill=False)
                    _balcony(L, bx, fy + fh, bay, ppm, S, C, rng, laundry=laundry)
                else:
                    if detail >= 2:
                        window(L, wx, wy, win_w, win_h, S, kind, sill=(f == 0))
                    else:
                        rect(L, wx, wy, win_w, win_h, S['warm'] if kind == 'lit' else S['glass'],
                             em=S['warm'] if kind == 'lit' else None)
            if is_stair and entrance and detail >= 1:
                dw = max(1, win_w - 1)
                dh = max(2, int(round(2.1 * ppm)))
                dx = bx + (bay - dw) // 2
                rect(L, dx, base - plinth - dh + plinth, dw, dh, S['glass'] if detail < 2 else NI[3])
                if detail >= 2:
                    # concrete canopy over the entrance + snow
                    cy = base - dh - 1
                    hline(L, dx - 2, cy, dw + 4, C[3], N_UP)
                    hline(L, dx - 2, cy - 1, dw + 4, S['snow'][-1], N_UP)
                    put(L, dx - 2, cy + 1, C[1])
                    put(L, dx + dw + 1, cy + 1, C[1])
            info['stairs'].append(bx) if is_stair else None
    # roof: parapet line with snow, antennas, vent stacks
    if built is None:
        hline(L, x, top, W, C[3], N_UP)
        snow_line(L, x, top - 1, W, S, depth=1, seed=seed, ragged=0.3)
        if detail >= 1:
            for s in range(sections):
                vx = x + end + s * bays * bay + int(bays * bay * 0.5) - 2
                rect(L, vx, top - max(1, int(ppm * 0.6)) - 1, max(2, int(ppm * 0.8)), max(1, int(ppm * 0.6)), C[2])
                hline(L, vx, top - max(1, int(ppm * 0.6)) - 2, max(2, int(ppm * 0.8)), S['snow'][-1], N_UP)
        for a in range(antennas):
            ax = x + 3 + int(rng.uniform(0.05, 0.95) * (W - 6))
            ah = max(2, int(round(rng.uniform(1.4, 2.4) * ppm)))
            antenna(L, ax, top - 1, ah, S['metal'][1] if 'metal' in S else C[0], bars=2 if ah > 5 else 1,
                    bw=3 if ppm > 3 else 3, tilt=int(rng.integers(-1, 2)) if ppm > 3 else 0)
    else:
        # unfinished: raw top slab edge, some standing wall panels of the next floor, rebar stubs
        hline(L, x, top, W, C[3], N_UP)
        k = 0
        px_ = x + end
        while px_ < x + W - bay and k < 3:
            if rng.random() < 0.65:
                facade(L, px_, top - fh, bay, fh, C)
                wx = px_ + (bay - win_w) // 2
                rect(L, wx, top - fh + max(1, (fh - win_h) // 2), win_w, win_h, S.get('void', NI[3]))
                hline(L, px_, top - fh - 1, bay, S['snow'][-1], N_UP)
                k += 1
            px_ += bay
        for xx in range(x + 2, x + W - 2, 4):
            put(L, xx, top - 1, C[0])
        snow_line(L, x, top, W, S, depth=1, seed=seed + 3, ragged=0.1)
    # right rim + a touch of sky bounce on the upper right corner
    vline(L, x + W - 1, top, H, C[4], N_RIGHT)
    info['h'] = H
    return info


def _balcony(L, bx, slab_y, bay, ppm, S, C, rng, laundry=True):
    """Balcony on a bay: slab (light top + snow), railing panel, laundry / firewood / box."""
    bw = bay - 2
    x0 = bx + 1
    rh = max(2, int(round(1.0 * ppm)))
    # railing panel (corrugated sheet: alternating columns)
    for xx in range(x0, x0 + bw):
        for yy in range(slab_y - rh, slab_y):
            c = C[3] if (xx - x0) % 2 == 0 else C[2]
            if xx == x0:
                c = C[1]
            put(L, xx, yy, c, N_FRONT)
    hline(L, x0, slab_y, bw, C[1], N_DOWN)                          # slab edge (shadow below)
    hline(L, x0, slab_y - rh - 1, bw, S['snow'][-1], N_UP)          # snow on the rail
    put(L, x0 + bw - 1, slab_y - rh, C[4], N_RIGHT)
    roll = rng.random()
    if laundry and roll < 0.3:
        # line strung across the balcony with 2-3 items (muted cloth colours, one warm accent sometimes)
        ly = slab_y - rh - 3
        cols = [SN[3], SN[2], SA[4], RU[4], TE[4], CO[1]]
        xx = x0 + 1
        while xx < x0 + bw - 1:
            iw = int(rng.integers(1, 3))
            ih = int(rng.integers(2, 4))
            col = cols[int(rng.integers(0, len(cols)))]
            rect(L, xx, ly, iw, ih, col)
            xx += iw + 1
    elif roll < 0.75:
        # firewood stack / boxes behind the rail, peeking above it
        sx = x0 + int(rng.integers(0, max(1, bw - 3)))
        rect(L, sx, slab_y - rh - 2, 3, 2, WO[2])
        put(L, sx + 1, slab_y - rh - 2, WO[3])
        put(L, sx, slab_y - rh - 3, S['snow'][-1])
    elif roll < 0.85:
        # skis / a sled leaned on the wall
        vline(L, x0 + bw - 2, slab_y - rh - 4, 4, WO[3])


# =========================================================================== GRAIN ELEVATOR
def grain_elevator(L, x, base, S, ppm, seed=0):
    """Reinforced-concrete grain elevator: battery of five silos with the conveyor gallery on top, the tall
    working house at the right end, a sloped conveyor bridge to the receiving building, slip-form joints, rain
    streaks.  One silo carries the patched shell hole.  Returns anchors (gallery top, tower top, ...)."""
    rng = np.random.default_rng(seed)
    C = S['conc']
    Cd = S['conc_d']
    d = 24                                   # silo diameter (5 m)
    hs = 98                                  # silo height (~20.6 m)
    n = 5
    sx0 = x
    stop = base - hs
    for i in range(n):
        cylinder_v(L, sx0 + i * d, stop, d, hs, C, joints=7, seed=seed + i)
        # V-notch shadow where neighbouring silos meet (star bins between them)
        if i > 0:
            vline(L, sx0 + i * d, stop, hs, C[0])
    # rain/soot streaks under the gallery
    for _ in range(12):
        xx = sx0 + int(rng.integers(1, n * d - 1))
        y0 = stop + int(rng.integers(0, 4))
        ln = int(rng.integers(6, 22))
        for yy in range(y0, min(base, y0 + ln)):
            cur = L.c[yy, xx]
            for a_, b_ in ((C[2], C[1]), (C[3], C[2]), (C[4], C[3])):
                if (cur[:3] == a_[:3]).all() and rng.random() < 0.8:
                    put(L, xx, yy, b_)
                    break
    # patched shell hole on silo 2 (index 1): lighter newer concrete, ragged dark seam, rebar hints
    hx_, hy_ = sx0 + d + 6, stop + 36
    patch = [(0, 3), (2, 1), (3, 2), (5, 0), (7, 1), (8, 0), (10, 2), (11, 5), (10, 7), (11, 9), (9, 11),
             (7, 10), (5, 12), (3, 10), (1, 11), (0, 8), (-1, 6)]
    m, mx, my = L.poly_mask([(hx_ + a, hy_ + b) for a, b in patch])
    L._put(m, mx, my, C[3])
    p = np.pad(m, 1)
    edge = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    ys, xs = np.nonzero(edge)
    for yy, xx in zip(ys, xs):                      # seam only on the shadow side and the bottom (ragged)
        if xx + mx < hx_ + 7 or yy + my > hy_ + 8:
            if (xx + yy) % 3:
                put(L, xx + mx, yy + my, C[1])
    for (a, b) in ((3, 4), (4, 4), (7, 6), (6, 8)):   # trowel marks of the newer concrete
        put(L, hx_ + a, hy_ + b, C[4])
    line(L, hx_ + 11, hy_ + 5, hx_ + 15, hy_ + 2, C[1])  # cracks radiating from the old hit
    line(L, hx_ + 1, hy_ + 11, hx_ - 2, hy_ + 16, C[1])
    # gallery on top of the battery (corrugated, small windows), snow on its roof
    gx0, gx1 = sx0 - 2, sx0 + n * d + 3
    gh = 9
    gtop = stop - gh
    facade(L, gx0, gtop, gx1 - gx0, gh, Cd)
    for xx in range(gx0 + 1, gx1 - 1):
        if xx % 2 == 0:
            for yy in range(gtop + 1, stop):
                if (L.c[yy, xx, :3] == Cd[2][:3]).all():
                    put(L, xx, yy, Cd[3] if yy < gtop + 3 else Cd[2])
    for wx in range(gx0 + 4, gx1 - 4, 7):
        rect(L, wx, gtop + 3, 3, 3, S['glass'])
    hline(L, gx0, stop, gx1 - gx0, C[0], N_DOWN)
    hline(L, gx0 - 1, gtop, gx1 - gx0 + 2, Cd[3], N_UP)
    snow_line(L, gx0 - 1, gtop - 1, gx1 - gx0 + 2, S, depth=1, seed=seed + 1)
    # working house (tall tower) at the right end
    tx0 = sx0 + n * d + 1
    tw = 33
    th = 146
    ttop = base - th
    facade(L, tx0, ttop, tw, th, Cd)
    vline(L, tx0 + 1, ttop, th, Cd[1])
    for k in range(tx0 + 3, tx0 + tw - 2, 6):           # board-formed vertical texture, faint
        for yy in range(ttop + 4, base, 2):
            if (yy // 2 + k) % 3 == 0:
                put(L, k, yy, Cd[1])
    # stair-window column (left third), floors every 9 px
    for yy in range(ttop + 22, base - 12, 9):
        rect(L, tx0 + 6, yy, 2, 4, S['glass'])
    # distributor floor: band of windows near the top
    rect(L, tx0 + 3, ttop + 8, tw - 6, 5, S['glass'])
    for k in range(tx0 + 3, tx0 + tw - 3, 4):
        vline(L, k, ttop + 8, 5, Cd[2])
    hline(L, tx0 + 3, ttop + 13, tw - 6, S['snow'][-1], N_UP)
    # lettering band (year) on the tower: "1936" in tiny numerals
    # machine room on the roof + lightning rod
    mx0 = tx0 + 5
    facade(L, mx0, ttop - 9, tw - 10, 9, Cd)
    rect(L, mx0 + 4, ttop - 6, 5, 3, S['glass'])
    snow_line(L, mx0 - 1, ttop - 10, tw - 8, S, depth=1, seed=seed + 2)
    hline(L, tx0 - 1, ttop, tw + 2, Cd[3], N_UP)
    snow_line(L, tx0 - 1, ttop - 1, 5, S, depth=1, seed=seed + 3)
    snow_line(L, tx0 + tw - 4, ttop - 1, 5, S, depth=1, seed=seed + 4)
    vline(L, mx0 + tw - 13, ttop - 17, 8, Cd[0])
    # conveyor bridge from the tower down-right to the receiving building
    bx0, by0 = tx0 + tw, ttop + 46
    bx1, by1 = bx0 + 46, base - 44
    for k in range(0, bx1 - bx0):
        t = k / max(1, bx1 - bx0 - 1)
        yy = int(round(by0 + (by1 - by0) * t))
        for j in range(5):
            put(L, bx0 + k, yy + j, Cd[2] if j else Cd[3])
        put(L, bx0 + k, yy + 5, Cd[0])
        if k % 6 == 0:
            line(L, bx0 + k, yy + 6, bx0 + k + 3, yy + 9, Cd[0])
    # receiving building (brick, low gable) + rail siding canopy
    rx0 = bx1 - 6
    rh = 40
    facade(L, rx0, base - rh, 34, rh, S['brick'])
    for yy in range(base - rh + 2, base, 3):
        for xx in range(rx0 + 1, rx0 + 33):
            if (xx + yy) % 5:
                put(L, xx, yy, S['brick'][1])
    for wx in (rx0 + 5, rx0 + 14, rx0 + 23):
        arched_window(L, wx, base - rh + 8, 5, 9, S)
    gable_roof(L, rx0, base - rh - 1, 34, 8, S['metal'], overhang=1)
    snow_on_tops(L, rx0 - 2, base - rh - 12, rx0 + 37, base - rh + 2, S, depth=1, seed=seed + 5)
    return {'gallery_top': gtop - 1, 'gallery_x': (gx0, gx1), 'tower': (tx0, tw, ttop), 'silos': (sx0, n, d, stop),
            'right': rx0 + 34}


def slogan_width(text_s, emblem=None, gap=4):
    from env_karsk_skyline_lib import text_width
    w = text_width(text_s, 'B', spacing=1)
    if emblem:
        w += gap + emblem_mask(emblem).shape[1]
    return w


def rooftop_slogan(L, x, roof_y, text_s, S, emblem=None, gap=4, frame_col=None, snow=0.35, seed=0, lift=2):
    """Soviet rooftop slogan: individual red sheet-metal letters (bold block capitals) standing on a low steel
    frame on a roof: one base rail, two thin posts under every letter, nothing crossing the letters.
    emblem: mask kind drawn to the right of the text (neutral gear-and-wheat 'gw*' or the historical hammer &
    sickle 'hs*' -- identical footprint, so only the emblem pixels differ between the two variants).
    Returns {'x', 'w', 'top', 'emblem_box'}."""
    red = S['red']
    fc = frame_col if frame_col is not None else S['metal'][1]
    glyphs = text_masks(text_s, 'B', spacing=1)
    tw = (glyphs[-1][0] + glyphs[-1][1].shape[1]) if glyphs else 0
    gh = 7
    em_m = emblem_mask(emblem) if emblem else None
    total = tw + ((gap + em_m.shape[1]) if em_m is not None else 0)
    ly = roof_y - lift - gh                               # letter top row
    base_rail = roof_y - 1
    hline(L, x - 1, base_rail, total + 2, fc)
    rng = np.random.default_rng(seed)
    for ox, m in glyphs:
        hh, ww = m.shape
        for px_ in (x + ox + 1, x + ox + ww - 2):
            vline(L, px_, ly + gh, base_rail - (ly + gh), fc)
        paint_mask(L, x + ox, ly, m, red[2], shade=red[1])
        # rim of the low sun on the right edges of the strokes
        for yy in range(hh):
            for xx in range(ww):
                if m[yy, xx] and (xx + 1 >= ww or not m[yy, xx + 1]) and yy < hh - 1:
                    put(L, x + ox + xx, ly + yy, red[3])
        for xx in range(ww):                                  # snow on the letter tops
            if m[0, xx] and rng.random() < snow:
                put(L, x + ox + xx, ly, S['snow'][-1], N_UP)
    box = None
    if em_m is not None:
        eh, ew = em_m.shape
        ex = x + tw + gap
        ey = ly + gh - eh + 1
        paint_mask(L, ex, ey, em_m, red[2], shade=red[1])
        for yy in range(eh):
            for xx in range(ew):
                if em_m[yy, xx] and (xx + 1 >= ew or not em_m[yy, xx + 1]):
                    put(L, ex + xx, ey + yy, red[3])
        if emblem.startswith('gw'):                    # fictional emblem: golden wheat ear inside the red gear
            c0 = (ew - 1) / 2.0
            for yy in range(eh):
                for xx in range(ew):
                    if em_m[yy, xx] and math.hypot(xx - c0, yy - c0) < c0 - 1.6:
                        put(L, ex + xx, ey + yy, CO[2] if (xx + yy) % 3 else CO[1])
        vline(L, ex + ew // 2, ey + eh, max(0, base_rail - (ey + eh)), fc)
        box = (ex, ey, ew, eh)
    return {'x': x, 'w': total, 'top': min(ly, (box[1] if box else ly)), 'emblem_box': box}


def tiny_person(L, x, base, h, body, rim, head=None, pose='stand'):
    """Far-away person for scale (h = 1.75 m * plane px/m): cap, padded coat, legs; 1 px rim on the sun side."""
    head = head if head is not None else body
    hw = 2 if h >= 8 else 1
    rect(L, x, base - h, hw, max(1, h // 5), head)
    th = max(2, int(h * 0.5))
    rect(L, x - (1 if h >= 8 else 0), base - h + max(1, h // 5), hw + (1 if h >= 8 else 0), th, body)
    ly = base - h + max(1, h // 5) + th
    if pose == 'walk':
        put(L, x - 1, base - 1, body)
        put(L, x + hw - 1, base - 1, body)
        rect(L, x, ly, 1, max(1, base - ly - 1), body)
    else:
        rect(L, x, ly, hw, base - ly, body)
    vline(L, x + hw - 1, base - h + max(1, h // 5), th, rim)
