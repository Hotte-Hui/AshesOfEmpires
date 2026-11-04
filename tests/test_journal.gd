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
		{"id": "q_m1_wrong_blueprint", "title_key": "ui.chapter_m1", "character": "konrad", "state": "locked"}], "quests")
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


func _finished() -> bool:
	var g := kit.play_verified_route("keep_private", "request_explanation")
	var j: Dictionary = g.journal()
	kit.eq(j["people"], ["irina", "emil"], "people met")
	kit.eq((j["evidence"] as Array).map(func(e: Dictionary) -> String: return e["id"]),
		["ev_damaged_seal", "ev_timetable", "ev_ledger", "ev_plan_a", "ev_plan_b", "ev_emil_note"], "all evidence")
	kit.eq(j["decisions"], [
		{"objective": "a1_choose", "choice": "keep_private", "text_key": "choice.keep_private", "objective_text_key": "obj.a1_choice"},
		{"objective": "m1_choose", "choice": "request_explanation", "text_key": "choice.ask_official", "objective_text_key": "obj.m1_choice"}],
		"both decisions")
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
