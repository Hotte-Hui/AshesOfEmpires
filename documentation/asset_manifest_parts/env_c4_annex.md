# Asset manifest part -- env_c4_annex (Chapter 4 part 1, Konrad's Berlin: the tram loop and the registry annex, L_C4_Annex)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_c4_annex.py` drives `env_c4_annex_loop.py` (street), `env_c4_annex_hall.py` (annex), `env_c4_annex_fx.py`
(strips), `env_c4_annex_docs.py` (inspect documents); helpers `env_c4_annex_kit.py`, `env_c4_annex_layout.py`, and
-- read-only -- `pg.py`, the tone-space painter / light bake / bitmap fonts of `env_veltrava_hall_kit.py`, the generic
painters of `env_c3p2_archive_kit.py` and the insignia drawings of `env_berlin_insignia.py`).  No pixels were copied,
traced, sampled, downloaded or AI-generated; no third-party assets, fonts or textures are embedded.

* Licence / rights: project-owned original artwork (generated for this project), freely redistributable with the
  game.  Provenance: deterministic generator (a re-run reproduces every file byte-for-byte, scene.json included;
  checked 2026-11-06), re-run with `py -3 -P tools/pixelgen/env_c4_annex.py [--preview=DIR]`, then the shared
  `--import`.  Machine-readable list: `assets/environments/berlin_annex/provenance.json` (66 files).
* Date: 2026-11-06 (round 9).  Owner: env-annex stream.
* Palette: `annex` of data/chapters/c4.json (night, concrete, steel, fluor, dawn, paper, snow, red, skin) plus the
  proposed ramp **`lamp`** `#4A3016 #83561E #BC862C #E6B44C #FAE3A2` (sodium light at the loop, the lit windows,
  tram 74, the counter lamp -- Berlin's only warm accents; C4_DESIGN 3 lets the env streams refine the placeholder
  ramps).  Every layer, patch and document is palette-pure in it (tests/test_c4_annex_art.gd); scene.json
  `meta.palette_ramps` lists the full palette.
