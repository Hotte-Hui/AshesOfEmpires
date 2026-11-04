# Produktionsrealismus und Reihenfolge

## Scope
P0 = echter 20–30-minütiger Slice. Kein Combat, kein Open-World-Fahrzeugverkehr, keine vollständige Politik-Simulation und keine acht Stunden Prototyp-Level. Weltgröße entsteht durch kontrollierte Bildregie, nicht durch leer bespielbare Fläche.

## Abhängigkeitskette
`Referenzanalyse -> Rendervergleich -> Zwei Stil-Gates -> Projektstart -> Quest 1 -> Save-System -> Quest 2 -> Charakterwechsel -> UI-/Audio-Polish -> Windows-Build -> echtes Playtest-Protokoll`.

## Risikoregister
| Risiko | Wahrscheinlichkeit | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| 4K + Temporal AA erzeugt Shimmer | hoch | hoch | native Sprites, Postprocess-A/B, Bewegungstests |
| Lumen/RT verdeckt handgesetzte Pixel | mittel | hoch | Beleuchtung in gesondertem Pass; per Szene abschaltbar |
| 2.5D- und 3D-Figuren passen nicht zusammen | hoch | hoch | gemeinsamer Silhouetten-/Palettenstandard |
| Monumentkulisse kostet zu viel Zeit | hoch | mittel | Matte/Low-poly-Blockout mit art-directed Shader zuerst |
| Speicherstände brechen bei Datenänderungen | mittel | hoch | versionierter Save + automatische Migrationstests |
| Ein Abschnitt ist erst nach Story-Dialog fest | mittel | hoch | aufgabenkritische Zustandsänderung unabhängig von Sequencer |
| Verwechslung von Alternativgeschichte mit Geschichte | mittel | hoch | klare Fiktion-Markierung + historische kritische Rahmung |
| Rechte an Referenzkunst unklar | hoch | hoch | interne Referenz-only Assets, eigene Bilder produzieren |

## Stop/Go-Gates
G0: Python-Validierung erfolgreich, Material-/Assetliste dokumentiert.
G1: Zwei Lookdev-Szenen visuell abgenommen nach Scorecard (inkl. Pan-Videos).
G2: Quest A1 in UE Editor vollständig spielbar und speicherbar.
G3: Quest M1 und Charakterwechsel vollständig spielbar; Skip-Sicherheit getestet.
G4: Gepackter Windows-Slice läuft von sauberem Start, zwei echte Playtester liefern Feedback.

Schätzungen erst nach G1 anhand tatsächlich gemessener Asset- und Implementierungszeiten. Nie aus einem Python-PASS auf UE5-Fertigstellung schließen.
