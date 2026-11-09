extends Node
## Localisation: merges data/v3/locale_de.json with every data/locale/<locale>_*.json (later files override) — German
## is the source table. Another language lays its files over it, each over its German twin (data/locale/de_x.json →
## data/locale/en_x.json, the "strings" of data/v3/locale_de.json → data/locale/en_v3.json); a key the twin does not
## translate keeps its German text, so a gap never shows a raw key (TECHNICAL_ARCHITECTURE §12.14).
## Loc.t("key", {"name": "Alexei"}) -> formatted string; unknown keys return "[key]" so gaps are visible.
## Language: the Settings value "language" (first launch: English unless the OS speaks German; automated runs stay
## German, `-- --lang=en` forces English for checks — Settings.forced_language). set_language() switches live: every
## Label/Button/RichTextLabel in the tree that shows a string of the old language gets the new one, then
## `language_changed` lets the open panels redo their formatted lines (UIRoot → _on_language_changed()).
## Extensions (story_engine area): t_or(), keys(), missing(), source_of(), overrides (QA of key collisions).

signal language_changed(language: String)

## The source language (its files define every key).
const SOURCE := "de"
## Playable languages, each in its own name (the settings menu lists them like this).
const LANGUAGES := {"de": "Deutsch", "en": "English"}
const V3_FILE := "res://data/v3/locale_de.json"

## Prefix of the source files (data/locale/<locale>_*.json) — stays the German source; `language` overlays it.
var locale := SOURCE
## Current language: "de" = the source table as it is, else the overlay of data/locale/<language>_*.json.
var language := SOURCE
## Folder of the locale files (tests point a fresh instance at a temporary folder).
var locale_dir := "res://data/locale"
## [key, earlier file, later file] for every key a later SOURCE file redefined (filled by reload()).
var overrides: Array = []
var _strings: Dictionary = {}
var _sources: Dictionary = {}
var _translated: Dictionary = {}   # key -> overlay file that gave the current text (language != SOURCE)
var _shown: Dictionary = {}        # text -> key of every plain t() result: a switch re-translates by the real key


func _ready() -> void:
	var s := get_node_or_null("/root/Settings")
	if s != null and s.has_method("get_value"):
		var v := str(s.get_value("language"))
		if LANGUAGES.has(v):
			language = v
	reload()


func reload() -> void:
	_strings.clear()
	_sources.clear()
	_translated.clear()
	overrides.clear()
	_merge_file(V3_FILE)
	for f in _files(locale):
		_merge_file(locale_dir + "/" + f)
	if language != locale:
		_overlay(language)


## data/locale files of one language prefix, sorted (the merge order).
func _files(prefix: String) -> Array:
	var out: Array = []
	var dir := DirAccess.open(locale_dir)
	if dir == null:
		return out
	for f in dir.get_files():
		if f.begins_with(prefix + "_") and f.ends_with(".json"):
			out.append(f)
	out.sort()
	return out


func _merge_file(path: String) -> void:
	var table := _table(path)
	for k in table:
		var key := str(k)
		if _sources.has(key) and _sources[key] != path:
			overrides.append([key, _sources[key], path])
		_strings[key] = str(table[k])
		_sources[key] = path


## The string table of one locale file ({} when missing or broken; a broken file only warns).
static func _table(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(data) != TYPE_DICTIONARY:
		push_warning("Loc: cannot parse " + path)
		return {}
	var table = data.get("strings", data)
	if typeof(table) != TYPE_DICTIONARY:
		push_warning("Loc: no string table in " + path)
		return {}
	return table


## The overlay file of `lang` for a source file: de_x.json → en_x.json, data/v3/locale_de.json → en_v3.json.
func twin_path(source_path: String, lang: String) -> String:
	if source_path == V3_FILE:
		return locale_dir + "/" + lang + "_v3.json"
	var f := source_path.get_file()
	if f.begins_with(locale + "_"):
		return source_path.get_base_dir() + "/" + lang + "_" + f.substr(locale.length() + 1)
	return ""


## Every key takes the text of the twin of the file that gave its German text; keys without one stay German.
func _overlay(lang: String) -> void:
	var tables := {}
	for key in _strings:
		var twin := twin_path(str(_sources[key]), lang)
		if twin == "":
			continue
		if not tables.has(twin):
			tables[twin] = _table(twin)
		var tb: Dictionary = tables[twin]
		if tb.has(key) and str(tb[key]) != "":
			_strings[key] = str(tb[key])
			_translated[key] = twin


## Switches the language now (Settings.apply calls this for the "language" setting): re-reads the tables,
## re-translates the texts on screen (retranslate) and emits language_changed. Unknown codes are ignored.
func set_language(lang: String) -> void:
	if not LANGUAGES.has(lang) or lang == language:
		return
	var old := _strings.duplicate()
	var shown := _shown
	_shown = {}
	language = lang
	reload()
	if is_inside_tree():
		retranslate(get_tree().root, old, shown)
	language_changed.emit(language)


## Re-translates a tree after a switch: every Label, Button and RichTextLabel whose text is the old language's
## string of a key — as it is or in capitals (headings, kickers) — gets the current one. `shown` (text -> key of the
## old language's t() results) decides between keys that shared a text; otherwise ui.* keys win. Formatted lines are
## the panels' job (language_changed). Returns how many texts changed.
func retranslate(root: Node, old: Dictionary, shown: Dictionary = {}) -> int:
	var map := {}
	var cap_map := {}
	for k in old:
		var a := str(old[k])
		if a.strip_edges() == "" or str(_strings.get(k, a)) == a:
			continue
		if not map.has(a) or str(k).begins_with("ui."):
			map[a] = k
		var ua := caps(a)
		if ua != a and (not cap_map.has(ua) or str(k).begins_with("ui.")):
			cap_map[ua] = k
	for txt in shown:
		var k = shown[txt]
		if old.has(k) and str(old[k]) == str(txt) and map.has(txt):
			map[txt] = k
			if cap_map.has(caps(str(txt))):
				cap_map[caps(str(txt))] = k
	if (map.is_empty() and cap_map.is_empty()) or root == null:
		return 0
	var n := 0
	var stack: Array = [root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		if node is Label or node is Button or node is RichTextLabel:
			var txt := str(node.get("text"))
			var now := ""
			if map.has(txt):
				now = str(_strings[map[txt]])
				_shown[now] = map[txt]
			elif cap_map.has(txt):
				now = caps(str(_strings[cap_map[txt]]))
			if now != "" and now != txt:
				node.set("text", now)
				n += 1
		stack.append_array(node.get_children())
	return n


## Capitals as the headings show them (ß → SS).
static func caps(s: String) -> String:
	return s.to_upper().replace("ß", "SS")


func has(key: String) -> bool:
	return _strings.has(key)


func t(key: String, args: Dictionary = {}) -> String:
	var s: String = _strings.get(key, "[" + key + "]")
	if not args.is_empty():
		return s.format(args)
	_shown[s] = key
	return s


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


## Source file that provided the German text of `key` ("" if unknown) — also while another language is shown.
func source_of(key: String) -> String:
	return _sources.get(key, "")


## Overlay file that translated `key` into the current language ("" = shows the German text).
func translated_by(key: String) -> String:
	return _translated.get(key, "")


## Keys of the source table without a translation in the current language (sorted; [] for German).
func untranslated() -> Array:
	var out: Array = []
	if language == locale:
		return out
	for k in _strings:
		if not _translated.has(k):
			out.append(k)
	out.sort()
	return out
