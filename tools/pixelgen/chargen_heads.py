"""chargen_heads -- hand-drawn pixel heads (side / front / back) for every character of the cast.

Each head is an ASCII map read by chargen_core.Bitmap.  Every pixel carries an explicit ramp tone, so the
heads are exactly as drawn (own outline, own rim light, own anti-aliasing); the renderer only adds the
dome normals for the scene lights.  Light convention (character-relative, survives mirroring):
  side  (facing right): key from the front-top (screen right), cool rim on the back-top edge (screen left)
  front: key from the upper left of the picture, rim on the top edge
  back : key from the upper right of the picture

Common legend (see `base_legend`):
  skin   q r s S L H  -> tones 0..5            e eye (dark)  w eye white  m mouth  M open mouth
  hair   k l h K j J  -> tones 0..5            b brow (hair tone 1)       n nose / crease shadow (fixed)
  hat    0 1 2 3 4 5  -> tones of the head-gear material, R = rim-lit pixel of it
  band   u v V x X Y  -> tones 0..5 of a second material (hat band, visor, scarf knot, cap badge ...)
  glass  g G E        -> spectacle frame dark / frame light / lens glint
Anchor = the neck pixel (last row) that is placed on the rig's neck joint.
Variants: side {base, blink, talk, look (= looking back over the shoulder)}, front {base, blink, talk},
back {base}.
"""
from __future__ import annotations

from chargen_core import Bitmap


def base_legend(skin='skin', eye='eye', hair='hair', hat='hat', band='band', glass='glass'):
    lg = {'q': (skin, 0), 'r': (skin, 1), 's': (skin, 2), 'S': (skin, 3), 'L': (skin, 4), 'H': (skin, 5),
          'e': (eye, 1, 'f'), 'w': (eye, 4, 'f'), 'm': (skin, 1, 'f'), 'M': (eye, 2, 'f'), 'n': (skin, 2, 'f'),
          'k': (hair, 0), 'l': (hair, 1), 'h': (hair, 2), 'K': (hair, 3), 'j': (hair, 4), 'J': (hair, 5),
          'b': (hair, 1, 'f'), 'B': (skin, 1, 'f')}
    if hat:
        for i in range(6):
            lg[str(i)] = (hat, i)
        lg['R'] = (hat, 'rim')
    if band:
        for ch, t in zip('uvVxXY', range(6)):
            lg[ch] = (band, t)
        lg['y'] = (band, 1)
    if glass:
        lg.update({'g': (glass, 1, 'f'), 'G': (glass, 3, 'f'), 'E': (glass, 5, 'f')})
    return lg


def _bm(rows, lg, anchor, dome=(1.0, 1.1)):
    return Bitmap(rows, lg, anchor=anchor, dome=dome)


def _find(rows, ch):
    for y, r in enumerate(rows):
        x = r.replace(' ', '').find(ch)
        if x >= 0:
            return x, y
    raise ValueError(ch)


def head_views(lg, side, front=None, back=None, side_blink=None, side_talk=None, front_blink=None,
               front_talk=None, anchor_char='@', look=True):
    """Build the view dict.  Rows contain one '@' = the neck anchor pixel (rendered as skin shadow 's').
    *_blink / *_talk: {char: char} or {(x, y): char} substitutions; defaults: e->S (blink), m->M (talk)."""
    out = {}

    def mk(rows):
        rows = [r.replace(' ', '') for r in rows]
        ax, ay = _find(rows, anchor_char)
        rows = [r.replace(anchor_char, 's') for r in rows]
        return _bm(rows, lg, (ax, ay))

    if side:
        b = mk(side)
        d = {'base': b,
             'blink': b.variant(side_blink if side_blink is not None else {'e': 'S'}),
             'talk': b.variant(side_talk if side_talk is not None else {'m': 'M'})}
        if look:
            d['look'] = b.flipped()
        out['side'] = d
    if front:
        b = mk(front)
        out['front'] = {'base': b,
                        'blink': b.variant(front_blink if front_blink is not None else {'e': 'S'}),
                        'talk': b.variant(front_talk if front_talk is not None else {'m': 'M'})}
    if back:
        out['back'] = {'base': mk(back)}
    return out


