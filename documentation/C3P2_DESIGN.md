# CHAPTER 3, PART 2 — „Der eiserne Frieden“ (second half) — design contract

Status: AUTHORED 2026-11-06 (round 8). Single source of truth for every contributor of this round (story data,
engine/switch, registry art, quay art, cinematics, puzzle UI, exploration, characters, audio, tests). Builds on
C3_DESIGN.md (the opening — its ids, texts and rules stay valid), STORY_BIBLE §2/§3/§6/§7, CHARACTER_BIBLE,
WORLD_BIBLE, TECHNICAL_ARCHITECTURE §11–§13 and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md` („Erst eine
gemeinsame Belegprüfung macht ihnen klar, dass der Vertragspartner nicht einfach die Person im anderen Land ist.
Die erste Zusammenarbeit ist begrenzt, angespannt und von Misstrauen begleitet.“). German protagonist: **Konrad
Adler** (`konrad`); the pre-rename name never appears.

**What part 2 is:** the night after the first conference day. Both men receive the same note („– E.“), meet in the
commission's registry, lay their halves side by side for the first time (the joint evidence check), find out that
their governments are not each other's opponents in C-17 but partners — and that „Begleitgut“ means people. Someone
sets the registry on fire; in alternating control they carry one file out through the smoke and a 1909 coal chute.
In the snow by the river the file falls apart; each keeps half. Elena does not return. A name on the next list —
Pjotr Iljin, Alexei's childhood friend — sets up Chapter 4. Nothing is resolved: not who set the fire, not where
Elena is, not what the „Begleitgut“ of tonight's train means for the fourteen people on it.

Target play time **15–17 min**: night cinematics ≈ 1 · registry A (Alexei) ≈ 3 · registry B (Konrad, the check)
≈ 5.5 · fire C+D (alternating) ≈ 3 · quay ≈ 2.5 · closing ≈ 0.5.

---------------------------------------------------------------------------------------------------------
## 1. Flow

```
… c3b_choose ══> c3b_completed ──> LS_C3_Close (existing: 23.40, platform 5) ──> LS_C3_Radio (new, hotel rooms)
 ──> L_C3_RegistryA (Alexei)    c3c_talk_konrad ══> c3c_completed ── in-level switch ──┐
 ┌──────────────────────────────────────────────────────────────────────────────────────┘
 └> L_C3_RegistryB (Konrad)     c3d_choose ══> c3d_completed ──> LS_C3_Fire ── in-level switch ──┐
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┘
 └> L_C3_RegistryC (Alexei)     c3e_reach_konrad ══> c3e_completed ── in-level switch ──┐
 ┌──────────────────────────────────────────────────────────────────────────────────────┘
 └> L_C3_RegistryD (Konrad)     c3f_climb ══> c3f_completed ──> LS_C3_Escape ──> level load (fade)
 ──> L_C3_Quay (Alexei)         c3g_choose ══> c3g_completed ──> LS_C3_Halves ──> L_X1_Montage (finale + end card)
```
* The unchanged engine needs ONE linear scene chain ending in the non-quest montage (C3_DESIGN §1). The five new
  scenes are inserted between `L_C3_Hall` and `L_X1_Montage`: `L_C3_Hall.next_scene = L_C3_RegistryA` … 
  `L_C3_Quay.next_scene = L_X1_Montage`; `slice_end_requires` = all nine quest events.
* `L_C3_RegistryA`–`D` are four Story scenes in ONE level file (`scenes/levels/L_C3_Registry.tscn`): the first
  authored use of the in-level protagonist switch (§4). `L_C3_Quay` is a normal level (`L_C3_Quay.tscn`).
* `LS_C3_Close` (trigger `c3b_completed`) keeps its scene and meaning; it is now the opening of the night, and
  `LS_C3_Radio` (same trigger, authored after it) follows directly. The end card still comes after the montage.

### 1.1 Save and profile compatibility (binding)
* **No new flags this round.** `Story.load_json` compares a v3 save's flag table exactly with the replay (only
  v0.3 files get defaults merged), so ONE new flag would invalidate every save AND every memory snapshot in
  `user://profile.json` of the current build. Part 2 therefore writes only the existing meters
  (`alexei_konrad_trust`, `evidence_chain`, `elena_trust`) and the choice history (`c3d_choose`, `c3g_choose`),
  which later chapters read (§3.2 `choice.<objective>` conditions; cinematics get `ctx.choices`).
  A later round that needs flags first lands the Saves-side default fill (patch in the round-8 integration notes).
* New events `c3c_completed` … `c3g_completed` are harmless: saves that have not reached them replay identically.
* Every save a player normally has stays valid (autosaves never store the montage). A save whose scene is
  `L_X1_Montage` with only a1…c3b done (impossible through the UI) is rejected, as in C3_DESIGN §1.
* **Profile snapshots of `L_C3_Hall`** (memories, recorded at `c3b_completed`) name `current_scene = L_X1_Montage`;
  after the re-link they fail validation → memory/film „broken“ toast. Required fix (memories owner): when a
  snapshot fails, re-base it — set `current_scene`/`active_character` to the scene that now follows the scene whose
  `exit_on_event` is the snapshot's last completed event, then validate again (patch in the integration notes).

---------------------------------------------------------------------------------------------------------
## 2. Story data (data/v3) — ids are binding

### 2.1 Scenes
| id | title_key (de) | protagonist | camera_mode | entry_spawn | quest | exit event | next | render_profile |
|---|---|---|---|---|---|---|---|---|
| `L_C3_RegistryA` | `world.c3c.title` „Registratur der Kommission, Veltrava – Nacht (fiktiv)“ | alexei | side_on_2d | `SP_C3_Gate` | `q_c3c_registry` | `c3c_completed` | `L_C3_RegistryB` | `rp_veltrava_registry` |
| `L_C3_RegistryB` | `world.c3d.title` „Registratur der Kommission – Sortiertisch“ | konrad | side_on_2d | `SP_C3_KonradCards` | `q_c3d_check` | `c3d_completed` | `L_C3_RegistryC` | `rp_veltrava_registry` |
| `L_C3_RegistryC` | `world.c3e.title` „Registratur der Kommission – Rauch“ | alexei | side_on_2d | `SP_C3_AlexeiTable` | `q_c3e_smoke` | `c3e_completed` | `L_C3_RegistryD` | `rp_veltrava_fire` |
| `L_C3_RegistryD` | `world.c3f.title` „Registratur der Kommission – Kohlenschütte“ | konrad | side_on_2d | `SP_C3_KonradBooth` | `q_c3f_chute` | `c3f_completed` | `L_C3_Quay` | `rp_veltrava_fire` |
| `L_C3_Quay` | `world.c3g.title` „Am Kai hinter dem Palais, Veltrava (fiktiv)“ | alexei | side_on_2d | `SP_C3_Quay` | `q_c3g_snow` | `c3g_completed` | `L_X1_Montage` | `rp_veltrava_quay` |
`L_C3_Hall.next_scene` changes from `L_X1_Montage` to `L_C3_RegistryA` (the only modified record).

### 2.2 Quests (title `ui.chapter_c3` „Der eiserne Frieden“ — same chapter)
| id | character | scene | requires_events | completion_event |
|---|---|---|---|---|
| `q_c3c_registry` | alexei | L_C3_RegistryA | `c3b_completed` | `c3c_completed` |
| `q_c3d_check` | konrad | L_C3_RegistryB | `c3c_completed` | `c3d_completed` |
| `q_c3e_smoke` | alexei | L_C3_RegistryC | `c3d_completed` | `c3e_completed` |
| `q_c3f_chute` | konrad | L_C3_RegistryD | `c3e_completed` | `c3f_completed` |
| `q_c3g_snow` | alexei | L_C3_Quay | `c3f_completed` | `c3g_completed` |

