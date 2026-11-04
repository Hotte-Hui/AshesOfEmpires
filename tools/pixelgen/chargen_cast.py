"""chargen_cast -- the vertical-slice cast: materials, hand-designed pixel bitmaps, garments, props.

Bitmap legends map a character to (material, tone[, flags]):  tone 0..5 = ramp slot (0 outline,
1 deep shadow, 2 shadow, 3 base, 4 light, 5 highlight), None = auto-shaded.  flags: 'f' = fixed pixel
(no outline / rim), 'd' = darker (-1).
"""
from __future__ import annotations

import math

import numpy as np

from chargen_body import Coat, Skirt, Spec, M
from chargen_core import (Bitmap, Light, Material, add, capsule, ellipse, make_ramp, poly, put_bitmap,
                          ramp_from_hex, rot)

SKIN = {
    'karsk': ['#2A1C22', '#5A3A3A', '#865548', '#B07A5E', '#CE9C7A', '#E6C2A0'],
    'berlin': ['#2B1A24', '#5C3540', '#8A5550', '#B67D66', '#D7A182', '#EDC7A6'],
}

RIM = {
    'karsk': np.array([168, 196, 184, 255], np.uint8),
    'berlin': np.array([170, 172, 200, 255], np.uint8),
    'archive': np.array([150, 178, 196, 255], np.uint8),
}


def materials(scene: str, table: dict):
    """table: name -> base hex | (base hex, kwargs) | list of 6 hexes.  Returns (mats, names)."""
    mats, names = [], {}
    for i, (name, spec) in enumerate(table.items()):
        kw = {}
        if isinstance(spec, tuple):
            spec, kw = spec
        if isinstance(spec, list):
            ramp = ramp_from_hex(spec)
        else:
            ramp = make_ramp(spec, scene)
        mats.append(Material(name, ramp, **kw))
        names[name] = i
    return mats, names


def side_light():
    return Light(key=(0.78, 0.42, 0.46), rim=(-0.80, 0.45, -0.30), ambient=0.16,
                 thresholds=(0.28, 0.62, 0.82, 0.96))


# ----------------------------------------------------------------------------------- shared legends
def skin_legend(m='skin'):
    return {'q': (m, 0), 'r': (m, 1), 's': (m, 2), 'S': (m, 3), 'L': (m, 4), 'H': (m, 5),
            'e': ('eye', 1, 'f'), 'E': ('eye', 3, 'f'), 'm': (m, 1, 'f'), 'M': ('eye', 2, 'f')}


def digit_legend(m):
    """'0'..'5' = tones of material m, 'R' = rim-lit pixel of m."""
    d = {str(i): (m, i) for i in range(6)}
    d['R'] = (m, 'rim')
    return d


def ramp_legend(m, chars='abcdD'):
    """chars for tones 1..5 of material m."""
    return {ch: (m, i + 1) for i, ch in enumerate(chars)}


