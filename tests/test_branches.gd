extends RefCounted
## All four branch combinations × skip × cinematic timing, identical progression gating across branches,
## save/load at every step, skip equivalence.

const Kit := preload("res://tests/support/test_kit.gd")

const COMBOS := [
	["share_with_irina", "preserve_evidence", {"irina_trust": 1, "alexei_secrecy": 0, "konrad_evidence": 1, "office_suspicion": 0}],
	["share_with_irina", "request_explanation", {"irina_trust": 1, "alexei_secrecy": 0, "konrad_evidence": 0, "office_suspicion": 1}],
	["keep_private", "preserve_evidence", {"irina_trust": 0, "alexei_secrecy": 1, "konrad_evidence": 1, "office_suspicion": 0}],
	["keep_private", "request_explanation", {"irina_trust": 0, "alexei_secrecy": 1, "konrad_evidence": 0, "office_suspicion": 1}],
]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("four_combinations_flags_and_end_state", _four_combinations)
	kit.run_case("skip_and_timing_equivalence", _skip_equivalence)
	kit.run_case("gating_identical_across_branches", _gating_identical)
	kit.run_case("save_load_at_every_step", _save_load_every_step)
	kit.run_case("finale_does_not_require_watching_cinematics", _finale_without_cinematics)
	kit.cleanup()
	return kit.failures


func _four_combinations() -> bool:
	var finals := {}
	for combo in COMBOS:
		var label := "%s/%s" % [combo[0], combo[1]]
		var g := kit.play_verified_route(combo[0], combo[1])
		var f: Dictionary = g.flags()
		for k in combo[2]:
			kit.eq(f[k], combo[2][k], label + " " + k)
		for k in ["c17_confirmed", "signal_restored", "blueprint_match_confirmed", "slice_finished"]:
			kit.eq(f[k], true, label + " " + k)
		kit.eq(f["civilian_welfare"], 0, label + " civilian_welfare untouched in the slice")
		kit.eq(g.completed_events(), ["a1_completed", "m1_completed", "slice_completed"], label + " events")
		kit.eq(g.current_scene, "L_X1_Montage", label + " scene")
		kit.eq(g.active_character, "none", label + " character")
		kit.eq(g.inventory().size(), 6, label + " evidence")
		kit.eq(g.is_finished(), true, label + " finished")
		kit.eq(g.is_finale_viewed(), true, label + " finale viewed")
		kit.eq(g.relationship("irina_trust"), combo[2]["irina_trust"], label + " relationship accessor")
		finals[g.save_json()] = label
	kit.eq(finals.size(), 4, "four distinct end states")
	return true


func _skip_equivalence() -> bool:
	for combo in COMBOS:
		var reference := ""
		for skip in [false, true]:
			for now in [false, true]:
				var g := kit.story()
				kit.play_route_on(g, combo[0], combo[1], skip, now)
				var text: String = g.save_json()
				if reference == "":
					reference = text
				kit.eq(text, reference, "%s/%s skip=%s consume_now=%s" % [combo[0], combo[1], skip, now])
	return true


## Records available() after every step of a route.
func _gating_trace(a1: String, m1: String) -> Array:
	var g := kit.story()
	var trace: Array = [g.available()]
	var advance := func(r) -> void:
		kit.step(r, "trace step")
		trace.append(g.available())
	advance.call(g.start_dialogue("a1_talk_irina"))
	while g.state["dialogue_progress"].has("a1_talk_irina"):
		advance.call(g.advance_dialogue("a1_talk_irina"))
	advance.call(g.inspect("a1_inspect_seal"))
	advance.call(g.inspect("a1_inspect_timetable"))
	advance.call(g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate()))
	advance.call(g.inspect("a1_inspect_ledger"))
	advance.call(g.choose("a1_choose", a1))
	advance.call(g.inspect("m1_inspect_plan_a"))
	advance.call(g.inspect("m1_inspect_plan_b"))
	advance.call(g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate()))
	advance.call(g.start_dialogue("m1_talk_emil"))
	while g.state["dialogue_progress"].has("m1_talk_emil"):
		advance.call(g.advance_dialogue("m1_talk_emil"))
	advance.call(g.choose("m1_choose", m1))
	return trace


func _gating_identical() -> bool:
	var reference := _gating_trace(COMBOS[0][0], COMBOS[0][1])
	kit.eq(reference[0], ["a1_talk_irina"], "start gate")
	kit.eq(reference[-1], [], "nothing available in the montage")
	for combo in COMBOS:
		kit.eq(_gating_trace(combo[0], combo[1]), reference, "gating of %s/%s equals the reference" % [combo[0], combo[1]])
	return true


func _save_load_every_step() -> bool:
	var g := kit.story()
	var checkpoints := [0]
	var roundtrip := func() -> void:
		var h := kit.story()
		var r: Dictionary = h.load_json(g.save_json())
		kit.is_ok(r, "reload at checkpoint %d" % checkpoints[0])
		kit.eq(h.snapshot(), g.snapshot(), "identical state at checkpoint %d" % checkpoints[0])
		kit.eq(h.available(), g.available(), "identical gates at checkpoint %d" % checkpoints[0])
		kit.eq(h.pending_cinematics(), g.pending_cinematics(), "identical cinematic queue at checkpoint %d" % checkpoints[0])
		checkpoints[0] += 1
		h.free()
	roundtrip.call()
	g.start_dialogue("a1_talk_irina")
	while g.state["dialogue_progress"].has("a1_talk_irina"):
		roundtrip.call()
		g.advance_dialogue("a1_talk_irina")
	for o in ["a1_inspect_seal", "a1_inspect_timetable"]:
		g.inspect(o)
		roundtrip.call()
	g.solve_puzzle("a1_solve_signal", ["triangle", "circle", "square"])
	roundtrip.call()
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	g.choose("a1_choose", "keep_private")
	roundtrip.call()   # protagonist boundary with a pending cinematic
	g.consume_cinematic("LS_A1_ToM1", true)
	roundtrip.call()
	g.inspect("m1_inspect_plan_b")
	g.inspect("m1_inspect_plan_a")
	g.solve_puzzle("m1_align_plans", {"rotation_steps": 1, "offset_x": 2, "offset_y": -1})
	roundtrip.call()
	g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	roundtrip.call()
	g.start_dialogue("m1_talk_emil")
	g.advance_dialogue("m1_talk_emil")
	roundtrip.call()
	while g.state["dialogue_progress"].has("m1_talk_emil"):
		g.advance_dialogue("m1_talk_emil")
	g.choose("m1_choose", "preserve_evidence")
	roundtrip.call()
	g.finale(true)
	roundtrip.call()
	kit.ok(checkpoints[0] >= 15, "checkpoints exercised (%d)" % checkpoints[0])
	return true


func _finale_without_cinematics() -> bool:
	# Python semantics: cinematics are presentation; the finale only needs both quest events.
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	for o in ["a1_inspect_seal", "a1_inspect_timetable"]:
		g.inspect(o)
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	g.choose("a1_choose", "share_with_irina")
	kit.is_err(g.finale(), "finale locked after A1 only")
	g.inspect("m1_inspect_plan_a")
	g.inspect("m1_inspect_plan_b")
	g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	kit.play_dialogue(g, "m1_talk_emil")
	g.choose("m1_choose", "request_explanation")
	kit.eq(g.pending_cinematics(), ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final"], "all three still queued")
	kit.is_ok(g.finale(), "finale reachable")
	kit.eq(g.pending_cinematics(), ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final"], "queue untouched by the finale")
	return true
