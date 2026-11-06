# Asset manifest — Chapter 4 part 2: cast and sound (round 10)

Area owner: cast-audio specialist · Date: **2026-11-06, round 10** · Engine target: Godot 4.7.2
Contract: `documentation/C4P2_DESIGN.md` §5 (cast: Maria Gorelowa, Hanna Adler, Kommissar Wendt, Erwin Kuhnert with
sheets + living portraits; the life sheets `guard_karsk`, `press_officer`, `stapo_civil`; the optional look
`alexei_press`) and §8 (audio brief). Extends `c4_cast_audio.md`, `c3p2_cast_audio.md`, `characters_r7.md`,
`portraits_r7.md`; everything listed there stays valid.

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (numpy + Pillow; no AI models, no
  network, no samples, no third-party art or recordings, no image or audio inputs).
* Characters: drawn on the project's own paper-doll rig (hand-drawn ASCII heads, garment hooks, keyframed poses, a
  two-link IK for Maria's shovel) and its signed-distance portrait pipeline; every face is designed for the person (no
  shared head preset).
* Sound: synthesised (noise shaping, modal impacts, grain clouds, stick-slip creaks, additive instruments, generated
  impulse responses). Every voice — the crowds, the station announcements in a Russian / a German cadence, the
  canteen radio, the bandmaster, the card players — is unintelligible by construction (`c3_audio.voice`: prosody
  profiles over random vowel targets — no words, no language). All music is composed here and quotes only the game's
  own motifs K (Karsk) and B (Berlin) from `tools/audiogen/music.py` and the bayan breath of `c4_audio.py`. The
  depot band's „Accord march“ and the dance tune on Lenz's radio are original tunes written for this round (no
  anthem, no existing march or song, no quotation); the march is a provincial band's, thin and a little out of tune in
  the cold — no cymbal, nothing triumphant: a diegetic counterpoint, never a celebration.
