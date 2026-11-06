extends RefCounted
## All four slice branch combinations × skip × cinematic timing, identical progression gating across branches,
## save/load at every step, skip equivalence — over the whole chain A1 → M1 → Chapter 3 (C3a, C3b, part 2 C3c–C3g)
## → Chapter 4 part 1 (C4a–C4d) → part 2 (C4e–C4h) → finale. The later options of every combination are the canonical
## defaults of Kit.play_verified_route (ask_elena / share_protocol / admit_plan / split_by_language / name_marta /
## publish_now); every option is covered in tests/test_c3_routes.gd, tests/test_c3p2_routes.gd, tests/test_c4_routes.gd
## and tests/test_c4p2_routes.gd.

const Kit := preload("res://tests/support/test_kit.gd")

const COMBOS := [
	["share_with_irina", "preserve_evidence", {"irina_trust": 1, "alexei_secrecy": 0, "konrad_evidence": 1, "office_suspicion": 0}],
	["share_with_irina", "request_explanation", {"irina_trust": 1, "alexei_secrecy": 0, "konrad_evidence": 0, "office_suspicion": 1}],
	["keep_private", "preserve_evidence", {"irina_trust": 0, "alexei_secrecy": 1, "konrad_evidence": 1, "office_suspicion": 0}],
	["keep_private", "request_explanation", {"irina_trust": 0, "alexei_secrecy": 1, "konrad_evidence": 0, "office_suspicion": 1}],
]
## Effects of the default Chapter-3 options (ask_elena: elena_trust +1, share_protocol: alexei_konrad_trust +1,
## part 2 — C3P2_DESIGN §2.4 — admit_plan: alexei_konrad_trust +1, split_by_language: evidence_chain +1; Chapter 4 —
## C4_DESIGN §2.4 — name_marta: evidence_chain +1; part 2 — C4P2_DESIGN §2.4 — publish_now: evidence_chain +1).
const C3_DEFAULT_FLAGS := {"elena_trust": 1, "alexei_konrad_trust": 2, "evidence_chain": 3, "kessler_alerted": 0,
	"people_protected": 0}
const EVENTS := ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed", "c3c_completed", "c3d_completed",
	"c3e_completed", "c3f_completed", "c3g_completed", "c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed",
	"c4e_completed", "c4f_completed", "c4g_completed", "c4h_completed", "slice_completed"]

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
		for k in C3_DEFAULT_FLAGS:
			kit.eq(f[k], C3_DEFAULT_FLAGS[k], label + " " + k)
		for k in ["c17_confirmed", "signal_restored", "blueprint_match_confirmed", "courier_files_seen", "protocol_matched",
				"elena_missing", "slice_finished"]:
			kit.eq(f[k], true, label + " " + k)
		kit.eq(f["civilian_welfare"], 0, label + " civilian_welfare untouched on the default route (protect_marta raises it)")
		kit.eq(g.completed_events(), EVENTS, label + " events")
		kit.eq(g.current_scene, "L_X1_Montage", label + " scene")
		kit.eq(g.active_character, "none", label + " character")
		kit.eq(g.inventory().size(), 48, label + " evidence (6 slice + 6 Chapter 3 + 10 part 2 + 15 Chapter 4 + 11 part 2)")
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


