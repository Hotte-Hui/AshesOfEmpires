# Asset manifest part -- env_c3p2_night (Chapter 3 part 2, the night quay, L_C3_Quay)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_c3p2_quay.py` drives `env_c3p2_quay_far.py`, `env_c3p2_quay_near.py` and `env_c3p2_quay_life.py`; the shared
helpers are `env_c3p2_quay_kit.py` and the read-only `env_veltrava_lib.py` / `pg.py`).  No pixels were copied, traced,
sampled, downloaded or AI-generated; no third-party assets, fonts or textures are embedded; the pixel fonts are the
hand-defined Veltrava fonts of `env_veltrava_lib.py`.

* Licence / rights: project-owned original artwork, freely redistributable with the game.  Provenance: deterministic
  generator with fixed seeds (a re-run reproduces every file byte for byte on the same Python/Pillow build), re-run
  with `py -3 -P tools/pixelgen/env_c3p2_quay.py` (`--preview=DIR` adds CPU composites, no Godot lighting).
  Machine-readable list of every file: `assets/environments/veltrava_quay/provenance.json`.
  The generator never touches `assets/environments/veltrava_quay/explore_hotspots.json` (exploration stream).
* Date: 2026-11-06 (round 8).
* Design contract: `documentation/C3P2_DESIGN.md` §5.2 -- every spawn, hotspot and zone name/position of the story
  shell is kept (`bench` 760, `konrad_quay` 800, `typist_quay` 330, `guard_quay` 1050, `kessler_quay` 1180,
  `voronova_quay` 1330, `journalist_quay` 1560, `SP_C3_Quay` (560, 300); walk band y 296-306).
* Painting model: geometry is drawn as (material, tone, height) and one "night bake" (`env_c3p2_quay_kit.resolve`)
  applies the scene's light fields to every lit plane and prop (six balustrade lanterns, the pylon and shelter
  lamps, five burning souterrain windows, the engine's headlight): cold ladder under the night sky, warm ladder in
  lamplight, amber/red ladder in the fire light, all colours from the Veltrava palette of `data/chapters/c3.json`
  (+ its skin ramp) -- stable under the post-grade palette snap (grade `quay`).  Emissive glass/flames also write
  `_e` maps (added unshaded); `glow_air.png` is a soft additive halo layer.
* Palette: `veltrava` only (checked by the generator and by `tests/test_c3p2_env_art.gd`).
* Insignia (TECHNICAL_ARCHITECTURE §12.4): only the fender pennants of the two delegation cars.  `props/car_ussr.png`
  (neutral: red with the fictional gear-and-wheat badge) / `props/car_ussr_hist.png` (star, hammer and sickle);
  `props/car_reich.png` (neutral: grey with the fictional Reichssiegel) / `props/car_reich_hist.png` (the historical
  pennant).  Chosen at runtime by `Symbols.pick()`; in-world iconography of the regimes inside the critical narrative
  only, never on people.  No life strip has a `_hist` twin.
* Content: nobody is heroised, nobody is a caricature.  The firemen, the woken neighbours, the two aides and the
  two drivers who share one lighter are anonymous working people; the delegation heads and the cast are the level's
  NPCs (not painted).  No injury, no gore; the fire is shown through light, flames in the windows, smoke and steam.
* Accessibility: the searchlights sweep at 6.7 s / 8 s per sweep; flame strips change shape at <= 6 fps (flicker
  <= 3 Hz); the blue beacon turns once a second without a flash; Godot light flicker <= 0.22; nothing flashes the
  screen.

