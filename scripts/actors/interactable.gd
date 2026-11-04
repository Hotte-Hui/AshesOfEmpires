class_name Interactable
extends Node2D
## A hotspot. Story hotspots (inspect/dialogue/puzzle/choice) are gated ONLY by the Story engine; a locked
## objective shows no prompt. Optional hotspots never change story state:
##   "observe"  — one line of thought (observe_key.prompt / observe_key.text)
##   "discover" — an exploration entry (TECHNICAL_ARCHITECTURE §12): detail, secret, easter egg or a find that
##                unlocks real-history cards; content lives in data/explore/<area>.json under `explore_id`
##   "chat"     — an optional conversation (data/explore/<area>.json entry of kind "chat", `explore_id`)

@export var objective_id := ""
@export_enum("inspect", "dialogue", "puzzle", "choice", "observe", "discover", "chat") var kind := "inspect"
@export var hotspot_id := ""            ## snaps to manifest hotspots[hotspot_id] (scene.json or explore_hotspots.json)
@export var hotspot_offset := Vector2.ZERO
@export var prompt_key := ""            ## default: per kind (ui.prompt.*) else ui.interact
@export var observe_key := ""           ## observe: "<key>.prompt" / "<key>.text"
@export var explore_id := ""            ## discover / chat: entry id in data/explore/*.json
@export var npc_id := ""                ## dialogue/choice/chat: speaking NPC (faces the player while talking)
@export var radius := 30.0
@export var prompt_height := 58.0       ## prompt anchor above the hotspot (world px)
@export var once := false               ## observe/discover/chat: hide after first use

var used := false


func _ready() -> void:
	add_to_group("interactables")


func is_optional() -> bool:
	return kind == "observe" or kind == "discover" or kind == "chat"


func is_active() -> bool:
	if is_optional():
		if kind != "observe" and explore_id == "":
			return false
		return not (once and used)
	if objective_id == "" or not Story.has_method("is_available"):
		return false
	return Story.is_available(objective_id)


func prompt_text() -> String:
	if kind == "observe" and observe_key != "" and Loc.has(observe_key + ".prompt"):
		return Loc.t(observe_key + ".prompt")
	if (kind == "discover" or kind == "chat") and explore_id != "":
		var ex = get_node_or_null("/root/Explore")
		if ex and ex.has_method("prompt_for"):
			var p := str(ex.prompt_for(explore_id))
			if p != "":
				return p
	if prompt_key != "":
		return Loc.t(prompt_key)
	var k := "ui.prompt." + kind
	return Loc.t(k) if Loc.has(k) else Loc.t("ui.interact")


## Presentation hint for the HUD prompt (§12): "new" = an exploration find not discovered yet (small amber
## spark), "found" = already discovered / already looked at (dimmed verb + tick), "" = story hotspot (plain).
## Read-only: never changes Story or Explore state.
func prompt_state() -> String:
	if (kind == "discover" or kind == "chat") and explore_id != "":
		var ex = get_node_or_null("/root/Explore")
		if ex != null and ex.has_method("is_found"):
			return "found" if ex.is_found(explore_id) else "new"
		return ""
	if kind == "observe":
		return "found" if used else ""
	return ""
