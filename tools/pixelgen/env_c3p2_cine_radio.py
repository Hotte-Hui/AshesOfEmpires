"""env_c3p2_cine_radio -- art of LS_C3_Radio (owner: cinematics stream, round 8; C3P2_DESIGN §2.9).

r1/r6  the station square at night from the station roof (one painting, two shots): Hotel Europa (Konrad, left)
       and Hotel Nord (Alexei, right) face each other across the snow, the palais with its dark east wing at the
       far end; pinhole camera SQ shared with scenes/cinematics/ch3_radio/ch3_radio.gd (walker paths, footprints
       and the lit windows are computed here and handed over in layout.json)
r2     Alexei's room in the Hotel Nord: the table at the window, the Bakelite radio, the tea glass; across the
       square Konrad's lit window
r3     Konrad's room in the Hotel Europa: the same radio model at the same place (the match cut on the dial),
       the notepad, the desk lamp; across the square Alexei's lit window
r4     split: the two doors from the floor, the gap of corridor light; the folded note; the note close-up in two
       languages (its words are copied from data/locale/de_c3p2_cinematics.json)
r5     Café „Korridor" after closing: chairs on the tables, Elena's table with an untouched glass, the station
       clock outside (its hands are drawn at runtime: 0.10)
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, PAPER, BRASS, BAKE, RED, K_COAT,
                               A_COAT, A_FUR, grid, poly, ell, box, hexrgb)
import pg

L = Q.LAYOUT.setdefault('radio', {})

# ======================================================================================= the square (r1/r6)
SQ = {'f': 360.0, 'H': 10.0, 'yh': 120.0, 'cx': 320.0}
HOTEL_X = 24.0                       # facades at X = -24 (Europa) and +24 (Nord)
HOTEL_Z = (18.0, 95.0)
PALAIS_Z = 150.0
DOOR_K = (-24.0, 38.0)               # Europa entrance (X, Z) - Konrad
DOOR_A = (24.0, 43.25)               # Nord entrance - Alexei
WIN_K = (50.6, 53.4, 13.2, 15.4)     # Konrad's window on the Europa facade: Z0, Z1, Y0, Y1
WIN_A = (58.2, 60.8, 7.9, 9.7)       # Alexei's window on the Nord facade
EAST_WING = (22.0, PALAIS_Z)         # where the two tracks converge


def sq(X, Y, Z):
    return (SQ['cx'] + SQ['f'] * X / Z, SQ['yh'] + SQ['f'] * (SQ['H'] - Y) / Z)


def _window_quad(kind):
    z0, z1, y0, y1 = WIN_K if kind == 'konrad' else WIN_A
    X = -HOTEL_X if kind == 'konrad' else HOTEL_X
    pts = [sq(X, y1, z0), sq(X, y1, z1), sq(X, y0, z1), sq(X, y0, z0)]
    return [(round(x, 2), round(y, 2)) for (x, y) in pts]


def lit_window(kind):
    """The lit window seen from the station roof (oblique): lamp light, curtain, the man at his radio."""
    q = _window_quad(kind)
    xs = [p[0] for p in q]
    ys = [p[1] for p in q]
    x0, y0 = int(math.floor(min(xs))) - 6, int(math.floor(min(ys))) - 6
    x1, y1 = int(math.ceil(max(xs))) + 6, int(math.ceil(max(ys))) + 6
    w, h = x1 - x0, y1 - y0
    R = C.ramps(L=LAMP, N=NIGHT)
    p = C.Paint(w, h, R, 'litwin_' + kind)
    m = poly([(x - x0, y - y0) for (x, y) in q], w, h)
    yy, xx = grid(h, w)
    cxw = (xx[m].mean() if m.any() else w / 2)
    p.put(m, 'L', 4.6 - np.clip((yy - yy[m].min()) / max(1, h - 12), 0, 1) * 1.6)
    p.put(m & (np.abs(xx - cxw) < 0.6), 'N', 3.0)                            # mullion
    side = (xx < cxw - 2) if kind == 'konrad' else (xx > cxw + 2)
    p.put(m & side & (np.mod(xx, 2) == 0), 'L', 2.6)                            # curtain folds
    lis = None
    try:
        import env_c3p2_cine_figs as F
        if hasattr(F, 'window_listener'):
            ys_, xs_ = np.nonzero(m)
            lis = F.window_listener(kind, (int(xs_.max() - xs_.min() + 1), int(ys_.max() - ys_.min() + 1)))
    except Exception:
        lis = None
    if lis is None:
        # the man at the table: head and shoulders against the light
        hx = cxw + (2 if kind == 'konrad' else -2)
        by = yy[m].max() if m.any() else h
        head = ell(hx, by - 5.5, 1.6, 1.9, w, h)
        sh = poly([(hx - 3.2, by + 1), (hx - 2.4, by - 3.2), (hx + 2.4, by - 3.2), (hx + 3.2, by + 1)], w, h)
        p.put((head | sh) & m, 'N', 1.0)
    p.resolve(band=2.0)
    out = p.L.c
    if lis is not None:
        ys_, xs_ = np.nonzero(m)
        sub = np.zeros_like(out)
        Q.blit(sub, lis, int(xs_.min()), int(ys_.min()))
        sel = (sub[..., 3] > 0) & m
        out[sel] = sub[sel]
    L['win_' + kind] = [x0, y0]
    return out


def door_open(kind):
    """r6: the hotel door opened, warm light falling onto the snow (straight RGBA, drawn over the bg)."""
    X, Z = DOOR_K if kind == 'konrad' else DOOR_A
    sgn = -1 if kind == 'konrad' else 1
    w_m = 1.0 if kind == 'konrad' else 1.3
    pts = [sq(X, 2.7, Z - w_m), sq(X, 2.7, Z + w_m), sq(X, 0.0, Z + w_m), sq(X, 0.0, Z - w_m)]
    a = np.zeros((VH, VW, 3), np.float32)
    m = poly(pts)
    yy, xx = grid()
    a[m] = np.array([236, 190, 120], np.float32)
    a[m & (yy > min(p[1] for p in pts) + 0.6 * (max(p[1] for p in pts) - min(p[1] for p in pts)))] = \
        np.array([250, 214, 150], np.float32)
    # light spill on the snow: a wedge from the door toward the square centre
    spill = [sq(X, 0, Z - w_m), sq(X, 0, Z + w_m), sq(X - sgn * 7.0, 0, Z + w_m * 2.6), sq(X - sgn * 7.0, 0, Z - w_m * 2.2)]
    sm = poly(spill) & ~m
    d = np.clip(np.abs(xx - pts[0][0]) / 60.0, 0, 1)
    g = (1 - d) ** 1.5
    th = pg.bayer(VW, VH, 1, 2)
    sel = sm & (g > th * 0.9)
    a[sel] = np.array([96, 72, 46], np.float32) + g[sel, None] * np.array([70, 50, 24], np.float32)
    out = np.zeros((VH, VW, 4), np.uint8)
    on = m | sel
    pal = LAMP + ['#5A4630', '#7A5E40', '#9A7650', '#6B4A2C']
    q = Q.requant(a, pal, spread=10.0)
    out[on] = q[on]
    ys, xs = np.nonzero(on)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    L['door_' + kind] = [int(x0), int(y0)]
    return out[y0:y1, x0:x1]


def walker(kind):
    """r6: a tiny man walking away from the camera, 4 frames (back view), ~13/11 px."""
    hgt = 15 if kind == 'konrad' else 13
    fw, fh = 11, hgt + 3
    frames = []
    for i in range(4):
        R = C.ramps(N=NIGHT, K=K_COAT, A=A_COAT, F=A_FUR, H=['#0E0D12', '#1F1A22', '#2D2D36'], S=SNOW,
                    L=LAMP)
        p = C.Paint(fw, fh, R, 'walker')
        cx = fw / 2
        ph = i / 4 * 2 * math.pi
        step = math.sin(ph)
        bob = 0 if i % 2 == 0 else -1
        top = 2 + bob
        coat = 'K' if kind == 'konrad' else 'A'
        legy = top + int(hgt * 0.62)
        for s_, k in ((-1, step), (1, -step)):
            lx = cx + s_ * 1.0 + k * 0.8
            p.put(p.box(int(lx) - (1 if s_ < 0 else 0), legy, int(lx) + (1 if s_ > 0 else 0) + 1,
                        min(fh, top + hgt + int(max(0, -k) * 0)) ), 'N', 1.0)
        body = poly([(cx - 2.6, top + 4), (cx + 2.6, top + 4), (cx + 3.1, legy + 1), (cx - 3.1, legy + 1)], fw, fh)
        p.put(body, coat, 2.0)
        p.put(body & (p.xx > cx + 1), coat, 3.2)                                   # lamp-lit side
        if kind == 'konrad':
            p.put(ell(cx, top + 2.6, 1.4, 1.7, fw, fh), 'N', 2.0)
            p.put(p.box(int(cx) - 2, top + 1, int(cx) + 3, top + 2), 'H', 1.0)    # hat brim
            p.put(p.box(int(cx) - 1, top, int(cx) + 2, top + 1), 'H', 1.6)
        else:
            p.put(ell(cx, top + 2.4, 2.0, 2.0, fw, fh), 'F', 2.4)                  # ushanka
            p.put(p.box(int(cx) - 2, top + 3, int(cx) + 3, top + 5), 'F', 1.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


def _record_square():
    L['sq'] = dict(SQ)
    L['door_konrad_xz'] = list(DOOR_K)
    L['door_alexei_xz'] = list(DOOR_A)
    # round 11: the whole walk from each door to the dark east wing (r6 shows its start, then dissolves to the two
    # tracks converging on the wing): path = [x, y, figure height, metres walked] every 0.5 m; prints = [x, y,
    # metres, size px] every 0.37 m, alternating left/right of the line; trail = [x, y, half width px, metres] of
    # the trodden furrow every metre; the two men end a little apart at the wing's dark door
    ends = {'konrad': (EAST_WING[0] - 1.4, EAST_WING[1] - 2.0), 'alexei': (EAST_WING[0] + 1.2, EAST_WING[1] - 2.6)}
    for kind, (X0, Z0) in (('konrad', DOOR_K), ('alexei', DOOR_A)):
        X0 = X0 + (1.4 if X0 < 0 else -1.4)          # the first step out of the door, off the pavement edge
        ex, ez = ends[kind]
        # a gentle curve: out from the facade first, then straight for the wing
        def at(u):
            bx = X0 + (ex - X0) * u + (1 if X0 < 0 else -1) * 11.0 * math.sin(math.pi * u) * (1 - u) ** 2
            bz = Z0 + (ez - Z0) * u
            return bx, bz
        pts = [at(i / 400.0) for i in range(401)]
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
        D = acc[-1]

        def by_d(d):
            j = int(np.searchsorted(acc, d))
            j = min(max(j, 1), len(acc) - 1)
            f = (d - acc[j - 1]) / max(1e-6, acc[j] - acc[j - 1])
            return (pts[j - 1][0] + (pts[j][0] - pts[j - 1][0]) * f, pts[j - 1][1] + (pts[j][1] - pts[j - 1][1]) * f,
                    pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1])
        path, prints, trail = [], [], []
        d = 0.0
        while d <= D:
            X, Z, _, _ = by_d(d)
            x, y = sq(X, 0.0, Z)
            path.append([round(x, 2), round(y, 2), round(SQ['f'] * 1.8 / Z, 2), round(d, 2)])
            d += 0.5
        k = 0
        d = 0.2
        while d < D - 0.3:
            X, Z, tx, tz = by_d(d)
            n = math.hypot(tx, tz) or 1.0
            side = 0.14 if k % 2 == 0 else -0.14
            Xs, Zs = X - tz / n * side, Z + tx / n * side
            x, y = sq(Xs, 0.0, Zs)
            prints.append([round(x, 2), round(y, 2), round(d, 2), round(max(1.0, SQ['f'] * 0.22 / Zs), 2)])
            d += 0.37
            k += 1
        d = 0.0
        while d <= D:
            X, Z, _, _ = by_d(d)
            x, y = sq(X, 0.0, Z)
            trail.append([round(x, 2), round(y, 2), round(max(0.6, SQ['f'] * 0.3 / Z), 2), round(d, 2)])
            d += 1.0
        L['path_' + kind] = path
        L['prints_' + kind] = prints
        L['trail_' + kind] = trail
        L['walk_' + kind] = round(D, 2)


def rig_walker(kind, hgt, n=6, yaw=None):
    """r6: Konrad / Alexei walking away from the camera toward the wing (the figures stream's rig, called here at
    the sizes this shot needs): n frames, hgt px tall, lit by the lamps from the side and the door behind."""
    import env_c3p2_cine_people as PP
    B = PP.B
    ch = B.KONRAD if kind == 'konrad' else B.ALEXEI
    yaw = (155.0 if kind == 'konrad' else -155.0) if yaw is None else yaw
    fw = max(9, int(round(hgt * 0.7))) | 1
    fh = hgt + 4
    frames = []
    for i in range(n):
        pose = B.walk(i / float(n), stride=1.05, arm_swing=0.85, lean=5.0)
        frames.append(PP.person(ch, pose, (fw, fh), (fw / 2.0, fh - 2.0), yaw, 16.0, (hgt + 0.5) / PP.U,
                                light='lamp', look='yard', eyes=False, key=('r6walk', kind, hgt, n, i, yaw), ss=4))
    return Q.sheet(frames)


# ======================================================================================= the rooms (r2/r3)
WIN = (168, 52, 492, 214)            # window opening (x0, y0, x1, y1) - identical in both rooms
MULLION = 330
RADIO_AT = (278, 134)                # top-left of the radio sprite in both rooms
DIAL = (330, 182)                    # dial centre (absolute) - the match cut
DIAL_R = 24
TABLE_Y = 236                        # front edge of the tabletop


def radio():
    """The Bakelite table radio (shared by both rooms): dial left, cloth grille right, knobs, piano keys."""
    w, h = 172, 104
    R = C.ramps(B=BAKE, C=['#2A1E14', '#4A3826', '#6A5236', '#8C7048', '#A88A5C', '#C2A576', '#E0C894'],
                G=['#1E140E', '#3A2A1C', '#55402A', '#6E5638', '#8A6E48'], K=['#1A1410', '#3A3024', '#6E604A',
                                                                             '#A69878', '#D8CCAE', '#F0E8D2'],
                M=BRASS, N=NIGHT)
    p = C.Paint(w, h, R, 'radio')
    yy, xx = p.yy, p.xx
    arch = 6.0 + 7.0 * ((xx + 0.5 - w / 2) / (w / 2)) ** 2
    body = (yy >= arch) & (yy < h - 2) & (xx >= 0) & (xx < w)
    body &= ~((xx < 3) & (yy > h - 6)) & ~((xx > w - 4) & (yy > h - 6))
    lit = np.clip(1.0 - (xx / w) * 0.6, 0, 1) + np.clip((26 - yy) / 26, 0, 1) * 0.8
    p.put(body, 'B', 2.6 + lit * 1.9)
    p.put(body & (yy < arch + 2), 'B', 6.2 - (xx / w) * 1.6)                     # polished top edge
    p.put(body & (xx < 2), 'B', 5.0)
    p.put(body & (yy >= h - 5), 'B', 1.2)                                         # foot
    # dial bezel + glass (warm backlight); the needle is drawn at runtime
    dx, dy = DIAL[0] - RADIO_AT[0], DIAL[1] - RADIO_AT[1]
    r = np.hypot(xx + 0.5 - dx, yy + 0.5 - dy)
    p.put(body & (r < DIAL_R + 3), 'M', 3.4 - (yy - dy) / DIAL_R * 1.2)
    p.put(body & (r < DIAL_R + 1), 'M', 1.4)
    face = body & (r < DIAL_R)
    p.put(face, 'C', 4.6 - r[face] / DIAL_R * 1.8)
    ang = (np.degrees(np.arctan2(xx + 0.5 - dx, -(yy + 0.5 - dy))) + 360) % 360
    ring = face & (r > DIAL_R - 6) & (r < DIAL_R - 5)
    p.put(ring & ((ang < 140) | (ang > 220)), 'G', 1.2)
    for k in range(-13, 14):
        a = (k * 10) % 360
        tick = face & (r > DIAL_R - 6 - (2 if k % 3 == 0 else 0)) & (r < DIAL_R - 2) & \
            (np.abs(((ang - a + 180) % 360) - 180) < (2.4 if k % 3 == 0 else 1.2))
        p.put(tick, 'G', 0.8)
    # the two Veltrava services: a red mark (I, russisch) and a blue one (II, deutsch)
    for a, col in ((300.0, 'red'), (40.0, 'blue')):
        mk = face & (r > DIAL_R - 4.5) & (r < DIAL_R - 1.5) & (np.abs(((ang - a + 180) % 360) - 180) < 5.5)
        if col == 'red':
            p.put(mk, 'B', 7.0)
        else:
            p.put(mk, 'N', 6.0)
    p.put(face & (r < 3.2), 'M', 2.0)                                              # needle hub
    # the maker's name on a small plate under the dial (the needle stays the only thing moving on the glass)
    tm = K.vtext('KOMET', 's', 1)
    sm = K.place(tm, w, h, int(dx - tm.shape[1] / 2), int(dy + DIAL_R + 4))
    p.put(body & (np.abs(xx - dx) < 12) & (yy >= dy + DIAL_R + 4) & (yy < dy + DIAL_R + 11), 'M', 2.6)
    p.put(sm & body, 'B', 1.0)
    # cloth grille behind a Bakelite fret
    gx0, gx1, gy0, gy1 = 92, 162, 18, 80
    grille = body & (xx >= gx0) & (xx < gx1) & (yy >= gy0) & (yy < gy1)
    weave = ((xx.astype(int) + yy.astype(int)) % 2 == 0)
    p.put(grille, 'G', 2.0 + weave[grille] * 0.6 + (1 - (xx[grille] - gx0) / (gx1 - gx0)) * 0.8)
    for bx in range(gx0 + 6, gx1 - 2, 9):
        bar = grille & (xx >= bx) & (xx < bx + 3)
        p.put(bar, 'B', 3.6 - (bx - gx0) / 70.0)
        p.put(bar & (xx == bx), 'B', 5.4)
    p.put(body & (xx >= gx0 - 2) & (xx < gx1 + 2) & ((yy == gy0 - 1) | (yy == gy1)), 'B', 5.2)
    # magic eye above the grille (green; drawn brighter at runtime), maker's badge
    p.put(body & (np.hypot(xx + 0.5 - 127, yy + 0.5 - 11) < 3.6), 'M', 1.5)
    p.put(body & (np.hypot(xx + 0.5 - 127, yy + 0.5 - 11) < 2.4), 'N', 0.0)
    p.put(body & (xx >= 112) & (xx < 142) & (yy >= 84) & (yy < 86), 'M', 3.0)
    # knobs (volume, tuning) and four ivory piano keys
    for kx in (22, 70):
        kn = body & (np.hypot(xx + 0.5 - kx, yy + 0.5 - 90) < 6.5)
        p.put(kn, 'B', 1.6 + np.clip((92 - yy[kn]) / 6, 0, 1) * 4.0)
        p.put(kn & (np.hypot(xx + 0.5 - kx + 1.5, yy + 0.5 - 87.5) < 1.5), 'B', 7.0)
    for i in range(4):
        kx0 = 98 + i * 15
        key = body & (xx >= kx0) & (xx < kx0 + 12) & (yy >= 88) & (yy < 96)
        p.put(key, 'K', 4.2 - (i * 0.2))
        p.put(key & (yy >= 94), 'K', 2.0)
    p.resolve(band=2.0)
    out = p.L.c
    L['radio'] = list(RADIO_AT)
    L['dial'] = list(DIAL)
    L['dial_r'] = DIAL_R
    L['knob_tune'] = [RADIO_AT[0] + 70, RADIO_AT[1] + 90]
    L['magic_eye'] = [RADIO_AT[0] + 127, RADIO_AT[1] + 11]
    return out


def dial_glow():
    """Additive amber light of the dial on the radio front, the table and the near wall."""
    return Q.glow_sprite(VW, VH, [(DIAL[0], DIAL[1], 30, 30, (70, 48, 20), 1.4),
                                  (DIAL[0], TABLE_Y - 4, 90, 10, (44, 28, 10), 1.6),
                                  (DIAL[0], DIAL[1], 130, 90, (18, 12, 5), 1.2)], 6.0)


def lamp_glow():
    return Q.glow_sprite(VW, VH, [(206, 158, 70, 50, (60, 42, 18), 1.5), (206, 145, 22, 14, (80, 60, 30), 1.2),
                                  (300, TABLE_Y - 4, 170, 12, (40, 28, 12), 1.5)], 6.0)


def magic_eye():
    """3 frames of the green tuning indicator: open (searching), half, closed (tuned)."""
    fw, fh = 7, 7
    out = np.zeros((fh, fw * 3, 4), np.uint8)
    yy, xx = grid(fh, fw)
    r = np.hypot(xx + 0.5 - 3.5, yy + 0.5 - 3.5)
    ang = np.degrees(np.arctan2(xx + 0.5 - 3.5, -(yy + 0.5 - 3.5)))
    for i, gap in enumerate((70.0, 36.0, 6.0)):
        a = np.zeros((fh, fw, 3), np.float32)
        disc = r < 2.6
        a[disc] = np.array([60, 190, 120], np.float32)
        a[disc & (np.abs(ang) < gap)] = np.array([14, 40, 26], np.float32)
        a[r < 0.9] = np.array([20, 50, 30], np.float32)
        out[:, i * fw:(i + 1) * fw] = K.soft_quant(a, 6.0)
    return out


def steam_tea():
    """6 frames of steam rising from the tea glass (light, thin)."""
    fw, fh = 18, 34
    out = np.zeros((fh, fw * 6, 4), np.uint8)
    yy, xx = grid(fh, fw)
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        cxs = fw / 2 + np.sin(ph + (fh - yy) * 0.22) * (1 + (fh - yy) * 0.12)
        d = np.abs(xx + 0.5 - cxs)
        dens = np.clip(1 - d / 1.6, 0, 1) * np.clip((yy - 2) / 10, 0, 1) * np.clip((fh - yy) / 6, 0, 1)
        m = dens > pg.bayer(fw, fh, i, i * 2) * 0.9 + 0.08
        fr = np.zeros((fh, fw, 4), np.uint8)
        fr[m, :3] = hexrgb('#7D8796').astype(np.uint8)
        fr[m & (dens > 0.75), :3] = hexrgb('#A1AAB7').astype(np.uint8)
        fr[m, 3] = 255
        out[:, i * fw:(i + 1) * fw] = fr
    L['steam_tea'] = [467, TABLE_Y - 66]
    return out


def arm_alexei():
    """Alexei's right arm reaching for the tuning knob: 4 frames (0 = out of the shot).  The arm comes from
    behind his body (the figure is drawn over its root); knit sleeve lit by the dial from above-right."""
    kx, ky = L.get('knob_tune', [348, 224])
    x0, y0, w, h = 200, 168, 160, 72
    R = C.ramps(K=['#08090B', '#121418', '#1D2025', '#2A2E34', '#3A3E44', '#5A5450', '#7E6A56'],
                S=SKIN_A, L=LAMP)
    frames = []
    for i in range(4):
        p = C.Paint(w, h, R, 'arm_a', ox=x0, oy=y0)
        if i > 0:
            reach = (0.62, 0.96, 1.0)[i - 1]
            sh = (238.0, 190.0)                                   # shoulder, hidden behind the torso
            hx = sh[0] + (kx - 3 - sh[0]) * reach
            hy = sh[1] + (ky - 1 - sh[1]) * reach
            el = (sh[0] + (hx - sh[0]) * 0.42, max(sh[1], hy) + 9.0)
            upper = p.line([sh, el], r=7.0)
            fore = p.line([el, ((el[0] + hx) / 2, (el[1] + hy) / 2 + 1.5), (hx - 7, hy)], r=5.2)
            sleeve = upper | fore
            yy, xx = p.yy, p.xx
            lit = C.edge_light(sleeve, (0.6, -1.0), width=4.0, soft=1)
            p.put(sleeve, 'K', 1.4 + lit[sleeve] * 3.6)
            rib = sleeve & (np.mod(xx * 0.8 + yy * 0.35, 3.0) < 1.0)
            p.put(rib, 'K', 1.0 + lit[rib] * 3.0)
            p.put(sleeve & ~C.shift(sleeve, 0, 1), 'K', 0.4)                      # under side in shadow
            cuff = p.line([(hx - 10, hy), (hx - 6, hy)], r=4.4)
            p.put(cuff & ~sleeve | cuff, 'K', 2.2 + lit[cuff] * 2.0)
            turn = i == 3
            palm = p.ell(hx - 2.0, hy - 0.5, 4.6, 3.6)
            fingers = p.line([(hx - 1, hy - 3), (hx + 4, hy - 3.5 + (1 if turn else 0))], r=1.3) |                 p.line([(hx + 1, hy - 1), (hx + 5, hy + (1 if turn else 0))], r=1.2) |                 p.line([(hx - 1, hy + 2), (hx + 3, hy + 3.5 - (1 if turn else 0))], r=1.1)
            hand = palm | fingers
            hl = C.edge_light(hand, (0.7, -0.8), width=2.5, soft=1)
            p.put(hand, 'S', 1.6 + hl[hand] * 3.2)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    L['arm_alexei'] = [x0, y0]
    return Q.sheet(frames)


SKIN_A = ['#2A1C1C', '#4E302C', '#6E4440', '#8E5C50', '#B07A66', '#CC9A7E']
SKIN_K = ['#2A1C22', '#4E3036', '#6E4448', '#8E5C58', '#B47B68', '#D29A80']


def hand_konrad():
    """Konrad's right hand writing on the notepad: 4 writing frames + 1 stopped (pencil lifted)."""
    x0, y0, w, h = 404, 186, 110, 56
    R = C.ramps(K=K_COAT, S=SKIN_K, Y=['#3A2A10', '#6E5420', '#A8862E', '#D8B84A'], P=PAPER,
                W=['#2A2C32', '#5A5E66', '#9A9EA6', '#D2D4D8'])
    frames = []
    for i in range(5):
        p = C.Paint(w, h, R, 'hand_k', ox=x0, oy=y0)
        stop = i == 4
        tipx = 430 + (i % 4) * 9 if not stop else 452
        tipy = TABLE_Y - 6 - (3 if stop else 0)
        hx, hy = tipx + 12, tipy - 7
        sleeve = p.line([(520, 200), (hx + 22, hy - 4), (hx + 10, hy - 1)], r=6.0)
        p.put(sleeve, 'K', 2.4)
        p.put(sleeve & ~C.shift(sleeve, 0, -2), 'K', 4.4)
        cuff = p.line([(hx + 10, hy - 1), (hx + 6, hy)], r=4.0)
        p.put(cuff, 'W', 2.6)
        hand = p.ell(hx, hy, 6.0, 4.4) | p.line([(hx - 3, hy + 2), (tipx + 3, tipy - 1)], r=1.5)
        p.put(hand, 'S', 2.6)
        p.put(hand & ~C.shift(hand, 0, -1), 'S', 4.6)
        p.put(hand & ~C.shift(hand, 0, 1), 'S', 1.2)
        pencil = p.line([(tipx, tipy), (tipx + 14, tipy - 12)], r=0.9)
        p.put(pencil, 'Y', 2.6)
        p.put(p.line([(tipx, tipy), (tipx + 1.6, tipy - 1.4)], r=0.6), 'W', 0.4)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    L['hand_konrad'] = [x0, y0]
    L['pad_line'] = [428, TABLE_Y - 6, 466]
    return Q.sheet(frames)


