"""gen_title_splash -- original boot-sequence art of ASHES OF EMPIRES: THE LAST WINTER (round 11, owner: splash).

Draws procedurally and deterministically (no image input; no reference is sampled, traced or copied):
  assets/ui/splash/title_scene.png   640x420  key visual: Karsk's snowy railyard (left, cold dusk) and the domed Great
                                              Hall of Berlin (right, warm afterglow) divided by ONE railway line that
                                              runs to the horizon, where a train's lamp burns.  The boot card shows rows
                                              TILT..TILT+359 first and tilts up to rows 0..359 (camera rotation: all
                                              layers move together, so the rails always meet the lamp).
  assets/ui/splash/title_lamp.png    640x420  the headlamp, its halo, a horizontal flare and its light on the rails
                                              (binary alpha; the card fades / pulses it as the train comes closer)
  assets/ui/splash/title_logo.png    ASHES OF EMPIRES -- own 7x9 capitals -> Scale3x -> bold verticals, forged
                                     copper ramp, bevel, snow lying on the letters, ash flecks, outline + drop shadow
  assets/ui/splash/title_sub.png     ◆── THE LAST WINTER ──◆ -- the same capitals at 1x in snow tones
  assets/ui/splash/studio_mark.png   40x40 studio emblem: a broken ring of ash around a glowing ember (shown x4)
  assets/ui/splash/studio_glow.png   40x40 the ember's dithered glow (pulsed at runtime)
No insignia, no flags, no text other than the game title; no third-party logo of any kind.
One art pixel = one world pixel; the boot card shows the scene x3 (1920x1080) with nearest filtering.

Run:  py -3 -P tools/pixelgen/gen_title_splash.py [--preview=DIR]   (DIR gets a small review sheet, never the project)
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'splash')
W, H = 640, 420
HZ = 232            # horizon row (final view = rows 0..359)
VPX = 320           # vanishing point of the railway (the train's lamp)
TILT = 60           # the card starts on rows TILT..TILT+359
GROUND = H - HZ     # rows of ground below the horizon
hx = pg.hx


def C(h: str) -> np.ndarray:
    return hx(h)


def arr(cols) -> np.ndarray:
    return np.stack([C(c) for c in cols])


B4 = pg.bayer(W, H, size=4)
B8 = pg.bayer(W, H, size=8)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def pick(idx: np.ndarray, ramp: np.ndarray, thr: np.ndarray) -> np.ndarray:
    """Ordered-dither a float index into a colour ramp."""
    i = np.floor(idx).astype(int)
    i = i + ((idx - i) > thr)
    return ramp[np.clip(i, 0, len(ramp) - 1)]


def aniso_noise(w: int, h: int, cx: float, cy: float, seed: int, octaves: int = 3, pers: float = 0.5) -> np.ndarray:
    """fBm value noise with different cell sizes in x and y (streaky dusk clouds, wind-blown snow)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    tot, amp = 0.0, 1.0
    for _ in range(octaves):
        gw, gh = int(math.ceil(w / cx)) + 2, int(math.ceil(h / cy)) + 2
        g = rng.random((gh, gw)).astype(np.float32)
        xs, ys = np.arange(w) / cx, np.arange(h) / cy
        x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
        fx, fy = xs - x0, ys - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a, b = g[y0[:, None], x0[None, :]], g[y0[:, None], x0[None, :] + 1]
        c, d = g[y0[:, None] + 1, x0[None, :]], g[y0[:, None] + 1, x0[None, :] + 1]
        top, bot = a + (b - a) * fx[None, :], c + (d - c) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None])
        tot += amp
        amp *= pers
        cx, cy = max(1.0, cx / 2), max(1.0, cy / 2)
    return out / tot


