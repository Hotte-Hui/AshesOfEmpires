extends RefCounted
## Evidence board „Die Akte C-17“ (round 9, owner: board; TECHNICAL_ARCHITECTURE §12.12): data/board/c17_links.json and
## c17_board.json against data/v3 (every thread item, place scene, look, milestone condition is real; captions and
## texts exist in de_board.json in house style), threads only ever between owned items on every stage of the
## canonical route, the running summary per stage and per decision, the memory cut-off (only what lies at or before
## the remembered scene), every board pair of C4_DESIGN.md §10 on a thread of its own, spatial navigation (pure and on
## a real board), the board never changes Story state, sizes at 100/125/150 % text (no overlapping cards, labels fit
## their cards, every region inside 1920x1080; the detail strip shows every whole name and decision note, the sheet
## opens on its newest lines with a whole first line), high contrast, the journal tab „Akte“ (the seven index tabs
## keep their size, cover page, „Pinnwand öffnen“) and the art.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const BOARD_SCRIPT := "res://scripts/ui/evidence_board.gd"
const BOARD_SCENE := "res://scenes/ui/EvidenceBoard.tscn"
const JOURNAL_SCENE := "res://scenes/ui/Journal.tscn"
const THEME := "res://assets/ui/theme.tres"
const LOCALE := "res://data/locale/de_board.json"
const LINKS := "res://data/board/c17_links.json"
const BOARD := "res://data/board/c17_board.json"
const COND_KEYS := ["items", "any_items", "objectives", "events"]
## The board pairs of documentation/C4_DESIGN.md §10 („pairs that belong together on the board“; a chain a ↔ b ↔ c
## names the pairs a–b and b–c).
const C4_PAIRS := [["ev_c4_card_de", "ev_c4_card_ru"], ["ev_c4_stencils", "ev_c4_card_de"],
	["ev_c4_cut_signatures", "ev_c3_intake_book"], ["ev_c3_intake_book", "ev_timetable"],
	["ev_c4_carbon", "ev_c4_cut_signatures"], ["ev_c4_notice", "ev_c4_annex_plan"],
	["ev_c4_annex_plan", "ev_c3_kordon_plan"], ["ev_c4_route_board", "ev_c4_shaft"],
	["ev_c4_card_de", "ev_c3_escort_list"], ["ev_c4_tube_slip", "ev_c4_drawer_s8"]]


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"text_scale": 1.0, "high_contrast": false, "reduced_motion": true}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockAudio extends Node:
	var played: Array = []

	func ui(id) -> void:
		played.append(str(id))


class FakeGame extends Node:
	var memory_mode := false
	var memory_scene := ""

	func memory_info() -> Dictionary:
		return {"scene": memory_scene, "place": "Bahnhof Veltrava", "date": "Februar 1964"} if memory_mode else {}


var kit: TKit
var B: Script
var _saved := {}
var _settings: MockSettings


func run() -> Array:
	kit = TKit.new()
	B = load(BOARD_SCRIPT)
	_saved = UIKit.overrides.duplicate()
	_settings = MockSettings.new()
	kit.track(_settings)
	var audio := MockAudio.new()
	kit.track(audio)
	UIKit.overrides = {"Settings": _settings, "Audio": audio}
	kit.run_case("data_links_point_to_real_items", _links_data)
	kit.run_case("board_data_places_looks_milestones", _board_data)
	kit.run_case("locale_texts_in_house_style", _locale)
	kit.run_case("threads_only_between_owned_items", _threads_owned)
	kit.run_case("thread_skips_an_unowned_middle_item", _thread_skip)
	kit.run_case("summary_milestones_per_stage_and_decision", _summary)
	kit.run_case("places_known_and_compact_unknown", _places)
	kit.run_case("chapter4_file_and_decision", _chapter4)
	kit.run_case("memory_shows_the_file_as_it_was", _memory)
	kit.run_case("neighbor_is_spatial", _neighbor_pure)
	kit.run_case("board_navigation_and_inspect_are_read_only", _navigation)
	kit.run_case("sizes_at_100_125_150_percent", _sizes)
	kit.run_case("detail_strip_shows_whole_name_and_note", _strip_whole)
	kit.run_case("summary_sheet_first_line_whole", _sheet_whole)
	kit.run_case("high_contrast_rebuild", _contrast)
	kit.run_case("new_cards_since_the_last_opening", _new_cards)
	kit.run_case("journal_tab_akte", _journal)
	kit.run_case("art_and_manifest", _art)
	UIKit.overrides = _saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _json(path: String) -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	return d if d is Dictionary else {}


func _items() -> Dictionary:
	var out := {}
	for it in _json("res://data/v3/items.json").get("items", []):
		out[str(it["id"])] = it
	return out


func _objectives() -> Dictionary:
	var out := {}
	for q in _json("res://data/v3/quests.json").get("quests", []):
		for o in q.get("objectives", []):
			out[str(o["id"])] = o
	return out


func _events() -> Dictionary:
	var out := {}
	for q in _json("res://data/v3/quests.json").get("quests", []):
		if q.get("completion_event") != null:
			out[str(q["completion_event"])] = true
	for s in _json("res://data/v3/scenes.json").get("scenes", []):
		if s.get("exit_on_event") != null:
			out[str(s["exit_on_event"])] = true
	return out


func _loc() -> Node:
	var l: Node = kit.track(load("res://scripts/story/loc.gd").new())
	l.reload()
	return l


