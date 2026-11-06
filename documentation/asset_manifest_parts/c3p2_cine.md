# Asset manifest part — c3p2_cine (Chapter 3 part 2: LS_C3_Radio, LS_C3_Fire, LS_C3_Escape, LS_C3_Halves)

* **Date:** 2026-11-06 (round 8)
* **Area owner:** cinematics stream (C3P2_DESIGN.md §2.9)
* **Scenes / code:** `scenes/cinematics/ch3_radio/` (`Ch3Radio.tscn`, `ch3_radio.gd`), `ch3_fire/`, `ch3_escape/`,
  `ch3_halves/` (the paths registered by the story stream in `data/chapters/c3.json` → `cinematics`) on the shared
  base `scenes/cinematics/c3p2_common/c3p2_cinematic.gd`, which extends the unchanged round-6 runtime
  `ch3_common/c3_cinematic.gd` (§12.5 contract: `finished` exactly once, idempotent `skip()`, `configure(ctx)`,
  `seek()`/`advance()`, cue list, reduced motion) with the c3p2 asset root, `choice(objective)` (the inner lines
  and the bench choreography follow `ctx.choices`: c3a/c3b in the radio film, c3d/c3g at the quay), a subtitle
  scheduler (lines follow each other, about-the-note lines after the note) and flame/puff/snow helpers; dev switch
  `--cine-choices=c3g_choose=swap_halves,…` for captures. Played by `ChapterExt.play_cinematic()`.
* **Generators:** `py -3 -P tools/pixelgen/env_c3p2_cine.py [--only radio,fire,escape,halves]` (~45 s, figures
  cached) writes every texture and `assets/cinematics/c3p2/layout.json` (anchors shared with the runtimes: the
  dial/match cut, walker paths and footprints projected through the square's pinhole camera, flame anchors, hatch,
  window and board geometry; `tests/test_c3p2_cinematics.gd` checks them). Modules: `env_c3p2_cine_kit.py` (ramps,
  re-quantiser, glows, flame/smoke/ember sheets, pencil block letters), `env_c3p2_cine_radio.py`,
  `env_c3p2_cine_fire.py` (fire + escape), `env_c3p2_cine_quay.py` (halves), `env_c3p2_cine_figs.py`. Round-6 tools
  imported read-only: `env_veltrava_cine` (Paint, masks, light helpers), `env_veltrava_cine_kit` (trilingual pixel
  fonts, dithered puffs), `env_veltrava_cine_figs` (figure renderer), `chargen_portrait2_*` (the portrait specs).
  Sound: `py -3 -P tools/audiogen/c3p2_cine_audio.py` → `assets/audio/sfx/c3p2cine_*.wav` (on the DSP helpers of
  `c3_cine_audio.py`, read-only). Offline layer preview (review tool, not a test):
  `py -3 -P tests/visual/c3p2cine_preview.py OUT.png radio|fire|escape|halves`; in-game review with
  `tests/visual/c3cine_harness.tscn --c3-id=LS_C3_…` (shots / seq / run modes).
* **Figures:** Konrad and Alexei close up (at the radios without hats, at the sorting table, on the quay bench)
  are sculpted and lit with the signed-distance pipeline of the dialogue portraits through
  `env_veltrava_cine_figs.render()` with the specs `konrad()` / `alexei()` (faces, hats, hair, coats as in the
  portraits; seen from behind, lit by the dial, the green lamp or the fire). Smaller and action poses (crawling out
  of the hatch, lying in the snow, the hands, walking, the walkers on the square, Alexei backlit by the fire) are
  painted silhouettes with rim light. The arsonist is a backlit silhouette from behind in a long coat and porter's
  cap — never a face.
* **Determinism:** fixed seeds (`np.random.default_rng(n)`, `zlib.crc32(name)` for audio); two full builds are
  byte-identical (md5 over all 80 PNG + layout.json + 27 WAV, checked 2026-11-06).
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio made for ASHES OF
  EMPIRES: THE LAST WINTER by these generators (AI-authored code, project-owned, same licence as the game). No
  downloaded, copied or traced images, fonts or samples. The radio voices are wordless formant babble (the words are
  the subtitles). No insignia anywhere in these films (no `_hist` variants needed).
* **Palettes / grade:** night/snow/lamp ramps of the round-6 cinematics, the `registry` ramps of
  `data/chapters/c3.json` (oak, green lamp, paper, brass, fire), the protagonists' portrait ramps; grade `c3_cine`.
* **Names:** the German delegation's hotel is labelled „Hotel Europa“ as in the station level and LS_C3_Close (the
  design table says „Bellevue“; kept Europa for continuity — see the round-8 open issues).

