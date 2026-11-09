# TEST REPORT — Ashes of Empires: The Last Winter (vertical slice)

Date: 2026-11-04 · Godot 4.7.2.stable.official (ed1daf0bf) · Windows 11 Pro · NVIDIA RTX 4090 (Vulkan 1.4, Forward+)
All results below were produced by actually running the commands on this machine. Nothing here was played or
listened to by a human (see "Not covered").

## 1. Test layers
| Layer | Command | Result |
|---|---|---|
| Import | `godot --headless --path . --import` | exit 0 |
| Unit tests | `godot --headless --path . --script res://tests/run_all.gd` | **14 files, 104 cases, 6000 checks — all passed** (2.4 s) |
| Story parity with the Python reference | part of the unit tests (`test_reference_parity.gd`) | 3121 mutated/corrupted saves: 550 accepted with identical state, 2571 rejected (2473 with identical error message), **0 mismatches**; 4 branch routes × play/skip byte-identical |
| UI test | `godot --headless --path . res://tests/visual/UIPreview.tscn` | **29 steps, 0 failures** (modal stack, pausing, typewriter, choices, inspect, both puzzles incl. hints, journal, save overwrite confirm, 150 % text) |
| Audio test | `godot --headless --path . --script res://tools/audiogen/test_audio_headless.gd` | **passed, 51 streams** (bus layout, limiter, volumes, crossfades, stings, loops, variants) |
| Autoplay E2E (Story API) | `-- --autoplay=<a1>,<m1> [--autoplay-skip]` | see §2 |
| Real-input E2E (key presses only) | `-- --inputplay=<a1>,<m1> [--inputplay-skip] [--inputplay-shots=DIR]` | see §3 |
| Exported build | see §4 | see §4 |

## 2. Autoplay — every branch combination, cinematics watched and skipped
Each run plays the real Main scene: waits until each objective is genuinely available (no gate bypass),
triggers the normal interaction, answers each puzzle wrong once and then correctly, saves to slot 1 after the
ledger, plays through all cinematics and the finale, checks choice history and consequence flags, then loads
slot 1 and verifies the restored state is byte-identical.

| A1 choice | M1 choice | Cinematics | Result |
|---|---|---|---|
| share_with_irina | preserve_evidence | watched | **AUTOPLAY_PASS** |
| share_with_irina | preserve_evidence | skipped | **AUTOPLAY_PASS** |
| share_with_irina | request_explanation | watched | **AUTOPLAY_PASS** |
| share_with_irina | request_explanation | skipped | **AUTOPLAY_PASS** |
| keep_private | preserve_evidence | watched | **AUTOPLAY_PASS** |
| keep_private | preserve_evidence | skipped | **AUTOPLAY_PASS** |
| keep_private | request_explanation | watched | **AUTOPLAY_PASS** |
| keep_private | request_explanation | skipped | **AUTOPLAY_PASS** |

All eight runs exit 0 (headless, final regression after all fixes). Each run also verified the consequence flags
(`irina_trust` / `alexei_secrecy`, `konrad_evidence` / `office_suspicion`) and the mid-run save/load round trip.
The first integration run failed at `m1_align_plans` (puzzle answer sent as floats) — fixed before these runs.

## 3. Real-input playthrough
`scripts/core/inputplay.gd` drives the game exclusively with synthetic keyboard events through Godot's input
pipeline: main menu via arrow keys + Enter → disclaimer → intro pan skipped with Esc → journal (J) and pause
menu (Esc) opened and closed → walking (WASD + Shift) into every hotspot's prompt range → E → dialogue advanced
with Space → inspect views closed with E and Esc → signal puzzle with number keys (wrong order, Backspace,
right order, Enter) → blueprint puzzle (Enter on the wrong pose, then R, R, →, →, ↑, Enter) → first choice with
↓ + Enter, second choice with the number key → cinematics → end card → main menu → "Fortsetzen".

