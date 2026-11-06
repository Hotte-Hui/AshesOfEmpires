# Asset manifest — Chapter 4 part 1 exploration: finds under the Karsk freight yard and at the tram loop Süd 8, „Ilses Puppe“, „Der Hebelrahmen“ (area: explore_c4)

Owner: exploration c4 specialist · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: documentation/C4_DESIGN.md §4/§6/§7,
TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9 (user request this round: Chapter 4 part 1, content, look, feel, fun).

Everything listed here is **original work**, written for this game or generated procedurally by the project scripts
below on 2026-11-06. No pixel, sample or melody was taken from `documentation/references/` or any other source; no
downloads, no AI media, no recordings. Colours come from `data/chapters/c4.json` palettes `tunnels` (lever frame) and
`annex` (Ilse's drawing) plus documented extras: the enamel green of the track diagram (`BOARD` #0E1914 / #15241C /
#1E3226 / #2A4434 in `gen_mg_c4_lever.py`), the moon-white route light #EEF2F5 and the signal green #6FD08C (drawn by
`lever_game.gd`), and a child's five wax crayons (`CRAYON` yellow #E8C04A, blue #34508C, brown #7A5230, black #24262B,
green #4F7A3A in `gen_explore_c4.py`). Pixel fonts: the hand-made bitmaps of `tools/pixelgen/mg_r7_v_kit.py` (SMALL 5×7
with the Cyrillic letters used, TINY 3×5 digits) — no font file is read or traced; Ilse's signature is drawn stroke by
stroke. No regime insignia anywhere (§12.4). Historical model of the mini-game: the general principle of mechanical
interlocking (points, route and signal levers held by locking bars, a locking table) — the frame itself, its track
diagram and its lever set are fictional, no real frame type, plan or plate was copied. Licence: original project work
(same terms as the rest of the game).

## Content (text, data)