### 2.3 Objectives
Every inspect objective grants an item (the InspectView and the input driver rely on it).

Registry A — Alexei arrives (night, snow):
```
c3c_inspect_crates ─> c3c_inspect_night_book ─> c3c_talk_konrad ══> c3c_completed (switch → Konrad)
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c3c_inspect_crates` | inspect | `obj.c3c_crates` „Sieh dir die Kisten an der Rampe an.“ | — | `ev_c3_cut_seal` | `crates` |
| `c3c_inspect_night_book` | inspect | `obj.c3c_night_book` „Lies das Nachtbuch in der Pförtnerloge.“ | crates | `ev_c3_night_book` | `porter_booth` |
| `c3c_talk_konrad` | dialogue `dlg_c3c_night` | `obj.c3c_konrad` „Geh dem Licht zwischen den Karteischränken nach.“ | night_book | — | `konrad_cards` |

Registry B — Konrad, the joint evidence check:
```
c3d_inspect_intake ─┬─> c3d_talk_compare ─> c3d_solve_check ─> c3d_inspect_plan ─> c3d_talk_partner ─> c3d_choose
c3d_inspect_drawer ─┘                                                                                     ══> c3d_completed
```
| id | type | text (de) | requires | grants | effects | hotspot |
|---|---|---|---|---|---|---|
| `c3d_inspect_intake` | inspect | `obj.c3d_intake` „Schlag das Eingangsbuch der Registratur auf.“ | — | `ev_c3_intake_book` | — | `intake_desk` |
| `c3d_inspect_drawer` | inspect | `obj.c3d_drawer` „Sieh dir die offene Schublade C-17 an.“ | — | `ev_c3_scarf` | — | `drawer_c17` |
| `c3d_talk_compare` | dialogue `dlg_c3d_compare` | `obj.c3d_compare` „Leg deine Unterlagen neben Morozovs.“ | intake, drawer | `ev_c3_halves` | — | `alexei_table` |
| `c3d_solve_check` | puzzle `pz_c3_check` | `obj.c3d_check` „Prüft Beleg gegen Beleg: Welcher Eintrag gehört zu welchem Papier?“ | compare | — | — | `sorting_table` |
| `c3d_inspect_plan` | inspect | `obj.c3d_plan` „Such Blatt 7 von Anlage C an der Planwand.“ | solve_check | `ev_c3_kordon_plan` | — | `plan_wall` |
| `c3d_talk_partner` | dialogue `dlg_c3d_partner` | `obj.c3d_partner` „Sprich mit Morozov über Blatt 7.“ | inspect_plan | — | — | `alexei_table` |
| `c3d_choose` | choice | `obj.c3d_choice` „Entscheide, was du ihm über Blatt 7 sagst.“ | talk_partner | — | per choice | `alexei_table` |

Registry C — Alexei carries the file through the smoke; Konrad reads the building plan:
```
c3e_take_file ─> c3e_try_ramp ─> c3e_reach_konrad ══> c3e_completed (switch → Konrad)
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c3e_take_file` | inspect | `obj.c3e_file` „Nimm die Akte C-17 vom Sortiertisch.“ | — | `ev_c3_file` | `sorting_table` |
| `c3e_try_ramp` | inspect | `obj.c3e_ramp` „Versuch, durch die Rampentür hinauszukommen.“ | take_file | `ev_c3_bolt` | `ramp_door` |
| `c3e_reach_konrad` | dialogue `dlg_c3e_smoke` | `obj.c3e_konrad` „Folge Adlers Stimme zur Pförtnerloge.“ | try_ramp | — | `konrad_booth` |

Registry D — the reverse: Konrad carries the file; Alexei holds the iron door:
```
c3f_inspect_hose ─> c3f_push_desk ─> c3f_climb ══> c3f_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c3f_inspect_hose` | inspect | `obj.c3f_hose` „Hol den Löschschlauch aus dem Feuerkasten.“ | — | `ev_c3_cut_hose` | `fire_case` |
| `c3f_push_desk` | dialogue `dlg_c3f_desk` | `obj.c3f_desk` „Schieb mit Morozov das Pult von der Kohlenschütte.“ | hose | — | `intake_desk` |
| `c3f_climb` | dialogue `dlg_c3f_chute` | `obj.c3f_chute` „Kletter mit der Akte in die Schütte.“ | push_desk | — | `chute_door` |

Quay — Alexei, outside in the snow:
```
c3g_inspect_halves ─> c3g_talk_konrad ─> c3g_choose ══> c3g_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c3g_inspect_halves` | inspect | `obj.c3g_file` „Sieh dir an, was von der Akte übrig ist.“ | — | `ev_c3_escort_list` | `bench` |
| `c3g_talk_konrad` | dialogue `dlg_c3g_snow` | `obj.c3g_konrad` „Sprich mit Adler.“ | halves | — | `konrad_quay` |
| `c3g_choose` | choice | `obj.c3g_choice` „Entscheide, wie ihr die Akte teilt.“ | talk_konrad | — | `konrad_quay` |

### 2.4 Choices (every option raises exactly one existing meter; all options always offered)
| objective | choice id | base text (de) | effect | reaction (speaker: line) |
|---|---|---|---|---|
| `c3d_choose` | `admit_plan` | „Ihm sagen, dass Blatt 7 deine Zeichnung ist“ | `alexei_konrad_trust +1` | alexei: „Gezeichnet haben Sie einen Raum. Die Bank hat ein anderer hineingestellt. – Danke, dass Sie es sagen.“ (c3b = report_delegation: „Heute früh melden Sie mich, heute Nacht sagen Sie mir die Wahrheit. Sie sind gründlich, Adler.“) |
| | `pocket_plan` | „Blatt 7 einstecken und sagen: ‚Ein Büro in Berlin.‘“ | `evidence_chain +1` | alexei: „Ein Büro in Berlin. Bei uns zeichnen auch immer Büros.“ |
| `c3g_choose` | `split_by_language` | „Nach Sprache teilen: Du nimmst die russischen Blätter, er die deutschen“ | `evidence_chain +1` | konrad: „Jeder trägt, was er lesen kann. Und jeder kann es bezeugen – in seiner Sprache.“ |
| | `swap_halves` | „Über Kreuz teilen: Er nimmt die russischen Blätter mit Pjotrs Namen, du die deutschen“ | `alexei_konrad_trust +1` | konrad: „Pjotrs Name fährt mit mir nach Berlin. Bei mir sucht ihn niemand. – Ich passe darauf auf, Morozov.“ |
| | `hide_for_elena` | „Die Liste in Elenas Mantel stecken – Garderobe, Marke 27 – und den Rest nach Sprache teilen“ | `elena_trust +1` | konrad: „Wenn sie zurückkommt, holt sie zuerst ihren Mantel. Das tun alle. – Ich bringe die Liste hin.“ |

Why each option costs something: `admit_plan` earns trust, but Blatt 7 stays on the wall and burns (the sheet is
lost as evidence); `pocket_plan` saves the sheet (an independent document) and keeps Konrad's secret.
`split_by_language` keeps every page verifiable by its holder; `swap_halves` makes each man carry the other's
names over his own border (safer at home, but each depends on the other); `hide_for_elena` keeps the names out of
every border search and bets on Elena coming back.
Option text variants (`data/chapters/c3.json` `choice_text`, first match wins): `admit_plan` — c3b report_delegation
„Ihm sagen, dass Blatt 7 deine Zeichnung ist – nach der Meldung bei Kessler schuldest du ihm das“; `pocket_plan` —
konrad_evidence ≥ 1 „Blatt 7 zu Emils Abschrift stecken und sagen: ‚Ein Büro in Berlin.‘“, office_suspicion ≥ 1
„Blatt 7 einstecken – in Berlin fragt man nicht zweimal – und sagen: ‚Ein Büro in Berlin.‘“ (every variant keeps the quoted words the reaction answers; the base text is fallback-only because M1 always sets one of the two flags); `split_by_language` — alexei_secrecy ≥ 1 „Nach
Sprache teilen – und für dich behalten, wer Pjotr ist“; `swap_halves` — alexei_konrad_trust ≥ 2 „Über Kreuz teilen:
Du vertraust ihm Pjotrs Namen an, er dir seine Leute“; `hide_for_elena` — elena_trust ≥ 2 „Die Liste in Elenas
Mantel stecken, Marke 27 – sie wird kommen“.
Meter ranges stay valid on every route: trust ≤ 3 (share_protocol + admit + swap), evidence ≤ 3, elena ≤ 3, kessler ≤ 1.

