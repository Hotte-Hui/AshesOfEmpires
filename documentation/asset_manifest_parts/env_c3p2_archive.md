# Asset manifest part -- env_c3p2_archive (Chapter 3 part 2, the commission's registry, L_C3_Registry)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_c3p2_archive.py` drives `env_c3p2_archive_room.py`, `_props.py`, `_fx.py`, helpers `env_c3p2_archive_kit.py`,
`env_c3p2_archive_layout.py`, the shared read-only `pg.py` and -- read-only -- the tone-space painter, light bake and
bitmap fonts of `env_veltrava_hall_kit.py`).  No pixels were copied, traced, sampled, downloaded or AI-generated; no
third-party assets, fonts or textures are embedded.

* Licence / rights: project-owned original artwork (generated for this project), freely redistributable with the
  game.  Provenance: deterministic generator (a re-run reproduces every file byte-for-byte; checked 2026-11-06),
  re-run with `py -3 -P tools/pixelgen/env_c3p2_archive.py [--preview=DIR]`.  Machine-readable list:
  `assets/environments/veltrava_registry/provenance.json`.
* Date: 2026-11-06 (round 8).  Owner: registry art stream.
* Palette: `registry` of data/chapters/c3.json (night, slate, oak, lamp green, paper, brass, snow, fire, red, skin),
  checked at build time; every room look is palette-pure (tests/test_c3p2_archive_art.gd).
