# Implementation contract for Claude Code

## Work order and dependencies
1. Audit all files and references; verify actual installed UE5 version and plugins.
2. Set up a clean UE5 project, source control, content naming conventions, and a reproducible startup map.
3. Run the rendering experiment matrix before bulk art production.
4. Implement a **single playable Alexei loop**: approach Irina -> inspect signal box -> solve puzzle -> inspect ledger -> choice -> checkpoint.
5. Implement a **single playable Matthias loop**: enter archive -> compare plans -> talk to Emil -> choice -> checkpoint.
6. Connect with a Sequencer-driven transition, but provide a safe fallback scene load if cinematics fail.
7. Implement typed story flags and save versioning; add automated and manual tests.
8. Polish the slice, package for Windows, and verify from a fresh launch.

## Naming conventions
Maps: `L_A1_Railyard`, `L_M1_Archive`, `L_X1_Transition`.
Blueprints: `BP_` prefix; widgets: `WBP_`; materials: `M_`; material instances: `MI_`; textures: `T_`; sequences: `LS_`; data assets: `DA_`.

## System interfaces (design contracts, not implemented APIs)
- `StoryState`: get/set typed flags; apply choice transaction; save/load with version migration.
- `QuestRuntime`: resolve objective IDs, track prerequisites, emit quest events once.
- `InteractionComponent`: discover nearby interactables; show prompt; invoke action once.
- `DialogueRuntime`: conditional nodes, speaker portraits, choice effects, localization keys.
- `SceneDirector`: switch protagonist only at authorized narrative boundaries; fade, load, checkpoint.

## No-fake-completion rule
Every status report uses `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, or `VERIFIED` and includes a link/path to evidence. A screenshot does not prove a quest is playable. A successful editor launch does not prove a Windows package works.

## User approvals required
Purchases, publishing, untrusted installs, destructive operations outside project, and final narrative changes to locked canon. For reversible implementation details, decide autonomously and document.
