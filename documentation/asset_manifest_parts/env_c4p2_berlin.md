# Asset manifest part -- env_c4p2_berlin (Chapter 4 part 2, Konrad's Berlin: the Ostbahnhof and Kolonnenstraße 14, L_C4P2_Berlin)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_c4p2_berlin.py` drives `env_c4p2_berlin_station.py` (scene A), `env_c4p2_berlin_yard.py` (scene B),
`env_c4p2_berlin_strips.py` + `env_c4p2_berlin_life.py` (life strips, steam, snow, smoke), `env_c4p2_berlin_crowd.py`
(walker rigs), `env_c4p2_berlin_docs.py` (inspect documents); helpers `env_c4p2_berlin_kit.py`,
`env_c4p2_berlin_layout.py`; read-only: `pg.py`, the tone-space painter / light bake / fonts of
`env_veltrava_hall_kit.py`, the painters of `env_c3p2_archive_kit.py`, the insignia drawings of
`env_berlin_insignia.py` / `env_karsk_emblems.py`, the character pipeline through `walkers_r8.build_rig`, the
shared-folder rules of `env_keep.py`).  No pixels were copied, traced, sampled, downloaded or AI-generated; no
third-party assets, fonts or textures are embedded.  References (photographs of Berlin courtyards, station halls,
DR rolling stock) were used for study only.

* Licence / rights: project-owned original artwork, freely redistributable with the game.  Provenance: deterministic
  generator (a re-run reproduces every file byte for byte, scene.json included), re-run with
  `py -3 -P tools/pixelgen/env_c4p2_berlin.py [--preview=DIR] [--no-docs]`, then the shared, locked `--import`.
  Machine-readable list: `assets/environments/berlin_c4p2/provenance.json` (154 rows).  The generator follows
  `env_keep.py`: it removes only its own previously recorded PNGs, merges scene.json (the explore stream's keys and any
  foreign `actors` stay) and provenance.json; `explore_hotspots.json` (exploration stream) is never touched.
* Date: 2026-11-06 (round 10).  Owner: env-berlin stream (C4P2_DESIGN §10).
* Level script: `scripts/levels/c4p2/berlin_c4p2_level.gd` (root `script` line of `L_C4P2_Berlin.tscn`; extends the
  round-9 two-places script `annex_level.gd`: scene filter, camera zones, after / until / choice gates, looks) plus the
  footsteps of the place (concrete under the glass roof, snow in the courtyard) and `look()` = station | courtyard.
  Actor `scenes/levels/c4p2/C4P2StationClock.tscn` (`scripts/levels/c4p2/station_clock.gd`): the platform clock's
  hands at 20.31 when the level opens -- the minute hand jumps, the red second hand rests at the top.  Capture
  harness `scripts/levels/c4p2/berlin_shots.tscn` (`--as-shots`, `--as-done`, like the annex harness).

## Palettes (proposal for data/chapters/c4p2.json -- the story stream's ramps are kept colour for colour)
* `palettes.ostbahnhof` + **`wood`** `#2A1B12 #43291A #5E3B24 #7C5233` (buffet, kiosk, benches, the painted board)
  · **`brick`** `#2B1A15 #3F261D #573527 #714734` (the hall's far wall) · **`enamel`** `#101C34 #1C2E52 #2E4878` (the
  departure board, the K signs, the sleeping car) · **`cream`** `#E9DFC4 #F6F0DE` (tablecloths, enamel letters, the
  clock dial) -- 53 colours in all.
* `palettes.courtyard` + **`dusk`** `#1C2433 #273248 #36435C #4A5874 #63718C` (night-blue plaster and snow in shadow)
  · **`wood`** (as above: doors, window frames, Kuhnert's box) · **`green`** `#1B2E28 #28423A #3A5B4F` (the stair
  door, the pump) -- 50 colours.
* Every layer, patch, strip and document is palette-pure in its place's palette (`tests/test_c4p2_berlin_art.gd`;
  scene.json `meta.palette_ostbahnhof` / `meta.palette_courtyard`).  Until the ramps are in c4p2.json the grade's
  palette snap (strength 0.5) pulls the proposed colours half-way to the placeholder ramps -- it still reads.

