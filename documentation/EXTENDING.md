# EXTENDING — the recipe for the next chapter

State after round 10: Chapters 1–4 (part 2 included) form one Story chain that ends in `L_X1_Montage`, the end card
and the credits. Everything chapter-specific is data (`data/v3/*.json` + one `data/chapters/c<n>.json`) plus new
levels, films, puzzle UIs and art — the engine (`scripts/core/game.gd`, `scripts/story/story_engine.gd`,
`scripts/core/chapter_ext.gd`) normally needs no change. Chapter 4 part 2 (round 10) is the model for every step
below; its files are named as examples. Contracts in detail: `documentation/TECHNICAL_ARCHITECTURE.md` (§3 level,
§12 exploration / insignia / films / mini-games / tasks / memories / switches / board, §13 chapter extensions);
„§“ numbers below point there, „step n“ to the sections of this file.

## 0. Ground rules
- Tools: `GODOT="$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64_console.exe"`; Python `py -3 -P`
  (`PYTHONIOENCODING=utf-8`). Line ends LF everywhere (`.gitattributes`); generators write with `newline='\n'`.
- Imports only under the shared lock: `until mkdir .import_lock 2>/dev/null; do sleep 3; done;
  "$GODOT" --headless --path . --import > /dev/null 2>&1; rmdir .import_lock`. Never delete `.godot/`.
- Art and audio come from the project's own deterministic generators (`tools/pixelgen/`, `tools/audiogen/`): no
  downloads, no traced references, no AI pixels. Real regime insignia only in `*_hist` files with a neutral twin, picked
  by `Symbols.pick()` (`scripts/core/symbols.gd`, §12.4); never glorifying. German player texts, no „fiktiv“ notes.
- Protagonists: Alexei Morozov (`alexei`, Karsk) and Konrad Adler (`konrad`, Berlin).
- One owner per file when streams work in parallel; shared files only by exact, small edits.

