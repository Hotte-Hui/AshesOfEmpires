# Asset manifest part -- env_c4_tunnels (Chapter 4 part 1, Alexei's Karsk: Archivkeller, Dienststollen 3, Umsetzgleis, L_C4_Tunnels)

All files below are **original works generated procedurally** by the scripts in `tools/pixelgen/`
(`env_c4_tunnels.py` drives `env_c4_tunnels_room.py` (cellar, door wall, floors), `env_c4_tunnels_siding.py`
(earth section, tunnel, siding hall, wagon 24 318), `env_c4_tunnels_fx.py` (outside, veils, strips, swing lamps,
event strips); `env_c4_tunnels_docs.py` (inspect documents); helpers `env_c4_tunnels_kit.py`,
`env_c4_tunnels_layout.py`, and -- read-only -- `pg.py`, the tone-space painter / light bake / bitmap fonts of
`env_veltrava_hall_kit.py`, the masonry / wood painters of `env_c3p2_archive_kit.py` and the hand-pixelled emblem
masks of `env_karsk_emblems.py`).  No pixels were copied, traced, sampled, downloaded or AI-generated; no third-party
assets, fonts or textures are embedded.  References (Soviet two-axle covered wagons, 1941 air-raid shelters, lever
frames, freight-office ledgers) were studied only, never copied.

* Licence / rights: project-owned original artwork, freely redistributable with the game.  Provenance: deterministic
  generators (two consecutive runs reproduce all 72 files byte-for-byte, checked 2026-11-06); re-run with
  `py -3 -P tools/pixelgen/env_c4_tunnels.py [--preview=DIR]` and `py -3 -P tools/pixelgen/env_c4_tunnels_docs.py`,
  then the shared `--import`.  Machine-readable list: `assets/environments/karsk_tunnels/provenance.json` (62 files).
* Date: 2026-11-06 (round 9).  Owner: env-tunnels stream.
* Palette `tunnels` = data/chapters/c4.json `palettes.tunnels` (night, brick, iron, lamp, wagon, paper, snow, red,
  skin -- kept unchanged) plus two ramps taken from Chapter 1's Karsk palette so Karsk stays one city:
  **`green`** `#1B3033 #26403F #36534D #4A675C #6C7A62 #9DAF91` (oil-paint dado, Lev's lamp shade, the iron door) and
  **`concrete`** `#2A2D2C #3B3F3B #4F534C #666A60 #7F8275 #9A9B8B` (the 1941 tube, the siding hall).  Every room layer,
  patch and document is palette-pure in it (`tests/test_c4_tunnels_art.gd`); scene.json `meta.palette_ramps` lists it.

| Path (assets/environments/karsk_tunnels/ unless noted) | Content |
|---|---|
| `room.png` (+ `_n`, `_e`) | the whole level, baked once (1920 x 360): **Archivkeller** (scene A, ~4.40) -- four brick barrel vaults on lunettes, two barred windows, the stair from the office (door ajar, warm), the freight-book shelves 1963 / 1964 / АРХИВ with the January gap and Lev's slip, stamp rack, card cabinet, wall clock (4.40), 1964 calendar, railway schematic „СХЕМА / КАРСК“, Lev's desk (green lamp, open January book, abacus, photo, tea), samovar table, the light box made of a signal lamp, the stove with felt boots, the 1941 iron door with „Бомбоубежище · Служебный тоннель №3“; the **door wall** in section; **Dienststollen 3** (scene C) -- earth section with the freight yard above, concrete tube, cage lamps, old and new cables, heating pipe with the leaking flange, phone niche, „← К укрытию“, lever frame (8 levers, diagram board) and point „СТР 2“, the sealed gallery „ЗАКРЫТО“, boards with a scratched house; the **Umsetzgleis** -- vaulted hall, the siding office „ДЕЖУРНЫЙ“ with the card box „C-17/45 / ПРИНЯТЬ“ and the stamp, the painters' crate and roster post, the paint stand (C-17/41 … /45, two alphabets, the bucket), fire shield, plate heap, wagon 24 318 (C-17/45 stencil still taped over 47 702 over the ghost of C-17/42, enamel plate 24 318, chalk „ВТ 23.40“, marks „РЕВ 11.62 / ДЕП КАРСК“), the kit pile, the brazier, the shut portal with padlock and dawn in the cracks |
| `patches/plan_taken`, `door_open`, `wagon_open` (+ maps) | opaque crops of a bake with one story change: the tunnel plan handed over (after `c4a_talk_tunnel`), the iron door open (after `c4a_open_door`), the wagon door slid open (after `c4c_inspect_wagon`) |
| `patches/insignia_calendar`, `insignia_lever_plate`, `insignia_wagon` (+ `_hist`, maps) | the three insignia sites: fictional gear-and-wheat emblem of Chapter 1 / hammer and sickle in the `_hist` twin (TECHNICAL_ARCHITECTURE §12.4, Symbols.pick) |
| `outside.png` | the yard at night behind the cellar windows (snow at the glass, the yard lamp, a wagon) |
| `veils.png` | soft light cones (bulb over the wagon, work lamps, the enamel lamp, Lev's lamp) and the faint paint haze |
| `fg_frame.png` | dark foreground silhouettes, parallax 1.25 (crates, sack, cable drum, buffer stop, sleepers) |
| `fx/snow_win_0/1`, `feet_win`, `samovar_steam`, `stove_vents` (+`_e`), `clock_pendulum`, `dust_lamp`, `dust_hang` | life of scene A: snow behind the windows, the night shift's felt boots passing, steam, the fire breathing, the pendulum, dust in the lamplight |
| `fx/drip_0..4`, `steam_flange`, `booth_smoke`, `kerosene_flame` (+`_e`), `dust_bulb`, `dust_work`, `brazier_embers` (+`_e`), `snow_gate` | life of scene C: drops falling into puddles, steam at the flange, smoke from the booth's pipe, the kerosene flame, dust in the bulb and work-lamp light, embers, snow blown under the gate |
| `fx/hang_lamp`, `fx/bulb_wagon` (+`_e`) | 7-frame swing strips of the two hanging lamps (driven by the level script) |
| `fx/dust_fall_0..7`, `fx/train_top` | event strips: grit shaken from the vault, the underframes of a train crossing the yard above |
| `scene.json`, `provenance.json` | art manifest (story contract kept: spawns, hotspots, npcs, the blocker `cellar_door`) + file list |
| `assets/ui/documents/karsk_tunnels_book_gap`, `_freight_book`, `_carbon`, `_plan`, `_tracks`, `_card_ru`, `_stencils`, `_wagon_inside` (.png) + `karsk_tunnels_documents.json` | inspect close-ups of the eight Karsk items of C4_DESIGN §2.5 (weighbill style, legible only the story figures; the card's perforation contract pitch 6 / hole 3 / first 8 px / 15 holes is shared with the German half) |
| `data/locale/de_env_karsk_tunnels.json` | German caption lines (alt texts) of the eight documents |

Code and tests of this stream (hand-written): `scripts/levels/c4/tunnels_level.gd` (extends the registry level:
scene filters, camera zones, looks, swinging lamps, the passing train), the root script line of
`scenes/levels/L_C4_Tunnels.tscn`, `tests/test_c4_tunnels_art.gd`, `tests/visual/c4_tunnels_shots.gd` / `.tscn`,
screenshots `documentation/screenshots/c4_tunnels_*.png` (captures of the real renderer + the contact sheet).
