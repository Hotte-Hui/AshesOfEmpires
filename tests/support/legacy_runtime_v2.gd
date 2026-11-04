extends RefCounted
## TEST FIXTURE — GDScript port of preproduction/tools/simulate_slice.py (v0.3 StoryRuntime).
## It produces authentic save_version 2 files for the migration tests and keeps the v0.3 regression tests
## (tests/test_data_and_runtime.gd). Not used by the game.
##
## Difference to the Python file: the protagonist after a1_completed is read from scenes.json instead of
## the hard-coded pre-rename id (this project's canonical id is "konrad"). Errors are returned as
## {ok: false, error} instead of raised.

const ENGINE := preload("res://scripts/story/story_engine.gd")

var flag_def: Dictionary = {}
var quests: Array = []
var scene_defs: Array = []
var defined_items := {}
var obj_index := {}
var state: Dictionary = {}


func _init() -> void:
	var r: Dictionary = ENGINE.load_data()
	var d: Dictionary = r["data"]
	flag_def = d["flags"]
	quests = d["quests"]["quests"]
	scene_defs = d["scenes"]["scenes"]
	for item in d["items"]["items"]:
		defined_items[item["id"]] = true
	for q in quests:
		for o in q["objectives"]:
			obj_index[o["id"]] = [q, o]
	start_new()


func start_new() -> Dictionary:
	var flags := {}
	for k in flag_def["flags"]:
		flags[k] = flag_def["flags"][k]["default"]
	state = {"save_version": flag_def["save_version"], "flags": flags, "completed_objectives": [],
		"completed_events": [], "inventory": [], "choice_history": {}, "current_scene": "L_A1_Railyard",
		"active_character": "alexei"}
	return state.duplicate(true)


func available() -> Array:
	var out: Array = []
	var finished := {}
	for o in state["completed_objectives"]:
		finished[o] = true
	var events := {}
	for e in state["completed_events"]:
		events[e] = true
	for q in quests:
		if q["scene"] != state["current_scene"] or not _subset(q.get("requires_events", []), events):
			continue
		for obj in q["objectives"]:
			if not finished.has(obj["id"]) and _subset(obj.get("requires", []), finished):
				out.append(obj["id"])
	return out


static func _subset(a: Array, s: Dictionary) -> bool:
	for x in a:
		if not s.has(x):
			return false
	return true


func _apply_effects(effects: Dictionary) -> void:
	for flag_name in effects:
		var meta: Dictionary = flag_def["flags"][flag_name]
		if meta["type"] == "boolean":
			state["flags"][flag_name] = effects[flag_name]["set"]
		else:
			var value: int = state["flags"][flag_name] + effects[flag_name]["delta"]
			state["flags"][flag_name] = mini(meta["max"], maxi(meta["min"], value))


func perform(objective_id: String, choice_id = null) -> Dictionary:
	if not obj_index.has(objective_id):
		return {"ok": false, "error": "Unknown objective: " + objective_id}
	if not available().has(objective_id):
		return {"ok": false, "error": "Objective locked or already complete: " + objective_id}
	var q: Dictionary = obj_index[objective_id][0]
	var obj: Dictionary = obj_index[objective_id][1]
	var effects: Dictionary
	if obj["type"] == "choice":
		var matches: Array = []
		for c in obj["choices"]:
			if c["id"] == choice_id:
				matches.append(c)
		if matches.size() != 1:
			return {"ok": false, "error": "A valid choice is required for " + objective_id}
		effects = matches[0]["effects"]
	else:
		if choice_id != null:
			return {"ok": false, "error": objective_id + " does not accept a choice"}
		effects = obj.get("effects", {})
	# Transactional: all validations above precede state mutation.
	_apply_effects(effects)
	state["completed_objectives"].append(objective_id)
	var item = obj.get("grant_item")
	if item != null and not (state["inventory"] as Array).has(item):
		state["inventory"].append(item)
	if obj["type"] == "choice":
		state["choice_history"][objective_id] = choice_id
	var all_done := true
	for o in q["objectives"]:
		if not (state["completed_objectives"] as Array).has(o["id"]):
			all_done = false
	if all_done:
		_complete_event(q["completion_event"])
	return {"ok": true, "error": "", "state": state.duplicate(true)}


func _protagonist_of(scene_id: String) -> String:
	for s in scene_defs:
		if s["id"] == scene_id:
			return s["protagonist"]
	return ""


func _complete_event(event: String) -> void:
	if not (state["completed_events"] as Array).has(event):
		state["completed_events"].append(event)
	if event == "a1_completed":
		state["current_scene"] = "L_M1_Archive"
		state["active_character"] = _protagonist_of("L_M1_Archive")
	elif event == "m1_completed":
		state["current_scene"] = "L_X1_Montage"
		state["active_character"] = "none"


