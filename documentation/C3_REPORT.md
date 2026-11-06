# C3 REPORT — Kapitel 3 „Der eiserne Frieden“, spielbarer Anfang (Branch `kapitel-3`)

Stand: 2026-11-05, Ende der Cloud-Sitzung (auf Wunsch des Nutzers vorzeitig abgeschlossen). Gebaut in einer Cloud-Sitzung
ohne GPU; alle Bildschirmfotos stammen aus dem echten Spiel über Software-Rendering (Compatibility-Renderer, `xvfb-run`).
Design-Vertrag: `documentation/C3_DESIGN.md` · Änderungen an bestehenden Dateien: `documentation/MERGE_NOTES_C3.md` ·
Architektur: `TECHNICAL_ARCHITECTURE.md` §13 · Offene Textprüfung: `documentation/C3_TEXT_REVIEW.md` ·
Provenienz: `documentation/asset_manifest_parts/c3.md`.

## 1. Was gebaut wurde (alles auf `kapitel-3`, `master`-Stand `2e1ff78` bereits eingearbeitet)
| Bereich | Inhalt | Dateien |
|---|---|---|
| Story-Daten | 2 Szenen (`L_C3_Station`, `L_C3_Hall`), 2 Quests, 13 Ziele, 5 Dialoge (42 Zeilen) mit 16 flag-abhängigen Varianten, 2 Entscheidungen (2 + 3 Optionen) mit Reaktionen, 6 Beweisstücke, 1 Rätsel, 3 Filmsequenz-Einträge, 7 neue Zustandswerte | `data/v3/*.json`, `data/chapters/c3.json`, `data/locale/de_c3_*.json` |
| Ablauf | Kapitel 2 endet weiterhin mit der X1-Montage; danach geht es statt der Endkarte in Kapitel 3 weiter (Bahnhof → Palais); Endkarte und Abspann folgen erst nach Kapitel 3 | `data/v3/scenes.json`, `quests.json` |
| Regie-Erweiterung | `ChapterExt`: Levels, Einstiegspunkte, Kapitelkarten, Paletten/Grades, Zeilenvarianten, Optionstexte, Reaktionen, Rätsel-UIs, §12.5-Filmsequenzen – datengetrieben, Engine-Semantik unverändert | `scripts/core/chapter_ext.gd`, `scripts/actors/story_npc.gd`, `scripts/actors/gated_interactable.gd` |
| Level Bahnhof Veltrava | 2.5D schräg wie Karsk, Alexei spielbar: Ankunft, Kurierwagen 4, Abfahrtstafel, Passkontrolle, Elena im Café; 6 Story-Ziele, 13 Funde, 2 Nebengespräche; 14 Ebenen, 18 Props, Lichter, Schnee/Dampf/Tauben | `scenes/levels/L_C3_Station.tscn`, `assets/environments/veltrava_station/`, `tools/pixelgen/env_veltrava_station*.py`, `env_veltrava_lib.py` |
| Level Palais der Kommission | Seitenansicht wie das Archiv, Konrad spielbar: Kessler, Sitzordnung, Protokollbüro, Rätsel, Kabine 2, erste Begegnung mit Alexei; 7 Story-Ziele, 10 Funde, 2 Nebengespräche; 74 Dateien | `scenes/levels/L_C3_Hall.tscn`, `assets/environments/veltrava_hall/`, `tools/pixelgen/env_veltrava_hall*.py` |
| Rätsel | „Sitzordnung und Dolmetscherprotokoll“ (`pz_c3_protocol`): Namenskarten in Redereihenfolge; Hinweis nach 2 Fehlversuchen; Tastatur/Maus/Controller; Textskalierung 100/125/150 %; Kontrastmodus | `scenes/ui/ProtocolPuzzle.tscn`, `scripts/ui/protocol_puzzle.gd`, `assets/ui/puzzle/c3_*`, `tools/pixelgen/gen_ui_c3.py` |
| Figuren | Elena Weiss, Grenzbeamter, Schaffner, Lidia Voronova, Gerhard Kessler, Frau Brunner, Nils Ekdahl: Sprite-Sheets mit Normal-Maps, Porträts mit 4 Ausdrücken, deterministisch (zweimal byteidentisch gebaut) | `assets/characters/<id>/`, `tools/pixelgen/characters_c3.py`, `chargen_cast_c3.py`, `chargen_portrait_c3.py` |
| Dokumente | Wiegekarte, Abfahrtstafel, Dienstreiseauftrag, Sitzordnung, Dolmetscherprotokoll, Durchschrift (1:1 Pixelkunst, HD-Text darüber) | `assets/ui/documents/veltrava_*` |
| Erkundung | 27 Einträge in Alexeis/Konrads Stimme (12 + 1 geheim + 2 Gespräche am Bahnhof; 10 + 2 im Palais), 3 reale Geschichtskarten: Zwangsrepatriierungen nach Jalta, NKWD-Auslieferungen an die Gestapo 1940, Simultandolmetschen in Nürnberg | `data/explore/veltrava_*.json`, `c3_history_soviet.json`, `c3_history_reich.json`, `data/locale/de_explore_veltrava.json`, `de_history_c3.json` |
| Audio | `amb_veltrava_station` (60 s), `amb_veltrava_palais` (60 s), `mus_veltrava` (90 s, Loop) – synthetisiert, deterministisch, in die Levels eingebunden | `tools/audiogen/c3_audio.py`, `assets/audio/` |
| Hoheitszeichen | Fahnen/Wimpel beider Seiten als neutrale Datei + `_hist`-Variante; `LayerStack.tex()` löst über `Symbols.pick` auf | `assets/environments/veltrava_*/props/flag_*` |
| Tests | Legacy-Suite auf die neue Kette umgestellt, Python-Referenzabgleich auf `data/v3` neu erzeugt, neue Tests `test_c3_routes`, `test_c3_presentation`, `test_c3_assets`, `test_c3_puzzle_ui`; beide E2E-Treiber spielen die ganze Kette | `tests/`, `scripts/core/autoplay.gd`, `inputplay.gd` |
| Doku | `C3_DESIGN.md`, `MERGE_NOTES_C3.md`, `QUEST_DATABASE.md` §C3 (generiert durch `tools/docs/gen_quest_db_c3.py`), `TECHNICAL_ARCHITECTURE.md` §13, Asset-Manifest-Teil | `documentation/` |

