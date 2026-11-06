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

## 2. Rendering architecture (round 2: smooth hi-res world path)
```
Main (Node, main.gd)
 ├─ World (SubViewport)        hi-res: (640+2)k x (360+2)k, transparent, snap_2d_transforms OFF, vertices ON
 │   ├─ LevelRoot              levels / 2D cinematics / the 3D hall
 │   ├─ Camera (world_camera)  zoom = k, position = drawn - (1,1)   (1 world px overscan margin)
 │   └─ Post/Grade (ColorRect) in-viewport post: low-res path only (hidden in hi-res)
 ├─ Graded (SubViewport)       hi-res only: GradeStage (TextureRect = World texture, grade material, from_texture)
 ├─ WorldView/Display          shows Graded (hi-res) or World (low-res) at canvas -3,-3, size 1926x1086
 ├─ UI (CanvasLayer 10), Overlay (CanvasLayer 5)   unchanged
```
* **k = `Game.view.world_scale`** = round(3 × window content scale) when that is an integer and the stretch offset
  is whole (1080p → 3, 1440p → 4, 2160p → 6, 720p → 2): the world maps **1:1 onto physical pixels**. Other sizes:
  k = floor(3 × scale), stretched by the canvas (old behaviour). Re-evaluated on every window resize.
* **Camera**: `pos` continuous top-left (world px); `drawn` = `pos` rounded to 1/k world px; everything that is
  positioned by the render code lands on whole viewport pixels → camera, parallax and actors move in **single
  screen pixels**, texels stay crisp k×k blocks. `Game.world_to_ui()` unchanged (uses `drawn`).
* **Snapping**: Godot's `snap_2d_transforms_to_pixel` snaps in *world units* (verified by
  `camera_snap_probe`), so it is **off** in the hi-res path; `snap_2d_vertices_to_pixel` stays on. Free-moving
  nodes are rasterised on the nearest viewport pixel.
* **Low-res path** (any Node3D in LevelRoot, e.g. the Great Hall; also legacy `--capture-world` runs, see below):
  642×362, zoom 1, pixel-locked gameplay camera, sub-pixel remainder of cinematic moves and of the hall's lens
  shift via `PixelView.set_fraction` — identical to the round-1 pipeline.
* **Post** (`post_grade.gdshader`): palette snap + 4×4 Bayer, grade, vignette dither and grain are evaluated per
  world texel (`px_scale` = k, `dither_origin` = camera in viewport px). The dither threshold comes from the
  **texel code** that opaque sprites write into the framebuffer alpha (`pixel_sprite.gdshader`, 16 levels in
  0.03..0.87): the dither sticks to each layer's/actor's own texels → no dither crawl on parallax layers during
  pans, no 1-px slivers on actors between world pixels. Pixels without a code (alpha ≤ 0.02 or ≥ 0.97: other
  materials, translucent overlays over nothing, empty background) fall back to a playfield-anchored Bayer.
  `hint_screen_texture` copies force alpha = 1 (verified by `camera_alpha_probe`), hence the second stage.
* **World sprite materials** (assigned by PixelView to every Sprite2D/AnimatedSprite2D entering the World without
  a material of its own; layer_stack assigns them with plane-consistent `dither_anchor`): opaque binary-alpha
  textures → coded material (`TexelLight.coded_material()`); translucent lit sprites → per-texel lighting only.
  Coded sprites are watched every frame and fall back to normal blending while their effective modulate alpha
  < 1, so fades keep working. A node that brings its own material is never touched.
* **Followed actor**: `player.gd` interpolates its drawn position between the last two physics states
  (`get_visual_position()`), the camera chooses its pixel (`draw_pos_for`): it keeps its screen pixel while
  camera and player move together (TARGET_TOL 1 screen px), keeps its world pixel while standing and never steps
  back against its walking direction.
* **Follow model**: dead zone (6×4 px), look-ahead 40 px after 10 px of committed walking direction (own
  critically damped spring ω = 2.1/s, held when stopping), exact critically damped spring ω = 5.2/s (no
  overshoot, frame-rate independent). `reduced_motion`: ω ×2, look-ahead ×0.6 (ω ×2.2), dead zone ×0.6.
  `tween_to` keeps its API (Tween on `pos`, sub-pixel smooth); `release()` / `set_top_left()` stop a running
  `tween_to` tween.
* **Screen-space content inside the World** (a CanvasLayer under a level or cinematic laid out for 642×362) is
  scaled by k automatically (meta `pv_no_autoscale` opts out). `get_viewport().get_visible_rect()` inside the
  World returns the hi-res size — use `Game.view.world_scale` if a script needs it.
* Full detail (public APIs, scene.json `decals` / `blend` / `alpha` schema, measurements):
  `documentation/asset_manifest_parts/render-camera.md`.

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
* Round 7 (characters): optional rows `talk_front` (every sheet with `idle_front`) and `talk_back` (protagonists),
  always appended after the existing rows (row indices never move). `sprite_rig.view_hint` = `"front"`/`"back"`
  maps requests for `*_side` rows to that view when the sheet has it (the player sets it from its facing view, a
  front-on NPC from its idle), so `play("talk_side")` from dialogue code shows `talk_front` for an actor facing the
  camera. `turn_to(left, hold, row)` = soft turn through an in-between row (`idle_front`, or `walk_front` for a
  walking turn); the player turns softly too (`player.face(dir, soft := true)`, `face_point()`, `get_view()`).
  Front / back walks keep one foot on the origin row in every frame. Details: `asset_manifest_parts/characters_r7.md`.

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
v2→v3 migration). The German protagonist's character id from the preproduction package (its draft name)
is **renamed `konrad`** everywhere (user request 2026-11-04); the Python reference in `preproduction/` keeps
the old id (tests/test_rename_guard.gd derives it from there instead of spelling it).

### 5.2 Interaction
`scripts/actors/interactable.gd` (Node2D): `objective_id`, `kind` (`inspect|dialogue|puzzle|choice|observe`),
`prompt_key`, `radius`, `observe_text_key` (for optional observations). The player queries the nearest
interactable whose objective is available (or `observe`). Locked objectives show **no** prompt. Activation
routes through `Game.interact(interactable)` → Story API → UI. Nothing else may complete objectives.

## 6. UI contract — `scenes/ui/*.tscn`, scripts in `scripts/ui/`
All UI is Control-based at 1920×1080, uses `assets/ui/theme.tres`, all text via `Loc.t`. Scenes:
`HUD` (objective tracker, interaction prompt `show_prompt(ui_pos, text)` / `hide_prompt()`, toast),
`DialogueBox` (`show_line(speaker_id, text, expression)`, `show_choices([{id, text}])` → `signal chosen(id)`,
`signal advanced`, history log), `InspectView` (`open(item_id)`; at 125 / 150 % text the record card widens
beside the document, scrolls inside when still too tall and takes over a caption too long for the room under the
document — tests/test_inspect_fit.gd), `SignalPuzzle` / `BlueprintPuzzle`
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

## 12. Exploration layer, symbols & expansion round 2 (contract, 2026-11-04 evening)
Goal of this round (user request): ~10 minutes of high-quality content; better characters and faces; more
detail and life (busier streets); a smoother camera; much more to explore (details, animations, effects,
hiding places, easter eggs, real post-war historical findings about the Nazi state and the Soviet Union,
e.g. in a library); softer protagonist transitions in story and animation; real regime insignia where the
symbolism matters (with a switch).

### 12.1 Exploration data (`Explore` autoload, `scripts/core/explore.gd`)
Optional content NEVER touches the canonical `Story` state. Files in `data/explore/` (one owner per file):
```json
{ "area": "karsk",
  "entries": [
    { "id": "karsk.cat",                 "kind": "detail|secret|easter_egg|chat",
      "level": "L_A1_Railyard",          "title_key": "explore.karsk.cat.title",
      "text_key": "explore.karsk.cat.text",          "prompt_key": "explore.karsk.cat.prompt",
      "image": "res://assets/explore/karsk/cat.png", "history": ["hist.soviet.gulag"],
      "lines": [ {"speaker": "vendor", "key": "explore.karsk.vendor.l1", "expr": "neutral"} ] } ] }
```
`image` (optional) = pixel-art close-up ≤ 320×200, shown ×3. `history` (optional) = real-history cards unlocked
by this find. `lines` only for kind `chat` (speaker = character id; `alexei`/`konrad` = player).
History files `data/explore/history_reich.json` / `history_soviet.json`:
`{"side": "reich", "cards": [{"id", "side", "title_key", "text_key", "year": "1947", "sources": [{"label", "url"}]}]}`.
Strings: `data/locale/de_explore_<area>.json`, `de_history_<side>.json` (format `{"locale","area","strings":{}}`).
API (keep): `find(id) -> {ok,new,entry,cards_new}`, `is_found`, `entry`, `card`, `counts(area_or_level)`,
`history_counts()`, `chat_lines(id)`, `prompt_for(id)`, `state()/restore()/reset()`, signals `found`,
`history_unlocked`, `state_changed`. Saved in the save file's `extra.explore`.
Interactables: `kind = "discover"` or `"chat"` with `explore_id`; Game presents them (`_do_discover` opens
`ui.discovery.open(id, cards_new)` and awaits `closed`; `_do_chat` speaks `lines` via the DialogueBox).

