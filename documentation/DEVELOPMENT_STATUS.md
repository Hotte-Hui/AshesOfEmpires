# DEVELOPMENT STATUS — Ashes of Empires: The Last Winter

Date: 2026-11-04 · Engine: Godot 4.7.2 (GDScript, Forward+) · Platform: Windows 10/11 x64
Scope reached: **vertical slice**, playable start to finish (main menu → Chapter 1 opening → transition →
Chapter 2 opening → Great Hall reveal → X1 finale → end card → main menu).
Evidence for every "verified" item: `TEST_REPORT.md`.

## Round 11 (2026-11-07) — the five Chapter-4-part-2 films reworked, a prologue, an AAA start, round-off
The user kept the round-10 film overhaul and asked for the same treatment of the five new films, better swastikas
in the hall / parade, a gentler start and a round-off; budget-conscious (one lean workflow). Evidence: TEST_REPORT §15.
| Area | Now |
|---|---|
| C4P2 films (Depot, Steam, Book, Express, Clock) | full figures instead of armless busts and silhouette blobs (Lev, Irina, Alexei from behind with the tied ushanka, Ekdahl's hand and film tin, Ilse asleep, the photographer with his own rig), Kolonnenstraße 14 with stucco, lit rooms and street life, Kordon-17 with depth, towers and floodlights, the coal gang reworked; before/after sheets sent to the user |
| Swastikas (hall, parade, plaza, street banners — `_hist` only) | hand-pixelled emblems on the 45° grid (`tools/pixelgen/swastika_px.py`), the portico banner texture 40×144 so the tribune banners stay crisp; neutral twins unchanged |
| Start of a new game | the disclaimer card, then a 60 s prologue (five painted shots: the Line, the map with Veltrava and the corridors, the C-17 stamp, Konrad in Berlin, Alexei in Karsk), then Chapter 1; skippable; never on load |
| Game launch | black → „HOTTE-HUI präsentiert“ (name in `data/locale/de_splash.json`) → „Erstellt mit Godot Engine“ (own lettering, no third-party logos) → the title picture with falling ash and a new sting → main menu; a one-time demo letter (reopen via „Mitwirkende“); never in tests or drivers |
| Round-off | every env generator merges scene.json / provenance.json through `env_keep.py` and removes only its own PNGs; the end card with eight decisions fits at 100–150 % text; `documentation/EXTENDING.md` = the recipe for the next chapter |
| For testers | `builds/AshesOfEmpires_Testversion.zip` (exe + pck + „LIES MICH.txt“ with start help, SmartScreen note and feedback questions) |

## Round 10 (2026-11-06/07) — the user's playtest feedback, a cinematics overhaul, Chapter 4 part 2
The user played round 9 and sent screenshots; the round answered them and extended the game in parallel (round 10 in a
git worktree, merged afterwards). Evidence: TEST_REPORT.md §14.
| Area | Now |
|---|---|
| Screenshot feedback | archive reading room: the pinned note no longer covers the AUFBAU poster; the eagle above the archive portal (LS_A1_ToM1) redrawn as a dark relief (neutral + _hist); parade: figures drawn at their real on-screen size (no upscaled blocks), ranks and files marching in step, a varied crowd without interpenetration or popping, detailed procedural tanks and half-tracks, tribune detail, the far avenue in p8 filled with the parade itself, p7 reframed |
| Cinematics overhaul (LS_C3_Trains → finale, 13 films) | continuous arms and real hands everywhere, people and detail where places were empty; LS_C3_Trains 25.5 s → 36 s (villages, a halt, a crossing, a truss bridge, a new high shot of both trains, a crane up to the whole city of Veltrava); extras on platforms and in the palace; the C3-part-2 rig reworked; the C4 stamp fists, Fengler as a full figure, Konrad larger; the finale's arms as 3D chains. Before/after sheets for every film went to the user for a keep / revert decision |
| Texts | the repeated fiction notes („(fiktiv)“, „fiktive … – kein echtes …“, „(alternative Geschichte)“) under titles, puzzle subtitles, an objective, the menu footer and every history card are gone (user request); the intro disclaimer and the credits keep it |
| Save migration | `SaveSystem.fill_flag_defaults()` fills missing Story flags in every older save and memory snapshot before validation; first new flag `people_protected` |
| Chapter 4 part 2 (C4P2_DESIGN) | the archive path and the transport path joined: Karsk depot, Berlin Ostbahnhof, the depot showcase with the join of card 0417, Kolonnenstraße 14; decision c4g publish_now / protect_first echoing a1, m1, c3b, c3d, c3g, c4d; JoinPuzzle (the two halves) and HousePuzzle (a way through the tenement); five match-cut films (Depot, Steam, Book, Express, Clock); new cast with living portraits; music and ambiences; exploration with tasks, mini-games and four history cards (propiska, foreign correspondents, Schriftleitergesetz, Blockleiter); board cards; memories |
| Polish | unused cast cues wired or dropped; the board strip pages its threads; env generators keep walker rigs and actor blocks (`env_keep.py`, now also env_berlin.py); chapter-switch grades applied on load; palette cap 128 |
| Found in integration | the overhaul and round 10 both added a `loop_frame` helper (renamed in the C4P2 films); a degenerate light polygon in LS_C3_Radio (the first E2E batch logged „triangulation failed“; inset clamped); two more fiction notes in chapter titles |
| Playtime (estimate) | main path ≈ 64 min; everything ≈ 4 h 35 min (185 finds, 46 chats, 14 mini-games, 11 tasks, 29 history cards, 8 decisions; `tools/docs/estimate_playtime.py`, not measured with a human) |

## Round 9 (2026-11-06) — Chapter 4 part 1 „Stimmen unter Beton“, the evidence board „Die Akte C-17“, feel pass 2
Planned before the user went to sleep. Built by 9 parallel specialists from the contract `documentation/C4_DESIGN.md`;
then four review lenses (text & history, code & saves, art & UI, completeness) found 42 issues, each checked by a second
agent before an owner fixed it (2 refuted); the remaining low ones were fixed in an integration pass with its own
review. Integrated and tested by the lead (evidence: TEST_REPORT.md §13).
| Area | Now |
|---|---|
| Story (C4_DESIGN) | both men travel home with their half. Karsk: Lev Sokolov's archive cellar under the freight yard (cut signatures, Archipov's carbon, the January gap in the freight books), then Service Tunnel 3 to the hidden transfer siding where wagon 24 318 is repainted „C-17/45“. Berlin: Marta Vogel's tram loop Süd 8 at dawn (the gutted No. 9, the shafts S 1–S 3 drawn by K. Adler), then the registry annex „Nebenstelle Süd“ under the Great Hall district (drawer Süd 8: 212 cleared households, 37 flagged C-17, card No. 0417 torn in two). Decision c4d: give registrar Fengler Marta's name for the household records — or protect her. Match cuts on shared objects (the 45, card 0417, the stamps); 9 line and 2 option variants react to earlier decisions; 7 decisions on the end card (story order, also after a reload) |
| New places | Karsk tunnels level (archive cellar at 4.40, Dienststollen 3, the siding hall with the stencil board and wagon 24 318; trains overhead shake dust and lamps) and Berlin annex level (Wendeschleife Süd 8 with tram 74 and the cleared blocks under the dome; the underground card hall with drawer bank Süd 1–12, tube station and the counter „Auskunft · Abgleich“) — story-state art, insignia twins, one camera zone per scene |
| Cinematics | LS_C4_Homeward, LS_C4_Number, LS_C4_Card, LS_C4_Stamp, LS_C4_Voices (14 / 13 / 11 / 11 / 24 s) with choice variants from c3g and c4d |
| Puzzles | „Linie 74“ (RoutePuzzle: lay Marta's tracing paper of detours over the site plan — every detour sits on a shaft) and „Die Nummernkette“ (TracePuzzle: follow one wagon through four switch posts by the paint layers of its number plates, with a back-light lamp) |
| Cast / sound | Lev Sokolov, Marta Vogel, Registrator Fengler (sheets, living portraits; Fengler stamps cards at the counter); 4 ambiences, 3 music cues (Karsk, Berlin, „Voices“), synced cinematic sounds |
| „Die Akte C-17“ (new) | journal tab „Akte“: a cork wall with every owned evidence item of both men (picture cards, steel / brass pins by finder), 33 thread groups (red threads only between owned items), a growing summary „Was die Akte bisher zeigt“ (35 milestones incl. decisions), unknown items as „?“, memories show the file as it was then |
| Exploration | 35 Chapter-4 entries (finds, chats with Lev, Marta and the guard), side tasks „Wir sind vierzehn“ (tunnels) and „Ilses Puppe“ (annex), mini-games „Der Hebelrahmen“ (tunnels) and „Die Lüftungsklappen“ (annex), 4 history cards (Order No. 270, special settlements, „Ostarbeiter“, denunciation) |
| Feel pass 2 | quay walkers (fireman, a man in his coat over pyjamas, a clerk with rescued files, an old woman, a policeman) that give way to each other; side task „Eine Decke für Frau Brunner“; toasts keep their time while a menu holds them; redrawn hands and figures in LS_C3_Escape / Halves; distinct Ä/Ö/Ü in the pixel font and on the world signs; InspectView and journal fit 150 % text (scrolling record card, pinned buttons) |
| Fixed in review / integration | memories: story NPCs in shared levels follow the remembered state (Lev in his cellar after the chapter), each memory card counts its own walk area, memory twins per scene; route-board close-up and board pictures as close-up fallback; the annex mini-game, the tunnels task and the denunciation card added to meet the contract; texts (the Sunday timeline, Alexei's closing line, Süd 8 counts, Tepluschka); evidence-board strip and summary at 150 %; palette ramps; train sounds no longer pile up; drawer Süd 3 painted ajar; alt texts for the annex close-ups; the quay blanket locker painted behind the cab. Found by the lead's E2E runs: a Space / Enter / E press that closed the last dialogue line also skipped the film starting right after it (players who press twice lost the cinematic) → „advance“ cannot skip a film within 0.7 s of an interaction (Esc still can); loading a slot from inside a level returned before the level was loaded (`_on_load_slot` now awaits it) |
| Playtime (estimate) | main path ≈ 49 min; everything ≈ 3 h 40 min (151 finds, 35 chats, 12 mini-games, 9 tasks, 25 history cards; `tools/docs/estimate_playtime.py`, not measured with a human) |

## Round 8 (2026-11-06) — Chapter 3 part 2: the joint evidence check, the registry fire, the first co-op scene
Planned with the user before they went to sleep („arbeite weiter … schaff neue Pläne“). Built by 9 parallel specialists
from the contract `documentation/C3P2_DESIGN.md`, integrated and tested by the lead (evidence: TEST_REPORT.md §12).
| Area | Now |
|---|---|
| Story (C3P2_DESIGN) | radio night (LS_C3_Radio: the same news in both hotel rooms, „begleitete Personen“ / „Begleitgut“, the note signed „– E.“); registry A (Alexei: emptied crates, the night book), B (Konrad: the two halves on one table, puzzle „Gegenprobe“, Blatt 7 with Konrad's own initials, choice c3d admit/pocket the plan), C/D (the fire: Alexei takes the file, the ramp door is bolted, Konrad pushes the desk, both climb out through the 1909 coal chute), the night quay (each keeps half; choice c3g split by language / swap / hide for Elena); 6 decisions on the end card |
| In-level protagonist switch (§12.11) | two Story scenes may share one level file; control passes in place (no reload, no fade, camera glide ≈ 1.2 s), the other man stays as a story NPC, walks to his spot, talks; saves keep both; memories open each scene with its own protagonist |
| New places | registry level (four looks of the same rooms: night with Konrad's torch, green lamp, smoke, fire; gated art, blockers, breathing fire light), night quay behind the Palais (fire engine, searchlights, the burning wing over the ice) |
| Cinematics | LS_C3_Radio 30.8 s, LS_C3_Fire, LS_C3_Escape, LS_C3_Halves; memory film titles |
| Puzzle | „Gegenprobe“ (CheckPuzzle): pair each paper of the freight chain with a registry entry by the one fact they share; keys, pad, mouse; hint, 150 % text |
| Cast / sound | soot looks for both men and a night look for the typist (per-scene „looks“, portraits included), Konrad/Alexei carry the file, 32 synthesized sounds, fire and quay music, registry/fire/quay ambience; the porter's radio waltz louder near his booth, roof creaks and glass in the fire |
| Exploration | 18 registry finds + 7 on the quay, a registry side task, the „Kartei“ mini-game, two history cards (1939 census, filtration) |
| Feel | ambient walkers in the Palais, on the station platform and in the reading room (they give way to the player), car 3 thaws after the heating task, decal loops desynchronised, portraits for the evicted Berlin family, Voronova's hat, MemoryView fixes, toasts wait while a menu is open |
| Fixes in integration | pad A now presses the focused button in every menu (Godot's built-in `ui_accept` has no pad button — controller players were stuck in menus); saves and memory snapshots from the shorter round-7 chain continue in the registry instead of failing (`SaveSystem.rebase_story`, test_save_rebase_r8); memory cards of the shared registry level count its finds |
| Playtime (estimate) | main path ≈ 35 min; everything ≈ 2 h 50 min (116 finds, 27 chats, 10 mini-games, 6 tasks, 21 history cards; not measured with a human) |

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
`builds/windows/AshesOfEmpires.exe` (109 MB Godot runtime, icon embedded) + `AshesOfEmpires.pck` (502 MB after
round 11, mostly lossless audio and art) + `AshesOfEmpires.console.exe` (log output). Rebuild:
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
- Playable: Chapters 1–4. Chapters 5–6 and the ending matrix exist only as design documents (STORY_BIBLE §6–8);
  saves fill missing Story flags with their defaults since round 10.
- No human has played or listened to the game yet; all judgements are automated, numeric (audio) or screenshot-based.
- Controller input is tested only synthetically (pad A confirms in menus since round 8), never with a physical
  controller; no click-to-walk in the world.
- German only; no English localisation yet.
- The build ships lossless WAV audio on purpose (size is not a goal right now).
