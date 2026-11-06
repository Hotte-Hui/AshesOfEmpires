"""env_c3p2_cine_people -- every person of LS_C3_Radio / _Fire / _Escape / _Halves that is not a close hero shot
(owner: figures stream, round 10).  All of them stand on the anatomical rig of env_c3p2_cine_body (shoulder ->
elbow -> wrist -> hand, hip -> knee -> foot, portrait heads, garments that follow the bones).

Drop-in sprites (same sheet layout as the round-8 painted figures they replace, so the runtimes need no change):
  quay_walk_sheet(kind, n=6)      h2   side-view walk cycle facing right, n frames of 44 x 72 (feet at y 69);
                                       the runtime flips Konrad (he walks west)
  square_walker_sheet(kind)       r6   tiny walker seen from behind, 4 frames, 11 x 18 (konrad) / 11 x 16 (alexei)
  fire_alexei_sheet()             f4   Alexei from behind against the fire, 2 frames of 190 x 230 at F4_ALEXEI_AT
  crawl_sheet()                   e2   Konrad out of the coal hatch: to the shoulders, to the waist, on hands and
                                       knees (two steps); 4 frames of 420 x 220 at E2_KONRAD_AT
  chute_file_sheet()              e1   Konrad's sooty hands shoving the tied file up the chute; 2 frames (rest /
                                       shove), bottom-centre anchored by the runtime at (320, 334 - lift)
  doorway_figure(i, door_rect)    f2   the man in the porter's cap in the lit doorway (i 0) / half through (i 1),
                                       backlit, never a face: RGBA of the door sprite's size, transparent elsewhere
  window_listener(kind, size)     r1   a man at his radio behind a lit hotel window (head, shoulders, the arm to
                                       the set), lit by the dial
Extras for the places (call them, place the result yourself):
  person_sheet(kind, variant, action, height, ...)   any townsperson: kind guest | woman | porter | worker | fireman,
                                       action stand | walk | run | look_up | point | carry | hose | shovel; facing
                                       0 (toward the camera) .. 90 (walks right) .. 180 (away); n frames side by side,
                                       feet at the bottom row - 2
  hotel_guests(), onlookers(), firemen(), quay_crowd(), travellers()   ready-made groups (list of sheets + anchors
                                       relative to a ground point, documented in each function)
Everything deterministic; renders memoised on disk (ASHES_NO_CACHE=1 disables).
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
import env_c3p2_cine_body as B   # noqa: E402

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]

U = 395.0          # a man's height in body units


def _cache(tag, key, fn):
    import tempfile
    h = hashlib.sha1((B._src_key() + _SRC + repr((tag, key))).encode('utf-8')).hexdigest()[:20]
    d = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
    os.makedirs(d, exist_ok=True)
    pth = os.path.join(d, 'people_' + tag + '_' + h + '.npz')
    if os.environ.get('ASHES_NO_CACHE') != '1' and os.path.exists(pth):
        return np.load(pth)['rgba']
    out = fn()
    if os.environ.get('ASHES_NO_CACHE') != '1':
        np.savez(pth, rgba=out)
    return out


def _sheet(frames):
    return np.concatenate(frames, axis=1)


LOOKS = {
    # light directions in view space (x right, y down, z toward the viewer)
    'night': dict(key=(0.35, -0.60, 0.70), rim=(-0.80, -0.30, -0.50), ambient=0.09, wrap=0.15, bg='berlin',
                  glow=(0.8, 0.2), fill=0.10, fill_dir=(0.0, -0.8, 0.6), ao=0.5),
    'lantern': dict(key=(0.10, -0.85, 0.50), rim=(-0.80, -0.30, -0.50), ambient=0.09, wrap=0.15, bg='berlin',
                    glow=(0.8, 0.2), fill=0.12, fill_dir=(0.0, -0.6, 0.8), ao=0.5),
    'fire_back': dict(key=(0.05, -0.35, -0.94), rim=(0.0, -0.6, -0.8), ambient=0.035, wrap=0.34, bg='berlin',
                      glow=(0.8, 0.2), fill=0.025, fill_dir=(0.0, -0.8, 0.6), ao=0.5),
    'fire_left': dict(key=(-0.85, -0.25, -0.45), rim=(0.60, -0.40, -0.60), ambient=0.08, wrap=0.20, bg='berlin',
                      glow=(0.8, 0.2), fill=0.10, fill_dir=(0.3, -0.8, 0.5), ao=0.5),
    'fire_front': dict(key=(0.25, -0.30, 0.92), rim=(-0.70, -0.40, -0.60), ambient=0.07, wrap=0.15, bg='berlin',
                       glow=(0.8, 0.2), fill=0.08, fill_dir=(0.0, -0.8, 0.6), ao=0.5),
    'door_back': dict(key=(0.10, -0.20, -0.97), rim=(0.0, -0.5, -0.85), ambient=0.04, wrap=0.10, bg='berlin',
                      glow=(0.8, 0.2), fill=0.03, fill_dir=(0.0, -0.8, 0.6), ao=0.5),
    'yard': dict(key=(0.60, -0.70, 0.40), rim=(-0.70, -0.40, -0.60), ambient=0.09, wrap=0.15, bg='berlin',
                 glow=(0.8, 0.2), fill=0.10, fill_dir=(0.0, 0.85, 0.5), ao=0.5),
}


def person(ch, pose, size, origin, yaw, elev, scale, light='night', look='night', hide=(), eyes=True, key=None,
           styles_=None, ss=3):
    lk = LOOKS[look] if isinstance(look, str) else look
    return _cache('person', key or (repr(sorted(ch.items())), repr(pose)), lambda: B.render(
        ch, pose, size, origin, yaw=yaw, elev=elev, scale=scale, light=light, look=lk, hide=hide, eyes=eyes,
        styles_=styles_, ss=ss)) if key is not None else B.render(
        ch, pose, size, origin, yaw=yaw, elev=elev, scale=scale, light=light, look=lk, hide=hide, eyes=eyes,
        styles_=styles_, ss=ss)


# =============================================================================================== h2 quay walkers
def quay_walk_sheet(kind, n=6):
    """LS_C3_Halves h2: side-view walk cycle facing right (the runtime flips Konrad), n frames of 44 x 72, feet on
    row 69 (the runtime puts the sprite's top-left at (x, prom_y - 70)).  Lantern light from above, the fire's
    glow from the west as a warm rim on the back, cold night fill."""
    ch = B.KONRAD if kind == 'konrad' else B.ALEXEI
    fw, fh = 44, 72
    scale = 64.0 / U
    frames = []
    for i in range(n):
        ph = i / float(n)

        def fn(ph=ph):
            pose = B.walk(ph, stride=0.95, arm_swing=1.0, lean=5.0)
            lk = dict(LOOKS['lantern'])
            lk['rim'] = (-0.85, -0.20, -0.45)
            return B.render(ch, pose, (fw, fh), (fw / 2.0, fh - 3.0), yaw=90.0, elev=6.0, scale=scale,
                            light='night', look=lk, eyes=True)
        frames.append(_cache('qwalk', (kind, i, n), fn))
    return _sheet(frames)


# =============================================================================================== r6 square walkers
def square_walker_sheet(kind):
    """LS_C3_Radio r6: a tiny man walking away from the camera across the night square (seen from behind and
    above), 4 frames; 11 x 18 (Konrad, hat) / 11 x 16 (Alexei, ushanka); lamp light from the side."""
    ch = B.KONRAD if kind == 'konrad' else B.ALEXEI
    hgt = 15 if kind == 'konrad' else 13
    fw, fh = 11, hgt + 3
    scale = (hgt + 0.5) / U
    frames = []
    for i in range(4):
        def fn(i=i):
            pose = B.walk(i / 4.0, stride=1.0, arm_swing=0.8, lean=4.0)
            return B.render(ch, pose, (fw, fh), (fw / 2.0, fh - 1.0), yaw=180.0, elev=18.0, scale=scale,
                            light='lamp', look=LOOKS['yard'], eyes=False, ss=4)
        frames.append(_cache('sqwalk', (kind, i), fn))
    return _sheet(frames)


# =============================================================================================== f4 Alexei vs fire
F4_ALEXEI_AT = (54, 112)


def fire_alexei_sheet():
    """LS_C3_Fire f4: Alexei from behind at the near side of the sorting table, the burning cabinets beyond: a dark
    figure with the fire rimming the ushanka, the shoulders and the quilted sleeves; frame 1 turns the head a
    little toward the fire's front.  2 frames of 190 x 230, top-left at F4_ALEXEI_AT."""
    ch = dict(B.ALEXEI, collar='fur')
    w, h = 190, 230
    frames = []
    for fr in range(2):
        def fn(fr=fr):
            pose = B.stand(spine=(4.0, 6.0, 0.0), head=(-8.0 - 14.0 * fr, -2.0 + 2.0 * fr, 0.0),
                           arm_l=dict(fk=(10.0, 10.0, 34.0, 20.0), hand=dict(curl=0.7, grip=0.4)),
                           arm_r=dict(fk=(18.0, 12.0, 46.0, 10.0), hand=dict(curl=0.75, grip=0.5)))
            out = B.render(ch, pose, (w, h), (98.0, 486.0), yaw=176.0, elev=4.0, scale=1.12,
                           light='fire', look=LOOKS['fire_back'], eyes=False)
            return back_rim(out, FIRE_RIM, width=3, top=1.0, side=0.95, seed=fr)
        frames.append(_cache('f4alexei', fr, fn))
    return _sheet(frames)


FIRE_RIM = ['#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']
LAMP_RIM = ['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777']


def back_rim(img, ramp, width=2, top=1.0, side=0.7, seed=0, left=None, right=None, fall_off=True):
    """A light behind the figure (fire, a lit doorway) eats into its outline: the outer silhouette pixels take the
    light's colour, strongest on the top (head, shoulders), weaker on the flanks, fading inward over `width` px,
    broken by an ordered dither so it reads as glow, not as a drawn line.  left / right override `side` for a light
    from one side (the burning wing at the left of the quay bench)."""
    wl = side if left is None else left
    wr = side if right is None else right
    out = img.copy()
    a = out[..., 3] > 0
    h, w = a.shape
    if not a.any():
        return out
    cols = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)] for c in ramp], np.uint8)
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
    yy, xx = np.mgrid[0:h, 0:w]
    th = bay[(yy + seed) % 4, xx % 4]
    # the light is high (a burning wing, a stairwell lamp): the rim is full on the head and the shoulders and dies
    # away toward the feet
    ys = np.nonzero(a.any(axis=1))[0]
    y_top, y_bot = ys.min(), ys.max()
    fall = np.clip(1.0 - (yy - y_top) / max(1.0, float(y_bot - y_top)) * 1.05, 0.12, 1.0) if fall_off else 1.0
    pad = np.pad(a, width + 1, constant_values=False)
    for k in range(1, width + 1):
        up = ~pad[width + 1 - k:width + 1 - k + h, width + 1:width + 1 + w]
        lf = ~pad[width + 1:width + 1 + h, width + 1 - k:width + 1 - k + w]
        rt = ~pad[width + 1:width + 1 + h, width + 1 + k:width + 1 + k + w]
        strength = np.maximum(up * top, np.maximum(lf * wl, rt * wr) * fall) * (1.0 - (k - 1) / float(width))
        sel = a & (strength > 0.1) & (th < strength * (0.95 if k == 1 else 0.6))
        idx = np.clip(np.round(strength * (len(cols) - 1)).astype(int) - (k - 1), 0, len(cols) - 1)
        out[sel, :3] = cols[idx[sel]]
        a_done = sel
        a = a & ~a_done
    return out


