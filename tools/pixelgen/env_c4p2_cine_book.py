"""env_c4p2_cine_book -- LS_C4P2_Book (12 s): Berlin -> Karsk, Monday -> Tuesday.  THE shared object of this
round: Ekdahl's Swedish guidebook (1938, dark red cloth, sprinkled red edges, chapter "Karsk -- stationen och
depån", pages 212/213).

  b1 close           the dining car at the Ostbahnhof, seen from above: the open book on the damask cloth among
                     the table's things (the lamp, Ekdahl's coffee, the menu, a carnation, the cruet, the ashtray);
                     Konrad's bare hand (navy sleeve, shirt cuff) slides the German half of card 0417 (upside down)
                     and the folded tracing onto page 213 and withdraws; Ekdahl's grey glove (tweed sleeve) lifts
                     the right half and swings it over; in the black window the man from the kiosk is reflected
  b2 macro_locked    the book in profile at table height (its head edge to the camera, the spine at the left): the
                     upper half comes down (ease-in), the card's corner between the pages, the book shuts at
                     BOOK_SHUT -- a breath of dust in the lamp light
  b3 macro_to_medium the same profile, the same corner, on the oilcloth of the Karsk depot canteen: the cover lifts
                     under the grey glove (BOOK_OPEN); hard cut on the movement to the canteen table from above (the
                     camera settles back): the book open at 212 among tea glasses in their holders, black bread,
                     sugar, the ashtray, a newspaper; the glove holds the page, Alexei's hand (quilted sleeve, the
                     knitted cuff, a plaster on the index) lies where Konrad's lay, his fingers on the German half
  b4 establishing    the depot showcase under floodlights (env_c4p2_cine_show.py)
Close shots are painted flat (env_c4p2_cine_flat.py) and the hands drawn with the game's sprite shader at full
resolution (env_c4p2_cine_hands.py) -- crisp pixel art, no soft render, no bokeh.  The book on the tables is the
one 3-D model of env_c4p2_cine_book3d.py (flat per-face light, outlined, a flat cast shadow).
Outputs assets/cinematics/c4p2/book/*.png; anchors in layout.json "book".
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_kit as K
import env_c4p2_cine_pal as PAL
import env_c4p2_cine_flat as FL
import env_c4p2_cine_hands as HD
from env_c4p2_cine_kit import GB, Lt, tex_noise

L = K.LAYOUT.setdefault('book', {})
PAL_B = PAL.BERLIN_ST
PAL_K = PAL.KARSK

SPREAD = (214, 132, 426, 292)            # open book: left page x0..318, gutter 320, right page 322..x1 (b1 and b3)
GUTTER = 320
CARD = (64, 40)                           # the German half of card 0417 (w, h)
CARD_ON = (344, 196)                      # its place on page 213 (top-left)
TRACE_ON = (334, 222)
BOOK_SHUT = 4.15                          # b2: the halves meet (c4p2cine_book_shut thud)
BOOK_OPEN = 5.12                          # b3a: the cover leaves the page block (c4p2cine_canteen)
CLOSE_T = (2.6, 3.5)                      # b1: the right half swings up to ~80 deg over this span
SLIDE_T = (0.3, 1.5)                      # b1: Konrad's hand slides the card in
WITHDRAW_T = (1.6, 2.3)
CUT_B3 = 5.62                             # b3: the macro cuts to the table on the cover's movement
SETTLE = (5.62, 6.4, 10)                  # b3b: the camera settles back over this span by this many px


# ================================================================================================= paper
def page_tex(w, h, which, seed):
    """A guidebook page (GB albedo, w x h): aged paper, the running head, justified text, the page number,
    on 213 a small engraved plan of a depot."""
    g = GB(w, h)
    g.put(np.ones((h, w), bool), '#e6dabd', tex=tex_noise(g, 9, seed, 0.03), z=10)
    edge = np.clip(1 - np.minimum.reduce([g.xx, w - 1 - g.xx, g.yy, h - 1 - g.yy]) / 6.0, 0, 1)
    g.mul(np.ones((h, w), bool), 1 - np.round(edge * 2) / 2 * 0.1)
    head = 'KARSK' if which == 212 else 'STATIONEN OCH DEPÅN'
    hw_ = K.VK.vtext(head, 's').shape[1]
    g.put(g.text(head, w // 2 - hw_ // 2, 6, 's'), '#5a4a3a', z=9)
    num = str(which)
    nx = 6 if which == 212 else w - 6 - K.VK.vtext(num, 's').shape[1]
    g.put(g.text(num, nx, 6, 's'), '#3a2a1e', z=9)
    g.put(g.box(6, 14, w - 6, 15), '#8a7a62', z=9)
    y = 20
    k = 0
    while y < h - 10:
        if which == 213 and 60 <= y < 112:
            y += 3
            continue
        x_end = w - 7 if (K.hash2(k, 3, seed) > 0.12) else int(w * (0.4 + 0.4 * K.hash2(k, 4, seed)))
        x = 7 if not (k % 9 == 0) else 11
        while x < x_end:
            ln = 2 + int(K.hash2(x, k, seed) * 7)
            g.put(g.box(x, y, min(x_end, x + ln), y + 1), '#5e564a', z=9)
            x += ln + 2
        y += 4 if k % 9 != 8 else 7
        k += 1
    if which == 213:
        ox, oy = 10, 60
        g.put(g.box(ox, oy, w - 10, oy + 50), '#efe4c8', z=8)
        for i in range(7):
            a = math.radians(200 + i * 18)
            g.put(g.line([(ox + 30, oy + 44), (ox + 30 + 26 * math.cos(a), oy + 44 + 26 * math.sin(a))], 0.4), '#4a4036',
                  z=7)
        g.put(g.box(ox + 50, oy + 30, w - 14, oy + 31) | g.box(ox + 50, oy + 36, w - 14, oy + 37), '#4a4036', z=7)
        g.put(g.box(ox + 60, oy + 20, ox + 76, oy + 28), '#6a5a48', z=7)
        g.put(g.text('DEPÅN', ox + 4, oy + 2, 's'), '#4a4036', z=7)
    return g


def card_rgba(upside_down=True, lit=('#ffd9a0', 1.0)):
    """The German half of card 0417: cream index card, ruled, typed (upside down in the book), its right edge the
    torn perforation (teeth)."""
    w, h = CARD
    g = GB(w, h)
    m = np.ones((h, w), bool)
    teeth = (g.xx > w - 4) & (np.mod(g.yy, 4) >= 2)
    g.put(m & ~teeth, '#ece2c6', z=10)
    for ry in range(9, h - 3, 5):
        g.put(g.box(3, ry, w - 6, ry + 1), '#9ab0c8', z=9)
    g.put(g.box(3, 3, w - 6, 4), '#c84a3a', z=9)
    for k, (tx, ty, s_) in enumerate(((5, 6, '0417'), (5, 11, 'LINDNER, ANNA'), (5, 16, 'GEB. KOWALENKO'),
                                      (5, 26, 'C-17 RUECKF. OST'))):
        g.put(g.text(s_, tx, ty - 2, 's'), '#2a2a3a', z=8)
    out = g.final([Lt(w * 0.3, -40, -60, lit[0], I=lit[1], r=400)], PAL_B, spread=0.0, sky='#d0c8b8', gnd='#8a8070',
                  amb=0.9)
    if upside_down:
        out = out[::-1, ::-1].copy()
    return FL.outline_rgba(out, 0.72)


def tracing_rgba():
    """The folded tracing: pale translucent paper, the room of Kordon-17 in ruled pencil (Tür West, Tür Ost)."""
    w, h = 54, 34
    g = GB(w, h)
    g.put(np.ones((h, w), bool), '#d6dcd8', z=10)
    g.put(g.box(0, h // 2, w, h // 2 + 1), '#aab4b0', z=9)
    g.put(g.box(6, 6, w - 6, 7) | g.box(6, h - 8, w - 6, h - 7) | g.box(6, 6, 7, h - 7) | g.box(w - 7, 6, w - 6, h - 7),
          '#5a6470', z=8)
    g.put(g.box(6, 12, 7, 18) | g.box(w - 7, 14, w - 6, 20), '#d6dcd8', z=7)
    g.put(g.box(20, 10, 34, 12), '#5a6470', z=8)
    out = g.final([Lt(10, -40, -60, '#ffd9a0', I=1.0, r=400)], PAL_B, spread=0.0, sky='#d0c8b8', gnd='#8a8070', amb=0.9)
    return FL.outline_rgba(out, 0.78)


# ================================================================================================= the top camera
def cam_top():
    """b1 / b3b: looking down on the table (80 deg), the spine at x 320, the book's centre at y 212."""
    import env_c4p2_cine_book3d as B3
    e = math.radians(80)
    return B3.Cam((0, 1180 * math.sin(e), 80 + 1180 * math.cos(e)), (0, 0, 80), f=1180, c=(320, 212))


SWING = (0, 0, 14, 30, 47, 64, 80)       # b1 frames: 0 the open book (no card baked), 1.. card baked, rising
KEY_B = (-0.5, 0.8, 0.3)
KEY_K = (0.5, 0.8, 0.25)
LAMP_B = (1.0, 0.88, 0.72)
LAMP_K = (1.0, 0.82, 0.6)


