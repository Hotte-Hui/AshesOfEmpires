"""cine_finale_karsk -- Karsk shots of the X1 finale montage (owner: trans-finale).

Mirror of the Berlin shots: the window is on the LEFT (west, towards Berlin), the lamp on the right.
  ext       night view from the signal box over the snowy yard: signal lamps, a sodium mast, wagons,
            silos and cooling towers against an industrial cloud glow (one painting for every Karsk window)
  k_close   Alexei's desk from above: green enamel lamp, open freight ledger (C-17 line), tea glass in a
            metal holder, Morse key, the desk drawer at the front edge
  k_wide    the signal box interior with Alexei (runtime sprite)
  k_window  insert: snow against the glass, the yard beyond
Original, procedural, deterministic; karsk palette (pg.PALETTES['karsk']).
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as bb
import pg

KR = kit.KR
W, H = bb.W, bb.H
OX, OY = bb.OX, bb.OY
V = bb.V
LAMP_K = kit.Lamp(490 + OX, 168 + OY, 118, 150, depth=0.62, power=1.05, aim=(-62, 52))
DESK_Y = 112 + OY
FRONT_Y = 282 + OY                  # front edge of the desk top (drawer front below)
WIN_K = (-20, -10, 256 + OX, 106 + OY)
EXT_OFF_CLOSE = (130 + OX - 360, 98 + OY - 192)
COLD_K = [pg.hx(c) for c in ('#05090F', '#0A1219', '#0E1A20', '#13252B', '#122126', '#1B3033', '#26403F',
                             '#36534D', '#4A675C', '#7E8E8C', '#A3B1AD')]


def exterior(w: int = 720, h: int = 400) -> np.ndarray:
    """Night over the Karsk yard seen from the elevated signal box."""
    cv = kit.Canvas(w, h, 'kext')
    xx, yy = cv.grid()
    bay = kit.bayer_full(w, h)
    rng = np.random.default_rng(kit.seed_of('ext_karsk'))
    sky = [pg.hx(c) for c in ('#05090F', '#0A1219', '#0E1A20', '#13252B', '#122126', '#1B3033', '#26403F')]
    glow = np.exp(-(((xx - w * 0.62) / (w * 0.5)) ** 2) - (((yy - h * 0.40) / (h * 0.20)) ** 2)) * 0.30
    st = np.clip(yy / (h * 0.52), 0, 1) ** 1.5 * 0.50 + glow
    cv.paint(np.ones((h, w), bool), np.clip(st, 0, 1), sky)
    cl = kit.Canvas(w, h)
    pg.clouds(cl, int(h * 0.04), int(h * 0.22), [pg.hx(c) for c in ('#0A1219', '#0E1A20', '#13252B', '#1B3033')],
              seed=kit.seed_of('kext_clouds'), count=6, min_w=160, max_w=340, light=(0.0, 0.95, 0.3), ambient=0.4)
    sel = cl.c[..., 3] > 0
    cv.c[sel] = cl.c[sel]
    horizon = int(h * 0.48)
    far = kit.Canvas(w, h)
    col_far = pg.hx('#0E1A20')
    for (x0, wd, ht) in ((60, 26, 70), (90, 26, 76), (120, 26, 70), (150, 26, 64)):
        far.rect(x0, horizon - ht, wd - 2, ht, col_far)
        far.ellipse(x0 + wd / 2 - 1, horizon - ht, wd / 2 - 1, 4, col_far)
        far.rect(x0 + wd - 4, horizon - ht, 1, ht, pg.hx('#13252B'))
    for (cx, wd, ht) in ((520, 70, 88), (610, 64, 76)):
        top = horizon - ht
        poly = [(cx - wd * 0.5, horizon), (cx - wd * 0.36, top + ht * 0.45), (cx - wd * 0.34, top),
                (cx + wd * 0.34, top), (cx + wd * 0.36, top + ht * 0.45), (cx + wd * 0.5, horizon)]
        far.poly(poly, col_far)
    for (cx, ht) in ((300, 110), (330, 96)):
        far.rect(cx, horizon - ht, 6, ht, col_far)
    sel = far.c[..., 3] > 0
    cv.c[sel] = far.c[sel]
    for (cx, ht) in ((300, 110), (330, 96)):
        cv.px(cx + 2, horizon - ht - 1, pg.hx('#A8382E'))
    for (x, y) in ((70, horizon - 40), (96, horizon - 22), (160, horizon - 30), (305, horizon - 60), (126, horizon - 52)):
        cv.px(x, y, pg.hx('#DCA16E'))
    # soft steam above the cooling tower (a few lit puffs drifting west)
    plume = kit.Canvas(w, h)
    circles = [(520 - k * 16, horizon - 96 - k * 7 - (k * k) * 0.6, 9 + k * 2.2) for k in range(7)]
    pg.puffs(plume, circles, [pg.hx(c) for c in ('#0E1A20', '#13252B', '#1B3033', '#26403F')], light=(0.0, 0.9, 0.4),
             ambient=0.35, seed=kit.seed_of('kplume'), gaps=(6, 0.45))
    sel = plume.c[..., 3] > 0
    cv.c[sel] = plume.c[sel]
    # yard: snow field, darker far away, drifts
    ground = yy >= horizon
    rel = np.clip((yy - horizon) / (h - horizon), 0, 1)
    nz = pg.value_noise(w, h, 18, kit.seed_of('kground'), octaves=3)
    gt = 0.14 + 0.24 * rel + (nz - 0.5) * 0.16
    snow_r = [pg.hx(c) for c in ('#0A1219', '#13252B', '#26403F', '#4A675C', '#7E8E8C', '#A3B1AD')]
    cv.paint(ground, np.clip(gt, 0, 1), snow_r)
    # tracks converging to a vanishing point on the right horizon
    vp = (w * 1.15, horizon + 1)
    lamp_x = w * 0.40
    for k in range(-2, 9):
        y_near = horizon + 30 + k * 34
        for side, off in (('a', 0.0), ('b', 9.0 + k * 0.6)):
            ya = y_near + off
            pts = []
            for x in range(-4, w + 4):
                f = (x + 4) / (vp[0] + 4)
                y = ya + (vp[1] - ya) * f
                pts.append((x, y))
            for (x, y) in pts:
                if y < horizon or y >= h:
                    continue
                near_lamp = math.exp(-((x - lamp_x) / 70.0) ** 2) * (1.0 - abs(y - (horizon + 40)) / 120.0)
                c = pg.hx('#0A1219')
                cv.px(x, y, c)
                if near_lamp > 0.25:
                    cv.px(x, y - 1, pg.hx('#C98A5C') if near_lamp > 0.5 else pg.hx('#7E8E8C'))
                elif (x * 13 + k * 7) % 23 == 0:
                    cv.px(x, y - 1, pg.hx('#4A675C'))
        # sleepers: short dark ticks between the rails
        for x in range(0, w, 6):
            f = x / vp[0]
            y0 = y_near + (vp[1] - y_near) * f
            y1 = y_near + 9 + (vp[1] - y_near - 9) * f
            if horizon < y0 < h and (x // 6) % 2 == 0:
                cv.line(x, y0 + 1, x, y1 - 1, pg.hx('#13252B'))
    # sodium lamp mast: soft cone + warm pool on the snow
    mx, mtop = int(lamp_x), horizon - 72
    cone = kit.poly_mask_full(w, h, [(mx - 5, mtop + 3), (mx - 3, mtop + 3), (mx + 30, horizon + 46), (mx - 42, horizon + 46)])
    ct = np.clip(1.0 - (yy - mtop) / (horizon + 46 - mtop), 0, 1)
    sel = cone & (bay < 0.06 + 0.16 * ct)
    cv.c[sel] = kit.tone_to_ramp(np.clip(0.2 + ct * 0.5, 0, 1), KR['copper'][:3])[sel]
    pool = kit.ellipse_full(w, h, mx - 6, horizon + 46, 56, 11)
    pd = np.sqrt(((xx - (mx - 6)) / 56.0) ** 2 + ((yy - (horizon + 46)) / 11.0) ** 2)
    cv.c[pool & (bay < 0.75 * (1 - pd))] = pg.hx('#8D5542')
    cv.c[pool & (bay < 0.45 * (1 - pd))] = pg.hx('#C98A5C')
    cv.c[pool & (bay < 0.18 * (1 - pd))] = pg.hx('#F0C487')
    cv.rect(mx, mtop, 2, horizon + 46 - mtop, pg.hx('#05090F'))
    cv.rect(mx - 7, mtop, 9, 2, pg.hx('#05090F'))
    cv.px(mx - 6, mtop + 2, pg.hx('#FBE3AE'))
    cv.px(mx - 5, mtop + 2, pg.hx('#FBE3AE'))
    cv.px(mx - 4, mtop + 2, pg.hx('#F0C487'))
    # signal masts with lamps and dithered halos (emissive look)
    for (sx, lamp_c, hgt, halo_c) in ((int(w * 0.18), '#9DAF91', 54, '#36534D'), (int(w * 0.66), '#C8503C', 46, '#6B3B2C'),
                                      (int(w * 0.86), '#9DAF91', 50, '#36534D')):
        top = horizon + 22 - hgt
        hal = kit.ellipse_full(w, h, sx + 1, top + 3, 9, 8)
        hd = np.sqrt(((xx - sx - 1) / 9.0) ** 2 + ((yy - top - 3) / 8.0) ** 2)
        cv.c[hal & (bay < 0.6 * (1 - hd))] = pg.hx(halo_c)
        cv.rect(sx, top, 2, hgt, pg.hx('#05090F'))
        cv.rect(sx - 2, top, 6, 9, pg.hx('#05090F'))
        cv.rect(sx, top + 2, 2, 2, pg.hx(lamp_c))
        cv.px(sx, top + 2, pg.hx('#DCE2C8' if lamp_c == '#9DAF91' else '#FBE3AE'))
        refl = kit.ellipse_full(w, h, sx + 1, horizon + 24, 5, 2)
        cv.c[refl & (bay < 0.4)] = pg.hx(halo_c)
    wy = horizon + 3
    x = 430
    for k in range(4):
        cv.rect(x, wy - 18, 44, 18, pg.hx('#22180F'))
        cv.rect(x + 1, wy - 17, 42, 1, pg.hx('#33251A'))
        cv.rect(x, wy - 19, 44, 2, pg.hx('#7E8E8C'))
        cv.rect(x + 18, wy - 14, 8, 10, pg.hx('#0A1219'))
        cv.rect(x + 4, wy, 4, 2, pg.hx('#05090F'))
        cv.rect(x + 36, wy, 4, 2, pg.hx('#05090F'))
        x += 47
    cv.c[..., 3] = 255
    return cv.c


# ------------------------------------------------------------------------------------------- k_close
LEDGER_L = [V(262, 184), V(368, 180), V(370, 262), V(266, 268)]     # left page
LEDGER_R = [V(368, 180), V(474, 182), V(476, 266), V(370, 262)]     # right page
GLASS_C = V(536, 200)


def cold_patch_k(cv, quad, gain=1.3, lift=0.04):
    w, h = cv.w, cv.h
    m = kit.poly_mask_full(w, h, quad)
    bay = kit.bayer_full(w, h)
    core = kit.erode(m, 2)
    edge = m & ~core
    cl = np.array([0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in COLD_K], np.float32) / 255.0
    rgb = cv.c[..., :3].astype(np.float32) / 255.0
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    idx = np.abs((lum * gain + lift)[..., None] - cl[None, None, :]).argmin(-1)
    col = np.stack(COLD_K)[idx]
    sel = (core | (edge & (bay < 0.5))) & (cv.c[..., 3] > 0)
    cv.c[sel] = col[sel]
    return m


def lamp_enamel(w, h, head, lamp_on=True):
    """Green enamel desk lamp on a gooseneck from the right; shade opens down-left.  Returns (rgba, em)."""
    cv = kit.Canvas(w, h)
    hx, hy = head
    gr = KR['enamel']
    met = KR['metal']
    # gooseneck: from the right edge, a segmented curve to the shade top
    neck = pg.bezier([(hx + 120, hy - 40), (hx + 60, hy - 52), (hx + 26, hy - 30), (hx + 14, hy - 14)], n=60)
    for i, (px_, py_) in enumerate(neck):
        cv.px(px_, py_, met[3])
        cv.px(px_, py_ + 1, met[5] if i % 3 == 0 else met[2])
    ax, ay = -0.55, 0.83
    nxp, nyp = -ay, ax
    top_c = (hx - ax * 14, hy - ay * 14)
    rim_c = (hx + ax * 12, hy + ay * 12)
    r_top, r_rim = 8.0, 25.0
    poly = [(top_c[0] + nxp * r_top, top_c[1] + nyp * r_top), (rim_c[0] + nxp * r_rim, rim_c[1] + nyp * r_rim),
            (rim_c[0] - nxp * r_rim, rim_c[1] - nyp * r_rim), (top_c[0] - nxp * r_top, top_c[1] - nyp * r_top)]
    sm = kit.poly_mask_full(w, h, poly)
    xx, yy = cv.grid()
    across = ((xx - hx) * nxp + (yy - hy) * nyp) / r_rim
    along = ((xx - hx) * ax + (yy - hy) * ay) / 14.0
    tone = 0.45 + 0.28 * np.clip(-across, -1, 1) + 0.10 * np.clip(along, -1, 1)
    tone = np.where(np.abs(across + 0.45) < 0.09, tone + 0.32, tone)
    cv.paint(sm, np.clip(tone, 0, 1), gr)
    lip = sm & (along > 0.6)
    cv.paint(lip, np.clip(0.4 + 0.3 * (along - 0.6), 0, 1), KR['brass'])
    dxr, dyr = xx - rim_c[0], yy - rim_c[1]
    u = dxr * nxp + dyr * nyp
    v = dxr * ax + dyr * ay
    rim_m = (u / r_rim) ** 2 + (v / 6.5) ** 2 <= 1.0
    inner = (u / (r_rim - 2)) ** 2 + (v / 4.6) ** 2 <= 1.0
    bulb = (u / 6.0) ** 2 + ((v + 1.5) / 3.0) ** 2 <= 1.0
    em = np.zeros((h, w), bool)
    if lamp_on:
        g = np.clip(1.0 - np.sqrt((u / r_rim) ** 2 + (v / 6.5) ** 2), 0, 1)
        cv.paint(rim_m & ~inner, np.full((h, w), 0.6, np.float32), KR['brass'])
        cv.paint(inner, np.clip(0.5 + g * 0.6, 0, 1), KR['copper'])
        cv.c[bulb] = pg.hx('#FBE3AE')
        em = inner | bulb
    else:
        cv.paint(rim_m & ~inner, np.full((h, w), 0.4, np.float32), met)
        cv.paint(inner, np.full((h, w), 0.12, np.float32), met)
        cv.c[bulb] = pg.hx('#3B3F3B')
    a = cv.alpha()
    edge = kit.outline_of(a) & (xx < hx)
    cv.c[edge & sm] = gr[0]
    return cv.c, em


def tea_glass(cv: kit.Canvas, cx, cy, lamp):
    """Faceted tea glass in a metal holder (podstakannik) with a spoon; tea glows amber in the lamp."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    base = kit.ellipse_full(w, h, cx, cy + 22, 13, 5)
    bb.drop_shadow(cv, base, -8, 4, 1, KR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=20)
    # glass body above the holder (top ellipse = tea surface)
    body = kit.poly_mask_full(w, h, [(cx - 11, cy - 6), (cx + 11, cy - 6), (cx + 12, cy + 8), (cx - 12, cy + 8)])
    gt = 0.25 + 0.55 * pool + 0.12 * (np.abs(((xx - cx) % 4) - 2) < 0.6)
    cv.paint(body, np.clip(gt, 0, 1), KR['glass'])
    top = kit.ellipse_full(w, h, cx, cy - 6, 11, 4)
    cv.paint(top, np.clip(0.30 + 0.7 * pool, 0, 1), KR['tea'])
    rim = kit.outline_of(top)
    cv.paint(rim, np.clip(0.5 + 0.6 * pool, 0, 1), KR['glass'])
    # holder: filigree cylinder + handle on the left
    hold = kit.poly_mask_full(w, h, [(cx - 13, cy + 6), (cx + 13, cy + 6), (cx + 13, cy + 22), (cx - 13, cy + 22)])
    ht = 0.25 + 0.55 * pool + 0.25 * ((xx - cx) > 4) * 0 + np.where(((xx + yy) % 5) == 0, 0.16, 0.0)
    cv.paint(hold, np.clip(ht, 0, 1), KR['metal'])
    band = hold & ((np.abs(yy - (cy + 8)) < 1) | (np.abs(yy - (cy + 20)) < 1))
    cv.paint(band, np.clip(0.5 + 0.5 * pool, 0, 1), KR['metal'])
    hb = kit.ellipse_full(w, h, cx - 16, cy + 13, 5, 6) & ~kit.ellipse_full(w, h, cx - 16, cy + 13, 2.5, 3.5)
    cv.paint(hb & (xx < cx - 13), np.clip(0.3 + 0.5 * pool, 0, 1), KR['metal'])
    # spoon
    cv.line(cx + 4, cy - 7, cx + 10, cy - 20, KR['metal'][8])
    cv.line(cx + 5, cy - 7, cx + 11, cy - 20, KR['metal'][5])
    cv.px(cx + 4, cy - 6, KR['tea'][4])
    a = cv.alpha()


