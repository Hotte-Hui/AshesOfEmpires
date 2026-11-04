"""env_karsk_life -- round-2 detail and exploration set dressing for scene A1 'Verladebahnhof Karsk'.

Adds (all world coordinates, playfield parallax 1):
  * surfaces: icicles on every eave, rust streaks, snow drifts against walls, coal heap, frozen puddles,
    footprint trails (boots, child, cat, crow), sled runner tracks
  * exploration objects (TECHNICAL_ARCHITECTURE §12.2): PA loudspeaker pole + wire (exp_loudspeaker, crows'
    perch), snowman with a tin-can ushanka (exp_snowman), tin box in a gap between the crates (exp_stash,
    hidden), newspaper on the bench (exp_newspaper), bookshelf behind the office window (exp_kontora_shelf),
    cache under the signal-box stairs (exp_stairs_under, hidden), chalk marks at the far end of the C-17
    wagon (exp_wagon_chalk), dwarf shunting signal
  * insignia placements (§12.4) via env_karsk_emblems: every painter that shows an emblem takes `hist`.
Deterministic: seeds are fixed integers; no hash().
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import math

import numpy as np

import pg
from env_karsk_lib import (Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, bayer, value_noise, text, text_width,
                           cyl_normal, flat_normal, snow_top, col_key)
import env_karsk_emblems as EMB

GROUND_Y = 250
CLEAR = np.zeros(4, np.uint8)
SNOW_KEYS = set(int(k) for k in col_key(np.stack(SN)[:, :3]))


def _is(L, x, y, ramp):
    if not (0 <= x < L.w and 0 <= y < L.h) or L.c[y, x, 3] == 0:
        return False
    k = int(col_key(L.c[y, x, :3]))
    return k in set(int(v) for v in col_key(np.stack(ramp)[:, :3]))


# =========================================================================== surfaces
def icicles(L, x0, x1, y, seed=0, density=0.28, maxlen=5, big=0.25):
    """Icicles hanging from row y (the underside of an eave).  Clusters, not a comb: lengths follow a
    smooth noise so long icicles group where the meltwater runs; tips are pale, a cold highlight right."""
    rng = np.random.default_rng(seed)
    n = value_noise(max(2, x1 - x0), 1, 5, seed=seed + 7, octaves=2)[0]
    x = x0
    while x < x1:
        v = n[x - x0]
        if rng.random() < density * (0.4 + v):
            ln = 1 + int(round((maxlen - 1) * v ** 1.6 * rng.uniform(0.6, 1.0)))
            for k in range(ln):
                c = SN[2] if k < ln - 1 else SN[3]
                L.px(x, y + k, c, 0.7)
            if ln >= 3:
                L.px(x, y, SN[3], 0.72)
                if rng.random() < big and x + 1 < x1:     # thicker root
                    L.px(x + 1, y, SN[1], 0.7)
                    L.px(x + 1, y + 1, SN[2], 0.7)
                L.px(x, y + ln - 2, SN[4], 0.75)           # glint
            x += 2 if ln >= 3 else 1
        x += 1


def rust_streak(L, x, y, length, seed=0, strong=False):
    """Thin rust run-off below a bolt / hinge / edge (fades and breaks up downward)."""
    rng = np.random.default_rng(seed)
    for k in range(length):
        t = k / max(1, length - 1)
        if rng.random() < 0.15 + 0.5 * t:
            continue
        c = RU[2] if (strong and t < 0.4) else (RU[1] if t < 0.7 else RU[0])
        L.px(x, y + k, c)
        if strong and k < 3:
            L.px(x + 1, y + k, RU[1])


def drift_wedge(L, x0, x1, y_base, h, rise_left=True, seed=0):
    """Snow drift piled against a wall: a smooth wedge, highest at the wall side."""
    w = x1 - x0
    rng = np.random.default_rng(seed)
    for i, x in enumerate(range(x0, x1)):
        t = i / max(1, w - 1)
        if not rise_left:
            t = 1 - t
        hh = int(round(h * (1 - t) ** 1.7 + rng.uniform(-0.4, 0.4)))
        for k in range(max(0, hh)):
            yy = y_base - 1 - k
            c = SN[2] if k < hh - 1 else SN[3]
            if k == 0:
                c = SN[1]
            L.px(x, yy, c, 0.5 + 0.03 * k)
            L.nrm[yy, x] = (0.0, 0.7, 0.7)


def coal_heap(L, x0, w, y_base, h, seed=0, shovel=True):
    """Coal heap for the cabin stove: dark lumps with cold sheen, a dusting of fresh snow, a shovel."""
    rng = np.random.default_rng(seed)
    cx = x0 + w / 2
    for x in range(x0, x0 + w):
        t = abs((x + 0.5 - cx) / (w / 2))
        hh = int(round(h * (1 - t ** 1.8)))
        for k in range(hh):
            yy = y_base - 1 - k
            c = NI[1] if (x + yy) % 3 else NI[2]
            if rng.random() < 0.18:
                c = ST[1]
            L.px(x, yy, c, 0.45 + k * 0.03)
        if hh > 0:
            top = y_base - hh
            if rng.random() < 0.55:
                L.px(x, top, SN[1], 0.6)
            if rng.random() < 0.15:
                L.px(x, top - 1, SN[2], 0.6)
    for _ in range(int(w * h * 0.12)):
        x = int(x0 + rng.integers(0, w))
        yy = int(y_base - 1 - rng.integers(0, max(1, h - 1)))
        if L.c[yy, x, 3] and _is(L, x, yy, [NI[1], NI[2]]):
            L.px(x + 1 if x + 1 < x0 + w else x, yy, ST[2])
    if shovel:  # shovel stuck in at an angle: blade in the heap, handle up-right
        sx, sy = int(cx + 2), y_base - h + 1
        L.rect(sx - 1, sy, 3, 3, ST[2], hgt=0.7)
        L.hline(sx - 1, sy, 3, ST[4])
        L.line(sx, sy - 1, sx + 5, sy - 12, WO[2])
        L.line(sx + 1, sy - 1, sx + 6, sy - 12, WO[1])
        L.hline(sx + 4, sy - 13, 4, WO[3])


def footprints(L, pts, kind='boot', spacing=None, only=('snow', 'cinder'), seed=0):
    """Stamp a trail along the polyline pts.  Prints only land on snow (and on the cinder path for 'boot').
    kinds: boot (2x1, 2 px apart), child (1x1), cat (paired dots), bird (3-px arrow)."""
    spacing = spacing or {'boot': 6, 'child': 4, 'cat': 3, 'bird': 4}[kind]
    path = pg.bezier(pts, n=max(8, int(sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:])) / 1.0)))
    acc, side = 0.0, 1
    last = path[0]
    for p in path[1:]:
        acc += math.dist(last, p)
        last = p
        if acc < spacing:
            continue
        acc = 0.0
        side = -side
        x, y = int(round(p[0])), int(round(p[1] + side * (0.6 if kind in ('boot', 'child') else 0.4)))
        snow_here = L.c[y, x, 3] and int(col_key(L.c[y, x, :3])) in SNOW_KEYS
        if not snow_here and not (kind == 'boot' and 'cinder' in only and _is(L, x, y, [NI[3], ST[0]])):
            continue
        dark = SN[0] if snow_here else NI[2]
        if kind == 'boot':
            L.px(x, y, dark)
            L.px(x + 1, y, dark)
            if snow_here:
                L.px(x + 1, y - 1, SN[1]) if _is(L, x + 1, y - 1, SN) else None
        elif kind == 'child':
            L.px(x, y, dark)
        elif kind == 'cat':
            L.px(x, y, dark)
            L.px(x + 2, y + (1 if side > 0 else 0), dark)
        elif kind == 'bird':
            L.px(x, y, dark)
            L.px(x - 1, y - 1, dark)
            L.px(x - 1, y + 1, dark)


def ice_patch(L, cx, cy, rx, ry, seed=0):
    """Frozen puddle: pale, glassy, with white cracks and one specular point (cold sky)."""
    rng = np.random.default_rng(seed)
    m, mx, my = L.ellipse_mask(cx, cy, rx, ry)
    hh, ww = m.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    t = 1 - yy / max(1, hh - 1)
    ladder = [TE[2], TE[3], SK[0], SK[1]]
    T = t * 0.9 * (len(ladder) - 1)
    idx = np.clip(np.floor(T + (T % 1 > bayer(ww, hh, mx, my))), 0, len(ladder) - 1).astype(int)
    L._put(m, mx, my, np.stack(ladder)[idx], hgt=0.06)
    for _ in range(3):        # cracks
        x, y = cx + rng.uniform(-rx * 0.6, rx * 0.6), cy + rng.uniform(-ry * 0.5, ry * 0.5)
        ang = rng.uniform(0, math.pi)
        for k in range(int(rx * 0.8)):
            px_, py_ = int(round(x + math.cos(ang) * k)), int(round(y + math.sin(ang) * k * 0.35))
            mm = (0 <= py_ - my < hh) and (0 <= px_ - mx < ww) and m[py_ - my, px_ - mx]
            if mm:
                L.px(px_, py_, SN[2])
    L.px(int(cx + rx * 0.35), int(cy - ry * 0.3), SN[4])
    L.px(int(cx + rx * 0.35) + 1, int(cy - ry * 0.3), SN[3])
    for x in range(mx, mx + ww):              # frozen rim
        col = m[:, x - mx]
        if col.any():
            L.px(x, my + int(np.nonzero(col)[0].max()) + 1, SN[1])


def sled_tracks(L, x0, x1, y, seed=0):
    """Two parallel runner lines in the slush (sled pulled along the platform)."""
    for x in range(x0, x1):
        wob = int(round(math.sin((x + seed) / 23.0) * 1.2))
        for dy in (0, 3):
            yy = y + wob + dy
            if L.c[yy, x, 3] and (int(col_key(L.c[yy, x, :3])) in SNOW_KEYS or _is(L, x, yy, [ST[1], ST[2]])):
                L.px(x, yy, SN[0] if int(col_key(L.c[yy, x, :3])) in SNOW_KEYS else ST[0])


# =========================================================================== yard_back additions
def pa_wire(L, a, b, sag):
    """PA cable from the cabin horn bracket to the loudspeaker pole; returns the curve points."""
    pts = pg.catenary(a[0], a[1], b[0], b[1], sag)
    q = [(int(round(x)), int(round(y))) for x, y in pts]
    for (x, y) in q:
        L.px(x, y, NI[2])
    # a few snow beads on the cable
    for i, (x, y) in enumerate(q):
        if (x * 7) % 19 == 0:
            L.px(x, y - 1, SN[1])
    return q


def stairs_cache(L, E):
    """Cache under the signal-box stairs (exp_stairs_under, hidden): loose bricks and a leaning board hide
    a hollow with an oilcloth bundle whose red cloth corner flutters in gusts (actor KarskFlutter)."""
    x0, yb = 398, GROUND_Y
    # dark hollow under the bottom treads
    L.rect(x0 + 2, yb - 8, 12, 7, NI[0], hgt=0.1)
    L.hline(x0 + 2, yb - 9, 12, NI[1])
    # oilcloth bundle (teal-black) inside, red cloth corner peeking at the left
    L.rect(x0 + 6, yb - 6, 7, 4, TE[0], hgt=0.25)
    L.hline(x0 + 6, yb - 6, 7, TE[1])
    L.px(x0 + 12, yb - 5, TE[2])
    # two loose bricks in front + a leaning board
    for (bx, by_) in ((x0, yb - 3), (x0 + 5, yb - 3), (x0 + 2, yb - 5)):
        L.rect(bx, by_, 5, 2, RU[1], hgt=0.6)
        L.hline(bx, by_, 5, RU[2])
        L.px(bx + 4, by_ + 1, RU[0])
    L.line(x0 + 13, yb - 1, x0 + 17, yb - 13, WO[1])
    L.line(x0 + 14, yb - 1, x0 + 18, yb - 13, WO[2])
    L.px(x0 + 18, yb - 14, SN[2])
    snow_top(L, x0, yb - 6, 9, [SN[1], SN[2]], depth=1, seed=3)
    E['cache_cloth'] = (x0 + 3, yb - 9)     # top-left of the 7x5 flutter sprite (sits in the hollow mouth)
    E['cache_mark'] = (x0 + 8, yb - 6)


def office_shelf_window(L, x, y, w, h):
    """Freight-office window (exp_kontora_shelf): dark room behind glass, a tall bookshelf with ledgers and
    box files, a cold sky reflection band across the upper panes."""
    L.rect(x - 1, y - 1, w + 2, h + 2, SN[1], hgt=0.6)
    L.vline(x - 1, y - 1, h + 2, TE[1])
    L.rect(x, y, w, h, NI[1], hgt=0.22)
    # shelf carcass
    L.rect(x + 2, y + 2, w - 4, h - 2, WO[0], hgt=0.24)
    spine_cols = [TE[1], WO[1], ST[1], RU[1], TE[0], SA[0]]
    rng = np.random.default_rng(1616)
    for row, sy in enumerate((y + 3, y + 9, y + 15)):
        xx = x + 3
        while xx < x + w - 3:
            bw = int(rng.integers(1, 3))
            bh = int(rng.integers(3, 5))
            c = spine_cols[int(rng.integers(0, len(spine_cols)))]
            if rng.random() < 0.12:      # gap / a leaning file
                xx += 1
                continue
            L.rect(xx, sy + 5 - bh, bw, bh, c, hgt=0.26)
            if bw == 2:
                L.px(xx, sy + 5 - bh + 1, ST[2])     # label
            xx += bw
        L.hline(x + 2, sy + 5, w - 4, WO[1], 0.27)    # shelf board
    # cold reflection: diagonal band upper right
    for k in range(min(w, h) // 2 + 3):
        xx = x + w - 2 - k
        yy = y + 1 + k // 2
        if x <= xx < x + w and y <= yy < y + h:
            L.px(xx, yy, TE[3])
            if xx - 1 >= x:
                L.px(xx - 1, yy, TE[2])
    L.px(x + w - 1, y, SK[1])
    L.vline(x + w // 2, y, h, SN[1], 0.55)
    L.hline(x, y + h // 3, w, SN[1], 0.55)
    L.hline(x - 2, y + h + 1, w + 4, SN[3], 0.75)
    L.hline(x - 2, y + h + 2, w + 4, ST[1], 0.7)


def emblem_patch_rect(x, y, kind, pad=1):
    w, h = EMB.size(kind)
    return (x - pad, y - pad, w + 2 * pad, h + 2 * pad)


# =========================================================================== props
def loudspeaker_pole():
    """Wooden PA pole with two horn loudspeakers on a cross-arm, junction box, enamel plate, insulator for the
    cable to the signal box.  Foot at local (9, 112).  Returns (Layer, foot, wire_anchor_local)."""
    P = Layer(34, 116, 'loudspeaker_pole')
    fx, fy = 15, 113
    top = 6
    # pole (tarred wood, round): 4 px, slight taper
    for y in range(top, fy + 1):
        w = 4 if y > 40 else 3
        P.rect(fx - 1, y, w, 1, WO[1], hgt=0.6)
        P.px(fx - 1, y, WO[0])
        P.px(fx + w - 2, y, WO[3] if y % 3 else WO[2])
    cyl_normal(P, fx - 1, top, 4, fy - top)
    for y in range(fy - 26, fy - 4, 4):               # creosote rings / tar stains near the foot
        P.px(fx, y, WO[0])
    P.rect(fx - 3, fy - 3, 8, 4, ST[2], hgt=0.6)      # concrete foot
    P.hline(fx - 3, fy - 3, 8, ST[4])
    snow_top(P, fx - 3, fy - 4, 8, [SN[1], SN[2]], depth=1, seed=5)
    # cross-arm
    ay = top + 8
    P.rect(fx - 10, ay, 22, 2, WO[1], hgt=0.66)
    P.hline(fx - 10, ay, 22, WO[3])
    snow_top(P, fx - 10, ay - 1, 22, [SN[2], SN[3]], depth=1, seed=7)
    # insulator + cable anchor (left end of the arm)
    P.rect(fx - 9, ay - 3, 2, 3, SN[2], hgt=0.75)
    P.px(fx - 9, ay - 3, SN[4])
    anchor = (fx - 9, ay - 3)

    def horn(x, y, d):
        # bell-mouthed horn seen from the side; d = +1 points right, -1 points left
        for k in range(8):
            r = 1 + k // 3
            cx = x + d * k
            for dy in range(-r, r + 1):
                c = ST[2] if dy < 0 else ST[1]
                if abs(dy) == r:
                    c = ST[3] if dy < 0 else NI[2]
                P.px(cx, y + dy + k // 3, c, 0.7)
        mx = x + d * 8
        for dy in range(-3, 4):
            P.px(mx, y + dy + 2, ST[4] if dy < 0 else ST[2], 0.75)
        P.rect(x - d * 2, y - 1, 3, 3, NI[2], hgt=0.7)   # driver housing
    horn(fx - 4, ay + 6, -1)
    horn(fx + 5, ay + 6, +1)
    P.vline(fx - 4, ay + 2, 4, NI[2])
    P.vline(fx + 5, ay + 2, 4, NI[2])
    # junction box + cable down the pole
    P.rect(fx - 3, ay + 22, 7, 8, ST[2], hgt=0.7)
    P.hline(fx - 3, ay + 22, 7, ST[4])
    P.vline(fx + 3, ay + 22, 8, ST[3])
    P.px(fx, ay + 25, NI[2])
    for y in range(ay + 30, fy - 6):
        if y % 2 == 0:
            P.px(fx + 2, y, NI[2])
    # enamel plate (white with a black number)
    P.rect(fx - 2, ay + 40, 6, 5, SN[3], hgt=0.7)
    P.hline(fx - 1, ay + 42, 4, NI[2])
    # step bolts
    for y in range(ay + 48, fy - 10, 7):
        P.px(fx - 2, y, ST[3])
        P.px(fx + 3, y + 3, ST[3])
    # icicles under the horns and the arm
    icicles(P, fx - 10, fx + 12, ay + 2, seed=11, density=0.35, maxlen=3)
    rust_streak(P, fx - 4, ay + 9, 6, seed=2)
    rust_streak(P, fx + 4, ay + 32, 8, seed=3)
    return P, (fx, fy), anchor


def snowman():
    """Child-built snowman (exp_snowman): two lumpy balls, coal eyes, a twig nose and arms, and an 'ushanka'
    made from a rusty tin can with cardboard ear flaps.  Foot at local (10, 33)."""
    P = Layer(22, 35, 'snowman')
    fx, fy = 10, 33

    def ball(cx, cy, rx, ry, seed):
        m, mx, my = P.ellipse_mask(cx, cy, rx, ry)
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        u = (xx + mx + 0.5 - cx) / rx
        v = (yy + my + 0.5 - cy) / ry
        lit = np.clip(0.55 + 0.45 * (u * 0.6 - v * 0.8), 0, 1)
        nz = value_noise(ww, hh, 3, seed=seed, octaves=2)
        t = np.clip(lit + (nz - 0.5) * 0.25, 0, 0.999)
        ladder = [SN[0], SN[1], SN[2], SN[3], SN[4]]
        idx = np.clip((t * len(ladder)).astype(int), 0, len(ladder) - 1)
        P._put(m, mx, my, np.stack(ladder)[idx], hgt=None)
        P.dome_height(cx, cy, rx, ry, amp=0.8)
    ball(fx + 0.5, fy - 5.5, 6.8, 5.2, 3)
    ball(fx + 0.5, fy - 14.5, 4.6, 4.2, 4)
    # contact shadow + packed snow at the foot
    for x in range(fx - 7, fx + 9):
        P.px(x, fy, SN[0] if abs(x - fx) < 6 else ST[2])
    # coal buttons
    for y in (fy - 8, fy - 4):
        P.px(fx + 1, y, NI[1])
    # face: coal eyes, twig nose pointing left (towards the family), coal mouth
    P.px(fx - 1, fy - 16, NI[0])
    P.px(fx + 2, fy - 16, NI[0])
    P.line(fx, fy - 14, fx - 3, fy - 14, WO[1])
    for x in (fx - 1, fx, fx + 1, fx + 2):
        P.px(x, fy - 12 + (1 if x in (fx, fx + 1) else 0), NI[1])
    # tin-can ushanka: rusty can + cardboard ear flaps tied down with string
    cx0, cy0 = fx - 3, fy - 23
    P.rect(cx0, cy0, 8, 5, RU[3], hgt=0.85)
    P.vline(cx0, cy0, 5, RU[2])
    P.vline(cx0 + 7, cy0, 5, RU[5])
    P.vline(cx0 + 6, cy0, 5, RU[4])
    P.hline(cx0, cy0, 8, ST[3])                 # rolled rim (tin)
    P.hline(cx0, cy0 + 4, 8, ST[2])
    P.px(cx0 + 2, cy0 + 2, ST[4])               # bit of the old label / bare tin
    P.px(cx0 + 3, cy0 + 2, ST[3])
    cyl_normal(P, cx0, cy0, 8, 5)
    snow_top(P, cx0, cy0 - 1, 8, [SN[2], SN[3]], depth=1, seed=9)
    for (ex, d) in ((cx0 - 1, -1), (cx0 + 8, 1)):   # flaps
        P.rect(ex, cy0 + 3, 1, 5, WO[2], hgt=0.7)
        P.px(ex + d * 0, cy0 + 8, WO[1])
    P.line(cx0 - 1, cy0 + 8, cx0 + 8, cy0 + 8, ST[1])   # string under the chin
    # twig arms
    P.line(fx - 5, fy - 11, fx - 9, fy - 17, WO[1])
    P.px(fx - 9, fy - 18, WO[1])
    P.px(fx - 10, fy - 16, WO[1])
    P.line(fx + 6, fy - 11, fx + 10, fy - 15, WO[1])
    P.px(fx + 11, fy - 16, WO[1])
    P.px(fx + 10, fy - 17, WO[2])
    return P, (fx, fy)


def dwarf_signal():
    """Low (dwarf) shunting signal beside track 2: cast-iron head on a stub post, moon-white lamp lit,
    blue lamp dark, hood, number plate.  Foot at local (5, 18).  The lit lens is emissive (cold)."""
    P = Layer(12, 20, 'dwarf_signal')
    fx, fy = 5, 18
    P.rect(fx - 1, fy - 6, 3, 6, NI[2], hgt=0.6)
    P.vline(fx + 1, fy - 6, 6, ST[2])
    P.rect(fx - 3, fy - 1, 7, 2, ST[2], hgt=0.6)
    P.hline(fx - 3, fy - 1, 7, ST[4])
    P.rect(fx - 3, fy - 16, 7, 10, NI[3], hgt=0.7)       # head (black)
    P.vline(fx + 3, fy - 16, 10, ST[2])
    P.hline(fx - 3, fy - 16, 7, ST[2])
    P.rect(fx - 4, fy - 17, 9, 1, NI[2], hgt=0.75)       # hood
    snow_top(P, fx - 4, fy - 18, 9, [SN[2], SN[3]], depth=1, seed=4)
    # lenses: top = moon-white (lit), bottom = blue (dark)
    P.rect(fx - 1, fy - 14, 3, 3, SN[4], hgt=0.8, em=SN[4])
    P.px(fx, fy - 13, SK[5], em=SK[5])
    P.rect(fx - 1, fy - 10, 3, 3, NI[1], hgt=0.8)
    P.px(fx + 1, fy - 10, TE[2])
    P.rect(fx - 2, fy - 5, 5, 2, SN[3])                  # number plate
    P.px(fx, fy - 5, NI[2])
    return P, (fx, fy)


def crates_with_gap(seed=1):
    """crates_a (exp_stash): two crate stacks with a narrow dark gap; at the back of the gap a tin box catches
    a cold glint now and then (actor KarskGlint).  Foot at local (20, 33); returns (Layer, foot, glint_local)."""
    P = Layer(44, 34, 'crates')
    by = 33
    rng = np.random.default_rng(seed)
    # tin box in the gap (drawn first, partly hidden)
    gx = 18
    P.rect(gx, by - 6, 4, 5, NI[1], hgt=0.2)
    P.rect(gx + 1, by - 4, 3, 3, ST[2], hgt=0.3)       # tin corner
    P.px(gx + 1, by - 4, ST[4])
    P.px(gx + 2, by - 4, ST[3])
    P.px(gx + 3, by - 3, RU[1])
    boxes = [(1, by - 12, 17, 12), (3, by - 23, 14, 11), (22, by - 14, 19, 14), (25, by - 23, 13, 9)]
    for (x, y, w, h) in boxes:
        P.rect(x, y, w, h, WO[2], hgt=0.55)
        P.rect(x, y, w, 1, WO[4])
        P.vline(x + w - 1, y, h, WO[3])
        P.vline(x, y, h, WO[1])
        P.hline(x, y + h // 2, w, WO[1])
        P.line(x + 1, y + 1, x + w - 2, y + h - 2, WO[1])
        text(P, x + 3, y + 3, 'Г-' + str(int(rng.integers(1, 9))), WO[0], font='s')
        snow_top(P, x, y - 1, w, [SN[1], SN[2], SN[3]], depth=2, seed=x)
    # gap shadow between the stacks (the two inner faces)
    P.vline(18, by - 12, 6, NI[2])
    P.vline(21, by - 14, 8, NI[2])
    return P, (20, by), (gx + 2, by - 4)


def bench_newspaper(hist=False):
    """Platform bench with a newspaper left behind (exp_newspaper): one sheet leans against the backrest,
    masthead with the state emblem (5 px; neutral gear / hist hammer & sickle) and an official stamp.
    Foot at local (18, 19).  Returns (Layer, foot, emblem_local_xy)."""
    o = 4                                             # headroom for the sheet above the backrest
    P = Layer(36, 16 + o, 'bench')
    by = 15 + o
    P.rect(1, 6 + o, 34, 3, WO[2], hgt=0.6)
    P.hline(1, 6 + o, 34, WO[4])
    P.rect(1, 1 + o, 34, 2, WO[2], hgt=0.6)
    P.hline(1, 1 + o, 34, WO[3])
    for lx in (3, 31):
        P.rect(lx, 9 + o, 2, 6, NI[2])
        P.vline(lx, 1 + o, 8, NI[2])
    snow_top(P, 1, 5 + o, 34, [SN[2], SN[3]], depth=1, seed=2)
    nx = 8
    P.rect(nx, 5 + o, 14, 2, SN[2], hgt=0.7)         # folded part lying on the seat
    P.hline(nx, 5 + o, 14, SN[3])
    P.hline(nx + 2, 6 + o, 9, ST[3])
    sx, sy = nx + 1, o - 1                            # leaning sheet (top above the backrest)
    P.rect(sx, sy, 12, 7, SN[3], hgt=0.72)
    P.vline(sx + 11, sy, 7, SN[2])
    P.hline(sx, sy, 12, SN[4])
    kind = EMB.kind_for('gw5', hist)
    EMB.paint(P, sx + 1, sy + 1, kind, RED[2])
    P.rect(sx + 7, sy + 1, 4, 2, NI[2])               # masthead title bar
    P.hline(sx + 7, sy + 4, 4, ST[2])
    P.hline(sx + 1, sy + 6, 10, ST[2])
    P.px(sx + 9, sy + 3, RED[1])                      # official stamp
    return P, (18, by), (sx + 1, sy + 1)


def fire_wood(P, x, y):
    """Chopped sleeper blocks stacked at the barrel (fuel)."""
    for (bx, by_, w) in ((x, y - 3, 6), (x + 5, y - 3, 6), (x + 2, y - 6, 6)):
        P.rect(bx, by_, w, 3, WO[1], hgt=0.6)
        P.hline(bx, by_, w, WO[3])
        P.vline(bx, by_, 3, WO[2])
        P.px(bx + w - 1, by_ + 1, NI[3])


def sled():
    """Child's wooden sled (sanki) with a bundle tied on, beside the waiting family.  Foot at local (8, 8)."""
    P = Layer(18, 10, 'sled')
    by = 8
    # runners (bent steel strips) curling up at the front (right)
    P.hline(1, by, 14, ST[2], 0.6)
    P.hline(1, by - 1, 1, ST[2])
    P.px(15, by - 1, ST[3])
    P.px(16, by - 2, ST[3])
    P.px(16, by - 3, ST[4])
    for lx in (3, 7, 11):
        P.vline(lx, by - 3, 3, WO[1])
    # slats
    P.rect(1, by - 4, 14, 2, WO[2], hgt=0.6)
    P.hline(1, by - 4, 14, WO[4])
    for lx in range(2, 15, 3):
        P.px(lx, by - 3, WO[1])
    # bundle (checked cloth) tied on with string
    P.ellipse(8, by - 6.5, 4.5, 2.6, SA[1], hgt=0.7)
    P.ellipse(8.6, by - 7.2, 3.2, 1.6, SA[2])
    P.px(6, by - 7, SA[0])
    P.px(10, by - 6, SA[0])
    P.vline(8, by - 9, 4, ST[1])
    snow_top(P, 5, by - 10, 6, [SN[2], SN[3]], depth=1, seed=12)
    P.line(16, by - 3, 17, by + 1, ST[1])      # pull string trailing
    return P, (8, by)


