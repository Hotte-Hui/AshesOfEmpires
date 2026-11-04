# Asset manifest part — trans_a1m1 (cinematic LS_A1_ToM1: Alexei/Karsk → Konrad/Berlin)

* **Date:** 2026-11-04
* **Area owner:** trans-a1m1 (soft protagonist switch after the A1 decision, TECHNICAL_ARCHITECTURE §12.5)
* **Scene / code:** `scenes/cinematics/a1m1/CinA1ToM1.tscn`, `scripts/cinematics/a1m1/cin_a1_to_m1.gd`
  (`signal finished`, `configure(ctx)`, `play()`, `skip()`; plus `seek(t)`, `get_time()`, `get_duration()`
  for harnesses). Strings: `data/locale/de_trans_a1m1.json`. Harness: `tests/visual/cine_a1m1_harness.tscn/.gd`.
* **Generators:** `py -3 -P tools/pixelgen/cine_a1m1.py` (all art + `assets/cinematics/a1m1/layout.json`);
  modules `cine_a1m1_lib.py` (ramps, dithered tone fills, 3×5 / 4×7 pixel fonts, insignia templates, savers),
  `cine_a1m1_karsk.py`, `cine_a1m1_close.py`, `cine_a1m1_berlin.py`. Sound: `py -3 -P tools/audiogen/cine_a1m1_sfx.py`.
  Built on `tools/pixelgen/pg.py` (unchanged, read-only).
* **Determinism:** every seed comes from `zlib.crc32(name)`; no `hash()`, no network, no external media.
* **Licence / provenance (all files below):** original procedural pixel art and synthesized audio created for
  ASHES OF EMPIRES: THE LAST WINTER by the trans-a1m1 generators (AI-authored code, project-owned, same licence as
  the game). No third-party images, fonts, samples or traced references.
* **Palettes:** `karsk` (dusk shot), `sepia` tone + red (ledger close-up, C-17 red), `archive` paper/blue/ink (plan),
  `berlin` (street). Grade blends sepia → archive → berlin during the dissolves (palette swapped at zero snap).
* **Re-used read-only (not copied):** `assets/environments/karsk_railyard/` `far_city`, `far_industry`, `mid`,
  `poles` layers (tinted to dusk), their smoke-ribbon strips (re-anchored from the A1 `scene.json`), props
  `wagon_c17` (the actual C-17 wagon 24-311, incl. its `_hist` variant), `lamp_post_1`, `bench`; character sheets
  `alexei`, `irina`, `konrad`, `guard`, `clerk`, `berlin_mother`, `berlin_child` (loaded at runtime).
