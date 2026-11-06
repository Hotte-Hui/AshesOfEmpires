# Asset manifest — Chapter 3 part 2 exploration: registry and quay finds, „Die Pforte“, „Die Suchkartei“ (area: explore_c3p2)

Owner: exploration c3p2 specialist · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: documentation/C3P2_DESIGN.md §7,
TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9 (user request this round: Chapter 3 part 2, content, look, feel, fun).

Everything listed here is **original work**, written for this game or generated procedurally by the project scripts
below on 2026-11-06. No pixel, sample or melody was taken from `documentation/references/` or any other source; no
downloads, no AI media, no recordings. Colours come from `data/chapters/c3.json` palette `registry` (night, slate, oak,
lamp_green, paper, brass, snow, red) plus one documented extra: the violet office ink of the Russian clerks' cards
(`VIOLET` #3E2C5E / #5C4488 / #8068B0 in the generator). Pixel fonts: the hand-made bitmaps of
`tools/pixelgen/mg_r7_v_kit.py` (SMALL 5×7, Latin + Cyrillic) and `tools/pixelgen/env_veltrava_lib.py` (FONT_S 3×5,
Latin + Cyrillic) — no font file is read or traced. No regime insignia anywhere (§12.4): the tracing index is the
neutral commission's, its drawer carries only „SUCHKARTEI“. Historical model: 1950s/60s office card-index cabinets
(oak drawers, brass label holders, card rods, guide cards with coloured tabs) and Soviet office practice of violet ink.
Licence: original project work (same terms as the rest of the game).

## Content (text, data)

| File | What |
|---|---|
| `data/explore/c3p2_registry.json` | 18 registry entries (level key `L_C3_RegistryA`): Alexei, scene A — gate sign, two tracks (secret), handcart, coal hatch 1909, his own index card („Begleitperson“, card `hist.soviet.filtration`), the side task „Die Pforte“ (thermos → radio + ten-Kronen note → key board → the porter's note); Konrad, scene B — fire bucket, his own card („Anfrage Berlin“, card `hist.reich.census_1939`), rolling ladder, stamps and seal pliers „Zange 7“, the tracing index (mini-game), boots at the window, plan chests (Blatt 7 missing), Kesselhaus 1909 plaque, cassation list („Serie C-17 … erledigt“) |
| `data/explore/c3p2_quay.json` | 10 quay entries (Alexei): two soot hands (secret), the ladder engine (Storz/Bogdanov adapter), lantern, ice, searchlights, two cars and one lighter, the bridge of the city arms; chats with Frau Brunner, Lidia Voronova, Nils Ekdahl |
| `data/explore/c3p2_history_reich.json`, `c3p2_history_soviet.json` | the two real-history cards with their sources (fact-checked 06.11.2026, ≥ 2 independent web sources each + literature) |
| `data/locale/de_explore_c3p2.json`, `de_history_c3p2.json` | all German texts (finds, chats, task, mini-game, place labels; the two cards) |
| `assets/environments/veltrava_registry/explore_hotspots.json`, `veltrava_quay/explore_hotspots.json` | the exp_* hotspots (shared, append-only blocks) |

## Mini-game „Die Suchkartei“ (`scenes/ui/minigames/Kartei.tscn`)

| Asset | Generator | What |
|---|---|---|
| `assets/ui/minigames/kartei/kartei_back.png` (400×136) | `py -3 -P tools/pixelgen/gen_mg_c3p2_kartei.py` | the card-hall floor at night (oak parquet, the green lamp's pool, cold edges) with the fallen drawer: back wall, dark inner bottom, side walls, shadow |
| `kartei_front.png` (400×136) | same | the drawer's front panel drawn over the cards: brass label holder „SUCHKARTEI“, cup handle, rod nut |
| `kartei_tabs.png` (15 × 22×36) | same | guide cards „B·Б“, „K·К“, „V·В“ (pressboard, coloured tabs) and the upper part of the twelve cards (origin letter, year/number, handwriting) |
| `kartei_faces.png` (9 × 46×30) | same | the nine floor cards in full: code as written, origin in the card's script, handwriting, result stamp |
| `kartei_closeup.png` (200×120) | same | close-up for the find (DiscoveryView): the drawer in order, Teodor Wanek's card („Anschrift übermittelt“) on top |
| `world_drawer.png` (2 × 34×12) | same | world cue in L_C3_Registry beside drawer C-17: the fallen drawer with scattered cards / empty |
| `kartei_layout.json` | same | canvas, slots, cells, atlas order, floor spots; the rule itself is `scripts/ui/minigames/kartei_logic.gd` |
| `assets/audio/sfx/mg_c3p2_card_take.wav` | `py -3 -P tools/audiogen/mg_audio_c3p2.py` | a card lifted off the parquet (paper flick + slide), 0.22 s |
| `mg_c3p2_card_file.wav` | same | a card slipped between its neighbours, the soft tick on the rod, 0.3 s |
| `mg_c3p2_rattle.wav` | same | a refused card: the drawer jolts, the cards rattle once, the rod rings quietly, 0.45 s |
| `mg_c3p2_drawer_shut.wav` | same | the drawer slid home: rumble on the runners, a muffled knock, 0.75 s |

Scripts (no assets): `scripts/ui/minigames/kartei_game.gd` (modal, extends `minigame_base.gd`: auto mode, `demo_solve()`
by synthetic keys, hints after two refusals following Settings `puzzle_hints`, Esc puts a held card back or gives up,
keyboard + pad + mouse, compact ×2 layout above 100 % text, high-contrast cursor), `kartei_logic.gd` (pure rule),
`kartei_spot.gd` (registry find spot: Story gates in the game, the remembered scene in memories), `kartei_world_cue.gd`.
Deterministic: seeds are crc32 of names; re-running the generators reproduces the files byte for byte.
