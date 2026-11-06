"""env_veltrava_cine_figs -- the two protagonists for the Chapter-3 cinematics (owner: cinematics stream).

The close figures are sculpted and lit with the signed-distance pipeline of the dialogue busts
(chargen_portrait2_*: anatomy, hats, hair, garments, sphere tracer, material ramps; imported read-only,
nothing there is modified) so that Konrad and Alexei keep the faces, hats and coats the player knows:

  back_konrad / back_alexei   seated at the compartment window, seen from behind, lit by the reading lamp
                              (key) and the cold window (rim); two head poses
  face_konrad / face_alexei   the same men seen from the front, lit from below by the lamp: the source of
                              their reflections in the black window glass (posterised, additive)
  walk_konrad                 Konrad in profile walking right (the foreground silhouette under the palais clock)

Everything is deterministic numpy (fixed seeds, no image inputs).  The trace is slow (~10-25 s per image),
so results are memoised per process.
"""
from __future__ import annotations

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
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402

E = S.Ellipsoid
C0 = np.array([56.0, 56.0, 0.0])        # zoom centre used by the bust tone passes (_local)
_memo: dict = {}


class _Hit:
    def __init__(self, hit):
        self.hit = hit


def _disk_key(cache_key, args):
    """Content key of a render: the sources of the sculpting/painting pipeline + this call's arguments.
    The disk cache only skips recomputation (results are byte-identical); ASHES_NO_CACHE=1 disables it."""
    import hashlib
    h = hashlib.sha1()
    for f in ('chargen_portrait2_anat.py', 'chargen_portrait2_cast.py', 'chargen_portrait2_paint.py',
              'chargen_portrait2_sdf.py', 'env_veltrava_cine_figs.py'):
        with open(os.path.join(HERE, f), 'rb') as fh:
            h.update(fh.read())
    h.update(repr((cache_key, args)).encode('utf-8'))
    return h.hexdigest()[:20]


def _cache_dir():
    import tempfile
    d = os.path.join(tempfile.gettempdir(), 'ashes_c3cine_cache')
    os.makedirs(d, exist_ok=True)
    return d


def _pre(px, zoom):
    """Pixel position -> pre-zoom scene coordinates (the scene is scaled about C0)."""
    p = np.asarray(px, float)
    out = (p - C0[:len(p)]) / zoom + C0[:len(p)]
    return tuple(out)


# ----------------------------------------------------------------------------------- body parts
def seated_torso(M, mat='body', width=1.0, depth=1.0, slope=1.0, arm_out=1.0, lean=0.0, arm_l=None, arm_r=None):
    """Shoulders + chest (bust torso) + the back down to the waist and both arms of a man sitting at a
    table, torso-local frame (origin at the pit of the neck, y down, z forward = towards the table)."""
    m = M(mat)
    base = A.build_torso(M, mat, width, depth, slope)
    w = width
    parts = [base,
             E((0.0, 52.0, -1.0 + lean), (24.0 * w, 26.0, 13.0 * depth), m),          # lower back / belly
             E((0.0, 76.0, 0.0 + lean * 1.4), (23.0 * w, 16.0, 14.0 * depth), m)]     # hips on the seat
    for sgn, spec in ((-1, arm_l), (1, arm_r)):
        sh = (sgn * 27.0 * w, 20.0, -3.0)
        el = spec[0] if spec else (sgn * 31.0 * w * arm_out, 58.0, 4.0)
        hd = spec[1] if spec else (sgn * 22.0 * w, 66.0, 30.0)
        parts.append(S.RoundCone(sh, el, 8.6, 6.6, m))                                 # upper arm
        parts.append(S.RoundCone(el, hd, 6.4, 4.6, m))                                 # forearm on the table
    return S.Union(parts, k=6.0)


