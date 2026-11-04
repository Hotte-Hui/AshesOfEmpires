"""chargen_portrait -- 112x112 dialogue portraits (bust, 3/4 view facing right) for the speaking cast.

Method (deterministic; no AI, nothing sampled from reference images):
  1. A bust is modelled from analytic ellipsoids in view space (skull, jaw, nose, brow, cheeks, ears,
     neck, shoulders, collars, hats).  Each primitive is ray-cast orthographically (exact quadratic hit)
     into a per-group depth buffer; primitives of one group merge with a polynomial smooth-max (organic
     joins: nose into face, jaw into skull); groups are composited by depth.
  2. A 2.5D screen-space march along the key light gives cast shadows (hat brims shadow the eyes).
  3. Lighting = one strong warm key (front-right-top), deep navy ambient, cool back rim.  The light value
     is posterised onto short hand-picked material ramps (navy shadow -> warm key) with a narrow
     ordered-dither band; selective silhouette outlines and depth-contour lines are added.
  4. Eyes, brows, mouths, wrinkles and spectacles are hand-designed pixel stamps placed at projected
     3D landmarks and swapped per expression (neutral, concerned, determined, surprised).
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image

W = H = 112
EXPRESSIONS = ['neutral', 'concerned', 'determined', 'surprised']
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 + 1 / 32


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)


def ramp(*hs):
    return [hexc(h) for h in hs]


def rotm(yaw=0.0, pitch=0.0, roll=0.0):
    """Rotation: yaw turns the +z (towards viewer) axis towards +x (image right); pitch > 0 tilts the
    face down; roll > 0 tilts the head clockwise in the picture."""
    y, p, r = (math.radians(a) for a in (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), math.sin(p)], [0, -math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


# ----------------------------------------------------------------------------------- scene
class Scene:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w]
        self.X = xx + 0.5
        self.Y = yy + 0.5
        self.groups: dict[str, dict] = {}
        self.order: list[str] = []
        self.mat_names: list[str] = []
        self.landmarks: dict[str, np.ndarray] = {}

    def mid(self, name):
        if name not in self.mat_names:
            self.mat_names.append(name)
        return self.mat_names.index(name)

    def group(self, g):
        if g not in self.groups:
            self.groups[g] = dict(z=np.full((self.h, self.w), -1e9), n=np.zeros((self.h, self.w, 3)),
                                  mat=np.full((self.h, self.w), -1, np.int32))
            self.order.append(g)
        return self.groups[g]

    def ellipsoid(self, c, r, R=None, mat='skin', group='head', k=0.0, clip=None, inner=False, frame=None):
        """c, r in view space (or in `frame` = (origin, rotation) local space if given)."""
        R = np.eye(3) if R is None else np.asarray(R, float)
        c = np.asarray(c, float)
        r = np.asarray(r, float)
        if frame is not None:
            o, FR = frame[0], frame[1]
            sc_ = frame[2] if len(frame) > 2 else 1.0
            c = o + FR @ (c * sc_)
            R = FR @ R
            r = r * sc_
        Z0 = 500.0
        O = np.stack([self.X - c[0], self.Y - c[1], np.full_like(self.X, Z0 - c[2])], -1)
        q = (O @ R) / r
        e = (np.array([0.0, 0.0, -1.0]) @ R) / r
        a = float(e @ e)
        b = 2.0 * (q @ e)
        cc = (q * q).sum(-1) - 1.0
        disc = b * b - 4 * a * cc
        hit = disc >= 0
        sq = np.sqrt(np.clip(disc, 0, None))
        t = (-b - sq) / (2 * a)
        L = q + t[..., None] * e
        if clip is not None:
            keep = clip(L * r)
            if inner:
                t2 = (-b + sq) / (2 * a)
                L2 = q + t2[..., None] * e
                keep2 = clip(L2 * r) & ~keep
                t = np.where(keep, t, t2)
                L = np.where(keep[..., None], L, L2)
                hit &= keep | keep2
            else:
                hit &= keep
        z = Z0 - t
        nl = L / r
        n = nl @ R.T
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        self._merge(group, hit, z, n, self.mid(mat), k)

    def _merge(self, g, hit, z, n, mat, k):
        G = self.group(g)
        both = hit & (G['z'] > -1e8)
        only = hit & ~both
        G['z'][only] = z[only]
        G['n'][only] = n[only]
        G['mat'][only] = mat
        if both.any():
            za, zb = G['z'][both], z[both]
            if k > 0:
                h = np.clip(0.5 + 0.5 * (za - zb) / k, 0, 1)
                zz = zb + (za - zb) * h + k * h * (1 - h)
            else:
                h = (za >= zb).astype(float)
                zz = np.maximum(za, zb)
            nn = G['n'][both] * h[:, None] + n[both] * (1 - h[:, None])
            nn /= np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9
            G['z'][both] = zz
            G['n'][both] = nn
            G['mat'][both] = np.where(h >= 0.5, G['mat'][both], mat)

    def landmark(self, name, p, frame=None):
        p = np.asarray(p, float)
        if frame is not None:
            o, FR = frame[0], frame[1]
            sc_ = frame[2] if len(frame) > 2 else 1.0
            p = o + FR @ (p * sc_)
        self.landmarks[name] = p

    def composite(self):
        z = np.full((self.h, self.w), -1e9)
        n = np.zeros((self.h, self.w, 3))
        mat = np.full((self.h, self.w), -1, np.int32)
        grp = np.full((self.h, self.w), -1, np.int32)
        for gi, g in enumerate(self.order):
            G = self.groups[g]
            m = G['z'] > z
            z[m] = G['z'][m]
            n[m] = G['n'][m]
            mat[m] = G['mat'][m]
            grp[m] = gi
        self.z, self.n, self.mat, self.grp = z, n, mat, grp
        return self


def shadow_march(z, occ, L, steps=48, bias=1.2):
    """2.5D cast shadows: march from every pixel towards the light over the depth map."""
    h, w = z.shape
    lx, ly, lz = L
    s = 1.0 / max(1e-6, math.hypot(lx, ly))
    dx, dy, dz = lx * s, -ly * s, lz * s
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    shadow = np.zeros((h, w), bool)
    for i in range(1, steps):
        X = np.round(xx + dx * i).astype(int)
        Y = np.round(yy + dy * i).astype(int)
        inside = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
        Xc, Yc = np.clip(X, 0, w - 1), np.clip(Y, 0, h - 1)
        zz = z[Yc, Xc]
        shadow |= inside & occ[Yc, Xc] & (zz > z + dz * i + bias)
    return shadow & occ


# ----------------------------------------------------------------------------------- stamps
def parse(rows):
    rows = [r for r in (ln.strip() for ln in rows.strip('\n').split('\n')) if r]
    return rows


def stamp(img, rows, x0, y0, colors: dict, mask=None, anchor=(0, 0)):
    """Draw ASCII pixel stamp; '.' is transparent; anchor = (col,row) in the stamp placed at x0,y0."""
    if isinstance(rows, str):
        rows = parse(rows)
    ax, ay = anchor
    X0 = int(round(x0)) - ax
    Y0 = int(round(y0)) - ay
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.' or ch == ' ':
                continue
            x, y = X0 + i, Y0 + j
            if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
                if mask is not None and not mask[y, x]:
                    continue
                c = colors.get(ch)
                if c is not None:
                    img[y, x] = c


# ----------------------------------------------------------------------------------- shading
class Look:
    """Lighting + palette for one portrait."""

    def __init__(self, key=(0.70, 0.46, 0.55), rim=(-0.82, 0.30, -0.50), ambient=0.06,
                 thresholds=(0.08, 0.18, 0.30, 0.45, 0.62, 0.80), dither=0.035, bg=None, rim_cols=None):
        self.key = np.asarray(key, float) / np.linalg.norm(key)
        self.rim = np.asarray(rim, float) / np.linalg.norm(rim)
        self.ambient = ambient
        self.th = thresholds
        self.dither = dither
        self.bg = bg
        self.rim_cols = rim_cols


def clean_tones(tone, mat, passes=2):
    """Remove isolated tone pixels (cluster cleanup) inside one material."""
    h, w = tone.shape
    for _ in range(passes):
        p = np.pad(tone, 1, mode='edge')
        pm = np.pad(mat, 1, mode='edge')
        offs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        nbs = [p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in offs]
        mms = [pm[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in offs]
        same = sum(((nb == tone) | (mm != mat)).astype(int) for nb, mm in zip(nbs, mms))
        diff_all = sum(((nb != tone) & (mm == mat)).astype(int) for nb, mm in zip(nbs, mms))
        orphan = (diff_all >= 3) & (same <= 1)
        med = np.median(np.stack(nbs), 0).round().astype(np.int32)
        tone = np.where(orphan, med, tone)
    return tone


def shade_portrait(sc: Scene, look: Look, ramps: dict, no_shadow_mats=()):
    h, w = sc.h, sc.w
    occ = sc.mat >= 0
    # image-space normal: n.y is "down" in our view space -> light y up = -y
    n = sc.n
    L = np.array([look.key[0], -look.key[1], look.key[2]])
    Lr = np.array([look.rim[0], -look.rim[1], look.rim[2]])
    ndl = np.clip((n * L).sum(-1), 0, 1)
    sh = shadow_march(sc.z, occ, look.key)
    for nm in no_shadow_mats:
        if nm in sc.mat_names:
            sh &= sc.mat != sc.mat_names.index(nm)
    lit = ndl * np.where(sh, 0.12, 1.0)
    val = look.ambient + lit
    bay = BAYER4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    v2 = val + (bay - 0.5) * look.dither
    tone = np.zeros((h, w), np.int32)
    for t in look.th:
        tone += (v2 >= t)
    tone = clean_tones(tone, sc.mat)
    ndr = (n * Lr).sum(-1)
    near_edge = np.zeros((h, w), bool)
    pad_bg = np.pad(~occ, 2, constant_values=True)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) <= 2:
                near_edge |= pad_bg[2 + dy:2 + dy + h, 2 + dx:2 + dx + w]
    rim1 = occ & near_edge & (ndr > 0.30) & (lit < 0.22)
    rim2 = rim1 & (ndr > 0.58)
    edge1 = np.zeros((h, w), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        edge1 |= pad_bg[2 + dy:2 + dy + h, 2 + dx:2 + dx + w]
    rim2 &= edge1
    # depth contours: a pixel whose neighbour is clearly in front gets a dark contour
    pad = np.pad(sc.z, 1, constant_values=-1e9)
    contour = np.zeros((h, w), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        contour |= occ & (nb > sc.z + 3.5) & (nb > -1e8)
    # silhouette outline (selective: only where unlit)
    pad_o = np.pad(occ, 1)
    sil = np.zeros((h, w), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sil |= occ & ~pad_o[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    img = np.zeros((h, w, 4), np.uint8)
    if look.bg is not None:
        img[:] = look.bg
    for mi, mname in enumerate(sc.mat_names):
        sel = sc.mat == mi
        if not sel.any():
            continue
        R = np.stack(ramps[mname])
        img[sel] = R[np.clip(tone, 0, len(R) - 1)][sel]
    rc = look.rim_cols
    if rc is not None:
        img[rim1] = rc[0]
        img[rim2] = rc[1]
    # depth-contour lines (one step above the darkest shade) and selective silhouette outline (darkest
    # shade of the material, only where the surface is unlit and not rim-lit)
    dark = contour & (val < 0.62)
    sil_dark = sil & (val < 0.30) & ~rim1
    for mi, mname in enumerate(sc.mat_names):
        R = ramps[mname]
        img[(sc.mat == mi) & dark] = R[min(1, len(R) - 1)]
        img[(sc.mat == mi) & sil_dark] = R[0]
    return img, dict(val=val, tone=tone, shadow=sh, occ=occ, ndl=ndl)


# ----------------------------------------------------------------------------------- anatomy
def add_head(sc: Scene, frame, p: dict):
    """Generic head in head-local space (x: viewer's right when facing front, y down, z to viewer)."""
    jw = p.get('jaw_w', 13.5)        # jaw half width
    cw = p.get('crown_w', 18.5)
    nl = p.get('nose_len', 1.0)
    nw = p.get('nose_w', 1.0)
    chin = p.get('chin', 1.0)
    jd = p.get('jaw_drop', 0.0)      # surprised: open jaw
    fh = p.get('face_h', 1.0)        # lower-face height factor
    E = dict(frame=frame, group='head')
    _ell = sc.ellipsoid

    def ell(c, r, **kw):             # scale y of everything below the brow line
        c = (c[0], c[1] * fh if c[1] > 0 else c[1], c[2])
        _ell(c, r, **kw)
    ell((0, -8, -1), (cw, 21, 21), mat='skin', k=0, **E)
    ell((0, 5, 3.5), (cw - 3.2, 16, 15), mat='skin', k=6, **E)
    ell((0, 15 + jd * 0.6, 2.5), (jw, 9, 13), mat='skin', k=5, **E)
    ell((0, 21.5 + jd, 9.5), (6.6 * chin, 4.8, 7), mat='skin', k=4, **E)
    for sx in (-1, 1):
        ell((sx * 10.2, 2.5, 10.5), (6.2, 5, 6.2), mat='skin', k=4, **E)
        ell((sx * 18.2, 0.5, -2.5), (2.8, 6.8, 5.0), mat='skin', k=1.5, **E)          # ears
    ell((0, -6.0, 15.0), (13.5, 3.6, 5.2), mat='skin', k=3, **E)                     # brow ridge
    ell((0, 0.5, 17.5), (2.5 * nw, 8.5 * nl, 3.6), mat='skin', k=2.5, **E)            # bridge
    ell((0, 7.5 * nl, 20.5 + 1.5 * (nl - 1)), (3.3 * nw, 3.0, 3.4), mat='skin', k=2.0, **E)  # tip
    for sx in (-1, 1):
        ell((sx * 3.3 * nw, 8.5 * nl, 17.5), (2.4, 2.1, 2.3), mat='skin', k=1.5, **E)   # wings
    ell((0, 12.3, 17.2), (5.4 * p.get('lip_w', 1.0), 1.7, 3.0), mat='skin', k=1.5, **E)
    ell((0, 15.0 + jd, 16.2), (5.0 * p.get('lip_w', 1.0), 2.0 * p.get('lip_l', 1.0), 3.0), mat='skin',
                 k=1.5, **E)
    # neck (own group -> contour under the jaw)
    sc.ellipsoid((0, 30, -4), (10.5, 16, 10.5), mat='skin', group='neck', frame=frame, k=0)
    for nm, pt in {'eye_n': (-7.2, -1.2, 15.2), 'eye_f': (7.2, -1.2, 15.2),
                   'brow_n': (-7.4, -6.6, 16.6), 'brow_f': (7.4, -6.6, 16.6),
                   'mouth': (0.0, 13.6 + jd * 0.5, 18.0), 'nose': (0.0, 8.5 * nl, 21.5),
                   'nostril': (2.2, 9.2 * nl, 19.5), 'chin': (0.0, 21.5 + jd, 15.0),
                   'forehead': (0.0, -13.0, 17.0), 'cheek_n': (-10.0, 5.0, 14.0), 'cheek_f': (10.0, 5.0, 14.0),
                   'ear': (-18.0, 0.5, -2.0), 'jaw_n': (-11.0, 15.0, 8.0)}.items():
        pt = (pt[0], pt[1] * fh if pt[1] > 0 else pt[1], pt[2])
        sc.landmark(nm, pt, frame)


def head_frame(origin=(52.0, 47.0, 0.0), yaw=30.0, pitch=3.0, roll=-2.0, scale=1.0):
    return (np.asarray(origin, float), rotm(yaw, pitch, roll), float(scale))


def project(sc, name):
    p = sc.landmarks[name]
    return p[0], p[1], p[2]


# ----------------------------------------------------------------------------------- features
EYES = {
    'near': {
        'neutral': ('''
            .LLLLLL.
            LLwWIIW.
            ..wWICl.
            ...lll..''', (4, 1)),
        'concerned': ('''
            ..LLLLL.
            .LwWWWWl
            ..wWIIl.
            ...lIl..''', (4, 1)),
        'determined': ('''
            .LLLLLL.
            LLLLIIL.
            ..wWICl.
            ...ll...''', (4, 1)),
        'surprised': ('''
            ..LLLL..
            .LwWWWL.
            LwWIIWWl
            .wWICWl.
            ..llll..''', (4, 2)),
    },
    'far': {
        'neutral': ('''
            .LLLL
            lWIIL
            .wICL
            ..ll.''', (2, 1)),
        'concerned': ('''
            .LLL.
            lWWWL
            .wIIL
            ..lI.''', (2, 1)),
        'determined': ('''
            .LLLL
            lLIIL
            .wICL
            ..l..''', (2, 1)),
        'surprised': ('''
            .LLL.
            lWWWL
            lWIIL
            .wICL
            ..ll.''', (2, 2)),
    },
}
BROWS = {
    'near': {
        'neutral': ('''
            ...bBBBBB.
            .bBBBBBBBB
            bBb.......''', (5, 1)),
        'concerned': ('''
            .......BBb
            ....bBBBBB
            .bBBBBb...
            bBb.......''', (5, 2)),
        'determined': ('''
            bBBBb.....
            .bBBBBBb..
            ....bBBBBB
            .......bBB''', (5, 1)),
        'surprised': ('''
            ...bBBBb..
            .bBBBBBBBb
            bBb.....bB''', (5, 4)),
    },
    'far': {
        'neutral': ('''
            BBBBb.
            BBBBBB
            .....b''', (2, 1)),
        'concerned': ('''
            BBb...
            BBBBb.
            ..bBBB''', (2, 2)),
        'determined': ('''
            ....bB
            ..bBBB
            BBBBb.
            Bb....''', (2, 1)),
        'surprised': ('''
            .BBBb.
            BBBBBB
            B....b''', (2, 4)),
    },
}
MOUTHS = {
    'neutral': ('''
        mMMMMMMm
        ..uuuu..''', (4, 0)),
    'concerned': ('''
        ..mMMMm.
        .mM...Mm
        mM.uuu.M
        ........''', (4, 0)),
    'determined': ('''
        MMMMMMMM
        .ssssss.''', (4, 0)),
    'surprised': ('''
        ..MMMM..
        .MTTTTM.
        .MDDDDM.
        ..MDDM..
        ...uu...''', (4, 1)),
}
CREASES = {
    'neutral': [],
    'concerned': [('forehead', '''
        .cccc...
        ....ccc.''', (4, 4)), ('forehead', '''
        ..ccc...''', (4, 1))],
    'determined': [('brow_mid', '''
        c.c
        c.c''', (1, 0))],
    'surprised': [('forehead', '''
        .cccccc.''', (4, 5)), ('forehead', '''
        ..cccccc''', (4, 2))],
}


def face_colors(c: dict, lit: bool):
    """Feature colour set (lit or in shadow)."""
    return {
        'L': c['lash'], 'W': c['white_lit'] if lit else c['white_dk'], 'w': c['white_dim'] if lit else c['white_dk2'],
        'I': c['iris'], 'C': c['catch'] if lit else c['white_dim'], 'l': c['lid'] if lit else c['lid_dk'],
        'B': c['brow'], 'b': c['brow2'], 'M': c['mouth'], 'm': c['mouth2'], 'u': c['lip'] if lit else c['lip_dk'],
        'D': c['mouth_in'], 'T': c['teeth'] if lit else c['teeth_dk'], 's': c['lid'] if lit else c['lid_dk'],
        'c': c['crease'] if lit else c['crease_dk'],
    }


def draw_features(img, sc, info, expr, cols, skin_mask, extra=None, creases=True):
    val = info['val']

    def lit_at(x, y):
        xi, yi = int(np.clip(round(x), 0, W - 1)), int(np.clip(round(y), 0, H - 1))
        return val[yi, xi] > 0.30

    for side in ('near', 'far'):
        x, y, z = project(sc, 'eye_' + side[0])
        rows, anc = EYES[side][expr]
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
        x, y, z = project(sc, 'brow_' + side[0])
        rows, anc = BROWS[side][expr]
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    x, y, z = project(sc, 'mouth')
    rows, anc = MOUTHS[expr]
    stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    for where, rows, anc in (CREASES[expr] if creases else []):
        if where == 'brow_mid':
            xn, yn, _ = project(sc, 'brow_n')
            xf, yf, _ = project(sc, 'brow_f')
            x, y = (xn + xf) / 2 + 0.5, (yn + yf) / 2 + 1
        else:
            x, y, _ = project(sc, where)
        stamp(img, rows, x, y, face_colors(cols, lit_at(x, y)), mask=skin_mask, anchor=anc)
    x, y, _ = project(sc, 'nostril')
    stamp(img, 'nn', x, y, {'n': cols['nostril']}, mask=skin_mask, anchor=(1, 0))
    if extra:
        extra(img, sc, info, expr, cols, skin_mask, lit_at)


# ----------------------------------------------------------------------------------- background
def background(cols: list, glow=None):
    """Navy gradient with a soft key-side glow, posterised with ordered dither."""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    t = 0.50 * (1 - yy / H) + 0.20 * (xx / W)
    if glow is not None:
        gx, gy, gr = glow
        d = np.sqrt((xx - gx) ** 2 + (yy - gy) ** 2) / gr
        t = t + 0.55 * np.clip(1 - d, 0, 1) ** 1.6
    vig = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
    t = t - 0.35 * np.clip(vig - 0.55, 0, 1)
    n = len(cols) - 1
    T = np.clip(t, 0, 0.999) * n
    idx = np.floor(T).astype(int)
    bay = BAYER4[yy.astype(int) % 4, xx.astype(int) % 4]
    idx = idx + ((T - idx) > bay)
    idx = np.clip(idx, 0, n)
    return np.stack(cols)[idx]


# ----------------------------------------------------------------------------------- helpers
def local_coords(sc, frame):
    """Head-local coordinates of every visible surface point."""
    o, R = frame[0], frame[1]
    s_ = frame[2] if len(frame) > 2 else 1.0
    P = np.stack([sc.X, sc.Y, sc.z], -1) - o
    return (P @ R) / s_          # = R^T p / s


def dither_mask(h=H, w=W, level=0.5):
    bay = BAYER4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    return bay < level


KARSK_FEAT = dict(lash='#140E14', white_lit='#CBBDA2', white_dim='#9A8C78', white_dk='#3C3E4A',
                  white_dk2='#2A2C38', iris='#2A3432', catch='#EDE6D2', lid='#9C6650', lid_dk='#3C2C34',
                  brow='#22171A', brow2='#4A3228', mouth='#3E2024', mouth2='#6A3A34', lip='#B0745A',
                  lip_dk='#4A3034', mouth_in='#1A0A10', teeth='#CDBFA4', teeth_dk='#5A5050', crease='#8A5A48',
                  crease_dk='#2E2430', nostril='#4A2A2A')
BERLIN_FEAT = dict(lash='#120E16', white_lit='#D2C2A2', white_dim='#A08C76', white_dk='#3E3A4C',
                   white_dk2='#2C2A3A', iris='#2E3440', catch='#F0E6D0', lid='#A2664E', lid_dk='#3E2C3A',
                   brow='#2A1E1A', brow2='#5A4030', mouth='#401E26', mouth2='#6E3A38', lip='#B8745A',
                   lip_dk='#4A2E38', mouth_in='#1A0A12', teeth='#D2C2A6', teeth_dk='#5A4E54', crease='#8E5A48',
                   crease_dk='#30243A', nostril='#4E2A2E')


def feat(d, **over):
    out = {k: hexc(v) for k, v in d.items()}
    for k, v in over.items():
        out[k] = hexc(v)
    return out


LOOK_KARSK = dict(bg=ramp('#04080C', '#07111A', '#0B1920', '#102228', '#162C30'),
                  rim=ramp('#2E5A5E', '#7FA89C'), glow=(98, 30, 70))
LOOK_BERLIN = dict(bg=ramp('#05070E', '#0A0E1A', '#0F1522', '#151D2C', '#1C2534'),
                   rim=ramp('#3A4A6A', '#8C9CC0'), glow=(98, 28, 70))
LOOK_ARCHIVE = dict(bg=ramp('#03070B', '#06111A', '#0A1820', '#0F2128', '#152A2E'),
                    rim=ramp('#30505E', '#7E9CB0'), glow=(100, 34, 72))

SKIN_K = ramp('#0A121A', '#1C2030', '#3C2C34', '#6A4440', '#9C6650', '#C88E60', '#EBC285')
SKIN_B = ramp('#0B0E18', '#1C1C2C', '#3E2C3A', '#6E4442', '#A2664E', '#D2925E', '#F2C47E')


def finish(sc, look_d, ramps, frame, expr, feat_cols, extra=None, creases=True):
    sc.composite()
    look = Look(rim_cols=look_d['rim'])
    img, info = shade_portrait(sc, look, ramps)
    bg = background(look_d['bg'], look_d.get('glow'))
    out = bg.copy()
    occ = info['occ']
    out[occ] = img[occ]
    skin_mask = np.zeros((H, W), bool)
    if 'skin' in sc.mat_names:
        skin_mask = (sc.mat == sc.mat_names.index('skin')) & (sc.grp == sc.order.index('head'))
    draw_features(out, sc, info, expr, feat_cols, skin_mask, extra, creases=creases)
    return out, info


def add_shoulders(sc, cx=54.0, yaw=20.0, mat='coat', width=1.0, drop=0.0, z=0.0):
    """Sloped coat shoulders + chest in a body frame turned a little less than the head."""
    bf = (np.array([cx, 0.0, z]), rotm(yaw, 0.0, 0.0), 1.0)
    B = dict(frame=bf, group='body', mat=mat)
    sc.ellipsoid((0, 108 + drop, -6), (33 * width, 30, 18), k=0, **B)                     # chest / torso
    for sx in (-1, 1):
        sc.ellipsoid((sx * 26 * width, 94 + drop, -7), (16 * width, 9.5, 13), k=7, **B)    # shoulder caps
        sc.ellipsoid((sx * 35 * width, 114 + drop, -6), (10.5, 26, 12), k=6, **B)          # upper arms
    sc.ellipsoid((0, 92 + drop, -16), (28 * width, 12, 10), k=6, **B)                     # upper back
    return bf


def cloth_folds(img, sc, info, mat_name, ramps, frame, lines):
    """Darker crease lines on cloth: lines = [(x0, y0, x1, y1), ...] in body-frame coords (approx)."""
    if mat_name not in sc.mat_names:
        return
    mid = sc.mat_names.index(mat_name)
    R = np.stack(ramps[mat_name])
    o = frame[0]
    for x0, y0, x1, y1 in lines:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, n):
            x = int(round(o[0] + x0 + (x1 - x0) * t))
            y = int(round(y0 + (y1 - y0) * t))
            if 0 <= x < W and 0 <= y < H and sc.mat[y, x] == mid:
                img[y, x] = R[max(0, info['tone'][y, x] - 1)]


