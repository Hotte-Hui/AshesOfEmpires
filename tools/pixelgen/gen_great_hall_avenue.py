"""gen_great_hall_avenue -- figure atlas for the avenue staging between the street and the Great Hall's plaza.

Owner: hall (great_hall_3d).  Original, deterministic pixel art, berlin palette only (pg.PALETTES['berlin']).
Used by scripts/levels/hall/hall_avenue.gd (opt-in layer of the hall set; the parade's shot p8 looks down the
whole avenue from the roofs).  Massed figures are MultiMesh billboards drawn by
assets/architecture/great_hall/avenue/avenue_figures.gdshader, which picks per instance the LOD strip whose
figure height matches the projected size (1 texel = 1 screen pixel; only the largest strip may be enlarged).

Outputs (assets/architecture/great_hall/avenue/):
  avenue_figures.png + avenue_figures.json   13 LOD strips (figure heights 2..27 px), every strip holds the
      same slots side by side:
        march_back x4   infantry marching away from the camera (greatcoat, Y-straps, pack with blanket roll,
                        rifle slung, snow-dusted helmet; boots lifting)
        stand_back x3   infantry halted at attention, seen from behind (snow on helmets and shoulders; NCO)
        guard_side x2   cordon guard in profile, rifle at the order / slung (facing +x; flip for -x), breath
        honour x2       honour guard of the avenue in profile: pale parade greatcoat, white belt and cross strap,
                        white gloves, rifle shouldered with the bayonet fixed / at the order
        officer x2      officer seen from behind (peaked cap, long coat, hands behind the back) / from the side
        shovel x4       snow-clearing worker in profile: dig, lift, throw, recover (padded jacket, ear-flap cap,
                        pale blade with its load of snow)
        carry x2        worker carrying a barrier section on the shoulder / a coil of rope
        civ_back x12    civilians held back at the barriers, seen from behind: men in fedoras, caps and fur hats,
                        women in headscarves and berets, an old woman with a stick, children; bags, collars up
        civ_walk x4     man walking in profile (coat, hat) -- the stream towards the plaza
        civ_walk2 x4    woman walking in profile (headscarf, coat, bag)
        police x2       traffic policeman in a pale coat, arm raised / lowered (waving the lorries through)
        crow x3         crow in flight, wings up / level / down (shader height_m ~1.4 m: the wing span fills
                        the cell width)
        puff x4         vapour puff growing and dissolving (vents, exhausts; height_m ~3.6 m)
        flame x4        the fire in a pylon's bowl, flickering: ochre rim, glow body, pale core (warm ramp only;
                        shader height_m ~1.5 m, own self-lit material)
      Faces are never drawn: anonymous ranks and a crowd that is made to stand and watch.
  standard.png / standard_hist.png   18x30  the marching column's standards (three per colour party, on cross-bar
      poles; read from p8's roof 250-800 m away).  TECHNICAL_ARCHITECTURE section 12.4: the neutral file shows the
      regime's fictional Reichssiegel (black disc, white pillar) on silver-grey cloth with a dark border and fringe
      -- pale, so the colour parties stand out over the dark blocks; the _hist twin (picked by Symbols.pick) is the
      same standard with the real insignia (terracotta cloth, white disc, black swastika on point), drawn with the
      helpers of gen_great_hall_symbols.py.
  Rendering: shapes are rasterised 8x supersampled and reduced by majority vote; every figure gets a one-step
  lighter top edge (snow and floodlight on helmets, hats and shoulders -- the silhouettes stay readable on the
  dark asphalt) and, from 12 px up, a dark outline.  Strokes never fall below one pixel from 8 px up.
Run:  py -3 -P tools/pixelgen/gen_great_hall_avenue.py [preview.png]
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'architecture', 'great_hall', 'avenue')
B = pg.PALETTES['berlin']
LODS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 17, 21, 27]
SS = 8
OUTLINE = B['night'][0]


def c(r, i):
    return B[r][i]


# the ramp order inside every ramp is dark -> light; lighter(col) = the next step of the same ramp
_RAMP_OF = {}
for _r, _cols in B.items():
    for _i, _h in enumerate(_cols):
        _RAMP_OF.setdefault(_h, (_r, _i))


def lighter(col, k=1):
    r, i = _RAMP_OF[col]
    return B[r][min(i + k, len(B[r]) - 1)]


# ----------------------------------------------------------------------------------------------- shapes
# Figure units: x right, y up, feet centre at (0, 0), adult height 1.0 (= 1.8 m).
# ('poly', col, [(x, y), ...]) | ('ell', col, (cx, cy, rx, ry)) | ('line', col, (x0, y0, x1, y1, width))
def P(col, pts):
    return ('poly', col, pts)


def E(col, cx, cy, rx, ry):
    return ('ell', col, (cx, cy, rx, ry))


def L(col, x0, y0, x1, y1, w):
    return ('line', col, (x0, y0, x1, y1, w))


def R(col, x0, y0, x1, y1):
    return P(col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def _legs_back(lift=(0.0, 0.0), top=0.3, gap=0.022, w=0.064, col=None, boot=None, boot_h=0.075):
    col = col or c('night', 2)
    boot = boot or c('night', 1)
    sh = []
    for sx, up in ((-1.0, lift[0]), (1.0, lift[1])):
        xa, xb = sx * gap, sx * (gap + w)
        lo, hi = min(xa, xb), max(xa, xb)
        sh.append(P(col, [(lo, up + boot_h * 0.8), (hi, up + boot_h * 0.8), (hi - sx * 0.004, top), (lo, top)]))
        sh.append(P(boot, [(lo - 0.006, up), (hi + 0.006, up), (hi + 0.004, up + boot_h), (lo - 0.004, up + boot_h)]))
    return sh


def _coat_back(top, hem, sw, hw, coat, dark, lit=None):
    """Coat body seen from behind: shoulders `sw` wide at `top`, flaring to `hw` at the hem, the right half in
    shadow, a lit seam on the left."""
    sh = [P(coat, [(-sw, top), (sw, top), (sw + 0.03, top - 0.1), (hw, hem), (-hw, hem), (-sw - 0.03, top - 0.1)]),
          P(dark, [(0.04, top), (sw, top), (sw + 0.03, top - 0.1), (hw, hem), (0.055, hem)])]
    if lit:
        sh.append(P(lit, [(-sw, top), (-sw + 0.045, top), (-hw + 0.045, hem), (-hw, hem), (-sw - 0.03, top - 0.1)]))
    return sh


def _sleeves_back(top, low, sw, col, hand=None, swing=(0.0, 0.0)):
    sh = []
    for sx, dx in ((-1.0, swing[0]), (1.0, swing[1])):
        x0 = sx * (sw - 0.005)
        x1 = sx * (sw + 0.04)
        sh.append(P(col, [(x0, top - 0.02), (x1, top - 0.06), (x1 + dx, low), (x0 + dx * 0.6, low + 0.02)]))
        if hand:
            sh.append(E(hand, sx * (sw + 0.018) + dx, low - 0.02, 0.026, 0.03))
    return sh


def _helmet_back(hy, col, rim, snow=True):
    sh = [R(c('stone', 0), -0.032, hy - 0.1, 0.032, hy - 0.04),                          # nape
          E(col, 0.0, hy, 0.09, 0.066),
          P(col, [(-0.108, hy - 0.04), (0.108, hy - 0.04), (0.094, hy - 0.004), (-0.094, hy - 0.004)]),
          E(rim, -0.028, hy + 0.03, 0.05, 0.026)]
    if snow:
        sh.append(E(c('snow', 3), -0.01, hy + 0.05, 0.058, 0.018))
    return sh


def soldier_back(lift=(0.0, 0.0), bob=0.0, swing=(0.0, 0.0), pack=True, snow=True, nco=False):
    """Infantryman seen from behind: greatcoat, Y-straps, pack with a blanket roll, rifle slung on the right."""
    coat, dark, lit = c('steel', 2), c('steel', 1), c('steel', 3)
    sh = _legs_back(lift)
    top = 0.795 + bob
    sh += _coat_back(top, 0.27 + bob * 0.5, 0.12, 0.15, coat, dark, lit)
    sh.append(L(c('steel', 1), 0.0, 0.27 + bob, 0.0, 0.43 + bob, 0.018))                 # coat vent
    sh += _sleeves_back(top, 0.47 + bob, 0.12, c('steel', 1), c('night', 3), swing)
    sh.append(R(c('night', 2), -0.135, 0.495 + bob, 0.135, 0.53 + bob))                # belt
    for sx in (-1.0, 1.0):                                                               # Y-straps
        sh.append(L(c('night', 3), sx * 0.06, 0.53 + bob, sx * 0.075, top - 0.01, 0.02))
    if pack and not nco:
        sh.append(R(c('steel', 1), -0.08, 0.57 + bob, 0.08, 0.72 + bob))
        sh.append(R(c('steel', 0), 0.035, 0.57 + bob, 0.08, 0.72 + bob))
        sh.append(E(c('stone', 2), 0.0, 0.745 + bob, 0.115, 0.03))                       # blanket roll
        sh.append(R(c('steel', 3), 0.03, 0.43 + bob, 0.1, 0.495 + bob))                  # mess tin
    else:
        sh.append(R(c('stone', 1), -0.12, 0.43 + bob, -0.05, 0.495 + bob))               # map case (NCO)
    # rifle slung on the right shoulder, muzzle above the helmet
    sh.append(L(c('stone', 0), 0.07, 0.42 + bob, 0.09, 0.56 + bob, 0.045))
    sh.append(L(c('night', 1), 0.085, 0.5 + bob, 0.135, 1.0 + bob, 0.026))
    sh.append(R(c('steel', 3), -0.07, top - 0.01, 0.07, top + 0.02))                    # collar
    sh += _helmet_back(0.895 + bob, c('steel', 2), c('steel', 4), snow=snow)
    if snow:
        sh.append(P(c('snow', 2), [(-0.12, top + 0.005), (-0.07, top + 0.005), (-0.08, top - 0.02),
                                   (-0.125, top - 0.025)]))
    return sh


def march_back(f):
    """Marching away from the camera, 4 frames (left boot up, pass, right boot up, pass)."""
    lift = [(0.07, 0.0), (0.02, 0.0), (0.0, 0.07), (0.0, 0.02)][f]
    bob = [0.0, 0.012, 0.0, 0.012][f]
    sw = [(0.03, 0.0), (0.0, 0.0), (-0.03, 0.0), (0.0, 0.0)][f]
    return soldier_back(lift, bob, sw)


def stand_back(v):
    """Halted at attention, seen from behind; v=1 more snow on the shoulders, v=2 an NCO without a pack."""
    sh = soldier_back(snow=True, nco=(v == 2))
    if v == 1:
        sh.append(P(c('snow', 3), [(-0.125, 0.8), (-0.03, 0.8), (-0.04, 0.78), (-0.125, 0.775)]))
        sh.append(P(c('snow', 2), [(0.04, 0.8), (0.12, 0.8), (0.12, 0.78), (0.05, 0.785)]))
    return sh


def _head_profile(hx_, hy, helmet=True, col=None, rim=None, face=None):
    col = col or c('steel', 2)
    rim = rim or c('steel', 4)
    face = face or c('stone', 1)
    sh = [P(c('stone', 0), [(hx_ - 0.04, hy - 0.1), (hx_ + 0.03, hy - 0.1), (hx_ + 0.035, hy - 0.04),
                            (hx_ - 0.04, hy - 0.04)]),
          E(face, hx_ + 0.03, hy - 0.025, 0.04, 0.045)]                                  # shadowed face
    if helmet:
        sh += [E(col, hx_ - 0.005, hy, 0.088, 0.062),
               P(col, [(hx_ - 0.115, hy - 0.04), (hx_ + 0.075, hy - 0.035), (hx_ + 0.08, hy - 0.005),
                       (hx_ - 0.1, hy - 0.0)]),
               E(rim, hx_ - 0.03, hy + 0.032, 0.045, 0.022),
               E(c('snow', 3), hx_ - 0.02, hy + 0.052, 0.045, 0.014)]
    return sh


def guard_side(v):
    """Cordon guard in profile facing +x, feet apart (stand-at-ease); v=0 rifle at the order (breath in the cold),
    v=1 slung."""
    coat, dark, lit = c('steel', 2), c('steel', 1), c('steel', 3)
    sh = [P(c('night', 2), [(-0.09, 0.07), (-0.035, 0.07), (-0.02, 0.3), (-0.07, 0.3)]),
          P(c('night', 2), [(0.03, 0.07), (0.085, 0.07), (0.07, 0.3), (0.02, 0.3)]),
          P(c('night', 1), [(-0.1, 0.0), (-0.025, 0.0), (-0.03, 0.08), (-0.095, 0.08)]),
          P(c('night', 1), [(0.03, 0.0), (0.12, 0.0), (0.09, 0.08), (0.03, 0.08)])]
    sh.append(P(coat, [(-0.07, 0.8), (0.07, 0.8), (0.1, 0.62), (0.11, 0.26), (-0.14, 0.26), (-0.11, 0.6)]))
    sh.append(P(dark, [(-0.07, 0.8), (-0.02, 0.8), (-0.04, 0.6), (-0.08, 0.26), (-0.14, 0.26), (-0.11, 0.6)]))
    sh.append(P(lit, [(0.04, 0.8), (0.07, 0.8), (0.1, 0.62), (0.105, 0.3), (0.08, 0.3), (0.07, 0.6)]))
    sh.append(R(c('night', 2), -0.115, 0.5, 0.105, 0.535))
    sh.append(R(c('night', 3), 0.05, 0.535, 0.1, 0.59))                                  # ammunition pouch
    sh.append(P(c('steel', 1), [(-0.135, 0.56), (-0.07, 0.56), (-0.07, 0.75), (-0.135, 0.73)]))   # pack
    sh.append(E(c('stone', 2), -0.1, 0.765, 0.045, 0.028))                                 # blanket roll
    if v == 0:
        sh.append(L(c('night', 1), 0.15, 0.0, 0.15, 0.8, 0.03))                          # rifle at the order
        sh.append(L(dark, 0.0, 0.77, 0.13, 0.52, 0.055))                                   # arm to the rifle
        sh.append(E(c('night', 3), 0.14, 0.52, 0.03, 0.03))
        sh.append(E(c('snow', 1), 0.15, 0.86, 0.04, 0.025))                                # breath
    else:
        sh.append(L(c('night', 1), -0.06, 0.45, 0.06, 0.98, 0.028))                      # slung, muzzle up
        sh.append(L(dark, 0.0, 0.77, 0.02, 0.47, 0.055))
    sh.append(R(lit, -0.02, 0.785, 0.06, 0.815))                                           # collar
    sh += _head_profile(0.0, 0.9)
    return sh


def honour(v):
    """Honour guard along the avenue's axis, in profile facing +x, at attention: pale parade greatcoat, white belt
    and cross strap, white gloves, polished boots; v=0 rifle shouldered, bayonet fixed; v=1 rifle at the order."""
    coat, dark, lit = c('steel', 4), c('steel', 3), c('steel', 5)
    white = c('snow', 4)
    sh = [P(c('night', 1), [(-0.07, 0.0), (0.0, 0.0), (0.0, 0.3), (-0.06, 0.3)]),
          P(c('night', 0), [(-0.02, 0.0), (0.07, 0.0), (0.05, 0.3), (-0.02, 0.3)]),
          R(c('steel', 3), 0.035, 0.015, 0.06, 0.035)]                                     # toe shine
    sh.append(P(coat, [(-0.075, 0.81), (0.065, 0.81), (0.095, 0.62), (0.1, 0.27), (-0.12, 0.27), (-0.1, 0.6)]))
    sh.append(P(dark, [(-0.075, 0.81), (-0.025, 0.81), (-0.045, 0.6), (-0.08, 0.27), (-0.12, 0.27),
                       (-0.1, 0.6)]))
    sh.append(P(lit, [(0.04, 0.81), (0.065, 0.81), (0.095, 0.62), (0.098, 0.32), (0.08, 0.32), (0.07, 0.6)]))
    sh.append(R(white, -0.105, 0.5, 0.1, 0.535))                                           # parade belt
    sh.append(L(white, -0.06, 0.8, 0.07, 0.53, 0.022))                                     # cross strap
    sh.append(R(c('steel', 5), -0.01, 0.5, 0.025, 0.535))                                  # buckle
    if v == 0:
        sh.append(L(c('stone', 1), -0.02, 0.6, 0.02, 0.8, 0.05))                          # butt in the hand
        sh.append(L(c('night', 1), 0.01, 0.75, 0.055, 1.02, 0.026))
        sh.append(L(white, 0.055, 1.02, 0.065, 1.09, 0.016))                               # bayonet
        sh.append(L(dark, 0.0, 0.79, -0.01, 0.6, 0.055))
        sh.append(E(white, -0.01, 0.585, 0.03, 0.03))                                      # white glove
    else:
        sh.append(L(c('night', 1), 0.15, 0.0, 0.15, 0.82, 0.028))
        sh.append(L(white, 0.15, 0.82, 0.15, 0.9, 0.016))
        sh.append(L(dark, 0.0, 0.78, 0.13, 0.52, 0.055))
        sh.append(E(white, 0.14, 0.52, 0.03, 0.03))
    sh.append(R(lit, -0.02, 0.79, 0.06, 0.825))                                            # collar
    sh += _head_profile(0.0, 0.905, col=c('steel', 3), rim=c('steel', 5), face=c('stone', 2))
    return sh


def officer(v):
    """v=0 from behind (hands behind the back), v=1 in profile facing +x."""
    coat, dark, lit = c('steel', 3), c('steel', 2), c('steel', 4)
    boots = c('night', 0)
    if v == 0:
        sh = _legs_back(top=0.3, col=boots, boot=boots, boot_h=0.3)
        sh += _coat_back(0.82, 0.2, 0.12, 0.165, coat, dark, lit)
        sh.append(L(dark, 0.0, 0.2, 0.0, 0.4, 0.02))
        sh += _sleeves_back(0.82, 0.54, 0.12, dark)
        sh.append(R(c('night', 2), -0.135, 0.52, 0.135, 0.55))
        sh.append(E(c('night', 3), 0.0, 0.5, 0.065, 0.04))                                 # gloved hands behind
        sh.append(R(lit, -0.075, 0.81, 0.075, 0.845))                                      # collar
        sh.append(R(c('stone', 0), -0.035, 0.84, 0.035, 0.88))
        sh.append(E(c('stone', 0), 0.0, 0.905, 0.058, 0.055))
        sh.append(P(c('steel', 1), [(-0.07, 0.925), (0.07, 0.925), (0.1, 0.99), (-0.1, 0.99)]))   # cap crown
        sh.append(E(c('steel', 1), 0.0, 0.995, 0.1, 0.028))
        sh.append(R(c('steel', 4), -0.07, 0.925, 0.07, 0.945))                             # cap band
        sh.append(E(c('snow', 3), -0.02, 1.012, 0.06, 0.012))
    else:
        sh = [P(boots, [(-0.08, 0.0), (0.0, 0.0), (0.0, 0.3), (-0.07, 0.3)]),
              P(boots, [(0.0, 0.0), (0.1, 0.0), (0.06, 0.3), (0.0, 0.3)])]
        sh.append(P(coat, [(-0.075, 0.82), (0.07, 0.82), (0.1, 0.6), (0.12, 0.2), (-0.15, 0.2), (-0.11, 0.6)]))
        sh.append(P(dark, [(-0.075, 0.82), (-0.02, 0.82), (-0.05, 0.6), (-0.1, 0.2), (-0.15, 0.2), (-0.11, 0.6)]))
        sh.append(P(lit, [(0.045, 0.82), (0.07, 0.82), (0.1, 0.6), (0.115, 0.25), (0.09, 0.25), (0.075, 0.6)]))
        sh.append(R(c('night', 2), -0.115, 0.52, 0.105, 0.55))
        sh.append(L(dark, 0.0, 0.79, 0.04, 0.5, 0.055))
        sh.append(R(c('stone', 1), -0.14, 0.4, -0.08, 0.5))                               # map case
        sh.append(E(c('stone', 1), 0.03, 0.88, 0.05, 0.055))
        sh.append(P(c('steel', 1), [(-0.07, 0.92), (0.06, 0.92), (0.085, 0.985), (-0.06, 0.99)]))
        sh.append(P(c('night', 1), [(0.03, 0.92), (0.13, 0.915), (0.12, 0.94), (0.03, 0.945)]))     # peak
        sh.append(R(c('steel', 4), -0.065, 0.92, 0.06, 0.94))
    return sh


def _limb(sh, col, a, b, w):
    sh.append(L(col, a[0], a[1], b[0], b[1], w))


def shovel(f):
    """Snow-clearing worker in profile facing +x: 0 dig, 1 lift, 2 throw, 3 recover.  Municipal padded jacket
    (light, so the gang reads on the dark asphalt), dark trousers, felt boots, ear-flap cap, pale steel blade."""
    jak, jd, jl = c('stone', 3), c('stone', 2), c('stone', 4)
    tr, boot = c('night', 2), c('stone', 0)
    bend = math.radians([52.0, 36.0, 14.0, 26.0][f])
    hip = (-0.03, 0.42)
    knee_f = (0.05, 0.22) if f in (0, 1) else (0.04, 0.2)
    knee_b = (-0.08, 0.22)
    foot_f, foot_b = (0.1, 0.0), (-0.12, 0.0)
    sh = []
    _limb(sh, tr, hip, knee_b, 0.075)
    _limb(sh, tr, knee_b, foot_b, 0.07)
    _limb(sh, c('night', 3), hip, knee_f, 0.075)
    _limb(sh, c('night', 3), knee_f, foot_f, 0.07)
    for fx in (foot_b[0], foot_f[0]):
        sh.append(R(boot, fx - 0.05, 0.0, fx + 0.06, 0.06))
    sho = (hip[0] + 0.36 * math.sin(bend), hip[1] + 0.36 * math.cos(bend))
    ux, uy = math.sin(bend), math.cos(bend)
    nx, ny = uy, -ux                                    # forward normal of the spine
    wb, wf = 0.1, 0.085
    sh.append(P(jak, [(hip[0] - nx * wb, hip[1] - ny * wb - 0.04), (hip[0] + nx * wf, hip[1] + ny * wf - 0.04),
                      (sho[0] + nx * wf, sho[1] + ny * wf), (sho[0] - nx * wb, sho[1] - ny * wb)]))
    sh.append(P(jd, [(hip[0] - nx * wb, hip[1] - ny * wb - 0.04), (hip[0] - nx * 0.02, hip[1] - ny * 0.02 - 0.04),
                     (sho[0] - nx * 0.02, sho[1] - ny * 0.02), (sho[0] - nx * wb, sho[1] - ny * wb)]))
    sh.append(L(jl, sho[0] + nx * 0.06, sho[1] + ny * 0.06, hip[0] + nx * 0.06, hip[1] + ny * 0.06 - 0.02, 0.025))
    sh.append(R(c('night', 3), hip[0] - 0.1, hip[1] - 0.06, hip[0] + 0.09, hip[1] - 0.03))   # belt
    head = (sho[0] + ux * 0.1 + nx * 0.03, sho[1] + uy * 0.1 + ny * 0.03)
    sh.append(E(c('stone', 1), head[0], head[1], 0.055, 0.058))
    sh.append(E(c('night', 3), head[0] - 0.012, head[1] + 0.03, 0.064, 0.04))            # ear-flap cap
    sh.append(R(c('night', 3), head[0] - 0.06, head[1] - 0.045, head[0] - 0.02, head[1] + 0.01))
    sh.append(E(c('snow', 3), head[0] - 0.02, head[1] + 0.06, 0.04, 0.012))
    # arms + shovel: back hand on the grip end, front hand down the shaft, blade
    poses = [((0.1, 0.3), (0.2, 0.17), (0.34, 0.03), 0.0),
             ((0.12, 0.44), (0.2, 0.37), (0.32, 0.3), 0.15),
             ((0.08, 0.66), (0.16, 0.7), (0.3, 0.78), 0.6),
             ((0.08, 0.42), (0.14, 0.32), (0.25, 0.12), 0.25)][f]
    hb, hf, bl, tilt = poses
    _limb(sh, jd, sho, hb, 0.06)
    _limb(sh, jak, sho, hf, 0.06)
    gx, gy = hb[0] - (hf[0] - hb[0]) * 0.5, hb[1] - (hf[1] - hb[1]) * 0.5
    sh.append(L(c('stone', 4), gx, gy, bl[0], bl[1], 0.026))                               # shaft
    ang = math.atan2(bl[1] - hf[1], bl[0] - hf[0])
    dx, dy = math.cos(ang) * 0.07, math.sin(ang) * 0.07
    px_, py_ = -math.sin(ang) * 0.045, math.cos(ang) * 0.045
    sh.append(P(c('steel', 5), [(bl[0] - px_, bl[1] - py_), (bl[0] + dx - px_, bl[1] + dy - py_),
                                (bl[0] + dx + px_, bl[1] + dy + py_), (bl[0] + px_, bl[1] + py_)]))
    for hp in (hb, hf):
        sh.append(E(c('night', 3), hp[0], hp[1], 0.028, 0.028))
    if f == 1:
        sh.append(E(c('snow', 4), bl[0] + 0.04, bl[1] + 0.045, 0.06, 0.03))
    if f == 2:
        sh.append(E(c('snow', 4), bl[0] + 0.1, bl[1] + 0.06, 0.05, 0.025))
        sh.append(E(c('snow', 3), bl[0] + 0.16, bl[1] + 0.02, 0.035, 0.02))
        sh.append(E(c('snow', 3), bl[0] + 0.2, bl[1] - 0.04, 0.025, 0.018))
    return sh


def carry(v):
    """Worker walking (profile, +x) with a barrier section on the shoulder (v=0) or a coil of rope (v=1)."""
    jak, jd = (c('ochre', 2), c('ochre', 1)) if v == 0 else (c('stone', 3), c('stone', 2))
    sh = []
    _limb(sh, c('night', 3), (-0.02, 0.38), (-0.1, 0.0), 0.075)
    _limb(sh, c('night', 2), (0.0, 0.38), (0.1, 0.0), 0.075)
    sh += [R(c('stone', 0), -0.15, 0.0, -0.05, 0.05), R(c('stone', 0), 0.06, 0.0, 0.16, 0.05),
           P(jak, [(-0.1, 0.34), (0.08, 0.34), (0.09, 0.76), (-0.07, 0.78)]),
           P(jd, [(-0.1, 0.34), (-0.03, 0.34), (-0.02, 0.77), (-0.07, 0.78)]),
           R(c('night', 3), -0.1, 0.4, 0.085, 0.44),
           E(c('stone', 1), 0.03, 0.86, 0.052, 0.06),
           E(c('night', 3), 0.01, 0.9, 0.065, 0.035),
           E(c('snow', 3), 0.0, 0.93, 0.045, 0.012)]
    if v == 0:
        sh.append(R(c('steel', 4), -0.36, 0.78, 0.3, 0.81))
        sh.append(R(c('steel', 4), -0.36, 0.69, 0.3, 0.715))
        for x in (-0.33, -0.15, 0.03, 0.27):
            sh.append(R(c('steel', 3), x - 0.012, 0.65, x + 0.012, 0.82))
        sh.append(R(c('snow', 3), -0.36, 0.81, 0.3, 0.825))
        sh.append(L(jd, 0.02, 0.74, 0.07, 0.8, 0.05))
    else:
        sh.append(E(c('stone', 4), 0.08, 0.56, 0.08, 0.08))
        sh.append(E(c('stone', 2), 0.08, 0.56, 0.04, 0.04))
        sh.append(L(jd, 0.0, 0.74, 0.07, 0.56, 0.055))
    return sh


# civilians held back at the barriers, seen from behind
#   coat, shade, lit, accent (scarf / collar / headscarf), head kind, hat colour, height, width, hem, legs,
#   extra (bag | stick | case | none), hunch
CIVIL = [
    (c('violet', 2), c('violet', 1), c('violet', 3), c('snow', 2), 'fedora', c('night', 2), 0.98, 1.0, 0.3,
     'trousers', 'none', 0.0),
    (c('stone', 2), c('stone', 1), c('stone', 3), c('ochre', 1), 'scarf', c('ochre', 1), 0.91, 0.95, 0.22,
     'stockings', 'bag', 0.01),
    (c('steel', 2), c('steel', 1), c('steel', 3), c('stone', 3), 'cap', c('night', 3), 0.96, 1.05, 0.4,
     'trousers', 'none', 0.0),
    (c('stone', 1), c('stone', 0), c('stone', 2), c('violet', 3), 'hat', c('night', 2), 0.93, 0.95, 0.24,
     'stockings', 'case', 0.0),
    (c('violet', 1), c('violet', 0), c('violet', 2), c('patina', 2), 'shawl', c('patina', 2), 0.86, 1.0, 0.18,
     'stockings', 'stick', 0.045),
    (c('night', 3), c('night', 2), c('violet', 2), c('snow', 1), 'fur', c('stone', 3), 0.99, 1.08, 0.3,
     'trousers', 'none', 0.0),
    (c('ochre', 0), c('stone', 0), c('ochre', 1), c('stone', 3), 'hood', c('stone', 2), 0.6, 0.82, 0.3,
     'trousers', 'none', 0.0),                                                                    # child
    (c('patina', 2), c('patina', 1), c('patina', 3), c('stone', 3), 'beret', c('violet', 2), 0.92, 0.95, 0.24,
     'stockings', 'bag', 0.0),
    (c('stone', 2), c('stone', 1), c('stone', 3), c('night', 3), 'bare', c('snow', 1), 0.95, 1.0, 0.32,
     'trousers', 'none', 0.03),                                                                   # old man
    (c('steel', 3), c('steel', 2), c('steel', 4), c('stone', 4), 'fur', c('stone', 4), 0.93, 0.98, 0.2,
     'stockings', 'none', 0.0),
    (c('stone', 1), c('stone', 0), c('stone', 2), c('snow', 2), 'hood', c('patina', 2), 0.68, 0.85, 0.3,
     'trousers', 'none', 0.0),                                                                    # child
    (c('violet', 2), c('violet', 1), c('violet', 3), c('stone', 2), 'cap', c('steel', 1), 0.97, 1.0, 0.36,
     'trousers', 'case', 0.0),
]


def _civ_head(kind, hcol, acc, hy, hw=1.0):
    sh = []
    if kind in ('scarf', 'shawl'):
        sh.append(E(hcol, 0.0, hy + 0.005, 0.068 * hw, 0.075))
        sh.append(P(hcol, [(-0.04, hy - 0.05), (0.04, hy - 0.05), (0.0, hy - 0.13)]))          # knot tail
        sh.append(E(lighter(hcol), -0.025, hy + 0.04, 0.035, 0.025))
        return sh
    sh.append(E(c('stone', 0) if kind != 'bare' else c('stone', 1), 0.0, hy - 0.035, 0.05, 0.04))   # nape
    hair = hcol if kind == 'bare' else c('night', 2)
    sh.append(E(hair, 0.0, hy, 0.058 * hw, 0.068))
    if kind == 'fedora':
        sh += [E(hcol, 0.0, hy + 0.035, 0.105, 0.024),
               P(hcol, [(-0.058, hy + 0.035), (0.058, hy + 0.035), (0.05, hy + 0.105), (-0.05, hy + 0.105)]),
               R(c('night', 1), -0.058, hy + 0.04, 0.058, hy + 0.058),
               E(c('snow', 3), -0.02, hy + 0.06, 0.09, 0.012)]
    elif kind == 'cap':
        sh += [E(hcol, 0.0, hy + 0.04, 0.07, 0.04), E(c('snow', 2), -0.015, hy + 0.07, 0.045, 0.012)]
    elif kind == 'hat':
        sh += [E(hcol, 0.0, hy + 0.045, 0.07, 0.045), E(acc, 0.0, hy + 0.02, 0.07, 0.014)]
    elif kind == 'beret':
        sh += [E(hcol, 0.01, hy + 0.05, 0.075, 0.03)]
    elif kind == 'fur':
        sh += [P(hcol, [(-0.068, hy + 0.0), (0.068, hy + 0.0), (0.07, hy + 0.1), (-0.07, hy + 0.1)]),
               E(hcol, 0.0, hy + 0.1, 0.07, 0.018), E(lighter(hcol), -0.03, hy + 0.06, 0.025, 0.035)]
    elif kind == 'hood':
        sh += [E(hcol, 0.0, hy + 0.015, 0.075, 0.08), E(lighter(hcol), -0.03, hy + 0.05, 0.03, 0.025)]
    return sh


def civ_back(v):
    coat, dark, lit, acc, head, hcol, h, w, hem, legs, extra, hunch = CIVIL[v]
    sh = []
    if legs == 'trousers':
        sh += _legs_back(top=hem + 0.04, gap=0.02 * w, w=0.06 * w, col=c('night', 2), boot=c('night', 1))
    else:                                                                           # thin stockinged legs
        sh += _legs_back(top=hem + 0.04, gap=0.03 * w, w=0.042 * w, col=c('stone', 1), boot=c('night', 1),
                         boot_h=0.05)
    top = 0.79 * h - hunch
    hem_y = hem * h
    sw, hw = 0.112 * w, (0.15 if legs == 'stockings' else 0.135) * w
    sh += _coat_back(top, hem_y, sw, hw, coat, dark, lit)
    sh += _sleeves_back(top, 0.45 * h, sw, dark, c('stone', 0) if extra != 'none' else None)
    sh.append(L(dark, 0.0, hem_y, 0.0, hem_y + 0.12 * h, 0.016))                          # coat seam
    if head not in ('scarf', 'shawl', 'hood'):
        sh.append(P(acc, [(-0.07 * w, top + 0.025), (0.07 * w, top + 0.025), (0.08 * w, top - 0.035),
                          (-0.08 * w, top - 0.035)]))                                        # collar / scarf
    if head == 'shawl':
        sh.append(P(hcol, [(-sw - 0.01, top), (sw + 0.01, top), (0.0, top - 0.22 * h)]))
    if extra == 'bag':
        sh.append(L(c('night', 3), sw + 0.02, top - 0.05, sw + 0.05, 0.47 * h, 0.014))
        sh.append(R(c('night', 3), sw + 0.01, 0.38 * h, sw + 0.09, 0.47 * h))
    elif extra == 'case':
        sh.append(R(c('night', 2), -sw - 0.1, 0.3 * h, -sw - 0.01, 0.4 * h))
    elif extra == 'stick':
        sh.append(L(c('stone', 2), sw + 0.06, 0.0, sw + 0.04, 0.44 * h, 0.022))
    sh += _civ_head(head, hcol, acc, top + 0.085 + hunch * 0.5, hw=w)
    return sh


def _walker(f, coat, dark, lit, head, hcol, legcol, bag=False, hem=0.3):
    legs = [((0.11, 0.0), (-0.1, 0.0)), ((0.035, 0.0), (-0.025, 0.045)), ((-0.1, 0.0), (0.11, 0.0)),
            ((-0.025, 0.045), (0.035, 0.0))][f]
    sh = []
    for (fx, fy), col in ((legs[1], c('night', 1)), (legs[0], legcol)):
        sh.append(L(col, 0.0, 0.36, fx, fy + 0.03, 0.062))
        sh.append(R(c('night', 1), fx - 0.04, fy, fx + 0.065, fy + 0.045))
    sh.append(P(coat, [(-0.07, 0.78), (0.07, 0.78), (0.1, 0.6), (0.12, hem), (-0.12, hem), (-0.1, 0.6)]))
    sh.append(P(dark, [(-0.07, 0.78), (-0.02, 0.78), (-0.05, 0.6), (-0.07, hem), (-0.12, hem), (-0.1, 0.6)]))
    sh.append(L(lit, 0.06, 0.76, 0.1, hem + 0.04, 0.022))
    sw = [0.045, 0.0, -0.045, 0.0][f]
    sh.append(L(dark, 0.0, 0.75, 0.02 + sw, 0.46, 0.055))
    if bag:
        sh.append(R(c('night', 3), -0.02 + sw, 0.36, 0.08 + sw, 0.46))
    sh.append(E(c('stone', 1), 0.035, 0.85, 0.048, 0.055))
    if head == 'hat':
        sh.append(E(c('night', 2), 0.0, 0.87, 0.052, 0.06))
        sh.append(E(hcol, 0.02, 0.9, 0.1, 0.02))
        sh.append(P(hcol, [(-0.035, 0.9), (0.075, 0.9), (0.065, 0.955), (-0.025, 0.955)]))
        sh.append(E(c('snow', 3), 0.02, 0.962, 0.05, 0.01))
    else:
        sh.append(E(hcol, -0.005, 0.87, 0.06, 0.07))
        sh.append(P(hcol, [(-0.06, 0.84), (-0.02, 0.84), (-0.07, 0.74)]))
        sh.append(E(lighter(hcol), -0.02, 0.91, 0.03, 0.022))
    sh.append(R(c('snow', 2) if head == 'hat' else c('stone', 3), -0.02, 0.765, 0.07, 0.795))
    return sh


def civ_walk(f):
    """Man (coat, hat) walking in profile facing +x, 4 frames."""
    return _walker(f, c('violet', 2), c('violet', 1), c('violet', 3), 'hat', c('night', 2), c('night', 2))


def civ_walk2(f):
    """Woman (headscarf, coat, bag) walking in profile facing +x, 4 frames."""
    return _walker(f, c('stone', 2), c('stone', 1), c('stone', 3), 'scarf', c('violet', 3), c('stone', 1),
                   bag=True, hem=0.24)


def police(f):
    """Traffic policeman (pale coat, white sleeves), facing the camera; f=0 arm raised, f=1 arm out."""
    coat, dark = c('snow', 2), c('snow', 1)
    sh = [P(c('night', 1), [(-0.07, 0.0), (-0.01, 0.0), (-0.01, 0.27), (-0.07, 0.27)]),
          P(c('night', 1), [(0.01, 0.0), (0.07, 0.0), (0.07, 0.27), (0.01, 0.27)]),
          P(coat, [(-0.12, 0.8), (0.12, 0.8), (0.15, 0.25), (-0.15, 0.25)]),
          P(dark, [(0.03, 0.8), (0.12, 0.8), (0.15, 0.25), (0.05, 0.25)]),
          R(c('night', 2), -0.14, 0.5, 0.14, 0.535),
          L(c('night', 2), -0.08, 0.78, 0.08, 0.535, 0.02),
          E(c('stone', 1), 0.0, 0.88, 0.058, 0.068),
          P(c('steel', 1), [(-0.065, 0.92), (0.065, 0.92), (0.06, 1.0), (-0.06, 1.0)]),
          E(c('snow', 4), 0.0, 1.0, 0.065, 0.018)]
    if f == 0:
        sh.append(L(c('snow', 4), 0.12, 0.76, 0.2, 1.04, 0.06))
    else:
        sh.append(L(c('snow', 4), 0.12, 0.76, 0.34, 0.72, 0.06))
    sh.append(L(c('snow', 3), -0.12, 0.76, -0.14, 0.48, 0.055))
    return sh


def crow(f):
    """Crow in flight seen from the side and a little below, heading +x; the wing span fills the cell width
    (shader height_m ~1.4 m).  Frames: wings up, level, down."""
    body, wing, tip = c('night', 0), c('night', 1), c('night', 2)
    y = 0.5
    sh = [E(body, 0.0, y, 0.09, 0.05), E(body, 0.1, y + 0.014, 0.04, 0.036),                 # body, head
          P(c('stone', 0), [(0.125, y + 0.012), (0.165, y + 0.004), (0.125, y - 0.002)]),     # beak
          P(body, [(-0.075, y + 0.015), (-0.17, y + 0.035), (-0.17, y - 0.03), (-0.075, y - 0.012)])]   # tail
    if f == 0:
        wings = [[(-0.04, y + 0.02), (0.04, y + 0.02), (-0.14, y + 0.2), (-0.3, y + 0.3), (-0.2, y + 0.19)],
                 [(-0.02, y + 0.02), (0.05, y + 0.02), (0.2, y + 0.17), (0.36, y + 0.26), (0.18, y + 0.21)]]
    elif f == 1:
        wings = [[(-0.04, y + 0.03), (0.04, y + 0.03), (-0.2, y + 0.06), (-0.38, y + 0.01), (-0.2, y - 0.03)],
                 [(-0.02, y + 0.03), (0.05, y + 0.03), (0.22, y + 0.065), (0.39, y + 0.02), (0.2, y - 0.025)]]
    else:
        wings = [[(-0.04, y + 0.0), (0.04, y + 0.0), (-0.12, y - 0.13), (-0.27, y - 0.24), (-0.18, y - 0.1)],
                 [(-0.02, y + 0.0), (0.05, y + 0.0), (0.17, y - 0.12), (0.33, y - 0.22), (0.2, y - 0.08)]]
    for wpts in wings:
        sh.append(P(wing, wpts))
        sh.append(P(tip, [wpts[2], wpts[3], wpts[4]]))
    return sh


def puff(k):
    """Vapour puff growing and dissolving: low-contrast grey (it is breath and steam in the cold, not smoke)."""
    r = [0.12, 0.18, 0.24, 0.28][k]
    body = [c('snow', 2), c('snow', 2), c('snow', 1), c('snow', 0)][k]
    hi = [c('snow', 3), c('snow', 3), c('snow', 2), c('snow', 1)][k]
    lo = [c('snow', 1), c('snow', 1), c('snow', 0), c('violet', 3)][k]
    y = 0.1 + k * 0.08
    return [E(body, 0.0, y + r, r, r * 0.8), E(body, r * 0.55, y + r * 1.35, r * 0.6, r * 0.5),
            E(body, -r * 0.5, y + r * 0.6, r * 0.55, r * 0.45),
            E(hi, -r * 0.25, y + r * 1.3, r * 0.5, r * 0.36), E(lo, r * 0.3, y + r * 0.45, r * 0.55, r * 0.3)]


def flame(f):
    """Fire burning in a pylon's bowl, 4 flicker frames.  Warm ramp only: ochre rim, glow body, pale core low in
    the bowl.  Round 13: from 6 px up a cell is drawn by the pixel fire kit (kit_flame: designed tongues, merged
    colour bands, hard pixels at every LOD); these shapes only feed the one-pixel columns of the far LODs."""
    rim, body, core, hot = c('ochre', 4), c('glow', 1), c('glow', 3), c('glow', 4)
    lean = [0.0, 0.06, -0.04, 0.03][f]
    tip = [0.96, 0.84, 1.0, 0.9][f]
    tl, tr = [(0.56, 0.66), (0.7, 0.5), (0.5, 0.7), (0.64, 0.58)][f]
    sh = [P(rim, [(-0.21, 0.0), (0.21, 0.0), (0.23, 0.16), (0.16, tr * 0.72), (0.12 + lean, tr), (0.06 + lean * 0.6, 0.44),
                  (lean, tip), (-0.06 + lean * 0.4, 0.46), (-0.13 + lean, tl), (-0.17, tl * 0.7), (-0.23, 0.16)]),
          P(body, [(-0.15, 0.0), (0.15, 0.0), (0.16, 0.15), (0.07 + lean * 0.6, 0.46), (lean * 0.8, tip - 0.22),
                   (-0.08 + lean * 0.4, 0.42), (-0.16, 0.14)]),
          E(core, 0.0, 0.15, 0.11, 0.13),
          E(hot, 0.0, 0.08, 0.07, 0.06)]
    sh = _Frames(sh)
    sh.frame = f
    return sh


class _Frames(list):
    """a slot's shape list that also knows which frame of its loop it is"""
    frame = 0


