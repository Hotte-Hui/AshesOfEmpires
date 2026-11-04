# ASHES OF EMPIRES: THE LAST WINTER — PREPRODUCTION v0.4

**Current prepared handoff · German-first · 4 November 2026**

> **Not a finished Unreal Engine game.** This package is a concrete, versioned development preparation: design docs; four user-provided reference images used only for style research; canonical v3 data; a more strictly checked v4 reference quest engine; an offline browser-based story-lab with original placeholder pixel scenery; production asset/shot registries; 34 offline automated Python tests; optional browser smoke tests; and an uncompiled UE5 C++ starting point. There is **no** proof of UE5 compilation, imported assets, Windows packaging or 4K/60 performance.

## Open this first
- **Windows:** `START_HERE_WINDOWS.md` → `CLAUDE.md` → `production/FIRST_72_HOURS_AT_PC.md`.
- **Immediately try the concept:** open `preview/ashes_story_lab_v0.4.html` in a normal browser, offline. It offers actual clicks through dialogue, evidence, symbol and plan puzzles, two decisions per protagonist, a finale, journal, and JSON save export. The scenery is deliberately **original placeholder work**, not source-image replication.
- **Full offline verification:** from the extracted project root, run `powershell -ExecutionPolicy Bypass -File .\automation\verify_windows.ps1` or execute the individual commands below. This script does **not** install anything or modify UE5.
- **Claude Code entrypoint:** start Claude Code in this folder and instruct it to read `CLAUDE.md`. Do not use old v0.3 handoff as the only entrypoint.

## Canonical contents and precedence
1. **Creative canon:** `technical/DECISION_LOG.md`, `docs/STORY_BIBLE.md`, `docs/WORLD_RULES_AND_TIMELINE.md`, `docs/ART_DIRECTION.md`.
2. **Canonical gameplay content:** `data/v3/*.json` (the schema remains **v3**; v4 is the stronger runtime/toolchain, not a silent incompatible data migration).
3. **Current trusted reference behavior:** `tools/story_engine_v4.py`, `tools/validate_integrity_v4.py`, and `tests/`. The previous `tools/simulate_slice.py` is retained for **legacy save migration tests**, not production API design.
4. **Current visual and engineering handoff:** `technical/UE5_RENDERING_ACCEPTANCE_V4.md`, `technical/QUEST_RUNTIME_INTEGRATION_V4.md`, `production/` plus `assets/planned/`.
5. **UE5 seed:** `ue5_seed/` is **uncompiled illustrative code**, not a ready-built game. It includes public completion hooks that must be replaced by the stricter v4 contract before real gameplay.

## Commands (Python 3.10+)
```powershell
py -3 tools/validate_v3.py
py -3 tools/validate_integrity_v4.py
py -3 tools/story_engine_v4.py
py -3 -m unittest discover -s tests -v
py -3 tools/build_preview_v4.py
```
Only standard-library Python is required for the commands above. `tools/generate_production_manifests_v4.py` requires Pillow **only if you choose to rerun image color analysis**; generated CSV/JSON manifests are already included. Optional real-browser tests need Playwright and locally installed Chromium; they are not required to validate the story data.

## Planned gameplay and graphics
- 1964 **fictional alternate history**, critical of dictatorships and oppression; Soviet railway engineer Alexei Morozov and German architect Matthias Adler investigate a dual-use reconstruction registry.
- High-detail, deliberately hand-composed pixel art: hybrid 2D, oblique 2.5D, selective 3D, two micro-scenes as lookdev benchmarks; UE5 as the game engine, Blender as an optional asset tool.
- First real deliverable: a **20–30 min** Windows vertical slice with two scripted protagonist segments, real investigations, choices, accessible dialogue, save/load and transitions. Full six-chapter scope is future work.

## Legal/ethical boundary
`references/reference_*.jpeg` are user-supplied visual references with **unverified redistribution rights**. Keep them internal for lookdev. Do **not** import the pictures wholesale into a public game or claim rights to third-party artwork. All new production visuals, sound and logos require proper provenance. Historical facts and fictional divergence must remain clearly distinguished.

See `PROJECT_STATUS.md` and `BUILD_VERIFICATION.txt` for evidence-based truth about what was and was not tested.
