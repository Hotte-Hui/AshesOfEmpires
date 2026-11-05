# C3 TEXT REVIEW — offene Befunde der Textprüfung (2026-11-05)

Automatische Prüfung der Kapitel-3-Texte durch zwei unabhängige Prüfblicke (ein dritter, Logik über alle Branch-Kombinationen,
wurde abgebrochen). Fünf Befunde wurden bereits umgesetzt (`dlg.c3.meet_07.irina`, `dlg.c3.meet_07.secrecy`, `dlg.c3.meet_03.evidence`,
`dlg.c3.el_06.secrecy`, `dlg.c3.react.ask_elena`). Die übrigen sind Vorschläge, keine Pflicht. Nach Änderungen in `data/v3`:
`python3 -P tests/reference/make_python_reference.py` und `python3 -P tools/docs/gen_quest_db_c3.py`.

## Ton und historische Sensibilität

*Gesamturteil:* Die Kapitel-3-Texte halten STORY_BIBLE §2 im Kern ein: konkrete Menschen statt Parolen, kein Glamour, beide Repressionen spezifisch und asymmetrisch (Reichsseite: die eigenen Euphemismen „Erfassungsraum“/„Begleitgut“, Kessler „ohne eigene Meinung“, das zweimal geöffnete Gepäck; Sowjetseite: der heimlich ergänzte Reiseauftrag, Alexei als unwissende „Begleitperson“ des Kurierwagens, Voronovas Halbblindheit), und Täterpositionen werden nirgends als legitim angeboten. Die geladenen Wörter – Sammelstelle, Begleitgut, Liste, Sonderzug/Leerfahrt, Kordon-17 – werden nüchtern als entlarvte Amtssprache eingesetzt, nie als Pointe; „Rückführung“ kommt in den geprüften Dateien nicht vor (nur im Explore-Fund „Büro für Rückführung“, dort ebenfalls nüchtern als Euphemismus gelesen), und die `_hist`-Fahnenvarianten in C3_DESIGN §4 folgen der inzwischen aktualisierten WORLD_BIBLE-Symbolregel. Elena ist bis auf eine Zeile Berufsfrau mit eigenem Risiko, der Schaffner ein anständiger Mitwisser, dessen Wissen das Tagebuch ausdrücklich festhält, Kessler kalt durch Banalität. Zwei Stellen müssen vor dem Merge geändert werden: der Erfolgstext des Protokoll-Rätsels („Beide Seiten haben zugestimmt, ohne nachzufragen“) bügelt die kanonische Asymmetrie Kessler/Voronova und das eigene Protokoll (Reichsdelegation kannte die Fassung vom 12. Januar) zur „beide gleich“-Pointe glatt, und Elenas „kommen Sie allein“ ist die einzige Agentenfilm-Floskel des Kapitels. Der Rest ist Feinschliff (Bruder-Formular ohne Opfer-Mitschuld, Alexeis Antwort auf „einer von uns lügt“, „Vorrang“ für die Reichsdelegation bei den Neutralen, Kesslers Pünktlichkeitsspruch, „meine“ statt „unsere Dispatcherin“). Jede Zeile ist dreifach gespiegelt – Daten, C3_DESIGN §2.4/§2.7/§2.8 und das generierte QUEST_DATABASE §11 –, also Daten und C3_DESIGN ändern und §11 per tools/docs/gen_quest_db_c3.py neu erzeugen; die Explore-Chatzeile „Sie sagten, hier sei jeder Ausländer“ hängt an ctrl_08, das unverändert bleiben kann.

### 1. [major] data/locale/de_c3_ui.json → ui.c3.protocol.success (gespiegelt in documentation/C3_DESIGN.md §2.7 „Success text“; QUEST_DATABASE.md §11.5 wird aus den Daten generiert)

