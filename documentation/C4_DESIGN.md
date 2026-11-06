# CHAPTER 4, PART 1 — „Stimmen unter Beton“ — design contract

Status: AUTHORED 2026-11-06 (round 9). Single source of truth for every contributor of this round (story data,
env-tunnels, env-annex, cinematics, puzzle UI, cast + audio, exploration; the evidence board „Die Akte C-17“ and the
feel pass read it). Builds on C3P2_DESIGN.md (its ids, texts and rules stay valid), STORY_BIBLE §2/§3/§6/§7,
CHARACTER_BIBLE, WORLD_BIBLE, TECHNICAL_ARCHITECTURE §11–§13 and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md`
(„Zeugnisse aus Wohnvierteln zeigen, dass C-17 nicht allein Waren organisiert, sondern Überwachung und erzwungene
Umsiedlung begünstigt. Ein Archivpfad und ein Transportpfad müssen zusammengeführt werden. Entscheidung: Schutz von
Menschen vor Geschwindigkeit der Veröffentlichung.“). German protagonist: **Konrad Adler** (`konrad`).

**What part 1 is:** four days after the night of the fire both men are home, each with his half of the file. Alexei,
back in Karsk, follows the three January wagons of the freight books into Service Tunnel 3 under the freight yard and
finds the transfer siding where the courier wagons change their numbers — one wagon, four numbers, the next one still
wet: **C-17/45**, Tuesday, 23.40. Konrad, back in Berlin, listens to Marta Vogel, who drives the first tram of line 74
around the cleared blocks, lays her route over the site plan he drew himself and finds the registry annex that breathes
through the advertising columns of the clearance zone. The two paths meet on **shared objects**, shown as cinematic
match cuts between the cities: the same wagon number (C-17/45 on a wagon in Karsk and on card crates in Berlin), the
same registry card (No. 0417, torn in two: the German half in Konrad's glove, the Russian half on Alexei's desk), the
same rubber-stamp gesture („ABGANG“ / „ПРИНЯТЬ“). The card belongs to **Anna Lindner, née Kowalenko** — taken to the
Reich as a forced labourer in 1942, evicted from house No. 9 in January, now listed for „Rückführung Ost“ in wagon
C-17/45 on Tuesday, together with Pjotr Iljin. Her daughter Ilse (8) sleeps on Marta's sofa; her teacher is Konrad's
sister Hanna. At the annex counter Konrad can have Anna's household file — signed proof, before Tuesday — if he gives the
registrar Marta's name. Lev Sokolov in Karsk asked Alexei for the same thing the other way round: „Mein Name steht in
keinem Papier.“ Nothing is resolved: the wagon still leaves on Tuesday.

Target play time **15–18 min** main path: homeward cinematic ≈ 0.3 · Karsk cellar (Alexei) ≈ 3.5 · tram loop
(Konrad, with the route puzzle) ≈ 5 · transfer siding (Alexei, with the number puzzle) ≈ 4 · annex counter (Konrad, the
decision) ≈ 3 · match cuts + closing ≈ 1.2.

---------------------------------------------------------------------------------------------------------
## 1. Flow

```
… c3g_choose ══> c3g_completed ──> LS_C3_Halves (existing) ──> LS_C4_Homeward (new) ──> level load
 ──> L_C4_TunnelsA (Alexei, Karsk cellar)     c4a_open_door      ══> c4a_completed ──> LS_C4_Number (match cut: C-17/45)
 ──> L_C4_AnnexA   (Konrad, Berlin tram loop)  c4b_inspect_crates ══> c4b_completed ──> LS_C4_Card   (match cut: card 0417)
 ──> L_C4_TunnelsB (Alexei, transfer siding)   c4c_talk_lev       ══> c4c_completed ──> LS_C4_Stamp  (match cut: the stamps)
 ──> L_C4_AnnexB   (Konrad, the annex)         c4d_choose         ══> c4d_completed ──> LS_C4_Voices ──> L_X1_Montage
     (existing montage → end card listing all seven decisions → credits)
