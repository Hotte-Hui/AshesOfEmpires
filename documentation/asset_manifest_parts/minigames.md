# Asset manifest — optional mini-games (area: minigames)

Owner: minigames specialist · Date: 2026-11-05 · Engine: Godot 4.7.2 · Contract: TECHNICAL_ARCHITECTURE §12.8
(user request: "mehr kleine mini games hinzufügen").

Everything listed here is **original work**, generated procedurally by project scripts on 2026-11-05. No pixel,
sample or melody was taken from `documentation/references/` or any external source; no downloads, no AI media.
Colours come from `data/palettes.json` (`karsk` snow/stone/wood/rust/teal/night/copper, `archive`
wood/amber/paper/ink/skin ramps). The porter's face in "Das Radio" is the existing portrait
`assets/characters/porter/portrait.png` (characters area), only drawn, not modified. No regime insignia anywhere.
Licence: original project work (same terms as the rest of the game).

## The three mini-games

| Explore entry | Scene / script | Place (hotspot, world px) | Game |
|---|---|---|---|
| `karsk.shunting` (detail) | `scenes/ui/minigames/Shunting.tscn` · `shunting_game.gd` + `shunting_logic.gd` | Karsk `exp_shunting` [1112, 256], beside the dwarf shunting signal | Inglenook-style shunting from above: headshunt (loco + 2 wagons), points 1/2, sidings 1 (3), 2 (2), 3 (2); four wagons (tank, coal, panels, covered). Build the evening train on siding 1 as the waybill says (points→buffer: panels, coal, tank). Optimal 6 trips (BFS solver in the logic, also feeds the third hint level). |
| `karsk.chess` (detail) | `ChessProblem.tscn` · `chess_game.gd` + `chess_logic.gd` | Karsk `exp_chess` [362, 256], at the sleeper stack left of the signal-box stairs (next to `exp_stairs_under`) | The day/night-shift peg chess on a crate lid: mate in two for the day shift (White Kg1 Qc4 Nh6 Pf2 g2 h2 vs Black Kh8 Qb2 Ra8 Re8 Pa7 b7 g7 h7): 1. Dg8+ Txg8 (forced) 2. Sf7# (smothered mate). The line is hard-coded; every other move is refused with a reason (illegal, night-shift piece, too slow: Db1+, Sf7+ Kg8, Sxg8 …). |
| `berlin.radio_dial` (detail) | `RadioDial.tscn` · `radio_game.gd` + `radio_logic.gd` | Berlin `exp_radio_dial` [158, 300], left end of the porter's counter (28 px from `exp_porter`) | Tune the 1955 set from the Reichssender (red line) to the pencil dot: static thins, magic eye closes, a jazz trio comes through; listen 5 s while the porter reads. When his paper sinks, the needle must be back on the red line (station key R); being "caught" only resets the needle and costs 40 % of the listening. |

Shared base `scripts/ui/minigames/minigame_base.gd` (extends `ui_modal.gd`): chrome (kicker, title, subtitle,
instruction, status, hint plate, buttons, key hints), UIRoot modal stack or stand-alone input, `finished(success)`,
`open(ctx)`, auto mode (success after 0.2 s), hint after 2 refusals, solved hold 2.4 s (confirm continues),
`demo_solve()` = synthetic key events only (`Input.parse_input_event`, keycode + physical_keycode). Keyboard,
mouse and pad (d-pad/stick, A, B, Y/X). All text via Loc: `data/locale/de_minigames.json` (`mg.*`); find texts in
`de_explore_karsk.json` / `de_explore_berlin.json` (protagonist voice).

## Generators

* `tools/pixelgen/gen_minigames.py` — `py -3 -P tools/pixelgen/gen_minigames.py`, then import (shared lock).
  Deterministic (seeds = `crc32` of names). Drawn 1:1, **stored x3 nearest** in `assets/ui/minigames/`.