# =========================================================================================== ALEXEI
# ushanka (dark grey-brown fur, ear-flaps hanging loose, front flap folded up), lean face, straight nose
ALEXEI_SIDE = [
    '. . . . 1 2 3 3 3 . . .',
    '. . . 1 2 3 3 3 4 4 . .',
    '. . 1 2 3 2 3 4 3 4 4 .',
    '. 1 2 2 3 3 4 4 4 5 5 4',
    '2 1 2 3 2 3 3 3 4 4 4 3',
    '2 1 2 3 3 2 1 r s b L .',
    '1 1 2 3 2 3 1 k S e L .',
    '. 1 2 3 3 2 1 s S S L H',
    '. 1 2 2 3 2 1 r S S m .',
    '. . 1 2 2 1 . r s S . .',
    '. . . 0 . . . s @ . . .',
]
ALEXEI_FRONT = [
    '. . . . 2 3 3 3 2 . . .',
    '. . . 2 3 4 4 4 3 2 . .',
    '. . 2 3 4 5 5 4 4 3 2 .',
    '. 1 3 4 4 4 4 4 4 3 2 1',
    '1 2 3 3 3 3 3 3 3 2 2 1',
    '1 3 2 L b S S b s 1 2 1',
    '1 3 2 L e S S e s 1 2 1',
    '1 3 2 L S S n s s 1 2 1',
    '. 1 2 s S m m S r 1 1 .',
    '. 1 2 . r S S r . 1 1 .',
    '. . 0 . . s @ . . . 0 .',
]
ALEXEI_BACK = [
    '. . . . 2 3 3 3 2 . . .',
    '. . . 2 3 3 3 4 4 3 . .',
    '. . 2 3 3 3 4 4 4 4 3 .',
    '. 1 2 2 3 3 3 4 4 4 3 2',
    '1 2 2 2 3 3 3 3 3 3 2 1',
    '1 2 2 2 2 2 3 3 3 3 2 1',
    '1 2 2 2 2 2 2 3 3 2 2 1',
    '1 2 2 1 2 2 2 2 2 2 2 1',
    '. 1 2 1 1 2 2 2 1 2 1 .',
    '. 1 1 . k h h k . 1 1 .',
    '. . 0 . . s @ . . . 0 .',
]

# =========================================================================================== KONRAD
# fedora with pinched crown, black band, snap brim; light-brown short hair; straight, narrow face
KONRAD_SIDE = [
    '. . . . . 2 3 4 4 . . .',
    '. . . . R 2 3 4 4 4 . .',
    '. . . . 2 3 3 4 4 5 . .',
    '. . . . u u v V V x . .',
    '. 1 2 2 3 3 3 4 4 4 5 5',
    '. . . k r r s s S L . .',
    '. . . k h S S e S L . .',
    '. . . . h s S S L L H .',
    '. . . . r s S S m S . .',
    '. . . . . r s S S . . .',
    '. . . . . s @ s . . . .',
]
KONRAD_FRONT = [
    '....2343....',
    '...234432...',
    '...244332...',
    '...uvVvuu...',
    '.1234444321.',
    '..lrrssrrl..',
    '..hLeSSes...',
    '...LSSnss...',
    '...sSmmSr...',
    '....rSSr....',
    '.....s@.....',
]
KONRAD_BACK = [
    '....2332....',
    '...233332...',
    '...233332...',
    '...uuuuuu...',
    '.1233333321.',
    '...lhhhhl...',
    '...lhKKhl...',
    '...lhhhhl...',
    '....rsss....',
    '.....s@.....',
]

