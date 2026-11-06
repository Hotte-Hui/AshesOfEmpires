"""env_c4_tunnels_siding -- painters for Dienststollen 3 and the Umsetzgleis (scene C) of L_C4_Tunnels.

Functions take the Room of env_c4_tunnels_room.py and paint into its TLayer: the earth section with the freight
yard above (the train of the level script's event rolls along it), the 1941 concrete tube (cage lamps, cables,
the heating pipe, the telephone niche, the lever frame and point W2, the sealed side gallery), the vaulted siding
hall (the siding office with the card box "C-17/45 - принять", the paint stand, the fire shield, the plate heap,
the kit pile, the exit portal) and wagon 24 318 with its four paint layers.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_tunnels_kit as K
import env_c4_tunnels_layout as L

W, H = L.WORLD_W, L.WORLD_H
FL = L.FLOOR


# =========================================================================== earth section + yard surface
def earth(room, x0, x1, bottom):
    """Soil in section between the freight yard (top) and a vault (bottom = its extrados): wavy strata of clay,
    sand and gravel, a few stones, the frost line, then ballast, sleepers, the rail and the snow of the yard."""
    lay = room.lay
    w = x1 - x0
    hh = bottom
    ys = np.arange(hh, dtype=np.float32)[:, None]
    n1 = K.noise(w, hh, 34, 501 + x0) * 1.0
    n2 = K.noise(w, hh, 5, 502 + x0, octaves=2) * 0.28
    band = np.floor((ys + n1 * 9.0) / 11.0).astype(int)
    tones = np.array([1.5, 2.0, 1.2, 1.8, 2.2, 1.4, 1.9, 1.6, 1.1, 1.7], np.float32)
    t = tones[band % len(tones)] + n2 - np.clip((ys - (hh - 12)) / 12.0, 0, 1) * 0.6
    lay.put(np.ones((hh, w), bool), x0, 0, 'E', t, flat=False, hgt=0.2)
    rng = np.random.default_rng(503 + x0)
    gravel = (band % len(tones)) == 4
    gv = gravel & (rng.random((hh, w)) < 0.12)
    lay.put(gv, x0, 0, 'C', 2.6, hgt=0.4)
    for _ in range(int(w * hh / 1500)):                                      # stones
        sx, sy = int(rng.integers(x0 + 3, x1 - 4)), int(rng.integers(20, max(21, hh - 5)))
        rx, ry = int(rng.integers(1, 4)), int(rng.integers(1, 3))
        m, mx, my = lay.ellipse_mask(sx, sy, rx, ry)
        lay.put(m, mx, my, 'C', 1.8 + rng.random() * 0.8, hgt=0.5)
        lay.px(sx - rx + 1, sy - ry + 1, 'C', 3.2, hgt=0.6)
        lay.hline(sx - rx + 1, sy + ry, 2 * rx - 1, 'N', 1.4)
    # frozen top soil, ballast, sleepers, rail, snow, night air above
    lay.rect(x0, 0, w, 5, 'N', 0.6, hgt=0.0)
    for x in range(x0, x1):
        sn = 5 + int(1.2 * math.sin(x / 13.0) + (x * 7 % 5 == 0))
        lay.rect(x, sn - 1, 1, 9 - sn + 1, 'S', 2.4 + (x % 3 == 0) * 0.8, hgt=0.3)
    for x in range(x0, x1):
        if (x - x0) % 3 == 0:
            lay.rect(x, 9, 2, 6, 'C', 1.8 + ((x * 13) % 7) * 0.2, hgt=0.4)      # ballast stones
    for x in range(x0 - (x0 % 14), x1, 14):                                   # sleepers (in section)
        if x0 <= x < x1 - 8:
            lay.rect(x, 9, 8, 3, 'I', 1.4, hgt=0.6)
    lay.rect(x0, 7, w, 2, 'I', 2.6, hgt=0.9)                                  # rail
    lay.rect(x0, 7, w, 1, 'S', 3.4, hgt=1.0)
    for x in range(x0, x1, 3):                                                # frost line
        lay.px(x + (x * 7 % 3), 16 + (x * 5 % 4), 'S', 1.0, hgt=0.1)


def _f(y, sp, cut, k):
    """Perspective spread of a vault surface between the springing (sp, f = 1) and the section cut (f = 1 + k)."""
    return 1.0 + k * (sp - y) / max(1.0, (sp - cut))


# =========================================================================== tunnel (Dienststollen 3)
def tunnel(room):
    lay = room.lay
    x0, x1 = L.TUNNEL
    w = x1 - x0
    earth(room, x0, x1, L.T_SHELL)
    for (cx_, cy_, r_) in ((1104, 50, 13),):                                    # old culvert in section
        ring = K.disc(2 * r_) & ~K.erode(K.disc(2 * r_), 3)
        lay.put(K.disc(2 * r_), cx_ - r_, cy_ - r_, 'N', 0.6, hgt=-0.3)
        lay.put(ring, cx_ - r_, cy_ - r_, 'C', 2.6, hgt=0.5)
        lay.rect(cx_ - r_ + 4, cy_ + r_ - 6, 2 * r_ - 8, 2, 'S', 1.0)
    for k in range(5):                                                         # buried cable bundle
        lay.put(K.disc(4), 862 + (k % 3) * 4, 66 + (k // 3) * 4, 'N', 1.6, hgt=0.4)
        lay.px(863 + (k % 3) * 4, 67 + (k // 3) * 4, 'I', 3.0)
    # concrete shell in section (the cut ring above the soffit), aggregate speckle, a rebar dot row
    sh0, sh1 = L.T_SHELL, L.T_SOFFIT[0]
    nz = K.noise(w, sh1 - sh0, 3, 511, octaves=1) * 0.5
    lay.put(np.ones((sh1 - sh0, w), bool), x0, sh0, 'C', 3.2 + nz, hgt=0.4, flat=False)
    lay.rect(x0, sh0, w, 1, 'C', 4.4, hgt=0.5)
    lay.rect(x0, sh1 - 1, w, 1, 'C', 1.0, hgt=0.2)
    for x in range(x0 + 4, x1, 9):
        lay.px(x, sh0 + 5, 'I', 1.6)
    # soffit: the vault curving overhead toward the cut, lit from the lamps below at the far springing, dark at
    # the cut; formwork lines along the axis, ring joints receding toward the viewer
    s0, s1 = L.T_SOFFIT
    vp = (x0 + x1) / 2.0
    for y in range(s0, s1):
        k = (y - s0) / (s1 - s0)
        tone = 0.9 + 2.0 * k ** 1.3
        lay.rect(x0, y, w, 1, 'C', tone, hgt=0.15 + 0.5 * k)
    for j in range(1, 9):
        y = int(round(s1 - (s1 - s0) * (1 - (1 - j / 9.0) ** 1.6)))
        lay.rect(x0, y, w, 1, 'C', 0.6 + 1.6 * (y - s0) / (s1 - s0), hgt=0.1)
    rings = list(range(x0 + 40, x1, 104))
    for xr in rings:
        for y in range(s0, s1):
            xx = int(round(vp + (xr - vp) * _f(y, s1, s0, 0.35)))
            if x0 <= xx < x1 - 1:
                lay.px(xx, y, 'C', 0.5, hgt=0.0)
                lay.px(xx + (1 if xr < vp else -1), y, 'C', 2.4 + 1.4 * (y - s0) / (s1 - s0), hgt=0.4)
    # back wall: concrete, formwork planks, whitewash band above, luminous guide stripe (blackout), damp
    wy0 = s1
    hh = FL - wy0
    ys = np.arange(hh, dtype=np.float32)[:, None]
    nz = K.noise(w, hh, 20, 512) * 0.45 + K.noise(w, hh, 3, 513, octaves=1) * 0.18
    base = 3.0 - 0.4 * np.clip(ys / hh, 0, 1)
    lay.put(np.ones((hh, w), bool), x0, wy0, 'C', base + nz, hgt=0.15, flat=False)
    for y in range(wy0 + 4, FL, 7):                                           # formwork plank lines
        lay.rect(x0, y, w, 1, 'C', 2.2, hgt=0.05)
    for x in range(x0 + 30, x1, 96):                                           # plank butt joints
        for y in range(wy0 + 4, FL, 7):
            lay.rect(x + (y * 3) % 40, y, 1, 6, 'C', 2.0)
    wash = np.zeros((hh, w), bool)
    wash[:72, :] = K.noise(w, 72, 14, 514).astype(np.float32).reshape(72, w) > -0.28
    lay.put(wash, x0, wy0, 'W', 3.4, hgt=0.15)
    lay.shade_mask(wash & (K.noise(w, hh, 9, 516) > 0.15), x0, wy0, -0.5)
    sy = 226
    for x in range(x0, x1):                                                    # guide stripe, worn
        if (x // 3) % 7 != 0 and K.noise(1, 1, 1, x)[0, 0] > -0.2:
            lay.rect(x, sy, 1, 2, 'G', 5.4, hgt=0.2)
    damp = np.zeros((hh, w), bool)
    prof = (hh - 30 + 10 * K.noise(w, 1, 24, 517)[0]).astype(int)
    for xx in range(w):
        damp[max(0, prof[xx]):, xx] = True
    lay.shade_mask(damp, x0, wy0, -0.55)
    rng = np.random.default_rng(518)
    for _ in range(14):                                                        # water streaks + efflorescence
        sx = int(rng.integers(x0 + 10, x1 - 10))
        ln = int(rng.integers(20, 70))
        for yy in range(wy0, wy0 + ln):
            lay.px(sx + (yy // 9) % 2, yy, 'C', 1.4, hgt=0.1)
        if rng.random() < 0.6:
            for yy in range(wy0 + ln, wy0 + ln + 8):
                lay.px(sx + int(rng.integers(-2, 3)), yy, 'S', 2.4 + rng.random(), hgt=0.12)
    for xr in rings:                                                           # ring joints of the tube
        lay.rect(xr, s1, 1, FL - s1, 'C', 1.0, hgt=0.0)
        lay.rect(xr + 1, s1, 1, FL - s1, 'C', 3.6, hgt=0.3)
    # cables on short hooks (sagging between them), the heating pipe with lagging and flanges
    for hx in range(x0 + 8, x1 - 20, 52):
        lay.rect(hx, 174, 1, 14, 'I', 3.0, hgt=0.9)
        for cy in (176, 181, 186):
            lay.rect(hx - 1, cy + 2, 3, 1, 'I', 3.4, hgt=0.9)
    for (cy, sag, t) in ((176, 2, 1.4), (181, 3, 1.8), (186, 2, 1.2)):
        for hx in range(x0 + 8, x1 - 60, 52):
            K.sag_line(lay, hx, hx + 52, cy, sag, 'N', t + 0.6, hgt=0.8, thick=2)
            K.sag_line(lay, hx, hx + 52, cy, sag, 'I', t + 1.4, hgt=0.9, thick=1)
    # a new black rubber cable, clamped beside the old cloth-wrapped ones, running on toward the siding
    for x in range(848, x1, 1):
        lay.rect(x, 190, 1, 2, 'N', 1.0, hgt=0.9)
        lay.px(x, 190, 'I', 3.6 if x % 2 else 3.0, hgt=1.0)
    for cx_ in range(856, x1, 26):
        lay.rect(cx_, 189, 2, 4, 'S', 2.6, hgt=1.0)                                # fresh clamps
    K.cyl(lay, x0, 198, w, 6, 'I', 2.6, hgt=1.0)
    for (la, lb) in ((760, 840), (930, 990)):
        for x in range(la, lb):
            for y in range(197, 205):
                lay.px(x, y, 'P', 2.6 + ((x + y * 2) % 4 == 0) * 0.5 - (y == 204) * 0.8, hgt=1.0)
    for fx_ in range(x0 + 60, x1, 120):
        lay.rect(fx_, 196, 3, 10, 'I', 3.4, hgt=1.0)
        lay.px(fx_ + 1, 195, 'I', 4.6, hgt=1.0)
    ff = L.T_FLANGE
    lay.rect(ff, 196, 3, 10, 'I', 3.4, hgt=1.0)
    for yy in range(206, 250):                                                 # rust streak below the leak
        lay.px(ff + 1 + (yy // 11) % 2, yy, 'K', 2.4, hgt=0.15)
    # cage lamps (1941): bracket, globe in a wire cage
    for (lx, lit) in L.T_LAMPS:
        ly = L.T_LAMP_Y
        lay.rect(lx - 1, ly - 10, 2, 8, 'I', 2.4, hgt=0.9)
        lay.rect(lx - 4, ly - 3, 8, 2, 'I', 3.0, hgt=1.0)
        g = K.disc(7)
        if lit:
            lay.put(g, lx - 3, ly - 1, 'L', 4.4, emis=True)
            lay.put(K.disc(3), lx - 1, ly + 1, 'L', 5.4, emis=True)
        else:
            lay.put(g, lx - 3, ly - 1, 'S', 1.0, hgt=0.9)
            lay.px(lx - 1, ly + 1, 'S', 3.2, hgt=1.0)
        for cxx in (lx - 3, lx, lx + 3):                                       # cage wires
            lay.rect(cxx, ly - 1, 1, 7, 'I', 1.6, hgt=1.0)
        lay.rect(lx - 3, ly + 2, 7, 1, 'I', 1.6, hgt=1.0)
        if lit:
            e = 0.95 if lx != 1142 else 0.85
            room.light('cage_%d' % lx, (lx, ly + 3), 'warm', e, 130, 12, pool=0.3, pool_depth=34, pool_w=12,
                       pool_spread=0.5)
    # arrows "К укрытию" (to the shelter: the cellar), distance plates
    for ax in (836, 966):
        K.worn_text(lay, '← К УКРЫТИЮ', ax, 212, 'P', 4.6, wear=0.1, seed=ax, hgt=0.2)
    for (px_, d) in ((826, '50'), (1066, '100')):
        lay.rect(px_, 150, 16, 14, 'P', 4.2, hgt=0.5)
        lay.rect(px_, 150, 16, 1, 'I', 2.0, hgt=0.5)
        K.text(lay, 'Т-3', px_ + 8, 152, 'I', 1.2, center=True, hgt=0.6)
        K.text(lay, d, px_ + 8, 158, 'I', 1.2, center=True, hgt=0.6)
    # an electrical cabinet (warning bolt), a first-aid box, a fire extinguisher by the airlock
    K.bevel(lay, 900, 232, 18, 26, 'I', 2.6, hi=3.8, lo=1.2, hgt=0.8)
    for (x, y) in ((910, 237), (909, 238), (908, 239), (910, 240), (909, 241), (908, 242)):
        lay.px(x, y, 'L', 4.4, hgt=0.9)
    lay.rect(902, 254, 14, 1, 'N', 1.4)
    lay.rect(958, 234, 14, 12, 'P', 5.0, hgt=0.8)
    lay.rect(958, 234, 14, 1, 'P', 6.0, hgt=0.85)
    lay.rect(964, 236, 2, 8, 'R', 2.6, hgt=0.9)
    lay.rect(961, 239, 8, 2, 'R', 2.6, hgt=0.9)
    lay.rect(748, 262, 6, 18, 'R', 2.2, hgt=0.9)
    lay.rect(748, 262, 2, 18, 'R', 3.4, hgt=1.0)
    lay.rect(749, 258, 3, 4, 'I', 2.6, hgt=1.0)
    lay.rect(746, 280, 10, 8, 'I', 2.4, hgt=0.7)
    lay.rect(746, 280, 10, 1, 'L', 2.6, hgt=0.75)
    # field telephone niche
    n0, n1 = L.T_NICHE
    lay.rect(n0, 222, n1 - n0, 50, 'C', 1.2, hgt=-0.4)
    lay.rect(n0, 222, n1 - n0, 2, 'C', 0.8, hgt=-0.5)
    lay.rect(n0, 222, 2, 50, 'C', 0.9, hgt=-0.5)
    lay.rect(n1 - 2, 222, 2, 50, 'C', 2.6, hgt=-0.3)
    lay.rect(n0, 271, n1 - n0, 2, 'C', 3.6, hgt=0.3)                          # sill
    bx = (n0 + n1) // 2 - 9
    lay.rect(bx, 236, 18, 26, 'D', 3.0, hgt=0.6)                              # wooden phone box
    lay.rect(bx, 236, 18, 1, 'D', 4.2, hgt=0.7)
    lay.rect(bx + 2, 239, 14, 12, 'D', 2.2, hgt=0.5)                          # front panel
    for bxx in (bx + 3, bx + 11):                                              # bells on top
        lay.rect(bxx, 233, 4, 3, 'L', 3.4, hgt=0.9)
        lay.px(bxx + 1, 233, 'L', 4.8, hgt=1.0)
    lay.put(K.disc(5), bx + 7, 242, 'N', 1.2, hgt=0.8)                         # mouthpiece
    lay.px(bx + 9, 243, 'I', 3.4, hgt=0.9)
    lay.rect(bx + 1, 254, 16, 2, 'D', 4.0, hgt=0.8)                            # writing ledge
    lay.rect(bx + 18, 248, 3, 2, 'I', 3.0, hgt=0.9)                            # crank
    lay.rect(bx + 20, 250, 2, 5, 'I', 2.6, hgt=0.9)
    lay.rect(bx - 4, 244, 3, 12, 'N', 1.8, hgt=0.9)                            # handset on its hook
    lay.line(bx - 3, 256, bx + 2, 262, 'N', 1.6)                               # cord
    room.plate(n0 + 1, 212, n1 - n0 - 2, 8, ['ТЕЛЕФОН'], ramp='P', tone=4.6, ink=('I', 1.0), border=('R', 2.0))
    # lever frame (mini-game spot) with the cast plate "НКПС 1941" (insignia site)
    lf0, lf1 = L.T_LEVER
    lay.rect(lf0, 270, lf1 - lf0, 18, 'I', 2.2, hgt=0.8)                      # cast frame
    lay.rect(lf0, 270, lf1 - lf0, 1, 'I', 3.8, hgt=0.9)
    for k in range(lf0 + 3, lf1 - 3, 6):
        lay.rect(k, 273, 3, 12, 'I', 1.4, hgt=0.6)
    # the track diagram board above the frame: yard, W1-W4, the siding
    db0, db1 = lf0 + 6, lf1 - 6
    lay.rect(db0, 212, db1 - db0, 20, 'D', 2.2, hgt=0.6)
    lay.rect(db0 + 1, 213, db1 - db0 - 2, 18, 'P', 3.8, hgt=0.65)
    lay.hline(db0 + 3, 224, db1 - db0 - 6, 'I', 1.0, hgt=0.7)
    for k, wx_ in enumerate(range(db0 + 10, db1 - 6, 12)):
        lay.line(wx_, 224, wx_ + 6, 219, 'I', 1.0)
        lay.px(wx_, 222, 'R', 2.6, hgt=0.75)
    lay.hline(db0 + 16, 219, db1 - db0 - 20, 'I', 1.0, hgt=0.7)
    cols = [('N', 2.2), ('R', 2.6), ('N', 2.2), ('S', 1.4), ('R', 2.6), ('N', 2.2), ('S', 1.4), ('R', 2.6)]
    for i, (ramp, tone) in enumerate(cols):                                   # points black, signals red, locks blue-grey
        lxx = lf0 + 5 + i * 7
        tilt = -3 if i in (1, 4, 6) else 3
        for (x, y) in K.bres(lxx, 271, lxx + tilt, 236):
            lay.rect(x, y, 2, 1, 'I', 3.0, hgt=1.0)
        lay.rect(lxx + tilt - 1, 232, 4, 6, ramp, tone + 0.8, hgt=1.0)          # lever head
        lay.px(lxx + tilt, 232, ramp, tone + 2.0, hgt=1.0)
        lay.rect(lxx - 1, 262, 4, 4, 'P', 4.2, hgt=0.9)                         # number plate
        lay.px(lxx, 263, 'I', 1.0)
    emb = 'hs5' if room.hist else 'gw5'
    import env_karsk_emblems as KE
    lay.rect(lf1 - 30, 276, 26, 9, 'L', 2.4, hgt=0.9)                          # cast brass plate
    lay.put(KE.mask(emb), lf1 - 29, 278, 'L', 4.4, hgt=1.0, flat=True, crisp=True)
    K.text(lay, '1941', lf1 - 13, 278, 'L', 4.4, center=True, hgt=1.0)
    # point W2: hand lever with the ball weight and the point lamp, at the back of the track
    p0, p1 = L.T_POINT
    lay.rect(p0, 280, p1 - p0, 8, 'I', 2.0, hgt=0.7)                           # bed plate
    for (x, y) in K.bres(p0 + 4, 282, p1 - 6, 262):
        lay.rect(x, y, 2, 2, 'P', 4.2 if (x // 3) % 2 else 1.2, hgt=1.0)          # lever, white/black
    lay.put(K.disc(7), p1 - 9, 258, 'I', 2.6, hgt=1.0)                          # weight
    lay.px(p1 - 7, 259, 'I', 4.2, hgt=1.0)
    lay.rect(p0 + 2, 254, 7, 7, 'I', 1.8, hgt=0.9)                              # point lamp
    lay.rect(p0 + 3, 256, 2, 3, 'S', 3.2, emis=True)
    lay.rect(p0 + 6, 256, 2, 3, 'L', 3.6, emis=True)
    lay.rect(p0 + 5, 261, 1, 20, 'I', 2.2, hgt=0.8)
    room.plate(p0 + 10, 246, 20, 8, ['СТР 2'], ramp='P', tone=4.6, ink=('I', 1.0), border=('I', 1.6))
    # the sealed side gallery the branch of W2 runs into
    g0, g1 = L.T_BRANCH
    top = 214
    for x in range(g0, g1):
        c = (x + 0.5 - (g0 + g1) / 2) / ((g1 - g0) / 2)
        ay = int(round(top + 14 * (1 - math.sqrt(max(0.0, 1 - c * c)))))
        lay.rect(x, ay, 1, FL - ay, 'C', 1.0, hgt=-0.3)
        lay.px(x, ay, 'C', 3.8, hgt=0.4)
    room.planks_v(g0 + 6, g1 - 6, top + 10, FL, 'D', 2.0, width=7, seed=531, hgt=0.5)
    for yy in (top + 22, top + 52):
        lay.rect(g0 + 6, yy, g1 - g0 - 12, 3, 'D', 2.8, hgt=0.7)
    K.worn_text(lay, 'ЗАКРЫТО', (g0 + g1) / 2, top + 36, 'P', 4.2, wear=0.25, seed=532, center=True, hgt=0.6)
    # at the tunnel mouth: rough bench boards taken out of a wagon, a small house scratched into the top one
    bb0, bb1 = L.BENCH_BOARDS
    for k in range(4):
        y = FL - 3 - k * 3
        lay.rect(bb0 + (k % 2) * 2, y, bb1 - bb0 - 4 - (k % 2) * 3, 3, 'D', 4.4 - (k % 2) * 0.6, hgt=0.6 + k * 0.05)
        lay.rect(bb0 + (k % 2) * 2, y + 2, bb1 - bb0 - 6, 1, 'D', 2.8, hgt=0.5)
    hx, hy = bb0 + 16, FL - 15
    for (x, y) in ((0, 3), (1, 2), (2, 1), (3, 0), (4, 1), (5, 2), (6, 3)):
        lay.px(hx + x, hy + y, 'P', 5.6, hgt=0.7)
    lay.px(hx + 1, hy + 4, 'P', 5.2, hgt=0.7)
    lay.px(hx + 5, hy + 4, 'P', 5.2, hgt=0.7)
    lay.px(hx + 3, hy + 4, 'P', 5.0, hgt=0.7)
    # left end: the airlock to the cellar door -- three steps up, warm light from the cellar falling in
    lay.rect(x0, wy0, 22, FL - wy0, 'C', 1.6, hgt=-0.2)
    lay.rect(x0 + 2, 230, 14, FL - 230, 'L', 2.4, emis=True)                    # the doorway (cellar lamp)
    lay.rect(x0 + 4, 232, 10, FL - 232, 'L', 3.2, emis=True)
    for i in range(3):
        lay.rect(x0, FL - 4 - i * 4, 22 - i * 5, 4, 'C', 3.0 + i * 0.3, hgt=0.5)
        lay.rect(x0, FL - 4 - i * 4, 22 - i * 5, 1, 'C', 4.2, hgt=0.6)
    room.light('airlock_warm', (x0 + 10, 250), 'warm', 0.8, 110, 8)
    # right end: the portal into the siding hall
    pr = x1 - 12
    lay.rect(pr, s0 - 6, 18, FL - s0 + 6, 'C', 3.6, hgt=0.7)
    lay.rect(pr, s0 - 6, 1, FL - s0 + 6, 'C', 4.6, hgt=0.75)
    lay.rect(pr + 17, s0 - 6, 1, FL - s0 + 6, 'C', 1.6, hgt=0.4)


# =========================================================================== siding hall (Umsetzgleis)
def siding(room):
    lay = room.lay
    x0, x1 = L.SIDING
    w = x1 - x0
    earth(room, x0, x1, 24)
    # vault section ring + soffit (dark, formwork lines along the axis), transverse ring beams receding
    lay.rect(x0, 24, w, 10, 'C', 3.0, hgt=0.4)
    lay.rect(x0, 24, w, 1, 'C', 4.2, hgt=0.5)
    lay.rect(x0, 33, w, 1, 'C', 1.0, hgt=0.2)
    sp = L.S_SPRING
    cut = 34
    vp = 1580.0
    nz = K.noise(w, sp - cut, 20, 541) * 0.35
    yy = np.arange(sp - cut, dtype=np.float32)[:, None]
    k = yy / (sp - cut)
    tone = 0.8 + 1.9 * k ** 1.4 + nz
    xs = np.arange(w, dtype=np.float32)[None, :] + x0
    soot = np.clip(1 - np.abs(yy - (sp - cut) * 0.55) / 30.0, 0, 1) * np.clip(1 - np.abs(xs - 1650) / 260.0, 0, 1)
    tone = tone - soot * (0.6 + 0.4 * K.noise(w, sp - cut, 12, 542))
    lay.put(np.ones((sp - cut, w), bool), x0, cut, 'C', tone, hgt=0.3, flat=False)
    for j in range(1, 12):
        y = int(round(sp - (sp - cut) * (1 - (1 - j / 12.0) ** 1.5)))
        lay.rect(x0, y, w, 1, 'C', 0.5 + 1.6 * (y - cut) / (sp - cut), hgt=0.1)
    for rx in L.S_RIBS:
        for y in range(cut, sp + 3):
            fy = _f(min(y, sp), sp, cut, 0.45)
            cxr = vp + (rx - vp) * fy
            half = 4.0 * fy
            a_, b_ = int(round(cxr - half)), int(round(cxr + half))
            kk = (y - cut) / (sp - cut)
            for x in range(max(x0, a_), min(x1, b_ + 1)):
                lay.px(x, y, 'C', 2.2 + 1.6 * kk + (0.6 if x == a_ else 0.0), hgt=0.9)
            sw = max(1, int(round(2 * fy - 1)))
            if cxr < vp:
                for x in range(b_ + 1, b_ + 1 + sw):
                    if x0 <= x < x1:
                        lay.px(x, y, 'C', 1.0 + 0.8 * kk, hgt=0.6)
            else:
                for x in range(a_ - sw, a_):
                    if x0 <= x < x1:
                        lay.px(x, y, 'C', 1.0 + 0.8 * kk, hgt=0.6)
        lay.rect(max(x0, rx - 8), sp + 2, 16, 4, 'C', 3.2, hgt=0.8)               # corbel
        lay.rect(max(x0, rx - 8), sp + 2, 16, 1, 'C', 4.2, hgt=0.85)
    # back wall: concrete, formwork lines, soot band, damp, the painted track number
    hh = FL - sp
    ys = np.arange(hh, dtype=np.float32)[:, None]
    nz = K.noise(w, hh, 22, 543) * 0.45 + K.noise(w, hh, 3, 544, octaves=1) * 0.16
    lay.put(np.ones((hh, w), bool), x0, sp, 'C', 3.1 - 0.5 * np.clip(ys / hh, 0, 1) + nz, hgt=0.15, flat=False)
    for y in range(sp + 5, FL, 8):
        lay.rect(x0, y, w, 1, 'C', 2.2, hgt=0.05)
    for x in range(x0 + 14, x1, 112):
        for y in range(sp + 5, FL, 8):
            lay.rect(x + (y * 5) % 50, y, 1, 7, 'C', 2.0)
    sootw = np.clip(1 - ys / 60.0, 0, 1) * (0.6 + 0.4 * K.noise(w, hh, 26, 545))
    lay.tone[sp:FL, x0:x1] -= sootw * 0.8
    damp = np.zeros((hh, w), bool)
    prof = (hh - 26 + 8 * K.noise(w, 1, 30, 546)[0]).astype(int)
    for xx in range(w):
        damp[max(0, prof[xx]):, xx] = True
    lay.shade_mask(damp, x0, sp, -0.5)
    K.worn_text(lay, 'ПУТЬ 1', 1645, 134, 'P', 4.6, font='57', wear=0.14, seed=547, center=True, hgt=0.2)
    # pilasters under the ring beams, water running down from the corbels, repaired patches
    for rx in L.S_RIBS[1:-1]:
        lay.rect(rx - 4, sp + 6, 8, FL - sp - 6, 'C', 3.3, hgt=0.5)
        lay.rect(rx - 4, sp + 6, 1, FL - sp - 6, 'C', 4.2, hgt=0.6)
        lay.rect(rx + 3, sp + 6, 1, FL - sp - 6, 'C', 1.6, hgt=0.3)
        lay.rect(rx + 4, sp + 6, 2, FL - sp - 6, 'C', 2.0, hgt=0.1)
    rng2 = np.random.default_rng(548)
    for rx in L.S_RIBS:
        for k in range(2):
            sx_ = rx + (-9 if k == 0 else 9) + int(rng2.integers(-2, 3))
            ln = int(rng2.integers(30, 90))
            for yy in range(sp + 6, min(FL - 4, sp + 6 + ln)):
                if x0 <= sx_ < x1:
                    lay.px(sx_ + (yy // 13) % 2, yy, 'C', 1.4, hgt=0.1)
    for (px_, py_, pw, ph) in ((1420, 150, 26, 18), (1752, 176, 30, 14), (1310, 140, 18, 12)):
        lay.rect(px_, py_, pw, ph, 'C', 3.7, hgt=0.2)
        lay.rect(px_, py_ + ph - 1, pw, 1, 'C', 2.2, hgt=0.1)
    # conduit, junction box and knife switch near the booth
    lay.rect(x0, 160, w, 2, 'I', 2.2, hgt=0.6)
    lay.rect(x0, 160, w, 1, 'I', 3.4, hgt=0.65)
    lay.rect(1262, 162, 2, 70, 'I', 2.2, hgt=0.6)
    K.bevel(lay, 1254, 220, 18, 22, 'I', 2.4, hi=3.6, lo=1.2, hgt=0.7)
    lay.rect(1258, 226, 10, 2, 'I', 4.2, hgt=0.9)
    lay.rect(1262, 228, 2, 8, 'N', 1.4, hgt=0.9)
    # work lamps (floodlights) on the corbels
    for (wx, wy) in L.WORK_LAMPS:
        lay.rect(wx - 2, wy - 8, 4, 8, 'I', 2.4, hgt=0.9)
        lay.rect(wx - 7, wy, 14, 7, 'I', 2.8, hgt=1.0)
        lay.rect(wx - 6, wy + 6, 12, 2, 'P', 6.0, emis=True)
        lay.rect(wx - 4, wy + 7, 8, 1, 'S', 6.0, emis=True)
        for gx in range(wx - 6, wx + 7, 3):
            lay.px(gx, wy + 7, 'I', 1.6, hgt=1.0)
    room.light('work_left', (L.WORK_LAMPS[0][0], L.WORK_LAMPS[0][1] + 10), 'cold', 1.5, 300, 30,
               cone=(0.35, 1.0, 0.25), pool=0.45, pool_dx=40, pool_depth=44, pool_w=34, pool_spread=0.9)
    room.light('work_right', (L.WORK_LAMPS[1][0], L.WORK_LAMPS[1][1] + 10), 'cold', 1.1, 260, 30,
               cone=(-0.4, 1.0, 0.25), pool=0.35, pool_dx=-36, pool_depth=40, pool_w=28, pool_spread=0.8)
    booth(room)
    painters_corner(room)
    paint_stand(room)
    fire_shield(room)
    plate_heap(room)
    kit_pile(room)
    portal(room)
    brazier(room)


def booth(room):
    lay = room.lay
    a, b = L.BOOTH
    top = 204
    room.planks_v(a, b, top, FL, 'D', 2.2, width=6, seed=551, hgt=0.5)
    lay.rect(a, top, b - a, 2, 'D', 3.4, hgt=0.7)
    for yy in range(top - 10, top):                                           # roof (tar paper), overhang
        k = (yy - (top - 10)) / 10
        lay.rect(a - 4 + int(2 * (1 - k)), yy, b - a + 8 - int(2 * (1 - k)), 1, 'N', 2.2 + k * 0.8, hgt=0.8)
    lay.rect(a - 4, top - 1, b - a + 8, 1, 'I', 2.6, hgt=0.9)
    # stove pipe through the roof with its cap
    K.cyl(lay, b - 16, 166, 4, top - 10 - 166, 'I', 2.4, hgt=1.0, axis='v')
    lay.rect(b - 19, 162, 10, 4, 'I', 2.8, hgt=1.0)
    # door (left) ajar: warm interior
    lay.rect(a + 3, top + 10, 18, FL - top - 10, 'L', 2.6, emis=True)
    room.planks_v(a + 8, a + 22, top + 10, FL, 'D', 2.8, width=5, seed=552, hgt=0.6)
    lay.rect(a + 20, top + 30, 2, 3, 'I', 3.8, hgt=0.9)
    # window with the sash pushed up, the counter, kerosene lamp inside
    w0, w1 = L.BOOTH_WIN
    lay.rect(w0 - 2, 220, w1 - w0 + 4, 40, 'D', 3.6, hgt=0.7)                # frame
    lay.rect(w0, 222, w1 - w0, 16, 'S', 2.4, hgt=0.5)                         # upper pane (raised sash), reflection
    for k in range(4):
        lay.line(w0 + 4 + k * 12, 236, w0 + 10 + k * 12, 223, 'S', 3.6)
    lay.rect(w0, 230, w1 - w0, 1, 'D', 3.0, hgt=0.7)                           # sash bar
    lay.rect(w0, 238, w1 - w0, 18, 'L', 2.0, emis=True)                        # the lit interior
    lay.rect(w0 + 2, 248, w1 - w0 - 4, 8, 'D', 1.6, emis=True)                 # the desk inside
    lay.rect(w0 + 6, 246, 12, 2, 'P', 3.6, emis=True)                          # papers
    lx = (w0 + w1) // 2 - 4
    lay.rect(lx, 238, 1, 3, 'I', 2.0, emis=True)                               # kerosene lamp (flame strip on top)
    lay.rect(lx - 2, 241, 5, 6, 'P', 4.6, emis=True)
    lay.rect(lx - 1, 242, 3, 4, 'L', 5.4, emis=True)
    lay.rect(lx - 3, 247, 7, 2, 'L', 3.0, emis=True)
    cy = L.BOOTH_COUNTER_Y
    lay.rect(w0 - 6, cy, w1 - w0 + 12, 3, 'D', 3.8, hgt=0.8)                   # counter
    lay.rect(w0 - 6, cy, w1 - w0 + 12, 1, 'D', 5.0, hgt=0.9)
    lay.rect(w0 - 4, cy + 3, 2, 6, 'D', 2.4, hgt=0.6)                          # brackets
    lay.rect(w1 + 2, cy + 3, 2, 6, 'D', 2.4, hgt=0.6)
    # the card box "C-17/45 - принять" + the stamp on its pad
    c0, c1 = L.CARD_BOX
    lay.rect(c0, cy - 16, c1 - c0, 16, 'D', 2.8, hgt=0.9)
    lay.rect(c0, cy - 16, c1 - c0, 1, 'D', 4.2, hgt=0.95)
    for k in range(c0 + 2, c1 - 2, 2):                                          # card tops
        lay.rect(k, cy - 18, 1, 2, 'P', 4.6, hgt=0.9)
    lay.rect(c0 + 1, cy - 14, c1 - c0 - 2, 13, 'P', 5.4, hgt=0.95)            # label
    K.text(lay, 'C-17/45', (c0 + c1) / 2, cy - 13, 'I', 0.8, center=True, hgt=1.0)
    K.text(lay, 'ПРИНЯТЬ', (c0 + c1) / 2, cy - 7, 'R', 2.4, center=True, hgt=1.0)
    s0, s1 = L.STAMP
    lay.rect(s0, cy - 2, s1 - s0, 2, 'R', 1.6, hgt=0.8)                        # ink pad
    lay.rect(s0 + 3, cy - 10, 5, 3, 'D', 3.6, hgt=1.0)                         # stamp knob
    lay.rect(s0 + 4, cy - 7, 3, 3, 'D', 3.0, hgt=1.0)                          # handle
    lay.rect(s0 + 2, cy - 4, 7, 2, 'N', 1.6, hgt=0.9)                          # rubber block
    # sign "ДЕЖУРНЫЙ" + the duty roster on the side
    room.plate(w0 - 2, 208, w1 - w0 + 4, 9, ['ДЕЖУРНЫЙ'], ramp='P', tone=4.6, ink=('I', 1.0), border=('I', 1.6))
    lay.rect(b - 13, 218, 9, 12, 'P', 3.8, hgt=0.5)                             # a timetable on the side
    for r in range(3):
        lay.hline(b - 12, 220 + r * 3, 7, 'I', 2.0, hgt=0.55)
    room.light('kerosene', (lx, 244), 'warm', 1.3, 100, 10, pool=0.4, pool_depth=26, pool_w=16, pool_spread=0.6)


def painters_corner(room):
    lay = room.lay
    a, b = L.PAINTERS
    lay.rect(a, 272, 26, FL - 272, 'D', 3.0, hgt=0.7)                          # a crate as table
    lay.rect(a, 272, 26, 1, 'D', 4.6, hgt=0.75)
    lay.rect(a, 279, 26, 1, 'D', 2.0, hgt=0.6)
    lay.rect(a + 2, 273, 1, FL - 273, 'D', 2.2, hgt=0.6)
    lay.rect(a + 23, 273, 1, FL - 273, 'D', 2.2, hgt=0.6)
    K.worn_text(lay, 'ГВОЗДИ', a + 13, 281, 'N', 1.4, wear=0.3, seed=571, center=True, hgt=0.7)
    pst = b - 4                                                                 # the post with the duty roster
    lay.rect(pst, 190, 4, FL - 190, 'D', 2.8, hgt=0.8)
    lay.rect(pst, 190, 1, FL - 190, 'D', 4.0, hgt=0.85)
    lay.rect(pst - 4, 226, 12, 18, 'P', 4.4, hgt=0.85)
    for r in range(5):
        lay.hline(pst - 3, 229 + r * 3, 10, 'I', 1.8 + (r == 0) * -0.6, hgt=0.9)
    lay.px(pst + 1, 227, 'I', 4.2, hgt=0.95)                                    # the nail
    for gx in (a + 2, a + 7):                                                   # two tea glasses
        lay.rect(gx, 265, 4, 7, 'L', 2.2, hgt=0.75)
        lay.rect(gx, 264, 4, 1, 'S', 3.4, hgt=0.8)
        lay.rect(gx, 269, 4, 3, 'I', 3.0, hgt=0.8)
    lay.rect(a + 12, 268, 14, 4, 'P', 4.4, hgt=0.75)                            # folded newspaper "Гудок"
    lay.rect(a + 12, 268, 14, 1, 'P', 5.2, hgt=0.8)
    K.text(lay, 'ГУДОК', a + 19, 268, 'I', 1.0, center=True, hgt=0.8)


def paint_stand(room):
    lay = room.lay
    a, b = L.PAINT_STAND
    # trestle legs
    for (x0_, x1_) in ((a + 4, a + 10), (b - 10, b - 4)):
        lay.line(x0_, FL, x1_, 204, 'D', 2.4)
        lay.line(x0_ + 1, FL, x1_ + 1, 204, 'D', 3.2)
    bx0, bx1, by0, by1 = a + 2, b - 2, 204, 262
    lay.rect(bx0, by0, bx1 - bx0, by1 - by0, 'D', 2.6, hgt=0.6)                # board (plywood)
    lay.rect(bx0, by0, bx1 - bx0, 1, 'D', 3.8, hgt=0.7)
    rng = np.random.default_rng(561)
    for _ in range(60):                                                         # paint splatter
        sx, sy = int(rng.integers(bx0, bx1)), int(rng.integers(by0, by1))
        lay.px(sx, sy, 'V', 2.6 + rng.random() * 1.6, hgt=0.65)
    # number stencils, sorted by run: C-17/41 .. /44 worn, /45 wet
    sx0 = bx0 + 2
    for i, num in enumerate(['41', '42', '43', '44', '45']):
        sy = by0 + 3 + i * 11
        wet = num == '45'
        lay.rect(sx0, sy, 31, 9, 'I', 4.2 if wet else 3.2, hgt=0.8)             # tin plate
        lay.rect(sx0, sy, 31, 1, 'I', 5.2, hgt=0.85)
        lay.px(sx0 + 15, sy - 1, 'I', 5.0, hgt=0.9)                              # nail
        m = K.text_mask('C-17/' + num)
        mh, mw = m.shape
        tx = sx0 + (31 - mw) // 2
        if wet:
            lay.put(m, tx, sy + 2, 'V', 4.4, hgt=0.5, flat=True, crisp=True)    # wet paint in the cut-outs
            for k in range(0, mw, 3):
                if m[mh - 1, k]:
                    lay.rect(tx + k, sy + 7, 1, 2 + (k % 2), 'V', 5.2, hgt=0.5)  # a drip
            lay.px(sx0 + 3, sy + 2, 'V', 6.0, hgt=0.9)
        else:
            lay.put(m, tx, sy + 2, 'D', 1.4, hgt=0.4, flat=True, crisp=True)    # holes: the board behind
            for k in range(8):                                                  # crusted paint on the edges
                lay.px(sx0 + int(rng.integers(0, 31)), sy + int(rng.integers(0, 9)), 'V', 2.4, hgt=0.85)
    # letter stencils in two alphabets (Cyrillic over Latin)
    for r, letters in enumerate(['АБВ', 'ABC']):
        for c, ch in enumerate(letters):
            lx, ly = bx0 + 36 + c * 6, by0 + 8 + r * 14
            if lx + 5 > bx1:
                continue
            lay.rect(lx, ly, 5, 8, 'I', 3.4, hgt=0.8)
            lay.put(K.text_mask(ch)[:, :3], lx + 1, ly + 1, 'D', 1.4, hgt=0.4, flat=True, crisp=True)
    # brushes in a can, paint tins, the bucket of red-brown
    lay.rect(a + 2, FL - 12, 8, 12, 'I', 3.0, hgt=0.7)
    lay.rect(a + 2, FL - 12, 8, 1, 'N', 1.2)
    for k in range(3):
        lay.line(a + 4 + k * 2, FL - 12, a + 3 + k * 3, FL - 22, 'D', 3.6)
        lay.rect(a + 2 + k * 3, FL - 24, 2, 3, 'V', 3.0, hgt=0.8)
    for k in range(2):
        lay.rect(a + 12 + k * 9, FL - 8, 8, 8, 'I', 3.4 - k * 0.6, hgt=0.7)
        lay.rect(a + 12 + k * 9, FL - 8, 8, 1, 'V', 3.6, hgt=0.75)
    k0, k1 = L.BUCKET
    for yy in range(FL - 18, FL):
        f = (yy - (FL - 18)) / 18.0
        lay.rect(k0 + int(f * 1.5), yy, k1 - k0 - int(f * 3), 1, 'I', 3.2 - f * 0.8, hgt=0.8)
    lay.rect(k0, FL - 18, k1 - k0, 2, 'V', 3.4, hgt=0.75)                     # paint surface, glossy
    lay.rect(k0 + 3, FL - 18, 4, 1, 'V', 5.6, hgt=0.8)
    for dx in (2, 7, 12):                                                       # runs down the side
        lay.rect(k0 + dx, FL - 16, 1, 3 + dx % 5, 'V', 3.2, hgt=0.8)
    lay.line(k1 - 4, FL - 18, k1 + 4, FL - 34, 'D', 3.8)                       # brush handle
    lay.rect(k1 + 2, FL - 37, 4, 4, 'D', 2.2, hgt=0.9)
    lay.line(k0 - 1, FL - 17, k1, FL - 19, 'I', 4.0)                            # handle (bail)
    # "НЕ КУРИТЬ" above the stand
    room.plate(a + 6, 186, 46, 11, [('НЕ КУРИТЬ', ('R', 2.6))], ramp='P', tone=4.8, ink=('R', 2.6),
               border=('R', 2.0), wear=0.05, seed=562)


def fire_shield(room):
    lay = room.lay
    a = L.PLATE_HEAP[0] + 2
    w = 38
    y0 = 186
    lay.rect(a, y0, w, 44, 'R', 2.0, hgt=0.5)
    lay.rect(a, y0, w, 1, 'R', 3.0, hgt=0.55)
    lay.rect(a + 1, y0 + 1, w - 2, 42, 'R', 1.6, hgt=0.45)
    for k in range(2):                                                           # conical buckets
        bx = a + 4 + k * 13
        for yy in range(y0 + 6, y0 + 16):
            f = (yy - (y0 + 6)) / 10
            lay.rect(bx + int(f * 3), yy, 10 - int(f * 6), 1, 'R', 3.2 - f * 0.6, hgt=0.8)
    lay.line(a + 30, y0 + 6, a + 30, y0 + 38, 'D', 3.4)                        # axe
    lay.rect(a + 28, y0 + 6, 6, 4, 'I', 3.8, hgt=0.9)
    lay.line(a + 6, y0 + 22, a + 24, y0 + 22, 'D', 3.2)                         # hook pole
    lay.line(a + 6, y0 + 30, a + 24, y0 + 30, 'D', 3.2)
    lay.rect(a + 22, y0 + 34, 6, 6, 'I', 2.6, hgt=0.8)                          # sand shovel blade


def plate_heap(room):
    lay = room.lay
    a, b = L.PLATE_HEAP
    rng = np.random.default_rng(571)
    nums = ['53117', '62409', '24871', '47115', '30298', '58226', '41760', '27503', '64091', '39844']
    for i, num in enumerate(nums):
        px = a + 2 + (i % 3) * 13 + int(rng.integers(-2, 3))
        py = FL - 7 - (i // 3) * 6 - int(rng.integers(0, 2))
        if py < 250:
            continue
        lay.rect(px, py, 14, 6, 'P', 4.6 + rng.normal(0, 0.3), hgt=0.7 + i * 0.02)
        lay.rect(px, py, 14, 1, 'P', 5.4, hgt=0.75)
        lay.rect(px, py + 5, 14, 1, 'P', 3.0, hgt=0.6)
        lay.put(K.text_mask(num[:3])[:, :11], px + 2, py + 1, 'I', 1.0, hgt=0.75, flat=True, crisp=True)
        for _ in range(3):
            lay.px(px + int(rng.integers(0, 14)), py + int(rng.integers(0, 6)), 'K', 2.6, hgt=0.7)   # rust chips
    # some freshly overpainted in red-brown
    for (ox, oy) in ((a + 15, FL - 13), (a + 2, FL - 19)):
        lay.rect(ox, oy, 12, 5, 'V', 3.4, hgt=0.8)
        lay.px(ox + 2, oy, 'V', 5.4, hgt=0.85)
    # leaning ones against the wall
    for k in range(3):
        lx = b - 10 + k * 3
        for yy in range(FL - 24, FL):
            lay.rect(lx + (FL - yy) // 6, yy, 2, 1, 'P', 4.0 - k * 0.4, hgt=0.6)


def kit_pile(room):
    """The conversion kit at the siding entrance: stove-pipe elbows, a small iron stove, zinc buckets, bench
    brackets (exp_stovepipes)."""
    lay = room.lay
    a, b = L.KIT_PILE
    # small iron stove (the kind that goes into the wagons)
    lay.rect(a + 2, FL - 16, 12, 14, 'I', 2.4, hgt=0.9)
    lay.rect(a + 2, FL - 16, 12, 1, 'I', 3.8, hgt=1.0)
    lay.rect(a + 4, FL - 12, 6, 6, 'N', 1.4, hgt=0.8)
    for lx in (a + 3, a + 12):
        lay.rect(lx, FL - 2, 1, 2, 'I', 2.0, hgt=0.7)
    K.cyl(lay, a + 6, FL - 26, 4, 10, 'I', 2.6, hgt=1.0, axis='v')
    # stove-pipe straights + elbows heaped
    for (px, py, ln) in ((a + 18, FL - 6, 20), (a + 20, FL - 11, 16)):
        K.cyl(lay, px, py, ln, 5, 'I', 2.8, hgt=1.0, axis='h')
    for (ex, ey) in ((a + 30, FL - 20), (a + 16, FL - 24)):
        for i in range(8):
            lay.rect(ex + i, ey + int(round(4 - math.sqrt(max(0, 16 - (i - 4) ** 2)))), 5, 5, 'I', 3.0, hgt=1.0)
            lay.px(ex + i, ey + int(round(4 - math.sqrt(max(0, 16 - (i - 4) ** 2)))), 'I', 4.4, hgt=1.0)
    # zinc buckets (grey, a little sheen) and bench brackets (angle irons)
    for k, bx in enumerate((b - 14, b - 24)):
        lay.rect(bx, FL - 11 + k * 2, 9, 11 - k * 2, 'S', 0.6 + k * 0.3, hgt=0.8)
        lay.rect(bx, FL - 11 + k * 2, 9, 1, 'S', 2.4, hgt=0.85)
        lay.px(bx + 2, FL - 8 + k * 2, 'S', 3.0, hgt=0.9)
    for k in range(3):
        lay.rect(a + 2 + k * 5, FL - 30 - k, 1, 8, 'I', 3.2, hgt=0.9)
        lay.rect(a + 2 + k * 5, FL - 23 - k, 5, 1, 'I', 3.2, hgt=0.9)


def brazier(room):
    """The workers' brazier by the portal: a perforated drum on bricks, embers still red (flicker strip on top)."""
    lay = room.lay
    a, b = L.BRAZIER
    lay.rect(a, FL - 4, b - a, 4, 'K', 2.6, hgt=0.6)
    for yy in range(FL - 26, FL - 4):
        lay.rect(a + 2, yy, b - a - 4, 1, 'I', 1.8 + (yy % 4 == 0) * 0.5, hgt=0.9)
    for (hx, hy) in ((a + 5, FL - 20), (a + 10, FL - 20), (a + 14, FL - 20), (a + 7, FL - 14), (a + 12, FL - 14),
                     (a + 5, FL - 8), (a + 10, FL - 8), (a + 14, FL - 8)):
        lay.rect(hx, hy, 2, 2, 'L', 3.6, emis=True)
    lay.rect(a + 3, FL - 27, b - a - 6, 2, 'R', 2.4, emis=True)
    room.light('brazier', ((a + b) / 2, FL - 26), 'warm', 0.7, 80, 10)


