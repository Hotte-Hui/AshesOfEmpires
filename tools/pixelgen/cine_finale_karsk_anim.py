"""cine_finale_karsk_anim -- animated layers of the Karsk desk close-up (owner: trans-finale).

Branch a1_choose:
  share_with_irina  a knock; the door opens (cold light wedge, the tea steam bends in the draught); Irina's hand
                    lays a folded note on the ledger; Alexei puts the pencil down and covers it with his hand.
  keep_private      he finishes the entry, closes the ledger, opens the desk drawer, slides the book in, closes
                    it, turns the key and pockets it.
Also: steam / smoke loops shared with Berlin, and the rhyme 'finger tap' frames for both desks.
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as bb
import cine_finale_karsk as k
import pg

KR = kit.KR
BR = kit.BR
W, H = bb.W, bb.H
V = bb.V
LAMP = k.LAMP_K
FPS = 12.0
DUR = 8.0


# ------------------------------------------------------------------------------------------- wisps
def wisp_frames(atlas: kit.Atlas, origin, n: int, ramp, lamp, seed: str, height=46, spread=3.0, draft=0.0,
                count=7, rmax=4.5, density=0.75, ribbon=False) -> list:
    """Looping steam/smoke frames rising from origin.  draft bends the column sideways (px at the top,
    negative = left).  Dithered density, lit by the lamp (brighter where the pool is)."""
    rng = np.random.default_rng(kit.seed_of(seed))
    offs = rng.random(count)
    amps = rng.uniform(0.6, 1.4, count)
    frames = []
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    bay = kit.bayer_full(W, H)
    pool = lamp.pool(xx, yy, lift=30)
    for i in range(n):
        dens = np.zeros((H, W), np.float32)
        for kk in range(count):
            p = (i / n + offs[kk]) % 1.0
            y = origin[1] - p * height
            x = origin[0] + math.sin(p * 5.0 + kk * 1.7 + i * 2 * math.pi / n * 0) * spread * p * amps[kk] \
                + draft * p * p
            if ribbon:
                x += math.sin(p * 9.0 + kk) * 2.0 * p
            r = 0.8 + p * rmax
            a = density * math.sin(math.pi * min(1.0, p * 1.15)) * (1.0 - p * 0.55)
            d = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.3) ** 2) / r
            dens = np.maximum(dens, np.clip(1.0 - d, 0, 1) * a)
        m = dens > bay * 0.95 + 0.04
        tone = np.clip(0.25 + 0.9 * pool + dens * 0.25, 0, 1)
        col = kit.tone_to_ramp(tone, ramp, dither=False)
        img = np.zeros((H, W, 4), np.uint8)
        img[m] = col[m]
        img[..., 3] = np.where(m, 255, 0)
        frames.append(atlas.add(img))
    return frames


# ------------------------------------------------------------------------------------------- props
def pencil_extra(state_key='pencil'):
    """extra() callback for render_arm_track: a pencil held between thumb and index."""
    def fn(t, s, rgba):
        if not s.get(state_key):
            return None if rgba is None else None
        wx, wy = s['wrist']
        ang = s['ang']
        L = s.get('length', 60)
        tipx = wx + math.cos(ang) * L * 0.78 - math.sin(ang) * 6
        tipy = wy + math.sin(ang) * L * 0.78 * 0.66 + math.cos(ang) * 6
        endx = tipx - math.cos(ang - 0.9) * 30
        endy = tipy - math.sin(ang - 0.9) * 30 * 0.66
        if rgba is None:
            return (round(tipx), round(tipy), round(endx), round(endy))
        cv = kit.Canvas(W, H)
        cv.line(tipx, tipy, endx, endy, KR['brass'][4])
        cv.line(tipx + 1, tipy, endx + 1, endy, KR['brass'][2])
        cv.px(tipx, tipy, KR['metal'][2])
        kit.over(rgba, cv.c)
        return None
    return fn


def pencil_on_desk(x, y) -> np.ndarray:
    cv = kit.Canvas(W, H)
    cv.line(x, y, x + 30, y - 8, KR['brass'][5])
    cv.line(x, y + 1, x + 30, y - 7, KR['brass'][2])
    cv.px(x - 1, y + 1, KR['metal'][3])
    cv.line(x + 31, y - 8, x + 33, y - 9, KR['red'][3])
    return cv.c


def note_img(cx, cy, lamp=LAMP) -> np.ndarray:
    """Irina's folded note: a small sheet folded once, pencil marks on the visible half."""
    cv = kit.Canvas(W, H)
    q = [(cx - 14, cy - 9), (cx + 13, cy - 10), (cx + 14, cy + 8), (cx - 13, cy + 9)]
    bb.sheet(cv, q, KR['paper'], lamp, base=0.10, gain=0.9, shadow=False, lift=3)
    cv.line(cx - 13, cy, cx + 13, cy - 1, KR['paper'][4])
    for i in range(0, 18, 2):
        cv.px(cx - 9 + i, cy - 5 + (i % 3 == 0), KR['ink'][0] if 'ink' in KR else KR['metal'][2])
    for i in range(0, 12, 2):
        cv.px(cx - 9 + i, cy - 2, KR['metal'][3])
    return cv.c


