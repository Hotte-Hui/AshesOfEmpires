# Asset manifest part — c3_cine (Chapter-3 cinematics LS_C3_Trains, LS_C3_ToHall, LS_C3_Close)

* **Date:** 2026-11-05/06 (finishes the c3-cine work started in the cloud session of 2026-11-04/05)
* **Area owner:** cinematics stream (C3_DESIGN.md §2.9, §7)
* **Scenes / code:** `scenes/cinematics/ch3_trains/` (`Ch3Trains.tscn`, `ch3_trains.gd`), `ch3_tohall/`, `ch3_close/`,
  shared `ch3_common/` (`c3_cinematic.gd` = the §12.5 contract: `finished` exactly once, idempotent `skip()`,
  `configure(ctx)` picks the inner lines from the story flags, `seek()`/`advance()` for tools and tests, cue list for
  subtitles/sound/loops, reduced motion; `pixel_fx.gd` = deterministic snow and 1 px Bresenham wires/hands;
  `c3_dissolve*.gdshader` = ordered-dither dissolve, one Bayer cell per world pixel). Registered in
  `data/chapters/c3.json` → `cinematics`, played by `ChapterExt.play_cinematic()`.
* **Generators:** `py -3 -P tools/pixelgen/env_veltrava_cine.py [--only trains,tohall,close]` writes every texture and
  `assets/cinematics/ch3/layout.json` (anchors shared with the runtimes; `tests/test_c3_cinematics.gd` checks the
  match-cut geometry, the clock centre and the platform projection against it). Modules:
  `env_veltrava_cine.py` (trains interiors + exterior + flare, build/main), `env_veltrava_cine_dawn.py` (t4),
  `env_veltrava_cine_tohall.py`, `env_veltrava_cine_close.py`, `env_veltrava_cine_kit.py` (fonts via
  `env_veltrava_lib`, rings, dial indices, dithered puffs), `env_veltrava_cine_figs.py` (the two protagonists).
  Sound: `py -3 -P tools/audiogen/c3_cine_audio.py` → `assets/audio/sfx/c3cine_*.wav`.
* **Figures:** Konrad and Alexei at the compartment windows (from behind), their faces in the black glass and
  Konrad's profile are sculpted and lit with the signed-distance pipeline of the dialogue portraits
  (`chargen_portrait2_anat/_cast/_paint/_sdf`, imported read-only, nothing there modified): the specs `konrad()` /
  `alexei()` supply heads, hats, hair and coat materials, so the cinematic figures follow the portraits. Renders are
  memoised on disk (`%TEMP%/ashes_c3cine_cache`, keyed by the pipeline sources + arguments, results byte-identical;
  `ASHES_NO_CACHE=1` disables it).
* **Figures, round 10 (figures stream):** the round-7 busts had two capsules per arm with the forearms hidden behind
  the back and a hand painted separately into the room, so arms read as stumps growing out of the chest. New modules:
  `env_veltrava_cine_rig.py` (one continuous chain per arm: shoulder, upper arm, elbow with the sleeve's folds and
  the point of the elbow, forearm, shirt cuff, wrist, a hand of palm, knuckles, three phalanges per finger and a
  two-joint thumb; limbs modelled in view space with radii tapering toward the window, which fakes the room's
  perspective; point lights — reading lamp, tea glass, chandelier — added to the painter; split finger materials
  for the dark gaps between fingers), `env_veltrava_cine_heroes.py` (seated Konrad: left forearm along the table, the
  hand holding the cup by its handle, thumb on top, the right elbow out, the buttoned club chair hiding his hips;
  seated Alexei: the right hand at the holder's handle, quilted sleeves with stitched rings, the satchel strap on
  the outer coat; breath frames lift only head and shoulders, hand and chair stay put; Konrad walking under the
  palais clock as an 8-frame cycle; the contact shadows of the arms on the tables) and
  `env_veltrava_cine_people.py` (full-body extras from the same rig — legs with knees and shoes, coats that open
  with the stride, 17 kinds from travellers to the police of the Free City, walk / stand / sit poses, dawn / day /
  palais / night light presets; `person_sheet()` is the API the places builder calls; the passengers behind the lit
  windows of the dawn trains, Konrad and Alexei at one window each; the two hotel-window silhouettes as hand-set
  pixel templates). `env_veltrava_cine_figs.py` is unchanged (the other film families import it).
