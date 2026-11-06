# Asset manifest — Chapter-3 mini-games (area: minigames r7, Veltrava)

Owner: minigames r7 (Veltrava) · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: TECHNICAL_ARCHITECTURE §12.8
(user request this round: more play time, new mini-game ideas, finish Chapter 3).

Everything listed here is **original work**, generated procedurally by project scripts. No pixel, glyph, sample or
melody was taken from `documentation/references/`, a font file or any external source; no downloads, no AI media.
The three bitmap fonts (7×11 flap capitals, 5×7 sign letters incl. the Cyrillic of the station signs, 3×5 plate
digits) are hand-made in `tools/pixelgen/mg_r7_v_kit.py`. Colours: `data/chapters/c3.json` palettes `veltrava`
(station) and `palais` (palace) plus documented mixes of two palette entries (skin tones, camel, charcoal); the
greens of scarves and the Soviet delegation pin use `veltrava.patina`. **No state insignia anywhere**: the
"delegation pins" are a fictional conference system told apart by shape (square Reich delegation, triangle Soviet
delegation, diamond observers, circle commission). The maker's plate "W. HOLUB · VELTRAVA" is fictional; no brands.
Licence: original project work (same terms as the rest of the game).

## The two mini-games

| Explore entry | Scene / scripts | Place (hotspot, world px) | Game |
|---|---|---|---|
| `veltrava.station.flap_board` (detail, Alexei) | `scenes/ui/minigames/FlapBoard.tscn` · `flap_game.gd` + `flap_logic.gd` | `L_C3_Station` `exp_flap_board` [548, 304] below canopy column 3; world cue `FlapBoardCue` (`flap_world_cue.gd`) | The arrivals board ANKUNFT · ПРИБЫТИЕ · ARRIVÉE hangs in its top row at Alexei's own train. Six flap drums (hour 24, tens 6, units 10, from 10, via 8, platform 8 flaps) only fall forward; four couplings (units→tens carry on 9→0, tens→hour, from→via, track→via) make the order matter. Target = the printed timetable's special train **8:41 MOSKVA über KARSK, Gleis 5**. The line engages by itself; „Probelauf“ names what differs. The KARSK card is new (white, no yellowing) — Alexei's detail. |
| `veltrava.hall.cloak_tokens` (detail, Konrad) | `scenes/ui/minigames/Cloakroom.tscn` · `cloak_game.gd` + `cloak_logic.gd` | `L_C3_Hall` `exp_cloak_tokens` [205, 300], beside the text agent's `veltrava.hall.cloakroom` (240); world cue `WenzelCue` (`cloak_world_cue.gd`) behind the counter | Session break; Herr Wenzel (garderobier since 1927) hung the coats on the wrong hooks. Round 1: four guests (Dr. Imhof, Frau Orlova, M. Duval, Herr Bauer), five coats; round 2: three of them come back for their hats, wearing their coats; six hats. Clues: pin shape, newspaper (Berlin / Moscow / Zurich), scarf colour, dictionary; the hook numbers mislead. Elena Weiss's charcoal coat with the wine-red scarf (check 27) stays — consistent with the cloakroom find and Frau Brunner's chat. |

## Generators (deterministic; a re-run reproduces every file byte for byte — checked 2026-11-06, 28 files)

* `py -3 -P tools/pixelgen/gen_mg_flap.py` → `assets/ui/minigames/flap/` (imports under the shared lock)
* `py -3 -P tools/pixelgen/gen_mg_cloak.py` → `assets/ui/minigames/cloak/`
* `tools/pixelgen/mg_r7_v_kit.py` — shared module of both (palettes, canvas, fonts); writes nothing itself
* `py -3 -P tools/audiogen/mg_audio_r7_v.py` → `assets/audio/sfx/mg_flap_*`, `mg_cloak_*` (numpy only)

Seeds are `crc32` of names; drawn 1:1, binary alpha, shown x3 (x2 in the compact layout above 100 % text scale).

## Files

