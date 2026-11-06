# Asset manifest — round-7 mini-games „Der Morsetaster“ and „Rohrpost“ (area: minigames_r7_kb)

Owner: minigames_r7_kb specialist · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: TECHNICAL_ARCHITECTURE §12.1/§12.8
(user request this round: more play time, new mini-game ideas).

Everything listed here is **original work**, generated procedurally by the project scripts below on 2026-11-06. No
pixel, sample or melody was taken from `documentation/references/` or any other source; no downloads, no AI media,
no recordings. Colours come from `data/palettes.json` (`karsk` night/teal/sage/sky/stone/rust/copper/snow/wood,
`archive` paper/ink/blue/amber/wood/night, `berlin` patina/snow) plus a polished-brass ramp and a violet stamp ink
defined in the generators. The 5×7 / 3×5 pixel fonts (Latin capitals with umlauts, the full Russian alphabet, digits)
are hand-made bitmaps in `tools/pixelgen/mg_r7_kb_lib.py`. No regime insignia, no flags, no emblems anywhere (§12.4):
the Karsk desk shows a plain tea-glass holder, the archive board a plain brass plate.
Historical model: the Morse registers (paper-tape inkers), sounders and keys of Soviet railway telegraphy, Russian
Morse code with its international equivalents as printed on wall charts; the hand-switched house pneumatic-tube
systems of large German offices. Licence: original project work (same terms as the rest of the game).

## The two mini-games

| Explore entry | Scene / scripts | Place (hotspot, world px) | Game |
|---|---|---|---|
| `karsk.morse` (detail, area `karsk`) | `scenes/ui/minigames/MorseKey.tscn` · `scripts/ui/minigames/morse_game.gd` + `morse_logic.gd` | L_A1_Railyard `exp_morse` [590, 256], right corner of the signal box where the telegraph line comes in (38 px from the side task's `exp_task_signalbox`) | The duty officer has gone for tea; the telegraph rings. The register prints the dispatcher's telegram on its tape, the sounder clicks, the call lamp flashes. Alexei takes the routine (ВАГ 24311) down by ear; the player decodes НЕ ВЗВЕШИВАТЬ („nicht verwiegen“) letter by letter with the wall chart АЗБУКА МОРЗЕ (7×6: Russian Morse with the international equivalents), then keys the receipt ПР (= принял) on the key: short = dot, held past the mark = dash, pauses never matter, a wrong element restarts only that letter. The line answers Р. Telegram line already on the form: П 2417 ОПОЗД 40 МИН (delay). |
| `berlin.rohrpost` (detail, area `berlin`) | `scenes/ui/minigames/Rohrpost.tscn` · `scripts/ui/minigames/rohrpost_game.gd` + `rohrpost_logic.gd` | L_M1_Archive `exp_rohrpost` [932, 300], at the information desk of the reading room where the copper tube comes down from the ceiling | The house tube system's switch board (1938). Three capsules from the porter's lodge to the reading room, three boards of rising difficulty (2, 3, 4 knobs to turn; board 2 with a frozen main line, board 3 with a crossing, a return line and a knob that is not on the way). The capsule rushes through the brass tubes (whoosh); a wrong setting sends it to the registry, Abt. III, the director's office, the canteen, the plan archive or back to the lodge (each comes back with a small line), or jams it in a knob / the frozen line. Each delivered capsule shows what it brought: the porter's loan slip for a book about pigeons, the house management asking who turned up the heating, a sandwich for the librarian. |

Contract (§12.8, shared base `minigame_base.gd`): `open(ctx)`, `ctx.auto` resolves after 0.2 s, `finished(success)`
exactly once, Esc / „Aufgeben“ without penalty (nothing is ever lost), hints after two refusals — following the
Settings `puzzle_hints` (0 never, 2 at once) and the current letter / board (Morse: the group's length, then the field
glows; receipt: how to key, then the rhythm of П and Р; Rohrpost: follow the tube back from the reading room, then
„Weiche n steht noch falsch“ with the knob ringed), `demo_solve()` plays through synthetic key events only (~25 s each).
Keys — Morse: arrows/WASD/d-pad on the chart, Enter/Space/E/pad A write, R/pad Y repeats the letter; receipt: hold
Space/Enter/E/pad A or the mouse on the key, R plays the receipt once. Rohrpost: arrows choose a knob (every knob
reachable), Space/E/pad A turn, Enter/pad X/Y call the capsule, R puts the board's knobs back; mouse on knobs (right
click turns back) and the button. Layout: one custom-drawn stage per game that fits the panel — pixel art ×3, or ×2
(×1 as a last resort) when the panel is short (large text, hint plate); room for the hint is reserved so nothing
jumps. Text scale: all drawn texts follow it; the Morse form moves up over the register and stacks its translations
before any text shrinks, the Rohrpost side column switches to a compact list instead of shrinking below 100 %; board
labels never go below their normal size. High contrast: white paper, black ink, yellow cursors and rings.
All text: `data/locale/de_minigames_r7_kb.json` (`mg.morse.*`, `mg.tube.*`, find texts `explore.karsk.morse.*`,
`explore.berlin.rohrpost.*`); entries: `data/explore/minigames_r7_kb.json`.

