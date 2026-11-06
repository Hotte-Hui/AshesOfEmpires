"""env_c4_cine -- art of the five Chapter-4 cinematics (owner: cine stream, round 9).

LS_C4_Homeward, LS_C4_Number, LS_C4_Card, LS_C4_Stamp, LS_C4_Voices (documentation/C4_DESIGN.md §2.9).  Every
file written here is original, painted in code, deterministic (fixed seeds, no time or global random state) and
drawn at 1 texel = 1 px of the 640x360 world.  Run:

    py -3 -P tools/pixelgen/env_c4_cine.py [--only homeward,number,card,stamp,voices]

Modules: env_c4_cine_kit.py (palettes, io, the shared objects of the match cuts: stencil letters, the torn
perforation of card No. 0417, the rubber stamps; the game's character sheets re-lit per shot),
env_c4_cine_places.py (places seen in more than one film: the Karsk freight yard, the Berlin tram loop, the
siding hall, the tram), env_c4_cine_{homeward,number,card,stamp,voices}.py (one per film) and
env_c4_cine_figs.py (hands and the two men from behind through the portrait pipeline).
Output: assets/cinematics/c4/{homeward,number,card,stamp,voices,places}/*.png and assets/cinematics/c4/layout.json
(anchors shared with the runtimes in scenes/cinematics/ch4_*/; tests/test_c4_cinematics.gd checks them).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_c4_cine_kit as Q  # noqa: E402

PARTS = ('places', 'homeward', 'number', 'card', 'stamp', 'voices')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=','.join(PARTS))
    a = ap.parse_args(argv)
    parts = [s.strip() for s in a.only.split(',') if s.strip()]
    t0 = time.time()
    written = []

    def w(rel, img):
        Q.save(img, rel)
        written.append(rel)

    # a partial run keeps the other parts' layout entries (and stand-ins) from the previous layout.json
    prev = {}
    p = os.path.join(Q.OUT, 'layout.json')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            prev = json.load(f)
    Q.STANDINS.update(prev.get('standins', {}))
    for name in PARTS:
        if name in parts:
            mod = importlib.import_module('env_c4_cine_' + name)
            mod.build(w)
        elif name in prev:
            Q.LAYOUT[name] = prev[name]
    Q.write_layout()
    print('env_c4_cine: %s (%d files) in %.1f s -> %s' % (','.join(parts), len(written), time.time() - t0, Q.OUT))


if __name__ == '__main__':
    main()
