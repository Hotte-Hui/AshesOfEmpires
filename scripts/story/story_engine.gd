extends Node
## Story — authoritative story/quest state (autoload "Story").
##
## GDScript port of preproduction/tools/story_engine_v4.py with the same semantics:
## prerequisite gating, scene/protagonist correctness, dialogue completes only at its terminal node,
## typed puzzle answers with clue ownership, hint after N failed attempts, choice transactions applied
## once, completion events once, cinematic queue/consume (skip has no state effect), finale gating and a
## replay-validated save format (format "ashes_of_empires_story_reference_v4", save_version 3) with
## migration of v0.3 saves (save_version 2).
##
## GDScript has no exceptions: every mutating call returns {ok: bool, error: String, error_key: String, ...}.
## `error` is the technical (English) message of the Python reference, `error_key` a Loc key with the
## German player-facing text (data/locale/de_system.json). Failed calls never change state.
##
## Canonical data is read at runtime from res://data/v3/*.json (character id "konrad", see
## TECHNICAL_ARCHITECTURE §5.1). The data is validated once on load (port of validate_v3.py and the data
## part of validate_integrity_v4.py); invalid data disables the engine with a clear error.

signal objective_completed(id: String)
signal event_fired(id: String)
signal flag_changed(name: String, value: Variant)
signal item_granted(id: String)
signal cinematic_queued(id: String)
signal scene_changed(scene_id: String)
## Emitted after new_game() ("new_game") or a successful load_json() ("load"). Per-item signals are NOT
## replayed in these cases; listeners should re-read the state (current_scene, journal(), ...).
signal state_replaced(reason: String)

const FORMAT := "ashes_of_empires_story_reference_v4"
const VERSION := 3
const LEGACY_VERSION := 2
const MAX_SAVE_BYTES := 128 * 1024
const MAX_ATTEMPTS := 100000
const DATA_DIR := "res://data/v3"
const DATA_FILES := ["flags", "quests", "items", "scenes", "dialogue", "puzzles", "cinematics", "locale_de",
	"reference_manifest"]
const OBJECTIVE_TYPES := ["inspect", "dialogue", "puzzle", "choice"]
const LOCKED_CINEMATICS := ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains", "LS_C3_ToHall", "LS_C3_Close",
	"LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves",
	"LS_C4_Homeward", "LS_C4_Number", "LS_C4_Card", "LS_C4_Stamp", "LS_C4_Voices"]   # Chapter 4 part 1 (C4_DESIGN §2.9)
## Hard-coded in the Python reference as well (finale()).
const FINALE_SCENE := "L_X1_Montage"
const FINALE_EVENT := "slice_completed"
const FINALE_FLAG := "slice_finished"
const SAVE_KEYS := ["format", "save_version", "flags", "completed_objectives", "completed_events", "inventory",
	"choice_history", "current_scene", "active_character", "dialogue_progress", "puzzle_attempts",
	"cinematics_seen", "finale_viewed"]

## Read-only views of the authoritative state.
var current_scene: String:
	get:
		return str(_core.state["current_scene"]) if _core else ""
	set(_value):
		push_warning("Story.current_scene is read-only; scenes change only through story events.")
var active_character: String:
	get:
		return str(_core.state["active_character"]) if _core else ""
	set(_value):
		push_warning("Story.active_character is read-only.")
## Deep copy of the full state (same keys as the Python reference). Mutating it has no effect.
var state: Dictionary:
	get:
		return _core.snapshot() if _core else {}
	set(_value):
		push_warning("Story.state is read-only; use load_json() to replace it.")

var _db: DB = null
var _core: Core = null


func _init() -> void:
	_db = DB.shared()
	if _db.ok:
		_core = Core.new(_db)


# =====================================================================================================
# Public API — lifecycle
# =====================================================================================================

## Starts a new game (start scene, default flags). Emits state_replaced("new_game").
func new_game() -> Dictionary:
	if not _db.ok:
		return _data_error()
	_core.new_game()
	state_replaced.emit("new_game")
	return {"ok": true, "error": "", "error_key": "", "state": _core.snapshot()}


## True when the canonical data loaded and validated.
func data_ok() -> bool:
	return _db.ok


func data_error() -> String:
	return _db.error


func snapshot() -> Dictionary:
	return _core.snapshot() if _core else {}


# =====================================================================================================
# Public API — queries
# =====================================================================================================

func available() -> Array[String]:
	var out: Array[String] = []
	if _core:
		for id in _core.available():
			out.append(str(id))
	return out


func is_available(objective_id) -> bool:
	return _core != null and Util.is_str(objective_id) and _core.available().has(str(objective_id))


## "locked" | "available" | "complete" (unknown ids report "locked").
func objective_state(objective_id) -> String:
	if _core == null or not Util.is_str(objective_id):
		return "locked"
	var id := str(objective_id)
	if (_core.state["completed_objectives"] as Array).has(id):
		return "complete"
	if _core.available().has(id):
		return "available"
	return "locked"


func flag(flag_name) -> Variant:
	if _core == null or not Util.is_str(flag_name):
		return null
	return _core.state["flags"].get(str(flag_name))


func flags() -> Dictionary:
	return (_core.state["flags"] as Dictionary).duplicate(true) if _core else {}


## Integer story meter (relationship/consequence flag such as irina_trust). 0 for unknown/non-integer.
func relationship(flag_name) -> int:
	if _core == null or not Util.is_str(flag_name) or not _db.flags_def.has(str(flag_name)):
		return 0
	if _db.flags_def[str(flag_name)]["type"] != "integer":
		return 0
	return int(_core.state["flags"][str(flag_name)])


## {name: {value, min, max, default}} for every integer flag, in data order.
func relationships() -> Dictionary:
	var out := {}
	if _core == null:
		return out
	for fname in _db.flag_order:
		var meta: Dictionary = _db.flags_def[fname]
		if meta["type"] == "integer":
			out[fname] = {"value": int(_core.state["flags"][fname]), "min": meta["min"], "max": meta["max"],
				"default": meta["default"]}
	return out


func has_item(item_id) -> bool:
	return _core != null and Util.is_str(item_id) and (_core.state["inventory"] as Array).has(str(item_id))


func inventory() -> Array[String]:
	var out: Array[String] = []
	if _core:
		for id in _core.state["inventory"]:
			out.append(str(id))
	return out


func choice_history() -> Dictionary:
	return (_core.state["choice_history"] as Dictionary).duplicate(true) if _core else {}


func completed_objectives() -> Array[String]:
	var out: Array[String] = []
	if _core:
		for id in _core.state["completed_objectives"]:
			out.append(str(id))
	return out


func completed_events() -> Array[String]:
	var out: Array[String] = []
	if _core:
		for id in _core.state["completed_events"]:
			out.append(str(id))
	return out


func has_event(event_id) -> bool:
	return _core != null and Util.is_str(event_id) and (_core.state["completed_events"] as Array).has(str(event_id))


func is_finished() -> bool:
	return has_event(FINALE_EVENT)


func is_finale_viewed() -> bool:
	return _core != null and bool(_core.state["finale_viewed"])


func puzzle_attempts(objective_id) -> int:
	if _core == null or not Util.is_str(objective_id):
		return 0
	return int(_core.state["puzzle_attempts"].get(str(objective_id), 0))


## True once the failed attempts reach the puzzle's hint_after_attempts. False when the objective is not an
## available puzzle (the Python reference raises in that case).
func puzzle_hint_available(objective_id) -> bool:
	if _core == null:
		return false
	var r: Dictionary = _core.puzzle_hint_available(objective_id)
	return r["ok"] and r["available"]


func pending_cinematics() -> Array[String]:
	var out: Array[String] = []
	if _core:
		for id in _core.pending_cinematics():
			out.append(str(id))
	return out


## Loc key naming the current chapter (quest title of the scene, or the scene title for the montage).
func chapter_key() -> String:
	if _core == null:
		return ""
	var scene: Dictionary = _db.scenes.get(_core.state["current_scene"], {})
	var quest_id = scene.get("associated_quest")
	if Util.is_str(quest_id) and _db.quest_by_id.has(str(quest_id)):
		return str(_db.quest_by_id[str(quest_id)]["title_key"])
	return str(scene.get("title_key", ""))


## Copy of the objective definition ({} if unknown).
func objective_def(objective_id) -> Dictionary:
	if not _db.ok or not Util.is_str(objective_id) or not _db.objectives.has(str(objective_id)):
		return {}
	return (_db.objectives[str(objective_id)][1] as Dictionary).duplicate(true)


## Quest definition (without the objective list) owning the objective ({} if unknown).
func quest_for(objective_id) -> Dictionary:
	if not _db.ok or not Util.is_str(objective_id) or not _db.objectives.has(str(objective_id)):
		return {}
	var q: Dictionary = (_db.objectives[str(objective_id)][0] as Dictionary).duplicate(true)
	q.erase("objectives")
	return q


## Quest of the current scene ({} for the montage).
func current_quest() -> Dictionary:
	if _core == null:
		return {}
	var scene: Dictionary = _db.scenes.get(_core.state["current_scene"], {})
	var quest_id = scene.get("associated_quest")
	if not Util.is_str(quest_id) or not _db.quest_by_id.has(str(quest_id)):
		return {}
	var q: Dictionary = (_db.quest_by_id[str(quest_id)] as Dictionary).duplicate(true)
	q.erase("objectives")
	return q


func item_def(item_id) -> Dictionary:
	if not _db.ok or not Util.is_str(item_id) or not _db.items.has(str(item_id)):
		return {}
	return (_db.items[str(item_id)] as Dictionary).duplicate(true)


func scene_def(scene_id) -> Dictionary:
	if not _db.ok or not Util.is_str(scene_id) or not _db.scenes.has(str(scene_id)):
		return {}
	return (_db.scenes[str(scene_id)] as Dictionary).duplicate(true)


func cinematic_def(cinematic_id) -> Dictionary:
	if not _db.ok or not Util.is_str(cinematic_id):
		return {}
	for seq in _db.sequences:
		if seq["id"] == str(cinematic_id):
			return (seq as Dictionary).duplicate(true)
	return {}


