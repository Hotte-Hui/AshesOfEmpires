extends RefCounted
## Explore autoload (scripts/core/explore.gd, TECHNICAL_ARCHITECTURE §12.1): find/counts/history API,
## cards unlock exactly once, unknown ids, save round trip through JSON (Game.save_extra()["explore"]),
## validation warnings for broken data and loading from a directory. Uses its own mock data only — the
## real data/explore/*.json files are checked by test_explore_data.gd.

const Kit := preload("res://tests/support/test_kit.gd")
const EXPLORE := "res://scripts/core/explore.gd"
const TMP_DIR := "user://test_explore_tmp/"

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("find_counts_and_listings", _find_counts)
	kit.run_case("cards_unlock_once", _cards_once)
	kit.run_case("signals", _signals)
	kit.run_case("unknown_ids", _unknown_ids)
	kit.run_case("save_round_trip_through_json", _round_trip)
	kit.run_case("restore_repairs_and_tolerates_garbage", _restore_edge)
	kit.run_case("clean_data_validates", _clean_validates)
	kit.run_case("broken_data_warnings", _broken_warnings)
	kit.run_case("reload_from_directory", _reload_dir)
	kit.run_case("prompt_and_chat_lines", _prompt_chat)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ fixtures
func _new() -> Node:
	var ex: Node = kit.track(load(EXPLORE).new())
	ex.print_warnings = false
	return ex


## Two areas, two history sides. Keys are real Loc keys so the clean set validates without warnings.
static func area_karsk() -> Dictionary:
	return {"area": "karsk", "entries": [
		{"id": "k.cat", "kind": "detail", "level": "L_A1_Railyard", "title_key": "ui.journal.title",
			"text_key": "ui.journal.view", "prompt_key": "ui.prompt.discover", "history": ["hist.s.one"]},
		{"id": "k.stash", "kind": "secret", "level": "L_A1_Railyard", "title_key": "ui.journal.title",
			"text_key": "ui.journal.view", "history": ["hist.s.one", "hist.s.two"],
			"image": "res://assets/ui/portrait_placeholder.png"},
		{"id": "k.snowman", "kind": "easter_egg", "level": "L_A1_Railyard", "title_key": "ui.journal.title",
			"text_key": "ui.journal.view"},
		{"id": "k.workers", "kind": "chat", "level": "L_A1_Railyard", "title_key": "ui.journal.title",
			"history": ["hist.s.three"], "lines": [
				{"speaker": "worker_a", "key": "ui.journal.view", "expr": "neutral"},
				{"speaker": "alexei", "key": "ui.journal.title"}]},
	]}


static func area_berlin() -> Dictionary:
	return {"area": "berlin", "entries": [
		{"id": "b.shelf", "kind": "detail", "level": "L_M1_Archive", "title_key": "ui.journal.title",
			"text_key": "ui.journal.view", "history": ["hist.r.one"]},
		{"id": "b.mouse", "kind": "easter_egg", "level": "L_M1_Archive", "title_key": "ui.journal.title",
			"text_key": "ui.journal.view"},
	]}


static func hist(side: String, ids: Array) -> Dictionary:
	var cards: Array = []
	for id in ids:
		cards.append({"id": id, "title_key": "ui.journal.title", "text_key": "ui.journal.view", "year": "1990",
			"sources": [{"label": "Archiv", "url": "https://example.org/a"}]})
	return {"side": side, "cards": cards}


func _loaded() -> Node:
	var ex := _new()
	ex.load_data(area_karsk(), "karsk.json")
	ex.load_data(area_berlin(), "berlin.json")
	ex.load_data(hist("soviet", ["hist.s.one", "hist.s.two", "hist.s.three"]), "history_soviet.json")
	ex.load_data(hist("reich", ["hist.r.one"]), "history_reich.json")
	return ex


static func _ids(list: Array) -> Array:
	var out: Array = []
	for e in list:
		out.append(str(e["id"]))
	return out


