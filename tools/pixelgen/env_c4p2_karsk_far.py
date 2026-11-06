"""env_c4p2_karsk_far -- the parallax backgrounds of L_C4P2_Karsk (sky, the town of Karsk, the embankment / station).

Scene A (Monday 6.10, dawn): a blue-grey dawn sky with long stratus bands lit from below in the east, the last stars;
Karsk waking up behind the depot -- blocks of flats with the first lit kitchens, the chimneys of the works with their
plumes leaning in the wind, the water tower, cranes over a building site; nearer, the railway embankment with
telegraph poles and birches (the passing goods train runs on it -- actor KarskTrain, own sprites).
Scene B (Tuesday 17.30-20.10, evening): night, the town's sodium haze low on the clouds, many lit windows, the
station of Karsk behind platform 1 (the clock tower, the long lit facade), lamp masts.

Each layer is wide enough for its scene's camera range at its parallax (layer x 0 = home); see parallax_home().
Painted in tone space, resolved without baked lights (unlit layers; the emissive windows come from `emis`).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K
import env_c4p2_karsk_layout as L

H = L.WORLD_H


def parallax_home(scene: str, p: float) -> tuple[int, int]:
    """(home x, width) of a layer at parallax p for the camera range of `scene`."""
    c0 = L.CAMERA[scene][0]
    c1 = max(c0, L.CAMERA[scene][1] - 640)
    home = int(math.floor(c0 * p))
    w = int(math.ceil(640 + (c1 - c0) * p)) + 6
    return home, w


def _resolve(lay, seed=0):
    F = K.empty_fields(lay.h, lay.w)
    K.resolve(lay, F, seed=seed, exposure=1.0, band=2.0)
    return lay


# =========================================================================== sky
def sky_tone(y, dawn):
    """The sky's tone (ramp 'B') at row y -- the clouds and the far smoke are painted relative to it."""
    yy = np.clip(np.asarray(y, np.float32) / H, 0, 1)
    if dawn:
        return 1.9 + np.clip(yy * 1.55, 0, 1) ** 1.15 * 5.0
    return 2.6 + yy ** 1.2 * 2.1