## Puzzle definition of a puzzle objective (display_symbols, type, hint_after_attempts, ...). The solution
## is removed so UI code cannot short-circuit validation.
func puzzle_for(objective_id) -> Dictionary:
	var obj := objective_def(objective_id)
	if obj.get("type") != "puzzle":
		return {}
	var p: Dictionary = (_db.puzzles[obj["puzzle_id"]] as Dictionary).duplicate(true)
	p.erase("solution")
	return p


## [{id, text_key}] of a choice objective.
func choices_for(objective_id) -> Array:
	var out: Array = []
	var obj := objective_def(objective_id)
	if obj.get("type") != "choice":
		return out
	for c in obj["choices"]:
		out.append({"id": str(c["id"]), "text_key": str(c["text_key"])})
	return out


# =====================================================================================================
# Public API — player actions (the only way objectives complete)
# =====================================================================================================

func inspect(objective_id) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var before := _probe()
	return _settle(_core.inspect(objective_id), before)


## Starts (or resumes at the saved node) a dialogue objective. Returns the current line at top level.
func start_dialogue(objective_id) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var r: Dictionary = _core.start_dialogue(objective_id)
	if not r["ok"]:
		return r
	var out := _line_result(r["line"])
	out["error"] = ""
	out["error_key"] = ""
	out["objective"] = str(objective_id)
	return out


## {speaker, text_key, node, id, end, next} of the current node. On failure {ok: false, error, error_key}
## (there is deliberately no "error" key on success).
func current_dialogue_line(objective_id) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var r: Dictionary = _core.current_dialogue_line(objective_id)
	if not r["ok"]:
		return r
	return _line_result(r["line"])


## Advances one node. At the terminal node the objective completes: {ok, finished: true, changes}.
## Otherwise {ok, finished: false} plus the next line's fields.
func advance_dialogue(objective_id) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var before := _probe()
	var r: Dictionary = _core.advance_dialogue(objective_id)
	if not r["ok"]:
		return r
	if r["finished"]:
		return _settle({"ok": true, "error": "", "error_key": "", "finished": true}, before)
	var out := _line_result(r["line"])
	out["error"] = ""
	out["error_key"] = ""
	out["finished"] = false
	return out


## answer: Array/PackedStringArray of symbol ids (symbol_order) or {rotation_steps, offset_x, offset_y} of
## ints (overlay_alignment). A wrong typed answer is a valid call: {ok: true, solved: false}.
func solve_puzzle(objective_id, answer) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var before := _probe()
	var r: Dictionary = _core.solve_puzzle(objective_id, answer)
	if r["ok"]:
		r["hint_available"] = puzzle_hint_available(objective_id) if not r["solved"] else false
	return _settle(r, before)


func choose(objective_id, choice_id) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var before := _probe()
	return _settle(_core.choose(objective_id, choice_id), before)


## Marks a pending cinematic as seen. `skipped` is presentation only and never changes story state.
func consume_cinematic(cinematic_id, skipped: bool = false) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var r: Dictionary = _core.consume_cinematic(cinematic_id, skipped)
	if r["ok"]:
		r["skipped"] = skipped
	return r


## Completes the slice (once) when both investigations are done; idempotent afterwards.
func finale(skipped: bool = false) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var before := _probe()
	return _settle(_core.finale(skipped), before)


# =====================================================================================================
# Public API — persistence
# =====================================================================================================

## Byte-identical to Python's json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2).
func save_json() -> String:
	if _core == null:
		return ""
	return Json.dumps(_core.state, 2)


## Transactional, replay-validated load. On failure the live state is untouched.
## Returns {ok, error, error_key, warnings, state}. Emits state_replaced("load") on success.
func load_json(raw) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var replay := Core.new(_db)
	var r: Dictionary = replay.load_from_json(raw)
	if not r["ok"]:
		return r
	_core = replay
	state_replaced.emit("load")
	return {"ok": true, "error": "", "error_key": "", "warnings": r["warnings"], "state": _core.snapshot()}


## Dry run of load_json(): same validation, never touches the live state, emits nothing.
func validate_save_json(raw) -> Dictionary:
	if not _db.ok:
		return _data_error()
	var replay := Core.new(_db)
	var r: Dictionary = replay.load_from_json(raw)
	if not r["ok"]:
		return r
	return {"ok": true, "error": "", "error_key": "", "warnings": r["warnings"], "state": replay.snapshot()}


# =====================================================================================================
# Public API — journal
# =====================================================================================================

## {objectives:[{id, quest, text_key, state}], evidence:[{id, name_key, description_key, category}],
##  people:[ids met], decisions:[{objective, choice, text_key, objective_text_key}],
##  quests:[{id, title_key, character, state}], chapter_key, scene, character}
## Objectives are listed for every unlocked quest (state locked/available/complete; UIs usually hide
## "locked"). People = non-protagonist speakers of dialogue nodes the player has reached.
func journal() -> Dictionary:
	var out := {"objectives": [], "evidence": [], "people": [], "decisions": [], "quests": [],
		"chapter_key": chapter_key(), "scene": current_scene, "character": active_character}
	if _core == null:
		return out
	var s: Dictionary = _core.state
	var done := Util.as_set(s["completed_objectives"])
	var events := Util.as_set(s["completed_events"])
	var avail := Util.as_set(_core.available())
	for q in _db.quests:
		var unlocked := Util.subset(q.get("requires_events", []), events)
		var q_state := "complete" if events.has(q["completion_event"]) else ("active" if unlocked else "locked")
		out["quests"].append({"id": q["id"], "title_key": q["title_key"], "character": q["character"],
			"state": q_state})
		if not unlocked:
			continue
		for obj in q["objectives"]:
			var o_state := "complete" if done.has(obj["id"]) else ("available" if avail.has(obj["id"]) else "locked")
			out["objectives"].append({"id": obj["id"], "quest": q["id"], "text_key": obj["text_key"],
				"type": obj["type"], "state": o_state})
	for item_id in s["inventory"]:
		var item: Dictionary = _db.items[item_id]
		out["evidence"].append({"id": item_id, "name_key": item["name_key"],
			"description_key": item["description_key"], "category": item["category"]})
	out["people"] = _people_met()
	var history: Dictionary = s["choice_history"]
	for oid in s["completed_objectives"]:
		if not history.has(oid):
			continue
		var obj: Dictionary = _db.objectives[oid][1]
		for c in obj["choices"]:
			if c["id"] == history[oid]:
				out["decisions"].append({"objective": oid, "choice": c["id"], "text_key": c["text_key"],
					"objective_text_key": obj["text_key"]})
	return out


# =====================================================================================================
# Static helpers (used by Saves and the tests)
# =====================================================================================================

## Reads data/v3 (or another dir) into {stem: parsed JSON}. {ok, error, data}
static func load_data(dir: String = DATA_DIR) -> Dictionary:
	return DB.read_files(dir)


## Port of validate_v3.validate(). reference_root "" skips the reference-image existence check
## (the game never ships those images); tests pass e.g. "res://documentation".
static func validate_data(data: Dictionary, reference_root: String = "") -> Dictionary:
	return Validator.validate(data, reference_root)


## Port of the data part of validate_integrity_v4.deep_validate() (+ runtime safety checks).
static func deep_validate_data(data: Dictionary, reference_root: String = "") -> Dictionary:
	return Validator.deep_validate(data, reference_root)


## Python-json compatible parser: integers stay int, floats float; NaN/Infinity accepted like Python.
## {ok, value, error}
static func json_parse(text) -> Dictionary:
	return Json.parse(text)


## Python json.dumps(v, ensure_ascii=False, sort_keys=True, indent=indent); indent < 0 → compact.
static func json_dumps(value: Variant, indent: int = 2) -> String:
	return Json.dumps(value, indent)


## Python == semantics for JSON-like values (1 == 1.0 == True, deep containers).
static func py_eq(a: Variant, b: Variant) -> bool:
	return Util.py_eq(a, b)


## Container nesting depth of a parsed JSON value (iterative).
static func json_depth(value: Variant) -> int:
	return Json.depth(value)


## Forces the next engine instance to re-read data/v3 (hot reload during development).
static func reload_shared_data() -> void:
	DB.clear_shared()


# =====================================================================================================
# Internals — Node side (signals, results)
# =====================================================================================================

func _data_error() -> Dictionary:
	return {"ok": false, "error": "Story data invalid: " + _db.error, "error_key": "sys.err.data_invalid"}


func _line_result(line: Dictionary) -> Dictionary:
	return {"ok": true, "node": str(line["id"]), "id": str(line["id"]), "speaker": str(line["speaker"]),
		"text_key": str(line["text_key"]), "end": Util.truthy(line.get("end", false)),
		"next": str(line.get("next", ""))}


func _probe() -> Dictionary:
	var s: Dictionary = _core.state
	return {"flags": (s["flags"] as Dictionary).duplicate(), "objectives": (s["completed_objectives"] as Array).size(),
		"events": (s["completed_events"] as Array).size(), "items": (s["inventory"] as Array).size(),
		"scene": s["current_scene"], "pending": _core.pending_cinematics()}


## Computes what a successful action changed, attaches it as result.changes and emits the signals
## (after the state is fully committed, so handlers may call back into Story safely).
func _settle(result: Dictionary, before: Dictionary) -> Dictionary:
	if not result.get("ok", false):
		return result
	var s: Dictionary = _core.state
	var changes := {"flags": {}, "objectives": [], "items": [], "events": [], "cinematics": [], "scene": ""}
	for fname in _db.flag_order:
		var now = s["flags"][fname]
		var was = before["flags"][fname]
		if typeof(now) != typeof(was) or now != was:
			changes["flags"][fname] = now
	changes["objectives"] = (s["completed_objectives"] as Array).slice(before["objectives"])
	changes["items"] = (s["inventory"] as Array).slice(before["items"])
	changes["events"] = (s["completed_events"] as Array).slice(before["events"])
	for cid in _core.pending_cinematics():
		if not (before["pending"] as Array).has(cid):
			changes["cinematics"].append(cid)
	if s["current_scene"] != before["scene"]:
		changes["scene"] = s["current_scene"]
	result["changes"] = changes
	for fname in changes["flags"]:
		flag_changed.emit(fname, changes["flags"][fname])
	for id in changes["items"]:
		item_granted.emit(id)
	for id in changes["objectives"]:
		objective_completed.emit(id)
	for id in changes["events"]:
		event_fired.emit(id)
	for id in changes["cinematics"]:
		cinematic_queued.emit(id)
	if changes["scene"] != "":
		scene_changed.emit(changes["scene"])
	return result


