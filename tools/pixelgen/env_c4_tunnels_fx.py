"""env_c4_tunnels_fx -- outside layer, light veils, looping life strips and event strips of L_C4_Tunnels.

All palette-pure in 'tunnels' (env_c4_tunnels_kit.TUN).  Looping strips are seamless (particles live on the loop),
deterministic (fixed seeds), slow (<= 12 fps) and never flash.  Event strips (dust falling from the vault, the
train crossing the freight yard above, the swinging lamps) are driven by scripts/levels/c4/tunnels_level.gd.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_tunnels_kit as K
import env_c4_tunnels_layout as L
import pixel_fire_bake as PFB


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


def _put(img, x, y, c):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        img[y, x] = c


def soft_alpha(a: np.ndarray, x0=0, y0=0, levels=(0, 70, 110, 150, 190)) -> np.ndarray:
    """Quantised, ordered-dithered alpha (5 levels) for veils."""
    h, w = a.shape
    thr = K.pg.bayer(w, h, x0, y0, 4)
    lv = np.zeros((h, w), np.int32)
    for cut in (0.12, 0.3, 0.5, 0.72):
        lv += (a + (thr - 0.5) * 0.14 > cut)
    return np.array(levels, np.uint8)[lv]


# =========================================================================== outside (behind the cellar windows)
def outside(windows, w=L.WORLD_W, h=L.WORLD_H):
    """The freight yard at ground level seen through the high cellar windows: night, snow heaped against the
    glass, the yard lamp's glow (second window), a fence post.  Unlit plain layer."""
    out = np.zeros((h, w, 4), np.uint8)
    for i, (x0, y0, x1, y1) in enumerate(windows):
        ww, hh = x1 - x0 + 4, y1 - y0 + 4
        X0, Y0 = x0 - 2, y0 - 2
        t = np.zeros((hh, ww), np.float32)
        ys = np.arange(hh, dtype=np.float32)[:, None]
        t[:] = 1.0 + 1.6 * (ys / hh)                                        # sky -> snow glow
        rgba = K.ramp_rgba('N', np.clip(t, 0, 3), np.full((hh, ww), 255, np.uint8), seed=i)
        # snow ground: the lower third, a heap against the glass
        prof = (hh * 0.62 + 3 * np.sin(np.arange(ww) / 5.0 + i) - 2 * (np.arange(ww) / ww)).astype(int)
        for xx in range(ww):
            for yy in range(max(0, prof[xx]), hh):
                k = (yy - prof[xx]) / max(1, hh - prof[xx])
                tone = 2.4 + 1.6 * (1 - k) + (0.6 if yy == prof[xx] else 0.0)
                rgba[yy, xx] = K.rgba('S', int(np.clip(round(tone), 0, 6)))
        if i == 1:
            # the yard lamp: post at the right, warm glow on the snow, cone of falling-snow light
            px = ww - 8
            for yy in range(0, prof[px]):
                rgba[yy, px] = K.rgba('N', 0)
            rgba[2:4, px - 4:px + 1] = K.rgba('I', 2)
            rgba[4, px - 3:px] = K.rgba('L', 5)
            for yy in range(5, hh):
                for xx in range(ww):
                    d = math.hypot((xx - (px - 2)) / 1.4, yy - 5)
                    if d < 16 and (xx + yy) % 2 == 0 and yy >= prof[xx] - 1:
                        rgba[yy, xx] = K.rgba('L', 3 if d < 8 else 2)
                    elif d < 10 and yy < prof[xx] and (xx * 3 + yy) % 5 == 0:
                        rgba[yy, xx] = K.rgba('L', 1)
        else:
            # a fence post and the dark bulk of a wagon on the yard track
            for yy in range(4, prof[6] + 1):
                rgba[yy, 6:8] = K.rgba('N', 0)
            rgba[2:9, 14:ww] = K.rgba('V', 1)
            rgba[9:11, 14:ww] = K.rgba('N', 0)
        out[Y0:Y0 + hh, X0:X0 + ww] = rgba
    return out


