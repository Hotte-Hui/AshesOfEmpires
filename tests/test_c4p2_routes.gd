extends RefCounted
## Chapter 4 part 2 „Stimmen unter Beton“ (documentation/C4P2_DESIGN.md) through the public Story API and the
## presentation data: every choice combination of the whole chain (a1 × m1 × c3a × c3b × c3d × c3g × c4d × c4g = 576
## routes), the gating of the 21 part-2 objectives step by step (four city changes, the cinematic queue, locks swept after
## every step), both puzzles (the join „Die Hälften“, the house „Haus 14“ — whose answer must be the only safe way through
## the house graph of the contract), the decision (both options always offered, one meter each, the new flag
## people_protected), save/load at every part-2 step, round-9 saves continuing into part 2, the line variants per route
## (no dead variant, fallback-only bases never heard, earlier decisions felt), the presentation contract of
## data/chapters/c4p2.json, the two level shells, the engine's reading of the data, German typography, the board data of
## the new evidence, and the end card's eight decisions in story order. Art, films, puzzle UIs and the new cast are built
## by their own streams this round: reported as pending while missing, never failed.

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
const C4G := ["publish_now", "protect_first"]
const P2_SCENES := ["L_C4P2_KarskA", "L_C4P2_BerlinA", "L_C4P2_KarskB", "L_C4P2_BerlinB"]
const PROTAGONIST := {"L_C4P2_KarskA": "alexei", "L_C4P2_BerlinA": "konrad", "L_C4P2_KarskB": "alexei",
	"L_C4P2_BerlinB": "konrad"}
const KARSK := "res://scenes/levels/L_C4P2_Karsk.tscn"
const BERLIN := "res://scenes/levels/L_C4P2_Berlin.tscn"
const ENVS := {KARSK: "res://assets/environments/karsk_c4p2/scene.json",
	BERLIN: "res://assets/environments/berlin_c4p2/scene.json"}
## data order = the order in which the canonical route (Kit) completes them
const P2_OBJECTIVES := ["c4e_inspect_order", "c4e_talk_irina", "c4e_inspect_list", "c4e_talk_maria", "c4e_inspect_notice",
	"c4f_inspect_board", "c4f_talk_marta", "c4f_inspect_courier", "c4f_talk_ekdahl", "c4f_inspect_book",
	"c4g_talk_ekdahl", "c4g_inspect_book", "c4g_talk_lev", "c4g_solve_halves", "c4g_inspect_card", "c4g_choose",
	"c4h_inspect_gate", "c4h_talk_hanna", "c4h_inspect_cards", "c4h_solve_house", "c4h_talk_wendt"]
const P2_ITEMS := ["ev_c4_special_order", "ev_c4_work_list", "ev_c4_press_notice", "ev_c4_departures_east",
	"ev_c4_courier_seals", "ev_c4_konrad_tracing", "ev_c4_guidebook", "ev_c4_card_ru_original", "ev_c4_card_whole",
	"ev_c4_house_notice", "ev_c4_house_cards"]
const EVENTS := ["a1_completed", "m1_completed", "c3a_completed", "c3b_completed", "c3c_completed", "c3d_completed",
	"c3e_completed", "c3f_completed", "c3g_completed", "c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed",
	"c4e_completed", "c4f_completed", "c4g_completed", "c4h_completed", "slice_completed"]
const P2_CINEMATICS := ["LS_C4P2_Depot", "LS_C4P2_Steam", "LS_C4P2_Book", "LS_C4P2_Express", "LS_C4P2_Clock"]
const P2_DIALOGUES := ["dlg_c4e_irina", "dlg_c4e_maria", "dlg_c4f_marta", "dlg_c4f_ekdahl", "dlg_c4g_ekdahl", "dlg_c4g_lev",
	"dlg_c4h_hanna", "dlg_c4h_wendt"]
## Base lines that a variant always replaces in normal play (a1 / c4d cover every option).
const FALLBACK_ONLY := ["c4e_iri_01", "c4f_mar_01", "c4f_mar_03", "c4f_mar_04", "c4f_mar_05", "c4h_han_01", "c4h_wen_01"]
## Base lines with variants that some route still hears.
const BASE_HEARD := ["c4f_mar_09", "c4f_mar_11", "c4f_ekd_06", "c4f_ekd_10", "c4f_ekd_11", "c4g_ekd_02", "c4g_ekd_06",
	"c4g_ekd_07", "c4g_lev_04", "c4h_han_06", "c4h_wen_03", "c4h_wen_04", "c4h_wen_08"]
## C4P2_DESIGN §4: story hotspots and NPC anchors (x at feet y 300), spawns, walk areas.
const HOTSPOTS := {
	KARSK: {"dispatch_window": 132, "irina_window": 196, "coal_list": 400, "maria_coal": 560, "guard_coal": 690,
		"press_notice": 780, "signal_post": 980, "minder_canteen": 1110, "canteen_table": 1170, "lev_sandhouse": 1350,
		"sand_table": 1460, "sand_lamp": 1520, "express_door": 1780},
	BERLIN: {"departure_board": 110, "marta_buffet": 300, "shadow_kiosk": 410, "courier_car": 500, "ekdahl_window": 680,
		"dining_table": 800, "gate_notice": 1000, "kuhnert_gate": 1060, "wendt_yard": 1110, "hanna_yard": 1250,
		"lodge_window": 1420, "yard_pump": 1600}}
const SPAWNS := {KARSK: {"SP_C4P2_Yard": [48, 300], "SP_C4P2_Signal": [930, 300]},
	BERLIN: {"SP_C4P2_Platform": [60, 300], "SP_C4P2_Gate": [960, 300]}}
const AREAS := {"L_C4P2_KarskA": [18, 858], "L_C4P2_KarskB": [898, 1902], "L_C4P2_BerlinA": [18, 898],
	"L_C4P2_BerlinB": [938, 1902]}
## C4P2_DESIGN §2.7 „Haus 14“: three wings (V Vorderhaus, S Seitenflügel, H Hinterhaus) × cellar, ground floor, 1–3,
## attic; stairs up/down inside a wing, crossings only along the attic (vd–sd–hd) and the cellar corridor (vk–sk–hk), the
## cobbler's workshop ws hangs on the back cellar. Unsafe: Frau Pohl's landing (s2), the lodge (se), the gate passage (ve).
const HOUSE_ROOMS := ["vk", "ve", "v1", "v2", "v3", "vd", "sk", "se", "s1", "s2", "s3", "sd", "hk", "he", "h1", "h2", "h3",
	"hd", "ws"]
