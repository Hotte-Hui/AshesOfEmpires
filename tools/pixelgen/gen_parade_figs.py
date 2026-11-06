"""gen_parade_figs -- figure kit + figure designs of the parade atlas (owner: parade).  Used by gen_parade.py.
Original procedural pixel art, deterministic, berlin palette only (pg.PALETTES['berlin']).

A figure is a list of PARTS (filled shapes in figure units: x right, y up, feet centre at (0, 0), an adult is
~0.85..1.0 tall = 1.8 m) plus DETAILS (strokes, dots and small fills rasterised at the TARGET resolution, so seams,
buttons, buckles and folds stay crisp 1-px marks on every LOD and simply drop out below their `minh`).
render(fig, h) draws one LOD strip cell at 1 texel = 1 px:
  * supersampled majority labels (thin parts such as rifles survive on the small strips),
  * per-part cylindrical shading lit from the upper left (dithered band seams on the large strips),
  * contact-shadow lines where a part lies over another part, snow caught on upward edges (shoulders, hats,
    helmets), a 1-px night outline, overlay parts without outline (breath).
Tone: the people are cold, anonymous, dwarfed -- troops' faces stay a shadow under the helmet, nobody poses.
"""
from __future__ import annotations
import math

import numpy as np
from PIL import Image, ImageDraw

import pg

B = pg.PALETTES['berlin']
OUTLINE = B['night'][0]

# dark -> light ramps, every colour taken from the berlin palette
RAMPS = {
    'coal':    ['#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#443B43'],
    'violet':  ['#1B1520', '#25202B', '#342F37', '#443B43', '#57494D', '#6E6A73'],
    'steel':   ['#1E2329', '#2F363F', '#454E58', '#5F6973', '#7C8690', '#A3ACB4'],
    'stone':   ['#2A2130', '#4A3A35', '#5F4A40', '#7A5E4E', '#94735C', '#AE8A6C', '#C9A585'],
    'ochre':   ['#4A3A35', '#5F4530', '#735145', '#8D5542', '#AF6C47', '#D07744'],
    'snow':    ['#443B43', '#57494D', '#6E6A73', '#8F8A92', '#B2ACB0', '#D2CCCB', '#ECE6E0'],
    'skin':    ['#2A2130', '#4A3A35', '#5F4A40', '#7A5E4E', '#94735C', '#AE8A6C', '#C9A585'],
    'leather': ['#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#454E58'],
    'wood':    ['#2A2130', '#4A3A35', '#5F4530', '#735145', '#8D5542'],
    'metal':   ['#120C14', '#1E2329', '#2F363F', '#454E58', '#5F6973', '#7C8690', '#A3ACB4'],
}
RNAMES = list(RAMPS)
RGB = [np.array([pg.hx(c)[:3] for c in RAMPS[k]], np.uint8) for k in RNAMES]
BIG = 10 ** 6


def cell_size(h):
    return max(3, int(round(0.7 * h)) + 3), h + 2


# ------------------------------------------------------------------------------------------- geometry
def ell(cx, cy, rx, ry, n=28, a0=0.0, a1=None):
    if a1 is None:
        return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def seg(p0, p1, w0, w1=None):
    w1 = w0 if w1 is None else w1
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * 0.5, dx / ln * 0.5
    return [(p0[0] + nx * w0, p0[1] + ny * w0), (p1[0] + nx * w1, p1[1] + ny * w1),
            (p1[0] - nx * w1, p1[1] - ny * w1), (p0[0] - nx * w0, p0[1] - ny * w0)]


def limb(pts, ws, end_caps=False):
    """Thick polyline: one quad per segment + round joints (and optionally round ends)."""
    polys = [seg(pts[i], pts[i + 1], ws[i], ws[i + 1]) for i in range(len(pts) - 1)]
    for i, p in enumerate(pts):
        if 0 < i < len(pts) - 1 or end_caps:
            polys.append(ell(p[0], p[1], ws[i] * 0.5, ws[i] * 0.5, 14))
    return polys


def mirror(pts):
    return [(-x, y) for x, y in pts]


def ik_knee(hip, foot, l1, l2, fwd=1.0):
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 1e-4)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    mx, my = hip[0] + ux * a, hip[1] + uy * a
    # perpendicular pointing forward (+x * fwd)
    px, py = -uy, ux
    if px * fwd < 0:
        px, py = -px, -py
    return (mx + px * hh, my + py * hh)


# ------------------------------------------------------------------------------------------- figure kit
class Fig:
    def __init__(self, outline=True, puff=False):
        self.parts = []
        self.details = []
        self.overlays = []
        self.outline = outline
        self.puff = puff
        # snow caught on upward edges (render): None = the default even cover; a civilian sets his own share of
        # covered edge pixels, its ramp index and a seed, so a packed crowd does not wear one identical pale dash
        # on every hat
        self.snow_amt = None
        self.snow_idx = 4
        self.snow_seed = 0

    def part(self, name, ramp, i, polys, shade='cyl', minh=0, maxh=BIG, sep=True, snow=False, lit=0.0, rim=0,
             tex=0.0):
        if polys and isinstance(polys[0], tuple):
            polys = [polys]
        if not tex and name in ('coat', 'arm'):
            tex = 0.05
        self.parts.append({'name': name, 'ramp': ramp, 'i': i, 'polys': polys, 'shade': shade, 'minh': minh,
                           'maxh': maxh, 'sep': sep, 'snow': snow, 'lit': lit, 'rim': rim, 'tex': tex})

    def line(self, pts, rel=-1, minh=40, clip=None, col=None, maxh=BIG, w=1):
        self.details.append({'k': 'line', 'pts': pts, 'rel': rel, 'col': col, 'minh': minh, 'maxh': maxh,
                             'clip': clip, 'w': w})

    def dot(self, x, y, rel=1, minh=40, clip=None, col=None, r=0.0, maxh=BIG):
        self.details.append({'k': 'dot', 'pts': [(x, y)], 'rel': rel, 'col': col, 'minh': minh, 'maxh': maxh,
                             'clip': clip, 'r': r})

    def fill(self, pts, rel=-1, minh=40, clip=None, col=None, maxh=BIG):
        self.details.append({'k': 'fill', 'pts': pts, 'rel': rel, 'col': col, 'minh': minh, 'maxh': maxh,
                             'clip': clip})

    def overlay(self, ramp, i, polys, minh=0):
        if polys and isinstance(polys[0], tuple):
            polys = [polys]
        self.overlays.append({'ramp': ramp, 'i': i, 'polys': polys, 'minh': minh})


def _row_extents(polys_px, ch):
    x0 = np.full(ch, np.inf)
    x1 = np.full(ch, -np.inf)
    ys = np.arange(ch) + 0.5
    for pts in polys_px:
        P = np.asarray(pts, np.float64)
        Q = np.roll(P, -1, 0)
        ya, yb = P[:, 1][:, None], Q[:, 1][:, None]
        xa, xb = P[:, 0][:, None], Q[:, 0][:, None]
        cross = ((ya <= ys) & (ys < yb)) | ((yb <= ys) & (ys < ya))
        with np.errstate(divide='ignore', invalid='ignore'):
            xi = xa + (ys - ya) * (xb - xa) / (yb - ya)
        xi = np.where(cross, xi, np.nan)
        if np.isnan(xi).all():
            continue
        x0 = np.fmin(x0, np.nanmin(np.where(cross, xi, np.inf), 0))
        x1 = np.fmax(x1, np.nanmax(np.where(cross, xi, -np.inf), 0))
    return x0, x1


BAYER2 = np.array([[0.125, 0.625], [0.875, 0.375]])


def _cyl(u, w, h, bay):
    """Shade offset across a part (u = 0 lit left edge .. 1 shadow edge)."""
    if h < 9:
        return np.where((u > 0.62) & (w >= 2), -1, 0)
    if h < 30:
        return np.where((u < 0.2) & (w >= 4), 1, np.where(u > 0.64, -1, 0))
    s = np.interp(u, [0.0, 0.16, 0.58, 0.86, 1.0], [1.5, 0.5, -0.5, -1.5, -2.0])
    # dithered band seams only across wide parts (coats); on a head or a sleeve they read as checker noise
    amp = np.where(w >= 16, 0.55, 0.0) if h >= 80 else 0.0
    off = np.ceil(s - 0.5 + (bay - 0.5) * amp)
    off = np.where(w < 6, np.clip(off, -1, 1), off)
    return off