# ------------------------------------------------------------------ cases
func _find_counts() -> bool:
	var ex := _loaded()
	kit.eq(ex.areas(), ["karsk", "berlin"], "areas in data order")
	kit.eq(_ids(ex.entries_for("karsk")), ["k.cat", "k.stash", "k.snowman", "k.workers"], "entries_for(area) in data order")
	kit.eq(_ids(ex.entries_for("L_M1_Archive")), ["b.shelf", "b.mouse"], "entries_for(level)")
	kit.eq(_ids(ex.entries_for("", "easter_egg")), ["k.snowman", "b.mouse"], "entries_for kind filter")
	kit.eq(ex.counts(), {"found": 0, "total": 6}, "nothing found yet")
	var r: Dictionary = ex.find("k.cat")
	kit.eq(r, {"ok": true, "new": true, "entry": ex.entry("k.cat"), "cards_new": ["hist.s.one"]}, "find result shape")
	kit.eq(str(r["entry"].get("area", "")), "karsk", "entry carries its area")
	ex.find("b.shelf")
	kit.eq(ex.counts("karsk"), {"found": 1, "total": 4}, "counts(area)")
	kit.eq(ex.counts("L_A1_Railyard"), {"found": 1, "total": 4}, "counts(level)")
	kit.eq(ex.counts("berlin"), {"found": 1, "total": 2}, "counts(other area)")
	kit.eq(ex.counts(""), {"found": 2, "total": 6}, "counts(all)")
	kit.eq(ex.counts("karsk", "secret"), {"found": 0, "total": 1}, "counts(area, kind)")
	kit.eq(ex.counts("nowhere"), {"found": 0, "total": 0}, "counts(unknown area)")
	kit.eq(ex.area_counts(), {"karsk": {"found": 1, "total": 4}, "berlin": {"found": 1, "total": 2}}, "area_counts")
	kit.eq(ex.history_counts(), {"found": 2, "total": 4}, "history_counts")
	kit.eq(ex.history_counts("soviet"), {"found": 1, "total": 3}, "history_counts(soviet)")
	kit.eq(ex.history_counts("reich"), {"found": 1, "total": 1}, "history_counts(reich)")
	kit.eq(ex.progress(), {"found": 2, "total": 6, "cards_found": 2, "cards_total": 4}, "progress")
	kit.eq(_ids(ex.found_entries("karsk")), ["k.cat"], "found_entries(area)")
	kit.eq(_ids(ex.cards_list("soviet")), ["hist.s.one", "hist.s.two", "hist.s.three"], "cards_list(side) in data order")
	kit.eq(_ids(ex.found_cards()), ["hist.s.one", "hist.r.one"], "found_cards in data order")
	kit.eq(ex.cards_of("k.stash"), ["hist.s.one", "hist.s.two"], "cards_of")
	kit.ok(ex.is_found("k.cat") and not ex.is_found("k.stash"), "is_found")
	kit.ok(ex.is_card_found("hist.s.one") and not ex.is_card_found("hist.s.two"), "is_card_found")
	kit.eq(str(ex.card("hist.r.one").get("side", "")), "reich", "card side defaults to the file side")
	kit.eq(ex.entry_image("k.stash"), "res://assets/ui/portrait_placeholder.png", "entry_image (no _hist variant)")
	kit.eq(ex.entry_image("k.cat"), "", "entry_image empty without image")
	return true


func _cards_once() -> bool:
	var ex := _loaded()
	kit.eq(ex.find("k.cat")["cards_new"], ["hist.s.one"], "first find unlocks its card")
	kit.eq(ex.find("k.stash")["cards_new"], ["hist.s.two"], "a card linked twice unlocks only once")
	var again: Dictionary = ex.find("k.stash")
	kit.eq([again["ok"], again["new"], again["cards_new"]], [true, false, []], "re-finding is idempotent")
	kit.eq(ex.find("k.workers")["cards_new"], ["hist.s.three"], "chat entries unlock cards too")
	kit.eq(ex.history_counts("soviet"), {"found": 3, "total": 3}, "all soviet cards found")
	return true


func _signals() -> bool:
	var ex := _loaded()
	var log: Array = []
	ex.found.connect(func(id): log.append("found:" + id))
	ex.history_unlocked.connect(func(c): log.append("card:" + c))
	ex.state_changed.connect(func(): log.append("changed"))
	ex.find("k.stash")
	kit.eq(log, ["found:k.stash", "card:hist.s.one", "card:hist.s.two", "changed"], "signals of a new find")
	log.clear()
	ex.find("k.stash")
	kit.eq(log, [], "no signals when nothing changed")
	ex.find("k.cat")
	kit.eq(log, ["found:k.cat", "changed"], "card already known: no history_unlocked")
	log.clear()
	ex.restore(ex.state())
	kit.eq(log, ["changed"], "restore emits state_changed once and no found/history signals")
	log.clear()
	ex.reset()
	kit.eq(log, ["changed"], "reset emits state_changed")
	return true