const HOUSE_UNSAFE := ["s2", "se", "ve"]
const HOUSE_START := "s3"
const HOUSE_GOAL := "ws"

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
	kit.run_case("all_576_choice_combinations", _all_combinations)
	kit.run_case("part2_gating_scenes_and_queue_step_by_step", _step_by_step)
	kit.run_case("part2_locked_before_its_scenes", _locks)
	kit.run_case("join_puzzle_rules", _halves_puzzle)
	kit.run_case("house_puzzle_rules_and_the_only_safe_way", _house_puzzle)
	kit.run_case("decision_options_and_meters", _decision)
	kit.run_case("save_load_at_every_part2_step", _save_load)
	kit.run_case("round9_saves_continue_into_part2", _old_saves)
	kit.run_case("variants_per_route", _variants)
	kit.run_case("presentation_data_contract", _presentation)
	kit.run_case("level_shells", _level_shells)
	kit.run_case("engine_reads_the_part2_data", _engine_contract)
	kit.run_case("texts_german_typography", _texts)
	kit.run_case("board_data_for_the_new_evidence", _board)
	kit.run_case("end_card_lists_eight_decisions_in_story_order", _end_card)
	kit.run_case("streams_pending_report", _pending)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Meters of a finished route (every option raises one meter; C4P2_DESIGN §2.4: publish_now → evidence_chain,
## protect_first → people_protected, the round-10 flag).
static func meters(a1: String, m1: String, c3a: String, c3b: String, c3d: String, c3g: String, c4d: String,
		c4g: String) -> Dictionary:
	return {"irina_trust": int(a1 == "share_with_irina"), "alexei_secrecy": int(a1 == "keep_private"),
		"konrad_evidence": int(m1 == "preserve_evidence"), "office_suspicion": int(m1 == "request_explanation"),
		"elena_trust": int(c3a == "ask_elena") + int(c3b == "search_elena") + int(c3g == "hide_for_elena"),
		"evidence_chain": int(c3a == "note_alone") + int(c3d == "pocket_plan") + int(c3g == "split_by_language") +
			int(c4d == "name_marta") + int(c4g == "publish_now"),
		"alexei_konrad_trust": int(c3b == "share_protocol") + int(c3d == "admit_plan") + int(c3g == "swap_halves"),
		"kessler_alerted": int(c3b == "report_delegation"), "civilian_welfare": int(c4d == "protect_marta"),
		"people_protected": int(c4g == "protect_first")}


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
			return g.solve_puzzle(oid, Kit.C4_HALVES.duplicate() if oid == "c4g_solve_halves" else Kit.C4_HOUSE.duplicate())
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


func _quest_of(oid: String) -> Dictionary:
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			if o["id"] == oid:
				return q
	return {}


func _puzzle(id: String) -> Dictionary:
	for x in data["puzzles"]["puzzles"]:
		if x["id"] == id:
			return x
	return {}


## The house graph of C4P2_DESIGN §2.7 (undirected adjacency).
static func house_edges() -> Dictionary:
	var adj := {}
	for r in HOUSE_ROOMS:
		adj[r] = []
	var link := func(a: String, b: String) -> void:
		adj[a].append(b)
		adj[b].append(a)
	for w in ["v", "s", "h"]:
		var col := [w + "k", w + "e", w + "1", w + "2", w + "3", w + "d"]
		for i in col.size() - 1:
			link.call(col[i], col[i + 1])
	link.call("vd", "sd")
	link.call("sd", "hd")
	link.call("vk", "sk")
	link.call("sk", "hk")
	link.call("hk", "ws")
	return adj


## Every simple path from the start to the goal that avoids the unsafe rooms.
static func safe_paths(adj: Dictionary) -> Array:
	var out: Array = []
	var stack: Array = [[HOUSE_START]]
	while not stack.is_empty():
		var path: Array = stack.pop_back()
		var last: String = path[-1]
		if last == HOUSE_GOAL:
			out.append(path)
			continue
		for n in adj[last]:
			if path.has(n) or HOUSE_UNSAFE.has(n):
				continue
			stack.append(path + [n])
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
							for c4d in C4D:
								for c4g in C4G:
									var label := "%s/%s/%s/%s/%s/%s/%s/%s" % [a1, m1, c3a, c3b, c3d, c3g, c4d, c4g]
									var g := kit.play_verified_route(a1, m1, false, c3a, c3b, c3d, c3g, c4d, c4g)
									var f: Dictionary = g.flags()
									var want := meters(a1, m1, c3a, c3b, c3d, c3g, c4d, c4g)
									for k in want:
										kit.eq(f[k], want[k], label + " " + k)
									kit.ok(int(f["evidence_chain"]) <= 5 and int(f["people_protected"]) <= 1, label + " meters in range")
									kit.eq(g.completed_events(), EVENTS, label + " events")
									kit.eq([g.current_scene, g.active_character], ["L_X1_Montage", "none"], label + " montage")
									kit.eq(g.inventory().slice(37), P2_ITEMS, label + " part-2 evidence in order")
									kit.eq(g.completed_objectives().slice(65), P2_OBJECTIVES, label + " part-2 objectives in data order")
									kit.eq(g.choice_history().get("c4g_choose"), c4g, label + " c4g recorded")
									kit.eq(g.choice_history().size(), 8, label + " eight decisions")
									kit.eq([g.is_finished(), g.is_finale_viewed(), g.pending_cinematics()], [true, true, []], label + " finished")
									finals[g.save_json()] = label
									n += 1
									g.free()
	kit.eq(n, 576, "every combination played")
	kit.eq(finals.size(), 576, "576 distinct end states")
	return true


func _step_by_step() -> bool:
	var g := kit.story()
	kit.play_until(g, "c4d", {"c4d": "protect_marta"})
	kit.eq([g.current_scene, g.active_character, g.chapter_key()], ["L_C4P2_KarskA", "alexei", "ui.chapter_c4"],
		"part 2 opens with Alexei at the Karsk depot")
	kit.eq(g.current_quest().get("id"), "q_c4e_depot", "depot quest")
	kit.eq(g.pending_cinematics().slice(-2), ["LS_C4_Voices", "LS_C4P2_Depot"], "c4d_completed queues the voices, then the depot")
	kit.is_err(g.finale(), "finale locked in part 2")
	for cid in g.pending_cinematics():
		kit.step(g.consume_cinematic(cid, true), "consume " + cid)
	# [action, objective, available() afterwards, scene afterwards, cinematics queued by this step]
	var steps := [
		["inspect", "c4e_inspect_list", ["c4e_inspect_order"], "L_C4P2_KarskA", []],
		["inspect", "c4e_inspect_order", ["c4e_talk_irina"], "L_C4P2_KarskA", []],
		["talk", "c4e_talk_irina", ["c4e_talk_maria"], "L_C4P2_KarskA", []],
		["talk", "c4e_talk_maria", ["c4e_inspect_notice"], "L_C4P2_KarskA", []],
		["inspect", "c4e_inspect_notice", ["c4f_inspect_board", "c4f_inspect_courier"], "L_C4P2_BerlinA", ["LS_C4P2_Steam"]],
		["inspect", "c4f_inspect_courier", ["c4f_inspect_board"], "L_C4P2_BerlinA", []],
		["inspect", "c4f_inspect_board", ["c4f_talk_marta"], "L_C4P2_BerlinA", []],
		["talk", "c4f_talk_marta", ["c4f_talk_ekdahl"], "L_C4P2_BerlinA", []],
		["talk", "c4f_talk_ekdahl", ["c4f_inspect_book"], "L_C4P2_BerlinA", []],
		["inspect", "c4f_inspect_book", ["c4g_talk_ekdahl"], "L_C4P2_KarskB", ["LS_C4P2_Book"]],
		["talk", "c4g_talk_ekdahl", ["c4g_inspect_book"], "L_C4P2_KarskB", []],
		["inspect", "c4g_inspect_book", ["c4g_talk_lev"], "L_C4P2_KarskB", []],
		["talk", "c4g_talk_lev", ["c4g_solve_halves"], "L_C4P2_KarskB", []],
		["solve", "c4g_solve_halves", ["c4g_inspect_card"], "L_C4P2_KarskB", []],
		["inspect", "c4g_inspect_card", ["c4g_choose"], "L_C4P2_KarskB", []],
		["choose", "c4g_choose", ["c4h_inspect_gate"], "L_C4P2_BerlinB", ["LS_C4P2_Express"]],
		["inspect", "c4h_inspect_gate", ["c4h_talk_hanna"], "L_C4P2_BerlinB", []],
		["talk", "c4h_talk_hanna", ["c4h_inspect_cards"], "L_C4P2_BerlinB", []],
		["inspect", "c4h_inspect_cards", ["c4h_solve_house"], "L_C4P2_BerlinB", []],
		["solve", "c4h_solve_house", ["c4h_talk_wendt"], "L_C4P2_BerlinB", []],
		["talk", "c4h_talk_wendt", [], "L_X1_Montage", ["LS_C4P2_Clock"]],
	]
	kit.eq(g.available(), ["c4e_inspect_order", "c4e_inspect_list"], "depot gates: the order and the list")
	_sweep_locked(g, "depot entry")
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
				var sol = Kit.C4_HALVES.duplicate() if oid == "c4g_solve_halves" else Kit.C4_HOUSE.duplicate()
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
	kit.ok(g.has_item("ev_c4_card_ru_original"), "Lev's dialogue grants the Russian half at its last line")
	kit.eq([g.current_quest(), g.available()], [{}, []], "montage: no quest, nothing available")
	kit.eq(g.choice_history().get("c4g_choose"), "protect_first", "second option recorded")
	kit.eq(g.flags()["people_protected"], 1, "protect_first: people_protected +1 (the round-10 flag)")
	kit.is_ok(g.finale(true), "finale open after c4h")
	kit.eq(g.completed_events(), EVENTS, "events once each, in order")
	return true


func _locks() -> bool:
	var g := kit.story()
	_sweep_locked(g, "new game")
	for stage in ["m1", "c3g", "c4c"]:
		g.free()
		g = kit.story()
		kit.play_until(g, stage)
		_sweep_locked(g, "after " + stage)
	kit.play_c4d(g)
	kit.eq(g.available(), ["c4e_inspect_order", "c4e_inspect_list"], "only the depot gates after the annex")
	for oid in ["c4f_inspect_board", "c4g_talk_ekdahl", "c4h_inspect_gate", "c4g_choose", "c4h_solve_house"]:
		kit.eq(attempt(g, oid, objectives).get("error_key"), "sys.err.locked", "%s locked while Alexei is at the depot" % oid)
	g.free()
	return true


func _halves_puzzle() -> bool:
	var p := _puzzle("pz_c4_halves")
	kit.eq([p.get("type"), p.get("scene"), p.get("hint_after_attempts"), p.get("retry_unlimited")],
		["overlay_alignment", "L_C4P2_KarskB", 2, true], "overlay type (Konrad's mechanic in Alexei's hands), hint after 2, unlimited")
	kit.eq(p.get("solution"), Kit.C4_HALVES, "solution = Kit.C4_HALVES (C4P2_DESIGN §2.7)")
	kit.ne(p.get("solution"), {"rotation_steps": 0, "offset_x": 0, "offset_y": 0}, "the UI start pose is wrong")
	kit.ne(p.get("solution"), {"rotation_steps": 1, "offset_x": 0, "offset_y": 0}, "the autoplay's wrong pose is wrong")
	var g := kit.story()
	kit.play_until(g, "c4f")
	kit.play_dialogue(g, "c4g_talk_ekdahl")
	kit.step(g.inspect("c4g_inspect_book"), "book")
	kit.eq(g.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate()).get("error_key"), "sys.err.locked",
		"locked until Lev brought the Russian half")
	kit.play_dialogue(g, "c4g_talk_lev")
	kit.eq(g.puzzle_for("c4g_solve_halves").get("clue_item_ids"), ["ev_c4_guidebook", "ev_c4_card_ru_original"], "clue items")
	var w1: Dictionary = g.solve_puzzle("c4g_solve_halves", {"rotation_steps": 0, "offset_x": 0, "offset_y": 0})
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts")], [true, false, 1], "start pose: attempt 1")
	kit.eq(g.puzzle_hint_available("c4g_solve_halves"), false, "no hint after one failure")
	for bad in [{"rotation_steps": 2, "offset_x": 4}, {"rotation_steps": 2, "offset_x": 4, "offset_y": 1.0},
			[2, 4, 1], null, {"rotation_steps": 2, "offset_x": 4, "offset_y": 1, "z": 0}]:
		kit.eq(g.solve_puzzle("c4g_solve_halves", bad).get("error_key"), "sys.err.answer_format", "malformed %s rejected" % Kit.fmt(bad))
	kit.eq(g.puzzle_attempts("c4g_solve_halves"), 1, "malformed answers are not attempts")
	var w2: Dictionary = g.solve_puzzle("c4g_solve_halves", {"rotation_steps": 0, "offset_x": 4, "offset_y": 1})
	kit.eq([w2.get("solved"), w2.get("attempts")], [false, 2], "not turned (the writing upside down): attempt 2")
	kit.eq(g.puzzle_hint_available("c4g_solve_halves"), true, "hint after two failures")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "save with failed attempts loads")
	var ok: Dictionary = h.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate())
	kit.eq([ok.get("solved"), ok.get("attempts"), h.available()], [true, 2, ["c4g_inspect_card"]], "joined; the whole card next")
	kit.eq(h.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate()).get("error_key"), "sys.err.locked", "joined once only")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for k in ["title", "subtitle", "instruction", "legend.teeth", "legend.stamp", "wrong", "wrong_turned", "hint", "success",
			"btn.check", "btn.rotate", "btn.reset", "btn.close"]:
		kit.ok(loc.has("ui.c4p2.halves." + k), "UI text ui.c4p2.halves.%s" % k)
	g.free()
	h.free()
	return true


