# Asset manifest — Photo mode (area: photo-mode)

Owner: photo-mode specialist · Date: 2026-11-05 · Engine: Godot 4.7.2. Everything below is **original work**,
generated procedurally by a project script (no downloads, no traced or sampled pixels). Colours: the UI kit palette
of `scripts/ui/ui_kit.gd` (paper ramp, night/navy, copper, amber).

## 1. Assets
| File | Size | Generator | Notes |
|---|---|---|---|
| `assets/ui/photo/frame_print.png` | 640×360 RGBA (1:1, shown ×3 nearest) | `tools/pixelgen/gen_ui_photo.py` | 1940s deckle-edged paper print ("Büttenrand") on a dark album page, four black photo corners, transparent picture window (18,18)-(622,338). Seed crc32("photo_frame_print"). |
| `assets/ui/photo/icon_camera.png` | 48×36 RGBA (16×12 drawn ×3) | same | Pixel rangefinder camera for the panel header. |

Run: `py -3 -P tools/pixelgen/gen_ui_photo.py [--preview=<dir>]` (deterministic). Shutter sound: none in the audio set;
the code plays the first of `ui_shutter`, `camera_shutter`, `shutter` if the audio department adds one (silent otherwise).

## 2. Code / data
* `scenes/ui/PhotoMode.tscn` + `scripts/ui/photo_mode.gd` (extends `ui_modal.gd`), registered by `scripts/ui/ui_root.gd`
  as `photo` (instanced in `_ready`, UIRoot.tscn untouched) with `open_photo() -> bool`.
* Strings: `data/locale/de_photo.json` (`ui.photo.*`). Reuses `ui.hint.close` and `ui.key.*`.
* Tests: `tests/test_photo_mode.gd` (file names, filter presets restore the grade exactly incl. shader defaults, bounds
  clamping, open/close restores camera/figure/grade, blocked in cinematic / dialogue / busy / without level).
* Windowed harness: `tests/visual/photo_harness.tscn` (see its header; `--ph-real` writes the export copy to the
  real Pictures folder).

## 3. Behaviour contract
* Opens only in free play (level loaded, not `Game.busy` / `in_cinematic` / `input_locked`, no UI cinematic, no modal
  incl. dialogue). Pauses the world; hides every other UIRoot child and `Game.overlay`, restores them on close.
* Camera: `cinematic = true`, `set_top_left()` inside `camera.bounds`; on close position, spring velocity and the
  cinematic flag are restored exactly (`set_top_left(saved, false)`; not `snap_now()`, which would jump to the follow
  goal). 3D / low-res path (`Game.view.is_hires() == false`): the camera is never touched.
* Zoom 1×/2×/3×: integer scale of `Game.view.display` (nearest) placed on whole screen pixels — crisp texel blocks
  (verified on a 1080p crop); world viewport, grade and dither are not changed. Restored on close.
* Filters write `lift/gamma/gain/tint/saturation/vignette/grain` on `Game.grade.material` on top of the snapshot taken
  at open (`palette_strength` kept); close writes the snapshot back (falls back to `Game._apply_grade(level)`).
* Photo: UI hidden for the frame, frame overlay kept, root viewport image (window size) saved as
  `user://photos/ashes_YYYYMMDD_HHMMSS[_n].png` and `<OS Pictures>/Ashes of Empires/` (same name), then flash
  (dimmer with reduced motion) + toast with file name and folder.
