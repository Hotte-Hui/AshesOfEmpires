extends Node
## Localisation: merges data/v3/locale_de.json with every data/locale/<locale>_*.json (later files override).
## Loc.t("key", {"name": "Alexei"}) -> formatted string; unknown keys return "[key]" so gaps are visible.
## Extensions (story_engine area): t_or(), keys(), missing(), source_of(), overrides (QA of key collisions).

var locale := "de"
## [key, earlier file, later file] for every key a later file redefined (filled by reload()).
var overrides: Array = []
var _strings: Dictionary = {}
var _sources: Dictionary = {}

func _ready() -> void:
	reload()

func reload() -> void:
	_strings.clear()
	_sources.clear()
	overrides.clear()
	_merge_file("res://data/v3/locale_de.json")
	var dir := DirAccess.open("res://data/locale")
	if dir:
		var files := Array(dir.get_files())
		files.sort()
		for f in files:
			if f.begins_with(locale + "_") and f.ends_with(".json"):
				_merge_file("res://data/locale/" + f)

func _merge_file(path: String) -> void:
	if not FileAccess.file_exists(path):
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(data) != TYPE_DICTIONARY:
		push_warning("Loc: cannot parse " + path)
		return
	var table = data.get("strings", data)
	if typeof(table) != TYPE_DICTIONARY:
		push_warning("Loc: no string table in " + path)
		return
	for k in table:
		var key := str(k)
		if _sources.has(key) and _sources[key] != path:
			overrides.append([key, _sources[key], path])
		_strings[key] = str(table[k])
		_sources[key] = path

func has(key: String) -> bool:
	return _strings.has(key)

func t(key: String, args: Dictionary = {}) -> String:
	var s: String = _strings.get(key, "[" + key + "]")
	return s.format(args) if not args.is_empty() else s

## Like t(), but returns `fallback` (formatted with args) when the key is unknown.
func t_or(key: String, fallback: String, args: Dictionary = {}) -> String:
	var s: String = _strings.get(key, fallback)
	return s.format(args) if not args.is_empty() else s

## All loaded keys, sorted.
func keys() -> Array:
	var k := _strings.keys()
	k.sort()
	return k

## The subset of `wanted` keys that have no string.
func missing(wanted: Array) -> Array:
	var out: Array = []
	for k in wanted:
		if not _strings.has(str(k)):
			out.append(str(k))
	return out

## File that provided the final value of `key` ("" if unknown).
func source_of(key: String) -> String:
	return _sources.get(key, "")
