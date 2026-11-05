"""chargen_cast_new -- the four characters added in round 2 (TECHNICAL_ARCHITECTURE section 12.6):

  librarian  Berlin archive reading room: woman ~55, grey bun, glasses on a chain, cardigan, long skirt
  porter     Berlin doorman: older man, uniform cap with braid, long double-breasted coat, white moustache
  vendor     Karsk tea stall: woman ~50, dark flowered shawl, padded jacket, apron; pours tea (work row)
  worker_b   Karsk rail worker: padded telogreika, ushanka tied under the chin, felt boots, warms his hands
"""
from __future__ import annotations

import math

import chargen_heads as HD
from chargen_body import Coat, Skirt, Spec, M, make_hands
from chargen_cast import (EYE_B, EYE_K, GLASS, RIM, SKIN, belt_front, belt_side, bm, boot_bitmaps, buttons, flap,
                          column_line, lapels_front, materials, merge, put_bitmap, put_line, put_poly, quilt_lines,
                          row_line, side_light, tones, walking, lag_dx, _puff)


# =========================================================================================== LIBRARIAN
def librarian():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': ('#6A5868', {'texture': 'knit'}),        # plum-heather cardigan
        'skirt': '#37323E',
        'trouser': '#5A4E4E',                            # stockings
        'boot': ('#2A2024', {'glossy': True}),
        'patch': '#3A3436',
        'blouse': ['#3A3C3A', '#7A7C76', '#A6A89E', '#C8C6B8', '#DEDCCC', '#EEEDE2'],
        'skin': SKIN['old'],
        'hair': ['#2E2E30', '#55575A', '#7C7E80', '#A2A3A2', '#C4C4BE', '#E0DFD8'],
        'eye': EYE_B,
        'glass': GLASS,
        'book': ('#6A2E2A', {'glossy': True}),
        'page': ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'],
        'button': '#2A2026',
        'hat': '#6A5868',
        'band': '#2A2A30',
        'ink': '#2A2A3A',
        'metal': '#A8A49A',
    })
    lg = HD.base_legend()
    spec = Spec(id='librarian', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.5, torso=12.4, neck=1.2, thigh=9.6, shin=9.4, uarm=7.0, farm=6.0,
                leg_r=(1.25, 1.1), arm_r=(1.55, 1.3), hip_f=1.6,
                coat=Coat(mat='coat', hem=-2.0, back=3.8, front=3.8, flare=0.4, chest=1.0, collar=0.6,
                          width_f=5.0, waist_f=3.8, hem_f=4.2, R=2.2, cyl=0.65, hunch=0.4),
                skirt=Skirt(mat='skirt', top=3.0, hem=-17.0, back=3.5, front=3.4, flare=1.4, hem_f=4.8,
                            waist_f=3.7, folds=0.7),
                heads=HD.librarian(lg), boots=boot_bitmaps('boot', style='lady'), hands=make_hands('skin'),
                lean=1.0, stoop=4.0,
                style=dict(stride=4.0, swing=14.0, bob=1, walk_lean=1.5, lift=2.2, idle_feet=(1.0, -1.0),
                           hold_f=(-10.0, 120.0), arm_f_idle=(-10.0, 120.0), arm_n_idle=(4.0, 14.0),
                           gesture='push_glasses', work='stamp'))
    spec.hooks = {'side': [('coat', librarian_coat_side), ('coat', book_side), ('head', librarian_chain_side),
                           ('front', stamp_side)],
                  'front': [('coat', librarian_coat_front), ('arms', book_front)]}
    return spec


def librarian_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    # blouse collar points over the cardigan neckline
    put_poly(fr, spec, [body(c.front - 1.6, T + 0.6), body(c.front + 0.2, T - 0.2), body(c.front - 0.6, T - 1.6)],
             'blouse', tone=4, R=0.8, cyl=0.2, cast=False, name='blouse')
    column_line(fr, spec, J, c.front - 0.8, -2, T - 2, 'coat', -0.8)
    buttons(fr, spec, J, c.front - 0.8, (T - 3.0, T - 6.0, T - 9.0, 1.0))
    flap(fr, spec, J, c.front - 3.0, c.front - 1.6, 1.0, 'coat')