### 12.2 Hotspot names (art ↔ content contract)
Exploration hotspots come from `<env>/scene.json` (art owner) or `<env>/explore_hotspots.json` (content owner,
merged by `Level`, scene.json wins on name clashes). Interactive ambient life is declared in scene.json
`"actors": [{"scene": "res://…tscn", "pos": [x,y], "props": {}}]` (self-contained scenes, instanced into the
y-sorted Playfield). The art owners MUST provide these named hotspots (position = where the player stands to
look at the thing, inside the walkable area); content owners rely on exactly these names:
- **Karsk** (`karsk_railyard/scene.json`): `exp_cat`, `exp_crows`, `exp_snowman`, `exp_stash` (hidden),
  `exp_loudspeaker`, `exp_newspaper`, `exp_mitten`, `exp_kontora_shelf`, `exp_grain`, `exp_cooling_towers`,
  `exp_barrack`, `exp_wagon_chalk`, `exp_banner`, `exp_workers`, `exp_stall`, `exp_stairs_under` (hidden),
  `exp_distant_train`.
- **Berlin** (`berlin_archive/scene.json`, incl. the new library/reading room): `exp_lib_shelf_1` … `exp_lib_shelf_5`,
  `exp_lib_hidden` (hidden), `exp_card_catalogue`, `exp_librarian_desk`, `exp_reading_table`, `exp_globe`,
  `exp_poster_aufbau`, `exp_photo`, `exp_master_plan`, `exp_pneumatic_tube`, `exp_radio`, `exp_mouse`,
  `exp_pigeons`, `exp_coat_stand`, `exp_porter`, `exp_clock`, `exp_heater`; spawn **`SP_M1_Arrival`** just inside
  the stairwell door (Konrad's new entrance; `SP_M1_Office` stays).

### 12.3 Real-history cards (fixed ids → placement)
| id | topic (post-war findings / disclosures) | found at |
|---|---|---|
| `hist.reich.germania` | Speer's "Welthauptstadt Germania" plans and the real Große Halle design | Berlin `exp_poster_aufbau` |
| `hist.reich.evictions` | GBI evictions of Jewish Berliners for Germania; the sanitised office chronicle | Berlin `exp_photo` |
| `hist.reich.schwerbelastungskoerper` | 1941 load-test body in Tempelhof and what it proved | Berlin `exp_master_plan` |
| `hist.reich.wannsee` | Wannsee protocol, the copy found in 1947 | Berlin `exp_lib_shelf_1` |
| `hist.reich.reichsbahn` | Deportation trains, Reichsbahn timetable orders as evidence | Berlin `exp_lib_shelf_2` |
| `hist.reich.generalplan_ost` | Generalplan Ost planning documents | Berlin `exp_lib_shelf_3` |
| `hist.reich.t4` | "Aktion T4" murders of patients | Berlin `exp_lib_shelf_4` |
| `hist.reich.forced_labor` | Forced labour; compensation only from 2000 | Berlin `exp_lib_shelf_5` |
| `hist.soviet.secret_protocol` | Secret protocol of Aug 1939, denied until 1989 | Karsk `exp_kontora_shelf` |
| `hist.soviet.katyn` | Katyn massacre, Soviet cover-up, admission 1990 | Karsk `exp_newspaper` |
| `hist.soviet.deportations` | Deportations of whole peoples in freight trains | Karsk `exp_wagon_chalk` |
| `hist.soviet.novocherkassk` | Novocherkassk 1962: strike, shootings, cover-up | Karsk `exp_workers` (chat) |
| `hist.soviet.kyshtym` | Kyshtym/Mayak 1957 disaster and closed cities | Karsk `exp_cooling_towers` |
| `hist.soviet.gulag` | Gulag figures from the opened archives | Karsk `exp_barrack` |
| `hist.soviet.great_terror` | Great Terror 1937–38 (Order No. 00447) | Karsk `exp_banner` |
| `hist.soviet.holodomor` | Famine 1932–33 and its concealment | Karsk `exp_grain` |
| `hist.soviet.repatriation` | Forced repatriations after Yalta 1945–47 (Lienz, „Operation Keelhaul“), widely known only in the 1970s | Veltrava station `exp_return_notice` (Chapter 3, `data/explore/c3_history_soviet.json`) |
| `hist.soviet.handover_1940` | NKVD handovers of German/Austrian prisoners to the Gestapo at Brest-Litovsk 1939–41 (M. Buber-Neumann) | Veltrava palais `exp_treaty_shelf` (Chapter 3) |
| `hist.reich.nuremberg_interpreters` | Simultaneous interpreting at the Nuremberg IMT trial 1945–46 | Veltrava palais `exp_headsets` (Chapter 3, `c3_history_reich.json`) |
| `hist.reich.census_1939` | The census of 17 May 1939 and its „Ergänzungskarte“ on descent (≈ 277 500 people of Jewish descent registered; Aly/Roth 1984; the surviving cards in the Bundesarchiv) | Registry `exp_card_konrad` — Konrad's own index card (Chapter 3 part 2, `c3p2_history_reich.json`) |
| `hist.soviet.filtration` | NKVD checking-and-filtration of returning POWs and „Ostarbeiter“ 1945–46: presumption of guilt, army/labour battalions, > 200 000 handed to the NKVD, unrecognised until 1991 | Registry `exp_card_alexei` — Alexei filed as „Begleitperson“ (Chapter 3 part 2, `c3p2_history_soviet.json`) |
| `hist.soviet.order_270` | Order No. 270 of 16 Aug 1941: captured officers as deserters, families arrested or without support; read to every company, published 1988; ≈ 3 of up to 5.7 million Red Army POWs died in German captivity; secret resolution of 29 Jun 1956, decree of 24 Jan 1995 | Tunnels `exp_lev_photo` — Lev's granddaughter turned down (Chapter 4 part 1, `c4_history_soviet.json`) |
| `hist.soviet.special_settlements` | The special-settlement regime (decree of 26 Nov 1948: exile „forever“, 20 years for escape) and the unequal returns: Soviet Germans released 13 Dec 1955 without return or compensation, five peoples' autonomies restored 9 Jan 1957, Volga Germans exonerated 29 Aug 1964 (made known Jan 1965), Crimean Tatars back only from 1989 | Tunnels `exp_stovepipes` — the kit that turns a freight wagon into a wagon for people (Chapter 4 part 1) |
| `hist.reich.ostarbeiter` | The „Ostarbeiter“ decrees of 20 Feb 1942: almost three million Soviet civilians, raids, the OST badge, fenced camps, special tax, contact ban, death penalty for intimacy, forced abortions and the „Ausländerkinder-Pflegestätten“ | Annex `exp_wallpaper` — Anna's embroidered towel on the party wall (Chapter 4 part 1, `c4_history_reich.json`) |
| `hist.reich.denunciation` | Denunciation: the small Gestapo (Würzburg: about twenty officials for all of Lower Franconia) depended on reports from the population — Gellately 1990 (more than half of the Würzburg „Rassenschande“ cases began with one), Mallmann/Paul 1991 (Saarland); the Heimtücke law, the Nuremberg laws, the radio ban and the contact ban as occasions; private motives; the objections of Johnson / Evans | Annex `exp_waiting_bench` — the bench „Warten bis zum Aufruf“ beside the counter where Konrad is asked for a name (Chapter 4 part 1, `c4_history_reich.json`) |
Cards are real-world history, presented OUTSIDE the fiction ("REALE GESCHICHTE"), sober, sourced, 450–800
characters, never celebrated (no fanfare, no "achievement" language; neutral paper sound).

### 12.4 Historical insignia switch
Setting `historical_symbols` (default **on**). Assets showing real insignia exist as a neutral/fictional file
`name.png` plus `name_hist.png`; every loader resolves paths through `Symbols.pick(path)`
(`scripts/core/symbols.gd`). Insignia appear only as in-world iconography of the regimes (Great Hall banners,
eagle, official stamps, posters, Soviet banner/locomotive/stamps) inside the critical narrative (StGB §86 Abs. 4
social-adequacy clause) — never in menus, the UI chrome, rewards or as decoration of the player's side.
Neutral variants: Berlin → the fictional "Reichssiegel" / a plain eagle without swastika; Karsk → a fictional
gear-and-wheat emblem.

### 12.5 Cinematic scenes (transitions)
`scenes/cinematics/<name>/<Name>.tscn`, root `Node2D` script with `signal finished`, `configure(ctx)` (ctx =
`{"choices": Story.choice_history(), "flags": {…}, "symbols": bool}`), `play()`, `skip()` (idempotent; `finished`
exactly once). Rendered in the world viewport under `Game.level_root`; camera via `Game.camera`
(`set_top_left`, `tween_to`, `release`); subtitles via `Game.subtitle(text, dur)`; audio via `Audio`.
- **Chapter-3 cinematics** (`LS_C3_Trains` 25.5 s, `LS_C3_ToHall` 6 s, `LS_C3_Close` 12 s; owner: cinematics stream)
  extend `scenes/cinematics/ch3_common/c3_cinematic.gd`: every frame is a pure function of the timeline (`seek(t)`,
  `advance(dt)` for tools/tests), a sorted cue list fires once while playing (`say`, short `sfx`, `bed` = longer sounds
  on the scene's own player that `skip()` fades, `amb`, `music`, `loop`), `reduced_motion` (Settings or
  `reduced_motion_override`) halves travel, drops jolts/roll and softens flashes; shot groups dissolve with
  `c3_dissolve*.gdshader` (one Bayer cell per world pixel, `px_scale` = `Game.view.world_scale`). Art and anchors come
  from `py -3 -P tools/pixelgen/env_veltrava_cine.py` (`assets/cinematics/ch3/**`, `layout.json`), sound from
  `tools/audiogen/c3_cine_audio.py`; review harness `tests/visual/c3cine_harness.tscn` (`--c3-mode=shots|seq|run`).
- **Chapter-4 cinematics** (`LS_C4_Homeward` 14 s, `_Number` 13 s, `_Card` 11 s, `_Stamp` 11 s, `_Voices` 24 s; owner:
  cine stream, round 9) extend `scenes/cinematics/c4_common/c4_cinematic.gd` (on top of the C3P2 base): lengths = the
  registered shot sheets, hard match cuts on shared objects (the stencilled 45, the mirrored perforation of card 0417,
  the stamp frame), subtitles timed by `line_dur()` (≤ 19 chars/s), wide-shot figures = the game's own sheets re-lit
  from their normal maps (`env_c4_cine_kit.relight`), close-ups from the portrait SDF pipeline; `optional_music()` cues a
  track only when it exists. Art: `py -3 -P tools/pixelgen/env_c4_cine.py` (`assets/cinematics/c4/**`, `layout.json`),
  sound: `tools/audiogen/c4_cine_audio.py` (`c4cine_*`); same harness (`--c3-id=LS_C4_…`).

### 12.6 New characters (ids)
`librarian` (Berlin), `porter` (Berlin doorman), `vendor` (Karsk tea stall), `worker_b` (Karsk). Chat speakers
with portraits: `alexei`, `konrad`, `irina`, `emil`, `vendor`, `worker_a`, `babushka`, `librarian`, `porter`.

### 12.7 Content rules for this round
No glorification; no false equivalence (each card stands on its own facts); easter eggs and jokes never sit
on atrocity topics; in-world finds speak in the protagonist's voice (Alexei dry and tired, Konrad precise and
euphemistic at first), history cards in a neutral documentary voice. German first. All generators deterministic.