def _shift(a, dy, dx, fill):
    out = np.full_like(a, fill)
    H, W = a.shape
    ys = slice(max(dy, 0), H + min(dy, 0))
    yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0))
    xd = slice(max(-dx, 0), W + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def render(fig, h, outline=None):
    cw, ch = cell_size(h)
    ax, ay = cw // 2, h + 1
    out = np.zeros((ch, cw, 4), np.uint8)
    outline = fig.outline if outline is None else outline
    if h <= 4:
        return _render_tiny(fig, h, out)
    ss = 8 if h < 40 else (6 if h < 100 else 4)
    parts = [p for p in fig.parts if p['minh'] <= h <= p['maxh']]
    if not parts:
        return out

    def PX(x, y):
        return (ax + x * h, ay - y * h)
    lab = Image.new('L', (cw * ss, ch * ss), 0)
    dr = ImageDraw.Draw(lab)
    for n, p in enumerate(parts):
        for poly in p['polys']:
            dr.polygon([(X * ss, Y * ss) for X, Y in (PX(x, y) for x, y in poly)], fill=n + 1)
    big = np.asarray(lab)
    blk = big.reshape(ch, ss, cw, ss).transpose(0, 2, 1, 3).reshape(ch, cw, ss * ss)
    cov = (blk > 0).mean(-1)
    counts = np.zeros((ch, cw, len(parts)), np.int16)
    for v in np.unique(big):
        if v:
            counts[..., v - 1] = (blk == v).sum(-1)
    lab1 = counts.argmax(-1)
    solid = cov >= (0.42 if h >= 8 else 0.3)

    names = []
    gid = np.zeros(len(parts), np.int32)
    for n, p in enumerate(parts):
        if p['name'] not in names:
            names.append(p['name'])
        gid[n] = names.index(p['name'])
    grp = gid[lab1]
    sep = np.array([p['sep'] for p in parts])[lab1]
    snowp = np.array([p['snow'] for p in parts])[lab1]
    rimp = np.array([p['rim'] for p in parts])[lab1]
    rid = np.zeros((ch, cw), np.int16)
    idx = np.zeros((ch, cw), np.int16)
    yy, xx = np.mgrid[0:ch, 0:cw]
    bay = BAYER2[yy & 1, xx & 1]
    for n, p in enumerate(parts):
        m = solid & (lab1 == n)
        if not m.any():
            continue
        rid[m] = RNAMES.index(p['ramp'])
        off = np.zeros((ch, cw))
        if p['shade'] == 'cyl':
            x0, x1 = _row_extents([[PX(x, y) for x, y in poly] for poly in p['polys']], ch)
            w = (x1 - x0)[:, None] * np.ones((1, cw))
            with np.errstate(invalid='ignore'):
                u = np.clip(((xx + 0.5) - x0[:, None]) / np.maximum(w, 1e-3), 0.0, 1.0)
            u = np.nan_to_num(u, nan=0.5)
            w = np.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)
            off = _cyl(u, w, h, bay) + p['lit']
            off = np.where(w < 3, p['lit'], off)
        elif p['lit']:
            off = off + p['lit']
        idx[m] = (p['i'] + np.round(off))[m]
    # sparse wool / cloth texture on the large strips
    if h >= 86:
        hsh = ((xx * 73856093) ^ (yy * 19349663)) % 997 / 997.0
        for n, p in enumerate(parts):
            if p.get('tex'):
                m = solid & (lab1 == n) & (hsh < p['tex'])
                idx[m] -= 1
    # details at the target resolution
    for d in fig.details:
        if not (d['minh'] <= h <= d['maxh']):
            continue
        im = Image.new('L', (cw, ch), 0)
        dd = ImageDraw.Draw(im)
        pts = [(ax + x * h - 0.5, ay - y * h - 0.5) for x, y in d['pts']]
        if d['k'] == 'line':
            dd.line(pts, fill=255, width=d['w'])
        elif d['k'] == 'fill':
            dd.polygon(pts, fill=255)
        else:
            r = d['r'] * h
            if r < 0.75:
                dd.point(pts, fill=255)
            else:
                dd.ellipse([pts[0][0] - r + 0.5, pts[0][1] - r + 0.5, pts[0][0] + r - 0.5, pts[0][1] + r - 0.5],
                           fill=255)
        m = (np.asarray(im) > 0) & solid
        if d['clip']:
            ids = [names.index(c) for c in d['clip'] if c in names]
            m &= np.isin(grp, ids)
        if not m.any():
            continue
        if d['col'] is not None:
            rid[m] = RNAMES.index(d['col'][0])
            idx[m] = d['col'][1]
        else:
            idx[m] += d['rel']
    # contact shadow where a later part overlaps an earlier one
    if h >= 21:
        dark = np.zeros((ch, cw), bool)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nl = _shift(lab1, dy, dx, -1)
            ns = _shift(solid, dy, dx, False)
            ng = _shift(grp, dy, dx, -1)
            nsep = _shift(sep, dy, dx, False)
            dark |= solid & ns & (nl > lab1) & (ng != grp) & sep & nsep
        idx[dark] -= 1
    # upward edges: snow on shoulders / hats / helmets, rim light
    if h >= 12:
        up_open = solid & ~_shift(solid, 1, 0, False)
        rim = up_open & (rimp > 0)
        idx[rim] += rimp[rim]
        run = up_open & _shift(up_open, 0, 1, False) & _shift(up_open, 0, -1, False)
        run |= up_open & (_shift(run, 0, 1, False) | _shift(run, 0, -1, False))
        hsh = ((xx * 7919) ^ (yy * 104729)) % 101
        if fig.snow_amt is None:
            sn = run & snowp & (hsh >= 9)
        else:
            hs2 = ((xx * 7919 + fig.snow_seed * 6151) ^ (yy * 104729 + fig.snow_seed * 389)) % 101
            sn = run & snowp & (hs2 < int(round(fig.snow_amt * 101)))
        lite = np.zeros_like(sn)
        if h >= 49:     # thicker, irregular caps on the large strips
            lite = sn & (hsh < 30)
            below = _shift(sn, 1, 0, False) & solid & snowp & (hsh % 3 != 0)
            if h >= 150:
                below |= _shift(below, 1, 0, False) & solid & snowp & (hsh % 4 == 0)
            sn |= below
        rid[sn] = RNAMES.index('snow')
        idx[sn] = fig.snow_idx
        idx[lite] = fig.snow_idx + 1
    lens = np.array([len(RAMPS[k]) for k in RNAMES])
    idx = np.clip(idx, 0, lens[rid] - 1)
    for r in range(len(RNAMES)):
        m = solid & (rid == r)
        out[m, :3] = RGB[r][idx[m]]
    out[solid, 3] = 255
    if outline and h >= 11:
        nb = np.zeros_like(solid)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb |= _shift(solid, dy, dx, False)
        edge = nb & ~solid
        out[edge, :3] = pg.hx(OUTLINE)[:3]
        out[edge, 3] = 255
        if h >= 16:
            # selective outline: the rim takes a dark shade of the cloth it bounds (light coats get lighter
            # rims, so a packed crowd does not fuse into one black mass); the ground line stays night
            for dy, dx in ((0, 1), (0, -1), (1, 0)):
                nr = _shift(rid, dy, dx, -1)
                ni = _shift(idx, dy, dx, 0)
                ns = _shift(solid, dy, dx, False)
                m = edge & ns & (nr >= 0)
                for r in range(len(RNAMES)):
                    mm = m & (nr == r)
                    if mm.any():
                        out[mm, :3] = RGB[r][np.clip(ni[mm] - 2, 0, len(RAMPS[RNAMES[r]]) - 1)]
                edge = edge & ~m
    if fig.puff and h >= 6:
        # dissolving edge: checker-out the outer ring, thin the second ring
        a = out[:, :, 3] > 0
        inner = a.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            inner &= _shift(a, dy, dx, False)
        inner2 = inner.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            inner2 &= _shift(inner, dy, dx, False)
        out[(a & ~inner) & (((xx + yy) % 2) == 0), 3] = 0
        out[(inner & ~inner2) & ((xx % 2 == 0) & (yy % 2 == 0)), 3] = 0
    for ov in fig.overlays:
        if h < ov['minh']:
            continue
        im = Image.new('L', (cw * ss, ch * ss), 0)
        dd = ImageDraw.Draw(im)
        for poly in ov['polys']:
            dd.polygon([(X * ss, Y * ss) for X, Y in (PX(x, y) for x, y in poly)], fill=255)
        c2 = (np.asarray(im).reshape(ch, ss, cw, ss) > 0).mean((1, 3))
        m = c2 >= 0.45
        if h >= 30:
            inner = m.copy()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                inner &= _shift(m, dy, dx, False)
            m &= inner | (((xx + yy) % 2) == 0)
        r = RNAMES.index(ov['ramp'])
        out[m, :3] = RGB[r][ov['i']]
        out[m, 3] = 255
    return out


def _render_tiny(fig, h, out):
    ref_h = 40
    ref = render(fig, ref_h, outline=False)
    rcw, rch = cell_size(ref_h)
    cw, ch = cell_size(h)
    ax = cw // 2
    cols = [ax - 1, ax] if fig.puff else [ax]
    for r in range(h):
        y = (h - r - 0.5) / h
        ry = min(max(int((ref_h + 1) - y * ref_h), 0), rch - 1)
        row = ref[ry]
        best = None
        for dx in (0, -1, 1, -2, 2, -3, 3):
            c = rcw // 2 + dx
            if 0 <= c < rcw and row[c, 3] > 0:
                best = row[c]
                break
        if best is None:
            continue
        for cx in cols:
            out[1 + r, cx] = best
    return out


# ------------------------------------------------------------------------------------------- civilians (backs)
def _legs(f, hip, lw, ramp, shoe, spread, shift=0.0, fem=False, socks=None):
    for side in (-1, 1):
        xt = side * spread * 0.85 + shift * 0.5
        xb = side * (spread + 0.004) + (shift if side > 0 else 0.0) * 0.4
        f.part('legs', ramp[0], ramp[1] - (1 if side > 0 else 0), limb([(xt, hip), (xb, 0.045)], [lw, lw * 0.8]),
               sep=False)
        if socks:
            f.part('socks', socks[0], socks[1], seg((xb, 0.04), (xb, 0.11), lw * 0.82, lw * 0.85), sep=False)
        sw_ = lw * (0.55 if fem else 0.6)
        heel = [(xb - sw_, 0.0), (xb - sw_, 0.03), (xb - sw_ * 0.7, 0.048), (xb + sw_ * 0.7, 0.048),
                (xb + sw_, 0.03), (xb + sw_, 0.0)]
        f.part('shoe', shoe[0], shoe[1], heel, sep=False)
        f.dot(xb - sw_ * 0.4, 0.035, rel=2, minh=86, clip=('shoe',))