* `tools/audiogen/minigame_sfx.py` — `py -3 -P tools/audiogen/minigame_sfx.py` (numpy only, deterministic).
  44.1 kHz / 16-bit mono WAV in `assets/audio/sfx/`; loops carry a RIFF `smpl` chunk (import loop_mode detect).

## Files

| Path | Size (1:1 art px) | Use |
|---|---|---|
| `assets/ui/minigames/shunt_yard.png` | 360×150 | Snowy yard from above: headshunt + 3 sidings, two points, ballast, sleepers, rails, buffer stops, track boards 1–3, sleeper stack, fence |
| `assets/ui/minigames/shunt_engine.png` | 34×12 | Shunting tank engine from above (cab/bunker rear, boiler, dome, chimney; red buffer beams) |
| `assets/ui/minigames/shunt_wagon_{tank,coal,flat,box}.png` | 36×12 each | Tank wagon, coal gondola, flat wagon with wall panels, covered wagon with snow |
| `assets/ui/minigames/shunt_lever_{0,1}.png` | 14×22 | Hand-throw points lever with lamp (0 straight, 1 thrown) |
| `assets/ui/minigames/shunt_layout.json` | — | Route polylines, lever spots, buffers (art px) read by the script |
| `assets/ui/minigames/chess_board.png` | 172×172 | Peg-chess board (19 px squares, peg holes) on a crate lid with nails and snow |
| `assets/ui/minigames/chess_pieces.png` | 108×40 (6×2 cells 18×20) | K Q R B N P; row 0 day shift (birch), row 1 night shift (stained) |
| `assets/ui/minigames/radio.png` | 288×146 | 1955 walnut table radio: fabric grille with ribs, magic-eye bezel, glass scale with ticks, red Reichssender line, pencil dot, 5 piano keys, volume knob |
| `assets/ui/minigames/radio_eye.png` | 144×18 (8 frames) | Magic eye, 0 = no signal … 7 = tuned |
| `assets/ui/minigames/radio_knob.png` | 192×24 (8 frames) | Tuning knob rotation |
| `assets/ui/minigames/radio_newspaper.png` | 104×64 | The porter's newspaper (abstract print, no masthead text) held in two hands |
| `assets/ui/minigames/radio_layout.json` | — | Scale / eye / knob / key positions (art px) |
| `assets/audio/sfx/mg_points.wav` | 0.9 s | Points lever clank + blade slide |
| `assets/audio/sfx/mg_couple.wav` | 1.1 s | Automatic coupler clash |
| `assets/audio/sfx/mg_shunt.wav` | 1.5 s | Engine moving off (chuffs, rail joints) |
| `assets/audio/sfx/mg_chess_tap.wav` | 0.22 s | Wooden peg piece set down |
| `assets/audio/sfx/mg_radio_static.wav` | 4 s LOOP | Medium-wave hiss and crackle |
| `assets/audio/sfx/mg_radio_jazz.wav` | 8 s LOOP | Original jazz trio (Dm7 G7 Cmaj7 A7, walking bass, brushes, comping) through far medium wave |
| `assets/audio/sfx/mg_radio_whistle.wav` | 1 s LOOP | Heterodyne whistle; the UI bends its pitch with the detuning |
| `assets/audio/sfx/mg_radio_key.wav` | 0.3 s | Radio piano key snapping down |

The Reichssender plays the existing `assets/audio/sfx/berlin_radio_loop.wav` (audio area), unchanged.

## Verification (2026-11-05)

* `tests/test_minigames.gd` (10 cases, 557 checks): solver + hand solution accepted, wrong moves refused, chess
  lines and soundness, radio porter cycle / caught / listening, entries + hotspots + Interactables + Loc keys,
  auto mode, keyboard via `modal_input`, give-up.
* `tests/visual/minigames_harness.gd` (windowed): real UIRoot over a game screenshot; start / hint / solved shots of
  all three, each solved by `demo_solve()` through synthetic keys, `finished(true)` received, tree unpaused after.
  `godot --path . --script res://tests/visual/minigames_harness.gd -- --shots=<dir> [--only=shunting|chess|radio]`
