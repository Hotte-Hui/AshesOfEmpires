"""env_c3p2_cine_hero -- the close shots of Konrad and Alexei in the Chapter-3 part-2 cinematics, each built as ONE
3D scene on the full-body rig of env_c3p2_cine_body (owner: figures stream, round 10).

A shot whose runtime draws an arm / a hand as a separate sprite (UNDER the body sprite) renders that arm from the
very same scene, so it leaves the body exactly at the shoulder, with the body's light and occlusion:

  h1  bench_body(who, breath)        LS_C3_Halves: the two men on the quay bench from behind and above, forearms in
      bench_arm(who, mode)           their laps; the inner arm reaching for the near / far pages or holding them
Everything is deterministic numpy; renders are memoised on disk (key = pipeline sources + call).
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_anat as A   # noqa: E402
import env_c3p2_cine_body as B       # noqa: E402

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]


def _n(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


class Cam:
    """Orthographic shot camera: scene point q -> view px origin + scale * R q."""

    def __init__(self, yaw, elev, scale, origin):
        self.yaw, self.elev, self.s = yaw, elev, scale
        self.R = B.camera(yaw, elev)
        self.o = B._o3(origin)

    def px(self, q):
        return self.o + self.s * (self.R @ np.asarray(q, float))

    def on_plane(self, x, y, plane_y):
        """Scene point on the horizontal plane y = plane_y that appears at view pixel (x, y)."""
        r = self.R.T
        a = r[1, 0] * (x - self.o[0]) + r[1, 1] * (y - self.o[1])
        z = self.o[2] + (plane_y * self.s - a) / r[1, 2]
        return r @ (np.array([x, y, z]) - self.o) / self.s

    def shifted(self, x0, y0):
        """Origin for a sprite whose top-left corner sits at frame pixel (x0, y0)."""
        return (self.o[0] - x0, self.o[1] - y0)


def mask_mats(rgba, d, names, keep):
    out = rgba.copy()
    ids = [i for i, n in enumerate(names) if n in keep]
    m = np.isin(d.mat, ids) & d.hit
    out[~m] = 0
    return out


def cached(tag, key, fn):
    import tempfile
    h = hashlib.sha1((B._src_key() + _SRC + repr((tag, key))).encode('utf-8')).hexdigest()[:20]
    d = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
    os.makedirs(d, exist_ok=True)
    pth = os.path.join(d, 'hero_' + tag + '_' + h + '.npz')
    if os.environ.get('ASHES_NO_CACHE') != '1' and os.path.exists(pth):
        return np.load(pth)['rgba']
    out = fn()
    if os.environ.get('ASHES_NO_CACHE') != '1':
        np.savez(pth, rgba=out)
    return out


DEPTH = (230.0, -230.0, 170)      # tracing volume of the close shots (view z near / far, march steps)


def render_scene(figs, cam, x0, y0, size, look, light, keep=None, ss=3, glow=None, extra=None, eyes=False,
                 clip=None, styles_over=None, outline=True, post=None, rim=True):
    """figs = [(character dict, pose dict, suffix dict or None[, hide tuple])] -> RGBA sprite (top-left at frame
    px x0, y0).  keep = material names to keep (None = all); clip(Q) = signed scene-space function, > 0 is cut
    away; styles_over = {material: MatStyle} on top of the light's styles; post(rgba, d, names) -> rgba."""
    M = A.Mats()
    nodes, rigs = [], []
    for fg in figs:
        ch, pose, suffix = fg[0], fg[1], fg[2]
        hide = fg[3] if len(fg) > 3 else ()
        rig = B.Rig(pose)
        rigs.append(rig)
        nd = B.build(M, ch, rig, suffix=suffix, hide=hide)
        if clip is not None:
            nd = B.S.Inter(nd, B.S.Fn(clip, 0))
        nodes.append(nd)
    origin = cam.shifted(x0, y0)
    root = B.S.Union([B.place(n, origin, cam.R, cam.s) for n in nodes], k=0.5)
    if extra is not None:
        root = B.S.Union([root, extra(M, origin)], k=0.5)
    st = {}
    for fg in reversed(figs):
        st.update(B.styles(fg[0]['id'], light))
    if styles_over:
        st.update(styles_over)
    rig0 = rigs[0]
    frames = {'tf': B.view_frame(rig0.o_ch, rig0.R_ch, origin, cam.R, cam.s),
              'hf': B.view_frame(rig0.o_head, rig0.R_head, origin, cam.R, cam.s)}
    tps = []
    for fg in figs:
        for tp in B.figure_passes(fg[0]):
            tps.append(tp)
    out, d = B.trace_paint(root, M, size, look, st, frames=frames, tone_passes=tps, ss=ss, glow=glow,
                           outline=outline, rim=rim, depth=DEPTH)
    if eyes:
        out = B.face_marks(out, d, [(r.o_head, r.R_head, figs[i][0].get('head_scale', B.HEAD_SCALE), r.atlas)
                                    for i, r in enumerate(rigs)], cam.s, cam.R, origin)
    if post is not None:
        out = post(out, d, M.names)
    if keep is not None:
        out = mask_mats(out, d, M.names, keep)
    return out, d, M.names


def render_arm(ch, arm, cam, x0, y0, size, look, light, extra=None, ss=3, styles_over=None):
    """One arm ALONE (sleeve, cuff, wrist, hand; extra(M) -> scene node for what the hand holds) through the shot
    camera: the runtimes draw it UNDER the body sprite, which covers its root at the shoulder.  Rendered without
    the body, so the sprite may be shifted a few px (following a pencil line, a sliding stack) without opening a
    gap at the shoulder."""
    M = A.Mats()
    node = B.arm_node(M, ch, arm)
    if extra is not None:
        node = B.S.Union([node, extra(M)], k=0.4)
    origin = cam.shifted(x0, y0)
    root = B.place(node, origin, cam.R, cam.s)
    st = B.styles(ch['id'], light)
    if styles_over:
        st.update(styles_over)
    # the knit / quilt passes read the sleeve in a frame along the forearm (ribs run along the arm)
    fd = _n(arm['wr'] - arm['el'])
    side = _n(np.cross(fd, np.array([0.0, -1.0, 0.0])) + np.array([1e-3, 0.0, 0.0]))
    up = np.cross(side, fd)
    Rf = np.stack([side, fd, up], axis=1)
    tf = B.view_frame(arm['sh'] - fd * 200.0, Rf, origin, cam.R, cam.s)
    tps = [tp for tp in B.figure_passes(ch, frames_ok=True)]
    out, d = B.trace_paint(root, M, size, look, st, frames={'tf': tf, 'hf': tf}, tone_passes=tps, ss=ss,
                           depth=DEPTH)
    return out


# =============================================================================================== h1 quay bench
# The granite bench: seat surface y = -100 (the ground y = 0); Alexei at scene +x (image left: we look at their
# backs), Konrad at -x.  The runtime (ch3_halves.gd) draws stacks -> arms -> bodies, puts the breath at
# fig + (80, 30) / (66, 28) and slides a taken stack to the lap points (236, 262) / (404, 262).
BENCH_SEAT_Y = -100.0
BENCH_CAM = dict(yaw=180.0, elev=22.0, scale=0.72, origin=(320.0, 334.0))
BENCH_X = {'a': 150.0, 'k': -150.0}
# sprite rects chosen so that the runtime's breath (fig + (80, 30) / (66, 28)) rises beside each face
BENCH_AT = {'a': (156, 98), 'k': (338, 96)}
BENCH_WH = {'a': (106, 182), 'k': (136, 184)}
# ARMS_AT / ARMS_WH: the h1 arm sheet's rect -- see the arm sheet section below
STACK_RU = (276, 262)
STACK_DE = (364, 262)


def bench_cam():
    return Cam(**BENCH_CAM)


