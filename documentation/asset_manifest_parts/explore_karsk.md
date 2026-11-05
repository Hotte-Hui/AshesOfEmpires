# Asset manifest part — explore_karsk (exploration content of the Karsk railyard, Alexei's chapter)

All files below are **original works** made for this project. The close-ups are generated procedurally by
`tools/pixelgen/explore_karsk.py` on top of the shared, read-only `tools/pixelgen/pg.py` (palettes, Bayer dither,
value noise, `Layer`). The small Cyrillic bitmap fonts (5×7, 3×5), the hammer-and-sickle masks and the fictional
gear-and-wheat emblem are defined in that module. No pixels were copied, traced or sampled from
`documentation/references/` or any other source; no third-party images, fonts or textures are embedded. All German
text was written for this project.

* **Date:** 2026-11-04 · **Area owner:** karsk-explore
* **Licence / rights:** project-owned original work (AI-authored code and text), same licence as the game.
* **Provenance:** deterministic generator, seeds = crc32 of the image/part names:
  `py -3 -P tools/pixelgen/explore_karsk.py` (writes `assets/explore/karsk/*.png`);
  `--preview` additionally writes ×3 review sheets to the folder in the environment variable
  `EXPLORE_KARSK_PREVIEW` (never into the project). Verified: two runs produce byte-identical files (SHA-1).
* **Format:** 16 files, 256×160 px RGBA (opaque), pixel art 1:1, shown ×3 by the DiscoveryView (TECHNICAL_ARCHITECTURE §12.1,
  limit 320×200). No normal/emission maps: the close-ups are UI images, not lit world sprites.
* **Palette:** `karsk` ramps of `pg.PALETTES` (night, teal, sage, sky, stone, rust, copper, snow, wood) plus the
  shared C-17 red ramp `pg.PALETTES['sepia']['red']` (banner cloth, mitten, rag, ink). The generator aborts on any
  off-palette pixel. 25–40 colours per image, ordered dither only along band edges.
* **Light:** follows the scene's key lights (ART_DIRECTION §5): low dawn from the back right (warm rims on right
  edges), cold sky ambient, local warm sources (fire barrel, office lamp, signal-box window).
* **Insignia (§12.4):** `newspaper.png` / `banner.png` carry the fictional gear-and-wheat emblem; their twins
  `newspaper_hist.png` / `banner_hist.png` show the hammer and sickle (real Soviet state insignia, same layout as the
  Karsk environment's emblems). Twins differ only in the emblem pixels (banner: the two end emblems, rows 41–76;
  newspaper: the masthead emblem). Loaders resolve the path through `Symbols.pick()` (setting `historical_symbols`,
  CLI `--symbols=0|1`); `Explore.entry_image()` and the DiscoveryView already do. Shown only as in-world iconography
  of the Soviet state inside the critical narrative — never in UI chrome, rewards or as player decoration.
* **Content:** all in-world texts stay inside the fictional 1964 and Alexei's voice; the eight real-history cards
  (`hist.soviet.*`, §12.3) are written by the history specialists and only referenced by id.