| File(s) under `assets/environments/veltrava_quay/` | Generator | Content |
|---|---|---|
| `sky.png` | env_c3p2_quay_far.py | overcast snow night, faint cold glow over the Line (p 0.02) |
| `far_bank.png` (+ `_e`) | env_c3p2_quay_far.py | the far bank: hills, double fence, six floodlight masts with cold pools, five watchtowers (two with searchlights) (p 0.10) |
| `river.png` (+ `_e`) | env_c3p2_quay_far.py | the frozen river: drifts, pressure ridges, the open black lead; the three-arch bridge with the city arms, eight lamps, the barrier and the guard hut of the Line (p 0.30) |
| `oldtown.png` (+ `_e`) | env_c3p2_quay_far.py | the old town beyond the river bend: gables with warm windows, the church tower with a lit clock, the embankment with lamps (p 0.45) |
| `pall.png` | env_c3p2_quay_far.py | the smoke of the wing gathering under the clouds, fire-lit near the source, drifting right (p 1) |
| `wing.png` (+ `_n`, `_e`) | env_c3p2_quay_near.py | the corner of the burning east wing (Kurhaus 1909): fire behind the bars of five souterrain windows, soot plumes, dark upper windows mirroring the fire, one lit dormer, the yard railing with the open gate, the iron coal hatch, coal dust and two body prints in the snow |
| `promenade.png` (+ `_n`, `_e`) | env_c3p2_quay_near.py | the quay: snow, hydrant and hose lines, tyre tracks, footprints of two men from the hatch to the bench, the balustrade with six lanterns, two snowed-in benches, the bridgehead pylon with the great lantern and the city arms, the ramp wall, tram stop (lines 7 / 12) and shelter with a commission poster, catenary poles and wire |
| `glow_air.png` | env_c3p2_quay_near.py | soft additive halos (lanterns, fire windows, headlight), alpha in dithered steps |
| `fg.png` | env_c3p2_quay_near.py | low dark snow banks and bollards along the bottom edge (p 1.25, below y 318) |
| `props/fire_engine.png` (+ `_n`, `_e`) | env_c3p2_quay_near.py | ladder truck of the Veltrava fire brigade, turntable ladder at a first-floor window, FEUERWEHR lettering, the city arms on the door |
| `props/car_reich.png`, `props/car_reich_hist.png` (+ `_n`, `_e`) | env_c3p2_quay_near.py | the German delegation car with its fender pennant (neutral / historical) |
| `props/car_ussr.png`, `props/car_ussr_hist.png` (+ `_n`, `_e`) | env_c3p2_quay_near.py | the Soviet delegation car with its fender pennant (neutral / historical) |
| `props/bench_file.png` (+ `_n`) | env_c3p2_quay_near.py | the bench at x 760: the file burst open, two fans of sheets, the red C-17 tag and its string, sheets in the snow, soot smudges |
| `props/trestle.png` (+ `_n`) | env_c3p2_quay_near.py | the commission guard's striped trestle barrier |
| `life/hose_team.png`, `ladder_man`, `pump_man` (+ maps) | env_c3p2_quay_life.py | firemen: the jet into the first window, a man on the ladder, the machinist at the pump |
| `life/onlookers.png` (+ maps) | env_c3p2_quay_life.py | woken neighbours behind the trestle (a woman in a coat over her nightdress, an old man pointing, a boy on tiptoe) |
| `life/aide_kessler.png`, `life/aide_voronova.png` (+ maps) | env_c3p2_quay_life.py | the two aides waiting apart (briefcase and watch / folder and cold hands) |
| `life/drivers.png` (+ maps) | env_c3p2_quay_life.py | the two chauffeurs share one lighter between the cars, then smoke |
| `life/beacon.png` (+ `_e`) | env_c3p2_quay_life.py | the blue rotating lamp on the cab |
| `life/fire_win_1..5.png` (+ `_e`) | env_c3p2_quay_life.py | flames licking out of the souterrain windows |
| `life/embers_1..3.png` (+ `_e`) | env_c3p2_quay_life.py | sparks rising over three windows (emission only) |
| `life/searchlight_a.png`, `searchlight_b.png` (+ `_e`) | env_c3p2_quay_life.py | the searchlight beams sweeping the ice, with snow glinting in the light (emission only) |
| `life/town_win_1..6.png` (+ `_e`) | env_c3p2_quay_life.py | old-town windows lighting up as people wake (60 s loop) |
| `fx/smoke_1..3.png`, `fx/smoke_ladder.png` | env_c3p2_quay_life.py | continuous smoke columns (seamless periodic turbulence) |
| `fx/steam_jet.png` | env_c3p2_quay_life.py | steam where the jet hits the fire |
| `fx/chimney_1..4.png` | env_c3p2_quay_life.py | old-town chimney smoke |
| `fx/exhaust_ussr.png` | env_c3p2_quay_life.py | the idling Soviet car's exhaust |
| `scene.json`, `provenance.json` | env_c3p2_quay.py | art manifest (TECHNICAL_ARCHITECTURE §3.1) incl. `explore_sites` suggestions; file provenance |

Screenshots (Forward+, real GPU, `res://tests/visual/c3_station_shots.tscn -- --scene=L_C3_Quay`):
`documentation/screenshots/c3p2_night_cam0000.png`, `_cam0480`, `_cam0960`, `_cam1280`, the contact sheet
`c3p2_night_contact.png` (six cameras) and `c3p2_night_symbols_neutral_vs_hist.png` (the car pennants).