# =============================================================================================== f2 doorway figure
def doorway_figure(i, door_rect, pad=(4, 2, 4, 2)):
    """LS_C3_Fire f2: the man in the long coat and porter's cap in the lit doorway at the end of the aisle, seen from
    behind against the stairwell light (never a face).  i 0 = in the doorway, 1 = half through (the right part of
    him already past the jamb), 2/3 = nobody.  door_rect = (x0, y0, x1, y1) of the opening; the result has the size
    of the door sprite ((x1 - x0) + pad[0] + pad[2], (y1 - y0) + pad[1] + pad[3]) and is transparent around him."""
    x0, y0, x1, y1 = door_rect
    w, h = int(x1 - x0 + pad[0] + pad[2]), int(y1 - y0 + pad[1] + pad[3])
    if i >= 2:
        return np.zeros((h, w, 4), np.uint8)
    ch = B.townsperson('porter')
    ch = dict(ch, hem=128.0, coat_bulk=4.6, buttons=False, collar='turned')
    hgt = (y1 - y0) * 0.86
    scale = hgt / U

    def fn():
        pose = B.walk(0.18 if i == 0 else 0.42, stride=0.7, arm_swing=0.6, lean=6.0, head=(28.0, 6.0, 0.0))
        out = B.render(ch, pose, (w, h), (w / 2.0 + (0 if i == 0 else 9), h - pad[3] - 1.0), yaw=192.0, elev=2.0,
                       scale=scale, light='lamp', look=LOOKS['door_back'], eyes=False, ss=4)
        out = back_rim(out, LAMP_RIM, width=1, top=0.8, side=0.9, seed=i)
        if i == 1:
            cut = int(pad[0] + (x1 - x0) * 0.55)
            out[:, :cut] = 0
        return out
    return _cache('door', (i, tuple(door_rect), pad), fn)


