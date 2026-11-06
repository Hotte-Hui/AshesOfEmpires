# Asset manifest — env-karsk, round 10 (Chapter 4 part 2: L_C4P2_Karsk, the Karsk locomotive depot)

Area owner: env-karsk specialist · Date: **2026-11-06, round 10** · Engine target: Godot 4.7.2 ·
Contract: `documentation/C4P2_DESIGN.md` §4.1 (art ↔ content), §2.5 (documents), §6 (the explore stream's
`explore_hotspots.json` `info` = the art contract of every find).

## Provenance & licence
Everything here is original project work, made by the project's own deterministic Python generators (numpy /
Pillow / stdlib; fixed seeds, no network). No samples, no third-party art, no traced or AI-generated pixels; the
bitmap fonts are hand-defined (`env_veltrava_hall_kit.py`, `env_c4_tunnels_kit.py`, `env_c4p2_karsk_kit.py`).
Project-owned, no attribution needed. No real person is named or depicted; the eleven names of the work list are
illegible on purpose; the guidebook has no real publisher. Real insignia exist only as `*_hist` variants
(`Symbols.pick()`, TECHNICAL_ARCHITECTURE §12.4); neutral = the fictional gear-and-wheat emblem of Chapter 1.

## Reproduce
```bash
# run the generators UNDER the worktree's import lock: an import that scans the folder while the generator
# rewrites it marks the half-written PNGs valid=false and never retries them (seen once this round; fix: delete the
# stale *.png.import sidecars and import again)
until mkdir .import_lock 2>/dev/null; do sleep 3; done
py -3 -P tools/pixelgen/env_c4p2_karsk.py [--preview=DIR]   # the level art (≈ 15 s, byte-identical re-runs)
py -3 -P tools/pixelgen/env_c4p2_karsk_docs.py              # the six inspect documents + their alt texts
"$GODOT" --headless --path . --import > /dev/null 2>&1; rmdir .import_lock
godot --path . res://tests/visual/c4p2_karsk_shots.tscn -- --scene=L_C4P2_KarskA --char=alexei \
      --capture=<dir>/boot.png --frames=100000 --ts-out=<dir> --ts-cams=0,238 [--ts-done=…] [--symbols=0]
```
The generator follows the round-10 shared-folder rules (`tools/pixelgen/env_keep.py`): it removes only the PNGs
its own previous run recorded, merges its `scene.json` over the old one (foreign keys and `actors` stay) and keeps
other generators' provenance rows; `explore_hotspots.json` (explore stream) is never touched.