func _house_puzzle() -> bool:
	var p := _puzzle("pz_c4_house")
	kit.eq([p.get("type"), p.get("scene"), p.get("hint_after_attempts"), p.get("retry_unlimited")],
		["symbol_order", "L_C4P2_BerlinB", 2, true], "symbol order (the new HousePuzzle UI), the courtyard, hint after 2, unlimited")
	kit.eq(p.get("solution"), Kit.C4_HOUSE, "solution = Kit.C4_HOUSE (C4P2_DESIGN §2.7)")
	kit.eq(Kit.sorted(p.get("display_symbols", [])), Kit.sorted(p.get("solution", [])), "display_symbols = the solution's rooms")
	# the answer is the ONLY safe way through the contract's house graph
	var adj := house_edges()
	var ways := safe_paths(adj)
	kit.eq(ways, [Kit.C4_HOUSE], "exactly one safe way from Hanna's flat to the workshop, and it is the answer")
	kit.ok(HOUSE_ROOMS.size() == 19 and adj.size() == 19, "19 rooms in the house")
	for i in Kit.C4_HOUSE.size() - 1:
		kit.ok((adj[Kit.C4_HOUSE[i]] as Array).has(Kit.C4_HOUSE[i + 1]), "%s → %s is a passage" % [Kit.C4_HOUSE[i], Kit.C4_HOUSE[i + 1]])
	# the decoy: down the side wing past Frau Pohl, and the front wing down to Kuhnert in the gate passage
	kit.ok((adj["s3"] as Array).has("s2") and (adj["vd"] as Array).has("v3"), "the decoys are real passages")
	# the layout file of the puzzle stream (when it exists) must be the contract's graph
	var lay := _manifest("res://assets/ui/puzzle/c4p2_house.json")
	if lay.is_empty():
		print("      pending (round 10): assets/ui/puzzle/c4p2_house.json (HousePuzzle layout)")
	else:
		var rooms: Array = (lay.get("rooms", {}) as Dictionary).keys() if lay.get("rooms") is Dictionary else []
		kit.eq(Kit.sorted(rooms), Kit.sorted(HOUSE_ROOMS), "layout rooms = the contract's rooms")
		kit.eq(Kit.sorted(lay.get("unsafe", [])), Kit.sorted(HOUSE_UNSAFE), "layout unsafe rooms = the contract's")
		kit.eq([lay.get("start"), lay.get("goal")], [HOUSE_START, HOUSE_GOAL], "layout start and goal")
	var g := kit.story()
	kit.play_until(g, "c4g")
	kit.step(g.inspect("c4h_inspect_gate"), "gate notice")
	kit.eq(g.solve_puzzle("c4h_solve_house", Kit.C4_HOUSE.duplicate()).get("error_key"), "sys.err.locked", "locked before Hanna and the cards")
	kit.play_dialogue(g, "c4h_talk_hanna")
	kit.step(g.inspect("c4h_inspect_cards"), "cards")
	kit.eq(g.puzzle_for("c4h_solve_house").get("clue_item_ids"), ["ev_c4_house_notice", "ev_c4_house_cards"], "clue items")
	var w1: Dictionary = g.solve_puzzle("c4h_solve_house", ["s3", "s2"])
	kit.eq([w1.get("ok"), w1.get("solved"), w1.get("attempts")], [true, false, 1], "past Frau Pohl: attempt 1")
	for bad in [["s3", 3, "hd"], "s3,sd,hd", {"0": "s3"}, null]:
		kit.eq(g.solve_puzzle("c4h_solve_house", bad).get("error_key"), "sys.err.answer_format", "malformed %s rejected" % Kit.fmt(bad))
	var w2: Dictionary = g.solve_puzzle("c4h_solve_house", ["s3", "sd", "vd", "v3", "v2", "v1", "ve"])
	kit.eq([w2.get("solved"), w2.get("attempts")], [false, 2], "down the front stairs into the gate passage: attempt 2")
	kit.eq(g.puzzle_hint_available("c4h_solve_house"), true, "hint after two failures")
	var ok: Dictionary = g.solve_puzzle("c4h_solve_house", Kit.C4_HOUSE.duplicate())
	kit.eq([ok.get("solved"), ok.get("attempts"), g.available()], [true, 2, ["c4h_talk_wendt"]], "safe way; Wendt next")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for k in ["title", "subtitle", "instruction", "hint", "success", "no_way", "stop.s2", "stop.se", "stop.ve", "stop.flat",
			"stop.short", "btn.check", "btn.undo", "btn.reset", "btn.cards", "btn.lights", "btn.close"]:
		kit.ok(loc.has("ui.c4p2.house." + k), "UI text ui.c4p2.house.%s" % k)
	for r in HOUSE_ROOMS:
		kit.ok(loc.has("ui.c4p2.house.room." + r) and loc.has("ui.c4p2.house.note." + r), "room %s: name and card note" % r)
	for w in ["v", "s", "h"]:
		kit.ok(loc.has("ui.c4p2.house.wing." + w), "wing %s named" % w)
	g.free()
	return true


