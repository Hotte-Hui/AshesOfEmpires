# Windows Quick Start — v0.4

1. **Keep a backup** of the downloaded ZIP. Extract to a normal writable directory such as `D:\Projects\AshesOfEmpires_Preproduction`.
2. Open `preview\ashes_story_lab_v0.4.html` in Edge/Chrome. This original pixel-art story-lab is playable offline; it is **not** the UE5 game. It can export/import JSON save files. The Python engine is the authoritative validator for exported state.
3. Open PowerShell in the extracted root folder.
4. If Python is installed, run:

```powershell
py -3 tools/validate_v3.py
py -3 tools/validate_integrity_v4.py
py -3 -m unittest discover -s tests -v
py -3 tools/story_engine_v4.py
```

5. Open Claude Code in **this extracted folder**. Give it this exact starting instruction:

> Lies zuerst `CLAUDE.md` und `PROJECT_STATUS.md`. Kontrolliere die UE5-Installation und führe sämtliche Offline-Tests aus. Erstelle anschließend ein echtes UE5-Projekt und zwei originale grafische Testschauplätze anhand `technical/UE5_RENDERING_ACCEPTANCE_V4.md`. Übernimm die Questlogik nur mit den Gate- und Speicherregeln von `tools/story_engine_v4.py`. Dokumentiere echte Ergebnisse und blockierte Aufgaben; behaupte keine Tests, die nicht gelaufen sind.

6. Claude should work in a separately tracked Unreal project directory if needed; do not erase this source package.
7. Before public use, clarify rights to third-party image references and produce original game artwork.

**Evidence boundary:** Offline story engine and browser demo are executed/tested; engine code and graphics have **not** been compiled/rendered in UE5 here.
