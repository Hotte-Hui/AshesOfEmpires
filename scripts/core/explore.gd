extends Node
## Exploration layer (TECHNICAL_ARCHITECTURE §12): optional discoveries, secrets, easter eggs, chats and
## real-history cards. None of this touches the canonical Story state.
##
## Data: data/explore/*.json (one owner per file, read in file-name order)
##   area files    {"area": "karsk", "entries": [{id, kind, level, title_key, text_key, prompt_key?, image?,
##                  history?: [card ids], lines?: [{speaker, key, expr}] (kind "chat" only)}]}
##   history files {"side": "reich"|"soviet", "cards": [{id, side, title_key, text_key, year,
##                  sources: [{label, url}]}]}
##
## Public API (stable, §12.1): find(id) -> {ok, new, entry, cards_new}, is_found, entry, card, counts,
## history_counts, chat_lines, prompt_for, state()/restore()/reset(), signals found / history_unlocked /
## state_changed. Additions (explore-system round 2): validation on load (`warnings`), data-ordered listings
## (areas, entries_for, found_entries, cards_list, found_cards), per-area/level/kind/side counts, progress(),
## cards_of(), entry_image() (resolved through Symbols.pick), load_data() for tests and UI previews.
## Save format (Game.save_extra()["explore"]) is unchanged: {"found": [ids in find order], "cards": [ids]}.

signal found(id: String)
signal history_unlocked(card_id: String)
signal state_changed
## Emitted after reload()/load_data() (data changed, not progress).
signal data_reloaded

const DIR := "res://data/explore/"
const KINDS := ["detail", "secret", "easter_egg", "chat"]
const SIDES := ["reich", "soviet"]
## Close-up images are pixel art shown at x3 (§12.1).
const MAX_IMAGE := Vector2i(320, 200)

## Problems found by the last reload()/load_data(): clear, one line each (also printed as warnings).
var warnings: Array[String] = []
## Print each new warning with push_warning (tests switch this off for deliberately broken data).
var print_warnings := true

var _entries: Dictionary = {}     # id -> entry (insertion order = data order)
var _cards: Dictionary = {}       # card id -> card (data order)
var _found: Dictionary = {}       # id -> true (insertion order = find order; unknown ids are kept for saves)
var _cards_found: Dictionary = {} # card id -> true
var _areas: Array = []            # area names in data order
var _entry_src: Dictionary = {}   # id -> source file
var _card_src: Dictionary = {}    # card id -> source file
var _load_warnings: Array[String] = []


func _ready() -> void:
	reload()


# ================================================================ loading & validation
## Reads every *.json in `dir` (sorted by file name) and validates the result.
func reload(dir := DIR) -> void:
	clear_data()
	var d := DirAccess.open(dir)
	if d != null:
		var files: Array = Array(d.get_files())
		files.sort()
		for f in files:
			if not str(f).ends_with(".json"):
				continue
			var path := dir.path_join(str(f))
			var j := JSON.new()
			var err := j.parse(FileAccess.get_file_as_string(path))
			if err != OK:
				_warn_load("%s: invalid JSON (line %d: %s)" % [f, j.get_error_line(), j.get_error_message()])
				continue
			_ingest(j.data, str(f))
	_finish_load()


## Adds one area/history dictionary (same format as a file) and re-validates. For tests and UI previews.
func load_data(data, source := "memory") -> void:
	_ingest(data, source)
	_finish_load()


## Forgets all data (not the progress).
func clear_data() -> void:
	_entries.clear()
	_cards.clear()
	_areas.clear()
	_entry_src.clear()
	_card_src.clear()
	_load_warnings.clear()
	warnings.clear()


func _finish_load() -> void:
	var before := warnings.duplicate()
	validate()
	if print_warnings:
		var fresh: Array[String] = []
		for w in warnings:
			if not (w in before):
				fresh.append(w)
		if fresh.size() <= 3:
			for w in fresh:
				push_warning("Explore: " + w)
		else:   # one compact report instead of a backtrace per line
			push_warning("Explore: %d data problem(s) in %s:\n  - %s" % [fresh.size(), DIR, "\n  - ".join(fresh)])
	data_reloaded.emit()


func _warn_load(msg: String) -> void:
	_load_warnings.append(msg)


func _ingest(data, source: String) -> void:
	if not (data is Dictionary):
		_warn_load("%s: top level must be an object" % source)
		return
	var area := str(data.get("area", source.get_basename()))
	var side := str(data.get("side", ""))
	var entries = data.get("entries", [])
	var cards = data.get("cards", [])
	if not (entries is Array) or not (cards is Array):
		_warn_load("%s: 'entries' and 'cards' must be arrays" % source)
		return
	if entries.is_empty() and cards.is_empty():
		_warn_load("%s: neither 'entries' nor 'cards' found" % source)
	for e in entries:
		if not (e is Dictionary) or str(e.get("id", "")) == "":
			_warn_load("%s: entry without id skipped" % source)
			continue
		var id := str(e["id"])
		if _entries.has(id):
			_warn_load("duplicate entry id '%s' in %s (first defined in %s; ignored)" % [id, source, _entry_src[id]])
			continue
		var x: Dictionary = e.duplicate(true)
		x["area"] = str(x.get("area", area))
		_entries[id] = x
		_entry_src[id] = source
		if not (x["area"] in _areas):
			_areas.append(x["area"])
	for c in cards:
		if not (c is Dictionary) or str(c.get("id", "")) == "":
			_warn_load("%s: card without id skipped" % source)
			continue
		var cid := str(c["id"])
		if _cards.has(cid):
			_warn_load("duplicate card id '%s' in %s (first defined in %s; ignored)" % [cid, source, _card_src[cid]])
			continue
		var y: Dictionary = c.duplicate(true)
		if str(y.get("side", "")) == "" and side != "":
			y["side"] = side
		_cards[cid] = y
		_card_src[cid] = source


