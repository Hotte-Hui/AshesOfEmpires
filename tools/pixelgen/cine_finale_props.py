"""cine_finale_props -- extra desk and room props for the X1 finale montage (owner: trans-finale).

Everything that makes the two desks look worked at rather than staged: Konrad's grey felt hat put down on the
desk, a coffee cup on its saucer, rolled plans and a pencil cup (Berlin); a wooden abacus, an inkwell with a
dip pen, the rubber stamp on its pad, a black telephone and a signal lantern (Karsk).  All drawn top-down on
the desk plane (foreshortening 0.62) with the same lamp model as the rest of the close-ups, deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import pg

BR, KR = kit.BR, kit.KR
FELT = kit.R('#16110F', '#2A2421', '#3E3632', '#544A44', '#6B6058', '#82766C', '#9C9083', '#B7AC9F')


def _grid(cv):
    return cv.grid()


def felt_hat(cv: kit.Canvas, cx, cy, lamp, ramp=FELT, band=None, lift=8.0):
    """A grey felt hat lying crown-up on the desk: brim, crown with the centre dent, ribbon band."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    band = band or BR['black']
    brim = kit.ellipse_full(w, h, cx, cy, 34, 19)
    crown = kit.ellipse_full(w, h, cx + 1, cy - 6, 21, 12)
    # cast shadow of the brim on the desk
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, brim, 6, 4, 1, BR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=lift)
    # brim: curls up at the sides (lighter rim), darker under the crown's shadow
    rr = np.sqrt(((xx - cx) / 34.0) ** 2 + ((yy - cy) / 19.0) ** 2)
    bt = 0.14 + 0.62 * pool + 0.12 * np.clip(rr - 0.75, 0, 1) * 4.0
    cv.paint(brim, np.clip(bt, 0, 1), ramp)
    # crown: dome with the long centre dent (pinch) along its axis
    hc = np.sqrt(np.clip(1 - ((xx - cx - 1) / 21.0) ** 2 - ((yy - cy + 6) / 12.0) ** 2, 0, 1))
    dent = np.exp(-((xx - cx - 1) / 3.0) ** 2) * np.clip(1 - np.abs((yy - cy + 7) / 9.0), 0, 1)
    ct = 0.18 + 0.70 * pool * (0.55 + 0.45 * hc) - 0.22 * dent + 0.10 * (xx < cx - 4) * hc
    cv.paint(crown, np.clip(ct, 0, 1), ramp)
    # ribbon band round the crown's base, with a small bow on the left
    bnd = crown & ~kit.ellipse_full(w, h, cx + 1, cy - 8, 20, 10.5)
    cv.paint(bnd, np.clip(0.10 + 0.4 * pool, 0, 1), band)
    cv.rect(int(cx - 21), int(cy - 6), 3, 4, band[2])
    # outlines on the shadow side
    cv.c[kit.outline_of(brim) & (yy > cy)] = np.asarray(ramp[0], np.uint8)
    cv.c[kit.outline_of(crown) & (yy > cy - 6) & ~kit.outline_of(brim)] = np.asarray(ramp[1], np.uint8)
    return brim | crown


