# C3 TEXT REVIEW — Textprüfung Kapitel 3 (2026-11-05, abgeschlossen 2026-11-06)

Prüfung der Kapitel-3-Texte durch drei Prüfblicke: Ton/Geschichte und Sprache/Stimme (2026-11-05, Cloud) und Logik über alle
Branch-Kombinationen (2026-11-06, unten „Dritter Prüfblick“). Fünf Befunde wurden schon in der Cloud umgesetzt
(`dlg.c3.meet_07.irina`, `dlg.c3.meet_07.secrecy`, `dlg.c3.meet_03.evidence`, `dlg.c3.el_06.secrecy`, `dlg.c3.react.ask_elena`).
**Stand 2026-11-06: alle 23 Befunde erledigt** – 18 wörtlich umgesetzt, 5 in geänderter Fassung (1, 9, 20, 21, 23; Begründung jeweils
unter „Status“), keiner verworfen. Gespiegelt in `documentation/C3_DESIGN.md`, `QUEST_DATABASE.md` §11 neu erzeugt, Python-
Referenz neu erzeugt. Offen sind nur Stellen in Dateien anderer Bereiche (gezeichnete Uhrzeiten und „2 410“, Rätsel-Fußzeile bei
125/150 %, Lesepause nach dem Lösen) – siehe „Übergaben an andere Bereiche“ am Ende. Nach Änderungen in `data/v3`: `py -3 -P
tests/reference/make_python_reference.py` und `py -3 -P tools/docs/gen_quest_db_c3.py`.

## Ton und historische Sensibilität

*Gesamturteil:* Die Kapitel-3-Texte halten STORY_BIBLE §2 im Kern ein: konkrete Menschen statt Parolen, kein Glamour, beide Repressionen spezifisch und asymmetrisch (Reichsseite: die eigenen Euphemismen „Erfassungsraum“/„Begleitgut“, Kessler „ohne eigene Meinung“, das zweimal geöffnete Gepäck; Sowjetseite: der heimlich ergänzte Reiseauftrag, Alexei als unwissende „Begleitperson“ des Kurierwagens, Voronovas Halbblindheit), und Täterpositionen werden nirgends als legitim angeboten. Die geladenen Wörter – Sammelstelle, Begleitgut, Liste, Sonderzug/Leerfahrt, Kordon-17 – werden nüchtern als entlarvte Amtssprache eingesetzt, nie als Pointe; „Rückführung“ kommt in den geprüften Dateien nicht vor (nur im Explore-Fund „Büro für Rückführung“, dort ebenfalls nüchtern als Euphemismus gelesen), und die `_hist`-Fahnenvarianten in C3_DESIGN §4 folgen der inzwischen aktualisierten WORLD_BIBLE-Symbolregel. Elena ist bis auf eine Zeile Berufsfrau mit eigenem Risiko, der Schaffner ein anständiger Mitwisser, dessen Wissen das Tagebuch ausdrücklich festhält, Kessler kalt durch Banalität. Zwei Stellen müssen vor dem Merge geändert werden: der Erfolgstext des Protokoll-Rätsels („Beide Seiten haben zugestimmt, ohne nachzufragen“) bügelt die kanonische Asymmetrie Kessler/Voronova und das eigene Protokoll (Reichsdelegation kannte die Fassung vom 12. Januar) zur „beide gleich“-Pointe glatt, und Elenas „kommen Sie allein“ ist die einzige Agentenfilm-Floskel des Kapitels. Der Rest ist Feinschliff (Bruder-Formular ohne Opfer-Mitschuld, Alexeis Antwort auf „einer von uns lügt“, „Vorrang“ für die Reichsdelegation bei den Neutralen, Kesslers Pünktlichkeitsspruch, „meine“ statt „unsere Dispatcherin“). Jede Zeile ist dreifach gespiegelt – Daten, C3_DESIGN §2.4/§2.7/§2.8 und das generierte QUEST_DATABASE §11 –, also Daten und C3_DESIGN ändern und §11 per tools/docs/gen_quest_db_c3.py neu erzeugen; die Explore-Chatzeile „Sie sagten, hier sei jeder Ausländer“ hängt an ctrl_08, das unverändert bleiben kann.

### 1. [major] data/locale/de_c3_ui.json → ui.c3.protocol.success (gespiegelt in documentation/C3_DESIGN.md §2.7 „Success text“; QUEST_DATABASE.md §11.5 wird aus den Daten generiert)

**Befund:** Der Erkenntnissatz des Kapitels stellt beide Delegationen als gleich ahnungslose Abnicker nebeneinander und macht das neutrale Sekretariat zur einzigen handelnden Partei. Das widerspricht dem eigenen Protokoll (C3_DESIGN §2.7: 10:06, Mikrofon 9 Reichsdelegation: „Keine Einwände gegen die Fassung vom 12. Januar“ – sie kannte die Fassung, bevor § 4 überhaupt verlesen wurde; 10:11, Mikrofon 3 sowjetisch: „Wir schließen uns an“) und der Kanon-Asymmetrie (CHARACTER_BIBLE: Kessler kennt „die Anlagen des Abkommens“, Voronova nur „das öffentliche Abkommen“; STORY_BIBLE §3: die Kommission schaut weg, sie erfindet den Paragraphen nicht – „Wer hat den Text geliefert?“ bleibt offen). „Beide Seiten … ohne nachzufragen“ ist genau die „beide gleich“-Lesart, die §2 verbietet, und entlastet nebenbei Kessler. Der Vorschlag ist ~50 Zeichen länger – Umbruch im Rätsel-UI prüfen.

**Aktuell:** Paragraph vier kam vom Sekretariat der Kommission – nicht von einer Delegation. Beide Seiten haben zugestimmt, ohne nachzufragen.

**Vorschlag:** Paragraph vier kam als fertiger Text vom Sekretariat der Kommission – nicht von einer Delegation. Die Reichsdelegation kannte die Fassung schon, die sowjetische hat sich angeschlossen. Nachgefragt hat niemand.

