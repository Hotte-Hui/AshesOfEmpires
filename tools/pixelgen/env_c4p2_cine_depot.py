"""env_c4p2_cine_depot -- LS_C4P2_Depot (13 s): Karsk, Monday 17 February 1964, 6.10, before dawn.

  p1 establishing  the locomotive depot under floodlights: the coal heap under the gantry crane, Kolonne 4 (eleven
                   returnees, Western coats and issued quilted vests mixed, every age) shovelling in a line down the
                   heap into two open wagons, a twelfth resting on his shovel; the young guard at a barrel fire;
                   the roundhouse with one lit stall, the water tower, the town's cooling towers far off
  p2 side_on       inside the open stall door of the roundhouse: a locomotive's smokebox front under a work lamp,
                   a fitter oiling the buffer beam, the banner ВОССТАНОВИМ ВМЕСТЕ patched with sacking over the
                   arch; Alexei carries his toolbox under the arch, his breath in the cold
  p3 close         Irina's lit dispatch window from the yard: frost flowers, snow on the sill; inside the samovar,
                   the telephone, Irina at her ledger (looks up when it rings) and the typed order on the sill
Outputs assets/cinematics/c4p2/depot/*.png; anchors in layout.json "depot" (scenes/cinematics/ch4p2_depot/).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_kit as K
import env_c4p2_cine_flat as FL
import env_c4p2_cine_pal as PAL
import env_c4p2_cine_places as PL
import env_c4p2_cine_rig as R
from env_c4p2_cine_kit import GB, Lt, lc, noise, snow_on, tex_noise

PAL_K = PAL.KARSK
L = K.LAYOUT.setdefault('depot', {})

# ------------------------------------------------------------------------------------------------ p1
P1_FIRE = (569, 262)                     # the barrel's mouth (flames stand on it)
P1_MASTS = ((176, 58, 252), (394, 66, 256))
P1_GANG_Y0, P1_GANG_K = 210.0, 0.19      # feet line of the gang down the heap: y = Y0 + (x - 50) * K
P1_DOOR = 518                            # the lit stall door of the roundhouse
P1_VENT = (518, 140)                     # its roof hood: the safety valve's steam bursts out here
CYCLE_FPS = 8.0                          # shovel cycle: 8 frames at 8 fps = 1 s
# Kolonne 4 down the heap: (rig id, x, cycle phase (frames), recolours, mirrored?)
GANG = [
    ('worker_b', 50, 0, {'coat': '#3a4656', 'trouser': '#262a30'}),
    ('babushka', 78, 3, {'coat': '#4a2c2a'}),
    ('berlin_father', 111, 5, {'coat': '#5a4630', 'trouser': '#2a2622'}),
    ('maria', 134, 2, {}),
    ('worker_a', 166, 6, {'coat': '#34402c', 'trouser': '#24281e'}),
    ('berlin_mother', 188, 1, {'coat': '#2e3e5a'}),
    ('clerk', 220, 4, {'coat': '#3e3a44', 'trouser': '#22222a'}),
    ('vendor', 241, 7, {'coat': '#5a3424'}),
    ('porter', 270, 2, {'coat': '#2c3640', 'trouser': '#20242a'}),
    ('worker_b', 298, 5, {'coat': '#4a4232', 'trouser': '#2a2620'}),
    ('child_a', 322, 3, {}),
]
# each one's own footing (px off the heap's general line) and stance (extra lean, extra reach in degrees)
GANG_DY = (2, -4, 5, -2, 1, 6, -3, 3, -5, 2, -1)
GANG_POSE = ((0, 0), (4, 6), (-3, -4), (2, 4), (-2, 0), (5, 8), (0, -6), (3, 4), (-4, -2), (1, 6), (-2, -4))
REST = ('emil', 392, {'coat': '#3a3634'})        # an old man resting on his shovel behind the wagon
GUARD_X = 600                                    # guard_karsk warming at the barrel (faces left)
# the shovel bites the sound tool cuts into c4p2cine_depot (film time; the three nearest shovels)
NEAR_GANG = (8, 9, 10)


def gang_feet(x, i=None):
    return P1_GANG_Y0 + (x - 50) * P1_GANG_K + (GANG_DY[i] if i is not None else 0)


def bites(i, until=5.0):
    """Film times at which shovel i of GANG bites the coal (CONTACT_FRAME of its cycle)."""
    ph = GANG[i][2]
    out = []
    k = 0
    while True:
        t = ((R.CONTACT_FRAME - ph) % 8 + 8 * k) / CYCLE_FPS
        if t >= until:
            break
        out.append(round(t, 3))
        k += 1
    return out


P1_LIGHTS = [
    Lt(176, 60, 240, '#ffe2b4', I=2.4, r=440, spot=((0.02, -1.0, 0.12), 30, 70), wrap=0.2),
    Lt(394, 68, 250, '#ffe2b4', I=2.0, r=420, spot=((-0.32, -1.0, 0.10), 30, 66), wrap=0.2),
    Lt(206, 136, 300, '#ffd49a', I=1.1, r=200, wrap=0.3),
    Lt(P1_FIRE[0], P1_FIRE[1] - 6, 205, '#ff8a34', I=2.6, r=170, wrap=0.35),
    Lt(P1_DOOR, 236, 470, '#ffb468', I=1.3, r=150),
]
P1_AMB = dict(sky='#2a3a58', gnd='#3a4254', amb=0.5)


def p1_plate():
    g = GB()
    PL.sky(g, horizon=190, glow_x=470, glow='#7a5040')
    PL.skyline(g, base=190, z=1500, lit_k=0.7)
    # mid: the roundhouse at the right, the water tower, the sand tower
    PL.water_tower(g, 430, 112, 30, 14, 262, 560)
    PL.roundhouse(g, 448, 660, 264, 176, 500, doors=[(462, 20, 196), (P1_DOOR, 21, 194), (574, 20, 196)],
                  lit_door=P1_DOOR, banner=(486, 180, 552, 188, 'ВОССТАНОВИМ ВМЕСТЕ'))
    # inside the lit stall: the smokebox of a locomotive in the haze, its number plate, a hanging lamp
    cx = P1_DOOR
    g.put(g.ell(cx, 236, 13, 13), '#141210', tex=tex_noise(g, 2, 3, 0.2), z=520, gl=0.4)
    g.put(g.ell(cx, 236, 9, 9), '#1e1a16', z=519, gl=0.6)
    g.put(g.box(cx - 3, 222, cx + 4, 225), '#c8a060', em=lc('#ffd090') * 0.3, z=518)
    g.put(g.box(cx - 18, 254, cx + 18, 258), '#2a1810', z=518)
    g.glow(g.box(cx - 1, 204, cx + 2, 207), '#ffe0a0', 2.0)
    K.ground_light_pool(g, cx, 266, 34, 10, '#ffb060', 0.6)
    # floodlight masts and the gantry crane over the heap
    for (mx, top, base) in P1_MASTS:
        PL.mast(g, mx, top, base, 262)
    PL.gantry(g, 44, 252, 118, 236, 330, trolley_x=206, grab_y=172)
    cab = g.box(236, 128, 256, 146)
    g.put(cab, '#3a2e1c', tex=tex_noise(g, 2, 4, 0.15), z=326)
    g.put(g.box(239, 131, 253, 139), '#2a1a0c', em=lc('#ffb860') * 0.9, z=325)
    g.put(g.ell(247, 134, 2, 2) | g.box(245, 136, 250, 139), '#1a100a', em=lc('#ffb860') * 0.12, z=324)
    g.put(snow_on(cab, 2, 5), '#e2e8ee', n=(0, 0.9, 0.4), z=326)
    # the coal heap: a plateau under the crane, the front slope the gang stands on, down to the wagons
    heap = [(-10, 360), (-10, 178), (20, 172), (70, 176), (120, 170), (170, 178), (215, 186), (262, 204),
            (300, 222), (340, 240), (380, 258), (410, 272), (420, 360)]
    PL.coal_heap(g, heap, 280, snow_k=0.55)
    # the terrace the gang stands on (trodden: lighter, flatter) and their shovelled hollows
    for i, (cid, x, ph, cols) in enumerate(GANG):
        yb = gang_feet(x, i)
        step = g.poly([(x - 13, yb + 3), (x - 9, yb - 1), (x + 10, yb - 1), (x + 14, yb + 3)])
        g.put(step, '#2a2a30', n=(0, 0.8, 0.6), z=276, gl=0.1)
        g.put(g.box(x - 9, yb - 1, x + 10, yb), '#3a3a44', n=(0, 0.9, 0.4), z=275)
        pile = g.ell(x + 15, yb + 1, 6, 3)
        g.put(pile & ~step, '#16161a', z=276, gl=0.3)
    # retaining wall of old sleepers at the foot of the heap
    wall = g.box(250, 270, 430, 300) & ~g.poly(heap) | g.box(330, 286, 430, 300)
    K.planks(g, g.box(250, 272, 340, 300) & ~g.poly(heap), '#2a2018', pw=4, vertical=False, seed=7, z=262)
    # the wagons (the first half full, the second heaped) on the track
    PL.gondola(g, 334, 470, 250, 300, 222, number='61 205', load=0.45, seed=83)
    PL.gondola(g, 478, 624, 250, 300, 222, number='61 218', load=1.0, seed=87)
    # ground: snow, the track under the wagons, footprints to the barrel, a trodden path
    PL.ground(g, 296, 360, 160, tracks=((300, -10, 650, 200),))
    foot = g.box(470, 302, 640, 312) & (noise(g.w, g.h, 2, 5, 1) > 0.55)
    g.mul(foot, 0.82)
    # the barrel fire basket and a crate / bench beside it
    PL.barrel(g, P1_FIRE[0], P1_FIRE[1], 300, 190)
    crate = g.box(536, 288, 552, 300)
    K.planks(g, crate, '#4a3826', pw=4, vertical=False, seed=11, z=192)
    g.put(snow_on(crate, 2, 12), '#e2e8ee', n=(0, 0.9, 0.4), z=192)
    g.put(g.box(539, 284, 547, 288), '#2a2a30', z=191)                      # a tin mug and a bundle
    out = g.final(P1_LIGHTS, PAL_K, spread=0.045, fog='#1a2234', fogz=(350, 1800), fogmax=0.75, **P1_AMB)
    front = out.copy()
    front[..., 3] = np.where(g.z < 235, 255, 0)            # wagons, barrel, ground: drawn over the gang
    return out, front


def p1_glows():
    """Additive: the two floodlight beams through the snow haze, the lamp halos, the crane lamp, the stall door,
    the fire's light (its own sprite: it flickers)."""
    beams = np.zeros((K.VH, K.VW, 4), np.uint8)
    for (mx, top, base), ang in zip(P1_MASTS, (18, -14)):
        b = K.beam_sprite(K.VW, K.VH, mx, top + 6, ang, 230, 22, (70, 58, 40), 6.0, 1.2, 0.55, seed=mx)
        m = b[..., 3] > 0
        beams[m] = np.maximum(beams[m], b[m])
    halos = K.glow_sprite(K.VW, K.VH, [(mx, top + 3, 26, 18, (120, 100, 70), 1.4) for (mx, top, base) in P1_MASTS] +
                          [(206, 134, 14, 10, (80, 64, 40), 1.4), (P1_DOOR, 230, 40, 34, (90, 56, 24), 1.5),
                           (P1_DOOR, 266, 44, 8, (60, 36, 14), 1.5)], 6.0)
    fire = K.glow_sprite(K.VW, K.VH, [(P1_FIRE[0], P1_FIRE[1] - 6, 70, 52, (150, 70, 20), 1.5),
                                      (P1_FIRE[0], 302, 80, 9, (90, 40, 10), 1.5)], 6.0)
    return beams, halos, fire