## Checks a "when" dictionary against data/v3; returns problems.
func _cond_problems(when, what: String) -> Array:
	var out: Array = []
	if when == null:
		return out
	if not (when is Dictionary):
		return ["%s: when is not a dictionary" % what]
	var items := _items()
	var objs := _objectives()
	var evs := _events()
	for k in when:
		var key := str(k)
		if key in COND_KEYS:
			if not (when[k] is Array) or (when[k] as Array).is_empty():
				out.append("%s: %s must be a non-empty list" % [what, key])
				continue
			for id in when[k]:
				var ok: bool = items.has(str(id)) if key in ["items", "any_items"] else (objs.has(str(id)) if key == "objectives" else evs.has(str(id)))
				if not ok:
					out.append("%s: unknown %s id %s" % [what, key, id])
		elif key.begins_with("choice."):
			var obj := key.substr(7)
			var want := str(when[k]).trim_prefix("!")
			var ids: Array = []
			for c in objs.get(obj, {}).get("choices", []):
				ids.append(str(c.get("id", "")))
			if not objs.has(obj) or str(objs[obj].get("type", "")) != "choice":
				out.append("%s: %s is not a choice objective" % [what, obj])
			elif not (want in ids):
				out.append("%s: %s has no option %s" % [what, obj, want])
		else:
			out.append("%s: unknown condition key %s" % [what, key])
	return out


func _story_at(stage: String, choices := {}) -> Node:
	var g := kit.story()
	kit.play_until(g, stage, choices)
	return g


func _model(g: Node, mem := "") -> Dictionary:
	var ctx: Dictionary = B.data_context()
	return B.build_model(B.snapshot(g, mem, ctx), ctx)


func _ids(list: Array) -> Array:
	var out: Array = []
	for e in list:
		out.append(str(e["id"]))
	return out


static func _pair(a: String, b: String) -> String:
	return (a + "|" + b) if a < b else (b + "|" + a)


## Lays a board subtree out as the frame would (forced container sorting; wrapped labels re-break at the width just
## assigned), a few passes so scroll ranges and the sheet's margin settle.
static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label:
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


func _lay_out(board: Control, part: Control) -> void:
	for _pass in 5:
		board._apply_regions()
		_sort(part)


func _make_board(g: Node) -> Control:
	B.reset_seen()
	var holder := Control.new()
	holder.theme = UIKit.theme(UIKit.high_contrast())
	holder.size = Vector2(1920, 1080)
	kit.mount(holder)
	var board: Control = load(BOARD_SCENE).instantiate()
	holder.add_child(board)
	board.open({"story": g})
	return board


# ------------------------------------------------------------------ data
func _links_data() -> bool:
	var d := _json(LINKS)
	var items := _items()
	var loc := _loc()
	var groups: Array = d.get("groups", [])
	kit.ok(groups.size() >= 15, "at least 15 thread groups (%d)" % groups.size())
	var ids := {}
	var pairs := {}
	for g in groups:
		var gid := str(g.get("id", ""))
		kit.ok(gid != "" and not ids.has(gid), "group id '%s' set and unique" % gid)
		ids[gid] = true
		var list: Array = g.get("items", [])
		kit.ok(list.size() >= 2, "group %s links at least two items" % gid)
		var seen := {}
		for id in list:
			kit.ok(items.has(str(id)), "group %s: item %s exists in data/v3/items.json" % [gid, id])
			kit.ok(not seen.has(str(id)), "group %s: item %s listed once" % [gid, id])
			seen[str(id)] = true
		for i in range(list.size() - 1):
			var a := str(list[i])
			var b := str(list[i + 1])
			var key := (a + "|" + b) if a < b else (b + "|" + a)
			kit.ok(not pairs.has(key), "pair %s is drawn by one group only (also %s)" % [key, pairs.get(key, "")])
			pairs[key] = gid
		var ck := str(g.get("caption_key", ""))
		kit.ok(loc.has(ck) and loc.source_of(ck).ends_with("de_board.json"), "group %s caption '%s' in de_board.json" % [gid, ck])
		for p in _cond_problems(g.get("when"), "group " + gid):
			kit.fail(p)
	# every evidence item of Chapters 1-4 hangs on at least one thread (no orphan card on a full board)
	var linked := {}
	for g in groups:
		for id in g.get("items", []):
			linked[str(id)] = true
	for id in items:
		kit.ok(linked.has(id), "item %s has at least one thread" % id)
	return true


func _board_data() -> bool:
	var d := _json(BOARD)
	var loc := _loc()
	var items := _items()
	var scenes := {}
	for s in _json("res://data/v3/scenes.json").get("scenes", []):
		scenes[str(s["id"])] = s
	var in_place := {}
	for p in d.get("places", []):
		var pid := str(p.get("id", ""))
		kit.ok(loc.has(str(p.get("title_key", ""))), "place %s has a title" % pid)
		for s in p.get("scenes", []):
			kit.ok(scenes.has(str(s)), "place %s: scene %s exists" % [pid, s])
			kit.ok(not in_place.has(str(s)), "scene %s belongs to one place" % s)
			in_place[str(s)] = pid
	for id in items:
		var sc := str(items[id].get("scene", ""))
		kit.ok(in_place.has(sc), "item %s: its scene %s is on the board's place list" % [id, sc])
		kit.ok((d.get("spots", {}) as Dictionary).has(sc), "scene %s has a spot line" % sc)
		kit.ok(loc.has("board.short." + id), "item %s has a short card title" % id)
	for sc in d.get("spots", {}):
		kit.ok(scenes.has(str(sc)) and loc.has(str(d["spots"][sc])), "spot %s: scene and text exist" % sc)
	for lk in d.get("looks", []):
		kit.ok(items.has(str(lk.get("item", ""))), "look for a real item %s" % lk.get("item", ""))
		kit.ok(str(lk.get("note_key", "")) == "" or loc.has(str(lk["note_key"])), "look note %s exists" % lk.get("note_key", ""))
		kit.ok(str(lk.get("look", "")) in ["", "burned"], "look kind %s is drawn" % lk.get("look", ""))
		for p in _cond_problems(lk.get("when"), "look " + str(lk.get("item", ""))):
			kit.fail(p)
	var mids := {}
	for m in d.get("summary", []):
		var mid := str(m.get("id", ""))
		kit.ok(mid != "" and not mids.has(mid), "milestone id '%s' unique" % mid)
		mids[mid] = true
		kit.ok(loc.has(str(m.get("text_key", ""))), "milestone %s text exists" % mid)
		kit.ok(m.get("when") is Dictionary and not (m["when"] as Dictionary).is_empty(), "milestone %s has a condition" % mid)
		for p in _cond_problems(m.get("when"), "milestone " + mid):
			kit.fail(p)
	return true


