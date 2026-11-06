extends Node
## Saves — save slots, autosave and quicksave with atomic writes (autoload "Saves").
##
## Slots: "1", "2", "3" (manual), "auto", "quick". File: <base_dir>/<slot>.json (default user://saves)
##   {"meta":  {version, timestamp, chapter_key, character, scene, playtime_s, label},
##    "story": <the object written by Story.save_json() — format/save_version 3>,
##    "extra": <presentation data from Game.save_extra(): player position, playtime ...>}
## Writing: <slot>.json.tmp is written and verified, the previous <slot>.json is copied to
## <slot>.json.bak, then the .tmp replaces the .json.
## Loading: the file is parsed and the story payload is validated with Story.validate_save_json()
## (full replay validation) BEFORE Story.load_json() touches the live state; any failure leaves the
## live game unchanged. Every call returns {ok, error, error_key, ...}; error_key → de_system.json.
## Saving refuses while Game.save_block_key() names a reason (§12.10: inside a memory, "sys.save.err.memory").

signal saved(slot: String)
signal loaded(slot: String)
signal save_failed(slot: String, error: String)
signal load_failed(slot: String, error: String)
signal deleted(slot: String)

const ENGINE := preload("res://scripts/story/story_engine.gd")
const CONTAINER_VERSION := 1
const DEFAULT_DIR := "user://saves"
const MANUAL_SLOTS := ["1", "2", "3"]
const SLOTS := ["1", "2", "3", "auto", "quick"]
const MAX_FILE_BYTES := 512 * 1024
const MAX_EXTRA_BYTES := 32 * 1024
const MAX_LABEL_CHARS := 120
## The container is re-serialised before validation; real saves nest 4 levels deep.
const MAX_NESTING := 32

## Directory of the slot files (tests point this at a temporary user:// folder).
var base_dir := DEFAULT_DIR
## Story engine used for (de)serialisation. Defaults to the /root/Story autoload.
var story: Node = null
## Callable returning a Dictionary of presentation data stored next to the story payload.
## Defaults to Game.save_extra() when the Game autoload provides it.
var extra_provider: Callable = Callable()
## Callable returning a Loc key (String) when saving is impossible right now, "" when it is allowed.
## Defaults to Game.save_block_key() (§12.10: no save of any kind inside a memory).
var block_provider: Callable = Callable()
## Fallback playtime counter (used when the extra data has no "playtime"); runs while `counting`.
var counting := false
var playtime_s := 0.0
var last_loaded_slot := ""
var last_loaded_meta: Dictionary = {}
var last_loaded_extra: Dictionary = {}
var last_error := ""
var last_error_key := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	var st := _story()
	if st and st.has_signal("state_replaced") and not st.state_replaced.is_connected(_on_story_replaced):
		st.state_replaced.connect(_on_story_replaced)


func _process(delta: float) -> void:
	if counting:
		playtime_s += delta


func _on_story_replaced(reason: String) -> void:
	if reason == "new_game":
		playtime_s = 0.0
		last_loaded_extra = {}
		last_loaded_meta = {}
		last_loaded_slot = ""
	counting = true


# =====================================================================================================
# Public API
# =====================================================================================================

## Normalised slot id ("1".."3", "auto", "quick") or "" if unknown. Accepts ints 1..3 as well.
func normalize_slot(slot) -> String:
	var s := str(slot).strip_edges().to_lower()
	return s if SLOTS.has(s) else ""


func slot_path(slot) -> String:
	var s := normalize_slot(slot)
	return base_dir.path_join(s + ".json") if s != "" else ""


## Loc key for a slot's display name (sys.save.slot.1 … sys.save.slot.quick).
func slot_label_key(slot) -> String:
	var s := normalize_slot(slot)
	return "sys.save.slot." + s if s != "" else ""


