"""env_c4p2_karsk_life -- the life strips of L_C4P2_Karsk (who works, who waits, who watches, who looks away).

Scene A (Monday dawn) -- Kolonne 4, ten of the eleven (Maria is the eleventh, a speaking NPC at x 578):
  two shovelling coal out of the gondola on the deck, one breaking frozen coal at the bunker hole with an iron bar,
  one resting on the stair with a basket on her back, one shovelling the spilled coal into a barrow, a young man
  waiting at the barrow handles, an old man on a sleeper eating bread out of newspaper, a woman shovelling toward
  the baskets, a woman winding rags round her hands by the warm ash pit, a woman at the canteen hatch with a tin
  bowl; plus the cook in the hatch and a stoker warming his hands at the water crane's brazier.
Scene B (Tuesday evening) -- the brass band on one beat, five different people (the turntable man bareheaded with the
  helicon -- his cap lies on the controller --, a young fitter and a woman from the wagon shop with trumpets, an older
  man with the horn, a tall stoker with the bass drum), two children, the cleaner polishing the engine's headlamp, the
  canteen's waitress with tea and the cook at the kitchen range, an old fitter oiling the turntable, a smoker in the
  sand-house door, a woman sifting sand, the depot cat; on platform 1 the patrol (grey greatcoats, fur hats), a woman
  holding her permit out to the young militiaman, a man handing a parcel up to a window, children on a suitcase, the
  grandmother, the conductor (navy, silver cap band, lantern), a mother lifting her boy to a window, a couple, the
  pirozhki seller, the porter (quilted jacket, white apron).  Every outdoor figure gives its mouth for the breath puffs.

Every strip is baked in its scene's light at its world position (env_c4p2_karsk_people.Strip).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K
import env_c4p2_karsk_layout as L
import env_c4p2_karsk_people as PP
from env_c4p2_karsk_people import Rig, spec, standing, breathe, _pose, cycle

SA, SB = L.SA, L.SB


class Entry:
    def __init__(self, name, strip, fps, z, scene, desc, t0=None, base_y=None, gate=None):
        self.name, self.strip, self.fps, self.z, self.scene, self.desc = name, strip, fps, z, scene, desc
        self.t0 = t0
        self.base_y = base_y
        self.gate = gate or {}                       # registry gates ("after" / "until") of the decal
        self.mouth = getattr(strip, 'mouth', None)   # world point of the mouth (breath in the frost) or None


def _frame_at(x, base, fw, fh, ox_off=0):
    ox = fw // 2 + ox_off
    oy = fh - 2
    return (int(x - ox), int(base - oy)), ox, oy


def _clip(lay, origin, fw, fh, clip_rect=None, front_rects=()):
    """clip_rect (x0, y0, x1, y1, world): the figure shows only through that opening (a hatch, a doorway);
    front_rects [(x, y, w, h), ...] world: things standing in front of the figure (the kasha pot on the counter)."""
    if clip_rect is not None:
        x0, y0, x1, y1 = (int(v) for v in clip_rect)
        cx0, cy0, cx1, cy1 = x0 - origin[0], y0 - origin[1], x1 - origin[0], y1 - origin[1]
        if cy0 > 0:
            lay.erase(0, 0, fw, cy0)
        if cy1 < fh:
            lay.erase(0, max(0, cy1), fw, fh - max(0, cy1))
        if cx0 > 0:
            lay.erase(0, 0, cx0, fh)
        if cx1 < fw:
            lay.erase(max(0, cx1), 0, fw - max(0, cx1), fh)
    for (x, y, w, h) in front_rects:
        lay.erase(int(x - origin[0]), int(y - origin[1]), int(w), int(h))


def _make(name, sp, x, base, lights, exposure, poses, face=1, fw=36, fh=56, extras=None, ox_off=0, clip_y=None,
          clip_rect=None, front_rects=(), breath=True):
    origin, ox, oy = _frame_at(x, base, fw, fh, ox_off)
    rig = Rig(sp)
    st = PP.Strip(name, fw, fh, origin, lights, exposure)
    for i, p in enumerate(poses):
        lay = K.tlayer(fw, fh, 'fig')
        ex = extras(i) if extras else None
        P = rig.draw(lay, ox, oy, p, face, ex)
        if i == 0 and breath:
            hx_, hy_ = P['head']
            st.mouth = (int(round(origin[0] + hx_ + face * 3)), int(round(origin[1] + hy_ + 2)))
        if clip_y is not None:                                   # hidden behind a wall in front (gondola side)
            cy = int(clip_y - origin[1])
            if 0 <= cy < fh:
                lay.erase(0, cy, fw, fh - cy)
        _clip(lay, origin, fw, fh, clip_rect, front_rects)
        st.add(lay)
    return st, origin


def _breath_cycle(base_pose, n=8, amp=0.5):
    return [breathe(base_pose, k / float(n), amp) for k in range(n)]


# =========================================================================== scene A
def life_a(lights, exposure):
    out = []

    def add(name, st_origin, fps, z, desc, t0=None, base_y=None):
        st, origin = st_origin
        out.append(Entry(name, st, fps, z, SA, desc, t0, base_y))

    # --- in the gondola on the deck: upper bodies over the side, shovelling coal out to the bunker
    gtop = L.DECK_Y - 34
    for k, (x, face, sp, seed) in enumerate((
            (486, 1, spec(coat=('Q', 2.2), quilted=True, head='ushanka', hands='rags', fur=('D', 3.6)), 501),
            (556, -1, spec(coat=('K', 2.6), coat_len='short', head='knit', hat=('U', 3.0), band=('U', 2.2),
                           hands='mittens', mitten=('R', 2.4)), 502))):
        keys, counts = PP.shoveller_poses(44)
        poses = cycle(keys, counts)
        fw, fh = 48, 58
        origin, ox, oy = _frame_at(x, gtop + 16, fw, fh, -8 * face)
        rig = Rig(sp)
        st = PP.Strip('k4_gondola_%d' % k, fw, fh, origin, lights, exposure)
        for i, p in enumerate(poses):
            lay = K.tlayer(fw, fh, 'fig')

            def front(l_, P, f, i=i):
                PP.shovel(l_, P, f, load=i in (3, 4, 5, 6, 7, 8), seed=seed + i)
                if i in (9, 10, 11):
                    hx, hy = P['ha_n']
                    PP.coal_spray(l_, hx + f * 8, hy - 2, (i - 8) / 3.0, seed + 31, spread=7.0 * f)
            rig.draw(lay, ox, oy, p, face, {'front': front})
            cy = int(gtop + 1 - origin[1])
            lay.erase(0, cy, fw, fh - cy)
            st.add(lay)
        out.append(Entry('k4_gondola_%d' % k, st, 8, -44, SA,
                         'Kolonne 4 in the gondola on the deck, shovelling coal out over the side (12 frames)',
                         t0=0.4 * k))

    # --- on the deck: breaking frozen coal at the bunker hole with an iron bar
    H = 42
    up = _pose(H, (0, -20), (2, -34), (4, -38.5), (2, -32.5), (5, -27), (6, -31), (1, -32), (3, -26), (6, -25),
               (2, -10), (4, 0), (-2, -10.5), (-4, 0))
    down = _pose(H, (0, -19), (3, -32), (5, -36.5), (3, -30.5), (6, -24), (6, -19), (2, -30), (4, -23), (6, -14),
                 (2, -9.5), (4, 0), (-2, -10), (-4, 0))
    poses = cycle([up, down, down, up], [2, 1, 2, 3])

    def bar(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.line(int(round(hx)), int(round(hy - 8)), int(round(hx + f * 1)), int(round(hy + 18)), 'I', 3.4)
            l_.px(int(round(hx)), int(round(hy - 8)), 'I', 4.6)
            if i in (3, 4):
                for k in range(4):
                    l_.px(int(round(hx + f * (2 + k))), int(round(hy + 15 - k)), 'X', 3.6 + k * 0.3)
        return {'front': front}
    add('k4_bar', _make('k4_bar', spec(coat=('Q', 2.6), quilted=True, head='scarf', scarf_head=('P', 2.8),
                                       hands='rags', H=H, coat_len='mid', hem_patch=True),
                        426, L.DECK_Y, lights, exposure, poses, face=1, fw=34, fh=58, extras=bar),
        8, -44, 'a woman on the deck breaking frozen coal at the bunker hole with an iron bar (8 frames)')

    # --- on the stair: resting, the basket on her back, a hand on the rail
    H = 40
    rest = _pose(H, (0, -19), (2.5, -32), (4.5, -36.5), (2.5, -30.5), (5, -26), (7, -27), (1, -31), (0, -25),
                 (2, -23), (2, -9), (4, 0), (-2, -10), (-3, -5))
    poses = _breath_cycle(rest, 8, 0.7)

    def basket_back(i):
        def behind(l_, P, f):
            nx, ny = P['neck']
            bx = int(round(nx - f * 9)) - (8 if f > 0 else 0)
            PP.basket(l_, bx, int(round(ny)) - 1, 9, 12, load=True, seed=503)
            l_.line(int(round(nx - f * 2)), int(round(ny)), int(round(nx + f * 2)), int(round(ny + 8)), 'D', 2.0)
        return {'behind': behind}
    add('k4_stair', _make('k4_stair', spec(coat=('M', 2.4), coat_len='mid', head='shawl', scarf_head=('C', 3.2),
                                           boots='felt', hands='rags', H=H),
                          398, 228, lights, exposure, poses, face=1, fw=36, fh=52, extras=basket_back),
        5, -42, 'a woman resting on the stair, a basket of coal on her back (8 frames, breathing)')

    # --- the ground: shoveller into the barrow
    st = PP.make_shoveller('k4_shovel_a', spec(coat=('Q', 2.0), quilted=True, head='ushanka_up', hair=('N', 2.6),
                                               hands='rags', trousers=('C', 1.8)),
                           _frame_at(436, L.A_MID, 48, 58, -8)[0], lights, exposure, face=1, seed=511)
    out.append(Entry('k4_shovel_a', st, 8, -40, SA, 'a man shovelling spilled coal into the barrow (12 frames)',
                     t0=0.0))
    # --- the young man at the barrow handles: hands in his armpits, stamping
    H = 43
    sp = spec(coat=('N', 3.0), coat_len='short', head='flatcap', hat=('C', 2.4), band=('C', 1.6), boots='shoes',
              trousers=('C', 2.2), neck_scarf=('G', 2.4), scarf_tail=True, H=H, opening=False)
    a1 = standing(H, arms='front')
    a1.update({'el_n': (2.0, -H + 18.0), 'ha_n': (-1.0, -H + 15.0), 'el_f': (-1.0, -H + 18.0),
               'ha_f': (2.0, -H + 15.0)})
    a2 = dict(a1)
    a2.update({'ft_n': (1.5, -2.0), 'kn_n': (2.0, -H * 0.24 - 1.0)})
    a3 = dict(a1)
    a3.update({'ft_f': (-1.5, -2.0), 'kn_f': (0.0, -H * 0.24 - 1.0)})
    poses = cycle([a1, a2, a1, a3], [2, 2, 2, 2])
    add('k4_barrow', _make('k4_barrow', sp, 504, L.A_MID, lights, exposure, poses, face=-1, fw=32, fh=56),
        6, -40, 'a young returnee in a thin Western jacket at the barrow, hands in his armpits, stamping (8 frames)')
    # --- the old man on the sleeper by the canteen's bottle crates eating bread (his rest corner: L.REST)
    H = 44
    sit = _pose(H, (0, -9), (0.5, -25), (1.5, -29.5), (0.5, -23.5), (4, -18), (6, -19), (-0.5, -23.5), (2, -17),
                (5, -18), (6, -10), (8, 0), (5, -10.5), (6, 0))
    bite = dict(sit)
    bite.update({'el_n': (4, -21), 'ha_n': (4, -26), 'head': (1.8, -29.8)})
    poses = cycle([sit, sit, bite, bite, sit], [3, 1, 2, 1, 3])

    def bread(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.rect(int(round(hx)) - 1, int(round(hy)) - 3, 3, 2, 'L', 3.0)
            fx_, fy_ = P['ha_f']
            l_.rect(int(round(fx_)) - 2, int(round(fy_)) - 1, 5, 2, 'P', 3.6)
        return {'front': front}
    add('k4_old', _make('k4_old', spec(coat=('K', 2.2), coat_len='mid', head='bare_old', hair=('S', 3.4),
                                       boots='felt', hands='bare', skin=1.8, H=H, patch=('P', 2.2)),
                        L.REST, L.A_MID - 2, lights, exposure, poses, face=1, fw=34, fh=50, extras=bread),
        5, -40, "an old man on a sleeper by the canteen's bottle crates eating bread out of newspaper (10 frames)")
    # --- a woman shovelling toward the baskets (faces left)
    st = PP.make_shoveller('k4_shovel_b', spec(coat=('G', 2.2), coat_len='mid', head='scarf', scarf_head=('U', 3.0),
                                               hands='mittens', mitten=('P', 2.6), H=42),
                           _frame_at(L.SHOVEL_B, L.A_MID, 48, 58, -8)[0], lights, exposure, face=1, H=42,
                           seed=521)
    out.append(Entry('k4_shovel_b', st, 7, -40, SA, 'a woman in a Western coat shovelling coal up toward the '
                                                    'tender (12 frames)', t0=0.7))
    # --- by the ash pit: winding rags round her hands
    H = 42
    w1 = _pose(H, (0, -20), (1.5, -33), (3.5, -37.5), (1.5, -31.5), (5, -26), (6, -24), (0.5, -31.5), (3, -26),
               (5, -23), (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    w2 = dict(w1)
    w2.update({'el_n': (4, -27), 'ha_n': (6, -26), 'el_f': (2, -25), 'ha_f': (5, -22)})
    w3 = dict(w1)
    w3.update({'el_n': (5, -25), 'ha_n': (5, -22), 'el_f': (3, -27), 'ha_f': (6, -25)})
    poses = cycle([w1, w2, w3, w2], [2, 2, 2, 2])

    def rag(i):
        def front(l_, P, f):
            hx, hy = P['ha_f']
            l_.rect(int(round(hx)) - 1, int(round(hy)) - 1, 3, 3, 'P', 3.4)
            l_.line(int(round(hx)), int(round(hy)), int(round(P['ha_n'][0])), int(round(P['ha_n'][1])), 'P', 3.0)
        return {'front': front}
    add('k4_rags', _make('k4_rags', spec(coat=('C', 2.6), coat_len='long', head='scarf', scarf_head=('R', 2.2),
                                         boots='felt', hands='bare', H=H, neck_scarf=('P', 2.4)),
                         606, L.A_MID, lights, exposure, poses, face=1, fw=34, fh=56, extras=rag),
        5, -40, 'a woman winding rags round her hands in the warmth of the ash pit (8 frames)')
    # --- at the canteen hatch: the tin bowl
    H = 41
    b1 = _pose(H, (0, -20), (1.5, -33), (3.5, -37.5), (1.5, -31.5), (5, -26), (8, -25), (0.5, -31.5), (3, -26),
               (7, -25), (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    b2 = dict(b1)
    b2.update({'head': (4.0, -37.0), 'el_n': (5, -28), 'ha_n': (7, -29), 'el_f': (3, -28), 'ha_f': (6, -29)})
    poses = cycle([b1, b1, b2, b2], [3, 2, 3, 2])

    def bowl(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.rect(int(round(hx)) - 2, int(round(hy)) - 2, 5, 2, 'S', 3.6)
            l_.px(int(round(hx)), int(round(hy)) - 3, 'V', 4.0)
        return {'front': front}
    add('k4_bowl', _make('k4_bowl', spec(coat=('M', 3.0), coat_len='long', head='beret', hat=('N', 2.4),
                                         hair=('K', 2.6), boots='shoes', trousers=('N', 2.0), H=H, hands='bare',
                                         neck_scarf=('L', 2.8)),
                         312, L.A_MID - 2, lights, exposure, poses, face=-1, fw=32, fh=54, extras=bowl),
        5, -40, 'a woman in a plum Western coat and a beret at the canteen hatch with her tin bowl (10 frames)')
    # --- the cook in the hatch (behind the counter: upper body, clipped at the counter)
    H = 44
    c1 = _pose(H, (0, -20), (1, -33), (3, -37.5), (1, -31.5), (4, -27), (8, -28), (0, -31.5), (2, -26), (5, -24),
               (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    c2 = dict(c1)
    c2.update({'el_n': (5, -30), 'ha_n': (9, -33)})
    poses = cycle([c1, c2, c2, c1], [3, 2, 1, 2])

    def ladle(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.line(int(round(hx)), int(round(hy)), int(round(hx + f * 4)), int(round(hy + 6)), 'I', 4.4)
            l_.rect(int(round(hx + f * 4)) - 1, int(round(hy + 6)), 3, 2, 'I', 3.6)
        return {'front': front}
    hx_, hy_, hw_, hh_ = L.HATCH
    # he stands back in the kitchen: only head, shoulders and the ladle arm show through the opening (never above
    # its frame, never over the „РАЗДАЧА“ board); the kasha pot and the bowls on the counter stand in front of him
    add('cook_hatch', _make('cook_hatch', spec(coat=('P', 4.6), coat_len='short', head='knit', hat=('P', 5.2),
                                               band=('P', 4.2), hands='bare', H=H, opening=False, skin=2.2),
                            hx_ + 14, hy_ + 44, lights, exposure, poses, face=1, fw=30, fh=56, extras=ladle,
                            clip_rect=(hx_, hy_, hx_ + hw_, hy_ + hh_),
                            front_rects=((hx_ + 4, hy_ + hh_ - 7, 16, 7), (hx_ + 22, hy_ + hh_ - 3, 5, 3)),
                            breath=False),
        6, -47, 'the cook in the serving hatch ladling kasha, seen through the opening (8 frames)')
    # --- a stoker warming his hands at the water crane's brazier
    H = 45
    s1 = _pose(H, (0, -21), (2.5, -34), (4.5, -38.5), (2.5, -32.5), (6, -27), (9, -25), (1.5, -32.5), (4, -27),
               (8, -24), (2, -10.5), (3, 0), (-2, -11), (-3, 0))
    s2 = dict(s1)
    s2.update({'ha_n': (8, -24), 'ha_f': (9, -25)})
    poses = cycle([s1, s2], [4, 4])
    add('stoker', _make('stoker', spec(coat=('N', 2.8), quilted=True, head='railcap', hat=('U', 2.2),
                                       band=('U', 1.4), trousers=('N', 2.0), boots='boots', H=H, hands='gloves'),
                        L.WATER_CRANE - 2, L.A_BACK, lights, exposure, poses, face=1, fw=32, fh=56),
        4, -48, 'a depot stoker warming his hands over the water crane\'s brazier (8 frames)')
    # --- a fitter in the warm stall door, wiping his hands
    H = 44
    f1 = _pose(H, (0, -20), (1, -33), (3, -37.5), (1, -31.5), (4, -26), (5, -22), (0, -31.5), (2, -26), (5, -23),
               (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    f2 = dict(f1)
    f2.update({'ha_n': (6, -24), 'ha_f': (4, -21)})
    poses = cycle([f1, f2, f1, f2], [3, 2, 3, 2])
    da, db = L.STALL_DOORS[0]
    add('fitter_stall', _make('fitter_stall', spec(coat=('N', 1.8), coat_len='short', head='flatcap',
                                                   hat=('N', 1.6), trousers=('N', 1.6), boots='boots', H=H,
                                                   hands='bare', skin=1.6, opening=False),
                              da + 15, L.A_BACK - 2, lights, exposure, poses, face=1, fw=28, fh=56),
        5, -48, 'a fitter in the warm stall door wiping his hands on a rag (10 frames)')
    return out



# =========================================================================== scene B
def _ring(l_, cx, cy, rx, ry, th, ramp, tone, f, hgt=0.9):
    """An elliptic ring (the helicon's coil round the player's body), lit from the upper front."""
    x0, y0 = int(math.floor(cx - rx - 1)), int(math.floor(cy - ry - 1))
    w, h = int(2 * rx + 3), int(2 * ry + 3)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xs + x0 + 0.5 - cx, ys + y0 + 0.5 - cy
    out = (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0
    inn = (dx / max(0.5, rx - th)) ** 2 + (dy / max(0.5, ry - th)) ** 2 <= 1.0
    m = out & ~inn
    t = tone + 1.1 * np.clip(-dy / ry, -1, 1) + 0.5 * np.clip(dx * f / rx, -1, 1)
    l_.put(m, x0, y0, ramp, t, hgt=hgt, flat=False)


def _band_extras(kind, i):
    """The instrument of one band player as Rig.draw hooks (behind / mid / front)."""
    def tuba_behind(l_, P, f):
        # the helicon: a narrow tube climbs from the coil behind the shoulder, then flares into the bell over the
        # head -- its rim an ellipse, the dark mouth inside, brass highlights on the front
        nx, ny = P['neck']
        tx = nx - f * 5.0
        l_.rect(int(round(tx)) - 1, int(round(ny - 7)), 2, 11, 'L', 2.8, hgt=0.9)       # the tube
        l_.rect(int(round(tx)) - (0 if f > 0 else 1), int(round(ny - 7)), 1, 11, 'L', 4.0)
        for k in range(6):                                                # the flare, widening upward
            yy = int(round(ny - 8 - k))
            half = 1.5 + k * 0.95
            cx_ = tx + f * (0.4 * k)
            l_.rect(int(round(cx_ - half)), yy, int(round(2 * half)) + 1, 1, 'L', 2.6 + k * 0.25, hgt=0.9)
            l_.px(int(round(cx_ + f * (half - 0.5))), yy, 'L', 4.4)
        rx_, ry_ = tx + f * 2.6, ny - 14.5                                 # the rim and the dark mouth
        m, x0, y0 = l_.ellipse_mask(rx_, ry_, 6.2, 2.0)
        l_.put(m, x0, y0, 'L', 4.8, hgt=1.0)
        m2, x2, y2 = l_.ellipse_mask(rx_, ry_ + 0.3, 4.6, 1.0)
        l_.put(m2, x2, y2, 'L', 1.0, hgt=0.4)

    def tuba_mid(l_, P, f):
        nx, ny = P['neck']
        hx, hy = P['hip']
        cx, cy = (nx + hx) / 2.0 + f * 1.0, (ny + hy) / 2.0 + 1.0
        _ring(l_, cx, cy, 8.0, 6.0, 2.2, 'L', 3.0, f)
        l_.px(int(round(cx + f * 3)), int(round(cy - 5)), 'L', 5.0)          # a glint on the coil

    def tuba_front(l_, P, f):
        nx, ny = P['neck']
        hx, hy = P['hip']
        cx, cy = (nx + hx) / 2.0 + f * 1.0, (ny + hy) / 2.0 + 1.0
        ax, ay = P['ha_n']
        for k in range(3):                                               # three valves under the fingers
            vx = int(round(ax - f * 1 + f * k * 2))
            l_.rect(vx, int(round(ay)) - 1, 1, 4, 'L', 3.8)
            l_.px(vx, int(round(ay)) - 2, 'S', 5.0)
        hdx, hdy = P['head']
        l_.line(int(round(hdx + f * 3)), int(round(hdy + 2)), int(round(cx + f * 5)), int(round(cy - 4)), 'L', 3.6)
        l_.px(int(round(hdx + f * 3)), int(round(hdy + 2)), 'L', 4.6)        # the mouthpiece

    def drum_front(l_, P, f):
        # a marching bass drum: its heads face the player's sides, so in profile we see the round head -- a cream
        # disc in a red hoop with brass rods, hung on a sling in front of the belly; the felt beater strikes it
        nx, ny = P['neck']
        cx, cy = nx + f * 5.5, ny + 13.0
        l_.line(int(round(nx - f * 2)), int(round(ny)), int(round(cx)), int(round(cy - 8)), 'D', 2.0)   # the sling
        m, x0, y0 = l_.ellipse_mask(cx, cy, 8.5, 8.5)
        l_.put(m, x0, y0, 'R', 2.6, hgt=0.9)                              # the hoop
        m2, x2, y2 = l_.ellipse_mask(cx, cy, 6.8, 6.8)
        sub_t = np.full(m2.shape, 4.6, np.float32)
        ys_, xs_ = np.mgrid[0:m2.shape[0], 0:m2.shape[1]].astype(np.float32)
        sub_t += np.clip((-(ys_ + y2 - cy) - (xs_ + x2 - cx) * f) / 8.0, -1, 1) * 0.6   # the head, lit upper front
        l_.put(m2, x2, y2, 'P', sub_t, hgt=0.7, flat=False)
        for k in range(8):                                                # brass tension rods round the hoop
            ang = k * math.pi / 4 + 0.39
            l_.px(int(round(cx + 7.8 * math.cos(ang))), int(round(cy + 7.8 * math.sin(ang))), 'L', 4.4)
        bx, by = P['ha_n']
        hit = (i % 4) in (0, 1)
        tx_, ty_ = (cx - f * 1.5, cy - 1.0) if hit else (bx + f * 1, by - 5)
        l_.line(int(round(bx)), int(round(by)), int(round(tx_)), int(round(ty_)), 'D', 4.0)   # the beater
        l_.rect(int(round(tx_)) - 1, int(round(ty_)) - 1, 3, 3, 'P', 3.2)
        l_.px(int(round(tx_)), int(round(ty_)) - 1, 'P', 5.4)

    def brass_front(l_, P, f):
        hdx, hdy = P['head']
        mx, my = hdx + f * 4, hdy + 2
        if kind == 'horn':
            cx, cy = int(round(hdx + f * 5)), int(round(hdy + 7))
            m, x0, y0 = l_.ellipse_mask(cx, cy, 3, 3)
            l_.put(m, x0, y0, 'L', 3.8, hgt=0.9)
            l_.put(K.edge_of(m), x0, y0, 'L', 2.4)
            l_.rect(cx - 1, cy - 5, 3, 3, 'L', 4.6)
            l_.line(int(round(mx)), int(round(my)), cx, cy, 'L', 3.0)
        else:
            l_.rect(int(round(mx)) - (0 if f > 0 else 8), int(round(my)), 8, 1, 'L', 4.4, hgt=0.9)
            bx = int(round(mx + f * 8))
            l_.rect(bx - 1, int(round(my - 1)), 2, 3, 'L', 4.8, hgt=0.9)
            l_.rect(int(round(mx + f * 3)), int(round(my + 1)), 3, 1, 'L', 3.4)

    if kind == 'tuba':
        return {'behind': tuba_behind, 'mid': tuba_mid, 'front': tuba_front}
    if kind == 'drum':
        return {'front': drum_front}
    return {'front': brass_front}


def life_b(lights, exposure):
    out = []

    def add(name, st_origin, fps, z, desc, t0=None, gate=None):
        st, origin = st_origin
        out.append(Entry(name, st, fps, z, SB, desc, t0, gate=gate))

    # --- the band on its plank stage (top y 280), facing left toward the arrivals: five different people, one beat.
    #     The tuba is the turntable man (explore: his cap lies on the controller) -- bare grey head, his sheepskin.
    stage_y = 281
    band = (
        ('tuba', 1101, 45, 0.5, 'the turntable man, bare grey head and moustache, his sheepskin, the helicon',
         spec(coat=('P', 2.4), coat_len='long', head='bare_moust', hair=('S', 3.0), skin=1.9, boots='felt',
              trousers=('U', 1.6), hands='bare', width=1.25, collar=('P', 4.4), opening=True)),
        ('trumpet', 1113, 44, 0.7, 'a young fitter, blond, the band cap pushed back, a grey scarf',
         spec(coat=('U', 2.6), coat_len='mid', head='railcap_young', hat=('U', 2.2), band=('R', 2.6),
              hair=('P', 3.4), boots='boots', trousers=('U', 1.8), hands='bare', width=0.9, buttons=(4, 8, 12),
              belt=('N', 1.4), neck_scarf=('C', 3.2), scarf_tail=True, opening=False)),
        ('trumpet2', 1125, 41, 0.6, 'a woman from the wagon shop in a fur hat and a long coat, a red scarf',
         spec(coat=('U', 3.0), coat_len='long', head='furhat_f', fur=('D', 2.6), hat=('D', 3.0), hair=('K', 2.6),
              boots='felt', hands='bare', width=0.85, neck_scarf=('R', 2.8), buttons=(4, 8), opening=False)),
        ('horn', 1137, 44, 0.4, 'an older man with a grey moustache under the band cap',
         spec(coat=('U', 2.2), coat_len='mid', head='railcap_moust', hat=('U', 1.8), band=('R', 2.4),
              hair=('S', 2.4), skin=1.8, boots='boots', trousers=('U', 1.6), hands='bare', width=1.05,
              buttons=(4, 8, 12), belt=('N', 1.4), opening=False)),
        ('drum', 1149, 47, 0.8, 'a tall young stoker in his quilted jacket and ushanka, the bass drum on a sling',
         spec(coat=('Q', 2.6), quilted=True, coat_len='short', head='ushanka_up', fur=('C', 3.4), hat=('C', 2.6),
              hair=('N', 2.4), boots='felt', trousers=('U', 1.6), hands='bare', width=0.95)),
    )
    for kind, x, H, amp, who, sp in band:
        b0 = _pose(H, (0, -20), (-0.5, -33), (1, -37.5), (-0.5, -31.5), (3, -27), (6, -32.5), (-1.5, -31.5),
                   (2, -27), (5, -31), (1.5, -10), (3, 0), (-2, -10.5), (-3, 0))
        if kind == 'tuba':
            b0.update({'el_n': (4, -24), 'ha_n': (8, -27), 'el_f': (2, -24), 'ha_f': (6, -25), 'ft_n': (4, 0),
                       'ft_f': (-4, 0)})
        elif kind == 'drum':
            b0.update({'el_n': (7, -25), 'ha_n': (13, -24), 'el_f': (3, -24), 'ha_f': (8, -27)})
        bob = []
        for i in range(8):
            p = dict(b0)
            d = amp if i % 4 in (0, 1) else 0.0                          # the same beat for all five
            for j in ('neck', 'head', 'sh_n', 'sh_f', 'el_n', 'el_f', 'ha_n', 'ha_f', 'hip'):
                x_, y_ = p[j]
                p[j] = (x_, y_ + d)
            bob.append(p)
        ex = (lambda kind_: (lambda i: _band_extras(kind_, i)))(kind)
        add('band_%s' % kind, _make('band_%s' % kind, dict(sp, H=H), x, stage_y, lights, exposure, bob, face=-1,
                                    fw=40, fh=60, extras=ex),
            6, -42, 'the railway workers\' brass band, %s: %s (8 frames, in time with the others)' % (kind, who),
            t0=0.0)
    # --- children sitting on the stage edge, swinging their felt boots
    H = 28
    sitg = _pose(H, (0, -6), (0.5, -20), (1.5, -24.5), (0.5, -18.5), (2, -13), (3, -10), (-0.5, -18.5), (1, -13),
                 (2, -10), (5, -6), (5, 3), (4, -6.5), (4, 3))
    sitg2 = dict(sitg)
    sitg2.update({'ft_f': (7, 1), 'head': (2.2, -24.5)})
    poses = cycle([sitg, sitg2], [5, 3])
    add('child_watch', _make('child_watch', spec(coat=('R', 2.4), coat_len='mid', head='hood', hat=('R', 2.0),
                                                 boots='felt', trousers=('N', 2.0), H=H, hands='mittens',
                                                 mitten=('P', 3.6), width=0.8),
                             1096, stage_y, lights, exposure, poses, face=-1, fw=26, fh=40),
        5, -41, 'a girl in a red hooded coat on the edge of the band stage (8 frames)')
    H = 30
    sit = _pose(H, (0, -6), (0.5, -21), (1.5, -25.5), (0.5, -19.5), (2, -14), (3, -11), (-0.5, -19.5), (1, -14),
                (2, -11), (5, -6), (5, 3), (4, -6.5), (4, 3))
    sit2 = dict(sit)
    sit2.update({'ft_n': (7, 1), 'ft_f': (3, 3)})
    poses = cycle([sit, sit2], [4, 4])
    add('child_sit', _make('child_sit', spec(coat=('U', 3.0), coat_len='short', head='ushanka', fur=('D', 4.0),
                                             boots='felt', trousers=('N', 2.4), H=H, hands='mittens', width=0.8),
                           1157, stage_y, lights, exposure, poses, face=1, fw=26, fh=40),
        6, -41, 'a boy in an ushanka on the edge of the band stage, swinging his felt boots (8 frames)')
    # --- the cleaner polishing the engine's headlamp
    H = 42
    p1 = _pose(H, (0, -20), (2, -33), (4, -37.5), (2, -31.5), (5, -35), (7, -39), (1, -31.5), (3, -26), (5, -24),
               (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    p2 = dict(p1)
    p2.update({'el_n': (6, -34), 'ha_n': (8, -37)})
    p3 = dict(p1)
    p3.update({'el_n': (4, -35), 'ha_n': (6, -40)})
    poses = cycle([p1, p2, p3, p2], [2, 2, 2, 2])

    def rag_(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.rect(int(round(hx)) - 1, int(round(hy)) - 1, 3, 3, 'P', 4.8)
        return {'front': front}
    add('cleaner_engine', _make('cleaner_engine', spec(coat=('U', 2.6), quilted=True, head='scarf',
                                                       scarf_head=('P', 4.0), boots='felt', H=H, hands='bare',
                                                       apron=('P', 3.0)),
                                L.LOCO[0] + 6, L.A_MID, lights, exposure, poses, face=1, fw=30, fh=56, extras=rag_),
        6, -36, 'a cleaner in a white headscarf polishing the engine\'s headlamp for the guest (8 frames)')
    # --- the canteen: the waitress with a tray of tea; the cook at the kitchen range beside the curtain
    H = 42
    w1 = _pose(H, (0, -20), (0.5, -33), (2.5, -37.5), (0.5, -31.5), (3.5, -27), (7, -27), (-0.5, -31.5),
               (2.5, -27), (6, -27), (1.5, -10), (2, 0), (-1.5, -10.5), (-2, 0))
    w2 = dict(w1)
    w2.update({'head': (1.8, -37.0)})
    poses = cycle([w1, w2], [5, 5])

    def tray(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            x0 = int(round(hx)) - (2 if f > 0 else 6)
            l_.rect(x0, int(round(hy)) - 1, 9, 1, 'I', 4.6)
            for k in range(3):
                l_.rect(x0 + 1 + k * 3, int(round(hy)) - 4, 2, 3, 'L', 3.6 + (k % 2) * 0.6)
                l_.px(x0 + 1 + k * 3, int(round(hy)) - 4, 'S', 5.0)
        return {'front': front}
    add('waitress', _make('waitress', spec(coat=('N', 2.4), coat_len='mid', head='bun', hair=('K', 2.2),
                                           boots='shoes', H=H, hands='bare', apron=('P', 5.4), collar=('P', 5.6),
                                           trousers=('Y', 1.4), opening=False),
                          1208, L.A_MID, lights, exposure, poses, face=-1, fw=30, fh=56, extras=tray, breath=False),
        4, -38, 'the canteen\'s waitress with a tray of tea glasses (10 frames)')
    H = 44
    k1 = _pose(H, (0, -20), (2, -33), (4, -37.5), (2, -31.5), (6, -27), (8, -24), (1, -31.5), (4, -26), (7, -23),
               (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    k2 = dict(k1)
    k2.update({'ha_n': (9, -25), 'el_n': (6, -28)})
    poses = cycle([k1, k2, k1, k2], [2, 2, 2, 2])

    def spoon(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.line(int(round(hx)), int(round(hy)), int(round(hx + f * 2)), int(round(hy + 6)), 'D', 4.0)
        return {'front': front}
    add('cook_curtain', _make('cook_curtain', spec(coat=('P', 4.4), coat_len='mid', head='knit', hat=('P', 5.0),
                                                   band=('P', 4.0), boots='shoes', H=H, hands='bare', opening=False),
                              L.KITCHEN_COOK, L.A_MID - 4, lights, exposure, poses, face=1, fw=30, fh=56,
                              extras=spoon, breath=False),
        5, -47, 'the cook beside the curtain stirring the band\'s kasha on the range (8 frames)')
    # --- the turntable: an old fitter oiling the bridge's running wheel
    H = 43
    o1 = _pose(H, (-2, -18), (5, -30), (8.5, -33.5), (5, -28.5), (8, -21), (10, -14), (4, -28), (6, -21), (9, -15),
               (1, -9.5), (3, 0), (-4, -9.5), (-5, 0))
    o2 = dict(o1)
    o2.update({'ha_n': (10.5, -12.5), 'ha_f': (9.5, -13.5)})
    poses = cycle([o1, o1, o2, o2], [2, 2, 2, 2])

    def oilcan(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            x0, y0 = int(round(hx)), int(round(hy))
            l_.rect(x0 - 2, y0, 5, 4, 'I', 3.4, hgt=0.8)                 # the can
            l_.rect(x0 - 2, y0, 5, 1, 'I', 5.0)
            l_.line(x0 + f * 2, y0 + 1, x0 + f * 4, y0 + 6, 'I', 4.0)     # the long spout to the wheel
            if i in (5, 6):
                l_.px(x0 + f * 4, y0 + 8, 'L', 2.6)                       # a drop of oil
        return {'front': front}
    add('oiler_turntable', _make('oiler_turntable', spec(coat=('Q', 2.0), quilted=True, coat_len='mid',
                                                         head='ushanka', fur=('D', 3.0), hat=('D', 2.4),
                                                         boots='felt', H=H, hands='mittens', mitten=('N', 2.4),
                                                         apron=('D', 1.8), trousers=('N', 2.0), skin=1.8),
                                 L.OILER, L.A_MID, lights, exposure, poses, face=1, fw=34, fh=56, extras=oilcan),
        5, -40, 'an old fitter oiling the turntable\'s running wheel from a long-spouted can (8 frames)')
    # --- the sand-drying house: a man smoking in the doorway, a woman sifting sand, the depot cat on the warm sand
    H = 44
    d0 = standing(H, lean=-0.2, arms='pockets')
    d0.update({'el_n': (2, -H + 19), 'ha_n': (3, -H + 15)})
    d1 = dict(d0)
    d1.update({'el_n': (3, -H + 16), 'ha_n': (3.5, -H + 7.5)})          # the cigarette to the lips
    poses = cycle([d0, d0, d1, d0], [3, 2, 2, 3])

    def cig(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.px(int(round(hx + f * 1)), int(round(hy)) - 1, 'P', 5.4)
            l_.rect(int(round(hx + f * 2)), int(round(hy)) - 1, 1, 1, 'L', 5.0, emis=True)    # the ember
            if i in (6, 7, 8):
                hdx, hdy = P['head']
                for k in range(3):
                    l_.px(int(round(hdx + f * (4 + k))), int(round(hdy + 1 - k * 2 - (i - 6))), 'V', 4.4)
        return {'front': front}
    add('sand_door_smoker', _make('sand_door_smoker', spec(coat=('N', 2.6), coat_len='short', head='flatcap',
                                                           hat=('K', 2.0), band=('K', 1.6), boots='boots',
                                                           trousers=('N', 2.2), H=H, hands='bare',
                                                           neck_scarf=('M', 2.6), opening=True),
                                  L.SAND_DOOR_SMOKER, L.A_MID - 2, lights, exposure, poses, face=-1, fw=30, fh=56,
                                  extras=cig, breath=False),
        5, -41, 'a sand-house man smoking in the doorway, watching the band (10 frames)')
    H = 41
    v0 = _pose(H, (0, -20), (2, -33), (4, -37.5), (2, -31.5), (6, -27), (9, -24), (1, -31.5), (5, -26), (8, -24),
               (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    poses = []
    for j in range(8):
        p = dict(v0)
        s_ = 1.0 if j % 2 == 0 else -1.0                                   # shaking the sieve
        p.update({'ha_n': (9 + s_, -24), 'ha_f': (8 + s_, -24), 'el_n': (6 + s_ * 0.5, -27),
                  'el_f': (5 + s_ * 0.5, -26)})
        poses.append(p)

    def sieve(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            cx, cy = int(round(hx + f * 3)), int(round(hy)) + 1
            l_.rect(cx - 6, cy, 13, 2, 'D', 3.4, hgt=0.8)                 # the rim
            l_.rect(cx - 5, cy + 2, 11, 1, 'I', 2.6)                      # the mesh
            l_.rect(cx - 4, cy - 1, 9, 1, 'L', 3.2)                       # damp sand in it
            rng = np.random.default_rng(900 + i)
            for k in range(7):                                            # dry sand sifting into the box
                l_.px(cx - 4 + int(rng.integers(0, 9)), cy + 4 + int(rng.integers(0, 8)), 'L', 3.0 + rng.random())
        return {'front': front}
    add('sand_sieve', _make('sand_sieve', spec(coat=('Q', 2.8), quilted=True, coat_len='mid', head='scarf',
                                               scarf_head=('P', 4.6), boots='felt', H=H, hands='bare',
                                               apron=('D', 2.4), skin=2.1),
                            L.SAND_SIEVE, L.A_MID - 2, lights, exposure, poses, face=-1, fw=34, fh=56, extras=sieve,
                            breath=False),
        6, -41, 'a woman of the sand house sifting dried sand into a box (8 frames)')
    out.append(Entry('cat_sand', _cat(lights, exposure), 4, -40, SB,
                     'the depot cat asleep on the warm dry sand by the stove, ear and tail twitching (8 frames)'))
    # --- platform 1 (left -> right) as the explore texts tell it: the patrol at the gate, a woman holding her
    #     permit out to the young militiaman (he reads it twice), a man handing a parcel up to a window, a boy on the
    #     suitcase eating a pirozhok, the grandmother (side task), the conductor (side task), a mother lifting her
    #     boy to a window, [the vestibule door: Ekdahl], a couple saying goodbye, the pirozhki seller, the porter.
    #     The patrol wears grey winter greatcoats (red collar tabs, belts, holsters) and fur hats with a plain
    #     cockade; the railwaymen wear navy -- nobody reads as the other.
    H = 45
    s0 = standing(H, arms='hang')
    s0.update({'el_n': (-2, -H + 18), 'ha_n': (-4.5, -H + 23), 'el_f': (-3, -H + 18), 'ha_f': (-5, -H + 23)})
    poses = [breathe(s0, j / 8.0, 0.3) for j in range(8)]
    add('militia_0', _make('militia_0', spec(coat=('C', 2.6), coat_len='long', head='militia_winter_m',
                                             fur=('C', 3.4), hair=('N', 2.0), boots='boots', trousers=('U', 1.6),
                                             H=H, hands='gloves', belt=('D', 2.0), holster=('D', 2.6),
                                             buttons=(3, 7, 11), collar=('R', 2.6), opening=False, width=1.15),
                           1580, L.A_MID, lights, exposure, poses, face=1, fw=30, fh=58),
        3, -38, 'the older militiaman of the patrol in the gate, hands behind his back (8 frames)')
    H = 47
    r0 = standing(H, lean=0.3, arms='front')
    r0.update({'el_n': (2.5, -H + 19), 'ha_n': (4.5, -H + 22), 'el_f': (1.5, -H + 19), 'ha_f': (4, -H + 23)})
    poses = []
    for j in range(8):                                                    # reading it twice: the head goes along
        p = breathe(r0, j / 8.0, 0.25)
        p['head'] = (p['head'][0] + 0.6 + (0.0 if j % 4 < 2 else 0.8), p['head'][1] + 0.6)
        poses.append(p)
    add('militia_1', _make('militia_1', spec(coat=('C', 2.2), coat_len='long', head='militia_winter',
                                             fur=('C', 3.0), hair=('N', 2.4), boots='boots', trousers=('U', 1.6),
                                             H=H, hands='gloves', belt=('D', 2.0), holster=('D', 2.6),
                                             buttons=(3, 7, 11), collar=('R', 2.6), opening=False, width=0.9),
                           1604, L.A_MID, lights, exposure, poses, face=1, fw=30, fh=60),
        3, -38, 'the young militiaman reading a Corridor permit twice, once for each language (8 frames)')
    H = 41
    w0 = _pose(H, (0, -20), (1.5, -33), (3.5, -37.5), (1.5, -31.5), (5, -31), (9, -33), (0.5, -31.5), (3, -27),
               (5, -26), (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    w1 = dict(w0)
    w1.update({'ha_n': (9, -34), 'head': (3.6, -37.8)})
    poses = cycle([w0, w1], [4, 4])

    def permit(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            x0 = int(round(hx)) - (0 if f > 0 else 5)
            l_.rect(x0, int(round(hy)) - 5, 6, 5, 'P', 5.4)               # the permit: two stamps, typed lines
            l_.px(x0 + 1, int(round(hy)) - 4, 'U', 3.0)
            l_.px(x0 + 4, int(round(hy)) - 2, 'R', 3.0)
            l_.rect(x0 + 1, int(round(hy)) - 2, 2, 1, 'N', 2.4)
        return {'front': front}
    add('family_permit', _make('family_permit', spec(coat=('G', 3.0), coat_len='long', head='scarf',
                                                     scarf_head=('P', 4.2), boots='felt', H=H, hands='bare'),
                               1620, L.A_MID, lights, exposure, poses, face=-1, fw=30, fh=58, extras=permit),
        4, -38, 'a woman holding her Corridor permit with two stamps out to the militiaman (8 frames)')
    H = 45
    u0 = standing(H, arms='front')
    u0.update({'el_n': (3.5, -H + 3), 'ha_n': (6, -H - 4), 'el_f': (2.5, -H + 4), 'ha_f': (5, -H - 3),
               'head': (1.0, -H + 4.0)})
    u1 = dict(u0)
    u1.update({'el_n': (4, -H + 2), 'ha_n': (6.5, -H - 6), 'el_f': (3, -H + 3), 'ha_f': (5.5, -H - 5)})
    poses = cycle([u0, u1], [4, 4])

    def lift_parcel(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            x0 = int(round(hx)) - (2 if f > 0 else 7)
            l_.rect(x0, int(round(hy)) - 6, 9, 6, 'P', 3.4)               # the parcel, tied with string
            l_.rect(x0, int(round(hy)) - 3, 9, 1, 'D', 2.0)
            l_.rect(x0 + 4, int(round(hy)) - 6, 1, 6, 'D', 2.0)
            wx = x0 + (6 if f > 0 else 1)                                 # a traveller reaches down for it
            l_.rect(wx, int(round(hy)) - 12, 2, 6, 'K', 2.4)
            l_.rect(wx, int(round(hy)) - 7, 2, 2, 'Y', 2.2)
        return {'front': front}
    add('family_parcel', _make('family_parcel', spec(coat=('N', 2.6), coat_len='mid', head='ushanka_up',
                                                     fur=('D', 3.0), hair=('N', 2.4), boots='boots', H=H,
                                                     trousers=('C', 1.8)),
                               1640, L.A_MID, lights, exposure, poses, face=1, fw=30, fh=64, extras=lift_parcel),
        4, -38, 'a man handing a parcel up to a traveller at the sleeping car\'s window (8 frames)')
    kid_a = Rig(spec(coat=('R', 2.8), coat_len='mid', head='hood', hat=('R', 2.4), boots='felt', H=24,
                     hands='mittens', mitten=('P', 3.6), width=0.75))
    kid_b = Rig(spec(coat=('U', 3.2), coat_len='short', head='ushanka', fur=('D', 4.0), boots='felt', H=26,
                     hands='mittens', width=0.75))
    fw, fh = 34, 40
    origin, ox, oy = _frame_at(1660, L.A_MID, fw, fh)
    st = PP.Strip('family_kids', fw, fh, origin, lights, exposure)

    def pie(l_, P, f):
        hx, hy = P['ha_n']
        l_.rect(int(round(hx)) - 1, int(round(hy)) - 2, 3, 2, 'L', 3.4)          # a pirozhok
        l_.px(int(round(hx)), int(round(hy)) - 2, 'L', 4.4)
    for j in range(8):
        lay = K.tlayer(fw, fh, 'fig')
        lay.rect(ox - 12, oy - 7, 22, 8, 'K', 2.6, hgt=0.7)                # the suitcase
        lay.rect(ox - 12, oy - 7, 22, 1, 'K', 3.8)
        lay.rect(ox - 2, oy - 9, 4, 2, 'N', 1.4)
        swing = 1 if j % 4 in (1, 2) else 0
        sa_ = _pose(24, (0, -7), (0.5, -18), (1.2, -21.5), (0.5, -16.5), (2, -12), (3, -10), (0, -16.5), (1, -12),
                    (2, -10), (4, -7), (4 + swing, 1), (3, -7.5), (3, 1))
        kid_a.draw(lay, ox - 7, oy - 7, sa_, 1)
        bite = j % 4 in (1, 2)
        sb2 = _pose(26, (0, -7), (0.5, -19), (1.3, -22.5), (0.5, -17.5), (2.5, -15),
                    (3.5, -20) if bite else (4, -16), (0, -17.5), (1.5, -13), (2, -11), (4, -7), (4, 1), (3, -7.5),
                    (3 + (1 - swing), 1))
        kid_b.draw(lay, ox + 6, oy - 7, sb2, -1, {'front': pie})
        st.add(lay)
    st.mouth = (origin[0] + ox + 2, origin[1] + oy - 27)
    out.append(Entry('family_kids', st, 5, -37, SB, 'two children on a suitcase; the boy eats a pirozhok (8 frames)'))
    # the grandmother with her parcel (side task „Ein Paket über die Linie“)
    H = 39
    g0 = standing(H, lean=0.4, arms='front')
    g0.update({'el_n': (3, -H + 18), 'ha_n': (5, -H + 19), 'el_f': (2, -H + 18), 'ha_f': (4, -H + 20),
               'neck': (2.0, -H + 10.5), 'head': (3.0, -H + 6.0)})
    poses = cycle([g0, breathe(g0, 0.25, 0.6), g0, breathe(g0, 0.75, 0.6)], [3, 2, 3, 2])

    def gparcel(i):
        def front(l_, P, f):
            nx, ny = P['neck']
            x0 = int(round(nx + f * 1)) - (0 if f > 0 else 8)
            l_.rect(x0, int(round(ny)) + 5, 8, 8, 'P', 3.0)
            l_.rect(x0, int(round(ny)) + 8, 8, 1, 'D', 1.6)
            l_.rect(x0 + 3, int(round(ny)) + 5, 1, 8, 'D', 1.6)
            l_.rect(x0 + 2, int(round(ny)) + 4, 3, 1, 'D', 2.4)
        return {'mid': front}
    add('granny_parcel', _make('granny_parcel', spec(coat=('K', 2.4), coat_len='long', head='shawl',
                                                     scarf_head=('C', 3.4), boots='felt', H=H, hands='bare',
                                                     skin=1.8, apron=('M', 2.0)),
                               1680, L.A_MID, lights, exposure, poses, face=1, fw=30, fh=54, extras=gparcel),
        4, -38, 'the grandmother with a parcel tied with string for her son in Veltrava (side task, 10 frames)')
    # the sleeping car's conductor: navy uniform, silver cap band, shirt and tie, the ticket pouch, a lit lantern
    H = 44
    c0 = standing(H, arms='hang')
    c0.update({'el_n': (3, -H + 18), 'ha_n': (5, -H + 24)})
    poses = [breathe(c0, j / 8.0, 0.3) for j in range(8)]

    def lamp(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            l_.rect(int(round(hx)) - 1, int(round(hy)), 3, 4, 'I', 2.6)
            l_.rect(int(round(hx)) - 1, int(round(hy)) + 1, 3, 2, 'L', 5.0, emis=True)
            hx2, hy2 = P['hip']
            l_.rect(int(round(hx2 + f * 2)) - 2, int(round(hy2)) - 3, 5, 4, 'D', 2.0)     # ticket pouch
            l_.rect(int(round(hx2 + f * 2)) - 2, int(round(hy2)) - 3, 5, 1, 'D', 3.0)
        return {'front': front}
    add('conductor', _make('conductor', spec(coat=('U', 2.8), coat_len='mid', head='railcap', hat=('U', 2.4),
                                             band=('S', 4.4), hair=('K', 2.2), boots='boots', H=H, hands='bare',
                                             buttons=(3, 6, 9, 12), tie=('N', 1.2), opening=True, width=1.05,
                                             trousers=('U', 2.0)),
                           1728, L.A_MID, lights, exposure, poses, face=-1, fw=30, fh=58, extras=lamp),
        3, -38, 'the sleeping car\'s conductor: navy uniform, silver cap band, shirt and tie, ticket pouch, a lit '
                'lantern (side task, 8 frames)')
    # a mother lifting her boy to the express window
    H = 42
    m0 = _pose(H, (0, -20), (1.5, -33), (3.5, -37.5), (1.5, -31.5), (4, -35), (6, -38), (0.5, -31.5), (3, -28),
               (5, -30), (2, -10), (3, 0), (-2, -10.5), (-3, 0))
    poses = [breathe(m0, j / 8.0, 0.4) for j in range(8)]
    boy = Rig(spec(coat=('G', 2.8), coat_len='short', head='ushanka', fur=('D', 3.6), boots='felt', H=24,
                   hands='mittens', mitten=('R', 3.0), width=0.75))

    def lift(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            wave = (i % 4) in (1, 2)
            bp = _pose(24, (0, -11), (0.5, -18), (1.2, -21), (0.5, -17), (2.5, -20), (3 + (1 if wave else 0),
                       -24 - (2 if wave else 0)), (0, -17), (1.5, -14), (2, -12), (2, -6), (1, 0), (-1, -6), (-1, 0))
            boy.draw(l_, int(round(hx + f * 1)), int(round(hy + 8)), bp, f)
        return {'front': front}
    add('mother_window', _make('mother_window', spec(coat=('K', 3.0), coat_len='long', head='scarf',
                                                     scarf_head=('G', 3.4), boots='felt', H=H, hands='bare'),
                               1748, L.A_MID, lights, exposure, poses, face=-1, fw=34, fh=64, extras=lift),
        5, -38, 'a mother lifting her boy to the express window; he waves (8 frames)')
    # a couple saying goodbye (two figures, one strip)
    H1, H2 = 45, 41
    man = _pose(H1, (0, -21), (1.5, -34), (3, -38.5), (1.5, -32.5), (4, -30), (7, -32), (0.5, -32.5), (3, -29),
                (6, -31), (2, -10.5), (3, 0), (-2, -11), (-3, 0))
    wom = _pose(H2, (0, -19), (1.0, -31), (2.5, -35.5), (1.0, -29.5), (3.5, -27), (6, -29), (0, -29.5), (2.5, -26),
                (5, -27), (2, -9.5), (3, 0), (-2, -10), (-3, 0))
    rm = Rig(spec(coat=('N', 2.6), coat_len='long', head='felthat', hat=('N', 1.8), boots='shoes', H=H1,
                  trousers=('N', 1.8), neck_scarf=('P', 3.4), scarf_tail=True))
    rw = Rig(spec(coat=('M', 3.0), coat_len='long', head='shawl', scarf_head=('P', 3.6), boots='felt', H=H2))
    fw, fh = 40, 58
    origin, ox, oy = _frame_at(1826, L.A_MID, fw, fh)
    st = PP.Strip('couple', fw, fh, origin, lights, exposure)
    for j in range(8):
        lay = K.tlayer(fw, fh, 'fig')
        d = math.sin(j / 8.0 * 2 * math.pi) * 0.6
        rm.draw(lay, ox - 5, oy, breathe(man, j / 8.0, 0.4), 1)
        rw.draw(lay, ox + 6 + int(round(d)), oy, breathe(wom, (j + 4) / 8.0, 0.4), -1)
        st.add(lay)
    st.mouth = (origin[0] + ox - 5 + 6, origin[1] + oy - 36)
    out.append(Entry('couple', st, 4, -38, SB, 'a couple saying goodbye at the express (8 frames)'))
    # the pirozhki seller: a tray hung from her neck, steam
    H = 41
    v0 = standing(H, arms='front')
    v0.update({'el_n': (4, -H + 19), 'ha_n': (8, -H + 22), 'el_f': (2, -H + 19), 'ha_f': (7, -H + 23)})
    v1 = dict(v0)
    v1.update({'el_n': (5, -H + 15), 'ha_n': (9, -H + 13)})
    poses = cycle([v0, v0, v1, v0], [3, 2, 2, 3])

    def tray2(i):
        def front(l_, P, f):
            nx, ny = P['neck']
            x0 = int(round(nx + f * 3)) - (0 if f > 0 else 11)
            y0 = int(round(ny + 13))
            l_.rect(x0, y0, 11, 3, 'D', 3.0)
            for k in range(4):
                l_.rect(x0 + 1 + k * 3, y0 - 1, 2, 1, 'L', 4.0)
            l_.line(int(round(nx)), int(round(ny + 1)), x0 + (0 if f > 0 else 10), y0, 'D', 2.0)
            if i % 5 == 0:
                l_.px(x0 + 4, y0 - 3, 'V', 4.6)
        return {'front': front}
    add('vendor', _make('vendor', spec(coat=('C', 3.0), coat_len='long', head='scarf', scarf_head=('R', 3.2),
                                       boots='felt', H=H, hands='bare', apron=('P', 5.2)),
                        1858, L.A_MID, lights, exposure, poses, face=-1, fw=34, fh=56, extras=tray2),
        4, -38, 'a woman selling pirozhki from a tray, calling out (10 frames)')
    # the porter: quilted jacket, white apron with his brass number, a badge cap, the luggage cart
    H = 45
    po = standing(H, arms='front')
    po.update({'el_n': (5, -H + 19), 'ha_n': (9, -H + 21), 'el_f': (3, -H + 19), 'ha_f': (8, -H + 22)})
    poses = [breathe(po, k / 8.0, 0.4) for k in range(8)]

    def cart(i):
        def front(l_, P, f):
            hx, hy = P['ha_n']
            x0 = int(round(hx + f * 1))
            l_.rect(x0 - (0 if f > 0 else 16), int(round(hy)) + 6, 16, 3, 'D', 3.0)
            l_.line(int(round(hx)), int(round(hy)), x0 + f * 2, int(round(hy)) + 6, 'I', 3.0)
            for k in range(2):
                l_.rect(x0 + (2 if f > 0 else -15) + k * 7, int(round(hy)) + 1, 6, 5, ('K', 'P')[k], 2.4 + k)
            l_.ellipse(x0 + f * 10, int(round(hy)) + 11, 2, 2, 'I', 2.0)
        return {'front': front}
    add('porter', _make('porter', spec(coat=('Q', 2.4), quilted=True, coat_len='short', head='porter_cap',
                                       hat=('N', 2.2), hair=('N', 2.2), boots='felt', H=H, apron=('P', 5.0),
                                       badge=('L', 4.4), hands='mittens', mitten=('D', 3.0), trousers=('C', 1.8),
                                       width=1.1),
                        1898, L.A_MID, lights, exposure, poses, face=-1, fw=44, fh=58, extras=cart, ox_off=8),
        4, -38, 'a porter in his quilted jacket and white apron with the luggage cart (8 frames)')
    return out


def _cat(lights, exposure):
    """The depot cat curled up on the warm dry sand (tabby grey): breathing, an ear twitch, the tail tip."""
    fw, fh = 20, 12
    cx = L.SAND_HEAP[0]
    origin = (cx - 10, L.SAND_HEAP[1] - 9)
    st = PP.Strip('cat_sand', fw, fh, origin, lights, exposure)
    for j in range(8):
        lay = K.tlayer(fw, fh, 'fig')
        up = 1 if j in (2, 3) else 0                                       # breathing: the flank rises a row
        m, x0, y0 = lay.ellipse_mask(9, 7, 6, 3)
        lay.put(m, x0, y0 - up, 'C', 2.6, hgt=0.8)
        for k in range(4):                                                # tabby stripes
            lay.rect(5 + k * 3, 5 - up, 1, 3, 'N', 2.0)
        lay.rect(4, 9, 11, 1, 'C', 1.6)                                    # the belly in shadow
        lay.ellipse(15, 6, 2, 2, 'C', 3.0, hgt=0.8)                        # the head, tucked in
        ear = 0 if j != 5 else -1
        lay.px(14, 3 + ear, 'C', 3.4)
        lay.px(16, 3, 'C', 3.4)
        lay.px(15, 4, 'C', 2.4)
        lay.rect(15, 6, 2, 1, 'N', 1.0)                                    # the closed eye
        lay.px(17, 7, 'P', 4.4)                                            # the white muzzle
        tip = (2, 8) if j not in (6, 7) else (1, 6)                        # the tail curled round the front
        lay.line(3, 9, 9, 10, 'C', 2.2)
        lay.line(3, 9, tip[0], tip[1], 'C', 2.4)
        st.add(lay)
    return st
