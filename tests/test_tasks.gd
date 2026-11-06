extends RefCounted
## Side tasks („Aufgaben“, TECHNICAL_ARCHITECTURE §12.9; owner: tasks).
## System (own mock data, own Explore instances): "requires" gate can_find/find (refused finds keep the §12.1
## result shape), derived task states / current step / hints, task_changed on find / restore / reset (never for
## unrelated finds), reward cards unlock once with the completing find and are re-attached silently on restore,
## the save format stays {found, cards}, and validation reports unknown ids, cycles, foreign levels, steps out of
## order, unenforced order, steps in two tasks, missing keys and unknown reward cards.
## Interactables: the chain rule (first unfound findable entry, else the last found one, else the first), live
## chains on the real Explore autoload (requirements, prompt marks "task"/"found", once re-armed, kind follows the
## entry), the drivers' shared pending_finds() helper, the journal's task_rows() order.
## Content (the five real tasks): one per walkable level, every step an entry of that level placed exactly once
## (explore_id or explore_chain) in the level scene, the drivers' loop (re-collect until nothing new is findable,
## story gates open as in the final pass) completes every task in step order, texts present in de_tasks.json and
## used, German typography, lengths that fit the HUD / dialogue box, chat speakers known, new hotspots inside the
## walk area, clear of props, story spots and other finds, the close-up fits 320x200.
## Headless and read-only: level scenes are read through their SceneState, never instanced; the Explore autoload's
## state is restored after the live case.

const Kit := preload("res://tests/support/test_kit.gd")
const EXPLORE := "res://scripts/core/explore.gd"
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const INTERACTABLE_PATH := "res://scripts/actors/interactable.gd"
const GATED_PATH := "res://scripts/actors/gated_interactable.gd"
const AUTOPLAY := preload("res://scripts/core/autoplay.gd")
const JOURNAL := preload("res://scripts/ui/journal.gd")
const LOCALE := "res://data/locale/de_tasks.json"
const EXPLORE_DIR := "res://data/explore/"
const STORY_KINDS := ["inspect", "dialogue", "puzzle", "choice"]
const OBLIQUE_Y := 1.6           # scripts/actors/player.gd: dy x 1.6 in oblique levels
## The five walkable levels, their art folder, metric and spacing rules (same numbers as the per-area tests).
const LEVELS := {
	"L_A1_Railyard": {"env": "karsk_railyard", "oblique": true, "gap_story": 26.0, "gap_find": 12.0, "hero": "alexei"},
	"L_M1_Archive": {"env": "berlin_archive", "oblique": false, "gap_story": 24.0, "gap_find": 14.0, "hero": "konrad"},
	"L_M1_Plaza": {"env": "hall_plaza", "oblique": true, "gap_story": 26.0, "gap_find": 26.0, "hero": "konrad"},
	"L_C3_Station": {"env": "veltrava_station", "oblique": true, "gap_story": 26.0, "gap_find": 12.0, "hero": "alexei"},
	"L_C3_Hall": {"env": "veltrava_hall", "oblique": false, "gap_story": 24.0, "gap_find": 14.0, "hero": "konrad"},
}
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]

var kit: Kit
var loc: Node
var real: Node                      # fresh Explore instance on the real data
var task_files: Dictionary = {}     # file -> parsed tasks_*.json
var my_entries: Dictionary = {}     # explore id -> entry of a tasks_*.json file
var scenes: Dictionary = {}         # level id -> [{name, script, props}]
var hotspots: Dictionary = {}       # level id -> merged hotspots
var manifests: Dictionary = {}      # level id -> scene.json


class MockEx extends RefCounted:
	var found := {}
	var req := {}
	func is_found(id: String) -> bool:
		return found.has(id)
	func can_find(id: String) -> bool:
		for r in req.get(id, []):
			if not found.has(r):
				return false
		return true


class MockTasks extends RefCounted:
	var list: Array = []
	var states := {}
	func tasks_for(_x := "") -> Array:
		return list
	func task_state(id: String) -> Dictionary:
		return states.get(id, {"state": "", "step": -1, "hint_key": "", "done_steps": []})


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("requires_gate_find_and_can_find", _requires)
	kit.run_case("task_states_steps_and_hints", _states)
	kit.run_case("task_changed_signals", _signals)
	kit.run_case("reward_cards_unlock_once", _rewards)
	kit.run_case("restore_reset_and_save_format", _restore)
	kit.run_case("validation_reports_broken_tasks", _broken)
	kit.run_case("clean_mock_data_validates", _clean)
	kit.run_case("chain_rule", _chain_rule)
	kit.run_case("journal_task_rows", _journal_rows)
	kit.run_case("real_data_loads", _real_data)
	kit.run_case("live_chains_on_the_autoload", _live)
	kit.run_case("five_tasks_one_per_level", _five)
	kit.run_case("steps_placed_exactly_once", _placed)
	kit.run_case("drivers_complete_every_task", _drivers)
	kit.run_case("locale_keys_texts_and_typography", _texts)
	kit.run_case("chats_speakers_and_npcs", _chats)
	kit.run_case("new_hotspots_placement", _hotspots)
	kit.run_case("closeup_image", _image)
	if real != null and is_instance_valid(real):
		real.free()
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ fixtures
func _new() -> Node:
	var ex: Node = kit.track(load(EXPLORE).new())
	ex.print_warnings = false
	ex.notify_tasks = false
	return ex