* Insignia (TECHNICAL_ARCHITECTURE §12.4): the neutral sheets and all portraits carry none. Only `sheet_hist.png` of
  `blockwart` (the armband: red band, white disc, one dark pixel — the guard's hist pattern of `chargen_cast.py`) and of
  `guard_karsk` (the small red star on the ushanka) carry the historical insignia; same size and alpha as the neutral
  sheet (one normal map), resolved by `Symbols.pick()` only when the player enables historical insignia. Wendt wears
  no uniform, no badge, no moustache or glasses that quote a historical perpetrator; Kuhnert has no moustache.
* Licence: project-owned original assets, no attribution needed.
* Deterministic: verified 2026-11-06 — WAVs and sheets rebuilt and md5-compared (`c4p2_spyhole`, a stair-steps variant,
  `maria/sheet.png`, `blockwart/sheet_hist.png`: identical); after the review pass a review build (`--out`) and the real
  build were md5-identical for `hanna/sheet.png`, `wendt/portrait_anim.png`, `maria/portrait.png`,
  `blockwart/sheet_hist.png`, `guard_karsk/sheet_hist.png`, `alexei_press/sheet.png`, `press_officer/sheet.png`; seeds
  derive from crc32 of the names.

## Reproduce
```bash
py -3 -P tools/pixelgen/characters_c4p2.py --portraits   # 8 ids: sheets, normal maps, hist sheets, 5 living portraits, checks
py -3 -P tools/pixelgen/characters_c4p2.py --check       # validators only (characters_check + C4P2 contract checks)
py -3 -P tools/pixelgen/characters_c4p2.py --heads       # review image of the hand-drawn heads (8x)
py -3 -P tools/audiogen/c4p2_audio.py                    # 24 WAVs + .import + analysis + numeric checks
py -3 -P tools/audiogen/c4p2_audio.py --list             # names and where each is (to be) wired
# then the shared, locked import (TECHNICAL_ARCHITECTURE §1)
```
Portraits take ~60–70 s per speaker (run ids in parallel processes: one per id). Review images:
`assets/characters/_preview/c4p2_*` (git-ignored, `.gdignore`); spectrograms `assets/audio/_preview` (git-ignored).

## Characters (`tools/pixelgen/characters_c4p2.py`: sprite specs, heads, hooks, portrait specs, runner)
Through the existing pipeline: `characters.py` (`build_sheet`, `CAST_HIST`), `characters_check.py` and the part-1
runner `characters_c4.py` (its install chain) are imported and their tables extended in memory; three scene tints
(`c4p2_depot` sodium/kerosene light over coal-black blue shadow, `c4p2_station` sodium in steam, `c4p2_court` night
blue with warm windows), the gestures `press_back`, `find_key`, `note_word`, `tug_cap`, `tug_cap_f`, `one_drag`, `fold_paper` and
the work loops `shovel`, `cards`, `smoke`, `read_paper` are added in memory; portrait specs are registered in memory in
`chargen_portrait2_cast.CAST` with five backdrops in `chargen_portrait2_paint.BG` (`c4p2_depot`, `c4p2_window`,
`c4p2_gate`, `c4p2_lodge`, `c4p2_platform`). No other generator file is changed.

| Directory | Who | Sprite (32 × 56 cells, origin 16/54) | Portrait (112², 4 expressions × 6 states) |
|---|---|---|---|
| `assets/characters/maria/` | Maria Gorelowa (34), returnee from Veltrava, Kolonne 4 | straight-backed; the green woollen headscarf tied **under the chin** (it frames the face down to the knot, the back corner falls over the nape; a strip of dark hair under its rolled edge), coal on the cheek; the thin plum-heather Western coat with its lapel and the needle glinting in it, under the issued quilted vest; felt boots a size too big, hands wound in pale linen rags (a rag band above the near hand); gesture: both hands pressed into the small of the back, a breath; **work_side: shovels coal** (scoop, lift, swing, the load thrown up into the tender — the shovel solved by IK between the hands) — plays in the level (`idle_anim`); 44 px, walks 24 px/s | a long, angular face: cheekbones high and sharp over hollow cheeks, a long straight nose with the bump of an old break, a wide thin-lipped mouth, dark deep-set eyes under thick straight brows; the headscarf with its woven check (dark bars, a thin ochre thread) tied under the chin with knot and tails, folds radiating to the knot, a centre parting of dark hair under the edge; coal on brow, cheekbone and jaw; the plum lapels inside the quilted vest, the needle with a red thread; head raised and turned further than the others; the coal stage's sodium dawn |
| `assets/characters/hanna/` | Hanna Adler (27), teacher, Konrad's sister | upright like her brother, looser and quicker; **dark-blonde** hair pinned up in a round knot high on the crown (a dark pin band under it), a round open face; a knee-length navy swing coat open at the throat over the grey cardigan, a grey-brown tweed skirt below it, dark wool stockings, laced ankle boots; the rust-red scarf thrown on loosely with **both long ends down the front** (they swing); chalk dust on the near cuff and where she wiped her hand on the coat; the key ring in her hand; gesture: the keys come up, a thumb finds the right one; wide talking hands; 46 px (the knot), walks 27 px/s | a round, open face, full cheeks, a short rounded chin, a short straight nose, freckles, a wide ironic mouth, Konrad's blue-grey eyes set wider, a pearl stud; the dark-blonde knot standing high above the crown, strands escaped at temple and nape; the navy coat, grey cardigan, round white collar, the loose rust scarf with both ends down the front, chalk on the sleeve; she faces the viewer more squarely than anyone; her own lit window behind her |
| `assets/characters/wendt/` | Kommissar Ludwig Wendt (≈ 50), Staatspolizei | heavy, broad and calm (a big chest and belly, thick legs); a **pearl-grey homburg with a black band** (Kessler's is black: inverted on purpose), dark hair grey at the temples, heavy lids, soft jowls and a double chin; the long dark-grey civilian coat with a back vent and a **wide dark-brown fur shawl collar** over the shoulders and down the front edge, a **bottle-green silk foulard** with ivory dots in the opening (no white collar, no tie), black leather gloves; the small black notebook with its pale page edge in the near hand, open when he notes a word (gesture); gestures little with the far hand; 49 px, walks 21 px/s | a heavy, broad, fleshy, clean-shaven face, soft jowls and a double chin over a thick short neck, a fleshy rounded nose, small pale eyes under heavy lids, dark heavy brows, a polite half smile; dark hair oiled back, grey at the temples; the pearl-grey homburg; the dark-brown fur shawl collar, the green foulard; head a little lowered, almost straight at the viewer; the gate passage's cold lamp. No uniform, no badge, no glasses, no moustache |
| `assets/characters/blockwart/` | Erwin Kuhnert (≈ 60), caretaker and Blockleiter | a little stooped, short quick steps; the flat cap, grey temples, a pinched face; the brown work coat buttoned over the cardigan, a belt with the big key ring (it swings), the reading glasses dangling on their string, felt slippers in galoshes; the beech card box **clamped under the near arm** at his side (idle, walk, talk, glance — never held out); gesture: a nervous tug at the cap with the free hand, a glance down the passage; **work_side: the box held open against his belly, the near hand walks the cards, pulls one and holds it up to the glasses** — plays in the level; 44 px, walks 20 px/s; `sheet_hist.png`: + the armband | a lined, pinched face, deep nose-to-mouth lines, watery pale eyes under bushy grey brows, grey stubble, the reading glasses low on the nose and their cord; the flat cap; the brown work coat over a dark green cardigan; the lodge's yellow lamp |
| `assets/characters/guard_karsk/` | a young Soviet guard (life sheet) | the long sheepskin coat with fleece at collar, front edge and hem, belted, the sling across the chest, the **rifle slung on the back: the barrel (dark steel with a lit edge and the front sight) stands clear behind the ushanka, the wooden stock runs down behind the back to the hip**; the ushanka with its flaps tied up, cold-red cheeks; gesture: blows into his mittens; **work_side: warms his hands at the barrel fire** — plays in the level; 46 px, walks 25 px/s; `sheet_hist.png`: + the red star on the ushanka | — (life sheet) |
| `assets/characters/press_officer/` | the Soviet press minder (life sheet) | a good dark-grey double-breasted city coat, a karakul pirozhok, glasses; a **tan leather briefcase clamped under the near arm** (its back half sticks out behind the coat, the brass clasp catches the light), a cigarette in the same hand (a thread of smoke between drags); gesture: one drag; **work_side: smokes** (the ember glows, the smoke breathed out, the ash tapped off) — plays in the level; 46 px, walks 23 px/s | — (life sheet) |
| `assets/characters/stapo_civil/` | the man at the kiosk (life sheet) | square-built, the black belted leather coat (glossy), the hat with its brim snapped down over the eyes, the newspaper folded in the near hand; gesture: folds it, glances; **work_side: the paper held open, a page turned, a look over its edge** — plays in the level; 48 px, walks 24 px/s | — (life sheet) |
| `assets/characters/alexei_press/` | look: Alexei for the showcase (KarskB) | `chargen_cast.alexei` made presentable: the **ushanka's flaps tied up on the crown** (ear, cropped dark hair and the clean-shaven jaw show), a **new cream-white wool scarf** with its end lying over the jacket front; Alexei's 15 rows (rows and lengths unchanged, silhouette IoU 0.96) + `carry_side` / `carry_idle_side` with Ekdahl's red guidebook under the near arm (`c4p2.json` carry of KarskB); 47 px, walks 34.5 px/s like Alexei. Shown in game once `c4p2.json` has `"looks": {"L_C4P2_KarskB": {"alexei": "alexei_press"}}` (story's line; integration patch) | Alexei shaved (no stubble), the ushanka's flaps tied up, the new cream wool scarf wound over the quilted jacket instead of the grey roll-neck; the showcase's floodlights |

Rows: the four speakers ship the part-1 NPC rows (`idle_side, walk_side, idle_front, talk_side, blink_side, look_side,
gesture_side, blink_front, talk_front`), Maria and Kuhnert `work_side` appended; the life sheets `idle_side, walk_side,
talk_side, blink_side, look_side, gesture_side, work_side` (side rows only, `talk_side` for exploration chats).
Silhouettes: IoU of idle_side frame 0 ≤ 0.90 against each other and 24 existing figures; faces: > 1200 of 1936 samples
differ from each other and 15 existing speakers (`tests/test_c4p2_cast_audio.gd`).

### Round 10 art review (second pass, 2026-11-06) — what changed and why
The review found twins, unused work loops and costume details that did not read at 1x. Fixed in the generator:
* **No twins.** Hanna was Elena recoloured (same face, brown centre-parted hair, red scarf at the throat, slim dark
  coat): now dark-blonde with a high knot, a round freckled face that faces the viewer, a knee-length navy swing coat
  over a tweed skirt, the rust scarf loose with both ends down the front. Wendt was Kessler with a fur collar: now
  heavy and broad, a pearl-grey homburg (Kessler's is black), dark hair with grey temples, a wide fur shawl collar and
  a green silk foulard instead of the white collar and black tie. Maria's portrait used Irina's nape-tied cap shape:
  now the headscarf is tied under the chin (knot, tails, folds, a woven check, hair under the edge) in portrait and
  sprite, and her face is long and angular with an old break in the nose. Checked: the sprite head colours of the
  pairs differ by 107 / 144 / 66 (were 36 / 25 / 57) and the portraits' cell colours by 42 / 48 / 46 (were 26 / 27 /
  40) — `cast_no_twins_of_the_review` (thresholds 60 / 40).
* **The work loops play.** `L_C4P2_Karsk.tscn` (MariaCoal, GuardCoal, MinderCanteen) and `L_C4P2_Berlin.tscn`
  (ShadowKiosk, KuhnertGate) set `idle_anim = "work_side"` (one-line insertions) — `cast_work_loops_play_in_the_levels`.
* **Details that read.** The minder's briefcase (it was hidden behind the coat) is clamped under his arm; Kuhnert
  carries the card box under his arm (it was held out like a tray; the work loop holds it against his belly); the
  guard's rifle stands clear of the ushanka with a lit edge; Maria's needle has its own glint and her rag-wrapped hands
  are pale linen; Hanna's chalk is a dusty streak drawn over the sleeve (it was hidden under the arm); Wendt's notebook
  shows its pale page edge. The generator's `check_props()` renders every listed frame with and without the prop's hook
  and fails if the prop shows fewer pixels than required (or, for the card box, if it reaches out in front of him).
* **The look reads.** `alexei_press` ties the ushanka's flaps up and wears a cream scarf (39 px of idle_side frame 0
  differ from Alexei, silhouette IoU 0.96 — the same person); the portrait matches. It appears in game only with the
  `looks` line in `c4p2.json` (integration patch for the story owner).

