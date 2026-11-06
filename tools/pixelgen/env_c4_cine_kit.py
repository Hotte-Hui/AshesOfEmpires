"""env_c4_cine_kit -- shared helpers of the Chapter-4 cinematics (owner: cine stream, round 9).

Used by env_c4_cine.py (main) and the film modules env_c4_cine_{homeward,number,card,stamp,voices}.py and the
figure module env_c4_cine_figs.py.  Builds on the round-6/8 cinematic tools (env_veltrava_cine: Paint, masks,
light helpers; env_veltrava_cine_kit: trilingual pixel fonts, dithered puffs; env_c3p2_cine_kit: re-quantiser,
glows, hand lettering) which are imported read-only.

The two cities keep their own palettes so every match cut reads at a glance (C4_DESIGN §2.9):
  Karsk   kerosene amber + red-brown wagon paint (+ the green of the repaired signal)
  Berlin  dawn blue + fluorescent green (+ the sodium lamp of the tram loop)
The shared objects are generated ONCE and reused on both sides of a cut:
  stencil_mask()      the stencil letters of C-17/45 (wagon in Karsk, crates in Berlin: same shapes, same place)
  perforation()       the torn perforation of card No. 0417 (German half's right edge = Russian half's left edge,
                      mirrored)
  stamp_mask()        the rubber-stamp frame + letters (ПРИНЯТЬ in Karsk, ABGANG in Berlin: same frame)
Figures in the wide shots are the game's own character sheets (assets/characters/<id>/sheet.png + sheet_n.png,
the round-2 rig) re-lit with their normal maps for the light of each shot (relight()); close-ups come from the
portrait pipeline (env_c4_cine_figs.py).  A character whose sheet is not delivered yet (the round-9 cast) is
drawn from a declared stand-in and recorded in layout.json "standins" (tests report it as pending).
Deterministic: fixed seeds, no time or global random state.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_berlin_kit as kit  # noqa: E402
import env_veltrava_cine as C  # noqa: E402  (Paint, masks, blur, light helpers; read-only)
import env_veltrava_cine_kit as K  # noqa: E402  (fonts, puffs, soft_quant; read-only)
import env_c3p2_cine_kit as Q  # noqa: E402  (requant, glows, hand_text; read-only)

VW, VH = 640, 360
SAFE = (46, 314)
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'c4')
CHARS = os.path.join(ROOT, 'assets', 'characters')
LAYOUT: dict = {}
STANDINS: dict = {}

# ------------------------------------------------------------------------------------------------ palettes
# Karsk
KNIGHT = ['#05070A', '#090D12', '#0E141B', '#151D26', '#1D2832', '#283541', '#344452', '#465765', '#5B6C78']
AMBER = ['#1C1008', '#38200D', '#5A3412', '#844E17', '#B07224', '#D69A40', '#EEC26E', '#FAE2AA', '#FFF4D8']
RUST = ['#140706', '#240C09', '#3A130D', '#521B11', '#6E2516', '#8A301C', '#A64024', '#BE5634', '#D07048']
CREAM = ['#3E3628', '#665A44', '#8E8064', '#B6A886', '#D8CCAA', '#EEE4C8', '#FFF8E6']
CONCRETE = ['#08090A', '#101213', '#181A1C', '#222527', '#2D3133', '#3A3E40', '#4A4E4F', '#5E6262', '#767976']
BRICK = ['#0E0807', '#1A0E0B', '#2A1510', '#3C1E16', '#52291C', '#6A3624', '#84462E']
OAKK = ['#0C0806', '#170F0A', '#24170F', '#332116', '#462D1D', '#5C3C26', '#764E31', '#92653F']
SIGNAL = ['#04100A', '#082114', '#0E3A20', '#17602F', '#2A8C44', '#5CC070', '#A8EBA8', '#E2FFE0']
SNOWK = ['#0B1016', '#121A22', '#1B2530', '#25313E', '#33414F', '#465564', '#5E6D7B', '#7E8B96', '#A4AEB6',
         '#CED4D8']
VIOLET = ['#160F24', '#24183A', '#352452', '#48326C', '#5E4486', '#7A5EA2']
# Berlin
DAWN = ['#080C16', '#0D1424', '#141E34', '#1C2A46', '#26385A', '#32486E', '#425C84', '#58729A', '#7489AE',
        '#97A8C4', '#BCC8DA']
SNOWB = ['#121A28', '#1A2436', '#243046', '#2E3C56', '#3C4C68', '#4E5F7C', '#64768F', '#7E8EA4', '#9CAABB',
         '#BFC9D5', '#E2E8EE']
SODIUM = ['#24140A', '#46270F', '#6E3E14', '#9C5A1A', '#C87E2A', '#E8A646', '#F8CC78', '#FFEAB6']
FLUO = ['#080C0A', '#0E1612', '#16211A', '#1F2D24', '#2A3A2F', '#37493C', '#465A4B', '#58705C', '#708A72',
        '#8EA88C', '#B4CAAE', '#DCEAD2']
STEEL = ['#0A0D0D', '#121717', '#1B2121', '#252C2B', '#303837', '#3D4645', '#4D5655', '#606967', '#7A827E']
PINE = ['#1E1810', '#30261A', '#463826', '#5E4C34', '#786246', '#937B5A', '#AE9672', '#C8B290', '#E0CEAE']
PAPERB = ['#22241E', '#3A3C34', '#56574C', '#747466', '#949282', '#B4B09C', '#D2CCB4', '#EAE4CC', '#F8F4E2']
INKRED = ['#2A0A0A', '#4A1210', '#701C16', '#94281E', '#B4382A']
TRAM = ['#1A140A', '#2E2412', '#4A3A1C', '#6A5428', '#8E7036', '#B08E48', '#CCAA62', '#E2C680', '#F2DEA6']
NAVYB = ['#05070D', '#0A0F1C', '#111A2E', '#1A2742', '#253656', '#33476C', '#465C84']
IRONK = ['#05070A', '#0B0E12', '#13171C', '#1C2127', '#272D34', '#343B43', '#454D55', '#5B636B', '#757D84']


def ramps(**kw) -> kit.Ramps:
    return C.ramps(**kw)


def grid(h=VH, w=VW, x0=0, y0=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return yy + y0, xx + x0


def hexrgb(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32)


# ------------------------------------------------------------------------------------------------ io
def save(arr, rel):
    a = arr.c if hasattr(arr, 'c') else arr
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kit.save_rgba(np.ascontiguousarray(a.astype(np.uint8)), path)
    return path


def write_layout():
    os.makedirs(OUT, exist_ok=True)

    def norm(o):
        if isinstance(o, dict):
            return {str(k): norm(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [norm(v) for v in o]
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, (np.floating, float)):
            v = float(o)
            return int(v) if v.is_integer() else round(v, 4)
        return o
    data = dict(LAYOUT)
    data['standins'] = dict(STANDINS)
    txt = json.dumps(norm(data), indent=1, sort_keys=True, ensure_ascii=False)
    txt = re.sub(r'\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]',
                 lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']', txt)
    with open(os.path.join(OUT, 'layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt + '\n')


# ------------------------------------------------------------------------------------------------ masks
def poly(pts, w=VW, h=VH):
    return C.poly_mask(w, h, pts)


def ell(cx, cy, rx, ry, w=VW, h=VH):
    return C.ellipse_mask(w, h, cx, cy, rx, ry)


def box(x0, y0, x1, y1, w=VW, h=VH):
    m = np.zeros((h, w), bool)
    m[max(0, int(y0)):max(0, min(h, int(y1))), max(0, int(x0)):max(0, min(w, int(x1)))] = True
    return m


def line(pts, r, w=VW, h=VH):
    return C.stroke(w, h, pts, r)


def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(w, h, cell, seed, octaves=octaves)


def lightfield(w, h, lights):
    return Q.lightfield(w, h, lights)


def place(small, w, h, x, y):
    return K.place(small, w, h, int(x), int(y))


def upscale(m, k):
    return np.repeat(np.repeat(m, k, 0), k, 1)


def smooth_up(m, k, thr=0.5):
    """Bool mask scaled by k with rounded corners (box-blurred, re-thresholded): rubber-stamp / typed letters."""
    big = upscale(m.astype(np.float32), k)
    r = max(1, k // 2)
    return C.blur(big, r) > thr


def text(s, font='s', spacing=1):
    return K.vtext(s, font, spacing)


def text_at(s, w, h, x, y, font='s', spacing=1):
    return place(text(s, font, spacing), w, h, x, y)


def rotate_mask(m, deg, out_shape=None, center=None):
    """Nearest-neighbour rotation of a bool mask about its centre (a stamp lands a little askew)."""
    h, w = m.shape
    oh, ow = out_shape or (h, w)
    cy, cx = center or ((h - 1) / 2.0, (w - 1) / 2.0)
    oy, ox = (oh - 1) / 2.0, (ow - 1) / 2.0
    a = math.radians(deg)
    yy, xx = np.mgrid[0:oh, 0:ow].astype(np.float32)
    dx, dy = xx - ox, yy - oy
    sx = np.round(cx + dx * math.cos(a) + dy * math.sin(a)).astype(int)
    sy = np.round(cy - dx * math.sin(a) + dy * math.cos(a)).astype(int)
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    out = np.zeros((oh, ow), bool)
    out[ok] = m[sy[ok], sx[ok]]
    return out


# ------------------------------------------------------------------------------------------------ colour
def flat(mask, hexcol, out=None):
    """RGBA canvas (new or given) with `mask` set to one colour."""
    if out is None:
        out = np.zeros(mask.shape + (4,), np.uint8)
    c = hexrgb(hexcol).astype(np.uint8)
    out[mask, :3] = c
    out[mask, 3] = 255
    return out


def requant(rgb, pal, spread=18.0, ox=0, oy=0, alpha=None):
    return Q.requant(rgb, pal, spread, ox, oy, alpha)


def glow_sprite(w, h, blobs, step=6.0, ox=0, oy=0):
    return Q.glow_sprite(w, h, blobs, step, ox, oy)


def add_glow(a, cx, cy, rx, ry, rgb, power=1.5):
    return Q.add_glow(a, cx, cy, rx, ry, rgb, power)


def blit(dst, src, x, y):
    return Q.blit(dst, src, int(x), int(y))


def sheet(frames):
    return np.concatenate(frames, axis=1)


def vsheet(rows):
    return np.concatenate(rows, axis=0)


def darkness(w, h, cx, cy, r_in, r_out, hexcol, levels=(0.0, 0.35, 0.7, 1.0), squash=1.0, seed=0):
    """A sheet of darkness with a soft round hole (the light pool of a hand lamp): RGBA in one colour whose
    coverage steps through `levels` with an ordered dither between r_in and r_out (pixel-art falloff)."""
    yy, xx = grid(h, w)
    d = np.hypot((xx + 0.5 - cx), (yy + 0.5 - cy) * squash)
    u = np.clip((d - r_in) / max(1.0, r_out - r_in), 0, 1)
    n = len(levels) - 1
    th = pg.bayer(w, h, seed, seed)
    k = np.floor(u * n + th * 0.999).astype(int)
    k = np.clip(k, 0, n)
    a = np.asarray(levels, np.float32)[k]
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = hexrgb(hexcol).astype(np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    return out


def dither_alpha(rgba, alpha, seed=0):
    """Ordered-dither a float alpha (0..1) into a binary alpha (pixel art has no partial transparency)."""
    h, w = alpha.shape
    th = pg.bayer(w, h, seed, seed)
    out = rgba.copy()
    out[..., 3] = np.where(alpha > th * 0.98 + 0.01, out[..., 3], 0)
    return out


# ------------------------------------------------------------------------------------------------ game sheets
def char_sheet(cid: str, standin: str | None = None):
    """The game's own sprite sheet of `cid` -> (rgba, normals or None, meta, used id).  When the sheet is not
    delivered yet, `standin` is used and recorded in STANDINS (layout.json, reported by the tests)."""
    used = cid
    if not os.path.exists(os.path.join(CHARS, cid, 'sheet.png')):
        if standin is None:
            raise FileNotFoundError(cid)
        used = standin
        STANDINS[cid] = standin
    else:
        STANDINS.pop(cid, None)
    d = os.path.join(CHARS, used)
    img = np.asarray(Image.open(os.path.join(d, 'sheet.png')).convert('RGBA')).copy()
    nrm = None
    if os.path.exists(os.path.join(d, 'sheet_n.png')):
        nrm = np.asarray(Image.open(os.path.join(d, 'sheet_n.png')).convert('RGBA')).copy()
    with open(os.path.join(d, 'sheet.json'), encoding='utf-8') as f:
        meta = json.load(f)
    return img, nrm, meta, used


def anim_frames(cid, anim, standin=None, pick=None):
    """List of (rgba, normal) cells of one animation row of a character sheet (all frames, or `pick`)."""
    img, nrm, meta, used = char_sheet(cid, standin)
    cw, chh = meta['cell']
    a = meta['anims'].get(anim)
    if a is None:                                   # side-level NPC sheets have fewer rows: nearest kind
        for alt in (anim.replace('walk', 'idle'), 'walk_side', 'idle_side'):
            if alt in meta['anims']:
                a = meta['anims'][alt]
                break
    row, n = int(a['row']), int(a['frames'])
    idx = list(range(n)) if pick is None else list(pick)
    out = []
    for i in idx:
        c = img[row * chh:(row + 1) * chh, (i % n) * cw:(i % n + 1) * cw]
        nc = nrm[row * chh:(row + 1) * chh, (i % n) * cw:(i % n + 1) * cw] if nrm is not None else None
        out.append((c.copy(), None if nc is None else nc.copy()))
    return out


def relight(rgba, nrm, amb, key, key_rgb, rim=None, rim_rgb=(0, 0, 0), bands=3, rim_cut=0.55, gain=1.0):
    """Re-light one sprite cell for a shot: albedo x (ambient + banded Lambert of the key) + a cut rim light.
    amb / key_rgb / rim_rgb are linear-ish multipliers (1.0 = the sheet's own colour); key / rim are directions
    (x right, y UP, z toward the viewer) like the sheets' normal maps.  Without a normal map the cell gets a
    flat front normal."""
    a = rgba[..., 3] > 0
    base = rgba[..., :3].astype(np.float32)
    if nrm is not None:
        n = nrm[..., :3].astype(np.float32) / 127.5 - 1.0
    else:
        n = np.zeros(base.shape, np.float32)
        n[..., 2] = 1.0
    nn = np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    n = n / nn
    L = np.asarray(key, np.float32)
    L = L / (np.linalg.norm(L) + 1e-6)
    lam = np.clip((n * L).sum(-1), 0, 1)
    lam = np.floor(lam * bands + 0.5) / bands
    light = np.asarray(amb, np.float32)[None, None] + lam[..., None] * np.asarray(key_rgb, np.float32)[None, None]
    out = base * light * gain
    if rim is not None:
        R = np.asarray(rim, np.float32)
        R = R / (np.linalg.norm(R) + 1e-6)
        rr = (n * R).sum(-1)
        sel = a & (rr > rim_cut)
        out[sel] = out[sel] + np.asarray(rim_rgb, np.float32)[None] * 255.0
    res = np.zeros_like(rgba)
    res[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    res[..., 3] = rgba[..., 3]
    return res


def feet_shadow(cell, strength=1.0):
    """Contact shadow of a sheet cell (origin (16, 54)): black with partial alpha on the transparent pixels round
    and under the feet (rows 53-55), as wide as the stance of this frame -- the figure stands on the plate's
    ground instead of floating over it (round 10)."""
    out = cell.copy()
    h, w = out.shape[:2]
    if h < 56:
        return out
    a = out[..., 3] > 0
    xs = np.nonzero(a[48:55].any(0))[0]
    if xs.size == 0:
        return out
    x0, x1 = xs.min() - 2.0, xs.max() + 3.0
    cx, rx = (x0 + x1) / 2.0, (x1 - x0) / 2.0 + 0.5
    for y, k, al in ((53, 0.80, 52), (54, 1.0, 84), (55, 0.82, 58)):
        for x in range(w):
            d = abs(x + 0.5 - cx) / (rx * k)
            if d <= 1.0 and not a[y, x]:
                out[y, x, :3] = 0
                out[y, x, 3] = int((al if d < 0.68 else al * 0.55) * strength)
    return out


def lit_row(cid, anim, look, standin=None, pick=None, flip=False, shadow=True):
    """One relit animation row as a horizontal sheet (look = relight kwargs); shadow = feet_shadow() under every
    frame (round 10; False = the bare cells of round 9)."""
    cells = []
    for c, n in anim_frames(cid, anim, standin, pick):
        if flip:
            c = c[:, ::-1].copy()
            if n is not None:
                n = n[:, ::-1].copy()
                n[..., 0] = 255 - n[..., 0]
        cell = relight(c, n, **look)
        cells.append(feet_shadow(cell) if shadow else cell)
    return sheet(cells)


def _rgb2hsv(rgb):
    r, g, b = (rgb[..., i] for i in range(3))
    mx = np.max(rgb, -1)
    mn = np.min(rgb, -1)
    d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return np.stack([h % 1.0, s, mx], -1)


def _hsv2rgb(hsv):
    h, s, v = (hsv[..., i] for i in range(3))
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    out = np.zeros(hsv.shape, np.float32)
    for k, (a, b, c) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        m = i == k
        out[m] = np.stack([a[m], b[m], c[m]], -1)
    return out


# deterministic clothing variations of a crowd: (hue shift, saturation gain, value gain)
CROWD_VARIANTS = ((0.0, 1.0, 1.0), (0.07, 0.9, 1.05), (-0.06, 1.1, 0.92), (0.45, 0.6, 0.95), (0.12, 0.7, 1.12),
                  (-0.12, 0.8, 0.86), (0.30, 0.5, 1.0), (0.0, 0.35, 1.08))


def crowd_variant(rgba, seed):
    """The same sprite in other clothes: hue / saturation / value of the cloth pixels shift by a deterministic
    variant (skin keeps its colour), so a crowd built from a few sheets does not look cloned."""
    dh, ds, dv = CROWD_VARIANTS[seed % len(CROWD_VARIANTS)]
    if (dh, ds, dv) == (0.0, 1.0, 1.0):
        return rgba.copy()
    out = rgba.copy()
    a = out[..., 3] > 0
    rgb = out[..., :3].astype(np.float32) / 255.0
    hsv = _rgb2hsv(rgb)
    skin = (((hsv[..., 0] < 0.11) | (hsv[..., 0] > 0.96)) & (hsv[..., 1] > 0.18) & (hsv[..., 1] < 0.75)
            & (hsv[..., 2] > 0.30))
    m = a & ~skin & (out[..., 3] == 255)
    hs = hsv.copy()
    hs[..., 0] = (hs[..., 0] + dh) % 1.0
    hs[..., 1] = np.clip(hs[..., 1] * ds, 0, 1)
    hs[..., 2] = np.clip(hs[..., 2] * dv, 0, 1)
    new = _hsv2rgb(hs)
    out[m, :3] = np.clip(new[m] * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return out


def crowd_row(cid, anim, look, seed=0, standin=None, pick=None, flip=False, shadow=True):
    """lit_row() of an extra in one of the CROWD_VARIANTS clothes (people for the empty plates: travellers,
    workers, passers-by from the game's own sheets -- porter, worker_a/b, babushka, clerk, typist, berlin_*,
    conductor, vendor, child_a ...)."""
    row = lit_row(cid, anim, look, standin, pick, flip, shadow)
    return crowd_variant(row, seed)


def cell_size(cid, standin=None):
    _, _, meta, _ = char_sheet(cid, standin)
    return tuple(meta['cell']), tuple(meta.get('origin', [meta['cell'][0] // 2, meta['cell'][1] - 2]))


# ------------------------------------------------------------------------------------------------ stencil
# Stencil letters on a 6 x 9 unit box, every stroke a separate piece (the bridges of a cut stencil are the gaps).
_ARC = lambda cx, cy, rx, ry, a0, a1, n=14: [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),  # noqa: E731
                                              cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
                                             for i in range(n + 1)]
STENCIL = {
    'C': [_ARC(3.3, 4.5, 2.5, 3.7, 44, 316, 18)],
    '-': [[(1.1, 4.9), (4.4, 4.9)]],
    '1': [[(3.6, 0.7), (3.6, 8.3)], [(1.5, 2.6), (2.5, 1.5)]],
    '7': [[(0.9, 0.8), (5.1, 0.8)], [(4.5, 2.1), (2.3, 8.3)]],
    '/': [[(4.6, 0.4), (1.3, 8.6)]],
    '4': [[(3.1, 0.7), (0.9, 5.2)], [(1.4, 6.0), (5.4, 6.0)], [(4.1, 2.6), (4.1, 4.9)], [(4.1, 7.1), (4.1, 8.3)]],
    '5': [[(1.5, 0.8), (5.0, 0.8)], [(1.5, 2.0), (1.5, 3.6)], _ARC(2.9, 5.95, 2.3, 2.35, -152, 150, 16)],
    '2': [_ARC(3.0, 2.8, 2.1, 2.0, 200, 365, 10), [(4.6, 4.4), (1.0, 8.0)], [(1.6, 8.3), (5.2, 8.3)]],
    '0': [_ARC(3.0, 4.5, 2.2, 3.6, 105, 255, 12), _ARC(3.0, 4.5, 2.2, 3.6, -75, 75, 12)],
    '3': [_ARC(2.8, 2.5, 2.0, 1.8, 200, 450, 12), _ARC(2.8, 6.2, 2.2, 2.1, -90, 150, 12)],
}
STENCIL_ADV = {'-': 5.2, '/': 5.6, '1': 5.6}


def stencil_layout(s, H):
    """[(char, x0)] and the total width of a stencil string with cap height H px."""
    u = H / 9.0
    x = 0.0
    out = []
    for ch in s:
        out.append((ch, x))
        x += STENCIL_ADV.get(ch, 6.4) * u
    return out, x


def thick(pts, wid, w, h):
    """A stroke with FLAT ends (a cut stencil): one quad per segment, round joints only inside the line."""
    m = np.zeros((h, w), bool)
    r = wid / 2.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L * r, dx / L * r
        m |= C.poly_mask(w, h, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])
        if 0 < i:
            m |= C.ellipse_mask(w, h, x0, y0, r, r)
    return m


def stencil_mask(s, H, w=None, h=None, x0=0.0, y0=0.0, width=1.75):
    """Bool mask of stencil text, cap height H px, top-left at (x0, y0) in a w x h canvas."""
    u = H / 9.0
    lay, tw = stencil_layout(s, H)
    w = w or int(math.ceil(tw + x0 + 4))
    h = h or int(math.ceil(H + y0 + 4))
    m = np.zeros((h, w), bool)
    for ch, gx in lay:
        for st in STENCIL.get(ch, []):
            pts = [(x0 + gx + px * u, y0 + py * u) for (px, py) in st]
            m |= thick(pts, width * u, w, h)
    return m


def chalk(s, scale=2, slant=0.18, seed=0, dry=0.28):
    """Chalk lettering: hand capitals with dry gaps."""
    m = Q.hand_text(s, scale, slant, seed)
    rng = np.random.default_rng(seed + 9)
    gaps = rng.random(m.shape) < dry
    return m & ~gaps


# ------------------------------------------------------------------------------------------------ stamps
STAMP_FRAME = (212, 64)                # outer size of both rubber stamps (ПРИНЯТЬ / ABGANG) at macro scale


def stamp_mask(word, k=4, frame=STAMP_FRAME, angle=-2.5, seed=0, ink=0.86):
    """Rubber-stamp impression: double-line frame + the word in the 5x7 Veltrava capitals scaled by k with
    rounded corners, a little askew, uneven ink (dry spots, a heavier edge)."""
    fw, fh = frame
    pad = 10
    W, H = fw + 2 * pad, fh + 2 * pad
    m = np.zeros((H, W), bool)
    outer = box(pad, pad, pad + fw, pad + fh, W, H) & ~box(pad + 4, pad + 4, pad + fw - 4, pad + fh - 4, W, H)
    inner = box(pad + 7, pad + 7, pad + fw - 7, pad + fh - 7, W, H) & ~box(pad + 9, pad + 9, pad + fw - 9,
                                                                            pad + fh - 9, W, H)
    m |= outer | inner
    t = text(word, 'l', 1)
    big = smooth_up(t, k)
    th, tw = big.shape
    m |= place(big, W, H, pad + (fw - tw) // 2, pad + (fh - th) // 2 + 1)
    m = rotate_mask(m, angle)
    rng = np.random.default_rng(seed)
    nz = pg.value_noise(W, H, 5, seed + 3, octaves=3)
    dry = nz < (1.0 - ink) + 0.1 * rng.random((H, W))
    return m & ~dry


# ------------------------------------------------------------------------------------------------ the card
PERF_PITCH = 6.0                       # hole pitch of the perforation at card scale 1 (px)


def perforation(n_holes, pitch, radius, seed=417):
    """Shared geometry of the torn perforation of card No. 0417: hole centres (along the edge) and a fibre
    profile per position (tiny tufts between the holes); both halves use it (mirrored)."""
    rng = np.random.default_rng(seed)
    ys = [pitch * (i + 0.5) for i in range(n_holes)]
    tufts = rng.random(4096)
    return dict(ys=ys, r=radius, pitch=pitch, tufts=tufts)


def torn_edge_mask(h, w, edge_x, perf, side, y0=0.0, scale=1.0):
    """Paper mask of a card half: paper on `side` ('left' = the German half, paper left of the edge) of the
    vertical line x = edge_x, with the half-holes of the perforation notched out and fibre tufts between them.
    Coordinates in px; perf ys are scaled by `scale` and offset by y0."""
    yy, xx = grid(h, w)
    sgn = 1.0 if side == 'left' else -1.0
    inside = (xx + 0.5 - edge_x) * sgn < 0
    for i, yc in enumerate(perf['ys']):
        cy = y0 + yc * scale
        r = perf['r'] * scale
        inside &= ~((np.hypot(xx + 0.5 - edge_x, yy + 0.5 - cy)) < r)
    # fibre tufts: between the holes the tear is not clean -- short fibres stand out of the edge
    t = perf['tufts']
    rows = np.arange(h)
    k = (np.floor((rows - y0) / max(1.0, scale * 0.8)).astype(int)) % len(t)
    reach = (t[k] ** 3) * 1.6 * scale
    yrel = (rows - y0) / scale
    near_hole = np.zeros(h, bool)
    for yc in perf['ys']:
        near_hole |= np.abs(yrel - yc) < perf['r'] * 1.05
    reach[near_hole] = 0
    out_d = (xx + 0.5 - edge_x) * sgn
    inside |= (out_d >= 0) & (out_d < reach[:, None])
    return inside


def fig_sheet(cid, rows, look, standin=None):
    """One horizontal sheet of relit cells from several animation rows of a character:
    rows = [(anim, pick or None, flip)] -> (sheet, {anim: [first, count]}) (the runtime picks frames by name)."""
    cells, index = [], {}
    for anim, pick, flip in rows:
        part = lit_row(cid, anim, look, standin, pick, flip)
        n = part.shape[1] // 32
        key = anim + ('_l' if flip else '')
        index[key] = [len(cells), n]
        cells += [part[:, i * 32:(i + 1) * 32] for i in range(n)]
    return sheet(cells), index


# re-light presets (amb, key, key_rgb, rim, rim_rgb): x right, y UP, z toward the viewer
LIGHT_KARSK_NIGHT = dict(amb=(0.30, 0.34, 0.44), key=(0.6, 0.2, 0.75), key_rgb=(0.55, 0.40, 0.22),
                         rim=(-0.8, 0.5, -0.2), rim_rgb=(0.05, 0.16, 0.08), bands=3)
LIGHT_SIGNAL = dict(amb=(0.34, 0.42, 0.42), key=(-0.7, 0.5, 0.5), key_rgb=(0.26, 0.56, 0.30),
                    rim=(0.8, -0.3, -0.2), rim_rgb=(0.20, 0.11, 0.03), bands=3)
LIGHT_DAWN_B = dict(amb=(0.42, 0.48, 0.62), key=(-0.5, 0.6, 0.6), key_rgb=(0.40, 0.44, 0.52),
                    rim=(0.8, 0.2, -0.3), rim_rgb=(0.20, 0.12, 0.04), bands=3)
LIGHT_MORNING_B = dict(amb=(0.56, 0.60, 0.70), key=(-0.4, 0.7, 0.6), key_rgb=(0.40, 0.42, 0.46),
                       rim=(0.8, 0.3, -0.3), rim_rgb=(0.10, 0.09, 0.06), bands=3)
LIGHT_FLUO = dict(amb=(0.40, 0.48, 0.42), key=(0.0, 0.9, 0.4), key_rgb=(0.46, 0.56, 0.46),
                  rim=(-0.7, 0.6, -0.3), rim_rgb=(0.10, 0.12, 0.14), bands=3)
LIGHT_STATION = dict(amb=(0.40, 0.42, 0.52), key=(0.0, 0.8, -0.6), key_rgb=(0.42, 0.40, 0.44),
                     rim=(0.0, 0.9, -0.4), rim_rgb=(0.18, 0.16, 0.16), bands=3)


def hand_text_k(s, scale=1, slant=0.2, seed=0):
    """Pencil handwriting (block capitals, slanted, uneven pressure) -- the notebook pages."""
    return Q.hand_text(s, scale, slant, seed)