```
* The unchanged engine needs ONE linear scene chain ending in the non-quest montage (C3_DESIGN §1). The four new scenes
  are inserted between `L_C3_Quay` and `L_X1_Montage`: `L_C3_Quay.next_scene = L_C4_TunnelsA` (the only modified
  record) … `L_C4_AnnexB.next_scene = L_X1_Montage`; `slice_end_requires` = all thirteen quest events.
* Two level files, each hosting two Story scenes that are **not** consecutive: `scenes/levels/L_C4_Tunnels.tscn`
  (`L_C4_TunnelsA`, `L_C4_TunnelsB`) and `scenes/levels/L_C4_Annex.tscn` (`L_C4_AnnexA`, `L_C4_AnnexB`). Every
  protagonist change crosses a city, so every scene starts with a level load (no in-level switch, §12.11 detection
  never fires; `scene_partner()` = "" for all four, the c4.json `switches` say `"partner": "none"` explicitly and carry
  the per-scene ambience/music/grade). ChapterExt level keys (Explore `"level"`): `L_C4_TunnelsA`, `L_C4_AnnexA`.
* Each file has two walk areas separated by a permanent blocker (the iron tunnel door, the shaft wall): scene A plays
  left of it, scene B right of it; the match-cut cinematic carries the protagonist through. Entry spawns put each scene
  in its own area.

### 1.1 Save and profile compatibility (binding)
* **No new flags** (C3P2 §1.1 still holds: one new flag would invalidate every save and every memory snapshot). The
  decision writes existing meters only — `evidence_chain` (name_marta) or `civilian_welfare` (protect_marta, first use
  of this canonical meter) — and the choice history `c4d_choose`, which later chapters read (`choice.c4d_choose`).
* New events `c4a_completed` … `c4d_completed` (flags.json `events`, before `slice_completed`) are harmless for saves
  that have not reached them.
* Every save a round-8 player can have stays valid: autosaves never store the montage, so the latest is „before
  c3g_choose“ on the quay — it loads, the decision now leads into Karsk.
* **Profile snapshots of `L_C3_Quay`** (memories, recorded at `c3g_completed` by a round-8 build) name
  `current_scene = L_X1_Montage`; `SaveSystem.rebase_story()` (round 8) re-bases them to the scene after the last exit
  event = `L_C4_TunnelsA` / `alexei` (test: `tests/test_save_rebase_r8.gd`). A save claiming the montage with only
  a1 … c3g done is rejected (as before).
* Planned STORY_BIBLE §7 variables stay design notes (§2.6): they are derivable later from `choice_history`, so nothing
  is lost by not storing them now.

---------------------------------------------------------------------------------------------------------
## 2. Story data (data/v3) — ids are binding

### 2.1 Scenes
| id | title_key (de) | protagonist | camera_mode | entry_spawn | quest | exit event | next | level file | render_profile |
|---|---|---|---|---|---|---|---|---|---|
| `L_C4_TunnelsA` | `world.c4a.title` „Archivkeller der Güterabfertigung, Karsk (fiktiv)“ | alexei | side_on_2d | `SP_C4_Stairs` | `q_c4a_cellar` | `c4a_completed` | `L_C4_AnnexA` | `L_C4_Tunnels.tscn` | `rp_karsk_cellar` |
| `L_C4_AnnexA` | `world.c4b.title` „Wendeschleife Süd 8, Berlin (alternative Geschichte)“ | konrad | side_on_2d | `SP_C4_Shelter` | `q_c4b_loop` | `c4b_completed` | `L_C4_TunnelsB` | `L_C4_Annex.tscn` | `rp_berlin_dawn` |
| `L_C4_TunnelsB` | `world.c4c.title` „Umsetzgleis unter dem Güterbahnhof, Karsk“ | alexei | side_on_2d | `SP_C4_Office` | `q_c4c_siding` | `c4c_completed` | `L_C4_AnnexB` | `L_C4_Tunnels.tscn` | `rp_karsk_tunnel` |
| `L_C4_AnnexB` | `world.c4d.title` „Erfassungsstelle, Nebenstelle Süd – Berlin“ | konrad | side_on_2d | `SP_C4_Ladder` | `q_c4d_annex` | `c4d_completed` | `L_X1_Montage` | `L_C4_Annex.tscn` | `rp_berlin_annex` |
`L_C3_Quay.next_scene` changes from `L_X1_Montage` to `L_C4_TunnelsA` (the only modified record).

### 2.2 Quests (title `ui.chapter_c4` „Stimmen unter Beton“ — chapter number 4 in memories / journal)
| id | character | scene | requires_events | completion_event |
|---|---|---|---|---|
| `q_c4a_cellar` | alexei | L_C4_TunnelsA | `c3g_completed` | `c4a_completed` |
| `q_c4b_loop` | konrad | L_C4_AnnexA | `c4a_completed` | `c4b_completed` |
| `q_c4c_siding` | alexei | L_C4_TunnelsB | `c4b_completed` | `c4c_completed` |
| `q_c4d_annex` | konrad | L_C4_AnnexB | `c4c_completed` | `c4d_completed` |

### 2.3 Objectives
Every inspect objective grants an item (InspectView and the input driver rely on it). Two dialogues grant an item at
their last line (`ev_c4_tunnel_plan`, `ev_c4_route_board`).

Tunnels A — Alexei in the archive cellar (Karsk, ≈ 4.40):
```
c4a_inspect_shelf ─> c4a_talk_lev ─> c4a_inspect_book ─> c4a_inspect_carbon ─> c4a_talk_tunnel ─> c4a_open_door ══> c4a_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4a_inspect_shelf` | inspect | `obj.c4a_shelf` „Such im Archivkeller die Frachtbücher vom Januar.“ | — | `ev_c4_book_gap` | `book_shelf` |
| `c4a_talk_lev` | dialogue `dlg_c4a_lev` | `obj.c4a_lev` „Sprich mit Lev Sokolov an seinem Tisch.“ | inspect_shelf | — | `lev_cellar` |
| `c4a_inspect_book` | inspect | `obj.c4a_book` „Lies im Januarbuch die Spalte ‚Genehmigt‘.“ | talk_lev | `ev_c4_cut_signatures` | `desk_book` |
| `c4a_inspect_carbon` | inspect | `obj.c4a_carbon` „Halte Levs Durchschläge gegen die Lampe.“ | inspect_book | `ev_c4_carbon` | `lamp_table` |
| `c4a_talk_tunnel` | dialogue `dlg_c4a_tunnel` | `obj.c4a_tunnel` „Frag Lev, wohin die Wagen gefahren sind.“ | inspect_carbon | `ev_c4_tunnel_plan` | `lev_cellar` |
| `c4a_open_door` | inspect | `obj.c4a_door` „Öffne die Eisentür zum Dienststollen.“ | talk_tunnel | `ev_c4_fresh_tracks` | `tunnel_door` |

Annex A — Konrad at the tram loop Süd 8 (Berlin, ≈ 5.10):
```
c4b_inspect_notice ─> c4b_talk_marta ─> c4b_solve_routes ─> c4b_inspect_column ─> c4b_talk_ilse ─> c4b_inspect_crates ══> c4b_completed
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4b_inspect_notice` | inspect | `obj.c4b_notice` „Lies den Bescheid an der Tür von Nummer neun.“ | — | `ev_c4_notice` | `door_9` |
| `c4b_talk_marta` | dialogue `dlg_c4b_marta` | `obj.c4b_marta` „Sprich mit der Fahrerin der Linie 74.“ | inspect_notice | `ev_c4_route_board` | `marta_tram` |
| `c4b_solve_routes` | puzzle `pz_c4_routes` | `obj.c4b_routes` „Leg Martas Linienplan im Licht des Fahrplankastens auf den Lageplan.“ | talk_marta | — | `timetable_case` |
| `c4b_inspect_column` | inspect | `obj.c4b_column` „Sieh dir die Litfaßsäule an der Schleife an.“ | solve_routes | `ev_c4_shaft` | `column_s2` |
| `c4b_talk_ilse` | dialogue `dlg_c4b_ilse` | `obj.c4b_ilse` „Sag Marta, was unter ihrer Schleife liegt.“ | inspect_column | — | `marta_tram` |
| `c4b_inspect_crates` | inspect | `obj.c4b_crates` „Sieh dir die Kisten an der Ladeluke an.“ | talk_ilse | `ev_c4_card_de` | `loading_hatch` |

Tunnels B — Alexei at the transfer siding (Karsk, ≈ 7.30):
```
c4c_inspect_card ─────┬─> c4c_solve_numbers ─> c4c_inspect_wagon ─> c4c_talk_lev ══> c4c_completed
c4c_inspect_stencils ─┘
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4c_inspect_card` | inspect | `obj.c4c_card` „Lies die Karteikarte auf dem Tisch der Gleisbude.“ | — | `ev_c4_card_ru` | `office_desk` |
| `c4c_inspect_stencils` | inspect | `obj.c4c_stencils` „Sieh dir den Farbstand mit den Schablonen an.“ | — | `ev_c4_stencils` | `paint_stand` |
| `c4c_solve_numbers` | puzzle `pz_c4_numbers` | `obj.c4c_numbers` „Finde heraus, welche Nummern dieser Wagen getragen hat.“ | inspect_card, inspect_stencils | — | `wagon_side` |
| `c4c_inspect_wagon` | inspect | `obj.c4c_wagon` „Schieb die Tür des Wagens auf.“ | solve_numbers | `ev_c4_wagon_inside` | `wagon_door` |
| `c4c_talk_lev` | dialogue `dlg_c4c_lev` | `obj.c4c_lev` „Sprich mit Lev.“ | inspect_wagon | — | `lev_siding` |

Annex B — Konrad in the registry annex (Berlin, ≈ 6.00):
```
c4d_inspect_drawer ─┬─> c4d_inspect_tube ─> c4d_talk_registrar ─> c4d_choose ══> c4d_completed
c4d_inspect_plan ───┘
```
| id | type | text (de) | requires | grants | hotspot |
|---|---|---|---|---|---|
| `c4d_inspect_drawer` | inspect | `obj.c4d_drawer` „Such in der Kartei die Schublade Süd 8.“ | — | `ev_c4_drawer_s8` | `drawer_s8` |
| `c4d_inspect_plan` | inspect | `obj.c4d_plan` „Sieh dir den Lüftungsplan an der Wand an.“ | — | `ev_c4_annex_plan` | `plan_wall` |
| `c4d_inspect_tube` | inspect | `obj.c4d_tube` „Lies, was die Rohrpost gebracht hat.“ | inspect_drawer, inspect_plan | `ev_c4_tube_slip` | `tube_station` |
| `c4d_talk_registrar` | dialogue `dlg_c4d_counter` | `obj.c4d_registrar` „Frag am Schalter nach der Akte Lindner.“ | inspect_tube | — | `registrar_counter` |
| `c4d_choose` | choice | `obj.c4d_choice` „Entscheide, ob du Martas Namen nennst.“ | talk_registrar | per choice | `registrar_counter` |

### 2.4 The decision (every option raises exactly one existing meter; both options always offered)
| objective | choice id | base text (de) | effect | option variants (choice_text) | reaction (speaker: line) |
|---|---|---|---|---|---|
| `c4d_choose` | `name_marta` | `choice.c4d.name_marta` „Marta Vogels Namen nennen – die Akte Lindner wäre ein Beweis mit Unterschriften, noch vor Dienstag“ | `evidence_chain +1` | v choice.c3d = pocket_plan: `choice.c4d.name_marta.pocket` „Marta Vogels Namen nennen – zu Blatt 7 käme die Akte Lindner, ein Beweis mit Unterschriften, noch vor Dienstag“ | registrar (`dlg.c4.react.name_marta`): „Vogel, Marta. Straßenbahn, Linie 74 – das finden wir. Danke, Herr Adler. Die Akte Lindner, bitte sehr.“ |
| `c4d_choose` | `protect_marta` | `choice.c4d.protect_marta` „Keinen Namen nennen – ‚Ich habe es auf der Straße gehört.‘“ | `civilian_welfare +1` | v choice.c3b = report_delegation: `choice.c4d.protect_marta.report` „Keinen Namen nennen – ‚Ich habe es auf der Straße gehört.‘ In Veltrava hast du schon einmal jemanden gemeldet“ | registrar (`dlg.c4.react.protect_marta`): „Auf der Straße. Dann bleibt die Akte im Schrank, Herr Adler. Kommen Sie wieder, wenn die Straße einen Namen hat.“ |

Why each option costs something: `name_marta` gets the one document that names every official of the chain (eviction →
C-17 flag → „Rückführung Ost“, signed) **before Tuesday**, the kind of proof a neutral press can print — and it puts
Marta's name in the annex on the morning Kommissar Wendt asks for „Verbleib der Kinder, Auskunftspersonen namentlich“
(the tube slip): Marta, Ilse and Hanna become findable. `protect_marta` keeps all three out of the files and keeps
Konrad's promise — and leaves him with a card half and a site plan, no signed chain, two days before the wagon leaves.
Neither option changes what happens on Tuesday in this part; the end card lists the decision and Chapter 4 part 2 /
Chapter 5 read it.
Option text variants (`data/chapters/c4.json` `choice_text`, first match wins; every variant keeps the words the
reaction answers): see the table. The bases are heard on the routes the variants do not cover.
Meter ranges stay valid on every route: `evidence_chain` ≤ 4 (note_alone + pocket_plan + split_by_language +
name_marta) ≤ 6, `civilian_welfare` ≤ 1 ≤ 3.

### 2.5 Items (evidence)
| id | name (de) | description (de) | category | scene |
|---|---|---|---|---|
| `ev_c4_book_gap` | Lücke im Regal | Im Regal der Frachtbücher fehlen drei Bände: Januar 1964, erste bis dritte Dekade. Auf dem leeren Brett liegt ein Zettel in Levs Schrift: „Bei L. S. – zur Durchsicht.“ | physical_clue | L_C4_TunnelsA |
| `ev_c4_cut_signatures` | Frachtbuch Januar, Spalte „Genehmigt“ | Bei den drei Umbuchungen vom 14., 21. und 28. Januar ist die Unterschrift herausgeschnitten – sauber, mit einer Klinge. Daneben jedes Mal derselbe Vermerk: „Abt. T – mündlich“. | document | L_C4_TunnelsA |
| `ev_c4_carbon` | Durchschläge mit Druckspur | Lev hebt von jedem Frachtbrief den Durchschlag auf. Gegen die Lampe zeichnet sich ab, was oben herausgeschnitten wurde: „Ju. Archipov, Oberst, Transportabteilung“ – dreimal dieselbe Hand. | document | L_C4_TunnelsA |
| `ev_c4_tunnel_plan` | Plan Dienststollen 3, 1941 | Ein Luftschutzplan von 1941, auf Leinen gezogen. Der Stollen läuft unter dem ganzen Güterbahnhof durch und endet an einem Gleis ohne Nummer. Jemand hat den Weg mit Bleistift nachgezogen. | document | L_C4_TunnelsA |
| `ev_c4_fresh_tracks` | Spuren hinter der Eisentür | Die Schienen im Stollen sind blank gefahren, der Staub daneben ist zertreten. Auf der Schwelle ein Tropfen rotbraune Farbe, noch weich. | physical_clue | L_C4_TunnelsA |
| `ev_c4_notice` | Räumungsbescheid Nr. 9 mit Lageplan | Der Bescheid vom Januar, darunter ein frischer Nachtrag: „Haushalt aufgelöst. Vorgang an Nebenstelle Süd.“ Angeheftet der Lageplan Süd 8 mit drei Schächten, S 1 bis S 3. Im Schriftfeld: gez. K. A. | document | L_C4_AnnexA |
| `ev_c4_route_board` | Martas Linienplan, Linie 74 | Auf Pauspapier aus dem Depot: die Linie 74, wie sie im Herbst fuhr, und drei Umleitungen – Oktober, Dezember, Januar. Gezeichnet in Fahrtrichtung, nicht nach Norden. | document | L_C4_AnnexA |
| `ev_c4_shaft` | Litfaßsäule S 2 | Aus dem Gitter am Fuß der Säule steigt warme Luft, mitten im Frost. Hinter den Plakaten eine Stahltür: „Lüftungsbauwerk S 2 – Zutritt nur für Bedienstete der Nebenstelle“. | physical_clue | L_C4_AnnexA |
| `ev_c4_card_de` | Karteikarte Nr. 0417, deutsche Hälfte | Aus einer geplatzten Kiste in den Schnee gefallen: „Lindner, Anna, geb. Kowalenko, * 1926 Charkow. Vermerk C-17: Rückführung Ost. Abgabe Kordon-17, Tür Ost, Kurierwagen C-17/45, Di 18.2., 23.40.“ Darunter: „Kind Ilse, 8 – Verbleib ungeklärt.“ Rechts eine Perforation; die andere Hälfte fehlt. | document | L_C4_AnnexA |
| `ev_c4_card_ru` | Karteikarte Nr. 0417, russische Hälfte | Im Kasten „C-17/45 – annehmen“ auf dem Tisch der Gleisbude: „Kowalenko, Anna Petrowna, 1926, Charkow. 1942 nach Deutschland verbracht. Rückkehrerin. Weiter: Filtrationspunkt Karsk.“ Links eine Perforation. Alexei schreibt die Karte ab und legt sie zurück. | document | L_C4_TunnelsB |
| `ev_c4_stencils` | Schablonen am Farbstand | Blechschablonen in zwei Alphabeten, nach Läufen sortiert: C-17/41 bis /44, abgegriffen. C-17/45 klebt noch nass am Brett. Daneben ein Kübel Rotbraun, die Farbe aller Güterwagen. | physical_clue | L_C4_TunnelsB |
| `ev_c4_wagon_inside` | Wagen 24 318, innen | Zwei Bänke aus rohen Brettern, ein Ofenloch im Dach, ein Eimer. In die Wand geritzt: Namen in zwei Schriften und ein Datum, 21.1. Darunter, kleiner: „Wir sind vierzehn.“ | physical_clue | L_C4_TunnelsB |
| `ev_c4_drawer_s8` | Schublade Süd 8 | Eine Karte für jeden geräumten Haushalt im Abschnitt Süd 8 der Linie 74, zusammen 212. Ein rotes Fähnchen – C-17 – tragen 37 davon. Bei allen 37 fehlt die rechte Hälfte. | document | L_C4_AnnexB |
| `ev_c4_annex_plan` | Lüftungsplan der Nebenstelle Süd | Gerahmt hinter Glas: Lüftungsplan Nebenstelle Süd, 1961, Blatt 3. Drei Schächte, darüber drei Häuserblocks, mit Bleistift schraffiert: „freizumachen“. Im Schriftfeld: gez. K. Adler. | document | L_C4_AnnexB |
| `ev_c4_tube_slip` | Rohrpostzettel der Staatspolizei | In der Kapsel ein Zettel. Absender: Staatspolizeistelle, Kommissar Wendt. „Bis Montag: alle C-17-Haushalte Süd 8, Verbleib der Kinder. Auskunftspersonen namentlich.“ | document | L_C4_AnnexB |
Document art (inspect close-ups, owners env-tunnels `assets/ui/documents/karsk_tunnels_*` and env-annex
`assets/ui/documents/berlin_annex_*`): legible only the story-critical figures, weighbill-style. Freight book: column
„Genehmigt“ with three rectangular cut-outs (14.1. · 21.1. · 28.1.), each beside „Abt. T – mündlich“. Carbon: the
pressure trace „Ю. Архипов“ visible only as a light relief (InspectView shows it with a German caption line). Card No.
0417: a bilingual two-part form, perforated in the middle — German half (left: „Lindner, Anna, geb. Kowalenko … Abgabe
Kordon-17, Tür Ost, Kurierwagen C-17/45, Di 18.2., 23.40 … Kind Ilse, 8 – Verbleib ungeklärt“, the red C-17 tab) and
Russian half (right: „Коваленко Анна Петровна, 1926, Харьков … возвращенка … далее: фильтрационный пункт, Карск“,
stamp „ПРИНЯТЬ“); both halves carry „Nr. 0417“ and the same perforation teeth (the match cut needs them identical,
mirrored). Site plan Süd 8: north up, three rings S 1–S 3 over three blocks, title block „Lageplan Süd 8 · Lüftung ·
gez. K. A.“. Route board: tracing paper, line 74 in Marta's pencil, three loops dated „Okt.“ „Dez.“ „Jan.“, drawn in
driving direction. Annex plan: „Nebenstelle Süd · Lüftung · Blatt 3 · 1961 · gez. K. Adler“, the three blocks hatched
„freizumachen“. Tube slip: typed, the Staatspolizei letterhead neutral (no insignia in the neutral variant; `_hist`
variant may carry the eagle stamp per §12.4).

### 2.6 Flags, events and design notes
No new flags (§1.1). Events appended before `slice_completed`: `c4a_completed`, `c4b_completed`, `c4c_completed`,
`c4d_completed`. Meters written: `evidence_chain` (name_marta), `civilian_welfare` (protect_marta). No combined
morality score.
Design notes for later chapters (STORY_BIBLE §7 planned variables — **not flags this round**, derive them from the
choice history once the Saves-side default fill exists): `witnesses_exposed` += 1 if `c4d_choose = name_marta` (Marta);
`people_protected` += 1 if `protect_marta` (Marta, Ilse, Hanna stay unseen); `marta_trust` +1 / −1 accordingly;
`arkhipov_alerted` stays 0 (Lev's carbons were read, not taken). Hooks for part 2 / Chapter 5 (PLANNED, NOT
IMPLEMENTED): C4_WAGON_45 (Tuesday 23.40: Anna Kowalenko-Lindner and Pjotr Iljin in the same wagon to the filtration
point Karsk), C4_LEV_PROMISE (Alexei promised Lev's name stays out of every paper — the first test of that promise),
C4_MARTA_EXPOSED / C4_MARTA_PROTECTED (Wendt's Monday deadline; Ilse at Marta's, her teacher Hanna Adler), C4_ARKHIPOV
(the signature on the carbons), C4_KONRAD_SIGNATURE (gez. K. Adler on the site plan and the annex plan — he drew the
shafts that needed the evictions).

### 2.7 Puzzles — key/pad/mouse contracts for the UI stream
**`pz_c4_numbers` „Die Nummernkette“ — NEW puzzle UI `TracePuzzle` (Story type `symbol_order`; both engines know only
`symbol_order` / `overlay_alignment`, so the novelty is the UI, as with the Gegenprobe).** Alexei, at the siding.
* Board: a schematic of Service Tunnel 3, left → right: the freight yard, four switch posts W1–W4, the siding. Each
  post has its log line from the switch book (date + remark, no number) and an empty plate hook. Tray: four number
  plates / paint layers in display order. A wagon marker stands at the yard; when a plate is hung it rolls to that post
  and shows the number. „Lampe“ toggles the backlight (Gegenlicht): every plate shows the number under its paint
  (translucent), the side panel lists them as text (accessibility: the lamp may stay on). „Probefahrt“ (check) rolls
  the wagon through all posts; at the first post whose plate does not lie over the previous plate's number (or a plate
  with an older number under it at W1) it stops with the reason; a full chain rolls into the siding → success.
* Posts (fixed, `ui.c4.numbers.post.n` / `log.n`): W1 „Einfahrt Güterbahnhof“ · „19.1. · Einfahrt, leer“ — W2
  „Umsetzgleis“ · „21.1. · Sonderlauf nach Kordon-17“ — W3 „Ausbesserung“ · „28.1. · zurück, in Ausbesserung“ — W4
  „Bereitstellung“ · „15.2. · bereitgestellt, Di 23.40“.
* Plates (symbol → face / under the paint): `n24318` enamel „24 318“ / bare metal · `c1742` stencil „C-17/42“ /
  „24 318“ · `n47702` brush „47 702“ / „C-17/42“ · `c1745` stencil „C-17/45“ (wet) / „47 702“.
* `display_symbols` `["c1745", "n47702", "n24318", "c1742"]` (no plate starts at its own post; the tray
  order is a wrong answer); **solution
  `["n24318", "c1742", "n47702", "c1745"]`**; `clue_item_ids` `["ev_c4_card_ru", "ev_c4_stencils"]`; hint after 2
  failures; unlimited retries; no penalty. Two independent routes to the answer: the under-layers (lamp) and the dates
  (the January courier number C-17/42 is in the C3 intake book; C-17/45 carries Tuesday's chalk).
* Texts: `data/locale/de_c4_ui.json` `ui.c4.numbers.*` (title, subtitle, instruction, posts, logs, plates, under-layers,
  lamp state, wrong `{post} {piece} {under} {prev}`, wrong_first, incomplete, hint, success, buttons Probefahrt ·
  Rückgängig · Neu ordnen · Lampe · Schließen).
* Scene `res://scenes/ui/TracePuzzle.tscn`, script `scripts/ui/trace_puzzle.gd` (extends `ui_modal.gd`, registered in
  c4.json `puzzles`; API like CheckPuzzle: `open(obj_id)`, `signal solved(obj_id)`, `is_open` — checked by
  `tests/test_c3_assets.gd` once the scene exists). **Key contract (the input driver relies on it, = CheckPuzzle + L):** property `is_open`, property
  `symbols` (tray in display order), key **N** (1–4) hangs `symbols[N-1]` on the next empty post, **Backspace** undoes
  the last plate, **R** clears all, **L** toggles the lamp (presentation only), **Enter** checks (submits the post order
  through `Story.solve_puzzle`), **Esc** closes; the first two failures keep the board, the hint appears after
  `hint_after_attempts`; auto-close ≤ 7 s after success (Enter/Esc close at once). **Pad:** D-pad ←/→ select a tray
  plate, A hang it, B undo, X lamp, Y check, Back/Select close; LB/RB = ←/→. **Mouse:** click a plate, then a post (or
  drag & drop); right-click a hung plate returns it; buttons for every key; hover a plate = its under-layer in the side
  panel. Text scale and high contrast like CheckPuzzle (numbers stay ≥ 3 px stroke at ×3).