* **Figures, round 10b (art-director pass):** the hands at the cup and the tea glass are drawn at the scale of
  the cup and the glass (~1.85 px/cm; round 10's were 14 x 11 and 18 x 16 px mittens): hook grips with the first
  phalanges straight out of the knuckles (`rig.hand(joints=...)`), the thumb on top, and `finger_marks` drawing
  the gaps between the four fingers along their projected axes (`rig.hand_axes`); Alexei's fist closes round the
  holder's handle, whose bar the sprite repeats in lit nickel silver. Konrad's hat: a real ribbon band
  (`hat_band`) and a crown that ends at the brim (`fedora_cut`; the portrait crown's felt strip under the brim made
  the dashed line round the crown). The walking Konrad is a whole man (see `k2_konrad`), his rims drawn along the
  outline (`contour_rim`). The extras got profile faces (`face_marks`: eye, brow, closed mouth, ear; heads carried
  forward), straight-hanging men's coats, and cases / lanterns hanging from the fist by their handles.
* **Determinism:** fixed seeds everywhere (`np.random.default_rng(n)`, `zlib.crc32(name)` for audio); two full builds
  are byte-identical (checked with md5 over all PNG/WAV outputs).
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio made for ASHES OF
  EMPIRES: THE LAST WINTER by these generators (AI-authored code, project-owned, same licence as the game). No
  downloaded, copied or traced images, fonts or samples. No real insignia anywhere in these cinematics (pennants and
  flags are plain), so there are no `_hist` variants.
* **Palettes:** `veltrava` and `palais` ramps of `data/chapters/c3.json` (registered by `env_veltrava_lib`) plus the
  protagonists' material ramps of the portrait pipeline; grade `c3_cine` (no palette snap, light vignette and grain).

## Art — `assets/cinematics/ch3/trains/` (LS_C3_Trains, 36 s; round 10 rework: t3b new, t4 a crane shot)
| File | Use |
|---|---|
| `ext_sky`, `ext_far_de`, `ext_far_su`, `ext_near` | the night plain behind the glass: overcast sky lit from the Line, the floodlit double fence with masts and watchtowers (seen from the west / from the east), the embankment streaks; tileable 640 px strips scrolled per layer |
| `ext_mid_de`, `ext_mid_su` | (round 10, `env_veltrava_cine_journey.py`; AD round 2: placed at `trains.mid_y0` = row 150, they had sat 32 px low behind the embankment) the land between train and Line: in the west farmland, a village of half-timbered houses round its slate steeple (lit clock), a farm road (the runtime drives a car's lamps along it), a barn, birches; in the east log houses with carved window frames and smoking chimneys (runtime smoke), the wooden onion-dome church, a well sweep, the kolkhoz barn and a haystack |
| `pass_station` | (round 10) the halt „Erlengrund" that the saloon car rushes through without a stop: platform with its white edge and three lamps (their light sweeps through the car), station house with lit office window and name board, canopy, bench, parcel cart, signal box; the station master with his lantern under a lamp (its warm pool round his boots) and a porter at the parcel cart (figures-stream sheets stamped in; AD round 2: stamped at canvas rows -- the first version passed world rows and the station master was clipped away) |
| `pass_river`, `pass_river_obj` (4 cells) | (AD round 2 rework) the frozen river seen from the truss bridge in perspective: a ground image painted with the river's centre under the glass (scoured dark ice, snow tongues running down the river, an open lead with sea smoke and frost on its rims, white fracture lines, a trodden path and a sled track across, fishing holes, the snowy banks with reeds frozen in, the bend where the river turns away between two clumps of pollard willows and a fisherman's hut with a lit window). The runtime scrolls every row at the speed of its own depth (`layout.json` `trains.river`: vanishing row, bend, bottom-row speed), so the valley swings past like a wiper and slides in from the window's edge; the lateral ends fade into the plain. `pass_river_obj` = upright things on the ice drawn at the depth of their foot: an ice-fishing tent with its lantern, a fisher at the hole (figures stream), a rowing boat frozen in by the bank, a marker pole. The bridge is world-locked (portals pass the glass at 11.7 / 13.7 s, 13 bays, inclined end posts); over it the embankment strip and the car's window light on the snow give way to the drop |
| `pole` | telegraph pole with crossarms and insulators (the runtime strings the sagging wires between poles) |
| `int_konrad`, `fig_konrad` (4 frames), `refl_konrad`, `glow_lamp`, `patch_warm` | the German delegation's saloon car (figures: `env_veltrava_cine_heroes`, figures stream); the runtime adds the coffee's steam and the curtain tassels swinging with the joints |
| `int_alexei`, `fig_alexei` (4 frames), `refl_alexei`, `glow_tea`, `steam_tea` (6), `spoon` (2), `patch_cold` | the Soviet compartment (figures: `env_veltrava_cine_heroes`); the runtime adds the towel on the berth rail swinging with the joints |
| `sweep`, `flare`, `roomflare_k`, `roomflare_a` | the floodlit level crossing of the match cut (light band, the glass flooded, the room and the sitter's rim lit); `roomflare_*` also carries the flash of the passing lamps; the runtime adds the crossing's blinking red lamps and cross sign, two green signals |
| `l3_bg`, `l3_fg`, `l3_glow` | (round 10, `env_veltrava_cine_line.py`, t3b) the Line before dawn from high above in one-point perspective: night sky with the low cloud lit by the fence and by the city, the eastern horizon paling, the Free City glowing at the vanishing point; the snow plain, the raked control strip and patrol road between the double fence, light pools of the masts, both tracks on their embankments with telegraph poles and wires, villages with a steeple and an onion dome; `l3_fg` = fence posts, floodlight masts and watchtowers in front of the trains; `l3_glow` = mast halos and the city glow. The runtime draws both trains in the same projection (`line.proj`): lit windows on the inner sides, Konrad's salon car, Alexei's sealed wagon 4, red tail lamps, the plumes lit by the fireboxes, the towers' searchlights, snow |
| `d4_sky`, `d4_sun_glow` | (round 10, `env_veltrava_cine_city.py`, t4 crane plane „sky", travel 40 px) winter dawn: slate overhead, rose-cream low in the east, stratus banks with lit undersides, the low sun (it climbs out of the station roof while the camera rises) and its additive warmth |
| `d4_city`, `d4_dome_glow` | (plane „city", travel 105 px) Veltrava from the river: the castle hill (AD round 2: a crag of rock buttresses with snow on the ledges, spruce stands and birches on the flanks, the road zig-zagging up between retaining walls and lamps to the gatehouse; the castle with curtain wall, merlons and arrow slits, two round towers with conical roofs, the keep with its corbelled timber gallery and steep roof under a plain pennant, the palas with dormers, chimneys and lit windows, a chapel with its ridge turret, the stair tower's copper cap -- dawn on the east faces), the cathedral with two spires, the palais of the Commission (portico, pilasters, drum and the patinated dome catching the first sun), the onion church, the town hall with its copper spire and lit clock, the station's arched glass hall and tower, the old town (gables, mansards, stepped gables, brick and stucco, snow on every roof, lit windows), the quay rank with shopfronts, tram rails, wire poles and lamps, the quay wall and the water beyond the bridge with floating ice; `d4_dome_glow` = first sun on the dome and the station roof |
| `d4_bridge`, `d4_parapet`, `d4_lamp_glow` | (plane „bridge", travel 140 px) the three-arch stone bridge (far railing, deck, far track, signal posts, spandrel, voussoirs, icicles; the arches open so the far quay shows through with parallax), the river in front (dark water, short dawn streaks, the arches mirrored, ice sheets with pressure ridges and a wet rim, floes, a fishing hole and its wind screen, a sled track); the near parapet with its seven lanterns (in front of the trains) and their halos |
| `d4_bank` | (plane „bank", travel 225 px) the near bank of the low start: the promenade path, the iron fence along the crest, a bench, a dark lamp, reeds, snow-laden bushes, a rowing boat frozen in, the bollard, footprints, the willow leaning over the river with its hanging twigs |
| `d4_tram` (2 frames), `d4_gull` (4 frames), `d4_chimney_smoke` (6 frames) | the cream-and-red tram on the quay (trolley spark), gulls / crows over the city, thin chimney smoke |
| `train_de`, `train_su` (2 frames: pennants) | Konrad's train (grey-blue saloon cars, a salon car, pennants, engine running east) and Alexei's (green carriages, the sealed courier wagon 4 at its tail, engine running west) |
| `smoke` (8 frames) | (round 10) locomotive steam as clean pixel-art cauliflower puffs (lobes in 6 tones lit from the east, dithered only on tone borders and when it thins). AD round 2: the runtime varies growth, drift and frame per puff and fades each out; after the meeting the drivers shut off and coast in, the plumes thin to a wisp, so the final frame shows both trains and the old town |
| `pp_d4_*` | (round 10, `env_veltrava_cine_cast.py` -> `env_veltrava_cine_people.person_sheet`, figures stream) the extras of t4 by plane: the woman pulling her milk sled and a street sweeper on the bank, two ice fishers at their hole, four people on the quay; listed in `layout.json` `trains.people` (plane, place, speed) |

## Art — `assets/cinematics/ch3/tohall/` (LS_C3_ToHall, 6 s)
| File | Use |
|---|---|
| `k1_bg`, `k1_clock`, `k1_glass`, `steam_puffs` (8; AD round 2: one cloud at eight ages, cross-faded by the runtime, every puff living its own life -- no snapping back) (round 10: lit compartments with half-curtains, the route board МОСКВА · KORDON-17 · VELTRAVA, the conductor's door, the stove chimney (runtime smoke), two more hanging lamps; soft drifting steam; the runtime adds pigeons starting up at the minute's clack) | the cast-iron platform clock under the glazed canopy (lattice girder, frosted panes with drifted snow, fretwork valance), the green carriage and the misty old town beyond; the crystal's glare (additive); drifting steam |
| `k2_bg`, `k2_clock`, `k2_glass`, `pendulum` (8) | the gilded Jugendstil clock of the palais on its verde-antico panel between marble pilasters, the same dial geometry and index angles as the station clock (the match cut), its lyre pendulum |
| `k2_konrad` (8 frames, round 10b) | Konrad walking in under the clock: a whole man of ~112 px (hat to soles, inside the letterbox — round 10's 150 px bust was cut off at the chest) in profile, navy coat, taupe fedora with its ribbon band, camel scarf, the drafting tube on its strap. Legs by two-bone IK on a gait table (heel strike, flat foot, heel off, toe off, the swing with the knee folding; the planted foot slides back exactly one stride per cycle), the coat opening over the forward thigh, the arms swinging against the legs; lit by the chandelier with a continuous cold rim on his back and a warm rim along the hat and shoulders (drawn along the outline), a soft contact shadow on the marble under his feet. `layout.json` `tohall.konrad_path` (soles, he walks from the left edge at the cut to under the clock at 6 s), `konrad_anchor`, `konrad_stride` (88 px per cycle = 1.1 s, phased on the footstep sounds), `konrad_frames` |
| `ex_k1_*`, `ex_k2_*` (round 10, figures stream) | the extras (`env_veltrava_cine_people.EXTRAS['tohall']`, drawn by `scenes/cinematics/ch3_common/c3_people.gd` from `layout.json` `tohall.extras`): under the station clock a porter, a woman with her suitcase, the station master with his signal disc, a policeman of the Free City and a waiting man on the far platform; in the palais an usher at the door to the hall, two delegates talking by the wainscot, a secretary hurrying ahead of Konrad toward the hall, her briefcase hanging from her hand by its handle. Round 10b: every extra has a profile face (eye, brow, closed mouth, the ear; the head carried forward, never tipped back) and cases and lanterns hang from the fist |
Hands are drawn at runtime (1 px Bresenham) from the shown time 9:39:57 → 9:40:00.

## Art — `assets/cinematics/ch3/close/` (LS_C3_Close, 12 s; round 10: richer platform and square)
| File | Use |
|---|---|
| `n1_bg`, `n1_mid`, `n1_fg`, `board` (4 frames), `steam` (8, cross-faded) | platform 5 at 23:40 in one-point perspective (the pinhole `proj` the runtime uses to draw the departing special train as shrinking polygons): canopy, columns, lamps mirrored in the wet snow, the dual-gauge track, a goods train on the next track, the yard and the city at the vanishing point; the platform sign „5“ and a small clock at 23:40; the split-flap indicator (trilingual header) whose row clears after the departure |
| `n1_glow` | (round 10) additive light of platform 5: the canopy lamps' cones falling through the snow, their halos, the far signal at green (the special has a clear road) |
| `n2_bg`, `n2_win_konrad` (6), `n2_win_alexei` (6), `n2_lamp_glow` | the station square at night: Hotel Europa (mansard, balconies) and Hotel Nord (flat roof), snow on every ledge, the street into the old town with the palais dome, the lime trees and a parked car with someone smoking in it (runtime ember); the two lit windows where Konrad and Alexei step to the glass and turn toward the whistle. Round 10: more lit rooms in both hotels, lamps down the street into the old town, the kiosk with its shutters down, an advertising column, a telephone box, the tram stop, a taxi waiting at the Europa (runtime exhaust), the lobbies' light spilling onto the snow, footprint trails, bollards with their chain; the runtime raises a plume of steam over the roofs as the one whistle sounds. On platform 5 the goods train got real wagons (box cars with planks, straps and doors, tank wagons, a tarpaulin load; the end facing us with its brake wheel and tail board), a luggage trolley with mail sacks, crates, footprints; the engine's steam is soft drifting cloud. AD round 2: the right third is no longer an empty field under a straight horizon -- platform 6 under its own canopy (every other lamp lit, pools on the trodden snow, columns, the sign „6", a bench, a mail barrow), a sleeping-car train standing on track 8 with two lit compartments, the goods shed's snowy roof, the water tower and a floodlight mast of the yard over the goods train, a signal gantry, a water crane with its fire pot glowing, a plank crossing over tracks 5 and 6; the luggage barrow drawn as an oak barrow with canvas mail sacks tied at the neck, a parcel in string, a wicker hamper, the drawbar lowered; wooden crates instead of dark boxes |
| `ex_n1_*`, `ex_n2_*` (round 10, figures stream) | the extras of `EXTRAS['close']` (`layout.json` `close.extras`, placed in the platform's pinhole projection): a railwayman with his lantern at the platform edge, two men in long coats watching the special go, a policeman of the Free City by the near pillar; on the square a policeman walking his beat under the lamps, the Europa's doorman, a late traveller crossing from the station. The window silhouettes (`n2_win_*`) are hand-set pixel templates: head and jaw, neck, sloping shoulders, the turned profile with nose and chin, Alexei's tea glass at his chest, the room lamp's rim. Round 10b: six states shown on `close.win_seq` (each man comes in at the back of the room as a dim figure under the ceiling lamp, steps to the glass past the curtain, stands at the glass, turns his head halfway and then into profile after the whistle) instead of popping from an empty window to a silhouette |

## Sound — `assets/audio/sfx/` (`tools/audiogen/c3_cine_audio.py`, 44.1 kHz / 16-bit stereo)
| File | Content |
|---|---|
| `c3cine_ride_de.wav` (9.6 s) | the saloon car at night: rumble through the floor, padded rail joints (ta-tam every 1.55 s, in sync with the picture), wind at the glass, the panelling creaking |
| `c3cine_ride_su.wav` (9.4 s) | the Soviet car: harder joints every 1.8 s, loose fittings rattling, the spoon clinking in the tea glass on every knock |
| `c3cine_pass.wav` (1.2 s) | a lineside lamp post rushing past |
| `c3cine_crossing.wav` (2.4 s) | the level crossing at speed: its bell swells and drops in pitch, the rush of air |
| `c3cine_bridge.wav` (13.2 s) | two engines on the stone bridge at dawn: exhaust beats from both sides slowing, the hollow rumble of the arches, wheel clatter, the river valley echo (round 10: re-cut to the 12.5 s crane, the meeting 5.0 s in) |
| `c3cine_station_rush.wav` (2.8 s) | (round 10) the halt rushing past the saloon car: the platform wall throwing the rumble back, its bell dropping in pitch, three lamps whipping past |
| `c3cine_truss.wav` (3.0 s) | (round 10; AD round 2 re-cut to the 2 s bridge, bed at 11.55 s) the truss bridge over the frozen river: hollow steel drumming, a beat on every one of its 13 bays, the gorge's echo |
| `c3cine_line_night.wav` (7.2 s) | (round 10) the Line before dawn: wind over the snow, the hum of the floodlight masts, the two trains far off left and right |
| `c3cine_city_morning.wav` (5.8 s) | (round 10) the waking city: two church bells far apart, a tram's double ring, crows, the murmur of the streets |
| `c3cine_whistle_de.wav` (3.0 s) | Konrad's engine answering across the river, lower than the Karsk whistle |
| `c3cine_clock_tick.wav`, `c3cine_clock_clack.wav` | the seconds of the platform clock and the minute hand jumping to 9:40 |
| `c3cine_palais_chime.wav` (3.0 s) | one soft strike of the palais clock's gong spring |
| `c3cine_step_marble_1..3.wav` | leather heels on the marble of the foyer |
| `c3cine_depart_night.wav` (6.5 s) | the special train pulling out without a whistle: cylinder hiss, couplings snatching, heavy beats receding |
| `c3cine_flaps.wav` (1.0 s) | the split-flap indicator clearing its row |
Re-used (unchanged): `cine_a1m1_whistle_far` (the Karsk whistle — heard again from Alexei's engine at dawn and as
the one whistle over the night square: „Derselbe Pfiff“), `wind_gust`, `amb_veltrava_station`, `amb_veltrava_palais`,
`amb_transition`, `mus_veltrava` (starts at dawn and carries on into the station level).

## Checks
`tests/test_c3_cinematics.gd` (17 cases; round 10: 36 s Trains with shots t1 t2 t3 t3b t4, the layout keys of the
journey / Line / crane planes, both dissolves, the crane's plane offsets and its reduced-motion hold): registration, contract (`finished` once for skip/skip, skip before play,
natural end then skip, coarse fast-forward, replay), line variants for every flag combination, subtitles spoken in
order and localised, no cues after skip, reduced motion (no knocks, no roll), shot order, every texture and every cue
sound present, layout sync (glass/exterior box, clock centre, projection, runtime anchors), rail joints of the picture
== joints cut into the bed sounds, the dawn dissolve completes. Visual review: `tests/visual/c3cine_harness.tscn`
(`--c3-mode=shots|seq|run`).
`tests/test_c3_figures.gd` (5 cases, round 10 figures stream): the seated sheets have 4 frames and boxes that reach
the cup / the holder's handle, the palais walk has 8 frames, every extra has its sheet, an anchor inside the frame
and a time-ordered path, `c3_people.gd` interpolates paths and steps walk cycles by the distance walked, ToHall and
Close mount one people drawer per shot and follow the timeline.
