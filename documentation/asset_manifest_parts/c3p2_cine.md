# Asset manifest part — c3p2_cine (Chapter 3 part 2: LS_C3_Radio, LS_C3_Fire, LS_C3_Escape, LS_C3_Halves)

* **Date:** 2026-11-06 (round 8; places and motion reworked in round 10, see the section below)
* **Area owner:** cinematics stream (C3P2_DESIGN.md §2.9); round 10: places stream (places, light, motion) and
  figures stream (every person: `env_c3p2_cine_figs` / `_hero` / `_people` / `_body`)
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

## Round 10 — places, light and motion (user feedback: the films felt empty)
Same shots, order, lengths and lines; every place repainted as lit colour (albedo × light field + emission, snapped
to a scene palette with the kit's ordered dither) by new place modules, called from the round-8 build functions:
`env_c3p2_cine_life.py` (the float-RGB painter `Cv`, vectorised capsules, value noise at any coordinate, props:
bare lime trees, lamp posts, a snowed-in 1950s saloon, crates, barrels, railings, wires; sheets: steam lit from
below, fire smoke, living flame masses `flame_mass`, burning paper, crows, pigeons, the café cat),
`env_c3p2_cine_square.py` (r1/r6), `_rooms.py` (r2/r3), `_cafe.py` (r4/r5), `_registry.py` (f1–f4; the card hall is
ray-cast as a vaulted cellar), `_yard.py` (e1–e4), `_river.py` (h1–h4). People only through the figures stream's
API (`env_c3p2_cine_figs`: the hero figures, the drop-ins `walker`, `window_listener`, `doorway_figure`,
`fire_alexei`, `quay_walk`, `arm_alexei`/`hand_konrad`/`chute_file`/`hatch_konrad` when present, and the extras
`person_sheet`, `onlookers`, `firemen`); the h1 bench is drawn in their bench camera so the men sit on it.
* **Radio:** the square is layered (`square_bg` 664 × 380 at (−12, −10) with margins, `square_near` = the station
  roof's parapet with an urn and a lantern, `near_glow`): r1 cranes down onto it, r6 trucks right after the men
  (`square_camera(t)`); hotels with lit lobbies, balconies, brass and roof signs, random lit windows; tram wires and
  poles, a shelter, the clock post at 0.10, a kiosk, cars at the kerb, a taxi rank, ripples and tracks in the snow;
  steam of the 23.40 rises from behind the parapet (`steam` 6 × 150 × 96), a taxi drives the far street (`taxi`), a
  late couple crosses the near square (`couple_man`/`couple_woman`). Rooms: bed, print, radiator, frost flowers,
  curtains, newspaper (Nord); damask, wainscot, sconce, velvet curtains with tie-backs, net curtain, inkstand,
  folder, coffee cup with steam, the lamp's reflection (Europa); the chairs in front of the men (`chair_*`); a car's
  headlights sweep Alexei's ceiling. Doors: plaster/damask, chain, house rules, brass kick plate, rag rug, carpet,
  the keys with their fobs „214“/„317“ (`keyfob`, they shiver when the note pushes in), the courier's soles in the
  gaps; the note on the boards in the gap light with both folds. Café: front window with the reversed lettering
  and the closed sign, the station opposite with its name and lit clock (a running red second hand), lamp post,
  tram stop, pendant lamps, newspaper holders, coat stand with a forgotten umbrella, the bar with the espresso
  machine and night light, the cat on the bar (`cat`), bentwood chairs upside down, Elena's table in front
  (`cafe_fg`, parallax drift). Subtitles: the two broadcasts 7.0 / 6.5 s, the shared-note line 4.5 s, the note
  line 2.6 s — every line ≤ 19 characters per second (`tests/test_c3p2_cinematics.gd` now checks 19).
* **Fire:** f1/f4 ray-cast card hall (cabinets on three walls, segmental brick vault with tie rods, the barred
  window's snow light shaft, the ladder, the table with both halves, the red thread, magnifier, drawer C-17, ink,
  stamp, the chair with Elena's scarf); f2 aisle with caged lamps, pipes, ladder, book trolley, papers, the door's
  light wedge and the figure's long shadow down the aisle, smoke rolling along the vault (`smoke_hot`); f3 door
  with latch, hinges, crates, hand truck, fire bucket, lantern, the RAMPE sign, smoke creeping in; f4 with the
  ember band revealed behind the fire front (`fire_band`), new flame masses (`flame*.png`, `flame_tall`) on
  regenerated anchors, burning paper (`paper`) and a rolling smoke layer.
* **Escape:** chute with coal on the slide, soot, a pipe, the fire's glow from below and snow falling in; yard with
  the glowing souterrain window, drainpipe, coal heap, barrels, handcart, the gate and the lane's lamp; the lid
  sheds its snow; the hatch seen from above as a deep shaft with the glow below and sparks; the east wing with
  light wells, neighbouring houses, lime trees, a lamp post, a snowed-in car, flames licking out of the burst
  windows, glass glinting into the snow, onlookers (`onlooker_*`), two firemen running in (`fireman_*`) and a slow
  blue beacon as the bells come close.
* **Halves:** h1 far bank with the Line (double fence, barbed wire, towers, houses, lit windows), ice with drifts,
  ridges, cracks and the fire mirrored in streaks, the searchlights' pools wandering over the ice, the granite
  bench; h2 lime trees, globe lanterns, the bench and a bin, a parallax foreground (`h2_near`), lantern shadows
  under the walkers; h3 the palais with drum, dome and dormers, the burning east wing, the bridge with its lamps
  and the Line's barrier, a leaning smoke column with sparks, crows crossing the dawn (`crow`); h4 the station hall
  (glass roof at first light, chains, wall lamps), pigeons on the board (`pigeon`), steam (`steam`), two travellers
  looking up (`traveller_*`).
* **Checks:** the c3p2 suites pass (7 files, 86 cases); insignia on/off give identical frames in all four films
  (no insignia; the scripts never read `symbols`).

## Round 11 — art-director pass (fire that reads as fire, soft smoke, readable beats)
Same shots, order, lengths and story; new effect generators in `env_c3p2_cine_life.py`: `soft_puff_sheet` (soft
volumetric puffs — little lit spheres, alpha in a few levels, frayed rims — instead of the ordered-dither puffs that
read as checkerboard blotches), `soft_plume` (a whole smoke column as one soft image), `fire_sheet` (licking tongues
from a burning bed, domain-warped turbulence that only eats into the fire, flicks; colour bands from a translucent
red fringe to a white-hot core — no dark rim, the core is the brightest pixel), `fire_halo` (additive bloom).
* **Fire:** f4's hall is darker (`f4_bg` = the hall before the fire reaches it); the fire's light is `f4_lit`
  (burning hall minus unlit hall, additive) revealed behind the running front with a soft edge; the table is a
  layer in front (`f4_table`), so the clusters (`fire_mid`/`fire_big`/`fire_wide`/`fire_small`, anchors and kinds in
  layout `fire.f4_fire` / `f4_kinds`) rise behind its far edge, merge into one wall of uneven height, catch small and
  grow; no flames float alone over the cornices; halos bloom around them; soft smoke (`smoke_hot`) rolls along the
  vault toward the camera. f2: the aisle is dark before the fire (`f2_glow` = the fire's light, faded in from the
  catch), the boxes burn with `f2_fire_s/_m/_l` and halos, soft smoke rolls along the aisle's vault. f3: the gap
  light varies along its length (the yard lamp, snowflakes passing) and spills cold light on the jamb and the floor;
  the snow blown in is cold white. f1: soft lamp-lit wisps.
* **Radio:** the steam of the 23.40 is soft (`steam`, 6 × 150 × 110) and billows up from behind the parapet in
  beats; the lamp pools are lamp light on snow (pale warm greys, sparkle) plus soft additive pools; r6 pushes in
  toward the dark east wing, the men step out at a readable size (`walker_*`, 21/20 px, rigged through
  `env_c3p2_cine_people.person`) with their door-light shadows, then a dissolve (`LATER`) to a minute on: two
  trodden furrows with footprints (layout `trail_*`, `prints_*`, `path_*` over the whole way, `walk_*` metres)
  converge across the snow and the men, small (`walker_far_*`), reach the wing; the headlight sweep lands on the
  walls and the ceiling's edge, never on the glass; the folded note reads as a folded sheet; the café has a worn
  low-contrast floor with the window's light and sheen, a second row of tables, a mop bucket, a mat, a chair in
  front, readable bentwood chairs, a lever espresso machine, a passing car's light, and a visible parallax drift.
  Subtitles: the broadcasts are condensed excerpts (72 characters, 3.8 s each, same meaning: Anlage C, „begleitete
  Personen“ vs. „Begleitgut … ohne Halt“) so every line plays over its own picture (`LINE_AT`; checked by
  `radio_lines_over_their_pictures`).
* **Escape:** the lid is opaque cast iron (`e2_hatch`: tread plate under melting snow with the cast date; lifting
  with its thick edge; open with its ribbed underside, hinge knuckles, soot); the lane gets columns of soft smoke
  from every burst window merging into a mass under the cornice (snow falls in front), flames licking out
  (`flame_out`), halos, glass shards that glint and stay twinkling in the snow, onlookers who react (take sequences
  in layout `escape.e4_people[].seq`: flinch, hands to the face, a step back, pointing, walking to the engine) and
  the fire engine nosing in (`engine`) with its turning blue beacon (`beacon`, `beacon_wash`).
* **Halves:** h3's smoke column is the soft `h3_plume` (no flat sheet, no holes) drifting east; the dawn is visible
  (`h3_dawn`: the sky lifts, a pale band and a rose-grey line on the right horizon; horizon ≈ RGB 13,17,26 → 80,86,112);
  soft `smoke`, `steam`, `breath`; window fires from `fire_sheet`.

## Round 11 — figures (art-director pass: anatomy, no paper dolls)
Figures stream (`env_c3p2_cine_body` / `_hero` / `_people` / `_figs` / `_hands`).  Rig: a short, strong neck (the
head sits 6 units lower, the neck ~0.7 of the head's width, the trapezius high and flat — no bottle shoulders),
collars resized to it; skin ramps per scene light with warm shadows (`skin_ramp`, no lilac / mauve); cropped hair
with strands from the crown and a soft hairline at the nape (`pass_hair_strands`, `hair_fade`); anatomical sleeves
(deltoid / biceps mass, a slim elbow, the forearm tapering to the cuff, folds only in the bend); a larger palm;
the close shots trace a deeper volume (a hand far up a desk was cut away by the old ±90 px one).  An arm that moves
is never also part of its body sprite: its sheet holds it in every frame and is drawn under the body.
* **Radio:** `arm_alexei` 6 frames (resting on the table, lifting, on the way × 2, on the knob, turning; runtime
  `ARM_KEYS`), Alexei leans toward the set; `hand_konrad` 18 frames — Konrad writes with his LEFT hand and a pencil
  (the pad lies at his front-left): 6 positions × 2 strokes, then the 6 positions with the pencil lifted; the
  runtime picks the position the growing line has passed and shifts the sprite the rest of the way
  (`_apply_pencil_hand`), the line itself (`pad_line`, from `env_c3p2_cine_figs.PAD_LINE`) runs on the part of the
  notepad the radio does not cover.
* **Fire:** `f1_konrad` 4 frames (head bowed, lifting, up, turned toward the smoke; runtime `LOOK_KEYS`), the whole
  seated man on an archive chair down to the frame's bottom, the overcoat a dark slate navy under the green lamp.
* **Escape:** `e1_file` — the forearms come in from the lower corners, the hands lie flat on the file's back with
  spread fingers and thumbs; `e2_konrad` 6 frames (shoulders, waist, a knee on the rim, on all fours beside the
  hatch, two crawl steps — no jump; runtime `KONRAD`); `e3a_hands` 7 frames (the hand rises, opens, Konrad's open
  hand comes in, closes round the wrist, the pull in three steps; runtime `HANDS`); `e3b_men` from a low camera
  (profiles, lying in the snow with an uneven lip, no rim outline).
* **Halves:** `fig_alexei` / `fig_konrad` 4 frames (breath × 2, leaning over half / fully for the far stack);
  `arms` 2 rows × `arm_cols` (14) cells of 248 × 132 at `arms_at`: reach in three steps near / far, the pull with the
  pages (two cells each; the runtime shifts the sprite with the sliding stack), the hold, Konrad's list in his hand
  beside his hip (3 cells; the fold is drawn at layout `list_fold_at`); runtime `_apply_arms`.

## Art — `assets/cinematics/c3p2/radio/` (LS_C3_Radio, 30.8 s)
| File | Use |
|---|---|
| `square_bg`, `square_glow`, `win_konrad`, `win_alexei`, `steam` (6) | r1/r6: the station square from the station roof (pinhole projection, supersampled facades re-quantised): Hotel Europa (mansard, arches, sign) and Hotel Nord (flat roof, roof letters) facing each other, tram rails, lamp pools, the advertising column, lime trees, the palais with its dome and dark east wing (one dim window high up); the two lit windows with a man at his radio; steam of the 23.40 |
| `door_konrad`, `door_alexei`, `walker_konrad`, `walker_alexei` (6), `walker_far_konrad`, `walker_far_alexei` (4) | r6: both hotel doors open at once, warm light on the snow; the two men walking out, and small far off at the wing after the dissolve (paths, trodden furrows and footprints over the whole way in layout.json converge on the east wing) |
| `room_alexei`, `room_konrad`, `radio`, `dial_glow`, `lamp_glow`, `magic_eye` (3) | r2/r3: the two rooms around one window/table geometry — Hotel Nord (painted plaster, cotton curtains, doily, the tea glass in its holder, the quilted coat and ushanka on the hook, Hotel Europa across with Konrad's lit window) and Hotel Europa (damask, wainscot, velvet curtains, brass desk lamp, notepad, his hat, coat and scarf on the stand, Hotel Nord across with Alexei's lit window); the same Bakelite set („Komet“, round dial with the two Veltrava marks, cloth grille, piano keys) at the same place — the needle is drawn at runtime and sweeps across the cut |
| `fig_alexei`, `fig_konrad` (2 frames: breath), `arm_alexei` (6), `hand_konrad` (18), `steam_tea` (6) | the men from behind without hats (roll-neck / jacket), each without the arm that moves; Alexei's right arm from the table to the tuning knob; Konrad's left arm writing with a pencil (6 positions × 2 strokes + lifted) |
| `doors`, `note_fold`, `note_close` | r4: split screen at floor level — room 214 (oxblood, plain) and room 317 (cream panels, brass kick plate), the corridor light in both gaps; the folded note; the note unfolded in pencil block letters, Russian above German (text copied from `de_c3p2_cinematics.json`) |
| `cafe`, `cafe_glow` | r5: Café „Korridor“ after closing — chairs upside down on the marble tables, Elena's table with an untouched glass of tea, reversed gold lettering, the station clock across the square (hands at runtime: 0.10) |

## Art — `assets/cinematics/c3p2/fire/` (LS_C3_Fire, 12 s)
| File | Use |
|---|---|
| `f1_bg`, `lamp_cone`, `f1_konrad` (4: head down / lifting / up / turned) | the card hall under the brick vault: oak card cabinets with brass label holders, the high barred window, the sorting table with the two halves laid side by side and the red thread of the check, drawer C-17 and Elena's wine-red scarf; the green-shaded lamp's cone (flickers at runtime); Konrad from behind |
| `f2_bg`, `f2_door` (4), `f2_glow` | the Magazin aisle in one-point perspective, archive boxes and the red C-17 tags; the service door: the figure in the lit doorway, half through, the empty doorway, shut |
| `f3_bg`, `f3_warm` | the iron-clad ramp door from inside (planks, straps, rivets, lock box), snow blown in under it; the runtime draws the cold gap light, the passing shadow and the bolt's shadow |
| `f4_bg`, `f4_lit`, `f4_table`, `f4_glow`, `fire_band`, `f4_alexei` (2) | the same hall before the fire reaches it (smoke under the vault, scorched drawer fronts); the fire's light on it (additive, revealed behind the front); the table as a layer in front of the flames; Alexei from behind against the fire (ushanka, fur collar, quilted coat, satchel strap) |
| `fire_mid`, `fire_big`, `fire_wide`, `fire_small`, `f2_fire_s`, `f2_fire_m`, `f2_fire_l` (8 frames each), `fire_halo` | round 11: fire clusters (licking tongues, white-hot cores, translucent red fringe) for the burning cabinets and the C-17 boxes; their additive bloom |
| `smoke`, `smoke_hot` (8), `ember` (4), `paper` (6) | soft lamp-lit and fire-lit smoke puffs (soft alpha), embers, burning paper |

## Art — `assets/cinematics/c3p2/escape/` (LS_C3_Escape, 16 s)
| File | Use |
|---|---|
| `e1_bg`, `e1_light`, `e1_file` (2) | up the brick coal chute with its steel slide toward the square of snow light; Konrad's sooty hands shoving the tied file |
| `e2_bg`, `e2_lamp`, `e2_hatch` (3), `e2_konrad` (4) | the yard: rusticated base of the east wing, a souterrain window glowing, the bracket lamp, the iron hatch frame in the snow; the lid closed / lifting / open with „1909“; Konrad out to the shoulders, to the waist, a knee on the rim, on hands and knees beside the hatch, two crawl steps (6 frames) |
| `e3a_bg`, `e3a_glow`, `e3a_hands` (7) | looking down into the hatch: Alexei's hand out of the smoke, Konrad's hand reaches in and takes it, the pull in three steps |
| `e3b_bg`, `e3b_hatch` (2), `e3b_men` (2) | low at the snow: the lid slammed, both men on their backs, heads together, the file between them, Konrad's hat in the snow |
| `e4_bg`, `e4_window` (3), `e4_glow`, `smoke`, `breath` (6) | the east wing from the lane (pilasters, pediments, mansard, the one lit window high up, the yard gate); a souterrain window dark / bursting / burning; soft smoke lit from below; breath clouds |
| `flame_s`, `flame_out` (8), `fire_halo`, `engine` (2), `beacon`, `beacon_wash`, `onlooker_N` / `onlooker_N_r1`, `fireman_N` | round 11: fire inside and licking out of the burst windows and its bloom; the fire engine's nose with its blue beacon (glow and the wash it throws); the onlookers' two takes (watching, reacting) and the firemen running in |

## Art — `assets/cinematics/c3p2/halves/` (LS_C3_Halves, 21 s)
| File | Use |
|---|---|
| `h1_bg`, `h1_glow`, `fig_alexei`, `fig_konrad` (4 each), `stacks` (3), `arms` (2×14), `list_fold` (4) | the quay bench from behind: the balustrade, the frozen river with the fire's glow, the Line with fence and two watchtowers (searchlight beams at runtime); the men; the Russian pages (with the list of names), the German pages, the list; arms reaching near / across / holding; the list folded into Konrad's coat |
| `h2_bg`, `h2_glow`, `walk_alexei`, `walk_konrad` (6 each) | the promenade with its lanterns and their bench; the two walking apart (Konrad mirrored at runtime) |
| `h3_bg`, `h3_glow`, `h3_dawn`, `h3_plume`, `flame_s`, `smoke` | wide: the palais with the burning east wing and its mirror image in the ice, the far bank with the Line's towers, the three-arch bridge; the soft smoke column leaning east; the first grey of dawn (faded in at runtime) |
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
`tests/test_c3p2_cinematics.gd` (21 cases, ~1190 checks): registration; contract and planned lengths; `finished`
exactly once (skip/skip, skip before play, natural end, fast-forward, replay); inner lines for every c3a×c3b and
c3d×c3g combination, spoken in order, non-overlapping, inside the film, ≤ 19 characters per second, German text
present, every radio line over its own picture (round 11); skip stops the cues; reduced/full motion; shot order; no missing texture and layout keys in sync with the
scripts (dial = match cut); every cued sound exists and every loop is stopped; sound/picture timings shared with the
audio generator (lamp dips, chute shoves, window bursts); frames a pure function of t (seek away and back); the match
cut on the dial; who takes which pages per c3g; reduced motion halves the travel; fire light never strobes (≤ 3 Hz,
small frame-to-frame changes). In-game: real-time runs 30.8 / 12.0 / 16.0 / 21.0 s wall time, `finished` once,
~4.2 ms frames (harness `--c3-mode=run`).
