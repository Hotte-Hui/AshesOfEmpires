extends RefCounted
## Port of preproduction/tests/test_story_engine_v4.py (StoryV4Tests, 13 tests) against the GDScript
## engine. Same scenarios, inputs and assertions; Python exceptions become {ok: false} results.

const Kit := preload("res://tests/support/test_kit.gd")
const Legacy := preload("res://tests/support/legacy_runtime_v2.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("test_fresh_gates", _test_fresh_gates)
	kit.run_case("test_explicit_dialogue", _test_explicit_dialogue)
	kit.run_case("test_dialogue_resume_exact_node", _test_dialogue_resume_exact_node)
	kit.run_case("test_puzzle_wrong_then_hint", _test_puzzle_wrong_then_hint)
	kit.run_case("test_puzzle_payload_is_typed", _test_puzzle_payload_is_typed)
	kit.run_case("test_valid_branch_combinations", _test_valid_branch_combinations)
	kit.run_case("test_fade_skip_does_not_skip_story", _test_fade_skip_does_not_skip_story)
	kit.run_case("test_cinematics_available_only_when_triggered", _test_cinematics_available_only_when_triggered)
	kit.run_case("test_invalid_choice_no_mutation", _test_invalid_choice_no_mutation)
	kit.run_case("test_invalid_save_is_atomic", _test_invalid_save_is_atomic)
	kit.run_case("test_bad_save_corruption_detected", _test_bad_save_corruption_detected)
	kit.run_case("test_v03_save_migration", _test_v03_save_migration)
	kit.run_case("test_unknown_presentation_cursor_rejected", _test_unknown_presentation_cursor_rejected)
	kit.run_case("test_preserve_attempts_on_reload", _test_preserve_attempts_on_reload)
	kit.cleanup()
	return kit.failures


func _test_fresh_gates() -> bool:
	var r := kit.story()
	kit.eq(r.available(), ["a1_talk_irina"], "fresh available")
	kit.is_err(r.inspect("a1_inspect_seal"), "seal is gated behind Irina")
	kit.is_err(r.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"]), "puzzle gated")
	kit.is_err(r.finale(), "finale gated")
	return true


func _test_explicit_dialogue() -> bool:
	var r := kit.story()
	var line: Dictionary = r.start_dialogue("a1_talk_irina")
	kit.eq(line.get("node"), "irina_01", "entry node")
	kit.eq(r.current_dialogue_line("a1_talk_irina").get("node"), "irina_01", "current line")
	kit.ok(not r.state["completed_objectives"].has("a1_talk_irina"), "not complete after start")
	var count := 0
	while r.state["dialogue_progress"].has("a1_talk_irina") and count < 50:
		kit.is_ok(r.advance_dialogue("a1_talk_irina"), "advance")
		count += 1
	kit.eq(count, 5, "advance count")
	kit.ok(r.state["completed_objectives"].has("a1_talk_irina"), "complete at terminal node")
	kit.is_err(r.advance_dialogue("a1_talk_irina"), "cannot advance a finished dialogue")
	return true


func _test_dialogue_resume_exact_node() -> bool:
	var r := kit.story()
	r.start_dialogue("a1_talk_irina")
	r.advance_dialogue("a1_talk_irina")
	var save: String = r.save_json()
	var s := kit.story()
	kit.is_ok(s.load_json(save), "load mid-dialogue")
	kit.eq(s.current_dialogue_line("a1_talk_irina").get("node"), "alexei_01", "resumed node")
	kit.ok(not s.state["completed_objectives"].has("a1_talk_irina"), "still incomplete")
	return true


func _test_puzzle_wrong_then_hint() -> bool:
	var r := kit.story()
	kit.get_to_signal(r)
	kit.eq(r.puzzle_hint_available("a1_solve_signal"), false, "no hint at start")
	var w1: Dictionary = r.solve_puzzle("a1_solve_signal", ["circle", "square", "triangle"])
	kit.is_ok(w1, "wrong answer is a valid call")
	kit.eq(w1.get("solved"), false, "wrong 1")
	kit.eq(r.puzzle_hint_available("a1_solve_signal"), false, "no hint after 1")
	kit.eq(r.solve_puzzle("a1_solve_signal", ["circle", "triangle", "square"]).get("solved"), false, "wrong 2")
	kit.eq(r.puzzle_hint_available("a1_solve_signal"), true, "hint after 2")
	kit.eq(r.state["puzzle_attempts"]["a1_solve_signal"], 2, "attempts")
	kit.eq(r.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"]).get("solved"), true, "solve")
	kit.eq(r.state["flags"]["signal_restored"], true, "signal_restored")
	kit.is_err(r.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"]), "cannot solve twice")
	return true


func _test_puzzle_payload_is_typed() -> bool:
	var r := kit.story()
	kit.get_to_signal(r)
	for invalid in [1, "square,circle,triangle", {"a": 0}, [false, "circle", "triangle"]]:
		kit.is_err(r.solve_puzzle("a1_solve_signal", invalid), "invalid payload %s" % Kit.fmt(invalid))
	kit.eq(r.puzzle_attempts("a1_solve_signal"), 0, "malformed payloads are not attempts")
	return true


## The verified route now runs through Chapter 3 (default options ask_elena / share_protocol) before the
## finale: 5 events, 12 items, 24 objectives, 4 choices.
func _test_valid_branch_combinations() -> bool:
	for a in ["share_with_irina", "keep_private"]:
		for m in ["preserve_evidence", "request_explanation"]:
			var label := "%s/%s" % [a, m]
			var r := kit.play_verified_route(a, m)
			kit.eq(r.state["completed_events"], ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed",
				"slice_completed"], label + " events")
			kit.eq(r.state["inventory"].size(), 12, label + " inventory")
			kit.eq(r.state["completed_objectives"].size(), 24, label + " objectives")
			kit.eq(r.state["flags"]["slice_finished"], true, label + " slice_finished")
			kit.eq(r.state["choice_history"], {"a1_choose": a, "m1_choose": m, "c3a_choose": "ask_elena",
				"c3b_choose": "share_protocol"}, label + " choices")
			kit.eq(r.pending_cinematics(), [], label + " cinematics consumed")
			var reload := kit.story()
			kit.eq(reload.load_json(r.save_json()).get("state"), r.snapshot(), label + " reload equals snapshot")
	return true


func _test_fade_skip_does_not_skip_story() -> bool:
	var a := kit.play_verified_route("share_with_irina", "preserve_evidence", false)
	var b := kit.play_verified_route("share_with_irina", "preserve_evidence", true)
	kit.eq(a.snapshot(), b.snapshot(), "skip equivalence")
	return true


func _test_cinematics_available_only_when_triggered() -> bool:
	var r := kit.story()
	kit.is_err(r.consume_cinematic("LS_A1_ToM1"), "not unlocked yet")
	kit.get_to_signal(r)
	r.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"])
	r.inspect("a1_inspect_ledger")
	r.choose("a1_choose", "share_with_irina")
	kit.eq(r.pending_cinematics(), ["LS_A1_ToM1"], "queued")
	kit.is_ok(r.consume_cinematic("LS_A1_ToM1", true), "consume skipped")
	kit.eq(r.pending_cinematics(), [], "consumed")
	kit.is_err(r.consume_cinematic("LS_A1_ToM1"), "once only")
	return true


func _test_invalid_choice_no_mutation() -> bool:
	var r := kit.story()
	kit.get_to_signal(r)
	r.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"])
	r.inspect("a1_inspect_ledger")
	var original: Dictionary = r.snapshot()
	kit.is_err(r.choose("a1_choose", "unspecified"), "invalid choice")
	kit.eq(r.snapshot(), original, "no mutation")
	return true


func _test_invalid_save_is_atomic() -> bool:
	var r := kit.story()
	var original: Dictionary = r.snapshot()
	var cases := ["", "[]", "{}", "{\"save_version\":999}", "{" + "x".repeat(200000) + "}"]
	for c in cases:
		kit.is_err(r.load_json(c), "case %s" % (c as String).substr(0, 20))
		kit.eq(r.snapshot(), original, "state untouched after %s" % (c as String).substr(0, 20))
	return true


func _test_bad_save_corruption_detected() -> bool:
	var route := kit.play_verified_route()
	var valid: Dictionary = Kit.parse(route.save_json())
	var edits := {
		"flags": func(x: Dictionary) -> void: x["flags"]["c17_confirmed"] = false,
		"events": func(x: Dictionary) -> void: x["completed_events"].erase("a1_completed"),
		"unknown_item": func(x: Dictionary) -> void: x["inventory"].append("forged"),
		"wrong_scene": func(x: Dictionary) -> void: x["current_scene"] = "L_A1_Railyard",
		"character": func(x: Dictionary) -> void: x["active_character"] = "alexei",
		"tampered_choice": func(x: Dictionary) -> void: x["choice_history"]["m1_choose"] = "fake",
		"dup_objective": func(x: Dictionary) -> void: x["completed_objectives"].append("a1_choose"),
		"bad_sequence": func(x: Dictionary) -> void: x["cinematics_seen"].append("invalid"),
		"unexpected_finale": func(x: Dictionary) -> void: x["finale_viewed"] = "yes",
	}
	var r := kit.story()
	for label in edits:
		var record: Dictionary = valid.duplicate(true)
		(edits[label] as Callable).call(record)
		kit.is_err(r.load_json(Kit.dumps(record)), "corruption " + label)
	return true


## Python: legacy_play() (the v0.3 route up to its finale) migrates. Since Chapter 3 follows M1, that save claims
## the old demo end and the reference itself rejects it ("Finale locked", recorded in the parity fixture);
## the same assertions now run on the latest v0.3 save before that end (M1 decision pending).
func _test_v03_save_migration() -> bool:
	var r := kit.story()
	var before: Dictionary = r.snapshot()
	var end: Dictionary = r.load_json(Legacy.play_route().save_json())
	kit.is_err(end, "v2 save at the old demo end is rejected")
	kit.eq(end.get("error"), "Finale locked", "reference message")
	kit.eq(r.snapshot(), before, "rejected load is atomic")
	var rt := Legacy.new()
	for o in ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger",
			"a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans", "m1_talk_emil"]:
		rt.perform(o, "share_with_irina" if o == "a1_choose" else null)
	var res: Dictionary = r.load_json(rt.save_json())
	kit.is_ok(res, "v2 save loads")
	var st: Dictionary = res.get("state", {})
	kit.eq(st.get("save_version"), 3, "migrated version")
	kit.eq(st.get("flags", {}).get("irina_trust"), 1, "irina_trust kept")
	kit.eq(st.get("flags", {}).get("elena_trust"), 0, "Chapter-3 flag takes its default")
	kit.eq(st.get("completed_events"), ["a1_completed"], "events")
	kit.eq(r.pending_cinematics(), ["LS_A1_ToM1", "LS_M1_Hall"], "cinematics pending after migration")
	kit.eq(kit.story().load_json(r.save_json()).get("state"), st, "v3 round trip")
	return true


func _test_unknown_presentation_cursor_rejected() -> bool:
	var game := kit.story()
	game.start_dialogue("a1_talk_irina")
	var doc: Dictionary = Kit.parse(game.save_json())
	doc["dialogue_progress"]["a1_talk_irina"] = "missing_node"
	kit.is_err(kit.story().load_json(Kit.dumps(doc)), "unknown cursor")
	return true


func _test_preserve_attempts_on_reload() -> bool:
	var r := kit.story()
	kit.get_to_signal(r)
	r.solve_puzzle("a1_solve_signal", ["triangle", "square", "circle"])
	var loaded := kit.story()
	kit.is_ok(loaded.load_json(r.save_json()), "reload")
	kit.eq(loaded.state["puzzle_attempts"].get("a1_solve_signal"), 1, "attempts preserved")
	return true
