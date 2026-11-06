"""env_c4p2_cine_hands -- hands and sleeves of the Chapter-4-part-2 close shots (owner: cine stream, round 10).

The book's close shots (LS_C4P2_Book b1 / b2 / b3) and Ekdahl's window (LS_C4P2_Express x1) need hands at 3-4 px
per centimetre.  They are drawn with the game's own sprite shader (chargen_core: material ramps with six
hue-shifted tones, cel thresholds, the selective outline, the key-side lit edge, inner lines where a part lies over
another, contact shadows, the cloth texture patterns) at full resolution, so they read as crisp pixel art like the
in-game figures -- never as a smooth render:
  * fingers are single parts (three tapered capsules each) with explicit creases, knuckles and nails; the palm a
    pillow polygon with tendons; gloves carry their stitched points, seams and a press stud
  * sleeves are polygons whose height field carries real folds (stacked at the cuff, spiralling up the forearm),
    the wool / tweed / quilt patterns and seams; cuffs are their own parts (shirt cuff, knitted cuff, glove cuff)
  * a hand casts one flat translucent shadow on what it lies on (offset by the lamp and the lift)
Geometry is in centimetres in the hand's own frame (x across, + toward the little finger of a right hand seen from
the back; y along the hand, + toward the fingertips) and placed in canvas pixels by HandPose.  Deterministic.
"""
from __future__ import annotations

import dataclasses
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_core as CC  # noqa: E402  (Frame, capsule, Material, Light, shade, make_ramp; read-only)

ALL8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


# ================================================================================================= canvas
def ramp(*hexes):
    return CC.ramp_from_hex(list(hexes))