def kit_flame(f, cw, ch, h):
    """Frame f (of 4) of the bowl's fire for a LOD cell: the pixel fire kit's tongues (pixel_fire_bake.flames)
    in the avenue's warm ramp -- a main tongue with forks over a bed of embers, standing on the cell's foot
    line.  Hard pixels, exact palette colours."""
    import pixel_fire_bake as PFB
    cols = (c('ochre', 4), c('glow', 1), c('glow', 3), c('glow', 4))
    fr = PFB.flames(cw, h + 1, 4, [(cw / 2.0, 0.26 * cw, 1.0)], 571 + h, 1.0, base=0.25,
                    cols=cols if h >= 14 else cols[1:], tick=7.5, cool=c('ochre', 3))[f]
    out = np.zeros((ch, cw, 4), np.uint8)
    out[:h + 1] = fr
    return out


SLOTS = ([('march_back', march_back(f)) for f in range(4)] + [('stand_back', stand_back(v)) for v in range(3)]
         + [('guard_side', guard_side(v)) for v in range(2)] + [('honour', honour(v)) for v in range(2)]
         + [('officer', officer(v)) for v in range(2)]
         + [('shovel', shovel(f)) for f in range(4)] + [('carry', carry(v)) for v in range(2)]
         + [('civ_back', civ_back(v)) for v in range(len(CIVIL))] + [('civ_walk', civ_walk(f)) for f in range(4)]
         + [('civ_walk2', civ_walk2(f)) for f in range(4)]
         + [('police', police(f)) for f in range(2)] + [('crow', crow(f)) for f in range(3)]
         + [('puff', puff(k)) for k in range(4)] + [('flame', flame(f)) for f in range(4)])