# =============================================================================================== r1 window listener
def window_listener(kind, size=(14, 16), light='dial'):
    """LS_C3_Radio r1: the man at his radio behind his lit window, seen from the square (front-ish, from below):
    head and shoulders, one arm toward the set; for a window opening of `size` px (transparent around him)."""
    ch = dict(B.KONRAD if kind == 'konrad' else B.ALEXEI)
    ch.update(hat=None, scarf=False, bag=None, strap=None)
    if kind == 'alexei':
        ch.update(coat='sweater', coat_mat='knit', coat_bulk=2.0, sleeve=2.2, collar=None, quilt=None, hem=0.0)
    else:
        ch.update(coat='jacket', coat_mat='jacket', coat_bulk=2.6, sleeve=2.6, collar='suit', collar_mat='jacket',
                  hem=26.0, cuff='shirt')
    w, h = size
    # the head about a third of the window high, the shoulders across most of its width, the sill hides the rest
    scale = 0.30 * h / 52.0
    lk = dict(key=(0.15, 0.55, 0.82), rim=(0.0, -0.7, -0.7), ambient=0.07, wrap=0.2, bg='berlin',
              glow=(0.8, 0.2), fill=0.06, fill_dir=(0.0, -0.8, 0.6), ao=0.5)

    def fn():
        pose = B.stand(spine=(0.0, 10.0, 0.0), head=(0.0, 10.0, 0.0),
                       arm_l=dict(fk=(50.0, 10.0, 70.0)), arm_r=dict(fk=(50.0, 10.0, 70.0)))
        yaw = 22.0 if kind == 'konrad' else -22.0
        return B.render(ch, pose, (w, h), (w / 2.0, 0.30 * h + 392.0 * scale), yaw=yaw, elev=-6.0, scale=scale,
                        light=light, look=lk, eyes=False, ss=4)
    return _cache('window', (kind, tuple(size), light), fn)


