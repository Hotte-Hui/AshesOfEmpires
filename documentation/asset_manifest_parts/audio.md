# Asset manifest — AUDIO (soundscape, music, SFX, Audio autoload)

| | |
|---|---|
| Area owner | audio specialist (tools/audiogen/**, assets/audio/**, scripts/core/audio.gd, default_bus_layout.tres) |
| Date | 2026-11-04 |
| Provenance | **100 % original, synthesised from code** (Python 3.13 + numpy 2.5, stdlib `wave`). No recordings, no samples, no sound libraries, no downloads, no AI audio models, no reference audio. All melodies, harmonies and arrangements were composed for this project. |
| Licence | Project-owned original work (same terms as the game's own code/art). No third-party rights. |
| Reproduce | `py -3 -P tools/audiogen/build_all.py` (deterministic, bit-identical re-runs; ≈ 50 s synthesis + analysis on 12 cores, ≈ 65 s with `--godot`, which additionally runs `--import` and the headless test; `--only a,b` rebuilds a subset) |
| Format | `assets/audio/{amb,music,sfx}/*.wav`, 44 100 Hz, 16-bit PCM (TPDF-dithered), stereo for ambience/music/spatial cues, mono for point sources |
| Godot import | `*.wav.import` with `compress/mode=0` (lossless PCM in-engine, what was measured is what plays). Loops carry a RIFF `smpl` chunk → importer "Detect From WAV" sets `LOOP_FORWARD`, `loop_begin=0`, `loop_end=frames`; `Audio` additionally enforces looping at runtime. |
| Previews | `assets/audio/_preview/` (has `.gdignore`): spectrogram PNGs (log + linear frequency, RMS strip) for every music/ambience file, a zoomed loop-seam view for every loop, `sfx_sheet.png` contact sheet, `analysis.json`; `assets/audio/audio_manifest.json` lists paths, durations, loop points and levels. |

## Pipeline (tools/audiogen/)
| Module | Role |
|---|---|
| `dsp.py` | Core DSP: periodic FFT/STFT noise, zero-phase spectral EQ, exact biquads (closed-form IR + FFT convolution), circular convolution, **generated stereo convolution reverb** (8-band frequency-dependent decay of decorrelated noise + early reflections + optional facade slap echoes), periodic smooth control curves, look-ahead limiter, gentle offline RMS "glue" compressor, 2× decimator, WAV writer with `smpl` loop chunk, WAV reader. |
| `instruments.py` | Band-limited **wavetable** oscillators with morphing: bowed-string ensemble (5 detuned voices, delayed vibrato, bow noise, crescendo/brightness coupling, flautando/harmonic mode) and low brass pad (4 brightness tables, pitch scoop, breath); **additive** felt/muted piano (inharmonic partials, 1–3 detuned strings, two-stage decay, strike-position comb, hammer thump, damper); **FM** celesta (c:m 1:3.5 decaying index + harmonic 4:1 tine, rendered at 88.2 kHz and decimated); block-vectorised **Karplus-Strong** pluck; **modal** synthesis (damped sinusoid banks) for metal, wood and bells; ADSR / humanised timing in the score layer. |
| `foley.py` | Physically-inspired generators: grain-cloud footsteps (gravel, snow incl. cold-snow squeak, concrete, wood incl. creak), paper crackle/swish, page turn, stamp, cards, door, drawer, stick-slip creaks, metal clanks, tram gong, locomotive horn + far-field version, buffer-bump chains, STFT wind with gust-driven spectra and whistle, passing tram, **formant babble** (random vowel formants on a glottal pulse train — *no words, no language, unintelligible by construction*), 1960s loudspeaker colouring. |
| `ambience.py` | The four 60 s loops (circular timeline: events, reverb tails and modulators wrap; tonal parts use whole cycles per loop). |
| `music.py` | Score + rendering: motifs, chord plans, per-stem EQ, shared hall reverb send, mixdown (loudness glue, −20 dBFS RMS, −1 dBFS ceiling). |
| `sfx.py` | One-shots and the fire loop (peaks normalised ≤ −6 dBFS, 11 kHz/4th-order top limit, 30 Hz HPF, DC-free). |
| `analyze.py` | Metrics (RMS, max 400 ms RMS, sample + 4× true peak, clipping, DC, >16 kHz energy, loop-seam jump / HF / curvature percentiles, band energy, approx. LUFS) and preview rendering. |
| `build_all.py` | Orchestration (parallel), `.import` files, analysis, previews, this file's metrics table, optional Godot import + test. |
| `test_audio_headless.gd` | Godot headless test (see Verification). |

## Music (assets/audio/music/) — composed for this project
Motifs: **K** (Karsk / Alexei, D Aeolian: K_A "asks" D5 A4 E5 \| F5 E5 C5 and ends open on the b7, K_B answers and closes) and **B** (Berlin / Konrad Adler, G Aeolian: even quarter-note pulse, narrow range, b6 neighbour sigh G4 Bb4 A4 G4 \| D5 Eb5 D5 \| C5 Bb4 A4 Bb4 \| G4, over a low brass pedal on G = order imposed from below). Deliberately no national clichés (no folk scales with augmented seconds, no balalaika/accordion/choir, no march or fanfare); restrained chamber-orchestral minimalism. Hall reverb is generated (RT60 ≈ 3–3.8 s low / 1.3–1.5 s high).

| File | Generator | Length | Loop | Content |
|---|---|---|---|---|
| `music/mus_karsk.wav` | `music.py: mus_karsk()` seed 11 | 96.0 s (24 bars, ♩ = 60) | yes, whole file | Cold string pad (Dm(add9) – Bbmaj7#11 – Gm9 – A7sus4/Am7 – Fmaj9 – Cadd9/E – …), sparse felt-piano K motif (incl. low-octave variant and climax with soft octave doubling), Karplus-Strong low plucks, high flautando lines. |
| `music/mus_berlin.wav` | `music.py: mus_berlin()` seed 23 | 96.0 s (28 bars, ♩ = 70) | yes | Low brass pad over a G pedal (Gm – Eb/G – Cm/G – Ab/G "pressure" – Dsus/G …), B motif on muted piano, then celesta over a soft D4 "clock" pulse, pressure section with low strings, sparse celesta coda. |
| `music/mus_menu.wav` | `music.py: mus_menu()` seed 37 | 106.67 s (28 bars, ♩ = 63) | yes | Main theme: K on piano (D), B on celesta (G), then both together where B "bends" Eb→E (shared D-Aeolian/G-Dorian collection), climax with K in octaves answered by B fragments, calm return. |
| `music/mus_choice.wav` | `music.py: mus_choice()` seed 41 | 5.0 s | no | Decision sting: open D–A–E string chord swells and hangs, piano asks the K head (D5 → A4), soft low brass. Suggested use: `Audio.sting("mus_choice")`. |
| `music/mus_hall_reveal.wav` | `music.py: mus_hall_reveal()` seed 53 | 12.4 s | no | Oppressive low cluster (brass C2 Db2 F2 Gb2 G2 + low strings + C1 sub + timpani-like roll + rising high semitone) swelling for 10.8 s, hard (35 ms) cut, the generated hall rings on. Matches `LS_M1_Hall` (11 s). |
| `music/mus_finale_x1.wav` | `music.py: mus_finale_x1()` seed 61 | 20.0 s | no | K (piano) then B (celesta), both heads together at 15.8 s; ends on an A/Bb rub inside Bbmaj7/D under a high harmonic — unresolved, fades. Matches `LS_X1_Final` (15 s) with a tail. |

## Ambience (assets/audio/amb/) — 60 s seamless stereo loops, target ≈ −24 dBFS RMS
| File | Generator | Content |
|---|---|---|
| `amb/amb_karsk_yard.wav` | `ambience.py: amb_karsk_yard()` seed 1101 | Cold wind with 7 gusts (gust-driven brightness, aeolian whistle), snow hush, low industrial rumble, 3 distant shunting chains (buffer bumps travelling down the wagons, facade echoes) + a light clank, far locomotive horns at 9.0 s (single tone) and 34.4/36.1 s (two-tone + short toot) → intervals 25.4 s / 34.6 s, 4 faint metallic creaks, one far muffled station announcement (formant babble through a horn loudspeaker, unintelligible) — the scene atlas' "gedämpfte Bahnhofsdurchsage". |
| `amb/amb_berlin_archive.wav` | `ambience.py: amb_berlin_archive()` seed 2201 | Dark room tone, city rumble through the windows, wall clock on the left (60 ticks per loop, tick/tock), 9 radiator ticks + one gurgle, very muffled tram (rumble, rail joints, motor) with its gong at 24.3 s, two muffled cars, paper at other desks (3×), a faint typewriter in another room. Level −25 dBFS RMS (a quiet room; within the ≈ −24 target). |
| `amb/amb_berlin_street.wav` | `ambience.py: amb_berlin_street()` seed 3301 | Urban wind, catenary wires singing with the gusts (aeolian tones, whole cycles per loop) + faint 100 Hz electrical hum, a tram passing (rumble, rail-joint pairs, motor whine with Doppler, wire hiss) with its gong at 25.2 s, distant hall loudspeakers (two babble passages, unintelligible, long facade echoes), city rumble. |
| `amb/amb_transition.wav` | `ambience.py: amb_transition()` seed 4401 | Low airy drone on D (D1/D2/A2/D3 partials with slow beating, breathing noise band, faint high air) plus a faint bowed-metal shimmer on the tram-gong partials (820/1238/1747 Hz) — the "metal timbre" bridge between Karsk and Berlin from the scene atlas. |

## SFX (assets/audio/sfx/) — peaks ≤ −6 dBFS, mono unless noted
| File(s) | Generator (`sfx.py` → `foley.py`) | Notes |
|---|---|---|
| `step_gravel_1..4.wav` | `step_gravel` → `footstep('gravel')` | heel + toe crunch (grain clouds through stone resonators) + boot thump; peak −12 |
| `step_snow_1..4.wav` | `step_snow` → `footstep('snow')` | compressive crunch + cold-snow squeak, top limited 5.5 kHz; peak −13 |
| `step_concrete_1..4.wav` | `step_concrete` → `footstep('concrete')` | leather heel click/tock, toe tap, scuff, tiny room; peak −12 |
| `step_wood_1..4.wav` | `step_wood` → `footstep('wood')` | board knock (modal); variant 3 with a soft creak; peak −12 |
| `paper_rustle_1..3.wav` | `paper` → `paper_rustle()` | crackle + swish gestures; peak −14 |
| `page_turn_1..2.wav` | `pages` → `page_turn()` | lift, swoosh with flutter, soft landing; peak −14 |
| `stamp_thud.wav` | `stamp_thud` → `stamp()` | rubber stamp on paper on a wooden desk + archive room; peak −6 (C-17 moment) |
| `metal_clank_1..3.wav` | `clanks` → `metal_clank()` | 1 light coupling clank, 2 heavy buffer/rail clank, 3 ringing clank sharing the tram-gong partials (match-cut bridge to `tram_bell`); peak −8 |
| `tram_bell.wav` | `tram` → `tram_bell()` | Berlin tram foot gong, two strikes; peak −9 |
| `door_open.wav` | `door` → `door_open()` | latch, spring, hinge creak (stick-slip), air, archive room; peak −10 |
| `drawer_slide.wav` | `drawer` → `drawer_slide()` | wooden drawer friction + contents + stop knock; peak −11 |
| `card_place_1..2.wav` | `cards` → `card_place()` | short slide + soft tap; peak −14 |
| `puzzle_success.wav` (stereo) | `puzzle_success()` | subtle: celesta D5→A5→E5 over a soft open fifth; peak −10 |
| `puzzle_fail.wav` (stereo) | `puzzle_fail()` | soft, non-punishing: muted piano F4→E4 + wooden tock; peak −14 |
| `ui_move.wav`, `ui_select.wav`, `ui_back.wav` | `ui()` | soft tick (−20), felt "tock" D5 (−15), lower felt note (−17) |
| `type_tick_1..3.wav` | `type_ticks` → `type_tick()` | very short soft key ticks for dialogue text, 3 pitches; peak −22 |
| `train_horn_far.wav` (stereo) | `train_horn` → `far_horn()` | distant locomotive horn with facade echoes; peak −12 |
| `wind_gust.wav` (stereo) | `gust` → `wind()` | single gust sweeping across; peak −12 |
| `fire_crackle_loop.wav` (stereo, **10 s loop**) | `fire_loop()` | fire barrel: roar, hiss, crackles and pops on a circular timeline; peak −8, RMS −25 |

## Measured levels (all files)
RMS/peak in dBFS with full scale = 1.0 (a full-scale sine reads −3.01 dBFS RMS). Seam columns only for loops:
jump = |x[0] − x[n−1]| relative to the median sample step; HF / curvature = percentile of the >6 kHz energy
(±20 ms window) and of the second difference at the seam among the whole file (a click would sit at p≈100;
values spread across 0–100 are the expected statistics of a seamless loop).

<!-- metrics:begin (written by tools/audiogen/build_all.py) -->
| file | ch | s | loop (frames) | RMS dBFS | max 400 ms RMS | peak dBFS | true peak | clipped | DC | >16 kHz dB | seam (jump x median step / HF pct / curvature pct) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| amb/amb_berlin_archive.wav | 2 | 60.0 | 0..2646000 | -25.0 | -19.82 | -3.4 | -3.4 | 0 | 0.0e+00 | -50.3 | 0.55 / p91.5 / p39.79 |
| amb/amb_berlin_street.wav | 2 | 60.0 | 0..2646000 | -24.0 | -18.86 | -5.34 | -5.32 | 0 | 0.0e+00 | -52.7 | 0.57 / p8.5 / p12.02 |
| amb/amb_karsk_yard.wav | 2 | 60.0 | 0..2646000 | -24.0 | -18.28 | -4.37 | -4.37 | 0 | 0.0e+00 | -40.2 | 1.72 / p9.2 / p61.97 |
| amb/amb_transition.wav | 2 | 60.0 | 0..2646000 | -24.0 | -22.18 | -8.64 | -8.63 | 0 | 0.0e+00 | -43.1 | 1.64 / p88.5 / p96.95 |
| music/mus_berlin.wav | 2 | 96.0 | 0..4233600 | -20.0 | -11.6 | -2.23 | -2.23 | 0 | 0.0e+00 | -84.4 | 0.42 / p41.2 / p37.3 |
| music/mus_choice.wav | 2 | 5.0 | - | -22.51 | -14.9 | -4.71 | -4.71 | 0 | 0.0e+00 | -81.8 | - |
| music/mus_finale_x1.wav | 2 | 20.0 | - | -20.0 | -15.92 | -5.3 | -5.3 | 0 | 0.0e+00 | -84.2 | - |
| music/mus_hall_reveal.wav | 2 | 12.4 | - | -19.13 | -13.08 | -1.0 | -1.0 | 0 | 2.0e-06 | -85.1 | - |
| music/mus_karsk.wav | 2 | 96.0 | 0..4233600 | -20.0 | -13.1 | -2.62 | -2.62 | 0 | 0.0e+00 | -83.7 | 0.72 / p12.5 / p50.72 |
| music/mus_menu.wav | 2 | 106.667 | 0..4704000 | -20.0 | -12.55 | -1.59 | -1.57 | 0 | 0.0e+00 | -84.9 | 2.25 / p14.5 / p39.76 |
| sfx/card_place_1.wav | 1 | 0.17 | - | -37.9 | -37.9 | -14.0 | -13.96 | 0 | 0.0e+00 | -45.2 | - |
| sfx/card_place_2.wav | 1 | 0.17 | - | -37.35 | -37.35 | -14.0 | -14.0 | 0 | 0.0e+00 | -43.2 | - |
| sfx/door_open.wav | 1 | 1.433 | - | -33.24 | -29.15 | -10.0 | -9.96 | 0 | 1.0e-06 | -50.7 | - |
| sfx/drawer_slide.wav | 1 | 1.0 | - | -32.39 | -29.59 | -11.0 | -11.0 | 0 | 0.0e+00 | -50.4 | - |
| sfx/fire_crackle_loop.wav | 2 | 10.0 | 0..441000 | -25.0 | -21.52 | -8.0 | -8.0 | 0 | 0.0e+00 | -45.7 | 0.96 / p59.8 / p72.59 |
| sfx/metal_clank_1.wav | 1 | 0.343 | - | -28.63 | -28.63 | -8.0 | -8.0 | 0 | 1.4e-04 | -53.8 | - |
| sfx/metal_clank_2.wav | 1 | 2.2 | - | -30.44 | -23.05 | -8.0 | -7.99 | 0 | 1.0e-06 | -53.2 | - |
| sfx/metal_clank_3.wav | 1 | 2.414 | - | -33.32 | -25.66 | -8.0 | -7.91 | 0 | 1.2e-05 | -49.1 | - |
| sfx/page_turn_1.wav | 1 | 0.64 | - | -31.37 | -29.39 | -14.0 | -13.9 | 0 | 0.0e+00 | -52.6 | - |
| sfx/page_turn_2.wav | 1 | 0.64 | - | -31.15 | -29.16 | -14.0 | -13.93 | 0 | 0.0e+00 | -52.9 | - |
| sfx/paper_rustle_1.wav | 1 | 0.818 | - | -39.08 | -35.98 | -14.0 | -13.99 | 0 | 0.0e+00 | -51.5 | - |
| sfx/paper_rustle_2.wav | 1 | 1.193 | - | -34.78 | -30.29 | -14.0 | -13.84 | 0 | 0.0e+00 | -47.4 | - |
| sfx/paper_rustle_3.wav | 1 | 0.7 | - | -33.49 | -31.17 | -14.0 | -14.0 | 0 | 0.0e+00 | -48.2 | - |
| sfx/puzzle_fail.wav | 2 | 1.332 | - | -31.7 | -26.59 | -14.0 | -14.0 | 0 | 1.0e-05 | -60.0 | - |
| sfx/puzzle_success.wav | 2 | 3.393 | - | -24.9 | -19.77 | -10.0 | -9.99 | 0 | 0.0e+00 | -79.7 | - |
| sfx/stamp_thud.wav | 1 | 2.306 | - | -35.76 | -28.15 | -6.0 | -6.0 | 0 | 2.0e-06 | -57.4 | - |
| sfx/step_concrete_1.wav | 1 | 0.5 | - | -38.78 | -37.81 | -12.0 | -11.91 | 0 | 3.0e-06 | -41.1 | - |
| sfx/step_concrete_2.wav | 1 | 0.5 | - | -39.78 | -38.81 | -12.0 | -11.95 | 0 | 3.0e-06 | -38.6 | - |
| sfx/step_concrete_3.wav | 1 | 0.5 | - | -39.87 | -38.9 | -12.0 | -11.84 | 0 | 3.0e-06 | -42.4 | - |
| sfx/step_concrete_4.wav | 1 | 0.5 | - | -38.35 | -37.38 | -12.0 | -12.0 | 0 | 3.0e-06 | -40.3 | - |
| sfx/step_gravel_1.wav | 1 | 0.312 | - | -31.8 | -31.8 | -12.0 | -12.0 | 0 | 1.8e-05 | -45.7 | - |
| sfx/step_gravel_2.wav | 1 | 0.336 | - | -33.77 | -33.77 | -12.0 | -11.77 | 0 | 3.7e-05 | -45.1 | - |
| sfx/step_gravel_3.wav | 1 | 0.28 | - | -32.12 | -32.12 | -12.0 | -12.0 | 0 | 5.0e-06 | -44.8 | - |
| sfx/step_gravel_4.wav | 1 | 0.333 | - | -33.87 | -33.87 | -12.0 | -11.9 | 0 | 2.6e-05 | -46.5 | - |
| sfx/step_snow_1.wav | 1 | 0.415 | - | -32.31 | -32.15 | -13.0 | -12.96 | 0 | 2.0e-06 | -67.7 | - |
| sfx/step_snow_2.wav | 1 | 0.398 | - | -32.37 | -32.37 | -13.0 | -12.99 | 0 | 1.0e-06 | -68.1 | - |
| sfx/step_snow_3.wav | 1 | 0.446 | - | -32.64 | -32.17 | -13.0 | -13.0 | 0 | 2.0e-06 | -67.4 | - |
| sfx/step_snow_4.wav | 1 | 0.376 | - | -32.92 | -32.92 | -13.0 | -12.93 | 0 | 3.0e-06 | -67.9 | - |
| sfx/step_wood_1.wav | 1 | 0.5 | - | -34.92 | -33.95 | -12.0 | -11.99 | 0 | 5.0e-06 | -55.9 | - |
| sfx/step_wood_2.wav | 1 | 0.5 | - | -34.19 | -33.22 | -12.0 | -11.99 | 0 | 5.0e-06 | -51.0 | - |
| sfx/step_wood_3.wav | 1 | 0.5 | - | -34.17 | -33.2 | -12.0 | -11.93 | 0 | 6.0e-06 | -50.0 | - |
| sfx/step_wood_4.wav | 1 | 0.5 | - | -34.34 | -33.38 | -12.0 | -11.96 | 0 | 6.0e-06 | -54.2 | - |
| sfx/train_horn_far.wav | 2 | 4.917 | - | -28.55 | -22.48 | -12.0 | -12.0 | 0 | 0.0e+00 | -74.7 | - |
| sfx/tram_bell.wav | 1 | 3.07 | - | -27.75 | -20.06 | -9.0 | -9.0 | 0 | 0.0e+00 | -70.4 | - |
| sfx/type_tick_1.wav | 1 | 0.056 | - | -46.48 | -46.48 | -22.0 | -22.0 | 0 | 1.9e-05 | -51.4 | - |
| sfx/type_tick_2.wav | 1 | 0.06 | - | -45.55 | -45.55 | -22.0 | -21.95 | 0 | 1.3e-05 | -52.5 | - |
| sfx/type_tick_3.wav | 1 | 0.06 | - | -45.41 | -45.41 | -22.0 | -21.96 | 0 | 1.4e-05 | -45.3 | - |
| sfx/ui_back.wav | 1 | 0.421 | - | -36.65 | -36.42 | -17.0 | -16.96 | 0 | 3.0e-06 | -63.7 | - |
| sfx/ui_move.wav | 1 | 0.07 | - | -34.57 | -34.57 | -20.0 | -19.95 | 0 | 0.0e+00 | -67.4 | - |
| sfx/ui_select.wav | 1 | 0.437 | - | -33.62 | -33.24 | -15.0 | -15.0 | 0 | 3.0e-06 | -64.6 | - |
| sfx/wind_gust.wav | 2 | 4.41 | - | -32.74 | -25.88 | -12.0 | -11.99 | 0 | 0.0e+00 | -58.8 | - |
<!-- metrics:end -->

## Runtime (scripts/core/audio.gd, default_bus_layout.tres)
* Buses: Master (HardLimiter, ceiling −0.5 dB) ← Music, Ambience, SFX, UI (all send to Master).
* `Audio.play_ambience(id, fade := 1.5)`, `Audio.play_music(id, fade := 2.0)`, `Audio.stop_music(fade := 2.0)`,
  `Audio.sfx(id, volume_db := 0.0, pitch_var := 0.05)`, `Audio.ui(id)` exactly as in TECHNICAL_ARCHITECTURE §7.
  Equal-power crossfades; any number of overlapping changes is safe (each track keeps its own player while fading);
  same id = no restart; `""` fades out; missing files are a silent no-op with one warning.
* `sfx("step_gravel")` picks a random variant `_1.._4` (never the same twice in a row) with ±5 % pitch.
  `ui("move"|"select"|"back")` → `ui_*`; `ui("type_tick")` → `type_tick_1..3`; `ui()` also accepts any SFX id.
* Extras: `stop_ambience(fade)`, `sting(id, duck_db := -9, fade := 0.35)` (one-shot cue over the music, ducks it,
  restores when done — intended for `mus_choice`), `sfx_loop(id, key, volume_db, fade)` / `stop_sfx_loop(key, fade)`
  (e.g. `fire_crackle_loop`), `has_sound(id)`, `preload_sound(id)`, `current_music()`, `current_ambience()`,
  `set_bus_volume_linear(bus, v)`. Music/ambience stay uncached (freed after fading out); SFX are cached.
* Looping music: `mus_karsk`, `mus_berlin`, `mus_menu`; all `amb_*`; `fire_crackle_loop`. One-shot cues:
  `mus_choice`, `mus_hall_reveal`, `mus_finale_x1` (`current_music()` becomes `""` when a cue ends by itself).
* Volume settings: `Audio` applies `master/music/ambience/sfx/ui_volume` from the `Settings` autoload at start and on
  `Settings.changed`. (Settings' own `apply()` maps keys with `String.capitalize()` → "Sfx"/"Ui", which do not match
  the bus names "SFX"/"UI" from §7; Audio covers this, so no change to settings.gd is required.)

## Verification (2026-11-04) — what was and was not checked
* **Not listened to.** All judgements are from measurements and spectrograms (no audio playback available to the
  author). A human listening pass is still required before final sign-off.
* Every file analysed: no clipping, |DC| < 3e-4, peaks as designed (SFX ≤ −6 dBFS), music −20 dBFS RMS
  (loops; cues measured over their active span), ambience −24 dBFS RMS (archive −25), loop seams continuous
  (table above + `_preview/*_seam.png`).
* Spectrograms of all music/ambience inspected for harshness, aliasing and clicks; iterations made: string/brass
  noise and Karplus-Strong excitation band-limited (KS energy >16 kHz −29 dB → −76 dB), footstep stray grains removed,
  paper densified, ambience beds de-rumbled so shunting/horn/PA/clock events read, bass voices of string chords
  strengthened, gentle loudness glue added (1.6:1 above integrated +5 dB), stereo balance centred; the -1 dBFS
  safety limiter only touches the climax of mus_hall_reveal (0.3 dB) and no other music file.
* Loop seams additionally checked locally (+-0.5 s around the loop point): sample-step and curvature percentiles
  of the seam lie between p10 and p93 for all five loops checked (no outlier, i.e. no click).
* Harmony check by chroma analysis: for `mus_karsk` the 3 strongest pitch classes of each chord slot are chord tones
  in 38 of 39 cases (the remaining one is a motif melody note); `mus_berlin` 16/18 (the misses are the motif's
  intended non-chord tones over Cm/G).
* Godot 4.7.2: `--headless --import` imports all 51 WAVs as PCM16 44.1 kHz with the loop flags as designed;
  `tools/audiogen/test_audio_headless.gd` passes (bus layout + limiter, Settings → bus volumes for all five buses,
  crossfade, rapid triple change, same-id no-restart, ducked sting, SFX variants + pitch variation, UI routing,
  SFX loop start/stop, graceful missing files, one-shot cue end, and all 51 streams played into a muted bus with
  advancing playback under the headless dummy driver).