func _people_met() -> Array:
	var people: Array = []
	var s: Dictionary = _core.state
	var visits: Array = []   # [objective_id, cursor or ""] — "" means the whole dialogue was played
	for oid in s["completed_objectives"]:
		if _db.objectives[oid][1]["type"] == "dialogue":
			visits.append([oid, ""])
	for oid in _db.objective_order:
		if (s["dialogue_progress"] as Dictionary).has(oid):
			visits.append([oid, s["dialogue_progress"][oid]])
	for v in visits:
		var dlg: Dictionary = _db.dialogues[_db.objectives[v[0]][1]["dialogue_id"]]
		var by_id: Dictionary = _db.dialogue_nodes[dlg["id"]]
		var node_id = dlg["entry_node"]
		var guard := 0
		while node_id != null and by_id.has(node_id) and guard <= by_id.size():
			guard += 1
			var node: Dictionary = by_id[node_id]
			var speaker := str(node["speaker"])
			if not _db.protagonists.has(speaker) and not people.has(speaker):
				people.append(speaker)
			if v[1] != "" and node_id == v[1]:
				break
			if Util.truthy(node.get("end", false)):
				break
			node_id = node.get("next")
	return people


# =====================================================================================================
# Inner class: Util — Python-equivalent value semantics
# =====================================================================================================

class Util extends RefCounted:
	static func is_str(v) -> bool:
		var t := typeof(v)
		return t == TYPE_STRING or t == TYPE_STRING_NAME

	static func is_int(v) -> bool:
		return typeof(v) == TYPE_INT

	static func is_num(v) -> bool:
		var t := typeof(v)
		return t == TYPE_INT or t == TYPE_FLOAT

	static func all_str(a) -> bool:
		if typeof(a) != TYPE_ARRAY:
			return false
		for x in a:
			if typeof(x) != TYPE_STRING:
				return false
		return true

	## Python truthiness for JSON-like values.
	static func truthy(v) -> bool:
		match typeof(v):
			TYPE_NIL:
				return false
			TYPE_BOOL:
				return v
			TYPE_INT, TYPE_FLOAT:
				return v != 0
			TYPE_STRING, TYPE_STRING_NAME:
				return str(v) != ""
			TYPE_ARRAY, TYPE_DICTIONARY:
				return not v.is_empty()
		return true

	static func as_set(a) -> Dictionary:
		var s := {}
		if typeof(a) == TYPE_ARRAY or typeof(a) == TYPE_PACKED_STRING_ARRAY:
			for x in a:
				s[x] = true
		return s

	## Every element of `a` is a key of `s`.
	static func subset(a, s: Dictionary) -> bool:
		if typeof(a) != TYPE_ARRAY:
			return false
		for x in a:
			if not s.has(x):
				return false
		return true

	static func same_keys(a: Dictionary, b: Dictionary) -> bool:
		if a.size() != b.size():
			return false
		for k in a:
			if not b.has(k):
				return false
		return true

	## Python: set(a) == set(b) and len(a) == len(b) where b is a list of unique strings
	## (an unhashable element raises TypeError in Python → treated as "not equal").
	static func same_strings_any_order(a: Array, b: Array) -> bool:
		if a.size() != b.size():
			return false
		for x in a:
			if typeof(x) != TYPE_STRING:
				return false
		return same_keys(as_set(a), as_set(b))

	static func deep_copy(v):
		if typeof(v) == TYPE_ARRAY or typeof(v) == TYPE_DICTIONARY:
			return v.duplicate(true)
		return v

	## Python == for JSON values: bool/int/float compare numerically, containers deeply, str by value.
	static func py_eq(a, b) -> bool:
		var ta := typeof(a)
		var tb := typeof(b)
		var na := ta == TYPE_INT or ta == TYPE_FLOAT or ta == TYPE_BOOL
		var nb := tb == TYPE_INT or tb == TYPE_FLOAT or tb == TYPE_BOOL
		if na or nb:
			if not (na and nb):
				return false
			if ta == TYPE_INT and tb == TYPE_INT:
				return a == b
			return float(a) == float(b)
		var sa := ta == TYPE_STRING or ta == TYPE_STRING_NAME
		var sb := tb == TYPE_STRING or tb == TYPE_STRING_NAME
		if sa or sb:
			return sa and sb and str(a) == str(b)
		if ta == TYPE_NIL or tb == TYPE_NIL:
			return ta == tb
		if ta == TYPE_ARRAY and tb == TYPE_ARRAY:
			if a.size() != b.size():
				return false
			for i in a.size():
				if not py_eq(a[i], b[i]):
					return false
			return true
		if ta == TYPE_DICTIONARY and tb == TYPE_DICTIONARY:
			if a.size() != b.size():
				return false
			for k in a:
				if not b.has(k) or not py_eq(a[k], b[k]):
					return false
			return true
		return false

	static func err(message: String, key: String) -> Dictionary:
		return {"ok": false, "error": message, "error_key": key}


# =====================================================================================================
# Inner class: Json — Python json.loads/json.dumps compatible (int-preserving)
# =====================================================================================================

