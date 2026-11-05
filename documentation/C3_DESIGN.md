# CHAPTER 3 — „Der eiserne Frieden" (opening) — design contract

Status: AUTHORED 2026-11-04 on branch `kapitel-3`. This file is the single source of truth for every
Chapter-3 contributor (story data, art, characters, cinematics, puzzle UI, integration, tests). It builds on
STORY_BIBLE §2/§3/§6, CHARACTER_BIBLE, WORLD_BIBLE, ART_DIRECTION, TECHNICAL_ARCHITECTURE §2–§5/§11/§12,
QUEST_DATABASE §7.3 and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md` („Alexei sucht eine Original-
Frachtkette; Konrad eine verlässliche Planrevision. Elena kennt nur Fragmente. Erst eine gemeinsame
Belegprüfung macht ihnen klar, dass der Vertragspartner nicht einfach die Person im anderen Land ist.").
German protagonist: **Konrad Adler** (`konrad`). The pre-rename name must not appear in any new file.

Target play time: 15–20 min (station ≈ 8–10, palais ≈ 8–10, cinematics ≈ 1.5).

---------------------------------------------------------------------------------------------------------
## 1. Flow

```
… m1_choose ══> m1_completed ──> LS_X1_Final (existing Ch2 closer) ──> LS_C3_Trains ──> L_C3_Station (Alexei)
   c3a_choose ══> c3a_completed ──> LS_C3_ToHall ──> L_C3_Hall (Konrad)
   c3b_choose ══> c3b_completed ──> LS_C3_Close ──> L_X1_Montage (finale: Story.finale() + end card)
```
* The unchanged engine requires a single linear scene chain that ENDS in the non-quest montage and a finale
  that needs every quest event. Therefore the Chapter-3 scenes are inserted **between** `L_M1_Archive` and
  `L_X1_Montage`: `L_M1_Archive.next_scene = L_C3_Station`, `L_C3_Station.next_scene = L_C3_Hall`,
  `L_C3_Hall.next_scene = L_X1_Montage`; `slice_end_requires = [a1, m1, c3a, c3b]`. The X1 montage
  (`LS_X1_Final`, trigger `m1_completed`) still plays right after Chapter 2 — it is now the Chapter-2 closer —
  and the end card („Ende der Demo – Fortsetzung in Entwicklung“) comes after Chapter 3.
* Consequence (documented in MERGE_NOTES_C3.md): saves that claim the old demo end (`slice_completed` with
  only a1+m1) no longer replay; every save taken before the old end card stays valid.

## 2. Story data (data/v3) — ids are binding

### 2.1 Scenes
| id | title_key | protagonist | camera_mode | entry_spawn | quest | exit event | next | render_profile |
|---|---|---|---|---|---|---|---|---|
| `L_C3_Station` | `world.c3a.title` „Bahnhof Veltrava – Freie Stadt (fiktiv)“ | alexei | oblique_2_5d | `SP_C3_Platform` | `q_c3a_arrival` | `c3a_completed` | `L_C3_Hall` | `rp_veltrava_dawn` |
| `L_C3_Hall` | `world.c3b.title` „Palais der Kommission, Veltrava (fiktiv)“ | konrad | side_on_2d | `SP_C3_Vestibule` | `q_c3b_palais` | `c3b_completed` | `L_X1_Montage` | `rp_veltrava_palais` |

### 2.2 Quests
| id | title_key | character | scene | requires_events | completion_event |
|---|---|---|---|---|---|
| `q_c3a_arrival` | `ui.chapter_c3` „Der eiserne Frieden“ | alexei | L_C3_Station | `m1_completed` | `c3a_completed` |
| `q_c3b_palais` | `ui.chapter_c3` | konrad | L_C3_Hall | `c3a_completed` | `c3b_completed` |

### 2.3 Objectives
Station (Alexei):
```
c3a_talk_conductor ─┬─> c3a_inspect_weighbill ──┐
                    └─> c3a_inspect_departures ─┴─> c3a_pass_control ─> c3a_talk_elena ─> c3a_choose ══> c3a_completed