## One task (ask -> find -> back) in Karsk plus an unrelated find and a card reward. Keys exist (validates clean).
static func mock_area() -> Dictionary:
	var line := [{"speaker": "vendor", "key": "ui.tasks.next", "expr": "neutral"}, {"speaker": "alexei", "key": "ui.tasks.done_steps"}]
	return {"area": "mock", "entries": [
		{"id": "m.ask", "kind": "chat", "level": "L_A1_Railyard", "title_key": "ui.tasks.next", "lines": line},
		{"id": "m.find", "kind": "detail", "level": "L_A1_Railyard", "title_key": "ui.tasks.next", "text_key": "ui.tasks.done_steps",
			"requires": ["m.ask"]},
		{"id": "m.back", "kind": "chat", "level": "L_A1_Railyard", "title_key": "ui.tasks.next", "lines": line,
			"requires": ["m.find"]},
		{"id": "m.free", "kind": "detail", "level": "L_A1_Railyard", "title_key": "ui.tasks.next", "text_key": "ui.tasks.next",
			"history": ["hist.m.linked"]},
		{"id": "m.berlin", "kind": "detail", "level": "L_M1_Archive", "title_key": "ui.tasks.next", "text_key": "ui.tasks.next"},
	], "tasks": [
		{"id": "m.task", "level": "L_A1_Railyard", "title_key": "ui.tasks.kicker.active", "summary_key": "ui.tasks.next",
			"steps": [{"explore_id": "m.ask", "hint_key": "ui.tasks.kicker.active"},
				{"explore_id": "m.find", "hint_key": "ui.tasks.next"},
				{"explore_id": "m.back", "hint_key": "ui.tasks.done_steps"}],
			"reward_cards": ["hist.m.reward"]},
	]}


static func mock_hist() -> Dictionary:
	var cards: Array = []
	for id in ["hist.m.linked", "hist.m.reward"]:
		cards.append({"id": id, "title_key": "ui.tasks.next", "text_key": "ui.tasks.next", "year": "1990",
			"sources": [{"label": "Archiv", "url": "https://example.org/a"}]})
	return {"side": "soviet", "cards": cards}


func _loaded() -> Node:
	var ex := _new()
	ex.load_data(mock_area(), "tasks_mock.json")
	ex.load_data(mock_hist(), "history_mock.json")
	return ex


# ------------------------------------------------------------------ system
func _requires() -> bool:
	var ex := _loaded()
	kit.eq(ex.requires_of("m.find"), ["m.ask"], "requires_of")
	kit.eq(ex.requires_of("m.free"), [], "requires_of without requirements")
	kit.ok(ex.can_find("m.ask") and ex.can_find("m.free"), "entries without requirements are findable")
	kit.ok(not ex.can_find("m.find"), "a required entry is not found yet -> not findable")
	kit.ok(not ex.can_find("nope"), "unknown ids are never findable")
	kit.eq(ex.find("m.find"), {"ok": false, "new": false, "entry": {}, "cards_new": []}, "blocked find refused (§12.1 shape)")
	kit.ok(not ex.is_found("m.find"), "a refused find is not recorded")
	kit.eq(ex.counts("L_A1_Railyard"), {"found": 0, "total": 4}, "a refused find does not count")
	ex.find("m.ask")
	kit.ok(ex.can_find("m.find"), "requirement found -> findable")
	kit.eq(ex.find("m.find")["ok"], true, "find accepted once unlocked")
	kit.ok(ex.can_find("m.find"), "a found entry stays findable")
	kit.eq(ex.find("m.find"), {"ok": true, "new": false, "entry": ex.entry("m.find"), "cards_new": []}, "re-finding is idempotent")
	return true


func _states() -> bool:
	var ex := _loaded()
	kit.eq(ex.tasks_for("L_A1_Railyard").map(func(t): return t["id"]), ["m.task"], "tasks_for(level)")
	kit.eq(ex.tasks_for("mock").size(), 1, "tasks_for(area)")
	kit.eq(ex.tasks_for("").size(), 1, "tasks_for(all)")
	kit.eq(ex.tasks_for("L_M1_Archive"), [], "tasks_for(other level)")
	kit.eq(ex.task_of("m.find"), "m.task", "task_of(step)")
	kit.eq(ex.task_of("m.free"), "", "task_of(non-step)")
	kit.eq(ex.task_steps("m.task"), ["m.ask", "m.find", "m.back"], "task_steps")
	kit.eq(ex.task_state("m.task"), {"state": "not_started", "step": 0, "hint_key": "ui.tasks.kicker.active", "done_steps": []},
		"not started")
	ex.find("m.free")
	kit.eq(ex.task_state("m.task")["state"], "not_started", "an unrelated find does not start the task")
	ex.find("m.ask")
	kit.eq(ex.task_state("m.task"), {"state": "active", "step": 1, "hint_key": "ui.tasks.next", "done_steps": ["m.ask"]},
		"active after the first step: hint of the current step")
	ex.find("m.find")
	kit.eq(ex.task_state("m.task"), {"state": "active", "step": 2, "hint_key": "ui.tasks.done_steps",
		"done_steps": ["m.ask", "m.find"]}, "active, next step")
	kit.eq(ex.task_counts("L_A1_Railyard"), {"done": 0, "active": 1, "total": 1}, "task_counts while active")
	ex.find("m.back")
	kit.eq(ex.task_state("m.task"), {"state": "done", "step": 3, "hint_key": "", "done_steps": ["m.ask", "m.find", "m.back"]},
		"done")
	kit.eq(ex.task_counts(""), {"done": 1, "active": 0, "total": 1}, "task_counts when done")
	kit.eq(ex.task_state("nope"), {"state": "", "step": -1, "hint_key": "", "done_steps": []}, "unknown task")
	return true


