extends RefCounted
## Port of preproduction/tests/test_data_and_runtime.py.
##  * TestAuthoringData (3 tests) → the engine's validate_data() (port of tools/validate_v3.py).
##  * TestStateMachine (10 tests) → the v0.3 runtime fixture tests/support/legacy_runtime_v2.gd
##    (port of tools/simulate_slice.py), which produces the save_version 2 files the engine migrates.
## Renamed ids: the protagonist "konrad" and the flag "konrad_evidence" replace the pre-rename ids.

const Kit := preload("res://tests/support/test_kit.gd")
const Legacy := preload("res://tests/support/legacy_runtime_v2.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("TestAuthoringData.test_schema", _test_schema)
	kit.run_case("TestAuthoringData.test_detect_invalid_effect", _test_detect_invalid_effect)
	kit.run_case("TestAuthoringData.test_detect_objective_cycle", _test_detect_objective_cycle)
	kit.run_case("TestStateMachine.test_newgame", _test_newgame)
	kit.run_case("TestStateMachine.test_four_branch_combinations", _test_four_branch_combinations)
	kit.run_case("TestStateMachine.test_gate_and_invalid_choice", _test_gate_and_invalid_choice)
	kit.run_case("TestStateMachine.test_idempotence_and_no_double_flag", _test_idempotence_and_no_double_flag)
	kit.run_case("TestStateMachine.test_save_reload", _test_save_reload)
	kit.run_case("TestStateMachine.test_save_reload_at_protagonist_boundary", _test_save_reload_at_protagonist_boundary)
	kit.run_case("TestStateMachine.test_skip_has_no_state_effect", _test_skip_has_no_state_effect)
	kit.run_case("TestStateMachine.test_migrate_v1", _test_migrate_v1)
	kit.run_case("TestStateMachine.test_reject_corrupt_save", _test_reject_corrupt_save)
	kit.run_case("TestStateMachine.test_newgame_restarts_and_fixtures", _test_newgame_restarts_and_fixtures)
	kit.cleanup()
	return kit.failures


## The reference images live in documentation/references (git-ignored, internal study only). When they
## are present the existence check of validate_v3 runs against them; otherwise it is skipped.
static func reference_root() -> String:
	return "res://documentation" if DirAccess.dir_exists_absolute("res://documentation/references") else ""


static func fresh_data() -> Dictionary:
	return ENGINE.load_data()["data"]


func _test_schema() -> bool:
	var root := reference_root()
	if root == "":
		print("      note: documentation/references missing — reference file existence check skipped")
	var report: Dictionary = ENGINE.validate_data(fresh_data(), root)
	kit.is_ok(report, "canonical data validates")
	# The Python test expects the slice (2 quests, 3 scenes); Chapter 3 adds q_c3a_arrival / q_c3b_palais and
	# the scenes L_C3_Station / L_C3_Hall (documentation/C3_DESIGN.md §2), part 2 five quests and scenes with 19
	# objectives (C3P2_DESIGN.md §2), Chapter 4 part 1 four quests and scenes with 22 objectives (C4_DESIGN.md §2).
	kit.eq(report.get("report", {}).get("quests"), 13, "quests")
	kit.eq(report.get("report", {}).get("scenes"), 14, "scenes")
	kit.eq(report.get("report", {}).get("objectives"), 65, "objectives (11 slice + 13 Chapter 3 + 19 part 2 + 22 Chapter 4)")
	return true


func _test_detect_invalid_effect() -> bool:
	var data := fresh_data()
	var objectives: Array = data["quests"]["quests"][0]["objectives"]
	objectives[-1]["choices"][0]["effects"]["not_a_flag"] = {"delta": 1}
	kit.is_err(ENGINE.validate_data(data), "unknown flag effect rejected")
	return true


func _test_detect_objective_cycle() -> bool:
	var data := fresh_data()
	var a: Array = data["quests"]["quests"][0]["objectives"]
	a[0]["requires"] = ["a1_choose"]
	kit.is_err(ENGINE.validate_data(data), "objective cycle rejected")
	return true


func _test_newgame() -> bool:
	var r := Legacy.new()
	kit.eq(r.available(), ["a1_talk_irina"], "available")
	kit.eq(r.state["current_scene"], "L_A1_Railyard", "scene")
	kit.eq(r.state["flags"]["irina_trust"], 0, "irina_trust")
	return true


func _test_four_branch_combinations() -> bool:
	for pa in [["share_with_irina", "irina_trust"], ["keep_private", "alexei_secrecy"]]:
		for pm in [["preserve_evidence", "konrad_evidence"], ["request_explanation", "office_suspicion"]]:
			var label := "%s/%s" % [pa[0], pm[0]]
			var r = Legacy.play_route(pa[0], pm[0])
			kit.eq(r.state["flags"][pa[1]], 1, label + " " + pa[1])
			kit.eq(r.state["flags"][pm[1]], 1, label + " " + pm[1])
			kit.eq(r.state["completed_events"], ["a1_completed", "m1_completed", "slice_completed"], label + " events")
			kit.eq(r.state["flags"]["slice_finished"], true, label + " finished")
			kit.eq(r.state["completed_objectives"].size(), 11, label + " objectives")
			kit.eq(r.state["inventory"].size(), 6, label + " inventory")
			kit.eq(r.state["active_character"], "none", label + " character")
	return true


func _test_gate_and_invalid_choice() -> bool:
	var r := Legacy.new()
	kit.is_err(r.perform("a1_solve_signal"), "gated puzzle")
	kit.is_err(r.perform("a1_talk_irina", "some-choice"), "choice on non-choice objective")
	kit.is_ok(r.perform("a1_talk_irina"), "talk")
	kit.is_ok(r.perform("a1_inspect_seal"), "seal")
	kit.is_err(r.perform("a1_solve_signal"), "still gated")
	r.perform("a1_inspect_timetable")
	r.perform("a1_solve_signal")
	r.perform("a1_inspect_ledger")
	kit.is_err(r.perform("a1_choose", "invalid_choice"), "invalid choice")
	kit.is_ok(r.perform("a1_choose", "share_with_irina"), "valid choice")
	kit.eq(r.state["current_scene"], "L_M1_Archive", "scene switch")
	kit.eq(r.state["active_character"], "konrad", "protagonist switch")
	return true


func _test_idempotence_and_no_double_flag() -> bool:
	var r = Legacy.play_route()
	var before = r.state["flags"]["irina_trust"]
	kit.is_err(r.perform("a1_choose", "share_with_irina"), "choice twice")
	r.finale()
	kit.eq(r.state["flags"]["irina_trust"], before, "no double flag")
	kit.eq(r.state["completed_events"].count("slice_completed"), 1, "event once")
	return true


func _test_save_reload() -> bool:
	var r := Legacy.new()
	r.perform("a1_talk_irina")
	r.perform("a1_inspect_seal")
	var snap := r.save_json()
	var other := Legacy.new()
	kit.is_ok(other.load_json(snap), "load")
	kit.eq(other.save_json(), snap, "identical save")
	kit.eq(other.available(), ["a1_inspect_timetable"], "available after reload")
	return true


func _test_save_reload_at_protagonist_boundary() -> bool:
	var r := Legacy.new()
	for o in ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger"]:
		r.perform(o)
	r.perform("a1_choose", "keep_private")
	var other := Legacy.new()
	kit.is_ok(other.load_json(r.save_json()), "load at boundary")
	kit.eq(other.state["active_character"], "konrad", "protagonist")
	var avail: Array = other.available()
	avail.sort()
	kit.eq(avail, ["m1_inspect_plan_a", "m1_inspect_plan_b"], "available set")
	kit.eq(other.state["flags"]["alexei_secrecy"], 1, "secrecy")
	return true


func _test_skip_has_no_state_effect() -> bool:
	var a = Legacy.play_route("share_with_irina", "preserve_evidence", false)
	var b = Legacy.play_route("share_with_irina", "preserve_evidence", true)
	kit.eq(a.save_json(), b.save_json(), "skip equivalence")
	return true


func _test_migrate_v1() -> bool:
	var r := Legacy.new()
	var legacy := {"save_version": 1, "flags": {"irina_trust": 1}, "completed_objectives": ["a1_talk_irina"],
		"completed_events": [], "inventory": []}
	var res: Dictionary = r.load_json(Kit.dumps(legacy))
	kit.is_ok(res, "v1 migrates")
	var st: Dictionary = res.get("state", {})
	kit.eq(st.get("save_version"), 2, "version 2")
	kit.eq(st.get("flags", {}).get("irina_trust"), 1, "kept flag")
	kit.eq(st.get("flags", {}).get("konrad_evidence"), 0, "new flag default")
	kit.eq(st.get("active_character"), "alexei", "character")
	return true


func _test_reject_corrupt_save() -> bool:
	var r := Legacy.new()
	var save: Dictionary = Kit.parse(r.save_json())
	save["flags"]["irina_trust"] = 999
	kit.is_err(r.load_json(Kit.dumps(save)), "out of range flag")
	save = Kit.parse(r.save_json())
	save["current_scene"] = "not_a_map"
	kit.is_err(r.load_json(Kit.dumps(save)), "unknown scene")
	return true


func _test_newgame_restarts_and_fixtures() -> bool:
	var r = Legacy.play_route("keep_private", "request_explanation")
	r.start_new()
	kit.eq(r.state["completed_events"], [], "events reset")
	kit.eq(r.state["flags"]["office_suspicion"], 0, "flag reset")
	kit.eq(r.available(), ["a1_talk_irina"], "available reset")
	return true
