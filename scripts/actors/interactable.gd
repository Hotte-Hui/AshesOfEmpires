class_name Interactable
extends Node2D
## A story hotspot. Its availability is decided ONLY by the Story engine (gates); a locked objective shows
## no prompt.  "observe" hotspots are optional flavour (no story state change).

@export var objective_id := ""
@export_enum("inspect", "dialogue", "puzzle", "choice", "observe") var kind := "inspect"
@export var hotspot_id := ""            ## snaps to manifest hotspots[hotspot_id]
@export var hotspot_offset := Vector2.ZERO
@export var prompt_key := ""            ## default: per kind (ui.prompt.*) else ui.interact
@export var observe_key := ""           ## observe: "<key>.prompt" / "<key>.text"
@export var npc_id := ""                ## dialogue/choice: speaking NPC
@export var radius := 30.0
@export var prompt_height := 58.0       ## prompt anchor above the hotspot (world px)
@export var once := false               ## observe: hide after first use

var used := false


func _ready() -> void:
	add_to_group("interactables")


func is_active() -> bool:
	if kind == "observe":
		return not (once and used)
	if objective_id == "" or not Story.has_method("is_available"):
		return false
	return Story.is_available(objective_id)


func prompt_text() -> String:
	if kind == "observe" and observe_key != "" and Loc.has(observe_key + ".prompt"):
		return Loc.t(observe_key + ".prompt")
	if prompt_key != "":
		return Loc.t(prompt_key)
	var k := "ui.prompt." + kind
	return Loc.t(k) if Loc.has(k) else Loc.t("ui.interact")
