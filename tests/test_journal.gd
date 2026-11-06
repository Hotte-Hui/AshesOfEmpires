extends RefCounted
## Story.journal(): objectives with state, evidence, people met, decisions — at every chapter boundary,
## mid-dialogue, and identical after a save/load round trip.

const Kit := preload("res://tests/support/test_kit.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("fresh_journal", _fresh)
	kit.run_case("people_met_follows_dialogue_cursor", _people_mid_dialogue)
	kit.run_case("evidence_in_acquisition_order", _evidence)
	kit.run_case("after_a1_decision", _after_a1)
	kit.run_case("chapter3_boundaries", _chapter3)
	kit.run_case("finished_slice", _finished)
	kit.run_case("journal_survives_save_load", _survives_save_load)
	kit.run_case("journal_is_a_copy", _is_copy)
	kit.cleanup()
	return kit.failures


static func _states(j: Dictionary) -> Dictionary:
	var out := {}
	for o in j["objectives"]:
		out[o["id"]] = o["state"]
	return out


func _fresh() -> bool:
	var g := kit.story()
	var j: Dictionary = g.journal()
	kit.eq(j["quests"], [
		{"id": "q_a1_last_signal", "title_key": "ui.chapter_a1", "character": "alexei", "state": "active"},
		{"id": "q_m1_wrong_blueprint", "title_key": "ui.chapter_m1", "character": "konrad", "state": "locked"},
		{"id": "q_c3a_arrival", "title_key": "ui.chapter_c3", "character": "alexei", "state": "locked"},
		{"id": "q_c3b_palais", "title_key": "ui.chapter_c3", "character": "konrad", "state": "locked"},
		{"id": "q_c3c_registry", "title_key": "ui.chapter_c3", "character": "alexei", "state": "locked"},
		{"id": "q_c3d_check", "title_key": "ui.chapter_c3", "character": "konrad", "state": "locked"},
		{"id": "q_c3e_smoke", "title_key": "ui.chapter_c3", "character": "alexei", "state": "locked"},
		{"id": "q_c3f_chute", "title_key": "ui.chapter_c3", "character": "konrad", "state": "locked"},
		{"id": "q_c3g_snow", "title_key": "ui.chapter_c3", "character": "alexei", "state": "locked"},
		{"id": "q_c4a_cellar", "title_key": "ui.chapter_c4", "character": "alexei", "state": "locked"},
		{"id": "q_c4b_loop", "title_key": "ui.chapter_c4", "character": "konrad", "state": "locked"},
		{"id": "q_c4c_siding", "title_key": "ui.chapter_c4", "character": "alexei", "state": "locked"},
		{"id": "q_c4d_annex", "title_key": "ui.chapter_c4", "character": "konrad", "state": "locked"},
		{"id": "q_c4e_depot", "title_key": "ui.chapter_c4", "character": "alexei", "state": "locked"},
		{"id": "q_c4f_platform", "title_key": "ui.chapter_c4", "character": "konrad", "state": "locked"},
		{"id": "q_c4g_press", "title_key": "ui.chapter_c4", "character": "alexei", "state": "locked"},
		{"id": "q_c4h_house", "title_key": "ui.chapter_c4", "character": "konrad", "state": "locked"}], "quests")
	kit.eq(_states(j), {"a1_talk_irina": "available", "a1_inspect_seal": "locked", "a1_inspect_timetable": "locked",
		"a1_solve_signal": "locked", "a1_inspect_ledger": "locked", "a1_choose": "locked"}, "only A1 objectives, gated")
	kit.eq(j["objectives"][0], {"id": "a1_talk_irina", "quest": "q_a1_last_signal", "text_key": "obj.a1_talk",
		"type": "dialogue", "state": "available"}, "objective entry shape")
	kit.eq(j["evidence"], [], "no evidence")
	kit.eq(j["people"], [], "nobody met")
	kit.eq(j["decisions"], [], "no decisions")
	kit.eq(j["chapter_key"], "ui.chapter_a1", "chapter")
	kit.eq(j["character"], "alexei", "character")
	kit.eq(j["scene"], "L_A1_Railyard", "scene")
	return true


func _people_mid_dialogue() -> bool:
	var g := kit.story()
	g.start_dialogue("a1_talk_irina")
	kit.eq(g.journal()["people"], ["irina"], "Irina met at her first line (protagonist excluded)")
	g.advance_dialogue("a1_talk_irina")
	kit.eq(g.journal()["people"], ["irina"], "Alexei's own line adds nobody")
	kit.eq(_states(g.journal())["a1_talk_irina"], "available", "dialogue objective still open mid-dialogue")
	return true


func _evidence() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_timetable")
	g.inspect("a1_inspect_seal")
	var ev: Array = g.journal()["evidence"]
	kit.eq(ev, [
		{"id": "ev_timetable", "name_key": "item.timetable.name", "description_key": "item.timetable.description", "category": "document"},
		{"id": "ev_damaged_seal", "name_key": "item.seal.name", "description_key": "item.seal.description", "category": "physical_clue"}],
		"evidence entries in the order they were found")
	kit.eq(_states(g.journal())["a1_solve_signal"], "available", "puzzle unlocked by both clues")
	return true


func _after_a1() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	for o in ["a1_inspect_seal", "a1_inspect_timetable"]:
		g.inspect(o)
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	g.choose("a1_choose", "share_with_irina")
	var j: Dictionary = g.journal()
	kit.eq(j["quests"][0]["state"], "complete", "A1 complete")
	kit.eq(j["quests"][1]["state"], "active", "M1 active")
	var st := _states(j)
	kit.eq(st.size(), 11, "objectives of both unlocked quests")
	kit.eq(st["a1_choose"], "complete", "a1 choice complete")
	kit.eq(st["m1_inspect_plan_a"], "available", "plan A available")
	kit.eq(st["m1_align_plans"], "locked", "overlay locked")
	kit.eq(j["decisions"], [{"objective": "a1_choose", "choice": "share_with_irina", "text_key": "choice.share_irina",
		"objective_text_key": "obj.a1_choice"}], "decision recorded with its text key")
	kit.eq((j["evidence"] as Array).map(func(e: Dictionary) -> String: return e["id"]),
		["ev_damaged_seal", "ev_timetable", "ev_ledger"], "A1 evidence")
	kit.eq(j["chapter_key"], "ui.chapter_m1", "chapter switched")
	kit.eq(j["character"], "konrad", "protagonist switched")
	return true


static func _ids(entries: Array) -> Array:
	return entries.map(func(e: Dictionary) -> String: return e["id"])


static func _quest_states(j: Dictionary) -> Array:
	return (j["quests"] as Array).map(func(q: Dictionary) -> String: return q["state"])


## The journal at the Chapter-3 boundaries: station (Alexei) after M1, people met mid-dialogue, the switch to
## the palais (Konrad) after c3a, the new speakers and both Chapter-3 decisions.
func _chapter3() -> bool:
	var g := kit.story()
	kit.play_until(g, "m1", {"a1": "share_with_irina", "m1": "request_explanation"})
	var j: Dictionary = g.journal()
	# Chapter 3 part 2 (C3P2_DESIGN.md) adds five more quests behind the palais.
	kit.eq(_quest_states(j), ["complete", "complete", "active", "locked", "locked", "locked", "locked", "locked", "locked",
		"locked", "locked", "locked", "locked", "locked", "locked", "locked", "locked"],
		"after M1: Chapter 3a active, 3b, part 2 and Chapter 4 locked")
	kit.eq(j["chapter_key"], "ui.chapter_c3", "chapter key of the station")
	kit.eq([j["scene"], j["character"]], ["L_C3_Station", "alexei"], "station, Alexei")
	var st := _states(j)
	kit.eq(st.size(), 17, "objectives of the three unlocked quests (6 + 5 + 6)")
	kit.ok(not st.has("c3b_arrival"), "palais objectives hidden while their quest is locked")
	kit.eq([st["c3a_talk_conductor"], st["c3a_inspect_weighbill"], st["c3a_choose"]], ["available", "locked", "locked"], "station gates")
	kit.eq(j["people"], ["irina", "emil"], "nobody new before the first Chapter-3 line")
	g.start_dialogue("c3a_talk_conductor")
	kit.eq(g.journal()["people"], ["irina", "emil", "conductor"], "conductor met at his first line")
	while g.state["dialogue_progress"].has("c3a_talk_conductor"):
		g.advance_dialogue("c3a_talk_conductor")
	g.inspect("c3a_inspect_weighbill")
	g.inspect("c3a_inspect_departures")
	g.start_dialogue("c3a_pass_control")
	g.advance_dialogue("c3a_pass_control")
	kit.eq(g.journal()["people"], ["irina", "emil", "conductor", "border_officer", "elena"],
		"border officer and Elena (interpreting at the control) met in order")
	while g.state["dialogue_progress"].has("c3a_pass_control"):
		g.advance_dialogue("c3a_pass_control")
	kit.eq(_ids(g.journal()["evidence"]).slice(6), ["ev_c3_weighbill", "ev_c3_departures", "ev_c3_travel_order"], "station evidence in order")
	kit.play_dialogue(g, "c3a_talk_elena")
	g.choose("c3a_choose", "note_alone")
	j = g.journal()
	kit.eq(_quest_states(j), ["complete", "complete", "complete", "active", "locked", "locked", "locked", "locked", "locked",
		"locked", "locked", "locked", "locked", "locked", "locked", "locked", "locked"], "after c3a: palais active")
	kit.eq([j["scene"], j["character"], j["chapter_key"]], ["L_C3_Hall", "konrad", "ui.chapter_c3"], "palais, Konrad, same chapter")
	kit.eq(_states(j)["c3b_arrival"], "available", "Kessler first")
	kit.eq(j["decisions"][-1], {"objective": "c3a_choose", "choice": "note_alone", "text_key": "choice.c3a.note_alone",
		"objective_text_key": "obj.c3a_choice"}, "c3a decision recorded with its text key")
	g.start_dialogue("c3b_arrival")
	kit.eq(g.journal()["people"], ["irina", "emil", "conductor", "border_officer", "elena", "kessler"], "Kessler met; Elena not twice")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "reload mid Chapter 3")
	kit.eq(h.journal(), g.journal(), "Chapter-3 journal identical after reload")
	return true