## Records available() after every step of a route (A1, M1, C3a, C3b).
func _gating_trace(a1: String, m1: String) -> Array:
	var g := kit.story()
	var trace: Array = [g.available()]
	var advance := func(r) -> void:
		kit.step(r, "trace step")
		trace.append(g.available())
	var talk := func(oid: String) -> void:
		advance.call(g.start_dialogue(oid))
		while g.state["dialogue_progress"].has(oid):
			advance.call(g.advance_dialogue(oid))
	talk.call("a1_talk_irina")
	advance.call(g.inspect("a1_inspect_seal"))
	advance.call(g.inspect("a1_inspect_timetable"))
	advance.call(g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate()))
	advance.call(g.inspect("a1_inspect_ledger"))
	advance.call(g.choose("a1_choose", a1))
	advance.call(g.inspect("m1_inspect_plan_a"))
	advance.call(g.inspect("m1_inspect_plan_b"))
	advance.call(g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate()))
	talk.call("m1_talk_emil")
	advance.call(g.choose("m1_choose", m1))
	# Chapter 3 (same options for every slice combination)
	talk.call("c3a_talk_conductor")
	advance.call(g.inspect("c3a_inspect_weighbill"))
	advance.call(g.inspect("c3a_inspect_departures"))
	talk.call("c3a_pass_control")
	talk.call("c3a_talk_elena")
	advance.call(g.choose("c3a_choose", "ask_elena"))
	talk.call("c3b_arrival")
	advance.call(g.inspect("c3b_inspect_seating"))
	advance.call(g.inspect("c3b_inspect_log"))
	advance.call(g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()))
	advance.call(g.inspect("c3b_inspect_booth"))
	talk.call("c3b_talk_alexei")
	advance.call(g.choose("c3b_choose", "share_protocol"))
	# Chapter 3 part 2 (C3P2_DESIGN §2.3)
	advance.call(g.inspect("c3c_inspect_crates"))
	advance.call(g.inspect("c3c_inspect_night_book"))
	talk.call("c3c_talk_konrad")
	advance.call(g.inspect("c3d_inspect_intake"))
	advance.call(g.inspect("c3d_inspect_drawer"))
	talk.call("c3d_talk_compare")
	advance.call(g.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate()))
	advance.call(g.inspect("c3d_inspect_plan"))
	talk.call("c3d_talk_partner")
	advance.call(g.choose("c3d_choose", "admit_plan"))
	advance.call(g.inspect("c3e_take_file"))
	advance.call(g.inspect("c3e_try_ramp"))
	talk.call("c3e_reach_konrad")
	advance.call(g.inspect("c3f_inspect_hose"))
	talk.call("c3f_push_desk")
	talk.call("c3f_climb")
	advance.call(g.inspect("c3g_inspect_halves"))
	talk.call("c3g_talk_konrad")
	advance.call(g.choose("c3g_choose", "split_by_language"))
	# Chapter 4 part 1 (C4_DESIGN §2.3)
	advance.call(g.inspect("c4a_inspect_shelf"))
	talk.call("c4a_talk_lev")
	advance.call(g.inspect("c4a_inspect_book"))
	advance.call(g.inspect("c4a_inspect_carbon"))
	talk.call("c4a_talk_tunnel")
	advance.call(g.inspect("c4a_open_door"))
	advance.call(g.inspect("c4b_inspect_notice"))
	talk.call("c4b_talk_marta")
	advance.call(g.solve_puzzle("c4b_solve_routes", Kit.C4_ROUTES.duplicate()))
	advance.call(g.inspect("c4b_inspect_column"))
	talk.call("c4b_talk_ilse")
	advance.call(g.inspect("c4b_inspect_crates"))
	advance.call(g.inspect("c4c_inspect_stencils"))
	advance.call(g.inspect("c4c_inspect_card"))
	advance.call(g.solve_puzzle("c4c_solve_numbers", Kit.C4_NUMBERS.duplicate()))
	advance.call(g.inspect("c4c_inspect_wagon"))
	talk.call("c4c_talk_lev")
	advance.call(g.inspect("c4d_inspect_plan"))
	advance.call(g.inspect("c4d_inspect_drawer"))
	advance.call(g.inspect("c4d_inspect_tube"))
	talk.call("c4d_talk_registrar")
	advance.call(g.choose("c4d_choose", "protect_marta"))
	# Chapter 4 part 2 (C4P2_DESIGN §2.3)
	advance.call(g.inspect("c4e_inspect_list"))
	advance.call(g.inspect("c4e_inspect_order"))
	talk.call("c4e_talk_irina")
	talk.call("c4e_talk_maria")
	advance.call(g.inspect("c4e_inspect_notice"))
	advance.call(g.inspect("c4f_inspect_courier"))
	advance.call(g.inspect("c4f_inspect_board"))
	talk.call("c4f_talk_marta")
	talk.call("c4f_talk_ekdahl")
	advance.call(g.inspect("c4f_inspect_book"))
	talk.call("c4g_talk_ekdahl")
	advance.call(g.inspect("c4g_inspect_book"))
	talk.call("c4g_talk_lev")
	advance.call(g.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate()))
	advance.call(g.inspect("c4g_inspect_card"))
	advance.call(g.choose("c4g_choose", "protect_first"))
	advance.call(g.inspect("c4h_inspect_gate"))
	talk.call("c4h_talk_hanna")
	advance.call(g.inspect("c4h_inspect_cards"))
	advance.call(g.solve_puzzle("c4h_solve_house", Kit.C4_HOUSE.duplicate()))
	talk.call("c4h_talk_wendt")
	return trace


