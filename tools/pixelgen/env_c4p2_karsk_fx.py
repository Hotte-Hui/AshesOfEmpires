"""env_c4p2_karsk_fx -- looping fx strips, light veils and actor sprites of L_C4P2_Karsk.

Strips (frames side by side): steam rolling out of the stall door and the smoke hoods, smoke from stove pipes and the
sand stove's chimney, the kasha pot / samovar steam, snow, coal dust drifting in the floodlight, sparks, the
brazier's embers, the sand stove's fire door, the barrel's flames (KarskBarrel actor), the shovels and the coal dust
behind the tarpaulin (scene B), heating steam leaking under the express.  Veils: the cones of the floodlights and
lamps in the haze (unlit, plain alpha).  Actor sprites: sparrows (KarskCrows frame layout), the yard dog (KarskCat
frame layout), breath puffs (KarskBreath), the far goods train (KarskTrain: loco, four wagon types, smoke puffs).
All palette-pure in 'depot', deterministic, seamless loops.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K
import env_c4p2_karsk_layout as L


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


def soft_alpha(a: np.ndarray, x0=0, y0=0, levels=(0, 70, 110, 150, 190)) -> np.ndarray:
    h, w = a.shape
    thr = K.pg.bayer(w, h, x0, y0, 4)
    lv = np.zeros((h, w), np.int32)
    for cut in (0.12, 0.3, 0.5, 0.72):
        lv += (a + (thr - 0.5) * 0.14 > cut)
    return np.array(levels, np.uint8)[lv]


# =========================================================================== particles
def particles(w, h, frames, fps, n, seed, kind='snow', vy=(4, 8), vx=(-1, 2), life=None, sway=1.0, spawn=None):
    """kind: snow | dust (warm specks in sodium light) | coal (dark grains) | spark (rising embers)."""
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        L_ = T if life is None else life
        ph = rng.uniform(0, L_)
        x0, y0 = spawn(rng) if spawn is not None else (rng.uniform(0, w), rng.uniform(0, h))
        v_y, v_x = rng.uniform(*vy), rng.uniform(*vx)
        sw = rng.uniform(0.3, 1.0) * sway
        sp = rng.uniform(0.4, 1.1)
        big = rng.random() < (0.15 if kind == 'snow' else 0.06)
        for k in range(frames):
            age = ((k / fps) + ph) % L_
            a = age / L_
            x = x0 + v_x * age + sw * math.sin(2 * math.pi * (age * sp) / max(0.5, L_) * 2 + i)
            y = y0 + v_y * age
            if kind == 'snow':
                y, x = y % h, x % w
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < w and 0 <= yi < h):
                continue
            fade = min(1.0, a / 0.15, (1 - a) / 0.2) if kind != 'snow' else 1.0
            if fade <= 0.05:
                continue
            if kind == 'snow':
                c = K.rgba('S', 6 if big else (5 if (i % 3) else 4))
            elif kind == 'dust':
                c = K.rgba('L', 5 if fade > 0.6 else 4, 210)
            elif kind == 'coal':
                c = K.rgba('X', 2 if fade > 0.5 else 3, 230)
            else:
                c = K.rgba('L', 5 if fade > 0.6 else (4 if fade > 0.3 else 3))
            out[k, yi, xi] = c
            if big and xi + 1 < w:
                out[k, yi, xi + 1] = c
    return strip(list(out))


def plume(w, h, frames, seed, ramp='V', dens=1.0, drift=0.6, tone=3.0, spread_k=0.35, rise_fade=3.0, up=True):
    """Seamless rising wisp / plume: dithered alpha, a lighter core, curling as it rises and thins."""
    out = np.zeros((frames, h, w, 4), np.uint8)
    per = h
    nz = K.periodic_noise(w, per * 2, 6, 9, seed, octaves=3, per_y=per)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    for k in range(frames):
        off = int(round(k / frames * per))
        n = np.roll(nz, -off if up else off, axis=0)[:h]
        rise = ys / h if up else 1 - ys / h          # 1 at the source (bottom)
        cx = w * 0.3 + (1 - rise) * drift * w * 0.12 * np.sin((ys / h) * 3 + k / frames * 2 * math.pi) \
            + (1 - rise) ** 1.4 * drift * w * 0.45
        spread = 1.5 + (1 - rise) * w * spread_k
        core = np.exp(-((xs - cx) ** 2) / (2 * spread ** 2))
        a = core * (0.2 + 0.8 * rise) * (0.45 + 1.1 * (n - 0.5) + 0.3) * dens
        a = np.clip(a, 0, 1) * np.clip(rise * rise_fade, 0, 1)
        alpha = soft_alpha(a, k * 3, 0, levels=(0, 40, 66, 92, 120))
        t = np.full((h, w), tone, np.float32) + core * 1.2
        out[k] = K.ramp_rgba(ramp, np.clip(t, 0, K.R.n(ramp) - 1), alpha, seed=seed)
    return strip(list(out))


def billow(w, h, frames, seed, ramp='V', tone=3.4, warm_k=0.0):
    """Steam rolling out of an open stall door and up the wall: a dense base that billows and climbs."""
    out = np.zeros((frames, h, w, 4), np.uint8)
    nz = K.periodic_noise(w, h * 2, 7, 7, seed, octaves=3, per_y=h)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    for k in range(frames):
        n = np.roll(nz, -int(round(k / frames * h)), axis=0)[:h]
        rise = ys / h                                                     # 1 at the door (bottom)
        cx = w * 0.35 + (1 - rise) * w * 0.25
        spread = w * (0.18 + (1 - rise) * 0.3)
        core = np.exp(-((xs - cx) ** 2) / (2 * spread ** 2))
        a = core * (0.4 + 0.9 * (n - 0.5) + 0.4) * np.clip(rise * 2.2, 0, 1) * np.clip((1 - rise) * 6 + 0.3, 0, 1)
        alpha = soft_alpha(np.clip(a, 0, 1), k * 2, 0, levels=(0, 54, 90, 126, 160))
        t = np.full((h, w), tone, np.float32) + core * 1.4 - (1 - rise) * 0.8
        img = K.ramp_rgba(ramp, np.clip(t, 0, K.R.n(ramp) - 1), alpha, seed=seed)
        if warm_k > 0:                                                    # lit from inside: the base warm
            warm = (ys > h * (1 - warm_k)) & (alpha > 0)
            img2 = K.ramp_rgba('L', np.clip(t - 0.4, 0, 5), alpha, seed=seed)
            img[np.broadcast_to(warm, alpha.shape)] = img2[np.broadcast_to(warm, alpha.shape)]
        out[k] = img
    return strip(list(out))


def flames(frames=8, w=14, h=18, seed=0):
    """Barrel fire (KarskBarrel: origin = rim centre; cell bottom on the rim): three separate tongues that lick up
    at their own pace and sway, a yellow-white root, orange bodies, thin red tips -- air between them, so the fire
    never reads as a block or a sign."""
    out = np.zeros((frames, h, w, 4), np.uint8)
    nz = K.periodic_noise(w, h * 2, 3, 3, seed, octaves=2, per_y=h)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    u = (h - 1 - ys) / float(h - 1)                                   # 0 on the rim, 1 at the top of the cell
    tongues = ((-3.6, 0.0, 0.62, 0.95), (0.0, 2.1, 1.0, 1.25), (3.4, 4.0, 0.72, 0.9))   # dx, phase, height, width
    for k in range(frames):
        ph = k / frames * 2 * math.pi
        lv = np.zeros((h, w), np.float32)
        for j, (dx, p0, hk, wk) in enumerate(tongues):
            top = hk * (0.72 + 0.28 * math.sin(ph * (1 + j % 2) + p0))
            rel = u / max(0.2, top)
            sway = math.sin(ph + p0 + 1.0) * 1.3 * rel
            cxk = w / 2.0 - 0.5 + dx + sway
            half = 2.1 * wk * np.clip(1 - rel, 0, 1) ** 0.8 + 0.25
            core = np.clip(1 - np.abs(xs - cxk) / half, 0, 1) * (rel <= 1.0)
            lv = np.maximum(lv, core * (1.15 - rel * 0.55))
        n = np.roll(nz, -int(round(k / frames * h)), axis=0)[:h]
        lv = lv * (0.78 + 0.5 * (n - 0.5))
        img = np.zeros((h, w, 4), np.uint8)
        img[lv > 0.2] = K.rgba('R', 4)
        img[lv > 0.45] = K.rgba('L', 4)
        img[lv > 0.74] = K.rgba('L', 5)
        out[k] = img
    return strip(list(out))


def glow_door(w, h, frames=8, seed=0):
    """A fire door / brazier: glowing bars breathing (emission strip)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((frames, h, w, 4), np.uint8)
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(w)]
    for k in range(frames):
        for x in range(w):
            v = 0.5 + 0.5 * math.sin(k / frames * 2 * math.pi * (1 + x % 2) + ph[x])
            for y in range(h):
                hot = y >= h - 1 - int(v * (h - 1))
                out[k, y, x] = K.rgba('L', 5 if (hot and v > 0.6) else (4 if hot else 3))
    return strip(list(out))


