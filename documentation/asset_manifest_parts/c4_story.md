# Asset manifest part — Chapter 4, part 1 „Stimmen unter Beton“ (Karsk tunnels, Berlin annex) — story stream, round 9

Date for all entries: **2026-11-06**. Everything below is original work for this project, written by hand or produced by
deterministic scripts in this repository; no downloaded images, sounds or samples, no AI image services. Licence:
project-owned, same as the game. Binding design: `documentation/C4_DESIGN.md`.

## Story, presentation and code
| Path | Kind | How it was made |
|---|---|---|
| `documentation/C4_DESIGN.md` | design contract | hand-written; its tables are filled from the same one-off content table that wrote the JSON below (identical texts) |
| `data/v3/*.json` (Chapter-4 entries: 4 scenes, 4 quests, 22 objectives, 15 items, 6 conversations, `pz_c4_routes`, `pz_c4_numbers`, 5 cinematics, 4 events; `L_C3_Quay.next_scene` re-linked), `data/v3/locale_de.json` (`ui.chapter_c4`, `world.c4a`–`c4d`, `obj.c4*`, `choice.c4d.*`, `item.c4_*`, `dlg.c4.*`) | story data, German texts | hand-written; applied to the JSON files by a one-off formatting script (byte-identical round trip of the existing records) |
| `data/chapters/c4.json` (levels, entry spawns, chapter cards, `switches`, palettes `tunnels` / `annex`, grades `tunnels` / `tunnels_siding` / `annex_loop` / `annex`, line expressions/variants, option texts, reactions, puzzle UI and cinematic registry) | presentation rules | hand-written (palette ramps are placeholders for the env streams) |
| `data/locale/de_c4_dialogue.json`, `de_c4_cinematics.json`, `de_c4_ui.json`, `de_c4_characters.json` | German texts (variants, reactions, cinematic lines, both puzzle UIs, memory and task places, new people and journal notes) | hand-written |
| `scripts/story/story_engine.gd` (`LOCKED_CINEMATICS` += 5 ids — validator list only) | GDScript | hand-written one-line extension |
| `scripts/core/game.gd` (`end_card_decisions()`: the end card lists the decisions in story order) | GDScript | hand-written small extension |
| `scenes/levels/L_C4_Tunnels.tscn`, `L_C4_Annex.tscn` | level shells (story interactables, NPC nodes on named hotspots) | hand-written via the content table |
| `assets/environments/karsk_tunnels/scene.json`, `assets/environments/berlin_annex/scene.json` | **placeholder** art manifests (no images: spawns, hotspots, walk band, blockers, zones, NPC anchors) — replaced by the env-tunnels / env-annex streams, which keep every name | hand-written |
| `assets/environments/karsk_tunnels/explore_hotspots.json`, `assets/environments/berlin_annex/explore_hotspots.json` | empty append-only targets for the exploration stream | hand-written |
| `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd` (Chapter-4 routes, both new puzzles by keys, 7-value choice spec, siding quicksave check, „Fortsetzen“ in the annex) | E2E drivers | hand-written extensions |
| `tests/test_c4_routes.gd`, edits of the chain tests, `tests/support/test_kit.gd`, `tests/test_save_rebase_r8.gd` | tests | hand-written |
| `tests/reference/make_python_reference.py` → `tests/reference/python_reference.json.gz` | parity fixture | generator extended by hand; fixture generated from the unmodified preproduction reference engine on `data/v3` (576 routes) |
| `tools/docs/gen_quest_db_c4.py` → `documentation/QUEST_DATABASE.md` §12 | documentation generator | written by hand (reuses the helpers of `gen_quest_db_c3.py`) |

No image, sound or music file was produced by this stream; prints, art, cinematics, puzzle UIs, characters and
audio of Chapter 4 belong to the streams listed in C4_DESIGN §10.