def librarian_chain_side(fr, J, P, spec):
    """Spectacle chain hanging from the temple down to the collar."""
    hx, hy = J['head_at']
    for k in range(3):
        fr.px(hx - 2.0 + k * 0.3, hy - 2 + k, M(spec, 'metal'), 3)


def librarian_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_poly(fr, spec, [body(-1.8, T + 0.6), body(1.8, T + 0.6), body(0.0, T - 2.6)], 'blouse', tone=4, R=0.8,
             cyl=0.2, cast=False, name='blouse')
    lapels_front(fr, spec, J, depth=6.0, width=1.8)
    buttons(fr, spec, J, 0.0, (T - 4.0, T - 6.5, T - 9.0), tone=1)


BOOK_LG = merge(tones('book'), {'p': ('page', 4), 'P': ('page', 5), 'q': ('page', 3)})


def book_side(fr, J, P, spec):
    """Cloth-bound book held flat against the chest by the far arm (drawn over the cardigan, under the
    near arm); its spine faces the viewer, the page block shows on the key side."""
    if P.get('arm_f') != spec.style.get('hold_f'):
        return
    x, y = J['wr_f']
    b = bm(['obbbbP', 'obcccp', 'obcccp', 'obcccp', 'obcccq', 'oaaaao'], BOOK_LG, anchor=(5, 2))
    put_bitmap(fr, b, spec.names, x + 0.5, y, name='book')


def book_front(fr, J, P, spec):
    x, y = J['wr_l']
    b = bm(['obbbo', 'obccP', 'obccp', 'obccp', 'oaaao'], BOOK_LG, anchor=(2, 1))
    put_bitmap(fr, b, spec.names, x + 1, y - 2, name='book')


def stamp_side(fr, J, P, spec):
    """Rubber stamp in the near hand during the 'stamp' work loop (+ ink mark when it lands)."""
    if 'thump' not in P and not P.get('stamp_row'):
        return
    x, y = J['wr_n']
    s = bm(['.b.', 'bcb', 'oao'], merge(tones('book'), {}), anchor=(1, 0))
    put_bitmap(fr, s, spec.names, x + 1.5, y + 0.5, name='stamp')


# =========================================================================================== PORTER
def porter():
    scene = 'archive'
    mats, names = materials(scene, {
        'coat': '#2F3549',
        'trouser': '#2A2E3C',
        'boot': ('#1C181C', {'glossy': True}),
        'patch': '#3A3436',
        'hat': '#2F3549',
        'band': ['#3E2E18', '#6A4E26', '#8E6E36', '#A8884A', '#C8A862', '#E4CC8A'],   # braid / brass
        'visor': ['#08090B', '#121418', '#1E2126', '#2C3036', '#4A5058', '#7A828C'],
        'brass': ['#3E2E18', '#6A4E26', '#8E6E36', '#A8884A', '#C8A862', '#E4CC8A'],
        'skin': SKIN['old'],
        'hair': ['#3A3836', '#6E6A64', '#9A968E', '#BEBAB0', '#D8D4CA', '#EEEAE0'],
        'eye': EYE_B,
        'glass': GLASS,
        'button': '#A8884A',
        'collar': '#252A3A',
    })
    lg = HD.base_legend()
    lg.update({'y': ('visor', 1), 'V': ('visor', 2), 'x': ('visor', 3), '0': ('visor', 0)})
    spec = Spec(id='porter', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.6, neck=1.2,
                coat=Coat(mat='coat', hem=-13.0, back=4.4, front=4.5, flare=1.2, chest=1.1, collar=1.4,
                          width_f=6.0, waist_f=4.8, hem_f=5.4, R=2.3, cyl=0.65, folds=0.7, hunch=0.5),
                heads=HD.porter(lg), boots=boot_bitmaps('boot', style='shoe'), hands=make_hands('skin'),
                lean=-0.5, stoop=3.0, arm_r=(1.7, 1.45),
                style=dict(stride=4.4, swing=12.0, bob=1, walk_lean=1.0, lift=2.4, idle_feet=(1.5, -1.5),
                           arm_n_idle=(-8.0, 30.0), arm_f_idle=(-8.0, 30.0), gesture='check_watch', work='watch',
                           front_abd=4.0))
    spec.hooks = {'side': [('coat', porter_coat_side), ('head', porter_collar_side), ('front', pocket_watch_side)],
                  'front': [('coat', porter_coat_front), ('head', porter_collar_front)]}
    return spec


