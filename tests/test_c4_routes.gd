extends RefCounted
## Chapter 4 part 1 „Stimmen unter Beton“ (documentation/C4_DESIGN.md) through the public Story API and the
## presentation data: every choice combination of the whole chain (a1 × m1 × c3a × c3b × c3d × c3g × c4d = 288 routes),
## the gating of the 22 C4 objectives step by step (four city changes, the cinematic queue, locks swept after every
## step), both puzzles (route overlay „Linie 74“, number chain „Die Nummernkette“), save/load at every C4 step,
## round-8 saves continuing into Chapter 4, the line variants per route (no dead variant, fallback-only bases never
## heard), the presentation contract of data/chapters/c4.json, the two level shells, the engine's reading of the
## data, German typography, and the end card's decision list in story order.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const CE_PATH := "res://scripts/core/chapter_ext.gd"

const A1 := ["share_with_irina", "keep_private"]
const M1 := ["preserve_evidence", "request_explanation"]
const C3A := ["ask_elena", "note_alone"]
const C3B := ["share_protocol", "search_elena", "report_delegation"]
const C3D := ["admit_plan", "pocket_plan"]
const C3G := ["split_by_language", "swap_halves", "hide_for_elena"]
const C4D := ["name_marta", "protect_marta"]
const C4_SCENES := ["L_C4_TunnelsA", "L_C4_AnnexA", "L_C4_TunnelsB", "L_C4_AnnexB"]
const PROTAGONIST := {"L_C4_TunnelsA": "alexei", "L_C4_AnnexA": "konrad", "L_C4_TunnelsB": "alexei",
	"L_C4_AnnexB": "konrad"}
const TUNNELS := "res://scenes/levels/L_C4_Tunnels.tscn"
const ANNEX := "res://scenes/levels/L_C4_Annex.tscn"
const ENVS := {TUNNELS: "res://assets/environments/karsk_tunnels/scene.json",
	ANNEX: "res://assets/environments/berlin_annex/scene.json"}
## data order = the order in which the canonical route (Kit) completes them
const C4_OBJECTIVES := ["c4a_inspect_shelf", "c4a_talk_lev", "c4a_inspect_book", "c4a_inspect_carbon",
	"c4a_talk_tunnel", "c4a_open_door", "c4b_inspect_notice", "c4b_talk_marta", "c4b_solve_routes",
	"c4b_inspect_column", "c4b_talk_ilse", "c4b_inspect_crates", "c4c_inspect_card", "c4c_inspect_stencils",
	"c4c_solve_numbers", "c4c_inspect_wagon", "c4c_talk_lev", "c4d_inspect_drawer", "c4d_inspect_plan",
	"c4d_inspect_tube", "c4d_talk_registrar", "c4d_choose"]
const C4_ITEMS := ["ev_c4_book_gap", "ev_c4_cut_signatures", "ev_c4_carbon", "ev_c4_tunnel_plan", "ev_c4_fresh_tracks",
	"ev_c4_notice", "ev_c4_route_board", "ev_c4_shaft", "ev_c4_card_de", "ev_c4_card_ru", "ev_c4_stencils",
	"ev_c4_wagon_inside", "ev_c4_drawer_s8", "ev_c4_annex_plan", "ev_c4_tube_slip"]
const EVENTS := ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed", "c3c_completed", "c3d_completed",
	"c3e_completed", "c3f_completed", "c3g_completed", "c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed",
	"slice_completed"]
const C4_CINEMATICS := ["LS_C4_Homeward", "LS_C4_Number", "LS_C4_Card", "LS_C4_Stamp", "LS_C4_Voices"]
const C4_DIALOGUES := ["dlg_c4a_lev", "dlg_c4a_tunnel", "dlg_c4b_marta", "dlg_c4b_ilse", "dlg_c4c_lev", "dlg_c4d_counter"]
## Base lines that a variant always replaces in normal play (a1 / m1 / c3g cover every option).
const FALLBACK_ONLY := ["c4a_lev_01", "c4b_mar_02", "c4c_sid_08"]
## Base lines with variants that some route still hears.
const BASE_HEARD := ["c4a_lev_04", "c4a_tun_08", "c4b_mar_04", "c4b_mar_12", "c4c_sid_10", "c4d_cnt_03"]
## C4_DESIGN §4: story hotspots (x at feet y 300), spawns and NPC anchors of the two level files.
const HOTSPOTS := {
	TUNNELS: {"book_shelf": 184, "desk_book": 372, "lev_cellar": 428, "lamp_table": 520, "tunnel_door": 664,
		"office_desk": 1346, "paint_stand": 1468, "wagon_side": 1590, "wagon_door": 1680, "lev_siding": 1772},
	ANNEX: {"door_9": 118, "timetable_case": 292, "marta_tram": 404, "column_s2": 646, "loading_hatch": 762,
		"drawer_s8": 1232, "plan_wall": 1376, "tube_station": 1548, "registrar_counter": 1716, "guard_annex": 1868}}
const SPAWNS := {TUNNELS: {"SP_C4_Stairs": [48, 300], "SP_C4_Office": [1322, 300]},
	ANNEX: {"SP_C4_Shelter": [236, 300], "SP_C4_Ladder": [902, 300]}}
## Each walk area of a file (C4_DESIGN §4): scene A left of the blocker, scene B right of it.
const AREAS := {"L_C4_TunnelsA": [18, 700], "L_C4_TunnelsB": [720, 1902], "L_C4_AnnexA": [18, 822],
	"L_C4_AnnexB": [846, 1902]}

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
	kit.run_case("all_288_choice_combinations", _all_combinations)
	kit.run_case("c4_gating_scenes_and_queue_step_by_step", _step_by_step)
	kit.run_case("c4_locked_before_its_scenes", _locks)
	kit.run_case("route_overlay_puzzle_rules", _routes_puzzle)
	kit.run_case("number_chain_puzzle_rules", _numbers_puzzle)
	kit.run_case("decision_options_and_meters", _decision)
	kit.run_case("save_load_at_every_c4_step", _save_load)
	kit.run_case("round8_saves_continue_into_chapter4", _old_saves)
	kit.run_case("variants_per_route", _variants)
	kit.run_case("presentation_data_contract", _presentation)
	kit.run_case("level_shells", _level_shells)
	kit.run_case("engine_reads_the_chapter4_data", _engine_contract)
	kit.run_case("texts_german_typography", _texts)
	kit.run_case("end_card_lists_every_decision_in_story_order", _end_card)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Meters of a finished route (C3_DESIGN §2.4, C3P2_DESIGN §2.4, C4_DESIGN §2.4: every option raises one meter).
