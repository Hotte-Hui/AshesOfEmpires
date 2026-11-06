"""env_c4_cine_figs -- hands and figures of the Chapter-4 cinematics (owner: c4 figure stream; round 9, rebuilt in
round 10 after the player's report "die Arme der Charaktere sind komisch").

Everything here is sculpted and lit by the signed-distance pipeline of the dialogue portraits (chargen_portrait2_*:
sphere tracer, material ramps, outlines, rims; imported read-only).  The anatomy comes from env_c4_cine_anat (an
articulated hand with three-phalanx fingers, knuckles, thumb pads and nails, sleeves with an open end, elbow
folds and cuffs, cast shadows on the desk / card / counter); heads, hats and coats are the cast specs of the
portraits (chargen_portrait2_cast, characters_c4: Lev, Marta, Fengler), so the faces are the faces of the dialogue
busts.  No painted silhouettes, no upscaled blocks.

Function (output contract kept from round 9 -- canvas, anchor semantics, frame count):
  c1_lhand()        Konrad's left glove pinching card No. 0417 by its upper-left corner -> (behind, thumb) layers;
                    the card goes between them; anchor = the thumb tip (bottom-right-most pixel of the thumb
                    layer); the coat sleeve runs up out of the frame for the whole lift
  c1_rhand()        Konrad's right glove: the thumb pressed on the card at the perforated right edge (the leftmost
                    pixel = the thumb tip, the anchor), the index finger behind the edge, the sleeve out of the
                    frame at the lower right
  c2_thumb()        macro: the glove's thumb running down the German half's perforation (Berlin dawn) -- drawn
                    where the round-9 shadow sprite went (see MACRO_* below)
  c3_finger()       macro: Alexei's bare index finger along the Russian half's edge (kerosene lamp)
  c3_hand()         Alexei's right hand flat on the siding-office desk, the fingertips on the Russian half's
                    perforated edge; the quilted sleeve (knit cuff of the roll-neck) runs out of the frame bottom
  c4_back(f)        Alexei from behind at the booth window, f 0 bowed over the card, 1 looking up at the wagon;
                    both forearms on the desk
  s1_pencil(f)      Alexei's right hand writing (pencil held between thumb, index and middle finger), 2 frames
  s1_lev            Lev's left hand from across the desk (darned cardigan, black sleeve protector, the index
                    fingertip missing) sliding the card into the box; the arm runs up out of the frame
  stamp_hand(city)  a hand from above round the knob of a rubber stamp (Lev in Karsk / Fengler in Berlin)
  s3_hands_med()    Registrator Fengler leaning over the counter "Auskunft · Abgleich": his face (rimless glasses,
                    side parting), dust coat over suit and tie, sleeve protectors, the right hand on the stamp knob,
                    the left flat on a card -- the whole upper body, clipped at the counter's far edge
  v2_konrad(f)      Konrad from behind at the tram loop, f 0 arm down, 1 rising, 2 raised (he waves to Ilse)

People for the plates (round 10 -- ready for the film / places builders, not yet drawn by a runtime):
  c2_thumb() / c3_finger()   the real digits for the perforation macros (instead of the round-9 shadow sprite):
                    MACRO_SIZE canvas drawn at (EDGE_X - MACRO_OFF[side][0], shadow_y + 60 - MACRO_OFF[side][1]),
                    side 'de' (c2) / 'ru' (c3a), moving down with the shadow's speed
  w2_reflection(city)        Konrad's / Alexei's face mirrored in his compartment window (W2_SIZE = one window hole
                    of LS_C4_Homeward w2, layout homeward.win_k / win_a), dim warm layer over the landscape strips
  s4_konrad_medium(f)        Konrad waist-up at the foot of the shaft ladder (S4M_SIZE; f 0 hand down, 1 hand on
                    the coat over the card) -- a medium shot for s4 before the game-scale ending
  v3_thumb()        Alexei's hand holding the notebook of the v3 insert (V3T_SIZE at V3T_AT over v3_note.png)
  crowds            env_c4_cine_kit.crowd_row(cid, anim, look, seed) = a relit game sheet row in one of eight
                    clothing variants; every lit_row / fig_sheet cell now stands on a contact shadow (feet_shadow)

Renders are memoised on disk (key = pipeline sources + env_c4_cine_anat + the shot function's own source and
constants, see _fsrc); ASHES_NO_CACHE=1 disables the cache.
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
import chargen_portrait2_cast as CC  # noqa: E402
import chargen_portrait2_sdf as S    # noqa: E402
import env_c3p2_cine_hands as H      # noqa: E402  (frame_along, limb, bounded; read-only)
import env_c4_cine_anat as N         # noqa: E402
import env_veltrava_cine_figs as F   # noqa: E402  (render, styles; read-only)
from chargen_portrait2_paint import MatStyle, ramp  # noqa: E402

with open(os.path.abspath(__file__), 'rb') as _fh:
    _SRC = hashlib.sha1(_fh.read()).hexdigest()[:12]

E = S.Ellipsoid
RC = S.RoundCone
TH7 = [0.05, 0.12, 0.21, 0.32, 0.46, 0.62, 0.82]
SKIN_TH = [0.05, 0.11, 0.19, 0.30, 0.43, 0.60, 0.84]
_norm = N.nrm


# ----------------------------------------------------------------------------------------- materials
def _styles(city):
    """Material styles; `city` 'karsk' = kerosene amber light, 'berlin' = dawn blue / fluorescent green."""
    if city == 'karsk':
        skin_a = ramp('#0a0b10', '#1c1718', '#35231f', '#563428', '#7e4c32', '#a86a40', '#cc8e56', '#ecba7c')
        skin_l = ramp('#0b0b0f', '#1d1819', '#352826', '#52392f', '#76503c', '#9a6c4c', '#bc8c62', '#d8ae80')
        nail = ramp('#1c1414', '#3e2c28', '#6a4e42', '#96725e', '#bc967a', '#dcbc9a')
        # the quilted jacket under the kerosene lamp: dark olive, warming a little in the light -- one hue, no
        # khaki jump (round 10: the yellow top tones read as camouflage)
        quilt = ramp('#050806', '#0b110d', '#121b14', '#19251b', '#223022', '#2d3b29', '#3a4630', '#4a5338')
        knit = ramp('#0b0b0c', '#18171a', '#262426', '#383432', '#504840', '#6c5e4c', '#8a7658', '#a68e68')
        card = ramp('#0b0806', '#17110c', '#251b13', '#35271b', '#4a3624', '#634a32', '#7e6042', '#9a7852')
        prot = ramp('#050506', '#0b0b0d', '#131315', '#1c1b1d', '#2a2726', '#3e3632', '#584a40')
        wood = ramp('#120a06', '#22140c', '#361f12', '#4e2e1a', '#6a4024', '#8a5630', '#aa6e3e', '#c88a52')
        pencil = ramp('#1a1206', '#3a2a0e', '#6a4a14', '#9a6c1e', '#c8962c', '#e8bc4e')
        rim = '#6e4a2c'              # the lamp's warm bounce (no cold blue-grey edge dots in a lamp-lit room)
    elif city == 'signal':
        # the night yard under the repaired signal: green key, cold snow light
        skin_a = ramp('#060b0a', '#101814', '#1e2a22', '#33402f', '#4e5a40', '#6e7a52', '#94a06a', '#bcc890')
        skin_l = skin_a
        nail = ramp('#101410', '#26302a', '#46544a', '#6a7a6c', '#92a294', '#b8c8ba')
        quilt = ramp('#030705', '#07100b', '#0d1a12', '#14261a', '#1c3624', '#284a30', '#386440', '#4e8254')
        knit = ramp('#070a09', '#111614', '#1b221e', '#28322c', '#38463c', '#4c5e50', '#647a68', '#7e9682')
        card = knit
        prot = ramp('#040605', '#090c0a', '#0f1410', '#171e18', '#212b23', '#2f3c31', '#425244')
        wood = knit
        pencil = ramp('#10120a', '#262a16', '#424a24', '#646e34', '#8a9646', '#b0bc5a')
        rim = '#8aa4b4'
    else:
        skin_a = ramp('#0b0d16', '#1d1b28', '#372a37', '#5b3b43', '#86584f', '#b27b63', '#d4a17f', '#ecc9a1')
        # Fengler's hands under the tubes: the registrar bust's skin, a little cooler (round 10a: grey -- it
        # read as a rubber glove)
        skin_l = ramp('#0b1012', '#1c1d24', '#36302f', '#56443f', '#7c6152', '#a58068', '#c8a083', '#e2c2a0')
        nail = ramp('#14161c', '#2e2e34', '#55504e', '#7e766e', '#a89c90', '#cec2b4')
        quilt = ramp('#04060b', '#090e1a', '#0f1628', '#162036', '#1f2c48', '#2e3e5e', '#425478', '#5a6c90')
        knit = ramp('#0a0c0e', '#15191c', '#20262a', '#2d353a', '#3e484c', '#56605f', '#717a76', '#8e968e')
        card = ramp('#0a0c0c', '#141818', '#1e2422', '#2a302c', '#3a4038', '#4e5446', '#666a58', '#80826c')
        prot = ramp('#050607', '#0a0c0e', '#111417', '#191d21', '#23292c', '#33393a', '#4a504c')
        wood = ramp('#0e0e0c', '#1c1c18', '#2c2a24', '#403c32', '#585244', '#726a58', '#8e866e', '#aaa288')
        pencil = ramp('#14100a', '#2a2214', '#4a3c1e', '#6e5a2c', '#94783c', '#b49650')
        rim = '#7f9aa8'
    glove = ramp('#030304', '#08080a', '#0e0d10', '#151316', '#1d1a1d', '#272326', '#352e30', '#4a4042', '#625456')
    navy = ramp('#04060b', '#090e1a', '#0f1628', '#172038', '#202c48', '#2c3a5a', '#3c4c6e', '#526284')
    dust = ramp('#0c0e0e', '#171a1a', '#232727', '#303535', '#3f4544', '#525857', '#6a706c', '#888c86')
    shirt = ramp('#0e0f14', '#272a33', '#4a4c56', '#77777b', '#a19d98', '#d2c6b2')
    metal = ramp('#08090b', '#14161a', '#22262b', '#363b41', '#50565c', '#727980', '#9aa2a8', '#c8ced2')
    inner = ramp('#020203', '#050506', '#09090b', '#0e0e10')
    darn = ramp('#0e0b09', '#1c1714', '#2c241e', '#3e332a', '#544638', '#6c5a48', '#86705a')
    return {
        'darn': MatStyle(darn, TH7[:6], dither=0.0, rim=rim),
        # skin: band borders dithered (no flat "sticker" ovals on the back of a hand), cast shadows keep a
        # third of the key (a thumb under the palm stays skin, never a black sausage)
        'skin': MatStyle(skin_a, SKIN_TH, dither=0.05, rim=rim, wrap=0.18, lift=0.35),
        'skin_l': MatStyle(skin_l, SKIN_TH, dither=0.05, rim=rim, wrap=0.18, lift=0.35),
        'nail': MatStyle(nail, [0.05, 0.12, 0.24, 0.40, 0.60], rim=rim, spec=0.5, spec_pow=14.0),
        'glove': MatStyle(glove, [0.04, 0.09, 0.16, 0.25, 0.36, 0.50, 0.66, 0.84], dither=0.02, rim=rim, spec=0.55,
                          spec_pow=11.0),
        'quilt': MatStyle(quilt, TH7, dither=0.015, rim=rim),
        'coat': MatStyle(navy, TH7, dither=0.03, rim=rim),
        'knit': MatStyle(knit, TH7, dither=0.04, rim=rim),
        'cardigan': MatStyle(card, TH7, dither=0.04, rim=rim),
        'prot': MatStyle(prot, TH7[:6], dither=0.02, rim=rim, spec=0.25),
        'dust': MatStyle(dust, TH7, dither=0.03, rim=rim),
        'shirt': MatStyle(shirt, TH7[:5], dither=0.03, rim=rim),
        'wood': MatStyle(wood, TH7, dither=0.03, rim=rim, spec=0.25),
        'pencil': MatStyle(pencil, TH7[:5], rim=rim),
        'lead': MatStyle(ramp('#0c0c0e', '#1e1e22', '#34343a', '#50505a'), [0.1, 0.3, 0.6], rim=rim, spec=0.6),
        'metal': MatStyle(metal, TH7, rim=rim, spec=0.6, spec_pow=16.0),
        'inside': MatStyle(inner, [0.15, 0.35, 0.6], rim=None),
    }


GROUPS = {'skin': 0, 'skin_l': 0, 'nail': 0, 'glove': 1, 'quilt': 2, 'coat': 3, 'knit': 4, 'cardigan': 4, 'prot': 5,
          'dust': 6, 'shirt': 7, 'wood': 8, 'pencil': 9, 'lead': 9, 'metal': 10, 'inside': 11, 'darn': 4}


def _look(key, rim, ambient=0.06, fill=0.07, fill_dir=(0.0, -0.6, 0.8), bg='karsk'):
    return dict(key=key, rim=rim, ambient=ambient, wrap=0.12, bg=bg, glow=(0.8, 0.2), fill=fill,
                fill_dir=fill_dir, ao=0.55)


def _fsrc(depth=2):
    """Cache key of a render: the calling shot function's source, the shared helpers' sources and every
    upper-case module constant (so editing one shot re-renders only that shot)."""
    import inspect
    fr = sys._getframe(depth)
    try:
        own = inspect.getsource(fr.f_code)
    except (OSError, TypeError):
        own = _SRC
    g = globals()
    hnames = ('_styles', '_look', '_protector', '_fingertip_cut', '_quilt_stitches', '_wrist_for', '_berlin_dawn_look',
              '_darn_weave')
    helpers = ''.join(inspect.getsource(g[n]) for n in hnames if n in g)

    def names(code):
        out = set(code.co_names)
        for c in code.co_consts:
            if hasattr(c, 'co_names'):
                out |= names(c)
        return out
    used = names(fr.f_code)
    for n in hnames:
        if n in g:
            used |= names(g[n].__code__)
    consts = repr(sorted((k, repr(g[k])) for k in used if k in g and k.isupper()))
    return hashlib.sha1((own + helpers + consts).encode('utf-8')).hexdigest()[:12]


def _paint(nodes, M, size, look, city, cache, glow=None, passes=(), **kw):
    return N.paint(nodes, M, size, look, _styles(city), groups=GROUPS, tone_passes=list(passes),
                   cache=(cache, _fsrc()), glow=glow, **kw)


# ----------------------------------------------------------------------------------------- legacy helpers
def hand(M, mat, s, curl=0.25, spread=0.0, thumb=1.0, grip=0.0, curls=None, cut=None, thumb_dir=None,
         parts=('palm', 'fingers', 'thumb')):
    """Round-9 signature, now the articulated hand of env_c4_cine_anat (curl 0..1 -> MCP/PIP/DIP flexion)."""
    cs = curls if curls is not None else (curl,) * 4          # round 9 order: little .. index
    flex = tuple((70.0 * c, 90.0 * c, 50.0 * c) for c in reversed(cs))
    th = dict(abd=40.0 - 20.0 * grip, opp=20.0 + 40.0 * grip, mcp=10.0 + 30.0 * grip, ip=10.0 + 30.0 * grip)
    return N.hand(M, mat, s, side=1.0 if thumb >= 0 else -1.0, flex=flex, spread=spread * 10.0, thumb=th,
                  parts=parts)


def arm(M, sleeve, skin, shoulder, elbow, wrist, r, hand_y, hand_z, s, cuff=None, cuff_len=0.0, **hand_kw):
    """Round-9 signature on the new sleeve (open end, folds) and hand."""
    kw = {}
    if 'curls' in hand_kw or 'curl' in hand_kw:
        cs = hand_kw.get('curls') or (hand_kw.get('curl', 0.25),) * 4
        kw['flex'] = tuple((70.0 * c, 90.0 * c, 50.0 * c) for c in reversed(cs))
    if 'thumb' in hand_kw:
        kw['side'] = 1.0 if hand_kw['thumb'] >= 0 else -1.0
    if 'spread' in hand_kw:
        kw['spread'] = hand_kw['spread'] * 10.0
    return N.arm(M, sleeve, skin, shoulder, elbow, wrist, r, hand_y, hand_z, s, cuff=cuff, cuff_len=cuff_len,
                 hand_kw=kw, sleeve_in='inside')


# ----------------------------------------------------------------------------------------- placement helper
def _wrist_for(tip_local, target, hand_y, hand_z):
    """Wrist position that puts the hand-local point `tip_local` at the view point `target` for this orientation."""
    fr = N.frame_along((0.0, 0.0, 0.0), hand_y, hand_z)
    return np.asarray(target, float) - fr.to_view(tip_local)


# ========================================================================================= LS_C4_Card
# c1: card No. 0417 is held at CARD_AT (230, 104), 176 x 118 (env_c4_cine_card); the left hand's canvas is placed
# by the thumb tip (card corner + (14, 16)), the right hand's by its leftmost pixel (card's right edge - 4).
C1_L_SIZE = (480, 440)       # tall: the sleeve stays above the letterbox while the card rises 110 px
C1_R_SIZE = (540, 420)       # wide and tall enough that the sleeve leaves the frame (right edge / letterbox)
C1_S = 98.0                  # palm length of Konrad's gloves: the glove ~0.52 of the 176 px card (a man's hand
#                              is ~9.5 cm wide, a registry card 14.8 cm; round 9/10a had 0.28 -- doll hands)
C1_L_PINCH = (330.0, 330.0)  # canvas point of the pinch (the card corner region) in the left hand's canvas
C1_L_ROLL = 34.0             # the left glove turned about its finger axis: the back of the glove partly to us
C1_L_FINGERS = (0.80, 0.58, 0.05)  # the left glove comes in from the upper left at 45 degrees (a pinch at a top
C1_L_ELBOW = (-0.92, -0.10, -0.30)  # corner holds the hand above-left of it); wrist -> elbow: out to the left


def _berlin_dawn_look():
    return _look(key=(-0.62, -0.70, 0.36), rim=(0.82, -0.18, -0.54), ambient=0.06, fill=0.08, bg='berlin')


def c1_lhand():
    """Konrad's left hand in the black glove pinches the card by its upper-left corner: the thumb pad on the front
    (towards the camera), the index finger behind the paper, the other fingers curled behind it; the hand seen
    from its thumb side, the back of the glove turned up to the dawn; the coat sleeve runs up and left out of the
    frame.  -> (behind, thumb) layers of the same render (the card goes between)."""
    look = _berlin_dawn_look()
    s = C1_S
    side = -1.0                                        # left hand: the thumb on local -x
    hy = _norm(C1_L_FINGERS)                           # fingers point right and down, into the card corner
    hz_edge = _norm(np.cross((0.0, 0.0, -1.0), hy))    # round 9: the back of the hand up-right, edge-on to us
    hz = _norm(hz_edge * math.cos(math.radians(C1_L_ROLL)) + np.array([0.0, 0.0, 1.0]) *
               math.sin(math.radians(C1_L_ROLL)))
    hz = _norm(hz - hy * float(np.dot(hz, hy)))
    kw = dict(side=side, flex=((30, 40, 16), (56, 80, 42), (64, 86, 46), (70, 88, 48)), spread=2.0,
              thumb=dict(abd=32.0, opp=50.0, mcp=14.0, ip=14.0), glove=True)
    pts = N.hand_points(s, side=side, flex=kw['flex'], spread=2.0, thumb=kw['thumb'])
    pinch = (pts['thumb'] * 0.55 + pts['tips'][0] * 0.45)
    target = (C1_L_PINCH[0], C1_L_PINCH[1], 0.0)      # where the paper is pinched (canvas)
    wrist = _wrist_for(pinch, target, hy, hz)
    elbow = wrist + _norm(C1_L_ELBOW) * 2.6 * s
    shoulder = elbow + np.array([-2.2 * s, -0.5 * s, -0.4 * s])

    def build(thumb_only):
        M = A.Mats()
        if thumb_only:
            node = N.hand_at(M, 'glove', wrist, hy, hz, s, parts=('thumb',), **kw)
            return [node], M
        return [N.arm(M, 'coat', 'glove', shoulder, elbow, wrist, (0.56 * s, 0.50 * s, 0.42 * s), hy, hz, s,
                      cover=0.05, cuff='glove', cuff_len=0.30 * s, sleeve_in='inside', hand_kw=kw)], M
    n, M = build(False)
    full = _paint(n, M, C1_L_SIZE, look, 'berlin', 'c1_lhand', z_range=(300.0, -300.0), steps=160)
    n2, M2 = build(True)
    th = _paint(n2, M2, C1_L_SIZE, look, 'berlin', 'c1_lhand_thumb', z_range=(300.0, -300.0), steps=160)
    thumb, behind = N.split(full, th)
    return behind, thumb


def c1_rhand():
    """Konrad's right hand from the right: the thumb pad pressed on the card at the perforated edge (the leftmost
    pixel of the sprite is the thumb tip), the index finger behind the edge, the other fingers loosely curled,
    the back of the glove to the right; the coat sleeve runs on past the right frame edge / under the letterbox."""
    s = C1_S
    side = 1.0
    hx = _norm((-0.25, 0.05, 0.97))                    # local +x = the thumb side -> towards the viewer (paper)
    hz0 = _norm((0.72, -0.50, 0.36))                   # the back of the glove up and to the right, half to us
    hy = _norm(np.cross(hz0, hx))                      # fingers up-left, behind the card
    hz = _norm(np.cross(hx, hy))
    kw = dict(side=side, flex=((24, 34, 16), (38, 56, 30), (50, 68, 36), (58, 74, 40)), spread=2.0,
              thumb=dict(abd=34.0, opp=18.0, mcp=2.0, ip=-6.0), glove=True)
    pts = N.hand_points(s, side=side, flex=kw['flex'], spread=2.0, thumb=kw['thumb'])
    wrist = _wrist_for(pts['thumb'], (40.0, 80.0, 8.0), hy, hz)
    elbow = wrist + _norm((0.62, 0.70, -0.30)) * 2.6 * s
    shoulder = elbow + np.array([2.0 * s, 0.6 * s, -0.5 * s])

    def build(thumb_only):
        M = A.Mats()
        if thumb_only:
            return [N.hand_at(M, 'glove', wrist, hy, hz, s, parts=('thumb',), **kw)], M
        return [N.arm(M, 'coat', 'glove', shoulder, elbow, wrist, (0.56 * s, 0.50 * s, 0.42 * s), hy, hz, s,
                      cover=0.05, cuff='glove', cuff_len=0.30 * s, sleeve_in='inside', hand_kw=kw)], M
    n, M = build(False)
    full = _paint(n, M, C1_R_SIZE, _berlin_dawn_look(), 'berlin', 'c1_rhand', z_range=(320.0, -320.0), steps=170)
    n2, M2 = build(True)
    th = _paint(n2, M2, C1_R_SIZE, _berlin_dawn_look(), 'berlin', 'c1_rhand_thumb', z_range=(320.0, -320.0),
                steps=170)
    # the fingers behind the card: everything but the thumb left of the edge is hidden by the paper (the runtime
    # draws this sprite over the card with the thumb tip -- its leftmost pixel -- at the edge - 4 px)
    tm = th[..., 3] > 0
    ys, xs = np.nonzero(tm)
    edge = int(xs.min()) + 4 if xs.size else 0
    out = full.copy()
    hide = (~tm) & (np.arange(out.shape[1])[None, :] < edge)
    out[hide, 3] = 0
    return out


# macros (c2 / c3a): the perforation at EDGE_X = 330, holes 24 px apart (macro_k 4); the round-9 runtime drew a
# 120 x 150 shadow sprite at (EDGE_X - 96, y) / (EDGE_X - 24, y) moving down with the same speed on both sides of the
# cut.  The macro digits are sprites of the same placement idea: MACRO_SIZE canvas, its top-left at
# (EDGE_X - MACRO_OFF[side][0], y - MACRO_OFF[side][1]) with y = the round-9 shadow y; the pad of the thumb / the
# fingertip sits on the paper right beside the edge, the digit runs out of the frame (right for the thumb, left for
# the finger).
C2_SIZE = (300, 260)
MACRO_SIZE = (360, 300)
MACRO_OFF = {'de': (40, 30), 'ru': (330, 30)}


def c2_thumb():
    """Macro: Konrad's gloved right thumb pressed on the paper beside the torn edge (dawn from the upper left,
    the sodium lamp of the loop as a rim from the right), the glove's other fingers out of focus behind the edge.
    MACRO_SIZE canvas; the pad's centre at (MACRO_OFF['de'][0] + 26, MACRO_OFF['de'][1] + 92)."""
    s = 150.0
    side = 1.0
    hy = _norm((-0.86, -0.46, 0.20))
    hx = np.array([0.0, 0.0, 1.0])
    hz = np.cross(hx, hy)
    kw = dict(side=side, flex=((20, 30, 12), (40, 60, 30), (50, 70, 36), (60, 76, 40)), spread=3.0,
              thumb=dict(abd=52.0, opp=26.0, mcp=6.0, ip=-6.0), glove=True)
    pts = N.hand_points(s, side=side, flex=kw['flex'], spread=3.0, thumb=kw['thumb'])
    ox, oy = MACRO_OFF['de']
    wrist = _wrist_for(pts['thumb'], (ox + 8.0, oy + 92.0, 40.0), hy, hz)
    elbow = wrist + np.array([420.0, 260.0, -120.0])
    M = A.Mats()
    node = N.arm(M, 'coat', 'glove', elbow + np.array([300.0, 60.0, -60.0]), elbow, wrist, (120.0, 110.0, 96.0),
                 hy, hz, s, cover=0.05, cuff='glove', cuff_len=0.3 * s, sleeve_in='inside', hand_kw=kw)
    look = _look(key=(-0.60, -0.70, 0.38), rim=(0.70, -0.30, -0.62), ambient=0.05, bg='berlin')
    return _paint([node], M, MACRO_SIZE, look, 'berlin', 'c2_thumb', z_range=(400.0, -400.0), steps=170,
                  shadow=dict(p=(0.0, 0.0, -22.0), n=(0.0, 0.0, 1.0), rgb=(26, 30, 44)))