**Status (2026-11-06):** umgesetzt, leicht gekürzt: **„Paragraph vier kam als fertiger Text vom Sekretariat – nicht von einer Delegation. Die Reichsdelegation kannte die Fassung schon, die sowjetische schloss sich an. Nachgefragt hat niemand.“** (187 statt 209 Zeichen; Asymmetrie unverändert). Grund: Das gelöste Rätsel schließt nach höchstens 5,5 s von selbst (`SUCCESS_BEAT_MAX` in `scripts/ui/protocol_puzzle.gd`), für den längeren Satz reicht das kaum – Empfehlung an den Rätsel-UI-Bereich unten. Umbruch im Fenster bei 100 % geprüft (Papierkarte, kein Abschneiden). Mitgeändert: der fest eingetragene Text in `tests/test_c3_puzzle_ui.gd`.

### 2. [minor] data/v3/locale_de.json → dlg.c3.el_07 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3a_elena Nr. 7; QUEST_DATABASE.md §11.4)

**Befund:** „ohne das Kleingedruckte zu verstehen“ legt die Ursache für den Listeneintrag beim Bruder ab (eigene Nachlässigkeit) – eine leise Opfer-Mitschuld-Lesart, die das Register-/Listenthema verharmlost: Formulare, die Menschen auf Listen bringen, sind das Werkzeug der Apparate, nicht ein Lesefehler des Unterzeichners. Außerdem bleibt unerklärt, warum in einer zweisprachigen Familie niemand das Kleingedruckte lesen konnte. War das Formular in einer fremden Sprache, die ihm niemand übersetzt hat, trägt der Satz Elenas Berufsmotiv sauberer und nimmt dem Bruder die Schuld.

**Aktuell:** Mein Bruder hat einmal ein Formular unterschrieben, ohne das Kleingedruckte zu verstehen. Seitdem übersetze ich das Kleingedruckte.

**Vorschlag:** Mein Bruder hat einmal ein Formular unterschrieben. Das Kleingedruckte hat ihm niemand übersetzt. Seitdem übersetze ich das Kleingedruckte.

**Status (2026-11-06):** umgesetzt (wörtlich, 139 Zeichen).

### 3. [minor] data/v3/locale_de.json → dlg.c3.meet_11 (Antwort auf dlg.c3.meet_10 „Sie sind Russe, ich bin Deutscher. Man hat uns beigebracht, dass einer von uns lügt.“; gespiegelt in C3_DESIGN.md §2.8 dlg_c3b_meeting Nr. 11)

**Befund:** Konrads Satz (meet_10) ist kanonisch – er formuliert die Zentralfrage der STORY_BIBLE, und Konrad darf an diesem Punkt seines Bogens noch symmetrisch denken. Aber Alexeis Antwort nickt die Symmetrie stillschweigend ab: zwei Erziehungen, ein Topf. Für die „einer von uns lügt“-Logik der Szene ist das in Ordnung, auf Regime-Ebene ist es die Äquivalenz-Lesart, die §2 ausschließt („no false equivalence“). Zwei Wörter Widerspruch aus Alexeis Mund halten die Asymmetrie offen, ohne die Szene zu belehren; die Zeile bleibt kurz und trocken (seine Stimme) und behauptet keine moralische Überlegenheit.

**Aktuell:** Man hat uns vieles beigebracht. – Morozov. Karsk.

**Vorschlag:** Man hat uns vieles beigebracht. Nicht dasselbe. – Morozov. Karsk.

**Status (2026-11-06):** umgesetzt (wörtlich). „Nicht dasselbe.“ antwortet zugleich auf Alexeis Frage an Elena („Und sagen alle drei dasselbe?“).

### 4. [minor] data/v3/locale_de.json → dlg.c3.ctrl_01 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3a_control Nr. 1; QUEST_DATABASE.md §11.4)

**Befund:** Ein Beamter der Freien Stadt räumt der Reichsdelegation ausdrücklich „Vorrang“ ein – und erklärt sieben Zeilen später (ctrl_08), hier seien alle gleich Ausländer, das mache die Arbeit „gerecht“. Im Design (§4.1) sind die Schalter nur zugeordnet („Schalter 1 · Reichsdelegation“, „Schalter 2 · Sowjetische Delegation“); eine Rangordnung ist nirgends angelegt und wird von niemandem aufgegriffen. So liest sich der Vorrang des NS-Staats bei den Neutralen als unkommentierte Selbstverständlichkeit. Entweder Zuordnung statt Rang (Vorschlag) – oder, falls die Schlagseite der Kommission („peace at any price“) gemeint ist, muss Alexei oder der Beamte sie in derselben Szene benennen.

**Aktuell:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation hat Vorrang an Schalter eins.

**Vorschlag:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Schalter eins ist für die Reichsdelegation.

**Status (2026-11-06):** umgesetzt in der Fassung von Befund 11 („wird an Schalter eins abgefertigt“): Amtssprache des müden Beamten („Grenzabfertigung“), Zuordnung ohne Rang.

### 5. [minor] data/v3/locale_de.json → dlg.c3.arr_01 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3b_arrival Nr. 1; QUEST_DATABASE.md §11.4)

**Befund:** Der Pünktlichkeits-Witz bedient die Ordnungs-/Pünktlichkeitsfolklore über den NS-Staat (im selben Kapitel hängt die Kiosk-Schlagzeile „Deutsche Ordnung auf allen Gleisen“) und damit genau das Karikaturregister „schneidiger Ministerialer“, das Kessler laut Vorgabe vermeiden soll. Seine Kälte sitzt ohnehin besser in arr_03 („langsam, deutlich und ohne eigene Meinung“) und arr_03.suspicion. Banaler und kälter ist das Zählen von Köpfen; Konrads Antwort (Gepäckkontrolle an der Linie) passt unverändert.

**Aktuell:** Adler. Der Zug war pünktlich, Sie sind es nicht. Die Kommission wartet nicht auf Zeichner.

**Vorschlag:** Adler. Die Delegation ist seit zwanzig Minuten vollzählig – bis auf Sie. Die Kommission wartet nicht auf Zeichner.

