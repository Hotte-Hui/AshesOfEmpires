extends RefCounted
## Chapter 3 „Der eiserne Frieden“ through the public Story API (documentation/C3_DESIGN.md §1–§2):
## every slice combination (a1 × m1) × every Chapter-3 option (c3a × c3b), the gating order of the 13 objectives,
## inventory order, flags per choice, events, scene/protagonist switches, the finale gate, the cinematic queue,
## skip/timing equivalence, mid-chapter save/load, saves from before the M1 decision continued into Chapter 3,
## the protocol-puzzle rules and the validator's Chapter-3 integrity checks. Since round 8 the chain goes on from c3b
## into part 2 (documentation/C3P2_DESIGN.md, tests/test_c3p2_routes.gd); finished routes here play part 2 with the
## Kit defaults (admit_plan, split_by_language).

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const Legacy := preload("res://tests/support/legacy_runtime_v2.gd")

const A1 := ["share_with_irina", "keep_private"]
const M1 := ["preserve_evidence", "request_explanation"]
const C3A := ["ask_elena", "note_alone"]
const C3B := ["share_protocol", "search_elena", "report_delegation"]
## data order (= the order in which the canonical route completes them)
const C3_OBJECTIVES := ["c3a_talk_conductor", "c3a_inspect_weighbill", "c3a_inspect_departures", "c3a_pass_control",
	"c3a_talk_elena", "c3a_choose", "c3b_arrival", "c3b_inspect_seating", "c3b_inspect_log", "c3b_solve_protocol",
	"c3b_inspect_booth", "c3b_talk_alexei", "c3b_choose"]
const SLICE_ITEMS := ["ev_damaged_seal", "ev_timetable", "ev_ledger", "ev_plan_a", "ev_plan_b", "ev_emil_note"]
const C3_ITEMS := ["ev_c3_weighbill", "ev_c3_departures", "ev_c3_travel_order", "ev_c3_seating", "ev_c3_booth_log", "ev_c3_carbon"]
const C3_FLAGS := ["alexei_konrad_trust", "elena_trust", "evidence_chain", "kessler_alerted", "courier_files_seen",
	"protocol_matched", "elena_missing"]
const EVENTS := ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed", "c3c_completed", "c3d_completed",
	"c3e_completed", "c3f_completed", "c3g_completed", "slice_completed"]
const ALL_CINEMATICS := ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains", "LS_C3_ToHall", "LS_C3_Close",
	"LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves"]
## Part 2 with the Kit defaults (C3P2_DESIGN §2.3/§2.5): items in acquisition order, meters added on top of C3a/C3b.
const P2_ITEMS := ["ev_c3_cut_seal", "ev_c3_night_book", "ev_c3_intake_book", "ev_c3_scarf", "ev_c3_halves",
	"ev_c3_kordon_plan", "ev_c3_file", "ev_c3_bolt", "ev_c3_cut_hose", "ev_c3_escort_list"]
const P2_DEFAULT_DELTA := {"alexei_konrad_trust": 1, "evidence_chain": 1}

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("all_combinations_through_chapter3", _all_combinations)
	kit.run_case("gating_order_of_the_13_objectives", _gating_order)
	kit.run_case("events_scenes_queue_and_finale_step_by_step", _step_by_step)
	kit.run_case("skip_and_timing_equivalence", _skip_equivalence)
	kit.run_case("gating_identical_across_branches", _gating_identical)
	kit.run_case("inventory_order_follows_acquisition", _inventory_order)
	kit.run_case("mid_chapter3_save_load_round_trips", _mid_chapter_round_trips)
	kit.run_case("save_before_m1_choose_continues_into_chapter3", _continue_old_saves)
	kit.run_case("protocol_puzzle_rules", _protocol_puzzle)
	kit.run_case("validator_rejects_broken_chapter3_data", _integrity)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Chapter-3 flags a finished route must hold for the two Chapter-3 options (C3_DESIGN §2.4/§2.6).
static func c3_flags(c3a: String, c3b: String) -> Dictionary:
	return {"elena_trust": int(c3a == "ask_elena") + int(c3b == "search_elena"), "evidence_chain": int(c3a == "note_alone"),
		"alexei_konrad_trust": int(c3b == "share_protocol"), "kessler_alerted": int(c3b == "report_delegation"),
		"courier_files_seen": true, "protocol_matched": true, "elena_missing": true}


static func c3_states(g: Node) -> Array:
	return C3_OBJECTIVES.map(func(oid: String) -> String: return g.objective_state(oid))