func save(slot, label: String = "") -> Dictionary:
	var s := normalize_slot(slot)
	if s == "":
		return _save_fail(str(slot), "Unknown save slot: " + str(slot), "sys.save.err.unknown_slot")
	var blocked := save_block_key()
	if blocked != "":
		return _save_fail(s, "Saving is not possible right now (%s)" % blocked, blocked)
	var st := _story()
	if st == null or not st.has_method("save_json"):
		return _save_fail(s, "Story engine unavailable", "sys.save.err.no_story")
	var raw: String = st.save_json()
	var check: Dictionary = st.validate_save_json(raw)
	if not check.get("ok", false):
		return _save_fail(s, "Live story state failed validation: " + str(check.get("error", "")), "sys.save.err.state")
	var parsed: Dictionary = ENGINE.json_parse(raw)
	var extra := _collect_extra()
	var meta := {
		"version": CONTAINER_VERSION,
		"timestamp": snappedf(Time.get_unix_time_from_system(), 0.001),
		"chapter_key": str(st.chapter_key()) if st.has_method("chapter_key") else "",
		"character": str(st.get("active_character")),
		"scene": str(st.get("current_scene")),
		"playtime_s": _meta_playtime(extra),
		"label": label.substr(0, MAX_LABEL_CHARS),
	}
	var text := ENGINE.json_dumps({"meta": meta, "story": parsed["value"], "extra": extra}, 1)
	var w := _write_atomic(base_dir.path_join(s + ".json"), text)
	if not w["ok"]:
		return _save_fail(s, w["error"], "sys.save.err.write")
	last_error = ""
	last_error_key = ""
	saved.emit(s)
	return {"ok": true, "error": "", "error_key": "", "slot": s, "meta": meta}


## Validates the slot completely, then replaces the live story state. On failure nothing changes;
## the result tells whether a valid .bak exists (load_backup()).
func load(slot) -> Dictionary:
	var s := normalize_slot(slot)
	if s == "":
		return _load_fail(str(slot), "Unknown save slot: " + str(slot), "sys.save.err.unknown_slot")
	return _load_path(s, base_dir.path_join(s + ".json"))


## Loads the backup copy (<slot>.json.bak) written by the previous save.
func load_backup(slot) -> Dictionary:
	var s := normalize_slot(slot)
	if s == "":
		return _load_fail(str(slot), "Unknown save slot: " + str(slot), "sys.save.err.unknown_slot")
	return _load_path(s, base_dir.path_join(s + ".json.bak"))


func autosave(reason: String = "") -> Dictionary:
	return save("auto", reason)


func quicksave() -> Dictionary:
	return save("quick", "quick")


func quickload() -> Dictionary:
	return self.load("quick")


## One entry per slot: {slot, manual, exists, valid, backup, error, error_key, version, timestamp,
## chapter_key, character, scene, playtime_s, label}. "valid" means the file passes the same full
## validation as load() (without touching the live state).
func list_slots() -> Array:
	var out: Array = []
	for s in SLOTS:
		var path := base_dir.path_join(s + ".json")
		var info := {"slot": s, "manual": MANUAL_SLOTS.has(s), "exists": FileAccess.file_exists(path), "valid": false,
			"backup": FileAccess.file_exists(path + ".bak"), "error": "", "error_key": "", "version": 0,
			"timestamp": 0.0, "chapter_key": "", "character": "", "scene": "", "playtime_s": 0.0, "label": ""}
		if info["exists"]:
			var r := _inspect(path)
			info["valid"] = r["ok"]
			info["error"] = r["error"]
			info["error_key"] = r["error_key"]
			var meta: Dictionary = r.get("meta", {})
			for k in ["version", "timestamp", "chapter_key", "character", "scene", "playtime_s", "label"]:
				if meta.has(k):
					info[k] = meta[k]
		out.append(info)
	return out


## Slot info of one slot (same shape as list_slots()).
func slot_info(slot) -> Dictionary:
	var s := normalize_slot(slot)
	for info in list_slots():
		if info["slot"] == s:
			return info
	return {}


func has_any() -> bool:
	for info in list_slots():
		if info["exists"] and info["valid"]:
			return true
	return false


## Newest valid slot by timestamp ("" if none) — for "Fortsetzen".
func latest() -> String:
	var best := ""
	var best_t := -1.0
	for info in list_slots():
		if info["exists"] and info["valid"] and float(info["timestamp"]) > best_t:
			best_t = float(info["timestamp"])
			best = info["slot"]
	return best


## Removes the slot file together with its .bak/.tmp companions.
func delete(slot) -> Dictionary:
	var s := normalize_slot(slot)
	if s == "":
		return {"ok": false, "error": "Unknown save slot: " + str(slot), "error_key": "sys.save.err.unknown_slot"}
	var path := base_dir.path_join(s + ".json")
	var existed := FileAccess.file_exists(path)
	for p in [path, path + ".bak", path + ".tmp"]:
		if FileAccess.file_exists(p):
			var e := DirAccess.remove_absolute(p)
			if e != OK:
				return {"ok": false, "error": "Cannot delete %s (%s)" % [p, error_string(e)], "error_key": "sys.save.err.delete"}
	deleted.emit(s)
	return {"ok": true, "error": "", "error_key": "", "slot": s, "existed": existed}