def c3_finger():
    """Macro: Alexei's bare right index finger along the Russian half's torn edge (the kerosene lamp from the
    right): nail, knuckle creases, the other fingers curled out of the frame at the left.  MACRO_SIZE canvas; the
    fingertip on the paper at (MACRO_OFF['ru'][0] + 18, MACRO_OFF['ru'][1] + 92)."""
    s = 150.0
    side = 1.0
    hy = _norm((0.92, -0.30, -0.18))
    hz = _norm((0.10, 0.20, 0.97))
    kw = dict(side=side, flex=((10, 14, 8), (64, 90, 50), (72, 94, 52), (78, 92, 50)), spread=2.0,
              thumb=dict(abd=26.0, opp=56.0, mcp=30.0, ip=26.0), nail='nail')
    pts = N.hand_points(s, side=side, flex=kw['flex'], spread=2.0, thumb=kw['thumb'])
    ox, oy = MACRO_OFF['ru']
    wrist = _wrist_for(pts['tips'][0], (ox + 18.0, oy + 92.0, 14.0), hy, hz)
    elbow = wrist + np.array([-420.0, 200.0, -90.0])
    M = A.Mats()
    node = N.arm(M, 'quilt', 'skin', elbow + np.array([-300.0, 60.0, -60.0]), elbow, wrist, (128.0, 118.0, 100.0),
                 hy, hz, s, cover=0.42, cuff='knit', cuff_len=0.3 * s, sleeve_in='inside', hand_kw=kw)
    look = _look(key=(0.74, -0.58, 0.34), rim=(-0.70, -0.30, -0.62), ambient=0.05, bg='karsk')
    return _paint([node], M, MACRO_SIZE, look, 'karsk', 'c3_finger', z_range=(400.0, -400.0), steps=170,
                  shadow=dict(p=(0.0, 0.0, -10.0), n=(0.0, 0.0, 1.0), rgb=(30, 18, 10)))


