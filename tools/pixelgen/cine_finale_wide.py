"""cine_finale_wide -- life and detail for the two wide shots of the X1 finale (owner: trans-finale).

b_wide  Konrad's drafting office: coffered cornice, a second framed section drawing, a wall calendar, his
        desk against the wall under the framed rendering (typewriter, architect's lamp, papers, his hat lying
        on it) with Konrad seated at it, back to us -- the same desk the close-up then looks over his shoulder
        at; the model of the Great Hall's dome in a glass case on a pedestal, a basket of rolled plans, a
        waste-paper basket, a rug, herringbone parquet; animated: Konrad breathing and turning his head to the
        window, the pendulum (in step with the tick/tock), searchlights sweeping behind the dome, a tram's
        blue spark flashing on the ceiling (with the tram bell), a cigarette smoking on the sill.
k_wide  the Karsk signal box: an illuminated track diagram with blinking track lamps, a shelf of binders,
        the clock moved beside the stove pipe, a kettle steaming on the stove, the fire's glow flickering on
        the floor, a coal scuttle and firewood, a blanket and a tin mug on the bench, a hanging lantern;
        animated: a freight train passing in the yard behind the window (with the far horn), blinking track
        lamps, stove glow, kettle steam.
All drawn on the same set canvases (680x380) as cine_finale_rest, deterministic, original.
"""
from __future__ import annotations

import math
import os

import numpy as np

import cine_finale_kit as kit
import pg

BR, KR = kit.BR, kit.KR
W, H = 680, 380


def _over(dst, src):
    kit.over(dst, src)


