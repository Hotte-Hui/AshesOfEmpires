# Asset manifest — Chapter 4 part 1: cast and sound (round 9)

Area owner: cast-audio specialist · Date: **2026-11-06, round 9** · Engine target: Godot 4.7.2
Contract: `documentation/C4_DESIGN.md` §5 (cast: Lev Sokolov, Marta Vogel, Registrator Fengler; sheet with the side rows
of the other side-level NPCs + portrait with the four expressions) and §8 (audio brief). Extends `characters_r7.md`,
`portraits_r7.md`, `c3p2_cast_audio.md`; everything listed there stays valid. `c4.json` asks for no looks / carry rows.

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (numpy + Pillow; no AI models, no
  network, no samples, no third-party art or recordings, no image or audio inputs).
* Characters: drawn on the project's own paper-doll rig (hand-drawn ASCII heads, garment hooks, keyframed poses) and
  its signed-distance portrait pipeline; every face is designed for the person (no shared head preset).
* Sound: synthesised (noise shaping, modal impacts, stick-slip creaks, additive instruments, generated impulse
  responses). The murmur at the tram shelter is unintelligible by construction (prosody profile over random vowel
  targets — no words, no language). All music is composed here; it quotes only the game's own motifs K (Karsk) and
  B (Berlin) from `tools/audiogen/music.py`. The bayan is a free-reed tone synthesised in `c4_audio.py` and plays
  breaths and chords only (the contract's „bayan breath“) — no folk melody, no augmented-second scale, no cliché.
* No insignia on any new sprite or portrait: Marta's cap carries only the line number „74“, Fengler's lapel pin is a
  plain round pin. Licence: project-owned original assets, no attribution needed.
* Deterministic: verified 2026-11-06 — all 15 WAVs rebuilt and md5-compared (identical; round 10: 11 WAVs, the
  three re-voiced cues rebuild bit-identically and `amb_berlin_annex`, which shares `stamp_take`, is unchanged); all 18 character files
  (3 × sheet.png, sheet_n.png, sheet.json, portrait.png, portrait_anim.png, portrait.json) rebuilt into a scratch
  directory and byte-compared (identical).

## Reproduce
```bash
py -3 -P tools/pixelgen/characters_c4.py --portraits   # 3 speakers: sheets, normal maps, living portraits, checks
py -3 -P tools/pixelgen/characters_c4.py --check       # validators only (characters_check + C4 contract checks)
py -3 -P tools/pixelgen/characters_c4.py --heads       # review image of the hand-drawn heads (8x)
py -3 -P tools/audiogen/c4_audio.py                    # 11 WAVs + .import + analysis + numeric checks
py -3 -P tools/audiogen/c4_audio.py --list             # names and where each is (to be) wired
# then the shared, locked import (TECHNICAL_ARCHITECTURE §1)
```
Portraits take ~30–50 s per speaker. Review images: `assets/characters/_preview/c4_*` (git-ignored, `.gdignore`).

## Characters (`tools/pixelgen/characters_c4.py`: sprite specs, heads, hooks, portrait specs, runner)
Through the existing pipeline: `characters.py` (`build_sheet`) and `characters_check.py` are imported and their tables
extended in memory; three scene tints (`c4_cellar` kerosene amber / cold window, `c4_dawn` blue dawn, `c4_annex`
fluorescent green) and two gestures (`tap_stamp`, `look_down_line`) are added in memory; portrait specs are registered
in memory in `chargen_portrait2_cast.CAST` with three backdrops in `chargen_portrait2_paint.BG` (`c4_cellar`,
`c4_loop`, `c4_annex`). No other generator file is changed.

| Directory | Who | Sprite (32 × 56 cells, origin 16/54) | Portrait (112², 4 expressions × 6 states) |
|---|---|---|---|
| `assets/characters/lev/` | Lev Sokolov (54), archive clerk, Karsk | thin, a little stooped, bareheaded; iron-grey thinning hair, round steel glasses with sticking plaster on the hinge, a pencil behind the ear, grey stubble; grey quilted vest over the darned brown cardigan (darn at the elbow), black sleeve protectors, felt boots with galoshes; a glass of tea in its nickel holder held at the chest; gesture: pushes the glasses up; 44 px, walks 21 px/s | a long gaunt face, high cheekbones, hollow cheeks, deep-set tired eyes, thin lips; the plaster on the near hinge, the pencil over the ear, two darns on the cardigan, the vest's stitched channels; the cellar's kerosene glow |
| `assets/characters/marta/` | Marta Vogel (34), tram driver, line 74 | dark-blue driver's coat (brass buttons, belt), uniform cap with a brass number plate, short dark-blond hair, red cheeks, knitted grey scarf (one end swings), fingerless grey gloves (hands drawn here), the leather money satchel on its strap (bounces when she walks), lace-up boots; gesture: rubs her hands and blows into them (breath clouds); 44 px, walks 26 px/s | a round open face, full red cheeks, short straight nose, wide warm mouth (smiles at rest), quick eyes; „74“ in brass on the cap; Berlin dawn |
| `assets/characters/registrar/` | Registrator Fengler (≈ 50), Nebenstelle Süd | light-grey dust coat buttoned to the collar over a dark suit, white collar and dark tie, black sleeve protectors, rimless glasses, dark hair with grey temples combed from a precise side parting, a rubber stamp in the near hand, a plain round lapel pin; gesture: taps the stamp; extra row `work_side` (stamping cards — for `idle_anim`); 47 px, walks 23 px/s | a smooth, well-fed face, a soft double chin, small mouth, hooded bored eyes behind rimless glasses (only the lens edges catch the light), the parting, grey temples, dust coat over suit; fluorescent green |

Rows (all three): `idle_side, walk_side, idle_front, talk_side, blink_side, look_side, gesture_side, blink_front,
talk_front` (+ `work_side` for the registrar); 8-frame idle / talk / talk_front, blink / glance / gesture as non-looping
idle variants (TECHNICAL_ARCHITECTURE §4 contract). Silhouettes checked against each other and 14 existing figures
(IoU ≤ 0.90); portraits checked to differ from each other and from the existing speakers.
Speaker ids = sheet ids = the contract's `lev`, `marta`, `registrar` (names: `data/locale/de_c4_characters.json`).

## Sound (`tools/audiogen/c4_audio.py`) — 44.1 kHz / 16-bit PCM, lossless import, loops carry a `smpl` chunk
Measured on the delivered files (RMS / sample peak in dBFS; seam = level step over the loop point in 50 ms):

| File | Content | Length | RMS / peak | Wired |
|---|---|---|---|---|
| `amb/amb_karsk_cellar.wav` | the freight office's archive cellar before dawn: the vault's close room tone, the stove (low fire, the iron ticking), the samovar simmering and once singing, the wall clock, two trains crossing over the vault (rumble, rail joints, dust, the lamp chain), wind and snow at the barred window, the night shift's boots above, pages at Lev's desk | 60 s loop, stereo | −26.2 / −3.0 (seam −0.6 dB) | `L_C4_Tunnels.tscn` ambience; `c4.json` switch `L_C4_TunnelsA` |
| `amb/amb_karsk_tunnel.wav` | Service Tunnel 3 and the siding: the concrete tube's long echo, a draught, water dripping (one steady drip, others at random), a fan in an air shaft, shunting overhead through the ground, the work lamps' hum and one flicker, a train deep above, a plank of the converted wagon settling | 60 s loop, stereo | −25.0 / −3.0 (−1.1 dB) | `c4.json` switch `L_C4_TunnelsB` |
| `amb/amb_berlin_loop.wav` | the tram loop Süd 8 at dawn: cold air, a little snow, the city waking far off, the trolley wire humming and singing in the gusts, tram 74's air compressor (twice), warm air breathing from the advertising column, the first lorry idling at the hatch (tailgate, crates), crane chains of the axis far off, another line's bell far away, early-shift workers crunching past, a murmur at the shelter | 60 s loop, stereo | −24.0 / −3.3 (+1.0 dB) | `L_C4_Annex.tscn` ambience; switch `L_C4_AnnexA` |
| `amb/amb_berlin_annex.wav` | the registry annex: two huge fans behind the grille (blade tones of 31 / 33 Hz beating slowly — the column's breath), fluorescent ballast hum and one flickering tube, tube capsules landing (twice), typewriters muffled behind glass, a card drawer, a sliding ladder, a stamp at the counter, a tram on the street above | 60 s loop, stereo | −25.0 / −3.0 (+0.4 dB) | switch `L_C4_AnnexB` |
| `music/mus_c4_karsk.wav` | sparse low strings in D Aeolian, a cello line descending D–C–Bb–A, the bayan breathing three times (Dm, Dsus2, an open fifth into the loop), soft low plucks, K once on the felt piano | 71.1 s loop (54 bpm, 64 beats) | −22.0 / −5.5 (+0.7 dB) | `L_C4_Tunnels.tscn` music; switches `L_C4_TunnelsA` / `B` |
| `music/mus_c4_berlin.wav` | cool and mechanical in G Aeolian: a muted-piano pulse in 3+3+2, a card machine's dry tick (a heavier feed every two bars), brass chords over the G pedal, a cold harmonic line, B on the celesta, B low on the piano | 53.3 s loop (72 bpm, 64 beats) | −21.0 / −2.3 (−1.9 dB) | `L_C4_Annex.tscn` music; switches `L_C4_AnnexA` / `B` |
| `music/mus_c4_voices.wav` | the closing: a clock on every beat; the Karsk drone and K on the piano, then B on the celesta over the G pedal, then K_B and B together (B's Eb bent to E where they meet), the clock alone again. The first 24 s are a full arc for LS_C4_Voices (≈ 24 s); the loop serves longer scenes | 48.0 s loop (60 bpm, 48 beats) | −21.0 / −1.0 (−1.9 dB) | LS_C4_Voices `{"music": "mus_c4_voices"}` (cine stream) |
| `sfx/c4_stamp_accept.wav` | the surface of the Karsk stamp „ПРИНЯТЬ“ on the siding office's wooden desk in the small wooden booth: the desk's knock, the rubber's slap, the handle's ring — strike at 0.36 s; no ink pad, no low body, high-passed at 190 Hz (round 10: a layer over the film's bed) | 2.0 s | −36.7 / −6.0 | LS_C4_Stamp s2: `{"sfx": "c4_stamp_accept", "db": -5}` at `STAMP_RU[0]`, over the bed `c4cine_stamp_ru` |
| `sfx/c4_stamp_dispatch.wav` | the same for the Berlin stamp „ABGANG“ on the annex counter (linoleum over steel, concrete hall) — the match cut lands on two surfaces in two rooms | 2.4 s | −35.4 / −6.0 | LS_C4_Stamp s3a: at `STAMP_DE[0]`, over `c4cine_stamp_de` |
| `sfx/c4_card_tear.wav` | the perforator splits a card (round 10, re-timed on the picture): the card flexes under the coming lever, at the split (0.12 s) 28 teeth let go in equal steps along the perforation on the picture's ease-out while the fibres hiss with the halves' speed, the last tooth at 0.36 s where the halves come to rest; annex room, from the counter's side | 1.2 s | −40.9 / −9.0 | LS_C4_Stamp s3b: `{"sfx": "c4_card_tear", "db": -6}` at `LEVER[0]` (the bed `c4cine_annex` has the lever's clack) |
| `sfx/c4_train_overhead.wav` | a goods train crossing above a vault: rumble, wheelsets over a rail joint along the train, the vault's low modes, dust trickling, the lamp chain rattling | 13.0 s | −25.3 / −6.0 | `scripts/levels/c4/tunnels_level.gd` (the trains over the vault) |

Level windows enforced by the generator (`c3p2_audio.check_rows`) and `tests/test_c4_cast_audio.gd`: ambiences −28…−21
dBFS RMS, peak ≤ −2.5; music −25…−19, peak ≤ −0.8; one-shots −45…−9, peak ≤ −2.5, ending in silence. Loops: `smpl`
loop = whole file (imported as `LOOP_FORWARD`, checked), |Δ RMS over 50 ms| ≤ 3 dB and the seam step an ordinary step
(music loop points sit between pulses / ticks). Spectral balance matched to the existing mix by band shares: the
Karsk pair was de-rumbled (energy below 120 Hz 55 % / 68 % → 36 % / 38 %, like `amb_berlin_archive` 41 %); loudness
(LUFS≈ −21.4 … −23.8) sits between `amb_berlin_archive` (−23.0) and `amb_karsk_yard` (−21.1). The one-shots sit at
the levels of their relatives (`tram_bell` −27.7 RMS, `stamp_thud` −35.8 / −6 peak). SFX ids never end in `_<n>`
(Audio.sfx would treat them as random variants). Spectrograms + `c4_analysis.json`: `assets/audio/_preview/`.

### Round 10: the cast cues per beat (`tools/audiogen/c4_audio.py`, `scenes/cinematics/ch4_stamp/ch4_stamp.gd`)
The films had their own `c4cine_*` beds (`c4_cine_audio.py`, synced to the pictures and pinned by
`tests/test_c4_cinematics.gd`), so seven cast cues were never heard. Compared per beat (picture, sync, spectrum):
* **Stamps (s2 / s3a): layered.** The beds carry the descent's air, the thump on the contact frame and the lift, but
  their thump is 97 % / 87 % energy below 200 Hz (centroid 151 / 259 Hz) — on small speakers barely a stamp. The cast
  takes added the surfaces (desk knock, rubber slap, handle ring; booth vs. concrete hall) with the same 0.36 s strike;
  now re-voiced as layers without the ink-pad dab (the stamp enters the frame already inked) and the low body, played
  with their beds at −5 dB (≈ 2 dB under equal A-weighted energy with the bed's thump at −4 dB; centroid 590 / 800 Hz).
* **Card tear: moved to s3b.** No card tears in LS_C4_Card (it is found torn); the perforator in s3b splits one — the
  bed has only the lever's clack. Re-timed to the picture (split at `LEVER[1]`, rest at 90 % of the 5-px ease-out),
  annex room, −6 dB (≈ 2 dB under the clack's A-weighted energy).
* **Dropped:** `c4_stencil_brush` (n1 shows the number painted and wet, nobody paints), `c4_bell_once` / `_twice`
  (`c4cine_bell` is the same 1480-Hz bell tram 74 rings in LS_C4_Number n4; the double ring's 0.26 s gap misses the
  picture's 0.75 s; a second bell at once would be a second tram), `c4_lamp_out` (v4: nobody is at the wagon — the
  lamp fails and `c4cine_lamp_out` flickers it in sync; the cue's switch click and 100-Hz ballast hum contradict it).
  Generator, test and disk no longer carry them. Tests: every one-shot the generator builds is heard; the layers start
  with their beds without pitch variation, strike on the contact frames; the tear starts on the split and its last
  tooth lands where the picture's halves rest (`audio_*` cases in `tests/test_c4_cast_audio.gd`).

## Tests
`tests/test_c4_cast_audio.gd` — sheets (rows, 8-frame rhythm, variants, ground speed, size, normal map, feet on the
origin), the rig (every row loads and plays), living portraits (contract, the mouth opens and the eyes close in every
expression, expressions differ, opaque), individual silhouettes (IoU vs each other and 16 existing figures) and faces,
names and speakers (every speaker of the C4 dialogues and every `char_id` of the two level shells has a sheet and a
portrait), every WAV's format, loop chunk, import loop mode and length, levels and seams on the PCM, wiring (shell
ambience / music ids, the four switch ambiences of `c4.json`, every c4 sound a C4 cinematic cue names), and (round 10)
every one-shot heard and the LS_C4_Stamp layers in sync with the picture.