def porter_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    column_line(fr, spec, J, c.front - 1.4, c.hem + 1, T - 2, 'coat', -0.7)
    buttons(fr, spec, J, c.front - 0.6, (T - 3.0, T - 6.0, T - 9.0), mat='brass', tone=4)
    buttons(fr, spec, J, c.front - 2.4, (T - 3.0, T - 6.0, T - 9.0), mat='brass', tone=3)
    flap(fr, spec, J, c.front - 3.4, c.front - 1.8, -1.6, 'coat')
    # watch chain across the waistcoat line
    for k in range(3):
        x, y = J['body'](c.front - 1.2 - k * 0.6, 2.4 - abs(k - 1) * 0.4)
        fr.recolor(x, y, M(spec, 'brass'), 4 if k == 1 else 3)


def porter_coat_front(fr, J, P, spec):
    T = J['T']
    for u, t in ((-1.4, 4), (1.4, 3)):
        buttons(fr, spec, J, u, (T - 3.0, T - 6.0, T - 9.0), mat='brass', tone=t)
    column_line(fr, spec, J, 0.2, spec.coat.hem + 1, T - 2, 'coat', -0.8)
    lapels_front(fr, spec, J, depth=3.0, width=3.0)
    flap(fr, spec, J, -4.0, -2.2, -1.6, 'coat')
    flap(fr, spec, J, 2.2, 4.0, -1.6, 'coat')


def porter_collar_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_line(fr, spec, body(-1.6, T + 1.2), body(1.2, T + 0.8), 0.95, 'collar', name='collar')


def porter_collar_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    put_poly(fr, spec, [body(-2.8, T + 1.6), body(-0.4, T - 0.4), body(0.4, T - 0.4), body(2.8, T + 1.6),
                        body(2.4, T + 0.0), body(-2.4, T + 0.0)], 'collar', R=1.0, cyl=0.3, name='collar')


def pocket_watch_side(fr, J, P, spec):
    if not P.get('watch'):
        return
    x, y = J['wr_n']
    w = bm(['.d.', 'ded', '.c.'], {'c': ('brass', 3), 'd': ('brass', 4), 'e': ('brass', 5)}, anchor=(1, 1))
    put_bitmap(fr, w, spec.names, x + 1.5, y - 0.5, name='watch')