# =============================================================================================== generic extras
ACTIONS = ('stand', 'walk', 'run', 'look_up', 'point', 'carry', 'hose', 'shovel', 'huddle')


def action_pose(action, ph=0.0, variant=0):
    """Pose of an extra (the rig's +z is where he faces)."""
    if action == 'walk':
        return B.walk(ph, stride=0.9 + 0.1 * (variant % 2), arm_swing=0.9)
    if action == 'run':
        p = B.walk(ph, stride=1.35, arm_swing=1.6, lean=14.0)
        return p
    if action == 'look_up':
        return B.stand(head=(6.0 * math.sin(ph * 2 * math.pi), -24.0, 0.0), spine=(0.0, -4.0, 0.0),
                       arm_l=dict(fk=(8.0, 10.0, 70.0, 30.0), hand=dict(curl=0.6)),
                       arm_r=dict(fk=(8.0, 10.0, 70.0, 30.0), hand=dict(curl=0.6)))
    if action == 'point':
        return B.stand(head=(0.0, -10.0, 0.0), arm_r=dict(fk=(120.0 + 6 * math.sin(ph * 6.28), 22.0, 6.0),
                                                           hand=dict(curl=0.3, spread=0.0)))
    if action == 'carry':
        p = B.walk(ph, stride=0.8, arm_swing=0.2)
        p['arm_l'] = dict(fk=(38.0, 12.0, 70.0, 30.0), hand=dict(curl=0.8, grip=0.6))
        p['arm_r'] = dict(fk=(38.0, 12.0, 70.0, 30.0), hand=dict(curl=0.8, grip=0.6))
        return p
    if action == 'hose':
        bob = 3.0 * math.sin(ph * 2 * math.pi)
        return B.stand(spine=(0.0, 18.0, 0.0), head=(0.0, -12.0, 0.0),
                       arm_l=dict(fk=(70.0 + bob, 14.0, 30.0), hand=dict(curl=0.8, grip=0.7)),
                       arm_r=dict(fk=(40.0 + bob, 10.0, 70.0), hand=dict(curl=0.8, grip=0.7)),
                       leg_l=dict(fk=(22.0, 8.0, 18.0)), leg_r=dict(fk=(-14.0, 6.0, 8.0)))
    if action == 'shovel':
        s = math.sin(ph * 2 * math.pi)
        p = B.stand(spine=(0.0, 30.0 + 12.0 * s, 0.0), head=(0.0, -20.0, 0.0),
                    leg_l=dict(fk=(26.0, 8.0, 30.0)), leg_r=dict(fk=(-10.0, 6.0, 12.0)))
        tmp = B.Rig(p)
        # the right hand at the hip on the end of the shaft, the left hand low and forward, the blade in the snow
        p['arm_r'] = dict(wrist=tmp.pelvis((-14.0, -18.0 + 6.0 * s, 26.0)), pole=(-0.8, 0.2, -0.6),
                          hand=dict(curl=0.85, grip=0.8))
        p['arm_l'] = dict(wrist=tmp.pelvis((6.0, 34.0 + 10.0 * s, 74.0)), pole=(0.8, 0.0, -0.6),
                          hand=dict(curl=0.85, grip=0.8))
        return p
    if action == 'huddle':
        return B.stand(spine=(0.0, 12.0, 0.0), head=(0.0, 10.0, 0.0),
                       arm_l=dict(fk=(34.0, -6.0, 100.0, 40.0), hand=dict(curl=0.8)),
                       arm_r=dict(fk=(34.0, -6.0, 100.0, 40.0), hand=dict(curl=0.8)))
    sway = 1.5 * math.sin(ph * 2 * math.pi)
    return B.stand(spine=(0.0, 2.0 + sway * 0.5, 0.0), head=(sway * 3, 0.0, 0.0))


