# Faithful UE5 implementation contract — reference to target behavior

**Canonical inputs:** `data/v3/{flags,quests,scenes,items,dialogue,puzzles,cinematics,locale_de}.json`. **Reference behavior:** `tools/story_engine_v4.py`. This package does not compile or run UE5. Claude must build the implementation against the installed UE5 version and the test contract below.

## Runtime boundaries
- **QuestState service / GameInstanceSubsystem**: owner of completed objectives/events, typed flags, active character, current scene, inventory and choice history.
- **Dialogue service**: controls line-by-line advancement, speaker and localized text; it alone may mark a dialogue objective complete at a terminal node.
- **Puzzle actors**: validate the authored symbolic sequence and plan overlay, with unlimited retries and voluntary hint after two failed attempts. Puzzle success is an event to the QuestState service; neither UI nor a public Blueprint callable function may bypass validation.
- **Scene director**: listens for `a1_completed`/`m1_completed`, requests scene transitions exactly once and plays/skips authored sequences without mutating story flags twice.
- **Save service**: writes a versioned snapshot and validates it before committing load; failures preserve current in-memory state. Autosave after meaningful checkpoints, never while state is half-applied.
- **UI**: world interactions display text in native-resolution UMG, not on a rasterized billboard that becomes unreadable at UHD.

## API proposals (NOT signatures proven to compile)
`QueryAvailableObjectives(SceneId)`, `TryInspect(ObjectiveId)`, `BeginDialogue(ObjectiveId)`, `AdvanceDialogue(ObjectiveId)`, `TryPuzzleSolution(ObjectiveId, TypedAnswer)`, `TryChoice(ObjectiveId, ChoiceId)`, `ConsumeCinematic(SequenceId)`, `TryFinishSlice()`, `SaveSnapshot(Slot)`, `LoadSnapshot(Slot)`.

If `MarkObjectiveOnce` is retained from `ue5_seed/`, it must be PRIVATE to an authoritative quest service. The v0.3 example explicitly lacks prerequisite checking and must **never** be wired directly to interactables.

## Implementation invariants
1. Objective can't complete without its prerequisites and correct current scene.
2. Dialogue objective requires terminal dialogue node; puzzle objective requires exact solution with clue ownership.
3. An objective, item, completion event and effect apply at most once, even after cutscene skip or load.
4. Replay/load rejects unknown IDs, incompatible save versions, impossible scene+protagonist pairs, duplicate progress and contradictory flags.
5. Two independent branches must not alter progression gating unless expressly authored.
6. Every cutscene can skip, and skip cannot skip mandatory story state or trigger scene change twice.
7. Save files can be copied/backed up and restored. When migrating v0.3 save version 2 to v0.4 reference version 3, retain verified progress and report unknown fields.

## Sequencer timing
Triggers are in `data/v3/cinematics.json`, and **all** three sequences must be referenced by a real objective/event. Sequence playback is presentational. If a level streams slowly, show a clean fade and keep user input disabled until the spawn anchor and UI are ready. Retry failed scene loads safely rather than completing goals silently.

## Evidence for acceptance
For every line item in `technical/TEST_MATRIX_V3.md` and this document, attach actual PIE screenshots or logs and a packaged-build run; record installed UE5 version, machine specs and whether tests are editor-only. Do not call the game finished because the offline HTML demo works.
