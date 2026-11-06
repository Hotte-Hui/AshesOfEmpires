# Asset manifest — Feel & polish pass 2, round 9 (area: feel_r9)

Owner: feel_r9 specialist · Date: 2026-11-06 · Engine: Godot 4.7.2. Everything below is **original work** made by
project scripts from the game's own art pipelines (no downloads, no traced or sampled material, no AI image/audio
models). All generators are deterministic (fixed seeds / pure colour and geometry rules) and rewrite byte-identical
files; a re-run of a changed generator was diffed against the previous output — only the files listed here changed.
No asset of this round carries an insignia.

## 1. Walker rigs (front / back walks) and the quay walkers
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/environments/<env>/walkers/<name>_rig.png` + `_rig_n.png` + `_rig.json` (13 × 3) | 320×672 / 320×728 RGBA (the source's rows + 3) | `tools/pixelgen/walkers_r8.py` | Own sheet per walker: the source character's rows (same order, frames, timing, silhouette — checked) plus `walk_front`, `idle_back`, `walk_back` from the same body pipeline; own normal map. Back heads are derived from the front head bitmap (`back_head()`: hair or headscarf down to the nose row, the nape below). |
| `assets/environments/veltrava_quay/walkers/fireman_rig.*` | (sheet of `worker_b`) | same | Veltrava fire brigade: dark tunic, glossy grey helmet with a brass comb, leather gloves. |
| `assets/environments/veltrava_quay/walkers/resident_rig.*` | (sheet of `worker_a`) | same | A man from the old town woken by the fire: brown coat over pyjama trousers, grey hair; points at the fire. |
| `assets/environments/veltrava_quay/walkers/clerk_files_rig.*` | (sheet of `clerk`) | same | Commission clerk carrying rescued folders: dark coat, grey hair. |
| `assets/environments/veltrava_quay/walkers/old_woman_rig.*` | (sheet of `babushka`) | same | Old woman, red-brown headscarf, blue-grey coat. |
| `assets/environments/veltrava_quay/walkers/policeman_rig.*` | (sheet of `conductor`) | same | City policeman: green-grey uniform and cap, silver buttons (not the commission's blue). |
| `assets/environments/veltrava_quay/walkers.json` | JSON | hand-written data | Five walkers in the lane y 295 (x 446–700, 846–1022, 1452–1880), clear of the engine, the bench, Konrad, the trestle, the cars and every story spot. |

The round-8 diffuse variants (`walkers/<name>.png`) stay byte-identical and are still referenced as `"sheet"` (fallback).

## 2. Cinematic figures (LS_C3_Escape e3a / e3b, LS_C3_Halves h1)
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/cinematics/c3p2/escape/e3a_hands.png` | 2080×360 RGBA (4 frames 520×360) | `tools/pixelgen/env_c3p2_cine_hands.py` (`e3a_frame`) via `env_c3p2_cine_fire.py` | Alexei's sooty hand out of the coal hatch (quilted green sleeve, stitched channels), Konrad's navy sleeve and shirt cuff, his hand taking the wrist; lit from below by the hatch glow (local light falloff), the cold lamp as rim. |
| `assets/cinematics/c3p2/escape/e3b_men.png` | 1120×96 (2 frames) | `env_c3p2_cine_hands.py` (`lying_men`) + the file painted in `env_c3p2_cine_fire.py` | Both men on their backs in the snow: the cast heads of the portrait specs (Alexei's ushanka, Konrad's hair, his fedora beside him), coats, trousers, boots, one knee up, chest heave; a trodden contact shadow. |
| `assets/cinematics/c3p2/halves/arms.png` | 660×220 (3×2 frames 220×110) | `env_c3p2_cine_hands.py` (`arm_frame`) via `env_c3p2_cine_quay.py` | Reaching arms from the bench figures' shoulders (measured on their silhouettes) to the near / far stacks and back to the lap, in the bench figures' fire light. |
| `assets/cinematics/c3p2/halves/glyphs.png` | flap atlas | `env_c3p2_cine_quay.py` | Ä / Ö / Ü flaps keep their dots (pixfont_umlauts). |
| `assets/cinematics/c3p2/layout.json` | JSON | `env_c3p2_cine.py` | `escape.e3b_breath` moved to the new faces. |

Method: signed-distance sculpting and the material / light / outline / rim painting of the dialogue portraits
(`chargen_portrait2_*`, imported read-only); hands are built from a palm, two-segment fingers and a thumb (curl, spread,
grip); renders are memoised in the system temp dir (`ashes_c3cine_cache`, key = pipeline sources + call).

## 3. Distinct umlauts in the small pixel capitals
`tools/pixelgen/pixfont_umlauts.py` (new; `--preview=DIR` writes an old/new contact sheet): Ä / Ö / Ü use one row above
the cap line for the dots, a blank row, the letter one row shorter. Installed (opt-in, `overhang=True`) in
`explore_berlin.py` (`Canvas.text`, every Berlin and plaza close-up), `env_berlin_kit.py` (`text_mask(..., overhang)`,
used by `env_berlin_docs.label`), `gen_ui_c3.py` (protocol documents), `mg_r7_kb_lib.py` (`draw_text`, Rohrpost) and the
LS_C3_Halves flap atlas. Re-generated (only the umlaut pixels changed, 4–40 px per image):
`assets/explore/berlin/{lib_hidden, lib_shelf_3, lib_shelf_4, lib_shelf_5, master_plan(_hist), mouse, notice, photo,
pneumatic_tube, poster_aufbau(_hist), radio}.png`, `assets/explore/plaza/{family_door(_hist), tram_stop}.png`,
`assets/ui/documents/berlin_plan_{a,a_hist,a_lines,a_lines_hist,b,b_hist,b_lines}.png`,
`assets/ui/documents/veltrava_protocol_{seating,booth_log}.png`, `assets/ui/minigames/rohrpost/find_capsules.png`.
World backgrounds with umlaut signs (Berlin hall „PFÖRTNER“, palais „PROTOKOLLBÜRO“, station „BÜRO FÜR RÜCKFÜHRUNG“)
were not re-generated (their generators keep the old glyphs unless they pass `overhang=True`).

## 4. Data
`data/explore/quay_tasks.json` + `data/locale/de_quay_tasks.json` — side task „Eine Decke für Frau Brunner“ (hand-written
text, German typography checked by `tests/test_feel_r9.gd`).
