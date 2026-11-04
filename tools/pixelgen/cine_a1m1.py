"""cine_a1m1 -- builds every asset of the A1 -> M1 transition cinematic and writes layout.json.

    py -3 -P tools/pixelgen/cine_a1m1.py            (all art, deterministic)
    py -3 -P tools/audiogen/cine_a1m1_sfx.py        (sound effects)

layout.json carries the geometry the scene script (scripts/cinematics/a1m1/cin_a1_to_m1.gd) needs: sprite
anchors inside the generated images (chimney, whistle, cab window, glyph, imprint, pencil, door ...), so
art and code can never drift apart.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_a1m1_lib as lib  # noqa: E402
import cine_a1m1_karsk as karsk  # noqa: E402
import cine_a1m1_close as close  # noqa: E402
import cine_a1m1_berlin as berlin  # noqa: E402


def main():
    info = {'karsk': karsk.build(), 'close': close.build(), 'berlin': berlin.build()}
    layout = {
        'karsk': {
            'yard': [karsk.YARD_X0, karsk.YARD_Y0], 'rail_y': karsk.RAIL_Y, 'platform_y': karsk.PLATFORM_Y,
            'loco_size': [karsk.LOCO_W, karsk.LOCO_H], 'wheel_r': karsk.WHEEL_R, 'drivers': karsk.DRIVERS,
            'chimney': list(karsk.CHIMNEY), 'whistle': list(karsk.WHISTLE), 'cyl_steam': list(karsk.CYL_STEAM),
            'cab_window': list(karsk.CAB_WINDOW), 'headlamp': [16, 22],
        },
        'close': {
            'glyph': info['close']['glyph_centre'], 'imprint': info['close']['imprint']['pos'],
            'pencil': info['close']['pencil']['pos'], 'stamp_anchor': info['close']['stamp']['anchor'],
            'initials': [46, 152],
        },
        'berlin': info['berlin']['geometry'],
        'frames': {k: v.get('frames', 1) for part in info.values() for k, v in part.items()
                   if isinstance(v, dict) and 'frames' in v},
    }
    lib.write_json('layout.json', layout)
    print(json.dumps(layout, indent=1))


if __name__ == '__main__':
    main()
