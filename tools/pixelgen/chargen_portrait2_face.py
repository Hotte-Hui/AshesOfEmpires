"""chargen_portrait2_face -- hand-designed facial features for the dialogue busts.

Features are placed at landmarks projected from the 3D head and drawn in two layers:
  * relative marks on the TONE map (skin-relative: '-' one tone darker, '=' two, '#' three, '+' lighter),
    so lids, creases, nostrils and lip lines follow the local light automatically;
  * absolute colour marks after colourisation (lash line, sclera, iris, pupil, catch-light, teeth).
Eye stamps exist for the near (character's right, image left) and far eye in every expression, open and
closed; brows and mouths are parametric pixel strokes so every face shape gets clean, stepped lines.
"""
from __future__ import annotations

import numpy as np

# ------------------------------------------------------------------------------------------- eyes
# Alphabet: '.' keep | '-','=','#' darker skin tone (1/2/3 steps) | '+' lighter skin tone
#           'K' lash line | 'k' soft lash | 'W' sclera | 'w' sclera in shade | 'I' iris | 'i' iris dark
#           'P' pupil | 'H' catch-light
# Anchor = (col, row) of the eye centre landmark inside the stamp.
EYES = {
    # ---------------------------------------------------------------- near eye (image left), anchor (4, 2)
    ('near', 'neutral'): ("""
        ..=====..
        .KKKKKKK.
        KKWIPHWk.
        .-wIIiW-.
        ..-===-..
    """, (4, 2)),
    ('near', 'concerned'): ("""
        ....===..
        ..KKKKKKk
        .KWWIPHW.
        .-wWIIi-.
        ..-===-..
    """, (4, 2)),
    ('near', 'determined'): ("""
        .=======.
        .KKKKKKKK
        KKWIPIWk.
        ..-===-..
        .........
    """, (4, 2)),
    ('near', 'surprised'): ("""
        ..=====..
        .KKKKKKK.
        KWWIIIWk.
        .WWIPHW-.
        .-wIIiw-.
        ..-===-..
    """, (4, 2)),
    ('near', 'closed'): ("""
        ..=====..
        .........
        .-------.
        .KKKKKKk.
        ...---...
    """, (4, 2)),
    # ---------------------------------------------------------------- far eye (image right), anchor (3, 2)
    ('far', 'neutral'): ("""
        .====.
        KKKKKK
        KWIPHk
        .-IIi-
        ..==-.
    """, (3, 2)),
    ('far', 'concerned'): ("""
        ..===.
        .KKKKK
        KWIPHW
        .-IIi-
        ..==-.
    """, (3, 2)),
    ('far', 'determined'): ("""
        ======
        KKKKKK
        KWIPIk
        .-==-.
        ......
    """, (3, 2)),
    ('far', 'surprised'): ("""
        .====.
        KKKKKK
        WWIIIk
        WWIPHW
        .-IIi-
        ..==-.
    """, (3, 2)),
    ('far', 'closed'): ("""
        .====.
        ......
        .-----
        .KKKKK
        ..--..
    """, (3, 2)),
}


def parse(s):
    rows = [r.strip() for r in s.strip('\n').split('\n')]
    return [r for r in rows if r]


# ------------------------------------------------------------------------------------------- canvas
class Canvas:
    """Holds the tone map (relative marks) and absolute colour overrides for one frame."""

    def __init__(self, tone, mat, skin_ids, rgb=None):
        self.tone = tone
        self.mat = mat
        self.skin = np.isin(mat, list(skin_ids))
        self.abs = {}            # (x, y) -> colour key
        self.locked = np.zeros(tone.shape, bool)   # pixels drawn by features (cleanup must not touch)

    def rel(self, x, y, delta, allow=None):
        h, w = self.tone.shape
        if 0 <= x < w and 0 <= y < h:
            ok = self.skin[y, x] if allow is None else allow[y, x]
            if ok and self.tone[y, x] >= 0:
                self.tone[y, x] = max(0, self.tone[y, x] + delta)
                self.locked[y, x] = True

    def put(self, x, y, key, allow=None):
        h, w = self.tone.shape
        if 0 <= x < w and 0 <= y < h:
            ok = self.skin[y, x] if allow is None else allow[y, x]
            if ok:
                self.abs[(x, y)] = key
                self.locked[y, x] = True


REL = {'-': -1, '=': -2, '#': -3, '+': 1}