func _signals() -> bool:
	var ex := _loaded()
	var log: Array = []
	ex.found.connect(func(id): log.append("found:" + id))
	ex.history_unlocked.connect(func(c): log.append("card:" + c))
	ex.task_changed.connect(func(t): log.append("task:" + t))
	ex.state_changed.connect(func(): log.append("changed"))
	ex.find("m.free")
	kit.eq(log, ["found:m.free", "card:hist.m.linked", "changed"], "unrelated find: no task_changed")
	log.clear()
	ex.find("m.ask")
	kit.eq(log, ["found:m.ask", "task:m.task", "changed"], "first step: task_changed before state_changed")
	log.clear()
	ex.find("m.ask")
	kit.eq(log, [], "re-finding a step: nothing")
	ex.find("m.back")
	kit.eq(log, [], "a refused (blocked) step: nothing")
	ex.find("m.find")
	kit.eq(log, ["found:m.find", "task:m.task", "changed"], "middle step: the current step changed")
	log.clear()
	ex.find("m.back")
	kit.eq(log, ["found:m.back", "card:hist.m.reward", "task:m.task", "changed"], "last step: reward card, then task_changed")
	return true


func _rewards() -> bool:
	var ex := _loaded()
	kit.ok(not ex.is_card_found("hist.m.reward"), "reward card not found before")
	ex.find("m.ask")
	ex.find("m.find")
	var r: Dictionary = ex.find("m.back")
	kit.eq(r["cards_new"], ["hist.m.reward"], "the completing find returns the reward card in cards_new")
	kit.ok(ex.is_card_found("hist.m.reward"), "reward card filed")
	kit.eq(ex.find("m.back")["cards_new"], [], "a reward unlocks once")
	kit.eq(ex.history_counts(), {"found": 1, "total": 2}, "history counts include the reward")
	var w: Array = ex.validate()
	kit.ok(not "\n".join(w).contains("hist.m.reward"), "a card linked only as a task reward is not 'unlinked'")
	return true


func _restore() -> bool:
	var a := _loaded()
	a.find("m.ask")
	a.find("m.find")
	a.find("m.back")
	var st: Dictionary = a.state()
	kit.eq(st.keys(), ["found", "cards"], "save format unchanged: only found + cards")
	kit.eq(st["found"], ["m.ask", "m.find", "m.back"], "found ids in find order")
	var b := _loaded()
	var log: Array = []
	b.task_changed.connect(func(t): log.append("task:" + t))
	b.history_unlocked.connect(func(c): log.append("card:" + c))
	b.restore({"found": ["m.ask", "m.find", "m.back"], "cards": []})
	kit.ok(b.is_card_found("hist.m.reward"), "restore re-attaches the reward card of a finished task")
	kit.eq(log, ["task:m.task"], "restore: task_changed, but no history_unlocked")
	kit.eq(b.task_state("m.task")["state"], "done", "task done after restore")
	log.clear()
	b.reset()
	kit.eq(log, ["task:m.task"], "reset: task_changed")
	kit.eq(b.task_state("m.task")["state"], "not_started", "task not started after reset")
	log.clear()
	b.restore({"found": [], "cards": []})
	kit.eq(log, [], "restore without a change: no task_changed")
	return true


