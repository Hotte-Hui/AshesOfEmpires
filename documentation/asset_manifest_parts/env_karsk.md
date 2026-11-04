# Asset manifest part — env_karsk (scene A1 "Verladebahnhof Karsk")

* **Date:** 2026-11-04 (round 2: detail, life, exploration objects, insignia switch)
* **Area owner:** env_karsk / karsk-env (environment art + ambient actors for `L_A1_Railyard`)
* **Generators (all deterministic, no network, original work):**
  * Art: `py -3 -P tools/pixelgen/env_karsk.py` (`--no-preview` skips the review renders, `--docs` also rebuilds
    the inspect documents of round 1). Modules: `env_karsk.py` (orchestrator: layers, props, `_hist` twins,
    actor sprites, scene.json, locale), `env_karsk_lib.py` (palette access, pixel fonts, figures,
    shading helpers), `env_karsk_bg.py` (sky + parallax planes), `env_karsk_yard.py` (back-line buildings, ground,
    props, foreground frame), `env_karsk_life.py` (round-2 surfaces, exploration objects), `env_karsk_emblems.py`
    (hand-pixelled emblems), `env_karsk_sprites.py` (actor frame strips), `env_karsk_fx.py` (animated strips),
    `env_karsk_docs.py` (inspect-UI documents, round 1), `env_karsk_preview.py` (review composites).
    Built on `tools/pixelgen/pg.py` (unchanged).
  * Sound: `py -3 -P tools/audiogen/karsk_env_sfx.py` (uses `dsp.py`, `instruments.py`, `foley.py` read-only).
* **Determinism:** fixed integer seeds / `zlib.crc32` of names, never `hash()`. Verified 2026-11-04: SHA-1 of all
  art outputs (PNGs + scene.json) and all 9 WAVs identical after regeneration.
* **Licence / provenance (every file below):** original procedural pixel art and synthesised audio created for
  ASHES OF EMPIRES: THE LAST WINTER by the env_karsk generators (AI-authored code, project-owned, same licence as
  the game). No third-party images, fonts, textures, samples or recordings. The reference images in
  `documentation/references/` were never sampled, traced or embedded.
  Palette: `karsk` from `pg.PALETTES` + the shared C-17 red ramp `pg.PALETTES['sepia']['red']` (C-17 stamp,
  signal lamp, crane warning light, a scarf, the mitten, the cache cloth, medallion/poster red). Palette check on
  every colour PNG (layers, props, actors, fx): **OK**, no off-palette pixel.
* **Fictional content:** town "Karsk", slogan "ВОССТАНОВИМ ВМЕСТЕ" ("we rebuild together"), signs КАРСК / ЧАЙ /
  КВАС / КОНТОРА / ДЕПО / СКЛАД 2, stencils, numbers. The teaching board (УЧЕБНЫЙ) is a disconnected fictional
  training device.
* **Insignia (TECHNICAL_ARCHITECTURE §12.4):** the base files show a *fictional gear-and-wheat emblem*; the
  `*_hist.png` twins (identical except the emblem pixels) show the real Soviet **hammer & sickle**, hand-pixelled
  at 11/9/7/5 px (`env_karsk_emblems.py`). Placements — all in-world iconography of the Soviet state inside the
  critical narrative, never UI/reward: both ends of the civic banner, the medallion of the КОНТОРА sign, the red
  header of the reconstruction poster, an old weathered stencil on the C-17 wagon door, the masthead of the
  newspaper on the bench.

## Art manifest
| Path | Content |
|---|---|
| `assets/environments/karsk_railyard/scene.json` | §3.1 manifest: 10 layers, 16 y-sorted props (base_y + collision), walkable band, camera bounds, spawns, 25 hotspots (8 canonical + the 17 §12.2 `exp_*` names) with `hotspot_info` (mark, radius, hidden, description), 6 lights, 23 fx (snow, 18 anim strips, 4 fog bands), **17 actors** (§12.2), notes. |

