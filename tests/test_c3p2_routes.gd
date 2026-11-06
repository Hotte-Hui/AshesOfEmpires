extends RefCounted
## Chapter 3 part 2 „Der eiserne Frieden“ (documentation/C3P2_DESIGN.md) through the public Story API and the
## presentation data: every choice combination of the whole chain (a1 × m1 × c3a × c3b × c3d × c3g = 144 routes),
## the gating order of the 19 part-2 objectives, scenes / protagonists / chapter key at every in-level switch, the
## cinematic queue of the night, meters per decision, the check puzzle, save/load at every part-2 step (incl. saves
## from before the c3b decision), locks, the line variants per route (no dead variant, fallback-only bases never
## heard), ChapterExt's "choice.<objective>" conditions and shared-level helpers, and the two level shells.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const CE_PATH := "res://scripts/core/chapter_ext.gd"

const A1 := ["share_with_irina", "keep_private"]
const M1 := ["preserve_evidence", "request_explanation"]
const C3A := ["ask_elena", "note_alone"]
const C3B := ["share_protocol", "search_elena", "report_delegation"]
const C3D := ["admit_plan", "pocket_plan"]
const C3G := ["split_by_language", "swap_halves", "hide_for_elena"]
const P2_SCENES := ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD", "L_C3_Quay"]
const PROTAGONIST := {"L_C3_RegistryA": "alexei", "L_C3_RegistryB": "konrad", "L_C3_RegistryC": "alexei",
	"L_C3_RegistryD": "konrad", "L_C3_Quay": "alexei", "L_C4_TunnelsA": "alexei"}
## Chapter 4 part 1 follows the quay since round 9 (documentation/C4_DESIGN.md §1); tests/test_c4_routes.gd covers it.
const C4_SCENES := ["L_C4_TunnelsA", "L_C4_AnnexA", "L_C4_TunnelsB", "L_C4_AnnexB"]
const REGISTRY := "res://scenes/levels/L_C3_Registry.tscn"
const QUAY := "res://scenes/levels/L_C3_Quay.tscn"
## data order = the order in which the canonical route completes them
const P2_OBJECTIVES := ["c3c_inspect_crates", "c3c_inspect_night_book", "c3c_talk_konrad",
	"c3d_inspect_intake", "c3d_inspect_drawer", "c3d_talk_compare", "c3d_solve_check", "c3d_inspect_plan",
	"c3d_talk_partner", "c3d_choose", "c3e_take_file", "c3e_try_ramp", "c3e_reach_konrad",
	"c3f_inspect_hose", "c3f_push_desk", "c3f_climb", "c3g_inspect_halves", "c3g_talk_konrad", "c3g_choose"]
const P2_ITEMS := ["ev_c3_cut_seal", "ev_c3_night_book", "ev_c3_intake_book", "ev_c3_scarf", "ev_c3_halves",
	"ev_c3_kordon_plan", "ev_c3_file", "ev_c3_bolt", "ev_c3_cut_hose", "ev_c3_escort_list"]
const EVENTS := ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed", "c3c_completed", "c3d_completed",
	"c3e_completed", "c3f_completed", "c3g_completed", "c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed",
	"slice_completed"]
const NIGHT_CINEMATICS := ["LS_C3_Close", "LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves"]
## Base lines that a variant always replaces in normal play (every option of an earlier mandatory choice is covered).
const FALLBACK_ONLY := ["c3c_night_04", "c3c_night_11", "c3d_cmp_04", "c3d_cmp_05"]
const P2_DIALOGUES := ["dlg_c3c_night", "dlg_c3d_compare", "dlg_c3d_partner", "dlg_c3e_smoke", "dlg_c3f_desk",
	"dlg_c3f_chute", "dlg_c3g_snow"]

var kit: Kit
var ext: RefCounted
var data: Dictionary = {}
var objectives: Dictionary = {}   # objective id -> objective
var conversations: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	ext = load(CE_PATH).new()
	data = ENGINE.load_data()["data"]
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			objectives[o["id"]] = o
	for c in data["dialogue"]["conversations"]:
		conversations[c["id"]] = c
	kit.run_case("all_144_choice_combinations", _all_combinations)
	kit.run_case("part2_gating_scenes_and_queue_step_by_step", _step_by_step)
	kit.run_case("part2_locked_before_and_outside_its_scenes", _locks)
	kit.run_case("check_puzzle_rules", _check_puzzle)
	kit.run_case("save_load_at_every_part2_step", _save_load)
	kit.run_case("old_saves_continue_into_part2", _old_saves)
	kit.run_case("variants_per_route", _variants)
	kit.run_case("choice_conditions_and_shared_level_helpers", _chapter_ext)
	kit.run_case("presentation_data_contract", _presentation)
	kit.run_case("level_shells", _level_shells)
	kit.run_case("engine_reads_the_switch_data", _engine_contract)
	kit.run_case("texts_german_typography", _texts)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Meters of a finished route (C3_DESIGN §2.4 + C3P2_DESIGN §2.4: every option raises exactly one meter).
## The Chapter-4 decision is the Kit default (name_marta: evidence_chain +1, C4_DESIGN §2.4).
static func meters(a1: String, m1: String, c3a: String, c3b: String, c3d: String, c3g: String, c4d := "name_marta") -> Dictionary:
	return {"irina_trust": int(a1 == "share_with_irina"), "alexei_secrecy": int(a1 == "keep_private"),
		"konrad_evidence": int(m1 == "preserve_evidence"), "office_suspicion": int(m1 == "request_explanation"),
		"elena_trust": int(c3a == "ask_elena") + int(c3b == "search_elena") + int(c3g == "hide_for_elena"),
		"evidence_chain": int(c3a == "note_alone") + int(c3d == "pocket_plan") + int(c3g == "split_by_language") + int(c4d == "name_marta"),
		"civilian_welfare": int(c4d == "protect_marta"),
		"alexei_konrad_trust": int(c3b == "share_protocol") + int(c3d == "admit_plan") + int(c3g == "swap_halves"),
		"kessler_alerted": int(c3b == "report_delegation")}