# ======================================================================================= Berlin wide
def b_wide_enrich(cv: kit.Canvas, L: kit.Lamp, halo: np.ndarray, floor_y: int):
    """Draws the extra furniture into the b_wide base canvas (before the glass layer)."""
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    # coffered cornice under the ceiling
    cor = (yy >= 40) & (yy < 58)
    ct = 0.10 + 0.25 * halo + 0.10 * ((yy >= 54) & (yy < 56)) - 0.05 * ((np.floor(xx) % 46) < 2)
    cv.paint(cor, np.clip(ct, 0, 1), BR['wall'])
    cv.rect(0, 58, W, 1, BR['wall'][5])
    cv.rect(0, 59, W, 1, BR['wall'][1])
    # herringbone parquet over the plain planks, and a rug under the drafting table
    fl = yy >= floor_y
    hb = ((np.floor(xx / 6.0) + np.floor((yy - floor_y) / 3.0)) % 2 == 0)
    seam = fl & (((np.floor(xx) + np.floor(yy) * 2) % 12) == 0)
    cv.c[seam & hb] = kit.tone_to_ramp(np.clip(0.06 + 0.5 * L.pool(xx, yy), 0, 1), BR['desk'])[seam & hb]
    rug = (xx >= 226) & (xx < 400) & (yy >= floor_y + 1) & (yy < floor_y + 13)
    rt = 0.10 + 0.55 * L.pool(xx, yy) + 0.10 * (((np.floor(xx) % 9) < 2) | (np.abs(yy - floor_y - 3) < 0.6) |
                                                 (np.abs(yy - floor_y - 10) < 0.6))
    cv.paint(rug, np.clip(rt, 0, 1), BR['lining'])
    cv.c[rug & (np.abs(xx - 226.5) < 0.6)] = np.asarray(BR['lining'][1], np.uint8)
    for k in range(230, 398, 4):
        cv.px(k, floor_y + 13, BR['lining'][3])
    # section drawing (smaller frame) between cabinet and clock
    fr = (xx >= 144) & (xx < 176) & (yy >= 150) & (yy < 188)
    cv.paint(fr, np.clip(0.12 + 0.3 * halo, 0, 1), BR['desk'])
    inner = (xx >= 147) & (xx < 173) & (yy >= 153) & (yy < 185)
    cv.paint(inner, np.clip(0.22 + 0.45 * halo, 0, 1), BR['paper'])
    for k in range(4):
        cv.line(150, 180 - k * 6, 170, 180 - k * 6, BR['ink'][1])
    for k in range(9):
        a = math.pi * k / 8.0
        cv.px(160 + math.cos(a) * 9, 162 - math.sin(a) * 6, BR['ink'][1])
    # wall calendar by the drafting table (1964, January)
    cal = (xx >= 330) & (xx < 352) & (yy >= 168) & (yy < 198)
    cv.paint(cal, np.clip(0.30 + 0.6 * L.pool(xx, yy + 60), 0, 1), BR['paper'])
    cv.rect(330, 168, 22, 6, BR['red'][2])
    for r in range(5):
        for c in range(6):
            if (r * 6 + c) % 4:
                cv.px(333 + c * 3, 177 + r * 4, BR['ink'][0])
    cv.px(342, 164, BR['brass'][4])
    # the model of the Hall's dome in a glass case on a wooden pedestal, right of the desk
    DX = 170
    ped = (xx >= DX + 258) & (xx < DX + 290) & (yy >= 264) & (yy < floor_y)
    pt = 0.12 + 0.55 * L.pool(xx, yy - 30) + 0.12 * (xx > 282)
    cv.paint(ped, np.clip(pt, 0, 1), BR['desk'])
    cv.rect(DX + 254, 262, 40, 3, BR['desk'][6])
    cv.rect(DX + 256, floor_y - 3, 36, 3, BR['desk'][2])
    case = (xx >= DX + 256) & (xx < DX + 292) & (yy >= 226) & (yy < 262)
    cbase = (xx >= DX + 258) & (xx < DX + 290) & (yy >= 256) & (yy < 262)
    cv.paint(cbase, np.clip(0.2 + 0.5 * L.pool(xx, yy - 30), 0, 1), BR['stone'])
    dm = kit.ellipse_full(W, H, DX + 274, 250, 13, 11) & (yy < 250)
    u = (xx - DX - 274) / 13.0
    dtone = 0.18 + 0.35 * np.clip(u, -1, 1) * 0.5 + 0.35 * L.pool(xx, yy - 30) + 0.1 * (np.abs((np.arcsin(np.clip(u, -1, 1)) * 5) % 1 - 0.5) < 0.12)
    cv.paint(dm, np.clip(dtone + 0.15, 0, 1), BR['patina'])
    drum = (xx >= DX + 260) & (xx < DX + 289) & (yy >= 250) & (yy < 256)
    cv.paint(drum, np.clip(0.3 + 0.4 * (((np.floor(xx) - DX - 260) % 3) == 0) + 0.3 * L.pool(xx, yy - 30), 0, 1), BR['stone'])
    cv.rect(DX + 273, 237, 2, 2, BR['patina'][2])
    # glass: thin frame and two reflection streaks
    gl = case & ~kit.erode(case, 1)
    cv.c[gl] = np.asarray(BR['metal'][5], np.uint8)
    for k in range(10):
        cv.px(DX + 284 - k * 0.4, 229 + k * 2, BR['metal'][7])
        if k < 6:
            cv.px(DX + 287 - k * 0.4, 231 + k * 2, BR['metal'][6])
    # basket of rolled plans standing left of the desk, waste-paper basket with crumpled sheets
    bsk = kit.poly_mask_full(W, H, [(204, 270), (228, 270), (226, floor_y), (206, floor_y)])
    cv.paint(bsk, np.clip(0.10 + 0.6 * L.pool(xx, yy - 20) + 0.1 * ((np.floor(yy) % 4) == 0), 0, 1), BR['desk'])
    rng = np.random.default_rng(kit.seed_of('bw_rolls_bin'))
    for k in range(6):
        rx = 206 + k * 4 + int(rng.integers(0, 2))
        top = 240 + int(rng.integers(0, 16))
        cv.rect(rx, top, 3, 271 - top, BR['paper'][3 + (k % 3)])
        cv.px(rx + 1, top, BR['paper'][7])
        cv.px(rx, top + 3, BR['paper'][2])
    wb = kit.poly_mask_full(W, H, [(398, 288), (414, 288), (412, floor_y), (400, floor_y)])
    cv.paint(wb, np.clip(0.08 + 0.4 * L.pool(xx, yy - 10), 0, 1), BR['metal'])
    for (px_, py_) in ((402, 286), (406, 285), (410, 287), (404, 288)):
        cv.ellipse(px_, py_, 2.5, 2, BR['paper'][5])
        cv.px(px_, py_, BR['paper'][3])
    # ashtray on the window sill (the smoke is an animated node)
    cv.rect(470, 244, 10, 2, BR['metal'][4])
    cv.px(481, 243, BR['cuff'][5])
    cv.px(482, 243, pg.hx('#D07744'))
    return (482, 242)