def cold_wedge(base_rgba: np.ndarray, frac: float) -> np.ndarray:
    """Cold light from the opened door (off-frame right) falling over the right of the desk."""
    if frac <= 0:
        return np.zeros((H, W, 4), np.uint8)
    cv = kit.Canvas(W, H)
    cv.c[:] = base_rgba
    x_in = V(640, 0)[0] + 30
    spread = 230 * frac
    q = [(x_in, k.DESK_Y), (x_in - spread * 0.65, k.DESK_Y), (x_in - spread, k.FRONT_Y + 3), (x_in, k.FRONT_Y + 3)]
    m = k.cold_patch_k(cv, q, gain=1.45, lift=0.06)
    out = np.zeros((H, W, 4), np.uint8)
    out[m] = cv.c[m]
    out[..., 3] = np.where(m, 255, 0)
    return out


# ------------------------------------------------------------------------------------------- ledger states
def ledger_closed(dx=0, dy=0, clip_y=None, lamp=LAMP, clip_y2=None) -> np.ndarray:
    """Closed ledger (cover up) lying where the left page was, shifted by (dx, dy)."""
    cv = kit.Canvas(W, H)
    q = [(x + dx, y + dy) for (x, y) in k.LEDGER_L]
    q = [(q[0][0] - 3, q[0][1] - 3), (q[1][0] + 3, q[1][1] - 3), (q[2][0] + 3, q[2][1] + 4), (q[3][0] - 3, q[3][1] + 4)]
    m = kit.poly_mask_full(W, H, q)
    sh = kit.shift(m, -5, 4) & ~m
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=6)
    cv.paint(sh, np.clip(0.04 + 0.3 * pool, 0, 1), KR['desk'])
    tone = 0.12 + 0.75 * pool + 0.05 * (np.sin(xx * 0.9 + yy * 0.3) > 0.9)
    cv.paint(m, np.clip(tone, 0, 1), KR['cover'])
    # page block edge on the right and a paper label on the cover
    edge = kit.poly_mask_full(W, H, [(q[1][0] - 2, q[1][1] + 1), (q[1][0], q[1][1] + 1), (q[2][0], q[2][1] - 1), (q[2][0] - 2, q[2][1] - 1)])
    cv.paint(edge, np.clip(0.3 + 0.7 * pool, 0, 1), KR['ledger'])
    lab = kit.poly_mask_full(W, H, [bb.quad_map(q, 0.3, 0.2), bb.quad_map(q, 0.7, 0.2), bb.quad_map(q, 0.7, 0.42), bb.quad_map(q, 0.3, 0.42)])
    cv.paint(lab, np.clip(0.2 + 0.8 * pool, 0, 1), KR['ledger'])
    lx, ly = bb.quad_map(q, 0.36, 0.26)
    kit.blit_mask(cv.c, kit.text_mask('1964', kit.FONT3), int(lx), int(ly), KR['cover'][2])
    cv.c[kit.outline_of(m)] = KR['cover'][1]
    if clip_y is not None:
        cv.c[:int(clip_y)] = 0
    if clip_y2 is not None:
        cv.c[int(clip_y2):] = 0
    return cv.c