def _arm(f, s, side, kind, sw, sh, hip, waist, ramp, glove, fem):
    sx, sy = side * (sw - 0.032), sh - 0.02
    aw0, aw1 = (0.054, 0.044) if fem else (0.062, 0.05)
    lit = 0.0 if side < 0 else -0.6
    hand = None
    if kind in ('down', 'bag', 'cane', 'hold'):
        pts = [(sx, sy), (side * (sw - 0.002), sy - 0.19), (side * (sw - 0.014), hip - 0.035)]
        hand = (side * (sw - 0.016), hip - 0.07)
        if kind == 'hold':      # reaching down and out to a child's hand
            pts = [(sx, sy), (side * (sw + 0.012), sy - 0.18), (side * (sw + 0.05), hip - 0.06)]
            hand = (side * (sw + 0.058), hip - 0.09)
    elif kind == 'pockets':
        pts = [(sx, sy), (side * (sw + 0.02), sy - 0.18), (side * (sw - 0.045), hip + 0.012)]
    elif kind == 'behind':
        pts = [(sx, sy), (side * (sw + 0.004), sy - 0.18), (side * 0.04, hip - 0.02)]
    else:   # crossed
        pts = [(sx, sy), (side * (sw + 0.024), waist + 0.03), (side * (sw - 0.035), waist + 0.012)]
    f.part('arm', ramp[0], ramp[1], limb(pts, [aw0, aw0 * 0.92, aw1]), lit=lit, snow=False)
    # sleeve crease at the elbow + cuff
    ex, ey = pts[1]
    f.line([(ex - side * 0.012, ey + 0.012), (ex + side * 0.006, ey - 0.012)], rel=-1, minh=65, clip=('arm',))
    wx, wy = pts[2]
    f.line([(wx - 0.022, wy + 0.03), (wx + 0.022, wy + 0.03)], rel=-1, minh=86, clip=('arm',))
    if hand:
        f.part('hand', glove[0], glove[1], ell(hand[0], hand[1], 0.021, 0.03, 16), sep=True)
        f.dot(hand[0] - 0.008, hand[1] + 0.012, rel=1, minh=86, clip=('hand',))
    if kind == 'bag':
        bx, by = hand
        bag = s.get('bag', ('coal', 2))
        f.part('bag', bag[0], bag[1], [(bx - 0.045, by - 0.03), (bx + 0.045, by - 0.03), (bx + 0.05, by - 0.14),
                                         (bx - 0.05, by - 0.14)])
        f.line([(bx - 0.045, by - 0.05), (bx + 0.045, by - 0.05)], rel=-1, minh=37, clip=('bag',))
        f.dot(bx, by - 0.06, col=('metal', 5), minh=49, clip=('bag',))
    if kind == 'cane':
        bx, by = hand
        f.part('cane', 'wood', 3, limb([(bx, by + 0.02), (bx + side * 0.035, 0.0)], [0.016, 0.014]), sep=True)
    if kind == 'behind' and side > 0:
        f.part('hand', glove[0], glove[1], ell(0.0, hip - 0.032, 0.04, 0.03, 18))
        f.line([(0.0, hip - 0.012), (0.0, hip - 0.05)], rel=-1, minh=49, clip=('hand',))


def _hat(f, kind, ramp, hy, s):
    r, i = ramp
    if kind == 'fedora' or kind == 'homburg':
        b = hy + 0.014
        brim = [(-0.088, b - 0.003), (-0.074, b + 0.01), (0.074, b + 0.01), (0.088, b - 0.003), (0.06, b - 0.015),
                (0.0, b - 0.019), (-0.06, b - 0.015)]
        if kind == 'fedora':
            crown = [(-0.056, b + 0.004), (-0.051, b + 0.055), (-0.026, b + 0.066), (0.0, b + 0.059),
                     (0.026, b + 0.066), (0.051, b + 0.055), (0.056, b + 0.004)]
        else:
            crown = [(-0.053, b + 0.004), (-0.052, b + 0.048), (-0.04, b + 0.062), (0.04, b + 0.062),
                     (0.052, b + 0.048), (0.053, b + 0.004)]
        f.part('hat', r, i, brim, snow=True)
        f.part('hat', r, i, crown, snow=True)
        f.part('hatband', 'coal', 1, [(-0.056, b + 0.003), (-0.055, b + 0.022), (0.055, b + 0.022),
                                      (0.056, b + 0.003)], minh=12, shade='flat')
        if kind == 'fedora':
            f.line([(0.0, b + 0.057), (0.0, b + 0.036)], rel=-1, minh=37, clip=('hat',))
            f.line([(-0.04, b + 0.054), (-0.032, b + 0.036)], rel=-1, minh=86, clip=('hat',))
        else:
            f.line([(0.0, b + 0.06), (0.0, b + 0.036)], rel=-1, minh=37, clip=('hat',))
            f.line([(-0.086, b - 0.001), (0.086, b - 0.001)], rel=1, minh=49, clip=('hat',))
    elif kind == 'cap':
        crown = [(-0.058, hy - 0.002), (-0.064, hy + 0.034), (-0.045, hy + 0.058), (0.045, hy + 0.058),
                 (0.064, hy + 0.034), (0.058, hy - 0.002), (0.0, hy + 0.006)]
        f.part('hat', r, i, crown, snow=True)
        f.line([(0.0, hy + 0.055), (0.0, hy + 0.01)], rel=-1, minh=49, clip=('hat',))
        f.line([(-0.056, hy + 0.012), (0.056, hy + 0.012)], rel=-1, minh=65, clip=('hat',))
    elif kind == 'beret':
        f.part('hat', r, i, ell(0.012, hy + 0.045, 0.062, 0.026, 24), snow=True)
        f.part('hat', r, i, ell(0.0, hy + 0.028, 0.05, 0.02, 20), snow=False)
        f.dot(0.012, hy + 0.074, rel=0, minh=37, clip=None, col=(r, max(i - 1, 0)))
    elif kind == 'scarf':
        f.part('hscarf', r, i, ell(0.0, hy + 0.004, 0.057, 0.069, 28), snow=True)
        f.part('hscarf', r, i, [(-0.052, hy - 0.03), (0.052, hy - 0.03), (0.004, hy - 0.118)])
        f.line([(-0.035, hy + 0.05), (-0.02, hy - 0.04), (0.0, hy - 0.1)], rel=-1, minh=49, clip=('hscarf',))
        f.line([(0.03, hy + 0.04), (0.02, hy - 0.05)], rel=-1, minh=65, clip=('hscarf',))
        f.line([(-0.05, hy - 0.032), (0.05, hy - 0.032)], rel=-1, minh=37, clip=('hscarf',))
        if s.get('pattern'):
            # printed border + a sparse motif, only where it can be drawn as marks (a dot grid on a 10 px head
            # turns into checker noise)
            f.line([(-0.054, hy - 0.012), (0.0, hy - 0.11)], rel=-2, minh=86, clip=('hscarf',))
            f.line([(0.054, hy - 0.012), (0.0, hy - 0.11)], rel=-2, minh=86, clip=('hscarf',))
            for gx in np.arange(-0.036, 0.04, 0.036):
                for gy in np.arange(-0.07, 0.07, 0.044):
                    f.dot(gx + (0.018 if int(round(gy / 0.044)) % 2 else 0.0), hy + gy, rel=-1, minh=262,
                          clip=('hscarf',))
    elif kind == 'knit':
        dome = [(-0.056, hy - 0.016), (-0.058, hy + 0.026), (-0.04, hy + 0.06), (0.0, hy + 0.072),
                (0.04, hy + 0.06), (0.058, hy + 0.026), (0.056, hy - 0.016)]
        f.part('hat', r, i, dome, snow=True)
        f.part('hatcuff', r, i + 1, [(-0.06, hy - 0.022), (-0.06, hy + 0.012), (0.06, hy + 0.012),
                                     (0.06, hy - 0.022)])
        for k in range(-3, 4):
            f.line([(k * 0.014, hy + 0.012), (k * 0.014, hy - 0.02)], rel=-1, minh=150 if k % 2 == 0 else 262,
                   clip=('hatcuff',))
            if k % 2 == 0:
                f.line([(k * 0.014, hy + 0.055 - abs(k) * 0.006), (k * 0.014, hy + 0.016)], rel=-1, minh=198,
                       clip=('hat',))
        if s.get('pompom'):
            f.part('hat', r, i + 1, ell(0.0, hy + 0.08, 0.022, 0.02, 14), snow=True)
    elif kind == 'furhat':
        body = ell(0.0, hy + 0.03, 0.07, 0.05, 30)
        f.part('hat', r, i, body, snow=True)
        for k in range(7):
            a = math.pi * (0.1 + 0.8 * k / 6)
            f.part('hat', r, i, ell(0.064 * math.cos(a), hy + 0.03 + 0.048 * math.sin(a), 0.016, 0.014, 10),
                   snow=True)
        for side in (-1, 1):
            f.part('hat', r, i - 1, [(side * 0.045, hy + 0.01), (side * 0.066, hy + 0.01), (side * 0.062, hy - 0.045),
                                     (side * 0.044, hy - 0.04)])
        for k in range(10):
            f.dot(-0.055 + k * 0.012, hy + 0.03 + 0.012 * ((k * 7) % 3 - 1), rel=-1, minh=150 if k % 2 else 262,
                  clip=('hat',))
    elif kind == 'cloche':
        f.part('hat', r, i, ell(0.0, hy + 0.027, 0.055, 0.05, 26), snow=True)
        f.part('hat', r, i, [(-0.064, hy - 0.012), (-0.06, hy + 0.01), (0.06, hy + 0.01), (0.064, hy - 0.012),
                             (0.0, hy - 0.02)])
        f.line([(-0.055, hy + 0.018), (0.055, hy + 0.018)], col=('ochre', 2), rel=0, minh=37, clip=('hat',))
    elif kind == 'hood':
        f.part('hat', r, i, ell(0.0, hy + 0.006, 0.058, 0.066, 26), snow=True)
        f.part('hat', r, i, [(-0.058, hy - 0.01), (0.058, hy - 0.01), (0.03, hy - 0.08), (-0.03, hy - 0.08)])
        f.line([(0.0, hy + 0.07), (0.0, hy - 0.07)], rel=-1, minh=37, clip=('hat',))