def merge(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


# ----------------------------------------------------------------------------------- generic parts
def hand_bitmaps(m='skin', glove=None):
    g = glove or m
    lg = {'a': (g, 1), 'b': (g, 2), 'c': (g, 3), 'd': (g, 4)}
    return {
        'side': Bitmap(['cd', 'bc'], lg, anchor=(0, 0)),
        'side_open': Bitmap(['cdd', 'bc.'], lg, anchor=(0, 0)),
        'front': Bitmap(['cd', 'bc'], lg, anchor=(0, 0)),
        'front_l': Bitmap(['dc', 'cb'], lg, anchor=(1, 0)),
        'front_r': Bitmap(['cd', 'bc'], lg, anchor=(0, 0)),
        'back': Bitmap(['bc', 'ab'], lg, anchor=(0, 0)),
        'back_l': Bitmap(['cb', 'ba'], lg, anchor=(1, 0)),
        'back_r': Bitmap(['bc', 'ab'], lg, anchor=(0, 0)),
    }


def boot_bitmaps(m='boot', sole=None, style='heavy'):
    """Footwear.  Anchor = ankle pixel; standing boots put their sole on the row below the ankle row."""
    s = sole or m
    lg = {'a': (s, 1), 'b': (m, 2), 'c': (m, 3), 'd': (m, 4), 'o': (s, 0), 'p': ('patch', 3), 'q': ('patch', 4)}
    if style == 'heavy':        # Alexei: heavy, square-toed, repaired
        side_flat = Bitmap(['bcc...', 'bcccdd', 'aaaaaa'], lg, anchor=(1, 1))
        side_heel = Bitmap(['bcc..d', 'bcccdd', 'aaaaa.'], lg, anchor=(1, 1))
        side_toe = Bitmap(['bcc...', 'bcccd.', '.aaaaa'], lg, anchor=(1, 1))
        side_toe2 = Bitmap(['bc....', 'bccd..', '.bccd.', '..aaaa'], lg, anchor=(1, 1))
        front = Bitmap(['bcd', 'bcd', 'aaa'], lg, anchor=(1, 1))
        back = Bitmap(['bcb', 'bcb', 'aaa'], lg, anchor=(1, 1))
    elif style == 'shoe':       # leather street shoes
        side_flat = Bitmap(['bc...', 'bccd.', 'aaaaa'], lg, anchor=(1, 1))
        side_heel = Bitmap(['bc..d', 'bccd.', 'aaaa.'], lg, anchor=(1, 1))
        side_toe = Bitmap(['bc...', 'bccd.', '.aaaa'], lg, anchor=(1, 1))
        side_toe2 = Bitmap(['bc...', 'bcd..', '.bcd.', '..aaa'], lg, anchor=(1, 1))
        front = Bitmap(['bcd', 'bcd', 'aaa'], lg, anchor=(1, 1))
        back = Bitmap(['bcb', 'bcb', 'aaa'], lg, anchor=(1, 1))
    elif style == 'valenki':    # felt boots: tall, round, no heel
        side_flat = Bitmap(['bcc.', 'bcc.', 'bccd', 'abbb'], lg, anchor=(1, 2))
        side_heel = Bitmap(['bcc.', 'bcc.', 'bccd', 'abb.'], lg, anchor=(1, 2))
        side_toe = Bitmap(['bcc.', 'bcc.', 'bccd', '.abb'], lg, anchor=(1, 2))
        side_toe2 = Bitmap(['bc..', 'bcc.', 'bccd', '.bcd', '..ab'], lg, anchor=(1, 2))
        front = Bitmap(['bcd', 'bcd', 'bcd', 'abb'], lg, anchor=(1, 2))
        back = Bitmap(['bcb', 'bcb', 'bcb', 'abb'], lg, anchor=(1, 2))
    else:                       # tall riding boots (guard)
        side_flat = Bitmap(['bcd..', 'bcd..', 'bcd..', 'bccdd', 'aaaaa'], lg, anchor=(1, 3))
        side_heel = Bitmap(['bcd..', 'bcd..', 'bcd..', 'bccdd', 'aaaa.'], lg, anchor=(1, 3))
        side_toe = Bitmap(['bcd..', 'bcd..', 'bcd..', 'bccdd', '.aaaa'], lg, anchor=(1, 3))
        side_toe2 = Bitmap(['bc...', 'bcd..', 'bcd..', 'bccd.', '.bcdd', '..aaa'], lg, anchor=(1, 3))
        front = Bitmap(['bcd', 'bcd', 'bcd', 'bcd', 'aaa'], lg, anchor=(1, 3))
        back = Bitmap(['bcb', 'bcb', 'bcb', 'bcb', 'aaa'], lg, anchor=(1, 3))
    return dict(side_flat=side_flat, side_heel=side_heel, side_toe=side_toe, side_toe2=side_toe2,
                front=front, back=back)


def head_set(rows_by_face: dict, legend: dict, anchor, dome=(1.0, 1.0)):
    return {k: Bitmap(v, legend, anchor=anchor, dome=dome) for k, v in rows_by_face.items()}


def faces(base_rows: list[str], legend, anchor, blink=None, talk=None, dome=(1.0, 1.1)):
    """Make {'base','blink','talk'} from one hand-drawn head: 'e' eyes close to skin shadow, 'm' mouth
    opens to 'o'.  Explicit per-face overrides can be given as {(x,y): char}."""
    base = Bitmap(base_rows, legend, anchor=anchor, dome=dome)
    out = {'base': base}
    out['blink'] = base.variant(blink if blink is not None else {'e': 's'})
    out['talk'] = base.variant(talk if talk is not None else {'m': 'o'})
    return out


# ----------------------------------------------------------------------------------- helpers
def put_poly(fr, spec, pts, mat, tone=None, R=1.5, cyl=0.5, cast=True, name='poly', bias=0.0, inline=False):
    m, x0, y0, n = poly(pts, R=R, cyl=cyl)
    return fr.put(m, x0, y0, M(spec, mat), n, tone=tone, cast=cast, name=name, bias=bias, inline=inline)


def put_line(fr, spec, a, b, r, mat, tone=None, cast=False, name='line', bias=0.0):
    m, x0, y0, n = capsule(a, b, r)
    return fr.put(m, x0, y0, M(spec, mat), n, tone=tone, cast=cast, name=name, bias=bias)


def bm(rows, legend, anchor):
    return Bitmap(rows, legend, anchor=anchor)


def buttons(fr, spec, J, u, vs, mat='button', tone=2):
    for v in vs:
        x, y = J['body'](u, v)
        fr.recolor(x, y, M(spec, mat), tone)


def column_line(fr, spec, J, u, v0, v1, mat_name, dt=-1.0):
    """Darken a vertical seam (front edge of a coat) in body space."""
    mid = M(spec, mat_name)
    v = v0
    while v <= v1:
        x, y = J['body'](u, v)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if 0 <= xi < fr.w and 0 <= yi < fr.h and fr.mat[yi, xi] == mid:
            fr.bias[yi, xi] += dt
        v += 1.0


def quilt_lines(fr, spec, J, mat_name, step=3, start=1, vmin=-99, vmax=99, light=None):
    """Horizontal quilting seams: every `step`-th row of a material is darkened where the cloth faces
    the key light (seams read on lit cloth, the shadow side stays calm)."""
    mid = M(spec, mat_name)
    py = J['pelvis'][1]
    L = np.asarray(light if light is not None else spec.light.key, np.float32)
    L = L / np.linalg.norm(L)
    facing = (fr.n * L).sum(-1) > 0.45
    for y in range(fr.h):
        v = py - y - 0.5
        if v < vmin or v > vmax or (int(math.floor(v)) - start) % step != 0:
            continue
        row = (fr.mat[y] == mid) & np.isnan(fr.tone[y]) & facing[y]
        fr.bias[y][row] -= 1.0


def walking(P):
    return P.get('foot_f', (0, 0, 0))[1] > 0 or P.get('foot_n', (0, 0, 0))[1] > 0


EYE_K = ['#0A0E12', '#141A1F', '#3A2A2A', '#7E8A86', '#B9C6C0', '#E8EDE6']
EYE_B = ['#0A0B12', '#15141F', '#3A2A2E', '#7E808A', '#B9BCC6', '#E8E8EE']


# ----------------------------------------------------------------------------------- ALEXEI
def alexei():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#3B5443',
        'trouser': '#2A3034',
        'boot': '#3B302A',
        'patch': '#5E4C3B',
        'fur': '#57514A',
        'skin': SKIN['karsk'],
        'hair': '#3A2C24',
        'eye': EYE_K,
        'satchel': '#7A5639',
        'strap': '#4E3626',
        'metal': '#8C8E80',
        'button': '#2A2A22',
    })
    lg = merge(skin_legend(), digit_legend('fur'), {'k': ('hair', 2), 'K': ('hair', 3)})
    side_rows = [
        '..1222233.',
        '.R22333344',
        '0R22334555',
        '023331sSS.',
        '023331SeL.',
        '023331SSLL',
        '.22221sSm.',
        '..1111sS..',
        '.....rs...',
    ]
    front_rows = [
        '.1222221.',
        '122333221',
        '455554432',
        '23sSSSs21',
        '23SeLes21',
        '23SSLss21',
        '.2sSmSs1.',
        '...sSs...',
        '...rsr...',
    ]
    back_rows = [
        '.1222221.',
        '122333221',
        '123333321',
        '122222221',
        '123333321',
        '.1222221.',
        '..rsssr..',
        '...sss...',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 8), blink={(7, 4): 'S'}, talk={(8, 6): 'M'}),
        'front': faces(front_rows, lg, anchor=(4, 8), blink={(3, 4): 's', (5, 4): 's'}, talk={'m': 'M'}),
        'back': {'base': Bitmap(back_rows, lg, anchor=(4, 7), dome=(1.0, 1.1))},
    }
    spec = Spec(id='alexei', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                coat=Coat(mat='coat', hem=-6.5, back=4.7, front=4.3, flare=0.6, chest=0.5, collar=1.6,
                          width_f=5.8, waist_f=4.3, hem_f=4.8, R=2.4, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='heavy'), hands=hand_bitmaps('skin'),
                lean=2.0, style=dict(stride=7.0, swing=22.0, bob=1, walk_lean=3.0))
    spec.hooks = {'side': [('coat', alexei_coat_side), ('coat', satchel_side)],
                  'front': [('coat', alexei_coat_front)],
                  'back': [('coat', alexei_coat_back)]}
    return spec


