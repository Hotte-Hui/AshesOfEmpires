"""env_c4_annex_fx -- looping strips (layer_stack: hframes = frames) of L_C4_Annex: ambient life of both scenes.

Street (B): snow in two depths, warm air steaming out of the grate of S 2, the lorry's exhaust, chimney smoke of
No. 11, Ilse on the last bench of tram 74 (looks out, breathes on the glass, wipes a peephole with her mitten),
the red blinker on the hoarding, the aviation lights of the cranes.  Annex (D): the two fans turning behind the
grille, dust in the fan light, a capsule shooting through the glass length of the tube, a failing tube, the two
typists behind the glass.  Every strip loops seamlessly (particles live exactly one loop, rotations step through
a symmetric period); colours are palette-pure ('annex' + lamp); no strip pulses its overall brightness faster
than 1 Hz (the blinkers are 1 Hz, the failing tube drops out for two frames in three seconds).
Frames that sit on top of the baked room (Ilse, fans, typists, tube, capsule) start from an exact crop of the
baked layer, so only the moving thing changes.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_annex_kit as K
import pg

R = K.R


def _px(arr, x, y, col):
    h, w = arr.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        arr[y, x] = col


# =========================================================================== particles
def snow_strip(w, h, frames=24, fps=8, n=110, seed=0, ground=None):
    """Falling snow, two depths: far flakes 1 px slow, near flakes 2 px faster with a little sway.  Each flake
    lives one loop and fades at both ends (so the loop never shows a jump)."""
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        near = rng.random() < 0.3
        v = rng.uniform(26, 36) if near else rng.uniform(12, 20)
        vx = rng.uniform(-3, 1.5)
        x0, y0 = rng.uniform(0, w), rng.uniform(-v * T * 0.3, h)
        ph = rng.uniform(0, T)
        sw = rng.uniform(0.5, 1.6) * (2.0 if near else 1.0)
        for k in range(frames):
            age = ((k / fps) + ph) % T
            a = age / T
            fade = min(1.0, a / 0.18, (1 - a) / 0.18)
            if fade < 0.25:
                continue
            x = int(round(x0 + vx * age + sw * math.sin(2 * math.pi * age / T + i))) % w
            y = int(round(y0 + v * age))
            if ground is not None and y >= ground[min(w - 1, x)]:
                continue
            if near:
                col = K.rgba('SN', 7 if fade > 0.6 else 5)
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if dx + dy < 2 or fade > 0.7:
                        _px(out[k], x + dx, y + dy, col)
            else:
                _px(out[k], x, y, K.rgba('SN', 6 if fade > 0.6 else 4))
    return K.strip(list(out))


def dust_strip(w, h, frames=32, fps=6, n=40, seed=0, ramp='G', tones=(5, 4), drift=(-2, 2), rise=(-3, 3)):
    """Dust motes drifting in a light (very slow, faint)."""
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        vx, vy = rng.uniform(*drift), rng.uniform(*rise)
        ph = rng.uniform(0, T)
        for k in range(frames):
            age = ((k / fps) + ph) % T
            a = age / T
            fade = min(1.0, a / 0.3, (1 - a) / 0.3)
            if fade < 0.35:
                continue
            x = int(round(x0 + vx * age + math.sin(age * 1.7 + i))) % w
            y = int(round(y0 + vy * age)) % h
            col = K.rgba(ramp, tones[0] if fade > 0.7 else tones[1])
            col[3] = 200 if fade > 0.7 else 130
            _px(out[k], x, y, col)
    return K.strip(list(out))


def plume_strip(w, h, frames=16, seed=0, ramp='SN', base=4.0, dens=1.0, drift=0.0, warm_root=False):
    """Steam / smoke rising from the bottom centre, soft alpha in four levels, periodic noise scrolled one
    period per loop."""
    P = frames * 3
    nz = K.periodic_noise(w, P, 8, 10, seed, octaves=3, per_y=P)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    fr = []
    for k in range(frames):
        sh = (np.arange(h)[:, None] + k * 3) % P
        n = nz[sh, np.arange(w)[None, :]]
        up = 1 - ys / h                                         # 0 at the bottom .. 1 at the top
        cx = w / 2 + drift * up * w * 0.4 + (n - 0.5) * 4 * up
        width = (0.18 + 0.5 * up) * w / 2
        shape = np.clip(1 - np.abs(xs - cx) / np.maximum(1.0, width), 0, 1) ** 0.8
        shape *= np.clip(1.2 - up, 0, 1) * np.clip(ys / (h * 0.1) + 0.2, 0, 1)
        a = shape * (0.25 + 1.2 * (n - 0.3)) * dens
        thr = pg.bayer(w, h, k, 0, 4)
        level = np.zeros((h, w), np.int32)
        for cut in (0.16, 0.36, 0.6):
            level += (a + (thr - 0.5) * 0.2 > cut)
        alpha = np.array([0, 50, 92, 140], np.uint8)[level]
        tone = base + (n - 0.5) * 1.6 + level * 0.4
        col = K.ramp_rgba(ramp, tone.astype(np.float32), alpha, seed=k)
        if warm_root:
            root = (ys > h * 0.82) & (alpha > 0) & ((thr + (ys - h * 0.82) / (h * 0.18)) > 1.0)
            warm = K.ramp_rgba('L', np.full((h, w), 3.4, np.float32), alpha, seed=k)
            col[root] = warm[root]
        fr.append(col)
    return K.strip(fr)


def blink_strip(w, h, on: np.ndarray, frames=4, on_frames=(0, 1)):
    """A lamp that is on in `on_frames` and dark otherwise (`on` = RGBA of the lit lamp, transparent = off)."""
    fr = []
    for k in range(frames):
        fr.append(on.copy() if k in on_frames else np.zeros_like(on))
    return K.strip(fr)


# =========================================================================== Ilse in the last window
def ilse_strip(base: np.ndarray, frames=48, fps=6):
    """Ilse (8) on the last bench, the satchel on her lap, seen through the fogged window (crop `base` of the
    baked street).  Loop: sits and looks ahead -> turns to the glass -> breathes on it -> wipes a peephole
    with her mitten -> looks out -> the peephole fogs over again."""
    h, w = base.shape[:2]
    out = []
    coat = K.rgba('D', 2.0)
    coat_hi = K.rgba('D', 3.0)
    hair = K.rgba('P', 1.4)
    skin = K.rgba('Y', 1.6)
    skin_sh = K.rgba('Y', 0.6)
    sat = K.rgba('L', 1.4)
    mitt = K.rgba('R', 2.4)
    fogc = K.rgba('L', 4.4)
    for k in range(frames):
        fr = base.copy()
        t = k / frames
        turned = 0.18 < t < 0.85
        wipe = 0.42 < t < 0.58
        hole = 0.5 < t < 0.92
        cx = w // 2 + 2
        # coat (seated, profile to the left), satchel on the lap
        for y in range(h - 11, h):
            for x in range(cx - 4, cx + 3):
                fr[y, x] = coat
        fr[h - 11, cx - 4:cx + 3] = coat_hi
        for y in range(h - 7, h - 3):
            for x in range(cx - 8, cx - 2):
                fr[y, x] = sat
        # head: back of the head (looking ahead = to the left) or turned to the glass (towards the viewer)
        hy = h - 17
        for y in range(hy, hy + 6):
            for x in range(cx - 3, cx + 2):
                fr[y, x] = hair
        if turned:
            fr[hy + 2:hy + 5, cx - 3:cx] = skin
            fr[hy + 4, cx - 3:cx] = skin_sh
        else:
            fr[hy + 2:hy + 5, cx - 4] = skin
        fr[hy - 1, cx - 2:cx + 1] = hair
        # the mitten wiping (raised arm)
        if wipe:
            wx = cx - 6 + (2 if (k % 2) else -1)
            for y in range(hy - 2, hy + 2):
                for x in range(wx, wx + 3):
                    fr[y, x] = mitt
            for y in range(hy + 2, h - 10):
                fr[y, cx - 4] = coat
        # breath fog drawn back over the glass, a peephole while wiped
        for y in range(0, h - 2):
            for x in range(w):
                hx, hyy = x - (cx - 7), y - (hy - 1)
                in_hole = hole and hx * hx + hyy * hyy * 1.5 < 14
                if not in_hole and (x + 2 * y + k // 6) % 3 == 0 and y > 3:
                    fr[y, x] = fogc if (x + y) % 2 else fr[y, x]
        out.append(fr)
    return K.strip(out)


# =========================================================================== the typists behind the glass
def typist_strip(base: np.ndarray, glass_px: np.ndarray, frames=16, variant='a'):
    """A typist at her machine, seen from the side through the glass (crop `base` of the baked hall: her desk
    and typewriter are in it): she sits left of the machine facing it, hands drum on the keys, the head follows
    the copy, every eighth frame the left hand throws the carriage back.  `glass_px` = the glass reflection and
    frame pixels of the crop, re-applied on top so she stays behind the glass."""
    h, w = base.shape[:2]
    out = []
    top = K.rgba('P', 4.0) if variant == 'a' else K.rgba('D', 3.2)
    top_sh = K.rgba('P', 2.8) if variant == 'a' else K.rgba('D', 2.2)
    hair = K.rgba('P', 1.0) if variant == 'a' else K.rgba('S', 4.0)
    skin = K.rgba('Y', 1.6)
    chair = K.rgba('S', 1.4)
    desk_y = h - 20                      # the desk top of the crop (typists_room: y1 - 22, crop from y1 - 40)
    for k in range(frames):
        fr = base.copy()
        bob = 1 if (k % 4) in (1, 2) else 0
        ret = (k % 8) == 7
        fr[desk_y - 6:desk_y + 12, 3:5] = chair                              # chair back
        for y in range(desk_y - 8, desk_y + 3):                             # torso
            for x in range(6, 12):
                fr[y, x] = top if x > 6 else top_sh
        hy = desk_y - 16 + bob
        for y in range(hy, hy + 7):                                         # head
            for x in range(7, 12):
                fr[y, x] = hair
        fr[hy + 2:hy + 6, 11:13] = skin                                     # face in profile
        fr[hy + 5, 10:12] = skin
        if variant == 'a':
            fr[hy - 1:hy + 1, 6:8] = hair                                   # bun
        else:
            fr[hy + 1:hy + 4, 7] = K.rgba('S', 5.0)                         # grey curls
        fr[hy + 7, 9:11] = skin                                             # neck
        ay = desk_y - 4 - (1 if k % 2 else 0)
        for x in range(11, 15):                                              # forearm to the keys
            fr[ay, x] = top
        fr[ay - (k % 2), 15:17] = skin
        if ret:
            for t in range(6):
                fr[ay - 1 - t, 12 + t] = top
            fr[ay - 7:ay - 5, 18:20] = skin
        fr[glass_px] = base[glass_px]
        out.append(fr)
    return K.strip(out)