## 1. Contract document first
Write `documentation/C<n>_DESIGN.md` (model: `documentation/C4P2_DESIGN.md`) from `documentation/STORY_BIBLE.md`
§6 (chapters) / §7 (state variables) and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md`: scene list and protagonist
per scene, objectives in story order, events, decisions and their effects, new flags, puzzles (type + UI), films,
cast, places (env ids, hotspot names), finds / chats / tasks / mini-games / history cards, board threads, memories,
and which stream owns which file. Every later step only implements this document.

## 2. Story data — `data/v3/`
- `scenes.json`: insert the new scenes before `L_X1_Montage` (one linear chain; each scene has `protagonist` and
  `exit_on_event`).
- `quests.json`: objectives in story order — the end card (`Game.end_card_decisions`), the memories and the drivers
  follow that order; add every new quest event to `slice_end_requires`.
- `flags.json` (step 3), `puzzles.json` (step 6), `dialogue.json`, `items.json`, `cinematics.json` (step 5).
- Texts referenced by `data/v3` live in `data/v3/locale_de.json` (the validator checks that file); every other text
  goes to its own `data/locale/de_<area>.json` (e.g. `data/locale/de_c4p2_ui.json`, `de_c4p2_dialogue.json`).
- `LOCKED_CINEMATICS` in `scripts/story/story_engine.gd` lists every sequence of `cinematics.json`.

**`data/chapters/c<n>.json`** (copy the keys of `data/chapters/c4p2.json`): `levels` (scene → .tscn), `entry_spawn`,
`chapter_cards`, `palettes`, `grades`, `line_expr`, `line_variants`, `choice_text`, `reactions`, `puzzles`
(objective → UI scene), `cinematics` (sequence → scene), `switches` (per scene: partner, ambience, music, grade),
`looks`, `carry`. `ChapterExt` (`scripts/core/chapter_ext.gd`, `Game.ext`) merges all chapter files; conditions are
`{"<flag>": ">=1" | "==n" | … | true | false, "choice.<objective>": "<option>"}` (§13).

## 3. Story flags and the save migration
- A new flag goes into `data/v3/flags.json` with its default and is written only by objectives of the chapter that
  introduces it (C4P2_DESIGN §1.1) — then the default is exactly what an older save's replay computes.
- Old saves need no hand work: `rebase_story()` in `scripts/core/save_system.gd` (autoload `Saves`) re-bases a state
  recorded before the chain grew and first calls `fill_flag_defaults()`; `memory_flags()` in `scripts/core/memories.gd`
  does the same for memory replays. `Story.validate_save_json()` still refuses wrong values and unknown keys.
- Prove it: a `tests/test_save_migration_r<round>.gd` like `tests/test_save_migration_r10.gd` (payloads of every older
  shape, finished playthroughs, memory snapshots, and COPIES of the user's real saves — never the originals).

## 4. Levels and switch scenes
- Two Story scenes per level file, e.g. `scenes/levels/L_C4P2_Karsk.tscn` = `L_C4P2_KarskA` / `L_C4P2_KarskB`, two walk
  areas split by a permanent `blockers` entry. In-level protagonist switches: §12.11 (`switches` in the chapter file);
  alternating cities = a level load per scene (`"partner": "none"`) with a match-cut film between.
- Level script: the gated-art level `scripts/levels/c4/annex_level.gd` (gate keys `after` / `until` / `choice` /
  `scene` on layers, decals, fx, lights, actors) or a subclass (`scripts/levels/c4p2/berlin_c4p2_level.gd`); base
  `scripts/levels/level.gd`, layers `scripts/levels/layer_stack.gd`. Story NPCs: `scripts/actors/story_npc.gd`
  (`show_after` / `hide_after`); optional hotspots: `scripts/actors/gated_interactable.gd`.
- Art: one generator per place, `tools/pixelgen/env_<id>.py` → `assets/environments/<env_id>/` (layers + `_n` / `_e`
  maps, `scene.json` §3.1, `provenance.json`; hotspot names §12.2 shared with `explore_hotspots.json`). The folders are
  shared (walkers, hand-added actors, explore data), so every generator follows `tools/pixelgen/env_keep.py`
  (`KEEP.remove_own_pngs`, `KEEP.merge_scene` + `KEEP.write_json`, `KEEP.merge_rows`; rules:
  `py -3 -P tools/pixelgen/env_keep.py --selftest`; model `tools/pixelgen/env_c4p2_berlin.py`) and is listed in
  `tests/test_env_generators_keep.gd`. Ambient walkers: `tools/pixelgen/walkers_r8.py` + the `AmbientWalkers` actor
  (`scenes/actors/AmbientWalkers.tscn`, `<env>/walkers.json`).
- Check in the real renderer: `"$GODOT" --path . -- --capture=<dir>/shot.png --scene=<scene> --frames=90` (§1).

## 5. Cinematics
- Sequence id `LS_C<n>_<Name>`: `data/v3/cinematics.json` + `LOCKED_CINEMATICS` + `cinematics` in the chapter file.
- Scene `scenes/cinematics/ch<n>_<name>/` whose script extends the chapter base. The common runtimes are one chain:
  `scenes/cinematics/ch3_common/c3_cinematic.gd` (§12.5: finished exactly once, idempotent `skip()`, `configure(ctx)`,
  `seek()` / `advance()`, cue list, reduced motion) → `scenes/cinematics/c3p2_common/c3p2_cinematic.gd` →
  `scenes/cinematics/c4_common/c4_cinematic.gd` → `scenes/cinematics/ch4p2_common/c4p2_cinematic.gd`; a new chapter
  adds `scenes/cinematics/ch<n>_common/` extending the last one.
- Art `tools/pixelgen/env_c4p2_cine*.py` → `assets/cinematics/c4p2/` (+ `layout.json`); texts
  `data/locale/de_c4p2_cinematics.json`; sound `tools/audiogen/c4p2_cine_audio.py`; test `tests/test_c4p2_cinematics.gd`.
- Finale: `scripts/cinematics/finale/finale_montage.gd`; the end card lists every decision in story order and fits
  itself to the text size (`Game._show_end_card`). Check it at 100 / 125 / 150 %:
  `"$GODOT" --path . res://tests/visual/cine_finale_harness.tscn -- --cinematic=none --fin-mode=endcard
  --fin-endcard=<one option per decision> --fin-textscale=1.5 --fin-out=<dir>` (add the new objective to
  `ENDCARD_OBJECTIVES` in `tests/visual/cine_finale_harness.gd`).

## 6. Puzzles
- `data/v3/puzzles.json` (type, answer), `puzzles` in the chapter file (objective → UI scene; instanced once, opened
  with `open(obj_id)`); the verdict is always `Story.solve_puzzle`.
- Key contract (§13): `is_open`, `symbols` in tray order, keys 1…N, Backspace undo, R clear, Enter submits, Esc closes,
  auto-close ≤ 7 s after success, pad and mouse equivalents, readable at 125 / 150 %. Models:
  `scenes/ui/JoinPuzzle.tscn` + `scripts/ui/join_puzzle.gd`, `scenes/ui/HousePuzzle.tscn` + `scripts/ui/house_puzzle.gd`
  (layouts `assets/ui/documents/karsk_c4p2_halves.json`, `assets/ui/puzzle/c4p2_house.json`).
- Art + verification against `puzzles.json`: `tools/pixelgen/gen_ui_c4p2.py`; texts `data/locale/de_c4p2_puzzles.json`;
  test `tests/test_c4p2_puzzle_ui.gd`; shots `res://tests/visual/C4P2PuzzleShots.tscn -- --out=<dir>`.

## 7. Cast and audio
- Figures `assets/characters/<id>/` (§4) from a chapter generator (`tools/pixelgen/characters_c4p2.py`); portraits
  `tools/pixelgen/chargen_portrait2*.py`; names / lines `data/locale/de_c4p2_characters.json`.
- Sound `assets/audio/{amb,music,sfx}/` (§7, 44.1 kHz / 16 bit) from `tools/audiogen/c4p2_audio.py`,
  `tools/audiogen/mg_audio_c4p2.py`; test `tests/test_c4p2_cast_audio.gd`.