def bench_pose(who, mode='rest', target=None, breath=0, lean=0.0):
    """Seated on the bench; the inner arm (Alexei's right, Konrad's left) rests in the lap / reaches near or far
    (target = scene point of the pages) / holds the pages at the hip.  lean 0..1: he leans over toward the middle
    of the bench (round 11: the far stack is out of an arm's reach from upright)."""
    sgn = 1.0 if who == 'a' else -1.0
    inner = 'arm_r' if who == 'a' else 'arm_l'
    outer = 'arm_l' if who == 'a' else 'arm_r'
    root = (BENCH_X[who], BENCH_SEAT_Y - 24.0, 0.0)
    fwd = 9.0 - 1.2 * breath + BENCH_LEAN[1] * lean
    pose = dict(root=root, pelvis=(-sgn * 6.0, -8.0, 0.0),
                spine=(-sgn * 5.0 + sgn * BENCH_LEAN[0] * lean, fwd, -sgn * (3.0 + BENCH_LEAN[2] * lean)),
                head=(-sgn * (14.0 if who == 'a' else 9.0), -4.0, 0.0),
                leg_l=dict(fk=(86.0, 9.0, 88.0, -4.0)), leg_r=dict(fk=(86.0, 9.0, 88.0, -4.0)))
    tmp = B.Rig(pose)

    def lap(x, z, y=-22.0):
        return tmp.pelvis((x, y, z))
    pose[outer] = dict(wrist=lap(sgn * 10.0, 50.0), pole=tmp.R_ch @ np.array([sgn * 0.6, 0.5, -1.0]),
                       hand=dict(curl=0.55, spread=0.1, grip=0.2, dir=tmp.R_pel @ np.array([-sgn * 0.7, 0.3, 0.65]),
                                 up=tmp.R_pel @ np.array([0.0, -1.0, 0.0])))
    if mode == 'rest':
        pose[inner] = dict(wrist=lap(-sgn * 2.0, 44.0), pole=tmp.R_ch @ np.array([-sgn * 0.6, 0.5, -1.0]),
                           hand=dict(curl=0.6, spread=0.1, grip=0.2, dir=tmp.R_pel @ np.array([sgn * 0.7, 0.3, 0.65]),
                                     up=tmp.R_pel @ np.array([0.0, -1.0, 0.0])))
    elif mode in ('near', 'far'):
        t = np.asarray(target, float)
        sh = tmp.chest((-sgn * 39.0, 20.0, -3.0))
        dirt = _n(t - sh)
        pull = dirt * (13.0 if mode == 'far' else 5.0) + np.array([0.0, 5.0 if mode == 'far' else 1.0, 0.0])
        wrist = t + np.array([sgn * 7.0, -8.0, -5.0])
        flat = _n(np.array([dirt[0], 0.0, dirt[2]]))
        pose[inner] = dict(wrist=wrist, sh_off=pull, pole=np.array([sgn * 0.3, -0.85, -0.6]),
                           hand=dict(curl=0.25 if mode == 'near' else 0.14, spread=0.5, grip=0.0,
                                     dir=_n(flat * 0.8 + np.array([0.0, 0.6, 0.0])),
                                     up=np.array([0.0, -1.0, 0.1]), thumb=1.0 if who == 'a' else -1.0))
    elif who == 'k':
        # Konrad holds what he took at his left side, just outside his coat: the runtime folds the list there
        # (hide_for_elena) or slides the pages under his hip -- his hand is visible beside the body
        t = bench_cam().on_plane(HOLD_K[0], HOLD_K[1], BENCH_SEAT_Y - 34.0)
        pose[inner] = dict(wrist=t + np.array([-4.0, 4.0, -6.0]), pole=tmp.R_ch @ np.array([0.9, 0.3, -0.8]),
                           hand=dict(curl=0.62, spread=0.15, grip=0.55, dir=_n(np.array([0.35, 0.55, 0.75])),
                                     up=_n(np.array([0.85, -0.3, -0.3])), thumb=-1.0))
    else:
        pose[inner] = dict(wrist=lap(-sgn * 26.0, 20.0, -16.0), pole=tmp.R_ch @ np.array([-sgn * 0.9, 0.2, -0.9]),
                           hand=dict(curl=0.5, spread=0.2, grip=0.3, dir=tmp.R_pel @ np.array([sgn * 0.2, 0.25, 1.0]),
                                     up=tmp.R_pel @ np.array([-sgn * 0.9, -0.5, 0.0])))
    return pose


HOLD_K = (381.0, 239.0)        # where Konrad's hand holds the taken pages / the folding list (frame px)
BENCH_LEAN = (16.0, 14.0, 23.0)  # spine yaw, pitch, roll toward the middle of the bench at lean 1


def bench_look():
    # the burning wing upstream at the left, beyond the men: it rims their left sides; sky + snow = cold fill
    return dict(key=(-0.80, -0.20, -0.56), rim=(0.62, -0.45, -0.64), ambient=0.10, wrap=0.22, bg='berlin',
                glow=(0.8, 0.2), fill=0.17, fill_dir=(0.40, -0.80, 0.45), ao=0.5)


def _stacks():
    """The pages' seat positions as the place generator lays them out (fallback: the round-8 values)."""
    try:
        import env_c3p2_cine_quay as QY
        return tuple(QY.STACK_RU), tuple(QY.STACK_DE)
    except Exception:
        return STACK_RU, STACK_DE


def bench_target(who, mode):
    cam = bench_cam()
    ru, de = _stacks()
    near = ru if who == 'a' else de
    far = de if who == 'a' else ru
    x, y = near if mode == 'near' else far
    if mode == 'far':
        x = x + (-11 if who == 'a' else 11)
    return cam.on_plane(x, y - 5, BENCH_SEAT_Y - 4.0)


def _bench(who, mode, breath, arm_only, lean=0.0):
    ch = dict(B.ALEXEI if who == 'a' else B.KONRAD)
    inner = 'arm_r' if who == 'a' else 'arm_l'
    tgt = bench_target(who, mode) if mode in ('near', 'far') else None
    pose = bench_pose(who, mode, tgt, breath, lean=lean)
    cam = bench_cam()
    if arm_only:
        x0, y0 = ARMS_AT
        size = ARMS_WH
        keep = [ch['coat_mat'] + '__x', 'skin__x', (ch.get('cuff') or 'shirt') + '__x']
        out, _d, _n2 = render_scene([(ch, pose, {inner: '__x'})], cam, x0, y0, size, bench_look(), 'fire',
                                    keep=keep, clip=_seat_clip)
    else:
        x0, y0 = BENCH_AT[who]
        out, _d, _n2 = render_scene([(ch, pose, None)], cam, x0, y0, BENCH_WH[who], bench_look(), 'fire',
                                    clip=_seat_clip)
    # the burning wing upstream at the left: its glow eats into the left outlines (hat, shoulder, sleeve)
    import env_c3p2_cine_people as PP
    return PP.back_rim(out, BENCH_RIM, width=2, top=0.45, left=1.0, right=0.0, seed=0, fall_off=False)


BENCH_RIM = ['#2A140E', '#4A2214', '#7A3A1C', '#A85A28', '#C87A36']


def _seat_clip(Q):
    # nothing below the seat surface shows: the granite slab, its blocks and the men themselves hide the shins
    # and boots (the coat may hang over the near edge, z < -30)
    below = Q[:, 1] - (BENCH_SEAT_Y + 3.0)
    return np.where(Q[:, 2] < -30.0, Q[:, 1] - (BENCH_SEAT_Y + 34.0), below)


def bench_body(who, breath=0, lean=0.0):
    """h1 body: breath 0 / 1 upright, or leaning toward the middle of the bench (lean 0.5 / 1, the far reach)."""
    return cached('bench11', (who, breath, lean), lambda: _bench(who, 'rest', breath, False, lean))


BENCH_FRAMES = [(0, 0.0), (1, 0.0), (0, 0.5), (0, 1.0)]   # the body sheet: breath, breath, half lean, full lean


def bench_arm(who, mode):
    """Legacy single frame (near / far / hold) -- kept for callers of the round-9 API; the runtime uses
    arms_sheet()."""
    key = {'near': 'near_r3', 'far': 'far_r3', 'hold': 'hold'}.get(mode, mode)
    return bench_arm_frame(who, key)


# ---------------------------------------------------------------------------------------------- h1 arm sheet
# Round 11: the take is a motion, not a paper doll.  One row per man (0 Alexei, 1 Konrad), ARM_COLS columns:
#   0-2 near reach: lifting out of the lap / hand open over the pages / hand closed on the pages
#   3-5 far reach (across to the other man's stack): the same three
#   6-7 near pull: the hand on the pages one and two thirds of the way to the lap point (the runtime slides the
#       stack there and shifts the sprite by the rest of the way, so hand and pages move together)
#   8-9 far pull
#   10  hold: the pages under his thigh, the hand on them (mostly behind the body)
#   11-13 Konrad, hide_for_elena: the list in his left hand beside his hip -- flat, folded once, folded twice
#       (the runtime draws the list_fold frames at LIST_FOLD_AT, which the hand holds by its right edge)
ARM_COLS = 14
ARM_COL = {'near_r1': 0, 'near_r2': 1, 'near_r3': 2, 'far_r1': 3, 'far_r2': 4, 'far_r3': 5,
           'near_p1': 6, 'near_p2': 7, 'far_p1': 8, 'far_p2': 9, 'hold': 10, 'list0': 11, 'list1': 12, 'list2': 13}
ARMS_AT = (196, 140)
ARMS_WH = (248, 132)
LAP = {'a': (236.0, 262.0), 'k': (404.0, 262.0)}      # ch3_halves.gd LAP: where a taken stack slides to
LIST_FOLD_AT = (350.0, 240.0)                          # bottom centre of the list_fold frames (ch3_halves.gd)
LIST_HAND = (368.0, 230.0)                             # Konrad's fingers on the list's right edge (frame px)
STACK_TOP = 251.0                                      # the pages' top surface (frame px row) at their seat


def _stack_seat(who, mode):
    ru, de = _stacks()
    near = ru if who == 'a' else de
    far = de if who == 'a' else ru
    return np.asarray(near if mode == 'near' else far, float)


def _grip_px(who, mode, u=0.0):
    """The point of the pages the hand closes on (frame px), u = how far the stack has slid toward the lap."""
    seat = _stack_seat(who, mode)
    side = -1.0 if who == 'a' else 1.0                 # the edge nearest to him
    g = np.array([seat[0] + side * (7.0 if mode == 'near' else 15.0), STACK_TOP])
    lap = np.asarray(LAP[who], float)
    return g + (lap - seat) * u


