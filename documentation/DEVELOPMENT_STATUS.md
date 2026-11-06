# DEVELOPMENT STATUS — Ashes of Empires: The Last Winter

Date: 2026-11-04 · Engine: Godot 4.7.2 (GDScript, Forward+) · Platform: Windows 10/11 x64
Scope reached: **vertical slice**, playable start to finish (main menu → Chapter 1 opening → transition →
Chapter 2 opening → Great Hall reveal → X1 finale → end card → main menu).
Evidence for every "verified" item: `TEST_REPORT.md`.

## Round 7 (2026-11-05/06) — Chapter 3 finished, memories, side tasks, five new mini-games
Requested by the user: finish what was started, a good 20–30 minutes of play, new mini-game ideas, improve everything,
and revisit completed scenes („zurückreisen … wieder in die Gegenwart“). Built by 10 parallel specialists (+2 review
passes), integrated and tested by the lead (evidence: TEST_REPORT.md §11).
| Area | Now |
|---|---|
| Chapter 3 „Der eiserne Frieden“ | merged from the cloud branch `kapitel-3` (story data, director extension, Veltrava station + Palais, 7 characters, protocol puzzle, audio, 27 finds, 3 history cards); `.gitattributes` keeps LF so cloud and PC see identical files |
| C3 cinematics | LS_C3_Trains (25.5 s: Konrad's saloon car, flare match cut, Alexei's compartment, both trains meeting on the bridge at dawn), LS_C3_ToHall (6 s, clock match cut), LS_C3_Close (12 s, the dark special train, two hotel windows, „Derselbe Pfiff“); 14 new SFX |
| Erinnerungen (§12.10) | pause menu → MemoryView (thumbnails, finds counter, locked cards without spoilers) → „Zeitreise“ transition into a completed scene in memory mode (sepia grade, badge); Story is snapshotted and never changes, story interactables replay read-only, finds made there are kept, no saving inside; „In die Gegenwart zurückkehren“ restores level, position and HUD; also from the main menu via a global profile; rewatchable films |
| Aufgaben (§12.9) | five optional side tasks, one per walkable level (Karsk train, Berlin mittens, plaza photo, station heating, Palais buffet), 3–5 steps each, explore `requires`/`explore_chain`, journal tab „Aufgaben“, HUD task mark, toasts; drivers complete all of them |
| New mini-games (§12.8) | „Der Morsetaster“ (Karsk signal box), „Rohrpost“ (Berlin archive), „Die Fallblatttafel“ (station), „Die Garderobe“ and „Das Relaispult“ (Palais) — 9 optional mini-games in total |
| Texts / facts | all 23 open C3 review findings handled (incl. the false-equivalence fixes), third logic pass across all branch combinations, 1964 time notation („23.40“) in data and in the drawn documents, the three new history cards fact-checked on the web with sources |
| Art | station and Palais polished on the GPU (Forward+): value structure, light, ambient life (station: 12 actor loops, viaduct train; Palais: 11 life loops), both insignia settings; Chapter-3 cast rebuilt on the round-2 rig and living portraits; soft player turn, `talk_front`, individual portrait faces; skin ramps for the Veltrava palettes |
| Playtime (estimate, `tools/docs/estimate_playtime.py`) | main path ≈ 24 min; with all 91 finds, 24 chats, 9 mini-games, 5 tasks and 19 history cards well over two hours for a completionist (not measured with a human) |

## Round 6 (2026-11-05 night) — plaza task
- Plaza mini-game "Das Blatt im Schnee" (secure the carbon copy "WER FEHLT?" while the guards watch the parade),
  two quiet easter eggs (frost heart, cat trail), a portrait for the press photographer. Plaza: 18 finds/chats.
- Not done: preparing the `kapitel-3` merge (the isolated worktree could not be created because the session folder
  is not the game repository) — do it in a session started inside C:/Spiele/AshesOfEmpires.

## Rounds 4–5 (2026-11-05 night) — parade, plaza, photo mode, credits
- **Parade** (`L_M1_Parade`, 47 s, 8 shots) follows the Great Hall reveal: massed formations, the column behind the
  barrier, tanks, the tribune under the eagle, the forced crowd with the evicted family, searchlights and jets,
  Konrad, the sealed doors — oppressive, anonymous ranks, cold drum score; one skip press skips the whole chain.