**Befund:** Der Erkenntnissatz des Kapitels stellt beide Delegationen als gleich ahnungslose Abnicker nebeneinander und macht das neutrale Sekretariat zur einzigen handelnden Partei. Das widerspricht dem eigenen Protokoll (C3_DESIGN §2.7: 10:06, Mikrofon 9 Reichsdelegation: „Keine Einwände gegen die Fassung vom 12. Januar“ – sie kannte die Fassung, bevor § 4 überhaupt verlesen wurde; 10:11, Mikrofon 3 sowjetisch: „Wir schließen uns an“) und der Kanon-Asymmetrie (CHARACTER_BIBLE: Kessler kennt „die Anlagen des Abkommens“, Voronova nur „das öffentliche Abkommen“; STORY_BIBLE §3: die Kommission schaut weg, sie erfindet den Paragraphen nicht – „Wer hat den Text geliefert?“ bleibt offen). „Beide Seiten … ohne nachzufragen“ ist genau die „beide gleich“-Lesart, die §2 verbietet, und entlastet nebenbei Kessler. Der Vorschlag ist ~50 Zeichen länger – Umbruch im Rätsel-UI prüfen.

**Aktuell:** Paragraph vier kam vom Sekretariat der Kommission – nicht von einer Delegation. Beide Seiten haben zugestimmt, ohne nachzufragen.

**Vorschlag:** Paragraph vier kam als fertiger Text vom Sekretariat der Kommission – nicht von einer Delegation. Die Reichsdelegation kannte die Fassung schon, die sowjetische hat sich angeschlossen. Nachgefragt hat niemand.

### 2. [minor] data/v3/locale_de.json → dlg.c3.el_07 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3a_elena Nr. 7; QUEST_DATABASE.md §11.4)

**Befund:** „ohne das Kleingedruckte zu verstehen“ legt die Ursache für den Listeneintrag beim Bruder ab (eigene Nachlässigkeit) – eine leise Opfer-Mitschuld-Lesart, die das Register-/Listenthema verharmlost: Formulare, die Menschen auf Listen bringen, sind das Werkzeug der Apparate, nicht ein Lesefehler des Unterzeichners. Außerdem bleibt unerklärt, warum in einer zweisprachigen Familie niemand das Kleingedruckte lesen konnte. War das Formular in einer fremden Sprache, die ihm niemand übersetzt hat, trägt der Satz Elenas Berufsmotiv sauberer und nimmt dem Bruder die Schuld.

**Aktuell:** Mein Bruder hat einmal ein Formular unterschrieben, ohne das Kleingedruckte zu verstehen. Seitdem übersetze ich das Kleingedruckte.

**Vorschlag:** Mein Bruder hat einmal ein Formular unterschrieben. Das Kleingedruckte hat ihm niemand übersetzt. Seitdem übersetze ich das Kleingedruckte.

### 3. [minor] data/v3/locale_de.json → dlg.c3.meet_11 (Antwort auf dlg.c3.meet_10 „Sie sind Russe, ich bin Deutscher. Man hat uns beigebracht, dass einer von uns lügt.“; gespiegelt in C3_DESIGN.md §2.8 dlg_c3b_meeting Nr. 11)

**Befund:** Konrads Satz (meet_10) ist kanonisch – er formuliert die Zentralfrage der STORY_BIBLE, und Konrad darf an diesem Punkt seines Bogens noch symmetrisch denken. Aber Alexeis Antwort nickt die Symmetrie stillschweigend ab: zwei Erziehungen, ein Topf. Für die „einer von uns lügt“-Logik der Szene ist das in Ordnung, auf Regime-Ebene ist es die Äquivalenz-Lesart, die §2 ausschließt („no false equivalence“). Zwei Wörter Widerspruch aus Alexeis Mund halten die Asymmetrie offen, ohne die Szene zu belehren; die Zeile bleibt kurz und trocken (seine Stimme) und behauptet keine moralische Überlegenheit.

**Aktuell:** Man hat uns vieles beigebracht. – Morozov. Karsk.

**Vorschlag:** Man hat uns vieles beigebracht. Nicht dasselbe. – Morozov. Karsk.

### 4. [minor] data/v3/locale_de.json → dlg.c3.ctrl_01 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3a_control Nr. 1; QUEST_DATABASE.md §11.4)