SOFT = {'puff', 'flame'}
DARK = {'crow'}                     # no lit top edge, no outline: a black shape against the sky


# --------------------------------------------------------------------------------------------- rendering
def cell_size(h):
    return max(4, int(round(0.8 * h)) + 3), h + 2


def _draw(sh, cw, ch, h, ss, labels, min_w=0.0):
    im = Image.new('L', (cw * ss, ch * ss), 0)
    dr = ImageDraw.Draw(im)
    ax, ay = cw // 2, h + 1

    def Q(x, y):
        return ((ax + x * h) * ss, (ay - y * h) * ss)
    for kind, col, prm in sh:
        lab = labels.setdefault(col, len(labels) + 1)
        if kind == 'poly':
            dr.polygon([Q(x, y) for x, y in prm], fill=lab)
        elif kind == 'ell':
            cx, cy, rx, ry = prm
            x0, y0 = Q(cx - rx, cy + ry)
            x1, y1 = Q(cx + rx, cy - ry)
            dr.ellipse([x0, y0, x1, y1], fill=lab)
        else:
            x0, y0, x1, y1, w = prm
            w = max(w, min_w)
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln * w * 0.5, dx / ln * w * 0.5
            dr.polygon([Q(x0 + nx, y0 + ny), Q(x1 + nx, y1 + ny), Q(x1 - nx, y1 - ny), Q(x0 - nx, y0 - ny)],
                       fill=lab)
    return np.asarray(im)


