# Asset manifest — Chapter 4 part 2 exploration: the Karsk locomotive depot, the Ostbahnhof and Kolonnenstraße 14, „Ein Paket über die Linie“, „Ein Korb für Frau Grabowski“, „Die Drehscheibe“, „Die Gepäckwaage“ (area: explore_c4p2)

Owner: exploration c4p2 specialist · Date: 2026-11-06 · Engine: Godot 4.7.2 · Contract: documentation/C4P2_DESIGN.md
§4/§6/§7, TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9 (user request this round: a longer game, content, look, feel,
fun; places lived-in and people placed with intent).

Everything listed here is **original work**, written for this game or generated procedurally by the project scripts
below on 2026-11-06. No pixel, sample or melody was taken from `documentation/references/` or any other source; no
downloads, no AI media, no recordings. The two mini-game stages are drawn in code (pixel art in art px, ×3, ×2 for
larger text) from documented colour constants in their scripts (the depot yard's cinders, snow and tar roof, the brass
of a decimal scale, the tiled wall of a station hall); no texture file is read. No regime insignia anywhere (§12.4):
the permits in the texts carry „zwei Stempel“, never an emblem; the enamel signs say what the Corridor allows. Names of
people in the finds are fictional (Saizew on Irina's duty board, Grigori, Kolja, Frau Grabowski, the tenants Lenz,
Schulz, Pohl, Mertens, Kühn, Brettschneider of the house puzzle) — no list of real victims, no real person. Historical
models of the mini-games: the general principle of a locomotive turntable with a locking bolt and of a decimal
platform scale with sliding weights — no real machine, plan or plate was copied. Licence: original project work.

## Content (text, data)