def band_back(M, torso_node, lift, p0, angle_deg, width, mat, y_range=None):
    """Like chargen_portrait2_cast.band_on, but on the BACK of the torso (z < -2): a satchel strap seen
    from behind."""
    m = M(mat)
    a = np.radians(angle_deg)
    n = np.array([-np.sin(a), np.cos(a)])

    def region(P):
        dd = np.abs((P[:, 0] - p0[0]) * n[0] + (P[:, 1] - p0[1]) * n[1]) - width / 2
        dd = np.maximum(dd, P[:, 2] + 2.0)
        if y_range is not None:
            dd = np.maximum(dd, np.maximum(y_range[0] - P[:, 1], P[:, 1] - y_range[1]))
        return dd

    return S.Inter(S.Offset(torso_node, lift, m), S.Fn(region, m))


def pass_hair_back(mat='hair', seed=19):
    """Hair seen from behind: sparse, slightly slanted darker strands running down to the nape."""
    def fn(spec, G, tone, v):
        M = G['M']
        if mat not in M.names:
            return tone
        m = (G['d'].mat == M.names.index(mat)) & (tone >= 1)
        if not m.any():
            return tone
        L = CC._local(G, 'hf', m)
        k = np.floor(L[:, 0] * 0.55 + L[:, 1] * 0.10).astype(int)
        r = CC._hash2(k, np.zeros_like(k), seed)
        t = tone[m].copy()
        t = np.where((r < 0.16) & (t >= 2), t - 1, np.where(r > 0.94, t + 1, t))
        tone = tone.copy()
        tone[m] = t
        return tone
    return fn


def nape_hair(M, hp, c=(0.0, 7.0, -9.5), r=(12.0, 7.5, 8.0), mat='hair'):
    """Short hair over the back of the neck (the bust hair stops where the front view needs it)."""
    return E(c, r, M(mat))


def _scene(spec, zoom, head_px, torso_px, yaw, pitch, roll, torso_yaw, torso_pitch, torso_kw, head_items,
           torso_items, size):
    M = A.Mats()
    for nm in spec.get('mat_order', ()):
        M(nm)
    hp = A.head_params(**spec['head'])
    head, lm = A.build_head(hp, M, jaw_open=0.0)
    items, clips, solid = [], [], []
    for f in head_items:
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
    items = [body] + solid
    hpos = _pre(head_px + (0.0,), zoom)
    tpos = _pre(torso_px + (0.0,), zoom)
    hf = S.Frame(hpos, S.rot(yaw, pitch, roll))
    torso = seated_torso(M, **torso_kw) if torso_kw is not None else A.build_torso(M, **spec.get('torso', {}))
    t_items = [f(M, torso) for f in torso_items]
    tf = S.Frame(tpos, S.rot(torso_yaw, torso_pitch, 0))
    hnode = S.Bound(S.Xform(S.Union(items), frame=hf), np.array(hpos) + np.array([0, -7.0, 0]), 48.0, margin=3.0)
    reach = 120.0 if torso_kw is not None else 58.0
    tnode = S.Bound(S.Xform(S.Union([torso] + t_items), frame=tf), np.array(tpos) + np.array([0, 40.0, 0]),
                    reach, margin=3.0)
    root = S.Scale(S.Union([hnode, tnode]), C0, zoom)
    return root, M, hp, lm, hf, tf


