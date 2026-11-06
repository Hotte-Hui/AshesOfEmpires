# Asset manifest — Chapter-3 mini-game „Das Relaispult“ (area: minigames_r7_relay)

Owner: minigames_r7_relay specialist · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: TECHNICAL_ARCHITECTURE §12.1/§12.8
(user request this round: more play time, new mini-games, finish Chapter 3).

Everything listed here is **original work**, generated procedurally by the two project scripts below on 2026-11-06.
No pixel, sample, voice or melody was taken from `documentation/references/` or any other source; no downloads, no
AI media, no recordings. Colours come from `data/chapters/c3.json` (palettes `palais` and `veltrava`) plus three
lamp-glass ramps defined in the generator. No flags, no insignia, no text baked into the art (all text is Loc).
The voices are prosody only (glottal source, vowel formants, consonant noise) — they speak no language and no words.
Historical model: the booth-and-lamp systems of the post-war conferences (the real-history card
`hist.reich.nuremberg_interpreters` tells the Nuremberg story outside the fiction; in the game world the trial never
happened, so nothing in-world refers to it). Licence: original project work (same terms as the rest of the game).

## The mini-game

| Explore entry | Scene / scripts | Place | Game |
|---|---|---|---|
| `veltrava.hall.relay` (detail, area `veltrava`, links `hist.reich.nuremberg_interpreters`) | `scenes/ui/minigames/RelayDesk.tscn` · `scripts/ui/minigames/relay_game.gd` + `relay_logic.gd`; hotspot `scripts/ui/minigames/relay_spot.gd`; world prop `relay_world_desk.gd` | L_C3_Hall, interpreters' corridor, `exp_relay_desk` [1777, 300] between Kabine 3 and the fire box; prop `RelayDeskProp` (feet [1777, 295]) | The commission's sound technician has to go down to the Saal; Konrad keeps the interpretation desk. Four delegation channels (DE Reichsdelegation, RU Sowjetische Delegation, FR Vorsitz der Kommission, EN Beobachter) are plugged into the floor original or one of three booths (Kabine 1 · FR with German retour, Kabine 2 · RU↔DE, Kabine 3 · EN); booths that do not understand the floor take the relay of another booth and fall behind sooner. Yellow lamp: the speaker slows down; red: he stops a moment. Three rounds (Winterfahrplan · Lebensmittelzüge · Geschäftsordnung) with rising tempo and shorter warnings; a passage is repeated when less than 68 % got across or four threads were lost. The chair adjourns; the interpreter of Kabine 1 has the last word. Open after `c3b_arrival` until `c3b_inspect_booth` (the session) and in a memory of the palais (§12.10). |

Contract (§12.8, shared base `minigame_base.gd`): `open(ctx)`, `ctx.auto` resolves at once, `finished(success)` exactly
once, hint after two refusals (contextual: lamps after lost threads, guide lights on the right sockets after a wrong
desk, the announcements as third hint; Settings `puzzle_hints` 0 off / 2 at once), Esc gives up without penalty,
„Neu anfangen“ repeats the current round, `demo_solve()` plays the whole session through synthetic key events only
(~140 s). Keys: ↑/↓ channel, ←/→ move its plug, 1–4 plug straight in, G (pad X) yellow, R (pad Y) red,
Space/Enter/E (pad A) start/continue; mouse on sockets, tags, lamps and the display. Every state reads by text and
shape as well as colour; desk labels follow the text-scale setting as far as their plates allow (a too long line
shrinks instead of overflowing; the flavour subtitle gives way at 125/150 %); high contrast brightens needles,
selection, guides and the dim texts; reduced motion stops all blinking. All text: `data/locale/de_minigames_r7_relay.json`.

## Generators

* `tools/pixelgen/gen_mg_relay.py` — `py -3 -P tools/pixelgen/gen_mg_relay.py`, then import (shared lock).
  Deterministic (seeds = `crc32` of names; a re-run reproduces every file byte for byte). Drawn 1:1; the game draws
  the desk x3 (nearest), the DiscoveryView shows the close-up x3, the prop lives at world scale.
* `tools/audiogen/mg_audio_relay.py` — `py -3 -P tools/audiogen/mg_audio_relay.py` (numpy only, deterministic).
  44.1 kHz / 16-bit mono WAV in `assets/audio/sfx/`; loops are built periodic and carry a RIFF `smpl` chunk.

## Files

