"""env_veltrava_hall_docs -- inspect document of L_C3_Hall owned by the palais art stream.

veltrava_hall_carbon.png   ev_c3_carbon 'Durchschrift aus Kabine 2': Elena's desk blotter from booth 2,
                           lightly rubbed with a pencil.  In the graphite her last note, pressed through
                           from the (missing) protocol notebook, shows pale:
                               '§ 4 - Personen.' / 'Vom Sekretariat,' / 'nicht von einer Delegation.' /
                               'Wer hat den Text geliefert?'
                           faintly, older: '10:09 - Mik. 12' (matches the booth log), mirrored ink blots.
veltrava_hall_documents.json   metadata (schema of karsk_documents.json)
data/locale/de_env_veltrava_hall.json   German alt text
Pixel art 1:1, shown at 3x.  The handwriting is drawn from hand-defined stroke skeletons (no fonts).
(The seating plan and the booth log documents belong to the puzzle stream.)
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import env_veltrava_hall_kit as kit
import pg

R = kit.palais_ramps()
W, H = 300, 200

# ---------------------------------------------------------------- hand skeletons
# units of x-height: baseline v = 0, x-height v = -1, ascender -1.9, descender +0.9; (strokes, advance)
HAND = {
    'a': ([[(0.9, -0.85), (0.5, -1.0), (0.1, -0.6), (0.2, -0.05), (0.6, 0.0), (0.9, -0.4)], [(0.9, -1.0), (0.92, 0.0)]], 1.15),
    'c': ([[(0.85, -0.85), (0.45, -1.0), (0.1, -0.55), (0.25, -0.05), (0.85, -0.1)]], 1.0),
    'd': ([[(0.9, -0.85), (0.5, -1.0), (0.1, -0.6), (0.2, -0.05), (0.6, 0.0), (0.9, -0.4)], [(0.9, -1.9), (0.92, 0.0)]], 1.15),
    'e': ([[(0.1, -0.5), (0.85, -0.55), (0.7, -0.95), (0.35, -1.0), (0.1, -0.6), (0.25, -0.05), (0.85, -0.1)]], 1.0),
    'f': ([[(0.8, -1.8), (0.45, -1.9), (0.3, -1.6), (0.3, 0.6)], [(0.0, -1.0), (0.7, -1.0)]], 0.8),
    'g': ([[(0.9, -0.85), (0.5, -1.0), (0.1, -0.6), (0.25, -0.1), (0.6, -0.05), (0.9, -0.45)],
           [(0.9, -1.0), (0.9, 0.6), (0.5, 0.9), (0.1, 0.7)]], 1.15),
    'h': ([[(0.1, -1.9), (0.1, 0.0)], [(0.1, -0.6), (0.45, -1.0), (0.8, -0.85), (0.85, 0.0)]], 1.05),
    'i': ([[(0.2, -1.0), (0.2, 0.0)], [(0.2, -1.45), (0.26, -1.5)]], 0.55),
    'k': ([[(0.1, -1.9), (0.1, 0.0)], [(0.75, -1.0), (0.1, -0.45)], [(0.3, -0.6), (0.8, 0.0)]], 0.95),
    'l': ([[(0.2, -1.9), (0.2, -0.15), (0.4, 0.0)]], 0.6),
    'm': ([[(0.1, -1.0), (0.1, 0.0)], [(0.1, -0.7), (0.35, -1.0), (0.6, -0.8), (0.6, 0.0)],
           [(0.6, -0.7), (0.85, -1.0), (1.1, -0.8), (1.1, 0.0)]], 1.35),
    'n': ([[(0.1, -1.0), (0.1, 0.0)], [(0.1, -0.65), (0.45, -1.0), (0.8, -0.8), (0.8, 0.0)]], 1.0),
    'o': ([[(0.5, -1.0), (0.1, -0.6), (0.2, -0.1), (0.55, 0.0), (0.9, -0.4), (0.8, -0.9), (0.5, -1.0)]], 1.05),
    'r': ([[(0.1, -1.0), (0.1, 0.0)], [(0.1, -0.6), (0.45, -1.0), (0.75, -0.95)]], 0.85),
    's': ([[(0.8, -0.9), (0.45, -1.0), (0.15, -0.8), (0.3, -0.55), (0.7, -0.4), (0.8, -0.15), (0.45, 0.0),
            (0.1, -0.1)]], 0.95),
    't': ([[(0.35, -1.6), (0.35, -0.15), (0.6, 0.0)], [(0.0, -1.0), (0.7, -1.0)]], 0.8),
    'v': ([[(0.05, -1.0), (0.45, 0.0), (0.85, -1.0)]], 0.95),
    'x': ([[(0.1, -1.0), (0.8, 0.0)], [(0.8, -1.0), (0.1, 0.0)]], 0.95),
    'P': ([[(0.1, 0.0), (0.1, -1.9), (0.6, -1.9), (0.9, -1.6), (0.6, -1.1), (0.1, -1.1)]], 1.1),
    'V': ([[(0.0, -1.9), (0.5, 0.0), (1.0, -1.9)]], 1.15),
    'S': ([[(0.95, -1.7), (0.55, -1.9), (0.15, -1.65), (0.3, -1.15), (0.8, -0.8), (0.85, -0.3), (0.45, 0.0),
            (0.05, -0.2)]], 1.1),
    'D': ([[(0.1, 0.0), (0.1, -1.9), (0.55, -1.85), (0.95, -1.3), (0.9, -0.5), (0.5, 0.0), (0.1, 0.0)]], 1.15),
    'W': ([[(0.0, -1.9), (0.3, 0.0), (0.65, -1.2), (1.0, 0.0), (1.3, -1.9)]], 1.45),
    'T': ([[(0.0, -1.9), (1.0, -1.9)], [(0.5, -1.9), (0.5, 0.0)]], 1.1),
    'M': ([[(0.05, 0.0), (0.1, -1.9), (0.55, -0.8), (1.0, -1.9), (1.05, 0.0)]], 1.25),
    '§': ([[(0.75, -1.75), (0.4, -1.95), (0.15, -1.7), (0.35, -1.35), (0.7, -1.05), (0.75, -0.75), (0.4, -0.55)],
           [(0.45, -1.4), (0.15, -1.15), (0.2, -0.85), (0.6, -0.55), (0.7, -0.2), (0.4, 0.0), (0.1, -0.15)]], 1.0),
    '4': ([[(0.65, 0.0), (0.65, -1.9), (0.05, -0.6), (0.95, -0.6)]], 1.05),
    '1': ([[(0.2, -1.5), (0.55, -1.9), (0.55, 0.0)]], 0.85),
    '0': ([[(0.5, -1.9), (0.1, -1.3), (0.15, -0.4), (0.5, 0.0), (0.85, -0.5), (0.85, -1.4), (0.5, -1.9)]], 1.05),
    '9': ([[(0.85, -1.4), (0.5, -1.9), (0.1, -1.5), (0.3, -1.0), (0.85, -1.2), (0.75, 0.0)]], 1.0),
    '2': ([[(0.1, -1.5), (0.5, -1.9), (0.9, -1.5), (0.1, 0.0), (0.95, 0.0)]], 1.05),
    '–': ([[(0.1, -0.55), (0.9, -0.55)]], 1.0),
    '-': ([[(0.15, -0.55), (0.75, -0.55)]], 0.85),
    '.': ([[(0.2, -0.05), (0.3, 0.0)]], 0.5),
    ',': ([[(0.3, -0.05), (0.15, 0.4)]], 0.5),
    ':': ([[(0.25, -1.0), (0.3, -0.95)], [(0.25, -0.1), (0.3, -0.05)]], 0.5),
    '?': ([[(0.1, -1.6), (0.45, -1.9), (0.85, -1.65), (0.7, -1.1), (0.45, -0.85), (0.45, -0.5)],
           [(0.45, -0.1), (0.5, 0.0)]], 1.0),
    ' ': ([], 0.75),
}


def hand_line(text, x, y, xh, slant=0.22, seed=0, wobble=0.05, track=0.18):
    """Polylines (px) for `text` with the baseline at y, starting at x.  Returns (polys, end_x)."""
    rng = np.random.default_rng(seed)
    polys = []
    cx = x
    base_wave = rng.uniform(0, 2 * math.pi)
    for i, ch in enumerate(text):
        strokes, adv = HAND.get(ch, HAND[' '])
        sc = xh * rng.uniform(0.94, 1.06)
        dy = math.sin(base_wave + i * 0.45) * 0.35
        for st in strokes:
            pts = []
            for (u, v) in st:
                px_ = cx + u * sc - v * sc * slant + rng.normal(0, wobble)
                py_ = y + dy + v * sc + rng.normal(0, wobble)
                pts.append((px_, py_))
            polys.append(smooth(pts, 5) if len(pts) >= 3 else pts)
        cx += (adv + track) * sc
    return polys, cx


def smooth(pts, sub=5):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def bbox_of(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


# ---------------------------------------------------------------- the document
LINES = [('§ 4 – Personen.', 9.0, 64), ('Vom Sekretariat,', 7.0, 92), ('nicht von einer Delegation.', 7.0, 116),
         ('Wer hat den Text geliefert?', 7.0, 142)]


def carbon():
    lay = kit.TLayer(W, H, R, 'veltrava_hall_carbon')
    rng = np.random.default_rng(1964)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # booth desk (walnut) around the pad
    grain = pg.value_noise(W, H, 6, 3, octaves=2)
    lay.put(np.ones((H, W), bool), 0, 0, 'D', 2.4 + (grain - 0.5) * 1.2 + (yy % 7 == 0) * -0.4, flat=False)
    # blotter: blotting paper (cream) in leather corners
    bx0, by0, bx1, by1 = 14, 10, 286, 190
    edge = np.minimum(np.minimum(xx - bx0, bx1 - 1 - xx), np.minimum(yy - by0, by1 - 1 - yy))
    t = 6.2 - np.clip((10 - edge) / 10, 0, 1) * 0.7 + (pg.value_noise(W, H, 30, 5, octaves=2) - 0.5) * 0.4
    pad = (xx >= bx0) & (xx < bx1) & (yy >= by0) & (yy < by1)
    lay.put(pad, 0, 0, 'P', t, flat=False)
    for _ in range(260):                                                   # fibres
        x, y = int(rng.integers(bx0, bx1)), int(rng.integers(by0, by1))
        lay.px(x, y, 'P', float(rng.choice([5.2, 5.6])))
    lay.rect(bx0, by1, bx1 - bx0, 2, 'D', 1.0)                              # pad edge shadow
    lay.rect(bx1, by0 + 2, 2, by1 - by0, 'D', 1.0)
    for (cx, cy, sx, sy) in ((bx0, by0, 1, 1), (bx1 - 1, by0, -1, 1), (bx0, by1 - 1, 1, -1), (bx1 - 1, by1 - 1, -1, -1)):
        for k in range(26):
            for j in range(26 - k):
                lay.px(cx + sx * j, cy + sy * k, 'R', 1.8 + (0.6 if (j + k) % 9 == 0 else 0))
        for k in range(26):                                                # stitched seam
            if k % 3 == 0:
                lay.px(cx + sx * (25 - k), cy + sy * k, 'R', 3.0)
    # mirrored fountain-pen blots of older notes (blue-black, as blotting paper keeps them)
    for (x0, y0, ln) in ((200, 30, 46), (40, 166, 60), (180, 170, 40)):
        polys, _ = hand_line('nenon eser', x0, y0, 4.0, slant=-0.25, seed=x0, wobble=0.25)
        m = kit.stroke_mask(W, H, [[(2 * x0 + ln - px_, py_) for (px_, py_) in pl] for pl in polys], 0.55)
        lay.put(m & pad, 0, 0, 'I', 2.6)
    for (bx, by, r) in ((236, 40, 2.2), (62, 172, 1.6)):
        lay.ellipse(bx, by, r, r * 0.8, 'I', 2.4)
    # the indentations: Elena's last note + an older log entry
    note = np.zeros((H, W), bool)
    marks = {}
    for i, (txt, xh, base) in enumerate(LINES):
        polys, ex = hand_line(txt, 46 + (i % 2) * 3, base, xh, seed=40 + i)
        m = kit.stroke_mask(W, H, polys, 0.62 if i == 0 else 0.56, seed=i)
        note |= m
        marks['line_%d' % (i + 1)] = {'rect': bbox_of(m), 'text': txt}
    # 'Personen' underlined twice
    ul = kit.stroke_mask(W, H, [[(118, 69), (200, 67)], [(121, 72), (196, 71)]], 0.55)
    note |= ul
    old, _ = hand_line('10:09 - Mik. 12', 196, 178, 4.6, seed=77)
    oldm = kit.stroke_mask(W, H, old, 0.5)
    # pencil rubbing: an irregular region of diagonal graphite strokes over the note
    cxr, cyr = 150, 104
    rr = ((xx - cxr) / 128) ** 2 + ((yy - cyr) / 66) ** 2
    rub_edge = pg.value_noise(W, H, 18, 9, octaves=3)
    rub = (rr < 0.82 + (rub_edge - 0.5) * 0.5) & pad
    hatch = np.zeros((H, W), np.float32)
    for k in range(-H, W + H, 2):
        seg_len = int(rng.integers(16, 60))
        off = int(rng.integers(0, 30))
        for s in range(0, W + H, seg_len + int(rng.integers(2, 8))):
            for j in range(seg_len):
                x = k + off + s + j
                y = int(round((s + j) * 0.62))
                if 0 <= x < W and 0 <= y < H:
                    hatch[y, x] += 1.0
    dens = np.clip(1.15 - rr, 0, 1) ** 0.6
    thr = pg.bayer(W, H, 0, 0, 4)
    graphite = rub & ((hatch > 0) | (thr < dens * 0.55))
    lay.put(graphite, 0, 0, 'M', 3.4, flat=True)
    lay.put(rub & ~graphite, 0, 0, 'M', 4.6, flat=True)
    lay.put(rub & graphite & (thr < dens * 0.35), 0, 0, 'M', 2.6, flat=True)
    # the grooves stay pale inside the rubbing; a 1-px shadow on their lower-left side; faint outside
    groove_shadow = np.roll(np.roll(note, 1, axis=0), -1, axis=1) & ~note
    lay.put(rub & groove_shadow, 0, 0, 'M', 2.0, flat=True)
    lay.put(rub & note, 0, 0, 'P', 6.8, flat=True, crisp=True)
    lay.put(~rub & note & pad, 0, 0, 'P', 5.4, flat=True)
    old_in = oldm & pad
    lay.put(old_in & rub, 0, 0, 'P', 6.2, flat=True)
    lay.put(old_in & ~rub, 0, 0, 'P', 5.0, flat=True)
    lay.put(np.roll(old_in, 1, axis=0) & ~old_in & pad, 0, 0, 'P', 4.6, flat=True)
    marks['note'] = {'rect': bbox_of(note), 'note': "Elena's last note, pressed through and revealed by the rubbing"}
    marks['old_entry'] = {'rect': bbox_of(oldm), 'text': '10:09 - Mik. 12',
                          'note': 'older, faint impression; matches the booth log (10:09, microphone 12)'}
    marks['rubbing'] = {'rect': bbox_of(rub), 'note': 'graphite rubbing'}
    # the pencil that did it (hexagonal, gold lacquer), lying across the lower right corner
    p0, p1 = (206, 158), (284, 128)
    for k in range(3):
        tone = (4.4, 3.4, 2.2)[k]
        for (x, y) in kit.bres(p0[0], p0[1] + k, p1[0], p1[1] + k):
            lay.px(x, y, 'B', tone, flat=True)
    for (x, y) in kit.bres(p0[0] - 8, p0[1] + 4, p0[0], p0[1]):
        lay.px(x, y, 'D', 5.0)
        lay.px(x, y + 1, 'D', 4.0)
    lay.rect(p0[0] - 10, p0[1] + 4, 3, 2, 'M', 1.4)
    for (x, y) in kit.bres(p1[0] - 6, p1[1] + 2, p1[0], p1[1]):
        lay.px(x, y, 'S', 4.0)
        lay.px(x, y + 1, 'S', 3.0)
    marks['pencil'] = {'rect': [196, 124, 90, 42], 'note': 'pencil used for the rubbing'}
    lay.resolve()
    return lay, marks


def build_all(doc_dir, locale_path):
    out = []
    lay, marks = carbon()
    p = os.path.join(doc_dir, 'veltrava_hall_carbon.png')
    kit.save_rgba(lay.c, p)
    out.append((p, 'ev_c3_carbon: Elena\'s blotter from booth 2, pencil-rubbed impression of her last note'))
    meta = {
        'scene': 'L_C3_Hall',
        'palette': 'palais',
        'generator': 'tools/pixelgen/env_veltrava_hall_docs.py (via env_veltrava_hall.py)',
        'date': kit.DATE,
        'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Handwriting from hand-defined stroke skeletons; '
                'the UI shows the item name/description as HD text. All rects are [x, y, w, h] in document '
                'pixels. Seating plan and booth log documents are owned by the puzzle stream.',
        'documents': [{
            'file': 'res://assets/ui/documents/veltrava_hall_carbon.png',
            'size': [W, H],
            'display_scale': 3,
            'id': 'veltrava_hall_carbon',
            'alt_key': 'doc.veltrava_hall.carbon.alt',
            'item_id': 'ev_c3_carbon',
            'objective': 'c3b_inspect_booth',
            'hotspot': 'booth_2',
            'title_key': 'item.c3_carbon.name',
            'description_key': 'item.c3_carbon.description',
            'describes': "Elena's desk blotter from interpreter booth 2, lightly rubbed with a pencil. Pale "
                         "in the graphite: '§ 4 – Personen.' (underlined twice) / 'Vom Sekretariat,' / "
                         "'nicht von einer Delegation.' / 'Wer hat den Text geliefert?'. Faint older entry "
                         "'10:09 - Mik. 12'; mirrored ink blots; the pencil lies across the corner.",
            'marks': marks,
        }],
    }
    mp = os.path.join(doc_dir, 'veltrava_hall_documents.json')
    with open(mp, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    out.append((mp, 'document metadata (alt key, marks) for ev_c3_carbon'))
    loc = {
        'locale': 'de',
        'area': 'env_veltrava_hall',
        'strings': {
            'doc.veltrava_hall.carbon.alt':
                'Elenas Schreibunterlage aus Kabine 2, mit Bleistift leicht schraffiert. In der grauen '
                'Schraffur steht hell ihre durchgedrückte Handschrift: „§ 4 – Personen. Vom Sekretariat, '
                'nicht von einer Delegation. Wer hat den Text geliefert?“ – „Personen“ ist zweimal '
                'unterstrichen. Am Rand, schwächer, ein älterer Eintrag: „10:09 – Mik. 12“. Daneben '
                'liegt der Bleistift. Das Protokollheft, das auf der Unterlage lag, fehlt.',
        },
    }
    os.makedirs(os.path.dirname(locale_path), exist_ok=True)
    with open(locale_path, 'w', encoding='utf-8') as f:
        json.dump(loc, f, indent=1, ensure_ascii=False)
    out.append((locale_path, 'German alt text of the hall document'))
    return out
