# Szenenatlas v3 — Produktionsaufträge für Level-/Art-Teams

## A1 — Verladebahnhof Karsk (fiktive sowjetische Industriestadt)
**Spielansicht:** Schräge orthografische 2.5D-Kamera, kleine autorisierte Kamerazonen. **Raum:** 65 m lange bespielbare Silhouette, aber nur ca. sechs Interaktionspunkte. Hohe Silos und ausgebrannte Fassaden als nicht begehbare Hintergrundschichten.

**Schlüsselbilder:** (1) Weitwinkel, kalter Morgendunst über Schienen, ein warmes Stellwerksfenster; (2) Alexei vor Schaltkasten; (3) Ledger-Nahaufnahme mit C-17. Referenz-Leitmotiv: industrielle Schatten, stumpfes Grün, isolierte Kupferlichter.

**Bewegungsroute:** Bahnsteig -> Irina/Kabine -> beschädigtes Siegel -> Fahrplantafel -> *stromloser fiktiver Übungskasten* -> Frachtbuch -> Irina -> Abblende. Optional: eine Person am Heizwagen, aber kein offener Nebenquest in Slice 1.

**Spielbare Gegenstände:** Ledger, Stempel, Fahrplan, Übungskasten, Irina. **Kulissen:** Kräne, Waggons, Nebel, Schornsteine, entfernte Menschen. **Nicht implementieren:** vollständiges Bahnstellwerk, realistisches Signalsystem, riesige offene Stadt.

**Audio:** Anhaltender Wind, entferntes Rangieren, Papier, gedämpfte Bahnhofsdurchsage. Das Ende der Szene nutzt die Metallklangfarbe als Übergang nach Berlin.

**Fail-safe:** Nach 2 falschen Symbolreihenfolgen bietet UI eine deutliche Markierung der drei Symbole; Rätsel bleibt ohne Strafe lösbar.

## M1 — Berliner Bauarchiv
**Spielansicht:** 2D-Seitenansicht für Büro, Kamera fährt bei einer filmischen Sequenz kurz über pixelgerenderte 3D-Kulisse. Architektur wirkt gigantisch, aber die Interaktionsräume bleiben eng und menschlich.

**Route:** Büroflur -> Zeichenbrett A -> Archivrolle B -> Plan-Overlay -> Emil -> Entscheidung -> Montage. **Licht:** Bernsteinfarbene Lampen, blaugraue Tageslichter, tiefe, bewusst lesbare Schatten.

**Fiktionale Große Halle:** Als im Alternativjahr 1964 vollendeter Bau sichtbar; in unserer Geschichte existierte sie nicht. Die Szene zeigt die Unterdrückungsarchitektur kritisch: gewaltige Flächen gegenüber kleinen Wartenden, abgeriegelter Wohnraum, unterschwellige Kontrolle. Sie ist **nicht** frei begehbarer 3D-Level im ersten Slice.

**Fail-safe:** Zwei Planmarkierungen sind auch in Graustufen und ohne Rot-Grün-Unterscheidung erkennbar; optionale Einrastfunktion.

## X1 — Grenzkorridor-Montage
15–25 Sekunden aus präzisen Einzelbildern, kein neuer bespielbarer Ort: Alexei und Matthias besitzen unabhängig Hinweise auf denselben internationalen **Vertragsseriencode C-17**, nicht denselben Bahnhofs- oder Raumschlüssel. Damit ist die Verbindung innerhalb der Welt plausibel.

**Ende:** Untertitelkarte, Demo-Ende, tatsächlicher Save-Checkpoint, Rückkehr ins Menü.

## Mini-Lookdev-Szenen (vor Levelproduktion)
- `LD_SovietStreet`: 20 m Straße, drei Tiefenebenen, zwei Lichter, eine Figur, simulierte Kamerabewegung.
- `LD_BerlinMonument`: 25 m Platz und stark vereinfachte Große-Halle-Silhouette, ein ziviler Vordergrundmaßstab, exakte Palette.
- Beide müssen in Bewegung in 1080p und 4K überzeugen; sonst erst Stil-/Renderpipeline verbessern, **kein Asset-Massenbau**.

## Camera consistency
Fixiere je Einstellungsart: (a) logische Pixelhöhe, (b) world-to-texel Maßstab, (c) Kontrastkurve, (d) Haut-/Stoff-Farbfamilien, (e) gewählte Schärfe- und AA-Strategie. Ein Kameraschnitt darf die Pixelgröße nicht unmotiviert verdoppeln.