# =========================================================================================== IRINA
# rust headscarf tied under the chin, dark hair fringe, strong brows, 40s
IRINA_SIDE = [
    '. . . . 1 2 3 3 . . .',
    '. . . 1 2 3 3 4 4 . .',
    '. . 1 2 2 3 4 4 4 4 .',
    '. 1 2 2 3 3 3 4 4 3 .',
    '1 2 2 2 2 3 3 2 B L .',
    '1 2 2 2 2 2 3 S e L .',
    '1 1 2 2 2 2 2 s S L H',
    '. 1 1 2 2 2 2 r S m .',
    '. 0 1 1 2 1 x V S . .',
    '. . 0 1 1 u V x s . .',
    '. . . . . . . s @ . .',
]
IRINA_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 4 4 3 2 . .',
    '. 1 2 3 4 4 4 3 3 2 .',
    '1 2 3 h h h K h 2 2 1',
    '1 2 2 L B S B s 2 1 1',
    '1 2 2 L e S e s 2 1 1',
    '1 2 2 L S n s s 2 1 1',
    '. 1 2 s S m S r 1 1 .',
    '. 1 1 . r x r . 1 0 .',
    '. . 0 . u V x . 0 . .',
    '. . . . s @ s . . . .',
]

# =========================================================================================== EMIL
# bald crown, grey fringe, round spectacles, grey moustache, 60s (stooped body)
EMIL_SIDE = [
    '....rsSLL..',
    '...rsSSLLH.',
    '..KjsSSSLL.',
    '.KjjsSSSLL.',
    '.jjjrSgGEgL',
    '.jjjsSSSLLH',
    '..jjsSjJjS.',
    '...kjrsSm..',
    '.....rsS...',
    '......s@...',
]
EMIL_FRONT = [
    '...rsSLs...',
    '..rsSSLLs..',
    '.jsSSSLSsj.',
    '.jSbSSSbsj.',
    'jgEgSSgEgj.',
    '.jLSSSnssj.',
    '.jsjJjjJsk.',
    '..rsSmSsr..',
    '...rsSsr...',
    '.....s@....',
]

# =========================================================================================== WORKER A
# ushanka with the flaps tied up on top (dark brown fur), stubble, broad face
WORKER_A_SIDE = [
    '. . 1 2 3 3 3 3 . . .',
    '. 1 2 3 3 4 4 4 3 . .',
    '. 1 2 3 3 3 4 4 4 5 .',
    '1 1 2 2 2 3 3 3 4 4 3',
    '1 1 1 2 2 1 1 r s S L',
    '. k h 1 r s S B S L .',
    '. k h h s S S e S L .',
    '. . k h s S S S L L H',
    '. . k h r r S S m S .',
    '. . . . h r r s S . .',
    '. . . . . r r @ s . .',
]
WORKER_A_FRONT = [
    '..2333332..',
    '.233444332.',
    '12344444321',
    '12223333221',
    '.1rrsssrr1.',
    '.hLbSSSbsh.',
    '.hLeSSSesh.',
    '..LSSnsss..',
    '..rsSmmSr..',
    '...rrSSr...',
    '.....s@....',
]

# =========================================================================================== WORKER B
# ushanka flaps down & tied under the chin (dark grey fur), moustache, weathered
WORKER_B_SIDE = [
    '. . . . 1 2 3 3 3 . . .',
    '. . . 1 2 3 3 3 4 4 . .',
    '. . 1 2 3 2 3 4 3 4 4 .',
    '. 1 2 2 3 3 4 4 4 5 5 4',
    '1 1 2 3 2 3 3 3 4 4 4 3',
    '1 1 2 3 3 2 1 r s b L .',
    '1 1 2 3 2 3 1 k S e L .',
    '. 1 2 3 3 2 1 s S S L H',
    '. 1 2 2 3 2 1 r K K j .',
    '. . 1 2 2 1 v V s S . .',
    '. . . 1 . u V . s @ . .',
]
WORKER_B_FRONT = [
    '...23332...',
    '..2344432..',
    '.234455432.',
    '12344444321',
    '121rrssrr21',
    '121bSSSbs21',
    '121eSSSes21',
    '121LSSnss21',
    '.11KjjjKk1.',
    '.01.rSSr.10',
    '..1..s@s.1.',
]