class Canvas:
    """A chargen_core Frame of any size with named materials and a few drawing helpers (canvas pixels)."""

    def __init__(self, w, h, scene='berlin'):
        self.w, self.h, self.scene = int(w), int(h), scene
        self.fr = CC.Frame(self.w, self.h)
        self.mats: list = []
        self.ids: dict = {}

    # ------------------------------------------------------------------ materials
    def mat(self, name, base, **kw):
        """Register a material: base = hex (6-tone ramp around it, the scene's tint) or a list of 6 hexes."""
        if name in self.ids:
            return self.ids[name]
        r = CC.make_ramp(base, self.scene) if isinstance(base, str) else ramp(*base)
        self.mats.append(CC.Material(name, r, **kw))
        self.ids[name] = len(self.mats) - 1
        return self.ids[name]

    # ------------------------------------------------------------------ parts
    def put(self, mask, x0, y0, mat, nrm=None, **kw):
        return self.fr.put(mask, int(x0), int(y0), self.ids[mat] if isinstance(mat, str) else mat, nrm, **kw)

    def caps(self, segs, mat, **kw):
        """One part from several tapered capsules [(a, b, ra, rb)]: union mask, the most frontal normal."""
        parts = [CC.capsule(a, b, ra, rb, nz_min=0.2) for (a, b, ra, rb) in segs]
        x0 = min(p[1] for p in parts)
        y0 = min(p[2] for p in parts)
        x1 = max(p[1] + p[0].shape[1] for p in parts)
        y1 = max(p[2] + p[0].shape[0] for p in parts)
        m = np.zeros((y1 - y0, x1 - x0), bool)
        n = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
        for (pm, px, py, pn) in parts:
            sl = (slice(py - y0, py - y0 + pm.shape[0]), slice(px - x0, px - x0 + pm.shape[1]))
            take = pm & (~m[sl] | (pn[..., 2] > n[sl][..., 2]))
            n[sl][take] = pn[take]
            m[sl] |= pm
        return self.put(m, x0, y0, mat, n, **kw), (m, x0, y0)

    def poly(self, pts, mat, R=3.0, cyl=0.6, relief=None, strength=1.0, **kw):
        """Pillow / cylinder polygon; relief(X, Y) adds height (folds).  Fast distance by erosion."""
        m, x0, y0 = CC.poly_mask(pts)
        if not m.any():
            return -1, (m, x0, y0)
        d = _dist(m, int(math.ceil(R)) + 1)
        q = np.clip(d / max(R, 1e-3), 0, 1)
        pillow = R * np.sqrt(np.clip(1 - (1 - q) ** 2, 0, 1))
        cylh = np.zeros_like(pillow)
        if cyl > 0:
            for r in range(m.shape[0]):
                xs = np.nonzero(m[r])[0]
                if len(xs) == 0:
                    continue
                a, b = xs.min(), xs.max() + 1
                half = max(1.0, (b - a) / 2.0)
                u = (np.arange(a, b) + 0.5 - (a + b) / 2.0) / half
                cylh[r, a:b] = half * np.sqrt(np.clip(1 - u ** 2, 0, 1))
        hgt = cyl * cylh + (1 - cyl) * pillow
        if relief is not None:
            yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]].astype(np.float32)
            hgt = hgt + relief(xx + x0 + 0.5, yy + y0 + 0.5)
        n = CC.height_normals(np.where(m, hgt, 0), m, strength)
        return self.put(m, x0, y0, mat, n, **kw), (m, x0, y0)

    def ell(self, cx, cy, rx, ry, mat, **kw):
        m, x0, y0, n = CC.ellipse(cx, cy, rx, ry, nz_min=0.3)
        return self.put(m, x0, y0, mat, n, **kw), (m, x0, y0)

    # ------------------------------------------------------------------ marks on what is painted
    def _full(self, pm):
        m, x0, y0 = pm
        out = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + m.shape[1]), min(self.h, y0 + m.shape[0])
        if X1 > X0 and Y1 > Y0:
            out[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        return out

    def line_mask(self, pts, r=0.5):
        out = np.zeros((self.h, self.w), bool)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32) + 0.5
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            x0, x1 = int(max(0, min(ax, bx) - r - 2)), int(min(self.w, max(ax, bx) + r + 3))
            y0, y1 = int(max(0, min(ay, by) - r - 2)), int(min(self.h, max(ay, by) + r + 3))
            if x1 <= x0 or y1 <= y0:
                continue
            X, Y = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / max(L2, 1e-6), 0, 1)
            d = np.hypot(X - ax - t * dx, Y - ay - t * dy)
            out[y0:y1, x0:x1] |= d <= r
        return out

    def bias(self, mask, k, only=None):
        """Shift the tone of painted pixels under mask by k (relative creases / highlights)."""
        m = mask & (self.fr.mat >= 0)
        if only is not None:
            m &= np.isin(self.fr.mat, [self.ids[o] for o in only])
        self.fr.bias[m] += k
        return m

    def tone(self, mask, t, mat=None, only=None):
        """Fix the tone (and optionally the material) of painted pixels under mask (nails, studs, stitches)."""
        m = mask & (self.fr.mat >= 0)
        if only is not None:
            m &= np.isin(self.fr.mat, [self.ids[o] for o in only])
        if mat is not None:
            self.fr.mat[m] = self.ids[mat]
        self.fr.tone[m] = float(t)
        self.fr.fixed[m] = True
        self.fr.bias[m] = 0.0
        return m

    # ------------------------------------------------------------------ resolve
    def render(self, key=(-0.6, 0.62, 0.5), ambient=0.30, thresholds=(0.34, 0.54, 0.74, 0.92), shadow=None,
               shadow_col=(18, 10, 8, 92)):
        """chargen_core.shade with inner lines on every side; shadow=(dx, dy) adds one flat cast shadow."""
        k = np.asarray(key, float)
        k /= np.linalg.norm(k)
        sx = 1 if k[0] >= 0 else -1
        light = CC.Light(key=tuple(k), rim=(-sx * 0.8, 0.42, -0.3), ambient=ambient, thresholds=thresholds,
                         lit_dirs=((sx, 0), (sx, -1), (0, -1)), shadow_dirs=((0, -1), (sx, -1), (sx, 0)),
                         rim_dirs=((-sx, 0), (-sx, -1), (0, -1)), inline_dirs=ALL8)
        rgba, _nm, _t = CC.shade(self.fr, self.mats, light, rim_color=None, rim_strength=0.0, lit_boost=1.0)
        if shadow is None:
            return rgba
        a = rgba[..., 3] > 0
        dx, dy = int(round(shadow[0])), int(round(shadow[1]))
        sh = np.zeros_like(a)
        H, W = a.shape
        ys, yd = slice(max(0, dy), min(H, H + dy)), slice(max(0, -dy), min(H, H - dy))
        xs, xd = slice(max(0, dx), min(W, W + dx)), slice(max(0, -dx), min(W, W - dx))
        sh[ys, xs] = a[yd, xd]
        out = rgba.copy()
        put = sh & ~a
        out[put] = np.asarray(shadow_col, np.uint8)
        return out