def civ(s):
    """A civilian seen from behind (the crowd behind the barriers)."""
    f = Fig()
    H = s.get('H', 0.95)
    sw = s.get('sw', 0.125)
    fem = s.get('fem', False)
    kid = s.get('kid', False)
    hunch = s.get('hunch', 0.0)
    cr, ci = s['coat']
    sh = (0.76 if kid else 0.815) * H - hunch * 0.5
    waist = (0.56 if kid else 0.6) * H
    hip = (0.47 if kid else 0.5) * H
    hem = s.get('hem', 0.3) * H
    head_r = (0.042, 0.05) if kid else (0.049, 0.062)
    hy = H - head_r[1] - hunch * 0.9 - (0.014 if s.get('bowed') else 0.0)
    turn = s.get('turn', 0)
    skin = ('skin', s.get('skin', 3))
    glove = s.get('glove', ('coal', 2))
    shift = s.get('shift', 0.0)
    # legs + shoes (shoes stay dark: the snow at their feet comes from the ground)
    lw = 0.045 if kid else (0.05 if fem else 0.072)
    spread = 0.032 if kid else (0.04 if fem else 0.05)
    _legs(f, hip, lw, s.get('legs', ('coal', 2)), s.get('shoe', ('coal', 1)), spread, shift, fem,
          s.get('socks'))
    if s.get('skirt'):
        r2, i2 = s['skirt']
        f.part('skirt', r2, i2, [(-sw * 0.78, hem + 0.01), (sw * 0.78, hem + 0.01), (sw * 0.8, hem - 0.05),
                                 (-sw * 0.8, hem - 0.05)])
    # long hair hangs behind the coat collar region: drawn after the coat (see below)
    belt = s.get('belt', False)
    fl = s.get('flare', 0.026 if s.get('hem', 0.3) < 0.42 else 0.0)
    wx = sw * (0.8 if (belt or fem) else 0.88)
    hx_ = sw * 0.92 + (0.012 if fem else 0.0)
    body = [(-0.038, sh + 0.035), (0.038, sh + 0.035), (sw * 0.62, sh + 0.018), (sw - 0.01, sh - 0.006),
            (sw - 0.02, sh - 0.11), (wx, waist), (hx_, hip), (sw * 0.9 + fl, hem + 0.008), (0.0, hem),
            (-(sw * 0.9 + fl), hem + 0.008), (-hx_, hip), (-wx, waist), (-(sw - 0.02), sh - 0.11),
            (-(sw - 0.01), sh - 0.006), (-sw * 0.62, sh + 0.018)]
    f.part('coat', cr, ci, body, snow=True)
    # coat details: centre back seam, vent, folds, quilting, back yoke light
    f.line([(0.0, sh - 0.03), (0.0, hem + 0.1)], rel=-1, minh=49, clip=('coat',))
    if s.get('hem', 0.3) < 0.42:
        f.line([(0.0, hem + 0.1), (0.0, hem)], rel=-2, minh=28, clip=('coat',))
        f.line([(-sw * 0.45, waist - 0.03), (-sw * 0.7, hem + 0.02)], rel=-1, minh=65, clip=('coat',))
        f.line([(sw * 0.4, waist - 0.04), (sw * 0.62, hem + 0.03)], rel=-1, minh=65, clip=('coat',))
        f.line([(-sw * 0.15, hip - 0.02), (-sw * 0.25, hem + 0.04)], rel=-1, minh=114, clip=('coat',))
    f.line([(-sw * 0.62, sh - 0.04), (-sw * 0.25, sh - 0.065)], rel=1, minh=86, clip=('coat',))
    f.line([(-sw * 0.6, sh - 0.1), (-sw * 0.5, waist + 0.04)], rel=-1, minh=86, clip=('coat',))
    if s.get('quilted'):
        yq = waist - 0.05
        while yq < sh - 0.02:
            f.line([(-sw, yq), (sw, yq)], rel=-1, minh=37, clip=('coat',))
            yq += 0.05
    if belt:
        f.part('belt', cr, ci - 1, [(-wx - 0.004, waist - 0.012), (wx + 0.004, waist - 0.012),
                                    (wx + 0.004, waist + 0.012), (-wx - 0.004, waist + 0.012)], minh=16)
    elif s.get('hem', 0.3) < 0.42 and not fem:
        f.part('belt', cr, ci, [(-sw * 0.5, waist - 0.01), (sw * 0.5, waist - 0.01), (sw * 0.5, waist + 0.012),
                                (-sw * 0.5, waist + 0.012)], minh=28)
        for side in (-1, 1):
            f.dot(side * sw * 0.44, waist + 0.001, rel=2, minh=65, clip=('belt',))
    # arms
    arms = s.get('arms', 'down')
    al, ar = (arms, arms) if isinstance(arms, str) else arms
    for side, k in ((-1, al), (1, ar)):
        if k:
            _arm(f, s, side, k, sw, sh, hip, waist, (cr, ci), glove, fem)
    # neck, head, hair
    nk = 0.02 if kid else 0.023
    f.part('neck', skin[0], skin[1] - 1, [(-nk, sh + 0.02), (-nk, hy - 0.02), (nk, hy - 0.02), (nk, sh + 0.02)])
    hat = s.get('hat')
    hair = s.get('hair', ('coal', 2))
    hk = hat[0] if hat else None
    covers_ears = hk in ('scarf', 'furhat', 'hood')
    rx, ry = head_r
    if not covers_ears and not s.get('long_hair'):
        for side in (-1, 1):
            f.part('ear', skin[0], skin[1] - (0 if side < 0 else 1),
                   ell(side * (rx - 0.002) + turn * 0.006, hy - 0.006, 0.011, 0.018, 12))
    if turn:
        # head turned to one side: cheek, jaw and the tip of the nose show past the hair
        f.part('face', skin[0], skin[1], [(turn * 0.02, hy - 0.05), (turn * 0.05, hy - 0.045),
                                          (turn * 0.064, hy - 0.016), (turn * 0.07, hy - 0.002),
                                          (turn * 0.06, hy + 0.012), (turn * 0.02, hy + 0.01)])
    if s.get('bald'):
        f.part('head', skin[0], skin[1], ell(turn * 0.004, hy, rx, ry, 26), snow=False)
        f.part('hair', hair[0], hair[1], ell(turn * 0.004, hy - 0.006, rx + 0.002, ry * 0.75, 26, math.pi * 1.0,
                                             math.pi * 2.0) + [(rx, hy - 0.006 + 0.012), (-rx, hy + 0.006)])
        f.dot(-rx * 0.4, hy + ry * 0.55, rel=1, minh=49, clip=('head',))
    else:
        f.part('hair', hair[0], hair[1], ell(turn * 0.004, hy, rx, ry, 26), snow=not hat)
        if s.get('long_hair'):
            f.part('hair', hair[0], hair[1], [(-rx, hy), (-rx - 0.008, hy - 0.06), (-rx + 0.004, sh + 0.0),
                                              (rx - 0.004, sh + 0.0), (rx + 0.008, hy - 0.06), (rx, hy)])
        for k in range(-2, 3):
            f.line([(k * 0.012, hy + 0.04 - abs(k) * 0.006), (k * 0.014, hy - 0.04)], rel=-1, minh=86,
                   clip=('hair',))
        f.dot(-rx * 0.45, hy + ry * 0.5, rel=1, minh=49, clip=('hair',))
        if s.get('bun'):
            f.part('bun', hair[0], hair[1] + 1, ell(0.0, hy - 0.01, 0.028, 0.025, 18))
            f.line([(-0.02, hy - 0.01), (0.02, hy - 0.004)], rel=-1, minh=65, clip=('bun',))
    # collar / scarf on top of the neck and lower head
    collar = s.get('collar', 'flat')
    if collar == 'up':
        f.part('collar', cr, ci, [(-0.054, sh + 0.012), (-0.052, sh + 0.07), (-0.02, sh + 0.08), (0.02, sh + 0.08),
                                  (0.052, sh + 0.07), (0.054, sh + 0.012), (0.0, sh + 0.02)], snow=True)
        f.line([(-0.05, sh + 0.04), (0.05, sh + 0.04)], rel=-1, minh=65, clip=('collar',))
    elif collar == 'flat':
        f.part('collar', cr, ci, [(-sw * 0.62, sh + 0.012), (-0.045, sh + 0.04), (0.045, sh + 0.04),
                                  (sw * 0.62, sh + 0.012), (sw * 0.42, sh - 0.028), (0.0, sh - 0.065),
                                  (-sw * 0.42, sh - 0.028)], snow=True)
    elif collar == 'fur':
        fr, fi = s.get('fur', ('stone', 2))
        pts = []
        for k in range(17):
            a = math.pi * k / 16
            rr = 1.0 + (0.12 if k % 2 else 0.0)
            pts.append((-math.cos(a) * sw * 0.8 * rr, sh - 0.005 + math.sin(a) * 0.05 * rr))
        pts += [(sw * 0.7, sh - 0.04), (sw * 0.3, sh - 0.07), (0.0, sh - 0.08), (-sw * 0.3, sh - 0.07),
                (-sw * 0.7, sh - 0.04)]
        f.part('fur', fr, fi, pts, snow=True)
        for k in range(9):
            f.dot(-sw * 0.6 + k * sw * 0.15, sh - 0.02 - 0.015 * (k % 2), rel=-1, minh=114, clip=('fur',))
            f.dot(-sw * 0.55 + k * sw * 0.14, sh + 0.02 - 0.012 * ((k + 1) % 2), rel=1, minh=198, clip=('fur',))
    elif collar == 'scarf':
        r2, i2 = s.get('scarf', ('ochre', 2))
        f.part('scarf', r2, i2, [(-0.056, sh + 0.008), (-0.052, sh + 0.06), (0.052, sh + 0.06), (0.056, sh + 0.008)],
               snow=True)
        f.part('scarf', r2, i2, [(0.0, sh + 0.02), (0.046, sh + 0.02), (0.052, sh - 0.17), (0.006, sh - 0.175)])
        f.line([(0.008, sh - 0.165), (0.05, sh - 0.16)], rel=1, minh=49, clip=('scarf',))
        for k in range(4):
            f.dot(0.01 + k * 0.012, sh - 0.178, rel=0, minh=86, clip=None, col=(r2, i2))
        f.line([(-0.05, sh + 0.035), (0.05, sh + 0.035)], rel=-1, minh=49, clip=('scarf',))
    if hat:
        _hat(f, hat[0], (hat[1], hat[2]), hy, s)
    # how much snow this person's hat and shoulders hold (brims catch it, knitted caps and hair little), its
    # brightness and pattern: every head of a packed crowd carries its own
    amt, sidx = SNOW_BY_HAT.get(hat[0] if hat else None, (0.2, 3))
    f.snow_amt = s.get('snow_amt', amt)
    f.snow_idx = s.get('snow_idx', sidx)
    f.snow_seed = int(H * 997 + sw * 7919 + (31 if fem else 0) + len(str(s.get('hat')))) % 251
    return f