def person_sheet(kind, variant=0, action='stand', height=40, facing=20.0, light='night', look='night', n=1,
                 elev=6.0, eyes=True, extra=None, rim=None):
    """A townsperson as an n-frame sheet (frames side by side), `height` px tall (a man's height; women 0.93),
    feet on row h - 2, centred.  kind: guest | woman | porter | worker | fireman (variant changes head, hat, coat);
    action: stand | walk | run | look_up | point | carry | hose | shovel | huddle; facing: 0 = toward the camera,
    90 = to the right, 180 = away, -90 = to the left.  light: a body.LIGHTS preset (night, lamp, yard, fire, dawn);
    look: a LOOKS preset or a Look dict.  extra: dict of outfit overrides (e.g. coat colour via 'albedo').
    rim: a colour ramp (e.g. FIRE_RIM) for a light behind the figure eating into its outline (backlit crowds)."""
    ch = B.townsperson(kind if kind != 'guest' else 'man', variant)
    alb = None
    if extra:
        ch = dict(ch)
        alb = extra.get('albedo')
        ch.update({k: v for k, v in extra.items() if k != 'albedo'})
    f = 0.93 if ch.get('female') else 1.0
    scale = height * f / U
    wide = 0.95 if action in ('shovel', 'hose', 'point', 'carry', 'run') else 0.62
    w = int(max(9, round(height * wide))) | 1
    h = int(round(height * 1.08)) + 3
    st = B.styles(ch['id'], light, overrides=_variant_albedo(kind, variant, alb))
    frames = []
    for i in range(n):
        ph = i / float(max(1, n))

        def fn(ph=ph, i=i):
            pose = action_pose(action, ph, variant)
            out = B.render(ch, pose, (w, h), (w / 2.0, h - 2.0), yaw=facing, elev=elev, scale=scale, light=light,
                           look=LOOKS[look] if isinstance(look, str) else look, eyes=eyes, styles_=st,
                           ss=4 if height < 30 else 3, extra_nodes=_props(action, kind))
            if rim:
                out = back_rim(out, rim, width=1, top=1.0, side=0.8, seed=i)
            return out
        frames.append(_cache('ps', (kind, variant, action, height, facing, light, repr(look), n, i, elev, eyes,
                                    repr(extra), repr(rim)), fn))
    return _sheet(frames)