func _unknown_ids() -> bool:
	var ex := _loaded()
	kit.eq(ex.find("nope"), {"ok": false, "new": false, "entry": {}, "cards_new": []}, "find(unknown)")
	kit.ok(not ex.is_found("nope"), "unknown id is not found")
	kit.eq(ex.entry("nope"), {}, "entry(unknown)")
	kit.eq(ex.card("nope"), {}, "card(unknown)")
	kit.eq(ex.cards_of("nope"), [], "cards_of(unknown)")
	kit.eq(ex.chat_lines("nope"), [], "chat_lines(unknown)")
	kit.eq(ex.prompt_for("nope"), "", "prompt_for(unknown)")
	ex.restore({"found": ["k.cat", "gone.entry"], "cards": ["hist.s.one", "gone.card"]})
	kit.eq(ex.counts(), {"found": 1, "total": 6}, "unknown saved entry ids never count")
	kit.eq(ex.history_counts(), {"found": 1, "total": 4}, "unknown saved card ids never count")
	kit.eq(ex.state(), {"found": ["k.cat", "gone.entry"], "cards": ["hist.s.one", "gone.card"]},
		"unknown ids are kept in the save (data may come back)")
	return true


func _round_trip() -> bool:
	var a := _loaded()
	a.find("k.workers")
	a.find("b.shelf")
	a.find("k.cat")
	var st: Dictionary = a.state()
	kit.eq(st, {"found": ["k.workers", "b.shelf", "k.cat"], "cards": ["hist.s.three", "hist.r.one", "hist.s.one"]},
		"state() lists ids in find order")
	# exactly what the save system does with Game.save_extra()
	var raw := JSON.stringify({"extra": {"explore": st}})
	var parsed = JSON.parse_string(raw)
	var b := _loaded()
	b.restore(parsed["extra"]["explore"])
	kit.eq(b.state(), st, "state survives JSON")
	for id in ["k.cat", "k.stash", "k.snowman", "k.workers", "b.shelf", "b.mouse"]:
		kit.eq(b.is_found(id), a.is_found(id), "is_found(%s) after load" % id)
	kit.eq(b.counts(), a.counts(), "counts after load")
	kit.eq(b.history_counts(), a.history_counts(), "history counts after load")
	kit.eq(b.find("k.cat")["cards_new"], [], "a loaded card never unlocks again")
	kit.eq(b.find("k.stash")["cards_new"], ["hist.s.two"], "only the genuinely new card after load")
	return true


func _restore_edge() -> bool:
	var ex := _loaded()
	var unlocked: Array = []
	ex.history_unlocked.connect(func(c): unlocked.append(c))
	ex.restore({"found": ["k.stash"], "cards": []})
	kit.ok(ex.is_card_found("hist.s.one") and ex.is_card_found("hist.s.two"), "cards of found entries are re-attached")
	kit.eq(unlocked, [], "re-attaching is silent (no history_unlocked)")
	for bad in [null, "x", 3, {"found": "k.cat"}, {"found": [1, null, {"a": 1}]}, {"cards": "x"}]:
		ex.restore(bad)
		kit.eq(ex.state(), {"found": [], "cards": []}, "garbage restore -> empty state (%s)" % [bad])
	ex.find("k.cat")
	ex.reset()
	kit.eq(ex.progress(), {"found": 0, "total": 6, "cards_found": 0, "cards_total": 4}, "reset clears progress, keeps data")
	return true


func _clean_validates() -> bool:
	var ex := _loaded()
	kit.eq(ex.warnings, [], "valid data has no warnings")
	return true