# (share of upward edge pixels under snow, snow ramp index) per hat kind of a civilian
SNOW_BY_HAT = {'fedora': (0.55, 4), 'homburg': (0.55, 4), 'cap': (0.4, 3), 'cloche': (0.45, 3), 'scarf': (0.3, 3),
               'furhat': (0.5, 4), 'beret': (0.25, 3), 'knit': (0.35, 3), None: (0.2, 3)}


def child_flag():
    """A child from behind holding a limp little hand flag (plain cloth, no emblem)."""
    s = dict(H=0.6, sw=0.085, kid=True, coat=('steel', 3), hem=0.42, collar='flat', hat=('knit', 'ochre', 2),
             pompom=True, legs=('coal', 2), socks=('snow', 3), arms=('down', None), glove=('stone', 3))
    f = civ(s)
    # raise the right hand with the stick (drawn over the shoulder)
    H = 0.6
    sh = 0.76 * H
    f.part('arm', 'steel', 3, limb([(0.055, sh - 0.02), (0.1, sh - 0.07), (0.112, sh + 0.0)], [0.046, 0.042, 0.04]),
           lit=-0.6)
    f.part('hand', 'stone', 3, ell(0.112, sh + 0.012, 0.018, 0.022, 12))
    f.part('stick', 'wood', 3, limb([(0.114, sh - 0.03), (0.13, H + 0.16)], [0.012, 0.01]), sep=False,
           shade='flat')
    f.part('flag', 'ochre', 3, [(0.131, H + 0.165), (0.178, H + 0.16), (0.175, H + 0.11), (0.168, H + 0.07),
                                (0.152, H + 0.04), (0.14, H + 0.05), (0.134, H + 0.09)], snow=True)
    f.line([(0.15, H + 0.16), (0.152, H + 0.06)], rel=-1, minh=37, clip=('flag',))
    f.line([(0.165, H + 0.158), (0.166, H + 0.09)], rel=1, minh=65, clip=('flag',))
    return f


def child_plain():
    s = dict(H=0.54, sw=0.08, kid=True, coat=('stone', 3), hem=0.4, collar='flat', hat=('hood', 'stone', 3),
             legs=('violet', 2), socks=('snow', 2), arms=('hold', 'down'), glove=('ochre', 2), shoe=('coal', 2))
    return civ(s)


# a crowd of mixed age, class and coats; values kept mid-dark so the mass never reads as one black wall
CROWD = [
    dict(H=0.97, sw=0.13, coat=('coal', 4), hem=0.3, collar='up', hat=('fedora', 'violet', 3), hair=('coal', 2),
         arms='pockets', legs=('coal', 2), shift=0.01),
    dict(H=0.9, sw=0.112, fem=True, coat=('stone', 3), hem=0.33, belt=True, collar='flat',
         hat=('scarf', 'violet', 4), pattern=True, arms=('down', 'bag'), bag=('coal', 2), legs=('violet', 2),
         shoe=('coal', 2)),
    dict(H=0.95, sw=0.128, coat=('steel', 3), hem=0.32, collar='scarf', scarf=('ochre', 2), hat=('cap', 'steel', 2),
         hair=('stone', 1), arms='down', legs=('coal', 3)),
    dict(H=0.91, sw=0.11, fem=True, coat=('violet', 4), hem=0.36, collar='fur', fur=('stone', 2),
         hat=('cloche', 'coal', 3), hair=('stone', 2), bun=True, arms='down', legs=('violet', 2), glove=('coal', 3)),
    dict(H=0.88, sw=0.12, coat=('coal', 4), hem=0.26, hunch=0.035, collar='up', hat=('homburg', 'coal', 3),
         hair=('snow', 4), arms=('cane', 'down'), legs=('coal', 2)),
    dict(H=0.96, sw=0.135, coat=('ochre', 2), hem=0.5, collar='flat', hair=('coal', 1), arms='behind',
         legs=('steel', 2), glove=('skin', 3)),
    dict(H=0.92, sw=0.113, fem=True, coat=('snow', 3), hem=0.3, belt=True, collar='up', hat=('scarf', 'coal', 3),
         arms='crossed', legs=('violet', 2)),
    dict(H=0.98, sw=0.122, coat=('steel', 2), hem=0.46, collar='up', hair=('stone', 3), turn=1, arms='pockets',
         legs=('coal', 3)),
    dict(H=0.99, sw=0.145, coat=('stone', 2), hem=0.3, collar='fur', fur=('coal', 3), hat=('furhat', 'coal', 4),
         arms='down', legs=('coal', 2)),
    dict(H=0.93, sw=0.11, fem=True, coat=('coal', 4), hem=0.34, collar='flat', hat=('beret', 'ochre', 2),
         hair=('stone', 1), long_hair=True, turn=-1, arms='down', legs=('coal', 2), skirt=('violet', 3)),
    dict(H=1.0, sw=0.118, coat=('violet', 3), hem=0.28, collar='up', hat=('fedora', 'coal', 3), hair=('coal', 2),
         arms='behind', legs=('coal', 1)),
    dict(H=0.86, sw=0.112, fem=True, coat=('coal', 3), hem=0.24, hunch=0.04, collar='flat',
         hat=('scarf', 'snow', 3), arms=('down', 'bag'), bag=('stone', 2), legs=('coal', 1)),
    dict(H=0.95, sw=0.14, coat=('steel', 3), hem=0.48, quilted=True, collar='up', hat=('knit', 'coal', 3),
         arms='down', legs=('coal', 2), glove=('stone', 2)),
    dict(H=0.92, sw=0.11, fem=True, coat=('stone', 4), hem=0.34, belt=True, collar='scarf', scarf=('coal', 3),
         hair=('stone', 4), bun=True, arms='down', legs=('stone', 2)),
    dict(H=0.96, sw=0.125, coat=('snow', 2), hem=0.3, belt=True, collar='up', hat=('homburg', 'coal', 2),
         bowed=True, arms='down', legs=('coal', 2)),
    dict(H=0.84, sw=0.108, coat=('stone', 2), hem=0.5, collar='flat', hat=('cap', 'coal', 3), hair=('stone', 2),
         arms='pockets', legs=('steel', 2)),
    dict(H=0.9, sw=0.112, fem=True, coat=('ochre', 2), hem=0.32, collar='up', hat=('knit', 'snow', 3),
         arms='crossed', legs=('violet', 2)),
    dict(H=0.97, sw=0.13, coat=('coal', 3), hem=0.29, collar='up', hat=('cap', 'violet', 3), hair=('snow', 2),
         turn=1, arms=('down', 'hold'), legs=('coal', 2)),
    # more faces in the near rows of shot p5: a worker in a short padded jacket and fur hat, an old woman in a
    # coloured headscarf, a tall man in a belted dark coat with a beret, a young woman in a light coat
    dict(H=0.94, sw=0.138, coat=('violet', 3), hem=0.5, quilted=True, collar='up', hat=('furhat', 'stone', 2),
         arms='pockets', legs=('steel', 1), shoe=('coal', 1)),
    dict(H=0.85, sw=0.115, fem=True, coat=('violet', 2), hem=0.24, hunch=0.045, collar='flat',
         hat=('scarf', 'ochre', 2), arms=('bag', 'down'), bag=('coal', 3), legs=('coal', 2)),
    dict(H=1.0, sw=0.12, coat=('coal', 2), hem=0.27, belt=True, collar='up', hat=('beret', 'coal', 3),
         hair=('coal', 2), arms='crossed', legs=('coal', 1)),
    dict(H=0.91, sw=0.108, fem=True, coat=('steel', 4), hem=0.34, belt=True, collar='flat',
         hat=('knit', 'ochre', 3), pompom=True, hair=('stone', 3), long_hair=True, turn=-1, arms='pockets',
         legs=('violet', 2)),
]


# ------------------------------------------------------------------------------------------- troops
def _helmet_side(f, cx=0.0):
    pts = [(0.079, 0.897), (0.072, 0.93), (0.048, 0.965), (0.0, 0.982), (-0.045, 0.975), (-0.07, 0.952),
           (-0.078, 0.918), (-0.094, 0.865), (-0.072, 0.871), (-0.03, 0.882), (0.02, 0.889)]
    f.part('helmet', 'steel', 2, [(x + cx, y) for x, y in pts], snow=True)
    f.line([(0.079 + cx, 0.897), (0.02 + cx, 0.889), (-0.03 + cx, 0.882), (-0.072 + cx, 0.871)], rel=-1, minh=37,
           clip=('helmet',))
    f.dot(-0.028 + cx, 0.94, rel=1, minh=49, clip=('helmet',))
    f.fill([(-0.04 + cx, 0.965), (0.02 + cx, 0.977), (0.03 + cx, 0.968), (-0.03 + cx, 0.955)], rel=1, minh=29,
           clip=('helmet',))