**Status (2026-11-06):** umgesetzt (wörtlich). Konrads Antwort („Am Bahnhof …“, Befund 8) passt: Er stand an Schalter 1 in der Schlange, die Delegationsspitze war längst durch.

### 6. [minor] data/locale/de_c3_dialogue.json → dlg.c3.cond_02.irina und dlg.c3.ctrl_05.irina (gespiegelt in C3_DESIGN.md §2.8 Varianten Nr. 2 bzw. Nr. 5; QUEST_DATABASE.md §11.4)

**Befund:** Das Possessiv „meine Dispatcherin“ macht Irina ausgerechnet in der Vertrauens-Variante zur Untergebenen Alexeis (er ist Ingenieur, nicht ihr Vorgesetzter). CHARACTER_BIBLE und QUEST_DATABASE §7.4 führen sie als „volle Kollegin mit eigener Handlungsmacht“; die anderen irina_trust-Varianten (el_02.irina, meet_07.irina) sagen korrekt „eine Kollegin“. „unsere“ ist Eisenbahnerdeutsch und hält die Augenhöhe – ‚Menschen zuerst‘ (§2) gilt auch für Nebenfiguren.

**Aktuell:** In Karsk hätte meine Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Schaffner? / Davon wusste ich nichts. Gegengezeichnet hat meine Dispatcherin – für die Gleise, nicht für einen Wagen.

**Vorschlag:** In Karsk hätte unsere Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Schaffner? / Davon wusste ich nichts. Gegengezeichnet hat unsere Dispatcherin – für die Gleise, nicht für einen Wagen.

**Status (2026-11-06):** umgesetzt („unsere Dispatcherin“ in beiden Varianten). „Dispatcherin“ bleibt als Alexeis Eisenbahner-Jargon (диспетчер); die Rollenkarte nennt Irina amtlich „Fahrdienstleiterin“ – Umgangs- und Amtswort nebeneinander sind gewollt.

## Sprache und Figurenstimmen

*Gesamturteil:* Das Deutsch von Kapitel 3 ist insgesamt sauber und stilsicher: Die Typografie („…“ geschrieben, ‚…‘ gesprochen, Halbgeviertstrich mit Leerzeichen) stimmt durchgehend, die Figurenstimmen sind klar getrennt (Alexeis kurze Fragen und trockener Witz, Konrads Beschönigungen bis zum „Einer, den es nicht geben dürfte“, Elenas Präzision, Kesslers Kälte, der müde Grenzbeamte, der schlichte Schaffner), und die wiederkehrenden Begriffe folgen der Konvention gesprochen = Zahlwort („Wagen vier“, „Kabine zwei“, „Paragraph vier“), geschrieben = Ziffer („Kurierwagen 4“, „Kabine 2“, „§ 4“, „C-17/44“). Zwei Dinge müssen vor dem Merge repariert werden: Die beiden immer aktiven Varianten von c3b_meet_07 streichen den Serien-Satz, auf den Konrads Antwort „dieselbe Serie“ aufbaut (die Basiszeile wird nie gezeigt), und die evidence-Variante von c3b_meet_03 nennt C-17 schon in Zeile 3 und entwertet die Pointe „C-17.“/„C-17.“. Dazu kommen vier klare Fehler mittlerer Schwere (Bahnsteig statt Café, „An der Linie“ statt Bahnhof, die zweideutige Meldeoption, „Kommissar Aalto“ gegen Kommissar Wendt) und eine Reihe kleiner Register- und Konsistenzpunkte (Imperativformen, Zugbegleiter/Besatzung, Uhrzeit-Schreibweise 1964, „2 410 kg“, Rätsel-UI, Begleitschein). Nur arr_03 überschreitet mit 145 Zeichen die Dialogbox-Richtgröße; Kinosequenz-Zeilen, Journalnotizen und Beweistexte brauchen über die genannten Punkte hinaus keine Änderung.

### 7. [major] choice.c3b.report_delegation (data/v3/locale_de.json)

**Befund:** Dativ und Genitiv sind formgleich: Die Option lässt sich als „den Vorfall, den die deutsche Delegation verursacht hat, (jemandem) melden“ lesen – das Gegenteil dessen, was der Flag kessler_alerted bewirkt. Entscheidungstexte müssen eindeutig sein; die Variante „Den Dienstweg gehen – wie mit der Anfrage in Berlin“ ist in Ordnung.

**Aktuell:** Den Vorfall der deutschen Delegation melden

**Vorschlag:** Den Vorfall bei Ministerialdirektor Kessler melden

**Status (2026-11-06):** umgesetzt (wörtlich). Die Reaktionen („Melden Sie es. Aber nennen Sie Frau Weiss nicht beim Namen.“ / „Dann haben wir uns nie gesehen, Herr Adler.“) und die suspicion-Variante „Den Dienstweg gehen …“ passen unverändert.

### 8. [major] dlg.c3.arr_02 + dlg.c3.arr_02.evidence + dlg.c3.arr_02.suspicion (Node c3b_arr_02)

**Befund:** Kontinuität: Konrad kam im selben Delegationszug wie Kessler („Der Zug war pünktlich, Sie sind es nicht“). Verspätet hat ihn laut Bahnhofsszene (C3_DESIGN §4.1: deutsche Schlange an Schalter 1 mit Konrad) die Passkontrolle der Kommission am Bahnhof Veltrava – nicht eine Kontrolle „an der Linie“, was im Kapitel Kordon-17 bedeutet (cond_05: „In Kordon-17, an der Linie“). Alle drei Fassungen betroffen.

**Aktuell:** An der Linie wurde das Gepäck kontrolliert, Herr Ministerialdirektor.

**Vorschlag:** Basis: „Am Bahnhof wurde das Gepäck kontrolliert, Herr Ministerialdirektor.“ · evidence: „Am Bahnhof wurde das Gepäck kontrolliert, Herr Ministerialdirektor. Auch mein Zeichenrohr.“ · suspicion: „Am Bahnhof wurde mein Gepäck zweimal geöffnet, Herr Ministerialdirektor. Nur meines.“

