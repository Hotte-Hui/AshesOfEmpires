# First 72 hours at the PC — prioritized milestones, NOT estimated completion times

This is a **sequence of work items**, not a promise of work duration. If implementation takes much longer, preserve quality gates.

## Milestone 0 — inventory and reproducibility
- Record installed UE5 major/minor, Windows SDK, Visual Studio C++ workloads, Blender version and free disk space in `DEVELOPMENT_STATUS.md`.
- Run all Python validation scripts/tests. Verify ZIP checksums and keep untouched source ZIP as a backup.
- Create private Git repository; `.gitignore` must exclude UE DerivedDataCache, Intermediate, Saved and generated builds, **not** original authored art.
- **Exit criteria:** new project opens from a known location with a reproducible launch path. Upload no files to public repos without permission.

## Milestone 1 — lookdev gates before city production
- UE5 micro-scene 1 `L_A1_Railyard`: a railcar, human silhouette, distant factories, one interactable object, original art only.
- UE5 micro-scene 2 `L_M1_Archive`: office table, original two-plan prop, window silhouette of fictional Große Halle and displaced civilians.
- Use `technical/UE5_RENDERING_ACCEPTANCE_V4.md` to test AA, Lumen, temporal stability and logical pixel grids. Keep performance evidence rather than subjective claims.
- **Exit criteria:** two static comparison sheets, 20 seconds total of camera movement captures per variant, art scorecards, documented winning pipeline.

## Milestone 2 — one complete gameplay loop
- Build authoritative quest flow. Demonstrate Irina talk -> two item inspections -> symbol puzzle -> ledger -> choice -> save -> restart -> load with identical outcome.
- UI shows available/locked goals. Make a fresh Windows build early; no need for city scenery yet.
- **Exit criteria:** no bypass through dialogue/puzzle skip, 4 tested branch combinations in offline reference and UE5 PIE; real Windows build reaches one coherent chapter endpoint.

## Milestone 3 — second protagonist and transition
- Implement Matthias office, overlay interaction, Emil dialogue, choice, readable journal, match cut and finale.
- Test skips, interruptions, loading and switch to the correct protagonist. Include comfort settings and accessibility notes.
- **Exit criteria:** player can begin and finish without developer console; objective events apply once, Windows build stable.

## Stop / escalate flags
- If a requested engine plugin or asset costs money: ask before purchase.
- If source/reference artwork license is unclear: treat as local lookdev only.
- If optimized GPU effects change pixel cluster stability: accept the simpler rendering solution and document why.
- If GPU time budget fails on RTX 4090: report numbers and change materials/shading deliberately; don't claim 4K/60 based on guesses.