func _broken() -> bool:
	var ex := _new()
	var e := func(id: String, lvl: String, extra: Dictionary) -> Dictionary:
		var d := {"id": id, "kind": "detail", "level": lvl, "title_key": "ui.tasks.next", "text_key": "ui.tasks.next"}
		d.merge(extra, true)
		return d
	var step := func(id: String) -> Dictionary:
		return {"explore_id": id, "hint_key": "ui.tasks.next"}
	ex.load_data({"area": "x", "entries": [
		e.call("x.a", "L1", {"requires": ["x.nope"]}),
		e.call("x.b", "L1", {"requires": ["x.c"]}),
		e.call("x.c", "L1", {"requires": ["x.b"]}),
		e.call("x.d", "L2", {}),
		e.call("x.e", "L1", {"requires": ["x.d"]}),
		e.call("x.f", "L1", {"requires": ["x.f"]}),
		e.call("x.g", "L1", {"requires": "x.a"}),
		e.call("x.s1", "L1", {}),
		e.call("x.s2", "L1", {"requires": ["x.s3"]}),
		e.call("x.s3", "L1", {}),
		e.call("x.u1", "L1", {}),
		e.call("x.u2", "L1", {}),
	], "tasks": [
		{"id": "x.t_order", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.s1"), step.call("x.s2"), step.call("x.s3")]},
		{"id": "x.t_free", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.u1"), step.call("x.u2")]},
		{"id": "x.t_level", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.d")]},
		{"id": "x.t_unknown", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.none")]},
		{"id": "x.t_dup", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.u1")]},
		{"id": "x.t_keys", "level": "L1", "title_key": "explore.test.no_such_key", "steps": [{"explore_id": "x.a"}]},
		{"id": "x.t_reward", "level": "L1", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next",
			"steps": [step.call("x.e")], "reward_cards": ["hist.none"]},
		{"id": "x.t_empty", "title_key": "ui.tasks.next", "summary_key": "ui.tasks.next", "steps": []},
		{"title_key": "ui.tasks.next"},
	]}, "a_tasks.json")
	ex.load_data({"area": "x", "entries": [e.call("x.z", "L1", {})], "tasks": [{"id": "x.t_free", "level": "L1",
		"title_key": "ui.tasks.next", "summary_key": "ui.tasks.next", "steps": [step.call("x.z")]}]}, "b_tasks.json")
	ex.load_data({"area": "y", "entries": [e.call("y.a", "L1", {})], "tasks": "nope"}, "c_tasks.json")
	var all := "\n".join(ex.warnings)
	for frag in ["entry 'x.a' (a_tasks.json): requires unknown explore id 'x.nope'",
			"requires cycle: x.b -> x.c -> x.b",
			"entry 'x.e' (a_tasks.json): requires 'x.d' of another level (L2)",
			"entry 'x.f' (a_tasks.json): requires itself",
			"entry 'x.g' (a_tasks.json): 'requires' must be an array",
			"task 'x.t_order' (a_tasks.json): step 1 'x.s2' requires the later step 2 'x.s3' (steps out of order)",
			"task 'x.t_order' (a_tasks.json): step 2 'x.s3' does not require step 1 'x.s2' (the order is not enforced)",
			"task 'x.t_free' (a_tasks.json): step 1 'x.u2' does not require step 0 'x.u1'",
			"task 'x.t_level' (a_tasks.json): step 0 'x.d' belongs to level L2, not L1",
			"task 'x.t_unknown' (a_tasks.json): step 0 'x.none' is not an explore entry",
			"task 'x.t_dup' (a_tasks.json): step 'x.u1' is already a step of task 'x.t_free'",
			"task 'x.t_keys' (a_tasks.json): title_key 'explore.test.no_such_key' has no text",
			"task 'x.t_keys' (a_tasks.json): missing 'summary_key'",
			"task 'x.t_keys' (a_tasks.json): step 0 needs 'hint_key'",
			"task 'x.t_reward' (a_tasks.json): reward card 'hist.none' does not exist",
			"task 'x.t_empty' (a_tasks.json): missing 'level'",
			"task 'x.t_empty' (a_tasks.json): needs a non-empty 'steps' array",
			"a_tasks.json: task without id skipped",
			"duplicate task id 'x.t_free' in b_tasks.json (first defined in a_tasks.json",
			"c_tasks.json: 'tasks' must be an array"]:
		kit.ok(all.contains(frag), "warning reported: " + frag)
	kit.ok(not ex.can_find("x.b") and not ex.can_find("x.c"), "entries on a cycle can never be found")
	return true


func _clean() -> bool:
	var ex := _loaded()
	kit.eq(ex.warnings, [], "valid mock data with a task, requirements and a reward validates without warnings")
	return true


func _chain_rule() -> bool:
	var m := MockEx.new()
	m.req = {"b": ["a"], "c": ["x"]}
	var pick := func(chain: Array) -> String:
		return INTERACTABLE.pick_chain_step(PackedStringArray(chain), m)
	kit.eq(pick.call([]), "", "empty chain")
	kit.eq(pick.call(["a", "b"]), "a", "nothing found: the first findable entry")
	m.found = {"a": true}
	kit.eq(pick.call(["a", "b"]), "b", "next entry unlocked: it becomes current")
	kit.eq(pick.call(["a", "c"]), "a", "next entry still blocked: stay on the last found one (re-read)")
	m.found = {}
	kit.eq(pick.call(["c", "a"]), "a", "a blocked first entry is skipped for a findable later one")
	kit.eq(pick.call(["c"]), "c", "nothing found and nothing findable: the first entry (inactive)")
	m.found = {"a": true, "b": true}
	kit.eq(pick.call(["a", "b"]), "b", "all found: the last entry")
	return true


func _journal_rows() -> bool:
	var m := MockTasks.new()
	m.list = [{"id": "t.a", "level": "LA", "title_key": "ta", "summary_key": "sa", "steps": [{}, {}, {}]},
		{"id": "t.b", "level": "LB", "title_key": "tb", "summary_key": "sb", "steps": [{}, {}]},
		{"id": "t.c", "level": "LB", "title_key": "tc", "summary_key": "sc", "steps": [{}]},
		{"id": "t.d", "level": "LB", "title_key": "td", "summary_key": "sd", "steps": [{}, {}]}]
	m.states = {"t.a": {"state": "active", "step": 1, "hint_key": "ha", "done_steps": ["x"]},
		"t.b": {"state": "done", "step": 2, "hint_key": "", "done_steps": ["y", "z"]},
		"t.c": {"state": "not_started", "step": 0, "hint_key": "hc", "done_steps": []},
		"t.d": {"state": "active", "step": 1, "hint_key": "hd", "done_steps": ["w"]}}
	var rank := func(level: String) -> float:
		return 0.0 if level == "LA" else 1.0
	var rows: Array = JOURNAL.task_rows(m, rank)
	kit.eq(rows.map(func(r): return r["id"]), ["t.d", "t.a", "t.b"], "open tasks first (latest place first), then done; never the unstarted")
	kit.eq([rows[1]["hint_key"], rows[1]["step"], rows[1]["total"]], ["ha", 1, 3], "row carries the current hint and progress")
	kit.eq(rows[2]["done_steps"], ["y", "z"], "row carries the finished steps")
	kit.eq(JOURNAL.task_rows(null, rank), [], "no Explore service: no rows")
	kit.eq(JOURNAL.TABS.slice(0, 2), ["objectives", "tasks"], "journal tab 'Aufgaben' right after 'Ziele'")
	kit.ok(loc.has("ui.journal.tab.tasks") and loc.has("ui.journal.empty.tasks"), "tab title and empty text exist")
	return true


# ------------------------------------------------------------------ real data
func _real_data() -> bool:
	real = load(EXPLORE).new()
	real.print_warnings = false
	real.notify_tasks = false
	real.reload()
	var d := DirAccess.open(EXPLORE_DIR)
	if not kit.ok(d != null, "data/explore readable"):
		return true
	for f in d.get_files():
		if str(f).begins_with("tasks_") and str(f).ends_with(".json"):
			var parsed = JSON.parse_string(FileAccess.get_file_as_string(EXPLORE_DIR + str(f)))
			if kit.ok(parsed is Dictionary, "%s parses" % f):
				task_files[str(f)] = parsed
				for e in parsed.get("entries", []):
					my_entries[str(e.get("id", ""))] = e
	kit.ok(task_files.size() >= 4, "tasks_*.json files present (%d)" % task_files.size())
	var mine: Array = []
	for w in real.warnings:
		var s := str(w)
		var hit := s.contains("tasks_") or s.contains("requires") or s.begins_with("task ")
		for id in my_entries:
			hit = hit or s.contains("'%s'" % id)
		if hit:
			mine.append(s)
	kit.eq(mine, [], "Explore validation of the real data: no task / requires problems")
	for lid in LEVELS:
		var ps = load("res://scenes/levels/%s.tscn" % lid)
		if not kit.ok(ps is PackedScene, "%s loads" % lid):
			continue
		scenes[lid] = _nodes_of(ps)
		var env := "res://assets/environments/%s/" % LEVELS[lid]["env"]
		var m = JSON.parse_string(FileAccess.get_file_as_string(env + "scene.json"))
		manifests[lid] = m if m is Dictionary else {}
		var hs := {}
		var x = JSON.parse_string(FileAccess.get_file_as_string(env + "explore_hotspots.json")) \
			if FileAccess.file_exists(env + "explore_hotspots.json") else null
		if x is Dictionary and x.get("hotspots") is Dictionary:
			hs.merge(x["hotspots"], true)
		if manifests[lid].get("hotspots") is Dictionary:
			hs.merge(manifests[lid]["hotspots"], true)     # scene.json wins (Level._merge_explore_hotspots)
		hotspots[lid] = hs
	return true


static func _nodes_of(ps: PackedScene) -> Array:
	var out: Array = []
	var st: SceneState = ps.get_state()
	for i in st.get_node_count():
		var props := {}
		var script_path := ""
		for j in st.get_node_property_count(i):
			var pn := str(st.get_node_property_name(i, j))
			var pv = st.get_node_property_value(i, j)
			if pn == "script":
				script_path = pv.resource_path if pv is Resource else ""
			else:
				props[pn] = pv
		out.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props})
	return out


## Exploration nodes of a level: {name, gated, kind, explore_id, chain (Array), hotspot_id, pos, radius, props}.
func _explore_nodes(lid: String) -> Array:
	var out: Array = []
	for n in scenes.get(lid, []):
		if n["script"] != INTERACTABLE_PATH and n["script"] != GATED_PATH:
			continue
		var p: Dictionary = n["props"]
		var kind := str(p.get("kind", "inspect"))
		if kind != "discover" and kind != "chat":
			continue
		var chain: Array = Array(p.get("explore_chain", PackedStringArray()))
		out.append({"name": n["name"], "gated": n["script"] == GATED_PATH, "kind": kind,
			"explore_id": str(p.get("explore_id", "")), "chain": chain.map(func(c): return str(c)),
			"hotspot_id": str(p.get("hotspot_id", "")), "pos": _pos(lid, p), "radius": float(p.get("radius", 30.0)),
			"props": p})
	return out


func _pos(lid: String, p: Dictionary) -> Vector2:
	var hs: Dictionary = hotspots.get(lid, {})
	var h = hs.get(str(p.get("hotspot_id", "")), null)
	if not (h is Array) or h.size() < 2:
		return Vector2.INF
	return Vector2(float(h[0]), float(h[1])) + (p.get("hotspot_offset", Vector2.ZERO) as Vector2)


func _live() -> bool:
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if not kit.ok(ex != null and ex.has_method("task_state"), "Explore autoload with the task API"):
		return true
	var saved: Dictionary = ex.state()
	var notify: bool = ex.notify_tasks
	ex.notify_tasks = false
	ex.reset()
	var fam: Node = INTERACTABLE.new()
	fam.kind = "chat"
	fam.explore_id = "karsk.family"
	fam.explore_chain = PackedStringArray(["karsk.family", "karsk.task.train.return"])
	kit.mount(fam)
	var box: Node = INTERACTABLE.new()
	box.kind = "discover"
	box.explore_id = "karsk.task.train.signalbox"
	kit.mount(box)
	kit.eq(fam.explore_id, "karsk.family", "chain starts on its first entry")
	kit.ok(fam.is_active(), "first entry active")
	kit.eq(fam.prompt_state(), "task", "a task step that is not found yet: prompt mark 'task'")
	kit.ok(not box.is_active(), "a step with unmet requirements keeps its hotspot inactive")
	ex.find("karsk.family")
	kit.ok(box.is_active(), "requirement found -> the next step's hotspot is active")
	kit.eq(fam.explore_id, "karsk.family", "chain waits on the found entry while the next one is blocked")
	kit.eq(fam.prompt_state(), "found", "re-readable entry: prompt mark 'found'")
	kit.eq(AUTOPLAY.pending_finds([fam, box], ex), [box], "pending_finds: only what records something new now")
	ex.find("karsk.task.train.signalbox")
	ex.find("karsk.task.train.vendor")
	kit.eq(fam.explore_id, "karsk.task.train.return", "requirement met -> the chain moves on (Explore.state_changed)")
	kit.eq(fam.prompt_state(), "task", "next step marked as a task step")
	kit.eq(AUTOPLAY.pending_finds([fam, box], ex), [fam], "pending_finds follows the chain")
	# once: hidden after use, re-armed when the chain moves to an unfound entry
	var buf: Node = INTERACTABLE.new()
	buf.kind = "discover"
	buf.once = true
	buf.explore_id = "veltrava.hall.buffet"
	buf.explore_chain = PackedStringArray(["veltrava.hall.buffet", "veltrava.task.buffet.take"])
	kit.mount(buf)
	buf.used = true                          # what Game._do_discover does before Explore.find
	ex.find("veltrava.hall.buffet")
	kit.ok(not buf.is_active(), "once + used + next entry blocked -> hidden")
	ex.find("veltrava.hall.chat_typist")
	ex.find("veltrava.task.buffet.ask")
	kit.eq(buf.explore_id, "veltrava.task.buffet.take", "task started -> the buffet hosts the task step")
	kit.ok(buf.is_active() and not buf.used, "a once hotspot is re-armed for its next entry")
	# the node's kind follows its current entry (chat <-> discover)
	var mix: Node = INTERACTABLE.new()
	mix.kind = "discover"
	mix.explore_id = "karsk.cat"
	mix.explore_chain = PackedStringArray(["karsk.cat", "karsk.vendor"])
	kit.mount(mix)
	kit.eq(mix.kind, "discover", "kind of the first (detail) entry")
	ex.find("karsk.cat")
	kit.eq([mix.explore_id, mix.kind], ["karsk.vendor", "chat"], "kind follows the chat entry")
	ex.reset()
	kit.eq(fam.explore_id, "karsk.family", "reset: chain back on its first entry")
	ex.restore(saved)
	ex.notify_tasks = notify
	return true


func _five() -> bool:
	var tasks: Array = real.tasks_for("") if real != null else []
	kit.eq(tasks.size(), 5, "five side tasks")
	var per := {}
	for t in tasks:
		var lid := str(t.get("level", ""))
		per[lid] = int(per.get(lid, 0)) + 1
		var steps: Array = real.task_steps(str(t["id"]))
		kit.ok(steps.size() >= 3 and steps.size() <= 6, "%s: 3-6 steps (talk, search/do, return)" % t["id"])
		for sid in steps:
			kit.eq(str(real.entry(str(sid)).get("level", "")), lid, "%s: step %s belongs to %s" % [t["id"], sid, lid])
		var last: Dictionary = real.entry(str(steps[steps.size() - 1])) if not steps.is_empty() else {}
		kit.eq(str(last.get("kind", "")), "chat", "%s: ends with a closing conversation" % t["id"])
		kit.eq(str(real.entry(str(steps[0])).get("kind", "")), "chat", "%s: starts with a conversation" % t["id"])
	for lid in LEVELS:
		kit.eq(int(per.get(lid, 0)), 1, "exactly one task in %s" % lid)
	return true


func _placed() -> bool:
	var count := {}
	for lid in LEVELS:
		for n in _explore_nodes(lid):
			var ids: Array = n["chain"] if not n["chain"].is_empty() else [n["explore_id"]]
			var ours := false
			for id in ids:
				ours = ours or str(id) in my_entries or (real.has_entry(str(id)) and real.task_of(str(id)) != "")
			if not ours:
				continue    # nodes without task steps belong to the area tests
			if not n["chain"].is_empty():
				var fresh := MockEx.new()      # a new game: nothing found
				for id in real._entries:
					fresh.req[str(id)] = real.requires_of(str(id))
				kit.eq(n["explore_id"], INTERACTABLE.pick_chain_step(PackedStringArray(n["chain"]), fresh),
					"%s/%s: the scene's explore_id is the entry its chain shows in a new game" % [lid, n["name"]])
			for id in ids:
				if not kit.ok(real.has_entry(str(id)), "%s/%s: entry %s exists" % [lid, n["name"], id]):
					continue
				kit.eq(str(real.entry(str(id)).get("level", "")), lid, "%s/%s: %s belongs to this level" % [lid, n["name"], id])
				count[str(id)] = (count.get(str(id), []) as Array) + ["%s/%s" % [lid, n["name"]]]
			var first := str(n["explore_id"])
			if real.has_entry(first):
				kit.eq(n["kind"], "chat" if str(real.entry(first).get("kind", "")) == "chat" else "discover",
					"%s/%s: node kind matches its starting entry" % [lid, n["name"]])
	for t in real.tasks_for(""):
		for sid in real.task_steps(str(t["id"])):
			kit.eq((count.get(str(sid), []) as Array).size(), 1, "task step %s placed exactly once %s" % [sid, count.get(str(sid), [])])
	for id in my_entries:
		kit.ok(count.has(id), "task entry %s is placed in its level" % id)
	return true


## The drivers' loop on the parsed scenes: re-collect the hotspots whose current entry is new and findable until
## nothing changes. Story gates are open as in the final pass (every objective of the level but its last one).
func _drivers() -> bool:
	var quests = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/quests.json"))
	for lid in LEVELS:
		var done_obj := {}
		if quests is Dictionary:
			for q in quests.get("quests", []):
				if str(q.get("scene", "")) == lid:
					var objs: Array = q.get("objectives", [])
					for i in objs.size() - 1:
						done_obj[str(objs[i]["id"])] = true
		var nodes := _explore_nodes(lid)
		var m := MockEx.new()
		for id in real._entries:
			m.req[str(id)] = real.requires_of(str(id))
		var order: Array = []
		var guard := 0
		var progressed := true
		while progressed and guard < 200:
			guard += 1
			progressed = false
			for n in nodes:
				var p: Dictionary = n["props"]
				if str(p.get("after_objective", "")) != "" and not done_obj.has(str(p["after_objective"])):
					continue
				if str(p.get("until_objective", "")) != "" and done_obj.has(str(p["until_objective"])):
					continue
				var cur := INTERACTABLE.pick_chain_step(PackedStringArray(n["chain"]), m) if not n["chain"].is_empty() else str(n["explore_id"])
				if cur == "" or m.found.has(cur) or not m.can_find(cur):
					continue
				m.found[cur] = true
				order.append(cur)
				progressed = true
		for t in real.tasks_for(lid):
			var steps: Array = real.task_steps(str(t["id"]))
			var got: Array = order.filter(func(x): return x in steps)
			kit.eq(got, steps, "%s: the drivers' loop completes %s in step order" % [lid, t["id"]])
		for n in nodes:
			for id in (n["chain"] if not n["chain"].is_empty() else [n["explore_id"]]):
				if str(id) in my_entries:
					kit.ok(m.found.has(str(id)), "%s: %s is reached by the loop" % [lid, id])
	return true


func _texts() -> bool:
	var lf = JSON.parse_string(FileAccess.get_file_as_string(LOCALE))
	if not kit.ok(lf is Dictionary and lf.get("strings") is Dictionary, "de_tasks.json parses"):
		return true
	kit.eq(str(lf.get("locale", "")), "de-DE", "locale tag")
	var strings: Dictionary = lf["strings"]
	var used := {}
	var mine := func(key: String, what: String, max_len: int) -> void:
		used[key] = true
		if kit.ok(loc.has(key), "%s: '%s' has text" % [what, key]):
			kit.ok(loc.source_of(key).ends_with("de_tasks.json"), "'%s' comes from de_tasks.json" % key)
			kit.ok(loc.t(key).length() <= max_len, "%s: '%s' is at most %d characters (%d)" % [what, key, max_len, loc.t(key).length()])
	for id in my_entries:
		var e: Dictionary = my_entries[id]
		mine.call(str(e.get("title_key", "")), id + " title", 32)
		mine.call(str(e.get("prompt_key", "")), id + " prompt", 32)
		mine.call(str(e.get("text_key", "")), id + " text", 520 if str(e.get("kind", "")) != "chat" else 240)
		for l in e.get("lines", []):
			mine.call(str(l.get("key", "")), id + " line", 200)
	for t in real.tasks_for(""):
		mine.call(str(t.get("title_key", "")), str(t["id"]) + " title", 32)
		mine.call(str(t.get("summary_key", "")), str(t["id"]) + " summary", 200)
		for s in t.get("steps", []):
			mine.call(str(s.get("hint_key", "")), str(t["id"]) + " hint", 120)
	var code := FileAccess.get_file_as_string("res://scripts/ui/journal.gd") + FileAccess.get_file_as_string(EXPLORE)
	for key in strings:
		var k := str(key)
		var ok_use: bool = used.has(k) or code.contains("\"%s\"" % k)
		if k.begins_with("ui.tasks.place."):
			ok_use = LEVELS.has(k.trim_prefix("ui.tasks.place."))
		elif k.begins_with("ui.journal.tab."):
			ok_use = k.trim_prefix("ui.journal.tab.") in JOURNAL.TABS
		elif k.begins_with("ui.tasks.kicker."):
			ok_use = k.trim_prefix("ui.tasks.kicker.") in ["active", "done"]
		kit.ok(ok_use, "locale string '%s' is used" % k)
		var s := str(strings[key])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' is not empty and has no stray spaces" % k)
		kit.ok(not s.contains("\""), "'%s': German quotes („…“), not \"…\"" % k)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % k)
		kit.ok(not s.contains("..."), "'%s': ellipsis as '…'" % k)
		kit.ok(s.count("„") == s.count("“") and s.count("‚") == s.count("‘"), "'%s': balanced German quotes" % k)
	var old: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	if kit.ok(old != "", "pre-rename id derivable"):
		var raw := FileAccess.get_file_as_string(LOCALE).to_lower()
		for f in task_files:
			raw += FileAccess.get_file_as_string(EXPLORE_DIR + str(f)).to_lower()
		kit.ok(not raw.contains(old), "task texts and data never use the pre-rename name")
	return true


func _chats() -> bool:
	for id in my_entries:
		var e: Dictionary = my_entries[id]
		var lid := str(e.get("level", ""))
		if str(e.get("kind", "")) != "chat":
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
			continue
		var lines: Array = e.get("lines", [])
		kit.ok(lines.size() >= 4 and lines.size() <= 9, "%s: 4-9 lines (%d)" % [id, lines.size()])
		var speakers := {}
		for l in lines:
			var sp := str(l.get("speaker", ""))
			speakers[sp] = true
			kit.ok(DirAccess.dir_exists_absolute("res://assets/characters/" + sp), "%s: speaker %s has a character folder" % [id, sp])
			kit.ok(loc.has("char.%s.name" % sp), "%s: speaker %s has a German name" % [id, sp])
			kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression %s" % [id, l.get("expr", "")])
		kit.ok(speakers.has(str(LEVELS.get(lid, {}).get("hero", ""))), "%s: the level's protagonist speaks" % id)
		kit.ok(speakers.size() >= 2, "%s: a conversation, not a monologue" % id)
	# the NPC a chat hotspot turns to speaks in every chat entry of that hotspot
	for lid in LEVELS:
		for n in _explore_nodes(lid):
			var npc := str(n["props"].get("npc_id", ""))
			if npc == "":
				continue
			for id in (n["chain"] if not n["chain"].is_empty() else [n["explore_id"]]):
				var e: Dictionary = real.entry(str(id))
				if str(e.get("kind", "")) != "chat" or not (str(id) in my_entries):
					continue
				var sp: Array = (e.get("lines", []) as Array).map(func(l): return str(l.get("speaker", "")))
				kit.ok(npc in sp, "%s/%s: npc_id %s speaks in %s" % [lid, n["name"], npc, id])
	return true


## New task hotspots: in the walk area, outside prop collisions, clear of story spots and other finds. A task chat
## that shares a story NPC's spot must be gated after that NPC's story objective (they never compete).
func _hotspots() -> bool:
	for lid in LEVELS:
		var rule: Dictionary = LEVELS[lid]
		var man: Dictionary = manifests.get(lid, {})
		var walk := PackedVector2Array()
		for q in man.get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		var story: Array = []
		for n in scenes.get(lid, []):
			if (n["script"] == INTERACTABLE_PATH or n["script"] == GATED_PATH) and str(n["props"].get("kind", "inspect")) in STORY_KINDS:
				story.append({"name": n["name"], "pos": _pos(lid, n["props"]), "hotspot": str(n["props"].get("hotspot_id", "")),
					"objective": str(n["props"].get("objective_id", ""))})
		var finds := _explore_nodes(lid)
		for f in finds:
			if not (f["explore_id"] in my_entries):
				continue
			var who := "%s/%s" % [lid, f["name"]]
			var p: Vector2 = f["pos"]
			if not kit.ok(p.is_finite(), "%s: hotspot %s resolves" % [who, f["hotspot_id"]]):
				continue
			if walk.size() >= 3:
				kit.ok(Geometry2D.is_point_in_polygon(p, walk), "%s at %s lies in the walk area" % [who, p])
			for pr in man.get("props", []):
				var c = pr.get("collision", []) if pr is Dictionary else []
				if c is Array and c.size() >= 3:
					var poly := PackedVector2Array()
					for q in c:
						poly.append(Vector2(float(q[0]), float(q[1])))
					kit.ok(not Geometry2D.is_point_in_polygon(p, poly), "%s is outside the collision of %s" % [who, pr.get("name", "")])
			for s in story:
				if s["hotspot"] == f["hotspot_id"]:
					kit.eq(str(f["props"].get("after_objective", "")), s["objective"],
						"%s shares %s's spot: gated after %s" % [who, s["name"], s["objective"]])
					continue
				if s["pos"].is_finite():
					kit.ok(_dist(p, s["pos"], rule["oblique"]) >= rule["gap_story"], "%s keeps %d px from story spot %s (%.1f)" % [who,
						int(rule["gap_story"]), s["name"], _dist(p, s["pos"], rule["oblique"])])
			for o in finds:
				if o["name"] == f["name"] or not o["pos"].is_finite() or o["hotspot_id"] == f["hotspot_id"]:
					continue
				kit.ok(_dist(p, o["pos"], rule["oblique"]) >= rule["gap_find"], "%s keeps %d px from %s (%.1f)" % [who,
					int(rule["gap_find"]), o["name"], _dist(p, o["pos"], rule["oblique"])])
	return true


static func _dist(a: Vector2, b: Vector2, oblique: bool) -> float:
	return Vector2(a.x - b.x, (a.y - b.y) * (OBLIQUE_Y if oblique else 1.0)).length()


func _image() -> bool:
	for id in my_entries:
		var img := str(my_entries[id].get("image", ""))
		if img == "":
			continue
		kit.ok(img.begins_with("res://assets/explore/tasks/"), "%s: close-up lives in assets/explore/tasks/" % id)
		if not kit.ok(FileAccess.file_exists(img), "%s: %s exists" % [id, img]):
			continue
		var im := Image.load_from_file(ProjectSettings.globalize_path(img))
		if kit.ok(im != null and not im.is_empty(), "%s: close-up loads" % id):
			kit.ok(im.get_width() <= 320 and im.get_height() <= 200, "%s: %dx%d fits 320x200" % [id, im.get_width(), im.get_height()])
	return true
