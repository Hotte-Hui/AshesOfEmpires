# Asset manifest part — c4_cine (Chapter-4 cinematics LS_C4_Homeward, _Number, _Card, _Stamp, _Voices)

* **Date:** 2026-11-06 (round 9; places-and-motion polish pass the same evening)
* **Area owner:** cine stream (C4_DESIGN.md §2.9, §10)
* **Scenes / code:** `scenes/cinematics/ch4_homeward/` (`Ch4Homeward.tscn`, `ch4_homeward.gd`), `ch4_number/`,
  `ch4_card/`, `ch4_stamp/`, `ch4_voices/`, shared `scenes/cinematics/c4_common/c4_cinematic.gd` (extends the C3P2
  base `c3p2_common/c3p2_cinematic.gd` and through it the §12.5 contract of `ch3_common/c3_cinematic.gd`: textures from
  `assets/cinematics/c4/`, `line_dur()` keeps every subtitle under 19 characters per second, the game's character
  sheets drawn by named frame ranges, the in-game stride so feet never slide, `optional_music()`; the polish pass only
  ADDED helpers: `loop_frame()` / `fx_sprite()` for the levels' fx strips, `draw_puffs()`, `draw_motes()`,
  `draw_drips()`, `draw_lit_snow()`, `par_pos()` for parallax stacks, `h01()`). Registered in `data/chapters/c4.json`
  → `cinematics`, played by `ChapterExt.play_cinematic()`. Lengths = the registered shot sheets of
  `data/v3/cinematics.json`: 14 / 13 / 11 / 11 / 24 s (unchanged).
* **Match cuts (hard cuts on shared objects, the cities in their own palettes):** the stencilled 45 of wagon C-17/45
  (cream on red-brown in Karsk → black on pine in Berlin, same shapes at the same place: one stencil generator, one
  layout entry `number.macro`); the torn perforation of card No. 0417 (German half, paper left of the edge → Russian
  half, paper right of it: one perforation geometry, mirrored); the rubber stamp (ПРИНЯТЬ violet → ABGANG red, same
  frame at the same contact point; each landing now jolts the frame by 2 px, the impressions stay put).
* **Generators:** `py -3 -P tools/pixelgen/env_c4_cine.py [--only places,homeward,number,card,stamp,voices]` writes
  every texture and `assets/cinematics/c4/layout.json` (anchors shared with the runtimes; `tests/test_c4_cinematics.gd`
  checks them). Modules: `env_c4_cine_kit.py` (palettes, stencil letters, perforation, stamps, re-lighting of the game
  sheets with their normal maps), `env_c4_cine_places.py` (build of the shared places; the round-9 painters stay for
  reference), place modules of the polish pass: `env_c4_cine_levelart.py` (reads the levels' layers and normal /
  emission maps and re-lights them like the runtime's point lights; re-bakes the street of `env_c4_annex_loop` without
  its tram), `env_c4_cine_levelplates.py` (the tram loop Süd 8 as parallax layers for dawn / morning, the level's fx
  strips, tram 3518 in both directions, the siding hall of L_C4_TunnelsB lit / dark, the booth-window view, the annex
  card hall), `env_c4_cine_yard.py` (the Karsk freight yard in parallax layers: sky, the railyard level's skyline
  re-lit for the night with the cooling towers, the far sidings, the near yard and the freight office, parapet,
  glows), `env_c4_cine_station.py` (Veltrava platform 5, ray-cast so the 56 px figures stand at their true size);
  `env_c4_cine_{homeward,number,card,stamp,voices}.py`, `env_c4_cine_figs.py` (hands and close figures; the figures
  stream). Sound: `py -3 -P tools/audiogen/c4_cine_audio.py` → `assets/audio/sfx/c4cine_*.wav` (21 files; the
  picture-synced times are constants checked by the test).
* **Figures:** close-ups (Konrad's gloves on the card, Alexei's hand on the desk, the pencil hand, Lev's hand, both
  stamp hands, Fengler at the counter, Alexei over the shoulder, Konrad from behind waving) come from the figures
  stream's `env_c4_cine_figs.py`. Every person in the wide shots is a game sheet re-lit per shot
  (`assets/characters/<id>/sheet.png` + `sheet_n.png`, 32 x 56 cells, `env_c4_cine_kit.fig_sheet`): Konrad, Alexei, Lev,
  Marta (in the tram's cab) and the platform's and the loop's people (conductor, porter, worker_a / worker_b,
  berlin_mother, berlin_child, babushka); Ilse at the tram's last window and the annex typists are the levels' own life
  strips. A character without a delivered sheet would be drawn from a declared stand-in and listed in `layout.json` →
  `standins` (currently empty).
