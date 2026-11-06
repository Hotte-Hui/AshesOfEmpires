class_name Interactable
extends Node2D
## A hotspot. Story hotspots (inspect/dialogue/puzzle/choice) are gated ONLY by the Story engine; a locked
## objective shows no prompt. Optional hotspots never change story state:
##   "observe"  — one line of thought (observe_key.prompt / observe_key.text)
##   "discover" — an exploration entry (TECHNICAL_ARCHITECTURE §12): detail, secret, easter egg or a find that
##                unlocks real-history cards; content lives in data/explore/<area>.json under `explore_id`
##   "chat"     — an optional conversation (data/explore/<area>.json entry of kind "chat", `explore_id`)
## Side tasks (§12.9): an exploration entry with unmet "requires" keeps its hotspot inactive (no prompt).
## `explore_chain` lets one hotspot (an NPC, an object) host several entries in order: `explore_id` always holds
## the current one — the first unfound entry (in chain order) whose requirements are met; while nothing new is
## findable it stays on the last found entry (re-readable), before anything is found on the first entry. A task
## step may come before an older entry of the same hotspot, so the step is offered first once it unlocks. In the
## scene, `explore_id` is the entry the chain shows in a new game. It follows Explore (found / restore / reset /
## reload); discover/chat nodes take the kind of the current entry. Game keeps reading `explore_id` and `kind`.

@export var objective_id := ""
@export_enum("inspect", "dialogue", "puzzle", "choice", "observe", "discover", "chat", "exit") var kind := "inspect"
@export var hotspot_id := ""            ## snaps to manifest hotspots[hotspot_id] (scene.json or explore_hotspots.json)
@export var hotspot_offset := Vector2.ZERO
@export var prompt_key := ""            ## default: per kind (ui.prompt.*) else ui.interact
@export var observe_key := ""           ## observe: "<key>.prompt" / "<key>.text"
@export var explore_id := ""            ## discover / chat: entry id in data/explore/*.json
@export var explore_chain := PackedStringArray()  ## §12.9: several entries on this hotspot, in order (sets explore_id)
@export var target_level := ""          ## exit: level to walk to (side levels such as the parade plaza)
@export var target_spawn := ""          ## exit: spawn in the target level
@export var npc_id := ""                ## dialogue/choice/chat: speaking NPC (faces the player while talking)
@export var radius := 30.0
@export var prompt_height := 58.0       ## prompt anchor above the hotspot (world px)
@export var once := false               ## observe/discover/chat: hide after first use (chains: per entry)

var used := false


func _ready() -> void:
	add_to_group("interactables")
	if not explore_chain.is_empty():
		var ex := _explore()
		if ex != null:
			for sig in ["state_changed", "data_reloaded"]:
				if ex.has_signal(sig) and not ex.is_connected(sig, refresh_chain):
					ex.connect(sig, refresh_chain)
		refresh_chain()


func _explore() -> Node:
	return get_node_or_null("/root/Explore") if is_inside_tree() else null


func is_optional() -> bool:
	return kind == "observe" or kind == "discover" or kind == "chat"


## The entry a chain points at right now (pure: Explore-like object with is_found / can_find).
static func pick_chain_step(chain: PackedStringArray, ex: Object) -> String:
	if chain.is_empty():
		return ""
	var last_found := ""
	for id in chain:
		if ex.is_found(id):
			last_found = id
		elif ex.can_find(id):
			return id
	return last_found if last_found != "" else chain[0]


## Re-evaluates the chain (connected to Explore.state_changed / data_reloaded). A change to an entry that is not
## found yet re-arms a `once` hotspot.
func refresh_chain() -> void:
	if explore_chain.is_empty():
		return
	var ex := _explore()
	if ex == null or not ex.has_method("can_find"):
		if explore_id == "":
			explore_id = explore_chain[0]
		return
	var pick := pick_chain_step(explore_chain, ex)
	if pick != explore_id:
		explore_id = pick
		if not ex.is_found(pick):
			used = false
	if kind == "discover" or kind == "chat":
		var e: Dictionary = ex.entry(explore_id) if ex.has_method("entry") else {}
		if not e.is_empty():
			kind = "chat" if str(e.get("kind", "")) == "chat" else "discover"


func is_active() -> bool:
	if kind == "exit":
		return target_level != ""
	if is_optional():
		if kind != "observe":
			if explore_id == "":
				return false
			var ex := _explore()
			if ex != null and ex.has_method("can_find") and not ex.is_found(explore_id) and not ex.can_find(explore_id):
				return false   # §12.9: its requirements are not found yet
		return not (once and used)
	if objective_id == "" or not Story.has_method("is_available"):
		return false
	return Story.is_available(objective_id)


func prompt_text() -> String:
	if kind == "observe" and observe_key != "" and Loc.has(observe_key + ".prompt"):
		return Loc.t(observe_key + ".prompt")
	if (kind == "discover" or kind == "chat") and explore_id != "":
		var ex := _explore()
		if ex and ex.has_method("prompt_for"):
			var p := str(ex.prompt_for(explore_id))
			if p != "":
				return p
	if prompt_key != "":
		return Loc.t(prompt_key)
	var k := "ui.prompt." + kind
	return Loc.t(k) if Loc.has(k) else Loc.t("ui.interact")


## Presentation hint for the HUD prompt (§12): "new" = an exploration find not discovered yet (small amber
## spark), "task" = the next step of a side task (§12.9: subtle task mark), "found" = already discovered /
## already looked at (dimmed verb + tick), "" = story hotspot (plain). Read-only: never changes Story or Explore.
func prompt_state() -> String:
	if (kind == "discover" or kind == "chat") and explore_id != "":
		var ex := _explore()
		if ex != null and ex.has_method("is_found"):
			if ex.is_found(explore_id):
				return "found"
			if ex.has_method("task_of") and str(ex.task_of(explore_id)) != "":
				return "task"
			return "new"
		return ""
	if kind == "observe":
		return "found" if used else ""
	return ""
