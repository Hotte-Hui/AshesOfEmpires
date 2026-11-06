"""env_c4p2_cine_busts -- the cast's dialogue busts as film figures (owner: cine stream, round 10).

Close figures of the Chapter-4-part-2 films (Irina at her dispatch window, Ekdahl at his compartment window, Irina
and Alexei at the teleprinter) are the cast's own dialogue portraits: the same sculpt, the same posterised light,
the same hand-designed eyes, brows and mouths, at the portraits' native 112 px -- so a face in a film is exactly
the face the player knows from the dialogue box.  This module runs chargen_portrait2's frame pipeline (read-only)
and keeps the figure's coverage as alpha instead of painting the dialogue background, then grades it to the shot:
a key tint, a window's cold fill on the shadow side and an optional rim, all snapped to the figure's own ramps
(the tones stay crisp).  Deterministic.
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import chargen_portrait2 as PR        # noqa: E402  (render pipeline; read-only)
import chargen_portrait2_face as FC   # noqa: E402
import chargen_portrait2_paint as P   # noqa: E402

SIZE = PR.SIZE


def bust(cid, expr='neutral', row='rest'):
    """One dialogue frame of `cid` as RGBA (112 x 112): the portrait pipeline without its background."""
    spec = PR.C.CAST[cid]()
    mouth_state = PR.MOUTH_OF_ROW[row]
    blink = row.startswith('blink')
    G = PR.gbuffer(spec, expr, mouth_state)
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
    PR.draw_features(spec, G, cv, expr, mouth_state, blink, v)
    tone = P.clean(cv.tone, d.mat, protect=cv.locked)
    rgb = P.colorize(d, tone, styles, names)
    rgb = P.outline(rgb, d, styles, names, look=look)
    rgb, _ = P.depth_lines(rgb, d, styles, names, spec['groups'], skip=spec.get('no_depth_line', ()))
    rgb = P.apply_rim(rgb, d, rim, key, styles, names, tone)
    PR.paint_abs(spec, cv, rgb, v)
    for fn in spec.get('rgb_passes', ()):
        rgb = fn(spec, G, rgb, v, expr, row)
    out = np.zeros((SIZE, SIZE, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(d.hit, 255, 0)
    return out


def grade(rgba, mul=(1.0, 1.0, 1.0), lift=(0, 0, 0), side_fill=None, rim=None):
    """Grade a bust to the shot: multiply / lift in sRGB (a warm lamp, a cold window), optionally darken the
    side away from the key (side_fill = ('left'|'right', k)) and add a 1-px rim of colour on one side
    (rim = ('left'|'right', (r, g, b))).  Values are posterised to 4-step multiples so the tones stay flat."""
    out = rgba.copy()
    a = out[..., 3] > 0
    c = out[..., :3].astype(np.float32)
    c = c * np.asarray(mul, np.float32)[None, None] + np.asarray(lift, np.float32)[None, None]
    if side_fill is not None:
        side, k = side_fill
        h, w = a.shape
        xx = np.arange(w)[None, :].astype(np.float32) / max(1, w - 1)
        t = (1 - xx) if side == 'left' else xx
        f = 1.0 - k * np.clip((t - 0.45) / 0.55, 0, 1)
        f = np.round(f * 4) / 4
        c = c * f[..., None]
    c = np.clip(np.round(c / 4) * 4, 0, 255)
    out[..., :3] = np.where(a[..., None], c, 0).astype(np.uint8)
    if rim is not None:
        side, col = rim
        p = np.pad(a, 1)
        if side == 'left':
            edge = a & ~p[1:-1, :-2]
        else:
            edge = a & ~p[1:-1, 2:]
        top = a & ~p[:-2, 1:-1]
        e = (edge | top) & (np.arange(a.shape[0])[:, None] < a.shape[0] * 0.75)
        out[e, :3] = np.asarray(col, np.uint8)
    return out


def extend(rgba, down, shade_cols=None, buttons=True, open_front=True, spread=0.22):
    """Continue a bust's clothing below its cut: `down` more rows whose colours repeat the bottom row of the
    bust column by column (so the coat, the vest and the scarf run on), widening by `spread` px per row, with
    two fold shadows and, at the centre, the coat's opening and its buttons.  Returns the taller RGBA."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3] > 0
    rows = [r for r in range(h - 1, -1, -1) if a[r].any()]
    if not rows:
        return rgba
    last = rows[0]
    xs = np.nonzero(a[last])[0]
    x0, x1 = xs.min(), xs.max()
    out = np.zeros((h + down, w, 4), np.uint8)
    out[:h] = rgba
    src = rgba[last].copy()
    cx = (x0 + x1) / 2.0
    for k in range(1, down + (h - 1 - last) + 1):
        y = last + k
        if y >= h + down:
            break
        e0 = int(round(x0 - k * spread))
        e1 = int(round(x1 + k * spread))
        for x in range(max(0, e0), min(w, e1 + 1)):
            sx = int(np.clip(round(cx + (x - cx) * (x1 - x0) / max(1, e1 - e0)), x0, x1))
            c = src[sx].astype(np.float32)
            if c[3] == 0:
                c = src[int(np.clip(sx, x0 + 1, x1 - 1))].astype(np.float32)
            f = 1.0
            if x <= e0 + 1 or x >= e1 - 1:
                f = 0.45
            elif abs(x - (cx - (x1 - x0) * 0.28)) < 1.0 or abs(x - (cx + (x1 - x0) * 0.3)) < 1.0:
                f = 0.72
            if open_front and abs(x - cx) < 1.0:
                f = 0.5
            out[y, x, :3] = np.clip(c[:3] * f, 0, 255).astype(np.uint8)
            out[y, x, 3] = 255
        if buttons and open_front and k % 14 == 7:
            bx = int(round(cx)) + 3
            if 0 <= bx < w:
                out[y:y + 2, bx:bx + 2, :3] = (28, 26, 24)
                out[y:y + 2, bx:bx + 2, 3] = 255
    return out