### 12.8 Mini-games (contract; the base is `scripts/ui/minigames/minigame_base.gd`)
An exploration entry may carry `"minigame": "res://scenes/ui/minigames/<Name>.tscn"`: `Game._do_discover` runs it
first (`_run_minigame`: instanced under the UI root, `open({"explore_id", "auto"})`, awaits `finished(success)`);
only success grants the find, failure / Esc grants nothing and the spot can be retried. Scene root extends
`minigame_base.gd` (group `minigame`, modal, pauses the world): `finished(success)` exactly once, `ctx.auto`
resolves after 0.2 s (autoplay), `demo_solve()` solves through synthetic key events only (inputplay), a hint after
2 failures (`register_fail`), Esc / „Aufgeben“ without penalty, keyboard + pad + mouse, text scale and high
contrast. Chapter 3 (round 7, owner minigames r7 V; entries `data/explore/minigames_r7_v.json`, strings
`data/locale/de_minigames_r7_v.json`, tests `tests/test_minigames_r7_v.gd`, captures
`tests/visual/minigames_r7_v_harness.gd` (UI) and `minigames_r7_v_ingame.gd` (real Game path)):
| Scene | Find / hotspot / world cue | Play |
|---|---|---|
| `FlapBoard.tscn` „Die Fallblatttafel“ | `veltrava.station.flap_board` at `exp_flap_board` (548, 304); `FlapBoardCue` = arrivals board on canopy column 3 (jammed → restored) | six forward-only flap drums with four couplings (carry units→tens, drags tens→hour, from→via, track→via); target = the timetable's special train 8:41 MOSKVA über KARSK, Gleis 5; „Probelauf“ (Enter) names what differs; ×2 compact layout above 100 % text |
| `Cloakroom.tscn` „Die Garderobe“ | `veltrava.hall.cloak_tokens` at `exp_cloak_tokens` (205, 300), beside `veltrava.hall.cloakroom`; `WenzelCue` = Herr Wenzel behind the counter | 2 rounds (4 coats, 3 hats) matched by conference pin (shape), newspaper, scarf; hook numbers mislead; Elena's coat (check 27) stays |

Karsk / Berlin (round 7, owner minigames_r7_kb; entries `data/explore/minigames_r7_kb.json` with per-entry `area`,
strings `data/locale/de_minigames_r7_kb.json`, tests `tests/test_minigames_r7_kb.gd`, real-Game captures
`tests/visual/minigames_r7_kb_shots.tscn`, manifest `asset_manifest_parts/minigames_r7_kb.md`):
| Scene | Find / hotspot | Play |
|---|---|---|
| `MorseKey.tscn` „Der Morsetaster“ | `karsk.morse` at `exp_morse` (590, 256), signal-box corner where the telegraph line comes in | the register prints the dispatcher's telegram (sounder, call lamp); routine ВАГ 24311 is taken down by itself, НЕ ВЗВЕШИВАТЬ is decoded with the wall chart (Russian Morse + international equivalents; only arrived letters); receipt ПР keyed with forgiving timing (< 0.26 s dot, pauses free); the line answers Р |
| `Rohrpost.tscn` „Rohrpost“ | `berlin.rohrpost` at `exp_rohrpost` (932, 300), reading-room information desk under the copper tube | three capsules from the porter's lodge, three boards (2/3/4 knobs; frozen main line; crossing + return line + a knob off the way) from `assets/ui/minigames/rohrpost/rohrpost_layout.json` (verified by `gen_mg_rohrpost.py`); a wrong setting sends the capsule to another office and it comes back |
Both stages are custom-drawn and fit the panel (pixel art ×3, ×2 when short); hints follow Settings `puzzle_hints`.

Palais relay desk (round 7, owner minigames_r7_relay; entry `data/explore/minigames_r7_relay.json`, strings
`data/locale/de_minigames_r7_relay.json`, tests `tests/test_minigames_r7_relay.gd`): `RelayDesk.tscn` „Das Relaispult“,
find `veltrava.hall.relay` at `exp_relay_desk` (1777, 295) in the interpreters' corridor — three rounds at the
technician's desk: switch the floor feed and the booth outputs as the speaker changes language (DE/RU/FR), give the
lamp signals (yellow = slower, red = stop) when a booth falls behind; forgiving timing (`relay_logic.gd`: `PASS`,
`MAX_LOST`, per-round `grace`). Open from `c3b_arrival` until `c3b_inspect_booth` and in memories
(`scripts/ui/minigames/relay_spot.gd`); the drivers explore the hall again when `c3b_inspect_booth` becomes available.

Registry tracing index (round 8, owner exploration c3p2; entry `veltrava.registry.kartei` in `data/explore/c3p2_registry.json`,
strings `data/locale/de_explore_c3p2.json` `mg.kartei.*`, tests `tests/test_c3p2_explore.gd`, art
`tools/pixelgen/gen_mg_c3p2_kartei.py`, sounds `tools/audiogen/mg_audio_c3p2.py`): `Kartei.tscn` „Die Suchkartei“ at
`exp_kartei` (1152, 300) beside drawer C-17 (world cue `KarteiCue`, `kartei_world_cue.gd`: the fallen drawer until the
find) — Konrad files nine cards of the commission's tracing index back into their drawer: origin (B · K · V), year,
running number; five cards were written by Russian clerks (Б/К/В — the В of Veltrava looks like a Latin B); a wrong
gap is refused with the rule it breaks, the card stays in the hand; the side panel reads each card (people searching
across the Line since 1953). Open in scene B (after `c3c_talk_konrad`, until `c3d_choose`). Every registry find uses
`scripts/ui/minigames/kartei_spot.gd` (gated_interactable + `memory_scenes`: inside a memory the remembered scene, not
the objective gates, decides — A: Alexei's yard/Annahme finds, B: Konrad's card hall/Planarchiv/Magazin finds).

Tunnel lever frame (round 9, owner exploration c4; entry `karsk.tunnels.lever_frame` in `data/explore/c4_tunnels.json`,
strings `data/locale/de_explore_c4.json` `mg.lever.*`, tests `tests/test_c4_explore.gd`, art
`tools/pixelgen/gen_mg_c4_lever.py`, sounds `tools/audiogen/mg_audio_c4.py`, capture `tests/visual/c4_explore_shots.gd`):
`LeverFrame.tscn` „Der Hebelrahmen“ at `exp_lever_frame` (1064, 300) in Service Tunnel 3 — Alexei carries out the three
orders of the night shift's route book on a fictional 1941 mechanical frame (`lever_logic.gd`: points w1–w3, route
levers a/b/c, signals s1/s2; a route needs its points and holds them, b and c exclude each other, a signal needs its
route and holds it, signals always go back; 3 + 7 + 5 moves, no dead end from any of the 256 positions): entry to
track 1, exit to the main line (flank protection: points 1 reversed), then lever 6 without a plate — its route lights
the indicator „КОРДОН 17“ (why the wagons are missing from the signal-box book). Refusals name the lock; hints after two
(Settings `puzzle_hints`); keys ←/→ select, ↑/↓/E toggle, 1–8 direct, R restart; pad; mouse; x3 art, x2 + table in
the side column for larger text. Open in scene C (after `c4a_open_door`) and in its memory. Every Chapter-4 find uses
`scripts/ui/minigames/lever_spot.gd` (kartei_spot's gates + a chat on an NPC's spot only while that NPC is present).

