# DEVELOPMENT STATUS — Ashes of Empires: The Last Winter

Date: 2026-11-04 · Engine: Godot 4.7.2 (GDScript, Forward+) · Platform: Windows 10/11 x64
Scope reached: **vertical slice**, playable start to finish (main menu → Chapter 1 opening → transition →
Chapter 2 opening → Great Hall reveal → X1 finale → end card → main menu).
Evidence for every "verified" item: `TEST_REPORT.md`.

## What exists and is verified
| Area | Content | Verified by |
|---|---|---|
| Rendering | 640×360 world in a SubViewport, integer ×3 upscale (1080p; ×6 at 4K), pixel-locked gameplay camera, sub-pixel cinematic pans, parallax stacks, normal-mapped 2D lights, emission, palette-snap post with Bayer dither, grain, vignette, letterbox | windowed captures at 1080p and 4K |
| A1 "Verladebahnhof Karsk" | 2.5D oblique, 1920 px wide, 10 parallax layers, 12 y-sorted props with collision, 7 lights, 19 animated FX, snow, fog bands, 4 inspect documents | captures at cam 0/640/1280; real-input playthrough |
| M1 "Berliner Bauarchiv" | 2D side view, 1600 px, window exterior parallax with the Great Hall dome, 12 props, light shafts, dust, snow behind glass, plan documents | captures; real-input playthrough |
| LS_M1_Hall | 11 s 3D cinematic rendered as pixel art (toon shading, outline/crease post, palette snap, Sprite3D people, crane → establishing → push-in), timed loudspeaker subtitles | in-game run through `Game._cin_hall()`, screenshots |
| Transitions | LS_A1_ToM1 match cut (red C-17 stamp → pencil C-17 on a plan), LS_X1_Final (two desks → border map) | in-game, watched and skipped |
| Characters | 12 sprite sheets with normal maps (Alexei, Konrad full 9-row sets), 4×4 portrait expressions | validator + in-game |
| Story engine | full GDScript port of the preproduction Python engine, byte-identical save JSON, 3121-case parity corpus | unit tests |
| Gameplay systems | interaction prompts, dialogue with portraits/typewriter/history, inspect view, signal puzzle, blueprint overlay puzzle, binary choices with consequences/flags, journal (objectives/evidence/people/decisions), toasts, chapter cards | autoplay + real-input runs |
| Saves | slots 1–3, auto, quick; atomic writes with backup; validation before load; "Fortsetzen" resumes the last playable autosave | unit tests + real-input run |
| Menus/UI | main menu, pause, settings (video, audio, controls with rebinding, accessibility: text scale, text speed, subtitles, high contrast, reduced motion, pixel post), save/load, credits, confirm dialogs | UI preview test + real-input run (menu, journal, pause) |
| Audio | 4 ambience loops, 6 music cues, 41 SFX (all synthesized, original); 5 buses with limiter; crossfades, stings | headless audio test (51 streams) |
| Content safety | fictional-history disclaimer at new game; fictional insignia only (no real party symbols); no glorification | disclaimer seen in the real-input run; content rules given to every asset generator; spot checks of screens and strings (no full editorial review yet) |

## Windows build
`builds/windows/AshesOfEmpires.exe` (109 MB Godot runtime, icon embedded) + `AshesOfEmpires.pck` (110 MB, mostly
lossless audio) + `AshesOfEmpires.console.exe` (log output). Rebuild:
`godot --headless --path . --export-release "Windows Desktop" builds/windows/AshesOfEmpires.exe`. Start with
`Spiel starten.cmd` in the project root.

## Fixed during integration (real problems found by the tests)
- Interact key did nothing in real play (world viewport receives no input events) → routed through `Game`.
- Player could not move in Berlin (collider wider than the 10 px walk band) → flat side-mode collider.
- Feet slid at walk speed (walk stride too short) → longer stride for both protagonists, playback tied to speed.
- Blueprint puzzle auto-solve sent floats; Saves.load triggered a double level load; bus names "Sfx"/"Ui" never
  received their volumes; end card not skippable; "Fortsetzen" after the finale would replay the end card;
  dialogue box covered the speakers; mashed confirm keys could pick a choice instantly; one key press could
  chain two interactions; duplicate NPCs over baked prop figures in Karsk.

## Not done (honest list — see NEXT_STEPS.md)
- Only the slice: Chapters 3–6 and the full ending matrix exist as design documents, not as playable content.
- No human has played, listened to or rated the slice yet; all judgements are automated or screenshot-based.
- Controller mapping exists but was not tested with a physical controller; no click-to-walk in the world.
- German only; no English localisation yet.
- **The slice is shorter than the 20–30 min target.** Not measured with a human; estimated from the data
  (14 dialogue lines / ~800 characters, 7 observations, 6 documents, ~5300 px of walking at 45 px/s, 2 puzzles,
  ~1 min of cinematics): **about 10–15 minutes** for a first playthrough. The canonical slice script is thin on
  dialogue; see NEXT_STEPS §2a.
- Build ships uncompressed WAV audio (~120 MB).
