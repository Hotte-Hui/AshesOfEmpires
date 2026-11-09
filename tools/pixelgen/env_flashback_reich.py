"""env_flashback_reich -- the six plates of the two flashback films on the Reich side (TECHNICAL_ARCHITECTURE 12.15).

  nuremberg  (card hist.reich.nuremberg_interpreters)  court / booth / desk
  evictions  (card hist.reich.evictions)               street / chronicle / room
Only what the cards say is shown: the courtroom with the glazed, roofless booth and listeners with headphones (from
behind); the interpreters at their desk (from behind); headphones, the selector switch with four positions and the
yellow and the red lamp; a Berlin street with a handcart and three open, empty windows; the office chronicle of
1941 on a desk beside a plan with hatched blocks; the cleared room.  No faces, no uniforms, no insignia, no flags.
Painted with env_flashback_kit (luminance -> sepia ramp); deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import pg
from env_flashback_kit import PW, PH, Plate, rng, greek, wheel, pole, seated_back, tiny_head


# ================================================================================================ Nuremberg
def court() -> Plate:
    p = Plate(v=0.5)
    A = p.all()
    p.vgrad(A, 0, 0.62, 150, 0.52)                                    # plaster above the panelling
    pan = p.box(0, 150, PW, PH)
    p.fill(pan, 0.34)
    p.tex(pan, 0.03, 30, 11, sy=6.0)                                  # the grain runs upright
    for x in range(-6, PW, 26):                                       # panel stiles
        p.fill(p.box(x, 156, x + 2, PH), 0.25)
        p.fill(p.box(x + 2, 156, x + 3, PH), 0.41)
    p.fill(p.box(0, 148, PW, 151), 0.64)
    p.fill(p.box(0, 151, PW, 155), 0.22)
    p.fill(p.box(0, 34, PW, 36), 0.70)
    p.fill(p.box(0, 36, PW, 39), 0.44)
    for wx in (36, 150):                                              # two tall windows, heavy curtains half shut
        p.fill(p.box(wx, 50, wx + 62, 236), 0.2)
        p.fill(p.box(wx + 4, 54, wx + 58, 232), 0.9)
        p.fill(p.box(wx + 30, 54, wx + 32, 232), 0.36)
        for wy in (98, 142, 186):
            p.fill(p.box(wx + 4, wy, wx + 58, wy + 2), 0.36)
        for a, b in ((wx - 8, wx + 20), (wx + 44, wx + 70)):
            p.fill(p.box(a, 44, b, 240), 0.15)
            for fx in range(a + 3, b, 5):
                p.fill(p.box(fx, 46, fx + 1, 240), 0.23)
        p.fill(p.box(wx - 12, 40, wx + 74, 46), 0.11)
    p.glow(100, 150, 190, 170, 0.14)                                  # daylight in the room
    for lx in (96, 256, 416):                                         # strip lights
        p.fill(p.box(lx - 1, 0, lx + 1, 12), 0.2)
        p.fill(p.box(lx - 32, 10, lx + 32, 12), 0.3)
        p.fill(p.box(lx - 30, 12, lx + 30, 19), 0.98)
        p.glow(lx, 32, 92, 44, 0.2)
    # the booth of the interpreters in the corner: glass at the front and the sides, no roof
    bx0, bx1, by0, base, by1 = 292, 486, 152, 206, 238
    glass = p.box(bx0 + 2, by0, bx1 - 2, base)
    p.mix(glass, 0.52, 0.5)
    for row, (hy, hr) in enumerate(((172, 4.0), (184, 4.6))):
        for i in range(4):
            tiny_head(p, bx0 + 26 + i * 46 + (14 if row else 0), hy, hr, True)
    for k in range(-70, 230, 38):                                     # the panes catch the lamps
        p.lift(p.poly([(bx0 + k, base), (bx0 + k + 9, base), (bx0 + k + 60, by0), (bx0 + k + 51, by0)]) & glass, 0.2)
    p.fill(p.box(bx0, base, bx1, by1), 0.21)
    p.fill(p.box(bx0, base, bx1, base + 2), 0.44)
    for x in range(bx0 + 8, bx1, 24):
        p.fill(p.box(x, base + 7, x + 1, by1 - 4), 0.15)
    for x in (bx0, bx0 + 48, bx0 + 97, bx0 + 146, bx1 - 3):
        p.fill(p.box(x, by0 - 2, x + 3, base), 0.76)
    p.fill(p.box(bx0, by0 - 2, bx1, by0), 0.76)
    p.fill(p.box(bx0 - 3, by0 - 2, bx0, by1), 0.26)
    # a long table, then the rows of listeners: nearly every one with headphones
    p.fill(p.box(16, 236, 276, 243), 0.54)
    p.fill(p.box(16, 243, 276, 262), 0.19)
    rows = ((248, 6.5, 30, 14), (282, 9.5, 44, 4), (322, 13.5, 62, 22))
    for ri, (y, r, pitch, off) in enumerate(rows):
        x, k = off - pitch, 0
        while x < PW + pitch:
            seated_back(p, x + (3 if k % 3 == 1 else 0), y + (k * 7 % 3) - 1, r,
                        coat=0.12 + 0.03 * ((k * 5 + ri) % 3), head=0.19 + 0.03 * ((k + ri) % 2),
                        phones=0.66 if (k * 3 + ri) % 7 else None, chair=0.23 + 0.02 * (ri % 2))
            x += pitch
            k += 1
    p.shade(A, np.clip((p.yy - 262) / 260.0, 0, 1) * 0.4)
    return p


def booth() -> Plate:
    p = Plate(v=0.5)
    A = p.all()
    p.vgrad(A, 0, 0.64, 130, 0.55)
    p.fill(p.box(0, 130, PW, 262), 0.37)
    for x in range(4, PW, 22):
        p.fill(p.box(x, 134, x + 1, 262), 0.29)
    p.fill(p.box(0, 128, PW, 131), 0.62)
    for wx in (300, 404):                                             # the draped windows of the far wall
        p.fill(p.box(wx, 52, wx + 44, 192), 0.88)
        p.fill(p.box(wx + 21, 52, wx + 23, 192), 0.4)
        p.fill(p.box(wx - 6, 46, wx + 12, 198), 0.17)
        p.fill(p.box(wx + 32, 46, wx + 50, 198), 0.17)
        p.fill(p.box(wx - 9, 42, wx + 53, 47), 0.12)
    for lx in (70, 230, 390):
        p.fill(p.box(lx - 1, 0, lx + 1, 24), 0.25)
        p.fill(p.box(lx - 26, 24, lx + 26, 30), 0.98)
        p.glow(lx, 42, 84, 40, 0.2)
    r = rng(5)                                                        # the benches: rows of small heads, a table
    for hy, hr, pitch in ((170, 3.0, 15), (190, 3.6, 19)):
        x = int(r.integers(0, 8))
        while x < PW:
            tiny_head(p, x, hy + int(r.integers(-1, 2)), hr, bool(r.random() < 0.85))
            x += pitch + int(r.integers(-2, 3))
    p.fill(p.box(0, 206, PW, 212), 0.5)
    p.fill(p.box(0, 212, PW, 226), 0.2)
    x = 6
    while x < PW:
        tiny_head(p, x, 216 + int(r.integers(-1, 2)), 4.6, bool(r.random() < 0.85))
        x += 25 + int(r.integers(-3, 4))
    # glass in front of us and at the sides, uprights, ONE rail on top: above it the room is seen clear
    rail = 88
    glass = p.box(0, rail, PW, 262)
    p.mix(glass, 0.44, 0.28)
    for k in range(-100, PW, 58):
        p.lift(p.poly([(k, 262), (k + 9, 262), (k + 92, rail), (k + 83, rail)]) & glass, 0.14)
    for x in (22, 178, 334, 490):
        p.fill(p.box(x, rail - 3, x + 5, 262), 0.78)
        p.fill(p.box(x + 5, rail - 3, x + 6, 262), 0.3)
    p.fill(p.box(0, rail - 3, PW, rail + 1), 0.78)
    p.fill(p.box(0, rail + 1, PW, rail + 2), 0.3)
    # the desk along the glass: papers, a microphone for each place
    desk_m = p.box(0, 262, PW, 284)
    p.fill(desk_m, 0.5)
    p.tex(desk_m, 0.04, 30, 9, sx=6.0)
    p.fill(p.box(0, 284, PW, 292), 0.2)
    p.fill(p.box(0, 292, PW, PH), 0.15)
    for px, w in ((30, 34), (182, 30), (338, 38)):
        p.fill(p.box(px, 266, px + w, 279), 0.9)
        greek(p, px + 3, 268, px + w - 3, 3, 3, seed=px, val=0.42)
    for mx in (146, 304, 462):
        p.fill(p.line([(mx, 268), (mx, 238), (mx + 6, 229)], 2), 0.11)
        p.fill(p.ell(mx + 8, 227, 5, 4), 0.09)
        p.fill(p.box(mx - 7, 265, mx + 8, 269), 0.13)
    for i, x in enumerate((92, 250, 408)):                            # three interpreters, from behind
        seated_back(p, x + (5 if i == 1 else 0), 236 - (6 if i == 1 else 0), 17 + (1 if i == 2 else 0),
                    coat=(0.13, 0.17, 0.11)[i], head=(0.21, 0.25, 0.19)[i], phones=0.7, chair=0.2)
    p.shade(A, np.clip((p.yy - 290) / 170.0, 0, 1) * 0.45)
    return p


LAMPS = {'yellow': (416, 152), 'red': (460, 152)}                     # lens centres on the desk plate


def desk() -> Plate:
    """Everything the line speaks of lies in the upper two thirds: the caption plate covers the rest."""
    p = Plate(v=0.44)
    A = p.all()
    p.tex(A, 0.05, 40, 21, sx=8.0)
    p.tex(A, 0.02, 6, 22, sx=12.0)
    p.glow(170, 110, 330, 260, 0.26)
    p.shade(A, np.clip((p.xx - 300) / 520.0 + (p.yy - 230) / 420.0, 0, 1) * 0.4)
    # typed sheets, pushed aside
    sheet = p.poly([(352, -34), (522, -18), (510, 76), (340, 60)])
    p.shade(p.poly([(357, -28), (528, -12), (516, 83), (345, 67)]) & ~sheet, 0.3)
    p.fill(sheet, 0.9)
    greek(p, 362, -14, 500, 9, 8, seed=31, val=0.36, indent=12, slope=0.094, thick=2)
    # the headphones, put down: two cups, the band between them, the cord to the switch
    band = pg.bezier([(108, 152), (90, 60), (242, 50), (232, 188)], 48)
    p.shade(p.line([(x + 5, y + 6) for x, y in band], 9), 0.3)
    p.fill(p.line(band, 9), 0.2)
    p.fill(p.line(band, 5), 0.72)
    p.fill(p.line([(x - 1, y - 1) for x, y in band], 1), 0.9)
    cord = pg.bezier([(250, 216), (262, 262), (318, 268), (336, 232), (334, 202)], 48)
    p.fill(p.line(cord, 3), 0.1)
    for cx, cy in ((120, 168), (222, 204)):
        p.shade(p.ell(cx + 6, cy + 8, 36, 31), 0.35)
        cup = p.ell(cx, cy, 34, 29)
        p.fill(cup, 0.12)
        p.fill(cup & ~p.ell(cx + 2, cy + 2, 34, 29), 0.4)
        p.fill(p.ell(cx, cy, 27, 22), 0.2)
        p.fill(p.ell(cx, cy, 14, 11), 0.1)
        for gy in range(-8, 9, 4):
            p.fill(p.box(cx - 9, cy + gy, cx + 10, cy + gy + 1) & p.ell(cx, cy, 13, 10), 0.3)
    # the selector switch: one knob, four positions
    bx0, by0, bx1, by1 = 286, 108, 378, 200
    p.shade(p.box(bx0 + 6, by0 + 7, bx1 + 7, by1 + 8), 0.35)
    p.fill(p.box(bx0, by0, bx1, by1), 0.22)
    p.fill(p.box(bx0, by0, bx1, by0 + 2) | p.box(bx0, by0, bx0 + 2, by1), 0.4)
    p.fill(p.box(bx0, by1 - 2, bx1, by1) | p.box(bx1 - 2, by0, bx1, by1), 0.12)
    kx, ky = 332, 160
    p.fill(p.ell(kx, ky, 27, 27), 0.7)
    p.fill(p.ell(kx, ky, 27, 27) & ~p.ell(kx, ky, 25, 25), 0.4)
    for a in (-150, -110, -70, -30):
        p.fill(p.ell(kx + math.cos(math.radians(a)) * 36, ky + math.sin(math.radians(a)) * 36, 2.6, 2.6), 0.9)
    p.fill(p.ell(kx, ky, 15, 15), 0.13)
    p.fill(p.ell(kx - 2, ky - 2, 11, 11), 0.2)
    a = math.radians(-110)
    p.fill(p.line([(kx, ky), (kx + math.cos(a) * 24, ky + math.sin(a) * 24)], 3), 0.1)
    p.fill(p.line([(kx + math.cos(a) * 15, ky + math.sin(a) * 15), (kx + math.cos(a) * 24, ky + math.sin(a) * 24)], 1), 0.85)
    # the two lamps of the monitor (both dark on the plate; the film lights them: yellow, then red)
    lx0, ly0, lx1, ly1 = 388, 122, 488, 182
    p.shade(p.box(lx0 + 6, ly0 + 7, lx1 + 7, ly1 + 8), 0.35)
    p.fill(p.box(lx0, ly0, lx1, ly1), 0.18)
    p.fill(p.box(lx0, ly0, lx1, ly0 + 2) | p.box(lx0, ly0, lx0 + 2, ly1), 0.36)
    for name, (cx, cy) in LAMPS.items():
        p.fill(p.ell(cx, cy, 14, 14), 0.1)
        p.fill(p.ell(cx, cy, 12, 12), 0.38 if name == 'yellow' else 0.28)
        p.fill(p.ell(cx - 4, cy - 4, 3, 3), 0.6)
    p.fill(p.poly([(46, 262), (182, 282), (181, 287), (45, 267)]), 0.66)      # a pencil
    p.fill(p.poly([(182, 282), (194, 286), (181, 287)]), 0.3)
    return p


# ================================================================================================ Berlin, August 1941
def _window(p: Plate, x, y, w, h, wall, seed, cleared=False):
    r = rng(seed)
    p.fill(p.box(x - 2, y - 2, x + w + 2, y + h + 2), min(0.95, wall + 0.14))
    p.fill(p.box(x - 3, y + h + 2, x + w + 3, y + h + 4), min(0.95, wall + 0.22))
    p.fill(p.box(x - 3, y + h + 4, x + w + 3, y + h + 5), wall - 0.14)
    if cleared:                                                       # an open window, an empty room behind it
        p.fill(p.box(x, y, x + w, y + h), 0.06)
        p.fill(p.box(x - 5, y, x - 2, y + h) | p.box(x + w + 2, y, x + w + 5, y + h), 0.3)   # both casements stand open
        return
    p.fill(p.box(x, y, x + w, y + h), 0.14)
    c = float(r.random())
    if c < 0.55:                                                      # net curtains
        p.mix(p.box(x + 1, y + h // 3 + 1, x + w - 1, y + h - 1), 0.76, 0.75)
    elif c < 0.8:                                                     # a blind half down
        p.fill(p.box(x + 1, y + 1, x + w - 1, y + int(h * float(r.uniform(0.3, 0.7)))), 0.6)
    p.fill(p.box(x + w // 2 - 1, y, x + w // 2 + 1, y + h), 0.66)
    p.fill(p.box(x, y + h // 3, x + w, y + h // 3 + 1), 0.66)
    if float(r.random()) < 0.3:
        p.fill(p.box(x - 1, y + h - 2, x + w + 1, y + h + 2), 0.26)


def street() -> Plate:
    p = Plate(v=0.5)
    A = p.all()
    p.vgrad(A, 0, 0.84, 60, 0.76)
    p.tex(p.box(0, 0, PW, 60), 0.03, 50, 40, sx=5.0)
    houses = ((-30, 162, 0.56, 40), (162, 352, 0.47, 28), (352, 560, 0.62, 46))
    for hi, (x0, x1, val, ey) in enumerate(houses):
        wall = p.box(x0, ey, x1, 300)
        p.fill(wall, val)
        p.tex(wall, 0.03, 26, 41 + hi)
        p.fill(p.box(x0, ey - 7, x1, ey), val - 0.26)                 # the roof edge
        p.fill(p.box(x0 - 2, ey, x1 + 2, ey + 3), min(0.95, val + 0.14))
        p.fill(p.box(x0 - 2, ey + 3, x1 + 2, ey + 5), val - 0.16)
        p.fill(p.box(x0, 236, x1, 300), val - 0.13)                   # the ground floor, banded
        for y in range(244, 300, 9):
            p.fill(p.box(x0, y, x1, y + 1), val - 0.22)
        p.fill(p.box(x0, 232, x1, 236), min(0.95, val + 0.12))
        n = 5
        pitch = (x1 - x0) / float(n)
        sp = min(47, (218 - ey) // 4)
        for s in range(4):
            wy = ey + 14 + s * sp
            p.fill(p.box(x0, wy + 37, x1, wy + 38), val - 0.08)
            for k in range(n):
                wx = int(x0 + pitch * (k + 0.5)) - 8
                _window(p, wx, wy, 16, 30, val, hi * 100 + s * 10 + k, cleared=(hi == 1 and s == 2 and k in (1, 2, 3)))
        p.fill(p.box(x1 - 2, ey, x1, 300), val - 0.16)                # the joint to the next house
    # ground floors: a shuttered shop, the open house door, a gateway
    for y in range(250, 292, 3):
        p.fill(p.box(18, y, 104, y + 2), 0.38)
        p.fill(p.box(18, y + 2, 104, y + 3), 0.29)
    p.fill(p.box(14, 242, 108, 249), 0.78)                           # a blank signboard
    p.fill(p.box(120, 250, 148, 300), 0.7)
    p.fill(p.box(122, 252, 146, 300), 0.14)
    for wx in (180, 312):
        p.fill(p.box(wx - 2, 250, wx + 22, 284), 0.6)
        p.fill(p.box(wx, 252, wx + 20, 282), 0.13)
        p.fill(p.box(wx + 9, 252, wx + 11, 282), 0.6)
    p.fill(p.box(236, 242, 280, 300), 0.62)                          # the door surround
    p.fill(p.box(241, 248, 275, 300), 0.06)                          # the open doorway
    p.fill(p.box(241, 248, 275, 258), 0.2)
    p.fill(p.box(241, 258, 275, 259), 0.62)
    p.fill(p.poly([(241, 259), (252, 262), (252, 300), (241, 300)]), 0.3)   # one leaf stands open
    p.fill(p.box(232, 298, 284, 301), 0.7)
    gate = p.box(420, 250, 468, 300) | p.ell(444, 250, 24, 12)
    p.fill((p.box(416, 246, 472, 300) | p.ell(444, 250, 28, 16)), 0.72)
    p.fill(gate, 0.1)
    for wx in (372, 488):
        p.fill(p.box(wx - 2, 254, wx + 22, 286), 0.74)
        p.fill(p.box(wx, 256, wx + 20, 284), 0.13)
        p.fill(p.box(wx + 9, 256, wx + 11, 284), 0.74)
    # pavement, kerb, cobbles
    pave = p.box(0, 300, PW, 331)
    p.fill(pave, 0.68)
    p.tex(pave, 0.03, 20, 44)
    for x in range(-10, PW, 34):
        p.fill(p.box(x, 300, x + 1, 331), 0.57)
    p.fill(p.box(0, 315, PW, 316), 0.57)
    p.fill(p.box(0, 300, PW, 302), 0.48)
    p.fill(p.box(0, 331, PW, 335), 0.52)
    p.fill(p.box(0, 335, PW, PH), 0.33)
    for row, y in enumerate(range(337, PH, 6)):
        for x in range(-6 + (row % 2) * 5, PW, 10):
            p.fill(p.box(x, y, x + 8, y + 4), 0.40 + 0.04 * ((x * 7 + row * 3) % 3))
    pole(p, 108, 331, 118, 3, 0.15)                                  # a gas lantern
    p.fill(p.box(104, 203, 115, 214), 0.2)
    p.fill(p.box(106, 205, 113, 212), 0.74)
    p.fill(p.poly([(102, 203), (117, 203), (110, 196)]), 0.15)
    # carried down and set on the pavement
    p.shade(p.box(158, 298, 238, 302), 0.25)
    p.fill(p.poly([(160, 300), (164, 256), (182, 256), (184, 300)]), 0.24)      # a mirror against the wall
    p.fill(p.poly([(165, 296), (168, 261), (179, 261), (180, 296)]), 0.74)
    p.fill(p.box(188, 284, 208, 300), 0.42)                                     # a crate
    p.fill(p.box(188, 284, 208, 286), 0.56)
    p.fill(p.box(197, 286, 198, 300), 0.34)
    p.fill(p.box(210, 278, 234, 300), 0.27)                                     # a suitcase
    p.fill(p.box(210, 278, 234, 280), 0.42)
    p.fill(p.box(219, 274, 225, 278), 0.2)
    p.fill(p.box(213, 286, 215, 292) | p.box(229, 286, 231, 292), 0.6)
    p.fill(p.box(288, 290, 300, 300), 0.5)                                       # a bucket, a bundle
    p.fill(p.box(288, 290, 300, 291), 0.66)
    p.fill(p.ell(312, 296, 9, 6), 0.6)
    # the handcart at the kerb, loaded
    cx, by = 300, 334
    p.shade(p.ell(cx + 4, by + 25, 66, 5), 0.3)
    wheel(p, cx - 22, by + 12, 12, 0.13)
    wheel(p, cx + 26, by + 12, 12, 0.13)
    p.fill(p.box(cx - 46, by, cx + 50, by + 4), 0.2)
    p.fill(p.line([(cx + 50, by + 2), (cx + 92, by + 22)], 2), 0.2)             # the shafts rest on the ground
    p.fill(p.box(cx - 42, by - 26, cx + 28, by), 0.31)                          # a wardrobe on its side
    p.fill(p.box(cx - 42, by - 26, cx + 28, by - 24), 0.46)
    p.fill(p.box(cx - 8, by - 24, cx - 7, by), 0.2)
    p.fill(p.box(cx + 28, by - 16, cx + 46, by), 0.42)                          # crates
    p.fill(p.box(cx + 28, by - 16, cx + 46, by - 14), 0.56)
    p.fill(p.box(cx - 32, by - 40, cx - 8, by - 26), 0.4)
    p.fill(p.box(cx - 32, by - 40, cx - 8, by - 38), 0.54)
    p.fill(p.box(cx + 2, by - 30, cx + 22, by - 26), 0.2)                       # a chair, legs up
    p.fill(p.box(cx + 3, by - 46, cx + 5, by - 30) | p.box(cx + 19, by - 46, cx + 21, by - 30), 0.2)
    p.fill(p.box(cx + 3, by - 40, cx + 21, by - 38), 0.2)
    p.fill(p.box(cx - 48, by - 47, cx - 4, by - 41), 0.6)                       # a rolled carpet
    p.fill(p.ell(cx - 48, by - 44, 3, 3.5), 0.34)
    p.fill(p.box(cx - 30, by - 47, cx - 29, by) | p.box(cx + 14, by - 46, cx + 15, by), 0.66)   # the rope
    p.shade(A, np.clip((p.yy - 210) / 520.0, 0, 1) * 0.3)
    return p


def chronicle() -> Plate:
    p = Plate(v=0.25)
    A = p.all()
    p.tex(A, 0.04, 50, 51, sx=7.0)
    p.tex(A, 0.015, 5, 52, sx=12.0)
    p.fill(p.box(70, 14, 372, 356), 0.17)                            # the blotting pad
    p.fill(p.box(70, 14, 372, 16) | p.box(70, 14, 72, 356), 0.26)
    for cx, cy in ((70, 14), (350, 14), (70, 334), (350, 334)):
        p.fill(p.box(cx, cy, cx + 22, cy + 22), 0.11)
    # a plan at the right: blocks along an axis, some of them hatched
    plan = p.poly([(352, 40), (PW + 4, 28), (PW + 4, 330), (366, 342)])
    p.shade(p.poly([(357, 46), (PW + 4, 34), (PW + 4, 337), (371, 349)]) & ~plan, 0.3)
    p.fill(plan, 0.78)
    for i in range(7):
        y0 = 58 + i * 38
        for bx0, bx1 in ((382, 424), (448, 498)):
            inner = p.box(bx0 + 1, y0 + 1, bx1 - 1, y0 + 27)
            p.fill(p.box(bx0, y0, bx1, y0 + 28) & ~inner, 0.38)
            if (i * 3 + bx0) % 4 < 2:                                # hatched: to come down
                p.fill(((p.xx + p.yy) % 5 < 1) & inner, 0.45)
    p.fill(p.box(430, 44, 431, 336) | p.box(442, 44, 443, 336), 0.4)
    # the typed page of the chronicle
    px0, py0, pw, ph = 118, 24, 216, 304
    p.shade(p.box(px0 + 5, py0 + 6, px0 + pw + 6, py0 + ph + 7), 0.45)
    page = p.box(px0, py0, px0 + pw, py0 + ph)
    p.fill(page, 0.9)
    p.tex(page, 0.015, 40, 53)
    p.fill(p.text('CHRONIK', px0 + pw // 2, py0 + 20, 'l', 1, True), 0.2)
    p.fill(p.box(px0 + pw // 2 - 22, py0 + 32, px0 + pw // 2 + 22, py0 + 33), 0.3)
    p.fill(p.text('1941', px0 + pw - 34, py0 + 9, 's'), 0.36)
    y = py0 + 46
    for para, n in enumerate((5, 7, 4, 6, 5)):
        if para == 1:
            p.fill(p.text('AUGUST', px0 + 18, y, 'l'), 0.22)
            y += 12
        greek(p, px0 + 18, y, px0 + pw - 18, n, 5, seed=60 + para, val=0.34, indent=10)
        y += n * 5 + 9
    for hy in (py0 + 110, py0 + 190):                                # punched for the file
        p.fill(p.ell(px0 + 8, hy, 2.5, 2.5), 0.2)
    p.glow(230, 150, 300, 250, 0.22)
    # pen, ink, a rubber stamp on its pad
    p.fill(p.poly([(86, 300), (92, 296), (190, 346), (186, 351)]), 0.12)
    p.fill(p.poly([(86, 300), (92, 296), (80, 290)]), 0.7)
    p.fill(p.box(24, 40, 58, 74), 0.1)
    p.fill(p.ell(41, 57, 9, 9), 0.2)
    p.fill(p.ell(41, 57, 5, 5), 0.06)
    p.fill(p.box(16, 250, 62, 300), 0.14)
    p.fill(p.box(20, 254, 58, 296), 0.2)
    p.fill(p.ell(40, 274, 11, 11), 0.34)
    p.fill(p.ell(40, 274, 6, 6), 0.5)
    p.dusk(240, 170, 300, 240, 0.55)
    return p


def room() -> Plate:
    p = Plate(v=0.5)
    bx0, bx1, by0, by1 = 104, 428, 66, 258
    vp = (266, 158)
    ceil_m = p.poly([(0, 0), (PW, 0), (bx1, by0), (bx0, by0)])
    floor_m = p.poly([(0, PH), (PW, PH), (bx1, by1), (bx0, by1)])
    left = p.poly([(0, 0), (bx0, by0), (bx0, by1), (0, PH)])
    right = p.poly([(PW, 0), (bx1, by0), (bx1, by1), (PW, PH)])
    p.fill(ceil_m, 0.72)
    p.fill(floor_m, 0.36)
    p.fill(left, 0.47)
    p.fill(right, 0.38)
    p.fill(p.box(bx0, by0, bx1, by1), 0.53)
    p.tex(floor_m, 0.03, 30, 61, sy=5.0)
    for x in range(bx0 + 5, bx1, 11):                                # wallpaper in narrow stripes
        p.fill(p.box(x, by0 + 7, x + 1, by1 - 13), 0.49)
    p.fill(p.box(bx0, by0, bx1, by0 + 6), 0.66)
    p.fill(p.box(bx0, by0 + 6, bx1, by0 + 7), 0.42)
    p.fill(p.box(bx0, by1 - 13, bx1, by1), 0.3)
    p.fill(p.box(bx0, by1 - 13, bx1, by1 - 12), 0.42)
    p.fill(p.poly([(0, PH), (bx0, by1), (bx0, by1 - 13), (0, PH - 26)]), 0.27)
    p.fill(p.poly([(PW, PH), (bx1, by1), (bx1, by1 - 13), (PW, PH - 26)]), 0.24)
    for k in range(-16, 17):                                         # floorboards toward the vanishing point
        xb = 256 + k * 44
        xt = vp[0] + (xb - vp[0]) * (by1 - vp[1]) / float(PH - vp[1])
        p.fill(p.line([(xb, PH), (xt, by1)]) & floor_m, 0.28)
    # where things stood and hung the paper kept its colour: a wardrobe, three pictures
    p.fill(p.box(126, 116, 204, by1 - 13), 0.62)
    for gx, gy, gw, gh in ((228, 104, 34, 44), (272, 114, 24, 30), (306, 100, 30, 40)):
        p.fill(p.box(gx, gy, gx + gw, gy + gh), 0.62)
        p.fill(p.box(gx + gw // 2, gy - 7, gx + gw // 2 + 1, gy - 4), 0.2)
    p.shade(p.poly([(160, 276), (372, 276), (424, 344), (104, 344)]) & floor_m, 0.2)   # where the carpet lay
    # the open door to the corridor
    p.fill(p.box(350, 108, 410, by1), 0.68)
    p.fill(p.box(355, 113, 405, by1), 0.07)
    p.fill(p.box(374, 150, 384, 184), 0.46)
    p.fill(p.box(378, 150, 379, 184) | p.box(374, 166, 384, 167), 0.2)
    p.fill(p.poly([(405, 113), (440, 100), (440, 274), (405, by1)]), 0.45)
    p.fill(p.poly([(409, 122), (436, 112), (436, 180), (409, 184)]), 0.4)
    p.fill(p.poly([(409, 192), (436, 190), (436, 262), (409, 250)]), 0.4)
    p.fill(p.ell(411, 188, 2, 3), 0.8)
    # the window in the left wall, no curtains: the rod is bare
    p.fill(p.poly([(14, 36), (80, 70), (80, 234), (14, 272)]), 0.7)
    win = p.poly([(20, 44), (74, 74), (74, 228), (20, 262)])
    p.fill(win, 0.95)
    p.fill(p.line([(47, 59), (47, 245)], 2), 0.6)
    p.fill(p.line([(20, 150), (74, 150)], 2), 0.6)
    p.fill(p.line([(6, 22), (88, 62)], 2), 0.22)
    for rx, ry in ((22, 33), (44, 44), (66, 55)):
        p.fill(p.ell(rx, ry + 3, 2.5, 3.5) & ~p.ell(rx, ry + 3, 1.2, 2.2), 0.22)
    light = p.poly([(70, 300), (250, 280), (330, 322), (118, 360)]) & floor_m          # its light on the boards,
    p.lift(light, 0.34)
    p.shade(p.line([(160, 290), (224, 341)], 3) & light, 0.3)                          # crossed by the shadow of the bars
    p.shade(p.line([(94, 330), (290, 301)], 3) & light, 0.3)
    p.lift(p.poly([(bx0, 120), (bx0 + 16, 126), (bx0 + 16, 236), (bx0, by1 - 13)]), 0.18)
    # the ceiling rose and the bare wire
    p.fill(p.ell(266, 30, 24, 7), 0.62)
    p.fill(p.ell(266, 30, 12, 3.5), 0.52)
    p.fill(p.box(265, 30, 267, 64), 0.18)
    p.fill(p.box(262, 64, 270, 70), 0.2)
    # what was left: packing paper, a length of string
    p.fill(p.poly([(300, 300), (322, 296), (330, 306), (308, 312)]), 0.74)
    p.fill(p.poly([(210, 330), (226, 326), (232, 334), (216, 338)]), 0.7)
    p.fill(p.line(pg.bezier([(250, 318), (268, 308), (276, 326), (292, 316)], 24)), 0.72)
    p.dusk(230, 170, 330, 240, 0.4)
    return p