| Path | Size (art px) | Use |
|---|---|---|
| `assets/ui/minigames/flap/flap_board.png` | 252×110 | Iron housing with rivets, trilingual header, date plate 12.02.1964, column labels, rows 2–3 (11:05 KORDON 1, 14:30 WIEN LINZ 2), empty windows of row 1, row lamps, maker's plate |
| `…/flap/flap_faces.png` | 1992×108 (6 rows of 18 px faces) | Every flap card of every drum of row 1 (worn cards, the new KARSK card) |
| `…/flap/flap_faces_hc.png` | same | High-contrast cards (white on black) |
| `…/flap/flap_hatch.png` | 252×34 | Open service hatch: axle, brass end caps, bearing blocks, the brass carry pin and three bent wire hooks |
| `…/flap/world_flap_board.png` | 3 × 84×41 | World prop for column 3: jammed (2 twitch frames), restored |
| `…/flap/flap_closeup.png` | 240×96 | Find close-up (DiscoveryView): the restored line, the new KARSK card, the lit row lamp |
| `…/flap/flap_layout.json` | — | Module rects, flap lists, start / target, static rows, couplings + hatch rects |
| `assets/ui/minigames/cloak/cloak_back.png` | 320×150 | Green wall with damask stripes, token board (MARKEN, five pegs empty), walnut hat shelf, brass rail, hooks with plates 12 · 7 · 31 · 44 · 27, lamp glow |
| `…/cloak/cloak_front.png` | 320×150 | Walnut counter with brass edge and panels, ledger, tray of polished spare plates, counter bell, lamp |
| `…/cloak/cloak_coats.png` | 5 × 40×78 | Loden (square pin, Berlin paper), camel (diamond pin, green scarf, Zurich paper), charcoal lady's coat (circle pin, wine-red scarf, buttoned left), navy (circle pin, dictionary), dark brown with karakul collar (triangle pin, Moscow paper) |
| `…/cloak/cloak_hats.png` | 6 × 28×16 | Grey homburg with tram ticket, karakul cap, wine-red knitted cap, grey homburg with the square pin, rabbit-fur ushanka, black homburg with green band |
| `…/cloak/cloak_guests.png` | 6 × 4 cells of 64×72 | Busts of the four guests in the suit and in their coat, each neutral / pleased / puzzled |
| `…/cloak/cloak_wenzel.png` | 3 × 46×60 | Herr Wenzel behind the counter (polishing, blink, talking) |
| `…/cloak/cloak_tokens.png` | 5 × 14×14 | Brass coat checks 12, 31, 7, 44, 27 |
| `…/cloak/world_wenzel.png` | 3 × 20×30 | Herr Wenzel at world scale for `L_C3_Hall` (idle, blink, plate to the light) |
| `…/cloak/cloak_closeup.png` | 176×120 | Find close-up: the last coat on hook 31, the wine-red cap on the shelf |
| `…/cloak/cloak_layout.json` | — | Hook / shelf / token / guest positions and cell sizes |
| `assets/audio/sfx/mg_flap_clack_1..4.wav` | 0.12 s | One card falling onto the next (four pitches, Audio picks one) |
| `assets/audio/sfx/mg_flap_turn.wav` | 0.12 s | Ratchet pawl over one tooth (the thumb on the drum) |
| `assets/audio/sfx/mg_flap_rattle.wav` | 1.15 s | „Probelauf“: motor up, cards rattle past, nothing catches, motor down |
| `assets/audio/sfx/mg_flap_engage.wav` | 0.95 s | The line engages: settling cascade, the stop, the lamp relay (understated) |
| `assets/audio/sfx/mg_cloak_token.wav` | 0.6 s | Brass check on walnut |
| `assets/audio/sfx/mg_cloak_coat.wav` | 0.8 s | Hanger off the brass rail, wool on wool |
| `assets/audio/sfx/mg_cloak_hat.wav` | 0.45 s | Felt hat taken from the shelf |
| `assets/audio/sfx/mg_cloak_bell.wav` | 1.6 s | Counter bell, struck once |

All WAV: 44.1 kHz, 16-bit, mono, peak −4 … −9 dBFS.

## Data and code (not assets, listed for completeness)

`data/explore/minigames_r7_v.json` (2 entries, area `veltrava`), `data/locale/de_minigames_r7_v.json` (find texts in
the protagonists' voices, all `mg.flap.*` / `mg.cloak.*` strings), `tests/test_minigames_r7_v.gd`, capture harnesses
`tests/visual/minigames_r7_v_harness.gd` (UI over a screenshot, `--scale=1.5 --hc=1` variants) and
`tests/visual/minigames_r7_v_ingame.gd` (real Main/Game path: prompt → mini-game → DiscoveryView → world cue).