# =====================================================================================================
# Internals
# =====================================================================================================

func _story() -> Node:
	if story == null or not is_instance_valid(story):
		story = get_node_or_null("/root/Story") if is_inside_tree() else null
	return story


## Loc key of the reason why saving is blocked right now ("" = allowed): block_provider, else Game.save_block_key().
func save_block_key() -> String:
	if not block_provider.is_valid() and is_inside_tree():
		var game := get_node_or_null("/root/Game")
		if game and game.has_method("save_block_key"):
			block_provider = Callable(game, "save_block_key")
	if not block_provider.is_valid():
		return ""
	var k = block_provider.call()
	return str(k) if k is String or k is StringName else ""


func _collect_extra() -> Dictionary:
	if not extra_provider.is_valid() and is_inside_tree():
		var game := get_node_or_null("/root/Game")
		if game and game.has_method("save_extra"):
			extra_provider = Callable(game, "save_extra")
	if not extra_provider.is_valid():
		return {}
	var e = extra_provider.call()
	if typeof(e) != TYPE_DICTIONARY:
		return {}
	var clean = _json_safe(e, 0)
	if typeof(clean) != TYPE_DICTIONARY:
		return {}
	if ENGINE.json_dumps(clean, -1).to_utf8_buffer().size() > MAX_EXTRA_BYTES:
		push_warning("Saves: extra data larger than %d bytes was not stored" % MAX_EXTRA_BYTES)
		return {}
	return clean


## Converts presentation data into JSON-safe values (vectors → arrays, objects dropped).
static func _json_safe(v, depth: int) -> Variant:
	if depth > 8:
		return null
	match typeof(v):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return v
		TYPE_FLOAT:
			return v if is_finite(v) else null
		TYPE_STRING_NAME, TYPE_NODE_PATH:
			return str(v)
		TYPE_VECTOR2, TYPE_VECTOR2I:
			return [v.x, v.y]
		TYPE_VECTOR3, TYPE_VECTOR3I:
			return [v.x, v.y, v.z]
		TYPE_COLOR:
			return [v.r, v.g, v.b, v.a]
		TYPE_ARRAY, TYPE_PACKED_STRING_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_INT64_ARRAY, \
				TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_FLOAT64_ARRAY:
			var out: Array = []
			for x in Array(v):
				out.append(_json_safe(x, depth + 1))
			return out
		TYPE_DICTIONARY:
			var d := {}
			for k in v:
				d[str(k)] = _json_safe(v[k], depth + 1)
			return d
	return null


func _meta_playtime(extra: Dictionary) -> float:
	var p = extra.get("playtime")
	if (typeof(p) == TYPE_FLOAT or typeof(p) == TYPE_INT) and p >= 0:
		return snappedf(float(p), 0.1)
	return snappedf(playtime_s, 0.1)


func _save_fail(slot: String, message: String, key: String) -> Dictionary:
	last_error = message
	last_error_key = key
	save_failed.emit(slot, message)
	return {"ok": false, "error": message, "error_key": key, "slot": slot}


func _load_fail(slot: String, message: String, key: String, backup_valid := false) -> Dictionary:
	last_error = message
	last_error_key = key
	load_failed.emit(slot, message)
	return {"ok": false, "error": message, "error_key": key, "slot": slot, "backup_valid": backup_valid}


func _load_path(s: String, path: String) -> Dictionary:
	var st := _story()
	if st == null or not st.has_method("load_json"):
		return _load_fail(s, "Story engine unavailable", "sys.save.err.no_story")
	var r := _inspect(path)
	if not r["ok"]:
		var backup_ok := false
		if not path.ends_with(".bak") and FileAccess.file_exists(path + ".bak"):
			backup_ok = _inspect(path + ".bak")["ok"]
		return _load_fail(s, r["error"], r["error_key"], backup_ok)
	var res: Dictionary = st.load_json(r["story_raw"])
	if not res.get("ok", false):
		return _load_fail(s, str(res.get("error", "")), str(res.get("error_key", "sys.save.err.inconsistent")))
	last_loaded_slot = s
	last_loaded_meta = r["meta"]
	last_loaded_extra = r["extra"]
	playtime_s = float(r["meta"]["playtime_s"])
	counting = true
	last_error = ""
	last_error_key = ""
	loaded.emit(s)
	return {"ok": true, "error": "", "error_key": "", "slot": s, "meta": r["meta"],
		"warnings": res.get("warnings", []) + r["warnings"]}


