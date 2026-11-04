# UE5 Pixel-Art High-Fidelity Rendering — Entwicklungsprotokoll

**Status: UNTESTED IN UE5.** UE-Version wird am PC festgestellt. Die folgenden Tests sind ein Entscheidungsverfahren, kein fertiger Shader. Ziel ist die Referenzqualität bei stabiler Kamerabewegung auf einer RTX 4090, nicht generische Fotorealistik.

## 1. Drei Kandidaten, die es real zu vergleichen gilt
- **S1 – Originalsprites/Paper2D:** Handautorisierte Pixelcluster, orthografische Kamera, Pixel-Texturen passend zum vorgegebenen Pixelmaßstab, wenige selektive Lichter. Gut für Innenräume und Figurennahaufnahmen.
- **S2 – Mischwelt:** Niedrig-/mittelkomplexe 3D-Geometrie, sorgfältig angepasste Materialfarben, 2D-Figuren auf Ebenen oder 3D-Figuren mit stilisiertem Licht. Gut für A1 Bahnhof, starke Tiefenstaffelung, Parallaxen.
- **S3 – Pixelgerendertes 3D:** 3D Monumentkulisse in UE5, kontrollierte Farbstufen/Kanten, ggf. gerenderter RenderTarget oder Post-Process-Pass, per Bild kontrollierte Pixelrasterung, ohne Erzwingen fotorealistischer Feintexturen. Gut für den Außen-Reveal der Großen Halle.

## 2. Lookdev-Parameter (nur als Startwerte)
- Logische Szenenauflösung testen: 320×180, 640×360, 960×540 für 16:9; UI getrennt in Display-Auflösung. Bei 3840×2160 ergeben sich exakte integer Faktoren 12, 6, 4; bei anderen Formaten neu beurteilen.
- Für native Pixel-Sprites mit klaren Kanten: Point/Nearest-Sampling evaluieren; zu grobe Texel bei 3D nicht pauschal mit denselben Sprite-Regeln behandeln.
- Architekturdetails über große Schatten-/Lichtcluster, nicht über zufälliges Pixelrauschen. Häufige 1-Pixel-Details nur an ausgewählten Fokuspunkten.
- Fixiere bei Kamerafahrten Pixelraster, Weltmaßstab und FOV; teste Subpixel-Schritte gegen Snap-to-grid statt Reflex „nur mehr AA“.
- Tonemapping, HDR und Belichtung kontrollieren; Auto-Exposure darf nicht zwischen 2D-/3D-Shots beliebig driften.
- Post-Process nach TSR/Tonemapping nur mit dokumentierter Blendable Location benutzen; Effekte, die Depth-Information vor TSR benötigen, separat erproben.

## 3. Experimente in zwei 20–25-m-Testszenen
| Variante | 2D | 2.5D | 3D | Messung |
|---|---|---|---|---|
| Baseline unlit/statische Lichter | ja | ja | ja | Formtreue, Kontrast |
| Lumen aus vs. an | nein/optional | ja | ja | Licht und Temporalstabilität |
| Nanite aus vs. an (geeignete komplexe Meshes) | nein | optional | optional | Bauaufwand, Qualitäts-/GPU-Effekt |
| FXAA / TAA / TSR / kein AA soweit unterstützt | ja | ja | ja | Ghosting vs. Spritekanten |
| Pixel-RenderTarget und nearest integer upscale | ja | ja | ja | native 4K-Ausgabe vs. logische Pixel |
| Pixelation vor/nach Tonemapping/TSR | optional | ja | ja | Pixelcluster, Tiefe, UI-Trennung |
| Volumetrischer Nebel gering/hoch | nein | ja | ja | Silhouettenlesbarkeit |

## 4. Bewertungsablauf
1. Statische Bilder am **gleichen** Kamerapunkt und Lichteinfall erzeugen.
2. Langsamen und schnellen zehnsekündigen Kamerapan aufnehmen; Bild für Bild auf Flimmern und Nachzieheffekte prüfen.
3. Frametimes, VRAM, GPU/CPU-Anteile messen (`stat unit`, `stat gpu`, Profiling-Tools nach UE-Version). Screenshots alleine beweisen keine FPS.
4. Scorecard `docs/ART_QA_SCORECARD.md` ausfüllen, bestes Pipeline-Rezept pro Szenenart festhalten; ggf. Mischnutzung.
5. Erst nach positiver Abnahme komplexe Assets, NPCs oder Quests im gleichen Look bauen.

## 5. Technische Hinweise (Epic-Dokumentation, auf Version prüfen)
- Paper2D ist ein Plugin für Sprite-/2D-Hybridspiele: https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-overview-in-unreal-engine
- Lumen ist per Modus und Szenenbudget unterschiedlich teuer; Surface Cache beachten: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine
- TSR/Post-Process-Position beeinflusst Schärfe und Bewegungsartefakte: https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-upscalers-in-unreal-engine
- Spielspeicherung mit SaveGame-Slots und ggf. AsyncSaveGameToSlot: https://dev.epicgames.com/documentation/en-us/unreal-engine/saving-and-loading-your-game-in-unreal-engine

**Keine Features auf Verdacht aktivieren:** Lumen, Nanite, Raytracing oder DLSS helfen nur, wenn sie in dieser Ästhetik nachweislich besser aussehen.
