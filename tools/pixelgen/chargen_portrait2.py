"""chargen_portrait2 -- second-generation dialogue portraits (112x112 busts shown x3 in the DialogueBox).

    py -3 -P tools/pixelgen/chargen_portrait2.py                 # all speakers (+ previews)
    py -3 -P tools/pixelgen/chargen_portrait2.py konrad irina    # some speakers
    py -3 -P tools/pixelgen/chargen_portrait2.py --preview konrad # only preview sheets (no asset writes)
    py -3 -P tools/pixelgen/chargen_portrait2.py --jobs=8         # one process per speaker (same output)
    py -3 -P tools/pixelgen/chargen_portrait2.py --out=DIR        # review run into DIR (an assets/characters dir)

Pipeline per frame (deterministic numpy, no image inputs, no AI):
  1. sculpt   -- signed-distance head (chargen_portrait2_anat), hats / hair / garments (chargen_portrait2_cast)
                 in head- and torso-local frames; the jaw group rotates for the talking frames.
  2. trace    -- orthographic sphere tracing at 3x3 super-sampling (normals, soft key shadow, occlusion),
                 collapsed to final pixels by material majority (chargen_portrait2_sdf).
  3. paint    -- key / ambient / rim light posterised onto hand-picked hue-shifted ramps, cluster cleanup,
                 selective outline + depth-break lines, painted background (chargen_portrait2_paint).
  4. features -- hand-designed eye stamps (near/far eye x expression, open/closed), parametric brows and
                 mouths (rest / half / open), nostrils, ears, age lines, stubble (chargen_portrait2_face).

Outputs per speaker in assets/characters/<id>/:
  portrait.png       4 x 112 strip (or one frame per expression) = the REST frames (old contract, unchanged)
  portrait_anim.png  grid: columns = expressions (same order), rows = ANIM_ROWS
  portrait.json      {"size", "expressions", "anim": {...}} -- documented in documentation/asset_manifest_parts/portraits.md
"""
from __future__ import annotations

import json
import os
import sys
import time
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import chargen_portrait2_anat as A   # noqa: E402
import chargen_portrait2_cast as C   # noqa: E402
import chargen_portrait_c3 as C3     # noqa: E402,F401  registers the Chapter-3 speakers in C.CAST
import chargen_portrait2_face as FC  # noqa: E402
import chargen_portrait2_paint as P  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CHAR_DIR = os.path.join(ROOT, 'assets', 'characters')
PREV_DIR = os.path.join(CHAR_DIR, '_preview')
SIZE = 112
SS = 3
EXPRESSIONS = ['neutral', 'concerned', 'determined', 'surprised']
ANIM_ROWS = ['rest', 'talk_half', 'talk_open', 'blink', 'blink_talk_half', 'blink_talk_open']
MOUTH_OF_ROW = {'rest': 'rest', 'talk_half': 'half', 'talk_open': 'open', 'blink': 'rest',
                'blink_talk_half': 'half', 'blink_talk_open': 'open'}
JAW = {'rest': 0.0, 'half': 2.4, 'open': 5.0}

_cache: dict = {}


def seed_of(*parts):
    return zlib.crc32('/'.join(str(p) for p in parts).encode('utf-8')) & 0x7FFFFFFF


# ------------------------------------------------------------------------------------------- scene
def build_scene(spec, expr, jaw):
    M = A.Mats()
    for nm in spec.get('mat_order', ()):
        M(nm)
    hp = A.head_params(**spec['head'])
    head, lm = A.build_head(hp, M, jaw_open=jaw)
    items, clips, solid = [], [], []
    for f in spec['head_items']:
        r = f(M, hp)
        if isinstance(r, dict):
            solid.append(r['node'])
            if r.get('clip') is not None:
                clips.append(r['clip'])
            if r.get('soft') is not None:      # items that must be clipped like the head (hair)
                items.append(r['soft'])
        else:
            items.append(r)
    body = S.Union([head] + items)
    for c in clips:
        body = S.Inter(body, c)
    items = [body] + solid
    dy, dp, dr = spec['poses'].get(expr, (0, 0, 0))
    hf = S.Frame(spec['head_pos'], S.rot(spec['yaw'] + dy, spec['pitch'] + dp, spec['roll'] + dr))
    torso = A.build_torso(M, **spec.get('torso', {}))
    t_items = [f(M, torso) for f in spec['torso_items']]
    tf = S.Frame(spec['torso_pos'], S.rot(spec['torso_yaw'], 0, 0))
    hnode = S.Bound(S.Xform(S.Union(items), frame=hf), np.array(spec['head_pos']) + np.array([0, -7.0, 0]),
                    46.0, margin=3.0)
    tnode = S.Bound(S.Xform(S.Union([torso] + t_items), frame=tf),
                    np.array(spec['torso_pos']) + np.array([0, 22.0, 0]), 58.0, margin=3.0)
    root = S.Union([hnode, tnode])
    z = spec.get('zoom', 1.0)
    if z != 1.0:
        root = S.Scale(root, (SIZE / 2, SIZE / 2, 0.0), z)
    return root, M, hp, lm, hf, tf


