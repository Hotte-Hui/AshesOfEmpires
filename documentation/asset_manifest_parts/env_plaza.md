# Asset manifest part — plaza-env (L_M1_Plaza art, 2026-11-05)

Walkable level "Platz vor der Großen Halle" after the parade cinematic: evening, snow, palette `berlin`, Mode B
(oblique 2.5D like Karsk), world 1920×360. All assets are original and generated deterministically by the scripts
below (licence: project-owned, no third-party material, no downloads). Level root (owned by plaza-explore):
`scenes/levels/L_M1_Plaza.tscn` with `art_manifest = res://assets/environments/hall_plaza/scene.json`.

## Generators
| Command | Writes |
|---|---|
| `py -3 -P tools/pixelgen/env_plaza.py [--preview=DIR]` | everything under `assets/environments/hall_plaza/` incl. `scene.json`; runs the hotspot check (inside walk band, outside collisions, ≥ 26 px in the oblique metric dy×1.6) and the palette check; optional software previews |
| (module) `tools/pixelgen/env_plaza_sprites.py` | people painters (spectators from behind, guards front, marching soldiers 8-frame step), props, actor sheets, fx strips |
| `py -3 -P tools/audiogen/plaza_sfx.py` | `assets/audio/sfx/plaza_march_loop.wav` (8 s seamless loop, `smpl` chunk), `plaza_tank_pass.wav` (9 s), `plaza_shutter.wav` (0.6 s) |

Read-only reuse: `pg.py`, `env_berlin_insignia.py` (eagle / swastika masks), `env_berlin_kit.reichssiegel_mask`,
`env_karsk_lib.figure` (vendor, tank crewman; off-palette pixels snapped), `scripts/levels/karsk/karsk_actor.gd` (base).

## Layers (`scene.json` → LayerStack)
| File | Parallax / z | Content |
|---|---|---|
| `sky.png` | 0.12 / -100 | overcast dusk, cloud base lit by the searchlights, faint afterglow |
| `fx/beams.png` (12 frames, 3 fps, alpha 0.5) | 0.12 / -95 | 12 searchlight pillars ("Lichtdom"), slow sway |
| `hall.png` + `_n/_e`, `hall_hist.png` | 0.12 / -90 | Great Hall: block with pilasters and 8 banners, portico with nine piers and the state eagle, drum colonnade, ribbed patina dome, lantern with the (plain) eagle above the globe, warning lights |
| `far_plaza.png` + `_n/_e`, `far_plaza_hist.png` | 0.45 / -80 | tribune (banners, officials, lectern, floodlights), standing formations, flag masts |
| `ground.png` + `_n/_e` | 1 / -16 | avenue setts, guard strip, crowd strip, pavement with walking band and snow ridges, kerb, street with tram rails, manholes, lamp reflections, cleared lot |
| `plaza_mid.png` + `_n/_e` | 1 / -14 | guards facing the crowd, striped trestle barrier with sign board, 3 flood masts, chain line of the lot |
| `street_back.png` + `_n/_e` | 1 / -13 | side street to the archive, two tenements (sealed family door, shop shutter, balcony, lit windows, mansard, chimneys), fire wall of the cleared block |
| `fg_frame.png` | 1.25 / 60 | dark snow mounds and bollards at the bottom edge |

Decals: `props/window_life.png` (8 frames, emission), `props/notice_door.png` (+`_hist`), `props/banner_near.png`
(6 frames, +`_hist`), `props/crowd_1..7.png` (4 frames, 2 fps, playfield, base_y 266).
Props (y-sorted, collision where in the walk band): `lamp_post` ×2, `tram_stop`, `litfass` (+`_hist`), `loudspeaker`,
`children` (+`_hist`), `banner_mast`, `vendor` (emission), `photographer`, `tank_parked`, `barrel_guard` (emission),
`rubble_a`, `rubble_b`. FX strips: `fx/smoke.png`, `fx/steam.png`, `fx/exhaust.png`; snow and two fog bands.

## Actors (scenes/levels/plaza, scripts/levels/plaza)
| Scene | Behaviour |
|---|---|
| `PlazaParade.tscn` / `plaza_parade.gd` | endless procession left→right at 20 px/s, in step (7 fps): standard bearers (`actors/standard.png` + `_hist` via `Symbols.pick`), blocks of 4×9 anonymous helmeted soldiers (`actors/march_block.png`), tanks (`actors/tank.png`, exhaust puffs); z -15 between ground and guards. Drum/boots loop via `Audio.sfx_loop("plaza_march_loop", "plaza_march", dB)` following the nearest block (−9…−26 dB), stopped on exit; `plaza_tank_pass` when a tank comes on screen |
| `PlazaFlash.tscn` / `plaza_flash.gd` | the photographer's flash every 8–14 s (additive star + 0.3 s cold light, `plaza_shutter`); weak with `reduced_motion`, never a strobe |

## Contract data
Spawn `SP_Plaza_Start` (64,300). Hotspots (all inside the walk band y 270/276–352): `exit_archive`,
`exp_pz_tram_stop`, `exp_pz_window`, `exp_pz_family_door`, `exp_pz_poster`, `exp_pz_loudspeaker`, `exp_pz_children`,
`exp_pz_guard`, `exp_pz_barrier`, `exp_pz_tribune` (x 1000: hall + tribune centred on screen), `exp_pz_banner`,
`exp_pz_vendor`, `exp_pz_photographer`, `exp_pz_tank`, `exp_pz_rubble`; `hotspot_info` gives a marker point and a
description of the visible object for each. Lights: 2 street lamps, neighbours' window, vendor brazier, lot fire
barrel (warm focals), 3 cold flood masts, tribune floods.

## Insignia (§12.4) and tone
Neutral base files show the fictional Reichssiegel (black disc, white pillar) or a plain eagle; `_hist` twins show
the historical banners / wreathed eagle. The lantern figure is a plain eagle on the globe in both modes. Troops are
anonymous (helmet shadow over the eyes), the crowd is seen from behind, no salutes, no fanfare in the audio.

## Palette
All colour pixels are `berlin` palette entries plus the project's story-accent red ramp (`sepia.red`:
#4A1712 #7A2A26 #A8382E #C8503C), used only for historical banner cloth and the wax seal; binary alpha everywhere
(checked by `env_plaza.py`).

## Text
`data/locale/de_env_plaza.json`: area name, time of day, short names of the 15 spots (`env.plaza.*`).
