# Asset manifest — characters, round 7 (Chapter-3 cast finished, talk_front, soft turns, grounded front walks)

Area owner: characters specialist · Date: **2026-11-06, round 7** · Engine target: Godot 4.7.2
Extends `characters.md` (round 2, still valid for everything not listed here). Portraits: `portraits_r7.md`.

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (Pillow + numpy; no AI image
  models, no network, no third-party art, no image inputs). Heads, hats, hands, boots and props are hand-designed
  pixel maps written as ASCII in the generator source; bodies are rendered by the project's own paper-doll rig.
* Licence: project-owned original asset. No third-party attribution. No regime insignia on any new sprite (the
  border officer's cap badge is the Free City's bridge, the conductor's the railway's winged wheel).
* Deterministic: re-running the generators reproduces byte-identical PNGs and JSON (verified 2026-11-06: all 23
  sheets rebuilt into a scratch directory, 0 differing files; `sheet.json` is now always written with LF).

## Reproduce
```bash
py -3 -P tools/pixelgen/characters.py               # the 16 round-1/2 sheets (+ previews)
py -3 -P tools/pixelgen/characters_c3.py            # the 7 Chapter-3 sheets, then both validators
py -3 -P tools/pixelgen/characters_c3.py --check    # validators only (characters_check + C3 contract)
py -3 -P tools/pixelgen/characters.py --out=DIR     # review run (writes DIR/assets/characters)
```

## What changed
| Item | Before | Now |
|---|---|---|
| Chapter-3 generator (`chargen_cast_c3.py`, `characters_c3.py`) | written against the round-1 rig (`digit_legend`, `faces`, `hand_bitmaps`, first-gen portrait API) -- did not import any more, the sheets were frozen round-1 art | ported to the round-2 API: chargen_heads-format heads (`HD.head_views`, side + front, blink / talk / glance-back variants), `make_hands` (Kessler: gloves), round-2 materials / textures (tweed, knit, fur) |
| Chapter-3 rows | 6-frame idle, 4-frame talk, 2-4 rows, front view only for 3 of 7 | 9 rows each: `idle_side` (8, two-stage breathing), `walk_side`, `talk_side` (8: two beats + nod, per-frame hands / head), `idle_front`, `blink_side`, `look_side` (glance back), `gesture_side`, `blink_front`, `talk_front`; the first-contract rows keep their old order |
| Chapter-3 gestures | none | Elena tucks a strand behind her ear, the officer rocks on his heels, the conductor touches his cap, Voronova straightens her collar, Kessler straightens up, Frau Brunner reads her pad, Ekdahl jots a note (`chargen_anim.GESTURES`: `tuck_hair`, `touch_cap`, `straighten`, `read_pad`, `jot`) |
| Voronova | grey checker "karakul" that read as grey hair | dark brown karakul pirozhok with curl tips, grey hair under it, grey-brown karakul collar |
| Front long coats (Elena, Kessler) | lower front lit like an apron | calmer hem below the waist (`calm_front_hem`) |
| `talk_front` (all NPCs with a front view) + `talk_back` (protagonists) | did not exist (`talk_front` fell back to `talk_side`) | 8 frames: the free forearm rises in front of the body with an open hand, beat + nod, talking mouth; back view: the elbow moves out (a hand in front of the body would be hidden); per character `talk_front_arm` keeps props in the other hand (Berlin father: nod only) |
| `walk_front` / `walk_back` | planted foot travelled 0.5-2 px up in depth -> the whole figure floated 1-2 px above the origin mid-stride | the supporting foot stays on the origin row for the whole stance, frames 0 / 4 are double support (validator now checks these rows too) |

New rows are **appended** to the round-2 sheets (protagonists: rows 13-14, NPCs: last row), so every existing row
keeps its index (verified: only `walk_front` / `walk_back` of Alexei / Konrad changed pixels; the leaflet
mini-game's Konrad crop, the hall people and the cinematics read rows by name).

## Files — `assets/characters/<id>/` (cell 32x56, origin [16,54], facing right)
| id | rows | height | notes |
|---|---|---|---|
| `elena` | 9 | 44 px | charcoal coat, wine-red scarf, armband (white + slate stripe), notebook; gesture `tuck_hair` |
| `border_officer` | 9 | 48 px | slate-blue greatcoat + belt, peaked cap with the bridge badge, armband, stamp; `rock_heels` |
| `conductor` | 9 | 46 px | navy uniform coat, brass buttons, railway cap (winged wheel), white walrus moustache, bag, punch; `touch_cap` |
| `voronova` | 9 | 45 px | dark-brown coat, karakul pirozhok + collar, leather folder; `touch_collar` |
| `kessler` | 9 | 49 px | charcoal overcoat, homburg, gloves, briefcase, rimless glasses; `straighten` |
| `typist` | 9 | 44 px | oatmeal cardigan, blouse collar, sleeve protectors, steno pad, pencil behind the ear; `read_pad` |
| `journalist` | 9 | 48 px | tweed overcoat, blue scarf, camera on a strap, notebook; `jot` |
| round-2 cast | +1 (`talk_front`), protagonists +2 (`talk_front`, `talk_back`) | unchanged | |

## Runtime (round 7)
* `scripts/actors/sprite_rig.gd`: `view_hint` ("front" / "back": `*_side` requests play the matching view row if
  the sheet has it -- dialogue code keeps asking for `talk_side` / `idle_side`); `turn_to(left, hold, row)` with an
  in-between row (`walk_front` keeps the stride), the turn frame survives row changes, turning back mid-turn cancels;
  `talk_back` falls back to `idle_back`.
* `scripts/actors/player.gd`: soft turns (0.12 s on the spot, 0.07 s while walking, movement still reverses at
  once; `face(dir, false)` = instant), `face_point()` turns towards the NPC named by the interactable's `npc_id`
  (oblique levels: towards / away from the camera when it stands clearly below / above), `_set_dir` keeps the rig's
  `view_hint` in step; `get_view()`.
* `scripts/actors/npc.gd`: front-on idles (`idle_anim = "idle_front"`) talk front-on unless they turn to the
  player; talk release accepts any talk row; wanderers turn softly while pausing at the ends of their path.

## Tests
`tests/test_characters_r7.gd` (unit, run_all): C3 rows / frames / variants / normal maps, talk_front everywhere a
front view exists, contract row indices, front / back walks grounded in every frame, living portraits for all 17
speakers, rig view hint + turns, player soft turn + facing view, front-on NPC talk.
`tests/visual/CharRigSelftest.tscn` (headless, extended: 23 ids + the round-7 behaviours),
`tests/visual/CharLightTest.tscn` (normal-map mirroring, run with the C3 ids: PASS),
`tests/visual/char_lineup.tscn` (new: real Main scene, any level, a row of characters idle / talking / front-on),
`tests/visual/char_portraits.tscn` (new: the real DialogueBox for all 17 speakers, mouth / blink / expression checks).

## Review images
`documentation/screenshots/characters_r7_before.png`, `characters_r7_after.png` (same layout: idle side, idle
front, talk beat, front / back walk with the origin line, 17 portraits), `characters_r7_ingame_station.png`,
`characters_r7_ingame_palais_talk_front.png`, `characters_r7_dialogue_elena.png`; generator previews in
`assets/characters/_preview/c3_*` (`.gdignore`).