# =========================================================================== particles
def particles(w, h, frames, fps, n, seed, kind='dust', spawn=None, vy=(-2, 2), vx=(-2, 2), life=None, sway=2.0):
    """Looping particle strip.  kind 'snow' (falling flakes, cold) | 'dust' (slow drift, warm lamp dust) |
    'dust_cold' (drift in the work-lamp light) | 'paint' (red-brown mist specks)."""
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
        big = rng.random() < (0.15 if kind == 'snow' else 0.05)
        for k in range(frames):
            age = ((k / fps) + ph) % L_
            a = age / L_
            x = x0 + v_x * age + sw * math.sin(2 * math.pi * (age * sp) / max(0.5, L_) * 2 + i)
            y = y0 + v_y * age
            if kind == 'snow':
                y = y % h
                x = x % w
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < w and 0 <= yi < h):
                continue
            fade = min(1.0, a / 0.15, (1 - a) / 0.2)
            if fade <= 0.05:
                continue
            if kind == 'snow':
                c = K.rgba('S', 5 if big else (4 if fade > 0.5 else 3))
            elif kind == 'dust':
                c = K.rgba('L', 5 if fade > 0.6 else 4, 220)
            elif kind == 'dust_cold':
                c = K.rgba('S', 5 if fade > 0.6 else 4, 200)
            else:
                c = K.rgba('V', 4 if fade > 0.6 else 3, 170)
            out[k, yi, xi] = c
            if big and xi + 1 < w:
                out[k, yi, xi + 1] = c
    return strip(list(out))


def steam_wisp(w, h, frames, seed, dens=1.0, ramp='S', drift=0.6):
    """Seamless rising wisp (steam from the samovar, the leaking flange; thin smoke from a stove pipe).  Round
    13: pixel fire kit (pixel_fire_bake.wisp) -- hard-pixel puffs in three tones of the ramp that swell, climb
    and break up through the ordered dither, no soft alpha."""
    tones = tuple('#%02X%02X%02X' % tuple(int(v) for v in K.rgba(ramp, i)[:3]) for i in (3, 4, 5))
    return strip(PFB.wisp(w, h, frames, seed, tones, drift=drift))