# =========================================================================================== VENDOR
def vendor():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#46483F',                               # padded telogreika
        'skirt': '#3A3230',
        'trouser': '#3A3534',
        'boot': ('#5A564E', {'texture': 'felt'}),
        'galosh': '#1C1C20',
        'patch': '#6A685E',
        'hat': '#2C2834',                                # dark shawl ...
        'band': '#A8402E',                               # ... with red roses
        'apron': ['#3E3C36', '#5E5C52', '#76746A', '#8C897C', '#A2A090', '#B6B4A4'],
        'skin': SKIN['ruddy'],
        'hair': '#3A2A22',
        'eye': EYE_K,
        'glass': GLASS,
        'kettle': ('#5E7A86', {'glossy': True}),
        'tea': ['#2A140A', '#4A2410', '#6E3A18', '#8E5226', '#B07038', '#D09050'],
        'metal': '#9A9A8A',
        'button': '#22241E',
        'breath': ['#6E7C7A', '#8E9C98', '#AEBAB4', '#C4CEC8', '#DCE2DC', '#EEF2EE'],
    })
    lg = HD.base_legend()
    spec = Spec(id='vendor', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=20.0, torso=12.6, neck=1.2, thigh=9.4, shin=9.2, uarm=6.8, farm=5.9,
                leg_r=(1.55, 1.4), arm_r=(1.8, 1.5), hip_f=1.8,
                coat=Coat(mat='coat', hem=-3.0, back=4.6, front=4.6, flare=0.6, chest=1.2, collar=1.0,
                          width_f=5.8, waist_f=4.8, hem_f=5.0, R=2.5, cyl=0.6, hunch=0.4),
                skirt=Skirt(mat='skirt', top=3.0, hem=-15.5, back=3.8, front=3.8, flare=1.3, hem_f=5.0,
                            waist_f=4.2, folds=0.6),
                heads=HD.vendor(lg), boots=boot_bitmaps('boot', sole='galosh', style='valenki'),
                hands=make_hands('skin'), lean=1.5,
                style=dict(stride=3.8, swing=16.0, bob=1, walk_lean=2.0, lift=2.2, idle_feet=(1.2, -1.2),
                           arm_n_idle=(6.0, 18.0), arm_f_idle=(-2.0, 14.0), gesture='blow_hands', work='pour'))
    spec.hooks = {'side': [('coat', vendor_coat_side), ('front', kettle_side), ('front', _puff)],
                  'front': [('coat', vendor_coat_front)]}
    return spec


def vendor_coat_side(fr, J, P, spec):
    body = J['body']
    T = J['T']
    c = spec.coat
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-2, vmax=T - 1)
    # apron: bib + skirt part over the front, tied at the back
    pts = [body(c.front - 1.2, T - 2.0), body(c.front + 0.3, T - 2.4), body(c.front + 0.6, 2.0),
           J['skirt'](c.front + 1.5, -12.0), J['skirt'](c.front - 0.6, -12.0), body(c.front - 1.0, 2.0)]
    put_poly(fr, spec, pts, 'apron', R=1.2, cyl=0.6, cast=True, name='apron', inline=True)
    put_line(fr, spec, body(-c.back + 0.4, 3.2), body(c.front - 1.6, 3.2), 0.45, 'apron', tone=2, name='apron_tie')
    row_line(fr, spec, J, c.front - 1.4, c.front + 0.2, -3.0, 'apron', -1.0)   # pocket
    # tea stain
    x, y = body(c.front - 0.2, -6.0)
    fr.recolor(x, y, M(spec, 'apron'), 2)


def vendor_coat_front(fr, J, P, spec):
    body = J['body']
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=0, vmin=-2, vmax=T - 1, light=spec.light_front.key)
    pts = [body(-2.4, T - 2.0), body(2.4, T - 2.0), body(2.6, 2.6), body(4.0, -13.0), body(-4.0, -13.0),
           body(-2.6, 2.6)]
    put_poly(fr, spec, pts, 'apron', R=1.4, cyl=0.6, cast=True, name='apron', inline=True)
    put_line(fr, spec, body(-4.6, 3.2), body(-2.6, 3.2), 0.45, 'apron', tone=2, name='apron_tie_l')
    put_line(fr, spec, body(2.6, 3.2), body(4.6, 3.2), 0.45, 'apron', tone=2, name='apron_tie_r')
    row_line(fr, spec, J, -1.0, 1.0, -3.0, 'apron', -1.0)
    x, y = body(-1.2, -7.0)
    fr.recolor(x, y, M(spec, 'apron'), 2)


KETTLE_LG = merge(tones('kettle'), {'t': ('tea', 3), 'T': ('tea', 4), 'm': ('metal', 4)})