def alexei_coat_side(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -6, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 3.0, T - 7.0, 1.0))
    x, y = J['ank_n']
    fr.recolor(x + 1, y, M(spec, 'patch'), 4)       # repaired boot: a lighter patch pixel


SATCHEL_LG = {'a': ('satchel', 1), 'b': ('satchel', 2), 'c': ('satchel', 3), 'd': ('satchel', 4),
              'e': ('satchel', 5), 'm': ('metal', 4), 'o': ('satchel', 0)}


def satchel_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(1.8, T - 0.6), body(-0.6, 0.6), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['cddde.', 'bcmddd', 'obcccd', 'obbbcc', '.oooo.'], SATCHEL_LG, anchor=(2, 0))
    ph = P.get('phase', 0)
    sway = (-1 if walking(P) and ph in (1, 2, 5, 6) else 0)   # lags the body by a frame
    x, y = body(-1.2, 0.8)
    put_bitmap(fr, sat, spec.names, x + sway, y, name='satchel')


def alexei_coat_front(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, 0.5, -6, T - 1, 'coat', -0.8)
    buttons(fr, spec, J, 1.5, (T - 3.0, T - 7.0, 1.0))
    put_line(fr, spec, J['body'](3.6, T + 0.2), J['body'](-3.8, 0.0), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['cdd', 'bmd', 'bcc', 'obc', '.o.'], SATCHEL_LG, anchor=(1, 0))
    x, y = J['body'](-5.8, 0.6)
    put_bitmap(fr, sat, spec.names, x, y, name='satchel')


def alexei_coat_back(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, 0.0, -6, T - 3, 'coat', -0.5)
    put_line(fr, spec, J['body'](-3.6, T + 0.2), J['body'](3.8, 0.0), 0.55, 'strap', tone=2, name='strap')
    sat = bm(['bcd', 'bcd', 'obc', '.o.'], SATCHEL_LG, anchor=(1, 0))
    x, y = J['body'](5.8, 0.6)
    put_bitmap(fr, sat, spec.names, x, y, name='satchel')


# ----------------------------------------------------------------------------------- KONRAD
def konrad():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#2C3B5E',
        'trouser': '#2D2D36',
        'boot': '#2F2528',
        'patch': '#4A3A3A',
        'hat': '#3D3639',
        'band': ['#0E0B0D', '#17121A', '#1F1A22', '#2A2430', '#3A3240', '#4A4250'],
        'scarf': '#8E7656',
        'skin': SKIN['berlin'],
        'hair': '#7A6248',
        'eye': EYE_B,
        'tube': ('#525D57', {'max_tone': 3}),
        'cap': '#2B2B2E',
        'folder': '#5C3A28',
        'strap': '#3A2820',
        'button': '#1C1A22',
    })
    lg = merge(skin_legend(), digit_legend('hat'), {'k': ('band', 2), 'K': ('band', 3),
                                                   'a': ('hair', 1), 'b': ('hair', 2), 'c': ('hair', 3),
                                                   'd': ('hair', 4)})
    side_rows = [
        '....1233..',
        '...123344.',
        '...kkkkkK.',
        '0112233445',
        '...asssS..',
        '...bSSeS..',
        '...rSSSLL.',
        '...aSSmS..',
        '....sSS...',
        '.....s....',
    ]
    front_rows = [
        '....2332...',
        '...123321..',
        '...kKkkkk..',
        '01234443210',
        '...sSSSs...',
        '...SeLes...',
        '...SSLss...',
        '...sSmSs...',
        '....sSs....',
        '.....s.....',
    ]
    back_rows = [
        '....2332...',
        '...123321..',
        '...kkkkkk..',
        '01233333210',
        '...abbba...',
        '...abbba...',
        '...aabaa...',
        '....rsr....',
        '.....r.....',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 9), blink={(6, 5): 'S'}, talk={(6, 7): 'M'}),
        'front': faces(front_rows, lg, anchor=(5, 9), blink={(4, 5): 's', (6, 5): 's'}, talk={'m': 'M'}),
        'back': {'base': Bitmap(back_rows, lg, anchor=(5, 8))},
    }
    spec = Spec(id='konrad', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.5, torso=13.8, neck=1.8,
                coat=Coat(mat='coat', hem=-11.0, back=4.0, front=3.9, flare=1.2, chest=0.4, collar=1.8,
                          width_f=5.6, waist_f=4.0, hem_f=4.8, R=2.2, cyl=0.7),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=0.5, arm_r=(1.5, 1.3),
                style=dict(stride=7.2, swing=16.0, bob=1, walk_lean=1.5, hem=0.8, hold_f=(-4.0, 24.0),
                           arm_f_idle=(-4.0, 24.0)))
    spec.hooks = {'side': [('back0', konrad_tube_side), ('back1', konrad_folder_side), ('coat', konrad_coat_side)],
                  'front': [('back0', konrad_tube_front), ('arms', konrad_folder_front), ('coat', konrad_coat_front)],
                  'back': [('arms', konrad_folder_back), ('coat', konrad_coat_back), ('head', konrad_tube_back)]}
    return spec


def konrad_tube_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(-3.6, T + 2.6)      # top end sticks out above / behind the shoulder
    b = body(-4.9, 0.5)           # bottom end behind the hip
    put_line(fr, spec, a, b, 1.25, 'tube', name='tube', tone=None)
    put_line(fr, spec, a, (a[0] + (b[0] - a[0]) * 0.08, a[1] + (b[1] - a[1]) * 0.08), 1.3, 'cap', tone=2,
             name='tube_cap')


def konrad_tube_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(4.4, T + 2.8)        # sticks out above the right shoulder (screen right)
    b = body(-4.6, -2.5)
    put_line(fr, spec, a, b, 1.2, 'tube', name='tube', bias=-1.0)
    put_line(fr, spec, a, (a[0] - 0.6, a[1] + 0.9), 1.25, 'cap', tone=2, name='tube_cap')


def konrad_tube_back(fr, J, P, spec):
    body = J['body']
    T = J['T']
    a = body(-4.4, T + 2.8)
    b = body(4.6, -2.5)
    put_line(fr, spec, a, b, 1.25, 'tube', name='tube')
    put_line(fr, spec, a, (a[0] + 0.6, a[1] + 0.9), 1.3, 'cap', tone=2, name='tube_cap')
    put_line(fr, spec, body(-3.6, T + 0.6), body(3.6, 1.0), 0.5, 'strap', tone=2, name='strap')