def render(spec, size, zoom, head_px, torso_px, yaw, pitch=0.0, roll=0.0, torso_yaw=0.0, torso_pitch=0.0,
           look=None, torso_kw=None, head_items=None, torso_items=None, styles=None, tone_passes=None,
           outline=True, rim=True, key_cut=None, cache_key=None):
    """Trace + paint one figure image -> dict(rgba, mat, names, key, rim, d)."""
    if cache_key is not None and cache_key in _memo:
        return _memo[cache_key]
    disk = None
    if cache_key is not None and os.environ.get('ASHES_NO_CACHE') != '1':
        disk = os.path.join(_cache_dir(), _disk_key(cache_key, (size, zoom, head_px, torso_px, yaw, pitch, roll,
                                                                torso_yaw, torso_pitch, look, torso_kw)) + '.npz')
        if os.path.exists(disk):
            z = np.load(disk, allow_pickle=False)
            res = dict(rgba=z['rgba'], mat=z['mat'], names=[str(n) for n in z['names']], key=z['key'], rim=z['rim'],
                       d=_Hit(z['hit']), v=z['v'])
            _memo[cache_key] = res
            return res
    w, h = size
    root, M, hp, lm, hf, tf = _scene(spec, zoom, head_px, torso_px, yaw, pitch, roll, torso_yaw, torso_pitch,
                                     torso_kw, head_items if head_items is not None else spec['head_items'],
                                     torso_items if torso_items is not None else spec['torso_items'], size)
    lk = P.Look(**(look or spec['look']))
    g = S.trace(root, w, h, ss=3, key=lk.key)
    pri = [spec.get('priority', {}).get(n, 0) for n in M.names]
    d = S.downsample(g, len(M), priority=pri)
    G = dict(d=d, M=M, hp=hp, lm=lm, hf=hf, tf=tf, look=lk, jaw=0.0, zoom=zoom)
    st = dict(spec['styles'])
    if styles:
        st.update(styles)
    names = M.names
    v, rimv, keyv = P.light_value(d, lk, st, names)
    if key_cut is not None:
        v = key_cut(v, d, M)
    v = P.smooth_by_material(v, d.mat, passes=spec.get('smooth', 1))
    tone = P.quantise(d, v, st, names)
    for fn in (tone_passes if tone_passes is not None else spec.get('tone_passes', ())):
        tone = fn(spec, G, tone, v)
    tone = P.clean(tone, d.mat)
    rgb = P.colorize(d, tone, st, names)
    if outline:
        rgb = P.outline(rgb, d, st, names, look=lk)
        rgb, _ = P.depth_lines(rgb, d, st, names, spec['groups'], skip=spec.get('no_depth_line', ()))
    if rim:
        rgb = P.apply_rim(rgb, d, rimv, keyv, st, names, tone)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    res = dict(rgba=out, mat=d.mat, names=list(names), key=keyv, rim=rimv, d=d, v=v)
    if cache_key is not None:
        _memo[cache_key] = res
    if disk is not None:
        np.savez(disk, rgba=out, mat=d.mat, names=np.array(list(names)), key=keyv, rim=rimv, hit=d.hit, v=v)
    return res


def mat_mask(res, *names):
    m = np.zeros(res['mat'].shape, bool)
    for n in names:
        if n in res['names']:
            m |= res['mat'] == res['names'].index(n)
    return m


# ----------------------------------------------------------------------------------- styles
def _warm(base, warm_tail):
    """Ramp whose upper (lamp-lit) steps turn warm: base dark steps + warm_tail."""
    return ramp(*(list(base) + list(warm_tail)))


def konrad_train_styles():
    th7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]
    return {
        'coat': MatStyle(_warm(['#05070d', '#0a0f1d', '#10182b', '#18233c', '#23304f'],
                               ['#3c3a52', '#5e4b52', '#86624f']), th7, dither=0.02, rim='#56769c'),
        'coat_lapel': MatStyle(_warm(['#05070d', '#0a0f1d', '#10182b', '#18233c', '#23304f'],
                                     ['#3c3a52', '#5e4b52', '#86624f']), th7, rim='#56769c'),
        'felt': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840', '#7e6450',
                              '#a07c5c'), th7, dither=0.04, rim='#5a7590'),
        'brim': MatStyle(ramp('#07080d', '#111118', '#1c1b23', '#2a2730', '#3d3436', '#5a4840', '#7e6450',
                              '#a07c5c'), th7, rim='#5a7590'),
        'hair': MatStyle(ramp('#07080d', '#100e13', '#1a1518', '#261d1f', '#3a2a26', '#5a3e2e'),
                         [0.05, 0.12, 0.24, 0.40, 0.60], rim='#4a5f74'),
        'scarf': MatStyle(ramp('#0e0c0e', '#1f1a1b', '#352d2a', '#504536', '#6c5a40', '#93754c', '#b99159',
                               '#d6ad6c'), th7, dither=0.03, rim='#7f93a0'),
    }


