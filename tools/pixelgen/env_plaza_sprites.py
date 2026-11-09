"""env_plaza_sprites -- people, props and actor sheets for the plaza before the Great Hall (L_M1_Plaza).

Area: plaza-env.  Palette 'berlin' (+ the project's story-accent red ramp, used ONLY for the cloth of the
historical banners).  Builds on tools/pixelgen/pg.py, env_berlin_insignia (eagle / swastika masks) and
env_karsk_lib.figure (front-view civilians) -- all read-only.  Original procedural pixel art, deterministic.
Insignia sites take `hist` (TECHNICAL_ARCHITECTURE 12.4): neutral = fictional Reichssiegel / plain eagle.
Tone: the troops are anonymous (helmet shadow over the eyes), the crowd is seen from behind, no salutes.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
from pg import Layer  # noqa: E402
import env_berlin_insignia as INS  # noqa: E402
import env_berlin_kit as kit  # noqa: E402
import env_karsk_lib as KL  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ENV = os.path.join(ROOT, 'assets', 'environments', 'hall_plaza')

_B = pg.PALETTES['berlin']
N, V, S, O, G, T, PA, W = ([pg.hx(c) for c in _B[k]] for k in
                           ('night', 'violet', 'stone', 'ochre', 'glow', 'steel', 'patina', 'snow'))
RED_HEX = ['#4A1712', '#7A2A26', '#A8382E', '#C8503C']      # = PALETTES['sepia']['red'] (story accent)
RED = [pg.hx(c) for c in RED_HEX]
ALLOWED_HEX = sorted({c.upper() for r in _B.values() for c in r} | set(RED_HEX))
_PAL = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in ALLOWED_HEX], np.int32)
COLD = [N[0], N[1], N[2], N[3], V[1], V[2], V[3], W[0], W[1], W[2], W[3], W[4]]
STONE_D = [N[3], V[1], S[0], S[1], S[2], S[3], S[4]]
PATR = [N[0], N[1], PA[0], PA[1], PA[2], PA[3], PA[4]]
COATS = [[N[0], N[2], V[1]], [N[1], N[3], V[2]], [V[0], V[1], V[3]], [T[0], T[1], T[3]],
         [N[2], S[0], S[2]], [N[1], V[1], W[0]], [T[0], N[3], T[2]]]


# =========================================================================== basics
def snap(L: Layer) -> int:
    """binary alpha + every opaque pixel to the nearest allowed colour; returns #pixels that were off-palette"""
    a = L.c[..., 3] > 127
    L.c[~a] = 0
    if not a.any():
        return 0
    c = L.c[..., :3][a].astype(np.int32)
    d = ((c[:, None, :] - _PAL[None]) ** 2).sum(-1)
    bad = int((d.min(1) > 0).sum())
    L.c[..., :3][a] = _PAL[d.argmin(1)].astype(np.uint8)
    L.c[..., 3][a] = 255
    e = L.em[..., 3] > 0
    if e.any():
        ce = L.em[..., :3][e].astype(np.int32)
        de = ((ce[:, None, :] - _PAL[None]) ** 2).sum(-1)
        L.em[..., :3][e] = _PAL[de.argmin(1)].astype(np.uint8)
    return bad


OFF_PALETTE: dict = {}


def save(L: Layer, rel: str, normal=True, emission=None, strength=2.5):
    OFF_PALETTE[rel] = snap(L)
    base = os.path.join(ENV, rel)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    return L.save(base, normal=normal, emission=emission, strength=strength)


def save_color(L: Layer, rel: str):
    """historical twin: colour only (LayerStack.map_path falls back to the neutral _n/_e maps)"""
    OFF_PALETTE[rel] = snap(L)
    L.image().save(os.path.join(ENV, rel + '.png'))


def strip(frames: list) -> Layer:
    w, h = frames[0].w, frames[0].h
    out = Layer(w * len(frames), h, 'strip')
    for i, f in enumerate(frames):
        sl = slice(i * w, (i + 1) * w)
        out.c[:, sl], out.hgt[:, sl], out.nrm[:, sl], out.em[:, sl] = f.c, f.hgt, f.nrm, f.em
    return out


def edges(a):
    p = np.pad(a, 1)
    return (a & ~p[:-2, 1:-1], a & ~p[2:, 1:-1], a & ~p[1:-1, :-2], a & ~p[1:-1, 2:])


def tfill(L: Layer, x, y, t, ramp, mask=None, hgt=None):
    t = np.asarray(t, np.float32)
    m = np.ones(t.shape, bool) if mask is None else mask
    L.tone_fill(m, int(x), int(y), t, ramp, True, hgt)


def put(L: Layer, mask, x, y, col, hgt=None, em=None):
    L._put(np.asarray(mask, bool), int(x), int(y), col, hgt, em)


def disc(L: Layer, cx, cy, r, col, hgt=None, em=None):
    return L.ellipse(cx, cy, r, r, col, hgt, em)


def emit(col, a=255):
    return np.array([col[0], col[1], col[2], a], np.uint8)