func _decision() -> bool:
	var g := kit.story()
	kit.play_until(g, "c4f")
	kit.play_dialogue(g, "c4g_talk_ekdahl")
	kit.step(g.inspect("c4g_inspect_book"), "book")
	kit.play_dialogue(g, "c4g_talk_lev")
	kit.step(g.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate()), "halves")
	kit.step(g.inspect("c4g_inspect_card"), "card")
	kit.eq(g.choices_for("c4g_choose").map(func(c) -> String: return c["id"]), C4G, "two options, always both offered")
	var before: String = g.save_json()
	for bad in ["", "Publish_Now", "name_marta", "protect", 7, null]:
		var r: Dictionary = g.choose("c4g_choose", bad)
		kit.eq([r.get("ok"), r.get("error_key")], [false, "sys.err.invalid_choice"], "invalid option %s rejected" % Kit.fmt(bad))
		kit.eq(g.save_json(), before, "invalid option %s changes nothing" % Kit.fmt(bad))
	var h := kit.story()
	kit.is_ok(h.load_json(before), "the same moment, a second playthrough")
	var r1: Dictionary = g.choose("c4g_choose", "publish_now")
	kit.eq(r1.get("changes"), {"flags": {"evidence_chain": 3}, "objectives": ["c4g_choose"], "items": [],
		"events": ["c4g_completed"], "cinematics": ["LS_C4P2_Express"], "scene": "L_C4P2_BerlinB"}, "publish_now changes")
	kit.eq(g.flags()["people_protected"], 0, "publish_now leaves people_protected")
	var r2: Dictionary = h.choose("c4g_choose", "protect_first")
	kit.eq(r2.get("changes"), {"flags": {"people_protected": 1}, "objectives": ["c4g_choose"], "items": [],
		"events": ["c4g_completed"], "cinematics": ["LS_C4P2_Express"], "scene": "L_C4P2_BerlinB"}, "protect_first changes")
	kit.eq(h.flags()["evidence_chain"], 2, "protect_first leaves evidence_chain")
	kit.eq(g.choose("c4g_choose", "protect_first").get("error_key"), "sys.err.locked", "decided once only")
	g.free()
	h.free()
	# the flag table: round 10 adds people_protected (C4P2_DESIGN §1.1, after the save migration)
	var fl: Dictionary = data["flags"]["flags"]
	kit.eq(fl.size(), 17, "17 flags")
	kit.eq(fl.get("people_protected"), {"type": "integer", "default": 0, "min": 0, "max": 6}, "people_protected shape")
	kit.eq(fl.keys()[-1], "people_protected", "appended after the earlier flags (data order)")
	for e in ["c4e_completed", "c4f_completed", "c4g_completed", "c4h_completed"]:
		kit.ok((data["flags"]["events"] as Array).has(e), "event %s" % e)
	kit.eq(data["flags"]["events"][-1], "slice_completed", "slice_completed stays the last event")
	kit.eq(data["quests"]["slice_end_requires"], EVENTS.slice(0, EVENTS.size() - 1), "the finale needs all seventeen quest events")
	# the new flag is written only by the part-2 decision (so older saves lack it with the value their replay computes)
	var writers: Array = []
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			if (o.get("effects", {}) as Dictionary).has("people_protected"):
				writers.append(o["id"])
			for c in o.get("choices", []):
				if (c.get("effects", {}) as Dictionary).has("people_protected"):
					writers.append("%s=%s" % [o["id"], c["id"]])
	kit.eq(writers, ["c4g_choose=protect_first"], "people_protected is written by protect_first only")
	return true