ARM_LEAN = {'far_r1': 0.5, 'far_r2': 1.0, 'far_r3': 1.0, 'far_p1': 1.0, 'far_p2': 0.5}


def _bench_inner_pose(who, key):
    sgn = 1.0 if who == 'a' else -1.0
    inner = 'arm_r' if who == 'a' else 'arm_l'
    pose = bench_pose(who, 'rest', lean=ARM_LEAN.get(key, 0.0))
    tmp = B.Rig(pose)
    cam = bench_cam()
    s = B.PROP['palm']
    plane = BENCH_SEAT_Y - 6.0
    # fingers toward the middle of the bench and a little forward, the back of the hand up (toward the camera)
    hd = _n(np.array([-sgn * 1.0, 0.05, 0.45]))
    up = np.array([0.0, -1.0, 0.0])
    th = 1.0 if who == 'a' else -1.0
    rest_wr = tmp.arm[inner]['wr']
    pole = np.array([-sgn * 0.25, 0.55, -0.80])
    curl, spread, grip = 0.45, 0.15, 0.25
    if key.startswith('list'):
        # Konrad holds the list up beside his left hip, pinched at its right edge, the fingers pointing up and out
        i = int(key[-1])
        gx, gy = LIST_HAND[0], LIST_HAND[1] + 2.0 * i
        g = cam.on_plane(gx, gy, plane - 26.0)
        hd = _n(np.array([0.55, -0.55, 0.35]))
        up = _n(np.array([-0.30, -0.25, -0.92]))
        up = _n(up - hd * float(np.dot(up, hd)))
        wr = g - hd * 0.85 * s
        curl, spread, grip = 0.42, 0.05, 0.75
        pole = np.array([0.45, 0.65, -0.60])
    else:
        mode = 'near' if key.startswith('near') else 'far'
        if key == 'hold':
            u = 1.0
            mode = 'near'
        elif key.endswith('p1'):
            u = 1.0 / 3.0
        elif key.endswith('p2'):
            u = 2.0 / 3.0
        else:
            u = 0.0
        gp = _grip_px(who, mode, u)
        g = cam.on_plane(gp[0], gp[1], plane)
        # the palm's underside on the pages: wrist = grip - fingers x half a palm + the palm's thickness; across
        # the bench (far) he gets the near corner of the pages under his finger tips and drags them
        reach_k = 0.55 if mode == 'near' else 1.15
        on = g - hd * reach_k * s + up * 0.20 * s
        if key.endswith('r1'):
            hover = on + np.array([0.0, -16.0, 0.0])
            wr = rest_wr + (hover - rest_wr) * 0.62 + np.array([0.0, -9.0, 0.0])
            curl, spread, grip = 0.40, 0.18, 0.2
            hd = _n(hd + np.array([0.0, 0.35, 0.0]))
        elif key.endswith('r2'):
            wr = on + np.array([0.0, -11.0, 0.0]) + np.array([sgn * 6.0, 0.0, -3.0])
            curl, spread, grip = 0.14, 0.42, 0.0
        else:
            wr = on
            curl, spread, grip = (0.50, 0.12, 0.55) if mode == 'near' else (0.38, 0.10, 0.35)
        if key == 'hold':
            curl, spread, grip = 0.55, 0.1, 0.5
        if mode == 'far' and not key.endswith('r1'):
            # reaching across: the shoulder comes forward with the arm
            pose[inner + '_sh'] = True
    up = _n(up - hd * float(np.dot(up, hd)))
    spec = dict(wrist=wr, pole=pole, hand=dict(curl=curl, spread=spread, grip=grip, dir=hd, up=up, thumb=th))
    if pose.pop(inner + '_sh', False):
        sh = tmp.arm[inner]['sh']
        spec['sh_off'] = _n(wr - sh) * 9.0
    pose[inner] = spec
    return pose


def bench_arm_frame(who, key):
    """One cell of the h1 arm sheet: the inner arm ALONE (drawn under the body sprite by the runtime)."""
    if who == 'a' and key.startswith('list'):
        return np.zeros((ARMS_WH[1], ARMS_WH[0], 4), np.uint8)

    def fn():
        ch = dict(B.ALEXEI if who == 'a' else B.KONRAD)
        inner = 'arm_r' if who == 'a' else 'arm_l'
        arm = B.Rig(_bench_inner_pose(who, key)).arm[inner]
        out = render_arm(ch, arm, bench_cam(), ARMS_AT[0], ARMS_AT[1], ARMS_WH, bench_look(), 'fire')
        import env_c3p2_cine_people as PP
        return PP.back_rim(out, BENCH_RIM, width=2, top=0.45, left=1.0, right=0.0, seed=0, fall_off=False)
    return cached('bench_arm11', (who, key, _stacks()), fn)


def arms_sheet():
    """h1 arms.png: 2 rows (Alexei, Konrad) x ARM_COLS cells of ARMS_WH; returns (sheet, layout additions)."""
    order = sorted(ARM_COL, key=lambda k: ARM_COL[k])
    rows = [np.concatenate([bench_arm_frame(who, k) for k in order], axis=1) for who in ('a', 'k')]
    extra = {'arms_at': list(ARMS_AT), 'arm_cols': ARM_COLS, 'list_fold_at': list(LIST_FOLD_AT)}
    return np.concatenate(rows, axis=0), extra


# =============================================================================================== desk scenes
# r2 Alexei at the radio (Hotel Nord), r3 Konrad writing (Hotel Europa), f1 Konrad at the sorting table under the
# green lamp: a man seated at a table, seen from behind; the places draw a chair back over the r2/r3 figures
# (env_c3p2_cine_rooms.chair, centred x 172 / 552).  Round 11: the arm that moves (Alexei's right arm to the
# tuning knob, Konrad's writing LEFT hand -- the notepad lies to his front-left) is NOT part of the body sprite
# any more: its sheet holds it in every frame, the rest pose included, so there is never a second copy of it.
# The runtimes draw these sheets UNDER the body sprite, which covers the arm's root at the shoulder.
DESK = {
    'r2': dict(who='a', yaw=158.0, elev=8.0, scale=0.92, hip=(172.0, 304.0), light='dial', at=(40, 54),
               size=(270, 266), table=(-186.0, 40.0)),
    'r3': dict(who='k', yaw=210.0, elev=8.0, scale=0.92, hip=(556.0, 300.0), light='lamp', at=(420, 54),
               size=(220, 266), table=(-186.0, 40.0)),
    'f1': dict(who='k', yaw=160.0, elev=12.0, scale=0.98, hip=(432.0, 330.0), light='green', at=(296, 52),
               size=(272, 308), table=(-180.0, 44.0)),
}
KNOB = (348, 224)              # the tuning knob (layout radio.knob_tune)
# r2: the right arm of Alexei -- 0 resting on the table, 1 lifting, 2 / 3 on the way, 4 fingers on the knob,
# 5 turning it.  The runtime (ch3_radio.gd ARM_KEYS) steps 1..5 at 9.15 / 9.3 / 9.45 / 9.6 / 9.85 s.
ARM_A_AT = (176, 160)
ARM_A_WH = (196, 112)
ARM_A_N = 6
R2_REST_PX = (262, 237)        # where the right hand rests on the table (frame px)
# r3: the left hand of Konrad writes along layout radio.pad_line: HAND_K_POS positions x 2 pen strokes, then the
# same positions with the pencil lifted (frame = 2 * HAND_K_POS + position); the runtime shifts the sprite by
# the rest of the way to the line's growing end (< one position step), so the pencil stays on the line's end.
HAND_K_AT = (388, 150)
HAND_K_WH = (150, 110)
HAND_K_POS = 6
HAND_K_N = 3 * HAND_K_POS
R3_HEAD = (-4.0, 2.0, 0.0)
# f1: 0 head bowed over the halves, 1 lifting, 2 up, 3 up and turned toward the smell of smoke (left)
REG_POSES = 4
REG_HEADS = [(-6.0, 30.0, 0.0), (-9.0, 16.0, 0.0), (-12.0, -2.0, 0.0), (-24.0, -6.0, 0.0)]


def desk_cam(shot):
    d = DESK[shot]
    c = Cam(d['yaw'], d['elev'], d['scale'], (0.0, 0.0))
    p = c.px(np.array([0.0, -128.0, 0.0]))
    c.o = B._o3((d['hip'][0] - p[0], d['hip'][1] - p[1]))
    return c


def desk_look(shot):
    if shot == 'r2':
        # the dial and the cold window in front-right of him: warm key from the front-right, window rim
        return dict(key=(0.70, -0.10, -0.70), rim=(0.20, -0.60, -0.78), ambient=0.08, wrap=0.22, bg='karsk',
                    glow=(0.8, 0.2), fill=0.10, fill_dir=(-0.3, -0.8, 0.5), ao=0.5)
    if shot == 'r3':
        # the desk lamp at the front-left, the window rim
        return dict(key=(-0.75, -0.25, -0.62), rim=(-0.15, -0.62, -0.77), ambient=0.08, wrap=0.22, bg='berlin',
                    glow=(0.8, 0.2), fill=0.10, fill_dir=(0.3, -0.8, 0.5), ao=0.5)
    # f1: the green lamp above the table, in front of him: his back in its own shadow, the light on the hat's
    # crown, the shoulders and the rims
    return dict(key=(-0.20, -0.88, -0.44), rim=(-0.55, -0.55, -0.62), ambient=0.05, wrap=0.16, bg='berlin',
                glow=(0.8, 0.2), fill=0.05, fill_dir=(0.2, -0.8, 0.6), ao=0.55)