**Status (2026-11-06):** umgesetzt (alle drei Fassungen).

### 9. [major] ui.c3.protocol.card.chair (data/locale/de_c3_ui.json) + documentation/C3_DESIGN.md §2.7

**Befund:** „Kommissar“ kollidiert mit Kommissar Ludwig Wendt (Staatspolizei, STORY_BIBLE §4) und klingt im Deutschen nach Kriminalpolizei. Für den Vorsitzenden einer internationalen Kommission über eine Freie Stadt ist „Hochkommissar“ der zeitgenössische Titel (Freie Stadt Danzig, Alliierte Hohe Kommission). Jetzt eine Zeile, später steckt der Begriff im Puzzle-Board und in Kapitel 6.

**Aktuell:** Vorsitz – Kommissar Aalto

**Vorschlag:** Vorsitz – Hochkommissar Aalto (ebenso in C3_DESIGN §2.7)

**Status (2026-11-06):** umgesetzt mit geänderter Form: **„Hochkommissar Aalto (Vorsitz)“**. „Vorsitz – Hochkommissar Aalto“ bricht auf der Namenskarte in drei Zeilen um, die Karte zeigt zwei – „Aalto“ wäre abgeschnitten (gemessen mit dem echten ProtocolPuzzle). Die neue Form bricht als „Hochkommissar / Aalto (Vorsitz)“ in genau zwei Zeilen um und behält den Bezug zum Platz „Vorsitz“ auf dem Plan. C3_DESIGN §2.7 und CHARACTER_BIBLE (Aalto: „Hochkommissar“, nie „Kommissar“) nachgezogen.

### 10. [minor] dlg.c3.arr_03 + dlg.c3.arr_03.suspicion (Node c3b_arr_03)

**Befund:** Beide Fassungen haben 145 Zeichen (> 140, einzige Dialogzeilen über der Richtgröße), die Basiszeile stolpert über „erläutern Sie sie“. Kesslers knappe Befehlsform aus arr_01 („Adler. Der Zug war pünktlich …“) erlaubt die Kürzung ohne Verlust.

**Aktuell:** Sie hinterlegen die Pläne für Kordon-17 im Protokollbüro. Morgen erläutern Sie sie dem Fachausschuss – langsam, deutlich und ohne eigene Meinung.

**Vorschlag:** Basis: „Die Pläne für Kordon-17 ins Protokollbüro. Morgen erläutern Sie dem Fachausschuss jede Zeichnung – langsam, deutlich, ohne eigene Meinung.“ (137) · suspicion: „Die Pläne für Kordon-17 ins Protokollbüro. Ihre Anfrage aus Berlin liegt übrigens auf meinem Tisch. Hier beantworte ich sie nicht.“ (130)

**Status (2026-11-06):** umgesetzt (138 und 130 Zeichen; einzige Zeilen über 140 waren diese beiden).

### 11. [minor] dlg.c3.ctrl_01 (Node c3a_ctrl_01, Grenzbeamter)

**Befund:** „hat Vorrang an Schalter eins“ ist sachlich schief – die Schalter sind laut Beschilderung (§4.1) einfach zugeteilt – und klingt nach Rangordnung; das passt nicht zum müden, allen gleich misstrauenden Beamten („Hier ist jeder Ausländer. Das macht die Arbeit gerecht.“).

**Aktuell:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation hat Vorrang an Schalter eins.

**Vorschlag:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation wird an Schalter eins abgefertigt.

**Status (2026-11-06):** umgesetzt (ersetzt den Vorschlag von Befund 4).

### 12. [minor] dlg.c3.cond_02 + dlg.c3.cond_02.irina + dlg.c3.cond_02.secrecy (Node c3a_cond_02)

**Befund:** Fachlich fragt ein Eisenbahner bei einem plombierten Kurierwagen nach dem Begleiter, nicht nach dem Schaffner (der steht vor ihm). „Begleiter“ bereitet zudem die Pointe der Passkontrolle vor (‚Begleitperson Kurierwagen 4‘ – der Begleiter ist er selbst); cond_03 („Ein Wagen mit Schlüssel …“) funktioniert unverändert.

**Aktuell:** Ein Wagen ohne Schaffner?

**Vorschlag:** Basis: „Ein Wagen ohne Begleiter?“ · irina: „In Karsk hätte unsere Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Begleiter?“ · secrecy: „Ich frage nur. Ein Wagen ohne Begleiter?“

**Status (2026-11-06):** umgesetzt (alle drei Fassungen).

### 13. [minor] dlg.c3.ctrl_05.irina (und dlg.c3.cond_02.irina)

**Befund:** „meine Dispatcherin“ macht Irina zu Alexeis Untergebener; sie ist Kollegin (Slice-Journal: „Kollegin am Verladebahnhof Karsk“, Rollenkarte: „Fahrdienstleiterin“). „Dispatcherin“ selbst ist als sowjetischer bzw. Reichsbahn-Begriff in Alexeis Mund vertretbar – entweder bewusst so belassen oder einheitlich „Fahrdienstleiterin“.

**Aktuell:** Davon wusste ich nichts. Gegengezeichnet hat meine Dispatcherin – für die Gleise, nicht für einen Wagen.

**Vorschlag:** Davon wusste ich nichts. Gegengezeichnet hat unsere Dispatcherin – für die Gleise, nicht für einen Wagen. (cond_02.irina entsprechend „unsere Dispatcherin“)

**Status (2026-11-06):** umgesetzt, siehe Befund 6.

### 14. [minor] dlg.c3.ctrl_02 (Node c3a_ctrl_02, Elena)

**Befund:** Eine Konferenzdolmetscherin von 1964, die auf Genauigkeit besteht, sagt „dolmetschen“; „übersetzen“ passt zu ihrem Kleingedruckten-Satz (Schriftliches, el_07), nicht zur mündlichen Arbeit am Schalter. Alexeis laienhaftes „übersetzt“ in react.search_elena darf bleiben.