class Json extends RefCounted:
	## Same container nesting limit as CPython 3.13's C scanner (measured: 2998 nested arrays/objects
	## parse, 2999 raise RecursionError). The parser is iterative, so deep input cannot overflow the
	## GDScript call stack.
	const MAX_DEPTH := 2998

	var s := ""
	var i := 0
	var n := 0
	var err := ""

	static func parse(text) -> Dictionary:
		if typeof(text) != TYPE_STRING:
			return {"ok": false, "value": null, "error": "Expected a string"}
		var p := Json.new()
		return p._run(text)

	func _fail(msg: String) -> Variant:
		if err == "":
			err = "%s: char %d" % [msg, i]
		return null

	func _ws() -> void:
		while i < n:
			var c := s.unicode_at(i)
			if c == 32 or c == 9 or c == 10 or c == 13:
				i += 1
			else:
				return

	static func _digit(c: int) -> bool:
		return c >= 48 and c <= 57

	## Iterative pushdown parser (json.decoder semantics: strict strings, NaN/Infinity literals,
	## duplicate keys → last value wins, nothing but whitespace after the document).
	func _run(text: String) -> Dictionary:
		s = text
		n = s.length()
		i = 0
		err = ""
		if n > 0 and s.unicode_at(0) == 0xFEFF:
			return {"ok": false, "value": null, "error": "Unexpected UTF-8 BOM"}
		var stack: Array = []   # open containers
		var keys: Array = []    # pending key per open container (null for arrays)
		var value: Variant = null
		var need_value := true
		while true:
			if need_value:
				_ws()
				if i >= n:
					_fail("Expecting value")
					break
				var c := s.unicode_at(i)
				if c == 91 or c == 123:
					if stack.size() >= MAX_DEPTH:
						_fail("Maximum nesting depth exceeded")
						break
					i += 1
					_ws()
					if c == 91:
						if i < n and s.unicode_at(i) == 93:
							i += 1
							value = []
							need_value = false
						else:
							stack.append([])
							keys.append(null)
							continue
					else:
						if i < n and s.unicode_at(i) == 125:
							i += 1
							value = {}
							need_value = false
						else:
							var k = _key()
							if err != "":
								break
							stack.append({})
							keys.append(k)
							continue
				else:
					value = _scalar()
					if err != "":
						break
					need_value = false
			# A complete value: attach it to the open container (closing containers as they end).
			var done := false
			while true:
				if stack.is_empty():
					done = true
					break
				var top = stack.back()
				var is_array := typeof(top) == TYPE_ARRAY
				if is_array:
					top.append(value)
				else:
					top[keys.back()] = value
				_ws()
				if i >= n:
					_fail("Expecting ',' delimiter")
					break
				var d := s.unicode_at(i)
				if d == 44:
					i += 1
					if not is_array:
						_ws()
						keys[keys.size() - 1] = _key()
					need_value = true
					break
				if (is_array and d == 93) or (not is_array and d == 125):
					i += 1
					value = stack.pop_back()
					keys.pop_back()
					continue
				_fail("Expecting ',' delimiter")
				break
			if err != "" or done:
				break
		if err == "":
			_ws()
			if i != n:
				_fail("Extra data")
		if err != "":
			return {"ok": false, "value": null, "error": err}
		return {"ok": true, "value": value, "error": ""}

	## '"key"' followed by ':' (whitespace allowed around the colon).
	func _key() -> Variant:
		if i >= n or s.unicode_at(i) != 34:
			return _fail("Expecting property name enclosed in double quotes")
		var k = _string()
		if err != "":
			return null
		_ws()
		if i >= n or s.unicode_at(i) != 58:
			return _fail("Expecting ':' delimiter")
		i += 1
		return k

	func _scalar() -> Variant:
		var c := s.unicode_at(i)
		match c:
			34:
				return _string()
			110:
				return _literal("null", null)
			116:
				return _literal("true", true)
			102:
				return _literal("false", false)
			78:
				return _literal("NaN", NAN)
			73:
				return _literal("Infinity", INF)
		if c == 45 and s.substr(i, 9) == "-Infinity":
			i += 9
			return -INF
		if c == 45 or _digit(c):
			return _number()
		return _fail("Expecting value")

	func _literal(word: String, value: Variant) -> Variant:
		if s.substr(i, word.length()) == word:
			i += word.length()
			return value
		return _fail("Expecting value")

	func _number() -> Variant:
		var start := i
		if s.unicode_at(i) == 45:
			i += 1
		if i >= n:
			i = start
			return _fail("Expecting value")
		var c := s.unicode_at(i)
		if c == 48:
			i += 1
		elif c >= 49 and c <= 57:
			while i < n and _digit(s.unicode_at(i)):
				i += 1
		else:
			i = start
			return _fail("Expecting value")
		var is_float := false
		if i + 1 < n and s.unicode_at(i) == 46 and _digit(s.unicode_at(i + 1)):
			is_float = true
			i += 1
			while i < n and _digit(s.unicode_at(i)):
				i += 1
		if i < n and (s.unicode_at(i) == 101 or s.unicode_at(i) == 69):
			var j := i + 1
			if j < n and (s.unicode_at(j) == 43 or s.unicode_at(j) == 45):
				j += 1
			if j < n and _digit(s.unicode_at(j)):
				is_float = true
				i = j
				while i < n and _digit(s.unicode_at(i)):
					i += 1
		var tok := s.substr(start, i - start)
		if is_float:
			return tok.to_float()
		var digits := tok.trim_prefix("-")
		if digits.length() > 19 or (digits.length() == 19 and digits > ("9223372036854775808" if tok.begins_with("-") else "9223372036854775807")):
			return tok.to_float()   # beyond int64: Python keeps a big int; every consumer rejects such values anyway
		return tok.to_int()

	func _hex4(at: int) -> int:
		if at + 4 > n:
			return -1
		var v := 0
		for k in 4:
			var c := s.unicode_at(at + k)
			var d := -1
			if c >= 48 and c <= 57:
				d = c - 48
			elif c >= 97 and c <= 102:
				d = c - 87
			elif c >= 65 and c <= 70:
				d = c - 55
			if d < 0:
				return -1
			v = v * 16 + d
		return v

	func _string() -> Variant:
		i += 1
		var parts := PackedStringArray()
		var chunk := i
		while true:
			if i >= n:
				return _fail("Unterminated string")
			var c := s.unicode_at(i)
			if c == 34:
				parts.append(s.substr(chunk, i - chunk))
				i += 1
				return "".join(parts)
			if c == 92:
				parts.append(s.substr(chunk, i - chunk))
				i += 1
				if i >= n:
					return _fail("Unterminated string")
				var e := s.unicode_at(i)
				match e:
					34:
						parts.append("\"")
					92:
						parts.append("\\")
					47:
						parts.append("/")
					98:
						parts.append("\b")
					102:
						parts.append("\f")
					110:
						parts.append("\n")
					114:
						parts.append("\r")
					116:
						parts.append("\t")
					117:
						var cp := _hex4(i + 1)
						if cp < 0:
							return _fail("Invalid \\uXXXX escape")
						i += 4
						if cp >= 0xD800 and cp <= 0xDBFF and i + 6 < n and s.unicode_at(i + 1) == 92 and s.unicode_at(i + 2) == 117:
							var lo := _hex4(i + 3)
							if lo >= 0xDC00 and lo <= 0xDFFF:
								cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
								i += 6
						parts.append(String.chr(cp))
					_:
						return _fail("Invalid \\escape")
				i += 1
				chunk = i
				continue
			if c < 0x20:
				return _fail("Invalid control character")
			i += 1
		return null

	# ---------------------------------------------------------------- encoder
	## The encoder is recursive; nothing the game serialises nests deeper than a few levels.
	const MAX_DUMP_DEPTH := 256

	## Maximum container nesting of a value (iterative; scalars 0, [] 1, [[]] 2).
	static func depth(v: Variant) -> int:
		var best := 0
		var stack: Array = [[v, 1]]
		while not stack.is_empty():
			var item: Array = stack.pop_back()
			var x = item[0]
			var t := typeof(x)
			if t == TYPE_ARRAY or t == TYPE_DICTIONARY:
				best = maxi(best, item[1])
				var children: Array = x if t == TYPE_ARRAY else (x as Dictionary).values()
				for child in children:
					stack.append([child, item[1] + 1])
		return best

	static func dumps(v: Variant, indent: int = 2) -> String:
		var out := PackedStringArray()
		_enc(v, indent, 0, out)
		return "".join(out)

	static func _nl(indent: int, level: int) -> String:
		if indent < 0:
			return ""
		return "\n" + " ".repeat(indent * level)

	static func _enc(v: Variant, indent: int, level: int, out: PackedStringArray) -> void:
		if level >= MAX_DUMP_DEPTH:
			push_error("Story.Json: value nested deeper than %d levels serialized as null" % MAX_DUMP_DEPTH)
			out.append("null")
			return
		match typeof(v):
			TYPE_NIL:
				out.append("null")
			TYPE_BOOL:
				out.append("true" if v else "false")
			TYPE_INT:
				out.append(str(v))
			TYPE_FLOAT:
				out.append(float_repr(v))
			TYPE_STRING, TYPE_STRING_NAME, TYPE_NODE_PATH:
				out.append(quote(str(v)))
			TYPE_ARRAY, TYPE_PACKED_STRING_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_INT64_ARRAY, \
					TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_FLOAT64_ARRAY, TYPE_PACKED_BYTE_ARRAY:
				var arr: Array = Array(v)
				if arr.is_empty():
					out.append("[]")
					return
				out.append("[")
				var inner := _nl(indent, level + 1)
				for k in arr.size():
					if k > 0:
						out.append("," if indent >= 0 else ", ")
					out.append(inner)
					_enc(arr[k], indent, level + 1, out)
				out.append(_nl(indent, level))
				out.append("]")
			TYPE_DICTIONARY:
				var d: Dictionary = v
				if d.is_empty():
					out.append("{}")
					return
				var keyed := {}
				for k in d:
					keyed[key_str(k)] = d[k]
				var keys: Array = keyed.keys()
				keys.sort()
				out.append("{")
				var inner := _nl(indent, level + 1)
				for k in keys.size():
					if k > 0:
						out.append("," if indent >= 0 else ", ")
					out.append(inner)
					out.append(quote(keys[k]))
					out.append(": ")
					_enc(keyed[keys[k]], indent, level + 1, out)
				out.append(_nl(indent, level))
				out.append("}")
			TYPE_VECTOR2, TYPE_VECTOR2I:
				_enc([v.x, v.y], indent, level, out)
			_:
				push_warning("Story.Json: unsupported type %s serialized as null" % type_string(typeof(v)))
				out.append("null")

	static func key_str(k: Variant) -> String:
		match typeof(k):
			TYPE_STRING, TYPE_STRING_NAME:
				return str(k)
			TYPE_BOOL:
				return "true" if k else "false"
			TYPE_NIL:
				return "null"
			TYPE_FLOAT:
				return float_repr(k)
		return str(k)

	## Python repr for the common cases: integral floats "1.0", otherwise the shortest decimal that parses
	## back to the same double. Godot's String.to_float() is not correctly rounded for some 17-digit
	## inputs, so for those values the 17-significant-digit form is written (what Python's repr prints
	## there too); reading it back in Godot may then differ by one ulp. Story saves contain no floats.
	static func float_repr(f: float) -> String:
		if is_nan(f):
			return "NaN"
		if is_inf(f):
			return "Infinity" if f > 0 else "-Infinity"
		if f == 0.0:
			return "-0.0" if PackedFloat64Array([f]).to_byte_array()[7] >= 128 else "0.0"
		if f == floorf(f) and absf(f) < 1e16:
			return "%d.0" % int(f)
		for d in range(1, 18):
			var t := String.num(f, d)
			if t.to_float() == f:
				return t if t.contains(".") else t + ".0"
		var int_digits := maxi(1, int(floor(log(absf(f)) / log(10.0))) + 1)
		var t17 := String.num(f, clampi(17 - int_digits, 1, 17))
		return t17 if t17.contains(".") else t17 + ".0"

	static func quote(text: String) -> String:
		var out := PackedStringArray()
		out.append("\"")
		var start := 0
		var length := text.length()
		for k in length:
			var c := text.unicode_at(k)
			if c < 0x20 or c == 34 or c == 92:
				if k > start:
					out.append(text.substr(start, k - start))
				match c:
					34:
						out.append("\\\"")
					92:
						out.append("\\\\")
					10:
						out.append("\\n")
					13:
						out.append("\\r")
					9:
						out.append("\\t")
					8:
						out.append("\\b")
					12:
						out.append("\\f")
					_:
						out.append("\\u%04x" % c)
				start = k + 1
		if start < length:
			out.append(text.substr(start))
		out.append("\"")
		return "".join(out)


# =====================================================================================================
# Inner class: Validator — port of validate_v3.validate + validate_integrity_v4.deep_validate (data part)
# =====================================================================================================