| File | What |
|---|---|
| `data/explore/c4_tunnels.json` | 17 entries under the level key `L_C4_TunnelsA` (Alexei). Archive cellar, scene A: a mouse at the sugar (secret), the stamp box („Отдел Т“ hook empty), the personnel card index (Gerassimow, „fragte nach Wagen 24 318“), Lev's photo (his granddaughter turned down, card `hist.soviet.order_270`), the samovar's second glass, the stove (blank repatriation questionnaires), the 1941 air-raid sign, a chat with Lev (after `c4a_talk_tunnel`). Tunnel and siding, scene C: the live 1941 field telephone, new cables on old hooks, the lever frame (mini-game), a house scratched into a bench board (secret), the conversion kit (card `hist.soviet.special_settlements`), the painters' corner („Arbeitskolonne 7“), the heap of number plates, the wagon's maintenance marks („ausgemustert 03.1963“), the exit portal |
| `data/explore/c4_annex.json` | 18 entries under the level key `L_C4_AnnexA` (Konrad). Tram loop, scene B: house No. 11 (Marta's window, hatched „freizumachen“ on his own plan), a doll's shoe (secret), three storeys of wallpaper on the party wall with Anna's embroidered towel (card `hist.reich.ostarbeiter`), the „Berlin baut“ poster, Marta's cab, Ilse at the last window, the view through the hoarding, a chat with Marta (after `c4b_talk_ilse`) and the side task „Ilses Puppe“ (Marta asks → the 1941 cellar breakthrough from No. 11 into No. 9, the doll without an inventory number and Ilse's drawing → back to the tram). Annex, scene D: the fans of „Blatt 3“, Brandt's card in drawer Süd 3 (secret, „Auskunftsperson: Kollege“), the label „Haushaltskartei Süd“ („Kinder auf Beiblatt“), the card trolley (Tuesday 18th „Abgabe Kordon“, a birthday cake), the waiting bench under the number display 17, the perforating machine („links Reich, rechts Gegenstelle“), a chat with the guard |
| `data/explore/c4_history_soviet.json`, `c4_history_reich.json` | the four real-history cards with their sources (fact-checked 06.11.2026, ≥ 3 web sources each; the sources appear only in the credits' source list, never on the cards); the fourth, `hist.reich.denunciation` (Gellately 1990, Mallmann/Paul 1991), at the annex's waiting bench |
| `data/locale/de_explore_c4.json`, `de_history_c4.json` | all German texts (finds, chats, task, mini-game, place labels; the three cards) |
| `assets/environments/karsk_tunnels/explore_hotspots.json`, `berlin_annex/explore_hotspots.json` | the exp_* hotspots plus the `info` art contract (stand, focus, what to paint) for the env streams |
| `scenes/levels/L_C4_Tunnels.tscn`, `L_C4_Annex.tscn` | appended Find_* / Chat* / Task_* nodes (script `scripts/ui/minigames/lever_spot.gd`) |

## Mini-game „Der Hebelrahmen“ (`scenes/ui/minigames/LeverFrame.tscn`)

| Asset | Generator | What |
|---|---|---|
| `assets/ui/minigames/lever/lever_back.png` (400×148) | `py -3 -P tools/pixelgen/gen_mg_c4_lever.py` | the tunnel niche: formwork concrete in cage-lamp light, the enamel track diagram (tunnel 3, points 1–3, track 1 with wagon 24 318, track 2, main line, the taped-over track 0), the route indicator box, signal lamp sockets, the cast-iron frame of 1941 with slots, brass plates 1–8 and lock pip sockets, the night shift's route book, the painted locking table |
| `assets/ui/minigames/lever/lever_indicator.png` (3 × 64×9) | same | lit indicator texts „ПУТЬ 1“, „ГЛАВН.“, „КОРДОН 17“ |
| `assets/ui/minigames/lever/lever_closeup.png` (200×120) | same | the find's close-up: „КОРДОН 17“ lit over track 0, the tape peeled from „ПУТЬ 0“, the bright-worn handle of lever 6 |
| `assets/ui/minigames/lever/lever_layout.json` | same | every coordinate the game draws over the art |
| `assets/audio/sfx/mg_c4_lever_pull.wav`, `mg_c4_lever_back.wav`, `mg_c4_lever_locked.wav`, `mg_c4_route_set.wav` | `py -3 -P tools/audiogen/mg_audio_c4.py` | synthesized: lever pulled over / put back (catch, quadrant slide, thump, locking bar), a refused lever (hard stop, never a buzzer), an order carried out (signal wire, far arm, one bell stroke) |
| `scripts/ui/minigames/lever_logic.gd`, `lever_game.gd`, `lever_spot.gd` | hand-written | the rule (pure), the UI (keyboard, pad, mouse, demo_solve), the exploration spot of every C4 find |

## Mini-game „Die Lüftungsklappen“ (`scenes/ui/minigames/VentFlaps.tscn`, round-9 fix compl-01)

| Asset | Generator | What |
|---|---|---|
| (no image file) | drawn at run time by `scripts/ui/minigames/vent_game.gd` | the machine room of Nebenstelle Süd in pixel art (art px ×3 / ×2): two turning fans in their housing, the plenum, three ducts with butterfly flaps and notched handles, rising air, three dials with the green band of Blatt 3, the duct lamps, the fault bell and lamp, Konrad's sheet pinned on the wall; colours: steel ramp #15191C … #98A4AC, wall #1C2321 / #232D2A, paper #E6E1CF, the lamp red #E0483A and green #6FD08C, brass #C9A35A / #E6C27A / #8A6A30, air #D4EBE4 |
| `assets/audio/sfx/mg_c4_flap_open.wav`, `mg_c4_flap_close.wav`, `mg_c4_alarm_bell.wav`, `mg_c4_air_settled.wav` | `py -3 -P tools/audiogen/mg_audio_c4.py mg_c4_flap_open mg_c4_flap_close mg_c4_alarm_bell mg_c4_air_settled` | synthesized (numpy, deterministic): a flap handle one notch open / shut with the air in the duct, the electric fault bell (striker on a small steel gong), the fault acknowledged (relay, last gong tap, the fans settling) |
| `scripts/ui/minigames/vent_logic.gd`, `vent_game.gd` | hand-written | the rule (pure: fan curve, coupled ducts, one balance among 125 positions, no dead end), the UI (keyboard, pad, mouse, demo_solve by synthetic keys, auto mode, hints, text scale, high contrast) |

Historical model: the general principle of balancing a ventilation system with butterfly dampers (every damper changes
the pressure and so the flow in the other branches; a longer duct needs a wider damper) — the plant, its numbers and the
sheet are fictional.

## Side task close-up

| Asset | Generator | What |
|---|---|---|
| `assets/explore/c4/ilse_drawing.png` (240×150) | `py -3 -P tools/pixelgen/gen_explore_c4.py` | Ilse's wax-crayon drawing on squared exercise-book paper: house No. 9 at night with every window lit, three small figures in one window, tram 74, a moon, signed ILSE |

The tunnels' side task „Wir sind vierzehn“ (round-9 fix compl-02: four Task_* spots on wagon 24 318, the hand-in chat
with Lev) and the fourth card `hist.reich.denunciation` (compl-05, at the waiting bench) are text and data only — no new
image or sound.

## Checks

`tests/test_c4_explore.gd` (data, cards, placement and spacing, gates, memory/NPC rule of the spot, the side task, the
drivers' loop, the real Game path with the live Story at every C4 exploration pass, memory card counts, the mini-game
rule and scene, art/layout/sounds; since the fix round also „Wir sind vierzehn“ and the `vent_*` cases of „Die
Lüftungsklappen“). Windowed capture: `godot --path . --script res://tests/visual/c4_explore_shots.gd
-- --shots=<dir> [--scale=1.5] [--hc=1]` (UIRoot, synthetic keys, demo_solve; writes no saves); the flaps:
`tests/visual/c4_vent_shots.gd -- --shots=<absolute dir>`.