## Generators

* `tools/pixelgen/gen_mg_morse.py` — `py -3 -P tools/pixelgen/gen_mg_morse.py`, then import (shared lock).
* `tools/pixelgen/gen_mg_rohrpost.py` — `py -3 -P tools/pixelgen/gen_mg_rohrpost.py`, then import. Holds the three
  boards and verifies them before drawing (solvable, start not solved, a unique fewest-change setting with 2/3/4
  changes); writes `rohrpost_layout.json`, the single source of the puzzle for `rohrpost_logic.gd`.
* `tools/pixelgen/mg_r7_kb_lib.py` — shared canvas helpers and the pixel fonts of both generators.
* `tools/audiogen/mg_audio_r7_kb.py` — `py -3 -P tools/audiogen/mg_audio_r7_kb.py` (numpy only). 44.1 kHz / 16-bit
  mono WAV; loops are built periodic and carry a RIFF `smpl` chunk (import loop_mode detect).
All deterministic (seeds = `crc32` of names): a re-run reproduces all 28 files byte for byte (checked 2026-11-06).
UI art is drawn 1:1 and **stored ×3 nearest**; the two find close-ups are stored 1:1 (the DiscoveryView shows them ×3).

## Files

| Path | Size | Use |
|---|---|---|
| `assets/ui/minigames/morse/morse_desk.png` | 300×144 art (900×432) | The telegraph desk in the signal box: window onto the yard at dusk (wagon 24-311 under snow, lamp post), two-tone oil-paint wall, junction box and wiring, call-lamp plate ВЫЗОВ, calendar, oilcloth desk, duty log, tea glass, Morse register (paper reel, clockwork, inking wheel, electromagnet, tape table, tape spilling onto the desk), pencil |
| `assets/ui/minigames/morse/morse_sounder.png` | 2 × 40×30 art | Sounder (Klopfer): armature up / down |
| `assets/ui/minigames/morse/morse_key.png` | 2 × 54×24 art | Morse key: lever up / down |
| `assets/ui/minigames/morse/morse_lamp.png` | 2 × 20×20 art | Call lamp, amber glass off / on |
| `assets/ui/minigames/morse/morse_table.png` | 222×144 art (666×432) | Wall chart АЗБУКА МОРЗЕ: pinned paper card, 7×6 grid (letters, codes and equivalents drawn by the UI), pencil note ПРОВ. 1963, tea ring |
| `assets/ui/minigames/morse/morse_tape.png` | 48×6 art | Tileable Morse tape for the strips glued onto the telegram form |
| `assets/ui/minigames/morse/morse_layout.json` | — | Tape / sprite / form / chart positions in art px, the chart's sign order |
| `assets/ui/minigames/morse/find_telegram.png` | 300×190 (1:1) | Close-up of the find: the telegram form with the glued strips, ПРИНЯЛ: ПР, the station's receiving stamp, pencil, tea glass |
| `assets/ui/minigames/rohrpost/rohrpost_board_{1,2,3}.png` | 286×142 art (858×426) each | The switch board: enamel panel with an engraved plan grid in a wooden frame, brass tubes with flanges, diverter housings, station mouths, the crossing (board 3), the frozen line with frost and a red tag GESPERRT (board 2), brass plate HAUSROHRPOST 1938 |
| `assets/ui/minigames/rohrpost/rohrpost_knob.png` | 6 × 18×18 art | Diverter knob with its brass channel W-E, N-S, N-E, E-S, S-W, W-N |
| `assets/ui/minigames/rohrpost/rohrpost_capsule.png` | 2 × 12×12 art | The capsule (dark leather, brass caps, light rim) horizontal / vertical |
| `assets/ui/minigames/rohrpost/rohrpost_lamp.png` | 2 × 8×8 art | Station pilot lamp off / on |
| `assets/ui/minigames/rohrpost/rohrpost_layout.json` | — | The three boards (tiles, diverters, stations, frozen cells, verified solution) and the geometry |
| `assets/ui/minigames/rohrpost/find_capsules.png` | 300×180 (1:1) | Close-up of the find: the opened capsule, its lid, the loan slip, the circular with its EINGANG stamp, the sandwich in parchment |
| `assets/audio/sfx/mg_morse_down.wav` | 0.14 s | Sounder armature striking the lower stop |
| `assets/audio/sfx/mg_morse_up.wav` | 0.11 s | Armature back against the upper stop |
| `assets/audio/sfx/mg_morse_key_down.wav` | 0.15 s | Key contact closing (bakelite, brass, desk thump) |
| `assets/audio/sfx/mg_morse_key_up.wav` | 0.14 s | Key spring lifting the lever |
| `assets/audio/sfx/mg_morse_bell.wav` | 1.35 s | Call bell of the telegraph line (trembler bell + ring-out) |
| `assets/audio/sfx/mg_morse_inker.wav` | 2.00 s LOOP | Clockwork of the register drawing the tape |
| `assets/audio/sfx/mg_tube_turn.wav` | 0.30 s | Diverter knob into its next detent |
| `assets/audio/sfx/mg_tube_bell.wav` | 1.20 s | Desk bell calling the porter's lodge |
| `assets/audio/sfx/mg_tube_send.wav` | 1.05 s | Capsule dropped in far away, valve, the air takes it |
| `assets/audio/sfx/mg_tube_rush.wav` | 2.00 s LOOP | Air rushing through a brass tube |
| `assets/audio/sfx/mg_tube_arrive.wav` | 0.85 s | Capsule shooting out into the wicker basket |
| `assets/audio/sfx/mg_tube_stuck.wav` | 0.90 s | Capsule jamming: thud, knock, escaping air |