func _save_load() -> bool:
	var g := kit.story()
	kit.play_until(g, "c4d", {"a1": "keep_private", "m1": "request_explanation", "c3b": "report_delegation",
		"c3g": "hide_for_elena", "c4d": "protect_marta"})
	var checkpoints := [0]
	var roundtrip := func(what: String) -> void:
		var h := kit.story()
		kit.is_ok(h.load_json(g.save_json()), "reload: " + what)
		kit.eq(h.save_json(), g.save_json(), "byte-identical: " + what)
		kit.eq([h.current_scene, h.active_character, h.available(), h.pending_cinematics()],
			[g.current_scene, g.active_character, g.available(), g.pending_cinematics()], "scene, protagonist, gates, queue: " + what)
		checkpoints[0] += 1
		h.free()
	roundtrip.call("depot entry with the voices and the depot film queued")
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
				if oid == "c4g_solve_halves":
					g.solve_puzzle(oid, {"rotation_steps": 2, "offset_x": 0, "offset_y": 1})
					roundtrip.call("after a failed join")
					kit.step(g.solve_puzzle(oid, Kit.C4_HALVES.duplicate()), oid)
				else:
					g.solve_puzzle(oid, ["s3", "s2", "s1", "se"])
					roundtrip.call("after a failed way through the house")
					kit.step(g.solve_puzzle(oid, Kit.C4_HOUSE.duplicate()), oid)
			"choice":
				kit.step(g.choose(oid, o["choices"][-1]["id"]), oid)
		roundtrip.call("after " + oid)
	kit.is_ok(g.finale(false), "finale")
	roundtrip.call("finished")
	kit.ok(checkpoints[0] >= 110, "checkpoints exercised (%d)" % checkpoints[0])
	g.free()
	return true


