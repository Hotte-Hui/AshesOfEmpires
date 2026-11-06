# Asset manifest part — Chapter 3, part 2 „Der eiserne Frieden" (registry, fire, quay) — story stream, round 8

Date for all entries: **2026-11-06**. Everything below is original work for this project, written by hand or produced by
deterministic scripts in this repository; no downloaded images, sounds or samples, no AI image services. Licence:
project-owned, same as the game. Binding design: `documentation/C3P2_DESIGN.md`.

## Story, presentation and code
| Path | Kind | How it was made |
|---|---|---|
| `documentation/C3P2_DESIGN.md` | design contract | hand-written |
| `data/v3/*.json` (part-2 entries: 5 scenes, 5 quests, 19 objectives, 10 items, 7 conversations, `pz_c3_check`, 4 cinematics, 5 events), `data/v3/locale_de.json` (`world.c3c`–`c3g`, `obj.c3c_`–`obj.c3g_`, `choice.c3d.*`, `choice.c3g.*`, `item.c3_*` of part 2, `dlg.c3p2.*`) | story data, German texts | hand-written; applied to the JSON files by a one-off formatting script (byte-identical round trip of the existing records) |
| `data/chapters/c3.json` (levels, entry spawns, chapter cards, `switches`, palette `registry`, grades `registry`/`registry_fire`/`quay`, line expressions/variants, option texts, reactions, puzzle UI and cinematic registry of part 2) | presentation rules | hand-written |
| `data/locale/de_c3p2_dialogue.json`, `de_c3p2_cinematics.json`, `de_c3p2_ui.json` | German texts (variants, reactions, cinematic lines, check-puzzle UI, memory and task place names) | hand-written |
| `scripts/core/chapter_ext.gd` (`choice.<objective>` conditions, `level_key` / `same_level` / `scenes_of_level`) | GDScript | hand-written |
| `scripts/story/story_engine.gd` (`LOCKED_CINEMATICS` += 4 ids — validator list only) | GDScript | hand-written one-line extension |
| `scenes/levels/L_C3_Registry.tscn`, `L_C3_Quay.tscn` | level shells (story interactables, NPC nodes on named hotspots) | hand-written |
| `assets/environments/veltrava_registry/scene.json`, `assets/environments/veltrava_quay/scene.json` | **placeholder** art manifests (no images: spawns, hotspots, walk band, blockers) — replaced by the registry / quay art streams, which keep every name | hand-written |
| `assets/environments/veltrava_registry/explore_hotspots.json`, `assets/environments/veltrava_quay/explore_hotspots.json` | empty append-only targets for the exploration stream | hand-written |
| `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd` (part-2 routes, check puzzle by keys, saves in `user://e2e/saves`) | E2E drivers | hand-written extensions |
| `tests/test_c3p2_routes.gd`, edits of the chain tests, `tests/support/test_kit.gd` | tests | hand-written |
| `tests/reference/make_python_reference.py` → `tests/reference/python_reference.json.gz` | parity fixture | generator extended by hand; fixture generated from the unmodified preproduction reference engine on `data/v3` |
| `tools/docs/gen_quest_db_c3.py` → `documentation/QUEST_DATABASE.md` §11 | documentation generator | extended by hand |
