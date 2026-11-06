"""cine_finale_karsk_anim -- animated layers of the Karsk desk close-up (owner: trans-finale).

Branch a1_choose:
  share_with_irina  a knock; the door opens (cold light wedge, the tea steam bends in the draught); Irina leans
                    in from the door, her arm reaches across and lays a folded note on the ledger; Alexei puts
                    the pencil down and covers the note with his hand.
  keep_private      he finishes the entry, closes the ledger (the right page block turns over), pulls the
                    pedestal drawer wide open, slides the book across the blotter and over the edge of the desk
                    into the drawer, pushes it shut, turns the key and pockets it.  The camera tilts down with
                    his hand and comes back up to the empty blotter.
Also: steam / smoke loops shared with Berlin, and the rhyme 'finger tap' frames for both desks.
The figures are cine_finale_figure's 3D rig (over the shoulder, camera fitted to the set).
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as bb
import cine_finale_karsk as k
import cine_finale_figure as fig
import pg

KR = kit.KR
BR = kit.BR
W, H = bb.W, bb.H
V = bb.V
LAMP = k.LAMP_K
FPS = 12.0
DUR = 8.0
P = -math.pi / 2


def A(name: str):
    return tuple(1.0 if n == name else 0.0 for n in fig.ANCHOR_NAMES)


POLE_L = (-0.26, -0.42, -0.12)
POLE_R = (0.26, -0.42, -0.12)
POLE_R_WIDE = (0.46, -0.22, -0.02)
POLE_R_DOWN = (0.14, -0.50, -0.10)          # elbow hanging by the side (hands low, in front of the body)


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
            x = origin[0] + math.sin(p * 5.0 + kk * 1.7) * spread * p * amps[kk] + draft * p * p
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
    """extra() for the rig: the pencil held between thumb, index and middle finger -- the point on the paper
    just ahead of the fingertips, the end sticking back out over the web of the thumb."""
    def fn(t, s, rgba, info):
        if not s.get(state_key) or s.get(state_key, 0) < 0.5:
            return None
        px, py = info['anchors']['pinch']
        ang = info['ang']
        tipx = px + math.cos(ang) * 5.0
        tipy = py + math.sin(ang) * 5.0 + 2.0
        back = ang + math.pi - 0.75                      # towards the thumb side and back
        endx = tipx + math.cos(back) * 24.0
        endy = tipy + math.sin(back) * 24.0
        if rgba is None:
            return (round(tipx), round(tipy), round(endx), round(endy))
        cv = kit.Canvas(W, H)
        cv.line(tipx, tipy, endx, endy, KR['brass'][4])
        cv.line(tipx + 1, tipy, endx + 1, endy, KR['brass'][2])
        cv.px(tipx, tipy, KR['metal'][2])
        cv.px(endx, endy, KR['red'][3])
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
EDGE_Y = k.FRONT_Y + 3                       # desk-top edge line: anything in the drawer above it is hidden


def _closed_quad(dx=0.0, dy=0.0):
    q = [(x + dx, y + dy) for (x, y) in k.LEDGER_L]
    return [(q[0][0] - 3, q[0][1] - 3), (q[1][0] + 3, q[1][1] - 3), (q[2][0] + 3, q[2][1] + 4), (q[3][0] - 3, q[3][1] + 4)]


def ledger_closed(dx=0, dy=0, clip_y=None, lamp=LAMP, clip_y2=None, drop=0.0, dark=0.0) -> np.ndarray:
    """Closed ledger (cover up) lying where the left page was, shifted by (dx, dy).  drop > 0: the part past
    the desk edge has fallen into the open drawer (drawn `drop` px lower and darker, `dark` adds shade)."""
    cv = kit.Canvas(W, H)
    q = _closed_quad(dx, dy)
    xx, yy = cv.grid()

    def draw(qq, shade):
        m = kit.poly_mask_full(W, H, qq)
        pool = lamp.pool(xx, yy, lift=6)
        tone = 0.12 + 0.75 * pool + 0.05 * (np.sin(xx * 0.9 + yy * 0.3) > 0.9) - shade
        cv.paint(m, np.clip(tone, 0, 1), KR['cover'])
        edge = kit.poly_mask_full(W, H, [(qq[1][0] - 2, qq[1][1] + 1), (qq[1][0], qq[1][1] + 1), (qq[2][0], qq[2][1] - 1),
                                         (qq[2][0] - 2, qq[2][1] - 1)])
        cv.paint(edge, np.clip(0.3 + 0.7 * pool - shade, 0, 1), KR['ledger'])
        # page block seen at the near edge (the book's thickness)
        nb = kit.poly_mask_full(W, H, [(qq[3][0] + 2, qq[3][1]), (qq[2][0] - 2, qq[2][1]), (qq[2][0] - 2, qq[2][1] + 3),
                                       (qq[3][0] + 2, qq[3][1] + 3)])
        cv.paint(nb, np.clip(0.25 + 0.6 * pool - shade, 0, 1), KR['ledger'])
        cv.c[kit.outline_of(nb)] = KR['cover'][1]
        lab = kit.poly_mask_full(W, H, [bb.quad_map(qq, 0.3, 0.2), bb.quad_map(qq, 0.7, 0.2), bb.quad_map(qq, 0.7, 0.42),
                                        bb.quad_map(qq, 0.3, 0.42)])
        cv.paint(lab, np.clip(0.2 + 0.8 * pool - shade, 0, 1), KR['ledger'])
        lx, ly = bb.quad_map(qq, 0.36, 0.26)
        kit.blit_mask(cv.c, kit.text_mask('1964', kit.FONT3), int(lx), int(ly), KR['cover'][2])
        cv.c[kit.outline_of(m | nb)] = KR['cover'][1]
        return m | nb
    if drop <= 0:
        m = draw(q, dark)
        sh = kit.shift(m, -5, 4) & ~m
        pool = lamp.pool(xx, yy, lift=6)
        out = np.zeros((H, W, 4), np.uint8)
        sc = kit.tone_to_ramp(np.clip(0.04 + 0.3 * pool, 0, 1), KR['desk'])
        out[sh] = sc[sh]
        out[sh, 3] = 255
        kit.over(out, cv.c)
        cv.c[:] = out
    else:
        # the whole book is drawn twice: on the desk (above the edge) and dropped into the drawer (below it)
        top = kit.Canvas(W, H)
        cv0 = cv
        cv = top
        m_top = draw(q, dark)
        img_top = top.c.copy()
        img_top[int(EDGE_Y):] = 0
        cv = kit.Canvas(W, H)
        qd = [(x, y + drop) for (x, y) in q]
        draw(qd, dark + 0.14)
        img_low = cv.c.copy()
        img_low[:int(EDGE_Y)] = 0
        # a dark seam where the cover bends over the edge
        out = np.zeros((H, W, 4), np.uint8)
        kit.over(out, img_low)
        kit.over(out, img_top)
        row = out[int(EDGE_Y)]
        sel = row[:, 3] > 0
        row[sel, :3] = np.asarray(KR['cover'][0], np.uint8)[:3]
        cv0.c[:] = out
        cv = cv0
    if clip_y is not None:
        cv.c[:int(clip_y)] = 0
    if clip_y2 is not None:
        cv.c[int(clip_y2):] = 0
    return cv.c


def ledger_turn(f: float, lamp=LAMP) -> np.ndarray:
    """The right page block turning over onto the left (f 0..1) about the spine: it rises, stands on edge
    (we see its thickness), and falls with its back cover up."""
    cv = kit.Canvas(W, H)
    L = k.LEDGER_L
    R = k.LEDGER_R
    full = kit.Canvas(W, H)
    k.ledger_pages(full, lamp)
    lm = kit.poly_mask_full(W, H, [(L[0][0] - 3, L[0][1] - 2), L[1], L[2], (L[3][0] - 3, L[3][1] + 3)])
    cv.c[lm] = full.c[lm]
    gx0, gy0 = R[0]
    gx3, gy3 = R[3]
    wid = (R[1][0] - R[0][0])
    ang = math.pi * f
    c = math.cos(ang)
    rise = math.sin(ang) * 30.0                       # the free edge lifts towards the camera / up-screen
    q = [(gx0, gy0), (gx0 + wid * c, gy0 - rise), (gx3 + wid * c, gy3 - rise * 0.9), (gx3, gy3)]
    xx, yy = cv.grid()
    pool = lamp.pool(xx, yy, lift=20)
    front = c > 0
    m = kit.poly_mask_full(W, H, q)
    if abs(c) < 0.12:
        # on edge: a narrow strip, the page block's thickness
        q = [(gx0 - 3, gy0 - rise), (gx0 + 3, gy0 - rise), (gx3 + 3, gy3 - rise * 0.9), (gx3 - 3, gy3 - rise * 0.9)]
        m = kit.poly_mask_full(W, H, q) | kit.poly_mask_full(W, H, [(gx0 - 1, gy0), (gx0 + 1, gy0), (gx3 + 1, gy3),
                                                                     (gx3 - 1, gy3)])
        cv.paint(m, np.clip(0.25 + 0.8 * pool, 0, 1), KR['ledger'])
        for yv in range(int(min(gy0, gy3) - rise), int(max(gy0, gy3)), 3):
            cv.px(gx0, yv, KR['ledger'][3])
    else:
        ramp = KR['ledger'] if front else KR['cover']
        tone = 0.14 + 0.85 * pool * (0.55 + 0.45 * abs(c))
        cv.paint(m, np.clip(tone, 0, 1), ramp)
        if front:
            for kk in range(1, 8):
                a = bb.quad_map(q, 0.05, kk / 8.0)
                b2 = bb.quad_map(q, 0.95, kk / 8.0)
                cv.line(a[0], a[1], b2[0], b2[1], KR['ledger'][3])
        # shadow of the lifted block on the left page
        sh = kit.shift(m, -6, 5) & ~m & lm
        cv.paint(sh, np.clip(0.05 + 0.4 * pool, 0, 1), KR['ledger'])
    cv.c[kit.outline_of(m)] = KR['cover'][1]
    return cv.c


DRAWER_OPEN = 76             # wide open: the ledger has to fit in


def drawer_open_at(t: float) -> int:
    if t < 2.50:
        return 0
    if t < 3.10:
        return int(round(DRAWER_OPEN * kit._ease((t - 2.50) / 0.60)))
    if t < 4.60:
        return DRAWER_OPEN
    if t < 5.10:
        return int(round(DRAWER_OPEN * (1 - kit._ease((t - 4.60) / 0.50))))
    return 0


def drawer_img(open_px: int, lamp=LAMP, part: str = 'front') -> np.ndarray:
    """Desk drawer pulled out by open_px.  part='inner': the box (bottom, sides, back wall in shadow) between
    the desk edge and the front, drawn under the ledger; part='front': the drawer front with the keyhole and
    its brass escutcheon (drawn over it)."""
    cv = kit.Canvas(W, H)
    x0, x1 = k.DRAWER_X
    fy = k.FRONT_Y + 5 + open_px
    xx, yy = cv.grid()
    if part == 'inner':
        if open_px > 0:
            inner = (xx >= x0 + 2) & (xx < x1 - 2) & (yy >= EDGE_Y) & (yy < fy)
            depth = np.clip((yy - EDGE_Y) / 18.0, 0, 1)          # the back of the box, under the desk top, is dark
            tone = 0.06 + 0.55 * lamp.pool(xx, yy - 70) * depth + 0.10 * depth
            cv.paint(inner, np.clip(tone, 0, 1), KR['desk'])
            side = inner & ((xx < x0 + 6) | (xx >= x1 - 6))
            cv.paint(side, np.clip(0.16 + 0.60 * lamp.pool(xx, yy - 70), 0, 1), KR['desk'])
            # shadow of the desk top's edge across the back of the box
            cv.paint(inner & (yy < EDGE_Y + 4), np.full((H, W), 0.03, np.float32), KR['desk'])
            # the top edges of the side walls catch the lamp
            cv.c[inner & ((xx == x0 + 2) | (xx == x1 - 3))] = KR['desk'][5]
            grain = inner & ~side & (np.sin(xx * 0.7 + np.sin(yy * 0.13) * 3.0) > 0.92)
            cv.paint(grain, np.clip(tone - 0.03, 0, 1), KR['desk'])
        return cv.c
    front = (xx >= x0) & (xx < x1) & (yy >= fy) & (yy < fy + 21)
    cv.paint(front, np.clip(0.12 + 0.55 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    cv.paint(front & (yy < fy + 2), np.clip(0.3 + 0.7 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    # panel moulding
    mould = front & (((xx == x0 + 4) | (xx == x1 - 5)) & (yy > fy + 3) & (yy < fy + 18) |
                     ((yy == fy + 4) | (yy == fy + 17)) & (xx > x0 + 4) & (xx < x1 - 5))
    cv.paint(mould, np.clip(0.05 + 0.3 * lamp.pool(xx, yy - 60), 0, 1), KR['desk'])
    cv.c[kit.outline_of(front)] = KR['desk'][1]
    kx, ky = (k.DRAWER_X[0] + k.DRAWER_X[1]) // 2, fy + 10
    cv.ellipse(kx, ky, 3, 4, KR['brass'][4])
    cv.px(kx - 1, ky - 2, KR['brass'][6])
    cv.px(kx, ky - 1, KR['void'][0])
    cv.px(kx, ky, KR['void'][0])
    cv.px(kx, ky + 1, KR['void'][0])
    return cv.c


def key_img(stage: int, open_px: int = 0) -> np.ndarray:
    cv = kit.Canvas(W, H)
    kx, ky = (k.DRAWER_X[0] + k.DRAWER_X[1]) // 2, k.FRONT_Y + 15 + open_px
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
ANCHOR_K = (360, 318)                           # Alexei's shoulder line, over-the-shoulder staging
LIGHT_K = (LAMP.sx - 40, LAMP.sy - 60)
SHADOW_K = (-5, 4, KR['desk'][1])               # hands cast down-left (the lamp is up-right)
NOTE_C = bb.quad_map(k.LEDGER_R, 0.62, 0.40)    # where Irina lays the note (right page, within her reach)
PAGE_L = dict(at=(304, 220), h=0.0, anchor=A('palm'), ang=P + 1.15, curl=0.5, thumb='side', pitch=0.0, roll=0.0,
              pole=POLE_L)
WRITE_R = dict(at=(436, 252), h=0.0, anchor=A('pinch'), ang=P - 0.55, curl=0.5, curls=(0.45, 0.62, 0.86, 0.95),
               thumb='pinch', pitch=0.0, roll=0.25, pole=POLE_R, pencil=1)


def _rig(body, Lt, Rt):
    return fig.FigureRig('alexei', body, Lt, Rt, LAMP, LIGHT_K, ANCHOR_K, shadow=SHADOW_K, max_lean=0.45)


def branch_share(out_dir: str, base_static: np.ndarray) -> list:
    nodes = []
    at_w = kit.Atlas('k_wedge')
    fr = [at_w.add(cold_wedge(base_static, f)) for f in (0.35, 0.7, 1.0)]
    w_keys = [[0.0, -1], [1.45, fr[0]], [1.6, fr[1]], [1.75, fr[2]], [5.1, fr[1]], [5.25, fr[0]], [5.4, -1]]
    nodes.append({'id': 'k_wedge', 'type': 'anim', 'atlas': 'k_close/wedge.png', 'frames': at_w.save(out_dir + '/k_close/wedge.png'),
                  'keys': w_keys, 'z': 12})
    at_n = kit.Atlas('k_note')
    nf = at_n.add(note_img(*NOTE_C))
    T_LAY = 2.95
    nodes.append({'id': 'k_note', 'type': 'anim', 'atlas': 'k_close/note.png', 'frames': at_n.save(out_dir + '/k_close/note.png'),
                  'keys': [[0.0, -1], [T_LAY, nf]], 'z': 13})
    at_p = kit.Atlas('k_pencil')
    pf = at_p.add(pencil_on_desk(*V(482, 258)))
    nodes.append({'id': 'k_pencil', 'type': 'anim', 'atlas': 'k_close/pencil_a.png', 'frames': at_p.save(out_dir + '/k_close/pencil_a.png'),
                  'keys': [[0.0, -1], [4.0, pf]], 'z': 13})
    # Alexei: left hand flat on the left page, right hand writing; the knock; covering the note
    body = kit.Track(lean=(0.0, 0.0), head=(0.0, 0.0), breathe=0.0)
    Lt = kit.Track(**PAGE_L)
    Rt = kit.Track(**WRITE_R)
    Rt.key(0.0).key(0.2, at=(440, 252)).key(0.4, at=(444, 253)).key(0.55, at=(447, 252))
    Rt.key(0.65)                                                   # the knock: freeze
    Rt.key(1.3, at=(447, 249), h=0.02)                             # pencil lifts off the paper
    Rt.key(3.7, at=(448, 249))
    Rt.key(4.0, at=V(486, 254), h=0.0, pencil=0, anchor=A('palm'), curl=0.45, curls=None, thumb='side', roll=0.0,
           ang=P - 0.9)                                            # lays the pencil down
    Rt.key(4.6, at=(NOTE_C[0] + 2, NOTE_C[1] + 3), anchor=A('palm'), curl=0.38, ang=P - 1.0)   # covers the note
    Rt.key(5.4, at=(NOTE_C[0] + 1, NOTE_C[1] + 4), curl=0.55, ang=P - 1.15)
    Rt.key(DUR, at=(NOTE_C[0] + 1, NOTE_C[1] + 4))
    Lt.key(0.0).key(1.3).key(1.6, curl=0.55).key(4.6, curl=0.55).key(5.2, curl=0.42).key(DUR)
    body.key(0.62).key(0.9, head=(5.0, -2.0), lean=(0.04, 0.0)).key(3.6, head=(6.0, -2.0))
    body.key(4.2, head=(1.0, 0.0), lean=(0.02, 0.04)).key(5.6, head=(0.0, 1.0), lean=(0.0, 0.0), breathe=1.0)
    body.key(6.8, breathe=0.0).key(7.8, breathe=1.0)
    rig = _rig(body, Lt, Rt)
    fig.rig_nodes(nodes, rig, out_dir, 'k_close', 'k', 'share', DUR, FPS, extras={'R': pencil_extra()})
    # Irina leans in from the open door (right), her arm reaches across the desk and lays the note down
    S_out = rig.cam.on_plane_y(744, 196, 0.58)
    S_in = rig.cam.on_plane_y(668, 184, 0.52)
    It = kit.Track(sh=tuple(S_out), at=(596, 228), h=0.16, anchor=A('pinch'), ang=math.pi + 0.35, curl=0.3,
                   thumb='pinch', hidden=1, carry=1, body=1, pole=(0.10, -0.42, -0.25))
    It.key(0.0).key(2.12, hidden=0)
    It.key(2.55, sh=tuple(S_in), at=(NOTE_C[0] + 18, NOTE_C[1] - 4), h=0.05)
    It.key(T_LAY - 0.05, at=(NOTE_C[0] + 9, NOTE_C[1] - 1), h=0.01)
    It.key(T_LAY, carry=0, curl=0.25, thumb='side', anchor=A('tips'))
    It.key(3.25, at=(NOTE_C[0] + 26, NOTE_C[1] - 6), h=0.06, curl=0.35)
    It.key(3.52, sh=tuple(S_out), at=(598, 224), h=0.18)
    It.key(3.55, hidden=1)

    def carry(t, s, rgba, info):
        if not s.get('carry') or s.get('carry', 0) < 0.5 or s.get('hidden'):
            return None
        px, py = info['anchors']['pinch']
        cx, cy = px - 9, py + 1
        if rgba is None:
            return (round(cx), round(cy))
        kit.over(rgba, note_img(cx, cy))
        return None
    arm = fig.StandingArm('irina', It, rig.cam, rig.light, shadow=SHADOW_K)
    at_i = kit.Atlas('k_arm_irina')
    ik = fig.standing_arm_track(arm, at_i, 0.0, DUR, FPS, extra=carry)
    nodes.append({'id': 'k_arm_irina', 'type': 'anim', 'atlas': 'k_close/arm_irina.png',
                  'frames': at_i.save(out_dir + '/k_close/arm_irina.png'), 'keys': ik, 'z': 22})
    for n in nodes:
        n['when'] = {'a1_choose': 'share_with_irina'}
    return nodes


# keep_private timing
T_TURN = (1.45, 1.95)
T_SLIDE = (3.35, 3.85)
T_OVER = (3.85, 4.45)


def ledger_pose(t: float):
    """(dx, dy, drop, dark) of the closed ledger at time t (keep branch)."""
    led_cx = (k.LEDGER_L[0][0] + k.LEDGER_L[1][0]) / 2.0
    dr_cx = (k.DRAWER_X[0] + k.DRAWER_X[1]) / 2.0
    slide = dr_cx - led_cx
    q0 = _closed_quad()
    top0 = min(q0[0][1], q0[1][1])
    # into the drawer: the far edge ends just past the desk edge, the book drops 6 px into the box
    over = (EDGE_Y + 3) - top0
    if t < T_SLIDE[0]:
        return 0.0, 0.0, 0.0, 0.0
    if t < T_SLIDE[1]:
        f = kit._ease((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))
        return slide * f, 0.0, 0.0, 0.0
    op = drawer_open_at(t)
    if t < T_OVER[1]:
        f = kit._ease((t - T_OVER[0]) / (T_OVER[1] - T_OVER[0]))
        dy = over * f
        bottom = max(q0[2][1], q0[3][1]) + dy
        drop = 6.0 * float(np.clip((bottom - EDGE_Y) / 30.0, 0, 1))
        return slide, dy, drop, 0.0
    # in the drawer, riding with it as it closes
    return slide, over - (DRAWER_OPEN - op), 6.0, 0.06


def branch_keep(out_dir: str) -> list:
    nodes = []
    at_g = kit.Atlas('k_ledger')
    open_f = at_g.add(k.ledger_layer())
    g_keys = [[0.0, open_f]]
    n_turn = 7
    turn = [at_g.add(ledger_turn((i + 1) / (n_turn + 1))) for i in range(n_turn)]
    for i in range(n_turn):
        g_keys.append([round(T_TURN[0] + (T_TURN[1] - T_TURN[0]) * i / n_turn, 3), turn[i]])
    cache = {}
    last = None
    for i in range(int(T_TURN[1] * FPS), int(DUR * FPS) + 1):
        t = max(T_TURN[1], i / FPS)
        dx, dy, drop, dark = ledger_pose(t)
        op = drawer_open_at(t)
        in_drawer = t >= T_OVER[1]
        key = (round(dx), round(dy), round(drop), in_drawer)
        if key not in cache:
            # once it is in the drawer, everything above the desk edge is under the desk top
            img = ledger_closed(round(dx), round(dy), drop=drop, dark=dark,
                                clip_y=EDGE_Y if in_drawer else None,
                                clip_y2=(k.FRONT_Y + 5 + op) if in_drawer else None)
            cache[key] = at_g.add(img) if img[..., 3].any() else -1
        f = cache[key]
        if f != last:
            g_keys.append([round(t, 3), f])
            last = f
    nodes.append({'id': 'k_ledger', 'type': 'anim', 'atlas': 'k_close/ledger_keep.png',
                  'frames': at_g.save(out_dir + '/k_close/ledger_keep.png'), 'keys': g_keys, 'z': 11, 'no_static_ledger': True})
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
    T_KEY = (5.25, 5.55, 5.70)                       # quarter turn, locked, taken
    at_k = kit.Atlas('k_key')
    kk_keys, last, cache = [], None, {}
    for i in range(int(DUR * FPS) + 1):
        t = i / FPS
        stage = 0 if t < T_KEY[0] else (1 if t < T_KEY[1] else 2)
        if t >= T_KEY[2]:
            f = -1
        else:
            op = drawer_open_at(t)
            ck = (stage, op)
            if ck not in cache:
                cache[ck] = at_k.add(key_img(stage, op))
            f = cache[ck]
        if f != last:
            kk_keys.append([round(t, 3), f])
            last = f
    nodes.append({'id': 'k_key', 'type': 'anim', 'atlas': 'k_close/key.png', 'frames': at_k.save(out_dir + '/k_close/key.png'),
                  'keys': kk_keys, 'z': 24})
    at_p = kit.Atlas('k_pencil_b')
    pf = at_p.add(pencil_on_desk(*V(486, 254)))
    nodes.append({'id': 'k_pencil', 'type': 'anim', 'atlas': 'k_close/pencil_b.png',
                  'frames': at_p.save(out_dir + '/k_close/pencil_b.png'), 'keys': [[0.0, -1], [1.25, pf]], 'z': 13})
    # Alexei over the shoulder
    kx = (k.DRAWER_X[0] + k.DRAWER_X[1]) / 2.0
    fy = k.FRONT_Y + 5
    body = kit.Track(lean=(0.0, 0.0), head=(0.0, 0.0), breathe=0.0)
    Lt = kit.Track(**PAGE_L)
    Rt = kit.Track(**WRITE_R)
    Rt.key(0.0).key(0.3, at=(441, 252)).key(0.6, at=(446, 253)).key(0.9, at=(452, 252))
    Rt.key(1.25, at=V(484, 256), pencil=0, anchor=A('palm'), curl=0.45, curls=None, thumb='side', roll=0.0,
           ang=P - 0.9)                                                                   # pencil down
    R_ = k.LEDGER_R
    edge_mid = bb.quad_map(R_, 0.97, 0.55)
    Rt.key(T_TURN[0], at=edge_mid, h=0.01, anchor=A('grip'), curl=0.72, thumb='under', ang=P - 0.5)  # page edge
    gx = R_[0][0]
    for i in range(1, 8):
        f = i / 7.0
        c = math.cos(math.pi * f)
        x = gx + (edge_mid[0] - gx) * c
        y = edge_mid[1] - math.sin(math.pi * f) * 30.0
        Rt.key(T_TURN[0] + (T_TURN[1] - T_TURN[0]) * f, at=(x, y), h=0.01 + 0.10 * math.sin(math.pi * f), ease='lin',
               ang=P - 0.5 - 0.6 * f)
    cq = _closed_quad()
    on_book = bb.quad_map(cq, 0.62, 0.62)
    Rt.key(2.15, at=on_book, h=0.03, anchor=A('palm'), curl=0.4, thumb='side', ang=P - 0.9)    # hand on the book
    Rt.key(2.35, at=(on_book[0] + 1, on_book[1] + 1))
    knob0 = (kx, fy + 9)
    Rt.key(2.50, at=knob0, h=-0.05, anchor=A('grip'), curl=0.82, thumb='wrap', ang=P - 0.2, pole=POLE_R_DOWN)
    Rt.key(3.10, at=(kx, fy + 9 + DRAWER_OPEN), ease='lin')                                     # pulls it open
    Rt.key(3.35, at=(on_book[0] + 8, on_book[1] + 6), h=0.03, anchor=A('palm'), curl=0.35, thumb='side',
           ang=P - 1.0, pole=POLE_R)                                                             # back to the book
    slide_end = ledger_pose(T_SLIDE[1])
    Rt.key(T_SLIDE[1], at=(on_book[0] + 8 + slide_end[0], on_book[1] + 6), ease='lin')         # slides it right
    over_end = ledger_pose(T_OVER[1] - 0.001)
    Rt.key(T_OVER[1], at=(on_book[0] + 8 + slide_end[0], on_book[1] + 6 + over_end[1]), h=-0.02, curl=0.62,
           ang=P - 1.2)                                                                         # over the edge
    Rt.key(4.55, at=(kx + 2, fy + DRAWER_OPEN + 2), h=-0.04, anchor=A('palm'), curl=0.3, ang=P - 0.6,
           pole=POLE_R_DOWN)                                                                    # on the drawer front
    Rt.key(5.10, at=(kx + 2, fy + 2), ease='lin')                                              # pushes it shut
    Rt.key(5.22, at=(kx + 1, fy + 3), h=-0.06, anchor=A('pinch'), curl=0.5, curls=(0.4, 0.82, 0.9, 0.95),
           thumb='pinch', ang=P - 0.9)                                                          # the key
    Rt.key(T_KEY[1], at=(kx + 3, fy + 4), roll=0.6)                                              # turns it
    Rt.key(T_KEY[2], at=(kx + 1, fy + 8), roll=0.2, curl=0.85, thumb='under', anchor=A('knuckles'))   # takes it
    Rt.key(6.30, at=(ANCHOR_K[0] + 92, ANCHOR_K[1] + 52), h=0.15, roll=0.0)                   # pockets it
    Rt.key(6.95, at=(466, 252), h=0.0, anchor=A('palm'), curl=0.64, curls=None, thumb='side', ang=P - 1.2,
           pole=POLE_R, roll=0.0)
    Rt.key(DUR, at=(467, 253))
    Lt.key(0.0).key(1.15)
    Lt.key(1.42, at=(306, 352), h=-0.26, curl=0.55, ang=P + 1.2, anchor=A('palm'))  # off the page, into his lap
    Lt.key(6.2, at=(306, 352))
    Lt.key(6.9, at=(294, 248), h=0.0, curl=0.64, ang=P + 1.3).key(DUR, at=(295, 248))
    body.key(1.4).key(1.9, lean=(-0.02, 0.06)).key(2.2, lean=(0.0, 0.02))
    body.key(2.6, lean=(0.10, 0.06), head=(3.0, 3.0)).key(3.1, lean=(0.12, 0.08), head=(4.0, 4.0))
    body.key(3.85, lean=(0.10, 0.04), head=(3.0, 2.0)).key(4.6, lean=(0.12, 0.08), head=(4.0, 4.0))
    body.key(5.6, lean=(0.10, 0.06), head=(3.0, 3.0)).key(6.3, lean=(0.04, 0.0), head=(1.0, 1.0))
    body.key(7.0, lean=(0.0, 0.0), head=(0.0, 0.0), breathe=1.0).key(7.8, breathe=0.0)
    rig = _rig(body, Lt, Rt)
    fig.rig_nodes(nodes, rig, out_dir, 'k_close', 'k', 'keep', DUR, FPS, extras={'R': pencil_extra()})
    for n in nodes:
        n['when'] = {'a1_choose': 'keep_private'}
    return nodes