func _gating_identical() -> bool:
	var reference := _gating_trace(COMBOS[0][0], COMBOS[0][1])
	kit.eq(reference[0], ["a1_talk_irina"], "start gate")
	kit.ok(reference.any(func(gates) -> bool: return Kit.strict_eq(gates, ["c3a_talk_conductor"])),
		"M1 hands over to the Chapter-3 station gate")
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
	roundtrip.call()   # the former demo end: now the Chapter-3 entry (L_C3_Station) with X1 + C3 trains queued
	g.consume_cinematic("LS_X1_Final", true)
	kit.play_dialogue(g, "c3a_talk_conductor")
	g.inspect("c3a_inspect_departures")
	roundtrip.call()
	g.inspect("c3a_inspect_weighbill")
	g.start_dialogue("c3a_pass_control")
	g.advance_dialogue("c3a_pass_control")
	g.advance_dialogue("c3a_pass_control")
	roundtrip.call()   # mid-dialogue in Chapter 3
	while g.state["dialogue_progress"].has("c3a_pass_control"):
		g.advance_dialogue("c3a_pass_control")
	kit.play_dialogue(g, "c3a_talk_elena")
	g.choose("c3a_choose", "note_alone")
	roundtrip.call()   # protagonist boundary station → palais
	kit.play_dialogue(g, "c3b_arrival")
	g.inspect("c3b_inspect_seating")
	g.inspect("c3b_inspect_log")
	g.solve_puzzle("c3b_solve_protocol", ["soviet", "secretariat", "chair", "reich"])
	roundtrip.call()   # failed protocol attempt preserved
	g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate())
	g.inspect("c3b_inspect_booth")
	kit.play_dialogue(g, "c3b_talk_alexei")
	g.choose("c3b_choose", "report_delegation")
	roundtrip.call()   # Chapter 3 part 2: registry A (Alexei) with LS_C3_Close + LS_C3_Radio queued
	kit.play_c3c(g)
	roundtrip.call()   # in-level switch registry A → B (Konrad)
	g.inspect("c3d_inspect_intake")
	g.inspect("c3d_inspect_drawer")
	g.start_dialogue("c3d_talk_compare")
	g.advance_dialogue("c3d_talk_compare")
	roundtrip.call()   # mid-dialogue in the registry
	while g.state["dialogue_progress"].has("c3d_talk_compare"):
		g.advance_dialogue("c3d_talk_compare")
	g.solve_puzzle("c3d_solve_check", ["out_2340", "january", "par_4", "in_c17_44"])
	roundtrip.call()   # failed check attempt preserved
	g.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate())
	g.inspect("c3d_inspect_plan")
	kit.play_dialogue(g, "c3d_talk_partner")
	g.choose("c3d_choose", "pocket_plan")
	roundtrip.call()   # B → C with LS_C3_Fire queued
	kit.play_c3e(g)
	roundtrip.call()   # C → D
	kit.play_c3f(g)
	roundtrip.call()   # level change to the quay
	kit.play_c3g(g, "hide_for_elena")
	roundtrip.call()   # level change to Karsk (Chapter 4) with LS_C3_Halves + LS_C4_Homeward queued
	kit.play_c4a(g)
	roundtrip.call()   # city change: Berlin tram loop
	g.inspect("c4b_inspect_notice")
	kit.play_dialogue(g, "c4b_talk_marta")
	g.solve_puzzle("c4b_solve_routes", {"rotation_steps": 0, "offset_x": 3, "offset_y": -2})
	roundtrip.call()   # failed route overlay preserved
	g.solve_puzzle("c4b_solve_routes", Kit.C4_ROUTES.duplicate())
	g.inspect("c4b_inspect_column")
	kit.play_dialogue(g, "c4b_talk_ilse")
	g.inspect("c4b_inspect_crates")
	roundtrip.call()   # city change: the transfer siding
	g.inspect("c4c_inspect_card")
	g.inspect("c4c_inspect_stencils")
	g.solve_puzzle("c4c_solve_numbers", ["c1745", "n24318", "n47702", "c1742"])
	roundtrip.call()   # failed number chain preserved
	g.solve_puzzle("c4c_solve_numbers", Kit.C4_NUMBERS.duplicate())
	g.inspect("c4c_inspect_wagon")
	kit.play_dialogue(g, "c4c_talk_lev")
	roundtrip.call()   # city change: the annex
	kit.play_c4d(g, "protect_marta")
	roundtrip.call()   # Chapter 4 part 2: Karsk depot with LS_C4_Voices + LS_C4P2_Depot queued
	kit.play_c4e(g)
	roundtrip.call()   # city change: the Ostbahnhof
	kit.play_c4f(g)
	roundtrip.call()   # city change: the depot's showcase
	kit.play_dialogue(g, "c4g_talk_ekdahl")
	g.inspect("c4g_inspect_book")
	kit.play_dialogue(g, "c4g_talk_lev")
	g.solve_puzzle("c4g_solve_halves", {"rotation_steps": 0, "offset_x": 4, "offset_y": 1})
	roundtrip.call()   # failed join preserved
	g.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate())
	g.inspect("c4g_inspect_card")
	g.choose("c4g_choose", "protect_first")
	roundtrip.call()   # city change: Kolonnenstraße 14
	g.inspect("c4h_inspect_gate")
	kit.play_dialogue(g, "c4h_talk_hanna")
	g.inspect("c4h_inspect_cards")
	g.solve_puzzle("c4h_solve_house", ["s3", "s2", "s1", "se", "sk", "hk", "ws"])
	roundtrip.call()   # failed way through the house preserved
	g.solve_puzzle("c4h_solve_house", Kit.C4_HOUSE.duplicate())
	kit.play_dialogue(g, "c4h_talk_wendt")
	roundtrip.call()   # montage, finale still open
	g.finale(true)
	roundtrip.call()
	kit.ok(checkpoints[0] >= 40, "checkpoints exercised (%d)" % checkpoints[0])
	return true