## Reads and fully validates a save file without touching any live state.
## {ok, error, error_key, meta, story_raw, extra, warnings}
func _inspect(path: String) -> Dictionary:
	var c := read_container(path)
	if not c["ok"]:
		return c
	var st := _story()
	if st == null or not st.has_method("validate_save_json"):
		return _bad("Story engine unavailable", "sys.save.err.no_story", c)
	var dry: Dictionary = st.validate_save_json(c["story_raw"])
	if not dry.get("ok", false):
		return _bad(str(dry.get("error", "")), str(dry.get("error_key", "sys.save.err.inconsistent")), c)
	var state: Dictionary = dry["state"]
	if c["meta"]["scene"] != state["current_scene"] or c["meta"]["character"] != state["active_character"]:
		return _bad("Save metadata does not match the story state", "sys.save.err.meta", c)
	return c


static func _bad(message: String, key: String, c: Dictionary) -> Dictionary:
	var r := c.duplicate()
	r["ok"] = false
	r["error"] = message
	r["error_key"] = key
	return r


## Parses the container (size, UTF-8, JSON, meta schema). Does not validate the story payload.
static func _container_fail(message: String, key: String) -> Dictionary:
	return {"ok": false, "error": message, "error_key": key, "meta": {}, "story_raw": "", "extra": {}, "warnings": []}


static func _non_negative_number(x) -> bool:
	return (typeof(x) == TYPE_INT or typeof(x) == TYPE_FLOAT) and is_finite(float(x)) and x >= 0