static func meters(a1: String, m1: String, c3a: String, c3b: String, c3d: String, c3g: String, c4d: String) -> Dictionary:
	return {"irina_trust": int(a1 == "share_with_irina"), "alexei_secrecy": int(a1 == "keep_private"),
		"konrad_evidence": int(m1 == "preserve_evidence"), "office_suspicion": int(m1 == "request_explanation"),
		"elena_trust": int(c3a == "ask_elena") + int(c3b == "search_elena") + int(c3g == "hide_for_elena"),
		"evidence_chain": int(c3a == "note_alone") + int(c3d == "pocket_plan") + int(c3g == "split_by_language") + int(c4d == "name_marta"),
		"alexei_konrad_trust": int(c3b == "share_protocol") + int(c3d == "admit_plan") + int(c3g == "swap_halves"),
		"kessler_alerted": int(c3b == "report_delegation"), "civilian_welfare": int(c4d == "protect_marta")}


## Flags + "choice.<objective>" keys: what ChapterExt conditions see at this moment of the playthrough.
static func cond_flags(g: Node) -> Dictionary:
	var f: Dictionary = g.flags().duplicate()
	var h: Dictionary = g.choice_history()
	for k in h:
		f["choice." + str(k)] = h[k]
	return f


## The API call that would complete `oid` (on locked / completed objectives only).
static func attempt(g: Node, oid: String, objs: Dictionary) -> Dictionary:
	match str(objs[oid].get("type")):
		"inspect":
			return g.inspect(oid)
		"dialogue":
			return g.start_dialogue(oid)
		"puzzle":
			return g.solve_puzzle(oid, Kit.C4_NUMBERS.duplicate() if oid == "c4c_solve_numbers" else Kit.C4_ROUTES.duplicate())
		"choice":
			return g.choose(oid, str(objs[oid]["choices"][0]["id"]))
	return {}


func _sweep_locked(g: Node, where: String) -> void:
	for oid in C4_OBJECTIVES:
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


func _quest_of(oid: String) -> Dictionary:
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			if o["id"] == oid:
				return q
	return {}


func _play_c4(g: Node, c4d := "name_marta") -> void:
	kit.play_c4a(g)
	kit.play_c4b(g)
	kit.play_c4c(g)
	kit.play_c4d(g, c4d)


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
							for c4d in C4D:
								var label := "%s/%s/%s/%s/%s/%s/%s" % [a1, m1, c3a, c3b, c3d, c3g, c4d]
								var g := kit.play_verified_route(a1, m1, false, c3a, c3b, c3d, c3g, c4d)
								var f: Dictionary = g.flags()
								var want := meters(a1, m1, c3a, c3b, c3d, c3g, c4d)
								for k in want:
									kit.eq(f[k], want[k], label + " " + k)
								kit.ok(int(f["evidence_chain"]) <= 6 and int(f["civilian_welfare"]) <= 3, label + " meters in range")
								kit.eq(g.completed_events(), EVENTS, label + " events")
								kit.eq([g.current_scene, g.active_character], ["L_X1_Montage", "none"], label + " montage")
								kit.eq(g.inventory().slice(22), C4_ITEMS, label + " Chapter-4 evidence in order")
								kit.eq(g.completed_objectives().slice(43), C4_OBJECTIVES, label + " Chapter-4 objectives in data order")
								kit.eq(g.choice_history().get("c4d_choose"), c4d, label + " c4d recorded")
								kit.eq(g.choice_history().size(), 7, label + " seven decisions")
								kit.eq([g.is_finished(), g.is_finale_viewed(), g.pending_cinematics()], [true, true, []], label + " finished")
								finals[g.save_json()] = label
								n += 1
								g.free()
	kit.eq(n, 288, "every combination played")
	kit.eq(finals.size(), 288, "288 distinct end states")
	return true