- **Walkable parade plaza** (`L_M1_Plaza`, optional side level): after the parade Konrad stands on the plaza —
  looping parade behind the barriers, crowd, guards, tribune, the Great Hall; 13 finds + 2 chats (links to existing
  history cards), the evicted family as NPCs; exit "Zurück ins Archiv" (interactable kind `exit`, Game.side_level).
- **Photo mode** (P / pad R3): paused free camera, 1×–3× zoom, figure toggle, 6 filters, grain/vignette, 5 frames;
  PNGs to user://photos and Pictures/Ashes of Empires.
- **End-credits roll** (~84 s, Esc skips, hold Space speeds up) after the demo end card: production credits and all
  78 sources of the 16 history cards; the same list in the main menu under "Mitwirkende".

## Round 3 (2026-11-05) — after the user's second playtest
- Ch1→2 transition (43 s): the departing train now has 60-frame wheel rotation with rods and valve gear in phase
  with travel, coupling slack (wagons start one after another), wheel slip, chuffs synced to revolutions, rail-joint
  clacks; the swastika banners on Konrad's way to the archive wave strongly (32-frame cloth wave, gusts) and carry
  bold swastikas (`_hist`); neutral variant unchanged.
- Great Hall: the left banner now hangs flat in the facade plane; the plaza foreground is thinned and life moved
  back (queue 5→3, more mid/far walkers, patrol in the mid plaza); the reveal runs 24 s instead of 11 s (slower
  crane, 9 s establishing hold, slow push with tilt, held monumental frame), shown without letterbox bars, music
  swell timed to the final frame.
- Three optional mini-games (§12.8): shunting puzzle and a mate-in-two chess problem in Karsk, tuning the porter's
  radio in Berlin — each unlocks a find; auto-solve for autoplay, `demo_solve()` for the real-input driver.
- History cards no longer print their sources (planned: an end-credits scene listing all sources).
- Image gently calmer: grain −35 %, palette-snap dither −15 %, vignette −10 %.

## Round 2 (2026-11-04 evening) — expansion after the user's first playtest
User feedback: better characters and faces, more detail and life, fuller streets, smoother camera, much more to
explore (incl. real post-war findings in a library), softer protagonist switches, real regime symbolism, ~10 min
of quality content first. Delivered by 16 parallel specialists + integration (evidence: TEST_REPORT.md §7):
| Area | Now |
|---|---|
| Camera / rendering | world renders at screen resolution (k = 3/4/6 for 1080p/1440p/4K), camera and actors move in single screen pixels with a critically damped follow; post effects stay on the 640×360 texel grid; the 3D hall keeps its low-res path with a sub-pixel lens shift |
| Characters | 12 sprite sheets redesigned (heads, faces, costumes, walk/idle/talk) + librarian, porter, vendor, worker_b; 9 speakers with sculpted portraits, 4 expressions × talking mouth + blink, animated in the DialogueBox |
| Karsk | far richer art and 10 kinds of ambient life (crows that flee, the cat, a passing train, lamp, laundry, sparks…); a realistic Soviet skyline (grain elevator with "СЛАВА ТРУДУ!", church used as a warehouse, Khrushchyovka, Stalinist administration, log houses) |
| Berlin | archive extended to 2924 px: arrival through the stairwell (porter's lodge), a library / reading room with five shelf sections, pigeons, a mouse, clock, radio, passing tram |
| Exploration | 43 optional finds and chats (20 Karsk, 23 Berlin) with close-up images, a DiscoveryView, journal tabs "Entdeckungen" and "Geschichte" |
| Real history | 16 sourced "REALE GESCHICHTE" cards (8 Nazi state, 8 Soviet Union) — researched, then independently fact-checked; shown outside the fiction, without fanfare |
| Great Hall | inhabited street and plaza (walkers in five depth bands, queue, patrol, sweeper, moving tram and cars, pigeons), more architecture; swastika banners and the lantern eagle above the globe (Speer's final 1939 design) |
| Transitions | Ch1→2: 40 s animated sequence (train departure → stamp → match dissolve → Berlin morning, branch-dependent); finale: 47 s two-desk montage at the same minute, branch-dependent |
| Symbols | real insignia as `_hist` variants with the setting "Historische Hoheitszeichen" (default on), neutral twins when off |
| UX | the porter greets Konrad on arrival; history cards also after chats; prompt marks found/new finds |

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