def zoom_pt(spec, p):
    z = spec.get('zoom', 1.0)
    c = np.array([SIZE / 2, SIZE / 2, 0.0])
    return c + (np.asarray(p, float) - c) * z


def gbuffer(spec, expr, mouth_state):
    jaw = JAW[mouth_state] + spec.get('jaw_rest', {}).get(expr, 0.0)
    key = (spec['id'], expr, round(jaw, 3))
    if key in _cache:
        return _cache[key]
    root, M, hp, lm, hf, tf = build_scene(spec, expr, jaw)
    look = P.Look(**spec['look'])
    g = S.trace(root, SIZE, SIZE, ss=SS, key=look.key)
    pri = [spec.get('priority', {}).get(n, 0) for n in M.names]
    d = S.downsample(g, len(M), priority=pri)
    lmv = {k: zoom_pt(spec, hf.to_view(p)) for k, p in lm.items()}
    out = dict(d=d, M=M, hp=hp, lm=lm, lmv=lmv, hf=hf, tf=tf, look=look, jaw=jaw, zoom=spec.get('zoom', 1.0))
    _cache[key] = out
    return out


# ------------------------------------------------------------------------------------------- frame
def render(spec, expr, row):
    mouth_state = MOUTH_OF_ROW[row]
    blink = row.startswith('blink')
    G = gbuffer(spec, expr, mouth_state)
    d, M, look = G['d'], G['M'], G['look']
    styles = spec['styles']
    names = M.names
    v, rim, key = P.light_value(d, look, styles, names)
    v = P.smooth_by_material(v, d.mat, passes=spec.get('smooth', 1))
    tone = P.quantise(d, v, styles, names)
    for fn in spec.get('tone_passes', ()):
        tone = fn(spec, G, tone, v)
    skin_ids = [M.names.index(n) for n in spec['skin'] if n in M.names]
    cv = FC.Canvas(tone, d.mat, skin_ids)
    draw_features(spec, G, cv, expr, mouth_state, blink, v)
    tone = P.clean(cv.tone, d.mat, protect=cv.locked)
    rgb = P.colorize(d, tone, styles, names)
    rgb = P.outline(rgb, d, styles, names, look=look)
    rgb, _ = P.depth_lines(rgb, d, styles, names, spec['groups'], skip=spec.get('no_depth_line', ()))
    rgb = P.apply_rim(rgb, d, rim, key, styles, names, tone)
    paint_abs(spec, cv, rgb, v)
    for fn in spec.get('rgb_passes', ()):
        rgb = fn(spec, G, rgb, v, expr, row)
    bg = P.background(SIZE, SIZE, look, seed=seed_of(spec['id'], 'bg'))
    out = np.where(d.hit[..., None], rgb, bg)
    for fn in spec.get('final_passes', ()):
        out = fn(spec, G, out, expr, row)
    return out