## Flags + "choice.<objective>" keys: what ChapterExt conditions see at this moment of the playthrough.
static func cond_flags(g: Node) -> Dictionary:
	var f: Dictionary = g.flags().duplicate()
	var h: Dictionary = g.choice_history()
	for k in h:
		f["choice." + str(k)] = h[k]
	return f


func _play_stage(g: Node, stage: String, choice := "") -> void:
	match stage:
		"c3c":
			kit.play_c3c(g)
		"c3d":
			kit.play_c3d(g, choice if choice != "" else "admit_plan")
		"c3e":
			kit.play_c3e(g)
		"c3f":
			kit.play_c3f(g)
		"c3g":
			kit.play_c3g(g, choice if choice != "" else "split_by_language")


## The API call that would complete `oid` (on locked / completed objectives only).
static func attempt(g: Node, oid: String, objs: Dictionary) -> Dictionary:
	match str(objs[oid].get("type")):
		"inspect":
			return g.inspect(oid)
		"dialogue":
			return g.start_dialogue(oid)
		"puzzle":
			return g.solve_puzzle(oid, Kit.C3_CHECK.duplicate())
		"choice":
			return g.choose(oid, str(objs[oid]["choices"][0]["id"]))
	return {}


func _sweep_locked(g: Node, where: String) -> void:
	for oid in P2_OBJECTIVES:
		if g.objective_state(oid) != "locked":
			continue
		var before: String = g.save_json()
		var r := attempt(g, oid, objectives)
		kit.eq([r.get("ok"), r.get("error_key")], [false, "sys.err.locked"], "%s: %s is locked" % [where, oid])
		kit.eq(g.save_json(), before, "%s: a locked attempt on %s changes nothing" % [where, oid])


static func _manifest(path: String) -> Dictionary:
	var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string(path))
	return r["value"] if r["ok"] and r["value"] is Dictionary else {}


## [{name, props}] of the Playfield children of a .tscn (text parse: node blocks with their properties).
static func _nodes_of(path: String) -> Array:
	var out: Array = []
	for block in FileAccess.get_file_as_string(path).split("\n[node "):
		var m := RegEx.create_from_string("^name=\"([^\"]+)\"").search(block)
		if m == null or not block.contains("parent=\"Playfield\""):
			continue
		var props := {}
		for line in block.split("\n"):
			var kv := RegEx.create_from_string("^([a-z_]+) = (.+)$").search(line)
			if kv:
				props[kv.get_string(1)] = kv.get_string(2).trim_prefix("\"").trim_suffix("\"")
		out.append({"name": m.get_string(1), "props": props})
	return out


# ------------------------------------------------------------------ cases
func _all_combinations() -> bool:
	var finals := {}
	var n := 0
	for a1 in A1:
		for m1 in M1:
			for c3a in C3A:
				for c3b in C3B:
					for c3d in C3D:
						for c3g in C3G:
							var label := "%s/%s/%s/%s/%s/%s" % [a1, m1, c3a, c3b, c3d, c3g]
							var g := kit.play_verified_route(a1, m1, false, c3a, c3b, c3d, c3g)
							var f: Dictionary = g.flags()
							var want := meters(a1, m1, c3a, c3b, c3d, c3g)
							for k in want:
								kit.eq(f[k], want[k], label + " " + k)
							for k in ["courier_files_seen", "protocol_matched", "elena_missing", "c17_confirmed",
									"signal_restored", "blueprint_match_confirmed", "slice_finished"]:
								kit.eq(f[k], true, label + " " + k)
							kit.eq(g.completed_events(), EVENTS, label + " events")
							kit.eq([g.current_scene, g.active_character], ["L_X1_Montage", "none"], label + " montage")
							kit.eq(g.inventory().slice(12, 22), P2_ITEMS, label + " part-2 evidence in order")
							kit.eq(g.completed_objectives().slice(24, 43), P2_OBJECTIVES, label + " part-2 objectives in data order")
							kit.eq(g.choice_history(), {"a1_choose": a1, "m1_choose": m1, "c3a_choose": c3a,
								"c3b_choose": c3b, "c3d_choose": c3d, "c3g_choose": c3g, "c4d_choose": "name_marta"}, label + " choices")
							kit.eq([g.is_finished(), g.is_finale_viewed(), g.pending_cinematics()], [true, true, []], label + " finished")
							finals[g.save_json()] = label
							n += 1
							g.free()
	kit.eq(n, 144, "every combination played")
	kit.eq(finals.size(), 144, "144 distinct end states")
	return true