# =========================================================================== people
def civ_back(H, coat, hat, rim, seed=0, wide=1.0) -> Layer:
    """spectator seen from behind, flat-shaded (left third in shadow), backlit by the parade floods:
    rim on the top contour, lighter side edges"""
    k = H / 46.0
    Wd = int(round(18 * k * wide)) + 6
    L = Layer(Wd, H + 1, 'civ')
    cx = Wd // 2
    hw, hh = max(4, int(round(6 * k))), max(4, int(round(6.5 * k)))
    top = 2
    sh_y = top + hh + 1
    hem_y = int(round(H * 0.74))
    lw = max(2, int(round(3 * k)))
    L.rect(cx - lw - 1, hem_y - 1, lw, H - hem_y + 1, N[1], hgt=0.4)
    L.rect(cx + 1, hem_y - 1, lw, H - hem_y + 1, N[2], hgt=0.4)
    L.rect(cx - lw - 2, H - 1, lw + 1, 2, N[0], hgt=0.45)
    L.rect(cx + 1, H - 1, lw + 1, 2, N[0], hgt=0.45)
    arm = max(2, int(round(3 * k)))
    for y in range(sh_y, hem_y + 1):
        rel = (y - sh_y) / max(1, hem_y - sh_y)
        hw_ = (4.5 if y == sh_y else 6.5 if y == sh_y + 1 else 7.6 + (0.7 if rel > 0.75 else 0)
               - (0.5 if 0.4 < rel < 0.6 else 0)) * k * wide
        x0, x1 = int(round(cx - hw_)), int(round(cx + hw_))
        L.rect(x0, y, x1 - x0, 1, coat[1], hgt=0.6)
        L.rect(x0, y, max(1, int((x1 - x0) * 0.36)), 1, coat[0], hgt=0.55)
        if y > sh_y + 2 and rel < 0.58:
            L.px(x0 + arm, y, coat[0], 0.55)
            L.px(x1 - 1 - arm, y, coat[0], 0.55)
    L.vline(cx, sh_y + 3, max(1, hem_y - sh_y - 6), coat[0], 0.5)
    hx0 = cx - hw // 2
    hair = (N[1], N[2], S[0], V[1])[seed % 4]
    L.rect(hx0, top, hw, hh, hair, hgt=0.75)
    L.c[top, hx0] = 0
    L.c[top, hx0 + hw - 1] = 0
    L.rect(hx0 - 1, sh_y - 1, hw + 2, 2, coat[1], hgt=0.65)        # collar turned up
    hatc = (N[1], coat[0], N[2], T[1])[seed % 4]
    if hat == 'fedora':
        L.rect(hx0, 0, hw, 3, hatc, hgt=0.85)
        L.rect(hx0 - 2, 3, hw + 4, 1, hatc, hgt=0.8)
    elif hat == 'cap':
        L.rect(hx0, 1, hw + 1, 2, hatc, hgt=0.8)
    elif hat == 'scarf':
        sc = (S[1], V[2], O[0], T[2])[seed % 4]
        L.rect(hx0 - 1, 1, hw + 2, hh, sc, hgt=0.8)
        L.rect(cx - 1, top + hh - 1, 3, 2, sc, hgt=0.75)
    elif hat == 'beret':
        L.rect(hx0 - 1, 1, hw + 2, 2, hatc, hgt=0.8)
        L.px(cx, 0, hatc)
    a = L.alpha()
    tp, bt, lf, rt = edges(a)
    rows = np.arange(L.h)[:, None]
    L.c[(lf | rt) & ~tp & (rows < hem_y)] = coat[2]
    L.c[tp] = rim
    return L


def guard_front(H=42, rim=None) -> Layer:
    """guard facing the crowd: Stahlhelm, shadow band over the eyes (anonymous), greatcoat, rifle at order arms"""
    rim = T[4] if rim is None else rim
    Wd, cx = 20, 10
    L = Layer(Wd, H + 1, 'guard')
    rx = cx - 8
    L.rect(rx, 6, 1, H - 6, S[0], hgt=0.6)
    L.rect(rx, 2, 1, 9, T[1], hgt=0.7)
    L.rect(cx - 4, 30, 3, H - 32, T[0], 0.45)
    L.rect(cx + 1, 30, 3, H - 32, T[0], 0.45)
    L.rect(cx - 5, H - 2, 4, 3, N[0], 0.5)
    L.rect(cx + 1, H - 2, 4, 3, N[0], 0.5)
    pts = [(cx - 6.5, 9), (cx + 6.5, 9), (cx + 7, 12), (cx + 7.5, 31), (cx - 7.5, 31), (cx - 7, 12)]
    m, mx, my = L.poly_mask(pts)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    t = 0.55 - 0.32 * np.abs((xx + mx + 0.5 - cx) / 7.5) - 0.2 * yy / m.shape[0]
    L.tone_fill(m, mx, my, t, [T[0], T[1], T[2], T[3]], hgt=0.6)
    L.rect(cx - 7, 20, 15, 1, N[1], 0.65)
    L.px(cx, 20, T[4])
    L.rect(cx - 5, 21, 2, 2, N[1], 0.66)
    L.rect(cx + 4, 21, 2, 2, N[1], 0.66)
    for yb in (12, 15, 18, 24, 27):
        L.px(cx - 2, yb, T[4])
        L.px(cx + 2, yb, T[4])
    L.vline(cx, 21, 10, T[0], 0.55)
    L.rect(cx + 6, 11, 2, 13, T[1], 0.62)
    L.rect(cx + 6, 24, 2, 1, S[1], 0.62)
    L.rect(cx - 8, 11, 2, 11, T[1], 0.62)
    L.rect(cx - 8, 22, 2, 1, S[1], 0.62)
    L.rect(cx - 3, 8, 7, 2, T[2], 0.7)
    L.rect(cx - 2, 4, 5, 5, S[1], 0.75)
    L.rect(cx - 2, 4, 5, 2, N[1], 0.75)                      # helmet shadow: no eyes, no face
    L.px(cx, 7, S[0])
    L.rect(cx - 3, 0, 7, 1, T[1], 0.9)
    L.rect(cx - 4, 1, 9, 2, T[1], 0.9)
    L.rect(cx - 5, 3, 11, 1, T[0], 0.85)
    L.rect(cx - 5, 4, 1, 2, T[0], 0.8)
    L.rect(cx + 5, 4, 1, 2, T[0], 0.8)
    L.px(cx - 3, 6, N[1])
    L.px(cx + 3, 6, N[1])
    a = L.alpha()
    tp, bt, lf, rt = edges(a)
    L.c[(lf | rt) & ~bt] = rim
    L.c[tp] = T[5]
    return L


# march cycle (near foot dx, lift, far foot dx, lift), body bob
STEP = [(4, 0, -4, 0), (3, 0, -2, 1), (1, 0, 0, 2), (-1, 0, 2, 1),
        (-4, 0, 4, 0), (-2, 1, 3, 0), (0, 2, 1, 0), (2, 1, -1, 0)]
BOB = [0, 0, -1, 0, 0, 0, -1, 0]


