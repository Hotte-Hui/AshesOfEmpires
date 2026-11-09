"""env_c3p2_quay_life -- ambient life and FX strips of the night quay (L_C3_Quay).
Every looping element is a strip of equal frames (layer_stack: frame = int(t * fps) % frames); every element
moves on a closed cycle, so no loop has a seam.  Figures are painted per frame into a Canvas placed at their world
position and baked with the scene lights (fire from the left, the lanterns), like the props.  Nobody has a face
in detail; nobody stands on a story hotspot or a story NPC's spot; all playfield figures stay behind the walk band.
Decals (scene.json "decals"):
  hose_team      two firemen at the yard gate, the jet arcing into the first souterrain window       (playfield)
  ladder_man     a fireman on the turntable ladder at a first-floor window                            (playfield)
  pump_man       the machinist at the pump panel at the back of the engine                            (playfield)
  onlookers      woken neighbours behind the guard's trestle: a woman in a coat over her nightdress,
                 an old man who points, a boy on tiptoe                                               (playfield)
  aide_kessler / aide_voronova   each delegation head's aide, waiting apart                          (playfield)
  drivers        the two chauffeurs share one lighter between the cars (the flame flickers < 3 Hz)   (playfield)
  beacon         the blue rotating lamp on the engine's cab, one turn per second                      (playfield)
  fire_win_N     flames licking out of the five souterrain windows (+ emission)                      (layer wing)
  embers_N       sparks rising over three windows (emission only)                                     (layer wing)
  searchlight_a/_b  beams of two watchtowers sweeping the ice, 6.7 s / 8 s per sweep (emission only)  (far_bank)
  town_win_N     windows of the old town lighting up one after another as people wake            (layer oldtown)
FX (scene.json "fx", anim_sprite, unlit): smoke columns from the windows, steam where the jet hits, smoke out of
the first-floor window, chimney smoke of the old town, the idling Soviet car's exhaust.
"""
from __future__ import annotations

import math

import numpy as np

import pixel_fire_bake as PFB

import env_c3p2_quay_kit as K
from env_c3p2_quay_kit import (Canvas, Light, Layer, resolve, bayer, value_noise, NI, SL, IR, CR, PA, LA, SK, SN, RD,
                               SKIN)
import env_c3p2_quay_near as N