**Aktuell:** Ich übersetze für die Kommission. Er fragt nach dem Zweck Ihrer Reise.

**Vorschlag:** Ich dolmetsche für die Kommission. Er fragt nach dem Zweck Ihrer Reise.

**Status (2026-11-06):** umgesetzt (wörtlich). Alexeis „übersetzt“ in `dlg.c3.react.search_elena` bleibt bewusst (Laienwort).

### 15. [minor] obj.c3a_conductor, obj.c3a_control, obj.c3b_log, obj.c3b_booth (data/v3/locale_de.json)

**Befund:** Die Slice-Aufgaben nutzen durchgehend die volle Imperativform („Untersuche“, „Vergleiche“, „Prüfe“, „Lege“); Kapitel 3 mischt verkürzte Formen („Frag“, „Geh“, „Hol“, „Such“) mit „Prüfe die Abfahrtstafel.“ und „Lies …“ – in der Aufgabenliste des Tagebuchs sichtbar uneinheitlich.

**Aktuell:** Frag den Schaffner nach dem versiegelten Wagen.

**Vorschlag:** Frage den Schaffner nach dem versiegelten Wagen. · Gehe durch die Passkontrolle. · Hole das Dolmetscherprotokoll aus dem Protokollbüro. · Suche Elena Weiss in Kabine 2.

**Status (2026-11-06):** umgesetzt. „Lies“, „Prüfe“, „Sprich“, „Sieh dir … an“, „Melde dich“ sind bereits die vollen Imperative.

### 16. [minor] item.c3_weighbill.description (data/v3/locale_de.json)

**Befund:** „2 410 kg“ mit normalem Leerzeichen kann am Zeilenende umbrechen („2 / 410 kg“) und ist eine moderne DIN-Schreibweise; 1964 schrieb man „2410 kg“ oder „2.410 kg“.

**Aktuell:** Ladung „Akten, Anlage C“, 2 410 kg. Plombe C-17/44 mit Gegensiegel der Kommission. Empfänger: Sekretariat der Kommission.

**Vorschlag:** Ladung „Akten, Anlage C“, 2410 kg. Plombe C-17/44 mit Gegensiegel der Kommission. Empfänger: Sekretariat der Kommission.

**Status (2026-11-06):** umgesetzt in der Beweisbeschreibung. Die gezeichnete Wiegekarte und ihr Alt-Text (Generator der Bahnhofsgrafik) zeigen noch „2 410“ – Übergabe an den Bereich Bahnhof (unten). Ein Stempel mit Zifferngruppen wäre auf dem Dokument zwar möglich, einheitlich ist besser.

### 17. [minor] cin.c3.tohall.time, cin.c3.close.train, item.c3_departures.name, dlg.c3.react.share_protocol (Uhrzeiten; auch Abfahrtstafel und Protokollblatt der Art-Streams)

**Befund:** Uhrzeiten mit Doppelpunkt („9:40 Uhr“, „23:40“, im Protokoll „10:02“) sind die DIN-5008-Schreibweise der 1990er; 1964 stand in Fahrplänen, Protokollen und auf Titelkarten „9.40 Uhr“ / „23.40“. Derzeit immerhin konsistent – entweder überall auf die Punktform umstellen (dann auch die gezeichnete Tafel und das Protokollblatt) oder bewusst beim Doppelpunkt bleiben.

**Aktuell:** Palais der Kommission, 9:40 Uhr.

**Vorschlag:** Palais der Kommission, 9.40 Uhr. · „23.40 Uhr, Gleis 5. Ein Sonderzug ohne Halt nach Kordon-17.“ · „Sonderfahrt 23.40“ · „… Heute Nacht um 23.40 Uhr fährt ein Zug ohne Halt nach Kordon-17. Jetzt wissen Sie auch etwas.“ (139)

**Status (2026-11-06):** umgesetzt in allen Texten dieses Bereichs: Beweisname „Sonderfahrt 23.40“, Reaktion „um 23.40 Uhr“ (139 Zeichen), Filmzeilen „9.40 Uhr“ / „23.40 Uhr, Gleis 5.“, die vier Uhrzeiten im Rätsel-Protokoll (10.02 …), Alt-Text des Protokollblatts, C3_DESIGN. Die *gezeichneten* Uhrzeiten (Abfahrtstafel als Dokument und als Prop, Protokollblatt-PNG, Durchschrift „10:09 – Mik. 12“) und die Alt-Texte von Abfahrtstafel und Durchschrift liegen in Generatoren anderer Bereiche – Übergabe unten. Englische Shot-Beschreibungen („station clock 9:40“) bleiben englisch.

### 18. [minor] char.conductor.role (data/locale/de_c3_characters.json)

**Befund:** „Zugbegleiter“ ist der DB-Begriff der 1990er, „Besatzung“ gehört zu Schiff und Flugzeug; 1964 hieß es Schaffner/Zugschaffner und Zugpersonal.

**Aktuell:** Zugbegleiter des Korridor-Express, gemischte Besatzung

**Vorschlag:** Zugschaffner des Korridor-Express, gemischtes Zugpersonal

**Status (2026-11-06):** umgesetzt (wörtlich).

### 19. [minor] sys.journal.person.conductor.note (data/locale/de_c3_characters.json)

**Befund:** Gibt cond_05 falsch wieder: Der Schaffner sagt „Jede Woche einer“ (jede Woche ein solcher Wagen, mal von der einen, mal von der anderen Seite), nicht dass Wagen vier wöchentlich fährt.

**Aktuell:** Ein Eisenbahner aus dem Reich. Zählt Wagen, keine Akten – und weiß, dass Wagen vier jede Woche fährt.

**Vorschlag:** Ein Eisenbahner aus dem Reich. Zählt Wagen, keine Akten – und weiß, dass jede Woche so ein Wagen mitfährt.

**Status (2026-11-06):** umgesetzt (wörtlich).

### 20. [minor] ui.c3.protocol.subtitle (data/locale/de_c3_ui.json)

