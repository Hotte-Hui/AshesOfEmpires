# UE5 technical architecture proposal (not yet implemented)

## Engine
Unreal Engine 5, exact installed version to be checked on PC. Windows target. Blender for architecture and props. Favor Blueprint for visual orchestration, C++ for reusable performance-sensitive systems if Claude can compile/test.

## Suggested modules
- GameInstanceSubsystem: narrative state, persistent progression.
- SaveGame: versioned story flags, quest states, inventory, scene spawn points.
- PlayerController: input routing and interaction targeting.
- ProtagonistData: data-driven Alexei/Matthias differences.
- CameraDirector: authored transitions, orthographic/perspective camera presets, Sequencer hooks.
- DialogueSubsystem: data-driven dialogue nodes, conditions and effects.
- QuestSubsystem: objective dependency graph and journal state.
- EvidenceSubsystem: discovered clues and deductions.
- ArtLookSubsystem: pixel-grid settings, palette profiles, postprocess presets.

## Camera/presentation
Use separate authored levels or sublevels for side-on 2D, oblique 2.5D and cinematic 3D. Avoid one camera model for all gameplay. Test fixed internal pixel resolution, nearest-neighbor presentation and UI compositing separately.

## Performance and visual tradeoffs
Lumen and Nanite are optional per-scene tools, not mandatory quality toggles. Hardware ray tracing may introduce noise/shimmer at low internal pixel resolutions. Profile on RTX 4090, but define lower presets. Target stable frame pacing before aggressive effects.

## Validation plan
1. Confirm installed UE5 version, plugins, compiler, GPU driver and disk space.
2. Generate a minimal UE5 project and verify opening in Editor.
3. Create one small scene for each presentation mode.
4. Compare screenshots and motion clips at 1080p/1440p/4K output.
5. Measure frame time and visual artifacts; record results.
6. Implement one end-to-end dialogue/quest/save path before content expansion.

## Asset licensing
Keep a manifest of source, author, license, modification, and distribution permissions. User-provided reference images are not licensed for incorporation by default.