## 8. Exploration, tasks, mini-games, history cards
- Finds and chats per place: `data/explore/c4p2_karsk.json`, `data/explore/c4p2_berlin.json` (`Explore` autoload,
  `scripts/core/explore.gd`, §12.1–12.2); texts `data/locale/de_explore_c4p2.json`; test `tests/test_c4p2_explore.gd`.
- History cards by fixed id (§12.3): `data/explore/c4p2_history_reich.json`, `data/explore/c4p2_history_soviet.json`,
  texts `data/locale/de_history_c4p2.json` (their sources roll in the end credits).
- Side tasks (§12.9): `data/explore/tasks_*.json`, `data/explore/quay_tasks.json`; tests `tests/test_tasks.gd`.
- Mini-games (§12.8): base `scripts/ui/minigames/minigame_base.gd`; a game = `scenes/ui/minigames/<Name>.tscn` +
  `scripts/ui/minigames/<name>_game.gd` + `<name>_logic.gd` (e.g. `scenes/ui/minigames/LuggageScale.tscn`,
  `scripts/ui/minigames/luggage_game.gd`, `scripts/ui/minigames/luggage_logic.gd`).

## 9. Evidence board „Die Akte C-17“ (§12.12)
Items, places and threads in `data/board/c17_board.json` / `data/board/c17_links.json`; texts
`data/locale/de_board.json`; UI `scripts/ui/evidence_board.gd`; art `tools/pixelgen/gen_ui_board.py`; test
`tests/test_evidence_board.gd`.

## 10. Memories and prints (§12.10)
Every scene of `data/v3/scenes.json` with a protagonist and an exit event becomes a memory card by itself
(`scripts/core/memories.gd`, chapter = its quest's `title_key`). It needs a print `assets/ui/memories/<scene>.png`:
capture the raw frame with `res://tests/visual/memory_thumbs.tscn` (spot table in `tests/visual/memory_thumbs.gd`),
then `tools/pixelgen/gen_ui_memories.py` (crop in `CROPS`) makes the sepia print; rows in
`documentation/asset_manifest_parts/memories.md`; test `tests/test_memories.gd`.

## 11. The two E2E drivers
- `scripts/core/autoplay.gd` (Story API): add the new objectives to `ROUTE`, the final-pass / explore tables
  (`FINAL_PASS`, `EXPLORE_AT`), the default of the new decision in `choices`, its index in the comma spec and the
  meter / flag each option must move.
- `scripts/core/inputplay.gd` (synthetic keys and a path-finding walker): the same `choices` default and spec index,
  `ARROW_CHOICES` / `NOT_FINAL_WALK` where they apply, and the walking / puzzle-key steps of the new scenes.
- Both take one value per decision (`--autoplay=<a1>,<m1>,<c3a>,<c3b>,<c3d>,<c3g>,<c4d>,<c4g>` today) and keep their
  saves in `user://e2e/saves`.

## 12. Tests
`tests/run_all.gd` runs every `tests/test_*.gd` (a `RefCounted` with `run() -> Array` of failures; helpers
`tests/support/test_kit.gd`). Per chapter at least: routes (`tests/test_c4p2_routes.gd`), save migration, films,
puzzle UIs, place art (`tests/test_c4p2_karsk_art.gd`, `tests/test_c4p2_berlin_art.gd`), exploration, cast audio.
Filtered run: `"$GODOT" --headless --path . --script res://tests/run_all.gd -- --filter=<x> | grep -E "^FAIL|^      - |SUMMARY"`.

## 13. Asset manifest and documents
- Each stream writes `documentation/asset_manifest_parts/<area>.md` (provenance & licence, files, reproduce); add the
  part name to `ORDER` in `tools/docs/build_asset_manifest.py` (unknown names sort last) and run it →
  `documentation/ASSET_MANIFEST.md`.
- Quest database section: a `tools/docs/gen_quest_db_c<n>.py` like `tools/docs/gen_quest_db_c4p2.py` (marker block in
  `documentation/QUEST_DATABASE.md`, `--check`). Play time: `tools/docs/estimate_playtime.py`.
- Update `documentation/TECHNICAL_ARCHITECTURE.md` §13 (one bullet per stream), `documentation/DEVELOPMENT_STATUS.md`,
  `documentation/TEST_REPORT.md`, `documentation/NEXT_STEPS.md` and, for this file, any step that changed.

## 14. Import, E2E routine, user-data backup, export
1. Shared import (step 0), then the full unit suite.
2. Back up the player's folder first — `%APPDATA%/Godot/app_userdata/Ashes of Empires- The Last Winter` (saves,
   `settings.cfg`, profile, photos): the user plays the same build. Drivers never write the player's slots, but
   harnesses can touch settings.
3. Run the drivers one after another (they share `user://`): autoplay play / `--autoplay-skip` /
   `--autoplay-explore` / `--autoplay-memories` and inputplay play / `--inputplay-skip` / `--inputplay-explore` /
   `--inputplay-memories`, over routes that cover every option of every decision.
4. Delete `user://e2e/` (and any folder a harness made), restore the backup, compare.
5. Export `"$GODOT" --headless --path . --export-release "Windows Desktop" builds/windows/AshesOfEmpires.exe`
   (`export_presets.cfg`) and start the exe once before calling the round done.
