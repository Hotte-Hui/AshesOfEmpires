# Asset manifest — the data desk of Nebenstelle Süd: side task „Planspiel Abgang“, „Die Datenstelle“, the wireframe game (area: terminal_r13)

Owner: terminal specialist (round 13) · Date: 2026-11-09 · Engine: Godot 4.7.2 · Contract: TECHNICAL_ARCHITECTURE
§12.8 (mini-games) / §12.9 (side tasks), documentation/C4_DESIGN.md §4.2 / §6 (the annex, scene D).

Everything listed here is **original work**, written for this game or generated procedurally by the project scripts
below on 2026-11-09. No pixel, sample, font file or melody was taken from any other source; no downloads, no AI media,
no recordings, no traced reference. The machine is a period-plausible 1964 data-processing desk (vector display,
teleprinter, tape cabinet, card reader) without a real maker's name, type plate or screen layout; „Planspiel Abgang“,
its maps, post scheme and files are fictional, no real person is named (the households of the transfer list are
invented surnames). No regime insignia anywhere (§12.4). Colours: the desk and the roster are painted with the
`annex` ramps of `data/chapters/c4.json` / `env_c4_annex_kit.py` (checked: 0 pixels outside the ramps); the picture
tube has its own documented steps in `scripts/ui/minigames/crt_kit.gd` — glass #07120D / #0A1811, halo #173A26, green
beam #2F6B45 / #6FD08C / #DCFFE2, amber beam #A87A44 / #F2C46A (halo #3A2A14), alarm glass #2A0F0C, steel housing
#15191C–#98A4AC, plate #E6E1CF; high contrast: black glass, #4FAE72 / #9DF5B6 / #FFFFFF, #FFB000 / #FFE9A8. Letters:
the game's own 5×7 capitals (`scripts/ui/pixel_font.gd`) plus thirteen signs drawn for the desk (`crt_kit.gd` EXTRA);
the close-up uses the 3×5 / 5×7 bitmaps of the env kits. Licence: original project work (same terms as the rest of
the game).

## Content (text, data)

| File | What |
|---|---|
| `data/explore/c4_annex_terminal.json` | four entries (level key `L_C4_AnnexA`, scene `L_C4_AnnexB`) and the side task `berlin.task.planspiel`: the desk → the duty roster → mini-game „Die Datenstelle“ → mini-game „Planspiel Abgang“ |
| `data/locale/de_terminal.json`, `data/locale/en_terminal.json` | every text in German and English (same keys): finds, task, both mini-games, the machine's five files (line by line, ≤ 46 characters), the head-up text of the vector display |

## Art

| File | Generator | What |
|---|---|---|
| `assets/environments/berlin_annex/terminal/desk.png` (+ `_n`, `_e`; 65×52) | `py -3 -P tools/pixelgen/gen_annex_terminal.py` | the data desk between machine room and household index: tape cabinet with two reels and a lamp strip, the desk with the round vector display and the teleprinter, the card reader — painted into a bake of the hall with the annex kit and cut out as the difference (the room's own light, normal map, emission mask) |
| `assets/environments/berlin_annex/terminal/roster.png` (+ `_n`; 12×19) | same | the duty roster of the Datenstelle on its clipboard beside the second ladder |
| `assets/environments/berlin_annex/terminal/layout.json` | same | world positions of the cut-outs, the two exploration spots, the desk's small life (cursor, lamp, reel hubs) |
| `assets/environments/berlin_annex/scene.json` (one `actors` entry, two `hotspots`), `provenance.json` (its rows) | same, through `tools/pixelgen/env_keep.py` | `scenes/levels/c4/AnnexTerminal.tscn` with `"scene_id": "L_C4_AnnexB"`; `exp_terminal` (1096, 300), `exp_terminal_roster` (1327, 300). `env_c4_annex.py` is not run; its own merge keeps foreign actors and hotspots |
| `assets/explore/c4/planspiel_strip.png` (240×150) | same | close-up of the find „Lauf zwölf“: the tube with the attic as a wireframe, the breach marked, and the teleprinter strip „LAGE 3 LAUF 12 · ABGANG · WEG: …“ |

Drawn at run time, no files: the housing of the display unit (`crt_kit.gd draw_housing`), the text raster of the
terminal (`crt_kit.gd raster`), the 3D wireframe of the three maps (`abgang_game.gd`: line meshes in a 384×172
SubViewport, palette-stepped by the tube shader, shown ×3), the desk's cursor / lamp / reels (`annex_terminal.gd`).

## Sound (44.1 kHz, 16-bit, mono — `py -3 -P tools/audiogen/mg_audio_terminal.py`, numpy synthesis)

| File | What |
|---|---|
| `assets/audio/sfx/mg_term_hum.wav` (LOOP 2 s) | the display unit at rest: mains transformer 50 / 100 / 150 Hz, the cabinet fan as periodic band noise, a faint whine |
| `mg_term_relay.wav` | one relay: armature, contact bounce, body thump (menu steps; quiet: the beat of the posts) |
| `mg_term_key.wav` | one teleprinter key (digits) |
| `mg_term_ok.wav` | the number is accepted: relay, one 880 Hz tone, relay |
| `mg_term_refuse.wav` | a refusal: relay and a short, low mains buzzer |
| `mg_term_tape.wav` | the release: two relays, the tape drive running up |
| `mg_abgang_step.wav` | one step of the figure: a dry tick |
| `mg_abgang_seen.wav` | the tone when a post has seen the figure: relay, falling two-tone signal 660 → 440 Hz |
| `mg_abgang_through.wav` | a map is passed: three rising pips |
| `mg_abgang_print.wav` | the run is over: the teleprinter hammers the strip, the margin bell |

## Code

| File | What |
|---|---|
| `scenes/levels/c4/AnnexTerminal.tscn`, `scripts/levels/c4/annex_terminal.gd` | the desk as an actor of the art manifest: lit sprites, small life, the two `lever_spot.gd` interactables (chain on the desk) |
| `scenes/ui/minigames/DataTerminal.tscn`, `scripts/ui/minigames/terminal_game.gd`, `terminal_logic.gd` | „Die Datenstelle“: login, list / open / search, release |
| `scenes/ui/minigames/PlanspielAbgang.tscn`, `scripts/ui/minigames/abgang_game.gd`, `abgang_logic.gd` | „Planspiel Abgang“: three maps, posts, sight beams, solver (demo, hint trace), the 3D picture |
| `scripts/ui/minigames/crt_kit.gd` | the shared picture tube: phosphor shader, line shader, letters, text raster, housing |
| `tests/test_c4_terminal.gd`, `tests/visual/c4_terminal_shots.gd` | unit tests; windowed capture harness (`--shots=<dir> [--scale=1.5] [--hc=1] [--rm=1] [--lang=en]`) |

## Reproduce

```bash
py -3 -P tools/pixelgen/gen_annex_terminal.py      # art, layout, scene.json actor, provenance rows (byte-stable re-run)
py -3 -P tools/audiogen/mg_audio_terminal.py       # the ten sounds
"$GODOT" --headless --path . --script res://tests/run_all.gd -- --filter=test_c4_terminal
```