* **Scene A -- Wendeschleife Süd 8** (L_C4_AnnexA, Berlin, 16 Feb 1964, ~5.10, x 0..846): house No. 11, still lived
  in (Marta's window: a lamp left on behind the lace, a plant; the stairwell transom; a coal shop's shutter), house
  No. 9 gutted down to its ground floor -- the boarded double door with the red seal strip and the notice, the
  bricked-up windows, a child's sled -- and above it the exposed wall with three storeys of wallpaper, two rooms each
  (the paler ghosts of a wardrobe, a picture, the kitchen dresser, a mirror; a child's height marks on a door frame;
  a tiled stove still clinging to the wall; the stair's zig-zag), the rubble edge of the cleared lot, the tram
  shelter with the name fascia „WENDESCHLEIFE SÜD 8“ and the lit timetable case (Konrad's light table), the H sign,
  the sodium lamp under the span wire, tram 74 (two-axle motor car, lantern roof, bow collector at the contact wire,
  handwritten route board, warm interior, the open front door, fogged rear window), the lone street tree, the
  advertising column S 2 (posters, an official notice, the warm-air grate at its foot), the freight hatch under a
  hoist with the crates stencilled C-17/45, the split crate and card No. 0417 in the snow, the lorry backed up to it
  (tail lights, engine running), the site hoarding of the axis „BAUSTELLE · BETRETEN VERBOTEN“ with a red blinker;
  the wet setts of the loop with both sides of the track, slush and the lamps mirrored.  Behind: the cleared blocks
  (mid), the axis under construction with tower cranes (far), the Great Hall in the dawn haze (dome), the sky.
* **Scene B -- Nebenstelle Süd** (L_C4_AnnexB, ~6.00, x 846..1920): the cut wall of the shaft (poché with the
  draughtsman's hatch) and the ladder niche with a caged bulkhead lamp and the stencil „S 2“, the machine room
  behind an expanded-metal grille with the two fans the column breathes through, the card hall (steel card cabinets
  to the ceiling, sliding ladders, the drawer bank „HAUSHALTSKARTEI SÜD“ 1-12 with the red tab of Süd 8; Süd 3 stands a finger's width open with
  Brandt's card up — round-9 fix), the
  framed ventilation plan (Blatt 3, three shafts, three blocks hatched, „K.ADLER“), the wall clock at 6.00, the
  pneumatic-tube station „ROHRPOST“ with the capsule in the tray, the waiting bench under „WARTEN BIS ZUM AUFRUF“
  and the call number 17, the counter „AUSKUNFT · ABGLEICH“ under the plate „NEBENSTELLE SÜD“ (stamp carousel,
  stamp pad, forms, the goose-neck lamp -- the one warm light -- and the card perforator), the typists' room behind
  the glazed partition, the steel door „STAATSPOLIZEI“ with its red lamp, a fire extinguisher; air duct, tubes with
  a glass inspection length, cable tray and eight fluorescent fixtures under the slab; linoleum with the tubes'
  sheen.
* Story patches (exact crops of a layer baked with the change; gated in scene.json, applied by
  scripts/levels/c4/annex_level.gd on the registry's gate system): Konrad's tracing sheets on the timetable case
  (after c4b_solve_routes), the poster of S 2 torn back from the steel door (after c4b_inspect_column), drawer
  Süd 8 pulled out with the red C-17 tabs (after c4d_inspect_drawer), the capsule opened (after c4d_inspect_tube),
  the form on the counter (after c4d_talk_registrar).
* Insignia (TECHNICAL_ARCHITECTURE 12.4): `dome.png` (banners on the Great Hall: dark with the white pillar),
  `patches/notice_s2.png` (official notice on the column), `patches/plate_counter.png` and `patches/plate_stapo.png`
  are the neutral defaults with the fictional Reichssiegel; their `*_hist.png` twins carry the red banners and the
  state eagle with the wreath (drawn by env_berlin_insignia.py) as in-world iconography of the regime's offices,
  chosen at runtime by `Symbols.pick()` -- never decoration of the player's side.  The inspect documents carry no
  emblem.
* Round-9 art fixes (same generators, same palette, original and deterministic, no insignia):
  `patches/notice_9.png` (+ `_n`) -- the notice read at door_9: a typed sheet with the round red Bezirksamt stamp
  and the site plan stapled under it, pasted over the planks of the left leaf (ungated decal, scene A; the seal strip
  and the „9“ plate stay visible; painted by `env_c4_annex_loop.Street.notice9`, cfg `notice9`);
  the poster „Berlin baut“ on the shelter's right side wall (12×18 in `loop.png` at x 316–327: red title band, crane,
  dome, sun, three workers in open white shirts, the torn corner, the pencil line on the margin -- the find
  exp_shelter_poster; `Street.shelter_poster`); `props/counter_front.png` (+ `_n`) -- the counter „Auskunft ·
  Abgleich“ and what stands on it, an exact cut of `annex.png` (the pixels `Hall.counter()` paints, y ≥ 228, the form
  patch left open), a y-sorted prop with base_y 292: Fengler (feet y 276) stands behind it, the player in front.
* FX and life (looping strips, every one seamless): snow in two depths (two halves for the texture limit), warm air
  steaming out of the grate of S 2, the lorry's exhaust, chimney smoke of No. 11, the aviation lights of three cranes
  and the hoarding's blinker (1 Hz), Ilse on the last bench of tram 74 (looks out, breathes on the glass, wipes a
  peephole with her red mitten; with its own emission map), the two fans turning behind the grille, dust in their
  draught and under the tubes, a capsule shooting through the glass length of the tube every 6 s, a failing tube
  (drops out twice in 3 s), two typists behind the glass.  Ambient actors reuse existing project scenes and sprites
  by reference only: `KarskCrows` with `assets/environments/karsk_railyard/actors/crows.png` (hooded crows on the
  contact wire that lift when Konrad comes to the hatch) and `KarskBreath` with `.../breath_puff.png` (Marta's
  breath in the frost).
* Inspect documents (`assets/ui/documents/berlin_annex_*.png` + `berlin_annex_documents.json`, shown at 3x): the
  eviction notice of No. 9 with the addendum and the attached Lageplan Süd 8 (the grid and shafts of the route
  puzzle's plan), the steel door of S 2 with its enamel plate, card No. 0417 (German half, perforated edge, red
  C-17 tab), drawer Süd 8 from above (212 cards, 37 red tabs), the Lüftungsplan Blatt 3 signed „GEZ. K. ADLER“,
  the tube slip of the Staatspolizeistelle.  Story-critical words are legible pixel capitals; the rest is print /
  handwriting scribble under the UI caption; every close-up carries an alt text
  (`doc.berlin_annex_*.alt` in `data/locale/de_env_berlin_annex.json`, written by the generator; round-9 fix).  Added in the round-9 fix (compl-04, same generator
  `tools/pixelgen/env_c4_annex_docs.py`, palette `annex`): `berlin_annex_route_board.png` (320×210) — Marta's route
  board, tracing paper clipped to the cab's hardboard: line 74 in pencil with its stops and the turning loop Süd 8, the
  three dashed detours „OKT.“ „DEZ.“ „JAN.“ with hollow diamonds (the geometry of the route puzzle's trace), the depot
  stamp, the north arrow pointing left (drawn in driving direction); alt text `doc.berlin_annex_route_board.alt` in
  `data/locale/de_env_berlin_annex.json`. Original, deterministic, no insignia.
* Level script: `scripts/levels/c4/annex_level.gd` (extends the registry's gated-art script; per-scene filter
  `"scene"` / `"scene_id"`, `camera_zones` so the street never shows underground and the annex never shows the sky,
  looks with the c4.json grades `annex_loop` / `annex`, no porter radio).  Capture harness:
  `scripts/levels/c4/annex_shots.tscn` (fresh level load per scene, `--as-shots`, `--as-done`, `--symbols`).
* Screenshots: documentation/screenshots/c4_annex_contact.png (both scenes, neutral / historical symbols, story
  states), `c4_annex_a_loop_cam0000/0206.png`, `c4_annex_a_states_cam0206.png`, `c4_annex_b_annex_cam0846/1066/1280.png`,
  `c4_annex_b_states_cam1066.png`, `c4_annex_symbols_neutral_vs_hist.png`, `c4_annex_documents.png`.
* Tests: tests/test_c4_annex_art.gd (contract, files / maps / strips, insignia pairs, palette purity, hotspots at
  their objects, foreground frames clear, scene filter + camera zones + looks, story patches, memory, documents).