def soldier_side(f, H=26, carry='rifle', extra_top=0) -> Layer:
    """marching soldier, profile facing right (+x), in step; rifle on the far shoulder"""
    coat = [T[0], T[1], T[2], T[3]]
    Wd, cx = 20, 10
    L = Layer(Wd, H + 1 + extra_top, 'soldier')
    o = extra_top
    nd, nl, fd, fl = STEP[f % 8]
    b = BOB[f % 8]
    hip, sh = o + 15 + b, o + 7 + b

    def leg(dx, lift, col, boot):
        x1, y1 = cx + dx, o + H - 1 - lift
        L.line(cx, hip, x1, y1, col, 0.45)
        L.line(cx + 1, hip, x1 + 1, y1, col, 0.45)
        L.rect(x1, y1 - 1, 3, 2, boot, 0.5)
    if carry == 'rifle':
        L.line(cx + 1, sh + 6, cx - 7, sh - 7, S[0], 0.6)
        L.line(cx - 5, sh - 4, cx - 7, sh - 7, T[1], 0.6)
    leg(fd, fl, coat[0], N[0])
    leg(nd, nl, coat[1], N[1])
    pts = [(cx - 3, sh), (cx + 2.5, sh), (cx + 3.5, hip - 2), (cx + 4.5, hip + 4), (cx - 4.5, hip + 4),
           (cx - 3.5, hip - 2)]
    m, mx, my = L.poly_mask(pts)
    put(L, m, mx, my, coat[1], 0.6)
    xx = np.mgrid[0:m.shape[0], 0:m.shape[1]][1] + mx
    put(L, m & (xx <= cx - 2), mx, my, coat[0], 0.55)
    put(L, m & (xx >= cx + 2), mx, my, coat[2], 0.62)
    L.rect(cx - 3, hip - 3, 7, 1, N[1], 0.65)
    L.px(cx + 2, hip - 2, N[2])
    L.rect(cx - 1, sh - 4, 4, 4, S[1], 0.75)
    L.rect(cx - 1, sh - 4, 4, 2, N[1], 0.75)
    L.px(cx + 2, sh - 2, S[2])
    L.rect(cx - 2, sh - 7, 5, 1, coat[1], 0.9)
    L.rect(cx - 3, sh - 6, 7, 2, coat[1], 0.9)
    L.rect(cx - 4, sh - 4, 2, 2, coat[0], 0.85)
    L.px(cx + 3, sh - 4, coat[0])
    L.rect(cx - 1, sh - 7, 3, 1, T[4], 0.95)
    if carry == 'rifle':
        hd = -int(round(nd * 0.7))
        L.line(cx, sh + 1, cx + hd, sh + 8, coat[2], 0.65)
        L.line(cx + 1, sh + 1, cx + 1 + hd, sh + 8, coat[1], 0.65)
        L.px(cx + hd, sh + 9, S[1])
        L.line(cx - 4, sh - 2, cx - 7, sh - 7, T[3], 0.7)          # rifle above the shoulder reads in the block
    a = L.alpha()
    tp = edges(a)[0]
    L.c[tp & (np.arange(L.h)[:, None] < hip)] = T[4]
    return L