def soldier_march(fr, n=8):
    """Marching soldier in profile facing +x (we see his right side).  Greatcoat with the skirt corners buttoned
    back for the march (knees and boot shafts come free, so the stride reads even behind the barrier rail), belt,
    pouches, rifle on the far (left) shoulder held at the butt: upper stock, band and barrel slant back over the
    shoulder clear of the helmet.  The near arm swings against the near leg.  8 frames = 2 steps."""
    f = Fig()
    p = fr / n
    L, lift = 0.2, 0.065
    hip = (0.0, 0.465 - 0.012 * math.cos(4 * math.pi * p))

    def leg(q):
        if q < 0.5:
            t = q / 0.5
            return (L * (1 - 2 * t), 0.0), 0.0
        t = (q - 0.5) / 0.5
        e = t * t * (3 - 2 * t)
        return (-L + 2 * L * e, lift * math.sin(math.pi * t) ** 1.3), 14.0 * math.sin(math.pi * t)
    knees = []
    for q, near in (((p + 0.5) % 1.0, False), (p, True)):
        (fx, fy), toe = leg(q)
        foot = (hip[0] + fx, fy + 0.04)
        knee = ik_knee(hip, foot, 0.228, 0.228, 1.0)
        knees.append(knee)
        lr = ('steel', 1) if not near else ('steel', 2)
        f.part('leg_n' if near else 'leg_f', lr[0], lr[1], limb([hip, knee, foot], [0.072, 0.064, 0.054]),
               sep=near, lit=0.0 if near else -1.0)
        # jackboot shaft from the ankle up to below the knee
        bt = (foot[0] + (knee[0] - foot[0]) * 0.74, foot[1] + (knee[1] - foot[1]) * 0.74)
        f.part('boot_n' if near else 'boot_f', 'leather', 3 if near else 2, seg(foot, bt, 0.064, 0.072),
               lit=0.0 if near else -1.0)
        a = math.radians(toe)
        ca, sa = math.cos(a), math.sin(a)
        fp = [(-0.032, -0.04), (-0.032, 0.0), (0.035, -0.004), (0.074, -0.022), (0.078, -0.04)]
        f.part('boot_n' if near else 'boot_f', 'leather', 3 if near else 2,
               [(foot[0] + x * ca - y * sa, foot[1] + x * sa + y * ca) for x, y in fp],
               lit=0.0 if near else -1.0)
        if near:
            f.line([(bt[0] - 0.024, bt[1]), (bt[0] + 0.03, bt[1])], rel=-1, minh=49, clip=('boot_n',))
            f.line([(knee[0] + 0.02, knee[1] + 0.01), (knee[0] + 0.03, knee[1] - 0.03)], rel=1, minh=65,
                   clip=('leg_n',))
            f.dot(foot[0] + 0.03, foot[1] - 0.012, rel=2, minh=65, clip=('boot_n',))
    # rifle on the far shoulder: the butt in the far hand in front of the belly, the rifle hidden by the body up
    # to the shoulder, then upper stock + band + barrel slanting back at ~54 deg behind the neck
    ux, uy = -0.595, 0.804
    bx, by = 0.152, 0.548

    def rp(t):
        return (bx + ux * t, by + uy * t)
    f.part('rifle', 'wood', 3, seg(rp(0.0), rp(0.27), 0.046, 0.036))
    f.part('rifle', 'wood', 3, seg(rp(0.27), rp(0.53), 0.034, 0.026), rim=1)
    f.part('barrel', 'metal', 4, seg(rp(0.52), rp(0.625), 0.017, 0.015), shade='flat', rim=1)
    f.dot(*rp(0.625), col=('metal', 6), minh=49, clip=('barrel',))
    f.line([rp(0.47), rp(0.47)], col=('metal', 5), rel=0, minh=37, clip=('rifle',))           # upper band
    f.line([rp(0.36), rp(0.36)], col=('metal', 4), rel=0, minh=86, clip=('rifle',))           # lower band
    # sling sagging under the shouldered rifle
    f.part('sling', 'leather', 2, limb([rp(0.31), (rp(0.42)[0] + 0.018, rp(0.42)[1] - 0.026), rp(0.49)],
                                       [0.012, 0.012, 0.012]), sep=False, shade='flat', minh=37)
    f.part('hand_f', 'leather', 2, ell(0.128, 0.578, 0.027, 0.031, 14))
    # greatcoat: torso + skirt to just below the knee, front and back corners buttoned back, swinging with the
    # stride
    front = max(0.112, max(k[0] for k in knees) + 0.03)
    back = min(-0.108, min(k[0] for k in knees) - 0.05)
    hem = 0.315
    skirt = [(-0.1, 0.575), (-0.112, 0.45), (back, hem + 0.02), (back * 0.45, hem + 0.004), (0.0, hem),
             (front * 0.55, hem + 0.004), (front, hem + 0.018), (min(front, 0.132), 0.45), (0.116, 0.575)]
    f.part('coat', 'steel', 3, skirt, snow=False)
    # turned-back corners show the darker lining as a triangle at the front and back of the skirt
    f.part('lining', 'steel', 2, [(front, hem + 0.018), (front * 0.55, hem + 0.004), (front - 0.012, hem + 0.07)],
           minh=37, sep=False)
    f.part('lining', 'steel', 2, [(back, hem + 0.02), (back * 0.45, hem + 0.004), (back + 0.016, hem + 0.075)],
           minh=49, sep=False)
    torso = [(-0.072, 0.818), (-0.096, 0.785), (-0.106, 0.69), (-0.1, 0.565), (0.118, 0.565), (0.122, 0.66),
             (0.104, 0.76), (0.062, 0.812)]
    f.part('coat', 'steel', 3, torso, snow=True)
    f.line([(0.112, 0.565), (front - 0.006, hem + 0.024)], rel=-1, minh=28, clip=('coat',))
    f.line([(0.02, 0.55), (back * 0.2 + 0.01, hem + 0.02)], rel=-1, minh=49, clip=('coat',))
    f.line([(-0.06, 0.55), (back + 0.03, hem + 0.035)], rel=-1, minh=65, clip=('coat',))
    f.line([(-0.098, 0.7), (-0.095, 0.585)], rel=-1, minh=65, clip=('coat',))
    f.dot(front - 0.014, hem + 0.06, col=('metal', 5), minh=65, clip=('coat', 'lining'))
    for k, by_ in enumerate((0.735, 0.68, 0.625)):
        f.dot(0.105 + k * 0.004, by_, col=('metal', 5), minh=49, clip=('coat',))
    # belt, buckle, cartridge pouch, bayonet frog at the back hip
    f.part('belt', 'leather', 2, [(-0.104, 0.553), (0.12, 0.553), (0.122, 0.583), (-0.102, 0.583)], minh=11)
    f.fill([(0.104, 0.555), (0.122, 0.555), (0.122, 0.581), (0.104, 0.581)], col=('metal', 5), minh=21,
           clip=('belt',))
    f.part('pouch', 'leather', 3, [(0.05, 0.585), (0.1, 0.585), (0.1, 0.535), (0.05, 0.535)], minh=21)
    f.line([(0.05, 0.57), (0.1, 0.57)], rel=-1, minh=49, clip=('pouch',))
    f.part('pouch', 'leather', 2, [(-0.1, 0.56), (-0.082, 0.56), (-0.085, 0.43), (-0.1, 0.44)], minh=21)
    # collar, face in shadow under the helmet, helmet
    f.part('collar', 'steel', 2, [(-0.058, 0.802), (-0.064, 0.848), (0.0, 0.852), (0.048, 0.836), (0.068, 0.806),
                                  (0.02, 0.796)], snow=True)
    f.part('face', 'skin', 1, [(0.0, 0.84), (0.05, 0.836), (0.068, 0.858), (0.071, 0.874), (0.083, 0.886),
                               (0.074, 0.9), (0.02, 0.9), (-0.04, 0.89), (-0.045, 0.85)], shade='flat')
    f.line([(0.068, 0.858), (0.071, 0.874)], rel=1, minh=49, clip=('face',))
    f.line([(0.0, 0.888), (0.05, 0.845)], col=('leather', 1), rel=0, minh=37, clip=('face',))
    _helmet_side(f)
    f.line([(-0.04, 0.8), (0.04, 0.796)], rel=1, minh=49, clip=('coat',))     # shoulder strap
    # near arm swinging opposite to the near leg (forward to the belt buckle, back past the hip)
    sw_ = -math.cos(2 * math.pi * p)          # +1 forward
    sh_ = (0.0, 0.77)
    a1 = math.radians(-90 + 32 * sw_)
    el = (sh_[0] + 0.17 * math.cos(a1), sh_[1] + 0.17 * math.sin(a1))
    a2 = a1 + math.radians(12 + 16 * max(sw_, 0))
    wr = (el[0] + 0.15 * math.cos(a2), el[1] + 0.15 * math.sin(a2))
    f.part('arm', 'steel', 3, limb([sh_, el, wr], [0.068, 0.06, 0.052]))
    f.line([(wr[0] - 0.024, wr[1] + 0.03), (wr[0] + 0.022, wr[1] + 0.028)], rel=-1, minh=49, clip=('arm',))
    f.line([(el[0] - 0.012, el[1] + 0.02), (el[0] + 0.012, el[1] - 0.004)], rel=-1, minh=65, clip=('arm',))
    hd = (wr[0] + 0.012 * math.cos(a2), wr[1] + 0.03 * math.sin(a2))
    f.part('hand', 'leather', 3, ell(hd[0], hd[1], 0.024, 0.03, 14))
    # breath in the cold (one exhalation per cycle)
    k = fr % n
    if k in (2, 3, 4):
        r = [0.012, 0.02, 0.026][k - 2]
        cx = 0.1 + 0.025 * (k - 2)
        cy = 0.875 + 0.008 * (k - 2)
        f.overlay('snow', 3 if k < 4 else 2, ell(cx, cy, r * 1.3, r, 14), minh=21)
    return f