FOLDER_LG = {'a': ('folder', 1), 'b': ('folder', 2), 'c': ('folder', 3), 'd': ('folder', 4), 'o': ('folder', 0)}


def konrad_folder_side(fr, J, P, spec):
    # leather folder clamped under the far arm: shows behind the back when walking
    x, y = J['wr_f']
    f = bm(['obbbbbo', 'obbbbbo', 'oaaaaao'], FOLDER_LG, anchor=(3, 1))
    put_bitmap(fr, f, spec.names, x - 1, y - 4, name='folder', bias=-1.0)


def konrad_folder_front(fr, J, P, spec):
    x, y = J['el_r']
    f = bm(['obd', 'bcd', 'bcd', 'bcd', 'bcd', 'bcd', 'bcc', 'oab'], FOLDER_LG, anchor=(0, 0))
    put_bitmap(fr, f, spec.names, x + 0.3, y - 3, name='folder')


def konrad_folder_back(fr, J, P, spec):
    x, y = J['el_l']
    f = bm(['bbo', 'cbb', 'cbb', 'cbb', 'cbb', 'cbb', 'bba', 'aao'], FOLDER_LG, anchor=(2, 0))
    put_bitmap(fr, f, spec.names, x - 0.3, y - 3, name='folder')


SCARF_LG = {'a': ('scarf', 1), 'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4), 'e': ('scarf', 5),
            'o': ('scarf', 0)}


def konrad_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.2, -11, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.2, (T - 4.0, T - 8.0, 0.0))
    put_line(fr, spec, body(2.2, T - 0.4), body(-2.6, 1.0), 0.5, 'strap', tone=2, name='strap')
    x, y = body(0.4, T + 1.2)
    sc = bm(['.cdde', 'bccdd', 'obbcd', '..bcd', '..bc.', '..ab.'], SCARF_LG, anchor=(2, 0))
    ph = P.get('phase', 0)
    put_bitmap(fr, sc, spec.names, x - (1 if walking(P) and ph % 4 in (1, 2) else 0), y, name='scarf')


def konrad_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, 0.5, -11, T - 3, 'coat', -0.8)
    buttons(fr, spec, J, 1.6, (T - 4.0, T - 8.0, 0.0))
    put_line(fr, spec, body(-3.6, T + 0.4), body(3.8, 0.5), 0.5, 'strap', tone=2, name='strap')
    x, y = body(0.0, T + 1.4)
    sc = bm(['.bcddcb.', 'obccddcb', '..bccb..', '..bc.b..', '..bc.bc.', '..ab..b.', '..a.....'], SCARF_LG,
            anchor=(4, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


def konrad_coat_back(fr, J, P, spec):
    body = J['body']
    T = J['T']
    column_line(fr, spec, J, 0.0, -11, -2, 'coat', -0.8)   # rear vent
    x, y = body(0.0, T + 1.4)
    sc = bm(['.bccccb.', 'obbbbbbo'], SCARF_LG, anchor=(4, 0))
    put_bitmap(fr, sc, spec.names, x, y, name='scarf')


# ----------------------------------------------------------------------------------- IRINA
def irina():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#3E5262',
        'skirt': '#3B3530',
        'trouser': '#4A4844',
        'boot': '#58574F',
        'patch': '#6A685E',
        'scarf': '#8E4E38',
        'skin': SKIN['karsk'],
        'hair': '#3A2A22',
        'eye': EYE_K,
        'board': '#6E5438',
        'paper': ['#3E3C34', '#7C7868', '#A8A390', '#C9C3AC', '#DED8C2', '#EEE9D6'],
        'metal': '#8C8E80',
        'button': '#22262A',
    })
    lg = merge(skin_legend(), digit_legend('scarf'), {'h': ('hair', 2), 'p': ('scarf', 4)})
    side_rows = [
        '...1233...',
        '..123p44..',
        '.1223344..',
        '012233345.',
        '01p222sSS.',
        '0122p2SeL.',
        '012221SSLL',
        '.12221sSm.',
        '..12210S..',
        '...1121...',
    ]
    front_rows = [
        '..12331..',
        '.1234431.',
        '12344p321',
        '12hSSSh21',
        '12SeLes21',
        '1pSSLss21',
        '12sSmSs21',
        '.12sSs21.',
        '..23432..',
        '...121...',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 9), blink={(7, 5): 'S'}, talk={(8, 7): 'M'}),
        'front': faces(front_rows, lg, anchor=(4, 9), blink={(3, 4): 's', (5, 4): 's'}, talk={'m': 'M'}),
    }
    spec = Spec(id='irina', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.5, torso=12.2, neck=1.6, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.5, 1.35), arm_r=(1.5, 1.25), hip_f=1.7,
                coat=Coat(mat='coat', hem=-3.5, back=3.9, front=3.8, flare=0.4, chest=0.8, collar=1.2,
                          width_f=5.0, waist_f=3.8, hem_f=4.4, R=2.2, cyl=0.65),
                skirt=Skirt(mat='skirt', top=3.0, hem=-14.0, back=3.4, front=3.4, flare=1.1, hem_f=4.6, waist_f=3.6),
                heads=heads, boots=boot_bitmaps('boot', style='valenki'), hands=hand_bitmaps('skin'),
                lean=1.0,
                style=dict(stride=4.3, swing=18.0, bob=1, walk_lean=2.0, hold_n=(6.0, 30.0), lift=2.6,
                           idle_feet=(1.0, -1.0), arm_f_idle=(-3.0, 10.0),
                           talk_n=[(10.0, 60.0), (14.0, 78.0), (12.0, 70.0), (9.0, 56.0)]))
    spec.hooks = {'side': [('coat', irina_coat_side), ('front', clipboard_side)],
                  'front': [('coat', irina_coat_front), ('arms', clipboard_front)]}
    return spec


def irina_coat_side(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-4, vmax=T - 1)
    column_line(fr, spec, J, spec.coat.front - 1.0, -3, T - 2, 'coat', -0.6)


def irina_coat_front(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-4, vmax=T - 1, light=spec.light_front.key)
    column_line(fr, spec, J, 0.0, -3, T - 1, 'coat', -1.0)
    buttons(fr, spec, J, 1.0, (T - 3.0, T - 6.0, 2.0))