def _rest_arm(shot, tmp, sgn):
    ty, tz = DESK[shot]['table']
    wr = np.array([sgn * 18.0, ty - 7.0, tz + 30.0])
    return dict(wrist=wr, pole=tmp.R_ch @ np.array([sgn * 0.8, 0.6, -0.6]),
                hand=dict(curl=0.45, spread=0.15, grip=0.1, dir=_n(np.array([-sgn * 0.6, 0.15, 0.8])),
                          up=np.array([0.0, -1.0, 0.0])))


def desk_pose(shot, breath=0, head=None):
    """Seated at the table, leaning in, both forearms on the table (hands toward the middle)."""
    lean = (12.0 if shot != 'f1' else 16.0) - 1.2 * breath
    # r2: Alexei leans in toward the set at his front-right, listening (and the knob is within his reach)
    # r3: Konrad bends over the notepad, which lies far up the desk at his front-left
    spine = {'r2': (6.0, lean + 4.0, -6.0), 'r3': (-22.0, lean + 14.0, 6.0)}.get(shot, (0.0, lean, 0.0))
    pose = dict(root=(0.0, -128.0, 0.0), pelvis=(0.0, -6.0, 0.0), spine=spine,
                head=head or (0.0, 4.0, 0.0),
                leg_l=dict(fk=(84.0, 7.0, 86.0, -4.0)), leg_r=dict(fk=(84.0, 7.0, 86.0, -4.0)))
    tmp = B.Rig(pose)
    for key, sgn in (('arm_l', 1.0), ('arm_r', -1.0)):
        pose[key] = _rest_arm(shot, tmp, sgn)
    return pose


def _desk_scene_point(shot, x, y, plane='front', depth=None):
    """Scene point for an image pixel: on the table plane, or on the vertical plane z = depth."""
    cam = desk_cam(shot)
    if plane == 'table':
        return cam.on_plane(x, y, DESK[shot]['table'][0])
    r = cam.R.T
    a = r[2, 0] * (x - cam.o[0]) + r[2, 1] * (y - cam.o[1])
    z = cam.o[2] + (depth * cam.s - a) / r[2, 2]
    return r @ (np.array([x, y, z]) - cam.o) / cam.s


def _desk_char(shot):
    d = DESK[shot]
    ch = dict(B.ALEXEI if d['who'] == 'a' else B.KONRAD)
    if shot in ('r2', 'r3'):
        ch.update(hat=None, scarf=False, strap=None, bag=None)
        if d['who'] == 'a':
            # in his room: the grey roll-neck sweater, no quilted coat
            ch.update(coat='sweater', coat_mat='knit', coat_bulk=2.0, sleeve=2.2, collar=None, quilt=None, cuff=None,
                      hem=0.0)
        else:
            ch.update(coat='jacket', coat_mat='jacket', coat_bulk=2.6, sleeve=2.6, collar='suit', cuff='shirt',
                      collar_mat='jacket', hem=26.0)
    else:
        # f1: the overcoat with the collar turned up, the scarf inside it (no loose ends), the satchel on its strap
        ch.update(scarf=False)
    return ch


def _desk_clip(shot):
    ty, tz = DESK[shot]['table']

    def clip(Q):
        # the table top hides what is under it beyond its front edge (the knees, the far half of the thighs)
        return np.minimum(Q[:, 1] - (ty + 2.0), Q[:, 2] - (tz - 2.0))
    return clip


def _chair_f1(M, origin, cam):
    """f1: a plain archive chair under him -- seat, four turned legs with stretchers, two back posts with a
    curved back rail at the small of his back (oak; the lamp is in front of him, so mostly rims)."""
    w = M('chair')
    sy = -118.0                      # seat surface
    parts = [B.S.RoundBox((0.0, sy + 3.0, 6.0), (30.0, 3.0, 28.0), 1.5, w)]
    for sx in (-1.0, 1.0):
        for sz, top in ((-1.0, -196.0), (1.0, sy)):
            x, z = sx * 27.0, 6.0 + sz * 25.0
            parts.append(B.RC((x, top, z), (x, 0.0, z), 2.6, 2.4, w))
    for sx in (-1.0, 1.0):
        parts.append(B.RC((sx * 27.0, -40.0, -19.0), (sx * 27.0, -40.0, 31.0), 1.6, 1.6, w))
    parts.append(B.RC((-27.0, -40.0, 31.0), (27.0, -40.0, 31.0), 1.6, 1.6, w))
    for i in range(9):
        u0, u1 = i / 9.0, (i + 1) / 9.0
        x0, x1 = -27.0 + 54.0 * u0, -27.0 + 54.0 * u1
        z0, z1 = -19.0 - 7.0 * math.sin(math.pi * u0), -19.0 - 7.0 * math.sin(math.pi * u1)
        parts.append(B.RC((x0, -168.0, z0), (x1, -168.0, z1), 3.4, 3.4, w))
        parts.append(B.RC((x0, -186.0, z0), (x1, -186.0, z1), 2.4, 2.4, w))
    node = B.S.Union(parts, k=1.0)
    return B.place(node, origin, cam.R, cam.s)


def _f1_styles():
    """f1: the archive is dark, the green-shaded lamp hangs in front of him -- his overcoat is a dark slate navy
    whose few lit steps turn green, the felt of the hat the same; no saturated blue."""
    st = {}
    for nm, alb in (('coat', '#222937'), ('coat_lapel', '#222937'), ('felt', '#3a3438'), ('brim', '#3a3438'),
                    ('trouser', '#1e2028'), ('chair', '#3e2a1c')):
        st[nm] = B.MatStyle(B.ramp_for(alb, 'green'), B.TH7, dither=0.04 if nm in ('coat', 'felt') else 0.02,
                            rim='#5a7a6a')
    return st


def _desk_render(shot, pose, at=None, size=None, hide=(), extra=None):
    d = DESK[shot]
    ch = _desk_char(shot)
    cam = desk_cam(shot)
    x0, y0 = at or d['at']
    sz = size or d['size']
    out, _dd, _names = render_scene([(ch, pose, None, hide)], cam, x0, y0, sz, desk_look(shot), d['light'],
                                    clip=_desk_clip(shot) if shot != 'f1' else None, extra=extra,
                                    styles_over=_f1_styles() if shot == 'f1' else None)
    return out


def room_body(who, breath=0):
    """r2 / r3 body without the moving arm (Alexei's right, Konrad's left: their sheets hold them)."""
    shot = 'r2' if who == 'a' else 'r3'
    head = (14.0, 4.0, 0.0) if who == 'a' else R3_HEAD
    hide = ('arm_r',) if who == 'a' else ('arm_l',)
    return cached('desk', (shot, breath, 'r11'),
                  lambda: _desk_render(shot, desk_pose(shot, breath=breath, head=head), hide=hide))


def pole_for(sh, wr, y_target, out_dir, w_out=0.25):
    """An elbow pole that puts the elbow (two-bone IK, true bone lengths) as close as it can to the height
    y_target (a forearm resting on a table), on the side out_dir rather than across the body."""
    sh, wr = np.asarray(sh, float), np.asarray(wr, float)
    ax = _n(wr - sh)
    ref = _n(np.cross(ax, np.array([0.0, 0.0, 1.0])) + np.array([1e-4, 0.0, 0.0]))
    ref2 = np.cross(ax, ref)
    best, bc = None, 1e9
    for k in range(72):
        t = math.radians(k * 5.0)
        pv = ref * math.cos(t) + ref2 * math.sin(t)
        el, _w = B.ik2(sh, wr, B.PROP['upper'], B.PROP['fore'], pv)
        c = abs(float(el[1]) - y_target) - w_out * float(np.dot(el - sh, out_dir))
        if c < bc:
            bc, best = c, pv
    return best


def _bez(p0, p1, p2, p3, u):
    a = 1.0 - u
    return a * a * a * p0 + 3 * a * a * u * p1 + 3 * a * u * u * p2 + u * u * u * p3


R2_FRAMES = [  # (u along the path, curl, spread, grip, turn)
    (0.00, 0.42, 0.12, 0.15, 0.0),
    (0.20, 0.34, 0.16, 0.10, 0.0),
    (0.48, 0.24, 0.30, 0.05, 0.0),
    (0.78, 0.18, 0.45, 0.00, 0.0),
    (1.00, 0.52, 0.18, 0.62, 0.0),
    (1.00, 0.58, 0.18, 0.66, 1.0),
]


