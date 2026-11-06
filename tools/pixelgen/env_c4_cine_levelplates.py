"""env_c4_cine_levelplates -- cinematic plates built from the levels' own art (owner: cine stream, polish pass).

  loop_layers(light)     the tram loop Süd 8 of L_C4_AnnexA as parallax layers (sky + dome, far, mid, the street
                         WITHOUT the tram, the near snow bank) for 'dawn' (LS_C4_Number n4, ~5.10) and 'morning'
                         (LS_C4_Voices v1/v2, the poster of S 2 torn back); + the hour's additive light pools
  loop_fx()              the level's own animated fx copied for the films: steam from the grate of S 2, the
                         chimney of No. 11, the blinking crane lights, the lorry's exhaust, the crows on the wire,
                         Ilse at the last window of the tram
  tram_sheets()          tram 74 No. 3518 as the level paints it: arriving (front left, Marta in the cab) and
                         leaving (front right, line board and fleet number never mirrored; Ilse at the rear
                         window without / with her hand on the glass)
  siding(lit)            the siding hall of L_C4_TunnelsB around wagon 24 318 / C-17/45 under its work lamp, lit
                         and with the lamp out (only the dawn through the portal) -- LS_C4_Voices v4; the same
                         hall through the booth window (LS_C4_Card c4)
  annex_ladder()         the foot of the shaft ladder in the card hall of L_C4_AnnexB (LS_C4_Stamp s4)
  annex_back()           the card hall behind the counter „Auskunft · Abgleich“ (LS_C4_Stamp s3b background)
People are never painted here: Marta and the crowds come from the game's sheets (env_c4_cine_kit.fig_sheet /
lit_row), Ilse from the level's life strip.  Anchors in layout.json "places".
"""
from __future__ import annotations

import numpy as np

import env_c4_cine_kit as Q
import env_c4_cine_levelart as LA

L = Q.LAYOUT.setdefault('places', {})

MOD_DAWN = (0.76, 0.79, 0.85)          # the level's canvas_modulate #C2C9D8
MOD_MORNING = (0.90, 0.92, 0.96)
LOOP_LAYERS = {                        # name: (file, home x, home y, parallax) -- scene.json of berlin_annex
    'sky': ('sky', 0, 0, 0.03),
    'dome': ('dome', 430, 54, 0.08),
    'far': ('far', 0, 62, 0.2),
    'mid': ('mid', 0, 150, 0.5),
    'fg': ('fg_loop', 0, 318, 1.25),
}


def _f(img8):
    return img8.astype(np.float32) / 255.0


def _grade_unlit(a, light):
    if light == 'morning':
        return LA.grade(a, mul=(1.16, 1.15, 1.12), add=(0.07, 0.07, 0.075), sat=0.85)
    return a


def loop_layers(light='dawn'):
    """{name: (rgba uint8, [home_x, home_y, parallax])} -- the loop at the hour, layer by layer."""
    mod = MOD_MORNING if light == 'morning' else MOD_DAWN
    out = {}
    for name, (fn, hx, hy, par) in LOOP_LAYERS.items():
        a = LA.layer('berlin_annex', fn)['alb'].copy()
        a = _grade_unlit(a, light)
        a[..., :3] *= np.asarray(mod, np.float32)
        out[name] = (LA.to8(a), [hx, hy, par])
    st = LA.bake_street(light, bared=(light == 'morning'))
    s = _f(st.lay.c)
    if light == 'morning':
        s = LA.grade(s, mul=(1.05, 1.05, 1.04), add=(0.02, 0.02, 0.025))
    s[..., :3] *= np.asarray(mod, np.float32)
    out['street'] = (LA.to8(s), [0, 0, 1.0])
    # the lit pools of the street lights (additive, the runtime lets them breathe)
    k = 0.4 if light == 'morning' else 1.0
    blobs = []
    for li in st.all_lights():
        nm = str(li.get('name', ''))
        x, y = li['pos']
        if nm in ('dawn_sky', 'snow_bounce', 'day_sky') or 'tram' in nm or y < 0:
            continue
        e = float(li['energy'])
        r = float(li['radius'])
        warm = li.get('kind', 'warm') == 'warm'
        col = (int(70 * e * k), int(46 * e * k), int(16 * e * k)) if warm else (int(34 * e), int(40 * e), int(46 * e))
        if 'sodium' in nm:
            col = (int(96 * k), int(62 * k), int(18 * k))
            blobs.append((x, 300, r * 0.7, 12, (int(60 * k), int(40 * k), int(12 * k)), 1.5))
        blobs.append((x, y, r * 0.45, r * 0.4, col, 1.4))
    out['glow'] = (Q.glow_sprite(st.lay.w, 360, blobs, 6.0), [0, 0, 1.0])
    return out, st