def _dist(m, rmax):
    """Chessboard-ish distance inside a mask up to rmax (iterated 4/8 erosion), > rmax clipped."""
    d = np.zeros(m.shape, np.float32)
    cur = m.copy()
    for i in range(rmax):
        p = np.pad(cur, 1)
        er = cur & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        if i % 2 == 1:
            er &= p[:-2, :-2] & p[2:, 2:] & p[:-2, 2:] & p[2:, :-2]
        d += cur
        cur = er
        if not cur.any():
            break
    d += cur * 1.0
    return d


# ================================================================================================= the hand
FINGERS = {                 # base (x, y) cm on the knuckle line of a RIGHT hand seen from the back, segment lengths,
    'index': ((-2.9, 9.35), (4.2, 2.5, 1.95), 1.0, -3.0),           # radius at the base, splay (deg)
    'middle': ((-0.95, 9.75), (4.6, 2.8, 2.05), 1.04, 0.0),
    'ring': ((0.98, 9.45), (4.25, 2.6, 2.0), 0.98, 3.0),
    'little': ((2.78, 8.7), (3.3, 2.0, 1.75), 0.86, 7.5),
}
PALM = [(-3.1, 0.0), (-3.8, 1.6), (-4.15, 4.6), (-4.0, 8.4), (-3.45, 9.6), (-1.7, 10.15), (0.2, 10.25), (2.1, 9.75),
        (3.55, 8.85), (4.0, 7.0), (3.85, 3.2), (3.2, 0.0)]


@dataclasses.dataclass
class HandPose:
    wrist: tuple                 # canvas px of the wrist centre
    ang: float = 0.0             # 0 = fingers toward -y (up the canvas); positive turns clockwise
    s: float = 3.4               # px per cm
    side: str = 'R'              # R / L hand
    view: str = 'dorsal'         # dorsal (back of the hand) / palmar
    spread: float = 0.0          # extra splay of the fingers (deg)
    curl: tuple = (0.1, 0.1, 0.12, 0.15)     # index, middle, ring, little: 0 flat .. 1 fist
    thumb: tuple = (-8.0, 0.2)   # (abduction deg, curl)
    pitch: float = 0.0           # the hand tilts its fingertips down into the table (deg): shortens it
    glove: bool = False
    fold_under: tuple = (0, 0, 0, 0)   # fingers hidden under something from this segment on (1..3), 0 none


def _xf(p: HandPose):
    """Local cm -> canvas px."""
    a = math.radians(p.ang)
    ca, sa = math.cos(a), math.sin(a)
    mir = -1.0 if (p.side == 'L') != (p.view == 'palmar') else 1.0
    fp = math.cos(math.radians(p.pitch))

    def f(x, y):
        x = x * mir
        y = y * fp
        X, Y = x * p.s, -y * p.s
        return (p.wrist[0] + X * ca - Y * sa, p.wrist[1] + X * sa + Y * ca)
    return f, mir


def finger_chain(p: HandPose, name, extra_splay=0.0):
    """Joint points of one finger in canvas px (projected: flexion shortens the segments seen from above)."""
    f, mir = _xf(p)
    (bx, by), lens, r0, splay = FINGERS[name]
    i = ('index', 'middle', 'ring', 'little').index(name)
    c = p.curl[i]
    flex = (c * 62.0, c * 96.0, c * 62.0)
    sp = math.radians(splay + p.spread * (i - 1.2) + extra_splay)
    pts = [(bx, by)]
    acc = 0.0
    x, y = bx, by
    for L, fl in zip(lens, flex):
        acc += fl
        Lp = L * max(0.18, math.cos(math.radians(min(acc, 160.0))))
        x += math.sin(sp) * Lp
        y += math.cos(sp) * Lp
        pts.append((x, y))
    radii = [r0, r0 * 0.95, r0 * 0.88, r0 * 0.8]
    return [f(*q) for q in pts], [r * p.s for r in radii], acc