## 2. Rückbezüge auf Kapitel 1/2 (QUEST_DATABASE §7.3) – umgesetzt
| Hook | Wirkung in Kapitel 3 |
|---|---|
| `C3_IRINA_WITNESS` (`irina_trust`) | Alexei nennt Irina als Zeugin (Schaffner, Passkontrolle, Elena, Begegnung); Zugfenster-Zeile „Ihr Name fährt jetzt mit“ |
| `C3_ALEXEI_SILENCE` (`alexei_secrecy`) | Alexei bleibt wortkarg; „Niemand dort weiß, dass ich danach frage“; Elena fragt, warum er das einem Fremden erzählt |
| `C3_KONRAD_COPY` (`konrad_evidence`) | Konrad erwähnt die Abschrift (Zugfenster, Ankunft, Begegnung); Option „…und die Abschrift von Emils Vermerk“ |
| `C3_ARCHIVE_ALERTED` (`office_suspicion`) | Kessler: „Ihre Anfrage aus Berlin liegt auf meinem Tisch“; Konrads Gepäck wurde zweimal geöffnet; Option „Den Dienstweg gehen“ |
| `C3_EVIDENCE_BASE` | Beide tragen ihre Hälfte: Wiegekarte/Abfahrtstafel/Reiseauftrag (Alexei), Sitzordnung/Protokoll/Durchschrift (Konrad) |
Neue Werte: `alexei_konrad_trust` (0–5), `elena_trust`, `evidence_chain`, `kessler_alerted` (+ 3 boolesche Marker). Kein Moral-Score.
Der Autoplay-Treiber prüft auf jeder Route, dass die zur Entscheidungskombination passenden Varianten tatsächlich gesprochen wurden.