func _step_by_step() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3b", {"c3b": "report_delegation"})
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C3_RegistryA", "alexei", "ui.chapter_c3"], "night: Alexei at the registry")
	kit.eq(g.current_quest().get("id"), "q_c3c_registry", "registry quest")
	kit.eq(g.pending_cinematics().slice(-2), ["LS_C3_Close", "LS_C3_Radio"], "c3b_completed queues the closing train, then the radio")
	kit.is_err(g.finale(), "finale locked at the registry")
	for cid in g.pending_cinematics():
		kit.step(g.consume_cinematic(cid, true), "consume " + cid)
	# [action, objective, available() afterwards, scene afterwards, cinematics queued by this step]
	var steps := [
		["inspect", "c3c_inspect_crates", ["c3c_inspect_night_book"], "L_C3_RegistryA", []],
		["inspect", "c3c_inspect_night_book", ["c3c_talk_konrad"], "L_C3_RegistryA", []],
		["talk", "c3c_talk_konrad", ["c3d_inspect_intake", "c3d_inspect_drawer"], "L_C3_RegistryB", []],
		["inspect", "c3d_inspect_drawer", ["c3d_inspect_intake"], "L_C3_RegistryB", []],
		["inspect", "c3d_inspect_intake", ["c3d_talk_compare"], "L_C3_RegistryB", []],
		["talk", "c3d_talk_compare", ["c3d_solve_check"], "L_C3_RegistryB", []],
		["solve", "c3d_solve_check", ["c3d_inspect_plan"], "L_C3_RegistryB", []],
		["inspect", "c3d_inspect_plan", ["c3d_talk_partner"], "L_C3_RegistryB", []],
		["talk", "c3d_talk_partner", ["c3d_choose"], "L_C3_RegistryB", []],
		["choose", "c3d_choose", ["c3e_take_file"], "L_C3_RegistryC", ["LS_C3_Fire"]],
		["inspect", "c3e_take_file", ["c3e_try_ramp"], "L_C3_RegistryC", []],
		["inspect", "c3e_try_ramp", ["c3e_reach_konrad"], "L_C3_RegistryC", []],
		["talk", "c3e_reach_konrad", ["c3f_inspect_hose"], "L_C3_RegistryD", []],
		["inspect", "c3f_inspect_hose", ["c3f_push_desk"], "L_C3_RegistryD", []],
		["talk", "c3f_push_desk", ["c3f_climb"], "L_C3_RegistryD", []],
		["talk", "c3f_climb", ["c3g_inspect_halves"], "L_C3_Quay", ["LS_C3_Escape"]],
		["inspect", "c3g_inspect_halves", ["c3g_talk_konrad"], "L_C3_Quay", []],
		["talk", "c3g_talk_konrad", ["c3g_choose"], "L_C3_Quay", []],
		["choose", "c3g_choose", ["c4a_inspect_shelf"], "L_C4_TunnelsA", ["LS_C3_Halves", "LS_C4_Homeward"]],
	]
	kit.eq(g.available(), ["c3c_inspect_crates"], "registry gate")
	_sweep_locked(g, "registry entry")
	for s in steps:
		var oid: String = s[1]
		var queued_before: Array = g.pending_cinematics()
		match s[0]:
			"talk":
				kit.play_dialogue(g, oid)
			"inspect":
				var r: Dictionary = g.inspect(oid)
				kit.is_ok(r, "inspect " + oid)
				kit.eq(r.get("changes", {}).get("items"), [objectives[oid]["grant_item"]], "%s grants its item" % oid)
			"solve":
				kit.eq(g.solve_puzzle(oid, Kit.C3_CHECK.duplicate()).get("solved"), true, "solve " + oid)
			"choose":
				kit.is_ok(g.choose(oid, g.choices_for(oid)[0]["id"]), "choose " + oid)
		kit.eq(g.available(), s[2], "available after %s %s" % [s[0], oid])
		kit.eq(g.current_scene, s[3], "scene after %s" % oid)
		if s[3] != "L_X1_Montage":
			kit.eq(g.active_character, PROTAGONIST[s[3]], "protagonist after %s" % oid)
			kit.eq(g.chapter_key(), "ui.chapter_c4" if str(s[3]).begins_with("L_C4_") else "ui.chapter_c3", "chapter after %s" % oid)
		var queued: Array = g.pending_cinematics().filter(func(c) -> bool: return not queued_before.has(c))
		kit.eq(queued, s[4], "cinematics queued by %s" % oid)
		if s[3] != "L_X1_Montage":
			kit.is_err(g.finale(), "finale locked after %s" % oid)
		_sweep_locked(g, "after " + oid)
	kit.ok(g.has_item("ev_c3_halves"), "the joint check grants the two halves at its last line")
	kit.is_err(g.finale(true), "finale locked after c3g: Chapter 4 follows")
	kit.play_c4a(g)
	kit.play_c4b(g)
	kit.play_c4c(g)
	kit.play_c4d(g)
	kit.eq([g.current_quest(), g.available()], [{}, []], "montage: no quest, nothing available")
	kit.is_ok(g.finale(true), "finale open after c4d")
	kit.eq(g.completed_events(), EVENTS, "events once each, in order")
	kit.eq(g.choice_history().get("c3d_choose"), "admit_plan", "first option recorded")
	return true


func _locks() -> bool:
	var g := kit.story()
	kit.eq(P2_OBJECTIVES.map(func(o: String) -> String: return g.objective_state(o)), P2_OBJECTIVES.map(func(_o) -> String: return "locked"), "all 19 locked in a new game")
	_sweep_locked(g, "new game")
	kit.play_until(g, "c3a")
	_sweep_locked(g, "palais")
	kit.play_c3b(g, "search_elena")
	kit.play_c3c(g)
	# invalid options never mutate; a recorded decision cannot be changed
	kit.play_c3d(g, "pocket_plan")
	kit.is_err(g.choose("c3d_choose", "admit_plan"), "c3d decided once only")
	kit.play_c3e(g)
	kit.play_c3f(g)
	kit.step(g.inspect("c3g_inspect_halves"), "halves")
	kit.play_dialogue(g, "c3g_talk_konrad")
	var before: String = g.save_json()
	for bad in ["", "Swap_Halves", "admit_plan", "split", 7, null]:
		var r: Dictionary = g.choose("c3g_choose", bad)
		kit.eq([r.get("ok"), r.get("error_key")], [false, "sys.err.invalid_choice"], "invalid option %s rejected" % Kit.fmt(bad))
		kit.eq(g.save_json(), before, "invalid option %s changes nothing" % Kit.fmt(bad))
	kit.is_ok(g.choose("c3g_choose", "hide_for_elena"), "valid option")
	kit.eq(g.flags()["elena_trust"], 3, "ask_elena + search_elena + hide_for_elena = the meter's maximum, never beyond")
	return true


