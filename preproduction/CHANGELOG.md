# Change log

## v0.4 — 2026-11-04
- Retained all human-readable v0.3 design files, the four style references, canonical `data/v3/*.json`, browser v0.3 preview and uncompiled illustrative UE seed.
- Added `tools/story_engine_v4.py`: **actual dialogue-node progression, typed puzzle-answer verification, clue gates, choice-only transactions, event-based scene switching, idempotent cinematic consumption, canonical save format version 3, atomic reload/corrupt-save rejection and v0.3 save v2 migration**.
- Added independent `tools/validate_integrity_v4.py` checking quest-to-scene links, impossible objective dependencies, clue reachability, dialogue cycles, cinematic triggers, production asset references and shot IDs.
- Added an original, self-contained offline browser Story Lab with 2D pixel placeholder scenes for Karsk and Berlin, all 11 goals, both puzzles, two choice points, evidence journal, export/import state and finale. Its scene art is **not** the target final art and contains no copied reference image pixels.
- Added `tools/build_preview_v4.py` to regenerate the offline HTML directly from canonical JSON.
- Added browser verification across **all four** branching routes (optional test tool; needs Playwright/Chromium); 34 standalone Python regression unit tests in aggregate.
- Added asset registry (30 prospective items), production shot list (15 shots), four-reference approximate color measurements, UE5 lookdev testing protocol, narrative consequence matrix, integration API contract, initial PC production milestones and risk register.
- Updated `README.md`, `CLAUDE.md`, `START_HERE_WINDOWS.md`, `PROJECT_STATUS.md` with truthful output classifications.
- **Not done:** UE5 compile, actual production asset modeling, gameplay build packaging, external sensitivity/legal approval, 4K/60 bench.

## v0.3
- Canonical normalized v3 story data, basic Python runtime and 13 unit tests, scene bible, detailed vertical-slice screenplay, initial UE5 seed.

## v0.2
- 28-file planning baseline with user-supplied reference images and initial narrative/QA.