## The API call that would complete `oid` (used on locked / completed objectives only).
static func attempt(g: Node, oid: String) -> Dictionary:
	match g.objective_def(oid).get("type"):
		"inspect":
			return g.inspect(oid)
		"dialogue":
			return g.start_dialogue(oid)
		"puzzle":
			return g.solve_puzzle(oid, Kit.C3_PROTOCOL.duplicate())
		"choice":
			return g.choose(oid, g.choices_for(oid)[0]["id"])
	return {}


## Every Chapter-3 objective that is not available refuses its completing call and changes nothing.
func sweep_locked(g: Node, where: String) -> void:
	for oid in C3_OBJECTIVES:
		if g.objective_state(oid) == "available":
			continue
		var before: String = g.save_json()
		var r := attempt(g, oid)
		kit.is_err(r, "%s: %s refused" % [where, oid])
		kit.eq(r.get("error_key"), "sys.err.locked", "%s: %s locked key" % [where, oid])
		kit.eq(g.save_json(), before, "%s: refused %s changes nothing" % [where, oid])


## available() after every step from the Chapter-3 entry (after m1_choose) to the montage.
func c3_trace(g: Node, c3a: String, c3b: String) -> Array:
	var trace: Array = [g.available()]
	var step := func(r) -> void:
		kit.step(r, "c3 trace step")
		trace.append(g.available())
	var talk := func(oid: String) -> void:
		step.call(g.start_dialogue(oid))
		while g.state["dialogue_progress"].has(oid):
			step.call(g.advance_dialogue(oid))
	talk.call("c3a_talk_conductor")
	step.call(g.inspect("c3a_inspect_weighbill"))
	step.call(g.inspect("c3a_inspect_departures"))
	talk.call("c3a_pass_control")
	talk.call("c3a_talk_elena")
	step.call(g.choose("c3a_choose", c3a))
	talk.call("c3b_arrival")
	step.call(g.inspect("c3b_inspect_seating"))
	step.call(g.inspect("c3b_inspect_log"))
	step.call(g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()))
	step.call(g.inspect("c3b_inspect_booth"))
	talk.call("c3b_talk_alexei")
	step.call(g.choose("c3b_choose", c3b))
	return trace


## One part-2 stage with the Kit defaults (C3P2_DESIGN §2.3).
func _play_stage(g: Node, stage: String) -> void:
	match stage:
		"c3c":
			kit.play_c3c(g)
		"c3d":
			kit.play_c3d(g)
		"c3e":
			kit.play_c3e(g)
		"c3f":
			kit.play_c3f(g)
		"c3g":
			kit.play_c3g(g)


static func _find(records: Array, id: String) -> Dictionary:
	for r in records:
		if r is Dictionary and r.get("id") == id:
			return r
	return {}


# ------------------------------------------------------------------ cases
func _all_combinations() -> bool:
	var finals := {}
	for a1 in A1:
		for m1 in M1:
			for c3a in C3A:
				for c3b in C3B:
					var label := "%s/%s/%s/%s" % [a1, m1, c3a, c3b]
					var g := kit.play_verified_route(a1, m1, false, c3a, c3b)
					var f: Dictionary = g.flags()
					var want := c3_flags(c3a, c3b)
					for k in P2_DEFAULT_DELTA:
						want[k] = int(want[k]) + int(P2_DEFAULT_DELTA[k])
					for k in want:
						kit.eq(f[k], want[k], label + " " + k)
					kit.eq([f["irina_trust"], f["alexei_secrecy"]], [int(a1 == "share_with_irina"), int(a1 == "keep_private")], label + " A1 meters kept")
					kit.eq([f["konrad_evidence"], f["office_suspicion"]], [int(m1 == "preserve_evidence"), int(m1 == "request_explanation")], label + " M1 meters kept")
					kit.eq(g.completed_events(), EVENTS, label + " events")
					kit.eq([g.current_scene, g.active_character], ["L_X1_Montage", "none"], label + " montage, no protagonist")
					kit.eq(g.inventory(), SLICE_ITEMS + C3_ITEMS + P2_ITEMS, label + " inventory order")
					kit.eq(g.choice_history(), {"a1_choose": a1, "m1_choose": m1, "c3a_choose": c3a, "c3b_choose": c3b,
						"c3d_choose": "admit_plan", "c3g_choose": "split_by_language"}, label + " choices")
					kit.eq(g.completed_objectives().slice(11, 24), C3_OBJECTIVES, label + " Chapter-3 objectives in order")
					kit.eq([g.is_finished(), g.is_finale_viewed(), f["slice_finished"]], [true, true, true], label + " finished")
					kit.eq(g.pending_cinematics(), [], label + " every cinematic consumed")
					finals[g.save_json()] = label
					g.free()
	kit.eq(finals.size(), 24, "24 distinct end states (4 slice combinations × 2 × 3 Chapter-3 options)")
	return true