func _locale() -> bool:
	var lf := _json(LOCALE)
	kit.eq(str(lf.get("locale", "")), "de-DE", "locale tag")
	var strings: Dictionary = lf.get("strings", {})
	var code := FileAccess.get_file_as_string(BOARD_SCRIPT) + FileAccess.get_file_as_string("res://scripts/ui/journal.gd")
	var data := FileAccess.get_file_as_string(LINKS) + FileAccess.get_file_as_string(BOARD)
	var renamed := "Matt" + "hias"
	for k in strings:
		var key := str(k)
		var s := str(strings[k])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' not empty, no stray spaces" % key)
		kit.ok(not s.contains("\""), "'%s': German quotes („…“), not \"…\"" % key)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % key)
		kit.ok(not s.contains("..."), "'%s': ellipsis as '…'" % key)
		kit.ok(not s.contains(renamed), "'%s': the protagonist is Konrad" % key)
		var used: bool = code.contains("\"%s\"" % key) or data.contains("\"%s\"" % key) or key.begins_with("board.short.") \
			or key.begins_with("board.initials.") or key == "ui.journal.tab.board"
		kit.ok(used, "'%s' is used" % key)
		if key.begins_with("board.short."):
			kit.ok(s.length() <= 22, "short title '%s' at most 22 characters" % s)
		elif key.begins_with("board.link."):
			kit.ok(s.length() <= 48, "caption '%s' at most 48 characters" % s)
		elif key.begins_with("board.sum."):
			kit.ok(s.length() <= 210, "milestone '%s' at most 210 characters (%d)" % [key, s.length()])
	return true


# ------------------------------------------------------------------ model
func _threads_owned() -> bool:
	for stage in TKit.STAGES:
		var g := _story_at(stage)
		var m := _model(g)
		var owned := {}
		for id in g.inventory():
			owned[str(id)] = true
		for t in m["threads"]:
			kit.ok(owned.has(t["a"]) and owned.has(t["b"]), "%s: thread %s joins owned items (%s – %s)" % [stage, t["group"], t["a"], t["b"]])
		kit.eq(int(m["owned"]), owned.size(), "%s: owned counter" % stage)
	var fresh := kit.story()
	kit.eq((_model(fresh)["threads"] as Array).size(), 0, "a new game has no thread")
	var full := _model(_story_at("c3g"))
	kit.ok((full["threads"] as Array).size() >= 24, "the full Chapter-3 file has its threads (%d)" % (full["threads"] as Array).size())
	return true


## A fake Story with exactly the given items: the chain of a group runs through owned items only.
class ItemsStory extends Node:
	var items: Array = []
	var current_scene := "L_C3_Quay"

	func inventory() -> Array:
		return items

	func completed_objectives() -> Array:
		return []

	func has_event(_e) -> bool:
		return false

	func choice_history() -> Dictionary:
		return {}


func _thread_skip() -> bool:
	var s := ItemsStory.new()
	kit.track(s)
	s.items = ["ev_damaged_seal", "ev_emil_note"]
	var m := _model(s)
	var found := false
	for t in m["threads"]:
		if t["group"] == "mark_c17":
			found = (t["a"] == "ev_damaged_seal" and t["b"] == "ev_emil_note")
	kit.ok(found, "mark_c17 joins the seal and Emil's note across the missing ledger and draft")
	kit.eq((m["threads"] as Array).size(), 1, "and nothing else")
	s.items = ["ev_c3_halves", "ev_c3_intake_book"]
	kit.eq((_model(s)["threads"] as Array).size(), 0, "the Gegenprobe thread waits for the solved check (when)")
	return true


