"""chargen_portrait -- compatibility entry point for the dialogue portraits.

The first-generation ellipsoid bust generator that lived here was replaced on 2026-11-04 by the second
generation pipeline in chargen_portrait2.py (+ _sdf / _anat / _paint / _face / _cast modules): signed-distance
sculpted busts, hand-designed eye / brow / mouth features, talking-mouth and blink frames, nine speakers.
The old implementation is in the git history.

tools/pixelgen/characters.py still calls `chargen_portrait.main(ids)` for every id in `PORTRAITS`; this
module forwards to the new generator so a full character rebuild never resurrects the old portraits.
Speakers whose portrait files are newer than every generator module are skipped (pass --force to rebuild).
"""
from __future__ import annotations

import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import chargen_portrait2 as _gen   # noqa: E402

PORTRAITS = list(_gen.PORTRAITS)


def _up_to_date(cid: str) -> bool:
    d = os.path.join(_gen.CHAR_DIR, cid)
    outs = [os.path.join(d, n) for n in ('portrait.png', 'portrait_anim.png', 'portrait.json')]
    if not all(os.path.exists(p) for p in outs):
        return False
    newest_src = max(os.path.getmtime(p) for p in glob.glob(os.path.join(HERE, 'chargen_portrait2*.py')))
    return min(os.path.getmtime(p) for p in outs) >= newest_src


def main(ids=None, force=False):
    ids = [c for c in (ids or PORTRAITS) if c in PORTRAITS]
    todo = [c for c in ids if force or not _up_to_date(c)]
    for c in ids:
        if c not in todo:
            print(f'{c:10s} portrait up to date (chargen_portrait2)')
    if todo:
        _gen.main(todo)


if __name__ == '__main__':
    args = sys.argv[1:]
    main([a for a in args if not a.startswith('--')] or None, force='--force' in args)
