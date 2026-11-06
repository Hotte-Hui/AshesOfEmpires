extends RefCounted
## Second-pass review of the side tasks (TECHNICAL_ARCHITECTURE §12.9): regression tests for the defects fixed in the
## review and for edge cases tests/test_tasks.gd does not cover.
##  - requires-cycle validation: only real cycles are reported (an entry that merely depends on a cycle is not one),
##    independent cycles are all reported, and a step listed twice in one task is reported as such;
##  - task toasts („Neue Aufgabe“ / „Aufgabe erledigt“) through Game.toast(): exactly one per start / finish, none
##    for unrelated finds, middle steps, re-reads, restore() or reset(), none with notify_tasks off or outside the tree;
##  - a `once` chain whose next entry is already found stays hidden (no endless re-arm), and is re-armed only for an
##    entry that is new (live on the Explore autoload, state restored afterwards);
##  - the journal's seven index tabs fit the 1500 px sheet with late-game counters (real theme and fonts).

const Kit := preload("res://tests/support/test_kit.gd")
const EXPLORE := "res://scripts/core/explore.gd"
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const JOURNAL_SCENE := "res://scenes/ui/Journal.tscn"
const THEME := "res://assets/ui/theme.tres"
const SHEET_W := 1500.0

var kit: Kit


class StubHud extends Node:
	var log: Array = []
	func toast(text: String, _kind := "") -> void:
		log.append(text)


class StubUI extends Node:
	var hud: Node = null


func run() -> Array:
	kit = Kit.new()
	kit.run_case("cycle_validation_reports_real_cycles_only", _cycles)
	kit.run_case("duplicate_step_messages", _duplicates)
	kit.run_case("task_toasts_once_per_start_and_finish", _toasts)
	kit.run_case("once_chain_stays_hidden_on_a_found_entry", _once_chain)
	kit.run_case("journal_tabs_fit_the_sheet", _tabs)
	kit.cleanup()
	return kit.failures


func _new() -> Node:
	var ex: Node = kit.track(load(EXPLORE).new())
	ex.print_warnings = false
	ex.notify_tasks = false
	return ex


static func _entry(id: String, req: Array) -> Dictionary:
	var d := {"id": id, "kind": "detail", "level": "L1", "title_key": "ui.tasks.next", "text_key": "ui.tasks.next"}
	if not req.is_empty():
		d["requires"] = req
	return d


static func _cycle_lines(warnings: Array) -> Array:
	var out: Array = []
	for w in warnings:
		if str(w).begins_with("requires cycle: "):
			out.append(str(w).trim_prefix("requires cycle: ").get_slice(" (", 0))
	return out


# ------------------------------------------------------------------ validation
func _cycles() -> bool:
	var ex := _new()
	# a -> b <-> c (a depends on the cycle), d -> a, e -> c (dependents), f <-> g (a second cycle), h free
	ex.load_data({"area": "v", "entries": [
		_entry("v.a", ["v.b"]), _entry("v.b", ["v.c"]), _entry("v.c", ["v.b"]),
		_entry("v.d", ["v.a"]), _entry("v.e", ["v.c"]),
		_entry("v.f", ["v.g"]), _entry("v.g", ["v.f"]), _entry("v.h", []),
	]}, "review_cycles.json")
	var cyc := _cycle_lines(ex.warnings)
	kit.eq(cyc, ["v.b -> v.c -> v.b", "v.f -> v.g -> v.f"], "exactly the two real cycles, each once")
	for id in ["v.a", "v.d", "v.e", "v.h"]:
		for c in cyc:
			kit.ok(not str(c).begins_with(id + " "), "%s is not reported as the start of a cycle (%s)" % [id, c])
	for id in ["v.a", "v.b", "v.c", "v.d", "v.e", "v.f", "v.g"]:
		kit.ok(not ex.can_find(id), "%s can never be found (on or behind a cycle)" % id)
	kit.ok(ex.can_find("v.h"), "an entry without requirements stays findable")
	# a self reference is still reported as such (and as a one-entry cycle)
	var s := _new()
	s.load_data({"area": "v", "entries": [_entry("v.self", ["v.self"]), _entry("v.after", ["v.self"])]}, "review_self.json")
	var all := "\n".join(s.warnings)
	kit.ok(all.contains("entry 'v.self' (review_self.json): requires itself"), "self reference reported")
	kit.eq(_cycle_lines(s.warnings), ["v.self -> v.self"], "the dependent entry is not reported as a cycle")
	# the clean mock data of a valid task chain reports nothing
	var c := _new()
	c.load_data({"area": "v", "entries": [_entry("v.1", []), _entry("v.2", ["v.1"]), _entry("v.3", ["v.2", "v.1"])]},
		"review_chain.json")
	kit.eq(_cycle_lines(c.warnings), [], "a diamond of requirements is no cycle")
	return true


