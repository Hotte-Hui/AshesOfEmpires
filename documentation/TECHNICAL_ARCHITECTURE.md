# TECHNICAL ARCHITECTURE — contracts for all contributors

Engine **Godot 4.7.2-stable (standard, GDScript)**, renderer Forward+. Project root `C:\Spiele\AshesOfEmpires`.
This file is the single source of truth for paths, formats and APIs. Change it only together with the code.

## 1. Commands
```bash
GODOT="$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64_console.exe"   # console build (stdout)
"$GODOT" --headless --path /c/Spiele/AshesOfEmpires --import                  # (re)import assets, then quit
"$GODOT" --headless --path /c/Spiele/AshesOfEmpires --script res://tests/run_all.gd   # unit tests (exit 1 on fail)
"$GODOT" --path /c/Spiele/AshesOfEmpires -- --capture=C:/tmp/shot.png --scene=L_A1_Railyard --frames=90
#   ^ windowed run (needs GPU, headless has no renderer): loads a level, waits N frames, saves a 1920x1080
#     screenshot of the composed window and quits.  Extra: --spawn=<name> --cam=<x>,<y> --char=<id>
py -3 -P tools/pixelgen/<generator>.py                                         # art generators (Pillow+numpy)
```
Never run two `--import` passes at the same time on purpose; if an import fails because another process is
writing files, just run it again. Never delete `.godot/`.

## 2. Rendering architecture (LOCKED)
```
Main (Node, scripts/core/main.gd)            scenes/main/Main.tscn — the only main scene
 ├─ WorldView (Control, full rect, clip)     scripts/render/pixel_view.gd
 │   └─ Display (TextureRect)                shows the world viewport texture, nearest, scale ×3, sub-pixel offset
 ├─ World (SubViewport 642×362)              world renders at 640×360 + 1 px margin; 2D and 3D both live here
 │   ├─ LevelRoot (Node)                     current level PackedScene is instanced here
 │   ├─ Camera (Camera2D, scripts/render/world_camera.gd)   integer position; fraction → Display offset
 │   └─ Post (CanvasLayer 100) / Grade (ColorRect, assets/shaders/post_grade.gdshader)  grading, palette snap, grain
 ├─ UI (CanvasLayer 10)                      1920×1080 canvas (stretch canvas_items/keep) — HD UI scenes
 └─ Overlay (CanvasLayer 50)                 fades, letterbox bars, subtitles
```
* `project.godot`: window 1920×1080, `stretch/mode=canvas_items`, `aspect=keep`, default texture filter Nearest.
* Logical world pixel → screen: `screen = (world - camera_topleft) * 3` in UI canvas coordinates
  (`Game.world_to_ui(pos)` does this, including the sub-pixel offset).
* 3D levels (Mode C) are Node3D scenes instanced into the same `LevelRoot`; they own a `Camera3D` (current) and
  their own 3D post-process (full-screen quad, depth/normal outline + palette snap). Their 2D Camera is disabled.

## 3. Level contract
Level scene = `scenes/levels/<LevelId>.tscn`, root script `scripts/levels/level.gd` (class `Level`):
* exports `level_id: String` (e.g. `L_A1_Railyard`), `protagonist: String` (`alexei`/`konrad`/`none`),
  `mode: String` (`oblique` | `side` | `3d` | `cinematic`), `art_manifest: String` (path to scene.json),
  `ambience: String`, `music: String`.
* children: `Backdrop` (Node2D, built at runtime from the art manifest by `scripts/levels/layer_stack.gd`),
  `Playfield` (Node2D, `y_sort_enabled`), `Lights`, `FX`.
* API: `get_spawn(name) -> Vector2`, `get_camera_bounds() -> Rect2`, `is_walkable(pos) -> bool`.

