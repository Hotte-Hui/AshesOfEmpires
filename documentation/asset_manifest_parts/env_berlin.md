# Asset manifest part -- env_berlin (M1 Berliner Bauarchiv, plan documents, X1 stills)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_berlin.py` drives `env_berlin_room.py`, `env_berlin_ext.py`, `env_berlin_props.py`,
`env_berlin_fg.py`, `env_berlin_docs.py`, `env_berlin_stills.py`, helpers `env_berlin_kit.py`,
`env_berlin_layout.py` and the shared `pg.py`).  No pixels were copied, traced or sampled from the
reference images in `documentation/references/` (style study only).  No third-party assets, fonts
or textures are embedded; the tiny bitmap fonts are hand-defined in `env_berlin_kit.py`.

* Licence / rights: project-owned original artwork (generated for this project), freely
  redistributable with the game.  Provenance: deterministic generator, re-run with
  `py -3 -P tools/pixelgen/env_berlin.py`.
* Date: 2026-11-04.  Palettes: `archive` (+ local `green`, `graphite` ramps), `berlin`, `sepia`, `karsk`.
* Insignia policy: only the fictional **Reichssiegel** (white pillar in a black disc) appears; no
  swastika, eagle or SS rune anywhere.  The Great Hall is fictional and shown muted, not heroic.