def loop_fx():
    """{file: (rgba uint8, meta)} -- the level's animated fx, copied unchanged (frames, fps, home position)."""
    import json
    import os
    from PIL import Image
    d = os.path.join(LA.ENV, 'berlin_annex')
    with open(os.path.join(d, 'scene.json'), encoding='utf-8') as fh:
        sc = json.load(fh)
    want = ('steam_s2', 'chimney_11', 'crane_light_0', 'crane_light_1', 'crane_light_2', 'exhaust')
    out = {}
    for e in sc.get('fx', []):
        if e.get('name') in want:
            img = np.asarray(Image.open(os.path.join(d, e['file'])).convert('RGBA')).copy()
            par = e.get('parallax', [1.0, 1.0])
            out[e['name']] = (img, {'frames': int(e['frames']), 'fps': float(e['fps']), 'pos': list(e['pos']),
                                    'parallax': float(par[0])})
    for e in sc.get('decals', []):
        if e.get('name') == 'fence_blinker':
            img = np.asarray(Image.open(os.path.join(d, e['file'])).convert('RGBA')).copy()
            out['fence_blinker'] = (img, {'frames': int(e['frames']), 'fps': float(e['fps']), 'pos': list(e['pos']),
                                          'parallax': 1.0})
    crows = os.path.join(LA.ENV, 'karsk_railyard', 'actors', 'crows.png')
    if os.path.exists(crows):
        img = np.asarray(Image.open(crows).convert('RGBA')).copy()
        out['crows'] = (img, {'frames': img.shape[1] // 14, 'fps': 6.0, 'pos': [676, 176], 'parallax': 1.0,
                              'perches': [[676, 176], [690, 176], [705, 176], [722, 176]]})
    return out


