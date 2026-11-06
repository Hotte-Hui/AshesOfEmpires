"""env_veltrava_cine_reflect -- the faces of Konrad and Alexei mirrored in the black train windows of LS_C3_Trains
(t1 / t3), round 10 (owner: the figures stream of this film family).

The round-7 reflections were traced heads without eyes, brows or mouth (a mask in the glass).  Here the faces come
from the dialogue-portrait pipeline itself (chargen_portrait2.render: sculpted head, hat, hair, the hand-designed
eye stamps, brows, mouth, stubble -- imported read-only), posed nearly frontal (he looks into the glass) and lit
from below by the table lamp / the tea glass, then turned into a reflection: luminance, a few dithered levels,
warm tint, mirrored, fading out below the chin (the caller fades the coat into the dark).

  face_reflection(who, tint, gain, levels) -> (RGB(A) uint8 additive image, (cx, cy) face centre in it)
Deterministic; ~7 s per face (memoised per process).
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

_memo: dict = {}
CROP = (18, 6, 94, 104)                   # x0, y0, x1, y1 of the 112 px bust: hat to collar
FACE = (56, 54)                           # the face centre in the bust (between the eyes / the nose)


def _bust(who):
    if who in _memo:
        return _memo[who]
    import chargen_portrait2 as CP2
    import chargen_portrait2_cast as CC
    spec = CC.konrad() if who == 'konrad' else CC.alexei()
    spec['id'] = who + '_reflection'
    if who == 'konrad':
        spec.update(yaw=8.0, pitch=-2.0, torso_yaw=6.0)
        spec['look'] = dict(key=(-0.35, 0.75, 0.55), rim=(0.6, -0.3, -0.5), ambient=0.06, wrap=0.12, bg='berlin',
                            glow=(0.8, 0.2), fill=0.05, fill_dir=(0.0, 0.0, 1.0), ao=0.5)
    else:
        spec.update(yaw=-10.0, pitch=-2.0, torso_yaw=-6.0)
        spec['look'] = dict(key=(0.55, 0.55, 0.62), rim=(-0.6, -0.3, -0.5), ambient=0.06, wrap=0.12, bg='karsk',
                            glow=(0.8, 0.2), fill=0.05, fill_dir=(0.0, 0.0, 1.0), ao=0.5)
    img = CP2.render(spec, 'neutral', 'rest')
    hit = CP2.gbuffer(spec, 'neutral', 'rest')['d'].hit
    _memo[who] = (img, hit)
    return img, hit


def face_reflection(who, tint, gain=1.25, levels=5, mirror=True):
    """Additive reflection image of who's face (cropped bust, mirrored) and the face centre inside it."""
    img, hit = _bust(who)
    lum = (img[..., 0] * 0.30 + img[..., 1] * 0.59 + img[..., 2] * 0.11) / 255.0
    lum = np.where(hit, lum, 0.0)
    x0, y0, x1, y1 = CROP
    v = lum[y0:y1, x0:x1]
    h, w = v.shape
    yy, xx = np.mgrid[0:h, 0:w]
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
    q = np.floor(np.clip(v * gain, 0, 1) * levels + bay[yy % 4, xx % 4]) / levels
    out = np.zeros((h, w, 4), np.uint8)
    for c in range(3):
        out[..., c] = np.clip(q * tint[c], 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    cx, cy = FACE[0] - x0, FACE[1] - y0
    if mirror:
        out = out[:, ::-1].copy()
        cx = w - 1 - cx
    return out, (cx, cy)