## Scene A -- Ostbahnhof, Korridorbahnsteig K (L_C4P2_BerlinA, Monday 17.2.1964, 20.30, x 0..918)
* `station.png` (+ `_n` / `_e`): track K with the D 303 -- the engine 01 064, a Pacific (the big Wagner deflectors
  with their lit edge and handhold, the chimney with a lazy wisp of smoke, the long boiler with a warm rim, polished
  bands, handrail, feed pump, injector, two rounded domes, safety valves and whistle, the red bar frame, cylinder,
  slide bars, crosshead and Walschaerts gear, the leading bogie, three red-spoked drivers with coupling and connecting
  rods, the trailing axle, the cab with its lit window -- the driver -- the plate above the number (neutral „DR“
  monogram / `_hist` Reichsbahn eagle) and the number plate „01 064“): its boiler shows above the buffet's canopy, its
  drivers through the gap between buffet and kiosk (x 338..380, steam from the drain cocks), its cab above the
  kiosk's roof; the tender „DEUTSCHE REICHSBAHN“ with coal and the water filler, the
  two-axle courier van without windows (plates „KURIER / КУРЬЕР“, „C-17“, the sealed sliding door with two lead seals on
  its wire, x ~500), the coaches not yet coupled (buffers, the brake hose, the folded gangway, a shunter's hand lamp)
  and through that gap the next track, the wine-red dining car „SPEISEWAGEN“ (kitchen end with frosted windows and
  chimney, five lit windows with cloths and red-shaded lamps, the destination plate „BERLIN-KARSK“, the open door with
  the first table, a tea glass and the blue guidebook, x ~800), the blue sleeping car „SCHLAFWAGEN“ („KORDON-17“) running
  on behind the Corridor fence; platform K -- the liaison booth at the barrier (two officials at one desk under one
  lamp, „KONTROLLE / КОНТРОЛЬ“, the two plates), the enamel departure board „KORRIDOR OST · BAHNSTEIG K · D 303 BERLIN
  OST 21.10 · KORDON-17 · KARSK · MIT SPEISEWAGEN“ and the painted board for Tuesday („BAHNSTEIG K GESPERRT“ in red on
  a cream strip), the baggage hut „GEPÄCK“ with the decimal scale and a suitcase on it, the buffet „ERFRISCHUNGEN“ (an
  open stand under a green canopy on three posts: the back counter with stacked cups, bottles, the nickel urn and the
  cash box, the menu board „KAFFEE 20 · BRÜHE 25 · WURST 60“ hanging from the canopy, the counter with cups, rolls,
  sugar and a paper), the newspaper kiosk „ZEITUNGEN“ (the headline board „EIN WINTER / DES FRIEDENS“ of the explore
  text, papers clipped at the sides with the same big W in three inks, the „vergriffen“ card on its hook, magazines),
  the porters' carts, a bench with a forgotten paper, six sodium lamps on long rods, the K signs, the Accord's banner
  „DREI KORRIDORE · EIN FRIEDEN“ under the vault, the clock with the plate „ORTSZEIT / KARSK + 2“, the Corridor fence
  (the blocker) with „KEIN / DURCHGANG“ hanging from an iron arm, stone slabs, coping, the white line, melt water and
  blown-in snow at the open end, the timber deck at the platform's end (the hidden ticket stub at 850, 296).
* Parallax: `st_sky` (0.05), `st_city` (0.15, the night city through the open end of the hall and the far windows),
  `st_hall` (0.40: the glass barrel vault under its smoke lantern -- louvres, snow on the ledges, soot fanning down
  the glass --, the great lattice arches every 118 px with gusset plates and cast-iron consoles, their lower chords
  catching the sodium light, purlins in perspective, panes clear / snowed over / sooted / boarded since the war / one
  broken with icicles, cables sagging between the arches, pigeons, two rows of smaller lamps over the far platforms
  with their glow on the glass, the warm band of the vault facing the lamps; the far brick wall „BERLIN OSTBAHNHOF“
  with cornice and arched windows; the end screen with icicles), `st_track2` (0.92, the green windowless car with
  barred hatches and the chalk „DI – KORDON“, one hatch frosted from inside -- exp_green_car), `fg_station` (1.25: the
  coping and the stone face of the platform wall with cables on hooks, weep holes, soot and icicles, signal wires on
  their pulleys, the near track with snow-dusted sleepers, the lamps mirrored in the rail heads, joints with
  fishplates, meltwater with the lamps in it, coal, a newspaper, a cigarette packet, a broken bottle, a dwarf signal,
  the stair down to the underpass with lit nosings).
* `props/counter_front.png` -- the buffet counter cut from the layer (y-sorted, base_y 292: the buffet woman stands
  behind it).
* Patches: `roster_l3` / `roster_l74` -- Marta's duty roster (choice `c4d_choose` = name_marta / !name_marta);
  insignia sites `plates_booth` (Reichssiegel + gear-and-wheat / state eagle + hammer and sickle) and `plate_cab`
  (the „DR“ monogram / the Reichsbahn eagle, a plate of its own above the number), each with `_hist` (+ maps).
* Life (`life/`): `booth_officials` (the German railway policeman stamps and rules, the Soviet liaison officer drinks
  from the tea glass in its metal holder), `baggage_clerk`, `sleeping_boy` (exp_corridor_permit: a boy curled on the
  family's suitcase -- cheek on his arm, the knitted cap slipped back, scarf, knees drawn up, one shoe over the edge, a
  wooden engine held to his chest; he breathes, his foot twitches; y-sorted in front of the counter), `kiosk_woman`,
  `loco_crew` (the driver in the cab window: leaning on the sill, looking back along the platform, turning to the fire;
  the firebox glow flickers), `diners` (a couple with wine, a man behind his paper, Ekdahl's empty table with hat, cup
  and scarf, two women talking, an old man with soup, the waiter walking the aisle), `sleeper_passenger`.  Every
  platform strip is clipped to the pixels its own object owns in the layer (the station's owner map), so no figure or
  glow spills onto what stands in front of it.  FX (`fx/`): the safety valve's plume, a wisp from the chimney, steam
  from the drain cocks between the drivers, the kitchen chimney, steam heating leaking at the uncoupled ends and between
  diner and sleeper, the urn, the haze under the vault, snow blown in at the open end.
* People (`crowd/`, `walkers_a.json`, ambient walkers): 13 colour variants of existing characters re-rendered through
  the character pipeline (rigs with their own normal maps; no insignia -- the railway policeman's armband and emblem
  are painted over in his coat colour): a railway policeman walking the buffet, the buffet woman behind her counter,
  the family of the sleeping boy, a man reading the board, two porters by their carts, the sleeping-car conductor, the
  grandmother and her son at the sleeper's door, a railway worker with his coffee, two travellers walking the platform.
  The two porters are two builds: the young one in the long coat (porter), the older one in a short blue work jacket
  and felt boots with the brass badge on his cap (worker_a).
* Reused actors (by path, unchanged): the Veltrava station's pigeons (`StationPigeons`, tugging at a roll between
  buffet and kiosk), breath puffs (`KarskBreath`) for Marta and Ekdahl.

## Scene B -- Kolonnenstraße 14, gate passage and courtyard (L_C4P2_BerlinB, Tuesday 18.2.1964, 22.10, x 918..1920)
* `yard.png` (+ `_n` / `_e`): the courtyard unrolled into one elevation like the house puzzle's cutaway --
  Vorderhaus | Seitenflügel | Hinterhaus -- with the gate passage in the front wing's ground floor (the street door
  open to the night, the red-white barrier of No. 12 with its warning lamp, green-and-cream tiles, the cork board
  with the Blockleitung's notice and the pinned site plan (gate_notice), letterboxes, the residents' board, the front
  wing's stair door, a timer switch, the caged sodium lamp, the keystone „14“, a guard stone; the notice is typed
  „BEKANNT- / MACHUNG“ on two lines, the site plan pinned beside it has four hatched houses, No. 14 ringed in red), the
  façades in night-blue
  render (rusticated ground floor and window hoods on the front wing, a stair tower on the side wing, render repairs,
  fallen plaster with brick, cornices with snow, icicles, downpipes in the inner corners), 60-odd box windows each with
  its own small life (frame paint, drapes / net curtains / blinds, flower boxes under snow, a cat, a bird feeder, jars
  between the panes) -- the lit ones are the households of §2.7 (scene.json `households`); the side wing's green
  stair door „AUFG. B“ (Ilse's frost drawing: a house with all windows lit, exp_ilse_drawing), the briquettes delivered
  today with the shovel and the open iron cellar hatch with a luminous arrow (the white „LSR →“ on the wall), the lodge
  window (Frau Kuhnert, the radio, the wooden card box with one red tab on the sill), the bicycle, a sled, the
  wash-house door „WASCH“, four bins „VH SF HH HH 3“ (fir twigs, a chair leg, newspaper lining), the cast-iron pump
  with its frozen spout, the carpet rack with the plate of house rules and the hopscotch in chalk on the swept setts
  (1 to 5, „HIM…“ running under the new snow), the frozen laundry
  high across the corner (shirts, a stiff sheet, children's stockings in three sizes), Frau Grabowski's basket on a
  washing line from her dark kitchen window, the back wing's hall door four steps up and the cobbler's souterrain
  „SCHUHMACHEREI PIETSCH“ (half-sunk windows, shelves of shoes with name tags, the boot sign), roofs under snow with
  hatches, chimneys, television aerials, the neighbour's firewall „WASCHANSTALT · PLÄTTEREI“.
* Parallax: `yd_sky` (0.03), `yd_dome` (0.08, pos y 0: the Great Hall floodlit far above the roofs -- ribbed dome,
  lantern with the eagle on the globe, the arcaded drum, searchlight beams in the haze -- and four long banners on the
  drum: neutral grey cloth with the fictional Reichssiegel / `_hist` red cloth, white disc, swastika; drum and banners
  stand above the courtyard's ridge), `yd_roofs` (0.30, the roofscape kept low behind the dome, a church spire),
  `fg_yard` (1.25: trodden snow over the setts with footprints and a sledge track, a gully grate, a frozen puddle with
  a lit window in it, a handcart with a sack of briquettes, a crate of milk bottles, a broom and a frozen bucket, the
  railing of a light well, a child's lost mitten, cat tracks).
* Patches (after `c4h_solve_house`, z -48, under the life strips): `stairs_v` / `stairs_s` / `stairs_h` (the three
  stairwells lit -- the sweep went up), `car` (the sweep's car head-on in the doorway: snow on the roof, the windscreen
  with the street lamp in it, chrome grille, bumper, plate, two headlamps with their glare), `headlights` (their light
  on the passage's setts, soft and falling off, the two men's long shadows toward the courtyard), `candle_ws` (the
  candle in the souterrain); insignia site `notice_k14` (no emblem / the party eagle above the title, `_hist`).  The
  after-state is baked without the dynamic lights (headlights, candle, stairwells -- scene.json lights do them), so
  each patch differs from the base only where something is painted differently: tight boxes, no seams, none of them
  reaches the notice.
* Life: `v1_schulz`, `v3_lenz`, `s1_mertens`, `s2_pohl`, `s3_ilse` (until c4h_solve_house), `s3_hanna` (after: Hanna
  seen from the front behind the left lower pane -- dark cardigan, rust scarf, the bun lit by her lamp, eyes, nose and
  mouth; she holds the curtain aside and looks down into the courtyard), `se_kuhnert`, `h1_kuehn`, `sweep_men` (after:
  two of the sweep's men in the doorway, rim-lit by the headlights, one smoking), `candle_flame` (after: the flame
  flickers, its glow breathes, Ilse sits by it, her face lit by the flame, looking into it and up at the window),
  `warning_lamp`.  FX: snow in two halves, chimney smoke, the car's exhaust (after).
* Reused actors (by path, unchanged): `KarskCat` (a cat asleep on the lodge's warm sill, it wakes when Konrad comes to
  the card box), `KarskWind` (gusts blow snow off the eaves and the ridge), `KarskBreath` (Kuhnert), `BerlinRadio`
  (dance music, faint, from the lodge; own 3-frame glow `actors/radio_glow.png`).

## Documents (`assets/ui/documents/`, metadata `berlin_c4p2_documents.json`, alt texts `data/locale/de_env_berlin_c4p2.json`)
`berlin_c4p2_departures` (ev_c4_departures_east), `berlin_c4p2_seals` + `_hist` (ev_c4_courier_seals: the German seal
a plain disc „DR“ / an eagle, the Soviet seal a wheel / a star, both „C-17“; the green car's barred hatch and the
chalk), `berlin_c4p2_tracing` (ev_c4_konrad_tracing: the 1938 guidebook -- original design, no publisher -- at page
212, the card half upside down, the tracing of Kordon-17 -- „SCHALTER“ under the counter, „‹TÜR WEST“ / „TÜR OST›“
beside their doors, „BANK FÜR 14“ -- and its folded corner „MOROZOV – 0417 / DI 23.40 – TÜR OST“),
`berlin_c4p2_house_notice` + `_hist` (ev_c4_house_notice; on the site plan every house number 12..18 sits on a clear
label, No. 14 ringed in red pencil), `berlin_c4p2_house_cards` (ev_c4_house_cards: six cards and the cobbler's slip).
Drawn 1:1, shown at 3x; the story-critical lines are legible 3x5 capitals (the kit adds the en dash, the middle dot,
Å and a 5-wide W to the shared font -- its 3-wide W read as H).

## Content rules kept
No real person is named in the windows, the cards or the lists; Kordon-17 appears only as words and as Konrad's
drawing; real insignia only in the `_hist` files chosen by `Symbols.pick()` (booth plates, cab plate, dome banners,
the notice, two documents); the two apparatuses stay distinct (the Soviet liaison officer and the German railway
policeman share one desk -- shown, not equated); the Accord's slogan hangs as the regime's own banner.

## Review round 10 (art director) -- what was fixed
* **Sweep's men cut at the chest (high):** the after-patches now lie under the life strips (z -48 < -47); the
  headlights patch is split into `car` (the doorway) and `headlights` (the setts, y 288+), so the men stand whole, in
  front of the car, rim-lit, with their shadows on the floor.  Test: `strips_over_patches_and_insignia`.
* **„KORDON-1“:** the sleeper's plate is sized from its words and moved clear of the fence's bars („KORDON-17“).
* **Near-black vault and foreground bands:** the vault rebuilt with form (lantern, arches, lit chords, lamps, glow);
  both foregrounds painted as places (platform wall + near track / courtyard snow with things left out).  Measured on
  the captures: station top 24 -> 36 (std 14 -> 22), station bottom 13 -> 34 (std 7 -> 28), courtyard bottom
  10 -> 66 (std 3.5 -> 17).  Test: `no_empty_dark_bands`.
* **Engine 01 064 unreadable:** the buffet is an open stand with a lower canopy, the kiosk narrower and lower; the
  drivers and rods show in the gap, the boiler above the canopy, the cab, the eagle / DR plate and the number plate
  above the kiosk.  The old cab strip painted the firebox glow over the kiosk (the „blank peach rectangle“) and the
  neutral DR over the eagle: the platform strips are now clipped by the station's owner map, and the kit's TLayer
  clears the glow flag of every pixel painted over (a hidden glow no longer shows through).
* **The candle never flickered:** strips above patches; the candle moved off the window's bar; Ilse sits by it.
* **No working dome variant:** the banners hang on the drum above the courtyard's ridge (the far roofs kept low
  behind the dome); neutral Reichssiegel vs historical swastika banners.  Test: `dome_banners_above_the_ridge`.
* **Cab plate overlap:** a plate of its own above the number; nothing drawn over it.
* **The car / the beam:** a dark saloon head-on with glare instead of a pale box; the beam as light on the setts.
* **Blocks and twins:** the sleeping boy redrawn, the older porter another build, Hanna a readable frontal figure.
* **Clipped text:** clock plate on two lines, „KEIN DURCHGANG“ whole and readable from the platform, the kiosk headline
  of the explore text, „КУРЬЕР“ inside its plate, the 5-wide W („WASCH“, „WURST“, „TÜR WEST“), the menu one line
  per row above Marta's roster, the tracing's labels apart, the site plan's numbers on labels, the notice's title
  on two lines beside the plan, the dustbin „HH 3“, the hopscotch in bright chalk.
* Captures: both scenes at all camera stops with `--symbols=0` and `=1`, and after `c4h_solve_house`
  (`scripts/levels/c4p2/berlin_shots.tscn`); `documentation/screenshots/c4p2_berlin_contact.png`,
  `c4p2_berlin_documents.png`.