def r2_arm(i):
    """Rig arm (scene coordinates) of Alexei's right arm in frame i of the reach: from the rest on the table up in
    a low arc to the knob, where the finger tips and the thumb close round it (the grip point of the hand on the
    knob) and the wrist turns it."""
    ty, tz = DESK['r2']['table']
    base = desk_pose('r2', head=(14.0, 4.0, 0.0))
    tmp = B.Rig(base)
    sh = tmp.arm['arm_r']['sh']
    cam = desk_cam('r2')
    s = B.PROP['palm']
    w0 = cam.on_plane(R2_REST_PX[0], R2_REST_PX[1], ty - 7.0)
    knob = _desk_scene_point('r2', KNOB[0], KNOB[1], depth=tz + 40.0)
    dk = _n(knob - sh)
    dkh = _n(np.array([dk[0], 0.0, dk[2]]))
    u, curl, spread, grip, turn = R2_FRAMES[i]
    d_rest = _n(np.array([0.30, 0.12, 0.95]))
    up_rest = np.array([0.0, -1.0, 0.0])
    # at the knob the fingers point into the radio's face, the back of the hand toward him and up
    d_knob = _n(dkh * 0.45 + np.array([0.0, 0.12, 1.0]))
    up_knob = _n(np.array([-0.35, -0.90, -0.25]))
    up_knob = _n(up_knob - d_knob * float(np.dot(up_knob, d_knob)))
    wk = knob - d_knob * 1.08 * s + up_knob * 0.30 * s
    p1 = w0 + np.array([0.0, -26.0, 0.0]) + dkh * 6.0
    p2 = wk + np.array([0.0, -18.0, 0.0]) - dkh * 22.0
    wr = _bez(w0, p1, p2, wk, u)
    e = u * u * (3.0 - 2.0 * u)
    hd = _n(d_rest * (1.0 - e) + d_knob * e)
    up = _n(up_rest * (1.0 - e) + up_knob * e)
    if turn:
        # the wrist turns the knob: the back of the hand rolls round the fingers' axis
        c, s_ = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
        side = _n(np.cross(hd, up))
        up = _n(up * c + side * s_)
    pose = dict(base)
    pose['arm_r'] = dict(wrist=wr, sh_off=dk * 4.0 * e, pole=np.array([-0.55, 0.75, -0.40]),
                         hand=dict(curl=curl, spread=spread, grip=grip, dir=hd, up=up, thumb=1.0))
    return B.Rig(pose).arm['arm_r']


def arm_alexei_sheet():
    """r2: the right arm of Alexei, ARM_A_N frames (see R2_FRAMES), rendered alone (drawn under the body)."""
    frames = []
    ch = _desk_char('r2')
    for i in range(ARM_A_N):
        def fn(i=i):
            return render_arm(ch, r2_arm(i), desk_cam('r2'), ARM_A_AT[0], ARM_A_AT[1], ARM_A_WH, desk_look('r2'),
                              'dial')
        frames.append(cached('desk_arm', ('r2', i, 'r11'), fn))
    return np.concatenate(frames, axis=1)


PAD_LINE = (456, 230, 494)     # the line Konrad writes: on the part of the notepad the radio does not cover


def pad_line():
    return float(PAD_LINE[0]), float(PAD_LINE[1]), float(PAD_LINE[2])


PENCIL_TIP = (0.15, 1.45, -0.60)      # hand frame, x palm units (x * thumb side)
PENCIL_END = (0.60, 0.25, 0.55)
# the writing hand: finger direction, back of the hand (scene), thumb side (up: the hand rests on its little finger)
R3_HAND = ((-0.25, 0.10, 0.96), (0.80, -0.60, 0.0), -1.0)
R3_ELBOW_OUT = (-0.3, 0.0, -1.0)   # the elbow tucked in at his side: the forearm runs out along the desk and the
R3_ELBOW_W = 0.5                   # hand with the pencil stays in view at its far end


def pencil_node(M, a, s=None):
    """A pencil held in the writing hand (hand frame: +y the fingers, +z the back of the hand): the point on the
    paper in front of the finger tips, the shaft through the web of the thumb, the end over the knuckles."""
    s = s or B.PROP['palm']
    fr = B._frame(a['wr'], a['hdir'], a['hup'])
    th = a['thumb']
    tip = fr.to_view((PENCIL_TIP[0] * s * th, PENCIL_TIP[1] * s, PENCIL_TIP[2] * s))
    back = fr.to_view((PENCIL_END[0] * s * th, PENCIL_END[1] * s, PENCIL_END[2] * s))
    ax = _n(tip - back)
    cone0 = tip - ax * 5.0
    body = B.RC(tuple(back), tuple(cone0), 1.35, 1.35, M('pencil'))
    cone = B.RC(tuple(cone0), tuple(tip - ax * 1.2), 1.30, 0.55, M('pencil_wood'))
    lead = B.RC(tuple(tip - ax * 1.4), tuple(tip), 0.55, 0.30, M('graphite'))
    return B.S.Union([body, cone, lead], k=0.2)


def r3_arm(i):
    """Rig arm of Konrad's left (writing) arm in sheet frame i (position, stroke, lifted)."""
    x0, y, x1 = pad_line()
    lifted = i >= 2 * HAND_K_POS
    pos = (i - 2 * HAND_K_POS) if lifted else i // 2
    stroke = 0 if lifted else i % 2
    tx = x0 + (x1 - x0) * pos / float(HAND_K_POS - 1) + (1.5 if stroke else 0.0)
    ty = y - (0.8 if stroke else 0.0)
    cam = desk_cam('r3')
    tip = cam.on_plane(tx, ty, DESK['r3']['table'][0])
    base = desk_pose('r3', head=R3_HEAD)
    s = B.PROP['palm']
    # the hand on its little-finger side, the back of the hand up and out, the fingers toward the pad's far side
    hd = _n(np.asarray(R3_HAND[0], float))
    up = _n(np.asarray(R3_HAND[1], float))
    up = _n(up - hd * float(np.dot(up, hd)))
    th = R3_HAND[2]
    fr_R = np.stack([np.cross(hd, up), hd, up], axis=1)
    off = fr_R @ np.array([PENCIL_TIP[0] * s * th, PENCIL_TIP[1] * s, PENCIL_TIP[2] * s])
    wr = tip - off + np.array([0.0, -(7.0 if lifted else 0.0), 0.0])
    pose = dict(base)
    sh = B.Rig(base).arm['arm_l']['sh']
    # the forearm lies on the desk: the elbow rests on the table top beside the notepad, out to his left
    pole = pole_for(sh, wr, DESK['r3']['table'][0] - 9.0, np.array(R3_ELBOW_OUT), w_out=R3_ELBOW_W)
    pose['arm_l'] = dict(wrist=wr, pole=pole,
                         hand=dict(curl=0.58 + (0.06 if stroke else 0.0), spread=0.05, grip=0.55, dir=hd, up=up,
                                   thumb=th))
    return B.Rig(pose).arm['arm_l']


def hand_konrad_sheet():
    """r3: Konrad's left arm writing on the notepad: HAND_K_N frames (see HAND_K_POS), each with the pencil."""
    frames = []
    ch = _desk_char('r3')
    for i in range(HAND_K_N):
        def fn(i=i):
            arm = r3_arm(i)
            return render_arm(ch, arm, desk_cam('r3'), HAND_K_AT[0], HAND_K_AT[1], HAND_K_WH, desk_look('r3'),
                              'lamp', extra=lambda M, arm=arm: pencil_node(M, arm))
        frames.append(cached('desk_hand', ('r3', i, 'r11'), fn))
    return np.concatenate(frames, axis=1)


def reg_pose(pose_i):
    """f1: seated on the archive chair at the sorting table, forearms on the table, the head per REG_HEADS."""
    pose = desk_pose('f1', head=REG_HEADS[pose_i])
    # the knees under the table, the shins down to the floor (behind the chair seat and the coat)
    pose['leg_l'] = dict(fk=(86.0, 10.0, 84.0, -4.0))
    pose['leg_r'] = dict(fk=(82.0, 8.0, 92.0, -4.0))
    return pose


def reg_body(pose_i):
    def fn():
        cam = desk_cam('f1')
        return _desk_render('f1', reg_pose(pose_i), extra=lambda M, origin: _chair_f1(M, origin, cam))
    return cached('desk', ('f1', pose_i, 'r11'), fn)


# =============================================================================================== e3a the hatch
# Looking down into the open coal hatch from its front rim: the arm of Alexei rises out of the smoke (the quilted
# sleeve from the dark below: shoulder -> elbow -> wrist -> an opened, sooty hand), Konrad kneels at the rim to the
# upper right, his arm comes down (navy sleeve, shirt cuff) and his hand closes round the wrist, then he pulls.
# One scene per frame, joints in canvas px / E3A_S (the canvas is 520 x 360 at E3A_AT in the frame).
E3A_AT = (120, 0)
E3A_WH = (520, 360)
E3A_S = 2.05
E3A_A = dict(coat='quilted', coat_mat='quilt', sleeve=5.2, quilt=14.0, skin='skin', cuff=None)
E3A_K = dict(coat='long', coat_mat='coat', sleeve=2.4, skin='skin_k', cuff='shirt')


def _arm_dict(sh, wr, pole, hdir, hup, curl, spread, grip, thumb, s=E3A_S):
    """Arm from shoulder and wrist (canvas px) with the true bone lengths: the elbow by two-bone IK."""
    shq, wrq = np.asarray(sh, float) / s, np.asarray(wr, float) / s
    el, wrq = B.ik2(shq, wrq, B.PROP['upper'], B.PROP['fore'], pole)
    return dict(sh=shq, el=el, wr=wrq, hdir=_n(hdir), hup=_n(np.asarray(hup, float) - _n(hdir) *
                float(np.dot(hup, _n(hdir)))), curl=curl, spread=spread, grip=grip, thumb=thumb)