def ground_life(L, E):
    """Ground-band detail pass (after make_ground): footprint trails, cat and crow prints, sled runners,
    frozen puddles, chopped sleeper blocks by the barrel, coal grit."""
    # boot trails on the back strip: plank crossing -> cabin door; crossing -> tea stall; office door path
    footprints(L, [(395, 262), (430, 257), (470, 254), (490, 252)], 'boot', seed=1)
    footprints(L, [(382, 262), (350, 258), (300, 254), (292, 252)], 'boot', seed=2)
    footprints(L, [(1475, 262), (1490, 257), (1503, 252)], 'boot', seed=3)
    footprints(L, [(1110, 261), (1200, 256), (1300, 258), (1400, 254)], 'boot', seed=4)
    # crow prints under the PA cable
    footprints(L, [(630, 253), (650, 255), (668, 253), (690, 256)], 'bird', seed=5)
    # child prints: family -> snowman (round trip) and stamping circles around it
    footprints(L, [(300, 326), (322, 336), (338, 343), (352, 344)], 'child', seed=6)
    footprints(L, [(356, 346), (366, 342), (368, 335), (360, 333)], 'child', seed=7)
    footprints(L, [(352, 348), (330, 350), (308, 344), (296, 334)], 'child', seed=8)
    # cat prints along the back drift of the platform from the barrel to the timetable and back
    footprints(L, [(1006, 304), (1030, 302), (1052, 303), (1075, 301)], 'cat', seed=9)
    # sled runners pulled in from the left end of the platform
    sled_tracks(L, 150, 312, 331, seed=3)
    # frozen puddles (glassy, cracked) among the wet ones
    ice_patch(L, 446, 332, 14, 3.2, seed=1)
    ice_patch(L, 1236, 334, 16, 3.5, seed=2)
    ice_patch(L, 1700, 318, 12, 3.0, seed=3)
    ice_patch(L, 776, 256, 10, 2.0, seed=4)
    # chopped sleeper blocks + a scatter of ash by the fire barrel (fuel)
    fire_wood(L, 934, 304)
    for k, x in enumerate(range(952, 1000, 3)):
        if (x * 7) % 5 < 2:
            L.px(x, 306 + (k % 2), ST[1])
    # coal grit in front of the cabin's coal heap
    for k, x in enumerate(range(586, 606, 2)):
        L.px(x, 252 + (k % 3), NI[1])