func _check_puzzle() -> bool:
	var p: Dictionary = {}
	for x in data["puzzles"]["puzzles"]:
		if x["id"] == "pz_c3_check":
			p = x
	kit.eq([p.get("type"), p.get("scene"), p.get("hint_after_attempts"), p.get("retry_unlimited")],
		["symbol_order", "L_C3_RegistryB", 2, true], "existing puzzle type, registry B, hint after 2, unlimited")
	kit.eq(p.get("solution"), Kit.C3_CHECK, "solution = Kit.C3_CHECK (C3P2_DESIGN §2.7)")
	kit.eq(Kit.sorted(p.get("display_symbols", [])), Kit.sorted(p.get("solution", [])), "tray shows exactly the solution's cards")
	kit.ne(p.get("display_symbols"), p.get("solution"), "the tray is not already solved")
	for i in (p.get("solution", []) as Array).size():
		kit.ne(p["display_symbols"][i], p["solution"][i], "tray position %d differs from its answer" % i)
	var g := kit.story()
	kit.play_until(g, "c3c")
	kit.is_err(g.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate()), "locked before the halves are on the table")
	kit.step(g.inspect("c3d_inspect_intake"), "intake")
	kit.step(g.inspect("c3d_inspect_drawer"), "drawer")
	kit.eq(g.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate()).get("error_key"), "sys.err.locked", "locked until the halves are compared")
	kit.play_dialogue(g, "c3d_talk_compare")
	kit.eq(g.puzzle_for("c3d_solve_check").get("clue_item_ids"), ["ev_c3_halves", "ev_c3_intake_book"], "clue items")
	# clue ownership is enforced (white-box: the prerequisites grant the clues through the public API)
	var core = g.get("_core")
	core.state["inventory"].erase("ev_c3_halves")
	kit.eq(g.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate()).get("error_key"), "sys.err.missing_clues", "clues required")
	core.state["inventory"].append("ev_c3_halves")
	kit.eq(g.puzzle_attempts("c3d_solve_check"), 0, "a missing clue is not an attempt")
	var w1: Dictionary = g.solve_puzzle("c3d_solve_check", (p["display_symbols"] as Array).duplicate())
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts")], [true, false, 1], "tray order is wrong: attempt 1")
	kit.eq(g.puzzle_hint_available("c3d_solve_check"), false, "no hint after one failure")
	for bad in [["in_c17_44", 3, "par_4", "january"], "in_c17_44,out_2340,par_4,january", {"0": "in_c17_44"}, null]:
		kit.eq(g.solve_puzzle("c3d_solve_check", bad).get("error_key"), "sys.err.answer_format", "malformed %s rejected" % Kit.fmt(bad))
	kit.eq(g.puzzle_attempts("c3d_solve_check"), 1, "malformed answers are not attempts")
	var w2: Dictionary = g.solve_puzzle("c3d_solve_check", ["in_c17_44", "out_2340", "january", "par_4"])
	kit.eq([w2.get("solved"), w2.get("attempts")], [false, 2], "two pairs swapped: attempt 2")
	kit.eq(g.puzzle_hint_available("c3d_solve_check"), true, "hint after two failures")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "save with failed attempts loads")
	kit.eq([h.puzzle_attempts("c3d_solve_check"), h.puzzle_hint_available("c3d_solve_check")], [2, true], "attempts and hint survive a reload")
	var ok: Dictionary = h.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate())
	kit.eq([ok.get("solved"), ok.get("attempts"), h.available()], [true, 2, ["c3d_inspect_plan"]], "solved; Blatt 7 next")
	kit.eq(h.solve_puzzle("c3d_solve_check", Kit.C3_CHECK.duplicate()).get("error_key"), "sys.err.locked", "solved once only")
	# the UI texts of every card and row exist (the next phase builds the UI on them)
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for sym in p["solution"]:
		kit.ok(loc.has("ui.c3p2.check.card." + str(sym)), "card text of %s" % sym)
	for row in ["weighbill", "departures", "travel_order", "timetable"]:
		kit.ok(loc.has("ui.c3p2.check.row." + row), "row label %s" % row)
	for k in ["title", "subtitle", "instruction", "hint", "success", "wrong", "incomplete", "check", "undo", "reset", "close"]:
		kit.ok(loc.has("ui.c3p2.check." + k), "puzzle text %s" % k)
	kit.ok(loc.t("ui.c3p2.check.subtitle").contains("fiktiv"), "fiction note in the subtitle")
	return true


func _save_load() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3b", {"a1": "keep_private", "c3a": "note_alone", "c3b": "share_protocol"})
	var checkpoints := [0]
	var roundtrip := func(what: String) -> void:
		var h := kit.story()
		kit.is_ok(h.load_json(g.save_json()), "reload: " + what)
		kit.eq(h.save_json(), g.save_json(), "byte-identical: " + what)
		kit.eq([h.current_scene, h.active_character, h.available(), h.pending_cinematics()],
			[g.current_scene, g.active_character, g.available(), g.pending_cinematics()], "scene, protagonist, gates, queue: " + what)
		checkpoints[0] += 1
		h.free()
	roundtrip.call("registry entry with the night's cinematics queued")
	for oid in P2_OBJECTIVES:
		var o: Dictionary = objectives[oid]
		match str(o["type"]):
			"dialogue":
				g.start_dialogue(oid)
				while g.state["dialogue_progress"].has(oid):
					roundtrip.call("%s at %s" % [oid, g.state["dialogue_progress"][oid]])
					g.advance_dialogue(oid)
			"inspect":
				kit.step(g.inspect(oid), oid)
			"puzzle":
				g.solve_puzzle(oid, ["january", "par_4", "out_2340", "in_c17_44"])
				roundtrip.call("after a failed check")
				kit.step(g.solve_puzzle(oid, Kit.C3_CHECK.duplicate()), oid)
			"choice":
				kit.step(g.choose(oid, o["choices"][-1]["id"]), oid)
		roundtrip.call("after " + oid)
		if oid == "c3d_choose":
			kit.step(g.consume_cinematic("LS_C3_Fire", true), "fire watched")
			roundtrip.call("fire consumed, registry C")
	kit.play_c4a(g)
	kit.play_c4b(g)
	kit.play_c4c(g)
	kit.play_c4d(g)
	roundtrip.call("Chapter 4 played, montage")
	kit.is_ok(g.finale(false), "finale")
	roundtrip.call("finished")
	kit.ok(checkpoints[0] >= 70, "checkpoints exercised (%d)" % checkpoints[0])
	return true