func _gating_order() -> bool:
	var g := kit.story()
	kit.eq(c3_states(g), C3_OBJECTIVES.map(func(_o) -> String: return "locked"), "all 13 locked in a new game")
	kit.play_a1(g, "keep_private")
	sweep_locked(g, "after A1")
	g.inspect("m1_inspect_plan_a")
	g.inspect("m1_inspect_plan_b")
	g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	kit.play_dialogue(g, "m1_talk_emil")
	kit.eq(g.available(), ["m1_choose"], "only the M1 decision is left")
	sweep_locked(g, "before m1_choose")
	kit.step(g.choose("m1_choose", "preserve_evidence"), "m1 choice")
	# [action, objective, available() afterwards] — exact order, data order within a step
	var steps := [
		["start", "c3a_talk_conductor", ["c3a_talk_conductor"]],
		["finish", "c3a_talk_conductor", ["c3a_inspect_weighbill", "c3a_inspect_departures"]],
		["inspect", "c3a_inspect_weighbill", ["c3a_inspect_departures"]],
		["inspect", "c3a_inspect_departures", ["c3a_pass_control"]],
		["talk", "c3a_pass_control", ["c3a_talk_elena"]],
		["talk", "c3a_talk_elena", ["c3a_choose"]],
		["choose", "c3a_choose", ["c3b_arrival"]],
		["talk", "c3b_arrival", ["c3b_inspect_seating", "c3b_inspect_log"]],
		["inspect", "c3b_inspect_seating", ["c3b_inspect_log"]],
		["inspect", "c3b_inspect_log", ["c3b_solve_protocol"]],
		["solve", "c3b_solve_protocol", ["c3b_inspect_booth"]],
		["inspect", "c3b_inspect_booth", ["c3b_talk_alexei"]],
		["talk", "c3b_talk_alexei", ["c3b_choose"]],
		["choose", "c3b_choose", ["c3c_inspect_crates"]],
	]
	kit.eq(g.available(), ["c3a_talk_conductor"], "entry gate of the station")
	sweep_locked(g, "station entry")
	for s in steps:
		var oid: String = s[1]
		match s[0]:
			"start":
				kit.step(g.start_dialogue(oid), "start " + oid)
			"finish":
				while g.state["dialogue_progress"].has(oid):
					kit.step(g.advance_dialogue(oid), "advance " + oid)
			"talk":
				kit.play_dialogue(g, oid)
			"inspect":
				kit.step(g.inspect(oid), "inspect " + oid)
			"solve":
				kit.step(g.solve_puzzle(oid, Kit.C3_PROTOCOL.duplicate()), "solve " + oid)
			"choose":
				kit.step(g.choose(oid, g.choices_for(oid)[0]["id"]), "choose " + oid)
		kit.eq(g.available(), s[2], "available after %s %s" % [s[0], oid])
		var want: Array = C3_OBJECTIVES.map(func(o: String) -> String:
			return "complete" if g.completed_objectives().has(o) else ("available" if (s[2] as Array).has(o) else "locked"))
		kit.eq(c3_states(g), want, "objective states after %s %s" % [s[0], oid])
		sweep_locked(g, "after %s %s" % [s[0], oid])
	kit.eq(g.completed_objectives().slice(11), C3_OBJECTIVES, "completion order = data order")
	return true