def portal(room):
    lay = room.lay
    a, b = L.PORTAL
    top = 148
    # concrete arch ring, the gate (two braced leaves, a wicket), light leaking at the gaps
    for x in range(a, b):
        c = (x + 0.5 - (a + 60)) / 50.0
        ay = int(round(top - 22 * math.sqrt(max(0.0, 1 - min(1.0, c * c)))))
        lay.rect(x, ay - 8, 1, 8, 'C', 3.6, hgt=0.8)
        lay.px(x, ay - 8, 'C', 4.6, hgt=0.85)
    lay.rect(a, top - 10, 8, FL - top + 10, 'C', 3.4, hgt=0.8)
    lay.rect(a, top - 10, 1, FL - top + 10, 'C', 4.6, hgt=0.85)
    g0 = a + 8
    room.planks_v(g0, b, top, FL, 'D', 2.2, width=7, seed=591, hgt=0.6)
    for yy in (top + 12, FL - 22):                                               # iron bands
        lay.rect(g0, yy, b - g0, 3, 'I', 2.0, hgt=0.8)
        K.rivets(lay, g0 + 2, b, yy + 1, 7, 'I', 3.6, 1.2)
    for (x, y) in K.bres(g0 + 2, FL - 24, b - 2, top + 16):                     # Z brace
        lay.rect(x, y, 3, 2, 'D', 3.2, hgt=0.8)
    lay.rect(g0 + (b - g0) // 2 + 2, 238, 5, 4, 'I', 3.8, hgt=1.0)                 # padlock on the hasp
    lay.rect(g0 + (b - g0) // 2 + 3, 235, 3, 3, 'I', 2.4, hgt=1.0)
    lay.px(g0 + (b - g0) // 2 + 4, 239, 'N', 1.0)
    wk0 = g0 + 10                                                                # wicket door
    lay.rect(wk0, FL - 54, 22, 1, 'N', 1.0)
    lay.rect(wk0, FL - 54, 1, 54, 'N', 1.0)
    lay.rect(wk0 + 21, FL - 54, 1, 54, 'N', 1.0)
    lay.rect(wk0 + 17, FL - 30, 2, 4, 'I', 3.8, hgt=0.9)
    # dawn through the cracks (unlit glow) and under the gate; snow blown in
    gap_x = g0 + (b - g0) // 2 + 6
    lay.rect(gap_x, top + 4, 1, FL - top - 8, 'S', 4.6, emis=True)
    for yy in range(top + 20, FL - 10, 9):
        lay.px(gap_x + 1, yy, 'S', 3.2, emis=True)
    lay.rect(g0, FL - 2, b - g0, 2, 'S', 4.0, emis=True)
    for x in range(a - 30, b):
        hgt = max(0.0, 6 - abs(x - (b - 26)) / 9.0) + 2 * math.sin(x / 5.0) * (x > a)
        if hgt > 0.5:
            lay.rect(x, int(FL - hgt), 1, int(math.ceil(hgt)), 'S', 3.4 + (x % 3 == 0) * 0.8, hgt=0.3)
    room.light('portal_dawn', (gap_x, 230), 'cold', 0.9, 150, 4, pool=0.35, pool_depth=40, pool_w=18,
               pool_spread=0.9)
    # dwarf shunting signal, blue (stop for shunting)
    sx = a - 12
    lay.rect(sx, FL - 20, 9, 20, 'I', 1.8, hgt=0.8)
    lay.rect(sx, FL - 20, 9, 1, 'I', 3.4, hgt=0.9)
    lay.put(K.disc(5), sx + 2, FL - 17, 'S', 4.0, emis=True)
    lay.put(K.disc(5), sx + 2, FL - 10, 'N', 1.0, hgt=0.9)
    room.light('shunt_blue', (sx + 4, FL - 14), 'cold', 0.4, 40, 4)


# =========================================================================== wagon 24 318
def wagon(room):
    """Two-axle covered wagon converted for people, track 1 (back): planked body on a steel frame, stove pipe
    through the roof, sliding door half open (or open), the four numbers it carried."""
    lay = room.lay
    a, b = L.WAGON_BODY
    roof, flo = L.WAGON_ROOF, L.WAGON_FLOOR
    d0, d1 = L.WAGON_DOOR
    # roof (dark), stove pipe with cap and tin collar
    for yy in range(roof - 6, roof + 2):
        k = (yy - (roof - 6)) / 8.0
        inset = int(round(3 * (1 - k) ** 2 * 3))
        lay.rect(a - 2 + inset, yy, b - a + 4 - 2 * inset, 1, 'I', 1.6 + k * 1.2, hgt=0.9)
    lay.rect(a - 2, roof + 1, b - a + 4, 1, 'I', 3.6, hgt=1.0)
    px = 1612
    K.cyl(lay, px, 164, 5, roof - 4 - 164, 'I', 2.4, hgt=1.0, axis='v')
    lay.rect(px - 3, 160, 11, 4, 'I', 2.6, hgt=1.0)
    lay.rect(px - 2, roof - 6, 9, 2, 'L', 2.2, hgt=1.0)                          # fresh tin collar
    # body: horizontal planks in red-brown, steel stanchions and braces
    room.planks_h(a, b, roof + 2, flo, 'V', 2.6, height=5, seed=601, hgt=0.5, var=0.2)
    for sx in (a, a + 40, d0 - 3, d1, b - 4):
        lay.rect(sx, roof + 2, 4, flo - roof - 2, 'V', 1.8, hgt=0.9)
        lay.rect(sx, roof + 2, 1, flo - roof - 2, 'V', 3.0, hgt=0.95)
    for (p0, p1) in ((a + 4, a + 40), (a + 44, d0 - 3), (d1 + 4, b - 4)):
        for (x, y) in K.bres(p0, flo - 2, p1 - 1, roof + 6):
            lay.rect(x, y, 2, 2, 'V', 1.9, hgt=0.85)
    lay.rect(a, roof + 2, b - a, 3, 'V', 1.8, hgt=0.9)                           # top rail
    lay.rect(a, flo - 3, b - a, 3, 'V', 1.6, hgt=0.9)                            # bottom rail
    for hx in (a + 8, b - 22):                                                   # small hatches near the roof
        lay.rect(hx, roof + 7, 14, 9, 'V', 1.4, hgt=0.6)
        lay.rect(hx + 1, roof + 8, 12, 7, 'N', 0.8)
        for k in range(hx + 3, hx + 13, 3):
            lay.rect(k, roof + 8, 1, 7, 'I', 2.4, hgt=0.9)
    # weathering: grime toward the bottom, rust runs
    rng = np.random.default_rng(602)
    grime = np.clip((np.arange(flo - roof, dtype=np.float32)[:, None] - 30) / 40.0, 0, 1)
    lay.tone[roof:flo, a:b] -= grime[:, :1] * 0.5
    for _ in range(18):
        rx = int(rng.integers(a + 2, b - 2))
        ry = int(rng.integers(roof + 6, flo - 20))
        for yy in range(ry, ry + int(rng.integers(6, 18))):
            lay.px(rx, yy, 'K', 2.0, hgt=0.6)
    # old faded stencil block on the left panel: the emblem (insignia site) and the load ("20 т")
    import env_karsk_emblems as KE
    emb = KE.kind_for('gw7', room.hist)
    lay.put(KE.mask(emb), 1632, roof + 42, 'P', 3.0, hgt=0.55, flat=True, crisp=True)
    K.worn_text(lay, '20 Т', 1631, roof + 51, 'P', 3.0, wear=0.3, seed=621, hgt=0.55)
    # door: rail on top, the leaf half open (or fully open after c4c_inspect_wagon), interior
    lay.rect(d0 - 4, roof + 4, (d1 - d0) * 2 + 8, 2, 'I', 2.8, hgt=1.0)
    lay.rect(d0, roof + 6, d1 - d0, flo - roof - 6, 'N', 0.6, hgt=-0.4)          # dark interior
    opened = room.cfg.get('wagon_door', 'half') == 'open'
    leaf0 = d0 + (d1 - d0) // 2 if not opened else d1 + 2
    # interior: benches of raw boards, a bucket, straw; light from the bulb falling in
    inner_vis = (d0, leaf0)
    lay.rect(inner_vis[0], flo - 22, inner_vis[1] - inner_vis[0], 3, 'D', 3.8, hgt=0.3)    # bench
    lay.rect(inner_vis[0], flo - 19, inner_vis[1] - inner_vis[0], 1, 'D', 2.0, hgt=0.2)
    lay.rect(inner_vis[0], flo - 4, inner_vis[1] - inner_vis[0], 3, 'L', 1.6, hgt=0.1)     # straw
    for k in range(inner_vis[0], inner_vis[1], 3):
        lay.px(k, flo - 5, 'L', 2.6, hgt=0.15)
    if opened:
        lay.rect(d0 + 30, flo - 14, 8, 10, 'I', 2.2, hgt=0.4)                    # bucket
        lay.rect(d0 + 30, flo - 14, 8, 1, 'I', 3.4, hgt=0.5)
        lay.rect(d0 + 10, roof + 8, 10, 30, 'N', 1.4, hgt=0.2)                   # small iron stove + pipe
        lay.rect(d0 + 13, roof + 6, 3, 10, 'I', 2.4, hgt=0.4)
        lay.rect(d0 + 9, flo - 30, 12, 10, 'I', 2.0, hgt=0.4)
        for k in range(6):                                                        # scratched names (illegible)
            sxx = d0 + 24 + (k % 3) * 7
            syy = roof + 18 + (k // 3) * 6
            lay.hline(sxx, syy, 5, 'D', 3.4, hgt=0.25)
            lay.px(sxx + 1, syy + 1, 'D', 3.2, hgt=0.25)
        lay.rect(d0 + 2, flo - 22, 2, 18, 'D', 3.0, hgt=0.3)
    for yy in range(roof + 6, flo):                                              # the leaf
        pass
    room.planks_v(leaf0, leaf0 + (d1 - d0), roof + 6, flo - 1, 'V', 2.9, width=5, seed=603, hgt=0.7, var=0.15)
    lay.rect(leaf0, roof + 6, d1 - d0, 2, 'V', 3.6, hgt=0.9)
    lay.rect(leaf0, roof + 6, 2, flo - roof - 7, 'V', 3.8, hgt=0.95)
    lay.rect(leaf0 + d1 - d0 - 2, roof + 6, 2, flo - roof - 7, 'V', 1.6, hgt=0.8)
    for (x, y) in K.bres(leaf0 + 3, flo - 4, leaf0 + d1 - d0 - 3, roof + 10):
        lay.rect(x, y, 2, 2, 'V', 2.0, hgt=0.9)
    lay.rect(leaf0 + 4, (roof + flo) // 2, 3, 6, 'I', 3.4, hgt=1.0)               # handle
    # chalk on the leaf: "Вт 23.40" (Tuesday's run) -- the date clue of the number puzzle
    K.text(lay, 'ВТ 23.40', leaf0 + (d1 - d0) / 2, roof + 22, 'P', 5.4, center=True, hgt=0.95)
    lay.line(leaf0 + 6, roof + 29, leaf0 + d1 - d0 - 7, roof + 29, 'P', 4.6)
    # ---- the number field: base coat, ghost of C-17/42, "47 702" brushed, the fresh patch + stencil C-17/45
    n0, n1 = L.NUMBER_FIELD
    K.worn_text(lay, 'C-17/42', n0 + 4, flo - 22, 'V', 3.6, wear=0.45, seed=611, hgt=0.55)     # ghost under paint
    K.worn_text(lay, '47 702', n0 + 6, flo - 14, 'P', 3.8, wear=0.12, seed=612, hgt=0.6)
    for k in range(4):                                                            # brush strokes over it
        lay.rect(n0 + 4 + k * 7, flo - 15, 5, 1, 'V', 3.0, hgt=0.55)
    pf0, pf1, pt0, pt1 = n0, n1 - 2, roof + 12, roof + 36
    for yy in range(pt0, pt1):                                                    # the fresh patch, wet sheen
        lay.rect(pf0, yy, pf1 - pf0, 1, 'V', 3.2 + 0.25 * math.sin(yy * 0.9), hgt=0.6)
    for k in range(pf0 + 3, pf1 - 2, 9):
        lay.rect(k, pt0 + 1, 1, pt1 - pt0 - 2, 'V', 4.4, hgt=0.65)                # brush direction highlights
    for k in range(pf0 + 4, pf1, 11):
        lay.rect(k, pt1, 1, 2 + (k % 3), 'V', 3.8, hgt=0.6)                         # runs below the patch
    m = K.text_mask('C-17/45', '57s')
    mh, mw = m.shape
    tx = pf0 + (pf1 - pf0 - mw) // 2
    ty = pt0 + (pt1 - pt0 - mh) // 2
    lay.put(m, tx, ty, 'P', 5.8, hgt=0.7, flat=True, crisp=True)                   # fresh white paint
    lay.rect(tx - 3, ty - 3, mw + 6, 1, 'I', 4.4, hgt=0.9)                          # the tin stencil still on
    lay.rect(tx - 3, ty + mh + 2, mw + 6, 1, 'I', 4.0, hgt=0.9)
    lay.rect(tx - 3, ty - 3, 1, mh + 6, 'I', 4.4, hgt=0.9)
    lay.rect(tx + mw + 2, ty - 3, 1, mh + 6, 'I', 3.6, hgt=0.9)
    for (qx, qy) in ((tx - 5, ty - 5), (tx + mw + 1, ty - 5), (tx - 5, ty + mh + 1), (tx + mw + 1, ty + mh + 1)):
        lay.rect(qx, qy, 4, 4, 'P', 4.6, hgt=0.95)                                   # tape at the corners
        lay.px(qx + 3, qy + 3, 'P', 3.4, hgt=0.9)
    # ---- maintenance marks on the right end of the frame (revision dates, depot code; one line painted over)
    K.text(lay, 'РЕВ 11.62', b - 18, flo - 13, 'P', 4.2, center=True, hgt=0.7)
    K.text(lay, 'ДЕП КАРСК', b - 18, flo - 7, 'P', 4.0, center=True, hgt=0.7)
    lay.rect(b - 36, flo - 20, 36, 5, 'V', 3.3, hgt=0.7)                               # the line painted over
    lay.px(b - 30, flo - 20, 'V', 5.0, hgt=0.75)
    # ---- frame: solebar with the enamel plate "24 318", buffers, couplings, springs, axle boxes, wheels
    lay.rect(a - 4, flo, b - a + 8, 6, 'I', 1.8, hgt=0.9)
    lay.rect(a - 4, flo, b - a + 8, 1, 'I', 3.2, hgt=1.0)
    lay.rect(n0 + 4, flo + 1, 27, 6, 'P', 5.0, hgt=1.0)
    lay.rect(n0 + 4, flo + 1, 27, 1, 'P', 5.8, hgt=1.0)
    K.text(lay, '24 318', n0 + 4 + 13.5, flo + 1, 'I', 0.8, center=True, hgt=1.0)
    lay.px(n0 + 5, flo + 3, 'I', 3.0)
    lay.px(n0 + 29, flo + 3, 'I', 3.0)
    for (bx, sgn) in ((a - 4, -1), (b + 4, 1)):                                   # buffers + screw couplings
        lay.rect(bx + (-8 if sgn < 0 else 0), flo - 6, 8, 4, 'I', 2.6, hgt=1.0)
        lay.put(K.disc(7), bx + (-12 if sgn < 0 else 6), flo - 8, 'I', 3.4, hgt=1.0)
        lay.rect(bx + (-6 if sgn < 0 else 0), flo + 1, 6, 2, 'I', 2.2, hgt=0.9)
    for wx in (1592, 1700):
        lay.rect(wx - 16, flo + 6, 32, 3, 'I', 2.6, hgt=1.0)                         # leaf spring
        for k in range(3):
            lay.rect(wx - 14 + k * 2, flo + 6 + k, 28 - k * 4, 1, 'I', 3.2, hgt=1.0)
        lay.rect(wx - 5, flo + 8, 10, 8, 'I', 2.2, hgt=1.0)                           # axle box
        lay.rect(wx - 5, flo + 8, 10, 1, 'I', 3.6, hgt=1.0)
        wm = K.disc(30)
        lay.put(wm, wx - 15, FL - 26, 'I', 2.2, hgt=0.9)                              # wheel (rail at y 294)
        ring = wm & ~K.erode(wm, 2)
        lay.put(ring, wx - 15, FL - 26, 'I', 3.8, hgt=1.0)
        lay.put(wm & ~K.erode(wm, 1), wx - 15, FL - 26, 'I', 1.2, hgt=0.8)
        lay.put(K.disc(8), wx - 4, FL - 15, 'I', 3.0, hgt=1.0)                        # hub
        lay.px(wx - 1, FL - 13, 'I', 4.6, hgt=1.0)
        for k in range(6):
            ang = k * math.pi / 3
            lay.line(wx, FL - 11, int(round(wx + 9 * math.cos(ang))), int(round(FL - 11 + 9 * math.sin(ang))), 'I',
                     4.0)


# =========================================================================== floors of tunnel + siding
def floors(room):
    lay = room.lay
    x0, x1 = L.TUNNEL[0], W
    w = x1 - x0
    hh = H - FL
    nz = K.noise(w, hh, 14, 631) * 0.35 + K.noise(w, hh, 2, 632, octaves=1) * 0.15
    lay.put(np.ones((hh, w), bool), x0, FL, 'C', 2.4 + nz, hgt=0.0, flat=False)
    lay.rect(x0, FL, w, 3, 'N', 1.6, hgt=-0.1)                                  # drainage gutter at the wall
    lay.rect(x0, FL + 1, w, 1, 'S', 1.2, hgt=-0.1)
    # slab joints in perspective
    vp = (x0 + x1) / 2
    for u in range(x0 - 800, x1 + 800, 64):
        for yy in range(FL + 3, H):
            fr = (yy + 0.5 - L.HORIZON) / (FL - L.HORIZON)
            xx = int(round(vp + (u - vp) * fr))
            if x0 <= xx < x1:
                lay.px(xx, yy, 'C', 1.6)
    for ry in (FL + 22, FL + 46):
        lay.rect(x0, ry, w, 1, 'C', 1.8)
    # tunnel track (single, the walk runs between its rails) + siding track 1 (back) + track 2 (front)
    _track(room, L.TUNNEL[0] + 22, L.SIDING[0] + 4, 294, 312, polished=True)
    _track(room, L.SIDING[0] + 4, W, 290, 295, polished=False, sleepers=False)
    _track(room, L.SIDING[0] + 20, W, 330, 352, polished=False)
    # the switch W2: the diverging rails toward the sealed gallery
    for (r_y, k) in ((294, 0.0), (312, 1.0)):
        for x in range(L.T_POINT[1] + 10, L.T_BRANCH[0] + 20):
            f = (x - (L.T_POINT[1] + 10)) / (L.T_BRANCH[0] + 20 - (L.T_POINT[1] + 10))
            yy = int(round(r_y - (r_y - (FL + 1 + k * 3)) * f * f))
            lay.rect(x, yy, 1, 2, 'I', 2.6, hgt=0.6)
            lay.px(x, yy, 'S', 2.0, hgt=0.7)
    # footprints in the dust beside the polished rails (ev_c4_fresh_tracks) + a drop of red-brown
    rng = np.random.default_rng(633)
    for k in range(70):
        fx = L.TUNNEL[0] + 30 + k * 7 + int(rng.integers(-2, 3))
        fy = 300 + (k % 2) * 4 + int(rng.integers(0, 2))
        if fx >= L.SIDING[0]:
            break
        lay.rect(fx, fy, 3, 1, 'C', 1.4, hgt=-0.02)
    lay.px(L.TUNNEL[0] + 26, FL + 4, 'V', 3.6)
    lay.px(L.TUNNEL[0] + 27, FL + 4, 'V', 3.0)
    # puddles under the drips (the drip strips land here)
    for dx in L.T_DRIPS + [1418, 1760]:
        m, mx, my = lay.ellipse_mask(dx, FL + 6, 9, 2)
        lay.put(m, mx, my, 'S', 1.4, hgt=-0.05, flat=False)
        lay.rect(dx - 6, FL + 6, 4, 1, 'S', 3.4)
    # paint drips and a footprint trail in red-brown at the stand; snow blown in from the portal
    for k in range(40):
        px_ = L.PAINT_STAND[0] + int(rng.integers(0, 120))
        py_ = FL + 2 + int(rng.integers(0, 22))
        lay.px(px_, py_, 'V', 2.2 + rng.random(), hgt=0.02)
    for x in range(L.PORTAL[0] - 120, W):
        k = (x - (L.PORTAL[0] - 120)) / 120.0
        for yy in range(FL, H):
            if yy < FL + 14 and rng.random() < 0.05 * k * k * (1 - (yy - FL) / 14.0):
                lay.px(x, yy, 'S', 2.6 + rng.random() * 1.6, hgt=0.05)
    # oil stains under the wagon
    for (ox, oy, rx, ry) in ((1600, FL + 3, 14, 2), (1700, FL + 4, 18, 2)):
        m, mx, my = lay.ellipse_mask(ox, oy, rx, ry)
        lay.put(m, mx, my, 'N', 1.4, hgt=-0.02)
    m = np.zeros((H, W), bool)
    m[FL:, x0:] = lay.rid[FL:, x0:] >= 0
    lay.paint_normal(m, 0, 0, (0.0, 0.86, 0.5))
    lay.lgain[FL:, x0:] = 0.75
    mc = np.zeros((H, W), bool)
    mc[FL:, :L.DOOR_WALL[1]] = lay.rid[FL:, :L.DOOR_WALL[1]] >= 0
    lay.paint_normal(mc, 0, 0, (0.0, 0.86, 0.5))
    lay.lgain[FL:, :L.DOOR_WALL[1]] = 0.75


def _track(room, x0, x1, far_y, near_y, polished=True, sleepers=True):
    lay = room.lay
    vp = (L.TUNNEL[0] + W) / 2
    if sleepers:
        for u in range(x0 - 600, x1 + 600, 13):
            pts = []
            for yy in range(far_y - 1, near_y + 3):
                fr = (yy + 0.5 - L.HORIZON) / (FL - L.HORIZON)
                xx = int(round(vp + (u - vp) * fr))
                if x0 <= xx < x1 - 3:
                    lay.rect(xx, yy, 4, 1, 'I', 1.5 + (yy - far_y) * 0.02, hgt=0.3)
    for ry, th in ((far_y, 2), (near_y, 3)):
        lay.rect(x0, ry, x1 - x0, th, 'I', 2.2, hgt=0.9)
        lay.rect(x0, ry + th, x1 - x0, 1, 'N', 1.0)
        lay.rect(x0, ry, x1 - x0, 1, 'S', 4.6 if polished else 2.4, hgt=1.0, crisp=True)