### 2.5 Items (evidence)
| id | name (de) | description (de) | category | scene |
|---|---|---|---|---|
| `ev_c3_cut_seal` | Durchtrennte Plombe C-17/44 | Die Kisten aus Kurierwagen 4 stehen leer an der Rampe. Die Plombe hängt noch am Draht – durchtrennt, nicht gebrochen, mit einer Zange, die jemand dafür hatte. | physical_clue | RegistryA |
| `ev_c3_night_book` | Nachtbuch der Pforte | „23.10 – Weiss, E. (Kommission): Protokollheft Kabine 2 zur Ablage.“ Darunter: „23.25 – ab.“ Die zweite Zeile hat ein anderer geschrieben. Die Loge ist leer, am Haken hängt kein Mantel. | document | RegistryA |
| `ev_c3_intake_book` | Eingangsbuch der Registratur, Serie C-17 | Jeden Dienstag ein Kurierwagen, mal aus Karsk, mal aus Berlin. Heute, 9.52 Uhr: Wagen 4, Plombe C-17/44, 2410 kg „Akten“. Ausgang 23.40 Uhr, Gleis 5: „Begleitgut, 14 Stück“. Russische Spalte: 14 Personen. | document | RegistryB |
| `ev_c3_scarf` | Elenas Schal | Der weinrote Schal, den Elena heute Morgen im Palais trug, hängt über dem Stuhl vor der Schublade C-17. Vorn fehlt ein Bündel Karten – wo sie standen, liegt kein Staub. | physical_clue | RegistryB |
| `ev_c3_halves` | Zwei Hälften auf einem Tisch | Alexeis Frachtkette – Wiegekarte, Abfahrtstafel, Reiseauftrag, Dienstfahrplan aus Karsk – neben Konrads Sitzordnung, Dolmetscherprotokoll und Durchschrift. Zum ersten Mal liegt alles auf einem Tisch. | document | RegistryB |
| `ev_c3_kordon_plan` | Anlage C, Blatt 7: Erfassungsraum Kordon-17 | Ein Raum genau auf der Linie: eine Tür zur deutschen Halle, eine zur sowjetischen, dazwischen ein Durchgabeschalter. Revision c, mit anderer Tusche: „Wartebank, 14 Plätze“. Im Schriftfeld: gez. K. Adler. | document | RegistryB |
| `ev_c3_file` | Akte C-17 · Gegenstellen | Die Akte der Registratur zu Serie C-17: Ersuchen aus Berlin und aus Karsk, Durchschläge des Eingangsbuchs, die Begleitliste der nächsten Sonderfahrt. Der Einband ist warm. | document | RegistryC |
| `ev_c3_bolt` | Verriegelte Rampentür | Die Rampentür gibt nicht nach. Durch den Spalt am Boden: der Riegel ist von außen vorgeschoben, im Schnee führen frische Spuren zum Tor. | physical_clue | RegistryC |
| `ev_c3_cut_hose` | Durchtrennter Löschschlauch | Der Feuerkasten steht offen, der Schlauch ist durchgeschnitten – glatt, nicht gerissen. Wer das Feuer gelegt hat, kannte das Haus. | physical_clue | RegistryD |
| `ev_c3_escort_list` | Begleitliste, Dienstag 23.40 | Die Akte ist an der Bindung auseinandergebrochen. Obenauf die Liste der nächsten Sonderfahrt, Dienstag, 23.40 Uhr: Spalte „Tür West“, Spalte „Tür Ost“. Tür Ost, dritte Zeile: Iljin, P. A., geb. 1935. | document | Quay |
Document art (inspect close-ups, `assets/ui/documents/veltrava_registry_*`, `veltrava_quay_*`, owner registry art /
quay art): legible are only the story-critical figures — weighbill-style. Intake book page (three column heads
DE/RU/FR): rows `7.1. · West · C-17/B-11 · Berlin` (scribble), `14.1. · Ost · C-17/41 · Karsk`, `21.1. · Ost ·
C-17/42 · Karsk`, `28.1. · Ost · C-17/43 · Karsk` (these three legible, remark „weitergeleitet: Kordon-17,
Erfassungsraum“), `4.2. · West · C-17/B-12 · Berlin` (scribble), `11.2. · Ost · C-17/44 · Wagen 4 · 2410 kg ·
„Akten“ · 9.52` and its Ausgang `23.40 · Gleis 5 · „Begleitgut, 14 Stück“` with the Russian column „14 лиц“ (all
legible, the C-17 red accent on the two 11.2. lines). Blatt 7: plan with the Line drawn through the room, two doors
(„Halle West“, „Halle Ost“), the counter in the middle, two benches drawn in a different ink („Rev. c“), title block
„Anlage C · Blatt 7 · Kordon-17 · Erfassungsraum · gez. K. A.“. The night book: two lines in two hands.

### 2.6 Flags and events
No new flags (§1.1). Events appended before `slice_completed`: `c3c_completed`, `c3d_completed`, `c3e_completed`,
`c3f_completed`, `c3g_completed`. Meters written: `alexei_konrad_trust` (admit_plan, swap_halves), `evidence_chain`
(pocket_plan, split_by_language), `elena_trust` (hide_for_elena). No combined morality score.