func _step_by_step() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3g", {"c3g": "swap_halves"})
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C4_TunnelsA", "alexei", "ui.chapter_c4"], "Chapter 4 opens with Alexei in Karsk")
	kit.eq(g.current_quest().get("id"), "q_c4a_cellar", "cellar quest")
	kit.eq(g.pending_cinematics().slice(-2), ["LS_C3_Halves", "LS_C4_Homeward"], "c3g_completed queues the halves, then the journey home")
	kit.is_err(g.finale(), "finale locked in Chapter 4")
	for cid in g.pending_cinematics():
		kit.step(g.consume_cinematic(cid, true), "consume " + cid)
	# [action, objective, available() afterwards, scene afterwards, cinematics queued by this step]
	var steps := [
		["inspect", "c4a_inspect_shelf", ["c4a_talk_lev"], "L_C4_TunnelsA", []],
		["talk", "c4a_talk_lev", ["c4a_inspect_book"], "L_C4_TunnelsA", []],
		["inspect", "c4a_inspect_book", ["c4a_inspect_carbon"], "L_C4_TunnelsA", []],
		["inspect", "c4a_inspect_carbon", ["c4a_talk_tunnel"], "L_C4_TunnelsA", []],
		["talk", "c4a_talk_tunnel", ["c4a_open_door"], "L_C4_TunnelsA", []],
		["inspect", "c4a_open_door", ["c4b_inspect_notice"], "L_C4_AnnexA", ["LS_C4_Number"]],
		["inspect", "c4b_inspect_notice", ["c4b_talk_marta"], "L_C4_AnnexA", []],
		["talk", "c4b_talk_marta", ["c4b_solve_routes"], "L_C4_AnnexA", []],
		["solve", "c4b_solve_routes", ["c4b_inspect_column"], "L_C4_AnnexA", []],
		["inspect", "c4b_inspect_column", ["c4b_talk_ilse"], "L_C4_AnnexA", []],
		["talk", "c4b_talk_ilse", ["c4b_inspect_crates"], "L_C4_AnnexA", []],
		["inspect", "c4b_inspect_crates", ["c4c_inspect_card", "c4c_inspect_stencils"], "L_C4_TunnelsB", ["LS_C4_Card"]],
		["inspect", "c4c_inspect_stencils", ["c4c_inspect_card"], "L_C4_TunnelsB", []],
		["inspect", "c4c_inspect_card", ["c4c_solve_numbers"], "L_C4_TunnelsB", []],
		["solve", "c4c_solve_numbers", ["c4c_inspect_wagon"], "L_C4_TunnelsB", []],
		["inspect", "c4c_inspect_wagon", ["c4c_talk_lev"], "L_C4_TunnelsB", []],
		["talk", "c4c_talk_lev", ["c4d_inspect_drawer", "c4d_inspect_plan"], "L_C4_AnnexB", ["LS_C4_Stamp"]],
		["inspect", "c4d_inspect_plan", ["c4d_inspect_drawer"], "L_C4_AnnexB", []],
		["inspect", "c4d_inspect_drawer", ["c4d_inspect_tube"], "L_C4_AnnexB", []],
		["inspect", "c4d_inspect_tube", ["c4d_talk_registrar"], "L_C4_AnnexB", []],
		["talk", "c4d_talk_registrar", ["c4d_choose"], "L_C4_AnnexB", []],
		["choose", "c4d_choose", [], "L_X1_Montage", ["LS_C4_Voices"]],
	]
	kit.eq(g.available(), ["c4a_inspect_shelf"], "cellar gate")
	_sweep_locked(g, "cellar entry")
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
				var sol = Kit.C4_ROUTES.duplicate() if oid == "c4b_solve_routes" else Kit.C4_NUMBERS.duplicate()
				kit.eq(g.solve_puzzle(oid, sol).get("solved"), true, "solve " + oid)
			"choose":
				kit.is_ok(g.choose(oid, g.choices_for(oid)[1]["id"]), "choose " + oid)
		kit.eq(g.available(), s[2], "available after %s %s" % [s[0], oid])
		kit.eq(g.current_scene, s[3], "scene after %s" % oid)
		if s[3] != "L_X1_Montage":
			kit.eq(g.active_character, PROTAGONIST[s[3]], "protagonist after %s" % oid)
			kit.eq(g.chapter_key(), "ui.chapter_c4", "same chapter after %s" % oid)
			kit.is_err(g.finale(), "finale locked after %s" % oid)
		var queued: Array = g.pending_cinematics().filter(func(c) -> bool: return not queued_before.has(c))
		kit.eq(queued, s[4], "cinematics queued by %s" % oid)
		_sweep_locked(g, "after " + oid)
	kit.ok(g.has_item("ev_c4_tunnel_plan") and g.has_item("ev_c4_route_board"), "both dialogue items granted at their last line")
	kit.eq([g.current_quest(), g.available()], [{}, []], "montage: no quest, nothing available")
	kit.eq(g.choice_history().get("c4d_choose"), "protect_marta", "second option recorded")
	kit.eq(g.flags()["civilian_welfare"], 1, "protect_marta: civilian_welfare +1 (first use of the meter)")
	kit.is_ok(g.finale(true), "finale open after c4d")
	kit.eq(g.completed_events(), EVENTS, "events once each, in order")
	return true


func _locks() -> bool:
	var g := kit.story()
	_sweep_locked(g, "new game")
	for stage in ["m1", "c3b", "c3f"]:
		g.free()
		g = kit.story()
		kit.play_until(g, stage)
		_sweep_locked(g, "after " + stage)
	kit.play_c3g(g)
	kit.eq(g.available(), ["c4a_inspect_shelf"], "only the cellar gate after the quay")
	for oid in ["c4b_inspect_notice", "c4c_inspect_card", "c4d_inspect_drawer", "c4d_choose"]:
		kit.eq(attempt(g, oid, objectives).get("error_key"), "sys.err.locked", "%s locked while Alexei is in the cellar" % oid)
	g.free()
	return true


func _puzzle(id: String) -> Dictionary:
	for x in data["puzzles"]["puzzles"]:
		if x["id"] == id:
			return x
	return {}