def alexei_train_styles():
    th7 = [0.03, 0.07, 0.13, 0.22, 0.34, 0.50, 0.70]
    green = ['#050a09', '#0b1512', '#12201a', '#1b2c23', '#26392d']
    return {
        'coat': MatStyle(_warm(green, ['#3d4630', '#5d5a3a', '#867548']), th7, dither=0.05, rim='#5f8a84'),
        'coat_lapel': MatStyle(_warm(green, ['#3d4630', '#5d5a3a', '#867548']), th7, rim='#5f8a84'),
        'fur': MatStyle(ramp('#0b0a0c', '#191615', '#2a2420', '#3f362e', '#574b3f', '#7a6247', '#9c7d58',
                             '#bb9a6e'), th7, dither=0.06, rim='#7d9a92'),
        'hat_top': MatStyle(ramp('#0a0909', '#161312', '#221d1a', '#312a25', '#4a3a2c', '#665038'),
                            [0.05, 0.12, 0.24, 0.40, 0.6], rim='#5f7a76'),
        'hair': MatStyle(ramp('#0b0a0b', '#1b1614', '#2d241e', '#45372b', '#644a32', '#866340'),
                         [0.04, 0.10, 0.2, 0.34, 0.52], rim='#6b8a84'),
        'knit': MatStyle(ramp('#0a0b0d', '#16181c', '#24272c', '#353940', '#4f4c4a', '#6e6457', '#8f7f68'),
                         [0.04, 0.10, 0.2, 0.32, 0.48, 0.68], dither=0.03, rim='#6f8c88'),
    }


# ----------------------------------------------------------------------------------- figures
def back_konrad(turn=0):
    """Konrad at the window of the saloon car, seen from behind-right: hat, the back of his head with the
    lamp-lit edge of his left cheek, coat collar turned up, scarf; turn 1 = his head a little more toward the
    glass (the reflection)."""
    spec = CC.konrad()
    look = dict(key=(-0.78, 0.40, -0.48), rim=(0.05, -0.62, -0.78), ambient=0.06, wrap=0.10, bg='berlin',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2),
                  lambda M, hp: CC.hair_short(M, hp, nape=13.5, back_z=-11.0, thick=1.2),
                  lambda M, hp: nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0, collar_h=15.0, collar_r=(12.4, 14.8)),
                   lambda M, t: CC.scarf_wrap(M, y=-9.0, r=11.2, tube=5.0, ends='drape')]
    yaw = 198.0 + (9.0 if turn else 0.0)
    return render(spec, (200, 232), 1.62, (82.0, 58.0), (84.0, 100.0), yaw, pitch=4.0 + (2.0 if turn else 0.0),
                  roll=0.0, torso_yaw=192.0, torso_pitch=6.0, look=look,
                  torso_kw=dict(width=0.96, depth=1.0, slope=1.25, arm_out=1.05, lean=2.0,
                                arm_l=((-29.0, 54.0, 8.0), (-12.0, 50.0, 34.0)),
                                arm_r=((29.0, 56.0, 8.0), (12.0, 52.0, 34.0))),
                  head_items=head_items, torso_items=torso_items, styles=konrad_train_styles(),
                  tone_passes=[CC.pass_knit('scarf'), CC.pass_grain('felt', 0.07, seed=3),
                               CC.pass_grain('coat', 0.04, seed=4), pass_hair_back('hair')],
                  cache_key=('back_konrad', turn))