DESK_W = (232, 420)          # Konrad's desk against the wall (x range), top edge y = floor - 20
SEAT_X = 300                 # where he sits (under the right edge of the framed rendering, as in the close-up)


def b_wide_desk(cv: kit.Canvas, L: kit.Lamp, halo: np.ndarray, floor_y: int):
    """Konrad's desk against the wall under the framed rendering: top, apron with a drawer, a pedestal of
    drawers on the right, tapered legs on the left; on it the typewriter (with a sheet in), a stack of plans,
    a coffee cup and his hat, lying where the close-up shows it.  The lamp is a separate sprite."""
    xx, yy = cv.grid()
    x0, x1 = DESK_W
    top = floor_y - 20
    # cast shadow of the desk on the wall and floor
    sh = (xx >= x0 + 4) & (xx < x1 + 6) & (yy >= top - 2) & (yy < top + 1)
    cv.paint(sh, np.full((H, W), 0.05, np.float32), BR['desk'])
    # desk top (thin band seen from just above) and its lit front edge
    dt = (xx >= x0) & (xx < x1) & (yy >= top - 3) & (yy < top + 1)
    cv.paint(dt, np.clip(0.18 + 0.75 * L.pool(xx, yy + 6), 0, 1), BR['desk'])
    cv.rect(x0, top + 1, x1 - x0, 1, BR['desk'][7])
    ap = (xx >= x0) & (xx < x1) & (yy >= top + 2) & (yy < top + 7)
    cv.paint(ap, np.clip(0.10 + 0.40 * L.pool(xx, yy - 4), 0, 1), BR['desk'])
    cv.rect(x0 + 40, top + 4, 22, 1, BR['desk'][2])
    cv.px(x0 + 51, top + 4, BR['brass'][5])
    # pedestal of drawers (right) and legs (left)
    ped = (xx >= x1 - 34) & (xx < x1 - 2) & (yy >= top + 7) & (yy < floor_y)
    cv.paint(ped, np.clip(0.08 + 0.30 * L.pool(xx, yy - 10), 0, 1), BR['desk'])
    for k in range(3):
        y = top + 8 + k * 5
        cv.rect(x1 - 32, y, 28, 1, BR['desk'][1])
        cv.px(x1 - 18, y + 2, BR['brass'][4])
    for lx in (x0 + 3, x0 + 9):
        cv.rect(lx, top + 7, 2, floor_y - top - 7, BR['desk'][3])
        cv.px(lx, top + 7, BR['desk'][6])
    # typewriter seen from behind (mostly hidden by him): body, carriage with knobs, the sheet in it
    tx = SEAT_X
    body = (np.abs(xx - tx) < 13) & (yy >= top - 9) & (yy < top - 2)
    cv.paint(body, np.clip(0.10 + 0.35 * L.pool(xx, yy + 20), 0, 1), BR['black'])
    cv.rect(tx - 17, top - 11, 34, 2, BR['black'][3])
    cv.rect(tx - 19, top - 12, 3, 4, BR['black'][5])
    cv.rect(tx + 16, top - 12, 3, 4, BR['black'][4])
    sheet = (np.abs(xx - tx + 1) < 5) & (yy >= top - 20) & (yy < top - 11)
    cv.paint(sheet, np.clip(0.30 + 0.5 * L.pool(xx, yy + 30), 0, 1), BR['paper'])
    for r in range(top - 18, top - 13, 2):
        cv.line(tx - 4, r, tx + 1, r, BR['paper'][3])
    # stack of plans (left), coffee cup, the hat (right, on its crown, brim up -- as in the close-up)
    pl = (xx >= x0 + 18) & (xx < x0 + 44) & (yy >= top - 6) & (yy < top - 2)
    cv.paint(pl, np.clip(0.40 + 0.6 * L.pool(xx, yy + 6), 0, 1), BR['paper'])
    cv.rect(x0 + 18, top - 4, 26, 1, BR['paper'][3])
    cv.ellipse(tx + 34, top - 4, 3, 2, BR['cuff'][4])
    cv.rect(tx + 32, top - 6, 5, 3, BR['cuff'][5])
    cv.px(tx + 33, top - 7, BR['smoke'][4])
    hx, hy = x1 - 26, top - 4
    brim = kit.ellipse_full(W, H, hx, hy + 1, 9, 2.5)
    cv.paint(brim, np.clip(0.10 + 0.40 * L.pool(xx, yy), 0, 1), BR['black'])
    crown = kit.ellipse_full(W, H, hx, hy - 2, 6, 3.5) & (yy < hy + 1)
    cv.paint(crown, np.clip(0.12 + 0.45 * L.pool(xx, yy), 0, 1), BR['black'])
    cv.rect(hx - 6, hy, 12, 1, BR['lining'][3])                    # the hat band
    cv.px(hx - 3, hy - 4, BR['black'][6])
    # chair standing out from the desk (seat and back are part of the seated figure sprite)
    return top