func _finale_without_cinematics() -> bool:
	# Python semantics: cinematics are presentation; the finale needs every quest event (A1, M1, C3a … C3g, C4a … C4h).
	var g := kit.story()
	kit.play_a1(g, "share_with_irina")
	kit.is_err(g.finale(), "finale locked after A1 only")
	kit.play_m1(g, "request_explanation")
	kit.is_err(g.finale(), "finale locked after M1 (the old demo end): Chapter 3 is still open")
	kit.play_c3a(g, "note_alone")
	kit.is_err(g.finale(), "finale locked after C3a")
	kit.play_c3b(g, "search_elena")
	kit.is_err(g.finale(), "finale locked after C3b (the former demo end): part 2 is still open")
	for stage in ["c3c", "c3d", "c3e", "c3f"]:
		match stage:
			"c3c":
				kit.play_c3c(g)
			"c3d":
				kit.play_c3d(g, "pocket_plan")
			"c3e":
				kit.play_c3e(g)
			"c3f":
				kit.play_c3f(g)
		kit.is_err(g.finale(), "finale locked after " + stage)
	kit.play_c3g(g, "swap_halves")
	kit.is_err(g.finale(), "finale locked after c3g (the round-8 end): Chapter 4 is still open")
	for stage in ["c4a", "c4b", "c4c"]:
		match stage:
			"c4a":
				kit.play_c4a(g)
			"c4b":
				kit.play_c4b(g)
			"c4c":
				kit.play_c4c(g)
		kit.is_err(g.finale(), "finale locked after " + stage)
	kit.play_c4d(g, "protect_marta")
	kit.is_err(g.finale(), "finale locked after c4d (the round-9 end): part 2 is still open")
	for stage in ["c4e", "c4f", "c4g"]:
		kit.play_stage(g, stage, {"c4g": "protect_first"})
		kit.is_err(g.finale(), "finale locked after " + stage)
	kit.play_c4h(g)
	var all_twenty := ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains", "LS_C3_ToHall", "LS_C3_Close",
		"LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves", "LS_C4_Homeward", "LS_C4_Number", "LS_C4_Card",
		"LS_C4_Stamp", "LS_C4_Voices", "LS_C4P2_Depot", "LS_C4P2_Steam", "LS_C4P2_Book", "LS_C4P2_Express", "LS_C4P2_Clock"]
	kit.eq(g.pending_cinematics(), all_twenty, "all twenty still queued")
	kit.is_ok(g.finale(), "finale reachable")
	kit.eq(g.pending_cinematics(), all_twenty, "queue untouched by the finale")
	return true