## Art — `assets/cinematics/c3p2/radio/` (LS_C3_Radio, 30.8 s)
| File | Use |
|---|---|
| `square_bg`, `square_glow`, `win_konrad`, `win_alexei`, `steam` (6) | r1/r6: the station square from the station roof (pinhole projection, supersampled facades re-quantised): Hotel Europa (mansard, arches, sign) and Hotel Nord (flat roof, roof letters) facing each other, tram rails, lamp pools, the advertising column, lime trees, the palais with its dome and dark east wing (one dim window high up); the two lit windows with a man at his radio; steam of the 23.40 |
| `door_konrad`, `door_alexei`, `walker_konrad`, `walker_alexei` (4) | r6: both hotel doors open at once, warm light on the snow; the two men walking out (paths and footprints in layout.json converge on the east wing) |
| `room_alexei`, `room_konrad`, `radio`, `dial_glow`, `lamp_glow`, `magic_eye` (3) | r2/r3: the two rooms around one window/table geometry — Hotel Nord (painted plaster, cotton curtains, doily, the tea glass in its holder, the quilted coat and ushanka on the hook, Hotel Europa across with Konrad's lit window) and Hotel Europa (damask, wainscot, velvet curtains, brass desk lamp, notepad, his hat, coat and scarf on the stand, Hotel Nord across with Alexei's lit window); the same Bakelite set („Komet“, round dial with the two Veltrava marks, cloth grille, piano keys) at the same place — the needle is drawn at runtime and sweeps across the cut |
| `fig_alexei`, `fig_konrad` (2 frames: breath), `arm_alexei` (4), `hand_konrad` (5), `steam_tea` (6) | the men from behind without hats (roll-neck / jacket); Alexei's arm to the tuning knob; Konrad's pencil hand (4 writing frames + stopped) |
| `doors`, `note_fold`, `note_close` | r4: split screen at floor level — room 214 (oxblood, plain) and room 317 (cream panels, brass kick plate), the corridor light in both gaps; the folded note; the note unfolded in pencil block letters, Russian above German (text copied from `de_c3p2_cinematics.json`) |
| `cafe`, `cafe_glow` | r5: Café „Korridor“ after closing — chairs upside down on the marble tables, Elena's table with an untouched glass of tea, reversed gold lettering, the station clock across the square (hands at runtime: 0.10) |

## Art — `assets/cinematics/c3p2/fire/` (LS_C3_Fire, 12 s)
| File | Use |
|---|---|
| `f1_bg`, `lamp_cone`, `f1_konrad` (2: head down / looks up) | the card hall under the brick vault: oak card cabinets with brass label holders, the high barred window, the sorting table with the two halves laid side by side and the red thread of the check, drawer C-17 and Elena's wine-red scarf; the green-shaded lamp's cone (flickers at runtime); Konrad from behind |
| `f2_bg`, `f2_door` (4), `f2_glow` | the Magazin aisle in one-point perspective, archive boxes and the red C-17 tags; the service door: the figure in the lit doorway, half through, the empty doorway, shut |
| `f3_bg`, `f3_warm` | the iron-clad ramp door from inside (planks, straps, rivets, lock box), snow blown in under it; the runtime draws the cold gap light, the passing shadow and the bolt's shadow |
| `f4_bg`, `f4_glow`, `f4_alexei` (2) | the same hall burning (smoke under the vault, scorched drawer fronts); Alexei from behind against the fire (ushanka, fur collar, quilted coat, satchel strap) |
| `flame`, `flame_s`, `flame_big`, `flame_wide`, `smoke`, `ember` (8/8/8/8/8/4 frames) | fire sheets (palette `fire`), dithered smoke puffs, embers |

## Art — `assets/cinematics/c3p2/escape/` (LS_C3_Escape, 16 s)
| File | Use |
|---|---|
| `e1_bg`, `e1_light`, `e1_file` (2) | up the brick coal chute with its steel slide toward the square of snow light; Konrad's sooty hands shoving the tied file |
| `e2_bg`, `e2_lamp`, `e2_hatch` (3), `e2_konrad` (4) | the yard: rusticated base of the east wing, a souterrain window glowing, the bracket lamp, the iron hatch frame in the snow; the lid closed / lifting / open with „1909“; Konrad out to the shoulders, to the waist, on hands and knees (two steps) |
| `e3a_bg`, `e3a_glow`, `e3a_hands` (4) | looking down into the hatch: Alexei's hand out of the smoke, Konrad's hand takes it, the pull |
| `e3b_bg`, `e3b_hatch` (2), `e3b_men` (2) | low at the snow: the lid slammed, both men on their backs, heads together, the file between them, Konrad's hat in the snow |
| `e4_bg`, `e4_window` (3), `e4_glow`, `smoke`, `breath` (6) | the east wing from the lane (pilasters, pediments, mansard, the one lit window high up, the yard gate); a souterrain window dark / bursting / burning; smoke lit from below; breath clouds |