func finale(_skip := false) -> Dictionary:
	if state["current_scene"] != "L_X1_Montage":
		return {"ok": false, "error": "Finale locked; complete both investigations"}
	# Skip is presentation only; it cannot remove mandatory story state.
	_complete_event("slice_completed")
	_apply_effects({"slice_finished": {"set": true}})
	return {"ok": true, "error": "", "state": state.duplicate(true)}


func save_json() -> String:
	return ENGINE.json_dumps(state, 2)


func load_json(text: String) -> Dictionary:
	var parsed: Dictionary = ENGINE.json_parse(text)
	if not parsed["ok"] or typeof(parsed["value"]) != TYPE_DICTIONARY:
		return {"ok": false, "error": "Malformed JSON"}
	var st: Dictionary = parsed["value"]
	var version = st.get("save_version", 1)
	if not (ENGINE.py_eq(version, 1) or ENGINE.py_eq(version, 2)):
		return {"ok": false, "error": "Unsupported save version"}
	if typeof(st.get("flags")) != TYPE_DICTIONARY:
		return {"ok": false, "error": "Save missing flags"}
	var canonical := {}
	for k in flag_def["flags"]:
		canonical[k] = flag_def["flags"][k]["default"]
	for flag_name in st["flags"]:
		var val = st["flags"][flag_name]
		if not canonical.has(flag_name):
			if ENGINE.py_eq(version, 1):   # old files may have removed flags
				continue
			return {"ok": false, "error": "Unknown flag: " + flag_name}
		var schema: Dictionary = flag_def["flags"][flag_name]
		if schema["type"] == "boolean":
			if typeof(val) != TYPE_BOOL:
				return {"ok": false, "error": "Flag %s invalid bool" % flag_name}
		else:
			if typeof(val) != TYPE_INT or val < schema["min"] or val > schema["max"]:
				return {"ok": false, "error": "Flag %s invalid integer" % flag_name}
		canonical[flag_name] = val
	var events = st.get("completed_events", [])
	var objectives = st.get("completed_objectives", [])
	var inventory = st.get("inventory", [])
	var choices = st.get("choice_history", {})
	if typeof(events) != TYPE_ARRAY or typeof(objectives) != TYPE_ARRAY or typeof(inventory) != TYPE_ARRAY \
			or typeof(choices) != TYPE_DICTIONARY:
		return {"ok": false, "error": "Invalid saved collections"}
	if _dups(events) or _dups(objectives):
		return {"ok": false, "error": "Duplicated progress entries"}
	for e in events:
		if not (flag_def["events"] as Array).has(e):
			return {"ok": false, "error": "Unknown progression identifier"}
	for o in objectives:
		if not obj_index.has(o):
			return {"ok": false, "error": "Unknown progression identifier"}
	for i in inventory:
		if not defined_items.has(i):
			return {"ok": false, "error": "Unknown progression identifier"}
	var scene = st.get("current_scene")
	if not (typeof(scene) == TYPE_STRING and scene != ""):
		scene = "L_X1_Montage" if events.has("m1_completed") else ("L_M1_Archive" if events.has("a1_completed") else "L_A1_Railyard")
	var expected_character := ""
	var known := false
	for s in scene_defs:
		if s["id"] == scene:
			known = true
			expected_character = s["protagonist"]
	if not known:
		return {"ok": false, "error": "Unknown scene"}
	if ENGINE.py_eq(version, 2) and not ENGINE.py_eq(st.get("active_character", expected_character), expected_character):
		return {"ok": false, "error": "Scene/character mismatch"}
	for objective in choices:
		if not obj_index.has(objective) or not objectives.has(objective):
			return {"ok": false, "error": "Dangling choice history"}
		var obj: Dictionary = obj_index[objective][1]
		var valid := false
		if obj["type"] == "choice":
			for c in obj["choices"]:
				if ENGINE.py_eq(c["id"], choices[objective]):
					valid = true
		if not valid:
			return {"ok": false, "error": "Invalid saved choice"}
	state = {"save_version": 2, "flags": canonical, "completed_objectives": objectives.duplicate(true),
		"completed_events": events.duplicate(true), "inventory": inventory.duplicate(true),
		"choice_history": choices.duplicate(true), "current_scene": scene, "active_character": expected_character}
	return {"ok": true, "error": "", "state": state.duplicate(true)}


static func _dups(a: Array) -> bool:
	var seen := {}
	for x in a:
		var key := var_to_str(x)
		if seen.has(key):
			return true
		seen[key] = true
	return false


## Port of simulate_slice.play_route.
static func play_route(a1 := "share_with_irina", m1 := "preserve_evidence", skip := false) -> RefCounted:
	var game = load("res://tests/support/legacy_runtime_v2.gd").new()
	var order := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal",
		"a1_inspect_ledger", "a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans",
		"m1_talk_emil", "m1_choose"]
	for objective in order:
		var choice = {"a1_choose": a1, "m1_choose": m1}.get(objective)
		var r: Dictionary = game.perform(objective, choice)
		if not r["ok"]:
			push_error("legacy play_route failed at %s: %s" % [objective, r["error"]])
	game.finale(skip)
	return game