def ledger_flip(stage: int, lamp=LAMP) -> np.ndarray:
    """Right page block turning over onto the left: stage 1 lifting, 2 upright, 3 falling."""
    cv = kit.Canvas(W, H)
    L = k.LEDGER_L
    R = k.LEDGER_R
    # left page stays (with its entries) -- draw the left page via the full ledger art, masked
    full = kit.Canvas(W, H)
    k.ledger_pages(full, lamp)
    lm = kit.poly_mask_full(W, H, [(L[0][0] - 3, L[0][1] - 2), L[1], L[2], (L[3][0] - 3, L[3][1] + 3)])
    cv.c[lm] = full.c[lm]
    gx = R[0][0]
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=20)
    if stage == 1:
        q = [R[0], (R[1][0] - 26, R[1][1] - 24), (R[2][0] - 26, R[2][1] - 22), R[3]]
        ramp = KR['ledger']
    elif stage == 2:
        q = [(gx - 3, R[0][1] - 36), (gx + 3, R[0][1] - 36), (gx + 3, R[3][1] - 4), (gx - 3, R[3][1] - 4)]
        ramp = KR['cover']
    else:
        q = [(gx, R[0][1]), (L[0][0] + 26, L[0][1] - 22), (L[3][0] + 26, L[3][1] - 20), (gx, R[3][1])]
        ramp = KR['cover']
    m = kit.poly_mask_full(W, H, q)
    cv.paint(m, np.clip(0.18 + 0.85 * pool, 0, 1), ramp)
    cv.c[kit.outline_of(m)] = ramp[1]
    return cv.c


