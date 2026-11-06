"""cine_finale_berlin -- Berlin shots of the X1 finale montage (owner: trans-finale).

Shots (assets/cinematics/finale/b_*):
  ext        night exterior shared by every Berlin window: violet sky, floodlit Great Hall dome, snowy
             tenement roofs with a few lit windows (one painting, seen through different windows at 1:1)
  b_wide     Konrad's drafting room at night (window right = east, towards Karsk), lamp, clock, his desk
  b_close    the desk from above: architect's lamp, typewriter, plans, ashtray, Konrad's coat
  b_window   insert: snow against the window, the dome beyond
All art is original and procedural (deterministic), drawn at 1:1 on the archive/berlin palettes.
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import pg

BR = kit.BR
W, H = 680, 380            # set size (camera drifts inside it; visible window 640x360, letterbox 46..314)


# ------------------------------------------------------------------------------------------- exterior
def exterior(w: int = 720, h: int = 400) -> np.ndarray:
    """Night view east over Berlin roofs to the floodlit Great Hall.  Returns RGBA (h, w)."""
    cv = kit.Canvas(w, h, 'ext')
    xx, yy = cv.grid()
    bay = kit.bayer_full(w, h)
    rng = np.random.default_rng(kit.seed_of('ext_berlin'))
    sky_r = BR['sky'] + [pg.hx('#57494D')]
    sky_t = np.clip(yy / (h * 0.80), 0, 1) ** 1.7 * 0.78
    glow = np.exp(-(((xx - w * 0.5) / (w * 0.6)) ** 2) - (((yy - h * 0.66) / (h * 0.26)) ** 2)) * 0.26
    cv.paint(np.ones((h, w), bool), np.clip(sky_t + glow, 0, 1), sky_r)
    # thin, low cloud strata lit from below by the city
    cl = kit.Canvas(w, h)
    pg.clouds(cl, int(h * 0.12), int(h * 0.30), [pg.hx(c) for c in ('#1B1520', '#211623', '#2A2130')],
              seed=kit.seed_of('ext_clouds'), count=5, min_w=140, max_w=320, light=(0.0, 0.95, 0.3),
              ambient=0.45)
    sel = cl.c[..., 3] > 0
    cv.c[sel] = cl.c[sel]
    cx = w * 0.5
    base_y = h * 0.60                  # springing line of the dome (top of the drum cornice)
    rx, ry = 96.0, 64.0
    drum_h = 34
    foot = base_y + drum_h
    # searchlight beams rising behind the hall ("Lichtdom" of the regime's architecture)
    for k, bx in enumerate((cx - 150, cx - 112, cx + 112, cx + 150)):
        ang = (-0.10, -0.05, 0.05, 0.10)[k]
        Lb = foot - 10
        x1 = bx + math.sin(ang) * Lb
        poly = [(bx - 1.5, foot), (bx + 1.5, foot), (x1 + 5, foot - Lb), (x1 - 5, foot - Lb)]
        m = kit.poly_mask_full(w, h, poly)
        fade = np.clip((yy - (foot - Lb)) / Lb, 0, 1) ** 1.3
        sel = m & (bay < 0.15 + 0.55 * fade)
        beam = kit.tone_to_ramp(np.clip(sky_t + glow + 0.16 + 0.22 * fade, 0, 1), sky_r + [pg.hx('#6E6A73')])
        cv.c[sel] = beam[sel]
    # dome
    dm = kit.ellipse_full(w, h, cx, base_y, rx, ry) & (yy < base_y)
    u = (xx - cx) / rx
    v = (base_y - yy) / ry
    nz = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
    flood = np.clip(1.0 - v * 1.6, 0, 1) ** 1.8
    rim = np.clip(-u, 0, 1) ** 3 * 0.10 * (v > 0.2)
    tone = 0.06 + 0.45 * flood * (0.6 + 0.4 * nz) + 0.10 * nz * (1 - v) + rim
    lon = np.arcsin(np.clip(u / np.sqrt(np.clip(1 - v * v, 1e-4, 1)), -1, 1))
    rib = (np.abs(((lon / (math.pi / 14)) % 1.0) - 0.5) < 0.07) & (v < 0.85)
    tone = np.where(rib & dm, tone + 0.07 + 0.10 * flood, tone)
    cv.paint(dm, np.clip(tone, 0, 1), BR['patina'])
    # warm floodlight on the lowest band of the dome
    wb = dm & (v < 0.16)
    wt = np.clip(1.0 - v / 0.16, 0, 1)
    wcol = kit.tone_to_ramp(np.clip(0.15 + 0.5 * wt * (0.4 + 0.6 * nz), 0, 1), BR['glow'][:6])
    sel = wb & (bay < wt * 0.8)
    cv.c[sel] = wcol[sel]
    # snow on the upper ribs
    cv.c[dm & rib & (v > 0.6) & (bay < 0.4)] = pg.hx('#443B43')
    # lantern, globe and eagle on the crown
    lt = base_y - ry
    cv.rect(int(cx - 6), int(lt - 9), 12, 10, pg.hx('#1E2E2C'))
    for k in (-4, -1, 2):
        cv.rect(int(cx + k), int(lt - 8), 1, 7, pg.hx('#2C4440'))
    cv.rect(int(cx - 7), int(lt - 10), 14, 1, pg.hx('#3E5D55'))
    cv.ellipse(cx, lt - 14, 4, 4, pg.hx('#2C4440'))
    cv.px(cx - 2, lt - 16, pg.hx('#3E5D55'))
    em = kit.eagle_mask('small')
    kit.blit_mask(cv.c, em, int(cx - em.shape[1] / 2), int(lt - 18 - em.shape[0]), pg.hx('#1E2E2C'))
    # drum: cornice + colonnade in floodlight
    dx0, dx1 = int(cx - rx - 8), int(cx + rx + 8)
    stone = BR['stone'] + [pg.hx('#AE8A6C'), pg.hx('#E5945A')]
    cv.rect(dx0 - 2, int(base_y) - 2, dx1 - dx0 + 4, 3, pg.hx('#5F4A40'))
    cv.rect(dx0 - 2, int(base_y) - 2, dx1 - dx0 + 4, 1, pg.hx('#94735C'))
    for x in range(dx0, dx1):
        uu = (x - cx) / (rx + 8)
        shade = 1.0 - abs(uu) ** 2 * 0.55
        pil = ((x - dx0) % 7) < 3
        for y in range(int(base_y) + 1, int(foot)):
            ty = (y - base_y) / drum_h
            t = (0.22 + 0.72 * ty) * shade * (1.0 if pil else 0.5)
            cv.c[y, x] = kit.tone_to_ramp(np.array([[t]], np.float32), stone, x, y)[0, 0]
    # floodlight pool and haze at the foot of the hall
    ft = np.clip(1.0 - np.abs(yy - (foot + 4)) / 16.0, 0, 1) * np.clip(1 - (np.abs(xx - cx) / (rx + 60)) ** 2, 0, 1)
    gl = kit.tone_to_ramp(np.clip(ft * 0.8, 0, 1), BR['glow'][:5])
    sel = (ft > 0.04) & (bay < ft * 0.9)
    cv.c[sel] = gl[sel]
    # --- roofs: two rows of tenements, few lit windows (it is nearly midnight)
    roofs = kit.Canvas(w, h)
    rows = ((int(h * 0.86), BR['violet'][1:4], 22, 40, 0.07), (int(h * 0.99), BR['violet'][0:3], 30, 58, 0.11))
    for row, (ybase, col_r, hmin, hmax, lit_p) in enumerate(rows):
        x = -int(rng.integers(0, 40))
        while x < w:
            bw = int(rng.integers(46, 100))
            bh = int(rng.integers(hmin, hmax))
            top = ybase - bh
            roofs.rect(x, top, bw, h - top, col_r[1])
            rh = int(rng.integers(7, 13))
            roofs.poly([(x - 1, top), (x + bw + 1, top), (x + bw - 4, top - rh), (x + 4, top - rh)], col_r[0])
            for _ in range(int(rng.integers(1, 3))):
                chx = x + int(rng.integers(6, max(7, bw - 8)))
                chh = int(rng.integers(4, 9))
                roofs.rect(chx, top - rh - chh, 4, chh + 2, col_r[0])
                roofs.rect(chx - 1, top - rh - chh, 6, 1, col_r[2])
            for wy in range(top + 6, h, 11):
                for wx in range(x + 4, x + bw - 5, 9):
                    r = rng.random()
                    if r < lit_p:
                        roofs.rect(wx, wy, 4, 6, pg.hx('#F0AE6E') if rng.random() < 0.6 else pg.hx('#D07744'))
                        roofs.rect(wx, wy + 4, 4, 2, pg.hx('#AF6C47'))
                    elif r < lit_p + 0.55:
                        roofs.rect(wx, wy, 4, 6, col_r[0])
            roofs.rect(x + bw - 1, top, 1, h - top, col_r[2])
            x += bw + int(rng.integers(0, 3))
    pg.snow_caps(roofs, [pg.hx('#6E6A73'), pg.hx('#8F8A92'), pg.hx('#B2ACB0')], depth=2,
                 seed=kit.seed_of('ext_roofsnow'), coverage=0.8)
    sel = roofs.c[..., 3] > 0
    cv.c[sel] = roofs.c[sel]
    for (y0, y1, sag) in ((h * 0.70, h * 0.67, 12), (h * 0.745, h * 0.72, 16)):
        pg.wire(cv, -5, y0, w + 5, y1, sag, pg.hx('#120C14'))
    cv.c[..., 3] = 255
    return cv.c


# ------------------------------------------------------------------------------------------- shared
def paste_exterior(dst: np.ndarray, ext: np.ndarray, ox: int, oy: int, region_mask: np.ndarray) -> None:
    """Copy the exterior into dst where region_mask is True; exterior pixel (x-ox, y-oy)."""
    h, w = dst.shape[:2]
    ys, xs = np.nonzero(region_mask)
    ex = np.clip(xs - ox, 0, ext.shape[1] - 1)
    ey = np.clip(ys - oy, 0, ext.shape[0] - 1)
    dst[ys, xs] = ext[ey, ex]


# ------------------------------------------------------------------------------------------- b_close
OX, OY = 20, 10                       # view (640x360 at camera home) -> set coordinates
LAMP_B = kit.Lamp(150 + OX, 168 + OY, 118, 150, depth=0.62, power=1.08, aim=(62, 52))
DESK_Y = 118 + OY                     # far edge of the desk (set coords)
WIN_B = (384 + OX, -10, 680 + 20, 112 + OY)   # window opening (x0, y0, x1, y1), set coords
EXT_OFF_CLOSE = (470 + OX - 360, 100 + OY - 240)


def V(x, y):
    return x + OX, y + OY


def desk_wood(cv: kit.Canvas, lamp: kit.Lamp, y0: int, ramp, seed: str, plank: int = 30, base=0.10,
              power=0.95):
    """Desk top seen from above: planks left-right, grain, lamp pool (dithered)."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    m = yy >= y0
    nz = pg.value_noise(w, h, 22, kit.seed_of(seed), octaves=3)
    grain = pg.value_noise(w, h, 5, kit.seed_of(seed + 'g'), octaves=2)
    pool = lamp.pool(xx, yy)
    rel = (yy - y0)
    plank_i = np.floor(rel / plank)
    seam = (np.abs(rel - plank_i * plank) < 1.0) & (rel > 1)
    # grain: long horizontal streaks, wavy
    streak = np.sin(xx / 37.0 + plank_i * 1.7 + nz * 6.0) * 0.5 + 0.5
    g = ((grain > 0.62) & (streak > 0.55)).astype(np.float32) * -0.06 + ((grain < 0.30) & (streak < 0.4)) * 0.04
    detail = np.clip(0.25 + 1.4 * pool, 0, 1)          # grain shows where the light is, calm in the dark
    tone = base + power * pool + (g + (nz - 0.5) * 0.06) * detail - 0.04 * (plank_i % 2)
    tone = np.where(seam, tone - 0.12, tone)
    cv.paint(m, np.clip(tone, 0, 1), ramp)
    # far edge highlight (lit rim of the desk)
    edge = (yy >= y0) & (yy < y0 + 1)
    et = np.clip(base + power * pool + 0.15, 0, 1)
    ecol = kit.tone_to_ramp(et, ramp)
    cv.c[edge] = ecol[edge]
    return pool