def gang_sheets(lights):
    """Each member of Kolonne 4: an 8-frame shovel cycle (48 x 56 cells), tinted by the place's light."""
    out = []
    for i, (cid, x, ph, cols) in enumerate(GANG):
        spec, used = K.spec_of(cid, 'worker_b')
        R.strip_props(spec)
        for name, hexc in cols.items():
            K.recolor(spec, name, hexc)
        K.key_light(spec, 'left', up=0.75, front=0.35)
        lean, reach = GANG_POSE[i]
        frames = R.render_set(spec, R.shovel_poses(lean, reach), R.shovel_setup(spec), 48)
        feet = gang_feet(x, i)
        x0, y0 = x - 24, feet - 54
        cells = [K.fig_tint(rg, nm, lights, x0, y0, 250, PAL_K, gain=0.92, wrap=0.45, rim=0.45, **P1_AMB)
                 for rg, nm, J in frames]
        out.append((K.hsheet(cells), x0, int(round(y0))))
    return out


def rest_sheet(lights):
    cid, x, cols = REST
    spec, used = K.spec_of(cid, 'worker_b')
    R.strip_props(spec)
    for name, hexc in cols.items():
        K.recolor(spec, name, hexc)
    K.key_light(spec, 'left', up=0.75, front=0.35)
    frames = R.render_set(spec, R.rest_poses(), R.rest_setup(spec), 48)
    feet = 266
    x0, y0 = x - 24, feet - 54
    cells = [K.fig_tint(rg, nm, lights, x0, y0, 240, PAL_K, gain=1.2, wrap=0.55, rim=0.6, **P1_AMB)
             for rg, nm, J in frames]
    return K.hsheet(cells), x0, y0


def guard_sheet(lights):
    """The young guard warming his hands at the barrel: the cast stream's guard_karsk (rifle slung) in the
    rig's 'warm' work loop, mirrored to face the fire at his left; key from the fire."""
    CH, CB, A, CC = K.rig()
    spec, used = K.spec_of('guard_karsk', 'worker_a')
    K.key_light(spec, 'right', up=0.2, front=0.6)          # mirrored below: the fire lights his left side
    st = dict(spec.style)
    st['work'] = 'warm'
    frames = R.render_set(spec, A.work_side(st), [], 48)
    frames = R.flip_frames(frames)
    feet = 306
    x0, y0 = GUARD_X - 24, feet - 54
    cells = [K.fig_tint(rg, nm, lights, x0, y0, 200, PAL_K, gain=1.15, wrap=0.4, rim=0.8, **P1_AMB)
             for rg, nm, J in frames]
    return K.hsheet(cells), x0, y0, len(frames)


