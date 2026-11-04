# Asset manifest part -- explore_berlin (exploration content of the Berliner Bauarchiv, Konrad's chapter)

All files below are **original works** made for this project.  Close-ups are generated procedurally by
`tools/pixelgen/explore_berlin.py` on top of the shared, read-only `pg.py` (palettes, Bayer dither, noise); the
tiny bitmap fonts, the fictional Reichssiegel, the plain eagle and the swastika bitmaps are hand-defined in
that module.  No pixels were copied, traced or sampled from `documentation/references/` or any other source;
no third-party assets, fonts or textures are embedded.  All German text was written for this project.

* Licence / rights: project-owned original work, freely redistributable with the game.
* Provenance: deterministic generator (seeds = crc32 of the asset names; re-running produces byte-identical
  files): `py -3 -P tools/pixelgen/explore_berlin.py [--preview DIR] [names...]`.
* Date: 2026-11-04.  Size: 240 x 150 px each, pixel art 1:1, shown x3 by the DiscoveryView (TECHNICAL_ARCHITECTURE
  12.1).  No normal/emission maps: close-ups are UI images, not lit world sprites.
* Palettes: `archive` (night, wall, wood, amber, paper, blue, ink), `berlin` (steel, snow, violet/night, stone,
  patina, glow), `sepia` (photo tones, red ramp), plus the two archive extras of the Berlin room
  (`green` lamp glass, `graphite` pencil).  The generator rejects any colour outside these ramps.
* Light follows the archive's key lights (ART_DIRECTION 5): cold daylight from the left, warm lamp accents.
* Insignia (TECHNICAL_ARCHITECTURE 12.4): neutral file = fictional Reichssiegel (white obelisk in a black disc);
  `*_hist.png` = the real historical insignia, chosen at runtime by `Symbols.pick()` (setting
  `historical_symbols`, CLI `--symbols=0|1`).  Only in-world regime iconography inside the critical narrative,
  never UI, rewards or player decoration.  The two variants differ only in the insignia pixels.
* The real-history cards these finds unlock (`hist.reich.*`) are written by the history specialists and
  referenced by id only; in-world texts stay inside the fictional 1964.

| File | Content |
|---|---|
| `assets/explore/berlin/master_plan.png` | general plan of the north-south axis behind glass: hall, axis, Spree, Tempelhof, pencil circle "Probekörper 1941", title block with the office stamp (neutral: Reichssiegel) |
| `assets/explore/berlin/master_plan_hist.png` | same, office stamp with eagle and swastika |
| `assets/explore/berlin/poster_aufbau.png` | the AUFBAU 1964 poster (same design as berlin-env's wall decal): dome as cream line drawing on night blue, Reichssiegel above |
| `assets/explore/berlin/poster_aufbau_hist.png` | same, eagle with the wreathed swastika above the dome |
| `assets/explore/berlin/notice.png` | cork board, typed list "Bestandsänderungen Achse Süd", every line "umgesetzt", ends at "Kolonnenstr. 12" |
| `assets/explore/berlin/pneumatic_tube.png` | pneumatic tube station, capsule in the basket, routing slip "zur Aussonderung – Eilt", a pencil heart "17 Uhr?" |
| `assets/explore/berlin/clock.png` | the pendulum regulator by the porter's lodge (brass pendulum, two weights) |
| `assets/explore/berlin/card_catalogue.png` | open catalogue drawer: guide cards C-15/C-16/C-18, the C-17 guide leaning into the gap, "entnommen s. Abt. III" |
| `assets/explore/berlin/reading_table.png` | reading table under a green lamp: request slip "Leser Nr. 114 – Ausweis eingezogen 2.11.", folded spectacles |
| `assets/explore/berlin/globe.png` | 1938 globe with inked borders, pasted-over countries and the red armistice line |
| `assets/explore/berlin/lib_shelf_1.png` | open chronicle 1942: "19. Januar" / "21. Januar", pages 41/42 run on |
| `assets/explore/berlin/lib_shelf_2.png` | row of red Kursbücher with the grey linen dummy "Sonderz. 42–44" standing proud |
| `assets/explore/berlin/lib_shelf_3.png` | atlas page: green settlement land with villages in a grid, grey "freizumachende Fläche", model farm 1:500 |
| `assets/explore/berlin/lib_shelf_4.png` | ward plan "Bettenhaus II, Umbau 1940", 80 beds, red-pencil cross and "ENTFÄLLT" |
| `assets/explore/berlin/lib_shelf_5.png` | Festschrift appendix "Herkunft der Werkstoffe" (Flossenbürg, Mauthausen, Groß-Rosen), photo with the cut-off worker |
| `assets/explore/berlin/lib_hidden.png` | the pushed-in back panel of shelf V, an envelope and Brandt's index card in block letters |
| `assets/explore/berlin/mouse.png` | mouse hole in the skirting board, sign "Zutritt nur für Befugte", "Bewohnerin: Akte", crumbs, thimble |
| `assets/explore/berlin/radio.png` | the porter's radio: lit dial on the line, pencil dot far right, green magic eye |
| `assets/explore/berlin/heater.png` | rib radiator under the reading-room window, two small red mittens drying |
| `assets/explore/berlin/pigeons.png` | five puffed pigeons on the snowy sill at dusk, the dome in the haze, frost on the pane |
| `assets/explore/berlin/photo.png` | the last frame of the department chronicle: group photo before the hall model, one face scratched to white, embossed caption |
| `assets/explore/berlin/coat_stand.png` | bentwood coat stand: Emil's grey coat, two umbrellas, Brandt's dark-green scarf |

Content files of this area (original German text, no external sources):
`data/explore/berlin.json` (20 finds + 3 chats), `data/locale/de_explore_berlin.json`,
`assets/environments/berlin_archive/explore_hotspots.json`, the Interactable/NPC nodes in
`scenes/levels/L_M1_Archive.tscn`, tests `tests/test_explore_berlin.gd`, capture harness
`tests/visual/berlin_explore_shots.gd`.