def thumb_chain(p: HandPose):
    f, mir = _xf(p)
    ab, c = p.thumb
    base = (-2.6, 2.2)
    a0 = math.radians(-36.0 - ab)
    pts = [base]
    x, y = base
    for L, k in ((2.6, 0.0), (3.0, 0.5), (2.45, 1.0)):
        a = a0 + math.radians(c * 40.0 * k)
        x += math.sin(a) * L
        y += math.cos(a) * L
        pts.append((x, y))
    radii = [1.55, 1.22, 1.08, 0.92]
    return [f(*q) for q in pts], [r * p.s for r in radii]


def draw_hand(cv: Canvas, p: HandPose, skin='skin', nail='nail', glove_mat=None, grime=False, plaster=False,
              ring=False):
    """Palm, thumb and four fingers (each one part), knuckles, creases, nails or the glove's points."""
    f, mir = _xf(p)
    s = p.s
    mat = glove_mat if p.glove else skin
    out = {}
    # palm
    pts = [f(x, y) for (x, y) in PALM]
    w0 = f(0.0, 0.0)
    w1 = f(-0.4, 10.0)
    ax_, ay_ = w1[0] - w0[0], w1[1] - w0[1]
    al = math.hypot(ax_, ay_) + 1e-6
    nx_, ny_ = -ay_ / al, ax_ / al
    hw = 4.0 * s

    def dome(X, Y):
        v = ((X - w0[0]) * nx_ + (Y - w0[1]) * ny_) / hw
        return 0.55 * hw * np.sqrt(np.clip(1 - np.clip(v, -1, 1) ** 2, 0, 1))
    pid, pm = cv.poly(pts, mat, R=1.6 * s / 3.4, cyl=0.0, relief=dome, strength=0.55, inline=False, name='palm')
    palm_full = cv._full(pm)
    out['palm'] = palm_full
    if p.view == 'dorsal':
        # tendons fanning from the wrist to the knuckles; the knuckle bumps
        for name in ('index', 'middle', 'ring', 'little'):
            (bx, by), lens, r0, splay = FINGERS[name]
            if name in ('index', 'ring') and not p.glove:
                tm = cv.line_mask([f(bx * 0.35, 2.4), f(bx * 0.9, by - 1.6)], 0.45) & palm_full
                cv.bias(tm, 0.45)
        for name in ('index', 'middle', 'ring', 'little'):
            (bx, by), lens, r0, splay = FINGERS[name]
            kx, ky = f(bx, by - 0.35)
            km = cv.line_mask([(kx - 0.8 * s * 0.5, ky), (kx + 0.8 * s * 0.5, ky)], 0.9) & palm_full
            cv.bias(km, 0.7)
    else:
        # the palm's lines: heart line, head line, life line
        for seg in (((-3.4, 7.0), (0.0, 7.6), (3.4, 7.9)), ((-3.6, 5.4), (-0.6, 5.3), (2.6, 4.4)),
                    ((-3.4, 6.0), (-2.1, 3.4), (-1.0, 0.9))):
            lm = cv.line_mask([f(*q) for q in seg], 0.42) & palm_full
            cv.bias(lm, -1.0)
        th = cv.line_mask([f(-2.6, 2.6), f(-1.3, 1.2)], 1.6) & palm_full
        cv.bias(th, 0.5)
    # fingers: the far ones first (little -> index for a dorsal right hand drawn with the index over)
    order = ('little', 'ring', 'middle', 'index')
    for k, name in enumerate(order):
        i = ('index', 'middle', 'ring', 'little').index(name)
        pts_, radii, acc = finger_chain(p, name)
        under = p.fold_under[i]
        segs = []
        for j in range(3):
            if under and j >= under:
                break
            segs.append((pts_[j], pts_[j + 1], radii[j], radii[j + 1]))
        if not segs:
            continue
        pid, fm = cv.caps(segs, mat, inline=True, name='finger_' + name)
        full = cv._full(fm)
        out[name] = full
        # creases at the two finger joints (dorsal: short wrinkles; palmar: a firm line)
        for j in (1, 2):
            if under and j >= under:
                continue
            (ax, ay), (bx2, by2) = pts_[j - 1], pts_[j]
            if j < len(pts_) - 1:
                cx_, cy_ = pts_[j]
                dx, dy = bx2 - ax, by2 - ay
                L = math.hypot(dx, dy) + 1e-6
                nx, ny = -dy / L, dx / L
                w_ = radii[j] * 0.75
                cm = cv.line_mask([(cx_ - nx * w_, cy_ - ny * w_), (cx_ + nx * w_, cy_ + ny * w_)], 0.42) & full
                cv.bias(cm, -1.0 if (p.view == 'palmar' or not p.glove) else -0.7)
                if p.view == 'dorsal' and not p.glove:
                    hm = cv.line_mask([(cx_ - nx * w_ * 0.5 + dx / L * 1.2, cy_ - ny * w_ * 0.5 + dy / L * 1.2),
                                       (cx_ + nx * w_ * 0.5 + dx / L * 1.2, cy_ + ny * w_ * 0.5 + dy / L * 1.2)],
                                      0.4) & full
                    cv.bias(hm, 0.6)
        # the nail (dorsal, not gloved, not folded under, not curled away)
        if p.view == 'dorsal' and not p.glove and not under and acc < 120.0:
            (ax, ay), (bx2, by2) = pts_[2], pts_[3]
            dx, dy = bx2 - ax, by2 - ay
            L = math.hypot(dx, dy) + 1e-6
            ux, uy = dx / L, dy / L
            cx_, cy_ = ax + dx * 0.62, ay + dy * 0.62
            rr = radii[3] * 0.62
            ln = max(1.2, L * 0.42)
            yy, xx = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32) + 0.5
            u_ = (xx - cx_) * ux + (yy - cy_) * uy
            v_ = (xx - cx_) * (-uy) + (yy - cy_) * ux
            nm = ((u_ / ln) ** 2 + (v_ / rr) ** 2 < 1.0) & full
            cv.tone(nm, 3, mat=nail)
            tip = nm & (u_ > ln * 0.45)
            cv.tone(tip, 4, mat=nail)
            if grime:
                cv.tone(nm & (u_ > ln * 0.62), 1, mat=nail)
                cv.tone(nm & (np.abs(v_) > rr * 0.7), 2, mat=nail)
            edge = nm & (u_ < -ln * 0.55)
            cv.tone(edge, 2, mat=nail)
        if p.view == 'palmar' and not under:
            (ax, ay), (bx2, by2) = pts_[2], pts_[3]
            pad = cv.line_mask([(ax + (bx2 - ax) * 0.45, ay + (by2 - ay) * 0.45),
                                (ax + (bx2 - ax) * 0.8, ay + (by2 - ay) * 0.8)], radii[3] * 0.4) & full
            cv.bias(pad, 0.6)
        if p.glove and p.view == 'dorsal' and k < 3:
            # the seam between this finger and the next (stitched fourchette line along the finger's side)
            (ax, ay), (bx2, by2) = pts_[0], pts_[1]
            dx, dy = bx2 - ax, by2 - ay
            L = math.hypot(dx, dy) + 1e-6
            nx, ny = -dy / L, dx / L
            sgn = -mir
            r_ = radii[0] * 0.78
            sm = cv.line_mask([(ax + nx * r_ * sgn, ay + ny * r_ * sgn),
                               (bx2 + nx * r_ * sgn * 0.9, by2 + ny * r_ * sgn * 0.9)], 0.4) & full
            cv.bias(sm, -1.0)
    # thumb (over the palm on a dorsal right hand it lies at the side; one part)
    tp, tr = thumb_chain(p)
    pid, tm = cv.caps([(tp[j], tp[j + 1], tr[j], tr[j + 1]) for j in range(3)], mat, inline=True, name='thumb')
    tfull = cv._full(tm)
    out['thumb'] = tfull
    cm = cv.line_mask([((tp[2][0] + tp[1][0]) / 2, (tp[2][1] + tp[1][1]) / 2), tp[2]], 0.4) & tfull
    if p.view == 'dorsal' and not p.glove:
        (ax, ay), (bx2, by2) = tp[2], tp[3]
        dx, dy = bx2 - ax, by2 - ay
        L = math.hypot(dx, dy) + 1e-6
        ux, uy = dx / L, dy / L
        cx_, cy_ = ax + dx * 0.6, ay + dy * 0.6
        rr = tr[3] * 0.62
        ln = max(1.4, L * 0.42)
        yy, xx = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32) + 0.5
        u_ = (xx - cx_) * ux + (yy - cy_) * uy
        v_ = (xx - cx_) * (-uy) + (yy - cy_) * ux
        nm = ((u_ / ln) ** 2 + (v_ / rr) ** 2 < 1.0) & tfull
        cv.tone(nm, 3, mat=nail)
        cv.tone(nm & (u_ > ln * 0.45), 4, mat=nail)
        if grime:
            cv.tone(nm & (u_ > ln * 0.62), 1, mat=nail)
    if p.glove and p.view == 'dorsal':
        # three stitched points running from between the knuckles toward the wrist, a highlight beside each
        for (x0_, x1_) in ((-1.85, -1.3), (0.1, 0.0), (1.95, 1.2)):
            pm_ = cv.line_mask([f(x0_, 9.0), f(x1_, 3.4)], 0.42) & palm_full
            cv.bias(pm_, -1.0)
            hm_ = cv.line_mask([f(x0_ + 0.55, 8.7), f(x1_ + 0.5, 3.6)], 0.4) & palm_full & ~pm_
            cv.bias(hm_, 0.7)
        # the wrist's gather and the press stud
        gm = cv.line_mask([f(-2.9, 1.1), f(2.9, 1.1)], 0.45) & palm_full
        cv.bias(gm, -1.0)
        sx_, sy_ = f(-2.2, 0.55)
        cv.tone(cv.line_mask([(sx_ - 0.5, sy_), (sx_ + 0.5, sy_)], 1.1) & palm_full, 4, mat='stud')
        cv.tone(cv.line_mask([(sx_ - 0.6, sy_ - 0.6), (sx_ - 0.6, sy_ - 0.6)], 0.5) & palm_full, 5, mat='stud')
    if plaster and not p.glove:
        pts_, radii, acc = finger_chain(p, 'index')
        (ax, ay), (bx2, by2) = pts_[1], pts_[2]
        m_ = cv.line_mask([(ax + (bx2 - ax) * 0.25, ay + (by2 - ay) * 0.25),
                           (ax + (bx2 - ax) * 0.7, ay + (by2 - ay) * 0.7)], radii[1] * 0.95) & out['index']
        cv.tone(m_, 3, mat='plaster')
        cv.tone(m_ & cv.line_mask([(ax + (bx2 - ax) * 0.47, ay + (by2 - ay) * 0.47)] * 2, 1.3), 2, mat='plaster')
    if ring and not p.glove:
        pts_, radii, acc = finger_chain(p, 'ring')
        (ax, ay), (bx2, by2) = pts_[0], pts_[1]
        cx_, cy_ = ax + (bx2 - ax) * 0.55, ay + (by2 - ay) * 0.55
        dx, dy = bx2 - ax, by2 - ay
        L = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L, dx / L
        rm = cv.line_mask([(cx_ - nx * radii[0], cy_ - ny * radii[0]), (cx_ + nx * radii[0], cy_ + ny * radii[0])],
                          0.6) & out['ring']
        cv.tone(rm, 3, mat='gold')
        cv.tone(rm & cv.line_mask([(cx_, cy_), (cx_, cy_)], 0.9), 5, mat='gold')
    return out