def build_p1(w):
    bg, front = p1_plate()
    w('depot/p1_bg.png', bg)
    w('depot/p1_front.png', front)
    beams, halos, fire = p1_glows()
    w('depot/p1_beams.png', beams)
    w('depot/p1_halos.png', halos)
    w('depot/p1_fireglow.png', fire)
    w('depot/flame.png', K.flame_sheet(8, 18, 30, seed=3))
    w('depot/embers.png', K.ember_sheet(4, 3, 3))
    w('depot/vent_steam.png', K.puff_sheet(8, 40, 34, PAL.K_STEAM[:5], 5, grow=(0.25, 0.5), thin=0.6,
                                           light=(0.0, 0.8), drift=0.2))
    w('depot/valve_jet.png', K.puff_sheet(8, 30, 44, PAL.K_STEAM[1:], 9, grow=(0.2, 0.5), thin=0.45,
                                          light=(0.4, 0.8), drift=0.15))
    gang = gang_sheets(P1_LIGHTS)
    for i, (sh, x0, y0) in enumerate(gang):
        w('depot/gang_%02d.png' % i, sh)
    rs, rx, ry = rest_sheet(P1_LIGHTS)
    w('depot/gang_rest.png', rs)
    gs, gx, gy, gn = guard_sheet(P1_LIGHTS)
    w('depot/guard.png', gs)
    L.update(p1_fire=list(P1_FIRE), p1_masts=[list(m) for m in P1_MASTS], p1_vent=list(P1_VENT),
             p1_gang=[[x0, y0, GANG[i][2]] for i, (sh, x0, y0) in enumerate(gang)], p1_rest=[rx, ry],
             p1_guard=[gx, gy, gn], cycle_fps=CYCLE_FPS, contact_frame=R.CONTACT_FRAME, cell=[48, 56],
             near_gang=list(NEAR_GANG), bites=[bites(i) for i in NEAR_GANG])


# ================================================================================================ p2
P2_FLOOR = 300
P2_DOOR = (168, 472, 112, 74)            # opening x0, x1, springing y, crown y
P2_LAMP = (362, 118)                      # the work lamp inside (hangs from its cable)
P2_WALK = (96, 276)                       # Alexei's feet x at the start / end of p2 (45 px/s, 4 s)
P2_FITTER = (410, 292)
P2_LIGHTS = [
    Lt(P2_LAMP[0], P2_LAMP[1] + 6, 190, '#ffc27a', I=2.6, r=260, wrap=0.25),
    Lt(186, 106, 60, '#ffd8a0', I=1.8, r=260, wrap=0.3),
    Lt(330, 360, 20, '#8aa0c4', I=1.0, r=420, wrap=0.6),
    Lt(620, 60, -80, '#9aaccc', I=0.9, r=700, wrap=0.5),
]
P2_AMB = dict(sky='#4a5a7a', gnd='#3a4458', amb=0.62)


def _arch_mask(g, x0, x1, spring, crown, bottom):
    cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
    rise = spring - crown
    R_ = (hw * hw + rise * rise) / (2 * rise)
    cy = crown + R_
    return (g.box(x0, spring, x1, bottom) | (g.ell(cx, cy, R_, R_) & (g.yy < spring + 1) & (g.yy >= crown))) & \
        (g.xx >= x0) & (g.xx < x1)


