extends Node
## Localisation: merges data/v3/locale_de.json with every data/locale/*.json (later files override).
## Loc.t("key", {"name": "Alexei"}) -> formatted string; unknown keys return "[key]" so gaps are visible.

var locale := "de"
var _strings: Dictionary = {}

func _ready() -> void:
	reload()

func reload() -> void:
	_strings.clear()
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
	var table: Dictionary = data.get("strings", data)
	for k in table:
		_strings[str(k)] = str(table[k])

func has(key: String) -> bool:
	return _strings.has(key)

func t(key: String, args: Dictionary = {}) -> String:
	var s: String = _strings.get(key, "[" + key + "]")
	return s.format(args) if not args.is_empty() else s