func _routes_puzzle() -> bool:
	var p := _puzzle("pz_c4_routes")
	kit.eq([p.get("type"), p.get("scene"), p.get("hint_after_attempts"), p.get("retry_unlimited")],
		["overlay_alignment", "L_C4_AnnexA", 2, true], "overlay type (Konrad's M1 mechanic), tram loop, hint after 2, unlimited")
	kit.eq(p.get("solution"), Kit.C4_ROUTES, "solution = Kit.C4_ROUTES (C4_DESIGN §2.7)")
	kit.ne(p.get("solution"), {"rotation_steps": 0, "offset_x": 0, "offset_y": 0}, "the UI start pose is wrong")
	kit.ne(p.get("solution"), {"rotation_steps": 1, "offset_x": 0, "offset_y": 0}, "the autoplay's wrong pose is wrong")
	var g := kit.story()
	kit.play_until(g, "c4a")
	kit.step(g.inspect("c4b_inspect_notice"), "notice")
	kit.eq(g.solve_puzzle("c4b_solve_routes", Kit.C4_ROUTES.duplicate()).get("error_key"), "sys.err.locked", "locked until Marta gave her route")
	kit.play_dialogue(g, "c4b_talk_marta")
	kit.eq(g.puzzle_for("c4b_solve_routes").get("clue_item_ids"), ["ev_c4_notice", "ev_c4_route_board"], "clue items")
	var w1: Dictionary = g.solve_puzzle("c4b_solve_routes", {"rotation_steps": 0, "offset_x": 0, "offset_y": 0})
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts")], [true, false, 1], "start pose: attempt 1")
	kit.eq(g.puzzle_hint_available("c4b_solve_routes"), false, "no hint after one failure")
	for bad in [{"rotation_steps": 1, "offset_x": 3}, {"rotation_steps": 1, "offset_x": 3, "offset_y": -2.0},
			[1, 3, -2], null, {"rotation_steps": 1, "offset_x": 3, "offset_y": -2, "z": 0}]:
		kit.eq(g.solve_puzzle("c4b_solve_routes", bad).get("error_key"), "sys.err.answer_format", "malformed %s rejected" % Kit.fmt(bad))
	kit.eq(g.puzzle_attempts("c4b_solve_routes"), 1, "malformed answers are not attempts")
	var w2: Dictionary = g.solve_puzzle("c4b_solve_routes", {"rotation_steps": 5, "offset_x": 3, "offset_y": -2})
	kit.eq([w2.get("solved"), w2.get("attempts")], [false, 2], "rotation not reduced mod 4 is wrong (the UI submits 0–3): attempt 2")
	kit.eq(g.puzzle_hint_available("c4b_solve_routes"), true, "hint after two failures")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "save with failed attempts loads")
	var ok: Dictionary = h.solve_puzzle("c4b_solve_routes", Kit.C4_ROUTES.duplicate())
	kit.eq([ok.get("solved"), ok.get("attempts"), h.available()], [true, 2, ["c4b_inspect_column"]], "solved; the column next")
	kit.eq(h.solve_puzzle("c4b_solve_routes", Kit.C4_ROUTES.duplicate()).get("error_key"), "sys.err.locked", "solved once only")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for k in ["title", "subtitle", "instruction", "legend.shaft", "legend.loop", "wrong", "wrong_turned", "hint", "success",
			"btn.check", "btn.rotate", "btn.reset", "btn.close"]:
		kit.ok(loc.has("ui.c4.routes." + k), "UI text ui.c4.routes.%s" % k)
	g.free()
	h.free()
	return true


func _numbers_puzzle() -> bool:
	var p := _puzzle("pz_c4_numbers")
	kit.eq([p.get("type"), p.get("scene"), p.get("hint_after_attempts"), p.get("retry_unlimited")],
		["symbol_order", "L_C4_TunnelsB", 2, true], "symbol order (new TracePuzzle UI), the siding, hint after 2, unlimited")
	kit.eq(p.get("solution"), Kit.C4_NUMBERS, "solution = Kit.C4_NUMBERS (C4_DESIGN §2.7)")
	kit.eq(Kit.sorted(p.get("display_symbols", [])), Kit.sorted(p.get("solution", [])), "the tray shows exactly the solution's plates")
	for i in (p.get("solution", []) as Array).size():
		kit.ne(p["display_symbols"][i], p["solution"][i], "tray position %d differs from its answer (1-2-3-4 is wrong)" % i)
	# the chain the lamp shows: every plate lies over the face of the plate before it (the UI's own table)
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var sol: Array = p.get("solution", [])
	for i in sol.size():
		var under: String = loc.t("ui.c4.numbers.under." + str(sol[i]))
		if i == 0:
			kit.ok(not under.contains("„"), "the first plate has no older number under it")
		else:
			var prev_face: String = loc.t("ui.c4.numbers.card." + str(sol[i - 1]))
			var m := RegEx.create_from_string("„([^“]+)“").search(prev_face)
			kit.ok(m != null and under.contains(m.get_string(1)), "%s lies over %s" % [sol[i], sol[i - 1]])
	for k in ["title", "subtitle", "instruction", "lamp_on", "lamp_off", "wrong", "wrong_first", "incomplete", "hint",
			"success", "btn.check", "btn.undo", "btn.reset", "btn.lamp", "btn.close"]:
		kit.ok(loc.has("ui.c4.numbers." + k), "UI text ui.c4.numbers.%s" % k)
	for n in 4:
		kit.ok(loc.has("ui.c4.numbers.post.%d" % (n + 1)) and loc.has("ui.c4.numbers.log.%d" % (n + 1)), "post %d and its log line" % (n + 1))
	var g := kit.story()
	kit.play_until(g, "c4b")
	kit.eq(g.solve_puzzle("c4c_solve_numbers", Kit.C4_NUMBERS.duplicate()).get("error_key"), "sys.err.locked", "locked before card and stencils")
	kit.step(g.inspect("c4c_inspect_card"), "card")
	kit.eq(g.solve_puzzle("c4c_solve_numbers", Kit.C4_NUMBERS.duplicate()).get("error_key"), "sys.err.locked", "still locked without the stencils")
	kit.step(g.inspect("c4c_inspect_stencils"), "stencils")
	kit.eq(g.puzzle_for("c4c_solve_numbers").get("clue_item_ids"), ["ev_c4_card_ru", "ev_c4_stencils"], "clue items")
	var w1: Dictionary = g.solve_puzzle("c4c_solve_numbers", (p["display_symbols"] as Array).duplicate())
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts")], [true, false, 1], "tray order: attempt 1")
	for bad in [["n24318", 3, "n47702", "c1745"], "n24318,c1742,n47702,c1745", {"0": "n24318"}, null]:
		kit.eq(g.solve_puzzle("c4c_solve_numbers", bad).get("error_key"), "sys.err.answer_format", "malformed %s rejected" % Kit.fmt(bad))
	var w2: Dictionary = g.solve_puzzle("c4c_solve_numbers", ["n24318", "n47702", "c1742", "c1745"])
	kit.eq([w2.get("solved"), w2.get("attempts")], [false, 2], "the two middle layers swapped: attempt 2")
	kit.eq(g.puzzle_hint_available("c4c_solve_numbers"), true, "hint after two failures")
	var ok: Dictionary = g.solve_puzzle("c4c_solve_numbers", Kit.C4_NUMBERS.duplicate())
	kit.eq([ok.get("solved"), g.available()], [true, ["c4c_inspect_wagon"]], "solved; the wagon door next")
	g.free()
	return true