func _summary() -> bool:
	kit.eq(_model(kit.story())["summary"], [], "a new game: nothing in the file yet")
	var after := {
		"a1": ["karsk_wagons", "karsk_mark"],
		"m1": ["karsk_wagons", "karsk_mark", "berlin_corridor", "berlin_series"],
		"c3a": ["karsk_wagons", "karsk_mark", "berlin_corridor", "berlin_series", "veltrava_wagon", "veltrava_train"],
	}
	for stage in after:
		kit.eq(_ids(_model(_story_at(stage))["summary"]), after[stage], "summary after %s" % stage)
	var admit := _ids(_model(_story_at("c3d", {"c3d": "admit_plan"}))["summary"])
	var pocket := _ids(_model(_story_at("c3d", {"c3d": "pocket_plan"}))["summary"])
	kit.ok("sheet_admit" in admit and not ("sheet_pocket" in admit), "admit_plan: Blatt 7 burned on the wall")
	kit.ok("sheet_pocket" in pocket and not ("sheet_admit" in pocket), "pocket_plan: Blatt 7 in Konrad's pocket")
	kit.ok("cross_check" in admit and "partners" in admit, "the joint check and the partners are in the file after c3d")
	for opt in ["split_by_language", "swap_halves", "hide_for_elena"]:
		var ids := _ids(_model(_story_at("c3g", {"c3g": opt}))["summary"])
		var halves: Array = ids.filter(func(x): return str(x).begins_with("halves_"))
		kit.eq(halves.size(), 1, "%s: exactly one line about the halves" % opt)
		kit.ok("open_questions" in ids and "pjotr" in ids, "%s: Pjotr and the open questions" % opt)
	# the decision also changes the card of Blatt 7 (look + note) — never the Story state
	var m := _model(_story_at("c3d", {"c3d": "admit_plan"}))
	var slot := {}
	for g in m["places"]:
		for s in g["slots"]:
			if s["item"] == "ev_c3_kordon_plan":
				slot = s
	kit.eq(str(slot.get("look", "")), "burned", "admit_plan: the card of Blatt 7 is scorched")
	kit.eq(str(slot.get("note_key", "")), "board.note.kordon_burned", "with its note")
	return true


func _places() -> bool:
	var g := _story_at("a1")
	var m := _model(g)
	var known: Array = []
	var unknown := 0
	for p in m["places"]:
		if p["known"]:
			known.append(p["id"])
		else:
			unknown += 1
			kit.eq(str(p["id"]), "unknown", "all places ahead share one compact „?“ column")
	# after the Karsk decision the story stands in Berlin: Karsk and Berlin are reached
	kit.eq(known, ["karsk", "berlin"], "after A1: Karsk and Berlin (the story's current scene) are known")
	kit.eq(unknown, 1, "one column for everything ahead")
	var fresh := _model(kit.story())
	kit.eq(str(fresh["places"][0]["id"]), "karsk", "a new game stands in Karsk")
	kit.ok(fresh["places"][0]["known"], "Karsk known from the start (its pins are „?“ until found)")
	for s in fresh["places"][0]["slots"]:
		kit.eq(s["owned"], false, "nothing owned in a new game: %s" % s["item"])
	var q := _model(_story_at("c3f"))
	for p in q["places"]:
		if p["id"] == "veltrava":
			kit.eq(p["finders"], ["alexei", "konrad"], "Veltrava was searched by both")
	return true


## Chapter 4 part 1 (documentation/C4_DESIGN.md §2.3) through the public Story API; puzzle answers from data/v3.
func _play_c4(g: Node, c4d: String) -> void:
	var sol := {}
	for p in _json("res://data/v3/puzzles.json").get("puzzles", []):
		sol[str(p["id"])] = _ints(p.get("solution"))
	kit.step(g.inspect("c4a_inspect_shelf"), "shelf")
	kit.play_dialogue(g, "c4a_talk_lev")
	kit.step(g.inspect("c4a_inspect_book"), "book")
	kit.step(g.inspect("c4a_inspect_carbon"), "carbon")
	kit.play_dialogue(g, "c4a_talk_tunnel")
	kit.step(g.inspect("c4a_open_door"), "door")
	kit.step(g.inspect("c4b_inspect_notice"), "notice")
	kit.play_dialogue(g, "c4b_talk_marta")
	kit.step(g.solve_puzzle("c4b_solve_routes", sol.get("pz_c4_routes")), "routes")
	kit.step(g.inspect("c4b_inspect_column"), "column")
	kit.play_dialogue(g, "c4b_talk_ilse")
	kit.step(g.inspect("c4b_inspect_crates"), "crates")
	kit.step(g.inspect("c4c_inspect_card"), "card")
	kit.step(g.inspect("c4c_inspect_stencils"), "stencils")
	kit.step(g.solve_puzzle("c4c_solve_numbers", sol.get("pz_c4_numbers")), "numbers")
	kit.step(g.inspect("c4c_inspect_wagon"), "wagon")
	kit.play_dialogue(g, "c4c_talk_lev")
	kit.step(g.inspect("c4d_inspect_drawer"), "drawer")
	kit.step(g.inspect("c4d_inspect_plan"), "plan")
	kit.step(g.inspect("c4d_inspect_tube"), "tube")
	kit.play_dialogue(g, "c4d_talk_registrar")
	kit.step(g.choose("c4d_choose", c4d), "c4d choice")


## JSON numbers arrive as floats; the engine wants the overlay answer in integers.
static func _ints(v):
	if v is Dictionary:
		var d := {}
		for k in v:
			d[k] = _ints(v[k])
		return d
	if v is Array:
		var a: Array = []
		for x in v:
			a.append(_ints(x))
		return a
	if v is float and is_equal_approx(v, roundf(v)):
		return int(v)
	return v