class Validator extends RefCounted:
	var err := ""

	func ck(cond: bool, msg: String) -> bool:
		if not cond and err == "":
			err = msg
		return cond

	func bad() -> bool:
		return err != ""

	static func validate(d: Dictionary, reference_root: String = "") -> Dictionary:
		var v := Validator.new()
		var report: Dictionary = v._validate(d, reference_root)
		if v.bad():
			return {"ok": false, "error": v.err, "report": {}}
		return {"ok": true, "error": "", "report": report}

	static func deep_validate(d: Dictionary, reference_root: String = "") -> Dictionary:
		var v := Validator.new()
		v._validate(d, reference_root)
		var report := {}
		if not v.bad():
			report = v._deep(d)
		if not v.bad():
			v._runtime(d)
		if v.bad():
			return {"ok": false, "error": v.err, "report": {}}
		return {"ok": true, "error": "", "report": report}

	func unique(records, what: String) -> Dictionary:
		var ids := {}
		if not ck(typeof(records) == TYPE_ARRAY, what + ": expected a list"):
			return ids
		var listed: Array = []
		for r in records:
			if not ck(typeof(r) == TYPE_DICTIONARY and typeof(r.get("id")) == TYPE_STRING, what + ": record without string id"):
				return ids
			listed.append(r["id"])
			ids[r["id"]] = true
		ck(ids.size() == listed.size(), "Duplicate IDs in %s: %s" % [what, str(listed)])
		return ids

	func check_dag(records, label: String) -> void:
		var ids := unique(records, label)
		if bad():
			return
		var deps := {}
		for r in records:
			var req = r.get("requires", [])
			if not ck(Util.all_str(req), "%s: malformed requires" % r["id"]):
				return
			deps[r["id"]] = req
		for key in deps:
			if not ck(Util.subset(deps[key], ids), "%s: unknown prerequisites" % key):
				return
			if not ck(not (deps[key] as Array).has(key), "%s: self dependency" % key):
				return
		var visiting := {}
		var visited := {}
		for key in ids:
			if not _visit(key, deps, visiting, visited, label):
				return

	func _visit(node, deps: Dictionary, visiting: Dictionary, visited: Dictionary, label: String) -> bool:
		if visiting.has(node):
			ck(false, "%s: cycle at %s" % [label, node])
			return false
		if visited.has(node):
			return true
		visiting[node] = true
		for need in deps[node]:
			if not _visit(need, deps, visiting, visited, label):
				return false
		visiting.erase(node)
		visited[node] = true
		return true

	func localized(loc: Dictionary, key) -> bool:
		return ck(typeof(key) == TYPE_STRING and loc.has(key) and typeof(loc[key]) == TYPE_STRING
			and (loc[key] as String).strip_edges() != "", "Missing German text: %s" % str(key))

	func effects_valid(effects, flag_defs: Dictionary, context: String) -> void:
		if not ck(typeof(effects) == TYPE_DICTIONARY, "%s: malformed effects" % context):
			return
		for name in effects:
			if not ck(flag_defs.has(name), "%s: unknown flag %s" % [context, name]):
				return
			var kind = flag_defs[name]["type"]
			var effect = effects[name]
			if not ck(typeof(effect) == TYPE_DICTIONARY, "%s: malformed effect" % context):
				return
			if kind == "integer":
				ck(effect.size() == 1 and effect.has("delta") and Util.is_int(effect["delta"]), "%s: integer requires delta" % context)
			else:
				ck(effect.size() == 1 and effect.has("set") and typeof(effect["set"]) == TYPE_BOOL, "%s: boolean requires set" % context)
			if bad():
				return

	func _get_list(container, key: String, what: String) -> Array:
		if not ck(typeof(container) == TYPE_DICTIONARY and typeof(container.get(key)) == TYPE_ARRAY, "%s: missing list '%s'" % [what, key]):
			return []
		return container[key]

	func _validate(d: Dictionary, reference_root: String) -> Dictionary:
		for stem in DATA_FILES:
			if not ck(typeof(d.get(stem)) == TYPE_DICTIONARY, "%s: missing or not a JSON object" % stem):
				return {}
			if not ck(Util.py_eq(d[stem].get("schema_version"), 3), "%s: schema_version must be 3" % stem):
				return {}
		if not ck(Util.py_eq(d["flags"].get("save_version"), 2), "save_version should be 2"):
			return {}
		var flag_defs = d["flags"].get("flags")
		if not ck(typeof(flag_defs) == TYPE_DICTIONARY, "flags: missing flag table"):
			return {}
		for name in flag_defs:
			var f = flag_defs[name]
			if not ck(typeof(f) == TYPE_DICTIONARY and (f.get("type") == "integer" or f.get("type") == "boolean"), "%s: unsupported flag type" % name):
				return {}
			if f["type"] == "integer":
				if not ck(Util.is_int(f.get("default")), "%s: invalid integer default" % name):
					return {}
				if not ck(Util.is_int(f.get("min")) and Util.is_int(f.get("max")), "%s: bounds must be int" % name):
					return {}
				if not ck(f["min"] <= f["default"] and f["default"] <= f["max"], "%s: default outside bounds" % name):
					return {}
			else:
				if not ck(typeof(f.get("default")) == TYPE_BOOL, "%s: invalid boolean default" % name):
					return {}
		# Python hard-codes the two protagonist ids; this project reads the (renamed) list from flags.json.
		var protagonists = d["flags"].get("protagonists")
		if not ck(Util.all_str(protagonists) and not protagonists.is_empty(), "flags: protagonists must be a list of ids"):
			return {}
		var loc = d["locale_de"].get("strings")
		if not ck(typeof(loc) == TYPE_DICTIONARY, "locale_de: missing strings"):
			return {}

		var scenes := _get_list(d["scenes"], "scenes", "scenes")
		var sceneids := unique(scenes, "scenes")
		if bad():
			return {}
		if not ck(sceneids.has(d["scenes"].get("start_scene")), "start scene missing"):
			return {}
		var events = d["flags"].get("events")
		if not ck(Util.all_str(events), "flags: events must be a list of ids"):
			return {}
		if not ck(Util.as_set(events).size() == events.size(), "duplicate events"):
			return {}
		var eventids := Util.as_set(events)
		var items := _get_list(d["items"], "items", "items")
		var itemids := unique(items, "items")
		if bad():
			return {}
		for item in items:
			if not ck(sceneids.has(item.get("scene")), "Item %s: unknown scene" % item["id"]):
				return {}
			if not localized(loc, item.get("name_key")) or not localized(loc, item.get("description_key")):
				return {}
		var puzzles := _get_list(d["puzzles"], "puzzles", "puzzles")
		var puzzleids := unique(puzzles, "puzzles")
		if bad():
			return {}
		for p in puzzles:
			if not ck(sceneids.has(p.get("scene")), "Puzzle %s: unknown scene" % p["id"]):
				return {}
			if not ck(Util.all_str(p.get("clue_item_ids")) and Util.subset(p["clue_item_ids"], itemids), "Puzzle %s: unknown clue" % p["id"]):
				return {}
			var hint = p.get("hint_after_attempts")
			if not ck(Util.truthy(p.get("retry_unlimited")) and Util.is_num(hint) and hint >= 0, "Puzzle %s: accessibility config" % p["id"]):
				return {}
			if not ck(Util.truthy(p.get("solution")), "Puzzle %s: missing solution" % p["id"]):
				return {}

		var dialogues := _get_list(d["dialogue"], "conversations", "dialogue")
		var dialogueids := unique(dialogues, "dialogues")
		if bad():
			return {}
		for dialog in dialogues:
			var nodes := _get_list(dialog, "nodes", dialog["id"])
			var nodeids := unique(nodes, dialog["id"])
			if bad():
				return {}
			if not ck(nodeids.has(dialog.get("entry_node")), "%s: entry missing" % dialog["id"]):
				return {}
			var edges := {}
			for node in nodes:
				if not localized(loc, node.get("text_key")):
					return {}
				var edge: Array = [node["next"]] if node.has("next") else []
				edges[node["id"]] = edge
				if not ck(Util.truthy(node.get("end")) != (not edge.is_empty()), "%s: must end or go to next" % node["id"]):
					return {}
				if not ck(Util.subset(edge, nodeids), "%s: dangling link" % node["id"]):
					return {}
			var seen := {}
			var stack: Array = [dialog["entry_node"]]
			while not stack.is_empty():
				var cur = stack.pop_back()
				if not seen.has(cur):
					seen[cur] = true
					stack.append_array(edges[cur])
			if not ck(Util.same_keys(seen, nodeids), "%s: unreachable nodes" % dialog["id"]):
				return {}
			var has_end := false
			for node in nodes:
				if Util.truthy(node.get("end")):
					has_end = true
			if not ck(has_end, "%s: no endpoint" % dialog["id"]):
				return {}

		var quests := _get_list(d["quests"], "quests", "quests")
		var questids := unique(quests, "quests")
		if bad():
			return {}
		var completed_events := {}
		var allobjectives := {}
		for q in quests:
			if not ck(sceneids.has(q.get("scene")), "%s: missing scene" % q["id"]):
				return {}
			if not ck(typeof(q.get("character")) == TYPE_STRING and protagonists.has(q["character"]), "%s: unknown character" % q["id"]):
				return {}
			if not localized(loc, q.get("title_key")):
				return {}
			if not ck(eventids.has(q.get("completion_event")), "%s: completion event missing" % q["id"]):
				return {}
			if not ck(not completed_events.has(q["completion_event"]), "duplicate completion event"):
				return {}
			completed_events[q["completion_event"]] = true
			var objectives := _get_list(q, "objectives", q["id"])
			check_dag(objectives, q["id"])
			if bad():
				return {}
			for obj in objectives:
				if not ck(not allobjectives.has(obj["id"]), "Duplicate global objective: %s" % obj["id"]):
					return {}
				allobjectives[obj["id"]] = true
				if not localized(loc, obj.get("text_key")):
					return {}
				if not ck(OBJECTIVE_TYPES.has(obj.get("type")), "%s: invalid type" % obj["id"]):
					return {}
				if obj.has("grant_item"):
					if not ck(itemids.has(obj["grant_item"]), "%s: item missing" % obj["id"]):
						return {}
				if obj.has("effects"):
					effects_valid(obj["effects"], flag_defs, obj["id"])
					if bad():
						return {}
				if obj["type"] == "dialogue":
					if not ck(dialogueids.has(obj.get("dialogue_id")), "%s: dialogue missing" % obj["id"]):
						return {}
				if obj["type"] == "puzzle":
					if not ck(puzzleids.has(obj.get("puzzle_id")), "%s: puzzle missing" % obj["id"]):
						return {}
				if obj["type"] == "choice":
					var choices = obj.get("choices", [])
					if not ck(typeof(choices) == TYPE_ARRAY and choices.size() >= 2, "%s: fewer than 2 choices" % obj["id"]):
						return {}
					unique(choices, obj["id"] + " choices")
					if bad():
						return {}
					for choice in choices:
						if not localized(loc, choice.get("text_key")):
							return {}
						effects_valid(choice.get("effects", {}), flag_defs, choice["id"])
						if bad():
							return {}
			var gate = q.get("requires_events", [])
			if not ck(Util.all_str(gate), "%s: malformed requires_events" % q["id"]):
				return {}
			if not ck(not (gate as Array).has(q["completion_event"]), "%s: self gated" % q["id"]):
				return {}
		for q in quests:
			if not ck(Util.subset(q.get("requires_events", []), completed_events), "%s: unknown quest event gate" % q["id"]):
				return {}
		if not ck(Util.all_str(d["quests"].get("slice_end_requires")) and Util.subset(d["quests"]["slice_end_requires"], completed_events), "slice end events missing"):
			return {}
		for scene in scenes:
			if not localized(loc, scene.get("title_key")):
				return {}
			if not ck(typeof(scene.get("protagonist")) == TYPE_STRING and (protagonists.has(scene["protagonist"]) or scene["protagonist"] == "none"), "%s: protagonist invalid" % scene["id"]):
				return {}
			if not ck(scene.has("associated_quest") and scene.has("next_scene"), "%s: missing associated_quest/next_scene" % scene["id"]):
				return {}
			if scene["associated_quest"] != null:
				if not ck(questids.has(scene["associated_quest"]), "%s: quest invalid" % scene["id"]):
					return {}
			if scene["next_scene"] != null:
				if not ck(sceneids.has(scene["next_scene"]), "%s: next scene invalid" % scene["id"]):
					return {}
			if not ck(eventids.has(scene.get("exit_on_event")), "%s: unknown exit event" % scene["id"]):
				return {}
		var sequences := _get_list(d["cinematics"], "sequences", "cinematics")
		unique(sequences, "cinematics")
		if bad():
			return {}
		for seq in sequences:
			if not ck(eventids.has(seq.get("trigger_event")) or allobjectives.has(seq.get("trigger_objective")), "%s: invalid trigger" % seq["id"]):
				return {}
			var shots := _get_list(seq, "shots", seq["id"])
			unique(shots, seq["id"] + " shots")
			if bad():
				return {}
			for shot in shots:
				if not ck(Util.is_num(shot.get("duration_s")) and shot["duration_s"] > 0 and Util.truthy(shot.get("shot")), "%s: empty shot" % seq["id"]):
					return {}
		var assets := _get_list(d["reference_manifest"], "assets", "reference_manifest")
		if bad():
			return {}
		for asset in assets:
			if not ck(typeof(asset) == TYPE_DICTIONARY and typeof(asset.get("path")) == TYPE_STRING, "reference_manifest: malformed asset"):
				return {}
			if reference_root != "":
				if not ck(FileAccess.file_exists(reference_root.path_join(asset["path"])), "Reference file missing: %s" % asset["path"]):
					return {}
			if not ck(asset.get("license_status") == "reference_only", "Artwork rights status unreviewed: %s" % str(asset.get("id"))):
				return {}
		return {"quests": quests.size(), "objectives": allobjectives.size(), "dialogs": dialogues.size(),
			"items": items.size(), "puzzles": puzzles.size(), "scenes": scenes.size(), "locale_strings": loc.size()}

	func _deep(d: Dictionary) -> Dictionary:
		var scenes := {}
		for s in d["scenes"]["scenes"]:
			scenes[s["id"]] = s
		var quests := {}
		for q in d["quests"]["quests"]:
			quests[q["id"]] = q
		var items := {}
		for it in d["items"]["items"]:
			items[it["id"]] = it
		var puzzles := {}
		for p in d["puzzles"]["puzzles"]:
			puzzles[p["id"]] = p
		var objectives := {}
		var events := {}
		for q in quests.values():
			for o in q["objectives"]:
				objectives[o["id"]] = o
			events[q["completion_event"]] = q["id"]
		for scene in scenes.values():
			if scene["associated_quest"] != null:
				var q: Dictionary = quests[scene["associated_quest"]]
				if not ck(q["scene"] == scene["id"], "%s: quest scene mismatch" % scene["id"]):
					return {}
				if not ck(q["character"] == scene["protagonist"], "%s: quest protagonist mismatch" % scene["id"]):
					return {}
				if not ck(q["completion_event"] == scene["exit_on_event"], "%s: exit event mismatch" % scene["id"]):
					return {}
				if not ck(scene["next_scene"] != null and scenes.has(scene["next_scene"]), "%s: missing next scene" % scene["id"]):
					return {}
				if not ck(scene["id"] != scene["next_scene"], "%s: self scene loop" % scene["id"]):
					return {}
			else:
				if not ck(scene["protagonist"] == "none" and scene["next_scene"] == null, "Nonquest scene must be terminal montage"):
					return {}
		var seen: Array = []
		var cur = d["scenes"]["start_scene"]
		while cur != null:
			if not ck(not seen.has(cur), "Scene graph cycle at " + str(cur)):
				return {}
			seen.append(cur)
			cur = scenes[cur]["next_scene"]
		if not ck(Util.same_keys(Util.as_set(seen), scenes), "Unreachable scene(s)"):
			return {}
		if not ck(scenes[seen[-1]]["associated_quest"] == null, "Last scene must be montage"):
			return {}
		var ix := {}
		for k in seen.size():
			ix[seen[k]] = k
		for q in quests.values():
			for event in q.get("requires_events", []):
				if not ck(ix[quests[events[event]]["scene"]] < ix[q["scene"]], "%s: impossible event gate" % q["id"]):
					return {}
			for obj in q["objectives"]:
				if Util.truthy(obj.get("grant_item")):
					if not ck(items[obj["grant_item"]]["scene"] == q["scene"], "%s: item/quest scene mismatch" % obj["id"]):
						return {}
				if obj["type"] == "puzzle":
					var p: Dictionary = puzzles[obj["puzzle_id"]]
					if not ck(p["scene"] == q["scene"], "%s: puzzle scene mismatch" % obj["id"]):
						return {}
					var recursively := {}
					var stack: Array = (obj.get("requires", []) as Array).duplicate()
					while not stack.is_empty():
						var oid = stack.pop_back()
						if recursively.has(oid):
							continue
						recursively[oid] = true
						stack.append_array(objectives[oid].get("requires", []))
					var available_items := {}
					for oid in recursively:
						available_items[objectives[oid].get("grant_item")] = true
					if not ck(Util.subset(p["clue_item_ids"], available_items), "%s: inaccessible clue" % obj["id"]):
						return {}
		for p in puzzles.values():
			if p.get("type") == "symbol_order":
				var shown = p.get("display_symbols")
				if not ck(Util.all_str(shown) and Util.all_str(p["solution"]), "%s: symbols must be lists of strings" % p["id"]):
					return {}
				if not ck(Util.as_set(shown).size() == shown.size(), "Duplicate puzzle symbols"):
					return {}
				var a: Array = (p["solution"] as Array).duplicate()
				var b: Array = (shown as Array).duplicate()
				a.sort()
				b.sort()
				if not ck(a == b, "Puzzle display and solution differ"):
					return {}
			elif p.get("type") == "overlay_alignment":
				if not ck(typeof(p["solution"]) == TYPE_DICTIONARY and Util.same_keys(p["solution"], {"rotation_steps": 1, "offset_x": 1, "offset_y": 1}), "Overlay solution keys mismatch"):
					return {}
				for value in p["solution"].values():
					if not ck(Util.is_int(value), "Overlay solution non-integer"):
						return {}
			else:
				ck(false, "Unknown puzzle type: " + str(p.get("type")))
				return {}
		for convo in d["dialogue"]["conversations"]:
			var byid := {}
			for node in convo["nodes"]:
				byid[node["id"]] = node
			var node_id = convo["entry_node"]
			var visited := {}
			while true:
				if not ck(not visited.has(node_id), "%s: dialogue cycle" % convo["id"]):
					return {}
				visited[node_id] = true
				if Util.truthy(byid[node_id].get("end")):
					break
				node_id = byid[node_id]["next"]
			if not ck(Util.same_keys(visited, byid), "%s: unused dialogue nodes" % convo["id"]):
				return {}
		var cinematic_ids := {}
		for s in d["cinematics"]["sequences"]:
			if not ck(Util.truthy(s.get("trigger_event")) != Util.truthy(s.get("trigger_objective")), "Sequence needs exactly one trigger"):
				return {}
			cinematic_ids[s["id"]] = true
			if s.has("trigger_event"):
				if not ck(events.has(s["trigger_event"]), "Sequence event not emitted by a quest"):
					return {}
			if s.has("trigger_objective"):
				if not ck(objectives.has(s["trigger_objective"]), "Sequence objective not present"):
					return {}
		if not ck(Util.same_keys(cinematic_ids, Util.as_set(LOCKED_CINEMATICS)), "Missing locked cinematic(s)"):
			return {}
		if not ck(Util.same_keys(Util.as_set(d["quests"]["slice_end_requires"]), events), "Finale needs both quest events"):
			return {}
		return {"scenes": scenes.size(), "quests": quests.size(), "objectives": objectives.size(),
			"puzzles": puzzles.size(), "dialogues": d["dialogue"]["conversations"].size(),
			"cinematics": cinematic_ids.size()}

	## Guarantees the Python engine relies on implicitly (asserts / KeyErrors at runtime).
	func _runtime(d: Dictionary) -> void:
		var scenes := {}
		for s in d["scenes"]["scenes"]:
			scenes[s["id"]] = s
		if not ck(scenes.has(FINALE_SCENE), "runtime: finale scene %s missing" % FINALE_SCENE):
			return
		if not ck((d["flags"]["events"] as Array).has(FINALE_EVENT), "runtime: event %s missing" % FINALE_EVENT):
			return
		var fd: Dictionary = d["flags"]["flags"]
		if not ck(fd.has(FINALE_FLAG) and fd[FINALE_FLAG]["type"] == "boolean", "runtime: boolean flag %s missing" % FINALE_FLAG):
			return
		if not ck(typeof(scenes[d["scenes"]["start_scene"]].get("protagonist")) == TYPE_STRING, "runtime: start scene protagonist"):
			return
		for q in d["quests"]["quests"]:
			var scene: Dictionary = scenes[q["scene"]]
			if not ck(scene.get("exit_on_event") == q["completion_event"] and scene.get("next_scene") != null, "runtime: %s must exit its scene on %s" % [q["id"], q["completion_event"]]):
				return
			for obj in q["objectives"]:
				if obj.has("grant_item") and not ck(typeof(obj["grant_item"]) == TYPE_STRING, "runtime: %s grant_item must be an id" % obj["id"]):
					return
		for convo in d["dialogue"]["conversations"]:
			for node in convo["nodes"]:
				if not ck(typeof(node.get("speaker")) == TYPE_STRING, "runtime: %s: speaker missing" % node["id"]):
					return
		for seq in d["cinematics"]["sequences"]:
			for key in ["trigger_event", "trigger_objective"]:
				if seq.has(key) and not ck(typeof(seq[key]) == TYPE_STRING, "runtime: %s: %s must be an id" % [seq["id"], key]):
					return


