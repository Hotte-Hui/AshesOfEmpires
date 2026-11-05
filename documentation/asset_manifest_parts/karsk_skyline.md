# Asset manifest part — karsk_skyline (background buildings of scene A1 "Verladebahnhof Karsk")

* **Date:** 2026-11-04
* **Area owner:** karsk-skyline (redesign of the background planes of `L_A1_Railyard` after the user feedback
  "bei der ersten Szene sehe ich hinten so komisch aussehende Gebäude … realistisch oder typisch russisch").
* **Generator:** `py -3 -P tools/pixelgen/env_karsk_skyline.py` (add `--no-preview` to skip the review composites).
  Modules: `env_karsk_skyline.py` (orchestrator + mid plane, manifests, palette check, previews),
  `env_karsk_skyline_lib.py` (plane geometry, depth scale, palette access, haze chains, fonts incl. bold rooftop
  capitals, emblem masks, QA), `env_karsk_skyline_kit.py` (shapes, windows, Khrushchyovka, grain elevator, rooftop
  slogan, chimneys, masts, pylons, birches, people), `env_karsk_skyline_arch.py` (Orthodox church, Stalinist
  administration, tower crane, izba, garages), `env_karsk_skyline_far.py` (far_industry, far_city),
  `env_karsk_skyline_near.py` (near_bg), `env_karsk_skyline_preview.py` (review composites, sun check).
  Depends only on `tools/pixelgen/pg.py` (unchanged) — independent of the `env_karsk_*` railyard generator.
* **Determinism:** fixed seeds, no network. Verified: SHA-1 of all 17 outputs identical after regeneration.
* **Licence / provenance:** original procedural pixel art created for ASHES OF EMPIRES: THE LAST WINTER by the
  karsk-skyline generator (AI-authored code, project-owned, same licence as the game). No third-party images,
  fonts or textures; no photo was traced or sampled (architecture drawn from general knowledge of Soviet
  provincial towns around 1964). Palette `karsk` + the shared C-17 red ramp (`pg.PALETTES['sepia']['red']`) only;
  palette check of every colour / emission PNG passes (no off-palette pixels).
* **Fictional / historical content:** the slogan "СЛАВА ТРУДУ!" ("Glory to labour", generic civic slogan) stands
  in red sheet-metal letters on the elevator's silo gallery. §12.4: `mid.png` shows the fictional gear-and-wheat
  emblem beside it (red gear, golden ear), `mid_hist.png` the real hammer & sickle — identical files except the
  11×11 emblem box (77 px). Other text: СКЛАД (church used as warehouse), ДЕПО, year "1953" on the Stalinist
  attic. The red star on the spire is generic Soviet imagery (both variants).

## Files (`assets/environments/karsk_skyline/`)
All lit planes ship `<name>_n.png` (normal map, OpenGL +Y up) and `<name>_e.png` (emission: lit windows, red
obstruction / crane lamps, gilt spire edge is *not* emissive). Sizes, `pos`, parallax and z are **identical** to the
railyard layers they replace.

| File | Size | pos / parallax / z | Content |
|---|---|---|---|
| `far_city.png` + `_n` + `_e` | 802×112 | [0,118] / 0.12 / -90 | Town on the horizon (1.27 px/m): panel-block districts in two hazy rows with tiny cranes, old quarter with a little church, bread factory stacks, power station with **two hyperboloid cooling towers at x 546 / 662 flanking the sun** (tops 149 / 157 = unchanged tower_plume anchors), boiler house, two striped chimneys (smoke anchor 688,123 unchanged), switchyard + pylon lines, guyed TV mast with red lamps near the sun (x 757). |
| `far_industry.png` + `_n` + `_e` | 968×147 | [0,83] / 0.25 / -84 | Industrial belt (2.64 px/m): thermal power station (boiler house, turbine hall, coal conveyor, two red/white striped chimneys at x 36 / 50), brick saw-tooth halls with arched windows, Intze water tower, telescopic gasholder, a microdistrict of five-storey panel blocks with antennas, a brick school, low warehouses, east factory chimney (x 872), pylons; bypass railway embankment with rails at y 216. |
| `mid.png` + `_n` + `_e`, `mid_hist.png` + `_hist_n` + `_hist_e` | 1224×185 | [0,49] / 0.45 / -74 | The readable town (4.75 px/m): **grain elevator** (x 76–304: 5 silos, patched shell hole on silo 2, gallery with the rooftop slogan + emblem, working house, conveyor bridge, brick receiving building, a worker with a ladder), **five-domed church turned warehouse** (x 336–452: crosses removed, rusty dome with missing sheets, boarded windows, scaffolding, СКЛАД), **Khrushchyovka** (x 467–591: 2 sections, 5 storeys, panel joints, balconies with laundry / firewood, stairwell windows, entrance canopies, antennas), garages, **Stalinist railway administration** (x 640–790: rusticated ground floor, portico, balustrades, clock tower, colonnaded belvedere, gilt spire with red star, "1953", 3 lit windows), izba, **panel block under construction + tower crane** (x 850–1030, mast at 1000, panel hoisted high, red jib lamp, two erectors), log houses, district boiler house with striped chimney (x 1150), garages, birches; **far railway embankment** across the plane (rail heads y 209, sleepers y 210 = KarskTrain rail). |
| `near_bg.png` + `_n` + `_e` | 1570×113 | [0,137] / 0.72 / -60 | Near quarter (7.6 px/m): two-storey **timber barrack** (x 4–160, carved window frames, stovepipe through a window, laundry line to the pole at x 200), **izby** with steep snowy roofs and carved nalichniki (x 208, 412), birches, woodsheds and log piles, brick **locomotive shed ДЕПО** (x 690–1000, arched gates, row of smoke jacks), low goods shed, **half-stone merchant house** (x 1150–1270), garages, fences. |
| `skyline.json` | — | — | Machine-readable integration data: the 4 layer entries, the 12 fx entries, laundry pegs, hotspot marks. |

