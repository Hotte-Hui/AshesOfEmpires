# Evidence-based project status — v0.4

| Output | Actual status | Evidence and next boundary |
|---|---|---|
| Original user art references (four) | Present, reference-only | `references/`, rights unverified |
| Gameplay design, narrative and shot planning | Authored | `docs/`, `narrative/`, `production/` |
| Quest, scene, items, dialogue, puzzles, cinematics, localization | Authored + statically validated | `data/v3/`, `tools/validate_v3.py`, `tools/validate_integrity_v4.py` |
| Story-state engine with actual conversation/puzzle gates | Python tested | `tools/story_engine_v4.py`, `tests/test_story_engine_v4.py` |
| Save corruption detection and v0.3 save migration | Python tested | 34 total offline unit tests including migration/corruption cases |
| All four decision combinations | Python tested and browser smoke tested | `tests/`, `automation/browser_smoke_optional.py` |
| Offline original pixel placeholder interactive preview | Browser smoke tested (Chromium headless on build environment) | `preview/ashes_story_lab_v0.4.html` |
| Production asset registry and shot list | Authored and cross-reference checked | `assets/planned/`, `production/shot_list_v4.csv` |
| Reference image color measurements | Generated from supplied images using PIL median cut | `assets/planned/reference_palette_metrics_v4.json`; approximate palette readings |
| UE5 illustrative C++ seed | Not compiled | `ue5_seed/`; includes v0.3 code requiring replacement/hardening |
| Real UE5 materials, Paper2D scenes, Blueprints, original production 3D assets | Not built | UE5 editor access and real art creation needed |
| Windows playable vertical slice (20–30 min) | Not built | Future engine milestone |
| UHD/4K 60 fps on RTX 4090 | Not measured | GPU benchmark and packaged build required |
| 8–12-hour full game | Long-term goal only | Not implemented |

**There is no claim of a finished, perfect, release-ready game.** This package reaches a useful preproduction/handoff checkpoint; graphics and actual gameplay quality are still gated by implementation and playtesting.
