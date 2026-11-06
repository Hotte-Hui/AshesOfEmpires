# Asset manifest part — Chapter 4 part 1, puzzle UIs „Die Nummernkette“ and „Linie 74“ (puzzle UI stream, round 9)

Date for all entries: **2026-11-06**. Everything below is original work for this project, produced by a deterministic
generator in this repository or written by hand; no downloaded images, fonts or sounds, no AI image services, no tracing
of references. Licence: project-owned, same as the game. Contract: `documentation/C4_DESIGN.md` §2.5 (document
descriptions), §2.7 (puzzle contracts), §10.

## Puzzle art — `tools/pixelgen/gen_ui_c4.py` (`py -3 -P tools/pixelgen/gen_ui_c4.py [--preview=DIR]`)
Drawn 1:1, shown at x3 with nearest filtering (every digit stroke ≥ 3 screen px). Words are set in HD by the UI from Loc
keys; the only painted characters are the wagon numbers and Marta's pencil dates, in two pixel types designed in the
generator (plate type 7×11 with stencil bridges / brush jitter, mini type 3×5). Palette: the UI / archive ramps (paper,
ink, red, wall, amber) plus wood, rust-brown („die Farbe aller Güterwagen“), enamel blue, iron and chalk. Fixed seeds,
identical output on every run. The generator verifies the puzzle data against `data/v3/puzzles.json` before writing.

| Path | Kind | How it was made |
|---|---|---|
| `assets/ui/puzzle/c4_numbers_board.png` | slate in the siding hut: Service Tunnel 3 in chalk (freight yard fan, four switch posts with iron hooks, dashed tunnel walls, siding with buffer stop) | procedural: wood frame, dithered slate, wiped-chalk smudges, jittered chalk strokes |
| `assets/ui/puzzle/c4_plate_n24318.png`, `…_c1742.png`, `…_n47702.png`, `…_c1745.png` | the four paint layers of wagon 24 318 as number plates (enamel / old stencil / brush / wet stencil) | procedural plates, numbers in the generator's own plate type |
| `assets/ui/puzzle/c4_plate_<id>_lit.png` | the same plates held against the hand lamp (Gegenlicht): face as a ghost, the older number dark underneath (bare metal under 24 318) | procedural, from the same masks |
| `assets/ui/puzzle/c4_num_<id>.png` | mini numbers for the wagon token's number window | procedural, mini type |
| `assets/ui/puzzle/c4_wagon.png` | painted wooden token of the goods wagon (planks, sliding door, number window, wheels) | procedural |
| `assets/ui/puzzle/c4_wire.png`, `c4_tick.png`, `c4_halt.png`, `c4_glow.png`, `c4_lamp_on.png`, `c4_lamp_off.png` | hanging wire, chalk tick, red chalk stop mark (ring + cross, shape-coded), banded lamp glow, hand lamp on/off | procedural |
| `assets/ui/puzzle/c4_numbers_board.json` | sizes, post / track / wagon positions, plate faces + under-layers (paint-layer chain, self-checked), measured surface colours | written by the generator |
| `assets/ui/documents/berlin_c4_routes_plan.png` | site plan Süd 8 from the eviction notice (north up, streets, hatched blocks, tram tracks on street 7, shafts S 1–S 3 as rings, north arrow, empty title block) | procedural, original layout |
| `assets/ui/documents/berlin_c4_routes_trace.png` | Marta's tracing paper: line 74 (autumn route) and the detours Okt. / Dez. / Jan. with diamonds, drawn in driving direction | procedural translucent paper, pencil strokes, mini type |
| `assets/ui/puzzle/c4_route_snap.png`, `c4_route_match.png`, `c4_route_underline.png` | corner brackets (diamond on ring), red pencil loop around a matched pair, red underline of „gez. K. A.“ | procedural |
| `assets/ui/documents/berlin_c4_routes.json` | cell size, files, rings, loops, landmarks, start pose, board, title-block rects (no answer; the generator verifies that exactly one pose aligns all three pairs and that it is the solution of `pz_c4_routes`) | written by the generator |

## UI, texts, tests
| Path | Kind | How it was made |
|---|---|---|
| `scenes/ui/TracePuzzle.tscn`, `scripts/ui/trace_puzzle.gd` | number-chain modal (keys 1–4 / Backspace / R / L / Enter / Esc, pad ←/→ A B X Y Back, mouse click-plate-then-post, drag and drop, right-click, hover = layer under the paint; trial run of the wagon token, stop reason in words, success run into the siding) | hand-written, follows `scripts/ui/check_puzzle.gd` |
| `scenes/ui/RoutePuzzle.tscn`, `scripts/ui/route_puzzle.gd` | overlay modal on a light table (arrows / WASD / R / Shift+R / Backspace / Enter / Esc, pad D-pad RB LB A X Y B Back, mouse drag with snap, wheel / right-click turn; success: red pencil on the three pairs, „gez. K. A.“ underlined) | hand-written, key contract of `scripts/ui/blueprint_puzzle.gd` |
| `data/locale/de_c4_ui.json` (the `ui.c4.numbers.*` / `ui.c4.routes.*` keys the design leaves to the UI: faces, plate types, post ids, board labels, states, tips, lamp list, reasons, stamp, error, continue, controls, plan words, match labels) | German texts | hand-written |
| `tests/test_c4_puzzle_ui.gd`, `tests/visual/c4_puzzle_shots.gd` + `C4PuzzleShots.tscn` | unit tests (29 cases) and the screenshot harness of every state | hand-written |

World note: fictional wagon numbers, paint layers and switch posts; a fictional tram route over a fictional site plan of a
fictional Berlin district — not a real railway numbering scheme and not a real plan.
