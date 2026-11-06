extends "res://scripts/actors/gated_interactable.gd"
## Exploration spot of the commission's registry (scenes/levels/L_C3_Registry.tscn: four Story scenes in one level
## file, documentation/C3P2_DESIGN.md §7) -- used by every registry find, the mini-game "Die Suchkartei" included.
## In the running game the Story gates decide who can reach a find: yard and Annahme belong to Alexei until he has
## met Konrad (until_objective c3c_talk_konrad), card hall, Planarchiv and Magazin to Konrad until his decision about
## Blatt 7 (after c3c_talk_konrad, until c3d_choose); nothing during the fire. Inside a memory (§12.10) the Story
## state is the present one (or the snapshot taken at the scene's end), so objective gates say nothing there: the
## remembered scene decides instead (`memory_scenes`). Never touches Story.

## Story scenes (Game.memory_scene) in whose memory this spot can be used; empty = every scene of the file.
@export var memory_scenes := PackedStringArray()


func is_active() -> bool:
	var g := get_node_or_null("/root/Game")
	var mm = g.get("memory_mode") if g != null else null
	if mm is bool and mm:
		if not memory_scenes.is_empty() and not (str(g.get("memory_scene")) in memory_scenes):
			return false
		return _optional_active()
	return super.is_active()


## The optional part of interactable.is_active() without the objective gates (requirements of side-task steps hold).
func _optional_active() -> bool:
	if not (kind == "discover" or kind == "chat") or explore_id == "":
		return false
	var ex := _explore()
	if ex != null and ex.has_method("can_find") and not ex.is_found(explore_id) and not ex.can_find(explore_id):
		return false
	return not (once and used)
