# C3 REPORT — Kapitel 3 „Der eiserne Frieden“, spielbarer Anfang (Branch `kapitel-3`)

Stand: 2026-11-05 (wird am Ende der Cloud-Sitzung abgeschlossen). Gebaut in einer Cloud-Sitzung ohne GPU; alle
Bildschirmfotos stammen aus dem echten Spiel über Software-Rendering (Compatibility-Renderer, `xvfb-run`). Design-Vertrag:
`documentation/C3_DESIGN.md`; Änderungen an bestehenden Dateien: `documentation/MERGE_NOTES_C3.md`; Architektur: `TECHNICAL_ARCHITECTURE.md` §13.

## 1. Was gebaut wurde
| Bereich | Inhalt | Dateien |
|---|---|---|
| Story-Daten | 2 Szenen (`L_C3_Station`, `L_C3_Hall`), 2 Quests, 13 Ziele, 5 Dialoge (42 Zeilen) mit 16 flag-abhängigen Varianten, 2 Entscheidungen (2 + 3 Optionen) mit Reaktionen, 6 Beweisstücke, 1 Rätsel, 3 Filmsequenzen, 7 neue Zustandswerte | `data/v3/*.json`, `data/chapters/c3.json`, `data/locale/de_c3_*.json` |
| Übergang Kapitel 2→3 | Kapitel 2 endet weiter mit der X1-Montage; danach folgt die Zugfahrt („Konrads Zugfenster → Alexeis Zugfenster“), Kapitel 3 und erst dann die Endkarte mit Abspann | `data/v3/scenes.json`, `scenes/cinematics/ch3_*` |
| Regie-Erweiterung | `ChapterExt`: Levels, Einstiegspunkte, Kapitelkarten, Paletten/Grades, Zeilenvarianten, Optionstexte, Reaktionen, Rätsel-UIs, §12.5-Filmsequenzen – datengetrieben, ohne Engine-Änderung | `scripts/core/chapter_ext.gd`, `scripts/actors/story_npc.gd`, `scripts/actors/gated_interactable.gd` |
| Level Bahnhof Veltrava | 2.5D schräg wie Karsk, Alexei spielbar: Ankunft, Kurierwagen 4, Abfahrtstafel, Passkontrolle, Elena im Café; 6 Story-Ziele, 13 Funde, 2 Nebengespräche | `scenes/levels/L_C3_Station.tscn`, `assets/environments/veltrava_station/`, `tools/pixelgen/env_veltrava_station*.py` |
| Level Palais der Kommission | Seitenansicht wie das Archiv, Konrad spielbar: Kessler, Sitzordnung, Protokollbüro, Rätsel, Kabine 2, erste Begegnung mit Alexei; 7 Story-Ziele, 10 Funde, 2 Nebengespräche | `scenes/levels/L_C3_Hall.tscn`, `assets/environments/veltrava_hall/`, `tools/pixelgen/env_veltrava_hall*.py` |
| Rätsel | „Sitzordnung und Dolmetscherprotokoll“ (`pz_c3_protocol`): Namenskarten in Redereihenfolge, Hinweis nach 2 Fehlversuchen, Tastatur/Maus/Controller, Textskalierung, Kontrastmodus | `scenes/ui/ProtocolPuzzle.tscn`, `scripts/ui/protocol_puzzle.gd`, `assets/ui/puzzle/c3_*`, `tools/pixelgen/gen_ui_c3.py` |
| Figuren | Elena Weiss, Grenzbeamter, Schaffner, Lidia Voronova, Gerhard Kessler, Frau Brunner (Schreibkraft), Nils Ekdahl (Journalist): Sprite-Sheets mit Normal-Maps, Porträts mit 4 Ausdrücken | `assets/characters/<id>/`, `tools/pixelgen/characters_c3.py` |
| Dokumente | Wiegekarte, Abfahrtstafel, Dienstreiseauftrag, Sitzordnung, Dolmetscherprotokoll, Durchschrift | `assets/ui/documents/veltrava_*` |
| Filmsequenzen | `LS_C3_Trains` (Zugfahrt, ~24 s), `LS_C3_ToHall` (Uhr-Match-Cut), `LS_C3_Close` (Sonderzug 23:40) – animiert, überspringbar | `scenes/cinematics/ch3_*`, `tools/pixelgen/env_veltrava_cine.py` |
| Erkundung | 27 Einträge in Alexeis/Konrads Stimme, 3 reale Geschichtskarten (Zwangsrepatriierungen nach Jalta, NKWD-Auslieferungen an die Gestapo 1940, Simultandolmetschen in Nürnberg) | `data/explore/veltrava_*.json`, `c3_history_*.json`, `data/locale/de_explore_veltrava.json`, `de_history_c3.json` |
| Audio | `amb_veltrava_station`, `amb_veltrava_palais`, `mus_veltrava` (synthetisiert, deterministisch) | `tools/audiogen/c3_audio.py`, `assets/audio/` |
| Hoheitszeichen | Fahnen beider Seiten als neutrale Datei + `_hist`-Variante; `LayerStack.tex()` löst über `Symbols.pick` auf | `assets/environments/veltrava_*/props/flag_*` |
| `master` eingearbeitet | Erweiterungsrunden 2–6 des Hauptzweigs (Fund-Ansicht, Paradeplatz, Minispiele, Fotomodus, Abspann) sind in `kapitel-3` zusammengeführt | Merge `6a2f321` |

