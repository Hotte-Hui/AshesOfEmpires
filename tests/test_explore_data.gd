extends RefCounted
## Validates whatever data/explore/*.json files exist (TECHNICAL_ARCHITECTURE §12.1/§12.3; the files are owned by
## the content specialists): structure and references, never counts.
## Strict (failures): JSON parses; area files {area, entries[]} / history files {side, cards[]}; unique ids across
## all files; known kinds; level scenes exist; title/text/prompt/line keys have German text; chat lines are
## {speaker, key}; history ids are strings; cards have side, title/text keys with text, year, sources [{label,
## url?}] with http(s) URLs; images are PNG pixel art <= 320x200 (and a _hist variant has the same size).
## Cross-delivery references are strict once the target delivery exists, else printed as a note (so the suite
## stays green while other specialists are still writing): history cards of a side whose history file is not
## there yet, images of an area whose assets/explore/<area>/ folder does not exist yet.
## Advisory notes only: card texts outside 450-800 characters, card ids outside the §12.3 table.

const Kit := preload("res://tests/support/test_kit.gd")
const DIR := "res://data/explore/"
const KINDS := ["detail", "secret", "easter_egg", "chat"]
const SIDES := ["reich", "soviet"]
const MAX_IMAGE := Vector2i(320, 200)
const FIXED_CARDS := ["hist.reich.germania", "hist.reich.evictions", "hist.reich.schwerbelastungskoerper",
	"hist.reich.wannsee", "hist.reich.reichsbahn", "hist.reich.generalplan_ost", "hist.reich.t4",
	"hist.reich.forced_labor", "hist.soviet.secret_protocol", "hist.soviet.katyn", "hist.soviet.deportations",
	"hist.soviet.novocherkassk", "hist.soviet.kyshtym", "hist.soviet.gulag", "hist.soviet.great_terror",
	"hist.soviet.holodomor"]

var kit: Kit
var loc: Node
var files: Dictionary = {}     # file name -> parsed Dictionary (only files that parsed)
var entries: Dictionary = {}   # id -> [entry, file]
var cards: Dictionary = {}     # id -> [card, file]
var sides_present: Dictionary = {}
var notes: Array = []


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("files_parse_and_have_a_known_shape", _files)
	kit.run_case("entries_structure_and_ids", _entries)
	kit.run_case("entry_text_keys_resolve", _entry_keys)
	kit.run_case("cards_structure_and_keys", _cards)
	kit.run_case("history_references", _history_refs)
	kit.run_case("images_exist_and_fit", _images)
	kit.run_case("explore_loader_agrees", _loader_agrees)
	kit.cleanup()
	if files.is_empty():
		print("      note: data/explore/ has no files yet — nothing to validate")
	for n in notes:
		print("      note (other deliveries, not a failure): " + str(n))
	return kit.failures


func _files() -> bool:
	var d := DirAccess.open(DIR)
	if d == null:
		return true
	var names: Array = Array(d.get_files())
	names.sort()
	for f in names:
		if not str(f).ends_with(".json"):
			continue
		var j := JSON.new()
		var err := j.parse(FileAccess.get_file_as_string(DIR + str(f)))
		if not kit.ok(err == OK, "%s parses (line %d: %s)" % [f, j.get_error_line(), j.get_error_message()]):
			continue
		var data = j.data
		if not kit.ok(data is Dictionary, "%s: top level is an object" % f):
			continue
		var is_area: bool = data.has("entries")
		var is_hist: bool = data.has("cards")
		kit.ok(is_area != is_hist, "%s: either 'entries' (area file) or 'cards' (history file)" % f)
		if is_area:
			kit.ok(data["entries"] is Array, "%s: entries is an array" % f)
			kit.ok(str(data.get("area", "")) != "", "%s: has an 'area' name" % f)
		if is_hist:
			kit.ok(data["cards"] is Array, "%s: cards is an array" % f)
			var side := str(data.get("side", ""))
			if kit.ok(side in SIDES, "%s: side is one of %s (got '%s')" % [f, SIDES, side]):
				sides_present[side] = true
		files[str(f)] = data
	return true