CLIP_LG = {'a': ('board', 1), 'b': ('board', 2), 'c': ('board', 3), 'o': ('board', 0),
           'p': ('paper', 3), 'P': ('paper', 4), 'w': ('paper', 5), 'l': ('paper', 2), 'm': ('metal', 4)}


def clipboard_side(fr, J, P, spec):
    # clipboard carried flat against the hip, held by the near hand
    x, y = J['wr_n']
    cb = bm(['.omm..', 'oPwwPc', 'oplpPc', 'oPPwPc', 'opplPc', 'oPPPpc', 'oaaaab'], CLIP_LG, anchor=(2, 1))
    put_bitmap(fr, cb, spec.names, x + 0.5, y, name='clipboard')
    put_bitmap(fr, spec.hands['side'], spec.names, x + 0.2, y - 0.4, name='hand_n2')


def clipboard_front(fr, J, P, spec):
    x, y = J['wr_l']
    cb = bm(['.mm.', 'oPwc', 'oplc', 'oPPc', 'oplc', 'oaab'], CLIP_LG, anchor=(2, 1))
    put_bitmap(fr, cb, spec.names, x, y, name='clipboard')


# ----------------------------------------------------------------------------------- EMIL
def emil():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': '#5D6462',
        'inner': '#5E4C36',
        'trouser': '#33343B',
        'boot': '#2E2622',
        'patch': '#4A3E36',
        'skin': SKIN['berlin'],
        'grey': ['#2A2C30', '#4E5054', '#73767A', '#9A9C9C', '#BFC0BC', '#DCDCD6'],
        'glass': ['#101318', '#1E242C', '#3A4652', '#7A8C9A', '#B4C6D0', '#E4EEF2'],
        'eye': EYE_B,
        'pencil': '#9A6A3A',
        'button': '#2A2C2C',
    })
    lg = merge(skin_legend(), {'g': ('grey', 2), 'G': ('grey', 3), 'W': ('grey', 4), 'w': ('grey', 3),
                               'k': ('glass', 1), 'E': ('glass', 5), 'v': ('grey', 1)})
    lg['e'] = ('glass', 4, 'f')       # lens glint over the eye
    side_rows = [
        '....sSL...',
        '...sSSLL..',
        '..GgSSLL..',
        '.GggSSSL..',
        '.gggrSSSS.',
        '.gggSkkEk.',
        '.ggSSSSLL.',
        '..ggSWwm..',
        '..vgsSS...',
        '....ss....',
    ]
    front_rows = [
        '..sSLLs..',
        '.sSSLLSs.',
        'GSSSLSSsg',
        'GSSSSSSsg',
        'GkekSkekg',
        'gSSSLsssg',
        '.gsWWWsg.',
        '..sSmSs..',
        '...sSs...',
        '...rss...',
    ]
    heads = {
        'side': faces(side_rows, lg, anchor=(5, 9), blink={}, talk={'m': 'M'}),
        'front': faces(front_rows, lg, anchor=(4, 9), blink={}, talk={'m': 'M'}),
    }
    spec = Spec(id='emil', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.0, neck=1.4, thigh=10.0, shin=9.8, uarm=7.2, farm=6.3,
                leg_r=(1.6, 1.45), arm_r=(1.45, 1.25),
                coat=Coat(mat='coat', hem=-10.5, back=3.9, front=3.8, flare=0.9, chest=0.2, collar=1.0,
                          width_f=5.2, waist_f=4.1, hem_f=4.7, R=2.2, cyl=0.65),
                inner='inner', inner_w=1.6,
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=3.0, stoop=13.0, head_off=(1.0, -0.5),
                style=dict(stride=3.6, swing=10.0, bob=1, walk_lean=2.0, arm_n_idle=(4.0, 18.0),
                           arm_f_idle=(-4.0, 16.0), idle_feet=(1.0, -1.5),
                           talk_n=[(8.0, 56.0), (14.0, 82.0), (12.0, 74.0), (8.0, 50.0)]))
    spec.hooks = {'side': [('coat', emil_coat_side)], 'front': [('coat', emil_coat_front)]}
    return spec


def emil_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(spec.coat.front - 1.3, T - 0.8), body(spec.coat.front + 0.3, T - 3.0),
           body(spec.coat.front + 0.1, 2.0), body(spec.coat.front - 1.0, 2.0)]
    put_poly(fr, spec, pts, 'inner', R=1.0, cyl=0.3, cast=False, name='cardigan')
    x, y = body(1.2, T - 3.0)
    fr.recolor(x, y, M(spec, 'pencil'), 4)          # pencils in the breast pocket
    fr.recolor(x, y - 1, M(spec, 'pencil'), 3)


def emil_coat_front(fr, J, P, spec):
    T = J['T']
    buttons(fr, spec, J, 0.0, (T - 4.0, T - 7.0, 2.0), mat='button', tone=1)
    x, y = J['body'](3.0, T - 3.0)
    fr.recolor(x, y, M(spec, 'pencil'), 4)
    fr.recolor(x, y - 1, M(spec, 'pencil'), 3)