# =========================================================================================== BABUSHKA
# dotted dark headscarf, tied under the chin, deep-set eyes, old
BABUSHKA_SIDE = [
    '. . . . 1 2 3 3 . .',
    '. . . 1 2 3 3 X 4 .',
    '. . 1 2 3 3 4 4 4 .',
    '. 1 2 2 X 3 3 4 3 .',
    '1 2 2 2 2 3 2 r B L',
    '1 2 2 2 2 2 2 S e L',
    '1 1 2 X 2 2 2 s S H',
    '. 1 1 2 2 2 2 r m S',
    '. 0 1 1 1 1 x V s .',
    '. . 0 0 u V x @ . .',
]
BABUSHKA_FRONT = [
    '. . . 1 2 3 2 . . .',
    '. . 1 2 3 4 X 2 . .',
    '. 1 2 3 4 4 3 3 2 .',
    '1 2 X 3 3 3 3 2 2 1',
    '1 2 2 r B S B r 1 1',
    '1 2 2 L e S e s 1 1',
    '1 2 2 L S n s s X 1',
    '. 1 2 s r m r r 1 1',
    '. 1 1 . r x r . 1 .',
    '. . 0 . u V x . . .',
    '. . . . s @ . . . .',
]

# =========================================================================================== CHILD A
# red knit hat with pompom, round face, red scarf
CHILD_A_SIDE = [
    '. . . . 4 5 . . .',
    '. . 1 2 3 3 3 . .',
    '. 1 2 3 3 4 4 4 .',
    '. 2 3 2 3 3 4 4 3',
    '. 1 2 2 2 2 3 3 2',
    '. k h h S S B L .',
    '. k h h S S e L .',
    '. . h h s S S L H',
    '. . . h r S m S .',
    '. . . . . s @ . .',
]
CHILD_A_FRONT = [
    '. . . 4 5 . . .',
    '. 1 2 3 3 3 2 .',
    '1 2 3 4 4 3 3 2',
    '2 3 3 3 3 3 2 1',
    '. h L B S B s h',
    '. h L e S e s h',
    '. . L S n s s .',
    '. . s S m S r .',
    '. . . r S r . .',
    '. . . s @ . . .',
]

# =========================================================================================== BERLIN FATHER
# flat cap (grey tweed), short dark hair, moustache-less, tired
FATHER_SIDE = [
    '...2333....',
    '..R233444..',
    '.12333444 55',
    '.1122223333.',
    '..kh1rrsSSL.',
    '..khhSSSeSL',
    '..khhsSSSLLH',
    '...khrsSSmS',
    '....hrsSSL.',
    '.....rs@s..',
]
FATHER_FRONT = [
    '...23332...',
    '..2344432..',
    '.234444432.',
    '12233333221',
    '..hrrsrrh..',
    '..hLbSbsh..',
    '..hLeSesh..',
    '...LSnss...',
    '...sSmSr...',
    '....rSr....',
    '.....s@....',
]

# =========================================================================================== BERLIN MOTHER
# small dark felt hat, auburn hair in a low bun, lips
MOTHER_SIDE = [
    '. . . . 2 3 3 . . .',
    '. . . R 2 3 3 4 4 .',
    '. . 1 2 2 3 3 4 4 5',
    '. . . k h 1 r s S L',
    '. . k K h h S B e L',
    '. l K j h h s S L H',
    '. l h K h h r S m S',
    '. . l h h r r s S .',
    '. . . . . . s @ . .',
]
MOTHER_FRONT = [
    '. . . 2 3 3 2 . . .',
    '. . 2 3 4 4 3 2 . .',
    '. 1 2 2 3 3 2 2 1 .',
    '. h K h h h h K h .',
    '. h L B S S B s h .',
    '. h L e S S e s h .',
    '. h L S S n s s h .',
    '. h h s S m S r h .',
    '. . . . r S r . . .',
    '. . . . s @ s . . .',
]

