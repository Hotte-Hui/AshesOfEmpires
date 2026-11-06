"""env_c4p2_cine_show -- LS_C4P2_Book b4: the depot showcase under floodlights (owner: cine stream, round 10).

Karsk, Tuesday evening, the show for the Swedish visitor: the polished green engine with red ribbons and a fir
garland on the dressed track, the welcome banner on its poles and the bunting between the floodlight masts, the
reception table with bread and salt on an embroidered towel and the samovar, the works band in two rows round
its drum, the depot chief and a woman with the bread, a few workers in their Sunday caps at the back, the press
at the right (Ekdahl with his notebook, the photographer, the minder lighting a cigarette), Alexei in the left
foreground -- and at the far right the tarpaulin fence, lit from behind, with Kolonne 4's shadows shovelling on
it.  The swept platform is painted as slabs with snow in the joints and footprints, the floodlights as stepped
pools; every figure stands on its own contact shadow.  Painted flat (env_c4p2_cine_flat), the engine by
env_c4p2_cine_loco, the people on the rig (env_c4p2_cine_people).  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K
import env_c4p2_cine_loco as LO
import env_c4p2_cine_people as PP
import env_c4p2_cine_rig as R

RAIL = 262                       # the dressed track's rail top
EDGE = 270                       # the platform's edge (curb) below the track
B4_TARP = (520, 640, 150, 262)   # the tarpaulin fence (x0, x1, top, bottom): Kolonne 4's shadows behind it
MATCH_T = (10.05, 10.95)         # b4: the minder strikes the match (flare) and lights up
MARCH_T0 = 9.15                  # the band strikes up (c4p2cine_band starts here)
MARCH_BPM = 112.0
WARM = (1.08, 0.98, 0.84)        # the floodlights' sodium on the people
COOL = (0.78, 0.84, 1.0)
RIM = (255, 214, 150)
# (key, cid, instrument, x, sole y, mirrored): two rows round the bass drum, the conductor in front
BAND = (('band_0', 'conductor', 'trumpet', 212, 290, False), ('band_1', 'worker_a', 'trombone', 240, 290, False),
        ('band_2', 'conductor', 'helicon', 270, 291, True), ('band_3', 'border_officer', 'horn', 196, 304, False),
        ('band_4', 'porter', 'bassdrum', 232, 305, False), ('band_5', 'conductor', 'snare', 286, 304, True))
EXTRAS = (('extra_0', 'clerk', 70, 300, False, 'left'), ('extra_1', 'babushka', 98, 302, False, 'left'),
          ('extra_2', 'worker_b', 340, 286, True, 'left'), ('extra_3', 'worker_a', 364, 284, True, 'right'),
          ('extra_4', 'photographer', 432, 300, True, 'right'), ('extra_5', 'guard_karsk', 500, 290, True, 'right'))
PRESS = (('ekdahl', 'journalist', 410, 302, True), ('minder', 'press_officer', 462, 304, True))
ALEXEI = (146, 312)


def plate():
    F = FL.Flat(bg='#05070c')
    sky = F.box(0, 0, 640, 214)
    F.grad(sky, 0, 214, '#04060b', '#1a2236', steps=6)
    # the town: low blocks with lit windows, the cooling towers with their plumes lit from below
    for (x0, x1, top) in ((0, 70, 186), (64, 120, 176), (300, 380, 182), (372, 430, 170), (424, 520, 188),
                          (560, 640, 178)):
        b = F.box(x0, top, x1, 214)
        F.fill(b, '#0c111c')
        F.fill(b & FL.edge(b, 't'), '#1a2232')
        for wy in range(top + 5, 210, 7):
            for wx in range(x0 + 4, x1 - 3, 7):
                if K.hash2(wx, wy, 7) > 0.62:
                    F.fill(F.box(wx, wy, wx + 2, wy + 3), '#e0a050' if K.hash2(wx, wy, 8) > 0.3 else '#8a6a40')
    for (cx, w) in ((170, 20), (232, 24)):
        pts = []
        for k in range(13):
            t = k / 12.0
            y = 214 - t * 96
            hw = w * (1.0 - 0.42 * math.sin(math.pi * min(1.0, t * 1.25)) ** 0.8) if t < 0.8 else w * (0.66 + 0.1 * (t - 0.8) / 0.2)
            pts.append((cx - hw, y))
        tw = F.poly(pts + [(2 * cx - x, y) for (x, y) in reversed(pts)])
        F.fill(tw, '#0e1420')
        F.fill(tw & (F.xx < cx - w * 0.25), '#151d2e')
        F.fill(tw & FL.edge(tw, 't'), '#2a3044')
        F.outline(tw, col='#070a10', sides='lr')
        for (px, py, r) in ((cx - 4, 112, 12), (cx + 6, 100, 15), (cx - 2, 86, 17), (cx + 12, 70, 19), (cx + 26, 58, 18)):
            pf = F.ell(px, py, r, r * 0.8)
            F.fill(pf, '#2c2c38')
            F.fill(pf & ~F.ell(px + 2, py + 3, r, r * 0.8), '#3c3a46')
            F.fill(pf & (F.yy > py + r * 0.3) & (py > 95), '#4a3a34')
    # floodlight masts (lattice) with their lamp clusters
    for mx in (112, 590):
        mast = F.box(mx - 3, 58, mx + 3, RAIL)
        F.fill(mast, '#1a1e26')
        for y in range(60, RAIL, 8):
            F.fill(F.line([(mx - 3, y), (mx + 3, y + 8)], 0.5) | F.line([(mx + 3, y), (mx - 3, y + 8)], 0.5),
                   '#2c323e')
        head = F.box(mx - 10, 50, mx + 10, 60)
        F.fill(head, '#20242c')
        for k in range(4):
            F.fill(F.box(mx - 8 + k * 5, 52, mx - 5 + k * 5, 56), '#fff4d0')
        F.outline(head, col='#0a0c10')
    # bunting between the masts
    for i in range(46):
        u = i / 45
        x = 112 + (590 - 112) * u
        y = 70 + 30 * math.sin(math.pi * u)
        F.fill(F.poly([(x - 3, y), (x + 3, y), (x, y + 6)]), ['#b02a1e', '#e0d8c0', '#2a4a7a'][i % 3])
    F.fill(F.line([(112, 70), (351, 100), (590, 70)], 0.4), '#2a2a2a')
    # the welcome banner on its two poles
    ban = F.box(150, 112, 330, 130)
    F.fill(ban, '#8e2018')
    for k in range(0, 180, 12):
        F.fill(ban & F.box(150 + k, 112, 152 + k, 130), '#6e1410')
    F.fill(ban & FL.edge(ban, 't'), '#b8342a')
    txt = 'ДОБРО ПОЖАЛОВАТЬ'
    tw = K.VK.vtext(txt, 'm').shape[1]
    F.fill(F.text(txt, 240 - tw // 2, 117, 'm') & ban, '#f0e4c8')
    F.outline(ban, col='#3a0806')
    for px in (148, 330):
        F.fill(F.box(px, 108, px + 2, RAIL), '#3a3a3e')
    # the dressed track: sleepers in swept snow, the rails
    bed = F.box(0, RAIL - 2, 640, EDGE)
    F.fill(bed, '#2a2a30')
    for x in range(0, 640, 11):
        F.fill(F.box(x, RAIL + 1, x + 7, EDGE - 1), '#3a2c22')
    F.fill(F.box(0, RAIL - 1, 640, RAIL + 1), '#8a929c')
    F.fill(F.box(0, RAIL - 1, 640, RAIL), '#c8d0d8')
    # the show engine
    lo = LO.SideLoco(F, 34, RAIL, m=23.0, facing=-1, kind='show', number='Л-1964', crank=1.2, snow=False,
                     lit=-1).paint().tender(coal=True, number=None).finish()
    LO.ribbons(F, lo)
    # the tarpaulin fence at the right, lit from behind (Kolonne 4 shovels behind it)
    tx0, tx1, ty0, ty1 = B4_TARP
    tarp = F.box(tx0, ty0, tx1, ty1)
    F.fill(tarp, '#6a6a50')
    for k, x in enumerate(range(tx0, tx1, 9)):
        F.fill(tarp & F.box(x, ty0, x + 3, ty1), '#5a5a42' if k % 2 else '#76765a')
    F.pool(tarp, (tx0 + tx1) / 2 + 20, ty0 + 60, 90, 80, steps=((1.0, 1.1), (0.55, 1.25)), col='#ffd890')
    for x in range(tx0, tx1 + 1, 40):
        pole = F.box(x, ty0 - 10, x + 3, ty1)
        F.fill(pole, '#3a2a1c')
        F.fill(pole & FL.edge(pole, 'l'), '#5a4430')
    F.fill(F.line([(tx0, ty0), (tx1, ty0 + 3)], 0.6), '#2a2418')
    F.fill(tarp & FL.edge(tarp, 't', 2), '#dfe6ee')
    # the platform: curb with its white line, slabs in perspective, snow in the joints, footprints
    curb = F.box(0, EDGE, 640, EDGE + 5)
    F.fill(curb, '#7a7e86')
    F.fill(F.box(0, EDGE, 640, EDGE + 1), '#c8ccd4')
    F.fill(F.box(0, EDGE + 2, 640, EDGE + 3), '#e8e8e0')
    plat = F.box(0, EDGE + 5, 640, 360)
    F.fill(plat, '#40444e')
    ys = [EDGE + 5]
    while ys[-1] < 360:
        ys.append(ys[-1] + max(6, int((ys[-1] - EDGE) * 0.24)))
    for k, y in enumerate(ys):
        F.fill(F.box(0, y, 640, y + 1) & plat, '#33363e')
        F.fill(F.box(0, y + 1, 640, y + 2) & plat, '#4a4e58')
        if k + 1 < len(ys):
            for x in range(-400, 1040, 58):
                xa = 320 + (x - 320) * (1 + (y - EDGE) * 0.012)
                xb = 320 + (x - 320) * (1 + (ys[k + 1] - EDGE) * 0.012)
                F.fill(F.line([(xa, y + 1), (xb, ys[k + 1])], 0.45) & plat, '#363940')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    drift = plat & ((yy - EDGE) < 9) & (K.hash2(np.floor_divide(xx, 6), yy, 3) > 0.3)
    F.fill(drift, '#aeb8c6')
    F.fill(drift & (K.hash2(xx, yy, 4) > 0.7), '#d4dce6')
    for y in ys:
        jm = plat & (yy == y) & (K.hash2(np.floor_divide(xx, 9), yy, 5) > 0.55)
        F.fill(jm, '#8a94a4')
    for k in range(40):
        fx = 10 + K.hash2(k, 1, 9) * 620
        fy = EDGE + 8 + K.hash2(k, 2, 9) * 36
        F.fill(F.box(fx, fy, fx + 3, fy + 1) & plat, '#2a2c32')
    # the reception table: white cloth, bread and salt on the embroidered towel, the samovar, glasses
    tb = F.box(36, 280, 110, 296)
    F.fill(tb, '#e8e4dc')
    F.fill(tb & FL.edge(tb, 't', 2), '#fbf8f2')
    F.fill(F.box(36, 292, 110, 296), '#c8c2b6')
    F.fill(F.box(44, 286, 66, 292), '#f0e8d8')
    F.fill(F.box(44, 289, 66, 290), '#b02a1e')
    loaf = F.ell(55, 280, 10, 5)
    F.fill(loaf, '#b8742e')
    F.fill(loaf & (F.yy < 278), '#d8964a')
    F.fill(F.ell(55, 276, 2, 1), '#f0f0e8')
    F.outline(loaf, col='#4a2a0e')
    sam = F.ell(90, 270, 7, 10)
    F.fill(sam, '#b07a2e')
    F.fill(sam & (F.xx > 92), '#e8b85a')
    F.fill(F.box(88, 258, 92, 262), '#6a4a14')
    F.outline(sam, col='#3a2408')
    for gx in (74, 80):
        F.fill(F.box(gx, 274, gx + 3, 280), '#c8d4d8')
    for lx in (38, 106):
        F.fill(F.box(lx, 296, lx + 2, 304), '#2a2420')
    # the floodlights on the platform: stepped warm pools (the band at their centre)
    F.pool(plat | curb | bed, 250, 296, 250, 56, steps=((1.0, 1.18), (0.62, 1.34), (0.32, 1.5)), col='#ffc880')
    F.pool(plat | curb, 450, 300, 120, 30, steps=((1.0, 1.15), (0.5, 1.3)), col='#ffc880')
    F.pool(plat | curb, 90, 300, 90, 26, steps=((1.0, 1.12), (0.5, 1.24)), col='#ffc880')
    # contact shadows of everybody standing (the sprites stand on them)
    for (key, cid, kind, x, base, fl) in BAND:
        PP.shadow(F, x, base, 12 if kind in ('bassdrum', 'helicon') else 9)
    for (key, cid, x, base, fl, side) in EXTRAS:
        PP.shadow(F, x, base, 9)
    for (key, cid, x, base, fl) in PRESS:
        PP.shadow(F, x, base, 9)
    PP.shadow(F, ALEXEI[0], ALEXEI[1], 10)
    return F.opaque(), lo


def glows():
    beams = np.zeros((K.VH, K.VW, 4), np.uint8)
    for (mx, ang) in ((112, 18), (590, -16)):
        b = K.beam_sprite(K.VW, K.VH, mx, 58, ang, 270, 20, (64, 54, 38), 6.0, 1.2, 0.4, seed=mx)
        m = b[..., 3] > 0
        beams[m] = np.maximum(beams[m], b[m])
    halos = K.glow_sprite(K.VW, K.VH, [(112, 54, 22, 14, (130, 110, 80), 1.4), (590, 54, 22, 14, (130, 110, 80), 1.4),
                                       (580, 200, 70, 60, (40, 34, 20), 1.6)], 6.0)
    return beams, halos


def people():
    out = []
    for (key, cid, kind, x, base, fl) in BAND:
        sh, n, w = PP.sheet(cid, R.band_poses(kind), R.band_setup, 48, fl,
                            key='left' if x > 250 else 'right', mul=WARM, rim=RIM, standin='conductor',
                            recolor={'coat': ['#1e2a3a', '#26303e', '#1a2430'][len(out) % 3]})
        x0, y0 = PP.cell_xy(x, base, 48)
        out.append((key, sh, x0, y0, n, w))
    for (key, cid, x, base, fl, side) in EXTRAS:
        sh, n, w = PP.idle(cid, fl, key=side, mul=WARM, rim=RIM)
        x0, y0 = PP.cell_xy(x, base, 32)
        out.append((key, sh, x0, y0, n, w))
    cid = 'journalist'
    sh, n, w = PP.idle(cid, True, key='left', mul=WARM, rim=RIM)
    x0, y0 = PP.cell_xy(PRESS[0][2], PRESS[0][3], 32)
    out.append(('ekdahl', sh, x0, y0, n, w))
    sh, n, w = PP.sheet('press_officer', R.match_poses(), R.match_setup, 48, True, key='left', mul=WARM,
                        rim=RIM, standin='clerk')
    x0, y0 = PP.cell_xy(PRESS[1][2], PRESS[1][3], 48)
    out.append(('minder', sh, x0, y0, n, w))
    sh, n, w = PP.idle('alexei', False, key='right', mul=(0.92, 0.9, 0.86), rim=RIM)
    x0, y0 = PP.cell_xy(ALEXEI[0], ALEXEI[1], 32)
    out.append(('alexei', sh, x0, y0, n, w))
    # Kolonne 4's shadows on the canvas: the shovel cycle as flat dark silhouettes
    shadows = []
    for k, cid in enumerate(('worker_b', 'maria', 'porter')):
        spec, used = K.spec_of(cid, 'worker_b')
        R.strip_props(spec)
        frames = R.render_set(spec, R.shovel_poses(), R.shovel_setup(spec), 48)
        cells = []
        for rg, nm, J in frames:
            a = rg[..., 3] > 0
            c = np.zeros_like(rg)
            c[..., :3] = (40, 38, 26)
            c[..., 3] = np.where(a, 255, 0)
            cells.append(c)
        shadows.append(K.hsheet(cells))
    return out, shadows


def build(w, L):
    pl, lo = plate()
    w('book/b4_bg.png', pl)
    beams, halos = glows()
    w('book/b4_beams.png', beams)
    w('book/b4_halos.png', halos)
    ppl, shadows = people()
    for key, sh, x0, y0, n, cw in ppl:
        w('book/b4_%s.png' % key, sh)
    for k, sh in enumerate(shadows):
        w('book/b4_shadow_%d.png' % k, sh)
    L.update(b4_rail=RAIL, b4_tarp=list(B4_TARP), b4_people={key: [x0, y0, n, cw] for key, sh, x0, y0, n, cw in ppl},
             b4_chimney=[int(lo.anchors['chimney'][0]), int(lo.anchors['chimney'][1])],
             match_t=list(MATCH_T), march_t0=MARCH_T0, march_bpm=MARCH_BPM)