## Checks the loaded data; returns (and stores in `warnings`) one clear line per problem:
## unknown kinds, missing fields, Loc keys without text, dangling history ids, missing image files,
## malformed cards and cards that no entry links (they could never be found).
func validate() -> Array[String]:
	var out: Array[String] = _load_warnings.duplicate()
	var loc := _loc()
	var linked := {}
	for id in _entries:
		var e: Dictionary = _entries[id]
		var src := str(_entry_src.get(id, "?"))
		var where := "entry '%s' (%s)" % [id, src]
		var kind := str(e.get("kind", ""))
		if not (kind in KINDS):
			out.append("%s: unknown kind '%s' (allowed: %s)" % [where, kind, ", ".join(KINDS)])
		if str(e.get("level", "")) == "":
			out.append("%s: missing 'level'" % where)
		var keys := ["title_key"]
		if kind != "chat":
			keys.append("text_key")
		for k in keys:
			if str(e.get(k, "")) == "":
				out.append("%s: missing '%s'" % [where, k])
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			if key != "" and loc != null and not loc.has(key):
				out.append("%s: %s '%s' has no text in data/locale" % [where, k, key])
		var hist = e.get("history", [])
		if not (hist is Array):
			out.append("%s: 'history' must be an array of card ids" % where)
		else:
			for cid in hist:
				linked[str(cid)] = true
				if not _cards.has(str(cid)):
					out.append("%s: history card '%s' does not exist" % [where, cid])
		var img := str(e.get("image", ""))
		if img != "" and not (ResourceLoader.exists(img) or FileAccess.file_exists(img)):
			out.append("%s: image '%s' not found" % [where, img])
		var lines = e.get("lines", [])
		if kind == "chat":
			if not (lines is Array) or lines.is_empty():
				out.append("%s: chat without 'lines'" % where)
		if lines is Array:
			for i in lines.size():
				var l = lines[i]
				if not (l is Dictionary) or str(l.get("speaker", "")) == "" or str(l.get("key", "")) == "":
					out.append("%s: line %d needs 'speaker' and 'key'" % [where, i])
				elif loc != null and not loc.has(str(l["key"])):
					out.append("%s: line %d key '%s' has no text in data/locale" % [where, i, l["key"]])
		elif lines != null:
			out.append("%s: 'lines' must be an array" % where)
	for cid in _cards:
		var c: Dictionary = _cards[cid]
		var where := "card '%s' (%s)" % [cid, str(_card_src.get(cid, "?"))]
		if not (str(c.get("side", "")) in SIDES):
			out.append("%s: unknown side '%s' (allowed: %s)" % [where, c.get("side", ""), ", ".join(SIDES)])
		for k in ["title_key", "text_key"]:
			var key := str(c.get(k, ""))
			if key == "":
				out.append("%s: missing '%s'" % [where, k])
			elif loc != null and not loc.has(key):
				out.append("%s: %s '%s' has no text in data/locale" % [where, k, key])
		if str(c.get("year", "")) == "":
			out.append("%s: missing 'year'" % where)
		var srcs = c.get("sources", [])
		if not (srcs is Array) or srcs.is_empty():
			out.append("%s: needs at least one source {label, url}" % where)
		else:
			for s in srcs:
				if not (s is Dictionary) or str(s.get("label", "")) == "":
					out.append("%s: every source needs a 'label'" % where)
				elif s.has("url") and not (s["url"] is String):
					out.append("%s: source url must be a string" % where)
		if not _entries.is_empty() and not linked.has(cid):
			out.append("%s: not linked by any entry (it can never be found)" % where)
	warnings = out
	return out


func _loc() -> Node:
	var ml := Engine.get_main_loop() as SceneTree
	return ml.root.get_node_or_null("Loc") if ml != null and ml.root != null else null


# ================================================================ data access
func has_entry(id: String) -> bool:
	return _entries.has(id)


func entry(id: String) -> Dictionary:
	return _entries.get(id, {})


func has_card(card_id: String) -> bool:
	return _cards.has(card_id)


func card(id: String) -> Dictionary:
	return _cards.get(id, {})


## Areas in data order ("karsk", "berlin", ...).
func areas() -> Array:
	return _areas.duplicate()