# c3b: the Russian half lies at RU_AT (300, 150), 170 x 96; the hand canvas is placed at RU_AT - (172, 50) and slides
# 10 px down along the edge.  The canvas reaches 270 px down so the sleeve leaves the frame at the bottom.
C3_SIZE = (260, 270)


C3_S = 84.0                  # palm length: the hand ~160 px long on the 170 px half card (round 10a: ~95 px)
C3_LAMP_W = (548.0, 92.0)    # the kerosene flame in the frame (layout card.c3_lamp); the canvas sits at (128, 100)
C3_TIPS = (171.0, 70.0)      # index + middle fingertip on the card's perforated left edge (canvas)


def c3_hand():
    """Close: Alexei's right hand resting on the desk, relaxed -- the fingers a little curved and close together,
    pointing up and right, the tips of index and middle finger on the card's perforated left edge, the thumb
    lying loosely along the index side; the knit cuff of the roll-neck at the wrist, the quilted sleeve leaving
    the frame at the bottom.  The kerosene lamp at the upper right rakes across the back of the hand (knuckles,
    tendons, nails catch it), its warm bounce is the only rim, the hand's shadow falls down-left on the boards."""
    M = A.Mats()
    s = C3_S
    hy = _norm((0.66, -0.75, -0.02))
    hz = _norm((-0.06, 0.04, 1.0))
    kw = dict(side=1.0, flex=((12, 20, 10), (14, 22, 11), (17, 26, 12), (22, 30, 14)), spread=2.2,
              thumb=dict(abd=34.0, opp=12.0, mcp=8.0, ip=10.0), nail='nail', relief=False)
    pts = N.hand_points(s, side=1.0, flex=kw['flex'], spread=2.2, thumb=kw['thumb'])
    tips = (pts['tips'][0] + pts['tips'][1]) * 0.5
    wrist = _wrist_for(tips, (C3_TIPS[0], C3_TIPS[1], -6.0), hy, hz)
    fdir = _norm((-0.45, 0.89, 0.08))
    elbow = wrist + fdir * 2.4 * s
    shoulder = elbow + np.array([-0.3 * s, 1.6 * s, 0.4 * s])
    node = N.arm(M, 'quilt', 'skin', shoulder, elbow, wrist, (0.52 * s, 0.47 * s, 0.40 * s), hy, hz, s,
                 cover=0.52, cuff='knit', cuff_len=0.24 * s, sleeve_in='inside', hand_kw=kw,
                 cuff_r=(0.33 * s, 0.31 * s),
                 sleeve_fx=lambda n: N.quilt_on(n, wrist, -fdir, period=0.16 * s, amp=0.022 * s))
    look = _look(key=(0.74, -0.38, 0.56), rim=(-0.60, -0.40, -0.66), ambient=0.10, fill=0.14,
                 fill_dir=(-0.3, 0.2, 0.93), bg='karsk')
    lamp = (C3_LAMP_W[0] - 128.0, C3_LAMP_W[1] - 100.0, 150.0)   # the flame (frame c3_lamp) in this canvas
    return _paint([node], M, C3_SIZE, look, 'karsk', 'c3_hand', z_range=(160.0, -160.0), steps=150,
                  glow=(lamp, 760.0, 0.45),
                  shadow=dict(p=(0.0, 0.0, -11.0), n=(0.0, 0.0, 1.0), rgb=(24, 13, 8)),
                  passes=[_quilt_stitches(M, wrist, fdir, period=0.16 * s)])