* Success (de): „Ein Wagen, vier Nummern. Im Januar fuhr er als C-17/42 nach Veltrava, danach stand er als 47 702 „in
  Ausbesserung“ in unseren Büchern. Am Dienstag fährt er als C-17/45.“ (UI string uses „…“ for the quoted status.)

**`pz_c4_routes` „Linie 74“ — overlay UI `RoutePuzzle` (Story type `overlay_alignment`, Konrad's M1 mechanic on new
data).** Konrad, at the tram shelter's lit timetable case (his light table).
* Base sheet: the site plan Süd 8 from the notice (north up), three shaft rings S 1–S 3 (ring marks). Overlay: Marta's
  tracing paper with line 74 and three detour loops (diamond marks at each loop's centre, dated Okt./Dez./Jan.), drawn
  in driving direction — i.e. turned 90° against the plan.
* Grid as BlueprintPuzzle (cells, `snap_tolerance` 0); layout file `assets/ui/documents/berlin_c4_routes.json` (cell
  size, files, landmarks, start) — the puzzle stream may reuse `scripts/ui/blueprint_board.gd`.
* **Start pose `{rotation_steps: 0, offset_x: 0, offset_y: 0}` (wrong); solution `{"rotation_steps": 1, "offset_x": 3,
  "offset_y": -2}`** (one turn clockwise, three cells right, two up); `clue_item_ids` `["ev_c4_notice",
  "ev_c4_route_board"]`; hint after 2 failures; unlimited retries.
* Scene `res://scenes/ui/RoutePuzzle.tscn`, script `scripts/ui/route_puzzle.gd` (`open(obj_id)`, `signal
  solved(obj_id)`, `is_open`). **Key contract (= BlueprintPuzzle):**
  `is_open`; arrows/WASD move one cell (**RIGHT** = offset_x +1, **UP** = offset_y −1), **R** rotates +90°
  (rotation_steps +1 mod 4), **Shift+R** −90°, **Enter** („Abgleichen“) submits `{rotation_steps, offset_x, offset_y}`
  (ints) through `Story.solve_puzzle`, **Esc** closes. **Pad:** D-pad moves, RB/LB rotate, A check, B close.
  **Mouse:** drag the tracing paper (snaps to cells), buttons Drehen · Zurücksetzen · Abgleichen · Schließen. Wrong
  feedback: `ui.c4.routes.wrong_turned` while the rotation is wrong, else `ui.c4.routes.wrong`. Marks are shape-coded
  (ring vs. diamond), colour-independent.
* Success (de): „Drei Umleitungen, drei Schächte. Jede Schleife der Linie 74 führt um ein Haus, unter dem die Nebenstelle
  Luft holt. Geräumt wurde, wo ich die Schächte eingezeichnet habe.“

### 2.8 Dialogues (linear; node ids globally unique; ≤ 140 characters per line; speaker ids in parentheses)
Variant notation as C3P2 §2.8: `· v <condition>: „…“`, first match wins; `choice.c3g = swap_halves` means
`{"choice.c3g_choose": "swap_halves"}`. Base lines marked *(fallback-only)* are heard only on a level start without a
save (A1 / M1 / C3g always set one of the covering conditions). Expressions (`line_expr`) in brackets.
Base texts live in `data/v3/locale_de.json` (`dlg.c4.*`), variants and reactions in `data/locale/de_c4_dialogue.json`.

`dlg_c4a_lev` (objective `c4a_talk_lev`, entry `c4a_lev_01`) — 8 lines:
1. `c4a_lev_01` (lev) [neutral] „Um diese Zeit kommt keiner ins Archiv, Morozov. Nur wer nicht im Dienstbuch stehen will.“ *(fallback-only)* · v irina_trust ≥ 1: „Irina Belova hat gesagt, dass Sie kommen. Und dass man Ihnen trauen kann. Das sagt sie selten.“ · v alexei_secrecy ≥ 1: „Um diese Zeit, Morozov, und allein? Wer allein kommt, will etwas, das nicht im Dienstbuch steht.“
2. `c4a_lev_02` (alexei) [neutral] „Die Frachtbücher vom Januar. Im Regal ist eine Lücke.“
3. `c4a_lev_03` (lev) [neutral] „Die Lücke bin ich. Die Bücher liegen unter meinem Ellbogen. Wer sie will, muss an mir vorbei.“
4. `c4a_lev_04` (alexei) [determined] „Drei Wagen im Januar, umgebucht ohne Zielbahnhof. In Veltrava kamen sie an – als C-17. Die Liste dazu trage ich bei mir.“ · v choice.c3g = swap_halves: „Drei Wagen im Januar, umgebucht ohne Zielbahnhof. In Veltrava hießen sie C-17. Die Liste dazu trägt jetzt ein Deutscher.“ · v choice.c3g = hide_for_elena: „Drei Wagen im Januar, umgebucht ohne Zielbahnhof. In Veltrava hießen sie C-17. Die Liste dazu hängt in einem Mantel, Marke 27.“
5. `c4a_lev_05` (lev) [concerned] „Sie waren in Veltrava und sind zurückgekommen. Das schaffen nicht alle, die über die Linie fahren.“
6. `c4a_lev_06` (alexei) [determined] „Wer hat die Umbuchungen genehmigt, Lev?“
7. `c4a_lev_07` (lev) [concerned] „Spalte ‚Genehmigt‘. Lesen Sie selbst. Ich sage nichts, was man später zitieren kann.“
8. `c4a_lev_08` (alexei, end) [determined] „Dann lese ich, und Sie schweigen. Das können wir beide gut.“

`dlg_c4a_tunnel` (objective `c4a_talk_tunnel`, entry `c4a_tun_01`; grants `ev_c4_tunnel_plan` at the end) — 9 lines:
1. `c4a_tun_01` (alexei) [concerned] „Archipov. Oberst, Transportabteilung. Dreimal dieselbe Hand.“
2. `c4a_tun_02` (lev) [neutral] „Gelesen haben Sie das, nicht ich. Ich hebe nur Durchschläge auf. Einer muss die zweite Ausfertigung behalten.“
3. `c4a_tun_03` (alexei) [determined] „Über die Hauptstrecke sind die Wagen nie gefahren. Im Stellwerksbuch fehlen sie, ich habe nachgesehen.“
4. `c4a_tun_04` (lev) [neutral] „Weil sie unten fahren. Dienststollen drei, gebaut einundvierzig für den Luftschutz. Er läuft unter dem ganzen Güterbahnhof durch.“
5. `c4a_tun_05` (alexei) [surprised] „Und wohin?“
6. `c4a_tun_06` (lev) [concerned] „Zu einem Gleis, das in keinem Plan steht. Dort bekommen die Wagen neue Nummern. – Hier, der alte Stollenplan.“
7. `c4a_tun_07` (alexei) [surprised] „Warum geben Sie mir das?“
8. `c4a_tun_08` (lev) [concerned] „Weil ich alt bin und Sie nicht. Und weil mein Name in keinem Papier stehen wird, Morozov. In keinem.“ · v alexei_secrecy ≥ 1: „Weil Sie schweigen können, das sieht man. Und weil mein Name in keinem Papier stehen wird, Morozov. In keinem.“
9. `c4a_tun_09` (alexei, end) [determined] „In keinem. Mein Wort darauf.“

`dlg_c4b_marta` (objective `c4b_talk_marta`, entry `c4b_mar_01`; grants `ev_c4_route_board` at the end) — 13 lines:
1. `c4b_mar_01` (marta) [neutral] „Die 74 fährt erst in sieben Minuten, der Herr. Und warm ist es drinnen auch nicht.“
2. `c4b_mar_02` (konrad) [neutral] „Ich will nicht mitfahren. Ich bin Zeichner beim Generalbauamt. Diese Schleife hier ist neu.“ *(fallback-only)* · v konrad_evidence ≥ 1: „Ich will nicht mitfahren. Ich bin Zeichner beim Generalbauamt und sammle, was in keinem Bericht steht. Die Schleife ist neu.“ · v office_suspicion ≥ 1: „Ich will nicht mitfahren. Ich bin Zeichner beim Generalbauamt – heute nicht dienstlich. Diese Schleife hier ist neu.“
3. `c4b_mar_03` (marta) [concerned] „Die dritte seit Oktober. Jedes Mal, wenn ein Block geräumt wird, fahre ich einen neuen Bogen drumherum.“
4. `c4b_mar_04` (konrad) [neutral] „Baumaßnahmen. Für die Achse, so steht es im Bescheid.“ · v choice.c3d = admit_plan: „Baumaßnahmen, steht im Bescheid. – Nein. Ich habe aufgehört, Bescheide nachzusprechen.“
5. `c4b_mar_05` (marta) [determined] „Baumaßnahmen nachts um drei? Mit Lastwagen, die nicht vom Bau sind? Ich fahre die erste Bahn, ich sehe, wer abgeholt wird.“
6. `c4b_mar_06` (konrad) [concerned] „Wen?“
7. `c4b_mar_07` (marta) [concerned] „Nummer neun. Lindners. Paul war Schlosser bei uns im Depot. Anna kam aus Charkow, zweiundvierzig, mit einem Transport.“
8. `c4b_mar_08` (konrad) [concerned] „Ich habe die Familie gesehen. Im Januar, bei der Parade. Sie standen vor ihrer eigenen Tür.“
9. `c4b_mar_09` (marta) [concerned] „Am Dritten haben sie Anna geholt. ‚Klärung der Staatsangehörigkeit.‘ Paul haben sie ins Depot nach Stettin versetzt.“
10. `c4b_mar_10` (konrad) [concerned] „Und das Kind?“
11. `c4b_mar_11` (marta) [determined] „Welches Kind? – Sie fragen viel für einen, der nur zeichnet.“
12. `c4b_mar_12` (konrad) [determined] „Ich habe den Lageplan für diese Räumungen gezeichnet. Süd acht. Ich will wissen, wofür.“ · v choice.c3d = pocket_plan: „Ich habe den Lageplan für diese Räumungen gezeichnet. Und einen Raum an der Linie. Ich will wissen, wofür.“
13. `c4b_mar_13` (marta, end) [determined] „Dann nehmen Sie das. Meine Linie, wie sie im Herbst fuhr und wie heute. Machen Sie sich selbst ein Bild, Herr Zeichner.“

`dlg_c4b_ilse` (objective `c4b_talk_ilse`, entry `c4b_ils_01`) — 12 lines:
1. `c4b_ils_01` (konrad) [determined] „Ihre drei Umleitungen liegen genau über drei Schächten. Unter dieser Schleife ist eine Dienststelle.“
2. `c4b_ils_02` (marta) [concerned] „Eine Dienststelle. Und damit die Luft kriegt, haben sie Nummer neun ausgeräumt.“
3. `c4b_ils_03` (konrad) [concerned] „Und die Akten der Leute sind mit nach unten gegangen. ‚Vorgang an Nebenstelle Süd‘, steht im Bescheid.“
4. `c4b_ils_04` (marta) [concerned] „Dann wissen die da unten, dass Lindners eine Tochter haben.“
5. `c4b_ils_05` (konrad) [neutral] „Das Mädchen in Ihrer Bahn. Letzte Bank, den Ranzen auf dem Schoß – sie gibt ihn nicht aus der Hand.“
6. `c4b_ils_06` (marta) [concerned] „Ilse. Acht Jahre. Offiziell ist sie bei einer Tante in Stettin. In Wahrheit schläft sie bei mir, und morgens fährt sie mit.“
7. `c4b_ils_07` (konrad) [neutral] „Und die Schule?“
8. `c4b_ils_08` (marta) [neutral] „Die Lehrerin weiß Bescheid. Ein Fräulein Adler. Sie lässt Ilse vor der Stunde in die Klasse, wegen der Kälte.“
9. `c4b_ils_09` (konrad) [surprised] „Hanna.“
10. `c4b_ils_10` (marta) [surprised] „Sie kennen sie?“
11. `c4b_ils_11` (konrad) [concerned] „Sie ist meine Schwester.“
12. `c4b_ils_12` (marta, end) [determined] „Dann wissen Sie jetzt, was auf dem Spiel steht. Was Sie da unten finden, will ich hören. Meinen Namen hört dort keiner.“

`dlg_c4c_lev` (objective `c4c_talk_lev`, entry `c4c_sid_01`) — 12 lines:
1. `c4c_sid_01` (lev) [concerned] „Vierzehn, mit einem Nagel geritzt. Damit es einer liest. – Ich kenne solche Bretter, Morozov.“
2. `c4c_sid_02` (alexei) [neutral] „Von wo?“
3. `c4c_sid_03` (lev) [concerned] „Dreiundfünfzig, nach dem Waffenstillstand. Gefangenenaustausch an der Linie. ‚Heimkehrer‘ stand mit Kreide auf dem Wagen.“
4. `c4c_sid_04` (alexei) [neutral] „Sie sind nach Hause gekommen.“
5. `c4c_sid_05` (lev) [concerned] „Nach Karsk. Filtrationspunkt, Gleis neun. Wer zwölf Jahre bei den Deutschen war, muss erklären, warum er noch lebt.“
6. `c4c_sid_06` (alexei) [concerned] „Auf der Karte steht derselbe Ort. Filtrationspunkt Karsk. Für Anna Kowalenko.“
7. `c4c_sid_07` (lev) [concerned] „Die Deutschen haben sie zweiundvierzig geholt. Jetzt holen wir sie zurück – und fragen sie, warum sie mitgegangen ist.“
8. `c4c_sid_08` (alexei) [determined] „Am Dienstag. In diesem Wagen. Und Pjotr mit ihr.“ *(fallback-only)* · v choice.c3g = split_by_language: „Am Dienstag, in diesem Wagen. Pjotr steht auf derselben Liste – ich trage sie bei mir.“ · v choice.c3g = swap_halves: „Am Dienstag, in diesem Wagen. Und Pjotr mit ihr. Seinen Namen trägt jetzt ein Deutscher durch Berlin.“ · v choice.c3g = hide_for_elena: „Am Dienstag, in diesem Wagen. Und Pjotr mit ihr. Seine Liste hängt in Veltrava in einem Mantel.“
9. `c4c_sid_09` (lev) [concerned] „Hören Sie auf mit Namen, Morozov. Namen sind das, was die da oben sammeln.“
10. `c4c_sid_10` (alexei) [determined] „Dann sammle ich Nummern. Ein Wagen, vier Nummern seit Januar. Das kann man zählen, Lev.“ · v alexei_konrad_trust ≥ 2: „Dann sammle ich Nummern. Und in Berlin sammelt einer die Karten dazu. Zusammen kann man das zählen, Lev.“
11. `c4c_sid_11` (lev) [neutral] „Zählen. Und wem zeigen Sie es? – Gehen Sie, bevor die Schicht kommt. Sonntags streichen sie ab acht.“
12. `c4c_sid_12` (alexei, end) [determined] „Ich gehe. Und vor Dienstag komme ich wieder.“

`dlg_c4d_counter` (objective `c4d_talk_registrar`, entry `c4d_cnt_01`) — 11 lines:
1. `c4d_cnt_01` (registrar) [neutral] „Nebenstelle Süd, Auskunft und Abgleich. Sie sind früh dran, Herr …?“
2. `c4d_cnt_02` (konrad) [neutral] „Adler, Generalbauamt. Bauaufnahme der Lüftung, Blatt drei. Für die Schachtplanung brauche ich eine Haushaltsakte.“
3. `c4d_cnt_03` (registrar) [neutral] „Adler. Lüftung, Blatt drei – Ihr Name steht auf unserem Plan an der Wand. Welche Akte?“ · v kessler_alerted ≥ 1: „Adler – Herr Kessler hat Sie dem Amt empfohlen. Zuverlässig, schreibt er. Welche Akte?“ · v office_suspicion ≥ 1: „Adler. Nach Ihnen hat Ihr Amt neulich gefragt. Na, Lüftung ist Lüftung. Welche Akte?“
4. `c4d_cnt_04` (konrad) [neutral] „Lindner, Haus Nummer neun, Süd acht. Ich muss wissen, wer dort wohnte. Wegen der Schachtwand.“
5. `c4d_cnt_05` (registrar) [neutral] „Lindner. Rotes Fähnchen, C-17. Die Akte ist vollständig, bis auf das Kind. Ilse, acht Jahre. Verbleib ungeklärt.“
6. `c4d_cnt_06` (konrad) [neutral] „Für die Schachtplanung genügt die Belegung. Wer wann ausgezogen ist.“
7. `c4d_cnt_07` (registrar) [neutral] „Akten mit C-17 gebe ich nur gegen eine Auskunftsperson heraus. Einen Anwohner, der die Belegung bestätigt.“
8. `c4d_cnt_08` (konrad) [concerned] „Ich habe mit einer Anwohnerin gesprochen.“
9. `c4d_cnt_09` (registrar) [neutral] „Dann nennen Sie mir ihren Namen. Wer Ihnen von Lindners erzählt hat, weiß auch, wo das Kind ist.“
10. `c4d_cnt_10` (konrad) [determined] „Das Kind interessiert das Generalbauamt nicht.“
11. `c4d_cnt_11` (registrar, end) [neutral] „Aber uns, Herr Adler. Name und Anschrift, hier auf das Formular. Ordnung muss sein – auch hier unten.“

Voice notes: Lev — tired, exact, ironic in self-defence, never a mouthpiece; Marta — Berlin-direct, warm, practical,
protective (she lies once, „Welches Kind?“, and the player should feel why); Fengler — polite procedure, never a
villain's speech („Ordnung muss sein – auch hier unten.“). Lines c4c_sid_05/07 keep the asymmetry explicit: the Reich
deported Anna as a forced labourer, the Soviet side will punish her for having survived it — two different apparatuses,
no equation.

### 2.9 Cinematics (data/v3/cinematics.json; `LOCKED_CINEMATICS` extended — validator list only)
| id | trigger | skip | shots (duration) | scene (cine stream) |
|---|---|---|---|---|
| `LS_C4_Homeward` | event `c3g_completed` (after `LS_C3_Halves`) | visual_only | w1 Veltrava station at first light: two trains on opposite platforms; Alexei boards the eastbound, Konrad the westbound, each with his half of the file under the coat (5 s) · w2 Split windows: Alexei's train crosses the snow plain toward the cooling towers of Karsk, Konrad's passes under the dome of the Great Hall (4 s) · w3 Karsk freight yard before dawn, the repaired signal shows green; Alexei walks to the lit cellar window of the freight office (5 s) — ≈ 14 s | `res://scenes/cinematics/ch4_homeward/Ch4Homeward.tscn` |
| `LS_C4_Number` | event `c4a_completed` | visual_only | n1 Service tunnel 3: Alexei's lamp along the planks of a wagon; fresh red-brown paint, a stencil still taped on: C-17/45, a drip runs down; chalk beside it: Tuesday 23.40 (4 s) · n2 Extreme close-up of the stencilled 45 (match cut) (1.5 s) · n3 Berlin at dawn: the same C-17/45 stencilled on crates at a loading hatch; a truck's tail lights; the stack goes down a shaft (4 s) · n4 The tram loop at the cleared block: the first tram of line 74 rings and stops; Konrad at the shelter; control to Konrad (3.5 s) — ≈ 13 s | `res://scenes/cinematics/ch4_number/Ch4Number.tscn` |
| `LS_C4_Card` | event `c4b_completed` | visual_only | c1 Konrad lifts a card from the snow beside a split crate; his thumb along the perforated edge, No. 0417 (3.5 s) · c2 Close-up of the perforation (match cut) (1.5 s) · c3 Karsk siding office: Alexei's fingers along the other perforated half, the same No. 0417; a kerosene lamp, stencils on the wall (4 s) · c4 Alexei looks up at the wagon outside the window; control to Alexei (2 s) — ≈ 11 s | `res://scenes/cinematics/ch4_card/Ch4Card.tscn` |
| `LS_C4_Stamp` | event `c4c_completed` | visual_only | s1 Siding office: Alexei copies the card into his notebook; Lev slides the Russian half back into the box C-17/45 – accept (3.5 s) · s2 Close-up: the stamp ACCEPT in Cyrillic beside the box (match cut) (1.5 s) · s3 Berlin annex counter: the registrar's stamp comes down, DISPATCH, on another card (4 s) · s4 Konrad at the foot of the shaft ladder between the card cabinets, the German half in his coat; control to Konrad (2 s) — ≈ 11 s | `res://scenes/cinematics/ch4_stamp/Ch4Stamp.tscn` |
| `LS_C4_Voices` | event `c4d_completed` | visual_only | v1 Berlin morning: Konrad climbs out of the door in the advertising column, the Lindner file under his coat or empty-handed (per the c4d choice) (5 s) · v2 Marta's tram leaves the loop, Ilse at the last window; one ring of the bell, or two and Konrad raises his hand (per the c4d choice) (5 s) · v3 Karsk: Alexei and Lev climb out of the cellar into the dark yard under the green signal; Alexei's notebook with four numbers (5 s) · v4 The siding: wagon C-17/45 alone under a work lamp; the lamp goes out (5 s) · v5 Black; caption: Tuesday, 23.40, wagon C-17/45 (4 s) — ≈ 24 s | `res://scenes/cinematics/ch4_voices/Ch4Voices.tscn` |
Inner lines and captions (`data/locale/de_c4_cinematics.json`, chosen by `configure(ctx)` from `ctx.choices`):
`cin.c4.homeward.place` „Karsk, Sonntag, 16. Februar 1964, 4.40 Uhr.“ · `cin.c4.homeward.alexei.split` „Die russischen Blätter. Pjotrs Name liegt unter meinem Mantel.“ · `cin.c4.homeward.alexei.swap` „Die deutschen Blätter. Ich lese sie langsam. Pjotrs Namen trägt er.“ · `cin.c4.homeward.alexei.elena` „Pjotrs Liste hängt in einem Mantel in Veltrava. Ich habe nur die Zahlen.“ · `cin.c4.number.karsk` „Karsk, 7.10 Uhr.“ · `cin.c4.number.berlin` „Berlin, 5.10 Uhr.“ · `cin.c4.number.alexei` „Fünfundvierzig. Der nächste Lauf. Die Farbe ist noch nass.“ · `cin.c4.card.konrad` „Lindner, Anna. Die andere Hälfte ist schon unterwegs.“ · `cin.c4.card.karsk` „Karsk, 7.30 Uhr.“ · `cin.c4.stamp.lev` „Wenn die Karte fehlt, suchen sie zuerst bei mir.“ · `cin.c4.stamp.berlin` „Berlin, 6.00 Uhr.“ · `cin.c4.voices.konrad_name` „Die Akte Lindner, mit allen Unterschriften. Und mit Martas Namen darin.“ · `cin.c4.voices.konrad_protect` „Keine Akte. Aber morgen früh sitzt Ilse wieder bei Hanna in der Klasse.“ · `cin.c4.voices.alexei` „Vier Nummern, ein Wagen. Und Levs Name auf keinem Papier, das ich trage.“ · `cin.c4.voices.tuesday` „Dienstag, 23.40 Uhr. Wagen C-17/45.“
Rules (§12.5 + the C3 cinematic base `scenes/cinematics/ch3_common/c3_cinematic.gd`): every frame a pure function of t,
`skip()` idempotent, reduced_motion halves travel and softens flashes; match cuts are hard cuts on matched shapes
(number → number, perforation → perforation mirrored, stamp → stamp) with a 2-frame white-free dip at most; the two
cities keep their own palettes (Karsk: kerosene amber + red-brown paint; Berlin: dawn blue + fluorescent green) so the
cut reads at a glance; no violence shown, nobody inside a wagon shown — only the traces. Homeward chooses Alexei's inner
line by `ctx.choices.c3g_choose`; Voices chooses Konrad's by `ctx.choices.c4d_choose` (name_marta: the file under the
coat, one bell; protect_marta: empty hands, two bells, Konrad raises his hand). Every scene must also run with a
context that lacks the later choices (`tests/test_c3_assets.gd` configures all cinematics with a c3b-level context):
read `ctx.choices.get(...)` with a default.

