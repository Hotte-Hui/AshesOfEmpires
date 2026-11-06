"""gen_mg_relay -- art for the Chapter-3 mini-game "Das Relaispult" (owner: minigames_r7_relay, §12.8).

    py -3 -P tools/pixelgen/gen_mg_relay.py          (then import under the shared lock)

Writes assets/ui/minigames/relay/ at 1:1 art pixels (the game draws the desk x3, nearest; the DiscoveryView shows
the close-up x3; the world prop lives in the level at world scale):
  relay_desk.png        568x152  the interpreters' relay desk of the Palais: walnut body, the brass-framed floor
                                 display ("Saalanzeige"), four enamel channel tags, the black crossbar field with
                                 4x4 brass sockets, four source plates (Saal + three booth windows) with three
                                 backlog meters (painted green/yellow/red zones; the yellow zone hatched, the red
                                 one striped, so the zones read without colour), the lamp plate with two bezels.
                                 No text is baked in (all text is Loc, drawn by the game on the plates).
  relay_pins.png        3 x 15x17 crossbar pin (ivory knob, brass collar) / selection glow / guide ring (hint)
  relay_lamps.png       6 x 30x30 yellow off/on, red off/on, floor lamp off/on (pressed glass, fresnel rings)
  relay_icons.png       6 x 9x9   ok (check), wrong language (cross), silence (bars), relay (hook), thread lost
                                 (broken line), pause (two bars) -- told apart by shape
  relay_booths.png      5 x 4 cells 20x24: the three booth windows (rows 0-2: Kabine 1/2/3) and the floor
                                 rostrum (row 3) in five states: listening, speaking a/b, struggling, lost
  relay_interpreter.png 2 x 56x56 the interpreter of Kabine 1 (older woman, glasses, grey hair in a bun, headset
                                 round her neck) for the closing beat: calm / a small smile
  relay_layout.json     every rect of the composition (art px) for scripts/ui/minigames/relay_game.gd
  find_relay.png        232x150  close-up for the find (crossbar with the last four pins, the lit yellow lamp, a
                                 headset, a note card with pencilled arrows only, a pencil, a cold coffee)
  world_desk.png        4 x 44x38 the technician's desk in the interpreters' corridor (L_C3_Hall): lamp frames
  world_desk_n.png                (calm / yellow / green channel diodes / both); _n normal map and _e emission
  world_desk_e.png                (lamps and diodes) like the hall props
Deterministic (seeds = crc32 of names). Colours: the "palais" and "veltrava" palettes of data/chapters/c3.json
plus three lamp-glass ramps. No insignia, no flags, no text.
"""
from __future__ import annotations

import json
import math
import os
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'minigames', 'relay')
_C3 = json.load(open(os.path.join(ROOT, 'data', 'chapters', 'c3.json'), encoding='utf-8'))['palettes']
PAL = dict(_C3['palais'])
for _k, _v in _C3['veltrava'].items():
    PAL['v_' + _k] = _v              # every Veltrava ramp as v_<name> (night/red differ from the palais ones)
    PAL.setdefault(_k, _v)           # iron, patina, slate, cream, lamp, sky, snow unprefixed as well
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

# ------------------------------------------------------------------------------------------ geometry (art px)
W, H = 568, 152
FLOOR = (2, 1, 566, 37)                       # x0, y0, x1, y1 of the floor display plate
FLOOR_LAMP = (19, 19)
FLOOR_DIV = 432                               # divider between the text and the right block
ROWS_X = (2, 130)                             # channel tag panel
XB_X0, COL_W, NCOL = 134, 80, 4               # crossbar: column c = [XB_X0 + c*COL_W, +COL_W)
LAMPS_X = (458, 566)
HEAD_Y = (39, 77)                             # source plates
ROW_Y0, ROW_H, NROW = 79, 18, 4               # channel rows
LAMP_C = [(477, 67), (477, 123)]              # yellow, red lamp centres
LAMP_R = 13
WINDOW = (4, 4, 20, 24)                       # booth window inside a source plate (dx, dy, w, h)
METER = (4, 30, 72, 5)                        # meter window inside a booth plate (dx, dy, w, h)
ZONE_YELLOW, ZONE_RED = 0.45, 0.75            # must match relay_logic.gd


def hx(h: str, a: int = 255):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], np.float64)


def C(ramp: str, i: int, a: int = 255):
    r = PAL[ramp]
    return hx(r[max(0, min(len(r) - 1, i))], a)


YEL = [hx('#4a3a17'), hx('#6e5a24'), hx('#b89236'), hx('#f0cd5c'), hx('#fff0a8')]     # lamp glass (dark->lit)
RED = [hx('#3d1410'), hx('#5e1e17'), hx('#b23a2a'), hx('#ec6a4e'), hx('#ffc0a0')]
GRN = [hx('#1d2f27'), hx('#2e4a3a'), hx('#4f7b5c'), hx('#7fb08a'), hx('#c4e6c8')]     # ok / channel lamps
SKIN = [hx('#5a3a2c'), hx('#87604a'), hx('#b48a6c'), hx('#d4ab88'), hx('#e8c6a4')]
IVORY = [hx('#6a6253'), hx('#958a72'), hx('#c3b796'), hx('#e2d8bb'), hx('#f6efda')]


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float64)

    def px(self, x, y, c, alpha=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.blend(x, y, c, alpha)

    def blend(self, x, y, c, alpha=1.0):
        a = (c[3] / 255.0) * alpha
        if a <= 0:
            return
        dst = self.a[y, x]
        if a >= 0.999 or dst[3] == 0:
            self.a[y, x] = [c[0], c[1], c[2], max(dst[3], a * 255) if dst[3] > 0 else a * 255]
            return
        self.a[y, x, :3] = dst[:3] * (1 - a) + np.asarray(c[:3]) * a
        self.a[y, x, 3] = max(dst[3], a * 255)

    def rect(self, x0, y0, x1, y1, c, alpha=1.0):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.blend(x, y, c, alpha)

    def hline(self, x0, x1, y, c, alpha=1.0):
        self.rect(x0, y, x1, y + 1, c, alpha)

    def vline(self, x, y0, y1, c, alpha=1.0):
        self.rect(x, y0, x + 1, y1, c, alpha)

    def line(self, x0, y0, x1, y1, c, alpha=1.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, alpha)

    def disc(self, cx, cy, r, c, alpha=1.0):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.px(x, y, c, alpha)

    def ring(self, cx, cy, r0, r1, c, alpha=1.0):
        for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
            for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r0 <= d <= r1:
                    self.px(x, y, c, alpha)

    def ellipse(self, cx, cy, rx, ry, c, alpha=1.0):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c, alpha)

    def img(self):
        return Image.fromarray(np.clip(np.round(self.a), 0, 255).astype(np.uint8), 'RGBA')


def dither(cv: Cv, x0, y0, x1, y1, cols, f, alpha=1.0, mask=None, soft=1.0):
    """Fill with a ramp: f(x, y) in 0..len(cols)-1, ordered (Bayer) dithering between neighbours. soft < 1 keeps
    flat tone bands and dithers only a band of that width around each step (cleaner faces and small shapes)."""
    for y in range(max(0, int(y0)), min(cv.h, int(y1))):
        for x in range(max(0, int(x0)), min(cv.w, int(x1))):
            if mask is not None and not mask(x, y):
                continue
            v = min(len(cols) - 1.0001, max(0.0, f(x, y)))
            i = int(v)
            fr = v - i
            if soft < 1.0:
                fr = min(1.0, max(0.0, (fr - 0.5) / max(1e-6, soft) + 0.5))
            k = i + 1 if fr > BAYER[y % 4, x % 4] else i
            cv.blend(x, y, cols[min(k, len(cols) - 1)], alpha)