def wall(cv: kit.Canvas, lamp_pos, y1: int, ramp, seed: str, halo_r=110.0, base=0.20, stripes=9):
    w = cv.w
    xx, yy = cv.grid()
    m = yy < y1
    d = np.sqrt((xx - lamp_pos[0]) ** 2 + ((yy - lamp_pos[1]) * 1.2) ** 2) / halo_r
    halo = np.clip(1.0 - d, 0, 1) ** 1.8 * 0.42
    nz = pg.value_noise(cv.w, cv.h, 30, kit.seed_of(seed), octaves=3)
    stripe = ((np.floor(xx) % stripes) == 0) * -0.05
    tone = base + halo + (nz - 0.5) * 0.08 + stripe
    # shadow line under the ceiling / picture rail
    tone = np.where((yy > 30) & (yy < 33), tone - 0.07, tone)
    cv.paint(m, np.clip(tone, 0, 1), ramp)


def window_frame(cv: kit.Canvas, x0, y0, x1, y1, ramp, lamp, mull_x=None, transom_y=None, sill=8,
                 snow_ramp=None, frame=6):
    """Paints the window casing; leaves the panes transparent (alpha 0).  Returns the pane mask."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    outer = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    panes = (xx >= x0 + frame) & (xx < x1 - frame) & (yy >= y0 + frame) & (yy < y1 - frame)
    if mull_x is not None:
        panes &= ~((xx >= mull_x - 2) & (xx < mull_x + 2))
    if transom_y is not None:
        panes &= ~((yy >= transom_y - 2) & (yy < transom_y + 2))
    casing = outer & ~panes
    pool = lamp.pool(xx, yy + 40)
    tone = 0.10 + 0.55 * pool
    # bevel: inner edges lighter on the lamp side
    tone = np.where(casing & kit.dilate(panes, 1) & (xx < (x0 + x1) / 2), tone + 0.10, tone)
    cv.paint(casing, np.clip(tone, 0, 1), ramp)
    cv.c[panes] = 0
    # sill
    sy = y1
    sill_m = (xx >= x0 - 6) & (xx < x1 + 6) & (yy >= sy) & (yy < sy + sill)
    st = 0.14 + 0.7 * lamp.pool(xx, yy + 30) + np.where(yy < sy + 2, 0.12, 0.0)
    cv.paint(sill_m, np.clip(st, 0, 1), ramp)
    return panes


def lamp_architect(w, h, head, lamp_on=True, side='left'):
    """Black/brass architect's lamp: arm from off-frame, conical shade opening down-right.
    Returns (rgba, emission_mask).  head = shade centre."""
    cv = kit.Canvas(w, h)
    hx, hy = head
    met = BR['black']
    brass = BR['brass']
    # arm segments (from the upper-left off frame to the shade's knuckle)
    knuckle = (hx - 26, hy - 18)
    cv.line(knuckle[0] - 60, knuckle[1] - 70, knuckle[0], knuckle[1], met[3])
    cv.line(knuckle[0] - 59, knuckle[1] - 70, knuckle[0] + 1, knuckle[1], met[4])
    cv.line(knuckle[0] - 58, knuckle[1] - 72, knuckle[0] + 2, knuckle[1] - 2, met[2])
    cv.ellipse(knuckle[0], knuckle[1], 3, 3, brass[3])
    cv.px(knuckle[0] - 1, knuckle[1] - 1, brass[6])
    # springs along the arm
    for k in range(6):
        t = 0.2 + k * 0.1
        sx = knuckle[0] - 60 * (1 - t) + 4
        sy = knuckle[1] - 70 * (1 - t) - 2
        cv.px(sx, sy, brass[4])
    # neck to the shade
    cv.line(knuckle[0], knuckle[1], hx - 12, hy - 9, met[4])
    cv.line(knuckle[0], knuckle[1] + 1, hx - 12, hy - 8, met[2])
    # shade: cone, axis pointing down-right; drawn as a trapezoid with an elliptical rim
    ax, ay = 0.55, 0.83                  # axis direction (down-right)
    nxp, nyp = -ay, ax                   # perpendicular
    top_c = (hx - ax * 14, hy - ay * 14)
    rim_c = (hx + ax * 12, hy + ay * 12)
    r_top, r_rim = 7.0, 25.0
    poly = [(top_c[0] + nxp * r_top, top_c[1] + nyp * r_top), (rim_c[0] + nxp * r_rim, rim_c[1] + nyp * r_rim),
            (rim_c[0] - nxp * r_rim, rim_c[1] - nyp * r_rim), (top_c[0] - nxp * r_top, top_c[1] - nyp * r_top)]
    sm = kit.poly_mask_full(w, h, poly)
    xx, yy = cv.grid()
    # shading across the cone: lit edge on the upper-left (city glow is weak; the lamp is inside)
    across = ((xx - hx) * nxp + (yy - hy) * nyp) / r_rim
    along = ((xx - hx) * ax + (yy - hy) * ay) / 14.0
    tone = 0.42 + 0.30 * np.clip(across, -1, 1) + 0.12 * np.clip(along, -1, 1)
    tone = np.where(np.abs(across - 0.45) < 0.09, tone + 0.30, tone)        # specular streak (window side)
    tone = np.where(np.abs(across + 0.70) < 0.07, tone + 0.18, tone)
    cv.paint(sm, np.clip(tone, 0, 1), met)
    # warm bounce light on the lip of the shade
    lip = sm & (along > 0.55)
    cv.paint(lip, np.clip(0.35 + 0.3 * (along - 0.55), 0, 1), brass)
    # rim ellipse (opening) seen from above-right: the glowing inside
    rim_m = kit.ellipse_full(w, h, rim_c[0], rim_c[1], r_rim, 7.5)
    rot = np.zeros_like(rim_m)
    # rotate the ellipse to be perpendicular to the axis: approximate by masking with a rotated test
    dxr, dyr = xx - rim_c[0], yy - rim_c[1]
    u = dxr * nxp + dyr * nyp
    v = dxr * ax + dyr * ay
    rim_m = (u / r_rim) ** 2 + (v / 6.5) ** 2 <= 1.0
    em = np.zeros((h, w), bool)
    if lamp_on:
        inner = (u / (r_rim - 2)) ** 2 + (v / 4.6) ** 2 <= 1.0
        glow_t = np.clip(1.0 - np.sqrt((u / r_rim) ** 2 + (v / 6.5) ** 2), 0, 1)
        cv.paint(rim_m & ~inner, np.full((h, w), 0.55, np.float32), brass)
        cv.paint(inner, np.clip(0.55 + glow_t * 0.6, 0, 1), BR['amber'])
        bulb = (u / 6.0) ** 2 + ((v + 1.5) / 3.0) ** 2 <= 1.0
        cv.c[bulb] = pg.hx('#FFE3AA')
        em = inner | bulb
    else:
        inner = (u / (r_rim - 2)) ** 2 + (v / 4.6) ** 2 <= 1.0
        cv.paint(rim_m & ~inner, np.full((h, w), 0.4, np.float32), met)
        cv.paint(inner, np.full((h, w), 0.12, np.float32), met)
        bulb = (u / 6.0) ** 2 + ((v + 1.5) / 3.0) ** 2 <= 1.0
        cv.c[bulb] = pg.hx('#354448')
    # outline on the dark side
    a = cv.alpha()
    edge = kit.outline_of(a) & (xx > hx)
    cv.c[edge & sm] = met[0]
    return cv.c, em


# typewriter geometry (view coords)
TW = dict(x0=180, x1=320, back=176, front=214, face=232, strike=250, platen_y=150)
LEVER_TIP = V(TW['strike'] + 40 - 106, TW['platen_y'] + 14)     # set coords, carriage at the line start
OUT_TRAY = V(380, 226) + V(466, 266)                              # AUSGANG tray opening (x0, y0, x1, y1), set


def drop_shadow(cv: kit.Canvas, mask: np.ndarray, dx: int, dy: int, steps: int, ramp, lamp, blur: int = 1):
    """Darkens the desk under a shifted copy of mask (cast shadow away from the lamp)."""
    sh = kit.shift(mask, dx, dy)
    sh = kit.dilate(sh, blur) & ~mask
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy)
    core = kit.erode(sh, 1)
    bay = kit.bayer_full(cv.w, cv.h)
    t_core = np.clip(0.06 + 0.25 * pool, 0, 1)
    t_edge = np.clip(0.06 + 0.55 * pool, 0, 1)
    c1 = kit.tone_to_ramp(t_core, ramp)
    c2 = kit.tone_to_ramp(t_edge, ramp)
    edge = sh & ~core
    cv.c[core] = c1[core]
    sel = edge & (bay < 0.6)
    cv.c[sel] = c2[sel]


def typewriter_body(cv: kit.Canvas, lamp: kit.Lamp):
    x0, x1, back, front, face = TW['x0'], TW['x1'], TW['back'], TW['front'], TW['face']
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    blk = BR['black']
    # footprint shadow on the desk (cast down-right)
    foot = kit.poly_mask_full(w, h, [V(x0 - 6, 150), V(x1 + 6, 150), V(x1 + 2, face), V(x0 - 2, face)])
    drop_shadow(cv, foot, 12, 7, 2, BR['desk'], lamp, blur=2)
    pool = lamp.pool(xx, yy, lift=20)
    # side cheeks
    lc = kit.poly_mask_full(w, h, [V(x0 - 10, 150), V(x0 + 6, 150), V(x0 + 2, face), V(x0 - 6, face - 4)])
    cv.paint(lc, np.clip(0.18 + 0.55 * pool, 0, 1), blk)
    rc = kit.poly_mask_full(w, h, [V(x1 - 6, 150), V(x1 + 10, 150), V(x1 + 6, face - 4), V(x1 - 2, face)])
    cv.paint(rc, np.clip(0.08 + 0.25 * pool, 0, 1), blk)
    # typebar basket (dark well with radiating bars)
    bc = V(250, back + 1)
    well = kit.ellipse_full(w, h, bc[0], bc[1], 46, 18) & (yy < bc[1])
    cv.paint(well, np.full((h, w), 0.05, np.float32), blk)
    for k in range(-21, 22):
        a = math.pi * (0.5 + k / 46.0)
        ex = bc[0] + math.cos(a) * 44 * -1
        ey = bc[1] - abs(math.sin(a)) * 16
        col = blk[4] if k % 2 == 0 else blk[3]
        cv.line(bc[0] + (ex - bc[0]) * 0.35, bc[1] + (ey - bc[1]) * 0.35, ex, ey, col)
    cv.ellipse(bc[0], bc[1] - 2, 6, 3, blk[1])
    # keyboard deck
    deck = kit.poly_mask_full(w, h, [V(x0 + 6, back), V(x1 - 6, back), V(x1, front), V(x0, front)])
    dt = 0.14 + 0.62 * pool + (yy - (back + OY)) / (front - back) * 0.05
    cv.paint(deck, np.clip(dt, 0, 1), blk)
    # keys: 4 rows, staggered
    keyc = BR['cuff']
    for r in range(4):
        ky = back + 5 + r * 9
        kx0 = x0 + 16 + r * 3
        for kx in range(kx0, x1 - 16, 9):
            cx_, cy_ = V(kx, ky)
            rim = kit.ellipse_full(w, h, cx_ + 0.5, cy_ + 0.5, 3.2, 2.6)
            cap = kit.ellipse_full(w, h, cx_ + 0.5, cy_ + 0.0, 2.4, 1.8)
            pl = float(lamp.pool(np.float32(cx_), np.float32(cy_), lift=22))
            cv.c[rim] = blk[1]
            t = np.clip(0.18 + 0.85 * pl, 0, 1)
            cv.c[cap] = kit.tone_to_ramp(np.array([[t]], np.float32), keyc, dither=False)[0, 0]
            cv.px(cx_ - 1, cy_ - 1, kit.tone_to_ramp(np.array([[min(1, t + 0.2)]], np.float32), keyc, dither=False)[0, 0])
            cv.px(cx_, cy_ + 1, blk[3])
    sb = kit.poly_mask_full(w, h, [V(224, front - 7), V(276, front - 7), V(277, front - 3), V(223, front - 3)])
    cv.paint(sb, np.clip(0.2 + 0.7 * pool, 0, 1), keyc)
    # front face + chrome strip + nameplate
    face_m = kit.poly_mask_full(w, h, [V(x0, front), V(x1, front), V(x1 - 2, face), V(x0 + 2, face)])
    ft = 0.10 + 0.30 * pool
    cv.paint(face_m, np.clip(ft, 0, 1), blk)
    cv.paint(face_m & (yy < front + OY + 2), np.clip(ft + 0.25, 0, 1), blk)
    np_ = kit.poly_mask_full(w, h, [V(238, front + 6), V(262, front + 6), V(262, front + 9), V(238, front + 9)])
    cv.paint(np_, np.clip(0.3 + 0.6 * pool, 0, 1), BR['brass'])
    # outline (shadow side + bottom)
    body = lc | rc | deck | face_m | well
    edge = kit.outline_of(body) & ((xx > 250 + OX) | (yy > front + OY))
    cv.c[edge] = blk[0]


def carriage(w: int, h: int, lamp: kit.Lamp) -> np.ndarray:
    """Carriage at the start position (strike at the paper's left margin).  Moves as one sprite."""
    cv = kit.Canvas(w, h)
    xx, yy = cv.grid()
    blk = BR['black']
    met = BR['metal']
    py = TW['platen_y']
    cx = TW['strike'] + 40          # carriage centre at line start
    pool = lamp.pool(xx, yy, lift=34)
    # rail/back plate
    rail = kit.poly_mask_full(w, h, [V(cx - 98, py - 8), V(cx + 98, py - 8), V(cx + 98, py + 7), V(cx - 98, py + 7)])
    cv.paint(rail, np.clip(0.08 + 0.3 * pool, 0, 1), blk)
    # platen (rubber cylinder)
    pl = kit.poly_mask_full(w, h, [V(cx - 82, py - 6), V(cx + 82, py - 6), V(cx + 82, py + 4), V(cx - 82, py + 4)])
    across = (yy - (py - 1 + OY)) / 5.0
    pt = 0.06 + 0.42 * pool * np.clip(1.0 - np.abs(across + 0.4), 0, 1)
    cv.paint(pl, np.clip(pt, 0, 1), blk)
    hl = pl & (np.abs(yy - (py - 3.5 + OY)) < 0.6)
    cv.paint(hl, np.clip(0.35 + 0.6 * pool, 0, 1), blk)
    # knobs
    for kx in (cx - 92, cx + 92):
        k = kit.ellipse_full(w, h, *V(kx, py - 1), 7, 6)
        kt = 0.12 + 0.5 * pool + np.clip(-(xx - V(kx, 0)[0]) / 7, -1, 1) * 0.08
        cv.paint(k, np.clip(kt, 0, 1), blk)
        r_ = kit.ellipse_full(w, h, *V(kx, py - 1), 4, 3)
        cv.paint(r_, np.clip(kt + 0.15, 0, 1), met)
    # carriage return lever (chrome): from the left end of the carriage forward and to the left, towards
    # the typist, ending in a flat paddle for the fingers
    lx, ly = V(cx - 92, py - 3)
    tx, ty = LEVER_TIP
    cv.line(lx, ly, tx + 2, ty - 2, met[6])
    cv.line(lx, ly + 1, tx + 2, ty - 1, met[3])
    cv.line(lx + 1, ly, tx + 3, ty - 2, met[4])
    cv.ellipse(tx, ty, 3.5, 2.2, met[7])
    cv.px(tx - 1, ty - 1, met[8])
    cv.px(tx + 1, ty + 1, met[3])
    # paper bail with two rubber rollers (drawn over the paper)
    bail_y = py - 9
    cv.line(*V(cx - 60, bail_y), *V(cx + 60, bail_y), met[6])
    cv.line(*V(cx - 60, bail_y + 1), *V(cx + 60, bail_y + 1), met[3])
    for rx_ in (cx - 26, cx + 26):
        cv.rect(*V(rx_ - 3, bail_y - 1), 7, 3, blk[2])
        cv.px(*V(rx_ - 2, bail_y - 1), blk[5])
    # outline
    a = cv.alpha()
    edge = kit.outline_of(a)
    cv.c[edge & (yy > py + OY)] = blk[0]
    return cv.c


# ------------------------------------------------------------------------------------------- documents
def quad_map(quad, u, v):
    """Bilinear map of (u, v) in [0,1]^2 onto a quad [(tl), (tr), (br), (bl)]."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = quad
    top = (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
    bot = (x3 + (x2 - x3) * u, y3 + (y2 - y3) * u)
    return top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v


def sheet(cv: kit.Canvas, quad, ramp, lamp, base=0.08, gain=1.0, lift=1.0, curl=0.0, shadow=True,
          desk_ramp=None):
    """Paper sheet lying on the desk (quad in set coords).  Returns the mask."""
    w, h = cv.w, cv.h
    m = kit.poly_mask_full(w, h, quad)
    if shadow and desk_ramp is not None:
        drop_shadow(cv, m, 2, 2, 1, desk_ramp, lamp, blur=0)
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=lift)
    tone = base + gain * pool
    if curl:
        tone = tone + curl * np.clip((xx - quad[0][0]) / max(1, quad[1][0] - quad[0][0]) - 0.7, 0, 1)
    cv.paint(m, np.clip(tone, 0, 1), ramp)
    edge = kit.outline_of(m)
    et = np.clip(base + gain * pool - 0.18, 0, 1)
    ec = kit.tone_to_ramp(et, ramp, dither=False)
    sel = edge & ((yy > (quad[2][1] + quad[3][1]) / 2 - 2) | (xx > (quad[1][0] + quad[2][0]) / 2 - 2))
    cv.c[sel] = ec[sel]
    return m


def ink_line(cv: kit.Canvas, quad, pts_uv, col):
    pts = [quad_map(quad, u, v) for (u, v) in pts_uv]
    for a, b in zip(pts[:-1], pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], col)


def floor_plan(cv: kit.Canvas, quad, lamp, ink_ramp, corridor=True, red=None):
    """Blue-line (or pencil) floor plan: outer walls, rooms, the hidden corridor behind the second wall."""
    def col_at(u, v, k=0.0):
        x, y = quad_map(quad, u, v)
        t = float(np.clip(0.15 + 0.85 * lamp.pool(np.float32(x), np.float32(y)) + k, 0, 1))
        return kit.tone_to_ramp(np.array([[t]], np.float32), ink_ramp, int(x), int(y), dither=False)[0, 0]
    walls = [[(0.08, 0.12), (0.92, 0.12), (0.92, 0.86), (0.08, 0.86), (0.08, 0.12)],
             [(0.08, 0.45), (0.55, 0.45)], [(0.55, 0.12), (0.55, 0.62)], [(0.70, 0.12), (0.70, 0.86)],
             [(0.30, 0.45), (0.30, 0.86)], [(0.55, 0.62), (0.70, 0.62)]]
    for wl in walls:
        ink_line(cv, quad, wl, col_at(*wl[0]))
    for (u, v) in ((0.18, 0.45), (0.40, 0.45), (0.62, 0.62)):
        a = quad_map(quad, u, v)
        b = quad_map(quad, u + 0.04, v - 0.08)
        cv.line(a[0], a[1], b[0], b[1], col_at(u, v, -0.1))
    ink_line(cv, quad, [(0.08, 0.93), (0.92, 0.93)], col_at(0.5, 0.93, -0.15))
    for u in (0.08, 0.30, 0.55, 0.70, 0.92):
        a = quad_map(quad, u, 0.91)
        b = quad_map(quad, u, 0.95)
        cv.line(a[0], a[1], b[0], b[1], col_at(u, 0.93, -0.15))
    if corridor:
        for k in range(0, 10, 2):
            v0, v1 = 0.14 + k * 0.07, 0.14 + (k + 1) * 0.07
            for uu in (0.745, 0.79):
                a = quad_map(quad, uu, v0)
                b = quad_map(quad, uu, v1)
                cv.line(a[0], a[1], b[0], b[1], col_at(uu, v0, -0.05))
    if red is not None:
        cxu, cyu = 0.77, 0.50
        pts = [quad_map(quad, cxu + 0.12 * math.cos(a), cyu + 0.22 * math.sin(a))
               for a in np.linspace(0, 2 * math.pi, 40)]
        for a, b in zip(pts[:-1], pts[1:]):
            cv.line(a[0], a[1], b[0], b[1], red)
        tx, ty = quad_map(quad, 0.58, 0.70)
        kit.blit_mask(cv.c, kit.text_mask('C-17', kit.FONT3), int(tx), int(ty), red)


def ashtray(cv: kit.Canvas, cx, cy, lamp):
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    base = kit.ellipse_full(w, h, cx, cy + 3, 15, 7)
    drop_shadow(cv, base, 6, 3, 1, BR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=4)
    cv.paint(base, np.clip(0.10 + 0.6 * pool, 0, 1), BR['black'])
    rim = kit.ellipse_full(w, h, cx, cy, 15, 7)
    inner = kit.ellipse_full(w, h, cx, cy + 0.5, 11, 4.6)
    cv.paint(rim & ~inner, np.clip(0.30 + 0.7 * pool, 0, 1), BR['metal'])
    cv.paint(inner, np.clip(0.05 + 0.35 * pool, 0, 1), BR['black'])
    rng = np.random.default_rng(kit.seed_of('ash'))
    for _ in range(14):
        cv.px(cx + rng.uniform(-8, 8), cy + rng.uniform(-2, 3), BR['smoke'][int(rng.integers(2, 5))])
    cv.line(cx - 6, cy + 1, cx - 1, cy + 2, BR['cuff'][4])
    cv.px(cx - 6, cy + 1, BR['desk'][7])
    cv.line(cx + 6, cy - 2, cx + 17, cy - 5, BR['cuff'][5])
    cv.line(cx + 6, cy - 1, cx + 17, cy - 4, BR['cuff'][3])
    cv.px(cx + 5, cy - 2, pg.hx('#D07744'))
    cv.px(cx + 5, cy - 1, pg.hx('#AF6C47'))
    return (cx + 5, cy - 2)


def out_tray(cv: kit.Canvas, x0, y0, x1, y1, lamp, label='AUSGANG', papers=3):
    """Wooden letter tray (EINGANG / AUSGANG) with a few papers; set coords of the top opening."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    body = kit.poly_mask_full(w, h, [(x0, y0), (x1, y0), (x1 + 2, y1 + 8), (x0 - 2, y1 + 8)])
    drop_shadow(cv, body, 8, 4, 1, BR['desk'], lamp, blur=1)
    pool = lamp.pool(xx, yy, lift=6)
    inside = kit.poly_mask_full(w, h, [(x0 + 3, y0 + 2), (x1 - 3, y0 + 2), (x1 - 2, y1), (x0 + 2, y1)])
    cv.paint(body, np.clip(0.12 + 0.75 * pool, 0, 1), BR['desk'])
    cv.paint(inside, np.clip(0.06 + 0.4 * pool, 0, 1), BR['desk'])
    for k in range(papers):
        pq = [(x0 + 6 + k, y0 + 4 + k), (x1 - 8 + k, y0 + 3 + k), (x1 - 6 + k, y1 - 3), (x0 + 5 + k, y1 - 2)]
        sheet(cv, pq, BR['paper'], lamp, base=0.02, gain=0.55, shadow=False)
    lip = kit.poly_mask_full(w, h, [(x0 - 2, y1), (x1 + 2, y1), (x1 + 2, y1 + 8), (x0 - 2, y1 + 8)])
    cv.paint(lip, np.clip(0.10 + 0.6 * pool, 0, 1), BR['desk'])
    lab = kit.text_mask(label, kit.FONT3)
    lx = int((x0 + x1) / 2 - lab.shape[1] / 2)
    kit.blit_mask(cv.c, lab, lx, int(y1 + 2), BR['paper'][3])


def b_close_base(ext: np.ndarray):
    """Static layers of the Berlin desk close-up.  Returns dict of RGBA arrays + metadata."""
    cv = kit.Canvas(W, H, 'b_close')
    lamp = LAMP_B
    wall(cv, V(112, 70), DESK_Y, BR['wall'], 'b_close_wall', halo_r=120, base=0.16)
    calendar(cv, *V(300, 62), lamp)
    pinned_drawing(cv, *V(196, 54), lamp)
    desk_wood(cv, lamp, DESK_Y, BR['desk'], 'b_close_desk')
    cv.rect(0, DESK_Y - 1, W, 1, BR['wall'][0])
    panes = window_frame(cv, *WIN_B, BR['desk'], lamp, mull_x=512 + OX, transom_y=44 + OY, sill=7)
    # cold light from the window falling across the right of the desk (mullion shadow splits it)
    folders(cv, *V(540, 152), lamp, n=4)
    telephone(cv, *V(430, 182), lamp)
    import cine_finale_props as props
    props.rolled_plans(cv, 596, 238, lamp, n=3, seed='b_close_rolls')
    props.felt_hat(cv, 532, 282, lamp)                 # Konrad's hat, put down on the desk (cold window light)
    cold_patch(cv, [V(392, 128), V(500, 128), V(536, 340), V(378, 340)])
    cold_patch(cv, [V(522, 128), V(660, 128), V(700, 340), V(560, 340)])
    plan_q = [V(14, 192), V(180, 186), V(186, 304), V(18, 312)]
    sheet(cv, plan_q, BR['paper'], lamp, base=0.06, gain=1.0, desk_ramp=BR['desk'])
    floor_plan(cv, plan_q, lamp, [pg.hx(c) for c in ('#1D2A3A', '#2B3C50', '#3E546B', '#58718A')])
    cv.line(*V(206, 262), *V(240, 246), BR['brass'][3])
    cv.line(*V(206, 263), *V(240, 247), BR['brass'][1])
    cv.px(*V(241, 246), BR['black'][1])
    xx, yy = cv.grid()
    ruler = kit.poly_mask_full(W, H, [V(300, 300), V(392, 296), V(392, 300), V(300, 304)])
    cv.paint(ruler, np.clip(0.2 + 0.8 * lamp.pool(xx, yy), 0, 1), BR['brass'])
    for k in range(304, 392, 6):
        a = V(k, 300 - (k - 300) * 4 / 92)
        cv.px(a[0], a[1], BR['brass'][1])
    typewriter_body(cv, lamp)
    tip = ashtray(cv, *V(352, 196), lamp)
    cup = props.cup_saucer(cv, 392, 236, lamp)          # cold coffee, still steaming a little
    props.pencil_cup(cv, 182, 166, lamp)
    out_tray(cv, *V(22, 128), *V(146, 180), lamp, label='EINGANG', papers=4)
    out_tray(cv, *OUT_TRAY, lamp, label='AUSGANG', papers=1)          # front right, within his reach
    glass = np.zeros((H, W, 4), np.uint8)
    bay = kit.bayer_full(W, H)
    x0, y0, x1, y1 = WIN_B
    frost_d = np.minimum.reduce([xx - x0, x1 - xx, yy - max(y0, 0), y1 - yy])
    frost = panes & (frost_d < 12) & (bay < np.clip(1.0 - frost_d / 12.0, 0, 1) * 0.55)
    glass[frost] = pg.hx('#57494D')
    glass[frost & (frost_d < 4)] = pg.hx('#6E6A73')
    refl = panes & (np.abs((xx - x0) - (yy - y0) * 0.9 - 60) < 1.0) & ((yy - y0) < 70)
    glass[refl & (bay < 0.5)] = pg.hx('#443B43')
    lr = V(430, 60)
    lampref = panes & ((((xx - lr[0]) ** 2) / 16 + ((yy - lr[1]) ** 2) / 4) < 1)
    glass[lampref] = pg.hx('#F4BA81')
    return {'base': cv.c, 'glass': glass, 'panes': panes, 'tip': tip, 'plan_q': plan_q, 'cup': cup}


def stamp_overlay(plan_q, lamp, hist: bool) -> np.ndarray:
    rgba = np.zeros((H, W, 4), np.uint8)
    em = kit.state_emblem(21, hist)
    st = kit.round_stamp(34, em, kit.seed_of('b_stamp'))
    x, y = quad_map(plan_q, 0.80, 0.62)
    kit.ink(rgba, st, int(x - 17), int(y - 17), BR['stamp'] + [pg.hx('#6E6A73')], lamp, wear=0.10,
            seed=kit.seed_of('b_stamp_wear'), base=0.05, gain=1.1)
    return rgba


def copy_sheet(lamp, quad, state: str = 'flat') -> np.ndarray:
    """Tracing-paper copy Konrad made: pencil plan + red ring and C-17.
    state: flat / lift / half / quarter.  Returns RGBA (set size)."""
    cv = kit.Canvas(W, H)
    pencil = [pg.hx(c) for c in ('#354448', '#4A5A5B', '#62716E')]
    if state == 'flat':
        sheet(cv, quad, BR['tracing'], lamp, base=0.04, gain=0.95, shadow=False)
        floor_plan(cv, quad, lamp, pencil, corridor=True, red=pg.hx('#A8382E'))
    elif state == 'lift':
        l = [quad[0], quad_map(quad, 0.5, 0), quad_map(quad, 0.5, 1), quad[3]]
        sheet(cv, l, BR['tracing'], lamp, base=0.04, gain=0.95, shadow=False)
        floor_plan(cv, l, lamp, pencil, corridor=False)
        tl = quad_map(quad, 0.5, 0)
        bl = quad_map(quad, 0.5, 1)
        r = [tl, (tl[0] + 14, tl[1] - 20), (bl[0] + 14, bl[1] - 18), bl]
        sheet(cv, r, BR['tracing'], lamp, base=0.15, gain=1.0, shadow=False, lift=18)
    elif state == 'half':
        l = [quad[0], quad_map(quad, 0.52, 0), quad_map(quad, 0.52, 1), quad[3]]
        sheet(cv, l, BR['tracing'], lamp, base=0.08, gain=0.95, shadow=False, lift=2)
        a, b = quad_map(quad, 0.52, 0), quad_map(quad, 0.52, 1)
        cv.line(a[0] - 1, a[1], b[0] - 1, b[1], BR['tracing'][6])
    else:
        l = [quad[0], quad_map(quad, 0.52, 0), quad_map(quad, 0.52, 0.52), quad_map(quad, 0, 0.52)]
        sheet(cv, l, BR['tracing'], lamp, base=0.10, gain=0.95, shadow=False, lift=3)
        a, b = quad_map(quad, 0, 0.52), quad_map(quad, 0.52, 0.52)
        cv.line(a[0], a[1] - 1, b[0], b[1] - 1, BR['tracing'][6])
        cv.line(a[0], a[1], b[0], b[1], BR['tracing'][2])
    return cv.c


def composite(layers, w=W, h=H):
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 3] = 255
    for arr, x, y in layers:
        kit.over(out, arr, x, y)
    return out