def paint_abs(spec, cv, rgb, v):
    eye, br, mo = spec['eye'], spec['brow'], spec['mouth']
    lit = v > spec.get('eye_lit_th', 0.30)
    pal = {
        'K': (eye['lash'], eye['lash']), 'k': (eye.get('lash_soft', eye['lash']),) * 2,
        'W': (eye['sclera'], eye['sclera_d']), 'w': (eye['sclera_d'], eye.get('sclera_dd', eye['sclera_d'])),
        'I': (eye['iris'], eye['iris_d']), 'i': (eye['iris_d'], eye['iris_d']),
        'P': (eye['pupil'], eye['pupil']), 'H': (eye['catch'], eye.get('catch_d', eye['catch'])),
        'b': (br['col_l'], br['col']), 'B': (br['col'], br['col']),
        'M': (mo['line'], mo['line']), 'm': (mo['corner'], mo['corner']), 'O': (mo['inner'], mo['inner']),
        'T': (mo['teeth'], mo.get('teeth_d', mo['teeth'])), 'Q': (mo['tongue'], mo['tongue']),
    }
    pal.update(spec.get('abs_extra', {}))
    for (x, y), k in cv.abs.items():
        if k not in pal:
            continue
        c = pal[k][0] if lit[y, x] else pal[k][1]
        rgb[y, x] = P.hexc(c) if isinstance(c, str) else c


def ipt(p):
    return int(np.floor(p[0])), int(np.floor(p[1]))


def draw_features(spec, G, cv, expr, mouth_state, blink, v):
    lmv = G['lmv']
    F = spec.get('features', {})
    hf = G['hf']
    eyes_tab = F.get('eyes', FC.EYES)
    # ---- eyes
    ex, ey = ipt(lmv['eye_r'])
    fx, fy = ipt(lmv['eye_l'])
    off = F.get('eye_off', ((0, 0), (0, 0)))
    FC.eye(cv, 'near', expr, ex + off[0][0], ey + off[0][1], closed=blink, table=eyes_tab)
    FC.eye(cv, 'far', expr, fx + off[1][0], fy + off[1][1], closed=blink, table=eyes_tab)
    # ---- brows
    BR = F.get('brows', {})
    e = BR.get(expr, BR.get('neutral', {}))
    # round 7: brow geometry per speaker (head-local inner / outer end; default = the shared round-2 brow)
    (bix, biy, biz), (box, boy, boz) = F.get('brow_pts', ((1.6, -3.9, 17.0), (10.4, -3.4, 13.4)))
    for side in ('r', 'l'):
        sgn = -1 if side == 'r' else 1
        inner = zoom_pt(spec, hf.to_view((sgn * bix, biy + e.get('dy', 0), biz)))
        outer = zoom_pt(spec, hf.to_view((sgn * box, boy + e.get('dy', 0), boz)))
        li = e.get('lift_inner', 0.0) * (1.0 if side == 'r' else 0.9)
        lo = e.get('lift_outer', 0.0)
        x0, y0 = inner[0], inner[1]
        length = abs(outer[0] - inner[0]) + 1
        rise = outer[1] - inner[1]
        bt = F.get('brow_thick')
        thick = (bt[0] if side == 'r' else bt[1]) if bt else ((2, 2, 1) if side == 'r' else (2, 1, 1))
        FC.brow(cv, x0 + (0 if side == 'r' else 0), y0, length, rise=rise, arch=e.get('arch', 0.6),
                thick=thick, inner_left=(side == 'l'), key='b', lift_inner=li, lift_outer=lo)
    # ---- nose: nostril + tip (round 7: 'small' = one dark pixel, 'wide' = a broader wing shadow)
    nst = F.get('nostril', 'std')
    nx, ny = ipt(lmv['nostril_r'])
    cv.rel(nx, ny, -2)
    if nst != 'small':
        cv.rel(nx + 1, ny, -1)
    if nst == 'wide':
        cv.rel(nx - 1, ny, -1)
        cv.rel(nx, ny - 1, -1)
    fx2, fy2 = ipt(lmv['nostril_l'])
    cv.rel(fx2, fy2, -1)
    # ---- mouth
    mo = F.get('mouth', {})
    me = mo.get(expr, {})
    xl = lmv['mouth_r'][0] + mo.get('xl', 0.0)
    xr = lmv['mouth_l'][0] + mo.get('xr', 0.0)
    y = lmv['mouth_c'][1] + mo.get('dy', 0.0)
    open_h = {'rest': 0, 'half': 2, 'open': 3}[mouth_state] + me.get('open_add', 0)
    st = mouth_state
    if st == 'rest' and me.get('parted', 0):
        st, open_h = 'half', me['parted']
    FC.mouth(cv, xl, xr, int(np.floor(y)), st, expr, corner_drop=me.get('corner_drop', 0.0),
             smile=me.get('smile', 0.0), open_h=open_h, teeth=me.get('teeth', True))
    for fn in F.get('extra', ()):
        fn(spec, G, cv, expr, mouth_state, blink, v)


