# MERGE NOTES — Chapter 3 („Der eiserne Frieden“, opening) → master

Branch `kapitel-3` was built in parallel to work on `master`. New logic lives in NEW files; this list names EVERY change to a
file that already existed on `master` at 2d087fa, with the reason and how to resolve a conflict. Design: `C3_DESIGN.md`.

## 1. Changes to existing files
| File | Change | Why | If it conflicts |
|---|---|---|---|
| `data/v3/scenes.json` | `L_M1_Archive.next_scene` = `L_C3_Station`; two scenes inserted before `L_X1_Montage` | the engine accepts only one linear chain ending in the montage | keep both sides' additions; the chain must stay A1 → M1 → C3_Station → C3_Hall → X1 |
| `data/v3/quests.json` | `slice_end_requires` += `c3a_completed`, `c3b_completed`; quests `q_c3a_arrival`, `q_c3b_palais` appended | finale needs every quest event | keep both; append order irrelevant |
| `data/v3/flags.json` | events `c3a_completed`, `c3b_completed` (before `slice_completed`); 7 flags appended | new meters; defaults keep old saves valid | keep both |
| `data/v3/items.json`, `puzzles.json`, `cinematics.json`, `dialogue.json` | C3 entries appended | story data | keep both |
| `data/v3/locale_de.json` | 78 `*.c3*` keys appended (objective, choice, item, dialogue, chapter and scene titles) | the Story validator requires every text key used by data/v3 in THIS file | keep both |
| `scripts/story/story_engine.gd` | `LOCKED_CINEMATICS` += `LS_C3_Trains`, `LS_C3_ToHall`, `LS_C3_Close` | validator list must equal the cinematic ids; runtime semantics unchanged | keep the longer list (+ master's own additions) |
| `scripts/core/game.gd` | `const ChapterExt` + `var ext`; palettes/grades merge in `_ready`; fallbacks to `ext` in `goto_level` (level path, chapter card), `_setup_level` (entry spawn), `_do_dialogue` (line variant + expression), `_do_choice` (option texts + reaction), `_do_puzzle` (puzzle UI), `_play_cinematic_by_id` (§12.5 scenes); `_first_visit()` matches objectives by quest scene instead of the level-id prefix | chapter content stays data-driven; the old prefix test broke for two levels sharing "c3" | re-apply the one-line fallbacks on top of master's version; each is independent |
| `scripts/levels/layer_stack.gd` | `tex()` resolves paths through `Symbols.pick()` | §12.4 `_hist` variants of the C3 flags | if master already does this, keep one call |
| `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd` | Chapter-3 routes, slot-2 save in the station, line-variant checks, protocol puzzle by keys, one find + one chat by keys, „Fortsetzen“ now resumes before `c3b_choose` | E2E drivers must play the whole chain | keep both sides' steps; the C3 phases run after M1 |
| `tests/**` | legacy tests follow the new chain; fixture regenerated from `data/v3` | the demo end moved behind Chapter 3 | after merging data/v3 changes from both sides, re-run `python3 -P tests/reference/make_python_reference.py` |
| `documentation/QUEST_DATABASE.md` | Chapter-3 section between `C3:BEGIN/END` markers (generated), §1 flow, §7.3 note, §10 tests | `test_quest_database.gd` | re-run `python3 -P tools/docs/gen_quest_db_c3.py` |
| `documentation/TECHNICAL_ARCHITECTURE.md` | §13 appended | contract for the new APIs | keep both appended sections |
(The table is completed at the end of the branch — see §3.)

## 2. Behaviour changes a player can notice
* After Chapter 2 the X1 montage still plays, then the game continues into Chapter 3 instead of the end card; the end card
  („Ende der Demo – Fortsetzung in Entwicklung“) now comes after the Chapter-3 opening and lists all four decisions.
* Saves that claim the OLD demo end (`slice_completed` with only A1+M1, scene `L_X1_Montage`) are rejected as inconsistent
  by the unchanged engine; autosaves never store that state, so every save a player normally has stays valid.

## 3. Merge procedure
1. `git merge kapitel-3` into master; resolve the table above.
2. Regenerate: `python3 -P tests/reference/make_python_reference.py`, `python3 -P tools/docs/gen_quest_db_c3.py`,
   `python3 -P tools/docs/build_asset_manifest.py`.
3. `godot --headless --path . --import`, then the three test layers (unit suite, autoplay 4×, inputplay).