---------------------------------------------------------------------------------------------------------
## 3. Presentation layer — `data/chapters/c4.json` (ChapterExt merges every file in `data/chapters/`)
`levels`: TunnelsA/B → `res://scenes/levels/L_C4_Tunnels.tscn`, AnnexA/B → `res://scenes/levels/L_C4_Annex.tscn` ·
`entry_spawn` per scene (§2.1) · `chapter_cards` for all four scenes [`ui.chapter_c4`, `world.c4X.title`] (every scene
is a level load into another city; the card orients the player after the match cut) · `palettes.tunnels`,
`palettes.annex` (placeholder ramps — the env streams refine them) · `grades.tunnels`, `tunnels_siding`, `annex_loop`,
`annex` · `switches` (partner none + per-scene `ambience` / `music` / `grade`, read by `Game._scene_audio`) ·
`line_expr` (every C4 node), `line_variants`, `choice_text`, `reactions` · `puzzles` {`c4b_solve_routes`:
`RoutePuzzle.tscn`, `c4c_solve_numbers`: `TracePuzzle.tscn`} · `cinematics` (§2.9 paths) · `looks` / `carry` empty
(clean looks; no soot in Chapter 4). Texts: `de_c4_dialogue.json` (variants, reactions), `de_c4_cinematics.json`,
`de_c4_ui.json` (puzzle UIs, memories, task places), `de_c4_characters.json` (new names/roles).
Until a UI or cinematic scene exists, ChapterExt reports it missing and the director falls back (puzzle: the generic
blueprint UI; cinematic: skipped) — reported as pending, like round 8.