Annex ventilation flaps (round-9 fix compl-01, owner exploration c4; entry `berlin.annex.fans` in
`data/explore/c4_annex.json`, strings `de_explore_c4.json` `mg.vent.*`, tests `tests/test_c4_explore.gd` (`vent_*` cases),
sounds `mg_c4_flap_open` / `mg_c4_flap_close` / `mg_c4_alarm_bell` / `mg_c4_air_settled` from
`tools/audiogen/mg_audio_c4.py`, capture `tests/visual/c4_vent_shots.gd`): `VentFlaps.tscn` „Die Lüftungsklappen“ at
`exp_fans` (992, 300) in the machine room of Nebenstelle Süd (scene D, after `c4b_inspect_crates`, and in its memory) —
the fault bell rings; two fans feed one plenum, three ducts leave it (card hall, typists' room, the corridor of the
Staatspolizei), each with a butterfly flap of five positions. `vent_logic.gd`: flow_i = 30 · g_i / (Σg + 2) with
g_i = conductance · position, the corridor duct twice as long (conductance 0.5), so every flap moves all three needles;
Konrad's own Blatt 3 gives 12 000 / 6 000 / 6 000 m³/h ± 1 000; exactly one of the 125 positions balances them (4/2/4),
the night shift left 4/4/0, no dead end. Acknowledging („Störung quittieren“, E/Enter/pad A) out of balance is a refusal
naming the worst duct; hints after two (Settings `puzzle_hints`), the second names the next flap step. Keys ←/→ choose,
↑/↓ open/close a step, 1–3 direct, R restart; pad; mouse (click above / below a flap, wheel, right click closes, the
button acknowledges). The stage is drawn in code (pixel art ×3, ×2 + side sheet for larger text). The reveal: the third
duct's line on Blatt 3 reads „Gang – Warteraum, 14 Plätze“ in Konrad's own hand.

### 12.9 Side tasks („Aufgaben“, round 7, owner: tasks)
A small optional-task layer on top of §12.1 — backward compatible, **no save data beyond `Explore.state()`**
(`{found, cards}`), never Story state.
- **Requirements.** An entry may carry `"requires": [explore ids of the same level]`: it cannot be found
  (`Explore.find()` returns the usual `{ok: false, new: false, entry: {}, cards_new: []}`) and its interactable is
  inactive (no prompt) until all of them are found. `can_find(id)`, `requires_of(id)`.
- **Tasks.** Any `data/explore/*.json` may declare `"tasks": [{id, area?, level, title_key, summary_key,
  steps: [{explore_id, hint_key}], reward_cards?: [card ids]}]` (content: `tasks_<area>.json`, texts
  `data/locale/de_tasks.json`). A task's state is derived from its found step ids: `not_started` (none found),
  `active` (current step = first unfound step; its `hint_key` is the journal hint), `done` (all found). The find
  that completes a task also files its `reward_cards` (part of that find's `cards_new`, so Game shows them like
  any card; `restore()` re-attaches them silently). API: `tasks_for(level_or_area)`, `task(id)`, `task_steps(id)`,
  `task_of(explore_id)`, `task_state(id) -> {state, step, hint_key, done_steps}`, `task_counts(level_or_area) ->
  {done, active, total}`, signal `task_changed(id)` (find / restore / reset; never for unrelated finds).
- **Validation** (`Explore.warnings`): unknown / non-array / self / cross-level `requires`, requirement cycles,
  task steps that are not entries of the task's level, a step in two tasks, steps out of order (a step requiring a
  later one) or an order that is not enforced (step i does not require step i-1, directly or transitively),
  missing title/summary/hint keys or texts, unknown reward cards.
- **Interactables** (`scripts/actors/interactable.gd`): optional `explore_chain: PackedStringArray` — one hotspot
  hosts several entries; `explore_id` always holds the current one (first unfound entry in chain order whose
  requirements are met, else the last found one for re-reading, else the first). In the scene `explore_id` is the
  entry the chain shows in a new game. It follows `Explore.state_changed` / `data_reloaded`, re-arms a `once`
  hotspot for its next entry and takes the kind (`chat` / `discover`) of the current entry. `is_active()` respects
  `requires`. `prompt_state()` adds `"task"` (the next step of a side task; HUD mark
  `assets/ui/tasks/mark_task.png`) next to `"new"` / `"found"`. Pure helper: `Interactable.pick_chain_step()`.
