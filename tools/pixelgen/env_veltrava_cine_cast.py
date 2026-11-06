"""env_veltrava_cine_cast -- who stands where in LS_C3_Trains (round 10; the extras of LS_C3_ToHall and
LS_C3_Close are cast by the figures stream itself: env_veltrava_cine_people.EXTRAS / c3_people.gd).

Owner: cinematics stream (places and motion).  The people themselves are the figures stream's: every sheet comes
from env_veltrava_cine_people.person_sheet() (full bodies with articulated arms and legs, painted by the portrait
pipeline) -- this module only decides the cast of each shot (kind, height in px, pose, facing, light, place and
walking speed), writes the sheets next to the film's other art and records them in layout.json, which the scene
scripts read (`people` lists, drawn on their parallax plane).  If the people module is missing or a kind fails,
that extra is left out (no placeholders).
"""
from __future__ import annotations

import os

import numpy as np

import env_veltrava_cine as C

LAYOUT = C.LAYOUT


def person(kind, height, frames=8, pose='walk', facing=1, light='dawn', seed=0, **opts):
    """RGBA sheet from the figures stream, or None (logged) when it cannot be made."""
    try:
        import env_veltrava_cine_people as P
    except ImportError:
        return None
    try:
        return P.person_sheet(kind, height, frames=frames, pose=pose, facing=facing, light=light, seed=seed, **opts)
    except Exception as e:                                                    # noqa: BLE001
        print('env_veltrava_cine_cast: %s (%s px) left out: %s' % (kind, height, e))
        return None


def stamp(rgba, sheet, frames, frame, x, sole):
    """Alpha-composite one frame of a person sheet into an RGBA image: frame centre at x, soles on row `sole`."""
    if sheet is None:
        return
    fw = sheet.shape[1] // frames
    fh = sheet.shape[0]
    fr = sheet[:, frame * fw:(frame + 1) * fw]
    x0 = int(round(x - fw / 2))
    y0 = int(sole - fh + 1)
    H, W = rgba.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + fw), min(H, y0 + fh)
    if X1 <= X0 or Y1 <= Y0:
        return
    src = fr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    m = src[..., 3] > 0
    dst = rgba[Y0:Y1, X0:X1]
    dst[m] = src[m]


# name, kind, height, frames, pose, facing, light, seed, plane, x (centre), sole row, vx (px/s), fps, t0
CAST = {
    'trains': [
        # t4 dawn: the woman with the milk sled on the bank path, two ice fishers at their hole, people on the quay,
        # a street sweeper at the lamp of the promenade
        ('d4_sled', 'woman_sled', 24, 8, 'walk', 1, 'dawn', 0, 'bank', 112, 521, 8.0, 7.0, 22.4),
        ('d4_sweeper', 'sweeper', 22, 4, 'stand', -1, 'dawn', 1, 'bank', 438, 520, 0.0, 1.6, 22.4),
        ('d4_fisher1', 'fisher', 18, 4, 'sit', 1, 'dawn', 2, 'bridge', 58, 393, 0.0, 1.4, 22.4),
        ('d4_fisher2', 'fisher', 17, 4, 'sit', -1, 'dawn', 3, 'bridge', 96, 395, 0.0, 1.1, 22.4),
        ('d4_quay1', 'man_coat', 12, 8, 'walk', -1, 'dawn', 4, 'city', 470, 250, -7.0, 8.0, 22.4),
        ('d4_quay2', 'woman_coat', 11, 8, 'walk', 1, 'dawn', 5, 'city', 150, 250, 6.0, 8.0, 22.4),
        ('d4_quay3', 'porter', 12, 8, 'walk', 1, 'dawn', 6, 'city', 262, 250, 5.0, 7.0, 22.4),
        ('d4_quay4', 'man_cap', 12, 8, 'walk', -1, 'dawn', 7, 'city', 596, 250, -5.5, 7.0, 22.4),
    ],
}


def build(part, layout_part):
    """Write assets/cinematics/ch3/<part>/pp_<name>.png for the cast of `part`; layout_part['people'] = list."""
    out = []
    for (name, kind, h, frames, pose, facing, light, seed, plane, x, sole, vx, fps, t0) in CAST.get(part, []):
        sh = person(kind, h, frames=frames, pose=pose, facing=facing, light=light, seed=seed)
        if sh is None:
            continue
        rel = '%s/pp_%s.png' % (part, name)
        C.save(sh, rel)
        fw = sh.shape[1] // frames
        out.append({'name': name, 'tex': rel, 'frames': frames, 'w': fw, 'h': int(sh.shape[0]), 'plane': plane,
                    'x': float(x - fw / 2), 'y': float(sole - sh.shape[0] + 1), 'vx': vx, 'fps': fps, 't0': t0})
    layout_part['people'] = out
    return out


def clean(part):
    """Remove pp_*.png sheets of `part` that are no longer in the cast (and their .import files)."""
    names = {'pp_%s.png' % c[0] for c in CAST.get(part, [])}
    d = os.path.join(C.OUT, part)
    if not os.path.isdir(d):
        return
    for f in os.listdir(d):
        if f.startswith('pp_') and f.endswith('.png') and f not in names:
            for g in (f, f + '.import'):
                try:
                    os.remove(os.path.join(d, g))
                except OSError:
                    pass
