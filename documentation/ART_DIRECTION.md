# ART DIRECTION — ASHES OF EMPIRES: THE LAST WINTER

Status: AUTHORED 2026-11-04 from analysis of the 9 user references (`documentation/references/`, internal
lookdev only — never shipped, never traced) plus the preproduction art brief. Measurements below were taken with
`tools`-independent median-cut analysis (8 colours per image) and run-length pixel-scale estimation.

## 0. The one-sentence look
**Monumental, hand-composed pixel art in cold, hazy industrial air, where every warm light is a deliberate story
beat** — big silhouettes, tiny people, deep blue-green/violet shadows, smoke ribbons, snow and wet ground.

## 1. Reference analysis (what we learn, not what we copy)
| Ref | Content | Native px (est.) | Key lesson |
|---|---|---|---|
| user_ref_1 | Bust portrait, man with glasses, smoke | 200×376 @2× | Portrait lighting: navy/black body (#0B162A, #00070D 62 % of image) with a single acid-ochre key (#4F5E46→yellow). Faces read through 2–3 values only. Basis for dialogue portraits. |
| user_ref_2 | Ruined factory, sage sky, wreck car | 341×210 @2× | Side-on composition, low horizon, sage/olive palette (#83A387 #263A2E #A0BC94 #3E4E3D). Big cumulus with lit tops. Foreground framing object (car at the edge). Overgrown road. |
| user_ref_3/6 | Orange monumental tower, bridge, smoke | 404×317 / 309×667 @2–3× | Monochrome warm grade (#E5945A #735145 #211623): architecture glows from backlight, smoke ribbons in dark olive cross the facade, emblem as graphic focal point, tiny figures and vehicles for scale, dark foreground bridge as a frame. |
| user_ref_4 | Sepia silhouette fight in a metro hall | 600×600 @2× | One-hue value painting (#2A2829…#ACA99F), light shafts as dithered diagonal bands, dust specks. Model for memory/transition shots. |
| user_ref_5 | Propaganda hall with mosaic | 341×470 @2× | Near-symmetry, deep navy (#000F1A 32 %, #13252A 25 %), one warm accent (mosaic), crowd as black heads, small screens/lamps as rim lights. Model for ceremonial interiors (critically framed). |
| user_ref_7 | Burning ruined city, red-eyed figure | 600×336 @2× | Dusty beige haze (#BA9F7F), black silhouettes, fire as the only saturated colour, depth by 4 haze planes. |
| user_ref_8 | Snowy street, dynamic light, wet asphalt | 600×315 @2× | Pixel art + modern dynamic lighting: coloured point lights on characters, specular wet ground reflections, falling snow, fog. Our in-engine lighting target. |
| user_ref_9 | Top-down/oblique city blocks | 250×300 @2× | Oblique architecture with 1 px light edges on roofs, value-sorted greys, green as sparse relief. Map/overview style. |

## 2. Colour palette system
* Every scene uses **one palette file** (`tools/pixelgen/pg.py: PALETTES`) of ≤ 48 colours in ramps.
* Ramps are **hue-shifted**: shadows drift to blue-teal (Karsk) or violet (Berlin); highlights drift to warm ochre.
* Saturation is low everywhere except *story accents*: copper lamp light, fire, the red **C-17** stamp, signal lamps.
* Value structure per frame: 3 value groups (dark frame/foreground, mid architecture, light sky/haze) + accents.
* Palettes:
  * `karsk` — cold dawn: night `#05090F…#13252B`, teal `#122126…#4A675C`, sage `#3E4E3D…#B8C7A8`,
    sky `#6F8576…#DCE2C8`, rust `#2E1C1A…#C98A5C`, copper `#7A3E26…#FBE3AE`, snow, wood, stone.
  * `berlin` — exterior dusk: night/violet `#120C14…#57494D`, stone & ochre terracotta, glow `#E5945A…#FCE9C8`,
    steel blue-greys, patina green for the dome, snow.
  * `archive` — interior: navy-teal room `#04090D…#62716E`, wood, amber lamps `#6E3F22…#FFE3AA`, paper, ink.
  * `sepia` — transitions/memories, with a single red ramp for C-17.

## 3. Pixel density & scale (LOCKED)
* World renders at **640×360 logical pixels**, integer-upscaled (3× at 1080p, 4× at 1440p, 6× at 2160p).
* **1 texel = 1 screen pixel for every 2D layer**, near or far. Distance is expressed by less detail and haze,
  never by smaller pixels. No scaled/rotated sprites (no "mixels").
* Human adult ≈ **46 px** tall (head 7 px, ~6.5 heads), women ≈ 43 px, children 28–34 px.
  Doors ≈ 52 px, storey height ≈ 34–40 px near, wagons ≈ 40 px tall.
* Dialogue portraits: **112×112 px** busts shown at 3×.
* UI typography is rendered at native resolution (crisp), framed by pixel-art panels drawn at 1:1 and scaled ×3.

## 4. Architecture language
* **Soviet (Karsk):** prefabricated slab blocks (4–9 storeys, window grids 6×8 px with 3–4 px piers), grain
  elevators and silos (cylinders with vertical shading bands), brick factory halls with saw-tooth roofs, chimneys,
  cooling towers far away, lattice cranes, railway infrastructure (signal box with one amber window, water tower,
  catenary-free yard), reconstruction scaffolding and timber hoardings, hand-painted slogans in Cyrillic (fictional,
  civic: "ВОССТАНОВИМ ВМЕСТЕ" — "we rebuild together"). Damage is visible but the city is **lived-in**: stalls,
  stoves, laundry, repaired roofs, people.
* **German (Berlin):** neoclassical/monumental stripped classicism — endless pilaster rhythms, colossal square
  piers, bronze doors, travertine-ochre stone, heavy cornices, the fictional completed **Große Halle** (dome with
  green-black patina; on the lantern the eagle above the globe, as in Speer's final 1939 plan). Ordinary Berlin: Gründerzeit tenements with balconies, tram wires,
  sealed apartment doors, notice boards. Monumentality is always **juxtaposed with small, pressured lives**.
* **Insignia policy (updated 2026-11-04, user decision — TECHNICAL_ARCHITECTURE §12.4):** real regime insignia
  (swastika flags and banners, the state eagle with the wreathed swastika on stamps and plaques; hammer & sickle
  and red star) appear as in-world iconography of the two oppressive states while the player setting
  "Historische Hoheitszeichen" is on (default), always inside the critical narrative (social-adequacy clause,
  StGB §86 Abs. 4). Every such asset has a neutral twin used when the setting is off: the fictional
  **Reichssiegel** (white pillar/obelisk in a black disc) or a plain eagle; on the Soviet side a fictional
  gear-and-wheat emblem. Never SS runes, never on the player's side, in menus, UI chrome or rewards. Symbols are
  shown as instruments of power.

## 5. Lighting
* **Baked key light in the painted layers** (art-directed), plus **dynamic Godot 2D lights** for local life:
  * Karsk: low dawn sun behind haze, back-right → rim light on right edges, cold ambient, one amber signal-box
    window, fire barrels, sodium-ish lamps.
  * Berlin archive: tall windows left (blue-grey daylight shafts, dithered), amber desk lamps, deep shadows.
  * Berlin exterior / Great Hall: sunset behind the hall → giant silhouette with burning edge; floodlights.
* Every opaque environment layer ships a **normal map** (`*_n.png`, OpenGL +Y up) so lamps wrap around bricks,
  pipes and characters; lit windows/fire ship an **emission mask** (`*_e.png`) that is never darkened.
* Light falloff in the post shader is snapped to the scene palette with ordered dithering, so dynamic light still
  reads as hand-dithered pixel art.

## 6. Composition
* Low horizon for monumental scenes; high horizon for streets with ground detail.
* 5–8 depth planes: sky → far city (haze 35–60 %) → mid industry → near buildings → playfield → foreground frame.
* **Framing devices** at the screen edges (dead tree, wreck, pillar, bridge underside) in near-black silhouette.
* Leading lines: rails, tram wires, kerbs, cornices toward the story focal point.
* Tiny figures in far planes for scale; the protagonist is the only figure with full-detail lighting.
* Each playable screen has exactly **one warm focal light** near the next interaction.

## 7. Environmental detail & storytelling
Snow caps on every upward edge, slush and puddles reflecting lamps, rust streaks below metal, posters peeling,
laundry lines, stovepipes through windows (housing shortage), repaired roofs with mismatched sheets, scaffolding,
queues, ration notices, tram stops, sealed doors with official notices, propaganda billboards half-papered-over.
Detail density: highest on the playfield, medium in near background, silhouette-only far away.

## 8. Camera & perspective
* **Mode A (side-on 2D):** orthographic, horizon ≈ 55–65 % height, movement on x only.
* **Mode B (oblique 2.5D):** front-facing façades with a visible ground band (≈ 90–120 px deep) in which actors
  move on x and y (y-sorted, depth speed 0.6×). Tracks and kerbs run horizontally.
* **Mode C (3D pixel render):** Godot 3D rendered *inside the same 640×360 viewport*, narrow FOV (≤ 30°) or
  orthographic, toon-quantised light (4–5 steps), 1 px depth/normal outline, palette snap with Bayer dither,
  no TAA/SSR/SSAO/motion blur. Camera moves slowly (≤ 20 px/s screen-space) to avoid crawl.
* Camera is pixel-snapped; the sub-pixel remainder is applied at display scale (smooth pans, no shimmer).

## 9. Atmosphere
Layered haze bands between planes, dithered light shafts, falling snow (2 sizes, parallax), drifting smoke
ribbons (animated by slow UV/offset scrolling and sprite frames), steam from manholes/locomotives, dust motes in
interior light, flickering lamps (subtle, never strobe — accessibility).

## 10. Characters
* Silhouette first: **Alexei** — shapka with ear-flaps, padded dark-green coat, satchel on hip, heavy boots.
  **Konrad Adler** — fedora brim, long dark-blue overcoat to the knees, scarf, drafting tube / leather folder,
  upright posture that loosens over the story. **Irina** — headscarf, dispatcher's quilted jacket, clipboard.
  **Emil** — older, stooped, cardigan under a grey archive coat, round spectacles.
* 2–3 tone shading per material + rim light from the scene key; selective dark outline (outer edge only, tinted to
  the local shadow, never pure black except night).
* Normal maps for characters so scene lights wrap around them.

## 11. Animation principles
* Walk 8 frames @ 10 fps (contact–down–pass–up), 1 px head bob, arm swing opposite legs, coat hem lag.
* Idle 6 frames @ 5 fps: breathing (1 px shoulder rise), occasional blink/glance.
* Inspect/interact 4–6 frames with anticipation and hold; talk gestures 4 frames.
* Directions: side (right; left = mirror), front, back for Mode B; side for Mode A.
* Timing over frame count: hold key poses, never tween pixel sprites.

## 12. Materials & textures
| Material | Rule |
|---|---|
| Concrete | panel joints every 12–16 px, vertical stains, chipped corners (1–2 px), snow on ledges |
| Brick | 4×2 px bricks only on near planes; mid planes suggest coursing by dithered lines |
| Rusted steel | rivets as 1 px highlight dots, rust ramp gradients downward, rim light on edges |
| Glass | dark navy with 1–2 px cold reflection; lit = warm + emission; broken = black with shard |
| Wood | plank lines, 1 px grain, darker at joints |
| Snow | 1–3 px caps, blue-grey shadows, drifts in corners, footprint-darkened slush on paths |
| Wet ground | horizontal broken reflections of lamps/sky (dithered), darker value than dry |
| Paper/documents | UI-layer art at 1:1, readable text set in HD fonts on top — never blurry world text |

## 13. Acceptance gates (art)
Per scene, compare a 640×360 capture side by side with the reference board and score with
`preproduction/docs/ART_QA_SCORECARD.md`. Blockers: inconsistent pixel size, unreadable character, ideology
glorified, photoreal or cartoon style drift, shimmering during pans.
