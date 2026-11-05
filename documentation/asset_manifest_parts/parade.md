# Asset manifest part — parade (L_M1_Parade, 2026-11-05)

Second Great Hall cinematic, played right after `L_M1_HallReveal`: later that day the regime stages a military
parade on the plaza in front of the Great Hall. Mode C (3D pixel render, low-res world path), palette `berlin`,
47 s, 8 shots with hard cuts. All assets are original and generated deterministically by the scripts below
(licence: project-owned, no third-party material, no downloads).

## Scene and code
| Path | Content |
|---|---|
| `scenes/levels/L_M1_Parade.tscn` | root `Node3D` (script `parade_level.gd`), exports `level_id` L_M1_Parade, `mode` 3d, `protagonist` none, `grade_preset` hall_3d, `ambience` amb_berlin_street, `music` mus_parade |
| `scripts/levels/parade/parade_level.gd` | API like the reveal: `signal finished` (once), `signal cue(key)`, `play/skip/seek/set_paused/set_fade/get_time/get_duration/get_shot_id`; reuses `hall_builder.gd`, `hall_people.gd`, `hall_camera_rig.gd`, `pixel3d_post.gdshader` read-only; `own_sfx` plays the `parade.sfx.*` cues via `Audio.sfx("parade_*")` |
| `scripts/levels/parade/parade_shots.gd` | shot table p1–p8 (un-rotated camera, lens-shift tilts, eased moves, hard cuts) |
| `scripts/levels/parade/parade_set.gd` | tribune, barrier, loudspeakers, 27 searchlight pillars, 7 vehicles (4 tanks, 3 half-tracks), 5 jets, MultiMesh crowd (~13.9k), formations (1.8k), 6 marching blocks (720), guards, officials, dust puffs, cold spot lights |
| `assets/architecture/parade/parade_figures.gdshader` | MultiMesh billboard shader: per-instance LOD strip chosen from the projected height, feet snapped to whole pixels, 1 texel = 1 px (largest strip may scale ×2–3 for foreground silhouettes), toon light, flag 0.55 |

## Generated art — `tools/pixelgen/gen_parade.py` (`py -3 -P tools/pixelgen/gen_parade.py`)
| File | Content |
|---|---|
| `assets/architecture/parade/figures.png` + `figures.json` | 1368×399 atlas, 13 LOD strips (figure height 2–104 px) × 18 slots: marching soldier profile (4 frames), soldier front, guard front, 6 civilians from behind, child with limp flag, 2 grey officials, 3 dust puffs. Faces of troops = shadow band (anonymous) |
| `assets/architecture/parade/flag_limp.png` / `flag_limp_hist.png` | the child's limp hand flag (neutral cloth / historical variant via `Symbols.pick`) |
| `assets/architecture/parade/sky_parade.png`, `fog_parade.png` | 1024×720 cold overcast dusk matte and cold fog gradient (same screen mapping as the hall's sky, anchor 512,430) |

Insignia (§12.4): tribune, portico and march banners use the hall builder's Symbols-resolved materials
(`banner_portico`, `flag_street`); neutral mode shows the fictional Reichssiegel. No SS runes, no salutes.

## Generated audio — `tools/audiogen/parade_audio.py` (`py -3 -P tools/audiogen/parade_audio.py`)
| File | Length | Content |
|---|---|---|
| `assets/audio/music/mus_parade.wav` | 47.0 s one-shot | cold drum pulse (57 bpm bass drum, dry side-drum figure) over a low brass C/Db drone, tritone at the tribune, heartbeat in the crowd shot, silence under jets/Konrad, distant echo over the cleared street |
| `assets/audio/sfx/parade_boots.wav` | 6 s | boots in step on packed snow |
| `assets/audio/sfx/parade_tanks.wav` | 7 s | diesel rumble, track clatter, rattling window glass |
| `assets/audio/sfx/parade_jets.wav` | 5 s | low jet formation pass |
| `assets/audio/sfx/parade_pa_chime.wav` | 2.4 s | two-tone loudspeaker gong with plaza echo |

## Text — `data/locale/de_parade.json`
Loudspeaker lines (`parade.cue.loudspeaker_1..4`), Konrad's inner voice (`parade.cue.konrad`), sound-cue labels,
shot titles.

## Tests — `tests/visual/parade_harness.tscn` / `.gd`
`--selftest` (headless): finished once (end + skip), skip idempotent, cues complete/in order with locale text,
7–9 shots, 40–50 s, seek, banner texture follows `Symbols.enabled()`, viewport settings restored.
Windowed: frames of every shot (`--out=DIR --symbols=0|1`), exact palette check, `--realtime=47` frame cost.