- **Feedback.** `Explore` toasts „Neue Aufgabe: …“ / „Aufgabe erledigt: …“ through `Game.toast()` once the
  interaction is over (after the find's own „Entdeckt“ toast; `notify_tasks = false` in tests). Journal tab
  „Aufgaben“ right after „Ziele“: open tasks first with the current hint („Als Nächstes“), then the finished
  ones, each with place, summary and the steps done so far (re-readable); unstarted tasks stay hidden — only the
  current place says how many people there still wait to be listened to.
- **Placement rule.** A task step sits on a new `exp_task_*` hotspot (`explore_hotspots.json`) or joins the chain
  of an existing hotspot; a task chat on a story NPC's spot is a `gated_interactable` after that NPC's story
  objective. Checked by `tests/test_tasks.gd` (every step placed exactly once, spacing/walk-area rules of the
  area tests, the drivers' loop completes every task in order). Review regressions: `tests/test_tasks_review.gd`
  (only real requires cycles reported, a step listed twice in one task, one toast per task start / finish and none
  on restore/reset, a `once` chain never re-arms for an already found entry, the seven journal tabs fit 1500 px).
- **Drivers.** `--autoplay-explore` / `--inputplay-explore` explore every level at its start, on the parade
  plaza and once more right before each level's final decision (story-gated chats are open then); each pass
  re-collects `autoplay.gd pending_finds()` (active discover/chat hotspots whose current entry is new) until
  nothing new is findable, and the last pass of a level fails if a task of that level is not done.
- **Content (5 tasks, one per walkable level).** Karsk „Ein grünes Signal“ (the grandmother → the signal box →
  the tea vendor → back; a place in the mail train's luggage van), Berlin „Zweimal klopfen“ (the porter → Lotte's
  mittens on the reading-room heater → the stairwell door, her drawing → back), plaza „Ein Bild für die Schublade“
  (the woman from No. 9 → the press photographer → back), station „Wagen drei ist kalt“ (the conductor → the
  frozen heating coupling → hot water from the waiting-room stove → thawing it → back), Palais „Wer zuerst
  zugreift“ (Frau Brunner → the untouched buffet → Nils Ekdahl → back). Rewards are human beats (closing chats,
  one close-up: `assets/explore/tasks/berlin_drawing.png`, `tools/pixelgen/gen_tasks.py`); no new history card.
- **Chapter 3 part 2 (round 8, owner exploration c3p2).** Registry „Die Pforte“ (`veltrava.task.porter`, level key
  `L_C3_RegistryA`, Alexei, `data/explore/c3p2_registry.json`): the porter's thermos (`exp_thermos`) → the radio
  and a ten-Kronen note (`exp_radio`) → the key board, hook „Magazin“ empty (chain on `exp_radio`) → back to the
  booth, the porter's note for his relief (chain on `exp_thermos`): sent home at 23.15 by „a gentleman from the
  secretariat“, he left the money — so whoever wrote Elena's „ab“ at 23.25 was not the porter. An investigation, no
  NPC (the porter is never seen): starts and ends with a find, texts in `de_explore_c3p2.json`, checked by
  `tests/test_c3p2_explore.gd` (test_tasks.gd keeps its round-7 rules for its five levels).
- **Chapter 4 part 1 (round 9, owner exploration c4).** Tram loop „Ilses Puppe“ (`berlin.task.doll`, level key
  `L_C4_AnnexA`, Konrad, scene B only, `data/explore/c4_annex.json`): Marta asks after her loop chat (chain on
  `ChatMarta`: chat → ask → back, after `c4b_talk_ilse` until `c4b_inspect_crates`) → the cellar of No. 11 and its 1941
  wall breakthrough into the sealed No. 9, Ilse's doll on the kitchen bench without an inventory number (one red shoe
  missing -- the hidden find at the step of No. 9), her drawing on the wall (`exp_task_cellar`, close-up
  `assets/explore/c4/ilse_drawing.png`, `tools/pixelgen/gen_explore_c4.py`) → back to Marta: „Was keine Nummer hat, holt
  keiner ab.“ A doll, not the satchel C4_DESIGN §6 names: in `dlg_c4b_ilse` Ilse already holds her satchel. The drivers
  complete it in their pass before `c4b_inspect_crates`; checked by `tests/test_c4_explore.gd`. Transfer siding „Wir sind
  vierzehn“ (`karsk.task.fourteen`, level key `L_C4_TunnelsA`, Alexei, scene C only, `data/explore/c4_tunnels.json`): the
  names in wagon 24 318, read left to right along it — the roof beam through the air hatch (`exp_task_beam`, 1560),
  behind the stove pipe (`exp_task_pipe`, 1616), under the bench through the half-open door (`exp_task_bench`, 1644),
  at the door rail (`exp_task_rail`, 1708): 3 + 4 + 4 + 3 names in two scripts, no real persons — each a `Task_*` node
  after `c4a_open_door`, each step requiring the one before → the hand-in chat with Lev (`ChatLevSiding` on `lev_siding`,
  after `c4a_open_door` until `c4c_talk_lev`): „Vierzehn. Jetzt stehen sie in zwei Papieren.“ The chat node stands
  before `S_c4c_talk_lev` in the level file, so when both are open (names read, wagon inspected) the player's focus rule
  (nearest, then tree order) offers the hand-in first and the story talk right after. The drivers complete it in the
  siding's first pass (before `c4c_inspect_card`); the final pass before `c4c_talk_lev` requires it done.

### 12.10 Memories („Erinnerungen“, round 7, owner: memories)
Revisit a completed scene, look at everything again, return to the present — only completed scenes.
- **Code.** `scripts/core/memories.gd` (pure helper, instance `Game.memories`: scene table, unlock rules, profile,
  read-only echo plans, grade overlay) · `scripts/core/game.gd` (`travel_to_memory()`, `return_from_memory()`,
  `rewatch_film()`, `memory_scenes()`, `memory_films()`, `memory_info()`, `save_block_key()`, signal
  `memory_changed`) · `scripts/ui/memory_view.gd` + `scenes/ui/MemoryView.tscn` (added by `ui_root.gd`,
  `UIRoot.open_memories("game"|"menu")`) · `scripts/core/memory_drive.gd` (E2E helpers + `--memory-demo`).
- **Memory scenes.** Every scene of `data/v3/scenes.json` with a protagonist and an `exit_on_event`, in chain order,
  plus `Memories.SIDE_LEVELS` (`L_M1_Plaza`, unlocked with its parent `L_M1_Archive`). A new chapter appears
  automatically (texts `ui.memories.place|date.<scene>` in `data/locale/de_memories.json`, print
  `assets/ui/memories/<scene>.png`; fallbacks: scene title, no date, unexposed print). The montage never is one.
- **Unlocks.** In the game: `Story.has_event(exit_on_event)` of the running state (`a1_completed`, `m1_completed`,
  `c3a_completed`, `c3b_completed`). From the main menu: the global profile `user://profile.json` (NOT a save):
  `{"version": 1, "completed": {scene: {"t", "story": <Story.save_json() object at the moment of completion>}},
  "explore": {"found", "cards"}}` — recorded on `Story.event_fired` (exit events), seeded from every valid save slot
  at boot and from each loaded save (existing entries are never replaced), written atomically like the slots.
  Only the exported game writes it (feature `template`): runs of the editor binary (tests, harnesses, E2E drivers —
  they share `user://` with the player's build on this machine), automated runs and runs without Main never do,
  unless `--profile=<path>` names a file. Main menu entry „Erinnerungen“ appears once the profile has a scene
  (7 entries: the column moves up).
- **MemoryView.** Page „Orte“: one card per scene (sepia print 320×180, chapter, place, month, protagonist,
  `Explore.counts(scene)`), rows of three; locked = unexposed print + „Noch nicht erlebt“ (no names, no image);
  the scene the player stands in is marked „Hier bist du gerade.“ and cannot be chosen. Page „Filmsequenzen“:
  every cinematic of `data/v3/cinematics.json` whose trigger (event / objective) happened and whose scene exists
  (`LS_A1_ToM1`, `LS_M1_Hall` = reveal + parade, `LS_X1_Final`, the three `LS_C3_*`). Arrows/WASD/pad move,
  Enter/Space/A choose, Q/E or LB/RB switch pages, Esc/B back, mouse hover/click; text scale, high contrast.
- **Travel („Zeitreise“).** Only from free play (pause menu: level loaded, not busy / cinematic / input-locked, no
  transition) or from the main menu. Sequence: every panel closes → `mem_rewind.wav` (clock ticks running backwards)
  → colour drains to sepia with a faint film flicker, scratches and dust (CanvasLayer 89, 3-px grid; none with
  reduced motion) → warm darkroom fade (`MEM_DARK`) → card „ERINNERUNG · place · month“ (on the fade layer) while
  the level loads at its entry spawn (`ENTRY_SPAWN` / ChapterExt / side-level spawn) with the protagonist of THAT
  scene → fade in, film fades out. Return: `mem_return.wav` (ticks forward), drain, darkroom, card „GEGENWART ·
  place“, the present level reloads at the saved position (`side_level` restored, no intro pan / chapter card /
  porter greeting), the colour comes back during the fade-in, objectives refresh, **autosave „memory_return“**.
  reduced_motion (and autoplay) shortens every step; Esc/Space skips like a cinematic. Playtime keeps counting.
- **Grade.** `data/grades.json` `"memory"` is an overlay on the level preset (`Memories.overlay_grade`): lift adds,
  gamma/gain/tint multiply, saturation multiplies (0.28), vignette = max (0.38), grain adds; palette snap kept.
  Cinematics inside a film rewatch keep their own grades. Photo mode reads the memory grade as its base.
- **Rules inside a memory** (`Game.memory_mode`). Story never changes: the present `Story.save_json()` is kept and
  compared on every exit (a difference is restored with `load_json` + warning — a safety net only), and every Story
  path is blocked: `interact()` routes story hotspots to `_do_memory_echo`; `_do_inspect/_do_dialogue/_do_puzzle/
  _do_choice` return at a guard; `_after_story_change()`, `_play_cinematic_by_id()` and the finale do nothing.
  Each story hotspot gets a read-only twin (`interactable.gd`, kind `observe`, meta `memory_objectives`/`memory_kind`;
  a conversation and the decision taken with the same NPC in the same Story scene share one twin; in a level file
  shared by several scenes (§12.11) only the objectives of the remembered scene get twins; a twin steps 24 px aside
  when an active optional hotspot stands on it): inspect → the document again (InspectView); dialogue → the lines replayed from
  `data/v3/dialogue.json` with the flag variants of that playthrough (`Memories.memory_flags`: the profile snapshot
  when its decisions match, else the live flags); choice → „Hier habe ich …“ (`ui.memories.decided.<choice>`) + the
  reaction that followed; puzzle → one remembered line (`ui.memories.echo.<objective>`). Exploration (discover,
  chat, mini-games, side tasks) works normally; **finds are kept** (Explore is never rolled back). No autosave,
  quicksave or manual save (`Saves.save()` refuses with `sys.save.err.memory`; the save screen explains why;
  loading stays possible and makes the loaded save the new present). „Hauptmenü“ from an in-game memory restores
  the present state and leaves the present autosave as it was (finds of the visit are only secured by returning —
  the confirm dialog says so). Exits of side levels lead back to the present. The pause menu shows „ERINNERUNG ·
  name“ and „In die Gegenwart zurückkehren“ (from the menu: „Erinnerung beenden“) instead of „Erinnerungen“; the
  HUD shows the badge „ERINNERUNG · place · month“ with the return hint instead of the objectives.
- **From the main menu.** The scene's recorded Story state is loaded for the visit (NPCs, variants, decisions as
  then) and the Explore state becomes the profile's union of finds; on return the menu's Story and Explore states
  come back and the visit's finds stay in the profile only (the view says: „…bleiben in deinen Erinnerungen
  erhalten, gelangen aber in keinen Spielstand“).
- **Films.** `rewatch_film(id)` unloads the present level, plays the cinematic through the director's own function
  (nothing consumed, `_plaza_after_hall` cleared, Story compared), then reloads the present like a memory return
  (or the main menu).
- **Assets.** Prints: `tests/visual/memory_thumbs.tscn` (capture, `--symbols=0`: no real insignia in a menu) →
  `assets/ui/memories/src/raw_*.png` → `tools/pixelgen/gen_ui_memories.py` (deterministic crop + sepia tone +
  16-tone Bayer print, badge icon). Sounds: `tools/audiogen/memories_audio.py` → `assets/audio/sfx/mem_rewind.wav`,
  `mem_return.wav`. Provenance: `documentation/asset_manifest_parts/memories.md`. Chapter 4 (round-9 fix compl-03):
  `SHOTS` / `CROPS` for `L_C4_TunnelsA`, `L_C4_AnnexA`, `L_C4_TunnelsB`, `L_C4_AnnexB` (camera inside each scene's
  `camera_zones` rect); re-capture with `memory_thumbs.tscn -- --scene=L_C4_TunnelsA --char=alexei --symbols=0
  --capture=<dir>/boot.png --frames=100000 --mt-out=<dir> --mt-only=L_C4_TunnelsA,L_C4_AnnexA,L_C4_TunnelsB,L_C4_AnnexB`,
  copy the raws to `src/`, run the generator, import. The harness loads each scene as a memory of itself, so story NPCs
  follow the remembered state (Lev at his siding post in the TunnelsB print). Story NPCs of the shared levels
  (registry, tunnels, annex) evaluate `show_after` / `hide_after` inside a memory through the level's
  `objective_done` rule (only objectives of scenes before the memory scene count; `StoryNPC._done`); single-scene levels
  keep the live Story, because their conversation twins stand at the NPC spots.