# ----------------------------------------------------------------------------------- WORKER A
def worker_a():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#4A4C3E',
        'trouser': '#33352F',
        'boot': '#5A5852',
        'patch': '#6A685E',
        'fur': '#6A5A48',
        'skin': SKIN['karsk'],
        'hair': '#2E2620',
        'eye': EYE_K,
        'wood': '#7A5E40',
        'steel': '#5A6260',
    })
    lg = merge(skin_legend(), digit_legend('fur'), {'h': ('hair', 2)})
    side_rows = [
        '..1233331.',
        '.R2344443.',
        '0R2333344.',
        '0122223334',
        '.hhhssSS..',
        '.hhrSSeL..',
        '.hhrSSSLL.',
        '..hsSSSm..',
        '...ssSS...',
        '....ss....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 9), blink={(6, 5): 'S'}, talk={(7, 7): 'M'})}
    spec = Spec(id='worker_a', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.6,
                coat=Coat(mat='coat', hem=-4.0, back=4.9, front=4.6, flare=0.4, chest=0.6, collar=1.4,
                          width_f=6.0, waist_f=4.8, hem_f=5.0, R=2.6, cyl=0.6),
                heads=heads, boots=boot_bitmaps('boot', style='valenki'), hands=hand_bitmaps('skin'),
                lean=3.0, arm_r=(1.75, 1.45),
                style=dict(stride=4.8, swing=20.0, bob=1, walk_lean=3.0, hold_n=(18.0, 84.0), lift=2.8))
    spec.hooks = {'side': [('coat', worker_coat_side), ('coat', shovel_side)]}
    return spec


def worker_coat_side(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=1, vmin=-4, vmax=T - 1)
    column_line(fr, spec, J, spec.coat.front - 1.0, -4, T - 2, 'coat', -0.6)


SHOVEL_LG = {'a': ('steel', 1), 'b': ('steel', 2), 'c': ('steel', 3), 'd': ('steel', 4), 'o': ('steel', 0)}


def shovel_side(fr, J, P, spec):
    """Shovel resting on the near shoulder: shaft from the hand (chest height) up over the shoulder,
    blade behind the head."""
    hx, hy = J['wr_n']
    sx, sy = J['sh_n']
    tx, ty = sx - 1.0, sy - 3.0
    dx, dy = tx - hx, ty - hy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    a = (hx - ux * 2.5, hy - uy * 2.5)
    b = (hx + ux * 19.0, hy + uy * 19.0)
    put_line(fr, spec, a, b, 0.6, 'wood', name='shaft', cast=True)
    blade = bm(['.cd.', 'bccd', 'bccd', 'obcc', '.ob.'], SHOVEL_LG, anchor=(2, 4))
    put_bitmap(fr, blade, spec.names, b[0] + ux * 1.5, b[1] + uy * 1.5, name='blade')


# ----------------------------------------------------------------------------------- BABUSHKA
def babushka():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#3F3A35',
        'skirt': '#2E2B2A',
        'trouser': '#3A3634',
        'boot': '#4E4C46',
        'patch': '#6A685E',
        'scarf': '#4E4A5E',
        'skin': SKIN['karsk'],
        'eye': EYE_K,
        'cloth': '#8C7A58',
        'button': '#1E1C1A',
    })
    lg = merge(skin_legend(), digit_legend('scarf'), {'p': ('scarf', 4)})
    side_rows = [
        '...1233...',
        '..12p344..',
        '.1223344..',
        '0122p3345.',
        '012222sSS.',
        '01p222SeL.',
        '012221SSLL',
        '.12221rSm.',
        '..12210s..',
        '..1211r...',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 9), blink={(7, 5): 'S'}, talk={(8, 7): 'M'})}
    spec = Spec(id='babushka', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=19.0, torso=12.0, neck=1.2, thigh=8.9, shin=8.8, uarm=6.6, farm=5.8,
                leg_r=(1.5, 1.4), arm_r=(1.5, 1.25),
                coat=Coat(mat='coat', hem=-12.5, back=4.3, front=4.0, flare=1.3, chest=0.6, collar=1.0,
                          width_f=5.2, waist_f=4.4, hem_f=5.2, R=2.4, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='valenki'), hands=hand_bitmaps('skin'),
                lean=5.0, stoop=17.0, head_off=(1.2, -0.3),
                style=dict(stride=3.2, swing=10.0, bob=1, walk_lean=2.0, hold_n=(8.0, 10.0), lift=2.0,
                           idle_feet=(1.0, -1.0)))
    spec.hooks = {'side': [('coat', babushka_coat_side), ('front', bundle_side)]}
    return spec


def babushka_coat_side(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -12, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 3.0, T - 6.0, 0.0))


BUNDLE_LG = {'a': ('cloth', 1), 'b': ('cloth', 2), 'c': ('cloth', 3), 'd': ('cloth', 4), 'o': ('cloth', 0)}


def bundle_side(fr, J, P, spec):
    x, y = J['wr_n']
    b = bm(['..cd..', '.bccd.', 'obcdcd', 'obccdc', 'obbccc', '.oabb.'], BUNDLE_LG, anchor=(3, 0))
    put_bitmap(fr, b, spec.names, x + 0.5, y + 0.5, name='bundle')
    put_bitmap(fr, spec.hands['side'], spec.names, x + 0.3, y + 0.3, name='hand_n2')


# ----------------------------------------------------------------------------------- CHILD (Karsk)
def child_a():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#55634E',
        'trouser': '#3A3A3C',
        'boot': '#55544E',
        'patch': '#6A685E',
        'knit': '#8A4436',
        'scarf': '#8A4436',
        'skin': SKIN['karsk'],
        'hair': '#5A4030',
        'eye': EYE_K,
    })
    lg = merge(skin_legend(), digit_legend('knit'), {'h': ('hair', 2)})
    side_rows = [
        '...34...',
        '..1234..',
        '.122343.',
        '.1222334',
        '.1hsSSS.',
        '.1hSSeL.',
        '..hSSSL.',
        '...sSm..',
        '....s...',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(4, 8), blink={(5, 5): 'S'}, talk={(5, 7): 'M'})}
    spec = Spec(id='child_a', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=12.5, torso=8.4, neck=1.0, thigh=6.0, shin=5.9, ankle_h=2.0, uarm=4.6, farm=4.0,
                leg_r=(1.35, 1.25), arm_r=(1.3, 1.1), hip_f=1.4, sh_v=-1.0,
                coat=Coat(mat='coat', hem=-3.0, back=3.1, front=3.0, flare=0.5, chest=0.3, collar=0.8,
                          width_f=4.2, waist_f=3.5, hem_f=3.9, R=1.8, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='valenki'), hands=hand_bitmaps('skin'),
                lean=1.0,
                style=dict(stride=3.0, swing=24.0, bob=1, up=-1, walk_lean=2.0, lift=2.0, idle_feet=(1.0, -1.0)))
    spec.hooks = {'side': [('coat', child_scarf_side)]}
    return spec


def child_scarf_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    x, y = body(0.2, T + 0.8)
    sc = bm(['.bcd', 'obcd', '..bc', '..b.'], {'b': ('scarf', 2), 'c': ('scarf', 3), 'd': ('scarf', 4),
                                           'o': ('scarf', 0)}, anchor=(2, 0))
    ph = P.get('phase', 0)
    put_bitmap(fr, sc, spec.names, x - (1 if walking(P) and ph % 4 in (0, 1) else 0), y, name='scarf')