def loco_front(g, cx, rail_y, k, z, number='Л 3127', lamp_on=(True, False, True), seed=201):
    """A Soviet freight engine head-on at scale k: smokebox door with hinge straps and central handle, the
    number plate, chimney, the red buffer beam, buffers, coupling hook, three lamps, cylinders and steam pipes at
    the sides, the cab's front windows far behind."""
    def S(v):
        return v * k
    sb_c = (cx, rail_y - S(130))
    r = S(32)
    boiler = g.ell(sb_c[0], sb_c[1], r + S(6), r + S(6))
    g.put(boiler, '#1a1a1c', tex=tex_noise(g, 3, seed, 0.12), z=z + 4, gl=0.35)
    door = g.ell(sb_c[0], sb_c[1], r, r)
    side = (g.xx - sb_c[0]) / r
    up = (sb_c[1] - g.yy) / r
    n = np.stack([np.clip(side, -1, 1) * 0.55, np.clip(up, -1, 1) * 0.55, np.ones_like(side)], -1)
    g.put(door, '#202024', tex=tex_noise(g, 2, seed + 1, 0.1), n=n, z=z, gl=0.5)
    ring = door & ~K.erode(door, 2)
    g.put(ring, '#2e2e34', n=n, z=z - 1, gl=0.7)
    for dy in (-S(14), S(14)):
        g.put(g.box(sb_c[0] - r * 0.9, sb_c[1] + dy - 1, sb_c[0] + r * 0.2, sb_c[1] + dy + 1), '#36363c', z=z - 1,
              gl=0.6)
    g.put(g.ell(sb_c[0], sb_c[1], S(5), S(5)), '#3e3e44', z=z - 2, gl=0.9)
    g.put(g.box(sb_c[0] - 1, sb_c[1] - S(5), sb_c[0] + 1, sb_c[1] + S(5)), '#4a4a52', z=z - 3, gl=0.9)
    pl = g.box(sb_c[0] - S(16), sb_c[1] - S(26), sb_c[0] + S(16), sb_c[1] - S(18))
    g.put(pl, '#18181a', z=z - 2)
    g.put(g.text(number, sb_c[0] - K.VK.vtext(number, 's').shape[1] // 2, sb_c[1] - S(25), 's') & pl, '#d8c8a0',
          z=z - 3)
    ch = g.box(sb_c[0] - S(9), sb_c[1] - r - S(30), sb_c[0] + S(9), sb_c[1] - r + S(2))
    g.put(ch, '#141416', z=z + 2, gl=0.4)
    g.put(g.box(sb_c[0] - S(11), sb_c[1] - r - S(32), sb_c[0] + S(11), sb_c[1] - r - S(28)), '#1e1e22', z=z + 1)
    bb = g.box(cx - S(88), rail_y - S(64), cx + S(88), rail_y - S(42))
    g.put(bb, '#8a2418', tex=tex_noise(g, 3, seed + 2, 0.12), z=z - 6, gl=0.3)
    g.mul(bb & (noise(g.w, g.h, 5, seed + 3, 2) > 0.6), 0.6)
    for bx in (cx - S(62), cx + S(62)):
        g.put(g.box(bx - S(5), rail_y - S(58), bx + S(5), rail_y - S(48)), '#2a2a2e', z=z - 8)
        pad = g.ell(bx, rail_y - S(53), S(12), S(12))
        g.put(pad, '#3a3a40', z=z - 10, gl=0.8)
        g.put(pad & ~K.erode(pad, 1), '#222226', z=z - 10)
    g.put(g.box(cx - S(5), rail_y - S(56), cx + S(5), rail_y - S(40)), '#2a2a2e', z=z - 9, gl=0.6)
    for i, (lx, ly) in enumerate(((cx - S(56), rail_y - S(76)), (cx + S(56), rail_y - S(76)),
                                  (sb_c[0], sb_c[1] - r - S(12)))):
        g.put(g.box(lx - S(8), ly - S(7), lx + S(8), ly + S(7)), '#1c1c20', z=z - 7)
        lens = g.ell(lx, ly, S(5), S(5))
        if lamp_on[i]:
            g.put(lens, '#ffe0a0', em=lc('#ffd890') * 2.2, z=z - 8)
        else:
            g.put(lens, '#2a2a30', z=z - 8, gl=0.9)
    for sx in (-1, 1):
        cyl = g.box(cx + sx * S(64) - S(16), rail_y - S(44), cx + sx * S(64) + S(16), rail_y - S(12))
        g.put(cyl, '#1c1c20', tex=tex_noise(g, 2, seed + 4 + sx, 0.15), z=z + 6, gl=0.4)
        g.put(g.box(cx + sx * S(92) - S(4), rail_y - S(110), cx + sx * S(92) + S(4), rail_y - S(64)), '#18181c',
              z=z + 8)
        g.put(g.box(cx + sx * S(98) - S(10), rail_y - S(114), cx + sx * S(98) + S(10), rail_y - S(110)), '#26262a',
              z=z + 8, gl=0.5)
    return sb_c, r


def p2_plate():
    g = GB()
    x0, x1, spring, crown = P2_DOOR
    opening = _arch_mask(g, x0, x1, spring, crown, P2_FLOOR + 2)
    inside = opening
    g.put(inside, '#2a1e16', tex=tex_noise(g, 9, 3, 0.25), z=420)
    back = g.box(x0, crown, x1, 262) & inside
    K.bricks(g, back, '#3a2418', '#241a14', bw=7, bh=3, seed=5, z=420)
    g.put(g.box(250, 132, 290, 160) & inside, '#3a4a68', em=lc('#5a7096') * 0.35, z=430)        # high window
    g.put((g.box(269, 132, 271, 160) | g.box(250, 145, 290, 147)) & inside, '#1a1410', z=429)
    for (rx, ry, w_, h_, c) in ((186, 170, 38, 54, '#3a2a1e'), (418, 176, 34, 40, '#4a3a2a')):
        rack = g.box(rx, ry, rx + w_, ry + h_) & inside
        K.planks(g, rack, c, pw=4, vertical=True, seed=rx, z=410)
        for tx in range(rx + 3, rx + w_ - 2, 6):
            g.put(g.box(tx, ry + 4, tx + 1, ry + h_ - 10) & inside, '#1c1c20', z=409, gl=0.6)
            g.put(g.box(tx - 1, ry + 4, tx + 2, ry + 7) & inside, '#2a2a30', z=409, gl=0.6)
    g.put(g.box(430, 226, 442, 244) & inside, '#9a2a1e', z=408)                                  # fire bucket
    g.put(g.box(432, 222, 440, 226) & inside, '#6a1e16', z=408)
    notice = g.box(196, 236, 222, 256) & inside
    g.put(notice, '#c8bfa8', tex=tex_noise(g, 2, 9, 0.1), z=407)
    for ly in range(239, 254, 3):
        g.put(g.box(199, ly, 219 - (ly % 5), ly + 1) & notice, '#4a463c', z=406)
    floor = g.poly([(x0, P2_FLOOR + 2), (x1, P2_FLOOR + 2), (372, 262), (268, 262)]) & inside
    g.put(floor, '#2a2622', tex=tex_noise(g, 4, 11, 0.25), n=(0, 0.85, 0.5), z=300)
    pit = g.poly([(282, P2_FLOOR + 2), (358, P2_FLOOR + 2), (334, 262), (306, 262)]) & inside
    g.put(pit, '#0e0c0a', z=301)
    for (a, b) in (((262, P2_FLOOR + 2), (300, 262)), ((378, P2_FLOOR + 2), (340, 262))):
        g.put(g.line([a, b], 1.0) & inside, '#5a6068', n=(0, 0.8, 0.6), z=299, gl=0.9)
    sb_c, r = loco_front(g, 320, 262, 0.62, 360)
    L.update(p2_smokebox=[int(sb_c[0]), int(sb_c[1])], p2_cyl=[[int(320 - 0.62 * 64), 262 - 18],
                                                             [int(320 + 0.62 * 64), 262 - 18]])
    g.put(g.box(P2_LAMP[0], crown, P2_LAMP[0] + 1, P2_LAMP[1]) & inside, '#141414', z=330)
    # the facade: brick with pilasters, the arch ring, the patched banner above, a lamp bracket, a drain pipe
    wall = ~opening
    soot = 0.7 + 0.3 * np.clip((g.yy - 46) / 260.0, 0, 1)
    K.bricks(g, wall, '#6e3626', '#3a3430', bw=10, bh=4, seed=21, z=100, soot=soot)
    ring = K.dilate(opening, 5) & ~opening
    K.bricks(g, ring, '#7e4632', '#443a34', bw=4, bh=6, seed=23, z=99)
    for px_ in (x0 - 34, x1 + 22):
        pil = g.box(px_, 46, px_ + 12, P2_FLOOR + 2)
        K.bricks(g, pil, '#74402c', '#3a3430', bw=6, bh=4, seed=px_, z=96)
        g.put(snow_on(g.box(px_ - 2, 140, px_ + 14, 142), 2, px_), '#dde4ec', z=96)
    ban = (226, 50, 414, 70)
    bm = g.box(*ban)
    K.cloth(g, bm, '#8e2018', 31, folds=0.18, period=13, vertical=True, z=94)
    txt = 'ВОССТАНОВИМ ВМЕСТЕ'
    tw = K.VK.vtext(txt, 'm').shape[1]
    tm = g.text(txt, 320 - tw // 2, 54, 'm') & bm
    g.put(tm, '#efe2c8', z=93)
    tm_full = tm.copy()
    patch = g.poly([(384, 58), (398, 57), (400, 70), (383, 70)])
    K.cloth(g, patch, '#7a6a4c', 33, folds=0.15, period=3, vertical=False, z=92)
    g.put(K.dilate(patch, 1) & ~patch & bm, '#3a2a18', z=92)
    for k_ in range(384, 400, 3):
        g.put(g.box(k_, 56, k_ + 1, 57), '#d8c8a0', z=91)
    tear = g.line([(236, 66), (244, 70)], 0.5)
    g.put(tear & bm, '#2a0c08', z=92)
    for rx_ in (228, 412):
        g.put(g.line([(rx_, 46), (rx_ + (6 if rx_ < 300 else -6), 52)], 0.5), '#1a1a1a', z=93)
    g.put(snow_on(bm, 1, 35), '#e0e6ee', z=93)
    lb = g.box(178, 102, 196, 108)
    g.put(lb, '#1e2024', z=90)
    g.put(g.box(181, 108, 193, 112), '#ffe0b0', em=lc('#ffd8a0') * 1.8, z=89)
    g.put(g.box(184, 96, 186, 102), '#1e2024', z=90)
    g.put(snow_on(lb, 2, 37), '#e6ecf2', z=90)
    dp = g.box(526, 46, 532, P2_FLOOR)
    g.put(dp, '#2a2e34', n=(0.3, 0, 0.95), z=95, gl=0.4)
    for iy in (120, 210):
        g.put(g.box(524, iy, 534, iy + 3), '#22262a', z=94)
    for icx in range(527, 532, 2):
        g.put(g.box(icx, P2_FLOOR - 26, icx + 1, P2_FLOOR - 26 + 6 + (icx % 3) * 3), '#cfe0ea', z=94, gl=0.8)
    plate = g.box(486, 168, 520, 180)
    g.put(plate, '#1e3a5a', z=95)
    g.put(g.text('СТОЙЛО 7', 488, 171, 's') & plate, '#e0e4e8', z=94)
    poster = g.box(560, 150, 596, 196)
    g.put(poster, '#d0c6aa', tex=tex_noise(g, 2, 41, 0.12), z=95)
    g.put(g.box(564, 154, 592, 164) & poster, '#9a2a1e', z=94)
    for ly in range(168, 192, 3):
        g.put(g.box(564, ly, 588 - (ly % 7), ly + 1) & poster, '#4a4438', z=94)
    hose = g.box(84, 196, 112, 232)
    g.put(hose, '#8a2418', z=95)
    g.put(g.box(88, 200, 108, 228), '#6a1c14', z=94)
    g.put(g.text('01', 92, 210, 's') & hose, '#e8dcc4', z=93)
    for (sx, sy, sw) in ((x0 - 40, 46, 60), (x1 + 6, 46, 70)):
        g.put(snow_on(g.box(sx, sy + 98, sx + sw, sy + 100), 2, sx), '#dde4ec', z=97)
    ground = g.box(-2, P2_FLOOR + 2, 642, 360)
    K.snow(g, ground, 41, z=80, col='#d6dee8', shade_col='#8e9aac')
    cinder = g.poly([(x0 - 10, P2_FLOOR + 2), (x1 + 10, P2_FLOOR + 2), (x1 + 40, 330), (x0 - 40, 330)])
    g.put(cinder, '#5a5652', n=(0, 0.9, 0.4), z=79)
    g.put(cinder & (K.hash2(g.xx.astype(np.int64), g.yy.astype(np.int64), 44) > 0.93), '#3a3836', z=79)
    g.put(K.dilate(cinder, 1) & ~cinder & (g.yy > P2_FLOOR + 2), '#aeb8c6', z=79)
    for (a, b) in (((262, P2_FLOOR + 2), (236, 360)), ((378, P2_FLOOR + 2), (404, 360))):
        g.put(g.line([a, b], 1.2), '#4a5058', n=(0, 0.8, 0.6), z=78, gl=0.9)
    K.ground_light_pool(g, 320, P2_FLOOR + 10, 150, 22, '#ffb060', 0.35)
    out = g.final(P2_LIGHTS, PAL_K, spread=0.045, fog='#2a2018', fogz=(300, 900), fogmax=0.35, **P2_AMB)
    inter, lo = p2_interior()
    out[opening] = inter[opening]
    sb = lo.anchors['smokebox']
    L.update(p2_smokebox=[int(sb[0]), int(sb[1])], p2_cyl=[[int(320 - 1.12 * 24), 262 - 34],
                                                         [int(320 + 1.12 * 24), 262 - 34]])
    return out


# ================================================================================================= p2 interior
def p2_interior():
    """The stall behind the arch, painted flat and lit: the back wall's brick with its tall window in the
    dawn, the side walls with a tool board, the sand bin, the workbench and its vice, the roof trusses and the
    smoke hood, the inspection pit between the rails, the engine head-on under the hanging work lamp (its two
    lower lamps lit), a coiled hose; returns RGBA 640 x 360 to be laid into the arch opening."""
    import env_c4p2_cine_loco as LO
    F = FL.Flat(bg='#120c08')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    vx, vy = 320, 196
    bx0, by0, bx1, by1 = 232, 110, 408, 262
    F.fill(F.box(0, 0, 640, 360), '#1e140e')
    back = F.box(bx0, by0, bx1, by1)
    F.fill(back, '#3a2418')
    F.fill(back & (np.mod(yy - by0, 4) == 0), '#2a1a10')
    F.fill(back & (np.mod(xx + (np.floor_divide(yy - by0, 4) % 2) * 4, 8) == 0), '#2a1a10')
    win = F.ell(320, 136, 28, 16) & (F.yy < 136) | F.box(292, 136, 348, 178)
    F.fill(win, '#5a7096')
    F.fill(win & (F.yy > 160), '#7a8aa8')
    F.fill(win & ((np.abs(xx - 320) < 1) | (np.abs(yy - 154) < 1) | (np.abs(xx - 306) < 1) | (np.abs(xx - 334) < 1)),
           '#1a120c')
    F.outline(win, col='#1a120c')
    # side walls converging to the back, roof trusses, the smoke hood
    lw = F.poly([(0, 0), (bx0, by0), (bx0, by1), (0, 360)])
    F.fill(lw, '#2e1e14')
    rw = F.poly([(640, 0), (bx1, by0), (bx1, by1), (640, 360)])
    F.fill(rw, '#34221a')
    for k in range(6):
        t = k / 6.0
        x = bx0 * t
        F.fill(F.line([(x, by0 * t), (x, by1 + (360 - by1) * (1 - t))], 0.5) & lw, '#22160e')
        xr = 640 - (640 - bx1) * t
        F.fill(F.line([(xr, by0 * t), (xr, by1 + (360 - by1) * (1 - t))], 0.5) & rw, '#26180f')
    roof = F.poly([(0, 0), (640, 0), (bx1, by0), (bx0, by0)])
    F.fill(roof, '#1a120c')
    for k in range(5):
        t = (k + 1) / 6.0
        y = by0 * t
        x0_, x1_ = bx0 * t, 640 - (640 - bx1) * t
        F.fill(F.line([(x0_, y), (x1_, y)], 0.8), '#2a1c12')
        F.fill(F.line([(x0_, y), ((x0_ + x1_) / 2, y - 10 * t)], 0.6) | F.line([((x0_ + x1_) / 2, y - 10 * t), (x1_, y)], 0.6),
               '#2a1c12')
    hood = F.poly([(286, 60), (354, 60), (340, 100), (300, 100)])
    F.fill(hood, '#2a2a2e')
    F.fill(hood & FL.edge(hood, 'l', 2), '#4a4a52')
    F.fill(F.box(308, 0, 332, 60), '#1e1e22')
    F.outline(hood, col='#0a0a0c')
    # the floor, the rails and the pit converging to the back
    fl = F.poly([(0, 360), (640, 360), (bx1, by1), (bx0, by1)])
    F.fill(fl, '#2a2622')
    F.fill(fl & (K.hash2(np.floor_divide(xx, 5), np.floor_divide(yy, 3), 3) > 0.8), '#34302a')
    pit = F.poly([(262, 360), (378, 360), (334, by1), (306, by1)])
    F.fill(pit, '#0c0a08')
    F.fill(pit & FL.edge(pit, 'lr', 2), '#4a4038')
    for (a, b) in (((236, 360), (300, by1)), ((404, 360), (340, by1))):
        F.fill(F.line([a, b], 1.2), '#8a9098')
        F.fill(F.line([(a[0], a[1] - 1), (b[0], b[1] - 1)], 0.5), '#c8ced6')
    # left: the tool board with spanners and the red fire bucket, the sand bin
    tb_ = F.poly([(60, 140), (150, 158), (150, 236), (60, 246)])
    F.fill(tb_, '#4a3424')
    for k in range(6):
        tx = 70 + k * 13
        ty = 150 + k * 2.2
        F.fill(F.line([(tx, ty), (tx + 2, ty + 34)], 0.6), '#8a929a')
        F.fill(F.ell(tx, ty, 2.2, 2), '#8a929a')
    F.outline(tb_, col='#1a120c')
    bucket = F.box(166, 214, 182, 236)
    F.fill(bucket, '#9a2a1e')
    F.fill(bucket & FL.edge(bucket, 't'), '#c84a32')
    F.fill(F.text('ПГ', 168, 222, 's') & bucket, '#e8dcc4')
    F.outline(bucket, col='#3a0c08')
    sand = F.poly([(80, 268), (170, 262), (176, 300), (76, 310)])
    F.fill(sand, '#5a4a32')
    F.fill(sand & FL.edge(sand, 't', 3), '#c8a870')
    F.fill(F.text('ПЕСОК', 104, 282, 's') & sand, '#e8dcc4')
    F.outline(sand, col='#1a120c')
    # right: the workbench with its vice and a lamp, a coiled hose on the wall
    wb = F.poly([(470, 240), (600, 230), (600, 246), (470, 254)])
    F.fill(wb, '#5a3e26')
    F.fill(wb & FL.edge(wb, 't'), '#8a6a44')
    F.fill(F.box(486, 250, 490, 296) | F.box(590, 244, 594, 300), '#3a2818')
    vice = F.box(560, 220, 576, 232)
    F.fill(vice, '#3a4048')
    F.fill(vice & FL.edge(vice, 't'), '#8a929a')
    F.outline(wb | vice, col='#1a120c')
    hose = F.ell(530, 170, 18, 18) & ~F.ell(530, 170, 11, 11)
    F.fill(hose, '#2a2a2e')
    F.fill(hose & (np.mod(xx + yy, 5) == 0), '#4a4a52')
    F.outline(hose, col='#0a0a0c')
    # the engine head-on under the lamp, its two lower lamps lit
    lo = LO.FrontLoco(F, 320, 262, m=24.0, number='3127', star=True, lamps=True).paint()
    # the work lamp hanging in front of it: enamel shade, bulb, its stepped pool on the engine and the floor
    lx, ly = P2_LAMP
    F.fill(F.box(lx, 0, lx + 1, ly - 6), '#141414')
    shd = F.poly([(lx - 10, ly), (lx + 11, ly), (lx + 6, ly - 7), (lx - 5, ly - 7)])
    F.fill(shd, '#2a3a30')
    F.fill(shd & FL.edge(shd, 't'), '#5a7a64')
    F.fill(F.box(lx - 6, ly, lx + 7, ly + 3), '#fff0c0')
    F.pool(F.box(0, 0, 640, 360) & ~win, lx - 20, ly + 110, 210, 160, steps=((1.0, 1.1), (0.6, 1.32), (0.3, 1.6)),
           col='#ffb860')
    F.pool(fl, lx - 30, 300, 130, 40, steps=((1.0, 1.15), (0.5, 1.35)), col='#ffb860')
    # the dawn's cold from the back window on the floor in front of the back wall
    F.tint(F.poly([(286, by1), (354, by1), (372, 290), (268, 290)]) & fl, '#7a8aa8', 0.18)
    return F.opaque(), lo




def p2_glows():
    lamp = K.glow_sprite(K.VW, K.VH, [(P2_LAMP[0], P2_LAMP[1] + 4, 90, 110, (110, 70, 26), 1.5),
                                      (P2_LAMP[0], P2_LAMP[1] + 4, 16, 10, (160, 120, 60), 1.4)], 6.0)
    beam = K.beam_sprite(K.VW, K.VH, P2_LAMP[0], P2_LAMP[1] + 4, -6, 170, 26, (60, 40, 16), 6.0, 1.0, 0.5, seed=7)
    door = K.glow_sprite(K.VW, K.VH, [(187, 110, 30, 22, (80, 60, 34), 1.5)], 6.0)
    return lamp, beam, door


def alexei_toolbox_sheet():
    """Alexei's walk with the toolbox (the in-game stride: 8 frames, 4.5 px per frame), lit by the stall."""
    spec, used = K.spec_of('alexei')
    K.key_light(spec, 'right', up=0.45, front=0.4)
    frames = R.render_set(spec, R.toolbox_poses(spec.style), R.toolbox_setup(spec), 48)
    mid = (P2_WALK[0] + P2_WALK[1]) / 2
    x0, y0 = mid - 24, P2_FLOOR - 54
    cells = [K.fig_tint(rg, nm, P2_LIGHTS, x0, y0, 98, PAL_K, gain=1.0, wrap=0.4, rim=1.0, **P2_AMB)
             for rg, nm, J in frames]
    return K.hsheet(cells)


def fitter_sheet():
    """A fitter at the engine's right cylinder with an oil can (3 frames: the can tips and pours)."""
    spec, used = K.spec_of('worker_a')
    R.strip_props(spec)
    K.recolor(spec, 'coat', '#2a2c30')
    K.key_light(spec, 'left', up=0.6, front=0.2)
    poses = []
    for i, (an, tilt) in enumerate((((64.0, 34.0), 0), ((68.0, 44.0), 1), ((66.0, 40.0), 1))):
        poses.append(dict(bob=0, lean=8.0, stoop=6.0, foot_n=(4.0, 0.0, 0), foot_f=(-3.0, 0.0, 0), arm_n=an,
                          arm_f=(30.0, 40.0), face='base', phase=i, dx=0.0, lag=0.0, bounce=0, hand_n='fist',
                          hand_f='fist', c4p2_oil=1 + tilt))

    def oil_hook(fr, J, P, spec_):
        x, y = J['wr_n']
        R._line(fr, spec_, (x - 1, y), (x + 2, y + 2), 1.4, 'c4p2_steel', name='can')
        tip = (x + 6, y + (1 if P['c4p2_oil'] == 1 else 4))
        R._line(fr, spec_, (x + 2, y + 1), tip, 0.4, 'c4p2_steel', name='spout')
    R._mats(spec)
    frames = R.flip_frames(R.render_set(spec, poses, [('front', oil_hook)], 48))
    x0, y0 = P2_FITTER[0] - 24, P2_FITTER[1] - 54
    return K.hsheet([K.fig_tint(rg, nm, P2_LIGHTS, x0, y0, 300, PAL_K, gain=1.0, wrap=0.4, rim=1.2, **P2_AMB)
                     for rg, nm, J in frames]), x0, y0


def build_p2(w):
    w('depot/p2_bg.png', p2_plate())
    lamp, beam, door = p2_glows()
    w('depot/p2_lampglow.png', lamp)
    w('depot/p2_beam.png', beam)
    w('depot/p2_doorglow.png', door)
    w('depot/p2_alexei.png', alexei_toolbox_sheet())
    fs, fx, fy = fitter_sheet()
    w('depot/p2_fitter.png', fs)
    w('depot/breath.png', K.puff_sheet(6, 16, 12, PAL.K_STEAM[2:], 13, grow=(0.2, 0.5), thin=0.7, light=(0.5, -0.6),
                                       drift=0.35))
    w('depot/cock_steam.png', K.puff_sheet(8, 36, 26, PAL.K_STEAM[1:5], 17, grow=(0.2, 0.55), thin=0.6,
                                           light=(0.0, -0.8), drift=-0.2))
    L.update(p2_floor=P2_FLOOR, p2_walk=list(P2_WALK), p2_lamp=list(P2_LAMP), p2_fitter=[fx, fy],
             p2_door=list(P2_DOOR))


# ================================================================================================ p3
P3_WIN = (150, 74, 490, 270)              # outer frame of the window (x0, y0, x1, y1)
P3_TRANSOM = 104                          # the top lights' bar -- above Irina's head
P3_MULL = 400                             # the mullion -- right of her, the samovar's pane beyond
P3_IRINA_AT = (226, 112)                  # top-left of Irina's bust (112 x 152 with her jacket continued)
P3_PHONE = (194, 210)
P3_SAMOVAR = (446, 200)
P3_DESK = 224


def p3_flat():
    """(plate, overlay): the dispatch office's window close, from the yard: the ochre plaster wall with its bare
    brick, cracks and cornice, the sign, the lamp bracket, icicles; inside, the room (shelf of ledgers, wall clock,
    calendar, the green lamp, the wall telephone, the samovar in the right pane); the overlay carries what is in
    front of Irina: the desk with the ledger and the typed order, the cotton wool between the panes, the frames,
    the transom and mullion (both clear of her face), the frost."""
    F = FL.Flat(bg='#000000')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    x0, y0, x1, y1 = P3_WIN
    wall = F.box(0, 0, 640, 360)
    F.fill(wall, '#a88a52')
    F.fill(wall & (K.hash2(np.floor_divide(xx, 22), np.floor_divide(yy, 18), 51) > 0.8), '#9e8048')
    F.fill(wall & (np.mod(yy, 30) == 0) & (K.hash2(np.floor_divide(xx, 40), yy, 52) > 0.5), '#94784a')
    for pts in (((520, 170), (566, 160), (590, 196), (572, 236), (528, 228)), ((60, 262), (100, 250), (118, 292), (76, 300))):
        bare = F.poly(list(pts))
        F.fill(bare, '#8a4a34')
        F.fill(bare & (np.mod(yy, 5) == 0), '#5a5048')
        F.fill(bare & (np.mod(xx + (np.floor_divide(yy, 5) % 2) * 5, 10) == 0), '#5a5048')
        F.outline(bare, col='#c8aa70')
    F.fill(F.line([(500, 120), (512, 140), (506, 168), (520, 190)], 0.5) | F.line([(100, 90), (108, 120), (104, 140)], 0.5),
           '#5a4a30')
    corn = F.box(0, 30, 640, 50)
    F.fill(corn, '#8e744a')
    F.fill(corn & FL.edge(corn, 'b', 2), '#5a4830')
    F.fill(F.box(0, 30, 640, 34), '#e2e8f0')
    sign = F.box(520, 96, 624, 112)
    F.fill(sign, '#1e3a5a')
    F.fill(F.text('ДИСПЕТЧЕРСКАЯ', 524, 101, 's') & sign, '#e8ecf0')
    F.outline(sign, col='#0a1a2a')
    br = F.box(312, 52, 328, 58)
    F.fill(br, '#2a2a2e')
    F.fill(F.box(318, 40, 322, 52), '#2a2a2e')
    F.fill(F.box(314, 58, 326, 61), '#ffe8b0')
    F.fill(F.box(312, 50, 328, 52), '#e2e8f0')
    # the room inside
    inner = F.box(x0 + 10, y0 + 10, x1 - 10, y1 - 12)
    F.fill(inner, '#3e3226')
    F.fill(inner & F.box(0, 0, 640, y0 + 70), '#4a3e2e')
    for k in range(0, 640, 22):
        F.fill(inner & F.box(k, y0 + 70, k + 1, y1), '#34291e')
    shelf = F.box(166, 134, 226, 138)
    F.fill(shelf, '#3a2a1c')
    for k, bx_ in enumerate(range(168, 224, 5)):
        F.fill(F.box(bx_, 116 + (bx_ % 3), bx_ + 4, 134), ['#5a2a20', '#2a3a4a', '#4a4a2a'][k % 3])
    ck = F.ell(370, 128, 11, 11)
    F.fill(ck, '#e6dcc4')
    F.outline(ck, col='#2a1e14')
    F.fill(F.line([(370, 128), (370, 120)], 0.5) | F.line([(370, 128), (375, 131)], 0.5), '#1a1410')
    cal = F.box(412, 116, 440, 152)
    F.fill(cal, '#d8cdb2')
    F.fill(F.box(412, 116, 440, 124), '#9a2a1e')
    F.fill(F.text('ФЕВ', 418, 118, 's') & cal, '#efe4cc')
    for ry in range(128, 150, 4):
        for rx in range(415, 438, 4):
            F.fill(F.box(rx, ry, rx + 2, ry + 1), '#4a4436')
    px_, py_ = P3_PHONE
    ph = F.box(px_ - 10, py_ - 20, px_ + 10, py_ + 6)
    F.fill(ph, '#2a1e14')
    F.fill(F.box(px_ - 7, py_ - 26, px_ - 3, py_ - 20) | F.box(px_ + 3, py_ - 26, px_ + 7, py_ - 20), '#c8a050')
    F.fill(F.ell(px_, py_ - 6, 5, 5), '#d8cdb2')
    F.fill(F.box(px_ + 10, py_ - 16, px_ + 16, py_), '#141416')
    F.outline(ph, col='#0a0806')
    sx, sy = P3_SAMOVAR
    body = F.ell(sx, sy + 8, 16, 20)
    F.fill(body, '#b07a2e')
    F.fill(body & (F.xx > sx + 4), '#e0b060')
    F.fill(body & (F.xx < sx - 8), '#7a5020')
    F.fill(F.box(sx - 4, sy - 22, sx + 4, sy - 10), '#8a5a22')
    F.fill(F.box(sx - 10, sy + 26, sx + 10, sy + 32), '#7a4e1e')
    F.fill(F.box(sx - 3, sy + 12, sx + 14, sy + 14), '#6a441a')
    F.fill(F.ell(sx, sy - 26, 6, 4), '#d8c8b4')
    F.outline(body, col='#3a2408')
    lamp = F.poly([(250, 96), (278, 96), (286, 108), (242, 108)])
    F.fill(lamp, '#1e5a3a')
    F.fill(lamp & FL.edge(lamp, 't'), '#4a8a6a')
    F.fill(F.box(262, 78, 264, 96), '#1a1a1a')
    F.fill(F.box(248, 108, 280, 110), '#fff0c0')
    F.pool(inner, 264, 150, 180, 120, steps=((1.0, 1.1), (0.55, 1.3), (0.28, 1.5)), col='#ffcf8a')
    plate = F.opaque()
    # the overlay: what stands in front of Irina
    G = FL.Flat(bg='#000000')
    a = np.zeros((360, 640), bool)
    desk = G.box(x0 + 10, P3_DESK, x1 - 10, y1 - 12)
    G.fill(desk, '#4a3220')
    G.fill(desk & (np.mod(yy - P3_DESK, 6) == 0), '#3a2618')
    G.fill(G.box(x0 + 10, P3_DESK, x1 - 10, P3_DESK + 3), '#2a6a4a')
    led = G.poly([(300, P3_DESK + 4), (372, P3_DESK + 4), (380, P3_DESK + 16), (296, P3_DESK + 16)])
    G.fill(led, '#e2d8bc')
    for ly in range(P3_DESK + 6, P3_DESK + 15, 2):
        G.fill(G.box(306, ly, 370, ly + 1) & led, '#8a8070')
    G.outline(led, col='#6a6050')
    order = G.poly([(206, P3_DESK + 22), (264, P3_DESK + 20), (266, P3_DESK + 32), (204, P3_DESK + 34)])
    G.fill(order, '#ece4cc')
    for k in range(5):
        G.fill(G.box(210, P3_DESK + 23 + k * 2, 254 - (k * 7) % 13, P3_DESK + 24 + k * 2) & order, '#2a2620')
    G.fill(G.ell(250, P3_DESK + 28, 4, 3) & ~G.ell(250, P3_DESK + 28, 2, 1.5) & order, '#7a2a5a')
    G.outline(order, col='#8a8470')
    wool = G.box(x0 + 10, y1 - 18, x1 - 10, y1 - 12)
    G.fill(wool, '#e6e6e0')
    G.fill(wool & (K.hash2(xx, yy, 65) > 0.6), '#c8ccd4')
    for fx_ in (210, 330, 440):
        G.fill(G.box(fx_, y1 - 18, fx_ + 4, y1 - 15), '#c84a3a')
    a |= desk | led | order | wool
    frame_o = G.box(x0, y0, x1, y1)
    glass = G.box(x0 + 8, y0 + 8, x1 - 8, y1 - 8)
    fr = frame_o & ~glass
    bars = G.box(P3_MULL - 3, y0, P3_MULL + 3, y1) | G.box(x0, P3_TRANSOM - 3, x1, P3_TRANSOM + 3)
    G.fill(fr | bars, '#3e5a46')
    G.fill((fr | bars) & (np.mod(xx, 9) == 0), '#34503c')
    G.fill((fr | bars) & FL.edge(fr | bars, 't'), '#6a8a72')
    G.outline(frame_o, col='#1a2a1e')
    a |= fr | bars
    gl_ = glass & ~bars
    fern = gl_ & (((np.abs(np.sin((xx - x0) * 0.6 + (yy - y0) * 0.5)) > 0.84) &
                   (np.minimum(xx - x0, yy - y0) < 26 - 0.18 * np.maximum(xx - x0, yy - y0))) |
                  ((np.abs(np.sin((x1 - xx) * 0.55 + (y1 - yy) * 0.45)) > 0.86) &
                   (np.minimum(x1 - xx, y1 - yy) < 22 - 0.16 * np.maximum(x1 - xx, y1 - yy))))
    G.fill(fern, '#d8e6f0')
    a |= fern
    refl = gl_ & G.line([(x0 + 40, y0 + 40), (x0 + 24, y0 + 90)], 1.0)
    G.fill(refl, '#e8eef4')
    a |= refl
    sill = G.box(x0 - 8, y1, x1 + 8, y1 + 8)
    G.fill(sill, '#6a6460')
    G.fill(sill & FL.edge(sill, 't', 4), '#e8eef4')
    lint = G.box(x0 - 10, y0 - 8, x1 + 10, y0)
    G.fill(lint, '#9a7e4a')
    G.fill(lint & FL.edge(lint, 't', 3), '#e8eef4')
    a |= sill | lint
    for icx in range(x0 - 6, x1 + 8, 7):
        ln = 3 + int(K.hash2(icx, 1, 77) * 10)
        ic = G.poly([(icx, y0), (icx + 3, y0), (icx + 1.5, y0 + ln)])
        G.fill(ic, '#d8e6f0')
        a |= ic
    return plate, G.rgba(a)


def irina_sheet():
    """Irina's dialogue bust graded to her lamp (warm from the left) and the yard's cold light: f 0 at her
    ledger (neutral), f 1 the telephone has rung (surprised); her jacket continued below the cut."""
    import env_c4p2_cine_busts as BU
    out = []
    for ex in ('neutral', 'surprised'):
        b = BU.grade(BU.bust('irina', ex), mul=(1.06, 0.98, 0.86), rim=('left', (255, 214, 150)))
        out.append(BU.extend(b, 40, buttons=True, open_front=False, spread=0.15))
    return K.hsheet(out)


def build_p3(w):
    plate, over = p3_flat()
    w('depot/p3_bg.png', plate)
    w('depot/p3_over.png', over)
    w('depot/p3_irina.png', irina_sheet())
    w('depot/p3_lampglow.png', K.glow_sprite(K.VW, K.VH, [(264, 112, 60, 46, (90, 60, 20), 1.5),
                                                          (264, 110, 16, 6, (120, 90, 40), 1.4)], 8.0))
    w('depot/samovar_steam.png', K.puff_sheet(8, 20, 24, PAL.K_STEAM[2:], 19, grow=(0.2, 0.5), thin=0.7,
                                              light=(-0.5, -0.6), drift=0.15))
    x0, y0, x1, y1 = P3_WIN
    L.update(p3_win=list(P3_WIN), p3_irina_at=list(P3_IRINA_AT), p3_irina_cell=112, p3_phone=list(P3_PHONE),
             p3_samovar=list(P3_SAMOVAR), p3_glass=[x0 + 8, y0 + 8, x1 - 8, y1 - 8])


def build(w):
    build_p1(w)
    build_p2(w)
    build_p3(w)