```
| id | type | text (de) | requires | grants | effects | hotspot |
|---|---|---|---|---|---|---|
| `c3a_talk_conductor` | dialogue `dlg_c3a_conductor` | Frag den Schaffner nach dem versiegelten Wagen. | — | — | — | `conductor` |
| `c3a_inspect_weighbill` | inspect | Lies die Wiegekarte an Wagen 4. | talk_conductor | `ev_c3_weighbill` | `courier_files_seen = true` | `weighbill` |
| `c3a_inspect_departures` | inspect | Prüfe die Abfahrtstafel. | talk_conductor | `ev_c3_departures` | — | `departures` |
| `c3a_pass_control` | dialogue `dlg_c3a_control` | Geh durch die Passkontrolle. | weighbill, departures | `ev_c3_travel_order` | — | `control` |
| `c3a_talk_elena` | dialogue `dlg_c3a_elena` | Sprich mit der Dolmetscherin Elena Weiss. | pass_control | — | — | `elena_cafe` |
| `c3a_choose` | choice | Entscheide, ob du Elena ins Vertrauen ziehst. | talk_elena | — | per choice | `elena_cafe` |

Palais (Konrad):
```
c3b_arrival ─┬─> c3b_inspect_seating ─┐
             └─> c3b_inspect_log ─────┴─> c3b_solve_protocol ─> c3b_inspect_booth ─> c3b_talk_alexei ─> c3b_choose ══> c3b_completed