## A round-9 autosave in the annex (before c4d_choose — autosaves never store the montage) plays on through part 2 with
## the state of an uninterrupted route; its flag table (16 flags) gets people_protected through the save system.
func _old_saves() -> bool:
	var straight := kit.play_verified_route("keep_private", "preserve_evidence", false, "note_alone", "share_protocol",
		"pocket_plan", "hide_for_elena", "protect_marta", "protect_first")
	var b := kit.story()
	kit.play_until(b, "c4c", {"a1": "keep_private", "c3a": "note_alone", "c3d": "pocket_plan", "c3g": "hide_for_elena"})
	kit.step(b.inspect("c4d_inspect_drawer"), "drawer")
	kit.step(b.inspect("c4d_inspect_plan"), "plan")
	kit.step(b.inspect("c4d_inspect_tube"), "tube")
	kit.play_dialogue(b, "c4d_talk_registrar")
	var st: Dictionary = Kit.parse(b.save_json())
	(st["flags"] as Dictionary).erase("people_protected")     # as the round-9 build wrote it
	var saves_script = load("res://scripts/core/save_system.gd")
	var c := kit.story()
	kit.ok(not c.validate_save_json(Kit.dumps(st)).get("ok", true), "precondition: without the fill the round-9 payload fails")
	kit.is_ok(c.load_json(Kit.dumps(saves_script.rebase_story(st))), "the round-9 autosave loads through the save system's fill")
	kit.eq(c.available(), ["c4d_choose"], "the c4d decision is pending")
	kit.step(c.choose("c4d_choose", "protect_marta"), "c4d")
	kit.eq([c.current_scene, c.active_character], ["L_C4P2_KarskA", "alexei"], "the decision now leads to the Karsk depot")
	for stage in ["c4e", "c4f", "c4g", "c4h"]:
		kit.play_stage(c, stage, {"c4g": "protect_first"})
	for seq in c.pending_cinematics():
		kit.step(c.consume_cinematic(seq), "cinematic " + seq)
	kit.is_ok(c.finale(), "finale")
	kit.eq(c.save_json(), straight.save_json(), "same end state as an uninterrupted route")
	# a save claiming the round-9 end (montage right after c4d) with every flag present is re-based by the save system,
	# never accepted as it is by the engine alone
	var d := kit.story()
	kit.play_until(d, "c4d")
	var old: Dictionary = Kit.parse(d.save_json())
	old["current_scene"] = "L_X1_Montage"
	old["active_character"] = "none"
	var r: Dictionary = kit.story().validate_save_json(Kit.dumps(old))
	kit.eq([r.get("ok"), r.get("error")], [false, "Inconsistent save field: current_scene"], "the engine alone rejects the round-9 montage form")
	var reb: Dictionary = saves_script.rebase_story(old)
	kit.eq([reb["current_scene"], reb["active_character"]], ["L_C4P2_KarskA", "alexei"], "the save system re-bases it to the depot")
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
						for c4d in C4D:
							var g := kit.story()
							kit.play_until(g, "c4d", {"a1": a1, "m1": m1, "c3b": c3b, "c3d": c3d, "c3g": c3g, "c4d": c4d})
							_hear(g, ["dlg_c4e_irina", "dlg_c4e_maria"], heard, base_heard)
							kit.play_c4e(g)
							_hear(g, ["dlg_c4f_marta", "dlg_c4f_ekdahl"], heard, base_heard)
							kit.play_c4f(g)
							_hear(g, ["dlg_c4g_ekdahl", "dlg_c4g_lev"], heard, base_heard)
							kit.play_dialogue(g, "c4g_talk_ekdahl")
							kit.step(g.inspect("c4g_inspect_book"), "book")
							kit.play_dialogue(g, "c4g_talk_lev")
							kit.step(g.solve_puzzle("c4g_solve_halves", Kit.C4_HALVES.duplicate()), "halves")
							kit.step(g.inspect("c4g_inspect_card"), "card")
							for opt in C4G:
								var v: Dictionary = ext.pick(ext.choice_text.get("c4g_choose", {}).get(opt, []), cond_flags(g))
								choice_variants[str(v.get("key", "base:" + opt))] = true
								reaction_keys[str(ext.reaction("c4g_choose", opt, cond_flags(g))[1])] = true
							kit.step(g.choose("c4g_choose", "publish_now"), "c4g")
							_hear(g, ["dlg_c4h_hanna", "dlg_c4h_wendt"], heard, base_heard)
							g.free()
	for node_id in ext.line_variants:
		if not (str(node_id).substr(0, 3) in ["c4e", "c4f", "c4g", "c4h"]):
			continue
		for v in ext.line_variants[node_id]:
			kit.ok(heard.has(str(v["key"])), "variant %s of %s is heard on some route" % [v["key"], node_id])
	for node_id in FALLBACK_ONLY:
		kit.ok(not base_heard.has(node_id), "%s: the base line is fallback-only (never heard in normal play)" % node_id)
		kit.ok(ext.line_variants.has(node_id), "%s has the variants that replace it" % node_id)
	for node_id in BASE_HEARD:
		kit.ok(base_heard.has(node_id), "%s: its base line is heard on some route" % node_id)
	for k in ["choice.c4g.publish_now.marta", "choice.c4g.protect_first.marta", "base:publish_now", "base:protect_first"]:
		kit.ok(choice_variants.has(k), "option text %s is offered on some route" % k)
	for k in ["dlg.c4p2.react.publish_now", "dlg.c4p2.react.publish_now.elena", "dlg.c4p2.react.protect_first"]:
		kit.ok(reaction_keys.has(k), "reaction %s is spoken on some route" % k)
	# every option variant keeps the words the reaction answers (C3P2 rule): Tür Ost / the film
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for k in ["choice.c4g.publish_now", "choice.c4g.publish_now.marta"]:
		kit.ok(loc.t(k).begins_with("Ekdahl alles mitgeben") and loc.t(k).contains("23.40 Uhr an Tür Ost"), "%s keeps „alles … Tür Ost“" % k)
	for k in ["choice.c4g.protect_first", "choice.c4g.protect_first.marta"]:
		kit.ok(loc.t(k).begins_with("Den Film behalten") and loc.t(k).contains("nur die Nummern"), "%s keeps „Film behalten … Nummern“" % k)
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
	kit.eq(chain.slice(chain.find("L_C4_AnnexB")), ["L_C4_AnnexB"] + P2_SCENES + ["L_X1_Montage"],
		"part 2 sits between the annex and the montage")
	for sid in P2_SCENES:
		var s: Dictionary = scenes[sid]
		kit.eq(s["protagonist"], PROTAGONIST[sid], "%s protagonist" % sid)
		kit.eq(s["camera_mode"], "side_on_2d", "%s side view" % sid)
		kit.eq(ext.spawn_for(sid), s["entry_spawn"], "%s entry spawn mirrored in c4p2.json" % sid)
		kit.eq(ext.level_path(sid), KARSK if sid.begins_with("L_C4P2_Karsk") else BERLIN, "%s level file" % sid)
		kit.eq(ext.chapter_card(sid), ["ui.chapter_c4", s["title_key"]], "%s: chapter card after the city change" % sid)
		var st: Dictionary = ext.switches.get(sid, {})
		kit.eq(st.get("partner"), "none", "%s: nobody stands in (every scene is a level load)" % sid)
		for k in st:
			kit.ok(k in ["switch_spawn", "partner", "partner_spawn", "partner_anim", "partner_hide_after", "glide", "music", "ambience", "grade"], "%s: known switch key %s" % [sid, k])
		kit.ok(str(st.get("ambience", "")).begins_with("amb_") and str(st.get("music", "")).begins_with("mus_c4p2_"), "%s: own ambience and music" % sid)
		kit.ok(ext.grades.has(str(st.get("grade", ""))), "%s: grade %s defined" % [sid, st.get("grade")])
		kit.ok(ext.palettes.has(str(ext.grades.get(str(st.get("grade", "")), {}).get("palette", ""))), "%s: the grade's palette exists" % sid)
	for i in P2_SCENES.size() - 1:
		kit.ne(scenes[P2_SCENES[i]]["protagonist"], scenes[P2_SCENES[i + 1]]["protagonist"], "%s → %s changes the protagonist" % [P2_SCENES[i], P2_SCENES[i + 1]])
		kit.ne(ext.level_path(P2_SCENES[i]), ext.level_path(P2_SCENES[i + 1]), "%s → %s changes the city (level load)" % [P2_SCENES[i], P2_SCENES[i + 1]])
	kit.ne(scenes["L_C4_AnnexB"]["protagonist"], scenes["L_C4P2_KarskA"]["protagonist"], "part 1 → part 2 keeps the alternation")
	kit.eq(ext.scenes_of_level(KARSK), ["L_C4P2_KarskA", "L_C4P2_KarskB"], "two scenes share the Karsk file")
	kit.eq(ext.scenes_of_level(BERLIN), ["L_C4P2_BerlinA", "L_C4P2_BerlinB"], "two scenes share the Berlin file")
	kit.eq([ext.level_key("L_C4P2_KarskB"), ext.level_key("L_C4P2_BerlinB")], ["L_C4P2_KarskA", "L_C4P2_BerlinA"], "level keys for Explore")
	var seq_ids: Array = data["cinematics"]["sequences"].map(func(s: Dictionary) -> String: return s["id"])
	for cid in P2_CINEMATICS:
		kit.ok(str(ext.cinematics.get(cid, "")).begins_with("res://scenes/cinematics/ch4p2_"), "%s registered" % cid)
		kit.ok((ENGINE.LOCKED_CINEMATICS as Array).has(cid), "%s in the validator list" % cid)
		kit.ok(seq_ids.has(cid), "%s in cinematics.json" % cid)
	kit.eq(seq_ids.find("LS_C4P2_Depot") > seq_ids.find("LS_C4_Voices"), true, "the depot film follows the voices (data order)")
	kit.eq(ext.puzzles.get("c4g_solve_halves"), "res://scenes/ui/JoinPuzzle.tscn", "join UI path")
	kit.eq(ext.puzzles.get("c4h_solve_house"), "res://scenes/ui/HousePuzzle.tscn", "house UI path")
	var speakers := {}
	for did in P2_DIALOGUES:
		for node in conversations[did]["nodes"]:
			kit.ok(ext.line_expr.has(node["id"]), "%s has an expression" % node["id"])
			kit.ok(str(ext.line_expr.get(node["id"], "")) in ["neutral", "concerned", "determined", "surprised"], "%s: known expression" % node["id"])
			speakers[str(node["speaker"])] = true
	kit.eq(Kit.sorted(speakers), Kit.sorted(["alexei", "konrad", "irina", "maria", "marta", "journalist", "lev", "hanna", "wendt",
		"blockwart"]), "part-2 speakers")
	kit.eq(ext.looks_for("L_C4P2_KarskA"), {}, "clean looks in part 2")
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
			if kit.ok(hs.has(name), "%s: story hotspot %s (C4P2_DESIGN §4)" % [path, name]):
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
		var zones: Dictionary = man.get("camera_zones", {})
		for sid in P2_SCENES:
			if ext.level_path(sid) == path:
				kit.ok(zones.has(sid), "%s: camera zone of %s" % [path, sid])
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
					kit.ok(pr.get("npc_id") in ["irina", "maria", "marta", "journalist", "lev", "hanna", "wendt"], "%s: spoken with %s" % [oid, pr.get("npc_id")])
		for sid in P2_SCENES:
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
		var first: String = "SP_C4P2_Yard" if path == KARSK else "SP_C4P2_Platform"
		kit.eq(lvl.get_spawn(first), Vector2(SPAWNS[path][first][0], SPAWNS[path][first][1]), "%s: entry spawn" % path)
		for c in lvl.playfield.get_children():
			var hid = c.get("hotspot_id")
			if hid != null and str(hid) != "" and hs.has(str(hid)):
				var off: Vector2 = c.get("hotspot_offset") if c.get("hotspot_offset") != null else Vector2.ZERO
				kit.eq(c.position, Vector2(float(hs[str(hid)][0]), float(hs[str(hid)][1])) + off, "%s/%s placed on %s" % [path, c.name, hid])
		lvl.free()
	for oid in P2_OBJECTIVES:
		kit.eq(placed.get(oid, 0), 1, "%s has exactly one interactable" % oid)
	# people of the shells: Ekdahl twice (signal / express door, gated so only one is present), Lev after the book,
	# Hanna until the house is solved, Wendt after it; the ambient guard, minder and shadow never look at the player
	var npcs := {}
	for path in ENVS:
		for nd in _nodes_of(path):
			if nd["props"].has("char_id"):
				npcs[nd["name"]] = nd["props"]
	kit.eq(Kit.sorted(npcs.keys()), Kit.sorted(["IrinaYard", "MariaCoal", "GuardCoal", "EkdahlSignal", "MinderCanteen",
		"LevSandhouse", "EkdahlExpress", "MartaBuffet", "ShadowKiosk", "EkdahlWindow", "KuhnertGate", "WendtYard", "HannaYard"]),
		"NPC nodes")
	kit.eq([npcs.get("EkdahlSignal", {}).get("hide_after"), npcs.get("EkdahlExpress", {}).get("show_after")],
		["c4g_inspect_card", "c4g_inspect_card"], "Ekdahl at the signal until the card is whole, then at the express door")
	kit.eq([npcs.get("LevSandhouse", {}).get("show_after"), npcs.get("HannaYard", {}).get("hide_after"),
		npcs.get("WendtYard", {}).get("show_after")], ["c4g_inspect_book", "c4h_solve_house", "c4h_solve_house"], "gated people")
	for n in ["GuardCoal", "MinderCanteen", "ShadowKiosk"]:
		kit.eq(npcs.get(n, {}).get("look_at_player"), "false", "%s does not turn to the player" % n)
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
	for sid in P2_SCENES:
		kit.eq(game.level_file(sid), KARSK if sid.begins_with("L_C4P2_Karsk") else BERLIN, "%s level file" % sid)
		kit.eq(game.scene_partner(sid), "", "%s: nobody stands in" % sid)
	return true


