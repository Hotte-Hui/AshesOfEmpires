extends RefCounted
## API robustness of the Story engine: odd argument types, typed puzzle payloads, read-only views,
## definition accessors, the invalid-data guard, plus a seeded random-action fuzz test that checks the
## story invariants (prerequisites, once-only items/events, scene↔protagonist, flag bounds, reload).

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("odd_argument_types", _odd_arguments)
	kit.run_case("typed_overlay_payloads", _overlay_payloads)
	kit.run_case("symbol_payload_variants", _symbol_payloads)
	kit.run_case("dialogue_api_shape_and_resume", _dialogue_shape)
	kit.run_case("read_only_views_and_copies", _read_only)
	kit.run_case("definition_accessors", _accessors)
	kit.run_case("error_results_carry_keys", _error_keys)
	kit.run_case("clue_ownership_enforced", _clue_ownership)
	kit.run_case("invalid_data_disables_engine_cleanly", _invalid_data_guard)
	kit.run_case("random_action_fuzz_invariants", _fuzz)
	kit.cleanup()
	return kit.failures


func _ready_for_choice(g: Node) -> void:
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")


func _to_m1_overlay(g: Node) -> void:
	_ready_for_choice(g)
	g.choose("a1_choose", "share_with_irina")
	g.inspect("m1_inspect_plan_a")
	g.inspect("m1_inspect_plan_b")


func _odd_arguments() -> bool:
	var g := kit.story()
	var r: Dictionary = g.inspect(123)
	kit.is_err(r, "int id")
	kit.eq(r.get("error"), "Unknown objective: 123", "Python-identical message")
	kit.is_err(g.inspect(null), "null id")
	kit.is_err(g.start_dialogue(["a1_talk_irina"]), "array id")
	kit.is_ok(g.start_dialogue(&"a1_talk_irina"), "StringName id accepted")
	kit.eq(g.objective_state(42), "locked", "objective_state of a non-string")
	kit.eq(g.objective_state("nope"), "locked", "objective_state of an unknown id")
	kit.eq(g.is_available(null), false, "is_available(null)")
	kit.eq(g.flag(3), null, "flag(3)")
	kit.eq(g.flag("nope"), null, "unknown flag")
	kit.eq(g.has_item(null), false, "has_item(null)")
	kit.is_err(g.consume_cinematic(7), "int cinematic")
	kit.eq(g.puzzle_hint_available("a1_talk_irina"), false, "hint on a non-puzzle")
	kit.eq(g.puzzle_attempts(null), 0, "attempts(null)")
	var h := kit.story()
	_ready_for_choice(h)
	kit.eq(h.choose("a1_choose", 5).get("error"), "Invalid choice ID", "int choice")
	kit.eq(h.choose("a1_choose", null).get("error"), "Invalid choice ID", "null choice")
	kit.is_ok(h.choose("a1_choose", &"keep_private"), "StringName choice")
	kit.eq(h.choice_history(), {"a1_choose": "keep_private"}, "stored as String")
	kit.eq(typeof(h.choice_history()["a1_choose"]), TYPE_STRING, "String type in the save")
	return true


func _overlay_payloads() -> bool:
	var g := kit.story()
	_to_m1_overlay(g)
	var cases := [
		[{"rotation_steps": 0, "offset_x": 2, "offset_y": -1.0}, "Overlay coordinates must be integers"],
		[{"rotation_steps": true, "offset_x": 2, "offset_y": -1}, "Overlay coordinates must be integers"],
		[{"rotation_steps": 0, "offset_x": 2}, "Overlay expects rotation_steps, offset_x, offset_y"],
		[{"rotation_steps": 0, "offset_x": 2, "offset_y": -1, "z": 0}, "Overlay expects rotation_steps, offset_x, offset_y"],
		[{0: 0, "offset_x": 2, "offset_y": -1}, "Overlay expects rotation_steps, offset_x, offset_y"],
		[[0, 2, -1], "Overlay expects rotation_steps, offset_x, offset_y"],
		[Vector3i(0, 2, -1), "Overlay expects rotation_steps, offset_x, offset_y"],
	]
	for c in cases:
		var r: Dictionary = g.solve_puzzle("m1_align_plans", c[0])
		kit.is_err(r, "payload %s" % Kit.fmt(c[0]))
		kit.eq(r.get("error"), c[1], "message for %s" % Kit.fmt(c[0]))
	kit.eq(g.puzzle_attempts("m1_align_plans"), 0, "malformed payloads are not attempts")
	kit.eq(g.solve_puzzle("m1_align_plans", {"rotation_steps": 1, "offset_x": 2, "offset_y": -1}).get("solved"), false, "wrong rotation")
	kit.eq(g.solve_puzzle("m1_align_plans", {"rotation_steps": 0, "offset_x": -2, "offset_y": 1}).get("solved"), false, "mirrored offset")
	var w: Dictionary = g.solve_puzzle("m1_align_plans", {"rotation_steps": 0, "offset_x": 2, "offset_y": 0})
	kit.eq([w.get("solved"), w.get("attempts"), w.get("hint_available")], [false, 3, true], "third failure, hint available")
	var ok: Dictionary = g.solve_puzzle("m1_align_plans", {&"offset_y": -1, &"offset_x": 2, &"rotation_steps": 0})
	kit.eq(ok.get("solved"), true, "StringName keys, any key order")
	kit.eq(g.flag("blueprint_match_confirmed"), true, "effect applied")
	return true


