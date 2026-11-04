# Rätseldesign, Hinweise und QA

## PZ_SIGNAL – fiktives Lehrgerät, keine reale Betriebsanleitung
**Aussehen:** Drei mechanische Symbolkarten in einem ausgebauten, stromlosen Kontrollkasten. Nur eine Symbolreihenfolge ist die Lösung. Den Spielern wird das Prinzip durch das daneben hängende *fiktive* Demonstrationsdiagramm erklärt.

**Input:** Karten anklicken/umordnen. **Lösung:** square → circle → triangle. **Hinweis:** Auf dem Fahrplan sind Zeichen neben den drei Umbuchungen vermerkt; am Siegel befindet sich dieselbe Formengruppe. **Fehlversuch:** klare Rückmeldung, keine Sperre und keine Zeitstrafe. **Zwei Versuche:** optionaler Lösungsweg-Hinweis. **Reset:** manuell immer möglich. **Questwirkung:** nur bei echter Spielaktion `signal_restored = true` und objective complete, keine doppelten Effekte.

## PZ_BLUEPRINT – vereinfachte 2D-Overlayzeichnung
**Aussehen:** Zwei separate Papiere, die über ein Raster mit identischen Orientierungspunkten gelegt werden. Realer Städtebau wird nicht abgebildet.

**Input:** vier Raster-Richtungen, Rotation um 90-Grad-Schritte (aber Zielrotation 0), Einrasten bei passender Lage. **Lösung:** offset_x=2, offset_y=-1, rotation_steps=0. **Hinweis:** Der gleiche Schornstein und die gleiche Treppe sind auf beiden Zeichnungen zu sehen. **Fehlversuch:** neutrale Rückmeldung, beliebig viele Wiederholungen. **Gate:** beide Pläne müssen im Inventar sein.

## QA-Mindestfälle
- Falsche Eingabe sperrt Puzzle nicht.
- Neustart, Save/Load und Cinematic Skip führen nicht zu doppelten Events.
- UI-Texte bleiben ohne Farbwahrnehmung unterscheidbar.
- Storyfahnen ändern sich erst bei bestandenem Rätsel oder bewusster Spielerentscheidung.