def shovels_over(w, h, frames=12, seed=0):
    """Behind the tarpaulin (scene B): two shovel blades swing up over its top edge in turn, coal flies, dust."""
    rng = np.random.default_rng(seed)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for k in range(frames):
        img = out[k]
        for j, (bx, ph) in enumerate(((10, 0.0), (w - 18, 0.5))):
            u = ((k / frames) + ph) % 1.0
            lift = math.sin(u * math.pi) if u < 0.5 else 0.0
            if lift > 0.15:
                top = int(round(h - 2 - lift * (h - 6)))
                for yy in range(top + 4, h):
                    img[yy, bx + 3] = K.rgba('D', 4)
                for yy in range(top, top + 4):
                    for xx in range(bx, bx + 6):
                        img[yy, xx] = K.rgba('I', 4 if yy == top else 3)
                if lift > 0.8:
                    for p in range(6):
                        x = bx + 2 + int(rng.integers(-3, 8))
                        y = top - int(rng.integers(1, 6))
                        if 0 <= x < w and 0 <= y < h:
                            img[y, x] = K.rgba('X', 3 + int(rng.integers(0, 3)))
        # a dust haze rising (dark, sparse)
        for p in range(14):
            x = int((p * 7 + k * 2 + seed) % w)
            y = int((h - 1 - ((k * 3 + p * 5) % h)))
            if rng.random() < 0.5:
                img[y, x] = K.rgba('X', 4, 200)
    return strip(list(out))


