"""gen_annex_terminal -- the data desk of Nebenstelle Sued (round 13, owner: terminal; TECHNICAL_ARCHITECTURE
§12.8/§12.9, side task "Planspiel Abgang" in L_C4_Annex scene D).

    py -3 -P tools/pixelgen/gen_annex_terminal.py            # art + layout + scene.json actor + provenance rows
    py -3 -P tools/pixelgen/gen_annex_terminal.py --preview <dir>   # also a x3 look at the desk over the hall

A 1964 data-processing desk between the machine room and the household index (x 1062..1125): tape cabinet with two
reels behind glass, the desk with the round vector display ("Sichtgeraet") and the teleprinter, the card reader with
its hopper -- and, beside the second sliding ladder (x 1322..1332), the clipboard with the duty roster of the
Datenstelle. Period-plausible, no real maker's name.

How it stays in the room's light: the desk is painted INTO the hall with the annex kit (env_c4_annex_hall.Hall, the
same ramps, heights and light bake as env_c4_annex.py) and cut out again as the difference to the untouched hall --
so its pixels are palette-pure 'annex' colours under the hall's own lamps, with a normal map and an emission mask
like every prop. env_c4_annex.py itself is NOT run and none of its files is rewritten.

What it writes (assets/environments/berlin_annex is a shared folder: tools/pixelgen/env_keep.py rules):
  terminal/desk.png, desk_n.png, desk_e.png, roster.png, roster_n.png   the cut-outs (binary alpha)
  terminal/layout.json     world positions of the cut-outs, the two exploration spots, the desk's small life
  scene.json               ONE "actors" entry (scenes/levels/c4/AnnexTerminal.tscn, "scene_id": L_C4_AnnexB) and the
                           hotspots exp_terminal / exp_terminal_roster -- merged with env_keep.merge_scene and written
                           with env_keep.write_json; every other key, actor and hotspot stays. env_c4_annex.py's own
                           merge keeps foreign actors and hotspots, so a later re-run of it keeps the desk.
  provenance.json          its own rows (generator = this file) replace its previous rows; all other rows stay in place
  assets/explore/c4/planspiel_strip.png   the close-up of the find "Lauf zwoelf" (240x150): the display with the
                           attic as a wireframe and the teleprinter strip with the result
Deterministic; a second run leaves every file byte-identical.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import env_c4_annex_kit as K          # noqa: E402
import env_c4_annex_layout as L       # noqa: E402
import env_c4_annex_hall as EH        # noqa: E402
import env_keep as KEEP               # noqa: E402

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'berlin_annex')
OUT_DIR = os.path.join(ENV_DIR, 'terminal')
EXPLORE_DIR = os.path.join(ROOT, 'assets', 'explore', 'c4')
GEN = 'tools/pixelgen/gen_annex_terminal.py'
FAMILY = 'tools/pixelgen/gen_annex_terminal'
ACTOR = 'res://scenes/levels/c4/AnnexTerminal.tscn'
SCENE_B = 'L_C4_AnnexB'
FL = L.FLOOR

# world px
TAPE = (1062, 1080)
TAPE_Y = 238
DESK = (1082, 1112)
DESK_TOP = 263
TUBE = (1084, 1101)
TUBE_Y = (244, 262)
READER = (1114, 1125)
READER_Y = 258
ROSTER = (1322, 1332)
ROSTER_Y = (243, 258)
DESK_BOX = (1060, 234, 1127, 290)        # the cut-out windows (x0, y0, x1, y1)
ROSTER_BOX = (1319, 238, 1335, 261)
SPOTS = {'exp_terminal': [1096, 300], 'exp_terminal_roster': [1327, 300]}
ACTOR_POS = [1093, 288]
REEL_GY = TAPE_Y + 8
LAMP_Y = REEL_GY + 27


class DeskHall(EH.Hall):
    """The hall with the data desk and the roster painted in (before the floor, like every piece of furniture)."""

    def floor(self):
        self.data_desk()
        self.roster()
        super().floor()

    def data_desk(self):
        lay = self.lay
        lx = EH.lx
        # ---- tape cabinet: steel, a glass door, two reels, a lamp strip
        x0, x1 = lx(TAPE[0]), lx(TAPE[1])
        w = x1 - x0
        lay.rect(x0, TAPE_Y, w, FL - TAPE_Y, 'S', 2.6, hgt=0.6)
        lay.hline(x0, TAPE_Y, w, 'S', 4.6, hgt=0.8)
        lay.vline(x0, TAPE_Y, FL - TAPE_Y, 'S', 3.8, hgt=0.7)
        lay.vline(x1 - 1, TAPE_Y, FL - TAPE_Y, 'S', 1.6, hgt=0.4)
        lay.rect(x0 + 4, TAPE_Y + 2, 10, 4, 'P', 4.6, hgt=0.5, crisp=True)        # the plate "Datenstelle Sued"
        lay.hline(x0 + 5, TAPE_Y + 3, 8, 'I', 1.0)
        lay.hline(x0 + 5, TAPE_Y + 4, 5, 'I', 1.4)
        gy = REEL_GY
        lay.rect(x0 + 2, gy, w - 4, 24, 'N', 1.6, hgt=0.3)
        lay.hline(x0 + 2, gy, w - 4, 'S', 1.2)
        lay.vline(x0 + 4, gy + 6, 12, 'L', 2.0)                                   # the tape between the reels
        for k, cy in enumerate((gy + 2, gy + 13)):
            m = K.disc(9)
            lay.put(m, x0 + 5, cy, 'S', 3.4 - k * 0.3, hgt=0.6)
            lay.put(K.edge_of(m), x0 + 5, cy, 'S', 4.8, hgt=0.7)
            lay.rect(x0 + 8, cy + 3, 3, 3, 'I', 1.0)
        cy = LAMP_Y
        lay.rect(x0 + 2, cy, w - 4, 6, 'S', 1.8, hgt=0.5)
        lay.rect(x0 + 4, cy + 2, 2, 2, 'G', 5.0, emis=True)
        lay.rect(x0 + 8, cy + 2, 2, 2, 'L', 4.6, emis=True)
        lay.rect(x0 + 12, cy + 2, 2, 2, 'R', 3.0)
        for y in range(cy + 9, FL - 3, 2):
            lay.hline(x0 + 3, y, w - 6, 'S', 1.4)
        lay.rect(x0, FL - 2, w, 2, 'I', 1.4)
        # ---- the desk: slab, a drawer pedestal, a leg (the ladder's foot shows in the knee space)
        d0, d1 = lx(DESK[0]), lx(DESK[1])
        dw = d1 - d0
        lay.rect(d0, DESK_TOP, dw, 3, 'S', 3.2, hgt=0.7)
        lay.hline(d0, DESK_TOP, dw, 'S', 4.8, hgt=0.8)
        lay.hline(d0, DESK_TOP + 2, dw, 'S', 1.6)
        lay.rect(d0 + 1, DESK_TOP + 3, 11, FL - DESK_TOP - 3, 'S', 2.4, hgt=0.55)
        for y in (DESK_TOP + 10, DESK_TOP + 17):
            lay.hline(d0 + 1, y, 11, 'S', 1.4)
        for y in (DESK_TOP + 6, DESK_TOP + 13, DESK_TOP + 20):
            lay.rect(d0 + 5, y, 3, 1, 'S', 4.6, hgt=0.7)
        lay.rect(d1 - 3, DESK_TOP + 3, 2, FL - DESK_TOP - 3, 'S', 2.2, hgt=0.5)
        # ---- the display unit: a hooded housing, the round tube, a faint green line and the cursor
        t0, t1 = lx(TUBE[0]), lx(TUBE[1])
        tw = t1 - t0
        ty0, ty1 = TUBE_Y
        th = ty1 - ty0 + 1
        lay.rect(t0, ty0, tw, th, 'S', 3.0, hgt=0.7)
        lay.hline(t0, ty0, tw, 'S', 4.8, hgt=0.85)
        lay.vline(t0, ty0, th, 'S', 4.0, hgt=0.8)
        lay.vline(t1 - 1, ty0, th, 'S', 1.6, hgt=0.5)
        m = K.disc(13)
        lay.put(m, t0 + 2, ty0 + 2, 'N', 1.2, hgt=0.3)
        lay.put(K.edge_of(m), t0 + 2, ty0 + 2, 'S', 1.4, hgt=0.4)
        lay.hline(t0 + 5, ty0 + 7, 6, 'G', 3.0, emis=True)
        lay.rect(t0 + 5, ty0 + 10, 2, 1, 'G', 4.6, emis=True)
        lay.rect(t0 + 2, ty0 + 16, 5, 1, 'L', 3.4)                                # a brass type plate
        lay.px(t1 - 3, ty0 + 16, 'S', 5.0)
        lay.px(t1 - 5, ty0 + 16, 'S', 5.0)
        # ---- the teleprinter on the desk: body, paper from the roll, a row of keys
        k0 = t1 + 1
        lay.rect(k0, DESK_TOP - 6, 9, 6, 'S', 2.2, hgt=0.6)
        lay.hline(k0, DESK_TOP - 6, 9, 'S', 4.2, hgt=0.7)
        lay.rect(k0 + 2, DESK_TOP - 11, 5, 5, 'P', 4.8, hgt=0.6, crisp=True)
        lay.hline(k0 + 3, DESK_TOP - 9, 3, 'I', 1.0)
        for x in range(k0 + 1, k0 + 8, 2):
            lay.px(x, DESK_TOP - 2, 'P', 4.2, hgt=0.7)
        # ---- the card reader: a low cabinet, cards in the hopper, the slot, a lamp, the stacker
        r0, r1 = lx(READER[0]), lx(READER[1])
        rw = r1 - r0
        lay.rect(r0, READER_Y, rw, FL - READER_Y, 'S', 2.6, hgt=0.6)
        lay.hline(r0, READER_Y, rw, 'S', 4.6, hgt=0.8)
        lay.vline(r1 - 1, READER_Y, FL - READER_Y, 'S', 1.6, hgt=0.4)
        lay.rect(r0 + 2, READER_Y - 5, rw - 4, 5, 'P', 4.4, hgt=0.6, crisp=True)
        for y in (READER_Y - 4, READER_Y - 2):
            lay.hline(r0 + 2, y, rw - 4, 'P', 3.4)
        lay.rect(r0 + 2, READER_Y + 4, rw - 4, 1, 'I', 1.0)
        lay.rect(r0 + 2, READER_Y + 8, 2, 2, 'L', 4.6, emis=True)
        lay.rect(r0 + 2, READER_Y + 14, rw - 4, 8, 'S', 1.8, hgt=0.4)
        lay.rect(r0, FL - 2, rw, 2, 'I', 1.4)

    def roster(self):
        lay = self.lay
        a0, a1 = EH.lx(ROSTER[0]), EH.lx(ROSTER[1])
        y0, y1 = ROSTER_Y
        mid = (a0 + a1) // 2
        lay.px(mid, y0 - 3, 'S', 4.8)                                             # the nail
        lay.vline(mid, y0 - 2, 2, 'I', 1.4)
        lay.rect(a0, y0, a1 - a0, y1 - y0, 'L', 2.0, hgt=0.5)                     # the board
        lay.rect(a0 + 1, y0 + 2, a1 - a0 - 2, y1 - y0 - 3, 'P', 4.9, hgt=0.55, crisp=True)
        lay.rect(mid - 2, y0 - 1, 4, 3, 'S', 4.4, hgt=0.7)                        # the clip
        for k, y in enumerate(range(y0 + 4, y1 - 2, 2)):
            lay.hline(a0 + 2, y, (a1 - a0 - 4) - (k % 3), 'I', 0.8)
        lay.px(a1 - 3, y1 - 4, 'R', 3.0)                                          # the pencilled Tuesday


def bake(cls):
    """The hall of class `cls`, lit and resolved exactly like env_c4_annex_hall.bake_hall: (colour, normal, emission)."""
    h = cls({})
    h.build()
    lights = h.all_lights()
    fields = K.light_fields(h.lay, lights, origin=(EH.X0, 0))
    local = [dict(lt, pos=(lt['pos'][0] - EH.X0, lt['pos'][1])) for lt in lights]
    K.add_pools(fields, local, EH.FL, EH.H, EH.W)
    K.resolve(h.lay, fields, exposure=0.9)
    return h.lay.c.copy(), h.lay.normal_map(3.0), h.lay.em.copy()


def cut(base, new, box):
    """The pixels of `new` that differ from `base` inside the world box -> (colour, normal, emission, x0, y0)."""
    x0, y0, x1, y1 = box
    sl = (slice(y0, y1), slice(x0 - EH.X0, x1 - EH.X0))
    mask = np.zeros(base[0][sl].shape[:2], bool)
    for a, b in zip(base, new):
        mask |= np.any(a[sl] != b[sl], axis=-1)
    ys, xs = np.nonzero(mask)
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out = []
    for arr in new:
        p = arr[sl][by0:by1, bx0:bx1].copy()
        m = mask[by0:by1, bx0:bx1]
        p[..., 3] = np.where(m, 255 if arr is not new[2] else p[..., 3], 0)
        out.append(p)
    return out[0], out[1], out[2], int(x0 + bx0), int(y0 + by0)


def save_png(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.asarray(arr).astype(np.uint8), 'RGBA').save(path)


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


# =========================================================================== the close-up of the find
PHOS = {'bg': '#07120D', 'bg2': '#0A1811', 'glow': '#173A26', 'g1': '#2F6B45', 'g2': '#6FD08C', 'g3': '#DCFFE2'}


def hx(h):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255], np.uint8)


def strip_image():
    """240x150: the tube with the attic as a wireframe (the breach marked), in front the teleprinter strip."""
    w, h = 240, 150
    steel = [hx(c) for c in K.RAMPS['S']]
    paper = [hx(c) for c in K.RAMPS['P']]
    ink = hx(K.RAMPS['I'][2])
    img = np.zeros((h, w, 4), np.uint8)
    img[:] = steel[2]
    for y in range(h):                                   # the housing: brushed rows
        if y % 3 == 0:
            img[y, :] = steel[3]
    # the glass
    gx0, gy0, gx1, gy1 = 8, 8, 168, 112
    img[gy0 - 3:gy1 + 3, gx0 - 3:gx1 + 3] = steel[1]
    img[gy0 - 1:gy1 + 1, gx0 - 1:gx1 + 1] = steel[0]
    lit = np.zeros((h, w), np.uint8)                     # beam strength 0..3

    def proj(x, y, z):
        # a cabinet projection: x right, y up, z into the glass (up and to the right)
        return int(round(gx0 + 7 + x * 10.6 + z * 4.5)), int(round(90 - y * 17.0 - z * 9.0))

    def line(a, b, lv, dash=0):
        (ax, ay), (bx, by) = proj(*a), proj(*b)
        for i, (px, py) in enumerate(K.bres(ax, ay, bx, by)):
            if dash and (i // dash) % 2:
                continue
            if gx0 + 2 <= px < gx1 - 2 and gy0 + 2 <= py < gy1 - 2:
                lit[py, px] = max(lit[py, px], lv)

    # attic floor 13 x 3, knee walls, rafters, ridge, three chimneys
    for (a, b) in (((0, 0, 0), (13, 0, 0)), ((13, 0, 0), (13, 0, 3)), ((13, 0, 3), (0, 0, 3)), ((0, 0, 3), (0, 0, 0))):
        line(a, b, 2)
    line((0, 1.6, 1.5), (13, 1.6, 1.5), 1)
    for x in (0, 3, 6, 9, 13):
        line((x, 0, 0), (x, 1.6, 1.5), 1)
        line((x, 1.6, 1.5), (x, 0, 3), 1)
    for (cx, cz) in ((4.5, 0.5), (4.5, 2.5), (7.5, 2.5)):
        for (dx, dz) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            line((cx + dx, 0, cz + dz), (cx + dx, 1.2, cz + dz), 1)
        for k in range(4):
            p = ((0, 0), (1, 0), (1, 1), (0, 1))
            line((cx + p[k][0], 1.2, cz + p[k][1]), (cx + p[(k + 1) % 4][0], 1.2, cz + p[(k + 1) % 4][1]), 2)
    # the breach in the fire wall (x = 0) and the way to it
    for (a, b) in (((0, 0, 1), (0, 1.0, 1)), ((0, 1.0, 1), (0, 1.0, 2)), ((0, 1.0, 2), (0, 0, 2))):
        line(a, b, 3)
    way = [(10.5, 0, 2.5), (10.5, 0, 0.5), (6.5, 0, 0.5), (6.5, 0, 1.5), (0.4, 0, 1.5)]
    for a, b in zip(way[:-1], way[1:]):
        line(a, b, 3, dash=2)
    fx, fy = proj(0.4, 0.3, 1.5)
    for (dx, dy) in ((0, -3), (-2, 0), (2, 0), (0, 3), (-1, -2), (1, -2), (-1, 2), (1, 2), (-2, -1), (2, -1), (-2, 1), (2, 1)):
        lit[fy + dy, fx + dx] = 3
    tm = K.text_mask('LUECKE', '35', 1)
    tx, ty = proj(0, 1.9, 1.5)
    tx = max(gx0 + 4, tx - tm.shape[1] // 2)
    lit[ty:ty + tm.shape[0], tx:tx + tm.shape[1]][tm] = 3
    hm = K.text_mask('PLANSPIEL ABGANG  LAGE 3', '35', 1)
    lit[gy0 + 4:gy0 + 4 + hm.shape[0], gx0 + 5:gx0 + 5 + hm.shape[1]][hm] = 1
    rm = K.text_mask('LAUF 12', '35', 1)
    lit[gy1 - 9:gy1 - 9 + rm.shape[0], gx0 + 5:gx0 + 5 + rm.shape[1]][rm] = 2
    # phosphor: hard steps, a one-pixel halo, scan rows on the dark glass
    glass = np.zeros((h, w), bool)
    glass[gy0:gy1, gx0:gx1] = True
    for (cx, cy) in ((gx0, gy0), (gx1 - 1, gy0), (gx0, gy1 - 1), (gx1 - 1, gy1 - 1)):
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                y, x = cy + dy, cx + dx
                inx = (dx if cx == gx0 else -dx)
                iny = (dy if cy == gy0 else -dy)
                if 0 <= inx < 5 and 0 <= iny < 5 and (5 - inx - 0.5) ** 2 + (5 - iny - 0.5) ** 2 > 25:
                    glass[y, x] = False
    rows = (np.arange(h)[:, None] % 2 == 0)
    bg = np.where(rows[..., None], hx(PHOS['bg']), hx(PHOS['bg2']))
    bg = np.broadcast_to(bg, (h, w, 4))
    img[glass] = bg[glass]
    strong = lit >= 2
    halo = np.zeros_like(strong)
    halo[1:, :] |= strong[:-1, :]
    halo[:-1, :] |= strong[1:, :]
    halo[:, 1:] |= strong[:, :-1]
    halo[:, :-1] |= strong[:, 1:]
    img[glass & halo & (lit == 0)] = hx(PHOS['glow'])
    for lv, key in ((1, 'g1'), (2, 'g2'), (3, 'g3')):
        img[glass & (lit == lv)] = hx(PHOS[key])
    # the teleprinter strip: out of a slot at the right, across the foreground, torn at its end
    img[97:101, 176:236] = steel[0]
    sx0, sx1, sy0, sy1 = 150, 232, 101, 149
    img[sy0:sy1, sx0:sx1] = paper[5]
    img[sy0:sy1, sx1 - 2:sx1] = paper[4]
    img[sy1 - 1:sy1, sx0:sx1] = paper[3]
    rng = np.random.default_rng(1964)
    for y in range(sy0, sy1):                              # the torn left edge
        img[y, sx0:sx0 + int(rng.integers(0, 4))] = steel[2] if y % 3 else steel[3]
    for i in range(sx0 + 6, sx1 - 4, 6):                   # feed holes
        img[sy0 + 2:sy0 + 4, i:i + 2] = paper[2]
    lines = [('LAGE 3  LAUF 12', '35'), ('ABGANG', '57'), ('WEG: DURCHFAHRT', '35'), ('HOF - AUFGANG', '35'),
             ('BODEN - BRANDMAUER', '35')]
    y = sy0 + 6
    for s, font in lines:
        tmask = K.text_mask(s, font, 1)
        x = sx0 + 7
        sub = img[y:y + tmask.shape[0], x:x + tmask.shape[1]]
        sub[tmask[:, :sub.shape[1]]] = ink
        y += tmask.shape[0] + 2
    return img


# =========================================================================== manifests
def write_scene(layout):
    path = os.path.join(ENV_DIR, 'scene.json')
    old = KEEP.read_json(path)
    if old is None:
        raise SystemExit('gen_annex_terminal: %s is missing (run env_c4_annex.py first)' % rel(path))
    actor = {'scene': ACTOR, 'pos': ACTOR_POS, 'props': {}, 'gen': 'gen_annex_terminal', 'scene_id': SCENE_B,
             'note': 'the data desk between machine room and household index (terminal/desk.png) and the duty '
                     'roster beside the second ladder (terminal/roster.png); carries the exploration spots '
                     'exp_terminal / exp_terminal_roster of the side task „Planspiel Abgang“ '
                     '(tools/pixelgen/gen_annex_terminal.py, terminal/layout.json)'}
    hotspots = dict(old.get('hotspots', {}))
    hotspots.update(layout['spots'])
    new = {'actors': [actor], 'hotspots': hotspots}
    merged = KEEP.merge_scene(new, old)
    return KEEP.write_json(path, merged)


def write_provenance(rows):
    path = os.path.join(ENV_DIR, 'provenance.json')
    old = KEEP.read_json(path)
    if old is None:
        raise SystemExit('gen_annex_terminal: %s is missing' % rel(path))
    kept = [r for r in old.get('files', []) if not (isinstance(r, dict) and KEEP.is_own(r, FAMILY))]
    data = dict(old)
    data['files'] = kept + rows
    if data == old:
        return False
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    return True


def main(argv):
    KEEP.remove_own_pngs(ENV_DIR, ROOT, FAMILY)
    base = bake(EH.Hall)
    new = bake(DeskHall)
    rows = []
    layout = {'doc': 'The data desk of Nebenstelle Süd (tools/pixelgen/gen_annex_terminal.py; read by '
                     'scripts/levels/c4/annex_terminal.gd). World px. desk / roster: cut-outs of the baked hall '
                     '(pos = top-left). spots: where Konrad stands (feet line y 300). life: the cursor on the '
                     'tube, the first line of the trace it shows after the release, the lamp of the tape cabinet '
                     'and the hubs of its two reels.',
              'spots': SPOTS,
              'life': {'cursor': [TUBE[0] + 5, TUBE_Y[0] + 10], 'trace': [TUBE[0] + 5, TUBE_Y[0] + 4],
                       'lamp': [TAPE[0] + 8, LAMP_Y + 2], 'reel_a': [TAPE[0] + 9, REEL_GY + 6],
                       'reel_b': [TAPE[0] + 9, REEL_GY + 17]}}
    desc = {'desk': 'the data desk of the Datenstelle: tape cabinet, desk with the round vector display and the '
                    'teleprinter, card reader (cut from a bake of the hall; y-sorted actor sprite)',
            'roster': 'the duty roster of the Datenstelle on its clipboard beside the second ladder (cut from a bake '
                      'of the hall)'}
    for name, box in (('desk', DESK_BOX), ('roster', ROSTER_BOX)):
        c, n, e, wx, wy = cut(base, new, box)
        save_png(c, os.path.join(OUT_DIR, name + '.png'))
        save_png(n, os.path.join(OUT_DIR, name + '_n.png'))
        rows.append({'path': rel(os.path.join(OUT_DIR, name + '.png')), 'generator': GEN, 'description': desc[name]})
        rows.append({'path': rel(os.path.join(OUT_DIR, name + '_n.png')), 'generator': GEN,
                     'description': desc[name] + ' -- normal map'})
        if bool(e[..., 3].any()):
            save_png(e, os.path.join(OUT_DIR, name + '_e.png'))
            rows.append({'path': rel(os.path.join(OUT_DIR, name + '_e.png')), 'generator': GEN,
                         'description': desc[name] + ' -- emission mask'})
        layout[name] = {'file': name + '.png', 'pos': [wx, wy], 'size': [int(c.shape[1]), int(c.shape[0])]}
        if name == 'desk':
            layout[name]['base_y'] = ACTOR_POS[1]
        print('  %s: %dx%d at (%d, %d), %d px' % (name, c.shape[1], c.shape[0], wx, wy, int((c[..., 3] > 0).sum())))
    KEEP.write_json(os.path.join(OUT_DIR, 'layout.json'), layout)
    print('  scene.json %s, provenance.json %s' % ('written' if write_scene(layout) else 'unchanged',
                                                  'written' if write_provenance(rows) else 'unchanged'))
    save_png(strip_image(), os.path.join(EXPLORE_DIR, 'planspiel_strip.png'))
    print('  wrote', rel(os.path.join(EXPLORE_DIR, 'planspiel_strip.png')))
    # palette check: every opaque pixel of the cut-outs is an 'annex' colour
    allowed = {tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for ramp in K.RAMPS.values() for h in ramp}
    for name in ('desk', 'roster'):
        a = np.asarray(Image.open(os.path.join(OUT_DIR, name + '.png')).convert('RGBA'))
        cols = {tuple(int(v) for v in px[:3]) for px in a[a[..., 3] > 0]}
        off = cols - allowed
        print('  palette %s: %d colours, %d outside the annex ramps' % (name, len(cols), len(off)))
    if '--preview' in argv:
        out = argv[argv.index('--preview') + 1]
        os.makedirs(out, exist_ok=True)
        c = new[0]
        x0, x1 = 1040 - EH.X0, 1350 - EH.X0
        crop = Image.fromarray(c[200:300, x0:x1].astype(np.uint8), 'RGBA').resize(((x1 - x0) * 4, 400), Image.NEAREST)
        st = Image.fromarray(strip_image(), 'RGBA').resize((720, 450), Image.NEAREST)
        sheet = Image.new('RGBA', (1240, 860), (20, 20, 24, 255))
        sheet.paste(crop, (0, 0))
        sheet.paste(st, (0, 405))
        sheet.save(os.path.join(out, 'terminal_art.png'))
        print('  preview', os.path.join(out, 'terminal_art.png'))


if __name__ == '__main__':
    main(sys.argv[1:])