# =====================================================================================================
# Inner class: DB — parsed + validated canonical data with lookup tables (shared, read-only)
# =====================================================================================================

class DB extends RefCounted:
	static var _shared: DB = null

	var ok := false
	var error := ""
	var report: Dictionary = {}
	var flags_def: Dictionary = {}
	var flag_order: Array = []
	var protagonists: Array = []
	var events: Array = []
	var quests: Array = []
	var quests_def: Dictionary = {}
	var quest_by_id: Dictionary = {}
	var scenes: Dictionary = {}
	var start_scene := ""
	var items: Dictionary = {}
	var puzzles: Dictionary = {}
	var dialogues: Dictionary = {}
	var dialogue_nodes: Dictionary = {}   # dialogue id -> {node id -> node}
	var sequences: Array = []
	var sequence_ids: Dictionary = {}
	var objectives: Dictionary = {}       # id -> [quest, objective]
	var objective_order: Array = []

	static func shared() -> DB:
		if _shared == null:
			_shared = from_dir(DATA_DIR)
			if not _shared.ok:
				push_error("Story: canonical data invalid — " + _shared.error)
		return _shared

	static func clear_shared() -> void:
		_shared = null

	static func read_files(dir: String) -> Dictionary:
		var data := {}
		for stem in DATA_FILES:
			var path := dir.path_join(stem + ".json")
			if not FileAccess.file_exists(path):
				return {"ok": false, "error": "Missing data file " + path, "data": {}}
			var parsed := Json.parse(FileAccess.get_file_as_string(path))
			if not parsed["ok"]:
				return {"ok": false, "error": "%s: %s" % [path, parsed["error"]], "data": {}}
			data[stem] = parsed["value"]
		return {"ok": true, "error": "", "data": data}

	static func from_dir(dir: String) -> DB:
		var r := read_files(dir)
		if not r["ok"]:
			var db := DB.new()
			db.error = r["error"]
			return db
		return from_data(r["data"])

	static func from_data(data: Dictionary) -> DB:
		var db := DB.new()
		var v := Validator.deep_validate(data, "")
		if not v["ok"]:
			db.error = v["error"]
			return db
		db.report = v["report"]
		db._index(data)
		db.ok = true
		return db

	func _index(d: Dictionary) -> void:
		flags_def = d["flags"]["flags"]
		flag_order = flags_def.keys()
		protagonists = d["flags"]["protagonists"]
		events = d["flags"]["events"]
		quests_def = d["quests"]
		quests = d["quests"]["quests"]
		for q in quests:
			quest_by_id[q["id"]] = q
			for o in q["objectives"]:
				objectives[o["id"]] = [q, o]
				objective_order.append(o["id"])
		for s in d["scenes"]["scenes"]:
			scenes[s["id"]] = s
		start_scene = d["scenes"]["start_scene"]
		for x in d["items"]["items"]:
			items[x["id"]] = x
		for x in d["puzzles"]["puzzles"]:
			puzzles[x["id"]] = x
		for x in d["dialogue"]["conversations"]:
			dialogues[x["id"]] = x
			var by_id := {}
			for node in x["nodes"]:
				by_id[node["id"]] = node
			dialogue_nodes[x["id"]] = by_id
		sequences = d["cinematics"]["sequences"]
		for s in sequences:
			sequence_ids[s["id"]] = true