## Sound (`tools/audiogen/c4p2_audio.py`; levels: the round-8 windows; loops seamless with `smpl` chunks)
| File | What | Wiring |
|---|---|---|
| `amb/amb_karsk_depot.wav` (60 s loop) | the depot before dawn: Kolonne 4 shovelling in a ragged line (six workers, each with its own rhythm and rests), a standing engine's blower and its safety valve lifting twice, the guard's barrel fire, a yard dog, the canteen radio behind a window, sparrows in the eaves, a fitter's hammer, couplings bumping, a goods train passing behind, boots on frozen cinders | `L_C4P2_Karsk.tscn` ambience; c4p2.json KarskA; LS_C4P2_Depot p1 |
| `amb/amb_karsk_platform.wav` (60 s loop) | platform 1 in the evening: the depot band rehearsing the Accord march across the tracks (breaks off on a cracked note, two baton taps, the bandmaster's voice, again from the top; later a second strain), the express's air pumps and a steam leak, announcements in a Russian cadence after a two-tone chime, the crowd (officials, press, workers), snow ticking on the iron canopy and two slides of it, steps in the snow, a camera shutter | c4p2.json KarskB; LS_C4P2_Book b4 |
| `amb/amb_berlin_station.wav` (60 s loop) | the Ostbahnhof under glass at night: the hall's long echo, announcements in a German cadence after a three-tone gong, the express's steam and air pump, two luggage carts, steps on stone, pigeons in the roof, the kiosk's counter bell, cutlery and cups in the dining car, a tram ringing on the forecourt | `L_C4P2_Berlin.tscn` ambience; c4p2.json BerlinA; LS_C4P2_Steam m4 |
| `amb/amb_berlin_courtyard.wav` (60 s loop) | the courtyard of No. 14 at night: Lenz's radio (an original slow foxtrot through a valve set and the window glass), the Schulz baby fussing for a moment, a card game behind another window, a dog far off, the S-Bahn crossing its viaduct twice, wind whistling in the gate passage, a gutter dripping into the yard (now and then onto the rain barrel), a window shut, a chain in the back house, and under everything the Hall's distant hum | c4p2.json BerlinB; LS_C4P2_Express x4 |
| `music/mus_c4p2_karsk.wav` (loop, 45 bpm, 64 beats, 85.3 s) | the bayan breath of part 1, slower (four breaths: Dm, Bb colour, Dsus2, an open A–E), over low strings in D Aeolian; K returns augmented in the cellos (the question only); three felt-piano notes; a high harmonic into the loop. Against it in KarskB the band of `amb_karsk_platform` plays in F major — the same notes, the other face of them | level + c4p2.json KarskA/KarskB; LS_C4P2_Depot p2 |
| `music/mus_c4p2_berlin.wav` (loop, 63 bpm, 64 beats, 61.0 s) | piano and low strings in G Aeolian: the clockwork pulse of part 1 (3+3+2 on a muted piano) softer and slower, the machine tick only on downbeats, low strings instead of the brass, a viola counter-line, B on the piano | level + c4p2.json BerlinA/BerlinB; LS_C4P2_Steam m4 |
| `music/mus_c4p2_clock.wav` (one-shot cue, 24.5 s; NOT in `LOOPING_MUSIC`) | LS_C4P2_Clock from its first frame: the tick on every second 0–19 s; k1 the clockwork pulse and B on the celesta, k2 the drone under the G pedal, k3 the bayan and K on the felt piano, k4 K's answer and B's close (Eb bent to E) ending on the last tick; k5 (20 s) the tick never comes, a low D–G dyad dies away, silence from 22.6 s. Shot times `CLOCK_SHOTS` = the registered shots (test-checked) | LS_C4P2_Clock (cine stream): `{"t": 0.0, "music": "mus_c4p2_clock"}` |
| `sfx/c4p2_halves_snap.wav` | the German half slid home against the Russian one, its edge stopping, the palm pressing the card flat | JoinPuzzle: the solving moment (integration patch) |
| `sfx/c4p2_tooth_1..3.wav` | one tooth seating in its notch: a tiny crisp card click (random variants) | JoinPuzzle `_reveal_click`, five of them 0.14 s apart (integration patch) |
| `sfx/c4p2_stamp_close.wav` | a soft press, then two brass tones a quarter-tone apart beating slower and slower until they meet in one (one card, two halves) | JoinPuzzle `_reveal_ring` (its fallback chain asks for it) |
| `sfx/c4p2_shutter.wav` | Ekdahl's rangefinder: the cloth shutter's double tick, the film advanced with the lever (within the 0.6 s between his two photographs) | JoinPuzzle `_photo` (asked for) |
| `sfx/c4p2_steps_1..3.wav`, `sfx/c4p2_steps_down_1..3.wav` | three careful steps on old wooden stairs at night (soft soles, the treads answering, one creak, the sole scuffing the worn edge), up slower and heavier, down quicker; random variants | HousePuzzle `_walk` sets off (asked for); DOWN moves (integration patch) |
| `sfx/c4p2_attic_door.wav` | the drying loft's plank door: thumb latch, a long careful hinge squeal, the door against a beam, the cold loft's draught, a pigeon flapping off | HousePuzzle: moves into / along the lofts (integration patch) |
| `sfx/c4p2_spyhole.wav` | behind Frau Pohl's door the brass spy-hole cover slides aside, a click, a floorboard under her slipper | HousePuzzle: the Probegang stops at `s2` (integration patch) |
| `sfx/c4p2_door.wav` | they are down: the bolt drawn on Pietsch's cellar door, the heavy door dragged over the stone sill, the cellar's hollow answer | HousePuzzle `_reveal_workshop` (asked for) |
| `sfx/c4p2_pencil.wav` | Konrad's red pencil ringing the workshop on the plan: the lead dragged round once, the grain following the curve, a tap where it closes | HousePuzzle `_reveal_circle` (asked for) |
| `sfx/c4p2_knock.wav` | a knuckle against the stairwell wall, softly | HousePuzzle `_no_way` (asked for) |

The SFX ids are the ones the puzzle UIs already ask for in their `Kit.ui_sound_first` fallback chains (round 10's
`join_puzzle.gd` / `house_puzzle.gd`), so six of them are heard without any patch; the other five are wired by the
lead (integration notes of the cast-audio stream).

`scripts/core/audio.gd`: `LOOPING_MUSIC` += `mus_c4p2_karsk`, `mus_c4p2_berlin` (one-line edit; the cue stays a
one-shot so its tick can stop). Tests: `tests/test_c4p2_cast_audio.gd` (15 cases: sheets, rig, living portraits, life
sheets and hist variants, the look, silhouettes and faces, no twins of the review, the work loops in the level shells,
names and speakers, WAV format / loops / import, levels and
seams, registry and variants, the clock cue on the film's registered shots, wiring, a pending report of the puzzle UIs
and the Clock film that do not call these sounds yet).
