# Vertikaler Slice — Regie- und Interaktionsskript v3

**Spielzeit-Ziel 24 Minuten (20–30 akzeptiert), keine garantierte Laufzeit.** Zwei wählbare Ausgänge je Hauptfigur, aber fest montierter Wechsel. Lokalisierte Dialogtexte liegen in `data/v3/locale_de.json` und sind provisorisches Originalmaterial.

## 0:00–1:10 Vorspann A1
Totale des fiktiven sowjetischen Industriestadt-Bahnhofs Karsk. Tiefblaugraue Schatten, matte nasse Gleise, ein einzelnes Bernsteinfenster. Die Stadt bleibt sichtbar beschädigt und im Wiederaufbau; keine pauschale Behauptung vollständiger Zerstörung. Zuggeräusch wird leiser. Kamera senkt sich auf Alexei. Optionaler Skip führt direkt zum Startspawn.

## 1:10–3:10 Begegnung mit Irina
Der Spieler geht zur Kabine (visueller Wegweiser, nicht leuchtender Fantasy-Pfeil). Irina: „Der Zug kam pünktlich. Die Wagen in den Papieren kamen nicht mit.“ Alexei: „Was fehlt genau?“ Irina: „Drei Nummern. Und ein Ziel, das auf keiner öffentlichen Karte steht.“ Alexei: „Gib mir den Fahrplan und das Siegel. Ich prüfe es selbst.“ Irina: „Dann schau zweimal hin. Einmal für die Akte, einmal für die Menschen.“

**Gate:** Nur wenn Gespräch abgeschlossen, werden Siegel und Fahrplan aktiv.

## 3:10–5:50 Der erste Widerspruch
Untersuche in beliebiger Reihenfolge das doppelt gestempelte Siegel und den Dienstfahrplan. Der Eintrag C-17 ist noch ohne sichere Bedeutung. Beide Objekte erscheinen im Tagebuch, behalten den exakten Date-ID-Verweis. Die Kamera erlaubt langsames Zoomen, aber Text wird in einer UI-Lupe separat gerendert, nicht als unscharfer Welt-Text.

## 5:50–8:50 Signal-Puzzle
Ein **stromloses, erfundenes Lehrmodell** mit drei abstrakten Symbolen (Quadrat, Kreis, Dreieck). Die Spielerin/der Spieler ordnet sie anhand der lokalen Hinweise. Lösung `square, circle, triangle`; fehlerhafte Eingabe setzt nur das Rätsel zurück, keine realistische Manipulation eines Sicherungssystems. Zwei Fehlversuche -> freiwilliger Tipp. Erfolg setzt `signal_restored = true`.

## 8:50–10:40 Frachtbuch
Ledger ist jetzt einsehbar. Ein überarbeiteter Empfängerposten enthält C-17; Alexei erkennt, dass die Kennung in der öffentlich sichtbaren Zielortliste nicht auftaucht. `c17_confirmed = true`; Beweis ins Journal.

## 10:40–12:10 Alexeis Entscheidung
„Irina die vollständige Abweichung zeigen“ -> `irina_trust +1`; alternative „Hinweis vorerst für dich behalten“ -> `alexei_secrecy +1`. Wähle genau eine Option. Kurze Reaktion Irinas je nach Wahl; irreversibel nur innerhalb dieses Save-Zweigs. Ereignis `a1_completed` wird **einmalig** ausgelöst.

## 12:10–12:20 Match Cut
C-17-Stempel wird zur handschriftlichen Nummer auf einem Papierplan. Ambientes Metallklirren wird zum Berliner Tramgong. Skip erhält `a1_completed` und lädt M1, ohne die Kamerafahrt doppelt abzuspielen.

## 12:20–13:40 Matthias im Berliner Bauarchiv
Seitenansicht, enge Büros mit langen Fensterschatten. Matthias legt die Zeichnungsrolle auf einen Tisch. Draußen: Alltag einer politisch kontrollierten Stadt. Die fiktional vollendete Große Halle ist im weiten Hintergrund erkennbar, aber nicht von Anfang an als bewundernswertes Ziel ausgeleuchtet.

## 13:40–16:50 Zwei Pläne
Plan A ist die offiziell genehmigte Fassung, Plan B ein archivierter Vorentwurf. Einsammeln in beliebiger Reihenfolge. Plan-Overlay als Puzzle: Rotation 0, Verschiebung (+2, -1) auf einer rein visuellen Rasterkarte. Lösung zeigt einen verdeckten Korridor, der unter Vertragsserie C-17 erfasst ist. `blueprint_match_confirmed = true`.

## 16:50–17:05 Hallen-Reveal
Die Kamera fährt aus dem Archiv. Gewaltige Architektur dominiert den Horizont; unmittelbar im Vordergrund steht eine Familie vor einer versiegelten Wohnung. Der Moment dient der Kritik staatlicher Machtinszenierung und führt zurück zu den Aufzeichnungen.

## 17:05–19:50 Gespräch mit Emil
Emil: „Es gibt die Pläne, nach denen gebaut wird. Und die, die man abheftet.“ Matthias: „Beide tragen dieselbe Genehmigung. Das ist unmöglich.“ Emil: „Unmöglich ist im Archiv nur, was niemand eintragen darf.“ Matthias: „Hier ist eine zweite Wand. Dahinter führt ein Korridor weiter.“ Emil: „Die Kennung C-17 ist kein Raum. Sie ist eine Serie von Verträgen.“ Matthias erhält `ev_emil_note`.

## 19:50–21:20 Matthias' Entscheidung
„Eine eigene Kopie des Vermerks sichern“ -> `matthias_evidence +1`; Alternative „offizielle Stellungnahme verlangen“ -> `office_suspicion +1`. Beide Wege sind spielbar; die Konsequenz ist in der späteren Vollspielplanung anders. Ereignis `m1_completed` wird einmalig ausgelöst.

## 21:20–22:00 Abschlussmontage
Alexei und Matthias sehen getrennt dieselbe grenzübergreifende Vertragsserie. Sie haben sich noch **nicht** getroffen; das Treffen findet in Kapitel 3 statt. Ein neutraler Grenzplan wird sichtbar. Die Montage darf übersprungen werden, ohne den finalen Save-Eintrag zu verlieren.

## 22:00–24:00 Spielbare freie Sicht + Demo-Ende
Kurzes Journal-Resümee der gesammelten Belege, Menü/fortsetzen/neu beginnen. `slice_completed` und `slice_finished = true` setzen. Der finale Bildschirm ist erreichbar ohne Cheat, ohne Entwicklerkonsole und ohne todsicheren Quest-Softlock.

### Konsequenzplanung für später
- Irina-Vertrauen ermöglicht später glaubwürdigere Mitarbeit im Depot, aber kein automatisches „gutes“ Ende.
- Alexeis Verschwiegenheit kann kurzfristig Schutz gewähren, kostet langfristig Rechenschaft.
- Kopierte Unterlagen schaffen unabhängige Belege, werfen aber Besitz-/Sicherheitsrisiken auf.
- Offizielle Anfrage erzeugt Dokumenten-Spuren und Aufmerksamkeit; kein direktes Game-Over.

### Glaubwürdigkeit
C-17 ist **ein standardisierter Vertrag-/Projektseriencode des fiktiven Corridor Accord**, nicht ein universeller Zug-Code, der zufällig auch in Berlin ein Raum ist. Beide Funde zeigen unterschiedliche Teile derselben administrativen Struktur.
