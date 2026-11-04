# Optional UE5 C++ bootstrap — NOT COMPILED

These are illustrative C++ starter files for a fresh Unreal Engine 5 C++ project. They are **not** a complete game and have not been opened in Unreal Editor. They provide a centralized `GameInstanceSubsystem` for basic state and an illustrative `USaveGame` representation only. No quest prerequisites, dialogue, scene travel, or JSON importer has been integrated; implement them according to `technical/DATA_CONTRACT_V3.md`.

1. Install/check your own UE5 and Microsoft C++ build tools on Windows first.
2. Create a native Unreal Engine C++ project if the installed engine version does not accept the provided `.uproject` template.
3. Merge **source files** with generated project according to engine conventions, keep the `ASHESOFEMPIRES_API` macro consistent with your module name.
4. Generate VS project files and compile. Address all actual compiler/editor errors; record them in `TEST_REPORT.md`.
5. Register the subsystem in your GameInstance and connect to data definitions/Blueprints after a successful compile.

Only the Python data simulator and tests have been run in this archive-building environment. Never claim C++ compiled.