def konrad_seated_frames(atlas: kit.Atlas, floor_y: int, lamp_head):
    """Konrad at the desk, seen from behind at the game-sprite scale: bareheaded (brown hair, ears), the cream
    scarf, navy coat, elbows out to the typewriter, the chair's slatted back over his lower back and its legs.
    Frames: 0 rest, 1 breath in, 2 head turned to the window (right), 3 turned + breath, 4 leaning in."""
    import cine_finale_figure as fig
    cost = fig.COSTUMES['konrad']
    hair, skin, coat, scarf = cost['hair'], cost['skin'], cost['sleeve'], cost['scarf']
    top = floor_y - 20
    frames = []
    for (breath, turn, lean) in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)):
        cv = kit.Canvas(W, H)
        xx, yy = cv.grid()
        cx = SEAT_X
        sy = top - 8 - breath + lean            # shoulder line
        # coat: shoulders 18 px, waist 14 px, down to the seat
        torso = kit.poly_mask_full(W, H, [(cx - 9, sy + 1), (cx - 6, sy - 1), (cx + 6, sy - 1), (cx + 9, sy + 1),
                                          (cx + 8, top + 8), (cx - 8, top + 8)])
        lx = np.clip((lamp_head[0] + 40 - xx) / 30.0, -1, 1)
        tone = 0.30 + 0.16 * lx - 0.12 * np.clip((yy - sy) / 14.0, 0, 1)
        cv.paint(torso, np.clip(tone, 0, 1), coat)
        cv.c[torso & (np.abs(xx - cx) < 0.6) & (yy > sy + 2)] = coat[1]
        # elbows out to the keys (left one catches the lamp)
        for s_, t_ in ((-1, 0.46), (1, 0.26)):
            el = kit.ellipse_full(W, H, cx + s_ * 10, sy + 6 + (breath if s_ > 0 else 0), 2.5, 3.0)
            cv.paint(el, np.full((H, W), t_, np.float32), coat)
        cv.c[kit.outline_of(torso) & (xx < cx - 4) & (yy < sy + 4)] = coat[6]
        # scarf, nape, head
        cv.rect(cx - 3, sy - 2, 7, 2, scarf[6])
        cv.px(cx + 3, sy - 1, scarf[3])
        hy = sy - 6 - lean
        hx = cx + turn
        head = kit.ellipse_full(W, H, hx + 0.5, hy, 3.6, 4.2)
        ht = 0.42 + 0.30 * np.clip((lamp_head[0] + 44 - xx) / 8.0, -1, 1) * 0.5 - 0.15 * np.clip((yy - hy) / 4.0, 0, 1)
        cv.paint(head, np.clip(ht, 0, 1), hair)
        cv.px(hx - 3, hy, skin[4] if not turn else skin[3])                      # ears
        cv.px(hx + 4, hy, skin[3] if not turn else skin[5])
        if turn:
            cv.px(hx + 4, hy + 1, skin[4])                                       # the edge of his cheek
        cv.px(hx - 1, hy - 3, hair[7])
        cv.px(hx, hy - 4, hair[6])
        # chair: slatted back over the lower back, seat edge, legs to the floor
        ch = BR['desk']
        cv.rect(cx - 8, top + 1, 16, 2, ch[3])
        cv.rect(cx - 8, top + 1, 16, 1, ch[6])
        for k in (-6, -2, 2, 6):
            cv.rect(cx + k, top + 3, 1, 6, ch[2])
        cv.rect(cx - 8, top + 3, 1, 9, ch[3])
        cv.rect(cx + 7, top + 3, 1, 9, ch[3])
        cv.rect(cx - 9, top + 9, 18, 2, ch[4])
        for k in (-8, -4, 3, 7):
            cv.rect(cx + k, top + 11, 1, floor_y - top - 11, ch[2])
        frames.append(atlas.add(cv.c))
    return frames


