"""env_c4p2_cine -- art of the five Chapter-4-part-2 cinematics (owner: cine stream, round 10).

LS_C4P2_Depot, LS_C4P2_Steam, LS_C4P2_Book, LS_C4P2_Express, LS_C4P2_Clock (documentation/C4P2_DESIGN.md §2.9).
Every file written here is original, painted in code, deterministic (fixed seeds, no time or global random state)
and drawn at 1 texel = 1 px of the 640x360 world.  Run:

    py -3 -P tools/pixelgen/env_c4p2_cine.py [--only depot,steam,book,express,clock]

Modules: env_c4p2_cine_kit.py (the G-buffer painter of the wide plates, palette quantiser, textures, the game's
rig), env_c4p2_cine_flat.py (the flat pixel-art painter of the close and macro plates: flat ramps, stepped light,
outlines, flat cast shadows), env_c4p2_cine_hands.py (hands and sleeves on the game's sprite shader at full
resolution), env_c4p2_cine_busts.py (the cast's dialogue busts as film figures), env_c4p2_cine_loco.py (steam
engines side-on and head-on), env_c4p2_cine_people.py (rig figures placed, graded, on their contact shadows),
env_c4p2_cine_pal.py (the city palettes), env_c4p2_cine_places.py (structures seen in more than one film),
env_c4p2_cine_rig.py (poses and props on the rig), env_c4p2_cine_book3d.py (the guidebook as one 3-D model),
env_c4p2_cine_show.py (the depot showcase) and env_c4p2_cine_{depot,steam,book,express,clock}.py (one per film).
Output: assets/cinematics/c4p2/<film>/*.png and assets/cinematics/c4p2/layout.json (anchors shared with the
runtimes in scenes/cinematics/ch4p2_*/; tests/test_c4p2_cinematics.gd checks them).
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
import env_c4p2_cine_kit as K  # noqa: E402

PARTS = ('depot', 'steam', 'book', 'express', 'clock')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=','.join(PARTS))
    a = ap.parse_args(argv)
    parts = [s.strip() for s in a.only.split(',') if s.strip()]
    t0 = time.time()
    written = []

    def w(rel, img):
        K.save(img, rel)
        written.append(rel)

    prev = {}
    p = os.path.join(K.OUT, 'layout.json')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            prev = json.load(f)
    K.STANDINS.update(prev.get('standins', {}))
    for name in PARTS:
        if name in parts:
            for k in [k for k, v in K.STANDINS.items() if v and k.startswith(name + ':')]:
                K.STANDINS.pop(k, None)
            t1 = time.time()
            mod = importlib.import_module('env_c4p2_cine_' + name)
            mod.build(w)
            print('  %-8s %.1f s' % (name, time.time() - t1))
        elif name in prev:
            K.LAYOUT[name] = prev[name]
    K.write_layout()
    print('env_c4p2_cine: %s (%d files) in %.1f s -> %s' % (','.join(parts), len(written), time.time() - t0, K.OUT))


if __name__ == '__main__':
    main()