---------------------------------------------------------------------------------------------------------
## 4. Levels and hotspots (art ↔ content contract)
Both levels: side view like the registry, 1920×360, `mode = "side"`, feet line y 300, walk band y 296–306 (x 18–1902),
everything painted stands behind it (props `base_y` ≤ 294), foreground layer below y 318. Two walk areas per file,
separated by a permanent blocker (`scene.json` `"blockers"`). The art streams need the gated-art features of
`scripts/levels/c3p2_archive/registry_level.gd` (`blockers`, `after` / `until` / `choice` gates, `looks`): extend it or
factor a shared base in their own script and change the root `script` line of their .tscn (one-line Edit). A memory
of a scene opens at its entry spawn, in its own walk area (registry rule: objectives of earlier scenes always count).

### 4.1 `L_C4_Tunnels` — env `assets/environments/karsk_tunnels/` (scenes A and C)
Karsk, Sunday 16 February 1964, before dawn (A ≈ 4.40, C ≈ 7.30 local time). Rooms left → right:
* 0–700 **Archivkeller der Güterabfertigung** (A): a brick-vaulted cellar under the freight office. Stairs down from the
  office (x 0–60, spawn), shelves of freight books with a three-volume gap (x 90–300), Lev's desk under a green-shaded
  lamp with the January book, the samovar, two tea glasses and the freight office's card index (x 330–480), a light box
  made from an old signal lamp (x 500–540), the stove with its pipe through the vault (x 560–600), the iron door with the
  1941 air-raid sign „Бомбоубежище – Служебный тоннель №3“ (x 640–700). High barred window at the top: snow, the yard
  lamp, the feet of the night shift passing (life strip).