def ledger_pages(cv: kit.Canvas, lamp, hist_overlay=None):
    """Open freight ledger: ruled columns, pencil entries, the red C-17 line."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    for q in (LEDGER_L, LEDGER_R):
        m = kit.poly_mask_full(w, h, q)
        if q is LEDGER_L:
            outer = kit.poly_mask_full(w, h, [(q[0][0] - 3, q[0][1] - 2), (LEDGER_R[1][0] + 3, LEDGER_R[1][1] - 2),
                                            (LEDGER_R[2][0] + 3, LEDGER_R[2][1] + 3), (q[3][0] - 3, q[3][1] + 3)])
            bb.drop_shadow(cv, outer, -6, 4, 1, KR['desk'], lamp, blur=1)
            cv.paint(outer, np.clip(0.10 + 0.6 * lamp.pool(xx, yy, lift=3), 0, 1), KR['cover'])
        pool = lamp.pool(xx, yy, lift=4)
        gutter = np.abs(xx - q[1][0] if q is LEDGER_L else xx - q[0][0])
        tone = 0.08 + 0.95 * pool - 0.25 * np.clip(1.0 - gutter / 10.0, 0, 1)
        cv.paint(m, np.clip(tone, 0, 1), KR['ledger'])
    rule = KR['ledger'][3]
    for q in (LEDGER_L, LEDGER_R):
        for k in range(1, 12):
            v = k / 12.0
            a = bb.quad_map(q, 0.04, v)
            b2 = bb.quad_map(q, 0.96, v)
            cv.line(a[0], a[1], b2[0], b2[1], rule if k % 4 else KR['ledger'][2])
        for u in (0.18, 0.62, 0.80):
            a = bb.quad_map(q, u, 0.04)
            b2 = bb.quad_map(q, u, 0.96)
            cv.line(a[0], a[1], b2[0], b2[1], KR['ledger'][2])
    rng = np.random.default_rng(kit.seed_of('ledger_entries'))
    pen = [KR['ledger'][1], KR['ledger'][2]]
    for q, rows in ((LEDGER_L, range(1, 11)), (LEDGER_R, range(1, 7))):
        for k in rows:
            v = k / 12.0 + 0.04
            for (u0, u1) in ((0.05, 0.16), (0.20, 0.58), (0.64, 0.78), (0.82, 0.94)):
                n = int((u1 - u0) * 100 * rng.uniform(0.4, 1.0))
                for i in range(n):
                    if rng.random() < 0.25:
                        continue
                    x, y = bb.quad_map(q, u0 + i * 0.0095, v)
                    cv.px(x, y + (rng.random() < 0.3) * -1, pen[int(rng.random() < 0.2)])
    # the C-17 line (right page, row 7): red stamp box + red letters
    v = 7 / 12.0 + 0.04
    a = bb.quad_map(LEDGER_R, 0.62, v - 0.035)
    b2 = bb.quad_map(LEDGER_R, 0.94, v + 0.04)
    cv.rect(int(a[0]), int(a[1]), int(b2[0] - a[0]), int(b2[1] - a[1]), KR['red'][3])
    cv.rect(int(a[0]) + 1, int(a[1]) + 1, int(b2[0] - a[0]) - 2, int(b2[1] - a[1]) - 2, KR['ledger'][6])
    tm = kit.text_mask('C-17', kit.FONT3)
    kit.blit_mask(cv.c, tm, int(a[0]) + 3, int(a[1]) + 2, KR['red'][3])
    for i in range(30):
        x, y = bb.quad_map(LEDGER_R, 0.20 + i * 0.013, v)
        if i % 4:
            cv.px(x, y, KR['ledger'][1])


def morse_key(cv: kit.Canvas, cx, cy, lamp):
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    base = kit.poly_mask_full(w, h, [(cx - 22, cy - 6), (cx + 22, cy - 6), (cx + 24, cy + 8), (cx - 24, cy + 8)])
    bb.drop_shadow(cv, base, -6, 3, 1, KR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=4)
    cv.paint(base, np.clip(0.18 + 0.7 * pool, 0, 1), KR['desk'])
    cv.paint(base & (yy > cy + 5), np.clip(0.08 + 0.4 * pool, 0, 1), KR['desk'])
    lever = kit.poly_mask_full(w, h, [(cx - 18, cy - 2), (cx + 12, cy - 4), (cx + 12, cy - 1), (cx - 18, cy + 1)])
    cv.paint(lever, np.clip(0.35 + 0.7 * pool, 0, 1), KR['brass'])
    knob = kit.ellipse_full(w, h, cx - 20, cy - 2, 5, 4)
    cv.paint(knob, np.clip(0.12 + 0.4 * pool, 0, 1), KR['metal'])
    cv.px(cx - 22, cy - 4, KR['metal'][7])
    for sx in (cx + 4, cx + 14):
        cv.ellipse(sx, cy + 3, 2, 1.5, KR['brass'][5])
    cv.line(cx + 22, cy + 2, cx + 60, cy - 30, KR['metal'][2])


def waybills(cv: kit.Canvas, x0, y0, lamp):
    for k in range(3):
        q = [(x0 + k * 3, y0 - k * 2), (x0 + 58 + k * 2, y0 - 3 - k * 2), (x0 + 60 + k, y0 + 40 - k * 2),
             (x0 + 1 + k, y0 + 42 - k * 2)]
        bb.sheet(cv, q, KR['paper'], lamp, base=0.05, gain=0.9, shadow=(k == 0), desk_ramp=KR['desk'], lift=2 + k)
        for r in range(4, 38, 5):
            a = bb.quad_map(q, 0.1, r / 42.0)
            b2 = bb.quad_map(q, 0.8, r / 42.0)
            if k == 2:
                cv.line(a[0], a[1], b2[0], b2[1], KR['paper'][3])


def plaque(hist: bool, lamp) -> np.ndarray:
    """Enamel ministry plate on the wall: emblem + 'МПС' (hist: star, hammer & sickle; else gear-and-wheat)."""
    rgba = np.zeros((H, W, 4), np.uint8)
    cv = kit.Canvas(W, H)
    x0, y0 = V(392, 52)
    m = np.zeros((H, W), bool)
    m[y0:y0 + 26, x0:x0 + 22] = True
    xx, yy = cv.grid()
    t = 0.18 + 0.7 * lamp.pool(xx, yy + 120)
    cv.paint(m, np.clip(t, 0, 1), KR['red'])
    cv.c[kit.outline_of(m)] = KR['metal'][5]
    em = kit.soviet_emblem(hist)
    kit.blit_mask(cv.c, em, x0 + (22 - em.shape[1]) // 2, y0 + 3, pg.hx('#F0C487'))
    tm = kit.text_mask('МПС', kit.FONT3)
    kit.blit_mask(cv.c, tm, x0 + (22 - tm.shape[1]) // 2, y0 + 19, pg.hx('#F0C487'))
    return cv.c


def ledger_stamp(hist: bool, lamp) -> np.ndarray:
    rgba = np.zeros((H, W, 4), np.uint8)
    st = kit.round_stamp(30, kit.soviet_emblem(hist), kit.seed_of('k_stamp'))
    x, y = bb.quad_map(LEDGER_L, 0.66, 0.66)
    kit.ink(rgba, st, int(x - 15), int(y - 15), KR['stamp'] + [pg.hx('#C8503C')], lamp, wear=0.12,
            seed=kit.seed_of('k_stamp_wear'), base=0.05, gain=1.0)
    return rgba


def k_close_base(ext: np.ndarray):
    cv = kit.Canvas(W, H, 'k_close')
    lamp = LAMP_K
    bb.wall(cv, V(528, 70), DESK_Y, KR['wall'], 'k_close_wall', halo_r=130, base=0.20, stripes=1000)
    # painted wainscot line + a timetable sheet pinned to the wall
    cv.rect(0, V(0, 84)[1], W, 2, KR['wall'][2])
    tt = kit.poly_mask_full(W, H, [V(300, 48), V(352, 48), V(352, 86), V(300, 86)])
    xx, yy = cv.grid()
    cv.paint(tt, np.clip(0.1 + 0.75 * lamp.pool(xx, yy + 110), 0, 1), KR['paper'])
    for r in range(52, 84, 3):
        cv.line(*V(304, r), *V(348, r), KR['paper'][3])
    cv.rect(*V(324, 46), 2, 2, KR['brass'][4])
    bb.desk_wood(cv, lamp, DESK_Y, KR['desk'][:10], 'k_close_desk', plank=26, power=0.82)
    cv.rect(0, DESK_Y - 1, W, 1, KR['wall'][0])
    panes = bb.window_frame(cv, *WIN_K, KR['wall'], lamp, mull_x=V(120, 0)[0], transom_y=V(0, 40)[1], sill=7)
    # front edge of the desk and the drawer front with a brass keyhole
    fe = (yy >= FRONT_Y) & (yy < FRONT_Y + 3)
    cv.paint(fe, np.clip(0.2 + 0.9 * lamp.pool(xx, yy - 20), 0, 1), KR['desk'])
    below = yy >= FRONT_Y + 3
    cv.paint(below, np.clip(0.05 + 0.25 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    dr = (xx >= V(250, 0)[0]) & (xx < V(450, 0)[0]) & (yy >= FRONT_Y + 5) & (yy < FRONT_Y + 26)
    cv.paint(dr, np.clip(0.10 + 0.5 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    cv.c[kit.outline_of(dr)] = KR['desk'][1]
    waybills(cv, *V(40, 196), lamp)
    tea_glass(cv, *GLASS_C, lamp)
    morse_key(cv, *V(232, 140), lamp)
    cold_patch_k(cv, [V(0, 116), V(130, 116), V(100, 282), V(-30, 282)])
    cold_patch_k(cv, [V(140, 116), V(250, 116), V(236, 282), V(118, 282)])
    glass = np.zeros((H, W, 4), np.uint8)
    bay = kit.bayer_full(W, H)
    x0, y0, x1, y1 = WIN_K
    fd = np.minimum.reduce([xx - max(x0, 0), x1 - xx, yy - max(y0, 0), y1 - yy])
    frost = panes & (fd < 14) & (bay < np.clip(1.0 - fd / 14.0, 0, 1) * 0.6)
    glass[frost] = pg.hx('#4A675C')
    glass[frost & (fd < 5)] = pg.hx('#7E8E8C')
    refl = panes & (np.abs((xx - x0) * 0.8 - (yy - y0) - 30) < 1.0) & ((yy - y0) < 70)
    glass[refl & (bay < 0.5)] = pg.hx('#26403F')
    lr = V(196, 60)
    glass[panes & ((((xx - lr[0]) ** 2) / 16 + ((yy - lr[1]) ** 2) / 4) < 1)] = pg.hx('#F0C487')
    return {'base': cv.c, 'glass': glass, 'panes': panes}


def ledger_layer(lamp=LAMP_K) -> np.ndarray:
    cv = kit.Canvas(W, H)
    ledger_pages(cv, lamp)
    return cv.c