func _chapter4() -> bool:
	if not _objectives().has("c4d_choose"):
		kit.fail("Chapter 4 data missing (C4_DESIGN.md)")
		return true
	for c4d in ["name_marta", "protect_marta"]:
		var g := _story_at("c3g")
		_play_c4(g, c4d)
		var m := _model(g)
		kit.eq(int(m["owned"]), int(m["total"]), "%s: every item of Chapters 1-4 is in the file" % c4d)
		for t in m["threads"]:
			kit.ok(g.has_item(str(t["a"])) and g.has_item(str(t["b"])), "%s: thread %s joins owned items" % [c4d, t["group"]])
		var groups := {}
		var joined := {}
		for t in m["threads"]:
			groups[str(t["group"])] = true
			joined[_pair(str(t["a"]), str(t["b"]))] = str(t["group"])
		for gid in ["card_0417", "signed_ka", "wagon_45", "children", "next_tuesday", "january", "detours", "households"]:
			kit.ok(groups.has(gid), "%s: the thread %s hangs" % [c4d, gid])
		# review r9 compl-13: every pair the contract names gets a thread of its own
		for p in C4_PAIRS:
			kit.ok(joined.has(_pair(p[0], p[1])), "%s: a thread joins %s and %s (C4_DESIGN.md §10)" % [c4d, p[0], p[1]])
		var ids := _ids(m["summary"])
		kit.ok("c4_anna" in ids and "c4_card_whole" in ids and "c4_tuesday" in ids, "%s: Anna's card and the open Tuesday" % c4d)
		kit.ok(("c4_named" in ids) == (c4d == "name_marta") and ("c4_protected" in ids) == (c4d == "protect_marta"), "%s: one line about Marta's name" % c4d)
		var known: Array = []
		for p in m["places"]:
			if p["known"]:
				known.append(p["id"])
		kit.eq(known, ["karsk", "berlin", "veltrava", "karsk_c4", "berlin_c4"], "%s: five places on the board" % c4d)
	return true


func _memory() -> bool:
	var g := _story_at("c3d", {"c3d": "pocket_plan"})
	var ctx: Dictionary = B.data_context()
	var st: Dictionary = B.snapshot(g, "L_C3_Station", ctx)
	var m: Dictionary = B.build_model(st, ctx)
	kit.eq(int(m["owned"]), 9, "a memory of the station: Karsk 3 + Berlin 3 + station 3")
	for t in m["threads"]:
		for id in [t["a"], t["b"]]:
			kit.ok(B.item_scene(ctx, str(id)) in ["L_A1_Railyard", "L_M1_Archive", "L_C3_Station"], "memory thread item %s lies before the station" % id)
	var ids := _ids(m["summary"])
	kit.ok(not ("sheet_pocket" in ids) and not ("cross_check" in ids), "decisions and checks after the station do not count")
	kit.ok("veltrava_wagon" in ids, "the station's own milestone counts")
	for p in m["places"]:
		if p["id"] == "veltrava":
			kit.ok(p["known"], "Veltrava is reached in the memory")
			for s in p["slots"]:
				if s["scene"] != "L_C3_Station":
					kit.eq(s["owned"], false, "%s is not in the remembered file" % s["item"])
	kit.eq(str(m["memory_scene"]), "L_C3_Station", "the model knows its memory")
	# Game's running memory is picked up by live_model()
	var game := FakeGame.new()
	kit.track(game)
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	UIKit.overrides["Game"] = game
	UIKit.overrides["Story"] = g
	var lm: Dictionary = B.live_model()
	kit.eq(int(lm["owned"]), 3, "Game.memory_mode: the file of the Karsk memory")
	kit.eq(str(lm["memory_scene"]), "L_A1_Railyard", "memory scene from Game")
	var board := _make_board(g)
	board.open({"story": g, "memory_scene": "L_A1_Railyard"})
	kit.ok(board._note_stamp.visible and board._note_stamp.text.contains("BAHNHOF VELTRAVA"), "the sheet carries the memory stamp")
	UIKit.overrides.erase("Game")
	UIKit.overrides.erase("Story")
	return true


# ------------------------------------------------------------------ navigation
func _neighbor_pure() -> bool:
	var c: Array = []
	for r in 3:
		for col in 4:
			c.append(Vector2(col * 200, r * 170))
	kit.eq(B.neighbor(c, 0, Vector2.RIGHT), 1, "right in the row")
	kit.eq(B.neighbor(c, 0, Vector2.DOWN), 4, "down in the column")
	kit.eq(B.neighbor(c, 5, Vector2.LEFT), 4, "left")
	kit.eq(B.neighbor(c, 5, Vector2.UP), 1, "up")
	kit.eq(B.neighbor(c, 3, Vector2.RIGHT), -1, "nothing beyond the edge")
	kit.eq(B.neighbor(c, 0, Vector2.UP), -1, "nothing above the top row")
	var stagger: Array = [Vector2(0, 0), Vector2(200, 300), Vector2(220, 20)]
	kit.eq(B.neighbor(stagger, 0, Vector2.RIGHT), 2, "the card in line wins over a closer one far below")
	return true


func _navigation() -> bool:
	var g := _story_at("c3f")
	var before: String = g.save_json()
	var board := _make_board(g)
	kit.ok(board.is_open, "open")
	board.focus_card(board._first_card())
	kit.eq(board.focused_item, "ev_damaged_seal", "the first card (top left) is the Karsk seal")
	kit.eq(board.move_focus(Vector2.DOWN), "ev_timetable", "down: the timetable")
	kit.eq(board.move_focus(Vector2.RIGHT), "ev_plan_b", "right: the Berlin draft beside it")
	kit.eq(board.move_focus(Vector2.UP), "ev_plan_a", "up: the approved plan")
	kit.eq(board.move_focus(Vector2.UP), "", "nothing above the top row")
	# keys through modal_input (arrows, WASD), enter = inspect
	var ev := InputEventAction.new()
	ev.action = "ui_right"
	ev.pressed = true
	kit.ok(board.modal_input(ev), "ui_right handled")
	kit.eq(board.focused_item, "ev_c3_weighbill", "right: into Veltrava")
	var acc := InputEventAction.new()
	acc.action = "ui_accept"
	acc.pressed = true
	kit.ok(board.modal_input(acc), "accept handled")
	kit.eq(board.last_inspected, "ev_c3_weighbill", "Enter opens the close-up of the focused card")
	# unknown pins are never focusable
	for id in board._cards:
		kit.ok(g.has_item(str(id)), "only owned items are cards: %s" % id)
	kit.ok(not board._cards.has("ev_c3_escort_list"), "the quay list is not found yet: no card")
	kit.ok(board.layout_info["cards"].has("ev_c3_escort_list"), "…but its place is reserved (empty pin)")
	board.inspect("ev_c3_escort_list")
	kit.eq(board.last_inspected, "ev_c3_weighbill", "an unowned item cannot be opened")
	# mouse: hovering focuses, a click opens
	var card: Button = board._cards["ev_c3_scarf"]
	card.mouse_entered.emit()
	kit.eq(board.focused_item, "ev_c3_scarf", "hover focuses")
	card.pressed.emit()
	kit.eq(board.last_inspected, "ev_c3_scarf", "click opens")
	kit.eq(g.save_json(), before, "the board never changed the Story state")
	board.close()
	kit.ok(not board.is_open, "Esc/close")
	return true