def _proj_tex(cam, x_tex, y_tex, theta, page='213'):
    """Screen position of a point of page 213's texture (x from the spine side, y from the head) at angle theta."""
    import env_c4p2_cine_book3d as B3
    P = B3._rot((float(x_tex), B3.H, float(y_tex)), theta, B3.H)
    p, z = cam.p(np.asarray(P, float))
    return [int(round(p[0])), int(round(p[1]))]


def _edge_mid(cam, theta):
    """Screen position of the middle of the right half's fore-edge at angle theta (where a hand lifts it)."""
    import env_c4p2_cine_book3d as B3
    P = B3._rot((B3.W, B3.H * 0.5, B3.D * 0.55), theta, B3.H)
    p, z = cam.p(np.asarray(P, float))
    return [int(round(p[0])), int(round(p[1]))]


def book_top(cam, thetas, pal, key, lamp, card, shadow):
    """The 3-D book seen from above: flat per-face light, no dither, a dark outline, a flat cast shadow."""
    import env_c4p2_cine_book3d as B3
    out = []
    for i, f in enumerate(B3.book_frames(cam, thetas, pal, key, lamp, 0.5, card=card, spread=0.0)):
        f = FL.outline_rgba(f, 0.45)
        rise = max(0.0, thetas[i]) / 80.0
        out.append(FL.shadow_rgba(f, shadow[0] * (1 + rise), shadow[1] * (1 + 2 * rise), shadow[2]))
    return out


# ================================================================================================= table things
def _ell_shade(F, cx, cy, rx, ry, base, dark, light, key=(-1, -1)):
    """A flat ellipse with a darker crescent away from the key and a lighter one toward it, outlined."""
    m = F.ell(cx, cy, rx, ry)
    F.fill(m, base)
    kx, ky = key
    F.fill(m & ~F.ell(cx + kx * rx * 0.18, cy + ky * ry * 0.18, rx, ry), dark)
    F.fill(m & ~F.ell(cx - kx * rx * 0.22, cy - ky * ry * 0.22, rx, ry), light)
    return m


def cup_saucer(F, cx, cy, r, liquid, china=('#f4f0e6', '#d6d0c2', '#fffdf6', '#b8b0a0'), gold='#c09034',
               key=(-1, -1), sh=(5, 6, 0.7), spoon=True, under=None):
    """Cup and saucer from above: the saucer's rim and well, a gold line, the cup's rim, the coffee (or tea) with
    the lamp's highlight, the handle, a spoon on the saucer."""
    base, dark, light, rim = china
    sau = F.ell(cx, cy, r * 1.9, r * 1.7)
    F.shadow(sau, sh[0], sh[1], sh[2], under=under)
    _ell_shade(F, cx, cy, r * 1.9, r * 1.7, base, dark, light, key)
    F.fill(F.ell(cx, cy, r * 1.9, r * 1.7) & ~F.ell(cx, cy, r * 1.9 - 1, r * 1.7 - 1), rim)
    F.fill(F.ell(cx, cy, r * 1.55, r * 1.38) & ~F.ell(cx, cy, r * 1.55 - 1, r * 1.38 - 1), gold)
    if spoon:
        sp = F.line([(cx + r * 0.9, cy + r * 1.05), (cx + r * 1.75, cy + r * 0.2)], 0.7)
        F.fill(sp, '#b8bcc4')
        F.fill(F.ell(cx + r * 0.8, cy + r * 1.15, 2.5, 2.0), '#a8acb4')
        F.fill(F.line([(cx + r * 1.0, cy + r * 0.9), (cx + r * 1.6, cy + r * 0.3)], 0.3), '#e8ecf2')
    hd = F.ell(cx + r * 1.12, cy - r * 0.1, r * 0.42, r * 0.32) & ~F.ell(cx + r * 1.12, cy - r * 0.1, r * 0.2, r * 0.12)
    F.shadow(F.ell(cx, cy, r, r * 0.92) | hd, sh[0] * 0.7, sh[1] * 0.7, 0.8)
    F.fill(hd, base)
    F.outline(hd, k=0.7)
    cup = _ell_shade(F, cx, cy, r, r * 0.92, base, dark, light, key)
    F.outline(cup, k=0.7)
    inner = F.ell(cx, cy, r - 2, r * 0.92 - 2)
    F.fill(inner, liquid[0])
    F.fill(inner & ~F.ell(cx + key[0] * 1.2, cy + key[1] * 1.2, r - 2, r * 0.92 - 2), liquid[1])
    F.fill(F.ell(cx + key[0] * r * 0.35, cy + key[1] * r * 0.32, r * 0.22, r * 0.14), liquid[2])
    return sau


def roll_plate(F, cx, cy, r, key=(-1, -1), under=None):
    pl = F.ell(cx, cy, r, r * 0.9)
    F.shadow(pl, 5, 6, 0.72, under=under)
    _ell_shade(F, cx, cy, r, r * 0.9, '#f2eee4', '#d4cebe', '#fdfaf2', key)
    F.fill(F.ell(cx, cy, r * 0.72, r * 0.64) & ~F.ell(cx, cy, r * 0.72 - 1, r * 0.64 - 1), '#c09034')
    F.outline(pl, k=0.72)
    # half a roll, its cut face up, crumbs around
    ro = F.ell(cx - 3, cy - 2, r * 0.42, r * 0.3)
    F.shadow(ro, 3, 3, 0.75)
    F.fill(ro, '#b06a2a')
    F.fill(ro & ~F.ell(cx - 4, cy - 3, r * 0.42, r * 0.3), '#7a4218')
    cut = F.ell(cx - 1, cy - 1, r * 0.3, r * 0.2)
    F.fill(cut, '#e8d4a8')
    F.speckle(cut, 0.18, '#c8b080', seed=int(cx))
    F.outline(ro, k=0.6)
    for k in range(14):
        a = K.hash2(k, 1, int(cx)) * 6.283
        d = r * (0.45 + 0.4 * K.hash2(k, 2, int(cx)))
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.9
        F.fill(F.box(x, y, x + 1 + (k % 2), y + 1), '#c08a4a' if k % 3 else '#8a5424')
    kn = F.line([(cx + r * 0.55, cy + r * 0.7), (cx + r * 1.25, cy - r * 0.25)], 1.0)
    F.shadow(kn, 2, 3, 0.75)
    F.fill(kn, '#c8ccd4')
    F.fill(F.line([(cx + r * 0.55, cy + r * 0.7), (cx + r * 0.78, cy + r * 0.38)], 1.3), '#5a3a22')


def menu_card(F, x, y, w, h, title='SPEISEKARTE', under=None, rot=0.0):
    pts = [(x, y), (x + w, y + rot), (x + w - rot * 0.3, y + h), (x - rot * 0.3, y + h - rot)]
    m = F.poly(pts)
    F.shadow(m, 4, 5, 0.7, under=under)
    F.fill(m, '#ece4d0')
    F.fill(m & F.poly([(x + w * 0.5, y), (x + w, y + rot), (x + w - rot * 0.3, y + h), (x + w * 0.5, y + h)]), '#e2d8c2')
    F.fill(F.line([(x + w * 0.5, y + 1), (x + w * 0.5, y + h - 1)], 0.4), '#c8bca4')
    F.fill(F.poly([(x + 3, y + 3), (x + w - 3, y + 3 + rot), (x + w - 3, y + 4 + rot), (x + 3, y + 4)]), '#8e2018')
    tw = K.VK.vtext(title, 's').shape[1]
    F.fill(F.text(title, int(x + w / 2 - tw / 2), int(y + 7), 's') & m, '#5a1410')
    for k, ly in enumerate(range(int(y + 17), int(y + h - 5), 5)):
        for side in (0, 1):
            x0 = x + 5 + side * (w * 0.5)
            ln = (w * 0.5 - 12) * (0.55 + 0.45 * K.hash2(k, side, 7))
            F.fill(F.box(x0, ly, x0 + ln, ly + 1), '#6a6050')
            F.fill(F.box(x0 + w * 0.5 - 12, ly, x0 + w * 0.5 - 9, ly + 1), '#6a6050')
    F.outline(m, k=0.6)


def carnation_vase(F, cx, cy, under=None):
    v = F.ell(cx, cy, 7, 6)
    F.shadow(v, 6, 7, 0.68, under=under)
    _ell_shade(F, cx, cy, 7, 6, '#9ab0b8', '#6a8088', '#d8e8ee')
    F.outline(v, k=0.55)
    F.fill(F.ell(cx, cy, 4, 3), '#3a5048')
    for (lx, ly, ex, ey) in ((-2, 0, -16, 10), (1, 1, 12, 14), (0, -1, -6, -14)):
        F.fill(F.line([(cx + lx, cy + ly), (cx + ex, cy + ey)], 0.9), '#3a5a2a')
        F.fill(F.line([(cx + ex * 0.6, cy + ey * 0.6), (cx + ex * 0.6 + 4, cy + ey * 0.6 + 2)], 0.8), '#4e7034')
    fl = F.ell(cx - 6, cy - 16, 7, 6)
    F.shadow(fl, 8, 9, 0.72, under=under)
    F.fill(fl, '#b8202a')
    for k in range(18):
        a = k * 2.4
        r = 1.5 + (k % 5)
        x, y = cx - 6 + math.cos(a) * r, cy - 16 + math.sin(a) * r * 0.85
        F.fill(F.box(x, y, x + 1, y + 1), '#e04a4a' if k % 3 else '#7a1018')
    F.outline(fl, col='#5a0a10')


