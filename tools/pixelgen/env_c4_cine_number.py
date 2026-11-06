"""env_c4_cine_number -- art of LS_C4_Number (owner: cine stream, round 9; C4_DESIGN §2.9).

The first match cut between the cities, on the wagon number C-17/45:
  n1  Service tunnel 3, Karsk: Alexei's lamp along the planks of covered wagon 24 318 -- the fresh red-brown
      paint over the old layers, the painted-over enamel plate, the tin stencil still taped on with the wet
      cream paint in its cut-outs, chalk beside it: „ВТ 23.40“ (Tuesday)                       (pan, 1100 px)
  n2  macro: the stencilled 45 through the tin, wet; the drip runs down                      (match shape)
  n3  Berlin at dawn: the SAME 45 (same shapes, same place) stencilled black on a pine crate, snow in the
      air (n3a) -> the loading hatch of the clearance zone: the lorry's tail lights, the stack of crates going
      down the shaft on the hoist (n3b)
  n4  the tram loop Süd 8: the level's own layers re-baked for the dawn (env_c4_cine_levelplates, shared with
      LS_C4_Voices), Konrad and the people waiting for the first tram (game sheets)
Polish pass: n3b repainted in front of the loop's distant layers (n3b_hatch2); the round-9 n3b_hatch stays for
reference.
Runtime: scenes/cinematics/ch4_number/ch4_number.gd (anchors in layout.json "number").
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CREAM, CONCRETE, IRONK, DAWN, SNOWB, SODIUM, PINE,
                             STEEL, PAPERB, box, ell, poly, grid)
import pg

L = Q.LAYOUT.setdefault('number', {})

N1_W = 1100
N1_PLANK = 13                          # plank height on the wagon side (n1)
N1_DY = 40                             # round 10: the wagon sits 40 px lower -- the tunnel's vault shows above it
N1_TOP, N1_BOT = 64 + N1_DY, 292 + N1_DY   # wagon side: roof edge .. sole bar
N1_STENCIL = (640, 136 + N1_DY, 50)    # x, y (cap top), cap height of C-17/45 on the plate
N1_TIN = (624, 124 + N1_DY, 1000, 198 + N1_DY)   # the tin stencil sheet on the plate
N1_PLATE = (330, 168 + N1_DY)          # the painted-over enamel plate (oval centre)
N1_CHALK = (700, 210 + N1_DY)
N1_GAP = (40, 112)                     # the gap to the wagon before it (buffers, the tunnel's far wall)
N1_LAMP_Y = 206                        # the lamp pool's height on the planks (runtime lamp_pos)
MACRO_H = 180                          # cap height of the macro 45 (n2 and n3a, same shapes, same place)
MACRO_X, MACRO_Y = 192, 92             # top-left of the macro 45
MACRO_PLANK = 52                       # the plank / board seams of n2 and n3a line up (y = 40 + k * 52)


def _wood_grain(w, h, seed, stretch=10, cell=6):
    n = pg.value_noise(max(2, w // stretch + 2), h, cell, seed, octaves=3)
    return np.repeat(n, stretch, axis=1)[:, :w]


# ======================================================================================= n1
def n1_wagon():
    R = Q.ramps(K=KNIGHT, A=AMBER, R=RUST, W=CREAM, I=IRONK, G=['#1A2018', '#2A3226', '#3C4636', '#525C48',
                                                                    '#6A7458'],
                E=['#1A1610', '#2C251A', '#40362A', '#584B3A'])
    W = N1_W
    p = C.Paint(W, VH, R, 'n1')
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 9, 4101)
    grain = _wood_grain(W, VH, 4103)
    lamp = Q.lightfield(W, VH, [(x, 170 + N1_DY, 300, 0.7, 1.2) for x in range(80, W, 240)]) * 0.75
    fine = Q.noise(W, VH, 2, 4121)
    # ---- the tunnel above the wagon: the cast concrete vault (shuttering boards, a rib every 180 px), wet
    # streaks, the cable tray with its sagging cables on brackets, a water pipe, a caged bulkhead lamp (dead), the
    # stencilled tunnel mark; all of it only half-lit by the hand lamp below
    up = yy < N1_TOP - 6
    p.put(up, 'I', 1.8 + nz[up] * 0.8 + fine[up] * 0.3 + lamp[up] * 2.2 + (yy[up] - 40) / 60.0 * 0.8)
    p.put(up & (np.mod(yy - 41, 11) < 1), 'I', 0.6)                            # the shuttering's board lines
    rib = up & (np.mod(xx - 150, 180) < 9)
    p.put(rib, 'I', 1.6 + lamp[rib] * 1.8 + nz[rib] * 0.5)
    p.put(up & (np.mod(xx - 150, 180) == 0), 'I', 2.8 + lamp[up & (np.mod(xx - 150, 180) == 0)] * 1.6)
    wet = up & (Q.noise(W, VH, 4, 4123) > 0.66) & (np.mod(xx, 7) < 3)
    p.put(wet, 'I', 0.5)                                                       # damp runs down the concrete
    p.put(box(0, 52, W, 55, W), 'I', 2.2 + lamp[52:55].mean() * 2.0)            # the water pipe
    p.put(box(0, 52, W, 53, W), 'I', 4.2)
    for fx_ in range(60, W, 140):
        p.put(box(fx_, 50, fx_ + 3, 57, W), 'I', 3.4)                            # its flanges
    p.put(box(0, 55, W, 56, W), 'R', 1.6 + lamp[55] * 3.0)                      # lit from below by the hand lamp
    for bx_ in range(20, W, 110):                                              # cable brackets
        p.put(box(bx_, 62, bx_ + 2, 74, W), 'I', 3.0)
        p.put(box(bx_ - 4, 72, bx_ + 6, 74, W), 'I', 3.4)
    for k, (cy0, sag, tone) in enumerate(((66, 4.0, 2.4), (69, 5.0, 1.6), (71, 6.0, 2.0))):
        u = np.mod(xx - 20, 110) / 110.0
        cy = cy0 + sag * 4.0 * u * (1.0 - u)
        cab = (np.abs(yy - cy) < 1.0) & up
        p.put(cab, 'K', tone + lamp[cab] * 2.4)
        under = (yy - cy >= 0.6) & (yy - cy < 1.6) & up & (fine > 0.3)
        p.put(under, 'R', 1.2 + lamp[under] * 2.6)                              # the warm edge underneath
    for lx_ in (300, 780):                                                     # the caged bulkhead lamps
        cage = ell(lx_, 86, 9, 7, W) & (yy < N1_TOP - 6)
        p.put(cage, 'I', 1.4)
        p.put(cage & (np.mod(xx - lx_, 4) == 0), 'I', 3.4)
        p.put(ell(lx_, 86, 5, 4, W), 'K', 2.0)
        p.put(box(lx_ - 2, 76, lx_ + 2, 80, W), 'I', 3.0)
    mark = Q.stencil_mask('III', 12, W, VH, 520, 60, width=1.4) & (fine > 0.25)
    p.put(mark, 'W', 1.4 + lamp[mark] * 1.4)                                   # tunnel 3, stencilled
    # the roof of the wagon: its eaves and gutter, beaded with condensation
    p.put(box(0, N1_TOP - 10, W, N1_TOP - 6, W), 'I', 1.4 + lamp[N1_TOP - 8].mean() * 1.2)
    beads = box(0, N1_TOP - 6, W, N1_TOP - 5, W) & (fine > 0.6)
    p.put(beads, 'W', 3.0)
    below = yy >= N1_BOT
    p.put(below, 'I', 0.6 + nz[below] * 0.8)
    # roof edge (iron angle) and the sole bar with rivets
    p.put(box(0, N1_TOP - 6, W, N1_TOP, W), 'I', 2.6)
    p.put(box(0, N1_TOP - 6, W, N1_TOP - 5, W), 'I', 4.4)
    p.put(box(0, N1_BOT, W, N1_BOT + 12, W), 'I', 1.8)
    p.put(box(0, N1_BOT, W, N1_BOT + 1, W), 'I', 3.6)
    rv = (yy >= N1_BOT + 4) & (yy < N1_BOT + 6) & (np.mod(xx, 22) < 2)
    p.put(rv, 'I', 4.0)
    # the planks: fresh red-brown paint, grain showing through, a dark seam between every two planks
    side = (yy >= N1_TOP) & (yy < N1_BOT)
    k = np.floor((yy - N1_TOP) / N1_PLANK)
    v = (yy - N1_TOP) - k * N1_PLANK
    tone = 3.2 + grain * 1.6 + nz * 0.5 - (v < 2) * 0.8 + (v > N1_PLANK - 3) * 0.4 + lamp * 1.6
    p.put(side, 'R', tone[side])
    seam = side & (v < 1)
    p.put(seam, 'R', 0.6)
    # old layers where the fresh coat has flaked: grey-green of the Reichsbahn era and bare wood
    flake = side & (Q.noise(W, VH, 7, 4105) > 0.73) & (v > 2) & ~((xx > N1_TIN[0] - 30) & (xx < N1_TIN[2] + 30))
    p.put(flake, 'G', 1.6 + grain[flake] * 2.0)
    bare = flake & (Q.noise(W, VH, 3, 4107) > 0.62)
    p.put(bare, 'E', 1.4 + grain[bare] * 1.8)
    # iron stanchions with bolt heads and the diagonal brace (straps over the planks)
    for sx in (120, 470, 1060):
        st = box(sx, N1_TOP, sx + 10, N1_BOT, W)
        p.put(st, 'I', 2.2 + lamp[st] * 1.4)
        p.put(box(sx, N1_TOP, sx + 1, N1_BOT, W), 'I', 4.0)
        for by in range(N1_TOP + 8, N1_BOT, 26):
            p.put(ell(sx + 5, by, 1.8, 1.8, W), 'I', 4.6)
    brace = p.line([(130, N1_BOT - 4), (460, N1_TOP + 6)], r=3.0)
    p.put(brace, 'I', 2.0 + lamp[brace] * 1.2)
    p.put(brace & C.rim(brace, 0, -1), 'I', 3.8)
    # the painted-over enamel plate: an oval in relief under the red-brown, „24 318“ embossed faintly
    px, py = N1_PLATE
    oval = ell(px, py, 58, 22, W)
    p.put(oval, 'R', 3.6 + grain[oval] * 0.8 + lamp[oval] * 1.4)
    p.put(oval & C.rim(oval, 0, -1, 2), 'R', 6.0)
    p.put(oval & C.rim(oval, 0, 1, 2), 'R', 1.4)
    emb = Q.place(Q.smooth_up(Q.text('24 318', 'l', 2), 2), W, VH, px - 46, py - 8)
    p.put(emb, 'R', 5.0)
    p.put(emb & ~C.shift(emb, 0, 1) & C.shift(emb, 0, -1) | (C.shift(emb, 0, 1) & ~emb), 'R', 1.8)
    # the fresh patch where the number goes: glossier paint, brush strokes
    tx0, ty0, tx1, ty1 = N1_TIN
    patch = box(tx0 - 14, ty0 - 10, tx1 + 14, ty1 + 10, W)
    strokes = np.sin(xx * 0.9 + Q.noise(W, VH, 4, 4109) * 6.0) > 0.6
    p.put(patch, 'R', 3.8 + grain[patch] * 0.6 + lamp[patch] * 1.6 + strokes[patch] * 0.6)
    # the tin stencil sheet, taped at the corners, overspray around the cut-outs
    tin = box(tx0, ty0, tx1, ty1, W)
    dent = Q.noise(W, VH, 11, 4111)
    p.put(tin, 'I', 4.0 + dent[tin] * 1.4 + lamp[tin] * 1.0)
    p.put(tin & (yy == ty0), 'I', 6.6)
    p.put(tin & (yy == ty1 - 1), 'I', 1.8)
    sx_, sy_, sh = N1_STENCIL
    letters = Q.stencil_mask('C-17/45', sh, W, VH, sx_, sy_)
    spray = C.blur(letters.astype(np.float32), 4) > (0.18 + pg.bayer(W, VH, 1, 2) * 0.5)
    p.put(tin & spray & ~letters, 'W', 2.2 + nz[tin & spray & ~letters])
    p.put(letters, 'W', 4.4 + grain[letters] * 0.8 + lamp[letters] * 1.2)
    p.put(letters & C.rim(letters, -1, -1), 'W', 6.0)                 # wet sheen on the upper-left edges
    p.put(letters & C.rim(letters, 1, 1), 'W', 2.6)
    for (cx, cy) in ((tx0 + 2, ty0 + 2), (tx1 - 18, ty0 + 2), (tx0 + 2, ty1 - 10), (tx1 - 18, ty1 - 10)):
        tape = box(cx - 4, cy - 4, cx + 16, cy + 8, W)
        p.put(tape, 'E', 2.6 + nz[tape] * 0.8)
        p.put(tape & (yy == cy - 4), 'E', 3.6)
    # chalk on the planks to the right of the number: Tuesday 23.40 (Вт = вторник)
    ch = Q.place(Q.chalk('ВТ 23.40', scale=2, slant=0.2, seed=4113), W, VH, N1_CHALK[0], N1_CHALK[1])
    p.put(ch, 'W', 3.4 + nz[ch] * 1.4)
    ul = p.line([(N1_CHALK[0] - 2, N1_CHALK[1] + 22), (N1_CHALK[0] + 70, N1_CHALK[1] + 19)], r=0.7) & \
        (Q.noise(W, VH, 2, 4115) > 0.35)
    p.put(ul, 'W', 3.0)
    # the gap to the wagon in front (the start of the pan, in the dark): its end post and buffers, the coupling
    # chain, and through the gap the tunnel's far wall with a cable and a refuge niche
    g0, g1 = N1_GAP
    gap = (xx >= g0) & (xx < g1) & (yy >= N1_TOP - 6)
    p.put(gap, 'I', 0.6 + nz[gap] * 0.6 + lamp[gap] * 0.8)
    p.put(gap & (np.mod(yy - N1_TOP, 13) < 1), 'I', 0.3)
    niche = box(g0 + 18, N1_TOP + 60, g1 - 20, N1_TOP + 140, W)
    p.put(niche, 'K', 0.4)
    p.put(box(g0, N1_TOP + 30, g1, N1_TOP + 32, W), 'K', 2.0)                  # the far wall's cable
    prev = box(0, N1_TOP - 6, g0, N1_BOT, W)                                   # the end of the wagon before it
    p.put(prev, 'R', 1.8 + grain[prev] * 0.8 + lamp[prev] * 0.8)
    p.put(box(g0 - 8, N1_TOP - 6, g0, N1_BOT, W), 'I', 1.6)
    for (a_, b_) in ((g0, g0 + 6), (g1 - 6, g1)):                              # the wagons' corner posts
        post = box(a_, N1_TOP - 6, b_, N1_BOT, W)
        p.put(post, 'I', 1.8 + lamp[post] * 1.0)
    ch = p.line([(g0 + 6, N1_TOP + 150), ((g0 + g1) / 2, N1_TOP + 168), (g1 - 6, N1_TOP + 150)], r=0.8)
    p.put(ch, 'I', 2.6)                                                        # the brake hose hanging across
    p.resolve(band=2.0)
    L['n1_w'] = W
    L['n1_lamp_y'] = N1_LAMP_Y
    L['n1_stencil'] = list(N1_STENCIL)
    L['n1_tin'] = list(N1_TIN)
    lay, _ = Q.stencil_layout('C-17/45', sh)
    five_x = sx_ + [g[1] for g in lay if g[0] == '5'][0]
    L['n1_drip'] = [round(five_x + 2.6 * sh / 9.0, 1), round(sy_ + sh * 0.97, 1)]   # under the bowl of the 5
    return p.L.c


def n1_glow():
    """Warm light of the hand lamp (additive, moved with the lamp at runtime)."""
    return Q.glow_sprite(360, 300, [(180, 150, 170, 140, (80, 46, 14), 1.3), (180, 150, 70, 60, (60, 36, 10), 1.5)],
                         6.0)


N1_BEAM = (360, 300, 270, 110)         # beam sprite w, h; the pool's centre in it (x, y): the lamp is low left


def n1_beam():
    """The hand lamp's beam in the tunnel's dusty air (additive): a soft cone from Alexei's lamp, held low at the
    left just out of the frame, widening up to the pool of light on the planks; brighter along its axis and near
    the lamp, broken by the dust (dithered steps).  Moved with the pool at runtime."""
    w, h, px, py = N1_BEAM
    yy, xx = grid(h, w)
    ax, ay = 0.0, float(h)                                                     # the lamp, out of the frame
    vx, vy = px - ax, py - ay
    L_ = math.hypot(vx, vy)
    ux, uy = vx / L_, vy / L_
    rx, ry = xx + 0.5 - ax, yy + 0.5 - ay
    along = rx * ux + ry * uy
    across = np.abs(rx * (-uy) + ry * ux)
    t = np.clip(along / L_, 0, 1.2)
    half = 8.0 + t * 62.0
    core = np.clip(1.0 - across / half, 0, 1) ** 1.3
    fade = np.clip(1.0 - (t - 0.9) / 0.18, 0, 1) * np.clip(along / 50.0, 0, 1)
    fade *= np.clip(np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / 12.0, 0, 1)
    dust = 0.75 + 0.25 * Q.noise(w, h, 7, 4131)
    v = core * fade * dust * (0.55 + 0.45 * (1.0 - t))
    q = np.floor(v * 5.0 + pg.bayer(w, h, 1, 3) * 0.95) / 5.0
    out = np.zeros((h, w, 4), np.uint8)
    rgb = np.asarray((104, 66, 26), np.float32)
    out[..., :3] = np.clip(rgb[None, None] * q[..., None], 0, 255).astype(np.uint8)
    out[..., 3] = 255
    L['n1_beam'] = [px, py]
    return out


# ======================================================================================= n2 / n3a (macro)
def _macro_letters():
    return Q.stencil_mask('45', MACRO_H, VW, VH, MACRO_X, MACRO_Y)


def n2_macro():
    R = Q.ramps(R=RUST, W=CREAM, I=IRONK, E=['#1A1610', '#2C251A', '#40362A', '#584B3A', '#6E604A'], A=AMBER)
    p = C.Paint(VW, VH, R, 'n2')
    yy, xx = p.yy, p.xx
    grain = _wood_grain(VW, VH, 4201, stretch=26, cell=5)
    nz = Q.noise(VW, VH, 14, 4203)
    lamp = Q.lightfield(VW, VH, [(-40, 140, 620, 1.0, 1.1)])
    k = np.floor((yy - 40) / MACRO_PLANK)
    v = (yy - 40) - k * MACRO_PLANK
    p.put(yy >= 0, 'R', 2.6 + grain * 2.0 + nz * 0.6 + lamp * 2.2 - (v < 5) * 1.0)
    p.put((v < 3), 'R', 0.6 + lamp[v < 3] * 0.8)
    brush = (np.sin(yy * 0.35 + xx * 0.04 + Q.noise(VW, VH, 6, 4205) * 5.0) > 0.82)
    p.put(brush, 'R', 4.2 + lamp[brush] * 1.6)
    # the tin sheet (macro): dents, a scratched edge, the cut-outs
    tin = box(96, 64, 600, 296)
    dent = Q.noise(VW, VH, 30, 4207, octaves=4)
    p.put(tin, 'I', 3.8 + dent[tin] * 2.0 + lamp[tin] * 1.8)
    p.put(tin & (yy < 67), 'I', 7.0)
    p.put(tin & (xx < 99), 'I', 6.2)
    p.put(tin & (yy >= 293), 'I', 1.4)
    scr = tin & (Q.noise(VW, VH, 2, 4209) > 0.86) & (np.mod(xx + yy, 3) == 0)
    p.put(scr, 'I', 6.0)
    letters = _macro_letters()
    spray = C.blur(letters.astype(np.float32), 9) > (0.10 + pg.bayer(VW, VH, 3, 1) * 0.55)
    sp = tin & spray & ~letters
    p.put(sp, 'W', 1.6 + nz[sp] * 1.6 + lamp[sp] * 1.4)
    # the wet paint in the cut-outs: brush texture, a sheen along the lit edges, a darker pooled bottom
    body = letters
    paint = 3.4 + Q.noise(VW, VH, 5, 4211) * 1.4 + lamp * 1.6
    p.put(body, 'W', paint[body])
    p.put(body & C.rim(body, -1, -1, 2), 'W', 6.0)
    p.put(body & C.rim(body, 1, 1, 2), 'W', 1.8)
    gl = body & (Q.noise(VW, VH, 3, 4213) > 0.78)
    p.put(gl, 'W', 6.0)
    # tape at the tin's top-left corner
    tape = poly([(80, 52), (176, 46), (180, 84), (84, 92)])
    p.put(tape, 'E', 2.4 + nz[tape] * 1.6 + lamp[tape] * 1.4)
    p.put(tape & C.rim(tape, 0, -1), 'E', 4.4)
    p.resolve(band=2.0)
    lay, _ = Q.stencil_layout('45', MACRO_H)
    L['macro'] = [MACRO_X, MACRO_Y, MACRO_H]
    L['macro_drip'] = [round(MACRO_X + lay[1][1] + 2.6 * MACRO_H / 9.0, 1), round(MACRO_Y + MACRO_H * 0.97, 1)]
    return p.L.c


def n2_glints():
    """Additive glints on the wet paint (pulsing slowly at runtime: the lamp's flame breathes)."""
    letters = _macro_letters()
    a = np.zeros((VH, VW, 3), np.float32)
    rng = np.random.default_rng(4215)
    ys, xs = np.nonzero(letters & C.rim(letters, -1, -1, 3))
    for i in rng.choice(len(ys), size=min(40, len(ys)), replace=False):
        Q.add_glow(a, xs[i] + 0.5, ys[i] + 0.5, 4.0, 3.0, (120, 96, 60), 1.6)
    return Q.K.soft_quant(a, 6.0)


def n3a_macro():
    """Berlin: the same 45 stencilled black on a pine crate at dawn (same shapes, same place as n2)."""
    R = Q.ramps(P=PINE, B=['#06080C', '#0C1018', '#141A24', '#1E2632'], D=DAWN, S=SNOWB)
    p = C.Paint(VW, VH, R, 'n3a')
    yy, xx = p.yy, p.xx
    grain = _wood_grain(VW, VH, 4301, stretch=30, cell=4)
    nz = Q.noise(VW, VH, 12, 4303)
    sky = Q.lightfield(VW, VH, [(620, -40, 640, 1.0, 1.0)])
    k = np.floor((yy - 40) / MACRO_PLANK)
    v = (yy - 40) - k * MACRO_PLANK
    knot = Q.noise(VW, VH, 40, 4305) > 0.8
    p.put(yy >= 0, 'P', 2.6 + grain * 2.4 + nz * 0.5 + sky * 1.6 - (v < 4) * 1.4 - knot * 1.0)
    p.put(v < 2, 'B', 1.2)
    # nail heads at the board ends
    for ny in range(40 + 26, VH, MACRO_PLANK):
        for nx in (40, 604):
            p.put(ell(nx, ny, 4, 4), 'B', 2.4)
            p.put(ell(nx - 1, ny - 1, 1.5, 1.5), 'S', 6.0)
    # black stencil paint soaked into the grain: blunter edges, a little bleed along the fibres
    letters = _macro_letters()
    bleed = C.blur(letters.astype(np.float32), 2)
    bl = (bleed > 0.25 + (grain - 0.5) * 0.5) & ~letters
    p.put(letters, 'B', 0.6 + grain[letters] * 1.2)
    p.put(bl, 'B', 2.4)
    # a little snow resting in the board seams and on the upper edges of the letters
    snow = (v >= 2) & (v < 4) & (Q.noise(VW, VH, 6, 4307) > 0.45)
    p.put(snow, 'S', 7.0 + nz[snow])
    p.resolve(band=2.0)
    return p.L.c


# ======================================================================================= n3b (the hatch)
N3_HATCH = (360, 276, 520, 292)        # the open shaft hatch in the ground (x0, y0 opening top, x1, y1)
N3_STACK = (382, 160)                  # top-left of the crate stack before it goes down


def n3b_hatch():
    R = Q.ramps(D=DAWN, S=SNOWB, T=STEEL, P=PINE, B=['#06080C', '#0C1018', '#141A24', '#1E2632', '#2A3440'],
                N=SODIUM, R=['#200808', '#401010', '#6A1A16', '#96281E'], K=['#0C0C0E', '#18181C', '#26262A',
                                                                           '#36363A', '#4A4A4C'])
    p = C.Paint(VW, VH, R, 'n3b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 4401)
    hz = 172
    sky = yy < hz
    p.put(sky, 'D', 8.4 - (hz - yy[sky]) / 126.0 * 5.6 + nz[sky] * 0.5)
    # far: the dome of the Great Hall in the haze (a darker silhouette against the dawn), cranes, blocks
    dome = ell(250, hz - 6, 120, 70) & (yy < hz - 6)
    p.put(dome, 'D', 5.4 - (yy[dome] - 96) / 70.0 * 0.6 + nz[dome] * 0.3)
    p.put(dome & C.rim(dome, 1, -1, 2), 'D', 6.6)
    p.put(box(240, hz - 92, 260, hz - 70), 'D', 5.2)
    p.put(ell(250, hz - 94, 8, 5), 'D', 5.0)
    ribs = dome & (np.mod(np.arctan2(yy - (hz - 6), xx - 250) * 12.0, 1.0) < 0.12)
    p.put(ribs, 'D', 4.6)
    for cx_, h_ in ((80, 70), (520, 84), (600, 60)):
        p.put(box(cx_, hz - h_, cx_ + 3, hz), 'D', 4.4)
        p.put(p.line([(cx_ - 40, hz - h_), (cx_ + 50, hz - h_ + 2)], r=0.8), 'D', 4.4)
    blocks = (yy >= hz - 26) & sky & (np.mod(np.floor(xx / 30) * 13.7, 9) > 3.2 + (hz - yy) / 8.0)
    p.put(blocks, 'D', 3.8)
    # the cleared ground: trodden snow, ruts of the lorry, the edge of a demolished wall at the right
    gr = yy >= hz
    u = (yy - hz) / (VH - hz)
    p.put(gr, 'S', 4.2 + u[gr] * 2.4 + nz[gr] * 1.0)
    ruts = gr & (np.abs(np.mod(xx * 0.6 + (yy - hz) * 1.8, 48) - 24) < 1.2) & (xx < 330)
    p.put(ruts, 'S', 2.6)
    wall = poly([(560, 120), (640, 96), (640, 300), (580, 300), (574, 220), (590, 170)])
    p.put(wall, 'B', 2.0 + nz[wall] * 1.2)
    p.put(wall & (np.mod(yy, 8) == 0), 'B', 1.0)
    # the lorry from behind (left): canvas tilt, tailgate down, tail lights, exhaust pipe
    body = box(40, 150, 230, 268)
    p.put(body, 'K', 1.4 + nz[body] * 0.8)
    tilt = poly([(36, 150), (234, 150), (228, 118), (42, 118)])
    p.put(tilt, 'K', 2.2 + nz[tilt] * 0.8)
    p.put(tilt & (np.mod(xx, 24) < 2), 'K', 1.4)
    p.put(box(36, 118, 234, 120), 'S', 7.0)                      # snow on the tilt
    gate = box(46, 248, 224, 262)
    p.put(gate, 'K', 2.8)
    p.put(box(46, 248, 224, 249), 'S', 6.0)
    for wx in (56, 196):
        p.put(ell(wx + 10, 276, 16, 16), 'K', 0.6)
        p.put(ell(wx + 10, 276, 7, 7), 'K', 2.0)
    for lx in (52, 210):
        p.put(box(lx, 230, lx + 10, 240), 'R', 3.0)
    # the hoist: an A-frame gantry over the hatch, the chain block, the platform rails
    hx0, hy0, hx1, hy1 = N3_HATCH
    for gx in (hx0 - 8, hx1 + 4):
        p.put(p.line([(gx, hy1), (gx + (4 if gx < 400 else -4), 104)], r=2.0), 'T', 3.0)
    p.put(box(hx0 - 10, 98, hx1 + 10, 106), 'T', 3.6)
    p.put(box(hx0 - 10, 98, hx1 + 10, 99), 'S', 7.0)
    p.put(box(436, 106, 446, 122), 'T', 2.2)
    # the hatch: steel frame flush with the ground, the shaft below
    op = box(hx0, hy0, hx1, hy1 + 22)
    p.put(op, 'B', 0.4)
    p.put(box(hx0, hy0, hx1, hy0 + 3), 'B', 1.6)
    fr = box(hx0 - 8, hy0 - 4, hx1 + 8, hy0) | box(hx0 - 8, hy1, hx1 + 8, hy1 + 6)
    p.put(fr, 'T', 4.0)
    lid = poly([(hx1 + 8, hy0 - 2), (hx1 + 60, hy0 - 70), (hx1 + 68, hy0 - 64), (hx1 + 16, hy0 + 2)])
    p.put(lid, 'T', 3.0 + nz[lid])
    p.put(lid & C.rim(lid, 0, -1), 'S', 6.6)
    p.resolve(band=2.0)
    L['n3_hatch'] = list(N3_HATCH)
    L['n3_stack'] = list(N3_STACK)
    L['n3_tail'] = [[57, 235], [215, 235]]
    L['n3_exhaust'] = [232, 262]
    L['n3_chain'] = [441, 122]
    return p.L.c


def n3b_lip():
    """The near lip of the hatch frame + the ground in front of it: drawn over the lowering stack."""
    hx0, hy0, hx1, hy1 = N3_HATCH
    R = Q.ramps(S=SNOWB, T=STEEL)
    p = C.Paint(VW, VH, R, 'n3lip')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 4401)
    u = (yy - 172) / (VH - 172)
    front = box(hx0 - 12, hy1, hx1 + 12, VH)
    p.put(front, 'S', 4.2 + u[front] * 2.4 + nz[front] * 1.0)
    p.put(box(hx0 - 8, hy1, hx1 + 8, hy1 + 6), 'T', 4.0)
    p.put(box(hx0 - 8, hy1, hx1 + 8, hy1 + 1), 'T', 6.4)
    p.resolve(band=2.0)
    return p.L.c


def n3b_stack():
    """Three crates on the hoist platform, each stencilled C-17/45; chains up to the block."""
    w, h = 116, 132
    R = Q.ramps(P=PINE, B=['#06080C', '#0C1018', '#141A24', '#1E2632'], T=STEEL, S=SNOWB)
    p = C.Paint(w, h, R, 'stack')
    yy, xx = p.yy, p.xx
    grain = _wood_grain(w, h, 4411, stretch=8, cell=3)
    p.put(box(0, h - 8, w, h, w, h), 'T', 2.6)
    p.put(box(0, h - 8, w, h - 7, w, h), 'T', 5.0)
    for i, (cy0, cx0) in enumerate(((84, 4), (44, 10), (6, 2))):
        cb = box(cx0, cy0, cx0 + 104, cy0 + 38, w, h)
        p.put(cb, 'P', 3.0 + grain[cb] * 1.8 - (np.mod(yy[cb] - cy0, 13) < 1) * 1.6 + (xx[cb] - cx0) / 104.0)
        p.put(cb & ((xx == cx0) | (xx == cx0 + 103) | (yy == cy0 + 37)), 'B', 2.4)
        p.put(cb & (yy == cy0), 'S', 7.4)
        st = Q.stencil_mask('C-17/45', 10, w, h, cx0 + 14, cy0 + 14, width=1.9)
        p.put(st, 'B', 0.8)
    for cx_ in (8, 106):
        p.put(p.line([(cx_, h - 8), (58, -40)], r=0.6), 'T', 4.4)
    p.resolve(band=2.0)
    return p.L.c


def flakes_sheet():
    """Macro snowflakes for n3a: 4 sizes (soft out-of-focus discs), additive."""
    out = []
    for r in (3, 5, 8, 12):
        s = 2 * r + 4
        a = np.zeros((s, s, 3), np.float32)
        Q.add_glow(a, s / 2, s / 2, r, r, (70, 78, 92), 1.0)
        fr = Q.K.soft_quant(a, 8.0)
        pad = np.zeros((28, 28, 4), np.uint8)
        o = (28 - s) // 2
        pad[o:o + s, o:o + s] = fr
        out.append(pad)
    return Q.sheet(out)


# ======================================================================================= n3b (polish pass)
def n3b_hatch2():
    """The loading hatch at dawn, closer than the level shows it: behind, the loop's own distant layers (the dome
    of the Great Hall, the axis, the cranes); the site hoarding 'BAUSTELLE / BETRETEN VERBOTEN' at the right; the
    lorry from behind (canvas tilt on its hoops, ropes, the tailgate down on chains, twin rear wheels, mud flaps,
    the tail lights); the A-frame hoist with its chain block over the open hatch, the lid standing up on its hinge,
    warm light rising from the shaft; trodden snow with tyre tracks and boot prints."""
    import env_c4_cine_levelart as LA
    import env_c4_cine_levelplates as LP
    bg = np.zeros((VH, VW, 4), np.float32)
    bg[..., 3] = 1.0
    cam = 520
    mod = np.asarray(LP.MOD_DAWN, np.float32)
    for name, (fn, hx, hy, par) in LP.LOOP_LAYERS.items():
        if name == 'fg':
            continue
        a = LA.layer('berlin_annex', fn)['alb'].copy()
        a[..., :3] *= mod
        LA.over(bg, a, int(round(hx - cam * par)), hy - 24)
    R = Q.ramps(D=DAWN, S=SNOWB, T=STEEL, P=PINE, B=['#06080C', '#0C1018', '#141A24', '#1E2632', '#2A3440'],
                N=SODIUM, R=['#200808', '#401010', '#6A1A16', '#96281E', '#C83A28'],
                K=['#0C0C0E', '#18181C', '#26262A', '#36363A', '#4A4A4C', '#606064'],
                G=['#141A12', '#1E281A', '#2A3624', '#3A4830', '#4C5C3E', '#627452'],
                X=PAPERB, H=['#2A2016', '#4A3A22', '#7A6232', '#A88A4A', '#D0B070'])
    p = C.Paint(VW, VH, R, 'n3b2')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 4501)
    fine = Q.noise(VW, VH, 3, 4503)
    hx0, hy0, hx1, hy1 = N3_HATCH
    shaft = Q.lightfield(VW, VH, [((hx0 + hx1) / 2, hy0 + 10, 150, 1.0, 1.3)])
    sky = Q.lightfield(VW, VH, [(420, -60, 520, 1.0, 1.0)])
    # the cleared ground: trodden snow, tyre tracks from the lorry, boot prints to the hatch
    hz = 200
    gr = yy >= hz
    u = (yy - hz) / (VH - hz)
    p.put(gr, 'S', 3.6 + u[gr] * 2.6 + nz[gr] * 0.9 + fine[gr] * 0.3 + shaft[gr] * 1.6)
    for tx_ in (70, 96, 180, 206):
        trk = gr & (np.abs(xx - (tx_ + (yy - hz) * 0.18)) < 4) & (yy > 268)
        p.put(trk, 'S', 2.4 + nz[trk] * 0.6)
        p.put(trk & (np.mod(yy, 5) < 2), 'S', 1.8)
    for k in range(14):
        bx_, by_ = 250 + k * 9 + (k % 2) * 4, 300 - k * 1.5 + (k % 2) * 5
        p.put(ell(bx_, by_, 3, 2), 'S', 2.6)
    # the site hoarding at the right: planks, the sign, a blinking lamp on top (runtime)
    hd = box(540, 150, VW, 284)
    p.put(hd, 'P', 2.4 + nz[hd] * 0.8 + sky[hd] * 1.2 - (np.mod(xx[hd], 14) < 1) * 1.2)
    p.put(box(540, 146, VW, 150), 'S', 6.6)
    sign = box(566, 160, 636, 204)                                             # (round 10: clear of the lid)
    p.put(sign, 'X', 6.6)
    p.put(sign & C.rim(sign, 0, 0, 1), 'R', 3.4)
    p.put(Q.text_at('BAUSTELLE', VW, VH, 572, 166, 's'), 'R', 3.6)
    p.put(Q.text_at('BETRETEN', VW, VH, 574, 178, 's') | Q.text_at('VERBOTEN', VW, VH, 574, 188, 's'), 'B', 1.0)
    for nx_ in (569, 633):
        p.put(box(nx_, 162, nx_ + 1, 163), 'K', 1.0)                           # its nails
    p.put(box(600, 140, 604, 150), 'K', 2.0)
    # the A-frame hoist over the hatch: legs, the cross beam, the trolley and chain block, braces
    for (gx0, gx1) in ((hx0 - 10, hx0 + 6), (hx1 + 8, hx1 - 8)):
        leg = p.line([(gx0, hy1 + 2), (gx1, 104)], r=2.2)
        p.put(leg, 'T', 2.8 + nz[leg] * 0.4 + sky[leg] * 1.4)
        p.put(leg & C.rim(leg, -1, 0), 'T', 4.6)
    p.put(p.line([(hx0 - 4, 200), (hx1 + 2, 200)], r=1.0), 'T', 2.4)
    p.put(p.line([(hx0 - 2, 150), (hx0 + 30, 108)], r=0.8) | p.line([(hx1 + 2, 150), (hx1 - 30, 108)], r=0.8),
          'T', 2.6)
    p.put(box(hx0 - 14, 96, hx1 + 14, 106), 'T', 3.4)
    p.put(box(hx0 - 14, 96, hx1 + 14, 97), 'S', 7.0)
    p.put(box(hx0 - 14, 105, hx1 + 14, 106), 'T', 1.6)
    p.put(box(430, 106, 452, 116), 'T', 2.2)                                  # trolley
    p.put(box(434, 116, 448, 124), 'K', 2.4)                                   # chain block
    p.put(ell(441, 120, 5, 5) & ~ell(441, 120, 2, 2), 'K', 4.0)
    # (the hand chain is a runtime drawing now: it runs down into the shaft, pulled from below)
    # the hatch: steel frame flush with the snow, the shaft lit from below, the lid on its hinge
    op = box(hx0, hy0, hx1, hy1 + 22)
    p.put(op, 'N', 0.6 + shaft[op] * 2.6 - (yy[op] - hy0) / 30.0)
    p.put(box(hx0, hy0, hx1, hy0 + 3), 'B', 1.6)
    fr = box(hx0 - 8, hy0 - 4, hx1 + 8, hy0) | box(hx1, hy0, hx1 + 8, hy1)
    p.put(fr, 'T', 3.6 + shaft[fr] * 1.4)
    p.put(box(hx0 - 8, hy0 - 4, hx1 + 8, hy0 - 3), 'S', 6.6)
    lid = poly([(hx1 + 8, hy0 - 2), (hx1 + 38, hy0 - 58), (hx1 + 48, hy0 - 53), (hx1 + 18, hy0 + 2)])
    p.put(lid, 'T', 2.8 + nz[lid] * 0.8 + sky[lid] * 1.2)
    p.put(lid & (np.mod(xx + yy, 9) < 1), 'T', 2.0)                           # chequer plate
    p.put(lid & C.rim(lid, 0, -1), 'S', 6.4)
    p.put(lid & C.rim(lid, 1, 0), 'T', 4.4)
    # the lorry from behind: canvas tilt over hoops, ropes, snow; the open back; tailgate on chains
    tilt = poly([(36, 152), (234, 152), (228, 116), (216, 108), (54, 108), (42, 116)])
    p.put(tilt, 'G', 2.0 + nz[tilt] * 0.8 + sky[tilt] * 1.0)
    p.put(tilt & (np.mod(xx, 26) < 2), 'G', 1.2)
    p.put(tilt & (np.mod(yy, 11) == 0), 'G', 1.4)
    p.put(poly([(54, 108), (216, 108), (210, 102), (60, 102)]), 'S', 6.8)
    back = box(46, 120, 224, 150)
    p.put(back, 'K', 0.8 + nz[back] * 0.4)
    for (cx_, cw) in ((60, 30), (96, 26), (128, 34), (170, 28)):              # crates still inside, in the dark
        cb = box(cx_, 130, cx_ + cw, 150)
        p.put(cb, 'P', 1.2 + nz[cb] * 0.5)
        p.put(box(cx_, 130, cx_ + cw, 131), 'P', 2.2)
    p.put(box(42, 116, 46, 152) | box(224, 116, 228, 152), 'G', 1.4)
    for rx_ in range(56, 220, 26):
        p.put(p.line([(rx_, 108), (rx_ + 2, 120)], r=0.5), 'H', 2.4)          # the lashing ropes
    body = box(38, 150, 232, 250)
    p.put(body, 'K', 1.6 + nz[body] * 0.6 - (np.mod(yy[body] - 150, 14) < 1) * 0.6)
    p.put(box(38, 150, 232, 152), 'K', 3.0)
    gate = box(42, 248, 228, 262)
    p.put(gate, 'K', 2.6 + nz[gate] * 0.4)
    p.put(box(42, 248, 228, 249), 'S', 6.2)
    for cx_ in (44, 224):
        p.put(p.line([(cx_, 236), (cx_ + (6 if cx_ < 100 else -6), 250)], r=0.5), 'T', 4.2)
    plate = box(118, 252, 152, 260)
    p.put(plate, 'X', 5.4)
    p.put(plate & (np.mod(xx, 4) == 0) & (yy == 256), 'B', 1.2)
    for lx_ in (50, 208):
        p.put(box(lx_, 228, lx_ + 12, 240), 'R', 3.2)
        p.put(box(lx_ + 2, 230, lx_ + 10, 238), 'R', 4.4)
    for wx in (52, 186):
        p.put(ell(wx + 16, 278, 20, 18), 'K', 0.6)
        p.put(ell(wx + 16, 278, 9, 8), 'K', 2.2)
        p.put(ell(wx + 16, 278, 3, 3), 'K', 3.6)
        p.put(box(wx + 2, 262, wx + 30, 268), 'K', 1.0)                         # mud flap
    p.put(box(228, 262, 238, 266), 'K', 2.6)                                    # exhaust pipe
    p.resolve(band=2.0)
    out = bg.copy()
    LA.over(out, p.L.c.astype(np.float32) / 255.0, 0, 0)
    L['n3_hatch'] = list(N3_HATCH)
    L['n3_stack'] = list(N3_STACK)
    L['n3_tail'] = [[56, 234], [214, 234]]
    L['n3_exhaust'] = [238, 262]
    L['n3_chain'] = [441, 122]
    L['n3_blinker'] = [602, 138]
    L['n3_hand_chain'] = [502, 124]                   # the hoist's hand chain: top (at the block) -> the hatch
    L['n3_people_at'] = {'banksman': [292, 240], 'driver': [22, 234]}
    return LA.to8(out)