# ================================================================================================= sleeves
def sleeve(cv: Canvas, wrist, far, w_near, w_far, mat, seed=0, folds=6, quilt=False, cuff_round=0.35,
           name='sleeve', bunch=1.0, herring=False, seam=None):
    """A coat sleeve from far (off canvas) to the wrist: a tapered polygon whose height carries folds -- a stack
    of short ones at the cuff, long spiralling ones up the forearm -- and, for a quilted jacket, its channels."""
    ax, ay = far
    bx, by = wrist
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / n
        w = (w_far + (w_near - w_far) * t) / 2.0
        pts.append((ax + dx * t + nx * w, ay + dy * t + ny * w))
    # the cuff end: a gently convex arc around the wrist
    for i in range(1, 8):
        a = math.pi * i / 8.0
        w = w_near / 2.0
        pts.append((bx + nx * math.cos(a) * w + ux * math.sin(a) * w * cuff_round,
                    by + ny * math.cos(a) * w + uy * math.sin(a) * w * cuff_round))
    for i in range(n, -1, -1):
        t = i / n
        w = (w_far + (w_near - w_far) * t) / 2.0
        pts.append((ax + dx * t - nx * w, ay + dy * t - ny * w))
    rng = [((k * 7919 + seed * 104729) % 1000) / 1000.0 for k in range(40)]

    def relief(X, Y):
        u = (X - ax) * ux + (Y - ay) * uy            # along, 0 at far, L at the wrist
        v = (X - ax) * nx + (Y - ay) * ny            # across
        wloc = (w_far + (w_near - w_far) * np.clip(u / L, 0, 1)) / 2.0
        vv = v / np.maximum(wloc, 1.0)
        h = 0.62 * wloc * np.sqrt(np.clip(1 - np.clip(vv, -1, 1) ** 2, 0, 1))
        # stacked folds near the cuff: arcs bowing toward the hand
        for k in range(int(3 * bunch)):
            c = L - w_near * (0.55 + 0.42 * k + 0.2 * rng[k])
            bow = (1 - vv ** 2) * w_near * (0.18 + 0.1 * rng[k + 3])
            d = u - (c + bow)
            sg = (2.4 + 1.2 * rng[k + 6]) * w_near / 60.0
            h += 3.2 * w_near / 60.0 * np.exp(-(d / sg) ** 2) * np.clip(1 - np.abs(vv) * 0.35, 0, 1)
        # long diagonal folds up the forearm
        for k in range(folds):
            c = L * (0.1 + 0.62 * rng[k + 10]) - w_near * 0.3
            ang = (rng[k + 20] - 0.5) * 1.6
            span = 0.45 + 0.4 * rng[k + 30]
            d = (u - c) - vv * wloc * ang
            mask_v = np.clip(1 - (np.abs(vv - (rng[k + 25] - 0.5)) / span) ** 2, 0, 1)
            sg = 3.0 * w_near / 60.0
            h += 2.4 * w_near / 60.0 * np.exp(-(d / sg) ** 2) * mask_v
        if quilt:
            ph = np.mod(u, 9.0)
            h -= 1.5 * np.exp(-((ph - 0.5) / 0.9) ** 2)
        return h

    pid, pm = cv.poly(pts, mat, R=2.0, cyl=0.0, relief=relief, strength=0.9, name=name, inline=True)
    full = cv._full(pm)
    yy, xx = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32) + 0.5
    if herring:
        uu = (xx - ax) * ux + (yy - ay) * uy
        vv_ = (xx - ax) * nx + (yy - ay) * ny
        zz = np.abs(np.mod(uu, 6.0) - 3.0)
        cv.bias(full & (np.mod(np.floor(vv_ + zz), 3.0) == 0), -0.55)
    if seam:
        vs = (xx - ax) * nx + (yy - ay) * ny
        uu = (xx - ax) * ux + (yy - ay) * uy
        wl = (w_far + (w_near - w_far) * np.clip(uu / L, 0, 1)) / 2.0
        cv.bias(full & (np.abs(vs - wl * seam) < 0.6) & (uu < L - w_near * 0.25), -1.0)
    if quilt:
        u = (xx - ax) * ux + (yy - ay) * uy
        seam = full & (np.mod(u, 9.0) < 1.0)
        cv.bias(seam, -1.0)
    return full, (ux, uy, nx, ny)


