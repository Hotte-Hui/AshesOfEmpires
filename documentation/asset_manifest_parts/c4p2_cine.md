# Asset manifest part — c4p2_cine (Chapter-4 part-2 cinematics LS_C4P2_Depot, _Steam, _Book, _Express, _Clock)

* **Date:** 2026-11-06 (round 10)
* **Area owner:** cine stream (C4P2_DESIGN.md §2.9, §10)
* **Scenes / code:** `scenes/cinematics/ch4p2_depot/` (`Ch4p2Depot.tscn`, `ch4p2_depot.gd`), `ch4p2_steam/`,
  `ch4p2_book/`, `ch4p2_express/`, `ch4p2_clock/`, shared `scenes/cinematics/ch4p2_common/c4p2_cinematic.gd` (extends
  the C4 base `c4_common/c4_cinematic.gd` and through it the §12.5 contract of `ch3_common/c3_cinematic.gd`: textures
  and `layout.json` from `assets/cinematics/c4p2/`, sheets with any cell width, `puffs()` steam / breath emitters as
  pure functions of t, `optional_amb()`, `c4g()` / `c4d()` with the drivers' defaults). Registered in
  `data/chapters/c4p2.json` → `cinematics`, played by `ChapterExt.play_cinematic()`. Lengths = the registered shot
  sheets of `data/v3/cinematics.json`: 13 / 12.5 / 12 / 13 / 24 s (74.5 s in all). Film titles for the memory page
  „Filmsequenzen“: `data/locale/de_c4p2_cine.json`.
* **Match cuts (hard cuts on shared objects, each city in its own palette):** the safety valve's steam jet (one
  12-frame jet sheet on one clock at one anchor `steam.jet_base`, over the Karsk engine's twin pop valves against the
  coal stage at dawn and the Berlin express engine's brass valve under the iron and glass of the roof; one sound bed
  across the cut that changes rooms on it); the guidebook (on the tables one 3-D model, `env_c4p2_cine_book3d.py`,
  seen from above; in the macros one profile drawing — the closing book on the dining car's damask and the opening
  book on the canteen's oilcloth are the same pixels at the same place, the same card corner); the red lamp (the
  express's tail lamp and the building site's warning lamp at one centre `express.lamp_c` and one radius). The
  macro_to_medium moves (b3, m3) are hard cuts on the movement with a small settle of the camera — no dissolves.
* **Generators:** `py -3 -P tools/pixelgen/env_c4p2_cine.py [--only depot,steam,book,express,clock]` writes every
  texture (~150 files) and `assets/cinematics/c4p2/layout.json` (anchors shared with the runtimes;
  `tests/test_c4p2_cinematics.gd` checks them). Close and macro plates and most establishing plates are **painted
  flat as pixel art** by `env_c4p2_cine_flat.py`: every surface a flat colour from a short ramp, light laid on in
  stepped rings with a one-pixel checker seam, a dark outline on the shadow side, a lit edge on the key side, cast
  shadows as flat offset silhouettes, textures as explicit patterns (damask lattice, the canteen oilcloth's rose
  print in perspective, plank floors, cobbles, brick bond, quilting) — no soft gradients, no bokeh, no blur.
  `env_c4p2_cine_hands.py` draws hands and sleeves with the game's own sprite shader (chargen_core: six-tone ramps,
  cel thresholds, the selective outline, inner lines, contact shadows) at full resolution: fingers as single parts
  with creases, knuckles and nails, gloves with their stitched points and press stud, sleeves whose height field
  carries real folds (navy wool with a shirt cuff, tweed in herringbone, the quilted telogreika with its knitted cuff).
  `env_c4p2_cine_loco.py` paints the steam engines (soviet 2-10-0, the polished green show engine with ribbons and
  garland, the german express with smoke deflectors; side-on with tender, and head-on) with stepped cylinder bands,
  rivets, domes, pop valves, rods, valve gear, spoked wheels and snow on every upper edge. `env_c4p2_cine_busts.py`
  runs the dialogue-portrait pipeline (read-only) without its background so the close figures are the cast's own
  busts; `env_c4p2_cine_people.py` places the rig figures on their contact shadows, graded by the shot's light with a
  rim on the key side; `env_c4p2_cine_show.py` is the depot showcase (Book b4). The wide plates of Depot p1/p2 still
  use the G-buffer painter of `env_c4p2_cine_kit.py` (lights, palette quantiser; calm wind-laid snow), with the
  stall's interior in p2 painted flat. Other modules: `env_c4p2_cine_pal.py` (city palettes),
  `env_c4p2_cine_places.py` (skyline, roundhouse, masts, gantry crane, coal heap, wagons, fire basket, the jet),
  `env_c4p2_cine_rig.py` (poses and props on the rig — the shovel cycle digs, bites low and throws high),
  `env_c4p2_cine_book3d.py` and one module per film. The earlier signed-distance busts and hands
  (`env_c4p2_cine_figs.py`) were removed in the lead's round-10 cleanup, with the stale `express/x2_band.png`.
  Sound: `py -3 -P tools/audiogen/c4p2_cine_audio.py [--only ...]` →
  `assets/audio/sfx/c4p2cine_*.wav` (21 beds incl. the stand-in tick); the picture-synced times are module constants
  checked by the test, the shovel bites and the teleprinter's characters are read from `layout.json`.