## Saves of the round-7 build (taken before the c3b decision or earlier) load and play on through part 2 with the
## state of an uninterrupted route; a save that claims the old end (montage right after c3b) is rejected.
func _old_saves() -> bool:
	var straight := kit.play_verified_route("share_with_irina", "request_explanation", false, "ask_elena", "search_elena", "pocket_plan", "swap_halves")
	var b := kit.story()
	kit.play_until(b, "c3a", {"m1": "request_explanation"})
	kit.play_dialogue(b, "c3b_arrival")
	kit.step(b.inspect("c3b_inspect_seating"), "seating")
	kit.step(b.inspect("c3b_inspect_log"), "log")
	kit.step(b.solve_puzzle("c3b_solve_protocol", Kit.C3_PROTOCOL.duplicate()), "protocol")
	kit.step(b.inspect("c3b_inspect_booth"), "booth")
	kit.play_dialogue(b, "c3b_talk_alexei")
	var c := kit.story()
	kit.is_ok(c.load_json(b.save_json()), "save before c3b_choose (round 7) loads")
	kit.eq(c.available(), ["c3b_choose"], "the c3b decision is pending")
	kit.step(c.choose("c3b_choose", "search_elena"), "c3b")
	kit.eq([c.current_scene, c.active_character], ["L_C3_RegistryA", "alexei"], "the decision now leads into the night")
	kit.play_c3c(c)
	kit.play_c3d(c, "pocket_plan")
	kit.play_c3e(c)
	kit.play_c3f(c)
	kit.play_c3g(c, "swap_halves")
	kit.play_c4a(c)
	kit.play_c4b(c)
	kit.play_c4c(c)
	kit.play_c4d(c)
	for seq in c.pending_cinematics():
		kit.step(c.consume_cinematic(seq), "cinematic " + seq)
	kit.is_ok(c.finale(), "finale")
	kit.eq(c.save_json(), straight.save_json(), "same end state as an uninterrupted route")
	# the old end: c3b done, scene = montage (never autosaved; impossible through the UI) — rejected, not migrated
	var d := kit.story()
	kit.play_until(d, "c3b")
	var old: Dictionary = Kit.parse(d.save_json())
	old["current_scene"] = "L_X1_Montage"
	old["active_character"] = "none"
	var r: Dictionary = kit.story().validate_save_json(Kit.dumps(old))
	kit.eq([r.get("ok"), r.get("error")], [false, "Inconsistent save field: current_scene"], "a save claiming the old montage after c3b is rejected")
	# the round-7 flag table is unchanged: part 2 adds no flag (C3P2_DESIGN §1.1)
	var flag_names: Array = Kit.sorted(data["flags"]["flags"])
	kit.eq(flag_names.size(), 16, "16 flags, as in round 7")
	for e in ["c3c_completed", "c3d_completed", "c3e_completed", "c3f_completed", "c3g_completed"]:
		kit.ok((data["flags"]["events"] as Array).has(e), "event %s" % e)
	kit.eq(data["flags"]["events"][-1], "slice_completed", "slice_completed stays the last event")
	return true


func _variants() -> bool:
	var heard := {}          # variant key -> true
	var base_heard := {}     # node id -> true (base text spoken)
	var choice_variants := {}
	var reaction_keys := {}
	for a1 in A1:
		for m1 in M1:
			for c3a in C3A:
				for c3b in C3B:
					for c3d in C3D:
						var g := kit.story()
						kit.play_until(g, "c3b", {"a1": a1, "m1": m1, "c3a": c3a, "c3b": c3b})
						_hear(g, ["dlg_c3c_night", "dlg_c3d_compare", "dlg_c3d_partner"], heard, base_heard)
						kit.play_c3c(g)
						for opt in C3D:
							var v: Dictionary = ext.pick(ext.choice_text.get("c3d_choose", {}).get(opt, []), cond_flags(g))
							choice_variants[str(v.get("key", "base:" + opt))] = true
						kit.play_c3d(g, c3d)
						reaction_keys[str(ext.reaction("c3d_choose", c3d, cond_flags(g))[1])] = true
						_hear(g, ["dlg_c3e_smoke", "dlg_c3f_desk", "dlg_c3f_chute", "dlg_c3g_snow"], heard, base_heard)
						kit.play_c3e(g)
						kit.play_c3f(g)
						kit.step(g.inspect("c3g_inspect_halves"), "halves")
						kit.play_dialogue(g, "c3g_talk_konrad")
						for opt in C3G:
							var v2: Dictionary = ext.pick(ext.choice_text.get("c3g_choose", {}).get(opt, []), cond_flags(g))
							choice_variants[str(v2.get("key", "base:" + opt))] = true
						for opt in C3G:
							reaction_keys[str(ext.reaction("c3g_choose", opt, cond_flags(g))[1])] = true
						g.free()
	for node_id in ext.line_variants:
		if not _is_p2_node(str(node_id)):
			continue
		for v in ext.line_variants[node_id]:
			kit.ok(heard.has(str(v["key"])), "variant %s of %s is heard on some route" % [v["key"], node_id])
	for node_id in FALLBACK_ONLY:
		kit.ok(not base_heard.has(node_id), "%s: the base line is fallback-only (never heard in normal play)" % node_id)
	for node_id in ["c3c_night_01", "c3c_night_05", "c3c_night_13", "c3d_cmp_03", "c3d_par_06", "c3e_smk_06", "c3f_cht_02", "c3g_snw_06", "c3g_snw_11"]:
		kit.ok(base_heard.has(node_id), "%s: its base line is heard on some route" % node_id)
	for opt in ["c3d.admit_plan.report", "c3d.pocket_plan.evidence", "c3d.pocket_plan.suspicion", "c3g.split_by_language.secrecy",
			"c3g.swap_halves.trust", "c3g.hide_for_elena.elena"]:
		kit.ok(choice_variants.has("choice." + opt), "option variant choice.%s is offered on some route" % opt)
	for opt in ["admit_plan", "split_by_language", "swap_halves", "hide_for_elena"]:
		kit.ok(choice_variants.has("base:" + opt), "base text of %s is offered on some route" % opt)
	# M1 always raises konrad_evidence or office_suspicion: pocket_plan's base text is fallback-only (like C3 Befund 23)
	kit.ok(not choice_variants.has("base:pocket_plan"), "pocket_plan always shows an M1 variant in normal play")
	for k in ["dlg.c3p2.react.admit_plan", "dlg.c3p2.react.admit_plan.report", "dlg.c3p2.react.pocket_plan",
			"dlg.c3p2.react.split_by_language", "dlg.c3p2.react.swap_halves", "dlg.c3p2.react.hide_for_elena"]:
		kit.ok(reaction_keys.has(k), "reaction %s is spoken on some route" % k)
	return true