def build(w):
    w('number/n1_wagon.png', n1_wagon())
    # round 10: a softer, wider falloff that never goes fully black -- the tunnel stays faintly there around
    # the pool (the vault, the far planks, the gap)
    w('number/n1_dark.png', Q.darkness(1280, 720, 640, 360, 70, 310, '#05070A',
                                       levels=(0.0, 0.28, 0.5, 0.66, 0.78, 0.85), squash=0.9, seed=1))
    w('number/n1_glow.png', n1_glow())
    w('number/n1_beam.png', n1_beam())
    w('number/n2_macro.png', n2_macro())
    w('number/n2_glints.png', n2_glints())
    w('number/n3a_macro.png', n3a_macro())
    w('number/flakes.png', flakes_sheet())
    w('number/n3b_hatch.png', n3b_hatch2())
    w('number/n3b_lip.png', n3b_lip())
    w('number/n3b_stack.png', n3b_stack())
    w('number/n3b_tail.png', Q.glow_sprite(64, 48, [(32, 24, 26, 18, (150, 30, 16), 1.4),
                                                    (32, 24, 8, 6, (120, 40, 20), 1.6)], 6.0))
    w('number/n3b_shaft.png', Q.glow_sprite(220, 90, [(110, 70, 90, 50, (80, 52, 18), 1.4)], 6.0))
    w('number/exhaust.png', Q.K.puff_sheet(6, 28, 22, ['#3C4C68', '#4E5F7C', '#64768F'], 4421, grow=(0.2, 0.46),
                                           thin=0.7))
    look = Q.LIGHT_DAWN_B
    # n3b's people (the game's sheets, at the depth their size fits): the banksman beside the hatch signalling the
    # descent, the driver by his cab, smoking
    sb, ib = Q.fig_sheet('worker_a', [('gesture_side', None, False), ('look_side', None, False),
                                      ('idle_side', None, False)], look)
    w('number/n3_banksman.png', sb)
    sd, idd = Q.fig_sheet('worker_b', [('idle_side', None, False), ('look_side', None, False)], look)
    w('number/n3_driver.png', sd)
    L['n3_people'] = {'banksman': ib, 'driver': idd}
    sk, ik = Q.fig_sheet('konrad', [('idle_side', None, False), ('look_side', None, False)], look)
    w('number/n4_konrad.png', sk)
    L['n4_konrad'] = ik
    # people waiting for the first tram (the game's own sheets): a woman with her boy, a worker on early shift
    people = {'mother': ('berlin_mother', [('idle_side', None, False), ('walk_side', None, False)]),
              'child': ('berlin_child', [('idle_side', None, False), ('walk_side', None, False)]),
              'worker': ('worker_b', [('idle_side', None, False), ('walk_side', None, False)])}
    idx = {}
    for key, (cid, rows) in people.items():
        sh_, ix_ = Q.fig_sheet(cid, rows, look)
        w('number/n4_%s.png' % key, sh_)
        idx[key] = ix_
    L['n4_people'] = idx
    L['n4_people_at'] = {'mother': [286, 300], 'child': [300, 300], 'worker': [196, 300]}
