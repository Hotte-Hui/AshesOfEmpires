# Asset manifest part -- env_berlin (M1 Berliner Bauarchiv round 2, plan documents)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_berlin.py` drives `env_berlin_room.py`, `env_berlin_hall.py`, `env_berlin_library.py`,
`env_berlin_ext.py`, `env_berlin_props.py`, `env_berlin_fg.py`, `env_berlin_fx.py`, `env_berlin_actors.py`,
`env_berlin_insignia.py`, `env_berlin_docs.py`, helpers `env_berlin_kit.py`, `env_berlin_layout.py` and the
shared, read-only `pg.py`).  No pixels were copied, traced or sampled from the reference images in
`documentation/references/` (style study only).  No third-party assets, fonts or textures are embedded;
the tiny bitmap fonts are hand-defined in `env_berlin_kit.py`.  Sounds: `tools/audiogen/berlin_env_sfx.py`
(numpy synthesis, no samples).

* Licence / rights: project-owned original artwork (generated for this project), freely
  redistributable with the game.  Provenance: deterministic generator, re-run with
  `py -3 -P tools/pixelgen/env_berlin.py` and `py -3 -P tools/audiogen/berlin_env_sfx.py`.
* Date: 2026-11-04.  Palettes: `archive` (+ local `green`, `graphite` ramps), `berlin` (+ archive ink reds for flag
  cloth), `sepia`.