**Befund:** Ein Beamter der Freien Stadt räumt der Reichsdelegation ausdrücklich „Vorrang“ ein – und erklärt sieben Zeilen später (ctrl_08), hier seien alle gleich Ausländer, das mache die Arbeit „gerecht“. Im Design (§4.1) sind die Schalter nur zugeordnet („Schalter 1 · Reichsdelegation“, „Schalter 2 · Sowjetische Delegation“); eine Rangordnung ist nirgends angelegt und wird von niemandem aufgegriffen. So liest sich der Vorrang des NS-Staats bei den Neutralen als unkommentierte Selbstverständlichkeit. Entweder Zuordnung statt Rang (Vorschlag) – oder, falls die Schlagseite der Kommission („peace at any price“) gemeint ist, muss Alexei oder der Beamte sie in derselben Szene benennen.

**Aktuell:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation hat Vorrang an Schalter eins.

**Vorschlag:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Schalter eins ist für die Reichsdelegation.

### 5. [minor] data/v3/locale_de.json → dlg.c3.arr_01 (gespiegelt in C3_DESIGN.md §2.8 dlg_c3b_arrival Nr. 1; QUEST_DATABASE.md §11.4)

**Befund:** Der Pünktlichkeits-Witz bedient die Ordnungs-/Pünktlichkeitsfolklore über den NS-Staat (im selben Kapitel hängt die Kiosk-Schlagzeile „Deutsche Ordnung auf allen Gleisen“) und damit genau das Karikaturregister „schneidiger Ministerialer“, das Kessler laut Vorgabe vermeiden soll. Seine Kälte sitzt ohnehin besser in arr_03 („langsam, deutlich und ohne eigene Meinung“) und arr_03.suspicion. Banaler und kälter ist das Zählen von Köpfen; Konrads Antwort (Gepäckkontrolle an der Linie) passt unverändert.

**Aktuell:** Adler. Der Zug war pünktlich, Sie sind es nicht. Die Kommission wartet nicht auf Zeichner.

**Vorschlag:** Adler. Die Delegation ist seit zwanzig Minuten vollzählig – bis auf Sie. Die Kommission wartet nicht auf Zeichner.

### 6. [minor] data/locale/de_c3_dialogue.json → dlg.c3.cond_02.irina und dlg.c3.ctrl_05.irina (gespiegelt in C3_DESIGN.md §2.8 Varianten Nr. 2 bzw. Nr. 5; QUEST_DATABASE.md §11.4)

**Befund:** Das Possessiv „meine Dispatcherin“ macht Irina ausgerechnet in der Vertrauens-Variante zur Untergebenen Alexeis (er ist Ingenieur, nicht ihr Vorgesetzter). CHARACTER_BIBLE und QUEST_DATABASE §7.4 führen sie als „volle Kollegin mit eigener Handlungsmacht“; die anderen irina_trust-Varianten (el_02.irina, meet_07.irina) sagen korrekt „eine Kollegin“. „unsere“ ist Eisenbahnerdeutsch und hält die Augenhöhe – ‚Menschen zuerst‘ (§2) gilt auch für Nebenfiguren.

**Aktuell:** In Karsk hätte meine Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Schaffner? / Davon wusste ich nichts. Gegengezeichnet hat meine Dispatcherin – für die Gleise, nicht für einen Wagen.

**Vorschlag:** In Karsk hätte unsere Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Schaffner? / Davon wusste ich nichts. Gegengezeichnet hat unsere Dispatcherin – für die Gleise, nicht für einen Wagen.

## Sprache und Figurenstimmen