* **Determinism:** fixed seeds everywhere; no time or global random state (level layers are read, never written).
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio made for ASHES OF
  EMPIRES: THE LAST WINTER by these generators (AI-authored code, project-owned, same licence as the game). No
  downloaded, copied or traced images, fonts or samples. Image inputs are only the project's own art: the character
  sheets and the level layers / fx strips of `assets/environments/{berlin_annex,karsk_tunnels,karsk_railyard}` (neutral
  variants only). No insignia anywhere in these films (stamps, signs, the cap badge „74“ and the forms are plain text;
  the column's notice carries the level's neutral seal), so there are no `_hist` variants and the films look the same
  with symbols on or off.
* **Texts:** memory film titles `ui.memories.film.LS_C4_*` / `film_sub.*` in `data/locale/de_c4_cine.json` (this
  stream); the films' subtitles are the story stream's `data/locale/de_c4_cinematics.json`. No disclaimers in the films.

| path | what |
|---|---|
| `assets/cinematics/c4/layout.json` | anchors for the five runtimes (sections places, homeward, number, card, stamp, voices, standins) |
| `assets/cinematics/c4/places/yard_l_{sky,far,mid,main,parapet,green,warm}.png` | the Karsk yard before dawn in parallax layers (Homeward w3 tracks Alexei across them; Voices v3 at rest): low snow clouds, the skyline with lit windows and blinking red lamps (runtime), the cooling towers and their plumes, the rake of wagons, the water tower and gantry, the repaired signal, the freight office with its lit window, gutter, sign, door, the stair down to the cellar and the lit cellar window |
| `assets/cinematics/c4/places/yard.png`, `yard_parapet.png`, `yard_green.png`, `yard_warm.png` | the same yard composited at camera 0 (legacy single plates) |
| `assets/cinematics/c4/places/loop_{dawn,morning}_{sky,dome,far,mid,street,fg,glow}.png` | the tram loop Süd 8 from L_C4_AnnexA's own layers, re-baked without the tram for dawn (Number n4) and morning with the poster of S 2 torn back (Voices v1/v2); `glow` = the street lights' pools |
| `assets/cinematics/c4/places/loop_dawn.png`, `loop_morning.png`, `loop_glow_*.png` | the loop composited at camera 0 (legacy) |
| `assets/cinematics/c4/places/fx_{steam_s2,chimney_11,crane_light_0..2,exhaust,fence_blinker,crows}.png` | the levels' fx strips (column steam, chimney, crane lamps, exhaust, hoarding blinker, crows) |
| `assets/cinematics/c4/places/tram_left.png`, `tram_right.png` | tram 74 No. 3518 as the level paints it: arriving (front left, Marta in the cab, Ilse at the last window); leaving (front right, line board and fleet number unmirrored; Ilse without / with her red mitten on the glass) |
| `assets/cinematics/c4/places/siding_lit.png`, `siding_dark.png`, `siding_glow.png` | the siding hall of L_C4_TunnelsB around wagon C-17/45, lit by its single work lamp / lamp out (the dawn at the portal, the booth's kerosene) |
| `assets/cinematics/c4/places/breath.png`, `steam.png`, `steam_light.png`, `steam_warm.png`, `smoke.png`, `smoke_light.png`, `motes.png` | dithered puff sheets and dust specks |
| `assets/cinematics/c4/homeward/w1_station.png`, `w1_glow.png`, `w1_door_{k,a}.png` | Veltrava platform 5 at first light (ray-cast: shed vault, globes, clock, the two trains with lit compartments and destination boards, benches, trolley, kiosk, the dawn in the opening); the two doors open / shut |
| `assets/cinematics/c4/homeward/w1_{konrad,alexei,conductor_k,conductor_a,porter,mother,child,babushka}.png` | the walkers and the platform's people (game sheets, re-lit) |
| `assets/cinematics/c4/homeward/w2_frames.png`, `w2_{sky,far,mid,near}_{berlin,karsk}.png`, `w2_streaks.png` | the two compartments (walnut / brass, reading lamp, suitcase; green panels, lace curtain, tea glass, bundle) and three depths of landscape per window, snow streaks |
| `assets/cinematics/c4/homeward/w3_alexei.png` | Alexei re-lit for the night yard |
| `assets/cinematics/c4/number/n1_*.png` | the wagon side (1100 px pan): fresh paint over old layers, the painted-over enamel plate „24 318“, the tin stencil with the wet C-17/45, chalk „ВТ 23.40“; lamp darkness + glow |
| `assets/cinematics/c4/number/n2_macro.png`, `n2_glints.png`, `n3a_macro.png`, `flakes.png` | the macros of the 45 (wagon / crate) |
| `assets/cinematics/c4/number/n3b_hatch.png`, `n3b_lip.png`, `n3b_stack.png`, `n3b_tail.png`, `n3b_shaft.png`, `exhaust.png` | the loading hatch at dawn: the loop's distant layers behind, the lorry with its tilt and tail lights, the A-frame hoist, the open shaft lit from below, the hoarding „BAUSTELLE / BETRETEN VERBOTEN“ |
| `assets/cinematics/c4/number/n4_{konrad,mother,child,worker}.png` | Konrad at the stop and the people waiting for the first tram |
| `assets/cinematics/c4/card/card_de.png`, `c1_bg.png`, `c1_*hand*.png` | the German half of card No. 0417, the snow by the split crate (tyre track, boot prints, fanned cards, a dropped chain), Konrad's gloved hands (figures stream) |
| `assets/cinematics/c4/card/c2_macro.png`, `c3a_macro.png`, `shadow.png` | the two macros of the perforation (mirrored), the moving fingertip shadow |
| `assets/cinematics/c4/card/c3b_desk.png`, `card_ru.png`, `c3_hand.png`, `flame.png`, `lamp_glow.png` | the siding booth's desk: stencils C-17/41–44, calendar February 1964, abacus, tea glass, pencil jar, stamp pad, freight ledger, the card box, the kerosene lamp; the Russian half; Alexei's hand |
| `assets/cinematics/c4/card/c4_bg.png`, `c4_lampglow.png`, `c4_alexei.png` | over Alexei's shoulder through the booth window onto the level's siding hall (dirty glass, frost in the corners, the lamp's reflection) |
| `assets/cinematics/c4/stamp/s1_*.png` | the desk from above: forms, notebook (pencil lines revealed at runtime), the card box „C-17/45 – ПРИНЯТЬ“, stamp and ink pad, tea glass, ashtray with Lev's cigarette, ruler, pencil shavings, the lamp's base; Lev's hand, the pencil hand, the small card |
| `assets/cinematics/c4/stamp/s2_slip.png`, `s3a_card.png`, `imp_ru.png`, `imp_de.png`, `stamp_ru.png`, `stamp_de.png`, `hand_ru.png`, `hand_de.png` | the overhead stamp inserts (same frame, same point) |
| `assets/cinematics/c4/stamp/s3b_back.png`, `s3b_counter.png`, `typist_{a,b}.png`, `s3b_hands.png`, `lever.png`, `split.png` | the counter close-up in front of the annex's card hall (level art, hazed), the frosted glazing with the level's typists at work, Fengler (figures stream), the perforating machine and the split card |
| `assets/cinematics/c4/stamp/s4_ladder.png`, `s4_konrad.png` | the foot of the shaft ladder in the annex (the level's ladder niche, fans, card cabinets), Konrad re-lit (idle / hand to the coat / looking up) |
| `assets/cinematics/c4/voices/v1_door.png`, `v1_file.png`, `v1_konrad.png` | the open steel door of S 2 (ladder rungs, warm air), the corner of the Lindner file, Konrad re-lit (morning) |
| `assets/cinematics/c4/voices/v2_konrad.png` | Konrad from behind: arm down / half / raised (figures stream) |
| `assets/cinematics/c4/voices/v3_*.png`, `lantern.png` | Alexei and Lev re-lit for the green signal, the squared notebook page with the four numbers, Lev's lantern glow |
| `assets/audio/sfx/c4cine_station.wav`, `_rails`, `_yard` | Homeward beds (doors at 3.75 / 4.05 s) |
| `assets/audio/sfx/c4cine_tunnel.wav`, `_drip`, `_hatch`, `_tram` | Number beds (tram bell at 11.4 s) |
| `assets/audio/sfx/c4cine_card_snow.wav`, `_perf`, `_perf_ru`, `_office` | Card beds (perforation ticks 3.6–4.85 s; a train over the vault) |
| `assets/audio/sfx/c4cine_desk.wav`, `_stamp_ru`, `_stamp_de`, `_annex` | Stamp beds (contacts at 3.86 / 5.36 s, perforator at 7.42 s) |
| `assets/audio/sfx/c4cine_column.wav`, `_tram_leave`, `_bell`, `_yard_night`, `_lamp_out`, `_tuesday` | Voices beds and the tram bell (rung once or twice by the picture; lamp flicks at 18.2 / 18.45 / 18.9 s) |
| `data/locale/de_c4_cine.json` | memory film titles and subtitles of the five films |