func _symbol_payloads() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	kit.eq(g.solve_puzzle("a1_solve_signal", ["square", "circle"]).get("solved"), false, "too short counts as an attempt")
	kit.eq(g.solve_puzzle("a1_solve_signal", []).get("solved"), false, "empty list counts as an attempt")
	kit.is_err(g.solve_puzzle("a1_solve_signal", ["square", 1, "triangle"]), "mixed list")
	kit.is_err(g.solve_puzzle("a1_solve_signal", {"0": "square"}), "dict")
	kit.eq(g.puzzle_attempts("a1_solve_signal"), 2, "two attempts")
	kit.eq(g.solve_puzzle("a1_solve_signal", PackedStringArray(["square", "circle", "triangle"])).get("solved"), true,
		"PackedStringArray is a list of strings")
	return true


func _dialogue_shape() -> bool:
	var g := kit.story()
	var s: Dictionary = g.start_dialogue("a1_talk_irina")
	kit.eq(s, {"ok": true, "error": "", "error_key": "", "objective": "a1_talk_irina", "node": "irina_01", "id": "irina_01",
		"speaker": "irina", "text_key": "dlg.irina.01", "end": false, "next": "alexei_01"}, "start_dialogue result")
	var line: Dictionary = g.current_dialogue_line("a1_talk_irina")
	kit.ok(not line.has("error"), "no 'error' key on a valid line (game.gd checks line.has(\"error\"))")
	kit.eq(line.get("speaker"), "irina", "speaker")
	var adv: Dictionary = g.advance_dialogue("a1_talk_irina")
	kit.eq([adv.get("finished"), adv.get("node"), adv.get("speaker")], [false, "alexei_01", "alexei"], "advance returns the next line")
	kit.eq(g.start_dialogue("a1_talk_irina").get("node"), "alexei_01", "restart resumes, never resets")
	var bad: Dictionary = g.current_dialogue_line("m1_talk_emil")
	kit.is_err(bad, "line of a dialogue that never started")
	kit.eq(bad.get("error"), "Dialogue not started", "message")
	kit.eq(g.start_dialogue("a1_inspect_seal").get("error"), "a1_inspect_seal: expected dialogue, got inspect", "wrong type message")
	return true


func _read_only() -> bool:
	var g := kit.story()
	var st: Dictionary = g.state
	st["current_scene"] = "L_X1_Montage"
	st["flags"]["irina_trust"] = 3
	kit.eq(g.current_scene, "L_A1_Railyard", "state is a copy")
	kit.eq(g.flags()["irina_trust"], 0, "flags copy")
	var f: Dictionary = g.flags()
	f["irina_trust"] = 3
	kit.eq(g.flag("irina_trust"), 0, "flags() is a copy")
	var inv: Array = g.inventory()
	inv.append("ev_ledger")
	kit.eq(g.inventory(), [], "inventory() is a copy")
	var od: Dictionary = g.objective_def("a1_choose")
	od["choices"].clear()
	kit.eq(g.choices_for("a1_choose").size(), 2, "objective_def is a copy")
	return true