## Verification (2026-11-06)

* `tests/test_minigames_r7_kb.gd` (17 cases, ~1340 checks): chart complete and unique with correct international
  equivalents; telegram timeline (bell, one click/release per element, every letter arrives once, slower target words);
  decoding and receipt accepted, refusals with reasons (too early, wrong letter, wrong element restarts the letter);
  boards solvable with unique 2/3/4-change solutions matching the generator, knob-by-knob progress through the wrong
  offices, jam / frozen / loop detection, continuous capsule path; both scenes: §12.8 contract, auto mode, keyboard play
  to the solution through `modal_input`, every knob reachable by arrows, hint after two refusals, `puzzle_hints` 0/1/2,
  Esc without a find, `finished` exactly once, `demo_solve` sends synthetic keys only; data, Loc keys (no overrides,
  calm German typography), art sizes, layout files, audio format and loop chunks, placement (content-owned hotspots
  inside the walk band, clear of story spots / finds / other mini-games, one Interactable each under Playfield).
* `tests/visual/minigames_r7_kb_shots.tscn` (windowed, real Game path): boots Main into the level, puts the
  protagonist on the find, captures the prompt, opens the find through `Game.interact()`, refuses twice by keys (hint),
  runs `demo_solve()` while capturing every stage, checks `finished(true)`, the DiscoveryView and the recorded find.
  `godot --path . res://tests/visual/minigames_r7_kb_shots.tscn -- --scene=L_A1_Railyard|L_M1_Archive
  --capture=<dir>/boot.png --frames=100000 --r7-out=<dir> [--r7-ts=1.5] [--r7-hc=1] [--r7-tag=x]`