**Befund:** Die beiden bestehenden Rätsel tragen im Untertitel den Fiktionshinweis („… fiktiv, keine echte Signalvorschrift.“ / „… kein echtes Baudokument.“), passend zur world_note in puzzles.json; das Protokollrätsel nicht.

**Aktuell:** Eröffnungssitzung · Tagesordnungspunkt 4 „Anlage C – Logistikintegration“

**Vorschlag:** Eröffnungssitzung · Tagesordnungspunkt 4 „Anlage C – Logistikintegration“ – fiktive Sitzung, kein echtes Protokoll.

**Status (2026-11-06):** umgesetzt in gekürzter Form: **„Eröffnungssitzung · TOP 4 „Anlage C“ – fiktive Sitzung, kein echtes Protokoll“**. Der Vorschlag (alter Untertitel + Zusatz) macht die Kopfzeile 288 px breiter als das Rätselpanel (Messung bei 100 %); der volle Tagesordnungspunkt steht ohnehin oben auf dem Protokollblatt.

### 21. [minor] ui.c3.protocol.incomplete, ui.c3.protocol.instruction, ui.c3.protocol.undo, ui.c3.protocol.controls

**Befund:** „legen“ ohne Partikel wirkt unvollständig (Signalrätsel: „Lege … ein“); „Zurück“ als Rücknahme-Taste kollidiert mit ui.back „Zurück“ – das Signalrätsel sagt deshalb „Zurücknehmen“.

**Aktuell:** Lege zuerst alle vier Karten.

**Vorschlag:** Lege zuerst alle vier Karten ab. · instruction: „Lege die Namenskarten in der Reihenfolge ab, in der zu Anlage C gesprochen wurde. Das Protokoll nennt nur Uhrzeit und Mikrofon – die Sitzordnung verrät, wer an welchem Mikrofon saß.“ · undo: „Zurücknehmen“ · controls: „1–4 Karte legen · Rücktaste zurücknehmen · Enter prüfen · Esc schließen“

**Status (2026-11-06):** umgesetzt: „Lege zuerst alle vier Karten ab.“, Anweisung mit „ab“, Tooltip ausführlich („1–4 Karte legen · Rücktaste letzte Karte zurücknehmen · R neu ordnen · Enter prüfen · Esc schließen“). **Abweichend:** Rücknahme-Knopf **„Rückgängig“** statt „Zurücknehmen“, Tastenhinweis bleibt „zurück“. Grund: Bei 125/150 % stehen Tastenhinweise und vier Knöpfe (je mindestens 196 px) in einer Zeile, die schon mit den alten Texten 25 px breiter ist als das Panel; „Zurücknehmen“ + „zurücknehmen“ machen daraus 128 px (der letzte Knopf wird abgeschnitten), „Rückgängig“ passt in die Mindestbreite, ist das übliche deutsche Wort für die Rücknahme und kollidiert nicht mit ui.back „Zurück“. Die verbleibenden 25 px sind ein Layoutfehler von `scripts/ui/protocol_puzzle.gd` – Übergabe unten.

### 22. [minor] documentation/C3_DESIGN.md#Titel (Z. 1) und Zitat Z. 6–8; §2.5 vs. §2.7; item.c3_booth_log.description

**Befund:** Typografie im Vertrag: öffnendes „ mit geradem Schlusszeichen " im Titel und im Zitat aus FUTURE_CHAPTER_ARCS. Außerdem nennen §2.5 und item.c3_booth_log.description die Randnotiz ohne Ausrufezeichen, §2.7 und das gedruckte Protokollblatt (gen_ui_c3.py, veltrava_protocol_documents.json) mit – die Beweisbeschreibung sollte dem Druck folgen.

**Aktuell:** # CHAPTER 3 — „Der eiserne Frieden" (opening) — design contract

**Vorschlag:** Titel: „Der eiserne Frieden“; Zitat: „… Land ist.“; §2.5 und item.c3_booth_log.description: „RU: begleitete Personen – DE: Begleitgut!“

**Status (2026-11-06):** umgesetzt (Titel, Zitat, §2.5, Beweisbeschreibung – dort jetzt ohne Schlusspunkt nach dem Ausrufezeichen).

### 23. [minor] data/chapters/c3.json#line_variants (c3a_cond_02, c3a_ctrl_05, c3b_arr_02, c3b_meet_03, c3b_meet_07, c3b_meet_08)

**Befund:** Strukturell: Die Variantenpaare irina_trust/alexei_secrecy, konrad_evidence/office_suspicion und elena_trust/evidence_chain sind nach den Pflichtentscheidungen a1_choose, m1_choose und c3a_choose immer genau einseitig ≥ 1 (chapter_ext.gd: erste passende Bedingung gewinnt). Die sechs Basiszeilen in locale_de.json werden daher nie gesprochen; die Varianten sind die eigentlichen Zeilen und müssen das Gespräch allein tragen (Ursache des Bruchs in meet_07).

**Vorschlag:** Entweder in C3_DESIGN §2.8 festhalten, dass diese sechs Basiszeilen nur Fallback sind, oder je eine Variante zur Basiszeile machen (z. B. secrecy/suspicion als Basis, nur irina/evidence als Variante), damit locale_de.json den tatsächlich gehörten Text enthält und jede Variante gegen die Folgezeile gelesen wird.

**Status (2026-11-06):** umgesetzt als Dokumentation (erste Möglichkeit): C3_DESIGN §2.8 nennt die sechs Fallback-Basiszeilen, und `tools/docs/gen_quest_db_c3.py` erkennt und markiert sie in QUEST_DATABASE §11.4 selbst („base line = fallback only: every option of `a1_choose` …“). Jede Variante wurde im dritten Prüfblick gegen ihre Folgezeile gelesen (zwei Brüche behoben, siehe dort). Den Umbau „eine Variante wird Basiszeile“ habe ich verworfen: Er ändert Schlüssel, die `tests/test_c3_presentation.gd` und der Autoplay-Treiber gezielt prüfen, und der Spieler hört danach nichts anderes; die Basiszeilen bleiben die sinnvollen Texte für Level-Starts ohne Spielstand (`--scene=`).

