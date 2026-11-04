# Asset manifest — characters (sprite sheets, normal maps, dialogue portraits)

Area owner: characters specialist · Date: **2026-11-04** · Engine target: Godot 4.7.2

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (Pillow + numpy, no AI image
  models, no network, no third-party art). Hand-designed pixel shapes (heads, hands, boots, props, facial
  feature stamps) are written as ASCII maps inside the generator source.
* The reference images in `documentation/references/` were used **only** as internal style study
  (lighting idea of `user_ref_1` for the portraits, value structure of `user_ref_8`). Nothing was traced,
  sampled, copied or embedded.
* Licence: project-owned original asset (same licence as the game's own content). No attribution required
  to third parties.
* Deterministic: re-running the generator reproduces byte-identical PNGs.

## Reproduce
```bash
py -3 -P tools/pixelgen/characters.py            # all sheets + normal maps + portraits + previews (~10 s)
py -3 -P tools/pixelgen/characters.py konrad     # one character
py -3 -P tools/pixelgen/characters_check.py      # validator (exit 1 on failure)
```

## Generator scripts
| File | Role |
|---|---|
| `tools/pixelgen/characters.py` | entry point: sheet layout, `sheet.json`, previews, calls the portrait generator |
| `tools/pixelgen/chargen_core.py` | G-buffer rig renderer: OKLab hue-shifted ramps, capsules / polygons / bitmaps, height-derived normals, shading (key, contact shadows, AO, inner lines, cool rim, selective outline), 2-bone IK |
| `tools/pixelgen/chargen_body.py` | generic humanoid paper-doll (side / front / back), coats, skirts, sleeves, legs, boots |
| `tools/pixelgen/chargen_anim.py` | keyframed poses: walk 8, idle 6, inspect 6, interact 4, talk 4; front/back walk + idle |
| `tools/pixelgen/chargen_cast.py` | the cast: palettes, hand-drawn heads / hands / boots / props, garments, per-character hooks |
| `tools/pixelgen/chargen_portrait.py` | 112×112 portraits: analytic-ellipsoid bust ray-cast into depth buffers, 2.5D cast shadows, posterised key/rim lighting, expression stamps |
| `tools/pixelgen/characters_check.py` | contract validator (schema, origin row, clipping, normal alpha/length, heights, portrait strips) |

`tools/pixelgen/pg.py` is used unchanged (not modified).

## Sprite sheets — `assets/characters/<id>/` (cell 32×56, origin [16,54] = feet pixel, facing right)
Every sheet ships `sheet.png` (diffuse, RGBA, binary alpha), `sheet_n.png` (OpenGL +Y-up normal map,
identical alpha) and `sheet.json` (contract of TECHNICAL_ARCHITECTURE §4; extra optional key
`ground_speed` = px/s that matches the planted-foot travel of the walk cycles).

| id | rows (row index → anim, frames @ fps) | sheet px | figure height | silhouette keys |
|---|---|---|---|---|
| `alexei` | 0 idle_side 6@5 · 1 walk_side 8@10 · 2 idle_front 6@5 · 3 walk_front 8@10 · 4 idle_back 6@5 · 5 walk_back 8@10 · 6 inspect_side 6@8 (once) · 7 interact_side 4@8 (once) · 8 talk_side 4@6 | 256×504 | 46 px | ushanka with hanging ear-flaps, padded dark-green coat (quilting, buttons), satchel on the hip with cross strap, heavy repaired boots |
| `konrad` | same 9 rows as alexei | 256×504 | 48 px (with fedora) | fedora with ribbon + brim, knee-long dark-blue overcoat, sand scarf, drafting tube slung on the back, leather folder under the far arm, upright posture |
| `irina` | 0 idle_side · 1 walk_side · 2 idle_front · 3 talk_side | 256×224 | 44 px | rust headscarf, quilted slate dispatcher jacket, skirt, felt boots, clipboard at the hip (raised while talking) |
| `emil` | 0 idle_side · 1 talk_side · 2 idle_front | 192×168 | 44 px (stooped) | bald crown + grey fringe, round spectacles, grey moustache, grey archive coat open over a brown cardigan, pencils in the breast pocket, stoop |
| `worker_a` | 0 idle_side · 1 walk_side | 256×112 | 47 px | ushanka with flaps tied up, bulky quilted olive jacket, shovel on the shoulder, felt boots |
| `babushka` | 0 idle_side · 1 walk_side | 256×112 | 40 px | strongly stooped, dotted headscarf, long dark coat, cloth bundle in hand |
| `child_a` | 0 idle_side · 1 walk_side | 256×112 | 30 px | red knit hat with pompom, red scarf, short coat, felt boots, bouncy walk |
| `berlin_father` | 0 idle_side · 1 walk_side | 256×112 | 46 px | flat cap, short brown coat, wooden crate of belongings carried in both arms |
| `berlin_mother` | 0 idle_side · 1 walk_side | 256×112 | 43 px | small dark hat + hair bun, belted plum coat, suitcase in hand |
| `berlin_child` | 0 idle_side · 1 walk_side | 256×112 | 31 px | beret, short coat, knee socks, toy bear in hand |
| `clerk` | 0 idle_side · 1 walk_side | 256×112 | 46 px | bare head with slicked dark hair, grey suit, shirt collar + tie, black sleeve protector, file folder |
| `guard` | 0 idle_side · 1 walk_side | 256×112 | 48 px | generic grey greatcoat with belt (no insignia), peaked cap with dark visor, tall boots, hands behind the back |

Animation: walk 8 frames (contact, down, passing, up per step; 1 px bob on the down frames; opposite arm
swing with a half-frame lag; coat hem lag + knee push; satchel / scarf lag one frame), idle 6 frames
(1 px chest/shoulder rise on frames 2–3, blink on frame 4), inspect (anticipation → lean in → hold, hand to
chin, blink in the hold), interact (anticipation → reach → hold), talk (4 small gestures, mouth open on
frames 1 and 3, small nod on frame 2). Front/back walks keep the feet on the origin row (rear foot higher).

Lighting baked into the diffuse is **character-relative** (warm key from the front-top of the facing
direction, cool rim on back/top edges, 2–3 tones per material, selective outline tinted to each material's
darkest hue-shifted shade, never pure black) so it stays valid when the sprite is mirrored; the scene light
comes from Godot 2D lights through the normal maps.

## Portraits — `assets/characters/<id>/portrait.png` + `portrait.json`
Horizontal strip 448×112 = 4 frames of 112×112 in the order `neutral, concerned, determined, surprised`
(`portrait.json`: `{"size": [112, 112], "expressions": [...]}`). Opaque painted background (scene-tinted navy
with a soft key-side glow). Bust in 3/4 view facing right, single warm key light from the front-right, deep
navy shadows, cool rim on the back edge. Files: `alexei`, `konrad`, `irina`, `emil`.

## Localisation
`data/locale/de_characters.json` — `char.<id>.name`, `char.<id>.role` for all 12 ids and
`char.expression.<name>` (German).

## Review images (not shipped; folder has `.gdignore`)
`assets/characters/_preview/`: `<id>_contact_3x.png` (every row of every character on a dark scene colour
and on light haze), `lineup_1x/3x.png` (idle frame of the whole cast on 3 backgrounds),
`lineup_silhouettes_3x.png` (pure silhouettes at 1x scale ×3), `walk_strips_3x.png` + `walk_side_all.gif`
(all walk cycles side by side), `<id>_walk_side_onion.png` (frame overlay → volume / jitter check),
`normal_relight_test.png` (sheets relit from left / right / top through `sheet_n.png`),
`<id>_portraits_3x.png`, `portraits_all_2x.png`.