*Gesamturteil:* Das Deutsch von Kapitel 3 ist insgesamt sauber und stilsicher: Die Typografie („…“ geschrieben, ‚…‘ gesprochen, Halbgeviertstrich mit Leerzeichen) stimmt durchgehend, die Figurenstimmen sind klar getrennt (Alexeis kurze Fragen und trockener Witz, Konrads Beschönigungen bis zum „Einer, den es nicht geben dürfte“, Elenas Präzision, Kesslers Kälte, der müde Grenzbeamte, der schlichte Schaffner), und die wiederkehrenden Begriffe folgen der Konvention gesprochen = Zahlwort („Wagen vier“, „Kabine zwei“, „Paragraph vier“), geschrieben = Ziffer („Kurierwagen 4“, „Kabine 2“, „§ 4“, „C-17/44“). Zwei Dinge müssen vor dem Merge repariert werden: Die beiden immer aktiven Varianten von c3b_meet_07 streichen den Serien-Satz, auf den Konrads Antwort „dieselbe Serie“ aufbaut (die Basiszeile wird nie gezeigt), und die evidence-Variante von c3b_meet_03 nennt C-17 schon in Zeile 3 und entwertet die Pointe „C-17.“/„C-17.“. Dazu kommen vier klare Fehler mittlerer Schwere (Bahnsteig statt Café, „An der Linie“ statt Bahnhof, die zweideutige Meldeoption, „Kommissar Aalto“ gegen Kommissar Wendt) und eine Reihe kleiner Register- und Konsistenzpunkte (Imperativformen, Zugbegleiter/Besatzung, Uhrzeit-Schreibweise 1964, „2 410 kg“, Rätsel-UI, Begleitschein). Nur arr_03 überschreitet mit 145 Zeichen die Dialogbox-Richtgröße; Kinosequenz-Zeilen, Journalnotizen und Beweistexte brauchen über die genannten Punkte hinaus keine Änderung.

### 7. [major] choice.c3b.report_delegation (data/v3/locale_de.json)

**Befund:** Dativ und Genitiv sind formgleich: Die Option lässt sich als „den Vorfall, den die deutsche Delegation verursacht hat, (jemandem) melden“ lesen – das Gegenteil dessen, was der Flag kessler_alerted bewirkt. Entscheidungstexte müssen eindeutig sein; die Variante „Den Dienstweg gehen – wie mit der Anfrage in Berlin“ ist in Ordnung.

**Aktuell:** Den Vorfall der deutschen Delegation melden

**Vorschlag:** Den Vorfall bei Ministerialdirektor Kessler melden

### 8. [major] dlg.c3.arr_02 + dlg.c3.arr_02.evidence + dlg.c3.arr_02.suspicion (Node c3b_arr_02)

**Befund:** Kontinuität: Konrad kam im selben Delegationszug wie Kessler („Der Zug war pünktlich, Sie sind es nicht“). Verspätet hat ihn laut Bahnhofsszene (C3_DESIGN §4.1: deutsche Schlange an Schalter 1 mit Konrad) die Passkontrolle der Kommission am Bahnhof Veltrava – nicht eine Kontrolle „an der Linie“, was im Kapitel Kordon-17 bedeutet (cond_05: „In Kordon-17, an der Linie“). Alle drei Fassungen betroffen.

**Aktuell:** An der Linie wurde das Gepäck kontrolliert, Herr Ministerialdirektor.

**Vorschlag:** Basis: „Am Bahnhof wurde das Gepäck kontrolliert, Herr Ministerialdirektor.“ · evidence: „Am Bahnhof wurde das Gepäck kontrolliert, Herr Ministerialdirektor. Auch mein Zeichenrohr.“ · suspicion: „Am Bahnhof wurde mein Gepäck zweimal geöffnet, Herr Ministerialdirektor. Nur meines.“

### 9. [major] ui.c3.protocol.card.chair (data/locale/de_c3_ui.json) + documentation/C3_DESIGN.md §2.7

**Befund:** „Kommissar“ kollidiert mit Kommissar Ludwig Wendt (Staatspolizei, STORY_BIBLE §4) und klingt im Deutschen nach Kriminalpolizei. Für den Vorsitzenden einer internationalen Kommission über eine Freie Stadt ist „Hochkommissar“ der zeitgenössische Titel (Freie Stadt Danzig, Alliierte Hohe Kommission). Jetzt eine Zeile, später steckt der Begriff im Puzzle-Board und in Kapitel 6.

**Aktuell:** Vorsitz – Kommissar Aalto

**Vorschlag:** Vorsitz – Hochkommissar Aalto (ebenso in C3_DESIGN §2.7)