## Close-ups (`assets/explore/karsk/`)
| File | Find (entry id) | Content |
|---|---|---|
| `barrack.png` | `karsk.barrack` | Clapboard wall of the two-storey barrack: door, paler rectangle with four rusty screw holes where the "Sonderkontingent" sign hung, frosted window with a tin plate and a stovepipe (elbow, cap, smoke). |
| `cat.png` | `karsk.cat` | Ginger tabby "Pjatiletka" curled on a scrap of sacking beside the fire barrel (glowing holes, flames), head raised with half-open eyes; the workers' coats and felt boots at the frame edges; firelight on the snow. |
| `stairs_under.png` | `karsk.stairs_under` | Under the signal-box stair: treads seen from below, three loose bricks pulled from the foundation, opened oilcloth bundle with a red rag, pegged travel chess mid-game, score sheet. |
| `loudspeaker.png` | `karsk.loudspeaker` | Timber PA mast with crossarm, junction box, cables and two flared horn loudspeakers; snow, icicles, rust tears. |
| `newspaper.png` | `karsk.newspaper` | Page 3 of the fictional local paper "КАРСКАЯ ПРАВДА" on the bench slats: masthead with the gear-and-wheat emblem, page number, headline, the halftone "commission" photo (men in coats among trees), columns, the round "ДЕПО" library stamp, wet margin, folded corner. |
| `newspaper_hist.png` | `karsk.newspaper` | Same with the hammer and sickle in the masthead. |
| `wagon_chalk.png` | `karsk.wagon_chalk` | Oxide-red boards of wagon 24-311 with steel straps and rivets: chipped stencil, layers of chalk tallies, ticks, arrows, a circled 20, a crossed-out number, and at the bottom, almost washed away, "40 ЧЕЛ.". |
| `grain.png` | `karsk.grain` | The grain elevator: five concrete silos with a patched shell hole and rust tears, head house and gallery, loading chute into a hopper wagon stencilled "КОРИДОР 3", spilled grain and sparrows on the track bed. |
| `snowman.png` | `karsk.snowman` | Two-ball kids' snowman with a tin-can "ushanka" (bent tin ear flaps), coal eyes, a hex-bolt nose, nut buttons, one stick arm saluting; wooden sled beside, small footprints around. |
| `banner.png` | `karsk.banner` | Red cloth banner on the timber hoarding: fresh cream "ВОССТАНОВИМ ВМЕСТЕ" following the folds, gear-and-wheat emblems at both ends, the older slogan "СЛАВА ТОВ." shimmering through, the name after it painted out with darker brushwork; nails, snow on the hem. |
| `banner_hist.png` | `karsk.banner` | Same with the hammer and sickle at both ends. |
| `stash.png` | `karsk.stash` | Top-down: lifted slab, rusty tin box and its lid; inside a round-cut X-ray film with grooves, a ghostly ribcage and a burnt centre hole ("music on ribs"), white wax-pencil scrawl. |
| `kontora_shelf.png` | `karsk.kontora_shelf` | Freight-office shelf of year binders 1934–1948 with the 1939 binder missing: dust outline, darker shadow, the "1939" label still glued to the shelf edge; stamp, ink pad, boxes; warm lamp light. |
| `crows.png` | `karsk.crows` | Three hooded crows (grey mantles, black hoods and wings) on the snowy PA cable next to the timber mast; one looks straight at the viewer, one preens; far yard silhouettes in the haze. |
| `cooling_towers.png` | `karsk.cooling_towers` | Two hyperboloid cooling towers in the dawn haze with drifting steam, a chimney, a power line and a barbed-wire fence in the snowy foreground. |
| `mitten.png` | `karsk.mitten` | A child's red knitted mitten (pale snowflake band, ribbed cuff, thumb) pushed onto a concrete fence post, snow cap, chain-link fence and yard silhouettes behind. |

## Data, text and level wiring (same owner)
| Path | Content |
|---|---|
| `data/explore/karsk.json` | 20 entries: 17 discover (11 details, 3 secrets, 3 easter eggs; 14 with a close-up) + 3 chats (tea vendor, workers at the barrel, grandmother and grandchild); 8 link the §12.3 Soviet history cards. |
| `data/locale/de_explore_karsk.json` | 83 German strings (`explore.karsk.*`): titles, prompts, Alexei's notes, 23 chat lines. |
| `assets/environments/karsk_railyard/explore_hotspots.json` | Content-owned hotspots `exp_wreck`, `exp_family`, `exp_flatcar` (the §12.2 `exp_*` names come from karsk-env's scene.json). |
| `scenes/levels/L_A1_Railyard.tscn` | 20 exploration Interactables (`discover`/`chat`) + NPCs `Vendor` (char `vendor`, at the tea stall) and `WorkerB` (char `worker_b`, walking the back strip by the canopy); all story nodes unchanged. |
| `tests/test_explore_karsk.gd` | Headless consistency test (run by `tests/run_all.gd`). |
| `tests/visual/karsk_explore_shots.tscn` (+ `.gd`) | Windowed harness: prompts, DiscoveryView pages and chat lines in the real game, PNGs to `--kx-out`. |