def pendulum_frames(atlas: kit.Atlas, pivot, length, n=16, amp=0.22):
    """Pendulum of the wall clock: rod + brass bob, n frames over one period (2 s = tick + tock)."""
    frames = []
    for i in range(n):
        a = amp * math.sin(2 * math.pi * i / n)
        cv = kit.Canvas(W, H)
        ex = pivot[0] + math.sin(a) * length
        ey = pivot[1] + math.cos(a) * length
        cv.line(pivot[0], pivot[1], ex, ey, BR['brass'][3])
        cv.ellipse(ex, ey + 1, 3, 3, BR['brass'][5])
        cv.px(ex - 1, ey, BR['brass'][7])
        frames.append(atlas.add(cv.c))
    return frames


def clock_case_cover(cv: kit.Canvas, cx, cy):
    """Paint over the static pendulum of the base (the animated one replaces it)."""
    xx, yy = cv.grid()
    pend = (np.abs(xx - cx) < 7) & (yy >= cy + 12) & (yy < cy + 40)
    cv.paint(pend, np.full((H, W), 0.08, np.float32), BR['desk'])
    glass = (np.abs(xx - cx) < 6) & (yy >= cy + 13) & (yy < cy + 39)
    cv.c[glass & (((np.floor(xx) + np.floor(yy)) % 7) == 0)] = np.asarray(BR['desk'][3], np.uint8)


def searchlight_frames(atlas: kit.Atlas, ext_off, n=24):
    """Two searchlight beams behind the dome sweeping slowly (one period = n frames).  Drawn in exterior
    coordinates offset into the set like the exterior layer."""
    ox, oy = ext_off
    frames = []
    w, h = 720, 400
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    bay = kit.bayer_full(w, h)
    cx = w * 0.5
    foot = h * 0.60 + 34
    # beams rise from behind the hall: never over the dome, its drum and lantern, or the roofs in front
    base_y = h * 0.60
    hide = (((xx - cx) / 104.0) ** 2 + ((yy - base_y) / 72.0) ** 2 <= 1.0) & (yy < base_y + 2)
    hide |= (np.abs(xx - cx) < 106) & (yy >= base_y - 4) & (yy < foot + 2)
    hide |= (np.abs(xx - cx) < 10) & (yy > base_y - 64 - 32) & (yy < base_y - 60)
    hide |= yy > h * 0.72
    for i in range(n):
        ph = 2 * math.pi * i / n
        img = np.zeros((h, w, 4), np.uint8)
        for k, (bx, a0, sp) in enumerate(((cx - 70, -0.32, 0.20), (cx + 80, 0.28, -0.22))):
            ang = a0 + sp * math.sin(ph + k * 1.7)
            L = foot + 30
            x1 = bx + math.sin(ang) * L
            poly = [(bx - 2, foot), (bx + 2, foot), (x1 + 9, foot - L), (x1 - 9, foot - L)]
            m = kit.poly_mask_full(w, h, poly)
            fade = np.clip((yy - (foot - L)) / L, 0, 1) ** 1.2
            sel = m & (bay < 0.10 + 0.28 * fade) & ~hide
            img[sel] = pg.hx('#57494D')
            img[sel & (bay < 0.08 + 0.12 * fade)] = pg.hx('#6E6A73')
        out = np.zeros((H, W, 4), np.uint8)
        x0_, y0_ = max(0, ox), max(0, oy)
        x1_, y1_ = min(W, ox + w), min(H, oy + h)
        out[y0_:y1_, x0_:x1_] = img[y0_ - oy:y1_ - oy, x0_ - ox:x1_ - ox]
        frames.append(atlas.add(out))
    return frames