def cuff_band(cv: Canvas, wrist, dirv, width, depth, mat, round_=0.35, name='cuff', ribs=0):
    """A cuff (shirt / knitted / glove gauntlet) around the wrist, `depth` px long toward the hand."""
    ux, uy, nx, ny = dirv
    bx, by = wrist
    w = width / 2.0
    pts = []
    for i in range(0, 9):
        a = math.pi * i / 8.0
        pts.append((bx + nx * math.cos(a) * w - ux * math.sin(a) * w * round_ * 0.5,
                    by + ny * math.cos(a) * w - uy * math.sin(a) * w * round_ * 0.5))
    for i in range(8, -1, -1):
        a = math.pi * i / 8.0
        pts.append((bx + ux * depth + nx * math.cos(a) * w * 0.94 + ux * math.sin(a) * w * round_,
                    by + uy * depth + ny * math.cos(a) * w * 0.94 + uy * math.sin(a) * w * round_))
    pid, pm = cv.poly(pts, mat, R=2.5, cyl=0.8, inline=True, name=name)
    full = cv._full(pm)
    if ribs:
        yy, xx = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32) + 0.5
        v = (xx - bx) * nx + (yy - by) * ny
        cv.bias(full & (np.mod(v, ribs) < 1.0), -1.0)
    return full