## Generators (tools/pixelgen/)
| File | What |
|---|---|
| `env_c4p2_karsk.py` | assembly: the two bakes, story patches, insignia sites, backgrounds, veils, foreground, life strips, fx, actor sprites, `scene.json`, `provenance.json`, a parallax-correct preview composer |
| `env_c4p2_karsk_kit.py` | palette `DEPOT` (c4p2.json `palettes.depot` + the ramps of this stream, incl. `skyglow` and `violet` of the review pass), tone ramps, light hue tables, fonts (Cyrillic incl. a 5-px Д, Å, the 5×7 slogan font; „4“ in its open form so it never reads as „Ч“; overhang tables: „Й“ with its breve and the distinct umlauts one row above the cap line), painters (brick, planks, snow caps, icicles, windows, coal heaps, ground, signs) |
| `env_c4p2_karsk_layout.py` | every coordinate: the story contract (hotspots, spawns, NPC anchors, blocker, camera zones) and the art placement |
| `env_c4p2_karsk_yard.py` | scene A, Monday 6.10 dawn: yard lamp, sleepers, fire board, Irina's dispatch office (lit window, the carbon on the sill, the duty roster, the padded door), the canteen's back (hatch, kasha pot, radio), the water crane (straw lagging, brazier), the coal stage (gondola, deck, chutes, strut with Lena's mitten, the stair, the list post), the special run's tender (chalk „ВТ“), the floodlight mast, the ash pit, the fire barrel (a full drum with two rows of glowing air holes, the snow melted back into wet cinders round it), the roundhouse back (stall door ajar, smoke hoods, the patched banner „ВОССТАНОВИМ ВМЕСТЕ“ in the 5×7 font with its sacking only at the ends and in the word gap, the back door with the press notice, the emblem disc on the parapet between two smoke hoods), the tarpaulin's back (patches, sack, mirrored letters, a child's chalk train) |
| `env_c4p2_karsk_show.py` | scene B, Tuesday evening: the tarpaulin's painted front (the coal stage and its mast over it), the restored colour-light signal (green aspect, bows, rust foot with „А. М.“, the lineman's wire box), the roundhouse front with the polished engine head-on (wreath, ribbons, emblem, brass plate „1939“, white-rimmed wheels), the band stage under a string of bulbs, the press canteen cut open (white cloth, tea glasses, bread with red and black caviar, the guidebook, the samovar, the curtain and, inside its right wall, the tiled kitchen corner with the range and the band's kasha), the turntable (running wheels; the cabin with the empty stool, the operator's cap on the controller), the sand-drying house cut open (limewash worn through in a few broad places, a grey-green dado, soot over the sand stove, round sieves, the red fire board, „НЕ КУРИТЬ“, the wall phone, coats on hooks, the platform sack scale and sacks, the cat's sand heap, Lev's bench under the green lamp), a lattice floodlight mast behind it, the gate with an iron bracket carrying the sign and the two clocks (19.10 / „КОР. ВРЕМЯ“ 17.10), platform 1 under the same trodden snow as the yard (swept and wet where people stand), the canopy, the westbound Corridor express with its lettering on the letterboard ABOVE the windows (route board „БЕРЛИН – КАРСК“, „СПАЛЬНЫЙ ВАГОН 07“, „ВАГОН-РЕСТОРАН“) |
| `env_c4p2_karsk_far.py` | parallax backgrounds per scene: sky (dawn decks with rose undersides / evening: a lit town's night, dark blue-grey up high, the sodium skyglow under the low cloud, the cloud decks lighter than the gaps), the town of Karsk (blocks of flats with snow on the roofs, works chimneys whose smoke catches the town's light, water tower, crane, a radio mast with red lamps, warm haze; in B the station with its clock tower and its lit name „КАРСК“), the embankment (telegraph line, birches, far signal box) / the station side |
| `env_c4p2_karsk_people.py` | the figure rig in tone space (joints, garments, head patterns per headgear, rim/outline pass, baked in the scene's light at the figure's world position), the shovelling cycle |
| `env_c4p2_karsk_life.py` | the life strips of both scenes (below) |
| `env_c4p2_karsk_fx.py` | fx strips, light veils, actor sprites (sparrows, dog, breath, barrel flames, the far goods train) |
| `env_c4p2_karsk_docs.py` | the six documents, `karsk_c4p2_documents.json`, `data/locale/de_env_karsk_c4p2.json` |

## Files — `assets/environments/karsk_c4p2/` (163 generated files; full list with one line each in `provenance.json`)
| File(s) | What |
|---|---|
| `depot_a.png` (+ `_n`, `_e`) | scene A baked in its light (x 0–904): dawn, sodium floods, windows, fire |
| `depot_b.png` (+ `_n`, `_e`) | scene B baked in its light (x 856–1920): evening floodlight, canteen, platform lamps |
| `sky_a/b`, `town_a/b` (+ `_e`), `line_a/b` (+ `_e`) | parallax 0.10 / 0.30 / 0.55 backgrounds, sized to each scene's camera range |
| `veils_a/b.png` | light cones of the floods and lamps in the haze (unlit, plain alpha) |
| `fg_a/b.png` | foreground snowbanks and silhouettes below y 318 (parallax 1.25) |
| `patches/order_taken`, `book_taken`, `halves_on_bench`, `card_joined` (+ maps) | story states (gated after / until objectives) |
| `patches/insignia_roundhouse_back`, `insignia_roundhouse_front`, `insignia_engine` (+ `_hist`, maps) | insignia sites, neutral + historical |
| `life/*.png` (+ `_n`, some `_e`) | 38 life strips: A — Kolonne 4 (`k4_gondola_0/1`, `k4_bar`, `k4_stair`, `k4_shovel_a/b`, `k4_barrow`, `k4_old`, `k4_rags`, `k4_bowl`), the cook seen through the hatch (clipped to the opening, behind the pot), the stoker at the brazier, the fitter in the stall door; B — the band, five different people on one beat (`t0` 0): the turntable man bareheaded with the helicon, a young fitter, a woman from the wagon shop, an older man with a moustache, a tall stoker with the bass drum; two children on the stage edge, the cleaner at the engine, the waitress, the cook at the kitchen range, an old fitter oiling the turntable, a smoker in the sand-house door, a woman sifting sand, the depot cat; on platform 1 as the explore text tells it: the patrol (grey greatcoats, fur hats), a woman holding her permit out to the young militiaman, a man handing a parcel up to a window, two children on a suitcase (the boy eats a pirozhok), the grandmother (side task), the conductor (navy, silver cap band, shirt and tie, lantern; side task), a mother lifting her boy to a window, a couple, the pirozhki seller, the porter (quilted jacket, white apron, badge cap, cart) |
| `fx/*.png` (+ some `_e`) | steam from the stall door, smoke hoods, stove pipes, the canteen vent, the kasha pot, the samovar, the sand-house chimney, the turntable cabin, the heating steam under the express; snow, coal dust in the floods, coal grains from the chutes, barrel sparks, brazier embers, the sand stove's fire door, the shovels and coal dust behind the tarpaulin, the barrel flames |
| `actors/*.png` | `sparrows` (KarskCrows layout), `dog` (+ `_e`, KarskCat layout), `breath_puff`, `train_loco`, `train_wag_box/gond/tank/flat`, `train_puff` |
| `scene.json`, `provenance.json` | the art manifest (registry gates + `scene` filters of `annex_level.gd`, camera zones, looks, actors) and the provenance list |

