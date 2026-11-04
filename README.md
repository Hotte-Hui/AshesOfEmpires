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

## Inhalt der spielbaren Fassung (Vertical Slice)
1. **Kapitel 1 – „Das letzte Signal“** (Karsk, Alexei): Gespräch mit Irina, Bleisiegel, Fahrplan, Signalrätsel,
   Frachtbuch, erste Entscheidung.
2. **Übergang:** Der Waggon C-17 wird an einen Güterzug nach Westen gekoppelt – je nach Entscheidung steht Irina neben
   Alexei oder er bleibt allein. Der rote C-17-Stempel löst sich in Konrads Bleistiftvermerk auf, dann ein
   verschneiter Berliner Morgen, Konrad geht ins Archiv.
3. **Kapitel 2 – „Die falsche Zeichnung“** (Berlin, Konrad): Ankunft durchs Treppenhaus, Pförtner, Lesesaal, zwei
   Bauplanfassungen, Planabgleich, die belebte Große Halle (3D im Pixel-Look), Gespräch mit Emil, zweite Entscheidung.
4. **Finale:** zwei Schreibtische zur selben Minute – Berlin und Karsk – je nach beiden Entscheidungen, die
   C-17-Route zeichnet sich auf der Grenzkarte.

**Erkunden (optional):** 43 Entdeckungen und Gespräche – Details, Verstecke, Easter Eggs, Nebengespräche – und
**16 Karten „Reale Geschichte“**: was nach dem Krieg über NS-Staat und Sowjetunion aufgedeckt, bewiesen oder
zugegeben wurde (Wannsee-Protokoll, Reichsbahn-Fahrpläne, Germania, Katyn, Nowotscherkassk, Kyschtym …), sachlich
und mit Quellen. Alles im Tagebuch unter „Entdeckungen“ und „Geschichte“.

**Spielzeit (geschätzt, nicht mit Testspielern gemessen):** Hauptweg ca. 12–15 Minuten, mit allen Entdeckungen
ca. 25–30 Minuten.

**Historische Hoheitszeichen:** Hakenkreuz, Reichsadler, Hammer und Sichel erscheinen als Bildsprache der beiden
Regime in kritischem Zusammenhang (Sozialadäquanzklausel, § 86 Abs. 4 StGB). Unter *Einstellungen* lassen sie sich
abschalten; dann zeigt das Spiel fiktive Embleme.

## Für Entwickler
- Engine: **Godot 4.7.2** (GDScript, Forward+). Projektstruktur und Verträge: `documentation/TECHNICAL_ARCHITECTURE.md`.
- Tests:
  - Unit-Tests: `godot --headless --path . --script res://tests/run_all.gd`
  - Komplettdurchlauf über die Story-API: `godot --headless --path . -- --autoplay=share_with_irina,preserve_evidence [--autoplay-skip] [--autoplay-explore]`
  - Komplettdurchlauf nur über simulierte Tastendrücke: `godot --path . -- --inputplay=keep_private,request_explanation [--inputplay-skip] [--inputplay-explore] [--inputplay-shots=ORDNER]`
  - `--autoplay-explore` / `--inputplay-explore` besuchen zusätzlich jede Entdeckung und jedes Nebengespräch.
- Assets neu erzeugen (deterministisch): `py -3 -P tools/pixelgen/env_karsk.py`, `env_berlin.py`, `characters.py`,
  `gen_ui.py`, `gen_great_hall.py`, `icon.py`; Audio: `py -3 -P tools/audiogen/build_all.py`.
- Status, Testbericht und nächste Schritte: `documentation/DEVELOPMENT_STATUS.md`, `TEST_REPORT.md`, `NEXT_STEPS.md`.