def cruet(F, cx, cy, under=None):
    for k, (dx, cap) in enumerate(((0, '#e8e4dc'), (11, '#3a3a40'))):
        m = F.ell(cx + dx, cy, 4, 4)
        F.shadow(m, 3, 4, 0.7, under=under)
        _ell_shade(F, cx + dx, cy, 4, 4, '#c8ccd4', '#8a9098', '#f2f4f8')
        F.outline(m, k=0.55)
        for (px, py) in ((-1, -1), (1, 0), (0, 1)):
            F.fill(F.box(cx + dx + px, cy + py, cx + dx + px + 1, cy + py + 1), cap)


def ashtray(F, cx, cy, r, glass=True, under=None, butts=1, papirosa=False):
    m = F.ell(cx, cy, r, r * 0.9)
    F.shadow(m, 4, 5, 0.7, under=under)
    if glass:
        _ell_shade(F, cx, cy, r, r * 0.9, '#8a9aa4', '#5a6a74', '#c8d8e0')
        F.fill(F.ell(cx, cy, r * 0.62, r * 0.55), '#4a5a64')
    else:
        _ell_shade(F, cx, cy, r, r * 0.9, '#6a6e72', '#3a3e44', '#9aa0a6')
        F.fill(F.ell(cx, cy, r * 0.78, r * 0.7), '#2e3034')
    F.outline(m, k=0.5)
    F.speckle(F.ell(cx, cy, r * 0.55, r * 0.5), 0.35, '#8a8680', seed=int(cy))
    for b in range(butts):
        a = 0.6 + b * 2.1
        x0, y0 = cx + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2
        x1, y1 = cx + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.2
        cig = F.line([(x0, y0), (x1, y1)], 1.2)
        F.shadow(cig, 2, 3, 0.7)
        F.fill(cig, '#efeae0')
        if papirosa:
            F.fill(F.line([(x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45), (x1, y1)], 1.0), '#d8c8a0')
        else:
            F.fill(F.line([(x0 + (x1 - x0) * 0.72, y0 + (y1 - y0) * 0.72), (x1, y1)], 1.2), '#c87a3a')
        F.fill(F.ell(x0, y0, 1.6, 1.6), '#6a6660')


def napkin(F, x, y, w, under=None):
    pts = [(x, y), (x + w, y + 3), (x + w * 0.45, y + w * 0.62)]
    m = F.poly(pts)
    F.shadow(m, 4, 5, 0.75, under=under)
    F.fill(m, '#f6f2ea')
    F.fill(F.line([(x + 2, y + 1), (x + w * 0.47, y + w * 0.58)], 0.4), '#d8d2c4')
    F.outline(m, k=0.75)


# ================================================================================================= b1 plate
B1_LAMP = (428, 102)
B1_KEY = (1, -1)


def _damask(F, m, base, line, dot):
    F.fill(m, base)
    xx, yy = F.xx.astype(np.int32), F.yy.astype(np.int32)
    lat = ((np.mod(xx + yy, 28) == 0) | (np.mod(xx - yy, 28) == 0)) & ((xx + yy) % 2 == 0)
    F.fill(m & lat, line)
    ros = (np.abs(np.mod(xx, 28) - 14) + np.abs(np.mod(yy, 28) - 0) <= 2) & ((xx + yy) % 2 == 1)
    F.fill(m & ros, dot)


def b1_plate():
    """The dining car table from above: the black window with the Ostbahnhof's lamps and the man from the kiosk
    (his own sprite), the wood and brass sill, the wine-red curtain, the table lamp with its pleated shade, the
    damask cloth with its ironed creases, and the things on it (the book, the card and the hands are sprites)."""
    F = FL.Flat(bg='#000000')
    # the window: black glass; far platform lamps in rows; the lamp's own reflection
    win = F.box(0, 0, 640, 86)
    F.grad(win, 0, 86, '#06070b', '#0e0d14', steps=3)
    for row, (y, n, sp) in enumerate(((52, 7, 92), (64, 9, 72), (74, 11, 58))):
        for k in range(n):
            x = 40 + k * sp + (row * 23) % sp
            F.fill(F.box(x, y, x + 2, y + 1), '#ffd08a' if row < 2 else '#f0a050')
            F.fill(F.box(x - 1, y + 1, x + 3, y + 2) & (((F.xx + F.yy).astype(int) & 1) == 0), '#5a3a1e')
    refl = F.poly([(396, 56), (460, 56), (468, 80), (388, 80)])
    F.fill(refl, '#1c1418')
    F.fill(refl & F.box(0, 76, 640, 80), '#3a2418')
    F.fill(F.box(0, 82, 640, 86), '#16120e')
    # the sill: polished mahogany with a brass rail
    sill = F.box(0, 86, 640, 100)
    F.fill(sill, '#5a2a18')
    F.fill(F.box(0, 86, 640, 88), '#2a120a')
    F.fill(F.box(0, 89, 640, 91), '#c09034')
    F.fill(F.box(0, 89, 640, 90), '#f0cc6a')
    F.fill(F.box(0, 96, 640, 100), '#3a180e')
    for x in range(30, 640, 120):
        F.fill(F.box(x, 88, x + 3, 92), '#8a6420')
    # the curtain at the left, gathered by a tasselled cord
    cur = F.poly([(0, 0), (58, 0), (40, 64), (52, 98), (0, 98)])
    F.fill(cur, '#6e1a18')
    for k, x in enumerate(range(4, 56, 7)):
        F.fill(cur & F.line([(x, 0), (x * 0.7, 64), (x * 0.85, 98)], 1.2), '#4a0e10' if k % 2 else '#8e2a22')
    F.outline(cur, k=0.5, sides='r')
    F.fill(F.ell(40, 66, 5, 4), '#c09034')
    F.fill(F.line([(40, 70), (44, 84)], 1.2), '#c09034')
    # the table: damask cloth, ironed creases, the cloth's hem along the sill
    tab = F.box(0, 100, 640, 360)
    _damask(F, tab, '#dcd5c6', '#e3ddd0', '#e7e2d6')
    for y in (182, 268):
        F.fill(F.box(0, y, 640, y + 1) & tab, '#cfc8b9')
        F.fill(F.box(0, y + 1, 640, y + 2) & tab, '#f2eee6')
    for x in (150, 488):
        F.fill(F.box(x, 100, x + 1, 360) & tab, '#d4cdbf')
        F.fill(F.box(x + 1, 100, x + 2, 360) & tab, '#efebe2')
    F.fill(F.box(0, 100, 640, 102), '#bfb6a6')
    F.fill(F.box(0, 102, 640, 103), '#f6f2ea')
    under = tab
    # the lamp: brass base, stem, pleated shade seen from above, its bulb glowing through the top
    lx, ly = B1_LAMP
    base = F.ell(lx, ly + 6, 15, 11)
    F.shadow(base, -7, 8, 0.7, under=under)
    _ell_shade(F, lx, ly + 6, 15, 11, '#a87828', '#6a4a14', '#e8c060')
    F.outline(base, k=0.5)
    shade_o = F.ell(lx, ly, 34, 27)
    F.shadow(shade_o, -14, 16, 0.78, under=under & ~base)
    F.fill(shade_o, '#e8cc98')
    xx, yy = F.xx - lx, F.yy - ly
    ang = np.arctan2(yy, xx)
    pleat = (np.mod(ang * 18 / math.pi, 2.0) < 1.0)
    F.fill(shade_o & pleat, '#d4b47c')
    F.fill(shade_o & ~F.ell(lx - 3, ly + 3, 34, 27), '#f8e2b0')
    F.fill(shade_o & ~F.ell(lx + 2, ly - 2, 34, 27), '#b08a54')
    F.outline(shade_o, col='#6a4a24')
    top = F.ell(lx, ly, 13, 10)
    F.fill(top, '#fff4cc')
    F.fill(F.ell(lx, ly, 8, 6), '#ffffff')
    F.fill(top & ~F.ell(lx, ly, 12, 9), '#c8a050')
    # light: the lamp's pool in steps on the cloth (inner rings brighter), the far right in the window's cold
    F.pool(tab & ~shade_o & ~base, lx - 20, ly + 50, 470, 300,
           steps=((1.0, 0.98), (0.58, 1.03), (0.3, 1.07)), col='#ffd890')
    far = tab & ~F.ell(lx - 20, ly + 50, 500, 320)
    F.mul(far, 0.88)
    # the things on the table
    cup_saucer(F, 112, 214, 15, ('#2a140a', '#3e2212', '#a8805a'), key=B1_KEY, under=under)
    roll_plate(F, 70, 300, 30, key=B1_KEY, under=under)
    napkin(F, 150, 270, 34, under=under)
    menu_card(F, 500, 120, 72, 52, under=under, rot=4.0)
    carnation_vase(F, 604, 214, under=under)
    cruet(F, 364, 106, under=under)
    ashtray(F, 586, 290, 16, glass=True, under=under, butts=1)
    # the window's cold light on the far left of the cloth (a strip under the glass)
    F.tint(F.box(0, 100, 300, 116) & tab, '#9aa8c8', 0.12)
    return F.opaque()