static func read_container(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return _container_fail("Save slot is empty", "sys.save.err.empty")
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return _container_fail("Cannot open save file (%s)" % error_string(FileAccess.get_open_error()), "sys.save.err.read")
	var size := f.get_length()
	if size > MAX_FILE_BYTES:
		f.close()
		return _container_fail("Save file too large", "sys.save.err.too_large")
	var bytes := f.get_buffer(size)
	f.close()
	if not _valid_utf8(bytes):
		return _container_fail("Save file is not valid UTF-8", "sys.save.err.malformed")
	# A UTF-8 BOM (added by some text editors) is tolerated on the container; the story payload inside is
	# re-serialised and validated strictly by Story.validate_save_json().
	if bytes.size() >= 3 and bytes[0] == 0xEF and bytes[1] == 0xBB and bytes[2] == 0xBF:
		bytes = bytes.slice(3)
	var parsed: Dictionary = ENGINE.json_parse(bytes.get_string_from_utf8())
	if not parsed["ok"]:
		return _container_fail("Save file is not valid JSON", "sys.save.err.malformed")
	var doc = parsed["value"]
	if ENGINE.json_depth(doc) > MAX_NESTING:
		return _container_fail("Save file nested too deeply", "sys.save.err.malformed")
	if typeof(doc) != TYPE_DICTIONARY or typeof(doc.get("meta")) != TYPE_DICTIONARY or typeof(doc.get("story")) != TYPE_DICTIONARY:
		return _container_fail("Save file lacks meta/story", "sys.save.err.malformed")
	var meta: Dictionary = doc["meta"]
	if typeof(meta.get("version")) != TYPE_INT or meta["version"] != CONTAINER_VERSION:
		return _container_fail("Unsupported save container version", "sys.save.err.version")
	for k in ["chapter_key", "character", "scene", "label"]:
		if typeof(meta.get(k)) != TYPE_STRING:
			return _container_fail("Malformed save metadata: " + k, "sys.save.err.meta")
	if not _non_negative_number(meta.get("timestamp")) or not _non_negative_number(meta.get("playtime_s")):
		return _container_fail("Malformed save metadata: timestamp/playtime_s", "sys.save.err.meta")
	var warnings: Array = []
	var extra = doc.get("extra", {})
	if typeof(extra) != TYPE_DICTIONARY:
		warnings.append("Ignored malformed extra data")
		extra = {}
	for k in doc:
		if not ["meta", "story", "extra"].has(k):
			warnings.append("Unknown container field ignored: " + str(k))
	# Round 8: a save taken at the end of an older, shorter chain (e.g. the montage after c3b_completed) continues
	# in the scene that now follows its last completed event instead of failing the replay validation.
	var story_doc: Dictionary = rebase_story(doc["story"])
	if str(story_doc.get("current_scene")) != str(doc["story"].get("current_scene")):
		warnings.append("Save re-based to the extended story chain: " + str(story_doc.get("current_scene")))
	return {"ok": true, "error": "", "error_key": "", "meta": meta,
		"story_raw": ENGINE.json_dumps(story_doc, 2), "extra": extra, "warnings": warnings}


## Re-bases a Story state recorded before the scene chain grew (round 8: c3b_completed used to lead to the montage,
## now to the registry): current_scene / active_character = the scene after the last completed exit event, as the
## replay validation computes it. Finished playthroughs (slice_completed) and unknown shapes stay unchanged.
## Used for save slots (read_container) and for the profile snapshots of the memories (Memories.snapshot_raw).
static func rebase_story(story: Dictionary) -> Dictionary:
	var st: Dictionary = story.duplicate(true)
	var events = st.get("completed_events", [])
	if not (events is Array) or (events as Array).has("slice_completed") or not st.has("current_scene"):
		return st
	var sd: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/v3/scenes.json"))
	if not sd.get("ok", false) or not (sd["value"] is Dictionary):
		return st
	var scenes := {}
	var next_after := {}
	for s in sd["value"].get("scenes", []):
		scenes[str(s["id"])] = s
		if s.get("next_scene") != null:
			next_after[str(s.get("exit_on_event", ""))] = str(s["next_scene"])
	var cur := str(sd["value"].get("start_scene", ""))
	for ev in events:
		cur = str(next_after.get(str(ev), cur))
	if scenes.has(cur) and cur != str(st.get("current_scene")):
		st["current_scene"] = cur
		st["active_character"] = str(scenes[cur].get("protagonist", "none"))
	return st


## Strict UTF-8 check (no overlongs, no surrogates) so corrupt files are rejected without decoding noise.
static func _valid_utf8(b: PackedByteArray) -> bool:
	var i := 0
	var n := b.size()
	while i < n:
		var c := b[i]
		if c < 0x80:
			i += 1
			continue
		var extra := 0
		var cp := 0
		var min_cp := 0
		if c >= 0xC2 and c <= 0xDF:
			extra = 1
			cp = c & 0x1F
			min_cp = 0x80
		elif c >= 0xE0 and c <= 0xEF:
			extra = 2
			cp = c & 0x0F
			min_cp = 0x800
		elif c >= 0xF0 and c <= 0xF4:
			extra = 3
			cp = c & 0x07
			min_cp = 0x10000
		else:
			return false
		if i + extra >= n:
			return false
		for k in range(1, extra + 1):
			var cc := b[i + k]
			if (cc & 0xC0) != 0x80:
				return false
			cp = (cp << 6) | (cc & 0x3F)
		if cp < min_cp or cp > 0x10FFFF or (cp >= 0xD800 and cp <= 0xDFFF):
			return false
		i += extra + 1
	return true


## tmp → verify → copy previous to .bak → rename tmp over the slot file.
static func _write_atomic(path: String, text: String) -> Dictionary:
	var dir := path.get_base_dir()
	if not DirAccess.dir_exists_absolute(dir):
		# A file where a folder should be would make Godot print an engine error; report it cleanly.
		var probe := dir
		for _guard in 32:
			if probe == "" or DirAccess.dir_exists_absolute(probe):
				break
			if FileAccess.file_exists(probe):
				return {"ok": false, "error": "Save directory blocked by a file: " + probe}
			probe = probe.get_base_dir()
		var de := DirAccess.make_dir_recursive_absolute(dir)
		if de != OK:
			return {"ok": false, "error": "Cannot create %s (%s)" % [dir, error_string(de)]}
	var tmp := path + ".tmp"
	var bak := path + ".bak"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return {"ok": false, "error": "Cannot write %s (%s)" % [tmp, error_string(FileAccess.get_open_error())]}
	var stored := f.store_string(text)
	f.flush()
	var ferr := f.get_error()
	f.close()
	if not stored or ferr != OK or FileAccess.get_file_as_string(tmp) != text:
		DirAccess.remove_absolute(tmp)
		return {"ok": false, "error": "Write verification failed for " + tmp}
	if FileAccess.file_exists(path):
		var ce := DirAccess.copy_absolute(path, bak)
		if ce != OK:
			DirAccess.remove_absolute(tmp)
			return {"ok": false, "error": "Cannot keep backup %s (%s)" % [bak, error_string(ce)]}
	var re := DirAccess.rename_absolute(tmp, path)
	if re != OK:
		if not FileAccess.file_exists(path) and FileAccess.file_exists(bak):
			DirAccess.copy_absolute(bak, path)
		if FileAccess.file_exists(tmp):
			DirAccess.remove_absolute(tmp)
		return {"ok": false, "error": "Cannot replace %s (%s)" % [path, error_string(re)]}
	return {"ok": true, "error": ""}
