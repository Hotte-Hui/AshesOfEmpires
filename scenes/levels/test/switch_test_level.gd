extends "res://scripts/levels/level.gd"
## Test level of the in-level protagonist switch (TECHNICAL_ARCHITECTURE §12.11) — used by tests/test_switch.gd and
## the windowed check `-- --switch-demo=<dir>` (scenes/levels/test/switch_demo.gd). The Veltrava station art without
## any story hotspot, plus named spawns: the entry spawns of the four Story scenes the checks map onto this one file
## (Game.level_overrides: A1 → M1 → C3 station → C3 hall = Alexei → Konrad → Alexei → Konrad) and the spots the
## test switch settings name. Never part of the game: no Story scene points here by itself.

const SPAWNS := {
	"SP_A1_Platform": [200, 300],        # scene 1 (Alexei) entry
	"SP_M1_Arrival": [760, 296],         # scene 2 (Konrad) entry, used when he did not stand in before
	"SP_C3_Vestibule": [1180, 300],      # scene 4 (Konrad) entry
	"SP_Test_KonradWaits": [560, 292],   # scene 1 partner spot: Konrad waits here while Alexei is played
	"SP_Test_AlexeiPost": [380, 306],    # scene 2 partner spot: Alexei walks here after handing over
	"SP_Test_Switch": [980, 298],        # scene 4 switch_spawn: where Konrad takes over
}


func _ready() -> void:
	super._ready()
	var sp: Dictionary = manifest.get("spawns", {})
	for k in SPAWNS:
		sp[k] = SPAWNS[k]
	manifest["spawns"] = sp