def cup_saucer(cv: kit.Canvas, cx, cy, lamp, ramp=None, drink=None):
    """White china cup with coffee on its saucer, handle to the right.  Returns the steam origin."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    ramp = ramp or BR['paper']
    drink = drink or kit.R('#120C0A', '#2A1B16', '#3D2820', '#55372A')
    from cine_finale_berlin import drop_shadow
    sau = kit.ellipse_full(w, h, cx, cy + 3, 17, 10)
    drop_shadow(cv, sau, 5, 3, 1, BR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=4)
    cv.paint(sau, np.clip(0.18 + 0.75 * pool, 0, 1), ramp)
    cv.paint(kit.ellipse_full(w, h, cx, cy + 3, 11, 6.5) & sau, np.clip(0.10 + 0.6 * pool, 0, 1), ramp)
    body = kit.ellipse_full(w, h, cx, cy - 1, 10, 7)
    cv.paint(body, np.clip(0.22 + 0.8 * pool + 0.12 * (xx < cx - 3), 0, 1), ramp)
    hnd = kit.ellipse_full(w, h, cx + 12, cy, 3.5, 3) & ~kit.ellipse_full(w, h, cx + 12, cy, 1.5, 1.2)
    cv.paint(hnd, np.clip(0.2 + 0.7 * pool, 0, 1), ramp)
    top = kit.ellipse_full(w, h, cx, cy - 2, 8, 5)
    cv.paint(top, np.clip(0.15 + 0.4 * pool + 0.2 * (np.abs(xx - cx + 3) < 1.0) * (np.abs(yy - cy + 4) < 1.0), 0, 1), drink)
    cv.c[kit.outline_of(body) & (yy > cy)] = np.asarray(ramp[2], np.uint8)
    cv.c[kit.outline_of(sau) & (yy > cy + 3)] = np.asarray(ramp[1], np.uint8)
    return (cx, cy - 3)


def rolled_plans(cv: kit.Canvas, x0, y0, lamp, n=4, seed='rolls', ramp=None):
    """A few rolled-up plans lying side by side, tied with string, ends showing the paper spiral."""
    ramp = ramp or BR['paper']
    rng = np.random.default_rng(kit.seed_of(seed))
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    from cine_finale_berlin import drop_shadow
    for i in range(n):
        ln = int(rng.integers(64, 92))
        r = float(rng.uniform(4.0, 6.0))
        ax, ay = x0 + i * 3, y0 + i * 11
        bx, by = ax + ln, ay - ln * 0.18
        hh, t = kit.capsule_height(xx, yy, ax, ay, bx, by, r)
        m = hh > 0.05
        drop_shadow(cv, m, 4, 3, 1, BR['desk'], lamp, blur=1)
        pool = lamp.pool(xx, yy, lift=6)
        tone = 0.12 + 0.62 * pool * (0.45 + 0.55 * hh / r) + 0.05 * (np.sin(t * ln / 3.0) > 0.85)
        cv.paint(m, np.clip(tone, 0, 1), ramp)
        cv.c[kit.outline_of(m) & (yy > (ay + by) / 2)] = np.asarray(ramp[1], np.uint8)
        # paper spiral at the near end
        cv.ellipse(ax, ay, max(1, r - 1.5), max(1, r - 2.0), ramp[3])
        cv.px(ax, ay, ramp[1])
        # string tie
        tx, ty = ax + ln * 0.35, ay - ln * 0.35 * 0.18
        cv.line(tx, ty - r, tx + 1, ty + r, BR['brass'][2])


def pencil_cup(cv: kit.Canvas, cx, cy, lamp):
    """Tin cup with pencils, a ruler edge and a pair of compasses sticking out."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pool = lamp.pool(xx, yy, lift=14)
    for (dx, dy, col) in ((-5, -16, BR['brass'][4]), (-1, -19, BR['red'][2]), (3, -15, BR['brass'][5]),
                          (6, -12, BR['metal'][6]), (-7, -11, BR['ink'][1])):
        cv.line(cx + dx * 0.3, cy - 2, cx + dx, cy + dy, col)
        cv.px(cx + dx, cy + dy, BR['black'][3])
    body = kit.poly_mask_full(w, h, [(cx - 7, cy - 4), (cx + 7, cy - 4), (cx + 6, cy + 9), (cx - 6, cy + 9)])
    cv.paint(body, np.clip(0.15 + 0.7 * pool + 0.15 * (xx < cx - 2), 0, 1), BR['metal'])
    cv.paint(kit.ellipse_full(w, h, cx, cy - 4, 7, 2.5), np.clip(0.05 + 0.2 * pool, 0, 1), BR['black'])
    cv.c[kit.outline_of(body) & (xx > cx)] = np.asarray(BR['black'][1], np.uint8)