# ------------------------------------------------------------------ sizes
func _sizes() -> bool:
	var g := _story_at("c3f")
	for ts in [1.0, 1.25, 1.5]:
		_settings.values["text_scale"] = ts
		var board := _make_board(g)
		UIKit.refresh_text_scale()
		board.rebuild()
		board._apply_regions()
		var rects: Array = []
		for id in board.layout_info["cards"]:
			rects.append(board.layout_info["cards"][id])
		for i in rects.size():
			for j in range(i + 1, rects.size()):
				kit.ok(not (rects[i] as Rect2).intersects(rects[j]), "%d%%: cards %d and %d do not overlap" % [int(ts * 100), i, j])
		var csize: Vector2 = board._canvas.custom_minimum_size
		for r in rects:
			kit.ok(Rect2(Vector2.ZERO, csize).grow(1.0).encloses(r), "%d%%: card inside the cork canvas" % int(ts * 100))
		var f: Font = UIKit.font("fv_serif_italic")
		var fs := int(round(20 * ts))
		for id in board._cards:
			var b: Button = board._cards[id]
			var l: Label = null
			for c in b.get_children():
				if c is Label:
					l = c
			if l == null:
				kit.fail("card %s has a label" % id)
				continue
			var need := f.get_multiline_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, l.size.x, fs).y
			kit.ok(need <= l.size.y + 1.0, "%d%%: label of %s fits its card (%.0f <= %.0f)" % [int(ts * 100), id, need, l.size.y])
			for word in l.text.split(" ", false):
				kit.ok(f.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x <= l.size.x + 1.0, "%d%%: '%s' fits the card width" % [int(ts * 100), word])
		var screen := Rect2(0, 0, 1920, 1080)
		for k in ["head", "counts", "note", "strip", "scroll"]:
			var c: Control = {"head": board._head_plate, "counts": board._count_plate, "note": board._note, "strip": board._strip, "scroll": board._scroll}[k]
			kit.ok(screen.encloses(Rect2(c.position, c.size)), "%d%%: %s inside the screen (%s)" % [int(ts * 100), k, Rect2(c.position, c.size)])
		var note := Rect2(board._note.position, board._note.size)
		var strip := Rect2(board._strip.position, board._strip.size)
		var scroll := Rect2(board._scroll.position, board._scroll.size)
		kit.ok(not note.intersects(strip) and not scroll.intersects(strip) and not note.intersects(scroll), "%d%%: sheet, cork and strip apart" % int(ts * 100))
		kit.ok(board.card_size.x >= 180.0 and int(board.card_size.x) % 3 == 0 and int(board.card_size.y) % 3 == 0, "%d%%: card size on the 3-px grid" % int(ts * 100))
		if ts == 1.0:
			kit.ok(board._canvas.custom_minimum_size.x <= board._scroll.size.x, "100%%: the whole Chapter-3 file fits without panning (%.0f <= %.0f)" % [board._canvas.custom_minimum_size.x, board._scroll.size.x])
			var rows := {}
			for id in board.layout_info["cards"]:
				rows[int((board.layout_info["cards"][id] as Rect2).position.y)] = true
			kit.eq(rows.size(), 4, "100%: Veltrava hangs in four rows")
		board.focus_card("ev_c3_kordon_plan")
		kit.ok(board._d_name.text != "" and board._d_threads.text != "", "%d%%: detail strip filled" % int(ts * 100))
	_settings.values["text_scale"] = 1.0
	UIKit.refresh_text_scale()
	return true


