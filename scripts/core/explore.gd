extends Node
## Exploration layer (TECHNICAL_ARCHITECTURE §12): optional discoveries, secrets, easter eggs, chats and
## real-history cards. None of this touches the canonical Story state.
## MINIMAL CONTRACT IMPLEMENTATION — the explore-system specialist extends it; keep every public signature.
##
## Data: data/explore/*.json
##   area files    {"area": "karsk", "entries": [{id, kind, level, title_key, text_key, image?, history?, lines?}]}
##   history files {"side": "reich"|"soviet", "cards": [{id, side, title_key, text_key, year, sources:[{label,url}]}]}

signal found(id: String)
signal history_unlocked(card_id: String)
signal state_changed

const DIR := "res://data/explore/"

var _entries: Dictionary = {}     # id -> entry
var _cards: Dictionary = {}       # card id -> card
var _found: Dictionary = {}       # id -> true (entries)
var _cards_found: Dictionary = {} # card id -> true


func _ready() -> void:
	reload()


func reload() -> void:
	_entries.clear()
	_cards.clear()
	var d := DirAccess.open(DIR)
	if d == null:
		return
	for f in d.get_files():
		if not f.ends_with(".json"):
			continue
		var data = JSON.parse_string(FileAccess.get_file_as_string(DIR + f))
		if typeof(data) != TYPE_DICTIONARY:
			push_warning("Explore: cannot parse " + f)
			continue
		var area := str(data.get("area", f.get_basename()))
		for e in data.get("entries", []):
			if e is Dictionary and e.has("id"):
				var x: Dictionary = e.duplicate(true)
				x["area"] = str(x.get("area", area))
				_entries[str(x["id"])] = x
		for c in data.get("cards", []):
			if c is Dictionary and c.has("id"):
				_cards[str(c["id"])] = c.duplicate(true)


func has_entry(id: String) -> bool:
	return _entries.has(id)


func entry(id: String) -> Dictionary:
	return _entries.get(id, {})


func card(id: String) -> Dictionary:
	return _cards.get(id, {})


func entries_for(area_or_level := "") -> Array:
	var out: Array = []
	for id in _entries:
		var e: Dictionary = _entries[id]
		if area_or_level == "" or str(e.get("area", "")) == area_or_level or str(e.get("level", "")) == area_or_level:
			out.append(e)
	return out


func is_found(id: String) -> bool:
	return _found.has(id)


func is_card_found(card_id: String) -> bool:
	return _cards_found.has(card_id)


## Marks an entry as found (idempotent). Returns {ok, new, entry, cards_new: [card ids unlocked now]}.
func find(id: String) -> Dictionary:
	if not _entries.has(id):
		return {"ok": false, "new": false, "entry": {}, "cards_new": []}
	var is_new := not _found.has(id)
	_found[id] = true
	var cards_new: Array = []
	for cid in _entries[id].get("history", []):
		var c := str(cid)
		if _cards.has(c) and not _cards_found.has(c):
			_cards_found[c] = true
			cards_new.append(c)
			history_unlocked.emit(c)
	if is_new:
		found.emit(id)
	state_changed.emit()
	return {"ok": true, "new": is_new, "entry": _entries[id], "cards_new": cards_new}


## {found, total} for an area ("karsk"), a level id ("L_A1_Railyard") or everything (""). Chats count too.
func counts(area_or_level := "") -> Dictionary:
	var tot := 0
	var got := 0
	for e in entries_for(area_or_level):
		tot += 1
		if _found.has(str(e["id"])):
			got += 1
	return {"found": got, "total": tot}


func history_counts() -> Dictionary:
	return {"found": _cards_found.size(), "total": _cards.size()}


func chat_lines(id: String) -> Array:
	var e := entry(id)
	return e.get("lines", []) if e.get("lines", []) is Array else []


## Prompt label for an interactable (empty = default per kind).
func prompt_for(id: String) -> String:
	var e := entry(id)
	var k := str(e.get("prompt_key", ""))
	if k != "" and Loc.has(k):
		return Loc.t(k)
	return ""


func state() -> Dictionary:
	return {"found": _found.keys(), "cards": _cards_found.keys()}


func restore(d) -> void:
	reset()
	if d is Dictionary:
		for id in d.get("found", []):
			_found[str(id)] = true
		for c in d.get("cards", []):
			_cards_found[str(c)] = true
	state_changed.emit()


func reset() -> void:
	_found.clear()
	_cards_found.clear()
	state_changed.emit()
