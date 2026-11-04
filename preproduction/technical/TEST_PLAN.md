# Verification plan — no UE5 environment assumed

## Automated tests to implement when UE5 is available
- T01 New game loads A1 with Alexei and controls enabled.
- T02 Signal puzzle supports correct solution, wrong attempt, reset and re-entry.
- T03 Ledger interaction advances objective exactly once.
- T04 Alexei choice updates exactly one intended flag.
- T05 Character switch loads M1 and selects Matthias.
- T06 Blueprint puzzle resolves only after both overlays are inspected.
- T07 Matthias choice persists after save/reload.
- T08 Save migration handles missing/new flags without crashing.
- T09 Skipping cinematics retains all quest-critical state.
- T10 Main menu -> new game -> slice ending -> menu works without debug commands.

## Manual visual QA
- V01 Character stays pixel-sharp during slow and fast camera pans.
- V02 No temporal ghosting around rain, silhouettes or animated signs.
- V03 2D/2.5D/3D shots feel like one art direction.
- V04 Dark environments preserve legible interactables.
- V05 Great Hall communicates scale and coercive state power, not ideological celebration.
- V06 UI and subtitles are legible at 1080p and 4K output.

## Performance QA
Capture actual resolution, graphics preset, average FPS, 1% low or representative frame-time distribution, GPU/CPU times, VRAM use, engine version and driver version. Do not fabricate metrics.

## Build QA
Run a packaged Windows build on a clean start, not only PIE. Record launch result, map travel, input, save/load and demo completion.

## Known status as of preproduction
**None of the UE5 tests have been executed.** These are acceptance criteria for later implementation.
