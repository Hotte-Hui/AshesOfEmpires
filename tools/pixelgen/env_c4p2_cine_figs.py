"""env_c4p2_cine_figs -- the people and hands of the five Chapter-4-part-2 films as whole figures (owner: figure
stream, round 11, from the player's screenshots of LS_C4P2_Express / _Steam / _Clock).

Round 10 drew the close people of these films as dialogue busts pasted on a painted torso without arms, the backs
as flat black blobs with an outline and the hands as huge flat cut-outs.  Every person here is now traced by the
figure pipeline of the round-10 Chapter-4 films (env_c4_cine_bust.figure + env_c4_cine_anat, imported read-only):
the face, hat and coat of the dialogue portrait on a trunk down to the hips, and anatomical arms -- shoulder ->
upper arm -> elbow -> forearm -> wrist -> hand with three-phalanx fingers, knuckles and nails, sleeves with an open
end, cuffs and elbow folds -- posed for the shot and lit by its lights.  Output contracts (cell sizes, frame counts,
anchors) are the round-10 ones, so the runtimes in scenes/cinematics/ch4p2_* play them unchanged:

  alexei_back_sheet()   Express x2 / Steam m1: Alexei from behind in the left foreground (240 x 214, 8 frames:
                        breathing) -- ushanka, ear flaps tied up on the crown, the quilted telogreika, the raised collar
  lev_sheet()           Express x2: Lev at the platform's edge (160 x 184, 14 frames: 0..7 the empty hands rise,
                        palms out, and sink; 8..13 the carbons folded and pushed under the coat, the coat buttoned)
  ekdahl_cells(base)    Express x1: Ekdahl at his compartment window (168 x 110, 4 frames: hands down, the film
                        canister up at the glass, the open empty hand, the empty hand and a nod)
  irina_k3_sheet()      Clock k3: Irina at the teleprinter reading the tape (112 x 160, 10 frames)
  alexei_k3_sheet()     Clock k3: Alexei outside the frosted window (112 x 148, 8 frames)
  irina_p3_sheet()      Depot p3: Irina at her dispatch window, the ledger, the telephone rings (112 x 152, 2)
  ilse_asleep()         Clock k1: Ilse asleep on the leather offcuts under the cobbler's coat (paint_into the plate)
  photographer()        a rig spec of his own for the press photographer (install() puts it in the rig's cast)
For the places builder (extras): window_figure(), far_figure(), passerby_sheet() -- see their docstrings.
Round 11c (art director): Irina at the whole-figure scale (IRINA_* constants: smaller head, broader shoulders, a
short neck in the raised collar) with painted hands (flat_hand(): a palm-down hand at ~18 px with four fingers and
the thumb, reusable for any desk figure at that scale), the film tin of Clock k4 in Ekdahl's fist (_ekdahl_can,
_can_label), Alexei's ushanka from behind as one fur band (ushanka_tied()), the k1 neighbour standing at her sill.
Deterministic; renders memoised on disk by env_c4_cine_bust (key includes this file's source).
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2_cast as CC   # noqa: E402  (portrait cast; read-only)
import chargen_portrait2_sdf as S     # noqa: E402
import env_c4_cine_anat as N          # noqa: E402  (arms and hands; read-only)
import env_c4_cine_bust as B          # noqa: E402  (figure tracer; read-only)
from chargen_portrait2_paint import MatStyle, hexc, ramp  # noqa: E402

E, RC = S.Ellipsoid, S.RoundCone
WARM = (255, 210, 148)


_HELPERS = ('spec_of', 'bust_pose', 'rim_of', 'arm_styles', 'limb', 'lerp', '_hang', '_show', '_lev_look')


def _src(fn=None, *consts):
    """Cache key of a render: the source of the shared posing helpers, of the shot's own function and its
    constants (an edit elsewhere in this file keeps the other shots' renders)."""
    import inspect
    g = globals()
    parts = [inspect.getsource(g[n]) for n in _HELPERS if n in g]
    if fn is not None:
        parts.append(inspect.getsource(fn))
    parts.append(repr(consts))
    return hashlib.sha1(''.join(parts).encode('utf-8')).hexdigest()[:12]


def spec_of(cid):
    """A fresh dialogue-portrait spec (dict) of `cid`; Lev lives in characters_c4."""
    if cid == 'lev':
        import characters_c4 as C4
        return dict(C4.PORTRAITS_C4['lev']())
    return dict(CC.CAST[cid]())


def bust_pose(spec, at, zoom=None, dx=0.0, dy=0.0):
    """(zoom, head_px, torso_px) of the portrait's own pose with its 112-px bust's top-left at `at`: the figure
    stands where the round-10 bust stood, its head where the player saw it."""
    z = float(spec['zoom'] if zoom is None else zoom)
    c = np.array([56.0, 56.0])
    hp = c + (np.asarray(spec['head_pos'][:2], float) - c) * z + np.asarray(at, float) + (dx, dy)
    tp = c + (np.asarray(spec['torso_pos'][:2], float) - c) * z + np.asarray(at, float) + (dx, dy)
    return z, (float(hp[0]), float(hp[1])), (float(tp[0]), float(tp[1]))


def rim_of(st, col):
    """A copy of a MatStyle with another rim colour (the shot's light on the silhouette)."""
    s2 = copy.copy(st)
    s2.rim = hexc(col)
    return s2


def arm_styles(sty, sleeve='coat', inside='#06070a'):
    """The sleeve material of the arms (its own id, so a depth line parts arm and coat) and the sleeve's dark
    inside, from the coat's style."""
    st = dict(sty)
    st['arm_coat'] = st[sleeve]
    st['inside'] = MatStyle(ramp('#020203', inside, '#0c0d10'), [0.2, 0.5], rim=None)
    return st


def limb(M, ctx, side, el_l, wr_l, hand_y, hand_z, s, r, sleeve='arm_coat', skin='skin', sh=None, cover=0.30,
         cuff=None, cuff_len=0.0, hand_kw=None, fx=None, local_dirs=True, **kw):
    """One arm in torso-local terms: side -1 = the figure's right, +1 = left; el_l / wr_l = elbow / wrist
    (torso-local units, origin the pit of the neck, y down, z forward); hand_y / hand_z = finger direction /
    back of the hand (torso-local when local_dirs); s = palm length and r = (shoulder, elbow, sleeve end) radii
    in canvas px.  The shoulder joint is the bust's (env_c4_cine_bust.shoulder) unless `sh` is given."""
    shp = ctx.t2v(sh if sh is not None else (side * 24.5, 17.0, -3.0))
    el, wr = ctx.t2v(el_l), ctx.t2v(wr_l)
    hy = ctx.tdir(hand_y) if local_dirs else N.nrm(np.asarray(hand_y, float))
    hz = ctx.tdir(hand_z) if local_dirs else N.nrm(np.asarray(hand_z, float))
    hz = N.nrm(hz - hy * float(np.dot(hz, hy)))
    sfx = None
    if fx is not None:
        sfx = (lambda n, a=shp, d=el - shp: fx(n, a, d))
    return N.arm(M, sleeve, skin, shp, el, wr, r, hy, hz, s, cover=cover, cuff=cuff, cuff_len=cuff_len,
                 sleeve_in='inside', hand_kw=dict(hand_kw or {}), sleeve_fx=sfx, **kw)


def lerp(a, b, t):
    return tuple(float(x) + (float(y) - float(x)) * t for x, y in zip(a, b))


def shift_rows(rgba, dy):
    """Move a cell up by dy rows (breathing), the bottom row repeated so a figure cut by the frame stays cut."""
    if dy <= 0:
        return rgba.copy()
    out = np.empty_like(rgba)
    out[:-dy] = rgba[dy:]
    out[-dy:] = rgba[-1:]
    return out


def hsheet(cells):
    return np.concatenate(cells, axis=1)


def grade(rgba, mul=(1.0, 1.0, 1.0), lift=(0, 0, 0), rim=None, rim_k=0.6):
    """A shot grade on a traced figure: multiply / lift (posterised to 3-steps so the tones stay crisp) and an
    optional one-pixel rim of the light's colour on one side ('left' / 'right') and the top of the silhouette."""
    out = rgba.copy()
    a = out[..., 3] > 0
    c = out[..., :3].astype(np.float32) * np.asarray(mul, np.float32)[None, None] + np.asarray(lift, np.float32)
    c = np.clip(np.round(c / 3.0) * 3.0, 0, 255)
    out[..., :3] = np.where(a[..., None], c, 0).astype(np.uint8)
    if rim is not None:
        side, col = rim
        p = np.pad(a, 1)
        nb = p[1:-1, 2:] if side == 'right' else p[1:-1, :-2]
        e = a & (~nb | ~p[:-2, 1:-1])
        e[-2:] = False
        out[e, :3] = (out[e, :3].astype(np.float32) * (1.0 - rim_k) + np.asarray(col, np.float32) * rim_k).astype(np.uint8)
    return out


# ================================================================================================ Alexei, back
ALEXEI_BACK_CELL = (240, 214)


def alexei_back(lifted=0):
    """Alexei from behind, over his right shoulder, in the left foreground of the platform (and of the coal
    stage): the ushanka with its ear flaps tied up on the crown (fur roll, the back flap over the nape, the ears
    red with cold), the raised collar of the quilted telogreika, its channels running across the back and round
    the arms, the shoulders as rounded
    caps, the arms hanging at his sides (the elbows near the frame's bottom).  The platform lamps beyond him are
    the warm rim (right), the snow's cold the fill.  Rendered 2 px taller than the cell (breathing shifts)."""
    import env_veltrava_cine_figs as F
    w, h = ALEXEI_BACK_CELL
    spec = dict(CC.alexei())
    spec['head'] = dict(spec['head'], neck_bot=(0.0, 20.0, 1.5), neck_top=(0.0, 8.0, -3.0))
    look = dict(key=(0.66, -0.36, -0.66), rim=(0.74, -0.42, -0.52), ambient=0.07, wrap=0.12, bg='karsk',
                glow=(0.8, 0.2), fill=0.12, fill_dir=(-0.5, -0.5, 0.7), ao=0.5)
    sty = dict(F.alexei_train_styles())
    green = ramp('#06090a', '#0b1112', '#111a19', '#182421', '#21302a', '#2c3c33', '#3a4a3e', '#4c5a48')
    th = [0.04, 0.09, 0.16, 0.26, 0.38, 0.53, 0.72]
    sty.update({'coat': MatStyle(green, th, dither=0.02, rim='#d8a868'),
                'coat_lapel': MatStyle(green, th, rim='#d8a868')})
    # the fur in the lamps' back light: dark brown-grey in broad tones (no speckle: it read as curly hair), its
    # edges catching the amber; the crown's leather a shade apart, so roll, crown and tied flaps separate
    fur = ramp('#080706', '#110d0a', '#1a140f', '#251c15', '#32271d', '#403124', '#524030', '#685238')
    sty['fur'] = MatStyle(fur, th, dither=0.0, rim='#f0b878')
    sty['hat_top'] = MatStyle(ramp('#050506', '#0b0b0d', '#131316', '#1c1c20', '#28272c', '#363438'),
                              [0.06, 0.16, 0.32, 0.52, 0.74], rim='#e8b070')
    sty['tie_string'] = MatStyle(ramp('#0a0806', '#1e1812', '#3a2e22', '#5a4834'), [0.15, 0.4, 0.7],
                                 rim='#e8b070')
    for nm in ('knit', 'hair', 'skin', 'ear'):
        if nm in sty:
            sty[nm] = rim_of(sty[nm], '#e0a860')
    # the cropped hair under the hat's band: near-black, so the strip above the collar never reads as a scalp
    sty['hair'] = MatStyle(ramp('#050405', '#0b0909', '#13100e', '#1c1612', '#261e18', '#33281f'),
                           [0.08, 0.2, 0.38, 0.6, 0.82], rim='#c89060')
    sty = arm_styles(sty, 'coat')
    zoom = 2.0
    head_px = (100.0, 66.0)
    torso_px = (92.0, 66.0 + 34.0 * zoom)
    # the round-10 design of this shot: the ear flaps tied up on the crown, the back flap down over the nape --
    # from behind that is what reads as an ushanka (flaps down it is a fur box); the ears show, red with cold
    head_items = [lambda M, hp: ushanka_tied(M, hp, r=(17.6, 21.2)),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=17.0, collar_r=(13.6, 15.2)),
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-25.0, y_bot=3.0, r=(11.4, 12.6))]

    def arms(M, ctx):
        z = ctx.zoom
        nodes = []
        for side in (-1.0, 1.0):
            sh = (side * 29.0, 17.0, -3.0)
            el = (side * 35.0, 50.0, -3.0)
            wr = (side * 31.0, 78.0, 6.0)
            nodes.append(limb(M, ctx, side, el, wr, (0.0, 1.0, 0.2), (side * 1.0, 0.0, 0.0), 19.0 * z,
                              (12.4 * z, 11.0 * z, 9.6 * z), sh=sh, cover=0.36, cuff='knit',
                              cuff_len=0.2 * 19.0 * z, skin='skin',
                              hand_kw=dict(side=-side, flex='relaxed', spread=3.0, thumb='rest'),
                              fx=lambda n, a, d: N.quilt_on(n, a, d, period=5.0 * z, amp=0.55 * z)))
        return nodes

    return B.figure(spec, (w, h + 2), zoom, head_px, torso_px, yaw=160.0, pitch=2.0, roll=-2.0, torso_yaw=170.0,
                    torso_pitch=4.0, look=look, torso_kw=dict(width=1.22, depth=1.1, slope=1.15, lean=2.0),
                    head_items=head_items, torso_items=torso_items, styles=sty, extra=arms,
                    tone_passes=[CC.pass_stitches('coat', 5.0), F.pass_hair_back('hair'),
                                 CC.pass_knit('knit', ribs=30), N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                    cache_key=('c4p2_alexei_back', lifted, _src(alexei_back, ALEXEI_BACK_CELL), _src(ushanka_tied)))


def ushanka_tied(M, hp, r=(17.6, 21.2), y0=-15.6, z0=-4.8, tilt=(3.0, -2.0), seed=21):
    """The ushanka seen from behind with its flaps tied up (round 11c: the portrait's 'up' hat read as a
    cauliflower of fur over a smooth tan dome): one continuous fur band all round, deep on the head (the back
    flap folded up into it, a little taller at the back), the two ear flaps folded up the sides of the crown and
    tied on top with a string bow, the cloth crown between them; only a breath of noise on the fur, so its
    masses stay broad (head-local, like chargen_portrait2_cast.ushanka)."""
    mf, mt, ms = M('fur'), M('hat_top'), M('tie_string')
    hf = S.Frame((0.0, y0, z0), S.rot(0, tilt[0], tilt[1]))
    rx, rz = r
    dome = S.Inter(E((0, -1.0, 0), (rx - 1.4, 10.5, rz - 1.4), mt), S.Plane((0, 4.0, 0), (0, 1, 0), mt))
    band = []
    for i in range(24):
        a = np.radians(i * 15.0)
        back = max(0.0, -float(np.cos(a)))
        band.append(E(((rx + 0.4) * np.sin(a), 4.2 + 6.0 * back ** 1.5, (rz + 0.4 - 1.2 * back) * np.cos(a)),
                      (5.2, 6.0 + 3.2 * back ** 1.5, 3.0), mf, R=S.rot(np.degrees(a), 0, 0)))
    parts = [dome, S.Union(band, k=2.2)]
    for sx in (1, -1):
        parts.append(S.RoundBox((sx * (rx - 7.0), -7.6, -1.5), (2.2, 5.4, 7.0), 2.0, mf, R=S.rot(0, 0, -sx * 50.0)))
    parts.append(E((0, -11.8, -1.5), (2.0, 1.3, 1.6), ms))
    for sx in (1, -1):
        parts.append(RC((0.0, -11.8, -1.5), (sx * 3.2, -11.0, -2.6), 0.6, 0.45, ms))
    hat = S.Union(parts, k=[1.4] + [1.8] * (len(parts) - 2))
    hat = S.Displace(hat, lambda P: S.vnoise3(P * np.array([1.0, 0.6, 1.0], np.float32), 2.6, seed),
                     amp=0.3, lipschitz=1.2)
    allowed = S.Union([S.Offset(dome, -0.6), S.Fn(lambda P: -(P[:, 1] - 6.0), mt)])
    return dict(node=S.Xform(hat, frame=hf), clip=S.Xform(allowed, frame=hf))


def alexei_back_sheet():
    """8 cells (240 x 214): the shoulders rise a pixel on frames 2..4 (breathing), the platform's amber rim."""
    w, h = ALEXEI_BACK_CELL
    base = alexei_back(0)
    g = grade(base, mul=(0.92, 0.92, 1.0), rim=('right', (240, 190, 120)), rim_k=0.7)
    # a second, softer rim pixel inside the first on the lamp side (the amber wraps a little round the fur)
    a = base[..., 3] > 0
    p = np.pad(a, 1)
    e1 = a & (~p[1:-1, 2:] | ~p[:-2, 1:-1])
    p1 = np.pad(e1, 1)
    e2 = a & ~e1 & (p1[1:-1, 2:] | p1[:-2, 1:-1])
    e2[:, :int(w * 0.3)] = False
    g[e2, :3] = (g[e2, :3].astype(np.float32) * 0.7 + np.asarray((220, 160, 96), np.float32) * 0.3).astype(np.uint8)
    cells = []
    for f in range(8):
        lift = 1 if f in (2, 3, 4) else 0
        cells.append(shift_rows(g, lift)[:h])
    return hsheet(cells)


# ================================================================================================ Lev, x2
LEV_CELL = (160, 184)
LEV_AT = (24, 0)                    # where the round-10 bust sat in the cell (top-left of its 112 px)
LEV_LIFT = (0, 12, 26, 36, 36, 30, 16, 0)
# protect_first: (bundle up, fold) per frame, the round-10 keys
LEV_KEYS = ((46, 0.0), (44, 0.0), (40, 0.6), (30, 0.9), (22, 1.0), (16, 1.0))


def _lev_look():
    return dict(key=(-0.50, -0.38, 0.78), rim=(0.76, -0.40, -0.50), ambient=0.09, wrap=0.16, bg='karsk',
                glow=(0.8, 0.2), fill=0.10, fill_dir=(0.4, -0.5, 0.75), ao=0.5)


def _hang(side):
    """A relaxed hanging arm (torso-local): elbow, wrist, finger direction, back of the hand."""
    return (side * 29.0, 46.0, -1.0), (side * 27.5, 73.0, 5.0), (side * 0.05, 1.0, 0.12), (side * 1.0, 0.0, 0.1)


def _show(side):
    """The empty hand shown: elbow at the side, the forearm forward, out and up, the open hand tilted so the
    palm faces up and out to the viewer, the fingers spread a little."""
    return (side * 30.0, 45.0, 4.0), (side * 37.0, 34.0, 21.0), (side * 0.55, -0.62, 0.56), (side * 0.10, 0.62, -0.78)


def lev_frame(kind, k, blink=False):
    """One Lev cell (160 x 184).  kind 'show': k in 0..1 = how far the empty hands are up; kind 'carbons':
    k = 0..5, the protect_first keys (LEV_KEYS)."""
    spec = spec_of('lev')
    w, h = LEV_CELL
    zoom, head_px, torso_px = bust_pose(spec, LEV_AT)
    sty = arm_styles(spec['styles'], 'coat')
    # the carbons must read at a glance in the night grade (tests/test_c4p2_cinematics: a big white bundle)
    sty['paper'] = MatStyle(ramp('#4a4a4e', '#8a8a8c', '#bcbab4', '#e2dfd6', '#f2efe6', '#fbf9f2'),
                            [0.08, 0.18, 0.30, 0.46, 0.66], rim='#fff0d0')
    look = _lev_look()

    def bundle(M, ctx, up, fold, tuck=0.0):
        """The carbons: a thick sheaf of foolscap copies, folded once at fold > 0.5; tuck > 0 slides it under the
        coat's left panel (it is cut by the coat's surface: the part inside is not there)."""
        m = M('paper')
        hh = 20.0 if fold < 0.5 else 11.0
        th = 2.2 if fold < 0.5 else 3.6
        c = (3.0 + 9.0 * tuck, 58.0 - up * 0.62 + 6.0 * tuck, 19.0 - 9.0 * tuck)
        R = S.rot(-8.0 + 26.0 * tuck, 30.0, 4.0 + 6.0 * fold)
        node = S.RoundBox(tuple(ctx.t2v(c)), (15.5 * ctx.zoom * (1.0 - 0.25 * tuck), hh * ctx.zoom, th * ctx.zoom),
                          0.6 * ctx.zoom, m, R=R)
        return node, c

    def arms(M, ctx):
        z = ctx.zoom
        s = 17.5 * z
        r = (9.4 * z, 8.4 * z, 7.4 * z)
        common = dict(cuff='cardigan', cuff_len=0.18 * s, skin='skin')
        nodes = []
        if kind == 'show':
            t = float(k)
            for side in (-1.0, 1.0):
                a, b = _hang(side), _show(side)
                ease = t * t * (3.0 - 2.0 * t)
                el, wr = lerp(a[0], b[0], ease), lerp(a[1], b[1], ease)
                # the hands turn from hanging (backs out) to shown square to the viewer (palms to us, fingers
                # up and a little out) -- canvas space, so the torso's turn never twists a palm away
                hy = N.nrm(np.asarray(lerp(ctx.tdir(a[2]), (side * 0.30, -0.95, 0.10), ease)))
                hz = N.nrm(np.asarray(lerp(ctx.tdir(a[3]), (side * 0.05, 0.10, -0.99), ease)))
                nodes.append(limb(M, ctx, side, el, wr, hy, hz, s, r, **common, local_dirs=False,
                                  hand_kw=dict(side=-side, flex='flat' if t > 0.5 else 'relaxed', spread=5.0 * t,
                                               thumb='out' if t > 0.5 else 'rest')))
            return nodes
        up, fold = LEV_KEYS[int(k)]
        if k <= 2:
            node, c = bundle(M, ctx, up, fold)
            nodes.append(node)
            for side in (-1.0, 1.0):
                # the hands hold the sheaf by its lower corners, the thumbs on the front sheet
                el = (side * 28.0, 47.0, 6.0)
                wr = (side * 18.0, c[1] + 12.0 - fold * 6.0, c[2] + 2.0)
                nodes.append(limb(M, ctx, side, el, wr, (-side * 0.25, -0.92, 0.25), (side * 1.0, 0.0, 0.25), s,
                                  r, **common, hand_kw=dict(side=-side, flex='grip', spread=2.0, thumb='press')))
        elif k == 3:
            node, c = bundle(M, ctx, up, fold, tuck=1.0)
            nodes.append(node)
            # his right hand pushes the folded carbons under the coat's left panel, his left holds the panel
            nodes.append(limb(M, ctx, -1.0, (-26.0, 46.0, 6.0), (2.0, c[1] + 6.0, c[2] + 4.0), (0.7, -0.55, 0.2),
                              (0.05, 0.25, 0.97), s, r, **common,
                              hand_kw=dict(side=1.0, flex='flat', spread=1.0, thumb='along')))
            nodes.append(limb(M, ctx, 1.0, (28.0, 46.0, 2.0), (19.0, 34.0, 15.0), (-0.35, -0.9, 0.2),
                              (0.9, 0.0, 0.4), s, r, **common,
                              hand_kw=dict(side=-1.0, flex='pinch', spread=1.0, thumb='pinch')))
        else:
            # the bundle is gone; his right hand flat on the coat over it (k 4) / at the top button (k 5)
            if k == 4:
                wr, hy = (2.0, 40.0, 17.0), (0.75, -0.6, 0.1)
            else:
                wr, hy = (-4.0, 26.0, 17.5), (0.55, -0.82, 0.08)
            nodes.append(limb(M, ctx, -1.0, (-27.0, 46.0, 7.0), wr, hy, (0.0, 0.1, 1.0), s, r, **common,
                              hand_kw=dict(side=1.0, flex='press' if k == 4 else 'pinch', spread=1.0,
                                           thumb='along' if k == 4 else 'pinch')))
            el, wr_, hy_, hz_ = _hang(1.0)
            nodes.append(limb(M, ctx, 1.0, el, wr_, hy_, hz_, s, r, **common,
                              hand_kw=dict(side=-1.0, flex='relaxed', spread=2.0, thumb='rest')))
        return nodes

    tk = dict(spec['torso'])
    return B.figure(spec, (w, h), zoom, head_px, torso_px, yaw=spec['yaw'], pitch=spec['pitch'], roll=spec['roll'],
                    torso_yaw=spec['torso_yaw'], look=look, torso_kw=tk, styles=sty, extra=arms,
                    expr='concerned', blink=blink,
                    tone_passes=list(spec.get('tone_passes', ())) + [N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                    cache_key=('c4p2_lev', kind, k, blink, _src(lev_frame, LEV_CELL, LEV_AT, LEV_KEYS)))


def lev_sheet():
    """14 cells: 0..7 publish_now (the empty hands, LEV_LIFT; a blink on 4), 8..13 protect_first (LEV_KEYS),
    graded to the night platform: cold on the face, the lamps' amber on the right edges."""
    out = []
    memo = {}
    for f, lift in enumerate(LEV_LIFT):
        key = (lift, f == 4)
        if key not in memo:
            memo[key] = lev_frame('show', lift / 36.0, blink=(f == 4))
        out.append(memo[key])
    for k in range(len(LEV_KEYS)):
        out.append(lev_frame('carbons', k))
    return hsheet([grade(c, mul=(0.88, 0.9, 1.0), rim=('right', (255, 206, 140)), rim_k=0.55) for c in out])


# ================================================================================================ Ekdahl, x1
EKDAHL_GLASS = (168, 110)
EKDAHL_AT = (14, 6)                 # the round-10 bust's top-left in the glass


def ekdahl(f):
    """Ekdahl at his compartment window (the glass, 168 x 110): f 0 his hands down (below the sill), 1 his left
    hand up at the glass holding a 35-mm film can between thumb and fingers, 2 the open empty hand, palm to the
    glass, 3 the empty hand and a nod (head down, eyes shut).  The compartment lamp at the right is the warm key,
    the platform's cold light through the glass a faint fill from the left."""
    spec = spec_of('journalist')
    w, h = EKDAHL_GLASS
    zoom, head_px, torso_px = bust_pose(spec, EKDAHL_AT)
    sty = arm_styles(spec['styles'], 'coat')
    sty['can'] = MatStyle(ramp('#0e1012', '#1c2024', '#2c3136', '#41474e', '#5c646b', '#838c93'),
                          [0.14, 0.30, 0.50, 0.70, 0.88], spec=0.5, spec_pow=14.0, rim='#ffe2b0')
    sty['can_top'] = MatStyle(ramp('#1e2024', '#40444a', '#646a72', '#8e959c', '#c2c8cc'),
                              [0.15, 0.35, 0.6, 0.82], spec=0.5, rim='#ffe2b0')
    look = dict(key=(0.70, -0.25, 0.67), rim=(-0.72, -0.30, -0.62), ambient=0.08, wrap=0.18, bg='karsk',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(-0.6, -0.4, 0.7), ao=0.5)

    def arms(M, ctx):
        if f == 0:
            return []
        z = ctx.zoom
        s = 17.5 * z
        r = (9.6 * z, 8.6 * z, 7.6 * z)
        nodes = []
        # the forearm rises beside him, the hand at the glass level of his cheek, clear of his face (round 11b:
        # a can in front of the chin read as eating)
        el = (42.0, 40.0, 12.0)
        wr = EKDAHL_WRIST[f == 1]
        if f == 1:
            hy, hz = (0.05, -1.0, 0.05), (0.15, 0.0, -0.99)
            hk = dict(side=-1.0, flex='grip', spread=1.5, thumb='rest')
        else:
            hy, hz = (0.12, -0.99, 0.0), (0.05, 0.12, -0.99)
            hk = dict(side=-1.0, flex='flat', spread=5.0, thumb='out')
        nodes.append(limb(M, ctx, 1.0, el, wr, hy, hz, s, r, cuff='shirt', cuff_len=0.2 * s, local_dirs=False,
                          hand_kw=hk))
        if f == 1:
            # round 11c: the flat round film tin of Clock k4 (it read as a torch lying across the fist): upright
            # on his curled fingers, the lid to the glass, the fingertips over its lower rim; the tin's body, the
            # lid proud of it with its rim, the raised centre (the tape and C-17 are painted after the trace)
            c, ax, r0 = _ekdahl_can(ctx.t2v(wr), s)
            Rm = _axis_frame(ax)
            nodes.append(S.Cylinder(tuple(c), r0, 0.11 * s, M('can'), R=Rm, e=0.6))
            nodes.append(S.Cylinder(tuple(c + ax * 0.10 * s), r0 + 0.5, 0.05 * s, M('can_top'), R=Rm, e=0.4))
            nodes.append(S.Cylinder(tuple(c + ax * 0.15 * s), r0 * 0.30, 0.04 * s, M('can'), R=Rm, e=0.3))
        return nodes

    pitch = spec['pitch'] + (11.0 if f == 3 else 0.0)
    out = B.figure(spec, (w, h), zoom, head_px, (torso_px[0], torso_px[1]), yaw=spec['yaw'] - 4.0, pitch=pitch,
                   roll=spec['roll'], torso_yaw=spec['torso_yaw'], look=look, torso_kw=dict(spec['torso']),
                   styles=sty, extra=arms, expr='determined' if f == 1 else 'neutral', blink=(f == 3),
                   tone_passes=list(spec.get('tone_passes', ())) + [N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                   cache_key=('c4p2_ekdahl', f, _src(ekdahl, EKDAHL_GLASS, EKDAHL_AT, EKDAHL_WRIST),
                              _src(_ekdahl_can)))
    if f == 1:
        ctx = B.Ctx(zoom, None, S.Frame(B._pre(torso_px, zoom), S.rot(spec['torso_yaw'], 0.0, 0.0)), None, None)
        c, ax, r0 = _ekdahl_can(ctx.t2v(EKDAHL_WRIST[True]), 17.5 * zoom)
        out = _can_label(out, c[0] + ax[0] * 0.15 * 17.5 * zoom, c[1] + ax[1] * 0.15 * 17.5 * zoom, r0)
    return out


EKDAHL_WRIST = {False: (47.0, -17.0, 19.0), True: (47.0, -12.0, 19.0)}


def _ekdahl_can(wv, s):
    """(centre, axis, radius) of the film tin in Ekdahl's raised fist, canvas space: standing on the curled
    fingers, a little behind them, its lid turned to the glass (a slight tilt shows the rim)."""
    r0 = 0.64 * s
    c = np.asarray(wv, float) + np.array([0.04 * s, -(1.0 * s + r0 * 0.8), -0.16 * s])
    return c, N.nrm(np.array([-0.20, 0.10, 1.0])), r0


def _axis_frame(axis):
    """Rotation whose local y axis is `axis` (the columns are the local axes, for S.Cylinder's R)."""
    y = N.nrm(np.asarray(axis, float))
    t = np.array([1.0, 0.0, 0.0]) if abs(y[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = N.nrm(t - y * float(np.dot(t, y)))
    return np.stack([x, y, np.cross(x, y)], axis=1)


def _can_label(rgba, cx, cy, r):
    """The tape strip across the film tin's lid with C-17 in pencil (the tin of Clock k4), painted on the traced
    figure where the tin shows: grey pixels inside the lid (the fingers in front keep their skin)."""
    import env_c4p2_cine_flat as FL
    out = rgba.copy()
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    c = out[..., :3].astype(np.int32)
    grey = (out[..., 3] > 0) & ((c.max(-1) - c.min(-1)) < 30)
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 < (r - 1.8) ** 2
    band = grey & inside & (np.abs(yy - cy) <= 2.6)
    out[band, :3] = (226, 218, 190)
    out[band & (np.abs(yy - (cy + 2.6)) < 0.6), :3] = (168, 160, 134)
    T = FL.Flat(40, 10, bg='#000000')
    ys, xs = np.nonzero(T.text('C-17', 2, 2, 's'))
    if len(xs):
        ox = int(round(cx - (xs.max() - xs.min() + 1) / 2.0)) - xs.min()
        oy = int(round(cy - (ys.max() - ys.min() + 1) / 2.0)) - ys.min()
        for y, x in zip(ys + oy, xs + ox):
            if 0 <= x < w and 0 <= y < h and band[y, x]:
                out[y, x, :3] = (62, 62, 68)
    return out


def ekdahl_cells(base):
    """The four window cells: the compartment `base` (168 x 110 RGBA, painted by the film) with Ekdahl over it."""
    out = []
    for f in range(4):
        cell = base.copy()
        fig = grade(ekdahl(f), mul=(1.04, 0.98, 0.9), rim=('right', (255, 214, 150)), rim_k=0.5)
        a = fig[..., 3:4].astype(np.float32) / 255.0
        cell[..., :3] = (fig[..., :3] * a + cell[..., :3] * (1.0 - a)).astype(np.uint8)
        cell[..., 3] = np.maximum(cell[..., 3], fig[..., 3])
        out.append(cell)
    return out


# ================================================================================================ Irina
IRINA_K3_CELL = (112, 160)
IRINA_P3_CELL = (112, 152)
# round 11c (art director: "still a portrait bust on a body"): the head a size smaller than the dialogue
# portrait's (zoom 1.18 -> 1.0), the shoulders broader (trunk width 0.92 -> 1.26: shoulders ~2.5 heads wide),
# the neck shorter (head centre -> pit of the neck 35.5 -> 30 units) and the jacket's quilted collar standing up
# round a short folded roll-neck, so no long mustard tube joins the head to the body
IRINA_ZOOM = 1.0
IRINA_TORSO = dict(width=1.26, depth=1.06, slope=1.2)
IRINA_NECK = 30.0
IRINA_HEAD_Y = {'k3': 60.0, 'p3': 50.0}      # head centre row in the cell (the desk / counter lower on her body)


IRINA_SKIN = ('#2a1418', '#5f3739', '#8d5445', '#b77553', '#d89b6d', '#f0c695')


def flat_hand(face=1, key=1, curl=0.0, skin=IRINA_SKIN, nail='#e8b8a0'):
    """A hand lying palm-down on a desk seen from the front at eye level, painted at 1:1 for the figure scale of
    the dispatch shots (a hand ~18 px from wrist to fingertip): the back of the hand with its knuckles, four
    fingers fanned a little across the desk (the index farthest, the little finger nearest, a dark line between
    each two, the nails on the tips), the thumb behind the index at the wrist.  face +1: the fingers point
    right; key +1: the lamp is on the right.  Returns (rgba 22 x 13, wrist anchor (x, y))."""
    import env_c4p2_cine_flat as FL
    W, H = 22, 13
    F = FL.Flat(W, H, bg='#000000')
    yy = F.yy
    out_c, deep, shade, base, lit, high = skin
    k = 1.0 - 0.4 * curl
    thumb = F.line([(4.0, 4.4), (7.6, 2.4), (10.4, 1.9)], 1.05)
    back = F.poly([(1.0, 4.4), (6.0, 3.2), (11.2, 3.4), (11.8, 10.6), (6.0, 11.0), (1.0, 9.8)])
    fingers = [((10.8, 4.2), (10.8 + 6.2 * k, 3.1), 1.05),        # index (the far side)
               ((11.4, 6.2), (11.4 + 7.3 * k, 5.9), 1.05),        # middle
               ((11.4, 8.2), (11.4 + 6.6 * k, 8.5), 1.0),         # ring
               ((10.8, 10.0), (10.8 + 5.0 * k, 10.9), 0.9)]       # little (the near side)
    F.fill(thumb, shade)
    F.fill(thumb & (yy < 2.6), base)
    F.fill(back, base)
    F.fill(back & (yy < 6.0), lit)
    F.fill(back & F.ell(9.2, 4.6, 2.0, 1.0), high)                # the knuckles catch the light
    F.fill(back & (yy > 9.6), shade)
    masks = [thumb, back]
    for (a, b, r) in fingers:
        fm = F.line([a, b], r)
        F.fill(fm, base)
        F.fill(fm & (yy < (a[1] + b[1]) / 2.0 - 0.3), lit)
        F.fill(fm & F.ell(b[0] - 0.6, b[1] - 0.3, 1.0, 0.6), nail)
        F.fill(FL.edge(fm, 'b', 1) & ~F.ell(b[0], b[1], 0.8, 0.8), deep)   # the line to the next finger
        masks.append(fm)
    m = np.zeros((H, W), bool)
    for q in masks:
        m |= q
    F.fill(FL.edge(m, 'r' if key > 0 else 'l', 1) & m & (yy < 9), high)
    F.outline(m, col=out_c)
    rgba = F.rgba(m | FL.edge(m, 'all', 1))
    anchor = (1, 7)
    if face < 0:
        rgba = rgba[:, ::-1].copy()
        anchor = (W - 2, 7)
    return rgba, anchor


def _over(dst, src, x, y):
    """Composite src over dst (both RGBA uint8) with src's top-left at (x, y), clipped."""
    h, w = src.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(w, dst.shape[1] - x0), min(h, dst.shape[0] - y0)
    if ex <= sx0 or ey <= sy0:
        return dst
    s = src[sy0:ey, sx0:ex].astype(np.float32)
    d = dst[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32)
    a = s[..., 3:4] / 255.0
    d[..., :3] = s[..., :3] * a + d[..., :3] * (1.0 - a)
    d[..., 3] = np.maximum(d[..., 3], s[..., 3])
    dst[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = d.astype(np.uint8)
    return dst


def irina_items():
    """Her jacket and roll-neck for the whole figure: the quilted collar stands up round the neck (higher than
    the portrait's), the roll-neck shows as a short folded rim above it."""
    return [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.5, lapel=False, quilt=(4.4, 0.55),
                                        collar_h=9.5, collar_r=(12.2, 14.4)),
            lambda M, t: CC.rollneck(M, 'knit', y_top=-8.5, y_bot=3.0, r=(8.6, 10.2))]


def irina(expr, blink=False, size=IRINA_K3_CELL, desk=136, look_down=True, turn=0.0, tag='k3'):
    """Irina seated behind a desk whose near edge is at cell row `desk` (the film's front layer hides what is
    below): her dispatcher's quilted jacket and roll-neck, broad shoulders and whole arms -- the upper arms down
    at her sides, the elbows at the desk, the forearms forward and in on it, both hands lying on the desk with the
    fingers pointing across it (four fingers and the thumb apart, the backs of the hands with their knuckles to
    the lamp) -- the face of her dialogue portrait.  turn: degrees the head turns towards the telephone (p3)."""
    spec = spec_of('irina')
    w, h = size
    z0, hp0, _tp = bust_pose(spec, (0, 0))
    zoom = IRINA_ZOOM
    head_px = (hp0[0], IRINA_HEAD_Y[tag])
    torso_px = (hp0[0] + 0.5 * zoom, head_px[1] + IRINA_NECK * zoom)
    sty = arm_styles(spec['styles'], 'coat')
    look = dict(key=(0.68, -0.30, 0.67), rim=(-0.74, -0.34, -0.58), ambient=0.08, wrap=0.18, bg='karsk',
                glow=(0.8, 0.2), fill=0.09, fill_dir=(-0.6, -0.4, 0.7), ao=0.5)
    dy = (desk - torso_px[1]) / zoom              # the desk's near edge, torso-local
    tw = IRINA_TORSO['width']
    tyaw = spec['torso_yaw'] * 0.6
    joints = []
    for side in (-1.0, 1.0):
        sh = (side * 23.5 * tw, 16.0, -3.0)
        if dy > 38.0:                             # k3: elbows at the desk by her sides, forearms in on it
            joints.append((side, sh, (side * 31.0, dy - 3.0, 6.0), (side * 19.0, dy - 8.0, 27.0)))
        else:                                     # p3: leaning on the counter, the elbows on it
            joints.append((side, sh, (side * 31.0, dy - 3.0, 16.0), (side * 18.0, dy - 7.0, 33.0)))

    def arms(M, ctx):
        z = ctx.zoom
        s = 8.0 * z                               # a small traced hand under the painted one (flat_hand)
        r = (9.8 * z, 8.6 * z, 7.4 * z)
        nodes = []
        for side, sh, el, wr in joints:
            hy, hz = (-side * 0.93, 0.06, 0.36), (side * 0.04, -0.40, 0.92)
            nodes.append(limb(M, ctx, side, el, wr, hy, hz, s, r, sh=sh, cuff='knit', cuff_len=0.4 * s,
                              hand_kw=dict(side=-side, flex='rest', spread=2.0, thumb='rest'),
                              fx=lambda n, a, d: N.quilt_on(n, a, d, period=4.4 * z, amp=0.5 * z)))
        return nodes

    pitch = spec['pitch'] + (9.0 if look_down else 0.0)
    out = B.figure(spec, (w, h), zoom, head_px, torso_px, yaw=spec['yaw'] - turn, pitch=pitch, roll=spec['roll'],
                   torso_yaw=tyaw, look=look, torso_kw=dict(IRINA_TORSO), torso_items=irina_items(),
                   styles=sty, extra=arms, expr=expr, blink=blink,
                   tone_passes=list(spec.get('tone_passes', ())) + [N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                   cache_key=('c4p2_irina', expr, blink, size, desk, look_down, turn, tag,
                              _src(irina, IRINA_ZOOM, IRINA_TORSO, IRINA_NECK, IRINA_HEAD_Y),
                              _src(irina_items)))
    # the hands, painted at the figure's scale where the traced wrists are: lying on the desk, the fingers
    # pointing across it toward each other (round 11c: the traced hands read as mittens at this size)
    ctx = B.Ctx(zoom, None, S.Frame(B._pre(torso_px, zoom), S.rot(tyaw, 0.0, 0.0)), None, None)
    key = 1 if tag == 'k3' else -1
    for side, sh, el, wr in joints:
        wv = ctx.t2v(wr)
        hand, (ax, ay) = flat_hand(face=-int(side), key=key, curl=0.35 if side > 0 else 0.0)
        out = _over(out, hand, wv[0] - ax - side * 2.0, min(wv[1] - ay + 2.0, desk - 12.0))
    return out


def irina_k3_sheet():
    """Clock k3, 10 cells (the round-10 sequence): reading the tape -- neutral, a blink, then concerned; 6..9
    concerned breathing with a blink.  The green lamp at her left is the warm key."""
    seq = [('neutral', False), ('neutral', False), ('neutral', True), ('concerned', False), ('concerned', False),
           ('concerned', False), ('concerned', False), ('concerned', False), ('concerned', True),
           ('concerned', False)]
    memo = {}
    cells = []
    for ex, bl in seq:
        if (ex, bl) not in memo:
            memo[(ex, bl)] = grade(irina(ex, bl), mul=(1.06, 1.0, 0.88), rim=('right', (255, 220, 160)), rim_k=0.45)
        cells.append(memo[(ex, bl)])
    return hsheet(cells)


def irina_p3_sheet():
    """Depot p3, 2 cells: f 0 at her ledger (neutral, eyes down), f 1 the telephone has rung -- she looks up and
    round to it (surprised).  Her lamp warm from the left, the yard's cold light on the right."""
    a = irina('neutral', size=IRINA_P3_CELL, desk=112, look_down=True, tag='p3')
    b = irina('surprised', size=IRINA_P3_CELL, desk=112, look_down=False, turn=10.0, tag='p3')
    return hsheet([grade(c, mul=(1.04, 0.98, 0.88), rim=('left', (255, 214, 150)), rim_k=0.45) for c in (a, b)])


# ================================================================================================ Alexei, k3
ALEXEI_K3_CELL = (112, 148)
ALEXEI_K3_GLASS = (-16, -48, 188, 124)   # the window's glass in his cell (K3_WIN - K3_ALEXEI)


def alexei_k3(blink=False):
    """Alexei outside the frosted dispatch window at night: the ushanka with the flaps down, the quilted
    telogreika's raised collar, his shoulders and upper arms (the window's sill cuts him at the chest), turned
    to Irina inside; the room's warm light on his face, the night's cold on the rest."""
    spec = spec_of('alexei')
    w, h = ALEXEI_K3_CELL
    zoom, head_px, torso_px = bust_pose(spec, (0, 0))
    sty = arm_styles(spec['styles'], 'coat')
    look = dict(key=(0.62, -0.28, 0.73), rim=(-0.70, -0.40, -0.60), ambient=0.08, wrap=0.16, bg='karsk',
                glow=(0.8, 0.2), fill=0.10, fill_dir=(-0.5, -0.5, 0.7), ao=0.5)

    def arms(M, ctx):
        z = ctx.zoom
        s = 17.5 * z
        nodes = []
        for side in (-1.0, 1.0):
            el, wr, hy, hz = _hang(side)
            nodes.append(limb(M, ctx, side, (side * 31.0, 46.0, 0.0), wr, hy, hz, s,
                              (12.0 * z, 10.8 * z, 9.6 * z), sh=(side * 26.0, 17.0, -3.0), cuff='knit',
                              cuff_len=0.2 * s, hand_kw=dict(side=-side, flex='relaxed', spread=3.0, thumb='rest'),
                              fx=lambda n, a, d: N.quilt_on(n, a, d, period=5.0 * z, amp=0.55 * z)))
        return nodes

    out = B.figure(spec, (w, h), zoom, head_px, torso_px, yaw=spec['yaw'] + 6.0, pitch=spec['pitch'],
                   roll=spec['roll'], torso_yaw=spec['torso_yaw'], look=look, torso_kw=dict(spec['torso']),
                   styles=sty, extra=arms, expr='concerned', blink=blink,
                   tone_passes=list(spec.get('tone_passes', ())) + [N.pass_contact((('coat', 'arm_coat'),), (2, 1))],
                   cache_key=('c4p2_alexei_k3', blink, _src(alexei_k3, ALEXEI_K3_CELL)))
    gx0, gy0, gx1, gy1 = ALEXEI_K3_GLASS
    yy, xx = np.mgrid[0:h, 0:w]
    out[~((xx >= gx0) & (xx < gx1) & (yy >= gy0) & (yy < gy1)), 3] = 0
    return out


def alexei_k3_sheet():
    """Clock k3, 8 cells (a blink on 5), graded cold by the night with the room's warm light on the left."""
    rest = grade(alexei_k3(False), mul=(0.66, 0.74, 0.94), lift=(4, 6, 14), rim=('right', (255, 214, 150)), rim_k=0.5)
    bl = grade(alexei_k3(True), mul=(0.66, 0.74, 0.94), lift=(4, 6, 14), rim=('right', (255, 214, 150)), rim_k=0.5)
    return hsheet([bl if i == 5 else rest for i in range(8)])


# ================================================================================================ the photographer
# The press photographer of the depot show had no rig spec and was drawn from the stand-in worker_b.  His own: the
# dark gabardine coat of his dialogue portrait (chargen_portrait2_cast.photographer), the fedora pushed back with
# the white press card in its band, the loosened tie, the rangefinder on its strap at his chest.
PHOTOG_SIDE = [
    '. . . . 1 2 3 3 . . . .',
    '. . . 1 2 3 3 3 3 . . .',
    '. . 1 2 2 3 3 3 4 . . .',
    '. . u u v c V V V . . .',
    '. R 1 2 2 2 3 3 4 3 . .',
    '. . . j r r s B s S . .',
    '. . . j h s S e S L . .',
    '. . . . r s S S L L H .',
    '. . . . r s S S m S . .',
    '. . . . . r s S S S . .',
    '. . . . . . s @ . . . .',
]
CAM_ROWS = ['dddd', 'blbb', 'aaaa']


def photographer():
    """Rig spec (chargen_body) of the press photographer."""
    import chargen_heads as HDS
    from chargen_body import Coat, Spec, make_hands
    from chargen_cast import EYE_B, GLASS, SKIN, boot_bitmaps, materials, side_light
    from chargen_cast_c3 import CHROME
    import characters_c4p2 as C5
    scene = 'c4p2_depot'
    mats, names = materials(scene, {
        'coat': '#3E3A34',
        'trouser': '#2A2826',
        'boot': ('#161210', {'glossy': True}),
        'patch': '#34302A',
        'hat': ['#14110E', '#211C17', '#2E2720', '#3C332A', '#4C4136', '#5E5244'],
        'band': ['#060606', '#0C0C0C', '#141414', '#1C1C1C', '#262626', '#303030'],
        'card': ['#8A867A', '#B4AE9E', '#D0CAB8', '#E2DCCB', '#EEEADC', '#FAF8F0'],
        'camera': ['#050506', '#0C0C0E', '#151518', '#202024', '#2E2E34', '#44444C'],
        'chrome': CHROME,
        'lens': ['#06080C', '#121820', '#22303E', '#3A5066', '#6A86A2', '#B8CCE0'],
        'strap': '#3A2A1C',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#5A2A26',
        'skin': SKIN['berlin'],
        'hair': '#3A3028',
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#16161A',
    })
    lg = HDS.base_legend()
    lg['c'] = ('card', 5)
    spec = Spec(id='photographer', scene=scene, mats=mats, names=names, light=side_light(), rim=C5.RIM_C4P2[scene],
                hip_h=22.4, torso=13.8, neck=1.4, thigh=10.4, shin=10.2,
                leg_r=(1.55, 1.4), arm_r=(1.55, 1.35), hip_f=1.8,
                coat=Coat(mat='coat', hem=-10.0, back=4.0, front=4.3, flare=0.8, chest=0.6, collar=1.4,
                          width_f=5.6, waist_f=4.8, hem_f=5.2, R=2.3, cyl=0.65, folds=0.7),
                heads=HDS.head_views(lg, PHOTOG_SIDE, None, side_talk={(8, 8): 'M'}),
                boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'), lean=0.4,
                style=dict(stride=4.6, swing=10.0, bob=1, walk_lean=0.5, lift=2.4, hem=0.5, idle_feet=(1.6, -1.2),
                           hold_n=(10.0, 70.0), arm_f_idle=(-2.0, 10.0), arm_n_idle=(10.0, 70.0),
                           gesture='one_drag', work='smoke',
                           talk_n=[(10.0, 70.0), (12.0, 76.0), (16.0, 86.0), (18.0, 90.0), (16.0, 84.0),
                                   (12.0, 74.0), (14.0, 80.0), (10.0, 70.0)],
                           talk_hand_n=['fist'] * 8))
    spec.hooks = {'side': [('coat', photographer_coat_side), ('front', photographer_rangefinder_side)]}
    return spec


def photographer_coat_side(fr, J, P, spec):
    """The coat open at the neck: the shirt, the loosened tie hanging askew, the coat's front edge, buttons."""
    from chargen_cast import buttons, column_line, put_line, put_poly
    body, T, c = J['body'], J['T'], spec.coat
    put_poly(fr, spec, [body(c.front - 1.6, T + 0.8), body(c.front - 0.1, T - 0.4), body(c.front - 0.2, T - 2.8),
                        body(c.front - 1.4, T - 2.4)], 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(c.front - 0.7, T - 1.2), body(c.front - 0.1, T - 3.2), 0.45, 'tie', tone=2, name='tie')
    column_line(fr, spec, J, c.front - 0.6, -10.0, T - 3.2, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 0.6, (T - 4.4, T - 7.6, -0.2), tone=1)


def photographer_rangefinder_side(fr, J, P, spec):
    """The rangefinder at his chest (black body, the chrome top plate, the lens a dark eye) on its strap."""
    from chargen_cast import bm, put_line
    from chargen_core import put_bitmap
    body, T, c = J['body'], J['T'], spec.coat
    put_line(fr, spec, body(c.front - 0.4, T - 3.4), body(c.front - 1.8, T + 0.4), 0.35, 'strap', tone=2,
             name='strap')
    lgd = {'a': ('camera', 1), 'b': ('camera', 2), 'd': ('chrome', 4), 'l': ('lens', 3)}
    x, y = body(c.front + 0.2, T - 3.6)
    put_bitmap(fr, bm(CAM_ROWS, lgd, anchor=(1, 0)), spec.names, x, y, name='camera')


def install():
    """Put the figures of this module into the game rig's cast (in memory, idempotent): the photographer."""
    import env_c4p2_cine_kit as K
    CH, CB, A, CC_ = K.rig()
    CH.CAST.setdefault('photographer', photographer)
    K.STANDINS.pop('photographer', None)


# ================================================================================================ Ilse, k1
ILSE_SIZE = (72, 26)


def ilse_asleep():
    """Ilse asleep on the leather offcuts of the cobbler's basement (LS_C4P2_Clock k1), 72 x 26 px, the candle to
    her left: curled on her side under the cobbler's big coat (its collar, the shoulder and hip under the cloth,
    the knees drawn up, a button, the hem with a fold), her head on a rolled leather apron, her plaits, the face
    in profile with the eye shut, one hand under her cheek, her stockinged feet out of the hem.  Painted flat at
    1:1 (the plate's scale: a head ~9 px), the candle's warm light on the upper edges.  Anchor: top-left."""
    import env_c4p2_cine_flat as FL
    w, h = ILSE_SIZE
    F = FL.Flat(w, h, bg='#000000')
    xx, yy = F.xx, F.yy
    # the leather roll under her head
    roll = F.ell(10, 20, 9, 4)
    F.fill(roll, '#5a3018')
    F.fill(roll & (yy < 18), '#8a5028')
    F.fill(roll & (yy < 17) & (xx < 12), '#b07038')
    F.fill(roll & F.line([(4, 22), (16, 22)], 0.5), '#3a1c0c')
    # the coat over her: shoulder (left), waist dip, hip, the knees drawn up (right), the hem with a fold
    coat = (F.ell(25, 17, 11, 7) | F.ell(43, 15, 10, 8) | F.ell(56, 17, 8, 6) | F.box(18, 18, 63, 24)) & (yy < 25)
    F.fill(coat, '#2a2420')
    F.fill(coat & (yy < 13) | (coat & F.ell(43, 12, 8, 4)), '#3a322a')
    F.fill(coat & F.ell(25, 13, 7, 3), '#3a322a')
    F.fill(FL.edge(coat, 't', 1) & (xx < 52), '#6a5038')
    F.fill(coat & F.line([(30, 20), (40, 16), (50, 18)], 0.5), '#1a1612')
    F.fill(coat & F.line([(46, 22), (58, 21)], 0.5), '#1a1612')
    F.fill(F.box(35, 18, 37, 20), '#8a7a5a')
    # the collar turned up round her neck
    col = F.poly([(15, 13), (21, 10), (24, 14), (20, 19), (15, 18)])
    F.fill(col, '#3e342a')
    F.fill(FL.edge(col, 't', 1), '#7a5c40')
    # stockinged feet out of the hem
    feet = F.ell(65, 21, 4, 2.2) | F.ell(66, 23.5, 3.5, 1.8)
    F.fill(feet, '#5a4a40')
    F.fill(feet & (yy < 21), '#7a6656')
    # head: hair with the plait over the roll, the face in profile turned up to the candle, the hand under it
    hair = F.ell(10, 12, 6, 5)
    F.fill(hair, '#6a3e1c')
    F.fill(hair & (yy < 10), '#8a5428')
    F.fill(hair & F.line([(6, 9), (12, 8)], 0.5), '#a86a34')
    plait = F.line([(6, 15), (3, 18), (2, 22)], 1.0)
    F.fill(plait, '#6a3e1c')
    F.fill(plait & (np.mod(yy, 2) == 0), '#8a5428')
    face = F.poly([(12, 9), (17, 10), (18, 13), (16, 16), (12, 16)]) & ~F.ell(7, 12, 4, 5)
    F.fill(face, '#c88a64')
    F.fill(face & (xx >= 16), '#e0a882')
    F.fill(F.box(14, 12, 16, 13), '#6a3a26')          # the shut eye: a short dark lash line
    F.fill(F.box(17, 13, 18, 14), '#e8b894')           # the nose tip catching the light
    F.fill(F.box(16, 15, 17, 16), '#9a5a44')           # the mouth
    hand = F.ell(15, 18, 3, 1.6)
    F.fill(hand, '#d09a74')
    F.fill(hand & (yy < 18), '#e8b894')
    mask = roll | coat | col | feet | hair | plait | face | hand
    F.outline(mask, col='#1a0e08')
    return F.rgba(mask | FL.edge(mask, 'all', 1))


def paint_into(F, rgba, x, y):
    """Composite an RGBA sprite into an env_c4p2_cine_flat.Flat canvas at (x, y) (alpha > 0 = covered)."""
    h, w = rgba.shape[:2]
    full = np.zeros((F.h, F.w, 3), np.float32)
    m = np.zeros((F.h, F.w), bool)
    x0, y0 = int(x) - F.g.ox, int(y) - F.g.oy
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(w, F.w - x0), min(h, F.h - y0)
    if ex <= sx0 or ey <= sy0:
        return m
    sub = rgba[sy0:ey, sx0:ex]
    m[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = sub[..., 3] > 0
    scale = 1.0 if F.rgb.dtype != np.uint8 and float(F.rgb.max()) > 1.5 else 1.0 / 255.0
    full[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = sub[..., :3].astype(np.float32) * scale
    F.fill(m, full.astype(F.rgb.dtype))
    return m


# ================================================================================================ extras
def window_figure(kind='stand', w=14, h=20, light='#f0b860', seed=0, face=1):
    """A person seen against a lit window from the street at night (for the places builder): a dark silhouette
    with a readable head, neck, shoulders and arms -- kind 'stand' (at the window, a shoulder turned), 'sit'
    (at a table, an elbow up, a cup), 'pair' (two heads, one leaning), 'lean' (both hands on the sill, looking
    down at the yard), 'curtain' (half hidden behind a drawn curtain's edge, the hand on it).  w x h RGBA, the
    figure's own colour a deep warm-dark, its edges one step lighter on the lamp side (face = +1: the light is
    behind-right).  Composite it over the window's glow before the window frame is drawn."""
    import env_c4p2_cine_flat as FL
    F = FL.Flat(w, h, bg='#000000')
    xx, yy = F.xx, F.yy
    rng = np.random.default_rng(seed)
    cx = w / 2.0 + rng.uniform(-1.0, 1.0)
    hr = max(2.0, h * 0.13)

    def bust(x, top, turn=0.0):
        """Head (a little turned), neck, the slope of the shoulders down to the frame's bottom -- one piece."""
        head = F.ell(x + turn * hr * 0.25, top + hr, hr * 0.86, hr * 1.04)
        neck = F.poly([(x - hr * 0.42, top + hr * 1.5), (x + hr * 0.42, top + hr * 1.5),
                       (x + hr * 0.62, top + hr * 2.25), (x - hr * 0.62, top + hr * 2.25)])
        sh = F.poly([(x - hr * 0.75, top + hr * 2.0), (x + hr * 0.75, top + hr * 2.0), (x + hr * 2.0, top + hr * 2.7),
                     (x + hr * 2.3, top + hr * 3.4), (x + hr * 2.4, h), (x - hr * 2.4, h), (x - hr * 2.3, top + hr * 3.4),
                     (x - hr * 2.0, top + hr * 2.7)])
        return head | neck | sh

    parts = []
    if kind in ('stand', 'curtain', 'lean'):
        top = h * 0.18
        parts.append(bust(cx, top, face * (1.0 if kind != 'lean' else 0.4)))
        if kind == 'lean':
            # round 11c (Clock k1: the bent-over version read as a seated lump): a woman standing at the window,
            # her hair up in a bun, leaning a little on the sill -- the elbows out, both hands on the sill
            parts.append(F.ell(cx + face * hr * 0.15, top + hr * 0.05, hr * 0.48, hr * 0.42))
            for s in (-1, 1):
                parts.append(F.line([(cx + s * hr * 2.2, top + hr * 3.1), (cx + s * hr * 2.75, h - hr * 1.2),
                                     (cx + s * hr * 1.5, h - 1.0)], hr * 0.42))
        if kind == 'curtain':
            # the curtain's edge in the hand: the hand up at shoulder height on the lamp-away side
            parts.append(F.line([(cx - face * hr * 2.1, top + hr * 3.0), (cx - face * hr * 2.7, top + hr * 2.0)],
                                hr * 0.45))
            parts.append(F.ell(cx - face * hr * 2.8, top + hr * 1.8, hr * 0.42, hr * 0.5))
    elif kind == 'sit':
        top = h * 0.34
        parts.append(bust(cx, top, face))
        # a cup at the mouth: the elbow out and down, the forearm up, the hand and cup by the chin
        parts.append(F.line([(cx + face * hr * 2.0, top + hr * 2.9), (cx + face * hr * 2.5, top + hr * 4.1),
                             (cx + face * hr * 1.3, top + hr * 2.1)], hr * 0.42))
        parts.append(F.box(cx + face * hr * 0.9 - (hr * 0.8 if face < 0 else 0.0), top + hr * 1.4,
                           cx + face * hr * 0.9 + (hr * 0.8 if face > 0 else 0.0), top + hr * 2.1))
    else:                                   # pair: one turned to the other, a little lower
        parts.append(bust(cx - hr * 1.7, h * 0.20, 1.0))
        parts.append(bust(cx + hr * 1.6, h * 0.28, -1.0))
    m = np.zeros((h, w), bool)
    for p in parts:
        m |= p
    F.fill(m, '#1a1210')
    lit = FL.edge(m, 'r' if face > 0 else 'l', 1) | FL.edge(m, 't', 1)
    F.fill(lit & m, FL.hx(light) * 0.35 + FL.hx('#1a1210') * 0.65)
    return F.rgba(m)


def far_figure(kind='walk', h=12, coat='#2a2a30', frames=2, face=1, light=None, hat='cap', seed=0):
    """A far figure (h 9..20 px tall) for the wide plates (for the places builder): kind 'walk' (a 2-frame stride,
    the coat's hem swinging), 'stand', 'guard' (a long greatcoat, the rifle's barrel above the shoulder, the cap
    with ear flaps), 'carry' (a case or a bundle in the near hand), 'lead' (an arm out, as if guiding someone).
    hat 'cap' | 'ushanka' | 'hat' | 'kerchief' | None.  Returns an RGBA sheet of `frames` cells (w = h * 0.8, at
    least 8 px), the feet on the bottom row, facing +x when face = 1; light = (side, hex) puts a one-pixel rim
    of a lamp's colour on that side."""
    import env_c4p2_cine_flat as FL
    cw = max(8, int(round(h * 0.8)))
    cells = []
    for f in range(frames):
        F = FL.Flat(cw, h, bg='#000000')
        cx = cw / 2.0
        u = h / 12.0
        hr = 1.25 * u
        head_y = 1.6 * u + (0.0 if f % 2 == 0 or kind not in ('walk', 'carry', 'lead') else 0.4 * u)
        head = F.ell(cx + 0.3 * face * u, head_y + hr, hr, hr)
        sh_y = head_y + 2.4 * hr
        hem_y = h - 3.2 * u if kind != 'guard' else h - 2.0 * u
        swing = (0.8 * u if f % 2 else -0.8 * u) if kind in ('walk', 'carry', 'lead') else 0.0
        body = F.poly([(cx - 1.5 * u, sh_y), (cx + 1.5 * u, sh_y), (cx + 2.0 * u + swing * 0.3, hem_y),
                       (cx - 2.0 * u + swing * 0.3, hem_y)])
        legs = (F.line([(cx - 0.6 * u, hem_y - 0.4), (cx - 0.6 * u - swing, h - 1.0)], 0.55 * u) |
                F.line([(cx + 0.6 * u, hem_y - 0.4), (cx + 0.6 * u + swing, h - 1.0)], 0.55 * u))
        arm = F.line([(cx + face * 1.2 * u, sh_y + 0.6 * u), (cx + face * (1.6 * u - swing * 0.6), sh_y + 3.6 * u)],
                     0.5 * u)
        m = head | body | legs | arm
        if kind == 'guard':
            m |= F.line([(cx - face * 1.4 * u, sh_y + 2.6 * u), (cx - face * 0.4 * u, sh_y - 2.6 * u)], 0.35 * u)
        if kind == 'carry':
            m |= F.box(cx + face * 1.2 * u, sh_y + 3.4 * u, cx + face * 3.0 * u, sh_y + 4.8 * u)
        if kind == 'lead':
            m |= F.line([(cx + face * 1.2 * u, sh_y + 0.8 * u), (cx + face * 3.4 * u, sh_y + 1.6 * u)], 0.5 * u)
        if hat == 'cap' or hat == 'ushanka':
            m |= F.ell(cx + 0.2 * face * u, head_y + hr * 0.5, hr * 1.15, hr * 0.7)
            if hat == 'ushanka':
                m |= F.box(cx - hr * 1.1, head_y + hr * 0.6, cx + hr * 1.1, head_y + hr * 1.8)
        elif hat == 'hat':
            m |= F.box(cx - hr * 1.6, head_y + hr * 0.3, cx + hr * 1.6, head_y + hr * 0.7)
            m |= F.ell(cx, head_y + hr * 0.1, hr * 0.95, hr * 0.7)
        elif hat == 'kerchief':
            m |= F.ell(cx - 0.2 * face * u, head_y + hr * 0.9, hr * 1.15, hr * 1.1)
        F.fill(m, coat)
        F.fill(head & ~F.ell(cx + 0.2 * face * u, head_y + hr * 0.5, hr * 1.15, hr * 0.8) &
               (F.xx * face > (cx + 0.2 * face * u) * face), '#9a7a64')
        F.fill(legs & (F.yy > h - 2.0), '#14110e')
        if light is not None:
            side, col = light
            F.fill(FL.edge(m, side[0], 1) & m, col)
        cells.append(F.rgba(m))
    return np.concatenate(cells, axis=1)


def passerby_sheet(cid='clerk', flip=False, n=None, key='left', mul=(1.0, 1.0, 1.0), rim=None, walk=True):
    """A passer-by on the game's rig at the plates' 32-px scale (for the places builder): `cid` any rig cast id
    (clerk, babushka, worker_a/b, porter, berlin_mother, berlin_father, berlin_child, guard_karsk, photographer
    ...), walking (the rig's walk cycle) or idling, graded like env_c4p2_cine_people.sheet -> (sheet, n, 32)."""
    import env_c4p2_cine_kit as K
    import env_c4p2_cine_people as PP
    install()
    CH, CB, A, CC_ = K.rig()
    spec, used = K.spec_of(cid, 'worker_b')
    poses = A.walk_side(spec.style) if walk else A.idle_side(spec.style)
    if n:
        poses = poses[:n]
    return PP.sheet(cid, poses, [], 32, flip, key=key, mul=mul, rim=rim)