# ================================================================================================= materials
def mats_common(cv: Canvas, skin='#c48a68', nail='#d8aa98'):
    cv.mat('skin', skin)
    cv.mat('nail', nail, outline=False)
    cv.mat('stud', ['#1e1e22', '#3a3a40', '#5e5e66', '#8a8a92', '#b8b8c0', '#eeeef2'], outline=False, glossy=True)
    cv.mat('gold', ['#3a2408', '#6a4612', '#9a6e22', '#c8983a', '#e8c46a', '#fff0b8'], outline=False, glossy=True)
    cv.mat('plaster', ['#5a4a3a', '#8a7660', '#b49e82', '#d2bea0', '#e8d8bc', '#f6ecd8'], outline=False)
    cv.mat('paper', ['#3a4458', '#7a8494', '#b4bac4', '#dcdde0', '#eeeeea', '#fbfbf6'], outline=True)
    cv.mat('ink', ['#101830', '#1c2a50', '#2a3c74', '#3a5090', '#5a70b0', '#8a9ad0'], outline=False)


def carbons(cv: Canvas, x, y, w, h, ang=0.0, fold=0.0):
    """Lev's carbon copies: a thin bundle of flimsy paper, typed lines, the blue of the carbon at its edges."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    hw, hh = w / 2.0, h / 2.0 * (1.0 - 0.45 * fold)

    def P(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    m, x0, y0 = CC.poly_mask([P(-hw, -hh), P(hw, -hh), P(hw, hh), P(-hw, hh)])
    cv.put(m, x0, y0, 'paper', None, tone=4.0, name='carbons', inline=False)
    full = cv._full((m, x0, y0))
    yy, xx = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32) + 0.5
    u = (xx - x) * ca + (yy - y) * sa
    v = -(xx - x) * sa + (yy - y) * ca
    lines = full & (np.mod(v + hh, 3.0) < 1.0) & (np.abs(u) < hw - 3) & (np.abs(v) < hh - 3) & \
        (np.mod(np.floor(u / 2.0) + np.floor(v / 3.0) * 3, 7) < 5)
    cv.tone(lines, 2, mat='ink')
    cv.tone(full & ((np.abs(u) > hw - 1.5) | (np.abs(v) > hh - 1.5)), 3, mat='ink')
    cv.tone(full & (v > hh - 2.5) & (u > -hw + 2), 5, mat='paper')
    return full



def crop(rgba, pad=1):
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return rgba, (0, 0)
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + pad + 1)
    return rgba[y0:y1, x0:x1].copy(), (x0, y0)