def render(kind, sh, h):
    cw, ch = cell_size(h)
    labels: dict = {}
    out = np.zeros((ch, cw, 4), np.uint8)
    soft = kind in SOFT
    if kind == 'flame' and h >= 6 and isinstance(sh, _Frames):
        return kit_flame(sh.frame, cw, ch, h)
    if h <= 4:
        # tiny figures: a one-pixel column (puffs / crows: two) sampled from a reference render; the top pixel
        # keeps the helmet / hat (the pale dot that makes a formation read as ranks of men)
        ref_h = 40
        rcw, rch = cell_size(ref_h)
        ref = _draw(sh, rcw, rch, ref_h, 1, labels)
        inv = {v: k for k, v in labels.items()}
        ax = cw // 2
        cols = [ax - 1, ax] if kind in ('puff', 'crow') else [ax]
        rx0 = rcw // 2 - 3
        for r in range(h):
            # the band of reference rows this output row covers (the whole band, so a thin crow or a puff
            # that sits between two band centres is not lost)
            ya, yb = (h - r - 1) / h, (h - r) / h
            r0 = int((ref_h + 1) - yb * ref_h)
            r1 = int((ref_h + 1) - ya * ref_h)
            band = ref[max(r0, 0):min(max(r1, r0 + 1), rch), rx0:rx0 + 6]
            if r == 0 and kind not in SOFT | DARK:
                band = ref[max(r0, 0):max(r0, 0) + max(2, (r1 - r0) // 2), rx0:rx0 + 6]
            nz = band[band > 0]
            if nz.size == 0:
                continue
            lab = int(np.bincount(nz).argmax())
            col = inv[lab]
            if r == 0 and kind not in SOFT | DARK:
                col = lighter(col)
            for cx in cols:
                out[1 + r, cx, :3] = pg.hx(col)[:3]
                out[1 + r, cx, 3] = 255
        return out
    big = _draw(sh, cw, ch, h, SS, labels, min_w=(0.95 / h if h >= 8 else 0.0))
    inv = {v: k for k, v in labels.items()}
    blk = big.reshape(ch, SS, cw, SS).transpose(0, 2, 1, 3).reshape(ch, cw, SS * SS)
    cov = (blk > 0).mean(-1)
    n = len(labels) + 1
    counts = np.stack([(blk == i).sum(-1) for i in range(1, n)], -1)
    lab = counts.argmax(-1) + 1
    solid = cov >= (0.4 if h >= 8 else 0.3)
    colmap = np.empty((ch, cw), object)
    for i in range(1, n):
        m = solid & (lab == i)
        colmap[m] = inv[i]
    a = solid.copy()
    if kind not in SOFT | DARK and h >= 5:
        # lit top edge: snow and floodlight on helmets, hats and shoulders
        above = np.zeros_like(a)
        above[1:, :] = a[:-1, :]
        top = a & ~above
        for y, x in zip(*np.nonzero(top)):
            colmap[y, x] = lighter(colmap[y, x])
    for y, x in zip(*np.nonzero(a)):
        out[y, x, :3] = pg.hx(colmap[y, x])[:3]
        out[y, x, 3] = 255
    if h >= 12 and kind not in SOFT | DARK:
        nb = np.zeros_like(a)
        nb[1:, :] |= a[:-1, :]
        nb[:-1, :] |= a[1:, :]
        nb[:, 1:] |= a[:, :-1]
        nb[:, :-1] |= a[:, 1:]
        edge = nb & ~a
        edge[0, :] = False                                 # the cell's top row stays free (no outline lid)
        out[edge, :3] = pg.hx(OUTLINE)[:3]
        out[edge, 3] = 255
    return out


def build_atlas():
    strips = []
    width = 0
    for h in LODS:
        cw, ch = cell_size(h)
        strip = np.zeros((ch, cw * len(SLOTS), 4), np.uint8)
        for i, (kind, sh) in enumerate(SLOTS):
            strip[:, i * cw:(i + 1) * cw] = render(kind, sh, h)
        strips.append(strip)
        width = max(width, strip.shape[1])
    height = sum(s.shape[0] for s in strips)
    atlas = np.zeros((height, width, 4), np.uint8)
    lods = []
    y = 0
    for h, s in zip(LODS, strips):
        atlas[y:y + s.shape[0], :s.shape[1]] = s
        cw, ch = cell_size(h)
        lods.append([y, cw, ch, h])
        y += s.shape[0]
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(atlas, 'RGBA').save(os.path.join(OUT, 'avenue_figures.png'))
    names = [k for k, _ in SLOTS]
    slots = {}
    for i, k in enumerate(names):
        if k not in slots:
            slots[k] = [i, names.count(k)]
    meta = {'atlas': [width, height], 'lods': lods, 'slots': slots, 'height_m': 1.8,
            'anchor': 'x = floor(cell_w / 2), y = fig_h + 1 (feet bottom boundary)',
            'generator': 'tools/pixelgen/gen_great_hall_avenue.py'}
    with open(os.path.join(OUT, 'avenue_figures.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, indent=1)
        f.write('\n')
    return atlas, meta


def preview(atlas, path, scale=4):
    """Zoomed contact sheet of the largest strips on the avenue's asphalt tone (scratch / review only)."""
    a = Image.fromarray(atlas, 'RGBA')
    bg = Image.new('RGBA', a.size, tuple(pg.hx(c('violet', 1))[:3]) + (255,))
    bg.alpha_composite(a)
    bg.resize((a.width * scale, a.height * scale), Image.NEAREST).save(path)


def standards():
    """The column's standards (neutral + _hist), see the module doc."""
    import gen_great_hall_symbols as S
    w, h = 18, 30
    folds = [(4, 0.7), (9, 0.6), (14, 0.7)]
    hist = S.banner(w, h, 12, 13, 9, True, folds, 21)
    neutral = S.cloth(w, h, [S.STEEL[3], S.STEEL[4], S.STEEL[5], S.SNOW[3]], folds, 21)
    a = neutral[:, :, 3] > 0
    for x in (0, w - 1):
        neutral[a[:, x], x, :3] = S.H(S.STEEL[1])[:3]
    d = 13
    x0, y0 = (w - d) // 2, 12 - d // 2
    S.stamp(neutral, S.disc_mask(d), x0, y0, S.STEEL[1])
    inner = d - 2
    disc, pillar = S.reichssiegel(inner)
    S.stamp(neutral, disc, x0 + 1, y0 + 1, S.BLACK)
    S.stamp(neutral, pillar, x0 + 1, y0 + 1, S.WHITE[1])
    # fringe along the hem: dark and pale threads
    rows = np.nonzero(a.any(1))[0]
    yb = int(rows.max())
    for x in range(w):
        if a[yb, x]:
            neutral[yb, x, :3] = S.H(S.STEEL[1] if x % 2 == 0 else S.SNOW[2])[:3]
    for name, img in (('standard.png', neutral), ('standard_hist.png', hist)):
        Image.fromarray(np.asarray(img, np.uint8), 'RGBA').save(os.path.join(OUT, name))
    return neutral, hist


def main():
    standards()
    atlas, meta = build_atlas()
    print('avenue_figures.png', atlas.shape[1], 'x', atlas.shape[0], 'slots', len(SLOTS), meta['slots'])
    if len(sys.argv) > 1:
        preview(atlas, sys.argv[1])


if __name__ == '__main__':
    main()
