extends "res://scripts/levels/c4/annex_level.gd"
## L_C4P2_Berlin — Konrad's two places of Chapter 4 part 2 in ONE level file (C4P2_DESIGN §4.2): the Ostbahnhof,
## Korridorbahnsteig K on Monday evening (Story scene L_C4P2_BerlinA, x 18–898) and the courtyard of
## Kolonnenstraße 14 on Tuesday night (L_C4P2_BerlinB, x 938–1902), separated by the permanent blocker
## `platform_end`.  Art: assets/environments/berlin_c4p2 (tools/pixelgen/env_c4p2_berlin.py).
##
## Everything of the round-9 two-places script (annex_level.gd: the "scene" filter decided at load, camera_zones,
## after / until / choice gates with fades, looks / grades per scene) plus:
## * the footsteps of the place: stone under the glass roof, snow in the courtyard (Game reads footstep_surface
##   when it sets the player up, after this level's _ready);
## * look() names the place ("station" | "courtyard") for tests and debug.
## Nothing here changes Story state.

const SURFACE := {"L_C4P2_BerlinA": "concrete", "L_C4P2_BerlinB": "snow"}


func _ready() -> void:
	footstep_surface = str(SURFACE.get(str(level_id), footstep_surface))
	super._ready()


## "station" | "courtyard": the place the level plays.
func look() -> String:
	if look_name != "":
		return look_name
	return "courtyard" if str(level_id) == "L_C4P2_BerlinB" else "station"