func _entries() -> bool:
	for f in files:
		var data: Dictionary = files[f]
		if not (data.get("entries", null) is Array):
			continue
		for e in data["entries"]:
			if not kit.ok(e is Dictionary, "%s: every entry is an object" % f):
				continue
			var id := str(e.get("id", ""))
			if not kit.ok(id != "" and not id.contains(" "), "%s: entry id present and without spaces ('%s')" % [f, id]):
				continue
			if not kit.ok(not entries.has(id), "entry id '%s' unique (also in %s)" % [id, entries.get(id, ["", ""])[1]]):
				continue
			entries[id] = [e, f]
			var where := "%s/%s" % [f, id]
			var kind := str(e.get("kind", ""))
			kit.ok(kind in KINDS, "%s: kind '%s' is one of %s" % [where, kind, KINDS])
			var lvl := str(e.get("level", ""))
			kit.ok(lvl != "" and ResourceLoader.exists("res://scenes/levels/%s.tscn" % lvl), "%s: level '%s' exists" % [where, lvl])
			kit.ok(str(e.get("title_key", "")) != "", "%s: has title_key" % where)
			if kind != "chat":
				kit.ok(str(e.get("text_key", "")) != "", "%s: has text_key" % where)
			var hist = e.get("history", [])
			if kit.ok(hist is Array, "%s: history is an array" % where):
				for c in hist:
					kit.ok(c is String and str(c).begins_with("hist."), "%s: history id '%s' is a hist.* string" % [where, c])
			var lines = e.get("lines", null)
			if kind == "chat":
				kit.ok(lines is Array and not (lines as Array).is_empty(), "%s: chat has lines" % where)
			if lines != null and kit.ok(lines is Array, "%s: lines is an array" % where):
				for i in (lines as Array).size():
					var l = lines[i]
					kit.ok(l is Dictionary and str(l.get("speaker", "")) != "" and str(l.get("key", "")) != "",
						"%s: line %d has speaker and key" % [where, i])
			if e.has("image"):
				kit.ok(e["image"] is String and str(e["image"]).begins_with("res://") and str(e["image"]).ends_with(".png"),
					"%s: image is a res:// PNG path" % where)
	return true


func _entry_keys() -> bool:
	var missing: Array = []
	for id in entries:
		var e: Dictionary = entries[id][0]
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			if key != "" and not loc.has(key):
				missing.append("%s.%s=%s" % [id, k, key])
		var lines = e.get("lines", [])
		if lines is Array:
			for l in lines:
				if l is Dictionary and str(l.get("key", "")) != "" and not loc.has(str(l["key"])):
					missing.append("%s line %s" % [id, l["key"]])
	kit.eq(missing, [], "explore text keys without German text in data/locale")
	return true


