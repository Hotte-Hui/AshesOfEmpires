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

### 12.6 New characters (ids)
`librarian` (Berlin), `porter` (Berlin doorman), `vendor` (Karsk tea stall), `worker_b` (Karsk). Chat speakers
with portraits: `alexei`, `konrad`, `irina`, `emil`, `vendor`, `worker_a`, `babushka`, `librarian`, `porter`.

### 12.7 Content rules for this round
No glorification; no false equivalence (each card stands on its own facts); easter eggs and jokes never sit
on atrocity topics; in-world finds speak in the protagonist's voice (Alexei dry and tired, Konrad precise and
euphemistic at first), history cards in a neutral documentary voice. German first. All generators deterministic.

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
  `puzzles` (objective → UI scene, instanced once under UIRoot and pushed on the modal stack via `open(obj_id)`),
  `cinematics` (sequence → §12.5 scene, played by `ChapterExt.play_cinematic(game, id)`). Conditions:
  `{"<flag>": ">=1" | "<=n" | "==n" | "!=n" | ">n" | "<n" | true | false}`, all must hold, first match wins.
  `game.gd` keeps its slice tables and falls back to `Game.ext` for unknown ids.
- **Actors.** `scripts/actors/story_npc.gd` (extends npc.gd): `show_after` / `hide_after` objective ids control presence.
  `scripts/actors/gated_interactable.gd` (extends interactable.gd): optional hotspots with `after_objective` /
  `until_objective`, so an optional chat never competes with a story interaction at the same spot.
- **Insignia.** `LayerStack.tex()` resolves every texture through `Symbols.pick()` (§12.4).
- **Drivers.** `--autoplay=<a1>,<m1>[,<c3a>[,<c3b>]]` and `--inputplay=…` (same spec) play the whole chain.