### 10. [minor] dlg.c3.arr_03 + dlg.c3.arr_03.suspicion (Node c3b_arr_03)

**Befund:** Beide Fassungen haben 145 Zeichen (> 140, einzige Dialogzeilen über der Richtgröße), die Basiszeile stolpert über „erläutern Sie sie“. Kesslers knappe Befehlsform aus arr_01 („Adler. Der Zug war pünktlich …“) erlaubt die Kürzung ohne Verlust.

**Aktuell:** Sie hinterlegen die Pläne für Kordon-17 im Protokollbüro. Morgen erläutern Sie sie dem Fachausschuss – langsam, deutlich und ohne eigene Meinung.

**Vorschlag:** Basis: „Die Pläne für Kordon-17 ins Protokollbüro. Morgen erläutern Sie dem Fachausschuss jede Zeichnung – langsam, deutlich, ohne eigene Meinung.“ (137) · suspicion: „Die Pläne für Kordon-17 ins Protokollbüro. Ihre Anfrage aus Berlin liegt übrigens auf meinem Tisch. Hier beantworte ich sie nicht.“ (130)

### 11. [minor] dlg.c3.ctrl_01 (Node c3a_ctrl_01, Grenzbeamter)

**Befund:** „hat Vorrang an Schalter eins“ ist sachlich schief – die Schalter sind laut Beschilderung (§4.1) einfach zugeteilt – und klingt nach Rangordnung; das passt nicht zum müden, allen gleich misstrauenden Beamten („Hier ist jeder Ausländer. Das macht die Arbeit gerecht.“).

**Aktuell:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation hat Vorrang an Schalter eins.

**Vorschlag:** Sowjetische Delegation an Schalter zwei. Ihre Papiere, bitte. Die Reichsdelegation wird an Schalter eins abgefertigt.

### 12. [minor] dlg.c3.cond_02 + dlg.c3.cond_02.irina + dlg.c3.cond_02.secrecy (Node c3a_cond_02)

**Befund:** Fachlich fragt ein Eisenbahner bei einem plombierten Kurierwagen nach dem Begleiter, nicht nach dem Schaffner (der steht vor ihm). „Begleiter“ bereitet zudem die Pointe der Passkontrolle vor (‚Begleitperson Kurierwagen 4‘ – der Begleiter ist er selbst); cond_03 („Ein Wagen mit Schlüssel …“) funktioniert unverändert.

**Aktuell:** Ein Wagen ohne Schaffner?

**Vorschlag:** Basis: „Ein Wagen ohne Begleiter?“ · irina: „In Karsk hätte unsere Dispatcherin so einen Wagen längst aufgeschrieben. Ohne Begleiter?“ · secrecy: „Ich frage nur. Ein Wagen ohne Begleiter?“

### 13. [minor] dlg.c3.ctrl_05.irina (und dlg.c3.cond_02.irina)

**Befund:** „meine Dispatcherin“ macht Irina zu Alexeis Untergebener; sie ist Kollegin (Slice-Journal: „Kollegin am Verladebahnhof Karsk“, Rollenkarte: „Fahrdienstleiterin“). „Dispatcherin“ selbst ist als sowjetischer bzw. Reichsbahn-Begriff in Alexeis Mund vertretbar – entweder bewusst so belassen oder einheitlich „Fahrdienstleiterin“.

**Aktuell:** Davon wusste ich nichts. Gegengezeichnet hat meine Dispatcherin – für die Gleise, nicht für einen Wagen.

**Vorschlag:** Davon wusste ich nichts. Gegengezeichnet hat unsere Dispatcherin – für die Gleise, nicht für einen Wagen. (cond_02.irina entsprechend „unsere Dispatcherin“)

### 14. [minor] dlg.c3.ctrl_02 (Node c3a_ctrl_02, Elena)

**Befund:** Eine Konferenzdolmetscherin von 1964, die auf Genauigkeit besteht, sagt „dolmetschen“; „übersetzen“ passt zu ihrem Kleingedruckten-Satz (Schriftliches, el_07), nicht zur mündlichen Arbeit am Schalter. Alexeis laienhaftes „übersetzt“ in react.search_elena darf bleiben.