* The level (C3P2_DESIGN 5.1, side view 1920 x 360, feet y 300): the snowy Wirtschaftshof (gate with the
  trilingual delivery sign, the east-wing facade with one lit window, bracket lamp, the handcart with the emptied
  crates of wagon 4, the cast hatch "1909", ramp and the iron-clad ramp door), the Annahme (chute door "1909",
  oak standing desk with the intake book and the day's card box, red fire case with hose and axe, electric fire
  bell, the glazed porter's booth with key board, the 1909 Kurhaus plan, Bakelite radio, thermos and night book),
  the Karteisaal (bucket stand, Rohrpost receiver, rows of card cabinets with a rolling ladder, sorting table under
  the green lamp, stamp board, the card bank with drawer C-17 and Elena's wine-red scarf on the chair), the
  Planarchiv (office-green walls, the wall of framed Annex C sheets with Blatt 7 askew, plan chests "KORDON-17",
  drafting table) and the Magazin (bare brick, the enamel plate of the Kurhaus boiler house, mobile shelving with
  the C-17 unit, the cassation list, delegation shelves, the barred service-stair door with a steel fire door).
  A 1964 cellar without sprinklers: fire case, buckets, extinguisher, fire bell.
* Looks (one opaque room layer each, gated in scene.json, applied by scripts/levels/c3p2_archive/registry_level.gd):
  A night with Konrad's torch (until c3c_talk_konrad) - B the green lamp on - C smoke under the vaults, the Magazin
  and Planarchiv burning, the ramp door shut (after c3d_choose) - D the fire in the Karteisaal (after
  c3e_reach_konrad, cross-fades live).  Story patches: seal wire taken, scarf taken, halves on the table, the file
  taken, Blatt 7 pocketed (choice c3d_choose = pocket_plan), fire case smashed with the cut hose, desk pushed off
  the chute door.  FX: yard snow, snow through the door gaps, dust in the lamp light, flames (binary alpha +
  emission), embers and ash (no brightness flicker; ember fades are slower than 3 Hz), smoke veils, rolling smoke,
  plumes, heat shimmer, the ringing fire bell; life: a guard's boots passing a high window like a pendulum.
* Insignia (TECHNICAL_ARCHITECTURE 12.4): `props/cart.png` / `props/cart_open.png` (railway stencil on the crates:
  neutral winged wheel + "МПС") and `patches/insignia_magazin_*.png` (delegation plates: fictional gear-and-wheat
  emblem / fictional Reichssiegel) are the neutral defaults; their `*_hist.png` twins carry the hammer and sickle
  and the hooked cross as small in-world stamps of the two delegations, chosen at runtime by `Symbols.pick()` --
  iconography of the regimes inside the critical narrative only, never decoration.
* Screenshots: documentation/screenshots/c3p2_archive_*.png (contact sheets for both protagonists and both symbol
  settings, the live C -> D cross-fade, the insignia comparison, seven full-size views).

| File | Generator | Content |
|---|---|---|
| `assets/environments/veltrava_registry/fg_frame.png` | `tools/pixelgen/env_c3p2_archive_props.py` | foreground silhouettes (bollard, cast-iron columns, boxes, cables), parallax 1.25 |
| `assets/environments/veltrava_registry/fx/ash_c0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling ash (look c) |
| `assets/environments/veltrava_registry/fx/ash_c1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling ash (look c) |
| `assets/environments/veltrava_registry/fx/ash_c2.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling ash (look c) |
| `assets/environments/veltrava_registry/fx/ash_d0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling ash (look d) |
| `assets/environments/veltrava_registry/fx/ash_d1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling ash (look d) |
| `assets/environments/veltrava_registry/fx/bell_ringing.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | fire bell ringing: the striker against the dome (4 frames, small motion, no flashing) |
| `assets/environments/veltrava_registry/fx/dust_lamp.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | dust motes in the light of the green lamp |
| `assets/environments/veltrava_registry/fx/embers_c0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | rising embers (look c) |
| `assets/environments/veltrava_registry/fx/embers_c1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | rising embers (look c) |
| `assets/environments/veltrava_registry/fx/embers_d0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | rising embers (look d) |
| `assets/environments/veltrava_registry/fx/embers_d1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | rising embers (look d) |
| `assets/environments/veltrava_registry/fx/flames_bank.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_bank), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_bank_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_bank) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_c17.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_c17), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_c17_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_c17) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_chests.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_chests), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_chests_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_chests) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_door.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_door), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_door_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_door) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_fallen.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_fallen), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_fallen_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_fallen) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_frame_a.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_a), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_frame_a_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_a) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_frame_b.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_b), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_frame_b_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_b) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_frame_c.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_c), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_frame_c_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_frame_c) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_front_c.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_front_c), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_front_c_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_front_c) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_front_d.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_front_d), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_front_d_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_front_d) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_rows.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_rows), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_rows_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_rows) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_shelves.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_shelves), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_shelves_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_shelves) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_table.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_table), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_table_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_table) -- emission strip |
| `assets/environments/veltrava_registry/fx/flames_units.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_units), 16 frames |
| `assets/environments/veltrava_registry/fx/flames_units_e.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | flames (flames_units) -- emission strip |
| `assets/environments/veltrava_registry/fx/heat_c.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | heat shimmer above the fire front |
| `assets/environments/veltrava_registry/fx/heat_d.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | heat shimmer above the fire front |
| `assets/environments/veltrava_registry/fx/plume_door.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke squeezing out above the ramp door |
| `assets/environments/veltrava_registry/fx/plume_front_c.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rising from the fire front (C) |
| `assets/environments/veltrava_registry/fx/plume_front_d.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rising from the fire front (D) |
| `assets/environments/veltrava_registry/fx/plume_service.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke pouring from the service stairs |
| `assets/environments/veltrava_registry/fx/roll_c0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rolling along under the vaults toward the Annahme |
| `assets/environments/veltrava_registry/fx/roll_c1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rolling along under the vaults toward the Annahme |
| `assets/environments/veltrava_registry/fx/roll_c2.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rolling along under the vaults toward the Annahme |
| `assets/environments/veltrava_registry/fx/roll_d0.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rolling along under the vaults toward the Annahme |
| `assets/environments/veltrava_registry/fx/roll_d1.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke rolling along under the vaults toward the Annahme |
| `assets/environments/veltrava_registry/fx/snow_gap.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | snow blowing through the gaps of the shut ramp door |
| `assets/environments/veltrava_registry/fx/snow_yard.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | falling snow over the yard (24 frames, 8 fps) |
| `assets/environments/veltrava_registry/life/guard_feet.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | a guard's boots passing the high window of the Karteisaal, turning, passing back (80 frames, 8 fps) |
| `assets/environments/veltrava_registry/outside.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | light wells behind the high windows: snow heap, grating shadow, street-lamp glow (unlit) |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_c.png` | `tools/pixelgen/env_c3p2_archive.py` | look c with the story change "blatt7_pocketed" |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_c_e.png` | `tools/pixelgen/env_c3p2_archive.py` | look c with the story change "blatt7_pocketed" -- emission mask |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_c_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look c with the story change "blatt7_pocketed" -- normal map |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_d.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "blatt7_pocketed" |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_d_e.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "blatt7_pocketed" -- emission mask |
| `assets/environments/veltrava_registry/patches/blatt7_pocketed_d_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "blatt7_pocketed" -- normal map |
| `assets/environments/veltrava_registry/patches/case_broken_d.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "case_broken" |
| `assets/environments/veltrava_registry/patches/case_broken_d_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "case_broken" -- normal map |
| `assets/environments/veltrava_registry/patches/desk_pushed_d.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "desk_pushed" |
| `assets/environments/veltrava_registry/patches/desk_pushed_d_e.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "desk_pushed" -- emission mask |
| `assets/environments/veltrava_registry/patches/desk_pushed_d_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look d with the story change "desk_pushed" -- normal map |
| `assets/environments/veltrava_registry/patches/file_taken_c.png` | `tools/pixelgen/env_c3p2_archive.py` | look c with the story change "file_taken" |
| `assets/environments/veltrava_registry/patches/file_taken_c_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look c with the story change "file_taken" -- normal map |
| `assets/environments/veltrava_registry/patches/halves_b.png` | `tools/pixelgen/env_c3p2_archive.py` | look b with the story change "halves" |
| `assets/environments/veltrava_registry/patches/halves_b_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look b with the story change "halves" -- normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_a.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look a), neutral emblems |
| `assets/environments/veltrava_registry/patches/insignia_magazin_a_hist.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look a), neutral emblems -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/patches/insignia_magazin_a_hist_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look a), neutral emblems -- historical, normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_a_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look a), neutral emblems -- normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_b.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look b), neutral emblems |
| `assets/environments/veltrava_registry/patches/insignia_magazin_b_hist.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look b), neutral emblems -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/patches/insignia_magazin_b_hist_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look b), neutral emblems -- historical, normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_b_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look b), neutral emblems -- normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c_e.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems -- emission mask |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c_hist.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c_hist_e.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems -- historical, emission |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c_hist_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems -- historical, normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_c_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look c), neutral emblems -- normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d_e.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems -- emission mask |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d_hist.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d_hist_e.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems -- historical, emission |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d_hist_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems -- historical, normal map |
| `assets/environments/veltrava_registry/patches/insignia_magazin_d_n.png` | `tools/pixelgen/env_c3p2_archive.py` | Magazin delegation plates (look d), neutral emblems -- normal map |
| `assets/environments/veltrava_registry/patches/scarf_taken_b.png` | `tools/pixelgen/env_c3p2_archive.py` | look b with the story change "scarf_taken" |
| `assets/environments/veltrava_registry/patches/scarf_taken_b_n.png` | `tools/pixelgen/env_c3p2_archive.py` | look b with the story change "scarf_taken" -- normal map |
| `assets/environments/veltrava_registry/props/cart.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire dangling, red C-17 tag) |
| `assets/environments/veltrava_registry/props/cart_hist.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire dangling, red C-17 tag) -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/props/cart_hist_n.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire dangling, red C-17 tag) -- historical, normal map |
| `assets/environments/veltrava_registry/props/cart_n.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire dangling, red C-17 tag) -- normal map |
| `assets/environments/veltrava_registry/props/cart_open.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire taken, red C-17 tag) |
| `assets/environments/veltrava_registry/props/cart_open_hist.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire taken, red C-17 tag) -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4) |
| `assets/environments/veltrava_registry/props/cart_open_hist_n.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire taken, red C-17 tag) -- historical, normal map |
| `assets/environments/veltrava_registry/props/cart_open_n.png` | `tools/pixelgen/env_c3p2_archive_props.py` | handcart with the emptied crates of courier wagon 4 (seal wire taken, red C-17 tag) -- normal map |
| `assets/environments/veltrava_registry/room.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night: yard in the snow, Annahme, Karteisaal under the green lamp, Planarchiv, Magazin |
| `assets/environments/veltrava_registry/room_a.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night, before the green lamp is switched on (Konrad's torch in the aisle) |
| `assets/environments/veltrava_registry/room_a_e.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night, before the green lamp is switched on (Konrad's torch in the aisle) -- emission mask (unshaded glow) |
| `assets/environments/veltrava_registry/room_a_n.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night, before the green lamp is switched on (Konrad's torch in the aisle) -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_registry/room_e.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night: yard in the snow, Annahme, Karteisaal under the green lamp, Planarchiv, Magazin -- emission mask (unshaded glow) |
| `assets/environments/veltrava_registry/room_fire_c.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (C): smoke under the vaults, the Magazin and Planarchiv burning, ramp door shut |
| `assets/environments/veltrava_registry/room_fire_c_e.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (C): smoke under the vaults, the Magazin and Planarchiv burning, ramp door shut -- emission mask (unshaded glow) |
| `assets/environments/veltrava_registry/room_fire_c_n.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (C): smoke under the vaults, the Magazin and Planarchiv burning, ramp door shut -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_registry/room_fire_d.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (D): the fire in the Karteisaal, smoke low, ramp door shut |
| `assets/environments/veltrava_registry/room_fire_d_e.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (D): the fire in the Karteisaal, smoke low, ramp door shut -- emission mask (unshaded glow) |
| `assets/environments/veltrava_registry/room_fire_d_n.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry on fire (D): the fire in the Karteisaal, smoke low, ramp door shut -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_registry/room_n.png` | `tools/pixelgen/env_c3p2_archive_room.py` | registry at night: yard in the snow, Annahme, Karteisaal under the green lamp, Planarchiv, Magazin -- normal map (OpenGL +Y up) |
| `assets/environments/veltrava_registry/scene.json` | `tools/pixelgen/env_c3p2_archive.py` | art manifest (TECHNICAL_ARCHITECTURE 3.1 + the registry gates) |
| `assets/environments/veltrava_registry/shafts.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | cold light falling from the high windows (soft veil, plain alpha) |
| `assets/environments/veltrava_registry/smoke_c.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke under the vaults (smoke_c): sooty grey, lit orange from below near the fire |
| `assets/environments/veltrava_registry/smoke_d.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | smoke under the vaults (smoke_d): sooty grey, lit orange from below near the fire |
| `assets/environments/veltrava_registry/torch_beam.png` | `tools/pixelgen/env_c3p2_archive_fx.py` | Konrad's torch: soft cone of light into the aisle (look A, plain alpha) |