* **Figures:** the people of the wide shots are the game's own rig (`chargen_body` with the cast specs of
  `chargen_cast*`, `characters_c4` and the round-10 cast stream's `characters_c4p2`) in poses made for these films —
  eleven returnees of Kolonne 4 on their own footing down the heap, out of step, each with its own lean and reach
  (8-frame cycle, the contact frame drives the sound), a twelfth resting on his shovel, Alexei's walk with the
  toolbox, a fitter's oil can, the tarpaulin men, a works band of six in two rows round the drum, the depot chief,
  the bread-and-salt woman, workers, the photographer, the guard, the minder's match; platform K in three depths with a
  clear lane for Konrad (1 texel = 1 px, never scaled). Close figures are the cast's **dialogue busts** at their native
  112 px, graded to the shot (Irina at her dispatch window, p3; Irina at the teleprinter and Alexei outside the frosted
  window, k3; Ekdahl behind his compartment window with the film canister / the open empty hand, x1; Lev on the
  platform, his coat continued below the bust, with the white bundle of carbons going under his coat or his empty
  hands shown, x2). Over-the-shoulder figures are painted silhouettes with a lit rim (Alexei from behind in x2 and m1).
  Hands of the book shots: Konrad's bare right hand, Ekdahl's grey gloves (resting, reaching, lifting; and from the
  side in the macro), Alexei's worn hand where Konrad's lay (`env_c4p2_cine_hands.py`). Far figures (Kordon-17) are
  painted small. Stand-ins: none (`layout.json` → `standins` is empty).
* **Content rules:** no violence shown, no face at Tür Ost, nobody inside a wagon (Kordon-17 only wide and from far:
  figures 12 px, no force); the guard is a bored boy at a fire, not a threat staged for effect; the slogan banners are
  shown as the place has them (ВОССТАНОВИМ ВМЕСТЕ patched with sacking; ДОБРО ПОЖАЛОВАТЬ for the press) and the
  pictures put the people before them (the tarpaulin with the shovellers' shadows behind the showcase). No real
  insignia, no state emblems (the engines carry number plates; the band wears plain caps); no brands (the dining car,
  the guidebook — a Swedish „resehandbok“ of 1938 — and the canister are generic). The pre-rename name of the German
  protagonist never appears. Typed and printed texts: KARSK, СТОЙЛО 7, ДИСПЕТЧЕРСКАЯ, ДОБРО ПОЖАЛОВАТЬ, ВОССТАНОВИМ
  ВМЕСТЕ, the board's trains (E 412 WARSCHAU, P 1307 STRALSUND, P 1188 FRANKFURT(O); P 1265 FÜRSTENWALDE flipping to
  D 303 KARSK 21.10 K), ABFAHRT / ОТПРАВЛЕНИЕ, ZEITUNGEN, ERFRISCHUNGEN, BERLIN - KARSK D 303, КАРСК - БЕРЛИН,
  СПАЛЬНЫЙ ВАГОН, ПРЯМОГО СООБЩЕНИЯ, SPEISEKARTE, the canteen paper СИГНАЛ, ГРАФИК, ТА-68, ПЕСОК, ПГ, КОРДОН-17,
  SCHUHMACHEREI PIETSCH, KOHLEN · BRIKETTS, BAUSTELLE / BETRETEN VERBOTEN, the hoarding's posters (RADRENNEN, KINO,
  WINTERBALL, TANZ, SAMMLUNG), the engines' plates (Л-2238, Л-1964, 01 1064, DR as on the level's express), the card half (0417, LINDNER, ANNA, GEB. KOWALENKO — the item text),
  the teleprinter (ПЕРЕДАЧА ПРИОСТАНОВЛЕНА ТЧК / С-17/45 УБЫЛ КОРДОН-17 ТЧК, C4P2_DESIGN §2.9 k3).
* **Provenance:** every image and sound is original, generated in code from fixed seeds (no time, no global random
  state, no image or audio inputs, nothing traced or sampled). Reference study only (railway depots, coaling stages,
  Soviet and German steam engines, Berlin tenement courtyards, split-flap boards, teleprinters) — nothing copied.
* **Tests:** `tests/test_c4p2_cinematics.gd` (27 cases: contract, registered lengths and shot order, finished once in
  every path, readable German lines ≤ 19 characters per second, every texture / sound present, layout in sync, frames
  a pure function of t, the three match cuts, the decision shown per c4g / c4d, reduced motion, sound sync for all five
  films; and the art review of round 10: no dissolve in the macro_to_medium moves, the close figures are the dialogue
  busts, Kolonne 4 off the ruled line and out of step, Konrad's lane on platform K clear, the courtyard's tilt (a cut
  with reduced motion), Lev's gesture readable at a glance); `tests/test_c3_assets.gd` runs the five films with
  c3b-level contexts.