func _step_by_step() -> bool:
	var g := kit.story()
	kit.play_a1(g, "share_with_irina")
	kit.is_err(g.finale(), "finale locked after A1")
	g.inspect("m1_inspect_plan_a")
	g.inspect("m1_inspect_plan_b")
	g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	kit.play_dialogue(g, "m1_talk_emil")
	kit.is_err(g.consume_cinematic("LS_C3_Trains"), "trains not unlocked before m1_completed")
	var r: Dictionary = g.choose("m1_choose", "request_explanation")
	kit.eq(r.get("changes", {}).get("events"), ["m1_completed"], "m1 event")
	kit.eq(r.get("changes", {}).get("cinematics"), ["LS_X1_Final", "LS_C3_Trains"], "m1_completed queues the Chapter-2 closer, then the Chapter-3 trains")
	kit.eq(r.get("changes", {}).get("scene"), "L_C3_Station", "scene → station")
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C3_Station", "alexei", "ui.chapter_c3"], "Alexei at the station")
	kit.eq(g.pending_cinematics(), ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains"], "queue in data order")
	var fl: Dictionary = g.finale()
	kit.eq([fl.get("ok"), fl.get("error"), fl.get("error_key")], [false, "Finale locked", "sys.err.finale_locked"], "finale locked at the station (the old demo end)")
	kit.is_err(g.consume_cinematic("LS_C3_ToHall"), "LS_C3_ToHall not unlocked yet")
	kit.is_err(g.consume_cinematic("LS_C3_Close", true), "LS_C3_Close not unlocked yet")
	for cid in g.pending_cinematics():
		var c: Dictionary = g.consume_cinematic(cid, true)
		kit.eq([c.get("ok"), c.get("skipped")], [true, true], "consume " + cid)
	kit.eq(g.pending_cinematics(), [], "queue drained by the director")
	kit.is_err(g.consume_cinematic("LS_C3_Trains", false), "trains once only")
	# station, step by step with the reported changes
	kit.play_dialogue(g, "c3a_talk_conductor")
	var w: Dictionary = g.inspect("c3a_inspect_weighbill")
	kit.eq([w["changes"]["flags"], w["changes"]["items"]], [{"courier_files_seen": true}, ["ev_c3_weighbill"]], "weighbill sets courier_files_seen and grants the weighbill")
	var d: Dictionary = g.inspect("c3a_inspect_departures")
	kit.eq([d["changes"]["flags"], d["changes"]["items"]], [{}, ["ev_c3_departures"]], "departures board")
	g.start_dialogue("c3a_pass_control")
	var last: Dictionary = {}
	while g.state["dialogue_progress"].has("c3a_pass_control"):
		last = g.advance_dialogue("c3a_pass_control")
	kit.eq([last.get("finished"), last.get("changes", {}).get("items")], [true, ["ev_c3_travel_order"]], "travel order granted at the terminal control line")
	kit.play_dialogue(g, "c3a_talk_elena")
	kit.is_err(g.finale(), "finale locked before the c3a decision")
	var ra: Dictionary = g.choose("c3a_choose", "ask_elena")
	kit.eq(ra.get("changes"), {"flags": {"elena_trust": 1}, "objectives": ["c3a_choose"], "items": [], "events": ["c3a_completed"],
		"cinematics": ["LS_C3_ToHall"], "scene": "L_C3_Hall"}, "c3a decision changes")
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C3_Hall", "konrad", "ui.chapter_c3"], "Konrad in the palais")
	kit.eq(g.current_quest().get("id"), "q_c3b_palais", "palais quest active")
	kit.is_err(g.finale(true), "finale locked in the palais")
	kit.is_ok(g.consume_cinematic("LS_C3_ToHall"), "station → palais transition")
	kit.is_err(g.consume_cinematic("LS_C3_ToHall"), "transition once only")
	# palais
	kit.play_dialogue(g, "c3b_arrival")
	g.inspect("c3b_inspect_seating")
	g.inspect("c3b_inspect_log")
	var p: Dictionary = g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate())
	kit.eq([p.get("solved"), p["changes"]["flags"]], [true, {"protocol_matched": true}], "protocol solved sets protocol_matched")
	var b: Dictionary = g.inspect("c3b_inspect_booth")
	kit.eq([b["changes"]["flags"], b["changes"]["items"]], [{"elena_missing": true}, ["ev_c3_carbon"]], "booth 2: Elena missing, carbon copy")
	kit.play_dialogue(g, "c3b_talk_alexei")
	kit.is_err(g.finale(), "finale locked before the c3b decision")
	var rb: Dictionary = g.choose("c3b_choose", "search_elena")
	kit.eq(rb.get("changes"), {"flags": {"elena_trust": 2}, "objectives": ["c3b_choose"], "items": [], "events": ["c3b_completed"],
		"cinematics": ["LS_C3_Close", "LS_C3_Radio"], "scene": "L_C3_RegistryA"}, "c3b decision changes (search_elena adds to elena_trust)")
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C3_RegistryA", "alexei", "ui.chapter_c3"], "part 2: Alexei at the registry")
	kit.eq([g.current_quest().get("id"), g.available()], ["q_c3c_registry", ["c3c_inspect_crates"]], "registry quest, first gate")
	kit.eq(g.pending_cinematics(), ["LS_C3_Close", "LS_C3_Radio"], "the night: closing train, then the radio")
	kit.is_err(g.finale(true), "finale locked after c3b (part 2 is open)")
	kit.play_c3c(g)
	kit.play_c3d(g)
	kit.play_c3e(g)
	kit.play_c3f(g)
	kit.play_c3g(g)
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_X1_Montage", "none", "world.x1.title"], "montage")
	kit.eq([g.current_quest(), g.available()], [{}, []], "no quest, nothing available")
	var fin: Dictionary = g.finale(true)
	kit.is_ok(fin, "finale open after c3g")
	kit.eq([fin["changes"]["events"], fin["changes"]["flags"]], [["slice_completed"], {"slice_finished": true}], "finale changes")
	kit.is_ok(g.finale(false), "finale idempotent")
	kit.eq(g.completed_events(), EVENTS, "events once each, in order")
	kit.eq(g.pending_cinematics(), ["LS_C3_Close", "LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves"], "the finale does not consume the night's cinematics")
	for cid in ["LS_C3_Close", "LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves"]:
		kit.is_ok(g.consume_cinematic(cid, false), "consume " + cid)
	kit.eq(g.state["cinematics_seen"], ALL_CINEMATICS, "every cinematic seen once, data order")
	return true