def _props(action, kind):
    """Props held by an extra, built from the posed rig (scene coordinates)."""
    S = B.S

    def shovel(M, rig):
        a, b_ = rig.arm['arm_r']['wr'], rig.arm['arm_l']['wr']
        d = B._n(b_ - a)
        top = a - d * 14.0
        tip = b_ + d * max(10.0, (0.0 - b_[1]) / max(0.2, d[1]) * 0.9) if d[1] > 0.1 else b_ + d * 110.0
        blade_c = tip + d * 10.0
        return S.Union([B.RC(tuple(top), tuple(tip), 2.0, 2.0, M('wood')),
                        S.RoundBox(tuple(blade_c), (12.0, 9.0, 1.6), 1.0, M('iron'))], k=1.0)

    def hose(M, rig):
        a, b_ = rig.arm['arm_l']['wr'], rig.arm['arm_r']['wr']
        d = B._n(a - b_)
        nozzle = a + d * 34.0
        back = b_ - d * 40.0
        ground = np.array([back[0], -4.0, back[2] - 30.0])
        return S.Union([B.RC(tuple(b_ - d * 6.0), tuple(nozzle), 4.2, 3.0, M('hose')),
                        B.RC(tuple(nozzle), tuple(nozzle + d * 8.0), 2.6, 2.0, M('brass')),
                        B.RC(tuple(b_ - d * 6.0), tuple(back), 4.2, 4.2, M('hose')),
                        B.RC(tuple(back), tuple(ground), 4.2, 4.2, M('hose'))], k=2.0)

    def case(M, rig):
        w = rig.arm['arm_r']['wr']
        c = w + np.array([0.0, 30.0, 0.0])
        return S.Union([S.RoundBox(tuple(c), (6.0, 22.0, 30.0), 2.5, M('case')),
                        B.RC(tuple(w + np.array([0.0, 4.0, -6.0])), tuple(w + np.array([0.0, 4.0, 6.0])), 1.6, 1.6,
                             M('case'))], k=1.0)

    def ladder(M, rig):
        a, b_ = rig.arm['arm_l']['wr'], rig.arm['arm_r']['wr']
        m = (a + b_) / 2.0
        fwd = np.array([0.0, 0.0, 1.0])
        return S.Union([B.RC(tuple(m - fwd * 60.0 + np.array([x, 0, 0])), tuple(m + fwd * 140.0 + np.array([x, -6.0, 0])),
                             2.2, 2.2, M('wood')) for x in (-14.0, 14.0)] +
                       [B.RC(tuple(m + fwd * z + np.array([-14.0, -z * 0.03, 0])), tuple(m + fwd * z + np.array([14.0, -z * 0.03, 0])),
                             1.6, 1.6, M('wood')) for z in (-40.0, 0.0, 40.0, 80.0, 120.0)], k=0.5)
    if action == 'shovel':
        return [shovel]
    if action == 'hose':
        return [hose]
    if action == 'carry':
        return [ladder] if kind == 'fireman' else [case]
    return None


COATS = ['#3a3a40', '#4a3a30', '#2e3446', '#3e4436', '#5a4a3e', '#2a2a2e', '#4e4048', '#3a4048']
SCARVES = ['#7a3a34', '#5a6a7a', '#8a7a4a', '#4a5a3a', '#6a4a6a']


def _variant_albedo(kind, variant, alb=None):
    o = {}
    if kind in ('guest', 'woman', 'worker'):
        o['coat'] = COATS[(variant * 3 + (1 if kind == 'woman' else 0)) % len(COATS)]
        o['scarf'] = SCARVES[variant % len(SCARVES)]
        o['felt'] = ['#3a3438', '#4a4440', '#2a2830', '#5a4a40'][variant % 4]
        o['brim'] = o['felt']
        o['kerchief'] = ['#6a3a34', '#3a4a6a', '#6a5a3a', '#4a3a4a'][variant % 4]
    if kind == 'fireman':
        o['fjacket'] = ['#2e2c2a', '#26282c', '#302a26'][variant % 3]
    if alb:
        o.update(alb)
    return o