# ----------------------------------------------------------------------------------------------- the tram
def _ilse_frames():
    import os
    from PIL import Image
    p = os.path.join(LA.ENV, 'berlin_annex', 'life', 'ilse.png')
    im = np.asarray(Image.open(p).convert('RGBA')).copy()
    return [im[:, i * 18:(i + 1) * 18].copy() for i in range(im.shape[1] // 18)]


ILSE_LOOK, ILSE_HAND = 6, 21           # frames of the level's life strip: looking out / red mitten on the glass


def _marta_head(flip):
    """Marta's head and shoulders from her game sheet, re-lit by the cab's warm light (cropped)."""
    cells = Q.anim_frames('marta', 'idle_side', pick=[0])
    c, n = cells[0]
    if flip:
        c = c[:, ::-1].copy()
        if n is not None:
            n = n[:, ::-1].copy()
            n[..., 0] = 255 - n[..., 0]
    look = dict(amb=(0.50, 0.46, 0.42), key=(0.2, 0.5, 0.8), key_rgb=(0.55, 0.44, 0.26), rim=None, bands=3)
    return Q.relight(c, n, **look)[0:26]


def tram_sheets():
    """(arrive rgba, leave sheet rgba (2 frames), meta) -- the level's tram in both directions."""
    import env_c4_annex_layout as AL
    base, (x0, y0) = LA.street_tram()
    h, w = base.shape[:2]
    t0 = AL.TRAM[0] - x0
    ty0 = AL.TRAM_Y[0] - y0
    belt = 258 - y0
    wy0 = 232 - y0
    mod = np.asarray(MOD_DAWN, np.float32)

    def finish(a8, light):
        a = _f(a8)
        if light == 'morning':
            a = LA.grade(a, mul=(1.06, 1.06, 1.05), add=(0.02, 0.02, 0.02))
        a[..., :3] *= np.asarray(MOD_MORNING if light == 'morning' else MOD_DAWN, np.float32)
        return LA.to8(a)

    def paste(dst, src, x, y):
        sh, sw = src.shape[:2]
        reg = dst[y:y + sh, x:x + sw]
        m = src[..., 3] > 0
        reg[m] = src[m]

    def cab(img, mirrored):
        """Marta behind the two narrow cab windows of the front end, facing the way the car drives."""
        head = _marta_head(flip=not mirrored)          # the sheet faces right; the arriving car drives left
        win = np.zeros(img.shape[:2], bool)
        for a in (t0 + 3, t0 + 11):
            ax = (w - a - 7) if mirrored else a
            win[wy0 + 2:wy0 + 22, ax:ax + 7] = True
        hx = (w - (t0 - 2) - 32) if mirrored else t0 - 2
        tmp = np.zeros_like(img)
        paste(tmp, head, hx, wy0 - 2)
        m = (tmp[..., 3] > 0) & win
        img[m] = tmp[m]

    ilse = _ilse_frames()
    ia = AL.ILSE_WIN[0] - x0
    arrive = base.copy()
    cab(arrive, False)
    paste(arrive, ilse[ILSE_LOOK], ia, 232 - y0)
    arrive = finish(arrive, 'dawn')
    # leaving: mirrored, the line board and the fleet number copied back unmirrored
    leave = base[:, ::-1].copy()
    for (bx, by, bw, bh) in ((t0 + 6, ty0 + 7, 30, 8), (t0 + 152, belt + 5, 20, 8)):
        blk = base[by:by + bh, bx:bx + bw].copy()
        leave[by:by + bh, w - bx - bw:w - bx] = blk
    cab(leave, True)
    frames = []
    ix = w - ia - 18
    for fi in (ILSE_LOOK, ILSE_HAND):
        f = leave.copy()
        fr = ilse[fi][:, ::-1].copy()
        paste(f, fr, ix, 232 - y0)
        frames.append(finish(f, 'morning'))
    meta = {'size': [w, h], 'rail_y': AL.TRAM_Y[1] - y0, 'origin': [x0, y0], 'level_x': AL.TRAM[0]}
    return arrive, Q.sheet(frames), meta


# ----------------------------------------------------------------------------------------------- the siding
SIDING_CROP = (1280, 0, 1920, 360)     # level x 1280..1920 of L_C4_TunnelsB = the film's 0..640
SIDING_BULB = (1646, 153)              # the work lamp over the wagon (scene.json light 'bulb_wagon')
SIDING_PORTAL = (1903, 230)
SIDING_KEROSENE = (1339, 244)


def siding(lit=True, crop=SIDING_CROP):
    """The siding hall around wagon C-17/45: lit by its single work lamp (+ the dawn at the portal, the booth's
    kerosene) or with the lamp out.  Returns rgba uint8 of the crop."""
    Ld = LA.layer('karsk_tunnels', 'room', crop)
    x0 = crop[0]
    cool = LA.hexf('#E8E4DA')
    blue = LA.hexf('#9FB4CC')
    warm = LA.hexf('#F2B060')
    lights = [{'pos': SIDING_PORTAL, 'height': 4, 'rgb': blue, 'energy': 0.55, 'radius': 170},
              {'pos': SIDING_KEROSENE, 'height': 10, 'rgb': warm, 'energy': 0.5 if lit else 0.35, 'radius': 80}]
    if lit:
        lights.append({'pos': SIDING_BULB, 'height': 30, 'rgb': cool, 'energy': 1.25, 'radius': 260})
        lights.append({'pos': (SIDING_BULB[0], 300), 'height': 60, 'rgb': cool, 'energy': 0.35, 'radius': 180})
    amb = (0.16, 0.17, 0.21) if lit else (0.07, 0.08, 0.11)
    a = LA.relight(Ld, amb, lights, origin=(x0, crop[1]), emis_k=1.0)
    # the other work lamps of the hall are off in the film: their bulbs lose the emission
    e = Ld['emi']
    if e is not None:
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
        xx += x0
        for (lx, ly, keep) in ((1432, 136, False), (1812, 136, False), (SIDING_BULB[0], SIDING_BULB[1], lit)):
            if keep:
                continue
            near = (np.abs(xx - lx) < 12) & (np.abs(yy - ly) < 10) & (e[..., 3] > 0)
            a[near, :3] = Ld['alb'][near, :3] * (0.30 if not lit else 0.4)
    a = LA.dither_quant(a, 40, seed=3)
    return LA.to8(a)


def siding_glow(crop=SIDING_CROP):
    bx = SIDING_BULB[0] - crop[0]
    by = SIDING_BULB[1] - crop[1]
    return Q.glow_sprite(crop[2] - crop[0], crop[3] - crop[1],
                         [(bx, by + 6, 120, 110, (64, 62, 58), 1.3), (bx, by + 2, 16, 12, (120, 116, 104), 1.6),
                          (bx, 296, 170, 22, (34, 34, 32), 1.5)], 6.0)


def booth_view():
    """The siding as seen through the booth window (LS_C4_Card c4): the lit hall around the wagon, level x
    1470..1830, y 70..262 (the window shows 350 x 184 of it)."""
    return siding(True, (1470, 70, 1830, 262))


# ----------------------------------------------------------------------------------------------- the annex
ANNEX_X = 846                          # world x of annex.png


def annex_ladder():
    """The foot of the shaft ladder in the card hall (annex x 0..640): fluorescent light, daylight down the shaft."""
    Ld = LA.layer('berlin_annex', 'annex', (0, 0, 640, 360))
    fl = LA.hexf('#E8F0E4')
    day = LA.hexf('#C8D8EC')
    lights = [{'pos': (ANNEX_X + 40, 30), 'height': 40, 'rgb': day, 'energy': 0.7, 'radius': 200},
              {'pos': (ANNEX_X + 50, 250), 'height': 46, 'rgb': day, 'energy': 0.55, 'radius': 130}]
    for x in (154, 274, 394, 514, 634):
        lights.append({'pos': (ANNEX_X + x, 78), 'height': 30, 'rgb': fl, 'energy': 0.6, 'radius': 180})
    a = LA.relight(Ld, (0.52, 0.56, 0.54), lights, origin=(ANNEX_X, 0), emis_k=1.0)
    return LA.to8(LA.dither_quant(a, 40, seed=5))


def annex_back(x0=780, x1=1074):
    """The counter wall of the annex (annex x 780..1074: the glass booth „Auskunft · Abgleich“ with its
    typewriters and the cabinets), lit by its tubes -- the far background of the counter close-up."""
    Ld = LA.layer('berlin_annex', 'annex', (x0, 40, x1, 290))
    fl = LA.hexf('#E8F0E4')
    lights = [{'pos': (ANNEX_X + x, 78), 'height': 30, 'rgb': fl, 'energy': 0.6, 'radius': 180}
              for x in range(x0 + 40, x1, 110)]
    a = LA.relight(Ld, (0.50, 0.54, 0.52), lights, origin=(ANNEX_X + x0, 40), emis_k=1.0)
    return LA.to8(a)