- **Tests / checks.** `tests/test_memories.gd` (unlocks, profile, echo plans for every objective, round trip on the
  live autoloads byte-identical, save guard, view/HUD/pause/save screen headless). GPU check run without touching
  the player's files: `godot --path . -- --memory-demo=all|game|c3|menu|films|view [--memory-shots=DIR]`
  (private `user://memdemo`, prints MEMDEMO_PASS/FAIL). E2E hooks: `--autoplay-memories`, `--inputplay-memories`.

Review additions (round 7): a memory opened from the main menu refuses saving with `sys.save.err.memory_menu` (no
present to return to; its finds live only in the profile). Films from the main menu run with the first profile
snapshot (story order) in which their trigger happened (`Game._film_snapshot`), so they show the decisions of the
playthrough in which they were seen; input stays locked (`in_cinematic`) until the present has faded back in. The film
look stops with the memory (`_mem_film_stop`) and is never drawn while the tree is paused. `Game.side_level` is reset by
a new game and by every loaded save. Drivers: `--autoplay-memories` (round trip at `c3a_talk_conductor`) and
`--inputplay-memories` (keys only, at the start of L_C3_Station) call `scripts/core/memory_drive.gd`.

### 12.11 In-level protagonist switch (round 8, owner: engine)
Control passes between Alexei and Konrad inside ONE level, at an authored story moment — never a menu, no reload.
- **Data.** Consecutive Story scenes may share one level file: `data/chapters/<ch>.json` `"levels"` maps both scene ids
  (e.g. `L_C3_ArchiveA`, `L_C3_ArchiveB`) to the same `res://scenes/levels/<X>.tscn`; each scene keeps its protagonist,
  quest, exit event (`data/v3/scenes.json`; the Story engine and its Python reference are unchanged) and needs its own
  `"entry_spawn"`. Control may go back and forth (A → B → A2 …). Optional per-scene settings in the chapter file's
  `"switches"` section (read through `ChapterExt.switch_settings(id)` / `switch_spawn(id)`, all keys optional):
  `switch_spawn` (where control passes to this scene's protagonist), `partner` (who stands in while this scene is
  played; `"none"` = nobody; default: the protagonist of the chain scene before, when it plays in the same file),
  `partner_spawn` (where he stands: he walks there after the hand-over, is placed there on a load), `partner_anim`
  (idle row, e.g. `work_side`), `partner_hide_after` (objective id: he leaves then), `glide` (s, default 1.2),
  `music` / `ambience` (the scene's own tracks; default the level's).
- **Detection.** `Game.goto_level(next)` → `can_switch_in_level(next)`: a walkable level with a player is loaded, `next` is
  another scene of the same level file (`level_file()`), no memory / return trip / transition, no loaded save
  (`_force_reload`, set by `_on_loaded_slot()` and a new game). Then `_switch_in_level()` instead of a reload.
- **The switch** (`switch_now()` = synchronous part, `_switch_in_level()` = timing). The level node now plays the next
  scene: `level.level_id` / `level.protagonist` follow (drivers, journal, memories, saves read them). The incoming
  protagonist takes over at `spawn` / `switch_spawn` > where he stood in as an NPC (seamless, same facing) > the
  scene's entry spawn. The outgoing body `retire()`s (leaves the "player" group at once, frees itself at frame end)
  and the new `Game.player` is created in the same call — there is never a frame without a valid player. The one who
  had control becomes **Game's stand-in**: a StoryNPC (`stand_in = true`, meta `stand_in`) with his sheet at his spot,
  softly turning to the new player, idling / talking when his lines come (group "npcs", `npc_id` hotspots and dialogue
  docking find him), walking to `partner_spawn` (`walk_to`, 45 px/s; a conversation pauses the walk). The camera
  `retarget()`s: a critically damped glide from where it is (99 % after `glide` s, no overshoot, then plain following);
  `busy` + `input_locked` until 90 % of the glide (~0.7 s); then a 350 ms interact cooldown, so the key that ended the
  last line never acts for the new protagonist. The HUD shows a quiet name plate („KONRAD ADLER“, `HUD.show_protagonist`)
  — no fade, no chapter card, no intro pan, no porter greeting; objectives refresh; signal
  `Game.protagonist_switched(scene, char)`; autosave `level_<scene>` at the end. **Cut** instead of the glide with
  reduced motion, and when a cinematic on the way left the screen black or the level hidden (`switch_cuts()`): the
  level is shown again and fades in (0.9 s).
- **Authored NPCs.** In a switch scene an authored NPC of the protagonist being played is suppressed (`set_suppressed`)
  and an authored, present NPC of the partner replaces Game's stand-in (then the author places him). Prefer the
  settings above: the protagonists should not also be placed as NPCs in the .tscn.
- **Saves / loads.** `save_extra()` adds `controlled` and `stand_in = {char, pos}` (pos = end of a running walk) in switch
  scenes; `apply_loaded_extra()` restores the player's position and the stand-in's on the fresh load. A fresh load
  without saved positions (memory, `--scene`) puts the player at the scene's entry spawn and the partner at
  `partner_spawn`, else 38 px beside the player.
- **Memories / films / photo mode.** A memory of a switch scene opens with that scene's own protagonist (scenes.json),
  the partner stands in by the same rules; there is never a switch inside a memory. `travel_to_memory`,
  `return_from_memory`, `rewatch_film` and `_mem_abort` keep and restore the present stand-in with the position. Photo
  mode is closed during a switch (busy); afterwards it works as before (the figure switch hides `Game.player` only).
- **Untouched.** Levels with a file of their own never adopt anything (`_adopt_scene` is a no-op); capture mode
  (`--capture`, `--scene`, `--char`) and every existing flow behave as before.
- **Tests / checks.** `tests/test_switch.gd` (synchronous: detection, partners, setup, `switch_now` without reload,
  positions, camera glide stepped by hand, save/load, memory entry, reduced-motion cut, hidden level, same-person
  scenes, untouched levels, HUD plate). Windowed check in real frames: `godot --path . -- --switch-demo=<dir>`
  (`scenes/levels/test/switch_demo.gd`; prints SWITCHDEMO_PASS / SWITCHDEMO_FAIL; private `user://switchdemo` saves):
  Game.player valid and alone in "player" in every frame, swallowed key presses, glide timing, load, memory round trip,
  cut, black screen, photo mode. Fixture for both: `scenes/levels/test/L_Test_Switch.tscn` (station art + named
  spawns) with `Game.level_overrides` mapping A1 → M1 → C3 station → C3 hall onto it (tests only).
- **Gated art of a shared level (round 8, registry art).** `L_C3_Registry.tscn` runs
  `scripts/levels/c3p2_archive/registry_level.gd` (extends `Level`): scene.json entries of `layers` / `props` /
  `decals` / `fx` / `lights` with `"after": [objective…]`, `"until": [objective…]` or `"choice": {objective: id | "!id"}`
  are taken out before the base build (`_merge_explore_hotspots` hook) and built per condition (one LayerStack per
  gate group); `"blockers": [{name, rect, after?, until?}]` become StaticBody2D walls; `"looks"` (last match) set
  CanvasModulate + `grade_preset` (live: `Game._apply_grade`). An objective of a Story scene before `level_id` always
  counts (fresh loads, `--scene` captures, memories — inside a memory only those); else the live Story, except
  `c3d_choose`, whose fire look waits until LS_C3_Fire hides the level. Live changes cross-fade (`"fade"` s; the
  replaced look stays until the new one covers it), loads / cuts / a hidden level change instantly; fire lights
  breathe ≤ 3 Hz (damped with reduced motion). Test: `tests/test_c3p2_archive_art.gd`; windowed shots of every look
  incl. the live C → D fade: `res://scripts/levels/c3p2_archive/registry_shots.tscn` (header).
  Sound of the registry (lead integration): in the night looks the porter's radio plays `c3p2_radio_waltz` as an
  SFX loop whose level follows the player's distance to the `porter_booth` hotspot (−10 … −32 dB); in the fire looks
  roof creaks / bursting glass every 6–15 s; `c3e_try_ramp` → `c3p2_bolt`, `c3f_push_desk` → `c3p2_desk_push`.
- **Two places in one level file (round 9, C4 annex).** `L_C4_Annex.tscn` runs `scripts/levels/c4/annex_level.gd`
  (extends the registry script, no porter radio): entries of `layers` / `props` / `decals` / `fx` / `lights` / `looks`
  with `"scene": id | [ids]` (actors: `"scene_id"`) are only built when the level plays that Story scene — decided at
  load (every C4 scene starts with a level load, C4_DESIGN §1; memories load too); `"camera_zones": {scene id: [x, y,
  w, h]}` clamp `get_camera_bounds()` to the walk area of the scene played (the street never shows underground);
  one look per scene carries its c4.json grade. Test `tests/test_c4_annex_art.gd`; shots
  `res://scripts/levels/c4/annex_shots.tscn` (fresh level load per scene, `--as-shots=A:0,B:846 …`, `--as-done=…`).
  `L_C4_Tunnels.tscn` runs `scripts/levels/c4/tunnels_level.gd` on the same conventions (`"scene"` filters of
  layers / props / decals / fx / lights, `camera_zones`, one look + grade per scene; every light carries an empty gate
  so it is named and its slow flicker runs) plus the passing trains of Karsk (scene C: the level's own train every 20–40 s at −8 dB, never while the
  tunnel ambience's train is audible or due; scene A: the dust / lamp beat follows the cellar ambience's own trains at
  10.5 s and 39 s; not headless, not behind a cinematic): `"swing"` = 7-frame lamp strips (frame `rest` hangs still, ≤ 3 px at the shade ≈ 2°, reduced motion
  a third) moved with their named light, `"event_fx"` = dust strips played once (`delay` s), `"train"` = underframes
  rolling over the yard above the tunnel (scene C), lights dip ≤ 10 % at ≈ 2.4 Hz, sfx `c4_train_overhead`.
  Test `tests/test_c4_tunnels_art.gd`; shots `res://tests/visual/c4_tunnels_shots.tscn` (header: `--ts-cams`,
  `--ts-done`, `--ts-train=1`, `--symbols=0|1`).
