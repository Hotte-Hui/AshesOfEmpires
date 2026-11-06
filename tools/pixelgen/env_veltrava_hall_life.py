"""env_veltrava_hall_life -- ambient life of L_C3_Hall: looping figure strips and small animated touches.

Everything here is a scene.json "decal" with frames (scripts/levels/layer_stack.gd plays every strip as a
loop: frame = int(t * fps) % frames).  Long strips with holds give the figures a calm, non-mechanical rhythm;
the loop lengths differ so nothing beats in sync.  Figures are painted in the palais tone space
(env_veltrava_hall_kit.TLayer) in the style of the cast sheets (assets/characters: ~43 px tall, profile heads
with a hair mass and a one-pixel nose, a cold rim on the back edge, darker near arm), get a rounded height
field (normal map) and are baked with the scene lights at their world position, like the props.  Clothing
uses the palais ramps; skin uses the cast's skin tones so background people and story characters match.

Placement (all behind the walk band, nobody stands on a hotspot):
  garderobiere    behind the cloakroom counter (playfield, base 290 < counter 292)          vestibule
  cleaner         mopping the melt water in the archway vestibule|foyer (playfield, base 293)
  landing_pair    two delegates talking at the gallery door on the stair landing + the commission usher
                  (room layer, behind the landing balustrade, whose pixels are copied back over them)
  waiter          a waiter beside the untouched buffet (playfield, base 294 > buffet 293)     foyer
  interp_1/_3     interpreters at work in booths 1 (FR) and 3 (EN), backs to us, the lit Saal beyond
  saal_life       the session seen through the booth windows: a speaker, nods, an usher with a note
  door_flash      press flashes behind the etched glass of the Saal doors (rare, double)
  pigeon          a pigeon on the outer sill of the office window (behind the glass)
  clock_*         red second hands on the vestibule and corridor clocks (60 frames, 1 fps)
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L
import pg

P = kit.PALAIS
LIFE_DIR = 'life'
# the cast's skin tones (tools/pixelgen/chargen_* output), dark -> light
SKIN = ['#3E2A20', '#8A5550', '#B67D66', '#D7A182']


def life_ramps() -> kit.Ramps:
    base = kit.palais_ramps()
    d = {n: base.hex[n] for n in base.names}
    d['K'] = SKIN
    return kit.Ramps(d)


R = life_ramps()
WARM = dict(kit.WARM_OF, K='K')
COLD = dict(kit.COLD_OF, K='K')
GAINS = dict(kit.GAINS, K=(0.9, 0.5, 0.7))


def frame(w, h):
    return kit.TLayer(w, h, R, 'life', warm_of=WARM, cold_of=COLD, gains=GAINS)


# =========================================================================== drawing helpers
def limb(lay, pts, r, ramp, t, hgt=0.6):
    m = kit.stroke_mask(lay.w, lay.h, [pts], r, step=0.3)
    lay.put(m, 0, 0, ramp, t, hgt=hgt, flat=True)
    return m


def blit_pat(lay, x, y, pat, cmap, flip=False, hgt=0.6):
    """Hand-made pixel pattern: rows of characters, cmap char -> (ramp, tone)."""
    w = max(len(r) for r in pat)
    for yy, row in enumerate(pat):
        row = row.ljust(w, '.')
        if flip:
            row = row[::-1]
        for xx, ch in enumerate(row):
            if ch in cmap:
                rmp, t = cmap[ch]
                lay.px(x + xx, y + yy, rmp, t, hgt=hgt)


def rounded(lay, amount=0.9):
    """Rounded height field from the silhouette (the normal map then models the figure)."""
    m = lay.rid >= 0
    if m.any():
        h = kit.box_blur(m.astype(np.float32), 1)
        lay.hgt[m] = lay.hgt[m] * 0.3 + h[m] * amount


def bake(lay, lights, origin):
    lay.resolve(kit.light_fields(lay, lights, origin=origin), band=1.6)
    return lay


class Strip:
    """Collects baked frames into one horizontal strip (+ normal + emission strips)."""

    def __init__(self, name, fw, fh):
        self.name, self.fw, self.fh = name, fw, fh
        self.frames = []

    def add(self, lay):
        assert lay.w == self.fw and lay.h == self.fh
        self.frames.append((lay.c.copy(), lay.normal_map(3.0), lay.em.copy()))

    def save(self, env_dir, normal=True):
        n = len(self.frames)
        c = np.concatenate([f[0] for f in self.frames], axis=1)
        nm = np.concatenate([f[1] for f in self.frames], axis=1)
        em = np.concatenate([f[2] for f in self.frames], axis=1)
        base = os.path.join(env_dir, LIFE_DIR, self.name)
        kit.save_rgba(c, base + '.png')
        out = [base + '.png']
        if normal:
            kit.save_rgba(nm, base + '_n.png')
            out.append(base + '_n.png')
        has_em = bool(em[..., 3].any())
        if has_em:
            kit.save_rgba(em, base + '_e.png')
            out.append(base + '_e.png')
        return out, n, has_em


def seq(spec):
    """[(pose, count), ...] -> list of poses (holds as repeated entries)."""
    out = []
    for pose, n in spec:
        out += [pose] * n
    return out


# =========================================================================== heads (profile, facing RIGHT)
# H dark hair, h mid hair, g hair rim/light, S skin, s skin shadow, L skin light (nose), E eye, M mouth
HEAD_MAN = ['..HHHHH..',
            '.HHHHHHh.',
            'gHHHHHhS.',
            'gHHHHsSE.',
            'gHHHsSSSL',
            '.HHHsSSS.',
            '.HHssSM..',
            '..HsSS...',
            '...ss....']
HEAD_BALD = ['...hhhh..',
             '..hSSSSS.',
             'gHSSSSSS.',
             'gHHHsSSE.',
             'gHHHsSSSL',
             '.HHHsSSS.',
             '.HHssSM..',
             '..HsSS...',
             '...ss....']
HEAD_BUN = ['....HHHHH..',
            '...HHHHHHh.',
            '..gHHHHHhS.',
            'HHgHHHHsSE.',
            'gHHHHHsSSSL',
            '.HgHHHsSSS.',
            '...HHssSM..',
            '....HsSS...',
            '.....ss....']
HEAD_SCARF = ['..RRRRr..',
              '.RRRRRRr.',
              'RRRRRRrS.',
              'RRRRRsSE.',
              'RRRRsSSSL',
              'RRRRsSSS.',
              '.RRssSM..',
              '.R.sSS...',
              '...ss....']
HEAD_CAP = ['...CCCCc..',
            '..CCCCCCc.',
            '..KKKKKKKK',
            'gHHHHHhS..',
            'gHHHHsSE..',
            'gHHHsSSSL.',
            '.HHHsSSS..',
            '.HHssSM...',
            '..HsSS....',
            '...ss.....']
# backs of heads (interpreters, seen from behind)
HEAD_BACK_BOB = ['..HHHHH..',
                 '.HHHHHHH.',
                 'gHHHHHHHh',
                 'gHHHHHHHh',
                 'gHHHHHHHh',
                 'gHHHHHHHh',
                 '.HHHHHHh.',
                 '..sSSSs..',
                 '...sSs...']
HEAD_BACK_MAN = ['..hhhhh..',
                 '.hHHHHHh.',
                 'gHHHHHHHh',
                 'gHHHHHHHh',
                 'sHHHHHHHs',
                 '.HHHHHHH.',
                 '..sSSSs..',
                 '..sSSSs..',
                 '...sSs...']


def head(lay, x, y, pat, hair, face_right=True, extra=None, hgt=0.8):
    """hair = (ramp, dark tone): H dark, h +0.7, g +1.6 (rim)."""
    rmp, t = hair
    cmap = {'H': (rmp, t), 'h': (rmp, t + 0.7), 'g': (rmp, t + 1.6), 'S': ('K', 2.0), 's': ('K', 1.0),
            'L': ('K', 3.0), 'E': ('I', 0.4), 'M': ('K', 1.2)}
    if extra:
        cmap.update(extra)
    blit_pat(lay, x, y, pat, cmap, flip=not face_right, hgt=hgt)


# =========================================================================== body parts (profile)
def torso(lay, cx, top, bot, s, coat, chest=1, back_rim=('C', 3.0), width=(4, 3)):
    """Profile torso facing s (+1 right / -1 left): back edge cx - s*wb, front cx + s*wf (+chest).
    coat = (ramp, tone)."""
    wb, wf = width
    rmp, t = coat
    pts = [(cx - s * wb, top), (cx + s * wf, top), (cx + s * (wf + chest), top + 6), (cx + s * wf, bot),
           (cx - s * (wb + 1), bot)]
    m, mx, my = lay.poly(pts, rmp, t, hgt=0.6)
    # rim light on the back edge, a darker front fold
    for yy in range(top + 1, bot):
        bx = cx - s * wb - (1 if (s > 0 and yy > top + (bot - top) * 0.6) else 0) * s
        lay.px(bx, yy, back_rim[0], back_rim[1], crisp=True)
    lay.line(cx + s * (wf - 1), top + 7, cx + s * (wf - 1), bot - 1, rmp, t - 0.6)
    return m


def legs(lay, cx, top, base, s, col=('I', 1.2), shoe=('I', 0.5), stride=0):
    rmp, t = col
    # far leg (darker), near leg
    lay.rect(cx - 2 - stride, top, 2, base - top, rmp, t - 0.3, hgt=0.6)
    lay.rect(cx + stride, top, 2, base - top, rmp, t + 0.2, hgt=0.6)
    for lx in (cx - 2 - stride, cx + stride):
        lay.rect(lx - (1 if s < 0 else 0), base - 1, 3, 1, shoe[0], shoe[1], hgt=0.5)
        lay.px(lx + (2 if s > 0 else -1), base - 1, shoe[0], shoe[1] + 0.6)


def arm(lay, pts, sleeve, hand=True, hand_t=2.0, r=1.05):
    rmp, t = sleeve
    limb(lay, pts, r, rmp, t, hgt=0.85)
    if hand:
        hx, hy = pts[-1]
        hx, hy = int(round(hx)), int(round(hy))
        lay.rect(hx - 1, hy, 2, 2, 'K', hand_t, hgt=0.9)
        lay.px(hx - 1, hy + 1, 'K', hand_t - 0.8)


def person(lay, cx, base, s, look, coat, trousers, hair_pat, hair, arm_pts=None, coat_len=21, bob=0,
           shirt=True, tie=('R', 2.2), extra_head=None, head_dx=0, h=43, sleeve=None, hands=True):
    """Standing adult in profile.  look: head offset (-1 down/0 level).  arm_pts: near arm joints (relative to
    the shoulder) or None for a hanging arm."""
    top = base - h + bob
    sh_y = top + 9
    hem = sh_y + coat_len
    legs(lay, cx, hem, base, s, trousers)
    torso(lay, cx, sh_y, hem, s, coat)
    if shirt:
        lay.px(cx + s * 2, sh_y, 'P', 6.4)
        lay.px(cx + s * 1, sh_y, 'P', 5.6)
        if tie:
            lay.px(cx + s * 2, sh_y + 1, tie[0], tie[1])
            lay.px(cx + s * 2, sh_y + 2, tie[0], tie[1] - 0.4)
    hx = cx - 4 + (1 if s > 0 else 0) + head_dx
    head(lay, hx, top + look, hair_pat, hair, face_right=s > 0, extra=extra_head)
    slv = sleeve or (coat[0], coat[1] - 0.5)
    shoulder = (cx + s * 0.5, sh_y + 2)
    if arm_pts is None:
        arm_pts = [(0, 0), (s * 0.5, 8), (s * 1, 13)]
    pts = [(shoulder[0] + dx, shoulder[1] + dy) for (dx, dy) in arm_pts]
    arm(lay, pts, slv, hand=hands)
    return top


# =========================================================================== figures
def garderobiere(lights, wx, base):
    """Cloakroom attendant behind the counter (on the raised floor of the alcove), facing left toward the
    arriving guests: black dress, white collar, grey hair in a bun.  Sorts the brass tokens on the counter,
    turns to check a coat number on the hooks behind her, looks up toward the door."""
    fw, fh = 24, 50
    ox, oy = wx - 12, base - fh + 1
    st = Strip('garderobiere', fw, fh)
    poses = seq([({'look': 0, 'arm': 'rest', 'turn': 0}, 12), ({'look': 1, 'arm': 'reach', 'turn': 0}, 3),
                 ({'look': 1, 'arm': 'sort1', 'turn': 0}, 3), ({'look': 1, 'arm': 'sort2', 'turn': 0}, 3),
                 ({'look': 1, 'arm': 'sort1', 'turn': 0}, 3), ({'look': 1, 'arm': 'sort2', 'turn': 0}, 3),
                 ({'look': 1, 'arm': 'reach', 'turn': 0}, 2), ({'look': 0, 'arm': 'rest', 'turn': 0}, 10),
                 ({'look': 0, 'arm': 'rest', 'turn': 1}, 9), ({'look': 0, 'arm': 'rest', 'turn': 0}, 6),
                 ({'look': 1, 'arm': 'reach', 'turn': 0}, 3), ({'look': 1, 'arm': 'sort1', 'turn': 0}, 4),
                 ({'look': 0, 'arm': 'rest', 'turn': 0}, 4)])
    for i, p in enumerate(poses):
        lay = frame(fw, fh)
        s = 1 if p['turn'] else -1
        cx = 12
        b = 1 if (i // 7) % 4 == 1 else 0                         # slow breathing
        arm_rel = {'rest': None, 'reach': [(0, 0), (-2, 5), (-6, 7)], 'sort1': [(0, 0), (-3, 5), (-8, 7)],
                   'sort2': [(0, 0), (-3, 5), (-6, 8)]}[p['arm']]
        if arm_rel is not None and s > 0:
            arm_rel = [(-dx, dy) for (dx, dy) in arm_rel]
        top = person(lay, cx, fh - 10 + b, s, p['look'], ('I', 1.5), ('I', 1.2), HEAD_BUN, ('M', 3.0),
                     arm_pts=arm_rel, coat_len=24, shirt=False, sleeve=('I', 1.2))
        sh_y = top + 9
        lay.rect(cx - 2, sh_y, 4, 1, 'P', 6.4, hgt=0.9)                   # lace collar
        lay.px(cx + s * 2, sh_y + 1, 'P', 5.6)
        lay.px(cx - s * 3, sh_y + 1, 'P', 4.8)
        lay.rect(cx + s * 1 - (1 if s < 0 else 0), sh_y + 3, 2, 4, 'P', 5.4, hgt=0.7)   # apron bib edge
        if p['arm'] in ('sort1', 'sort2'):
            hx = cx + (-8 if p['arm'] == 'sort1' else -6) * (-s if s > 0 else 1)
            lay.px(int(hx) - 1, sh_y + 9, 'B', 4.6, hgt=0.95)                # a brass token
        rounded(lay)
        bake(lay, lights, (ox, oy))
        st.add(lay)
    return st, (ox, oy)


def cleaner(lights, wx, base):
    """Cleaning woman mopping the melt water in the archway: wine headscarf, slate smock with a grey apron,
    dark skirt and stockings, a zinc bucket with a wringer.  Strokes, dips and wrings the mop, straightens her
    back with a hand at the small of it."""
    fw, fh = 46, 46
    ox, oy = wx - 26, base - fh + 1
    st = Strip('cleaner', fw, fh)
    poses = []
    for s_ in range(3):
        for k in range(10):
            poses.append({'mop': math.sin(k / 10 * 2 * math.pi) * 6, 'lean': 4, 'st': 'mop'})
    poses += [{'mop': 0, 'lean': 3, 'st': 'lift'}] * 3
    poses += [{'mop': 0, 'lean': 3, 'st': 'dip'}] * 6
    poses += [{'mop': 0, 'lean': 2, 'st': 'wring'}] * 6
    poses += [{'mop': 0, 'lean': 0, 'st': 'back'}] * 10
    poses += [{'mop': 0, 'lean': 1, 'st': 'stand'}] * 5
    for k in range(10):
        poses.append({'mop': math.sin(k / 10 * 2 * math.pi) * 6, 'lean': 4, 'st': 'mop'})
    bx = 3                                                     # bucket, local x (in front of her, left)
    for p in poses:
        lay = frame(fw, fh)
        cx, bse = 30, fh - 1
        lean = p['lean']
        s = -1
        # legs, skirt
        legs(lay, cx, bse - 11, bse, s, ('I', 1.0), ('D', 0.8))
        lay.poly([(cx - 5, bse - 21), (cx + 4, bse - 21), (cx + 5, bse - 10), (cx - 6, bse - 10)], 'D', 1.6,
                 hgt=0.6)
        lay.px(cx + 4, bse - 18, 'C', 2.8)                                     # rim on the skirt back
        # torso bent forward from the hips (shoulders move toward her mop by `lean`)
        hip = (cx, bse - 20)
        shx = cx - lean
        sht = bse - 33 + lean // 2
        lay.poly([(shx - 4, sht), (shx + 4, sht), (cx + 5, hip[1]), (cx - 5, hip[1])], 'C', 1.9, hgt=0.6)
        lay.line(shx + 4, sht + 1, cx + 5, hip[1] - 1, 'C', 3.2)              # cold rim on the back
        lay.poly([(shx - 3, sht + 4), (shx, sht + 3), (cx - 3, hip[1] + 4), (cx - 6, hip[1] + 4)], 'P', 3.2,
                 hgt=0.65)                                                     # apron front
        lay.rect(cx - 2, hip[1] - 1, 6, 1, 'P', 2.6)                           # apron string
        head(lay, shx - 6, sht - 9, HEAD_SCARF, ('R', 1.8), face_right=False,
             extra={'R': ('R', 1.9), 'r': ('R', 2.7)})
        lay.px(shx + 3, sht - 2, 'R', 1.4)                                     # scarf knot at the nape
        st_ = p['st']
        mx = cx - 18 + int(round(p['mop']))
        shoulder = (shx - 1, sht + 2)
        if st_ in ('mop', 'lift', 'stand'):
            fy = bse if st_ != 'lift' else bse - 4
            h1 = (shx - 6, sht + 6)
            h2 = (shx - 3, sht + 10)
            lay.line(h1[0] + 1, h1[1] - 5, mx, fy - 1, 'D', 3.6, hgt=0.85)    # wooden handle
            lay.rect(mx - 4, fy - 1, 9, 1, 'P', 3.4, hgt=0.6)                  # mop head + strands
            for k in range(-4, 5, 2):
                lay.px(mx + k, min(fh - 1, fy), 'P', 2.6)
            arm(lay, [shoulder, (shx - 4, sht + 6), h1], ('C', 1.6), hand_t=1.8)
            arm(lay, [(shx + 1, sht + 3), (shx - 1, sht + 9), h2], ('C', 1.4), hand_t=1.6)
        elif st_ == 'dip':
            lay.line(shx - 8, sht + 2, bx + 5, bse - 9, 'D', 3.6, hgt=0.85)
            arm(lay, [shoulder, (shx - 5, sht + 4), (shx - 8, sht + 3)], ('C', 1.6), hand_t=1.8)
        elif st_ == 'wring':
            lay.line(shx - 9, sht - 2, bx + 6, bse - 9, 'D', 3.6, hgt=0.85)
            arm(lay, [shoulder, (shx - 5, sht + 2), (shx - 9, sht)], ('C', 1.6), hand_t=1.8)
            arm(lay, [(shx + 1, sht + 3), (shx - 4, sht + 10), (bx + 10, bse - 13)], ('C', 1.4), hand_t=1.6)
        else:                                       # 'back': upright, mop leaning on her shoulder, hand at back
            lay.line(shx - 3, sht - 6, shx - 12, bse, 'D', 3.6, hgt=0.85)
            lay.rect(shx - 16, bse - 1, 8, 1, 'P', 3.4)
            arm(lay, [shoulder, (shx - 3, sht + 4), (shx - 4, sht + 1)], ('C', 1.6), hand_t=1.8)
            arm(lay, [(shx + 2, sht + 3), (shx + 5, sht + 9), (cx + 4, hip[1] - 2)], ('C', 1.4), hand_t=1.6)
        # zinc bucket with a wringer
        lay.poly([(bx, bse - 10), (bx + 10, bse - 10), (bx + 9, bse), (bx + 1, bse)], 'S', 1.9, hgt=0.6)
        lay.rect(bx, bse - 10, 11, 1, 'S', 3.4, hgt=0.7)
        lay.rect(bx + 1, bse - 5, 9, 1, 'S', 1.4, hgt=0.6)
        lay.px(bx + 1, bse - 8, 'S', 3.0)
        lay.rect(bx + 2, bse - 9, 7, 1, 'C', 1.4)                              # grey water
        lay.rect(bx + 7, bse - 14, 3, 4, 'S', 2.4, hgt=0.7)                    # wringer
        lay.rect(bx + 6, bse - 15, 5, 1, 'S', 3.4, hgt=0.75)
        lay.line(bx + 1, bse - 10, bx + 5, bse - 15, 'S', 2.8)                 # bail handle
        lay.line(bx + 5, bse - 15, bx + 9, bse - 10, 'S', 2.2)
        rounded(lay)
        bake(lay, lights, (ox, oy))
        st.add(lay)
    return st, (ox, oy)


def usher_figure(lay, cx, base, arm_state, bob=0):
    """Commission usher: slate-blue tunic with brass buttons, white armband, peaked cap, white gloves; faces
    left (toward the stair)."""
    s = -1
    top = base - 44 + bob
    sh_y = top + 10
    hem = sh_y + 19
    legs(lay, cx, hem, base, s, ('N', 2.2), ('N', 0.6))
    lay.rect(cx, hem, 1, base - hem - 1, 'R', 2.0)                             # trouser stripe
    torso(lay, cx, sh_y, hem, s, ('C', 1.8), back_rim=('C', 3.2))
    for k in range(4):
        lay.px(cx - 3, sh_y + 3 + k * 4, 'B', 4.4, hgt=0.9)                   # buttons
    lay.rect(cx - 5, hem - 2, 10, 1, 'I', 1.0, hgt=0.6)                       # belt
    lay.px(cx - 3, hem - 2, 'B', 4.0)
    head(lay, cx - 5, top, HEAD_CAP, ('D', 0.8), face_right=False,
         extra={'C': ('C', 1.5), 'c': ('C', 2.6), 'K': ('I', 0.5)})
    lay.px(cx - 4, top + 1, 'B', 4.6)                                         # cap badge (bridge)
    shoulder = (cx, sh_y + 2)
    if arm_state == 'behind':
        pts = [shoulder, (cx + 1, sh_y + 8), (cx + 3, sh_y + 12)]
        arm(lay, pts, ('C', 1.4), hand=False)
        lay.rect(cx + 3, sh_y + 12, 2, 2, 'P', 6.4, hgt=0.9)                  # white glove behind his back
    elif arm_state == 'watch':
        pts = [shoulder, (cx - 2, sh_y + 8), (cx - 6, sh_y + 6)]
        arm(lay, pts, ('C', 1.4), hand=False)
        lay.rect(cx - 7, sh_y + 5, 2, 2, 'P', 6.4, hgt=0.9)
        lay.px(cx - 5, sh_y + 5, 'B', 4.8)                                    # wrist watch
    else:                                                                     # 'side'
        pts = [shoulder, (cx - 1, sh_y + 8), (cx - 1, sh_y + 13)]
        arm(lay, pts, ('C', 1.4), hand=False)
        lay.rect(cx - 2, sh_y + 13, 2, 2, 'P', 6.4, hgt=0.9)
    lay.rect(cx - 1, sh_y + 4, 3, 2, 'P', 6.2, hgt=0.9)                       # white armband (near arm)
    lay.px(cx, sh_y + 4, 'C', 3.0)


def landing_group(lights, room_c, front_mask):
    """Two delegates talking at the gallery door + the usher beside it, on the stair landing (feet y 176),
    behind the landing balustrade (its baked room pixels are copied back over them)."""
    xt, yt = L.STAIR_TOP
    lx1 = L.LANDING[1]
    x0w, fw = xt, lx1 - xt + 2
    fh = 50
    y0w = yt - fh + 1
    st = Strip('landing_pair', fw, fh)
    sub = room_c[y0w:y0w + fh, x0w:x0w + fw].copy()
    railish = front_mask[y0w:y0w + fh, x0w:x0w + fw] & (sub[..., 3] > 0)
    # conversation: A speaks (two gestures), B nods; B answers with his folder arm still; a pause; repeat
    talk = ([('a', 'g1')] * 5 + [('a', 'g2')] * 4 + [('a', 'g1')] * 4 + [('a', 'down')] * 6 +
            [('b', 'g1')] * 5 + [('b', 'g2')] * 5 + [('b', 'down')] * 5 + [('-', 'chin')] * 10 +
            [('-', 'down')] * 8)
    usher = ['behind'] * 26 + ['watch'] * 7 + ['behind'] * 12 + ['side'] * 7
    GEST = {'g1': [(0, 0), (2, 6), (6, 5)], 'g2': [(0, 0), (2, 6), (6, 3)], 'down': None,
            'chin': [(0, 0), (2, 6), (3, -2)]}
    for j, (who, g) in enumerate(talk):
        lay = frame(fw, fh)
        base = fh - 1
        a_arm = GEST[g] if who == 'a' or (who == '-' and g == 'chin') else None
        b_arm = GEST[g] if who == 'b' else None
        if b_arm is not None:
            b_arm = [(-dx, dy) for (dx, dy) in b_arm]
        a_look = 1 if (who == 'b' and j % 6 == 2) else 0
        b_look = 1 if (who == 'a' and j % 7 == 3) else 0
        # A: older diplomat, grey hair, glasses, charcoal suit (faces right)
        person(lay, 12, base, 1, a_look, ('I', 1.8), ('I', 1.4), HEAD_BALD, ('M', 3.4), arm_pts=a_arm,
               coat_len=19, tie=('R', 2.6))
        lay.px(12 + 3, base - 43 + a_look + 3, 'S', 4.4)                      # glasses glint
        # B: younger, dark hair, grey suit, folder under the far arm (faces left)
        person(lay, 25, base, -1, b_look, ('W', 3.4), ('W', 2.6), HEAD_MAN, ('D', 0.9), arm_pts=b_arm,
               coat_len=19, tie=('C', 2.4))
        lay.rect(28, base - 31, 2, 9, 'D', 3.4, hgt=0.7)                      # folder
        lay.rect(28, base - 31, 2, 1, 'P', 5.6, hgt=0.75)
        usher_figure(lay, fw - 8, base, usher[j % len(usher)], bob=1 if (j // 11) % 3 == 1 else 0)
        rounded(lay)
        bake(lay, lights, (x0w, y0w))
        lay.c[railish] = sub[railish]                                         # balustrade in front of them
        lay.em[railish] = 0
        st.add(lay)
    return st, (x0w, y0w)


def waiter(lights, wx, base):
    """Waiter beside the untouched buffet: black tailcoat, white shirt front and bow tie, a napkin over the
    forearm; waits, glances toward the closed Saal doors, adjusts the napkin, looks back toward the stair."""
    fw, fh = 20, 48
    ox, oy = wx - 10, base - fh + 1
    st = Strip('waiter', fw, fh)
    poses = seq([({'look': 0, 'arm': 'napkin', 'f': 1}, 16), ({'look': 1, 'arm': 'napkin', 'f': 1}, 6),
                 ({'look': 0, 'arm': 'napkin', 'f': 1}, 8), ({'look': 0, 'arm': 'adjust', 'f': 1}, 4),
                 ({'look': 0, 'arm': 'napkin', 'f': 1}, 8), ({'look': 0, 'arm': 'napkin', 'f': -1}, 10),
                 ({'look': 0, 'arm': 'napkin', 'f': 1}, 6)])
    for i, p in enumerate(poses):
        lay = frame(fw, fh)
        s = p['f']
        cx, bse = 10, fh - 1
        b = 1 if (i // 8) % 3 == 1 else 0
        arm_rel = [(0, 0), (s * 1, 7), (s * 5, 7)] if p['arm'] == 'napkin' else [(0, 0), (s * 1, 6), (s * 4, 4)]
        top = person(lay, cx, bse + b, s, p['look'], ('I', 1.5), ('I', 1.0), HEAD_MAN, ('D', 0.7),
                     arm_pts=arm_rel, coat_len=22, tie=('I', 0.4), sleeve=('I', 1.2))
        sh_y = top + 9
        lay.rect(cx + s * 1 - (1 if s < 0 else 0), sh_y + 1, 2, 7, 'P', 6.2, hgt=0.7)   # white shirt front
        lay.px(cx + s * 2, sh_y + 1, 'I', 0.3)                                # bow tie
        lay.px(cx + s * 3, sh_y + 1, 'I', 0.3)
        lay.px(cx + s * 1, sh_y + 9, 'P', 5.0)                                # waistcoat tip
        nx = cx + s * 4 - (3 if s < 0 else 0)
        lay.rect(nx, sh_y + 9, 4, 5 if p['arm'] == 'napkin' else 4, 'P', 6.6, hgt=0.9)   # napkin
        lay.px(nx + (3 if s > 0 else 0), sh_y + 13, 'P', 5.4)
        rounded(lay)
        bake(lay, lights, (ox, oy))
        st.add(lay)
    return st, (ox, oy)


def interpreter(lights, booth_idx, woman):
    """Interpreter at work in a booth, back to us, the lit Saal beyond: headset, listening, speaking (small
    nods), writing, a hand pressed to the earpiece, turning a page."""
    b0, b1 = L.BOOTHS[booth_idx]
    # booth 3 (EN): seated left of centre, so Alexei (who waits in front of it, x 1718) never stands
    # directly in front of him
    cxw = (b0 + b1) // 2 + (-13 if booth_idx == 2 else 0)
    fw, fh = 30, 36
    ox, oy = cxw - 15, L.BOOTH_DESK_Y - fh + 2
    st = Strip('interp_%d' % (booth_idx + 1), fw, fh)
    poses = seq([({'nod': 0, 'hand': 'desk', 'turn': 0}, 8), ({'nod': 1, 'hand': 'desk', 'turn': 0}, 2),
                 ({'nod': 0, 'hand': 'desk', 'turn': 0}, 4), ({'nod': 1, 'hand': 'write', 'turn': 0}, 2),
                 ({'nod': 0, 'hand': 'write', 'turn': 0}, 3), ({'nod': 0, 'hand': 'write2', 'turn': 0}, 3),
                 ({'nod': 0, 'hand': 'write', 'turn': 0}, 3), ({'nod': 0, 'hand': 'ear', 'turn': 0}, 9),
                 ({'nod': 1, 'hand': 'ear', 'turn': 0}, 2), ({'nod': 0, 'hand': 'desk', 'turn': -1}, 6),
                 ({'nod': 0, 'hand': 'page', 'turn': -1}, 3), ({'nod': 0, 'hand': 'desk', 'turn': 0}, 5)])
    if not woman:
        poses = poses[10:] + poses[:10]
    hair = ('D', 0.8) if woman else ('M', 3.0)
    body = ('R', 1.4) if woman else ('W', 3.4)
    for p in poses:
        lay = frame(fw, fh)
        cx = 15 + p['turn']
        bse = fh - 3                                       # the desk edge (desk itself is in the room layer)
        top = bse - 24 + p['nod']
        lay.poly([(cx - 7, top + 10), (cx + 7, top + 10), (cx + 8, bse), (cx - 8, bse)], body[0], body[1],
                 hgt=0.6)
        lay.rect(cx - 6, top + 9, 13, 2, body[0], body[1] + 0.5, hgt=0.65)
        lay.line(cx - 7, top + 11, cx - 8, bse - 1, body[0], body[1] + 1.2)    # rim from the Saal window
        lay.line(cx + 7, top + 11, cx + 8, bse - 1, body[0], body[1] + 1.0)
        if not woman:
            lay.rect(cx - 1, top + 9, 3, 1, 'P', 6.0)                          # shirt collar at the nape
        head(lay, cx - 4, top + 1, HEAD_BACK_BOB if woman else HEAD_BACK_MAN, hair)
        # headset: band over the crown, earcups, cable to the console
        lay.rect(cx - 3, top + 1, 7, 1, 'I', 1.0, hgt=0.95)
        lay.rect(cx - 5, top + 4, 2, 3, 'I', 0.8, hgt=0.95)
        lay.rect(cx + 4, top + 4, 2, 3, 'I', 0.8, hgt=0.95)
        lay.px(cx - 5, top + 4, 'S', 3.4)
        lay.line(cx + 5, top + 7, cx + 8, bse - 2, 'I', 1.2)
        hand = p['hand']
        if hand in ('write', 'write2'):
            hx = cx + 9 + (1 if hand == 'write2' else 0)
            arm(lay, [(cx + 6, top + 12), (cx + 9, top + 17), (hx, bse - 3)], (body[0], body[1] + 0.3),
                hand_t=2.2)
            lay.px(hx + 1, bse - 4, 'B', 4.6)                                  # pencil
        elif hand == 'ear':
            arm(lay, [(cx - 6, top + 12), (cx - 8, top + 9), (cx - 6, top + 5)], (body[0], body[1] + 0.3),
                hand_t=2.2)
        elif hand == 'page':
            arm(lay, [(cx - 6, top + 12), (cx - 9, top + 17), (cx - 11, bse - 4)], (body[0], body[1] + 0.3),
                hand_t=2.2)
            lay.rect(cx - 15, bse - 7, 5, 4, 'P', 6.6, hgt=0.85)               # the page turning
            lay.rect(cx - 15, bse - 7, 5, 1, 'P', 5.6)
        rounded(lay, 0.7)
        bake(lay, lights, (ox, oy))
        # corridor-side glass sheen streaks over the figure (as on the rest of the booth glazing)
        g0, g1 = L.BOOTH_GLASS
        for k in range(fh):
            wy = k + oy
            if not (g0 <= wy < g1) or ((wy - g0) // 6) % 3 == 2:
                continue
            for off in (5, 8):
                xx = (b0 + off + (wy - g0) // 3) - ox
                if 0 <= xx < fw and lay.c[k, xx, 3] > 0:
                    lay.c[k, xx, :3] = pg.hx(P['daylight'][2])[:3] if off == 5 else pg.hx(P['daylight'][1])[:3]
        st.add(lay)
    return st, (ox, oy)


def saal_life(near_pos):
    """The session through the booth windows (local coords of saal_near): the delegate at the centre of the
    presidium stands up to speak and gestures, his neighbours turn their heads to him, an usher carries a note
    behind the presidium (hidden below the row of seated heads)."""
    import env_veltrava_hall_ext as EX
    cx = 200
    x0l, y0l = cx - 50, 26
    fw, fh = 100, 14
    st = Strip('saal_life', fw, fh)
    n = 48
    head_row = 33 - y0l                                    # seated presidium heads (env_veltrava_hall_ext)
    for f in range(n):
        lay = frame(fw, fh)
        u = f / n
        sx = 50                                            # the speaker's seat (local 200)
        standing = 6 <= f < 38
        if standing:
            lay.rect(sx - 1, 4, 3, 5, 'I', 1.4)            # standing: dark suit, white shirt front
            lay.px(sx, 4, 'P', 6.4)
            lay.rect(sx - 2, 9, 5, 3, 'I', 1.2)            # covers his empty seat
            lay.rect(sx - 1, 2, 3, 2, 'K', 2.0)            # head
            lay.px(sx - 1, 2, 'I', 0.6)
            g = (f // 4) % 4
            if g == 1:
                lay.px(sx + 2, 5, 'K', 2.6)                # gesturing hand
            elif g == 2:
                lay.px(sx + 2, 4, 'K', 2.6)
                lay.px(sx + 3, 3, 'K', 2.6)
            elif g == 3:
                lay.px(sx - 2, 6, 'K', 2.4)
            for nx in (40, 60):                            # neighbours turn toward him (face pixel shifts)
                lay.px(nx + (1 if nx < sx else -1), head_row, 'K', 3.0)
                lay.px(nx + (-1 if nx < sx else 1), head_row, 'I', 0.8)
        ux = int(round(4 + u * 92))                        # the usher with a note, left -> right
        if 2 <= ux < fw - 2 and abs(ux - sx) > 3:
            lay.rect(ux - 1, 2, 2, head_row - 2, 'C', 1.6)
            lay.rect(ux - 1, 0, 2, 2, 'K', 2.0)
            lay.px(ux + 1, 3, 'P', 6.8)                    # the note
        lay.unlit[:] = True
        lay.resolve()
        st.add(lay)
    return st, (near_pos + x0l, EX.SAAL_Y + y0l)


def door_flash():
    """Press flashes behind the etched glass of the Saal doors: a rare double flash in a 12 s loop."""
    x0, x1 = L.SAAL_DOOR
    top = L.SAAL_DOOR_TOP
    w = x1 - x0
    half = w // 2
    fw, fh = w, 46
    st = Strip('door_flash', fw, fh)
    n = 72
    for f in range(n):
        lay = frame(fw, fh)
        lay.unlit[:] = True
        level = {44: 2, 45: 1, 47: 2.4, 48: 1.2}.get(f, 0)
        if level:
            for k in range(2):
                gx, gy, gw, gh = k * half + 4, 7, half - 8, 38
                tt = 3.6 + level * 0.6 + pg.value_noise(gw, gh, 8, 70 + k, octaves=2) * 0.8
                lay.put(np.ones((gh, gw), bool), gx, gy, 'A', np.clip(tt, 0, 5.0), emis=True, flat=False)
                for yy in range(gy + 3, gy + gh - 2, 6):
                    lay.rect(gx + 2, yy, gw - 4, 1, 'P', 7.0 if level > 1.5 else 6.0, emis=True)
        lay.resolve()
        st.add(lay)
    return st, (x0, top)


def pigeon(lights):
    """A pigeon on the outer sill of the office window: struts, pecks, turns, flies off, comes back."""
    x0, x1, y0, y1 = L.OFFICE_WIN
    fw, fh = 24, 14
    ox, oy = x0 + 2, y1 - fh - 1
    st = Strip('pigeon', fw, fh)
    path = ([(14, 0, 'stand')] * 10 + [(14, 0, 'peck')] * 2 + [(14, 0, 'stand')] * 3 + [(14, 0, 'peck')] * 2 +
            [(15, 0, 'walk'), (16, 0, 'walk'), (17, 0, 'walk'), (18, 0, 'walk')] + [(18, 0, 'stand')] * 8 +
            [(18, 1, 'stand')] * 10 + [(18, 1, 'peck')] * 2 + [(18, 1, 'stand')] * 4 +
            [(18, 1, 'fly1'), (19, 1, 'fly2'), (21, 1, 'fly1')] + [(0, 0, 'gone')] * 22 +
            [(15, 0, 'land'), (14, 0, 'stand')] + [(14, 0, 'stand')] * 6)
    for (px_, turned, state) in path:
        lay = frame(fw, fh)
        if state != 'gone':
            fr = turned == 0                       # facing right (toward the window centre) unless turned
            base = fh - 2
            bx = px_
            s = 1 if fr else -1
            # body (grey), darker wing bars, iridescent neck (green/wine), head, beak, red feet
            body = [(bx - 4 * s, base - 4), (bx + 2 * s, base - 5), (bx + 3 * s, base - 2), (bx - 3 * s, base - 1),
                    (bx - 6 * s, base - 2)]
            if state in ('fly1', 'fly2'):
                lay.poly(body, 'S', 3.2, hgt=0.6)
                wy = base - 8 if state == 'fly1' else base - 3
                lay.poly([(bx - 1, base - 4), (bx + 2 * s, base - 4), (bx - 2 * s, wy)], 'S', 4.2, hgt=0.7)
            else:
                lay.poly(body, 'S', 3.0, hgt=0.6)
                lay.rect(min(bx - 2 * s, bx) , base - 3, 3, 1, 'S', 1.8)           # wing bar
                hy = base - 7 if state != 'peck' else base - 4
                hx = bx + 2 * s if state != 'peck' else bx + 4 * s
                lay.px(bx + 1 * s, base - 5, 'G', 4.4)                          # neck sheen
                lay.px(bx + 2 * s, base - 5, 'R', 2.6)
                lay.rect(min(hx, hx + s), hy, 2, 2, 'S', 3.4, hgt=0.7)          # head
                lay.px(hx + 2 * s if s > 0 else hx - 1, hy + 1, 'P', 4.4)       # beak
                lay.px(hx + (1 if s > 0 else 0), hy, 'I', 1.0)                  # eye
                if state != 'land':
                    lay.px(bx - 1, base, 'R', 3.2)
                    lay.px(bx + 1, base, 'R', 3.2)
                    if state == 'walk':
                        lay.px(bx + 2 * s, base, 'R', 3.0)
        lay.unlit[:] = True
        lay.resolve()
        st.add(lay)
    return st, (ox, oy)


def second_hand(name, cx, cy, r=6):
    fw = fh = 2 * r + 3
    st = Strip(name, fw, fh)
    c = r + 1
    for f in range(60):
        lay = frame(fw, fh)
        a = math.radians(f * 6 - 90)
        for (x, y) in kit.bres(c, c, c + math.cos(a) * r, c + math.sin(a) * r):
            if (x, y) != (c, c):
                lay.px(x, y, 'R', 3.0, crisp=True)
        lay.px(c, c, 'B', 4.0, crisp=True)
        lay.unlit[:] = True
        lay.resolve()
        st.add(lay)
    return st, (cx - c, cy - c)


# =========================================================================== build
def build_all(env_dir, room, near_pos):
    """-> (produced files [(path, desc)], decal entries for scene.json)"""
    lights = room.all_lights
    files, decals = [], []
    os.makedirs(os.path.join(env_dir, LIFE_DIR), exist_ok=True)

    def emit(st, pos, fps, layer, z, desc, lit=True, base_y=None, normal=True, extra=None):
        out, n, has_em = st.save(env_dir, normal=normal and lit)
        for pth in out:
            files.append((pth, desc + (' -- normal map' if pth.endswith('_n.png') else
                                       ' -- emission' if pth.endswith('_e.png') else '')))
        e = {'name': st.name, 'file': '%s/%s.png' % (LIFE_DIR, st.name), 'pos': [int(pos[0]), int(pos[1])],
             'frames': n, 'fps': fps, 'layer': layer, 'z': z, 'lit': lit, 'normal': bool(normal and lit),
             'emission': has_em, 'note': desc}
        if base_y is not None:
            e['base_y'] = int(base_y)
        if extra:
            e.update(extra)
        decals.append(e)

    st, pos = garderobiere(lights, 228, 290)
    emit(st, pos, 6, 'playfield', 0, 'cloakroom attendant behind the counter (sorts tokens, looks up)', base_y=290)
    st, pos = cleaner(lights, 421, 293)
    emit(st, pos, 7, 'playfield', 0, 'cleaning woman mopping the melt water in the archway', base_y=293)
    st, pos = landing_group(lights, room.lay.c, room.landing_front)
    emit(st, pos, 6, 'room', 2, 'two delegates talking at the gallery door, the usher beside it (stair landing)')
    st, pos = waiter(lights, 761, 294)
    emit(st, pos, 5, 'playfield', 0, 'waiter at the untouched buffet', base_y=294)
    st, pos = interpreter(lights, 0, True)
    emit(st, pos, 6, 'room', 2, 'interpreter at work in booth 1 (FR), seen from behind')
    st, pos = interpreter(lights, 2, False)
    emit(st, pos, 5, 'room', 2, 'interpreter at work in booth 3 (EN), seen from behind')
    st, pos = saal_life(near_pos)
    emit(st, pos, 4, 'saal_near', 1, 'the session through the booth windows: speaker, nods, an usher with a note',
         lit=False)
    st, pos = door_flash()
    emit(st, pos, 6, 'room', 2, 'press flashes behind the etched glass of the Saal doors', lit=False)
    st, pos = pigeon(lights)
    emit(st, pos, 6, '', -60, 'a pigeon on the outer sill of the office window (behind the glass)', lit=False,
         extra={'parallax': [1.0, 1.0]})
    st, pos = second_hand('clock_vestibule', 336, 120)
    emit(st, pos, 1, 'room', 2, 'second hand of the vestibule clock', lit=False)
    st, pos = second_hand('clock_corridor', 1470, 160)
    emit(st, pos, 1, 'room', 2, "second hand of the interpreters' corridor clock", lit=False)
    return files, decals