def tram_flash(atlas: kit.Atlas, win):
    """A blue-white flash of a tram's pantograph spark thrown onto the ceiling and the window reveal."""
    wx0, wy0, wx1, wy1 = win
    out = []
    for strength in (1.0, 0.5):
        cv = kit.Canvas(W, H)
        xx, yy = cv.grid()
        bay = kit.bayer_full(W, H)
        g = np.clip(1.0 - np.sqrt(((xx - (wx0 + wx1) / 2) / 260.0) ** 2 + ((yy - 40) / 70.0) ** 2), 0, 1) * strength
        m = (yy < wy0 + 10) & (bay < g * 0.55)
        cv.c[m] = pg.hx('#58718A')
        cv.c[m & (bay < g * 0.2)] = pg.hx('#7A93A8')
        reveal = (xx >= wx0 - 6) & (xx < wx0) & (yy >= wy0) & (yy < wy1) & (bay < 0.5 * strength)
        cv.c[reveal] = pg.hx('#7A93A8')
        out.append(atlas.add(cv.c))
    return out


# ======================================================================================= Karsk wide
def k_wide_enrich(cv: kit.Canvas, L: kit.Lamp, halo: np.ndarray, floor_y: int):
    """Extra furniture of the signal box.  Returns positions used by the animated nodes."""
    xx, yy = cv.grid()
    wall = KR['wall']
    # paint over the old clock (it moves beside the stove pipe)
    old = kit.ellipse_full(W, H, 420, 122, 12, 12)
    cv.paint(old, np.clip(0.20 + 0.42 * halo[int(122), int(420)] + 0 * xx, 0, 1), wall)
    # illuminated track diagram: dark enamel panel, white track lines, station boxes, lamp sockets
    px0, py0, px1, py1 = 404, 84, 536, 150
    pan = (xx >= px0) & (xx < px1) & (yy >= py0) & (yy < py1)
    cv.paint(pan, np.clip(0.10 + 0.25 * halo + 0.03 * ((np.floor(yy) % 2) == 0), 0, 1), KR['green'])
    cv.c[kit.outline_of(pan)] = np.asarray(KR['metal'][5], np.uint8)
    track = KR['paper'][5]
    for y_ in (104, 118, 132):
        cv.line(px0 + 6, y_, px1 - 6, y_, track)
    for (a, b_, c, d) in ((430, 104, 446, 118), (470, 118, 486, 132), (452, 132, 468, 118), (500, 104, 516, 118)):
        cv.line(a, b_, c, d, track)
    for (sx, sy) in ((414, 98), (442, 112), (476, 126), (506, 98), (520, 126)):
        cv.rect(sx, sy, 6, 3, KR['paper'][3])
    lamps = [(418, 104), (438, 118), (456, 104), (478, 132), (494, 118), (512, 104), (526, 132), (462, 118)]
    for (lx, ly) in lamps:
        cv.px(lx, ly, KR['metal'][1])
    tm = kit.text_mask('УЧАСТОК К-17', kit.FONT3) if False else kit.text_mask('KARSK', kit.FONT3)
    kit.blit_mask(cv.c, tm, px0 + 4, py0 + 4, KR['paper'][4])
    # new wall clock right of the stove pipe
    ccx, ccy = 596, 116
    face = kit.ellipse_full(W, H, ccx, ccy, 10, 10)
    cv.paint(face, np.full((H, W), 0.62, np.float32), KR['paper'])
    cv.c[kit.outline_of(face)] = np.asarray(KR['metal'][1], np.uint8)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        cv.px(ccx + math.sin(a) * 8, ccy - math.cos(a) * 8, KR['metal'][1])
    am = 47 / 60 * 2 * math.pi
    cv.line(ccx, ccy, ccx + math.sin(am) * 8, ccy - math.cos(am) * 8, KR['metal'][0])
    ah = (1 + 47 / 60) / 12 * 2 * math.pi
    cv.line(ccx, ccy, ccx + math.sin(ah) * 5, ccy - math.cos(ah) * 5, KR['metal'][0])
    # shelf with binders and a samovar-less tea tin, above the bench
    cv.rect(400, 206, 104, 3, KR['desk'][4])
    cv.rect(400, 209, 104, 1, KR['desk'][1])
    rng = np.random.default_rng(kit.seed_of('kw_binders'))
    x = 404
    while x < 470:
        bw = int(rng.integers(5, 8))
        bh = int(rng.integers(18, 25))
        col = [KR['cover'][3], KR['cover'][4], KR['green'][4], KR['metal'][4]][int(rng.integers(0, 4))]
        cv.rect(x, 206 - bh, bw, bh, col)
        cv.rect(x + 1, 206 - bh + 4, bw - 2, 3, KR['paper'][4])
        cv.rect(x + bw - 1, 206 - bh, 1, bh, KR['void'][1])
        x += bw + 1
    tin = (xx >= 482) & (xx < 496) & (yy >= 190) & (yy < 206)
    cv.paint(tin, np.clip(0.2 + 0.4 * halo, 0, 1), KR['rust'])
    # blanket and tin mug on the bench
    bl = (xx >= 448) & (xx < 482) & (yy >= 266) & (yy < 274)
    cv.paint(bl, np.clip(0.18 + 0.3 * halo + 0.1 * ((np.floor(xx) % 6) < 2), 0, 1), KR['cover'])
    cv.rect(500, 265, 6, 7, KR['metal'][5])
    cv.px(506, 267, KR['metal'][5])
    # coal scuttle and firewood by the stove
    sc = kit.poly_mask_full(W, H, [(578, 286), (596, 286), (598, floor_y), (576, floor_y)])
    cv.paint(sc, np.clip(0.12 + 0.2 * (xx < 584), 0, 1), KR['metal'])
    for k in range(5):
        cv.ellipse(581 + k * 3, 285, 2, 1.5, KR['void'][1])
    for k in range(4):
        cv.rect(604, floor_y - 4 - k * 4, 20, 4, KR['rust'][2 + (k % 2)])
        cv.ellipse(604, floor_y - 2 - k * 4, 2, 2, KR['rust'][5])
    # hanging oil lantern by the door frame (lit, small warm glow)
    hx_, hy_ = 630, 176
    cv.line(hx_, 150, hx_, hy_ - 8, KR['metal'][3])
    cv.rect(hx_ - 4, hy_ - 8, 9, 13, KR['metal'][4])
    cv.rect(hx_ - 2, hy_ - 5, 5, 7, KR['fire'][3])
    cv.px(hx_, hy_ - 3, KR['fire'][4])
    bay = kit.bayer_full(W, H)
    g = np.clip(1.0 - np.sqrt(((xx - hx_) / 30.0) ** 2 + ((yy - hy_) / 30.0) ** 2), 0, 1)
    glow = (g > 0.05) & (bay < g * 0.30) & (xx < 646) & ~((xx >= hx_ - 4) & (xx < hx_ + 5) & (yy >= hy_ - 8) & (yy < hy_ + 5))
    cv.c[glow] = np.asarray(KR['rust'][3], np.uint8)
    # ceiling lamp (enamel shade, off) on a cable
    cv.line(330, 40, 330, 70, KR['metal'][2])
    shade = kit.poly_mask_full(W, H, [(322, 70), (338, 70), (346, 80), (314, 80)])
    cv.paint(shade, np.clip(0.2 + 0.3 * halo, 0, 1), KR['enamel'])
    return {'lamps': lamps, 'stove': (556, 270), 'kettle': (555, 250), 'panel': (px0, py0, px1, py1)}