| Run | Mode | A1 / M1 choice | Cinematics | Result |
|---|---|---|---|---|
| 1 | headless | share_with_irina / request_explanation | skipped (Esc) | **INPUTPLAY_PASS** (101 s) |
| 2 | windowed, 4K fullscreen, screenshots | keep_private / preserve_evidence | watched in full | **INPUTPLAY_PASS** (143 s) |
| 3 | windowed, 4K fullscreen, screenshots | share_with_irina / request_explanation | skipped | **INPUTPLAY_PASS** (106 s) |
| 4 | headless, final regression | keep_private / request_explanation | skipped | **INPUTPLAY_PASS** (101 s) |
| 5 | **exported .exe**, 4K fullscreen | keep_private / preserve_evidence | watched in full | **INPUTPLAY_PASS** (143 s) |
| 6 | **final exported .exe**, 4K fullscreen | share_with_irina / preserve_evidence | skipped | **INPUTPLAY_PASS** (105 s) |

All four branch combinations have been played by real key presses (runs 1/3, 2/5, 4 and 6).

Two test-environment failures happened before the passes above, both caused by someone using the computer while
the fullscreen test ran: (a) the window lost focus mid-walk and Godot released the held keys (as it would for a
player) — the driver now re-asserts held keys, and the game now opens the pause menu on focus loss during free
play; (b) the real mouse hovering a menu button moved the menu focus — the driver now makes the window
mouse-transparent while it runs. Neither was a game defect.

**Blockers this test found (all fixed):** the interact key did nothing (the world SubViewport receives no input
events); the player could not move in the Berlin archive (collider wider than the 10 px walk band); the end card
was not skippable; "Fortsetzen" after the demo replayed the end card. None of these was visible to the
Story-API autoplay, which is why both layers are kept.

## 4. Exported Windows build
Command: `godot --headless --path . --export-release "Windows Desktop" builds/windows/AshesOfEmpires.exe` → exit 0.

| File | Size | SHA-256 (first 16) |
|---|---|---|
| `AshesOfEmpires.exe` | 109.1 MB | `c446ee9d6b2defae` |
| `AshesOfEmpires.pck` | 110.6 MB | `f29c06013df74b26` |
| `AshesOfEmpires.console.exe` | 68 KB | `089ee9a9c4a0c94d` |

- **Pack contents checked** (parsed the PCK directory): 826 files, 41 JSON data files present, **0 files** from
  `tests/`, `tools/`, `preproduction/`, `documentation/`, `_preview/` or the test environment.
- **Icon:** all six sizes of `assets/icon/icon.ico` (16–256 px) found byte-identical inside the .exe.
- **Runs of the exported build:** windowed capture of the Berlin archive (renders like the editor build);
  full real-input playthroughs, runs 5 and 6 in §3, including the 3D hall, both puzzles, the finale and "Fortsetzen".

## 5. Visual verification (screenshots inspected)
Windowed captures at 1920×1080 (capture mode) and at 3840×2160 (real fullscreen runs on a 4K display, ×6 pixel
scale) were opened and checked: Karsk at camera x 0 / 640 / 1280, the Berlin archive at 0 / 960, every
interaction UI, both puzzles, the stamp → plan match cut, the Great Hall, the finale tableau, the journal and
menus. Curated copies: `documentation/screenshots/`.
Issues found visually and fixed: duplicate NPCs standing over figures baked into Karsk props; dialogue box
covering the speakers (now docks at the top when speakers stand low).

## 6. Not covered (needs a human)
- Nobody has listened to the music, ambience and SFX on real speakers; the mix is unverified by ear.
- No physical controller was used; no real mouse play in the world (UI mouse paths are covered by the UI test).
- Motion quality (shimmer during pans, animation feel at speed) was judged from stills and frame strips only.
- Subjective quality: pacing, puzzle difficulty, readability, emotional impact.
- Only an RTX 4090 was used; no low-end GPU, no 1440p display.

