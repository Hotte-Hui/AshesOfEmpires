"""pixfont_umlauts -- distinct Ä / Ö / Ü for the small pixel capitals of the close-ups and the small UI art
(round 9, feel pass 2; owner feel_r9).

The 3x5 and 5x7 capitals of the generators (explore_berlin F35 / F57 for every Berlin and plaza close-up,
gen_ui_c3 for the protocol documents, mg_r7_kb_lib for the Rohrpost board, the departures board of LS_C3_Halves)
drew the two dots INSIDE the letter cell: on a 3-px letter they continue the strokes, so at 1x „FÜR“ read „FUR“,
„ENTFÄLLT“ read „ENTFALLT“.  Here every umlaut uses ONE row above the cap line for the dots, then a blank row, then
the letter one row shorter -- the dots never touch the letter and the letter keeps its shape:

    3x5 (6 rows, row 0 above the cap line)      5x7 (8 rows)
    #.#   #.#   #.#                              .#.#.   .#.#.   .#.#.
    ...   ...   ...                              .....   .....   .....
    .#.   .#.   #.#                              .###.   .###.   #...#
    #.#   #.#   #.#                              #...#   #...#   #...#
    ###   #.#   #.#                              #...#   #...#   #...#
    #.#   .#.   ###                              #####   #...#   #...#
                                                 #...#   #...#   #...#
                                                 #...#   .###.   .###.

Renderers that use these glyphs draw a glyph taller than the font height `extra = len(g) - height` rows ABOVE the
given cap line (overhang); masks grow by that many rows at the top.  Deterministic, no image inputs.

    py -3 -P tools/pixelgen/pixfont_umlauts.py --preview=DIR   # DIR/umlauts_contact.png: old vs new at 1x / 2x / 3x
"""
from __future__ import annotations

import os
import sys

UML_35 = {
    'Ä': ['#.#', '...', '.#.', '#.#', '###', '#.#'],
    'Ö': ['#.#', '...', '.#.', '#.#', '#.#', '.#.'],
    'Ü': ['#.#', '...', '#.#', '#.#', '#.#', '###'],
}
UML_57 = {
    'Ä': ['.#.#.', '.....', '.###.', '#...#', '#...#', '#####', '#...#', '#...#'],
    'Ö': ['.#.#.', '.....', '.###.', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Ü': ['.#.#.', '.....', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
}


def install(font: dict, height: int) -> dict:
    """Puts the distinct umlauts into a glyph table of the given cap height (5 or 7); returns the table."""
    src = UML_35 if height == 5 else UML_57
    for k, g in src.items():
        font[k] = list(g)
    return font


def overhang(font: dict, s: str, height: int) -> int:
    """Rows a string reaches above the cap line in this font (0 when it has no tall glyph)."""
    extra = 0
    for ch in s.upper():
        g = font.get(ch)
        if g is not None and len(g) > height:
            extra = max(extra, len(g) - height)
    return extra


def _preview(path):
    import numpy as np
    from PIL import Image
    old_35 = {'Ä': ['#.#', '.#.', '#.#', '###', '#.#'], 'Ö': ['#.#', '...', '###', '#.#', '###'],
              'Ü': ['#.#', '...', '#.#', '#.#', '###']}
    base_35 = {'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
               'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
               'R': ['##.', '#.#', '##.', '##.', '#.#'], 'S': ['.##', '#..', '.#.', '..#', '##.'],
               'D': ['##.', '#.#', '#.#', '#.#', '##.'], ' ': ['...'] * 5}

    def strip(word, table):
        rows = 7
        cols = sum(len(table.get(c, base_35.get(c, ['...']))[0]) + 1 for c in word)
        m = np.zeros((rows, cols), bool)
        x = 0
        for c in word:
            g = table.get(c) or base_35.get(c) or ['...'] * 5
            top = 1 - (len(g) - 5)
            for yy, row in enumerate(g):
                for xx, v in enumerate(row):
                    if v == '#':
                        m[top + yy, x + xx] = True
            x += len(g[0]) + 1
        return m

    words = ['FÜR', 'SÜD', 'FÄDS', 'RÖSA', 'AOU ÄÖÜ']
    tiles = []
    for tab in (old_35, UML_35):
        for w in words:
            tiles.append(strip(w, tab))
    k_list = (1, 2, 3)
    cw = max(t.shape[1] for t in tiles) * 3 + 6
    img = Image.new('RGB', (cw * 3 * 2, (7 * 3 + 6) * len(words)), (230, 222, 200))
    for i, t in enumerate(tiles):
        for j, k in enumerate(k_list):
            a = np.repeat(np.repeat(t, k, 0), k, 1)
            rgb = np.where(a[..., None], np.array([40, 34, 30], np.uint8), np.array([230, 222, 200], np.uint8))
            im = Image.fromarray(rgb.astype(np.uint8))
            col = (i // len(words)) * 3 + j
            img.paste(im, (col * cw + 3, (i % len(words)) * (7 * 3 + 6) + 3))
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(path)


if __name__ == '__main__':
    prev = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--preview=')), '')
    if prev:
        os.makedirs(prev, exist_ok=True)
        _preview(os.path.join(prev, 'umlauts_contact.png'))
        print('pixfont_umlauts: preview ->', os.path.join(prev, 'umlauts_contact.png'))