## 3. Was getestet wurde (Endstand `kapitel-3`)
| Prüfung | Ergebnis |
|---|---|
| `godot --headless --path . --script res://tests/run_all.gd` | **27 Dateien, 223 Fälle, 20 609 Checks – alles grün bis auf 3 Checks in `test_c3_assets.gd`**: die drei Filmsequenz-Szenen fehlen (siehe §4) |
| Referenzabgleich (`test_reference_parity.gd`) | Routen (4 Slice-Kombinationen × alle Kapitel-3-Optionen × play/skip), Legacy-Saves, API-Traces, ~3 000 mutierte Saves gegen den unveränderten Python-Motor auf `data/v3`: 0 Abweichungen |
| Autoplay (Story-API) | PASS für `share_with_irina,preserve_evidence,ask_elena,share_protocol` (skip), `keep_private,request_explanation,note_alone,report_delegation` (skip), `keep_private,preserve_evidence,note_alone,search_elena` (skip), `share_with_irina,request_explanation,ask_elena,report_delegation` (skip + `--autoplay-explore`: alle 27 Funde über die Fund-Ansicht, 19/19 Geschichtskarten), `keep_private,request_explanation,ask_elena,search_elena` (play) – jeweils mit Save/Load in Karsk und im Bahnhof |
| Tastendruck-Durchlauf (`--inputplay=keep_private,request_explanation,note_alone,share_protocol --inputplay-skip`, headless) | **INPUTPLAY_PASS, 261 s**: Menü, Kapitel 1–3 nur per Tastendruck, ein Fund und ein Nebengespräch am Bahnhof, Protokoll-Rätsel (erst falsch, dann richtig), Endkarte, Abspann übersprungen, „Fortsetzen“ landet vor der letzten Entscheidung |
| Bildprüfung | Bahnhof (Kamera 0/640/1280 mit Figuren), Palais (0/640/1280 mit Figuren), Rätsel (offen, gelöst, 125/150 %, Kontrast), Dokumente über die echte Inspektionsansicht, alle Figuren im Lineup und als Porträts – angesehen und mit den Kapitel-1/2-Screenshots verglichen |
| Determinismus | Figuren-, Palais-, Bahnhofs- und Rätsel-Generatoren zweimal gebaut: byteidentisch |

## 4a. Stand nach Runde 7 (auf dem PC, 2026-11-06) – die Punkte 1–6 aus §4 sind erledigt
1. **Filmsequenzen** – fertig: LS_C3_Trains (25,5 s: Konrads Salonwagen, Abgleich durch den Lichtblitz, Alexeis Abteil,
   Morgengrauen über der Brücke), LS_C3_ToHall (6 s), LS_C3_Close (12 s); Grafik `py -3 -P tools/pixelgen/env_veltrava_cine.py`
   → `assets/cinematics/ch3/**` + `layout.json`, Ton `tools/audiogen/c3_cine_audio.py` → `assets/audio/sfx/c3cine_*`;
   `tests/test_c3_cinematics.gd` grün (17 Fälle). Übergang 2→3: X1-Montage → Nachtfahrt → Kapitelkarte → Bahnhof.
2. **Bahnhof** – Politur-Pass mit Forward+ auf dem PC (RTX 4090), beide Hoheitszeichen-Einstellungen, Umgebungsleben
   (`env_veltrava_station_life.py`, 12 Figuren-Schleifen, Viadukt-Zug); Bilder `documentation/screenshots/c3_station_*`.
3. **Textprüfung** – alle 23 Befunde bearbeitet (18 wörtlich, 5 abgewandelt), dritter Prüfblick (Logik über alle
   Branch-Kombinationen) nachgeholt; Uhrzeiten 1964 („23.40“) auch in den gezeichneten Dokumenten.
4. **Geschichtskarten** – im Netz gegengeprüft (je ≥ 2 Quellen), korrigiert, `review`-Marker entfernt.
5. **`merge-kapitel-3`** – nur noch Vergleichsstand; die Cloud-Fassung ist maßgeblich (Bahnhof-Pass hat Einzelheiten verglichen).
6. **GPU-Prüfung** – Bahnhof, Palais, Figuren und Filmsequenzen auf dem PC mit Forward+ geprüft; Palais-Pass mit
   11 Lebens-Schleifen (Garderobiere, Putzfrau, Delegierte, Dolmetscher in den Kabinen …), Bilder `c3_palais_*`.
Neu in Runde 7 für Kapitel 3: Minispiele „Die Fallblatttafel“, „Die Garderobe“, „Das Relaispult“, Aufgaben „Wagen drei
ist kalt“ (Bahnhof) und am Buffet (Palais), Erinnerungen an beide Szenen. Offen bleibt Punkt 7 (menschlicher Spieltest).