# =========================================================================================== BERLIN CHILD
# navy beret, light brown hair, round face
BCHILD_SIDE = [
    '..2334..',
    '.R233445',
    '.122223.',
    '.hhsSSL.',
    '.hhSSeL.',
    '.hhSSSLH',
    '..hsSmS.',
    '...rs@..',
]
BCHILD_FRONT = [
    '. . 2 3 4 3 . .',
    '. 2 3 4 4 3 2 .',
    '1 2 2 2 2 2 2 1',
    '. h L S S s h .',
    '. h L e S e s .',
    '. . L S n s s .',
    '. . s S m S r .',
    '. . . r s @ . .',
]

# =========================================================================================== CLERK
# slicked-back dark hair with a side parting, clean-shaven, narrow face
CLERK_SIDE = [
    '...lhKKj...',
    '..lhhKKKj..',
    '.lhhhhKKjj.',
    '.lhhhhhsSL.',
    '.lhrhhSSeL.',
    '.lhrhsSSLLH',
    '..lhhrSSmS.',
    '...lhrsSL..',
    '.....s@s...',
]
CLERK_FRONT = [
    '...lKjj...',
    '..lhKKjJ..',
    '.lhhhKKjh.',
    '.lhLSSSsh.',
    '.lLbSSbsh.',
    '.rLeSSesr.',
    '..LSSnss..',
    '..sSmmSr..',
    '...rSSr...',
    '....s@....',
]

# =========================================================================================== GUARD
# grey peaked cap, black visor, plain badge (no insignia), stern
GUARD_SIDE = [
    '. . . 1 2 3 4 4 . . .',
    '. . 1 2 3 3 4 4 5 . .',
    '. . 1 2 3 3 4 4 4 . .',
    '. . 1 2 2 3 3 3 X . .',
    '. . 0 y y y V V x x .',
    '. . . k r r s B S L .',
    '. . . k h S S e S L .',
    '. . . k h s S S L L H',
    '. . . . h r S S m S .',
    '. . . . . r s S L . .',
    '. . . . . . s @ . . .',
]
GUARD_FRONT = [
    '. . 1 2 3 3 4 4 1 . .',
    '. 1 2 3 3 4 4 4 3 1 .',
    '. 1 2 3 3 X 4 3 3 1 .',
    '. 1 2 2 3 3 3 3 2 1 .',
    '. . y y V V V y y . .',
    '. . h r b S b r h . .',
    '. . h L e S e s h . .',
    '. . . L S n s s . . .',
    '. . . s S m m r . . .',
    '. . . . r S r . . . .',
    '. . . . . s @ . . . .',
]

# =========================================================================================== LIBRARIAN
# grey hair in a bun, glasses on a chain, ~55
LIBRARIAN_SIDE = [
    '. . . . j J J . . .',
    '. . K j j J J j . .',
    '. K j h j j J j L .',
    'K j K h h j s S L .',
    'K j j h h h B S L .',
    '. K h h h g G E G .',
    '. . h h h s S S L H',
    '. . . h g r S m S .',
    '. . . . g . r S . .',
    '. . . . . . s @ . .',
]
LIBRARIAN_FRONT = [
    '. . . . j J . . . .',
    '. . . j J J j . . .',
    '. . K j j J j K . .',
    '. K h j S S j h K .',
    '. h L B S S B s h .',
    '. g E G S S E G g .',
    '. h L S S n s s h .',
    '. g . s S m S r . g',
    '. . . . r S r . . .',
    '. . . . . s @ . . .',
]