def _quilt_stitches(M, wrist, fdir, period=7.0):
    """The quilted sleeve's stitched channels: rings across the forearm (frame along the arm)."""
    fr = N.frame_along(tuple(wrist), tuple(fdir), (0.0, 0.0, 1.0))

    def fn(spec, G, tone, v):
        G['qf'] = fr
        return CC.pass_stitches('quilt', period, frame='qf', axis=1)(spec, G, tone, v)
    return fn


C4_SIZE = (300, 280)
C4_AT = (-20, 70)            # top-left of the over-shoulder figure in the frame (bottom cut by the letterbox)


def c4_back(f):
    """Alexei from behind at the booth window, seen over his right shoulder: f 0 the head bowed to the card on the
    desk, 1 lifted to the window (the wagon outside).  Since round 10b the bust pipeline's figure with real arms
    (env_c4_cine_bust.alexei_back_desk): ushanka flaps that cover the ears, the back flap over the nape, the
    roll-neck pulled up, rounded shoulder caps, quilted upper arms going down to the desk under the frame edge.
    Kerosene lamp at his left (warm key), the cold work lamp beyond the glass as rim."""
    import env_c4_cine_bust as B
    return B.alexei_back_desk(f, C4_SIZE, _fsrc(1))


# ========================================================================================= LS_C4_Stamp
S1_P_SIZE = (200, 180)