## Layers (`assets/environments/karsk_railyard/`, `<name>.png` + `_n` normal map where lit, `_e` emission where listed)
| File | Parallax / z | Content (round-2 changes in **bold**) |
|---|---|---|
| `sky.png` | 0.0 / -100 | Dawn gradient, hazy low sun, haze bars. Unlit. |
| `clouds.png` + `_n` | 0.03 / -96 | Stratocumulus banks, altocumulus, sunlit stratus. Unlit. |
| `far_city.png` + `_n` + `_e` | 0.12 / -90 | Slab districts, radio mast, old quarter, **two cooling towers grouped (both visible together from camera ~800, exp_cooling_towers)**, chimneys, dim lit windows. |
| `far_industry.png` + `_n` | 0.25 / -84 | Saw-tooth halls, stacks, gasholder, power plant, water tank. |
| `mid.png` + `_n` + `_e` | 0.45 / -74 | Grain elevator (exp_grain), railway water tower, tower crane + new block, damaged factory facade, **far railway embankment (rail at world y 210) for the KarskTrain**. |
| `near_bg.png` + `_n` + **`_e`** | 0.72 / -60 | Barrack (exp_barrack) **with the laundry now an actor**, sheds, depot ДЕПО, house under repair, slab block; **four dim lamp-lit windows (2 barrack, 2 slab block) for KarskWindowLife 'small'**. |
| `poles.png` + `_n` + `_e` | 0.86 / -50 | Telegraph poles, wires, distant crows, birches, home-signal mast (red lamp). |
| `yard_back.png` + `_n` + `_e`, **`yard_back_hist.png` + `_hist_n` + `_hist_e`** | 1.0 / -14 | Back line: fences, tea stall ЧАЙ, signal box (ONE amber window), relay hut, freight canopy, hoarding with the **emblem banner (hist: hammer & sickle)** and **reconstruction poster with emblem header**, office КОНТОРА with **emblem medallion sign** and **bookshelf window (exp_kontora_shelf)**, buffer stop; **icicles on every eave, rust run-off (horn bracket, relay hut, canopy bolts, chimney, buffer), drifts against walls, coal heap + shovel, PA cable to the loudspeaker pole (crows' perch), cache under the stairs (exp_stairs_under: loose bricks, oilcloth bundle)**. |
| `ground.png` + `_n` + `_e` | 1.0 / -16 | Back strip, tracks, platform; **footprint trails (boots, child round the snowman, cat, crow), sled runners, frozen puddles with cracks, chopped sleeper blocks + ash by the barrel, coal grit**. |
| `fg_frame.png` | 1.3 / 60 | Wreck truck, fence fragments, dead grass, bare tree. |

## Props (`props/`, all with `_n`; `_e` / `_hist` where listed)
| File | Placement (base_y) | Content |
|---|---|---|
| `wagon_c17.png`, **`wagon_c17_hist.png`** (+ `_n`) | x 730, track 1 (297) | Covered wagon 24-311, lead seal; **weathered state stencil on the door; chalk tallies, an arrow and a crossed-out mark at the far end (exp_wagon_chalk)**. |
| `bench.png`, **`bench_hist.png`** (+ `_n`) | x 549 (320) | Bench **with a newspaper left behind (exp_newspaper): masthead emblem (5 px), official stamp**. |
| **`crates_a.png`** | x 1414 (306) | **Two crate stacks with a dark gap; a tin box at the back of the gap (exp_stash, hidden, KarskGlint)**. |
| **`loudspeaker_pole.png`** | x 722 (255) | **Tarred PA pole, cross-arm, two horn loudspeakers, junction box, enamel plate, icicles (exp_loudspeaker)**. |
| **`snowman.png`** | x 350 (339) | **Child-built snowman, coal eyes, twig nose/arms, tin-can "ushanka" with cardboard flaps (exp_snowman)**. |
| **`sled.png`** | x 318 (334) | **Wooden sled with a checked bundle tied on**. |
| **`dwarf_signal.png`** + `_e` | x 1100 (262) | **Dwarf shunting signal beside track 2, moon-white lamp lit (emissive), blue lamp dark**. |
| `lamp_post_1/3.png` + `_e`, `lamp_post_2.png` (**no `_e`**: its bulb glow is the KarskLamp actor) | x 205 / 700 / 1185 | Platform lamps. |
| `fire_barrel.png` + `_e`, `flatcar_panels.png`, `timetable_board.png`, `teaching_board.png`, `family_bundles.png`, `crates_b.png` | unchanged | Round-1 props (barrel workers = exp_workers, timetable, signal board, family). |

## Insignia switch
Only the three files above carry an emblem; their `*_hist.png` twins (with `_hist_n` / `_hist_e` maps) are picked by
`LayerStack` through `Symbols.pick` when "historical_symbols" is on (applied at scene load, like every other
level). No decals are needed. Verified with in-engine captures at `--symbols=0` and `--symbols=1`.

## Actor sprites (`actors/`) and actor scenes (`scenes/levels/karsk/*.tscn`, scripts `scripts/levels/karsk/*.gd`)
All actors share `karsk_actor.gd`: background actors use LayerStack's parallax grid rule (locked to their layer in
the high-resolution world path) and every opaque sprite gets render-camera's texel material (`texel_light.gd`).
| Sprite strip(s) | Actor scene | Behaviour |
|---|---|---|
| `crows.png` + `_n` (11 × 14×12: idle, breathe, look, caw, preen, hop, take-off, 3 wing frames, glide) | `KarskCrows` | Four hooded crows on the PA cable: idle acting; nervous within 80 px (turn, hop, caw); fly off one by one within 34 px or when the player runs; return after 22–40 s (exp_crows). |
| `cat.png` + `_n` + `_e` (7 × 18×11) | `KarskCat` | Ginger cat curled by the barrel: breathing; lifts its head (fire-lit eyes) within 46 px, blinks / ear / tail; settles again (exp_cat). |
| `train_loco.png` + `_e`, `train_wag_{box,tank,flat,gond}.png`, `train_puff.png` (8 × 18²) | `KarskTrain` | Goods train (loco + tender + 6–9 wagons) on the mid-plane embankment (parallax 0.45) every ~40–50 s, alternating direction, lingering smoke plume; first one enters the view ~4 s after arrival (exp_distant_train). |
| `laundry_{sheet,shirt,towel,johns,apron,cloth}.png` + `_n` (4 sway frames each) | `KarskLaundry` | Barrack laundry (parallax 0.72): gentle phase-shifted sway, flutters in gusts. |
| `window_signalman.png` (7 × 24²) | `KarskWindowLife` (cabin) | The signalman's silhouette in the amber window: sits, drinks tea, crosses, bends over the desk. |
| `window_near_{0..3}.png` (4 × 7×11 / 9×11) | `KarskWindowLife` (small, parallax 0.72) | Somebody at a lit background window now and then, or a curtain drawn. |
| `glint.png` + `_e` (5 × 5²), `cache_cloth.png` (4 × 7×5), `mitten.png` + `_n` (4 × 9×10) | `KarskGlint` | Stash glint every 4–7.5 s (exp_stash); red cloth corner under the stairs flutters only in gusts (exp_stairs_under); the lost mitten on the fence post leans in gusts (exp_mitten). |
| `lamp_bulb.png` + `_e` | `KarskLamp` | Tired platform lamp 2 with its own light: stutters every 6–15 s, sometimes drops out ~1 s (≤ 3 transitions/s; reduced motion: dips ≥ 70 %). |
| `breath_puff.png` (6 × 6²), `fx/barrel_flames.png` + `_e` (**8 × 18×20, redrawn as one merged licking fire**) | `KarskBarrel`, `KarskBreath` | Flames + sparks (more in gusts) + the workers' breath, y-sorted with the barrel; breath of the family and the tea vendor. |
| — | `KarskWind` | Gusts every 9–20 s: spindrift along the ground and off the roof edges, shared `gust` value for laundry / mitten / cloth / sparks. |
| new fx strip `fx/samovar_steam.png` (6 × 14×26) | scene.json fx | Steam over the samovar in the tea-stall hatch. |