## 2. Rückbezüge auf Kapitel 1/2 (QUEST_DATABASE §7.3)
| Hook | Wirkung in Kapitel 3 |
|---|---|
| `C3_IRINA_WITNESS` (`irina_trust`) | Alexei nennt Irina als Zeugin (Schaffner, Passkontrolle, Elena, Begegnung); Zugfenster-Zeile „Ihr Name fährt jetzt mit“ |
| `C3_ALEXEI_SILENCE` (`alexei_secrecy`) | Alexei bleibt wortkarg und misstrauisch; „Niemand dort weiß, dass ich hier danach frage“; Elena fragt nach, warum er Fremden vertraut |
| `C3_KONRAD_COPY` (`konrad_evidence`) | Konrad erwähnt die Abschrift (Zeichenrohr, Begegnung); Option „…und die Abschrift von Emils Vermerk“ |
| `C3_ARCHIVE_ALERTED` (`office_suspicion`) | Kessler: „Ihre Anfrage aus Berlin liegt auf meinem Tisch“; Konrads Gepäck wurde zweimal geöffnet; Option „Den Dienstweg gehen“ |
| `C3_EVIDENCE_BASE` | Beide tragen ihre Hälfte: Wiegekarte/Abfahrtstafel/Reiseauftrag (Alexei), Sitzordnung/Protokoll/Durchschrift (Konrad) |
Neue Werte: `alexei_konrad_trust`, `elena_trust`, `evidence_chain`, `kessler_alerted` (+ 3 boolesche Marker). Kein Moral-Score.

## 3. Was getestet wurde
(wird am Ende mit den Endergebnissen vervollständigt)
* Unit-Tests `godot --headless --path . --script res://tests/run_all.gd`: 27 Dateien / 223 Fälle nach dem Palais-Merge; Referenzabgleich mit dem unveränderten Python-Motor auf `data/v3` (Routen × alle Entscheidungen × play/skip, Legacy-Saves, API-Traces, Mutations-Korpus): 0 Abweichungen.
* Autoplay (Story-API) durch alle drei Kapitel inkl. `--autoplay-explore`: alle 27 Funde über die Fund-Ansicht, 19/19 Geschichtskarten.
* Tastendruck-Durchlauf (`--inputplay`): siehe Endergebnis.
* Bildprüfung: jede Levelansicht, das Rätsel, die Dokumente und die Filmsequenzen wurden als Screenshot angesehen und mit den Kapitel-1/2-Screenshots verglichen.

## 4. Was offen ist
* Geschichtskarten: Die Fakten konnten in der Cloud nicht online gegengeprüft werden (kein Webzugriff); jede Karte trägt `review`. Vor Veröffentlichung prüfen (Details im Explore-Bericht: Lienz Juni 1945, „Operation Keelhaul“ 1946/47, Brest-Litowsk Februar 1940, Nürnberg: Glaskabinen/„erstmals in großem Umfang“).
* Lokaler Zweig `merge-kapitel-3` (`2260cf0`, nur auf dem PC): enthält eine zweite, lokal gebaute Fassung von Protokoll-Rätsel und Bahnhofsgrafik. Empfehlung: `kapitel-3` von GitHub übernehmen (vollständig getestet, `master` bereits eingearbeitet) und den lokalen Zweig verwerfen oder nur einzelne Grafiken daraus vergleichen.
* GPU-Prüfung: Alle Bilder entstanden mit dem Compatibility-Renderer; Forward+ auf dem PC kann minimal anders aussehen (Lichtradien, Dithering).
* Noch kein Mensch hat Kapitel 3 gespielt: Tempo, Rätselschwierigkeit, Lesbarkeit, Audio-Mix.
* (weitere Punkte folgen aus den Strang-Berichten)
