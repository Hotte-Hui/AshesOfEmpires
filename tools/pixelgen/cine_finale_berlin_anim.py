"""cine_finale_berlin_anim -- animated layers of the Berlin desk close-up (owner: trans-finale).

Branch m1_choose:
  request_explanation  Konrad types a formal request on office letterhead (red ribbon for 'C-17'), throws the
                       carriage, stops, hesitates (sits back, the right hand closes), leans in, pulls the sheet
                       out by its top edge and lays it into the AUSGANG tray.
  preserve_evidence    he separates his tracing-paper copy from the stamped original and folds it twice, pulls
                       the left front panel of his coat up over the edge of the desk (lining up), slides the
                       packet through the slit of the inner pocket, smooths it and lets the panel fall back.
Every moving part is rasterised per frame from geometry (no rotated or scaled pixels) and packed into atlases;
times are local to the shot (seconds).  Letterhead / stamp frames exist twice (neutral + _hist, same rects).
The figure is cine_finale_figure's 3D rig (over the shoulder, camera fitted to the set).
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as b
import cine_finale_figure as fig
import pg

BR = kit.BR
W, H = b.W, b.H
V = b.V
LAMP = b.LAMP_B
FPS = 12.0
DUR = 8.0
P = -math.pi / 2

# ------------------------------------------------------------------------------------------- typewriter paper
PAPER_W, PAPER_H = 76, 104
MARGIN = 8
PLATEN = V(0, 146)[1]          # set y of the platen line (paper disappears below)
STRIKE = V(250, 0)[0]          # set x of the type guide
TYPE_Y0, LINE_SP = 40, 4
LINES = ['Betr.: Vorgang C-17', 'Ich bitte um Auskunft zur Aenderung', 'der Plaene im Bestand C.']
RED_SPANS = {0: (14, 18)}      # chars typed with the red half of the ribbon
PULL_PX = 14                   # the sheet slides this far up out of the platen before it comes free


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
    em = kit.state_emblem(17, hist)
    ex = left + (PAPER_W - em.shape[1]) // 2
    ey = top + 4
    kit.blit_mask(cv.c, em, ex, ey, BR['ink'][1])
    for k, wd in ((0, 44), (1, 30)):
        y = top + 4 + em.shape[0] + 3 + k * 3
        for x in range(left + (PAPER_W - wd) // 2, left + (PAPER_W + wd) // 2):
            if (x * 7 + k * 3) % 5 != 0:
                cv.px(x, y, BR['ink'][1] if k == 0 else BR['paper'][3])
    ry = top + 4 + em.shape[0] + 10
    cv.line(left + 6, ry, left + PAPER_W - 7, ry, BR['paper'][4])
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
    img = cv.c[top:top + visible, left:left + PAPER_W].copy()
    return img, left, top


def paper_flat(quad, hist: bool, lamp=LAMP) -> np.ndarray:
    """The finished request lying flat (in the tray / carried): letterhead + text rows."""
    cv = kit.Canvas(W, H)
    b.sheet(cv, quad, BR['paper'], lamp, base=0.10, gain=1.0, shadow=False, lift=6)
    em = kit.state_emblem(17, hist)
    cx, cy = b.quad_map(quad, 0.5, 0.06)
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
T_PULL = (6.05, 6.45)
T_SWING = (6.45, 6.85)          # the free sheet comes down towards him
T_CARRY = (6.85, 7.45)          # ... and into the AUSGANG tray at the front right


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


def carriage_dx(t: float) -> int:
    return typing_state(t)[2] if t < T_PULL[1] else -len(LINES[1])


# hand anchors as blend weights (palm, tips, pinch, grip, knuckles) so a change of grip never pops
def A(name: str):
    return tuple(1.0 if n == name else 0.0 for n in fig.ANCHOR_NAMES)


POLE_L = (-0.26, -0.42, -0.12)
POLE_R = (0.26, -0.42, -0.12)
POLE_L_WIDE = (-0.46, -0.22, -0.02)
POLE_R_WIDE = (0.46, -0.22, -0.02)

# poses of the request branch
KEY_L = dict(at=(250, 200), h=0.07, anchor=A('tips'), ang=P + 0.45, curl=0.72, thumb='under', pitch=0.0,
             roll=0.0, pole=POLE_L)
KEY_R = dict(at=(298, 200), h=0.07, anchor=A('tips'), ang=P - 0.45, curl=0.72, thumb='under', pitch=0.0,
             roll=0.0, pole=POLE_R)
ANCHOR_REQ = (272, 314)


def letter_quad(t: float):
    """The sheet once it has come free of the platen, held by its top edge (right hand): swung down towards
    him (tilted, the letterhead towards the lamp), then laid into the AUSGANG tray at the front right."""
    n1 = len(LINES[1])
    left_end = STRIKE - MARGIN - n1
    top_end = PLATEN - (TYPE_Y0 + 9 + LINE_SP + PULL_PX)
    v_q = [(left_end, top_end), (left_end + PAPER_W, top_end), (left_end + PAPER_W, top_end + PAPER_H * 0.55),
           (left_end, top_end + PAPER_H * 0.55)]
    held = [(290, 150), (356, 146), (362, 204), (294, 210)]
    x0, y0, x1, y1 = b.OUT_TRAY
    tray_q = [(x0 + 5, y0 + 3), (x1 - 7, y0 + 2), (x1 - 4, y1 - 2), (x0 + 6, y1 - 1)]
    if t < T_SWING[1]:
        f = kit._ease((t - T_SWING[0]) / (T_SWING[1] - T_SWING[0]))
        a_q, b_q, lift = v_q, held, 0.0
    else:
        f = kit._ease((t - T_CARRY[0]) / (T_CARRY[1] - T_CARRY[0]))
        a_q, b_q, lift = held, tray_q, 10.0
    q = []
    for i, ((vx, vy), (tx, ty)) in enumerate(zip(a_q, b_q)):
        q.append((vx + (tx - vx) * f, vy + (ty - vy) * f - math.sin(f * math.pi) * lift * (1.0 if i < 2 else 0.5)))
    return q, f


def letter_grip(q):
    """Where the right hand holds the sheet: on the top edge, 70 % towards its right corner."""
    return (q[0][0] + (q[1][0] - q[0][0]) * 0.70, q[0][1] + (q[1][1] - q[0][1]) * 0.70)


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
    sig_cache = {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        line, chars, cdx, pdy, vis = typing_state(t)
        hidden = False
        if t >= T_PULL[0]:
            f = kit._ease((t - T_PULL[0]) / (T_PULL[1] - T_PULL[0]))
            vis = int(round(pull_v0 + PULL_PX * f))
            if t >= T_PULL[1]:
                hidden = True       # handed over to the carried / flat sheet
        sig = (line, chars, vis, hidden, cdx)
        if sig not in sig_cache:
            if hidden:
                sig_cache[sig] = -1
            else:
                img, ox, oy = paper_frame(line, chars, vis, False, dx=cdx + chars, dy=0)
                imgh, _, _ = paper_frame(line, chars, vis, True, dx=cdx + chars, dy=0)
                sig_cache[sig] = (at_p.add_cropped(img, ox, oy), at_ph.add_cropped(imgh, ox, oy))
        fr = sig_cache[sig]
        frn = fr if fr == -1 else fr[0]
        if frn != last:
            p_keys.append([round(t, 3), frn])
            last = frn
        cx = carriage_dx(t)
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
    at_b = kit.Atlas('b_typebar')
    cv = np.zeros((H, W, 4), np.uint8)
    at_b.add(cv)
    bar = kit.Canvas(W, H)
    bar.line(*V(250, 176), *V(250, 140), BR['metal'][6])
    bar.line(*V(249, 176), *V(249, 142), BR['metal'][3])
    at_b.add(bar.c)
    nodes.append({'id': 'b_typebar', 'type': 'anim', 'atlas': 'b_close/typebar.png',
                  'frames': at_b.save(out_dir + '/b_close/typebar.png'), 'keys': bar_keys, 'z': 14})
    car = b.carriage(W, H, LAMP)
    kit.save_rgba(car, out_dir + '/b_close/carriage.png')
    nodes.append({'id': 'b_carriage', 'type': 'sprite', 'file': 'b_close/carriage.png', 'z': 13,
                  'pos_keys': c_keys, 'step': True})
    # --- carried / laid down sheet (held by its top edge until it lies in the tray)
    at_s = kit.Atlas('b_letter')
    at_sh = kit.Atlas('b_letter_hist')
    s_keys = []
    last = None
    cache = {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        if t < T_PULL[1]:
            fr = -1
        else:
            q, f = letter_quad(t)
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
    # --- Konrad over the shoulder
    body = kit.Track(lean=(0.0, 0.0), head=(0.0, 0.0), breathe=0.0)
    L = kit.Track(**KEY_L, typing=0)
    R = kit.Track(**KEY_R, typing=0)
    L.key(0.0, typing=0).key(T_LINE0[0], typing=1).key(T_LINE0[1], typing=0)
    R.key(0.0, typing=0).key(T_LINE0[0], typing=1).key(T_LINE0[1], typing=0)
    # carriage return: the left hand goes to the chrome lever (front left of the carriage) and throws it
    lx0, ly0 = b.LEVER_TIP
    n0 = len(LINES[0])
    lever_end = (lx0 - n0, ly0)
    L.key(T_CR1[0] + 0.14, at=(lever_end[0] - 3, lever_end[1] + 1), h=0.13, anchor=A('tips'), ang=P + 1.05, curl=0.62,
          thumb='side', pole=POLE_L_WIDE)
    L.key(T_CR1[0] + 0.25, at=(lever_end[0] - 1, lever_end[1]))
    L.key(T_CR1[0] + 0.55, at=(lever_end[0] - 1 + n0, lever_end[1]), ease='lin')
    L.key(T_CR1[0] + 0.68, at=(lever_end[0] + n0 + 6, lever_end[1] + 6), curl=0.5)
    L.key(T_LINE1[0] - 0.02, **KEY_L)
    body.key(T_CR1[0] + 0.14, lean=(-0.06, 0.10)).key(T_CR1[0] + 0.55, lean=(-0.02, 0.08))
    body.key(T_LINE1[0], lean=(0.0, 0.0))
    L.key(T_LINE1[0] + 0.01, typing=1).key(T_LINE1[1], typing=0)
    R.key(T_LINE1[0] + 0.01, typing=1).key(T_LINE1[1], typing=0)
    # hesitation: hands lift off the keys onto the front of the machine, he sits back and looks to the window;
    # the right hand closes into a fist
    L.key(T_HES[0] + 0.35, at=(240, 226), h=0.03, anchor=A('palm'), ang=P + 1.1, curl=0.55, thumb='side')
    R.key(T_HES[0] + 0.35, at=(308, 226), h=0.03, anchor=A('palm'), ang=P - 1.1, curl=0.55, thumb='side')
    R.key(T_HES[0] + 0.85, at=(308, 228), anchor=A('knuckles'), curl=0.95, thumb='under')
    R.key(T_HES[1], at=(309, 228))
    L.key(T_HES[1], at=(239, 227), curl=0.5)
    body.key(T_HES[0] + 0.5, lean=(0.0, -0.06), head=(4.0, 1.0), breathe=1.0)
    body.key(T_HES[0] + 1.0, breathe=0.0)
    body.key(T_HES[1], lean=(0.0, -0.05), head=(3.0, 1.0), breathe=1.0)
    # reach: he leans in, the right hand takes the top edge of the sheet and pulls it out of the platen
    pinch_x = STRIKE - MARGIN - len(LINES[1]) + int(PAPER_W * 0.70)
    top0 = PLATEN - (TYPE_Y0 + 9 + LINE_SP)
    R.key(T_REACH[0] + 0.1, at=(318, 214), h=0.04, anchor=A('palm'), curl=0.5, thumb='side', ang=P - 1.0)
    R.key(T_REACH[1], at=(pinch_x, top0 + 2), h=0.22, anchor=A('pinch'), ang=P - 0.95, curl=0.5,
          curls=(0.4, 0.78, 0.88, 0.92), thumb='pinch', pitch=-0.45, pole=POLE_R_WIDE)
    R.key(T_PULL[1], at=(pinch_x, top0 - PULL_PX + 2), h=0.27, ease='lin')
    L.key(T_REACH[1], at=(244, 222), h=0.03, anchor=A('palm'), curl=0.55, thumb='side', ang=P + 1.1)
    body.key(T_REACH[1], lean=(0.05, 0.22), head=(1.0, -2.0), breathe=0.0)
    body.key(T_PULL[1], lean=(0.06, 0.24))
    # swing + lay down: the hand holds the top edge all the way into the tray
    t = T_PULL[1]
    while t < T_CARRY[1] - 1e-6:
        t = min(T_CARRY[1], t + 1.0 / FPS)
        q, f = letter_quad(t)
        gx, gy = letter_grip(q)
        sw = t < T_SWING[1]
        R.key(t, at=(gx, gy + 1), h=(0.27 - 0.17 * f) if sw else (0.10 - 0.08 * f),
              pitch=(-0.45 + 0.25 * f) if sw else -0.2 + 0.2 * f, ang=P - 0.95 - 0.45 * (f if not sw else 0.0),
              pole=POLE_R, ease='lin')
    R.key(T_CARRY[1] + 0.15, at=(letter_grip(letter_quad(T_CARRY[1])[0])[0] - 8,
                                 letter_grip(letter_quad(T_CARRY[1])[0])[1] + 14), curl=0.6, curls=None,
          thumb='side', anchor=A('palm'), h=0.0, pitch=0.0, ang=P - 1.45)
    R.key(DUR - 0.1, at=(318, 238), curl=0.6, ang=P - 1.3)
    body.key(T_SWING[1], lean=(0.04, 0.10), head=(2.0, 0.0)).key(T_CARRY[1], lean=(0.10, 0.04), head=(3.0, 1.0))
    body.key(DUR - 0.2, lean=(0.02, 0.0), head=(0.0, 0.0), breathe=1.0)
    L.key(T_CARRY[1], at=(242, 224)).key(DUR, at=(238, 230), curl=0.55)
    fig_nodes(nodes, 'konrad', ANCHOR_REQ, body, L, R, out_dir, 'req')
    for n in nodes:
        n['when'] = {'m1_choose': 'request_explanation'}
    return nodes


SHADOW_B = (5, 4, BR['desk'][1])


def fig_nodes(nodes, who, anchor, body, L, R, out_dir, tag, extras=None, lamp=None, light=None, shadow=None,
              max_lean=0.45, z=(20, 21, 23), set_dir='b_close', prefix='b'):
    """Render a FigureRig (body + arms) into atlases and append the anim nodes (arm_l, arm_r, body)."""
    lamp = lamp or LAMP
    light = light or (LAMP.sx + 40, LAMP.sy - 60)
    rig = fig.FigureRig(who, body, L, R, lamp, light, anchor, shadow=shadow or SHADOW_B, max_lean=max_lean)
    fig.rig_nodes(nodes, rig, out_dir, set_dir, prefix, tag, DUR, FPS, extras=extras, z=z)
    return rig


# ------------------------------------------------------------------------------------------- branch A
COPY_Q0 = [V(46, 202), V(150, 198), V(154, 260), V(50, 264)]
COPY_Q1 = [(x - 10, y - 6) for (x, y) in COPY_Q0]          # slid off the stamped original
ANCHOR_EV = (236, 314)

# lining of Konrad's overcoat: wine-red satin with a fine woven stripe and a bright sheen; the coat's navy
# wool from his sleeve
LINING = [pg.hx(c) for c in ('#12080C', '#220C12', '#3A1018', '#55141F', '#731C26', '#91282E', '#AE3F3A',
                             '#C8604E', '#DE8A6C', '#F0B894')]
NAVY = fig.COSTUMES['konrad']['sleeve']
LABEL = [pg.hx(c) for c in ('#3A2F24', '#8E8A78', '#CEC6AA', '#F5EFDA')]

# the opened left front panel, laid over the edge of the desk (o = 1): hinge under his arm (right, below the
# frame), the shoulder seam on top, the front edge with the navy facing on the left
PANEL_OPEN = {'h0': (186, 362), 'h1': (176, 300), 'h2': (170, 262), 't': (128, 247), 'l0': (104, 253),
              'l1': (92, 300), 'l2': (100, 362)}
SLIT = ((114, 276), (140, 273))                             # inner pocket welt, slit along it
LABEL_AT = (150, 258)


def _panel_pts(o: float, wob: float = 0.0):
    """Outline control points of the panel at opening o (0 = hanging closed under the arm, 1 = laid open)."""
    hinge = (182.0, 372.0)
    out = {}
    for k_, (x, y) in PANEL_OPEN.items():
        # closed: everything folded down to the hinge line below the frame; opening swings it up and out
        cx = hinge[0] + (x - hinge[0]) * 0.35
        cy = hinge[1] + 30.0
        e = kit._ease(o)
        px = cx + (x - cx) * e
        py = cy + (y - cy) * e
        # the free edge lifts while it travels (the cloth billows), then settles
        if k_ in ('t', 'l0', 'l1'):
            py -= math.sin(min(1.0, o) * math.pi) * 10.0
            px -= math.sin(min(1.0, o) * math.pi) * 4.0
        if k_ in ('t', 'l0', 'h2'):
            py += wob * (1.0 if k_ != 'h2' else 0.4)
        out[k_] = (px, py)
    return out


def coat_panel(o: float, wob: float = 0.0, slit_open: float = 0.0, lamp=LAMP) -> np.ndarray:
    """The left front panel of Konrad's overcoat pulled up over the desk, lining up: champagne satin with a
    woven stripe and soft folds radiating from the hinge, the navy wool facing with two buttonholes along the
    front edge, the inner pocket welt with its slit (slit_open widens it as the packet goes in), the tailor's
    label.  Returns RGBA (set size)."""
    cv = kit.Canvas(W, H)
    if o <= 0.02:
        return cv.c
    pp = _panel_pts(o, wob)
    h0, h1, h2, t_, l0, l1, l2 = (pp[k_] for k_ in ('h0', 'h1', 'h2', 't', 'l0', 'l1', 'l2'))
    edge_hinge = pg.bezier([h0, ((h0[0] + h1[0]) / 2 + 3, (h0[1] + h1[1]) / 2), h1], n=20) + \
        pg.bezier([h1, ((h1[0] + h2[0]) / 2 + 2, (h1[1] + h2[1]) / 2), h2], n=16)
    edge_top = pg.bezier([h2, ((h2[0] + t_[0]) / 2, (h2[1] + t_[1]) / 2 - 3), t_], n=20) + \
        pg.bezier([t_, ((t_[0] + l0[0]) / 2, (t_[1] + l0[1]) / 2 - 1), l0], n=10)
    edge_front = pg.bezier([l0, (l0[0] - 9, (l0[1] + l1[1]) / 2), l1], n=20) + \
        pg.bezier([l1, (l1[0] - 2, (l1[1] + l2[1]) / 2), l2], n=20)
    poly = edge_hinge + edge_top + edge_front
    m = kit.poly_mask_full(W, H, poly)
    if not m.any():
        return cv.c
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=8)
    # frame of the cloth: u across (front edge -> hinge), v down from the shoulder seam
    ex, ey = (h2[0] - l0[0]), (h2[1] - l0[1])
    el = math.hypot(ex, ey) + 1e-6
    ux, uy = ex / el, ey / el
    u = ((xx - l0[0]) * ux + (yy - l0[1]) * uy) / el
    v = (-(xx - l0[0]) * uy + (yy - l0[1]) * ux)
    # soft folds radiating from the hinge (under his arm), sheen on their crests
    hx, hy = h0
    ang = np.arctan2(yy - hy, xx - hx)
    fold = np.sin(ang * 11.0 + 0.6 * np.sin(v / 13.0) + wob * 0.2) * 0.5 + 0.5
    fold2 = np.sin(ang * 23.0 - v / 31.0) * 0.5 + 0.5
    near_h = np.clip(1.0 - np.hypot(xx - hx, yy - hy) / 110.0, 0, 1)
    tone = 0.10 + 0.78 * pool * (0.62 + 0.38 * fold) + 0.16 * (fold > 0.90) * pool - 0.10 * (fold < 0.12) \
        + 0.04 * (fold2 > 0.86) - 0.22 * near_h ** 1.5
    # woven stripe of the lining (every 5 px across, broken by the folds)
    stripe = (np.abs(((u * el) % 5.0) - 2.5) < 0.55) & (fold > 0.2)
    tone = np.where(stripe, tone - 0.07, tone)
    cv.paint(m, np.clip(tone, 0, 1), LINING)
    # navy wool facing along the front edge (inside of the coat's front), 7 px, with two buttonholes
    band = np.zeros((H, W), bool)
    for pts in (edge_front, edge_top[len(edge_top) - 10:]):
        for (p0, p1) in zip(pts[:-1], pts[1:]):
            vx, vy = p1[0] - p0[0], p1[1] - p0[1]
            L2 = vx * vx + vy * vy + 1e-6
            tp = np.clip(((xx - p0[0]) * vx + (yy - p0[1]) * vy) / L2, 0, 1)
            d = np.hypot(xx - (p0[0] + tp * vx), yy - (p0[1] + tp * vy))
            band |= d < 7.5
    band &= m
    wt = 0.08 + 0.62 * pool + 0.07 * (np.sin((xx + yy) / 2.2) > 0.7) - 0.12 * near_h
    cv.paint(band, np.clip(wt, 0, 1), NAVY)
    for k_ in (0.30, 0.62):
        bx_, by_ = edge_front[int(len(edge_front) * k_)]
        cv.line(bx_ + 2, by_, bx_ + 6, by_ - 1, NAVY[1])
        cv.px(bx_ + 6, by_ - 1, NAVY[0])
    # the outside of the coat shows along the free edges as a dark rim (the wool has a thickness)
    rim = kit.outline_of(m) & (band | (yy < h2[1] + 4))
    cv.c[rim] = NAVY[1]
    seam = kit.outline_of(band) & m & ~kit.outline_of(m)
    cv.c[seam] = LINING[2]
    # armhole seam near the hinge (curved stitched line)
    for k_ in range(18):
        f_ = k_ / 17.0
        sx = h2[0] - 8 + 6 * math.sin(f_ * 1.6)
        sy = h2[1] + 4 + f_ * 34
        if m[int(sy), int(sx)] if 0 <= int(sy) < H and 0 <= int(sx) < W else False:
            cv.px(sx, sy, LINING[2] if k_ % 2 == 0 else LINING[3])
    # inner pocket welt + slit, and the tailor's label (only once the panel lies open enough)
    if o > 0.75:
        (sx0, sy0), (sx1, sy1) = SLIT
        dy0 = (pp['t'][1] - PANEL_OPEN['t'][1])
        n = int(sx1 - sx0)
        for k_ in range(n):
            x = sx0 + k_
            y = sy0 + (sy1 - sy0) * k_ / n + dy0 * 0.5
            cv.px(x, y - 2, LINING[7])                          # welt lip catches the light
            cv.px(x, y - 1, LINING[5])
            gap = 1 + (1 if (slit_open > 0.3 and 3 < k_ < n - 3) else 0)
            for g in range(gap):
                cv.px(x, y + g, LINING[0])
            cv.px(x, y + gap, LINING[3])
            if k_ % 3 == 1:
                cv.px(x, y + gap + 2, LINING[4])                 # stitching under the welt
        for e_ in (0, n):
            cv.px(sx0 + e_, sy0 + (sy1 - sy0) * e_ / n + dy0 * 0.5 - 1, LINING[2])
            cv.px(sx0 + e_, sy0 + (sy1 - sy0) * e_ / n + dy0 * 0.5, LINING[2])
        lx, ly = LABEL_AT
        ly += dy0 * 0.4
        lab = kit.poly_mask_full(W, H, [(lx - 7, ly - 3), (lx + 7, ly - 4), (lx + 7, ly + 2), (lx - 7, ly + 3)])
        cv.paint(lab, np.clip(0.45 + 0.6 * pool, 0, 1), LABEL)
        for k_ in range(-5, 6, 2):
            cv.px(lx + k_, ly - 1, LABEL[0])
        for k_ in range(-3, 4, 2):
            cv.px(lx + k_, ly + 1, LABEL[1])
    a = cv.alpha()
    # contact shadow of the lifted cloth on the desk / plan (cast down-right, away from the lamp)
    sh = kit.shift(a, 4, 3) & ~a
    out = np.zeros((H, W, 4), np.uint8)
    bay = kit.bayer_full(W, H)
    s_sel = sh & (bay < 0.55)
    out[s_sel, :3] = np.asarray(BR['desk'][1], np.uint8)[:3]
    out[s_sel, 3] = 255
    kit.over(out, cv.c)
    return out


def packet_img(cx: float, cy: float, ang: float = 0.0, crop_line=None, lamp=LAMP) -> np.ndarray:
    """The twice-folded copy (~30x19) centred at (cx, cy), turned by ang; the part past crop_line
    ((x0, y0), (x1, y1): the slit, everything above it hidden inside the lining) is cut away."""
    c, s = math.cos(ang), math.sin(ang)

    def R_(x, y):
        return cx + x * c - y * s, cy + x * s + y * c
    q = [R_(-15, -9), R_(14, -10), R_(15, 9), R_(-14, 10)]
    cv = kit.Canvas(W, H)
    b.sheet(cv, q, BR['tracing'], lamp, base=0.12, gain=0.95, shadow=False, lift=10)
    a0, a1 = R_(-14, 0), R_(14, -1)
    cv.line(a0[0], a0[1], a1[0], a1[1], BR['tracing'][2])
    m0, m1 = R_(-1, -9), R_(0, 9)
    cv.line(m0[0], m0[1], m1[0], m1[1], BR['tracing'][6])
    for k in range(4):
        x, y = R_(5 + k, 4 - (k * k) // 4)
        cv.px(x, y, pg.hx('#A8382E'))
    if crop_line is not None:
        (x0, y0), (x1, y1) = crop_line
        xx, yy = cv.grid()
        # signed side of the slit line: above it (inside the lining) is hidden
        side = (xx - x0) * (y1 - y0) - (yy - y0) * (x1 - x0)
        cv.c[side > 0] = 0
    return cv.c


def branch_evidence(out_dir: str) -> list:
    nodes = []
    # ---- copy flipbook (lying on the plan; slid off the original; folded twice; then picked up)
    at_c = kit.Atlas('b_copy')
    states = [('flat', COPY_Q0), ('flat', COPY_Q1), ('lift', COPY_Q1), ('half', COPY_Q1), ('quarter', COPY_Q1)]
    fr = [at_c.add(b.copy_sheet(LAMP, q, st)) for (st, q) in states]
    T_PICK = 3.88
    c_keys = [[0.0, fr[0]], [0.55, fr[1]], [1.15, fr[2]], [1.55, fr[3]], [2.15, fr[4]], [T_PICK, -1]]
    nodes.append({'id': 'b_copy', 'type': 'anim', 'atlas': 'b_close/copy.png',
                  'frames': at_c.save(out_dir + '/b_close/copy.png'), 'keys': c_keys, 'z': 11})
    # ---- coat panel, rendered per frame (12 fps): pulled up 2.75-3.35, settles, lies open, falls back 5.3-5.85
    at_k = kit.Atlas('b_coat')
    k_keys = []
    cache = {}
    last = None
    T_IN = (4.20, 4.90)

    def panel_state(t):
        if t < 2.70:
            return 0.0, 0.0
        if t < 3.35:
            return (t - 2.70) / 0.65, 0.0
        if t < 5.30:
            # settles with a small damped sway, then lies still; a tiny lift while the packet goes in
            wob = 2.0 * math.exp(-(t - 3.35) * 5.0) * math.sin((t - 3.35) * 14.0)
            if T_IN[0] <= t < T_IN[1] + 0.2:
                wob += 1.0 * math.sin((t - T_IN[0]) / (T_IN[1] + 0.2 - T_IN[0]) * math.pi)
            return 1.0, wob
        if t < 5.85:
            return 1.0 - (t - 5.30) / 0.55, 0.0
        return 0.0, 0.0
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        o, wob = panel_state(t)
        sl = 1.0 if T_IN[0] <= t <= T_IN[1] + 0.1 else 0.0
        key = (round(o, 2), round(wob), sl)
        if o <= 0.02:
            f = -1
        else:
            if key not in cache:
                cache[key] = at_k.add(coat_panel(o, round(wob), sl))
            f = cache[key]
        if f != last:
            k_keys.append([round(t, 3), f])
            last = f
    nodes.append({'id': 'b_coat', 'type': 'anim', 'atlas': 'b_close/coat.png',
                  'frames': at_k.save(out_dir + '/b_close/coat.png'), 'keys': k_keys, 'z': 16})
    # ---- Konrad: the left hand does the work, the right hand keeps the stamped original flat
    qc = b.quad_map(COPY_Q1, 0.26, 0.26)                 # centre of the folded packet on the plan
    slit_mid = ((SLIT[0][0] + SLIT[1][0]) / 2.0, (SLIT[0][1] + SLIT[1][1]) / 2.0)
    body = kit.Track(lean=(0.0, 0.0), head=(0.0, 0.0), breathe=0.0)
    REST_R = dict(at=(280, 244), h=0.0, anchor=A('palm'), ang=P - 1.15, curl=0.55, thumb='side', pitch=0.0,
                  roll=0.0, pole=POLE_R)
    Lt = kit.Track(at=b.quad_map(COPY_Q0, 0.55, 0.55), h=0.0, anchor=A('palm'), ang=P + 1.05, curl=0.35,
                   thumb='side', pitch=0.0, roll=0.0, pole=POLE_L, packet=0)
    Rt = kit.Track(**REST_R)
    lift_mid = b.quad_map(COPY_Q1, 0.5, 0.5)
    Lt.key(0.0).key(0.20, at=b.quad_map(COPY_Q0, 0.55, 0.55))
    Lt.key(0.55, at=b.quad_map(COPY_Q1, 0.55, 0.55))                                  # slides the copy off
    Lt.key(0.95, at=b.quad_map(COPY_Q1, 0.98, 0.5), anchor=A('pinch'), curl=0.3, thumb='pinch', ang=P + 0.25,
           h=0.01)                                                                     # takes the right edge
    Lt.key(1.15, at=(lift_mid[0] + 14, lift_mid[1] - 19), h=0.07)                     # lifts it
    Lt.key(1.50, at=b.quad_map(COPY_Q1, 0.06, 0.5), h=0.02)                           # lays it over
    Lt.key(1.62, at=b.quad_map(COPY_Q1, 0.30, 0.5), anchor=A('palm'), curl=0.35, thumb='side', ang=P + 1.1,
           h=0.0)                                                                       # runs the fold flat
    Lt.key(1.80, at=b.quad_map(COPY_Q1, 0.26, 0.95), anchor=A('pinch'), curl=0.3, thumb='pinch', ang=P + 0.5,
           h=0.01)                                                                     # takes the bottom edge
    Lt.key(2.05, at=b.quad_map(COPY_Q1, 0.26, 0.10), h=0.05)                          # folds it up
    Lt.key(2.25, at=qc, anchor=A('knuckles'), curl=0.62, thumb='under', ang=P + 0.9, h=0.0)  # presses the folds
    Lt.key(2.50, at=(qc[0] + 3, qc[1] + 1))
    # the coat: down to the front edge of the panel (below the frame), pulls it up over the desk edge
    Lt.key(2.72, at=(150, 336), h=0.03, anchor=A('grip'), curl=0.85, thumb='wrap', ang=P + 1.2, pole=POLE_L_WIDE)
    pts_open = _panel_pts(1.0)
    hold = ((pts_open['t'][0] + pts_open['l0'][0]) / 2.0, (pts_open['t'][1] + pts_open['l0'][1]) / 2.0)
    for i in range(1, 9):
        t = 2.70 + 0.65 * i / 8.0
        pp = _panel_pts((t - 2.70) / 0.65)
        Lt.key(t, at=((pp['t'][0] + pp['l0'][0]) / 2.0, (pp['t'][1] + pp['l0'][1]) / 2.0 + 1), ease='lin',
               h=0.03 + 0.06 * math.sin(i / 8.0 * math.pi))
    Lt.key(3.47, at=(hold[0] + 16, hold[1] + 12), anchor=A('palm'), curl=0.40, thumb='side', ang=P + 1.15, h=0.01,
           pole=POLE_L)                                                                 # smooths the lining
    Lt.key(3.62, at=(hold[0] + 30, hold[1] + 26))
    Lt.key(T_PICK, at=qc, anchor=A('pinch'), curl=0.32, thumb='pinch', ang=P + 0.5, h=0.01)  # takes the packet
    Lt.key(T_PICK + 0.02, packet=1)
    Lt.key(T_IN[0], at=(slit_mid[0] + 4, slit_mid[1] + 20), h=0.02, ang=P + 0.15)     # brings it to the slit
    Lt.key(T_IN[1], at=(slit_mid[0] + 2, slit_mid[1] + 3), h=0.015, ease='lin')       # pushes it in
    Lt.key(T_IN[1] + 0.04, packet=0)
    Lt.key(5.05, at=(slit_mid[0] + 3, slit_mid[1] + 9), anchor=A('palm'), curl=0.45, thumb='side', ang=P + 1.1,
           h=0.0)                                                                        # pats it flat
    Lt.key(5.18, at=(slit_mid[0] + 2, slit_mid[1] + 6))
    Lt.key(5.30, at=hold, anchor=A('grip'), curl=0.75, thumb='wrap', ang=P + 0.9, h=0.03, pole=POLE_L_WIDE)
    for i in range(1, 7):
        t = 5.30 + 0.55 * i / 6.0
        pp = _panel_pts(1.0 - (t - 5.30) / 0.55)
        Lt.key(t, at=((pp['t'][0] + pp['l0'][0]) / 2.0, (pp['t'][1] + pp['l0'][1]) / 2.0 + 1), ease='lin')
    Lt.key(6.30, at=(150, 252), anchor=A('palm'), curl=0.5, thumb='side', ang=P + 1.1, h=0.0, pole=POLE_L)
    Lt.key(DUR, at=(152, 253))
    # the right hand holds the original down, shifts when he leans, rests on it at the end
    Rt.key(0.0).key(0.9, at=(276, 244)).key(2.6, at=(272, 246), curl=0.5)
    Rt.key(3.6, at=(270, 247)).key(5.6, at=(272, 246)).key(6.4, at=(278, 244), curl=0.45).key(DUR, at=(279, 244))
    body.key(0.6, lean=(-0.10, 0.04), head=(-3.0, 2.0)).key(2.3, lean=(-0.14, 0.06), head=(-4.0, 2.0))
    body.key(2.75, lean=(-0.10, -0.04), head=(-5.0, 4.0)).key(3.4, lean=(-0.12, 0.0), head=(-4.0, 4.0))
    body.key(4.8, lean=(-0.14, 0.02), head=(-4.0, 3.0)).key(5.9, lean=(-0.06, -0.02), head=(-2.0, 2.0), breathe=1.0)
    body.key(6.8, lean=(-0.04, 0.0), head=(0.0, 0.0), breathe=0.0).key(7.7, breathe=1.0)

    def packet_extra(t, s, rgba, info):
        if not s.get('packet') or s.get('packet', 0) < 0.5:
            return None
        px, py = info['anchors']['pinch']
        crop = SLIT if t >= T_IN[0] - 0.05 else None
        ang_ = -0.10
        if rgba is None:
            return (round(px), round(py), crop is not None)
        # the fingers hold the near edge; the packet points ahead of them (into the slit)
        kit.over(rgba, packet_img(px + 1, py - 8, ang_, crop_line=crop))
        return None
    fig_nodes(nodes, 'konrad', ANCHOR_EV, body, Lt, Rt, out_dir, 'ev', extras={'L': packet_extra})
    for n in nodes:
        n['when'] = {'m1_choose': 'preserve_evidence'}
    return nodes