### 3.1 Art manifest — `assets/environments/<env_id>/scene.json`
```json
{
 "id": "karsk_railyard", "palette": "karsk", "world_size": [1920, 360],
 "camera": {"bounds": [0, 0, 1920, 360]},
 "canvas_modulate": "#c8d2d6",
 "layers": [
  {"name": "sky", "file": "sky.png", "pos": [0, 0], "parallax": [0.0, 0.0], "z": -100,
   "normal": false, "emission": false, "lit": false, "repeat_x": 0},
  {"name": "far_city", "file": "far_city.png", "pos": [0, 40], "parallax": [0.15, 0.0], "z": -90,
   "normal": true, "emission": true, "lit": true},
  {"name": "ground", "file": "ground.png", "pos": [0, 0], "parallax": [1, 1], "z": -10, "normal": true,
   "lit": true},
  {"name": "fg_frame", "file": "fg_frame.png", "pos": [0, 0], "parallax": [1.3, 1.0], "z": 60, "lit": false}
 ],
 "props": [ {"name": "wagon_a", "file": "props/wagon_a.png", "pos": [600, 180], "base_y": 262,
             "collision": [[604, 250], [700, 250], [700, 262], [604, 262]], "normal": true, "emission": false} ],
 "walkable": [[0, 250], [1920, 250], [1920, 352], [0, 352]],
 "spawns": {"SP_A1_Platform": [140, 300]},
 "hotspots": {"irina": [520, 296], "seal": [700, 300]},
 "lights": [ {"pos": [520, 230], "color": "#F0C487", "energy": 1.1, "radius": 96, "flicker": 0.08,
              "height": 30, "on_layer": "playfield"} ],
 "fx": [ {"type": "snow", "density": 0.6}, {"type": "smoke", "pos": [1210, 60], "scale": 1.0, "layer": "mid"},
         {"type": "steam", "pos": [880, 260]}, {"type": "fog_band", "y": 230, "height": 40, "color": "#AFC1AA",
          "alpha": 0.35, "parallax": 0.6} ]
}
```
* `camera.bounds` is `[x, y, width, height]` (Rect2 convention).
* All coordinates are **world pixels** of the playfield (parallax 1). `pos` = top-left where the layer sits when
  the camera's top-left is at (0,0). Parallax layer screen x = `pos.x - cam_x * parallax.x`.
  **Required layer width** = `640 + parallax.x * (world_w - 640)` (+ margin); same for height/y.
* `props` are y-sorted sprites inside `Playfield`; `base_y` is the world y of the footprint (sort key).
* Hotspot ids for the slice: Karsk `irina, seal, timetable, signal_board, ledger` (+ optional `obs_*`);
  archive `plan_a, plan_b, overlay_table, emil` (+ optional `obs_*`).
* Each PNG may have `<name>_n.png` (normal, OpenGL +Y up) and `<name>_e.png` (emission mask, drawn unshaded).

## 4. Characters — `assets/characters/<id>/`
* `sheet.png` (+ `sheet_n.png`) with a uniform cell grid; `sheet.json`:
```json
{"id": "alexei", "cell": [32, 56], "origin": [16, 54], "facing": "right",
 "anims": {"idle_side": {"row": 0, "frames": 6, "fps": 5, "loop": true},
           "walk_side": {"row": 1, "frames": 8, "fps": 10, "loop": true},
           "idle_front": {"row": 2, "frames": 6, "fps": 5, "loop": true},
           "walk_front": {"row": 3, "frames": 8, "fps": 10, "loop": true},
           "idle_back": {"row": 4, "frames": 6, "fps": 5, "loop": true},
           "walk_back": {"row": 5, "frames": 8, "fps": 10, "loop": true},
           "inspect_side": {"row": 6, "frames": 6, "fps": 8, "loop": false},
           "interact_side": {"row": 7, "frames": 4, "fps": 8, "loop": false},
           "talk_side": {"row": 8, "frames": 4, "fps": 6, "loop": true}}}
```
  `origin` = feet pixel inside a cell (sprite is drawn with this pixel at the actor position). NPC sheets may omit
  rows they do not need (at least `idle_side`, `talk_side`; civilians at least `idle_side`, `walk_side`).
* `portrait.png`: horizontal strip of 112×112 frames, `portrait.json`:
  `{"size": [112, 112], "expressions": ["neutral", "concerned", "determined", "surprised"]}`.
* Runtime: `scripts/actors/sprite_rig.gd` builds a `Sprite2D` with `CanvasTexture(diffuse, normal)` and plays
  rows by name.

