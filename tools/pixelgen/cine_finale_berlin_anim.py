"""cine_finale_berlin_anim -- animated layers of the Berlin desk close-up (owner: trans-finale).

Branch m1_choose:
  request_explanation  Konrad types a formal request on office letterhead (red ribbon for 'C-17'), returns the
                       carriage, stops, hesitates, pulls the sheet out and lays it into the AUSGANG tray.
  preserve_evidence    he separates his tracing-paper copy from the stamped original, folds it twice, lifts the
                       front panel of his coat and slips the packet through a slit in the lining.
Every moving part is rasterised per frame from geometry (no rotated or scaled pixels) and packed into atlases;
times are local to the shot (seconds).  Letterhead / stamp frames exist twice (neutral + _hist, same rects).
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as b
import pg

BR = kit.BR
W, H = b.W, b.H
V = b.V
LAMP = b.LAMP_B
FPS = 12.0
DUR = 8.0

# ------------------------------------------------------------------------------------------- typewriter paper
PAPER_W, PAPER_H = 76, 104
MARGIN = 8
PLATEN = V(0, 146)[1]          # set y of the platen line (paper disappears below)
STRIKE = V(250, 0)[0]          # set x of the type guide
TYPE_Y0, LINE_SP = 40, 4
LINES = ['Betr.: Vorgang C-17', 'Ich bitte um Auskunft zur Aenderung', 'der Plaene im Bestand C.']
RED_SPANS = {0: (14, 18)}      # chars typed with the red half of the ribbon


def _glyph_h(ch: str, i: int) -> int:
    if ch == ' ':
        return 0
    if ch.isupper() or ch in 'bdfhklt1C7-':
        return 2
    return 1


def paper_frame(line: int, chars: int, visible: int, hist: bool, dx: int = 0, dy: int = 0,
                lamp=LAMP) -> tuple[np.ndarray, int, int]:
    """The visible part of the typed sheet: `visible` px from the top edge down (<= PAPER_H).
    line/chars = typing progress.  Paper left edge at STRIKE - MARGIN - chars(current) + dx; its visible
    bottom sits on the platen (+dy when pulled out).  Returns (img, ox, oy) cropped to the sheet."""
    cur = chars
    left = STRIKE - MARGIN - (cur if line < len(LINES) else 0) + dx
    top = PLATEN - visible + dy
    cv = kit.Canvas(W, H)
    q = [(left, top), (left + PAPER_W, top), (left + PAPER_W, top + visible), (left, top + visible)]
    m = kit.poly_mask_full(W, H, q)
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy + 40)
    tone = 0.10 + 1.0 * pool + 0.06
    cv.paint(m, np.clip(tone, 0, 1), BR['paper'])
    ed = kit.outline_of(m) & (xx > left + PAPER_W - 2)
    ec = kit.tone_to_ramp(np.clip(tone - 0.2, 0, 1), BR['paper'], dither=False)
    cv.c[ed] = ec[ed]
    # letterhead: emblem + two tiny lines of office text + a rule
    em = kit.state_emblem(17, hist)
    ex = left + (PAPER_W - em.shape[1]) // 2
    ey = top + 4
    ink_c = BR['ink'][1]
    if True:
        kit.blit_mask(cv.c, em, ex, ey, ink_c)
    for k, wd in ((0, 44), (1, 30)):
        y = top + 4 + em.shape[0] + 3 + k * 3
        for x in range(left + (PAPER_W - wd) // 2, left + (PAPER_W + wd) // 2):
            if (x * 7 + k * 3) % 5 != 0:
                cv.px(x, y, BR['ink'][1] if k == 0 else BR['paper'][3])
    ry = top + 4 + em.shape[0] + 10
    cv.line(left + 6, ry, left + PAPER_W - 7, ry, BR['paper'][4])
    # typed text
    for li in range(min(line + 1, len(LINES))):
        txt = LINES[li]
        n = len(txt) if li < line else min(len(txt), chars)
        y = top + TYPE_Y0 + li * LINE_SP
        for i in range(n):
            gh = _glyph_h(txt[i], i)
            if gh == 0:
                continue
            red = li in RED_SPANS and RED_SPANS[li][0] <= i < RED_SPANS[li][1]
            col = BR['red'][2] if red else BR['ink'][0]
            x = left + MARGIN + i
            cv.px(x, y + 1, col)
            if gh == 2:
                cv.px(x, y, col)
    # mask to the visible part (everything already inside q) -- crop
    img = cv.c[top:top + visible, left:left + PAPER_W].copy()
    return img, left, top


def paper_flat(quad, hist: bool, lamp=LAMP) -> np.ndarray:
    """The finished request lying flat (in the tray / carried): letterhead + text rows."""
    cv = kit.Canvas(W, H)
    b.sheet(cv, quad, BR['paper'], lamp, base=0.10, gain=1.0, shadow=False, lift=6)
    em = kit.state_emblem(17, hist)
    cx, cy = b.quad_map(quad, 0.5, 0.06)
    # foreshortened emblem: keep it 1:1 but only when the sheet is flat enough
    kit.blit_mask(cv.c, em[::1, :], int(cx - em.shape[1] / 2), int(cy), BR['ink'][1])
    for li in range(3):
        for i in range(len(LINES[li])):
            if LINES[li][i] == ' ':
                continue
            x, y = b.quad_map(quad, (MARGIN + i) / PAPER_W, (TYPE_Y0 + li * LINE_SP) / PAPER_H)
            red = li in RED_SPANS and RED_SPANS[li][0] <= i < RED_SPANS[li][1]
            cv.px(x, y, BR['red'][2] if red else BR['ink'][0])
    return cv.c


# ------------------------------------------------------------------------------------------- branch B timing
T_LINE0 = (0.30, 1.50)          # typing line 0
T_CR1 = (1.55, 2.30)            # carriage return (left hand on the lever)
T_LINE1 = (2.45, 4.30)          # typing line 1
T_HES = (4.30, 5.55)            # hesitation
T_REACH = (5.55, 6.05)
T_PULL = (6.05, 6.75)
T_CARRY = (6.75, 7.45)


def typing_state(t: float):
    """(line, chars, carriage_dx, paper_dy, visible) at local time t for branch B."""
    n0, n1 = len(LINES[0]), len(LINES[1])
    vis0 = TYPE_Y0 + 9
    if t < T_LINE0[0]:
        return 0, 0, 0, 0, vis0
    if t < T_LINE0[1]:
        c = int((t - T_LINE0[0]) / (T_LINE0[1] - T_LINE0[0]) * n0)
        return 0, c, -c, 0, vis0
    if t < T_CR1[0] + 0.25:
        return 0, n0, -n0, 0, vis0
    if t < T_CR1[0] + 0.55:      # carriage slides back, then the line feed
        f = (t - T_CR1[0] - 0.25) / 0.30
        dx = -n0 + int(round(kit._ease(f) * n0))
        return 0, n0, dx, 0, vis0
    if t < T_LINE1[0]:
        return 1, 0, 0, 0, vis0 + LINE_SP
    if t < T_LINE1[1]:
        c = int((t - T_LINE1[0]) / (T_LINE1[1] - T_LINE1[0]) * n1)
        return 1, c, -c, 0, vis0 + LINE_SP
    return 1, n1, -n1, 0, vis0 + LINE_SP


def branch_request(out_dir: str) -> list:
    nodes = []
    # --- paper frames (typing + pull), carriage keys, typebar
    at_p = kit.Atlas('b_paper')
    at_ph = kit.Atlas('b_paper_hist')
    p_keys, c_keys, bar_keys = [], [], []
    last = None
    lastc = None
    lastbar = None
    pull_v0 = TYPE_Y0 + 9 + LINE_SP
    n1 = len(LINES[1])
    sig_cache = {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        line, chars, cdx, pdy, vis = typing_state(t)
        hidden = False
        if t >= T_PULL[0]:
            f = kit._ease((t - T_PULL[0]) / (T_PULL[1] - T_PULL[0]))
            vis = int(round(pull_v0 + (PAPER_H - pull_v0) * f))
            if t >= T_PULL[1]:
                hidden = True       # handed over to the carried / flat sheet
        sig = (line, chars, vis, hidden, cdx)
        if sig not in sig_cache:
            if hidden:
                sig_cache[sig] = -1
            else:
                img, ox, oy = paper_frame(line, chars, vis, False, dx=cdx + chars, dy=0)
                imgh, _, _ = paper_frame(line, chars, vis, True, dx=cdx + chars, dy=0)
                # paper_frame places the sheet using `chars`; cdx re-centres it during the carriage return
                sig_cache[sig] = (at_p.add_cropped(img, ox, oy), at_ph.add_cropped(imgh, ox, oy))
        fr = sig_cache[sig]
        frn = fr if fr == -1 else fr[0]
        if frn != last:
            p_keys.append([round(t, 3), frn])
            last = frn
        cx = cdx if t < T_PULL[1] else -n1
        if cx != lastc:
            c_keys.append([round(t, 3), int(cx), 0])
            lastc = cx
        typing = (T_LINE0[0] <= t < T_LINE0[1]) or (T_LINE1[0] <= t < T_LINE1[1])
        bar = (i % 2) if typing else 0
        if bar != lastbar:
            bar_keys.append([round(t, 3), bar])
            lastbar = bar
    nodes.append({'id': 'b_paper', 'type': 'anim', 'atlas': 'b_close/paper.png', 'frames': at_p.save(out_dir + '/b_close/paper.png'),
                  'hist_atlas': 'b_close/paper_hist.png', 'keys': p_keys, 'z': 12})
    at_ph.save(out_dir + '/b_close/paper_hist.png')
    # typebar flick (tiny anim at the type guide)
    at_b = kit.Atlas('b_typebar')
    cv = np.zeros((H, W, 4), np.uint8)
    f0 = at_b.add(cv)
    bar = kit.Canvas(W, H)
    bar.line(*V(250, 176), *V(250, 140), BR['metal'][6])
    bar.line(*V(249, 176), *V(249, 142), BR['metal'][3])
    f1 = at_b.add(bar.c)
    nodes.append({'id': 'b_typebar', 'type': 'anim', 'atlas': 'b_close/typebar.png',
                  'frames': at_b.save(out_dir + '/b_close/typebar.png'), 'keys': bar_keys, 'z': 14})
    # carriage: static sprite, moved by keys (dx per char)
    car = b.carriage(W, H, LAMP)
    kit.save_rgba(car, out_dir + '/b_close/carriage.png')
    nodes.append({'id': 'b_carriage', 'type': 'sprite', 'file': 'b_close/carriage.png', 'z': 13,
                  'pos_keys': c_keys, 'step': True})
    # --- carried / laid down sheet
    at_s = kit.Atlas('b_letter')
    at_sh = kit.Atlas('b_letter_hist')
    s_keys = []
    left_end = STRIKE - MARGIN - n1
    top_end = PLATEN - PAPER_H
    tray_q = [V(34, 134), V(112, 132), V(116, 168), V(36, 171)]
    last = None
    cache = {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        if t < T_PULL[1]:
            fr = -1
        else:
            f = kit._ease((t - T_CARRY[0]) / (T_CARRY[1] - T_CARRY[0]))
            # vertical sheet (top edge = pinch line) -> flat in the tray
            v_q = [(left_end, top_end), (left_end + PAPER_W, top_end), (left_end + PAPER_W, top_end + PAPER_H),
                   (left_end, top_end + PAPER_H)]
            # lift a little first, then travel; the sheet tilts back as it is laid down
            q = []
            for (vx, vy), (tx, ty) in zip(v_q, tray_q):
                q.append((vx + (tx - vx) * f, vy + (ty - vy) * f - math.sin(f * math.pi) * 18))
            key = tuple(int(round(c)) for p in q for c in p)
            if key not in cache:
                cache[key] = (at_s.add(paper_flat(q, False)), at_sh.add(paper_flat(q, True)))
            fr = cache[key][0]
        if fr != last:
            s_keys.append([round(t, 3), fr])
            last = fr
    nodes.append({'id': 'b_letter', 'type': 'anim', 'atlas': 'b_close/letter.png', 'frames': at_s.save(out_dir + '/b_close/letter.png'),
                  'hist_atlas': 'b_close/letter_hist.png', 'keys': s_keys, 'z': 15})
    at_sh.save(out_dir + '/b_close/letter_hist.png')
    # --- arms
    kw = dict(sleeve_ramp=BR['wool'], skin_ramp=BR['skin'], cuff_ramp=BR['cuff'], sleeve_w=(30, 42))
    L = kit.Track(wrist=V(222, 206), ang=-math.pi / 2 + 0.25, length=60, curl=0.55, thumb='side', entry=V(150, 430),
                  typing=0, tilt=0.0)
    R = kit.Track(wrist=V(282, 206), ang=-math.pi / 2 - 0.2, length=60, curl=0.55, thumb='side', entry=V(350, 430),
                  typing=0, tilt=0.0)
    L.key(0.0, typing=0).key(T_LINE0[0], typing=1).key(T_LINE0[1], typing=0)
    R.key(0.0, typing=0).key(T_LINE0[0], typing=1).key(T_LINE0[1], typing=0)
    # carriage return: left hand to the lever, push right, back
    lever0 = (V(250 + 40 - 92 - 19, 0)[0] - len(LINES[0]), V(0, 146 - 6 - 14)[1])
    L.key(T_CR1[0] + 0.05, wrist=(lever0[0] + 6, lever0[1] + 34), ang=-math.pi / 2 + 0.6, curl=0.35, thumb='side')
    L.key(T_CR1[0] + 0.25, wrist=(lever0[0] + 6, lever0[1] + 34))
    L.key(T_CR1[0] + 0.55, wrist=(lever0[0] + 6 + len(LINES[0]), lever0[1] + 34))
    L.key(T_LINE1[0], wrist=V(222, 206), ang=-math.pi / 2 + 0.25, curl=0.55)
    L.key(T_LINE1[0] + 0.01, typing=1).key(T_LINE1[1], typing=0)
    R.key(T_LINE1[0] + 0.01, typing=1).key(T_LINE1[1], typing=0)
    # hesitation: hands lift, fingers loosen, then the right hand tightens
    L.key(T_HES[0] + 0.35, wrist=V(220, 201), curl=0.32)
    R.key(T_HES[0] + 0.35, wrist=V(284, 201), curl=0.32)
    R.key(T_HES[0] + 0.85, curl=0.62)
    R.key(T_HES[1], curl=0.62)
    L.key(T_HES[1], wrist=V(220, 201))
    # reach: left hand to the top of the sheet (pinch), pull up, carry to the tray
    pinch_x = STRIKE - MARGIN - len(LINES[1]) + PAPER_W // 2 - 6
    top0 = PLATEN - (TYPE_Y0 + 9 + LINE_SP)
    L.key(T_REACH[1], wrist=(pinch_x - 4, top0 + 30), ang=-math.pi / 2 + 0.1, curl=0.15, thumb='pinch')
    L.key(T_PULL[1], wrist=(pinch_x - 4, PLATEN - PAPER_H + 30), ease='lin')
    tray_c = V(74, 150)
    L.key(T_CARRY[1], wrist=(tray_c[0] + 10, tray_c[1] + 26), ang=-math.pi / 2 + 0.35, curl=0.05, thumb='side')
    L.key(DUR, wrist=(tray_c[0] + 12, tray_c[1] + 30), curl=0.0)
    R.key(T_REACH[1], wrist=V(290, 214), curl=0.3)
    R.key(DUR, wrist=V(292, 216), curl=0.25)
    at_l = kit.Atlas('b_arm_l_req')
    at_r = kit.Atlas('b_arm_r_req')
    lk = kit.render_arm_track(L, 'L', at_l, W, H, LAMP, 0.0, DUR, FPS, seed=11, **kw)
    rk = kit.render_arm_track(R, 'R', at_r, W, H, LAMP, 0.0, DUR, FPS, seed=12, **kw)
    nodes.append({'id': 'b_arm_l', 'type': 'anim', 'atlas': 'b_close/arm_l_req.png',
                  'frames': at_l.save(out_dir + '/b_close/arm_l_req.png'), 'keys': lk, 'z': 20,
                  '_atlas': at_l, '_path': out_dir + '/b_close/arm_l_req.png'})
    nodes.append({'id': 'b_arm_r', 'type': 'anim', 'atlas': 'b_close/arm_r_req.png',
                  'frames': at_r.save(out_dir + '/b_close/arm_r_req.png'), 'keys': rk, 'z': 21,
                  '_atlas': at_r, '_path': out_dir + '/b_close/arm_r_req.png'})
    for n in nodes:
        n['when'] = {'m1_choose': 'request_explanation'}
    return nodes


# ------------------------------------------------------------------------------------------- branch A
COPY_Q0 = [V(46, 202), V(150, 198), V(154, 260), V(50, 264)]
SLIT = (V(240, 254), V(310, 250))
COAT_LIFT = [V(176, 380), V(198, 214), V(244, 205), V(430, 214), V(446, 380)]


def _shift_q(q, dx, dy):
    return [(x + dx, y + dy) for (x, y) in q]


def coat_panel(state: str, lamp=LAMP) -> np.ndarray:
    """Front panel of Konrad's overcoat lifted into frame, lining up.  state: enter / lift / open / drop."""
    cv = kit.Canvas(W, H)
    dy = {'enter': 70, 'lift': 0, 'open': 0, 'drop': 46}[state]
    q = _shift_q(COAT_LIFT, 0, dy)
    m = kit.poly_mask_full(W, H, q)
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=30)
    # lining: satin, diagonal sheen streaks
    sheen = np.sin((xx * 0.55 + yy * 0.35) / 6.0) * 0.5 + 0.5
    folds = np.sin((xx * 0.9 - yy * 0.45) / 13.0 + 1.3) * 0.5 + 0.5
    tone = 0.10 + 0.52 * pool + 0.16 * (sheen > 0.86) * pool * 1.6 - 0.10 * (folds > 0.78) - 0.05 * (sheen < 0.12)
    cv.paint(m, np.clip(tone, 0, 1), BR['lining'])
    # wool facing band along the front edge (first two edges of the polygon)
    (ax, ay), (bx, by), (cx, cy) = q[0], q[1], q[2]
    band = np.zeros((H, W), bool)
    for (p0, p1) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy))):
        vx, vy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(vx, vy)
        tpar = np.clip(((xx - p0[0]) * vx + (yy - p0[1]) * vy) / (L * L), 0, 1)
        d = np.hypot(xx - (p0[0] + tpar * vx), yy - (p0[1] + tpar * vy))
        band |= d < 9.5
    band &= m
    wt = 0.12 + 0.7 * pool + 0.12 * (np.sin(yy / 3.0) > 0.8)
    cv.paint(band, np.clip(wt, 0, 1), BR['wool'])
    # seam between facing and lining
    seam = kit.outline_of(band) & m & ~kit.outline_of(m)
    cv.c[seam] = BR['lining'][1]
    # inner pocket welt + the slit in the lining (stitched)
    (sx0, sy0), (sx1, sy1) = SLIT
    sy0 += dy
    sy1 += dy
    if state in ('lift', 'open'):
        for k in range(0, int(sx1 - sx0)):
            x = sx0 + k
            y = sy0 + (sy1 - sy0) * k / (sx1 - sx0)
            cv.px(x, y, BR['lining'][0] if state == 'open' else BR['lining'][2])
            if state == 'open' and 6 < k < sx1 - sx0 - 6:
                cv.px(x, y + 1, BR['lining'][0])
            if k % 3 == 0:
                cv.px(x, y - 2, BR['lining'][5])
        # breast-pocket welt higher up
        cv.line(sx0 + 20, sy0 - 26, sx0 + 60, sy0 - 29, BR['lining'][2])
        cv.line(sx0 + 20, sy0 - 25, sx0 + 60, sy0 - 28, BR['lining'][6])
    a = cv.alpha()
    edge = kit.outline_of(a)
    cv.c[edge & (xx < q[1][0] + 30)] = BR['wool'][1]
    return cv.c