# ================================================================================================= figures
def person(cv: Canvas, ox, base, H, spec, face=-1, ph=0.0, arm=None, stride=0.0, bob=0):
    """Side-view figure, feet on `base`, centred on ox, facing face (-1 left, +1 right).
    spec: coat (tone), coat_mat, hem (fraction of H), hat ('helmet'|'cap'|'homburg'|'scarf'|'shapka'|'bare'),
    hat_tone, skirt (tone of a long hem under the coat), width.  arm: list of (x, y) points of the near arm
    relative to the shoulder (forward = +x in facing direction)."""
    f = face
    k = H / 44.0
    top = base - H + 1 + bob
    head_h = max(4, int(round(6 * k)))
    head_w = max(3, int(round(5 * k)))
    sh_y = top + head_h + 1
    hip_y = base - int(round(H * 0.46))
    hem_y = base - int(round(H * spec.get('hem', 0.28)))
    body_w = max(5, int(round(8 * k * spec.get('width', 1.0))))
    cm = spec.get('coat_mat', 'cloth')
    ct = spec.get('coat', 0.08)
    # legs
    a = math.sin(2 * math.pi * ph) * stride
    for leg, lt in ((-1, 0.02), (1, 0.05)):
        fx_ = ox + f * leg * a * 3 * k
        for y in range(hip_y, base + 1):
            t = (y - hip_y) / max(1, base - hip_y)
            x = ox + (fx_ - ox) * t
            cv.rect(int(round(x)) - (1 if leg < 0 else 0), y, 2, 1, 'cloth', lt, hgt=0.5)
        cv.rect(int(round(fx_)) - 1 + (1 if f > 0 else -1), base, 4, 1, 'iron', 0.02, hgt=0.5)
    if spec.get('skirt') is not None:
        for y in range(hem_y, base - 3):
            w = body_w + 2
            cv.rect(ox - w // 2, y, w, 1, 'snow', spec['skirt'], hgt=0.55)
    # coat: trapezoid
    for y in range(sh_y, hem_y + 1):
        t = (y - sh_y) / max(1, hem_y - sh_y)
        w = body_w + int(round(t * 3 * k * spec.get('flare', 1.0)))
        x0 = ox - w // 2
        cv.rect(x0, y, w, 1, cm, ct, hgt=0.6)
        back = x0 + w - 1 if f < 0 else x0
        cv.px(back, y, cm, ct - 0.03)
        cv.px(x0 if f < 0 else x0 + w - 1, y, cm, ct + 0.05)          # front edge catches light
    cv.rect(ox - body_w // 2, hip_y - 1, body_w, 1, cm, ct - 0.04)       # belt
    if spec.get('belt') is not None:
        cv.rect(ox - body_w // 2, hip_y - 1, body_w, 2, 'wood', spec['belt'])
    # head
    hx0 = ox - head_w // 2 + (0 if f < 0 else 1)
    cv.rect(hx0, top + 1, head_w, head_h, 'skin', 0.32, hgt=0.75)
    back_x = hx0 + head_w - 1 if f < 0 else hx0
    cv.rect(back_x, top + 1, 1, head_h - 1, 'cloth', 0.06)              # hair / back of the head
    nose_x = hx0 - 1 if f < 0 else hx0 + head_w
    cv.px(nose_x, top + 1 + head_h // 2, 'skin', 0.3)
    cv.rect(hx0, top + head_h, head_w, 1, cm, ct - 0.02)                 # collar
    hat = spec.get('hat', 'bare')
    ht = spec.get('hat_tone', 0.05)
    if hat == 'helmet':                                                   # fire helmet with comb and neck flap
        cv.rect(hx0 - 1, top, head_w + 2, 3, 'iron', ht, hgt=0.85)
        cv.rect(hx0, top - 1, head_w, 1, 'iron', ht + 0.08)
        cv.rect(hx0 + head_w // 2, top - 2, 1, 2, 'iron', ht + 0.3)       # comb
        cv.rect(back_x - (1 if f > 0 else -1) * 0, top + 2, 2, head_h, 'cloth', 0.1)
        cv.rect(hx0 - 1 if f < 0 else hx0 + head_w - 1, top + 2, 2, 1, 'iron', ht)    # brim at the front
    elif hat == 'cap':
        cv.rect(hx0, top, head_w + 1, 2, 'cloth', ht, hgt=0.8)
        cv.rect(hx0 - 2 if f < 0 else hx0 + head_w - 1, top + 1, 3, 1, 'iron', ht + 0.05)   # peak
    elif hat == 'homburg':
        cv.rect(hx0 - 1, top + 1, head_w + 2, 1, 'cloth', ht, hgt=0.8)
        cv.rect(hx0, top - 1, head_w, 2, 'cloth', ht + 0.03)
    elif hat == 'scarf':
        cv.rect(hx0 - 1, top, head_w + 2, 2, spec.get('scarf_mat', 'red'), ht, hgt=0.8)
        cv.rect(back_x + (1 if f < 0 else -1), top + 1, 1, head_h + 1, spec.get('scarf_mat', 'red'), ht)
    elif hat == 'shapka':
        cv.rect(hx0 - 1, top - 1, head_w + 2, 3, 'cloth', ht, hgt=0.8)
        cv.rect(back_x + (1 if f < 0 else -1), top + 1, 1, 3, 'cloth', ht)
    # near arm
    sx = ox + f * 1
    pts = arm if arm is not None else [(0, 0), (0, int(H * 0.3))]
    for (p, q) in zip(pts[:-1], pts[1:]):
        cv.line(sx + f * p[0], sh_y + 1 + p[1], sx + f * q[0], sh_y + 1 + q[1], cm, ct - 0.02, hgt=0.7)
    hx, hy = pts[-1]
    if spec.get('gloves', False):
        cv.px(sx + f * hx, sh_y + 2 + hy, 'cloth', 0.03)
    else:
        cv.px(sx + f * hx, sh_y + 2 + hy, 'skin', 0.3)
    return dict(sh=(sx, sh_y + 1), head=(hx0, top), hand=(sx + f * hx, sh_y + 2 + hy))


def _strip_from(frames, name):
    """Concatenate resolved frame Layers into one strip Layer (colour, height, emission)."""
    fw, fh = frames[0].w, frames[0].h
    S = Layer(fw * len(frames), fh, name)
    for i, F in enumerate(frames):
        S.c[:, i * fw:(i + 1) * fw] = F.c
        S.hgt[:, i * fw:(i + 1) * fw] = F.hgt
        S.em[:, i * fw:(i + 1) * fw] = F.em
    return S


def _frames(n, box, draw, lights, name):
    x0, y0, w, h = box
    out = []
    for i in range(n):
        cv = Canvas(w, h, name, ox=x0, oy=y0)
        draw(cv, i, n)
        out.append(resolve(cv, lights))
    return _strip_from(out, name)


FIREMAN = dict(coat=0.07, coat_mat='cloth', hem=0.3, hat='helmet', hat_tone=0.06, belt=0.3, gloves=True)


# ================================================================================================= decals
def hose_team(lights):
    box = (18, 228, 150, 68)
    target = (N.BASE_WIN[0] + 2, 250)

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        t = i / n
        # rear man braces the line, front man holds the branchpipe (both face left, toward the window)
        p2 = person(cv, 150 - X, 293 - Y, 43, FIREMAN, -1, arm=[(0, 0), (4, 7), (8, 11)],
                    bob=1 if i % 6 < 3 else 0)
        p1 = person(cv, 128 - X, 293 - Y, 44, FIREMAN, -1, arm=[(0, 0), (5, 6), (10, 7)])
        # the hose between them and the branchpipe
        hx, hy = p1['hand']
        cv.line(p2['hand'][0], p2['hand'][1], hx + 2, hy + 1, 'cloth', 0.1)
        nx, ny = hx - 5, hy - 2
        cv.line(hx, hy, nx, ny, 'iron', 0.34)
        # the jet: a parabola from the nozzle to the window, droplets running along it
        tx, ty = target[0] - X, target[1] - Y
        L = 64
        for s in range(L):
            u = s / (L - 1)
            x = nx + (tx - nx) * u
            y = ny + (ty - ny) * u - 22 * u * (1 - u) * 1.0 + 0.4 * math.sin((u * 9 + t * 2 * math.pi) * 2)
            if (s + i * 3) % 7 == 0 and u > 0.08:
                continue
            cv.px(x, y, 'snow', 0.84 if s % 3 else 0.95)
            if u < 0.6:
                cv.px(x, y + 1, 'snow', 0.7)
            if u > 0.55 and (s + i) % 4 == 0:
                cv.px(x + 1, y + 1, 'snow', 0.6)
        for k in range(10):                                            # spray at the impact
            a = (k * 2.399 + t * 6.283)
            r = 2 + (k * 7 + i * 3) % 6
            cv.px(tx + r * math.cos(a), ty + 0.6 * r * math.sin(a), 'snow', 0.7)

    return _frames(12, box, draw, lights, 'hose_team'), box


def ladder_man(lights):
    box = (188, 86, 34, 50)

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        lean = 1 if (i // 2) % 4 == 1 else 0
        p = person(cv, 208 - X - lean, 130 - Y, 40, FIREMAN, -1, arm=[(0, 0), (5, 3), (9, 2)])
        hx, hy = p['hand']
        cv.line(hx, hy, hx - 4, hy - 1, 'iron', 0.34)
        for s in range(6):                                              # short spray into the window
            cv.px(hx - 5 - s * 2, hy - 1 + (s * s) // 9 + (i % 2), 'snow', 0.8)

    return _frames(8, box, draw, lights, 'ladder_man'), box


def pump_man(lights):
    box = (262, 240, 30, 56)

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        ph = i / n
        reach = i in (6, 7, 8, 9)
        arm = [(0, 0), (6, 4), (9, 2)] if reach else [(0, 0), (2, 8), (3, 13)]
        person(cv, 276 - X, 293 - Y, 43, FIREMAN, 1 if i < 12 else -1, arm=arm, bob=1 if i in (3, 4) else 0)

    return _frames(16, box, draw, lights, 'pump_man'), box


def onlookers(lights):
    box = (1052, 240, 66, 54)
    WOMAN = dict(coat=0.12, coat_mat='cloth', hem=0.36, hat='scarf', hat_tone=0.24, skirt=0.48, width=0.95,
                 scarf_mat='red')
    OLD = dict(coat=0.1, coat_mat='cloth', hem=0.28, hat='homburg', hat_tone=0.06)
    BOY = dict(coat=0.16, coat_mat='cloth', hem=0.34, hat='cap', hat_tone=0.12, width=0.85)

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        point = 8 <= i < 15
        old_arm = [(0, 0), (6, -2), (11, -5)] if point else [(0, 0), (2, 6), (3, 12)]
        person(cv, 1100 - X, 291 - Y, 42, OLD, -1, arm=old_arm, bob=1 if i in (16, 17) else 0)
        person(cv, 1076 - X, 291 - Y, 40, WOMAN, -1, arm=[(0, 0), (-2, 6), (2, 8)],
               bob=1 if (i // 3) % 4 == 2 else 0)
        tip = 2 if (i // 4) % 3 == 1 else 0
        person(cv, 1062 - X, 291 - Y - tip, 33, BOY, -1, arm=[(0, 0), (1, 6), (2, 10)])

    return _frames(24, box, draw, lights, 'onlookers'), box


def aide(lights, kind):
    if kind == 'kessler':
        box, ox = (1138, 246, 28, 50), 1150
        spec = dict(coat=0.12, coat_mat='cloth', hem=0.26, hat='homburg', hat_tone=0.07)
    else:
        box, ox = (1364, 246, 28, 50), 1376
        spec = dict(coat=0.1, coat_mat='cloth', hem=0.24, hat='shapka', hat_tone=0.08)

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        if kind == 'kessler':
            watch = i in (9, 10, 11)
            arm = [(0, 0), (5, 5), (4, 1)] if watch else [(0, 0), (1, 7), (1, 12)]
            p = person(cv, ox - X, 294 - Y, 44, spec, -1, arm=arm, bob=1 if i in (2, 3) else 0)
            if not watch:                                           # briefcase
                hx, hy = p['hand']
                cv.rect(hx - 3, hy, 7, 5, 'wood', 0.12)
                cv.rect(hx - 3, hy, 7, 1, 'wood', 0.22)
        else:
            rub = (i // 2) % 2
            arm = [(0, 0), (3, 6), (5 + rub, 7)]
            person(cv, ox - X, 294 - Y, 43, spec, -1, arm=arm)
            cv.rect(ox - X + 2, 294 - Y - 30, 3, 8, 'stone', 0.4)       # folder under the arm

    return _frames(16, box, draw, lights, 'aide_' + kind), box


def drivers(lights):
    box = (1232, 244, 56, 50)
    DRV_DE = dict(coat=0.09, coat_mat='cloth', hem=0.3, hat='cap', hat_tone=0.05)
    DRV_SU = dict(coat=0.13, coat_mat='cloth', hem=0.3, hat='cap', hat_tone=0.08)
    n_frames = 32

    def draw(cv, i, n):
        X, Y = box[0], box[1]
        lit = 4 <= i < 15
        lean = 1 if 3 <= i < 15 else 0
        a = person(cv, 1252 - X + lean, 293 - Y, 43, DRV_DE, 1, arm=[(0, 0), (4, 5), (6, 3)] if lean else [(0, 0), (1, 7), (2, 12)],
                   bob=lean)
        b = person(cv, 1272 - X, 293 - Y, 44, DRV_SU, -1, arm=[(0, 0), (4, 6), (7, 4)] if 2 <= i < 16 else [(0, 0), (2, 7), (3, 12)])
        # cigarette of the German driver (a 2-px stick), glowing tip after it is lit
        hx, hy = a['head'][0] + 6, a['head'][1] + 5
        cv.px(hx, hy, 'snow', 0.8)
        if i >= 12:
            cv.px(hx + 1, hy, 'flame', 0.5 if i % 6 < 3 else 0.3)
        if lit:
            fx_, fy_ = b['hand'][0] - 1, b['hand'][1] - 2
            tall = 2 if i % 3 != 1 else 1
            for k in range(tall):
                cv.px(fx_, fy_ - k, 'flame', 0.9 - 0.3 * k)
            cv.px(fx_, fy_ + 1, 'lit', 0.4)
        if i >= 16:                                                 # a breath of smoke drifting up
            u = (i - 16) / 16.0
            for k in range(3):
                cv.px(hx + 2 + int(u * 6) + k, hy - 2 - int(u * 14) - k % 2, 'smoke', 0.35 - 0.1 * u)

    return _frames(n_frames, box, draw, lights, 'drivers'), box


def beacon(pos):
    """Blue rotating lamp: 8 frames @ 8 fps; the bright lobe swings across the dome (emission)."""
    w, h = 11, 7
    S = Layer(w * 8, h, 'beacon')
    cx = 5
    for i in range(8):
        a = i / 8 * 2 * math.pi
        lobe = math.sin(a)
        ox = i * w
        for x in range(3, 8):
            for y in range(2, 6):
                d = abs((x - cx) / 2.5 - lobe)
                c = SN[3] if d < 0.45 else (SK[2] if d < 1.0 else SL[3])
                S.c[y, ox + x] = (*c[:3], 255)
                S.em[y, ox + x] = (*c[:3], 255)
        S.c[1, ox + 4:ox + 7] = (*IR[2][:3], 255)
        S.c[6, ox + 3:ox + 8] = (*IR[1][:3], 255)
        if abs(lobe) > 0.7:                                          # brief halo pixels to the side it faces
            sx = ox + (9 if lobe > 0 else 1)
            for y in (2, 3, 4):
                S.c[y, sx] = (*SK[2][:3], 255)
                S.em[y, sx] = (*SK[2][:3], 255)
    box = (pos[0] - cx, pos[1] - 5, w, h)
    return S, box


# Round 13: the wing's fire comes from the pixel fire kit (pixel_fire.py through pixel_fire_bake.py) in the quay's
# own colours -- the Veltrava palette has no fire ramp, so the bands run red -> lamp light.
QUAY_FLAME = ('#A8382E', '#D08F55', '#EDB777', '#FCE2B0')              # rim .. core (small flames: 4 bands)
QUAY_COOL = '#7A2218'
SMOKE_LIT = ('#22262D', '#4A4236', '#6E3F22')                          # dark / body / lit by the fire below
SMOKE_NIGHT = ('#1A2431', '#2A3646', '#3A4859')                        # .. out of its light


def window_fire(c, lights):
    """Fire in a souterrain window and licking up the wall above it -- 8 frames @ 6 fps.  Designed pixel tongues
    (pixel_fire_bake.flames): one set fills the opening, one stands on the lintel; the emission twin is the hot
    core only."""
    box = (c - 16, 226, 32, 38)
    y0w, y1w = N.BASE_WIN_Y
    n = 8
    inside = PFB.flames(22, y1w - y0w, n, [(6, 4, 0.9), (15, 5, 1.0)], c * 31, 1.0, base=0.3, cols=QUAY_FLAME,
                        tick=6, cool=QUAY_COOL)
    over = PFB.flames(box[2], y0w - box[1], n, [(9, 3, 0.8), (20, 4, 1.0), (26, 2, 0.55)], c * 31 + 7, 1.0,
                      base=0.0, cols=QUAY_FLAME, tick=6, cool=QUAY_COOL)
    S = Layer(box[2] * n, box[3], 'fire_win')
    for i in range(n):
        fr = np.zeros((box[3], box[2], 4), np.uint8)
        PFB.paste(fr, over[i], 0, 0)
        PFB.paste(fr, inside[i], 5, y0w - box[1])
        S.c[:, i * box[2]:(i + 1) * box[2]] = fr
        S.em[:, i * box[2]:(i + 1) * box[2]] = PFB.hot([fr], QUAY_FLAME[1:])[0]
    return S, box


def embers(c, seed):
    """Sparks rising and drifting right (emission only; 16 frames @ 8 fps)."""
    w, h, n = 44, 116, 16
    S = Layer(w * n, h, 'embers')
    rng = np.random.default_rng(seed)
    sparks = [(rng.uniform(4, 22), rng.uniform(0, 1), rng.uniform(0.6, 1.0), rng.uniform(0, 6.28)) for _ in range(11)]
    for i in range(n):
        for (x0, ph, sp, wob) in sparks:
            u = (i / n * sp + ph) % 1.0
            x = x0 + 18 * u * u + 2 * math.sin(wob + u * 9)
            y = h - 4 - u * (h - 10)
            col = LA[4] if u < 0.25 else (LA[3] if u < 0.55 else (LA[2] if u < 0.8 else RD[3]))
            xx, yy = int(i * w + x), int(y)
            if 0 <= yy < h and i * w <= xx < (i + 1) * w:
                S.em[yy, xx] = (*col[:3], 255)
    box = (c - 10, 246 - h, w, h)
    return S, box


def searchlight(src, seed, n=80, amp=74, period_frames=80):
    """Beam of a watchtower searchlight sweeping the ice (emission only, soft alpha).  The footprint swings
    across the river and back once per loop (n frames)."""
    fw, fh = 200, 128
    sx, sy = 100, 3
    S = Layer(fw * n, fh, 'searchlight')
    rng = np.random.default_rng(int(seed * 100) + 7)
    flakes = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0.6, 1.3)) for _ in range(22)]
    col = np.asarray(SN[3], np.float32)[:3]
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    for i in range(n):
        ph = 2 * math.pi * i / period_frames + seed
        fx_ = sx + amp * math.sin(ph)
        fy_ = 108 + 7 * math.cos(ph)
        rx, ry = 22 + 4 * math.cos(ph), 4.0
        # cone: inside the triangle (src, left/right extreme of the footprint ellipse)
        u = np.clip((yy - sy) / max(1.0, fy_ - sy), 0, 1)
        cxl = sx + (fx_ - rx - sx) * u
        cxr = sx + (fx_ + rx - sx) * u
        inside = (yy >= sy) & (yy <= fy_) & (xx >= np.minimum(cxl, cxr) - 0.5) & (xx <= np.maximum(cxl, cxr) + 0.5)
        edge = np.minimum(np.abs(xx - cxl), np.abs(xx - cxr)) / np.maximum(1.0, np.abs(cxr - cxl) / 2)
        a = np.where(inside, (0.30 - 0.14 * u) * np.clip(0.35 + edge, 0, 1), 0.0)
        d = np.sqrt(((xx - fx_) / rx) ** 2 + ((yy - fy_) / ry) ** 2)
        a = np.maximum(a, np.where(d < 1, 0.55 * np.clip(1 - d, 0, 1) ** 0.7 + 0.12, 0.0))
        q = np.floor(a * 6 + bayer(fw, fh) * 0.999) / 6.0                 # dithered steps
        for (fxu, fyu, spd) in flakes:                                 # snow glinting in the beam
            v = (fyu + i / n * spd * 3) % 1.0
            py_ = int(sy + 4 + v * (fy_ - sy - 6))
            uu = (py_ - sy) / max(1.0, fy_ - sy)
            px_ = int(sx + (fx_ - sx) * uu + (fxu - 0.5) * 2 * rx * uu)
            if 0 <= py_ < fh and 0 <= px_ < fw:
                q[py_, px_] = max(q[py_, px_], 0.85)
        sl = S.em[:, i * fw:(i + 1) * fw]
        sl[..., :3] = col.astype(np.uint8)
        sl[..., 3] = np.clip(np.round(q * 255), 0, 255).astype(np.uint8)
        sl[sl[..., 3] == 0] = 0
    box = (src[0] - sx, src[1] - sy, fw, fh)
    return S, box


def town_windows(info, picks=6, n=30):
    """Dark old-town windows that light up one after another (people woken by the bells) and go dark again;
    frame 1 per 2 s (n frames = 60 s loop).  Returns [(Layer, box)] in oldtown layer coordinates."""
    dark = [w for w in info['windows'] if not w[4]]
    rng = np.random.default_rng(870)
    out = []
    if not dark:
        return out
    idx = sorted(rng.choice(len(dark), size=min(picks, len(dark)), replace=False))
    for j, k in enumerate(idx):
        wx, wy, ww, wh, _ = dark[k]
        S = Layer(ww * n, wh, 'town_win')
        on0 = int(rng.integers(0, n))
        dur = int(rng.integers(8, 20))
        warm = [LA[1], LA[2], LA[3]][j % 3]
        for i in range(n):
            if (i - on0) % n < dur:
                for y in range(wh):
                    for x in range(ww):
                        c = warm if not (x == ww // 2 or y == 3) else LA[0]
                        S.c[y, i * ww + x] = (*c[:3], 255)
                        S.em[y, i * ww + x] = (*c[:3], 255)
        out.append((S, (wx, wy, ww, wh)))
    return out


# ================================================================================================= fx strips
def _periodic_noise(w, h, cell, seed, octaves=3):
    """Value noise made periodic along y (two half-shifted copies cross-faded with sin^2 / cos^2)."""
    n1 = value_noise(w, h, cell, seed=seed, octaves=octaves)
    n2 = np.roll(n1, h // 2, axis=0)
    wy = np.sin(np.pi * np.arange(h, dtype=np.float32) / h)[:, None] ** 2
    return n1 * wy + n2 * (1 - wy)


def smoke_column(c, seed, n=16, fw=84, fh=226, drift=34.0, r0=5.0, r1=26.0, y_src=246, dens=1.0, fire=1.0):
    """Thick smoke pouring from a window and rolling up the facade, drifting right: a column of pixel puffs
    (pixel_fire_bake.column) that swell, climb and break up through the ordered dither -- binary alpha, three
    tones; fire-lit while young near the window (fire), the night's slate above.  Returns (Layer strip, box)."""
    X, Y = c - 16, y_src - fh + 6
    fr = PFB.column(fw, fh, n, (16.0, fh - 10.0), (16.0 + drift, 0.6 * r1), seed,
                    tones=SMOKE_LIT if fire > 0.5 else SMOKE_NIGHT, cool=SMOKE_NIGHT,
                    sizes=(int(1.3 * r1), int(1.6 * r1), int(2.0 * r1)), count=7, loops=2, sway=2.5,
                    warm_until=0.22)
    S = Layer(fw * n, fh, 'smoke')
    S.c[:] = np.concatenate(fr, axis=1)
    return S, (X, Y, fw, fh)


def steam_puffs(cx, cy, seed, n=12, fw=40, fh=48):
    X, Y = cx - fw // 2, cy - fh + 8
    rng = np.random.default_rng(seed)
    jit = [(rng.uniform(-6, 6), rng.uniform(0, 1)) for _ in range(4)]
    S = Layer(fw * n, fh, 'steam')
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    for i in range(n):
        D = np.zeros((fh, fw), np.float32)
        for k, (jx, ph) in enumerate(jit):
            u = (i / n + k / len(jit)) % 1.0
            px_ = fw / 2 + jx + 6 * u
            py_ = fh - 8 - u * (fh - 16)
            r = 3 + 8 * u
            D = np.maximum(D, (1 - u) * np.clip(1 - ((xx - px_) ** 2 + (yy - py_) ** 2) / (r * r), 0, 1))
        m = D > 0.25 + 0.3 * (bayer(fw, fh) - 0.5)
        cols = np.where((D > 0.55)[..., None], np.asarray(SN[2], np.uint8), np.asarray(SL[4], np.uint8))
        sl = S.c[:, i * fw:(i + 1) * fw]
        sl[m] = cols[m]
    return S, (X, Y, fw, fh)


def chimney_smoke(seed, n=8, fw=28, fh=50):
    rng = np.random.default_rng(seed)
    S = Layer(fw * n, fh, 'chimney')
    for i in range(n):
        for k in range(14):
            u = ((i / n) + k / 14.0) % 1.0
            x = 4 + 16 * u * u + 1.5 * math.sin(u * 8 + seed)
            y = fh - 3 - u * (fh - 6)
            r = 1 + int(3 * u)
            col = SL[2] if u < 0.5 else SL[1]
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r and bayer(1, 1, int(x + dx), int(y + dy))[0, 0] < 0.8 - 0.5 * u:
                        xx, yy_ = int(i * fw + x + dx), int(y + dy)
                        if i * fw <= xx < (i + 1) * fw and 0 <= yy_ < fh:
                            S.c[yy_, xx] = (*col[:3], 255)
    return S, (4, fh - 3, fw, fh)


def exhaust(seed, n=8, fw=26, fh=18):
    S = Layer(fw * n, fh, 'exhaust')
    for i in range(n):
        for k in range(3):
            u = (i / n + k / 3) % 1.0
            x, y = 2 + 18 * u, fh - 4 - 8 * u
            r = 1 + 2 * u
            for dy in range(-2, 3):
                for dx in range(-3, 4):
                    if (dx * dx + dy * dy) <= r * r and ((dx + dy + i) % 2 == 0 or u < 0.4):
                        xx, yy_ = int(i * fw + x + dx), int(y + dy)
                        if i * fw <= xx < (i + 1) * fw and 0 <= yy_ < fh:
                            S.c[yy_, xx] = (*(SL[3] if u < 0.5 else SL[2])[:3], 255)
    return S, (0, fh - 4, fw, fh)