## 5. Autoload singletons (registered in project.godot — do not rename)
| Name | Script | Responsibility |
|---|---|---|
| `Settings` | scripts/core/settings.gd | options, input map (runtime, rebindable), persistence `user://settings.cfg` |
| `Loc` | scripts/story/loc.gd | `Loc.t(key, args := {}) -> String`; merges `data/v3/locale_de.json` + `data/locale/*.json` |
| `Story` | scripts/story/story_engine.gd | authoritative story/quest state (port of `preproduction/tools/story_engine_v4.py`) |
| `Saves` | scripts/core/save_system.gd | slots, autosave, atomic writes, validation via `Story.load_json` |
| `Audio` | scripts/core/audio.gd | ambience/music crossfades, SFX, buses |
| `Game` | scripts/core/game.gd | scene director, protagonist switches, cinematics, world↔UI mapping, capture mode |

### 5.1 `Story` API (GDScript has no exceptions → every mutating call returns `{ok: bool, error: String, ...}`)
`new_game()`, `available() -> Array[String]`, `is_available(obj_id) -> bool`, `objective_state(obj_id) ->
"locked"|"available"|"complete"`, `inspect(obj_id)`, `start_dialogue(obj_id)`, `current_dialogue_line(obj_id) ->
{speaker, text_key, node}`, `advance_dialogue(obj_id) -> {ok, finished}`, `puzzle_attempts(obj_id)`,
`puzzle_hint_available(obj_id)`, `solve_puzzle(obj_id, answer) -> {ok, solved}`, `choose(obj_id, choice_id)`,
`pending_cinematics() -> Array`, `consume_cinematic(id, skipped)`, `finale(skipped)`, `flag(name)`,
`has_item(id)`, `inventory() -> Array`, `choice_history() -> Dictionary`, `current_scene`, `active_character`,
`save_json() -> String`, `load_json(raw) -> {ok, error}`, `journal() -> Dictionary` (objectives with state,
evidence items, people met, decisions). Signals: `objective_completed(id)`, `event_fired(id)`,
`flag_changed(name, value)`, `item_granted(id)`, `cinematic_queued(id)`, `scene_changed(scene_id)`.
Semantics must equal the Python reference (gates, once-only effects, skip equivalence, save validation,
v2→v3 migration). Character id `matthias` from the preproduction package is **renamed `konrad`** everywhere
(user request 2026-11-04); the Python reference in `preproduction/` keeps the old id.

### 5.2 Interaction
`scripts/actors/interactable.gd` (Node2D): `objective_id`, `kind` (`inspect|dialogue|puzzle|choice|observe`),
`prompt_key`, `radius`, `observe_text_key` (for optional observations). The player queries the nearest
interactable whose objective is available (or `observe`). Locked objectives show **no** prompt. Activation
routes through `Game.interact(interactable)` → Story API → UI. Nothing else may complete objectives.

## 6. UI contract — `scenes/ui/*.tscn`, scripts in `scripts/ui/`
All UI is Control-based at 1920×1080, uses `assets/ui/theme.tres`, all text via `Loc.t`. Scenes:
`HUD` (objective tracker, interaction prompt `show_prompt(ui_pos, text)` / `hide_prompt()`, toast),
`DialogueBox` (`show_line(speaker_id, text, expression)`, `show_choices([{id, text}])` → `signal chosen(id)`,
`signal advanced`, history log), `InspectView` (`open(item_id)`), `SignalPuzzle` / `BlueprintPuzzle`
(`open(obj_id)`; submit via Story), `Journal`, `PauseMenu`, `MainMenu`, `SettingsMenu`, `SaveLoadMenu`,
`Credits`, `Subtitles`, `Fade` (`fade_out(t)`, `fade_in(t)`, letterbox). `scenes/ui/UIRoot.tscn` aggregates them
and is instanced by Main under `UI`.

## 7. Audio — `assets/audio/{amb,music,sfx}/*.wav` (44.1 kHz, 16-bit; loops tagged in ASSET_MANIFEST)
Buses: Master, Music, Ambience, SFX, UI (`default_bus_layout.tres`). `Audio.play_ambience(name, fade)`,
`Audio.play_music(name, fade)`, `Audio.stop_music(fade)`, `Audio.sfx(name, volume_db := 0.0, pitch_var := 0.05)`,
`Audio.ui(name)`.