def smooth(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def warmth(x) -> np.ndarray:
    """0 = Karsk (cold, left) .. 1 = Berlin (warm, right); the line between them is the railway."""
    return smooth(268.0, 392.0, x)


# ----------------------------------------------------------------------------- sky
COLD_SKY = ['#04090D', '#05090F', '#06151D', '#0A1219', '#0E1A20', '#13252B', '#1B3033', '#26403F', '#36534D',
            '#4A675C', '#6F8576', '#83998A', '#98AD9A', '#AFC1AA', '#C7D3BA', '#DCE2C8', '#E6DEC2']
WARM_SKY = ['#04090D', '#05090F', '#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#443B43', '#57494D',
            '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A', '#F0AE6E', '#F4BA81', '#F8D2A0']


def glow(gx, gy, rx, ry, k, p=1.6) -> np.ndarray:
    d = np.sqrt(((XX - gx) / rx) ** 2 + ((YY - gy) / ry) ** 2)
    return np.clip(1 - d, 0, 1) ** p * k


def sky_brightness() -> np.ndarray:
    t = np.clip(YY / HZ, 0, 1)
    b = (t ** 2.6) * 8.0
    b += glow(482, HZ + 8, 300, 122, 8.2, 1.8)      # afterglow behind the dome (Berlin)
    b += glow(112, HZ + 6, 250, 92, 4.4, 1.6)       # cold last light over Karsk
    b += glow(VPX, HZ, 120, 26, 1.6, 1.4)           # a pale seam where the line meets the sky
    return b


def paint_sky() -> pg.Layer:
    l = pg.Layer(W, H)
    b = sky_brightness()
    w = warmth(XX) > B8
    cold, warm = arr(COLD_SKY), arr(WARM_SKY)
    col = np.where(w[..., None], pick(b, warm, B4), pick(b, cold, B4))
    l.c[:] = col
    # stars over the dark top (never where the dusk is bright)
    rng = np.random.default_rng(1964)
    star = (rng.random((H, W)) < 0.0026) & (YY < 128) & (b < 1.4)
    tone = rng.random((H, W))
    l.c[star & (tone < 0.82)] = C('#4A5A5B')
    l.c[star & (tone >= 0.82) & (tone < 0.97)] = C('#7A93A8')
    l.c[star & (tone >= 0.97)] = C('#E6DEC2')
    # streaky dusk clouds (stratus): silhouettes against the glow, undersides lit from below the horizon
    n = aniso_noise(W, H, 96, 6, seed=11, octaves=4)
    band = np.exp(-((YY - 182) / 24) ** 2) * 0.60 + np.exp(-((YY - 112) / 10) ** 2) * 0.30 \
        + np.exp(-((YY - 150) / 8) ** 2) * 0.22
    cloud = (n + band > 1.04) & (YY < HZ - 3)
    below = np.zeros_like(cloud)
    below[:-1] = cloud[1:]
    below2 = np.zeros_like(cloud)
    below2[:-2] = cloud[2:]
    rim = cloud & ~(below & below2)
    body = cloud & ~rim
    cb = b * 0.52 + 0.4
    rb = b * 0.92 + 1.6
    l.c[body] = np.where(w[..., None], pick(cb, warm, B4), pick(cb, cold, B4))[body]
    l.c[rim] = np.where(w[..., None], pick(rb, warm, B4), pick(rb, cold, B4))[rim]
    return l


# ----------------------------------------------------------------------------- far skylines
KARSK_BODY, KARSK_MID, KARSK_SNOW = '#0A1219', '#0E1A20', '#26403F'
BERLIN_BODY, BERLIN_MID, BERLIN_LINE = '#1B1520', '#211623', '#2A2130'


def window_rows(l: pg.Layer, x, y0, x1, y1, step_x, step_y, dark, lit, rng, p_lit, p_dark=0.45):
    for wy in range(y0, y1, step_y):
        for wx in range(x, x1, step_x):
            r = rng.random()
            if r < p_lit:
                l.rect(wx, wy, 2, 2, C(lit), em=C(lit))
            elif r < p_dark:
                l.rect(wx, wy, 2, 2, C(dark))


def karsk(l: pg.Layer, smoke: pg.Layer):
    rng = np.random.default_rng(64)
    body, mid = C(KARSK_BODY), C(KARSK_MID)
    base = HZ
    # water tower (railway) far left
    l.poly([(16, base), (20, base - 44), (34, base - 44), (38, base)], body)
    for k in range(base - 40, base, 6):
        l.hline(19, k, 16, mid)
    l.rect(12, base - 60, 30, 16, body)
    l.ellipse(27, base - 60, 15, 4, body)
    l.poly([(12, base - 61), (27, base - 70), (42, base - 61)], body)
    l.rect(13, base - 52, 28, 1, mid)
    # sawtooth depot shed
    l.rect(44, base - 16, 66, 16, body)
    for k in range(44, 108, 9):
        l.poly([(k, base - 16), (k + 9, base - 16), (k + 9, base - 23)], body)
    window_rows(l, 48, base - 11, 106, base - 3, 5, 5, KARSK_MID, '#9A5A2F', rng, 0.06)
    # slab blocks and silos
    for (x, w, h) in [(58, 34, 46), (150, 40, 60), (196, 36, 40), (262, 30, 22)]:
        l.rect(x, base - h, w, h, body)
        window_rows(l, x + 3, base - h + 4, x + w - 3, base - 2, 6, 6, KARSK_MID, '#D79A62', rng, 0.035)
        l.hline(x, base - h, w, mid)
    for i in range(4):
        sx, sh = 104 + i * 11, 58 + (i % 2) * 6
        l.rect(sx, base - sh, 10, sh, body)
        l.ellipse(sx + 5, base - sh, 5, 3, body)
        l.vline(sx + 2, base - sh + 2, sh - 4, mid)
    l.rect(102, base - 78, 6, 78, body)                   # silo elevator tower
    l.rect(100, base - 82, 10, 5, body)
    # chimneys with smoke drifting east, toward the other empire
    for (cx, ch, cw, reach) in [(144, 106, 4, 150), (212, 120, 5, 230), (236, 84, 3, 0)]:
        l.rect(cx, base - ch, cw, ch, body)
        l.rect(cx - 1, base - ch, cw + 2, 2, body)
        for k in range(base - ch + 8, base, 14):
            l.hline(cx, k, cw, mid)
        top = base - ch
        if reach:
            pg.smoke_ribbon(smoke, [(cx + cw / 2, top - 2), (cx + 14, top - 16), (cx + reach * 0.4, top - 27),
                                    (cx + reach, top - 33)], 2, 9,
                            [C('#05090F'), C('#0A1219'), C('#0E1A20'), C('#13252B'), C('#1B3033')],
                            seed=cx * 7 + 3, gaps=0.5)
    # lattice crane
    pg.truss(l, 240, base - 96, 304, base - 96, 3, body, step=5)
    pg.truss(l, 250, base - 96, 250, base, 4, body, step=6)
    l.rect(226, base - 96, 14, 5, body)
    pg.wire(l, 300, base - 93, 300, base - 52, 0, body)
    l.rect(297, base - 52, 7, 4, body)
    # low sheds toward the line
    l.rect(274, base - 12, 34, 12, body)
    l.poly([(272, base - 12), (290, base - 19), (310, base - 12)], body)
    pg.snow_caps(l, [C('#1B3033'), C(KARSK_SNOW)], depth=1, seed=5, coverage=0.75)


def berlin(l: pg.Layer):
    rng = np.random.default_rng(1937)
    body, mid, line = C(BERLIN_BODY), C(BERLIN_MID), C(BERLIN_LINE)
    base = HZ
    # far city blocks (haze-light) all along the right half
    for (x, w, h) in [(330, 26, 10), (352, 18, 14), (548, 30, 12), (600, 40, 16), (626, 20, 10)]:
        l.rect(x, base - h, w, h, C('#2A2130'))
    # side wings with tall window slits
    for (x0, x1, h) in [(360, 410, 24), (534, 600, 28), (600, 640, 20)]:
        l.rect(x0, base - h, x1 - x0, h, body)
        l.hline(x0, base - h, x1 - x0, line)
        for wx in range(x0 + 3, x1 - 2, 6):
            r = rng.random()
            col = '#E5945A' if r < 0.12 else ('#8D5542' if r < 0.2 else BERLIN_LINE)
            l.rect(wx, base - h + 5, 2, h - 9, C(col), em=C(col) if r < 0.2 else None)
    # the Great Hall: podium with colonnade, drum, dome, lantern (fictional, no insignia)
    l.rect(404, base - 34, 136, 34, body)
    l.rect(400, base - 36, 144, 3, line)
    l.hline(404, base - 32, 136, C('#120C14'))
    for px_ in range(408, 538, 4):
        l.vline(px_, base - 29, 27, line)
    l.rect(452, base - 22, 40, 22, C('#120C14'))            # the great portal
    l.vline(471, base - 22, 22, C('#8D5542'))                # a seam of light through the doors
    l.rect(414, base - 50, 116, 15, body)
    for px_ in range(418, 528, 7):
        l.rect(px_, base - 47, 3, 9, mid)
    l.hline(412, base - 51, 120, line)
    cx, cy, rx, ry = 472, base - 50, 60, 56
    m, x0, y0 = l.ellipse_mask(cx, cy, rx, ry)
    m[int(cy) - y0 + 1:, :] = False
    l._put(m, x0, y0, body)
    hh, ww = m.shape
    my, mx = np.mgrid[0:hh, 0:ww]
    tdome = ((mx + x0) - (cx - rx * 0.1)) / (rx * 1.1)          # the afterglow side is a little lighter
    bt = pg.bayer(ww, hh, x0, y0)
    shade = np.where((tdome > 0.62) & (tdome - 0.62 > bt * 0.5), 2, np.where(tdome > bt, 1, 0))
    tone_cols = np.stack([body, C(BERLIN_LINE), C('#342F37')])
    l._put(m, x0, y0, tone_cols[shade])
    for k in range(-5, 6):                                   # ribs (meridians)
        phi = k * 0.27
        for j in range(0, 60):
            lat = j / 59 * (math.pi / 2)
            x = cx + rx * math.cos(lat) * math.sin(phi)
            y = cy - ry * math.sin(lat)
            l.px(int(round(x)), int(round(y)), line)
    for j in range(3):                                       # horizontal rings
        lat = (0.25 + 0.22 * j) * (math.pi / 2)
        y = int(round(cy - ry * math.sin(lat)))
        half = rx * math.cos(lat)
        l.hline(int(round(cx - half)), y, int(round(2 * half)), line)
    l.rect(465, int(cy - ry) - 11, 14, 12, body)              # lantern
    for px_ in range(467, 478, 3):
        l.vline(px_, int(cy - ry) - 9, 8, line)
    l.ellipse(472, int(cy - ry) - 11, 7, 4, body)
    l.vline(472, int(cy - ry) - 26, 12, body)
    l.px(471, int(cy - ry) - 16, body)
    l.px(473, int(cy - ry) - 16, body)
    # rim light: the afterglow burns along the dome's right shoulder and the lantern
    a = l.alpha()
    up = np.zeros_like(a)
    up[1:] = a[:-1]
    right = np.zeros_like(a)
    right[:, :-1] = a[:, 1:]
    edge = a & (~up | ~right) & (XX > 452) & (YY < base - 36) & (YY > 40)
    t = np.clip((XX - 452) / 74, 0, 1)
    rim_col = np.where((t > B4)[..., None], C('#D07744'), C('#8D5542'))
    l.c[edge] = rim_col[edge]
    ledge = a & ~up & (XX <= 452) & (XX > 404) & (YY < base - 36)
    l.c[ledge] = C('#57494D')


def train(l: pg.Layer):
    """The locomotive, tiny at the vanishing point (head-on silhouette)."""
    body = C('#05090F')
    l.rect(VPX - 4, HZ - 7, 9, 7, body)
    l.rect(VPX - 3, HZ - 9, 7, 2, body)
    l.rect(VPX - 1, HZ - 12, 3, 3, body)                      # chimney
    l.rect(VPX - 5, HZ - 1, 11, 1, body)


# ----------------------------------------------------------------------------- ground, railway, poles
COLD_SNOW = ['#0B1C24', '#14272B', '#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E', '#7E8E8C', '#A3B1AD']
WARM_SNOW = ['#1B1520', '#211623', '#2A2130', '#342F37', '#443B43', '#57494D', '#6E6A73', '#8F8A92', '#B2ACB0']


def rail_x(y, side: int, spread: float = 130.0):
    return VPX + side * spread * (y - HZ) / GROUND


def track(l: pg.Layer, drift: np.ndarray, offset: float, used: bool):
    """One track in perspective: sleepers at equal ground spacing, two rails meeting at the lamp.
    `used` = the main line (cleared, rails polished); sidings lie under snow."""
    d = 1.0
    while True:
        y = HZ + GROUND / d
        if y - HZ < 1.2:
            break
        sv = (y - HZ) / GROUND
        half = 154.0 * sv
        th = max(1, int(round(7.0 * sv)))
        yi = int(round(y))
        cxs = VPX + offset * sv
        x0, x1 = int(round(cxs - half)), int(round(cxs + half))
        if not used and th < 2:
            d += 0.21
            continue
        for xs in range(max(0, x0), min(W, x1 + 1)):
            buried = (not used) and (drift[min(H - 1, yi), xs] > 0.36 or abs(xs - cxs) > half * 0.8)
            if buried:
                continue
            l.rect(xs, yi - th + 1, 1, th, C('#22180F'))
            if th >= 2:
                snowy = drift[min(H - 1, yi), xs] > (0.52 if used else 0.36)
                l.px(xs, yi - th + 1, C('#62716E') if snowy else C('#4A3626'))
        d += 0.21
    for side in (-1, 1):
        for y in range(HZ, H):
            sv = (y - HZ) / GROUND
            x = VPX + (offset + side * 130.0) * sv
            wd = max(1, int(round(4.2 * sv)))
            x0 = int(round(x - wd / 2))
            if not used and drift[y, min(W - 1, max(0, x0))] > 0.6:
                continue                                      # drifts cover the siding's rails in places
            warm = x > VPX
            head = ('#AE8A6C' if warm else '#A3B1AD') if used else ('#57494D' if warm else '#4A5A5B')
            l.hline(x0, y, wd, C('#1E2329'))
            l.px(x0 + (wd - 1 if side < 0 else 0), y, C(head))
            if wd >= 3 and used:
                l.px(x0 + (wd - 2 if side < 0 else 1), y, C('#94735C' if warm else '#7C8690'))


def wagons(l: pg.Layer, offset: float, d_from: float, count: int):
    """A standing freight train on the siding (box cars, far down the yard): end faces + the side toward the line."""
    half, hgt, length, gap = 270.0, 600.0, 2.3, 0.35
    d = d_from
    for i in range(count):
        d1, d2 = d, d + length * (d / d_from) ** 0.0
        xr = offset + half
        xl = offset - half

        def P(X, Hh, dd):
            return (VPX + X / dd, HZ + (GROUND - Hh) / dd)
        side = [P(xr, 30, d1), P(xr, 30, d2), P(xr, hgt, d2), P(xr, hgt, d1)]
        end = [P(xl, 30, d1), P(xr, 30, d1), P(xr, hgt, d1), P(xl, hgt, d1)]
        l.poly(side, C('#0E1A20'))
        l.poly(end, C('#0A1219'))
        for k in range(1, 6):                                 # planks / doors on the side
            dk = d1 + (d2 - d1) * k / 6
            a, b = P(xr, 40, dk), P(xr, hgt - 10, dk)
            l.line(a[0], a[1], b[0], b[1], C('#0A1219'))
        r0, r1 = P(xr, hgt, d1), P(xr, hgt, d2)
        l.line(r0[0], r0[1], r1[0], r1[1], C('#4A5A5B'))      # snow on the roof edge
        e0, e1 = P(xl, hgt, d1), P(xr, hgt, d1)
        l.line(e0[0], e0[1] - 1, e1[0], e1[1] - 1, C('#62716E'))
        w0, w1 = P(xr, 30, d1), P(xr, 30, d2)
        l.line(w0[0], w0[1], w1[0], w1[1], C('#05090F'))
        d = d2 + gap * (d2 / d_from)


def paint_ground(l: pg.Layer):
    g = YY >= HZ
    s = np.clip((YY - HZ) / GROUND, 0, 1)
    tone = 4.6 - 3.4 * s ** 0.7
    tone += glow(112, HZ, 260, 34, 1.3) + glow(482, HZ, 280, 34, 1.5) + glow(VPX, HZ, 70, 16, 1.0)
    drift = aniso_noise(W, H, 60, 5, seed=21, octaves=4)
    swell = aniso_noise(W, H, 150, 14, seed=23, octaves=3)
    tone += (drift - 0.5) * 2.0 * (0.35 + s) + (swell - 0.5) * 2.4 * (0.25 + s)
    streak = aniso_noise(W, H, 24, 2, seed=22, octaves=2)
    tone += np.where(streak > 0.72, 0.8, 0.0) * (0.25 + s)
    half_bed = 172.0 * s
    dxv = np.abs(XX - VPX)
    bed = g & (dxv < half_bed)
    bank = g & (dxv >= half_bed) & (dxv < half_bed + 3 + 12 * s)
    tone = np.where(bed, tone - 1.3, tone)
    tone = np.where(bank, tone + 0.9, tone)
    w = warmth(XX) > B8
    col = np.where(w[..., None], pick(tone, arr(WARM_SNOW), B4), pick(tone, arr(COLD_SNOW), B4))
    l.c[g] = col[g]
    rng = np.random.default_rng(31)
    speck = bed & (rng.random((H, W)) < 0.10 + 0.18 * s) & (drift < 0.55)
    l.c[speck] = np.where(w[..., None], C('#2A2130'), C('#14272B'))[speck]
    track(l, drift, -470.0, False)                            # Karsk railyard sidings
    track(l, drift, -860.0, False)
    track(l, drift, 0.0, True)                                # the line


def signal_mast(l: pg.Layer):
    """Semaphore signal on the Karsk side of the line (red lamp)."""
    body = C('#03070A')
    x, base, top = 196, 334, 176
    l.rect(x, top, 3, base - top, body)
    for k in range(top + 6, base - 4, 5):                   # ladder
        l.hline(x + 4, k, 3, body)
    l.vline(x + 6, top + 4, base - top - 8, body)
    l.rect(x - 22, top + 8, 22, 3, body)                     # arm
    l.rect(x - 24, top + 6, 4, 7, body)
    l.rect(x - 2, top - 6, 7, 7, body)                       # lamp case
    l.rect(x - 1, top - 4, 2, 2, C('#A8382E'), em=C('#A8382E'))
    l.px(x - 1, top - 4, C('#C8503C'))
    l.rect(x - 4, base, 11, 4, body)
    l.vline(x - 1, top + 2, base - top - 6, C('#1B3033'))   # cold rim from the Karsk sky


def telegraph(l: pg.Layer):
    """A line of telegraph poles along the Berlin side, receding to the lamp; wires sag between them."""
    body = C('#03070A')
    tips = []
    for d in [1.12, 1.55, 2.2, 3.1, 4.4, 6.3, 9.0, 13.0]:
        base = HZ + GROUND / d
        x = VPX + 296.0 / d
        hgt = 212.0 / d
        wpx = max(1, int(round(4 / d)))
        top = base - hgt
        l.rect(int(round(x)), int(round(top)), wpx, int(round(hgt)), body)
        arm = max(2, int(round(30 / d)))
        for k, yy in enumerate([top + 4 / d, top + 12 / d]):
            l.hline(int(round(x - arm / 2)), int(round(yy)), arm + wpx, body)
            if d < 3.5:
                for ix in (-arm / 2, -arm / 4, arm / 4 + wpx, arm / 2 + wpx - 1):
                    l.px(int(round(x + ix)), int(round(yy)) - 1, C('#4A5A5B'))
        tips.append((x - arm / 2, top + 4 / d, x + arm / 2 + wpx, top + 12 / d))
    for (a, b) in zip(tips[:-1], tips[1:]):
        pg.wire(l, a[0], a[1], b[0], b[1], 3.0 * (a[1] - b[1] + 6) / 14 + 1, C('#05090F'))
        pg.wire(l, a[2], a[3], b[2], b[3], 3.0 * (a[1] - b[1] + 6) / 14 + 1, C('#05090F'))
    pg.wire(l, tips[-1][0], tips[-1][1], VPX + 6, HZ - 3, 1, C('#0A1219'))


def snow_fence(l: pg.Layer):
    """A half-buried snow fence on the Berlin side, running toward the lamp (gives the empty plain depth)."""
    body = C('#120C14')
    prev = None
    d = 1.25
    while d < 14:
        base = HZ + GROUND / d
        x = VPX + 520.0 / d
        hgt = max(1.0, 26.0 / d)
        l.rect(int(round(x)), int(round(base - hgt)), max(1, int(round(3 / d))), int(round(hgt)) + 1, body)
        if prev is not None:
            px_, pb, ph = prev
            for k in (0.35, 0.75):
                l.line(px_, pb - ph * k, x, base - hgt * k, body)
        prev = (x, base, hgt)
        d *= 1.18


def foreground(l: pg.Layer):
    """Framing: snowed-in weeds and a buried fence in the corners."""
    body = C('#020507')
    rng = np.random.default_rng(77)
    pg.grass_tufts(l, 0, 120, H - 1, [body, C('#05090F')], density=0.55, hmax=16, seed=78)
    pg.grass_tufts(l, 0, 70, H - 14, [body], density=0.4, hmax=12, seed=79)
    pg.grass_tufts(l, 560, 640, H - 1, [body, C('#05090F')], density=0.5, hmax=14, seed=80)
    for k in range(4):
        x = 590 + k * 14 + int(rng.integers(-2, 3))
        l.rect(x, H - 40 + k * 3, 3, 40, body)
        l.px(x, H - 41 + k * 3, C('#57494D'))
    l.line(586, H - 30, 640, H - 22, body)
    l.line(586, H - 20, 640, H - 12, body)


# ----------------------------------------------------------------------------- the lamp
def paint_lamp() -> pg.Layer:
    l = pg.Layer(W, H)
    lx, ly = VPX, HZ - 4
    d = np.sqrt(((XX - lx) / 1.35) ** 2 + (YY - ly) ** 2)
    rings = [(2.2, '#FCE9C8', 1.0), (4.6, '#F8D2A0', 0.9), (8.0, '#F4BA81', 0.55), (14.0, '#F0AE6E', 0.3),
             (22.0, '#E5945A', 0.14), (32.0, '#AF6C47', 0.06)]
    prev = 0.0
    sparkle = np.random.default_rng(228).random((H, W))       # random (not Bayer) threshold: a round, glittering halo
    for (r, col, dens) in rings:
        sel = (d >= prev) & (d < r)
        fall = 1.0 - (d - prev) / max(0.001, r - prev) * 0.45
        on = sel & ((B8 if r < 5 else sparkle) < dens * fall)
        l.c[on] = C(col)
        prev = r
    # anamorphic flare along the horizon
    fl = (np.abs(YY - ly) < 0.5) & (np.abs(XX - lx) < 86)
    fd = np.clip(1.0 - np.abs(XX - lx) / 86.0, 0.0, 1.0)
    on = fl & (B8 < fd ** 1.4 * 0.95)
    l.c[on & (np.abs(XX - lx) < 30)] = C('#F8D2A0')
    l.c[on & (np.abs(XX - lx) >= 30)] = C('#F0AE6E')
    # the light running down the rails toward the viewer
    for side in (-1, 1):
        for y in range(HZ, HZ + 96):
            sv = (y - HZ) / GROUND
            x = rail_x(y, side)
            wd = max(1, int(round(4.2 * sv)))
            x0 = int(round(x - wd / 2))
            hx_ = x0 + (wd - 1 if side < 0 else 0)
            k = (y - HZ) / 96.0
            if B8[y, hx_] < (1.0 - k) ** 1.6 * 0.95:
                l.px(hx_, y, C('#F8D2A0') if k < 0.25 else C('#F0AE6E'))
    # a faint sheen on the trodden snow between the rails
    s = np.clip((YY - HZ) / GROUND, 0, 1)
    between = (YY > HZ + 1) & (np.abs(XX - VPX) < 120 * s) & (YY < HZ + 60)
    k = np.clip((YY - HZ) / 60.0, 0, 1)
    sheen = between & (B8 < (1 - k) ** 2 * 0.22) & (l.c[..., 3] == 0)
    l.c[sheen] = C('#8D5542')
    return l


# ----------------------------------------------------------------------------- lettering
# Own 7x9 capitals (1-px strokes): the title is Scale3x-ed and given bold verticals, the subtitle stays 1x.
GLYPHS = {
    'A': ["...#...", "..#.#..", ".#...#.", ".#...#.", "#.....#", "#######", "#.....#", "#.....#", "#.....#"],
    'S': [".#####.", "#.....#", "#......", ".##....", "...###.", "......#", "......#", "#.....#", ".#####."],
    'H': ["#.....#", "#.....#", "#.....#", "#.....#", "#######", "#.....#", "#.....#", "#.....#", "#.....#"],
    'E': ["#######", "#......", "#......", "#......", "######.", "#......", "#......", "#......", "#######"],
    'O': [".#####.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", ".#####."],
    'F': ["#######", "#......", "#......", "#......", "######.", "#......", "#......", "#......", "#......"],
    'M': ["#.....#", "##...##", "#.#.#.#", "#..#..#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#"],
    'P': ["######.", "#.....#", "#.....#", "#.....#", "######.", "#......", "#......", "#......", "#......"],
    'I': ["###", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    'R': ["######.", "#.....#", "#.....#", "#.....#", "######.", "#...#..", "#....#.", "#.....#", "#.....#"],
    'T': ["#######", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "...#..."],
    'L': ["#......", "#......", "#......", "#......", "#......", "#......", "#......", "#......", "#######"],
    'W': ["#.....#", "#.....#", "#.....#", "#.....#", "#..#..#", "#..#..#", "#.#.#.#", "##...##", "#.....#"],
    'N': ["#.....#", "##....#", "#.#...#", "#.#...#", "#..#..#", "#...#.#", "#...#.#", "#....##", "#.....#"],
}


def glyph(ch: str) -> np.ndarray:
    return np.array([[c == '#' for c in row] for row in GLYPHS[ch]], bool)


def scale3x(m: np.ndarray) -> np.ndarray:
    """Scale3x (AdvMAME3x) on a binary mask: smooth diagonals, 3-px strokes."""
    h, w = m.shape
    p = np.pad(m, 1)
    A, B, Cc = p[:-2, :-2], p[:-2, 1:-1], p[:-2, 2:]
    D, E, F = p[1:-1, :-2], p[1:-1, 1:-1], p[1:-1, 2:]
    G, Hh, I = p[2:, :-2], p[2:, 1:-1], p[2:, 2:]
    o = np.zeros((h * 3, w * 3), bool)
    c1 = (D == B) & (D != Hh) & (B != F)
    c2 = (B == F) & (B != D) & (F != Hh)
    c3 = (D == Hh) & (D != B) & (Hh != F)
    c4 = (Hh == F) & (D != Hh) & (B != F)
    o[0::3, 0::3] = np.where(c1, D, E)
    o[0::3, 1::3] = np.where((c1 & (E != Cc)) | (c2 & (E != A)), B, E)
    o[0::3, 2::3] = np.where(c2, F, E)
    o[1::3, 0::3] = np.where((c1 & (E != G)) | (c3 & (E != A)), D, E)
    o[1::3, 1::3] = E
    o[1::3, 2::3] = np.where((c2 & (E != I)) | (c4 & (E != Cc)), F, E)
    o[2::3, 0::3] = np.where(c3, D, E)
    o[2::3, 1::3] = np.where((c3 & (E != I)) | (c4 & (E != G)), Hh, E)
    o[2::3, 2::3] = np.where(c4, F, E)
    return o


def set_text(text: str, big: bool, tracking: int, space: int) -> np.ndarray:
    parts = []
    for i, ch in enumerate(text):
        if ch == ' ':
            parts.append(np.zeros((27 if big else 9, space), bool))
            continue
        g = glyph(ch)
        if big:
            g = scale3x(g)
            g = np.pad(g, ((0, 0), (0, 2)))
            g0 = g.copy()
            g[:, 1:] |= g0[:, :-1]                  # bold verticals: stems 5 px, bars stay 3 px (monumental contrast)
            g[:, 2:] |= g0[:, :-2]
        parts.append(g)
        if i < len(text) - 1 and text[i + 1] != ' ':
            parts.append(np.zeros((g.shape[0], tracking), bool))
    return np.concatenate(parts, axis=1)


def shift(m: np.ndarray, dy: int, dx: int) -> np.ndarray:
    o = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    o[yd, xd] = m[ys, xs]
    return o


def finish(mask: np.ndarray, fill: np.ndarray, shadow: int, pad: int = 4) -> np.ndarray:
    """Outline (1 px) + drop shadow around a lettered mask; returns RGBA."""
    mask = np.pad(mask, pad)
    fill = np.pad(fill, ((pad, pad), (pad, pad), (0, 0)))
    around = np.zeros_like(mask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            around |= shift(mask, dy, dx)
    outline = around & ~mask
    sh = shift(around, shadow, shadow) & ~around if shadow else np.zeros_like(mask)
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[sh] = C('#020507')
    out[outline] = C('#05090F')
    out[mask] = fill[mask]
    return out


def title_logo() -> np.ndarray:
    m = set_text('ASHES OF EMPIRES', True, 4, 14)
    h, w = m.shape
    yy = np.repeat(np.arange(h)[:, None], w, 1).astype(np.float32)
    bthr = pg.bayer(w, h, size=4)
    ramp = arr(['#FBE3AE', '#F0C487', '#DCA16E', '#BA775B', '#9A5A2F', '#7A3E26'])
    tone = (yy / (h - 1)) ** 1.05 * 5.0 + 0.35
    up, dn = shift(m, 1, 0), shift(m, -1, 0)
    lf, rt = shift(m, 0, 1), shift(m, 0, -1)
    top_edge = m & ~up
    tone = np.where(m & ~lf, tone - 0.9, tone)               # lit from the upper left
    tone = np.where(m & ~rt, tone + 0.8, tone)
    tone = np.where(m & ~dn, tone + 1.4, tone)
    tone = np.where(top_edge, tone - 1.6, tone)
    fill = pick(tone, ramp, bthr)
    rng = np.random.default_rng(1964)
    ash = m & (rng.random(m.shape) < 0.035) & (yy > h * 0.45) & ~top_edge
    fill[ash] = C('#4A2A22')
    # snow lying on the letters: every upward-facing surface, with a little drift above
    cov = pg.value_noise(w, 1, 5, 7, octaves=2)[0]
    snow1 = top_edge & (cov[None, :] > 0.28)
    snow2 = shift(snow1, 1, 0) & m & (cov[None, :] > 0.5)
    fill[snow1] = C('#F1F4EC')
    fill[snow2] = C('#C4CFC8')
    cap = shift(snow1, -1, 0) & ~m & (cov[None, :] > 0.62)
    m2 = m | cap
    fill[cap] = C('#DEE5DC')
    return finish(m2, fill, 2)


def diamond(r: int) -> np.ndarray:
    k = np.arange(-r, r + 1)
    return (np.abs(k)[:, None] + np.abs(k)[None, :]) <= r


def title_sub() -> np.ndarray:
    t = set_text('THE LAST WINTER', False, 3, 8)
    h, w = t.shape
    rule, gap, dia = 40, 7, 3
    tot = 2 * (2 * dia + 1 + 2 + rule + gap) + w
    m = np.zeros((h, tot), bool)
    fill = np.zeros((h, tot, 4), np.uint8)
    x = 0
    mid = h // 2
    d = diamond(dia)
    for side in (0, 1):
        if side == 1:
            x0 = 2 * dia + 1 + 2 + rule + gap
            m[:, x0:x0 + w] = t
            yy = np.repeat(np.arange(h)[:, None], w, 1).astype(np.float32)
            tone = yy / (h - 1) * 3.0
            snow = pick(tone, arr(['#F1F4EC', '#DEE5DC', '#C4CFC8', '#A3B1AD']), pg.bayer(w, h, size=4))
            fill[:, x0:x0 + w][t] = snow[t]
            x = x0 + w + gap
        segs = [('rule', rule), ('gap', 2), ('dia', 2 * dia + 1)] if side == 1 else \
            [('dia', 2 * dia + 1), ('gap', 2), ('rule', rule)]
        for kind, n in segs:
            if kind == 'dia':
                y0 = mid - dia
                m[y0:y0 + 2 * dia + 1, x:x + n] |= d
                sub = fill[y0:y0 + 2 * dia + 1, x:x + n]
                sub[d] = C('#DCA16E')
                sub[diamond(1) if False else np.pad(diamond(1), dia - 1)] = C('#F0C487')
            elif kind == 'rule':
                m[mid, x:x + n] = True
                fill[mid, x:x + n] = C('#BA775B')
            x += n
    return finish(m, fill, 1)


# ----------------------------------------------------------------------------- studio emblem
def studio_mark() -> tuple[np.ndarray, np.ndarray]:
    S = 40
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    cx, cy = 19.5, 20.5
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ang = np.degrees(np.arctan2(-(yy - cy), xx - cx)) % 360
    bthr = pg.bayer(S, S, size=4)
    out = np.zeros((S, S, 4), np.uint8)
    rng = np.random.default_rng(42)
    ring = (r >= 15.2) & (r <= 18.2) & ~((ang > 28) & (ang < 62))
    ring &= rng.random((S, S)) > 0.06
    lit = np.cos(np.radians(ang - 135)) * 0.5 + 0.5               # light from the upper left
    tone = (1 - lit) * 2.2 + (r - 15.2) / 3.0 * 0.9
    out[ring] = pick(tone, arr(['#7F8275', '#666A60', '#4F534C', '#3B3F3B']), bthr)[ring]
    for (x, y, col) in [(33, 8, '#4F534C'), (35, 6, '#666A60'), (37, 3, '#4F534C'), (34, 3, '#3B3F3B'),
                        (31, 5, '#3B3F3B')]:
        out[y, x] = C(col)
    # the ember: charred rim, glowing cracks, hot core; a small tongue of flame above it
    e = (((xx - 19.5) / 7.6) ** 2 + ((yy - 24.0) / 4.8) ** 2) <= 1.0
    n = pg.value_noise(S, S, 3, 9, octaves=2)
    core = (((xx - 19.5) / 4.0) ** 2 + ((yy - 23.5) / 2.4) ** 2) <= 1.0
    out[e] = C('#4A2A22')
    inner = e & ~(shift(~e, 1, 0) | shift(~e, -1, 0) | shift(~e, 0, 1) | shift(~e, 0, -1))
    out[inner] = C('#7A3E26')
    crack = inner & (n > 0.56)
    out[crack] = C('#D07744')
    out[core] = C('#F0AE6E')
    out[core & (n > 0.45)] = C('#FBE3AE')
    flame = [(19, 13, '#FBE3AE'), (19, 14, '#F0C487'), (20, 15, '#F0C487'), (19, 15, '#F0C487'),
             (18, 16, '#E5945A'), (19, 16, '#F0C487'), (20, 16, '#E5945A'), (18, 17, '#D07744'),
             (19, 17, '#F0AE6E'), (20, 17, '#E5945A'), (21, 17, '#D07744'), (17, 18, '#BA775B'),
             (18, 18, '#E5945A'), (19, 18, '#F0C487'), (20, 18, '#E5945A'), (21, 18, '#BA775B'),
             (20, 12, '#F0C487'), (20, 11, '#DCA16E')]
    for (x, y, col) in flame:
        out[y, x] = C(col)
    g = np.zeros((S, S, 4), np.uint8)
    d = np.sqrt(((xx - 19.5) / 1.2) ** 2 + (yy - 21.0) ** 2)
    halo = (d > 4) & (d < 13.5) & (bthr < (1 - (d - 4) / 9.5) * 0.55) & (out[..., 3] == 0)
    g[halo & (d < 8)] = C('#9A5A2F')
    g[halo & (d >= 8)] = C('#6E3F22')
    return out, g


# ----------------------------------------------------------------------------- build
def build() -> dict:
    sky = paint_sky()
    smoke = pg.Layer(W, H)
    far_k = pg.Layer(W, H)
    karsk(far_k, smoke)
    # the smoke takes the warm light once it has drifted over the line
    warm_map = {('#0A1219', '#1B1520'), ('#0E1A20', '#211623'), ('#13252B', '#2A2130'), ('#1B3033', '#443B43'),
                ('#26403F', '#57494D')}
    sw = smoke.alpha() & (warmth(XX) > B8)
    warm_map |= {('#05090F', '#120C14')}
    for a, b in warm_map:
        sel = sw & np.all(smoke.c == C(a), axis=-1)
        smoke.c[sel] = C(b)
    pg.atmos(smoke, C('#26403F'), 0.18)
    pg.atmos(far_k, C('#1B3033'), 0.16)
    far_b = pg.Layer(W, H)
    berlin(far_b)
    near = pg.Layer(W, H)
    paint_ground(near)
    tr = pg.Layer(W, H)
    train(tr)
    snow_fence(near)
    telegraph(near)
    signal_mast(near)
    foreground(near)
    scene = pg.Layer(W, H)
    scene.c[:] = sky.c
    for layer in (smoke, far_k, far_b, near, tr):
        scene.blit(layer, 0, 0)
    lamp = paint_lamp()
    logo = title_logo()
    sub = title_sub()
    mark, mglow = studio_mark()
    os.makedirs(OUT, exist_ok=True)
    files = {
        'title_scene.png': Image.fromarray(scene.c, 'RGBA').convert('RGB'),
        'title_lamp.png': Image.fromarray(lamp.c, 'RGBA'),
        'title_logo.png': Image.fromarray(logo, 'RGBA'),
        'title_sub.png': Image.fromarray(sub, 'RGBA'),
        'studio_mark.png': Image.fromarray(mark, 'RGBA'),
        'studio_glow.png': Image.fromarray(mglow, 'RGBA'),
    }
    for name, img in files.items():
        img.save(os.path.join(OUT, name), optimize=False)
        print('wrote assets/ui/splash/%s %dx%d' % (name, img.width, img.height))
    return files


def preview(files: dict, out_dir: str) -> None:
    """Review sheet (NOT in the project): final frame 1x with lamp + logo, the first frame of the tilt, studio card."""
    os.makedirs(out_dir, exist_ok=True)
    scene = files['title_scene.png'].convert('RGBA')
    full = scene.copy()
    full.alpha_composite(files['title_lamp.png'])
    logo, sub = files['title_logo.png'], files['title_sub.png']
    final = full.crop((0, 0, 640, 360))
    final.alpha_composite(logo, ((640 - logo.width) // 2, 26))
    final.alpha_composite(sub, ((640 - sub.width) // 2, 26 + logo.height + 2))
    start = full.crop((0, TILT, 640, TILT + 360))
    sheet = Image.new('RGBA', (1280, 360 + 100), (0, 0, 0, 255))
    sheet.paste(final, (0, 0))
    sheet.paste(start, (640, 0))
    st = Image.new('RGBA', (40, 40), (0, 0, 0, 255))
    st.alpha_composite(files['studio_glow.png'])
    st.alpha_composite(files['studio_mark.png'])
    sheet.paste(st.resize((80, 80), Image.NEAREST), (10, 370))
    sheet.save(os.path.join(out_dir, 'title_splash_sheet.png'))
    final.resize((1920, 1080), Image.NEAREST).crop((300, 40, 1620, 360)).save(os.path.join(out_dir, 'title_logo_x3.png'))
    print('preview', out_dir)


if __name__ == '__main__':
    f = build()
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            preview(f, a.split('=', 1)[1])
