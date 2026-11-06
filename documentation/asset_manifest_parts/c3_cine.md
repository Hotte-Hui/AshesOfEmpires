# Asset manifest part — c3_cine (Chapter-3 cinematics LS_C3_Trains, LS_C3_ToHall, LS_C3_Close)

* **Date:** 2026-11-05/06 (finishes the c3-cine work started in the cloud session of 2026-11-04/05)
* **Area owner:** cinematics stream (C3_DESIGN.md §2.9, §7)
* **Scenes / code:** `scenes/cinematics/ch3_trains/` (`Ch3Trains.tscn`, `ch3_trains.gd`), `ch3_tohall/`, `ch3_close/`,
  shared `ch3_common/` (`c3_cinematic.gd` = the §12.5 contract: `finished` exactly once, idempotent `skip()`,
  `configure(ctx)` picks the inner lines from the story flags, `seek()`/`advance()` for tools and tests, cue list for
  subtitles/sound/loops, reduced motion; `pixel_fx.gd` = deterministic snow and 1 px Bresenham wires/hands;
  `c3_dissolve*.gdshader` = ordered-dither dissolve, one Bayer cell per world pixel). Registered in
  `data/chapters/c3.json` → `cinematics`, played by `ChapterExt.play_cinematic()`.
* **Generators:** `py -3 -P tools/pixelgen/env_veltrava_cine.py [--only trains,tohall,close]` writes every texture and
  `assets/cinematics/ch3/layout.json` (anchors shared with the runtimes; `tests/test_c3_cinematics.gd` checks the
  match-cut geometry, the clock centre and the platform projection against it). Modules:
  `env_veltrava_cine.py` (trains interiors + exterior + flare, build/main), `env_veltrava_cine_dawn.py` (t4),
  `env_veltrava_cine_tohall.py`, `env_veltrava_cine_close.py`, `env_veltrava_cine_kit.py` (fonts via
  `env_veltrava_lib`, rings, dial indices, dithered puffs), `env_veltrava_cine_figs.py` (the two protagonists).
  Sound: `py -3 -P tools/audiogen/c3_cine_audio.py` → `assets/audio/sfx/c3cine_*.wav`.
* **Figures:** Konrad and Alexei at the compartment windows (from behind), their faces in the black glass and
  Konrad's profile are sculpted and lit with the signed-distance pipeline of the dialogue portraits
  (`chargen_portrait2_anat/_cast/_paint/_sdf`, imported read-only, nothing there modified): the specs `konrad()` /
  `alexei()` supply heads, hats, hair and coat materials, so the cinematic figures follow the portraits. Renders are
  memoised on disk (`%TEMP%/ashes_c3cine_cache`, keyed by the pipeline sources + arguments, results byte-identical;
  `ASHES_NO_CACHE=1` disables it).
* **Determinism:** fixed seeds everywhere (`np.random.default_rng(n)`, `zlib.crc32(name)` for audio); two full builds
  are byte-identical (checked with md5 over all PNG/WAV outputs).
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio made for ASHES OF
  EMPIRES: THE LAST WINTER by these generators (AI-authored code, project-owned, same licence as the game). No
  downloaded, copied or traced images, fonts or samples. No real insignia anywhere in these cinematics (pennants and
  flags are plain), so there are no `_hist` variants.
* **Palettes:** `veltrava` and `palais` ramps of `data/chapters/c3.json` (registered by `env_veltrava_lib`) plus the
  protagonists' material ramps of the portrait pipeline; grade `c3_cine` (no palette snap, light vignette and grain).

