"""env_c4p2_cine_people -- figures of the game's rig placed in the Chapter-4-part-2 plates (owner: cine stream).

The wide shots use the in-game rig (chargen_body + the cast specs), so a person in a film is the person of the level:
  sheet()      render a cast member in a set of poses (props from env_c4p2_cine_rig hooks), the rig's baked key
               turned toward the shot's main light, optionally mirrored, graded by the light at the figure's place
               (a posterised colour multiply that keeps the rig's tone steps), with a one-pixel rim of the light's
               colour on the lit side of the silhouette
  shadow()     the flat contact shadow under a figure's feet (painted into the plate)
  place()      bookkeeping of where a sheet stands (top-left, frame count, cell width) for the runtime's layout
Deterministic.
"""
from __future__ import annotations

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K
import env_c4p2_cine_rig as R


def _grade(rg, mul, rim=None, rim_side=1, lift=(0, 0, 0)):
    out = rg.copy()
    a = out[..., 3] > 0
    c = out[..., :3].astype(np.float32) * np.asarray(mul, np.float32)[None, None] + np.asarray(lift, np.float32)
    c = np.clip(np.round(c / 3) * 3, 0, 255)
    out[..., :3] = np.where(a[..., None], c, 0).astype(np.uint8)
    if rim is not None:
        p = np.pad(a, 1)
        side = a & ~(p[1:-1, 2:] if rim_side > 0 else p[1:-1, :-2])
        top = a & ~p[:-2, 1:-1]
        rows = np.arange(a.shape[0])[:, None] < a.shape[0] - 8
        e = (side | top) & rows
        out[e, :3] = (out[e, :3].astype(np.float32) * 0.35 + np.asarray(rim, np.float32) * 0.65).astype(np.uint8)
    return out


def sheet(cid, poses, setup=None, width=32, flip=False, key='left', mul=(1.0, 1.0, 1.0), rim=None, standin='worker_b',
          strip=True, recolor=None, view='side', lift=(0, 0, 0)):
    """(sheet rgba, n frames, cell width) of `cid` on the rig.  key: the side of the baked key light in the
    final picture (after any mirroring); rim: (r, g, b) or None, laid on the key side."""
    spec, used = K.spec_of(cid, standin)
    if strip:
        R.strip_props(spec)
    for name, col in (recolor or {}).items():
        K.recolor(spec, name, col)
    side = key
    if flip:
        side = 'right' if key == 'left' else 'left'
    K.key_light(spec, side, up=0.65, front=0.5)
    hooks = setup(spec) if callable(setup) else list(setup or [])
    frames = K.rig_frames(spec, poses, view, width, hooks)
    if flip:
        frames = R.flip_frames(frames)
    cells = [_grade(rg, mul, rim, 1 if key == 'right' else -1, lift) for rg, nm, J in frames]
    return K.hsheet(cells), len(cells), width


def idle(cid, flip=False, n=None, **kw):
    CH, CB, A, CC = K.rig()
    spec, used = K.spec_of(cid, kw.get('standin', 'worker_b'))
    poses = A.idle_side(spec.style)
    if n:
        poses = poses[:n]
    return sheet(cid, poses, [], 32, flip, **kw)


def shadow(F, x, base, w=11, h=2.5, k=0.55, under=None):
    """A flat contact shadow (an ellipse darkening the ground) under a figure standing at x with its feet on
    `base` (the sole row)."""
    m = F.ell(x, base + 0.5, w, h)
    if under is not None:
        m &= under
    F.mul(m, k)
    F.mul(m & F.ell(x, base + 0.5, w * 0.55, h * 0.6), 0.85)
    return m


def cell_xy(x, base, width=32, sole=54):
    """Top-left of a rig cell whose figure stands at x (pelvis column) with its soles on `base`."""
    return int(round(x - width / 2.0)), int(round(base - sole))