def s1_pencil(f):
    """Alexei's right hand writing: the pencil held between thumb, index and middle finger (the ring and little
    fingers curled under, resting on the page), the quilted sleeve from the lower right out of the frame; two
    frames of the stroke.  The pencil point is at (60, 62) in frame 0 (+7 px in frame 1) -- the runtime's anchor."""
    M = A.Mats()
    s = 36.0
    dx = (0.0, 7.0)[f]
    tip = np.array([60.0 + dx, 62.0 + (1.5 if f else 0.0), -6.0])
    pdir = _norm((0.62, -0.70, 0.36))                  # pencil from the point up and back to the right
    pen_len = 92.0
    end = tip + pdir * pen_len
    # the hand holds the pencil a third of the way up: index pad on top, thumb at the side
    hy = _norm((-0.55, -0.62, -0.56))
    hz = _norm((0.30, -0.45, 0.84))
    kw = dict(side=1.0, flex=((26, 40, 26), (44, 60, 36), (66, 86, 48), (74, 90, 50)), spread=2.0,
              thumb=dict(abd=34.0, opp=46.0, mcp=16.0, ip=8.0), nail='nail')
    pts = N.hand_points(s, side=1.0, flex=kw['flex'], spread=2.0, thumb=kw['thumb'])
    grip = tip + pdir * 26.0 + np.array([0.0, 0.0, 6.0])
    wrist = _wrist_for(pts['tips'][0], grip, hy, hz)
    fdir = _norm((0.55, 0.78, -0.25))
    elbow = wrist + fdir * 150.0
    shoulder = elbow + np.array([110.0, 100.0, -40.0])
    node = N.arm(M, 'quilt', 'skin', shoulder, elbow, wrist, (30.0, 28.0, 24.0), hy, hz, s, cover=0.45,
                 cuff='knit', cuff_len=0.22 * s, sleeve_in='inside', hand_kw=kw)
    pen = [RC(tuple(tip + pdir * 7.0), tuple(end), 2.6, 2.8, M('pencil')),
           RC(tuple(tip + pdir * 0.8), tuple(tip + pdir * 7.5), 0.8, 2.5, M('wood')),
           S.Sphere(tuple(tip + pdir * 0.6), 0.9, M('lead'))]
    look = _look(key=(0.62, -0.60, 0.50), rim=(-0.60, -0.45, -0.66), ambient=0.06, bg='karsk')
    return _paint([node] + pen, M, S1_P_SIZE, look, 'karsk', ('s1_pencil', f), z_range=(120.0, -120.0),
                  shadow=dict(p=(0.0, 0.0, -10.0), n=(0.0, 0.0, 1.0), rgb=(60, 46, 30)),
                  passes=[_quilt_stitches(M, wrist, fdir)])


S1_L_SIZE = (300, 330)       # the arm runs up out of the frame from every position of the card
S1_L_S = 40.0                # Lev's palm length (Alexei's pencil hand: 36): a thin, bony old hand
S1_L_TIP = (110.0, 318.0)    # the middle fingertip -- the sprite's lowest pixel, the runtime's anchor (lev_tip)
S1_L_ELBOW = (0.50, -0.72, 0.48)   # wrist -> elbow: up the frame, to the right (his left elbow), up to the camera
S1_L_UPPER = (3.6, -1.4, 3.0)      # elbow -> shoulder (x s): to his shoulder at the right, up to the camera; the
#                                    shoulder lies outside the canvas (the upper arm leaves it under the letterbox)


