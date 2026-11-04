# UE5-Import — konkrete Arbeitsvereinbarung

1. Verify actual UE version, toolchain, source-control workspace and plugin availability on the PC.
2. Make `Source/` / `Content/` project directories with Unreal Editor, not through a fake binary `.uasset` writer.
3. Convert stable v3 definitions to UStruct/DataAsset types. Suggested structures: `FStoryFlagDef`, `FQuestDefinition`, `FObjectiveDefinition`, `FDialogueNode`, `FStoryScene`, `FTrackedItem`; use FName for stable IDs and FText for localization.
4. Use `UGameInstanceSubsystem` or one dedicated state owner to persist across level loads, `USaveGame` for disk serialization; no duplicate flag stores in actors.
5. For choices, check unlocked state and valid option, apply effects, mark objective complete, emit event transactionally. Never put essential flag mutation in an optional Sequencer-only callback.
6. Map `L_A1_Railyard`, `L_M1_Archive`, `L_X1_Montage` to level assets after verifying map names. Keep current scene and active character synced to the state owner.
7. Import sprites only from your **own newly created art** or properly licensed sources; internal reference JPGs are not gameplay textures.
8. If using DataTables, generate UTF-8 CSV from the vetted canonical JSON, or directly author Data Assets with an Editor Utility; no unsupported file-format tricks. UE DataTable structs and CSV headers must match the target engine's import expectations.
9. Set test checkpoints in a clean packaged Windows build and exercise all four choice combinations.

The optional code under `ue5_seed/` is a compilation starting point only. Always use actual VS compiler output to judge compatibility.