## Art — `assets/cinematics/c3p2/halves/` (LS_C3_Halves, 21 s)
| File | Use |
|---|---|
| `h1_bg`, `h1_glow`, `fig_alexei`, `fig_konrad` (2 each), `stacks` (3), `arms` (2×3), `list_fold` (4) | the quay bench from behind: the balustrade, the frozen river with the fire's glow, the Line with fence and two watchtowers (searchlight beams at runtime); the men; the Russian pages (with the list of names), the German pages, the list; arms reaching near / across / holding; the list folded into Konrad's coat |
| `h2_bg`, `h2_glow`, `walk_alexei`, `walk_konrad` (6 each) | the promenade with its lanterns and their bench; the two walking apart (Konrad mirrored at runtime) |
| `h3_bg`, `h3_glow`, `h3_dawn`, `flame_s`, `smoke` | wide: the palais with the burning east wing and its mirror image in the ice, the far bank with the Line's towers, the three-arch bridge; the first grey of dawn (faded in at runtime) |
| `board_bg`, `board_glow`, `glyphs` | the departures board (trilingual header, four standing rows) and the split-flap glyph atlas (glyphs + mid-flap) from which the runtime flips „DIENSTAG · 23.40 · KORDON-17 · GLEIS 5“ in |

## Sound — `assets/audio/sfx/` (`tools/audiogen/c3p2_cine_audio.py`, 44.1 kHz / 16-bit stereo)
| File | Content |
|---|---|
| `c3p2cine_interval` (3.8 s) | Radio Veltrava's interval signal: an original four-note celesta motif (G E A D), twice, through the set, across the square |
| `c3p2cine_news_ru`, `c3p2cine_news_de` (6.9 / 6.8 s) | announcer babble (two voices) through a small loudspeaker with hum and static |
| `c3p2cine_tune` (1.25 s) | the dial turned: heterodyne whistle, static, a fragment of a voice |
| `c3p2cine_pencil` (2.0 s, looped) | graphite strokes on a pad; stopped at the line's „Begleitgut“ |
| `c3p2cine_corridor`, `c3p2cine_cafe`, `c3p2cine_doors`, `c3p2cine_snowsteps` | steps on a runner and two notes slid under two doors; the empty café (fridge hum, wall clock); two hotel doors at once and the wind; two men walking in snow |
| `c3p2cine_lamp`, `c3p2cine_ignite`, `c3p2cine_service_door`, `c3p2cine_steps_out`, `c3p2cine_bolt`, `c3p2cine_roar` | the green lamp's buzz with crackles at the flicker dips; the boxes catching; a door shut in the stairwell; steps outside, muffled; the iron bolt slid home; the fire's roar and crackle |
| `c3p2cine_chute`, `c3p2cine_hatch_open`, `c3p2cine_cough_k`, `c3p2cine_pull`, `c3p2cine_hatch_slam`, `c3p2cine_cough_both`, `c3p2cine_burst`, `c3p2cine_brigade` | scraping up the chute on the three shoves; the lid flipping open; coughing; the pull; the lid slamming; both coughing in the snow; seven souterrain windows bursting (one every 0.42 s); fire-brigade bells approaching |
| `c3p2cine_quay`, `c3p2cine_steps_apart`, `c3p2cine_ice`, `c3p2cine_board` | wind over the ice with the fire far off; two walkers diverging; the river ice booming and creaking; a split-flap row flipping in the station hall |
Re-used (unchanged): `wind_gust`, `paper_rustle_1..3`.

## Checks
`tests/test_c3p2_cinematics.gd` (20 cases, ~1100 checks): registration; contract and planned lengths; `finished`
exactly once (skip/skip, skip before play, natural end, fast-forward, replay); inner lines for every c3a×c3b and
c3d×c3g combination, spoken in order, non-overlapping, inside the film, ≤ 22.5 characters per second, German text
present; skip stops the cues; reduced/full motion; shot order; no missing texture and layout keys in sync with the
scripts (dial = match cut); every cued sound exists and every loop is stopped; sound/picture timings shared with the
audio generator (lamp dips, chute shoves, window bursts); frames a pure function of t (seek away and back); the match
cut on the dial; who takes which pages per c3g; reduced motion halves the travel; fire light never strobes (≤ 3 Hz,
small frame-to-frame changes). In-game: real-time runs 30.8 / 12.0 / 16.0 / 21.0 s wall time, `finished` once,
~4.2 ms frames (harness `--c3-mode=run`).