static func _is_p2_node(node_id: String) -> bool:
	for p in ["c3c_", "c3d_", "c3e_", "c3f_", "c3g_"]:
		if node_id.begins_with(p):
			return true
	return false


## Resolves every line of the given conversations with the conditions of this moment of the playthrough.
func _hear(g: Node, dialogue_ids: Array, heard: Dictionary, base_heard: Dictionary) -> void:
	var f := cond_flags(g)
	for did in dialogue_ids:
		for node in conversations[did]["nodes"]:
			var key: String = ext.line_key(str(node["id"]), str(node["text_key"]), f)
			if key == str(node["text_key"]):
				base_heard[str(node["id"])] = true
			else:
				heard[key] = true


func _chapter_ext() -> bool:
	var CE = load(CE_PATH)
	var f := {"elena_trust": 1, "choice.c3b_choose": "report_delegation"}
	kit.ok(CE.matches({"choice.c3b_choose": "report_delegation"}, f), "a recorded choice matches its id")
	kit.ok(not CE.matches({"choice.c3b_choose": "share_protocol"}, f), "…and no other option")
	kit.ok(CE.matches({"choice.c3b_choose": "report_delegation", "elena_trust": ">=1"}, f), "choice and flag conditions combine")
	kit.ok(not CE.matches({"choice.c3b_choose": "report_delegation", "elena_trust": ">=2"}, f), "…all must hold")
	# without the key in the dictionary the live Story answers ("" while undecided)
	var keep: String = Story.save_json()
	Story.new_game()
	kit.eq(CE.live_choice("a1_choose"), "", "undecided: empty")
	kit.ok(not CE.matches({"choice.a1_choose": "keep_private"}, {}), "an undecided choice never matches")
	kit.play_a1(Story, "keep_private")
	kit.eq(CE.live_choice("a1_choose"), "keep_private", "live choice history")
	kit.ok(CE.matches({"choice.a1_choose": "keep_private"}, {}), "live fallback when the dictionary lacks the key")
	kit.ok(not CE.matches({"choice.a1_choose": "keep_private"}, {"choice.a1_choose": "share_with_irina"}), "an explicit key wins over the live state")
	kit.is_ok(Story.load_json(keep), "live Story restored")
	# variants resolve with explicit flags (as memories pass them)
	kit.eq(ext.line_key("c3c_night_01", "dlg.c3p2.night_01", {"choice.c3b_choose": "share_protocol"}), "dlg.c3p2.night_01.share", "choice variant")
	kit.eq(ext.line_key("c3c_night_01", "dlg.c3p2.night_01", {"choice.c3b_choose": "search_elena"}), "dlg.c3p2.night_01", "base line")
	kit.eq(ext.line_key("c3f_cht_02", "dlg.c3p2.cht_02", {"alexei_konrad_trust": 0}), "dlg.c3p2.cht_02.distrust", "trust 0 variant")
	kit.eq(ext.line_key("c3f_cht_02", "dlg.c3p2.cht_02", {"alexei_konrad_trust": 1}), "dlg.c3p2.cht_02", "trust 1: base")
	# shared level files
	kit.eq(ext.scenes_of_level(REGISTRY), ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"], "four scenes share the registry")
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		kit.eq(ext.level_key(sid), "L_C3_RegistryA", "%s plays in the level of L_C3_RegistryA" % sid)
	kit.eq([ext.level_key("L_C3_Quay"), ext.level_key("L_C3_Hall"), ext.level_key("L_A1_Railyard")], ["L_C3_Quay", "L_C3_Hall", "L_A1_Railyard"], "own level files are their own key")
	kit.ok(ext.same_level("L_C3_RegistryA", "L_C3_RegistryD"), "A and D share the file")
	kit.ok(not ext.same_level("L_C3_RegistryD", "L_C3_Quay"), "the quay is another level")
	kit.ok(not ext.same_level("L_A1_Railyard", "L_A1_Railyard"), "scenes without a chapter file entry are never 'shared'")
	return true


func _presentation() -> bool:
	var scenes := {}
	for s in data["scenes"]["scenes"]:
		scenes[s["id"]] = s
	var chain: Array = []
	var cur = data["scenes"]["start_scene"]
	while cur != null:
		chain.append(cur)
		cur = scenes[cur]["next_scene"]
	kit.eq(chain.slice(chain.find("L_C3_Hall")), ["L_C3_Hall"] + P2_SCENES + C4_SCENES + ["L_X1_Montage"], "part 2 sits between the palais and Chapter 4")
	for sid in P2_SCENES:
		var s: Dictionary = scenes[sid]
		kit.eq(s["protagonist"], PROTAGONIST[sid], "%s protagonist" % sid)
		kit.eq(s["camera_mode"], "side_on_2d", "%s side view" % sid)
		kit.eq(ext.spawn_for(sid), s["entry_spawn"], "%s entry spawn mirrored in c3.json" % sid)
		kit.eq(ext.level_path(sid), QUAY if sid == "L_C3_Quay" else REGISTRY, "%s level file" % sid)
	kit.eq([ext.chapter_card("L_C3_RegistryA"), ext.chapter_card("L_C3_Quay")], [["ui.chapter_c3", "world.c3c.title"], ["ui.chapter_c3", "world.c3g.title"]], "chapter cards where a level loads")
	for sid in ["L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		kit.eq(ext.chapter_card(sid), [], "%s: no card at an in-level switch" % sid)
	# switches (TECHNICAL_ARCHITECTURE §12.11 keys + grade): the partner of each registry scene and where he stands
	var man := _manifest("res://assets/environments/veltrava_registry/scene.json")
	var spawns: Dictionary = man.get("spawns", {})
	var sw: Dictionary = ext.switches
	kit.eq(sw.get("L_C3_RegistryA", {}).get("partner"), "konrad", "Konrad stands among the cards while Alexei arrives")
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		var st: Dictionary = sw.get(sid, {})
		kit.ok(spawns.has(str(st.get("partner_spawn", ""))), "%s: partner spawn %s exists" % [sid, st.get("partner_spawn")])
		kit.ok(spawns.has(str(scenes[sid]["entry_spawn"])), "%s: entry spawn exists" % sid)
		for k in st:
			kit.ok(k in ["switch_spawn", "partner", "partner_spawn", "partner_anim", "partner_hide_after", "glide", "music", "ambience", "grade"], "%s: known switch key %s" % [sid, k])
		if st.has("grade"):
			kit.ok(ext.grades.has(str(st["grade"])), "%s: grade %s defined" % [sid, st["grade"]])
	# the seam: each switch hands control to the protagonist where he stood as partner in the scene before
	kit.eq(scenes["L_C3_RegistryB"]["entry_spawn"], sw["L_C3_RegistryA"]["partner_spawn"], "B starts where Konrad stood in A")
	kit.eq(scenes["L_C3_RegistryC"]["entry_spawn"], sw["L_C3_RegistryB"]["partner_spawn"], "C starts where Alexei stood in B")
	kit.eq(scenes["L_C3_RegistryD"]["entry_spawn"], sw["L_C3_RegistryC"]["partner_spawn"], "D starts where Konrad stood in C")
	for g in ["registry", "registry_fire", "quay"]:
		kit.ok(ext.grades.has(g), "grade %s" % g)
	kit.ok(ext.palettes.has("registry"), "registry palette")
	# cinematics and puzzle UI registered (scenes come from their streams this round)
	for cid in ["LS_C3_Radio", "LS_C3_Fire", "LS_C3_Escape", "LS_C3_Halves"]:
		kit.ok(str(ext.cinematics.get(cid, "")).begins_with("res://scenes/cinematics/ch3_"), "%s registered" % cid)
		kit.ok((ENGINE.LOCKED_CINEMATICS as Array).has(cid), "%s in the validator list" % cid)
	var seq_ids: Array = data["cinematics"]["sequences"].map(func(s: Dictionary) -> String: return s["id"])
	kit.eq(seq_ids.find("LS_C3_Radio"), seq_ids.find("LS_C3_Close") + 1, "the radio directly follows the closing train (data order)")
	kit.eq(ext.puzzles.get("c3d_solve_check"), "res://scenes/ui/CheckPuzzle.tscn", "check puzzle UI path")
	# expressions for every part-2 node; dialogue lines of part 2 are spoken by the two protagonists only
	for did in P2_DIALOGUES:
		for node in conversations[did]["nodes"]:
			kit.ok(ext.line_expr.has(node["id"]), "%s has an expression" % node["id"])
			kit.ok(str(node["speaker"]) in ["alexei", "konrad"], "%s: spoken by a protagonist" % node["id"])
	return true


func _level_shells() -> bool:
	var files := {REGISTRY: "res://assets/environments/veltrava_registry/scene.json", QUAY: "res://assets/environments/veltrava_quay/scene.json"}
	var placed := {}     # objective -> count
	for path in files:
		var man := _manifest(files[path])
		kit.eq(man.get("world_size"), [1920, 360], "%s: 1920x360" % path)
		var hs: Dictionary = (man.get("hotspots", {}) as Dictionary).duplicate()
		var xh: Dictionary = _manifest(str(files[path]).get_base_dir() + "/explore_hotspots.json").get("hotspots", {})
		for k in xh:     # exploration spots (Level._merge_explore_hotspots; scene.json wins on name clashes)
			if not hs.has(k):
				hs[k] = xh[k]
		var poly := PackedVector2Array()
		for q in man.get("walkable", []):
			poly.append(Vector2(float(q[0]), float(q[1])))
		for name in hs:
			var p := Vector2(float(hs[name][0]), float(hs[name][1]))
			kit.ok(Geometry2D.is_point_in_polygon(p, poly), "%s: hotspot %s on the walkable floor" % [path, name])
		for name in man.get("spawns", {}):
			var sp: Array = man["spawns"][name]
			kit.ok(Geometry2D.is_point_in_polygon(Vector2(float(sp[0]), float(sp[1])), poly), "%s: spawn %s on the walkable floor" % [path, name])
		for nd in _nodes_of(path):
			var pr: Dictionary = nd["props"]
			if pr.has("hotspot_id"):
				kit.ok(hs.has(pr["hotspot_id"]), "%s/%s: hotspot %s exists" % [path, nd["name"], pr["hotspot_id"]])
			if pr.has("objective_id"):
				var oid: String = pr["objective_id"]
				placed[oid] = int(placed.get(oid, 0)) + 1
				kit.ok(objectives.has(oid), "%s/%s: objective %s exists" % [path, nd["name"], oid])
				if objectives.has(oid):
					kit.eq(pr.get("kind"), objectives[oid]["type"], "%s: interactable kind = objective type" % oid)
					var scene := str(_quest_of(oid).get("scene", ""))
					kit.eq(ext.level_path(scene), path, "%s: placed in the level file of its scene" % oid)
					if pr.get("kind") in ["dialogue", "choice"]:
						var partner := "konrad" if PROTAGONIST.get(scene, "") == "alexei" else "alexei"
						kit.eq(pr.get("npc_id"), partner, "%s: spoken with the partner" % oid)
		# the shell loads headless: manifest, spawns, hotspot placement
		var lvl: Node = (load(path) as PackedScene).instantiate()
		lvl.set("ambience", "")
		lvl.set("music", "")
		kit.mount(lvl)
		kit.ok(lvl.get("manifest") is Dictionary and not (lvl.manifest as Dictionary).is_empty(), "%s: manifest loaded" % path)
		kit.ok(lvl.get_node_or_null("WalkLimits") != null, "%s: walk limits built" % path)
		var first: String = "SP_C3_Gate" if path == REGISTRY else "SP_C3_Quay"
		kit.eq(lvl.get_spawn(first), Vector2(man["spawns"][first][0], man["spawns"][first][1]), "%s: entry spawn" % path)
		for c in lvl.playfield.get_children():
			var hid = c.get("hotspot_id")
			if hid != null and str(hid) != "" and hs.has(str(hid)):
				var off: Vector2 = c.get("hotspot_offset") if c.get("hotspot_offset") != null else Vector2.ZERO
				kit.eq(c.position, Vector2(float(hs[str(hid)][0]), float(hs[str(hid)][1])) + off, "%s/%s placed on %s" % [path, c.name, hid])
		lvl.free()
	for oid in P2_OBJECTIVES:
		kit.eq(placed.get(oid, 0), 1, "%s has exactly one interactable" % oid)
	# protagonists are not authored as NPCs in the registry (the partner comes from the switch settings, §12.11)
	for nd in _nodes_of(REGISTRY):
		kit.ok(not (str(nd["props"].get("char_id", "")) in ["alexei", "konrad"]), "registry: %s is not a protagonist NPC" % nd["name"])
	var quay_npcs: Array = _nodes_of(QUAY).filter(func(nd) -> bool: return nd["props"].has("char_id")).map(func(nd) -> String: return nd["props"]["char_id"])
	kit.eq(Kit.sorted(quay_npcs), Kit.sorted(["konrad", "typist", "border_officer", "kessler", "voronova", "journalist"]), "quay people (existing characters only)")
	return true


## The director (TECHNICAL_ARCHITECTURE §12.11, engine stream) reads this round's data as intended: one level file for
## the registry scenes, a partner for each of them, the quay a level of its own. Public Game API only; skipped with a
## note while the engine side is not there.
func _engine_contract() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game") if Kit.root() else null
	if game == null or not (game.has_method("level_file") and game.has_method("is_switch_scene") and game.has_method("scene_partner")):
		print("      note: Game without the §12.11 switch API — engine contract not checked")
		return true
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		kit.eq(game.level_file(sid), REGISTRY, "%s plays in the registry file" % sid)
		kit.ok(game.is_switch_scene(sid), "%s is a switch scene" % sid)
	kit.eq(game.level_file("L_C3_Quay"), QUAY, "the quay file")
	kit.ok(not game.is_switch_scene("L_C3_Quay"), "the quay is reached by a level load")
	kit.eq([game.scene_partner("L_C3_RegistryA"), game.scene_partner("L_C3_RegistryB"), game.scene_partner("L_C3_RegistryC"),
		game.scene_partner("L_C3_RegistryD"), game.scene_partner("L_C3_Quay")], ["konrad", "alexei", "konrad", "alexei", ""],
		"partners: Konrad waits in A; afterwards always the one who just had control; nobody stands in on the quay")
	return true


func _quest_of(oid: String) -> Dictionary:
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			if o["id"] == oid:
				return q
	return {}


func _texts() -> bool:
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var keys: Array = []
	for oid in P2_OBJECTIVES:
		keys.append(objectives[oid]["text_key"])
		for c in objectives[oid].get("choices", []):
			keys.append(c["text_key"])
	for it in data["items"]["items"]:
		if P2_ITEMS.has(it["id"]):
			keys.append_array([it["name_key"], it["description_key"]])
	for did in P2_DIALOGUES:
		for node in conversations[did]["nodes"]:
			keys.append(node["text_key"])
	for f in ["de_c3p2_dialogue", "de_c3p2_cinematics", "de_c3p2_ui"]:
		var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/locale/%s.json" % f))
		kit.ok(r["ok"], f + " parses")
		if r["ok"]:
			keys.append_array((r["value"]["strings"] as Dictionary).keys())
	for sid in P2_SCENES:
		keys.append(data["scenes"]["scenes"].filter(func(s) -> bool: return s["id"] == sid)[0]["title_key"])
	kit.ok(keys.size() >= 150, "part-2 texts collected (%d)" % keys.size())
	var line_keys: Dictionary = {}
	for did in P2_DIALOGUES:
		for node in conversations[did]["nodes"]:
			line_keys[node["text_key"]] = true
	for node_id in ext.line_variants:
		if _is_p2_node(str(node_id)):
			for v in ext.line_variants[node_id]:
				line_keys[v["key"]] = true
	for k in keys:
		var t: String = loc.t(str(k))
		kit.ok(loc.has(str(k)) and t.strip_edges() != "", "%s has German text" % k)
		kit.ok(not t.contains("\""), "%s: German quotes („…“, ‚…‘), no ASCII double quote" % k)
		kit.ok(not t.contains(" - "), "%s: dashes are – (en dash), not -" % k)
		if line_keys.has(k) or str(k).begins_with("dlg.c3p2.react."):
			kit.ok(t.length() <= 140, "%s: spoken line ≤ 140 characters (%d)" % [k, t.length()])
	return true
