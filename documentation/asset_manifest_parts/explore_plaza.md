# Asset manifest part -- explore_plaza (exploration on the plaza before the Great Hall during the parade, Konrad)

All files below are **original works** made for this project.  Close-ups are generated procedurally by
`tools/pixelgen/explore_plaza.py`, which reuses (read-only) the close-up toolkit of `tools/pixelgen/explore_berlin.py`
(tone-space Canvas, masks, 3x5/5x7 bitmap fonts, fictional Reichssiegel, eagle and swastika bitmaps) and the
shared `pg.py` (palettes, Bayer dither, noise).  Nothing was copied, traced or sampled from
`documentation/references/` or any other source; no third-party assets, fonts or textures.  All German text was
written for this project.

* Licence / rights: project-owned original work, freely redistributable with the game.
* Provenance: deterministic generator (seeds = crc32 of `plaza.<name>`; re-running gives byte-identical files):
  `py -3 -P tools/pixelgen/explore_plaza.py [--preview DIR] [names...]`.
* Date: 2026-11-05.  Size: 240 x 150 px each, pixel art 1:1, shown x3 by the DiscoveryView (TECHNICAL_ARCHITECTURE
  12.1).  No normal/emission maps (UI images).
* Palettes: the Berlin close-up ramps of explore_berlin.py (`berlin` snow/stone/steel/violet/patina/glow, `sepia`
  greys and red, `archive` paper/ink/wood/blue/amber, `green`, `graphite`); the generator reports any colour
  outside them (none).  Light: the parade evening of `hall_plaza` (snow clouds, searchlight shafts of the
  Lichtdom, lamp-lit walls), warm accents only at the brazier, the fire barrel and the lit window.
* Insignia (TECHNICAL_ARCHITECTURE 12.4): neutral file = fictional Reichssiegel; `*_hist.png` = real historical
  insignia, chosen at runtime by `Symbols.pick()` (`--symbols=0|1`).  Only in-world regime iconography inside the
  critical narrative (the parade poster, the facade banners, the office stamp on the eviction order); never UI,
  rewards or the player's side.  Like env's `banner_near`, the neutral banners are slate grey, `_hist` red.

| File (`assets/explore/plaza/`) | Find (`data/explore/plaza.json`) | Content |
|---|---|---|
| `tram_stop.png` | plaza.tram_stop | stop disc, closed route 74, typed notice "Sonderfahrten für Umsiedler … Güterbahnhof West" |
| `poster.png` / `poster_hist.png` | plaza.poster | parade poster on the Litfass column: dome silhouette, emblem (neutral / historical), programme, rubbed-out pencil house number |
| `vendor.png` | plaza.vendor (easter egg) | chestnut drum on a brazier, chalkboard "Kinder mit roter Nase 20 Pf", cone folded from an old city map |
| `loudspeaker.png` | plaza.loudspeaker | three-horn loudspeaker mast with snow caps, cables, crows, banner edge |
| `barrier.png` | plaza.barrier | red-white trestle barrier, chain, sign "Neuordnungsbezirk – Aufstellung nach Hausnummern", residents behind |
| `tank.png` | plaza.tank | parked tank in the cleared courtyard: snow on the hull, track, bent carpet-beating bar, crew's fire barrel |
| `tribune.png` | plaza.tribune | stepped stone tribune with slate drapes, guests in fur collars, dome in the haze, the barrier chain in front |
| `banner.png` / `banner_hist.png` | plaza.banner | 20 m banners (neutral: slate + Reichssiegel / historical: red + swastika disc), empty flat with a gathered curtain |
| `rubble.png` | plaza.rubble | fire wall with the ghost of floors, stairs and wallpapers; rubble: blue-rose wallpaper, green stove tile, nameless bell plate, blue-white "OST" cloth badge |
| `family_door.png` / `family_door_hist.png` | plaza.family_door | door of No. 9 with two laths, seal strip with red wax, enamel number, eviction order; office stamp (neutral Reichssiegel / historical eagle) |
| `window.png` | plaza.window | lit third-floor window, the neighbour drawing the curtain, a covered plate left on the sill |

Content files (same owner): `scenes/levels/L_M1_Plaza.tscn`, `data/explore/plaza.json` (13 finds + 2 chats; NPCs berlin_mother/father/child at `exp_pz_neighbour`),
`data/locale/de_explore_plaza.json`, `assets/environments/hall_plaza/explore_hotspots.json`,
`tests/test_explore_plaza.gd`.  History links (existing cards only): tribune → `hist.reich.germania`,
family_door → `hist.reich.evictions`, tram_stop → `hist.reich.reichsbahn`, rubble → `hist.reich.forced_labor`.
The fiction never quotes the real deportation sites (e.g. no "Gleis 17"): the real history stays on the cards.