# =========================================================================== veils (light cones in the haze)
def veils(scene: str, cones, x0: int, w: int, h: int = L.WORLD_H):
    """cones: [(x, y, half_top, half_bot, y_bot, ramp, tone, k, dx)] in world px; dx tilts the cone."""
    out = np.zeros((h, w, 4), np.uint8)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xs += x0
    for (cx, cy, ht, hb, yb, ramp, tone, k, dx) in cones:
        f = np.clip((ys - cy) / max(1.0, yb - cy), 0, 1)
        half = ht + (hb - ht) * f
        ccx = cx + dx * f
        inside = (ys >= cy) & (ys <= yb)
        a = np.clip(1 - np.abs(xs - ccx) / np.maximum(1, half), 0, 1) ** 1.6 * (1 - f) ** 0.7 * inside * 0.42 * k
        a *= 0.75 + 0.25 * (K.noise(w, h, 18, int(cx) + 7) + 0.5)
        alpha = soft_alpha(a, 0, 0, levels=(0, 30, 48, 68, 90))
        rgba = K.ramp_rgba(ramp, np.full((h, w), float(tone), np.float32), alpha)
        m = alpha > out[..., 3]
        out[m] = rgba[m]
    return out


# =========================================================================== actor sprites
SPARROW_FRAMES = 11       # idle_a idle_b look caw preen hop takeoff fly_up fly_mid fly_down glide (KarskCrows layout)