### 2.7 Puzzle `pz_c3_check` „Gegenprobe“ (type `symbol_order` — the engine has no other list type)
* Board (UI, next phase): a table with four FIXED rows — Alexei's freight chain, in this order — and one empty slot
  per row; the tray holds four cards (entries of the registry/Konrad's protocol) in display order. The player puts
  the matching card into each row's slot; the answer is the card order top→bottom.
* Rows (fixed): 1 `ev_c3_weighbill` „Wiegekarte · Plombe C-17/44 · 2410 kg“ · 2 `ev_c3_departures` „Abfahrtstafel ·
  Sonderfahrt 23.40 · Gleis 5 · Leerfahrt“ · 3 `ev_c3_travel_order` „Reiseauftrag · Begleitperson Kurierwagen 4“ ·
  4 `ev_timetable` „Dienstfahrplan Karsk · drei Wagen ohne Zielbahnhof“.
* Cards: `in_c17_44` „Eingang 11.2., 9.52 Uhr: Wagen 4, Plombe C-17/44, 2410 kg ‚Akten‘“ · `out_2340` „Ausgang
  11.2., 23.40 Uhr, Gleis 5: ‚Begleitgut, 14 Stück‘ – russisch: 14 Personen“ · `par_4` „Anlage C, § 4 (Text des
  Sekretariats): DE ‚Begleitgut‘ – RU ‚begleitete Personen‘“ · `january` „Eingänge 14., 21., 28.1.: drei Wagen aus
  Karsk, C-17/41 bis /43 – weitergeleitet: Kordon-17, Erfassungsraum“.
* `display_symbols` `["out_2340", "january", "in_c17_44", "par_4"]`; **solution `["in_c17_44", "out_2340",
  "par_4", "january"]`**; `clue_item_ids` `["ev_c3_halves", "ev_c3_intake_book"]`; hint after 2 failures;
  unlimited retries; no penalty. Each pair has exactly one shared fact: seal + weight · 23.40 + Gleis 5 · the word
  „Begleit-“ (Elena's margin note) · three January wagons.
* Hint (de): „Lies Alexeis Zeilen einzeln und such im Eingangsbuch dieselbe Zahl: Plombe, Uhrzeit, Anzahl der Wagen.
  Für den Reiseauftrag hilft Elenas Randnotiz zu Paragraph vier.“
* Success (de): „Jede Fahrt hat zwei Papiere. Auf der Waage steht Akten, in der Registratur Begleitgut, in der
  russischen Spalte Personen. Und alle Wege enden am selben Ort: Kordon-17, Erfassungsraum.“
* UI texts (`data/locale/de_c3p2_ui.json`, `ui.c3p2.check.*`): title „Gegenprobe“, subtitle „Eingangsbuch Serie C-17
  gegen Alexeis Frachtkette – fiktive Akten, keine echten Dokumente“, instruction, row labels, card texts, wrong,
  incomplete, hint, success, buttons (same words as the protocol puzzle: Prüfen · Rückgängig · Neu ordnen · Schließen).
* UI scene `res://scenes/ui/CheckPuzzle.tscn` (script `scripts/ui/check_puzzle.gd`, registered in c3.json
  `puzzles`). Key contract (= ProtocolPuzzle, the input driver relies on it): property `is_open`, property
  `symbols` (tray in display order), number key n places the n-th tray card into the next empty row, Backspace undoes
  the last card, Enter checks (submits through `Story.solve_puzzle`), Esc closes; the first two failures keep the
  board, the hint appears after `hint_after_attempts`. Rows show a thumbnail of the item (InspectView art).

### 2.8 Dialogues (linear; node ids globally unique; speaker ids in parentheses; ≤ 140 characters per line)
Variant notation: `· v <condition>: „…“` — first match wins (§3). `choice.c3b = report_delegation` means
`{"choice.c3b_choose": "report_delegation"}`. Base lines marked *(fallback-only)* are heard only on a level start
without a save (C3_DESIGN §2.8, Befund 23).

`dlg_c3c_night` (entry `c3c_night_01`) — the card hall, Konrad with a torch:
1. `c3c_night_01` (konrad) „Stehen bleiben. – Ach. Sie sind es.“ · v choice.c3b = share_protocol: „Morozov. Gut. Ich hatte gehofft, dass der Zettel auch bei Ihnen lag.“ · v choice.c3b = report_delegation: „Stehen bleiben. – Morozov. Ausgerechnet.“
2. `c3c_night_02` (alexei) „Sie haben auch einen Zettel bekommen.“
3. `c3c_night_03` (konrad) „Unter der Tür, kurz nach Mitternacht. Deutsch geschrieben, mit einem E darunter.“
4. `c3c_night_04` (alexei) „Meiner war russisch. Dieselbe Hand.“ *(fallback-only)* · v choice.c3a = ask_elena: „Meiner war russisch, dieselbe Hand. Ins Café ist sie nicht gekommen. Ich habe bis zur Sperrstunde gewartet.“ · v choice.c3a = note_alone: „Meiner war russisch, dieselbe Hand. Heute früh wollte ich allein suchen. Jetzt schreibt sie mir.“
5. `c3c_night_05` (konrad) „Sie ist nicht hier. Die Pforte ist leer, das Licht brannte schon, als ich kam.“ · v choice.c3b = search_elena: „Sie ist nicht hier. Ich habe den ganzen Abend nach ihr gefragt. Im Palais weiß niemand etwas. Oder sagt es.“
6. `c3c_night_06` (alexei) „Im Nachtbuch steht ihr Name, 23.10 Uhr. Um 23.25 Uhr hat jemand für sie ‚ab‘ geschrieben. Mit einem anderen Stift.“
7. `c3c_night_07` (konrad) „Und die Kisten draußen an der Rampe?“
8. `c3c_night_08` (alexei) „Aus Wagen vier. Leer, die Plombe durchtrennt. Was drin war, liegt jetzt hier.“
9. `c3c_night_09` (konrad) „Die Registratur ist das Sekretariat. Jedes Blatt der Kommission kommt durch dieses Haus.“
10. `c3c_night_10` (alexei) „Und Sie? Was suchen Sie hier, Adler?“
11. `c3c_night_11` (konrad) „Wer den Text von Paragraph vier geliefert hat. Und was aus meinen Zeichnungen wurde.“ *(fallback-only)* · v konrad_evidence ≥ 1: „Wer Paragraph vier geliefert hat. Ob Emils Bauserie hier eine Akte hat. Und was aus meinen Zeichnungen wurde.“ · v office_suspicion ≥ 1: „Wer Paragraph vier geliefert hat – in Berlin bekam ich keine Antwort. Und was aus meinen Zeichnungen wurde.“
12. `c3c_night_12` (alexei) „Wo meine Wagen hinfahren. – Sie haben Licht, ich habe Papiere. Fangen wir an.“
13. `c3c_night_13` (konrad, end) „Am Sortiertisch. Fassen Sie nichts an, was Sie nicht genau so zurücklegen können.“ · v choice.c3b = report_delegation: „Am Sortiertisch. Und Morozov: Ich habe Sie heute gemeldet. Das sollten Sie wissen, bevor wir anfangen.“

`dlg_c3d_compare` (entry `c3d_cmp_01`; grants `ev_c3_halves` at the end):
1. `c3d_cmp_01` (alexei) „Sie zuerst.“
2. `c3d_cmp_02` (konrad) „Warum ich?“
3. `c3d_cmp_03` (alexei) „Weil Sie das Licht halten.“ · v choice.c3b = share_protocol: „Weil Sie heute Morgen angefangen haben. Elenas Notiz. Wer einmal anfängt, fängt leichter wieder an.“ · v choice.c3b = report_delegation: „Weil Sie mich heute gemeldet haben. Wer meldet, legt zuerst.“
4. `c3d_cmp_04` (konrad) „Sitzordnung, Dolmetscherprotokoll, die Durchschrift aus Kabine zwei.“ *(fallback-only)* · v konrad_evidence ≥ 1: „Sitzordnung, Protokoll, Durchschrift. Und Emils Abschrift aus Berlin: C-17 ist dort eine Bauserie.“ · v office_suspicion ≥ 1: „Sitzordnung, Protokoll, Durchschrift. Mehr nicht – wer in Berlin offiziell fragt, bekommt keine Abschriften.“
5. `c3d_cmp_05` (alexei) „Wiegekarte, Abfahrtstafel, mein Reiseauftrag. Und der Dienstfahrplan aus Karsk.“ *(fallback-only)* · v irina_trust ≥ 1: „Wiegekarte, Abfahrtstafel, Reiseauftrag. Und der Dienstfahrplan aus Karsk – Irina hat ihn mir abgeschrieben.“ · v alexei_secrecy ≥ 1: „Wiegekarte, Abfahrtstafel, Reiseauftrag. Den Dienstfahrplan aus Karsk habe ich selbst abgeschrieben. Heimlich.“
6. `c3d_cmp_06` (konrad) „Dazu das Eingangsbuch. Drei Spalten, Deutsch, Russisch, Französisch – und jede Zeile hat eine Nummer.“
7. `c3d_cmp_07` (alexei, end) „Dann Zeile für Zeile. Ihr Papier gegen meins.“

`dlg_c3d_partner` (entry `c3d_par_01`) — after Blatt 7; the realisation:
1. `c3d_par_01` (konrad) „Blatt sieben. Kordon-17, Erfassungsraum. Ein Raum genau auf der Linie.“
2. `c3d_par_02` (alexei) „Zwei Türen. Eine zu Ihrer Halle, eine zu unserer. Und dazwischen ein Schalter.“
3. `c3d_par_03` (konrad) „Ein Durchgabeschalter. Für Karteikästen – so steht es in der Legende.“
4. `c3d_par_04` (alexei) „Und eine Bank mit vierzehn Plätzen. Karteikästen sitzen nicht.“
5. `c3d_par_05` (konrad) „Revision c. Die Bank ist nachgetragen, mit anderer Tusche.“
6. `c3d_par_06` (alexei) „Ich dachte, Ihre Leute holen unsere Wagen.“ · v choice.c3b = report_delegation: „Ich dachte, Ihre Leute holen unsere Wagen. Dass Sie mich heute gemeldet haben, passte gut dazu.“
7. `c3d_par_07` (konrad) „Und ich dachte, Ihre Leute wollen unsere Korridore.“
8. `c3d_par_08` (alexei) „Sie tauschen. Mal von Ihrer Seite, mal von unserer – so hat es der Schaffner gesagt.“
9. `c3d_par_09` (konrad) „Dann ist der Vertragspartner nicht Ihr Land. Es sind die Ämter, die bei Ihnen und bei uns die Listen führen.“
10. `c3d_par_10` (alexei) „Bei uns heißt das Amt Transportabteilung. Wer über sie zurückkommt, kommt nicht nach Hause.“
11. `c3d_par_11` (konrad) „Bei uns heißt es Erfassungsstelle. Was nach der Erfassung kommt, nennt bei uns keiner beim Namen. Ich auch nicht.“ · v office_suspicion ≥ 1: „Bei uns heißt es Erfassungsstelle. Was danach kommt, nennt keiner beim Namen. Ich habe einmal danach gefragt. Einmal.“
12. `c3d_par_12` (alexei, end) „Wer zeichnet so einen Raum, Adler?“
Lines 10/11 keep the asymmetry explicit: two different apparatuses, two different fates, no equation.

`dlg_c3e_smoke` (entry `c3e_smk_01`) — at the porter's booth, the 1909 Kurhaus plan:
1. `c3e_smk_01` (alexei) „Die Rampe ist zu. Von außen verriegelt.“
2. `c3e_smk_02` (konrad) „Hier – der alte Kurhausplan, 1909. Souterrain: Kohlenkeller. Eine Schütte führt in den Wirtschaftshof.“
3. `c3e_smk_03` (alexei) „Die Eisentür hinter dem Pult. Mit der Jahreszahl.“
4. `c3e_smk_04` (konrad) „Das Pult ist aus Eiche. Allein bewegt das keiner von uns.“
5. `c3e_smk_05` (alexei) „Dann nicht allein. Nehmen Sie die Akte – ich brauche die Hände.“
6. `c3e_smk_06` (konrad, end) „Blatt sieben hängt noch an der Wand. – Soll es brennen.“ · v choice.c3d = pocket_plan: „Die Akte. Gut. – Gehen wir.“

`dlg_c3f_desk` (entry `c3f_dsk_01`):
1. `c3f_dsk_01` (alexei) „Auf drei. Sie drücken, ich ziehe.“
2. `c3f_dsk_02` (konrad) „Ich zeichne Pulte, Morozov. Ich schiebe sie nicht.“ · v alexei_konrad_trust ≥ 2: „Ich zeichne Pulte, Morozov. Aber für Sie schiebe ich eins.“
3. `c3f_dsk_03` (alexei) „Heute schon. Eins, zwei –“
4. `c3f_dsk_04` (konrad, end) „Drei!“

`dlg_c3f_chute` (entry `c3f_cht_01`) — Alexei holds the iron door:
1. `c3f_cht_01` (alexei) „Die Tür klemmt. Ich halte sie. Erst die Akte, dann Sie.“
2. `c3f_cht_02` (konrad) „Und wer hält die Tür, wenn Sie als Letzter gehen?“ · v alexei_konrad_trust == 0: „Und wenn ich oben bin – woher wissen Sie, dass ich Ihnen die Hand gebe?“
3. `c3f_cht_03` (alexei) „Niemand. Deshalb gehe ich als Letzter.“ · v alexei_konrad_trust == 0: „Ich weiß es nicht. Deshalb gehen Sie zuerst.“
4. `c3f_cht_04` (konrad) „Das ist keine Ingenieurslösung.“ · v alexei_konrad_trust == 0: „Das ist keine Antwort.“
5. `c3f_cht_05` (alexei, end) „Doch. Eine aus Karsk. – Los, Adler!“ · v alexei_konrad_trust == 0: „Doch. Die einzige, die ich habe. – Los!“

`dlg_c3g_snow` (entry `c3g_snw_01`) — on the quay, the file in two halves:
1. `c3g_snw_01` (konrad) „Die Bindung ist durchgebrannt. Die Akte fällt von selbst auseinander.“
2. `c3g_snw_02` (alexei) „Deutsche Blätter, russische Blätter. Wie bestellt.“
3. `c3g_snw_03` (konrad) „Sie lesen die russische Spalte seit einer Minute. Was steht da?“
4. `c3g_snw_04` (alexei) „Dritte Zeile. Iljin, Pjotr Andrejewitsch. Als Kinder haben wir Kopeken auf die Gleise in Karsk gelegt.“
5. `c3g_snw_05` (konrad) „Er steht auf der Liste für Dienstag.“
6. `c3g_snw_06` (alexei) „1957 ist er über die Linie gegangen. Seitdem lebt er hier, in Veltrava. Dachte ich.“ · v alexei_secrecy ≥ 1: „1957 ist er über die Linie gegangen. In Karsk weiß keiner, dass wir Freunde waren. Jetzt wissen Sie es.“
7. `c3g_snw_07` (konrad) „In der deutschen Spalte stehen auch Namen. Ich kenne keinen davon. Noch nicht.“
8. `c3g_snw_08` (alexei) „Vierzehn Stück um 23.40 Uhr. Um 23.25 Uhr hat jemand für Elena ‚ab‘ geschrieben.“
9. `c3g_snw_09` (konrad) „Sie glauben, sie saß in dem Zug.“
10. `c3g_snw_10` (alexei) „Ich glaube nichts mehr, was auf einem Papier steht. Nur noch, was zwei Papiere zusammen sagen.“
11. `c3g_snw_11` (konrad) „Gleich durchsuchen die Wachen jeden mit Ruß im Gesicht. Mit der ganzen Akte kommen wir nicht weit.“ · v choice.c3b = report_delegation: „Kessler steht da drüben bei den Wagen. Ich habe ihn heute geholt. Mit der ganzen Akte komme ich an ihm nicht vorbei.“
12. `c3g_snw_12` (alexei, end) „Dann teilen wir sie.“

Expressions (`line_expr`): neutral unless listed — concerned: c3c_night_01/05/06, c3d_par_04/06/10/11, c3e_smk_01/04,
c3f_cht_02, c3g_snw_04/05/08/09; determined: c3c_night_12, c3d_cmp_07, c3d_par_09/12, c3e_smk_05/06, c3f_dsk_03/04,
c3f_cht_01/05, c3g_snw_10/12; surprised: c3c_night_02, c3d_par_05, c3g_snw_03.

### 2.9 Cinematics (data/v3/cinematics.json; `LOCKED_CINEMATICS` extended — validator list only)
| id | trigger | skip | shots (duration) | scene (cinematics stream) |
|---|---|---|---|---|
| `LS_C3_Radio` | event `c3b_completed` (after `LS_C3_Close`) | visual_only | r1 station square at night, two hotels face each other across the snow (Hotel Nord — Soviet delegation, Hotel Europa — German), steam of the 23.40 train drifting off; interval signal of Radio Veltrava (4 s) · r2 Alexei's room: Bakelite radio, tea glass, the Russian news (6 s) · r3 match cut on the tuning dial → Konrad's room, same radio model, the German news; his pencil stops (6 s) · r4 two doors side by side (split): a folded note slides under each; close-up of the note in two languages (5 s) · r5 Café „Korridor“: chairs on the tables, Elena's table, an untouched glass; station clock 0.10 (4 s) · r6 two hotel doors open at once; two men in the snow, their tracks converge on the dark east wing of the palais (4 s) — ≈ 29 s | `res://scenes/cinematics/ch3_radio/Ch3Radio.tscn` |
| `LS_C3_Fire` | event `c3d_completed` | visual_only | f1 the green lamp flickers over the sorting table; a smell; Konrad looks up (3 s) · f2 the stacks: an orange glow between the shelves, the C-17 boxes catch; a figure in a long coat and a porter's cap slips out through the service door — face never shown (3 s) · f3 the ramp door from inside: a shadow outside, the iron bolt slides home (sound + bolt shadow) (2.5 s) · f4 fire runs along the old shelves, smoke rolls under the ceiling toward the camera; Alexei stands at the table (3.5 s) — ≈ 12 s | `res://scenes/cinematics/ch3_fire/Ch3Fire.tscn` |
| `LS_C3_Escape` | event `c3f_completed` | visual_only | e1 inside the chute: coal dust, the file pushed up toward a square of snow light (4 s) · e2 the yard: the iron hatch flips open, Konrad crawls out with the file, smoke pours after him (4 s) · e3 Alexei's hand; Konrad pulls him out; the hatch slams; both on their backs in the snow, coughing (4 s) · e4 the east wing: souterrain windows burst orange, fire-brigade bells, snow falling through smoke (4 s) — ≈ 16 s | `res://scenes/cinematics/ch3_escape/Ch3Escape.tscn` |
| `LS_C3_Halves` | event `c3g_completed` | visual_only | h1 the quay bench: each man takes his half (which pages per `ctx.choices.c3g_choose`; hide_for_elena: Konrad folds the list into his coat to carry it to the cloakroom) (6 s) · h2 they walk apart along the quay, Alexei east toward the station, Konrad west toward the palais (5 s) · h3 wide: the burning wing mirrored in the river ice, the Line's searchlights on the far bank, first grey of dawn (6 s) · h4 the departures board at the station, a fresh line: „Dienstag · 23.40 · Kordon-17 · Gleis 5“ (4 s) — ≈ 21 s | `res://scenes/cinematics/ch3_halves/Ch3Halves.tscn` |
Inner lines and captions (`data/locale/de_c3p2_cinematics.json`, chosen from `configure(ctx)` choices/flags):
`cin.c3p2.radio.time` „Veltrava, 0.10 Uhr.“ · `cin.c3p2.radio.ru` „(Radio Veltrava, russisch) …hat die Kommission
Anlage C angenommen. Der Verkehr von Gütern und begleiteten Personen über die Linie…“ · `cin.c3p2.radio.de` „(Radio
Veltrava) …hat die Kommission Anlage C angenommen. Güter und Begleitgut passieren die Linie ab März ohne Aufenthalt.“
· `cin.c3p2.radio.note` „Registratur. Hof, Rampe. 0.30 Uhr. – E.“ · Alexei: `…alexei.base` „Begleitete Personen.
Auf Deutsch sagen sie es anders.“, `…alexei.cafe` (c3a ask_elena) „Ins Café ist sie nicht gekommen. Ich habe zwei
Gläser Tee bezahlt.“, `…alexei.alone` (c3a note_alone) „Ich wollte allein suchen. Jetzt schreibt sie mir.“ · Konrad:
`…konrad.base` „Begleitgut. Das Wort habe ich heute dreimal gehört.“, `…konrad.share` (share_protocol) „Ich habe ihm
Elenas Notiz gezeigt, er mir einen Zug. Jetzt schreibt sie uns beiden.“, `…konrad.search` (search_elena) „Ihr Mantel
hing noch in der Garderobe, als ich ging. Marke 27.“, `…konrad.report` (report_delegation) „Kessler hat zugehört
und genickt. Sonst nichts.“ · `cin.c3p2.fire.time` „1.40 Uhr.“ · `cin.c3p2.halves.split` „Jeder trägt seine
Sprache nach Hause – und die Namen, die darin stehen.“ · `…halves.swap` „Er trägt Pjotrs Namen über seine Grenze.
Ich trage seine Leute über meine.“ · `…halves.elena` „Die Liste steckt in einem Mantel, Marke 27. Wenn sie
zurückkommt, findet sie sie.“ · `…halves.plan_kept` (c3d pocket_plan) „In meiner Manteltasche: Blatt sieben.
Gezeichnet K. Adler.“ · `…halves.plan_burnt` (c3d admit_plan) „Blatt sieben ist verbrannt. Gezeichnet habe ich ihn
trotzdem.“ · `…halves.tuesday` „Dienstag, 23.40 Uhr. Gleis 5.“
Rules (§12.5 + C3 cinematic base): every frame a pure function of t, `skip()` idempotent, reduced_motion halves
travel and softens the fire flashes (no strobing: fire flicker ≤ 3 Hz, never full-screen white), no gore, no
injury shown, the arsonist never identifiable.

---------------------------------------------------------------------------------------------------------
## 3. Presentation layer — `data/chapters/c3.json` + `scripts/core/chapter_ext.gd`
### 3.1 New entries in c3.json
`levels`: the four registry scenes → `res://scenes/levels/L_C3_Registry.tscn`, `L_C3_Quay` →
`res://scenes/levels/L_C3_Quay.tscn` · `entry_spawn` per scene (§2.1) · `chapter_cards`: only `L_C3_RegistryA`
[`ui.chapter_c3`, `world.c3c.title`] and `L_C3_Quay` [`ui.chapter_c3`, `world.c3g.title`] (a switch shows none) ·
`palettes.registry` · `grades.registry`, `grades.registry_fire`, `grades.quay` · `switches` (§4) · `line_expr`,
`line_variants`, `choice_text`, `reactions` (§2.4/§2.8) · `puzzles` {`c3d_solve_check`:
`res://scenes/ui/CheckPuzzle.tscn`} · `cinematics` (§2.9 paths). Variant texts: `data/locale/de_c3p2_dialogue.json`;
cinematic lines `de_c3p2_cinematics.json`; puzzle UI, memories and misc. texts `de_c3p2_ui.json`.
### 3.2 ChapterExt additions (data-driven only)
* Condition keys `choice.<objective_id>` compare with the recorded choice id (`{"choice.c3b_choose":
  "report_delegation"}`); a flags dictionary may carry them, otherwise the live `Story.choice_history()` answers.
  Unchosen = "" (never equal to an option id).
* `level_key(scene_id) -> String` (the FIRST scene id that maps to the same level file — the identity of a shared
  level for Explore entries and the drivers' exploration passes), `same_level(a, b) -> bool`,
  `scenes_of_level(path) -> Array`. (`switches` / `switch_settings()` / `switch_spawn()` belong to the engine stream,
  TECHNICAL_ARCHITECTURE §12.11.)

---------------------------------------------------------------------------------------------------------
## 4. In-level protagonist switch — data side (mechanics: TECHNICAL_ARCHITECTURE §12.11, engine stream)
* Scene ↔ level file: c3.json `levels` maps `L_C3_RegistryA`–`D` to `res://scenes/levels/L_C3_Registry.tscn`
  (`level_id = "L_C3_RegistryA"`, `protagonist = "alexei"` in the file; Game adopts the running scene's id and
  protagonist). No protagonist is authored as an NPC in the shell: the partner comes from the settings below.
* c3.json `switches` (keys of §12.11; `grade` is this contract's addition — see the integration notes):
  ```json
  "L_C3_RegistryA": {"partner": "konrad", "partner_spawn": "SP_C3_KonradCards"},
  "L_C3_RegistryB": {"partner_spawn": "SP_C3_AlexeiTable"},
  "L_C3_RegistryC": {"partner_spawn": "SP_C3_KonradBooth", "ambience": "amb_veltrava_fire", "grade": "registry_fire"},
  "L_C3_RegistryD": {"partner_spawn": "SP_C3_AlexeiChute", "ambience": "amb_veltrava_fire", "grade": "registry_fire"}
  ```
  A: Konrad stands among the card cabinets while Alexei arrives. B: control passes to Konrad where he stood (the
  default `switch_spawn` rule = seamless); Alexei walks to the sorting table. C: after `LS_C3_Fire` control passes to
  Alexei at the table; Konrad hurries to the porter's booth (the 1909 plan). D: control passes to Konrad at the booth;
  Alexei goes to the chute door. Each scene's `entry_spawn` (fresh loads, memories) is the spot where its protagonist
  stood as partner in the scene before (A: the gate). The dialogue/choice hotspots of a scene sit next to the
  partner spot (A–C: 18 px to its left, the palais' NPC convention; D: the desk and the chute door just right of
  Alexei); `npc_id` of those interactables = the partner.
* `LS_C3_Fire` plays between B and C (its trigger moved the story to `L_C3_RegistryC`, a scene of the SAME file):
  the director shows the registry again and switches with a cut (§12.11 `switch_cuts()`).
* Saves in B/C/D restore the controlled character and the partner (§12.11 saves/loads). Each registry scene is its
  own memory and opens with its own protagonist.
* Gated walls (engine + registry art): `scene.json` `"blockers": [{"name", "rect": [x, y, w, h], "after"?:
  objective, "until"?: objective}]` → a StaticBody2D rectangle enabled while the condition holds. Registry:
  `ramp_bolted` [384, 280, 12, 40] after `c3d_choose` · `fire_c` [1236, 270, 24, 60] after `c3d_choose` ·
  `fire_d` [690, 270, 24, 60] after `c3e_reach_konrad`. Same `after`/`until` keys on `layers`, `decals`, `lights`,
  `fx` give the two looks of the level (night → fire). Until the engine honours them nothing is blocked (the
  drivers do not need them).

---------------------------------------------------------------------------------------------------------
## 5. Levels and hotspots (art ↔ content contract)
### 5.1 `L_C3_Registry` — env `assets/environments/veltrava_registry/` (side view like the palais, 1920×360)
The commission's registry in the souterrain of the palais' east wing (the former Kurhaus' coal and boiler cellar,
converted 1963). Night. Walk band y 296–306, feet y 300. Rooms left → right:
* 0–380 **Wirtschaftshof** (exterior): snow falling, one bracket lamp, the iron gate to the lane (x 0–60), the
  emptied crates of courier wagon 4 on a handcart (x 200–270, seal wire dangling, the red C-17 tag), the iron
  coal-chute hatch in the ground against the wall (x 320–350, cast „1909“), the ramp and the iron-clad **ramp door**
  (x 370–400). Behind: the palais wall, dark windows, one lit window high up; snow on the cornice.
* 380–680 **Annahme**: in the back wall the small iron **chute door** (x 435–465, „1909“), the oak **intake desk**
  in front of it (x 480–530, the intake book open under a lamp), the red **fire case** with glass front, hose and
  axe (x 550–575, trilingual sign „Bei Feuer Scheibe einschlagen / При пожаре разбить стекло / En cas d'incendie“),
  the glazed **porter's booth** (x 590–680: key board, night book, a Bakelite radio playing low, an empty coat hook,
  the framed 1909 Kurhaus plan).
* 680–1260 **Karteisaal**: the sand/water fire bucket stand (x 700), rows of tall oak card cabinets with brass label
  holders (x 740–1240), a sliding ladder, the **sorting table** under a green-shaded lamp (x 940–1060), drawer
  „C-17“ half open with a chair and Elena's wine-red scarf (x 1090–1120); high souterrain windows at the top edge
  with snow and the feet of a passing guard (life strip).
* 1260–1560 **Planarchiv**: flat plan chests, the wall of framed Annex C sheets; **Blatt 7** at x ≈ 1340 (its frame
  slightly askew, lighter rectangle on the wall paint where it hung before).
* 1560–1920 **Magazin**: compact shelving, the C-17 shelf (x ≈ 1700, where the fire starts), the barred door to the
  palais service stairs (x ≈ 1890).
Two looks: **night** (A/B: cold blue snow light through the high windows, warm pools of the green lamp and the booth
lamp, deep shadow between the cabinets) and **fire** (C/D, `after: c3d_choose`: orange glow from the right, smoke
layer under the ceiling that grows lower toward x 0 in D, embers, sparks, a burning fallen frame in the Planarchiv,
the ramp door shut with snow blowing through the gap; `fire_d` look `after: c3e_reach_konrad` puts fire into the
Karteisaal). FX: snow (yard), dust motes (lamps), smoke, embers (≤ 3 Hz flicker), heat shimmer at the fire front.
Story hotspots (x, 300): `crates` 232 · `ramp_door` 398 · `alexei_chute` 440 · `chute_door` 476 · `intake_desk`
505 · `fire_case` 560 · `porter_booth` 612 · `konrad_booth` 640 · `konrad_cards` 880 · `alexei_table` 950 ·
`sorting_table` 1012 · `drawer_c17` 1104 · `plan_wall` 1340.
Spawns (feet): `SP_C3_Gate` (44, 300) · partner / entry spots `SP_C3_KonradCards` (898, 300) · `SP_C3_AlexeiTable`
(968, 300) · `SP_C3_KonradBooth` (658, 300) · `SP_C3_AlexeiChute` (458, 300).
Exploration hotspots (explore stream, `explore_hotspots.json`): keep ≥ 24 px from the story hotspots above; yard
and Annahme finds at x < 680, card-hall finds 690–1230, Planarchiv 1270–1540, Magazin 1580–1880.

### 5.2 `L_C3_Quay` — env `assets/environments/veltrava_quay/` (side view, 1920×360)
Before dawn (≈ 2.20 Uhr), the riverside quay behind the palais. Walk band y 296–306. Left → right:
* 0–420 the corner of the burning east wing beyond the yard wall: orange souterrain windows, smoke columns, the
  coal hatch they came out of (x ≈ 170); the fire brigade's ladder engine (x 250–420, red, Veltrava bridge arms on the
  door), hoses across the snow, firemen (life strips, no faces needed).
* 420–1100 the **quay promenade**: lanterns, snowed-in benches; the stone balustrade in the foreground; beyond it the
  frozen river and, far away, the Line on the other bank — watchtowers and two searchlights sweeping the ice (slow,
  ≥ 6 s per sweep). The **bench** with the broken file at x ≈ 760; Konrad beside it.
* 1100–1520 the two black delegation cars with pennants (USSR / Reich neutral + `_hist`), Kessler and Voronova
  standing apart, each alone with an aide (life strips), a commission guard holding back onlookers.
* 1520–1920 the approach to the three-arch bridge of the city arms, tram stop, the old town's dark roofs; Nils
  Ekdahl with his camera.
Story hotspots: `bench` 760 · `konrad_quay` 800 · NPC anchors `typist_quay` 330 · `guard_quay` 1050 ·
`kessler_quay` 1180 · `voronova_quay` 1330 · `journalist_quay` 1560. Spawn `SP_C3_Quay` (560, 300).
Grade `quay`: cold blue night, warm only from the fire (left) and the lanterns; snow FX; smoke drifting right.

---------------------------------------------------------------------------------------------------------
## 6. Characters (existing ids only)
`alexei`, `konrad` (both protagonists; nice-to-have from the characters stream: a soot overlay/palette for the fire
scenes and the quay, a `carry_side` row with the file), `kessler`, `voronova`, `journalist` (Nils Ekdahl),
`typist` (Frau Brunner, coat over her nightdress), `border_officer` (as commission guard at the quay). `elena`
appears only in absence (scarf, note, empty café table). No new character is needed; firemen and the guard's feet
are life strips. The night porter is never seen (his coat is gone).

## 7. Exploration brief (§12, §12.9, §12.8) — owner: exploration stream
Files `data/explore/veltrava_registry.json`, `veltrava_quay.json` (area `veltrava`, ids `veltrava.registry.<name>`,
`veltrava.quay.<name>`), strings `data/locale/de_explore_veltrava_p2.json`. **Explore entries of the shared level use
`"level": "L_C3_RegistryA"`** (ChapterExt.level_key). Finds speak in the voice of the protagonist who can reach
them: registry finds are `gated_interactable`s — yard/Annahme finds `until_objective = c3c_talk_konrad` (Alexei),
card hall/Planarchiv finds `after_objective = c3c_talk_konrad`, `until_objective = c3d_choose` (Konrad); none during
the fire.
* Registry, Alexei (A): `exp_gate_sign` trilingual sign „Anlieferung nur werktags“ · `exp_handcart` · `exp_hatch`
  the 1909 coal hatch (Alexei notes the hinge: „Wer die geölt hat, wollte sie benutzen.“) · `exp_radio` the porter's
  radio, Radio Veltrava's night waltz · `exp_thermos` still warm · `exp_key_board` one hook empty („Magazin“) ·
  `exp_card_alexei` his own index card („Morozov, A. – Begleitperson – Wagen 4“) · hidden `exp_two_tracks` two
  sets of footprints in the yard snow, one small.
* Registry, Konrad (B): `exp_card_konrad` his own card („Adler, K. – Zeichner – Bemerkung: ‚Anfrage Berlin‘“ only
  as written, no flag text) · `exp_tube` the commission's pneumatic-tube station · `exp_stamps` stamp rack with the
  bridge counter-seal and the seal pliers „Zange 7“ · `exp_ladder` · `exp_plan_chests` · `exp_window_feet` ·
  `exp_kurhaus_plaque` „Kurhaus Veltrava 1909 – Kesselhaus“.
* Quay (Alexei): `exp_fire_engine` · `exp_ice` · `exp_searchlights` · `exp_bridge_arms` · `exp_cars` (two cars,
  two pennants, two drivers sharing one cigarette lighter — a human beat, never a symmetry statement) · `exp_lantern`
  · hidden `exp_soot_print` · chats at `typist_quay` (Frau Brunner: thirty years of files) and `journalist_quay`
  (Ekdahl: „Ein Feuer in der Registratur, in der Nacht nach Anlage C. Das schreibe ich nicht. Das schreibt sich
  selbst.“); a tense optional chat at `voronova_quay` (his deputy minister sees the soot on his sleeve).
* Real-history cards (sober, sourced, 450–800 characters, fact-checked like C3): `hist.reich.census_1939` — the
  May-1939 census and its „Ergänzungskarte“ on descent, used to register Jews (G. Aly / K. H. Roth, „Die restlose
  Erfassung“, 1984) — at `exp_card_konrad` (B); `hist.soviet.filtration` — NKVD filtration of returning POWs and
  forced labourers 1945–46, many sent on to camps (P. Polian, „Deportiert nach Hause“, 2001) — at `exp_card_alexei`
  (A). Never on a joke spot.
* Side tasks (one per new level): registry „Die Pforte“ (A: the empty booth, the thermos → the radio → the key board →
  back to the night book: the porter was sent away „by a man from the secretariat“ with a ten-franc note — Alexei's
  voice); quay „Eine Decke für Frau Brunner“ (the typist shivers → a blanket from the fire engine → back).
* Optional mini-game ideas (§12.8, minigames stream): registry „Die Kartei“ — a dropped drawer of index cards
  re-sorted by the commission's three-part code (origin · year · number), Cyrillic and Latin labels interleaved;
  quay „Die Kupplung“ — help the firemen couple two hose lines whose couplings come from different standards (Soviet
  and German): find the adapter piece and the right turn; no timer, no failure state beyond retry.

## 8. Audio brief (optional stream)
`amb_veltrava_registry` (souterrain night: distant city, radiator ticks, the porter's radio low), `amb_veltrava_fire`
(roar, crackle, glass, beams, muffled bells — mixed so dialogue stays clear), `amb_veltrava_quay` (fire far left,
bells, river ice creak, wind); radio programme for `LS_C3_Radio` (original interval signal + newsreader murmur,
no real broadcast). Missing files are tolerated by `Audio` (graceful).

## 9. Tests and drivers
* `tests/test_c3p2_routes.gd`: every choice combination through the Story API (a1 × m1 × c3a × c3b × c3d × c3g =
  144 routes): chain, protagonists, events, meters, items, cinematic order, finale; locks; save/load in every new
  scene; puzzle validation; data contract (ids, texts, items, hotspots/spawns of the shells, switches, variants).
* `tests/reference/make_python_reference.py` routes cover all six choices × skip/play; `tests/support/test_kit.gd`
  plays the extended chain; tests encoding the old chain get minimal edits.
* Drivers: `--autoplay=<a1>,<m1>,<c3a>,<c3b>,<c3d>,<c3g>` and `--inputplay=…` (same spec); both run their saves in
  `user://e2e/saves` (never the player's slots); inputplay solves `CheckPuzzle` with number keys (one wrong order
  first) and checks that „Fortsetzen“ resumes on the quay before `c3g_choose`.
* QUEST_DATABASE §C3P2 is generated by `tools/docs/gen_quest_db_c3p2.py`.

## 10. Ownership for the build phase (one owner per file; shared files only by small appended blocks)
| stream | owns |
|---|---|
| story data (this contract) | `data/v3/*.json`, `data/locale/de_c3p2_*.json`, `data/chapters/c3.json`, `scripts/core/chapter_ext.gd` (data queries), `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd`, `scenes/levels/L_C3_Registry.tscn` / `L_C3_Quay.tscn` (node list), `tests/test_c3p2_routes.gd`, `tests/reference/**`, `tools/docs/gen_quest_db_c3*.py`, `documentation/QUEST_DATABASE.md` |
| engine (switch) | `scripts/core/game.gd` (switch, save restore, grades/ambience per scene, blockers + `after`/`until` in `scripts/levels/level.gd` / `layer_stack.gd`), `scripts/actors/*` additions, `tests/test_switch*.gd` |
| registry art | `tools/pixelgen/env_veltrava_registry*.py`, `assets/environments/veltrava_registry/**` (replaces the placeholder scene.json, keeps every name of §5.1), `assets/ui/documents/veltrava_registry_*` |
| quay art | `tools/pixelgen/env_veltrava_quay*.py`, `assets/environments/veltrava_quay/**`, `assets/ui/documents/veltrava_quay_*` |
| cinematics | `scenes/cinematics/ch3_{radio,fire,escape,halves}/**`, `tools/pixelgen/env_veltrava_cine_p2.py`, `assets/cinematics/ch3p2/**` |
| puzzle UI | `scenes/ui/CheckPuzzle.tscn`, `scripts/ui/check_puzzle.gd`, `assets/ui/puzzle/c3p2_*`, `tests/test_c3p2_puzzle_ui.gd` |
| exploration / tasks / minigames | `data/explore/veltrava_registry.json`, `veltrava_quay.json`, `tasks_veltrava_p2.json`, `c3p2_history_*.json`, `data/locale/de_explore_veltrava_p2.json`, `de_history_c3p2.json`, `explore_hotspots.json` of the two envs, new mini-game scenes |
| characters | soot variants / carry rows in `assets/characters/{alexei,konrad}/` via their generators |
| audio | `tools/audiogen/c3p2_audio.py`, `assets/audio/amb/amb_veltrava_{registry,fire,quay}.wav` |