# round 11: seven frames -- 0 the hand rises out of the smoke, 1 the fingers open, reaching, 2 Konrad's hand comes in
# from the rim (open), 3 it closes round the wrist (Alexei's round his), 4-6 the pull: both arms rise, Konrad's
# elbow bends and his shoulder goes back.  The runtime (ch3_escape.gd HANDS) steps them at 8.0 .. 10.0 s.
E3A_FRAMES = 7
E3A_UP = (0.0, -10.0, -12.0, -14.0, -32.0, -50.0, -66.0)      # Alexei's wrist rises (canvas px)
E3A_RISE = (0.0, 6.0, 7.0, 8.0, 28.0, 46.0, 62.0)              # ... and his shoulder with it (he is pulled up)


def e3a_arms(fr):
    """(alexei arm dict, konrad arm dict or None) of frame fr in canvas px (z toward the viewer).  Alexei stands
    on the chute below and reaches up (the shoulder deep in the dark, the arm almost straight toward the light);
    Konrad kneels at the right rim, his shoulder just outside the frame."""
    up = E3A_UP[fr]
    wx, wy = 182.0, 214.0 + up
    rise = E3A_RISE[fr]
    grip = fr >= 3
    a = _arm_dict(sh=(246.0, 432.0 - rise, -150.0 + rise * 0.6), wr=(wx, wy, 10.0), pole=(0.6, 0.3, 0.5),
                  hdir=(0.10, -0.82, 0.56) if not grip else (0.35, -0.80, 0.48),
                  hup=(-0.15, 0.25, 0.95) if not grip else (-0.45, 0.2, 0.87),
                  curl=(0.42, 0.05, 0.10, 0.55, 0.60, 0.62, 0.62)[fr], spread=(0.25, 1.25, 1.1, 0.35, 0.3, 0.3, 0.3)[fr],
                  grip=(0.05, 0.0, 0.0, 0.55, 0.6, 0.6, 0.6)[fr], thumb=1.0)
    k = None
    if fr >= 2:
        if fr == 2:
            # reaching in: the open hand above and to the right of the wrist, coming down
            kx, ky, kz = wx + 92.0, wy - 76.0, 52.0
            kd, ku, kc, ks, kg = (-0.70, 0.62, -0.30), (0.20, -0.30, 0.93), 0.18, 0.55, 0.0
        else:
            kx, ky, kz = wx + 46.0, wy - 22.0, 34.0
            kd, ku, kc, ks, kg = (-0.82, 0.48, -0.30), (0.25, -0.45, 0.86), 0.78, 0.12, 0.85
        back = max(0, fr - 3)
        k = _arm_dict(sh=(478.0 + 10.0 * back, 34.0 - 9.0 * back, 112.0 - 8.0 * back), wr=(kx, ky, kz),
                      pole=(0.35, -0.75, 0.55) if fr > 2 else (0.5, -0.2, 0.85), hdir=kd, hup=ku, curl=kc, spread=ks,
                      grip=kg, thumb=1.0)
    return a, k


def _e3a_render(fr):
    import env_c3p2_cine_hands as HN
    M = A.Mats()
    a, k = e3a_arms(fr)
    nodes = [B.arm_node(M, E3A_A, a)]
    if k is not None:
        nodes.append(B.arm_node(M, E3A_K, k))
        # his shoulder and back leaning over the rim, mostly outside the frame (the arm belongs to a body)
        shp = k['sh']
        cm = M('coat')
        torso = B.S.Union([B.E(tuple(shp + np.array([26.0, -16.0, 10.0])), (34.0, 26.0, 30.0), cm),
                           B.E(tuple(shp + np.array([58.0, -6.0, 0.0])), (40.0, 34.0, 34.0), cm),
                           B.RC(tuple(shp + np.array([10.0, -24.0, 14.0])), tuple(shp + np.array([40.0, -60.0, 20.0])),
                                9.0, 10.0, M('neck'))], k=8.0)
        nodes.append(torso)
    root = B.place(B.S.Union(nodes, k=0.6), (0.0, 0.0), np.eye(3), E3A_S)
    # round 11: more of the cold yard light on Konrad's sleeve (it read as a black log): fill from the upper right
    look = dict(key=(0.10, 0.80, 0.22), rim=(0.60, -0.62, 0.48), ambient=0.06, wrap=0.14, bg='berlin',
                glow=(0.8, 0.2), fill=0.17, fill_dir=(0.55, -0.65, 0.5), ao=0.5)
    st = HN._styles_escape()
    # round 11: Konrad's navy sleeve stays navy in the hatch's glow (the old ramp's lit steps went mauve and read
    # as bare skin) -- dark navy, then a warm grey-brown only on the steps the fire reaches
    st['coat'] = B.MatStyle(P_ramp('#04060b', '#090e1a', '#0f1628', '#172036', '#202a40', '#2c3344', '#463f3c',
                                   '#665044'), B.TH7, dither=0.03, rim='#7290b0')
    ax0 = a['sh'] * E3A_S
    tf = S_Frame_along(a['el'] * E3A_S, (a['wr'] - a['el']), (0.0, 0.3, 1.0), E3A_S)
    out, d = B.trace_paint(root, M, E3A_WH, look, st, frames={'tf': tf},
                           tone_passes=[__import__('chargen_portrait2_cast').pass_stitches('quilt', 14.0 * 0.8, frame='tf', axis=1)],
                           ss=3, glow=((200.0, 430.0, -60.0), 380.0, 0.55), depth=DEPTH)
    return _fade_bottom(out, 262, 372)


def S_Frame_along(o, y_axis, z_hint, s):
    ey = _n(y_axis)
    zh = np.asarray(z_hint, float)
    ez = _n(zh - ey * float(np.dot(zh, ey)))
    ex = np.cross(ey, ez)
    return B.S.Frame(np.asarray(o, float), np.stack([ex, ey, ez], axis=1) / s)


def _fade_bottom(img, y0, y1):
    """The sleeve sinks into the smoke and the dark of the chute: darker, then dithered away toward the bottom."""
    out = img.copy()
    h, w = out.shape[:2]
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
    for y in range(max(0, y0), min(h, y1)):
        u = (y - y0) / float(y1 - y0)
        row = out[y]
        m = row[:, 3] > 0
        row[m, :3] = (row[m, :3].astype(np.float32) * (1.0 - 0.8 * u) + np.array([12, 8, 8]) * 0.8 * u).astype(np.uint8)
        th = bay[y % 4, np.arange(w) % 4]
        row[m & (th < (u - 0.55) * 2.2), 3] = 0
    return out


def P_ramp(*cols):
    import chargen_portrait2_paint as P
    return P.ramp(*cols)


def e3a_frame(fr):
    return cached('e3a11', fr, lambda: _e3a_render(fr))


# =============================================================================================== e3b in the snow
# Both men on their backs in the yard, heads toward each other a hand's breadth apart (Konrad left, his hat beside
# him; Alexei right in the ushanka), seen from the side, low over the snow; chests heaving (b = 0 / 1).
E3B_AT = (40, 220)
E3B_WH = (560, 96)
E3B_HEADS = (292.0, 360.0)
E3B_CAM = dict(yaw=0.0, elev=11.0, scale=0.52)   # round 11: low over the snow like the yard's own camera
E3B_MOUTH_ROW = 258.0


def _lying_pose(who, b):
    """Lying on the back along the scene x axis, the head toward x = 0 (Konrad at -x, Alexei at +x)."""
    sgn = -1.0 if who == 'k' else 1.0
    # body +y (toward the feet) -> scene -sgn*x ... feet away from the other man; body +z (front) -> up (-y)
    col_y = np.array([sgn, 0.0, 0.0])
    col_z = np.array([0.0, -1.0, 0.0])
    col_x = np.cross(col_y, col_z)
    Rb = np.stack([col_x, col_y, col_z], axis=1)
    heave = 1.6 * b
    pose = dict(pelvis_R=Rb, root=(sgn * 272.0, -15.0, 0.0), spine=(0.0, -4.0 - heave, 0.0))
    if who == 'k':
        pose['head'] = (8.0, -16.0, 0.0)             # face up to the sky (a profile from the low camera), chin up
        pose['arm_l'] = dict(fk=(70.0, 78.0, 34.0), hand=dict(curl=0.45, spread=0.35))    # flung out in the snow
        pose['arm_r'] = dict(fk=(40.0, 12.0, 110.0, 40.0), hand=dict(curl=0.6))            # on the chest
        pose['leg_l'] = dict(fk=(6.0, 6.0, 4.0, 10.0))
        pose['leg_r'] = dict(fk=(58.0, 4.0, 100.0, 10.0))                                    # knee up
    else:
        pose['head'] = (-10.0, -14.0, 0.0)
        pose['arm_r'] = dict(fk=(60.0, 84.0, 40.0), hand=dict(curl=0.4, spread=0.4))       # flung out
        pose['arm_l'] = dict(fk=(36.0, 10.0, 104.0, 40.0), hand=dict(curl=0.6))             # on the chest
        pose['leg_l'] = dict(fk=(52.0, 8.0, 96.0, 10.0))                                    # knee up
        pose['leg_r'] = dict(fk=(4.0, 10.0, 6.0, 12.0))
    return pose