* Locale `data/locale/de_env_berlin.json` is hand-written original German text (Konrad's voice).

| File | Generator | Content |
|---|---|---|
| `assets/environments/berlin_archive/ext_far.png` | `tools/pixelgen/env_berlin_ext.py` | far city, smoke and the fictional Great Hall dome (muted, hazy) |
| `assets/environments/berlin_archive/ext_far_e.png` | `tools/pixelgen/env_berlin_ext.py` | far city, smoke and the fictional Great Hall dome (muted, hazy) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/ext_near.png` | `tools/pixelgen/env_berlin_ext.py` | Gruenderzeit tenements across the street, tram wires |
| `assets/environments/berlin_archive/ext_near_e.png` | `tools/pixelgen/env_berlin_ext.py` | Gruenderzeit tenements across the street, tram wires -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/ext_sky.png` | `tools/pixelgen/env_berlin_ext.py` | Berlin winter dusk sky (seen through windows) |
| `assets/environments/berlin_archive/fg_frame.png` | `tools/pixelgen/env_berlin_fg.py` | foreground framing silhouettes (columns, rubber plant, desk, chair) |
| `assets/environments/berlin_archive/fx_dust_archive.png` | `tools/pixelgen/env_berlin_fx.py` | warm dust motes under the archive pendant (16-frame loop) |
| `assets/environments/berlin_archive/fx_dust_office.png` | `tools/pixelgen/env_berlin_fx.py` | dust motes hovering in the window shafts (16-frame loop) |
| `assets/environments/berlin_archive/fx_window_snow.png` | `tools/pixelgen/env_berlin_fx.py` | snowfall seen through the windows (16-frame loop, behind the room layer) |
| `assets/environments/berlin_archive/props/bench.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench; a forgotten hat and a newspaper |
| `assets/environments/berlin_archive/props/bench_n.png` | `tools/pixelgen/env_berlin_props.py` | waiting bench; a forgotten hat and a newspaper -- normal map (OpenGL +Y up) |
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
| `assets/environments/berlin_archive/props/ladder.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the shelf rail |
| `assets/environments/berlin_archive/props/ladder_n.png` | `tools/pixelgen/env_berlin_props.py` | rolling library ladder hooked on the shelf rail -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/light_table.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) |
| `assets/environments/berlin_archive/props/light_table_e.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/light_table_n.png` | `tools/pixelgen/env_berlin_props.py` | light table for overlaying drawings (overlay_table) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/plan_basket.png` | `tools/pixelgen/env_berlin_props.py` | wicker stand with rolled plans (in front of the walk line) |
| `assets/environments/berlin_archive/props/plan_basket_n.png` | `tools/pixelgen/env_berlin_props.py` | wicker stand with rolled plans (in front of the walk line) -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/stool_konrad.png` | `tools/pixelgen/env_berlin_props.py` | tall drafting stool pushed aside |
| `assets/environments/berlin_archive/props/stool_konrad_n.png` | `tools/pixelgen/env_berlin_props.py` | tall drafting stool pushed aside -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/props/typist_desk.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair |
| `assets/environments/berlin_archive/props/typist_desk_e.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/props/typist_desk_n.png` | `tools/pixelgen/env_berlin_props.py` | typist desk: typewriter, telephone, gooseneck lamp, chair -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/room.png` | `tools/pixelgen/env_berlin_room.py` | archive interior: office, archive hall, light-table room, issue counter |
| `assets/environments/berlin_archive/room_e.png` | `tools/pixelgen/env_berlin_room.py` | archive interior: office, archive hall, light-table room, issue counter -- emission mask (unshaded glow) |
| `assets/environments/berlin_archive/room_n.png` | `tools/pixelgen/env_berlin_room.py` | archive interior: office, archive hall, light-table room, issue counter -- normal map (OpenGL +Y up) |
| `assets/environments/berlin_archive/scene.json` | `tools/pixelgen/env_berlin.py` | art manifest (TECHNICAL_ARCHITECTURE 3.1) |
| `assets/environments/berlin_archive/shafts.png` | `tools/pixelgen/env_berlin.py` | volumetric daylight-shaft veil (soft alpha, additive blend hint) |
| `assets/ui/documents/berlin_emil_note.png` | `tools/pixelgen/env_berlin_docs.py` | Emil's handwritten archive slip (Serie C-17) |
| `assets/ui/documents/berlin_plan_a.png` | `tools/pixelgen/env_berlin_docs.py` | approved public floor plan (supply wing closed), 18x12 cells |
| `assets/ui/documents/berlin_plan_a_lines.png` | `tools/pixelgen/env_berlin_docs.py` | approved public floor plan (supply wing closed), 18x12 cells -- lines only on transparent (overlay UI) |
| `assets/ui/documents/berlin_plan_b.png` | `tools/pixelgen/env_berlin_docs.py` | archived 1958 draft: corridor behind a second wall, pencil C-17 |
| `assets/ui/documents/berlin_plan_b_lines.png` | `tools/pixelgen/env_berlin_docs.py` | archived 1958 draft: corridor behind a second wall, pencil C-17 -- lines only on transparent (overlay UI) |
| `assets/ui/documents/berlin_plans.json` | `tools/pixelgen/env_berlin_docs.py` | overlay puzzle data: cells, landmarks, solution (+2,-1,rot 0), hidden corridor rects |
| `assets/ui/documents/x1_alexei_desk.png` | `tools/pixelgen/env_berlin_stills.py` | X1: Alexei files the document in Karsk (copper lamp) (640x360) |
| `assets/ui/documents/x1_blueprint_closeup.png` | `tools/pixelgen/env_berlin_stills.py` | A1->M1 match cut 2/2: pencil C-17 on a Berlin plan, same position/size as the stamp (640x360) |
| `assets/ui/documents/x1_border_map.png` | `tools/pixelgen/env_berlin_stills.py` | X1: neutral schematic of a fictional border corridor, C-17 route in red (640x360) |
| `assets/ui/documents/x1_konrad_desk.png` | `tools/pixelgen/env_berlin_stills.py` | X1: Konrad folds the matching memorandum in Berlin (640x360) |
| `assets/ui/documents/x1_stamp_closeup.png` | `tools/pixelgen/env_berlin_stills.py` | A1->M1 match cut 1/2: red C-17 stamp on the Karsk ledger (sepia) (640x360) |
| `data/locale/de_env_berlin.json` | hand-written | observation prompts/texts (obs_window, obs_notice, obs_photo) |