def sparrows():
    """Sparrows in the KarskCrows layout (cell 14 x 12, feet at (6, 11), facing right): a plump brown bird."""
    cw, ch = 14, 12
    out = np.zeros((ch, cw * SPARROW_FRAMES, 4), np.uint8)
    BR, BRl, BRd, GR, BL, BK = K.rgba('D', 4), K.rgba('D', 5), K.rgba('D', 2), K.rgba('C', 4), K.rgba('N', 0), \
        K.rgba('L', 3)

    def put(f, pts, c):
        for (x, y) in pts:
            if 0 <= x < cw and 0 <= y < ch:
                out[y, f * cw + x] = c

    body = [(5, 8), (6, 8), (7, 8), (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (5, 10), (6, 10), (7, 10)]
    for f in range(SPARROW_FRAMES):
        dy = 0
        if f in (1,):
            dy = 0
        hx, hy = 8, 7
        if f == 2:                                                       # look round
            hx = 7
        if f == 4:                                                       # preen: head down to the wing
            hx, hy = 6, 8
        if f == 5:
            dy = -1
        if f >= 6:                                                       # flight frames
            yy = {6: -1, 7: -3, 8: -4, 9: -2, 10: -3}[f]
            put(f, [(x, y + yy) for (x, y) in body], BR)
            put(f, [(9, 7 + yy), (8, 7 + yy)], GR)
            wing_up = f in (6, 8, 10)
            if wing_up:
                put(f, [(5, 6 + yy), (6, 5 + yy), (7, 6 + yy)], BRd)
            else:
                put(f, [(5, 10 + yy), (6, 11 + yy), (7, 10 + yy)], BRd)
            put(f, [(10, 8 + yy)], BK)
            continue
        put(f, [(x, y + dy) for (x, y) in body], BR)
        put(f, [(5, 8 + dy), (6, 8 + dy)], BRl)
        put(f, [(4, 10 + dy), (3, 10 + dy)], BRd)                         # tail
        put(f, [(hx, hy + dy), (hx + 1, hy + dy), (hx, hy + 1 + dy)], GR)  # grey crown + head
        put(f, [(hx + 1, hy + 1 + dy)], BL)                              # eye
        put(f, [(hx + 2, hy + 1 + dy)] if f != 3 else [(hx + 2, hy + dy), (hx + 2, hy + 2 + dy)], BK)   # beak
        put(f, [(6, 11), (7, 11)] if f != 5 else [(6, 10), (7, 10)], BRd)  # feet
        if f == 1:
            put(f, [(6, 9), (7, 9)], BRl)
    return out


DOG_FRAMES = 7            # sleep_a sleep_b head_mid head_up blink ear tail (KarskCat layout, offset (-10, -10))


def dog():
    """A grey-brown yard dog curled up in the ash pit's warmth (cell 24 x 12, ground row 11, anchor (10, 10))."""
    cw, ch = 24, 12
    out = np.zeros((ch, cw * DOG_FRAMES, 4), np.uint8)
    em = np.zeros_like(out)
    lay_cols = {'b': K.rgba('C', 2), 'B': K.rgba('C', 3), 'd': K.rgba('N', 1), 'l': K.rgba('L', 1),
                'n': K.rgba('N', 0), 'e': K.rgba('L', 4), 'w': K.rgba('P', 5)}      # sooty grey, the fire on its back
    body = ['.......ddddddd..........',
            '.....ddBBBBBBBdl........',
            '...ddBBBBBBBBBBBdl......',
            '..dbBBBBBBBBBBBBBdl.....',
            '.dbbBBBBBBBBBBBBBBd.....',
            'dbbbbBBBBBBBBBBBBbbd....',
            'dbdbbbbbbbbbbbbbbbbd....',
            '.dd.ddddddddddddddd.....']
    heads = {      # the head resting on the paws at the front (right), one ear standing up
        'down': ['.d....', '.db...', 'dbBBd.', 'dBBBBdd', 'dbBBBBn', '.ddddd.'],
        'mid': ['.d....', 'dbd...', 'dBBBd.', 'dBeBBdd', 'dbBBBBn', '.ddddd.'],
        'up': ['d.d...', 'dbd...', 'dBBBd..', 'dBeBBBd', '.dbBBBn', '..dddd.'],
        'blink': ['d.d...', 'dbd...', 'dBBBd..', 'dBdBBBd', '.dbBBBn', '..dddd.'],
        'ear': ['dd....', 'dbd...', 'dBBBd..', 'dBeBBBd', '.dbBBBn', '..dddd.'],
    }

    def blit(f, pat, x0, y0, emis=False):
        for yy, row in enumerate(pat):
            for xx, ch_ in enumerate(row):
                if ch_ in lay_cols:
                    x, y = x0 + xx, y0 + yy
                    if 0 <= x < cw and 0 <= y < ch:
                        out[y, f * cw + x] = lay_cols[ch_]
                        if emis and ch_ == 'e':
                            em[y, f * cw + x] = lay_cols['e']

    for f in range(DOG_FRAMES):
        dy = 1 if f == 1 else 0                                          # breathing
        blit(f, body, 0, 4)
        if dy:
            blit(f, [body[1]], 0, 4)                                     # breathing: the flank rises a row
            blit(f, [body[0]], 0, 3)
        hk = {0: 'down', 1: 'down', 2: 'mid', 3: 'up', 4: 'blink', 5: 'ear', 6: 'up'}[f]
        blit(f, heads[hk], 16, 5 - (2 if hk in ('up', 'blink', 'ear') else (1 if hk == 'mid' else 0)), emis=True)
        tail = [(1, 11), (2, 11), (3, 10)] if f != 6 else [(0, 9), (1, 10), (2, 11)]   # the tail curled round
        for (x, y) in tail:
            out[y, f * cw + x] = lay_cols['B']
    return out, em


def breath_puff(frames=6, size=6):
    """A small pale puff that grows and fades (KarskBreath: square cells)."""
    out = np.zeros((size, size * frames, 4), np.uint8)
    for k in range(frames):
        r = 0.8 + k * 0.45
        a = 1.0 - k / float(frames)
        for y in range(size):
            for x in range(size):
                d = math.hypot(x - 1.5 - k * 0.35, y - size / 2.0 + 0.5)
                if d <= r and ((x + y + k) % 2 == 0 or a > 0.6):
                    out[y, k * size + x] = K.rgba('S', 5 if a > 0.6 else 4, int(200 * a + 30))
    return out


def train_parts():
    """The goods train on the far embankment (parallax 0.55), facing left: loco + tender, four wagon types,
    the smoke puff strip.  It has to read against the dark town at dawn: oxide-red box wagons, grey gondolas
    heaped with coal and snow, a black tank wagon with its white band, a flat wagon with crates under snow; every
    roof and load white with snow along its top edge, the dawn's rim light on the right-hand (east) ends; the loco
    black with a red buffer beam and red wheels, the firebox glow in the cab, a lit headlamp."""
    def canvas(w, h):
        return np.zeros((h, w, 4), np.uint8)

    def rect(img, x, y, w, h, c):
        img[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = c

    N1, N2, N3 = K.rgba('N', 1), K.rgba('N', 2), K.rgba('N', 3)
    I2, I3, I4 = K.rgba('I', 2), K.rgba('I', 3), K.rgba('I', 4)
    S6, S5, S4, S3 = K.rgba('S', 6), K.rgba('S', 5), K.rgba('S', 4), K.rgba('S', 3)
    L5, L4, L3 = K.rgba('L', 5), K.rgba('L', 4), K.rgba('L', 3)
    K3, K4, K5 = K.rgba('K', 3), K.rgba('K', 4), K.rgba('K', 5)
    R2, R3 = K.rgba('R', 2), K.rgba('R', 3)
    X2, X4 = K.rgba('X', 2), K.rgba('X', 4)
    C3, C4 = K.rgba('C', 3), K.rgba('C', 4)
    P5 = K.rgba('P', 5)
    loco = canvas(62, 20)
    rect(loco, 4, 7, 30, 9, N3)                       # boiler
    rect(loco, 4, 7, 30, 1, I4)                       # its top catches the sky
    rect(loco, 4, 11, 30, 1, I2)                      # a handrail
    rect(loco, 6, 2, 4, 5, N3)                        # chimney
    rect(loco, 6, 2, 4, 1, S5)
    rect(loco, 16, 4, 5, 3, N3)                       # dome
    rect(loco, 16, 4, 5, 1, S4)
    rect(loco, 32, 3, 12, 13, N3)                     # cab
    rect(loco, 31, 2, 14, 1, S5)
    rect(loco, 35, 6, 5, 4, L4)                       # firelight in the cab window
    rect(loco, 36, 7, 3, 2, L5)
    rect(loco, 33, 13, 10, 2, L3)                     # the fire's glow under the cab
    rect(loco, 2, 15, 44, 2, N1)                      # frame
    rect(loco, 0, 13, 3, 3, R3)                       # red buffer beam
    rect(loco, 46, 7, 16, 9, N3)                      # tender, coal heaped under snow
    rect(loco, 47, 5, 14, 2, X4)
    rect(loco, 46, 5, 16, 1, S5)
    rect(loco, 61, 7, 1, 9, I4)                       # the dawn's rim on the east end
    for x in (8, 15, 22, 29, 50, 57):
        rect(loco, x - 2, 16, 5, 4, R2)               # red wheels
        loco[18, x] = I4
    rect(loco, 1, 9, 3, 3, L5)                        # headlamp, lit
    loco[10, 0] = S6
    wag = {}
    for kind in ('box', 'gond', 'tank', 'flat'):
        img = canvas(36, 18)
        if kind == 'box':                             # oxide red, planked, the door, snow on the roof
            rect(img, 1, 3, 34, 11, K4)
            for x in range(3, 34, 4):
                rect(img, x, 4, 1, 10, K3)
            rect(img, 14, 5, 8, 9, K3)
            rect(img, 14, 5, 8, 1, K5)
            rect(img, 1, 2, 34, 1, S5)
            rect(img, 2, 1, 32, 1, S4)
            rect(img, 34, 3, 1, 11, K5)               # the dawn's rim on the east end
        elif kind == 'gond':                          # grey steel sides, heaped coal, snow on the heap
            rect(img, 1, 7, 34, 7, I3)
            for x in range(4, 34, 6):
                rect(img, x, 7, 1, 7, I2)
            rect(img, 1, 7, 34, 1, I4)
            rect(img, 3, 4, 30, 3, X2)
            rect(img, 6, 3, 22, 1, X4)
            rect(img, 8, 2, 18, 1, S5)
            rect(img, 4, 4, 4, 1, S4)
            rect(img, 34, 7, 1, 7, I4)
        elif kind == 'tank':                          # black tank, a white band, snow along the top
            rect(img, 3, 5, 30, 8, N3)
            rect(img, 3, 9, 30, 1, P5)
            rect(img, 3, 4, 30, 1, S5)
            rect(img, 4, 6, 28, 1, I3)
            rect(img, 16, 2, 4, 3, N3)
            rect(img, 16, 2, 4, 1, S4)
            rect(img, 32, 5, 1, 8, I4)
        else:                                         # flat wagon with crates under snow
            rect(img, 1, 11, 34, 3, I3)
            rect(img, 6, 6, 22, 5, C3)
            rect(img, 16, 6, 1, 5, C4)
            rect(img, 6, 5, 22, 1, S5)
            rect(img, 7, 4, 20, 1, S4)
        rect(img, 0, 14, 36, 1, N1)
        for x in (6, 12, 24, 30):
            rect(img, x - 2, 15, 5, 3, N2)
            img[16, x] = I4
        wag[kind] = img
    puff = np.zeros((18, 18 * 8, 4), np.uint8)
    for k in range(8):
        r = 2.5 + k * 0.9
        a = 1.0 - k / 8.0
        for y in range(18):
            for x in range(18):
                d = math.hypot(x - 9, y - 10 + k * 0.4)
                if d <= r and ((x * 3 + y * 5 + k) % 4 != 0 or a > 0.7):
                    tone = 5 if d < r * 0.45 else (4 if d < r * 0.8 else 3)
                    puff[y, k * 18 + x] = K.rgba('V', tone, int(190 * a + 50))
    return loco, wag, puff