| File | What |
|---|---|
| `data/explore/c4p2_karsk.json` | 24 entries under the level key `L_C4P2_KarskA` (Alexei). Coal stage, scene A (Monday dawn, until `c4e_inspect_notice`): Irina's duty board (seven drivers, passport numbers and registrations, one marked „krank“ in red pencil — card `hist.soviet.propiska`), the canteen hatch and its radio (grain figures, then a waltz), the water crane wrapped in straw (three winters of repairs), the Western shoes beside the issued felt boots, Lena's mitten nailed to a trestle post (secret), the dog „Inspektor“ in the ash pit, the guard at the barrel fire (nineteen, from Kursk, turning a pair of darned gloves), the back of the tarpaulin, a chat with Maria Gorelowa (after `c4e_talk_maria`: the needle, the children's home behind the water tower). Showcase and platform 1, scene B (Tuesday evening): the tarpaulin's front and the shovel handle behind the tear, „А. М. 1949“ at the foot of Alexei's signal (secret), the polished show engine (brass plate 1939), the brass band (Grigori, Irina's husband, on the tuba), caviar and kasha, the press minder (chat; card `hist.soviet.foreign_correspondents`), the turntable (mini-game), a chat with Lev under the lamp (after `c4g_inspect_card`, until `c4g_choose`: papers from Brest, 1940), two clocks over the gate („Korridorzeit“), families at the sleeping car, and the side task „Ein Paket über die Linie“ |
| `data/explore/c4p2_berlin.json` | 21 entries under the level key `L_C4P2_BerlinA` (Konrad). Ostbahnhof, scene A (Monday evening, until `c4f_inspect_book`): the liaison booth at the barrier (a tea glass and a stamp pad at one desk), the baggage counter's decimal scale (mini-game), the family's permit in cellophane, a chat with Marta (after `c4f_talk_marta`: „mit Koffer?“), the kiosk (one headline; the Swedish paper sold out — card `hist.reich.schriftleitergesetz`), the green car's frosted hatch, the porters No. 14 and No. 31, the station clock at 20.31, a return ticket never used (secret). Courtyard, scene B (Tuesday night): a chat with Kuhnert (until `c4h_solve_house`), a chat with Hanna (after `c4h_talk_hanna`, until `c4h_solve_house`), the frozen laundry (Tuesday is washing day: the drying loft is open), Ilse's house drawn into the frost of the stair door (secret), the cellar hatch and the wartime shelter route under all three wings, the lit windows (card `hist.reich.blockleiter`), the dustbins („HH 3“ empty since October), the carpet-beating rack and the house rules, the cobbler's souterrain (the house's census in shoes), and the side task „Ein Korb für Frau Grabowski“ |
| `data/explore/c4p2_history_soviet.json`, `c4p2_history_reich.json` | the four real-history cards with their sources (fact-checked 06.11.2026 against ≥ 3 web sources each, see the `doc` of each file; the sources appear only in the credits' source list, never on the cards) |
| `data/locale/de_explore_c4p2.json`, `de_history_c4p2.json` | all German texts: finds, chats, both tasks, both mini-games, the place labels, the voice from the window (`char.grabowski.name`), the four cards |
| `assets/environments/karsk_c4p2/explore_hotspots.json`, `berlin_c4p2/explore_hotspots.json` | the exp_* hotspots plus the `info` art contract (stand, focus, what to paint) the two env streams painted to — checked against their layers on 06.11. (the barrel fire and the signal's foot moved onto env-karsk's actors) |
| `scenes/levels/L_C4P2_Karsk.tscn`, `L_C4P2_Berlin.tscn` | appended Find_* / Chat* / Task_* nodes (script `scripts/ui/minigames/lever_spot.gd`: memory-aware gates, a chat only while its NPC stands there) |

## Side tasks (§12.9; rewards are human beats, no history card)

| Task | Steps (all in one walk area) |
|---|---|
| `karsk.task.parcel` „Ein Paket über die Linie“ (scene B) | the grandmother on platform 1 (`exp_task_parcel`, speaker `babushka`) → the sack scale in the sand-drying house (`exp_task_scale`: 5,6 kg, the jar of lime honey is the 600 g too much) → back to her (chain on the same spot: a letter instead of the honey — „Kolja, der Honig wartet auf dich. Komm ihn holen.“ — and Alexei does not tell her what happens at the coal stage to those who come back) → the signal wire left from his January repair (`exp_task_wire`) → the sleeping-car conductor (`exp_task_conductor`, speaker `conductor`): a present for his nephew Kolja; she must not wave, waving is noticed |
| `berlin.task.basket` „Ein Korb für Frau Grabowski“ (scene B) | a basket on a washing line from the dark kitchen window, front wing, 2nd floor (`exp_task_basket`; Frau Grabowski's coal card is blocked since her son went over the Line; a voice only, the dialogue box shows the silhouette) → two shovels of Hanna's briquettes by the cellar hatch (then a third) (`exp_task_coal`) → she pulls it up and puts her light on: „Im Dunkeln friert man weniger, weil man seinen Atem nicht sieht.“ |

## Mini-game „Die Drehscheibe“ (`scenes/ui/minigames/Turntable.tscn`)

| File | What |
|---|---|
| `scripts/ui/minigames/turntable_logic.gd` | the rule, pure and deterministic: a 30-m bridge with the shunting engine („Kukuschka“) on it; a tap sets it ~4 cm (impulse 0.7 °/s), holding drives it up to 18 °/s, released it coasts ~100°, the band brake stops it in ~8°; a pull is refused while it moves, between the tracks, at the entry track, at another stall, or more than 0.2° (≈ 5 cm at the rim) off stall 7; `next_move()` reaches stall 7 from every angle (tested) |
| `scripts/ui/minigames/turntable_game.gd` | the stage (the yard with a stack of sleepers, the shunters' brazier, a floodlight and its pool of light, footprints, banked snow; the roundhouse roof with numbered plates over stalls 1–9 and stall 7's gate lit; the pit with its scale; the bridge, the operator's empty hut, the engine with steam; the loupe on the rail joint ahead of the chimney end, „fluchtet“ / „… daneben“ / „Stand 7 noch …° entfernt“), side panel (scale, speed), keys (←/→ hold or tap, Space brake, E pull, R), pad (LB/RB or d-pad, A brake, X pull, Y), mouse (drag the rim, right button brakes, wheel nudges, click the loupe), hints after two refusals (Settings `puzzle_hints` 0/1/2), compact ×2 layout, high contrast, reduced motion, `demo_solve()` by synthetic keys (≈ 11 s) |
| `assets/audio/sfx/mg_c4p2_tt_start.wav`, `_brake`, `_bump`, `_lock`, `_roll` (2-s loop with a RIFF 'smpl' chunk) | `py -3 -P tools/audiogen/mg_audio_c4p2.py` (numpy, deterministic, no samples) |

## Mini-game „Die Gepäckwaage“ (`scenes/ui/minigames/LuggageScale.tscn`)

| File | What |
|---|---|
| `scripts/ui/minigames/luggage_logic.gd` | the rule: a big sliding weight in 5-kg notches (0–50 kg), a small one in 0.1-kg steps (0–5 kg); the tongue plays in at the mark when they equal the load (±0.5 kg of free swing); three weighings — the suitcase of presents for the grandmother in Karsk 23,6 kg (over the Corridor's 20 kg; the mother repacks coffee, oranges and a tin of ham), the suitcase again 19,8 kg, the parcel 3,8 kg: the same 23,6 kg in a form the Corridor allows; no dead end from any position (tested) |
| `scripts/ui/minigames/luggage_game.gd` | the stage (the hall's tiled wall, the enamel signs „Gepäck“ and the Corridor's luggage rule, a timetable, the station clock at 20.31, the platform with the suitcase or the parcel, the column and the swinging beam with its two weights, the tongue in its frame, the clerk in his cap behind the grille whose stamp comes down on each good reading), the slip „Gepäckschein D 303“ in the side panel, keys (←/→, ↑/↓ held to slide, Page Up/Down a kilo, E/Enter/Space read, R), pad (d-pad, LB/RB a kilo, A, Y), mouse (click or drag a weight, wheel over a rail, „Ablesen“), hints, compact layout, high contrast, reduced motion (the beam does not swing), `demo_solve()` by synthetic keys |
| `assets/audio/sfx/mg_c4p2_poise_coarse.wav`, `mg_c4p2_poise_fine.wav`, `mg_c4p2_beam_knock.wav`, `mg_c4p2_stamp.wav` | `py -3 -P tools/audiogen/mg_audio_c4p2.py` |

## Close-ups (`assets/explore/c4p2/`, 240×150, shown ×3 by the discovery view)

| File | What |
|---|---|
| `lena_mitten.png` | `karsk.depot.lena_mitten`: the foot of a coal-stage trestle post at dawn, a rusty horseshoe nail through the cuff of a small grey knitted mitten, darned once, frost on the wool, „Lena“ cross-stitched in red; the coal stage's lamp warming the post's edge |
| `ilse_frost_house.png` | `berlin.k14.ilse_drawing`: the stair door's pane grown over with frost ferns; drawn into it with a child's finger a five-storey house, every window lit (the cellar too), smoke from the chimney, the door open; melt water running from the strokes; Konrad's breath already clouding one corner |
| `signal_scratch.png` | `karsk.depot.signal_scratch`: the foot of the restored signal mast — fresh paint with drips down to a hand's width above the ballast, below it the old rust with „А. М.“ and „1949“ scratched to the bare metal; base plate, ballast, snow |

All three: `py -3 -P tools/pixelgen/gen_explore_c4p2.py` (deterministic; colours from `data/chapters/c4p2.json` palettes
`depot` and `courtyard` plus the documented door green and wool greys in the generator's header; letters drawn stroke by
stroke, no font file).

## Tests and tools

| File | What |
|---|---|
| `tests/test_c4p2_explore.gd` | 20 cases: data, texts and typography, the four cards, Explore validation, placement and spacing against the env manifests and the art contract, gates and memory scenes, both side tasks, the drivers' passes (autoplay and inputplay — a pending note names the passes the drivers still lack), the real Game path on both level files with the live Story, memory cards per walk area, both mini-games (rules, scenes, keys, pad, mouse, hints, full solves by keys, compact layout, hint modes), sounds |
| `tests/visual/c4p2_explore_shots.gd` | windowed capture of both mini-games through the real UIRoot (`--shots=<dir> [--game=turntable|luggage] [--scale=1.5] [--hc=1]`) |
| `tools/audiogen/mg_audio_c4p2.py` | the nine sounds above |
| `tools/pixelgen/gen_explore_c4p2.py` | the three close-ups above |