func _texts() -> bool:
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var keys: Array = ["ui.chapter_c4"]
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
	for f in ["de_c4p2_dialogue", "de_c4p2_cinematics", "de_c4p2_ui", "de_c4p2_characters"]:
		var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/locale/%s.json" % f))
		kit.ok(r["ok"], f + " parses")
		if r["ok"]:
			keys.append_array((r["value"]["strings"] as Dictionary).keys())
	for sid in P2_SCENES:
		keys.append(data["scenes"]["scenes"].filter(func(s) -> bool: return s["id"] == sid)[0]["title_key"])
	kit.ok(keys.size() >= 280, "part-2 texts collected (%d)" % keys.size())
	var spoken: Dictionary = {}
	for did in P2_DIALOGUES:
		for node in conversations[did]["nodes"]:
			spoken[node["text_key"]] = true
	for node_id in ext.line_variants:
		if str(node_id).substr(0, 3) in ["c4e", "c4f", "c4g", "c4h"]:
			for v in ext.line_variants[node_id]:
				spoken[v["key"]] = true
	for k in keys:
		var t: String = loc.t(str(k))
		kit.ok(loc.has(str(k)) and t.strip_edges() != "", "%s has German text" % k)
		kit.ok(not t.contains("\""), "%s: German quotes („…“, ‚…‘), no ASCII double quote" % k)
		kit.ok(not t.contains(" - "), "%s: dashes are – (en dash), not -" % k)
		kit.ok(not t.contains("Matth" + "ias"), "%s: the pre-rename name never appears" % k)
		if spoken.has(k) or str(k).begins_with("dlg.c4p2.react."):
			kit.ok(t.length() <= 140, "%s: spoken line ≤ 140 characters (%d)" % [k, t.length()])
	# memories, tasks, journal people
	for sid in P2_SCENES:
		kit.ok(loc.has("ui.memories.place." + sid) and loc.has("ui.memories.date." + sid), "%s: memory place and date" % sid)
	for opt in C4G:
		kit.ok(loc.has("ui.memories.decided." + opt), "memory line for %s" % opt)
	for oid in ["c4g_solve_halves", "c4h_solve_house"]:
		kit.ok(loc.has("ui.memories.echo." + oid), "memory echo for %s" % oid)
	for sid in ["L_C4P2_KarskA", "L_C4P2_BerlinA"]:
		kit.ok(loc.has("ui.tasks.place." + sid), "task place of the level key %s" % sid)
	for p in ["maria", "hanna", "wendt", "blockwart"]:
		for k in ["char.%s.name", "char.%s.role", "sys.journal.person.%s.name", "sys.journal.person.%s.note"]:
			kit.ok(loc.has(k % p), (k % p) + " exists")
	# the closing film's lines for both decisions and both c4d routes
	for k in ["cin.c4p2.clock.konrad_name", "cin.c4p2.clock.konrad_protect", "cin.c4p2.clock.publish", "cin.c4p2.clock.protect",
			"cin.c4p2.express.alexei_publish", "cin.c4p2.express.alexei_protect", "cin.c4p2.clock.end"]:
		kit.ok(loc.has(k), "film line %s" % k)
	return true


