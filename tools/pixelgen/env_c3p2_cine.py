"""env_c3p2_cine -- art of the four Chapter-3 part-2 cinematics (owner: cinematics stream, round 8).

LS_C3_Radio, LS_C3_Fire, LS_C3_Escape, LS_C3_Halves (documentation/C3P2_DESIGN.md §2.9).  Every file written here
is original, painted in code, deterministic (fixed seeds, no time or global random state) and drawn at 1 texel =
1 px of the 640x360 world.  Run:

    py -3 -P tools/pixelgen/env_c3p2_cine.py [--only radio,fire,escape,halves]

Modules: env_c3p2_cine_kit.py (ramps, io, re-quantiser, glows, flame/smoke sheets, hand lettering),
env_c3p2_cine_radio.py, env_c3p2_cine_fire.py (fire + escape), env_c3p2_cine_quay.py (halves),
env_c3p2_cine_figs.py (the protagonists through the portrait pipeline).
Output: assets/cinematics/c3p2/{radio,fire,escape,halves}/*.png and assets/cinematics/c3p2/layout.json (anchors
shared with the runtimes in scenes/cinematics/ch3_{radio,fire,escape,halves}/; tests/test_c3p2_cinematics.gd
checks them against the scripts' constants).
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_c3p2_cine_kit as Q  # noqa: E402

PARTS = ('radio', 'fire', 'escape', 'halves')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=','.join(PARTS))
    ap.add_argument('--layout-only', action='store_true')
    ap.add_argument('--fx-only', action='store_true',
                    help='only the fire / escape sheets made with the pixel fire kit (env_c3p2_cine_fire.build_fx)')
    a = ap.parse_args(argv)
    parts = [s.strip() for s in a.only.split(',') if s.strip()]
    t0 = time.time()
    written = []

    def w(rel, img):
        Q.save(img, rel)
        written.append(rel)

    import importlib
    import json
    # a partial run keeps the other parts' layout entries from the previous layout.json
    prev = {}
    p = os.path.join(Q.OUT, 'layout.json')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            prev = json.load(f)
    mods = {'radio': ('env_c3p2_cine_radio', 'build'), 'fire': ('env_c3p2_cine_fire', 'build_fire'),
            'escape': ('env_c3p2_cine_fire', 'build_escape'), 'halves': ('env_c3p2_cine_quay', 'build')}
    if a.fx_only:
        Q.LAYOUT.update(prev)
        fire = importlib.import_module('env_c3p2_cine_fire')
        fire.LF, fire.LE = Q.LAYOUT['fire'], Q.LAYOUT['escape']
        fire.build_fx(w)
        fire._preview_fire()
        fire._preview_escape()
        Q.LAYOUT['fire'].pop('f4_kinds', None)
        parts = ['fx']
    for name in PARTS:
        if a.fx_only:
            break
        if name in parts and not a.layout_only:
            mod = importlib.import_module(mods[name][0])
            getattr(mod, mods[name][1])(w)
        elif name in prev:
            Q.LAYOUT[name] = prev[name]
    Q.write_layout()
    print('env_c3p2_cine: %s (%d files) in %.1f s -> %s' % (','.join(parts), len(written), time.time() - t0, Q.OUT))


if __name__ == '__main__':
    main()