func _decision() -> bool:
	var g := kit.story()
	kit.play_until(g, "c4c")
	kit.step(g.inspect("c4d_inspect_drawer"), "drawer")
	kit.step(g.inspect("c4d_inspect_plan"), "plan")
	kit.step(g.inspect("c4d_inspect_tube"), "tube")
	kit.play_dialogue(g, "c4d_talk_registrar")
	kit.eq(g.choices_for("c4d_choose").map(func(c) -> String: return c["id"]), C4D, "two options, always both offered")
	var before: String = g.save_json()
	for bad in ["", "Name_Marta", "admit_plan", "protect", 7, null]:
		var r: Dictionary = g.choose("c4d_choose", bad)
		kit.eq([r.get("ok"), r.get("error_key")], [false, "sys.err.invalid_choice"], "invalid option %s rejected" % Kit.fmt(bad))
		kit.eq(g.save_json(), before, "invalid option %s changes nothing" % Kit.fmt(bad))
	var r2: Dictionary = g.choose("c4d_choose", "name_marta")
	kit.eq(r2.get("changes"), {"flags": {"evidence_chain": 2}, "objectives": ["c4d_choose"], "items": [],
		"events": ["c4d_completed"], "cinematics": ["LS_C4_Voices"], "scene": "L_X1_Montage"}, "name_marta changes")
	kit.eq(g.flags()["civilian_welfare"], 0, "name_marta leaves civilian_welfare")
	kit.eq(g.choose("c4d_choose", "protect_marta").get("error_key"), "sys.err.locked", "decided once only")
	g.free()
	# the flag table is unchanged: Chapter 4 adds no flag (C4_DESIGN §1.1)
	kit.eq((data["flags"]["flags"] as Dictionary).size(), 16, "16 flags, as in round 7/8")
	for e in ["c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed"]:
		kit.ok((data["flags"]["events"] as Array).has(e), "event %s" % e)
	kit.eq(data["flags"]["events"][-1], "slice_completed", "slice_completed stays the last event")
	kit.eq(data["quests"]["slice_end_requires"], EVENTS.slice(0, EVENTS.size() - 1), "the finale needs all thirteen quest events")
	return true


func _save_load() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3g", {"a1": "keep_private", "m1": "request_explanation", "c3b": "report_delegation", "c3g": "hide_for_elena"})
	var checkpoints := [0]
	var roundtrip := func(what: String) -> void:
		var h := kit.story()
		kit.is_ok(h.load_json(g.save_json()), "reload: " + what)
		kit.eq(h.save_json(), g.save_json(), "byte-identical: " + what)
		kit.eq([h.current_scene, h.active_character, h.available(), h.pending_cinematics()],
			[g.current_scene, g.active_character, g.available(), g.pending_cinematics()], "scene, protagonist, gates, queue: " + what)
		checkpoints[0] += 1
		h.free()
	roundtrip.call("Karsk cellar entry with the halves and the journey home queued")
	for oid in C4_OBJECTIVES:
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
				if oid == "c4b_solve_routes":
					g.solve_puzzle(oid, {"rotation_steps": 2, "offset_x": 3, "offset_y": -2})
					roundtrip.call("after a failed overlay")
					kit.step(g.solve_puzzle(oid, Kit.C4_ROUTES.duplicate()), oid)
				else:
					g.solve_puzzle(oid, ["c1742", "n24318", "n47702", "c1745"])
					roundtrip.call("after a failed number chain")
					kit.step(g.solve_puzzle(oid, Kit.C4_NUMBERS.duplicate()), oid)
			"choice":
				kit.step(g.choose(oid, o["choices"][-1]["id"]), oid)
		roundtrip.call("after " + oid)
	kit.is_ok(g.finale(false), "finale")
	roundtrip.call("finished")
	kit.ok(checkpoints[0] >= 85, "checkpoints exercised (%d)" % checkpoints[0])
	g.free()
	return true


## A round-8 autosave on the quay (before c3g_choose — autosaves never store the montage) plays on through Chapter 4
## with the state of an uninterrupted route; a save claiming the round-8 end (montage right after c3g) is rejected.
func _old_saves() -> bool:
	var straight := kit.play_verified_route("keep_private", "preserve_evidence", false, "note_alone", "share_protocol",
		"pocket_plan", "hide_for_elena", "protect_marta")
	var b := kit.story()
	kit.play_until(b, "c3f", {"a1": "keep_private", "c3a": "note_alone", "c3d": "pocket_plan"})
	kit.step(b.inspect("c3g_inspect_halves"), "halves")
	kit.play_dialogue(b, "c3g_talk_konrad")
	var c := kit.story()
	kit.is_ok(c.load_json(b.save_json()), "save before c3g_choose (round 8) loads")
	kit.eq(c.available(), ["c3g_choose"], "the c3g decision is pending")
	kit.step(c.choose("c3g_choose", "hide_for_elena"), "c3g")
	kit.eq([c.current_scene, c.active_character], ["L_C4_TunnelsA", "alexei"], "the decision now leads to Karsk")
	_play_c4(c, "protect_marta")
	for seq in c.pending_cinematics():
		kit.step(c.consume_cinematic(seq), "cinematic " + seq)
	kit.is_ok(c.finale(), "finale")
	kit.eq(c.save_json(), straight.save_json(), "same end state as an uninterrupted route")
	var d := kit.story()
	kit.play_until(d, "c3g")
	var old: Dictionary = Kit.parse(d.save_json())
	old["current_scene"] = "L_X1_Montage"
	old["active_character"] = "none"
	var r: Dictionary = kit.story().validate_save_json(Kit.dumps(old))
	kit.eq([r.get("ok"), r.get("error")], [false, "Inconsistent save field: current_scene"], "a save claiming the round-8 montage after c3g is rejected")
	for x in [straight, b, c, d]:
		x.free()
	return true