def soldier_front(kind='stand'):
    """Front view at attention: 'stand' (rifle at order), 'guard' (gorget, white belt, rifle at order),
    'guard_b' (rifle slung, hand on the sling), 'leader' (block leader, no rifle, holster)."""
    f = Fig()
    guard = kind.startswith('guard')
    # legs + jackboots, toes slightly out
    for side in (-1, 1):
        f.part('leg', 'steel', 2, seg((side * 0.04, 0.42), (side * 0.046, 0.2), 0.07, 0.066), sep=False,
               lit=0.0 if side < 0 else -0.6)
        f.part('boot', 'leather', 3, [(side * 0.012, 0.22), (side * 0.08, 0.22), (side * 0.078, 0.04),
                                      (side * 0.09, 0.0), (side * 0.01, 0.0), (side * 0.014, 0.04)],
               lit=0.0 if side < 0 else -0.6)
        f.line([(side * 0.02, 0.2), (side * 0.075, 0.2)], rel=-1, minh=49, clip=('boot',))
        f.dot(side * 0.06 - 0.01, 0.02, rel=2, minh=49, clip=('boot',))
    rifle_x = -0.185
    def order_rifle():
        # rifle at order: butt beside the right boot, wooden fore-end up past the gloved hand, barrel and (guards)
        # a fixed bayonet catching the floodlight above it -- reads as a rifle, not a stick, against the night.
        # Drawn over the hanging arm (the rifle stands in front of the sleeve), the hand then grips it; a dark edge
        # keeps barrel and blade apart from the lit sleeve (same greys).
        f.part('rifle_edge', 'coal', 1, seg((rifle_x, 0.44), (rifle_x, 0.664), 0.04, 0.034), shade='flat', sep=False)
        if guard:
            f.part('rifle_edge', 'coal', 1, seg((rifle_x, 0.64), (rifle_x, 0.79), 0.028, 0.016), shade='flat',
                   sep=False)
        f.part('rifle', 'wood', 3, [(rifle_x - 0.026, 0.0), (rifle_x + 0.022, 0.0), (rifle_x + 0.016, 0.2),
                                    (rifle_x + 0.011, 0.205), (rifle_x + 0.011, 0.585), (rifle_x - 0.011, 0.585),
                                    (rifle_x - 0.012, 0.21), (rifle_x - 0.018, 0.2)], rim=1)
        f.part('barrel', 'metal', 2, seg((rifle_x, 0.575), (rifle_x, 0.655), 0.018, 0.016), shade='flat', rim=2)
        f.line([(rifle_x - 0.005, 0.58), (rifle_x - 0.005, 0.652)], col=('metal', 5), rel=0, minh=49,
               clip=('barrel',))
        f.line([(rifle_x - 0.011, 0.53), (rifle_x + 0.011, 0.53)], col=('metal', 5), rel=0, minh=37,
               clip=('rifle',))
        f.line([(rifle_x - 0.011, 0.38), (rifle_x + 0.011, 0.38)], col=('metal', 4), rel=0, minh=86,
               clip=('rifle',))
        if guard:
            f.part('bayonet', 'metal', 5, [(rifle_x - 0.009, 0.652), (rifle_x + 0.009, 0.652),
                                           (rifle_x + 0.006, 0.75), (rifle_x, 0.775), (rifle_x - 0.006, 0.75)],
                   shade='flat', rim=1)
        else:
            f.dot(rifle_x, 0.657, col=('metal', 6), minh=37, clip=('barrel',))
        f.line([(rifle_x + 0.016, 0.06), (rifle_x + 0.02, 0.3), (rifle_x + 0.013, 0.52)], col=('leather', 2), rel=0,
               minh=37, clip=('rifle',))
        f.line([(rifle_x - 0.02, 0.18), (rifle_x + 0.016, 0.18)], rel=-1, minh=65, clip=('rifle',))
    if kind == 'guard_b':
        f.part('barrel', 'metal', 3, seg((-0.15, 0.86), (-0.162, 1.0), 0.014, 0.012), shade='flat')
        f.part('rifle', 'wood', 2, seg((-0.135, 0.36), (-0.15, 0.86), 0.034, 0.024))
    # greatcoat skirt + torso
    f.part('coat', 'steel', 3, [(-0.122, 0.575), (0.122, 0.575), (0.142, 0.25), (0.135, 0.235), (-0.135, 0.235),
                                (-0.142, 0.25)])
    f.part('coat', 'steel', 3, [(-0.07, 0.808), (0.07, 0.808), (0.128, 0.79), (0.13, 0.7), (0.118, 0.575),
                                (-0.118, 0.575), (-0.13, 0.7), (-0.128, 0.79)], snow=True)
    f.line([(0.006, 0.575), (0.012, 0.236)], rel=-1, minh=21, clip=('coat',))
    f.line([(-0.06, 0.55), (-0.09, 0.25)], rel=-1, minh=65, clip=('coat',))
    f.line([(0.07, 0.55), (0.1, 0.25)], rel=-1, minh=65, clip=('coat',))
    f.line([(-0.13, 0.235), (0.135, 0.235)], rel=-1, minh=37, clip=('coat',))
    for side in (-1, 1):
        for k, by in enumerate((0.745, 0.69, 0.635)):
            f.dot(side * (0.048 - k * 0.006), by, col=('metal', 5), minh=37, clip=('coat',))
        f.dot(side * 0.03, 0.49, col=('metal', 4), minh=65, clip=('coat',))
        f.line([(side * 0.075, 0.802), (side * 0.12, 0.79)], rel=1, minh=49, clip=('coat',))
    # arms
    for side in (-1, 1):
        lit = 0.0 if side < 0 else -0.6
        if kind in ('stand', 'guard') and side < 0:
            pts = [(-0.118, 0.775), (-0.158, 0.64), (-0.176, 0.52)]
            hand = (rifle_x + 0.004, 0.5)
        elif kind == 'guard_b' and side < 0:
            pts = [(-0.118, 0.775), (-0.152, 0.64), (-0.105, 0.7)]
            hand = (-0.098, 0.712)
        else:
            pts = [(side * 0.118, 0.775), (side * 0.145, 0.63), (side * 0.14, 0.49)]
            hand = (side * 0.138, 0.46)
        f.part('arm', 'steel', 3, limb(pts, [0.066, 0.06, 0.054]), lit=lit)
        f.line([(pts[2][0] - 0.026, pts[2][1] + 0.028), (pts[2][0] + 0.026, pts[2][1] + 0.028)], rel=-1, minh=49,
               clip=('arm',))
        f.part('hand', 'snow' if guard else 'leather', 4 if guard else 3, ell(hand[0], hand[1], 0.024, 0.032, 14))
    if kind in ('stand', 'guard'):
        order_rifle()
        f.part('hand', 'snow' if guard else 'leather', 4 if guard else 3, ell(rifle_x + 0.004, 0.5, 0.024, 0.032, 14))
        f.line([(rifle_x - 0.014, 0.508), (rifle_x + 0.018, 0.508)], rel=-1, minh=86, clip=('hand',))
    if kind == 'guard_b':
        f.line([(-0.098, 0.72), (-0.12, 0.79), (-0.13, 0.62), (-0.138, 0.4)], col=('leather', 3), rel=0, minh=21,
               clip=None)
    # belt (white for the guards), buckle, pouches / holster
    bc = ('snow', 4) if guard else ('leather', 2)
    f.part('belt', bc[0], bc[1], [(-0.12, 0.553), (0.12, 0.553), (0.12, 0.585), (-0.12, 0.585)], minh=9)
    f.fill([(-0.016, 0.551), (0.016, 0.551), (0.016, 0.587), (-0.016, 0.587)], col=('metal', 5), minh=21,
           clip=('belt',))
    f.dot(0.0, 0.569, col=('metal', 3), minh=49, clip=('belt',))
    if kind == 'leader':
        f.part('holster', 'leather', 3, [(0.07, 0.585), (0.112, 0.585), (0.11, 0.5), (0.074, 0.505)], minh=16)
        f.line([(0.072, 0.56), (0.11, 0.56)], rel=-1, minh=49, clip=('holster',))
    elif not guard:
        for side in (-1, 1):
            f.part('pouch', 'leather', 3, [(side * 0.028, 0.585), (side * 0.07, 0.585), (side * 0.07, 0.53),
                                           (side * 0.028, 0.53)], minh=16)
            f.line([(side * 0.028, 0.568), (side * 0.07, 0.568)], rel=-1, minh=49, clip=('pouch',))
            f.line([(side * 0.049, 0.585), (side * 0.049, 0.532)], rel=-1, minh=86, clip=('pouch',))
    # collar with the lapels, neck, face in shadow, chin strap
    f.part('neck', 'skin', 1, [(-0.03, 0.8), (0.03, 0.8), (0.03, 0.85), (-0.03, 0.85)], shade='flat')
    f.part('collar', 'steel', 2, [(-0.078, 0.8), (-0.03, 0.735), (0.0, 0.765), (0.03, 0.735), (0.078, 0.8),
                                  (0.055, 0.832), (0.025, 0.812), (-0.025, 0.812), (-0.055, 0.832)], snow=True)
    if kind == 'leader':
        f.line([(-0.07, 0.8), (-0.03, 0.745)], rel=2, minh=37, clip=('collar',))
        f.line([(0.07, 0.8), (0.03, 0.745)], rel=2, minh=37, clip=('collar',))
    f.part('face', 'skin', 2, ell(0.0, 0.866, 0.041, 0.04, 22), shade='flat')
    f.part('face', 'skin', 1, [(-0.044, 0.872), (0.044, 0.872), (0.046, 0.904), (-0.046, 0.904)], shade='flat')
    f.line([(-0.012, 0.852), (0.012, 0.852)], rel=-1, minh=65, clip=('face',))
    f.dot(-0.022, 0.862, rel=1, minh=86, clip=('face',))
    for side in (-1, 1):
        f.line([(side * 0.04, 0.89), (side * 0.016, 0.834)], col=('leather', 1), rel=0, minh=37, clip=('face',))
    # helmet: dome + flared skirt, visor edge, highlight
    f.part('helmet', 'steel', 2, ell(0.0, 0.928, 0.072, 0.056, 28, 0.0, math.pi) + [(-0.072, 0.928)], snow=True)
    f.part('helmet', 'steel', 2, [(-0.086, 0.874), (-0.073, 0.93), (0.073, 0.93), (0.086, 0.874), (0.058, 0.887),
                                  (0.0, 0.894), (-0.058, 0.887)], snow=False)
    f.line([(-0.086, 0.874), (-0.058, 0.887), (0.0, 0.894), (0.058, 0.887), (0.086, 0.874)], rel=-1, minh=29,
           clip=('helmet',))
    f.fill([(-0.05, 0.95), (-0.02, 0.972), (-0.006, 0.968), (-0.036, 0.944)], rel=2, minh=21, clip=('helmet',))
    f.dot(0.05, 0.93, rel=1, minh=65, clip=('helmet',))
    if guard:
        # gorget on a chain: a plain crescent plate with two studs (no emblem)
        arc_o = ell(0.0, 0.775, 0.058, 0.052, 16, math.pi * 1.08, math.pi * 1.92)
        arc_i = ell(0.0, 0.79, 0.042, 0.04, 16, math.pi * 1.92, math.pi * 1.08)
        f.part('gorget', 'snow', 4, arc_o + arc_i)
        f.dot(-0.03, 0.748, col=('metal', 2), minh=37, clip=('gorget',))
        f.dot(0.03, 0.748, col=('metal', 2), minh=37, clip=('gorget',))
        f.line([(-0.04, 0.742), (0.0, 0.73), (0.04, 0.742)], rel=1, minh=65, clip=('gorget',))
        for side in (-1, 1):
            f.line([(side * 0.05, 0.765), (side * 0.045, 0.81)], col=('metal', 5), rel=0, minh=37, clip=('coat',
                                                                                                      'collar'))
    return f