**Aktuell:** Ich übersetze für die Kommission. Er fragt nach dem Zweck Ihrer Reise.

**Vorschlag:** Ich dolmetsche für die Kommission. Er fragt nach dem Zweck Ihrer Reise.

### 15. [minor] obj.c3a_conductor, obj.c3a_control, obj.c3b_log, obj.c3b_booth (data/v3/locale_de.json)

**Befund:** Die Slice-Aufgaben nutzen durchgehend die volle Imperativform („Untersuche“, „Vergleiche“, „Prüfe“, „Lege“); Kapitel 3 mischt verkürzte Formen („Frag“, „Geh“, „Hol“, „Such“) mit „Prüfe die Abfahrtstafel.“ und „Lies …“ – in der Aufgabenliste des Tagebuchs sichtbar uneinheitlich.

**Aktuell:** Frag den Schaffner nach dem versiegelten Wagen.

**Vorschlag:** Frage den Schaffner nach dem versiegelten Wagen. · Gehe durch die Passkontrolle. · Hole das Dolmetscherprotokoll aus dem Protokollbüro. · Suche Elena Weiss in Kabine 2.

### 16. [minor] item.c3_weighbill.description (data/v3/locale_de.json)

**Befund:** „2 410 kg“ mit normalem Leerzeichen kann am Zeilenende umbrechen („2 / 410 kg“) und ist eine moderne DIN-Schreibweise; 1964 schrieb man „2410 kg“ oder „2.410 kg“.

**Aktuell:** Ladung „Akten, Anlage C“, 2 410 kg. Plombe C-17/44 mit Gegensiegel der Kommission. Empfänger: Sekretariat der Kommission.

**Vorschlag:** Ladung „Akten, Anlage C“, 2410 kg. Plombe C-17/44 mit Gegensiegel der Kommission. Empfänger: Sekretariat der Kommission.

### 17. [minor] cin.c3.tohall.time, cin.c3.close.train, item.c3_departures.name, dlg.c3.react.share_protocol (Uhrzeiten; auch Abfahrtstafel und Protokollblatt der Art-Streams)

**Befund:** Uhrzeiten mit Doppelpunkt („9:40 Uhr“, „23:40“, im Protokoll „10:02“) sind die DIN-5008-Schreibweise der 1990er; 1964 stand in Fahrplänen, Protokollen und auf Titelkarten „9.40 Uhr“ / „23.40“. Derzeit immerhin konsistent – entweder überall auf die Punktform umstellen (dann auch die gezeichnete Tafel und das Protokollblatt) oder bewusst beim Doppelpunkt bleiben.

**Aktuell:** Palais der Kommission, 9:40 Uhr.

**Vorschlag:** Palais der Kommission, 9.40 Uhr. · „23.40 Uhr, Gleis 5. Ein Sonderzug ohne Halt nach Kordon-17.“ · „Sonderfahrt 23.40“ · „… Heute Nacht um 23.40 Uhr fährt ein Zug ohne Halt nach Kordon-17. Jetzt wissen Sie auch etwas.“ (139)

### 18. [minor] char.conductor.role (data/locale/de_c3_characters.json)

**Befund:** „Zugbegleiter“ ist der DB-Begriff der 1990er, „Besatzung“ gehört zu Schiff und Flugzeug; 1964 hieß es Schaffner/Zugschaffner und Zugpersonal.

**Aktuell:** Zugbegleiter des Korridor-Express, gemischte Besatzung

**Vorschlag:** Zugschaffner des Korridor-Express, gemischtes Zugpersonal

### 19. [minor] sys.journal.person.conductor.note (data/locale/de_c3_characters.json)

**Befund:** Gibt cond_05 falsch wieder: Der Schaffner sagt „Jede Woche einer“ (jede Woche ein solcher Wagen, mal von der einen, mal von der anderen Seite), nicht dass Wagen vier wöchentlich fährt.