## Dritter Prüfblick – Logik über alle Branch-Kombinationen (2026-11-06)

*Methode:* Für alle 24 Kombinationen (a1 × m1 × c3a × c3b) wurde der gesamte gelesene Text in Spielreihenfolge erzeugt (Filmzeilen,
Aufgaben, Dialogzeilen mit der jeweils greifenden Variante, Beweistexte, Optionen samt Varianten, Reaktion, Schlussfilm; Auswahl wie
`ChapterExt`: erste passende Bedingung gewinnt) und Zeile für Zeile gegen die vorige Zeile, die eigenen früheren Entscheidungen,
Tagebuchnotizen, Aufgaben- und Beweistexte gelesen. Befunde und Änderungen:

### L1. [major] dlg.c3.meet_03.evidence → c3b_meet_04 (Route `note_alone`)
**Befund:** Nach `note_alone` sagt Alexei „Ich suche den Empfänger eines Kurierwagens. Die Plombennummer habe ich. Die Wiegekarte nennt
dieses Haus.“ – Konrad antwortet „Sie ist nicht hier. Ihr Protokollheft auch nicht.“ Das „Sie“ hat keinen Bezug (Frau Weiss fällt in
dieser Fassung nicht), ebenso „ihrer Kabine“ in meet_05.
**Neu:** „Die Wiegekarte nennt dieses Haus als Empfänger. Die Plombennummer habe ich. Für den Rest brauche ich Frau Weiss.“ (112) –
greift Elenas Reaktion auf `note_alone` auf („Zahlen übersetzen sich nicht von selbst“) und verrät C-17 weiterhin nicht vor meet_09.

### L2. [minor] dlg.c3.meet_08.evidence → Option `share_protocol` (Route `preserve_evidence`)
**Befund:** Konrad sagt „Was darin steht, behalte ich vorerst.“, und unmittelbar danach bietet die Entscheidung „Ihm Elenas Notiz zeigen
– und die Abschrift von Emils Vermerk“. Die Zeile nimmt die Entscheidung vorweg und macht die Option zum Widerruf.
**Neu:** „In Berlin trägt ein Korridor dieselbe Serie. Ich habe eine Abschrift des Vermerks. Ob ich sie Ihnen zeige, weiß ich noch
nicht.“ (127) – die Zeile öffnet die Entscheidung, alle drei Optionen bleiben stimmig.

### L3. [minor] sys.journal.person.kessler.note (Route `request_explanation`)
**Befund:** „Will Pläne ohne eigene Meinung.“ zitiert die Basiszeile von c3b_arr_03; mit `office_suspicion` sagt Kessler den Satz nie.
**Neu:** „Leitet die Reichsdelegation. Will von seinem Zeichner Pläne – keine Meinung, keine Fragen.“ – trägt beide Fassungen
(„ohne eigene Meinung“ / „Hier beantworte ich sie nicht“).

### L4. [minor] explore.veltrava.station.chat_voronova.l1 (154 Zeichen)
**Neu:** „… jede Weiche von Kordon-17. Ihre Meinung dazu sagen Sie zuerst mir.“ (139). Alle Kapitel-3-Dialog- und Gesprächszeilen sind
jetzt ≤ 140 Zeichen.

### Geprüft, ohne Änderung
* Zeitlinie: Ankunft im Morgengrauen → Passkontrolle → Café → 9.40 Uhr Palais (Konrad stand in der Schlange an Schalter 1; Kessler:
  „seit zwanzig Minuten vollzählig“) → Eröffnungssitzung, TOP 4 um 10.02–10.11 Uhr → Protokoll, Rätsel, Kabine 2 → Begegnung → 23.40 Uhr
  Sonderzug. „Fassung vom 12. Januar“ liegt vor „Februar 1964“. Stimmig in allen Routen.
* `irina_trust`/`alexei_secrecy`: Filmzeile („Irina hat meinen Reiseauftrag gegengezeichnet“ / „Irina hat nicht gefragt …“),
  ctrl_05 („Gegengezeichnet hat unsere Dispatcherin – für die Gleise“ / „In Karsk hat niemand diesen Auftrag gegengezeichnet“),
  meet_07 („ihr Name steht neben meinem“ / „Niemand dort weiß, dass ich danach frage“) und die note_alone-Option widersprechen sich nie.
* `konrad_evidence`/`office_suspicion`: Abschrift im Zeichenrohr (Film) → „Auch mein Zeichenrohr“ → L2 → Option mit Abschrift;
  „Auf meine Anfrage kam keine Antwort“ → „Ihre Anfrage aus Berlin liegt übrigens auf meinem Tisch“ → „Seitdem sieht man mir über
  die Schulter“ → „Den Dienstweg gehen – wie mit der Anfrage in Berlin“.
* `elena_trust`/`evidence_chain`: Reaktion „Nach der Eröffnungssitzung, Kabine zwei“ ↔ meet_03.elena „… nach der Sitzung verabredet“;
  Reaktion auf report_delegation mit `elena_trust` („nennen Sie Frau Weiss nicht beim Namen“) schützt die verabredete Zusammenarbeit,
  ohne Vorwissen vorauszusetzen. `search_elena`: „Am Bahnhof hat sie für den Grenzbeamten übersetzt“ ist Alexeis letzter Stand.
* Beweise ↔ Aufgaben ↔ Dialoge: Wiegekarte („Papier, sagt die Wiegekarte“ → „Akten, Anlage C … Empfänger: Sekretariat“), Abfahrtstafel
  (→ Reaktion „23.40 Uhr … ohne Halt nach Kordon-17“ und Schlussfilm), Reiseauftrag (ctrl_04/06 ↔ „Auf Russisch begleitet er Fracht,
  auf Deutsch Akten“ ↔ „Auf meinem Schein steht Fracht“), Protokoll/Durchschrift (Erfolgssatz ↔ „Vom Sekretariat, nicht von einer
  Delegation. Wer hat den Text geliefert?“ – die Frage bleibt offen, wie STORY_BIBLE §3 es verlangt).