## Review r9 art-10: at 100 / 125 / 150 % the detail strip shows every card's whole name and decision note (a long
## line widens the left column) -- no label of its left column clips or trims, the strip never needs more room than
## its region, which stays clear of the cork, and the file of Chapters 1-4 keeps the base height (the cork its rows).
func _strip_whole() -> bool:
	var files := {"c3g": {"c3d": "admit_plan", "c3g": "split_by_language"}, "c4d": {"c3d": "pocket_plan", "c3g": "hide_for_elena"}}
	var notes := 0
	var widened := 0
	for stage in files:
		var g := _story_at(stage, files[stage])
		for ts in [1.0, 1.25, 1.5]:
			_settings.values["text_scale"] = ts
			var board := _make_board(g)
			UIKit.refresh_text_scale()
			board.rebuild()
			var pct := int(ts * 100)
			var region: Rect2 = board._regions["strip"]
			kit.eq(region.size.y, B._snap(120.0 * pow(ts, 0.75)), "%s %d%%: the strip keeps its base height" % [stage, pct])
			kit.ok(not region.intersects(board._regions["scroll"]), "%s %d%%: strip and cork apart" % [stage, pct])
			var labels := {"kicker": board._d_kicker, "name": board._d_name, "note": board._d_note, "note below": board._d_note_below}
			for k in labels:
				var l: Label = labels[k]
				kit.ok(not l.clip_text and l.text_overrun_behavior == TextServer.OVERRUN_NO_TRIMMING and l.max_lines_visible < 0,
					"%s %d%%: the %s line never trims" % [stage, pct, k])
			var bad: Array = []
			for id in board._cards:
				board.focus_card(id)
				_lay_out(board, board._strip)
				var s: Dictionary = board._slot(id)
				if board._d_name.text != UIKit.t(str(s["name_key"])):
					bad.append("%s: name „%s“" % [id, board._d_name.text])
				var nk := str(s.get("note_key", ""))
				if nk != "":
					notes += 1
					var shown: String = board._d_note.text if board._d_note.visible else board._d_note_below.text
					if not shown.ends_with(UIKit.t(nk)):
						bad.append("%s: note „%s“" % [id, shown])
				var need: float = board._strip.get_combined_minimum_size().y
				if need > region.size.y + 0.5 or board._strip.size != region.size:
					bad.append("%s: the strip needs %.0f of %.0f (%s)" % [id, need, region.size.y, board._strip.size])
				if (board._d_who.get_parent() as Control).get_combined_minimum_size().x > board._d_left.size.x + 0.5:
					bad.append("%s: finder and note are wider than the column" % id)
				if board._d_left.size.x > board._strip_base + 3.5:
					widened += 1
			kit.eq(bad, [], "%s %d%%: every card's name and note show whole in the strip" % [stage, pct])
	kit.ok(notes >= 12, "decision notes were checked (%d)" % notes)
	kit.ok(widened > 0, "a card with a long line widened the left column (%d)" % widened)
	# the empty file of a new game: its one line stands whole where the name would be
	var fresh := kit.story()
	for ts in [1.0, 1.5]:
		_settings.values["text_scale"] = ts
		var board := _make_board(fresh)
		UIKit.refresh_text_scale()
		board.rebuild()
		_lay_out(board, board._strip)
		var region: Rect2 = board._regions["strip"]
		kit.eq(board._d_name.text, UIKit.t("board.summary.empty"), "%d%%: the empty file says so in the strip" % int(ts * 100))
		kit.ok(board._strip.get_combined_minimum_size().y <= region.size.y + 0.5 and board._strip.size == region.size,
			"%d%%: and the strip holds it (%s in %s)" % [int(ts * 100), board._strip.get_combined_minimum_size(), region.size])
	_settings.values["text_scale"] = 1.0
	UIKit.refresh_text_scale()
	return true


## "" when the sheet's view starts just above a line (NOTE_LIFT) and no line above it reaches more than the empty
## pixel row under its ink into the view, else what is cut.
func _sheet_problem(board: Control) -> String:
	var sv := float(board._note_scroll.scroll_vertical)
	var tops: Array = []
	for row in board._note_list.get_children():
		var rc := row as Control
		if rc == null or not rc.visible:
			continue
		var l: Label = rc as Label
		if l == null:
			for c in rc.get_children():
				if c is Label and (c as Label).autowrap_mode != TextServer.AUTOWRAP_OFF:
					l = c
		if l == null:
			continue
		var sb := l.get_theme_stylebox("normal")
		var y: float = rc.position.y + (l.position.y if l != rc else 0.0) + (sb.get_margin(SIDE_TOP) if sb != null else 0.0)
		var ls := float(l.get_theme_constant("line_spacing"))
		for i in l.get_line_count():
			var h := float(l.get_line_height(i))
			if y < sv - 0.5 and y + h > sv + 1.5:
				return "the line %d–%d is cut by the view top at %d" % [int(y), int(y + h), int(sv)]
			tops.append(y)
			y += h + ls
	if sv > 0.5 and not tops.any(func(t): return absf(float(t) - B.NOTE_LIFT - sv) <= 0.5):
		return "the view top %d is not just above a line" % int(sv)
	return ""


## Review r9 art-10: the sheet „Was die Akte bisher zeigt“ opens on its newest lines with its first visible line
## whole (it stops on a line; a margin under the last entry makes that stop reachable); Page Up / Down land on lines.
func _sheet_whole() -> bool:
	var g := _story_at("c4d")
	for ts in [1.0, 1.25, 1.5]:
		_settings.values["text_scale"] = ts
		var board := _make_board(g)
		UIKit.refresh_text_scale()
		board.rebuild()
		_lay_out(board, board._note)
		var pct := int(ts * 100)
		var sc: ScrollContainer = board._note_scroll
		var content: float = board._note_list.get_combined_minimum_size().y
		kit.ok(content > sc.size.y + 40.0, "%d%%: the Chapter-4 sheet is longer than its page (%.0f > %.0f)" % [pct, content, sc.size.y])
		kit.ok(sc.scroll_vertical + sc.size.y >= content - 0.5, "%d%%: it opens on its newest lines (%d + %.0f >= %.0f)" % [pct, sc.scroll_vertical, sc.size.y, content])
		kit.eq(_sheet_problem(board), "", "%d%%: its first visible line is whole" % pct)
		var opened := sc.scroll_vertical
		board.scroll_note(-1.0)
		kit.ok(sc.scroll_vertical < opened, "%d%%: Page Up scrolls back" % pct)
		kit.eq(_sheet_problem(board), "", "%d%%: Page Up lands on a whole line" % pct)
		board.scroll_note(1.0)
		kit.eq(_sheet_problem(board), "", "%d%%: Page Down too" % pct)
		board.scroll_note(1.0)
		kit.eq(sc.scroll_vertical, opened, "%d%%: Page Down ends where the sheet opened" % pct)
		board.close()
	_settings.values["text_scale"] = 1.0
	UIKit.refresh_text_scale()
	return true