def ext_layer(ext: np.ndarray, off, w=W, h=H) -> np.ndarray:
    """Exterior positioned for a set (offset = set position of exterior pixel 0,0)."""
    out = np.zeros((h, w, 4), np.uint8)
    ox, oy = off
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(w, ox + ext.shape[1]), min(h, oy + ext.shape[0])
    out[y0:y1, x0:x1] = ext[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return out


# ------------------------------------------------------------------------------------------- b_close extras
def cold_patch(cv: kit.Canvas, quad, ramp_from=None, strength=0.55, seed='cold', gain=1.25, lift=0.03):
    """Cold window light on the desk: a luminance-matched palette swap towards the cold blue ramp
    (texture preserved, no screen-door), with a 2 px ordered-dither border."""
    w, h = cv.w, cv.h
    m = kit.poly_mask_full(w, h, quad)
    bay = kit.bayer_full(w, h)
    core = kit.erode(m, 2)
    edge = m & ~core
    cold = [pg.hx(c) for c in ('#04090D', '#06151D', '#0B1C24', '#14272B', '#1A2A2E', '#24373A', '#2B3C50',
                               '#354448', '#3E546B', '#4A5A5B', '#58718A', '#62716E', '#7A93A8')]
    cl = np.array([0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in cold], np.float32) / 255.0
    rgb = cv.c[..., :3].astype(np.float32) / 255.0
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    target = lum * gain + lift
    idx = np.abs(target[..., None] - cl[None, None, :]).argmin(-1)
    carr = np.stack(cold)
    col = carr[idx]
    sel = (core | (edge & (bay < 0.5))) & (cv.c[..., 3] > 0)
    cv.c[sel] = col[sel]
    return m


def telephone(cv: kit.Canvas, cx, cy, lamp):
    """Black bakelite desk telephone (W48-like, original drawing), lit by the cold window light."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    blk = BR['black']
    body = kit.poly_mask_full(w, h, [(cx - 20, cy - 4), (cx + 20, cy - 4), (cx + 25, cy + 14), (cx - 25, cy + 14)])
    drop_shadow(cv, body, 5, 3, 1, BR['desk'], lamp, blur=1)
    tone = 0.18 + 0.25 * np.clip((cx - xx) / 25.0, -1, 1) * 0.0 + 0.15 * ((yy - cy) < 2)
    cv.paint(body, np.clip(tone, 0, 1), blk)
    dial = kit.ellipse_full(w, h, cx, cy + 5, 9, 6)
    cv.paint(dial, np.full((h, w), 0.32, np.float32), blk)
    for k in range(10):
        a = math.pi * (0.25 + 1.5 * k / 10.0)
        cv.px(cx + math.cos(a) * 6.5, cy + 5 + math.sin(a) * 4.2, blk[1])
    cv.px(cx, cy + 5, BR['cuff'][3])
    # handset on the cradle
    hs = kit.poly_mask_full(w, h, [(cx - 28, cy - 12), (cx + 28, cy - 12), (cx + 30, cy - 5), (cx - 30, cy - 5)])
    cv.paint(hs, np.full((h, w), 0.26, np.float32), blk)
    cv.paint(hs & (yy < cy - 10), np.full((h, w), 0.45, np.float32), blk)
    for ex in (cx - 26, cx + 26):
        e = kit.ellipse_full(w, h, ex, cy - 8, 6, 5)
        cv.paint(e, np.full((h, w), 0.3, np.float32), blk)
        cv.px(ex - 2, cy - 11, blk[6])
    cord = pg.bezier([(cx + 24, cy + 10), (cx + 50, cy + 30), (cx + 30, cy + 46), (cx + 70, cy + 52)], n=40)
    for (px_, py_) in cord:
        cv.px(px_, py_, blk[2])
    a = cv.alpha()


def folders(cv: kit.Canvas, x0, y0, lamp, n=4):
    """Stack of buff archive folders with tabs."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    for k in range(n):
        q = [(x0 + k * 2, y0 - k * 3), (x0 + 92 + k * 2, y0 - 2 - k * 3), (x0 + 96 + k, y0 + 44 - k * 3),
             (x0 + 2 + k, y0 + 46 - k * 3)]
        m = kit.poly_mask_full(w, h, q)
        if k == 0:
            drop_shadow(cv, m, 6, 4, 1, BR['desk'], lamp, blur=1)
        pool = lamp.pool(xx, yy, lift=4 + k * 3)
        ramp = [pg.hx(c) for c in ('#14272B', '#3D2820', '#55372A', '#805C4E', '#9C7560', '#B57B59')]
        cv.paint(m, np.clip(0.12 + 0.8 * pool + k * 0.02, 0, 1), ramp)
        e = kit.outline_of(m)
        cv.c[e & (yy > y0 + 30 - k * 3)] = ramp[0]
        tab = kit.poly_mask_full(w, h, [(x0 + 60 + k * 9, y0 - k * 3 - 4), (x0 + 74 + k * 9, y0 - k * 3 - 4),
                                         (x0 + 75 + k * 9, y0 - k * 3), (x0 + 59 + k * 9, y0 - k * 3)])
        cv.paint(tab, np.clip(0.14 + 0.8 * pool, 0, 1), ramp)


def calendar(cv: kit.Canvas, x, y, lamp, year='1964', month='JANUAR'):
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    m = (xx >= x) & (xx < x + 34) & (yy >= y) & (yy < y + 30)
    t = 0.1 + 0.9 * lamp.pool(xx, yy + 90)
    cv.paint(m, np.clip(t * 0.8, 0, 1), BR['paper'])
    head = (xx >= x) & (yy >= y) & (xx < x + 34) & (yy < y + 8)
    cv.paint(head, np.clip(t * 0.5, 0, 1), BR['red'] + [pg.hx('#C8503C')])
    tm = kit.text_mask(year, kit.FONT3)
    kit.blit_mask(cv.c, tm, x + 17 - tm.shape[1] // 2, y + 2, BR['paper'][4])
    for r in range(4):
        for c in range(7):
            cv.px(x + 4 + c * 4, y + 12 + r * 4, BR['wall'][1])
    cv.rect(x + 16, y - 3, 2, 3, BR['brass'][2])


def pinned_drawing(cv: kit.Canvas, x, y, lamp):
    """Elevation sketch of the hall pinned to the wall (the office drawings Konrad makes)."""
    w, h = cv.w, cv.h
    xx, yy = cv.grid()
    m = (xx >= x) & (xx < x + 56) & (yy >= y) & (yy < y + 40)
    t = 0.05 + 0.9 * lamp.pool(xx, yy + 110)
    cv.paint(m, np.clip(t * 0.85, 0, 1), BR['paper'])
    ink_c = BR['wall'][2]
    cx, by = x + 28, y + 32
    for k in range(0, 30):
        a = math.pi * k / 29.0
        cv.px(cx + math.cos(a) * 16, by - 8 - math.sin(a) * 13, ink_c)
    cv.line(x + 8, by - 8, x + 48, by - 8, ink_c)
    cv.line(x + 8, by, x + 48, by, ink_c)
    for k in range(10, 48, 4):
        cv.line(x + k, by - 7, x + k, by - 1, ink_c)
    cv.px(cx, by - 23, ink_c)
    cv.px(x + 2, y + 1, BR['brass'][4])
    cv.px(x + 53, y + 1, BR['brass'][4])
