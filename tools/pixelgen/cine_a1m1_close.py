"""cine_a1m1_close -- shots 2+3 of the A1 -> M1 transition: the stamp comes down on the Karsk freight
ledger (red C-17) and dissolves into the pencil C-17 on a Berlin diazo plan at the IDENTICAL position.

Top-down macro shots, 640x360 (the letterboxed window shows rows 46..313).  Both glyphs are built on the
same skeleton (GLYPH) so the match dissolve lands exactly.  Lamp light comes from the upper left.

Writes assets/cinematics/a1m1/close/:
  ledger.png            ledger page (sepia), the C-17 row with wagon 24-311 and the blacked-out recipient
  ledger_hist.png       + the faded round railway seal with hammer & sickle (neutral: gear-and-wheat seal)
  imprint.png           strip 4: red C-17 stamp, wet -> soaked -> dry (ink spread)
  stamp.png             strip 3: hand + rubber stamp seen from above: high, hover, contact (scale 1.12/1.06/1)
  stamp_shadow.png      strip 3: dithered shadow of the stamp for the three heights
  hand_irina.png        branch share_with_irina: Irina's hand holding the page flat (left edge)
  plan.png              Berlin diazo plan, blue lines, corridor + second wall (archive palette)
  plan_hist.png         + GBI round office stamp with the eagle and swastika (neutral: eagle with the
                        fictional Reichssiegel), TECHNICAL_ARCHITECTURE 12.4
  pencil.png            pencil C-17 + circle + arrow (graphite), separate layer for the glyph morph
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_a1m1_lib as lib  # noqa: E402
from cine_a1m1_lib import Layer, SR_, AR, tone_put, bayer, value_noise, white_noise, seed_of  # noqa: E402

TONE = SR_['tone']          # 12 sepia tones dark -> light
RED = SR_['red']            # 4 reds
PAPER, BLUE, INK, WOOD, AMB = AR['paper'], AR['blue'], AR['ink'], AR['wood'], AR['amber']
DIR = 'close'
VW, VH = 640, 360
GLYPH_C = (320, 176)        # centre of the C-17 mark (same in both shots)


def glyph_polys():
    """C-17 skeleton (polylines) centred on GLYPH_C; letter height 60 px."""
    cx, cy = GLYPH_C
    ox, oy = cx - 66, cy
    arc = [(ox + 2 + 20 * math.cos(math.radians(t)), oy - 29 * math.sin(math.radians(t)))
           for t in np.linspace(48, 312, 36)]
    dash = [(ox + 32, oy + 2), (ox + 50, oy + 2)]
    one = [(ox + 64, oy - 20), (ox + 76, oy - 29), (ox + 76, oy + 29)]
    seven = [(ox + 94, oy - 28), (ox + 128, oy - 28), (ox + 106, oy + 29)]
    return [arc, dash, one, seven]


def paper_field(w, h, seed, base, amp=0.5, cell=34):
    nz = value_noise(w, h, cell, seed, octaves=3)
    return base + (nz - 0.5) * amp


def vignette(L, ramp, strength, cx, cy, power=1.7, mask=None):
    yy, xx = np.mgrid[0:L.h, 0:L.w].astype(np.float32)
    d = np.sqrt(((xx - cx) / (L.w * 0.6)) ** 2 + ((yy - cy) / (L.h * 0.62)) ** 2)
    return -strength * np.clip(d, 0, 1.4) ** power


def cursive_polys(x, y, length, seed, h=6.5):
    """Pixel cursive: words of trochoid loops with occasional ascenders/descenders (reads as handwriting
    without pretending to be legible text)."""
    rng = np.random.default_rng(seed)
    words = []
    xx = x
    while xx < x + length - 8:
        word = []
        for k in range(int(rng.integers(3, 8))):
            a = rng.uniform(2.0, 3.0)
            hh = h * rng.uniform(0.45, 0.75)
            asc = rng.random() < 0.2
            desc = rng.random() < 0.12
            for u in np.linspace(0, 2 * math.pi, 9)[(1 if word else 0):]:
                px = xx + a * u / math.pi - 0.9 * math.sin(u)
                lift = (1 - math.cos(u)) / 2
                py = y - hh * lift * (2.1 if asc else 1.0) + (h * 0.7 * math.sin(u / 2) if desc else 0)
                word.append((px, py))
            xx += 2 * a
        words.append(word)
        xx += rng.uniform(5, 10)
    return words


def scribble(L, x, y, length, seed, ramp, tone, width=1.0):
    m = lib.stroke_raster(L.w, L.h, cursive_polys(x, y, length, seed), width, ss=4)
    tone_put(L, m, 0, 0, ramp, tone, dither=False)


# =========================================================================== ledger page
def make_ledger(hist: bool):
    L = Layer(VW, VH, 'ledger')
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    # paper: warm lamp from the upper left, darker toward the binding gutter (left) and the bottom
    t = 9.0 + 1.3 * np.clip(1 - np.hypot(xx - 150, yy - 40) / 640, 0, 1)
    t -= 3.6 * np.clip((52 - xx) / 52, 0, 1) ** 1.5
    t += (value_noise(VW, VH, 28, seed_of('lpaper'), octaves=3) - 0.5) * 0.6
    t += vignette(L, TONE, 2.4, 330, 170)
    tone_put(L, np.ones((VH, VW), bool), 0, 0, TONE, t, hgt=0.0)
    rng = np.random.default_rng(seed_of('lfibres'))
    for _ in range(1100):                                         # paper tooth / fibres
        x, y = int(rng.integers(0, VW)), int(rng.integers(0, VH))
        ln = int(rng.integers(1, 4))
        c = L.c[y, x].copy()
        idx = int(np.argmin([np.abs(c[:3].astype(int) - tc[:3].astype(int)).sum() for tc in TONE]))
        L.rect(x, y, ln, 1, TONE[max(0, idx - 1)])
    # ruled rows (36 px) and column rules
    rows = list(range(34, VH, 36))
    for y in rows:
        for x in range(VW):
            c = L.c[y, x]
            idx = int(np.argmin([np.abs(c[:3].astype(int) - tc[:3].astype(int)).sum() for tc in TONE]))
            L.c[y, x] = TONE[max(0, idx - 3)]
    for x in (96, 99, 214, 486, 572):
        for y in range(VH):
            c = L.c[y, x]
            idx = int(np.argmin([np.abs(c[:3].astype(int) - tc[:3].astype(int)).sum() for tc in TONE]))
            L.c[y, x] = TONE[max(0, idx - 2)]
    # entries: date | wagon no. | cargo | consignee | tons -- handwritten, ink tone 2..3
    gr = TONE
    stamp_row = 34 + 3 * 36 + 27   # baseline 169: the C-17 row (wagon 24-311) under the stamp
    for i, y0 in enumerate(rows[:-1]):
        base = y0 + 27
        if base > VH - 4:
            break
        tn = 2.0 if 60 < base < 300 else 3.0
        day = '%d.1.' % (9 + i)
        lib.text(L, 20, base - 5, day, gr[2])
        num = '24-%03d' % (300 + i * 3 + (2 if base == stamp_row else 0))
        if base == stamp_row:
            num = '24-311'
        lib.text(L, 110, base - 5, num, gr[1] if base == stamp_row else gr[2])
        scribble(L, 224, base, 150 + (i * 37) % 90, seed_of('cargo%d' % i), gr, tn)
        if base == stamp_row:
            # the consignee is blacked out (A1 story: "Der Empfänger ist geschwärzt")
            for k in range(3):
                y = base - 7 + k * 3
                pts = [(490 + rng.uniform(-2, 2), y + rng.uniform(-0.6, 0.6)), (530, y + rng.uniform(-0.8, 0.8)),
                       (566 + rng.uniform(-3, 1), y + rng.uniform(-0.6, 0.6))]
                m = lib.stroke_raster(VW, VH, [pts], 3.4, ss=4)
                tone_put(L, m, 0, 0, gr, 0.3)
        else:
            scribble(L, 494, base, 60 + (i * 23) % 20, seed_of('cons%d' % i), gr, tn)
        lib.text(L, 584, base - 5, str(18 + (i * 7) % 9), gr[2])
    # page corner seal (faded, old, partially under the stamp area? no: lower left, out of the way)
    sx, sy = 60, 252
    d = lib.disc_mask(44)
    ring = lib.edge_of(d) | (lib.edge_of(lib.erode(d, 3)))
    seal = Layer(44, 44, 'seal')
    seal._put(ring, 0, 0, RED[1])
    inner = lib.HS_15 if hist else lib.GEAR_WHEAT_13
    ih, iw = inner.shape
    seal._put(inner, (44 - iw) // 2, (44 - ih) // 2, RED[1])
    for k in range(0, 44, 3):                                         # tiny lettering dots in the ring
        a = k / 44 * 2 * math.pi
        seal.px(22 + math.cos(a) * 18.5, 22 + math.sin(a) * 18.5, RED[0])
    keep = (white_noise(44, 44, seed_of('sealfade')) > 0.16) & seal.alpha()
    seal.c[~keep] = 0
    L.blit(seal, sx, sy)
    L.hgt[:] = 0
    return L


def make_imprint():
    """Red stamp: double frame + C-17, uneven ink, 4 frames: wet (gloss) -> spreading -> soaked -> dry."""
    frames = []
    sk = glyph_polys()
    cx, cy = GLYPH_C
    fx0, fy0, fx1, fy1 = cx - 84, cy - 46, cx + 84, cy + 46
    frame_o = [[(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1), (fx0, fy0)]]
    frame_i = [[(fx0 + 8, fy0 + 7), (fx1 - 8, fy0 + 7), (fx1 - 8, fy1 - 7), (fx0 + 8, fy1 - 7), (fx0 + 8, fy0 + 7)]]
    glyph = lib.stroke_raster(VW, VH, sk, 9.0, ss=4)
    fr = lib.stroke_raster(VW, VH, frame_o, 3.2, ss=4) | lib.stroke_raster(VW, VH, frame_i, 1.4, ss=4)
    for x in range(fx0 + 16, fx1 - 16, 9):                           # micro lettering line at the top
        fr[fy0 + 11:fy0 + 13, x:x + 6] = True
    stamp = glyph | fr
    nz = value_noise(VW, VH, 5, seed_of('inknz'), octaves=3)
    wn = white_noise(VW, VH, seed_of('inkwn'))
    base_gaps = stamp & ((wn < 0.05) | ((nz < 0.28) & (wn < 0.30)))
    edge = stamp & ~lib.erode(stamp, 1)
    spread = lib.dilate(stamp, 1) & ~stamp & (nz > 0.55) & (wn < 0.5)
    for k in range(4):
        F = Layer(VW, VH, 'imprint%d' % k)
        m = stamp & ~base_gaps
        if k >= 1:
            m = m | (spread & (wn < 0.2 + 0.12 * k))
        if k >= 2:
            m = m & ~(stamp & (wn > 0.9 - 0.04 * k) & (nz < 0.45))       # paper fibres drink the ink
        tone = np.full((VH, VW), 2.0, np.float32)
        tone[edge] = 1.0 + (0.6 if k == 0 else 0)
        tone[(nz > 0.6) & stamp] = 2.6
        if k <= 1:                                                     # wet gloss: lighter red pixels
            gloss = stamp & ~edge & (wn > (0.88 if k == 0 else 0.95)) & (nz > 0.4)
            tone[gloss] = 3.0
        if k == 3:
            tone -= 0.35
        tone_put(F, m, 0, 0, RED, tone, dither=True)
        if k == 0:                                                     # specular glints of the lamp
            sp = stamp & ~edge & (wn > 0.985)
            F._put(sp, 0, 0, TONE[11])
        F.hgt[:] = 0
        crop, ox, oy = lib.crop_alpha(F, pad=2)
        frames.append((F, ox, oy))
    # common crop box for all frames
    x0 = min(o[1] for o in frames)
    y0 = min(o[2] for o in frames)
    x1 = max(o[1] + lib.crop_alpha(o[0], 2)[0].w for o in frames)
    y1 = max(o[2] + lib.crop_alpha(o[0], 2)[0].h for o in frames)
    out = []
    for F, _, _ in frames:
        C = Layer(x1 - x0, y1 - y0, F.name)
        C.c = F.c[y0:y1, x0:x1].copy()
        out.append(C)
    return out, (x0, y0)


# =========================================================================== stamp + hand (top-down)
def _stamp_frame(scale: float, press: bool, branch_sleeve):
    """Office rubber stamp seen from above with a slight tilt: wooden block, brass ferrule and the turned
    handle leaning out of the frame toward the top (the hand stays outside the letterboxed frame -- only the
    dark coat sleeve shows at the very top). Re-rendered per height (scale), never resampled."""
    W, H = 300, 330
    L = Layer(W, H, 'stamp')
    s = scale
    cx, cy = 130, 250                                   # block centre (anchor)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bw, bh, side = 176 * s, 98 * s, (7 if not press else 5) * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    # front side face of the block (visible because of the tilt) + dark rubber edge
    sidem = lib.poly_raster(W, H, [[(x0 + 2, y0 + bh - 2), (x0 + bw - 2, y0 + bh - 2), (x0 + bw - 3, y0 + bh + side),
                                    (x0 + 3, y0 + bh + side)]])
    tone_put(L, sidem, 0, 0, TONE, 3.2 + (xx - x0) / bw * -0.8)
    rub = lib.poly_raster(W, H, [[(x0 + 3, y0 + bh + side - 1), (x0 + bw - 3, y0 + bh + side - 1),
                                  (x0 + bw - 4, y0 + bh + side + 2), (x0 + 4, y0 + bh + side + 2)]])
    L._put(rub, 0, 0, RED[0] if not press else TONE[1])
    blk = lib.poly_raster(W, H, [[(x0 + 4, y0), (x0 + bw - 4, y0), (x0 + bw, y0 + 4), (x0 + bw, y0 + bh - 4),
                                  (x0 + bw - 4, y0 + bh), (x0 + 4, y0 + bh), (x0, y0 + bh - 4), (x0, y0 + 4)]])
    grain = value_noise(W, H, 3, seed_of('wood'), octaves=2)
    tone = 5.4 + (grain - 0.5) * 1.0 + np.sin(xx * 0.30 + grain * 5) * 0.3
    tone -= np.clip((xx - x0) / bw, 0, 1) * 0.9 + np.clip((yy - y0) / bh, 0, 1) * 0.7
    tone_put(L, blk, 0, 0, TONE, tone)
    e = blk & ~lib.erode(blk, 2)
    L._put(e, 0, 0, TONE[3])
    L._put(e & ((yy < y0 + 2.5) | (xx < x0 + 2.5)), 0, 0, TONE[8])
    lx, ly = int(cx - 74 * s), int(cy + 18 * s)
    L.rect(lx, ly, int(36 * s), int(15 * s), TONE[10])
    L.hline(lx, ly, int(36 * s), TONE[11])
    L.hline(lx, ly + int(15 * s) - 1, int(36 * s), TONE[7])
    lib.text(L, lx + 5, ly + int(5 * s), 'C-17', TONE[2])
    # brass ferrule (ellipse) at the handle foot
    fm, fx_, fy_ = L.ellipse_mask(cx, cy - 2 * s, 24 * s, 12 * s)
    gg = np.mgrid[0:fm.shape[0], 0:fm.shape[1]]
    tone_put(L, fm, fx_, fy_, TONE, 7.4 - (gg[1] / max(1, fm.shape[1])) * 3.0 - (gg[0] / max(1, fm.shape[0])) * 1.2)
    L._put(lib.edge_of(fm), fx_, fy_, TONE[3])
    # turned handle: tapered cylinder leaning up and slightly right, widening toward the camera
    top_x, top_y = cx + 34 * s, -10
    n = int(cy - 4 * s - top_y)
    for i in range(n):
        y = int(cy - 4 * s) - i
        u = i / max(1, n - 1)
        xc = cx + (top_x - cx) * u
        w = (15 + 9 * u + (4 if 0.18 < u < 0.26 else 0)) * s        # a turned bead ring part way up
        xl, xr = int(round(xc - w / 2)), int(round(xc + w / 2))
        for x in range(xl, xr + 1):
            if not (0 <= x < W and 0 <= y < H):
                continue
            q = (x - xl) / max(1, xr - xl)                           # 0 = left (lit) .. 1 = right
            tq = 7.6 - q * 4.6 - u * 0.4
            if 0.18 < u < 0.26:
                tq += 0.6
            k = int(np.clip(round(tq + (bayer(1, 1, x, y)[0, 0] - 0.5)), 0, 11))
            L.c[y, x] = TONE[k]
        if 0 <= xl < W and 0 <= y < H:
            L.c[y, xl] = TONE[3]
        if 0 <= xr < W and 0 <= y < H:
            L.c[y, xr] = TONE[2]
    # the coat sleeve of the hand holding it, at the very top (cut by the frame)
    sl = lib.poly_raster(W, H, [[(top_x - 50 * s, -20), (top_x + 70 * s, -20), (top_x + 64 * s, 14 * s),
                                 (top_x - 40 * s, 22 * s)]])
    tone_put(L, sl, 0, 0, TONE, branch_sleeve + (value_noise(W, H, 5, seed_of('sleeve'), octaves=2) - 0.5))
    L._put(lib.edge_of(sl), 0, 0, TONE[0])
    L.hgt[:] = 0
    return L, (cx, cy)


def _shadow(scale: float, offset):
    W, H = 300, 330
    S = Layer(W, H, 'shadow')
    cx, cy = 130 + offset[0], 250 + offset[1]
    bw, bh = 176 * scale * 1.02, 98 * scale * 1.02
    m = lib.poly_raster(W, H, [[(cx - bw / 2, cy - bh / 2), (cx + bw / 2, cy - bh / 2), (cx + bw / 2, cy + bh / 2),
                                (cx - bw / 2, cy + bh / 2)]])
    shaft = lib.stroke_raster(W, H, [[(cx + 8, cy), (cx + 60, cy - 120)]], 16 * scale, ss=3)
    m = m | shaft
    soft = lib.dilate(m, 2) & ~m
    dens = 0.55 if scale > 1.05 else 0.75
    S._put(m & (bayer(W, H, size=4) < dens), 0, 0, TONE[5])
    S._put(soft & (bayer(W, H, size=4) < dens * 0.35), 0, 0, TONE[6])
    return S


def make_stamp_frames(sleeve_tone):
    frames, shadows = [], []
    for (sc, press, off) in ((1.12, False, (16, 12)), (1.06, False, (8, 6)), (1.0, True, (2, 2))):
        F, anchor = _stamp_frame(sc, press, sleeve_tone)
        frames.append(F)
        shadows.append(_shadow(sc, off))
    return frames, shadows, anchor


def make_initials():
    """Branch share_with_irina: Irina's countersign in the margin of the C-17 row (blue pencil, sepia):
    a tick and the initials of Irina Belova -- now two people have signed what they know."""
    L = Layer(40, 22, 'initials')
    tick = lib.stroke_raster(40, 22, [[(2, 12), (6, 17), (14, 4)]], 1.2, ss=4)
    L._put(tick, 0, 0, TONE[2])
    lib.text(L, 18, 9, '\u0418.\u0411.', TONE[2], spacing=1)
    und = lib.stroke_raster(40, 22, [[(17, 17), (38, 16)]], 1.0, ss=4)
    L._put(und, 0, 0, TONE[3])
    return L


# =========================================================================== Berlin plan
def make_plan(hist: bool):
    L = Layer(VW, VH, 'plan')
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    t = 4.4 + 0.9 * np.clip(1 - np.hypot(xx - 120, yy - 60) / 640, 0, 1)
    t += (value_noise(VW, VH, 60, seed_of('ppaper'), octaves=2) - 0.5) * 0.45
    t += vignette(L, PAPER, 1.6, 330, 170)
    tone_put(L, np.ones((VH, VW), bool), 0, 0, PAPER, t)
    rng = np.random.default_rng(seed_of('ptooth'))
    for _ in range(1300):
        x, y = int(rng.integers(0, VW)), int(rng.integers(0, VH))
        L.rect(x, y, int(rng.integers(1, 3)), 1, PAPER[max(0, int(t[y, x]) - 1)])
    # printed construction grid (light blue dots)
    for gx in range(40, VW, 112):
        for y in range(0, VH, 5):
            L.rect(gx, y, 2, 1, BLUE[4])
    for gy in (30, 254):
        for x in range(0, VW, 5):
            L.rect(x, gy, 2, 1, BLUE[4])

    def diazo(m, tone=2.6):
        L._put(lib.dilate(m, 1) & ~m, 0, 0, BLUE[4])
        L._put(m, 0, 0, BLUE[int(tone)])
    walls = np.zeros((VH, VW), bool)
    walls[0:64, 28:48] = True             # thick outer wall with the corridor gap
    walls[118:VH, 28:48] = True
    walls[300:318, 48:VW] = True          # south wall
    diazo(walls, 2)
    sec = np.zeros((VH, VW), bool)        # the SECOND wall (dashed) - the contradiction
    for y in range(60, 122):
        if (y // 6) % 2 == 0:
            sec[y, 96:104] = True
    diazo(sec, 3)
    cor = np.zeros((VH, VW), bool)        # corridor continuing behind it (dashed outlines)
    for x in range(48, VW):
        if (x // 14) % 2 == 0:
            cor[62:66, x] = True
            cor[116:120, x] = True
    diazo(cor, 3)
    for x in range(120, VW, 20):          # walking line
        L.rect(x, 90, 6, 2, BLUE[3])
    # dimension line + tick marks + small printed labels
    L.hline(60, 284, 520, BLUE[3])
    for x in (60, 236, 412, 580):
        L.vline(x, 280, 9, BLUE[3])
    lib.text(L, 140, 274, '12.40', BLUE[2])
    lib.text(L, 316, 274, '12.40', BLUE[2])
    lib.text(L, 470, 274, '9.60', BLUE[2])
    lib.text(L, 500, 230, 'BLATT 7', BLUE[2])
    lib.text(L, 500, 238, 'NORDACHSE C', BLUE[3])
    # GBI office stamp, lower left (blue-violet ink)
    sx, sy = 62, 186
    D = 58
    stamp = Layer(D, D, 'gbi')
    d = lib.disc_mask(D)
    stamp._put(lib.edge_of(d) | lib.edge_of(lib.erode(d, 4)), 0, 0, BLUE[1])
    for k in range(0, 40):
        a = k / 40 * 2 * math.pi
        if k % 5:
            stamp.px(D / 2 + math.cos(a) * (D / 2 - 4.5), D / 2 + math.sin(a) * (D / 2 - 4.5), BLUE[1])
    eagle = eagle_mask()
    eh, ew = eagle.shape
    stamp._put(eagle, (D - ew) // 2, 12, BLUE[1])
    if hist:
        sw = lib.swastika(3, 2, 2)
        wr = lib.edge_of(lib.disc_mask(16))
        stamp._put(wr, (D - 16) // 2, 12 + eh, BLUE[1])
        stamp._put(sw, (D - sw.shape[1]) // 2, 12 + eh + 2, BLUE[1])
    else:
        rs = lib.REICHSSIEGEL_11
        wr = lib.edge_of(lib.disc_mask(16))
        stamp._put(wr, (D - 16) // 2, 12 + eh, BLUE[1])
        stamp._put(rs, (D - rs.shape[1]) // 2, 12 + eh + 3, BLUE[1])
    keep = (white_noise(D, D, seed_of('gbifade')) > 0.12) & stamp.alpha()
    stamp.c[~keep] = 0
    L.blit(stamp, sx, sy)
    L.hgt[:] = 0
    return L


def eagle_mask() -> np.ndarray:
    """Small heraldic eagle (wings spread, head turned to the viewer's left), 23x12."""
    rows = [
        '..........X............',
        '.........XXX...........',
        '........XXX............',
        'X........XX...........X',
        'XX......XXXX.........XX',
        'XXXX...XXXXXX......XXXX',
        '.XXXXXXXXXXXXXXXXXXXXX.',
        '..XXXXXXXXXXXXXXXXXXX..',
        '....XXXX.XXXXX.XXXX....',
        '.........XXXXX.........',
        '........XX.X.XX........',
        '.......X...X...X.......',
    ]
    return lib._grid(rows)


def make_pencil():
    L = Layer(VW, VH, 'pencil')
    sk = glyph_polys()
    core = lib.stroke_raster(VW, VH, sk, 2.6, ss=4)
    second = lib.stroke_raster(VW, VH, [[(x + 1.2, y - 0.8) for (x, y) in p] for p in sk], 1.4, ss=4)
    gr = white_noise(VW, VH, seed_of('graph'))
    pm = (core | second) & (gr > 0.14)
    tone = np.where(gr > 0.72, 1.0, np.where(gr > 0.4, 0.4, 0.0)).astype(np.float32)
    tone_put(L, pm, 0, 0, [INK[1], BLUE[1], BLUE[2]], tone, dither=False)
    cx, cy = GLYPH_C
    # circle round the code, underline, arrow toward the second wall
    ring = [(cx + math.cos(a) * 104, cy + math.sin(a) * 56) for a in np.linspace(0.2, 2 * math.pi + 0.6, 80)]
    rm = lib.stroke_raster(VW, VH, [ring], 1.3, ss=4) & (gr > 0.2)
    L._put(rm, 0, 0, BLUE[1])
    arr = [(cx - 104, cy - 22), (cx - 150, cy - 60), (cx - 196, cy - 82), (110, 92)]
    am = lib.stroke_raster(VW, VH, [arr, [(110, 92), (122, 84)], [(110, 92), (121, 101)]], 1.3, ss=4) & (gr > 0.15)
    L._put(am, 0, 0, BLUE[1])
    un = lib.stroke_raster(VW, VH, [[(cx - 70, cy + 40), (cx, cy + 37), (cx + 66, cy + 41)]], 1.4, ss=4) & (gr > 0.2)
    L._put(un, 0, 0, INK[1])
    L.hgt[:] = 0
    crop, ox, oy = lib.crop_alpha(L, pad=1)
    return crop, (ox, oy)


# =========================================================================== build
def build():
    info = {}
    for hist in (False, True):
        sfx = '_hist' if hist else ''
        info['ledger' + sfx] = lib.save(make_ledger(hist), DIR + '/ledger' + sfx, normal=False)
        info['plan' + sfx] = lib.save(make_plan(hist), DIR + '/plan' + sfx, normal=False)
    frames, org = make_imprint()
    info['imprint'] = lib.strip(frames, DIR + '/imprint', normal=False)
    info['imprint']['pos'] = [int(v) for v in org]
    for branch, tone in (('alexei', 2.2), ):
        fr, sh, anchor = make_stamp_frames(tone)
        info['stamp'] = lib.strip(fr, DIR + '/stamp', normal=False)
        info['stamp']['anchor'] = [int(v) for v in anchor]
        info['stamp_shadow'] = lib.strip(sh, DIR + '/stamp_shadow', normal=False)
    info['initials'] = lib.save(make_initials(), DIR + '/initials', normal=False)
    pen, porg = make_pencil()
    info['pencil'] = lib.save(pen, DIR + '/pencil', normal=False)
    info['pencil']['pos'] = [int(v) for v in porg]
    info['glyph_centre'] = list(GLYPH_C)
    return info


if __name__ == '__main__':
    import json
    print(json.dumps(build(), indent=1))