def official(v):
    """Grey officials on the tribune, front view, faceless under hat / cap."""
    f = Fig()
    if v == 2:      # uniform: tunic, breeches, riding boots
        for side in (-1, 1):
            f.part('boot', 'leather', 3, [(side * 0.01, 0.3), (side * 0.075, 0.3), (side * 0.072, 0.04),
                                          (side * 0.085, 0.0), (side * 0.008, 0.0), (side * 0.012, 0.04)],
                   lit=0.0 if side < 0 else -0.6)
            f.part('breeches', 'steel', 2, [(side * 0.008, 0.5), (side * 0.11, 0.5), (side * 0.13, 0.4),
                                            (side * 0.075, 0.29), (side * 0.012, 0.29)],
                   lit=0.0 if side < 0 else -0.6)
        f.part('coat', 'steel', 3, [(-0.07, 0.808), (0.07, 0.808), (0.125, 0.79), (0.128, 0.6), (0.13, 0.47),
                                    (-0.13, 0.47), (-0.128, 0.6), (-0.125, 0.79)], snow=True)
        f.line([(0.0, 0.79), (0.0, 0.48)], rel=-1, minh=21, clip=('coat',))
        cap = ('steel', 2)
    else:
        coat = ('leather', 4) if v == 0 else ('snow', 3)
        for side in (-1, 1):
            f.part('leg', 'coal', 2, seg((side * 0.04, 0.3), (side * 0.045, 0.04), 0.07, 0.064), sep=False)
            f.part('shoe', 'coal', 1, [(side * 0.008, 0.045), (side * 0.08, 0.045), (side * 0.085, 0.0),
                                       (side * 0.005, 0.0)])
        f.part('coat', coat[0], coat[1], [(-0.07, 0.808), (0.07, 0.808), (0.128, 0.79), (0.132, 0.62),
                                          (0.152, 0.2), (-0.152, 0.2), (-0.132, 0.62), (-0.128, 0.79)], snow=True)
        f.line([(0.008, 0.75), (0.016, 0.2)], rel=-1, minh=21, clip=('coat',))
        f.line([(-0.06, 0.5), (-0.1, 0.21)], rel=-1, minh=49, clip=('coat',))
        if v == 0:
            # leather sheen: hard light streaks down the lit side
            f.line([(-0.1, 0.76), (-0.112, 0.62), (-0.13, 0.25)], rel=2, minh=21, clip=('coat',))
            f.line([(0.05, 0.7), (0.07, 0.3)], rel=1, minh=49, clip=('coat',))
            for k, by in enumerate((0.73, 0.65, 0.57, 0.49)):
                f.dot(0.03, by, col=('metal', 4), minh=37, clip=('coat',))
        cap = ('coal', 3) if v == 0 else ('coal', 2)
    for side in (-1, 1):
        lit = 0.0 if side < 0 else -0.6
        ar = ('leather', 4) if v == 0 else (('snow', 3) if v == 1 else ('steel', 3))
        if v == 1:      # hands behind the back
            pts = [(side * 0.118, 0.775), (side * 0.148, 0.64), (side * 0.13, 0.52)]
            hand = None
        else:           # hands clasped in front at the belt
            pts = [(side * 0.118, 0.775), (side * 0.15, 0.63), (side * 0.04, 0.52)]
            hand = True
        f.part('arm', ar[0], ar[1], limb(pts, [0.064, 0.058, 0.052]), lit=lit)
    if v != 1:
        f.part('hand', 'coal', 2, ell(0.0, 0.51, 0.045, 0.032, 16))
        f.line([(0.0, 0.535), (0.0, 0.49)], rel=-1, minh=37, clip=('hand',))
    f.part('belt', 'leather', 2, [(-0.125, 0.56), (0.125, 0.56), (0.125, 0.588), (-0.125, 0.588)], minh=9)
    if v != 1:
        f.line([(0.1, 0.79), (-0.11, 0.57)], col=('leather', 2), rel=0, minh=21, clip=('coat',))
        f.fill([(-0.014, 0.558), (0.014, 0.558), (0.014, 0.59), (-0.014, 0.59)], col=('metal', 4), minh=29,
               clip=('belt',))
    f.part('neck', 'skin', 1, [(-0.03, 0.8), (0.03, 0.8), (0.03, 0.85), (-0.03, 0.85)], shade='flat')
    if v == 1:      # dark fur collar
        pts = []
        for k in range(13):
            a = math.pi * k / 12
            pts.append((-math.cos(a) * 0.105, 0.795 - math.sin(a) * 0.05 * (1.0 + 0.15 * (k % 2))))
        f.part('collar', 'coal', 3, [(-0.11, 0.83)] + pts + [(0.11, 0.83)], snow=True)
    else:
        f.part('collar', cap[0], cap[1] + 1, [(-0.075, 0.8), (-0.03, 0.74), (0.0, 0.77), (0.03, 0.74), (0.075, 0.8),
                                              (0.05, 0.83), (-0.05, 0.83)], snow=True)
    f.part('face', 'skin', 2, ell(0.0, 0.868, 0.04, 0.04, 22), shade='flat')
    f.part('face', 'skin', 1, [(-0.043, 0.875), (0.043, 0.875), (0.045, 0.905), (-0.045, 0.905)], shade='flat')
    f.line([(-0.012, 0.852), (0.012, 0.852)], rel=-1, minh=65, clip=('face',))
    if v == 1:      # homburg
        f.part('hat', 'coal', 2, [(-0.085, 0.9), (0.085, 0.9), (0.075, 0.915), (-0.075, 0.915)], snow=True)
        f.part('hat', 'coal', 2, [(-0.052, 0.912), (-0.05, 0.965), (-0.035, 0.978), (0.035, 0.978), (0.05, 0.965),
                                  (0.052, 0.912)], snow=True)
        f.part('hatband', 'coal', 0, [(-0.052, 0.912), (0.052, 0.912), (0.051, 0.928), (-0.051, 0.928)], minh=16)
    else:           # peaked cap with a high front
        f.part('hat', cap[0], cap[1], [(-0.088, 0.95), (-0.06, 0.98), (0.0, 0.995), (0.06, 0.98), (0.088, 0.95),
                                       (0.05, 0.93), (-0.05, 0.93)], snow=True)
        f.part('hatband', 'coal', 1, [(-0.05, 0.905), (0.05, 0.905), (0.05, 0.935), (-0.05, 0.935)], minh=9)
        f.part('visor', 'coal', 0, [(-0.052, 0.9), (0.052, 0.9), (0.04, 0.885), (-0.04, 0.885)], shade='flat')
        f.dot(0.0, 0.945, col=('snow', 3), minh=37, clip=('hat',))
    return f


def puff(k):
    f = Fig(outline=False, puff=True)
    r = [0.16, 0.24, 0.3][k]
    f.part('p', 'snow', 3, ell(0.0, r * 0.9, r, r * 0.85, 24), shade='flat', sep=False)
    f.part('p', 'snow', 4, ell(-r * 0.3, r * 1.15, r * 0.65, r * 0.55, 20), shade='flat', sep=False)
    f.part('p', 'snow', 2, ell(r * 0.35, r * 0.5, r * 0.55, r * 0.4, 20), shade='flat', sep=False)
    return f


# ------------------------------------------------------------------------------------------- atlas layout
# Strip heights.  The large strips (drawn 1 texel = 1 px, never scaled up) carry only the slots that come that
# close to a camera: crowd backs, children and guards (p5 stands inside the crowd, p2 passes a guard at 12 m).
LODS = [2, 3, 4, 5, 7, 9, 12, 16, 21, 28, 37, 49, 65, 86, 114, 150, 198, 262, 346]


def slots():
    """[(kind, fig)] in atlas order; the order decides which large strips a slot lives in."""
    out = [('crowd', civ(s)) for s in CROWD]
    out += [('child_flag', child_flag()), ('child', child_plain())]
    out += [('guard', soldier_front('guard')), ('guard', soldier_front('guard_b'))]
    big_n = len(out)                       # up to the 346 px strip
    out += [('stand', soldier_front('stand')), ('leader', soldier_front('leader'))]
    out += [('march', soldier_march(f)) for f in range(8)]
    mid_n = len(out)                       # up to the 114 px strip
    out += [('official', official(v)) for v in range(3)]
    out += [('puff', puff(k)) for k in range(3)]
    return out, big_n, mid_n


def strip_slot_count(h, n_all, big_n, mid_n):
    if h >= 150:
        return big_n
    if h >= 86:
        return mid_n
    return n_all