* 700–720 the door wall (blocker `cellar_door`).
* 720–1240 **Dienststollen 3**: single track in a concrete tube, 1941 cage lamps, cable runs, water dripping, a niche
  with an old field telephone, the hand-thrown switch W2 with a lever frame (mini-game spot), arrows „К укрытию“.
* 1240–1920 **Umsetzgleis**: a vaulted hall with two tracks. The siding office (a wooden booth with a window, x
  1290–1390: desk, kerosene lamp, the card box „C-17/45 – принять“, the stamp), the paint stand (x 1440–1500: stencils
  in two alphabets on a board, a bucket of red-brown, brushes), wagon **24 318** on track 1 (x 1550–1740, a two-axle
  covered wagon converted for people: stove-pipe hole, the door half open; on its left side the paint layers and the
  fresh stencil C-17/45 still taped on), a heap of enamel number plates, stove-pipe elbows and bench boards (the
  conversion kit), the exit portal to the main line, gate shut (x ≈ 1880).
Looks: A = kerosene/lamp-green warmth in the cellar; C = cold work lamps, the paint smell as a faint haze, the wagon
under a single bulb. FX: dust motes, dripping water, breath in the cold, trains passing overhead (A: the cellar ambience's own trains; C: a
level train every 20–40 s at −8 dB that waits for the tunnel ambience's train; dust falls from the vault, the lamps
swing ≤ 2°).
Story hotspots (x, 300): `book_shelf` 184 · `desk_book` 372 · `lev_cellar` 428 · `lamp_table` 520 · `tunnel_door` 664 · `office_desk` 1346 · `paint_stand` 1468 · `wagon_side` 1590 · `wagon_door` 1680 · `lev_siding` 1772.
NPC anchors: `lev_cellar` → Lev at (446, 300), facing left, `hide_after` `c4c_inspect_card`; `lev_siding` → Lev at
(1790, 300), facing left, `show_after` `c4a_open_door` (two StoryNPC nodes; only one is ever in the walk area being
played). Spawns: `SP_C4_Stairs` (48, 300) — entry of A · `SP_C4_Office` (1322, 300) — entry of C.
Exploration hotspots (explore stream, `explore_hotspots.json`): keep ≥ 24 px from the story hotspots; A finds x 60–690
(gated `until_objective = c4a_open_door`), C finds x 730–1900 (gated `after_objective = c4a_open_door`).

### 4.2 `L_C4_Annex` — env `assets/environments/berlin_annex/` (scenes B and D)
Berlin, Sunday 16 February 1964, dawn (B ≈ 5.10, D ≈ 6.00). Left → right:
* 0–820 **Wendeschleife Süd 8** (B, exterior, snow): the half-cleared block — house No. 9 with its boarded, sealed door
  and the notice (x 90–150), wallpaper of three storeys on the exposed party wall above, house No. 11 still lived in
  (Marta's window, a lamp); the tram shelter with the lit timetable case (x 250–330); tram 74 standing in the loop (x
  350–600, two-axle motor car, line board „74“, Ilse on the last bench as a life strip, breath on the glass); the
  advertising column **S 2** (x 620–670, posters, warm air from the grate at its foot, steam rising); the shaft's freight
  hatch with a stack of crates stencilled C-17/45, one split open, a lorry's tail lights (x 700–800). Behind: the
  cleared ground, cranes of the axis, the dome of the Great Hall far away in the dawn haze (`_hist` banners per §12.4).
* 820–880 the shaft wall (blocker `shaft_wall`); the ladder shaft is seen in section at the boundary.
* 880–1920 **Nebenstelle Süd der Zentralen Erfassungsstelle** (D, underground, fluorescent): the foot of the shaft
  ladder (x 880–930, spawn), the machine room behind a grille (x 940–1060: two huge fans, the air the column breathes),
  the card hall (x 1060–1500: steel cabinets to the ceiling, sliding ladders, the drawer bank „Süd 1 … Süd 12“ — drawer
  Süd 8 at x ≈ 1232), the framed ventilation plan (x ≈ 1376), the pneumatic-tube station (x ≈ 1548), the counter
  „Auskunft · Abgleich“ with stamps, forms and a perforating machine (x 1650–1760; Fengler behind it), the typists'
  room behind glass (life strips, `clerk` variants), the door to the Staatspolizei corridor with a guard (x ≈ 1868).
Looks: B = blue dawn, warm windows, sodium lamp at the loop; D = flat fluorescent green-white, no daylight, the city as
a rumble. FX: snow and steam (B), dust in the fan light, a capsule shooting through the tubes (D).
Story hotspots (x, 300): `door_9` 118 · `timetable_case` 292 · `marta_tram` 404 · `column_s2` 646 · `loading_hatch` 762 · `drawer_s8` 1232 · `plan_wall` 1376 · `tube_station` 1548 · `registrar_counter` 1716.
NPC anchors: `marta_tram` → Marta at (422, 300), facing left · `registrar_counter` → Fengler at (1734, 276) behind
the counter (hotspot (1716, 300) + `hotspot_offset` (18, −24); the y-sorted prop `counter_front`, base_y 292, hides
his legs while the player passes in front), facing left · `guard_annex` → the existing `guard` at (1868, 300), `look_at_player = false`. Ilse (existing `berlin_child`
sheet) appears only as a life strip in the tram (no dialogue, never in the walk band). Spawns: `SP_C4_Shelter` (236,
300) — entry of B · `SP_C4_Ladder` (902, 300) — entry of D.
Exploration hotspots: B finds x 30–810 (`until_objective = c4b_inspect_crates`), D finds x 890–1900
(`after_objective = c4b_inspect_crates`); ≥ 24 px from the story hotspots.