def track_lamp_frames(atlas: kit.Atlas, lamps, n=8):
    """Track-occupancy lamps on the diagram: most steady, a few blinking / changing (n frames, 2 fps)."""
    frames = []
    cols = [KR['signal_r'][3], KR['signal_g'][3], pg.hx('#F0C487')]
    for i in range(n):
        cv = kit.Canvas(W, H)
        for k, (lx, ly) in enumerate(lamps):
            mode = k % 4
            if mode == 0:
                on, c = True, cols[1]
            elif mode == 1:
                on, c = (i % 2 == 0), cols[0]
            elif mode == 2:
                on, c = (i // 2) % 2 == 0, cols[2]
            else:
                on, c = (i < 5), cols[1] if i < 3 else cols[0]
            if on:
                cv.px(lx, ly, c)
                cv.px(lx + 1, ly, c)
                cv.px(lx, ly - 1, KR['signal_r'][4] if c is cols[0] else KR['signal_g'][4])
        frames.append(atlas.add(cv.c))
    return frames


def stove_glow_frames(atlas: kit.Atlas, stove, n=8, seed='stove_glow'):
    """The open stove door's firelight on the floor and the stove front: flickering pool (n frames)."""
    rng = np.random.default_rng(kit.seed_of(seed))
    frames = []
    sx, sy = stove
    for i in range(n):
        cv = kit.Canvas(W, H)
        xx, yy = cv.grid()
        bay = kit.bayer_full(W, H)
        k = 0.75 + 0.25 * rng.random()
        g = np.clip(1.0 - np.sqrt(((xx - sx) / (52.0 * k)) ** 2 + ((yy - 306) / (13.0 * k)) ** 2), 0, 1)
        m = (yy >= 302) & (bay < g * 0.55)
        cv.c[m] = np.asarray(KR['rust'][3], np.uint8)
        cv.c[m & (bay < g * 0.25)] = np.asarray(KR['rust'][5], np.uint8)
        door = (xx >= sx - 6) & (xx < sx + 8) & (yy >= sy - 6) & (yy < sy + 6)
        ft = 0.45 + 0.4 * k + 0.15 * (((np.floor(yy) + i) % 3) == 0)
        cv.paint(door, np.clip(ft + 0 * xx, 0, 1), KR['fire'])
        frames.append(atlas.add(cv.c))
    return frames


def train_sprite(length=360, seed='kw_train'):
    """A freight train seen from the side at yard distance: locomotive with a lit headlamp and cab window,
    a string of dark box wagons with snow on the roofs.  Returns (rgba, h) with the loco at the left (it runs
    west = left).  Drawn small (yard distance)."""
    hgt = 26
    img = kit.Canvas(length, 40)
    rng = np.random.default_rng(kit.seed_of(seed))
    base = 30
    blk = KR['void']
    # locomotive (steam): boiler, cab, chimney, wheels
    img.rect(6, base - 14, 34, 9, blk[2])
    img.rect(30, base - 20, 12, 15, blk[2])
    img.rect(32, base - 18, 5, 4, KR['fire'][3])
    img.rect(10, base - 19, 4, 5, blk[1])
    img.rect(0, base - 8, 44, 3, blk[1])
    for wx_ in (10, 18, 26, 36):
        img.ellipse(wx_, base - 3, 3, 3, blk[1])
    img.rect(2, base - 13, 3, 3, pg.hx('#FBE3AE'))
    img.px(1, base - 12, pg.hx('#FBE3AE'))
    x = 48
    while x < length - 30:
        wl = int(rng.integers(30, 38))
        img.rect(x, base - 16, wl, 12, blk[2] if rng.random() < 0.6 else KR['cover'][2])
        img.rect(x, base - 17, wl, 1, KR['snow'][4])
        img.rect(x + wl // 2 - 3, base - 14, 6, 8, blk[1])
        for wx_ in (x + 5, x + wl - 6):
            img.ellipse(wx_, base - 3, 2.5, 2.5, blk[1])
        img.rect(x - 4, base - 9, 4, 1, blk[1])
        x += wl + 4
    return img.c


def steam_plume_frames(atlas: kit.Atlas, n=6):
    """A loco's steam plume trailing behind (to the right), drawn relative to the train sprite's origin."""
    frames = []
    for i in range(n):
        cv = kit.Canvas(140, 40)
        xx, yy = cv.grid()
        bay = kit.bayer_full(140, 40)
        dens = np.zeros((40, 140), np.float32)
        for k in range(7):
            p = (k / 7.0 + i / n / 7.0)
            x = 12 + p * 120
            y = 10 - 6 * math.sqrt(p) + math.sin(p * 9 + i) * 1.5
            r = 3 + p * 9
            d = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.4) ** 2) / r
            dens = np.maximum(dens, np.clip(1 - d, 0, 1) * (1 - p * 0.8))
        m = dens > bay * 0.9 + 0.05
        cv.c[m] = np.asarray(KR['steam'][3], np.uint8)
        cv.c[m & (dens > 0.5)] = np.asarray(KR['steam'][5], np.uint8)
        frames.append(cv.c)
    return frames
