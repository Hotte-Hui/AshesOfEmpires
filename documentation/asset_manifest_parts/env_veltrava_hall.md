# Asset manifest part -- env_veltrava_hall (Chapter 3, Palais der Kommission, L_C3_Hall)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_veltrava_hall.py` drives `env_veltrava_hall_room.py`, `_props.py`, `_ext.py`, `_fg.py`, `_fx.py`, `_life.py`,
helpers `env_veltrava_hall_kit.py`, `env_veltrava_hall_layout.py` and the shared, read-only `pg.py`; previews
`env_veltrava_hall_preview.py`).  No pixels were copied, traced, sampled, downloaded or AI-generated; no third-party
assets, fonts or textures are embedded; the bitmap fonts are hand-defined in `env_veltrava_hall_kit.py`.

* Licence / rights: project-owned original artwork (generated for this project), freely redistributable with the
  game.  Provenance: deterministic generator (a re-run reproduces every file byte-for-byte on the same Python/Pillow
  build; the cloud build and this PC produced identical pixels, only the PNG compression bytes differ), re-run with `py -3 -P tools/pixelgen/env_veltrava_hall.py --scene-only` (the hall documents
  in `assets/ui/documents/veltrava_hall_*` are rebuilt only without `--scene-only`; their owner decides).
  Machine-readable list: `assets/environments/veltrava_hall/provenance.json`.
* Dates: 2026-11-05 (cloud build, Compatibility renderer) · 2026-11-06 round 7 (Forward+ pass on this PC: calmer
  marble floor, open archway, entrance transom, raking stair wainscot, the *PAX 1953* allegory and the president's
  medallion, office wall structure (pipe, picture rail, delegations' pigeonholes, session indicator, Saal monitor
  speaker), tufted acoustic wall and three etched transoms in the interpreters' corridor, the agenda board,
  thresholds, the horseshoe table of the Saal readable through the booths, and the ambient life in `life/`).
* Palettes: `palais` (data/chapters/c3.json + one cold near-white) for the interior and the Saal layers, the
  Veltrava town palette for everything seen through the windows.  The life figures use the palais ramps for
  clothes and the cast's four skin tones (as in `assets/characters`) so they sit with the story characters.