def fur_texture(img, sc, mat_name, ramps, info, period=(5, 3)):
    """Breaks large fur areas with short darker strokes (deterministic hash pattern)."""
    if mat_name not in sc.mat_names:
        return
    m = sc.mat == sc.mat_names.index(mat_name)
    yy, xx = np.mgrid[0:H, 0:W]
    # short 2 px vertical strokes on a scattered lattice read as fur pile rather than as dots
    pat = (((xx * 7 + (yy // 2) * 13) % 11) == 0) | (((xx * 5 + ((yy + 1) // 2) * 3) % 17) == 0)
    sel = m & pat & (info['tone'] >= 2)
    R = np.stack(ramps[mat_name])
    t = np.clip(info['tone'] - 1, 0, len(R) - 1)
    img[sel] = R[t][sel]


# ----------------------------------------------------------------------------------- ALEXEI
def alexei_portrait(expr):
    sc = Scene()
    jd = 2.4 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 50.0, 0.0), yaw=28.0, pitch=4.0, roll=-2.0, scale=1.2)
    add_head(sc, fr, dict(jaw_w=14.4, nose_len=1.0, chin=1.05, jaw_drop=jd, lip_w=0.95))
    H_ = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -22.0, -2.0), (20.6, 16.0, 21.6), mat='fur', k=0, **H_)            # crown
    sc.ellipsoid((0, -30.0, -2.0), (15.0, 8.0, 16.0), mat='fur', k=6, **H_)             # rounded top
    sc.ellipsoid((0, -14.6, 11.2), (20.4, 7.4, 8.0), mat='fur2', k=1.0, **H_)           # turned-up front flap
    for sx in (-1, 1):
        sc.ellipsoid((sx * 17.8, 6.0, -0.5), (4.4, 16.5, 9.6), mat='fur2', k=2.5, **H_)  # ear flaps
    sc.ellipsoid((0, 0.0, -16.0), (18.5, 15.0, 8.0), mat='fur2', k=3, **H_)            # back flap
    bf = add_shoulders(sc, cx=56.0, yaw=20.0, mat='coat', width=0.92, drop=4.0)
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.5, 86, 1), (10.5, 9.5, 9.5), mat='coat', group='collar', frame=bf, k=3)
    sc.ellipsoid((0, 83, -9), (15, 10, 7), mat='coat', group='collar', frame=bf, k=3)
    sc.ellipsoid((2, 110, 18.5), (4.2, 28, 1.2), R=rotm(0, 0, -36), mat='strap', group='strap', frame=bf)
    ramps = {
        'skin': SKIN_K,
        'fur': ramp('#07090C', '#13161A', '#232425', '#383530', '#544A3F', '#73624E', '#977E62'),
        'fur2': ramp('#08090C', '#15181B', '#272829', '#403C36', '#5E5446', '#816E56', '#A68C6A'),
        'coat': ramp('#040A0B', '#091414', '#10211D', '#193026', '#264232', '#3C583C', '#5C7246'),
        'strap': ramp('#070606', '#140E10', '#241816', '#38261C', '#523826', '#704E32', '#906842'),
    }

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        Lc = local_coords(sc, fr)
        # two-day stubble: sparse darker pixels on the lit lower jaw / upper lip
        jaw = skin_mask & (((Lc[..., 1] > 15.5) & (Lc[..., 1] < 24)) | ((Lc[..., 1] > 10.5) & (Lc[..., 1] < 11.8)))
        jaw &= (info['val'] > 0.30) & dither_mask(level=0.13)
        R = np.stack(SKIN_K)
        img[jaw] = R[np.clip(info['tone'] - 1, 0, 6)][jaw]
        fur_texture(img, sc, 'fur', ramps, info)
        fur_texture(img, sc, 'fur2', ramps, info)
        # padded coat: horizontal quilting seams + shoulder creases
        cm = sc.mat == sc.mat_names.index('coat')
        Rc = np.stack(ramps['coat'])
        seam = cm & (np.round(sc.Y).astype(int) % 7 == 3) & (sc.Y > 92) & (info['tone'] >= 2)
        img[seam] = Rc[np.clip(info['tone'] - 1, 0, 6)][seam]
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-24, 96, -20, 112), (22, 95, 18, 112), (-14, 104, -12, 112)])

    out, info = finish(sc, LOOK_KARSK, ramps, fr, expr, feat(KARSK_FEAT), extra)
    return out


