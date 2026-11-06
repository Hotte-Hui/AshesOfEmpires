# Asset manifest part — Chapter 4 part 2, puzzle UIs „Die Hälften“ and „Haus 14“ (puzzle UI stream, round 10)

Date for all entries: **2026-11-06** (revised the same day after the art director's review: card lettering, the
house's figures, stairs, cellars, workshop and back house, the cap mark, the ring; see „Review fixes“ below).
Everything below is original work for this project, produced by a deterministic generator in this repository or
written by hand; no downloaded images, fonts or sounds, no AI image services, no tracing of references. Licence:
project-owned, same as the game. Contract: `documentation/C4P2_DESIGN.md` §2.5 (document descriptions), §2.7 (puzzle
contracts), §4 (the courtyard of L_C4P2_BerlinB), §5 (cast looks), §10 (ownership).

## Puzzle art — `tools/pixelgen/gen_ui_c4p2.py` (`py -3 -P tools/pixelgen/gen_ui_c4p2.py [--preview=DIR]`)
Drawn 1:1, shown at x3 with nearest filtering. Words the player must read are set in HD by the UI from Loc keys; the
painted characters are document type (the card, the book page, the box label, the shop sign) in the 3×5 / 5×7 bitmap
types of `tools/pixelgen/env_veltrava_hall_kit.py` (imported read-only) with the distinct Ä / Ö / Ü of
`tools/pixelgen/pixfont_umlauts.py` (round 9, imported read-only: the dots one row above the cap line, never touching
the letter) plus glyphs added in the generator (Щ, №, *, –, Ø, a distinct Å and Ё in the same manner, a rounded 8 that
cannot be read as B, a flat-roofed Д with feet that cannot be read as А, a Л with its left leg kicked out that cannot be
read as П, the digits 0 / 4 / 7 of the 5×7 type). Palette: the UI / archive ramps (paper, ink, red, amber) plus wood,
sand, brass, steel, stamp violet, night sky, three courtyard plasters, sooted brick, lamp and sodium light. Fixed seeds,
identical output on every run. The generator verifies the puzzle data against `data/v3/puzzles.json` and the contract
before writing (see the two `*_check` blocks of the layout files).

| Path | Kind | How it was made |
|---|---|---|
| `assets/ui/documents/karsk_c4p2_halves_de.png`, `karsk_c4p2_halves_ru.png` | card No. 0417 as two halves: the German half (left, five teeth, the red C-17 tab, the left half of the round stamp in German letters), stored upside down as Konrad laid it into the guidebook; the Russian half (right, five notches, the right half of the stamp in Cyrillic, the rectangular red „ПРИНЯТЬ“ top right with two clear pixels round its letters, the number №0417 at the foot). No tooth comes near the stamp's centre, so the joined stamp reads „C-17“ | procedural: the WHOLE card is painted once (paper, ruled form, typed lines, perforation, the violet round stamp „C-17“ across the cut) and then cut along the toothed edge, so the halves fit by construction |
| `assets/ui/puzzle/c4p2_halves_table.png` | the table of the sand house in the Karsk depot under a hanging lamp: the open Swedish guidebook (pages 212/213, original design, no publisher's name), Konrad's tracing of the Kordon room with the bench for fourteen, Lev's card box „С-17/45 ПРИНЯТЬ“ with the empty slot, a pocket watch at 19.05, a generic 1950s rangefinder camera (no maker's name), a tin mug, a sieve and drying sand | procedural planks (one cell high), grain and nails; props drawn with primitives; banded, dithered lamp light |
| `assets/ui/puzzle/c4p2_halves_snap.png`, `c4p2_halves_ring.png`, `c4p2_halves_click.png` | amber corner brackets (a tooth in its notch), the pale violet ring of the closed stamp, the spark of a tooth clicking in | procedural |
| `assets/ui/puzzle/c4p2_halves_legend_teeth.png`, `…_legend_stamp.png`, `…_legend_lines.png` | legend drawings: tooth and notch, a stamp half, ruled lines with their ticks at the cut | procedural |
| `assets/ui/documents/karsk_c4p2_halves.json` | cell size, files, board (with the paper's margin to the table's edge), mark positions and inward normals of both sheets, start pose, the offset range of every turn (the whole half stays on the table), legend files, measured surface colours (no answer; the generator verifies that only half a turn lets the marks face each other, that exactly one pose joins all five teeth and the stamp — the solution of `pz_c4_halves` — that no other pose joins even one tooth, and that the start, the solution and every pose of the input driver lie inside the ranges) | written by the generator |
| `assets/ui/puzzle/c4p2_house_board.png`, `c4p2_house_night.png` | Kolonnenstraße 14 seen from the courtyard, Tuesday night, in the plasters of the courtyard level L_C4P2_BerlinB: Vorderhaus (ochre-grey plaster, keystones, rusticated ground floor, the gate passage with Kuhnert in his cap under the vault lamp), Seitenflügel (sooty plaster, a patch of fallen plaster, the lodge with Frau Kuhnert and the card box on the sill), Hinterhaus (cool grey plaster with two spalled patches; one long roof; it goes on right of its stairwell over the cobbler's souterrain, whose board „SCHUHMACHEREI / PIETSCH“ hangs over the souterrain windows as in the courtyard); stairwells cut open (oil-paint dado, a dog-leg stair per storey — the far flight, the half landing, the near flight with its handrail —, landings, tall flat doors — Pohl's spy hole, the paper seal of No. 3 —, the steep cellar stairs under the ground landings); drying lofts with frozen laundry, baskets and a trunk, a junk loft; cellars with numbered, padlocked coal partitions, a bicycle, a sled and potato sacks, preserving jars and an old pram, the corridor doors and Pietsch's door ajar; Pietsch's workshop (shelves of lasts and of shoes waiting with their tags, the tool rack and the hanging lamp, the bench with a boot on the last, nails, glue and a candle stub, the arm sewing machine, his stool, his apron on a nail, the stove, a crate of shoes — the same in every light); the dome of the Great Hall far away in the haze; chimneys, 1964 television aerials, dustbins, snow; 27 windows each with an interior (who is awake at 22.40: Pohl's window dim behind its curtain, as in the courtyard). Two renderings: the overview and the 22.40 lights. Herr Pietsch himself is not shown (C4P2 §5) | procedural: dithered plaster / brick / stone fields, primitives, role-painted interiors (one drawing, three lights: neutral / lit / dark; Pohl's dim window mixes lit and dark) |
| `assets/ui/puzzle/c4p2_house_anim.png` | two frames each for five lit windows: Lenz turns a page, Herr Schulz rocks the baby, Pohl's curtain opens on a face (dim), Frau Kuhnert turns her head, Herr Kühn slaps a card down | procedural, same window painter |
| `assets/ui/puzzle/c4p2_house_konrad.png`, `c4p2_house_ilse.png` | the two walking figures, five frames each (standing, a four-frame walk), facing right: Konrad (21 px) in his grey fedora with the brim snapped down, his face under it (ear, eye, nose), dark-blue civilian overcoat, ochre wool scarf, the drafting tube on his back, dark trousers; Ilse (15 px) in her dark-blue knitted cap with a short peak, a light-brown plait, her face, the pale grey wool coat, the brown satchel she never lets go of, grey wool stockings. Three tones per material, lit from the upper left, a dark outline for the board (looks follow the cast sheets `konrad` / `berlin_child`) | hand-placed pixel rows in the generator |
| `assets/ui/puzzle/c4p2_house_eye.png`, `c4p2_house_lamp.png`, `c4p2_house_hat.png`, `c4p2_house_stop.png` | shape-coded marks: the spy-hole eye (Pohl), the table lamp (the lodge window), the Blockleiter's peaked cap in side view — a wide flat crown, the piping, the narrow band, the peak jutting forward (the passage; id `hat` per the contract) —, the stop sign (a light bar on a red disc) | procedural |
| `assets/ui/puzzle/c4p2_house_circle.png`, `c4p2_house_ws_lit.png` | Konrad's red pencil ring around the workshop (on the board, under the shop board); the workshop with the candle lit (success; the same objects as by day and by night) | procedural |
| `assets/ui/puzzle/c4p2_house.json` | board files and size, rows, wings, the 19 rooms (wing, floor, grid cell, rect and the back house's parts right of its stairs, route node, the figures' place on the floor and Konrad's place beside Ilse at the start, label position, kind, windows), the contract's passages and for each the way the figures walk (feet points along the floor or the flights), unsafe rooms with their watcher marks, households, the rooms awake / dim at 22.40, window animations, the figures' frames and feet, the ring's centre (the generator verifies that the only simple path from `s3` to `ws` avoiding the watchers is the solution of `pz_c4_house`, that every room has at most one passage per arrow, the input driver's key sequence, that every place is on its floor with room above Konrad's hat and that every way runs level or along a flight) | written by the generator |

## UI, texts, tests
| Path | Kind | How it was made |
|---|---|---|
| `scenes/ui/JoinPuzzle.tscn`, `scripts/ui/join_puzzle.gd` | join modal on the sand-house table (arrows / WASD / R / Shift+R / Backspace / Enter / Esc, pad D-pad RB LB A X Y Back, mouse drag with snap, wheel / right-click turn; the half is clamped per turn so it never leaves the table; teeth in notches get brackets; the German half's shadow falls on the table while the halves lie side by side; success: the teeth click in, the stamp closes, two soft photo flashes; the success card takes the instruction's place at every text size) | hand-written, key contract of `scripts/ui/route_puzzle.gd` |
| `scenes/ui/HousePuzzle.tscn`, `scripts/ui/house_puzzle.gd` | house modal (arrows / WASD walk the route, Backspace / R / K / L / Enter / Esc, pad D-pad A Y B X LB RB Back, mouse click / drag / right-click / hover; side panel with the room's nameplate, Kuhnert's card, the window at 22.40 and the passages; the figures stand on the floors — Ilse at the head of the route with a ring on the floor at her feet, Konrad a step behind her — and walk the stairs on the Probegang; the stop mark beside Ilse, clear of both figures, the marks and the writing; Kuhnert's cards in two fixed sizes, long notes wrap, a watched card carries its mark at its edge; success: candle, red ring) | hand-written |
| `data/locale/de_c4p2_puzzles.json` (the `ui.c4p2.halves.*` / `ui.c4p2.house.*` keys the contract leaves to the UI: states, counts, sideways note, tips, controls, buttons, stamps, the room nameplates, card tags, windows at 22.40, floors, legends) | German texts | hand-written |
| `tests/test_c4p2_puzzle_ui.gd`, `tests/visual/c4p2_puzzle_shots.gd` + `C4P2PuzzleShots.tscn` | unit tests (32 cases) and the screenshot harness of every state (incl. the half at the table's edge in every turn, the solved states at 100 / 125 / 150 %, the stop at the lodge, the cards at 125 %, the way into the back cellar) | hand-written |

## Review fixes (art director, round 10)
* The solved „Die Hälften“ fits the 1080-px screen at 100 % (the success card replaces the instruction; tests check
  every state at 100 / 125 / 150 % and in high contrast).
* Card lettering: distinct umlauts (round-9 glyphs), a rounded 8, Д and Л that read as themselves, „ПРИНЯТЬ“ in a frame
  with clear pixels, away from „КАРСК“ and the header.
* The figures: shaded, with faces, five frames; they stand on floors and walk the flights (never in a slab, never
  floating), the stop mark never covers them, the head of the route is a ring on the floor.
* Kuhnert's cards: one size per line kind, wrapping instead of shrinking; the watcher marks hang at the card's edge,
  never over its writing.
* The red ring stays on the board; the shop name hangs on the courtyard board where nothing covers it; the half stays on
  the table at every offset; the closed stamp reads „C-17“; the workshop is furnished in every light; the cap reads as a
  cap; the back house and Pohl's dim window match the courtyard level.

Sound cues used (existing files of the audio stream, with fallbacks; nothing new recorded): `tick`, `move`, `back`,
`snap`, `page`, `fail`, `paper`, `step_wood`, `mg_c3p2_card_file`, `mg_relay_click`, `c4cine_stamp_ru` / `stamp_thud`,
`plaza_shutter`, `door_open`, `cine_finale_pencil`; optional ids `c4p2_steps`, `c4p2_stamp_close`, `c4p2_shutter`,
`c4p2_door`, `c4p2_pencil`, `ui_knock` are picked up first if the audio stream adds them.

World note: a fictional two-part registry card laid against its other half (not a real form); a fictional depot; a
fictional Berlin tenement, its fictional households and a fictional card file — no real persons.