---------------------------------------------------------------------------------------------------------
## 5. Cast
Existing ids first: `alexei`, `konrad` (protagonists, base looks), `guard` (annex door), `berlin_child` (Ilse, life strip
only — the child of the cleared family seen in LS_M1_Hall), `clerk` (typists, life strips). Mentioned, not shown: Irina
Belova, Emil Hartmann, Hanna Adler, Anna and Paul Lindner, Kommissar Ludwig Wendt (the tube slip), Oberst Juri Archipov
(the carbons), Pjotr Iljin, Elena Weiss.
New characters (cast stream; sheet with the side rows of the other side-level NPCs + portrait with the four
expressions neutral / concerned / determined / surprised; names in `data/locale/de_c4_characters.json`):
| id | name (de) | role | age | look / costume | voice |
|---|---|---|---|---|---|
| `lev` | Lev Sokolov | archive clerk of the Karsk freight office; Soviet POW 1941–53, returned in the armistice exchange, filtration point Karsk, eight years labour camp | 54 | thin, slightly stooped; grey stubble; round steel glasses taped at the hinge; grey quilted vest over a darned cardigan, black sleeve protectors, felt boots with galoshes, a pencil behind the ear; a missing fingertip on the left hand | tired, exact, dry irony; never raises his voice |
| `marta` | Marta Vogel | tram driver, line 74, lives in house No. 11; keeps the block alive; hides Ilse | 34 | dark-blue driver's coat with brass buttons, a numbered „74“ cap badge (no insignia), knitted grey scarf, fingerless gloves, leather money satchel on a strap, lace-up boots; short dark-blond hair under the cap, red cheeks, quick eyes | Berlin-direct, warm, practical, a dry laugh |
| `registrar` | Registrator Fengler | „Auskunft und Abgleich“, Nebenstelle Süd of the Zentrale Erfassungsstelle | ≈ 50 | grey dust coat over a suit, sleeve protectors, rimless glasses, precise side parting, a rubber stamp in his hand; a small round lapel badge without insignia (may derive from the `clerk` sheet) | polite, bored, procedural |
Priority: `lev` and `marta` (portraits needed in the main path), then `registrar`.

---------------------------------------------------------------------------------------------------------
## 6. Exploration brief (§12, §12.8, §12.9) — owner: exploration stream
Files `data/explore/c4_tunnels.json`, `c4_annex.json` (areas `karsk` / `berlin`, ids `karsk.tunnels.<name>`,
`berlin.annex.<name>`), strings `data/locale/de_explore_c4.json`, history `data/explore/c4_history_soviet.json` /
`c4_history_reich.json` + `data/locale/de_history_c4.json`, hotspots in the two envs' `explore_hotspots.json`. **Explore
entries of the shared levels use `"level": "L_C4_TunnelsA"` / `"L_C4_AnnexA"`** (ChapterExt.level_key). Finds speak in
the voice of the protagonist who can reach them and are `gated_interactable`s per walk area (§4) with the
`memory_scenes` rule of `scripts/ui/minigames/kartei_spot.gd` (inside a memory the remembered scene decides).
* Tunnels A (Alexei, cellar): `exp_samovar` (two glasses — Lev always pours one for a visitor who does not come) ·
  `exp_card_index` (the freight office's personnel cards: „Gerassimov, P. – Weichenwärter – auf eigenen Wunsch
  versetzt“, pencilled „fragte nach Wagen 24 318“ — workers who ask are re-booked too) · `exp_lev_photo` (his
  granddaughter with a Leningrad university leaflet; his biography closes the door) · `exp_air_raid_sign` · `exp_stamps`
  (the stamp box: „Umgebucht“, „Leer“, one hook empty) · `exp_stove` · hidden `exp_sugar_mouse`. Chat: Lev after
  `c4a_talk_tunnel` (until `c4a_open_door`).
* Tunnels C (Alexei, tunnel + siding): `exp_field_phone` (1941 field telephone, still live: someone reads out the time) ·
  `exp_lever_frame` (mini-game) · `exp_plate_heap` (a dozen numbers of wagons that „are in repair“) · `exp_stovepipes`
  (the conversion kit: stove-pipe elbows, bench boards, buckets) · `exp_painters_corner` (tea glasses, a newspaper, the
  duty roster of an „Arbeitskolonne“) · `exp_exit_portal` · hidden `exp_child_drawing` (a house scratched into a plank).
* Annex B (Konrad, tram loop): `exp_tram_cab` (Marta's cab: route board hook, thermos, a child's mitten) ·
  `exp_wallpaper` (three storeys of wallpaper on the party wall — three families) · `exp_shelter_poster` („Berlin baut“) ·
  `exp_queue` (early-shift workers waiting, a short overheard exchange) · `exp_house_11` (Marta's lit window) · hidden
  `exp_doll_shoe`. Chat: Marta after `c4b_talk_ilse` (until `c4b_inspect_crates`).
* Annex D (Konrad, annex): `exp_fans` · `exp_perforator` (the machine that splits the C-17 cards: „links Reich, rechts
  Gegenstelle“) · `exp_card_sorter` · `exp_canteen_calendar` · `exp_typists` · hidden `exp_brandt_card` (Konrad's
  colleague Brandt — the empty desk of the Bauarchiv — „überstellt Staatspolizei, März 1963“). Chat: the guard (short,
  any time in D).
* **Side tasks (one per level, all steps inside ONE walk area so a missed scene can never strand a task):** tunnels
  (C, siding) „Wir sind vierzehn“ — read every name scratched into wagon 24 318 (under the bench, on the roof beam, on
  the door rail, behind the stove pipe) and take them to Lev: „Vierzehn. Jetzt stehen sie in zwei Papieren.“ — quiet,
  no names of real persons, no spectacle; annex (B, tram loop, after `c4b_talk_ilse`) „Ilses Ranzen“ — Marta asks for
  Ilse's satchel from the sealed flat of No. 9 → the courtyard window → the satchel (Ilse's drawing inside: house No. 9
  with all windows lit) → back to the tram. Rewards are human beats, no new history card.
* **Mini-games (§12.8, one per level):** tunnels C „Der Hebelrahmen“ at `exp_lever_frame` — a 1941 mechanical lever
  frame: set points and lock the route before the signal lever may move (fictional teaching frame, no failure beyond
  retry); annex B „Die Schleifenweiche“ — the loop's frozen point: Marta's point iron, salt, the right moment between
  two cars (forgiving timing) — or D „Die Lüftungsklappen“ (balance three flaps so the machine-room alarm stops);
  keyboard + pad + mouse, `demo_solve()` by synthetic keys, `ctx.auto`.
* **Real-history cards (sober, sourced, 450–800 characters, fact-checked like C3; never on a joke spot):** tunnels —
  `hist.soviet.order_270` (Order No. 270 of 16 Aug 1941: captured soldiers treated as traitors, families of officers
  liable to arrest; published 1988) at `exp_lev_photo`; `hist.soviet.volga_germans` (decree of 28 Aug 1941, deportation
  of the Volga Germans in freight trains, labour army, special settlement until 1955; the collective accusation was
  withdrawn only on 29 Aug 1964, return to the Volga not allowed) at `exp_stovepipes`; optional `hist.soviet.propiska`
  (internal passport and residence permit since 1932; collective farmers without passports until 1974) at
  `exp_card_index`. Annex — `hist.reich.ostarbeiter` (civilian forced labourers from the occupied Soviet territories,
  ≈ 2.75 million; the „OST“ badge decree of 20 Feb 1942; many met suspicion and filtration after their return) at
  `exp_tram_cab` or `exp_wallpaper`; `hist.reich.denunciation` (the Gestapo's small staff depended on reports from the
  population — Gellately 1990, Mallmann/Paul 1991) at the counter area (D); optional `hist.reich.hollerith` (punched-card
  machines of DEHOMAG in the 1939 census; Aly/Roth 1984) at `exp_card_sorter`. Facts are checked by the explore stream;
  topics may be swapped for better-sourced ones with a note.

**As built (round 9) — departures from this brief, recorded by the lead:**
- Annex side task „Ilses Puppe“ instead of „Ilses Ranzen“ (Ilse already holds her satchel in `dlg.c4.ils_05`): Marta
  asks → the 1941 cellar breakthrough into No. 9 (`doll_cellar`) → back to Marta; the find image is Ilse's crayon drawing.
  The tunnels task „Wir sind vierzehn“ is built as briefed (four scratched names + Lev; added in the review, compl-02).
- Mini-games: „Der Hebelrahmen“ (tunnels C) and „Die Lüftungsklappen“ (annex D, added in the review, compl-01);
  „Die Schleifenweiche“ was not built.
- History cards: `hist.soviet.order_270`, `hist.soviet.special_settlements` (replaces `volga_germans`),
  `hist.reich.ostarbeiter`, `hist.reich.denunciation` (added in the review, compl-05); the optional `propiska` and
  `hollerith` cards were not built.
- Finds follow the painted art: annex B `exp_queue` and annex D `exp_card_sorter`, `exp_canteen_calendar`,
  `exp_typists` were replaced by `tram_rear`, `axis_view` (B) and `household_index`, `card_cart`, `waiting_bench` (D);
  tunnels C gained `cables` and `wagon_marks`. Counts: tunnels 22 entries, annex 18 (incl. chats and task steps).