func _broken_warnings() -> bool:
	var ex := _new()
	ex.load_data({"area": "x", "entries": [
		{"id": "x.dup", "kind": "detail", "level": "L", "title_key": "ui.journal.title", "text_key": "ui.journal.view"},
		{"id": "x.kind", "kind": "treasure", "level": "L", "title_key": "ui.journal.title", "text_key": "ui.journal.view"},
		{"id": "x.nolevel", "kind": "detail", "title_key": "ui.journal.title", "text_key": "ui.journal.view"},
		{"id": "x.notitle", "kind": "detail", "level": "L", "text_key": "ui.journal.view"},
		{"id": "x.loc", "kind": "detail", "level": "L", "title_key": "explore.test.no_such_key", "text_key": "ui.journal.view"},
		{"id": "x.hist", "kind": "detail", "level": "L", "title_key": "ui.journal.title", "text_key": "ui.journal.view",
			"history": ["hist.missing"]},
		{"id": "x.img", "kind": "detail", "level": "L", "title_key": "ui.journal.title", "text_key": "ui.journal.view",
			"image": "res://assets/explore/test/does_not_exist.png"},
		{"id": "x.chat", "kind": "chat", "level": "L", "title_key": "ui.journal.title"},
		{"kind": "detail"},
	]}, "a.json")
	ex.load_data({"area": "y", "entries": [
		{"id": "x.dup", "kind": "detail", "level": "L", "title_key": "ui.journal.title", "text_key": "ui.journal.view"}]}, "b.json")
	ex.load_data({"side": "elsewhere", "cards": [{"id": "hist.bad", "title_key": "ui.journal.title"}]}, "h.json")
	ex.load_data("not a dictionary", "c.json")
	var all := "\n".join(ex.warnings)
	for frag in ["duplicate entry id 'x.dup' in b.json (first defined in a.json",
			"entry 'x.kind' (a.json): unknown kind 'treasure'",
			"entry 'x.nolevel' (a.json): missing 'level'",
			"entry 'x.notitle' (a.json): missing 'title_key'",
			"title_key 'explore.test.no_such_key' has no text",
			"history card 'hist.missing' does not exist",
			"image 'res://assets/explore/test/does_not_exist.png' not found",
			"entry 'x.chat' (a.json): chat without 'lines'",
			"a.json: entry without id skipped",
			"card 'hist.bad' (h.json): unknown side 'elsewhere'",
			"card 'hist.bad' (h.json): missing 'text_key'",
			"card 'hist.bad' (h.json): missing 'year'",
			"card 'hist.bad' (h.json): needs at least one source",
			"card 'hist.bad' (h.json): not linked by any entry",
			"c.json: top level must be an object"]:
		kit.ok(all.contains(frag), "warning reported: " + frag)
	kit.eq(str(ex.entry("x.dup").get("area", "")), "x", "first definition of a duplicate id wins")
	return true


func _reload_dir() -> bool:
	var abs_dir := ProjectSettings.globalize_path(TMP_DIR)
	DirAccess.make_dir_recursive_absolute(abs_dir)
	var files := {"b_area.json": JSON.stringify(area_berlin()), "a_hist.json": JSON.stringify(hist("reich", ["hist.r.one"])),
		"c_broken.json": "{\"area\": \"z\", \"entries\": [ ", "notes.txt": "ignored"}
	for f in files:
		var fa := FileAccess.open(TMP_DIR + f, FileAccess.WRITE)
		fa.store_string(files[f])
		fa.close()
	var ex := _new()
	ex.reload(TMP_DIR)
	kit.eq(_ids(ex.entries_for()), ["b.shelf", "b.mouse"], "entries read from the directory")
	kit.eq(_ids(ex.cards_list()), ["hist.r.one"], "cards read from the directory")
	kit.ok("\n".join(ex.warnings).contains("c_broken.json: invalid JSON"), "invalid JSON is reported with its file name")
	ex.find("b.shelf")
	ex.reload(TMP_DIR)
	kit.ok(ex.is_found("b.shelf"), "reloading data keeps the progress")
	for f in files:
		DirAccess.remove_absolute(abs_dir.path_join(f))
	DirAccess.remove_absolute(abs_dir)
	return true


func _prompt_chat() -> bool:
	var ex := _loaded()
	var loc := Engine.get_main_loop().root.get_node_or_null("Loc") as Node
	kit.ok(loc != null, "Loc autoload present")
	if loc != null:
		kit.eq(ex.prompt_for("k.cat"), str(loc.t("ui.prompt.discover")), "prompt_for uses the entry's prompt_key")
	kit.eq(ex.prompt_for("k.stash"), "", "no prompt_key -> empty (interactable uses the kind default)")
	var lines: Array = ex.chat_lines("k.workers")
	kit.eq(lines.size(), 2, "chat_lines")
	kit.eq(str(lines[0].get("speaker", "")), "worker_a", "chat line speaker")
	kit.eq(ex.chat_lines("k.cat"), [], "no lines for a detail")
	return true