def s1_lev():
    """Lev's left hand from across the desk (from the top of the frame): bare, thin, the tip of the index finger
    missing (an old injury); the fingertips hook the card's upper edge and pull it into the box.  His forearm
    rises from the wrist to the elbow near the top of the frame (it TAPERS from the elbow to the wrist), the
    upper arm turns away up and out of the frame; the black sleeve protector is gathered by its elastic at both
    ends with soft folds, the darned brown cardigan shows at the elbow (a darn on its point) and as a knitted
    cuff at the wrist.  Its shadow falls down-right on the desk.  The lowest pixel is the anchor (lev_tip)."""
    M = A.Mats()
    s = S1_L_S
    hy = _norm((-0.12, 0.95, -0.28))                 # fingers down the frame onto the card, down to the desk
    hz = _norm((0.0, 0.28, 0.95))                    # the back of the hand up to the camera
    hz = _norm(hz - hy * float(np.dot(hz, hy)))
    kw = dict(side=-1.0, flex=((14, 26, 18), (16, 30, 20), (20, 34, 20), (26, 38, 22)), spread=3.0,
              thumb=dict(abd=30.0, opp=36.0, mcp=14.0, ip=12.0), nail='nail')
    pts = N.hand_points(s, side=-1.0, flex=kw['flex'], spread=3.0, thumb=kw['thumb'])
    wrist = _wrist_for(pts['tips'][1], (S1_L_TIP[0], S1_L_TIP[1], -6.0), hy, hz)
    edir = _norm(S1_L_ELBOW)
    elbow = wrist + edir * 2.4 * s
    shoulder = elbow + np.array(S1_L_UPPER) * s
    fdir = _norm(wrist - elbow)
    node = N.arm(M, 'cardigan', 'skin_l', shoulder, elbow, wrist, (0.52 * s, 0.47 * s, 0.33 * s), hy, hz, s,
                 cover=0.36, cuff='cardigan', cuff_len=0.22 * s, sleeve_in='inside', hand_kw=dict(kw),
                 cuff_r=(0.32 * s, 0.31 * s))
    L = float(np.linalg.norm(wrist - elbow))
    prot = N.cloth_tube(M, 'prot', elbow + fdir * L * 0.17, wrist - fdir * 0.42 * s, 0.52 * s, 0.35 * s,
                        puff=0.09, gather=0.84, folds=6, fold_amp=0.09, seed=5)
    # the darn on the elbow's point: a patch of greyer wool, a little proud of the sleeve
    out_e = _norm(_norm(elbow - shoulder) - fdir)
    darn = E(tuple(elbow + out_e * 0.44 * s * 0.98), (0.20 * s, 0.05 * s, 0.17 * s), M('darn'),
             R=N.ortho(out_e, fdir))
    root = S.Union([node, prot, darn], k=0.0)
    look = _look(key=(-0.55, -0.62, 0.40), rim=(0.55, -0.50, -0.66), ambient=0.06, bg='karsk')
    cut = _fingertip_cut(wrist, hy, hz, s, kw)
    root = S.Sub(root, cut, k=0.6)
    out = _paint([root], M, S1_L_SIZE, look, 'karsk', 's1_lev', z_range=(260.0, -120.0), steps=150,
                 shadow=dict(p=(0.0, 0.0, -9.0), n=(0.0, 0.0, 1.0), rgb=(60, 46, 30)),
                 passes=[_darn_weave()])
    # the runtime anchors the lowest pixel (lev_tip) on the card: no shadow pixel may lie below the fingertip
    solid = out[..., 3] == 255
    low = int(np.nonzero(solid.any(1))[0].max())
    out[low:, :, 3] = np.where(solid[low:], out[low:, :, 3], 0)
    return out