func _finished() -> bool:
	var g := kit.play_verified_route("keep_private", "request_explanation")
	var j: Dictionary = g.journal()
	# Chapter 3 adds the conductor, the border officer, Elena and Kessler, Chapter 4 Lev Sokolov, Marta Vogel and the
	# registrar, part 2 Maria Gorelowa, Nils Ekdahl, Hanna Adler, Kommissar Wendt and Kuhnert (non-protagonist speakers in
	# order; Irina, Marta and Lev are met before).
	kit.eq(j["people"], ["irina", "emil", "conductor", "border_officer", "elena", "kessler", "lev", "marta", "registrar",
		"maria", "journalist", "hanna", "wendt", "blockwart"], "people met")
	kit.eq(_ids(j["evidence"]),
		["ev_damaged_seal", "ev_timetable", "ev_ledger", "ev_plan_a", "ev_plan_b", "ev_emil_note",
		"ev_c3_weighbill", "ev_c3_departures", "ev_c3_travel_order", "ev_c3_seating", "ev_c3_booth_log", "ev_c3_carbon",
		"ev_c3_cut_seal", "ev_c3_night_book", "ev_c3_intake_book", "ev_c3_scarf", "ev_c3_halves", "ev_c3_kordon_plan",
		"ev_c3_file", "ev_c3_bolt", "ev_c3_cut_hose", "ev_c3_escort_list",
		"ev_c4_book_gap", "ev_c4_cut_signatures", "ev_c4_carbon", "ev_c4_tunnel_plan", "ev_c4_fresh_tracks", "ev_c4_notice",
		"ev_c4_route_board", "ev_c4_shaft", "ev_c4_card_de", "ev_c4_card_ru", "ev_c4_stencils", "ev_c4_wagon_inside",
		"ev_c4_drawer_s8", "ev_c4_annex_plan", "ev_c4_tube_slip",
		"ev_c4_special_order", "ev_c4_work_list", "ev_c4_press_notice", "ev_c4_departures_east", "ev_c4_courier_seals",
		"ev_c4_konrad_tracing", "ev_c4_guidebook", "ev_c4_card_ru_original", "ev_c4_card_whole", "ev_c4_house_notice",
		"ev_c4_house_cards"],
		"all evidence")
	kit.eq(j["decisions"], [
		{"objective": "a1_choose", "choice": "keep_private", "text_key": "choice.keep_private", "objective_text_key": "obj.a1_choice"},
		{"objective": "m1_choose", "choice": "request_explanation", "text_key": "choice.ask_official", "objective_text_key": "obj.m1_choice"},
		{"objective": "c3a_choose", "choice": "ask_elena", "text_key": "choice.c3a.ask_elena", "objective_text_key": "obj.c3a_choice"},
		{"objective": "c3b_choose", "choice": "share_protocol", "text_key": "choice.c3b.share_protocol", "objective_text_key": "obj.c3b_choice"},
		{"objective": "c3d_choose", "choice": "admit_plan", "text_key": "choice.c3d.admit_plan", "objective_text_key": "obj.c3d_choice"},
		{"objective": "c3g_choose", "choice": "split_by_language", "text_key": "choice.c3g.split_by_language", "objective_text_key": "obj.c3g_choice"},
		{"objective": "c4d_choose", "choice": "name_marta", "text_key": "choice.c4d.name_marta", "objective_text_key": "obj.c4d_choice"},
		{"objective": "c4g_choose", "choice": "publish_now", "text_key": "choice.c4g.publish_now", "objective_text_key": "obj.c4g_choice"}],
		"all eight decisions")
	kit.eq(j["objectives"].size(), 86, "every objective listed")
	for q in j["quests"]:
		kit.eq(q["state"], "complete", "quest %s complete" % q["id"])
	for o in j["objectives"]:
		kit.eq(o["state"], "complete", "objective %s complete" % o["id"])
	kit.eq(j["chapter_key"], "world.x1.title", "montage uses the scene title")
	kit.eq(j["character"], "none", "no playable character in the montage")
	return true


func _survives_save_load() -> bool:
	var g := kit.story()
	kit.play_dialogue(g, "a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.solve_puzzle("a1_solve_signal", Kit.A1_SYMBOLS.duplicate())
	g.inspect("a1_inspect_ledger")
	g.choose("a1_choose", "keep_private")
	g.inspect("m1_inspect_plan_b")
	g.inspect("m1_inspect_plan_a")
	g.solve_puzzle("m1_align_plans", Kit.M1_OVERLAY.duplicate())
	g.start_dialogue("m1_talk_emil")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "reload")
	kit.eq(h.journal(), g.journal(), "journal identical after reload")
	kit.eq(h.journal()["people"], ["irina", "emil"], "Emil met (dialogue in progress)")
	return true


func _is_copy() -> bool:
	var g := kit.story()
	var j: Dictionary = g.journal()
	j["objectives"].clear()
	j["people"].append("nobody")
	kit.eq(g.journal()["objectives"].size(), 6, "mutating the journal does not touch the engine")
	kit.eq(g.journal()["people"], [], "people unchanged")
	return true