* Insignia (TECHNICAL_ARCHITECTURE 12.4): `props/flag_ussr.png`, `props/flag_reich.png` and `saal_far.png` are the
  neutral defaults (fictional gear-and-wheat emblem / fictional Reichssiegel); the `*_hist.png` twins carry the
  historical flags and are chosen at runtime by `Symbols.pick()` -- in-world iconography of the regimes inside the
  critical narrative only.  No life strip shows an insignia (the usher wears the commission's bridge badge).
* Content: the people are working staff and delegates -- nobody heroic, nobody caricatured; the allegory *PAX 1953* is
  the commission's own commissioned picture and is shown as cool and a little empty.

| File | Generator | Content |
|---|---|---|
| `assets/environments/veltrava_hall/ext_river.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | frozen river, the three-arched bridge with a barrier, old-town roofs, dome and spire |
| `assets/environments/veltrava_hall/ext_river_e.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | frozen river, the three-arched bridge with a barrier, old-town roofs, dome and spire -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/ext_sky.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | overcast winter morning sky (seen through every window) |
| `assets/environments/veltrava_hall/ext_square.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | the snowy square in front of the palais: stucco houses, tram stop, lamp post, car |
| `assets/environments/veltrava_hall/ext_square_e.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | the snowy square in front of the palais: stucco houses, tram stop, lamp post, car -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/ext_town.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | far river bank with the Line: double fence, watchtowers, floodlight masts (hazy) |
| `assets/environments/veltrava_hall/fg_frame.png` | `tools/pixelgen/env_veltrava_hall_fg.py` | foreground framing silhouettes (columns, velvet drapes, palm, chair) |
| `assets/environments/veltrava_hall/fx_dust_foyer.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | dust motes in the foyer shafts (16-frame loop) |
| `assets/environments/veltrava_hall/fx_dust_office.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | dust motes in the office window shaft (16-frame loop) |
| `assets/environments/veltrava_hall/fx_dust_vestibule.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | dust motes in the entrance daylight (16-frame loop) |
| `assets/environments/veltrava_hall/fx_glints.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | slow crystal glints on the foyer chandelier (16-frame loop) |
| `assets/environments/veltrava_hall/fx_snow_river.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | snowfall in front of the river view (foyer + office windows, 16-frame loop) |
| `assets/environments/veltrava_hall/fx_snow_square.png` | `tools/pixelgen/env_veltrava_hall_fx.py` | snowfall over the square, seen through the entrance glazing (16-frame loop) |
| `assets/environments/veltrava_hall/life/cleaner.png` | `tools/pixelgen/env_veltrava_hall_life.py` | cleaning woman mopping the melt water in the archway |
| `assets/environments/veltrava_hall/life/cleaner_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | cleaning woman mopping the melt water in the archway -- normal map |
| `assets/environments/veltrava_hall/life/clock_corridor.png` | `tools/pixelgen/env_veltrava_hall_life.py` | second hand of the interpreters' corridor clock |
| `assets/environments/veltrava_hall/life/clock_vestibule.png` | `tools/pixelgen/env_veltrava_hall_life.py` | second hand of the vestibule clock |
| `assets/environments/veltrava_hall/life/door_flash.png` | `tools/pixelgen/env_veltrava_hall_life.py` | press flashes behind the etched glass of the Saal doors |
| `assets/environments/veltrava_hall/life/door_flash_e.png` | `tools/pixelgen/env_veltrava_hall_life.py` | press flashes behind the etched glass of the Saal doors -- emission |
| `assets/environments/veltrava_hall/life/garderobiere.png` | `tools/pixelgen/env_veltrava_hall_life.py` | cloakroom attendant behind the counter (sorts tokens, looks up) |
| `assets/environments/veltrava_hall/life/garderobiere_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | cloakroom attendant behind the counter (sorts tokens, looks up) -- normal map |
| `assets/environments/veltrava_hall/life/interp_1.png` | `tools/pixelgen/env_veltrava_hall_life.py` | interpreter at work in booth 1 (FR), seen from behind |
| `assets/environments/veltrava_hall/life/interp_1_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | interpreter at work in booth 1 (FR), seen from behind -- normal map |
| `assets/environments/veltrava_hall/life/interp_3.png` | `tools/pixelgen/env_veltrava_hall_life.py` | interpreter at work in booth 3 (EN), seen from behind |
| `assets/environments/veltrava_hall/life/interp_3_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | interpreter at work in booth 3 (EN), seen from behind -- normal map |
| `assets/environments/veltrava_hall/life/landing_pair.png` | `tools/pixelgen/env_veltrava_hall_life.py` | two delegates talking at the gallery door, the usher beside it (stair landing) |
| `assets/environments/veltrava_hall/life/landing_pair_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | two delegates talking at the gallery door, the usher beside it (stair landing) -- normal map |
| `assets/environments/veltrava_hall/life/pigeon.png` | `tools/pixelgen/env_veltrava_hall_life.py` | a pigeon on the outer sill of the office window (behind the glass) |
| `assets/environments/veltrava_hall/life/saal_life.png` | `tools/pixelgen/env_veltrava_hall_life.py` | the session through the booth windows: speaker, nods, an usher with a note |
| `assets/environments/veltrava_hall/life/waiter.png` | `tools/pixelgen/env_veltrava_hall_life.py` | waiter at the untouched buffet |
| `assets/environments/veltrava_hall/life/waiter_n.png` | `tools/pixelgen/env_veltrava_hall_life.py` | waiter at the untouched buffet -- normal map |
| `assets/environments/veltrava_hall/props/buffet.png` | `tools/pixelgen/env_veltrava_hall_props.py` | buffet: untouched Sekt and caviar on crushed ice |
| `assets/environments/veltrava_hall/props/buffet_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | buffet: untouched Sekt and caviar on crushed ice -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/carbon_basket.png` | `tools/pixelgen/env_veltrava_hall_props.py` | wire basket of carbon copies on an oak cabinet (booth_log) |
| `assets/environments/veltrava_hall/props/carbon_basket_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | wire basket of carbon copies on an oak cabinet (booth_log) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/cloak_counter.png` | `tools/pixelgen/env_veltrava_hall_props.py` | cloakroom counter: bell, numbered tokens, lamp |
| `assets/environments/veltrava_hall/props/cloak_counter_e.png` | `tools/pixelgen/env_veltrava_hall_props.py` | cloakroom counter: bell, numbered tokens, lamp -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/props/cloak_counter_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | cloakroom counter: bell, numbered tokens, lamp -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/easel_seating.png` | `tools/pixelgen/env_veltrava_hall_props.py` | seating-plan easel (horseshoe, mics 1/2/12) |
| `assets/environments/veltrava_hall/props/easel_seating_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | seating-plan easel (horseshoe, mics 1/2/12) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_commission.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: commission |
| `assets/environments/veltrava_hall/props/flag_commission_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: commission -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_finland.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: finland |
| `assets/environments/veltrava_hall/props/flag_finland_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: finland -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_reich.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: reich (neutral default; *_hist = historical flag) |
| `assets/environments/veltrava_hall/props/flag_reich_hist.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: reich -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_hall/props/flag_reich_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: reich (neutral default; *_hist = historical flag) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_sweden.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: sweden |
| `assets/environments/veltrava_hall/props/flag_sweden_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: sweden -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_switzerland.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: switzerland |
| `assets/environments/veltrava_hall/props/flag_switzerland_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: switzerland -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/flag_ussr.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: ussr (neutral default; *_hist = historical flag) |
| `assets/environments/veltrava_hall/props/flag_ussr_hist.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: ussr -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_hall/props/flag_ussr_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | flag on a brass pole: ussr (neutral default; *_hist = historical flag) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/mimeograph.png` | `tools/pixelgen/env_veltrava_hall_props.py` | stencil duplicator (mimeograph) on its stand, fresh copies |
| `assets/environments/veltrava_hall/props/mimeograph_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | stencil duplicator (mimeograph) on its stand, fresh copies -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/palm_corridor.png` | `tools/pixelgen/env_veltrava_hall_props.py` | Kentia palm in a Jugendstil jardiniere |
| `assets/environments/veltrava_hall/props/palm_corridor_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | Kentia palm in a Jugendstil jardiniere -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/palm_vest.png` | `tools/pixelgen/env_veltrava_hall_props.py` | Kentia palm in a Jugendstil jardiniere |
| `assets/environments/veltrava_hall/props/palm_vest_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | Kentia palm in a Jugendstil jardiniere -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/protocol_table.png` | `tools/pixelgen/env_veltrava_hall_props.py` | the big table of the Protokollbuero (protocol_table) |
| `assets/environments/veltrava_hall/props/protocol_table_e.png` | `tools/pixelgen/env_veltrava_hall_props.py` | the big table of the Protokollbuero (protocol_table) -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/props/protocol_table_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | the big table of the Protokollbuero (protocol_table) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/saal_rope.png` | `tools/pixelgen/env_veltrava_hall_props.py` | brass stanchions with a velvet rope before the Saal doors |
| `assets/environments/veltrava_hall/props/saal_rope_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | brass stanchions with a velvet rope before the Saal doors -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/props/typist_desk.png` | `tools/pixelgen/env_veltrava_hall_props.py` | typist desk: typewriter, carbon box, lamp, telephone |
| `assets/environments/veltrava_hall/props/typist_desk_e.png` | `tools/pixelgen/env_veltrava_hall_props.py` | typist desk: typewriter, carbon box, lamp, telephone -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/props/typist_desk_n.png` | `tools/pixelgen/env_veltrava_hall_props.py` | typist desk: typewriter, carbon box, lamp, telephone -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/room.png` | `tools/pixelgen/env_veltrava_hall_room.py` | palais interior: vestibule, foyer + staircase, Protokollbuero, interpreters' corridor |
| `assets/environments/veltrava_hall/room_e.png` | `tools/pixelgen/env_veltrava_hall_room.py` | palais interior: vestibule, foyer + staircase, Protokollbuero, interpreters' corridor -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/room_n.png` | `tools/pixelgen/env_veltrava_hall_room.py` | palais interior: vestibule, foyer + staircase, Protokollbuero, interpreters' corridor -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_hall/saal_far.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | Grosser Saal head wall: windows, panelling, dais with six small flags, chandeliers |
| `assets/environments/veltrava_hall/saal_far_e.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | Grosser Saal head wall: windows, panelling, dais with six small flags, chandeliers -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/saal_far_hist.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | same as saal_far with the historical USSR / Reich flags (Symbols.pick variant) |
| `assets/environments/veltrava_hall/saal_far_hist_e.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | same as saal_far with the historical USSR / Reich flags (Symbols.pick variant) -- emission mask (unshaded glow) |
| `assets/environments/veltrava_hall/saal_near.png` | `tools/pixelgen/env_veltrava_hall_ext.py` | the horseshoe table seen from the booths: presidium, delegates, secretariat table |
| `assets/environments/veltrava_hall/scene.json` | `tools/pixelgen/env_veltrava_hall.py` | art manifest (TECHNICAL_ARCHITECTURE 3.1) |
| `assets/environments/veltrava_hall/shafts.png` | `tools/pixelgen/env_veltrava_hall.py` | volumetric daylight-shaft veil (soft alpha, plain alpha blending) |