func _skip_equivalence() -> bool:
	for a1 in A1:
		for m1 in M1:
			for c3a in C3A:
				for c3b in C3B:
					var reference := ""
					for skip in [false, true]:
						for now in [false, true]:
							var g := kit.story()
							kit.play_route_on(g, a1, m1, skip, now, c3a, c3b)
							var text: String = g.save_json()
							if reference == "":
								reference = text
							kit.eq(text, reference, "%s/%s/%s/%s skip=%s consume_now=%s" % [a1, m1, c3a, c3b, skip, now])
							g.free()
	return true


func _gating_identical() -> bool:
	var reference: Array = []
	for a1 in A1:
		for m1 in M1:
			for c3a in C3A:
				for c3b in C3B:
					var g := kit.story()
					kit.play_until(g, "m1", {"a1": a1, "m1": m1})
					var trace := c3_trace(g, c3a, c3b)
					if reference.is_empty():
						reference = trace
						# one entry per call: 13 objectives, dialogues node by node (start + one advance per node)
						kit.eq(reference.size(), 59, "trace covers every Chapter-3 step (%d)" % reference.size())
						kit.eq([reference[0], reference[-1]], [["c3a_talk_conductor"], ["c3c_inspect_crates"]], "from the station gate to the registry gate")
					kit.eq(trace, reference, "Chapter-3 gating of %s/%s/%s/%s equals the reference" % [a1, m1, c3a, c3b])
					g.free()
	return true


func _inventory_order() -> bool:
	var g := kit.story()
	var granted: Array = []
	g.item_granted.connect(func(id: String) -> void: granted.append(id))
	kit.play_until(g, "m1")
	kit.play_dialogue(g, "c3a_talk_conductor")
	g.inspect("c3a_inspect_departures")      # any order: the board before the weighbill
	g.inspect("c3a_inspect_weighbill")
	kit.play_dialogue(g, "c3a_pass_control")
	kit.play_dialogue(g, "c3a_talk_elena")
	g.choose("c3a_choose", "note_alone")
	kit.play_dialogue(g, "c3b_arrival")
	g.inspect("c3b_inspect_log")             # the log before the seating plan
	g.inspect("c3b_inspect_seating")
	g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate())
	g.inspect("c3b_inspect_booth")
	var expect := SLICE_ITEMS + ["ev_c3_departures", "ev_c3_weighbill", "ev_c3_travel_order", "ev_c3_booth_log", "ev_c3_seating", "ev_c3_carbon"]
	kit.eq(g.inventory(), expect, "inventory in acquisition order")
	kit.eq(granted, expect, "item_granted once per item, same order")
	kit.eq((g.journal()["evidence"] as Array).map(func(e: Dictionary) -> String: return e["id"]), expect, "journal evidence order")
	kit.eq(g.item_def("ev_c3_carbon").get("category"), "physical_clue", "carbon copy is a physical clue")
	kit.eq(g.item_def("ev_c3_weighbill").get("scene"), "L_C3_Station", "item scene")
	kit.play_dialogue(g, "c3b_talk_alexei")
	g.choose("c3b_choose", "report_delegation")
	kit.eq(g.inventory().size(), 12, "no item twice")
	return true


