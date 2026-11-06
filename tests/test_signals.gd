extends RefCounted
## Story signals and once-only effects: exact signal stream of a full route, no signals on failed or
## repeated actions, state_replaced on new_game/load, consistent state inside handlers (re-entrancy).

const Kit := preload("res://tests/support/test_kit.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("full_route_signal_stream", _full_stream)
	kit.run_case("dialogue_completes_only_at_terminal_node", _dialogue_terminal)
	kit.run_case("failed_and_repeated_actions_emit_nothing", _once_only)
	kit.run_case("finale_idempotent", _finale_idempotent)
	kit.run_case("new_game_and_load_emit_state_replaced_only", _replaced)
	kit.run_case("handlers_see_committed_state_and_may_reenter", _reentrancy)
	kit.run_case("result_changes_match_signals", _changes_match)
	kit.cleanup()
	return kit.failures


## Records every Story signal as [name, args...].
static func record(g: Node) -> Array:
	var log: Array = []
	g.objective_completed.connect(func(id: String) -> void: log.append(["objective_completed", id]))
	g.event_fired.connect(func(id: String) -> void: log.append(["event_fired", id]))
	g.flag_changed.connect(func(n: String, v) -> void: log.append(["flag_changed", n, v]))
	g.item_granted.connect(func(id: String) -> void: log.append(["item_granted", id]))
	g.cinematic_queued.connect(func(id: String) -> void: log.append(["cinematic_queued", id]))
	g.scene_changed.connect(func(id: String) -> void: log.append(["scene_changed", id]))
	g.state_replaced.connect(func(r: String) -> void: log.append(["state_replaced", r]))
	return log


func _full_stream() -> bool:
	var g := kit.story()
	var log := record(g)
	kit.play_route_on(g, "share_with_irina", "preserve_evidence", false, false)
	kit.eq(log, [
		["objective_completed", "a1_talk_irina"],
		["item_granted", "ev_damaged_seal"], ["objective_completed", "a1_inspect_seal"],
		["item_granted", "ev_timetable"], ["objective_completed", "a1_inspect_timetable"],
		["flag_changed", "signal_restored", true], ["objective_completed", "a1_solve_signal"],
		["flag_changed", "c17_confirmed", true], ["item_granted", "ev_ledger"], ["objective_completed", "a1_inspect_ledger"],
		["flag_changed", "irina_trust", 1], ["objective_completed", "a1_choose"], ["event_fired", "a1_completed"],
		["cinematic_queued", "LS_A1_ToM1"], ["scene_changed", "L_M1_Archive"],
		["item_granted", "ev_plan_a"], ["objective_completed", "m1_inspect_plan_a"],
		["item_granted", "ev_plan_b"], ["objective_completed", "m1_inspect_plan_b"],
		["flag_changed", "blueprint_match_confirmed", true], ["objective_completed", "m1_align_plans"],
		["cinematic_queued", "LS_M1_Hall"],
		["item_granted", "ev_emil_note"], ["objective_completed", "m1_talk_emil"],
		["flag_changed", "konrad_evidence", 1], ["objective_completed", "m1_choose"], ["event_fired", "m1_completed"],
		# m1_completed now queues the Chapter-2 closer AND the Chapter-3 trains and moves on to the station
		["cinematic_queued", "LS_X1_Final"], ["cinematic_queued", "LS_C3_Trains"], ["scene_changed", "L_C3_Station"],
		["objective_completed", "c3a_talk_conductor"],
		["flag_changed", "courier_files_seen", true], ["item_granted", "ev_c3_weighbill"], ["objective_completed", "c3a_inspect_weighbill"],
		["item_granted", "ev_c3_departures"], ["objective_completed", "c3a_inspect_departures"],
		["item_granted", "ev_c3_travel_order"], ["objective_completed", "c3a_pass_control"],
		["objective_completed", "c3a_talk_elena"],
		["flag_changed", "elena_trust", 1], ["objective_completed", "c3a_choose"], ["event_fired", "c3a_completed"],
		["cinematic_queued", "LS_C3_ToHall"], ["scene_changed", "L_C3_Hall"],
		["objective_completed", "c3b_arrival"],
		["item_granted", "ev_c3_seating"], ["objective_completed", "c3b_inspect_seating"],
		["item_granted", "ev_c3_booth_log"], ["objective_completed", "c3b_inspect_log"],
		["flag_changed", "protocol_matched", true], ["objective_completed", "c3b_solve_protocol"],
		["flag_changed", "elena_missing", true], ["item_granted", "ev_c3_carbon"], ["objective_completed", "c3b_inspect_booth"],
		["objective_completed", "c3b_talk_alexei"],
		["flag_changed", "alexei_konrad_trust", 1], ["objective_completed", "c3b_choose"], ["event_fired", "c3b_completed"],
		["cinematic_queued", "LS_C3_Close"], ["cinematic_queued", "LS_C3_Radio"], ["scene_changed", "L_C3_RegistryA"],
		# Chapter 3 part 2 (C3P2_DESIGN.md): registry A → B → C → D (in-level switches), the quay
		["item_granted", "ev_c3_cut_seal"], ["objective_completed", "c3c_inspect_crates"],
		["item_granted", "ev_c3_night_book"], ["objective_completed", "c3c_inspect_night_book"],
		["objective_completed", "c3c_talk_konrad"], ["event_fired", "c3c_completed"], ["scene_changed", "L_C3_RegistryB"],
		["item_granted", "ev_c3_intake_book"], ["objective_completed", "c3d_inspect_intake"],
		["item_granted", "ev_c3_scarf"], ["objective_completed", "c3d_inspect_drawer"],
		["item_granted", "ev_c3_halves"], ["objective_completed", "c3d_talk_compare"],
		["objective_completed", "c3d_solve_check"],
		["item_granted", "ev_c3_kordon_plan"], ["objective_completed", "c3d_inspect_plan"],
		["objective_completed", "c3d_talk_partner"],
		["flag_changed", "alexei_konrad_trust", 2], ["objective_completed", "c3d_choose"], ["event_fired", "c3d_completed"],
		["cinematic_queued", "LS_C3_Fire"], ["scene_changed", "L_C3_RegistryC"],
		["item_granted", "ev_c3_file"], ["objective_completed", "c3e_take_file"],
		["item_granted", "ev_c3_bolt"], ["objective_completed", "c3e_try_ramp"],
		["objective_completed", "c3e_reach_konrad"], ["event_fired", "c3e_completed"], ["scene_changed", "L_C3_RegistryD"],
		["item_granted", "ev_c3_cut_hose"], ["objective_completed", "c3f_inspect_hose"],
		["objective_completed", "c3f_push_desk"],
		["objective_completed", "c3f_climb"], ["event_fired", "c3f_completed"],
		["cinematic_queued", "LS_C3_Escape"], ["scene_changed", "L_C3_Quay"],
		["item_granted", "ev_c3_escort_list"], ["objective_completed", "c3g_inspect_halves"],
		["objective_completed", "c3g_talk_konrad"],
		["flag_changed", "evidence_chain", 1], ["objective_completed", "c3g_choose"], ["event_fired", "c3g_completed"],
		["cinematic_queued", "LS_C3_Halves"], ["scene_changed", "L_X1_Montage"],
		["flag_changed", "slice_finished", true], ["event_fired", "slice_completed"],
	], "exact signal stream of the share/preserve route (+ ask_elena / share_protocol / admit_plan / split_by_language)")
	return true


func _dialogue_terminal() -> bool:
	var g := kit.story()
	var log := record(g)
	g.start_dialogue("a1_talk_irina")
	for i in 4:
		var r: Dictionary = g.advance_dialogue("a1_talk_irina")
		kit.eq(r.get("finished"), false, "advance %d not finished" % i)
	kit.eq(log, [], "no completion before the terminal node")
	kit.eq(g.current_dialogue_line("a1_talk_irina").get("end"), true, "at terminal node")
	var last: Dictionary = g.advance_dialogue("a1_talk_irina")
	kit.eq(last.get("finished"), true, "finished at terminal node")
	kit.eq(log, [["objective_completed", "a1_talk_irina"]], "exactly one completion")
	return true


func _once_only() -> bool:
	var g := kit.story()
	var log := record(g)
	kit.is_err(g.inspect("a1_inspect_seal"), "locked")
	kit.is_err(g.choose("a1_choose", "share_with_irina"), "locked choice")
	kit.is_err(g.finale(), "locked finale")
	kit.is_err(g.consume_cinematic("LS_A1_ToM1"), "locked cinematic")
	kit.eq(log, [], "failed actions emit nothing")
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	log.clear()
	kit.is_err(g.inspect("a1_inspect_seal"), "inspect twice")
	kit.is_err(g.start_dialogue("a1_talk_irina"), "dialogue twice")
	g.inspect("a1_inspect_timetable")
	log.clear()
	for wrong in [["circle", "square", "triangle"], [], ["square"]]:
		kit.eq(g.solve_puzzle("a1_solve_signal", wrong).get("solved"), false, "wrong answer")
	kit.eq(log, [], "wrong answers emit nothing")
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	var before: Dictionary = g.snapshot()
	kit.is_err(g.choose("a1_choose", "both"), "invalid choice")
	kit.eq(g.snapshot(), before, "invalid choice mutates nothing")
	g.choose("a1_choose", "keep_private")
	log.clear()
	var after: Dictionary = g.snapshot()
	kit.is_err(g.choose("a1_choose", "share_with_irina"), "second choice refused")
	kit.is_err(g.choose("a1_choose", "keep_private"), "same choice twice refused")
	kit.eq(g.snapshot(), after, "choice applied once")
	kit.eq(g.flags()["alexei_secrecy"], 1, "delta applied once")
	kit.is_ok(g.consume_cinematic("LS_A1_ToM1", true), "consume")
	kit.is_err(g.consume_cinematic("LS_A1_ToM1", false), "consume twice")
	kit.eq(log, [], "repeated actions emit nothing")
	kit.eq(g.completed_events().count("a1_completed"), 1, "event once")
	return true


func _finale_idempotent() -> bool:
	var g := kit.play_verified_route()
	var log := record(g)
	var snap: Dictionary = g.snapshot()
	kit.is_ok(g.finale(true), "finale again")
	kit.is_ok(g.finale(false), "and again")
	kit.eq(log, [], "no second slice_completed / slice_finished")
	kit.eq(g.snapshot(), snap, "state unchanged")
	kit.eq(g.completed_events().count("slice_completed"), 1, "slice_completed once")
	return true


func _replaced() -> bool:
	var g := kit.story()
	var log := record(g)
	var src := kit.play_verified_route()
	kit.is_ok(g.load_json(src.save_json()), "load")
	kit.eq(log, [["state_replaced", "load"]], "load emits only state_replaced")
	log.clear()
	kit.is_err(g.load_json("{}"), "bad load")
	kit.eq(log, [], "failed load emits nothing")
	kit.is_ok(g.new_game(), "new game")
	kit.eq(log, [["state_replaced", "new_game"]], "new_game emits only state_replaced")
	kit.eq(g.available(), ["a1_talk_irina"], "fresh after new_game")
	return true


func _reentrancy() -> bool:
	var g := kit.story()
	var seen: Array = []
	g.objective_completed.connect(func(id: String) -> void:
		if id == "a1_inspect_timetable":
			seen.append(g.available()))
	# The director consumes a cinematic from inside the signal handler.
	g.cinematic_queued.connect(func(id: String) -> void: seen.append(g.consume_cinematic(id, true).get("ok")))
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	var r: Dictionary = g.choose("a1_choose", "share_with_irina")
	kit.eq(seen, [["a1_solve_signal"], true], "handler saw the committed state; re-entrant consume succeeded")
	kit.eq(r["changes"]["cinematics"], ["LS_A1_ToM1"], "result still reports the queued cinematic")
	kit.eq(g.pending_cinematics(), [], "consumed inside the handler")
	kit.eq(g.current_scene, "L_M1_Archive", "scene switched")
	return true


func _changes_match() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	var r: Dictionary = g.inspect("a1_inspect_ledger")
	kit.eq(r.get("changes"), {"flags": {"c17_confirmed": true}, "objectives": ["a1_inspect_ledger"], "items": ["ev_ledger"],
		"events": [], "cinematics": [], "scene": ""}, "inspect ledger changes")
	var c: Dictionary = g.choose("a1_choose", "share_with_irina")
	kit.eq(c.get("changes"), {"flags": {"irina_trust": 1}, "objectives": ["a1_choose"], "items": [],
		"events": ["a1_completed"], "cinematics": ["LS_A1_ToM1"], "scene": "L_M1_Archive"}, "choice changes")
	return true
