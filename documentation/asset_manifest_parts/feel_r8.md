# Asset manifest — Feel & polish pass, round 8 (area: feel_r8)

Owner: feel_r8 specialist · Date: 2026-11-06 · Engine: Godot 4.7.2. Everything below is **original work** made by
project scripts from the game's own art pipelines (no downloads, no traced or sampled material, no AI image/audio
models). All generators are deterministic (fixed seeds / pure colour and geometry rules) and rewrite byte-identical
files. No asset of this round carries an insignia.

## 1. Ambient walkers (Palais, station, Berlin reading room)
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/environments/veltrava_hall/walkers/secretary.png` | 320×504 RGBA (sheet of `typist`) | `tools/pixelgen/walkers_r8.py` | Delegation secretary: navy cardigan, blue-black hair, dark skirt. |
| `assets/environments/veltrava_hall/walkers/pressman.png` | 320×504 (sheet of `journalist`) | same | Second press man: grey tweed coat, dark hair, burgundy scarf. |
| `assets/environments/veltrava_hall/walkers/delegate.png` | 320×504 (sheet of `clerk`) | same | Elderly delegate with his files: dark brown suit, grey hair, navy tie. |
| `assets/environments/veltrava_station/walkers/traveller_woman.png` | 320×504 (sheet of `berlin_mother`) | same | Traveller with her suitcase: bottle-green coat, brown felt hat, dark hair. |
| `assets/environments/veltrava_station/walkers/traveller_man.png` | 320×504 (sheet of `berlin_father`) | same | Traveller carrying a crate: grey-blue coat, dark cap, camel scarf. |
| `assets/environments/veltrava_station/walkers/porter.png` | 320×504 (sheet of `porter`) | same | Veltrava station porter: brown uniform, dark hair, ruddy skin. |
| `assets/environments/berlin_archive/walkers/reader.png` | 320×504 (sheet of `clerk`) | same | Older reader: brown tweed jacket, grey hair. |
| `assets/environments/berlin_archive/walkers/student.png` | 320×504 (sheet of `typist`) | same | Student: wine-red cardigan, fair hair. |
| `assets/environments/<env>/walkers.json` (3) | JSON | hand-written data | Paths, speeds, pauses, give-way settings; schema in `scripts/actors/ambient_walker.gd`. |

Method: `walkers_r8.py` calls the existing cast function (`chargen_cast` / `chargen_cast_new` / `chargen_cast_c3`) with a
few entries of its material table swapped (same keys and order → same material indices) and renders the rows of the
shipped `sheet.json` through `chargen_body.render`. The tool checks that the unmodified pipeline reproduces every source
sheet byte for byte (`--check`) and that every variant's silhouette is identical to its source, so the runtime reuses
the character's own `sheet_n.png` and `sheet.json`; only the diffuse changes. Runtime: `scripts/actors/ambient_walker.gd`
+ `scenes/actors/AmbientWalkers.tscn` (one actor entry in each `scene.json`).

## 2. Station side-task payoff („Wagen drei ist kalt“)
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/environments/veltrava_station/thaw/car3_thaw.png` (+ `_n`, `_e`) | 820×19 RGBA, 5 frames of 164×19 | `tools/pixelgen/env_veltrava_station_thaw.py` | Window band of car 3 (layer `train_near` x 357..520, y 25..43): frame 0 = the painted layer (no seam), 1-3 the frost recedes from the top (hash-dithered edge), 4 thawed: lamp on in compartment 4 (typists, coats off), compartment 5 coat on the hook, compartment 6 the man with his samovar tea. `_n` = crop of `train_near_n.png`, `_e` = lit glass glow like `train_near_e.png`. |
| `assets/environments/veltrava_station/thaw/car3_peephole.png` (+ `_n`, `_e`) | 180×19 RGBA, 10 frames of 18×19 | same | Window 6 incl. its frame: frosted, a blurred hand wipes a circle (4 frames), a face, waving with the raised palm of `actors/window_life.png` frame 3 (2 frames), face, hand down. |

Palette: only colours already painted in the car-3 windows (veltrava ramps). Runtime: `scripts/levels/veltrava_station/
station_thaw.gd` + `scenes/levels/veltrava_station/StationThaw.tscn` (actor in the station `scene.json`); the pipe knock
reuses `assets/audio/sfx/berlin_radiator_knock.wav`.

## 3. Portraits of the evicted Berlin family
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/characters/berlin_father/portrait.png`, `portrait_anim.png`, `portrait.json` | 448×112 strip, 448×672 grid | `tools/pixelgen/chargen_portrait2.py berlin_father` (spec in `chargen_portrait2_berlin.py`) | Tired forties: grey tweed flat cap (new SDF builder `flat_cap`, no badge), short dark hair, bags under the eyes, stubble; brown coat, grey knitted scarf. Four expressions × rest / talk / blink rows, like the round-2 cast. |
| `assets/characters/berlin_mother/portrait.png`, `portrait_anim.png`, `portrait.json` | same | `... berlin_mother` | Worried late thirties: small dark felt pillbox with a wine ribbon (new builder `pillbox`), auburn hair swept into a low chignon (`hair_swept` of the C3 module), plum coat, oatmeal knitted scarf. |

Both match their sprites (`chargen_cast.py`: coat, hat and hair colours) and the Berlin look of Konrad / Emil / the
porter (rim `#6e8fa6`, background `berlin`).

## 4. Voronova's hat edge
`assets/characters/voronova/sheet.png` (only this file changed; `sheet_n.png` and `sheet.json` are identical): the
lowest row of the karakul pirozhok uses the light curl-tip tones (hat ramp 5/4 instead of 1/2) in the side and front
head bitmaps, a 1-px lighter fur edge so the hat no longer merges with her grey hair at 1×. Patched in memory by
`tools/pixelgen/characters_c3.py` (`voronova_hat_edge()`, called from `install()`); run
`py -3 -P tools/pixelgen/characters_c3.py voronova`.

## 5. LS_C3_Trains t3 — the Soviet compartment
`assets/cinematics/ch3/trains/int_alexei.png` and `roomflare_a.png` only (`py -3 -P tools/pixelgen/env_veltrava_cine.py
--only t3`): a pleated pelmet with scalloped hem and red cross-stitch band, curtain tie-backs and lace edges, the lower
berths with leatherette buttons and piping, made-up bedding on the right berth (folded blanket with the red stripe,
white pillow, paper-wrapped linen), Alexei's kit bag, folded blankets on the upper berths, a carpet runner, a second
(empty) tea glass in a filigree holder with the spoon standing in it; the room flare of the passing station lamp now
throws the warm, skewed window (with the sash shadow) over the right curtain and wall and a band across the ceiling.
The glass opening is untouched (t2 match cut), timing unchanged (25.5 s).

## 6. Text
`data/locale/de_feel_r8.json`: the two reasons a main-menu memory cannot be opened (no recorded state / incomplete
record); the save-check reasons come from `de_system.json` (`sys.save.err.*`).
