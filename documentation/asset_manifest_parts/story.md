# Asset manifest part — story_engine area (code, data, tests, docs)

Date for all entries: **2026-11-04**. Author: story_engine specialist (Claude) for ASHES OF EMPIRES. No third-party
code, libraries or downloaded material; no network access was used. All files are original work for this project
(licence: project-owned, same as the game). The behavioural reference is the project's own preproduction package
(`preproduction/tools/story_engine_v4.py`, `simulate_slice.py`, `validate_v3.py`, `validate_integrity_v4.py`,
`preproduction/tests/*.py`), which was read and executed but not modified.

| Path | Kind | How it was made | Provenance / licence |
|---|---|---|---|
| `scripts/story/story_engine.gd` | GDScript, autoload `Story` | Hand-written port of `story_engine_v4.py` (+ data validators ported from `validate_v3.py` / `validate_integrity_v4.py`, Python-compatible JSON reader/writer) | original, project-owned |
| `scripts/story/loc.gd` | GDScript, autoload `Loc` | Extended the lead's stub (kept `t/has/reload`; added `t_or`, `keys`, `missing`, `source_of`, `overrides`) | original, project-owned |
| `scripts/core/save_system.gd` | GDScript, autoload `Saves` | Hand-written (slots, atomic write + `.bak`, validation through Story) | original, project-owned |
| `data/locale/de_system.json` | German system strings (`sys.*`) | Hand-written; character notes paraphrase `preproduction/docs/CHARACTER_BIBLE_V3.md` with the Konrad rename | original text, project-owned |
| `documentation/QUEST_DATABASE.md` | Design documentation | Hand-written from `data/v3` and `preproduction/narrative/*`; German lines quoted from `data/v3/locale_de.json` | project-owned |
| `tests/run_all.gd` | Test runner (SceneTree) | Hand-written | original |
| `tests/support/test_kit.gd` | Test helpers | Hand-written | original |
| `tests/support/legacy_runtime_v2.gd` | Test fixture: v0.3 runtime | Hand-written port of `preproduction/tools/simulate_slice.py` | original |
| `tests/test_story_engine_v4.gd`, `tests/test_data_and_runtime.gd`, `tests/test_integrity_v4.gd` | Tests | Ports of `preproduction/tests/*.py` (all 34 tests) | original |
| `tests/test_autoloads.gd`, `tests/test_reference_parity.gd`, `tests/test_branches.gd`, `tests/test_signals.gd`, `tests/test_journal.gd`, `tests/test_engine_api.gd`, `tests/test_saves.gd`, `tests/test_loc.gd`, `tests/test_rename_guard.gd`, `tests/test_quest_database.gd`, `tests/test_json_compat.gd` | Tests | Hand-written | original |
| `tests/reference/make_python_reference.py` | Fixture generator (Python 3.13, stdlib only) | Hand-written; imports the unmodified preproduction reference | original |
| `tests/reference/python_reference.json.gz` | Generated test fixture (gzip JSON, ~65 KB) | **Generated** by `py -3 -P tests/reference/make_python_reference.py` (Python 3.13.17, deterministic: sorted keys, gzip mtime 0) from the preproduction reference implementation with the protagonist id mapping derived from the data | derived from project-owned code/data |
| `tests/reference/.gdignore` | Keeps the generator/fixture out of the Godot editor scan | — | — |

Regenerate the fixture after any change to `data/v3/*.json` or the preproduction reference; `tests/test_reference_parity.gd`
fails with "unchanged since the fixture was generated" until it is regenerated.