def drawer_img(open_px: int, lamp=LAMP, part: str = 'front') -> np.ndarray:
    """Desk drawer pulled out by open_px.  part='inner': the box interior between the desk edge and the
    front (drawn under the ledger); part='front': the drawer front with the keyhole (drawn over it)."""
    cv = kit.Canvas(W, H)
    x0, x1 = V(250, 0)[0], V(450, 0)[0]
    fy = k.FRONT_Y + 5 + open_px
    xx, yy = cv.grid()
    if part == 'inner':
        if open_px > 0:
            inner = (xx >= x0 + 2) & (xx < x1 - 2) & (yy >= k.FRONT_Y + 3) & (yy < fy)
            cv.paint(inner, np.clip(0.02 + 0.25 * lamp.pool(xx, yy - 40), 0, 1), KR['desk'])
            side = inner & ((xx < x0 + 4) | (xx >= x1 - 4))
            cv.paint(side, np.clip(0.10 + 0.4 * lamp.pool(xx, yy - 40), 0, 1), KR['desk'])
        return cv.c
    front = (xx >= x0) & (xx < x1) & (yy >= fy) & (yy < fy + 21)
    cv.paint(front, np.clip(0.12 + 0.55 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    cv.paint(front & (yy < fy + 2), np.clip(0.3 + 0.7 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    cv.c[kit.outline_of(front)] = KR['desk'][1]
    kx, ky = V(350, 0)[0], fy + 10
    cv.ellipse(kx, ky, 3, 4, KR['brass'][4])
    cv.px(kx, ky - 1, KR['void'][0])
    cv.px(kx, ky, KR['void'][0])
    cv.px(kx, ky + 1, KR['void'][0])
    return cv.c


def key_img(stage: int, open_px: int = 0) -> np.ndarray:
    cv = kit.Canvas(W, H)
    kx, ky = V(350, 0)[0], k.FRONT_Y + 15 + open_px
    if stage == 0:            # key upright in the lock
        cv.line(kx, ky - 1, kx, ky - 6, KR['brass'][6])
        cv.ellipse(kx, ky - 8, 2.5, 2.5, KR['brass'][5])
        cv.px(kx, ky - 8, KR['void'][0])
    elif stage == 1:          # quarter turn
        cv.line(kx, ky - 1, kx + 4, ky - 5, KR['brass'][6])
        cv.ellipse(kx + 6, ky - 7, 2.5, 2.5, KR['brass'][5])
    else:                     # turned (locked)
        cv.line(kx, ky, kx + 6, ky, KR['brass'][6])
        cv.ellipse(kx + 8, ky, 2.5, 2.5, KR['brass'][5])
        cv.px(kx + 8, ky, KR['void'][0])
    return cv.c


# ------------------------------------------------------------------------------------------- branches
ARM_KW = dict(sleeve_ramp=KR['quilt'], skin_ramp=KR['skin'], quilt=True, cuff_style='knit', sleeve_w=(34, 46))
IRINA_KW = dict(sleeve_ramp=KR['irina'], skin_ramp=KR['skin'], quilt=True, cuff_style='knit', sleeve_w=(30, 40),
                hand_scale_w=0.92)


def branch_share(out_dir: str, base_static: np.ndarray) -> list:
    nodes = []
    # cold wedge of the opened door
    at_w = kit.Atlas('k_wedge')
    fr = [at_w.add(cold_wedge(base_static, f)) for f in (0.35, 0.7, 1.0)]
    w_keys = [[0.0, -1], [1.45, fr[0]], [1.6, fr[1]], [1.75, fr[2]], [5.1, fr[1]], [5.25, fr[0]], [5.4, -1]]
    nodes.append({'id': 'k_wedge', 'type': 'anim', 'atlas': 'k_close/wedge.png', 'frames': at_w.save(out_dir + '/k_close/wedge.png'),
                  'keys': w_keys, 'z': 12})
    # note left on the ledger
    note_c = bb.quad_map(k.LEDGER_R, 0.42, 0.40)
    at_n = kit.Atlas('k_note')
    nf = at_n.add(note_img(*note_c))
    nodes.append({'id': 'k_note', 'type': 'anim', 'atlas': 'k_close/note.png', 'frames': at_n.save(out_dir + '/k_close/note.png'),
                  'keys': [[0.0, -1], [2.95, nf]], 'z': 13})
    at_p = kit.Atlas('k_pencil')
    pf = at_p.add(pencil_on_desk(*V(482, 258)))
    nodes.append({'id': 'k_pencil', 'type': 'anim', 'atlas': 'k_close/pencil_a.png', 'frames': at_p.save(out_dir + '/k_close/pencil_a.png'),
                  'keys': [[0.0, -1], [4.0, pf]], 'z': 13})
    # Alexei: left hand flat on the left page, right hand writing, then covering the note
    Lt = kit.Track(wrist=V(300, 270), ang=-math.pi / 2 + 0.35, length=60, curl=0.08, thumb='side', entry=V(200, 440))
    Rt = kit.Track(wrist=V(404, 262), ang=-math.pi / 2 + 0.15, length=60, curl=0.4, thumb='pinch', entry=V(330, 446),
                   pencil=1)
    Rt.key(0.0).key(0.2, wrist=V(408, 262)).key(0.4, wrist=V(412, 263)).key(0.55, wrist=V(414, 262))
    Rt.key(0.65)                                                   # the knock: freeze
    Rt.key(1.3, wrist=V(414, 258), curl=0.3)
    Rt.key(3.7, wrist=V(414, 258))
    Rt.key(4.0, wrist=V(474, 270), pencil=0, curl=0.2, thumb='side')   # lays the pencil down
    Rt.key(4.6, wrist=(note_c[0] - 4, note_c[1] + 42), ang=-math.pi / 2 + 0.05, curl=0.05)   # covers the note
    Rt.key(DUR, wrist=(note_c[0] - 4, note_c[1] + 42))
    Lt.key(0.0).key(1.3).key(1.6, curl=0.25).key(4.6, curl=0.25).key(5.2, curl=0.08).key(DUR)
    at_l = kit.Atlas('k_arm_l_share')
    at_r = kit.Atlas('k_arm_r_share')
    lk = kit.render_arm_track(Lt, 'L', at_l, W, H, LAMP, 0.0, DUR, FPS, seed=31, **ARM_KW)
    rk = kit.render_arm_track(Rt, 'R', at_r, W, H, LAMP, 0.0, DUR, FPS, seed=32, extra=pencil_extra(), **ARM_KW)
    nodes.append({'id': 'k_arm_l', 'type': 'anim', 'atlas': 'k_close/arm_l_share.png',
                  'frames': at_l.save(out_dir + '/k_close/arm_l_share.png'), 'keys': lk, 'z': 20,
                  '_atlas': at_l, '_path': out_dir + '/k_close/arm_l_share.png'})
    nodes.append({'id': 'k_arm_r', 'type': 'anim', 'atlas': 'k_close/arm_r_share.png',
                  'frames': at_r.save(out_dir + '/k_close/arm_r_share.png'), 'keys': rk, 'z': 21,
                  '_atlas': at_r, '_path': out_dir + '/k_close/arm_r_share.png'})
    # Irina's arm from the right edge, carrying the note
    It = kit.Track(wrist=V(760, 236), ang=math.pi + 0.15, length=56, curl=0.2, thumb='pinch', entry=V(860, 250),
                   hidden=1, carry=1)
    It.key(0.0).key(1.95, hidden=0)
    It.key(2.75, wrist=(note_c[0] + 52, note_c[1] + 6), ang=math.pi + 0.1)
    It.key(2.95, carry=0, curl=0.05, thumb='side')
    It.key(3.7, wrist=V(760, 236), ang=math.pi + 0.2)
    It.key(3.75, hidden=1)

    def carry(t, s, rgba):
        if not s.get('carry') or s.get('hidden'):
            return None
        wx, wy = s['wrist']
        cx = wx - 44
        cy = wy - 4
        if rgba is None:
            return (round(cx), round(cy))
        kit.over(rgba, note_img(cx, cy))
        return None
    at_i = kit.Atlas('k_arm_irina')
    ik = kit.render_arm_track(It, 'R', at_i, W, H, LAMP, 0.0, DUR, FPS, seed=33, extra=carry, **IRINA_KW)
    nodes.append({'id': 'k_arm_irina', 'type': 'anim', 'atlas': 'k_close/arm_irina.png',
                  'frames': at_i.save(out_dir + '/k_close/arm_irina.png'), 'keys': ik, 'z': 22})
    for n in nodes:
        n['when'] = {'a1_choose': 'share_with_irina'}
    return nodes


def branch_keep(out_dir: str) -> list:
    nodes = []
    # ledger: open (static layer) -> flip -> closed -> into the drawer
    at_g = kit.Atlas('k_ledger')
    open_f = at_g.add(k.ledger_layer())
    flips = [at_g.add(ledger_flip(s_)) for s_ in (1, 2, 3)]
    g_keys = [[0.0, open_f], [1.45, flips[0]], [1.65, flips[1]], [1.85, flips[2]]]
    LT = kit.Track(d=(0.0, 0.0))
    LT.key(2.05, d=(0.0, 0.0)).key(3.0, d=(0.0, 0.0)).key(3.9, d=(8.0, 37.0))
    cache = {}
    last = flips[2]
    for i in range(int(2.05 * FPS), int(DUR * FPS) + 1):
        t = i / FPS
        dx, dy = LT.at(t)['d']
        op = drawer_open_at(t)
        in_drawer = t >= 3.9
        dyy = dy - (22 - op) if in_drawer else dy
        key = (round(dx), round(dyy), in_drawer, op)
        if key not in cache:
            if in_drawer and op <= 0:
                cache[key] = -1
            else:
                cache[key] = at_g.add(ledger_closed(round(dx), round(dyy),
                                                    clip_y=(k.FRONT_Y + 3) if in_drawer else None,
                                                    clip_y2=(k.FRONT_Y + 5 + op) if in_drawer else None))
        f = cache[key]
        if f != last:
            g_keys.append([round(t, 3), f])
            last = f
    nodes.append({'id': 'k_ledger', 'type': 'anim', 'atlas': 'k_close/ledger_keep.png',
                  'frames': at_g.save(out_dir + '/k_close/ledger_keep.png'), 'keys': g_keys, 'z': 11, 'no_static_ledger': True})
    # drawer: interior under the ledger, front over it
    for part, z in (('inner', 10), ('front', 12)):
        at_d = kit.Atlas('k_drawer_' + part)
        d_keys = []
        cache = {}
        last = None
        for i in range(int(DUR * FPS) + 1):
            t = i / FPS
            op = drawer_open_at(t)
            if op not in cache:
                cache[op] = at_d.add(drawer_img(op, part=part))
            if cache[op] != last:
                d_keys.append([round(t, 3), cache[op]])
                last = cache[op]
        nodes.append({'id': 'k_drawer_' + part, 'type': 'anim', 'atlas': 'k_close/drawer_%s.png' % part,
                      'frames': at_d.save(out_dir + '/k_close/drawer_%s.png' % part), 'keys': d_keys, 'z': z})
    # key in the lock
    at_k = kit.Atlas('k_key')
    kf = [at_k.add(key_img(s_)) for s_ in (0, 1, 2)]
    nodes.append({'id': 'k_key', 'type': 'anim', 'atlas': 'k_close/key.png', 'frames': at_k.save(out_dir + '/k_close/key.png'),
                  'keys': [[0.0, kf[0]], [3.0, -1], [4.75, kf[0]], [5.0, kf[1]], [5.2, kf[2]], [5.55, -1]], 'z': 24})
    at_p = kit.Atlas('k_pencil_b')
    pf = at_p.add(pencil_on_desk(*V(486, 254)))
    nodes.append({'id': 'k_pencil', 'type': 'anim', 'atlas': 'k_close/pencil_b.png',
                  'frames': at_p.save(out_dir + '/k_close/pencil_b.png'), 'keys': [[0.0, -1], [1.25, pf]], 'z': 13})
    # arms
    lc = bb.quad_map(k.LEDGER_L, 0.5, 0.5)
    Lt = kit.Track(wrist=V(300, 270), ang=-math.pi / 2 + 0.35, length=60, curl=0.08, thumb='side', entry=V(200, 440))
    Rt = kit.Track(wrist=V(404, 262), ang=-math.pi / 2 + 0.15, length=60, curl=0.4, thumb='pinch', entry=V(330, 446),
                   pencil=1)
    Rt.key(0.0).key(0.3, wrist=V(410, 262)).key(0.6, wrist=V(416, 263)).key(0.9, wrist=V(420, 262))
    Rt.key(1.25, wrist=V(478, 268), pencil=0, curl=0.15, thumb='side')
    Rt.key(1.45, wrist=V(452, 252), ang=-math.pi / 2 - 0.4, curl=0.3, thumb='under')        # grips the page edge
    Rt.key(1.85, wrist=V(330, 250), ang=-math.pi / 2 + 0.2, curl=0.1, thumb='side')
    Rt.key(2.1, wrist=(lc[0] + 30, lc[1] + 40), curl=0.05)
    Rt.key(3.0, wrist=(lc[0] + 30, lc[1] + 40))
    Rt.key(3.9, wrist=(lc[0] + 38, lc[1] + 78))                                         # pushes it into the drawer
    Rt.key(4.6, wrist=V(360, 330), ang=-math.pi / 2, curl=0.4, thumb='pinch')
    Rt.key(4.75, wrist=V(354, 334))
    Rt.key(5.2, wrist=V(356, 334), ang=-math.pi / 2 + 0.5)                               # turns the key
    Rt.key(5.55, wrist=V(352, 342), curl=0.85, thumb='under')
    Rt.key(6.3, wrist=V(250, 420), entry=V(200, 470))                                     # pockets it
    Rt.key(6.35, hidden=1)
    Lt.key(0.0).key(1.0)
    Lt.key(1.4, wrist=V(296, 262), curl=0.2)
    Lt.key(2.1, wrist=(lc[0] - 26, lc[1] + 42), curl=0.05, ang=-math.pi / 2 + 0.3)
    Lt.key(2.4, wrist=V(300, 340), curl=0.5, thumb='under')                              # pulls the drawer
    Lt.key(3.0, wrist=V(300, 362))
    Lt.key(3.2, wrist=(lc[0] - 30, lc[1] + 40), curl=0.05, thumb='side')
    Lt.key(3.9, wrist=(lc[0] - 22, lc[1] + 78))
    Lt.key(4.2, wrist=V(300, 362), curl=0.4, thumb='under')
    Lt.key(4.6, wrist=V(300, 340))                                                        # pushes it shut
    Lt.key(5.4, wrist=V(330, 270), curl=0.05, thumb='side')
    Lt.key(DUR, wrist=V(332, 268))
    at_l = kit.Atlas('k_arm_l_keep')
    at_r = kit.Atlas('k_arm_r_keep')
    lk = kit.render_arm_track(Lt, 'L', at_l, W, H, LAMP, 0.0, DUR, FPS, seed=41, **ARM_KW)
    rk = kit.render_arm_track(Rt, 'R', at_r, W, H, LAMP, 0.0, DUR, FPS, seed=42, extra=pencil_extra(), **ARM_KW)
    nodes.append({'id': 'k_arm_l', 'type': 'anim', 'atlas': 'k_close/arm_l_keep.png',
                  'frames': at_l.save(out_dir + '/k_close/arm_l_keep.png'), 'keys': lk, 'z': 20,
                  '_atlas': at_l, '_path': out_dir + '/k_close/arm_l_keep.png'})
    nodes.append({'id': 'k_arm_r', 'type': 'anim', 'atlas': 'k_close/arm_r_keep.png',
                  'frames': at_r.save(out_dir + '/k_close/arm_r_keep.png'), 'keys': rk, 'z': 21,
                  '_atlas': at_r, '_path': out_dir + '/k_close/arm_r_keep.png'})
    for n in nodes:
        n['when'] = {'a1_choose': 'keep_private'}
    return nodes


def drawer_open_at(t: float) -> int:
    if t < 2.4:
        return 0
    if t < 3.0:
        return int(round(22 * kit._ease((t - 2.4) / 0.6)))
    if t < 4.2:
        return 22
    if t < 4.6:
        return int(round(22 * (1 - kit._ease((t - 4.2) / 0.4))))
    return 0
