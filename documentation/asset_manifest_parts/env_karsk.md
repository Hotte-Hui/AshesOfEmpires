# Asset manifest part — env_karsk (scene A1 "Verladebahnhof Karsk")

* **Date:** 2026-11-04
* **Area owner:** env_karsk (environment art for `L_A1_Railyard`)
* **Generator:** `py -3 -P tools/pixelgen/env_karsk.py` (add `--no-preview` to skip the review renders).
  Modules: `tools/pixelgen/env_karsk.py` (orchestrator, manifest, locale), `env_karsk_lib.py` (palette access,
  pixel fonts, figures, shading helpers), `env_karsk_bg.py` (sky + parallax planes), `env_karsk_yard.py`
  (back-line buildings, ground band, props, foreground frame), `env_karsk_fx.py` (animated strips),
  `env_karsk_docs.py` (inspect-UI documents), `env_karsk_preview.py` (review composites). Built on
  `tools/pixelgen/pg.py` (unchanged).
* **Determinism:** fixed seeds, no network. Verified: SHA-1 of all 66 outputs identical after regeneration.
* **Licence / provenance (all files below):** original procedural pixel art created for ASHES OF EMPIRES:
  THE LAST WINTER by the env_karsk generator (AI-authored code, project-owned, same licence as the game).
  No third-party images, fonts, textures or samples. The reference images in `documentation/references/` were
  viewed only as internal style study (lighting, depth layering); nothing was traced, sampled or embedded.
  Palette: `karsk` from `pg.PALETTES`; the only additional colours are the shared C-17 red accent ramp of
  `pg.PALETTES['sepia']['red']` (C-17 stamp, distant signal lamp, crane warning light, a scarf, a ribbon).
  Palette check (all colour PNGs) passes: no off-palette pixels.
* **Fictional content:** town "Karsk", slogan "ВОССТАНОВИМ ВМЕСТЕ" (civic, "we rebuild together"), signs
  КАРСК / ЧАЙ / КВАС / КОНТОРА / ДЕПО / СКЛАД 2, stencils and numbers are invented. The teaching board
  ("Übungskasten", plate УЧЕБНЫЙ) is a disconnected, unpowered fictional training device; no real signalling
  procedure is depicted. No state insignia are used.

## Art manifest
| Path | Content |
|---|---|
| `assets/environments/karsk_railyard/scene.json` | Art manifest (TECHNICAL_ARCHITECTURE §3.1): 10 layers, 12 y-sorted props with base_y + collision, walkable polygon, camera bounds, spawns, hotspots (+ `hotspot_info`), 7 lights, 19 anim_sprite fx, snow, 4 fog bands. |

## Layers (`assets/environments/karsk_railyard/`, each `<name>.png` + `<name>_n.png` normal map where lit, `<name>_e.png` emission where listed)
| File | Size | Parallax / z | Content |
|---|---|---|---|
| `sky.png` | 648×360 | 0.0 / -100 | Dawn gradient (teal → pale sage), hazy low sun right of centre (screen x 612), haze bars. Unlit. |
| `clouds.png` + `_n` | 709×160 | 0.03 / -96 | Stratocumulus banks with lit undersides (low sun behind-right), thin altocumulus, sunlit stratus streaks. Unlit. |
| `far_city.png` + `_n` + `_e` | 802×112 | 0.12 / -90 | Slab districts, radio mast, old quarter with roofless church drum, cooling towers + chimneys in front of the sun, heavy haze; a few dim lit windows (emission). |
| `far_industry.png` + `_n` | 968×147 | 0.25 / -84 | Saw-tooth halls, stack clusters, gasholder, coke tower + conveyor, power plant, water tank on lattice; haze base. |
| `mid.png` + `_n` + `_e` | 1224×185 | 0.45 / -74 | Grain elevator (5 silos, head house, gallery, shell hole + repair patch), railway water tower, tower crane with panel on the hook + new block under construction, damaged factory facade (window grid, broken/boarded panes, collapsed roof, scaffolding, workers, cloth banner), chimneys, bare trees. Crane warning lamp (emission). |
| `near_bg.png` + `_n` | 1570×113 | 0.72 / -60 | Two-storey barrack with stovepipes through windows + laundry line + woman, sheds, brick locomotive depot with arched gates (one open, smokebox inside, ДЕПО), low warehouse, house under repair with scaffold + workers, 5-storey prefab block, small houses. |
| `poles.png` + `_n` + `_e` | 1749×141 | 0.86 / -50 | Telegraph poles with insulators and sagging wires, crows, bare birches, distant home-signal mast with red lamp (emission). |
| `yard_back.png` + `_n` + `_e` | 1920×136 | 1.0 / -14 | Playfield back line (bases at y 250): concrete diamond-relief fences, tea kiosk ЧАЙ with vendor + samovar, sleeper piles, signal box / dispatcher cabin (brick ground floor, timber operator room, ONE amber window, external stair, nameplate КАРСК, loudspeaker), relay hut, open freight canopy with goods, timber hoarding with the banner ВОССТАНОВИМ ВМЕСТЕ and the reconstruction poster + housing notice, freight office КОНТОРА with counter window, ledger on the shelf and warm enamel lamp (emission), buffer stop. |
| `ground.png` + `_n` + `_e` | 1920×114 | 1.0 / -16 | Walkable band: cinder back strip (250–262), track 2 (rails 264/272), snowy ballast, track 1 (rails 286/294), platform edge stones with worn stripe (297–300), wet concrete platform slabs with repairs, grates, manhole, slush, drifts, puddles mirroring sky; baked warm/cold reflection dashes (emission). |
| `fg_frame.png` | 2312×311 | 1.3 / 60 | Near-black frame: wrecked 1940s truck front at the left edge, low broken fence fragments with barbed wire, dead grass, bare tree at the far right. Unlit. |

