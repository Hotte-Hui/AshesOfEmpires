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
the rename guard flagged the real historian "Matthias Schmidt" in a source → "M. Schmidt"; a second vendor sprite
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