# =====================================================================================================
# Inner class: Core — the state machine (1:1 port of StoryEngine); no signals, no Node
# =====================================================================================================

class Core extends RefCounted:
	var db: DB
	var state: Dictionary = {}

	func _init(p_db: DB) -> void:
		db = p_db
		new_game()

	func new_game() -> Dictionary:
		var f := {}
		for name in db.flag_order:
			f[name] = db.flags_def[name]["default"]
		state = {
			"format": FORMAT,
			"save_version": VERSION,
			"flags": f,
			"completed_objectives": [], "completed_events": [], "inventory": [],
			"choice_history": {}, "current_scene": db.start_scene,
			"active_character": db.scenes[db.start_scene]["protagonist"],
			"dialogue_progress": {}, "puzzle_attempts": {},
			"cinematics_seen": [], "finale_viewed": false,
		}
		return snapshot()

	func snapshot() -> Dictionary:
		return state.duplicate(true)

	func available() -> Array:
		var done := Util.as_set(state["completed_objectives"])
		var ev := Util.as_set(state["completed_events"])
		var result: Array = []
		for q in db.quests:
			if q["scene"] != state["current_scene"] or not Util.subset(q.get("requires_events", []), ev):
				continue
			for obj in q["objectives"]:
				if not done.has(obj["id"]) and Util.subset(obj.get("requires", []), done):
					result.append(obj["id"])
		return result

	func require(objective_id, kind: String) -> Dictionary:
		if not Util.is_str(objective_id) or not db.objectives.has(str(objective_id)):
			return Util.err("Unknown objective: " + str(objective_id), "sys.err.unknown_objective")
		var id := str(objective_id)
		var pair: Array = db.objectives[id]
		var obj: Dictionary = pair[1]
		if obj["type"] != kind:
			return Util.err("%s: expected %s, got %s" % [id, kind, obj["type"]], "sys.err.wrong_type")
		if not available().has(id):
			return Util.err("%s: locked, wrong scene, or already completed" % id, "sys.err.locked")
		return {"ok": true, "error": "", "error_key": "", "id": id, "quest": pair[0], "obj": obj}

	func apply_effects(effects: Dictionary) -> void:
		var f: Dictionary = state["flags"]
		for name in effects:
			var meta: Dictionary = db.flags_def[name]
			var spec: Dictionary = effects[name]
			if meta["type"] == "boolean":
				f[name] = spec["set"]
			else:
				var value: int = f[name] + spec["delta"]
				f[name] = maxi(meta["min"], mini(meta["max"], value))

	## The single place where an objective completes (effects, item, choice, event, scene change).
	func commit(objective_id: String, effects = null, choice_id = null) -> void:
		var pair: Array = db.objectives[objective_id]
		var q: Dictionary = pair[0]
		var obj: Dictionary = pair[1]
		apply_effects(effects if effects != null else obj.get("effects", {}))
		state["completed_objectives"].append(objective_id)
		var item = obj.get("grant_item")
		if Util.truthy(item) and not (state["inventory"] as Array).has(item):
			state["inventory"].append(item)
		if choice_id != null:
			state["choice_history"][objective_id] = choice_id
		var done := Util.as_set(state["completed_objectives"])
		for o in q["objectives"]:
			if not done.has(o["id"]):
				return
		var event: String = q["completion_event"]
		if not (state["completed_events"] as Array).has(event):
			state["completed_events"].append(event)
			var scene: Dictionary = db.scenes[q["scene"]]
			state["current_scene"] = scene["next_scene"]
			state["active_character"] = db.scenes[scene["next_scene"]]["protagonist"]

	func inspect(objective_id) -> Dictionary:
		var r := require(objective_id, "inspect")
		if not r["ok"]:
			return r
		commit(r["id"])
		return {"ok": true, "error": "", "error_key": ""}

	func start_dialogue(objective_id) -> Dictionary:
		var r := require(objective_id, "dialogue")
		if not r["ok"]:
			return r
		if not (state["dialogue_progress"] as Dictionary).has(r["id"]):
			state["dialogue_progress"][r["id"]] = db.dialogues[r["obj"]["dialogue_id"]]["entry_node"]
		return current_dialogue_line(r["id"])

	func current_dialogue_line(objective_id) -> Dictionary:
		if not Util.is_str(objective_id) or not (state["dialogue_progress"] as Dictionary).has(str(objective_id)):
			return Util.err("Dialogue not started", "sys.err.dialogue_not_started")
		var r := require(objective_id, "dialogue")
		if not r["ok"]:
			return r
		var node_id = state["dialogue_progress"][r["id"]]
		var node: Dictionary = db.dialogue_nodes[r["obj"]["dialogue_id"]][node_id]
		return {"ok": true, "error": "", "error_key": "", "line": node.duplicate(true)}

	func advance_dialogue(objective_id) -> Dictionary:
		var r := current_dialogue_line(objective_id)
		if not r["ok"]:
			return r
		var id := str(objective_id)
		var line: Dictionary = r["line"]
		if Util.truthy(line.get("end", false)):
			state["dialogue_progress"].erase(id)
			commit(id)
			return {"ok": true, "error": "", "error_key": "", "finished": true}
		state["dialogue_progress"][id] = line["next"]
		var nxt := current_dialogue_line(id)
		nxt["finished"] = false
		return nxt

	func puzzle_hint_available(objective_id) -> Dictionary:
		var r := require(objective_id, "puzzle")
		if not r["ok"]:
			return r
		var puzzle: Dictionary = db.puzzles[r["obj"]["puzzle_id"]]
		var attempts: int = state["puzzle_attempts"].get(r["id"], 0)
		return {"ok": true, "error": "", "error_key": "", "available": attempts >= puzzle["hint_after_attempts"]}

	## Python: isinstance(answer, list) and all(isinstance(x, str)). PackedStringArray is a GDScript list of
	## strings and is accepted as well. Returns null when the payload is not a list of strings.
	static func _string_list(answer) -> Variant:
		var t := typeof(answer)
		if t == TYPE_PACKED_STRING_ARRAY:
			return Array(answer)
		if t != TYPE_ARRAY:
			return null
		var out: Array = []
		for x in answer:
			if not Util.is_str(x):
				return null
			out.append(str(x))
		return out

	func solve_puzzle(objective_id, answer) -> Dictionary:
		var r := require(objective_id, "puzzle")
		if not r["ok"]:
			return r
		var id: String = r["id"]
		var puzzle: Dictionary = db.puzzles[r["obj"]["puzzle_id"]]
		if not Util.subset(puzzle["clue_item_ids"], Util.as_set(state["inventory"])):
			return Util.err("Missing clues for puzzle", "sys.err.missing_clues")
		var correct := false
		if puzzle["type"] == "symbol_order":
			var list = _string_list(answer)
			if list == null:
				return Util.err("Symbol puzzle expects a list of symbols", "sys.err.answer_format")
			correct = list == puzzle["solution"]
		elif puzzle["type"] == "overlay_alignment":
			var solution: Dictionary = puzzle["solution"]
			if typeof(answer) != TYPE_DICTIONARY:
				return Util.err("Overlay expects rotation_steps, offset_x, offset_y", "sys.err.answer_format")
			var keys := {}
			for k in answer:
				if not Util.is_str(k):
					return Util.err("Overlay expects rotation_steps, offset_x, offset_y", "sys.err.answer_format")
				keys[str(k)] = true
			if not Util.same_keys(keys, solution):
				return Util.err("Overlay expects rotation_steps, offset_x, offset_y", "sys.err.answer_format")
			for value in answer.values():
				if typeof(value) != TYPE_INT:
					return Util.err("Overlay coordinates must be integers", "sys.err.answer_format")
			correct = true
			for k in solution:
				if answer[k] != solution[k]:
					correct = false
		else:
			return Util.err("Unsupported puzzle type", "sys.err.unsupported_puzzle")
		if correct:
			commit(id)
			return {"ok": true, "error": "", "error_key": "", "solved": true,
				"attempts": int(state["puzzle_attempts"].get(id, 0))}
		state["puzzle_attempts"][id] = int(state["puzzle_attempts"].get(id, 0)) + 1
		return {"ok": true, "error": "", "error_key": "", "solved": false, "attempts": state["puzzle_attempts"][id]}

	func choose(objective_id, choice_id) -> Dictionary:
		var r := require(objective_id, "choice")
		if not r["ok"]:
			return r
		var matches: Array = []
		if Util.is_str(choice_id):
			for c in r["obj"]["choices"]:
				if c["id"] == str(choice_id):
					matches.append(c)
		if matches.size() != 1:
			return Util.err("Invalid choice ID", "sys.err.invalid_choice")
		commit(r["id"], matches[0].get("effects", {}), str(choice_id))
		return {"ok": true, "error": "", "error_key": "", "choice": str(choice_id)}

	func pending_cinematics() -> Array:
		var seen := Util.as_set(state["cinematics_seen"])
		var obj := Util.as_set(state["completed_objectives"])
		var ev := Util.as_set(state["completed_events"])
		var out: Array = []
		for s in db.sequences:
			if seen.has(s["id"]):
				continue
			if obj.has(s.get("trigger_objective")) or ev.has(s.get("trigger_event")):
				out.append(s["id"])
		return out

	func consume_cinematic(cinematic_id, _skipped: bool = false) -> Dictionary:
		if not Util.is_str(cinematic_id) or not pending_cinematics().has(str(cinematic_id)):
			return Util.err("Cinematic not unlocked or already consumed", "sys.err.cinematic_locked")
		state["cinematics_seen"].append(str(cinematic_id))
		return {"ok": true, "error": "", "error_key": ""}

	func finale(_skipped: bool = false) -> Dictionary:
		var ev := Util.as_set(state["completed_events"])
		if state["current_scene"] != FINALE_SCENE or not Util.subset(db.quests_def["slice_end_requires"], ev):
			return Util.err("Finale locked", "sys.err.finale_locked")
		if not ev.has(FINALE_EVENT):
			state["completed_events"].append(FINALE_EVENT)
			state["flags"][FINALE_FLAG] = true
		state["finale_viewed"] = true
		return {"ok": true, "error": "", "error_key": ""}

	static func _bad(message: String) -> Dictionary:
		return Util.err(message, "sys.save.err.inconsistent")

	## Port of StoryEngine.load_json, executed on a FRESH core (the "replay"). On success this core holds
	## the loaded state; the caller adopts it. Never fabricates proof of future objectives.
	func load_from_json(raw) -> Dictionary:
		if typeof(raw) != TYPE_STRING:
			return Util.err("Expected save text", "sys.save.err.malformed")
		var text: String = raw
		if text.to_utf8_buffer().size() > MAX_SAVE_BYTES:
			return Util.err("Save too large", "sys.save.err.too_large")
		var parsed := Json.parse(text)
		if not parsed["ok"]:
			return Util.err("Malformed JSON", "sys.save.err.malformed")
		var source = parsed["value"]
		if typeof(source) != TYPE_DICTIONARY:
			return Util.err("Expected JSON object", "sys.save.err.malformed")
		var ver = source.get("save_version")
		if typeof(ver) != TYPE_INT or not (ver == LEGACY_VERSION or ver == VERSION):
			return Util.err("Unsupported save version", "sys.save.err.version")
		if ver == VERSION and not Util.py_eq(source.get("format"), FORMAT):
			return Util.err("Unknown save format", "sys.save.err.format")
		# Replay objective history to establish a valid state/scene/event/flag basis.
		var actions = source.get("completed_objectives")
		var choices = source.get("choice_history")
		if not Util.all_str(actions):
			return _bad("Malformed completed objectives")
		if Util.as_set(actions).size() != actions.size():
			return _bad("Duplicate objectives")
		if typeof(choices) != TYPE_DICTIONARY:
			return _bad("Malformed choice history")
		for objective_id in actions:
			if not db.objectives.has(objective_id):
				return _bad("Unknown objective")
			var obj: Dictionary = db.objectives[objective_id][1]
			if not available().has(objective_id):
				return _bad("Invalid quest order or scene transition")
			var r := {}
			match obj["type"]:
				"choice":
					var selected = choices.get(objective_id)
					var valid := false
					if typeof(selected) == TYPE_STRING:
						for c in obj["choices"]:
							if c["id"] == selected:
								valid = true
					if not valid:
						return _bad("Choice missing/invalid")
					r = choose(objective_id, selected)
				"inspect":
					r = inspect(objective_id)
				"dialogue":
					r = start_dialogue(objective_id)
					var guard := 0
					while r["ok"] and (state["dialogue_progress"] as Dictionary).has(objective_id):
						guard += 1
						if guard > 100000:
							return _bad("Dialogue does not terminate")
						r = advance_dialogue(objective_id)
				"puzzle":
					r = solve_puzzle(objective_id, Util.deep_copy(db.puzzles[obj["puzzle_id"]]["solution"]))
			if not r.get("ok", false):
				return _bad(str(r.get("error", "Replay failed")))
		var choice_objectives := {}
		for o in actions:
			if db.objectives[o][1]["type"] == "choice":
				choice_objectives[o] = true
		if not Util.same_keys(choices, choice_objectives):
			return _bad("Choice history mismatch")
		# Python: `'slice_completed' in source.get('completed_events', [])` (list/str/dict membership).
		var claims_finale := false
		if (source as Dictionary).has("completed_events"):
			var ce = source["completed_events"]
			match typeof(ce):
				TYPE_ARRAY:
					claims_finale = ce.has(FINALE_EVENT)
				TYPE_STRING:
					claims_finale = (ce as String).contains(FINALE_EVENT)
				TYPE_DICTIONARY:
					claims_finale = ce.has(FINALE_EVENT)
				_:
					return _bad("Malformed completed events")
		if claims_finale:
			var fr := finale(false)
			if not fr["ok"]:
				return _bad(fr["error"])
		# Compare every authoritative component, refusing contradictory saves.
		var defaults := {}
		for name in db.flag_order:
			defaults[name] = db.flags_def[name]["default"]
		for key in ["flags", "completed_objectives", "completed_events", "inventory", "choice_history",
				"current_scene", "active_character"]:
			var a = source.get(key)
			var b = state[key]
			# Legacy v2 could omit optional unused flags but must not contradict progress.
			if ver == LEGACY_VERSION and key == "flags" and typeof(a) == TYPE_DICTIONARY:
				var merged := defaults.duplicate()
				for k in a:
					merged[k] = a[k]
				a = merged
			if not Util.py_eq(a, b):
				if (key == "completed_events" or key == "inventory") and typeof(a) == TYPE_ARRAY \
						and Util.same_strings_any_order(a, b):
					continue
				return _bad("Inconsistent save field: " + key)
		var warnings: Array = []
		if ver == VERSION:
			var p = source.get("dialogue_progress", {})
			var attempts = source.get("puzzle_attempts", {})
			var seen = source.get("cinematics_seen", [])
			var viewed = source.get("finale_viewed", false)
			if typeof(p) != TYPE_DICTIONARY or typeof(attempts) != TYPE_DICTIONARY or typeof(seen) != TYPE_ARRAY \
					or typeof(viewed) != TYPE_BOOL:
				return _bad("Malformed presentation state")
			var avail := available()
			for objective in p:
				if not avail.has(objective) or db.objectives[objective][1]["type"] != "dialogue":
					return _bad("Invalid dialogue cursor")
				var node = p[objective]
				var nodes: Dictionary = db.dialogue_nodes[db.objectives[objective][1]["dialogue_id"]]
				if typeof(node) != TYPE_STRING or not nodes.has(node):
					return _bad("Invalid dialogue node")
			for objective in attempts:
				if not db.objectives.has(objective) or db.objectives[objective][1]["type"] != "puzzle":
					return _bad("Invalid puzzle counter")
				var count = attempts[objective]
				if typeof(count) != TYPE_INT or count < 0 or count > MAX_ATTEMPTS:
					return _bad("Invalid attempt count")
			if not Util.all_str(seen) or Util.as_set(seen).size() != seen.size() or not Util.subset(seen, db.sequence_ids):
				return _bad("Invalid cinematic IDs")
			var ev_now := Util.as_set(state["completed_events"])
			var obj_now := Util.as_set(state["completed_objectives"])
			for seq in db.sequences:
				if (seen as Array).has(seq["id"]) and not (ev_now.has(seq.get("trigger_event")) or obj_now.has(seq.get("trigger_objective"))):
					return _bad("Cinematic was not triggered")
			if viewed and not ev_now.has(FINALE_EVENT):
				return _bad("Invalid finale viewed")
			state["dialogue_progress"] = (p as Dictionary).duplicate(true)
			state["puzzle_attempts"] = (attempts as Dictionary).duplicate(true)
			state["cinematics_seen"] = (seen as Array).duplicate(true)
			state["finale_viewed"] = viewed
		else:
			warnings.append("Migrated save_version %d to %d" % [LEGACY_VERSION, VERSION])
		for k in source:
			if not SAVE_KEYS.has(k):
				warnings.append("Unknown save field ignored: " + str(k))
		return {"ok": true, "error": "", "error_key": "", "warnings": warnings}