## Files — elsewhere
| File | What |
|---|---|
| `assets/ui/documents/karsk_c4p2_order.png`, `_work_list`, `_press_notice`, `_guidebook`, `_card_ru`, `_card_whole` + `karsk_c4p2_documents.json` | the inspect close-ups of the six Karsk items of part 2 (shown at ×3) |
| `data/locale/de_env_karsk_c4p2.json` | their German alt texts (`doc.karsk_c4p2_*.alt`) |
| `scenes/levels/c4p2/KarskDepotTrain.tscn` + `scripts/levels/c4p2/karsk_depot_train.gd` | the passing goods train (karsk_train.gd with this level's sprites): every 30–50 s, −8 dB, waits while a film runs |
| `scenes/levels/c4p2/KarskDepotDog.tscn` + `scripts/levels/c4p2/karsk_depot_dog.gd` | the yard dog on the ash pit (karsk_cat.gd behaviour, no purr) |
| `scenes/levels/c4p2/KarskDepotSparrows.tscn` + `scripts/levels/c4p2/karsk_depot_sparrows.gd` | sparrows on the hatch and the cornice (karsk_crows.gd behaviour, no caws, softer wings) |
| `tests/test_c4p2_karsk_art.gd` | the art test (contract, files, places, insignia, palette, people, patches, objects, level, train, documents; review pass: story text readable (no strip, sparrow or NPC over the `readable` rects), the cook inside the hatch, the evening sky not black, no twins in the band and on the platform, the showcase middle populated, the barrel unburied, the emblem above the windows, the train's colours) |
| `tests/visual/c4p2_karsk_shots.gd/.tscn` | capture harness (camera positions, story states, the train: put into the current view at `--ts-train-at`, default the stage/roundhouse gap at camera 238, so the shot is never empty) |
| `documentation/screenshots/c4p2_karsk_*.png` | contact sheet, the four views, story states, insignia neutral vs historical, the documents |

## Round-10 art review (fixes)
Every point of the art director's list is fixed in the generators and re-captured
(`documentation/screenshots/c4p2_karsk_*`): the cook shows only through the hatch (clipped to the opening, the pot in
front; „РАЗДАЧА“ clear; the sparrows perch on top of the board and on the counter); the express lettering runs on the
letterboard above the windows and the canopy columns stand clear of it, so the platform crowd cannot hide it; scene
B's upper picture is a lit town's night (skyglow, lit cloud decks, lit roofs and smoke, warm haze, a floodlight mast,
the station's lit name) -- top 40 % with luma < 25 is 7-9 % in the captures (was 75-78 %; A 23 %); five different band
members with a readable helicon and bass drum, the patrol in grey greatcoats and fur hats apart from the navy
railwaymen; the turntable and the sand-drying house populated before Lev arrives (oiler, smoker, sifting woman, cat),
the limewash worn in a few broad places instead of chips; the fire barrel a full drum clear of the guard and of any
snow bank, its flames three tongues; the gable emblem on the parapet, clear of the window bays; the 3x5 „4“ no longer
equals „Ч“ and „Й“ has its breve (the documents read „НАРЯД № 45/С“, „19.40“, „СПЕЦРЕЙС“, „ШВЕДСКОЙ“, „ЗАДНИЙ“), the
roundhouse banner uses the 5x7 font; the tarpaulin panel is lashed in front of its poles, vendor and porter stand
apart, the gate clocks hang from an iron bracket, platform and yard lie under one trodden snow, the kitchen sits
inside the canteen's wall (no black slab); the far goods train is oxide red / grey / snow with a lit headlamp and red
wheels; the order's carbon is violet as its alt text says. `scene.json` lists the story text under `readable` (rect +
scene) and the test keeps it clear.
