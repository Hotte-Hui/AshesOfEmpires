# Asset manifest part — tasks (side tasks „Aufgaben", TECHNICAL_ARCHITECTURE §12.9, 2026-11-06)

All assets are original and generated deterministically by the script below (licence: project-owned, no
third-party material, nothing downloaded, copied or traced). A re-run reproduces every file byte for byte (seeds
are crc32 of fixed names; no wall clock, no `hash()`).

## Generator
| Command | Writes |
|---|---|
| `py -3 -P tools/pixelgen/gen_tasks.py [--preview DIR]` | `assets/explore/tasks/berlin_drawing.png`, `assets/ui/tasks/mark_task.png`; `--preview` adds ×3 previews |

Read-only reuse: `tools/pixelgen/explore_berlin.py` (Canvas tone-space painter, ramps, masks, F35 glyphs, paper and
wall helpers — the close-up shares the Berlin archive palette and Bayer dithering; the palette check of that module
runs on the output), `tools/pixelgen/pg.py` (colour helpers), the exploration UI kit colours of
`tools/pixelgen/gen_ui_explore.py` (copper/amber values copied as constants).

## Files
| File | Size | Content |
|---|---|---|
| `assets/explore/tasks/berlin_drawing.png` | 240×150, pixel art 1:1 (shown ×3) | close-up of the find `berlin.task.mittens.door` (task „Zweimal klopfen"): Lotte's folded drawing for the porter on squared school paper with a red margin line, held up in the dim stairwell — the lodge with a wobbly PFÖRTNER sign, the porter with cap and moustache, the radio with its green eye, notes flying out to a sun, signature LOTTE and a heart; coloured-pencil strokes with a child's unsteady line, unfinished colouring. No insignia. |
| `assets/ui/tasks/mark_task.png` | 27×27 (9×9 art px ×3, like `assets/ui/explore/icons/mark_new.png`) | HUD prompt marker for the next step of a side task (`Interactable.prompt_state() == "task"`): a hollow amber diamond with a copper rim and a lit core, quieter than the "new find" twinkle. Used by the HUD once the hud.gd patch of the tasks round is integrated. |

## Not assets
Texts: `data/locale/de_tasks.json`. Data: `data/explore/tasks_karsk.json`, `tasks_berlin.json`, `tasks_plaza.json`,
`tasks_veltrava.json`. Hotspots: `exp_task_signalbox` (Karsk), `exp_task_stairwell` (Berlin archive),
`exp_task_coupling` (Veltrava station) in the environments' `explore_hotspots.json`. Visual harness:
`tests/visual/tasks_shots.tscn`.