func _variants() -> bool:
	var heard := {}          # variant key -> true
	var base_heard := {}     # node id -> true (base text spoken)
	var choice_variants := {}
	var reaction_keys := {}
	for a1 in A1:
		for m1 in M1:
			for c3b in C3B:
				for c3d in C3D:
					for c3g in C3G:
						var g := kit.story()
						kit.play_until(g, "c3g", {"a1": a1, "m1": m1, "c3b": c3b, "c3d": c3d, "c3g": c3g})
						_hear(g, ["dlg_c4a_lev", "dlg_c4a_tunnel"], heard, base_heard)
						kit.play_c4a(g)
						_hear(g, ["dlg_c4b_marta", "dlg_c4b_ilse"], heard, base_heard)
						kit.play_c4b(g)
						_hear(g, ["dlg_c4c_lev"], heard, base_heard)
						kit.play_c4c(g)
						_hear(g, ["dlg_c4d_counter"], heard, base_heard)
						kit.step(g.inspect("c4d_inspect_drawer"), "drawer")
						kit.step(g.inspect("c4d_inspect_plan"), "plan")
						kit.step(g.inspect("c4d_inspect_tube"), "tube")
						kit.play_dialogue(g, "c4d_talk_registrar")
						for opt in C4D:
							var v: Dictionary = ext.pick(ext.choice_text.get("c4d_choose", {}).get(opt, []), cond_flags(g))
							choice_variants[str(v.get("key", "base:" + opt))] = true
							reaction_keys[str(ext.reaction("c4d_choose", opt, cond_flags(g))[1])] = true
						g.free()
	for node_id in ext.line_variants:
		if not str(node_id).begins_with("c4"):
			continue
		for v in ext.line_variants[node_id]:
			kit.ok(heard.has(str(v["key"])), "variant %s of %s is heard on some route" % [v["key"], node_id])
	for node_id in FALLBACK_ONLY:
		kit.ok(not base_heard.has(node_id), "%s: the base line is fallback-only (never heard in normal play)" % node_id)
		kit.ok(ext.line_variants.has(node_id), "%s has the variants that replace it" % node_id)
	for node_id in BASE_HEARD:
		kit.ok(base_heard.has(node_id), "%s: its base line is heard on some route" % node_id)
	for k in ["choice.c4d.name_marta.pocket", "choice.c4d.protect_marta.report", "base:name_marta", "base:protect_marta"]:
		kit.ok(choice_variants.has(k), "option text %s is offered on some route" % k)
	for k in ["dlg.c4.react.name_marta", "dlg.c4.react.protect_marta"]:
		kit.ok(reaction_keys.has(k), "reaction %s is spoken" % k)
	# every option variant keeps the words the reaction answers (C3P2 rule)
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.ok(loc.t("choice.c4d.name_marta.pocket").begins_with("Marta Vogels Namen nennen"), "name variant keeps „Marta Vogels Namen nennen“")
	kit.ok(loc.t("choice.c4d.protect_marta.report").contains("auf der Straße gehört"), "protect variant keeps ‚auf der Straße gehört‘")
	return true


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


func _presentation() -> bool:
	var scenes := {}
	for s in data["scenes"]["scenes"]:
		scenes[s["id"]] = s
	var chain: Array = []
	var cur = data["scenes"]["start_scene"]
	while cur != null:
		chain.append(cur)
		cur = scenes[cur]["next_scene"]
	kit.eq(chain, Kit.CHAIN, "the whole chain = Kit.CHAIN")
	kit.eq(chain.slice(chain.find("L_C3_Quay")), ["L_C3_Quay"] + C4_SCENES + ["L_X1_Montage"], "Chapter 4 sits between the quay and the montage")
	for sid in C4_SCENES:
		var s: Dictionary = scenes[sid]
		kit.eq(s["protagonist"], PROTAGONIST[sid], "%s protagonist" % sid)
		kit.eq(s["camera_mode"], "side_on_2d", "%s side view" % sid)
		kit.eq(ext.spawn_for(sid), s["entry_spawn"], "%s entry spawn mirrored in c4.json" % sid)
		kit.eq(ext.level_path(sid), TUNNELS if sid.begins_with("L_C4_Tunnels") else ANNEX, "%s level file" % sid)
		kit.eq(ext.chapter_card(sid), ["ui.chapter_c4", s["title_key"]], "%s: chapter card after the city change" % sid)
		var st: Dictionary = ext.switches.get(sid, {})
		kit.eq(st.get("partner"), "none", "%s: nobody stands in (every scene is a level load)" % sid)
		for k in st:
			kit.ok(k in ["switch_spawn", "partner", "partner_spawn", "partner_anim", "partner_hide_after", "glide", "music", "ambience", "grade"], "%s: known switch key %s" % [sid, k])
		kit.ok(str(st.get("ambience", "")).begins_with("amb_") and str(st.get("music", "")).begins_with("mus_c4_"), "%s: own ambience and music" % sid)
		kit.ok(ext.grades.has(str(st.get("grade", ""))), "%s: grade %s defined" % [sid, st.get("grade")])
	# protagonists alternate between the cities
	for i in C4_SCENES.size() - 1:
		kit.ne(scenes[C4_SCENES[i]]["protagonist"], scenes[C4_SCENES[i + 1]]["protagonist"], "%s → %s changes the protagonist" % [C4_SCENES[i], C4_SCENES[i + 1]])
		kit.ne(ext.level_path(C4_SCENES[i]), ext.level_path(C4_SCENES[i + 1]), "%s → %s changes the city (level load)" % [C4_SCENES[i], C4_SCENES[i + 1]])
	kit.eq(ext.scenes_of_level(TUNNELS), ["L_C4_TunnelsA", "L_C4_TunnelsB"], "two scenes share the tunnels")
	kit.eq(ext.scenes_of_level(ANNEX), ["L_C4_AnnexA", "L_C4_AnnexB"], "two scenes share the annex")
	kit.eq([ext.level_key("L_C4_TunnelsB"), ext.level_key("L_C4_AnnexB")], ["L_C4_TunnelsA", "L_C4_AnnexA"], "level keys for Explore")
	for p in ["tunnels", "annex"]:
		kit.ok(ext.palettes.has(p), "palette %s" % p)
	# cinematics registered (scenes come from the cine stream this round) and in the validator list
	var seq_ids: Array = data["cinematics"]["sequences"].map(func(s: Dictionary) -> String: return s["id"])
	for cid in C4_CINEMATICS:
		kit.ok(str(ext.cinematics.get(cid, "")).begins_with("res://scenes/cinematics/ch4_"), "%s registered" % cid)
		kit.ok((ENGINE.LOCKED_CINEMATICS as Array).has(cid), "%s in the validator list" % cid)
		kit.ok(seq_ids.has(cid), "%s in cinematics.json" % cid)
	kit.eq(seq_ids.find("LS_C4_Homeward"), seq_ids.find("LS_C3_Halves") + 1, "the journey home directly follows the halves (data order)")
	kit.eq(ext.puzzles.get("c4b_solve_routes"), "res://scenes/ui/RoutePuzzle.tscn", "route overlay UI path")
	kit.eq(ext.puzzles.get("c4c_solve_numbers"), "res://scenes/ui/TracePuzzle.tscn", "number chain UI path")
	# expressions for every C4 node; the speakers of Chapter 4
	var speakers := {}
	for did in C4_DIALOGUES:
		for node in conversations[did]["nodes"]:
			kit.ok(ext.line_expr.has(node["id"]), "%s has an expression" % node["id"])
			kit.ok(str(ext.line_expr.get(node["id"], "")) in ["neutral", "concerned", "determined", "surprised"], "%s: known expression" % node["id"])
			speakers[str(node["speaker"])] = true
	kit.eq(Kit.sorted(speakers), Kit.sorted(["alexei", "konrad", "lev", "marta", "registrar"]), "Chapter-4 speakers")
	kit.eq(ext.looks_for("L_C4_TunnelsA"), {}, "clean looks in Chapter 4")
	return true