## Sounds (`assets/audio/sfx/`, 44.1 kHz / 16-bit, stereo, one-shots; generator `tools/audiogen/karsk_env_sfx.py`)
| File | Length / peak | Content | Used by |
|---|---|---|---|
| `karsk_crow_caw_1..3.wav` | 1.1–1.9 s / -9 dBFS | Hooded-crow "kraa" calls (1–3), nasal harmonic tone + rasp, short yard ambience | KarskCrows (`Audio.sfx("karsk_crow_caw")`) |
| `karsk_crow_flap.wav` | 2.1 s / -10 dBFS | Three crows taking off: wing whumps + feather rustle | KarskCrows |
| `karsk_cat_mrrp.wav` | 0.5 s / -14 dBFS | Soft rising trill | KarskCat |
| `karsk_train_far.wav` | 21.8 s / -10 dBFS | Distant goods train: rumble swell, chuffs, rail-joint clacks, far two-tone whistle | KarskTrain |
| `karsk_wind_gust_1..2.wav` | 4.4 s / -11 dBFS | Gust whoosh (one with a faint whistle) | KarskWind (`Audio.sfx("karsk_wind_gust")`) |
| `karsk_lamp_buzz.wav` | 0.7 s / -16 dBFS | Mains buzz stutter + relay tick | KarskLamp |

## Inspect-UI documents (round 1, unchanged; `assets/ui/documents/karsk_*`) and locale
Unchanged this round (rebuild only with `--docs`). `data/locale/de_env_karsk.json`: `obs.karsk.{stove,poster,family}.*`
and `doc.karsk.*` reading-mode strings (11). The texts of all exploration finds belong to karsk-explore.

## Review renders (not shipped; `.gdignore`)
`assets/environments/karsk_railyard/_preview/`: unlit composites `world_cam0000/0640/1280.png` and the scroll-stitched
panorama. In-engine verification captures are kept outside the project. Visual probe for the actors:
`tests/visual/karsk_life_probe.tscn` (+ `karsk_probe_cam.gd`) — walks a stand-in player past the crows and the cat,
forces a gust and a glint, saves frames to `--out=` (no saves, no autoplay).