# ------------------------------------------------------------------------------------------- Karsk
WOOD_K = kit.R('#1A0F08', '#2E1C10', '#46301C', '#5E4228', '#7A5836', '#987246', '#B48C5A')
BEAD = kit.R('#1A0C08', '#3A1810', '#5E2618', '#86382A', '#A8503A', '#C86E52', '#E4987A')
BEAD_W = kit.R('#262420', '#4A4740', '#6E6A60', '#948F82', '#BAB4A4', '#DCD6C6')


def abacus(cv: kit.Canvas, x0, y0, lamp, seed='schoty'):
    """Office abacus (schoty) lying flat: wooden frame, ten wires, beads pushed to either side (a sum stands
    on it); the two middle beads of every wire are light."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    fw, fh = 64, 40
    frame = kit.poly_mask_full(w, h, [(x0, y0), (x0 + fw, y0 - 3), (x0 + fw + 2, y0 + fh), (x0 + 2, y0 + fh + 3)])
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, frame, -5, 4, 1, KR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=4)
    cv.paint(frame, np.clip(0.12 + 0.7 * pool, 0, 1), WOOD_K)
    inner = kit.erode(frame, 3)
    cv.paint(inner, np.clip(0.02 + 0.22 * pool, 0, 1), KR['desk'])
    rng = np.random.default_rng(kit.seed_of(seed))
    for r in range(10):
        wy = y0 + 4 + r * 3.6
        cv.line(x0 + 3, wy - 0.3 * 0, x0 + fw - 1, wy - 3 * (1 - r / 10.0) * 0, KR['metal'][5])
        left = int(rng.integers(0, 11))
        for b_ in range(10):
            slot = b_ if b_ < left else (b_ + 4)
            bx = x0 + 6 + slot * 3.9
            light = b_ in (4, 5)
            t = float(np.clip(0.20 + 0.85 * lamp.pool(np.float32(bx), np.float32(wy), lift=6), 0, 1))
            ramp = BEAD_W if light else BEAD
            cv.ellipse(bx, wy, 1.7, 1.4, kit.tone_to_ramp(np.array([[t]], np.float32), ramp, dither=False)[0, 0])
            cv.px(bx - 1, wy - 1, kit.tone_to_ramp(np.array([[min(1, t + 0.25)]], np.float32), ramp, dither=False)[0, 0])
    cv.c[kit.outline_of(frame) & (xx < x0 + fw / 2)] = np.asarray(WOOD_K[0], np.uint8)


def inkwell_pen(cv: kit.Canvas, cx, cy, lamp):
    """Square glass inkwell with violet ink, a dip pen resting across its rim."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pool = lamp.pool(xx, yy, lift=8)
    body = kit.poly_mask_full(w, h, [(cx - 8, cy - 6), (cx + 8, cy - 7), (cx + 9, cy + 6), (cx - 7, cy + 7)])
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, body, -4, 3, 1, KR['desk'], lamp, blur=1)
    cv.paint(body, np.clip(0.20 + 0.7 * pool, 0, 1), KR['glass'])
    ink = kit.ellipse_full(w, h, cx, cy - 1, 4, 3)
    cv.paint(ink, np.clip(0.1 + 0.3 * pool, 0, 1), kit.R('#140C1C', '#26183A', '#3A2858', '#56407A'))
    cv.c[kit.outline_of(body) & (xx < cx)] = np.asarray(KR['glass'][1], np.uint8)
    cv.line(cx - 2, cy - 1, cx + 26, cy - 11, KR['metal'][2])
    cv.line(cx - 2, cy, cx + 26, cy - 10, KR['brass'][4])
    cv.px(cx - 3, cy, KR['metal'][7])


