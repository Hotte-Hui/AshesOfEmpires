"""env_c4_cine_bust -- whole upper bodies with the faces of the dialogue busts (owner: c4 figure stream, round 10).

The portrait pipeline (chargen_portrait2: head sculpt, hats, hair, garments; chargen_portrait2_face: the
hand-designed eyes, brows, mouths; imported read-only) is re-posed on a cinematic canvas and given the anatomical
arms and hands of env_c4_cine_anat, so a figure in a film is the person of the dialogue box -- same face, same coat
-- with real shoulders, elbows, wrists and fingers:

  figure(spec, size, zoom, head_px, torso_px, ...)   one traced + painted figure: head (+ features when `expr`),
                                                     trunk down to the hips, coat layers, extra nodes (arms, props)
                                                     built in canvas space, optional clip / cast shadow
  fengler_counter(...)                               LS_C4_Stamp s3b: Registrator Fengler bent over the counter
  konrad_back_wave(f, size)                          LS_C4_Voices v2: Konrad from behind, the right arm down /
                                                     rising / raised to Ilse
Canvas coordinates: x right, y down (px), z towards the viewer; the bust's own scene is scaled about (56, 56, 0) by
`zoom` exactly as the portraits are, so every feature helper of the portrait pipeline finds its landmarks.
Deterministic; memoised on disk like env_c4_cine_anat.paint.
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_anat as A   # noqa: E402
import chargen_portrait2_cast as CC  # noqa: E402
import chargen_portrait2_paint as P  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402
import env_c4_cine_anat as N         # noqa: E402
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402

E = S.Ellipsoid
RC = S.RoundCone
C0 = np.array([56.0, 56.0, 0.0])
_memo: dict = {}


def _pre(p, zoom):
    p = np.asarray(p, float)
    if p.size == 2:
        p = np.array([p[0], p[1], 0.0])
    return (p - C0) / zoom + C0


def _post(p, zoom):
    return C0 + (np.asarray(p, float) - C0) * zoom


class Ctx:
    """Frames of a posed figure: torso / head local -> canvas."""

    def __init__(self, zoom, hf, tf, hp, lm):
        self.zoom, self.hf, self.tf, self.hp, self.lm = zoom, hf, tf, hp, lm

    def t2v(self, p):
        return _post(self.tf.to_view(np.asarray(p, float)), self.zoom)

    def h2v(self, p):
        return _post(self.hf.to_view(np.asarray(p, float)), self.zoom)

    def tdir(self, v):
        return N.nrm(self.tf.dir_to_view(np.asarray(v, float)))


def trunk(M, mat='body', width=1.0, depth=1.0, slope=1.0, lean=0.0, hips=True):
    """Shoulders + chest of the bust (chargen_portrait2_anat.build_torso) continued down over the belly to the hips
    (torso-local: origin = the pit of the neck, y down, z forward) -- the figure has no arms here (they are built
    by env_c4_cine_anat.arm in canvas space)."""
    m = M(mat)
    base = A.build_torso(M, mat, width, depth, slope)
    parts = [base, E((0.0, 52.0, -1.0 + lean), (24.0 * width, 26.0, 13.0 * depth), m)]
    if hips:
        parts.append(E((0.0, 78.0, 0.0 + lean * 1.4), (23.5 * width, 18.0, 13.5 * depth), m))
    return S.Union(parts, k=6.0)


def coat_closed(M, torso_node, mat='coat', y_from=26.0, t=2.7, skirt=0.0):
    """The coat buttoned below the chest (the portrait's coat_layers opens a V that keeps widening down a long
    trunk) and, with skirt > 0, the coat's skirt hanging `skirt` units below the hips (a figure cut at the thighs
    by the frame edge, never at a rounded trunk end)."""
    m = M(mat)
    shell = S.Inter(S.Offset(torso_node, t, m), S.Fn(lambda P, y0=y_from: (y0 - P[:, 1]).astype(np.float32), m))
    parts = [shell]
    if skirt > 0:
        parts.append(S.RoundCone((0.0, 80.0, 0.0), (0.0, 80.0 + skirt, -1.0), 26.5, 29.0, m))
    return S.Union(parts, k=2.0)


def figure(spec, size, zoom, head_px, torso_px, yaw, pitch=0.0, roll=0.0, torso_yaw=0.0, torso_pitch=0.0,
           look=None, torso_kw=None, head_items=None, torso_items=None, styles=None, tone_passes=None, extra=None,
           expr=None, clip=None, shadow=None, cache_key=None, head_over=None, groups=None, rgb_passes=None,
           blink=False, cut=None):
    """Trace + paint one figure -> RGBA.  head_px / torso_px: canvas positions of the head centre and the pit of
    the neck; extra(M, ctx) -> list of nodes in canvas space (arms, props); expr: draw the face (portrait features
    for that expression); clip(out, d, M, ctx) -> out (hide what lies behind a counter ...); cut = a node in
    canvas space removed from the whole scene BEFORE tracing (a counter, a desk: what it hides is not there, so a
    hidden trunk can never punch a hole into an arm in front of it); shadow: see env_c4_cine_anat.paint."""
    key = None
    if cache_key is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        hk = hashlib.sha1((N._src_key() + _own_src() + repr((cache_key, size, zoom, head_px, torso_px, yaw, pitch,
                                                                roll, torso_yaw, torso_pitch, look, torso_kw,
                                                                expr, blink, shadow is None))).encode('utf-8')).hexdigest()[:22]
        key = N._cache_path('c4b_' + hk)
        if key in _memo:
            return _memo[key].copy()
        if os.path.exists(key):
            out = np.load(key)['rgba']
            _memo[key] = out
            return out.copy()
    import chargen_portrait2 as CP
    import chargen_portrait2_face as FC
    w, h = size
    M = A.Mats()
    for nm in spec.get('mat_order', ()):
        M(nm)
    hpd = dict(spec['head'])
    if head_over:
        hpd.update(head_over)
    hp = A.head_params(**hpd)
    head, lm = A.build_head(hp, M, jaw_open=0.0)
    items, clips, solid = [], [], []
    for f in (head_items if head_items is not None else spec['head_items']):
        r = f(M, hp)
        if isinstance(r, dict):
            solid.append(r['node'])
            if r.get('clip') is not None:
                clips.append(r['clip'])
            if r.get('soft') is not None:
                items.append(r['soft'])
        else:
            items.append(r)
    body = S.Union([head] + items)
    for c in clips:
        body = S.Inter(body, c)
    hpos = _pre(head_px, zoom)
    tpos = _pre(torso_px, zoom)
    hf = S.Frame(hpos, S.rot(yaw, pitch, roll))
    tf = S.Frame(tpos, S.rot(torso_yaw, torso_pitch, 0.0))
    tk = dict(torso_kw or {})
    torso = trunk(M, 'body', **tk)
    t_items = [f(M, torso) for f in (torso_items if torso_items is not None else spec['torso_items'])]
    hnode = S.Bound(S.Xform(S.Union([body] + solid), frame=hf), hpos + np.array([0, -7.0, 0]), 50.0, margin=3.0)
    tnode = S.Bound(S.Xform(S.Union([torso] + t_items), frame=tf), tpos + np.array([0, 44.0, 0]), 92.0, margin=3.0)
    root = S.Scale(S.Union([hnode, tnode]), C0, zoom)
    ctx = Ctx(zoom, hf, tf, hp, lm)
    ex_nodes = list(extra(M, ctx)) if extra is not None else []
    nodes = [root] + ex_nodes
    full = S.Union(nodes, k=0.0)
    if cut is not None:
        full = S.Sub(full, cut)
        ex_nodes = [S.Sub(S.Union(ex_nodes, k=0.0), cut)] if ex_nodes else []
    lk = P.Look(**(look or spec['look']))
    g = S.trace(full, w, h, ss=3, key=lk.key, z0=200.0, zfar=-200.0, steps=150)
    pri = [spec.get('priority', {}).get(n, 0) for n in M.names]
    d = S.downsample(g, len(M), priority=pri)
    st = dict(spec['styles'])
    if styles:
        st.update(styles)
    names = M.names
    lmv = {k: CP.zoom_pt({'zoom': zoom}, hf.to_view(p)) for k, p in lm.items()}
    G = dict(d=d, M=M, hp=hp, lm=lm, lmv=lmv, hf=hf, tf=tf, look=lk, jaw=0.0, zoom=zoom)
    v, rimv, keyv = P.light_value(d, lk, st, names)
    v = P.smooth_by_material(v, d.mat, passes=spec.get('smooth', 1))
    tone = P.quantise(d, v, st, names)
    sp = dict(spec)
    sp['zoom'] = zoom
    for fn in (tone_passes if tone_passes is not None else spec.get('tone_passes', ())):
        tone = fn(sp, G, tone, v)
    tone = N.crease_lines(d, tone, v)
    cv = None
    if expr is not None:
        skin_ids = [M.names.index(n) for n in spec['skin'] if n in M.names]
        cv = FC.Canvas(tone, d.mat, skin_ids)
        CP.draw_features(sp, G, cv, expr, 'rest', blink, v)
        tone = P.clean(cv.tone, d.mat, protect=cv.locked)
    else:
        tone = P.clean(tone, d.mat)
    rgb = P.colorize(d, tone, st, names)
    rgb = P.outline(rgb, d, st, names, look=lk)
    rgb, _ = P.depth_lines(rgb, d, st, names, groups or spec['groups'], skip=spec.get('no_depth_line', ()))
    rgb = P.apply_rim(rgb, d, rimv, keyv, st, names, tone)
    if cv is not None:
        CP.paint_abs(sp, cv, rgb, v)
        for fn in (rgb_passes if rgb_passes is not None else spec.get('rgb_passes', ())):
            rgb = fn(sp, G, rgb, v, expr, 'rest')
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    if clip is not None:
        out = clip(out, d, M, ctx)
    if shadow is not None:
        caster = S.Union(ex_nodes, k=0.0) if (shadow.get('extra_only') and ex_nodes) else full
        vis = N.plane_shadow(caster, w, h, shadow['p'], shadow['n'], lk.key, k=shadow.get('k', 0.035))
        lay = N.shadow_layer(vis, out[..., 3] > 0, shadow.get('rgb', (0, 0, 0)),
                             levels=shadow.get('levels', ((0.18, 0.46), (0.45, 0.30), (0.75, 0.15))))
        if shadow.get('clip') is not None:
            lay[~shadow['clip'], 3] = 0
        empty = out[..., 3] == 0
        out[empty] = lay[empty]
    if key is not None:
        np.savez(key, rgba=out)
        _memo[key] = out
    return out.copy()


def _own_src():
    with open(os.path.abspath(__file__), 'rb') as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:12]


def shoulder(ctx, side, width=1.0, out=0.0, drop=0.0):
    """Canvas position of a shoulder joint (side -1 = the figure's right, +1 = left in torso-local x)."""
    return ctx.t2v((side * (24.5 + out) * width, 17.0 + drop, -3.0))


# ========================================================================================= Fengler
def _fengler_spec():
    import characters_c4 as C4
    return C4.registrar_portrait()


def fengler_counter(size, at, counter_y, knob, card, src):
    """Registrator Fengler bent over the counter: front view, the head bowed over the stamp (the side parting and
    the grey temples show), the hooded eyes behind rimless glasses on his work; dust coat over the dark suit,
    white collar and tie, the plain round lapel pin.  His arms are one chain each (round 10b, after the art
    director's "broken arms" note): the dust-coat sleeves go out and down from the shoulders to the elbows
    resting on the counter's far edge, the forearms in gathered black sleeve protectors turn in to the work, the
    white shirt cuffs show at the wrists; the right hand (our left) is closed round the stamp knob from above, the
    left lies flat on the card, turned in.  The counter is a plane of the canvas space and everything below its
    top in front of the far edge is cut away BEFORE tracing (his trunk can no longer hide a wrist); the arms
    and hands cast their shadow on the counter top.  size / at = canvas and its frame position; knob / card =
    frame points."""
    spec = _fengler_spec()
    ax, ay = at
    zoom = 1.15
    head_px = (184.0, 48.0)
    torso_px = (182.0, 88.0)
    knob_c = np.array([knob[0] - ax, knob[1] - ay - 2.0, 24.0])
    card_c = np.array([card[0] - ax, card[1] - ay, 30.0])
    look = dict(key=(0.18, -0.86, 0.48), rim=(-0.62, -0.42, -0.66), ambient=0.10, wrap=0.14, bg='c4_annex',
                glow=(0.6, 0.1), fill=0.10, fill_dir=(0.0, 0.3, 1.0), ao=0.5)
    sty = dict(spec['styles'])
    dust = ramp('#0c0e0e', '#191c1b', '#272b29', '#373c39', '#4a504c', '#5f6661', '#777e78', '#90968e')
    sty['coat'] = MatStyle(dust, [0.05, 0.11, 0.19, 0.30, 0.43, 0.59, 0.78], dither=0.03, rim='#8eac94')
    sty['coat_lapel'] = MatStyle(dust, [0.05, 0.11, 0.19, 0.30, 0.43, 0.59, 0.78], rim='#8eac94')
    prot = ramp('#040606', '#090c0b', '#0f1312', '#171c1a', '#212825', '#2d3632', '#3e4a44')
    sty.update({
        'prot': MatStyle(prot, [0.05, 0.12, 0.24, 0.40, 0.58, 0.78], dither=0.02, rim='#8eac94', spec=0.3),
        'arm_coat': sty['coat'],
        'cuff': sty['shirt'],
        'inside': MatStyle(ramp('#030404', '#070909', '#0c0f0e'), [0.2, 0.5], rim=None),
        'nail': MatStyle(ramp('#1a1c1c', '#3a3a3a', '#646058', '#8e8678', '#b8ae9e', '#dcd2c2'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#8eac94', spec=0.4),
    })

    # The counter top as a plane of the canvas space: its far edge is the row `cy`, it rises towards the viewer
    # (the plate shows it from above), FENGLER_ZE = how far in front of his chest the far edge lies.  Everything
    # below that top and in front of the far edge is CUT away before tracing (trunk, hips, the upper arms where
    # they go down behind the edge); the forearms and hands lie on it and throw their shadow on it.
    cy = float(counter_y - ay)
    n_top = N.nrm(COUNTER_N)
    e0 = np.array([0.0, cy, FENGLER_ZE])
    slope = -n_top[1] / n_top[2]

    def on_top(x, y, h=0.0):
        """The canvas point seen at (x, y) that lies h px above the counter top (along its normal)."""
        yb = y - n_top[1] * h
        return np.array([x, yb, FENGLER_ZE + slope * (yb - cy)]) + n_top * h

    def wedge(P):
        return np.maximum(F32(cy) - P[:, 1], (P - e0.astype(F32)) @ n_top.astype(F32))

    s = FENGLER_S

    def arms(M, ctx):
        nodes = []
        for side in (-1.0, 1.0):                    # -1: his right arm (canvas left, the stamp), +1: his left
            sh = shoulder(ctx, side, 1.10, out=1.5)
            ex, ey, eh = FENGLER_ELBOW
            el = on_top(sh[0] + side * ex, cy + ey, eh)
            if side < 0:
                # the right hand closed round the stamp knob from above: the palm on the knob, the fingers round
                # its far side, the thumb round the near side, the back of the hand up; the wrist a little flexed
                kx, ky = knob_c[0], knob_c[1] - 4.0
                target = on_top(kx, ky, FENGLER_KNOB_H)
                hk = dict(side=1.0, flex='grip', spread=1.5, thumb='wrap', nail='nail')
                wr, hy, hz = N.reach(el, target, (0.0, 0.62 * s, -0.24 * s), n_top, flexion=16.0, deviation=6.0,
                                     side=1.0)
            else:
                # the left hand lies on the card: palm down, fingers a little curled, towards the viewer and in
                target = on_top(card_c[0] + FENGLER_CARD_DX, card_c[1] - 17.0, 0.17 * s)
                hk = dict(side=-1.0, flex='rest', spread=4.0, thumb='rest', nail='nail')
                wr, hy, hz = N.reach(el, target, (0.0, 0.50 * s, -0.14 * s), n_top, flexion=-14.0,
                                     deviation=-16.0, side=-1.0)
            fd = N.nrm(wr - el)
            nodes.append(N.arm(M, 'arm_coat', 'skin', sh, el, wr, (12.6, 11.2, 9.4), hy, hz, s, cover=0.46,
                               cuff='cuff', cuff_len=0.18 * s, sleeve_in='inside', hand_kw=hk, folds=True))
            L = float(np.linalg.norm(wr - el))
            nodes.append(N.cloth_tube(M, 'prot', el + fd * L * 0.14, wr - fd * (0.40 * s), 12.0, 10.4,
                                      puff=0.10, gather=0.84, folds=6, fold_amp=0.07, seed=int(side + 2)))
        return nodes

    head_items = list(spec['head_items'])
    cyy = np.arange(size[1])[:, None] + ay
    cmask = np.broadcast_to(cyy > counter_y + 1, (size[1], size[0]))
    return figure(spec, size, zoom, head_px, torso_px, yaw=6.0, pitch=17.0, roll=-2.0, torso_yaw=4.0,
                  torso_pitch=FENGLER_LEAN, look=look, torso_kw=dict(width=1.12, depth=1.08, slope=1.0, lean=2.0),
                  head_items=head_items, styles=sty, extra=arms, expr='neutral', blink=True,
                  cut=S.Fn(wedge, 0),
                  tone_passes=list(spec.get('tone_passes', ())) + [N.pass_contact((('arm_coat', 'coat'),
                                                                                   ('prot', 'arm_coat')), (1, 1))],
                  shadow=dict(p=tuple(e0), n=tuple(n_top), rgb=(14, 22, 18), clip=cmask, extra_only=True),
                  cache_key=('fengler_counter_r10b', size, at, counter_y, knob, card, src))


COUNTER_N = (0.0, -0.55, 0.84)     # the s3b counter top's normal in canvas space (the plate's view from above)
FENGLER_ZE = 22.0                  # depth of the counter's far edge: just in front of his chest
FENGLER_S = 32.0                   # his palm length (the plate's stamp block is 44 px wide, its knob 14 px)
FENGLER_ELBOW = (18.0, 14.0, 9.0)  # elbows: px outside the shoulders, px in front of the far edge, height on it
FENGLER_KNOB_H = 17.0              # the knob's top above the counter
FENGLER_CARD_DX = 4.0              # the left palm: right of the card point (the ABGANG impression stays free)
FENGLER_LEAN = 6.0                 # torso pitch: leaning a little over his work
F32 = np.float32


def _protector(M, elbow, wrist, r0, r1, cover):
    elbow, wrist = np.asarray(elbow, float), np.asarray(wrist, float)
    dd = N.nrm(wrist - elbow)
    L = float(np.linalg.norm(wrist - elbow))
    a = elbow + dd * L * 0.14
    b = wrist - dd * cover
    m = M('prot')
    parts = [RC(tuple(a), tuple(b), r0 * 1.06, r1 * 1.08, m),
             E(tuple(a + dd * 1.6), (r0 * 1.12, 1.8, r0 * 1.12), m, R=N.ortho(dd)),
             E(tuple(b - dd * 1.6), (r1 * 1.14, 1.8, r1 * 1.14), m, R=N.ortho(dd))]
    return S.Union(parts, k=1.0)


# ========================================================================================= Konrad, v2
def konrad_back_wave(f, size, src):
    """Konrad from behind at the tram loop: fedora, the turned-up coat collar, the scarf, the coat's back seam and
    belt; the left arm hangs, the hand in the black glove; the right arm f 0 hangs too, f 1 rises (elbow out,
    the hand at the shoulder), f 2 is raised -- upper arm out and up, forearm upright, the open glove with the
    fingers up and the back of the hand to us (he waves to Ilse).  Morning light from the front (cold, beyond him),
    the sodium lamp of the loop as a warm rim from the right."""
    import env_veltrava_cine_figs as F
    spec = CC.konrad()
    look = dict(key=(0.30, -0.50, -0.81), rim=(0.72, -0.28, -0.64), ambient=0.09, wrap=0.12, bg='berlin',
                glow=(0.8, 0.2), fill=0.10, fill_dir=(0.0, -0.6, 0.8), ao=0.5)
    sty = dict(F.konrad_train_styles())
    sty.update({
        'glove': MatStyle(ramp('#030304', '#08080a', '#0e0d10', '#151316', '#1d1a1d', '#272326', '#352e30',
                               '#4a4042'), [0.04, 0.09, 0.16, 0.26, 0.38, 0.54, 0.74], dither=0.02, rim='#c4a070',
                          spec=0.45, spec_pow=10.0),
        'inside': MatStyle(ramp('#020306', '#05070c', '#090c14'), [0.2, 0.5], rim=None),
        'arm_coat': sty['coat'],
        'belt': MatStyle(ramp('#04050a', '#0a0d18', '#121828', '#1a2236'), [0.08, 0.2, 0.4], rim='#56769c'),
        # dark hair under the hat brim (seen from behind it is in his own shadow: no reddish mid tones)
        'hair': MatStyle(ramp('#050608', '#0b0b0f', '#121216', '#1a191d', '#242126', '#302b2e'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#c49a68'),
    })
    zoom = 1.42
    head_px = (118.0, 62.0)
    torso_px = (116.0, 104.0)
    head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2),
                  lambda M, hp: F.nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape'),
                   lambda M, t: _coat_back(M)]

    def hanging(M, ctx, side):
        """An arm hanging at his side, seen from behind: the sleeve stands free of the coat's back (a sliver of
        the loop between arm and waist), a soft bend at the elbow, the cuff, the glove relaxed by the thigh with
        its back turned out and to us.  side +1 = his left (canvas left), -1 = his right."""
        z = ctx.zoom
        s = V2_GLOVE_S * z
        out = -side                                  # canvas x direction away from his body
        sh = shoulder(ctx, side, 0.98, out=V2_SHOULDER_OUT)
        el = sh + np.array([out * V2_ELBOW[0] * z, V2_ELBOW[1] * z, V2_ELBOW[2]])
        wr = el + np.array([-out * V2_WRIST[0] * z, V2_WRIST[1] * z, V2_WRIST[2]])
        fd = N.nrm(wr - el)
        up = N.nrm((out * 0.80, 0.0, 0.60))          # the back of the hand: out and towards the viewer
        hz0 = N.nrm(up - fd * float(np.dot(up, fd)))
        ax = N.nrm(np.cross(fd, hz0))
        hy = N.rot(fd, ax, -14.0)
        hz = N.rot(hz0, ax, -14.0)
        return N.arm(M, 'arm_coat', 'glove', sh, el, wr, (9.6 * z, 8.4 * z, 7.4 * z), hy, hz, s, cover=0.08,
                     cuff='glove', cuff_len=0.22 * s, sleeve_in='inside',
                     hand_kw=dict(side=-side, flex='relaxed', spread=2.5, thumb='rest', glove=True))

    def arms(M, ctx):
        z = ctx.zoom
        s = V2_GLOVE_S * z
        nodes = [hanging(M, ctx, 1.0)]
        sh = shoulder(ctx, -1.0, 0.98, out=V2_SHOULDER_OUT)
        if f == 0:
            return nodes + [hanging(M, ctx, -1.0)]
        elif f == 1:
            el = sh + np.array([20.0 * z, 18.0 * z, -2.0])
            wr = el + np.array([2.0 * z, -18.0 * z, 6.0])
            hy, hz, hk = (0.10, -0.95, 0.20), (0.15, 0.20, 0.97), dict(flex='rest', thumb='rest')
        else:
            el = sh + np.array([24.0 * z, -4.0 * z, -2.0])
            wr = el + np.array([-2.0 * z, -26.0 * z, 2.0])
            hy, hz, hk = (-0.05, -1.0, 0.05), (0.05, 0.05, 1.0), dict(flex=((4, 6, 3), (4, 6, 3), (6, 8, 4),
                                                                            (8, 10, 5)), thumb='out', spread=8.0)
        nodes.append(N.arm(M, 'arm_coat', 'glove', sh, el, wr, (9.4 * z, 8.6 * z, 7.8 * z), hy, hz, s, cover=0.05,
                           cuff='glove', cuff_len=0.2 * s, sleeve_in='inside',
                           hand_kw=dict(dict(side=1.0, spread=3.0, glove=True), **hk)))
        return nodes

    return figure(spec, size, zoom, head_px, torso_px, yaw=182.0, pitch=2.0, roll=0.0, torso_yaw=182.0,
                  torso_pitch=2.0, look=look, torso_kw=dict(width=V2_TRUNK_W, depth=1.0, slope=1.25, lean=0.0),
                  head_items=head_items, torso_items=torso_items, styles=sty, extra=arms,
                  tone_passes=[CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3),
                               CC.pass_grain('coat', 0.04, seed=4), F.pass_hair_back('hair'),
                               N.pass_contact((('coat', 'arm_coat'), ('arm_coat', 'glove')), (2, 1))],
                  cache_key=('konrad_back_wave_r10b', f, size, src))


V2_GLOVE_S = 19.0                  # palm length of the gloves (x zoom): a hand ~0.8 of the head's height
V2_SHOULDER_OUT = 2.6              # shoulder joints out of the bust's (the sleeves stand free of the coat's back)
V2_ELBOW = (12.0, 30.0, 7.0)       # hanging arm: elbow out, down (x zoom), towards the viewer (px)
V2_WRIST = (4.0, 26.0, -9.0)       # forearm: back in, down (x zoom), away from the viewer (px)
V2_TRUNK_W = 0.94                  # the coat's trunk a little narrower than round 9 (the arms hang beside it)


# ========================================================================================= Alexei, Card c4
def ushanka_back(M, hp, seed=21, tilt=(3.0, -2.0), y0=-15.6, z0=-4.8, r=(18.4, 22.2), fur='fur', top='hat_top'):
    """The fur ushanka seen from behind, flaps down: the side flaps reach far enough back and down to cover the
    ears completely (no pink sliver between flap and back flap), their ends rounded and tucked (no strings
    dangling on the shoulders), the back flap long and wide over the nape down to the collar."""
    mf, mt = M(fur), M(top)
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    dome = E((0, -1.0, 0), (rx - 1.2, 10.0, rz - 1.2), mt)
    dome = S.Inter(dome, S.Plane((0, 2.0, 0), (0, 1, 0), mt))
    parts = [dome]
    roll = []
    for i in range(17):
        a = np.radians(-128 + i * 16.0)
        roll.append(E(((rx + 0.6) * np.sin(a), 0.6, (rz + 0.6) * np.cos(a)), (5.6, 5.4, 3.4), mf,
                      R=S.rot(np.degrees(a), 0, 0)))
    parts.append(S.Union(roll, k=2.4))
    for sx in (1, -1):
        # down to the jaw line (round 10b: the flaps ended at the ear and the jaw showed as pink slivers)
        parts.append(S.RoundBox((sx * (rx - 1.2), 22.0, -8.0), (3.0, 18.5, 12.6), 2.8, mf, R=S.rot(sx * 6.0, 0,
                                                                                                     sx * 11.0)))
    # the back flap: a rounded slab (an ellipsoid's edge rose at the sides and bared the jaw corners) that tapers
    # towards the nape, so the hat narrows to the neck like a head instead of standing on the collar like a box
    y_top, w_top, taper = -2.0, rx + 2.4, 0.22
    slab = S.RoundBox((0, 19.0, -rz + 5.2), (rx - 3.0, 21.0, 4.6), 5.4, mf)
    trap = S.Fn(lambda P: (np.abs(P[:, 0]) - (w_top - (P[:, 1] - y_top) * taper)).astype(np.float32), mf)
    parts.append(S.Inter(slab, trap, k=2.0))
    # dome / roll blended softly; the three flaps meet the roll with a tight join, so a fold line separates them
    hat = S.Union(parts, k=[1.6] + [0.9] * (len(parts) - 2))
    hat = S.Displace(hat, lambda P: S.vnoise3(P * np.array([1.0, 0.6, 1.0], np.float32), 1.6, seed),
                     amp=0.75, lipschitz=1.35)
    allowed = S.Union([S.Offset(dome, -0.6), S.Fn(lambda P: -(P[:, 1] - 3.6), mt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def alexei_back_desk(f, size, src):
    """LS_C4_Card c4: Alexei from behind at the booth window, over his right shoulder; f 0 bowed over the card on
    the desk, 1 the head lifted to the wagon beyond the glass.  Ushanka with the flaps down (ears covered, the back
    flap over the nape), the roll-neck collar, the quilted jacket: its channels run across the back and ROUND the
    arms, the shoulders are rounded caps, the upper arms go down and forward to the desk at his sides (the elbows
    under the frame edge), a contact crease where arm and back meet.  Kerosene lamp at his left (warm key), the
    cold work lamp of the hall beyond the glass as rim."""
    import env_veltrava_cine_figs as F
    spec = dict(CC.alexei())
    # a short neck that stays inside the collar when he bows (round 10b: it poked through the collar's back)
    spec['head'] = dict(spec['head'], neck_bot=(0.0, 20.0, 1.5), neck_top=(0.0, 8.0, -3.0))
    look = dict(key=(-0.70, 0.20, -0.62), rim=(0.40, -0.55, -0.72), ambient=0.08, wrap=0.14, bg='karsk',
                glow=(0.8, 0.2), fill=0.12, fill_dir=(-0.3, -0.5, 0.8), ao=0.5)
    sty = dict(F.alexei_train_styles())
    green = ramp('#050a09', '#0a1310', '#101c17', '#17271f', '#203227', '#2b3f31', '#384d3b', '#475c46')
    th = [0.04, 0.09, 0.16, 0.26, 0.38, 0.53, 0.72]
    sty.update({
        'coat': MatStyle(green, th, dither=0.02, rim='#6f8f86'),
        'coat_lapel': MatStyle(green, th, rim='#6f8f86'),
        'arm_coat': MatStyle(green, th, dither=0.02, rim='#6f8f86'),
        'inside': MatStyle(ramp('#020303', '#050807', '#090d0b'), [0.2, 0.5], rim=None),
    })
    zoom = 1.75
    head_px = (150.0, 86.0 + (5.0 if f == 0 else 0.0))
    torso_px = (146.0, 128.0)
    head_items = [lambda M, hp: ushanka_back(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=16.0, collar_r=(13.4, 14.8)),
                   # pulled up to the hat: the bowed head lifts the back flap off the collar, the nape must not
                   # show in the gap (round 10b: pink slivers)
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-25.0, y_bot=3.0, r=(11.4, 12.6))]
    tp = 12.0 if f == 0 else 8.0

    def arms(M, ctx):
        z = ctx.zoom
        nodes = []
        for side in (-1.0, 1.0):                   # -1 his right (the near side, canvas right), +1 his left
            sh_l = np.array([side * (24.5 + C4B_ARM[0]) * 1.06, 17.0, -3.0])
            el_l = sh_l + np.array([side * C4B_ARM[1], C4B_ARM[2], C4B_ARM[3]])
            wr_l = el_l + np.array([-side * 10.0, 5.0, 26.0])
            sh, el, wr = ctx.t2v(sh_l), ctx.t2v(el_l), ctx.t2v(wr_l)
            fd = N.nrm(wr - el)
            up = ctx.tdir((0.0, -1.0, 0.0))
            hz0 = N.nrm(up - fd * float(np.dot(up, fd)))
            nodes.append(N.arm(M, 'arm_coat', 'skin', sh, el, wr, (11.6 * z, 10.4 * z, 9.0 * z), fd, hz0, 19.0 * z,
                               cover=0.40, cuff='knit', cuff_len=0.2 * 19.0 * z, sleeve_in='inside',
                               hand_kw=dict(side=-side, flex='rest', spread=3.0, thumb='rest'),
                               sleeve_fx=lambda n, a=sh, dd=el - sh: N.quilt_on(n, a, dd, period=5.0 * z,
                                                                                amp=0.55 * z)))
        return nodes

    return figure(spec, size, zoom, head_px, torso_px, yaw=198.0, pitch=12.0 if f == 0 else -12.0, roll=0.0,
                  torso_yaw=194.0, torso_pitch=tp, look=look,
                  torso_kw=dict(width=1.02, depth=1.08, slope=1.0, lean=5.0), head_items=head_items,
                  torso_items=torso_items, styles=sty, extra=arms,
                  tone_passes=[CC.pass_fur('fur'), CC.pass_stitches('coat', 5.0), F.pass_hair_back('hair'),
                               CC.pass_knit('knit', ribs=30),
                               N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                  cache_key=('alexei_back_desk', f, size, src))


C4B_ARM = (1.5, 3.0, 30.0, 16.0)   # shoulder out; elbow: out, down, forward (torso-local units)


def _coat_back(M):
    """The back of Konrad's coat: the half belt across the small of the back and the centre seam / vent."""
    m = M('belt')
    return S.Union([S.RoundBox((0.0, 64.0, -15.6), (17.0, 2.6, 1.4), 1.0, m),
                    S.Sphere((-14.0, 64.0, -16.4), 1.6, m), S.Sphere((14.0, 64.0, -16.4), 1.6, m)], k=0.5)
