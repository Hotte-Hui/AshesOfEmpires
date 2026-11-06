# Asset manifest — Chapter 3 part 2: cast looks and sound (round 8)

Area owner: c3p2 cast/audio specialist · Date: **2026-11-06, round 8** · Engine target: Godot 4.7.2
Contract: `documentation/C3P2_DESIGN.md` §6 (characters: existing ids only, a soot look for the fire scenes and the
quay, a carry row with the file, Frau Brunner in her coat over the nightdress) and §8 (audio). Extends
`characters_r7.md`, `portraits_r7.md` and `c3.md` (Veltrava sound); everything listed there stays valid.

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (numpy + Pillow; no AI models, no
  network, no samples, no third-party art or recordings, no image or audio inputs).
* Characters: the looks are rendered by the project's own paper-doll rig and portrait pipeline from the base
  characters' own specs (same poses, same heads) plus hand-chosen soot ramps, smear positions and costume parts.
* Sound: synthesised (noise shaping, modal impacts, stick-slip creaks, additive instruments, generated impulse
  responses). Voices are unintelligible by construction (prosody profiles over random vowel targets — no words, no
  language, no real broadcast). The night waltz and the interval signal are original compositions (the interval
  signal is the game's own two-language motif V). The 1964 brigade horns are a generic two-tone of a fourth, not a
  recording or a brand.
* Licence: project-owned original assets, no attribution needed. No insignia on any new sprite.
* Deterministic: every generator reproduces byte-identical files (verified 2026-11-06: all 32 WAVs rebuilt and
  md5-compared; all 18 look files rebuilt into a scratch directory and byte-compared).

## Reproduce
```bash
py -3 -P tools/pixelgen/characters_c3p2.py --portraits   # 3 looks: sheets, normal maps, living portraits, checks
py -3 -P tools/pixelgen/characters_c3p2.py --check       # validators only (characters_check + look contract)
py -3 -P tools/audiogen/c3p2_audio.py                    # 32 WAVs + .import + analysis + numeric checks
py -3 -P tools/audiogen/c3p2_audio.py --list             # names and where each is wired
# then the shared, locked import (TECHNICAL_ARCHITECTURE §1)
```
**Re-run `characters_c3p2.py --portraits` whenever `alexei`, `konrad` or `typist` (sheet or portrait) change** —
the looks derive from them and must keep the same silhouette (checked).

## Characters — looks (`tools/pixelgen/chargen_cast_c3p2.py`, `chargen_portrait_c3p2.py`, runner `characters_c3p2.py`)
A *look* is a sheet directory, not a character: dialogue speaker and NPC `char_id` stay `alexei` / `konrad` /
`typist`; the runtime picks the directory per scene (`data/chapters/c3.json` `"looks"` — integration notes, round 8).

| Directory | Base | What | Rows |
|---|---|---|---|
| `assets/characters/alexei_soot/` | `alexei` | after the smoke: blackened coat hem (ragged 2–4 px band under a 3-px dust band), sooty cuffs and hands, smoke-grey face with two dark smears (cheek, jaw), coal dust on the legs, greyed scarf, two ash flakes on the ushanka. Silhouette pixel-identical to `alexei` in every shared row | the 15 rows of `alexei` (same indices) + `carry_side` (8-frame walk, the file C-17 clamped under the near arm, ground speed = walk_side 34.5 px/s) + `carry_idle_side` (8-frame idle with the file) |
| `assets/characters/konrad_soot/` | `konrad` | the same for Konrad (forehead smear under the brim, beige scarf greyed, ash on the hat); his folder and tube stay | 15 rows of `konrad` + the two carry rows (35.0 px/s) |
| `assets/characters/typist_night/` | `typist` | Frau Brunner at the quay, 2.20 at night: dark aubergine-brown wool coat (knee length, collar up) over the pale nightdress (hem to the ankles), nightdress collar at the throat, felt boots, near hand holding the coat shut (gesture: hand to the collar); no pencil, no pad, no sleeve protectors | the 9 rows of `typist` |

Each directory: `sheet.png`, `sheet_n.png` (normal map), `sheet.json` (TECHNICAL_ARCHITECTURE §4 contract, base rows
first), `portrait.png` (4 × 112 strip), `portrait_anim.png` (living portrait grid, 6 rows) and `portrait.json`
(round-2 contract + `"look_of": <base id>`). Portraits: soot smears placed in head-local coordinates (they follow every
expression), grimy collar, ash on the hat, the rim light turned warm (the fire behind them), a smoky backdrop glowing
from the left (`c3p2_smoke`); `typist_night` on the quay's night backdrop (`c3p2_quay`) with the fire's glow.
Backdrops are registered in memory in `chargen_portrait2_paint.BG` — no `chargen_portrait2*.py` file is changed.
Review images: `assets/characters/_preview/c3p2_*` (git-ignored, `.gdignore`).

## Sound (`tools/audiogen/c3p2_audio.py`) — 44.1 kHz / 16-bit PCM, lossless import, loops carry a `smpl` chunk
Measured on the delivered files (RMS / sample peak in dBFS):

| File | Content | Length | RMS / peak | Wired |
|---|---|---|---|---|
| `amb/amb_veltrava_registry.wav` | souterrain at night: cellar room tone, the city far off, wind and snow at the high windows, radiator ticks + one gurgle, the porter's radio low in the glazed booth (the night waltz), a guard's steps crossing the yard snow above, the house settling, one far goods train | 60 s loop, stereo | −26.0 / −8.8 | `L_C3_Registry.tscn` ambience (scenes A, B) |
| `amb/amb_veltrava_fire.wav` | the registry burning: breathing roar, crackle (tamed around 3 kHz so the text stays in front), ember hiss, sap squeals, timber groaning and splitting, heat-cracked panes, debris far off, the palais' electric fire bell muffled through brick (10-s spells, 5-s pauses), the brigade's hand bell outside once | 60 s loop, stereo | −24.3 / −3.0 | `c3.json` switches C / D `"ambience"` |
| `amb/amb_veltrava_quay.wav` | the quay before dawn: wind over the frozen river, the burning wing far left, the ladder engine's pump idling, hose spray, river ice singing (dispersive chirps) and booming, the engine's bell, a second brigade's two-tone horn far across the town, boots in the snow | 60 s loop, stereo | −24.0 / −3.0 | `L_C3_Quay.tscn` ambience |
| `music/mus_c3p2_fire.wav` | tense, not action: bowed A drone, a heartbeat pulse that leans on Bb in the middle, violas rising A→Bb→B→C and falling back, flickering string harmonics, low brass breathing, the V motif begun and broken off twice; no drums | 66.7 s loop (72 bpm, 80 beats), stereo | −21.0 / −6.9 | to wire: `c3.json` switches C / D `"music"` (integration notes) |
| `music/mus_c3p2_halves.wav` | quiet: the two-language motif V divided — piano first half / viola second half (with Veltrava's Bb), then swapped (piano with B), then the piano alone and no answer; open-fifth drone, slow pads, celesta snow | 102.9 s loop (56 bpm, 96 beats), stereo | −23.0 / −5.1 | `L_C3_Quay.tscn` music (LS_C3_Halves keeps it) |
| `sfx/c3p2_fire_low/_mid/_high.wav` | fire beds in three intensities (smouldering crackle → steady fire → a room ablaze) | 20 s loops, stereo | −33.4 / −26.4 / −21.6, peaks −3.0 | cinematics (`loop` cue), level scripts (`Audio.sfx_loop`) |
| `sfx/c3p2_yard_night.wav` | the snowy yard at night: soft wind, flakes, the bracket lamp's hum, the town, a far train | 30 s loop, stereo | −27.0 / −6.4 | registry yard (level script) / LS_C3_Escape bed |
| `sfx/c3p2_radio_waltz.wav` | the porter's radio close up (same waltz, valve-set speaker) | 60 s loop, mono | −24.0 / −12.7 | `exp_radio` / registry level script |
| `sfx/c3p2_radio_interval.wav` | Radio Veltrava's interval signal (V on a music box, twice) | 4.0 s mono | −19.3 / −8.0 | LS_C3_Radio r1 (optional; the cinematic has its own `c3p2cine_*`) |
| `sfx/c3p2_radio_news_ru.wav`, `_de.wav` | newsreader murmur through the set (two prosody profiles, no words) | 6.5 s mono | −20.8 / −9.0 | LS_C3_Radio r2 / r3 (optional) |
| `sfx/c3p2_radio_tune.wav` | the dial: static, heterodyne whistle, fragments, the carrier settles | 1.4 s mono | −21.4 / −10.0 | LS_C3_Radio match cut (optional) |
| `sfx/c3p2_note_slide.wav` | a folded note pushed under a door | 1.7 s | −32.9 / −12.0 | LS_C3_Radio r4 |
| `sfx/c3p2_fire_catch.wav` | the C-17 stacks catching: whoomph, paper crackling up, first roar | 5.4 s | −27.4 / −6.0 | LS_C3_Fire f2 |
| `sfx/c3p2_bolt.wav` | the ramp door's iron bolt drawn home outside (heard through oak) | 3.6 s | −30.8 / −5.0 | LS_C3_Fire f3, `c3e_try_ramp` |
| `sfx/c3p2_desk_push.wav` | the oak intake desk dragged off the chute door | 4.4 s | −23.2 / −5.0 | `dlg_c3f_desk` („Drei!“) |
| `sfx/c3p2_door_jam.wav` | the jammed 1909 iron door: latch, grinding, a shoulder, a few centimetres | 4.0 s | −28.7 / −5.0 | `dlg_c3f_chute` |
| `sfx/c3p2_hatch_open.wav`, `_slam.wav` | the coal hatch in the yard: rusty hinge, lid on the snowy stone; slammed on the smoke | 6.0 / 5.7 s | −31.5 / −4.0, −28.7 / −3.0 | LS_C3_Escape e2 / e3 |
| `sfx/c3p2_window_burst.wav` | the souterrain windows bursting, glass on the yard, flame breathing out | 6.7 s | −25.3 / −4.0 | LS_C3_Escape e4 |
| `sfx/c3p2_roof_creak_1..3.wav` | burning timber under load (the third ends splitting) | 4.6–6.0 s | −27…−30 / −7…−9 | fire scenes (random variant via `Audio.sfx("c3p2_roof_creak")`) |
| `sfx/c3p2_glass_1..3.wav` | heat-cracked panes and falling shards | 4.8 s | −40…−43 / −6.0 | fire scenes (`Audio.sfx("c3p2_glass")`) |
| `sfx/c3p2_fire_bell.wav` | the ladder engine's brass bell rung by hand across the yard | 7.6 s | −23.2 / −6.0 | LS_C3_Escape e4, quay |
| `sfx/c3p2_sirens_far.wav` | two brigades' two-tone horns of 1964 crossing the town far away | 10 s | −23.6 / −9.0 | LS_C3_Escape e4, LS_C3_Halves h3 |

Level windows enforced by the generator and `tests/test_c3p2_cast_audio.gd`: ambiences −28…−21 dBFS RMS, peak ≤ −2.5;
music −25…−19, peak ≤ −0.8; sfx loops −36…−19, peak ≤ −2.5; one-shots −45…−9, peak ≤ −2.5, ending in silence.
Loops: `smpl` loop = whole file (imported as `LOOP_FORWARD`, checked), level continuous across the loop point
(|Δ RMS over 50 ms| ≤ 3 dB, the seam step an ordinary step; measured: registry 0.4 dB / 1.2× median step, fire 1.2 dB
/ 2.7×, quay 0.8 dB / 1.0×, music 0.1 and 0.6 dB, fire beds ≤ 0.9 dB / ≤ 2.1×, yard 1.9 dB / 0.5×, waltz 1.8 dB / 0.2×). Spectral balance was checked by band shares (the quay and the yard
were de-hissed: 4–8 kHz share 21 % → 5 %; the fire ambience's 2–4 kHz crackle band 20 % → 11 %).
Spectrograms + `c3p2_analysis.json`: `assets/audio/_preview/` (git-ignored).

## Tests
`tests/test_c3p2_cast_audio.gd` — looks follow their base (rows, indices, fps, variants, silhouette, visible soot,
carry rows and their ground speed), load and play on `SpriteRig`, living portraits (contract, talk/blink rows,
differ from the base); every WAV's format, loop chunk, import loop mode and length; levels and seams measured on the
PCM; wiring (level ambience/music ids, switch settings, an optional `"looks"` table, every c3p2 sound a round-8
cinematic cue names).