# =========================================================================================== PORTER
# soft uniform cap with a braid band, white moustache, older
PORTER_SIDE = [
    '...12344...',
    '..R233444..',
    '..12333444.',
    '..1XXXXXX4.',
    '..00yyyVVx.',
    '...kj1rSSL.',
    '...kjSSeSL.',
    '...kjsSSLLH',
    '....jrJJJS.',
    '.....rsSS..',
    '......s@...',
]
PORTER_FRONT = [
    '..1233441..',
    '.123444431.',
    '.123444431.',
    '.1XXXXXXX1.',
    '..yyVVVyy..',
    '..jrsssrj..',
    '..jLeSesj..',
    '...LSSnss..',
    '...JJjJJk..',
    '....rSSr...',
    '.....s@....',
]

# =========================================================================================== VENDOR
# flowered headscarf over a knitted hat? -> warm brown headscarf, round cheeks, 50s
VENDOR_SIDE = [
    '. . . . 1 2 3 3 . . .',
    '. . . 1 2 3 3 4 4 . .',
    '. . 1 2 3 3 4 X 4 4 .',
    '. 1 2 2 3 3 3 4 4 3 .',
    '1 2 X 2 2 3 3 2 B L .',
    '1 2 2 2 2 2 3 S e L .',
    '1 1 2 2 2 X 2 H S L H',
    '. 1 1 2 2 2 2 r S m .',
    '. 0 1 X 2 1 x V S . .',
    '. . 0 1 1 u V x s . .',
    '. . . . . . . s @ . .',
]
VENDOR_FRONT = [
    '. . . 1 2 3 3 2 . . .',
    '. . 1 2 3 4 X 3 2 . .',
    '. 1 2 3 4 4 4 3 3 2 .',
    '1 2 X h h h K h 2 2 1',
    '1 2 2 L B S B s 2 1 1',
    '1 2 2 L e S e s 2 X 1',
    '1 2 2 H S n s H 2 1 1',
    '. 1 2 s S m S r 1 1 .',
    '. 1 1 . r x r . 1 0 .',
    '. . 0 . u V x . 0 . .',
    '. . . . s @ s . . . .',
]


# ------------------------------------------------------------------------------------- registry
def alexei(lg):
    return head_views(lg, ALEXEI_SIDE, ALEXEI_FRONT, ALEXEI_BACK)


def konrad(lg):
    return head_views(lg, KONRAD_SIDE, KONRAD_FRONT, KONRAD_BACK)


def irina(lg):
    return head_views(lg, IRINA_SIDE, IRINA_FRONT)


def emil(lg):
    return head_views(lg, EMIL_SIDE, EMIL_FRONT, side_blink={'E': 'G'}, front_blink={'E': 'G'})


def worker_a(lg):
    return head_views(lg, WORKER_A_SIDE, WORKER_A_FRONT)


def worker_b(lg):
    return head_views(lg, WORKER_B_SIDE, WORKER_B_FRONT, side_talk={(8, 8): 'M'}, front_talk={(5, 8): 'M'})


def babushka(lg):
    return head_views(lg, BABUSHKA_SIDE, BABUSHKA_FRONT)


def child_a(lg):
    return head_views(lg, CHILD_A_SIDE, CHILD_A_FRONT)


def berlin_father(lg):
    return head_views(lg, FATHER_SIDE, FATHER_FRONT)


def berlin_mother(lg):
    return head_views(lg, MOTHER_SIDE, MOTHER_FRONT)


def berlin_child(lg):
    return head_views(lg, BCHILD_SIDE, BCHILD_FRONT)


def clerk(lg):
    return head_views(lg, CLERK_SIDE, CLERK_FRONT)


def guard(lg):
    return head_views(lg, GUARD_SIDE, GUARD_FRONT)


def librarian(lg):
    return head_views(lg, LIBRARIAN_SIDE, LIBRARIAN_FRONT, side_blink={'E': 'G'}, front_blink={'E': 'G'})


def porter(lg):
    return head_views(lg, PORTER_SIDE, PORTER_FRONT, side_talk={(7, 8): 'M'}, front_talk={(5, 8): 'M'})


def vendor(lg):
    return head_views(lg, VENDOR_SIDE, VENDOR_FRONT)