func _level_shells() -> bool:
	var placed := {}     # objective -> count
	for path in ENVS:
		var man := _manifest(ENVS[path])
		kit.eq(man.get("world_size"), [1920, 360], "%s: 1920x360" % path)
		var hs: Dictionary = (man.get("hotspots", {}) as Dictionary).duplicate()
		var xh: Dictionary = _manifest(str(ENVS[path]).get_base_dir() + "/explore_hotspots.json").get("hotspots", {})
		for k in xh:
			if not hs.has(k):
				hs[k] = xh[k]
		var poly := PackedVector2Array()
		for q in man.get("walkable", []):
			poly.append(Vector2(float(q[0]), float(q[1])))
		for name in HOTSPOTS[path]:
			if kit.ok(hs.has(name), "%s: story hotspot %s (C4_DESIGN §4)" % [path, name]):
				kit.ok(absf(float(hs[name][0]) - float(HOTSPOTS[path][name])) <= 8.0 and float(hs[name][1]) == 300.0, "%s: %s at x %d ± 8, feet y 300" % [path, name, HOTSPOTS[path][name]])
		for name in hs:
			var p := Vector2(float(hs[name][0]), float(hs[name][1]))
			kit.ok(Geometry2D.is_point_in_polygon(p, poly), "%s: hotspot %s on the walkable floor" % [path, name])
		for name in SPAWNS[path]:
			var sp = man.get("spawns", {}).get(name)
			if kit.ok(sp is Array and sp.size() == 2, "%s: spawn %s" % [path, name]):
				kit.ok(Geometry2D.is_point_in_polygon(Vector2(float(sp[0]), float(sp[1])), poly), "%s: spawn %s on the walkable floor" % [path, name])
		var blockers: Array = man.get("blockers", [])
		kit.eq(blockers.size(), 1, "%s: one permanent blocker between the two walk areas" % path)
		for nd in _nodes_of(path):
			var pr: Dictionary = nd["props"]
			if pr.has("hotspot_id"):
				kit.ok(hs.has(pr["hotspot_id"]), "%s/%s: hotspot %s exists" % [path, nd["name"], pr["hotspot_id"]])
			if pr.has("objective_id"):
				var oid: String = pr["objective_id"]
				placed[oid] = int(placed.get(oid, 0)) + 1
				if not kit.ok(objectives.has(oid), "%s/%s: objective %s exists" % [path, nd["name"], oid]):
					continue
				kit.eq(pr.get("kind"), objectives[oid]["type"], "%s: interactable kind = objective type" % oid)
				var scene := str(_quest_of(oid).get("scene", ""))
				kit.eq(ext.level_path(scene), path, "%s: placed in the level file of its scene" % oid)
				var x := float(hs.get(pr["hotspot_id"], [0, 0])[0])
				kit.ok(x >= AREAS[scene][0] and x <= AREAS[scene][1], "%s: hotspot inside the walk area of %s" % [oid, scene])
				if pr.get("kind") in ["dialogue", "choice"]:
					kit.ok(pr.get("npc_id") in ["lev", "marta", "registrar"], "%s: spoken with %s" % [oid, pr.get("npc_id")])
		for sid in C4_SCENES:
			if ext.level_path(sid) == path:
				var sp = man.get("spawns", {}).get(ext.spawn_for(sid))
				kit.ok(sp is Array and float(sp[0]) >= AREAS[sid][0] and float(sp[0]) <= AREAS[sid][1], "%s: entry spawn in its own walk area" % sid)
		# the shell loads headless: manifest, spawns, hotspot placement
		var lvl: Node = (load(path) as PackedScene).instantiate()
		lvl.set("ambience", "")
		lvl.set("music", "")
		kit.mount(lvl)
		kit.ok(lvl.get("manifest") is Dictionary and not (lvl.manifest as Dictionary).is_empty(), "%s: manifest loaded" % path)
		kit.ok(lvl.get_node_or_null("WalkLimits") != null, "%s: walk limits built" % path)
		var first: String = "SP_C4_Stairs" if path == TUNNELS else "SP_C4_Shelter"
		kit.eq(lvl.get_spawn(first), Vector2(SPAWNS[path][first][0], SPAWNS[path][first][1]), "%s: entry spawn" % path)
		for c in lvl.playfield.get_children():
			var hid = c.get("hotspot_id")
			if hid != null and str(hid) != "" and hs.has(str(hid)):
				var off: Vector2 = c.get("hotspot_offset") if c.get("hotspot_offset") != null else Vector2.ZERO
				kit.eq(c.position, Vector2(float(hs[str(hid)][0]), float(hs[str(hid)][1])) + off, "%s/%s placed on %s" % [path, c.name, hid])
		lvl.free()
	for oid in C4_OBJECTIVES:
		kit.eq(placed.get(oid, 0), 1, "%s has exactly one interactable" % oid)
	# people of the shells: two Levs (cellar / siding, gated so only one is ever present), Marta, the registrar, a guard
	var npcs := {}
	for path in ENVS:
		for nd in _nodes_of(path):
			if nd["props"].has("char_id"):
				npcs[nd["name"]] = nd["props"]
	kit.eq(Kit.sorted(npcs.keys()), Kit.sorted(["LevCellar", "LevSiding", "MartaTram", "Registrar", "GuardAnnex"]), "NPC nodes")
	kit.eq([npcs.get("LevCellar", {}).get("hide_after"), npcs.get("LevSiding", {}).get("show_after")],
		["c4c_inspect_card", "c4a_open_door"], "Lev in the cellar for scene A, at the siding for scene C")
	for n in npcs:
		kit.ok(not (str(npcs[n].get("char_id")) in ["alexei", "konrad"]), "%s is not a protagonist NPC" % n)
	return true