def kettle_side(fr, J, P, spec):
    """Enamel teapot in the near hand during the pour loop; a thin tea stream on the pour frames."""
    if 'tilt' not in P:
        return
    x, y = J['wr_n']
    tilt = P.get('tilt', 0)
    rows = {0: ['.mm..', 'bccd.', 'bcdde', 'bccd.', '.oo..'],
            1: ['.mm...', 'bccd..', 'bcddde', 'bccd.e', '.oo...'],
            2: ['mm....', 'bccd..', 'bcddde', 'bcccd.', '.oo...']}[tilt]
    put_bitmap(fr, bm(rows, KETTLE_LG, (1, 1)), spec.names, x + 0.5, y, name='kettle')
    if P.get('stream'):
        sx, sy = x + 5, y + 3
        for k in range(2 + P['stream']):
            fr.px(sx, sy + k, M(spec, 'tea'), 4 if k == 0 else 3)


# =========================================================================================== WORKER B
def worker_b():
    scene = 'karsk'
    mats, names = materials(scene, {
        'coat': '#3E4652',                               # blue-grey telogreika
        'trouser': '#2E3238',
        'boot': ('#4C4A46', {'texture': 'felt'}),
        'galosh': '#18181C',
        'patch': '#6A685E',
        'hat': ('#57544F', {'texture': 'fur'}),
        'band': '#26262A',
        'skin': SKIN['ruddy'],
        'hair': '#4A3A30',
        'eye': EYE_K,
        'glass': GLASS,
        'mitten': '#5E5848',
        'belt': '#2A2620',
        'metal': '#8C8E80',
        'button': '#1C1E22',
        'breath': ['#6E7C7A', '#8E9C98', '#AEBAB4', '#C4CEC8', '#DCE2DC', '#EEF2EE'],
    })
    lg = HD.base_legend()
    spec = Spec(id='worker_b', scene=scene, mats=mats, names=names, light=side_light(), rim=RIM[scene],
                hip_h=21.5, torso=13.4, neck=1.4,
                coat=Coat(mat='coat', hem=-4.5, back=4.9, front=4.8, flare=0.5, chest=0.8, collar=1.5,
                          width_f=6.3, waist_f=5.0, hem_f=5.2, R=2.6, cyl=0.6, hunch=0.5),
                heads=HD.worker_b(lg), boots=boot_bitmaps('boot', sole='galosh', style='valenki'),
                hands=make_hands('mitten', 'mitten'), lean=3.5, arm_r=(1.95, 1.65), leg_r=(1.95, 1.75),
                style=dict(stride=4.6, swing=18.0, bob=1, walk_lean=3.0, lift=2.6, idle_feet=(1.5, -1.5),
                           arm_n_idle=(8.0, 20.0), arm_f_idle=(-4.0, 14.0), gesture='blow_hands', work='warm'))
    spec.hooks = {'side': [('coat', workerb_coat_side), ('front', _puff)],
                  'front': [('coat', workerb_coat_front)]}
    return spec


def workerb_coat_side(fr, J, P, spec):
    T = J['T']
    c = spec.coat
    quilt_lines(fr, spec, J, 'coat', step=3, start=2, vmin=-5, vmax=T - 1)
    column_line(fr, spec, J, c.front - 1.0, c.hem + 1, T - 2, 'coat', -0.6)
    belt_side(fr, spec, J, 1.8, 'belt', buckle='metal')
    x, y = J['ank_f']
    fr.recolor(x, y - 2, M(spec, 'patch'), 3)       # darned felt boot


def workerb_coat_front(fr, J, P, spec):
    T = J['T']
    quilt_lines(fr, spec, J, 'coat', step=3, start=2, vmin=-5, vmax=T - 1, light=spec.light_front.key)
    column_line(fr, spec, J, 0.0, spec.coat.hem + 1, T - 1, 'coat', -1.0)
    buttons(fr, spec, J, 0.9, (T - 3.0, T - 6.0, 4.5))
    belt_front(fr, spec, J, 1.8, 'belt', buckle='metal')


CAST_NEW = {'librarian': librarian, 'porter': porter, 'vendor': vendor, 'worker_b': worker_b}
