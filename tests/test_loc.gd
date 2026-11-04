extends RefCounted
## Localisation coverage: every text key of data/v3 resolves, every sys.* key the Story/Saves code returns
## (error_key, slot names, journal headers/states/categories/people) exists in data/locale/de_system.json,
## the system keys are not overridden by other areas, and the Loc API (t/has/reload + extensions) works.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const SAVES := preload("res://scripts/core/save_system.gd")
const SYSTEM_FILE := "res://data/locale/de_system.json"

var kit: Kit
var loc: Node


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("data_text_keys_resolve", _data_keys)
	kit.run_case("code_sys_keys_exist", _code_keys)
	kit.run_case("journal_and_slot_keys_exist", _journal_keys)
	kit.run_case("system_file_shape", _system_file)
	kit.run_case("loc_api", _api)
	kit.cleanup()
	return kit.failures


func _data_keys() -> bool:
	var d: Dictionary = ENGINE.load_data()["data"]
	var wanted: Array = []
	for q in d["quests"]["quests"]:
		wanted.append(q["title_key"])
		for o in q["objectives"]:
			wanted.append(o["text_key"])
			for c in o.get("choices", []):
				wanted.append(c["text_key"])
	for it in d["items"]["items"]:
		wanted.append_array([it["name_key"], it["description_key"]])
	for s in d["scenes"]["scenes"]:
		wanted.append(s["title_key"])
	for conv in d["dialogue"]["conversations"]:
		for node in conv["nodes"]:
			wanted.append(node["text_key"])
	kit.eq(loc.missing(wanted), [], "data/v3 text keys without German text")
	return true


## Every literal "sys.xxx" in the engine and save system sources must exist.
func _code_keys() -> bool:
	var re := RegEx.new()
	re.compile("\"(sys\\.[a-z0-9_.]+)\"")
	var found := {}
	for path in ["res://scripts/story/story_engine.gd", "res://scripts/core/save_system.gd"]:
		for m in re.search_all(FileAccess.get_file_as_string(path)):
			var key := m.get_string(1)
			if not key.ends_with("."):
				found[key] = path
	kit.ok(found.size() >= 20, "found the error keys in the sources (%d)" % found.size())
	kit.eq(loc.missing(found.keys()), [], "error/system keys used in code but missing in de_system.json")
	return true


func _journal_keys() -> bool:
	var d: Dictionary = ENGINE.load_data()["data"]
	var wanted: Array = []
	for slot in SAVES.SLOTS:
		wanted.append("sys.save.slot." + slot)
	for st in ["available", "complete", "locked"]:
		wanted.append("sys.journal.state." + st)
	for st in ["active", "complete", "locked"]:
		wanted.append("sys.journal.quest." + st)
	for tab in ["objectives", "evidence", "people", "decisions"]:
		wanted.append_array(["sys.journal.tab." + tab, "sys.journal.empty." + tab])
	for it in d["items"]["items"]:
		wanted.append("sys.journal.category." + it["category"])
	var people := {}
	for p in d["flags"]["protagonists"]:
		people[p] = true
	for conv in d["dialogue"]["conversations"]:
		for node in conv["nodes"]:
			people[node["speaker"]] = true
	for p in people:
		wanted.append_array(["sys.journal.person.%s.name" % p, "sys.journal.person.%s.note" % p])
	kit.eq(loc.missing(wanted), [], "journal/slot keys missing")
	return true


func _system_file() -> bool:
	var parsed: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string(SYSTEM_FILE))
	kit.is_ok(parsed, "de_system.json parses")
	var strings: Dictionary = parsed.get("value", {}).get("strings", {})
	kit.ok(strings.size() >= 60, "system strings present (%d)" % strings.size())
	for k in strings:
		kit.ok(str(k).begins_with("sys."), "key %s uses the sys. namespace" % k)
		kit.ok(typeof(strings[k]) == TYPE_STRING and (strings[k] as String).strip_edges() != "", "key %s has text" % k)
		kit.eq(loc.source_of(k), SYSTEM_FILE, "key %s is not overridden by another area" % k)
	for o in loc.overrides:
		kit.ok(not str(o[0]).begins_with("sys."), "system key %s redefined by %s" % [o[0], o[2]])
	kit.ok(strings.get("sys.journal.person.konrad.name", "") == "Konrad Adler", "protagonist name")
	return true


func _api() -> bool:
	kit.eq(loc.t("sys.save.playtime", {"time": "1:23"}), "Spielzeit 1:23", "t() with args")
	kit.eq(loc.t("sys.journal.title"), "Tagebuch", "t()")
	kit.eq(loc.t("no.such.key"), "[no.such.key]", "unknown key visible")
	kit.eq(loc.t_or("no.such.key", "Ersatz {x}", {"x": 1}), "Ersatz 1", "t_or fallback")
	kit.eq(loc.has("ui.journal"), true, "base locale loaded")
	kit.ok(loc.keys().has("sys.err.locked"), "keys()")
	return true