## 4. Was offen ist
1. **Filmsequenzen (`LS_C3_Trains`, `LS_C3_ToHall`, `LS_C3_Close`)** – nicht fertig. Auf Branch `c3-cine` (nicht in `kapitel-3` gemergt)
   liegen die lauffähigen §12.5-Szenen (`scenes/cinematics/ch3_*`, `ch3_common`, Vertragstest `tests/test_c3_cinematics.gd`:
   `finished` genau einmal, Untertitel je Flag) und der Grafik-Generator `tools/pixelgen/env_veltrava_cine.py` (Wageninnenräume, Figuren,
   Spiegelungen fertig; Morgen-Totale begonnen; Ausgabe nach `assets/cinematics/ch3/` noch nicht angebunden). Ohne die Szenen überspringt
   `ChapterExt.play_cinematic()` die drei Einträge stumm; der Übergang 2→3 ist derzeit: X1-Montage → Kapitelkarte „Der eiserne Frieden“.
   Nächster Schritt: Generator fertigstellen, `assets/cinematics/ch3/**` + `layout.json` erzeugen, Test grün, in `kapitel-3` mergen.
2. **Bahnhof: letzte Politur** – der Strang wurde nach „WIP 3 + Dokumente“ gestoppt. Fertig und im Spiel geprüft; nicht mehr gemacht:
   Feinabgleich der Wertegruppen mit Karsk, Normal-Map-Kontrolle einzelner Props, Vergleich beider Fahnenvarianten im Spiel.
3. **Textprüfung** – zwei von drei Prüfblicken (Ton/Geschichte, Sprache/Stimme) sind fertig; 5 Befunde (2 Blocker, 3 schwer) sind behoben,
   die übrigen 24 stehen mit Vorschlägen in `documentation/C3_TEXT_REVIEW.md` (u. a. Erkenntnissatz des Rätsels, „Kommissar Aalto“,
   Option „Den Vorfall der deutschen Delegation melden“ (Genitiv/Dativ), Uhrzeiten-Schreibweise 1964, Aufgabentexte in voller Imperativform).
   Der dritte Blick (Logik über alle Branch-Kombinationen) wurde abgebrochen. Nach Textänderungen in `data/v3`: `python3 -P
   tests/reference/make_python_reference.py` und `python3 -P tools/docs/gen_quest_db_c3.py` ausführen.
4. **Geschichtskarten** – Fakten in der Cloud nicht online geprüft (kein Webzugriff); jede Karte trägt `review`. Vor Veröffentlichung
   gegenprüfen: Lienz Juni 1945, „Operation Keelhaul“ 1946/47, „mehr als zwei Millionen“, Brest-Litowsk Februar 1940, Heinz Neumann 1937,
   Nürnberg: „erstmals in großem Umfang“, verglaster Bereich, IBM-Anlage, Warnlampen; Buchquellen ohne URL.
5. **Lokaler Zweig `merge-kapitel-3`** (`2260cf0`, nur auf dem PC): enthält eine zweite, lokal gebaute Fassung von Protokoll-Rätsel und
   Bahnhofsgrafik. Empfehlung: `kapitel-3` von GitHub übernehmen (vollständig getestet, `master` bereits eingearbeitet) und den lokalen
   Zweig verwerfen oder nur einzelne Grafiken daraus vergleichen.
6. **GPU-Prüfung** – alle Bilder mit dem Compatibility-Renderer; Forward+ auf dem PC kann minimal anders aussehen (Lichtradien, Dithering).
7. **Kein menschlicher Spieltest** von Kapitel 3: Tempo, Rätselschwierigkeit, Lesbarkeit, Audio-Mix (Musik und Ambience nie gehört).
8. **Kleinigkeiten**: Fund-Bilder (`image`) für Kapitel-3-Einträge gibt es nicht (Textfunde); Spielzeit nicht gemessen (geschätzt 15–20 min);
   `historical_symbols` steht standardmäßig auf „an“, daher zeigen die Screenshots die `_hist`-Fahnen.

## 5. Branches auf GitHub
`kapitel-3` (Ergebnis, mergefähig) · Arbeitsstränge als Nachweis: `c3-tests`, `c3-explore`, `c3-audio`, `c3-chars`, `c3-puzzle`, `c3-hall`,
`c3-station` (alle in `kapitel-3` enthalten) und `c3-cine` (offen, siehe §4.1).