func _accessors() -> bool:
	var g := kit.story()
	kit.eq(g.data_ok(), true, "data ok")
	kit.eq(g.data_error(), "", "no data error")
	kit.eq(g.choices_for("a1_choose"), [{"id": "share_with_irina", "text_key": "choice.share_irina"},
		{"id": "keep_private", "text_key": "choice.keep_private"}], "choices_for")
	kit.eq(g.choices_for("a1_talk_irina"), [], "choices_for non-choice")
	var p: Dictionary = g.puzzle_for("a1_solve_signal")
	kit.ok(not p.has("solution"), "puzzle_for hides the solution")
	kit.eq(p.get("display_symbols"), ["triangle", "square", "circle"], "display symbols")
	kit.eq(p.get("hint_after_attempts"), 2, "hint threshold")
	kit.eq(g.item_def("ev_ledger").get("name_key"), "item.ledger.name", "item_def")
	kit.eq(g.item_def("nope"), {}, "unknown item")
	kit.eq(g.quest_for("m1_choose").get("id"), "q_m1_wrong_blueprint", "quest_for")
	kit.ok(not g.quest_for("m1_choose").has("objectives"), "quest_for omits objectives")
	kit.eq(g.current_quest().get("character"), "alexei", "current quest")
	kit.eq(g.scene_def("L_M1_Archive").get("protagonist"), "konrad", "scene_def")
	kit.eq(g.cinematic_def("LS_M1_Hall").get("trigger_objective"), "m1_align_plans", "cinematic_def")
	kit.eq(g.chapter_key(), "ui.chapter_a1", "chapter a1")
	var rel: Dictionary = g.relationships()
	kit.eq(rel.keys(), ["irina_trust", "alexei_secrecy", "konrad_evidence", "office_suspicion", "civilian_welfare"], "integer flags")
	kit.eq(rel["irina_trust"], {"value": 0, "min": 0, "max": 3, "default": 0}, "meter shape")
	kit.eq(g.relationship("c17_confirmed"), 0, "boolean flag is not a meter")
	kit.eq(g.relationship("nope"), 0, "unknown meter")
	var m := kit.play_verified_route()
	kit.eq(m.current_quest(), {}, "no quest in the montage")
	kit.eq(m.chapter_key(), "world.x1.title", "montage chapter key")
	return true


func _error_keys() -> bool:
	var g := kit.story()
	var results := [g.inspect("x"), g.inspect("a1_talk_irina"), g.inspect("a1_inspect_seal"),
		g.current_dialogue_line("a1_talk_irina"), g.choose("a1_choose", "x"), g.consume_cinematic("x"), g.finale(),
		g.load_json(""), g.load_json("[]"), g.load_json("{\"save_version\": 1}"),
		g.load_json("{\"save_version\": 3, \"format\": \"x\"}"), g.load_json("{\"save_version\": 2}"),
		g.load_json("x".repeat(140000))]
	var expected_keys := ["sys.err.unknown_objective", "sys.err.wrong_type", "sys.err.locked", "sys.err.dialogue_not_started",
		"sys.err.locked", "sys.err.cinematic_locked", "sys.err.finale_locked", "sys.save.err.malformed",
		"sys.save.err.malformed", "sys.save.err.version", "sys.save.err.format", "sys.save.err.inconsistent",
		"sys.save.err.too_large"]
	for i in results.size():
		kit.eq(results[i].get("error_key"), expected_keys[i], "error key %d (%s)" % [i, results[i].get("error")])
	return true


## Unreachable through the public API with valid data (prerequisites grant the clues), so the check is
## exercised white-box by removing a clue from the engine's state.
func _clue_ownership() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.get("_core").state["inventory"].erase("ev_timetable")
	var r: Dictionary = g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	kit.is_err(r, "solution without owning every clue")
	kit.eq([r.get("error"), r.get("error_key")], ["Missing clues for puzzle", "sys.err.missing_clues"], "message and key")
	kit.eq(g.puzzle_attempts("a1_solve_signal"), 0, "not counted as an attempt")
	kit.eq(g.objective_state("a1_solve_signal"), "available", "objective not completed")
	return true


func _invalid_data_guard() -> bool:
	var broken: Dictionary = ENGINE.load_data()["data"]
	broken["scenes"]["scenes"][0]["next_scene"] = "L_X1_Montage"
	var db = ENGINE.DB.from_data(broken)
	kit.eq(db.ok, false, "broken data rejected")
	kit.ok(str(db.error) != "", "with a reason")
	var g := kit.story()
	g.set("_db", db)
	g.set("_core", null)
	for r in [g.new_game(), g.inspect("a1_inspect_seal"), g.start_dialogue("a1_talk_irina"), g.load_json("{}"),
			g.finale(), g.solve_puzzle("a1_solve_signal", []), g.choose("a1_choose", "keep_private")]:
		kit.is_err(r, "guarded call")
		kit.eq(r.get("error_key"), "sys.err.data_invalid", "data_invalid key")
	kit.eq(g.available(), [], "no objectives")
	kit.eq(g.save_json(), "", "nothing to save")
	kit.eq(g.current_scene, "", "no scene")
	kit.eq(g.journal()["objectives"], [], "empty journal")
	kit.eq(g.data_ok(), false, "data_ok false")
	return true