* **Historical insignia (§12.4):** every image with real regime insignia has a neutral base file and a `_hist`
  variant, chosen from `ctx.symbols` (Game passes `Symbols.enabled()`): Soviet red star + hammer & sickle on the
  locomotive and the ledger's railway seal (neutral: fictional gear-and-wheat emblem); swastika on the Bauarchiv
  banners, the eagle relief's wreath and the GBI office stamp on the plan (neutral: the fictional Reichssiegel
  pillar). Shown only as in-world iconography of the regimes inside the critical narrative; never UI or reward.
  The Great Hall dome carries an eagle on a globe in both modes (Speer's final design had no swastika there).

## Art — `assets/cinematics/a1m1/`
| File | Size | Use |
|---|---|---|
| `layout.json` | — | Geometry for the script (chimney/whistle/cab/headlamp anchors, glyph centre, imprint/pencil/stamp anchors, Berlin street geometry, chimney tops, frame counts). |
| `dither_dissolve.gdshader` | — | 8×8 Bayer per-texel dissolve (optional radial ordering) for the match dissolve and the plan → Berlin transition. |
| `karsk/sky.png` | 642×360 | Dusk sky, glow low in the west (left), unlit, parallax 0. |
| `karsk/clouds.png` | 980×150 | Long stratus bands with warm-lit undersides in the west, parallax 0.04. |
| `karsk/yard.png` + `_n` + `_e` | 1760×220 | Fence, far track, water tower, signal mast (red lamp, emission), near track, snowy embankment, platform with trodden path. |
| `karsk/fg.png` | 2000×120 | Near-black hand cart + snow bank (parallax 1.15). |
| `karsk/loco.png` / `loco_hist.png` + `_n` + `_e` | 284×112 | 2-10-0 freight locomotive facing west; smoke deflector emblem (neutral gear-and-wheat / red star + hammer & sickle), cab with fire glow and driver, number Л-2317. |
| `karsk/loco_wheels.png` + `_n` | 8 × 284×112 | One driver revolution: 5 coupled red spoked wheels, coupling/main rods, crosshead. |
| `karsk/tender.png`, `gondola.png`, `boxcar.png` + `_n` | 196/180/196 wide | Tender 2317 with coal and snow, gondola 61-044 with scrap, covered wagon 42-905. |
| `karsk/tail_lamp.png` + `_e` | 7×9 | Red tail signal on the C-17 wagon. |
| `karsk/ledger_arm.png` + `_n` | 8×11 | The freight ledger under Alexei's arm (branch keep_private). |
| `karsk/fx_puff.png` | 12 × 56×60 | Exhaust puff (spawned per exhaust beat, 4 per wheel revolution). |
| `karsk/fx_steam.png`, `fx_whistle.png`, `fx_snowdrop.png` | 8 frames each | Cylinder-cock steam, whistle plume, snow sliding off the wagon roof at the coupling jolt. |
| `close/ledger.png` / `ledger_hist.png` | 640×360 | Ledger page (sepia): rows 9.–16.1., wagon 24-311 with the blacked-out consignee; faded railway seal (neutral / hammer & sickle). |
| `close/imprint.png` | 4 × 180×102 | Red C-17 stamp: wet gloss → spreading → soaked → dry. |
| `close/stamp.png`, `stamp_shadow.png` | 3 × 300×330 | Rubber stamp from above (block, label C-17, ferrule, turned handle leaving the frame), three heights; dithered shadows. |
| `close/initials.png` | 40×22 | Branch share_with_irina: Irina's countersign (tick + И.Б.) in the C-17 row. |
| `close/plan.png` / `plan_hist.png` | 640×360 | Diazo plan "Blatt 7, Nordachse C": corridor, dashed second wall, dimensions; GBI round stamp (eagle + Reichssiegel / eagle + swastika). |
| `close/pencil.png` | 317×151 | Pencil C-17 on the identical glyph skeleton as the stamp, circle, underline, arrow to the second wall. |
| `berlin/sky.png` | 642×362 | Overcast early-morning haze, faint warm east glow. |
| `berlin/dome.png` | 620×330 | The Große Halle in haze: drum, ribbed dome, lantern, globe and eagle (parallax 0.12/0.2). |
| `berlin/far.png` + `_e` | 1000×200 | Distant roofs, firewalls, chimneys, a few early lights (parallax 0.45). |
| `berlin/street.png` + `_n` + `_e` | 1000×620 | Bauarchiv (rusticated base, pilasters, BAUARCHIV attic, portal + lanterns), Gründerzeit tenements (balconies, stove pipes, bakery, tobacconist), tram stop, gas lamps, contact wire, pavement, cobbles with rails. |
| `berlin/fg.png` + `_e` | 1100×200 | Near cast-iron lamp post + snow bank (parallax 1.15). |
| `berlin/banner.png` / `banner_hist.png` | 3 × 24×96 | Vertical banners with sway (neutral Reichssiegel on black / red with white disc and swastika). |
| `berlin/relief.png` / `relief_hist.png` + `_n` | 52×34 | Stone eagle over the portal (wreath: Reichssiegel / swastika). |
| `berlin/door.png` + `_e`, `jambs.png` + `_n` | 3 × 34×50, 54×64 | Portal doors closed/ajar/open with warm interior; jambs drawn over Konrad as he enters. |
| `berlin/tram.png` + `_n` + `_e`, `tram_pole.png` + `_e` | 214×92, 3 × 70×64 | Two-axle tram "3 GR.HALLE" with lit windows and passengers; trolley pole with spark frames. |
| `berlin/smoke.png`, `pigeons.png`, `window_on.png` + `_e`, `queue.png` | strips | Chimney smoke, pigeons that fly off when the door closes, a window that lights up, the bakery queue. |

## Audio — `assets/audio/sfx/` (44.1 kHz, 16-bit, synthesized; not looped)
| File | Length | Content |
|---|---|---|
| `cine_a1m1_couple.wav` | 1.8 s | Buffers meet, coupling chain, yard reverb. |
| `cine_a1m1_whistle.wav` / `cine_a1m1_whistle_far.wav` | 2.6 / 3.6 s | Deep three-chime steam whistle, near / far (sound bridge into Berlin). |
| `cine_a1m1_chuff.wav` | 0.8 s | One exhaust beat (played per beat, quieter when the engine is far). |
| `cine_a1m1_hiss.wav` | 2.6 s | Cylinder cocks venting. |
| `cine_a1m1_depart.wav` | 6.0 s | Slack running out through the couplings, rail joints accelerating, rumble. |
| `cine_a1m1_stamp.wav` | 0.9 s | Swish, wooden knock, rubber squish (layered with the existing `stamp_thud`). |
| `cine_a1m1_swell.wav` | 9.0 s | Soft open-fifth string pad under the stamp and the dissolve. |
| `cine_a1m1_tram_arrive.wav` / `cine_a1m1_tram_depart.wav` | 4.0 / 4.5 s | Tram rolling in with brake squeal / motor whine and rumble receding. |
| `cine_a1m1_door.wav` | 1.8 s | Heavy portal door: latch, swing, closing thud. |
| `cine_a1m1_pigeons.wav` | 1.4 s | Pigeons taking off. |
Existing project sounds used: `tram_bell`, `stamp_thud`, `wind_gust`, `step_snow_*`; Audio channels `amb_berlin_street`,
`mus_berlin` (continues seamlessly into M1).

## Text — `data/locale/de_trans_a1m1.json`
`cin.a1m1.alexei.share`, `cin.a1m1.alexei.keep` (inner voice, branch-dependent), `cin.a1m1.konrad` (inner voice),
`cin.a1m1.caption` (description of the match dissolve for accessibility/QA).
