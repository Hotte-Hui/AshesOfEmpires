extends "res://scripts/actors/interactable.gd"
## Optional hotspot (observe / discover / chat) that only appears once an objective is complete
## (`after_objective`) and, optionally, disappears after another (`until_objective`). Used where an optional
## conversation shares a spot with a story NPC, so the story interaction always comes first and the two
## never compete for the same prompt. Story hotspots keep using plain interactable.gd (Story gates them).

@export var after_objective := ""
@export var until_objective := ""


func _done(oid: String) -> bool:
	var st := get_node_or_null("/root/Story")
	return st != null and st.has_method("objective_state") and str(st.objective_state(oid)) == "complete"


func is_active() -> bool:
	if after_objective != "" and not _done(after_objective):
		return false
	if until_objective != "" and _done(until_objective):
		return false
	return super.is_active()
