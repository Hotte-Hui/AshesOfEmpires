# v3 Data contract and runtime boundaries

All canonical files under `data/v3/`. Schema version 3, save version 2. IDs are stable lower-snake_case except actual UE level names `L_*`. Localization keys are required for all strings presented in-game.

## Objective state machine
`LOCKED -> AVAILABLE -> COMPLETE`, never regress except New Game. `requires` edges target objectives of the same quest; `requires_events` gate a quest by completed global events. One completion per objective; a choice requires one valid choice ID and applies its effects once. Completing the last objective adds the quest event once.

## Choice effects
`{ "delta": integer }` for integer flags (clamped by declared min/max), `{ "set": boolean }` for boolean flags. Effects applied atomically together with objective completion and inventory grant. For final branches, use **separate** effects, never a moral score.

## Save shape
```
{
  "save_version": 2,
  "flags": {"irina_trust": 0, "...": "..."},
  "completed_objectives": ["a1_talk_irina"],
  "completed_events": [],
  "inventory": [],
  "choice_history": {"a1_choose": "share_with_irina"},
  "current_scene": "L_A1_Railyard",
  "active_character": "alexei"
}
```
The ellipsis above is explanatory shorthand, **not valid JSON**. See `tools/simulate_slice.py` for exact generated saves.

## Migration
When loading `save_version=1`, fill missing flags from defaults, reject unknown references only with an explicit report, and mark `save_version=2`. Do not invent missing completed objectives. Test branch consistency before production migration.

## Unreal boundary
Export v3 JSON into validated UE5 Data Assets / Data Tables. Do not dynamically execute arbitrary JSON behavior in packaged game. UI/Sequencer handles presentation; quest runtime handles authoritative state. Align with the installed engine version. No Python requirement at runtime.