| Path | Size (1:1 px) | Use |
|---|---|---|
| `assets/ui/minigames/relay/relay_desk.png` | 568×152 | The relay desk: walnut body, brass-framed floor display, four enamel channel tags, black crossbar field with 4×4 brass sockets, four source plates (Saal rostrum + three booth windows) with three backlog meters (green / hatched yellow / striped red zones), the steel lamp plate with two bezels |
| `assets/ui/minigames/relay/relay_pins.png` | 3 × 15×17 | Crossbar pin (ivory knob, brass collar) · selection glow · dotted guide ring (hint) |
| `assets/ui/minigames/relay/relay_lamps.png` | 6 × 30×30 | Yellow off/on, red off/on, floor lamp off/on (pressed glass with fresnel rings, halo when lit) |
| `assets/ui/minigames/relay/relay_icons.png` | 6 × 9×9 | Check (understood), cross (wrong language), bars (silence), hook (relay), broken line (thread lost), pause |
| `assets/ui/minigames/relay/relay_booths.png` | 5×4 cells 20×24 | Booth windows of Kabine 1–3 (an older woman, a man with glasses, a young woman — none of them a story character) and the floor rostrum, each listening / speaking a / speaking b / struggling / lost |
| `assets/ui/minigames/relay/relay_interpreter.png` | 2 × 56×56 | The interpreter of Kabine 1 for the closing beat (grey hair in a bun, round glasses, cardigan, headset round her neck): calm / a small smile |
| `assets/ui/minigames/relay/relay_layout.json` | — | Every rect of the composition (art px) — written by the generator, read by `relay_game.gd` |
| `assets/ui/minigames/relay/find_relay.png` | 232×150 | Close-up of the find: the crossbar with the session's last four pins, the yellow lamp still glowing, a headset, the technician's note card with pencilled arrows only, a pencil, a cold coffee |
| `assets/ui/minigames/relay/world_desk.png` | 4 × 44×38 | The technician's desk in the corridor (table, sloped bakelite console with socket field, two lamps, three channel diodes, a headset on a hook); lamp frames calm / yellow / diodes / both |
| `assets/ui/minigames/relay/world_desk_n.png` | 4 × 44×38 | Normal map (table top up, console face tilted back) for the per-texel lighting |
| `assets/ui/minigames/relay/world_desk_e.png` | 4 × 44×38 | Emission of the lamps and diodes (additive child sprite, light mask 0) |
| `assets/audio/sfx/mg_relay_hall.wav` | 12 s LOOP | The Großer Saal heard from the corridor: a dozen far voices (no words), chairs, paper, a cough, room tone, behind glass |
| `assets/audio/sfx/mg_relay_voice_fr.wav` | 8 s LOOP | The chair at the microphone through the desk monitor (older man, calm, phrase-final rises) |
| `assets/audio/sfx/mg_relay_voice_ru.wav` | 8 s LOOP | The Soviet delegate (a woman, measured, darker vowels) |
| `assets/audio/sfx/mg_relay_voice_de.wav` | 8 s LOOP | The Reich delegate (a man, clipped consonants) — the UI fades each voice with its speaker and bends the pitch with the tempo |
| `assets/audio/sfx/mg_relay_plug.wav` | 0.3 s | A pin pushed into its socket (contact scrape + seat) |
| `assets/audio/sfx/mg_relay_switch.wav` | 0.45 s | A desk relay pulling in (round start) |
| `assets/audio/sfx/mg_relay_lamp_yellow.wav` | 0.47 s | Bakelite push button + the soft buzz of the lamp relay |
| `assets/audio/sfx/mg_relay_lamp_red.wav` | 0.6 s | The same, heavier and lower, with a relay clack |
| `assets/audio/sfx/mg_relay_lost.wav` | 0.7 s | A channel dropping out (crackle, falling hiss) |
| `assets/audio/sfx/mg_relay_bell.wav` | 2.2 s | The chair's small brass hand bell, two strokes |
| `assets/audio/sfx/mg_relay_click.wav` | 0.12 s | A dull button press that does nothing (lamp not needed) |

## Verification (2026-11-06)

* `tests/test_minigames_r7_relay.gd` (10 cases, ~1700 checks): booth/relay/pivot tables for every floor language,
  rising tempo and shorter warnings, a careful and a slower scripted player get through (no lost thread, ≥ 90 %),
  never re-plugging repeats round 1, ignoring the lamps repeats round 2 (lost threads), unneeded lamps are
  ignored, yellow slows / red pauses (no scoring) / a lost thread silences the relaying booths, auto mode, keys,
  hint, Esc, demo_solve source check, find + strings (calm, typographic quotes, no microphone numbers, nothing about
  Anlage C or Elena), hotspot on the walkable floor ≥ 26 px from every other spot, level nodes, art sizes vs layout,
  WAV format and loop chunks.
* Windowed captures (scratch harnesses, not in the repo): the desk over the palais at 100 %, 150 % text and high
  contrast; the real game booted into L_C3_Hall, Konrad at the desk, opened through `Game.interact` →
  `_run_minigame`, solved by `demo_solve()` in 140 s without a refusal, find + history card shown, game unpaused.