# ----------------------------------------------------------------------------------- KONRAD
def konrad_portrait(expr):
    sc = Scene()
    jd = 2.4 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 53.0, 0.0), yaw=27.0, pitch=0.0, roll=-1.5, scale=1.2)
    add_head(sc, fr, dict(jaw_w=14.6, crown_w=19.0, nose_len=1.0, nose_w=0.95, chin=1.02, jaw_drop=jd,
                          lip_w=0.94, lip_l=0.85, face_h=0.93))
    # short hair visible below the hat at the temple / back
    sc.ellipsoid((0, -4.0, -4.0), (18.9, 18.5, 20.6), mat='hair', group='hair', frame=fr,
                 clip=lambda L: (L[..., 2] < 2.0) & (L[..., 1] > -16.0) & (L[..., 1] < 9.0))
    Hh = dict(frame=fr, group='hat')
    sc.ellipsoid((0, -21.5, -1.0), (17.8, 7.5, 19.0), mat='hat', k=0, **Hh)              # lower crown
    sc.ellipsoid((0, -27.5, -1.5), (14.6, 6.5, 16.2), mat='hat', k=4, **Hh)              # tapered upper crown
    for sx in (-1, 1):                                                                    # centre crease lobes
        sc.ellipsoid((sx * 5.6, -32.0, -2.0), (6.6, 3.0, 13.0), mat='hat', k=2.5, **Hh)
    sc.ellipsoid((0, -16.8, -1.0), (18.2, 2.4, 19.6), mat='band', k=0.4, **Hh)           # ribbon band
    sc.ellipsoid((0, -14.8, 2.0), (27.0, 2.2, 28.5), R=rotm(0, -15, 0), mat='brim', k=0, **Hh)  # brim, snapped down
    bf = add_shoulders(sc, cx=57.0, yaw=20.0, mat='coat', width=0.92, drop=5.0)
    S = dict(frame=bf, group='scarf')
    sc.ellipsoid((0, 87, 2), (14.5, 6.5, 12.5), mat='scarf', k=0, **S)
    sc.ellipsoid((-5, 93, 10), (7.5, 6.0, 5.5), mat='scarf', k=3, **S)
    sc.ellipsoid((3, 106, 13.5), (4.6, 14.0, 2.6), R=rotm(0, 0, 6), mat='scarf2', k=1.5, **S)
    L_ = dict(frame=bf, group='lapel')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 11.5, 104, 15.5), (5.0, 17, 1.4), R=rotm(0, 0, sx * -20), mat='coat2', k=0, **L_)
    sc.ellipsoid((-17, 112, 18.5), (2.6, 24, 1.0), R=rotm(0, 0, -30), mat='strap', group='strap', frame=bf)
    ramps = {
        'skin': SKIN_B,
        'hair': ramp('#08070A', '#16121A', '#2A2226', '#463830', '#6A5440', '#8E7252', '#B09066'),
        'hat': ramp('#060609', '#100F14', '#1C1A20', '#2C272C', '#433A3C', '#5E504C', '#7C6A5E'),
        'brim': ramp('#050508', '#0E0D12', '#18161C', '#262126', '#3A3236', '#544848', '#726258'),
        'band': ramp('#040406', '#09080C', '#100E14', '#18151C', '#231E26', '#2E2830', '#3A323A'),
        'scarf2': ramp('#0C0A0C', '#1C161A', '#362A28', '#584636', '#7E6848', '#A48858', '#C6A66C'),
        'coat': ramp('#04060E', '#080D1A', '#0F1628', '#18223C', '#243250', '#384662', '#565E72'),
        'coat2': ramp('#04060E', '#080D1A', '#0E1526', '#162036', '#22304A', '#34425C', '#50586C'),
        'scarf': ramp('#0C0A0C', '#1E181C', '#3A2E2C', '#5E4C3C', '#86704E', '#AE925E', '#D0B074'),
        'strap': ramp('#060506', '#110C0E', '#1E1516', '#2E201C', '#423024', '#5A422E', '#76583A'),
    }

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        cloth_folds(img, sc, info, 'coat', ramps, bf, [(-26, 100, -22, 112), (24, 99, 20, 112)])
        # two coat buttons on the lapel edge (1 px detail)
        for (bx, by) in ((61, 106), (63, 111)):
            if sc.mat[by, bx] >= 0:
                img[by, bx] = hexc('#0A0E1A')

    out, info = finish(sc, LOOK_BERLIN, ramps, fr, expr, feat(BERLIN_FEAT), extra)
    return out


