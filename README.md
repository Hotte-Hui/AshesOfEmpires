# ASHES OF EMPIRES: THE LAST WINTER

Ein filmisches Pixel-Art-Abenteuer mit zwei Hauptfiguren in einer **fiktiven** alternativen Geschichte (1964):
Alexei Morozov, Bahnhofsinspektor im sowjetischen Industriestädtchen Karsk, und Konrad Adler, Bauzeichner im
Berliner Bauarchiv. Beide stoßen unabhängig voneinander auf dieselbe rätselhafte Kennung: **C-17**.

> Die Welt, ihre Orte, die Große Halle und alle Hoheitszeichen sind erfunden. Das Spiel verherrlicht kein Regime;
> es erzählt von Menschen, die zwischen Pflicht, Angst und Gewissen entscheiden müssen.

## Spielen (Windows)
- **Fertiger Build:** `builds/windows/AshesOfEmpires.exe` starten (oder `Spiel starten.cmd`).
- **Aus dem Projekt:** Godot 4.7.2 öffnen → Projekt `C:\Spiele\AshesOfEmpires` → F5.

### Steuerung
| Aktion | Tastatur | Controller |
|---|---|---|
| Gehen | WASD / Pfeiltasten | linker Stick |
| Laufen | Umschalt (halten) | LB |
| Untersuchen / Sprechen / Weiter | E, Leertaste, Enter | A |
| Entscheidung wählen | Pfeiltasten + Enter oder 1 / 2 | Steuerkreuz + A |
| Tagebuch | J oder Tab | Back |
| Pause / Überspringen (Filmsequenz) | Esc | Start / Y |
| Dialogverlauf | H | X |
| Signalrätsel | 1–3 Karten legen, Rücktaste zurück, Enter prüfen | — |
| Planrätsel | Pfeiltasten verschieben, R drehen, Enter bestätigen | LB/RB drehen |

Alle Tasten lassen sich unter *Einstellungen → Steuerung* neu belegen. Dort gibt es auch Untertitel,
Textgröße, Textgeschwindigkeit, hohen Kontrast, reduzierte Bewegung und alle Lautstärken.

## Inhalt der spielbaren Fassung (Vertical Slice, geschätzt 10–15 Minuten)
1. **Kapitel 1 – „Das letzte Signal“** (Karsk, Alexei): Gespräch mit Irina, Bleisiegel, Fahrplan, Signalrätsel,
   Frachtbuch, erste Entscheidung.
2. **Übergang:** der rote C-17-Stempel wird per Match-Cut zum Bleistift-Vermerk auf einem Berliner Bauplan.
3. **Kapitel 2 – „Die falsche Zeichnung“** (Berlin, Konrad): zwei Bauplanfassungen, Planabgleich am Lichttisch,
   filmische Enthüllung der Großen Halle (3D im Pixel-Look), Gespräch mit Emil, zweite Entscheidung.
4. **Finale der Demo:** zwei Schreibtische, eine Kennung, eine Grenzkarte. Die Entscheidungen werden vermerkt
   und wirken sich (laut Story-Bibel) in den späteren Kapiteln aus.

## Für Entwickler
- Engine: **Godot 4.7.2** (GDScript, Forward+). Projektstruktur und Verträge: `documentation/TECHNICAL_ARCHITECTURE.md`.
- Tests:
  - Unit-Tests: `godot --headless --path . --script res://tests/run_all.gd`
  - Komplettdurchlauf über die Story-API: `godot --headless --path . -- --autoplay=share_with_irina,preserve_evidence [--autoplay-skip]`
  - Komplettdurchlauf nur über simulierte Tastendrücke: `godot --path . -- --inputplay=keep_private,request_explanation [--inputplay-skip] [--inputplay-shots=ORDNER]`
- Assets neu erzeugen (deterministisch): `py -3 -P tools/pixelgen/env_karsk.py`, `env_berlin.py`, `characters.py`,
  `gen_ui.py`, `gen_great_hall.py`, `icon.py`; Audio: `py -3 -P tools/audiogen/build_all.py`.
- Status, Testbericht und nächste Schritte: `documentation/DEVELOPMENT_STATUS.md`, `TEST_REPORT.md`, `NEXT_STEPS.md`.