## 8. Data & localisation
Canonical gameplay data: `data/v3/*.json` (schema 3; renamed konrad). New strings go into
`data/locale/de_<area>.json` (one file per contributor area to avoid merge conflicts). German first.

## 9. Tests
`tests/run_all.gd` (extends SceneTree) loads every `tests/test_*.gd` (extends RefCounted, `func run() -> Array`
of failure strings), prints a report and quits with exit code 0/1. Tests instantiate scripts directly
(`load(...).new()`) rather than relying on autoloads.

## 10. Coding rules
GDScript with static types where practical, tabs, no third-party addons. No hard-coded user-facing text.
Pixel layers: texture filter Nearest, positions rounded to integers. Document every generated/downloaded asset in
`documentation/ASSET_MANIFEST.md` (generator script, licence, date).

## 11. Integration addenda (2026-11-04, after the first full integration)
These rules were found by the real-input playthrough (`--inputplay`) and are binding for all new code.
- **Input routing.** Nodes inside the World `SubViewport` receive **no input events** (the viewport is shown via a
  TextureRect, not a SubViewportContainer); they may only *poll* the global `Input` state. Event-driven world input
  goes through `Game._unhandled_input` (root viewport) — e.g. interact → `player.try_interact()`.
- **Interaction cooldown.** After any interaction ends, `Game.interact_ready_at` blocks player interact presses for
  350 ms, so the key that closed a dialogue/panel never re-triggers the next hotspot.
- **Choices.** `DialogueBox` ignores confirm/advance/interact for 450 ms after a choice list appears
  (`CHOICE_GUARD_MS`): a decision can never be taken by a key still being mashed for the previous line.
- **Dialogue placement.** `Game._dock_dialogue()` docks the box at the top (`dialogue.dock_top = true`) whenever the
  speakers' feet are below 60 % of the screen, so the box never covers the people who are talking.
- **Autosave policy.** `Game.autosave()` never writes the finished-demo state (`L_X1_Montage`): "Fortsetzen" resumes
  the last playable moment. After any load, still-queued cinematics are presented (`_after_story_change()`).
- **Saves.** File `user://saves/<slot>.json` = `{meta, story, extra}`; `extra` comes from `Game.save_extra()`
  (scene, player_pos, playtime). `Saves.loaded` is emitted synchronously inside `Saves.load()` and is deliberately
  **not** connected in Game (the caller continues the flow; connecting it would load levels twice).
- **Story API additions** (see `documentation/QUEST_DATABASE.md`): every action returns `{ok, error, error_key}`
  and on success `changes = {flags, objectives, items, events, cinematics, scene}`; accessors `flags()`,
  `relationship()`, `completed_objectives()`, `item_def()`, `puzzle_for()` (no solution), `choices_for()`,
  `snapshot()`, `validate_save_json()`; signal `state_replaced(reason)` on new game / load.
- **Movement.** Walk 45 px/s, run 90 px/s; walk-cycle playback = speed / `sheet.json` `ground_speed` (feet stay
  planted). Side levels use a flat 8×2 collider (their walk band is only ~10 px high).
- **Window focus.** Losing window focus during free play opens the pause menu (disabled in test modes).
- **Grades.** `data/grades.json` `hall_3d` is an identity preset: the 3D hall post shader already outputs final
  palette colours.

### 11.1 End-to-end test drivers
| Driver | What it proves | Command |
|---|---|---|
| `scripts/core/autoplay.gd` | the whole slice through the Story API, all gates honoured, save/load mid-run, all 4 branch combinations, cinematics watched or skipped | `godot --headless --path . -- --autoplay=<a1>,<m1> [--autoplay-skip] [--autoplay-shots=DIR]` |
| `scripts/core/inputplay.gd` | the whole slice through **synthetic key presses only**: menu, disclaimer, intro skip, journal, pause, walking, every interaction, both puzzle UIs (one wrong attempt each), choices by arrow keys and number keys, cinematics, end card, "Fortsetzen" | `godot --path . -- --inputplay=<a1>,<m1> [--inputplay-skip] [--inputplay-shots=DIR]` |