func _duplicates() -> bool:
	var ex := _new()
	var step := func(id: String) -> Dictionary:
		return {"explore_id": id, "hint_key": "ui.tasks.next"}
	ex.load_data({"area": "v", "entries": [_entry("v.s1", []), _entry("v.s2", ["v.s1"]), _entry("v.s3", ["v.s2"])],
		"tasks": [
			{"id": "v.twice", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
				"steps": [step.call("v.s1"), step.call("v.s2"), step.call("v.s2")]},
			{"id": "v.other", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
				"steps": [step.call("v.s1")]},
		]}, "review_dup.json")
	var all := "\n".join(ex.warnings)
	kit.ok(all.contains("task 'v.twice' (review_dup.json): step 'v.s2' is listed twice"), "a step listed twice in one task")
	kit.ok(not all.contains("step 'v.s2' is already a step of task 'v.twice'"), "not mistaken for a step of another task")
	kit.ok(all.contains("task 'v.other' (review_dup.json): step 'v.s1' is already a step of task 'v.twice'"),
		"a step shared by two tasks is still reported")
	return true


# ------------------------------------------------------------------ toasts
## A mock task in a mounted Explore instance with notify_tasks on; Game.toast() reaches a stub HUD.
func _toasts() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game")
	var loc: Node = Kit.root().get_node_or_null("Loc")
	if not kit.ok(game != null and game.has_method("toast") and loc != null, "Game and Loc autoloads"):
		return true
	var ex := _new()
	kit.mount(ex)
	ex.load_data({"area": "v", "entries": [
		{"id": "v.ask", "kind": "chat", "level": "L1", "title_key": "ui.tasks.next",
			"lines": [{"speaker": "vendor", "key": "ui.tasks.next"}]},
		_entry("v.do", ["v.ask"]),
		{"id": "v.back", "kind": "chat", "level": "L1", "title_key": "ui.tasks.next", "requires": ["v.do"],
			"lines": [{"speaker": "vendor", "key": "ui.tasks.next"}]},
		_entry("v.free", []),
	], "tasks": [{"id": "v.task", "level": "L1", "title_key": "ui.tasks.kicker.active", "summary_key": "ui.tasks.next",
		"steps": [{"explore_id": "v.ask", "hint_key": "ui.tasks.next"}, {"explore_id": "v.do", "hint_key": "ui.tasks.next"},
			{"explore_id": "v.back", "hint_key": "ui.tasks.next"}]}]}, "review_toasts.json")
	var title: String = loc.t("ui.tasks.kicker.active")
	var want_new: String = loc.t("ui.toast.task_new", {"name": title})
	var want_done: String = loc.t("ui.toast.task_done", {"name": title})
	var hud := StubHud.new()
	var ui := StubUI.new()
	ui.hud = hud
	kit.track(hud)
	kit.track(ui)
	var saved_ui = game.get("ui")
	var saved_busy = game.get("busy")
	game.set("ui", ui)
	game.set("busy", false)
	ex.notify_tasks = true
	ex.find("v.free")
	kit.eq(hud.log, [], "an unrelated find announces nothing")
	ex.find("v.ask")
	kit.eq(hud.log, [want_new], "the first step announces the new task once")
	ex.find("v.ask")
	kit.eq(hud.log, [want_new], "re-reading the first step announces nothing")
	ex.find("v.do")
	kit.eq(hud.log, [want_new], "a middle step announces nothing")
	ex.find("v.back")
	kit.eq(hud.log, [want_new, want_done], "the last step announces the finished task once")
	ex.find("v.back")
	kit.eq(hud.log.size(), 2, "re-reading the last step announces nothing")
	hud.log.clear()
	ex.reset()
	ex.restore({"found": ["v.ask", "v.do", "v.back"], "cards": []})
	ex.restore({"found": ["v.ask"], "cards": []})
	kit.eq(hud.log, [], "reset() / restore() never announce")
	ex.reset()
	ex.notify_tasks = false
	ex.find("v.ask")
	kit.eq(hud.log, [], "notify_tasks off: silent")
	var loose := _new()                   # never added to the tree
	loose.notify_tasks = true
	loose.load_data({"area": "v", "entries": [_entry("v.x", [])], "tasks": [{"id": "v.t1", "level": "L1",
		"title_key": "ui.tasks.next", "summary_key": "ui.tasks.next", "steps": [{"explore_id": "v.x", "hint_key": "ui.tasks.next"}]}]},
		"review_loose.json")
	loose.find("v.x")
	kit.eq(hud.log, [], "an Explore outside the tree (tests, previews) never toasts")
	game.set("ui", saved_ui)
	game.set("busy", saved_busy)
	return true