def shade_ellipse(cv: Cv, cx, cy, rx, ry, cols, light=(0.55, -0.45, 0.7), amb=0.25, gain=1.0, clip=None, soft=0.35):
    """A lit ellipsoid (pseudo-normal from the ellipse), dithered onto the ramp `cols`."""
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    def inside(x, y):
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        return u * u + v * v <= 1.0 and (clip is None or clip(x, y))

    def f(x, y):
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        w = math.sqrt(max(0.0, 1.0 - u * u - v * v))
        d = max(0.0, u * lx + v * ly + w * lz)
        return (amb + (1 - amb) * d) * gain * (len(cols) - 1)
    dither(cv, cx - rx - 1, cy - ry - 1, cx + rx + 2, cy + ry + 2, cols, f, 1.0, inside, soft)


def save(cv_or_img, name):
    os.makedirs(OUT, exist_ok=True)
    im = cv_or_img.img() if isinstance(cv_or_img, Cv) else cv_or_img
    im.save(os.path.join(OUT, name), optimize=True)
    print('wrote', name, im.size)


def save_json(name, data):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('wrote', name)


# ------------------------------------------------------------------------------------------ materials
def walnut(cv: Cv, x0, y0, x1, y1, seed, base=2.2):
    r = rng(seed)
    wood = [C('wood', 0), C('wood', 1), C('wood', 2), C('wood', 3), C('wood', 4)]
    ph = r.uniform(0, 6.28, 6)
    fr = r.uniform(0.6, 1.4, 6)

    def f(x, y):
        g = 0.0
        for k in range(3):
            g += 0.35 * math.sin((y + 3.0 * math.sin(x * 0.013 * fr[k] + ph[k])) * (0.55 + 0.25 * k) + ph[k + 3])
        return base + g
    dither(cv, x0, y0, x1, y1, wood, f)
    for _ in range(int((x1 - x0) * (y1 - y0) / 90)):
        x, y = int(r.integers(x0, x1)), int(r.integers(y0, y1))
        ln = int(r.integers(3, 12))
        c = C('wood', 1) if r.random() < 0.6 else C('wood', 3)
        cv.rect(x, y, min(x1, x + ln), y + 1, c, 0.35)


def bevel(cv: Cv, x0, y0, x1, y1, ramp='brass', w=1, hi=4, lo=0):
    """Raised frame: light top/left, dark bottom/right."""
    for i in range(w):
        cv.hline(x0 + i, x1 - i, y0 + i, C(ramp, hi - i))
        cv.vline(x0 + i, y0 + i, y1 - i, C(ramp, hi - 1 - i))
        cv.hline(x0 + i, x1 - i, y1 - 1 - i, C(ramp, lo + i))
        cv.vline(x1 - 1 - i, y0 + i, y1 - i, C(ramp, lo + 1 + i))
    cv.px(x0, y0, C(ramp, hi))
    cv.px(x1 - 1, y1 - 1, C(ramp, lo))


def inset(cv: Cv, x0, y0, x1, y1, ramp='night', dark=0, light=3):
    """Sunken edge: dark top/left, light bottom/right."""
    cv.hline(x0, x1, y0, C(ramp, dark))
    cv.vline(x0, y0, y1, C(ramp, dark))
    cv.hline(x0, x1, y1 - 1, C(ramp, light), 0.7)
    cv.vline(x1 - 1, y0, y1, C(ramp, light), 0.7)


def screw(cv: Cv, x, y):
    cv.disc(x + 0.5, y + 0.5, 1.6, C('brass', 1))
    cv.px(x, y, C('brass', 4))
    cv.px(x - 1, y + 1, C('brass', 3))
    cv.px(x + 1, y - 1, C('brass', 2))
    cv.px(x + 1, y + 1, C('brass', 0))


def enamel(cv: Cv, x0, y0, x1, y1, seed, ramp='night', lo=1.0, hi=2.3):
    r = rng(seed)
    cols = [C(ramp, i) for i in range(len(PAL[ramp]))]

    def f(x, y):
        return lo + (hi - lo) * (1.0 - (y - y0) / max(1, (y1 - y0))) * 0.6 + 0.25 * math.sin(x * 0.07 + y * 0.03)
    dither(cv, x0, y0, x1, y1, cols, f)
    for _ in range(int((x1 - x0) * (y1 - y0) / 140)):
        cv.px(int(r.integers(x0, x1)), int(r.integers(y0, y1)), C(ramp, min(len(cols) - 1, int(hi) + 1)), 0.25)


def socket(cv: Cv, cx, cy):
    cv.ellipse(cx + 0.5, cy + 2.5, 5.0, 2.0, C('night', 0), 0.55)           # recess shadow
    cv.disc(cx + 0.5, cy + 0.5, 4.4, C('brass', 1))
    cv.ring(cx + 0.5, cy + 0.5, 3.0, 4.5, C('brass', 2))
    for (dx, dy, k) in ((-2, -3, 4), (-3, -2, 4), (-1, -3, 3), (-3, -1, 3), (2, 3, 0), (3, 2, 0), (3, 1, 1)):
        cv.px(cx + dx, cy + dy, C('brass', k))
    cv.disc(cx + 0.5, cy + 0.5, 2.1, C('night', 0))
    cv.px(cx + 1, cy + 1, C('night', 2))