- **Looks and carry (round 8, C3P2 §6).** `c3.json` `"looks"`: scene → {character id: sheet dir} (soot looks in
  registry C/D and on the quay, `typist_night`); Game sets the static `SpriteRig.looks` on every level load and switch
  (cleared on unload and before the finale montage), so players, stand-ins, NPCs and dialogue portraits
  (`dialogue_box._portrait_entry`) of that scene use the look while ids, speakers and saves keep the base id.
  `"carry"`: scene → {character id: item}; once the item is owned the player's rig plays `carry_idle_side` /
  `carry_side` instead of the side idle/walk rows (Game `_update_carry` on load, switch and `Story.item_granted`).
- **Cinematic skip guard (round 9).** In a cinematic, „skip“ (Esc / pad Y) always skips; „advance“ (Space / Enter /
  E / pad A) skips only when more than `CINE_ADVANCE_GUARD_MS` (0.7 s) have passed since the last interaction ended
  (`Game._interact_end_ms`, set next to `interact_ready_at`) — the press that closed a dialogue's last line never
  skips the film the line triggers. `Game._on_load_slot` awaits the whole load (level included).
- **Saves from a shorter chain (round 8).** `SaveSystem.rebase_story()` (used by `read_container` and
  `Memories.snapshot_raw`): a Story state whose `current_scene` no longer follows from its completed events (a
  round-7 save in the montage after `c3b_completed`) continues in the scene after its last exit event; valid states,
  finished playthroughs (`slice_completed`) and unknown shapes are untouched; the load reports a warning.
  Round 9 grew the chain again behind `c3g_completed` (the round-8 montage form continues in `L_C4_TunnelsA` with
  Alexei). Test: `tests/test_save_rebase_r8.gd` (both generations, container path and memory snapshots).
- **Pad A in menus.** `Settings._build_input_map()` adds `JOY_BUTTON_A` to `ui_accept` (Godot 4.7's built-in action
  has Enter / Kp Enter / Space only), so the A button presses the focused button in every menu; modals that read
  `interact` / `advance` as well treat both as one press.

### 12.12 Evidence board „Die Akte C-17“ (round 9, owner: board)
A cork board of the whole investigation; it only ever READS Story (`inventory`, `completed_objectives`, `has_event`,
`choice_history`, `current_scene`) — no flags, no saves of its own.
- **Code.** `scripts/ui/evidence_board.gd` + `scenes/ui/EvidenceBoard.tscn` (modal, pauses). Pure statics for tests:
  `data_context()`, `snapshot(story, memory_scene)`, `holds(when, …)`, `build_model()`, `compute_layout()`,
  `neighbor()`, `thread_points()`, `live_model()`.
- **Opening.** Journal tab „Akte“ (`journal.gd` TABS gains `board`; it is a vertical file divider on the sheet's right
  edge, NOT in the flow row — `ROW_TABS` keep the seven index tabs at 24 px). Its page = cover (folder, counters,
  „Was die Akte bisher zeigt“, „Pinnwand öffnen“). The board is instanced once by the journal under UIRoot
  (`journal.board_node()`); no UIRoot change. J closes board + journal, Esc/B the board.
- **Data.** `data/board/c17_links.json` groups `{id, caption_key, items[], when?}`: a chain through the OWNED items in
  list order (a missing middle item is skipped; no pin pair in two groups). `data/board/c17_board.json`: `places`
  (columns in story order; Chapter 4: `karsk_c4`, `berlin_c4`), `spots` (scene → line in the detail strip), `looks`
  (item → `look` „burned“ / `note_key`, e.g. Blatt 7 after `admit_plan`, the escort list per `c3g_choose`), `summary`
  milestones (`slot` = alternatives). Conditions: `items`, `any_items`, `objectives`, `events`, `choice.<objective>`
  (`!id` negates). Texts `data/locale/de_board.json` (`board.short.<item>` = card title ≤ 22 chars, every item has one).
- **Board.** Cards (54×24 art px at ×3: detail crop of the inspect close-up, else an original drawing,
  `tools/pixelgen/gen_ui_board.py` → `assets/ui/board/`), steel pin = Alexei, brass = Konrad + initials chip;
  unowned items in a reached place = reserved place with an empty „?“ pin; places not reached = ONE compact „?“
  column (no names, no pictures, no count of places). Focus: arrows/WASD/D-pad/stick (spatial `neighbor()`),
  Enter/Space/A = InspectView (read-only), mouse hover/click; the focused card's threads light up, their captions
  hang on bare cork only (never over a card), all of them in the detail strip. PgUp/PgDn or the right stick scroll the
  summary sheet (opens on its newest line). 100 % shows Chapters 1–3 without panning (4 rows); larger text grows cards
  and strips and the cork pans to the focus. High contrast: dark cork, black ink, bright focus, 6-px threads.
  Cards pinned since the last opening in this session carry „Neu“ and the focus starts on the newest (session only;
  `Story.state_replaced` — new game / load — resets it; a memory never marks anything).
- **Memories.** Decision: the board stays available and shows the file AS IT WAS in the remembered scene — only items,
  objectives, events and choices of scenes up to the memory's scene (chain rank) count; stamp „Erinnerung · place ·
  month“, subtitle „So stand die Akte damals.“ (also on the cover). Menu memories read their snapshot the same way.
- **Tests / shots.** `tests/test_evidence_board.gd` (data ↔ data/v3, house style, owned-only threads on every stage,
  milestones per decision, memory cut-off, navigation, read-only, sizes 100/125/150 %, contrast, journal tab, art).
  Windowed: `godot --path . --script res://tests/visual/evidence_board_shots.gd -- --scene=L_C3_Quay --char=alexei
  --capture=<dir>/_unused.png --frames=999999 --shots=<dir>` (mock Settings, no saves).

## 13. Chapter extensions (Chapter 3 onward, branch `kapitel-3`, 2026-11-04)
Design contract: `documentation/C3_DESIGN.md`. Change log of existing files: `documentation/MERGE_NOTES_C3.md`.
- **Story chain.** The unchanged engine needs ONE linear scene chain ending in the non-quest montage, and a finale that
  requires every quest event. New chapters are therefore inserted before `L_X1_Montage`
  (`… L_M1_Archive → L_C3_Station → L_C3_Hall → L_X1_Montage`); `slice_end_requires` lists all quest events;
  `LOCKED_CINEMATICS` (validator list only) lists every sequence of `data/v3/cinematics.json`. Story texts referenced by
  `data/v3` must live in `data/v3/locale_de.json` (the validator checks that file); every other text goes to
  `data/locale/de_<area>.json`.
- **`ChapterExt`** (`scripts/core/chapter_ext.gd`, instance `Game.ext`) merges every `data/chapters/*.json` and answers the
  director's chapter-specific questions without touching Story state: `levels`, `entry_spawn`, `chapter_cards`,
  `palettes`/`grades` (merged into `Game.palettes/grades`), `line_expr`, `line_variants` (node → `[{when, key}]`),
  `choice_text` (objective → choice → `[{when, key}]`), `reactions` (objective → choice → `[{when?, speaker, key, expr}]`),
  `puzzles` (objective → UI scene, instanced once under UIRoot and pushed on the modal stack via `open(obj_id)`;
  key contract of both list puzzles — `ProtocolPuzzle` c3b and `CheckPuzzle` c3d „Gegenprobe“ (round 8,
  `scripts/ui/check_puzzle.gd`): `is_open`, `symbols` = tray in display order, key N lays `symbols[N-1]` into the
  next empty slot/row, Backspace undo, R clear, Enter submits via `Story.solve_puzzle`, Esc closes, auto-close ≤ 7 s
  after success; CheckPuzzle adds mouse rows (click chooses an empty row, drag and drop) and the „Lupe“ at 125/150 %),
  `cinematics` (sequence → §12.5 scene, played by `ChapterExt.play_cinematic(game, id)`). Conditions:
  `{"<flag>": ">=1" | "<=n" | "==n" | "!=n" | ">n" | "<n" | true | false}`, all must hold, first match wins.
  `game.gd` keeps its slice tables and falls back to `Game.ext` for unknown ids.
- **Actors.** `scripts/actors/story_npc.gd` (extends npc.gd): `show_after` / `hide_after` objective ids control presence.
  `scripts/actors/gated_interactable.gd` (extends interactable.gd): optional hotspots with `after_objective` /
  `until_objective`, so an optional chat never competes with a story interaction at the same spot.