def stamp_pad(cv: kit.Canvas, cx, cy, lamp):
    """Tin stamp pad (red ink) with the wooden rubber stamp standing beside it."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pool = lamp.pool(xx, yy, lift=4)
    tin = kit.poly_mask_full(w, h, [(cx - 13, cy - 7), (cx + 13, cy - 8), (cx + 14, cy + 7), (cx - 12, cy + 8)])
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, tin, -4, 3, 1, KR['desk'], lamp, blur=1)
    cv.paint(tin, np.clip(0.15 + 0.7 * pool, 0, 1), KR['metal'])
    pad = kit.erode(tin, 2)
    cv.paint(pad, np.clip(0.10 + 0.6 * pool, 0, 1), KR['stamp'])
    # the stamp: round wooden handle seen from above, its rubber foot's shadow
    hx, hy = cx + 24, cy - 2
    foot = kit.ellipse_full(w, h, hx, hy + 2, 7, 4.5)
    drop_shadow(cv, foot, -4, 3, 1, KR['desk'], lamp, blur=1)
    cv.paint(foot, np.clip(0.12 + 0.6 * pool, 0, 1), WOOD_K)
    knob = kit.ellipse_full(w, h, hx, hy - 4, 4.5, 4)
    cv.paint(knob, np.clip(0.25 + 0.8 * pool + 0.12 * (xx < hx - 1), 0, 1), WOOD_K)
    cv.c[kit.outline_of(knob) & (xx > hx)] = np.asarray(WOOD_K[0], np.uint8)


def telephone_k(cv: kit.Canvas, cx, cy, lamp):
    """Black bakelite desk telephone with a rotary dial, handset on the cradle, cord curling away."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pool = lamp.pool(xx, yy, lift=10)
    base = kit.poly_mask_full(w, h, [(cx - 16, cy - 8), (cx + 16, cy - 9), (cx + 19, cy + 10), (cx - 18, cy + 11)])
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, base, -5, 3, 1, KR['desk'], lamp, blur=1)
    blk = KR['metal']
    cv.paint(base, np.clip(0.06 + 0.45 * pool + 0.08 * (yy < cy - 3), 0, 1), blk)
    dial = kit.ellipse_full(w, h, cx, cy + 3, 8, 5)
    cv.paint(dial, np.clip(0.18 + 0.6 * pool, 0, 1), blk)
    for k in range(10):
        a = k / 10.0 * 2 * math.pi + 0.6
        cv.px(cx + math.cos(a) * 5.5, cy + 3 + math.sin(a) * 3.4, KR['paper'][4])
    cv.px(cx, cy + 3, KR['paper'][6])
    hs = kit.poly_mask_full(w, h, [(cx - 20, cy - 12), (cx + 20, cy - 13), (cx + 20, cy - 7), (cx - 20, cy - 6)])
    cv.paint(hs, np.clip(0.10 + 0.6 * pool + 0.18 * (np.abs(yy - cy + 11) < 1), 0, 1), blk)
    for e in (-1, 1):
        cv.ellipse(cx + e * 20, cy - 10, 5, 4, blk[3])
        cv.px(cx + e * 20 - 1, cy - 12, blk[6])
    for k in range(18):
        cv.px(cx + 19 + k * 1.6, cy + 6 + math.sin(k * 1.4) * 2.0 + k * 0.6, blk[2])