# ------------------------------------------------------------------------------------------- output
def build_char(cid, write=True):
    spec = C.CAST[cid]()
    exprs = spec.get('expressions', EXPRESSIONS)
    frames = {}
    t0 = time.time()
    for e in exprs:
        for r in ANIM_ROWS:
            frames[(e, r)] = render(spec, e, r)
    _cache.clear()
    n = len(exprs)
    grid = np.zeros((SIZE * len(ANIM_ROWS), SIZE * n, 3), np.uint8)
    for i, e in enumerate(exprs):
        for j, r in enumerate(ANIM_ROWS):
            grid[j * SIZE:(j + 1) * SIZE, i * SIZE:(i + 1) * SIZE] = frames[(e, r)]
    strip = grid[0:SIZE]
    if write:
        d = os.path.join(CHAR_DIR, cid)
        os.makedirs(d, exist_ok=True)
        save_png(strip, os.path.join(d, 'portrait.png'))
        save_png(grid, os.path.join(d, 'portrait_anim.png'))
        meta = {
            'size': [SIZE, SIZE],
            'expressions': exprs,
            'anim': {
                'file': 'portrait_anim.png',
                'layout': 'grid: column = expression index (same order as expressions), row = state',
                'rows': ANIM_ROWS,
                'talk_rows': ['rest', 'talk_half', 'talk_open'],
                'blink_offset': 3,
                'mouth_fps': 11,
                'blink_ms': 130,
                'blink_interval_s': [2.6, 5.2],
                'generator': 'tools/pixelgen/chargen_portrait2.py',
            },
        }
        with open(os.path.join(d, 'portrait.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
            f.write('\n')
    print(f'{cid:10s} {n} expressions x {len(ANIM_ROWS)} rows  {time.time() - t0:5.1f}s')
    return spec, frames, grid


def save_png(arr, path):
    """Opaque RGBA PNG (alpha 255) written deterministically."""
    a = np.concatenate([arr, np.full(arr.shape[:2] + (1,), 255, np.uint8)], 2)
    Image.fromarray(a, 'RGBA').save(path, optimize=False, compress_level=9)


def up(arr, k):
    return np.repeat(np.repeat(arr, k, 0), k, 1)


def preview(cid, frames, exprs, tag='portraits_v2'):
    os.makedirs(PREV_DIR, exist_ok=True)
    open(os.path.join(PREV_DIR, '.gdignore'), 'a').close()
    rows = []
    for r in ANIM_ROWS:
        rows.append(np.concatenate([frames[(e, r)] for e in exprs], 1))
    sheet = np.concatenate(rows, 0)
    Image.fromarray(up(sheet, 3)).save(os.path.join(PREV_DIR, f'{tag}_{cid}_3x.png'))


def set_out(char_dir):
    """Write portraits / previews below another assets/characters directory (review runs)."""
    global CHAR_DIR, PREV_DIR
    CHAR_DIR = os.path.abspath(char_dir)
    PREV_DIR = os.path.join(CHAR_DIR, '_preview')


def _job(args):
    cid, write, char_dir = args
    set_out(char_dir)
    spec, frames, grid = build_char(cid, write=write)
    preview(cid, frames, spec.get('expressions', EXPRESSIONS))
    return cid


def main(argv):
    """[ids] [--preview] [--jobs=N] [--out=DIR (an assets/characters directory)]"""
    only_preview = '--preview' in argv
    jobs = 1
    for a in argv:
        if a.startswith('--jobs='):
            jobs = max(1, int(a[7:]))
        elif a.startswith('--out='):
            set_out(a[6:])
    ids = [a for a in argv if not a.startswith('--')] or list(C.CAST)
    if jobs > 1 and len(ids) > 1:
        # one process per speaker: every frame is a pure function of its spec, so the output is identical
        # to a sequential run
        import multiprocessing as mp
        with mp.Pool(min(jobs, len(ids))) as pool:
            for cid in pool.imap(_job, [(c, not only_preview, CHAR_DIR) for c in ids]):
                pass
        return
    for cid in ids:
        spec, frames, grid = build_char(cid, write=not only_preview)
        preview(cid, frames, spec.get('expressions', EXPRESSIONS))


PORTRAITS = list(C.CAST)

if __name__ == '__main__':
    main(sys.argv[1:])