## Art — `assets/cinematics/ch3/trains/` (LS_C3_Trains, 25.5 s)
| File | Use |
|---|---|
| `ext_sky`, `ext_far_de`, `ext_far_su`, `ext_mid`, `ext_near` | the night plain behind the glass: overcast sky lit from the Line, the floodlit double fence with masts and watchtowers (seen from the west / from the east), the snow plain with birches and a cleared farm, the embankment streaks; tileable 640 px strips scrolled per layer |
| `pole` | telegraph pole with crossarms and insulators (the runtime strings the sagging wires between poles) |
| `int_konrad`, `fig_konrad` (4 frames: 2 head poses × breath), `refl_konrad`, `glow_lamp`, `patch_warm` | the German delegation's saloon car: mahogany panels, velvet curtains, the drafting tube on the rack, the reading lamp, the coffee cup with Konrad's hand on it; Konrad from behind; his lamp-lit face and the lamp mirrored in the glass; the light thrown onto the snow outside |
| `int_alexei`, `fig_alexei` (4 frames), `refl_alexei`, `glow_tea`, `steam_tea` (6), `spoon` (2), `patch_cold` | the Soviet compartment: laminate walls, upper berths, the wall lamp, the tea glass in its holder with Alexei's hand at the handle, the spoon that tips with every rail joint, frost in the glass corners |
| `sweep`, `flare`, `roomflare_k`, `roomflare_a` | the floodlit level crossing of the match cut (light band, the glass flooded, the room and the sitter's rim lit); `roomflare_*` also carries the weak flash of the passing lineside lamp |
| `bridge_bg`, `bridge_fg`, `dawn_glow`, `fg_glow` | dawn over Veltrava: castle hill, cathedral, the patinated palais dome, onion church, town hall; the three-arch stone bridge (the commission's arms) with its lanterns; the half-frozen river with ice sheets, floes, cracks and the dawn in the open channel; the near bank promenade with fence, bench and a bare willow |
| `train_de`, `train_su` (2 frames: pennants) | Konrad's train (grey-blue saloon cars, a salon car, pennants, engine running east) and Alexei's (green carriages, the sealed courier wagon 4 at its tail, engine running west) |
| `smoke` (8 frames) | steam puffs (2×2 block dither), used for both plumes and the town's chimneys |
| `walker` (6 frames) | a woman in a red-brown headscarf pulling a sled with a milk can along the bank |

## Art — `assets/cinematics/ch3/tohall/` (LS_C3_ToHall, 6 s)
| File | Use |
|---|---|
| `k1_bg`, `k1_clock`, `k1_glass`, `steam_puffs` (4) | the cast-iron platform clock under the glazed canopy (lattice girder, frosted panes with drifted snow, fretwork valance), the green carriage and the misty old town beyond; the crystal's glare (additive); drifting steam |
| `k2_bg`, `k2_clock`, `k2_glass`, `pendulum` (8) | the gilded Jugendstil clock of the palais on its verde-antico panel between marble pilasters, the same dial geometry and index angles as the station clock (the match cut), its lyre pendulum |
| `k2_konrad` (2 frames) | Konrad's silhouette walking in under the clock (warm chandelier rim, cold window rim, the drafting tube) |
Hands are drawn at runtime (1 px Bresenham) from the shown time 9:39:57 → 9:40:00.

## Art — `assets/cinematics/ch3/close/` (LS_C3_Close, 12 s)
| File | Use |
|---|---|
| `n1_bg`, `n1_mid`, `n1_fg`, `board` (4 frames), `steam` (4) | platform 5 at 23:40 in one-point perspective (the pinhole `proj` the runtime uses to draw the departing special train as shrinking polygons): canopy, columns, lamps mirrored in the wet snow, the dual-gauge track, a goods train on the next track, the yard and the city at the vanishing point; the platform sign „5“ and a small clock at 23:40; the split-flap indicator (trilingual header) whose row clears after the departure |
| `n2_bg`, `n2_win_konrad` (3), `n2_win_alexei` (3), `n2_lamp_glow` | the station square at night: Hotel Europa (mansard, balconies) and Hotel Nord (flat roof), snow on every ledge, the street into the old town with the palais dome, the lime trees and a parked car with someone smoking in it (runtime ember); the two lit windows where Konrad and Alexei step to the glass and turn toward the whistle |

## Sound — `assets/audio/sfx/` (`tools/audiogen/c3_cine_audio.py`, 44.1 kHz / 16-bit stereo)
| File | Content |
|---|---|
| `c3cine_ride_de.wav` (9.6 s) | the saloon car at night: rumble through the floor, padded rail joints (ta-tam every 1.55 s, in sync with the picture), wind at the glass, the panelling creaking |
| `c3cine_ride_su.wav` (9.4 s) | the Soviet car: harder joints every 1.8 s, loose fittings rattling, the spoon clinking in the tea glass on every knock |
| `c3cine_pass.wav` (1.2 s) | a lineside lamp post rushing past |
| `c3cine_crossing.wav` (2.4 s) | the level crossing at speed: its bell swells and drops in pitch, the rush of air |
| `c3cine_bridge.wav` (8.5 s) | two engines on the stone bridge at dawn: exhaust beats from both sides slowing, the hollow rumble of the arches, wheel clatter, the river valley echo |
| `c3cine_whistle_de.wav` (3.0 s) | Konrad's engine answering across the river, lower than the Karsk whistle |
| `c3cine_clock_tick.wav`, `c3cine_clock_clack.wav` | the seconds of the platform clock and the minute hand jumping to 9:40 |
| `c3cine_palais_chime.wav` (3.0 s) | one soft strike of the palais clock's gong spring |
| `c3cine_step_marble_1..3.wav` | leather heels on the marble of the foyer |
| `c3cine_depart_night.wav` (6.5 s) | the special train pulling out without a whistle: cylinder hiss, couplings snatching, heavy beats receding |
| `c3cine_flaps.wav` (1.0 s) | the split-flap indicator clearing its row |
Re-used (unchanged): `cine_a1m1_whistle_far` (the Karsk whistle — heard again from Alexei's engine at dawn and as
the one whistle over the night square: „Derselbe Pfiff“), `wind_gust`, `amb_veltrava_station`, `amb_veltrava_palais`,
`amb_transition`, `mus_veltrava` (starts at dawn and carries on into the station level).

## Checks
`tests/test_c3_cinematics.gd` (17 cases): registration, contract (`finished` once for skip/skip, skip before play,
natural end then skip, coarse fast-forward, replay), line variants for every flag combination, subtitles spoken in
order and localised, no cues after skip, reduced motion (no knocks, no roll), shot order, every texture and every cue
sound present, layout sync (glass/exterior box, clock centre, projection, runtime anchors), rail joints of the picture
== joints cut into the bed sounds, the dawn dissolve completes. Visual review: `tests/visual/c3cine_harness.tscn`
(`--c3-mode=shots|seq|run`).