func _mid_chapter_round_trips() -> bool:
	var g := kit.story()
	kit.play_until(g, "m1", {"a1": "keep_private"})
	g.consume_cinematic("LS_X1_Final", true)
	kit.play_dialogue(g, "c3a_talk_conductor")
	g.inspect("c3a_inspect_weighbill")
	g.inspect("c3a_inspect_departures")
	g.start_dialogue("c3a_pass_control")
	for i in 3:
		g.advance_dialogue("c3a_pass_control")
	var h := kit.story()
	var r: Dictionary = h.load_json(g.save_json())
	kit.is_ok(r, "mid-dialogue Chapter-3 save loads")
	kit.eq(h.save_json(), g.save_json(), "byte-identical after the round trip")
	kit.eq(h.state["dialogue_progress"], {"c3a_pass_control": "c3a_ctrl_04"}, "cursor kept")
	var line: Dictionary = h.current_dialogue_line("c3a_pass_control")
	kit.eq([line.get("node"), line.get("speaker")], ["c3a_ctrl_04", "border_officer"], "resumes at the exact node")
	kit.eq(h.start_dialogue("c3a_pass_control").get("node"), "c3a_ctrl_04", "restart resumes, never resets")
	kit.eq(h.pending_cinematics(), g.pending_cinematics(), "unconsumed cinematics survive (A1, M1 hall, C3 trains)")
	kit.eq(h.journal(), g.journal(), "journal identical")
	kit.eq(h.objective_state("c3a_pass_control"), "available", "dialogue still open")
	while h.state["dialogue_progress"].has("c3a_pass_control"):
		h.advance_dialogue("c3a_pass_control")
	kit.ok(h.has_item("ev_c3_travel_order"), "the reloaded game finishes the control and gets the travel order")
	# palais: puzzle attempts and a second cursor
	kit.play_dialogue(h, "c3a_talk_elena")
	h.choose("c3a_choose", "ask_elena")
	kit.play_dialogue(h, "c3b_arrival")
	h.inspect("c3b_inspect_seating")
	h.inspect("c3b_inspect_log")
	h.solve_puzzle("c3b_solve_protocol", ["soviet", "secretariat", "chair", "reich"])
	h.solve_puzzle("c3b_solve_protocol", ["reich", "chair", "secretariat", "soviet"])
	var k := kit.story()
	kit.is_ok(k.load_json(h.save_json()), "palais save with failed attempts loads")
	kit.eq(k.puzzle_attempts("c3b_solve_protocol"), 2, "attempts preserved")
	kit.eq(k.puzzle_hint_available("c3b_solve_protocol"), true, "hint still available after reload")
	kit.eq(k.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()).get("solved"), true, "solved after reload")
	k.inspect("c3b_inspect_booth")
	k.start_dialogue("c3b_talk_alexei")
	for i in 5:
		k.advance_dialogue("c3b_talk_alexei")
	var m := kit.story()
	kit.is_ok(m.load_json(k.save_json()), "save in the middle of the meeting loads")
	kit.eq(m.current_dialogue_line("c3b_talk_alexei").get("node"), "c3b_meet_06", "meeting resumes at its node")
	kit.eq(m.state["puzzle_attempts"], {"c3b_solve_protocol": 2}, "solved puzzle keeps its attempt count")
	kit.eq(m.save_json(), k.save_json(), "byte-identical")
	return true


## A save taken before the M1 decision (current format, and a v0.3 file) loads and plays on into Chapter 3 up to
## the finale with exactly the state of an uninterrupted route.
func _continue_old_saves() -> bool:
	var straight := kit.play_verified_route("share_with_irina", "request_explanation", false, "note_alone", "report_delegation")
	var finish := func(g: Node, label: String) -> void:
		kit.eq(g.available(), ["m1_choose"], label + ": the M1 decision is pending")
		kit.step(g.choose("m1_choose", "request_explanation"), label + " m1 choice")
		kit.eq([g.current_scene, g.active_character, g.available()], ["L_C3_Station", "alexei", ["c3a_talk_conductor"]], label + ": into Chapter 3")
		kit.play_c3a(g, "note_alone")
		kit.play_c3b(g, "report_delegation")
		for stage in ["c3c", "c3d", "c3e", "c3f", "c3g"]:
			_play_stage(g, stage)
		for seq in g.pending_cinematics():
			kit.step(g.consume_cinematic(seq), label + " cinematic " + seq)
		kit.is_ok(g.finale(), label + ": finale")
		kit.eq(g.save_json(), straight.save_json(), label + ": same end state as an uninterrupted route")
	# 1. current format, taken right before m1_choose
	var b := kit.story()
	kit.play_a1(b, "share_with_irina")
	b.inspect("m1_inspect_plan_a")
	b.inspect("m1_inspect_plan_b")
	b.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	kit.play_dialogue(b, "m1_talk_emil")
	var c := kit.story()
	kit.is_ok(c.load_json(b.save_json()), "save before m1_choose loads")
	finish.call(c, "v3 save")
	# 2. mid-M1 dialogue (Emil) — resumes, then the decision
	var d := kit.story()
	kit.play_a1(d, "share_with_irina")
	d.inspect("m1_inspect_plan_a")
	d.inspect("m1_inspect_plan_b")
	d.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	d.start_dialogue("m1_talk_emil")
	d.advance_dialogue("m1_talk_emil")
	var e := kit.story()
	kit.is_ok(e.load_json(d.save_json()), "save in the middle of Emil's dialogue loads")
	kit.play_dialogue(e, "m1_talk_emil")
	finish.call(e, "mid-M1 save")
	# 3. v0.3 file (save_version 2) of the old runtime, taken before the M1 decision
	var rt := Legacy.new()
	for o in ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger",
			"a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans", "m1_talk_emil"]:
		rt.perform(o, "share_with_irina" if o == "a1_choose" else null)
	var v := kit.story()
	var mr: Dictionary = v.load_json(rt.save_json())
	kit.is_ok(mr, "v0.3 save before m1_choose migrates")
	finish.call(v, "v0.3 save")
	# 4. The pre-Chapter-3 build wrote v3 saves WITHOUT the seven Chapter-3 flags. Story.load_json (like the Python
	#    reference) merges flag defaults only for v0.3 files, so such a save is reported here; it is not part of
	#    the contract of the unchanged engine (see the tests stream report).
	var old: Dictionary = Kit.parse(b.save_json())
	for f in C3_FLAGS:
		old["flags"].erase(f)
	var probe: Dictionary = kit.story().validate_save_json(Kit.dumps(old))
	if probe.get("ok", false):
		var w := kit.story()
		kit.is_ok(w.load_json(Kit.dumps(old)), "pre-Chapter-3 v3 save loads")
		finish.call(w, "pre-Chapter-3 v3 save")
	else:
		print("      note: a v3 save of the pre-Chapter-3 build (no Chapter-3 flags) is rejected: %s" % probe.get("error"))
	return true