# ------------------------------------------------------------------------------------------ the desk
def desk():
    cv = Cv(W, H)
    walnut(cv, 0, 0, W, H, 'relay.desk.walnut', 2.0)
    for y in (37, 38, 77, 78):
        cv.hline(0, W, y, C('wood', 0), 0.6)
    # ---------------- floor display
    x0, y0, x1, y1 = FLOOR
    cv.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, C('wood', 0))
    bevel(cv, x0, y0, x1, y1, 'brass', 2)
    enamel(cv, x0 + 2, y0 + 2, x1 - 2, y1 - 2, 'relay.floor', 'night', 1.0, 2.2)
    inset(cv, x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    for (sx, sy) in ((x0 + 4, y0 + 4), (x1 - 5, y0 + 4), (x0 + 4, y1 - 5), (x1 - 5, y1 - 5)):
        screw(cv, sx, sy)
    lx, ly = FLOOR_LAMP
    cv.disc(lx + 0.5, ly + 0.5, 10.0, C('brass', 0))
    cv.ring(lx + 0.5, ly + 0.5, 7.4, 10.0, C('brass', 2))
    cv.ring(lx + 0.5, ly + 0.5, 9.0, 10.0, C('brass', 3), 0.8)
    for (dx, dy) in ((-6, -7), (-7, -6), (-5, -8)):
        cv.px(lx + dx, ly + dy, C('brass', 4))
    cv.disc(lx + 0.5, ly + 0.5, 7.0, C('night', 0))
    cv.vline(FLOOR_DIV, y0 + 4, y1 - 4, C('brass', 1))
    cv.vline(FLOOR_DIV + 1, y0 + 4, y1 - 4, C('brass', 3), 0.6)
    cv.rect(440, 29, 560, 33, C('night', 0))                       # progress groove
    inset(cv, 440, 29, 560, 33, 'night', 0, 3)
    # ---------------- channel tags
    rx0, rx1 = ROWS_X
    cv.rect(rx0, HEAD_Y[0], rx1, H - 1, C('wood', 1))
    inset(cv, rx0, HEAD_Y[0], rx1, H - 1, 'wood', 0, 3)
    bevel(cv, rx0 + 3, HEAD_Y[0] + 3, rx1 - 3, HEAD_Y[1] - 2, 'brass', 1)
    enamel(cv, rx0 + 4, HEAD_Y[0] + 4, rx1 - 4, HEAD_Y[1] - 3, 'relay.kanal', 'wood', 0.6, 1.8)
    screw(cv, rx1 - 8, HEAD_Y[0] + 7)
    for r_ in range(NROW):
        ty0 = ROW_Y0 + r_ * ROW_H + 1
        ty1 = ty0 + ROW_H - 2
        cv.rect(rx0 + 3, ty0, rx1 - 3, ty1 + 1, C('night', 0), 0.8)
        bevel(cv, rx0 + 4, ty0, rx1 - 4, ty1, 'marble', 1, 5, 1)
        paper = [C('paper', 2), C('paper', 3), C('paper', 4)]
        dither(cv, rx0 + 5, ty0 + 1, rx1 - 5, ty1 - 1, paper,
               lambda x, y, a=ty0: 1.75 - (y - a) * 0.075 + 0.12 * math.sin(x * 0.2))
        # code chip (dark enamel) at the left of the tag
        cv.rect(rx0 + 6, ty0 + 2, rx0 + 27, ty1 - 2, C('v_slate', 1))
        cv.hline(rx0 + 6, rx0 + 27, ty0 + 2, C('v_slate', 3))
        cv.hline(rx0 + 6, rx0 + 27, ty1 - 3, C('v_slate', 0))
        cv.vline(rx0 + 26, ty0 + 2, ty1 - 2, C('v_slate', 0))
        screw(cv, rx1 - 8, ty0 + 3)
        screw(cv, rx1 - 8, ty1 - 4)
        rr = rng('relay.tag%d' % r_)
        for _ in range(12):
            cv.px(int(rr.integers(rx0 + 29, rx1 - 10)), int(rr.integers(ty0 + 1, ty1 - 1)), C('paper', 1), 0.45)
    # ---------------- crossbar: source plates
    for c in range(NCOL):
        cx0 = XB_X0 + c * COL_W
        px0, py0, px1, py1 = cx0 + 1, HEAD_Y[0], cx0 + COL_W - 1, HEAD_Y[1]
        cv.rect(px0 - 1, py0 - 1, px1 + 1, py1 + 1, C('wood', 0))
        bevel(cv, px0, py0, px1, py1, 'brass', 1)
        enamel(cv, px0 + 1, py0 + 1, px1 - 1, py1 - 1, 'relay.plate%d' % c, 'night', 1.2, 2.6)
        wx, wy, ww, wh = WINDOW
        fx0, fy0 = px0 + wx - 1, py0 + wy - 1
        cv.rect(fx0, fy0, fx0 + ww + 2, fy0 + wh + 2, C('wood', 0))
        bevel(cv, fx0, fy0, fx0 + ww + 2, fy0 + wh + 2, 'wood', 1, 4, 0)
        cv.rect(fx0 + 1, fy0 + 1, fx0 + ww + 1, fy0 + wh + 1, C('night', 0))
        if c > 0:
            mx, my, mw, mh = METER
            ax0, ay0 = px0 + mx, py0 + my
            cv.rect(ax0 - 1, ay0 - 1, ax0 + mw + 1, ay0 + mh + 1, C('night', 0))
            bevel(cv, ax0 - 1, ay0 - 1, ax0 + mw + 1, ay0 + mh + 1, 'brass', 1)
            for x in range(mw):
                v = x / float(mw - 1)
                for y in range(mh):
                    if v < ZONE_YELLOW:
                        col = GRN[2] if y else GRN[3]
                    elif v < ZONE_RED:
                        col = YEL[2] if ((x + y) % 3) else YEL[1]          # diagonal hatch: yellow zone
                    else:
                        col = RED[2] if (x % 2) else RED[1]                  # vertical stripes: red zone
                    cv.px(ax0 + x, ay0 + y, col)
            for k in range(0, 11):
                tx = ax0 + int(round(k / 10.0 * (mw - 1)))
                cv.px(tx, ay0, C('paper', 4), 0.8 if k % 5 == 0 else 0.45)
            for v in (ZONE_YELLOW, ZONE_RED):
                tx = ax0 + int(round(v * (mw - 1)))
                cv.vline(tx, ay0, ay0 + mh, C('paper', 5), 0.9)
        screw(cv, px1 - 4, py0 + 3)
    # ---------------- crossbar: socket field
    fx0, fy0, fx1, fy1 = XB_X0, ROW_Y0, XB_X0 + NCOL * COL_W, H - 1
    cv.rect(fx0, fy0, fx1, fy1, C('night', 1))
    bak = [C('night', 0), C('night', 1), C('night', 2), C('wall', 0)]
    dither(cv, fx0 + 1, fy0 + 1, fx1 - 1, fy1 - 1, bak, lambda x, y: 1.3 + 0.5 * math.sin(x * 0.035 + y * 0.02)
           - (y - fy0) * 0.006)
    inset(cv, fx0, fy0, fx1, fy1, 'night', 0, 3)
    for r_ in range(1, NROW):                               # engraved row rules
        y = ROW_Y0 + r_ * ROW_H
        cv.hline(fx0 + 3, fx1 - 3, y, C('night', 0))
        cv.hline(fx0 + 3, fx1 - 3, y + 1, C('wall', 1), 0.5)
    for c in range(1, NCOL):                                # engraved column rules
        x = XB_X0 + c * COL_W
        cv.vline(x, fy0 + 3, fy1 - 3, C('night', 0))
        cv.vline(x + 1, fy0 + 3, fy1 - 3, C('wall', 1), 0.4)
    for r_ in range(NROW):
        for c in range(NCOL):
            socket(cv, XB_X0 + c * COL_W + COL_W // 2, ROW_Y0 + r_ * ROW_H + ROW_H // 2)
    # ---------------- lamp plate
    lx0, lx1 = LAMPS_X
    cv.rect(lx0, HEAD_Y[0], lx1, H - 1, C('wood', 0))
    steel = [C('iron', 1), C('iron', 2), C('iron', 3), C('iron', 4)]
    dither(cv, lx0 + 1, HEAD_Y[0] + 1, lx1 - 1, H - 2, steel,
           lambda x, y: 1.25 + 0.3 * math.sin(y * 1.7 + x * 0.04) + 0.25 * math.sin(x * 0.09))
    bevel(cv, lx0, HEAD_Y[0], lx1, H - 1, 'iron', 1, 4, 0)
    for (sx, sy) in ((lx0 + 3, HEAD_Y[0] + 3), (lx1 - 4, HEAD_Y[0] + 3), (lx0 + 3, H - 5), (lx1 - 4, H - 5)):
        screw(cv, sx, sy)
    mid = (LAMP_C[0][1] + LAMP_C[1][1]) // 2
    cv.hline(lx0 + 6, lx1 - 6, mid, C('iron', 0))
    cv.hline(lx0 + 6, lx1 - 6, mid + 1, C('iron', 4), 0.6)
    for (cx, cy) in LAMP_C:
        cv.disc(cx + 0.5, cy + 0.5, LAMP_R + 2.4, C('iron', 0))
        cv.ring(cx + 0.5, cy + 0.5, LAMP_R + 0.2, LAMP_R + 2.4, C('iron', 4))
        cv.ring(cx + 0.5, cy + 0.5, LAMP_R + 1.4, LAMP_R + 2.4, C('marble', 5), 0.45)
        cv.disc(cx + 0.5, cy + 0.5, LAMP_R, C('night', 0))
    save(cv, 'relay_desk.png')


# ------------------------------------------------------------------------------------------ small sprites
PIN_CELL = (15, 17)
PIN_ORIGIN = (7, 11)       # socket centre inside the pin cell


def pins():
    cw, ch = PIN_CELL
    ox0, oy0 = PIN_ORIGIN
    cv = Cv(cw * 3, ch)
    # 0: pin seated -- ivory knob seen from the front-top, brass collar in the socket, short shadow
    cx, cy = ox0, oy0
    cv.ellipse(cx + 1.5, cy + 3.0, 5.6, 1.8, C('night', 0), 0.7)           # shadow on the panel
    cv.disc(cx + 0.5, cy + 0.5, 4.0, C('brass', 2))                       # collar
    cv.ring(cx + 0.5, cy + 0.5, 2.8, 4.1, C('brass', 3))
    cv.px(cx - 3, cy - 1, C('brass', 4))
    cv.px(cx + 3, cy + 2, C('brass', 0))
    shade_ellipse(cv, cx + 0.5, cy - 6.0, 4.2, 5.0, IVORY, (-0.6, -0.5, 0.7), 0.3)   # knob
    cv.rect(cx - 2, cy - 2, cx + 3, cy + 1, IVORY[1])                       # neck into the collar
    cv.vline(cx - 2, cy - 2, cy + 1, IVORY[2])
    cv.vline(cx + 2, cy - 2, cy + 1, IVORY[0])
    cv.px(cx - 2, cy - 9, IVORY[4])
    cv.px(cx - 1, cy - 10, IVORY[4])
    # dark outline round the knob for contrast on the black field
    m = cv.a[:, :cw, 3] > 0
    o = np.zeros_like(m)
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    o &= ~m
    sub = cv.a[:, :cw]
    sub[o] = C('night', 0)
    # 1: selection glow (drawn behind/around the pin of the selected row)
    ox = cw
    cv.ring(ox + ox0 + 0.5, oy0 - 2.5, 6.0, 7.4, C('amber', 3), 0.8)
    cv.ring(ox + ox0 + 0.5, oy0 - 2.5, 7.4, 8.2, C('amber', 4), 0.35)
    # 2: guide ring (hint: the socket this row needs) -- dotted, shape-coded, not colour-only
    ox = cw * 2
    for k in range(16):
        a = k / 16.0 * math.tau
        if k % 2 == 0:
            cv.px(ox + ox0 + round(6.2 * math.cos(a)), oy0 + round(6.2 * math.sin(a)), GRN[4])
            cv.px(ox + ox0 + round(5.3 * math.cos(a)), oy0 + round(5.3 * math.sin(a)), GRN[3], 0.8)
    save(cv, 'relay_pins.png')


def _lamp(cv: Cv, ox, oy, glass, lit: bool, r=12.0):
    cx, cy = ox + 15.0, oy + 15.0
    if lit:
        for k in range(6):                                   # halo
            cv.ring(cx, cy, r + k * 0.5, r + k * 0.5 + 0.6, glass[4], 0.24 - k * 0.035)
    cols = [glass[0], glass[1], glass[2]] if not lit else [glass[2], glass[3], glass[4]]

    def f(x, y):
        d = math.hypot(x + 0.5 - cx + 2.5, y + 0.5 - cy + 2.5) / r
        rings = 0.18 * math.cos(math.hypot(x + 0.5 - cx, y + 0.5 - cy) * 1.9)   # fresnel rings
        return (2.05 - d * 1.5 + rings) if lit else (1.7 - d * 1.4 + rings)
    dither(cv, cx - r - 1, cy - r - 1, cx + r + 2, cy + r + 2, cols, f, 1.0,
           lambda x, y: math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r)
    cv.ring(cx, cy, r - 1.1, r, glass[0], 0.85)
    for (dx, dy, a) in ((-5, -6, 0.95), (-4, -7, 0.75), (-6, -5, 0.6), (-3, -7, 0.4)):
        cv.px(cx + dx, cy + dy, C('marble', 5), a if lit else a * 0.5)


def lamps():
    cs = 30
    cv = Cv(cs * 6, cs)
    _lamp(cv, 0, 0, YEL, False)
    _lamp(cv, cs, 0, YEL, True)
    _lamp(cv, cs * 2, 0, RED, False)
    _lamp(cv, cs * 3, 0, RED, True)
    amber = [hx('#3a2412'), C('amber', 0), C('amber', 2), C('amber', 3), C('amber', 4)]
    _lamp(cv, cs * 4, 0, amber, False, 6.6)
    _lamp(cv, cs * 5, 0, amber, True, 6.6)
    save(cv, 'relay_lamps.png')


def icons():
    s = 9
    cv = Cv(s * 6, s)
    # 0 ok: a check mark (light green with a dark shadow)
    pts = [(1, 4), (2, 5), (3, 6), (4, 5), (5, 4), (6, 3), (7, 2)]
    for (x, y) in pts:
        cv.px(x, y + 1, C('night', 0))
    for (x, y) in pts:
        cv.px(x, y, GRN[4])
        cv.px(x, y - 1 if x > 3 else y, GRN[3])
    # 1 wrong: a cross (red)
    ox = s
    for i in range(1, 8):
        cv.px(ox + i, min(8, i + 1), C('night', 0), 0.8)
        cv.px(ox + i, i, RED[3])
        cv.px(ox + 8 - i, i, RED[3])
    cv.px(ox + 4, 4, RED[4])
    # 2 silence: a dash between two short bars (a headset without sound)
    ox = s * 2
    cv.rect(ox + 1, 4, ox + 8, 5, C('v_slate', 5))
    cv.rect(ox + 1, 2, ox + 2, 7, C('v_slate', 4))
    cv.rect(ox + 7, 2, ox + 8, 7, C('v_slate', 4))
    # 3 relay: a hooked arrow (brass)
    ox = s * 3
    for (x, y) in [(1, 6), (1, 5), (1, 4), (2, 3), (3, 2), (4, 2), (5, 2), (6, 3)]:
        cv.px(ox + x, y, C('brass', 4))
    for (x, y) in [(7, 4), (6, 4), (5, 4), (7, 3), (7, 5)]:
        cv.px(ox + x, y, C('brass', 3))
    # 4 thread lost: a broken zigzag (red)
    ox = s * 4
    for (x, y) in [(0, 4), (1, 3), (2, 4), (3, 5)]:
        cv.px(ox + x, y, RED[3])
    for (x, y) in [(5, 3), (6, 4), (7, 3), (8, 4)]:
        cv.px(ox + x, y, RED[3])
    cv.px(ox + 4, 7, RED[2])
    # 5 pause: two bars (amber)
    ox = s * 5
    cv.rect(ox + 2, 1, ox + 4, 8, C('amber', 3))
    cv.rect(ox + 5, 1, ox + 7, 8, C('amber', 3))
    save(cv, 'relay_icons.png')


# ------------------------------------------------------------------------------------------ booth windows
INTERPRETERS = [
    {'hair': hx('#8d8a84'), 'hair_hi': hx('#c2bdb2'), 'coat': C('v_slate', 2), 'coat_hi': C('v_slate', 3),
     'glasses': True, 'bun': True, 'skin': 2},                                     # Kabine 1: older woman
    {'hair': hx('#2b2420'), 'hair_hi': hx('#4a3c33'), 'coat': C('wood', 2), 'coat_hi': C('wood', 3),
     'glasses': True, 'bun': False, 'skin': 2},                                    # Kabine 2: a man (glasses)
    {'hair': hx('#5a3a24'), 'hair_hi': hx('#7e553b'), 'coat': C('patina', 1), 'coat_hi': C('patina', 2),
     'glasses': False, 'bun': False, 'skin': 3, 'bob': True},                      # Kabine 3: young woman
]


def _booth_cell(cv: Cv, ox, oy, who: int, state: int):
    w, h = 20, 24
    inner = [C('night', 0), C('night', 1), C('wood', 0), C('wood', 1)]
    lampk = 0.0 if state == 4 else 1.0
    dither(cv, ox, oy, ox + w, oy + h, inner,
           lambda x, y: 0.6 + 1.6 * lampk * math.exp(-(((x - ox - 16) / 8.0) ** 2 + ((y - oy - 13) / 9.0) ** 2)))
    for y in range(oy + 2, oy + 12, 3):
        cv.hline(ox + 1, ox + w - 1, y, C('night', 0), 0.6)
    if who < 3:
        p = INTERPRETERS[who]
        sk = SKIN[p['skin']]
        sk_d = SKIN[p['skin'] - 1]
        hx0 = ox + 7                    # head left edge (profile looks right, towards the Saal window)
        dy = 1 if state == 3 else (2 if state == 4 else 0)
        tilt = 1 if state == 4 else 0
        # shoulders / jacket
        cv.rect(ox + 2, oy + 18 + dy // 2, ox + 15, oy + 24, p['coat'])
        cv.rect(ox + 3, oy + 17 + dy // 2, ox + 14, oy + 18 + dy // 2, p['coat'])
        cv.vline(ox + 3, oy + 18, oy + 24, p['coat_hi'])
        cv.rect(ox + 8, oy + 17 + dy // 2, ox + 12, oy + 20, C('paper', 3) if who != 1 else C('paper', 4))   # collar
        # neck + head (6 wide, 8 tall)
        cv.rect(hx0 + 2, oy + 14 + dy, hx0 + 4, oy + 17 + dy, sk_d)
        cv.rect(hx0, oy + 6 + dy, hx0 + 6, oy + 14 + dy, sk)
        cv.rect(hx0 + 1, oy + 5 + dy, hx0 + 5, oy + 6 + dy, sk)
        cv.px(hx0 + 6, oy + 10 + dy + tilt, sk)                          # nose
        cv.vline(hx0, oy + 7 + dy, oy + 13 + dy, sk_d)                    # back of the head in shadow
        # hair
        cv.rect(hx0, oy + 4 + dy, hx0 + 6, oy + 7 + dy, p['hair'])
        cv.rect(hx0 - 1, oy + 5 + dy, hx0 + 2, oy + 11 + dy, p['hair'])
        cv.hline(hx0 + 1, hx0 + 5, oy + 4 + dy, p['hair_hi'])
        if p.get('bun'):
            cv.disc(hx0 - 1.0, oy + 7.5 + dy, 2.1, p['hair'])
            cv.px(hx0 - 2, oy + 6 + dy, p['hair_hi'])
        if p.get('bob'):
            cv.rect(hx0 - 1, oy + 5 + dy, hx0 + 1, oy + 14 + dy, p['hair'])
            cv.px(hx0 + 5, oy + 7 + dy, p['hair'])
        # eye, glasses, mouth
        eye_y = oy + 9 + dy + tilt
        cv.px(hx0 + 4, eye_y, C('night', 0))
        if p.get('glasses'):
            cv.px(hx0 + 3, eye_y, C('brass', 3))
            cv.px(hx0 + 5, eye_y, C('brass', 3))
            cv.px(hx0 + 4, eye_y - 1, C('brass', 2), 0.7)
        mouth = C('night', 1) if state in (1, 2) else sk_d
        cv.px(hx0 + 5, oy + 12 + dy + tilt, mouth)
        if state == 2:
            cv.px(hx0 + 5, oy + 13 + dy, C('night', 1))
        # headset: band over the crown, ear cup over the ear (middle of the head, behind the cheek)
        cv.hline(hx0 + 1, hx0 + 5, oy + 3 + dy, C('iron', 1))
        cv.vline(hx0 + 2, oy + 3 + dy, oy + 8 + dy, C('iron', 1))
        cv.rect(hx0 + 1, oy + 8 + dy, hx0 + 3, oy + 11 + dy, C('iron', 0))
        cv.px(hx0 + 1, oy + 8 + dy, C('iron', 3))
        # gooseneck microphone in front of the mouth
        mx = ox + 16
        cv.line(mx + 2, oy + 23, mx, oy + 15, C('iron', 3))
        cv.rect(mx - 1, oy + 12 + (1 if state == 4 else 0), mx + 2, oy + 15, C('iron', 2))
        cv.px(mx - 1, oy + 12, C('iron', 4))
        if state in (1, 2):                             # the "on air" diode on the microphone
            cv.px(mx + 1, oy + 15, RED[4])
        if state == 3:                                  # struggling: hand to the temple
            cv.rect(hx0 - 1, oy + 7 + dy, hx0 + 2, oy + 10 + dy, sk)
            cv.line(ox + 4, oy + 18, hx0, oy + 10 + dy, p['coat'])
        elif state == 0:                                # listening: pencil ready
            cv.line(ox + 10, oy + 22, ox + 14, oy + 19, C('brass', 3))
        cv.rect(ox + 15, oy + 18, ox + 20, oy + 20, C('patina', 2))   # desk lamp shade
        cv.px(ox + 16, oy + 20, C('amber', 4) if state != 4 else C('amber', 1))
    else:
        # the floor: a rostrum microphone with a speaking light, the Saal beyond in deep shadow
        cv.rect(ox, oy + 15, ox + w, oy + h, C('wood', 1))
        cv.hline(ox, ox + w, oy + 15, C('wood', 3))
        cv.rect(ox + 3, oy + 16, ox + 17, oy + 18, C('wood', 2))
        cv.line(ox + 10, oy + 15, ox + 10, oy + 8, C('iron', 3))
        cv.ellipse(ox + 10.5, oy + 6.5, 2.6, 3.2, C('iron', 2))
        cv.px(ox + 9, oy + 5, C('iron', 4))
        if state in (1, 2):
            cv.disc(ox + 10.5, oy + 13.5, 1.2, RED[4])
            for k in range(3):
                cv.px(ox + 14 + k, oy + 4 + k * 2 + (state - 1), C('amber', 4), 0.6)
                cv.px(ox + 6 - k, oy + 4 + k * 2 + (state - 1), C('amber', 4), 0.6)
        else:
            cv.disc(ox + 10.5, oy + 13.5, 1.2, RED[1])
    for k in range(5):                                  # glass reflection
        cv.px(ox + 2 + k, oy + 1 + k, C('daylight', 5), 0.18)
        cv.px(ox + 3 + k, oy + 1 + k, C('daylight', 5), 0.10)


def booths():
    w, h = 20, 24
    cv = Cv(w * 5, h * 4)
    for who in range(4):
        for st in range(5):
            _booth_cell(cv, st * w, who * h, who, st)
    save(cv, 'relay_booths.png')


# ------------------------------------------------------------------------------------------ the interpreter
def interpreter():
    s = 56
    cv = Cv(s * 2, s)
    p = INTERPRETERS[0]
    skin = [SKIN[0], SKIN[1], SKIN[2], SKIN[3], SKIN[4]]
    hair = [hx('#55524c'), hx('#7a766e'), p['hair'], hx('#aaa59b'), p['hair_hi'], hx('#dcd7cc')]
    cardigan = [C('v_slate', 0), C('v_slate', 1), C('v_slate', 2), C('v_slate', 3), C('v_slate', 4)]
    for f in range(2):
        ox = f * s
        bg = [C('night', 1), C('night', 2), C('wood', 0), C('wood', 1), C('wood', 2)]
        dither(cv, ox, 0, ox + s, s, bg,
               lambda x, y, o=ox: 0.7 + 2.6 * math.exp(-(((x - o - 44) / 20.0) ** 2 + ((y - 16) / 22.0) ** 2)))
        cv.rect(ox + 2, 0, ox + 6, s, C('wood', 1))                    # booth door frame
        cv.vline(ox + 5, 0, s, C('wood', 3))
        cv.vline(ox + 2, 0, s, C('wood', 0))
        cx = ox + 27
        # shoulders: cardigan over a white blouse
        shade_ellipse(cv, cx + 1, 53, 21, 14, cardigan, (0.7, -0.5, 0.5), 0.3, 1.0, lambda x, y: y < s)
        cv.rect(cx - 5, 41, cx + 6, s, C('paper', 4))
        cv.line(cx - 5, 41, cx - 9, s - 1, cardigan[1])
        cv.line(cx - 4, 41, cx - 8, s - 1, cardigan[3])
        cv.line(cx + 6, 41, cx + 9, s - 1, cardigan[1])
        cv.px(cx, 47, C('brass', 3))
        cv.px(cx, 52, C('brass', 3))
        cv.hline(cx - 3, cx + 4, 41, C('paper', 2))                     # collar edge
        # neck
        shade_ellipse(cv, cx + 1, 38, 5, 6, skin, (0.7, -0.3, 0.6), 0.25, 0.85)
        # head: a lit ellipsoid, turned a little to the right
        shade_ellipse(cv, cx + 1, 25, 9.5, 11.5, skin, (0.75, -0.35, 0.6), 0.28, 1.0)
        # hair: swept back, grey; the bun at the back of the head
        shade_ellipse(cv, cx - 1, 17, 10.5, 7.0, hair, (0.6, -0.7, 0.4), 0.3, 1.0, lambda x, y: y <= 20)
        shade_ellipse(cv, cx - 9, 23, 3.4, 8.5, hair, (0.4, -0.5, 0.6), 0.25, 0.9)
        shade_ellipse(cv, cx - 12, 15, 5.2, 4.8, hair, (0.5, -0.6, 0.6), 0.25, 1.0)    # bun
        for k in range(7):                                                # combed strands
            cv.line(cx - 8 + k * 2, 13 + (k % 2), cx + 3 + k, 20, hair[4 if k % 2 else 3], 0.5)
        cv.px(cx - 13, 13, hair[5])
        cv.px(cx - 11, 12, hair[5])
        # ear and a small pearl earring (left, half hidden)
        cv.rect(cx - 8, 25, cx - 6, 29, skin[1])
        cv.px(cx - 7, 30, hx('#efe9dc'))
        # brows, eyes behind round glasses
        cv.hline(cx - 3, cx + 1, 21, hair[2])
        cv.hline(cx + 4, cx + 8, 21, hair[2])
        cv.px(cx - 1, 24, C('night', 0))
        cv.px(cx + 6, 24, C('night', 0))
        cv.px(cx - 2, 24, hx('#e9e2d3'), 0.6)
        cv.px(cx + 5, 24, hx('#e9e2d3'), 0.6)
        for gx in (cx - 1, cx + 6):
            cv.ring(gx + 0.5, 24.5, 2.3, 3.2, C('brass', 2))
            cv.px(gx + 1, 23, C('marble', 5), 0.55)
        cv.hline(cx + 2, cx + 4, 24, C('brass', 2))
        cv.line(cx - 4, 24, cx - 7, 25, C('brass', 1))                    # temple arm
        # nose (light from the right: shadow on the left of the bridge), mouth, lines of a long working life
        cv.line(cx + 3, 25, cx + 2, 29, skin[2])
        cv.px(cx + 3, 30, skin[1])
        cv.px(cx + 4, 30, skin[2])
        lip = hx('#8a4a3c')
        if f == 0:
            cv.hline(cx + 1, cx + 6, 33, lip)
        else:
            cv.hline(cx + 1, cx + 6, 33, lip)
            cv.px(cx, 32, lip)
            cv.px(cx + 6, 32, lip)
            cv.px(cx - 2, 29, skin[1])                                    # smile lines
            cv.px(cx + 8, 29, skin[2])
        cv.px(cx - 4, 23, skin[1])
        cv.px(cx + 10, 23, skin[2])
        cv.px(cx - 4, 26, skin[1], 0.6)
        # headset round the neck: band across the collar, the two bakelite cups resting on it
        cv.line(cx - 9, 39, cx + 11, 39, C('iron', 1))
        for (ex, ey) in ((cx - 10, 41), (cx + 12, 41)):
            cv.ellipse(ex + 0.5, ey + 0.5, 3.6, 3.2, C('iron', 0))
            cv.ring(ex + 0.5, ey + 0.5, 2.0, 3.6, C('iron', 2), 0.6)
            cv.px(ex - 1, ey - 1, C('iron', 4))
        cv.line(cx + 14, 43, cx + 18, s - 1, C('iron', 1))               # the cable
        # warm rim light from the corridor sconce (right)
        for y in range(14, 36):
            cv.px(cx + 10 + (1 if 18 < y < 32 else 0), y, C('amber', 4), 0.3)
    save(cv, 'relay_interpreter.png')


# ------------------------------------------------------------------------------------------ the find close-up
def find_closeup():
    w, h = 232, 150
    cv = Cv(w, h)
    walnut(cv, 0, 0, w, h, 'relay.find.walnut', 2.3)
    px0, py0, px1, py1 = 14, 16, 150, 118
    cv.rect(px0 - 2, py0 - 2, px1 + 2, py1 + 2, C('wood', 0))
    bevel(cv, px0 - 2, py0 - 2, px1 + 2, py1 + 2, 'brass', 2)
    bak = [C('night', 0), C('night', 1), C('night', 2), C('wall', 0)]
    dither(cv, px0, py0, px1, py1, bak, lambda x, y: 1.0 + 0.8 * (1 - (y - py0) / (py1 - py0)) + 0.3 * math.sin(x * 0.05))
    for r_ in range(4):
        for c in range(4):
            cx = px0 + 18 + c * 33
            cy = py0 + 14 + r_ * 24
            cv.ellipse(cx + 0.5, cy + 3.5, 7.0, 2.6, C('night', 0), 0.5)
            cv.disc(cx + 0.5, cy + 0.5, 6.4, C('brass', 1))
            cv.ring(cx + 0.5, cy + 0.5, 4.6, 6.5, C('brass', 2))
            cv.ring(cx + 0.5, cy + 0.5, 5.6, 6.5, C('brass', 3), 0.6)
            cv.disc(cx + 0.5, cy + 0.5, 3.2, C('night', 0))
    # four pins (one per row) -- the last setting of the session: DE<-K1, RU<-K2, FR<-Saal, EN<-K3
    for r_, c in enumerate((1, 2, 0, 3)):
        cx = px0 + 18 + c * 33
        cy = py0 + 14 + r_ * 24
        cv.ellipse(cx + 2.5, cy + 4.5, 8.0, 2.6, C('night', 0), 0.75)
        cv.disc(cx + 0.5, cy + 0.5, 5.6, C('brass', 3))
        cv.ring(cx + 0.5, cy + 0.5, 4.2, 5.7, C('brass', 4), 0.8)
        shade_ellipse(cv, cx + 0.5, cy - 8.0, 6.0, 7.0, IVORY, (-0.6, -0.5, 0.7), 0.3)
        cv.rect(cx - 3, cy - 3, cx + 4, cy + 1, IVORY[1])
        cv.vline(cx - 3, cy - 3, cy + 1, IVORY[2])
        cv.px(cx - 3, cy - 12, IVORY[4])
        cv.px(cx - 2, cy - 13, IVORY[4])
    for (cx, cy, glass, lit) in ((180, 36, YEL, True), (180, 78, RED, False)):
        cv.disc(cx + 0.5, cy + 0.5, 16.0, C('iron', 0))
        cv.ring(cx + 0.5, cy + 0.5, 13.5, 16.0, C('iron', 4))
        tmp = Cv(30, 30)
        _lamp(tmp, 0, 0, glass, lit)
        a = tmp.a
        for y in range(30):
            for x in range(30):
                if a[y, x, 3] > 0:
                    cv.blend(cx - 15 + x, cy - 15 + y, a[y, x], 1.0)
    # headset lying on the desk (bottom right): band + two cups + cable
    for k in range(40):
        t = k / 39.0
        x = 160 + 54 * t
        y = 128 - 18 * math.sin(t * math.pi)
        cv.px(x, y, C('iron', 2))
        cv.px(x, y + 1, C('iron', 0))
    for (cx, cy) in ((160, 128), (214, 128)):
        cv.ellipse(cx + 0.5, cy + 0.5, 7.0, 6.0, C('iron', 0))
        cv.ellipse(cx - 0.5, cy - 0.5, 5.0, 4.0, C('iron', 1))
        cv.ring(cx - 0.5, cy - 0.5, 3.6, 5.0, C('iron', 2), 0.7)
        cv.px(cx - 2, cy - 3, C('iron', 4))
    for k in range(60):
        t = k / 59.0
        cv.px(214 + 8 * t + 3 * math.sin(t * 9), 134 + 14 * t, C('iron', 1))
    # the technician's note card (pencil arrows only) and a pencil
    nx0, ny0 = 22, 124
    cv.rect(nx0 + 1, ny0 + 1, nx0 + 59, ny0 + 23, C('night', 0), 0.4)
    cv.rect(nx0, ny0, nx0 + 58, ny0 + 22, C('paper', 4))
    cv.rect(nx0, ny0, nx0 + 58, ny0 + 1, C('paper', 5))
    cv.vline(nx0 + 57, ny0, ny0 + 22, C('paper', 2))
    for (ax, ay) in ((nx0 + 6, ny0 + 6), (nx0 + 6, ny0 + 14)):
        cv.hline(ax, ax + 18, ay, C('ink', 1), 0.8)
        cv.px(ax + 17, ay - 1, C('ink', 1), 0.8)
        cv.px(ax + 17, ay + 1, C('ink', 1), 0.8)
        cv.hline(ax + 26, ax + 44, ay, C('ink', 1), 0.6)
    cv.line(nx0 + 64, ny0 + 2, nx0 + 104, ny0 + 16, C('amber', 3))
    cv.line(nx0 + 64, ny0 + 3, nx0 + 104, ny0 + 17, C('amber', 1))
    cv.px(nx0 + 105, ny0 + 17, C('night', 0))
    # a coffee cup in the corner, gone cold
    cv.ellipse(214.5, 104.5, 10.0, 4.0, C('marble', 3))
    cv.rect(205, 96, 225, 105, C('marble', 4))
    cv.vline(205, 96, 105, C('marble', 5))
    cv.vline(224, 96, 105, C('marble', 2))
    cv.ellipse(215.5, 96.5, 10.0, 3.0, C('marble', 5))
    cv.ellipse(215.5, 96.5, 8.0, 2.0, hx('#3a2418'))
    cv.ring(227.5, 100.5, 2.0, 3.2, C('marble', 4))
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - 200) / 140.0, (y - 10) / 120.0)
            g = max(0.0, 0.22 - 0.2 * d)
            if g > 0.01:
                cv.blend(x, y, C('amber', 4), g)
            v = math.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
            if v > 0.75:
                cv.blend(x, y, C('night', 0), min(0.55, (v - 0.75) * 1.2))
    save(cv, 'find_relay.png')


# ------------------------------------------------------------------------------------------ the world prop
WD_W, WD_H = 44, 38


def _world_desk(frame: int) -> Cv:
    cv = Cv(WD_W, WD_H)
    for lx in (3, 38):                                   # legs + stretcher (feet on the bottom row)
        cv.rect(lx, 22, lx + 3, WD_H, C('wood', 1))
        cv.vline(lx, 22, WD_H, C('wood', 3))
    cv.rect(5, 31, 39, 33, C('wood', 0))
    cv.rect(1, 19, 43, 23, C('wood', 2))                 # table top + apron
    cv.hline(1, 43, 19, C('wood', 4))
    cv.hline(1, 43, 22, C('wood', 0))
    cv.rect(4, 23, 40, 26, C('wood', 1))
    cv.hline(4, 40, 25, C('wood', 0))
    cv.rect(6, 6, 38, 19, C('wood', 1))                  # the console, sloped panel
    for y in range(6, 19):
        lean = (19 - y) // 4
        cv.rect(6 + lean, y, 38 - lean, y + 1, C('wood', 2) if y < 9 else C('wood', 1))
    cv.rect(8, 8, 36, 18, C('night', 1))                 # bakelite face
    cv.hline(8, 36, 8, C('night', 3))
    cv.hline(8, 36, 17, C('night', 0))
    pins_at = [(1, 0), (2, 1), (0, 2), (3, 3)]
    for r_ in range(4):
        for c in range(4):
            cv.px(11 + c * 4, 9 + r_ * 2, C('brass', 2))
    for (c, r_) in pins_at:
        x, y = 11 + c * 4, 9 + r_ * 2
        cv.px(x, y, IVORY[3])
        cv.px(x, y - 1, IVORY[4])
    yl = YEL[4] if frame in (1, 3) else YEL[1]
    cv.disc(30.5, 11.0, 1.7, yl)
    cv.disc(30.5, 15.0, 1.7, RED[1])
    for k in range(3):
        on = ((frame in (2, 3)) and k != 1) or (frame == 0 and k == 0)
        cv.px(34, 10 + k * 2, GRN[4] if on else GRN[1])
    cv.hline(6, 38, 6, C('brass', 3))
    cv.px(7, 7, C('brass', 4))
    cv.px(37, 7, C('brass', 4))
    cv.px(5, 8, C('iron', 4))                            # headset hanging from a hook
    cv.line(5, 9, 3, 13, C('iron', 2))
    cv.line(5, 9, 7, 13, C('iron', 2))
    cv.rect(2, 13, 4, 16, C('iron', 1))
    cv.rect(6, 13, 8, 16, C('iron', 1))
    cv.px(2, 13, C('iron', 3))
    cv.px(6, 13, C('iron', 3))
    cv.line(7, 16, 9, 21, C('iron', 1))
    cv.rect(26, 19, 36, 20, C('paper', 4))               # papers and a pencil
    cv.rect(27, 18, 35, 19, C('paper', 5))
    cv.line(14, 19, 21, 18, C('amber', 3))
    cv.rect(18, 23, 26, 25, C('paper', 3))               # blank enamel plate on the apron
    m = cv.a[:, :, 3] > 0                                # dark outline, like the hall props
    o = np.zeros_like(m)
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    o &= ~m
    cv.a[o] = C('night', 0)
    return cv


def world_desk():
    frames = [_world_desk(f) for f in range(4)]
    sheet = Image.new('RGBA', (WD_W * 4, WD_H))
    for i, f in enumerate(frames):
        sheet.paste(f.img(), (i * WD_W, 0))
    save(sheet, 'world_desk.png')
    n = np.zeros((WD_H, WD_W * 4, 4), np.uint8)
    alpha = np.asarray(sheet)[:, :, 3]
    for y in range(WD_H):
        for x in range(WD_W * 4):
            if alpha[y, x] == 0:
                continue
            lx = x % WD_W
            nx, ny, nz = 0.0, 0.0, 1.0
            if 19 <= y <= 20:
                ny = -0.75                        # table top: faces up
            elif 6 <= y <= 18 and 6 <= lx <= 38:
                ny = -0.35                        # console face leans back
            if lx in (3, 38) and y > 22:
                nx = -0.4 if lx == 3 else 0.4
            v = np.array([nx, ny, nz])
            v /= np.linalg.norm(v)
            n[y, x] = [int(round((v[0] * 0.5 + 0.5) * 255)), int(round((-v[1] * 0.5 + 0.5) * 255)),
                       int(round((v[2] * 0.5 + 0.5) * 255)), 255]
    save(Image.fromarray(n, 'RGBA'), 'world_desk_n.png')
    e = np.zeros((WD_H, WD_W * 4, 4), np.uint8)
    arr = np.asarray(sheet).astype(np.int32)
    for i in range(4):
        for y in range(WD_H):
            for x in range(WD_W):
                px_ = arr[y, i * WD_W + x]
                if px_[3] == 0:
                    continue
                if (27 <= x <= 35 and 8 <= y <= 17) and px_[:3].sum() > 330:
                    e[y, i * WD_W + x] = [px_[0], px_[1], px_[2], 255]
    save(Image.fromarray(e, 'RGBA'), 'world_desk_e.png')


# ------------------------------------------------------------------------------------------ layout
def layout():
    cols = []
    for c in range(NCOL):
        cx0 = XB_X0 + c * COL_W
        plate = [cx0 + 1, HEAD_Y[0], COL_W - 2, HEAD_Y[1] - HEAD_Y[0]]
        win = [plate[0] + WINDOW[0], plate[1] + WINDOW[1], WINDOW[2], WINDOW[3]]
        tx = win[0] + WINDOW[2] + 3
        tw = plate[0] + plate[2] - tx - 3
        cols.append({'x': cx0, 'w': COL_W, 'plate': plate, 'window': win,
                     'name': [tx, plate[1] + 2, tw - 5, 8], 'out': [tx, plate[1] + 10, tw, 12],
                     'via': [tx, plate[1] + 22, tw, 7],
                     'meter': [plate[0] + METER[0], plate[1] + METER[1], METER[2], METER[3]] if c > 0 else None,
                     'socket_x': cx0 + COL_W // 2})
    rows = []
    for r_ in range(NROW):
        ty0 = ROW_Y0 + r_ * ROW_H + 1
        rows.append({'y': ROW_Y0 + r_ * ROW_H, 'h': ROW_H, 'socket_y': ROW_Y0 + r_ * ROW_H + ROW_H // 2,
                     'tag': [ROWS_X[0] + 4, ty0, ROWS_X[1] - ROWS_X[0] - 8, ROW_H - 2],
                     'code': [ROWS_X[0] + 6, ty0 + 2, 21, ROW_H - 6],
                     'name': [ROWS_X[0] + 30, ty0 + 1, ROWS_X[1] - ROWS_X[0] - 54, 8],
                     'state': [ROWS_X[0] + 30, ty0 + 9, ROWS_X[1] - ROWS_X[0] - 54, 7],
                     'icon': [ROWS_X[1] - 22, ty0 + 4]})
    fx0, fy0, fx1, fy1 = FLOOR
    data = {
        '_doc': 'Relay desk layout in ART px (relay_desk.png is 1:1; the game draws it x3). Written by '
                'tools/pixelgen/gen_mg_relay.py -- do not edit by hand. floor = Saalanzeige (lamp, kicker, speech, '
                'right block, progress groove); cols = sources Saal, Kabine 1-3 (plate, booth window, name/out/via text '
                'boxes, meter window); rows = channels DE, RU, FR, EN (tag, code chip, name and state boxes, icon spot); '
                'lamps = yellow, red (centre, radius, label box); body = everything under the floor display.',
        'size': [W, H],
        'floor': {'rect': [fx0, fy0, fx1 - fx0, fy1 - fy0], 'lamp': list(FLOOR_LAMP),
                  'kicker': [34, 4, FLOOR_DIV - 38, 9], 'speech': [34, 13, FLOOR_DIV - 38, 21],
                  'right': [FLOOR_DIV + 6, 4, fx1 - FLOOR_DIV - 12, 22], 'progress': [441, 30, 118, 2]},
        'rows_panel': [ROWS_X[0], HEAD_Y[0], ROWS_X[1] - ROWS_X[0], H - 1 - HEAD_Y[0]],
        'rows_head': [ROWS_X[0] + 4, HEAD_Y[0] + 4, ROWS_X[1] - ROWS_X[0] - 8, HEAD_Y[1] - HEAD_Y[0] - 7],
        'crossbar': [XB_X0, ROW_Y0, NCOL * COL_W, H - 1 - ROW_Y0],
        'body': [0, HEAD_Y[0] - 1, W, H - HEAD_Y[0] + 1],
        'cols': cols,
        'rows': rows,
        'lamps': [{'centre': [LAMP_C[i][0], LAMP_C[i][1]], 'r': LAMP_R,
                   'label': [LAMP_C[i][0] + LAMP_R + 5, LAMP_C[i][1] - 12, LAMPS_X[1] - (LAMP_C[i][0] + LAMP_R + 5) - 4, 24]}
                  for i in range(2)],
        'lamps_panel': [LAMPS_X[0], HEAD_Y[0], LAMPS_X[1] - LAMPS_X[0], H - 1 - HEAD_Y[0]],
        'zones': [ZONE_YELLOW, ZONE_RED],
        'cells': {'pin': list(PIN_CELL), 'pin_origin': list(PIN_ORIGIN), 'lamp': [30, 30], 'icon': [9, 9],
                  'booth': [20, 24], 'interpreter': [56, 56]},
        'world_desk': {'cell': [WD_W, WD_H], 'frames': 4, 'feet': [22, WD_H]},
    }
    save_json('relay_layout.json', data)


def main():
    desk()
    pins()
    lamps()
    icons()
    booths()
    interpreter()
    find_closeup()
    world_desk()
    layout()


if __name__ == '__main__':
    main()