```
| id | type | text (de) | requires | grants | effects | hotspot |
|---|---|---|---|---|---|---|
| `c3b_arrival` | dialogue `dlg_c3b_arrival` | Melde dich bei Ministerialdirektor Kessler. | — | — | — | `kessler` |
| `c3b_inspect_seating` | inspect | Sieh dir die Sitzordnung der Eröffnungssitzung an. | arrival | `ev_c3_seating` | — | `seating` |
| `c3b_inspect_log` | inspect | Hol das Dolmetscherprotokoll aus dem Protokollbüro. | arrival | `ev_c3_booth_log` | — | `booth_log` |
| `c3b_solve_protocol` | puzzle `pz_c3_protocol` | Gleiche Sitzordnung und Protokoll ab: Wer sprach wann zu Anlage C? | seating, log | — | `protocol_matched = true` | `protocol_table` |
| `c3b_inspect_booth` | inspect | Such Elena Weiss in Kabine 2. | solve_protocol | `ev_c3_carbon` | `elena_missing = true` | `booth_2` |
| `c3b_talk_alexei` | dialogue `dlg_c3b_meeting` | Sprich mit dem Mann von der sowjetischen Delegation. | inspect_booth | — | — | `alexei_meet` |
| `c3b_choose` | choice | Entscheide, was du ihm anvertraust. | talk_alexei | — | per choice | `alexei_meet` |

### 2.4 Choices
| objective | choice id | base text (de) | effect | reaction (speaker: line) |
|---|---|---|---|---|
| `c3a_choose` | `ask_elena` | Elena bitten, Anlage C nach der Sitzung mit dir zu vergleichen | `elena_trust +1` | elena: „Nach der Eröffnungssitzung, Kabine zwei. Bringen Sie den Begleitschein mit – und kommen Sie allein.“ |
| | `note_alone` | Die Plombennummer notieren und allein weitersuchen | `evidence_chain +1` | elena: „Wie Sie meinen. Aber Zahlen übersetzen sich nicht von selbst.“ |
| `c3b_choose` | `share_protocol` | Ihm Elenas Notiz zu Paragraph vier zeigen | `alexei_konrad_trust +1` | alexei: „Begleitgut. Auf meinem Schein steht Fracht. – Heute Nacht um 23:40 fährt ein Zug ohne Halt nach Kordon-17. Jetzt wissen Sie auch etwas.“ |
| | `search_elena` | Nur über Elena reden: Wo wurde sie zuletzt gesehen? | `elena_trust +1` | alexei: „Am Bahnhof hat sie für den Grenzbeamten übersetzt. Ich frage dort. Sie fragen hier. Getrennt.“ |
| | `report_delegation` | Den Vorfall der deutschen Delegation melden | `kessler_alerted +1` | alexei: „Dann haben wir uns nie gesehen, Herr Adler.“ (elena_trust ≥ 1: „Melden Sie es. Aber nennen Sie Frau Weiss nicht beim Namen.“) |

Option text variants (presentation, `data/chapters/c3.json`): `note_alone` — irina_trust ≥ 1 „Die Plombennummer
für Irinas Akte notieren und allein weitersuchen“, alexei_secrecy ≥ 1 „Die Plombennummer notieren – und wieder
niemandem etwas sagen“; `share_protocol` — konrad_evidence ≥ 1 „Ihm Elenas Notiz zeigen – und die Abschrift von
Emils Vermerk“, office_suspicion ≥ 1 „Ihm Elenas Notiz zeigen, obwohl dein Amt dich beobachtet“;
`report_delegation` — office_suspicion ≥ 1 „Den Dienstweg gehen – wie mit der Anfrage in Berlin“.
All options are always offered (the engine does not gate choices by flags; only texts and reactions vary).

### 2.5 Items (evidence)
| id | name (de) | description (de) | category | scene |
|---|---|---|---|---|
| `ev_c3_weighbill` | Wiegekarte Kurierwagen 4 | Ladung „Akten, Anlage C“, 2 410 kg. Plombe C-17/44 mit Gegensiegel der Kommission. Empfänger: Sekretariat der Kommission. | document | L_C3_Station |
| `ev_c3_departures` | Sonderfahrt 23:40 | Die Abfahrtstafel nennt für heute Nacht einen Zug ohne Halt nach Kordon-17, Gleis 5. Unter „Zuggattung“ steht nur: Leerfahrt. | document | L_C3_Station |
| `ev_c3_travel_order` | Dienstreiseauftrag mit Zusatz | Alexeis Reiseauftrag trägt einen Zusatz, von dem er nichts wusste: „Begleitperson Kurierwagen 4“. Auf Russisch begleitet er Fracht, auf Deutsch Akten. | document | L_C3_Station |
| `ev_c3_seating` | Sitzordnung der Eröffnungssitzung | Hufeisentisch im Großen Saal. Die Mikrofone sind im Uhrzeigersinn ab dem Vorsitz nummeriert; das Sekretariat sitzt an einem eigenen Tisch an der offenen Seite. | document | L_C3_Hall |
| `ev_c3_booth_log` | Dolmetscherprotokoll Kabine 2 | Elenas Protokoll der Sitzung: Uhrzeit, Mikrofon, Sprache. Neben Paragraph vier steht ihre Randnotiz: „RU: begleitete Personen – DE: Begleitgut“. | document | L_C3_Hall |
| `ev_c3_carbon` | Durchschrift aus Kabine 2 | Auf Elenas Schreibunterlage hat sich ihre letzte Notiz durchgedrückt: „§ 4 – Personen. Vom Sekretariat, nicht von einer Delegation. Wer hat den Text geliefert?“ Ihr Protokollheft fehlt. | physical_clue | L_C3_Hall |

### 2.6 Flags and events (append to data/v3/flags.json; defaults keep older saves valid)
| flag | type | default | range | set by |
|---|---|---|---|---|
| `alexei_konrad_trust` | integer | 0 | 0–5 | `c3b_choose = share_protocol` (+1) |
| `elena_trust` | integer | 0 | 0–3 | `c3a_choose = ask_elena` (+1), `c3b_choose = search_elena` (+1) |
| `evidence_chain` | integer | 0 | 0–6 | `c3a_choose = note_alone` (+1) |
| `kessler_alerted` | integer | 0 | 0–3 | `c3b_choose = report_delegation` (+1) |
| `courier_files_seen` | boolean | false | — | `c3a_inspect_weighbill` |
| `protocol_matched` | boolean | false | — | `c3b_solve_protocol` |
| `elena_missing` | boolean | false | — | `c3b_inspect_booth` |
Events: `c3a_completed`, `c3b_completed`. No combined morality score (QUEST_DATABASE §7.3).

### 2.7 Puzzle `pz_c3_protocol` (type `symbol_order` — the engine supports no new puzzle types)
* Clues: `ev_c3_seating`, `ev_c3_booth_log`. Display symbols (card order in the tray):
  `["soviet", "secretariat", "chair", "reich"]`. **Solution `["chair", "reich", "secretariat", "soviet"]`.**
  Hint after 2 failures; unlimited retries; no penalty.
* Cards (name plates): `chair` „Vorsitz – Kommissar Aalto“, `reich` „Reichsdelegation“, `soviet`
  „Sowjetische Delegation“, `secretariat` „Sekretariat der Kommission“.
* Seating plan (identical in the inspect document, the puzzle board and the world prop): U-shaped table,
  presidium at the top. Microphones are numbered **clockwise from the presidium (1)**. Right arm (viewer's
  right, going down): mics 2–5 = Sowjetische Delegation. Bottom right corner + bottom left corner: mics 6–7 =
  Beobachter (Schweden, Schweiz). Left arm (going up): mics 8–11 = Reichsdelegation. Secretariat table at the
  open end in the middle: mic 12. The plan PRINTS only the numbers 1, 2 and 12 plus the legend
  „Mikrofone im Uhrzeigersinn ab Vorsitz (1)“; the player counts the rest.
* Booth log (Kabine 2, RU ⇄ DE), entries for agenda item „Anlage C – Logistikintegration“:
  | time | mic | channel | remark (Elena) |
  |---|---|---|---|
  | 10:02 | 1 | FR → DE/RU | Eröffnung TOP 4 „Anlage C“ |
  | 10:06 | 9 | DE → RU | „Keine Einwände gegen die Fassung vom 12. Januar.“ |
  | 10:09 | 12 | FR → DE/RU | verliest § 4 (vorbereiteter Text) — Randnotiz: „RU: begleitete Personen – DE: Begleitgut!“ |
  | 10:11 | 3 | RU → DE | „Wir schließen uns an.“ |
  Mic 9 = left arm = Reichsdelegation; mic 3 = right arm = Sowjetische Delegation → solution above.
* Hint (de): „Die Mikrofone sind im Uhrzeigersinn nummeriert, beginnend beim Vorsitz. Zähle die Plätze am
  Hufeisen ab – das Sekretariat hat einen eigenen Tisch.“
* Success text (de): „Paragraph vier kam vom Sekretariat der Kommission – nicht von einer Delegation. Beide
  Seiten haben zugestimmt, ohne nachzufragen.“

### 2.8 Dialogues (linear; node ids are globally unique; speaker ids in parentheses)
`dlg_c3a_conductor` (entry `c3a_cond_01`):
1. `c3a_cond_01` (conductor) „Finger weg von der Plombe, Herr Ingenieur. Wagen vier gehört nicht zum Zug – nur zur Fahrt.“
2. `c3a_cond_02` (alexei) „Ein Wagen ohne Schaffner?“ · v irina_trust≥1: „In Karsk hätte meine Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Schaffner?“ · v alexei_secrecy≥1: „Ich frage nur. Ein Wagen ohne Schaffner?“
3. `c3a_cond_03` (conductor) „Ein Wagen mit Schlüssel. Und der Schlüssel reist erster Klasse.“
4. `c3a_cond_04` (alexei) „Wo wurde er angehängt?“
5. `c3a_cond_05` (conductor) „In Kordon-17, an der Linie. Jede Woche einer. Mal von Ihrer Seite, mal von unserer.“
6. `c3a_cond_06` (alexei) „Und was ist drin?“
7. `c3a_cond_07` (conductor, end) „Papier, sagt die Wiegekarte. Ich zähle Wagen, keine Akten. Das ist gesünder – auf beiden Seiten.“

`dlg_c3a_control` (entry `c3a_ctrl_01`; grants `ev_c3_travel_order` at the end):
1. `c3a_ctrl_01` (border_officer) „Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation hat Vorrang an Schalter eins.“
2. `c3a_ctrl_02` (elena) „Ich übersetze für die Kommission. Er fragt nach dem Zweck Ihrer Reise.“
3. `c3a_ctrl_03` (alexei) „Technisches Gutachten. Die Gleisanbindung von Kordon-17.“
4. `c3a_ctrl_04` (border_officer) „Hier steht noch etwas: ‚Begleitperson Kurierwagen 4‘. Davon haben Sie nichts gesagt.“
5. `c3a_ctrl_05` (alexei) „Davon wusste ich nichts.“ · v irina_trust≥1: „Davon wusste ich nichts. Gegengezeichnet hat meine Dispatcherin – für die Gleise, nicht für einen Wagen.“ · v alexei_secrecy≥1: „Davon wusste ich nichts. In Karsk hat niemand diesen Auftrag gegengezeichnet.“
6. `c3a_ctrl_06` (elena) „Der Vermerk ist zweisprachig. Auf Russisch begleiten Sie Fracht. Auf Deutsch begleiten Sie Akten.“
7. `c3a_ctrl_07` (border_officer) „Die Wörter sind nicht meine Sache. Der Stempel ist es.“
8. `c3a_ctrl_08` (border_officer, end) „Willkommen in Veltrava, Herr Morozov. Hier ist jeder Ausländer. Das macht die Arbeit gerecht.“

`dlg_c3a_elena` (entry `c3a_el_01`):
1. `c3a_el_01` (elena) „Sie haben den Vermerk gelesen, bevor der Beamte ihn vorlas. Ich habe es gesehen.“
2. `c3a_el_02` (alexei) „Ich lese alles zweimal.“ · v irina_trust≥1: „Eine Kollegin hat mir beigebracht, zweimal hinzusehen. Einmal für die Akte, einmal für die Menschen.“
3. `c3a_el_03` (elena) „Dann lesen Sie Anlage C zweimal. Es gibt sie auf Deutsch, auf Russisch und auf Französisch. Verbindlich sind alle drei.“
4. `c3a_el_04` (alexei) „Und sagen alle drei dasselbe?“
5. `c3a_el_05` (elena) „Fast. Ich notiere die Stellen, an denen sie es nicht tun. Dafür bezahlt mich die Kommission.“
6. `c3a_el_06` (alexei) „Nur dafür?“ · v alexei_secrecy≥1: „Und das erzählen Sie einem Fremden auf dem Bahnsteig?“
7. `c3a_el_07` (elena) „Mein Bruder hat einmal ein Formular unterschrieben, ohne das Kleingedruckte zu verstehen. Seitdem übersetze ich das Kleingedruckte.“
8. `c3a_el_08` (alexei) „Wo ist Ihr Bruder jetzt?“
9. `c3a_el_09` (elena, end) „Auf einer Liste. – Gehen Sie zu Ihrer Delegation, Herr Morozov. In Veltrava hören alle mit. Die Neutralen am genauesten.“

`dlg_c3b_arrival` (entry `c3b_arr_01`):
1. `c3b_arr_01` (kessler) „Adler. Der Zug war pünktlich, Sie sind es nicht. Die Kommission wartet nicht auf Zeichner.“
2. `c3b_arr_02` (konrad) „An der Linie wurde das Gepäck kontrolliert, Herr Ministerialdirektor.“ · v konrad_evidence≥1: „An der Linie wurde das Gepäck kontrolliert, Herr Ministerialdirektor. Auch mein Zeichenrohr.“ · v office_suspicion≥1: „An der Linie wurde mein Gepäck zweimal geöffnet, Herr Ministerialdirektor. Nur meines.“
3. `c3b_arr_03` (kessler) „Sie hinterlegen die Pläne für Kordon-17 im Protokollbüro. Morgen erläutern Sie sie dem Fachausschuss – langsam, deutlich und ohne eigene Meinung.“ · v office_suspicion≥1: „Sie hinterlegen die Pläne für Kordon-17 im Protokollbüro. Ihre Anfrage aus Berlin liegt übrigens auf meinem Tisch. Hier beantworte ich sie nicht.“
4. `c3b_arr_04` (kessler) „Frau Weiss von der Kommission überträgt Ihre Begriffe ins Russische. Sorgen Sie dafür, dass es keine Missverständnisse gibt.“
5. `c3b_arr_05` (elena) „Herr Adler, eine Frage vorab. Ihr Plan nennt einen ‚Erfassungsraum‘. Was wird dort erfasst?“
6. `c3b_arr_06` (konrad) „Unterlagen. Ein Archivraum mit Sortiertischen und Karteischränken.“
7. `c3b_arr_07` (elena) „In der russischen Fassung steht dort ‚Sammelstelle‘. Für Karteikarten sagt man das nicht.“
8. `c3b_arr_08` (konrad) „Übersetzungen weichen ab. Dafür gibt es Sie.“
9. `c3b_arr_09` (elena, end) „Dafür gibt es mich. Ich schreibe es auf. Kabine zwei, falls Sie mich suchen.“

`dlg_c3b_meeting` (entry `c3b_meet_01`):
1. `c3b_meet_01` (alexei) „Das ist nicht Ihre Kabine.“
2. `c3b_meet_02` (konrad) „Ihre auch nicht. Sowjetische Delegation, nehme ich an – das Abzeichen.“
3. `c3b_meet_03` (alexei) „Technischer Gutachter. Ich suche Frau Weiss.“ · v elena_trust≥1: „Frau Weiss und ich waren nach der Sitzung verabredet. Hier, an Kabine zwei.“ · v evidence_chain≥1: „Ich suche den Empfänger eines Kurierwagens. Plombe C-17/44. Die Wiegekarte nennt dieses Haus.“
4. `c3b_meet_04` (konrad) „Sie ist nicht hier. Ihr Protokollheft auch nicht. Unten in der Garderobe hängt noch ihr Mantel.“
5. `c3b_meet_05` (alexei) „Und Sie stehen zufällig in ihrer Kabine. Mit einem Bleistift in der Hand.“
6. `c3b_meet_06` (konrad) „Ich bin Zeichner. Ich lese, was auf Tischen liegt.“
7. `c3b_meet_07` (alexei) „In Karsk fehlen drei Wagen. Auf ihrem Siegel stand dieselbe Serie wie auf den Papieren hier.“ · v irina_trust≥1: „In Karsk fehlen drei Wagen. Eine Kollegin hat sie gezählt. Sie würde es bezeugen – ihr Name steht schon neben meinem.“ · v alexei_secrecy≥1: „In Karsk fehlen drei Wagen. Niemand dort weiß, dass ich hier danach frage. Das soll so bleiben.“
8. `c3b_meet_08` (konrad) „In Berlin trägt ein Korridor dieselbe Serie. Einer, den es nicht geben dürfte.“ · v konrad_evidence≥1: „In Berlin trägt ein Korridor dieselbe Serie. Ich habe eine Abschrift des Vermerks. Was darin steht, behalte ich vorerst.“ · v office_suspicion≥1: „In Berlin trägt ein Korridor dieselbe Serie. Ich habe offiziell danach gefragt. Seitdem sieht man mir über die Schulter.“
9. `c3b_meet_09` (alexei) „C-17.“
10. `c3b_meet_10` (konrad) „C-17. – Sie sind Russe, ich bin Deutscher. Man hat uns beigebracht, dass einer von uns lügt.“
11. `c3b_meet_11` (alexei) „Man hat uns vieles beigebracht. – Morozov. Karsk.“
12. `c3b_meet_12` (konrad, end) „Adler. Berlin.“

Variant priority = listed order (first matching condition wins). Variants and expressions live in
`data/chapters/c3.json`; their German text in `data/locale/de_c3_dialogue.json`.

### 2.9 Cinematics (data/v3/cinematics.json; LOCKED_CINEMATICS extended — validator list only)
| id | trigger | skip policy | shots |
|---|---|---|---|
| `LS_C3_Trains` | event `m1_completed` (after `LS_X1_Final`) | visual_only | t1 Konrad at the window of the German delegation's saloon car, night, snow plain, floodlit Line (8 s) · t2 match cut through the window frame (2 s) · t3 Alexei at the window of the Soviet car, tea glass in a metal holder, same plain from the other side (8 s) · t4 dawn: both trains converge on the river bridge into Veltrava (6 s) |
| `LS_C3_ToHall` | event `c3a_completed` | visual_only | k1 station clock 9:40 (3 s) · k2 match cut to the palais clock 9:40, Konrad enters (3 s) |
| `LS_C3_Close` | event `c3b_completed` | visual_only | n1 night, platform 5: a special train with dark windows leaves, steam (6 s) · n2 two lit hotel windows across the station square, two silhouettes, one whistle (6 s) |
Inner lines (presentation, `data/locale/de_c3_cinematics.json`, chosen from `configure(ctx).flags`):
`cin.c3.trains.konrad.base` „Die Pläne für Kordon-17 liegen im Zeichenrohr. Mehr, sagt man mir, muss ich nicht wissen.“ ·
`…konrad.evidence` (konrad_evidence ≥ 1) „Die Abschrift liegt im Zeichenrohr, zwischen zwei Lichtpausen, die niemand ausrollt.“ ·
`…konrad.suspicion` (office_suspicion ≥ 1) „Auf meine Anfrage kam keine Antwort. Nur diese Dienstreise.“ ·
`cin.c3.trains.alexei.base` „In Karsk fehlen drei Wagen. Ich fahre ihnen nach, mit einem Auftrag, den ich nicht ganz verstehe.“ ·
`…alexei.irina` (irina_trust ≥ 1) „Irina hat meinen Reiseauftrag gegengezeichnet. Ihr Name fährt jetzt mit.“ ·
`…alexei.secrecy` (alexei_secrecy ≥ 1) „Irina hat nicht gefragt, warum ich mich für diese Reise gemeldet habe. Das war schlimmer als jede Frage.“ ·
`cin.c3.trains.place` „Veltrava, Freie Stadt an der Linie. Februar 1964.“ ·
`cin.c3.tohall.time` „Palais der Kommission, 9:40 Uhr.“ ·
`cin.c3.close.train` „23:40, Gleis 5. Ein Sonderzug ohne Halt nach Kordon-17.“ ·
`cin.c3.close.after` „Zwei Hotels. Derselbe Pfiff.“

## 3. Presentation layer (no engine change) — `data/chapters/c3.json` + `scripts/core/chapter_ext.gd`
`Game` asks `ChapterExt` (loaded once from every `data/chapters/*.json`) for everything chapter-specific:
`levels`, `entry_spawn`, `chapter_cards` (level → [title key, subtitle key]), `palettes`, `grades`,
`line_expr` (node → expression), `line_variants` (node → [{when, key}]), `choice_text`
(objective → choice → [{when, key}]), `reactions` (objective → choice → [{when?, speaker, key, expr}]),
`puzzles` (objective → UI scene path), `cinematics` (sequence id → §12.5 scene path).
Condition `when`: `{"<flag>": ">=1" | "==0" | "<=2" | true | false, …}` — all must hold; first match wins.
Hook points in `scripts/core/game.gd` are listed in MERGE_NOTES_C3.md.

## 4. Levels and hotspots (art ↔ content contract)
### 4.1 `L_C3_Station` — env `assets/environments/veltrava_station/` (oblique 2.5D like Karsk, 1920×360)
Composition (back → front): dawn sky · Veltrava old-town skyline (baroque domes, Gothic spires, castle hill, the
palais dome with flagpoles; haze) · nearer mansard roofs with copper patina and chimney smoke · the
neo-renaissance station building (central hall with big lit arched window, clock tower, arcaded wings) ·
far track with the German delegation train (grey-black carriages, pennants) · platform canopies on cast-iron
columns · near track with the Soviet delegation train (green carriages) ending in **courier wagon 4**
(windowless dark van, lead seals, brass frame with the weighing ticket, convertible bogies) · the walkable
platform (y ≈ 262–350) · foreground frame (canopy column, bench, snowy platform edge).
**Tracks are four-rail dual gauge** (1435 mm + Soviet broad gauge): Veltrava serves both networks.
x-layout: 0–560 Soviet carriages (Alexei steps out near x 120) · 560–760 wagon 4 + conductor · 760–1060
platform middle (station clock hanging from the canopy, departures board on a pillar, benches, kiosk) ·
1060–1380 passport control of the commission (barrier, booth with two counters „Schalter 1 · Reichsdelegation“,
„Schalter 2 · Sowjetische Delegation“, trilingual signs DE/RU/FR, commission flag; the German queue at counter 1
with Konrad in it, seen from behind) · 1380–1920 concourse (Café „Korridor“ = the one warm focal light, newspaper
kiosk, exchange office, notice board, waiting-room door with a tiled stove, exit arch to the snowy square with a
tram). Flags: commission (fictional Veltrava arms: a bridge with three arches over a wavy line, white on
slate blue), USSR and Reich delegation flags — neutral file + `_hist` variant (§12.4).
Required hotspots (world px, where the player stands; inside the walkable polygon):
story `conductor` ~(600, 292) · `weighbill` ~(690, 290) · `departures` ~(900, 286) · `control` ~(1190, 292) ·
`elena_cafe` ~(1640, 300) · NPC anchors `elena_control` ~(1222, 288), `konrad_queue` ~(1300, 280),
`voronova` ~(330, 300).
exploration `exp_four_rails` (240) · `exp_luggage` (420) · `exp_pigeons` (480) · `exp_bogie` (730) ·
`exp_mitten` (800) · `exp_clock` (960) · `exp_kiosk` (1010) · `exp_poster` (1080) · `exp_return_notice` (1440) ·
`exp_stove` (1520) · `exp_exchange` (1770) · `exp_tram` (1880) · hidden `exp_footprints` (160, at the platform
edge) — chats at `voronova` and `control`.
Spawns: `SP_C3_Platform` ~(120, 300). Warm focal light: café. Cold lights: canopy lamps. FX: snow under the
canopy edge only (none under the roof), steam from the Soviet loco (left, off-screen) and from wagon heaters,
pigeons (anim sprite), smoke from city chimneys, fog band in front of the skyline.

### 4.2 `L_C3_Hall` — env `assets/environments/veltrava_hall/` (side view like the archive, 1920×360)
Jugendstil conference palace (former Kurhaus), morning: tall windows with cold daylight shafts, chandeliers
(warm), marble floor, walnut panelling, brass. Rooms left → right along the floor (feet y ≈ 300):
0–420 vestibule (revolving door, snow outside, cloakroom counter with numbered hooks, a row of six flags on
poles: commission, USSR, Reich, Sweden, Switzerland, Finland — USSR/Reich neutral + `_hist`) · 420–1000 foyer
(grand staircase, chandelier, buffet table, photo wall of the 1953 armistice signing, window to the old town
and the frozen river with Line watchtowers on the far bank, the double doors to the Großer Saal with the
seating-plan easel) · 1000–1400 corridor + Protokollbüro (typewriters, mimeograph, wire basket of carbon
copies, bookshelf of treaty volumes, evacuation plan on the wall, the large table where Konrad spreads the
plan and the log) · 1400–1920 interpreters' corridor behind the hall: three glass booths (1 FR, 2 RU⇄DE, 3
EN); through the booth glass the Großer Saal is seen below in parallax (horseshoe table, delegates, flags).
Required hotspots: story `kessler` ~(300) · `seating` ~(930) · `booth_log` ~(1180) · `protocol_table`
~(1270) · `booth_2` ~(1650) · `alexei_meet` ~(1700) · NPC anchors `elena_arrival` ~(345), `voronova_bg`
~(700), `typist` ~(1120), `journalist` ~(560).
exploration `exp_flags` (150) · `exp_cloakroom` (240) · `exp_photos` (470) · `exp_chandelier` (640) ·
`exp_buffet` (780) · `exp_window` (850) · `exp_evac_plan` (1010) · `exp_treaty_shelf` (1070) · `exp_mimeograph`
(1330) · `exp_headsets` (1520) — chats at `typist` and `journalist`.
Spawn `SP_C3_Vestibule` ~(70). Warm focal light: chandelier/booth 2 lamp at the right moment.

## 5. Characters (new; `tools/pixelgen/chargen_cast_c3.py` + `characters_c3.py`, sheets §4, portraits 4 expr.)
| id | who | look (silhouette first) | rows |
|---|---|---|---|
| `elena` | Elena Weiss (30s), bilingual interpreter of the commission — **most careful work** | slim, charcoal wool coat to mid-calf, wine-red scarf (her one warm accent), dark hair pinned low, white commission armband with a slate-blue band, black notebook held to the chest; alert, quick, no glamour | idle_side, walk_side, idle_front, talk_side |
| `border_officer` | Veltrava frontier officer (50s) | slate-blue greatcoat, peaked cap with a small bridge badge, armband, moustache, rubber stamp | idle_side, talk_side, idle_front |
| `conductor` | Schaffner of the Corridor Express (60), German railwayman of the mixed crew | dark navy uniform coat with brass buttons, peaked cap with a winged-wheel badge (no state insignia), grey moustache, ticket punch, slightly stooped | idle_side, walk_side, talk_side |
| `voronova` | Lidia Voronova (50s), Soviet deputy minister of railways | heavy dark-brown coat with karakul collar and hat, leather document folder, sturdy stance | idle_side, talk_side |
| `kessler` | Ministerialdirektor Gerhard Kessler (50s), Reich Ministry of Transport | long charcoal overcoat, homburg, gloves, briefcase, thin glasses, very upright; civil servant, no uniform, no badges | idle_side, talk_side, idle_front |
| `typist` | Commission typist (40s, Swiss) | cardigan, skirt, sleeve protectors, pencil behind the ear | idle_side, talk_side |
| `journalist` | Nils Ekdahl (40s), Swedish newspaper correspondent | tweed coat, scarf, notebook, camera on a strap | idle_side, walk_side, talk_side |
Names/roles: `data/locale/de_c3_characters.json` (`char.<id>.name`, `char.<id>.role`).

## 6. Exploration (§12) — `data/explore/veltrava_station.json`, `veltrava_hall.json`, `c3_history_soviet.json`, `c3_history_reich.json` (one history file per side, §12.1)
Area `veltrava`; ids `veltrava.station.<name>` / `veltrava.hall.<name>`; strings in
`data/locale/de_explore_veltrava.json`. Station: 12 finds + 1 hidden + 2 chats; palais: 10 finds + 2 chats.
Real-history cards (new file, sober documentary voice, 450–800 chars, verified sources):
`hist.soviet.repatriation` (forced repatriations 1945–47 after Yalta) at `exp_return_notice`;
`hist.soviet.handover_1940` (NKVD handovers of German and Austrian emigrants to the Gestapo, Brest-Litovsk
1940) at `exp_treaty_shelf`; `hist.reich.nuremberg_interpreters` (simultaneous interpretation at the Nuremberg
trial 1945–46) at `exp_headsets`. Jokes and easter eggs never touch atrocity topics.

## 7. Ownership (one owner per file; nobody edits another stream's files)
| stream | owns |
|---|---|
| integration (orchestrator) | `scripts/core/chapter_ext.gd`, `scripts/actors/story_npc.gd`, `scripts/actors/gated_interactable.gd`, `data/chapters/c3.json`, `scenes/levels/L_C3_*.tscn`, hook lines in `game.gd`/`layer_stack.gd`/`story_engine.gd`, `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd` |
| story data | `data/v3/*.json` (C3 additions), `data/locale/de_c3_*.json`, `documentation/QUEST_DATABASE.md` §C3 |
| exploration content | `data/explore/veltrava_*.json`, `data/explore/c3_history_*.json`, `data/locale/de_explore_veltrava.json`, `de_history_c3.json` |
| station art | `tools/pixelgen/env_veltrava_station*.py`, `env_veltrava_lib.py`, `assets/environments/veltrava_station/**`, station documents in `assets/ui/documents/veltrava_station_*` + `veltrava_station_documents.json` |
| palais art | `tools/pixelgen/env_veltrava_hall*.py`, `assets/environments/veltrava_hall/**`, hall documents `assets/ui/documents/veltrava_hall_*` + `veltrava_hall_documents.json` |
| characters | `tools/pixelgen/chargen_cast_c3.py`, `chargen_portrait_c3.py`, `characters_c3.py`, `assets/characters/{elena,border_officer,conductor,voronova,kessler,typist,journalist}/` |
| cinematics | `tools/pixelgen/env_veltrava_cine.py`, `scenes/cinematics/ch3_*/**`, `assets/cinematics/ch3/**` |
| puzzle UI | `scenes/ui/ProtocolPuzzle.tscn`, `scripts/ui/protocol_puzzle.gd`, `tools/pixelgen/gen_ui_c3.py`, `assets/ui/puzzle/c3_*` |
| tests | `tests/test_c3_*.gd`, updates of existing tests, `tests/reference/*` |
| audio (optional) | `tools/audiogen/c3_audio.py`, `assets/audio/{amb,music}/*veltrava*` |