def _darn_weave():
    """The darn's woven look: a 2 px check of alternating tones on the 'darn' material."""
    def fn(spec, G, tone, v):
        M = G['M']
        if 'darn' not in M.names:
            return tone
        m = (G['d'].mat == M.names.index('darn')) & (tone >= 2)
        h, w = tone.shape
        yy, xx = np.mgrid[0:h, 0:w]
        chk = ((xx // 2 + yy // 2) % 2) == 0
        out = tone.copy()
        out[m & chk] -= 1
        return out
    return fn


def _protector(M, elbow, wrist, r0, r1, cover):
    """A black cloth sleeve protector over the forearm: from below the elbow to just above the sleeve end, with
    the gathered elastic at both ends."""
    elbow, wrist = np.asarray(elbow, float), np.asarray(wrist, float)
    d = _norm(wrist - elbow)
    L = float(np.linalg.norm(wrist - elbow))
    a = elbow + d * L * 0.16
    b = wrist - d * cover
    m = M('prot')
    parts = [RC(tuple(a), tuple(b), r0 * 1.04, r1 * 1.06, m),
             E(tuple(a + d * 3.0), (r0 * 1.10, 3.0, r0 * 1.10), m, R=N.ortho(d)),
             E(tuple(b - d * 3.0), (r1 * 1.12, 3.0, r1 * 1.12), m, R=N.ortho(d))]
    return S.Union(parts, k=1.5)


def _fingertip_cut(wrist, hy, hz, s, kw):
    """A small sphere removing the last phalanx of the index finger (Lev's old injury)."""
    fl = kw['flex']
    pts, rr, lat, dd = N.finger_chain(0, s, kw['side'], fl, kw['spread'])
    fr = N.frame_along(wrist, hy, hz)
    c = fr.to_view(pts[3] + dd * 0.06 * s)
    return S.Sphere(tuple(c), FINGER_CUT * s, 0)


FINGER_CUT = 0.19


STAMP_HAND_SIZE = (300, 300)
STAMP_S = 148.0              # palm length: the fist ~2.7 x the 52 px handle (a man's hand on the stamp of s2 / s3a)
STAMP_KNOB = (100.0, 156.0, 46.0)  # the handle's top: layout hand_knob (100, 150) + the runtime's 6 px; height
STAMP_ELBOW = (-0.10, -0.80, 0.59)  # from the wrist back to the elbow: up the frame and up towards the camera
STAMP_BLOCK = (-16, 114, 216, 198)  # the stamp block under the hand in canvas px (stamp_top: 236 x 88 at c - (118, 44))


def stamp_hand(city):
    """A hand from above closed round the handle of a rubber stamp (the stamp itself is painted by stamp_top, its
    handle at (100, 156) of this canvas): the palm cupped over the handle's top, the four fingers round its far
    side, the thumb round the near side, the back of the hand to the camera, the wrist in line with the forearm,
    which rises up out of the frame; its shadow lies on the stamp block.  Lev (Karsk: darned cardigan under the
    black protector, the index fingertip missing, warm lamp) or Fengler (Berlin: grey dust coat, white shirt
    cuff, black protector, flat fluorescent light from above).  The fist is ~2.7 x the handle, the sleeve
    narrower than the fist."""
    M = A.Mats()
    s = STAMP_S
    top = np.array(STAMP_KNOB)
    # the palm cups the ball of the handle, the fingers drape over its far side (their backs seen from above:
    # proximal and middle phalanges, the nails tucked under), the thumb hooks round the near side
    kw = dict(side=1.0, flex=((34, 72, 44), (38, 76, 46), (42, 78, 46), (48, 78, 44)), spread=2.0,
              thumb=dict(abd=30.0, opp=50.0, mcp=24.0, ip=30.0), nail='nail')
    elbow = top + _norm(STAMP_ELBOW) * 3.1 * s
    wrist, hy, hz = N.reach(elbow, top, (0.0, 0.58 * s, -0.22 * s), (0.0, 0.25, 1.0), flexion=-14.0,
                            deviation=6.0, side=1.0)
    fdir = _norm(wrist - elbow)
    shoulder = elbow + np.array([-0.2 * s, -1.2 * s, 0.6 * s])
    sleeve = 'cardigan' if city == 'karsk' else 'dust'
    node = N.arm(M, sleeve, 'skin_l', shoulder, elbow, wrist, (0.50 * s, 0.44 * s, 0.36 * s), hy, hz, s,
                 cover=0.52, cuff='shirt' if city != 'karsk' else 'cardigan', cuff_len=0.34 * s,
                 sleeve_in='inside', hand_kw=dict(kw), cuff_r=(0.315 * s, 0.30 * s))
    L = float(np.linalg.norm(wrist - elbow))
    prot = N.cloth_tube(M, 'prot', elbow + fdir * L * 0.12, wrist - fdir * 0.48 * s, 0.43 * s, 0.39 * s,
                        puff=0.06, gather=0.86, folds=7, fold_amp=0.05, seed=3 if city == 'karsk' else 4)
    root = S.Union([node, prot], k=0.0)
    if city == 'karsk':
        look = _look(key=(0.62, -0.55, 0.56), rim=(-0.60, -0.45, -0.66), ambient=0.07, bg='karsk')
        root = S.Sub(root, _fingertip_cut(wrist, hy, hz, s, kw), k=0.6)
    else:
        look = _look(key=(0.22, -0.84, 0.50), rim=(-0.50, -0.40, -0.75), ambient=0.15, fill=0.16,
                     fill_dir=(0.0, -0.3, 1.0), bg='berlin')
    w, h = STAMP_HAND_SIZE
    bx0, by0, bx1, by1 = STAMP_BLOCK
    yy, xx = np.mgrid[0:h, 0:w]
    clip = (xx >= bx0 + 3) & (xx < bx1 - 3) & (yy >= by0 + 3) & (yy < by1 - 3)
    return _paint([root], M, STAMP_HAND_SIZE, look, city, ('stamp_hand', city), z_range=(420.0, -60.0),
                  steps=150, shadow=dict(p=(0.0, 0.0, 20.0), n=(0.0, 0.0, 1.0), clip=clip,
                                         rgb=(26, 16, 10) if city == 'karsk' else (8, 10, 12)))


# ----------------------------------------------------------------------------------------- s3b: Fengler
S3M_SIZE = (440, 280)        # canvas of Fengler at the counter, placed at S3M_AT (layout stamp.s3b_hands_at)
S3M_AT = (150, 34)           # its top edge lies under the letterbox
S3M_BODY = (332, 126)        # world: the pit of his neck (his whole upper body is in s3b_hands.png)
# Round 9 painted Fengler's chest into the counter plate between these shoulder x positions (env_c4_cine_stamp
# s3b_counter).  Since round 10 his whole upper body -- head, coat, arms -- is this figure, so the round-9 chest
# is parked off the frame (x < 0): a plate that still paints it paints nothing visible.
S3M_SHOULDERS = ((-120, 128), (-120, 128))
S3M_COUNTER_Y = 150          # world y of the counter's far edge: his body disappears behind it (arms reach over)
S3M_KNOB = (254, 204)        # world: the stamp knob under his right hand (s3b_counter paints the stamp there)
S3M_CARD = (326, 230)        # world: his left hand lies flat on the stamped card beside the stamp


def s3_hands_med():
    """Medium: Registrator Fengler behind the counter, leaning over his work -- his face from the dialogue bust
    (characters_c4.registrar_portrait: smooth full face, rimless glasses, side parting with grey temples), head a
    little bowed; light-grey dust coat over the dark suit, white collar and tie, the plain round pin; both forearms
    in black sleeve protectors on the counter: the right hand closed round the stamp knob, the left hand flat on a
    card.  His body ends at the counter's far edge (S3M_COUNTER_Y), the arms reach over it.  Flat fluorescent light
    from above, a cold rim from behind."""
    import env_c4_cine_bust as B
    out = B.fengler_counter(S3M_SIZE, S3M_AT, S3M_COUNTER_Y, S3M_KNOB, S3M_CARD, _fsrc(1))
    return _edge_shadow(out, S3M_COUNTER_Y - S3M_AT[1])


def _edge_shadow(out, row, depth=16, rgb=(14, 22, 18), alpha=0.55):
    """His body's shadow on the counter right in front of the far edge (the tubes are overhead): a dithered band
    `depth` px deep under every column where the figure meets the edge, fading away from the edge and towards
    the ends -- the trunk stands behind the counter instead of being pasted on its edge."""
    out = out.copy()
    h, w = out.shape[:2]
    r = int(row)
    on = out[r - 1, :, 3] == 255
    if not on.any():
        return out
    xs = np.nonzero(on)[0]
    xx = np.arange(w, dtype=np.float32)
    ends = np.clip(np.minimum(xx - xs.min(), xs.max() - xx) / 5.0, 0.0, 1.0)
    ends = np.where(on | ((xx >= xs.min()) & (xx <= xs.max())), ends, 0.0)
    bay = N.P.bayer(h, w)
    for k in range(depth):
        y = r + k
        if y >= h:
            break
        a = alpha * (1.0 - k / float(depth)) ** 1.4 * ends
        a = np.where(bay[y] < 0.25 + 0.75 * (1.0 - k / float(depth)), a, a * 0.5)
        cur = out[y, :, 3].astype(np.float32) / 255.0
        free = out[y, :, 3] < 255
        new = np.where(free, np.maximum(cur, a), cur)
        out[y, :, :3] = np.where((free & (a > cur))[:, None], np.asarray(rgb, np.uint8)[None, :], out[y, :, :3])
        out[y, :, 3] = (new * 255).astype(np.uint8)
    return out


# ========================================================================================= LS_C4_Homeward
W2_SIZE = (264, 220)         # one window of the split windows (layout homeward.win_k / win_a)


def w2_reflection(city):
    """The man's face mirrored in his compartment window, for the split windows of w2 (the motif of the night
    trains in LS_C3_Trains): Konrad under his hat in the Reich carriage ('berlin'), Alexei in the ushanka in the
    Soviet one ('karsk'), lit from below by the reading lamp / the tea-glass lamp, looking out at the land.  A
    W2_SIZE layer for the window hole: warm light, posterised in four steps, partial alpha (draw it over the
    landscape strips, normal or additive blending).  The faces sit in the lower half of the glass at the outer
    sides (Konrad left in the left window, Alexei right in the right one), turned towards each other across the
    split."""
    import env_c4_cine_bust as B
    import env_veltrava_cine_figs as F
    spec = CC.konrad() if city == 'berlin' else CC.alexei()
    if city == 'berlin':
        head_items = [lambda M, hp: CC.fedora(M, hp, y0=-13.2), lambda M, hp: CC.hair_short(M, hp)]
        torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.42, v_top=3.0),
                       lambda M, t: CC.scarf_wrap(M, y=-6.0, r=10.9, tube=4.6, ends='drape')]
        head_px, torso_px, yaw = (188.0, 112.0), (186.0, 152.0), -24.0
        tint = (236, 196, 140)
    else:
        head_items = [lambda M, hp: CC.ushanka(M, hp, flaps='down'),
                      lambda M, hp: CC.hair_short(M, hp, hairline=-13.0, front_z=9.0, burn_y=2.0)]
        torso_items = [lambda M, t: CC.coat_layers(M, t, v_open=0.16, v_top=7.0, lapel=False, quilt=(5.0, 0.55),
                                                   collar_h=12.0, collar_r=(13.4, 14.8)),
                       lambda M, t: CC.rollneck(M, 'knit', y_top=-11.5, y_bot=3.0, r=(10.2, 11.8))]
        head_px, torso_px, yaw = (80.0, 114.0), (82.0, 154.0), 24.0
        tint = (236, 186, 116)
    look = dict(key=(-0.20, 0.80, 0.56) if city == 'berlin' else (0.20, 0.80, 0.56), rim=(0.0, -0.6, -0.8),
                ambient=0.04, wrap=0.14, bg='berlin', glow=(0.8, 0.2), fill=0.02, fill_dir=(0.0, 0.0, 1.0), ao=0.5)
    styles = F.konrad_train_styles() if city == 'berlin' else F.alexei_train_styles()
    img = B.figure(spec, W2_SIZE, 1.15, head_px, torso_px, yaw, pitch=-3.0, torso_yaw=yaw * 0.5, look=look,
                   head_items=head_items, torso_items=torso_items, styles=styles, expr='neutral',
                   tone_passes=[], cache_key=('w2_reflection', city, _fsrc(1)))
    a = img[..., 3] > 0
    lum = img[..., :3].astype(np.float32).mean(-1) / 255.0
    lv = np.clip(np.floor(lum * 5.0 + N.P.bayer(W2_SIZE[1], W2_SIZE[0]) * 0.9), 0, 4)
    # the lamp lights the face; the coat below it fades into the dark glass (stepped, dithered)
    yy = np.arange(W2_SIZE[1], dtype=np.float32)[:, None]
    fade = np.clip(1.0 - (yy - (head_px[1] + 26.0)) / 46.0, 0.0, 1.0)
    lv = np.where(fade + N.P.bayer(W2_SIZE[1], W2_SIZE[0]) * 0.35 > 0.6, lv, np.maximum(lv - 2, 0))
    lv = np.where(fade > 0.05, lv, 0)
    out = np.zeros_like(img)
    sel = a & (lv > 0)
    k = (0.40 + 0.45 * lv / 4.0)[..., None]
    out[..., :3] = np.clip(np.asarray(tint, np.float32)[None, None] * k, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(sel, np.clip(22 + lv * 20, 0, 255), 0).astype(np.uint8)
    return out[:, ::-1].copy()


S4M_SIZE = (230, 300)        # the coat runs on to the canvas bottom (place it so that edge is under the letterbox)


def s4_konrad_medium(f):
    """Medium shot of LS_C4_Stamp s4 (the round-9 shot shows him only at the game's 56 px): Konrad at the foot of
    the shaft ladder, turned to the ladder at the left, looking up the shaft; hat, coat, scarf, the strap of his
    bag; f 0 his gloved left hand down at his side, 1 the hand pressed flat on the coat over the inner pocket where
    the German half is.  Fluorescent tubes overhead (flat green-white key), the daylight down the shaft as a cold
    rim from the upper left.  S4M_SIZE canvas, waist-up; the face is the dialogue portrait's (features drawn)."""
    import env_c4_cine_bust as B
    spec = CC.konrad()
    zoom = 1.30
    head_px, torso_px = (112.0, 70.0), (116.0, 116.0)
    look = dict(key=(0.15, -0.88, 0.45), rim=(-0.72, -0.52, -0.45), ambient=0.10, wrap=0.14, bg='berlin',
                glow=(0.6, 0.1), fill=0.10, fill_dir=(0.3, -0.2, 0.9), ao=0.5)
    sty = dict(spec['styles'])
    sty.update({
        'glove': MatStyle(ramp('#030304', '#08080a', '#0e0d10', '#151316', '#1d1a1d', '#272326', '#352e30',
                               '#4a4042'), [0.04, 0.09, 0.16, 0.26, 0.38, 0.54, 0.74], dither=0.02, rim='#b8d0c0',
                          spec=0.45, spec_pow=10.0),
        'inside': MatStyle(ramp('#020306', '#05070c', '#090c14'), [0.2, 0.5], rim=None),
        'arm_coat': sty['coat'],
    })

    def arms(M, ctx):
        z = ctx.zoom
        s = 21.0 * z
        sh = B.shoulder(ctx, 1.0, 0.98, out=0.5)            # his left arm: the near side (he faces left)
        if f == 0:
            el = sh + np.array([-4.0 * z, 30.0 * z, 6.0])
            wr = el + np.array([-2.0 * z, 26.0 * z, 6.0])
            hy, hz, hk = (-0.05, 1.0, 0.10), (0.30, 0.0, 0.95), dict(flex='relaxed', thumb='rest')
        else:
            el = sh + np.array([4.0 * z, 30.0 * z, 10.0])
            chest = ctx.t2v((-2.0, 30.0, 16.5))
            hy, hz = N.nrm((-0.80, -0.55, 0.15)), N.nrm((0.10, -0.20, 0.97))
            pts = N.hand_points(s, side=-1.0, flex='flat', spread=3.0, thumb='along')
            wr = chest - N.frame_along((0, 0, 0), hy, hz).to_view((pts['knuckles'][1] + pts['tips'][1]) * 0.5)
            hk = dict(flex='flat', thumb='along')
        return [N.arm(M, 'arm_coat', 'glove', sh, el, wr, (9.6 * z, 8.8 * z, 7.9 * z), hy, hz, s, cover=0.05,
                      cuff='glove', cuff_len=0.2 * s, sleeve_in='inside',
                      hand_kw=dict(dict(side=-1.0, spread=3.0, glove=True), **hk))]

    torso_items = list(spec['torso_items']) + [lambda M, t: B.coat_closed(M, t, y_from=24.0, skirt=70.0)]
    return B.figure(spec, S4M_SIZE, zoom, head_px, torso_px, yaw=-38.0, pitch=-12.0, roll=2.0, torso_yaw=-30.0,
                    look=look, torso_kw=dict(width=1.10, depth=1.04, slope=1.2), torso_items=torso_items,
                    styles=sty, extra=arms, expr='determined', cache_key=('s4_konrad_medium', f, _fsrc(1)))


# ========================================================================================= LS_C4_Voices
V2_SIZE = (240, 270)
V2_AT = (14, 98)             # top-left of Konrad's back in the frame (bottom cut by the letterbox)


V3T_SIZE = (260, 200)
V3T_AT = (-40, 190)          # frame position of the canvas (the hand comes in from the lower left)
V3T_COVER = ((96, 66), (560, 42), (576, 330), (92, 344))   # the notebook's cover (env_c4_cine_voices.v3_note)


def v3_thumb():
    """Insert v3: Alexei's left hand holding the notebook by its spine edge, in the green light of the signal --
    the thumb pad on the squared page beside the stapled spine, the fingers behind the cover (hidden by it: every
    pixel but the thumb inside V3T_COVER is cleared), the hand's edge, the wrist with the roll-neck's cuff and the
    quilted sleeve running out at the lower left.  V3T_SIZE canvas drawn at V3T_AT over v3_note.png."""
    s = 62.0
    ox, oy = V3T_AT
    hx = _norm((0.30, -0.42, 0.86))                     # thumb towards the viewer, onto the page
    hz0 = _norm((-0.70, -0.10, 0.70))                   # the back of the hand to the left, half to us
    hy = _norm(np.cross(hz0, hx))
    hz = _norm(np.cross(hx, hy))
    kw = dict(side=-1.0, flex=((30, 40, 18), (40, 56, 28), (50, 66, 34), (58, 72, 38)), spread=3.0,
              thumb=dict(abd=46.0, opp=24.0, mcp=6.0, ip=-4.0), nail='nail')
    pts = N.hand_points(s, side=-1.0, flex=kw['flex'], spread=3.0, thumb=kw['thumb'])
    wrist = _wrist_for(pts['thumb'], (156.0 - ox, 282.0 - oy, 10.0), hy, hz)
    elbow = wrist + np.array([-140.0, 110.0, -40.0])
    shoulder = elbow + np.array([-120.0, 140.0, -40.0])
    look = _look(key=(0.62, -0.62, 0.48), rim=(-0.70, -0.20, -0.68), ambient=0.11, fill=0.12, bg='karsk')

    def build(thumb_only):
        M = A.Mats()
        if thumb_only:
            return [N.hand_at(M, 'skin', wrist, hy, hz, s, parts=('thumb',), **kw)], M
        return [N.arm(M, 'quilt', 'skin', shoulder, elbow, wrist, (0.62 * s, 0.58 * s, 0.50 * s), hy, hz, s,
                      cover=0.45, cuff='knit', cuff_len=0.2 * s, sleeve_in='inside', hand_kw=kw)], M
    n, M = build(False)
    full = _paint(n, M, V3T_SIZE, look, 'signal', 'v3_thumb', z_range=(150.0, -150.0),
                  passes=[_quilt_stitches(M, wrist, _norm(wrist - elbow))])
    n2, M2 = build(True)
    th = _paint(n2, M2, V3T_SIZE, look, 'signal', 'v3_thumb_t', z_range=(150.0, -150.0))
    import env_veltrava_cine as VC
    cover = VC.poly_mask(V3T_SIZE[0], V3T_SIZE[1], [(x - ox, y - oy) for (x, y) in V3T_COVER])
    out = full.copy()
    out[cover & ~(th[..., 3] > 0), 3] = 0
    return out


def v2_konrad(f):
    """Konrad from behind at the tram loop (hat, coat, scarf), the tram leaving beyond him; f 0 arms down,
    1 the right arm rising, 2 raised (protect_marta: he waves to Ilse) -- shoulder, upper arm, bent elbow, forearm,
    the black glove open with the fingers up.  Morning light from the front (cold), the sodium lamp of the loop as
    a warm rim from the right."""
    import env_c4_cine_bust as B
    return B.konrad_back_wave(f, V2_SIZE, _fsrc(1))