## Every new evidence item is on the board (data/board/*: place, spot, short title, at least one thread); the open
## question of part 1 („Dienstag, 23.40“) is answered in place by the part-2 decision.
func _board() -> bool:
	var board := _manifest("res://data/board/c17_board.json")
	var links := _manifest("res://data/board/c17_links.json")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var placed := {}
	for pl in board.get("places", []):
		for sid in pl.get("scenes", []):
			placed[str(sid)] = str(pl.get("id"))
		kit.ok(loc.has(str(pl.get("title_key"))), "place title %s" % pl.get("title_key"))
	for sid in P2_SCENES:
		kit.ok(placed.has(sid), "%s is on a board place" % sid)
		kit.ok(loc.has(str(board.get("spots", {}).get(sid, ""))), "%s has a spot line" % sid)
	var threaded := {}
	for grp in links.get("groups", []):
		kit.ok(loc.has(str(grp.get("caption_key"))), "caption %s" % grp.get("caption_key"))
		for id in grp.get("items", []):
			threaded[str(id)] = true
	for id in P2_ITEMS:
		var short: String = loc.t("board.short." + id)
		kit.ok(loc.has("board.short." + id) and short.length() <= 22, "%s: short card title ≤ 22 (%s)" % [id, short])
		kit.ok(threaded.has(id), "%s has at least one thread" % id)
	var slots := {}
	for m in board.get("summary", []):
		kit.ok(loc.has(str(m.get("text_key"))), "milestone text %s" % m.get("text_key"))
		if str(m.get("slot", "")) == "tuesday":
			slots[str(m.get("id"))] = true
	kit.eq(Kit.sorted(slots.keys()), Kit.sorted(["c4p2_tuesday_publish", "c4p2_tuesday_protect", "c4_tuesday"]),
		"„Dienstag, 23.40“: the open question and its two answers share a slot")
	return true


## The end card lists every decision of the playthrough in story order — also after a reload (C4_DESIGN §1).
func _end_card() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game") if Kit.root() else null
	if game == null or not game.has_method("end_card_decisions"):
		print("      note: Game.end_card_decisions missing — end card not checked")
		return true
	var g := kit.play_verified_route("keep_private", "request_explanation", false, "note_alone", "report_delegation",
		"pocket_plan", "swap_halves", "protect_marta", "protect_first")
	var h := kit.story()
	kit.is_ok(h.load_json(g.save_json()), "finished state reloads")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var want: Array = []
	for oid in ["a1_choose", "m1_choose", "c3a_choose", "c3b_choose", "c3d_choose", "c3g_choose", "c4d_choose", "c4g_choose"]:
		for c in objectives[oid]["choices"]:
			if c["id"] == g.choice_history()[oid]:
				want.append("• " + loc.t(c["text_key"]))
	kit.eq(game.end_card_decisions(g.choice_history()), want, "eight decisions in story order (live)")
	kit.eq(game.end_card_decisions(h.choice_history()), want, "eight decisions in story order (after a reload)")
	kit.eq(want.size(), 8, "eight lines")
	g.free()
	h.free()
	return true


## What the other streams of round 10 deliver: reported while missing, checked once present.
func _pending() -> bool:
	var pend: Array = []
	for id in ["maria", "hanna", "wendt", "blockwart"]:
		var dir := "res://assets/characters/%s/" % id
		if not (FileAccess.file_exists(dir + "sheet.json") and FileAccess.file_exists(dir + "portrait.json")):
			pend.append("cast %s (sheet + portrait)" % id)
		else:
			var por = _manifest(dir + "portrait.json")
			kit.eq(Kit.sorted(por.get("expressions", [])).filter(func(e) -> bool: return e in ["neutral", "concerned", "determined", "surprised"]),
				["concerned", "determined", "neutral", "surprised"], "%s: the four expressions" % id)
	for id in ["guard_karsk", "press_officer", "stapo_civil"]:
		if not FileAccess.file_exists("res://assets/characters/%s/sheet.json" % id):
			pend.append("life sheet %s" % id)
	for path in ENVS.values():
		if _manifest(path).get("placeholder", false):
			pend.append("art " + str(path).get_base_dir().get_file())
	for cid in P2_CINEMATICS:
		if not ResourceLoader.exists(str(ext.cinematics.get(cid, ""))):
			pend.append("film " + cid)
	for oid in ["c4g_solve_halves", "c4h_solve_house"]:
		if not ResourceLoader.exists(str(ext.puzzles.get(oid, ""))):
			pend.append("puzzle UI " + oid)
	for p in pend:
		print("      pending (round 10): " + str(p))
	kit.ok(true, "pending report printed (%d)" % pend.size())
	return true