# ----------------------------------------------------------------------------------- IRINA
def irina_portrait(expr):
    sc = Scene()
    jd = 2.0 if expr == 'surprised' else 0.0
    fr = head_frame((53.0, 52.0, 0.0), yaw=20.0, pitch=4.0, roll=-3.0, scale=1.16)
    add_head(sc, fr, dict(jaw_w=13.0, crown_w=18.4, nose_len=0.88, nose_w=0.85, chin=0.88, jaw_drop=jd,
                          lip_w=1.0, lip_l=1.25, face_h=0.94))

    def face_hole(L):
        x, y, z = L[..., 0], L[..., 1], L[..., 2]
        opening = (z > 0.0) & (y > -11.5 + 0.014 * x * x) & (np.abs(x) < 16.0 - 0.004 * (y - 4) ** 2) & (y < 24.0)
        return ~opening
    Sc = dict(frame=fr, group='scarf')
    sc.ellipsoid((0, -7.0, -1.5), (20.6, 23.0, 22.4), mat='scarf', k=0, clip=face_hole, inner=True, **Sc)
    sc.ellipsoid((0, 12.0, -5.0), (21.5, 17.0, 17.5), mat='scarf', k=5, clip=face_hole, inner=True, **Sc)
    sc.ellipsoid((0, -12.2, 12.8), (15.0, 2.2, 6.4), mat='scarf2', k=0.8,
                 clip=lambda L: L[..., 2] > 5.0, **Sc)                                         # folded edge
    K = dict(frame=fr, group='knot')
    sc.ellipsoid((1.5, 26.5, 12.0), (5.2, 3.8, 4.2), mat='scarf2', k=0, **K)                   # knot
    sc.ellipsoid((-2.5, 32.0, 12.5), (2.6, 6.0, 2.4), R=rotm(0, 0, -14), mat='scarf2', k=1.2, **K)  # tails
    sc.ellipsoid((5.0, 31.5, 11.5), (2.4, 5.4, 2.2), R=rotm(0, 0, 20), mat='scarf2', k=1.2, **K)
    for hx_ in (-7.0, -2.5, 3.0):                                                                  # stray hair
        sc.ellipsoid((hx_, -10.6, 15.6), (2.2, 1.4, 2.2), mat='hair', group='hair', frame=fr)
    bf = add_shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.86, drop=7.0)
    sc.ellipsoid((0, 91, -1), (14.0, 8.0, 11.0), mat='coat', group='collar', frame=bf)
    ramps = {
        'skin': SKIN_K,
        'scarf': ramp('#0C080C', '#1C0F15', '#331818', '#512620', '#743828', '#965032', '#B46A40'),
        'scarf2': ramp('#0C080C', '#1A0E13', '#2E1616', '#4A221C', '#6A3224', '#8A462C', '#A85E3A'),
        'hair': ramp('#08060A', '#140C10', '#22161A', '#342220', '#4A3228', '#644432', '#80583E'),
        'coat': ramp('#04070C', '#08101A', '#0E1A26', '#172836', '#223846', '#344C56', '#506460'),
    }

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # quilting seams on the jacket + tiny pattern dots on the headscarf
        bm_ = sc.mat == sc.mat_names.index('coat')
        Lb = np.stack([sc.X, sc.Y, sc.z], -1)
        rows = (np.round(Lb[..., 1]).astype(int) % 6 == 0) & bm_
        R = np.stack(ramps['coat'])
        img[rows] = R[np.clip(info['tone'] - 1, 0, 6)][rows]
        sm = sc.mat == sc.mat_names.index('scarf')
        Ls = local_coords(sc, fr)
        Rs = np.stack(ramps['scarf'])
        # drapery folds: soft diagonal creases running from the knot up over the head
        fold = sm & (np.abs(((Ls[..., 1] - 0.55 * np.abs(Ls[..., 0])) % 9.0) - 4.5) < 0.6) & (Ls[..., 1] > -24)
        img[fold] = Rs[np.clip(info['tone'] - 1, 0, 6)][fold]
        yy, xx = np.mgrid[0:H, 0:W]
        dots = sm & ~fold & (((xx + 2 * (yy // 4)) % 5) == 0) & (yy % 4 == 1) & (info['tone'] >= 2)
        img[dots] = Rs[np.clip(info['tone'] + 2, 0, 6)][dots]
        # a pencil tucked into the headscarf above the near ear (dispatcher's habit)
        x, y, _ = project(sc, 'ear')
        for k in range(6):
            px_, py_ = int(round(x + 1 + k)), int(round(y - 9 - k * 0.6))
            if 0 <= px_ < W and 0 <= py_ < H and sc.mat[py_, px_] == sc.mat_names.index('scarf'):
                img[py_, px_] = hexc('#8C6A30') if k < 5 else hexc('#2A2A2E')

    out, info = finish(sc, LOOK_KARSK, ramps, fr, expr, feat(KARSK_FEAT, lip='#B86A58', mouth='#4A1E24'), extra,
                       creases=(expr == 'determined'))
    return out


# ----------------------------------------------------------------------------------- EMIL
def emil_portrait(expr):
    sc = Scene()
    jd = 2.0 if expr == 'surprised' else 0.0
    fr = head_frame((52.0, 52.0, 0.0), yaw=26.0, pitch=8.0, roll=-2.0, scale=1.18)
    add_head(sc, fr, dict(jaw_w=14.8, crown_w=18.6, nose_len=1.15, nose_w=1.15, chin=1.1, jaw_drop=jd,
                          lip_w=1.0, lip_l=0.9))
    E = dict(frame=fr, group='head')
    for sx in (-1, 1):
        sc.ellipsoid((sx * 10.0, 12.0, 8.0), (5.0, 5.0, 5.5), mat='skin', k=3, **E)        # jowls
    # grey fringe (bald crown)
    sc.ellipsoid((0, -4.0, -2.0), (19.6, 19.0, 21.6), mat='hair', group='hair', frame=fr,
                 clip=lambda L: (L[..., 1] > -11.0 + 0.25 * L[..., 2]) & (L[..., 2] < 7.0) & (L[..., 1] < 9.0))
    sc.ellipsoid((0, 10.6, 18.6), (6.4, 2.2, 3.0), mat='hair', group='stache', frame=fr)         # moustache
    bf = add_shoulders(sc, cx=56.0, yaw=18.0, mat='coat', width=0.92, drop=6.0)
    sc.ellipsoid((0, 104, 9), (13.0, 20, 7.0), mat='cardigan', group='cardigan', frame=bf)
    sc.ellipsoid((0, 90, 9), (7.5, 4.2, 6.0), mat='shirt', group='shirt', frame=bf)
    sc.ellipsoid((0.5, 99, 15.6), (1.9, 9.0, 1.0), mat='tie', group='tie', frame=bf)
    for sx in (-1, 1):
        sc.ellipsoid((sx * 15.0, 104, 14.5), (4.6, 19, 1.3), R=rotm(0, 0, sx * -16), mat='coat2', group='lap2',
                     frame=bf)
    ramps = {
        'skin': SKIN_B,
        'hair': ramp('#0E1014', '#22262C', '#3E4248', '#62666A', '#8C8E8C', '#B4B4AC', '#D4D2C6'),
        'coat': ramp('#06080A', '#0E1216', '#181E22', '#262E30', '#3A4240', '#565A52', '#787664'),
        'coat2': ramp('#06080A', '#0E1216', '#161C20', '#222A2C', '#343C3A', '#4E544C', '#6E6E5E'),
        'cardigan': ramp('#0A0808', '#18120E', '#2A2016', '#40301E', '#5A4428', '#785C34', '#987642'),
        'shirt': ramp('#14161C', '#2A2C34', '#4A4C52', '#76766E', '#A4A090', '#C8C2AA', '#E0D8BE'),
        'tie': ramp('#08040A', '#140A10', '#221016', '#34161C', '#4A2024', '#622C2C', '#7A3A36'),
    }

    def extra(img, sc, info, expr, cols, skin_mask, lit_at):
        # round spectacles over both eyes (frame ring, glint on the key side), bridge and temple arm
        frame_c = hexc('#16141C')
        glint = hexc('#E6E2D2')
        glint2 = hexc('#9AA8B0')
        for side, rx in (('n', 4), ('f', 3)):
            x, y, _ = project(sc, 'eye_' + side)
            cx, cy = int(round(x)), int(round(y)) + 0
            for a in np.linspace(0, 2 * np.pi, 48, endpoint=False):
                px_ = int(round(cx + 0.5 + math.cos(a) * (rx + 0.6)))
                py_ = int(round(cy + 0.5 + math.sin(a) * 3.6))
                if 0 <= px_ < W and 0 <= py_ < H:
                    img[py_, px_] = frame_c
            if lit_at(cx + 2, cy - 1):
                img[cy - 2, cx + rx - 2] = glint
                img[cy - 1, cx + rx - 1] = glint2
            else:
                img[cy - 2, cx + rx - 2] = glint2
        xn, yn, _ = project(sc, 'eye_n')
        xf, yf, _ = project(sc, 'eye_f')
        for t in np.linspace(0, 1, 8):
            bx = int(round(xn + 4.6 + (xf - 3.6 - xn - 4.6) * t))
            by = int(round(yn - 1 + (yf - yn) * t))
            img[by, bx] = frame_c
        xe, ye, _ = project(sc, 'ear')
        for t in np.linspace(0, 1, 14):
            bx = int(round(xn - 4.6 + (xe + 2 - xn + 4.6) * t))
            by = int(round(yn - 1 + (ye - 2 - yn + 1) * t))
            if 0 <= bx < W and 0 <= by < H and sc.mat[by, bx] == sc.mat_names.index('skin'):
                img[by, bx] = frame_c
        # age lines: crow's feet + nasolabial fold
        Rk = np.stack(SKIN_B)
        x, y, _ = project(sc, 'eye_n')
        stamp(img, ['c.', '.c', 'c.'], x - 6, y, {'c': Rk[2]}, mask=skin_mask)
        x, y, _ = project(sc, 'nostril')
        stamp(img, ['c..', '.c.', '.c.', '..c'], x - 5, y + 1, {'c': Rk[2] if not lit_at(x - 4, y + 2) else Rk[3]},
              mask=skin_mask)

    out, info = finish(sc, LOOK_ARCHIVE, ramps, fr, expr, feat(BERLIN_FEAT, brow='#8C8C86', brow2='#B4B2A8'),
                       extra)
    return out


PORTRAITS = {'alexei': alexei_portrait, 'konrad': konrad_portrait, 'irina': irina_portrait,
             'emil': emil_portrait}


def main(ids=None):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, '..', '..'))
    out_dir = os.path.join(root, 'assets', 'characters')
    prev = os.path.join(out_dir, '_preview')
    os.makedirs(prev, exist_ok=True)
    ids = ids if ids else list(PORTRAITS)
    sheet_all = []
    for cid in ids:
        fn = PORTRAITS[cid]
        frames = [fn(e) for e in EXPRESSIONS]
        strip = np.concatenate(frames, 1)
        d = os.path.join(out_dir, cid)
        os.makedirs(d, exist_ok=True)
        Image.fromarray(strip, 'RGBA').save(os.path.join(d, 'portrait.png'))
        with open(os.path.join(d, 'portrait.json'), 'w', encoding='utf-8') as f:
            json.dump({'size': [W, H], 'expressions': EXPRESSIONS}, f, indent=1)
        sheet_all.append(strip)
        Image.fromarray(strip, 'RGBA').resize((strip.shape[1] * 3, strip.shape[0] * 3), Image.NEAREST).save(
            os.path.join(prev, f'{cid}_portraits_3x.png'))
        print(f'portrait {cid}: {len(frames)} expressions')
    if len(sheet_all) > 1:
        allp = np.concatenate(sheet_all, 0)
        Image.fromarray(allp, 'RGBA').resize((allp.shape[1] * 2, allp.shape[0] * 2), Image.NEAREST).save(
            os.path.join(prev, 'portraits_all_2x.png'))


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
