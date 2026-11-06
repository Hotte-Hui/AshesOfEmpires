# Asset manifest part — c4_cine (Chapter-4 cinematics LS_C4_Homeward, _Number, _Card, _Stamp, _Voices)

* **Date:** 2026-11-06 (round 9)
* **Area owner:** cine stream (C4_DESIGN.md §2.9, §10)
* **Scenes / code:** `scenes/cinematics/ch4_homeward/` (`Ch4Homeward.tscn`, `ch4_homeward.gd`), `ch4_number/`,
  `ch4_card/`, `ch4_stamp/`, `ch4_voices/`, shared `scenes/cinematics/c4_common/c4_cinematic.gd` (extends the C3P2
  base `c3p2_common/c3p2_cinematic.gd` and through it the §12.5 contract of `ch3_common/c3_cinematic.gd`: textures from
  `assets/cinematics/c4/`, `line_dur()` keeps every subtitle under 19 characters per second, the game's character
  sheets drawn by named frame ranges, the in-game stride so feet never slide, `optional_music()`). Registered in
  `data/chapters/c4.json` → `cinematics`, played by `ChapterExt.play_cinematic()`. Lengths = the registered shot
  sheets of `data/v3/cinematics.json`: 14 / 13 / 11 / 11 / 24 s.
* **Match cuts (hard cuts on shared objects, the cities in their own palettes):** the stencilled 45 of wagon C-17/45
  (cream on red-brown in Karsk → black on pine in Berlin, same shapes at the same place: one stencil generator, one
  layout entry `number.macro`); the torn perforation of card No. 0417 (German half, paper left of the edge → Russian
  half, paper right of it: one perforation geometry, mirrored); the rubber stamp (ПРИНЯТЬ violet → ABGANG red, same
  frame at the same contact point).
* **Generators:** `py -3 -P tools/pixelgen/env_c4_cine.py [--only places,homeward,number,card,stamp,voices]` writes
  every texture and `assets/cinematics/c4/layout.json` (anchors shared with the runtimes; `tests/test_c4_cinematics.gd`
  checks them). Modules: `env_c4_cine_kit.py` (palettes, stencil letters, perforation, stamps, re-lighting of the game
  sheets with their normal maps), `env_c4_cine_places.py` (Karsk freight yard, Berlin tram loop in dawn and morning
  light, the tram of line 74, the siding hall lit / dark), `env_c4_cine_{homeward,number,card,stamp,voices}.py`,
  `env_c4_cine_figs.py` (hands and the two men from behind). Sound: `py -3 -P tools/audiogen/c4_cine_audio.py` →
  `assets/audio/sfx/c4cine_*.wav` (21 files; the picture-synced times are constants checked by the test).