## The director reads the data as intended: two level files, four scenes, no stand-in anywhere (public Game API only;
## skipped with a note when Game is not in the tree).
func _engine_contract() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game") if Kit.root() else null
	if game == null or not (game.has_method("level_file") and game.has_method("scene_partner")):
		print("      note: Game without the §12.11 API — engine contract not checked")
		return true
	for sid in C4_SCENES:
		kit.eq(game.level_file(sid), TUNNELS if sid.begins_with("L_C4_Tunnels") else ANNEX, "%s level file" % sid)
		kit.eq(game.scene_partner(sid), "", "%s: nobody stands in" % sid)
	return true


func _texts() -> bool:
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var keys: Array = ["ui.chapter_c4"]
	for oid in C4_OBJECTIVES:
		keys.append(objectives[oid]["text_key"])
		for c in objectives[oid].get("choices", []):
			keys.append(c["text_key"])
	for it in data["items"]["items"]:
		if C4_ITEMS.has(it["id"]):
			keys.append_array([it["name_key"], it["description_key"]])
	for did in C4_DIALOGUES:
		for node in conversations[did]["nodes"]:
			keys.append(node["text_key"])
	for f in ["de_c4_dialogue", "de_c4_cinematics", "de_c4_ui", "de_c4_characters"]:
		var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/locale/%s.json" % f))
		kit.ok(r["ok"], f + " parses")
		if r["ok"]:
			keys.append_array((r["value"]["strings"] as Dictionary).keys())
	for sid in C4_SCENES:
		keys.append(data["scenes"]["scenes"].filter(func(s) -> bool: return s["id"] == sid)[0]["title_key"])
	kit.ok(keys.size() >= 220, "Chapter-4 texts collected (%d)" % keys.size())
	var spoken: Dictionary = {}
	for did in C4_DIALOGUES:
		for node in conversations[did]["nodes"]:
			spoken[node["text_key"]] = true
	for node_id in ext.line_variants:
		if str(node_id).begins_with("c4"):
			for v in ext.line_variants[node_id]:
				spoken[v["key"]] = true
	for k in keys:
		var t: String = loc.t(str(k))
		kit.ok(loc.has(str(k)) and t.strip_edges() != "", "%s has German text" % k)
		kit.ok(not t.contains("\""), "%s: German quotes („…“, ‚…‘), no ASCII double quote" % k)
		kit.ok(not t.contains(" - "), "%s: dashes are – (en dash), not -" % k)
		kit.ok(not t.contains("Matth" + "ias"), "%s: the pre-rename name never appears" % k)
		if spoken.has(k) or str(k).begins_with("dlg.c4.react."):
			kit.ok(t.length() <= 140, "%s: spoken line ≤ 140 characters (%d)" % [k, t.length()])
	# memories and journal texts of the new scenes / people
	for sid in C4_SCENES:
		kit.ok(loc.has("ui.memories.place." + sid) and loc.has("ui.memories.date." + sid), "%s: memory place and date" % sid)
	for opt in C4D:
		kit.ok(loc.has("ui.memories.decided." + opt), "memory line for %s" % opt)
	for oid in ["c4b_solve_routes", "c4c_solve_numbers"]:
		kit.ok(loc.has("ui.memories.echo." + oid), "memory echo for %s" % oid)
	for p in ["lev", "marta", "registrar"]:
		for k in ["char.%s.name", "char.%s.role", "sys.journal.person.%s.name", "sys.journal.person.%s.note"]:
			kit.ok(loc.has(k % p), (k % p) + " exists")
	return true


## The end card lists every decision of the playthrough in story order — also after a reload, whose choice_history
## comes back key-sorted (Game.end_card_decisions, C4_DESIGN §1).
func _end_card() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game") if Kit.root() else null
	if game == null or not game.has_method("end_card_decisions"):
		print("      note: Game.end_card_decisions missing — end card not checked")
		return true
	var g := kit.play_verified_route("keep_private", "request_explanation", false, "note_alone", "report_delegation",
		"pocket_plan", "swap_halves", "protect_marta")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "finished state reloads")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var want: Array = []
	for oid in ["a1_choose", "m1_choose", "c3a_choose", "c3b_choose", "c3d_choose", "c3g_choose", "c4d_choose"]:
		for c in objectives[oid]["choices"]:
			if c["id"] == g.choice_history()[oid]:
				want.append("• " + loc.t(c["text_key"]))
	kit.eq(game.end_card_decisions(g.choice_history()), want, "seven decisions in story order (live)")
	kit.eq(game.end_card_decisions(h.choice_history()), want, "seven decisions in story order (after a reload)")
	g.free()
	h.free()
	return true