def packet_img(cx: float, cy: float, crop_y=None, lamp=LAMP) -> np.ndarray:
    """The twice-folded copy (~56x34) centred at (cx, cy); everything above crop_y is hidden (inside the
    lining)."""
    q = [(cx - 28, cy - 16), (cx + 27, cy - 18), (cx + 29, cy + 15), (cx - 27, cy + 17)]
    cv = kit.Canvas(W, H)
    b.sheet(cv, q, BR['tracing'], lamp, base=0.12, gain=0.95, shadow=False, lift=12)
    a = (cx - 27, cy)
    bb = (cx + 28, cy - 1)
    cv.line(a[0], a[1], bb[0], bb[1], BR['tracing'][2])
    cv.line(cx - 4, cy - 16, cx - 3, cy + 16, BR['tracing'][6])
    # a corner of the red ring shows through the tracing paper
    for k in range(6):
        cv.px(cx + 10 + k, cy + 6 - (k * k) // 6, pg.hx('#A8382E'))
    if crop_y is not None:
        cv.c[:int(math.ceil(crop_y)), :] = 0
    return cv.c


def branch_evidence(out_dir: str) -> list:
    nodes = []
    # ---- copy flipbook (lying on the plan; then picked up)
    at_c = kit.Atlas('b_copy')
    states = [('flat', 0, 0), ('flat', -10, -6), ('lift', -10, -6), ('half', -10, -6), ('quarter', -10, -6)]
    fr = [at_c.add(b.copy_sheet(LAMP, _shift_q(COPY_Q0, dx, dy), st)) for (st, dx, dy) in states]
    c_keys = [[0.0, fr[0]], [0.55, fr[1]], [1.15, fr[2]], [1.55, fr[3]], [2.15, fr[4]], [2.55, -1]]
    nodes.append({'id': 'b_copy', 'type': 'anim', 'atlas': 'b_close/copy.png',
                  'frames': at_c.save(out_dir + '/b_close/copy.png'), 'keys': c_keys, 'z': 11})
    # ---- coat panel
    at_k = kit.Atlas('b_coat')
    kf = {st: at_k.add(coat_panel(st)) for st in ('enter', 'lift', 'open', 'drop')}
    k_keys = [[0.0, -1], [2.85, kf['enter']], [3.15, kf['lift']], [3.85, kf['open']], [4.95, kf['lift']],
              [5.45, kf['drop']], [5.7, -1]]
    nodes.append({'id': 'b_coat', 'type': 'anim', 'atlas': 'b_close/coat.png',
                  'frames': at_k.save(out_dir + '/b_close/coat.png'), 'keys': k_keys, 'z': 16})
    # ---- packet path: picked up from the plan, carried to the slit, pushed up into the lining
    qcx, qcy = kit._lerp(_shift_q(COPY_Q0, -10, -6)[0], b.quad_map(_shift_q(COPY_Q0, -10, -6), 0.52, 0.52), 0.5)
    slit_y = (SLIT[0][1] + SLIT[1][1]) / 2.0
    sx_c = (SLIT[0][0] + SLIT[1][0]) / 2.0
    P = kit.Track(pos=(qcx, qcy), crop=0.0)
    P.key(2.55, pos=(qcx, qcy))
    P.key(3.55, pos=(sx_c, slit_y + 30))
    P.key(4.75, pos=(sx_c - 2, slit_y - 22), ease='lin')
    at_p = kit.Atlas('b_packet')
    p_keys = []
    last = None
    cache = {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        if t < 2.55 or t > 4.8:
            f = -1
        else:
            s = P.at(t)
            px_, py_ = int(round(s['pos'][0])), int(round(s['pos'][1]))
            crop = slit_y if t > 3.5 else None
            k = (px_, py_, crop is not None)
            if k not in cache:
                cache[k] = at_p.add(packet_img(px_, py_, crop))
            f = cache[k]
        if f != last:
            p_keys.append([round(t, 3), f])
            last = f
    nodes.append({'id': 'b_packet', 'type': 'anim', 'atlas': 'b_close/packet.png',
                  'frames': at_p.save(out_dir + '/b_close/packet.png'), 'keys': p_keys, 'z': 17})
    # ---- arms
    kw = dict(sleeve_ramp=BR['wool'], skin_ramp=BR['skin'], cuff_ramp=BR['cuff'], sleeve_w=(30, 42))
    Lt = kit.Track(wrist=V(58, 300), ang=-math.pi / 2 + 0.40, length=60, curl=0.05, thumb='side', entry=V(30, 450))
    Rt = kit.Track(wrist=V(132, 290), ang=-math.pi / 2 - 0.10, length=60, curl=0.08, thumb='side', entry=V(220, 450))
    Rt.key(0.0).key(0.25).key(0.55, wrist=V(122, 284))                         # slides the copy off the original
    Rt.key(1.0, wrist=V(150, 268), ang=-math.pi / 2 - 0.35, curl=0.2, thumb='pinch')
    Rt.key(1.2, wrist=V(154, 260))                                             # lifts the right half
    Rt.key(1.55, wrist=V(104, 274), ang=-math.pi / 2 - 0.15, curl=0.05, thumb='side')   # presses the fold
    Rt.key(1.85, wrist=V(98, 282), curl=0.25, thumb='pinch')
    Rt.key(2.15, wrist=V(96, 268), curl=0.05, thumb='side')                   # second fold pressed
    Rt.key(2.5, wrist=(qcx - 2, qcy + 58), curl=0.3, thumb='pinch', ang=-math.pi / 2 + 0.05)
    Rt.key(3.55, wrist=(sx_c - 2, slit_y + 30 + 58), ang=-math.pi / 2 + 0.05, curl=0.25, thumb='pinch',
           entry=V(320, 450))
    Rt.key(4.75, wrist=(sx_c - 4, slit_y - 22 + 58), curl=0.1, thumb='side', ease='lin')
    Rt.key(5.2, wrist=(sx_c + 10, slit_y + 40), curl=0.0)                            # smooths the lining
    Rt.key(6.0, wrist=V(146, 302), ang=-math.pi / 2 - 0.2, curl=0.15, entry=V(230, 450))
    Rt.key(DUR, wrist=V(146, 302))
    Lt.key(0.0).key(2.45)
    Lt.key(2.85, wrist=V(196, 340), ang=-math.pi / 2 + 0.25, curl=0.45, thumb='under', entry=V(110, 460))
    Lt.key(3.15, wrist=V(192, 290))
    Lt.key(4.95, wrist=V(192, 291))
    Lt.key(5.45, wrist=V(190, 330))
    Lt.key(6.1, wrist=V(58, 302), ang=-math.pi / 2 + 0.4, curl=0.05, thumb='side', entry=V(30, 450))
    Lt.key(DUR, wrist=V(58, 302))
    at_l = kit.Atlas('b_arm_l_ev')
    at_r = kit.Atlas('b_arm_r_ev')
    lk = kit.render_arm_track(Lt, 'L', at_l, W, H, LAMP, 0.0, DUR, FPS, seed=21, **kw)
    rk = kit.render_arm_track(Rt, 'R', at_r, W, H, LAMP, 0.0, DUR, FPS, seed=22, **kw)
    nodes.append({'id': 'b_arm_l', 'type': 'anim', 'atlas': 'b_close/arm_l_ev.png',
                  'frames': at_l.save(out_dir + '/b_close/arm_l_ev.png'), 'keys': lk, 'z': 20,
                  '_atlas': at_l, '_path': out_dir + '/b_close/arm_l_ev.png'})
    nodes.append({'id': 'b_arm_r', 'type': 'anim', 'atlas': 'b_close/arm_r_ev.png',
                  'frames': at_r.save(out_dir + '/b_close/arm_r_ev.png'), 'keys': rk, 'z': 21,
                  '_atlas': at_r, '_path': out_dir + '/b_close/arm_r_ev.png'})
    for n in nodes:
        n['when'] = {'m1_choose': 'preserve_evidence'}
    return nodes