**Aktuell:** Ein Eisenbahner aus dem Reich. Zählt Wagen, keine Akten – und weiß, dass Wagen vier jede Woche fährt.

**Vorschlag:** Ein Eisenbahner aus dem Reich. Zählt Wagen, keine Akten – und weiß, dass jede Woche so ein Wagen mitfährt.

### 20. [minor] ui.c3.protocol.subtitle (data/locale/de_c3_ui.json)

**Befund:** Die beiden bestehenden Rätsel tragen im Untertitel den Fiktionshinweis („… fiktiv, keine echte Signalvorschrift.“ / „… kein echtes Baudokument.“), passend zur world_note in puzzles.json; das Protokollrätsel nicht.

**Aktuell:** Eröffnungssitzung · Tagesordnungspunkt 4 „Anlage C – Logistikintegration“

**Vorschlag:** Eröffnungssitzung · Tagesordnungspunkt 4 „Anlage C – Logistikintegration“ – fiktive Sitzung, kein echtes Protokoll.

### 21. [minor] ui.c3.protocol.incomplete, ui.c3.protocol.instruction, ui.c3.protocol.undo, ui.c3.protocol.controls

**Befund:** „legen“ ohne Partikel wirkt unvollständig (Signalrätsel: „Lege … ein“); „Zurück“ als Rücknahme-Taste kollidiert mit ui.back „Zurück“ – das Signalrätsel sagt deshalb „Zurücknehmen“.

**Aktuell:** Lege zuerst alle vier Karten.

**Vorschlag:** Lege zuerst alle vier Karten ab. · instruction: „Lege die Namenskarten in der Reihenfolge ab, in der zu Anlage C gesprochen wurde. Das Protokoll nennt nur Uhrzeit und Mikrofon – die Sitzordnung verrät, wer an welchem Mikrofon saß.“ · undo: „Zurücknehmen“ · controls: „1–4 Karte legen · Rücktaste zurücknehmen · Enter prüfen · Esc schließen“

### 22. [minor] documentation/C3_DESIGN.md#Titel (Z. 1) und Zitat Z. 6–8; §2.5 vs. §2.7; item.c3_booth_log.description

**Befund:** Typografie im Vertrag: öffnendes „ mit geradem Schlusszeichen " im Titel und im Zitat aus FUTURE_CHAPTER_ARCS. Außerdem nennen §2.5 und item.c3_booth_log.description die Randnotiz ohne Ausrufezeichen, §2.7 und das gedruckte Protokollblatt (gen_ui_c3.py, veltrava_protocol_documents.json) mit – die Beweisbeschreibung sollte dem Druck folgen.

**Aktuell:** # CHAPTER 3 — „Der eiserne Frieden" (opening) — design contract

**Vorschlag:** Titel: „Der eiserne Frieden“; Zitat: „… Land ist.“; §2.5 und item.c3_booth_log.description: „RU: begleitete Personen – DE: Begleitgut!“

### 23. [minor] data/chapters/c3.json#line_variants (c3a_cond_02, c3a_ctrl_05, c3b_arr_02, c3b_meet_03, c3b_meet_07, c3b_meet_08)

**Befund:** Strukturell: Die Variantenpaare irina_trust/alexei_secrecy, konrad_evidence/office_suspicion und elena_trust/evidence_chain sind nach den Pflichtentscheidungen a1_choose, m1_choose und c3a_choose immer genau einseitig ≥ 1 (chapter_ext.gd: erste passende Bedingung gewinnt). Die sechs Basiszeilen in locale_de.json werden daher nie gesprochen; die Varianten sind die eigentlichen Zeilen und müssen das Gespräch allein tragen (Ursache des Bruchs in meet_07).

**Vorschlag:** Entweder in C3_DESIGN §2.8 festhalten, dass diese sechs Basiszeilen nur Fallback sind, oder je eine Variante zur Basiszeile machen (z. B. secrecy/suspicion als Basis, nur irina/evidence als Variante), damit locale_de.json den tatsächlich gehörten Text enthält und jede Variante gegen die Folgezeile gelesen wird.

