# Claude Code handoff — read first

You are continuing ASHES OF EMPIRES: THE LAST WINTER. This is a **preproduction package**, not a working UE5 game. Inspect `README.md`, `docs/`, `narrative/`, `technical/`, `data/` and `references/` before coding.

## Locked requirements
- **Unreal Engine 5**, not Godot. Verify the installed version rather than assuming one.
- User reference images are the visual authority: highly detailed, atmospheric pixel art; no photorealistic style drift.
- Alexei (Soviet railway engineer) and Matthias (German architect) alternate in **scripted cinematic story sections**, not freely.
- Story critically portrays both political systems without Nazi glorification or false equivalence.
- Hybrid 2D / 2.5D / selected 3D with consistent pixel-art rendering.

## First implementation goal
Create and verify a **20–30-minute playable vertical slice** with A1 Soviet railyard, M1 Berlin archive, a Great Hall exterior reveal, two investigation puzzles, two meaningful choices, persistent save state and a cinematic protagonist switch.

## Exact order
1. Audit package and image references; read `technical/DECISION_LOG.md`.
2. Check UE5, plugins, Blender and available build tools.
3. Execute `technical/RENDERING_PIPELINE.md` experiments before building the full city.
4. Use `data/quest_vertical_slice_v2.json` and `data/story_flags_v2.json` as **design inputs**, not as implemented UE data assets. Translate them into appropriate UE5 assets and code.
5. Implement according to `technical/IMPLEMENTATION_CONTRACT.md`.
6. Verify with `technical/TEST_PLAN.md`; document real evidence and limitations.
7. Keep `DEVELOPMENT_STATUS.md`, `TEST_REPORT.md`, `NEXT_STEPS.md` up to date.

## Scope and integrity
Do not promise AAA quality, complete campaign, working builds, FPS or tested gameplay without evidence. Ask before purchases, untrusted installs, publishing, destructive operations or overriding locked canon. Work autonomously within the project and report exactly what was accomplished.