def reflection_rgba():
    """The man from the kiosk reflected in the black window: the cast stream's stapo_civil (hat, leather coat,
    his newspaper up) on the rig, mirrored, posterised dim and warm (the lamp behind the glass)."""
    import env_c4p2_cine_rig as R
    CH, CB, A, CC = K.rig()
    spec, used = K.spec_of('stapo_civil', 'clerk')
    frames = R.render_set(spec, A.idle_side(spec.style)[:1], [], 32)
    rg = frames[0][0][:, ::-1]
    a = rg[..., 3] > 0
    lum = rg[..., :3].astype(np.float32).mean(-1) / 255.0
    out = np.zeros_like(rg)
    lv = np.clip(np.floor(lum * 4) / 4, 0, 1)
    out[..., 0] = (lv * 110 + 34).astype(np.uint8)
    out[..., 1] = (lv * 76 + 24).astype(np.uint8)
    out[..., 2] = (lv * 52 + 22).astype(np.uint8)
    out[..., 3] = np.where(a, 255, 0)
    return out


# ================================================================================================= hands (b1 / b3)
SH_B = (8, 10)        # cast shadow offset of a hand lying on the table, Berlin lamp upper left
SH_K = (-8, 10)       # Karsk lamp upper right


def _tip(cv_pose, finger='index'):
    pts, radii, acc = HD.finger_chain(cv_pose, finger)
    (ax, ay), (bx, by) = pts[2], pts[3]
    L_ = math.hypot(bx - ax, by - ay) + 1e-6
    return (bx + (bx - ax) / L_ * radii[3] * 0.6, by + (by - ay) / L_ * radii[3] * 0.6)


def _right_hand_from_lower_right(scene, sleeve_mat, sleeve_col, cuff_mat, cuff_col, skin, curls, lift, extra=None,
                                 cuff_kw=None, sleeve_kw=None, hand_kw=None, key=(-0.6, 0.6, 0.55), shadow=SH_B,
                                 ang=-58.0, s=7.0):
    """A right hand reaching up-left from the lower right of the frame (Konrad in b1, Alexei in b3): canvas
    520 x 460, the index fingertip near (62, 70).  Returns (rgba, tip)."""
    cv = HD.Canvas(520, 460, scene)
    HD.mats_common(cv, skin=skin)
    cv.mat(sleeve_mat, sleeve_col, **(extra or {}))
    cv.mat(cuff_mat, cuff_col, **({'texture': 'knit'} if cuff_mat == 'knit' else {}))
    a = math.radians(ang)
    d = (math.sin(a), -math.cos(a))
    tip0 = (62.0, 70.0)
    wrist = (tip0[0] - d[0] * 18.2 * s, tip0[1] - d[1] * 18.2 * s)
    cuff_w = 9.4 * s
    far = (wrist[0] - d[0] * 64 * s, wrist[1] - d[1] * 64 * s)
    full, dv = HD.sleeve(cv, (wrist[0] - d[0] * 1.6 * s, wrist[1] - d[1] * 1.6 * s), far, 12.4 * s, 14.5 * s,
                         sleeve_mat, **(sleeve_kw or {}))
    HD.cuff_band(cv, (wrist[0] - d[0] * 1.9 * s, wrist[1] - d[1] * 1.9 * s), (d[0], d[1], dv[2], dv[3]), cuff_w,
                 2.4 * s, cuff_mat, **(cuff_kw or {}))
    p = HD.HandPose(wrist=(wrist[0] + d[0] * 0.4 * s, wrist[1] + d[1] * 0.4 * s), ang=ang, s=s, side='R',
                    curl=curls, thumb=(-12.0, 0.3), spread=-5.0)
    HD.draw_hand(cv, p, **(hand_kw or {}))
    sh = (shadow[0] * (1 + lift), shadow[1] * (1 + lift))
    rgba = cv.render(key=key, shadow=sh)
    return rgba, _tip(p)


def konrad_hand(f):
    """b1: Konrad's bare right hand, navy wool sleeve, the white shirt cuff: f 0 the fingertips push the card,
    f 1 lifted a little and relaxing (withdrawing)."""
    curls = ((0.04, 0.06, 0.3, 0.42), (0.18, 0.2, 0.36, 0.46))[f]
    return _right_hand_from_lower_right('berlin', 'wool', '#28324c', 'shirt', '#dcd8d0', '#c98c6a', curls,
                                        (0.0, 0.6)[f], sleeve_kw=dict(seed=3, seam=0.5))


def alexei_hand(f):
    """b3: Alexei's right hand where Konrad's lay: the quilted telogreika sleeve, the knitted cuff, a worn hand,
    grime in the nails, a plaster on the index; f 0 resting on the German half, f 1 pressing along it."""
    curls = ((0.06, 0.1, 0.42, 0.55), (0.12, 0.14, 0.48, 0.6))[f]
    return _right_hand_from_lower_right('karsk', 'quilt', '#4e5442', 'knit', '#3e3a36', '#b6805e', curls, 0.0,
                                        sleeve_kw=dict(seed=7, quilt=True), cuff_kw=dict(ribs=3),
                                        hand_kw=dict(grime=True, plaster=True), key=(0.6, 0.6, 0.55),
                                        shadow=SH_K, ang=-56.0)


def ekdahl_glove(f, scene='berlin'):
    """Ekdahl's grey-gloved left hand from the upper left (his tweed sleeve): f 0 resting on page 212, f 1
    reaching over to the right half, f 2 the fingers curled under its fore-edge, lifting.  Canvas 520 x 460, the
    tip (between the index and the middle fingertip, or the curled fingers' front for f 2) near (430, 360)."""
    s = 7.0
    cv = HD.Canvas(520, 460, scene)
    HD.mats_common(cv)
    cv.mat('tweed', '#5e4c3a')
    cv.mat('glove', HD.KID_GLOVE, glossy=True)          # round 11c: warm grey kid leather (env_c4p2_cine_hands)
    ang, curls, under = {0: (118.0, (0.28, 0.3, 0.36, 0.44), (0, 0, 0, 0)),
                         1: (104.0, (0.12, 0.14, 0.2, 0.3), (0, 0, 0, 0)),
                         2: (98.0, (0.62, 0.62, 0.66, 0.7), (2, 2, 2, 2))}[f]
    a = math.radians(ang)
    d = (math.sin(a), -math.cos(a))
    tip0 = (430.0, 360.0)
    reach = 18.2 if f < 2 else 13.4
    wrist = (tip0[0] - d[0] * reach * s, tip0[1] - d[1] * reach * s)
    far = (wrist[0] - d[0] * 64 * s, wrist[1] - d[1] * 64 * s)
    full, dv = HD.sleeve(cv, (wrist[0] - d[0] * 2.4 * s, wrist[1] - d[1] * 2.4 * s), far, 12.8 * s, 14.6 * s,
                         'tweed', seed=5, herring=True)
    HD.cuff_band(cv, (wrist[0] - d[0] * 2.6 * s, wrist[1] - d[1] * 2.6 * s), (d[0], d[1], dv[2], dv[3]), 9.6 * s,
                 2.8 * s, 'glove')
    p = HD.HandPose(wrist=wrist, ang=ang, s=s, side='L', glove=True, curl=curls, thumb=(-6.0, 0.35), spread=-4.0,
                    fold_under=under)
    HD.draw_hand(cv, p, glove_mat='glove')
    key = (-0.6, 0.6, 0.55) if scene == 'berlin' else (0.6, 0.6, 0.55)
    sh = SH_B if scene == 'berlin' else SH_K
    lift = 0.9 if f == 2 else 0.0
    rgba = cv.render(key=key, shadow=(sh[0] * (1 + lift), sh[1] * (1 + lift)))
    if f < 2:
        t1, t2 = _tip(p, 'index'), _tip(p, 'middle')
        tip = ((t1[0] + t2[0]) / 2, (t1[1] + t2[1]) / 2)
    else:
        pts, radii, acc = HD.finger_chain(p, 'middle')
        tip = pts[2]
    return rgba, tip


# ================================================================================================= b3b plate
B3_LAMP = (560, 40)
B3_KEY = (1, -1)


