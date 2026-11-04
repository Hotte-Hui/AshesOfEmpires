# CLAUDE CODE — verbindliche Übergabe v0.3

## Das Material ist umfangreicher als v0.2, aber noch KEIN UE5-Spiel
Bisher existieren Dokumentation, Referenzbilder, validierbare v3-JSON-Inhalte, ein Python-Story-State-Simulator und optionaler unkompilierter UE5-C++-Startcode. Lies `PROJECT_STATUS.md` vor jeder Statusmeldung.

## Phasen
**P00 — Audit:** Verzeichnisse und Daten lesen, `py -3 tools/validate_v3.py` und `py -3 -m unittest discover -s tests -v` protokollieren, Toolchain/UE-Version prüfen.

**P01 — Render-Gate:** Zwei kleine Lookszenen (Soviet Street & Berlin Monument) in drei Render-Varianten produzieren. Screenshots und Pan-Videos, `docs/ART_QA_SCORECARD.md`; keine Massenproduktion.

**P02 — Minimalprojekt:** UE5-Projekt in **neuem Arbeitsordner**, sauberes Input-Handling, Sprite-/3D-Kameraexperimente, Journal-/Dialog-UI, persistenter Story-State. `ue5_seed/` nur bei passend bestätigter Toolchain nutzen; Dateien nicht blind übernehmen.

**P03 — Alexei-Quest:** A1 end-to-end mit realem Lauf, fiktivem Rätsel, Evidence-UI, Entscheidung, Checkpoint. Die Prerequisite-DAG aus `data/v3/quests.json` umsetzen und nach jeder Änderung testen.

**P04 — Matthias-Quest:** M1 + Pläne + Emil + getrackte Konsequenz. Story-Transition per Sequencer oder sicherem Skip-Fallback.

**P05 — Demo-Ende:** X1 Cut, Save/Load unter Windows, Hauptmenü, Eingabealternativen, lokalisierte Texte und Fehlerfälle.

**P06 — Veröffentlichung nur nach Freigabe:** Asset-Rechte prüfen; neues Build und echte Spielerabnahme. Kein heimliches Hochladen oder Kauf fremder Assets.

## Data contract
- `data/v3/flags.json`: typed flags & events. Integer choices use `{ "delta": +1 }`; booleans `{ "set": true/false }`.
- `data/v3/quests.json`: objective DAG; `requires` internal to the quest, `requires_events` external; completing all objectives emits exactly one `completion_event`.
- `data/v3/dialogue.json`: presentation nodes; **quest choices are not duplicated as dialogue side effects**.
- `data/v3/scenes.json`: scene-change gates. Scene transitions must be idempotent with cinematics skipped.
- `data/v3/puzzles.json`: abstract fictional puzzle solution data, with unlimited retries and hints.
- `data/v3/locale_de.json`: all currently required UI strings and voice/dialogue keys.
- Simulator is a **reference contract**, not executable Unreal integration. Implement real BP/C++ equivalents and verify.

## Verifikationskriterien
- Evidence directories `evidence/`, reports `DEVELOPMENT_STATUS.md`, `TEST_REPORT.md`, `NEXT_STEPS.md` in UE project.
- Each production task status must be: TODO, IN_PROGRESS, BLOCKED, or VERIFIED with proof path.
- Visual performance: aspiration of sharp coherent 4K output and 60FPS on RTX 4090, real benchmark required.
- Preserve alternate history as fiction and refrain from celebratory or propagandistic presentation of the Nazi regime.