# ------------------------------------------------------------------ chains
## Find_Stove in L_C3_Station: chain [kettle (task step), stove], once. Reading the stove first hides the spot; the
## coupling re-arms it for the kettle; once the kettle is found the chain falls back to the already-read stove and
## must stay hidden instead of offering it again.
func _once_chain() -> bool:
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if not kit.ok(ex != null and ex.has_method("task_state") and ex.has_entry("veltrava.task.heating.kettle"),
			"Explore autoload with the station task"):
		return true
	var saved: Dictionary = ex.state()
	var notify: bool = ex.notify_tasks
	ex.notify_tasks = false
	ex.reset()
	var stove: Node = INTERACTABLE.new()
	stove.kind = "discover"
	stove.once = true
	stove.explore_id = "veltrava.station.stove"
	stove.explore_chain = PackedStringArray(["veltrava.task.heating.kettle", "veltrava.station.stove"])
	kit.mount(stove)
	kit.eq(stove.explore_id, "veltrava.station.stove", "new game: the blocked task step is skipped")
	stove.used = true                     # Game._do_discover marks the spot used before Explore.find
	ex.find("veltrava.station.stove")
	kit.ok(not stove.is_active(), "stove read, kettle still blocked: hidden")
	ex.find("veltrava.task.heating.ask")
	ex.find("veltrava.task.heating.coupling")
	kit.eq(stove.explore_id, "veltrava.task.heating.kettle", "coupling found: the spot hosts the kettle step")
	kit.ok(stove.is_active() and not stove.used, "re-armed for the new entry")
	kit.eq(stove.prompt_state(), "task", "the kettle is marked as a task step")
	stove.used = true
	ex.find("veltrava.task.heating.kettle")
	kit.eq(stove.explore_id, "veltrava.station.stove", "nothing new left: back on the last found entry")
	kit.ok(stove.used and not stove.is_active(), "a found entry never re-arms a once spot")
	var pend: Array = load("res://scripts/core/autoplay.gd").pending_finds([stove], ex)
	kit.eq(pend, [], "the drivers see nothing new there")
	ex.reset()
	ex.restore(saved)
	ex.notify_tasks = notify
	return true


# ------------------------------------------------------------------ journal tabs
## Seven index tabs plus counters inside the 1500 px sheet with the real theme: no shrinking without counters,
## late-game counters (three-digit discoveries) still fit and stay readable.
func _tabs() -> bool:
	if not kit.ok(ResourceLoader.exists(JOURNAL_SCENE) and ResourceLoader.exists(THEME), "journal scene and theme"):
		return true
	var holder := Control.new()
	holder.theme = load(THEME)
	holder.size = Vector2(1920, 1080)
	kit.mount(holder)
	var j: Control = load(JOURNAL_SCENE).instantiate()
	holder.add_child(j)
	var row: Control = (j._tab_buttons["objectives"] as Button).get_parent()
	var sets := [
		{},
		{"objectives": 2, "tasks": 1, "evidence": 3, "people": 1, "decisions": 1, "discoveries": 10},
		{"objectives": 3, "tasks": 5, "evidence": 19, "people": 23, "decisions": 4, "discoveries": 115, "history": 19},
		{"objectives": 9, "tasks": 9, "evidence": 99, "people": 99, "decisions": 9, "discoveries": 999, "history": 99},
	]
	for s in sets:
		j._tab_counts = (s as Dictionary).duplicate()
		j._fit_tabs()
		var w: float = row.get_combined_minimum_size().x
		var fs: int = (j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size")
		kit.ok(w <= SHEET_W, "tabs fit the %d px sheet with %s (%.0f px)" % [int(SHEET_W), s, w])
		kit.ok(fs >= 16, "tab labels stay readable with %s (%d px)" % [s, fs])
		for id in s:
			kit.ok((j._tab_buttons[id] as Button).text.ends_with(str(s[id])), "tab %s shows its counter %s" % [id, s[id]])
	j._tab_counts = {}
	j._fit_tabs()
	kit.eq((j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size"), 24,
		"without counters the theme size is kept")
	return true
