# Benutzeroberfläche und Zugänglichkeit

## Grundlayout
- Dialog unten mit Sprechername, Portrait, 2–4 Textzeilen; keine unlesbar winzige Pixel-Schrift. Skalierbare UI-Ebene **nach** Pixel-Szenenkomposition.
- Interaktionsprompt erscheint nur im Fokusbereich und zeigt aktuelle Eingabetaste; zeigt keinen Tipp, wenn Handlung noch blockiert ist.
- Tagebuch trennt `Ziele`, `Beweise`, `Personen` und `Entscheidungen`; keine falschen Vollständigkeitsversprechen.
- Untertitel bei Kamerafahrten stets auf konsistent kontrastierendem Hintergrund; Videosequenzen überspringbar.

## Optionen ab dem Slice
- Textskalierung (100/125/150%), Untertitel dauerhaft aktivierbar, Dialoggeschwindigkeit, Standard- und Hochkontrastmodus, alternative Tastatureingaben, Hinweisstärke beim Rätsel, Kamera-Bewegungsreduktion.
- Kontrast und Form statt nur Farbe: Signale, Cursor und Kartenrouten mit Symbolen/Labels unterscheiden.
- Einstellbare Pixelintensität nicht mit stilistischer Gleichgültigkeit verwechseln: alle Modi müssen art-directed sein.

## Fehlertoleranz
- Rätsel niemals irreversibel blockieren; nach Fehlversuchen ein Hinweis, erneutes Probieren jederzeit.
- Ein Klick/Interaktion darf Questabschluss und Flageffekt nur einmal auslösen.
- Ein übersprungener Film muss exakt die gleichen Quest-/Szenenübergänge wie der abgespielte Film liefern.
- Speicherpunkt vor und nach Charakterwechsel; korrekter Protagonist und Position müssen nach Laden wiederhergestellt sein.
- Alle Pflichttexte werden über `data/v3/locale_de.json` referenziert. Übersetzungen sind später eigene Assets; keine Hardcoded UI-Texte.