## Props (`assets/environments/karsk_railyard/props/`, all with `_n`; `_e` where listed)
| File | Size | Placement (base_y) | Content |
|---|---|---|---|
| `wagon_c17.png` | 200×91 | x 730, track 1 (297) | Two-axle covered goods wagon, patched boards, steel braces, stencil 24-311, chalk marks, sliding door with the dented lead seal (hotspot `seal`). |
| `flatcar_panels.png` | 190×54 | x 1707, track 2 (276) | Flatcar with prefab concrete wall panels (reconstruction material). |
| `fire_barrel.png` + `_e` | 47×46 | x 951 (304) | Fire barrel with two workers warming hands (`obs_stove`); glowing holes/embers emissive. Flames = fx strip. |
| `timetable_board.png` | 40×55 | x 1048 (306) | Fahrplantafel on posts with roof; three pasted slips with tiny square/circle/triangle marks (hotspot `timetable`). |
| `teaching_board.png` | 38×63 | x 1269 (305) | Open steel cabinet on a post: unpowered teaching board, three empty slots, demo diagram, cut cable (hotspot `signal_board`). |
| `family_bundles.png` | 66×43 | x 244 (322) | Mother, child, grandfather on a trunk, cloth bundles, suitcase (`obs_family`). |
| `lamp_post_1/2/3.png` + `_e` | 24×80 each | x 205 / 700 / 1185 | Concrete platform lamp posts with enamel shades, cold bulbs (emission). |
| `crates_a.png`, `crates_b.png` | 34×25 | x 1432 / 640 | Stencilled crate stacks with snow. |
| `bench.png` | 34×14 | x 566 (320) | Platform bench. |

## Animated FX strips (`assets/environments/karsk_railyard/fx/`, horizontal frame strips, seamless loops)
| File | Frames × size | Use |
|---|---|---|
| `smoke_ribbon_a.png`, `smoke_ribbon_b.png` | 8 × 72×132 | Dark industrial smoke ribbons (far industry stacks). |
| `smoke_ribbon_far.png` | 8 × 56×96 | Pale distant smoke (far city / mid chimneys). |
| `tower_plume.png` | 8 × 84×64 | Cooling-tower steam. |
| `chimney_wisp.png` | 8 × 30×60 | Stovepipe smoke (signal box, stall, office, barrack, sheds). |
| `steam_puffs.png` | 6 × 26×44 | Steam puffs (depot lantern, barrel). |
| `barrel_flames.png` + `_e` | 6 × 18×20 | Flame tongues above the fire barrel (emissive). |

## Inspect-UI documents (`assets/ui/documents/`, pixel art 1:1, shown at 3×)
| File | Size | Key marks (rects in `karsk_documents.json`) |
|---|---|---|
| `karsk_seal.png` | 200×140 | Lead seal on the wagon door: doubled stamp "КРС 0412", abraded band revealing **C-17**, scratched **square, circle, triangle** beside it. |
| `karsk_timetable.png` | 300×200 | Worn enamel timetable: three re-booked lines on pasted strips, destinations empty, margin marks **square → circle → triangle** (puzzle order). |
| `karsk_ledger.png` | 320×200 | Freight ledger page, handwriting scribbles; new last line (wagon 24-311) with red **C-17** stamp, recipient blacked out. |
| `karsk_signal_board.png` | 260×180 | Unpowered teaching board: plate УЧЕБНЫЙ, three empty card slots, dead lamp, cut cable, demo diagram using cross/diamond/asterisk (never the solution). |
| `karsk_documents.json` | — | Per document: file, size, item/objective/hotspot ids, title/description/alt locale keys, mark rects. |

## Locale
| File | Content |
|---|---|
| `data/locale/de_env_karsk.json` | `obs.karsk.{stove,poster,family}.{prompt,text}` (Alexei's voice), `doc.karsk.signal_board.title`, `doc.karsk.{seal,timetable,ledger,signal_board}.alt` (reading-mode descriptions). |

## Review renders (not shipped; folder has `.gdignore`)
`assets/environments/karsk_railyard/_preview/`: `world_cam0000/0640/1280*.png` (unlit, 2×, lit approximation),
3× crops, document 3× views, fx contact sheet, normal-map crops, and in-engine captures
(`engine_world_cam*.png`, `engine_full_cam*.png`) taken with the game's `--capture` mode.