# ----------------------------------------------------------------------------------- BERLIN FAMILY
def berlin_father():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#5A4A3C',
        'trouser': '#3A3940',
        'boot': '#2E2426',
        'patch': '#4A3A3A',
        'cap': '#4E4A48',
        'skin': SKIN['berlin'],
        'hair': '#4A3A2E',
        'eye': EYE_B,
        'crate': '#8A6A48',
        'button': '#2A2222',
    })
    lg = merge(skin_legend(), digit_legend('cap'), {'h': ('hair', 2), 'H': ('hair', 3)})
    side_rows = [
        '..122333..',
        '.12233344.',
        '0122334455',
        '.hhrssSS..',
        '.hhrSSeS..',
        '.hhrSSSLL.',
        '..hsSSm...',
        '...rsSS...',
        '....ss....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 8), blink={(6, 4): 'S'}, talk={(6, 6): 'M'})}
    spec = Spec(id='berlin_father', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.0, torso=13.6,
                coat=Coat(mat='coat', hem=-5.0, back=4.2, front=4.0, flare=0.6, chest=0.5, collar=1.3,
                          width_f=5.6, waist_f=4.3, hem_f=4.7, R=2.3, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=3.0,
                style=dict(stride=4.6, swing=0.0, bob=1, walk_lean=2.5, hold_n=(26.0, 66.0), hold_f=(26.0, 66.0),
                           lift=2.6, dx=-1.5))
    spec.hooks = {'side': [('front', crate_side), ('coat', father_coat_side)]}
    return spec


def father_coat_side(fr, J, P, spec):
    T = J['T']
    column_line(fr, spec, J, spec.coat.front - 1.0, -5, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.0, (T - 4.0, T - 8.0))


CRATE_LG = {'a': ('crate', 1), 'b': ('crate', 2), 'c': ('crate', 3), 'd': ('crate', 4), 'e': ('crate', 5),
            'o': ('crate', 0)}


def crate_side(fr, J, P, spec):
    # a wooden crate with belongings carried in front of the chest (both hands)
    x, y = J['wr_n']
    cr = bm(['.oddeed.', 'obccccdd', 'obbbbbbd', 'obccccdc', 'obbbbbbc', 'obccccdc', 'oaaaaaab'], CRATE_LG,
            anchor=(2, 3))
    put_bitmap(fr, cr, spec.names, x, y, name='crate')
    put_bitmap(fr, spec.hands['side'], spec.names, x + 0.2, y - 0.2, name='hand_n2')


def berlin_mother():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#5A4452',
        'trouser': '#4A4046',
        'boot': '#2B2024',
        'patch': '#4A3A3A',
        'hat': '#2F2A33',
        'skin': SKIN['berlin'],
        'hair': '#5C3E2C',
        'eye': EYE_B,
        'case': '#6E5038',
        'metal': '#8A8478',
        'belt': '#3A2A30',
    })
    lg = merge(skin_legend(), digit_legend('hat'), {'h': ('hair', 2), 'H': ('hair', 3), 'g': ('hair', 1)})
    side_rows = [
        '...12233..',
        '..1223344.',
        '..0111111.',
        '.hhhsSSS..',
        'gHhhSSeL..',
        'ghhhSSSLL.',
        'ghhhsSSm..',
        '.ghhrSS...',
        '..g..s....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 8), blink={(6, 4): 'S'}, talk={(7, 6): 'M'})}
    spec = Spec(id='berlin_mother', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.5, torso=12.2, neck=1.6, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.4, 1.2), arm_r=(1.45, 1.2), hip_f=1.7,
                coat=Coat(mat='coat', hem=-11.0, back=3.8, front=3.7, flare=1.4, chest=0.8, collar=1.2,
                          width_f=4.9, waist_f=3.6, hem_f=4.8, R=2.2, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=-1.0,
                style=dict(stride=4.0, swing=16.0, bob=1, walk_lean=1.5, hold_n=(4.0, 4.0), lift=2.4,
                           idle_feet=(1.0, -1.0)))
    spec.hooks = {'side': [('coat', mother_coat_side), ('front', suitcase_side)]}
    return spec


def mother_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-spec.coat.back + 0.3, 3.0), body(spec.coat.front - 0.3, 3.0), 0.55, 'belt', tone=2,
             name='belt')
    column_line(fr, spec, J, spec.coat.front - 1.0, -11, T - 2, 'coat', -0.6)


CASE_LG = {'a': ('case', 1), 'b': ('case', 2), 'c': ('case', 3), 'd': ('case', 4), 'e': ('case', 5),
           'o': ('case', 0), 'm': ('metal', 4), 'n': ('metal', 2)}


def suitcase_side(fr, J, P, spec):
    x, y = J['wr_n']
    sc = bm(['...nn....', '..n..n...', 'ocddddddd', 'obcccccdd', 'obmccccmc', 'obcccccdc', 'obbbbbbcc',
             'oaaaaaaab'], CASE_LG, anchor=(4, 1))
    put_bitmap(fr, sc, spec.names, x, y + 0.5, name='suitcase')
    put_bitmap(fr, spec.hands['side'], spec.names, x, y, name='hand_n2')