- **Insignia.** `LayerStack.tex()` resolves every texture through `Symbols.pick()` (§12.4).
- **Drivers.** `--autoplay=<a1>,<m1>[,<c3a>[,<c3b>[,<c3d>[,<c3g>[,<c4d>]]]]]]` and `--inputplay=…` (same spec) play the
  whole chain; their saves go to `user://e2e/saves` (round 8), never to the player's slots.
- **Chapter 3, part 2 (round 8, story stream; contract `documentation/C3P2_DESIGN.md`).** Five scenes between `L_C3_Hall`
  and the montage: `L_C3_RegistryA`–`D` share `scenes/levels/L_C3_Registry.tscn` (in-level switches, §12.11; settings in
  c3.json `switches`, plus `grade` per scene) and `L_C3_Quay`. No new flags (a v3 save is compared flag by flag on load);
  decisions `c3d_choose`, `c3g_choose` raise existing meters. ChapterExt conditions may name `"choice.<objective>"`
  (the recorded option id; explicit key in the flags dictionary, else the live `Story.choice_history()`).
  `ChapterExt.level_key(scene)` = the first scene id of a shared level file — Explore entries of the registry use
  `"level": "L_C3_RegistryA"`; `same_level(a, b)`, `scenes_of_level(path)`. Tests `tests/test_c3p2_routes.gd`.
- **Chapter 4, part 1 (round 9, story stream; contract `documentation/C4_DESIGN.md`).** Four scenes between `L_C3_Quay`
  and the montage, alternating cities: `L_C4_TunnelsA` / `L_C4_TunnelsB` (Alexei, Karsk) share
  `scenes/levels/L_C4_Tunnels.tscn`, `L_C4_AnnexA` / `L_C4_AnnexB` (Konrad, Berlin) share `L_C4_Annex.tscn`; consecutive
  scenes never share a file, so every change is a level load (match-cut cinematics `LS_C4_Number` / `Card` / `Stamp`),
  `scene_partner()` is "" and c4.json `switches` carry only `"partner": "none"` + per-scene ambience / music / grade. Each
  file has two walk areas split by a permanent `blockers` entry (gated-art level script of the env streams). Puzzles:
  `pz_c4_routes` (`overlay_alignment`, `RoutePuzzle.tscn`, BlueprintPuzzle keys) and `pz_c4_numbers` (`symbol_order`,
  new `TracePuzzle.tscn`: CheckPuzzle keys + L = lamp). One decision `c4d_choose` (name_marta → `evidence_chain`,
  protect_marta → `civilian_welfare`); no new flag. `Game.end_card_decisions(choice_history)` lists every decision in
  story order. Tests `tests/test_c4_routes.gd`; QUEST_DATABASE §12 by `tools/docs/gen_quest_db_c4.py`.
- **Chapter-4 puzzle UIs (round 9, puzzle stream).** `scripts/ui/trace_puzzle.gd` („Die Nummernkette“): slate board with
  four posts; `slots` (post order) is the answer; the paint-layer table (`assets/ui/puzzle/c4_numbers_board.json`
  `plates.*.under`) drives the lamp (Gegenlicht, presentation only) and the words of a stopped trial run
  (`chain_break()`), never the verdict — that is `Story.solve_puzzle`. Pad: ←/→ LB/RB choose a plate, A hang, B undo,
  X lamp, Y check, Back close. `scripts/ui/route_puzzle.gd` („Linie 74“): light-table inner class `RouteBoard`
  (quarter turns around the trace centre, whole-cell offsets, layout `assets/ui/documents/berlin_c4_routes.json`);
  „wrong_turned“ is derived from the marks' geometry (`rotation_fits`), not from the answer. Art
  `tools/pixelgen/gen_ui_c4.py` (verifies both against `data/v3/puzzles.json`); tests `tests/test_c4_puzzle_ui.gd`,
  screenshots `res://tests/visual/C4PuzzleShots.tscn -- --out=<dir>`.
- **Palais ambient life (art, round 7).** `veltrava_hall/scene.json` `decals` with `frames`/`fps` are looping strips
  (`assets/environments/veltrava_hall/life/`, `tools/pixelgen/env_veltrava_hall_life.py`): figures on `"layer":
  "playfield"` keep `base_y` < 296 (actors always pass in front), figures behind glass or a balustrade sit on the `room`
  layer (`z` 2), the session on `saal_near`; no strip carries insignia. Contract test `tests/test_c3_palais_art.gd`;
  Forward+ review harness `res://tests/visual/palais_shots.tscn` (`--px-stage=arrival|booth`, `--char=konrad`).
- **Station ambient life (art, round 7).** `veltrava_station/scene.json` `actors`: `scenes/levels/veltrava_station/`
  `StationPigeons` (exp_pigeons; flee only from a runner), `StationWalkers` (island platform, parallax 0.93),
  `StationTram` (square behind the exit arch, parallax 0.85) — all extend `scripts/levels/karsk/karsk_actor.gd` — plus the
  generic `KarskTrain` (viaduct, parallax 0.2), `KarskWindowLife`, `KarskBreath` configured by props; sprites from
  `tools/pixelgen/env_veltrava_station_life.py`. Named decal hook `heater_leak_23` (steam leak between wagons 2 and 3,
  side task „Wagen drei ist kalt“): `level.backdrop.decals_by_name["heater_leak_23"].visible = false` stops it.
  Contract test `tests/test_c3_station_art.gd`; Forward+ harness `res://tests/visual/c3_station_shots.tscn`
  (`--scene=L_C3_Station --capture=<dir>/boot.png --frames=100000 --vs-out=<dir> [--symbols=0|1] [--vs-seconds=N]`).
- **Feel pass (round 8, owner feel_r8).** *Ambient walkers*: `scripts/actors/ambient_walker.gd` (one y-sorted manager,
  `scenes/actors/AmbientWalkers.tscn`, declared as a `scene.json` actor with `props.data` = `<env>/walkers.json`) walks
  2–3 anonymous people per level along a path (pause / soft turn / give way to the player: look-ahead, side step inside
  `bounds`, wait, turn back); side levels use a lane between the props' `base_y` and the walk band (y 295 / 295.5), so the
  player and every speaker stay in front. Deterministic, no collision, no group, no Story/Explore. Variant sheets
  (`<env>/walkers/*.png`, `tools/pixelgen/walkers_r8.py`) keep the source silhouette and reuse its `sheet_n.png`.
  *Decor loops*: every looping decal / fx strip starts at `"t0"` (s) or a stable FNV hash of name + position
  (`LayerStack.loop_t0`). *Car 3*: `scenes/levels/veltrava_station/StationThaw.tscn` hides `heater_leak_23` once
  `veltrava.task.heating.thaw` is found (on load, and live after the interaction: leak fades, pipes knock, a hand wipes
  a peephole and waves, the frost recedes; art `veltrava_station/thaw/`). Tests `tests/test_feel_r8.gd`; Forward+ harness
  `res://tests/visual/feel_r8_shots.tscn` (`--fr-shots=label:camx:px:py:seconds[:thaw|thawed|memview150|membroken|
  journal_late|dlg=<speaker>;<key>;<expr>]`). Provenance `documentation/asset_manifest_parts/feel_r8.md`.
- **Feel pass 2 (round 9, owner feel_r9).** *Walkers*: a spec may name its own `"rig"` (`walkers/<name>_rig.json` + `.png` +
  `_n.png`, `walkers_r8.py`: the source rows + `walk_front` / `idle_back` / `walk_back`; `"sheet"` stays the fallback);
  steep path segments (|dy| > 1.2 |dx|) walk toward / away from the camera; pauses really show their pose. Walkers give
  way to each other: head-on in one lane the lower rank (name hash) steps aside (`"pass"`, default 0.5 px back on side
  lanes = they pass one behind the other; `dodge` on oblique floors), without room the other one does, without room for
  either the lower rank waits ≤ 1.2 s and turns back; followers keep ≥ 18 px. Quay: five walkers (`veltrava_quay/
  walkers.json`). *Side task* „Eine Decke für Frau Brunner“ (`data/explore/quay_tasks.json`, texts `de_quay_tasks.json`;
  chain on `ChatTypistQuay` after her chat, locker `TaskBlanketLocker` at `exp_task_blanket` = explore site
  `blanket_source`). *HUD*: toasts on screen when a modal (or `hide_hud`) holds them pause their timer and slide back in
  afterwards (`hud.toasts_held()`). *Cinematics*: e3a / e3b / h1 figures from `tools/pixelgen/env_c3p2_cine_hands.py`
  (portrait SDF pipeline). *Umlauts*: `tools/pixelgen/pixfont_umlauts.py` (dots one row above the cap line, opt-in
  `overhang=True` in the close-up / document / mini-game text renderers). Tests `tests/test_feel_r9.gd`; Forward+ harness
  `res://tests/visual/feel_r9_shots.tscn` (`--f9-shots=label:camx|-:px|-:py:seconds[:hud|task|journal|toast_modal|
  toast_back|disc=<id>@<scale>|insp=<item>@<scale>|walker=<id>@<seg>]`, `--f9-sizes=2560x1440;3840x2160`).