* Tagebuch „Personen“: Schaffner (Befund 19), Grenzbeamter, Elena, Kessler (L3) – in jeder Route belegt.
* Erkundung: „Fräulein Weiss“ bei Frau Brunner ist Zeitkolorit ihrer Stimme (Schweizer Schreibkraft, 1964), kein Widerspruch zu
  „Frau Weiss“ bei Kessler und Konrad. Vierschienengleis „89 Millimeter“ = 1524 − 1435 mm, die sowjetische Spurweite von 1964 (1520 mm
  erst ab 1970): stimmt.
* Aufgabentexte nennen Elena beim Namen, bevor Alexei ihn hört – der Sprechername steht schon an der Passkontrolle im Dialogfeld.

## Faktencheck der drei Geschichtskarten (2026-11-06)

Jede Aussage gegen mindestens zwei unabhängige Quellen geprüft (Quellen mit URL in `data/explore/c3_history_*.json`); die
`review`-Marker sind entfernt, die Texte haben 787/795/793 Zeichen.

* **hist.soviet.repatriation** – Jalta-Abkommen 11.02.1945 (IPN; Universitäten Nottingham/Manchester). Korrigiert: „Bis 1947 … mehr als
  zwei Millionen“ → **„Bis Ende September 1945“** (IPN: Mai bis September 1945, Deutschland und Österreich; britisches Unterhaus, Hansard 17.10.1945: rund 2 000 000 bis
  15. September allein aus Westdeutschland, davon 917 000 aus der britischen Zone). Ergänzt: **„Die meisten
  wollten heim. Zehntausende aber wurden gegen ihren Willen ausgeliefert“** (die alte Fassung „viele gegen ihren Willen“ ließ die
  Mehrheit offen). Lienz: gewaltsame Räumung ab 1. Juni 1945, Tote und Selbsttötungen bestätigt (Tiroler Tageszeitung/APA 2018,
  Universität Innsbruck 2003; Peggetz-Lager). „Operation Keelhaul“: Deckname der letzten Zwangsrückführungen aus Italien,
  14.08.1946–09.05.1947 (Wikipedia; der Name steht heute oft für das Ganze). Filtration: alle Rückkehrer überprüft, rund 350 000 wegen
  Kollaboration/Spionage verurteilt (Nottingham) → „Hunderttausende kamen in Haft oder Zwangsarbeit“. „Breit bekannt erst durch Bethell
  (1974) und Tolstoy (1977)“ → **„erst in den 1970er-Jahren“** (Julius Epsteins „Operation Keelhaul“ erschien schon 1973; Freigabe der
  britischen Akten nach der 30-Jahre-Regel).
* **hist.soviet.handover_1940** – Korrigiert: Die Ausweisungen begannen **1937**, nicht erst mit dem Pakt; nach der Teilung Polens
  übergab das NKWD **ab Dezember 1939 bis Mai 1941** an der Bug-Brücke von Brest-Litowsk direkt an deutsche Stellen (dort wartete der
  SD), „wohl weniger als 500“ (W. Mensing, ZdF 20/2006) → „wohl mehrere hundert“; fast alle kamen aus Gefängnissen und Lagern, bis zur
  Hälfte KPD/KPÖ-nah, auch Juden (Mensing). Buber-Neumann: Übergabe im Februar 1940 mit etwa 30 anderen (Deutsche Nationalbibliothek,
  Exilarchiv), Karaganda bestätigt. **Heinz Neumann war ihr Lebensgefährte, nicht ihr Mann**; verhaftet im April 1937 in Moskau,
  hingerichtet am (vermutlich) 26.11.1937 (NDB). Korrigiert: „blieb nach der Übergabe bis 1945 in Ravensbrück“ → **erst Gestapo-Haft,
  ab August 1940 Ravensbrück, entlassen im April 1945** (DNB). Bericht: Erstausgabe München 1949 (schwedisch schon 1948).
* **hist.reich.nuremberg_interpreters** – Prozessdaten 20.11.1945–01.10.1946 bestätigt. „Erstmals in großem Umfang“: bestätigt mit der
  Einschränkung früherer Versuche (Völkerbund/IAO mit vorübersetzten Texten; USHMM). IBM stellte die Anlage kostenlos (USHMM, National
  WWII Museum). Präzisiert: Kopfhörer mit Wahlschalter (Kanal 1 = Originalton); **drei Teams zu je zwölf**; Kabinen **vorn und seitlich
  verglast, oben offen**; **gelbe Lampe = langsamer, rote = innehalten**, bedient von einem Aufsichtsdolmetscher (beide Quellen).

## Übergaben an andere Bereiche (Stand 2026-11-06)
* **Bahnhofsgrafik** (`tools/pixelgen/env_veltrava_station_docs.py`, `env_veltrava_station_props.py`, `env_veltrava_station.py`):
  Abfahrtstafel „23:40“ → „23.40“ (Dokument, Prop, Alt-Text `doc.veltrava.departures.alt`), Wiegekarte „2 410“ → „2410“ (Stempel und
  Alt-Text `doc.veltrava.weighbill.alt`).
* **Palais-Grafik** (`tools/pixelgen/env_veltrava_hall_docs.py`): Durchschrift „10:09 - Mik. 12“ → „10.09 - Mik. 12“ (Bild, Marke,
  Alt-Text `doc.veltrava_hall.carbon.alt`).
* **Rätsel-UI** (`tools/pixelgen/gen_ui_c3.py`): Uhrzeiten des Protokollblatts „10:02 …“ → „10.02 …“ (PNG + `veltrava_protocol_documents.json`);
  `scripts/ui/protocol_puzzle.gd`: Fußzeile bei 125/150 % 25 px zu breit (Tastenhinweise und vier Knöpfe in einer Zeile);
  Lesepause nach dem Lösen (`SUCCESS_BEAT_MAX` 5,5 s) für den Erkenntnissatz knapp.