def standard_frame(f, hist) -> Layer:
    """standard bearer at the head of each block: pole held upright, cloth trailing (insignia site)"""
    L = soldier_side(f, carry='pole', extra_top=26)
    cx = 10
    b = BOB[f % 8]
    sh = 26 + 7 + b
    px_ = cx + 4
    L.rect(px_, sh - 30, 1, 40, S[1], 0.7)
    L.rect(px_ - 1, sh - 32, 3, 2, O[4], 0.9)
    L.rect(cx + 2, sh + 2, 3, 2, S[1], 0.7)                    # hands on the pole
    fw, fh = 15, 12
    ph = f / 8.0 * 2 * math.pi
    for i in range(fw):
        x = px_ - 1 - i
        sag = int(round(0.9 * math.sin(i * 0.55 - ph) + i * 0.12))
        y0 = sh - 29 + sag
        tone = 0.5 + 0.32 * math.sin(i * 0.55 - ph + 1.3)
        ramp = [RED[0], RED[1], RED[2], RED[3]] if hist else [N[2], T[1], T[2], T[3]]
        L.tone_fill(np.ones((fh, 1), bool), x, y0, np.full((fh, 1), tone), ramp, hgt=0.6)
    cxf, cyf = px_ - 8, sh - 29 + 6 + int(round(0.9 * math.sin(7 * 0.55 - ph) + 0.8))
    if hist:
        disc(L, cxf + 0.5, cyf + 0.5, 4.2, W[3], 0.7)
        sw = INS.swastika_mask(7)
        put(L, sw, cxf - sw.shape[1] // 2, cyf - sw.shape[0] // 2, N[0], 0.7)
    else:
        d = 9
        dm, pil = kit.reichssiegel_mask(d)
        put(L, dm, cxf - d // 2, cyf - d // 2, N[0], 0.7)
        put(L, pil, cxf - d // 2, cyf - d // 2, W[3], 0.7)
    return L


def tank_frame(f) -> Layer:
    """medium tank, side view, facing right (+x); track links / wheel hubs advance per frame (4-frame loop)"""
    Wd, Ht = 86, 34
    L = Layer(Wd, Ht, 'tank')
    # hull
    hull = [(4, 15), (66, 15), (74, 20), (76, 25), (4, 25)]
    m, mx, my = L.poly_mask(hull)
    yy = np.mgrid[0:m.shape[0], 0:m.shape[1]][0]
    L.tone_fill(m, mx, my, 0.62 - 0.45 * yy / m.shape[0], [T[0], T[1], T[2], T[3]], hgt=0.6)
    L.rect(2, 21, 76, 2, T[1], 0.7)                            # fender
    L.rect(2, 21, 76, 1, T[3], 0.75)
    for bx in (12, 40):
        L.rect(bx, 17, 9, 4, T[2], 0.7)
        L.rect(bx, 17, 9, 1, T[3], 0.72)
    L.rect(2, 16, 3, 3, N[1], 0.6)                             # exhaust
    # tracks + wheels
    L.rect(6, 24, 68, 9, N[2], 0.5)
    L.rect(7, 23, 66, 1, T[1], 0.55)
    L.rect(7, 33, 64, 1, N[1], 0.5)
    for x in range(7, 73):
        if (x + f) % 4 == 0:
            L.px(x, 23, T[3])
        if (x - f) % 4 == 0:
            L.px(x, 32, T[2])
    for i, wx in enumerate((14, 23, 32, 41, 50, 59)):
        disc(L, wx + 0.5, 28.5, 3.6, T[1], 0.7)
        disc(L, wx + 0.5, 28.5, 1.6, T[2], 0.8)
        ang = f * math.pi / 4 + i
        L.px(wx + int(round(math.cos(ang) * 2)), 28 + int(round(math.sin(ang) * 2)), T[0])
    disc(L, 70.5, 27.5, 3.8, T[1], 0.7)
    disc(L, 7.5, 27.5, 3.2, T[1], 0.7)
    for k in range(6):
        a = f * math.pi / 8 + k * math.pi / 3
        L.px(70 + int(round(math.cos(a) * 3)), 27 + int(round(math.sin(a) * 3)), T[3])
    # turret, gun, cupola + commander (anonymous)
    tur = [(26, 6), (52, 6), (57, 9), (57, 15), (24, 15)]
    m, mx, my = L.poly_mask(tur)
    yy = np.mgrid[0:m.shape[0], 0:m.shape[1]][0]
    L.tone_fill(m, mx, my, 0.7 - 0.5 * yy / m.shape[0], [T[0], T[1], T[2], T[3], T[4]], hgt=0.8)
    L.rect(56, 8, 3, 6, T[1], 0.8)
    L.rect(58, 10, 24, 2, T[2], 0.85)
    L.rect(58, 10, 24, 1, T[3], 0.88)
    L.rect(81, 9, 3, 4, T[1], 0.85)
    L.rect(30, 3, 8, 3, T[1], 0.85)
    L.rect(32, 0, 4, 3, N[1], 0.9)
    L.px(36, 1, N[2])
    L.rect(22, 9, 2, 5, T[1], 0.7)                             # stowage bin
    a = L.alpha()
    tp = edges(a)[0]
    L.c[tp] = T[4]
    return L


# =========================================================================== crowd
def crowd_strip(width, seed, frames=4, children=0.08) -> Layer:
    """three rows of spectators from behind, standing at the barrier; a few sway (4-frame loop)"""
    rng = np.random.default_rng(seed)
    Ht = 52
    figs = []
    hats = ('fedora', 'fedora', 'cap', 'scarf', 'bare', 'beret', 'fedora', 'scarf', 'cap')
    for row, (dy, step, rim) in enumerate(((6, 10.0, W[2]), (3, 11.5, W[1]), (0, 13.0, W[1]))):
        x = rng.uniform(2, 9)
        while x < width - 6:
            child = row == 2 and rng.random() < children
            H = int(rng.integers(29, 34)) if child else int(rng.integers(39, 47))
            coat = COATS[int(rng.integers(0, len(COATS)))]
            hat = 'scarf' if child and rng.random() < 0.5 else ('cap' if child else hats[int(rng.integers(0, len(hats)))])
            spr = civ_back(H, coat, hat, rim, seed=int(rng.integers(0, 1000)), wide=float(rng.uniform(0.9, 1.15)))
            r = rng.random()
            mv = [0, 0, 1, 1] if r < 0.16 else ([0, -1, -1, 0] if r < 0.27 else [0, 0, 0, 0])
            figs.append((row, int(x), Ht - 1 - dy - H, spr, mv))
            x += step * rng.uniform(0.75, 1.3)
    out = []
    for f in range(frames):
        L = Layer(width, Ht, 'crowd')
        for row, x, y, spr, mv in figs:
            L.blit(spr, x - spr.w // 2 + mv[f % 4], y)
        out.append(L)
    return strip(out)


# =========================================================================== props
def lamp_post() -> Layer:
    L = Layer(13, 94, 'lamp')
    cx = 6
    L.rect(cx - 3, 87, 7, 7, N[2], 0.5)
    L.rect(cx - 3, 87, 7, 1, T[2], 0.55)
    L.rect(cx - 1, 20, 3, 67, N[2], 0.6)
    L.vline(cx + 1, 20, 67, V[2], 0.62)
    L.rect(cx - 2, 52, 5, 2, N[1], 0.65)
    L.rect(cx - 2, 18, 5, 3, N[1], 0.7)
    # lantern: frame + 3 lit panes, pyramid cap, finial
    L.rect(cx - 4, 6, 9, 12, N[1], 0.7)
    for i, gx in enumerate((cx - 3, cx - 1, cx + 1)):
        col = (G[1], G[3], G[2])[i]
        L.rect(gx, 7, 2 if i < 2 else 3, 10, col, 0.8, em=emit(col))
    L.rect(cx - 4, 12, 9, 1, N[1], 0.7)
    L.poly([(cx - 5, 6), (cx + 5, 6), (cx + 1, 2), (cx - 1, 2)], N[2], 0.8)
    L.rect(cx - 4, 5, 9, 1, W[3], 0.85)
    L.px(cx, 0, N[2])
    L.px(cx, 1, N[2])
    return L


def tram_stop() -> Layer:
    L = Layer(16, 68, 'tram_stop')
    cx = 7
    L.rect(cx, 10, 2, 58, T[2], 0.6)
    L.vline(cx + 1, 10, 58, T[3], 0.62)
    disc(L, cx + 1, 6, 6.2, T[1], 0.8)
    disc(L, cx + 1, 6, 5.0, G[2], 0.85)
    H_ = ['#...#', '#...#', '#####', '#...#', '#...#']
    for j, row in enumerate(H_):
        for i, ch in enumerate(row):
            if ch == '#':
                L.px(cx - 1 + i, 4 + j, PA[2])
    L.rect(cx - 4, 16, 11, 14, T[1], 0.7)                    # timetable case
    L.rect(cx - 3, 17, 9, 12, W[3], 0.75)
    for yy in range(18, 28, 2):
        L.hline(cx - 2, yy, 7 - (yy % 3), V[2])
    L.rect(cx - 3, 17, 9, 3, S[3], 0.75)                     # pasted-over strip ('Verkehr eingestellt')
    L.rect(cx - 4, 15, 11, 1, W[4], 0.8)
    L.rect(cx - 2, 32, 7, 4, T[4], 0.7)                      # line plate
    L.rect(cx - 1, 33, 2, 2, N[1])
    L.rect(cx + 2, 33, 2, 2, N[1])
    L.rect(cx - 2, 0, 7, 1, W[3], 0.9)
    return L


def litfass(hist) -> Layer:
    """advertising column with posters; the large state poster is an insignia site"""
    Wd, Ht = 22, 62
    L = Layer(Wd, Ht, 'litfass')
    x0, w, top = 2, 18, 10
    yy, xx = np.mgrid[top:Ht - 4, x0:x0 + w]
    u = (xx + 0.5 - (x0 + w / 2)) / (w / 2)
    t = 0.55 - 0.35 * u * u + 0.12 * u
    tfill(L, x0, top, t, [V[1], V[2], V[3], W[0]], hgt=0.6)
    # posters (paper) wrap: rectangles with cylindrical shading
    posters = [(x0 + 1, top + 3, 9, 13, [S[2], S[3], S[4]]), (x0 + 10, top + 2, 7, 18, [W[1], W[2], W[3]]),
               (x0 + 1, top + 18, 16, 14, [W[1], W[2], W[3]]), (x0 + 2, top + 34, 13, 10, [O[0], S[3], S[4]])]
    for (px_, py_, pw, ph, ramp) in posters:
        uu = (np.arange(px_, px_ + pw) + 0.5 - (x0 + w / 2)) / (w / 2)
        tt = np.tile(0.75 - 0.4 * uu * uu, (ph, 1))
        tfill(L, px_, py_, tt, ramp, hgt=0.62)
    # ration notice text lines
    for yy_ in range(top + 4, top + 15, 2):
        L.hline(x0 + 11, yy_, 5, V[2])
    # big state poster: emblem
    ex, ey = x0 + 9, top + 25
    if hist:
        em = INS.eagle_masks(13, wreath=True, swastika=True)
        h, w_ = em['size']
        put(L, em['all'], ex - w_ // 2, ey - h // 2, N[1], 0.7)
    else:
        dm, pil = kit.reichssiegel_mask(9)
        put(L, dm, ex - 4, ey - 4, N[1], 0.7)
        put(L, pil, ex - 4, ey - 4, W[3], 0.7)
    L.hline(x0 + 3, top + 31, 12, N[2])
    # torn corner + paste stains
    L.rect(x0 + 13, top + 30, 3, 3, V[2])
    L.px(x0 + 6, top + 44, V[1])
    # cap (dome) + finial + snow; base ring
    L.rect(x0 - 1, top - 2, w + 2, 3, N[2], 0.8)
    L.ellipse(x0 + w / 2, top - 2, w / 2 + 0.5, 5, N[2], 0.85)
    L.rect(x0 + w // 2 - 1, 0, 2, 4, N[1], 0.9)
    L.ellipse(x0 + w / 2, top - 4, w / 2 - 1, 2.5, W[3], 0.9)
    L.rect(x0 - 1, top - 1, w + 2, 1, W[2], 0.85)
    L.rect(x0 - 1, Ht - 4, w + 2, 4, N[2], 0.5)
    L.rect(x0 - 1, Ht - 4, w + 2, 1, T[2], 0.55)
    return L


def loudspeaker() -> Layer:
    Wd, Ht = 40, 120
    L = Layer(Wd, Ht, 'loudspeaker')
    cx = 20
    for side in (-1, 1):                                       # cables sagging away
        pts = pg.catenary(cx, 16, cx + side * 20, 30, 6, 24)
        L.polyline(pts, N[1])
    L.rect(cx - 1, 10, 3, Ht - 10, S[0], 0.6)
    L.vline(cx + 1, 10, Ht - 10, S[1], 0.62)
    for yb in (30, 64, 98):
        L.rect(cx - 1, yb, 3, 1, T[2], 0.66)
    L.rect(cx - 3, 70, 7, 9, T[1], 0.7)                      # junction box
    L.rect(cx - 3, 70, 7, 1, T[3], 0.72)
    L.rect(cx - 12, 12, 25, 2, T[1], 0.75)                   # crossbar
    for hx_, hy, r, side in ((cx - 11, 10, 4.6, -1), (cx, 7, 5.8, 0), (cx + 11, 10, 4.6, 1)):
        if side:
            L.poly([(hx_ - side * 7, hy - 1), (hx_ - side, hy - 3), (hx_ - side, hy + 4), (hx_ - side * 7, hy + 2)], T[2], 0.75)
        L.ellipse(hx_ + 0.5, hy + 0.5, r if not side else r * 0.7, r, T[3], 0.85)
        L.ellipse(hx_ + 0.5, hy + 0.5, (r - 1.2) if not side else (r - 1.2) * 0.7, r - 1.2, N[1], 0.7)
        L.px(hx_, hy, T[1])
    L.rect(cx - 12, 11, 25, 1, W[3], 0.8)
    return L


def banner_mast() -> Layer:
    L = Layer(30, 176, 'banner_mast')
    cx = 15
    L.rect(cx - 1, 6, 3, 164, T[2], 0.6)
    L.vline(cx - 1, 6, 164, T[3], 0.62)
    L.vline(cx + 1, 6, 164, T[1], 0.58)
    L.rect(cx - 12, 8, 25, 2, T[1], 0.75)
    L.rect(cx - 12, 8, 25, 1, W[3], 0.8)
    L.rect(cx - 2, 0, 5, 5, O[3], 0.9)
    L.rect(cx - 1, 0, 2, 2, G[2], 0.95)
    L.rect(cx - 5, 168, 11, 8, S[1], 0.5)
    L.rect(cx - 5, 168, 11, 1, W[3], 0.55)
    L.rect(cx - 5, 169, 11, 1, S[3], 0.52)
    return L


def banner_near(hist, frames=6) -> Layer:
    """long banner hanging from the mast crossbar, slow folds travelling across (6-frame loop)"""
    fw, fh = 24, 104
    out = []
    for f in range(frames):
        L = Layer(fw, fh, 'banner')
        ph = f / frames * 2 * math.pi
        for x in range(1, fw - 1):
            hang = fh - 3 - int(round(1.6 + 1.6 * math.sin(x * 0.45 + ph)))
            tone = 0.52 + 0.3 * math.sin(x * 0.55 - ph + 0.4) - (0.12 if x in (1, fw - 2) else 0)
            ramp = RED if hist else [N[2], T[0], T[1], T[2], T[3]]
            ci = int(round(float(np.clip(tone, 0, 1)) * (len(ramp) - 1)))
            L.rect(x, 1, 1, hang, ramp[ci], hgt=0.6)
            L.rect(x, hang - 3, 1, 4, ramp[max(0, ci - 1)], hgt=0.6)
        L.rect(0, 0, fw, 2, T[1], 0.8)
        cx_, cy_ = fw // 2, 30
        if hist:
            disc(L, cx_, cy_, 7.6, W[3], 0.7)
            sw = INS.swastika_mask(11)
            put(L, sw, cx_ - sw.shape[1] // 2, cy_ - sw.shape[0] // 2, N[0], 0.7)
            L.rect(2, 4, 1, fh - 12, W[2], 0.62)
            L.rect(fw - 3, 4, 1, fh - 12, W[2], 0.62)
        else:
            d = 15
            dm, pil = kit.reichssiegel_mask(d)
            put(L, dm, cx_ - d // 2, cy_ - d // 2, N[0], 0.7)
            put(L, pil, cx_ - d // 2, cy_ - d // 2, W[3], 0.7)
        out.append(L)
    return strip(out)


def vendor() -> Layer:
    """chestnut vendor: handcart with a glowing brazier, an old man warming his hands (warm focal light)"""
    Wd, Ht = 50, 48
    L = Layer(Wd, Ht, 'vendor')
    man = KL.figure(40, [N[2], V[1], V[2]], skin=S[3], hat='cap', facing='front', arms='forward',
                    trousers=N[1], boots=N[0], scarf=O[1], hat_col=N[1], apron=S[3], seed=5,
                    warm=('r', G[1]))
    L.blit(man, 26, 1)
    L.rect(4, 26, 34, 12, S[1], 0.6)                          # cart box
    L.rect(4, 26, 34, 1, S[3], 0.65)
    for xx in range(6, 38, 6):
        L.vline(xx, 27, 11, S[0], 0.55)
    L.rect(2, 24, 38, 2, S[2], 0.7)
    disc(L, 10, 41, 5.5, N[2], 0.6)
    disc(L, 10, 41, 2.0, S[1], 0.7)
    disc(L, 32, 41, 5.5, N[2], 0.6)
    disc(L, 32, 41, 2.0, S[1], 0.7)
    L.rect(38, 30, 10, 2, S[0], 0.6)                         # handle
    L.rect(8, 12, 14, 12, N[1], 0.7)                          # brazier drum
    L.rect(8, 12, 14, 1, T[2], 0.75)
    for i, xx in enumerate(range(9, 21)):
        col = (G[0], G[2], O[4], G[1])[i % 4]
        L.rect(xx, 10, 1, 2 + (i * 7 % 3), col, 0.8, em=emit(col))
    for xx in range(9, 21, 3):
        L.px(xx, 13, O[3], em=emit(O[3]))
    L.rect(24, 18, 9, 6, T[2], 0.7)                           # pan of chestnuts
    L.rect(25, 17, 7, 1, S[2], 0.72)
    L.rect(2, 20, 6, 4, W[2], 0.7)                            # paper cones
    L.px(3, 19, W[3])
    L.px(6, 19, W[3])
    return L


def photographer() -> Layer:
    """press photographer on a stepladder, from behind, camera up, round flash reflector"""
    Wd, Ht = 26, 64
    L = Layer(Wd, Ht, 'photographer')
    lx = 6
    L.line(lx, 46, lx - 2, 63, S[1], 0.5)
    L.line(lx + 12, 46, lx + 14, 63, S[1], 0.5)
    for yy in (51, 57):
        L.hline(lx - 1, yy, 15, S[2], 0.55)
    L.rect(lx - 1, 45, 15, 2, S[2], 0.6)
    man = civ_back(44, [N[1], N[3], V[2]], 'fedora', W[1], seed=7)
    L.blit(man, 13 - man.w // 2, 2)
    L.rect(4, 9, 3, 4, N[3], 0.7)                            # elbows out
    L.rect(19, 9, 3, 4, N[3], 0.7)
    L.rect(9, 2, 8, 3, N[1], 0.75)                            # camera above the brim
    disc(L, 20.5, 3.5, 3.2, T[4], 0.85)                       # flash reflector
    disc(L, 20.5, 3.5, 1.4, W[4], 0.9)
    L.rect(17, 5, 2, 4, T[1], 0.8)
    return L


def children(hist) -> Layer:
    """two children on a crate behind the crowd; one holds a limp paper flag (insignia site)"""
    Wd, Ht = 30, 44
    L = Layer(Wd, Ht, 'children')
    a = civ_back(30, [V[0], V[1], V[3]], 'cap', W[1], seed=11)
    b = civ_back(27, [N[2], S[0], S[2]], 'scarf', W[1], seed=14)
    L.blit(a, 3, 4)
    L.blit(b, 15, 7)
    L.vline(23, 0, 16, S[2], 0.7)                             # flag stick held up
    L.rect(22, 15, 2, 2, S[1], 0.7)
    fl = RED if hist else [T[0], T[1], T[2], T[2]]
    for i in range(6):
        hlen = 9 - (i // 2)
        tfill(L, 17 + i, 1 + (i // 3), np.full((hlen, 1), 0.45 + 0.25 * math.sin(i)), fl)
    if hist:
        L.rect(19, 3, 3, 3, W[3])
        L.px(20, 3, N[0])
        L.px(20, 4, N[0])
        L.px(19, 4, N[0])
        L.px(21, 5, N[0])
    else:
        L.rect(19, 3, 3, 3, N[0])
        L.px(20, 4, W[3])
    L.rect(1, 34, 28, 10, S[1], 0.55)                         # crate
    L.rect(1, 34, 28, 1, W[3], 0.6)
    L.hline(1, 39, 28, S[0], 0.5)
    L.vline(1, 34, 10, S[0], 0.5)
    L.vline(28, 34, 10, S[0], 0.5)
    return L


def barrel_guard() -> Layer:
    """fire barrel of the tank crew in the cleared lot, a crewman warming his hands"""
    Wd, Ht = 34, 48
    L = Layer(Wd, Ht, 'barrel')
    man = KL.figure(42, [N[0], N[1], N[3]], skin=S[2], hat='cap', facing='front', arms='forward',
                    trousers=N[1], boots=N[0], hat_col=N[0], seed=9, warm=('l', O[4]))
    L.blit(man, 15, 5)
    L.rect(2, 32, 12, 16, T[1], 0.6)
    L.rect(2, 32, 12, 1, T[3], 0.65)
    L.hline(2, 38, 12, O[1], 0.6)
    L.hline(2, 44, 12, O[1], 0.6)
    L.vline(3, 33, 14, T[2], 0.62)
    # round 13: the flame is one frame of the pixel fire kit's tongues (pixel_fire_bake.flames) in the plaza's
    # colours -- a main tongue with a fork over a bed of embers (the prop is a still)
    import pixel_fire_bake as PFB
    idx = PFB.bands(PFB.flames(12, 14, 8, [(6, 4, 1.0)], 9, 1.0, base=0.25, cols=PFB.MARKS[:4])[2])
    for y, x in zip(*np.nonzero(idx >= 0)):
        col = (O[3], O[4], G[1], G[2])[int(idx[y, x])]
        L.rect(2 + int(x), 18 + int(y), 1, 1, col, 0.8, em=emit(col))
    L.rect(5, 26, 1, 2, G[3], 0.85, em=emit(G[3]))
    return L


def rubble(seed, Wd, Ht) -> Layer:
    """heap of a cleared tenement: jagged profile, beams and a bent bedframe sticking out, sparse bricks,
    snow lying on the upper faces"""
    rng = np.random.default_rng(seed)
    L = Layer(Wd, Ht, 'rubble')
    prof = np.zeros(Wd)
    for _ in range(5):
        c, w, h = rng.uniform(0.15, 0.85) * Wd, rng.uniform(0.18, 0.4) * Wd, rng.uniform(0.35, 0.9) * (Ht - 6)
        prof = np.maximum(prof, h * np.clip(1 - np.abs(np.arange(Wd) + 0.5 - c) / w, 0, 1) ** 0.9)
    prof += rng.integers(0, 3, Wd) * (prof > 2)
    prof = np.minimum(prof, Ht - 4).astype(int)
    for x in range(Wd):
        hh = prof[x]
        if hh <= 0:
            continue
        y0 = Ht - hh
        L.rect(x, y0, 1, hh, V[1], 0.5)
        L.rect(x, y0 + max(2, hh // 2), 1, hh - max(2, hh // 2), N[3], 0.45)
        if x % 7 in (2, 3) and hh > 6:
            L.rect(x, y0 + 3, 1, hh - 5, N[2], 0.45)
    for _ in range(int(Wd * Ht / 30)):
        x, y = int(rng.integers(1, Wd - 3)), int(rng.integers(2, Ht - 2))
        if L.c[y, x, 3] and L.c[y, min(Wd - 1, x + 2), 3] and y > Ht - prof[x] + 2:
            col = (O[1], O[2], S[1], S[2], V[2])[int(rng.integers(0, 5))]
            L.rect(x, y, 2 + int(rng.integers(0, 2)), 1, col, 0.65)
    for _ in range(2):
        x0 = int(rng.integers(6, Wd - 18))
        y0 = Ht - prof[x0] + 2
        L.line(x0, y0, x0 + int(rng.integers(10, 16)), y0 - int(rng.integers(5, 10)), S[0], 0.7)
    bx = int(Wd * 0.6)
    by = Ht - prof[bx] + 1
    L.line(bx, by, bx + 11, by - 5, T[2], 0.7)
    for k in range(0, 12, 3):
        L.line(bx + k, by - k * 5 // 11, bx + k, by - k * 5 // 11 + 4, T[1], 0.7)
    a = L.alpha()
    tp = edges(a)[0]
    snow = tp.copy()
    for d in (1, 2):
        sh = np.vstack([np.zeros((d, Wd), bool), tp[:-d]]) & a & (rng.random((Ht, Wd)) < (0.85 if d == 1 else 0.4))
        snow |= sh
    L.c[snow] = W[2]
    L.c[tp] = W[3]
    return L


def notice_door(hist) -> Layer:
    """official notice pasted on the sealed door; round stamp = insignia site"""
    L = Layer(12, 16, 'notice')
    L.rect(0, 0, 12, 16, W[2], 0.6)
    L.rect(1, 1, 10, 14, W[3], 0.62)
    L.rect(2, 2, 8, 1, N[2])
    for yy in range(4, 10, 2):
        L.hline(2, yy, 8 - (yy % 4), V[2])
    cx, cy = 7, 12
    disc(L, cx + 0.5, cy + 0.5, 3.4, V[1], 0.64)
    disc(L, cx + 0.5, cy + 0.5, 2.4, W[3], 0.64)
    if hist:
        for j, row in enumerate(['#.###', '#.#..', '#####', '..#.#', '###.#']):
            for i, ch in enumerate(row):
                if ch == '#' and abs(i - 2) + abs(j - 2) < 4:
                    L.px(cx - 2 + i, cy - 2 + j, N[1])
    else:
        L.rect(cx - 1, cy - 1, 3, 3, N[1])
        L.px(cx, cy, W[3])
    return L


def window_life(frames=8) -> Layer:
    """lit window of the neighbours above the sealed flat: a woman behind the lace curtain, who now and then
    leans to look down at the street (frames 6-7)"""
    out = []
    for f in range(frames):
        L = Layer(12, 22, 'win')
        L.rect(0, 0, 12, 22, S[2], 0.6)
        g = np.zeros((20, 10), np.float32) + np.linspace(0.75, 0.35, 20)[:, None]
        tfill(L, 1, 1, g, [O[3], O[4], G[0], G[1], G[2]], hgt=0.3)
        L.em[1:21, 1:11] = L.c[1:21, 1:11]
        lean = 1 if f >= 6 else 0
        L.rect(6 - lean, 6, 4, 4, N[2], 0.4)                  # head
        L.rect(5 - lean, 10, 6, 11, N[2], 0.4)                # shoulders
        L.em[6:10, 6 - lean:10 - lean] = 0
        L.em[10:21, 5 - lean:11 - lean] = 0
        cur = 5 if f < 6 else 4
        for yy in range(1, 21):
            for xx in range(1, 1 + cur):
                if (xx + yy) % 3:
                    L.px(xx, yy, S[4] if (xx * yy) % 4 else W[2], 0.35)
                    L.em[yy, xx] = 0
        L.vline(6, 1, 20, S[1], 0.6)
        L.hline(1, 8, 10, S[1], 0.6)
        L.em[1:21, 6] = 0
        L.em[8, 1:11] = 0
        out.append(L)
    return strip(out)


# =========================================================================== fx sheets
def puff_strip(fw, fh, n, seed, frames=8, cols=None, drift=4.0, r0=1.2, r1=3.6) -> Layer:
    """seamless rising smoke / steam: particles on a closed cycle"""
    cols = cols or [V[3], W[0], W[1]]
    rng = np.random.default_rng(seed)
    parts = [(rng.random(), rng.uniform(-1.5, 1.5), rng.uniform(0, 6.28)) for _ in range(n)]
    out = []
    for f in range(frames):
        L = Layer(fw, fh, 'puff')
        for ph, x0, wob in parts:
            age = (ph + f / frames) % 1.0
            cy = fh - 3 - age * (fh - 6)
            cx = fw / 2 + x0 + drift * age + 1.2 * math.sin(wob + age * 6.28)
            r = r0 + r1 * age
            dens = 0.8 * (1 - age) ** 0.8
            m, mx, my = L.ellipse_mask(cx, cy, r, r * 0.85)
            th = pg.bayer(m.shape[1], m.shape[0], mx, my)
            sel = m & (th < dens)
            col = cols[min(len(cols) - 1, int(age * len(cols)))]
            put(L, sel, mx, my, col)
        out.append(L)
    return strip(out)


def build_sprites() -> dict:
    """writes every prop / decal / actor sheet; returns {name: (w, h)} of single frames"""
    sz = {}

    def rec(name, L, frames=1):
        sz[name] = (L.w // frames, L.h)

    L = lamp_post(); save(L, 'props/lamp_post'); rec('lamp_post', L)
    L = tram_stop(); save(L, 'props/tram_stop'); rec('tram_stop', L)
    L = litfass(False); save(L, 'props/litfass'); rec('litfass', L)
    save_color(litfass(True), 'props/litfass_hist')
    L = loudspeaker(); save(L, 'props/loudspeaker'); rec('loudspeaker', L)
    L = banner_mast(); save(L, 'props/banner_mast'); rec('banner_mast', L)
    L = banner_near(False); save(L, 'props/banner_near'); rec('banner_near', L, 6)
    save_color(banner_near(True), 'props/banner_near_hist')
    L = vendor(); save(L, 'props/vendor'); rec('vendor', L)
    L = photographer(); save(L, 'props/photographer'); rec('photographer', L)
    L = children(False); save(L, 'props/children'); rec('children', L)
    save_color(children(True), 'props/children_hist')
    L = barrel_guard(); save(L, 'props/barrel_guard'); rec('barrel_guard', L)
    t0 = tank_frame(0)
    snowy = t0.alpha() & ~np.vstack([np.zeros((1, t0.w), bool), t0.alpha()[:-1]])
    t0.c[snowy] = W[3]
    save(t0, 'props/tank_parked'); rec('tank_parked', t0)
    L = rubble(5, 64, 30); save(L, 'props/rubble_a'); rec('rubble_a', L)
    L = rubble(9, 52, 24); save(L, 'props/rubble_b'); rec('rubble_b', L)
    L = notice_door(False); save(L, 'props/notice_door'); rec('notice_door', L)
    save_color(notice_door(True), 'props/notice_door_hist')
    L = window_life(); save(L, 'props/window_life', emission=True); rec('window_life', L, 8)
    for i, (w, seed) in enumerate(((112, 21), (68, 22), (72, 23), (164, 24), (108, 25), (80, 26), (90, 27))):
        L = crowd_strip(w, seed)
        save(L, 'props/crowd_%d' % (i + 1))
        rec('crowd_%d' % (i + 1), L, 4)
    # actor sheets
    L = strip([soldier_side(f) for f in range(8)])
    blocks = []
    files, ranks, dxf, dyr = 9, 4, 10, 3
    for f in range(8):
        s = soldier_side(f)
        B_ = Layer((files - 1) * dxf + (ranks - 1) + s.w, s.h + (ranks - 1) * dyr, 'block')
        for r in range(ranks - 1, -1, -1):
            for i in range(files):
                B_.blit(s, i * dxf + r, (ranks - 1 - r) * dyr)
        blocks.append(B_)
    L = strip(blocks); save(L, 'actors/march_block'); rec('march_block', L, 8)
    L = strip([standard_frame(f, False) for f in range(8)]); save(L, 'actors/standard'); rec('standard', L, 8)
    save_color(strip([standard_frame(f, True) for f in range(8)]), 'actors/standard_hist')
    L = strip([tank_frame(f) for f in range(4)]); save(L, 'actors/tank'); rec('tank', L, 4)
    L = puff_strip(12, 12, 1, 3, frames=6, r0=2.5, r1=2.0, drift=0); save(L, 'actors/exhaust_puff', normal=False)
    rec('exhaust_puff', L, 6)
    L = Layer(9, 9, 'flash')
    disc(L, 4.5, 4.5, 2.2, W[4])
    L.hline(0, 4, 9, W[3])
    L.vline(4, 0, 9, W[3])
    save(L, 'actors/flash', normal=False); rec('flash', L)
    # fx
    L = puff_strip(18, 46, 7, 41, cols=[V[3], W[0], V[2]], drift=5.0); save(L, 'fx/smoke', normal=False)
    rec('smoke', L, 8)
    L = puff_strip(12, 20, 5, 42, cols=[W[2], W[1], W[0]], drift=2.0, r0=0.8, r1=2.2)
    save(L, 'fx/steam', normal=False); rec('steam', L, 8)
    L = puff_strip(14, 24, 5, 43, cols=[V[2], V[3], W[0]], drift=-3.0, r0=1.2, r1=2.6)
    save(L, 'fx/exhaust', normal=False); rec('exhaust', L, 8)
    return sz


if __name__ == '__main__':
    print(build_sprites())
    print({k: v for k, v in OFF_PALETTE.items() if v})