func _contrast() -> bool:
	var g := _story_at("c3c")
	_settings.values["high_contrast"] = true
	var board := _make_board(g)
	kit.ok(str(board._cork.texture.resource_path).ends_with("cork_hc.png") or board._cork.texture != null, "dark cork in high contrast")
	var card: Button = board._cards["ev_damaged_seal"]
	var fsb := card.get_theme_stylebox("focus") as StyleBoxTexture
	kit.ok(fsb != null and str(fsb.texture.resource_path).ends_with("focus_hc.png"), "bright focus ring")
	_settings.values["high_contrast"] = false
	board.rebuild()
	fsb = (board._cards["ev_damaged_seal"] as Button).get_theme_stylebox("focus") as StyleBoxTexture
	kit.ok(fsb != null and str(fsb.texture.resource_path).ends_with("focus.png"), "normal focus ring again")
	return true


func _new_cards() -> bool:
	var g := _story_at("c3c")
	var board := _make_board(g)
	kit.eq(board.new_items, [], "the first opening after a start or a load marks nothing")
	board.close()
	g.inspect("c3d_inspect_intake")
	g.inspect("c3d_inspect_drawer")
	board.open({"story": g})
	kit.eq(board.new_items, ["ev_c3_intake_book", "ev_c3_scarf"], "the two finds since the last opening are new")
	kit.eq(board.focused_item, "ev_c3_scarf", "the focus starts on the newest card")
	var b: Button = board._cards["ev_c3_scarf"]
	kit.ok(b.get_node_or_null("New") != null, "the new card carries its „Neu“ tag")
	kit.ok((board._cards["ev_damaged_seal"] as Button).get_node_or_null("New") == null, "an old card does not")
	board.close()
	board.open({"story": g})
	kit.eq(board.new_items, [], "seen once, not new again")
	board.close()
	g.inspect("c3d_inspect_intake")   # already done: refused, nothing changes
	board.open({"story": g, "memory_scene": "L_A1_Railyard"})
	kit.eq(board.new_items, [], "a memory never marks anything")
	board.close()
	return true


# ------------------------------------------------------------------ journal
func _journal() -> bool:
	var J: Script = load("res://scripts/ui/journal.gd")
	kit.ok("board" in J.TABS and not ("board" in J.ROW_TABS), "„Akte“ is a journal tab outside the flow row")
	kit.eq(J.ROW_TABS, ["objectives", "tasks", "evidence", "people", "decisions", "discoveries", "history"], "the seven index tabs")
	var g := _story_at("c3c")
	UIKit.overrides["Story"] = g
	var holder := Control.new()
	holder.theme = load(THEME)
	holder.size = Vector2(1920, 1080)
	kit.mount(holder)
	var j: Control = load(JOURNAL_SCENE).instantiate()
	holder.add_child(j)
	var vtab: Button = j._tab_buttons.get("board")
	kit.ok(vtab != null and vtab.get_parent() == j, "the divider is a child of the journal, not of the flow row")
	j._tab_counts = {}
	j._fit_tabs()
	kit.eq((j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size"), 24, "the row tabs keep 24 px")
	j.open("board")
	kit.eq(j.current_tab, "board", "open on „Akte“")
	kit.ok(vtab.button_pressed, "the divider is pressed")
	var open_btn: Button = j.find_child("OpenBoard", true, false)
	kit.ok(open_btn != null, "the cover page offers „Pinnwand öffnen“")
	if open_btn != null:
		open_btn.pressed.emit()
		kit.ok(j.board != null and j.board.is_open, "„Pinnwand öffnen“ opens the board")
		kit.eq(int(j.board.model.get("owned", 0)), g.inventory().size(), "with the Story's items")
		j.board.close()
	j.cycle_tab(1)
	kit.eq(j.current_tab, "objectives", "Q/E cycle past „Akte“ back to the first tab")
	j.cycle_tab(-1)
	kit.eq(j.current_tab, "board", "and back")
	j.close()
	UIKit.overrides.erase("Story")
	return true


# ------------------------------------------------------------------ art
func _art() -> bool:
	for f in ["cork.png", "cork_hc.png", "frame.png", "pin_alexei.png", "pin_konrad.png", "pin_red.png", "card_paper.png",
			"card_photo.png", "card_burned.png", "tag.png", "note.png", "ghost.png", "focus.png", "focus_hc.png",
			"unknown.png", "folder.png", "vtab_normal.png", "vtab_pressed.png", "vtab_hover.png", "vtab_focus.png"]:
		kit.ok(FileAccess.file_exists("res://assets/ui/board/" + f), "art %s exists" % f)
	for id in _items():
		var p := "res://assets/ui/board/thumbs/%s.png" % id
		kit.ok(FileAccess.file_exists(p), "card picture for %s" % id)
		if FileAccess.file_exists(p):
			var img := Image.load_from_file(ProjectSettings.globalize_path(p))
			kit.eq(img.get_size(), Vector2i(162, 72), "%s: 54x24 at x3" % id)
	var man := _json("res://assets/ui/board/manifest.json")
	kit.eq(str(man.get("generator", "")), "tools/pixelgen/gen_ui_board.py", "manifest names the generator")
	kit.ok((man.get("files", []) as Array).size() >= 50, "manifest lists the textures")
	kit.ok(FileAccess.file_exists("res://assets/ui/board/src_1x/.gdignore"), "1:1 sources are never imported")
	return true