func _protocol_puzzle() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3a")
	kit.eq(g.puzzle_hint_available("c3b_solve_protocol"), false, "no hint before the puzzle is open")
	kit.is_err(g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()), "locked before Kessler")
	kit.play_dialogue(g, "c3b_arrival")
	g.inspect("c3b_inspect_seating")
	var r: Dictionary = g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate())
	kit.eq(r.get("error_key"), "sys.err.locked", "locked until both clues are inspected")
	g.inspect("c3b_inspect_log")
	kit.eq(g.objective_state("c3b_solve_protocol"), "available", "open with both clue documents")
	kit.eq(g.puzzle_for("c3b_solve_protocol").get("clue_item_ids"), ["ev_c3_seating", "ev_c3_booth_log"], "clue items")
	# clue ownership is enforced (white-box: unreachable through the public API, the prerequisites grant the clues)
	var core = g.get("_core")
	core.state["inventory"].erase("ev_c3_booth_log")
	var mc: Dictionary = g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate())
	kit.eq([mc.get("ok"), mc.get("error"), mc.get("error_key")], [false, "Missing clues for puzzle", "sys.err.missing_clues"], "clue items required")
	kit.eq(g.puzzle_attempts("c3b_solve_protocol"), 0, "missing clue is not an attempt")
	core.state["inventory"].append("ev_c3_booth_log")
	# wrong order: a valid call that counts one attempt
	var w1: Dictionary = g.solve_puzzle("c3b_solve_protocol", ["soviet", "secretariat", "chair", "reich"])
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts"), w1.get("hint_available")], [true, false, 1, false], "display order is wrong: attempt 1, no hint yet")
	# malformed payloads (non-string items, not a list) are rejected and NOT counted
	for bad in [["chair", 1, "secretariat", "soviet"], [null, "reich", "secretariat", "soviet"], [["chair"], "reich", "secretariat", "soviet"],
			"chair,reich,secretariat,soviet", {"0": "chair"}, 4, null]:
		var e: Dictionary = g.solve_puzzle("c3b_solve_protocol", bad)
		kit.eq([e.get("ok"), e.get("error"), e.get("error_key")], [false, "Symbol puzzle expects a list of symbols", "sys.err.answer_format"],
			"malformed answer %s rejected" % Kit.fmt(bad))
	kit.eq(g.puzzle_attempts("c3b_solve_protocol"), 1, "malformed answers are not attempts")
	kit.eq(g.puzzle_hint_available("c3b_solve_protocol"), false, "still no hint after one failure")
	# A list of strings of the wrong length is a well-typed wrong answer: the engine (like the Python reference,
	# QUEST_DATABASE §4) counts it. Only the puzzle UI insists on four cards (ui.c3.protocol.incomplete).
	var w2: Dictionary = g.solve_puzzle("c3b_solve_protocol", ["chair", "reich", "secretariat"])
	kit.eq([w2.get("ok"), w2.get("solved"), w2.get("attempts"), w2.get("hint_available")], [true, false, 2, true], "wrong length: attempt 2, hint after 2 failures")
	kit.eq(g.solve_puzzle("c3b_solve_protocol", ["Chair", "reich", "secretariat", "soviet"]).get("attempts"), 3, "symbols are case-sensitive")
	kit.eq(g.flag("protocol_matched"), false, "nothing set by failures")
	var ok: Dictionary = g.solve_puzzle("c3b_solve_protocol", PackedStringArray(Kit.C3_PROTOCOL))
	kit.eq([ok.get("solved"), ok.get("attempts")], [true, 3], "PackedStringArray accepted; attempts kept")
	kit.eq(g.flag("protocol_matched"), true, "protocol_matched")
	kit.is_err(g.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()), "cannot solve twice")
	kit.eq(g.puzzle_hint_available("c3b_solve_protocol"), false, "no hint for a solved puzzle")
	kit.eq(g.available(), ["c3b_inspect_booth"], "booth 2 opens")
	return true


