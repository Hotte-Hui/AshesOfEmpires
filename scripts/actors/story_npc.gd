extends "res://scripts/actors/npc.gd"
## NPC whose presence follows the story (Chapter 3+): visible only after `show_after` is complete and until
## `hide_after` is complete (objective ids; empty = no limit). Presentation only — the Story engine never
## asks NPCs anything. A hidden NPC leaves the "npcs" group so it neither talks nor affects dialogue docking.

@export var show_after := ""
@export var hide_after := ""

var _present := true


func _ready() -> void:
	super._ready()
	var st := get_node_or_null("/root/Story")
	if st:
		for sig in ["objective_completed", "state_replaced"]:
			if st.has_signal(sig):
				st.connect(sig, func(_x): _refresh())
	_refresh()


func is_present() -> bool:
	return _present


func _done(oid: String) -> bool:
	var st := get_node_or_null("/root/Story")
	return st != null and st.has_method("objective_state") and str(st.objective_state(oid)) == "complete"


func _refresh() -> void:
	var on := (show_after == "" or _done(show_after)) and (hide_after == "" or not _done(hide_after))
	_present = on
	visible = on
	process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	if on and not is_in_group("npcs"):
		add_to_group("npcs")
	elif not on and is_in_group("npcs"):
		remove_from_group("npcs")


func _process(delta: float) -> void:
	if _present:
		super._process(delta)