def _clouds_lit(lay, w, seed, bands):
    """Evening: low stratus lit from below by the town (sodium skyglow) -- the decks are LIGHTER than the gaps
    between them, warm grey-brown, their undersides brightest, the upper edges dark; ragged dithered edges."""
    from PIL import Image
    for k, (cy, th, dens) in enumerate(bands):
        hh = th * 2 + 8
        n = K.nz(max(2, w // 7), max(2, hh // 2), 3, seed + k, octaves=3)
        img = Image.fromarray(((n + 0.5) * 255).astype(np.uint8)).resize((w, hh), Image.BILINEAR)
        nn = np.asarray(img, np.float32) / 255.0 - 0.5
        yy = np.abs(np.linspace(-1, 1, hh, dtype=np.float32))[:, None]
        env = np.clip(1 - yy ** 1.5, 0, 1)
        v = (nn + 0.5) * env * dens
        tq = K.pg.bayer(w, hh, k * 3, 0, 4)
        m = (v > 0.40) | ((v > 0.30) & (tq < (v - 0.30) * 8))
        if not m.any():
            continue
        y0 = int(cy - hh / 2)
        low = float(np.clip(cy / 190.0, 0, 1))                       # lower decks catch more of the town's light
        rows = np.linspace(0, 1, hh, dtype=np.float32)[:, None]
        lay.put(m, 0, y0, 'H', 1.3 + low * 1.7 + rows * 0.9 + nn * 0.5, flat=False)
        top_e = m & ~np.roll(m, 1, axis=0)
        lay.put(top_e, 0, y0, 'B', float(sky_tone(cy, False)) - 0.3, flat=False)
        under = m & ~np.roll(m, -1, axis=0)
        lay.put(under, 0, y0, 'H', 2.6 + low * 1.9, flat=False)


def _clouds(lay, w, rng, seed, bands, dawn):
    """Stratus decks: stretched noise masks inside soft horizontal bands, a little darker than the sky behind them
    (backlit), the ragged edges dithered; the undersides catch the light of the horizon (dawn: grey-rose in the
    east; evening: the town's sodium haze)."""
    from PIL import Image
    for k, (cy, th, dens) in enumerate(bands):
        hh = th * 2 + 8
        n = K.nz(max(2, w // 7), max(2, hh // 2), 3, seed + k, octaves=3)
        img = Image.fromarray(((n + 0.5) * 255).astype(np.uint8)).resize((w, hh), Image.BILINEAR)
        nn = np.asarray(img, np.float32) / 255.0 - 0.5
        yy = np.abs(np.linspace(-1, 1, hh, dtype=np.float32))[:, None]
        env = np.clip(1 - yy ** 1.5, 0, 1)
        v = (nn + 0.5) * env * dens
        tq = K.pg.bayer(w, hh, k * 3, 0, 4)
        m = (v > 0.40) | ((v > 0.30) & (tq < (v - 0.30) * 8))
        if not m.any():
            continue
        y0 = int(cy - hh / 2)
        rows = sky_tone(np.arange(y0, y0 + hh), dawn)[:, None]
        body = rows - (1.0 if dawn else 0.7) + nn * 0.4
        lay.put(m, 0, y0, 'B', body, flat=False)
        under = m & ~np.roll(m, -1, axis=0)
        under2 = m & ~np.roll(m, -2, axis=0) & ~under
        xs = np.arange(w, dtype=np.float32)[None, :].repeat(hh, 0)
        east = np.clip(xs / w * 1.4 - 0.2, 0, 1)
        if dawn:
            lay.put(under, 0, y0, 'Z', 0.6 + east * 2.0, flat=False)
            lay.put(under2, 0, y0, 'B', rows + 0.2 + nn * 0, flat=False)
        else:
            lay.put(under, 0, y0, 'Z', 0.3 + cy / 160.0, flat=False)


def sky(scene: str):
    home, w = parallax_home(scene, 0.1)
    lay = K.tlayer(w, H, 'sky')
    rng = np.random.default_rng(301 if scene == L.SA else 302)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(w, 1)
    if scene == L.SA:
        # dawn: night blue at the top, blue-grey at the horizon, a faint grey-rose band low in the east (right)
        t = 1.9 + np.clip(yy * 1.55, 0, 1) ** 1.15 * 5.0 + K.nz(w, H, 40, 303, octaves=2) * 0.3
        lay.put(np.ones((H, w), bool), 0, 0, 'B', t, flat=False)
        xx = np.linspace(0, 1, w, dtype=np.float32)[None, :].repeat(H, 0)
        glow = np.clip((yy - 0.36) * 3.0, 0, 1) * np.clip(xx * 1.2 - 0.1, 0, 1)
        mk = glow > 0.30 + K.nz(w, H, 8, 304) * 0.25
        lay.put(mk, 0, 0, 'Z', 0.8 + glow * 2.2, flat=False)
        for _ in range(16):                                                # the last stars, high up only
            x, y = int(rng.integers(0, w)), int(rng.integers(2, 46))
            lay.px(x, y, 'S', 2.4 + rng.random() * 1.6, crisp=True)
        _clouds(lay, w, rng, 310, ((40, 6, 1.0), (74, 9, 1.1), (112, 7, 1.2), (150, 10, 1.15), (184, 6, 1.0)), True)
    else:
        # evening: a winter night over a lit town is not black -- dark blue-grey up high, warming toward the roofs
        # where the town's sodium light hangs in the haze under the low cloud (strongest over the station, right);
        # the cloud decks catch that light; a few stars in the gaps, high up only
        t = sky_tone(yy * H, False) + K.nz(w, H, 40, 305, octaves=2) * 0.35
        lay.put(np.ones((H, w), bool), 0, 0, 'B', t, flat=False)
        xx = np.linspace(0, 1, w, dtype=np.float32)[None, :].repeat(H, 0)
        glow = np.clip((yy - 0.16) / 0.44, 0, 1) ** 1.25 * (0.75 + K.nz(w, H, 60, 306, octaves=2) * 0.6
                                                           + np.clip(xx - 0.45, 0, 1) * 0.5)
        thr = K.pg.bayer(w, H, 0, 0, 4)
        mk = glow > thr * 0.8 + 0.1
        lay.put(mk, 0, 0, 'H', 1.0 + glow * 3.0, flat=False)
        for _ in range(26):
            x, y = int(rng.integers(0, w)), int(rng.integers(2, 34))
            lay.px(x, y, 'S', 2.4 + rng.random() * 1.6, crisp=True)
        _clouds_lit(lay, w, 320, ((30, 7, 0.95), (64, 11, 1.1), (100, 10, 1.15), (134, 9, 1.15), (164, 8, 1.1)))
    return _resolve(lay, 1), home


# =========================================================================== the town
def _block(lay, x, base, w, h, rng, lit_share, tone=1.8, ramp='B', storeys=5, roof='flat', win_t=3.4, seed=0):
    """A block of flats far away: a flat silhouette, rows of windows (some lit), a roof line with snow."""
    lay.rect(x, base - h, w, h, ramp, tone, flat=True)
    lay.rect(x, base - h, 1, h, ramp, tone + 0.5)
    sh = (h - 4) // storeys
    for s in range(storeys):
        wy = base - h + 3 + s * sh
        for wx in range(x + 2, x + w - 2, 4):
            if rng.random() < lit_share:
                lay.rect(wx, wy, 2, 2, 'L', win_t + rng.random() * 1.2, emis=True)
            else:
                lay.rect(wx, wy, 2, 2, ramp, tone - 0.6)
    if roof == 'flat':
        lay.rect(x, base - h - 1, w, 1, 'S', 2.6 if lit_share < 0.4 else 3.4)
        if lit_share >= 0.4:                                      # evening: the snow on the roofs in the skyglow
            lay.rect(x, base - h - 2, w, 1, 'S', 2.2)
            for k in range(x + 2, x + w - 2, 7):
                lay.px(k, base - h - 1, 'H', 4.6)
    else:
        lay.poly([(x - 1, base - h), (x + w // 2, base - h - 6), (x + w + 1, base - h)], 'N', 2.0)
        lay.line(x - 1, base - h, x + w // 2, base - h - 6, 'S', 2.4 if lit_share < 0.4 else 3.4)


def _chimney(lay, x, base, h, smoke_dx, ramp='B', tone=1.6, seed=0, smoke=True, lit=False, dawn=True):
    for i in range(4):
        lay.rect(x + i, base - h + i // 3, 1, h, ramp, tone + (0.4 if i == 0 else 0.0))
    for k in range(3):
        lay.rect(x - 1, base - h + 8 + k * 14, 6, 1, ramp, tone - 0.5)
    if lit:
        lay.px(x + 1, base - h - 1, 'R', 3.6, emis=True)                   # aviation lamp
    if smoke:
        # a soft plume leaning with the wind: overlapping puffs, dithered thinner as it rises, a little lighter
        # than the sky behind it (lit by the town)
        thr = K.pg.bayer(120, 120, seed % 4, 0, 4)
        n = K.nz(120, 120, 6, seed, octaves=3)
        x0, y0 = x + 2, base - h - 2
        for i in range(0, 70, 2):
            u = i / 70.0
            cx = x0 + smoke_dx * i * 1.2 + math.sin(u * 4 + seed) * 2.0
            cy = y0 - i * 0.45 + u * u * 5
            r = 1.5 + u * 8.0
            dens = 0.85 * (1 - u) ** 0.7
            for yy in range(int(cy - r), int(cy + r) + 1):
                for xx in range(int(cx - r), int(cx + r) + 1):
                    d = math.hypot(xx - cx, yy - cy) / r
                    if d > 1:
                        continue
                    a = dens * (1 - d * d) + n[yy % 120, xx % 120] * 0.6
                    if a > thr[yy % 120, xx % 120] * 0.9 + 0.25:
                        if dawn:
                            lay.px(xx, yy, 'B', float(sky_tone(yy, dawn)) + 0.7, flat=False)
                        else:                         # evening: the smoke catches the town's light from below
                            lit_k = (1 - u) * 1.8 + (yy - cy + r) / max(1.0, 2 * r) * 0.8
                            lay.px(xx, yy, 'H', 1.6 + lit_k, flat=False)


def town(scene: str):
    home, w = parallax_home(scene, 0.3)
    lay = K.tlayer(w, H, 'town')
    rng = np.random.default_rng(331 if scene == L.SA else 332)
    dawn = scene == L.SA
    base = 236 if dawn else 204
    lit = 0.22 if dawn else 0.48
    tone = 1.6 if dawn else 1.2
    # ground band of the far town (snowy roofs, haze)
    lay.vgrad(0, base - 4, w, H - base + 4, 'B', 3.6 if dawn else 2.6, 2.2 if dawn else 1.6)
    x = -10
    k = 0
    while x < w:
        bw = int(rng.integers(26, 64))
        bh = int(rng.integers(26, 58))
        storeys = max(3, bh // 10)
        _block(lay, x, base + int(rng.integers(-2, 3)), bw, bh, rng, lit, tone=tone + rng.random() * 0.5,
               storeys=storeys, roof='flat' if rng.random() < 0.7 else 'gable', seed=k)
        x += bw + int(rng.integers(-6, 10))
        k += 1
    # the works: chimneys with plumes (leaning with the wind), the water tower, a crane
    stacks = (60, 210, 520) if dawn else (120, 430, 640)
    for i, sx in enumerate(stacks):
        if sx < w:
            _chimney(lay, sx, base - 10, 74 + i * 6, 0.55, tone=tone - 0.2, seed=341 + i, lit=True, dawn=dawn)
    tx = 330 if dawn else 560
    if tx < w - 10:
        lay.rect(tx, base - 64, 3, 30, 'B', tone)
        lay.rect(tx + 10, base - 64, 3, 30, 'B', tone)
        lay.ellipse(tx + 6, base - 72, 12, 9, 'B', tone + 0.4)
        lay.rect(tx - 6, base - 74, 25, 2, 'S', 2.4)
    cx = 450 if dawn else 230
    if cx < w - 30:
        lay.rect(cx, base - 92, 2, 60, 'B', tone)                         # a tower crane over a building site
        lay.rect(cx - 24, base - 92, 46, 2, 'B', tone)
        lay.line(cx - 24, base - 91, cx + 1, base - 104, 'B', tone)
        lay.line(cx + 22, base - 91, cx + 1, base - 104, 'B', tone)
        lay.px(cx + 1, base - 105, 'R', 3.6, emis=True)
    if not dawn:
        # the station of Karsk: the long lit facade and the clock tower (behind platform 1)
        sx0 = w - 300
        lay.rect(sx0, base - 40, 280, 40, 'B', 1.4)
        for wx in range(sx0 + 6, sx0 + 276, 9):
            lay.rect(wx, base - 30, 4, 10, 'L', 3.8 + rng.random(), emis=True)
            lay.rect(wx, base - 16, 4, 6, 'L', 3.2 + rng.random(), emis=True)
        tw = sx0 + 120
        lay.rect(tw, base - 104, 22, 64, 'B', 1.6)
        lay.poly([(tw - 2, base - 104), (tw + 24, base - 104), (tw + 11, base - 132)], 'B', 1.8)
        lay.line(tw + 11, base - 132, tw + 11, base - 142, 'B', 2.0)
        lay.ellipse(tw + 11, base - 88, 7, 7, 'P', 5.0, emis=True)        # clock face, lit
        lay.line(tw + 11, base - 88, tw + 11, base - 93, 'N', 1.0)
        lay.line(tw + 11, base - 88, tw + 14, base - 88, 'N', 1.0)
        lay.rect(sx0, base - 41, 280, 1, 'S', 3.2)
        # the station's name in lit letters on a frame over the roof, its glow in the haze
        nx_ = sx0 + 196
        nw = K.text_width('КАРСК', '57')
        for px_ in (nx_ + 2, nx_ + nw - 3):
            lay.rect(px_, base - 50, 1, 9, 'I', 1.8)
        lay.rect(nx_ - 1, base - 43, nw + 2, 1, 'I', 2.0)
        gm = K.dilate(K.text_mask('КАРСК', '57'), 1)
        lay.put(gm, nx_, base - 51, 'H', 3.0, flat=True)
        K.text(lay, 'КАРСК', nx_, base - 50, 'R', 4.6, font='57', emis=True)
        # a radio mast with its red aviation lamps
        rx = 300
        if rx < w - 10:
            for yy_ in range(base - 120, base - 30):
                k_ = (yy_ - (base - 120)) / 90.0
                hw_ = int(round(k_ * 3))
                lay.px(rx - hw_, yy_, 'B', 1.4)
                lay.px(rx + hw_, yy_, 'B', 1.4)
                if yy_ % 6 == 0:
                    lay.line(rx - hw_, yy_, rx + hw_, yy_ + 6, 'B', 1.3)
            for yy_ in (base - 121, base - 92, base - 63):
                lay.rect(rx - 1, yy_, 2, 2, 'R', 4.6, emis=True)
    # haze over the lower town (evening: warm, the street lights in it)
    hz = K.nz(w, 30, 10, 351)
    yy = np.linspace(0, 1, 30, dtype=np.float32)[:, None]
    mk = (hz + 0.5) * yy > 0.32
    if dawn:
        lay.put(mk, 0, base - 18, 'B', 3.4, flat=False)
    else:
        lay.put(mk, 0, base - 18, 'H', 2.2 + hz * 0.8, flat=False)
        thr = K.pg.bayer(w, 26, 0, 0, 4)
        hz2 = K.nz(w, 26, 14, 352)
        band = (hz2 + 0.5) * np.linspace(0.2, 1.0, 26, dtype=np.float32)[:, None] > thr * 0.9 + 0.3
        lay.put(band, 0, base - 70, 'H', 2.0 + hz2, flat=False)              # a thin haze band over the roofs
    return _resolve(lay, 2), home


# =========================================================================== the embankment (A) / the station side (B)
def embankment(scene: str):
    p = 0.55
    home, w = parallax_home(scene, p)
    lay = K.tlayer(w, H, 'embankment')
    dawn = scene == L.SA
    rng = np.random.default_rng(361 if dawn else 362)
    rail = 222 if dawn else 196
    # the embankment: snowy slope, the ballast edge, the rails (side-on)
    n = K.nz(w, 4, 18, 363)[0]
    for x in range(w):
        top = rail + 2 + int(n[x] * 2)
        lay.rect(x, top, 1, H - top, 'S', 2.4 if dawn else 1.6, flat=False)
        lay.rect(x, top, 1, 2, 'B', 3.0 if dawn else 2.0)
    yy = np.linspace(0, 1, H - rail, dtype=np.float32)[:, None]
    lay.shade_rect(0, rail + 6, w, H - rail - 6, -0.4)
    lay.rect(0, rail - 1, w, 2, 'I', 3.0)
    lay.rect(0, rail - 1, w, 1, 'I', 4.4)
    for x in range(0, w, 6):
        lay.rect(x, rail + 1, 4, 1, 'D', 1.6)
    # telegraph poles and wires along the line
    poles = list(range(18, w, 74))
    for px in poles:
        lay.rect(px, rail - 40, 2, 40, 'D', 1.8 if dawn else 1.2)
        lay.rect(px - 5, rail - 38, 12, 1, 'D', 2.0 if dawn else 1.4)
        lay.rect(px - 4, rail - 32, 10, 1, 'D', 2.0 if dawn else 1.4)
        for dx in (-4, -1, 2, 5):
            lay.px(px + dx, rail - 39, 'S', 3.0)
    for i in range(len(poles) - 1):
        for dy in (-38, -32):
            K.wire(lay, poles[i], rail + dy, poles[i + 1], rail + dy, 3, 'N', 1.4)
    # birches, bare, along the foot of the embankment
    for k in range(9):
        bx = int(rng.integers(0, w))
        bh = int(rng.integers(26, 44))
        by = rail + 18 + int(rng.integers(0, 10))
        lay.rect(bx, by - bh, 1, bh, 'S', 3.4 if dawn else 2.4)
        for j in range(5):
            yy_ = by - bh + 4 + j * (bh // 6)
            ln = int(rng.integers(3, 9))
            d = 1 if rng.random() < 0.5 else -1
            lay.line(bx, yy_, bx + d * ln, yy_ - ln // 2, 'B', 2.6 if dawn else 1.8)
        for j in range(3):
            lay.px(bx, by - 6 - j * 8, 'N', 1.2)
    if dawn:
        # a far signal box with one lit window, parked wagons
        sb = 520
        if sb < w - 30:
            lay.rect(sb, rail - 26, 22, 26, 'B', 2.0)
            lay.poly([(sb - 2, rail - 26), (sb + 24, rail - 26), (sb + 11, rail - 34)], 'N', 2.0)
            lay.rect(sb + 4, rail - 20, 6, 5, 'L', 4.2, emis=True)
            lay.rect(sb + 12, rail - 20, 6, 5, 'B', 1.4)
        for k in range(4):
            wx = 120 + k * 30
            lay.rect(wx, rail - 13, 27, 11, 'K', 1.8 if k % 2 else 1.4)
            lay.rect(wx, rail - 14, 27, 1, 'S', 3.0)
            lay.ellipse(wx + 5, rail - 2, 2, 2, 'N', 1.0)
            lay.ellipse(wx + 21, rail - 2, 2, 2, 'N', 1.0)
    else:
        # the passenger side: lamp masts with cold lamps, the long platform roof far off, a footbridge
        for k, lx in enumerate(range(40, w, 110)):
            lay.rect(lx, rail - 70, 2, 70, 'I', 1.8)
            lay.rect(lx - 4, rail - 72, 10, 2, 'I', 2.2)
            lay.rect(lx - 2, rail - 70, 6, 2, 'S', 5.4, emis=True)
        fb = w - 360
        if fb > 0:
            lay.rect(fb, rail - 54, 240, 6, 'I', 1.6)
            lay.rect(fb, rail - 55, 240, 1, 'S', 2.4)
            for px in (fb + 4, fb + 120, fb + 232):
                lay.rect(px, rail - 48, 4, 48, 'I', 1.4)
            for wx in range(fb + 8, fb + 236, 10):
                lay.rect(wx, rail - 52, 5, 2, 'L', 3.2, emis=True)
    return _resolve(lay, 3), home