def _e3b_cam():
    c = Cam(E3B_CAM['yaw'], E3B_CAM['elev'], E3B_CAM['scale'], (0.0, 0.0))
    # Konrad's head lands at the frame x E3B_HEADS[0], mouths on row ~258
    rk = B.Rig(_lying_pose('k', 0))
    hk = c.px(rk.head((0.0, 0.0, 0.0)))
    c.o = B._o3((E3B_HEADS[0] - hk[0], E3B_MOUTH_ROW - 2.0 - hk[1]))
    return c


def e3b_breath():
    """The two mouths in frame px (layout escape.e3b_breath: the runtime's breath puffs start there)."""
    cam = _e3b_cam()
    out = []
    for who in ('k', 'a'):
        r = B.Rig(_lying_pose(who, 0))
        hs = B.HEAD_SCALE
        m = r.atlas + hs * (r.head((0.0, 18.0, 14.0)) - r.atlas)
        p = cam.px(m)
        out.append([int(round(p[0])), int(round(p[1]))])
    return out


def _e3b_render(b):
    import env_c3p2_cine_hands as HN
    cam = _e3b_cam()
    figs = [(dict(B.KONRAD, hat=None, scarf=True, bag=None), _lying_pose('k', b), None),
            (dict(B.ALEXEI, bag=None), _lying_pose('a', b), None)]

    def hat(M, origin):
        # the fedora upside down beside his head, brim in the snow
        hp = A.head_params()
        hd = B.fedora_soft(M, hp, y0=-13.2)
        node = hd['node']
        rk = B.Rig(_lying_pose('k', 0))
        pos = rk.head((0.0, 0.0, 0.0)) + np.array([-8.0, -2.0, 46.0])
        R = B.S.rot(0.0, 180.0, 18.0)
        return B.place(B.S.Xform(node, o=pos, R=R), origin, cam.R, cam.s)
    look = dict(key=(0.50, -0.80, 0.33), rim=(-0.55, -0.45, -0.70), ambient=0.09, wrap=0.18, bg='berlin',
                glow=(0.8, 0.2), fill=0.14, fill_dir=(0.0, 0.85, 0.5), ao=0.5)

    def sink(Q):
        return Q[:, 1] + 1.5                     # they lie IN the snow: the lowest bit of each body is hidden

    out, d, names = render_scene(figs, cam, E3B_AT[0], E3B_AT[1], E3B_WH, look, 'yard', extra=hat, eyes=False,
                                 clip=sink, rim=False)
    return _snow_contact(out, d)


SNOW_E3B = np.array([[74, 84, 101], [92, 103, 121], [118, 129, 146]], np.float32)