func _cards() -> bool:
	var missing: Array = []
	for f in files:
		var data: Dictionary = files[f]
		if not (data.get("cards", null) is Array):
			continue
		var file_side := str(data.get("side", ""))
		for c in data["cards"]:
			if not kit.ok(c is Dictionary, "%s: every card is an object" % f):
				continue
			var id := str(c.get("id", ""))
			if not kit.ok(id.begins_with("hist."), "%s: card id '%s' starts with hist." % [f, id]):
				continue
			if not kit.ok(not cards.has(id), "card id '%s' unique" % id):
				continue
			cards[id] = [c, f]
			var side := str(c.get("side", file_side))
			kit.ok(side == file_side, "%s/%s: card side '%s' matches the file side '%s'" % [f, id, side, file_side])
			for k in ["title_key", "text_key"]:
				var key := str(c.get(k, ""))
				if kit.ok(key != "", "%s/%s: has %s" % [f, id, k]) and not loc.has(key):
					missing.append("%s.%s=%s" % [id, k, key])
			kit.ok(str(c.get("year", "")) != "", "%s/%s: has a year" % [f, id])
			var srcs = c.get("sources", [])
			if kit.ok(srcs is Array and not (srcs as Array).is_empty(), "%s/%s: has sources" % [f, id]):
				for s in srcs:
					if not kit.ok(s is Dictionary and str(s.get("label", "")) != "", "%s/%s: every source has a label" % [f, id]):
						continue
					var url := str(s.get("url", ""))
					kit.ok(url == "" or url.begins_with("https://") or url.begins_with("http://"),
						"%s/%s: source url is plain http(s) text ('%s')" % [f, id, url])
			if not (id in FIXED_CARDS):
				notes.append("card id '%s' is not in the §12.3 table" % id)
			var key := str(c.get("text_key", ""))
			if loc.has(key):
				var n := str(loc.t(key)).length()
				if n < 450 or n > 800:
					notes.append("card '%s' text has %d characters (§12.3 asks for 450-800)" % [id, n])
	kit.eq(missing, [], "history card keys without German text in data/locale")
	return true


func _history_refs() -> bool:
	var linked := {}
	for id in entries:
		var e: Dictionary = entries[id][0]
		var hist = e.get("history", [])
		if not (hist is Array):
			continue
		for c in hist:
			var cid := str(c)
			linked[cid] = true
			if cards.has(cid):
				continue
			var side := cid.get_slice(".", 1)
			if sides_present.has(side):
				kit.fail("entry '%s' links history card '%s', which data/explore/ does not define" % [id, cid])
			else:
				notes.append("entry '%s' links '%s'; no %s history file delivered yet" % [id, cid, side])
	for cid in cards:
		if not linked.has(cid) and not entries.is_empty():
			notes.append("card '%s' is not linked by any entry (cannot be found yet)" % cid)
	kit.ok(true, "history references checked")
	return true


func _images() -> bool:
	for id in entries:
		var e: Dictionary = entries[id][0]
		var img := str(e.get("image", ""))
		if img == "":
			continue
		var exists := ResourceLoader.exists(img) or FileAccess.file_exists(img)
		if not exists:
			if DirAccess.dir_exists_absolute(img.get_base_dir()):
				kit.fail("entry '%s': image %s does not exist" % [id, img])
			else:
				notes.append("entry '%s': image folder %s not delivered yet" % [id, img.get_base_dir()])
			continue
		var im := Image.load_from_file(ProjectSettings.globalize_path(img))
		if not kit.ok(im != null and not im.is_empty(), "entry '%s': image %s loads" % [id, img]):
			continue
		kit.ok(im.get_width() <= MAX_IMAGE.x and im.get_height() <= MAX_IMAGE.y,
			"entry '%s': close-up %dx%d fits 320x200 (shown x3)" % [id, im.get_width(), im.get_height()])
		var hist := img.get_basename() + "_hist." + img.get_extension()
		if FileAccess.file_exists(hist):
			var h := Image.load_from_file(ProjectSettings.globalize_path(hist))
			kit.ok(h != null and h.get_size() == im.get_size(), "entry '%s': _hist variant has the same size" % id)
	return true


## The Explore loader reads the same files: every entry/card the test found must be reachable through its API.
func _loader_agrees() -> bool:
	var ex: Node = kit.track(load("res://scripts/core/explore.gd").new())
	ex.print_warnings = false
	ex.reload()
	for id in entries:
		kit.ok(ex.has_entry(id), "Explore.entry('%s') loaded" % id)
	for cid in cards:
		kit.ok(ex.has_card(cid), "Explore.card('%s') loaded" % cid)
	kit.eq(ex.counts()["total"], entries.size(), "Explore counts every entry once")
	kit.eq(ex.history_counts()["total"], cards.size(), "Explore counts every card once")
	return true
