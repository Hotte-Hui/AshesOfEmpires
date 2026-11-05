"""gen_great_hall_sky -- the dramatic dusk matte behind the Great Hall (L_M1_HallReveal).

Owner: hall (great_hall_3d).  Original, deterministic, berlin palette only (banded ramps + ordered dither).
Same screen mapping as before (pixel3d_post.gdshader): texel (512, 430) = optical axis at the horizon, the sun
disc at texel (612, 346) sits behind the dome's right shoulder; the final frame shows texels x 192..832,
y 194..430 above the horizon.

Layers, back to front:
  * gradient: violet-black zenith -> violet -> terracotta -> burning band at the horizon, sun glow
  * crepuscular rays fanning out from the sun (angular noise, fading with distance)
  * a towering cloud bank above the hall, self-shadowed by marching towards the sun: the undersides and the
    edges that face the sun burn gold/orange, the bodies are dark violet; torn gaps let the glow through
  * high cirrus streaks catching the last light, low stratus strips across the sun glow
  * hazy far skyline with tiny lit windows and a radio mast; a few crows
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import gen_great_hall as ggh  # noqa: E402

W, Hh = ggh.SKY_W, ggh.SKY_H
AX, AY = ggh.ANCHOR
SX, SY = ggh.SUN
H = pg.hx

SKY_RAMP = ['#211623', '#2A2130', '#342F37', '#443B43', '#57494D', '#735145', '#8D5542', '#AF6C47',
            '#D07744', '#E5945A', '#F0AE6E', '#F4BA81', '#F8D2A0', '#FCE9C8']
CLOUD_DARK = ['#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#443B43']
CLOUD_LIT = ['#443B43', '#57494D', '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A', '#F0AE6E',
             '#F4BA81', '#F8D2A0']


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sky_gradient(yy, xx):
    elev = AY - yy
    up = np.clip(elev / 300.0, 0.0, 1.0) ** 0.75
    t = np.where(elev > 0, 0.56 - 0.5 * up, 0.55 - np.clip(-elev / 200.0, 0, 1) * 0.1)
    t += 0.15 * np.exp(-((elev - 18) / 40.0) ** 2)                      # burning band on the horizon
    dx = (xx - SX) / 270.0
    dy = (yy - SY) / 105.0
    t += 0.3 * np.exp(-(dx * dx + dy * dy) * 1.6)                       # sun glow
    dx2 = (xx - SX) / 60.0
    dy2 = (yy - SY) / 38.0
    t += 0.24 * np.exp(-(dx2 * dx2 + dy2 * dy2) * 1.3)                  # hot core behind the dome
    return t


def rays(yy, xx):
    """Crepuscular rays: angular bands around the sun, fading out with distance, only above the horizon."""
    ang = np.arctan2(yy - SY, xx - SX)                                  # -pi..pi
    dist = np.sqrt((xx - SX) ** 2 + ((yy - SY) * 1.25) ** 2)
    n = 720
    noise = pg.value_noise(n, 1, 9.0, seed=71, octaves=2)[0]
    noise2 = pg.value_noise(n, 1, 3.0, seed=72, octaves=1)[0]
    idx = ((ang + math.pi) / (2 * math.pi) * (n - 1)).astype(int)
    band = (noise[idx] - 0.5) * 2.0 + (noise2[idx] - 0.5) * 0.6
    fade = np.exp(-dist / 330.0) * _smooth(40.0, 110.0, dist)
    above = _smooth(-4.0, 30.0, AY - yy)
    upward = _smooth(0.15, 0.6, -np.sin(ang))                           # rays fan upwards only
    return band * fade * above * upward


def cloud_field(yy, xx):
    """Density of the cloud bank (0..1).  Several value-noise octaves, shaped by a vertical band profile with a
    lumpy, heavier underside; anvil-like towers on both sides of the dome."""
    base = pg.value_noise(W, Hh, 64.0, seed=301, octaves=5, persistence=0.55)
    detail = pg.value_noise(W, Hh, 14.0, seed=302, octaves=3, persistence=0.5)
    # main bank: centred ~ 150-190 px above the horizon, thicker towards the sides of the frame
    elev = AY - yy
    side = np.clip(np.abs(xx - 512.0) / 360.0, 0.0, 1.0)
    centre = 175.0 + 25.0 * side
    thick = 52.0 + 40.0 * side
    prof = np.exp(-((elev - centre) / thick) ** 2)
    # towers rising on the left and right of the dome (frame the crown)
    for cx, cy, rx, ry in ((300.0, 230.0, 110.0, 130.0), (790.0, 220.0, 120.0, 120.0)):
        prof = np.maximum(prof, np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)) * 0.95)
    gaps = pg.value_noise(W, Hh, 120.0, seed=303, octaves=2)
    d = prof * (0.45 + 0.8 * base) * (0.55 + 0.7 * gaps) + (detail - 0.5) * 0.35
    # keep a clear window right around the sun so the glow and the rays read
    sd = np.sqrt(((xx - SX) / 170.0) ** 2 + ((yy - SY) / 85.0) ** 2)
    d *= 0.25 + 0.75 * _smooth(0.55, 1.25, sd)
    return d


def light_march(dens, steps=10, step=4.0):
    """Light reaching each cloud pixel from the sun: march towards the sun accumulating density."""
    h, w = dens.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = SX - xx
    dy = SY - yy
    L = np.sqrt(dx * dx + dy * dy) + 1e-3
    ux, uy = dx / L, dy / L
    acc = np.zeros_like(dens)
    for k in range(1, steps + 1):
        px = np.clip(xx + ux * step * k, 0, w - 1).astype(int)
        py = np.clip(yy + uy * step * k, 0, h - 1).astype(int)
        acc += np.clip(dens[py, px] - 0.42, 0, 1)
    return np.exp(-acc * 0.9)


def make_sky():
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    t = sky_gradient(yy, xx)
    t += 0.07 * rays(yy, xx)
    t += (pg.value_noise(W, Hh, 90, seed=5, octaves=3) - 0.5) * 0.04
    img = ggh.ramp_fill(np.clip(t, 0, 1), SKY_RAMP, seam=0.3)
    # ---- the cloud bank
    dens = cloud_field(yy, xx)
    cloud = dens > 0.5
    lightk = light_march(dens)
    sund = np.sqrt(((xx - SX) / 420.0) ** 2 + ((yy - SY) / 220.0) ** 2)
    warm = np.clip(1.25 - sund, 0, 1)
    # rim: cloud pixels whose sun-ward neighbour is clear sky, and the thin lit underside
    edge_amt = _smooth(0.5, 0.74, dens)                                   # 0 at the cloud edge -> 1 inside
    lit = lightk * (0.15 + 0.85 * warm) * (1.15 - 0.6 * edge_amt)
    bump = pg.value_noise(W, Hh, 10.0, seed=304, octaves=3)
    # billows: lighter tops of the internal bumps (light from above-behind), darker cores
    body_t = np.clip(0.26 + 0.42 * (1.0 - edge_amt) * warm + 0.55 * (bump - 0.4) * (0.4 + 0.6 * lightk)
                     + 0.12 * np.clip((AY - yy) / 380.0, 0, 1), 0, 1)
    body = ggh.ramp_fill(body_t, CLOUD_DARK, seam=0.35)
    lit_img = ggh.ramp_fill(np.clip(lit, 0, 1), CLOUD_LIT, seam=0.35)
    use_lit = cloud & (lit > 0.28)
    img[cloud] = body[cloud]
    img[use_lit] = lit_img[use_lit]
    # ---- high cirrus streaks (pink-ochre last light) and low stratus strips across the glow
    rng = np.random.default_rng(11)
    cir = np.zeros((Hh, W), bool)
    for k in range(9):
        length = rng.uniform(140, 420)
        x0 = rng.uniform(-60, W - length * 0.5)
        y0 = AY - rng.uniform(240, 330)
        m, _ = ggh.stratus_mask(W, Hh, int(x0), y0, length, rng.uniform(1.5, 3.5), 500 + k, taper=0.3)
        cir |= m
    cir &= ~cloud
    cir_t = np.clip(0.25 + 0.5 * warm, 0, 1)
    cimg = ggh.ramp_fill(cir_t, ['#342F37', '#443B43', '#57494D', '#735145', '#8D5542'], seam=0.4)
    img[cir] = cimg[cir]
    low = np.zeros((Hh, W), bool)
    belly = np.zeros((Hh, W), bool)
    for k in range(10):
        length = rng.uniform(70, 260)
        x0 = rng.uniform(-60, W - length * 0.4)
        y0 = AY - rng.uniform(14, 70)
        m, b = ggh.stratus_mask(W, Hh, int(x0), y0, length, rng.uniform(2, 5), 600 + k)
        low |= m
        belly |= b
    lw = np.clip(0.15 + 0.85 * warm, 0, 1)
    limg = ggh.ramp_fill(np.clip(0.1 + 0.25 * warm, 0, 1), ['#211623', '#2A2130', '#342F37', '#443B43'],
                         seam=0.35)
    img[low] = limg[low]
    bimg = ggh.ramp_fill(lw, ['#57494D', '#735145', '#AF6C47', '#D07744', '#F0AE6E', '#F8D2A0'], seam=0.4)
    sel = belly & low
    img[sel] = bimg[sel]
    # ---- the sun disc (mostly hidden behind the dome's right shoulder)
    d = np.sqrt((xx - SX) ** 2 + (yy - SY) ** 2)
    img[d <= 13.5] = H('#F8D2A0')
    img[d <= 11.0] = H('#FCE9C8')
    # ---- far skyline with lit windows and a radio mast
    sk = pg.Layer(W, Hh)
    rng2 = np.random.default_rng(3)
    lights = []
    x = 0
    while x < W:
        w = int(rng2.integers(14, 46))
        h = int(rng2.integers(3, 12))
        sk.rect(x, AY - h, w, h + 12, H('#443B43'))
        for _ in range(int(rng2.integers(0, 3))):
            lights.append((x + int(rng2.integers(1, max(2, w - 1))), AY - int(rng2.integers(1, max(2, h)))))
        if rng2.random() < 0.3:
            cx = x + int(rng2.integers(2, max(3, w - 3)))
            ch = int(rng2.integers(10, 22))
            sk.rect(cx, AY - h - ch, 2, ch, H('#443B43'))
        x += w + int(rng2.integers(0, 6))
    sk.line(842, AY - 64, 842, AY, H('#443B43'))
    for k in range(0, 64, 8):
        sk.px(841, AY - 64 + k, H('#443B43'))
        sk.px(843, AY - 64 + k + 4, H('#443B43'))
    a = sk.alpha()
    sk_t = np.clip(0.35 + 0.5 * warm, 0, 1)
    skc = ggh.ramp_fill(sk_t, ['#342F37', '#443B43', '#57494D', '#735145', '#8D5542'], seam=0.4)
    img[a] = skc[a]
    for (lx, ly) in lights:
        if 0 <= lx < W and 0 <= ly < Hh:
            img[ly, lx] = H('#F4BA81')
    img[AY - 65, 842] = H('#D07744')                                    # aviation light on the mast
    # ---- a few crows
    for (bx, by) in [(300, 300), (309, 296), (318, 303), (700, 270)]:
        for ddx, ddy in ((-2, -1), (-1, 0), (0, 0), (1, 0), (2, -1)):
            img[by + ddy, bx + ddx] = H('#211623')
    # clean orphan pixels inside flat areas (keeps the dither seams crisp)
    rgba = np.concatenate([img[..., :3], np.full((Hh, W, 1), 255, np.uint8)], -1)
    ggh.save_rgba(rgba, ggh.out('sky.png'))
    return rgba


if __name__ == '__main__':
    make_sky()
    print('sky written')