def drip(h, frames=30, fps=10, seed=0, w=11):
    """A drop swells under the vault, falls (accelerating), splashes into the puddle, rings spread.  Seamless."""
    out = np.zeros((frames, h, w, 4), np.uint8)
    cx = w // 2
    rng = np.random.default_rng(seed)
    t_form, t_fall = int(frames * 0.55), max(3, int(frames * 0.12))
    for k in range(frames):
        img = out[k]
        if k < t_form:                                                      # swelling drop
            s = k / t_form
            img[0, cx] = K.rgba('S', 3)
            if s > 0.35:
                img[1, cx] = K.rgba('S', 4)
            if s > 0.7:
                img[2, cx] = K.rgba('S', 5)
        elif k < t_form + t_fall:                                           # falling
            f = (k - t_form + 1) / t_fall
            y = int(round(2 + (h - 6) * f * f))
            for j in range(3):
                _put(img, cx, y - j, K.rgba('S', 5 - j, 255 if j == 0 else 170))
        else:                                                               # splash + ring
            f = (k - t_form - t_fall) / max(1, frames - t_form - t_fall)
            by = h - 3
            if f < 0.25:
                for dx in (-2, -1, 1, 2):
                    _put(img, cx + dx, by - 1 - (abs(dx) == 1), K.rgba('S', 5))
                _put(img, cx, by - 3, K.rgba('S', 6))
            r = int(round(1 + f * (w // 2 - 1)))
            col = K.rgba('S', 5 if f < 0.5 else 4, int(220 * (1 - f) + 35))
            for dx in range(-r, r + 1):
                if abs(abs(dx) - r) < 1:
                    _put(img, cx + dx, by + 1, col)
            _put(img, cx - r, by + 1, col)
            _put(img, cx + r, by + 1, col)
    return strip(list(out))


def flame(frames=8, w=5, h=6, seed=0):
    """Kerosene flame in its glass chimney: a tiny tongue that leans and breathes (emission strip)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((frames, h, w, 4), np.uint8)
    cx = w // 2
    for k in range(frames):
        lean = int(round(math.sin(k / frames * 2 * math.pi) * 0.6))
        tall = 3 + (1 if k % 3 == 0 else 0)
        for j in range(tall):
            y = h - 1 - j
            x = cx + (lean if j >= 2 else 0)
            out[k, y, x] = K.rgba('L', 5 if j < tall - 1 else 4)
        out[k, h - 1, cx - 1] = K.rgba('L', 3)
        out[k, h - 1, cx + 1] = K.rgba('L', 3)
    return strip(list(out))


def vents(frames=8, seed=0):
    """The stove door's four vent slits: the fire behind them breathes (emission strip, 18 x 7)."""
    rng = np.random.default_rng(seed)
    w, h = 18, 7
    out = np.zeros((frames, h, w, 4), np.uint8)
    lv = [rng.uniform(0, 2 * math.pi) for _ in range(4)]
    for k in range(frames):
        for s in range(4):
            v = 0.5 + 0.5 * math.sin(k / frames * 2 * math.pi * (1 + s % 2) + lv[s])
            x = 3 + s * 4
            for y in range(1, 7):
                hot = (y > 6 - 2 - int(v * 3))
                c = K.rgba('L', 5 if hot and v > 0.6 else (4 if hot else 3))
                out[k, y - 1, x:x + 2] = c
            out[k, 5, x] = K.rgba('R', 3)
    return strip(list(out))


def embers(holes, w, h, frames=12, seed=0):
    """The brazier's holes glowing and dimming one by one (emission strip, never all at once)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((frames, h, w, 4), np.uint8)
    ph = [rng.uniform(0, 2 * math.pi) for _ in holes]
    for k in range(frames):
        for i, (hx, hy) in enumerate(holes):
            v = 0.5 + 0.5 * math.sin(k / frames * 2 * math.pi * (1 + i % 2) + ph[i])
            c = K.rgba('L', 4 if v > 0.66 else 3) if v > 0.25 else K.rgba('R', 3)
            out[k, hy:hy + 2, hx:hx + 2] = c
    return strip(list(out))


def pendulum(frames=12):
    """The wall clock's pendulum in its window (8 x 13), one beat per second."""
    w, h = 8, 13
    out = np.zeros((frames, h, w, 4), np.uint8)
    for k in range(frames):
        ang = math.sin(k / frames * 2 * math.pi) * 0.32
        for j in range(10):
            x = int(round(w / 2 - 0.5 + math.sin(ang) * j))
            out[k, j, x] = K.rgba('L', 3)
        bx = int(round(w / 2 - 0.5 + math.sin(ang) * 10))
        for dy in range(3):
            for dx in (-1, 0, 1):
                if 0 <= bx + dx < w:
                    out[k, 10 + dy, bx + dx] = K.rgba('L', 4 if dx < 1 and dy == 0 else 3)
    return strip(list(out))


def feet(w, h, frames=96):
    """The night shift passing the cellar window: felt boots in the snow, two men, a pause between."""
    out = np.zeros((frames, h, w, 4), np.uint8)
    ground = int(h * 0.62)
    walkers = [(6, 40, 1, 'N', 0), (54, 86, -1, 'I', 1)]    # (first frame, last frame, direction, ramp, tone)
    for (f0, f1, dr, ramp, tone) in walkers:
        for k in range(f0, f1):
            p = (k - f0) / (f1 - f0)
            x = int(round(-8 + p * (w + 16))) if dr > 0 else int(round(w + 8 - p * (w + 16)))
            for leg in (0, 1):
                ph = math.sin(k * 0.9 + leg * math.pi)
                lx = x + int(round(ph * 3)) + leg * 2
                lift = max(0, int(round(ph * 2))) if leg == (k % 2) else 0
                for yy in range(0, ground - lift):
                    for dx in range(3):
                        _put(out[k], lx + dx, yy, K.rgba(ramp, tone + (dx == 0)))
                for dx in range(-1 if dr < 0 else 0, 5 if dr > 0 else 4):        # boot
                    _put(out[k], lx + dx, ground - lift - 1, K.rgba('N', 1))
                    _put(out[k], lx + dx, ground - lift, K.rgba('N', 0))
                if lift == 0 and ph < -0.8:                                      # snow kicked up
                    _put(out[k], lx + (4 if dr > 0 else -2), ground - 2, K.rgba('S', 4))
    return strip(list(out))


def snow_gate(w=70, h=26, frames=24, fps=10, seed=0):
    """Snow blowing in under the shut portal gate (from the right), skittering along the floor."""
    return particles(w, h, frames, fps, 26, seed, kind='snow', vy=(-1, 3), vx=(-34, -16), sway=1.0,
                     spawn=lambda r: (r.uniform(w - 6, w), r.uniform(h - 10, h - 1)))


# =========================================================================== light veils (static, plain alpha)
def veils(w=L.WORLD_W, h=L.WORLD_H):
    """Soft cones under the lamps (bulb over the wagon, the work lamps, the hanging lamp and Lev's lamp) and the
    faint paint haze of the siding.  Unlit, plain alpha, drawn above the room."""
    out = np.zeros((h, w, 4), np.uint8)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)

    def cone(x, y, half_top, half_bot, y_bot, ramp, tone, k=1.0):
        f = np.clip((ys - y) / max(1.0, y_bot - y), 0, 1)
        half = half_top + (half_bot - half_top) * f
        inside = (ys >= y) & (ys <= y_bot)
        a = np.clip(1 - np.abs(xs - x) / np.maximum(1, half), 0, 1) ** 1.6 * (1 - f) ** 0.8 * inside * 0.42 * k
        return a

    layers = [
        (cone(L.BULB[0], L.BULB[1] + 2, 3, 70, 292, 'P', 6), 'P', 6),
        (cone(L.WORK_LAMPS[0][0] + 6, L.WORK_LAMPS[0][1] + 8, 6, 90, 290, 'S', 5) * 0.8, 'S', 5),
        (cone(L.WORK_LAMPS[1][0] - 6, L.WORK_LAMPS[1][1] + 8, 6, 80, 290, 'S', 5) * 0.7, 'S', 5),
        (cone(L.HANG_LAMP[0], L.HANG_LAMP[1] + 4, 4, 52, 286, 'L', 5) * 0.7, 'L', 5),
        (cone(L.GREEN_LAMP[0], L.GREEN_LAMP[1] + 2, 10, 28, 262, 'L', 5) * 0.8, 'L', 5),
    ]
    # composite per layer in order (the denser veil wins)
    for (a, ramp, tone) in layers:
        alpha = soft_alpha(a, 0, 0, levels=(0, 34, 54, 76, 100))
        rgba = K.ramp_rgba(ramp, np.full((h, w), float(tone), np.float32), alpha)
        m = alpha > out[..., 3]
        out[m] = rgba[m]
    # paint haze around the stand and the wagon: a low band, red-brown/paper, very faint
    hz = np.clip(1 - np.abs(ys - 236) / 46.0, 0, 1) * np.clip(1 - np.abs(xs - 1560) / 170.0, 0, 1)
    hz *= 0.55 + 0.45 * K.noise(w, h, 26, 701)
    alpha = soft_alpha(hz * 0.5, 0, 0, levels=(0, 26, 40, 54, 70))
    rgba = K.ramp_rgba('V', np.full((h, w), 4.0, np.float32), alpha)
    m = (alpha > 0) & (out[..., 3] < alpha)
    out[m] = rgba[m]
    return out


# =========================================================================== swinging lamps (7 swing frames)
SWING_FRAMES = 7          # frame 3 = at rest; frames 0..6 = bottom displaced -3..+3 px


def hang_lamp(cord=104):
    """Enamel shade on a cord from the cellar vault: dark green outside, white inside, the bulb (emission map).
    Returns (rgba strip, emission strip); frame width 17, height cord + 9."""
    w, h = 17, cord + 9
    frames, em = [], []
    for f in range(SWING_FRAMES):
        d = f - 3
        img = np.zeros((h, w, 4), np.uint8)
        e = np.zeros((h, w, 4), np.uint8)
        for y in range(cord):
            x = int(round(w // 2 + d * (y / cord)))
            img[y, x] = K.rgba('N', 1)
        bx = w // 2 + d
        for j, half in enumerate((2, 3, 4, 5, 6, 7)):                     # shade, green enamel
            y = cord + j
            for x in range(bx - half, bx + half + 1):
                if 0 <= x < w:
                    img[y, x] = K.rgba('G', 3 if x < bx else 2)
            if 0 <= bx - half < w:
                img[y, bx - half] = K.rgba('G', 4)
        y = cord + 6
        for x in range(bx - 6, bx + 7):                                   # white inner rim (lit)
            if 0 <= x < w:
                img[y, x] = K.rgba('P', 5)
                e[y, x] = K.rgba('P', 5)
        for (x, y) in ((bx - 1, cord + 7), (bx, cord + 7), (bx + 1, cord + 7), (bx, cord + 8)):
            img[y, x] = K.rgba('L', 5)
            e[y, x] = K.rgba('L', 5)
        frames.append(img)
        em.append(e)
    return strip(frames), strip(em)


def wagon_bulb(cord=112):
    """The single bulb over the wagon: cord from the vault, a small tin shade, a bare bright bulb."""
    w, h = 15, cord + 8
    frames, em = [], []
    for f in range(SWING_FRAMES):
        d = f - 3
        img = np.zeros((h, w, 4), np.uint8)
        e = np.zeros((h, w, 4), np.uint8)
        for y in range(cord):
            x = int(round(w // 2 + d * (y / cord)))
            img[y, x] = K.rgba('N', 1)
        bx = w // 2 + d
        for j, half in enumerate((1, 3, 5)):
            y = cord + j
            for x in range(bx - half, bx + half + 1):
                if 0 <= x < w:
                    img[y, x] = K.rgba('I', 3 if x < bx else 2)
        for (x, y, t) in ((bx - 1, cord + 3, 5), (bx, cord + 3, 6), (bx + 1, cord + 3, 5), (bx - 1, cord + 4, 6),
                          (bx, cord + 4, 6), (bx + 1, cord + 4, 6), (bx, cord + 5, 5)):
            img[y, x] = K.rgba('P', t)
            e[y, x] = K.rgba('P', t)
        frames.append(img)
        em.append(e)
    return strip(frames), strip(em)


# =========================================================================== event strips
def dust_fall(w=40, h=120, frames=16, fps=10, seed=0):
    """Grit and dust shaken from the vault by a train overhead: streams that thin out (played once)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((frames, h, w, 4), np.uint8)
    streams = [(rng.uniform(4, w - 4), rng.uniform(0.7, 1.0), rng.uniform(0, 3)) for _ in range(6)]
    grains = []
    for (sx, strength, delay) in streams:
        for _ in range(int(34 * strength)):
            grains.append((sx + rng.normal(0, 1.6), rng.uniform(0, 0.6) + delay / fps, rng.uniform(70, 140),
                           rng.random() < 0.3))
    for k in range(frames):
        t = k / fps
        for (gx, t0, g, big) in grains:
            if t < t0:
                continue
            dt = t - t0
            y = int(round(0.5 * g * dt * dt))
            x = int(round(gx + 0.6 * math.sin(dt * 7 + gx)))
            if 0 <= y < h and 0 <= x < w:
                out[k, y, x] = K.rgba('C', 6 if big else 5, 240)
                if big and x + 1 < w:
                    out[k, y, x + 1] = K.rgba('C', 4, 200)
        # a dust veil puff near the top, fading
        a = max(0.0, 1 - k / (frames * 0.7))
        for yy in range(0, 16):
            for xx in range(w):
                if (xx * 7 + yy * 3 + k) % 6 == 0 and a > 0.2 and yy < 16 * a:
                    out[k, yy, xx] = K.rgba('C', 5, int(150 * a))
    return strip(list(out))


def train_top(n_wagons=6, wl=118):
    """The underframes of a freight train rolling over the yard above (only the bottom rows show in the section:
    wheels on the rail, axle boxes, the dark bottoms of the wagons, couplings).  Wide single image."""
    gap = 6
    w = n_wagons * (wl + gap)
    h = 18
    img = np.zeros((h, w, 4), np.uint8)
    for i in range(n_wagons):
        x0 = i * (wl + gap)
        ramp, tone = (('V', 1) if i % 3 != 1 else ('I', 1))
        img[0:9, x0:x0 + wl] = K.rgba(ramp, tone)                              # wagon bottom
        img[8, x0:x0 + wl] = K.rgba('N', 1)
        img[9:11, x0 + 4:x0 + wl - 4] = K.rgba('N', 0)                         # frame
        for bx in (x0 + 18, x0 + wl - 18):
            for wx in (bx - 6, bx + 6):                                          # bogie wheels
                for yy in range(11, 18):
                    for xx in range(wx - 3, wx + 4):
                        if (xx - wx) ** 2 + (yy - 14.5) ** 2 <= 12:
                            img[yy, xx] = K.rgba('N', 0)
                img[14, wx] = K.rgba('I', 3)
            img[11:13, bx - 9:bx + 10] = K.rgba('N', 1)
        img[9, x0 + wl:x0 + wl + gap] = K.rgba('I', 2)                          # coupling
    return img