Depth scale (consistent, ∝ parallax as for a pinhole camera; the playfield person is hero-scale 47 px):
architecture px/m = 10.56 × parallax → near_bg 7.6 (person 13 px, storey 21 px), mid 4.75 (person 8 px, storey
13 px), far_industry 2.64 (storey 7 px), far_city 1.27 (storey 3 px). Haze: every plane is painted with its own
material ramps (far: sky ramp, mid: sage/stone/wood, near: teal/wood/brick) and a ground-fog pass that shifts colours
along palette chains toward the air light near the plane base (ordered dither, no new colours).

Composition rules applied: the sun disc (screen 612,190) is kept free by low buildings on its path in every plane at
cam 0 / 640 / 1280 (visible fraction of the disc 0.84 / 0.51 / 0.33, before 0.74 / 0.13 / 0.04); nothing busy sits on
the roofline of the signal box (cam 0–186: the Khrushchyovka hides fully behind it at cam 0, the church dome stays
below its roof at cam 186), the tea stall or the office (cam 1280: construction site stays below the office roof, the
crane's panel hangs high, the boiler chimney moved east of the office); no tall mast behind the tea stall.

## Integration into `assets/environments/karsk_railyard/scene.json` (lead)
Verified in Godot: `ResourceLoader` resolves `../karsk_skyline/…` relative to the manifest directory (also the
`_hist` pick through `Symbols.pick`), so the files stay in their own folder and survive railyard regenerations.
Probe: `godot --headless --path . --script res://tests/visual/skyline/path_probe.gd`.

1. **layers** — replace the four entries of the same name (note `emission` is now **true** for far_industry and
   near_bg, they gained lit windows):
```json
{"name": "far_city", "file": "../karsk_skyline/far_city.png", "pos": [0, 118], "parallax": [0.12, 0.0], "z": -90, "normal": true, "emission": true, "lit": true, "emission_strength": 0.35},
{"name": "far_industry", "file": "../karsk_skyline/far_industry.png", "pos": [0, 83], "parallax": [0.25, 0.0], "z": -84, "normal": true, "emission": true, "lit": true, "emission_strength": 0.35},
{"name": "mid", "file": "../karsk_skyline/mid.png", "pos": [0, 49], "parallax": [0.45, 0.0], "z": -74, "normal": true, "emission": true, "lit": true, "emission_strength": 0.45},
{"name": "near_bg", "file": "../karsk_skyline/near_bg.png", "pos": [0, 137], "parallax": [0.72, 0.0], "z": -60, "normal": true, "emission": true, "lit": true, "emission_strength": 0.45}
```
2. **fx** — delete every `anim_sprite` whose `"layer"` is `far_city`, `far_industry`, `mid` or `near_bg` (14 entries
   today) and insert these 12 (same strips in `karsk_railyard/fx/`, placed on the new chimney mouths):
```json
{"type": "anim_sprite", "file": "fx/smoke_ribbon_a.png", "frames": 8, "fps": 4, "pos": [26, -41], "parallax": 0.25, "z": -83, "emission": false, "frame_size": [72, 132], "layer": "far_industry"},
{"type": "anim_sprite", "file": "fx/smoke_ribbon_b.png", "frames": 8, "fps": 5, "pos": [40, -31], "parallax": 0.25, "z": -83, "emission": false, "frame_size": [72, 132], "layer": "far_industry"},
{"type": "anim_sprite", "file": "fx/smoke_ribbon_far.png", "frames": 8, "fps": 4, "pos": [862, 13], "parallax": 0.25, "z": -83, "emission": false, "frame_size": [56, 96], "layer": "far_industry"},
{"type": "anim_sprite", "file": "fx/smoke_ribbon_far.png", "frames": 8, "fps": 4, "pos": [678, 29], "parallax": 0.12, "z": -89, "emission": false, "frame_size": [56, 96], "layer": "far_city"},
{"type": "anim_sprite", "file": "fx/tower_plume.png", "frames": 8, "fps": 5, "pos": [526, 87], "parallax": 0.12, "z": -89, "emission": false, "frame_size": [84, 64], "layer": "far_city"},
{"type": "anim_sprite", "file": "fx/tower_plume.png", "frames": 8, "fps": 4, "pos": [642, 95], "parallax": 0.12, "z": -89, "emission": false, "frame_size": [84, 64], "layer": "far_city"},
{"type": "anim_sprite", "file": "fx/smoke_ribbon_far.png", "frames": 8, "fps": 4, "pos": [1140, 13], "parallax": 0.45, "z": -73, "emission": false, "frame_size": [56, 96], "layer": "mid"},
{"type": "anim_sprite", "file": "fx/chimney_wisp.png", "frames": 8, "fps": 5, "pos": [39, 139], "parallax": 0.72, "z": -59, "emission": false, "frame_size": [30, 60], "layer": "near_bg"},
{"type": "anim_sprite", "file": "fx/chimney_wisp.png", "frames": 8, "fps": 6, "pos": [234, 146], "parallax": 0.72, "z": -59, "emission": false, "frame_size": [30, 60], "layer": "near_bg"},
{"type": "anim_sprite", "file": "fx/chimney_wisp.png", "frames": 8, "fps": 5, "pos": [440, 146], "parallax": 0.72, "z": -59, "emission": false, "frame_size": [30, 60], "layer": "near_bg"},
{"type": "anim_sprite", "file": "fx/chimney_wisp.png", "frames": 8, "fps": 6, "pos": [1176, 123], "parallax": 0.72, "z": -59, "emission": false, "frame_size": [30, 60], "layer": "near_bg"},
{"type": "anim_sprite", "file": "fx/steam_puffs.png", "frames": 6, "fps": 5, "pos": [966, 126], "parallax": 0.72, "z": -59, "emission": false, "frame_size": [26, 44], "layer": "near_bg"}
```
3. **KarskLaundry** actor: `props.pegs` → `[[163,210],[169,210],[175,209],[182,207],[188,204],[193,201]]`
   (line from the barrack wall at 159,209 to the pole top at 200,193; ±1 px from today's pegs).
4. **KarskTrain**: no change. The current contract (pos [0,210], parallax 0.45, z -73) runs on the new mid-plane
   embankment (rail heads y 209, sleepers y 210, wheels on y 210); verified in-engine at cam 150 (train passes
   between tea stall and signal box). The far_industry plane additionally carries a bypass rail at y 216 (the
   earlier 0.25 contract) — harmless if unused.
5. **Hotspots**: **no player position changes**. `exp_grain` (elevator still at mid x 76–304, silos 76–196) and
   `exp_cooling_towers` (tower 1 still at far_city x 546, top 149 → current mark [1250,175] at cam ~800 still points at
   it; both towers are unobstructed at cam 800–840) keep their entries. Optional `hotspot_info.mark` refinements:
   `exp_grain` → `[136, 173]` (centre of the silo row next to the patched silo; today [190,120] lands on the gallery
   roof by the slogan), `exp_barrack` → `[82, 191]` (roof of the redrawn barrack, today [82,186]).
6. Notes for `hotspot_info.what` (optional): exp_grain "five silos, silo 2 with a patched shell hole, СЛАВА ТРУДУ! on
   the gallery"; exp_cooling_towers "two hyperboloid cooling towers flanking the sun"; exp_barrack "two-storey timber
   barrack, stovepipe through a window, laundry line".

## Verification
* Python composites (`env_karsk_skyline_preview.py`, test manifest) at cam 0 / 640 / 1280 (2×) + 3× crops reviewed
  over several rounds (slogan legibility → bold font; neutral emblem two-tone; shell-hole patch; calmer panel block;
  radio mast removed from behind the tea stall; smoke kept off the church; sun windows).
* In-engine (`tests/visual/skyline/L_KarskSkyline.tscn` = root of L_A1_Railyard with `art_manifest =
  res://tests/visual/skyline/scene.json`, a generated copy of the railyard manifest with these planes / fx / pegs):
  windowed captures at cam 0, 186, 640, 1280 with symbols on and `--symbols=0` (neutral emblem confirmed), and cam 150
  after ~14 s (distant train on the embankment). Import settings of the new PNGs identical to the railyard layers.
* Known limits: at cam 1280 the existing foreground tree (fg_frame) covers the TV mast and part of cooling tower 2,
  and the office covers tower 1's lower half — the towers read best from the current exp_cooling_towers spot (cam ~800).