## 7. Memories (§12.10)
The scene table is automatic (four new memory scenes, chapter 4 — „Kapitel 4 · Stimmen unter Beton“):
| memory scene | protagonist | unlocked by | place (de) | date (de) |
|---|---|---|---|---|
| `L_C4_TunnelsA` | alexei | `c4a_completed` | „Archivkeller der Güterabfertigung, Karsk“ | „Februar 1964“ |
| `L_C4_AnnexA` | konrad | `c4b_completed` | „Wendeschleife Süd 8, Berlin“ | „Februar 1964“ |
| `L_C4_TunnelsB` | alexei | `c4c_completed` | „Umsetzgleis unter dem Güterbahnhof, Karsk“ | „Februar 1964“ |
| `L_C4_AnnexB` | konrad | `c4d_completed` | „Nebenstelle Süd, Berlin“ | „Februar 1964“ |
Texts in `data/locale/de_c4_ui.json`: `ui.memories.decided.name_marta` „Hier habe ich Marta Vogels Namen genannt – für die Akte Lindner.“ · `ui.memories.decided.protect_marta` „Hier habe ich keinen Namen genannt. Die Akte blieb im Schrank.“ · `ui.memories.echo.c4b_solve_routes` „Drei Umleitungen, drei Schächte. Martas Linie hatte die Räumungen aufgezeichnet, bevor ich sie verstanden habe.“ · `ui.memories.echo.c4c_solve_numbers` „Ein Wagen, vier Nummern. Unter jeder Farbe die vorige. Am Dienstag fährt er wieder.“. Prints `assets/ui/memories/L_C4_*.png` come from the lead (capture → 
`gen_ui_memories.py`). Inside a memory each scene opens in its own walk area with its own protagonist; story NPCs of the shared
levels follow the remembered state (the levels' `objective_done` rule: only objectives of earlier scenes count), so Lev
stands in his cellar in a memory of A and at the siding in a memory of C (round-9 fix, `tests/test_memory_npcs.gd`).

## 8. Audio brief (cast + audio stream)
`amb_karsk_cellar` (stove ticks, a wall clock, the samovar, trains far above, wind at the barred window) ·
`amb_karsk_tunnel` (drips, the vault's echo, a fan in an air shaft, shunting overhead, the hum of a work lamp) ·
`amb_berlin_loop` (dawn, snow, the trolley wire's hum, the first lorry, crane chains of the axis, a tram bell far off) ·
`amb_berlin_annex` (two huge fans, tube capsules, muffled typewriters, the street above as a rumble); music
`mus_c4_karsk` (sparse low strings, a bayan breath), `mus_c4_berlin` (cool, mechanical pulse), `mus_c4_voices` (the
closing: both themes on one clock); cinematic cues: stencil brush, card tear, stamp thump, tram bell (existing
`tram_bell` sfx may be reused), a train overhead. Original, deterministic generators (`tools/audiogen/c4_audio.py`);
missing files are tolerated by `Audio`.

---------------------------------------------------------------------------------------------------------
## 9. Tests and drivers (story stream)
* `tests/test_c4_routes.gd`: every combination a1 × m1 × c3a × c3b × c3d × c3g × c4d (288 routes) through the Story API
  (chain, protagonists, events, meters, items, cinematic order, finale); gating step by step through the 22 C4
  objectives (locks swept after every step); both puzzles (wrong payloads keep the state; the solutions solve);
  save/load at every C4 step byte-identical; round-8 saves continue into Chapter 4; line variants per route (no dead
  variant, fallback-only bases never heard); presentation contract (c4.json, switches, grades, cinematics registered,
  LOCKED_CINEMATICS); the two level shells (hotspots and spawns on the floor, one interactable per objective, npc ids);
  German typography and ≤ 140 characters per spoken line; the end card lists the seven decisions in story order.
* `tests/support/test_kit.gd` plays the extended chain (`STAGES` … c4a–c4d, `DEFAULT_CHOICES.c4d`, `C4_ROUTES`,
  `C4_NUMBERS`); route / memories / parity / integrity tests that encode the old chain get minimal edits;
  `tests/test_save_rebase_r8.gd` gains the round-8 form „montage after c3g_completed“ → `L_C4_TunnelsA`.
* `tests/reference/make_python_reference.py`: routes cover all seven choices × skip/play (576 keys), the verified-route
  trace runs through Chapter 4, a `chapter4_with_noise` trace, corpus checkpoints in Chapter 4.
* Drivers: `--autoplay=<a1>,<m1>,<c3a>,<c3b>,<c3d>,<c3g>,<c4d>` and `--inputplay=…` (same spec; default c4d =
  `name_marta`, the first option like every other default); saves in `user://e2e/saves`; inputplay solves RoutePuzzle by keys (Enter on the start pose = one
  wrong attempt, then R, →×3, ↑×2, Enter) and TracePuzzle by number keys (tray order 1-2-3-4 = wrong, Backspace ×4, the
  solution by index, L once, Enter); „Fortsetzen“ must resume in `L_C4_AnnexB` before `c4d_choose`. Explore passes at
  every C4 scene start and before `c4a_open_door`, `c4b_inspect_crates`, `c4c_talk_lev`, `c4d_choose` (final passes:
  `c4c_talk_lev` for the tunnels, `c4d_choose` for the annex).
* QUEST_DATABASE §12 is generated by `tools/docs/gen_quest_db_c4.py` (C3's generator keeps §1 FLOW and §11).

## 10. Ownership for the build phase (one owner per file; shared files only by small appended blocks / one-line edits)
| stream | owns |
|---|---|
| story (this contract) | `data/v3/*.json`, `data/chapters/c4.json`, `data/locale/de_c4_{dialogue,cinematics,ui,characters}.json`, `scenes/levels/L_C4_Tunnels.tscn` / `L_C4_Annex.tscn` (node list), the placeholder `scene.json` of both envs until the art streams replace them, `LOCKED_CINEMATICS` in `scripts/story/story_engine.gd`, `scripts/core/autoplay.gd`, `scripts/core/inputplay.gd`, the end card's decision list, `tests/test_c4_routes.gd`, `tests/support/test_kit.gd`, `tests/reference/**`, `tools/docs/gen_quest_db_c*.py`, `documentation/QUEST_DATABASE.md` |
| env-tunnels | `tools/pixelgen/env_c4_tunnels*.py`, `assets/environments/karsk_tunnels/**` (replaces the placeholder scene.json, keeps every name of §4.1), `assets/ui/documents/karsk_tunnels_*`, its level script (e.g. `scripts/levels/c4/tunnels_level.gd`; root `script` line of `L_C4_Tunnels.tscn`), `tests/test_c4_tunnels_art.gd`, `asset_manifest_parts/env_c4_tunnels.md` |
| env-annex | `tools/pixelgen/env_c4_annex*.py`, `assets/environments/berlin_annex/**` (keeps every name of §4.2), `assets/ui/documents/berlin_annex_*`, its level script (root `script` line of `L_C4_Annex.tscn`), `tests/test_c4_annex_art.gd`, `asset_manifest_parts/env_c4_annex.md` |
| cine | `scenes/cinematics/ch4_{homeward,number,card,stamp,voices}/**`, `tools/pixelgen/env_c4_cine*.py`, `assets/cinematics/ch4/**`, cinematic sound cues (with audio), `tests/test_c4_cinematics.gd`, `asset_manifest_parts/c4_cine.md` |
| puzzle | `scenes/ui/TracePuzzle.tscn`, `scripts/ui/trace_puzzle.gd`, `scenes/ui/RoutePuzzle.tscn`, `scripts/ui/route_puzzle.gd`, `assets/ui/puzzle/c4_*`, `assets/ui/documents/berlin_c4_routes.json` (+ its plan art), `tests/test_c4_puzzle_ui.gd`, `asset_manifest_parts/c4_puzzle.md` |
| cast-audio | `assets/characters/{lev,marta,registrar}/**` via their generators, `tools/audiogen/c4_audio.py`, `assets/audio/amb/amb_{karsk_cellar,karsk_tunnel,berlin_loop,berlin_annex}.wav`, `assets/audio/music/mus_c4_*.wav`, `tests/test_c4_cast_audio.gd`, `asset_manifest_parts/c4_cast_audio.md` |
| explore | `data/explore/c4_*.json`, `data/locale/de_explore_c4.json`, `de_history_c4.json`, the two envs' `explore_hotspots.json`, new mini-game scenes/scripts, Find_/Chat_ nodes appended at the end of the two .tscn Playfields (small Edit insertions), `tests/test_c4_explore.gd`, `asset_manifest_parts/c4_explore.md` |
The evidence board („Die Akte C-17“) reads the C4 items as they are; pairs that belong together on the board: card
halves `ev_c4_card_de` ↔ `ev_c4_card_ru` (No. 0417) · `ev_c4_stencils` ↔ `ev_c4_card_de` (C-17/45) · `ev_c4_cut_signatures`
↔ `ev_c3_intake_book` (C-17/41–43 = the three January wagons) ↔ `ev_timetable` (A1: three wagons re-booked) ·
`ev_c4_carbon` ↔ `ev_c4_cut_signatures` (the cut-out hand) · `ev_c4_notice` ↔ `ev_c4_annex_plan` (gez. K. A. / K. Adler)
↔ `ev_c3_kordon_plan` (gez. K. Adler) · `ev_c4_route_board` ↔ `ev_c4_shaft` · `ev_c4_card_de` ↔ `ev_c3_escort_list`
(Tuesday 23.40, Tür Ost) · `ev_c4_tube_slip` ↔ `ev_c4_drawer_s8`.

## 11. Acceptance criteria (round 9, Chapter 4 part 1)
1. A new game reaches the montage through A1 … C3g and the four C4 scenes; every scene starts in its own city and walk
   area with its protagonist; the end card lists seven decisions in story order.
2. `L_C3_Quay → L_C4_TunnelsA → L_C4_AnnexA → L_C4_TunnelsB → L_C4_AnnexB → L_X1_Montage`; the five C4 cinematics are
   queued at their events (Homeward after Halves) and never block a scene when their scene file is missing.
3. Both puzzles are solvable by keyboard only, by pad only and by mouse only; a wrong answer never changes Story state
   beyond the attempt counter; the hint appears after two failures.
4. Every C4 line variant is heard on some route; every fallback-only base is never heard in normal play; the c4d
   option variants appear on the routes they are written for; every spoken line ≤ 140 characters, German typography.
5. Saves anywhere in C4 load byte-identically and continue; a round-8 autosave on the quay plays on into Chapter 4; a
   round-8 profile snapshot of the quay is re-based to `L_C4_TunnelsA`.
6. No new flag; `flags.json` keeps 16 flags; `LOCKED_CINEMATICS` and the Python reference cover the new data; the unit
   suite is green; the drivers' choice spec takes seven values.
7. Content rules: no glorification, no false equivalence (Lev's and Anna's stories keep the two repressions specific),
   people before slogans, real insignia only as `*_hist` variants via `Symbols.pick()`, no real person named in the
   wagon's scratches, the pre-rename name of the German protagonist never appears.