def draw_stamp(cv: Canvas, rows, ax, ay, x, y, mirror=False):
    if isinstance(rows, str):
        rows = parse(rows)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in '. ':
                continue
            ii = (len(row) - 1 - i) if mirror else i
            px = int(x) - (len(row) - 1 - ax if mirror else ax) + ii
            py = int(y) - ay + j
            if ch in REL:
                cv.rel(px, py, REL[ch])
            else:
                cv.put(px, py, ch)


def eye(cv: Canvas, side, expr, x, y, closed=False, table=None):
    t = table or EYES
    key = (side, 'closed' if closed else expr)
    if key not in t:
        key = (side, 'neutral' if not closed else 'closed')
    rows, (ax, ay) = t[key]
    draw_stamp(cv, rows, ax, ay, x, y)


# ------------------------------------------------------------------------------------------- brows
def brow(cv: Canvas, x0, y0, length, rise=0.0, arch=1.0, thick=(2, 2, 1), inner_left=False, key='b',
         lift_inner=0.0, lift_outer=0.0, tone_rel=None):
    """Parametric brow: columns from the inner end to the outer end.  `rise` = total y change inner ->
    outer (negative = outer end higher), `arch` = upward bow in px, thick = thickness at inner/mid/outer.
    inner_left: True when the inner end (towards the nose) is at the left of the stroke."""
    n = max(2, int(round(length)))
    for i in range(n):
        u = i / (n - 1)
        yc = y0 + rise * u - arch * 4 * u * (1 - u) - lift_inner * (1 - u) ** 2 - lift_outer * u * u
        t = thick[0] + (thick[1] - thick[0]) * min(1, u * 2) if u < 0.5 else \
            thick[1] + (thick[2] - thick[1]) * (u - 0.5) * 2
        t = max(1, int(round(t)))
        x = int(x0) + (i if inner_left else -i)
        top = int(np.floor(yc + 0.5))
        for k in range(t):
            if tone_rel is not None:
                cv.rel(x, top + k, tone_rel)
            else:
                cv.put(x, top + k, key if k < t - 1 or t == 1 else key.upper())


# ------------------------------------------------------------------------------------------- mouth
def mouth(cv: Canvas, xl, xr, y, state, expr, corner_drop=0.0, smile=0.0, open_h=0, teeth=True,
          lip_lo_rel=1, center=None, upper_rel=-1):
    """Closed / talking mouth between the near corner xl and far corner xr (image x), lip line at y.
    state: 'rest' | 'half' | 'open'.  open_h: pixel height of the opening for half/open states."""
    xl, xr = int(round(xl)), int(round(xr))
    if center is None:
        center = (xl + xr) / 2.0
    n = xr - xl + 1
    ys = []
    for i in range(n):
        x = xl + i
        u = (x - xl) / max(1, n - 1)
        # corners drop for concern / determination, slight centre peak (cupid's bow) at the centre
        edge = min(u, 1 - u)
        yy = y + corner_drop * (1 - min(1, edge * 3.2)) - smile * (1 - min(1, edge * 3.2))
        ys.append(int(round(yy)))
    if state == 'rest':
        for i in range(n):
            x = xl + i
            yy = ys[i]
            is_corner = i == 0 or i == n - 1
            cv.put(x, yy, 'M' if not is_corner else 'm')
            # upper lip (shaded, it faces down) and lower lip (catches light)
            if not is_corner:
                cv.rel(x, yy - 1, upper_rel)
                if lip_lo_rel:
                    cv.rel(x, yy + 1, lip_lo_rel if 0 < i < n - 1 else 0)
        # shadow under the lower lip (mentolabial groove), shorter than the mouth
        for i in range(2, n - 2):
            cv.rel(xl + i, ys[i] + 3, -1)
        return
    oh = max(1, open_h)
    for i in range(n):
        x = xl + i
        yy = ys[i]
        is_corner = i == 0 or i == n - 1
        if is_corner:
            cv.put(x, yy, 'm')
            continue
        # shape: deepest in the middle, tapering to the corners
        u = i / (n - 1)
        depth = oh if 0.2 <= u <= 0.8 else max(1, oh - 1)
        cv.put(x, yy, 'M')
        for k in range(1, depth + 1):
            cv.put(x, yy + k, 'O' if k < depth else 'M')
        if teeth and oh >= 2 and 0.15 < u < 0.85:
            cv.put(x, yy + 1 if oh >= 2 else yy, 'T')
        if oh >= 3 and 0.3 < u < 0.7:
            cv.put(x, yy + depth - 1, 'Q')
        cv.rel(x, yy - 1, upper_rel)
        cv.rel(x, yy + depth + 1, 1)
    for i in range(2, n - 2):
        cv.rel(xl + i, ys[i] + oh + 3, -1)