def signal_lantern(cv: kit.Canvas, cx, cy, lamp, lit=True):
    """Railwayman's hand lantern standing on the desk: tin body, glass lens, wire handle; a faint glow."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pool = lamp.pool(xx, yy, lift=16)
    body = kit.poly_mask_full(w, h, [(cx - 9, cy - 16), (cx + 9, cy - 16), (cx + 10, cy + 10), (cx - 10, cy + 10)])
    from cine_finale_berlin import drop_shadow
    drop_shadow(cv, body, -6, 3, 1, KR['desk'], lamp, blur=1)
    cv.paint(body, np.clip(0.12 + 0.6 * pool + 0.12 * (xx < cx - 3), 0, 1), KR['metal'])
    lens = kit.ellipse_full(w, h, cx, cy - 2, 6, 6)
    if lit:
        cv.paint(lens, np.clip(0.55 + 0.4 * (1 - np.sqrt((xx - cx) ** 2 + (yy - cy + 2) ** 2) / 6), 0, 1), KR['fire'])
    else:
        cv.paint(lens, np.clip(0.2 + 0.4 * pool, 0, 1), KR['glass'])
    top = kit.ellipse_full(w, h, cx, cy - 17, 8, 3)
    cv.paint(top, np.clip(0.2 + 0.6 * pool, 0, 1), KR['metal'])
    for k in range(13):
        a = math.pi * k / 12.0
        cv.px(cx - math.cos(a) * 8, cy - 18 - math.sin(a) * 7, KR['metal'][6])
    cv.c[kit.outline_of(body) & (xx > cx)] = np.asarray(KR['metal'][1], np.uint8)
    if lit:
        bay = kit.bayer_full(w, h)
        g = np.clip(1.0 - np.sqrt(((xx - cx) / 26.0) ** 2 + ((yy - cy - 4) / 16.0) ** 2), 0, 1)
        glow = (g > 0.05) & (bay < g * 0.35) & (cv.c[..., 3] > 0) & ~body
        cv.c[glow] = np.asarray(KR['rust'][4], np.uint8)


BLOTTER = kit.R('#04100C', '#081A14', '#0E261C', '#163326', '#204232', '#2C5240', '#3A644E')


def blotter(cv: kit.Canvas, x0, y0, x1, y1, lamp, seed='blotter'):
    """Desk blotter: green felt pad in a dark leather frame with corner pockets, ink blots and pencil marks
    (stays on the desk when the ledger is put away)."""
    w, h = cv.w, cv.h
    xx, yy = _grid(cv)
    pad = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    pool = lamp.pool(xx, yy, lift=1)
    nz = pg.value_noise(w, h, 7, kit.seed_of(seed), octaves=2)
    cv.paint(pad, np.clip(0.06 + 0.62 * pool + (nz - 0.5) * 0.08, 0, 1), BLOTTER)
    rim = pad & ~((xx >= x0 + 3) & (xx < x1 - 3) & (yy >= y0 + 2) & (yy < y1 - 2))
    cv.paint(rim, np.clip(0.06 + 0.5 * pool, 0, 1), WOOD_K)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
        tri = kit.poly_mask_full(w, h, [(cx, cy), (cx + sx * 22, cy), (cx, cy + sy * 14)])
        cv.paint(tri & pad, np.clip(0.10 + 0.6 * pool, 0, 1), WOOD_K)
        cv.c[kit.outline_of(tri) & pad & ~rim] = np.asarray(WOOD_K[0], np.uint8)
    rng = np.random.default_rng(kit.seed_of(seed + 'ink'))
    ink = kit.R('#140C1C', '#26183A')
    for _ in range(9):
        bx, by = rng.uniform(x0 + 10, x1 - 10), rng.uniform(y0 + 8, y1 - 8)
        r = rng.uniform(1.0, 3.2)
        m = kit.ellipse_full(w, h, bx, by, r * 1.4, r) & pad
        cv.c[m] = np.asarray(ink[int(rng.random() < 0.5)], np.uint8)
    for _ in range(14):
        ax_, ay_ = rng.uniform(x0 + 8, x1 - 40), rng.uniform(y0 + 6, y1 - 6)
        ln = rng.uniform(8, 30)
        for k in range(int(ln)):
            if rng.random() < 0.7:
                cv.px(ax_ + k, ay_ + math.sin(k * 0.7) * 0.6, BLOTTER[2])
    cv.c[kit.outline_of(pad) & (yy > (y0 + y1) / 2)] = np.asarray(WOOD_K[0], np.uint8)