def _snow_contact(out, d):
    """Round 11: no sticker edge -- the snow in front covers the bodies' lowest rows with a soft, uneven lip (a
    trodden hollow behind it), and a few flakes have settled on the upturned cloth."""
    out = out.copy()
    a = out[..., 3] > 0
    h, w = a.shape
    for x in range(w):
        ys = np.nonzero(a[:, x])[0]
        if ys.size == 0:
            continue
        # an uneven lip: drifts of 0-3 px, in runs (value noise along x), never a constant line
        n = 0.5 * CC_hash(x // 5, 3) + 0.5 * CC_hash(x // 5 + 1, 3) * ((x % 5) / 5.0) + 0.25 * CC_hash(x, 9)
        lip = int(n * 3.2) + (1 if ys.size > 12 else 0)
        for j in range(lip):
            y = ys[-1] - j
            if y < 0 or not a[y, x]:
                break
            c = SNOW_E3B[min(2, lip - 1 - j)]
            out[y, x, :3] = (out[y, x, :3].astype(np.float32) * 0.2 + c * 0.8).astype(np.uint8)
        y = ys[-1] + 1
        if y < h and not a[y, x] and lip == 0:
            out[y, x, :3] = (56, 64, 80)
            out[y, x, 3] = 255
    # a few flakes settled on the cloth that faces the sky (hashed, sparse -- no lattice)
    up = a & (d.n[..., 1] < -0.55)
    yy, xx = np.mgrid[0:h, 0:w]
    hv = (xx.astype(np.int64) * 374761393 + yy.astype(np.int64) * 668265263) & 0xFFFFFFFF
    hv = ((hv ^ (hv >> 13)) * 1274126177) & 0xFFFFFFFF
    fl = up & ((((hv ^ (hv >> 16)) & 0xFFFF) / 65535.0) < 0.035)
    out[fl, :3] = (out[fl, :3].astype(np.float32) * 0.35 + np.array([150, 160, 176]) * 0.65).astype(np.uint8)
    return out


def CC_hash(x, seed):
    v = (x * 374761393 + seed * 668265263) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def lying_men(b):
    return cached('e3b11', b, lambda: _e3b_render(b))


# =============================================================================================== e1 the chute
# First person up the coal chute: Konrad shoves the tied file ahead of him up the steel slide toward the square of
# snow light.  His forearms come up from the bottom edge (navy sleeves, shirt cuffs), both hands flat against the
# back of the file, fingers spread, knuckles sooty.  2 frames (0 grip, 1 shove: 8 px higher, fingers pressing).
E1_WH = (220, 130)
E1_S = 1.55
E1_TILT = -34.0                 # round 11: the file shows more of its back, the hands lie flat on it, fingers up
E1_HAND = (lambda sx: (-sx * 0.20, -0.86, -0.46), lambda sx: (sx * 0.05, -0.46, 0.89))


def _e1_render(fr):
    import env_c3p2_cine_hands as HN
    M = A.Mats()
    b = 0.0 if fr == 0 else -8.0
    s = E1_S
    ch = dict(coat='long', coat_mat='coat', sleeve=4.0, skin='skin_k', cuff='shirt')
    nodes = []
    cy = 64.0 + b
    piv = np.array([110.0 / s, cy / s, 0.0])
    Rt = B.S.rot(0.0, E1_TILT, 0.0)
    n_face = Rt @ np.array([0.0, 0.0, 1.0])                  # the file's back (toward us) after the tilt
    up_face = Rt @ np.array([0.0, -1.0, 0.0])                # 'up' along it, toward the pages
    hs = B.PROP['palm']
    for sx in (-1.0, 1.0):
        # round 11: the forearms come in diagonally from the lower corners (not end-on: no 'balls' of sleeve); the
        # hands lie flat ON the back of the file (palm on the card, fingers up along it and spread, the thumbs
        # turned in), the backs of the hands toward us with their sooty knuckles
        hd = _n(up_face + np.array([-sx * 0.22, 0.0, 0.0]))
        palm_c = piv + Rt @ np.array([sx * 46.0 / s, 4.0 / s, 26.0 / s]) + n_face * (0.24 * hs)
        wrq = palm_c - hd * (0.50 * hs)
        shq = np.array([(110.0 + sx * 168.0) / s, (250.0 + b) / s, 70.0 / s])
        el, wrq = B.ik2(shq, wrq, B.PROP['upper'], B.PROP['fore'], np.array([sx * 0.9, 0.3, 0.2]))
        hup = _n(n_face - hd * float(np.dot(n_face, hd)))
        a = dict(sh=shq, el=el, wr=wrq, hdir=hd, hup=hup, curl=0.06 if fr == 0 else 0.12,
                 spread=0.62 if fr == 0 else 0.72, grip=0.0, thumb=sx)
        nodes.append(B.arm_node(M, ch, a))
    # the tied file: grey-brown card cover, the edge of the pages, string crossed over it
    fm, pm, tm = M('card'), M('paper'), M('string')
    cover = B.S.RoundBox((110.0 / s, cy / s, 0.0), (70.0 / s, 18.0 / s, 26.0 / s), 2.0, fm)
    pages = B.S.RoundBox((110.0 / s, (cy - 15.0) / s, 0.0), (66.0 / s, 4.0 / s, 24.0 / s), 1.0, pm)
    string = B.S.Union([B.RC((110.0 / s, (cy - 20.0) / s, 27.0 / s), (110.0 / s, (cy + 19.0) / s, 27.5 / s), 0.7, 0.7, tm),
                        B.RC((40.0 / s, (cy - 1.0) / s, 27.0 / s), (180.0 / s, (cy + 1.0) / s, 27.5 / s), 0.7, 0.7, tm),
                        B.RC((110.0 / s, (cy - 20.5) / s, -24.0 / s), (110.0 / s, (cy - 20.5) / s, 27.0 / s), 0.7, 0.7, tm)],
                       k=0.3)
    # the file lies on the slide: tip it so its top (pages, string) faces up the chute toward us
    nodes.append(B.S.Xform(B.S.Xform(B.S.Union([cover, pages, string], k=0.6), o=-piv), o=piv, R=Rt))
    root = B.place(B.S.Union(nodes, k=0.4), (0.0, 0.0), np.eye(3), s)
    look = dict(key=(0.0, -0.80, -0.60), rim=(0.0, -0.9, -0.4), ambient=0.08, wrap=0.25, bg='berlin',
                glow=(0.8, 0.2), fill=0.30, fill_dir=(0.1, 0.55, 0.83), ao=0.5)
    st = HN._styles_escape()
    st['card'] = B.MatStyle(B.ramp_for('#7e6242', 'night'), B.TH7, dither=0.03, rim='#a1aab7')
    st['paper'] = B.MatStyle(B.ramp_for('#d8cfb2', 'night'), B.TH7, rim='#c2c9d2')
    st['string'] = B.MatStyle(B.ramp_for('#8a7a58', 'night'), B.TH7, rim='#c2c9d2')
    out, d = B.trace_paint(root, M, E1_WH, look, st, ss=3, depth=DEPTH)
    # the sleeves leave through the bottom edge into the dark of the chute
    return _fade_bottom(out, 112, 150)


def chute_file_sheet():
    """e1 drop-in for env_c3p2_cine_fire.e1_file: 2 frames of 220 x 130, bottom-anchored by the runtime."""
    return np.concatenate([cached('e1r11', fr, lambda fr=fr: _e1_render(fr)) for fr in (0, 1)], axis=1)


# =============================================================================================== e2 out of the hatch
# The yard from the side, low: Konrad climbs out of the coal hatch (the mouth between the back edge y 218 and the
# front edge y 246 of env_c3p2_cine_fire.HATCH, centre x 320): 0 head and shoulders out, a forearm on the rim, the
# file pushed onto the snow; 1 out to the waist, a knee on the rim; 2 / 3 on hands and knees in the snow right of
# the hatch (two steps), the file under his left hand.  Below the ground everything is cut (inside the hatch).
E2_AT = (190, 70)
E2_WH = (420, 220)
E2_CAM = dict(yaw=90.0, elev=14.0, scale=0.60)
E2_MOUTH = (320.0, 232.0)          # hatch centre on the ground (frame px)


def _e2_cam():
    c = Cam(E2_CAM['yaw'], E2_CAM['elev'], E2_CAM['scale'], (0.0, 0.0))
    c.o = B._o3(E2_MOUTH)
    return c


def _e2_crawl(zc, step):
    """On hands and knees, the hips at scene z = zc (toward image right), step 0 / 1 = which pair is forward."""
    sw = 14.0 if step else -14.0
    hip_h = 92.0
    pose = dict(root=(0.0, -hip_h, zc), pelvis=(0.0, 76.0, 0.0), spine=(0.0, 8.0, 0.0), head=(0.0, -58.0, 0.0))
    tmp = B.Rig(pose)
    sh_l = tmp.chest((38.5, 23.0, -3.0))
    sh_r = tmp.chest((-38.5, 23.0, -3.0))
    pose['arm_l'] = dict(wrist=np.array([sh_l[0] + 4.0, -8.0, sh_l[2] + 22.0 + sw]), pole=np.array([0.3, 0.0, -1.0]),
                         hand=dict(curl=0.3, spread=0.5, dir=(0.15, 0.0, 1.0), up=(0.0, -1.0, 0.0)))
    pose['arm_r'] = dict(wrist=np.array([sh_r[0] - 4.0, -8.0, sh_r[2] + 22.0 - sw]), pole=np.array([-0.3, 0.0, -1.0]),
                         hand=dict(curl=0.3, spread=0.5, dir=(-0.15, 0.0, 1.0), up=(0.0, -1.0, 0.0)))
    hip_l = tmp.pelvis((16.0, 0.0, 0.0))
    hip_r = tmp.pelvis((-16.0, 0.0, 0.0))
    pose['leg_l'] = dict(ankle=np.array([hip_l[0], -9.0, hip_l[2] - 80.0 + sw * 0.8]), pole=np.array([0.0, 0.3, 1.0]),
                         foot=(0.0, 0.6, -0.8))
    pose['leg_r'] = dict(ankle=np.array([hip_r[0], -9.0, hip_r[2] - 80.0 - sw * 0.8]), pole=np.array([0.0, 0.3, 1.0]),
                         foot=(0.0, 0.6, -0.8))
    return pose


# the frames of e2 (round 11: six steps, no jump -- the hips travel 62 -> 92 -> 118 -> 150 -> 172 -> 194 along the
# yard, i.e. ~13-19 px a frame; the hatch's right rim is at z ~ 127)
E2_FRAMES = 6
E2_FILE_Z = (196.0, 214.0, 228.0, 0.0, 0.0, 0.0)       # the file on the snow ahead of him (0: under his left hand)


def _e2_pose(fr):
    """Konrad climbs out of the coal hatch toward image right (= his +z; scene x = toward the wall)."""
    if fr == 0:
        # head and shoulders out, leaning on his forearms on the snow beyond the rim, shoving the file ahead
        pose = dict(root=(0.0, 58.0, 62.0), pelvis=(0.0, 12.0, 0.0), spine=(0.0, 32.0, 0.0), head=(0.0, -30.0, 0.0),
                    leg_l=dict(fk=(24.0, 6.0, 40.0)), leg_r=dict(fk=(-4.0, 6.0, 22.0)))
        pose['arm_l'] = dict(wrist=np.array([16.0, -5.0, 156.0]), pole=np.array([0.6, 0.7, -0.3]),
                             hand=dict(curl=0.3, spread=0.5, dir=(0.0, 0.2, 1.0), up=(0.0, -1.0, 0.0)))
        pose['arm_r'] = dict(wrist=np.array([-14.0, -6.0, 178.0]), pole=np.array([-0.6, 0.7, -0.3]),
                             hand=dict(curl=0.2, spread=0.4, dir=(0.0, 0.1, 1.0), up=(0.0, -1.0, 0.0)))
        return pose
    if fr == 1:
        # out to the waist: the torso over the rim, both hands planted on the snow, pushing up
        pose = dict(root=(0.0, -6.0, 94.0), pelvis=(0.0, 44.0, 0.0), spine=(0.0, 26.0, 0.0), head=(0.0, -46.0, 0.0),
                    leg_l=dict(fk=(40.0, 6.0, 60.0)), leg_r=dict(fk=(6.0, 6.0, 30.0)))
        tmp = B.Rig(pose)
        for key, sx in (('arm_l', 1.0), ('arm_r', -1.0)):
            sh = tmp.arm[key]['sh']
            pose[key] = dict(wrist=np.array([sx * 22.0, -8.0, sh[2] + 18.0]), pole=np.array([sx * 0.4, 0.2, -1.0]),
                             hand=dict(curl=0.3, spread=0.5, dir=(sx * 0.15, 0.0, 1.0), up=(0.0, -1.0, 0.0)))
        return pose
    if fr == 2:
        # the left knee up on the rim, the right leg still in the hatch, the hands further on
        pose = _e2_crawl(118.0, 0)
        pose['root'] = (0.0, -52.0, 118.0)
        pose['pelvis'] = (0.0, 58.0, 0.0)
        pose['leg_l'] = dict(ankle=np.array([16.0, -9.0, 62.0]), pole=np.array([0.0, 0.3, 1.0]), foot=(0.0, 0.6, -0.8))
        pose['leg_r'] = dict(fk=(10.0, 6.0, 40.0))                                         # hanging in the hatch
        return pose
    return _e2_crawl((150.0, 172.0, 194.0)[fr - 3], (fr - 3) % 2)


def _e2_render(fr):
    cam = _e2_cam()
    ch = dict(B.KONRAD, scarf=True)
    pose = _e2_pose(fr)

    def file_node(M, origin):
        m, pm = M('card'), M('paper')
        if E2_FILE_Z[fr] > 0.0:
            c = np.array([-16.0, -6.0, E2_FILE_Z[fr]])
        else:
            rk = B.Rig(pose)
            c = rk.arm['arm_l']['wr'] + np.array([0.0, 0.0, 24.0])
            c[1] = -6.0
        box = B.S.Union([B.S.RoundBox(tuple(c), (22.0, 5.0, 30.0), 1.5, m),
                         B.S.RoundBox(tuple(c + np.array([0.0, -5.5, 0.0])), (20.0, 1.2, 28.0), 0.6, pm)], k=0.5)
        return B.place(box, origin, cam.R, cam.s)
    look = dict(key=(0.55, -0.75, 0.38), rim=(-0.6, 0.5, -0.6), ambient=0.08, wrap=0.15, bg='berlin',
                glow=(0.8, 0.2), fill=0.16, fill_dir=(-0.2, 0.85, 0.45), ao=0.5)

    def clip(Q):
        return Q[:, 1] - 2.0                     # nothing below the snow (inside the hatch)
    out, d, names = render_scene([(ch, pose, None)], cam, E2_AT[0], E2_AT[1], E2_WH, look, 'yard', extra=file_node,
                                 eyes=True, clip=clip)
    return out


def hatch_konrad_sheet():
    """e2 drop-in for env_c3p2_cine_fire.e2_konrad: E2_FRAMES frames of 420 x 220 at E2_AT (the runtime steps them
    at ch3_escape.gd KONRAD)."""
    return np.concatenate([cached('e2r11', fr, lambda fr=fr: _e2_render(fr)) for fr in range(E2_FRAMES)], axis=1)