def berlin_child():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#6A5846',
        'trouser': '#50484C',
        'boot': '#2B2024',
        'patch': '#4A3A3A',
        'beret': '#343448',
        'skin': SKIN['berlin'],
        'hair': '#6E5034',
        'eye': EYE_B,
        'toy': '#8A6A4A',
        'sock': '#8C8478',
    })
    lg = merge(skin_legend(), digit_legend('beret'), {'h': ('hair', 2), 'H': ('hair', 3)})
    side_rows = [
        '..1234..',
        '.123344.',
        '0122223.',
        '.hhsSSS.',
        '.hhSSeL.',
        '.hhSSSLL',
        '..hsSm..',
        '...ss...',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(4, 7), blink={(5, 4): 'S'}, talk={(5, 6): 'M'})}
    spec = Spec(id='berlin_child', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=13.5, torso=8.8, neck=1.0, thigh=6.4, shin=6.4, ankle_h=2.0, uarm=4.8, farm=4.2,
                leg_r=(1.3, 1.15), arm_r=(1.3, 1.1), hip_f=1.4, sh_v=-1.0, trouser='sock',
                coat=Coat(mat='coat', hem=-4.0, back=3.1, front=3.0, flare=0.7, chest=0.3, collar=0.8,
                          width_f=4.2, waist_f=3.5, hem_f=4.0, R=1.8, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=0.0,
                style=dict(stride=3.2, swing=22.0, bob=1, up=-1, walk_lean=2.0, lift=2.0, hold_n=(10.0, 30.0),
                           idle_feet=(1.0, -1.0)))
    spec.hooks = {'side': [('front', toy_side)]}
    return spec


TOY_LG = {'a': ('toy', 1), 'b': ('toy', 2), 'c': ('toy', 3), 'd': ('toy', 4), 'o': ('toy', 0),
          'e': ('eye', 1)}


def toy_side(fr, J, P, spec):
    x, y = J['wr_n']
    t = bm(['c.c', 'cdc', 'bec', 'bcc', 'b.b'], TOY_LG, anchor=(1, 0))
    put_bitmap(fr, t, spec.names, x + 1, y + 1, name='toy')
    put_bitmap(fr, spec.hands['side'], spec.names, x + 0.3, y + 0.3, name='hand_n2')


# ----------------------------------------------------------------------------------- CLERK
def clerk():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': '#4C5157',
        'trouser': '#3F434A',
        'boot': '#1E1A1C',
        'patch': '#3A3436',
        'sleeve': '#24262C',
        'shirt': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C6C6BA', '#DCDCCE', '#EEEEE2'],
        'tie': '#4A2A30',
        'skin': SKIN['berlin'],
        'hair': '#2A2224',
        'eye': EYE_B,
        'file': ['#4A4030', '#7A6A4A', '#A08C62', '#BCA878', '#D2BF8E', '#E4D3A6'],
        'button': '#1C1C22',
    })
    lg = merge(skin_legend(), {'a': ('hair', 1), 'b': ('hair', 2), 'c': ('hair', 3), 'd': ('hair', 4),
                               'o': ('hair', 0)})
    side_rows = [
        '...bbcc...',
        '..abbccd..',
        '.abbbbcdd.',
        '.aabbsSS..',
        '.aabrSeS..',
        '.aabrSSLL.',
        '..aasSm...',
        '...rsSS...',
        '....ss....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 8), blink={(6, 4): 'S'}, talk={(6, 6): 'M'})}
    spec = Spec(id='clerk', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.0, torso=13.4, neck=1.8,
                coat=Coat(mat='coat', hem=-3.0, back=3.7, front=3.6, flare=0.2, chest=0.4, collar=1.0,
                          width_f=5.2, waist_f=3.9, hem_f=4.0, R=2.0, cyl=0.7),
                heads=heads, boots=boot_bitmaps('boot', style='shoe'), hands=hand_bitmaps('skin'),
                lean=0.5, arm_r=(1.4, 1.2), leg_r=(1.6, 1.45),
                style=dict(stride=4.8, swing=16.0, bob=1, walk_lean=1.0, hold_n=(4.0, 70.0), lift=2.6))
    spec.hooks = {'side': [('coat', clerk_coat_side), ('front', file_side)]}
    return spec


def clerk_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    pts = [body(spec.coat.front - 1.4, T + 0.6), body(spec.coat.front - 0.2, T - 0.8),
           body(spec.coat.front - 0.2, T - 5.0), body(spec.coat.front - 1.1, T - 5.0)]
    put_poly(fr, spec, pts, 'shirt', tone=4, R=1.0, cyl=0.2, cast=False, name='shirt')
    put_line(fr, spec, body(spec.coat.front - 0.5, T - 1.5), body(spec.coat.front - 0.4, T - 5.5), 0.5, 'tie',
             tone=3, name='tie')
    buttons(fr, spec, J, spec.coat.front - 0.8, (T - 7.0, 1.0))


FILE_LG = {'a': ('file', 1), 'b': ('file', 2), 'c': ('file', 3), 'd': ('file', 4), 'e': ('file', 5),
           'o': ('file', 0)}


def file_side(fr, J, P, spec):
    # file folder held under the near forearm; black sleeve protector (Aermelschoner) on the forearm
    x, y = J['wr_n']
    f = bm(['oddddeo', 'obccccd', 'obccccd', 'obccccd', 'oaaaaab'], FILE_LG, anchor=(4, 1))
    put_bitmap(fr, f, spec.names, x, y, name='file')
    put_line(fr, spec, J['el_n'], J['wr_n'], 1.25, 'sleeve', name='protector')
    put_bitmap(fr, spec.hands['side'], spec.names, x + 0.8, y + 0.2, name='hand_n2')


# ----------------------------------------------------------------------------------- GUARD
def guard():
    scene = 'berlin'
    mats, names = materials(scene, {
        'coat': '#55595A',
        'trouser': '#3C3F42',
        'boot': '#1E1B1D',
        'patch': '#3A3436',
        'cap': '#4E5354',
        'visor': ['#08090B', '#121418', '#1E2126', '#2C3036', '#4A5058', '#7A828C'],
        'belt': '#2A2422',
        'metal': '#9A968A',
        'skin': SKIN['berlin'],
        'hair': '#3A3030',
        'eye': EYE_B,
        'button': '#2E3134',
    })
    lg = merge(skin_legend(), digit_legend('cap'), {'v': ('visor', 1), 'V': ('visor', 3), 'h': ('hair', 2)})
    side_rows = [
        '..1233344.',
        '.12233445.',
        '..122334..',
        '..011vvVV.',
        '..hrssSS..',
        '..hrSSeS..',
        '..hhSSSLL.',
        '...hsSm...',
        '....sSS...',
        '.....s....',
    ]
    heads = {'side': faces(side_rows, lg, anchor=(5, 9), blink={(6, 5): 'S'}, talk={(6, 7): 'M'})}
    spec = Spec(id='guard', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=22.5, torso=14.0, neck=1.6,
                coat=Coat(mat='coat', hem=-14.0, back=4.3, front=4.3, flare=1.5, chest=0.8, collar=1.6,
                          width_f=6.0, waist_f=4.4, hem_f=5.4, R=2.3, cyl=0.65),
                heads=heads, boots=boot_bitmaps('boot', style='tall'), hands=hand_bitmaps('skin'),
                lean=-0.5,
                style=dict(stride=5.0, swing=12.0, bob=1, walk_lean=0.5, lift=2.6, hem=0.4,
                           arm_n_idle=(-24.0, 100.0), arm_f_idle=(-24.0, 100.0), idle_feet=(1.5, -1.5)))
    spec.hooks = {'side': [('coat', guard_coat_side)]}
    return spec


def guard_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-spec.coat.back + 0.3, 2.6), body(spec.coat.front - 0.3, 2.6), 0.6, 'belt', tone=2,
             name='belt')
    x, y = body(spec.coat.front - 0.6, 2.6)
    fr.recolor(x, y, M(spec, 'metal'), 4)
    column_line(fr, spec, J, spec.coat.front - 1.2, -14, T - 2, 'coat', -0.6)
    buttons(fr, spec, J, spec.coat.front - 1.2, (T - 3.0, T - 6.0, T - 9.0), mat='button', tone=1)


CAST = {
    'alexei': alexei, 'konrad': konrad, 'irina': irina, 'emil': emil,
    'worker_a': worker_a, 'babushka': babushka, 'child_a': child_a,
    'berlin_father': berlin_father, 'berlin_mother': berlin_mother, 'berlin_child': berlin_child,
    'clerk': clerk, 'guard': guard,
}
