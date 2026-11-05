# Asset manifest — characters (in-world sprite sheets + normal maps)

Area owner: characters specialist (`chars-sprites`) · Updated: **2026-11-04, round 2** · Engine target: Godot 4.7.2
(Dialogue portraits `portrait.png/json` are owned by the portrait generator `chargen_portrait*` and are not
listed here.)

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (Pillow + numpy; no AI image
  models, no network, no third-party art). All heads, hats, hands, boots and props are hand-designed pixel
  maps written as ASCII in the generator source; bodies are rendered by the project's own paper-doll rig.
* The reference images in `documentation/references/` were not traced, sampled or embedded.
* Licence: project-owned original asset (same licence as the game's own content). No third-party attribution.
* Deterministic: re-running the generator reproduces byte-identical PNGs (no randomness anywhere).

## Reproduce
```bash
py -3 -P tools/pixelgen/characters.py              # all 16 sheets + normal maps + review previews (~15 s)
py -3 -P tools/pixelgen/characters.py vendor       # one character
py -3 -P tools/pixelgen/characters.py --portraits  # additionally run the portrait generator (its owner's call)
py -3 -P tools/pixelgen/characters_check.py        # validator (exit 1 on failure)
```

## Generator scripts
| File | Role |
|---|---|
| `tools/pixelgen/characters.py` | entry point: row layout per character, `sheet.json` (incl. idle-variant metadata, ground speed), previews |
| `tools/pixelgen/chargen_core.py` | G-buffer rig renderer: OKLab hue-shifted ramps, capsules / polygons / bitmaps, height-derived normals, shading (key, contact shadows, AO, inner seams, key-side edge seams, cool rim, selective outline with convex-corner anti-aliasing, lit-edge highlight, orphan-tone cleanup, deterministic fur / knit / felt / tweed textures) |
| `tools/pixelgen/chargen_heads.py` | **new:** hand-drawn heads for all 16 characters, side / front / back + blink / talk / glance-back variants |
| `tools/pixelgen/chargen_body.py` | humanoid paper-doll (side / front / back): orientation-aware hands (hanging, reaching, raised, open palm, fist; skin / glove / mitten), sleeve cuffs, coat fold relief, collars over the neck, IK that reaches the ground at full stride |
| `tools/pixelgen/chargen_anim.py` | keyframed poses: walk 8 (uniform planted-foot travel, weight shift, secondary-motion signals), idle 8 (two-stage breathing), blink, glance back, character gestures, work loops, talk 8 (two hand beats + nod), inspect 6, interact 5, front/back walk + idle |
| `tools/pixelgen/chargen_cast.py` | the 12 round-1 characters: materials, garments, props, hooks |
| `tools/pixelgen/chargen_cast_new.py` | **new:** librarian, porter, vendor, worker_b |
| `tools/pixelgen/characters_check.py` | contract validator (schema, rows per role, origin / ground contact, clipping, normal alpha / length, heights ±1 px, variant integrity, protagonist ground speed, orphan pixels) |

`tools/pixelgen/pg.py` is used unchanged (not modified).

## Sprite sheets — `assets/characters/<id>/` (cell 32×56, origin [16,54] = feet pixel, facing right)
Every sheet ships `sheet.png` (diffuse, RGBA, binary alpha), `sheet_n.png` (OpenGL +Y-up normal map, identical
alpha) and `sheet.json` (TECHNICAL_ARCHITECTURE §4). Optional extra keys: `ground_speed` {anim: px/s};
`anims[a].variants` + `variant_gap` (one-shot rows `sprite_rig.gd` mixes into a looping idle);
`anims[v].variant_of`.

Row sets: **protagonist** = idle_side, walk_side, idle_front, walk_front, idle_back, walk_back, inspect_side,
interact_side, talk_side (the 9 contract rows, unchanged order) + blink_side, look_side, gesture_side,
blink_front · **NPC** = idle_side, walk_side, idle_front, talk_side, blink_side, look_side, gesture_side,
blink_front (+ work_side where listed). Emil's order keeps idle_side, talk_side, idle_front first.

| id | height | rows | 1964 design (silhouette keys) | gesture / work |
|---|---|---|---|---|
| `alexei` | 47 px | 13 | dark grey-brown fur ushanka, front flap up, ear-flaps loose (tie strings swing), padded dark-green coat (pocket flaps, dark buttons), grey knitted scarf, tan leather satchel on a cross strap, kirza boots with a patch | blows into his hands (breath puff) |
| `konrad` | 48 px | 13 | charcoal fedora with black band + snap brim, knee-long navy overcoat (lapels, half belt at the back, vent), ochre wool scarf with a swinging end, drafting tube on a strap, leather folder under the far arm, leather shoes | adjusts the hat brim |
| `irina` | 45 px | 8 | rust headscarf knotted under the chin, dark fringe, quilted slate dispatcher jacket with belt, rolled yellow signal flag at the back, dark skirt, felt boots with galoshes, clipboard (gestures with it while talking) | weight shift |
| `emil` | 44 px | 8 | bald crown, grey fringe, round spectacles (glint), grey moustache, open grey archive coat over a brown knit cardigan, shirt + tie, pencils in the breast pocket, stoop | pushes his glasses up |
| `worker_a` | 47 px | 9 | ushanka with flaps tied up, quilted olive telogreika with belt, padded trousers, felt boots with galoshes, canvas mittens, shovel on the shoulder | weight shift · work: warms hands |
| `babushka` | 40 px | 8 | violet headscarf with pale dots, fur collar, long dark coat, felt boots, cloth bundle; strong stoop | weight shift |
| `child_a` | 31 px | 8 | red knit hat with pompom, red scarf (tail swings), short green-grey coat, felt boots, red mittens | hops on the spot |
| `berlin_father` | 46 px | 8 | tweed flat cap, short brown coat with lapels, grey scarf, wooden crate of belongings with a folded blanket | hitches the crate up |
| `berlin_mother` | 43 px | 8 | small felt hat, auburn hair in a low bun, belted plum coat, stockings, low-heeled shoes, suitcase | weight shift |
| `berlin_child` | 31 px | 8 | navy beret, short coat, knee socks, toy bear | hugs the bear |
| `clerk` | 45 px | 8 | slicked side-parted hair, grey suit, white collar + tie, black sleeve protectors (Ärmelschoner), file folder | weight shift |
| `guard` | 48 px | 8 | grey peaked cap with black visor and a plain metal badge, belted field-grey greatcoat, stand-up collar, armband (see Insignia), tall boots, hands behind the back | rocks on his heels |
| `librarian` **new** | 44 px | 9 | grey hair in a bun, spectacles with chain, plum-heather knit cardigan over a white blouse, long dark skirt, low shoes, cloth-bound book held to the chest | pushes her glasses · work: stamps index cards |
| `porter` **new** | 47 px | 9 | navy uniform cap with gold braid, white moustache, long double-breasted navy coat with brass buttons and a watch chain, black shoes | checks his watch · work: pocket watch |
| `vendor` **new** | 44 px | 9 | dark shawl with red roses (Pavlovo-Posad style), padded telogreika, grey work apron with a tea stain, skirt, felt boots; enamel teapot | blows into her hands · work: pours tea (stream) |
| `worker_b` **new** | 47 px | 9 | dark grey ushanka tied under the chin, moustache, blue-grey telogreika with belt, padded trousers, darned felt boots, mittens | blows into his hands · work: warms hands at a fire |

Heights are within ±1 px of round 1 (validator-enforced). Walk ground speed: Alexei 34.5 px/s, Konrad
35.0 px/s (player playback = 45 / ground_speed); civilians 15–25 px/s (NPC wander playback is scaled the same
way in `npc.gd`).

Animation: walk 8 frames @10 fps (contact & down frames 1 px lower, passing & up high; opposite arm swing with
lag; coat hem, scarf ends, satchel, ear-flap strings and scarf tails lag one frame), idle 8 frames @5 fps
(two-stage breathing, no blink), variants: blink (3 f), glance back over the shoulder (10 f), character
gesture (7–10 f), talk 8 frames @7 fps (rest → lift → open-palm beat with nod → settle → second beat →
rest, mouth open/close), inspect (lean in, hand to chin, blink in the hold), interact (anticipation → reach →
hold). Light is baked character-relative (warm key from the front-top of the facing direction, cool rim on
back edges, selective outline tinted to each material's darkest hue-shifted shade) so it stays valid when
mirrored; scene lights act through the normal maps (mirroring verified, see below).

## Insignia (TECHNICAL_ARCHITECTURE §12.4)
Only the Reich building **guard** carries regime iconography, as in-world uniform detail of the coercive
apparatus (never on the protagonists or any player-side element): an armband on the near upper arm.
* `assets/characters/guard/sheet.png` (neutral, always present): grey-black band with the white pillar of the
  fictional "Reichssiegel".
* `assets/characters/guard/sheet_hist.png`: the historical red armband with white disc and black emblem (at 1x
  a 2-3 px detail). Same geometry and alpha as the neutral sheet; `sheet_n.png` and `sheet.json` serve both.
  Resolved at runtime by `Symbols.pick()` (via `LayerStack.canvas_tex` in `sprite_rig.gd`); verified in-engine
  with `--symbols=0` / `--symbols=1`.
No other character shows insignia (Soviet civilians and railway workers wear none in this slice).

## Localisation
`data/locale/de_characters.json` — `char.<id>.name`, `char.<id>.role` for all 16 ids (new: Bibliothekarin,
Pförtner, Teeverkäuferin, Gleisarbeiter) and `char.expression.<name>` (German).

## Runtime
`scripts/actors/sprite_rig.gd` (idle variants, `play_once`, soft `turn_to`), `scripts/actors/npc.gd`
(`idle_anim` override, soft turn toward the player, talk release on a resting frame, wander playback scaled by
ground speed). Tests: `tests/visual/CharLightTest.tscn` (windowed: normal-map mirroring under one lamp, both
facings), `tests/visual/CharRigSelftest.tscn` (headless logic test).

## Review images (not shipped; `_preview/` has `.gdignore`)
`assets/characters/_preview/`: `<id>_contact_3x.png`, `lineup_1x/3x/6x.png`, `lineup_front_6x.png`,
`lineup_silhouettes_3x.png`, `walk_strips_3x.png`, `walk_side_all.gif`, `<id>_walk_side_onion.png`,
`normal_relight_test.png` (incl. mirrored), `before_after_{side,front,walk}_4x.png`, `new_characters_4x.png`,
`guard_symbols_neutral_vs_hist_5x.png`.
