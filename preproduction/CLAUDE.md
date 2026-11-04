# ASHES OF EMPIRES — CLAUDE CODE HANDOFF v0.4 (mandatory)

**Reply in German.** Target Windows 11 / RTX 4090 / 32 GB system RAM. Use **Unreal Engine 5**; inspect installed version and C++/SDK tooling before starting. Do **not** switch to Godot and do not assume UE5 code supplied here has ever compiled.

## Read in this order
1. `README.md` and `PROJECT_STATUS.md` (truth-in-evidence)
2. `technical/DECISION_LOG.md` and `docs/STORY_BIBLE.md` (locked canon)
3. `docs/ART_DIRECTION.md` + the four local `references/` images (reference-only; rights unclear)
4. `technical/UE5_RENDERING_ACCEPTANCE_V4.md` (two-scene style experiment)
5. `data/v3/*.json` and `technical/QUEST_RUNTIME_INTEGRATION_V4.md` (canonical gameplay + semantics)
6. `tools/story_engine_v4.py` + `tests/test_story_engine_v4.py` + `tests/test_integrity_v4.py` (offline expected behavior)
7. `narrative/VERTICAL_SLICE_SCRIPT_V3.md`, `narrative/CHOICE_CONSEQUENCE_MATRIX_V4.md`, `production/shot_list_v4.csv`
8. `assets/planned/asset_registry_v4.csv`, `production/FIRST_72_HOURS_AT_PC.md`, `production/RISK_REGISTER_V4.md`

## First commands
From repository/project root: `py -3 tools/validate_v3.py`, `py -3 tools/validate_integrity_v4.py`, `py -3 -m unittest discover -s tests -v`, `py -3 tools/build_preview_v4.py`. Preserve outputs as a dated report. **Do not treat offline Python/browser test success as a UE5 compilation test.**

## Locked design
- 1964 alternate history, serious and explicitly critical treatment of Nazi dictatorship and Soviet repression; no celebratory extremist imagery or equivalence of different crimes. The fictional Great Hall is **not historical fact**.
- Two playable leads: Alexei Morozov (rail engineer) and Matthias Adler (architect/draftsman), scripted cinematic protagonist transitions, not unrestricted manual switching.
- Handcrafted-looking dramatic pixel art; closely analyze references but create all original distributable game visuals. Pixel readability/consistency over photorealistic technical maximalism.
- Hybrid side-on 2D / oblique 2.5D / selected 3D establishing shots. UE5 main engine, Blender when useful; source-controlled project with reproducible local build.
- Prioritize the **real, playtested 20–30-minute slice**; defer full six-chapter game until the first build proves feasible.

## The key bug to avoid
`ue5_seed/` contains a v0.3 **illustrative** `MarkObjectiveOnce` that does **not** enforce quest prerequisites or actual puzzle/dialogue solutions. Do not expose it to gameplay! Implement or port the transaction/gating flow in `tools/story_engine_v4.py`; objective completion must come only through properly validated interaction services. Maintain migration from v0.3 saves.

## Execution milestones
**M0 audit:** tool versions and installed capabilities, Git backup, tests, write `DEVELOPMENT_STATUS.md`.
**M1 visual proof:** original Karsk micro-scene and Berlin archive + fictional Great Hall background, render matrix and motion evidence in `evidence/`. Record actual settings, image comparison and FPS/frametime data. No city-scale geometry before style gate.
**M2 gameplay loop:** real character controller, interaction prompts, Irina's dialogue, two evidence inspections, symbolic puzzle, ledger, choice, working save/load; Windows launch proof.
**M3 second protagonist:** original Berlin scene, two-plan overlay, Emil dialogue, choice, cinematic character switch and finale; no bypass via skip.
**M4 delivery:** package Windows test build, check all scenes and four branch combinations, test corrupt saves/resumption, accessible UI and screenshot/performance gate.

## Evidence and approvals
- Maintain `DEVELOPMENT_STATUS.md`, `TEST_REPORT.md`, `NEXT_STEPS.md`. For each result label `AUTHORED`, `STATIC_VALIDATED`, `PYTHON_TESTED`, `BROWSER_TESTED`, `UE_COMPILED`, `PIE_TESTED`, `PACKAGED`, `USER_ACCEPTED` as appropriate.
- Never invent screenshots, metrics, test results or completed assets. A placeholder illustration is not reference-level final art.
- Ask approval before purchases, legal/rights assumptions, publication, changes to locked canon, major destructive edits or external account actions. No public upload by default.
- Prefer the simplest solution that demonstrably matches the visual identity; expensive RT/Lumen/Nanite/TSR features must earn their complexity by real side-by-side tests.

## Expected first response to user
Report environment specifics, results of validations, contents and limitations of the source package, top three next implementation actions and any genuine blockers. Proceed with development within the permitted environment; do not declare victory based solely on code generation.