## Entries of an area ("karsk"), a level id ("L_A1_Railyard") or all (""), in data order; optional kind filter.
func entries_for(area_or_level := "", kind := "") -> Array:
	var out: Array = []
	for id in _entries:
		var e: Dictionary = _entries[id]
		if area_or_level != "" and str(e.get("area", "")) != area_or_level and str(e.get("level", "")) != area_or_level:
			continue
		if kind != "" and str(e.get("kind", "")) != kind:
			continue
		out.append(e)
	return out


## Found entries of an area / level / everything, in data order.
func found_entries(area_or_level := "") -> Array:
	var out: Array = []
	for e in entries_for(area_or_level):
		if _found.has(str(e["id"])):
			out.append(e)
	return out


## Cards in data order, optionally of one side ("reich" / "soviet").
func cards_list(side := "") -> Array:
	var out: Array = []
	for cid in _cards:
		if side == "" or str(_cards[cid].get("side", "")) == side:
			out.append(_cards[cid])
	return out


func found_cards(side := "") -> Array:
	var out: Array = []
	for c in cards_list(side):
		if _cards_found.has(str(c["id"])):
			out.append(c)
	return out


## History card ids an entry links that exist (in the entry's order).
func cards_of(id: String) -> Array:
	var out: Array = []
	var h = entry(id).get("history", [])
	if h is Array:
		for c in h:
			if _cards.has(str(c)) and not (str(c) in out):
				out.append(str(c))
	return out


## Close-up image path of an entry ("" = none), resolved through Symbols.pick (§12.4 _hist variants).
func entry_image(id: String) -> String:
	var p := str(entry(id).get("image", ""))
	if p == "":
		return ""
	return Symbols.pick(p)


func is_found(id: String) -> bool:
	return _found.has(id)


func is_card_found(card_id: String) -> bool:
	return _cards_found.has(card_id)


# ================================================================ progress
## Marks an entry as found (idempotent). Returns {ok, new, entry, cards_new: [card ids unlocked now]}.
## Each card unlocks exactly once, even when several entries link it.
func find(id: String) -> Dictionary:
	if not _entries.has(id):
		return {"ok": false, "new": false, "entry": {}, "cards_new": []}
	var is_new := not _found.has(id)
	_found[id] = true
	var cards_new: Array = []
	for c in cards_of(id):
		if not _cards_found.has(c):
			_cards_found[c] = true
			cards_new.append(c)
	if is_new:
		found.emit(id)
	for c in cards_new:
		history_unlocked.emit(c)
	if is_new or not cards_new.is_empty():
		state_changed.emit()
	return {"ok": true, "new": is_new, "entry": _entries[id], "cards_new": cards_new}


## {found, total} for an area ("karsk"), a level id ("L_A1_Railyard") or everything (""); optional kind.
## Chats count too. Only entries that exist in the data are counted.
func counts(area_or_level := "", kind := "") -> Dictionary:
	var tot := 0
	var got := 0
	for e in entries_for(area_or_level, kind):
		tot += 1
		if _found.has(str(e["id"])):
			got += 1
	return {"found": got, "total": tot}


## {area: {found, total}} in data order.
func area_counts() -> Dictionary:
	var out := {}
	for a in _areas:
		out[a] = counts(a)
	return out


## {found, total} of real-history cards (all or one side). Unknown saved ids never count.
func history_counts(side := "") -> Dictionary:
	var tot := 0
	var got := 0
	for c in cards_list(side):
		tot += 1
		if _cards_found.has(str(c["id"])):
			got += 1
	return {"found": got, "total": tot}


## Everything at once (pause menu / journal header).
func progress() -> Dictionary:
	var e := counts()
	var h := history_counts()
	return {"found": e["found"], "total": e["total"], "cards_found": h["found"], "cards_total": h["total"]}


func chat_lines(id: String) -> Array:
	var e := entry(id)
	return e.get("lines", []) if e.get("lines", []) is Array else []


## Prompt label for an interactable (empty = default per kind).
func prompt_for(id: String) -> String:
	var e := entry(id)
	var k := str(e.get("prompt_key", ""))
	var loc := _loc()
	if k != "" and loc != null and loc.has(k):
		return loc.t(k)
	return ""


# ================================================================ persistence (save file extra.explore)
func state() -> Dictionary:
	return {"found": _found.keys(), "cards": _cards_found.keys()}


## Restores a state() dictionary. Unknown ids are kept (data may come back) but never counted; cards
## linked by found entries are re-attached silently, so a card can never be "unlocked" a second time.
func restore(d) -> void:
	_found.clear()
	_cards_found.clear()
	if d is Dictionary:
		var f = d.get("found", [])
		if f is Array:
			for id in f:
				if id is String or id is StringName:
					_found[str(id)] = true
		var c = d.get("cards", [])
		if c is Array:
			for cid in c:
				if cid is String or cid is StringName:
					_cards_found[str(cid)] = true
	for id in _found:
		for cid in cards_of(str(id)):
			_cards_found[cid] = true
	state_changed.emit()


func reset() -> void:
	_found.clear()
	_cards_found.clear()
	state_changed.emit()