## [label, expected validator message]; _break() applies the corruption.
const BREAKS := [
	["Chapter 3 cannot be skipped", "Unreachable scene(s)"],
	["the station cannot skip the palais", "Unreachable scene(s)"],
	["palais played by its quest's character", "L_C3_Hall: quest protagonist mismatch"],
	["protocol solution built from its cards", "Puzzle display and solution differ"],
	["protocol clues reachable through prerequisites", "c3b_solve_protocol: inaccessible clue"],
	["carbon copy granted in its scene", "c3b_inspect_booth: item/quest scene mismatch"],
	["closing cinematic locked", "Missing locked cinematic(s)"],
	["finale needs Chapter 3", "Finale needs both quest events"],
	["palais not gated by its own event", "q_c3b_palais: self gated"],
	["meeting terminates", "dlg_c3b_meeting: no endpoint"],
	["c3a offers two options", "c3a_choose: fewer than 2 choices"],
]


static func _objective(d: Dictionary, quest_id: String, objective_id: String) -> Dictionary:
	return _find(_find(d["quests"]["quests"], quest_id).get("objectives", []), objective_id)


static func _break(label: String, d: Dictionary) -> void:
	match label:
		"Chapter 3 cannot be skipped":
			var s := _find(d["scenes"]["scenes"], "L_M1_Archive")
			s["next_scene"] = "L_X1_Montage"
		"the station cannot skip the palais":
			var s := _find(d["scenes"]["scenes"], "L_C3_Station")
			s["next_scene"] = "L_X1_Montage"
		"palais played by its quest's character":
			var s := _find(d["scenes"]["scenes"], "L_C3_Hall")
			s["protagonist"] = "alexei"
		"protocol solution built from its cards":
			var p := _find(d["puzzles"]["puzzles"], "pz_c3_protocol")
			p["solution"][0] = "presidium"
		"protocol clues reachable through prerequisites":
			var o := _objective(d, "q_c3b_palais", "c3b_solve_protocol")
			o["requires"] = ["c3b_inspect_seating"]
		"carbon copy granted in its scene":
			var it := _find(d["items"]["items"], "ev_c3_carbon")
			it["scene"] = "L_C3_Station"
		"closing cinematic locked":
			d["cinematics"]["sequences"].erase(_find(d["cinematics"]["sequences"], "LS_C3_Close"))
		"finale needs Chapter 3":
			d["quests"]["slice_end_requires"].erase("c3b_completed")
		"palais not gated by its own event":
			var q := _find(d["quests"]["quests"], "q_c3b_palais")
			q["requires_events"] = ["c3b_completed"]
		"meeting terminates":
			var nodes: Array = _find(d["dialogue"]["conversations"], "dlg_c3b_meeting")["nodes"]
			nodes[-1].erase("end")
			nodes[-1]["next"] = "c3b_meet_01"
		"c3a offers two options":
			var o := _objective(d, "q_c3a_arrival", "c3a_choose")
			o["choices"].pop_back()


func _integrity() -> bool:
	kit.is_ok(ENGINE.deep_validate_data(ENGINE.load_data()["data"]), "canonical data incl. Chapter 3 passes deep validation")
	for b in BREAKS:
		var d: Dictionary = ENGINE.load_data()["data"]
		_break(b[0], d)
		var r: Dictionary = ENGINE.deep_validate_data(d)
		kit.is_err(r, b[0])
		kit.eq(r.get("error"), b[1], b[0] + " (message)")
	return true