# ======================================================================================= r4: doors + note
DOOR_FLOOR = 262                     # the gap line (bottom edge of both doors)


def _split_note(s: str):
    """'Registratur. Hof, Rampe. 0.30 Uhr. – E.' -> ['Registratur. Hof, Rampe.', '0.30 Uhr. – E.']"""
    i = s.find('0.30')
    return [s[:i].strip(), s[i:].strip()] if i > 0 else [s]


# ======================================================================================= r5: Café Korridor
CLOCK = (452, 112)
CLOCK_R = 21


# ======================================================================================= build
def build(w):
    import env_c3p2_cine_square as SQM
    w('radio/square_bg.png', SQM.square_bg())
    w('radio/square_near.png', SQM.square_near())
    w('radio/near_glow.png', SQM.near_glow())
    w('radio/taxi.png', SQM.taxi())
    w('radio/win_konrad.png', lit_window('konrad'))
    w('radio/win_alexei.png', lit_window('alexei'))
    w('radio/square_glow.png', SQM.lit_glow())
    w('radio/door_konrad.png', door_open('konrad'))
    w('radio/door_alexei.png', door_open('alexei'))
    import env_c3p2_cine_figs as F
    # r6 (round 11): the men leaving their doors at a readable size, and small far off at the wing after the
    # dissolve (the figures stream's rig through env_c3p2_cine_people.person)
    w('radio/walker_konrad.png', rig_walker('konrad', 21, 6))
    w('radio/walker_alexei.png', rig_walker('alexei', 20, 6))
    w('radio/walker_far_konrad.png', rig_walker('konrad', 9, 4))
    w('radio/walker_far_alexei.png', rig_walker('alexei', 9, 4))
    w('radio/steam.png', SQM.steam())
    # a late couple crossing the near square in r1 (the figures stream's townspeople), walking right
    ps = getattr(F, 'person_sheet', None)
    if ps:
        w('radio/couple_man.png', ps('guest', 1, 'walk', 24, 90.0, 'lamp', 'yard', 6))
        w('radio/couple_woman.png', ps('woman', 0, 'walk', 23, 90.0, 'lamp', 'yard', 6))
        L['couple'] = {'path': [[150.0, 277.0], [236.0, 279.0]], 'gap': 15.0, 't': [0.0, 4.0], 'fps': 7.0}
    else:
        L['couple'] = {}
    w('radio/radio.png', radio())
    import env_c3p2_cine_rooms as RMS
    w('radio/room_alexei.png', RMS.room('alexei'))
    w('radio/room_konrad.png', RMS.room('konrad'))
    w('radio/chair_alexei.png', RMS.chair('alexei'))
    w('radio/chair_konrad.png', RMS.chair('konrad'))
    w('radio/dial_glow.png', dial_glow())
    w('radio/lamp_glow.png', lamp_glow())
    w('radio/magic_eye.png', magic_eye())
    w('radio/steam_tea.png', steam_tea())
    arm_fn = getattr(F, 'arm_alexei', None)
    w('radio/arm_alexei.png', arm_fn() if arm_fn else arm_alexei())
    if arm_fn:
        L['arm_alexei'] = list(getattr(F, 'ARM_A_AT', (200, 168)))
    hand_fn = getattr(F, 'hand_konrad', None)
    w('radio/hand_konrad.png', hand_fn() if hand_fn else hand_konrad())
    if hand_fn:
        L['hand_konrad'] = list(getattr(F, 'HAND_K_AT', (404, 186)))
    # the figures stream's writing hand follows its own line on the part of the pad the radio does not cover
    L['pad_line'] = list(getattr(F, 'PAD_LINE', (428, TABLE_Y - 6, 466)))
    import env_c3p2_cine_cafe as CF
    w('radio/doors.png', CF.doors())
    w('radio/keyfob.png', CF.keyfob())
    w('radio/note_fold.png', CF.note_fold())
    w('radio/note_close.png', CF.note_close())
    w('radio/cafe.png', CF.cafe())
    w('radio/cafe_fg.png', CF.cafe_fg())
    w('radio/cafe_glow.png', CF.cafe_glow())
    w('radio/cat.png', CF.cat())
    w('radio/fig_alexei.png', F.room_alexei())
    w('radio/fig_konrad.png', F.room_konrad())
    L['fig_alexei'] = list(F.ROOM_A_AT)
    L['fig_konrad'] = list(F.ROOM_K_AT)