def _oilcloth(F, m):
    """Soviet canteen oilcloth: a cream ground printed with small red roses and green leaves in a half-drop
    repeat, a blue scroll between them; rubbed pale where the elbows go, a burn, a knife's nicks."""
    F.fill(m, '#d8ccac')
    xx, yy = F.xx.astype(np.int32), F.yy.astype(np.int32)
    rep_x, rep_y = 46, 40
    col = np.floor_divide(xx, rep_x)
    ux = np.mod(xx, rep_x)
    uy = np.mod(yy + np.where(np.mod(col, 2) == 0, 0, rep_y // 2), rep_y)
    rose = (ux - 14) ** 2 + (uy - 12) ** 2 <= 20
    rose_d = ((ux - 14) ** 2 + (uy - 12) ** 2 <= 6) | ((ux - 15) ** 2 + (uy - 10) ** 2 <= 2)
    leaf1 = ((ux - 20) ** 2 / 9 + (uy - 17) ** 2 / 3 <= 1)
    leaf2 = ((ux - 8) ** 2 / 3 + (uy - 18) ** 2 / 8 <= 1)
    scroll = (np.abs((uy - 30) - 3 * np.sin(ux * 0.27)) < 0.8) & (ux > 24) & (ux < 44)
    dots = ((ux - 34) ** 2 + (uy - 8) ** 2 <= 2) | ((ux - 38) ** 2 + (uy - 12) ** 2 <= 1)
    F.fill(m & rose, '#b03a2c')
    F.fill(m & rose_d, '#7a1e18')
    F.fill(m & rose & (ux < 13) & (uy < 11), '#d86a4a')
    F.fill(m & (leaf1 | leaf2), '#4e6e3a')
    F.fill(m & (leaf1 | leaf2) & (uy < 17), '#6e8e4a')
    F.fill(m & scroll, '#4a6688')
    F.fill(m & dots, '#4a6688')
    rub = m & F.ell(150, 330, 140, 60) & (K.hash2(xx, yy, 77) > 0.35)
    F.tint(rub, '#e2d8bc', 0.55)
    rub2 = m & F.ell(520, 320, 120, 50) & (K.hash2(xx, yy, 78) > 0.45)
    F.tint(rub2, '#e2d8bc', 0.45)
    burn = F.ell(468, 168, 3, 2)
    F.fill(m & F.ell(468, 168, 5, 4) & ~burn, '#8a6a3a')
    F.fill(m & burn, '#3a2410')
    for k in range(5):
        x0 = 110 + k * 9
        F.fill(m & F.line([(x0, 128 + k * 3), (x0 + 12, 124 + k * 3)], 0.4), '#a89a78')


def tea_glass(F, cx, cy, r, under=None, key=B3_KEY, lemon=True):
    """A tea glass in its nickel-silver holder from above: the holder's rim ring with its pierced band, the
    glass rim, the amber tea, a lemon slice, the spoon standing in it, the handle."""
    hd = F.ell(cx - r * 1.2, cy + r * 0.1, r * 0.55, r * 0.45) & ~F.ell(cx - r * 1.2, cy + r * 0.1, r * 0.3, r * 0.22)
    ring = F.ell(cx, cy, r + 3, r * 0.92 + 3)
    F.shadow(ring | hd, 8 * key[0] * -1 if key[0] < 0 else -8, 10, 0.68, under=under)
    F.fill(hd, '#9aa0a8')
    F.outline(hd, k=0.55)
    _ell_shade(F, cx, cy, r + 3, r * 0.92 + 3, '#a8aeb6', '#6a7078', '#e2e8ee', key=(-key[0], key[1]))
    band = ring & ~F.ell(cx, cy, r + 1, r * 0.92 + 1)
    F.fill(band & ((np.mod(np.arctan2(F.yy - cy, F.xx - cx) * 6, 1.0) < 0.5)), '#5a6068')
    F.outline(ring, k=0.5)
    gl = F.ell(cx, cy, r, r * 0.92)
    F.fill(gl, '#c8d0d0')
    tea = F.ell(cx, cy, r - 1.5, r * 0.92 - 1.5)
    F.fill(tea, '#a0521a')
    F.fill(tea & ~F.ell(cx - key[0] * 1.5, cy - key[1] * 1.5, r - 1.5, r * 0.92 - 1.5), '#6e3410')
    F.fill(F.ell(cx + key[0] * r * 0.35, cy + key[1] * r * 0.3, r * 0.2, r * 0.12), '#e8a860')
    if lemon:
        lm = F.ell(cx - r * 0.3, cy + r * 0.25, r * 0.38, r * 0.34)
        F.fill(lm, '#f0d870')
        F.fill(lm & ~F.ell(cx - r * 0.3, cy + r * 0.25, r * 0.38 - 1, r * 0.34 - 1), '#d8b040')
        for k in range(6):
            a = k * math.pi / 3
            F.fill(F.line([(cx - r * 0.3, cy + r * 0.25), (cx - r * 0.3 + math.cos(a) * r * 0.3,
                                                          cy + r * 0.25 + math.sin(a) * r * 0.27)], 0.3) & lm, '#e8c858')
    sp = F.line([(cx + r * 0.3, cy - r * 0.2), (cx + r * 1.6, cy - r * 1.3)], 0.8)
    F.shadow(sp, -5, 6, 0.72, under=under)
    F.fill(sp, '#c0c6ce')
    F.fill(F.ell(cx + r * 1.65, cy - r * 1.35, 1.6, 1.4), '#a8aeb6')


def sugar_bowl(F, cx, cy, r, under=None):
    m = F.ell(cx, cy, r, r * 0.92)
    F.shadow(m, -6, 7, 0.68, under=under)
    _ell_shade(F, cx, cy, r, r * 0.92, '#e8ecef', '#b8c0c8', '#ffffff', key=(1, -1))
    F.fill(m & ~F.ell(cx, cy, r - 1.5, r * 0.92 - 1.5), '#3a5a9a')
    F.outline(m, k=0.55)
    F.fill(F.ell(cx, cy, r - 3, r * 0.92 - 3), '#c8ccd0')
    for k in range(9):
        x = cx - r * 0.5 + (k % 3) * r * 0.36 + (k // 3) * 1.5
        y = cy - r * 0.45 + (k // 3) * r * 0.34
        c = F.box(x, y, x + 4, y + 4)
        F.fill(c, '#f6f6f2')
        F.fill(F.box(x + 3, y, x + 4, y + 4) | F.box(x, y + 3, x + 4, y + 4), '#c8ccd0')


def bread_plate(F, cx, cy, r, under=None):
    pl = F.ell(cx, cy, r, r * 0.88)
    F.shadow(pl, -6, 7, 0.68, under=under)
    _ell_shade(F, cx, cy, r, r * 0.88, '#d8d4c8', '#a8a294', '#f0ece2', key=(1, -1))
    F.outline(pl, k=0.55)
    F.fill(pl & ~F.ell(cx, cy, r - 2, r * 0.88 - 2), '#4a6a9a')
    for k in range(3):
        x0, y0 = cx - r * 0.55 + k * r * 0.34, cy - r * 0.5 + k * 3
        sl = F.poly([(x0, y0), (x0 + r * 0.42, y0 - 2), (x0 + r * 0.5, y0 + r * 0.9), (x0 + 3, y0 + r * 0.95)])
        F.shadow(sl, -2, 2, 0.7)
        F.fill(sl, '#4a2e1c')
        F.fill(sl & F.poly([(x0 + 2, y0 + 2), (x0 + r * 0.4, y0), (x0 + r * 0.46, y0 + r * 0.85),
                            (x0 + 4, y0 + r * 0.9)]), '#6a4228')
        F.speckle(sl, 0.12, '#8a5a38', seed=k + 31)
        F.outline(sl, col='#22140c')


def newspaper(F, x, y, w, h, under=None):
    m = F.poly([(x, y), (x + w, y - 6), (x + w + 4, y + h - 6), (x + 4, y + h)])
    F.shadow(m, -5, 6, 0.7, under=under)
    F.fill(m, '#cfc8b4')
    tw = K.VK.vtext('СИГНАЛ', 'm').shape[1]
    F.fill(F.text('СИГНАЛ', int(x + 8), int(y + 4), 'm') & m, '#2a2620')
    F.fill(F.box(x + 6, y + 13, x + w - 6, y + 14) & m, '#4a463c')
    for c in range(3):
        for ly in range(int(y + 18), int(y + h - 4), 3):
            x0 = x + 6 + c * (w - 12) / 3 + (ly - y) * 0.09
            F.fill(F.box(x0, ly - c * 0, x0 + (w - 12) / 3 - 4, ly + 1) & m, '#7a7468')
    F.fill(F.box(x + w * 0.62, y + 18, x + w - 8, y + 34) & m, '#5a564c')
    F.outline(m, k=0.65)


def matchbox(F, x, y, under=None):
    m = F.box(x, y, x + 22, y + 15)
    F.shadow(m, -4, 5, 0.7, under=under)
    F.fill(m, '#c8a040')
    F.fill(F.box(x + 2, y + 2, x + 20, y + 13), '#d8c890')
    F.fill(F.box(x + 4, y + 4, x + 18, y + 6), '#8e2018')
    F.fill(F.box(x + 4, y + 8, x + 12, y + 11), '#2a3a5a')
    F.outline(m, k=0.55)
    for k in range(3):
        F.fill(F.line([(x + 26 + k * 3, y + 4 + k * 2), (x + 34 + k * 3, y + 9 + k * 2)], 0.5), '#e8d8a8')
        F.fill(F.box(x + 33 + k * 3, y + 8 + k * 2, x + 35 + k * 3, y + 10 + k * 2), '#3a2a1a')


def b3_plate(book_rgba):
    """The canteen table from above: beyond its far edge the canteen floor (worn planks, felt boots and the hem
    of a quilted coat at the next table, a dropped papirosa); the oilcloth and its things; the book is
    composited in by build()."""
    F = FL.Flat(bg='#000000')
    floor = F.box(0, 0, 640, 84)
    F.fill(floor, '#2e2016')
    for k, y in enumerate(range(0, 84, 9)):
        F.fill(F.box(0, y, 640, y + 1), '#1a120c')
        F.fill(F.box(0, y + 1, 640, y + 2), '#3e2c1e')
        for x in range((k * 97) % 160, 640, 160):
            F.fill(F.box(x, y + 1, x + 1, y + 9), '#1a120c')
    F.speckle(floor, 0.06, '#4a3626', seed=91)
    # felt boots and a coat hem at the next table (top right); a bench leg; a papirosa end on the floor
    for (bx, by) in ((452, 18), (480, 24)):
        boot = F.ell(bx, by, 11, 16)
        F.shadow(boot, -5, 6, 0.6)
        F.fill(boot, '#4a4440')
        F.fill(boot & ~F.ell(bx - 2, by - 2, 11, 16), '#2e2a28')
        F.fill(F.ell(bx, by + 10, 9, 5), '#2a2420')
        F.outline(boot, k=0.5)
    hem = F.poly([(420, 0), (520, 0), (514, 8), (426, 10)])
    F.fill(hem, '#3a4232')
    F.fill(hem & F.box(0, 6, 640, 10), '#2a3024')
    F.outline(hem, k=0.5, sides='b')
    leg = F.box(96, 0, 108, 70)
    F.fill(leg, '#4a3020')
    F.fill(F.box(96, 0, 99, 70), '#6a4630')
    F.outline(leg, k=0.5)
    F.fill(F.line([(230, 50), (240, 46)], 1.0), '#e8e2d4')
    F.fill(F.box(229, 50, 231, 52), '#6a6660')
    F.mul(floor, 0.8)
    # the table: its aluminium edge strip, the oilcloth
    tab = F.box(0, 84, 640, 360)
    _oilcloth(F, tab)
    edge_ = F.box(0, 84, 640, 90)
    F.fill(edge_, '#8a9096')
    F.fill(F.box(0, 84, 640, 85), '#c8ced4')
    F.fill(F.box(0, 89, 640, 90), '#3a3e42')
    under = tab & ~edge_
    tea_glass(F, 206, 306, 15, under=under)
    tea_glass(F, 548, 150, 15, under=under, lemon=False)
    sugar_bowl(F, 600, 248, 18, under=under)
    bread_plate(F, 84, 296, 34, under=under)
    ashtray(F, 470, 112, 14, glass=False, under=under, butts=3, papirosa=True)
    newspaper(F, 506, 268, 96, 62, under=under)
    matchbox(F, 168, 116, under=under)
    for k in range(18):
        x = 30 + K.hash2(k, 5, 3) * 580
        y = 100 + K.hash2(k, 6, 3) * 230
        F.fill(F.box(x, y, x + 1 + (k % 2), y + 1) & under, '#3a2416' if k % 2 else '#6a4426')
    # the lamp above the right: its pool in steps; the far left in the cold of the window
    F.pool(tab, B3_LAMP[0] - 80, B3_LAMP[1] + 160, 560, 330, steps=((1.0, 1.0), (0.62, 1.05), (0.34, 1.1)),
           col='#ffb860')
    F.mul(tab & ~F.ell(B3_LAMP[0] - 80, B3_LAMP[1] + 160, 600, 360), 0.88)
    out = F.opaque()
    K.blit(out, book_rgba[..., :], 0, 0) if book_rgba is not None else None
    return out


# ================================================================================================= b2 / b3a: the profile
MACRO = (30.0, 22.0, 14.0, 8.0, 3.0, 0.0)   # the upper half's angle per frame (b2 closes it, b3a opens it)
M_HINGE = (118.0, 246.0)                     # the spine's hinge: the lower page block's top at the spine
M_LEN = 404.0                                # spine -> fore-edge (px, 4 px per mm)
M_PAGES = 24.0                               # a half's page block
M_BOARD = 7.0                                # a board (the dark red cloth over grey board)
M_TABLE = M_HINGE[1] + M_PAGES + M_BOARD     # 277: the lower board lies on the table here
CARD_OUT = 30.0                              # the card half's corner out of the fore-edge


def _rot(px, py, th):
    """A point given relative to the hinge (dx, dy; dy < 0 above) of the UPPER half, turned up by th degrees."""
    a = math.radians(th)
    return (M_HINGE[0] + px * math.cos(a) + py * math.sin(a), M_HINGE[1] - px * math.sin(a) + py * math.cos(a))


def _edge_lines(F, m, x0, y0, x1, y1, th, seed, card_y=None):
    """A page block's head edge: fine page lines (2 px pitch) following the block's angle, the signatures as
    darker lines, the sprinkled red edge."""
    a = math.radians(th)
    # coordinate across the block (perpendicular to its length)
    across = -(F.xx - M_HINGE[0]) * math.sin(-a) + (F.yy - M_HINGE[1]) * math.cos(-a)
    along = (F.xx - M_HINGE[0]) * math.cos(-a) + (F.yy - M_HINGE[1]) * math.sin(-a)
    q = np.floor(across)
    F.fill(m, '#e6dabd')
    F.fill(m & (np.mod(q, 2) == 0), '#d2c4a2')
    F.fill(m & (np.mod(q, 8) == 3), '#b4a482')
    wav = K.hash2(np.floor(along / 23).astype(np.int64), q.astype(np.int64), seed) > 0.86
    F.fill(m & wav, '#c2b290')
    spr = m & (K.hash2(F.xx.astype(np.int64), F.yy.astype(np.int64), seed + 5) > 0.965)
    F.fill(spr, '#a8382a')
    F.fill(m & (K.hash2(F.xx.astype(np.int64), F.yy.astype(np.int64), seed + 6) > 0.99), '#7a2018')


def book_profile(th, card=True):
    """The guidebook in profile at angle th (0 = shut): RGBA 640 x 360, transparent around it.  The lower half
    lies on the table; the upper half turns about the spine's hinge; the rounded spine joins the boards; the
    headband shows at the spine; the card's corner sticks out between the pages at the fore-edge."""
    F = FL.Flat(bg='#000000')
    hx_, hy_ = M_HINGE
    # lower half: page block and board
    lp = F.box(hx_, hy_, hx_ + M_LEN, hy_ + M_PAGES)
    lb = F.poly([(hx_ - 6, hy_ + M_PAGES), (hx_ + M_LEN + 3, hy_ + M_PAGES), (hx_ + M_LEN + 3, M_TABLE),
                 (hx_ - 6, M_TABLE)])
    # upper half: the block is the region dy in [-M_PAGES, 0] when shut, the board above it
    def up_poly(d0, d1, x0=0.0, x1=M_LEN):
        return F.poly([_rot(x0, d0, th), _rot(x1, d0, th), _rot(x1, d1, th), _rot(x0, d1, th)])
    gap = 0.0 if th <= 0.01 else 0.0
    up = up_poly(-M_PAGES - gap, -gap)
    ub = up_poly(-M_PAGES - M_BOARD, -M_PAGES, -6.0, M_LEN + 3.0)
    # the spine: a rounded back from the lower board's outer corner to the upper board's outer corner
    p_low = (hx_ - 6, M_TABLE)
    p_up = _rot(-6.0, -M_PAGES - M_BOARD, th)
    cx_ = (p_low[0] + p_up[0]) / 2.0 - 10.0
    cy_ = (p_low[1] + p_up[1]) / 2.0
    ry_ = abs(p_low[1] - p_up[1]) / 2.0 + 1.0
    sp = F.ell(cx_ + 6, cy_, 16, ry_) & (F.xx < hx_ + 2)
    alpha = lp | lb | up | ub | sp
    # wedge between the halves (when open): the inside, dark, with the pages' faces as a light line
    if th > 0.01:
        wedge = F.poly([(hx_, hy_), (hx_ + M_LEN, hy_), _rot(M_LEN, 0.0, th)])
        F.fill(wedge, '#1a120e')
        F.fill(wedge & F.line([(hx_, hy_), (hx_ + M_LEN, hy_)], 0.6), '#efe6d0')
        F.fill(wedge & F.line([(hx_, hy_), _rot(M_LEN, 0.0, th)], 0.6), '#c8bca0')
        F.grad(wedge & (F.xx > hx_ + M_LEN * 0.55), hx_ + M_LEN * 0.55, hx_ + M_LEN, '#1a120e', '#3a2a1e',
               steps=3, axis='x')
        alpha |= wedge
    # board cloth: dark red, a lighter worn corner, the grey board showing at the corners; the top lit edge
    for b, top_lit in ((lb, False), (ub, True)):
        F.fill(b, '#5e1c16')
        F.fill(b & FL.edge(b, 't'), '#8e3426')
        F.fill(b & FL.edge(b, 'b'), '#2e0c0a')
    F.fill(lb & (F.xx > hx_ + M_LEN - 6), '#7a5a4a')
    F.fill(ub & F.ell(*_rot(M_LEN, -M_PAGES - M_BOARD / 2, th), 6, 4), '#7a5a4a')
    # page blocks
    _edge_lines(F, lp, 0, 0, 0, 0, 0.0, 11)
    _edge_lines(F, up, 0, 0, 0, 0, th, 13)
    F.outline(lp, k=0.62, sides='b')
    F.outline(up, k=0.62, sides='t')
    # spine cloth and headband
    F.fill(sp & ~(lp | up | lb | ub), '#4a1410')
    F.fill(sp & FL.edge(sp, 'l'), '#7e2a20')
    hb = F.ell(hx_ - 2, (hy_ + _rot(0.0, 0.0, th)[1]) / 2.0, 4, max(3.0, abs(hy_ - _rot(0, -M_PAGES, th)[1]) / 2.0))
    F.fill(hb & (np.mod(F.yy.astype(np.int32), 3) == 0), '#e8e0d0')
    F.fill(hb & (np.mod(F.yy.astype(np.int32), 3) != 0), '#a02a20')
    alpha |= hb
    # the card half's corner: a thin cream slab between the blocks at the fore-edge, its red rule
    if card:
        y_c = hy_ - 1 if th <= 0.01 else hy_ - 1
        cm = F.poly([(hx_ + M_LEN - 40, y_c - 2), (hx_ + M_LEN + CARD_OUT, y_c - 3),
                     (hx_ + M_LEN + CARD_OUT + 1, y_c + 1), (hx_ + M_LEN - 40, y_c + 1)])
        F.fill(cm, '#f4ead2')
        F.fill(cm & F.box(hx_ + M_LEN + CARD_OUT - 1, 0, 640, 360), '#c8bca0')
        F.fill(cm & F.box(hx_ + M_LEN + 4, y_c - 3, hx_ + M_LEN + 16, y_c - 2), '#c84a3a')
        F.fill(cm & F.box(hx_ + M_LEN + 4, y_c - 1, hx_ + M_LEN + 26, y_c), '#9ab0c8')
        F.fill(cm & FL.edge(cm, 'b'), '#a89a80')
        alpha |= cm
    # the outline of the whole book
    out = F.rgba(alpha)
    a = out[..., 3] > 0
    e = FL.edge(a)
    out[e, :3] = (out[e, :3].astype(np.float32) * 0.45).astype(np.uint8)
    return out


def macro_edge(th):
    """Where the glove's fingertips lift the upper board: its fore-edge, under the board (b3a)."""
    x, y = _rot(M_LEN + 2.0, -2.0, th)
    return [int(round(x)), int(round(y))]


def _persp(F, m, horizon, near_y, cx, k, fn):
    """Paint a horizontal plane in perspective under mask m: screen row y maps to depth k / (y - horizon), x to
    u = (x - cx) * depth; fn(u, v) -> (h, w) colour array in sRGB floats for the texture's coordinates."""
    dy = np.maximum(F.yy - horizon, 0.5)
    u = (F.xx - cx) * 60.0 / dy
    v = k * 60.0 / dy / 6.0
    col = fn(u, v)
    F.rgb[m] = col[m]
    F.a |= m


def _tex_damask(u, v):
    base = np.empty(u.shape + (3,), np.float32)
    base[...] = FL.hx('#d8d1c2')
    ui, vi = np.floor(u).astype(np.int64), np.floor(v * 6.0).astype(np.int64)
    lat = (np.mod(ui + vi * 3, 28) < 2) | (np.mod(ui - vi * 3, 28) < 2)
    base[lat] = FL.hx('#e6e0d4')
    crease = np.mod(vi, 40) == 0
    base[crease] = FL.hx('#c4bcac')
    return base


def _tex_oilcloth(u, v):
    base = np.empty(u.shape + (3,), np.float32)
    base[...] = FL.hx('#d2c6a6')
    uu = np.mod(u, 46.0)
    vv = np.mod(v * 6.0, 40.0)
    rose = (uu - 14) ** 2 + ((vv - 12) * 1.0) ** 2 <= 20
    leaf = (uu - 20) ** 2 / 9 + (vv - 17) ** 2 / 3 <= 1
    scroll = (np.abs((vv - 30) - 3 * np.sin(uu * 0.27)) < 1.0) & (uu > 24) & (uu < 44)
    base[rose] = FL.hx('#a8382a')
    base[leaf] = FL.hx('#4e6e3a')
    base[scroll] = FL.hx('#4a6688')
    return base


def macro_bg(city):
    """Behind the book at table height.  berlin: the far side of the dining car table, the black window with a
    reflected lamp and the station's lamps, the curtain, the table lamp at the right on the cloth.  karsk: the
    canteen -- green oil paint below, whitewash above, a frosted window with the depot's sodium glow, a radiator,
    a tea glass in its holder at the far edge.  Both: the near table in perspective below the book."""
    F = FL.Flat(bg='#000000')
    horizon = 222
    if city == 'berlin':
        wall = F.box(0, 0, 640, horizon)
        F.grad(wall, 0, horizon, '#0a080c', '#16101a', steps=4)
        glass = F.box(0, 40, 640, 168)
        F.fill(glass, '#07080c')
        for k in range(12):
            x = 30 + k * 54 + (k * 17) % 23
            y = 70 + (k * 29) % 50
            F.fill(F.box(x, y, x + 2, y + 2), '#f0b060')
            F.fill(F.box(x - 1, y + 2, x + 3, y + 3) & (((F.xx + F.yy).astype(int) & 1) == 0), '#5a3418')
        rl = F.poly([(410, 92), (470, 92), (480, 126), (400, 126)])
        F.fill(rl, '#2a1a14')
        F.fill(rl & F.box(0, 120, 640, 126), '#4a2c1a')
        F.fill(F.box(0, 168, 640, 182), '#4a2214')
        F.fill(F.box(0, 168, 640, 170), '#7a3c22')
        F.fill(F.box(0, 174, 640, 176), '#c09034')
        F.fill(F.box(0, 174, 640, 175), '#f0cc6a')
        F.fill(F.box(0, 182, 640, horizon), '#2a1410')
        cur = F.poly([(0, 30), (70, 30), (54, 140), (76, 182), (0, 182)])
        F.fill(cur, '#5e1616')
        for k, x in enumerate(range(6, 72, 9)):
            F.fill(cur & F.line([(x, 30), (x * 0.75, 140), (x * 1.0, 182)], 1.5), '#3a0a0c' if k % 2 else '#7e2420')
        F.outline(cur, k=0.5, sides='r')
        # the table lamp on the far edge at the right: brass foot, stem, the pleated shade glowing
        lx = 532
        F.fill(F.ell(lx, horizon - 2, 22, 4), '#6a4a14')
        F.fill(F.ell(lx, horizon - 3, 20, 3), '#a87828')
        F.fill(F.box(lx - 2, horizon - 64, lx + 2, horizon - 3), '#8a6420')
        F.fill(F.box(lx - 2, horizon - 64, lx - 1, horizon - 3), '#e8c060')
        shd = F.poly([(lx - 22, horizon - 108), (lx + 22, horizon - 108), (lx + 36, horizon - 62),
                      (lx - 36, horizon - 62)])
        F.fill(shd, '#f0d098')
        for k in range(-5, 6):
            F.fill(shd & F.line([(lx + k * 4, horizon - 108), (lx + k * 6.5, horizon - 62)], 0.5), '#d8b478')
        F.fill(shd & F.box(0, horizon - 72, 640, horizon - 62), '#fff0c4')
        F.outline(shd, col='#8a6430')
        F.pool(wall & ~shd, lx, horizon - 76, 96, 70, steps=((1.0, 1.3), (0.55, 1.7)), col='#ffc070')
        tab_far = F.box(0, horizon, 640, 360)
        _persp(F, tab_far, horizon - 30, 360, 320, 260.0, _tex_damask)
        F.fill(F.box(0, horizon, 640, horizon + 1), '#8a8070')
        F.pool(tab_far, lx, horizon, 420, 160, steps=((1.0, 1.0), (0.6, 1.06), (0.3, 1.12)), col='#ffd890')
    else:
        wall = F.box(0, 0, 640, horizon)
        F.fill(wall, '#c8c4b4')
        F.fill(F.box(0, 120, 640, horizon), '#3e5a46')
        F.fill(F.box(0, 118, 640, 120), '#7a2a20')
        F.speckle(F.box(0, 0, 640, 118), 0.04, '#b0ac9c', seed=33)
        F.speckle(F.box(0, 120, 640, horizon), 0.05, '#2e4636', seed=34)
        win = F.box(380, 10, 560, 112)
        F.fill(win, '#2a1c14')
        pane = F.box(388, 18, 552, 104)
        F.fill(pane, '#e08a3a')
        F.pool(pane, 470, 60, 120, 70, steps=((1.0, 0.75), (0.6, 0.9), (0.3, 1.1)), col='#ffb050')
        ang_ = np.arctan2(F.yy - 62, F.xx - 470)
        fern = np.abs(np.sin(ang_ * 9 + np.hypot(F.xx - 470, F.yy - 62) * 0.35)) > 0.7
        F.fill(pane & ~F.ell(470, 62, 70, 38) & fern, '#f4e4cc')
        F.fill(pane & ~F.ell(470, 62, 84, 48), '#fbf0e0')
        F.fill(F.box(468, 18, 472, 104) | F.box(388, 58, 552, 62), '#2a1c14')
        F.outline(win, k=0.5)
        F.fill(F.box(370, 110, 570, 116), '#d8d4c4')
        F.fill(F.box(370, 115, 570, 116), '#8a8676')
        rad = F.box(400, 132, 540, 186)
        F.fill(rad, '#c8c4b8')
        for x in range(404, 540, 8):
            F.fill(F.box(x, 134, x + 5, 184), '#e0dcd0')
            F.fill(F.box(x + 5, 134, x + 6, 184), '#8a8478')
        F.outline(rad, k=0.55)
        F.pool(wall & ~win, 470, 64, 200, 110, steps=((1.0, 1.05), (0.6, 1.1)), col='#ffb860')
        tab_far = F.box(0, horizon, 640, 360)
        _persp(F, tab_far, horizon - 30, 360, 320, 260.0, _tex_oilcloth)
        F.fill(F.box(0, horizon, 640, horizon + 1), '#7a7058')
        # a tea glass in its holder at the far edge, seen from the side
        gx, gy = 150, horizon
        hold = F.poly([(gx - 13, gy - 30), (gx + 13, gy - 30), (gx + 11, gy - 2), (gx - 11, gy - 2)])
        glass_ = F.poly([(gx - 11, gy - 58), (gx + 11, gy - 58), (gx + 11, gy - 30), (gx - 11, gy - 30)])
        F.fill(glass_, '#b8c4c4')
        F.fill(F.box(gx - 10, gy - 52, gx + 10, gy - 30), '#a0521a')
        F.fill(F.box(gx - 10, gy - 52, gx + 10, gy - 50), '#e8a860')
        F.fill(F.box(gx - 9, gy - 57, gx - 7, gy - 32), '#e8f0f0')
        F.fill(F.line([(gx + 4, gy - 72), (gx + 1, gy - 40)], 0.8), '#c0c6ce')
        F.fill(hold, '#9aa0a8')
        F.fill(hold & ((np.mod(F.xx.astype(int), 4) == 0) & (F.yy > gy - 24) & (F.yy < gy - 8)), '#4a5058')
        F.fill(hold & F.box(gx - 13, gy - 30, gx + 13, gy - 27), '#d8dee4')
        hdl = F.poly([(gx + 12, gy - 26), (gx + 22, gy - 24), (gx + 22, gy - 10), (gx + 11, gy - 8),
                      (gx + 11, gy - 11), (gx + 19, gy - 13), (gx + 19, gy - 22), (gx + 12, gy - 23)])
        F.fill(hdl, '#8a9098')
        F.outline(hold | glass_ | hdl, k=0.5)
        F.fill(F.ell(gx, gy - 1, 15, 2), '#4a4030')
    near = F.box(0, M_TABLE, 640, 360)
    F.mul(near, 0.86)
    F.fill(F.box(0, M_TABLE, 640, M_TABLE + 1), '#3a3028' if city == 'karsk' else '#8a8274')
    return F.opaque()


def motes_sheet():
    """Dust motes puffed out when the book shuts: 8 frames, motes spreading and settling in the lamp light."""
    w, h = 160, 60
    out = []
    for f in range(8):
        cell = np.zeros((h, w, 4), np.uint8)
        for i in range(30):
            a = K.hash2(i, 1, 51) * math.pi
            r = (6 + K.hash2(i, 2, 51) * 70) * (f + 1) / 8
            x = int(w / 2 + math.cos(a) * r * (1.4 if K.hash2(i, 3, 51) > 0.5 else -1.4))
            y = int(h - 6 - math.sin(a) * r * 0.45 + f * 0.8)
            if 0 <= x < w and 0 <= y < h and K.hash2(i, f, 53) > f / 12:
                cell[y, x] = (240, 222, 186, 255)
        out.append(cell)
    return K.hsheet(out)


def glove_side(th):
    """b3a: Ekdahl's grey glove from the right, the fingers under the upper board's fore-edge, the thumb on its
    cover, tilted with the board; canvas 300 x 160 with the index fingertip at (36, 70).  Returns (rgba, tip)."""
    s = 7.0
    cv = HD.Canvas(300, 160, 'karsk')
    HD.mats_common(cv)
    cv.mat('tweed', '#5e4c3a')
    cv.mat('glove', HD.KID_GLOVE, glossy=True)          # round 11c: warm grey kid leather (env_c4p2_cine_hands)
    ang = -90.0 + th * 0.35 - 8.0
    a = math.radians(ang)
    tip0 = (36.0, 62.0)
    d = (math.sin(a), -math.cos(a))                 # toward the fingertips: left, a little down
    wrist = (tip0[0] - d[0] * 15.0 * s, tip0[1] - d[1] * 15.0 * s)
    far = (wrist[0] - d[0] * 40 * s, wrist[1] - d[1] * 40 * s + 24)
    full, dv = HD.sleeve(cv, (wrist[0] - d[0] * 2.4 * s, wrist[1] - d[1] * 2.4 * s), far, 11.0 * s, 12.0 * s,
                         'tweed', seed=9, herring=True)
    HD.cuff_band(cv, (wrist[0] - d[0] * 2.6 * s, wrist[1] - d[1] * 2.6 * s), (d[0], d[1], dv[2], dv[3]), 8.6 * s,
                 2.8 * s, 'glove')
    p = HD.HandPose(wrist=wrist, ang=ang, s=s, side='L', view='palmar', glove=True, curl=(0.3, 0.34, 0.42, 0.5),
                    thumb=(-30.0, 0.1), spread=-8.0, pitch=40.0)
    HD.draw_hand(cv, p, glove_mat='glove')
    rgba = cv.render(key=(0.5, 0.7, 0.5))
    return rgba, _tip(p, 'index')


# ================================================================================================= build
def build(w):
    import env_c4p2_cine_book3d as B3
    import env_c4p2_cine_show as SHOW
    ct = cam_top()
    # b1: the table, the book (frame 0 open without the card; 1.. rising with the card baked in), the card sprite
    w('book/b1_bg.png', b1_plate())
    f0 = book_top(ct, [SWING[0]], PAL_B, KEY_B, LAMP_B, False, (4, 5, (30, 18, 10, 110)))
    fs = book_top(ct, SWING[1:], PAL_B, KEY_B, LAMP_B, True, (4, 5, (30, 18, 10, 110)))
    w('book/b1_book.png', K.hsheet(f0 + fs))
    w('book/card.png', FL.shadow_rgba(card_rgba(True), 2, 3, (30, 18, 10, 100)))
    w('book/tracing.png', FL.shadow_rgba(tracing_rgba(), 2, 3, (30, 18, 10, 90)))
    w('book/b1_refl.png', reflection_rgba())
    kh = [konrad_hand(f) for f in (0, 1)]
    w('book/b1_khand.png', K.hsheet([r for r, t in kh]))
    gl = [ekdahl_glove(f, 'berlin') for f in (0, 1, 2)]
    w('book/b1_glove.png', K.hsheet([r for r, t in gl]))
    tx, ty = CARD_ON[0] - (GUTTER + 2), CARD_ON[1] - SPREAD[1]
    card_scr = _proj_tex(ct, tx, ty, 0)
    trace_scr = _proj_tex(ct, TRACE_ON[0] - (GUTTER + 2), TRACE_ON[1] - SPREAD[1] + 30, 0)
    edge_b1 = [_edge_mid(ct, th) for th in SWING]
    # b2 / b3a: the profile at table height, Berlin closing and Karsk opening (the same drawing)
    w('book/b2_bg.png', macro_bg('berlin'))
    prof = [book_profile(th) for th in MACRO]
    w('book/b2_book.png', K.hsheet(prof))
    w('book/b3a_bg.png', macro_bg('karsk'))
    w('book/b3a_book.png', K.hsheet(prof))
    w('book/motes.png', motes_sheet())
    gs = [glove_side(th) for th in MACRO]
    w('book/b3a_glove.png', K.hsheet([r for r, t in gs]))
    edge_m = [macro_edge(th) for th in MACRO]
    # b3b: the canteen table with the book open at 212/213 (Karsk light), the glove and Alexei's hand
    bk = book_top(ct, [0], PAL_K, KEY_K, LAMP_K, True, (-4, 5, (30, 16, 6, 110)))[0]
    w('book/b3_bg.png', b3_plate(bk))
    g3, gt3 = ekdahl_glove(0, 'karsk')
    w('book/b3_glove.png', g3)
    ah = [alexei_hand(f) for f in (0, 1)]
    w('book/b3_alexei.png', K.hsheet([r for r, t in ah]))
    w('book/tea_steam.png', K.puff_sheet(8, 20, 30, PAL.K_STEAM[2:], 83, grow=(0.2, 0.5), thin=0.7,
                                         light=(0.5, -0.6), drift=0.15))
    # b4: the showcase
    SHOW.build(w, L)
    gtip = [list(map(lambda v: int(round(v)), t)) for r, t in gl] + [list(map(lambda v: int(round(v)), gs[0][1]))]
    L.update(card=list(CARD), card_scr=card_scr, trace_scr=trace_scr, swing=list(SWING), edge_b1=edge_b1,
             macro=list(MACRO), edge_m=edge_m, close_t=list(CLOSE_T), slide_t=list(SLIDE_T),
             withdraw_t=list(WITHDRAW_T), ktip=[int(round(v)) for v in kh[0][1]], gtip=gtip,
             gtip_side=[[int(round(v)) for v in t] for r, t in gs],
             atip=[int(round(v)) for v in ah[0][1]], glove_rest=[262, 214], book_shut=BOOK_SHUT,
             book_open=BOOK_OPEN, cut_b3=CUT_B3, settle=list(SETTLE))