* Insignia (TECHNICAL_ARCHITECTURE 12.4): the layers carry only the neutral art (fictional Reichssiegel /
  a plain eagle).  The historical variants (`*_hist.png`: Reichsadler with the wreathed swastika on the
  plaque and the AUFBAU poster, the swastika flag on the facade banners, eagle seals on plan A / plan B /
  Emil's slip) are separate files chosen at runtime by `Symbols.pick()` -- in-world iconography of the regime
  inside the critical narrative only, never UI, rewards or player decoration.  Drawn from original geometry
  in `env_berlin_insignia.py` (no traced emblem).
* The Great Hall is fictional and shown muted, not heroic.
* Locale `data/locale/de_env_berlin.json` is hand-written original German text (Konrad's voice).
* `env_berlin_stills.py` / `x1_*.png` were made by this area in round 1; they now belong to the transition
  work and are not rebuilt by `env_berlin.py` (see that owner's manifest part).

| File | Generator | Content |
|---|---|---|
| `assets/environments/berlin_archive/actors/mouse.png` | `tools/pixelgen/env_berlin_actors.py` | archive mouse, 8 frames: peek, sniff, out, run |
| `assets/environments/berlin_archive/actors/papers.png` | `tools/pixelgen/env_berlin_actors.py` | loose sheets lifting in the draught, 8 frames |
| `assets/environments/berlin_archive/actors/pendulum.png` | `tools/pixelgen/env_berlin_actors.py` | regulator clock pendulum, 12 swing frames |
| `assets/environments/berlin_archive/actors/pigeons.png` | `tools/pixelgen/env_berlin_actors.py` | feral pigeon, 10 frames: idle, peck, ruffle, turn, fly |
| `assets/environments/berlin_archive/actors/radio_glow.png` | `tools/pixelgen/env_berlin_actors.py` | radio dial + magic eye glow overlay, 3 frames |
| `assets/environments/berlin_archive/actors/smoke_curl.png` | `tools/pixelgen/env_berlin_actors.py` | cigarette smoke curl over the porter's ashtray, 16 frames |
| `assets/environments/berlin_archive/actors/spark.png` | `tools/pixelgen/env_berlin_actors.py` | pantograph spark, 4 frames (actor) |
| `assets/environments/berlin_archive/actors/steam.png` | `tools/pixelgen/env_berlin_actors.py` | radiator valve steam puff, 12 frames |
| `assets/environments/berlin_archive/actors/tram.png` | `tools/pixelgen/env_berlin_actors.py` | tram motor car + trailer, side view (actor) |
| `assets/environments/berlin_archive/actors/tube.png` | `tools/pixelgen/env_berlin_actors.py` | pneumatic tube flap + capsule, 6 frames |
| `assets/environments/berlin_archive/decals/decal_banner_1.png` | `tools/pixelgen/env_berlin.py` | facade banner banner_1, neutral variant |
| `assets/environments/berlin_archive/decals/decal_banner_1_hist.png` | `tools/pixelgen/env_berlin.py` | facade banner banner_1, historical variant |
| `assets/environments/berlin_archive/decals/decal_banner_2.png` | `tools/pixelgen/env_berlin.py` | facade banner banner_2, neutral variant |
| `assets/environments/berlin_archive/decals/decal_banner_2_hist.png` | `tools/pixelgen/env_berlin.py` | facade banner banner_2, historical variant |
| `assets/environments/berlin_archive/decals/decal_plaque.png` | `tools/pixelgen/env_berlin.py` | insignia site plaque, neutral variant |
| `assets/environments/berlin_archive/decals/decal_plaque_hist.png` | `tools/pixelgen/env_berlin.py` | insignia site plaque, historical variant |
| `assets/environments/berlin_archive/decals/decal_plaque_hist_n.png` | `tools/pixelgen/env_berlin.py` | insignia site plaque -- normal map |
| `assets/environments/berlin_archive/decals/decal_plaque_n.png` | `tools/pixelgen/env_berlin.py` | insignia site plaque -- normal map |
| `assets/environments/berlin_archive/decals/decal_poster.png` | `tools/pixelgen/env_berlin.py` | insignia site poster, neutral variant |
| `assets/environments/berlin_archive/decals/decal_poster_hist.png` | `tools/pixelgen/env_berlin.py` | insignia site poster, historical variant |
| `assets/environments/berlin_archive/decals/decal_poster_hist_n.png` | `tools/pixelgen/env_berlin.py` | insignia site poster -- normal map |
| `assets/environments/berlin_archive/decals/decal_poster_n.png` | `tools/pixelgen/env_berlin.py` | insignia site poster -- normal map |
| `assets/environments/berlin_archive/ext_far.png` | `tools/pixelgen/env_berlin_ext.py` | far city, smoke and the fictional Great Hall dome (muted, hazy) |
| `assets/environments/berlin_archive/ext_far_e.png` | `tools/pixelgen/env_berlin_ext.py` | far city, smoke and the fictional Great Hall dome (muted, hazy) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/ext_near.png` | `tools/pixelgen/env_berlin_ext.py` | Gruenderzeit tenements across the street, state banners (neutral), tram contact wires, street lamps |
| `assets/environments/berlin_archive/ext_near_e.png` | `tools/pixelgen/env_berlin_ext.py` | Gruenderzeit tenements across the street, state banners (neutral), tram contact wires, street lamps -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/ext_sky.png` | `tools/pixelgen/env_berlin_ext.py` | Berlin winter dusk sky (seen through windows) |
| `assets/environments/berlin_archive/fg_frame.png` | `tools/pixelgen/env_berlin_fg.py` | foreground framing silhouettes (columns, plants, desk, chair, hanging lamps) |
| `assets/environments/berlin_archive/fx_dust_archive.png` | `tools/pixelgen/env_berlin_fx.py` | warm dust motes under the archive pendant (16-frame loop) |
| `assets/environments/berlin_archive/fx_dust_hall.png` | `tools/pixelgen/env_berlin_fx.py` | dust motes hovering in the window shafts (16-frame loop) |
| `assets/environments/berlin_archive/fx_dust_library.png` | `tools/pixelgen/env_berlin_fx.py` | dust motes hovering in the window shafts (16-frame loop) |
| `assets/environments/berlin_archive/fx_dust_office.png` | `tools/pixelgen/env_berlin_fx.py` | dust motes hovering in the window shafts (16-frame loop) |
| `assets/environments/berlin_archive/fx_dust_reading.png` | `tools/pixelgen/env_berlin_fx.py` | motes in the green reading-lamp light (16-frame loop) |
| `assets/environments/berlin_archive/fx_window_snow.png` | `tools/pixelgen/env_berlin_fx.py` | seamless snowfall tile seen through the windows (16-frame loop, behind the room layer) |
| `assets/environments/berlin_archive/props/bench.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench; a forgotten hat and a newspaper |
| `assets/environments/berlin_archive/props/bench_n.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench; a forgotten hat and a newspaper -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/book_trolley.png` | `tools/pixelgen/env_berlin_props.py` | book trolley with volumes waiting to be shelved |
| `assets/environments/berlin_archive/props/book_trolley_n.png` | `tools/pixelgen/env_berlin_props.py` | book trolley with volumes waiting to be shelved -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/card_catalogue.png` | `tools/pixelgen/env_berlin_props.py` | card catalogue cabinet with a drawer pulled out |
| `assets/environments/berlin_archive/props/card_catalogue_n.png` | `tools/pixelgen/env_berlin_props.py` | card catalogue cabinet with a drawer pulled out -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/coat_stand.png` | `tools/pixelgen/env_berlin_props.py` | bentwood coat stand with a grey coat, hat and umbrella |
| `assets/environments/berlin_archive/props/coat_stand_n.png` | `tools/pixelgen/env_berlin_props.py` | bentwood coat stand with a grey coat, hat and umbrella -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/counter.png` | `tools/pixelgen/env_berlin_props.py` | Emil's issue counter: banker's lamp, stamps, card files |
| `assets/environments/berlin_archive/props/counter_e.png` | `tools/pixelgen/env_berlin_props.py` | Emil's issue counter: banker's lamp, stamps, card files -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/counter_n.png` | `tools/pixelgen/env_berlin_props.py` | Emil's issue counter: banker's lamp, stamps, card files -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/drafting_covered.png` | `tools/pixelgen/env_berlin_props.py` | absent colleague's board under a dust sheet (obs_photo) |
| `assets/environments/berlin_archive/props/drafting_covered_n.png` | `tools/pixelgen/env_berlin_props.py` | absent colleague's board under a dust sheet (obs_photo) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/drafting_konrad.png` | `tools/pixelgen/env_berlin_props.py` | Konrad's drafting board with the approved plan (plan_a) |
| `assets/environments/berlin_archive/props/drafting_konrad_e.png` | `tools/pixelgen/env_berlin_props.py` | Konrad's drafting board with the approved plan (plan_a) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/drafting_konrad_n.png` | `tools/pixelgen/env_berlin_props.py` | Konrad's drafting board with the approved plan (plan_a) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/flat_file.png` | `tools/pixelgen/env_berlin_props.py` | plan chest; the drawer with the archived draft is pulled out (plan_b) |
| `assets/environments/berlin_archive/props/flat_file_n.png` | `tools/pixelgen/env_berlin_props.py` | plan chest; the drawer with the archived draft is pulled out (plan_b) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/globe.png` | `tools/pixelgen/env_berlin_props.py` | floor globe on a tripod stand (exp_globe) |
| `assets/environments/berlin_archive/props/globe_n.png` | `tools/pixelgen/env_berlin_props.py` | floor globe on a tripod stand (exp_globe) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/hall_bench.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench under the chronicle photos: briefcase, gloves |
| `assets/environments/berlin_archive/props/hall_bench_n.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench under the chronicle photos: briefcase, gloves -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/ladder.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the shelf rail |
| `assets/environments/berlin_archive/props/ladder_n.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the shelf rail -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/lib_catalogue.png` | `tools/pixelgen/env_berlin_props.py` | reading-room card catalogue: 9 x 4 drawers, one pulled out (exp_card_catalogue) |
| `assets/environments/berlin_archive/props/lib_catalogue_n.png` | `tools/pixelgen/env_berlin_props.py` | reading-room card catalogue: 9 x 4 drawers, one pulled out (exp_card_catalogue) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/lib_desk.png` | `tools/pixelgen/env_berlin_props.py` | librarian's desk: green lamp, date stamp, card trays, returned books, tube terminal |
| `assets/environments/berlin_archive/props/lib_desk_e.png` | `tools/pixelgen/env_berlin_props.py` | librarian's desk: green lamp, date stamp, card trays, returned books, tube terminal -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/lib_desk_n.png` | `tools/pixelgen/env_berlin_props.py` | librarian's desk: green lamp, date stamp, card trays, returned books, tube terminal -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/lib_ladder.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the brass rail (sections I/II) |
| `assets/environments/berlin_archive/props/lib_ladder_n.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the brass rail (sections I/II) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/light_table.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) |
| `assets/environments/berlin_archive/props/light_table_e.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/light_table_n.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/plan_basket.png` | `tools/pixelgen/env_berlin_props.py` | wicker stand with rolled plans (in front of the walk line) |
| `assets/environments/berlin_archive/props/plan_basket_n.png` | `tools/pixelgen/env_berlin_props.py` | wicker stand with rolled plans (in front of the walk line) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/porter_lodge.png` | `tools/pixelgen/env_berlin_props.py` | porter's lodge: panelled front, glazing with an open hatch, visitors' book |
| `assets/environments/berlin_archive/props/porter_lodge_e.png` | `tools/pixelgen/env_berlin_props.py` | porter's lodge: panelled front, glazing with an open hatch, visitors' book -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/porter_lodge_n.png` | `tools/pixelgen/env_berlin_props.py` | porter's lodge: panelled front, glazing with an open hatch, visitors' book -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/reading_table.png` | `tools/pixelgen/env_berlin_props.py` | reading table under the tilted window: two green lamps, open books, chairs |
| `assets/environments/berlin_archive/props/reading_table_e.png` | `tools/pixelgen/env_berlin_props.py` | reading table under the tilted window: two green lamps, open books, chairs -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/reading_table_n.png` | `tools/pixelgen/env_berlin_props.py` | reading table under the tilted window: two green lamps, open books, chairs -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/stool_konrad.png` | `tools/pixelgen/env_berlin_props.py` | tall drafting stool pushed aside |
| `assets/environments/berlin_archive/props/stool_konrad_n.png` | `tools/pixelgen/env_berlin_props.py` | tall drafting stool pushed aside -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/typist_desk.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair |
| `assets/environments/berlin_archive/props/typist_desk_e.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/typist_desk_n.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/umbrella_stand.png` | `tools/pixelgen/env_berlin_props.py` | umbrella stand by the door, two umbrellas, a puddle of melt water |
| `assets/environments/berlin_archive/props/umbrella_stand_n.png` | `tools/pixelgen/env_berlin_props.py` | umbrella stand by the door, two umbrellas, a puddle of melt water -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/room.png` | `tools/pixelgen/env_berlin_room.py` | interior: arrival hall + porter's lodge, reading room & library, office, archive hall, light-table room, issue counter (neutral insignia; hist variants are decals) |
| `assets/environments/berlin_archive/room_e.png` | `tools/pixelgen/env_berlin_room.py` | interior: arrival hall + porter's lodge, reading room & library, office, archive hall, light-table room, issue counter (neutral insignia; hist variants are decals) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/room_n.png` | `tools/pixelgen/env_berlin_room.py` | interior: arrival hall + porter's lodge, reading room & library, office, archive hall, light-table room, issue counter (neutral insignia; hist variants are decals) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/scene.json` | `tools/pixelgen/env_berlin.py` | art manifest (TECHNICAL_ARCHITECTURE 3.1, 12.2 hotspots, actors) |
| `assets/environments/berlin_archive/shafts.png` | `tools/pixelgen/env_berlin.py` | volumetric daylight-shaft veil (soft alpha, additive blend hint) |
| `assets/environments/berlin_archive/win_outer.png` | `tools/pixelgen/env_berlin_actors.py` | outer stone window sills with snow (behind the glass; the pigeons sit here) |
| `assets/ui/documents/berlin_emil_note.png` | `tools/pixelgen/env_berlin_docs.py` | Emil's handwritten archive slip (Serie C-17), printed Reichssiegel |
| `assets/ui/documents/berlin_emil_note_hist.png` | `tools/pixelgen/env_berlin_docs.py` | Emil's slip, historical-insignia variant (printed eagle) |
| `assets/ui/documents/berlin_plan_a.png` | `tools/pixelgen/env_berlin_docs.py` | approved public floor plan (supply wing closed), 18x12 cells, Reichssiegel seal |
| `assets/ui/documents/berlin_plan_a_hist.png` | `tools/pixelgen/env_berlin_docs.py` | plan A, historical-insignia variant (eagle seal) |
| `assets/ui/documents/berlin_plan_a_lines.png` | `tools/pixelgen/env_berlin_docs.py` | approved public floor plan (supply wing closed), 18x12 cells, Reichssiegel seal -- lines only on transparent (overlay UI) |
| `assets/ui/documents/berlin_plan_a_lines_hist.png` | `tools/pixelgen/env_berlin_docs.py` | plan A, historical-insignia variant (eagle seal) -- lines only on transparent (overlay UI) |
| `assets/ui/documents/berlin_plan_b.png` | `tools/pixelgen/env_berlin_docs.py` | archived 1958 draft: corridor behind a second wall, pencil C-17 |
| `assets/ui/documents/berlin_plan_b_hist.png` | `tools/pixelgen/env_berlin_docs.py` | plan B, historical-insignia variant (receipt stamp with eagle) |
| `assets/ui/documents/berlin_plan_b_lines.png` | `tools/pixelgen/env_berlin_docs.py` | archived 1958 draft: corridor behind a second wall, pencil C-17 -- lines only on transparent (overlay UI) |
| `assets/ui/documents/berlin_plans.json` | `tools/pixelgen/env_berlin_docs.py` | overlay puzzle data: cells, landmarks, solution (+2,-1,rot 0), hidden corridor rects |
| `assets/audio/sfx/berlin_tram_rumble.wav` | `tools/audiogen/berlin_env_sfx.py` | tram rumble loop: motor hum, rail joints, muffled by the window (44.1 kHz mono) |
| `assets/audio/sfx/berlin_tram_bell.wav` | `tools/audiogen/berlin_env_sfx.py` | tram bell, two strikes (44.1 kHz mono) |
| `assets/audio/sfx/berlin_pigeon_coo.wav` | `tools/audiogen/berlin_env_sfx.py` | pigeon cooing (44.1 kHz mono) |
| `assets/audio/sfx/berlin_pigeon_flutter.wav` | `tools/audiogen/berlin_env_sfx.py` | pigeons taking off (44.1 kHz mono) |
| `assets/audio/sfx/berlin_mouse_squeak.wav` | `tools/audiogen/berlin_env_sfx.py` | mouse squeaks (44.1 kHz mono) |
| `assets/audio/sfx/berlin_clock_tick.wav` | `tools/audiogen/berlin_env_sfx.py` | regulator tick (44.1 kHz mono) |
| `assets/audio/sfx/berlin_clock_tock.wav` | `tools/audiogen/berlin_env_sfx.py` | regulator tock (44.1 kHz mono) |
| `assets/audio/sfx/berlin_clock_chime.wav` | `tools/audiogen/berlin_env_sfx.py` | quarter-hour chime (44.1 kHz mono) |
| `assets/audio/sfx/berlin_radiator_knock.wav` | `tools/audiogen/berlin_env_sfx.py` | water hammer knocking in the heating pipes (44.1 kHz mono) |
| `assets/audio/sfx/berlin_radiator_hiss.wav` | `tools/audiogen/berlin_env_sfx.py` | steam hiss at the radiator valve (44.1 kHz mono) |
| `assets/audio/sfx/berlin_radio_loop.wav` | `tools/audiogen/berlin_env_sfx.py` | faint dance music from the porter's radio (loop) (44.1 kHz mono) |
| `assets/audio/sfx/berlin_paper_flutter.wav` | `tools/audiogen/berlin_env_sfx.py` | papers lifting in a draught (44.1 kHz mono) |
| `assets/audio/sfx/berlin_tube_capsule.wav` | `tools/audiogen/berlin_env_sfx.py` | pneumatic tube capsule arriving (44.1 kHz mono) |
| `data/locale/de_env_berlin.json` | hand-written | observation prompts/texts (obs_window, obs_notice, obs_photo), canonical hotspot prompts |
| `scripts/levels/berlin/*.gd`, `scenes/levels/berlin/*.tscn` | hand-written | ambient actors (tram, pigeons, mouse, clocks, radiator, radio, papers, tube, anim) |
| `tests/visual/berlin_env_capture.gd/.tscn`, `tests/visual/berlin_actors_check.gd` | hand-written | visual harness (no post) and headless actor/decal behaviour check |
