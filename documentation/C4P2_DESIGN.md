# CHAPTER 4, PART 2 — „Stimmen unter Beton“ (second half) — design contract

Status: AUTHORED 2026-11-06 (round 10). Single source of truth for every contributor of this round (story data,
env-karsk, env-berlin, cinematics, puzzle UI, cast + audio, exploration; the evidence board and the polish streams read
it). Builds on C4_DESIGN.md (part 1 — its ids, texts and rules stay valid), C3P2_DESIGN.md, STORY_BIBLE §2/§3/§6/§7/§8,
CHARACTER_BIBLE, WORLD_BIBLE, TECHNICAL_ARCHITECTURE §11–§13 and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md`
(„Ein Archivpfad und ein Transportpfad müssen zusammengeführt werden. Entscheidung: Schutz von Menschen vor
Geschwindigkeit der Veröffentlichung.“). German protagonist: **Konrad Adler** (`konrad`); the pre-rename name never
appears.

**What part 2 is:** Monday and Tuesday, 17 and 18 February 1964 — the two days before the special run C-17/45, Tuesday,
23.40. In Karsk, Alexei is sent to the locomotive depot at dawn. Irina Belova has a typed order on her sill: one engine
and one crew for the special run, „Das Personal schweigt“ — and seven drivers she will not send. Behind the coal stage
eleven of the fourteen of wagon 24 318 shovel coal as „Kolonne 4“: the people brought in the January run, now loading
the trains that will bring the next ones. Maria Gorelowa — the woman who scratched „Wir sind vierzehn“ into the wall —
tells him what C-17 means at the receiving end: the card arrives before the person, the filtration asks every day why
she survived, her children are in a children's home, her husband (a Black-Sea German) in a special settlement. On Monday
evening in Berlin, Konrad meets Marta at the Ostbahnhof, where the Corridor express leaves for Karsk and a green
windowless car stands ready for Tuesday. His decision at the annex counter (c4d) has consequences now: Marta was
questioned for three hours and lost her line (named) — or the Staatspolizei asks about "a gentleman from the Bauamt who
knew no name" (protected). Either way the households with the red tab are collected on Tuesday evening, and the children
with them. Konrad gives the Swedish correspondent Nils Ekdahl — who travels to Karsk on a press tour and will be shown
"an engineer who repaired a signal" — the German half of card 0417 and a tracing of his own Blatt 7, laid between pages
212 and 213 of a Swedish guidebook. **The shared object crosses the Line:** on Tuesday the same book opens on a canteen
table in Karsk. Lev borrows the Russian half from the box „C-17/45 – annehmen“ for one hour; under a lamp in the sand
house the perforation closes and a round stamp „C-17“, set half in German, half in Russian, closes with it: one card,
two states, one order. The archive path and the transport path are joined. At the westbound express Alexei has to decide
what Ekdahl takes tonight: everything — the photographs, Lev's carbons with Archipov's hand, the list of Kolonne 4 — so
that a neutral witness stands at Tür Ost at 23.40 and Stockholm prints it on Thursday; or only the numbers, and the film
stays in Karsk until Lev, Maria and Konrad's people are out of the line of fire. Tuesday night in Berlin, Konrad gets
Ilse out of his sister Hanna's flat at Kolonnenstraße 14 — a house his own office has already hatched for clearance — by
the one way through the house that no household card knows, while Kommissar Wendt and the Blockleiter wait in the gate
passage. 23.40: Berlin, Kordon-17 and Karsk on one clock. Nothing is resolved for good: a handover is suspended or a
wagon leaves, and Chapter 5 begins with the price.

Target play time **15–20 min** main path: opening film ≈ 0.2 · Karsk depot (Alexei) ≈ 4 · Ostbahnhof (Konrad) ≈ 4.5 ·
the showcase and the join (Alexei, puzzle + decision) ≈ 5 · Kolonnenstraße 14 (Konrad, puzzle) ≈ 4.5 · match cuts +
closing ≈ 1.5.

---------------------------------------------------------------------------------------------------------
## 1. Flow

```
… c4d_choose ══> c4d_completed ──> LS_C4_Voices (existing) ──> LS_C4P2_Depot (new) ──> level load
 ──> L_C4P2_KarskA  (Alexei, Karsk depot, Monday dawn)   c4e_inspect_notice ══> c4e_completed ──> LS_C4P2_Steam   (match cut: steam)
 ──> L_C4P2_BerlinA (Konrad, Ostbahnhof, Monday evening) c4f_inspect_book   ══> c4f_completed ──> LS_C4P2_Book    (match cut: the book)
 ──> L_C4P2_KarskB  (Alexei, depot showcase, Tuesday)    c4g_choose         ══> c4g_completed ──> LS_C4P2_Express (match cut: the tail lamp)
 ──> L_C4P2_BerlinB (Konrad, Kolonnenstraße 14, Tuesday) c4h_talk_wendt     ══> c4h_completed ──> LS_C4P2_Clock ──> L_X1_Montage
     (existing montage → end card listing all eight decisions → credits)