# ------------------------------------------------------------------------------------------------ groups
def hotel_guests(height=26, light='lamp'):
    """LS_C3_Radio r1/r6 (the station square): a porter with his cap (stand, facing the camera), a couple in
    overcoats walking toward the hotels (walk cycles, 6 frames), a late guest in a homburg (stand).
    -> list of dict(sheet, n, fps, kind) -- the places builder chooses the anchors."""
    return [dict(kind='porter', n=1, fps=0, sheet=person_sheet('porter', 0, 'stand', height, 15.0, light, 'yard')),
            dict(kind='guest_walk', n=6, fps=8, sheet=person_sheet('guest', 1, 'walk', height, 90.0, light, 'yard', 6)),
            dict(kind='woman_walk', n=6, fps=8,
                 sheet=person_sheet('woman', 0, 'walk', height, 90.0, light, 'yard', 6)),
            dict(kind='guest_stand', n=1, fps=0, sheet=person_sheet('guest', 2, 'stand', height, -25.0, light, 'yard'))]


def onlookers(height=22, light='fire', n=4):
    """LS_C3_Escape e4 / LS_C3_Halves h3: people in the lane looking up at the burning wing (faces lit from the
    front by the fire), one pointing, one with hands over the mouth (huddle).  -> list of dict(sheet, n, fps)."""
    out = []
    specs = [('guest', 3, 'look_up'), ('woman', 1, 'huddle'), ('worker', 0, 'point'), ('guest', 0, 'look_up'),
             ('woman', 0, 'look_up'), ('worker', 1, 'stand')]
    for k in range(n):
        kind, v, act = specs[k % len(specs)]
        # they face the burning wing (away from us): their backs dark, the fire eating into their outlines
        out.append(dict(kind=kind + '_' + act, n=2, fps=2,
                        sheet=person_sheet(kind, v + k // len(specs), act, height, 160.0 + (k % 3) * 15.0, light,
                                           'fire_back', 2, eyes=False, rim=FIRE_RIM)))
    return out


def firemen(height=26, light='fire'):
    """LS_C3_Escape e4: the fire brigade arriving -- two firemen running (helmets, belted jackets, boots;
    6-frame run cycles facing right), one at the hose (2 frames), one carrying a ladder end (carry, 6 frames)."""
    return [dict(kind='run', n=6, fps=12, sheet=person_sheet('fireman', 0, 'run', height, 90.0, light, 'fire_left', 6,
                                                             eyes=False, rim=FIRE_RIM)),
            dict(kind='run2', n=6, fps=12, sheet=person_sheet('fireman', 1, 'run', height, 90.0, light, 'fire_left', 6,
                                                              eyes=False, rim=FIRE_RIM)),
            dict(kind='hose', n=2, fps=3, sheet=person_sheet('fireman', 2, 'hose', height, 150.0, light, 'fire_back', 2,
                                                             eyes=False, rim=FIRE_RIM)),
            dict(kind='carry', n=6, fps=10, sheet=person_sheet('fireman', 0, 'carry', height, 90.0, light, 'fire_left', 6,
                                                               eyes=False, rim=FIRE_RIM))]


def quay_crowd(height=18, light='night'):
    """LS_C3_Halves h2/h3: far figures on the quay and the bridge -- a patrol pair standing, a woman walking with
    a bag, a man shovelling snow, a figure huddled at the balustrade."""
    return [dict(kind='walk', n=6, fps=8, sheet=person_sheet('woman', 1, 'walk', height, 90.0, light, 'lantern', 6, eyes=False)),
            dict(kind='shovel', n=4, fps=4, sheet=person_sheet('worker', 1, 'shovel', height, 70.0, light, 'lantern', 4, eyes=False)),
            dict(kind='huddle', n=1, fps=0, sheet=person_sheet('guest', 3, 'huddle', height, 160.0, light, 'lantern', 1, eyes=False)),
            dict(kind='stand', n=2, fps=1, sheet=person_sheet('porter', 1, 'stand', height, 20.0, light, 'lantern', 2, eyes=False))]


def travellers(height=34, light='dawn'):
    """LS_C3_Halves h4 (under the departures board): travellers with luggage and a railwayman, early morning."""
    return [dict(kind='walk', n=6, fps=8, sheet=person_sheet('guest', 0, 'carry', height, 90.0, light, 'night', 6)),
            dict(kind='woman', n=6, fps=8, sheet=person_sheet('woman', 1, 'walk', height, -90.0, light, 'night', 6)),
            dict(kind='porter', n=2, fps=1, sheet=person_sheet('porter', 0, 'stand', height, 10.0, light, 'night', 2)),
            dict(kind='look_up', n=2, fps=1, sheet=person_sheet('guest', 2, 'look_up', height, 170.0, light, 'night', 2))]