## Seeded random walk over the public API (valid and invalid calls) with invariant checks.
func _fuzz() -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1964
	var ids: Array = ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger",
		"a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans", "m1_talk_emil", "m1_choose", "bogus", 5]
	var answers: Array = [Kit.A1_SYMBOLS.duplicate(), ["circle", "square", "triangle"], [], Kit.M1_OVERLAY.duplicate(),
		{"rotation_steps": 1, "offset_x": 2, "offset_y": -1}, "square", null]
	var choices: Array = ["share_with_irina", "keep_private", "preserve_evidence", "request_explanation", "x"]
	var cinematics: Array = ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_nope"]
	var data: Dictionary = ENGINE.load_data()["data"]
	var objective_defs := {}
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			objective_defs[o["id"]] = [q, o]
	var finished_runs := 0
	for run_index in 12:
		var g := kit.story()
		for step_index in 400:
			var id = ids[rng.randi_range(0, ids.size() - 1)]
			match rng.randi_range(0, 9):
				0, 1:
					g.inspect(id)
				2:
					g.start_dialogue(id)
				3, 4:
					g.advance_dialogue(id)
				5:
					g.solve_puzzle(id, answers[rng.randi_range(0, answers.size() - 1)])
				6:
					g.choose(id, choices[rng.randi_range(0, choices.size() - 1)])
				7:
					g.consume_cinematic(cinematics[rng.randi_range(0, cinematics.size() - 1)], rng.randf() < 0.5)
				8:
					g.finale(rng.randf() < 0.5)
				9:
					var h := kit.story()
					if not kit.is_ok(h.load_json(g.save_json()), "fuzz reload"):
						return true
					kit.eq(h.snapshot(), g.snapshot(), "fuzz reload identical")
					h.free()
			if not _invariants(g, objective_defs, "run %d step %d" % [run_index, step_index]):
				return true
		if g.is_finished():
			finished_runs += 1
		g.free()
	kit.ok(true, "fuzz finished (%d of 12 random walks reached the finale)" % finished_runs)
	return true


func _invariants(g: Node, defs: Dictionary, where: String) -> bool:
	var s: Dictionary = g.snapshot()
	var done: Array = s["completed_objectives"]
	var seen := {}
	for i in done.size():
		var oid: String = done[i]
		if seen.has(oid):
			return kit.ok(false, "%s: duplicate objective %s" % [where, oid])
		for need in defs[oid][1].get("requires", []):
			if not seen.has(need):
				return kit.ok(false, "%s: %s completed before its prerequisite %s" % [where, oid, need])
		seen[oid] = true
	var granted := {}
	for oid in done:
		var item = defs[oid][1].get("grant_item")
		if item != null:
			granted[item] = true
	var inventory: Array = s["inventory"]
	var all_granted := inventory.all(func(x) -> bool: return granted.has(x))
	if inventory.size() != granted.size() or not all_granted:
		return kit.ok(false, "%s: inventory %s does not match granted items" % [where, inventory])
	var events: Array = s["completed_events"]
	var expect_scene := "L_A1_Railyard"
	var expect_char := "alexei"
	if events.has("a1_completed"):
		expect_scene = "L_M1_Archive"
		expect_char = "konrad"
	if events.has("m1_completed"):
		expect_scene = "L_X1_Montage"
		expect_char = "none"
	if s["current_scene"] != expect_scene or s["active_character"] != expect_char:
		return kit.ok(false, "%s: scene/character %s/%s inconsistent with events %s" % [where, s["current_scene"], s["active_character"], events])
	for e in events:
		if events.count(e) != 1:
			return kit.ok(false, "%s: event %s twice" % [where, e])
	if events.has("a1_completed") != (done.has("a1_choose") and done.size() >= 6):
		return kit.ok(false, "%s: a1_completed without all A1 objectives" % where)
	for k in ["irina_trust", "alexei_secrecy", "konrad_evidence", "office_suspicion", "civilian_welfare"]:
		if s["flags"][k] < 0 or s["flags"][k] > 3:
			return kit.ok(false, "%s: flag %s out of bounds" % [where, k])
	if s["flags"]["irina_trust"] + s["flags"]["alexei_secrecy"] > 1:
		return kit.ok(false, "%s: both A1 branches applied" % where)
	return true