```
* The unchanged engine needs ONE linear scene chain ending in the non-quest montage (C3_DESIGN §1). The four new scenes
  are inserted between `L_C4_AnnexB` and `L_X1_Montage`: `L_C4_AnnexB.next_scene = L_C4P2_KarskA` (the only modified
  record) … `L_C4P2_BerlinB.next_scene = L_X1_Montage`; `slice_end_requires` = all seventeen quest events.
* Two level files, each hosting two Story scenes that are **not** consecutive: `scenes/levels/L_C4P2_Karsk.tscn`
  (`L_C4P2_KarskA`, `L_C4P2_KarskB`) and `scenes/levels/L_C4P2_Berlin.tscn` (`L_C4P2_BerlinA`, `L_C4P2_BerlinB`). Every
  protagonist change crosses a city, so every scene starts with a level load (no in-level switch: the two men are never
  in one place in Chapter 4 — STORY_BIBLE §6: Chapter 4 "alternates on shared objects", Chapter 5 gets the first
  connection, a phone line; `scene_partner()` = "" for all four, the c4p2.json `switches` say `"partner": "none"` and
  carry the per-scene ambience/music/grade). ChapterExt level keys (Explore `"level"`): `L_C4P2_KarskA`,
  `L_C4P2_BerlinA`.
* Each file has two walk areas separated by a permanent blocker: Karsk — the tarpaulin fence (`tarpaulin`, „Kolonne 4
  hinter der Plane“: the back yard on Monday, the showcase and platform 1 on Tuesday); Berlin — the end of platform K
  (`platform_end`: the Ostbahnhof on Monday, the courtyard of Kolonnenstraße 14 on Tuesday — two places, one file).
  Entry spawns put each scene in its own area; the films carry the time and the city.
* The match-cut sequence on a shared object (the requirement of this round): `LS_C4P2_Book` — Konrad's hand closes the
  guidebook in the dining car (Berlin, Monday) → the same book opens on the canteen table (Karsk, Tuesday). Around it
  two more hard cuts on matched shapes: steam → steam (`LS_C4P2_Steam`), a red tail lamp → a red warning lamp
  (`LS_C4P2_Express`); and the closing on one clock (`LS_C4P2_Clock`, 23.40 in three places — a small rehearsal of the
  Chapter-6 cross-cut, kept to captions and wide shots).

### 1.1 Save and profile compatibility (binding — the round-10 save migration)
* **The migration comes first and is done** (NEXT_STEPS §1): `SaveSystem.rebase_story()` — used by `read_container`
  (every save slot, the load menu, „Fortsetzen“, profile seeding) and by `Memories.snapshot_raw` (menu memories, films)
  — now first calls `SaveSystem.fill_flag_defaults()`: every Story flag of `data/v3/flags.json` that a v3 payload lacks
  gets its default (a deep copy; present values are never touched — a wrong value or type, an unknown key or a missing
  flags dictionary is still refused by `Story.validate_save_json`). `Memories.memory_flags()` fills the same defaults
  for the replayed line variants. The container load reports „Save migrated: Story flags filled with their defaults: …“.
  The Story engine and its Python reference are unchanged (the engine alone still refuses a payload with a missing flag
  — the parity corpus depends on it). Tests: `tests/test_save_migration_r10.gd` (slice-era payloads with 9 flags — the
  real `1.json.bak` shape —, the round-7/8/9 montage forms, mid-chapter saves with dialogue cursors, puzzle attempts and
  pending films, finished playthroughs, memory snapshots, strictness, the byte-identical round trip of a save of this
  build at every stage), `tests/test_save_rebase_r8.gd` (round-9 forms). Checked on copies of the user's real saves and
  profile: all load, `1.json.bak` (slice era) only through the fill.
* **One new flag, `people_protected`** (integer 0–6, default 0; STORY_BIBLE §7: "`people_protected` (count)"), written
  ONLY by `c4g_choose = protect_first`. Rule for every later flag: a new flag is written only by objectives of the
  chapter that introduces it — then the default IS the value an older save's replay computes, and the fill is exact.
  Never add an effect to an existing objective.
* Not flags (derivable from `choice_history`, which every later chapter reads): `witnesses_exposed` (+1 if `c4d =
  name_marta`; +1 if `c4g = publish_now`: Lev's carbons and Maria's testimony leave Karsk with names), `marta_trust`
  (−1 named / +1 protected), `arkhipov_alerted` (1 if `publish_now`), the c4d part of `people_protected` (protect_marta
  counts in `civilian_welfare`, part 1). Chapter 5 adds them as flags if it needs them — by the rule above.
* New events `c4e_completed` … `c4h_completed` (flags.json `events`, before `slice_completed`) are harmless for saves
  that have not reached them.
* Every save a round-9 player can have stays valid: autosaves never store the montage, so the latest is "before
  `c4d_choose`" in the annex — it loads (its 16-flag table filled), the decision now leads to the Karsk depot.
* **Profile snapshots of `L_C4_AnnexB`** (memories, recorded at `c4d_completed` by a round-9 build) name `current_scene
  = L_X1_Montage`; the re-base (round 8) moves them to the scene after the last exit event = `L_C4P2_KarskA` / `alexei`.
  A finished playthrough of an older, shorter chain (`slice_completed` with only a1 … c4d) keeps its scene and stays
  refused — no build ever saved after the finale (no autosave in the montage, the credits lead to the main menu).

---------------------------------------------------------------------------------------------------------
## 2. Story data (data/v3) — ids are binding

### 2.1 Scenes
| id | title_key (de) | protagonist | camera_mode | entry_spawn | quest | exit event | next | level file | render_profile |
|---|---|---|---|---|---|---|---|---|---|
| `L_C4P2_KarskA` | `world.c4e.title` „Lokdepot Karsk, Kohlenbansen (fiktiv)“ | alexei | side_on_2d | `SP_C4P2_Yard` | `q_c4e_depot` | `c4e_completed` | `L_C4P2_BerlinA` | `L_C4P2_Karsk.tscn` | `rp_karsk_depot_dawn` |
| `L_C4P2_BerlinA` | `world.c4f.title` „Ostbahnhof, Korridorbahnsteig – Berlin (alternative Geschichte)“ | konrad | side_on_2d | `SP_C4P2_Platform` | `q_c4f_platform` | `c4f_completed` | `L_C4P2_KarskB` | `L_C4P2_Berlin.tscn` | `rp_berlin_station_night` |
| `L_C4P2_KarskB` | `world.c4g.title` „Lokdepot Karsk, Schauseite und Bahnsteig 1“ | alexei | side_on_2d | `SP_C4P2_Signal` | `q_c4g_press` | `c4g_completed` | `L_C4P2_BerlinB` | `L_C4P2_Karsk.tscn` | `rp_karsk_depot_evening` |
| `L_C4P2_BerlinB` | `world.c4h.title` „Kolonnenstraße 14, Hinterhof – Berlin“ | konrad | side_on_2d | `SP_C4P2_Gate` | `q_c4h_house` | `c4h_completed` | `L_X1_Montage` | `L_C4P2_Berlin.tscn` | `rp_berlin_yard_night` |
`L_C4_AnnexB.next_scene` changes from `L_X1_Montage` to `L_C4P2_KarskA` (the only modified record).
Time: Karsk local time = Berlin time + 2 h (part 1 already cut „Karsk, 7.10“ against „Berlin, 5.10“). The run is
scheduled in **Korridorzeit** (= Berlin time) on the Accord's papers: 23.40 at Kordon-17 is 23.40 in Berlin and 1.40 in
Karsk. Karsk captions use local time.

### 2.2 Quests (title `ui.chapter_c4` „Stimmen unter Beton“ — chapter number 4 in memories / journal)
| id | character | scene | requires_events | completion_event |
|---|---|---|---|---|
| `q_c4e_depot` | alexei | L_C4P2_KarskA | `c4d_completed` | `c4e_completed` |
| `q_c4f_platform` | konrad | L_C4P2_BerlinA | `c4e_completed` | `c4f_completed` |
| `q_c4g_press` | alexei | L_C4P2_KarskB | `c4f_completed` | `c4g_completed` |
| `q_c4h_house` | konrad | L_C4P2_BerlinB | `c4g_completed` | `c4h_completed` |

### 2.3 Objectives
Every inspect objective grants an item (InspectView and the input driver rely on it). One dialogue grants an item at its
last line (`c4g_talk_lev` → `ev_c4_card_ru_original`). `requires` below without the quest prefix.

Karsk depot, Monday 6.10 — Alexei at the coal stage (≈ 4 min):
```
c4e_inspect_order ─> c4e_talk_irina ─┐
c4e_inspect_list ────────────────────┴─> c4e_talk_maria ─> c4e_inspect_notice ══> c4e_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4e_inspect_order` | inspect | `obj.c4e_order` „Lies den Auftrag am Fenster der Dispatcherbude.“ | — | `ev_c4_special_order` | `dispatch_window` |
| `c4e_talk_irina` | dialogue `dlg_c4e_irina` | `obj.c4e_irina` „Sprich mit Irina Belova.“ | inspect_order | — | `irina_window` |
| `c4e_inspect_list` | inspect | `obj.c4e_list` „Sieh dir die Liste am Kohlenbansen an.“ | — | `ev_c4_work_list` | `coal_list` |
| `c4e_talk_maria` | dialogue `dlg_c4e_maria` | `obj.c4e_maria` „Sprich mit der Frau im grünen Kopftuch.“ | talk_irina, inspect_list | — | `maria_coal` |
| `c4e_inspect_notice` | inspect | `obj.c4e_notice` „Lies den Aushang an der Hintertür des Lokschuppens.“ | talk_maria | `ev_c4_press_notice` | `press_notice` |

Ostbahnhof, Monday 20.30 — Konrad at the Corridor platform (≈ 4.5 min):
```
c4f_inspect_board ─> c4f_talk_marta ─┐
c4f_inspect_courier ─────────────────┴─> c4f_talk_ekdahl ─> c4f_inspect_book ══> c4f_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4f_inspect_board` | inspect | `obj.c4f_board` „Lies die Abfahrtstafel am Korridorbahnsteig.“ | — | `ev_c4_departures_east` | `departure_board` |
| `c4f_talk_marta` | dialogue `dlg_c4f_marta` | `obj.c4f_marta` „Sprich mit Marta Vogel am Büfett.“ | inspect_board | — | `marta_buffet` |
| `c4f_inspect_courier` | inspect | `obj.c4f_courier` „Sieh dir die Wagen hinter der Lok an.“ | — | `ev_c4_courier_seals` | `courier_car` |
| `c4f_talk_ekdahl` | dialogue `dlg_c4f_ekdahl` | `obj.c4f_ekdahl` „Sprich mit Nils Ekdahl am Speisewagen.“ | talk_marta, inspect_courier | — | `ekdahl_window` |
| `c4f_inspect_book` | inspect | `obj.c4f_book` „Leg die Kartenhälfte in Ekdahls Reiseführer.“ | talk_ekdahl | `ev_c4_konrad_tracing` | `dining_table` |

Karsk depot, Tuesday 17.30–20.10 — Alexei at the showcase and platform 1 (≈ 5 min):
```
c4g_talk_ekdahl ─> c4g_inspect_book ─> c4g_talk_lev ─> c4g_solve_halves ─> c4g_inspect_card ─> c4g_choose ══> c4g_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4g_talk_ekdahl` | dialogue `dlg_c4g_ekdahl` | `obj.c4g_ekdahl` „Zeig dem schwedischen Journalisten dein Signal.“ | — | — | `signal_post` |
| `c4g_inspect_book` | inspect | `obj.c4g_book` „Schlag den Reiseführer auf, Seite 212.“ | talk_ekdahl | `ev_c4_guidebook` | `canteen_table` |
| `c4g_talk_lev` | dialogue `dlg_c4g_lev` | `obj.c4g_lev` „Lev wartet im Sandtrockenhaus.“ | inspect_book | `ev_c4_card_ru_original` (last line) | `lev_sandhouse` |
| `c4g_solve_halves` | puzzle `pz_c4_halves` | `obj.c4g_halves` „Leg die beiden Hälften der Karte 0417 aneinander.“ | talk_lev | — | `sand_table` |
| `c4g_inspect_card` | inspect | `obj.c4g_card` „Sieh dir die ganze Karte unter der Lampe an.“ | solve_halves | `ev_c4_card_whole` | `sand_lamp` |
| `c4g_choose` | choice | `obj.c4g_choice` „Entscheide, was Ekdahl heute Nacht mitnimmt.“ | inspect_card | per choice | `express_door` |

Kolonnenstraße 14, Tuesday 22.10–23.40 — Konrad in the courtyard (≈ 4.5 min):
```
c4h_inspect_gate ─> c4h_talk_hanna ─> c4h_inspect_cards ─> c4h_solve_house ─> c4h_talk_wendt ══> c4h_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4h_inspect_gate` | inspect | `obj.c4h_gate` „Lies den Aushang in der Durchfahrt.“ | — | `ev_c4_house_notice` | `gate_notice` |
| `c4h_talk_hanna` | dialogue `dlg_c4h_hanna` | `obj.c4h_hanna` „Sprich mit Hanna im Hof.“ | inspect_gate | — | `hanna_yard` |
| `c4h_inspect_cards` | inspect | `obj.c4h_cards` „Sieh in die Haushaltskartei am Logenfenster.“ | talk_hanna | `ev_c4_house_cards` | `lodge_window` |
| `c4h_solve_house` | puzzle `pz_c4_house` | `obj.c4h_house` „Finde in Haus 14 einen Weg für Ilse, den keine Karte kennt.“ | inspect_cards | — | `yard_pump` |
| `c4h_talk_wendt` | dialogue `dlg_c4h_wendt` | `obj.c4h_wendt` „Geh zu den Männern in der Durchfahrt.“ | solve_house | — | `wendt_yard` |

### 2.4 The decision (both options always offered; each raises exactly one meter)
| objective | choice id | base text (de) | effect | option variants (choice_text) | reaction (speaker: line) |
|---|---|---|---|---|---|
| `c4g_choose` | `publish_now` | `choice.c4g.publish_now` „Ekdahl alles mitgeben – den Film, Levs Durchschläge, die Liste der Kolonne vier –, damit er um 23.40 Uhr an Tür Ost steht“ | `evidence_chain +1` | v choice.c4d = name_marta: `choice.c4g.publish_now.marta` „Ekdahl alles mitgeben – den Film, Levs Durchschläge, auch die Seite mit Marta Vogels Namen –, damit er um 23.40 Uhr an Tür Ost steht“ | journalist (`dlg.c4p2.react.publish_now`, determined): „Dann steige ich in Kordon-17 aus und stehe um 23.40 Uhr an Tür Ost, mit Blitzlicht. Ihren Namen lasse ich weg. Die anderen nicht.“ · v choice.c3g = hide_for_elena (`dlg.c4p2.react.publish_now.elena`): „Dann steige ich in Kordon-17 aus und stehe um 23.40 Uhr an Tür Ost. Danach frage ich in Veltrava nach einem Mantel, Marke 27.“ |
| `c4g_choose` | `protect_first` | `choice.c4g.protect_first` „Den Film behalten und Ekdahl nur die Nummern geben – erst müssen Lev, Maria und Konrads Leute aus der Schusslinie“ | `people_protected +1` (the new flag) | v choice.c4d = protect_marta: `choice.c4g.protect_first.marta` „Den Film behalten und Ekdahl nur die Nummern geben – Konrad hat Martas Namen geschützt, ich schütze Levs“ | journalist (`dlg.c4p2.react.protect_first`, concerned): „Nummern ohne Namen druckt keine Zeitung, Herr Morozov. Behalten Sie den Film. Wenn Sie rufen, komme ich wieder.“ |

Why each option costs something — and protects someone:
* `publish_now` gives a neutral witness to the 23.40 handover: Ekdahl leaves the westbound express at Kordon-17 (it
  stops there 23.05–23.50 for the gauge change and the border control), stands at the fence of Tür Ost with a flashbulb
  and a notebook; the regimes suspend the handover „aus technischen Gründen“ rather than show people to the press — Anna
  Lindner and Pjotr Iljin are led back, a reprieve, not a rescue (Chapter 5's "return train" is the next one). Stockholm
  prints on Thursday: the joined card on a front page. The price: what Ekdahl carries names its sources — Lev's carbons
  (his invisible name on every copy; Alexei breaks the word he gave in part 1), Maria's testimony, the list of Kolonne
  4, and on the named route the Lindner page with Marta's name. Archipov will know by Wednesday who talked.
* `protect_first` keeps every source safe and the evidence whole for a later, stronger publication (the „Öffentliche
  Akte“ needs `witnesses_exposed = 0`): the film stays in Karsk, Lev's carbons go back into his coat, Maria's name is in
  no Swedish notebook, Konrad's drawing is in no newspaper. The price: no witness at Tür Ost — the door opens at 23.40,
  two figures cross the light into wagon C-17/45, and on Wednesday morning Anna and Pjotr are at the filtration point
  Karsk (where Alexei can reach them in Chapter 5).
Neither option is a good/evil score; each is a different protection. The end card lists the decision; Chapter 5 reads
`choice.c4g_choose`. Meters over all 576 routes: `evidence_chain` reaches at most 5 (note_alone + pocket_plan +
split_by_language + name_marta + publish_now; flag max 6), `people_protected` at most 1 (flag max 6).
Option text variants (`data/chapters/c4p2.json` `choice_text`, first match wins) keep the words the reaction answers
(„alles … 23.40 Uhr an Tür Ost“ / „Film behalten … nur die Nummern“); the bases are heard on the routes the variants do
not cover.

### 2.5 Items (evidence)
| id | name (de) | description (de) | category | scene |
|---|---|---|---|---|
| `ev_c4_special_order` | Auftrag Sonderlauf C-17/45 | Durchschlag am Fenster der Dispatcherbude: ‚Lokdepot Karsk stellt für Sonderlauf C-17/45 am Dienstag, 18.2., eine Lok und ein Personal. Ab Umsetzgleis 19.40 Uhr Ortszeit, an Kordon-17 23.40 Uhr Korridorzeit. Wagen 24 318. Begleitung: Abt. T. Das Personal schweigt.‘ Darunter in Irinas Bleistift: ‚Wer?‘ | document | L_C4P2_KarskA |
| `ev_c4_work_list` | Arbeitsliste Kolonne 4 | Am Pfosten des Kohlenbansens, unter Zellophan: ‚Kolonne 4. Zugang 22.1.1964. Bis zum Abschluss der Prüfung.‘ Elf Namen. Am Rand drei Vermerke in Bleistift: ‚Lena, 4, und Miron, 6 – Kinderheim Nr. 2‘ und ‚Wilhelm S. – Sondersiedlung Nord‘. Elf und drei sind vierzehn. | document | L_C4P2_KarskA |
| `ev_c4_press_notice` | Aushang: Besuch der Presse | An der Hintertür des Lokschuppens, mit dem Stempel der Depotleitung: ‚Dienstag, 18.2., 17.30 Uhr: Besuch eines Vertreters der schwedischen Presse. Vorzuführen: das wiederhergestellte Signal der Strecke (Ing. A. Morozov), die Musterbrigade, die Speisehalle. Kolonne 4 an diesem Tag: Hinterhof, hinter der Plane.‘ | document | L_C4P2_KarskA |
| `ev_c4_departures_east` | Abfahrtstafel Bahnsteig K | ‚D 303 Berlin Ost – Kordon-17 – Karsk, ab 21.10 Uhr, Bahnsteig K.‘ Darunter ein frisch gemaltes Schild: ‚Dienstag: Sonderzug nach Kordon-17 mit Sonderwagen, ab 15.30 Uhr. Bahnsteig K ab 15 Uhr gesperrt.‘ Ein Zug, der um 23.40 Uhr an der Linie sein soll. | document | L_C4P2_BerlinA |
| `ev_c4_courier_seals` | Kurierwagen und grüner Wagen | Hinter der Lok ein Kurierwagen ohne Fenster. An der Tür zwei Bleiplomben, eine deutsche, eine sowjetische, beide mit ‚C-17‘. Auf dem Nachbargleis ein grüner Wagen mit vergitterten Luken. Mit Kreide auf der Tür: ‚Di – Kordon‘. | physical_clue | L_C4P2_BerlinA |
| `ev_c4_konrad_tracing` | Konrads Pause von Blatt 7 | Auf Pauspapier, aus dem Gedächtnis und mit dem Lineal aus der Manteltasche: der Raum von Kordon-17, Tür West, Tür Ost, der Durchgabeschalter, die Wartebank für vierzehn. Auf der Rückseite in Druckbuchstaben: ‚MOROZOV – 0417 – DI 23.40 – TÜR OST‘. Sie liegt mit der deutschen Hälfte der Karte in Ekdahls Reiseführer, Seite 212. | document | L_C4P2_BerlinA |
| `ev_c4_guidebook` | Ekdahls Reiseführer, Seite 212 | Ein schwedischer Reiseführer von 1938, Kapitel ‚Karsk – Bahnhof und Depot‘. Zwischen den Seiten die deutsche Hälfte der Karte 0417, verkehrt herum eingelegt, und eine Pause: der Raum von Kordon-17, Tür West, Tür Ost, die Wartebank für vierzehn. Auf der Rückseite in Druckbuchstaben: ‚MOROZOV – 0417 – DI 23.40 – TÜR OST‘. | physical_clue | L_C4P2_KarskB |
| `ev_c4_card_ru_original` | Karte 0417, russische Hälfte (Original) | Aus dem Kasten ‚C-17/45 – annehmen‘, für eine Stunde ausgeliehen: ‚Kowalenko, Anna Petrowna, 1926, Charkow. Rückkehrerin. Weiter: Filtrationspunkt Karsk.‘ Stempel ‚Annehmen‘. Links die Perforation, darüber ein halber runder Stempel. Um halb acht muss sie wieder im Kasten liegen. | document | L_C4P2_KarskB |
| `ev_c4_card_whole` | Karte 0417, ganz | Die Zähne der Perforation greifen ineinander. Links, deutsch: ‚Lindner, Anna, geb. Kowalenko … Vermerk C-17: Rückführung Ost. Abgabe Kordon-17, Tür Ost.‘ Rechts, russisch: ‚Kowalenko, Anna Petrowna … Annehmen … Weiter: Filtrationspunkt Karsk.‘ Über den Schnitt läuft ein runder Stempel ‚C-17‘, halb in deutscher, halb in russischer Schrift. Er schließt sich. Ekdahl macht zwei Aufnahmen. | document | L_C4P2_KarskB |
| `ev_c4_house_notice` | Aushang in der Durchfahrt | ‚Bekanntmachung der Blockleitung: Alle Haushalte halten sich am Dienstag ab 22 Uhr zur Überprüfung der Haushaltskartei bereit. Kinder sind vorzuzeigen.‘ Darunter mit einer Reißzwecke: ‚Bauabschnitt Süd 9 – Kolonnenstraße 12 bis 18 – Lageplan‘, die Häuser schraffiert. Im Schriftfeld: gez. K. A. | document | L_C4P2_BerlinB |
| `ev_c4_house_cards` | Haushaltskartei Kolonnenstraße 14 | Ein Holzkasten auf dem Logenfenster, eine Karte je Wohnung, in Kuhnerts Schrift. Seitenflügel 3: ‚Adler, Hanna, Lehrerin, 1 Pers.‘ Seitenflügel 2: ‚Pohl, Gertrud, Witwe – meldet zuverlässig‘. Loge: ‚Kuhnert, Erwin und Frieda – Fenster zum Hof‘. Hinterhaus 3: ‚leer, umgesetzt 10/63‘. Durchfahrt: ‚ab 22 Uhr Blockleiter‘. Dachboden: ‚Waschtag Di: offen‘. Zuletzt, ohne Haushaltskarte: ‚Schuhmacherei Pietsch, Souterrain – Gewerbe‘. | document | L_C4P2_BerlinB |
Story inventory never shrinks: `ev_c4_card_de` (part 1) stays Konrad's item although the half now travels; the board's
`looks` mark it („In Ekdahls Reiseführer nach Karsk unterwegs.“ → „Seit Dienstag in Karsk an die russische Hälfte
gelegt.“). Document art (inspect close-ups; owners env-karsk `assets/ui/documents/karsk_c4p2_*`, env-berlin
`assets/ui/documents/berlin_c4p2_*`): legible only the story-critical lines. Special order: a typed carbon with the
depot stamp, Irina's pencil „Wer?“. Work list: a typed list under yellowed cellophane, eleven names **blurred/illegible
except the three pencil notes** (no real persons, no list of victims to read like a monument); the numbers „11 + 3 = 14“
are the point. Press notice: typed, the depot stamp, the line „Kolonne 4 … hinter der Plane“ underlined by someone.
Departure board: enamel letters „D 303 Berlin Ost – Kordon-17 – Karsk 21.10 K“, under it a hand-painted board for
Tuesday. Courier seals: two lead seals side by side — the German one with an eagle only in the `_hist` variant (neutral:
a plain disc „DR“), the Soviet one with a star only in `_hist` (neutral: a wheel) — both stamped „C-17“ (§12.4,
`Symbols.pick()`). Tracing / guidebook: Konrad's tracing on onion-skin paper (the Kordon room of Blatt 7: Tür West, Tür
Ost, the counter, the bench for 14) with block letters on the back; the guidebook a 1938 Swedish travel guide (original
design, no real publisher's name), page 212 „Karsk – Bahnhof och depå“. Card halves: as part 1 (No. 0417, the mirrored
perforation teeth), plus the round half-stamp „C-17“ across the perforation (left half German letters, right half
Cyrillic) that only closes when the halves are laid edge to edge. House notice: typed notice of the „Blockleitung“ (no
party emblem in the neutral variant), the pinned site plan „Bauabschnitt Süd 9 – Kolonnenstraße 12 bis 18 – Lageplan“
with the houses hatched and „gez. K. A.“ in the title block. House cards: a wooden box of index cards, Kuhnert's round
hand, the six notes of the description legible.

### 2.6 Flags, events and design notes
New flag `people_protected` (§1.1); events `c4e_completed` … `c4h_completed` (before `slice_completed`). Meters written:
`evidence_chain` (publish_now), `people_protected` (protect_first). No combined morality score.
**c4d made real (binding for every stream of part 2):**
* named (`choice.c4d_choose = name_marta`): Marta was fetched on Sunday evening — three hours „am Ring“, „Frau Vogel,
  Sie kennen ein Kind namens Ilse“ — and learned there who gave her name (Wendt's method: let the informer's name do the
  work). She lost line 74 and drives line 3 to the Ostbahnhof; she still helps — „Für Sie tue ich nichts mehr, Herr
  Adler. Für Ilse alles.“ Konrad put the signed page of the Lindner file into the guidebook as well (Ekdahl says so in
  Karsk) — on this route `publish_now` would print Marta's name. On Tuesday night Wendt thanks Konrad for „Frau Vogel“
  in the courtyard — a Berlin courtyard carries every word, and Hanna's window above is lit (the closing film's inner
  line: „Hanna weiß jetzt, wessen Namen ich genannt habe.“). Presentation: Marta's duty roster on the buffet counter
  reads „Linie 3“ (decal, art gate `choice.c4d_choose = name_marta`).
* protected (`protect_marta`): the Staatspolizei asked at Marta's depot „nach einem Herrn vom Bauamt, der in der
  Nebenstelle keinen Namen wusste“ — Konrad is under suspicion; Marta's trust grew („Das vergesse ich Ihnen nicht“, and
  through Hanna: „der Einzige vom Amt, der keine Namen sagt“). Wendt on Tuesday: „Wer keinen nennt, hat meistens
  einen.“ Presentation: Marta came straight from her shift, her roster on the counter reads „Linie 74“ (decal, art gate
  `choice.c4d_choose = protect_marta`); the man at the kiosk watches Konrad, not Ekdahl.
* Both routes: the households with the red C-17 tab are collected on Tuesday evening, „Und die Kinder dazu“
  („Familienzusammenführung“ — the regime's word, said by Marta with quotation marks) — Ilse must be out of every
  register by 22.00.
Hooks for Chapter 5 (PLANNED, NOT IMPLEMENTED): C4P2_TUESDAY (publish_now: the handover suspended, Anna and Pjotr back
in German custody / protect_first: both at the filtration point Karsk, Wednesday), C4P2_LEV (publish_now: Lev's carbons
in Stockholm — the first broken promise of Alexei, `arkhipov_alerted`), C4P2_HOUSE_14 (Konrad's office hatched
Kolonnenstraße 12–18, Hanna's house — the Chapter-5 decision about "his sister's neighbours' file" starts from Kuhnert's
box and the households of the house puzzle), C4P2_ILSE (in Pietsch's workshop; Marta has to get her out of Berlin),
C4P2_EKDAHL (a neutral journalist who "comes back when you call" — Chapter 5's phone line), C4P2_MARIA (Kolonne 4, the
Kinderheim Nr. 2, Wilhelm in the north), C4P2_PAUL (Paul Lindner in Stettin does not know where his wife is).

### 2.7 Puzzles — key/pad/mouse contracts for the UI stream
**`pz_c4_house` „Haus 14“ — the NEW puzzle UI `HousePuzzle` (Story type `symbol_order`; both engines know only
`symbol_order` / `overlay_alignment`, so the novelty is the UI, as with the TracePuzzle).** Konrad, at the courtyard
pump, looking up at the house; he knows how houses are built — he draws them before they are emptied.
* Board: a cutaway of Kolonnenstraße 14 seen from the courtyard, three wings as columns, left → right **Vorderhaus V**,
  **Seitenflügel S**, **Hinterhaus H**, six rows bottom → top **Keller K**, **Erdgeschoss E** (stair hall / passage),
  **1., 2., 3. Stock**, **Dachboden D**, plus the cobbler's workshop **W** in the souterrain, drawn right of the back
  cellar. 19 rooms (ids below). Every room shows its nameplate and a window vignette (who is awake at 22.40: a radio, a
  baby, a card game, a dark window, a curtain that moves) — the house is full of people, each placed with intent; this
  is where the Chapter-5 neighbours are introduced.
* Passages (exactly these, drawn as stairs and doors): up/down inside a wing between neighbouring floors
  (`vk–ve–v1–v2–v3–vd`, `sk–se–s1–s2–s3–sd`, `hk–he–h1–h2–h3–hd`); across the wings only along the attic (`vd–sd–hd`,
  the drying lofts) and the cellar corridor (`vk–sk–hk`); the workshop only by its cellar stair (`hk–ws`). The courtyard
  is NOT a passage (the lodge sees it).
* Room ids, names and card notes (`ui.c4p2.house.room.<id>` / `ui.c4p2.house.note.<id>`, de_c4p2_ui.json): `vd`
  Dachboden Vorderhaus („Waschtag Donnerstag – heute nur Gerümpel.“) · `v3` Lenz (student, radio till midnight) · `v2`
  Grabowski (widow, coal card blocked) · `v1` Schulz (baby) · `ve` Durchfahrt („ab 22 Uhr Blockleiter“) · `vk` Keller
  Vorderhaus (only via the passage) · `sd` Trockenboden Seitenflügel („Waschtag Dienstag: offen“) · `s3` **Hanna Adler
  (start)** · `s2` Pohl („meldet zuverlässig“) · `s1` Mertens (tram conductor) · `se` Loge Kuhnert („Fenster zum Hof“) ·
  `sk` Keller Seitenflügel · `hd` Trockenboden Hinterhaus (open on Tuesdays) · `h3` empty, sealed („umgesetzt 10/63“) ·
  `h2` Brettschneider (night shift at the gasworks) · `h1` Kühn (pensioners) · `he` Flur Hinterhaus · `hk` Keller
  Hinterhaus · `ws` **Schuhmacherei Pietsch (goal; „Gewerbe – keine Haushaltskarte“)**.
* Unsafe rooms (a route through one of them fails): `s2` (Frau Pohl's spy hole), `se` (Frau Kuhnert at the lodge
  window), `ve` (Kuhnert in the gate passage, the sweep comes through it). The clue items name all three
  (`ev_c4_house_cards`, `ev_c4_house_notice`), and the K overlay shows them.
* **Solution `["s3", "sd", "hd", "h3", "h2", "h1", "he", "hk", "ws"]`** — up to the side wing's drying loft, across to
  the back wing's, down the back stairs past the sealed flat, the night worker and the pensioners, into the cellar and
  through Pietsch's cellar door. It is the ONLY simple path from `s3` to `ws` that avoids the unsafe rooms
  (`tests/test_c4p2_routes.gd` proves it on this graph; decoys: down the side stairs past Pohl; across the front attic
  and down the front stairs into the gate passage). `display_symbols` `["he", "s3", "hk", "h2", "ws", "sd", "h1", "hd",
  "h3"]` (the validator wants a permutation of the answer; the UI does not show a tray). `clue_item_ids`
  `["ev_c4_house_notice", "ev_c4_house_cards"]`; hint after 2 failures; unlimited retries; no penalty.
* Layout file `assets/ui/puzzle/c4p2_house.json` (puzzle stream): `{"rooms": {id: {wing, floor, rect}}, "edges": [[a, b]
  …], "unsafe": [...], "start": "s3", "goal": "ws"}` — the test compares rooms, unsafe, start and goal with this
  contract once the file exists. The UI's „Probegang“ walks Ilse's marker (with Konrad behind her) along the route and
  stops at the first unsafe room with its reason (`ui.c4p2.house.stop.s2|se|ve`), or at the end of a route that ends in
  a household (`stop.flat` „In „{room}“ steht eine Haushaltskarte …“) or anywhere but the workshop (`stop.short`) —
  presentation only; the verdict is `Story.solve_puzzle`.
* Scene `res://scenes/ui/HousePuzzle.tscn`, script `scripts/ui/house_puzzle.gd` (extends `ui_modal.gd`, registered in
  c4p2.json `puzzles`; API like the other puzzles: `open(obj_id)`, `signal solved(obj_id)`, `is_open`). **Key contract
  (the input driver relies on it):** property `is_open`; the route starts as `["s3"]` with the head on `s3`;
  **arrows/WASD** move the head into the neighbouring room in that direction when a passage exists (UP/DOWN = stairs and
  the attic/cellar doors, LEFT/RIGHT = along the attic and the cellar corridor; `hk` → `ws` is RIGHT — the workshop is
  drawn right of the back cellar); moving onto a room already on the route cuts the route back to it (onto the previous
  room = undo); a move without a passage is refused (`ui.c4p2.house.no_way`, a soft knock); **Backspace** undoes the
  last step (also bound to cancel: consume it before UIRoot closes the modal); **R** resets to `["s3"]`; **K** toggles
  the card notes (Kuhnert's box — presentation only); **L** toggles the 22.40 lights (presentation only); **Enter**
  („Probegang“) submits the route ids through `Story.solve_puzzle` at once — the walk of the markers (≤ 1 s;
  reduced_motion: none) is presentation only and never swallows input: a key during the walk ends it and is then
  applied; **Esc** closes. The first two failures keep the route; the hint appears after `hint_after_attempts`;
  auto-close ≤ 7 s after success (Enter/Esc close at once). **Pad** (as the TracePuzzle): D-pad / left stick move the
  head, A or Y Probegang, B takes back the last step, X Kartei, LB Licht, RB Neu, Back/Select closes. **Mouse:** click a
  neighbouring room to extend the route, click a room of the route to cut it back there; buttons Probegang · Zurück ·
  Neu · Kartei · Licht · Schließen; hover a room = its nameplate, card note and window in the side panel. Text scale and
  high contrast like the TracePuzzle (route line ≥ 3 px at ×3; unsafe rooms shape-coded — a spy-hole eye, a lamp, a hat
  — never colour alone).
* Success (de, `ui.c4p2.house.success`): „Über den Trockenboden, die Hintertreppe hinab an der leeren Drei vorbei, durch
  den Keller in Pietschs Werkstatt: Dort steht keine Haushaltskarte. Dort sucht heute keiner ein Kind.“

**`pz_c4_halves` „Die Hälften“ — overlay UI `JoinPuzzle` (Story type `overlay_alignment`, Konrad's M1 mechanic in
Alexei's hands, on new data).** Alexei, at the sand house table under the lamp.
* Base sheet: the Russian (right) half of card 0417 on the table, its left edge with five perforation notches and the
  right half of a round stamp „C-17“ in Cyrillic letters. Overlay: the German (left) half from the guidebook, laid in
  upside down — five teeth on its right edge, the left half of the stamp in German letters, the ruled lines of the form.
* Grid as BlueprintPuzzle/RoutePuzzle (cells, `snap_tolerance` 0); layout `assets/ui/documents/karsk_c4p2_halves.json`
  (cell size, files, marks: `tooth` triangles vs `notch` cut-outs, `stamp_half` semicircles, `line_end` ticks; start
  pose).
* **Start pose `{rotation_steps: 0, offset_x: 0, offset_y: 0}` (wrong: upside down and off); solution
  `{"rotation_steps": 2, "offset_x": 4, "offset_y": 1}`** (half a turn, four cells right, one down); `clue_item_ids`
  `["ev_c4_guidebook", "ev_c4_card_ru_original"]`; hint after 2 failures; unlimited retries. (The autoplay's wrong pose
  `{1, 0, 0}` is wrong too.)
* Scene `res://scenes/ui/JoinPuzzle.tscn` — the puzzle stream may reuse `scripts/ui/route_puzzle.gd` (layout chosen per
  objective or exported on the scene) or give it its own `scripts/ui/join_puzzle.gd`; the driver finds the OPEN UI child
  with either script. **Key contract (= RoutePuzzle / BlueprintPuzzle):** `is_open`; arrows/WASD move one cell
  (**RIGHT** = offset_x +1, **DOWN** = offset_y +1), **R** rotates +90° (rotation_steps +1 mod 4), **Shift+R** −90°,
  **Backspace** takes back the last move (consumed before UIRoot's cancel), **Enter** („Anlegen“) submits
  `{rotation_steps, offset_x, offset_y}` (ints) through `Story.solve_puzzle` unless the GUI focus is on another action
  button (then Enter presses that button; the UI opens without focus on them), **Esc** closes. **Pad** (= RoutePuzzle):
  D-pad moves, RB/LB turn, A checks, X start pose, Y takes back the last move, Back/Select closes; B is left to UIRoot
  (cancel → close). **Mouse:** drag the half (snaps to cells), buttons Drehen · Zurücksetzen · Anlegen · Schließen.
  Wrong feedback `ui.c4p2.halves.wrong_turned` while the rotation is wrong (derived from the marks' geometry, never from
  the answer), else `ui.c4p2.halves.wrong`. Marks are shape-coded.
* Success (de, `ui.c4p2.halves.success`): „Die Zähne greifen ineinander, der Stempel schließt sich zum Kreis. Links das
  Reich, rechts die Gegenstelle: eine Karte, zwei Staaten, eine Ordnung.“
* Texts of both puzzles: `data/locale/de_c4p2_ui.json` (`ui.c4p2.halves.*`, `ui.c4p2.house.*` — title, subtitle,
  instruction, legend, wrong, hint, success, buttons, rooms, notes, stops); further UI strings of the puzzle stream go
  to its own `data/locale/de_c4p2_puzzles.json`.

### 2.8 Dialogues (linear; node ids globally unique; ≤ 140 characters per line; speaker ids in parentheses)
Variant notation as C4 §2.8: `· v <condition>: „…“`, first match wins; `choice.c4d = name_marta` means
`{"choice.c4d_choose": "name_marta"}`. Base lines marked *(fallback-only)* are heard only on a level start without a
save (A1 / C4d always set one of the covering conditions). Expressions (`line_expr`) in brackets. Base texts live in
`data/v3/locale_de.json` (`dlg.c4p2.<x>_<n>`), variants and reactions in `data/locale/de_c4p2_dialogue.json`.

`dlg_c4e_irina` (objective `c4e_talk_irina`, entry `c4e_iri_01`) — 10 lines:
1. `c4e_iri_01` (irina) [neutral] „Du hast den Auftrag gelesen. Lok und Personal für einen Wagen, der in keinem Buch fährt.“ *(fallback-only)* · v irina_trust ≥ 1: „Du hast den Auftrag gelesen. Im Januar hast du mir drei Wagen gezeigt, Aljoscha – das hier ist der vierte.“ · v alexei_secrecy ≥ 1: „Du hast den Auftrag gelesen. Im Januar wusstest du schon etwas und hast geschwiegen. Jetzt weiß ich es auch, Morozov.“
2. `c4e_iri_02` (alexei) [determined] „Wen schickst du?“
3. `c4e_iri_03` (irina) [concerned] „Ich habe sieben Lokführer. Jeder hat Kinder oder eine Mutter oder eine Akte. Ich schicke keinen.“
4. `c4e_iri_04` (alexei) [neutral] „Und wenn du keinen schickst?“
5. `c4e_iri_05` (irina) [concerned] „Dann schickt die Abteilung T einen. Und unter meinen Namen schreibt sie ‚Personal verweigert‘.“
6. `c4e_iri_06` (alexei) [concerned] „Die Leute am Kohlenbansen. Seit wann schaufeln die hier?“
7. `c4e_iri_07` (irina) [neutral] „Seit dem zweiundzwanzigsten Januar. Kolonne vier. Sie schaufeln die Kohle für die Züge, die sie hergebracht haben.“
8. `c4e_iri_08` (alexei) [surprised] „Die aus dem Wagen.“
9. `c4e_iri_09` (irina) [concerned] „Frag nicht mich. Frag die Frau mit dem grünen Kopftuch. Sie redet, wenn der Posten Tee holt.“
10. `c4e_iri_10` (irina, end) [neutral] „Und morgen um halb sechs kommt ein Schwede von der Zeitung. Du sollst ihm dein Signal zeigen. Rasier dich.“

`dlg_c4e_maria` (objective `c4e_talk_maria`, entry `c4e_mar_01`) — 13 lines:
1. `c4e_mar_01` (maria) [neutral] „Sie sind kein Posten. Posten tragen keine Werkzeugtasche, und sie sehen einem nicht in die Augen.“
2. `c4e_mar_02` (alexei) [neutral] „Ingenieur. Ich zähle Wagen, die in keinem Buch stehen. Einer hieß 24 318.“
3. `c4e_mar_03` (maria) [surprised] „Dann haben Sie unsere Bänke gesehen. Und das Loch für das Ofenrohr.“
4. `c4e_mar_04` (alexei) [concerned] „‚Wir sind vierzehn.‘ Es stand in der Wand, mit einem Nagel geritzt.“
5. `c4e_mar_05` (maria) [concerned] „Das war ich. Maria Gorelowa. Die Kinder saßen am Ofen, Lena und Miron. Wilhelm hat aufgepasst, dass sie nicht ans Blech kommen.“
6. `c4e_mar_06` (alexei) [neutral] „Wo sind sie jetzt?“
7. `c4e_mar_07` (maria) [concerned] „Die Kinder im Kinderheim Nummer zwei. Wilhelm in einer Sondersiedlung im Norden. Er ist Deutscher vom Schwarzen Meer – das genügt.“
8. `c4e_mar_08` (alexei) [neutral] „Und Sie?“
9. `c4e_mar_09` (maria) [concerned] „Ich schaufle, bis die Prüfung fertig ist. Jeden Tag dieselbe Frage: Warum sind Sie mitgegangen? Warum leben Sie noch?“
10. `c4e_mar_10` (alexei) [concerned] „Wie haben sie Sie in Veltrava gefunden?“
11. `c4e_mar_11` (maria) [determined] „Nicht mich. Meine Karte. Sie war vor mir hier, an der Tür stand einer und hat verglichen. Zuerst kommt die Karte, dann der Mensch.“
12. `c4e_mar_12` (alexei) [determined] „Am Dienstag kommt der nächste Wagen. Eine Frau aus Berlin, Anna Kowalenko. Und ein Freund von mir.“
13. `c4e_mar_13` (maria, end) [determined] „Dann sagen Sie es jemandem, der es aufschreiben darf. Uns glaubt hier keiner. Uns fragt man nur.“

`dlg_c4f_marta` (objective `c4f_talk_marta`, entry `c4f_mar_01`) — 11 lines:
1. `c4f_mar_01` (marta) [neutral] „Da sind Sie ja, Herr Adler. Pünktlich wie ein Fahrplan.“ *(fallback-only)* · v choice.c4d = name_marta: „Da sind Sie ja, Herr Adler. Ich wollte erst nicht kommen. Dann habe ich an Ilse gedacht.“ · v choice.c4d = protect_marta: „Da sind Sie ja. Ich bin nach der Schicht gleich her. Die 74 hatte heute Glück, keiner hat sie angehalten.“
2. `c4f_mar_02` (konrad) [concerned] „Was ist passiert?“
3. `c4f_mar_03` (marta) [concerned] „Gestern Abend war einer vom Amt im Depot und hat Fragen gestellt.“ *(fallback-only)* · v choice.c4d = name_marta: „Gestern Abend haben sie mich geholt. Drei Stunden am Ring. ‚Frau Vogel, Sie kennen ein Kind namens Ilse.‘ Ich kenne viele Kinder.“ · v choice.c4d = protect_marta: „Gestern war einer von der Staatspolizei im Depot. Er fragte nach einem Herrn vom Bauamt, der in der Nebenstelle keinen Namen wusste.“
4. `c4f_mar_04` (konrad) [concerned] „Und?“ *(fallback-only)* · v choice.c4d = name_marta: „Marta … am Schalter habe ich Ihren Namen genannt. Für die Akte Lindner.“ · v choice.c4d = protect_marta: „Nach mir.“
5. `c4f_mar_05` (marta) [determined] „Heute früh hatte ich eine andere Linie.“ *(fallback-only)* · v choice.c4d = name_marta: „Ich weiß. Der Herr am Ring hat es mir gesagt – wie freundlich Sie waren. Seit heute früh fahre ich nicht mehr die 74, sondern die 3.“ · v choice.c4d = protect_marta: „Nach Ihnen, ja. Nach mir nicht. Sie haben mich nicht genannt. Das vergesse ich Ihnen nicht.“
6. `c4f_mar_06` (konrad) [concerned] „Was wissen Sie über morgen?“
7. `c4f_mar_07` (marta) [concerned] „Morgen Abend holen sie die Haushalte mit dem roten Fähnchen. Und die Kinder dazu, sagt eine Kollegin, deren Mann am Ring fährt.“
8. `c4f_mar_08` (konrad) [surprised] „Die Kinder? Mit dem Zug am Dienstag?“
9. `c4f_mar_09` (marta) [concerned] „Zu den Müttern, heißt es. ‚Familienzusammenführung.‘ Ilse kann morgen nicht bei mir schlafen. Bei mir suchen sie zuerst.“ · v choice.c4d = protect_marta: „Zu den Müttern, heißt es. ‚Familienzusammenführung.‘ Bei mir sucht keiner – noch nicht. Aber in der Schule, bei Ihrer Schwester.“
10. `c4f_mar_10` (konrad) [determined] „Hanna. Kolonnenstraße vierzehn. Ein Haus voller Leute, die sie kennen – und einer, der Karten führt.“
11. `c4f_mar_11` (marta, end) [determined] „Dann bringe ich Ilse morgen Abend zu Ihrer Schwester. Und Sie, Herr Zeichner, finden heraus, wohin dieser Zug fährt.“ · v choice.c4d = name_marta: „Dann bringe ich Ilse morgen Abend zu Ihrer Schwester. Für Sie tue ich nichts mehr, Herr Adler. Für Ilse alles.“

`dlg_c4f_ekdahl` (objective `c4f_talk_ekdahl`, entry `c4f_ekd_01`) — 11 lines:
1. `c4f_ekd_01` (journalist) [neutral] „Herr Adler. Sie haben angerufen und nichts gesagt. Am Telefon ist das die höflichste Art zu reden.“
2. `c4f_ekd_02` (konrad) [neutral] „Sie fahren nach Karsk.“
3. `c4f_ekd_03` (journalist) [neutral] „Pressereise, ‚Der erste Winter des Abkommens‘. Man zeigt mir ein Depot, eine Kantine und einen Ingenieur, der ein Signal repariert hat.“
4. `c4f_ekd_04` (konrad) [surprised] „Wie heißt der Ingenieur?“
5. `c4f_ekd_05` (journalist) [neutral] „Morozov. Steht im Programm, mit Ausrufezeichen. Warum?“
6. `c4f_ekd_06` (konrad) [determined] „Sie sagten in Veltrava: Wenn ich einmal etwas zeichne, das nicht stimmt. Ich habe es gezeichnet. Und er hat die andere Hälfte.“ · v choice.c3d = admit_plan: „Ich habe einen Raum gezeichnet, in dem vierzehn Menschen auf einer Bank warten. Ich habe es ihm gesagt. Er hat die andere Hälfte.“
7. `c4f_ekd_07` (journalist) [concerned] „In Kordon-17 wird mein Gepäck durchsucht. Und der Herr am Zeitungsstand liest seit zwanzig Minuten dieselbe Seite.“
8. `c4f_ekd_08` (konrad) [neutral] „Ihren Reiseführer durchsucht keiner. Den liest jeder Reisende laut vor.“
9. `c4f_ekd_09` (journalist) [neutral] „Seite zweihundertzwölf, ‚Karsk – Bahnhof und Depot‘. Legen Sie es dorthin. Ich lese erst nach der Grenze.“
10. `c4f_ekd_10` (konrad) [concerned] „Sie sagten auch: Eine Zeitung hält keinen Zug an.“ · v choice.c3b = report_delegation: „In Veltrava habe ich einen Vorfall bei Kessler gemeldet. Morozov weiß das. Ob er Ihr Buch überhaupt aufschlägt?“
11. `c4f_ekd_11` (journalist, end) [determined] „Nein. Aber sie schreibt auf, dass er gefahren ist. Und manchmal steht einer daneben und zählt mit.“ · v choice.c3b = report_delegation: „Dann schreiben Sie etwas hinein, das kein Kessler versteht. Seite zweihundertzwölf. Der Zug fährt um zehn nach neun.“

`dlg_c4g_ekdahl` (objective `c4g_talk_ekdahl`, entry `c4g_ekd_01`) — 10 lines:
1. `c4g_ekd_01` (journalist) [neutral] „Das ist also das Signal, das im Januar wieder grün wurde. Ihre Pressestelle ist sehr stolz auf Sie, Herr Ingenieur.“
2. `c4g_ekd_02` (alexei) [neutral] „Ein Signal ist grün, wenn das Gleis frei ist. Mehr sagt es nicht.“ · v alexei_secrecy ≥ 1: „Ein Signal sagt, ob das Gleis frei ist. Wer darauf fährt, sagt es nicht.“
3. `c4g_ekd_03` (journalist) [neutral] „Mein Begleiter wünscht, dass ich ‚Wiederaufbau‘ schreibe. Ich schreibe es. – Haben Sie einen Reiseführer von Karsk?“
4. `c4g_ekd_04` (alexei) [surprised] „Nein. Wozu, ich wohne hier.“
5. `c4g_ekd_05` (journalist) [neutral] „Dann leihe ich Ihnen meinen. Seite zweihundertzwölf ist besonders gründlich. Ein Zeichner in Berlin hat sie mir empfohlen.“
6. `c4g_ekd_06` (alexei) [concerned] „Ein Zeichner.“ · v choice.c3b = report_delegation: „Adler. Der mich in Veltrava bei Kessler gemeldet hat.“ · v alexei_konrad_trust ≥ 2: „Adler.“
7. `c4g_ekd_07` (journalist) [neutral] „Er sagt, Sie sammeln Nummern. Er sammelt Räume. Ich sammle Leute, die danebenstehen.“ · v choice.c4d = name_marta: „Er sagt, Sie sammeln Nummern. Und er hat eine Seite aus einer Akte beigelegt – mit einem Namen, den er nicht hätte nennen dürfen.“
8. `c4g_ekd_08` (alexei) [determined] „Hinter der Plane dort schaufelt Kolonne vier. Die schreibt keiner auf.“
9. `c4g_ekd_09` (journalist) [concerned] „Ich habe die Plane gesehen. Als sie wackelte, hat mir mein Begleiter die Kantine gezeigt.“
10. `c4g_ekd_10` (alexei, end) [determined] „Bleiben Sie bis zum Abendzug. Ich bringe Ihnen das Buch zurück, bevor er fährt.“

`dlg_c4g_lev` (objective `c4g_talk_lev`, entry `c4g_lev_01`; grants `ev_c4_card_ru_original` at the end) — 11 lines:
1. `c4g_lev_01` (lev) [concerned] „Eine Stunde, Morozov. Um halb acht holt der Begleiter den Kasten. Dann liegt die Karte wieder darin – oder ich woanders.“
2. `c4g_lev_02` (alexei) [neutral] „Sie haben sie mitgebracht.“
3. `c4g_lev_03` (lev) [neutral] „Die rechte Hälfte, ‚annehmen‘. Und Sie haben die linke? Aus Berlin?“
4. `c4g_lev_04` (alexei) [determined] „In einem schwedischen Reiseführer, Seite zweihundertzwölf. Ein Deutscher hat sie hineingelegt.“ · v choice.c3g = swap_halves: „In einem schwedischen Reiseführer. Derselbe Deutsche, der Pjotrs Namen durch Berlin trägt, hat sie hineingelegt.“
5. `c4g_lev_05` (lev) [surprised] „Ein Deutscher, ein Schwede und ein Russe an einem Tisch. Früher nannte man so etwas eine Kommission.“
6. `c4g_lev_06` (alexei) [neutral] „Ihre Durchschläge, Lev. Archipovs Hand. Der Schwede fährt heute Abend nach Westen.“
7. `c4g_lev_07` (lev) [concerned] „Mit ihnen ist es eine Akte. Ohne sie sind es zwei halbe Karten und ein Reiseführer.“
8. `c4g_lev_08` (alexei) [concerned] „Ich habe Ihnen mein Wort gegeben. Ihr Name in keinem Papier.“
9. `c4g_lev_09` (lev) [concerned] „Mein Name steht auf jedem Durchschlag, den ich aufgehoben habe. Unsichtbar. Wer sie druckt, macht ihn lesbar.“
10. `c4g_lev_10` (lev) [determined] „Nehmen Sie sie, wenn Sie müssen. Ich werde nicht fragen, was Sie damit getan haben. Ich werde es erfahren.“
11. `c4g_lev_11` (alexei, end) [determined] „Erst die Karte. Dann sehen wir, was sie wiegt.“

`dlg_c4h_hanna` (objective `c4h_talk_hanna`, entry `c4h_han_01`) — 12 lines:
1. `c4h_han_01` (hanna) [concerned] „Du kommst spät, Konrad. Marta hat sie um neun gebracht, mit einer Tüte Äpfel.“ *(fallback-only)* · v choice.c4d = name_marta: „Du kommst spät, Konrad. Marta hat sie um neun gebracht, mit einer Tüte Äpfel. Für dich hatte sie kein Wort.“ · v choice.c4d = protect_marta: „Du kommst spät, Konrad. Marta hat sie um neun gebracht. Sie lässt dich grüßen – du seist der Einzige vom Amt, der keine Namen sagt.“
2. `c4h_han_02` (konrad) [neutral] „Wo ist sie?“
3. `c4h_han_03` (hanna) [neutral] „Oben, am Küchentisch. Sie malt Häuser mit hellen Fenstern. Das macht man so, sagt sie, wenn alle zu Hause sind.“
4. `c4h_han_04` (konrad) [concerned] „Du hast den Aushang gelesen.“
5. `c4h_han_05` (hanna) [determined] „Ab zweiundzwanzig Uhr Überprüfung, Kinder sind vorzuzeigen. Und darunter dein Plan. Zwölf bis achtzehn, schraffiert. Wir.“
6. `c4h_han_06` (konrad) [concerned] „Hanna, das ist ein Lageplan. Bauabschnitte werden erfasst, lange bevor –“ · v choice.c3d = admit_plan: „Ja. Ich habe ihn gezeichnet. Wie den Raum mit der Bank für vierzehn. Ich sage es dir, bevor es ein anderer tut.“
7. `c4h_han_07` (hanna) [determined] „Später, Konrad. In meiner Wohnung steht kein Kind auf der Karte. Finden sie Ilse dort, steht morgen eins drauf – und mein Name dabei.“
8. `c4h_han_08` (konrad) [neutral] „Kuhnert führt die Kartei.“
9. `c4h_han_09` (hanna) [neutral] „Der Kasten steht auf dem Logenfenster. Er selbst wartet in der Durchfahrt auf die Herren, seine Frau hört Radio.“
10. `c4h_han_10` (konrad) [determined] „Dann lese ich, was er weiß. Und suche, was er nicht weiß.“
11. `c4h_han_11` (hanna) [concerned] „Du kennst Häuser. Du zeichnest sie, bevor man sie leer macht. Finde in diesem einen Platz, den keiner gezeichnet hat.“
12. `c4h_han_12` (konrad, end) [determined] „Zieh ihr den Mantel an. Und lass dein Licht brennen – damit oben alle zu Hause sind.“

`dlg_c4h_wendt` (objective `c4h_talk_wendt`, entry `c4h_wen_01`) — 12 lines:
1. `c4h_wen_01` (wendt) [neutral] „Herr Adler, Generalbauamt. Wir sind uns noch nicht begegnet, aber ich kenne Ihre Handschrift.“ *(fallback-only)* · v choice.c4d = name_marta: „Herr Adler. Am Sonntag haben Sie uns eine Auskunftsperson genannt, Frau Vogel. Das war sehr hilfreich.“ · v choice.c4d = protect_marta: „Herr Adler. Am Sonntag haben Sie in der Nebenstelle keinen Namen genannt. Wer keinen nennt, hat meistens einen.“
2. `c4h_wen_02` (konrad) [neutral] „Ich besuche meine Schwester.“
3. `c4h_wen_03` (wendt) [neutral] „Um halb zwölf, in einem Haus, das Sie selbst schraffiert haben. Sie sind ein gründlicher Mensch.“ · v office_suspicion ≥ 1: „Um halb zwölf. Ihr Amt hat schon im Januar nach Ihnen gefragt, Herr Adler. Sie sind ein gründlicher Mensch.“
4. `c4h_wen_04` (konrad) [neutral] „Die Planung sieht Bestandsaufnahmen vor.“ · v choice.c3d = admit_plan: „Ich habe es schraffiert. Ich wollte sehen, wer darin wohnt, bevor ich es noch einmal tue.“
5. `c4h_wen_05` (wendt) [neutral] „Wohnt hier ein Kind namens Ilse Lindner? Acht Jahre, ein Ranzen, den es nicht aus der Hand gibt?“
6. `c4h_wen_06` (konrad) [determined] „In der Kartei steht keins. Fragen Sie Herrn Kuhnert.“
7. `c4h_wen_07` (blockwart) [concerned] „Haus vierzehn, kein Kind gemeldet, Herr Kommissar. Seitenflügel, Hinterhaus, alles abgehakt. Ordnung.“
8. `c4h_wen_08` (wendt) [neutral] „Ordnung. Dann sind wir die Treppen umsonst gestiegen. Das kommt vor.“ · v choice.c3b = report_delegation: „Ordnung. In Veltrava haben Sie Herrn Kessler einen Vorfall gemeldet. Ich hoffe, Sie bleiben so hilfsbereit, Herr Adler.“
9. `c4h_wen_09` (konrad) [neutral] „Es ist spät, Herr Kommissar.“
10. `c4h_wen_10` (wendt) [neutral] „Dreiundzwanzig Uhr vierzig. Um diese Zeit fährt irgendwo immer ein Zug.“
11. `c4h_wen_11` (wendt) [neutral] „Wir sehen uns, Herr Adler. Dienstags sind wir immer unterwegs.“
12. `c4h_wen_12` (konrad, end) [determined] „Gute Nacht, Herr Kommissar.“

Earlier decisions felt (every route hears its own): a1 (Irina's greeting, Alexei at the signal), m1 (Wendt: „Ihr Amt hat
schon im Januar nach Ihnen gefragt“), c3b (report_delegation: Konrad doubts Alexei will open the book, Alexei names it,
Wendt uses it — else alexei_konrad_trust ≥ 2: Alexei knows it is Adler), c3d (admit_plan: Konrad has learned to say "I
drew it" — to Ekdahl, to Hanna, to Wendt; pocket_plan: he still evades and Hanna cuts him off), c3g (swap_halves: Lev
hears that the same German carries Pjotr's name; hide_for_elena: Ekdahl will ask for coat 27 in Veltrava), c4d (Marta,
Hanna, Ekdahl, Wendt and the option texts of the decision). Voice notes: Irina — protective of her crew, blunt, warm
(„Aljoscha“, „Rasier dich“); Maria — quiet, exact, her pain in precision, never pleading, never a symbol; Marta —
Berlin-direct, hurt or grateful by route, still practical; Ekdahl — dry, courteous, careful, a journalist's ethics („Ich
sammle Leute, die danebenstehen“), never a saviour; Lev — as part 1, now with the price on the table; Hanna — direct,
braver than her brother, angry and loving; Wendt — soft, polite, procedural, never a villain's speech and never a raised
voice — menace by memory („Dienstags sind wir immer unterwegs“); Kuhnert — Berlin, nervous, officious, „Ordnung“ is his
word for fear (he says nothing false: no child is registered). Asymmetry kept explicit (C4 §2.8): Maria's filtration —
the Soviet presumption of guilt for having survived, children taken into a home, a Soviet German exiled for his
ethnicity — and the Reich's Blockleiter card file, the „Familienzusammenführung“ that sends children after their
mothers, Wendt's procedure: two different apparatuses, shown in their own terms, never equated.

### 2.9 Cinematics (data/v3/cinematics.json; `LOCKED_CINEMATICS` extended — validator list only)
| id | trigger | skip | length | scene (cine stream) |
|---|---|---|---|---|
| `LS_C4P2_Depot` | event `c4d_completed` (queued after `LS_C4_Voices`) | visual_only | ≈ 13 s | `res://scenes/cinematics/ch4p2_depot/Ch4p2Depot.tscn` |
| `LS_C4P2_Steam` | event `c4e_completed` | visual_only | ≈ 12.5 s | `res://scenes/cinematics/ch4p2_steam/Ch4p2Steam.tscn` |
| `LS_C4P2_Book` | event `c4f_completed` | visual_only | ≈ 12 s | `res://scenes/cinematics/ch4p2_book/Ch4p2Book.tscn` |
| `LS_C4P2_Express` | event `c4g_completed` | visual_only | ≈ 13 s | `res://scenes/cinematics/ch4p2_express/Ch4p2Express.tscn` |
| `LS_C4P2_Clock` | event `c4h_completed` | visual_only | ≈ 24 s | `res://scenes/cinematics/ch4p2_clock/Ch4p2Clock.tscn` |

**Shot sheets** — `picture` and `camera` are the data (`shot`, `camera`) verbatim; `sound` and `text` bind the cine and
audio streams. A caption is a place/time card, an inner line the protagonist's thought (as in the C4 films); texts in
`data/locale/de_c4p2_cinematics.json`, route variants read `ctx.choices` with defaults. Film titles for the memory page
„Filmsequenzen“ (`ui.memories.film.LS_C4P2_*` / `film_sub`) belong to the cine stream (`data/locale/de_c4p2_cine.json`,
like round 9).

`LS_C4P2_Depot` — Karsk, Monday dawn. Music: `mus_c4p2_karsk` enters on p2.
| shot | s | camera | picture | sound | text |
|---|---|---|---|---|---|
| p1 | 5 | establishing | Karsk locomotive depot before dawn: floodlights over the coal stage, the work gang of returnees shovelling in a line, a young guard at a barrel fire | `amb_karsk_depot` fades up: shovels biting into coal, a safety valve lifting, the barrel fire | caption `cin.c4p2.depot.place` „Karsk, Montag, 17. Februar 1964, 6.10 Uhr.“ |
| p2 | 4 | side_on | Alexei with his toolbox under the roundhouse arch, breath in the cold; the banner ВОССТАНОВИМ ВМЕСТЕ patched with sacking | Alexei's boots on frozen cinders; the bayan of `mus_c4p2_karsk` | — |
| p3 | 4 | close | Irina's lit dispatch window, a typed order on the sill; control to Alexei | a samovar humming behind the glass, a telephone rings once; hand-over to the level ambience | — |

`LS_C4P2_Steam` — Karsk → Berlin, Monday. The steam jet is ONE sound across the cut.
| shot | s | camera | picture | sound | text |
|---|---|---|---|---|---|
| m1 | 4 | side_on | The coal stage: the special-run locomotive takes coal; workers stretch a tarpaulin on poles "for tomorrow"; Alexei watches | coal rattling down the chute into the tender; the tarpaulin snapping on its poles | inner line `cin.c4p2.steam.alexei` „Sie spannen eine Plane für morgen. Damit der Schwede die Kohle sieht, aber nicht, wer schaufelt.“ |
| m2 | 1.5 | macro_locked | Macro: a white jet of steam from the locomotive's safety valve (match cut) | the safety valve's hiss (sound bridge) | — |
| m3 | 4 | macro_to_medium | Berlin, Ostbahnhof 20.30: the same white jet from the express locomotive under the glass roof; the departure board flips to D 303 Karsk 21.10 | the hiss opens into the glass hall's echo; the departure board's flaps clatter; a muffled announcement | caption `cin.c4p2.steam.berlin` „Berlin, Ostbahnhof, 20.30 Uhr.“ |
| m4 | 3 | establishing | Konrad on platform K in the crowd, Marta at the buffet in her driver's coat; control to Konrad | `amb_berlin_station`; the piano of `mus_c4p2_berlin` enters | — |

`LS_C4P2_Book` — Berlin → Karsk, Monday → Tuesday: THE shared object of this round. The cut lands on the sound of the
book.
| shot | s | camera | picture | sound | text |
|---|---|---|---|---|---|
| b1 | 3.5 | close | Dining car: Konrad's hand slides the card half and the tracing between pages 212 and 213 of Ekdahl's guidebook; Ekdahl closes it; the man from the kiosk reflected in the window | dining-car cutlery, the rustle of onion-skin paper | inner line `cin.c4p2.book.konrad` „Seite zweihundertzwölf. Mehr Russisch kann ich nicht.“ |
| b2 | 1.5 | macro_locked | Macro: the book closing (match cut) | the book shuts — a soft thud | — |
| b3 | 4 | macro_to_medium | Karsk, Tuesday 17.30: the same book opening at page 212 on the canteen table under a gloved hand; Alexei's fingers on the German half | the same book opens: paper; tea glasses in the canteen | caption `cin.c4p2.book.karsk` „Karsk, Dienstag, 17.30 Uhr.“ |
| b4 | 3 | establishing | The depot showcase under floodlights: the brass band, the polished locomotive with red ribbons, the press minder lighting a cigarette; control to Alexei | the brass band strikes up the Accord march (diegetic) over `amb_karsk_platform` | — |

`LS_C4P2_Express` — Karsk → Berlin, Tuesday. The decision is shown, never explained.
| shot | s | camera | picture | sound | text |
|---|---|---|---|---|---|
| x1 | 4 | side_on | Karsk platform 1, 20.10: the westbound express starts; Ekdahl at his window holds up a film canister (publish_now) or shows an empty hand and nods (protect_first) | the express whistle, the brakes releasing, couplings taking up the slack | — |
| x2 | 4 | fixed | Alexei and Lev on the emptying platform; the express recedes down the line; Lev buttons his carbons back into his coat (protect_first) or his hands are empty (publish_now) | the wheels fading; the band packing its instruments | inner line by `c4g_choose`: publish_now `cin.c4p2.express.alexei_publish` „Morgen weiß Stockholm, was in Kordon-17 um 23.40 Uhr geschieht. Und Archipov, wer es erzählt hat.“ / protect_first `cin.c4p2.express.alexei_protect` „Kein Zeuge an Tür Ost. Aber Lev schläft heute in seinem eigenen Bett.“ |
| x3 | 1.5 | macro_locked | Macro: the express's red tail lamp (match cut) | one last rail-joint knock, then quiet | — |
| x4 | 3.5 | tracking | Berlin, Kolonnenstraße 22.10: a red warning lamp on the building-site barrier of No. 12; Konrad walks under it into the gate passage of No. 14; control to Konrad | `amb_berlin_courtyard`: snow under shoes, the S-Bahn far off, a radio behind a window | caption `cin.c4p2.express.berlin` „Berlin, Kolonnenstraße, 22.10 Uhr.“ |

`LS_C4P2_Clock` — Berlin, Kordon-17, Karsk at 23.40 Korridorzeit. Music: `mus_c4p2_clock` throughout — both themes on
one clock; its tick runs from k1 and stops on k5.
| shot | s | camera | picture | sound | text |
|---|---|---|---|---|---|
| k1 | 5 | establishing | Berlin, 23.40: the courtyard of No. 14 from above; the black car leaves; Hanna's window stays lit; in the cobbler's basement window a candle, Ilse asleep on leather offcuts under the cobbler's coat | the car's doors and engine leaving the gate passage; the tick begins | caption `cin.c4p2.clock.berlin` „Berlin, 23.40 Uhr.“, then inner line by `c4d_choose`: name_marta `cin.c4p2.clock.konrad_name` „Ilse schläft zwischen Leisten und Leder. Hanna weiß jetzt, wessen Namen ich genannt habe.“ / protect_marta `cin.c4p2.clock.konrad_protect` „Ilse schläft zwischen Leisten und Leder. Wendt kennt jetzt meinen Namen.“ |
| k2 | 6 | establishing | Kordon-17, 23.40 corridor time, wide and from far: floodlights, the room on the Line, Tür Ost. publish_now: a flashbulb at the fence, a man with a notebook, the door stays shut, two figures are led back into the German hall; protect_first: the door opens, two figures cross the light into wagon C-17/45, the door closes (no faces, no force shown) | a far floodlight hum; publish_now: one flashbulb pop, voices far away; protect_first: a heavy door closing | caption `cin.c4p2.clock.kordon` „Kordon-17, 23.40 Uhr Korridorzeit.“ |
| k3 | 5 | side_on | Karsk, 1.40: Alexei at Irina's dispatch window; the teleprinter types (publish_now: handover suspended; protect_first: C-17/45 left Kordon-17); Lev's lamp in the freight office | the teleprinter (its strip in the picture, Russian telegraph style — publish_now „ПЕРЕДАЧА ПРИОСТАНОВЛЕНА ТЧК“, protect_first „С-17/45 УБЫЛ КОРДОН-17 ТЧК“; art only, not translated) | caption `cin.c4p2.clock.karsk` „Karsk, 1.40 Uhr.“ |
| k4 | 4 | macro_locked | Irina's desk under the lamp: the German half of card 0417 beside a film canister (protect_first) or beside Lev's empty folder (publish_now) | the lamp's hum, the tick | inner line by `c4g_choose`: publish_now `cin.c4p2.clock.publish` „Übergabe ausgesetzt. Nicht abgesagt.“ / protect_first `cin.c4p2.clock.protect` „Der Wagen fährt. Die Karte bleibt bei mir, bis keiner mehr dafür bezahlen muss.“ |
| k5 | 4 | title | Black; caption: end of the fourth chapter | the tick stops; silence | caption `cin.c4p2.clock.end` „Ende des vierten Kapitels.“ |
Rules (§12.5 + the C3 cinematic base `scenes/cinematics/ch3_common/c3_cinematic.gd`): every frame a pure function of t,
`skip()` idempotent, reduced_motion halves travel and softens flashes (the flashbulb of k2 becomes a soft brightening);
match cuts are hard cuts on matched shapes (steam jet → steam jet, closing book → opening book, red lamp → red lamp)
with a 2-frame white-free dip at most; the cities keep their palettes (Karsk: sodium and kerosene amber, coal black,
red banners; Berlin station: sodium under a glass roof and steam; Berlin courtyard: night blue with warm windows) so the
cut reads at a glance; Kordon-17 only wide and from far (Chapters 5–6 own the place up close); no violence shown, no
face of the people at Tür Ost, nobody inside a wagon. Voices/Depot/Steam/Book/Express/Clock choose by
`ctx.choices.get("c4g_choose", "")` and `ctx.choices.get("c4d_choose", "")` with defaults (`tests/test_c3_assets.gd`
configures all cinematics with a c3b-level context).

---------------------------------------------------------------------------------------------------------
## 3. Presentation layer — `data/chapters/c4p2.json` (ChapterExt merges every file in `data/chapters/`)
`levels`: KarskA/B → `res://scenes/levels/L_C4P2_Karsk.tscn`, BerlinA/B → `res://scenes/levels/L_C4P2_Berlin.tscn` ·
`entry_spawn` per scene (§2.1) · `chapter_cards` for all four scenes [`ui.chapter_c4`, `world.c4X.title`] (every scene
is a level load into another city) · `palettes.depot`, `palettes.ostbahnhof`, `palettes.courtyard` (placeholder ramps —
the env streams refine them) · `grades.depot_dawn`, `depot_evening`, `ostbahnhof`, `courtyard_night` · `switches`
(partner none + `ambience` / `music` / `grade` per scene: KarskA `amb_karsk_depot` / `mus_c4p2_karsk` / `depot_dawn`;
BerlinA `amb_berlin_station` / `mus_c4p2_berlin` / `ostbahnhof`; KarskB `amb_karsk_platform` / `mus_c4p2_karsk` /
`depot_evening`; BerlinB `amb_berlin_courtyard` / `mus_c4p2_berlin` / `courtyard_night`) · `line_expr` (every part-2
node), `line_variants`, `choice_text`, `reactions` · `puzzles` {`c4g_solve_halves`: `JoinPuzzle.tscn`,
`c4h_solve_house`: `HousePuzzle.tscn`} · `cinematics` (§2.9 paths) · `looks` {} (clean looks; optional for the cast
stream: a shaved, clean-scarf look `alexei_press` for KarskB — then `"looks": {"L_C4P2_KarskB": {"alexei":
"alexei_press"}}`, story owns the line) · `carry` {`L_C4P2_KarskB`: {`alexei`: `ev_c4_guidebook`}} (once Alexei owns
the guidebook he carries it — the existing carry rows). Texts: `de_c4p2_dialogue.json` (variants, reactions, option
variants), `de_c4p2_cinematics.json`, `de_c4p2_ui.json` (puzzle UIs, memories, task places), `de_c4p2_characters.json`
(new names/roles, journal people). Until a UI or cinematic scene exists ChapterExt reports it missing and the director
falls back (puzzle: the generic blueprint UI — fine for the join, NOT for the house; autoplay solves both through the
Story API; cinematic: skipped) — reported as pending (`tests/test_c3_assets.gd` `PENDING_R10`,
`tests/test_c4p2_routes.gd` `streams_pending_report`).

---------------------------------------------------------------------------------------------------------
## 4. Levels and hotspots (art ↔ content contract)
Both levels: side view like part 1, 1920×360, `mode = "side"`, feet line y 300, walk band y 296–306 (x 18–1902),
everything painted stands behind it (props `base_y` ≤ 294), foreground layer below y 318. Two walk areas per file,
separated by a permanent blocker; `camera_zones` per scene; one look + grade per scene. Both shells run
`scripts/levels/c4/annex_level.gd` (the round-9 two-places script: `"scene"` filters of layers / props / decals / fx /
lights / looks, `camera_zones`, blockers, `after` / `until` / `choice` gates); an env stream may give its level an own
script (one-line change of the root `script` line). The placeholder `scene.json` of both envs (story stream) names every
spawn, hotspot, blocker, camera zone and NPC anchor — **keep every name**; positions may move a few px for the art, the
walk areas and the order of the story hotspots stay. **Build the places lived-in from the start** (the user's art
feedback on the older scenes): no empty floor, no figure that reads as a block, people placed with intent (who works,
who waits, who watches, who looks away), layers of use and repair, light that tells the hour.

### 4.1 `L_C4P2_Karsk` — env `assets/environments/karsk_c4p2/` (scenes A and C of part 2: KarskA, KarskB)
Karsk locomotive depot, Monday 6.10 (A, dawn) and Tuesday 17.30–20.10 (B, evening floodlight). Left → right:
* 0–858 **Back yard and coal stage** (A): Irina's dispatch office — a brick lean-to with a lit window, the typed order
  on the sill, a samovar inside, a telephone, the duty board with seven names (x 90–230); the canteen's back hatch with
  a pot of kasha, a radio reading grain figures (x 250–330); the coal stage — a timber trestle with coal chutes over a
  tender, the list board on its post (x ≈ 400), Kolonne 4 at work (eleven returnees in mixed Western and Soviet
  clothes shovelling, carrying, resting — at least six readable figures as life strips; Maria at x ≈ 578 with a green
  headscarf), the ash pit with a dog asleep in the warmth (x 600–660), the guard at a barrel fire (x ≈ 690, sheepskin,
  rifle slung, young; he holds his hands over the fire and does not look at the gang), the roundhouse's back doors with
  steam from two stalls and the press notice (x 720–840); the water crane; snow, cinders, sparrows, frozen puddles,
  breath, the first train of the day passing behind.
* 858–898 the tarpaulin fence on poles (blocker `tarpaulin`): from A its back with patches and a gap; from B its front,
  painted with „ВОССТАНОВИМ ВМЕСТЕ“ for the press — the gang behind it.
* 898–1902 **Showcase and platform 1** (B): the restored signal on its post by the depot's front track (x 940–1010,
  green aspect — Alexei's signal of A1); the polished model locomotive with red ribbons and a wreath (x 1020–1100); the
  railway workers' brass band on a platform of planks (x 1100–1160, five players, children around); the press canteen —
  a hall with a white tablecloth, tea glasses, plates of bread with caviar on one side and the band's kasha behind a
  curtain (x 1140–1260; the minder at x ≈ 1110; the guidebook on the table at x ≈ 1170); the turntable in the yard
  (x 1260–1320, mini-game spot); the sand-drying house — a low brick shed, warm, a sand stove, a workbench under a
  green-shaded lamp (x 1320–1560: Lev at x ≈ 1368, the table at x ≈ 1460, the lamp at x ≈ 1520); a gate to the
  passenger side and platform 1 of Karsk station with the westbound Corridor express (x 1600–1902: the sleeping car, the
  dining car, Ekdahl's compartment door at x ≈ 1780, a militia patrol, families seeing off, a grandmother with a parcel,
  a vendor with pirozhki, the station clock); the line runs west into the dark (the special run leaves from the
  transfer track at 19.40 — never shown, only its order on Irina's sill).
Looks: A = blue-grey dawn, sodium on the coal stage, warm windows; B = evening floodlight on the showcase, warm canteen,
cold platform light. FX: steam (safety valves, the express), coal dust in the floodlight, snow, breath, the barrel fire,
a passing train in A every 30–50 s at −8 dB (never while a film runs). Story hotspots (x, 300): `dispatch_window` 132 ·
`irina_window` 196 · `coal_list` 400 · `maria_coal` 560 · `press_notice` 780 · `signal_post` 980 · `canteen_table` 1170
· `lev_sandhouse` 1350 · `sand_table` 1460 · `sand_lamp` 1520 · `express_door` 1780. NPC anchors: `irina_window` → Irina
at (214, 300), facing left · `maria_coal` → Maria at (578, 300), facing left · `guard_coal` → the guard (`guard_karsk`)
at (690, 300), `look_at_player = false` · `signal_post` → Ekdahl (`journalist`) at (998, 300), facing left, `hide_after`
`c4g_inspect_card` · `minder_canteen` → the press officer (`press_officer`) at (1110, 300), `look_at_player = false` ·
`lev_sandhouse` → Lev at (1368, 300), facing left, `show_after` `c4g_inspect_book` · `express_door` → Ekdahl again at
(1798, 300), facing left, `show_after` `c4g_inspect_card` (two StoryNPC nodes; only one is ever present). Spawns:
`SP_C4P2_Yard` (48, 300) — entry of A · `SP_C4P2_Signal` (930, 300) — entry of B. Camera zones: A `[0, 0, 878, 360]`, B
`[878, 0, 1042, 360]`. Exploration hotspots (explore stream, `explore_hotspots.json`): ≥ 24 px from the story hotspots;
A finds x 30–850 (gated `until_objective = c4e_inspect_notice`), B finds x 905–1895 (`after_objective =
c4e_inspect_notice`).

### 4.2 `L_C4P2_Berlin` — env `assets/environments/berlin_c4p2/` (BerlinA, BerlinB)
Berlin, Monday 20.30 (A, the Ostbahnhof under its glass roof) and Tuesday 22.10–23.40 (B, a tenement courtyard). Two
places in one file; left → right:
* 0–898 **Ostbahnhof, Korridorbahnsteig K** (A): the enamel departure board with the painted board for Tuesday (x
  60–160); the platform buffet — a counter with an urn, Marta at x ≈ 318 in her driver's coat (her duty roster on the
  counter reads „Linie 3“ / „Linie 74“ — decals with the art gate `choice.c4d_choose`), travellers with Corridor
  permits, a railway policeman (x 200–360); the newspaper kiosk with the man who reads the same page (`stapo_civil`, x ≈
  410); the D 303 express: the locomotive steaming under the roof, the windowless courier car with two lead seals (x ≈
  500), on the next track the green car with barred hatches and the chalk „Di – Kordon“; the dining car with lit windows
  and white tablecloths, Ekdahl leaning out (x ≈ 698), its open door with the table and the guidebook (x ≈ 800);
  porters, a family with a grandmother being helped up, pigeons under the roof, steam, snow blowing in from the open end
  of the hall, the station clock at 20.31.
* 898–938 the end of platform K (blocker `platform_end`).
* 938–1902 **Kolonnenstraße 14, courtyard** (B): the gate passage from the street (x 938–1100: the notice with the
  pinned site plan at x ≈ 1000, Kuhnert at x ≈ 1060 in a brown work coat with his card box under his arm, the sweep's
  car's headlights on the street after the puzzle); the courtyard of a five-storey Mietskaserne — the Seitenflügel on
  the left with its stair door and Hanna (x ≈ 1268, coat over her cardigan), the lodge window with Frau Kuhnert and the
  box of cards on the sill (x ≈ 1420), the pump and the carpet-beating rack in the middle (x ≈ 1600), the Hinterhaus at
  the back with the cobbler's souterrain windows (x 1700–1880; after the puzzle a candle — art gate `after
  c4h_solve_house`); dustbins, frozen laundry, a bicycle, a coal heap by the cellar hatch, snow on every sill. **Every
  lit window is a household** of the house puzzle (§2.7): Lenz's desk lamp and radio, the Schulzes' baby, Frau
  Grabowski's dark kitchen, Pohl's moving curtain, the Mertens family, the sealed dark windows of No. 3 in the back,
  Brettschneider's dark window, the Kühns' card game, Hanna's window with Ilse drawing at the table — the windows ARE
  the neighbours of Chapter 5. Far above the roofs the dome of the Great Hall in the night haze (`_hist` banners per
  §12.4).
Looks: A = sodium and steam under glass, warm dining car, cold platform; B = night blue, warm windows, one sodium lamp
in the passage; after 23.30 the car's headlights sweep the passage. FX: steam (A), snow (both), breath, a radio from a
window, the S-Bahn rumble (B). Story hotspots (x, 300): `departure_board` 110 · `marta_buffet` 300 · `courier_car` 500 ·
`ekdahl_window` 680 · `dining_table` 800 · `gate_notice` 1000 · `wendt_yard` 1110 · `hanna_yard` 1250 · `lodge_window`
1420 · `yard_pump` 1600. NPC anchors: `marta_buffet` → Marta at (318, 300), facing left · `shadow_kiosk` → the man at
the kiosk (`stapo_civil`) at (410, 300), `look_at_player = false` · `ekdahl_window` → Ekdahl at (698, 300), facing left
· `kuhnert_gate` → Kuhnert (`blockwart`) at (1060, 300) — present all of B (he waits in the passage from 22.00; he
speaks in Wendt's dialogue) · `wendt_yard` → Wendt at (1128, 300), facing left, `show_after` `c4h_solve_house` ·
`hanna_yard` → Hanna at (1268, 300), facing left, `hide_after` `c4h_solve_house` (she goes up to keep her light on).
Ilse appears only as a life strip (Hanna's window; the souterrain candle) — no dialogue, never in the walk band. Spawns:
`SP_C4P2_Platform` (60, 300) — entry of A · `SP_C4P2_Gate` (960, 300) — entry of B. Camera zones: A `[0, 0, 918, 360]`,
B `[918, 0, 1002, 360]`. Exploration hotspots: A finds x 30–890 (`until_objective = c4f_inspect_book`), B finds x
945–1895 (`after_objective = c4f_inspect_book`); ≥ 24 px from the story hotspots.

---------------------------------------------------------------------------------------------------------
## 5. Cast
Existing ids first: `alexei`, `konrad` (base looks), `irina` (dispatcher, A1 — dialogue in KarskA), `lev` (KarskB),
`marta` (BerlinA), `journalist` = Nils Ekdahl (C3, Stockholm correspondent — BerlinA and KarskB), `berlin_child` (Ilse,
life strips only), `clerk` / `worker_a` / `worker_b` (life strips). Mentioned, not shown: Anna Lindner, Pjotr Iljin,
Paul Lindner, Wilhelm, Lena and Miron, Archipov, Kessler, Elena Weiss, Herr Pietsch (the cobbler — his workshop only).
New characters (cast stream; sheet with the side rows of the other side-level NPCs + portrait with the four expressions
neutral / concerned / determined / surprised; names in `data/locale/de_c4p2_characters.json`):
| id | name (de) | role | age | look / costume | voice |
|---|---|---|---|---|---|
| `maria` | Maria Gorelowa | returnee from Veltrava, Kolonne 4 (scratched „Wir sind vierzehn“) | 34 | green headscarf; a thin Western wool coat (Veltrava) under an issued Soviet quilted vest, felt boots a size too big, rags around her hands, coal on her face, a needle stuck in her lapel (a seamstress); dark eyes, high cheekbones, a straight back | quiet, exact, bitter humour, never pleading |
| `hanna` | Hanna Adler | teacher, Konrad's younger sister, Kolonnenstraße 14, side wing 3rd floor | 27 | dark-blue wool coat over a grey cardigan, chalk dust on a sleeve, a rust-red knitted scarf, hair pinned up in a practical knot, a bunch of keys; the family's upright posture, freer than Konrad's | direct, warm, ironic toward her brother, braver than him |
| `wendt` | Kommissar Ludwig Wendt | Staatspolizei (the voice of the tube slip, part 1) | ≈ 50 | dark grey civilian overcoat with a fur collar, a homburg, black leather gloves, a small notebook; clean-shaven, heavy-lidded, a thin wedding ring; **no uniform, no insignia, no moustache or glasses that quote a historical perpetrator** | soft, polite, precise; never raises his voice |
| `blockwart` | Erwin Kuhnert | caretaker and Blockleiter, Kolonnenstraße 12–18 | ≈ 60 | brown work coat over a cardigan, a cap, reading glasses on a string, a big key ring, the wooden card box under his arm, felt slippers in galoshes; an armband only in the `_hist` variant via `Symbols.pick()` (neutral: none) | Berlin, nervous, officious — „Ordnung“ |
Life sheets without portraits (side rows, idle + a working idle; low priority, fallbacks in brackets): `guard_karsk` —
young Soviet guard, sheepskin coat, ushanka, rifle slung (fallback `worker_b`); `press_officer` — Soviet press minder,
grey coat, fur hat, briefcase, cigarettes (fallback `clerk`); `stapo_civil` — the man at the kiosk, leather coat, hat,
newspaper (fallback `clerk`). Kolonne 4 and the platform/street crowds are life strips of the env streams (no insignia,
people of every age, Western and Soviet clothes mixed on the returnees).
Priority: `maria` and `hanna` (portraits in the main path), then `wendt` and `blockwart`, then the three life sheets,
then the optional `alexei_press` look.

---------------------------------------------------------------------------------------------------------
## 6. Exploration brief (§12, §12.8, §12.9) — owner: exploration stream
Files `data/explore/c4p2_karsk.json`, `c4p2_berlin.json` (areas `karsk` / `berlin`, ids `karsk.depot.<name>`,
`berlin.ost.<name>` (station) and `berlin.k14.<name>` (courtyard)), strings `data/locale/de_explore_c4p2.json`, history
`data/explore/c4p2_history_soviet.json` / `c4p2_history_reich.json` + `data/locale/de_history_c4p2.json`, hotspots in
the two envs' `explore_hotspots.json`. **Explore entries of the shared levels use `"level": "L_C4P2_KarskA"` /
`"L_C4P2_BerlinA"`** (ChapterExt.level_key). Finds speak in the voice of the protagonist who can reach them and are
`gated_interactable`s per walk area (§4) with the `memory_scenes` rule of `scripts/ui/minigames/kartei_spot.gd`.
* Karsk A (Alexei, Monday dawn): `exp_duty_board` (seven drivers' names, one crossed out with „krank“ in Irina's hand —
  she protects them her way) · `exp_kolonne_shoes` (Western shoes falling apart beside issued felt boots: they came from
  Veltrava) · `exp_barrel_fire` (the guard is nineteen and from Kursk; he warms Maria's gloves when nobody looks) ·
  `exp_ash_pit_dog` · `exp_canteen_radio` (grain figures of the Accord, then a waltz) · `exp_banner_back` (the back of
  the tarpaulin: sacking patches, a child's chalk drawing of a train) · hidden `exp_lena_mitten` (a child's mitten
  nailed to the coal-stage post, a name sewn in Latin letters: „Lena“). Chat: Maria after `c4e_talk_maria` (until
  `c4e_inspect_notice`).
* Karsk B (Alexei, Tuesday showcase and platform): `exp_brass_band` (the tuba player is Irina's husband; they rehearsed
  the Accord march for a week) · `exp_model_engine` (a cleaner polished it for three days; the brass plate says 1939) ·
  `exp_press_buffet` (caviar for the guest, kasha behind the curtain) · `exp_tarpaulin_front` (through a tear: a
  shovel's handle) · `exp_platform_families` (permits with two stamps, a parcel for a son in Veltrava) · `exp_minder`
  (chat: the press officer hasn't slept; „Schreiben Sie: Wiederaufbau.“) · hidden `exp_signal_scratch` (on the signal
  post, scratched at child height in 1949: „А. М.“ — Alexei's own initials). Chat: Lev after `c4g_inspect_card` (until
  `c4g_choose`).
* Berlin A (Konrad, Ostbahnhof): `exp_kiosk` (the papers of the day; the Swedish paper is „vergriffen“) ·
  `exp_corridor_permit` (a family visiting a grandmother in Karsk once a year: two stamps, two languages) ·
  `exp_liaison_booth` (the Soviet liaison officer's glass booth: a Russian tea glass next to a German stamp pad — the
  two regimes at one desk) · `exp_station_clock` · `exp_porters` · `exp_green_car` (the barred hatches up close; a
  child's drawing inside the frost, wiped) · hidden `exp_ticket_stub`. Chat: Marta after `c4f_talk_marta` (until
  `c4f_inspect_book`).
* Berlin B (Konrad, courtyard): `exp_frozen_laundry` · `exp_carpet_rack` · `exp_workshop_window` (the cobbler's
  souterrain: lasts and shoes of the whole house, each pair with a name tag — the house's census in shoes) ·
  `exp_windows` (the lit windows, one line each) · `exp_dustbins` · `exp_cellar_hatch` · hidden `exp_ilse_drawing` (on
  the frost of Hanna's stair-door window: a house with all windows lit). Chats: Kuhnert (any time in B: „Ordnung muss
  sein, Herr Adler, sonst fragt einer, warum nicht.“), Hanna after `c4h_talk_hanna` (until `c4h_solve_house`).
* **Side tasks (one per level, all steps inside ONE walk area — the B areas, so the drivers' last passes before
  `c4g_choose` / `c4h_talk_wendt` finish them):** Karsk B „Ein Paket über die Linie“ — a grandmother on platform 1 wants
  to send a parcel to her son in Veltrava with the express; it is 600 g over the Corridor limit; Alexei weighs it on the
  sand house's scale, swaps the jar of honey for a letter, ties it with signal wire and hands it to the conductor — a
  human beat, no reward but her face. Berlin B „Ein Korb für Frau Grabowski“ — the widow in the front wing lowers a
  basket on a rope from the second floor (her coal card was blocked after her son "went over the Line"); Konrad fills it
  from the coal heap at the cellar hatch; she pulls it up and leaves her light on. Rewards are human beats, no new
  history card.
* **Mini-games (§12.8, one per level):** Karsk B „Die Drehscheibe“ at `exp_turntable` — turn the 30-m turntable so the
  model locomotive rolls into stall 7: rotate with inertia (←/→ or LB/RB or drag), brake (Space / A), the rails must
  meet within a few pixels, gentle failure (a bump, try again). Berlin A „Die Gepäckwaage“ at `exp_luggage_scale` — a
  decimal scale with two sliding weights: weigh the grandmother's suitcase and the family's parcels against the Corridor
  limit of 20 kg (keys ←/→ coarse, ↑/↓ fine, pad, mouse drag). Keyboard + pad + mouse, `demo_solve()` by synthetic keys,
  `ctx.auto`.
* **Real-history cards (sober, sourced, 450–800 characters, fact-checked like C3/C4; never on a joke spot; no duplicate
  of the 25 existing cards — `filtration`, `repatriation`, `special_settlements`, `order_270`, `deportations`,
  `census_1939`, `denunciation`, `ostarbeiter`, `evictions`, `forced_labor` are taken):** Karsk — `hist.soviet.propiska`
  (internal passport and residence registration since December 1932; the propiska as the register every police action
  could read; collective farmers without passports until the 1974 decree, issued from 1976) at `exp_duty_board` or
  `exp_corridor_permit`'s Karsk twin; `hist.soviet.foreign_correspondents` (foreign correspondents in Moscow: dispatches
  passed through the censor at the Central Telegraph until the formal end of prior censorship in 1961; travel outside
  Moscow only with permission, minders, expulsions) at `exp_press_buffet` or `exp_minder`; optional
  `hist.soviet.border_zone` (the Soviet border zone and "forbidden zone" regime: special permits, registration of
  residents, resettlements from the strip) at `exp_platform_families`. Berlin — `hist.reich.blockleiter` (the NSDAP's
  Block- and Zellenleiter: household lists down to the stairwell, reports on residents, the „Haushaltskartei“; a party
  office, not the police — and how often it simply fed the police) at `exp_windows` or the Kuhnert chat;
  `hist.reich.schriftleitergesetz` (the Editors Law of 4 October 1933: journalists licensed by the state, "Aryan"
  descent required, the editor answerable to the state; daily press directives from the Reich press conference) at
  `exp_kiosk`; optional `hist.reich.reichsmeldeordnung` (the national registration ordinance of 1938 and the 1939
  „Volkskartei“: every resident in a police register, used for call-ups and persecution — distinct from the census card
  already in `census_1939`) at `exp_liaison_booth`. Facts are checked by the explore stream (sources in the card, like
  round 9); topics may be swapped for better-sourced ones with a note in §12 "As built".

---------------------------------------------------------------------------------------------------------
## 7. Memories (§12.10)
The scene table is automatic (four new memory scenes, chapter 4 — „Kapitel 4 · Stimmen unter Beton“):
| memory scene | protagonist | unlocked by | place (de) | date (de) |
|---|---|---|---|---|
| `L_C4P2_KarskA` | alexei | `c4e_completed` | „Lokdepot Karsk, Kohlenbansen“ | „Februar 1964“ |
| `L_C4P2_BerlinA` | konrad | `c4f_completed` | „Ostbahnhof, Korridorbahnsteig, Berlin“ | „Februar 1964“ |
| `L_C4P2_KarskB` | alexei | `c4g_completed` | „Lokdepot Karsk, Schauseite“ | „Februar 1964“ |
| `L_C4P2_BerlinB` | konrad | `c4h_completed` | „Kolonnenstraße 14, Berlin“ | „Februar 1964“ |
Texts in `data/locale/de_c4p2_ui.json`: `ui.memories.decided.publish_now` „Hier habe ich Ekdahl alles mitgegeben – für
einen Zeugen an Tür Ost.“ · `ui.memories.decided.protect_first` „Hier habe ich den Film behalten. Lev, Maria und Konrads
Leute zuerst.“ · `ui.memories.echo.c4g_solve_halves` „Die Zähne griffen ineinander, der Stempel schloss sich. Eine
Karte, zwei Staaten.“ · `ui.memories.echo.c4h_solve_house` „Über den Boden, die Hintertreppe hinab, durch den Keller:
ein Weg, den keine Karte kennt.“ · task places `ui.tasks.place.L_C4P2_KarskA` „Lokdepot Karsk“,
`ui.tasks.place.L_C4P2_BerlinA` „Berlin: Ostbahnhof und Kolonnenstraße“. Prints `assets/ui/memories/L_C4P2_*.png` come
from the lead (capture → `gen_ui_memories.py`, `SHOTS` / `CROPS` inside each scene's camera zone; pending in
`tests/test_memories.gd` until then). Inside a memory each scene opens in its own walk area with its own protagonist;
story NPCs follow the remembered state (the levels' `objective_done` rule), so Ekdahl stands at the signal in a memory
of KarskB until the card is whole.

## 8. Audio brief (cast + audio stream)
Ambiences: `amb_karsk_depot` (dawn: safety valves, blowers, shovels on coal, a barrel fire, a dog, the canteen radio
far, sparrows, a train passing behind) · `amb_karsk_platform` (evening: the brass band rehearsing far, the express's air
pumps, Russian station announcements (original, unintelligible), a crowd, snow on the canopy) · `amb_berlin_station`
(under glass: echoing announcements, steam, luggage carts, pigeons, the kiosk's bell, the dining car's cutlery, a tram
bell from the forecourt) · `amb_berlin_courtyard` (night: a radio from a window, a baby, a dog far off, the S-Bahn
rumble, wind in the passage, a gutter dripping, the Hall's distant hum). Music: `mus_c4p2_karsk` (the bayan theme of
part 1 slower, low strings; in B the band's march as a diegetic counterpoint), `mus_c4p2_berlin` (piano and low strings,
the clockwork pulse of part 1), `mus_c4p2_clock` (the closing: both themes on one clock, a tick that stops). Cinematic
cues (per shot in §2.9): a safety-valve jet as a sound bridge, a book shutting / opening, an express whistle and
starting, a car leaving a gate passage, a teleprinter, a flashbulb (publish), a heavy door closing (protect), a clock
tick that stops. Puzzle sfx: card halves snapping together, a stamp ring closing; footsteps on wooden stairs, an attic
door, a spy-hole cover sliding (Pohl), a cellar door. Original, deterministic generators
(`tools/audiogen/c4p2_audio.py`); missing files are tolerated by `Audio`.

---------------------------------------------------------------------------------------------------------
## 9. Tests and drivers (story stream — done this round with the data)
* `tests/test_save_migration_r10.gd` (the migration, §1.1) and `tests/test_save_rebase_r8.gd` (round-9 forms: the
  montage after `c4d_completed` → `L_C4P2_KarskA` through the container path and as a memory snapshot, its missing flag
  filled).
* `tests/test_c4p2_routes.gd`: every combination a1 × m1 × c3a × c3b × c3d × c3g × c4d × c4g (576 routes) through the
  Story API (chain, protagonists, events, meters, items, finale); gating step by step through the 21 part-2 objectives
  (locks swept after every step, cinematics queued per step); both puzzles (wrong payloads keep the state; the solutions
  solve; the house answer is the ONLY safe way through the contract's graph); the decision (both options, invalid ids,
  meters, `people_protected` written by protect_first only); save/load at every part-2 step byte-identical; a round-9
  autosave plays on; line variants per route (no dead variant, fallback-only bases never heard, every base with variants
  heard where expected, option variants and reactions); the presentation contract (c4p2.json, switches, grades,
  palettes, cinematics registered and locked, puzzles registered); the two level shells (hotspots and spawns on the
  floor, inside their walk areas, one interactable per objective, NPC gates, camera zones; the shells load headless);
  German typography and ≤ 140 characters per spoken line; the board data of the new evidence; the end card's eight
  decisions; a pending report of what the other streams deliver.
* `tests/support/test_kit.gd` plays the extended chain (`STAGES` … c4e–c4h, `DEFAULT_CHOICES.c4g = publish_now`,
  `C4_HALVES`, `C4_HOUSE`, `play_c4e` … `play_c4h`, `play_stage`); every route / memories / parity / integrity / journal
  / signals / board test that encodes the chain got minimal edits; `tests/test_c3_assets.gd` `PENDING_R10`.
* `tests/reference/make_python_reference.py`: routes cover all eight choices × skip/play (1152 keys), the verified-route
  trace runs through part 2, a `chapter4p2_with_noise` trace, corpus checkpoints in part 2 (mid-dialogue, failed join,
  failed house, the decision, the end).
* Drivers: `--autoplay=<a1>,<m1>,<c3a>,<c3b>,<c3d>,<c3g>,<c4d>,<c4g>` and `--inputplay=…` (same spec; default c4g =
  `publish_now`, the first option like every other default); saves in `user://e2e/saves`; inputplay solves the
  JoinPuzzle by keys (Enter on the start pose = one wrong attempt, then R, R, →×4, ↓, Enter) and the HousePuzzle by keys
  (↓ + Enter = one wrong way past Frau Pohl, R, then ↑ → ↓×5 → and Enter); the decision by number key; „Fortsetzen“ must
  resume in `L_C4P2_BerlinB` before `c4h_talk_wendt` (the last autosave before the finale). Explore passes at every
  part-2 scene start and before `c4e_talk_maria`; the final passes before `c4g_choose` (Karsk file) and `c4h_talk_wendt`
  (Berlin file). The skip guard stays: Esc is pressed only while a cinematic is still running.
* QUEST_DATABASE §13 is generated by `tools/docs/gen_quest_db_c4p2.py` (§1 FLOW by gen_quest_db_c3.py, §12 by
  gen_quest_db_c4.py — now part 1 only); `--check` passes.

## 10. Ownership for the build phase (one owner per file; shared files only by small appended blocks / one-line edits)
| stream | owns |
|---|---|
| story (this contract) | `data/v3/*.json`, `data/chapters/c4p2.json`, `data/locale/de_c4p2_{dialogue,cinematics,ui,characters}.json`, `data/board/*` (data only), `scenes/levels/L_C4P2_Karsk.tscn` / `L_C4P2_Berlin.tscn` (node list), the placeholder `scene.json` of both envs until the art streams replace them, `LOCKED_CINEMATICS` in `scripts/story/story_engine.gd`, `scripts/core/save_system.gd` (flag fill), `Memories.memory_flags`, `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd`, `tests/test_c4p2_routes.gd`, `tests/test_save_migration_r10.gd`, `tests/support/test_kit.gd`, `tests/reference/**`, `tools/docs/gen_quest_db_c*.py`, `documentation/QUEST_DATABASE.md` |
| env-karsk | `tools/pixelgen/env_c4p2_karsk*.py`, `assets/environments/karsk_c4p2/**` (replaces the placeholder scene.json, keeps every name of §4.1), `assets/ui/documents/karsk_c4p2_*` (+ `karsk_c4p2_documents.json`), its level script (root `script` line of `L_C4P2_Karsk.tscn`), Kolonne 4 / platform life strips, `tests/test_c4p2_karsk_art.gd`, `asset_manifest_parts/env_c4p2_karsk.md` |
| env-berlin | `tools/pixelgen/env_c4p2_berlin*.py`, `assets/environments/berlin_c4p2/**` (keeps every name of §4.2; the windows of the courtyard = the households of §2.7), `assets/ui/documents/berlin_c4p2_*`, its level script, `tests/test_c4p2_berlin_art.gd`, `asset_manifest_parts/env_c4p2_berlin.md` |
| cine | `scenes/cinematics/ch4p2_{depot,steam,book,express,clock}/**`, `tools/pixelgen/env_c4p2_cine*.py`, `assets/cinematics/ch4p2/**`, cinematic sound cues (with audio), `data/locale/de_c4p2_cine.json` (film titles), `tests/test_c4p2_cinematics.gd`, `asset_manifest_parts/c4p2_cine.md` |
| puzzle | `scenes/ui/HousePuzzle.tscn`, `scripts/ui/house_puzzle.gd`, `scenes/ui/JoinPuzzle.tscn` (+ `scripts/ui/join_puzzle.gd` or a per-objective layout in `route_puzzle.gd` — then a minimal edit there), `assets/ui/puzzle/c4p2_*` (incl. `c4p2_house.json`), `assets/ui/documents/karsk_c4p2_halves.json` (+ its art), `data/locale/de_c4p2_puzzles.json`, `tests/test_c4p2_puzzle_ui.gd`, `asset_manifest_parts/c4p2_puzzle.md` |
| cast-audio | `assets/characters/{maria,hanna,wendt,blockwart,guard_karsk,press_officer,stapo_civil}/**` (+ optional `alexei_press`) via their generators, `tools/audiogen/c4p2_audio.py`, `assets/audio/amb/amb_{karsk_depot,karsk_platform,berlin_station,berlin_courtyard}.wav`, `assets/audio/music/mus_c4p2_*.wav`, `tests/test_c4p2_cast_audio.gd`, `asset_manifest_parts/c4p2_cast_audio.md` |
| explore | `data/explore/c4p2_*.json`, `data/locale/de_explore_c4p2.json`, `de_history_c4p2.json`, the two envs' `explore_hotspots.json`, new mini-game scenes/scripts, Find_/Chat_/Task_ nodes appended at the end of the two .tscn Playfields (small Edit insertions), `tests/test_c4p2_explore.gd`, `asset_manifest_parts/c4p2_explore.md` |
The evidence board reads the part-2 items as they are; its data (places `karsk_depot`, `berlin_ost`, `berlin_k14`,
spots, short titles, nine thread groups, eleven summary milestones incl. the `tuesday` slot that answers part 1's open
question in place) is in `data/board/*` already. Card pictures of the eleven new items: `tools/pixelgen/gen_ui_board.py`
after the document art lands (pending in `tests/test_evidence_board.gd`). Pairs that belong together on the board:
`ev_c4_special_order` ↔ `ev_c4_stencils` (run 45) · `ev_c4_work_list` ↔ `ev_c4_wagon_inside` (the fourteen) ·
`ev_c4_press_notice` ↔ `ev_c4_work_list` (behind the tarpaulin) · `ev_c4_departures_east` ↔ `ev_c4_courier_seals` ↔
`ev_c4_card_de` (Tuesday to Kordon-17) · `ev_c3_kordon_plan` ↔ `ev_c4_konrad_tracing` ↔ `ev_c4_guidebook` (the same room
drawn twice) · `ev_c4_card_de` ↔ `ev_c4_card_whole` ↔ `ev_c4_card_ru_original` (one card, two halves) ·
`ev_c4_special_order` ↔ `ev_c4_card_whole` (Tue 23.40, Tür Ost) · `ev_c4_notice` ↔ `ev_c4_house_notice` (gez. K. A. —
No. 14 too) · `ev_c4_drawer_s8` ↔ `ev_c4_house_cards` (card files down to the stairwell).

## 11. Acceptance criteria (round 10, Chapter 4 part 2)
1. A new game reaches the montage through A1 … C4d and the four part-2 scenes; every scene starts in its own city and
   walk area with its protagonist; the end card lists eight decisions in story order.
2. `L_C4_AnnexB → L_C4P2_KarskA → L_C4P2_BerlinA → L_C4P2_KarskB → L_C4P2_BerlinB → L_X1_Montage`; the five part-2
   films are queued at their events (Depot after Voices) and never block a scene when their scene file is missing.
3. Both puzzles are solvable by keyboard only, by pad only and by mouse only; a wrong answer never changes Story state
   beyond the attempt counter; the hint appears after two failures; the house's answer is the only safe way.
4. Every part-2 line variant is heard on some route; every fallback-only base is never heard in normal play; the option
   variants appear on the routes they are written for; every spoken line ≤ 140 characters, German typography.
5. Saves anywhere in part 2 load byte-identically and continue; saves of every earlier build (slice era, rounds 7/8/9 —
   autosaves, quicksaves, memory snapshots) load with their missing flags filled; a round-9 montage form / annex
   snapshot is re-based to `L_C4P2_KarskA`.
6. `flags.json` has 17 flags (`people_protected` new, written by protect_first only); `LOCKED_CINEMATICS` and the Python
   reference cover the new data; the unit suite is green (art, films, puzzle UIs and cast reported as pending while
   missing); the drivers' choice spec takes eight values.
7. Content rules: no glorification, no false equivalence (Maria's filtration and the Blockleiter's card file keep the
   two repressions specific), people before slogans, real insignia only as `*_hist` variants via `Symbols.pick()`, no
   real person named in the work list or the windows, the pre-rename name of the German protagonist never appears;
   Kordon-17 only from far.

## 12. As built (round 10) — departures from this contract, recorded by the lead
Everything not listed here is built as contracted above; ids, objectives, lengths, sound-sync times and layout keys
are unchanged.

**Cinematics (cine stream)**
* The film art lives in `assets/cinematics/c4p2/` (mirroring `assets/cinematics/c3p2/`), not in `assets/cinematics/ch4p2/`
  as §10 said; the scenes stay in `scenes/cinematics/ch4p2_*`.
* The `macro_to_medium` moves (b3 in `LS_C4P2_Book`, m3 in `LS_C4P2_Steam`) are hard cuts on the movement, followed by
  a small camera settle — no dissolve.
* k1 (`LS_C4P2_Clock`) shows the side-wing courtyard square-on and tilts up to Hanna's window; with reduced motion it
  cuts instead. k3 is a frontal two-shot built from the dialogue busts — Irina at the teleprinter, Alexei outside the
  frosted window — not side-on.
* x2 (`LS_C4P2_Express`) is over Alexei's shoulder, Lev facing the camera (his bundle of carbons or his empty hands).
* `LS_C4P2_Clock` plays `mus_c4p2_clock` as a one-shot from t = 0 and never cuts it (its tick runs to k5 = 20 s); if
  the file is missing the film's own stand-in bed `c4p2cine_tick` plays.

**Puzzles (puzzle stream)**
* The JoinPuzzle „Die Hälften“ has its own `scripts/ui/join_puzzle.gd` (the RoutePuzzle key/pad/mouse contract).
* `ui.c4p2.halves.wrong_sideways` answers a quarter turn, `ui.c4p2.halves.wrong_turned` an upside-down half (both read
  from the marks' geometry).
* HousePuzzle: from the 3rd failure on, a walk that runs into a watcher cuts the route back to the last safe room.
* The Blockleiter's watcher mark is drawn as his cap (as on his cast sheet); its id stays `hat`.
* Herr Pietsch is not drawn — his stool and apron in the souterrain workshop are.
* The puzzle texts are in `data/locale/de_c4p2_puzzles.json` (the contract's name); the file only adds keys and never
  overrides the story's.

**Exploration (explore stream)**
* „Die Drehscheibe“ pulls the sooty shunting engine („Kukuschka“) into stall 7, not the show engine: env-karsk keeps
  the Musterlok on the front track for the whole of scene B.
* Two finds beyond the brief: `exp_water_crane` (KarskA) and `exp_two_clocks` (KarskB).
* Kuhnert's chat closes at `c4h_solve_house`.
* History cards made: `propiska`, `foreign_correspondents`, `schriftleitergesetz`, `blockleiter`. The optional
  `border_zone` and `reichsmeldeordnung` cards were not made.
* Frau Grabowski is the voice-only speaker `grabowski` (no character sheet; the dialogue box shows the silhouette).

**Environments (env-karsk, env-berlin)**
* The generators carry the contract table's names `tools/pixelgen/env_c4p2_karsk*.py` and `env_c4p2_berlin*.py`.
* `L_C4P2_Berlin.tscn`'s root script is `scripts/levels/c4p2/berlin_c4p2_level.gd` (extends `annex_level.gd`; footsteps
  per place). The sweep's two men after the puzzle are painted figures (a gated life strip), not character sheets.
* Lead's integration pass: in KarskA the shoveller `k4_shovel_b` stands 21 px further left so her shovel stays clear of
  Maria, and the old man of Kolonne 4 with his rest corner (sleeper, thermos, bread) sits by the canteen's bottle
  crates — Lena's mitten on the strut post stays in view. In BerlinA the passenger with the case starts at x 345, clear
  of Marta. BerlinB's courtyard floor has two neighbours until the house is solved: an old man up from the cellar with
  a coal scuttle (between the hatch and the lodge) and a woman out of the wash-house with the last basket for the attic
  (Tuesday is washing day). Nobody beats a carpet at 22.10 — the rack's own house-rules plate says 8–12 and 15–18 Uhr.

**Shared data and code (lead)**
* `data/chapters/c4p2.json` carries the env streams' ramps: `palettes.depot` = all 22 ramps of
  `env_c4p2_karsk_kit.DEPOT` (98 colours, incl. `skyglow` and `violet`), `palettes.ostbahnhof` + wood / brick / enamel /
  cream (53), `palettes.courtyard` + dusk / wood / green (50). To hold the depot palette the post shader's palette snap
  (`assets/shaders/post_grade.gdshader`, `Game._apply_grade`, the a1→m1 film's grade blend) takes up to 128 colours
  (was 64); `test_c3_presentation` checks ≤ 128.
* `looks`: `L_C4P2_KarskB` dresses Alexei as `alexei_press` (clean scarf, shaved; carry rows with the red guidebook).
* The story NPCs with a work loop play it as their idle (`idle_anim = "work_side"`): Maria (shovel), the guard (warming
  at the barrel fire in front of him), the press minder (smokes), the man at the kiosk (reads), Kuhnert (card box).
* Evidence board: the „?“ column never grows past two sub-columns (`UNKNOWN_MAX_COLS`). The 11 new items have card
  pictures — detail crops of their inspect close-ups (`gen_ui_board.py` `DOC_CROPS`).