## 7. Round 2 (expansion, 2026-11-04 evening) — all results from runs on this machine
| Layer | Result |
|---|---|
| Unit tests (`tests/run_all.gd`) | **18 files, 143 cases, 10,406 checks — all passed** (new: exploration API/persistence, exploration data validation, Karsk/Berlin find consistency incl. spacing to story hotspots) |
| Exploration data | 43 entries (Karsk 20, Berlin 23) + 16 history cards load with **0 validation warnings** |
| Autoplay, 4 routes × cinematics skipped **+ exploration pass** | **4 × AUTOPLAY_PASS**; every run triggers all 43 finds/chats, unlocks all 16 history cards and verifies the canonical Story state is unchanged by optional content |
| Autoplay, 4 routes × cinematics watched (new 40.6 s transition + hall + 47.5 s finale) | **4 × AUTOPLAY_PASS** |
| Real-input, windowed 4K, skip + exploration (keep_private / request_explanation) | **INPUTPLAY_PASS** in 285 s — all 43 finds reached by walking and opened with E/Space (20/20, 23/23, 16/16 cards) |
| Real-input, windowed 4K, all cinematics watched (share_with_irina / preserve_evidence) | **INPUTPLAY_PASS** in 226 s |
| **Exported .exe**, real-input, skip + exploration (share_with_irina / request_explanation) | **INPUTPLAY_PASS** in 284 s, 43/43 finds, 16/16 cards |
| Export | exit 0; exe 109.1 MB, pack 135.5 MB; pack directory parsed: 1,841 files, data/explore/*.json present, **0 files** from tests/, tools/, preproduction/, documentation/ or `_preview/` |
| Camera smoothness (render-camera specialist, 144 Hz, 1080p, A1 walking) | frames where the camera moved but the image did not: 380 of 575 → 36 of 545; player 1-px vibration on screen: 174 → 1; FPS 596–1,324 (vsync off) |

**Found and fixed during round-2 integration:** the test walker could not reach two finds behind props (the tea stall
behind the family's luggage, the chalk marks behind the C-17 wagon) → grid path-finding over the walkable area;
a deferred render call received already-freed sprites (`pixel_view._style_world_sprite`) → untyped, validity-checked;
the rename guard flagged the real historian's first name in a source → now cited as "M. Schmidt"; a second vendor sprite
next to the stall contradicted the painted vendor and her portrait → removed; faces were dithered by the palette snap
→ skin tones added to the runtime palettes; plans/stamps in the UI and the hall crowd ignored the insignia switch →
resolved through `Symbols.pick`.

**Still not covered:** human playtest and listening pass (≈70 synthesized sounds, two new scores), physical
controller, motion quality judged by a person, other GPUs/1440p displays.

## 8. Round 3 (2026-11-05) — after the second playtest
| Layer | Result |
|---|---|
| Unit tests | **19 files, 153 cases, 11,221 checks — all passed** (new: `test_minigames.gd`: solver/hand solutions accepted, wrong moves refused, chess line sound, porter cycle, auto mode, placement) |
| Autoplay, cinematics watched (43 s train transition, 24 s hall, finale) | **AUTOPLAY_PASS** |
| Autoplay, skip + exploration | **AUTOPLAY_PASS** — 46 finds (Karsk 22, Berlin 24, incl. the 3 mini-games), 16/16 history cards |
| Real-input, windowed, skip + exploration | **INPUTPLAY_PASS** in 314 s — every find reached by walking; the three mini-games solved through synthetic key presses (`demo_solve`) |
| Exported .exe, real-input route | **INPUTPLAY_PASS** in 118 s |
| Specialist checks | train: 0 rod-phase/travel mismatches over 1,104 frames, 0 off-grid, skip finished once; hall: 0 off-palette pixels in 12 final frames, selftest + rig check pass; mini-games: demo_solve shunting 16.3 s, chess 1.8 s, radio 8.4 s |

## 9. Rounds 4–5 (2026-11-05 night)
| Layer | Result |
|---|---|
| Unit tests | **22 files, 172 cases, 12,855 checks — all passed** (new: photo mode, end credits, plaza consistency) |
| Autoplay, skip + exploration | **PASS** — Karsk 22, archive 24, **plaza 15** finds, 16/16 cards; plaza left through its exit |
| Autoplay, watched (reveal 24 s + parade 47 s chain) | **PASS** |
| Real-input, windowed, skip + exploration | **PASS** in 453 s — the plaza walked and explored by key presses, exit back to the archive, end-credits roll skipped with Esc |
| Exported .exe, real-input, skip + exploration | **PASS** in 446 s |

## 10. Round 6 (plaza task)
Unit **23 files, 178 cases, 13,195 checks — all passed**; autoplay skip+exploration **PASS** (plaza 18/18, cards 16/16);
real-input skip+exploration **PASS** in 461 s (the plaza mini-game solved by synthetic key presses); exported .exe
real-input skip+exploration **PASS** in 461 s.

## 11. Round 7 (2026-11-06) — Chapter 3 finished, memories, side tasks, five new mini-games
All runs on this machine (RTX 4090, Forward+, windowed 1080p unless noted).
| Layer | Result |
|---|---|
| Unit (`tests/run_all.gd`) | **37 files, 341 cases, 29,548 checks — all passed** |
| Autoplay, skip + exploration + memories (share_with_irina / preserve_evidence / ask_elena / share_protocol) | **PASS** 125 s — finds Karsk 26/26, archive 29/29, plaza 21/21, station 21/21, Palais 18/18; history 19/19; tasks 5/5; memory round trip Station → Karsk → Station |
| Autoplay, skip (keep_private / request_explanation / note_alone / report_delegation) and (keep_private / preserve_evidence / note_alone / search_elena) | **PASS** 36 s each |
| Autoplay, played in full (share_with_irina / request_explanation / ask_elena / search_elena) | **PASS** 251 s, every cinematic watched |
| Autoplay, skip + memories without exploration (a genuinely new find inside the memory) | **PASS**, the find is kept after the return |
| Real input, played in full (share_with_irina / preserve_evidence / ask_elena / report_delegation) | **INPUTPLAY_PASS** 519 s |
| Real input, skip + exploration + memories (keep_private / request_explanation / note_alone / share_protocol) | **INPUTPLAY_PASS** 1128 s — 115/115 finds incl. 9 mini-games by synthetic keys, 5/5 tasks, 19/19 cards, memory trip by keys only |
| Real input, skip + memories without exploration | **INPUTPLAY_PASS** 313 s |
| Exported .exe (218 MB pack, lossless audio), real input, skip + memories | **INPUTPLAY_PASS** 313 s, memory trip with a new find kept |
Found and fixed by these runs: Game's focus stayed cleared after a modal that pauses the tree, so a second task step on
the same hotspot never got its prompt (player.gd resyncs); the memory driver pressed E inside the 350 ms arrival
cooldown (driver waits it out). Not covered: a human playtest and listening pass (§6), physical controller.

## 12. Round 8 (2026-11-06) — Chapter 3 part 2, in-level protagonist switch, feel pass
All runs on this machine (RTX 4090, Forward+, windowed 1080p unless noted). Six choices per route now
(a1 / m1 / c3a / c3b / c3d / c3g); the drivers keep their saves in `user://e2e/saves`.
| Layer | Result |
|---|---|
| Unit (`tests/run_all.gd`) | **47 files, 458 cases, 46,812 checks — all passed** (new: test_switch, test_c3p2_routes, test_c3p2_archive_art, test_c3p2_cast_audio, test_c3p2_explore, test_c3p2 cinematics/puzzle tests, test_feel_r8, test_save_rebase_r8) |
| Autoplay, played in full (share_with_irina / preserve_evidence / ask_elena / share_protocol / admit_plan / split_by_language) | **PASS** 366 s, every cinematic watched incl. LS_C3_Radio / Fire / Escape / Halves; a slot-3 save inside registry B reloaded through the game (Konrad playing, his position, Alexei standing in) |
| Autoplay, skip (keep_private / request_explanation / note_alone / search_elena / pocket_plan / swap_halves) | **PASS** 64 s |
| Autoplay, skip + exploration (… report_delegation / admit_plan / hide_for_elena) | **PASS** 161 s — registry 18/18, quay 10/10, history 21/21 |
| Autoplay, skip + memories | **PASS** 70 s |
| Real input, skip (share_with_irina / preserve_evidence / ask_elena / share_protocol / pocket_plan / hide_for_elena) | **INPUTPLAY_PASS** 432 s — the in-level switches by real frames, „Gegenprobe“ solved by number keys, main menu „Fortsetzen“ resumes on the quay before the last decision |
| Real input, skip + exploration + memories (keep_private / request_explanation / note_alone / search_elena / admit_plan / swap_halves) | **INPUTPLAY_PASS** 1364 s — 143/143 finds (Karsk 26, archive 29, plaza 21, station 21, Palais 18, registry 18, quay 10) incl. 10 mini-games by synthetic keys, 6/6 tasks, 21/21 history cards, memory trips by keys only |
| All E2E logs | 0 script errors, 0 warnings |
| Exported .exe (324 MB pack, lossless audio), real input, skip + memories (share_with_irina / request_explanation / ask_elena / report_delegation / admit_plan / split_by_language) | **INPUTPLAY_PASS** 454 s, 0 errors, 0 warnings |
Found and fixed in the integration: pad A did not press focused buttons in menus (Godot 4.7's built-in `ui_accept`
has no pad button) → added in `Settings._build_input_map()`; saves and memory snapshots from the shorter round-7
chain failed the replay validation after the chain grew → `SaveSystem.rebase_story` (test_save_rebase_r8); memory
cards of the shared registry level counted 0/0 finds → counted by the level key; the old memory prints of the Berlin
archive and plaza showed Alexei (capture harness used the Story's protagonist) → harness fixed, prints re-captured.
Not covered: a human playtest and listening pass (§6), a physical controller.

## 13. Round 9 (2026-11-06) — Chapter 4 part 1, the evidence board, feel pass 2
All runs on this machine (RTX 4090, Forward+, windowed 1080p unless noted). Seven choices per route now
(a1 / m1 / c3a / c3b / c3d / c3g / c4d); the drivers keep their saves in `user://e2e/saves`.
| Layer | Result |
|---|---|
| Unit (`tests/run_all.gd`) | **60 files, 626 cases, 74,935 checks — all passed** in 77 s (new: test_c4_routes, test_c4_annex_art, test_c4_tunnels_art, test_c4_cinematics, test_c4_puzzle_ui, test_c4_cast_audio, test_c4_explore, test_evidence_board, test_feel_r9, test_inspect_fit, test_journal_fit_r9, test_memory_twins, test_memory_npcs; round-8 saves → Chapter 4 in test_save_rebase_r8) |
| Autoplay, played in full (share_with_irina / preserve_evidence / ask_elena / share_protocol / admit_plan / split_by_language / name_marta) | **PASS** 480 s, every cinematic watched incl. LS_C4_Homeward / Number / Card / Stamp / Voices; slot 3 (registry B) and the quicksave at the transfer siding reloaded through the game (Alexei at the siding, Lev there) |
| Autoplay, skip (keep_private / request_explanation / note_alone / search_elena / pocket_plan / swap_halves / protect_marta) | **PASS** 98 s |
| Autoplay, skip + exploration (… report_delegation / admit_plan / hide_for_elena / protect_marta) | **PASS** 222 s — tunnels 22/22, annex 18/18, history 25/25 |
| Autoplay, skip + memories | **PASS** 104 s |
| Real input, skip (share_with_irina / preserve_evidence / ask_elena / share_protocol / pocket_plan / hide_for_elena / name_marta) | **INPUTPLAY_PASS** 567 s — „Linie 74“ and „Die Nummernkette“ solved by keys (one wrong attempt each first), main menu „Fortsetzen“ resumes in the annex before the last decision |
| Real input, skip + exploration + memories (keep_private / request_explanation / note_alone / search_elena / admit_plan / swap_halves / protect_marta) | **INPUTPLAY_PASS** 1669 s — 186/186 finds and chats (Karsk 26, archive 29, plaza 21, station 21, Palais 18, registry 18, quay 13, tunnels 22, annex 18) incl. 12 mini-games by synthetic keys, 9/9 tasks, 25/25 history cards, memory trips by keys only |
| All E2E logs | 0 script errors, 0 warnings |
| The user's own saves (copies: 1, 2, auto) | load in the new build (A1, Station, A1) |
| Exported .exe (409 MB pack, lossless audio), real input, skip + memories (share_with_irina / request_explanation / ask_elena / report_delegation / admit_plan / split_by_language / name_marta) | **INPUTPLAY_PASS** 589 s, 0 errors, 0 warnings |
Found and fixed in the integration: the first E2E batch failed in every route at the transfer siding. (1) A Space press
that closed Lev's last line also skipped LS_C4_Stamp starting right after it (in a cinematic „advance“ skipped
immediately) — players who press twice lost the film; now „advance“ cannot skip within 0.7 s of an interaction, Esc
still can. The real-input driver then pressed Esc after the film had ended and opened the pause menu; it now checks that
the film is still running. (2) `Game._on_load_slot` returned before the level was loaded, so the autoplay's siding
check saw the previous level; it now awaits the load. The review lenses' own fixes are listed in DEVELOPMENT_STATUS.
Not covered: a human playtest and listening pass (NEXT_STEPS §2), a physical controller.

## 14. Round 10 (2026-11-06/07) — screenshot feedback, cinematics overhaul, Chapter 4 part 2
All runs on this machine (RTX 4090, Forward+, windowed 1080p). Eight choices per route now (a1 / m1 / c3a / c3b / c3d /
c3g / c4d / c4g); the drivers keep their saves in `user://e2e/saves`.
| Layer | Result |
|---|---|
| Unit (`tests/run_all.gd`) | **73 files, 810 cases, 112,540 checks — all passed** (new: test_save_migration_r10, test_c4p2_routes, the C4P2 art / cast / cinematics / puzzle / explore tests, test_hall_avenue, test_parade_vehicles, test_memory_npcs, test_env_generators_keep, test_switch_grade); one reported pending item (a cine stand-in figure, see NEXT_STEPS) |
| Autoplay, played in full (… / name_marta / publish_now) | **PASS** 614 s — every cinematic watched, incl. the reworked films and LS_C4P2_Depot / Steam / Book / Express / Clock |
| Autoplay, skip (… / protect_marta / protect_first) | **PASS** 141 s |
| Autoplay, skip + exploration | **PASS** 302 s |
| Autoplay, skip + memories | **PASS** 148 s |
| Real input, skip | **INPUTPLAY_PASS** 744 s — JoinPuzzle and HousePuzzle solved by keys, „Fortsetzen“ resumes in L_C4P2_BerlinB before the last decision |
| Real input, skip + exploration + memories | **INPUTPLAY_PASS** 2090 s — 231/231 finds and chats over all levels, every task, mini-game and history card, memory trips by keys only |
| E2E logs | 0 script errors, 0 warnings — except 22 engine messages „Invalid polygon data, triangulation failed“ from one light polygon in LS_C3_Radio (ap_full, ip_play, exe); fixed (inset clamped) and re-verified: LS_C3_Radio played in real time with 0 errors, test_c3p2 green |
| Exported .exe (499 MB pack) after the fix, real input, skip + memories | **INPUTPLAY_PASS** 755s, 0 errors, 0 warnings |
| The user's saves, settings, photos and memories profile | unchanged (md5) after every run |
Not covered: a human playtest and listening pass, a physical controller.

## 15. Round 11 (2026-11-07) — reworked C4P2 films, prologue, AAA start, round-off
Reduced E2E set agreed with the user (the routes that never found a unique bug in rounds 9–10 were skipped; nothing in
this round touched exploration).
| Layer | Result |
|---|---|
| Unit (`tests/run_all.gd`) | **75 files, 833 cases, 112,988 checks — all passed**, no pending items (new: test_prologue, test_splash, the extended C4P2 cinematics and generator-keep tests) |
| Autoplay, played in full (8 choices, every cinematic incl. the prologue and the reworked C4P2 films) | **PASS** 677 s, 0 errors, 0 warnings |
| Real input, skip | **INPUTPLAY_PASS** 745 s, 0 errors, 0 warnings |
| Exported .exe (502 MB pack), real input, skip + memories | **INPUTPLAY_PASS** 767 s, 0 errors, 0 warnings |
| User data | saves, settings and photos unchanged; the memories profile had been written by a test run and was restored from the backup |

## 16. Round 12 (2026-11-09) — English localisation, studio name, marketing material
| Layer | Result |
|---|---|
| Unit | **77 files, 846 cases, 113466 checks — ALL PASSED** (3990 / 3990 keys translated, test_localisation) |
| Autoplay, played in full | **PASS** |
| Real input, skip | **INPUTPLAY_PASS** |
| Exported .exe, real input | **INPUTPLAY_PASS**, 0 errors, 0 warnings |
The drivers and tests run in German; English was checked by the QA agent with `-- --lang=en` captures at 100 / 150 %.

## 17. Round 13 (2026-11-10) — pixel fire, the data desk with „Planspiel Abgang“, flashbacks
| Layer | Result |
|---|---|
| Unit | **80 files, 877 cases, 126640 checks — ALL PASSED** |
| Autoplay, played in full | **PASS** |
| Autoplay, skip + exploration (the data desk and its mini-games through ctx.auto) | **PASS** |
| Real input, skip | **INPUTPLAY_PASS** |
| Real input, skip + exploration + memories (every find, the terminal and the wireframe game by synthetic keys) | **INPUTPLAY_PASS** (last level: Explore counts 21/21) |
| Exported .exe, real input | **INPUTPLAY_PASS**, 0 errors, 0 warnings |
Not covered: a human playing „Planspiel Abgang“, listening to the new sounds.
