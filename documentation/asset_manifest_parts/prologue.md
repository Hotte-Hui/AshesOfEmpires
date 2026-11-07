# Asset manifest part — prologue (LS_Prologue, the prologue of a new game)

* **Date:** 2026-11-07 (round 11)
* **Area owner:** prologue stream
* **Scene / code:** `scenes/cinematics/prologue/` (`Prologue.tscn`, `prologue.gd`; extends the C4 base
  `c4_common/c4_cinematic.gd` and through it the §12.5 contract of `ch3_common/c3_cinematic.gd`). Not a Story
  cinematic: played by `Game._cin_prologue()` after the opening note of a NEW game (never on load), listed first on the
  „Filmsequenzen“ page (`Game.memory_films`). 60 s, five shots, subtitles only (`data/locale/de_prologue.json`),
  shot changes dip through black, every frame a pure function of t (`tests/test_prologue.gd`).
* **Insignia:** none in any shot (no `*_hist` files, nothing for `Symbols.pick()` to swap).

| Path | What | How it was made |
|---|---|---|
| `assets/cinematics/prologue/p1_line.png` | dusk over the snowfield: the armistice Line (posts, barbed wire, ploughed control strip, dragon's teeth), a watchtower against the last light, ruined villages on the horizon, a birch in front (680 × 360: the camera drifts) | `py -3 -P tools/pixelgen/env_prologue.py` (float painting on crisp masks, resolved once to a median-cut palette with Bayer dither, `env_prologue_kit.py`) |
| `assets/cinematics/prologue/p1_windowglow.png` | the tower window's breathing glow (additive) | same |
| `assets/cinematics/prologue/p2_map.png`, `p2_veltrava.png` | a paper map under a desk lamp (Baltic and Black Sea with hatched coasts, rivers, graticule, relief marks, BERLIN / KARSK, a red pencil); the label „FREIE STADT VELTRAVA“ (the Line, the ring and the three corridors with their trains are drawn at runtime from `layout.json`) | same; pixel fonts of `env_veltrava_cine_kit.py` (read-only) |
| `assets/cinematics/prologue/p3_papers.png`, `p3_stamp.png`, `p3_shadow.png`, `p3_imprint.png` | a freight office desk: the bilingual Frachtbrief of Korridor II (wagons 17-0417 …), a card index, a lead seal, the ink pad; the rubber stamp seen from above, its shadow, the violet „C-17 / ANLAGE C“ imprint | same |
| `assets/cinematics/prologue/p4_berlin.png`, `p4_lampglow.png` | a drafting hall in Berlin at dawn: the tall window, rooftops in snow, the dome of the Great Hall in the haze, pinned blueprints, the drafting table, the plan chest and its lamp (glow additive) | same |
| `assets/cinematics/prologue/p4_konrad.png` | Konrad at the window: the `idle_back` frames of his game sheet `assets/characters/konrad/sheet.png`, re-lit as a cool silhouette with window rims | same (re-lit, not redrawn) |
| `assets/cinematics/prologue/p5_karsk.png` | the Karsk yard at night: tracks into the dark, the floodlight mast, the lit signal box, a waiting locomotive, a wagon with the chalked „C-17“, the works on the horizon | same |
| `assets/cinematics/prologue/p5_alexei_walk.png`, `p5_alexei_idle.png` | Alexei walking in and standing: `walk_side` / `idle_side` of `assets/characters/alexei/sheet.png`, re-lit for the night with a warm rim | same (re-lit, not redrawn) |
| `assets/cinematics/prologue/p5_cone.png`, `p5_signal.png`, `p5_headlamp.png` | floodlight cone, the signal lamp (red | green), the locomotive's headlamp (all additive) | same |
| `assets/cinematics/prologue/layout.json` | runtime anchors (pans, lamp, map polylines, imprint, window, feet, walk) | same |
| `assets/audio/music/mus_prologue.wav` | the prologue's score (~64 s, one-shot): D-minor string ground under the Line, piano pins and a pluck pulse on the map, an Eb colour and a low pedal when the stamp lands, B (Konrad) on celesta in Berlin, K (Alexei) on felt piano in Karsk, ending open on A sus2 | `py -3 -P tools/audiogen/prologue_audio.py` (the game's own motifs and instruments of `music.py`, read-only) |
| `data/locale/de_prologue.json` | the 15 subtitles and the film's title on the „Filmsequenzen“ page | written by hand from `documentation/WORLD_BIBLE.md` / `STORY_BIBLE.md` |

Sounds reused from earlier rounds (unchanged): `karsk_wind_gust_1/2`, `paper_rustle_1/2/3`, `karsk_train_far`,
`stamp_thud`, `berlin_tram_bell`, `train_horn_far`, ambience `amb_karsk_yard`.