* **Figures:** close-ups (Konrad's gloves on the card, Alexei's hand on the desk, the pencil hand, Lev's hand with the
  missing fingertip, both stamp hands, Fengler's hands, Alexei over the shoulder, Konrad from behind waving) are
  sculpted and lit with the signed-distance pipeline of the dialogue portraits (`chargen_portrait2_*`,
  `env_c3p2_cine_hands`, `env_veltrava_cine_figs`; all imported read-only). Wide shots use the game's own sheets
  (`assets/characters/{alexei,konrad,lev}/sheet.png` + `sheet_n.png`, 32 x 56 cells) re-lit per shot from their
  normal maps, so the cinematic figures are the figures the player walks with. A character without a delivered
  sheet would be drawn from a declared stand-in and listed in `layout.json` → `standins` (currently empty).
  Renders are memoised on disk (keyed by the pipeline sources + this stream's sources + arguments).
* **Determinism:** fixed seeds everywhere; two full builds are byte-identical (md5 over all PNG/JSON outputs and all
  WAVs, checked 2026-11-06).
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio made for ASHES OF
  EMPIRES: THE LAST WINTER by these generators (AI-authored code, project-owned, same licence as the game). No
  downloaded, copied or traced images, fonts or samples. The only image inputs are the project's own character
  sheets (above). No insignia anywhere (the stamps, signs, cap badge „74“ and forms are plain text), so there are no
  `_hist` variants. The Great Hall's dome appears only as a far silhouette in the haze.
* **Texts:** memory film titles `ui.memories.film.LS_C4_*` / `film_sub.*` in `data/locale/de_c4_cine.json` (this
  stream); the films' subtitles are the story stream's `data/locale/de_c4_cinematics.json`.

| path | what |
|---|---|
| `assets/cinematics/c4/layout.json` | anchors for the five runtimes (sections places, homeward, number, card, stamp, voices, standins) |
| `assets/cinematics/c4/places/yard.png`, `yard_parapet.png`, `yard_green.png`, `yard_warm.png` | Karsk freight yard before dawn (Homeward w3, Voices v3): signal, wagons, cooling towers, freight office with the lit cellar window and the outside stair |
| `assets/cinematics/c4/places/loop_dawn.png`, `loop_morning.png`, `loop_glow_*.png` | the tram loop Süd 8, 1000 px (Number n4, Voices v1/v2): house No. 9 sealed, the wallpaper of the demolished neighbour, No. 11 with Marta's window, the shelter, the column S 2 as the level paints it (rounded cap with finial, „KONZERT“ / „KINO“ posters, the notice with a neutral seal ring; morning: the poster torn back from the steel door „S 2“), the C-17/45 crates |
| `assets/cinematics/c4/places/tram_left.png`, `tram_right.png` | the two-axle car of line 74, No. 3518, in the level's livery (cream body, dark belt rail at the sill, red pinstripe above the skirt, lantern roof with lit clerestory and bow collector; Marta in the cab, Ilse at the last window; right-facing sheet with/without her hand on the glass, line board and fleet number never mirrored) |
| `assets/cinematics/c4/places/siding_lit.png`, `siding_dark.png`, `siding_glow.png` | the siding hall with wagon 24 318 / C-17/45 under its work lamp (Voices v4) |
| `assets/cinematics/c4/places/breath.png`, `steam.png` | dithered puff sheets |
| `assets/cinematics/c4/homeward/w1_*.png` | Veltrava station at first light, the two trains (BERLIN / КАРСК), Konrad and Alexei re-lit (walk back / side) |
| `assets/cinematics/c4/homeward/w2_*.png` | split windows: carriage interiors, sky + far + tiled near strips (the dome of the Great Hall; the snow plain and the cooling towers of Karsk) |
| `assets/cinematics/c4/homeward/w3_alexei.png` | Alexei re-lit for the night yard |
| `assets/cinematics/c4/number/n1_*.png` | the wagon side (1100 px pan): fresh paint over old layers, the painted-over enamel plate „24 318“, the tin stencil with the wet C-17/45, chalk „ВТ 23.40“; lamp darkness + glow |
| `assets/cinematics/c4/number/n2_macro.png`, `n2_glints.png` | macro: the 45 through the tin, wet glints |
| `assets/cinematics/c4/number/n3a_macro.png`, `flakes.png` | macro: the same 45 black on a pine crate, macro snowflakes |
| `assets/cinematics/c4/number/n3b_*.png`, `exhaust.png` | the loading hatch at dawn: lorry, hoist, the stack of crates, tail-light glow |
| `assets/cinematics/c4/number/n4_konrad.png` | Konrad re-lit for the dawn loop |
| `assets/cinematics/c4/card/card_de.png`, `c1_*.png` | the German half of card No. 0417 (typed, red C-17 tab), the snow by the split crate, Konrad's gloved hands (the right coat sleeve runs on past the frame edge / under the letterbox) |
| `assets/cinematics/c4/card/c2_macro.png`, `c3a_macro.png`, `shadow.png` | the two macros of the perforation (mirrored), the moving fingertip shadow |
| `assets/cinematics/c4/card/c3b_desk.png`, `card_ru.png`, `c3_hand.png`, `flame.png`, `lamp_glow.png` | the siding office desk: the Russian half, Alexei's hand, the kerosene lamp, the stencils C-17/41–44 on the wall |
| `assets/cinematics/c4/card/c4_bg.png`, `c4_alexei.png` | over Alexei's shoulder to the wagon beyond the booth window (head down / up) |
| `assets/cinematics/c4/stamp/s1_*.png` | the desk from above: notebook (pencil lines revealed at runtime), the card box „C-17/45 – ПРИНЯТЬ“, Lev's hand, the pencil hand, the small card |
| `assets/cinematics/c4/stamp/s2_slip.png`, `s3a_card.png`, `imp_ru.png`, `imp_de.png`, `stamp_ru.png`, `stamp_de.png`, `hand_ru.png`, `hand_de.png` | the overhead stamp inserts (same frame, same point) |
| `assets/cinematics/c4/stamp/s3b_*.png`, `lever.png`, `split.png` | the annex counter: Fengler leaning over it (his chest in grey dust coat, shirt and tie, the lapel badge without insignia; the upper arms of `s3b_hands.png` run up into the letterbox to his shoulders), the perforating machine and its lever, the split card, cabinets, typists behind glass |
| `assets/cinematics/c4/stamp/s4_ladder.png`, `s4_konrad.png` | the foot of the shaft ladder between the card cabinets, Konrad re-lit (fluorescent) |
| `assets/cinematics/c4/voices/v1_*.png` | the column's open service door, the Lindner file corner, Konrad re-lit (morning) |
| `assets/cinematics/c4/voices/v2_konrad.png` | Konrad from behind: arm down / half / raised |
| `assets/cinematics/c4/voices/v3_*.png`, `lantern.png` | Alexei and Lev re-lit for the green signal, the notebook insert with the four numbers, Lev's lantern glow |
| `assets/audio/sfx/c4cine_station.wav`, `_rails`, `_yard` | Homeward beds (doors at 3.75 / 4.05 s) |
| `assets/audio/sfx/c4cine_tunnel.wav`, `_drip`, `_hatch`, `_tram` | Number beds (tram bell at 11.4 s) |
| `assets/audio/sfx/c4cine_card_snow.wav`, `_perf`, `_perf_ru`, `_office` | Card beds (perforation ticks 3.6–4.85 s; a train over the vault) |
| `assets/audio/sfx/c4cine_desk.wav`, `_stamp_ru`, `_stamp_de`, `_annex` | Stamp beds (contacts at 3.86 / 5.36 s, perforator at 7.42 s) |
| `assets/audio/sfx/c4cine_column.wav`, `_tram_leave`, `_bell`, `_yard_night`, `_lamp_out`, `_tuesday` | Voices beds and the tram bell (rung once or twice by the picture; lamp flicks at 18.2 / 18.45 / 18.9 s) |
| `data/locale/de_c4_cine.json` | memory film titles and subtitles of the five films |