def back_alexei(turn=0):
    """Alexei at the window of the Soviet compartment, seen from behind-left, the wall lamp at the right."""
    spec = CC.alexei()
    look = dict(key=(0.80, 0.25, -0.55), rim=(-0.05, -0.62, -0.78), ambient=0.06, wrap=0.10, bg='karsk',
                glow=(0.8, 0.2), fill=0.08, fill_dir=(-0.2, -0.8, 0.6), ao=0.5)
    head_items = [lambda M, hp: CC.ushanka(M, hp, flaps='down'),
                  lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0, nape=13.0,
                                              back_z=-11.0, thick=1.2),
                  lambda M, hp: nape_hair(M, hp)]
    torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                               collar_h=12.0, collar_r=(13.4, 14.8)),
                   lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8)),
                   lambda M, t: band_back(M, t, 3.4, (6.0, 30.0), 50.0, 3.0, 'strap', y_range=(8.0, 92.0))]
    yaw = 160.0 - (9.0 if turn else 0.0)
    return render(spec, (220, 232), 1.62, (118.0, 60.0), (114.0, 102.0), yaw, pitch=4.0 + (2.0 if turn else 0.0),
                  roll=0.0, torso_yaw=168.0, torso_pitch=6.0, look=look,
                  torso_kw=dict(width=1.05, depth=1.05, slope=1.0, arm_out=1.05, lean=2.0,
                                arm_l=((-30.0, 56.0, 8.0), (-12.0, 52.0, 34.0)),
                                arm_r=((30.0, 54.0, 8.0), (12.0, 50.0, 34.0))),
                  head_items=head_items, torso_items=torso_items, styles=alexei_train_styles(),
                  tone_passes=[CC.pass_fur('fur'), CC.pass_stitches('coat', 5.0), pass_hair_back('hair'),
                               CC.pass_knit('knit', ribs=30)],
                  cache_key=('back_alexei', turn))


def face_konrad(turn=0):
    """Konrad's face as the black glass mirrors it: frontal, lit from below by the table lamp."""
    spec = CC.konrad()
    look = dict(key=(-0.35, 0.75, 0.55), rim=(0.6, -0.3, -0.5), ambient=0.05, wrap=0.12, bg='berlin',
                glow=(0.8, 0.2), fill=0.03, fill_dir=(0.0, 0.0, 1.0), ao=0.5)
    return render(spec, (60, 76), 0.82, (30.0, 34.0), (31.0, 58.0), 8.0 + (6.0 if turn else 0.0), pitch=-2.0,
                  torso_yaw=6.0, look=look, outline=False, rim=False, cache_key=('face_konrad', turn))


def face_alexei(turn=0):
    spec = CC.alexei()
    look = dict(key=(0.55, 0.55, 0.62), rim=(-0.6, -0.3, -0.5), ambient=0.05, wrap=0.12, bg='karsk',
                glow=(0.8, 0.2), fill=0.03, fill_dir=(0.0, 0.0, 1.0), ao=0.5)
    return render(spec, (62, 78), 0.82, (31.0, 35.0), (31.0, 59.0), -10.0 - (6.0 if turn else 0.0), pitch=-2.0,
                  torso_yaw=-6.0, look=look, outline=False, rim=False, cache_key=('face_alexei', turn))


def reflection(res, tint, gain=1.0, levels=5, mirror=True):
    """A rendered figure -> dim additive RGB(A) reflection: value from the light field, posterised in a few
    dithered steps, tinted (warm lamp light in a black window)."""
    v = np.clip(res['v'], 0, 1) * res['d'].hit
    h, w = v.shape
    yy, xx = np.mgrid[0:h, 0:w]
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
    th = bay[yy % 4, xx % 4]
    q = np.floor(np.clip(v * gain, 0, 1) * levels + th) / levels
    out = np.zeros((h, w, 4), np.uint8)
    for c in range(3):
        out[..., c] = np.clip(q * tint[c], 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    if mirror:
        out = out[:, ::-1].copy()
    return out
